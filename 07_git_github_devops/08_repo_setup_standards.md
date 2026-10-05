# 08 — Repository setup standards

> *"A new repo without a README, LICENSE, and CODEOWNERS is a debt you'll pay back with interest."*

## Why this module exists

Every repo at a regulated bank has a baseline of files: a README that explains what it is, a LICENSE that defines reuse, a CONTRIBUTING that tells outsiders how to participate, a CODE_OF_CONDUCT that defines norms, issue/PR templates that route work efficiently, a SECURITY policy for vulnerability reporting, and CODEOWNERS to route reviews. This module covers the baseline. Specifics on CODEOWNERS + branch protection live in [module 11](11_branch_protection_rulesets_codeowners.md).

---

## 1. The standard repo skeleton

```
my-ml-service/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml
│   │   └── release.yml
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   ├── feature_request.md
│   │   └── config.yml
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── CODEOWNERS
│   ├── dependabot.yml
│   └── FUNDING.yml                    (OSS only)
├── docs/
│   ├── architecture/
│   │   └── adr-0001-record-decisions.md
│   └── README.md
├── src/                                 (or use src/<pkg> layout — see module 18)
├── tests/
├── .gitignore
├── .gitattributes
├── .editorconfig
├── .pre-commit-config.yaml
├── pyproject.toml
├── CHANGELOG.md
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── LICENSE
├── README.md
└── SECURITY.md
```

GitHub auto-detects files in `.github/`, root, or `docs/` and surfaces them in the UI. Conventional locations matter — a `LICENSE` in root gets a license badge; a `LICENSE` in `docs/legal/` doesn't.

---

## 2. README — the front door

Five sections, in order, no exceptions:

1. **One-paragraph what + why** — what does this do, why should I care
2. **Quick start** — copy-pasteable install + run-it commands; should work in < 60 seconds
3. **Usage** — minimum-viable code snippet; link to docs site for deeper
4. **Architecture** — one diagram (mermaid) + one paragraph
5. **Contributing / Development** — link to CONTRIBUTING.md; quick "run tests" command

GitHub renders mermaid diagrams in markdown natively — use them.

```markdown
## Architecture

\`\`\`mermaid
flowchart LR
    Client --> APIGateway --> Lambda
    Lambda --> SageMakerEndpoint
    Lambda --> DynamoDB
    SageMakerEndpoint --> S3[(Model Artifact)]
\`\`\`
```

For ML repos specifically, add:
- **Model card** section: what model, trained on what, intended use, known limitations, fairness considerations, contact for issues. Link to a separate `MODEL_CARD.md` if it's long.

---

## 3. LICENSE — the legal answer

| License | When |
|---|---|
| **Apache-2.0** | Most permissive corporate-friendly default. Includes patent grant. Capital One Hygieia + Cloud Custodian use this. |
| **MIT** | Permissive, ultra-simple, no patent grant. Common in JS world. |
| **BSD-3-Clause** | Permissive + advertising clause. |
| **GPL-3.0** | Copyleft. Anything that links must also be GPL. **Don't use for libraries** unless you intend that. |
| **MPL-2.0** | Weak copyleft. Mozilla's compromise. |
| **No LICENSE** | **Legally restrictive by default** — nobody can use, modify, or distribute without explicit permission. Worst of all worlds for OSS; fine for private repos. |

For **internal Capital One InnerSource**: usually an internal-license boilerplate that maps to "internal use only, no warranty, follows the InnerSource agreement." Your platform team owns the file.

GitHub UI: when creating a repo, you can pick a license and GitHub adds it. For an existing repo, drop the file in root; GitHub re-detects and shows the license name in the sidebar.

---

## 4. CONTRIBUTING.md

What a new contributor needs to know:

- How to set up dev env (link to `docs/dev-setup.md` if non-trivial)
- How to run tests (`pytest`, `make test`, etc.)
- How to format / lint (`pre-commit run --all-files`, `ruff check`)
- Commit message convention (link to Conventional Commits if used — [module 19](19_templates_adr_docs_conventional_commits.md))
- Branching strategy (link to [module 15](15_branching_strategies.md))
- PR process: who reviews, how long, when to ping
- Code of Conduct link

```markdown
# Contributing

Thanks for thinking about contributing! Here's how.

## Setup
\`\`\`
git clone git@github.com:org/repo.git
cd repo
./scripts/setup.sh    # creates .venv and installs deps
pre-commit install
\`\`\`

## Branching
Trunk-based: feature branches <24h. Open PR early; small is better than complete.

## Tests
\`pytest tests/ -v\` — must pass before opening PR.

## Commit format
[Conventional Commits](https://www.conventionalcommits.org/): \`feat:\`, \`fix:\`, \`docs:\`, etc.

## Review
CODEOWNERS routes reviews automatically. Default SLA: 1 business day for first review.

## Code of Conduct
By contributing you agree to the [Contributor Covenant](CODE_OF_CONDUCT.md).
```

---

## 5. CODE_OF_CONDUCT.md

The default at most orgs: **Contributor Covenant 2.1** (https://www.contributor-covenant.org/). Copy-paste the text, set the contact email, done. GitHub UI even has a "Add Code of Conduct" button that drops a templated one.

At a bank, internal projects usually inherit the company's **Code of Conduct** — that's the canonical reference. The repo's CODE_OF_CONDUCT.md should link to it.

---

## 6. SECURITY.md

How to report a vulnerability **without going through public issues**. GitHub surfaces this file specially under the "Security" tab.

```markdown
# Security Policy

## Supported versions
| Version | Supported |
| ------- | --------- |
| 2.x.x   | ✅ |
| 1.x.x   | ❌ (EOL 2026-01) |

## Reporting a vulnerability

Please **do not** file public GitHub issues for security problems.

Email: security@example.com

Or use [GitHub Private Vulnerability Reporting](https://github.com/org/repo/security/advisories/new) — enabled on this repo.

We aim to acknowledge within 2 business days and resolve critical issues within 30 days.
```

Pair with GitHub's **Private Vulnerability Reporting** (Settings → Security → enable) — researchers can submit advisories directly, you triage in private, and publish a CVE when fixed.

---

## 7. Issue templates

Put one or more in `.github/ISSUE_TEMPLATE/`. GitHub shows them when someone clicks "New Issue."

```yaml
# .github/ISSUE_TEMPLATE/bug_report.yml
name: Bug report
description: Something doesn't work as expected
title: "[Bug]: "
labels: ["bug", "triage"]
assignees:
  - vraicha
body:
  - type: markdown
    attributes:
      value: |
        Thanks for the report! Please fill in the details below.
  - type: textarea
    id: what-happened
    attributes:
      label: What happened?
      description: Clear description + expected behavior
    validations:
      required: true
  - type: input
    id: version
    attributes:
      label: Version
      placeholder: "2.3.1"
    validations:
      required: true
  - type: textarea
    id: logs
    attributes:
      label: Relevant log output
      render: shell
```

Use the YAML form-based templates (newer, structured) over the legacy markdown templates. Forms enforce required fields and produce parseable issues.

`config.yml` in the same directory lets you disable blank issues and link out:

```yaml
# .github/ISSUE_TEMPLATE/config.yml
blank_issues_enabled: false
contact_links:
  - name: Question / Discussion
    url: https://github.com/org/repo/discussions
    about: Use Discussions for questions, not Issues.
  - name: Security vulnerability
    url: https://github.com/org/repo/security/advisories/new
    about: Report security issues privately.
```

---

## 8. PR template

`.github/PULL_REQUEST_TEMPLATE.md` is prepopulated into the PR body when someone opens a PR.

```markdown
## What and why
<!-- One-paragraph summary. Why is this change needed? -->

## How
<!-- Brief technical approach. Link relevant ADRs. -->

## Validation
<!-- How did you test this? Link CI runs, screenshots, perf numbers. -->
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Model validation passes (if ML changes)
- [ ] Docs updated

## Risk + rollback
<!-- What's the blast radius? How would we roll back? -->

## Related
<!-- JIRA ticket, RFC, design doc, related PR -->

Closes #<issue-number>
```

For an org with many repo types, you can have multiple templates (`PULL_REQUEST_TEMPLATE/feature.md`, `PULL_REQUEST_TEMPLATE/hotfix.md`) and the user picks via URL parameter (`?template=hotfix.md`).

---

## 9. CODEOWNERS — quick mention; deep dive in module 11

```
# .github/CODEOWNERS
# Last matching rule wins. Order matters.

# Default owners — anyone in the platform team reviews
*                       @org/platform-team

# ML-specific paths
/src/models/            @org/ml-team
/src/inference/         @org/ml-team @org/sre-team
/notebooks/             @org/ml-team

# Infra-as-code
/infra/                 @org/devops-team
/.github/workflows/     @org/devops-team

# Security-sensitive
/auth/                  @org/security-team
SECURITY.md             @org/security-team
/.github/CODEOWNERS     @org/platform-team @org/security-team
```

With branch protection set to "Require review from Code Owners," any PR touching `/src/models/` requires an `@org/ml-team` approval. **This is how Capital One routes review at scale** — you don't ping people, the routing is automatic.

---

## 10. The other useful files

- **`.editorconfig`** — cross-IDE editor settings (tab/space, line endings, charset). Universal:
  ```ini
  root = true
  [*]
  charset = utf-8
  end_of_line = lf
  indent_style = space
  indent_size = 4
  trim_trailing_whitespace = true
  insert_final_newline = true

  [*.{yml,yaml,json}]
  indent_size = 2
  ```
- **`CHANGELOG.md`** — automated by release-please (see [module 19](19_templates_adr_docs_conventional_commits.md)); never write by hand at scale.
- **`.github/FUNDING.yml`** — only for OSS public repos asking for sponsorship.
- **`.github/dependabot.yml`** — Dependabot config (see [module 34](34_ghas_dependabot.md)).
- **`.github/labeler.yml` + `actions/labeler` action** — auto-label PRs by paths touched.

---

## 11. The InnerSource bonus file: `.well-known/` or `OWNERS`

At Capital One's InnerSource scale, some orgs use additional metadata files:

- **`OWNERS`** (alternative to CODEOWNERS, used by Kubernetes, OpenShift) — same idea, different file
- **`.well-known/security.txt`** — RFC 9116 standard for vulnerability disclosure contacts
- **`MAINTAINERS.md`** — current + emeritus list with contact info, prefer this over scattering names in README
- **`MODEL_CARD.md`** — for ML repos, the standardized model documentation (we cover this in module 42)

---

## 12. Cross-references

- CODEOWNERS in depth → [module 11](11_branch_protection_rulesets_codeowners.md).
- Conventional Commits + CHANGELOG automation → [module 19](19_templates_adr_docs_conventional_commits.md).
- Python ML repo `pyproject.toml` + `src/` layout → [module 18](18_python_ml_repo_structure.md).
- Dependabot config → [module 34](34_ghas_dependabot.md).
- pre-commit config for ML → [module 40](40_precommit_reproducibility_refactor.md).
