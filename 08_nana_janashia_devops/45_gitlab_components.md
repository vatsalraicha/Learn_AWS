# 45 — CI/CD Components (the 2024 Templates Replacement)

## 1. Why Components exist

GitLab CI Templates (`include: template:`) and `include: project:` worked but had limits:
- No typed inputs (everything was implicit YAML vars)
- No versioning (you referenced by ref name, no semver guarantees)
- No discoverability (no catalog)
- No tests (templates were tested by their consumers)

**CI/CD Components** (GA in GitLab 17.0, May 2024) add all four.

## 2. Anatomy of a Component

```
my-org/ci-components/
├── templates/
│   ├── docker-build/
│   │   └── template.yml     # the actual job(s)
│   ├── helm-deploy/
│   │   └── template.yml
│   └── trivy-scan/
│       └── template.yml
├── README.md
└── .gitlab-ci.yml            # tests for the components
```

Each subdir in `templates/` is one Component. The directory name is the component name.

## 3. A simple Component

```yaml
# templates/docker-build/template.yml
spec:
  inputs:
    image-name:
      type: string
      description: Image name to build/push
    dockerfile:
      type: string
      default: Dockerfile
      description: Path to Dockerfile
    context:
      type: string
      default: .
    push:
      type: boolean
      default: true
    stage:
      type: string
      default: build
---
docker-build:
  stage: $[[ inputs.stage ]]
  image: docker:27-cli
  services: [docker:27-dind]
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
  script:
    - docker build -f $[[ inputs.dockerfile ]] -t $[[ inputs.image-name ]] $[[ inputs.context ]]
    - if [ "$[[ inputs.push ]]" = "true" ]; then docker push $[[ inputs.image-name ]]; fi
```

## 4. Using a Component

```yaml
# consumer .gitlab-ci.yml
include:
  - component: $CI_SERVER_FQDN/my-org/ci-components/docker-build@v1.0.0
    inputs:
      image-name: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
      dockerfile: Dockerfile.prod
      context: ./app
```

The `$CI_SERVER_FQDN` predefined variable points to your GitLab instance (gitlab.com or self-hosted).

## 5. Input types

```yaml
spec:
  inputs:
    name:
      type: string
      default: "default-name"
      regex: '^[a-z][a-z0-9-]*$'
    replicas:
      type: number
      default: 3
    debug:
      type: boolean
      default: false
    environments:
      type: array
      default: [dev, staging, prod]
    timeout:
      type: string
      default: "30m"
```

Inputs are validated; bad input fails the pipeline early with a clear message.

## 6. Versioning

Component releases are git tags on the component project. Reference patterns:

```yaml
include:
  - component: $CI_SERVER_FQDN/my-org/ci-components/docker-build@v1.2.3   # exact version
  - component: $CI_SERVER_FQDN/my-org/ci-components/docker-build@~latest  # latest release
  - component: $CI_SERVER_FQDN/my-org/ci-components/docker-build@main     # main branch (testing only)
  - component: $CI_SERVER_FQDN/my-org/ci-components/docker-build@$CI_COMMIT_SHA  # SHA-pinned
```

For production: **pin to exact semver tag**, like any other dependency.

## 7. CI/CD Catalog

GitLab.com has a public Catalog (https://gitlab.com/explore/catalog) where Components are searchable, tagged, and rated. Self-managed instances have their own internal Catalog.

To publish to Catalog:
1. Project has at least one `templates/<component>/template.yml`
2. Add `description` and `spec.tags` to README
3. Create a release (git tag + GitLab Release object)
4. Mark project as **CI Catalog resource** in Settings

```yaml
# In templates/foo/template.yml
spec:
  description: "Build and push Docker image"
  inputs:
    # ...
```

## 8. The library pattern — your org's component library

```
my-org/ci-components/
├── templates/
│   ├── python-test/template.yml
│   ├── nodejs-test/template.yml
│   ├── docker-build/template.yml
│   ├── helm-deploy/template.yml
│   ├── argocd-sync/template.yml
│   ├── trivy-scan/template.yml
│   ├── cosign-sign/template.yml
│   ├── slack-notify/template.yml
│   └── ...
├── tests/
│   └── ... (verify each component)
└── .gitlab-ci.yml
```

Every service in the org references this:
```yaml
include:
  - component: $CI_SERVER_FQDN/my-org/ci-components/python-test@v3.1
  - component: $CI_SERVER_FQDN/my-org/ci-components/docker-build@v3.1
    inputs: { image-name: $CI_REGISTRY_IMAGE }
  - component: $CI_SERVER_FQDN/my-org/ci-components/trivy-scan@v3.1
    inputs: { image-name: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA }
  - component: $CI_SERVER_FQDN/my-org/ci-components/helm-deploy@v3.1
    inputs: { chart-path: ./charts/app }
```

One MR to the central components repo updates all consuming projects on next pipeline run.

## 9. Testing a Component

The component's project has its own `.gitlab-ci.yml` that exercises its own components:

```yaml
# Test docker-build component
include:
  - component: $CI_SERVER_FQDN/$CI_PROJECT_PATH/docker-build@$CI_COMMIT_SHA
    inputs:
      image-name: test-image:$CI_COMMIT_SHORT_SHA
      push: false
```

Pipeline runs → if the component breaks, the pipeline fails → block merge.

## 10. Migrating from CI Templates / Includes

Old:
```yaml
include:
  - project: 'my-org/ci-templates'
    ref: main
    file: '/python.yml'

unit-tests:
  extends: .python-test
```

New (Component):
```yaml
include:
  - component: $CI_SERVER_FQDN/my-org/ci-components/python-test@v1.0
    inputs:
      python-version: "3.13"
```

The migration is mechanical but gives:
- Versioning safety
- Typed inputs (no more "did I set the right magic var?")
- Catalog discoverability

## 11. Best practices

1. **One Component per concern** — `docker-build`, not `build-and-deploy`
2. **Typed inputs over implicit variables** — make the contract explicit
3. **Semver versioning** — major bumps for breaking changes
4. **Test in the component's own pipeline** — don't make consumers find your bugs
5. **Pin consumers to exact versions** — `@v1.2.3`, not `@~latest`
6. **Document inputs + outputs** — generate from `spec:` if you can
7. **Avoid hidden side effects** — Component should only do what its name says

## 12. Quick self-check

1. What four things did Components add over CI Templates?
2. What's the input type system give you?
3. How do you reference a Component?
4. Why pin to exact version `@v1.2.3` in production?
5. What's the CI/CD Catalog?

(Answers: typed inputs + versioning + catalog discoverability + testability; runtime validation of inputs with regex/range/enum — bad inputs fail early with clear messages; `include: - component: $CI_SERVER_FQDN/path/to/component-project/component-name@version`; supply-chain safety — `@~latest` could change unexpectedly and break your pipeline; searchable registry of published Components within an instance — public on gitlab.com, private on self-managed.)
