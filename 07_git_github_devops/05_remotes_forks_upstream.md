# 05 — Remote operations: fetch/pull/push, forks, upstream sync

> *"`fetch` is read-only. `pull` is a fetch plus a merge — that's two operations in one command, which is one too many."*

## Why this module exists

A remote is just another Git repo Git can talk to. The whole "GitHub workflow" — clone, branch, push, PR, sync — is built on a handful of plumbing commands (`fetch`, `push`, `remote`) wrapped by the higher-level Git porcelain. At Capital One scale with InnerSource, you'll work in **fork-of-an-org-repo** patterns where the difference between `origin` and `upstream` matters daily. Get this fluent.

---

## 1. The remote model

A **remote** is a named URL. `origin` is the conventional name for the one you cloned from.

```bash
git remote -v                                      # list remotes with URLs
git remote add origin git@github.com:org/repo.git
git remote add upstream git@github.com:org/repo.git
git remote remove old-name
git remote rename old new
git remote set-url origin git@github.com:org/repo.git   # change URL (e.g., SSH→HTTPS)
git remote show origin                              # detailed info about a remote
```

Each remote has its own set of **remote-tracking branches** under `refs/remotes/<remote>/<branch>` — these are read-only locally; they're updated only by `git fetch`.

```bash
git branch -a
# * main
#   feature-x
#   remotes/origin/HEAD -> origin/main
#   remotes/origin/main
#   remotes/origin/feature-y
#   remotes/upstream/main
```

---

## 2. Fetch — the read-only network operation

```bash
git fetch                          # fetch from origin (default)
git fetch upstream                 # fetch from a specific remote
git fetch --all                    # fetch from all remotes
git fetch --prune                  # remove remote-tracking branches whose remote branch is gone
git fetch origin main              # only fetch a specific branch
git fetch --tags                   # also fetch tags
```

`git fetch` updates `refs/remotes/origin/*` and downloads new objects. **It never touches your working tree or local branches.** Your `main` doesn't move; only `origin/main` does.

After fetch:

```bash
git log main..origin/main          # what's on origin/main that I don't have
git log origin/main..main          # what I have that origin doesn't (commits to push)
```

Set `fetch.prune = true` globally so fetch automatically removes references to deleted remote branches. Without it, you accumulate dead refs forever.

---

## 3. Pull — fetch + integrate

```bash
git pull                           # fetch origin, then merge origin/<current-branch> into current
git pull --rebase                  # fetch origin, then rebase current onto origin/<current-branch>
git pull --ff-only                 # only allow fast-forward — abort if a merge would be needed
```

Defaults (set globally once and forget):

```bash
git config --global pull.rebase true       # rebase on pull (not merge)
git config --global pull.ff only           # safety: never auto-merge
```

The `--rebase` default avoids the "merge commit on every pull" mess that pollutes history in active branches. The `--ff-only` belt-and-braces means if rebase would conflict, Git refuses and you handle it deliberately.

---

## 4. Push

```bash
git push                                       # push current branch to its upstream
git push origin feature-x                     # explicit branch
git push -u origin feature-x                  # set upstream (first push of a new branch)
git push --tags                                # also push tags
git push origin --delete feature-x            # delete branch on remote
git push --force                               # DANGEROUS — overwrites remote history
git push --force-with-lease                   # SAFER — only if remote hasn't moved since last fetch
git push --force-with-lease=feature-x:<SHA>   # even safer — only if remote points at SHA
```

**Use `--force-with-lease`, never `--force`.** The difference: `--force` overwrites whatever's on the remote. `--force-with-lease` checks "is the remote still at the SHA I last saw?" — if a teammate pushed in between, the operation fails (loudly), telling you to fetch first.

Set `push.autoSetupRemote = true` so `git push` on a new branch automatically does `-u origin <branch>` without you remembering.

`push.default` recommended value: `simple` (only push current branch, refuse if no upstream — Git's default since 2.0).

---

## 5. Tracking branches (upstream)

A local branch can **track** a remote-tracking branch. This makes `git status` show "ahead/behind by N commits" and lets you `git push` / `git pull` without arguments.

```bash
git branch --set-upstream-to=origin/main main    # set tracking
git branch -vv                                    # show tracking + ahead/behind
git checkout -t origin/feature-y                 # create + check out tracking branch
git switch -c feature-y origin/feature-y         # equivalent (preferred)
```

When you `git clone`, `main` is automatically set to track `origin/main`. When you `git switch -c new-branch && git push -u origin new-branch`, the upstream is set.

---

## 6. The fork workflow (InnerSource at Capital One)

You don't have write access to the central repo. You fork it on GitHub, make changes in your fork, open a PR back to the upstream.

```bash
# 1) Fork via GitHub UI: github.com/capitalone/cool-lib → click "Fork"

# 2) Clone YOUR fork
git clone git@github.com:vraicha/cool-lib.git
cd cool-lib

# 3) Add the upstream remote
git remote add upstream git@github.com:capitalone/cool-lib.git
git remote -v
# origin    git@github.com:vraicha/cool-lib.git (fetch+push) — your fork
# upstream  git@github.com:capitalone/cool-lib.git (fetch+push) — the real repo

# 4) Make your fork's main track upstream/main (DON'T push to it via origin/main)
git fetch upstream
git branch -u upstream/main main

# 5) Work in feature branches
git switch -c add-cool-feature
# ... edits ...
git commit -m "feat: add cool feature"
git push -u origin add-cool-feature

# 6) Open PR via gh CLI or web UI
gh pr create --repo capitalone/cool-lib --base main --head vraicha:add-cool-feature
```

**Keeping your fork in sync** (do this regularly — daily on busy repos):

```bash
git fetch upstream
git switch main
git rebase upstream/main         # main is now identical to upstream/main
git push origin main             # update your fork's main on GitHub

# For active feature branches, rebase them onto fresh upstream main too:
git switch add-cool-feature
git rebase upstream/main
git push --force-with-lease     # force-push (your fork, your branch — OK)
```

`gh repo sync` (GitHub CLI) automates step 4 in one command: `gh repo sync vraicha/cool-lib`.

---

## 7. The refspec (when you need to know)

The hidden parameter behind `git fetch` / `git push` is the **refspec**: `+<src>:<dst>`.

```bash
git push origin feature-x:main             # push local feature-x to remote main (rare)
git fetch origin '+refs/heads/*:refs/remotes/origin/*'   # standard refspec for `fetch = ...` line
```

Look in `.git/config`:

```ini
[remote "origin"]
    url = git@github.com:org/repo.git
    fetch = +refs/heads/*:refs/remotes/origin/*
```

The `+` means "force update even if not fast-forward." Standard refspecs map all remote branches into your `refs/remotes/origin/` namespace.

You'll rarely write refspecs by hand. But seeing one in CI scripts or `.git/config` shouldn't confuse you.

---

## 8. Shallow & partial clones in CI

```bash
# Old CI pattern (ubiquitous in GH Actions older configs)
git clone --depth 1 ...

# Modern pattern — partial clone, fetches blobs on demand
git clone --filter=blob:none ...

# Once cloned shallow, you can "deepen" or unshallow
git fetch --deepen 100
git fetch --unshallow
```

`actions/checkout` default `fetch-depth: 1` (shallow). If your CI needs full history (e.g., for `git log` based versioning, or `release-please`), set `fetch-depth: 0`. Partial clone (`filter=blob:none`) is faster than full but provides full ref history — best of both worlds for most CI.

---

## 9. Common breakage and fixes

| Symptom | Likely cause | Fix |
|---|---|---|
| `git push` rejected, "non-fast-forward" | Someone else pushed after your last pull | `git pull --rebase` then push again |
| `git pull` creates an unwanted merge commit | `pull.rebase` not set to true | `git config --global pull.rebase true`; for now, `git reset --hard HEAD~1` and `git pull --rebase` |
| `git push --force-with-lease` rejected | Remote moved since last fetch | `git fetch` first, review what changed, decide whether to incorporate |
| Tons of `refs/remotes/origin/dead-branch` | `fetch.prune` not set | `git config --global fetch.prune true`; `git fetch --prune` now |
| "fatal: refusing to merge unrelated histories" | Two repos with different roots | Almost always a mistake; use `--allow-unrelated-histories` only if intentional (e.g., merging an archived sub-repo) |
| Your fork's `main` diverged from upstream | You merged PRs directly into your fork's main | Reset: `git switch main && git fetch upstream && git reset --hard upstream/main && git push --force-with-lease origin main` |

---

## 10. Cross-references

- The PR side of the fork workflow (review, status checks, merge) → [module 10](10_prs_code_review_merge.md).
- `gh repo sync`, `gh pr create`, and CLI patterns → [module 14](14_gh_cli_fundamentals.md).
- InnerSource vs open-source workflows → [module 16](16_feature_flags_innersource.md).
- Why force-with-lease is the right hammer → [module 06](06_undo_recovery.md).
