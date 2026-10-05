# 32 — 🏦 Secret scanning + push protection

> *"Stopping a secret at push time is 1000× cheaper than rotating after a leak."*

## Why this module exists

GHAS Secret Protection is the bank-baseline feature that catches credentials before they leak. Two modes: **scanning** (find what's already committed) and **push protection** (block commits before they hit GitHub). Both ship with GitHub Secret Protection ($19/active committer/mo since April 2025 unbundling).

---

## 1. What's detected

GitHub partners with 200+ providers (AWS, Azure, GCP, Stripe, Slack, Twilio, Atlassian, Datadog, …) who provide regex + entropy patterns for their credential formats. Currently detected:

- **Provider keys**: AWS access keys, GCP service account JSON, Azure storage keys, Slack webhook URLs, Stripe live keys, npm tokens
- **GitHub tokens**: PATs (`ghp_*`, `github_pat_*`), App tokens (`ghs_*`), refresh tokens (`ghr_*`)
- **Private keys**: SSH, GPG, x509, RSA, ECDSA
- **AI-detected secrets** (Copilot-powered, since 2024): "anything that looks like a credential by entropy + naming"
- **Custom patterns**: org-specific regex you define

When a match is found:
- Public repo + partner-detected: GitHub notifies the partner (e.g., AWS automatically rotates the leaked key in some cases).
- Private repo + GHAS enabled: secret scanning alert appears in repo's Security tab.

---

## 2. Push protection — the block-at-source

Default behavior when push protection is enabled: a `git push` containing a detected secret is **rejected** by GitHub server-side.

```
$ git push
Enumerating objects: 5, done.
...
remote: ───────────────────────────────────────────────────
remote: GitHub Secret Scanning push protection
remote:
remote:   Resolve the following violations before pushing again
remote:
remote:    —— Push cannot contain secrets ——
remote:
remote:    AWS Access Key ID detected in:
remote:        commit: abc123
remote:        path:   src/config.py:42
remote:
remote: ───────────────────────────────────────────────────
```

The push is rejected; the dev fixes locally (rewrite history, remove the secret); push succeeds.

**Bypass options** (logged):
- Dev can declare it's a false positive (with reason captured).
- Dev can declare "I'll fix this later" (with reason — but secret is then a known live exposure).
- Org admin can permanently bypass with reason (for specific repos).

Every bypass is in the audit log with reason field — required for compliance review.

---

## 3. Enabling

Per repo:
- Settings → Code security and analysis → Secret scanning → Enable
- Push protection: separate toggle below secret scanning

Org-wide (preferred):
- Org Settings → Code security → Global settings → Enable secret scanning + push protection for ALL eligible repos.
- Choose to auto-enable on new repos (recommended).

For Capital One: enabled org-wide, no opt-out for production repos. Allowlist for specific repos that legitimately need to commit secret-shaped strings (rare; usually means refactor instead).

---

## 4. Custom patterns

For internal Capital One credential formats not in the default partner list:

```
# Pattern format (in repo Settings → Secret scanning → Custom patterns):

Name: "C1 Internal API Token"
Secret format (regex): c1_api_[A-Za-z0-9]{32}
Before secret (optional): \b
After secret (optional): \b
Test string: c1_api_abc123def456ghi789jkl012mno345pq
```

You can also require the secret be near specific keywords (e.g., a regex match only counts if "Authorization:" appears within 100 chars). This reduces false positives.

Custom patterns:
- Per-repo or per-org
- Tested before save (provide examples + non-examples)
- Apply to scanning AND push protection
- Can be marked as "high confidence" to gate push protection

---

## 5. Common false positives + handling

- **Test fixtures**: real-looking credentials in test data.
  Fix: use clearly-fake placeholders (`AKIATEST...` instead of `AKIA...`); use `# pragma: allowlist secret` or similar tooling comments.
- **Documentation examples**: real-looking but-not credentials in docs.
  Fix: same — use obviously-fake examples.
- **Pre-rotated credentials**: already-rotated, kept in git history for some reason.
  Fix: rewrite history with `git filter-repo` or accept the historical alert.

The pragma comment approach varies — for `detect-secrets` (a different tool), the comment is `# pragma: allowlist secret`. GitHub's secret scanning has its own dismissal mechanism in the UI per alert.

---

## 6. Local-first: `gitleaks` or `detect-secrets`

GitHub's scanning catches at PUSH. For pre-commit catches:

### gitleaks (Go, fast, well-maintained)

```bash
brew install gitleaks
gitleaks detect --source . --redact
gitleaks protect --staged    # pre-commit mode
```

As a pre-commit hook:

```yaml
# .pre-commit-config.yaml
- repo: https://github.com/gitleaks/gitleaks
  rev: v8.18.4
  hooks:
    - id: gitleaks
```

### detect-secrets (Yelp, Python)

```bash
pip install detect-secrets
detect-secrets scan > .secrets.baseline
detect-secrets audit .secrets.baseline   # mark TPs vs FPs

# pre-commit
- repo: https://github.com/Yelp/detect-secrets
  rev: v1.5.0
  hooks:
    - id: detect-secrets
      args: ['--baseline', '.secrets.baseline']
```

Run both: local catches at commit time; GitHub catches at push time (in case dev disabled the local hook).

---

## 7. Validity checking

GHAS automatically attempts to validate detected secrets against the providing service:
- AWS key → call `sts:GetCallerIdentity`
- GitHub PAT → call `/user`
- Slack webhook → ping with empty payload

Alert status:
- **Active** (validated as live) — highest priority
- **Inactive** (validation failed, possibly revoked)
- **Unknown** (no validator)

The UI sorts active first. Triage live ones immediately; inactive ones can be batched.

---

## 8. The leak-response runbook

When a real leak is detected (whether pre-push or post-push):

1. **Rotate the secret immediately.** The credential is compromised from the moment it entered git history. Rotating is step 1 — even before cleanup.
2. **Verify rotation took effect.** New consumers using the new value; old value invalidated.
3. **Identify exposure window.** Audit log — when was it pushed, who has cloned since, was the repo public, was it in a PR from a fork (visible publicly).
4. **Check for unauthorized use.** CloudTrail (AWS), Slack audit log, GitHub audit log for the leaked token's activity.
5. **Clean git history** (optional, for hygiene — does not remove from forks/clones):
   ```bash
   pip install git-filter-repo
   git filter-repo --replace-text replacements.txt
   # Then force-push (coordinate with team)
   git push --force-with-lease --all
   git push --force-with-lease --tags
   ```
6. **Document the incident** — required by SR 11-7 and security-team policy.

**Repeat**: rotating is step 1. History cleanup is hygiene, not security.

---

## 9. The audit + reporting view

GitHub UI: Org → Security → Secret scanning. Shows:
- All alerts across the org
- Filterable by repo, secret type, status (active/inactive)
- Statistics (alerts per week, mean time to resolve)
- Reviewer comments

Export via API for SIEM integration:

```bash
gh api /orgs/capitalone/secret-scanning/alerts --paginate
gh api /orgs/capitalone/secret-scanning/alerts?state=open
gh api /repos/capitalone/cool-repo/secret-scanning/alerts/123
```

For SR 11-7 + bank-grade audit: capture all secret-leak events in your central log; track MTTR per severity; review quarterly.

---

## 10. Cross-references

- The OIDC alternative (don't have AWS secrets to leak in the first place) → [module 29](29_actions_oidc_aws.md).
- Pre-commit framework for local-first detection → [module 40](40_precommit_reproducibility_refactor.md).
- Audit log streaming → [module 36](36_compliance_sso_scim_audit.md).
- Push protection bypass policy as part of governance → [module 11](11_branch_protection_rulesets_codeowners.md).
