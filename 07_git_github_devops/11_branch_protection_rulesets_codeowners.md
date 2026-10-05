# 11 — 🏦 Branch protection, Rulesets, CODEOWNERS

> *"At a bank, the only thing standing between a junior engineer's typo and prod is the rules on `main`. Get this configuration right and most of compliance falls out for free."*

## Why this module exists

Branch protection and CODEOWNERS are the governance backbone of every regulated GitHub repo. This is the most-tested-in-interviews topic for Sr Lead roles in finance. The 2026 reality: **Rulesets** are the modern, more powerful replacement for the legacy **Branch protection rules** — but both still work, and you'll see both in the wild.

---

## 1. The two systems — old vs new

| | Branch protection rules | Rulesets (GA 2023) |
|---|---|---|
| Scope | Per branch (pattern match) | Per branch pattern, org-wide or repo-wide |
| Stack? | One rule per branch pattern | **Multiple rulesets stack additively** |
| Visibility | Admin-only | Visible to everyone (better discoverability) |
| Bypass | Per-rule "allow" list | Bypass actors at ruleset level |
| Required reviewer rule (per path) | Via CODEOWNERS only | Native: `Required reviewer` rule with path patterns (GA Feb 2026) |
| API | REST | REST + GraphQL |

**Migration**: GitHub recommends Rulesets for new setups. Existing branch protection rules continue to work. Org-level rulesets can enforce policy across all repos without touching each repo's settings — the platform-engineer win.

---

## 2. The set of rules you should configure on `main`

A bank-grade `main` branch ruleset:

| Rule | Setting | Why |
|---|---|---|
| **Restrict creations** | On | Block accidental creation of conflicting branches |
| **Restrict updates** | Force-push: off | Stops history rewrites |
| **Restrict deletions** | On | Stops accidental branch deletion |
| **Require linear history** | On | No merge commits — forces clean trunk-based history |
| **Require signed commits** | On | Every commit is verifiably authored |
| **Require a pull request before merging** | On, 2 approvals, dismiss stale | Forces the review process |
| → Require review from Code Owners | On | CODEOWNERS-matched paths require SME approval |
| → Require approval of the most recent reviewable push | On | Author can't approve own changes |
| → Require conversation resolution before merging | On | No unresolved review threads at merge |
| **Require status checks to pass** | On, list specific checks, "Require branches to be up to date" | CI must be green; PR must be rebased on current main |
| **Require deployments to succeed before merging** | On (optional) | If you have a staging deploy gate |
| **Block force pushes** | On | Redundant with above but explicit |
| **Require a merge queue** | On (large teams) | Serializes merges, prevents semantic conflicts |
| **Required reviewer rule** (Rulesets only) | On, per path | E.g., `/auth/**` requires `@org/security` approval |

The combination is what makes the platform team's coffee-drinking time efficient. Every required gate is a thing the engineer can't bypass.

---

## 3. CODEOWNERS — the routing layer

CODEOWNERS lives at one of:
- `.github/CODEOWNERS` (preferred — the convention)
- `CODEOWNERS` (root)
- `docs/CODEOWNERS`

**Search order is the above.** Only the first found is used.

### Syntax

```
# Comments start with #
# Pattern         Owner1     Owner2  ...
# Patterns are gitignore-style: ! for negation, ** for any depth

# Default — applies to everything not matched by a more specific rule below
*                                    @org/platform-team

# Path-specific
/src/models/                         @org/ml-team
/src/inference/                      @org/ml-team @org/sre-team
/notebooks/                          @org/ml-team

# File-specific
README.md                            @org/docs-team
CODEOWNERS                           @org/platform-team @org/security-team

# Glob patterns
**/*.tfstate                         @org/devops-team
**/Dockerfile                        @org/devops-team @org/security-team

# Email instead of @-handle (for users without GitHub accounts)
/src/legal/                          legal@example.com

# Order matters — LAST matching pattern wins
/src/                                @org/backend-team
/src/critical-auth.py                @org/security-team @org/backend-team
```

**Key gotchas**:

- **Last match wins**, not first. Put broader rules earlier, more-specific later.
- **CODEOWNERS itself should be owned** — by the platform/security team — so a malicious PR can't change ownership and merge itself.
- A user can be a CODEOWNER only if they have **write access** to the repo (else GitHub ignores them for protection purposes).
- For org-team mentions (`@org/team-name`), the team must have write access to the repo.
- **Whitespace-separated** owners — multiple owners on one line means ANY of them can approve (not ALL).

### Negation (newer)

```
# Everything in /src/ requires backend team
/src/                                @org/backend-team

# ... except /src/ml/ which requires ML team
/src/ml/                             @org/ml-team

# ... and /src/security/ which requires BOTH security AND backend
/src/security/                       @org/security-team @org/backend-team
```

Pure CODEOWNERS doesn't support `!` negation. **Rulesets' "Required reviewer rule"** does — and is the new GA-Feb-2026 feature that fills this gap.

---

## 4. The Required Reviewer rule (Rulesets, GA Feb 2026)

```
# In a ruleset config, add a Required Reviewer rule:
# Require @org/security-team on PRs touching /auth/** OR /payment/**
# EXCLUDING /auth/tests/** (negation with !)

Rule type: Required Reviewer
Reviewer: @org/security-team
Required approvals: 1
File patterns:
  - auth/**
  - payment/**
  - "!auth/tests/**"
```

This separates **policy** (Rulesets) from **ownership** (CODEOWNERS). CODEOWNERS tells you who's responsible; Required Reviewer enforces who must approve. At Capital One scale, you use both:
- CODEOWNERS for "who knows this code best" (routing for review notification)
- Required Reviewer rules for "who MUST approve for compliance" (e.g., security team on auth changes)

---

## 5. Bypass — the controlled escape hatch

Sometimes you need to bypass a rule (urgent prod fix, automated PR from a bot). Rulesets have explicit **bypass actors**:

- **Specific people** (named users)
- **Specific teams**
- **Repo roles** (Maintain, Admin)
- **Apps** (GitHub Apps, e.g., your Dependabot or release-please bot)

Every bypass is **logged in the audit log** with a reason field — required for compliance. At a bank, the bypass list is small (a few SREs + the platform team's break-glass account) and is reviewed quarterly.

---

## 6. Layered rulesets (the platform-engineer pattern)

The win of Rulesets over old branch protection: **org-level rulesets** that apply across all repos.

Example:
- **Org-level ruleset "secure-default-main"**: targets `main` in all repos. Requires signed commits, required PR review, status checks. Cannot be disabled by repo admins.
- **Org-level ruleset "ml-repos-extra"**: targets `main` in repos with topic `ml`. Adds: require model-validation status check, require @org/ml-team CODEOWNERS approval.
- **Repo-level ruleset "service-X-specific"**: per-repo additions for service-specific needs.

All three apply additively. A PR has to satisfy ALL of them.

**The control plane**: rulesets are defined in YAML/JSON via API. Store them in a config repo, deploy via CI to every org. Platform-engineering best practice.

---

## 7. Reading the audit log for compliance evidence

Every ruleset action (bypass, override, change to ruleset) appears in the org audit log:

```bash
gh api -H "Accept: application/vnd.github+json" \
  "/orgs/capitalone/audit-log?phrase=action:repository_ruleset+include:web" \
  --paginate > audit.json
```

What auditors want to see:
- All changes to rulesets (who changed what, when)
- All bypasses (who, what PR, what reason)
- Any disabled enforcement
- Signed-commits verification rate across repos

GitHub Enterprise Cloud's audit log is searchable for 6 months in the UI, exportable indefinitely via API. Stream to your SIEM (Splunk, Sumo Logic) for long-term retention — see [module 36](36_compliance_sso_scim_audit.md).

---

## 8. The default-branch question

`main` is the universal default in 2026. Your ruleset targets `main`. But:

- **Old repos** may still have `master`. Target the actual default branch.
- **Release branches** like `release/2.4` may need their own ruleset (perhaps less strict than `main` — e.g., allow direct push for hotfixes).
- **`develop` branch** in Git Flow shops: protect with similar rules to main.
- **Personal forks**: don't waste effort protecting branches on forks; the upstream's ruleset is what matters.

Target pattern syntax in Rulesets:
- `main` — exactly main
- `release/*` — any release branch
- `~ALL` — all branches in repo
- `~DEFAULT_BRANCH` — the default (resilient to renames)

---

## 9. Bypass auditing — the SR 11-7 angle

For SR 11-7 model risk (see [module 37](37_compliance_sr117_audit.md)), the audit needs to show:

- Every model-impacting PR was reviewed by a member of the model-validation team
- No model deployment bypassed the review gate
- All bypasses (if any) were approved by the appropriate level

CODEOWNERS for `/models/**` and `/inference/**` to `@org/model-validation`, plus a Required Reviewer rule with same scope, plus bypass restricted to the on-call SRE list — that's the policy. Audit log is the evidence.

---

## 10. The senior pitfalls

❌ **CODEOWNERS without write access** — owners listed without write perms are silently ignored. The PR appears unreviewed by code owners and the protection doesn't trigger.

❌ **Branch protection but no required status checks** — passing CI isn't enforced. Bypass is the merge button.

❌ **"Require signed commits" without an enrollment campaign** — every contributor must set up SSH/GPG signing first. Otherwise PRs get blocked at merge. Roll out: warn for 30 days, then enforce.

❌ **Single-rule branch protection on a repo with multiple long-lived branches** — protect `main` but not `release/*` → a hotfix bypassing review on release branch.

❌ **No "require resolution of conversations"** — approve-and-merge while reviewer's comments remain open. They never get addressed.

❌ **Allowing PR author to be an approver** — disable "Allow specified actors to bypass required pull requests" except for emergency-only bot accounts.

---

## 11. Cross-references

- The PR mechanics (how the rules apply to a specific PR) → [module 10](10_prs_code_review_merge.md).
- Signed-commit setup (so users CAN sign) → [module 02](02_config_identity_signing.md).
- Status checks come from CI → [module 20](20_actions_workflow_events.md).
- Org-level audit log streaming → [module 36](36_compliance_sso_scim_audit.md).
- SR 11-7 audit-trail expectations → [module 37](37_compliance_sr117_audit.md).
