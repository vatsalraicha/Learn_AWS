# 31 — 🏦 GITHUB_TOKEN scoping, cost optimization, org workflow templates

> *"The platform-engineer lens: the things you do at org level that every repo inherits — token defaults, runner minute caps, starter workflows."*

## Why this module exists

Three platform-level levers that aren't single-repo concerns: how the auto-provisioned `GITHUB_TOKEN` is scoped (security), how Actions spend doesn't run away (cost), and how every new repo starts with sane CI (templates).

---

## 1. `GITHUB_TOKEN` — the auto-provisioned credential

Every workflow run gets a `secrets.GITHUB_TOKEN` automatically. It:
- Is generated at workflow start, expires at workflow end (max 24h).
- Authenticates as `github-actions[bot]`.
- Is scoped per workflow's `permissions:` block.
- Can ONLY operate on the running repo (for cross-repo writes, use GitHub App tokens — see [module 12](12_auth_pat_ssh_signing.md)).

```yaml
permissions:
  contents: read           # clone, read files
  pull-requests: write     # comment on / approve PRs
  issues: write
  id-token: write          # request OIDC JWT (for cloud auth)
  packages: write          # push to GitHub Packages
  pages: write             # deploy to GitHub Pages
  deployments: write       # create deployments
  checks: write            # post check runs
  security-events: write   # upload SARIF (CodeQL, etc.)
  statuses: write          # post commit statuses
  attestations: write      # generate artifact attestations
  actions: read            # read workflow info
```

Or to be exhaustive:

```yaml
permissions: read-all      # all read perms, no write
permissions: write-all     # all write perms (avoid!)
permissions: {}            # NONE — token has no perms
```

---

## 2. The 2026 default: read-only

Per the **Actions 2026 Security Roadmap**, the default `GITHUB_TOKEN` permissions on **new repos** are now read-only across all scopes. This means workflows that previously worked silently (e.g., a PR-comment action) now fail without explicit permissions grants.

To configure org-wide:
- Org Settings → Actions → General → Workflow permissions:
  - "Read repository contents and packages permissions" (default for new repos)
  - or "Read and write permissions" (legacy default — switch off for new orgs)
- Also: "Allow GitHub Actions to create and approve pull requests" — usually OFF; allowing it is a privilege-escalation vector.

To override per workflow:

```yaml
permissions:
  contents: read
  pull-requests: write     # explicit grant
```

To override per job (most-restrictive principle):

```yaml
jobs:
  read-only-job:
    permissions:
      contents: read       # this job: read-only
    runs-on: ubuntu-latest
  write-job:
    permissions:
      contents: write
      pull-requests: write
    runs-on: ubuntu-latest
```

---

## 3. Cost optimization — the levers

GitHub Actions billing is **per-minute on private repos**. The cost levers, in order of impact:

### A. Concurrency cancellation

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.head_ref || github.ref }}
  cancel-in-progress: true
```

A developer pushes 5 commits in 5 minutes → 5 CI runs by default. With cancellation: only the last completes. **Save 80%** on busy repos.

### B. Path filters

```yaml
on:
  push:
    paths-ignore: ['docs/**', '**/*.md']
  pull_request:
    paths: ['src/**', 'tests/**', 'pyproject.toml', 'uv.lock']
```

Doc-only changes don't trigger CI. **Save 10–30%** depending on doc-change frequency.

### C. Matrix pruning

Skip combinations that don't add value:

```yaml
strategy:
  matrix:
    python: ["3.11", "3.12"]
    os: [ubuntu-latest, macos-latest, windows-latest]
    exclude:
      - python: "3.11"
        os: macos-latest      # tested elsewhere
```

Or test only `ubuntu-latest` on PR; full matrix on main + nightly. **Save 50%** on cross-platform matrix overuse.

### D. Caching

`actions/cache` + `setup-*` cache options cut dep-install time. A Python project with `pip install -e ".[dev]"` typically takes 60s; cached it's 5s. **Save 30–50%** of total CI time.

### E. Runner sizing

GitHub-hosted standard: 4 vCPU. For test-suite-bound jobs, larger runners (16 vCPU, 8× faster but ~4× cost) are often net-cheaper per CI completion.

```yaml
runs-on: org-larger-runner-16cpu
```

Counter-intuitively: 16-cpu runner for 5 min costs less than 4-cpu runner for 20 min on jobs with parallelizable work (Bazel, large pytest suites with `-n auto`).

### F. Don't run macOS / Windows when not needed

| Runner | Minute multiplier |
|---|---|
| Linux | 1× |
| Windows | 2× |
| macOS | 10× |

`macos-latest` is **10× more expensive** per minute. Run macOS only when actually building for macOS (and even then, only on `push` to main, not every PR).

### G. Skip CI for low-value commits

```bash
git commit -m "chore: bump dep [skip ci]"
```

Or via PR title `[skip actions]`. Useful for dependency bumps you've already validated.

### H. Self-hosted at scale

For 100k+ minutes/month at a particular workload pattern (GPU training, big Docker builds), self-hosted runners on cheap spot capacity beat GitHub-hosted on raw $/minute. See [module 28](28_actions_self_hosted_arc_gpu.md).

---

## 4. Cost monitoring

```bash
# Per-workflow minutes used
gh api /orgs/capitalone/settings/billing/actions
gh api /repos/capitalone/cool-repo/actions/cache/usage
```

GitHub UI: Org Settings → Billing & licensing → Actions. Shows minutes per repo, per runner type, per month.

For larger orgs: integrate via GitHub Webhooks + Datadog/Splunk for per-workflow attribution. Tag workflows with `team` labels to enable team-level chargeback.

Hard caps via spending limits:
- Org-level spending limit ($N/month — Actions stops running when hit).
- Per-repo soft alerts via custom Actions to email teams approaching their budget.

---

## 5. Workflow templates (org-level starter workflows)

When a user creates a new workflow in any repo in your org, GitHub can show **starter workflows** specific to your org.

Setup: in a special repo named `.github` in your org (e.g., `capitalone/.github`), under `workflow-templates/`:

```
capitalone/.github/
└── workflow-templates/
    ├── python-ci.yml              # the workflow YAML
    ├── python-ci.properties.json  # metadata
    ├── python-ci.svg              # icon
    ├── docker-build-push.yml
    ├── docker-build-push.properties.json
    └── ...
```

`python-ci.properties.json`:

```json
{
  "name": "Python CI",
  "description": "Lint + test + build for Python projects (Capital One standard)",
  "iconName": "python-ci",
  "categories": ["Python"],
  "filePatterns": ["pyproject.toml"]
}
```

When someone goes to Actions → New workflow on a repo with `pyproject.toml`, the "Python CI" template appears under "Suggested by ..." at the top.

Inside `python-ci.yml`, reference your central reusable workflows so the user gets the canonical pipeline by default:

```yaml
on: [push, pull_request]

jobs:
  ci:
    uses: capitalone/workflows-org/.github/workflows/python-ci.yml@v3
    with:
      python-version: "3.12"
```

Result: new ML repo → engineer clicks "Python CI" template → 5 lines committed → full Capital One CI inherited.

---

## 6. Required workflows (Enterprise-only)

GitHub Enterprise Cloud has **required workflows** — org admins can require specific workflows run on every PR or push in selected repos, with no opt-out.

Setup: Org Settings → Actions → Required workflows → Add. Point to a workflow file in a specific repo + ref.

Use case: enforce a "security scan must run" workflow across all repos, where individual repo owners can't disable it.

This is the strongest org-wide enforcement. Combine with branch protection requiring those status checks → no PR merges without org-required scans green.

---

## 7. Org-level allowlist for marketplace actions

Settings → Actions → General → "Allow actions and reusable workflows":

| Option | Behavior |
|---|---|
| Allow all actions and reusable workflows | Open — convenient for OSS-style orgs |
| Disable actions | Actions disabled entirely |
| Allow [org] actions and reusable workflows | Only actions from this org are allowed |
| Allow [org] actions, and select non-[org] actions | Org actions + explicit allowlist of marketplace actions |

For Capital One: probably "Allow Capital One actions, and select non-Capital One actions" — with an explicit allowlist that's curated by the platform team (actions/checkout, actions/setup-*, aws-actions/*, etc.).

Allowlist syntax:

```
actions/*,
github/*,
aws-actions/*,
docker/setup-buildx-action@v3,
peaceiris/actions-gh-pages@*
```

Wildcards on owners ok; can pin per-action by version.

---

## 8. The platform-engineer Sr Lead checklist

For Capital One scale, your org's GitHub Actions configuration should include:

- ✅ Default `GITHUB_TOKEN` permissions = read-only (org-level setting)
- ✅ Actions allowlist enforced (only blessed marketplace actions)
- ✅ Self-hosted runner groups separated by trust tier (default / large / gpu / prod-deploy)
- ✅ Required workflows for security scans on every PR
- ✅ Org-level starter workflow templates for common project types
- ✅ Central `workflows-org` repo with reusable workflows tagged semver
- ✅ Central `actions-org` repo with composite + JS + Docker actions
- ✅ Dependabot enabled for `.github/workflows/*.yml` action version bumps
- ✅ Spending limit + monitoring dashboards
- ✅ Audit log streaming to SIEM
- ✅ Quarterly review of bypass actors on Rulesets

---

## 9. Cross-references

- Reusable workflows (the central repo pattern) → [module 26](26_actions_reusable_workflows.md).
- ARC + runner groups → [module 28](28_actions_self_hosted_arc_gpu.md).
- Branch protection + Rulesets → [module 11](11_branch_protection_rulesets_codeowners.md).
- Audit log + SIEM streaming → [module 36](36_compliance_sso_scim_audit.md).
- Dependabot for actions versions → [module 34](34_ghas_dependabot.md).
