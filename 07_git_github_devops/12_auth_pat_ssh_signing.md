# 12 — Authentication: PAT, SSH, GPG/SSH commit signing

> *"Three credential surfaces — push auth, API auth, commit signing. They look similar; they're different. Confuse them at your peril."*

## Why this module exists

GitHub has multiple credential types serving distinct purposes. Sr engineers regularly mix them up — using a PAT for git push when SSH is simpler, using a classic PAT when fine-grained is more secure, signing commits with a key that's not on GitHub. This module untangles them.

For commit signing setup, see [module 02](02_config_identity_signing.md). This module focuses on what kind of credential to use where, and the security posture for each.

---

## 1. The credential surfaces

| Surface | What it authenticates | Common credentials |
|---|---|---|
| **Git over HTTPS** | `git push`/`pull` via HTTPS | PAT, OAuth (via `gh`), credential helper |
| **Git over SSH** | `git push`/`pull` via SSH | SSH key |
| **GitHub API** (REST + GraphQL) | `curl`/`gh`/scripts | PAT, OAuth token, GitHub App token |
| **Commit signature** | Cryptographic identity of who made the commit | SSH key (signing) or GPG key |
| **GitHub Actions OIDC** | Workflow → cloud (AWS, GCP, Azure) | OIDC JWT (no long-lived credential) |

Different keys for different jobs. An SSH key can be used for both push auth AND signing (same key, two entries on GitHub: one "Authentication," one "Signing"). A PAT is for HTTPS push + API only.

---

## 2. Personal Access Tokens (PAT) — classic vs fine-grained

Both are bearer tokens (anyone holding them can act as you). They differ in scope granularity and the security model.

### Classic PAT (deprecated for new use)

- Scopes: `repo`, `workflow`, `admin:org`, etc. — coarse, all-or-nothing.
- `repo` scope = read AND write to ALL your repos AND all repos you have admin on.
- No expiry by default (you can set one, but it's opt-in).
- Listed under: Settings → Developer settings → Personal access tokens → Tokens (classic).
- **Use for**: legacy scripts that need API access. New tokens should be fine-grained.

### Fine-grained PAT (preferred since 2023)

- **Repository-scoped** — token can only act on repos you select.
- **Per-permission**: choose exactly which APIs (Actions: Read+Write, Contents: Read, Issues: None, ...).
- **Required expiry** — max 1 year.
- **Org approval required** if the resource is org-owned (org admin must approve the token before it can act).
- Listed under: Settings → Developer settings → Personal access tokens → Fine-grained tokens.

**Always prefer fine-grained.** The few cases that still need classic (some 3rd-party tools, some workflow scopes) are shrinking each release.

### What to do with leaked PATs

1. **Revoke immediately** in Developer Settings.
2. **Audit usage** — the audit log shows API calls by token (use `actor_id` filter).
3. **Rotate any data the token might have exposed** if it had write scope.

GitHub's **Secret Scanning** with **Push Protection** (see [module 32](32_ghas_secret_scanning.md)) will catch PATs as they're committed and refuse the push.

---

## 3. SSH keys for git push

The clean default for personal use.

```bash
# Generate (use ed25519, not RSA)
ssh-keygen -t ed25519 -C "vatsal.raicha@gmail.com" -f ~/.ssh/id_ed25519

# Optionally add to ssh-agent (so you don't type passphrase every time)
ssh-add --apple-use-keychain ~/.ssh/id_ed25519   # macOS
ssh-add ~/.ssh/id_ed25519                         # Linux

# Upload public key to GitHub: Settings → SSH and GPG keys → New SSH key
cat ~/.ssh/id_ed25519.pub
# Paste into GitHub; choose "Authentication Key" for push, or "Signing Key" for commit signing,
# or add the same key twice as both.

# Verify
ssh -T git@github.com
# Hi vraicha! You've successfully authenticated, but GitHub does not provide shell access.
```

`.ssh/config` makes multi-account life easier:

```
# ~/.ssh/config

Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes

Host github-work
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_work
    IdentitiesOnly yes
```

Then clone using the alias:

```bash
git clone git@github-work:capitalone/some-repo.git
```

That repo will use the work SSH key automatically.

For commit identity per directory, use `includeIf` (see [module 02](02_config_identity_signing.md)).

---

## 4. OAuth via the `gh` CLI

`gh auth login` walks you through device-code OAuth:

```bash
gh auth login

# Choose: GitHub.com or GitHub Enterprise Server
# Choose: HTTPS or SSH
# Choose: Authenticate with browser (preferred) or paste a token
# Browser opens, you authorize, done.

gh auth status                    # show current auth
gh auth refresh -s "workflow,admin:org"   # add scopes to existing auth

gh auth setup-git                 # configure git to use gh as credential helper for HTTPS
```

When you `gh auth setup-git`, `git push` over HTTPS calls `gh` which provides an OAuth token. **No PAT needed** for daily push, fetch, clone.

For automation and CI, use:
- `GITHUB_TOKEN` (auto-provisioned in Actions; ephemeral; scoped to current workflow run)
- Fine-grained PAT stored as a secret (for non-Actions automation)
- GitHub App tokens (best for bots; see [module 52](52_apps_webhooks_ghcli_graphql.md))

---

## 5. The `GITHUB_TOKEN` in Actions

Every workflow run automatically gets a `GITHUB_TOKEN` secret. It:
- Is generated at workflow start, expires at workflow end (~max 24h).
- Is scoped to the repo running the workflow.
- Has permissions configured via `permissions:` block (or org defaults).
- Authenticates as the `github-actions[bot]` identity.

```yaml
permissions:
  contents: read         # can clone the repo
  pull-requests: write   # can comment on / approve PRs
  id-token: write        # can request OIDC token (for cloud auth)
  packages: read         # can pull from GitHub Packages
```

**Per the 2026 Actions Security Roadmap**, the default `GITHUB_TOKEN` permissions on new repos are now **read-only**. You must explicitly grant write where needed.

For cross-repo writes (a workflow needs to push to another repo), `GITHUB_TOKEN` doesn't work — use a GitHub App or a fine-grained PAT scoped to that other repo.

---

## 6. GitHub App tokens (for bots and integrations)

The "right" way to run an org-level bot:
1. Create a GitHub App (Settings → Developer settings → GitHub Apps → New).
2. Define permissions + events.
3. Install on the org/repo.
4. Workflow exchanges the App's private key for a short-lived **installation access token**.

Action: `actions/create-github-app-token@v1` or `tibdex/github-app-token`.

```yaml
- uses: actions/create-github-app-token@v1
  id: app-token
  with:
    app-id: ${{ vars.MY_BOT_APP_ID }}
    private-key: ${{ secrets.MY_BOT_PRIVATE_KEY }}
    owner: capitalone

- run: gh pr review --approve 123
  env:
    GH_TOKEN: ${{ steps.app-token.outputs.token }}
```

Why this over a PAT:
- App identity is separate from any human — leaves the org gracefully when a person leaves.
- Tokens expire after 1 hour.
- Permissions are scoped per app installation.
- Audit log entries attribute to the app, not a person.

For Dependabot, release-please, etc. — install as GitHub Apps, not as PAT-authenticated automation.

---

## 7. Commit signing recap (cross-link)

Full details in [module 02](02_config_identity_signing.md). Short version:

- **SSH signing (Git 2.34+)** — reuse your push SSH key. Set `gpg.format = ssh`, `user.signingkey = ~/.ssh/id_ed25519.pub`, `commit.gpgsign = true`. Add the same key to GitHub as a "Signing Key."
- **GPG signing** — generate an ed25519 GPG key, configure git, add public key to GitHub. Heavier setup.
- **In Actions** — auto-signed if commit made by `github-actions[bot]` via API. For other identities, import key from secret via `crazy-max/ghaction-import-gpg`.

Enforce via Ruleset/branch protection: "Require signed commits."

---

## 8. SAML SSO and credential entitlement

At an enterprise on GitHub Enterprise Cloud with SAML SSO (Capital One scenario):

- SAML enforced — every push, every clone, every API call must be authorized via SSO session.
- PATs and SSH keys must be **authorized for SSO** (button in Settings → SSH keys / PATs after enabling SSO at org).
- SCIM provisioning auto-creates and deprovisions accounts as employees join/leave.
- An offboarded employee's credentials are immediately invalidated.

You as the user just go through SSO once a session; credentials work after. As a platform engineer, you ensure every cred type is SSO-authorized so deprovisioning is comprehensive.

Audit log shows SSO-authorized vs unauthorized credential usage — flag the latter.

---

## 9. The summary table

| Use case | Best credential |
|---|---|
| Personal `git push` daily | SSH key |
| Personal CLI scripts hitting GitHub API | `gh auth login` (OAuth) |
| Personal one-off API call | Fine-grained PAT |
| Workflow → another repo write | GitHub App installation token |
| Workflow → same repo (read-only) | `GITHUB_TOKEN` (default permissions) |
| Workflow → AWS | OIDC (see [module 29](29_actions_oidc_aws.md)) — no GitHub credential needed |
| Org-wide automation (DORA dashboards) | GitHub App |
| Migration scripts (one-off bulk operations) | Fine-grained PAT, revoke when done |
| Commit signing (push key reuse) | SSH signing key |
| Commit signing (PGP-shop standard) | GPG key |

---

## 10. Cross-references

- Commit signing setup (the "how") → [module 02](02_config_identity_signing.md).
- The Ruleset rule that enforces signing → [module 11](11_branch_protection_rulesets_codeowners.md).
- `GITHUB_TOKEN` scoping in workflows → [module 31](31_actions_token_cost_templates.md).
- OIDC to AWS (no long-lived AWS creds in GitHub) → [module 29](29_actions_oidc_aws.md).
- GitHub Apps in depth → [module 52](52_apps_webhooks_ghcli_graphql.md).
- SAML SSO + SCIM at the org level → [module 36](36_compliance_sso_scim_audit.md).
