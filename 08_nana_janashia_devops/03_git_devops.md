# 03 — Version Control with Git (DevOps angle)

> Cross-link: [Topic 07 Part A — Git fundamentals (Modules 1–7)](../07_git_github_devops/01_git_architecture_objects.md) covers the object model, internals, signing, recovery, hooks. This module is the **DevOps-specific subset**: what your CI/CD pipeline actually does with Git.

## Why this module exists

In a DevOps pipeline, Git is the *trigger* and the *source of truth*. Push to a branch → webhook fires → pipeline runs → artifacts produced. Tag a commit → release pipeline fires. Merge to main → deploy pipeline fires. If Git isn't disciplined, the pipeline is chaos.

## 1. The minimal Git you must know for pipelines

```bash
git clone <url>
git status
git add <files>
git commit -m "msg"
git push origin <branch>
git pull --ff-only             # avoid surprise merges
git checkout -b feat/new-thing
git rebase main                # linear history (most CI/CD pipelines prefer this)
git merge --no-ff branch       # merge commit (some teams prefer this for traceability)
git tag -a v1.2.3 -m "release"
git push origin v1.2.3
```

## 2. Branching strategies (the three serious options)

See [Topic 07 Module 15 — Branching strategies](../07_git_github_devops/15_branching_strategies.md) for the full deep dive. Short version:

| Strategy | When to use | DevOps fit |
|---|---|---|
| **Git Flow** (Vincent Driessen 2010) | Versioned products, slow release cadence | Out of favor; Driessen himself recants for web apps |
| **GitHub Flow** | Web apps, continuous deploy | Default for SaaS |
| **Trunk-based development** | High-velocity teams, feature flags | Industry gold standard 2026; DORA elite teams use this |

Capital One: trunk-based with very-short-lived branches (< 1 day), feature flags, every merge to `main` triggers prod deploy candidate.

## 3. The CI/CD trigger model

The pipeline lifecycle is driven by Git events:

| Event | Trigger |
|---|---|
| `push` to a branch | Run build + tests; deploy to dev if branch is `main` |
| `pull_request` opened/updated | Run build + tests + static analysis; block merge if fail |
| `tag` push (e.g., `v*`) | Run release pipeline; publish artifact |
| `schedule` (cron) | Nightly builds, dependency scans |
| `workflow_dispatch` / manual | Ad-hoc runs |

Webhook configuration: Jenkins, GitLab, GitHub all use HTTP POST from the Git server → CI server endpoint. Secret-shared signature verifies authenticity.

## 4. Merge requests / pull requests as the DevOps gate

The PR (GitHub) / MR (GitLab) is **the** quality gate. CI status checks must pass before merge:
- Lint passes
- Unit tests pass
- Integration tests pass
- SAST scan green
- SCA scan green
- Code review approval (CODEOWNERS-enforced)
- Branch up-to-date with target

**Branch protection** (GitHub) / **Push Rules + Protected Branches** (GitLab) enforce this. See [Topic 07 Module 11 — Branch protection + Rulesets + CODEOWNERS](../07_git_github_devops/11_branch_protection_rulesets_codeowners.md).

## 5. Rebase vs merge — the DevOps debate

Rebase camp:
- Linear history; easier to `git bisect` for failure introduction
- Cleaner GitHub PR list

Merge camp:
- Preserves the *actual* history (when you branched, when you merged)
- Safer for shared branches (rebasing public history rewrites it for everyone)

**The rule of thumb:** rebase your own feature branch onto target *before* opening the PR; merge (or squash-merge) the PR into target. Never rebase a branch others have pulled.

## 6. `.gitignore` for DevOps repos

Essentials for a Python+Terraform+K8s mixed repo:
```
# Python
__pycache__/
*.pyc
.venv/
venv/
.pytest_cache/

# Terraform
.terraform/
*.tfstate
*.tfstate.backup
*.tfvars
crash.log

# K8s
kubeconfig
*.kubeconfig

# Editor
.vscode/
.idea/
*.swp
.DS_Store

# Secrets
.env
.env.local
*.pem
*.key
credentials.json

# Build artifacts
dist/
build/
*.egg-info/
```

Add `*.tfvars` not `terraform.tfvars` — sometimes you want a *.example.tfvars in repo.

## 7. Git stash + reflog (recovery skills)

```bash
git stash                       # save uncommitted changes
git stash list
git stash pop                   # apply + drop top stash
git stash apply stash@{0}       # apply specific
git stash branch new-branch     # create branch from stash

git reflog                      # the safety net — every HEAD change for 90 days
git reset --hard HEAD@{5}       # restore HEAD to 5 ago
```

Reflog has saved more careers than any tool. If you `git reset --hard` and lose work, reflog → recover.

## 8. Git hooks for DevOps

- `pre-commit` — run linters, secret scanners locally before commit
- `commit-msg` — enforce Conventional Commits format
- `pre-push` — block pushes that would fail CI
- `post-receive` (server-side) — trigger CI/CD

The **pre-commit framework** (https://pre-commit.com) is the industry standard wrapper. Sample `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=500']
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.21.2
    hooks:
      - id: gitleaks
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
      - id: ruff-format
```

Run `pre-commit install` to wire it up, `pre-commit run --all-files` to scan everything.

## 9. Commit signing — required at most regulated shops

SR 11-7 (Federal Reserve model-risk guidance) and SOC 2 both effectively require provable commit attribution. SSH or GPG signed commits provide this.

```bash
# SSH signing (simpler, GitHub-supported since 2022)
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
git config --global commit.gpgsign true
```

GitHub/GitLab will display "Verified" on signed commits. See [Topic 07 Module 12](../07_git_github_devops/12_auth_pat_ssh_signing.md).

## 10. Resolving merge conflicts (you will, every week)

```bash
git pull origin main           # conflict reported
# Edit files; look for <<<<<<<, =======, >>>>>>> markers
git add <resolved-files>
git commit                     # merge commit auto-message
# OR if rebasing:
git rebase --continue
git rebase --abort             # bail out
```

Conflict markers:
```
<<<<<<< HEAD
my version
=======
their version
>>>>>>> main
```

Use a 3-way merge tool (VS Code's built-in, Beyond Compare, Meld) for non-trivial conflicts.

## 11. Quick self-check

1. What's the difference between `git pull` and `git fetch`?
2. When should you NOT rebase a branch?
3. How do you recover a commit you reset --hard away?
4. What's the most aggressive trunk-based-development rule about branch lifetime?
5. Which Git config makes commits SSH-signed by default?

(Answers: pull = fetch + merge/rebase, fetch is read-only; never rebase branches others have pulled or that are public; `git reflog` then `git reset --hard HEAD@{n}`; ≤ 1 day branch lifetime, integrate to trunk daily; `gpg.format ssh` + `commit.gpgsign true` + `user.signingkey` to public key.)
