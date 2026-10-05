# 36 — 🏦 SAML SSO, SCIM, IP allow lists, audit logs

> *"Identity + immutable audit history. Auditors keep these two as evidence. Wire them to your SIEM and you've satisfied 80% of the regulator's questions."*

## Why this module exists

Five org-level features that compose into the bank-grade identity + audit posture: SAML SSO (every access goes through your IdP), SCIM (provisioning automation), IP allow lists (network-level lockdown), audit log streaming, and external audit-log retention. None of these are individually complex; getting them all wired correctly is what makes Capital One's posture coherent.

---

## 1. SAML SSO

GitHub Enterprise Cloud supports SAML 2.0 against your IdP (Okta, Azure AD/Entra ID, Ping, OneLogin, Google Workspace, ADFS, …).

Setup (Org Settings → Authentication security → SAML single sign-on):
- IdP entity ID + Sign-on URL + public certificate (XML metadata)
- Enable: members must SSO to access org

After enablement:
- Every login goes through IdP.
- Every API/CLI access requires a SAML-authorized token (PATs and SSH keys must be explicitly authorized for the org after SSO setup).
- Sessions expire per IdP policy (typically 8 hours).

GitHub stays the source of truth for repo permissions, teams, and roles. The IdP is the source of truth for who's an employee.

**Enterprise Managed Users (EMU)** is the stricter variant: every user is IdP-managed; users can't have personal GitHub accounts that conflict; usernames are suffixed (`vraicha_capitalone`).

---

## 2. SCIM

SCIM (System for Cross-domain Identity Management) is the automation layer. When an employee:
- **Joins** → IdP sends a SCIM `create` → GitHub adds them as org member.
- **Joins a team in IdP** → SCIM update → added to the matching GitHub team.
- **Leaves** → IdP sends `deactivate` → GitHub disables the user; their authorizations expire immediately.
- **Changes name/email** → SCIM update propagates.

Setup is IdP-specific (Okta SCIM → GitHub connector, Azure AD provisioning, etc.) but the principle is identical: IdP → SCIM endpoint at `https://api.github.com/scim/v2/organizations/<org>` → GitHub.

For Capital One: SCIM is non-negotiable. Without it, offboarded employees' GitHub access lingers until manual cleanup — a compliance gap.

---

## 3. IP allow lists

Restrict who can access org resources by IP:

Org Settings → Authentication security → IP allow list. Add CIDR ranges:

```
198.51.100.0/24       # Corp office NYC
203.0.113.0/24        # Corp office VA
10.0.0.0/8            # VPN egress range
```

When enabled: requests from non-allowed IPs receive 403, even with valid auth.

Configuration choices:
- "Enable IP allow list for installed GitHub Apps" — also require Apps to come from allowed IPs (impacts CI integrations).
- Per-user: each user can also have IP rules at the user-account level.

For Capital One: enabled for org-wide access; GitHub Actions IP ranges added (since GH-hosted runners need access). Self-hosted runners obviously bypass since they originate from your own network.

---

## 4. Audit log — what's in it

Every action in the org is logged:
- User logins (and method — SAML, PAT, SSH, OAuth)
- Repo creates, deletes, transfers
- Team membership changes
- Permission changes
- Rulesets / branch protection edits
- Workflow runs
- Secret creation/deletion
- Push activity
- Bypasses (rulesets, secret scanning push protection, environment protection)
- App installations
- Settings changes

UI: Org Settings → Audit log. Default retention varies by plan:
- GitHub Enterprise Cloud: **6 months in UI**, exportable indefinitely via API.

Search/filter:
- `actor:vraicha` — who
- `action:repo.create` — what
- `created:>=2026-04-01` — when
- `repo:capitalone/cool-repo` — where
- `country:US` — from where

```bash
gh api -H "Accept: application/vnd.github+json" \
  "/orgs/capitalone/audit-log?phrase=action:repository_ruleset.update+created:>=2026-05-01" \
  --paginate > rulesets-changes.json
```

---

## 5. Audit log streaming

For long-term retention + SIEM integration, **stream the audit log** to:
- Splunk
- Azure Event Hubs
- Datadog
- Amazon S3
- HTTPS endpoint (generic)
- Google Cloud Storage

Configuration: Enterprise Settings → Audit log → Log streaming. Choose destination, provide credentials, choose:
- Include Git events (every push, every pull) — high volume but required for full audit
- Include API requests — high volume but required for forensics

Verify the stream is flowing via Settings UI status indicator. Set up alerting on stream gaps.

For Capital One: this stream feeds the SOC's SIEM. Detective controls run on the stream (anomaly detection on push patterns, unusual access from new IPs, etc.).

---

## 6. Per-repo audit log (newer)

In addition to org-level, per-repo audit log shows actions specific to that repo. Useful when a team wants to see "what happened in our repo last week" without org-wide noise.

API: `gh api /repos/capitalone/cool-repo/audit-log` (where supported).

---

## 7. SAML-authorized PATs and SSH keys

After enabling SAML SSO, existing PATs and SSH keys must be **explicitly authorized** for the org:
- User → Settings → Personal access tokens → for each token, click "Configure SSO" → authorize for the org
- Same for SSH keys

Unauthorized tokens/keys still work for personal repos but fail for org resources.

For deprovisioning: when SCIM removes the user, all their SAML-authorized PATs/SSH keys are revoked simultaneously. This is what makes "leaving = immediate access loss" actually work.

---

## 8. The compliance evidence pipeline

A regulator asks: "Show me that all changes to model code were reviewed by an authorized person and traceable to a specific deployment."

Your answer (in order):
1. Audit log entry: PR #N opened by alice@capitalone.com
2. Audit log entries: review submitted by bob@capitalone.com + carol@capitalone.com (CODEOWNERS-required)
3. Audit log entry: PR merged (squash) by alice; merge commit SHA X
4. Audit log entry: signed-commit verification PASSED on commit X
5. Deployment record (GitHub Environment): commit X deployed to `prod` env after approval by dave@capitalone.com (separation of duties — alice merged, dave approved deploy)
6. Artifact attestation: build provenance attestation for the model artifact, signed via OIDC tied to the workflow run; SHA matches commit X
7. SageMaker Model Registry entry: version Y created at time T, source artifact = the attested SHA
8. CloudTrail entry: `UpdateEndpoint` call by the GitHub Actions OIDC role, target endpoint `prod-fraud-detector`, model version Y
9. Slack notification archived in your SIEM: "Deployed prod-fraud-detector v.Y at T"

All from your audit log + GitHub Environment deployment history + SageMaker logs + CloudTrail + Slack. **No human spreadsheet.** Auditor accepts.

---

## 9. The org-level enforcement levers

Beyond audit, the org/enterprise levels also have:
- **Policy enforcement** (Enterprise): force settings on all orgs (require signed commits, force branch protection minimums, etc.)
- **Verified domains**: prove control of `capitalone.com` so user email matches; required for email-domain-based features
- **2FA enforcement**: org → require 2FA. Members without 2FA are removed.
- **Restricting org creation** (Enterprise): only platform team can create new orgs.
- **Restricting App installations**: only admins can install new GitHub Apps.

For Capital One: 2FA enforced; verified domain `capitalone.com`; restricted org creation; restricted App installs (platform/security team only); signed commits required across all orgs via Enterprise policy.

---

## 10. Cross-references

- The Rulesets that produce most of the auditable events → [module 11](11_branch_protection_rulesets_codeowners.md).
- Auth credentials types + SAML-authorization step → [module 12](12_auth_pat_ssh_signing.md).
- Environment-based deploy gates as the separation-of-duties layer → [module 30](30_actions_environments_protection.md).
- SR 11-7-specific audit requirements for ML model lifecycle → [module 37](37_compliance_sr117_audit.md).
