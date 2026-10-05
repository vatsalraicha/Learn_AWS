# 43 — Optimization — Caching, Multi-Stage, `extends`

## 1. The optimization levers

A slow CI pipeline kills velocity. The four levers:
1. **Parallelization** (DAG mode with `needs`)
2. **Caching** (don't reinstall deps every run)
3. **Smart triggers** (don't run jobs that don't matter)
4. **DRY config** (`extends`, `include`, anchors)

## 2. Dynamic image versioning

Don't push `latest`; use semantic + commit-SHA versioning:

```yaml
variables:
  IMAGE_TAG: $CI_REGISTRY_IMAGE:$CI_COMMIT_REF_SLUG-$CI_COMMIT_SHORT_SHA

# For tag-driven releases
variables:
  RELEASE_TAG: $CI_REGISTRY_IMAGE:$CI_COMMIT_TAG
```

Auto-version from git:
```yaml
build:
  before_script:
    - export APP_VERSION=$(git describe --tags --always --abbrev=7)
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$APP_VERSION .
```

## 3. Caching deeper

```yaml
.cache_template: &python_cache
  cache:
    key:
      files: [requirements.txt]
    paths:
      - .venv/
      - .cache/pip/
    policy: pull-push     # default; alternatives: pull, push, pull-push

test:
  <<: *python_cache
  script:
    - python -m venv .venv
    - .venv/bin/pip install -r requirements.txt
    - .venv/bin/pytest
```

`policy: pull` for jobs that only consume; `policy: push` for jobs that produce. Default `pull-push` does both.

### Caching node_modules
```yaml
.node_cache: &node_cache
  cache:
    key:
      files: [package-lock.json]
    paths:
      - node_modules/
      - .npm/

build:
  <<: *node_cache
  script:
    - npm ci --cache .npm --prefer-offline
    - npm run build
```

### Caching Docker layers
For Docker builds, BuildKit + registry cache (Module 23):
```yaml
build-image:
  image: gcr.io/kaniko-project/executor:v1.23.0-debug
  script:
    - /kaniko/executor --cache=true --cache-repo $CI_REGISTRY_IMAGE/cache ...
```

## 4. Speeding up `npm install` etc.

- `npm ci` (not `install`) — fail on lockfile mismatch + skip-update + faster
- `pip install --no-deps -r requirements-locked.txt`
- `uv pip install -r requirements.txt` — 10-100x faster
- `bun install` — even faster for Node

## 5. SAST + DAST as pipeline stages (with security-as-code)

```yaml
include:
  - template: Jobs/SAST.gitlab-ci.yml
  - template: Jobs/Secret-Detection.gitlab-ci.yml
  - template: Jobs/Dependency-Scanning.gitlab-ci.yml
  - template: Jobs/Container-Scanning.gitlab-ci.yml
  - template: Jobs/DAST.gitlab-ci.yml

variables:
  SAST_EXCLUDED_PATHS: "tests/, docs/"
  DS_EXCLUDED_PATHS: "vendor/"
  DAST_WEBSITE: https://staging.example.com
  DAST_FULL_SCAN_ENABLED: "true"
```

GitLab built-in templates (Premium/Ultimate) handle scanner runs + report integration. Free tier: bring your own (Semgrep, Trivy, ZAP).

## 6. Multi-stage deployments — Dev → Staging → Prod

```yaml
stages: [test, build, deploy-dev, deploy-staging, deploy-prod]

.deploy_template: &deploy
  image: alpine/k8s:1.31
  before_script:
    - kubectl config use-context $KUBE_CONTEXT

deploy-dev:
  stage: deploy-dev
  <<: *deploy
  environment: { name: dev, url: https://dev.example.com }
  variables: { KUBE_CONTEXT: dev-cluster, NAMESPACE: app-dev }
  script: kubectl -n $NAMESPACE set image deployment/app app=$IMAGE_TAG
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'

deploy-staging:
  stage: deploy-staging
  <<: *deploy
  environment: { name: staging, url: https://staging.example.com }
  variables: { KUBE_CONTEXT: stg-cluster, NAMESPACE: app-stg }
  script: kubectl -n $NAMESPACE set image deployment/app app=$IMAGE_TAG
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
      when: manual

deploy-prod:
  stage: deploy-prod
  <<: *deploy
  environment: { name: production, url: https://example.com }
  variables: { KUBE_CONTEXT: prd-cluster, NAMESPACE: app-prd }
  script: kubectl -n $NAMESPACE set image deployment/app app=$IMAGE_TAG
  rules:
    - if: '$CI_COMMIT_TAG'
      when: manual
```

## 7. Reusing config — `extends`

The cleaner modern syntax over YAML anchors:

```yaml
.test-template:
  image: python:3.13-slim
  cache:
    key:
      files: [requirements.txt]
    paths: [.venv/]
  before_script:
    - python -m venv .venv
    - .venv/bin/pip install -r requirements.txt

unit-tests:
  extends: .test-template
  script: .venv/bin/pytest tests/unit

integration-tests:
  extends: .test-template
  script: .venv/bin/pytest tests/integration
  services: [postgres:17]
```

`extends:` is **deep-merged** — child overrides only what it specifies.

## 8. Include — across files + projects

```yaml
include:
  # Local file
  - local: 'ci/build.yml'

  # File from another project
  - project: 'my-org/ci-templates'
    ref: main
    file: '/python/test.yml'

  # Remote URL
  - remote: 'https://example.com/ci/template.yml'

  # GitLab-provided template
  - template: 'Auto-DevOps.gitlab-ci.yml'

  # CI/CD Components (new way, GitLab 17+)
  - component: 'gitlab.com/components/secret-detection/secret-detection@~latest'
```

## 9. Matrix builds

```yaml
test:
  parallel:
    matrix:
      - PYTHON_VERSION: ["3.11", "3.12", "3.13"]
        OS: [linux]
  image: python:$PYTHON_VERSION-slim
  script:
    - pip install -r requirements.txt
    - pytest
```

This generates 3 parallel jobs.

## 10. Skipping unchanged work

`rules:changes` runs the job only when relevant files changed:
```yaml
build-frontend:
  rules:
    - changes: [frontend/**/*]
  script: cd frontend && npm run build

build-backend:
  rules:
    - changes: [backend/**/*]
  script: cd backend && go build
```

Combined with monorepo: only the changed component rebuilds.

## 11. Parallel + needs combo (DAG mode)

```yaml
test-1:
  stage: test
  script: pytest tests/unit_1

test-2:
  stage: test
  script: pytest tests/unit_2

# Aggregator starts as soon as both finish, doesn't wait for whole stage
report:
  stage: test
  needs: [test-1, test-2]
  script: ./aggregate-reports.sh
```

Or run test shards:
```yaml
test:
  parallel: 8
  script: pytest --shard $CI_NODE_INDEX/$CI_NODE_TOTAL
```

## 12. Quick self-check

1. What's the difference between `policy: pull` and `policy: push` in cache config?
2. What's `extends` and how does it compose with anchors?
3. What does `rules:changes` enable for monorepos?
4. How does `parallel:matrix` work?
5. What's the difference between `include:local` and `include:project`?

(Answers: pull only reads cache (don't update), push only writes (don't read first) — useful when only some jobs produce cache; extends is deep-merge of templates — preferred over anchors for readability — child overrides only specified keys; only build the components whose files changed in the commit — huge speedup in monorepos; generates N parallel jobs with cross-product of matrix dimensions, each with a unique combination as env vars; local is files in the same repo, project is files from another project (cross-project sharing).)
