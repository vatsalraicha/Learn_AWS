# 19 — Repo templates, ADRs, docs, Conventional Commits, release-please

> *"The InnerSource pattern is: standardize the parts that are the same across teams; let teams customize the parts that genuinely differ. Templates + ADRs + Conventional Commits are how."*

## Why this module exists

At Capital One scale (7,000 engineers), every new repo must look the same as the last one or productivity tanks. Templates enforce shape; ADRs preserve decisions; conventional commits enforce a vocabulary; release-please automates versioning. This module is the standardization toolkit.

---

## 1. Template repositories

GitHub lets you mark a repo as a **template** (Settings → General → check "Template repository"). Then "Use this template" button shows up; one click creates a new repo with the template's contents AND no shared history.

```bash
gh repo create capitalone/new-ml-svc \
  --template capitalone/python-ml-template \
  --private \
  --add-readme \
  --clone
```

What goes in the template:
- Standard repo files (LICENSE, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, .editorconfig — see [module 08](08_repo_setup_standards.md))
- Issue + PR templates
- `.github/workflows/` skeleton (ci.yml, release.yml using reusable workflows)
- `.github/CODEOWNERS` with default owners
- `pyproject.toml` skeleton
- `.pre-commit-config.yaml`
- `Makefile` with standard targets
- `README.md` with placeholders
- `docs/adr/0001-record-architecture-decisions.md` (the first ADR is "we use ADRs")
- Sometimes a `cookiecutter.json` for interactive customization

For more dynamic templates, **cookiecutter** is the next step up — Jinja-templated repos with variable substitution:

```bash
cookiecutter capitalone/cookiecutter-python-ml
# Service name [my-svc]: token-service
# Author [...]:
# Use GPU runners (yes/no) [no]: yes
# AWS account ID for prod [...]: 123456789012
```

Cookiecutter generates a fully-configured repo. Combine with `gh repo create` to push the result to GitHub.

---

## 2. Architecture Decision Records (ADRs)

An ADR is a 1–2 page document recording one architectural decision: what was decided, why, when, with what trade-offs, and what alternatives were considered.

Format (Michael Nygard's original):

```markdown
# ADR 0007: Use SageMaker Pipelines for training orchestration

Date: 2026-05-21
Status: Accepted
Deciders: @vraicha, @platform-team-lead

## Context
We need to orchestrate a 4-step ML training pipeline (data prep → train → eval → register).
Options considered: Airflow (MWAA), Step Functions, SageMaker Pipelines, Jenkins pipeline.

## Decision
Use SageMaker Pipelines because:
- Native integration with SageMaker training jobs + Model Registry
- IAM role per-step, no shared credentials
- Built-in lineage tracking (SR 11-7 audit requirement)
- Step Functions adds extra service layer with no benefit for ML-only pipelines

## Consequences
+ Tight coupling to AWS / SageMaker (acceptable — we're AWS-only)
+ Lineage and audit trails for free
+ Native model registry integration
- Local testing harder than Airflow (mitigated by Step Function emulator for integration tests)
- Smaller community than Airflow

## Alternatives
- **Airflow**: more flexible, multi-cloud; but C1's published MLOps spine uses Step Functions, not Airflow
- **Step Functions**: would need additional state machine on top of SageMaker calls
- **Jenkins**: not appropriate for long-running training jobs
```

### Where ADRs live

`docs/adr/0001-record-architecture-decisions.md` (numbered sequentially). Statuses: **Proposed → Accepted / Rejected → Superseded by ADR #N**.

The **adr-tools** CLI helps:

```bash
brew install adr-tools
adr init docs/adr
adr new "Use SageMaker Pipelines for training"   # creates next-numbered ADR
adr link 7 supersedes 3                          # ADR 7 supersedes ADR 3
```

For Capital One InnerSource: ADRs are the documentation of choices that other teams might rediscover. "Why didn't we use Airflow?" is a question that gets asked by every new ML team — ADR 0007 answers it once.

---

## 3. Documentation sites

For repos with non-trivial docs:

| Tool | When |
|---|---|
| **README only** | Single-purpose libs |
| **Wiki (in-GitHub)** | Light docs; cross-team discoverability low |
| **GitHub Pages + MkDocs Material** | Default for OSS Python projects; markdown-native |
| **GitHub Pages + Docusaurus** | Default for OSS JS projects; MDX support |
| **Sphinx + Read the Docs** | Python projects needing API autodocs |
| **Confluence** | Enterprise reality at most banks |
| **Backstage TechDocs** | Backstage-using orgs (catalog + docs together) |

For Capital One: probably Backstage for the catalog, Confluence for prose, MkDocs Material for in-repo technical docs.

### MkDocs Material example

```yaml
# mkdocs.yml
site_name: Token Service
theme:
  name: material
  palette:
    primary: blue
nav:
  - Home: index.md
  - Architecture:
    - Overview: arch/overview.md
    - ADRs: adr/index.md
  - API: api.md
  - Operations: ops.md
plugins:
  - search
  - mkdocstrings
  - mermaid2
```

Deploy via GitHub Actions:

```yaml
- uses: actions/setup-python@v5
- run: pip install mkdocs-material mkdocstrings[python] mkdocs-mermaid2-plugin
- run: mkdocs gh-deploy --force
```

---

## 4. Conventional Commits

A specification for commit messages that enables **machine-readable changelog generation**.

Format:
```
<type>(<scope>): <subject>

<body>

<footer>
```

Types (the standard set):

| Type | When | Triggers (release-please) |
|---|---|---|
| `feat` | New feature | MINOR version bump |
| `fix` | Bug fix | PATCH version bump |
| `docs` | Docs only | No version bump |
| `style` | Formatting, no code change | No bump |
| `refactor` | Code restructure, no behavior change | No bump |
| `perf` | Performance improvement | PATCH |
| `test` | Add/update tests | No bump |
| `build` | Build system changes | No bump |
| `ci` | CI config changes | No bump |
| `chore` | Maintenance | No bump |
| `revert` | Revert a previous commit | Depends on what was reverted |

**Breaking changes**: append `!` after type/scope OR add `BREAKING CHANGE:` in the footer. Triggers a MAJOR version bump.

Examples:

```
feat(auth): add OIDC token caching

Adds an in-memory LRU cache for OIDC tokens with a 5-minute TTL.
Reduces calls to STS by ~80% for repeated requests within the TTL.

Closes #142
```

```
fix(api): handle null user_id in /predict

Previously returned 500 on null user_id; now returns 400 with a clear error.
```

```
feat(api)!: rename /predict to /v2/predict

BREAKING CHANGE: The /predict endpoint is renamed to /v2/predict.
The old endpoint returns 410 Gone. Clients must update.
```

Enforce via:
- **commitlint** (`@commitlint/cli`) as a `commit-msg` hook
- **GitHub Action** to lint PR title/commits on push

```yaml
- uses: amannn/action-semantic-pull-request@v5
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  with:
    types: |
      feat
      fix
      docs
      ...
```

---

## 5. release-please — the automation

Google's [release-please](https://github.com/googleapis/release-please) parses Conventional Commits and creates a "Release PR" with:
- Updated version in `pyproject.toml` (or `package.json`, etc.)
- Updated CHANGELOG.md (autogenerated from commits)
- A pending tag in the PR description

When you merge the Release PR, release-please:
- Tags the release on main
- Creates a GitHub Release with the changelog
- Optionally publishes to npm / PyPI / etc.

Setup as a GitHub Action:

```yaml
# .github/workflows/release-please.yml
name: release-please
on:
  push:
    branches: [main]

permissions:
  contents: write
  pull-requests: write

jobs:
  release-please:
    runs-on: ubuntu-latest
    steps:
      - uses: googleapis/release-please-action@v4
        with:
          release-type: python
          package-name: my-ml-service
```

What you get:
- Every merge to main → release-please updates a draft Release PR.
- Multiple merges accumulate in one Release PR.
- When ready to release, merge the Release PR → tag + GitHub Release auto-created.
- No more manual version bumps. No more "what's in this release?" debate — the changelog IS the answer.

Per-repo or per-package config in `.release-please-config.json`:

```json
{
  "release-type": "python",
  "packages": {
    ".": {
      "package-name": "my-ml-service",
      "include-component-in-tag": false
    }
  },
  "changelog-sections": [
    { "type": "feat",     "section": "Features" },
    { "type": "fix",      "section": "Bug Fixes" },
    { "type": "perf",     "section": "Performance" },
    { "type": "deps",     "section": "Dependencies" },
    { "type": "revert",   "section": "Reverts" },
    { "type": "docs",     "section": "Documentation", "hidden": true },
    { "type": "style",    "hidden": true },
    { "type": "chore",    "hidden": true },
    { "type": "refactor", "hidden": true },
    { "type": "test",     "hidden": true },
    { "type": "build",    "hidden": true },
    { "type": "ci",       "hidden": true }
  ]
}
```

Alternatives: **semantic-release** (npm-focused, more configurable, more opinionated about npm publish flow), **Changesets** (per-package versioning in monorepos), **commitizen** (similar; Python-friendly).

---

## 6. Putting it together — the InnerSource template

A Capital One-grade template repo includes:

- ✅ Conventional Commits enforced (commitlint hook + GH Action)
- ✅ release-please workflow committed
- ✅ Standard `.github/workflows/` (reusable from `capitalone/workflows-org` repo — see [module 26](26_actions_reusable_workflows.md))
- ✅ CODEOWNERS with team placeholders
- ✅ `docs/adr/0001-record-architecture-decisions.md` (so ADRs start day one)
- ✅ Pre-commit config with bank-standard tools (gitleaks, ruff, mypy, nbstripout)
- ✅ Dependabot config (auto-grouped)
- ✅ SECURITY.md pointing to internal vulnerability disclosure email
- ✅ `pyproject.toml` with bank-standard tool configs (ruff, mypy, pytest)
- ✅ Bare-bones FastAPI service skeleton OR ML training skeleton (template variant per use case)
- ✅ Makefile with standard targets

Every new repo created from the template inherits the lot. Drift mitigated because reusable workflows are referenced by tag (e.g., `@v3`), not copied — when the platform team updates the central workflow, every consumer picks it up on next run.

---

## 7. Cross-references

- The repo file skeleton in detail → [module 08](08_repo_setup_standards.md).
- Reusable workflows (the heart of the templating story) → [module 26](26_actions_reusable_workflows.md).
- Pre-commit config + hooks → [module 40](40_precommit_reproducibility_refactor.md).
- Tag-based versioning + hatch-vcs → [module 18](18_python_ml_repo_structure.md).
- ADR practice at Capital One scale (InnerSource governance) → [module 56](56_capital_one_devops_deep.md).
