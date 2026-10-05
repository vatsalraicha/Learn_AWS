# 26 — ⭐ Reusable workflows (`workflow_call`)

> *"Reusable workflows are the GitHub Actions equivalent of Jenkins shared libraries — and the highest-leverage skill for a Sr Lead at Capital One scale."*

## Why this module exists

At 1 repo, you copy-paste workflows. At 100 repos, you have CI drift, security gaps, and 100 places to update when something changes. **Reusable workflows** solve this. You define a canonical CI/CD workflow once in a central repo; every other repo references it. Bug fix? Bump the version. Want every repo to get a new security scan? Add it to the central workflow.

This is THE pattern that lets a 7,000-engineer org maintain consistent CI/CD without manual coordination.

---

## 1. The shape

A reusable workflow lives in a regular `.github/workflows/*.yml` file but uses the `workflow_call` trigger:

```yaml
# In CENTRAL repo: capitalone/workflows-org/.github/workflows/python-ci.yml
name: Reusable Python CI

on:
  workflow_call:
    inputs:
      python-version:
        type: string
        required: false
        default: "3.11"
      working-directory:
        type: string
        required: false
        default: "."
      run-integration-tests:
        type: boolean
        default: false
    secrets:
      PYPI_TOKEN:
        required: false
    outputs:
      coverage:
        description: "Test coverage percentage"
        value: ${{ jobs.test.outputs.coverage }}

jobs:
  test:
    runs-on: ubuntu-latest
    outputs:
      coverage: ${{ steps.cov.outputs.coverage }}
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ inputs.python-version }}
          cache: pip
      - working-directory: ${{ inputs.working-directory }}
        run: pip install -e ".[dev]"
      - working-directory: ${{ inputs.working-directory }}
        run: ruff check src tests
      - working-directory: ${{ inputs.working-directory }}
        run: |
          pytest --cov=src --cov-report=term --cov-report=xml
      - id: cov
        run: |
          PCT=$(grep -oP 'line-rate="\K[^"]+' ${{ inputs.working-directory }}/coverage.xml | head -1 | awk '{printf "%.1f\n", $1*100}')
          echo "coverage=$PCT" >> $GITHUB_OUTPUT
      - if: inputs.run-integration-tests
        working-directory: ${{ inputs.working-directory }}
        run: pytest tests/integration

  publish:
    needs: test
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v5
      - run: pip install build twine
      - run: python -m build
      - run: twine upload dist/* -u __token__ -p ${{ secrets.PYPI_TOKEN }}
```

Calling repo:

```yaml
# In CONSUMER repo: capitalone/cool-ml-service/.github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  python-ci:
    uses: capitalone/workflows-org/.github/workflows/python-ci.yml@v3
    with:
      python-version: "3.12"
      run-integration-tests: true
    secrets:
      PYPI_TOKEN: ${{ secrets.PYPI_TOKEN }}

  notify:
    needs: python-ci
    runs-on: ubuntu-latest
    steps:
      - run: echo "Coverage: ${{ needs.python-ci.outputs.coverage }}%"
```

Three lines of `uses:` + `with:` + `secrets:` and the consumer gets the full canonical CI. The consumer can still add their own jobs alongside (in this example, `notify` is consumer-defined).

---

## 2. Versioning reusable workflows

Same rules as marketplace actions:

```yaml
uses: capitalone/workflows-org/.github/workflows/python-ci.yml@v3                                    # major tag — moves
uses: capitalone/workflows-org/.github/workflows/python-ci.yml@v3.2.1                               # exact tag
uses: capitalone/workflows-org/.github/workflows/python-ci.yml@a1b2c3d4e5f6                         # SHA — immutable
uses: capitalone/workflows-org/.github/workflows/python-ci.yml@main                                  # branch — DON'T
```

For non-prod workflows: `@v3` tag pin is fine.
For prod-deploy workflows: pin by SHA, bump via Dependabot PRs.

**Within the same repo** (calling a reusable workflow defined in the same repo):

```yaml
uses: ./.github/workflows/reusable.yml                    # relative path; uses current SHA
```

No version pin needed for self-referential calls.

---

## 3. Inputs, secrets, outputs

### Input types

```yaml
on:
  workflow_call:
    inputs:
      environment:
        type: string                # only string, boolean, number
        required: true
      replicas:
        type: number
        default: 3
      dry-run:
        type: boolean
        default: false
```

For complex types (lists, objects), pass a JSON string and `fromJSON()` it inside.

### Secrets

```yaml
on:
  workflow_call:
    secrets:
      PROD_DB_PASSWORD:
        required: true                  # caller must explicitly pass
      OPTIONAL_TOKEN:
        required: false

# Caller:
jobs:
  call:
    uses: ./.github/workflows/reusable.yml
    secrets:
      PROD_DB_PASSWORD: ${{ secrets.PROD_DB_PASSWORD }}

# Or pass ALL caller secrets:
jobs:
  call:
    uses: ./.github/workflows/reusable.yml
    secrets: inherit                   # forwards all caller's secrets — use sparingly
```

**`secrets: inherit`** is convenient but blurs trust boundaries. Per 2026 guidance, explicit per-secret passing is preferred. Use `inherit` only when the reusable workflow is in the same org and you're sure about what it does.

### Outputs

```yaml
on:
  workflow_call:
    outputs:
      version:
        description: "Built version"
        value: ${{ jobs.build.outputs.version }}

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.v.outputs.version }}
    steps:
      - id: v
        run: echo "version=1.2.3" >> $GITHUB_OUTPUT

# Caller:
jobs:
  call:
    uses: ./.github/workflows/reusable.yml
  next:
    needs: call
    runs-on: ubuntu-latest
    steps:
      - run: echo "Built ${{ needs.call.outputs.version }}"
```

---

## 4. Permissions

The reusable workflow runs with the **intersection** of permissions: what the caller has AND what the reusable workflow's `permissions:` declares.

```yaml
# In reusable workflow:
on:
  workflow_call:

permissions:                              # max permissions this workflow needs
  contents: read
  id-token: write
  pull-requests: write
```

```yaml
# In caller:
permissions:                              # what caller is willing to grant
  contents: read
  id-token: write
  pull-requests: write
  packages: write                         # additional permission caller has but reusable won't use

jobs:
  call:
    uses: ./.github/workflows/reusable.yml
    permissions:                          # override per-call (since 2023)
      contents: read
      id-token: write
```

If the caller's permissions are narrower than the reusable's needs, the reusable workflow's permission-needing operations fail.

---

## 5. Limits

- **Nesting**: max 4 levels deep (A → B → C → D, no further).
- **Outputs per workflow**: 10.
- **Calls per workflow run**: each `uses:` in a job counts; no documented cap but practical limit is "reasonable."

---

## 6. Reusable workflow vs composite action — which when

| | Reusable workflow | Composite action |
|---|---|---|
| Defines | Whole jobs (with `runs-on:`, multiple steps, services, container) | A sequence of steps within a job |
| Used as | `jobs.<id>.uses` | `steps.uses` |
| Multiple jobs? | Yes | No |
| Custom runner per call? | Yes (defined in reusable) | No (inherits caller's runner) |
| Matrix support? | Yes (inside reusable) | No |
| Pass secrets? | Yes (`secrets:`) | Indirectly via env |
| Outputs? | Yes | Yes |

**Rule of thumb**: if you need a whole pipeline (lint + test + build + scan), reusable workflow. If you need a step like "setup Python with cache + install + lint," composite action. Most Capital One-style central repos have both — composite actions for common step sequences, reusable workflows for whole pipelines.

Composite actions in [module 27](27_actions_composite_custom.md).

---

## 7. Org-wide pattern (the Capital One shape)

**Central repo**: `capitalone/workflows-org`
```
.github/
  workflows/
    python-ci.yml           # for Python services
    java-ci.yml             # for Java services
    docker-build-push.yml   # build + push image to ECR
    sagemaker-deploy.yml    # deploy SageMaker endpoint
    security-scan.yml       # SAST + SCA + container scan
    release-please.yml      # changelog + release automation
    deploy-eks.yml          # deploy to EKS via OIDC
```

Tagged: `v1.0.0`, `v2.0.0`, `v3.0.0` (semver — major bumps for breaking changes).

**Consumer repo**: `capitalone/some-ml-service`
```yaml
# .github/workflows/ci.yml
on: [push, pull_request]

jobs:
  python-ci:
    uses: capitalone/workflows-org/.github/workflows/python-ci.yml@v3
    with: { python-version: "3.12" }

  security:
    uses: capitalone/workflows-org/.github/workflows/security-scan.yml@v3
    secrets: inherit

# .github/workflows/release.yml
on:
  push:
    branches: [main]

jobs:
  release:
    uses: capitalone/workflows-org/.github/workflows/release-please.yml@v3

  build-image:
    needs: release
    if: needs.release.outputs.release_created == 'true'
    uses: capitalone/workflows-org/.github/workflows/docker-build-push.yml@v3
    with:
      image-name: cool-ml-service
      tag: ${{ needs.release.outputs.version }}

  deploy:
    needs: build-image
    uses: capitalone/workflows-org/.github/workflows/sagemaker-deploy.yml@v3
    with:
      endpoint-name: cool-ml-prod
      model-image: ${{ needs.build-image.outputs.image-uri }}
    secrets: inherit
```

Result:
- Every service repo gets the same canonical CI/CD with 30 lines of YAML.
- Bump `@v3` to `@v4` to adopt a major version. Dependabot raises the PR automatically.
- Bug fix in `python-ci.yml` → every consumer picks it up on next run.
- Add a new security scan to `security-scan.yml` → every consumer gets it for free.
- Audit: query the org via GitHub Search "uses: capitalone/workflows-org" to find every consumer.

---

## 8. Access control

Reusable workflows can be called from:
- The same repo
- Public repos (if the reusable workflow's repo is public)
- Private repos in the same org (if the reusable workflow's repo grants access via Settings → Actions → "Access" → "Accessible from repositories in the 'X' organization")

For Capital One: enable org-wide access on the central workflows-org repo. Consumers don't need any setup beyond `uses:`.

---

## 9. Testing reusable workflows

The challenge: you can't test a reusable workflow in isolation — it requires a caller.

**Pattern**: include a "self-test caller" in the reusable workflow's own repo:

```yaml
# In workflows-org repo: .github/workflows/_test-python-ci.yml
on:
  push:
    branches: [main]
    paths: ['.github/workflows/python-ci.yml']
  pull_request:
    paths: ['.github/workflows/python-ci.yml']

jobs:
  test-call:
    uses: ./.github/workflows/python-ci.yml      # call via relative path
    with:
      python-version: "3.11"
```

Now the central repo's CI exercises the reusable workflow on every PR to it. Combined with `act` for local iteration, that's a tight loop.

---

## 10. Cross-references

- Composite actions (the step-level reuse pattern) → [module 27](27_actions_composite_custom.md).
- OIDC-to-AWS reusable workflow example → [module 29](29_actions_oidc_aws.md).
- Org-level workflow templates (the "starter workflow" UI feature) → [module 31](31_actions_token_cost_templates.md).
- Jenkins shared libraries (the equivalent pattern in the Jenkins world) → [module 50](50_jenkins_multibranch_shared_libs.md).
- Capital One's "singular software delivery pipeline" — the org-level realization of this → [module 56](56_capital_one_devops_deep.md).
