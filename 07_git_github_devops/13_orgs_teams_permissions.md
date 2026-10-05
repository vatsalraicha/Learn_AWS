# 13 — Organizations, teams, permissions, repo roles

> *"GitHub Enterprise is org-shaped. Internalize the model — orgs contain teams contain people; teams have repo roles; people inherit team perms. Everything else is detail."*

## Why this module exists

The permissions model is what makes "GitHub for one developer" different from "GitHub for 7,000 Capital One engineers." This module lays it out so an org-level question never confuses you in an interview.

---

## 1. The hierarchy

```
GitHub Enterprise (the billing/admin top level — only at Enterprise Cloud)
    └── Organization (e.g., 'capitalone')
            ├── People (members + outside collaborators)
            ├── Teams (nestable hierarchies of people)
            │       └── Sub-teams (inherit parent's parent-org access, plus their own)
            └── Repositories (each with its own permissions)
```

- **Enterprise**: a billing/policy umbrella. One enterprise can have many orgs. Enterprise admins set policy that orgs must comply with.
- **Organization**: the unit that owns repos, has teams, has billing. Most companies have one main org + spinoffs.
- **Team**: a group of people. Can be nested. Teams own repo permissions.
- **Repository**: the code unit.

---

## 2. Member roles (org-level)

| Role | What |
|---|---|
| **Owner** | Full admin — can create/destroy repos, change billing, change org settings, delete the org |
| **Member** | Default; can be granted repo access via teams or direct invites |
| **Outside collaborator** | Not a member of the org; granted access to specific repos only |
| **Billing manager** | View billing only |

Owners are dangerous — most orgs keep 2–4 humans + 1 break-glass account. Day-to-day administration is delegated via teams.

---

## 3. Teams

A team is a group of people PLUS a set of repo permissions.

```bash
gh api -X POST /orgs/capitalone/teams -f name=ml-team -f description="Team owning ML services" -f privacy=closed
gh api /orgs/capitalone/teams/ml-team/members
gh api -X PUT /orgs/capitalone/teams/ml-team/repos/capitalone/cool-ml-repo -f permission=push
```

Team properties:
- **Name** + **slug** (URL-friendly version)
- **Privacy**: `secret` (team and members invisible to non-members) or `closed` (visible)
- **Parent team**: optional — nested teams inherit parent's repo permissions
- **Maintainers**: members who can add/remove other members
- **Repo permissions**: per-repo permission level for the team

### Team mentions

`@org/team-name` in PRs/issues notifies all team members AND can be used in CODEOWNERS.

### Nested teams

```
@capitalone/engineering
├── @capitalone/engineering/ml
│   ├── @capitalone/engineering/ml/research
│   └── @capitalone/engineering/ml/platform
└── @capitalone/engineering/security
```

A member of `@capitalone/engineering/ml/platform` is automatically considered a member of `@capitalone/engineering/ml` AND `@capitalone/engineering` for permission inheritance. Repo permissions are inherited downward — granting `ml` team write access to `repo-X` automatically gives `ml/platform` members write access too.

---

## 4. Repository roles

Each repo has 6 access levels (granted to teams or individuals):

| Role | Permissions (in order from least to most) |
|---|---|
| **Read** | Clone, view issues + PRs |
| **Triage** | Read + manage issues/PRs (apply labels, close, request reviews) without write code access |
| **Write** | Triage + push to non-protected branches, create branches |
| **Maintain** | Write + manage repo settings (excluding sensitive — no delete, no billing) |
| **Admin** | Maintain + delete repo, manage access, manage protected branches |
| **Custom roles** (Enterprise only) | Define your own permission set |

The role granted per team/person is the **maximum** they can do. Branch protection further restricts (e.g., even an Admin can't bypass branch protection if "Do not allow bypassing the above settings" is set).

### Best practice for write access

Don't grant individuals direct access. Grant teams. People come and go; team membership is the right abstraction.

```
Repo: cool-ml-service
  - @capitalone/ml-platform (Maintain)
  - @capitalone/ml-engineering (Write)
  - @capitalone/all-engineering (Read)
  - @capitalone/security-team (Triage)
```

When a person joins the team, they get the access. When they leave, they lose it.

---

## 5. Permission model deep — what beats what

Order of precedence (in case of conflict, the most-permissive wins):

1. **Repo-level direct collaborator access** (rare)
2. **Team-granted access** (most common)
3. **Org base permissions** (the floor — usually "None" or "Read")
4. **Outside collaborator access** (per-repo only)
5. **Public repos**: everyone gets Read

If a person is on multiple teams with different access levels on the same repo, they get the union (most permissive).

**Outside collaborators** are NOT org members but have access to specific repos. They count as a different category for billing. Use them for contractors, vendors, external auditors.

---

## 6. Org base permission — the floor

Org Settings → Member privileges → Base permissions: `None` / `Read` / `Triage` / `Write` / `Admin`.

This is the access EVERY org member has to EVERY internal repo by default. At a bank: usually **Read** for internal repos (InnerSource visibility) or **None** for sensitive orgs. Never `Write` or `Admin` — that gives everyone write access to everything.

---

## 7. SAML SSO + SCIM (cross-link to module 36)

For Capital One:

- **SAML SSO** — every API call/web access goes through your identity provider (Okta, Azure AD).
- **SCIM provisioning** — when an employee is added to a specific AD group, they're auto-added as a GitHub org member; when removed, auto-deprovisioned.
- **SAML-authorized credentials** — PATs and SSH keys must be authorized for SSO use; expire when SSO session expires or on deprovision.

The combination = **leaving Capital One = your GitHub access disappears within minutes**, no manual cleanup needed.

---

## 8. Enterprise account features (Enterprise Cloud / Enterprise Server)

- **Enterprise Managed Users (EMU)** — users are managed entirely by your IdP; usernames have a `_<enterprise>` suffix; users can't have personal accounts on github.com that conflict.
- **Restricting org creation** — only specific people can create new orgs under the enterprise.
- **Enterprise-level audit log** — aggregates all org audit logs.
- **Enterprise-level policies** — enforce things like "all repos must require signed commits."
- **IP allow lists** — restrict who can access org/enterprise resources by IP.

---

## 9. Custom org roles (newer, Enterprise)

GitHub added **custom organization roles** so you can define exactly what your "Platform Engineer" or "Security Reviewer" can do, beyond the built-in Owner/Member dichotomy.

Example: a "Repo Auditor" role that can read all repos AND view audit logs AND manage Rulesets, but NOT delete repos or change billing.

Set up via Org Settings → Custom roles. Each role = a set of permissions, applicable to all repos or specific repos.

---

## 10. The cost-per-permission consideration

GHAS, Copilot, Codespaces, and Advanced Security features are billed **per active committer**. Active committer = anyone who's pushed to a private repo in the last 90 days.

Cost-management implication: if someone has Write access but never pushes, they don't cost. But the moment they push once, they're a billable seat for 90 days.

Audit quarterly: which seats actively used Write access? Demote unused-Write accounts to Read.

---

## 11. The senior pitfalls

❌ **Direct collaborator access** to individuals (instead of via teams) — invisible to org admins, untracked, hard to audit when someone leaves.

❌ **Granting "Owner" too liberally** — every Owner has the ability to drop the entire org. Default to "Maintainer" team role.

❌ **Org base permission set to "Write" or higher** — every member gets write access to every repo. Massive blast radius.

❌ **CODEOWNERS pointing to teams without repo access** — silently ignored. The rule appears in CODEOWNERS but doesn't enforce review requirements.

❌ **Outside collaborators on sensitive repos** — they're not org members, harder to audit, often forgotten about. Quarterly review the outside collaborator list.

❌ **No SCIM** — employee leaves, manual cleanup. Eventually you'll miss one.

---

## 12. Cross-references

- CODEOWNERS using team mentions → [module 11](11_branch_protection_rulesets_codeowners.md).
- SAML SSO + SCIM + audit log → [module 36](36_compliance_sso_scim_audit.md).
- Org-level rulesets stacking → [module 11](11_branch_protection_rulesets_codeowners.md).
- Org-level reusable workflows + composite actions → [module 31](31_actions_token_cost_templates.md).
- GitHub Apps for org automation → [module 52](52_apps_webhooks_ghcli_graphql.md).
