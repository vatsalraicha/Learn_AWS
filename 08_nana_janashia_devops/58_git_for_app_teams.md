# 58 — Git for Application Teams

> Cross-link: [Topic 07 — Git, GitHub & DevOps (57 modules)](../07_git_github_devops/) is exhaustive. This module is the **beginner-level Git refresher** Nana includes in her IT Fundamentals course.

## 1. The 10-minute Git mental model

```
Working tree → git add → Staging area → git commit → Local repo → git push → Remote
                                                                       ← git pull ←
```

- **Working tree** — your files on disk
- **Staging area** — what's queued for the next commit
- **Local repo** — commits on your machine
- **Remote** — origin (GitHub/GitLab/etc.)

## 2. Setting up Git for the first time

```bash
git config --global user.name "Vatsal Raicha"
git config --global user.email "vatsal.raicha@gmail.com"
git config --global init.defaultBranch main
git config --global pull.rebase true        # rebase instead of merge on pull
git config --global core.editor "code --wait"

# SSH key for GitHub/GitLab
ssh-keygen -t ed25519 -C "vatsal@laptop"
# Copy public key to GitHub: Settings → SSH and GPG keys → New SSH key
cat ~/.ssh/id_ed25519.pub
```

## 3. Cloning + initializing

```bash
# Clone existing
git clone git@github.com:org/repo.git

# Initialize new
mkdir my-app && cd my-app
git init
git remote add origin git@github.com:org/my-app.git
echo "# my-app" > README.md
git add README.md
git commit -m "initial commit"
git push -u origin main
```

## 4. The daily Git loop

```bash
# Check status
git status

# Pull latest from main
git checkout main
git pull

# Create feature branch
git checkout -b feat/add-login

# Make changes, then:
git add src/login.js
git status         # confirm what's staged
git diff --cached  # review staged diff
git commit -m "feat: add login page"

# Push
git push -u origin feat/add-login

# Open PR on GitHub/GitLab in browser
```

## 5. `.gitignore` (essentials)

```
# Node
node_modules/
dist/
build/
*.log

# Python
__pycache__/
*.pyc
.venv/
.pytest_cache/

# IDE
.vscode/
.idea/
*.swp
.DS_Store

# Env / secrets
.env
.env.local
*.pem

# OS
Thumbs.db
```

Use https://gitignore.io to generate one for your stack.

## 6. Resolving merge conflicts

You pull, conflict reported:
```bash
$ git pull
Auto-merging src/auth.js
CONFLICT (content): Merge conflict in src/auth.js
```

Open the conflicted file; you'll see:
```
<<<<<<< HEAD
const apiKey = process.env.API_KEY_NEW
=======
const apiKey = process.env.API_KEY
>>>>>>> origin/main
```

Edit to resolve (pick one, both, or neither), remove the markers, then:
```bash
git add src/auth.js
git commit          # or git rebase --continue if rebasing
```

Use VS Code's built-in merge editor or a dedicated tool (Meld, Beyond Compare).

## 7. Commit message style (Conventional Commits)

```
feat: add user dashboard
fix: handle null email in login
docs: update README
refactor: extract auth helper
test: add user controller tests
chore: bump deps
feat!: change API contract (breaking)
```

The `<type>:` prefix makes commits scannable + parseable by release automation.

## 8. Branching strategies recap

| Strategy | When |
|---|---|
| **GitHub Flow** | Web apps, SaaS, continuous deploy |
| **Trunk-based** | High-velocity teams; feature flags |
| **Git Flow** | Versioned products (declining for SaaS) |

Most modern teams in 2026: GitHub Flow or Trunk-based.

## 9. Pulling changes

```bash
git pull                  # fetch + merge
git pull --rebase         # fetch + rebase (cleaner history)
git fetch origin          # download but don't merge
git fetch --all --prune   # update all + remove deleted branches
```

Set rebase default:
```bash
git config --global pull.rebase true
```

## 10. Branches

```bash
git branch                    # list local
git branch -a                 # list all incl. remote
git checkout -b feat/x        # create + switch
git switch feat/x             # switch (modern)
git switch -c feat/x          # create + switch (modern)
git push -u origin feat/x     # push and track
git branch -d feat/x          # delete local (safe — refuses if unmerged)
git branch -D feat/x          # delete local (force)
git push origin --delete feat/x   # delete remote
```

## 11. Merge Requests / Pull Requests

The MR/PR is the **collaboration unit**. Workflow:
1. Push feature branch
2. Open MR/PR
3. CI runs (tests, lint, security scans)
4. Reviewer comments
5. Address comments; push more commits
6. Approver clicks "Merge" (often with squash)
7. Delete branch

## 12. Deleting branches after merge

```bash
git checkout main
git pull
git branch -d feat/x          # local
# GitHub/GitLab usually auto-deletes remote branch after merge
```

For batch cleanup of merged branches:
```bash
git branch --merged main | grep -v '^\*\|main' | xargs git branch -d
```

## 13. Recovering from mistakes

```bash
# Undo last commit but keep changes staged
git reset --soft HEAD~1

# Undo last commit and changes (DESTRUCTIVE)
git reset --hard HEAD~1

# Reset to a remote state
git reset --hard origin/main

# Recover something from reflog (the safety net)
git reflog
git reset --hard HEAD@{5}
```

Reflog keeps everything for ~90 days — even "lost" commits.

## 14. Quick self-check

1. What's the difference between `git pull` and `git fetch`?
2. What does `git switch` give you over `git checkout`?
3. What's the Conventional Commits format?
4. What's the difference between `-d` and `-D` when deleting a branch?
5. Where's the safety net when you `git reset --hard` by accident?

(Answers: pull = fetch + merge/rebase, fetch only downloads (read-only); clearer intent — switch is for branches, restore is for files (vs checkout doing both confusingly); `<type>(scope)?: subject` with feat/fix/docs/refactor/test/chore types; `-d` refuses to delete unmerged branches, `-D` forces; `git reflog` — keeps every HEAD movement for ~90 days, can `git reset --hard HEAD@{n}` to recover.)
