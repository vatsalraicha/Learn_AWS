# 40 — GitLab CI/CD Core Concepts

## 1. The .gitlab-ci.yml file

GitLab CI reads `.gitlab-ci.yml` at the root of your repo. One YAML defines the pipeline.

```yaml
stages: [test, build, deploy]

test:
  stage: test
  image: python:3.13-slim
  script:
    - pip install -r requirements.txt
    - pytest

build:
  stage: build
  image: docker:27-cli
  services: [docker:27-dind]
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

deploy:
  stage: deploy
  image: alpine/k8s:1.31
  script:
    - kubectl set image deployment/app app=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

## 2. Jobs — the unit of work

A job has:
- **`script`** — what runs (shell commands)
- **`image`** — Docker image the job runs in
- **`stage`** — which stage it belongs to
- **`needs`** — dependency on other jobs (DAG mode)
- **`rules` / `only` / `except`** — when to run
- **`artifacts`** — files to keep
- **`cache`** — files to reuse between runs
- **`before_script` / `after_script`** — setup / teardown

```yaml
unit-tests:
  stage: test
  image: python:3.13-slim
  before_script:
    - pip install -r requirements.txt -r requirements-dev.txt
  script:
    - pytest --cov --junitxml=report.xml
  after_script:
    - echo "done"
  artifacts:
    when: always
    paths: [report.xml, htmlcov/]
    reports:
      junit: report.xml
    expire_in: 30 days
```

## 3. Stages — sequential groups of parallel jobs

```yaml
stages: [lint, test, build, deploy]
```

Jobs in same stage run in parallel; stages run sequentially. A stage waits for all jobs in the previous stage to succeed (unless `allow_failure: true`).

## 4. `needs` — the DAG mode

For granular dependencies, use `needs` to override the stage order:

```yaml
build-frontend:
  stage: build
  script: cd frontend && npm run build

build-backend:
  stage: build
  script: cd backend && go build

test-frontend:
  stage: test
  needs: [build-frontend]   # starts as soon as build-frontend finishes
  script: cd frontend && npm test

test-backend:
  stage: test
  needs: [build-backend]
  script: cd backend && go test ./...
```

`test-frontend` doesn't wait for `build-backend`; it starts as soon as `build-frontend` finishes. DAG mode lets you parallelize aggressively.

## 5. Triggers — `only`, `except`, `rules`, `workflow`

The 2026 way: **`rules`** (the modern syntax; `only`/`except` deprecated for new code).

```yaml
deploy-staging:
  stage: deploy
  script: ./deploy.sh staging
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
      changes: [src/**/*]
      when: on_success

deploy-prod:
  stage: deploy
  script: ./deploy.sh prod
  rules:
    - if: '$CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/'
      when: manual
```

### `workflow:rules` controls whole pipeline
```yaml
workflow:
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'   # MR pipeline
    - if: '$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH'        # main branch
    - if: '$CI_COMMIT_TAG'                                  # tag
```

If no rule matches, the pipeline doesn't run.

## 6. Predefined CI/CD Variables

Every job gets dozens of pre-populated env vars:

| Variable | Value |
|---|---|
| `$CI_COMMIT_SHA` | full SHA |
| `$CI_COMMIT_SHORT_SHA` | 8-char prefix |
| `$CI_COMMIT_BRANCH` | branch name |
| `$CI_COMMIT_TAG` | tag if any |
| `$CI_PIPELINE_ID` | unique pipeline ID |
| `$CI_PIPELINE_URL` | URL to view pipeline |
| `$CI_JOB_ID` | unique job ID |
| `$CI_PROJECT_PATH` | namespace/project |
| `$CI_REGISTRY` | host of project's container registry |
| `$CI_REGISTRY_IMAGE` | base image path in registry |
| `$CI_REGISTRY_USER` / `$CI_REGISTRY_PASSWORD` | auth to registry |
| `$CI_JOB_TOKEN` | API token scoped to this job |

Full list: 200+ predefined variables, in GitLab docs.

## 7. Custom variables

### In `.gitlab-ci.yml`
```yaml
variables:
  APP_NAME: my-app
  ENVIRONMENT: dev
```

### In UI (Settings → CI/CD → Variables)
- **Masked** — value hidden in logs
- **Protected** — only available on protected branches/tags
- **Expanded** — variable expansion enabled
- **File type** — value written to a temp file, var contains the path

### Hierarchy (precedence)
1. Inline variables (lowest)
2. `variables:` block
3. Project CI/CD variables (UI)
4. Group CI/CD variables
5. Manual job variables (highest)

## 8. Triggering a pipeline on Merge Request

GitLab MRs auto-trigger pipelines when:
- The MR is opened or commits pushed
- The pipeline source is `merge_request_event`

```yaml
workflow:
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
    - if: '$CI_COMMIT_BRANCH == "main"'

# In jobs:
test:
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
    - if: '$CI_COMMIT_BRANCH == "main"'
  script: pytest
```

**Merged-results pipelines** run the pipeline on the *merged* result (target + source merge) — closer to production behavior. **Merge trains** queue MRs to merge one at a time, each running the merged-results pipeline.

## 9. Artifacts + Reports

```yaml
test:
  script: pytest --junitxml=report.xml --cov-report=xml
  artifacts:
    when: always
    paths:
      - report.xml
      - coverage.xml
    reports:
      junit: report.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
    expire_in: 30 days
```

GitLab natively understands reports:
- **junit** — test results displayed in MR
- **coverage_report** — coverage in MR
- **sast** — SAST findings in MR
- **dependency_scanning** — SCA findings
- **container_scanning** — image scan
- **dast** — DAST findings
- **secret_detection** — secret scan
- **license_scanning** — license issues
- **terraform** — terraform plan in MR

## 10. Cache vs Artifacts

| | Artifacts | Cache |
|---|---|---|
| **Purpose** | Pass between stages + persist for download | Speed up subsequent runs |
| **Lifetime** | Configurable (default 30 days) | Until manually cleared or evicted |
| **Per-job** | Yes | Shared by key |
| **Compressed + uploaded** | To GitLab server | To shared storage (S3 / GCS / local) |
| **Use case** | Test reports, built binaries | node_modules, pip cache, .terraform |

```yaml
test:
  cache:
    key: $CI_COMMIT_REF_SLUG
    paths:
      - .venv/
      - .pytest_cache/
  script:
    - python -m venv .venv
    - .venv/bin/pip install -r requirements.txt
    - .venv/bin/pytest
```

## 11. Inline shell + multiline

```yaml
script:
  - |
    set -euo pipefail
    if [ "$CI_COMMIT_BRANCH" = "main" ]; then
      ./scripts/deploy.sh prod
    else
      ./scripts/deploy.sh staging
    fi
```

The `|` preserves newlines. Bash conditionals work fine.

## 12. Quick self-check

1. What's the difference between `stages` and `needs`?
2. What's the difference between `rules` and the legacy `only`/`except`?
3. What's a "merged-results pipeline" and why use it?
4. What's the difference between artifacts and cache?
5. What's `workflow:rules` vs job-level `rules`?

(Answers: stages = sequential groups, needs = DAG dependencies between jobs that override stage order; rules is the modern flexible syntax with if/changes/exists/when, only/except is legacy + simpler; runs the pipeline on the merged result (target + source merge) — closer to production state; artifacts pass files between jobs + persist for download (junit, coverage), cache speeds up subsequent runs (node_modules, pip cache); workflow:rules controls whether the entire pipeline runs, job-level rules controls whether the specific job runs within an already-running pipeline.)
