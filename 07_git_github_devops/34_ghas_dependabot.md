# 34 — 🏦 Dependabot + dependency review action

> *"Most CVEs come in via third-party deps. Dependabot is the auto-updater; dependency-review-action is the gate."*

## Why this module exists

Dependency security is most of your supply-chain risk surface. GitHub's tooling has two prongs: **Dependabot** (alerts + auto-PRs for updates) and **dependency-review-action** (blocks PRs introducing vulnerable deps). Both come with the Code Security SKU.

---

## 1. The three Dependabot products

| | Alerts | Security updates | Version updates |
|---|---|---|---|
| What | Notifications when a vuln matches a dep in your repo | Auto-opens PRs to bump to a fixed version | Auto-opens PRs to bump to latest version on schedule |
| Cost | Free (incl. private repos with GHAS) | Free | Free (configured via `dependabot.yml`) |
| Trigger | New CVE published + dep matches | After alert + fix available | Cron schedule |

---

## 2. Configuration file

`.github/dependabot.yml`:

```yaml
version: 2

updates:
  # Python deps
  - package-ecosystem: "pip"          # also: "uv" (newer), "poetry"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "06:00"
      timezone: "America/New_York"
    open-pull-requests-limit: 10
    groups:
      ml-deps:
        patterns:
          - "torch*"
          - "transformers"
          - "huggingface*"
      dev-deps:
        dependency-type: "development"
    ignore:
      - dependency-name: "fastapi"
        versions: ["1.x"]           # don't update fastapi to 1.x yet
      - dependency-name: "*"
        update-types: ["version-update:semver-major"]   # never auto-bump majors

  # GitHub Actions (action versions in workflow files)
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"

  # Docker base images
  - package-ecosystem: "docker"
    directory: "/"
    schedule:
      interval: "weekly"

  # Terraform modules
  - package-ecosystem: "terraform"
    directory: "/infra"
    schedule:
      interval: "weekly"
```

Supported ecosystems (2026): bun, bundler, cargo, composer, devcontainers, docker, docker-compose, dotnet-sdk, elm, gitsubmodule, github-actions, gomod, gradle, helm, maven, mix, npm, nuget, pip, pub, swift, terraform, uv.

---

## 3. Grouped updates

Default: one PR per dep. Quickly becomes noise.

**Grouped updates** (since 2023) combine related deps into one PR:

```yaml
groups:
  ml-deps:
    patterns: ["torch*", "transformers", "huggingface*"]
    update-types: ["minor", "patch"]
  test-deps:
    patterns: ["pytest*", "ruff", "mypy"]
  security:
    applies-to: security-updates
    patterns: ["*"]                  # ALL security updates in one PR
```

Recommendation: group dev deps together, group ML libs together, group security updates separately (so they merge fast).

---

## 4. Dependency review action

Run on every PR; surfaces what dependencies the PR changes + their CVE status. Optionally blocks PR if vulnerable deps added.

```yaml
# .github/workflows/dependency-review.yml
name: Dependency review
on:
  pull_request:

permissions:
  contents: read
  pull-requests: write

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/dependency-review-action@v4
        with:
          fail-on-severity: high          # block PR if any high+ CVE
          allow-licenses: Apache-2.0, MIT, BSD-2-Clause, BSD-3-Clause, ISC
          deny-licenses: GPL-3.0, AGPL-3.0
          comment-summary-in-pr: always
          warn-only: false                # block, don't just warn
```

What it does:
1. Diffs `package-lock.json` / `uv.lock` / `requirements.txt` / etc. between base and PR.
2. Identifies added or upgraded deps.
3. Checks each against GitHub Advisory Database for CVEs.
4. Checks against license allowlist.
5. Posts a summary comment + blocks merge if `fail-on-severity` triggered.

This is the bank's gate: no new vulnerable deps. No GPL deps in proprietary code. Combine with branch protection requiring this status check.

---

## 5. The advisory database

GitHub Advisory Database (publicly queryable): https://github.com/advisories. Contains CVEs from NVD + GitHub-reviewed advisories. Sources:
- NVD (the US National Vulnerability DB)
- Security advisories published on individual GitHub repos
- Curated submissions

Each advisory has:
- CVE ID + GHSA ID (GitHub Security Advisory)
- Affected package + versions
- Patched versions
- Severity (CVSS)
- Description + references

Dependabot watches this database; new advisory + your dep affected → alert + (if configured) auto-PR.

---

## 6. Triaging alerts

GitHub UI: repo Security → Dependabot alerts. Per alert:
- Severity
- Affected package + version
- Patched in
- Status (open / fixed / dismissed / closed)
- Auto-fix PR (if any)

Dismissal reasons:
- "Tolerable risk" — accept, document why
- "False positive" — Dependabot wrong
- "Inaccurate" — advisory wrong
- "Used in tests only"
- "No bandwidth to fix"

Dismissals require justification; for Capital One, also probably require security-team review.

Org-wide view: Org Security → Dependabot. Filter by repo, severity, age. Track MTTR per severity for compliance reporting.

---

## 7. The Renovate alternative

[Renovate](https://www.mend.io/renovate/) (Mend, OSS + commercial) is an alternative to Dependabot with more granular controls:

- Per-dep schedule (e.g., update torch only quarterly)
- Auto-merge low-risk updates without PR review
- Better monorepo support
- Larger ecosystem of platforms

Some teams use Renovate instead of Dependabot. Both work. GitHub-native = Dependabot; if you need its specific features = Renovate.

---

## 8. The Dependabot PR review pattern

A typical Dependabot PR:
- Title: `chore(deps): bump foo from 1.2.3 to 1.2.4`
- Body: changelog from the dep's repo + commit list
- Labels: `dependencies`, `python` (or ecosystem)

To accept the bump:
- Verify CI is green
- Read the changelog
- For minor/patch security updates with green CI: auto-merge OK
- For major updates: requires manual review (breaking changes possible)

**Auto-merge for low-risk Dependabot PRs**:

```yaml
# .github/workflows/dependabot-auto-merge.yml
name: Dependabot auto-merge
on:
  pull_request:

permissions:
  contents: write
  pull-requests: write

jobs:
  auto-merge:
    if: github.actor == 'dependabot[bot]'
    runs-on: ubuntu-latest
    steps:
      - uses: dependabot/fetch-metadata@v2
        id: meta
      - if: contains(fromJSON('["version-update:semver-patch", "version-update:semver-minor"]'), steps.meta.outputs.update-type)
        run: gh pr merge --auto --squash "$PR_URL"
        env:
          PR_URL: ${{ github.event.pull_request.html_url }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

Auto-merge patches + minors with green CI. Major bumps require human review.

For bank: probably only auto-merge **security** updates of patch/minor severity; everything else gets human eyes.

---

## 9. Dependabot scoped to GHAS-only checks

If you don't have full Code Security but you DO have Dependabot Alerts (free), you still get:
- Alerts in repo Security tab
- Auto-suggested PRs (with green-CI-passes requirement)

Without GHAS, **dependency-review-action** still works as a PR-time check (the action is free; it reads the public Advisory DB). Block merges on vulnerable deps even without paying for Code Security.

---

## 10. Cross-references

- Branch protection requiring dependency review status → [module 11](11_branch_protection_rulesets_codeowners.md).
- CodeQL for code-level vulns → [module 33](33_ghas_codeql_autofix.md).
- SBOM generation + supply chain attestations → [module 35](35_ghas_sbom_slsa_attestations.md).
- Auto-merging Dependabot PRs (the workflow above) → also see [module 10](10_prs_code_review_merge.md) auto-merge.
- Pinning marketplace actions + Dependabot for `.github/workflows/*.yml` → [module 22](22_actions_marketplace_expressions.md).
