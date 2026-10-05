# 20 — GitHub Actions: workflow YAML, events, triggers

> *"A workflow is a YAML file that says: when X event happens, run these jobs on these runners. Internalize that sentence and the rest is detail."*

## Why this module exists

GitHub Actions is the CI/CD system you'll use most days as a Sr Lead at a modern shop. The grammar is YAML; the semantics are events → workflows → jobs → steps → actions. This module covers the events + triggers layer — what causes a workflow to run, and the patterns for each.

---

## 1. The anatomy of a workflow file

```yaml
# .github/workflows/ci.yml
name: CI                                # human-readable workflow name (shown in UI)

on:                                     # the trigger(s)
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:                            # token scopes (default read-only in 2026)
  contents: read
  pull-requests: write

concurrency:                            # concurrency group (cancel duplicates)
  group: ci-${{ github.ref }}
  cancel-in-progress: true

env:                                    # workflow-level env vars
  PYTHON_VERSION: "3.11"

jobs:
  test:                                 # job ID
    name: Run tests                     # display name
    runs-on: ubuntu-latest              # which runner
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      - run: pip install -e ".[dev]"
      - run: pytest
```

Files live under `.github/workflows/`. One workflow per file. File name (without `.yml`) is what's referenced when triggering manually.

---

## 2. Events — the catalog

| Event | When | Use for |
|---|---|---|
| `push` | Commit pushed to a branch (or tag) | CI on main, release on tag |
| `pull_request` | PR opened, updated, or labeled (etc.) | CI on every PR |
| `pull_request_target` | Like PR but runs in target repo's context (sees secrets!) | Use with caution; for trusted-PR jobs |
| `schedule` | Cron schedule | Nightly builds, periodic reports |
| `workflow_dispatch` | Manual via UI or `gh workflow run` | On-demand operations |
| `repository_dispatch` | External webhook via API | Cross-repo triggers, external systems |
| `workflow_call` | Called by another workflow | **Reusable workflows** (see [module 26](26_actions_reusable_workflows.md)) |
| `release` | GitHub Release created/published | Trigger downstream actions on release |
| `issues` | Issue opened/edited/closed/labeled | Issue triage automation |
| `issue_comment` | Comment on issue or PR | ChatOps |
| `pull_request_review` | Review submitted | Auto-merge on approval |
| `deployment` / `deployment_status` | Deployment created or completed | Notify external systems |
| `discussion` | Discussion created (if enabled) | Forum automation |
| `merge_group` | Merge queue evaluating a tentative commit | Run CI on queued group |
| `registry_package` | Package published to GitHub Packages | Trigger downstream consumers |
| `check_run` / `check_suite` | Status check started/completed | Workflow chaining |

The full list is at [docs.github.com/actions/reference/events-that-trigger-workflows](https://docs.github.com/actions/reference/events-that-trigger-workflows).

---

## 3. Filtering — branches, tags, paths

```yaml
on:
  push:
    branches:
      - main
      - 'release/**'        # glob
    branches-ignore:
      - 'gh-pages'
    tags:
      - 'v*.*.*'           # any v-prefixed semver tag
    paths:
      - 'src/**'
      - 'pyproject.toml'
    paths-ignore:
      - 'docs/**'
      - '*.md'
  pull_request:
    branches: [main]
    types: [opened, synchronize, reopened, ready_for_review]   # default trims unwanted PR events
```

Filter combinations:
- **Both `branches` and `tags`** in same `push` block → AND, not OR. Use separate blocks if you mean OR.
- **`paths` filters** only matter for `push` and `pull_request` — they prevent the workflow from running unless changed files match.

`paths-ignore` is the under-used one. Skip CI when only docs change:

```yaml
on:
  pull_request:
    paths-ignore: ['docs/**', '**/*.md']
```

Or invert — only run on relevant changes:

```yaml
on:
  pull_request:
    paths: ['src/**', 'tests/**', 'pyproject.toml', 'uv.lock', '.github/workflows/ci.yml']
```

---

## 4. Pull request triggers — the safety boundary

The `pull_request` event runs in the **fork's context** for PRs from forks. Important consequences:

- **No secrets are available** to PRs from forks (prevents secret exfiltration from malicious PRs).
- **GITHUB_TOKEN has read-only permissions** for PRs from forks (per 2026 default).
- The workflow runs from the PR's branch (not the base branch).

The `pull_request_target` event runs from the **base branch** — gets secrets and write tokens. **Dangerous** if you `checkout` the PR's code and run it (which is the common mistake → arbitrary code execution with secrets in scope). Only use `pull_request_target` for:

- Auto-labeling PRs based on path
- Adding comments / assigning reviewers
- Things that don't execute PR-author-controlled code

**Never** `actions/checkout@v6 with: ref: ${{ github.event.pull_request.head.sha }}` inside a `pull_request_target` workflow that has secret access. That's the canonical CVE pattern.

For safer "needs secrets + needs PR code" jobs: use a **manual approval gate** via `environments` (see [module 30](30_actions_environments_protection.md)) so a maintainer approves before running.

---

## 5. Schedule — cron syntax

```yaml
on:
  schedule:
    - cron: '0 4 * * 1-5'   # 4am UTC, weekdays
    - cron: '*/30 * * * *'  # every 30 minutes (note: GitHub clamps to 5-min minimum)
```

Cron syntax: standard 5-field (minute hour day-of-month month day-of-week). All times in UTC. **GitHub does NOT guarantee exact timing** — heavily loaded periods can delay scheduled runs by minutes. Schedule for off-peak if you need closer-to-on-time.

Scheduled workflows run only on the **default branch** (not on feature branches). They use `github.workflow_sha` of the default branch's HEAD.

---

## 6. `workflow_dispatch` — manual triggers

```yaml
on:
  workflow_dispatch:
    inputs:
      environment:
        description: "Target environment"
        required: true
        type: choice
        options: [dev, staging, prod]
      version:
        description: "Version to deploy"
        required: true
        type: string
      dry_run:
        description: "Dry-run mode"
        type: boolean
        default: true
```

Triggered via:
- GitHub UI: Actions tab → workflow → "Run workflow" button
- CLI: `gh workflow run deploy.yml -f environment=staging -f version=1.2.3 -f dry_run=false`

Inputs are available as `${{ inputs.environment }}` in the workflow.

This is THE pattern for "I need to deploy now" without a code change.

---

## 7. `repository_dispatch` — external trigger

```yaml
on:
  repository_dispatch:
    types: [retrain-model, run-validation]
```

Triggered via API:

```bash
gh api repos/org/repo/dispatches -f event_type=retrain-model \
  -f client_payload='{"model": "fraud-detector", "version": "1.4.0"}'
```

Use cases:
- Cross-repo CI chains
- External system triggers (Snowflake task, Step Functions completion)
- Slack /command → Lambda → repository_dispatch → workflow

In the workflow:

```yaml
- run: echo "Retraining ${{ github.event.client_payload.model }}"
```

---

## 8. `workflow_call` — reusable workflows (sneak peek)

```yaml
# .github/workflows/python-ci-reusable.yml
on:
  workflow_call:
    inputs:
      python-version:
        type: string
        default: "3.11"
    secrets:
      PYPI_TOKEN:
        required: false
```

Then call it from another workflow:

```yaml
# .github/workflows/ci.yml
jobs:
  python-ci:
    uses: capitalone/workflows-org/.github/workflows/python-ci-reusable.yml@v3
    with:
      python-version: "3.11"
    secrets:
      PYPI_TOKEN: ${{ secrets.PYPI_TOKEN }}
```

Full pattern in [module 26](26_actions_reusable_workflows.md).

---

## 9. Multiple events in one workflow

```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 6 * * *'
  workflow_dispatch:
```

When triggered, `github.event_name` tells you which event:

```yaml
- if: github.event_name == 'pull_request'
  run: echo "Running on PR"
- if: github.event_name == 'schedule'
  run: echo "Nightly build"
- if: github.event_name == 'workflow_dispatch'
  run: echo "Manual: env=${{ inputs.environment }}"
```

---

## 10. The `github` context — what's available

A workflow always has `github.*` context with metadata about the trigger:

```yaml
- run: |
    echo "Event: ${{ github.event_name }}"
    echo "SHA: ${{ github.sha }}"
    echo "Ref: ${{ github.ref }}"               # refs/heads/main or refs/pull/123/merge
    echo "Ref name: ${{ github.ref_name }}"     # main or 123/merge
    echo "Actor: ${{ github.actor }}"           # the user who triggered the event
    echo "Repo: ${{ github.repository }}"       # org/name
    echo "Workflow: ${{ github.workflow }}"
    echo "Run ID: ${{ github.run_id }}"
    echo "Run number: ${{ github.run_number }}"
    echo "Run attempt: ${{ github.run_attempt }}"
```

For `pull_request` events specifically:
- `github.event.pull_request.number`
- `github.event.pull_request.head.sha`   ← the PR's branch tip
- `github.event.pull_request.base.sha`   ← what it's based on
- `github.event.pull_request.head.ref`
- `github.event.pull_request.user.login`
- `github.event.pull_request.draft`

Full schema: [docs.github.com/webhooks-and-events/webhooks/webhook-events-and-payloads](https://docs.github.com/webhooks-and-events/webhooks/webhook-events-and-payloads).

---

## 11. Skipping CI

In a commit message OR PR title, include `[skip ci]` (or `[ci skip]`, `[skip actions]`, etc.) and the workflow skips. Useful for doc-only changes, dependency bumps you've already validated, etc.

```bash
git commit -m "docs: fix typo [skip ci]"
```

Skip rule applies to `push` events. For PR events, the workflow runs anyway (because the PR title/commits may be different from the head commit message).

---

## 12. Cross-references

- Runners (where the jobs run) → [module 21](21_actions_jobs_steps_runners.md).
- Expressions + contexts in depth → [module 22](22_actions_marketplace_expressions.md).
- The `merge_group` event for merge queues → [module 10](10_prs_code_review_merge.md).
- Reusable workflows via `workflow_call` → [module 26](26_actions_reusable_workflows.md).
- Manual approvals + environments → [module 30](30_actions_environments_protection.md).
