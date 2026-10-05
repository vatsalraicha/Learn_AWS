# 02 — Configuration, identity & signing setup (SSH + GPG)

> *"At a regulated bank, an unsigned commit is an anonymous commit."*

## Why this module exists

At a small startup, `git config user.email` is a one-time chore. At Capital One, your identity + signing posture is enforced by **Rulesets / branch protection** ("require signed commits"), audited via the GitHub audit log, and tied to your SSO identity via SCIM. This module covers the configuration layers and the two signing paths (GPG and SSH) — pick SSH for new setups; it's simpler and Git 2.34+ supports it natively.

---

## 1. The three config layers

```
$XDG_CONFIG_HOME/git/config  or  ~/.gitconfig    (user-global)
.git/config                                        (repo-local)
/etc/gitconfig                                     (system-wide; rarely used)
```

Precedence: **local > global > system**. Use `git config --list --show-origin` to see exactly which file set each value.

```bash
# user-global identity (what you want for personal repos)
git config --global user.name  "Vatsal Raicha"
git config --global user.email "vatsal.raicha@gmail.com"

# repo-local override (e.g., when working on a client repo with a different email)
cd ~/work/capital-one-repo
git config --local user.email "vatsal.raicha@capitalone.com"
```

**Conditional includes** (Git 2.13+) let you switch identities by directory:

```ini
# ~/.gitconfig
[user]
    name  = Vatsal Raicha
    email = vatsal.raicha@gmail.com   # default

[includeIf "gitdir:~/work/capital-one/"]
    path = ~/.gitconfig-capitalone

# ~/.gitconfig-capitalone
[user]
    email = vatsal.raicha@capitalone.com
    signingkey = SSH-FINGERPRINT-HERE
[commit]
    gpgsign = true
```

Open any repo under `~/work/capital-one/` and your commits automatically use the work email + signing key.

---

## 2. Settings every Sr Lead should set

```bash
# Modern defaults
git config --global init.defaultBranch main
git config --global pull.rebase true              # avoid messy merge commits on pull
git config --global push.autoSetupRemote true     # auto-set upstream on first push
git config --global push.default simple           # only push current branch
git config --global fetch.prune true              # prune deleted remote branches on fetch

# Better diffs
git config --global diff.algorithm histogram      # better than default 'myers' for most code
git config --global diff.colorMoved zebra         # highlight moved blocks
git config --global merge.conflictStyle zdiff3    # show common ancestor in conflicts (since 2.35)

# Performance on big repos
git config --global core.fsmonitor true           # use OS file-system monitor (mac/win)
git config --global core.untrackedCache true
git config --global feature.manyFiles true        # since 2.24 — index v4 + commit graph

# Editor + pager
git config --global core.editor "nvim"            # or 'code --wait' for VS Code
git config --global core.pager "delta"            # delta = better pager for diffs

# Aliases (controversial — these are mine)
git config --global alias.lg  "log --oneline --graph --decorate --all"
git config --global alias.st  "status -sb"
git config --global alias.co  "checkout"
git config --global alias.sw  "switch"
git config --global alias.rs  "restore"
git config --global alias.amend "commit --amend --no-edit"
```

`zdiff3` (Git 2.35+) is the underrated one. In a merge conflict it shows you `<<<<<<<` (yours) / `|||||||` (**common ancestor**) / `=======` / `>>>>>>>` (theirs). The common-ancestor block tells you *why* the conflict exists, which is often more useful than the two competing versions.

---

## 3. Commit signing — the bank requirement

A **signed commit** has a cryptographic signature proving the listed author actually created the commit. The signature is stored as part of the commit object and verifiable by anyone with the signer's public key.

Why banks require it:
- Without signing, the `Author: Jane Doe <jane@bank.com>` line is **just a string**. Anyone with commit access can spoof it. `git commit --author="CEO <ceo@bank.com>" -m "fix"` works on any clone.
- Signed + verified commits are visible in GitHub (green "Verified" badge) and enforced by branch protection / Rulesets ("Require signed commits").
- For SR 11-7 audit trails: every commit that touches a model artifact must be tied to a verifiable identity, years later.

Two signing methods:

| Method | Setup complexity | Reuses existing key | Status |
|---|---|---|---|
| **GPG** | High (keyring, agent, subkeys) | Maybe (if you already use PGP for email) | Original; works everywhere |
| **SSH** (Git 2.34+) | Low (reuse your SSH key) | **Yes** — same key you push with | Preferred for new setups |
| S/MIME | Niche; corp X.509 cert | Maybe | Rare in OSS, common in enterprise CA-based shops |

---

## 4. SSH signing (the easy path)

You already have an SSH key for pushing to GitHub. Reuse it for signing.

```bash
# Tell git which key to sign with (use a key that you've also added to GitHub)
git config --global user.signingkey ~/.ssh/id_ed25519.pub
git config --global gpg.format ssh
git config --global commit.gpgsign true   # sign every commit
git config --global tag.gpgsign true      # sign every annotated tag

# For local-only verification (`git log --show-signature`):
echo "vatsal.raicha@gmail.com $(cat ~/.ssh/id_ed25519.pub)" >> ~/.config/git/allowed_signers
git config --global gpg.ssh.allowedSignersFile ~/.config/git/allowed_signers
```

Then on GitHub: **Settings → SSH and GPG keys → New SSH key → key type: "Signing Key"** (same key can be both an Authentication Key and a Signing Key — but each role needs its own entry).

Verify it works:

```bash
git commit --allow-empty -m "test signing"
git log --show-signature -1
# Good "git" signature for vatsal.raicha@gmail.com with ED25519 key ...
```

Push to GitHub — the commit should show a green **Verified** badge.

---

## 5. GPG signing (the long-tail path)

You'll still encounter GPG, especially at orgs that standardized before 2.34.

```bash
# 1) Generate a key — use ed25519, not RSA-4096 (faster, smaller, same security)
gpg --quick-generate-key "Vatsal Raicha <vatsal.raicha@gmail.com>" ed25519 sign 2y

# 2) Find the key ID
gpg --list-secret-keys --keyid-format=long
# sec   ed25519/ABC123DEF4567890 2026-05-21 [SC] [expires: 2028-05-21]

# 3) Configure git
git config --global user.signingkey ABC123DEF4567890
git config --global commit.gpgsign true

# 4) Add public key to GitHub (Settings → SSH and GPG keys → New GPG key)
gpg --armor --export ABC123DEF4567890   # paste this into GitHub

# 5) macOS: install pinentry so gpg can prompt for passphrase
brew install pinentry-mac gnupg
echo "pinentry-program $(brew --prefix)/bin/pinentry-mac" >> ~/.gnupg/gpg-agent.conf
gpgconf --kill gpg-agent
```

**Pitfalls**:
- `error: gpg failed to sign the data` — usually pinentry-agent issue. `export GPG_TTY=$(tty)` in your shell rc.
- Key expired — re-extend with `gpg --quick-set-expire <KEYID> 2y` and re-upload to GitHub.
- GitHub Verified badge depends on the **email in the commit** matching one of the **verified emails on the GPG key UID AND in your GitHub account**. All three must match.

---

## 6. Signing in GitHub Actions

Actions runs in an ephemeral container — no key on disk. Two options:

**Option A — let GitHub sign it** (easiest, for bot commits):
GitHub auto-signs commits made by the `github-actions[bot]` identity. Use the `actions/github-script` or `actions/checkout` then commit via API — the commit is automatically Verified.

**Option B — provide a key as a secret**:

```yaml
- name: Import GPG key
  uses: crazy-max/ghaction-import-gpg@v6
  with:
    gpg_private_key: ${{ secrets.BOT_GPG_PRIVATE_KEY }}
    passphrase: ${{ secrets.BOT_GPG_PASSPHRASE }}
    git_user_signingkey: true
    git_commit_gpgsign: true
- run: |
    git commit -m "automated: bump deps"
    git push
```

For SSH signing, equivalent action exists. At Capital One scale, you'd use a dedicated "bot" GPG identity for automation, separate from any human's identity, with its key stored in Secrets Manager and exposed via OIDC + Action.

---

## 7. Verifying others' signatures

```bash
git log --show-signature                          # show signature on every commit in log
git verify-commit <SHA>                            # verify one specific commit
git config --global log.showSignature true        # always show on log
```

To verify SSH-signed commits locally, you need an `allowedSignersFile` listing the principals (emails) and their public keys you trust. At an enterprise, the platform team distributes this file (sourced from SCIM-synced GitHub SSH keys); locally, you maintain your own.

---

## 8. The credential helper

For HTTPS-based push (rarely used at enterprise — SSH or OAuth via `gh` is preferred), the credential helper avoids re-prompting:

```bash
# macOS — uses the Keychain
git config --global credential.helper osxkeychain

# Cross-platform — uses the `gh` CLI
git config --global credential.helper "!gh auth git-credential"
```

Don't use `git config credential.helper store` — it writes credentials in plaintext to `~/.git-credentials`.

---

## 9. Cross-references

- The Rulesets/branch protection rule that **enforces** signing on a branch → [module 11](11_branch_protection_rulesets_codeowners.md).
- PAT vs SSH vs OAuth for authentication → [module 12](12_auth_pat_ssh_signing.md).
- Audit-log evidence of signing posture (compliance) → [module 36](36_compliance_sso_scim_audit.md).
- SR 11-7 implications of identity binding → [module 37](37_compliance_sr117_audit.md).
