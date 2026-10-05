# 20 — Application Vulnerability Scanning: GitLeaks + Pre-commit

## Why this module exists

The #1 supply-chain leak vector in 2026: **secrets committed to Git**. A leaked AWS access key gets discovered + exploited within minutes by automated scanners. GitLeaks is the OSS scanner; the pre-commit framework is the wrapper that runs it (and other linters) before code ever leaves your laptop.

## 1. The secret-leak problem

The numbers:
- **GitGuardian's 2024 State of Secrets Sprawl**: 23.7M new secrets detected in public repos in 2023
- **Average time-to-detection** by attackers for a leaked AWS key on GitHub public: ~5 minutes
- **Average cleanup cost** of a secret leak (rotate, audit, comms): $400-2000 per incident
- **GitHub Secret Scanning** (free for public repos, paid for private orgs via GHAS) catches 200+ secret patterns

## 2. GitLeaks — the OSS leader

GitLeaks scans commits, repos, files for high-entropy strings + known patterns (AWS keys, GitHub tokens, Stripe keys, JWT, RSA private keys, etc.).

```bash
# Install
brew install gitleaks
# Or
docker run -v $(pwd):/path zricethezav/gitleaks:latest detect -v --source=/path

# Run
gitleaks detect --source . --verbose
gitleaks protect --staged --verbose      # check staged before commit
gitleaks git history --source .          # scan full git history
```

### Config (.gitleaks.toml)
```toml
title = "gitleaks config"

[extend]
useDefault = true

[[rules]]
id = "company-api-key"
description = "Internal API key"
regex = '''[a-z]{4}_live_[A-Za-z0-9]{32}'''
keywords = ["live_"]

[allowlist]
description = "test fixtures"
paths = [
  '''tests/fixtures/.*''',
  '''docs/examples/.*''',
]
regexes = ['''dummy-key-.*''']
```

Allowlisting is essential — test fixtures + docs often contain dummy-looking strings.

## 3. Pre-commit framework

`pre-commit` (https://pre-commit.com) is the orchestrator. One YAML config runs many hooks:

```yaml
# .pre-commit-config.yaml
repos:
  # Core hygiene
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files
        args: ['--maxkb=500']
      - id: check-merge-conflict
      - id: detect-private-key
      - id: no-commit-to-branch
        args: ['--branch', 'main']

  # Secret scanning
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.21.2
    hooks:
      - id: gitleaks

  # Python
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]

  # Shell
  - repo: https://github.com/shellcheck-py/shellcheck-py
    rev: v0.10.0.1
    hooks:
      - id: shellcheck

  # YAML / Markdown
  - repo: https://github.com/adrienverge/yamllint.git
    rev: v1.35.1
    hooks:
      - id: yamllint
  - repo: https://github.com/igorshubovych/markdownlint-cli
    rev: v0.42.0
    hooks:
      - id: markdownlint

  # IaC
  - repo: https://github.com/antonbabenko/pre-commit-terraform
    rev: v1.96.1
    hooks:
      - id: terraform_fmt
      - id: terraform_validate
      - id: terraform_tflint
      - id: terraform_checkov
```

Install and run:
```bash
pip install pre-commit
pre-commit install              # install hooks in .git/hooks/pre-commit
pre-commit install --hook-type commit-msg
pre-commit run --all-files      # run on all files (not just staged)
pre-commit autoupdate           # bump hook versions
```

## 4. Running GitLeaks in CI (defense in depth)

Pre-commit catches at commit time. But devs can `--no-verify`. **CI must verify again.**

```yaml
# .github/workflows/security.yml
on: [push, pull_request]
jobs:
  gitleaks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }     # full history for git-history scanning
      - uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITLEAKS_LICENSE: ${{ secrets.GITLEAKS_LICENSE }}   # for org-level scanning
```

GitLab CI equivalent:
```yaml
gitleaks:
  image: zricethezav/gitleaks:latest
  script: gitleaks detect --source . --verbose --report-format sarif --report-path gitleaks.sarif
  artifacts:
    reports:
      sast: gitleaks.sarif
```

## 5. The `fix the leak` runbook

A leak found in commit history. The myth: "just delete the commit." The reality: assume the secret is compromised. Steps:

1. **Rotate the secret first** (AWS console / Secrets Manager / wherever) — before doing anything to Git
2. **Audit usage** of the old credential — CloudTrail for AWS, vendor audit logs
3. **Investigate** whether the secret was exploited (probably; act as if it was)
4. **Optionally** rewrite history with `git filter-repo` or BFG Repo-Cleaner — but only after rotation, and only if you control all clones
5. **Add a regex pattern** to detect this type in your `.gitleaks.toml`
6. **Postmortem** with the team — what process gap let it through?

GitHub Push Protection (GHAS) blocks the push *before* the leak. Use it where licensed.

## 6. False positives — the operational reality

Common FP patterns:
- Test fixtures with realistic-looking dummy data
- Doc examples (`AWS_KEY=AKIA...EXAMPLE`)
- Hex strings in checksums or git SHAs
- Base64 encoded test payloads

Manage by:
- **`#gitleaks:allow` inline comment** on the line
- **Allowlist in `.gitleaks.toml`** for files/patterns
- **Baseline file** with currently-known findings (don't break the build for legacy)

Discipline: every allowlist entry justified in a comment.

## 7. Beyond GitLeaks: the secret-scanning ecosystem

| Tool | When |
|---|---|
| **GitLeaks** | OSS, fast, default |
| **TruffleHog** | OSS, deep entropy analysis, **verifies secrets are live** (calls the API) |
| **GitHub Secret Scanning + Push Protection** | GitHub-native; 200+ partner patterns; push protection blocks at git server |
| **GitLab Secret Detection** | GitLab-native (Premium/Ultimate) |
| **AWS Macie** | Detects sensitive data in S3 (PII), not just credentials |
| **Snyk** | Commercial; broader DevSecOps platform |
| **GitGuardian** | Commercial; org-wide scanning + monitoring |

For Capital One scale: GitHub Secret Scanning + Push Protection + GitGuardian-equivalent commercial layer for monitoring + GitLeaks in dev pre-commit + CI.

## 8. SAST in pre-commit (a brief preview — full SCA in module 22)

Pre-commit can also run SAST:

```yaml
- repo: https://github.com/PyCQA/bandit
  rev: 1.7.10
  hooks:
    - id: bandit
      args: ['-c', 'pyproject.toml']
- repo: https://github.com/returntocorp/semgrep
  rev: v1.92.0
  hooks:
    - id: semgrep
      args: ['--config=auto', '--error']
```

Cost: slower commits. Calibrate to keep pre-commit < 10s total or devs will `--no-verify`.

## 9. Quick self-check

1. What does pre-commit do that running scanners individually doesn't?
2. Why must CI also scan even if pre-commit is installed?
3. What's the first step when a leaked secret is found in history?
4. What's TruffleHog's differentiator vs GitLeaks?
5. What's GitHub Push Protection and what advantage does it have over scanning at CI time?

(Answers: orchestrates many hooks from a single declarative config + version-pins them; devs can bypass with --no-verify; rotate the secret before doing anything to git; verifies the secret is actually live by calling the corresponding API; blocks the push at the git server before secret ever reaches remote — earliest possible mitigation.)
