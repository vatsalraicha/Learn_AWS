# 44 — Microservices CI/CD — Monorepo + Polyrepo

## 1. The microservices CI/CD problem

You have 30 services. Options:
- **Polyrepo**: each service its own repo → independent CI/CD; easy to scope ownership; hard to share code/config
- **Monorepo**: one repo with all services → shared code/config easy; complex CI/CD

Both are valid. Pick based on team org + scale.

## 2. Monorepo CI/CD pattern

The challenge: 30 services, one repo. Don't rebuild + retest all 30 on every commit.

### `rules:changes` per service
```yaml
# In services/service-a/ci.yml
service-a:test:
  stage: test
  script: cd services/service-a && npm test
  rules:
    - changes:
        - services/service-a/**/*
        - shared/**/*

service-a:build:
  stage: build
  needs: [service-a:test]
  script: cd services/service-a && docker build -t $CI_REGISTRY_IMAGE/service-a:$CI_COMMIT_SHA .
  rules:
    - changes:
        - services/service-a/**/*

service-a:deploy:
  stage: deploy
  needs: [service-a:build]
  script: kubectl set image deployment/service-a service-a=$CI_REGISTRY_IMAGE/service-a:$CI_COMMIT_SHA
  rules:
    - changes: [services/service-a/**/*]
      if: '$CI_COMMIT_BRANCH == "main"'
```

### Top-level orchestrator
```yaml
include:
  - local: services/service-a/ci.yml
  - local: services/service-b/ci.yml
  - local: services/service-c/ci.yml
  # ... 30 of these
```

Or dynamically:
```yaml
include:
  - local: services/*/ci.yml    # glob since GitLab 16.x
```

## 3. Polyrepo CI/CD pattern

Each service's repo has its own `.gitlab-ci.yml` referring to common templates:

```yaml
# Each service repo:
include:
  - project: 'my-org/ci-templates'
    ref: v2.4
    file: '/python/service.yml'

service:test:
  extends: .python-service-test
  variables:
    SERVICE_NAME: service-a
```

The `ci-templates` project holds the shared logic.

## 4. CI/CD Components (the 2024 way, replacing CI Templates)

GitLab 17.0 (May 2024) GA-d **CI/CD Components** — reusable, versioned bundles published to a Catalog.

A Component lives in its own GitLab project + has a `templates/` dir:

```
ci-templates/
├── templates/
│   ├── docker-build.yml      # Component "docker-build"
│   └── helm-deploy.yml       # Component "helm-deploy"
└── README.md
```

Publish a release tag (e.g., `v1.2`); consumers reference by version:

```yaml
include:
  - component: gitlab.com/my-org/ci-templates/docker-build@v1.2
    inputs:
      image-name: my-app
      build-args: "--build-arg ENV=prod"

  - component: gitlab.com/my-org/ci-templates/helm-deploy@v1.2
    inputs:
      chart-path: ./charts/my-app
      release-name: my-app
      namespace: my-app-prod
```

Components define typed inputs:
```yaml
# In templates/docker-build.yml
spec:
  inputs:
    image-name:
      type: string
      description: Docker image name
    build-args:
      type: string
      default: ""
      description: Extra docker build args
---
docker-build:
  stage: build
  script:
    - docker build $[[ inputs.build-args ]] -t $[[ inputs.image-name ]] .
```

This is **the modern way** for polyrepo orgs to share CI logic.

## 5. Job Templates with `extends:` (the older approach)

For simpler reuse without Component overhead:

```yaml
# in ci-templates/python.yml
.python-test:
  image: python:3.13-slim
  cache:
    paths: [.venv/]
  before_script:
    - python -m venv .venv
    - .venv/bin/pip install -r requirements.txt -r requirements-dev.txt
  script:
    - .venv/bin/pytest --cov

.python-build:
  image: docker:27-cli
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
```

```yaml
# in service's .gitlab-ci.yml
include:
  - project: my-org/ci-templates
    ref: main
    file: /python.yml

unit-tests:
  extends: .python-test

build:
  extends: .python-build
```

## 6. Multi-project pipelines

A pipeline in one project triggers a pipeline in another:

```yaml
trigger-deploy:
  stage: deploy
  trigger:
    project: my-org/deploy-project
    branch: main
    strategy: depend     # wait for triggered pipeline to finish
```

Useful when you want to keep app code separate from deploy manifests (GitOps).

## 7. Parent-child pipelines

Spawn a child pipeline from a parent:

```yaml
trigger-build:
  stage: build
  trigger:
    include:
      - local: ci/build-pipeline.yml
    strategy: depend
```

Useful for dynamic generation: detect what changed, generate a child pipeline that only builds those.

## 8. Dynamic child pipelines

Generate `.gitlab-ci.yml` at runtime:

```yaml
generate:
  stage: build
  script:
    - python ci/generate.py > dynamic-pipeline.yml
  artifacts:
    paths: [dynamic-pipeline.yml]

trigger:
  stage: deploy
  trigger:
    include:
      - artifact: dynamic-pipeline.yml
        job: generate
    strategy: depend
```

`generate.py` inspects the diff and writes only the relevant build jobs. Combines monorepo + per-service builds elegantly.

## 9. Monorepo vs Polyrepo decision

| | Monorepo | Polyrepo |
|---|---|---|
| **Coordination** | Atomic cross-service commits | Multi-PR dance |
| **Code share** | `shared/` dir easy | Package + version |
| **CI complexity** | Per-service triggers + components | Templates + Components per repo |
| **Build time** | Risk of "build everything" | Isolated |
| **Tooling** | Bazel, Nx, Turborepo help | Standard tooling |
| **Ownership** | CODEOWNERS per path | Repo per team |
| **Scale ceiling** | Soft at 1000+ services | Infinite |

Big tech monorepos: Google, Meta, Twitter. Polyrepo at scale: Netflix, Amazon.

## 10. Build the right thing — affected detection

For monorepos, **affected analysis**:
- Nx, Turborepo, Bazel — language/framework-specific tools that know the dep graph
- Custom: walk dep graph + diff to find affected packages
- Last resort: `git diff --name-only` + heuristic

Skipping unrelated jobs saves money and time at scale.

## 11. Quick self-check

1. What's the modern replacement for CI Templates in GitLab 17+?
2. What's a parent-child pipeline vs a multi-project pipeline?
3. How do `rules:changes` enable smart monorepo CI?
4. What's a dynamic child pipeline?
5. When does polyrepo's "one repo, one CI" beat monorepo for CI complexity?

(Answers: CI/CD Components — versioned, catalog-published, typed inputs; parent-child both inside same project (one spawns the other), multi-project triggers a pipeline in another project; only run jobs for services whose files changed in the commit; pipeline generates more pipeline YAML at runtime — useful when you need to decide what to build based on the diff; small to medium scale + clear service boundaries + no cross-service atomic changes needed.)
