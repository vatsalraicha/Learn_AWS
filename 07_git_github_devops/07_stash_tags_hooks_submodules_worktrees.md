# 07 — Stash, tags, hooks, submodules, worktrees

> *"The 'rest of Git' — each tool solves exactly one problem. Knowing which one is the senior move."*

## Why this module exists

Beyond commit/branch/merge, Git has five smaller subsystems that show up in real engineering: **stash** (parking changes), **tags** (immutable refs), **hooks** (local automation), **submodules** (repos inside repos), and **worktrees** (multiple working trees from one repo). Each has a narrow correct use. Most teams misuse at least one. Let's clear them up.

---

## 1. Stash — park changes temporarily

You're mid-feature; an urgent bug needs your attention on `main`. You don't want to commit WIP yet.

```bash
git stash                                          # stash tracked changes (NOT untracked)
git stash -u                                       # also include untracked files (often what you want)
git stash -a                                       # also include ignored files (rare)
git stash push -m "WIP on feature-x"               # named stash
git stash push -m "msg" -- file1.py file2.py       # stash specific files only

git stash list                                     # list all stashes (newest = stash@{0})
git stash show stash@{0}                           # show summary
git stash show -p stash@{0}                        # show diff

git stash pop                                      # apply newest stash + delete
git stash apply stash@{2}                          # apply specific stash, keep it in list
git stash drop stash@{1}                           # delete without applying
git stash clear                                    # delete all stashes

git stash branch <branch-name> stash@{0}           # create branch from stash, apply, drop
```

**Stash is local-only and global to the repo.** Stashes are stored under `.git/refs/stash` (a reflog of stashed states). They're not shared via push. If you `rm -rf .git/` you lose them.

**Better than stash for anything non-trivial**: commit a WIP commit (`git commit -m "WIP"`), switch branches, then `git reset --soft HEAD~1` when you return. WIP commits are reflog-protected for 90 days; stashes lose to careless `git stash drop`.

---

## 2. Tags — immutable reference points

Two kinds:

```bash
# Lightweight tag — just a name → SHA pointer
git tag v1.0.0

# Annotated tag — a full object with tagger, date, message (PREFER THIS)
git tag -a v1.0.0 -m "Release 1.0.0"

# Signed tag — annotated + cryptographically signed (RELEASE ENGINEERING STANDARD)
git tag -s v1.0.0 -m "Release 1.0.0"

git tag                                            # list local tags
git tag -l 'v1.*'                                  # filter
git push origin v1.0.0                             # push specific tag
git push --tags                                    # push all tags (use sparingly)
git push --follow-tags                             # push tags reachable from pushed commits

git tag -d v1.0.0                                  # delete local tag
git push origin --delete v1.0.0                   # delete remote tag

git show v1.0.0                                    # show tag + commit info
git describe --tags HEAD                           # "v1.0.0-3-gabc123" (3 commits past v1.0.0)
```

**Use annotated tags for releases**, always. Lightweight tags carry no metadata; annotated tags carry author/date/message and can be signed. GitHub Releases require annotated tags to attach changelog/binaries cleanly.

### Semantic Versioning (SemVer) refresher

`MAJOR.MINOR.PATCH` — `1.2.3`
- **MAJOR**: incompatible API change
- **MINOR**: added functionality, backward compatible
- **PATCH**: bug fix, backward compatible
- Optional pre-release: `1.2.3-rc.1`, `1.2.3-alpha`
- Optional build metadata: `1.2.3+20260521`

Tag every release. Automate the tag bump with **release-please** or **semantic-release** driven by Conventional Commits (see [module 19](19_templates_adr_docs_conventional_commits.md)).

---

## 3. Hooks — local automation

Hooks are shell scripts in `.git/hooks/` that Git runs at specific points in its lifecycle. Standard ones:

| Hook | Fires when | Common use |
|---|---|---|
| `pre-commit` | Before commit message editor opens | Run linters, formatters, tests |
| `prepare-commit-msg` | Before commit message editor opens | Pre-fill template (e.g., JIRA ticket from branch name) |
| `commit-msg` | After commit message is written | Validate format (Conventional Commits) |
| `pre-push` | Before push | Run integration tests, check for unsigned commits |
| `post-checkout` | After branch switch | Activate venv, install deps |
| `post-merge` | After merge | Re-install deps if `requirements.txt` changed |

**The problem with `.git/hooks/`**: not version-controlled. Every clone needs to install them. Don't write hooks directly there.

**The solution**: the **`pre-commit` framework** ([pre-commit.com](https://pre-commit.com/)). A standalone tool with a `.pre-commit-config.yaml` in your repo. Anyone clones, runs `pre-commit install`, gets the team's hooks. Cross-language (Python, JS, Rust, shell hooks all work).

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=500']

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/kynan/nbstripout
    rev: 0.7.1
    hooks:
      - id: nbstripout
```

```bash
brew install pre-commit
pre-commit install                # install into .git/hooks/pre-commit
pre-commit run --all-files        # run on every file (great for first-time setup)
pre-commit autoupdate             # bump rev: pins
```

We cover the full ML pre-commit stack in [module 40](40_precommit_reproducibility_refactor.md).

---

## 4. Submodules — repos inside repos

A submodule is a pointer to a specific commit of another repo, embedded in your repo.

```bash
git submodule add git@github.com:org/lib.git vendor/lib
git submodule init                                # initialize submodule configs
git submodule update --init --recursive          # clone submodule contents
git clone --recurse-submodules <url>             # clone parent + all submodules at once

# Update submodule to its remote's latest
cd vendor/lib
git fetch && git checkout main && git pull
cd ../..
git add vendor/lib
git commit -m "update vendor/lib to latest"
```

**The submodule problem**:
- `git status` in parent shows "modified" when submodule's HEAD moved — confusing.
- Clones forget `--recurse-submodules`, leaving empty directories.
- Two submodules updating each other becomes a coordination nightmare.
- CI must handle them explicitly.

**Better alternatives in 2026**:
- Package managers (pip, npm, cargo). If the dependency has a registry, use it.
- Monorepo + Bazel/Nx/Pants. If you control all the code, put it together.
- **Subtree merging** (less popular but no submodule overhead).
- For private dependencies needing source visibility: published private package on Artifactory/CodeArtifact.

Submodules are appropriate when: vendoring an unmodified upstream you'll need to update on a deliberate cadence, AND there's no good package distribution path. That's a smaller set of cases than people use them for.

---

## 5. Worktrees — multiple checkouts of one repo

A worktree is a separate working directory backed by the same `.git/` repo. You can have `main` checked out in one directory and `feature-x` in another, simultaneously.

```bash
git worktree add ../my-project-feature-x feature-x      # create worktree at ../my-project-feature-x
git worktree add ../my-project-hotfix -b hotfix main    # create worktree on new branch

git worktree list
# /Users/vr/Code/my-project           4f9a2b3 [main]
# /Users/vr/Code/my-project-feature-x 1a2b3c4 [feature-x]
# /Users/vr/Code/my-project-hotfix    4f9a2b3 [hotfix]

git worktree remove ../my-project-feature-x
git worktree prune                                       # remove stale worktree entries
```

**Why use worktrees**:
- Long-running build/test on one branch; do unrelated work on another without switching.
- Reviewing a PR locally (`gh pr checkout` + worktree) without stashing your current work.
- Comparing behavior between two branches by running both simultaneously.
- ML training on branch A while you iterate on branch B.

**Limitations**:
- A branch can be checked out in only one worktree at a time (Git enforces).
- All worktrees share the same submodule state (mostly).
- Some IDEs get confused.

The Claude Code `EnterWorktree` tool, GH Actions matrix workflows, and `git for-each-ref` over worktrees all build on this.

---

## 6. Combining them — a real scenario

You're working on `feature-x` in your main worktree. A teammate opens a PR you need to review.

```bash
# Without losing your work:
git stash -u                                      # park your WIP

# Option A — review in same worktree
gh pr checkout 123
# ... review, comment ...
git switch feature-x
git stash pop

# Option B — review in a fresh worktree (BETTER)
git worktree add ../my-project-pr-123
cd ../my-project-pr-123
gh pr checkout 123                                # checks out the PR's branch here
# ... review ...
cd ../my-project
# (Your original work is untouched; no stash needed)
git worktree remove ../my-project-pr-123
```

Worktrees + `gh pr checkout` is the senior code-review setup. No context-switching overhead.

---

## 7. The right-tool table

| Need | Right tool |
|---|---|
| Park changes <30 min | `git stash` (or commit WIP + reset later) |
| Park changes >30 min | Commit WIP, push to your fork, return later |
| Mark a release | Annotated (or signed) tag |
| Mark every PR-merged version | release-please / semantic-release automation |
| Run linter at commit time | `pre-commit` framework |
| Run tests before pushing | `pre-push` hook (via pre-commit) |
| Vendor an external dependency you don't own | Package registry > submodule > vendored copy |
| Vendor internal code shared across repos | Internal package registry; submodule as last resort |
| Two checkouts of same repo simultaneously | `git worktree` |
| Cherry-pick across worktrees | Same `.git/` — `git log` shows everything |

---

## 8. Cross-references

- The pre-commit framework deeply applied to ML → [module 40](40_precommit_reproducibility_refactor.md).
- Notebook-specific hooks (`nbstripout`, `jupytext`) → [module 38](38_notebook_discipline.md).
- Conventional Commits + release-please for automated tagging → [module 19](19_templates_adr_docs_conventional_commits.md).
- Worktrees in CI for matrix-of-branches builds → [module 21](21_actions_jobs_steps_runners.md).
