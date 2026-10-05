# 06 — Undo & recovery: reset, revert, restore, reflog, blame, bisect

> *"In Git, nothing is truly lost for 90 days. If you remember nothing else from this topic, remember `git reflog`."*

## Why this module exists

The senior signal here is calmness. When prod breaks at 2am, the engineer who knows `reflog`, `reset`, `revert`, and `bisect` cold is the one who fixes it. The engineer who reaches for Stack Overflow makes it worse.

This module is the survival kit.

---

## 1. The "I just did something stupid" decision tree

```
Did you commit?
├── NO  ─→ Did you stage?
│         ├── NO  → `git restore <file>`            (discard working-tree changes — LOSES WORK)
│         └── YES → `git restore --staged <file>`   (unstage; working tree untouched)
│
└── YES ─→ Has the commit been pushed AND pulled by others?
          ├── NO  → `git reset --soft HEAD~1`       (uncommit, keep changes staged)
          │   or → `git reset --mixed HEAD~1`       (uncommit, keep changes unstaged) — DEFAULT
          │   or → `git reset --hard HEAD~1`        (uncommit + DISCARD changes)
          │   or → `git commit --amend`             (edit the last commit in place)
          │
          └── YES → `git revert <SHA>`              (new commit that undoes the bad one — SAFE)
```

The cardinal rule: **`reset --hard` is destructive locally; `revert` is safe and shareable.**

---

## 2. Reset — three flavors

`git reset` moves the branch ref. The flavor controls what it does to the index and working tree.

| Flag | Branch ref | Index | Working tree | Use when |
|---|---|---|---|---|
| `--soft` | Moves | Untouched (still staged) | Untouched | You committed too early; want to add more before re-committing |
| `--mixed` (default) | Moves | Reset to match new HEAD | Untouched | You committed too early; want to re-stage selectively |
| `--hard` | Moves | Reset to match new HEAD | **Reset to match new HEAD** | You want to discard commits AND working-tree changes — irreversible |

```bash
git reset --soft HEAD~1          # "undo my last commit but keep my work staged"
git reset --mixed HEAD~3         # "uncommit the last 3 commits, leave changes in working tree"
git reset --hard origin/main     # "make my branch identical to origin/main" — destroys local commits
git reset --hard HEAD            # "discard all uncommitted changes"
```

**`reset --hard`** is what people regret most. It silently drops uncommitted work. The recovery (if you're fast enough) is the reflog (next section).

---

## 3. The reflog — your 90-day safety net

```bash
git reflog                       # all HEAD movements in this clone
git reflog show feature-x        # movements of a specific branch
git reflog expire --expire=now --all   # purge (rarely used; for security)
```

Output:

```
4f9a2b3 HEAD@{0}: reset: moving to HEAD~3
1a2b3c4 HEAD@{1}: commit: feat: add token caching
9z8y7x6 HEAD@{2}: commit: refactor: extract helper
...
```

To recover the "lost" commit:

```bash
git reset --hard 1a2b3c4          # back to where you were 2 moves ago
# or, create a branch pointing at it:
git branch recovered 1a2b3c4
```

The reflog is **per-clone, local-only.** Cloning fresh = no reflog from the old clone. Default retention: **90 days for reachable refs, 30 days for unreachable** (configurable via `gc.reflogExpire` and `gc.reflogExpireUnreachable`).

**This is why "force-pushed branch destroyed my work" is recoverable for 90 days locally** — find the old SHA in your reflog, `git push --force-with-lease origin <SHA>:<branch>`.

---

## 4. Revert — the shareable undo

`git revert <SHA>` creates a *new commit* whose diff is the inverse of `<SHA>`'s diff. Safe for shared history because nothing is rewritten.

```bash
git revert <SHA>                            # creates a "Revert <commit-msg>" commit
git revert HEAD~3..HEAD                     # revert a range (creates one commit per)
git revert --no-commit <SHA1> <SHA2>        # apply reverts, leave staged for combined commit
git revert -m 1 <merge-SHA>                 # revert a merge commit, keeping mainline parent (1)
```

**Reverting a merge commit** is the gotcha: a merge has two parents, so Git asks which mainline to keep with `-m 1` (the first parent, usually the target branch) or `-m 2`. After reverting a merge, if you want to re-merge later, you need to revert the revert (yes, really) or rebase the branch onto current main and merge again.

---

## 5. Restore — discard or unstage

Added in Git 2.23 to disambiguate `git checkout`'s overloaded behavior.

```bash
git restore file.py              # discard working-tree changes to file.py (LOSES WORK)
git restore --staged file.py     # unstage file.py (working tree untouched)
git restore --source=HEAD~3 file.py    # set file.py to its content at 3 commits ago

git restore .                    # discard ALL working-tree changes — careful
git restore --staged .           # unstage everything
```

Use `restore` instead of `checkout` for these operations. Reserve `checkout` for branch operations (and even there, prefer `switch`).

---

## 6. Blame — who, when, why

```bash
git blame file.py                            # who last touched each line
git blame -L 42,50 file.py                  # only lines 42-50
git blame -L '/function_name/,/^}/' file.py # blame a function (regex range)
git blame -w                                 # ignore whitespace-only changes (find real edits)
git blame -C file.py                         # detect lines moved/copied within file
git blame -CCC file.py                       # also detect moves across files (slow but powerful)
git blame --ignore-rev <SHA> file.py        # skip a specific commit (e.g., big reformat)
git blame --ignore-revs-file .git-blame-ignore-revs  # standard pattern for big reformats
```

The `.git-blame-ignore-revs` file is the senior-engineer move when you do a big `black`/`ruff format` PR. Commit the formatter PR, then add its SHA to `.git-blame-ignore-revs`:

```
# .git-blame-ignore-revs
# Big black reformat 2026-04-15
a1b2c3d4e5f6...
```

Then configure once:

```bash
git config blame.ignoreRevsFile .git-blame-ignore-revs
```

GitHub honors `.git-blame-ignore-revs` automatically in the Blame UI. The format reformat no longer hides the real author of every line.

---

## 7. Bisect — binary search for the bad commit

```bash
git bisect start
git bisect bad                   # current HEAD is broken
git bisect good v1.2.0           # this tag is known good
# Git checks out a commit halfway between
# Test it (run your repro)
git bisect good                  # or `git bisect bad` depending on result
# Repeat until Git names the first bad commit
git bisect reset                 # return to your original HEAD
```

Automatic mode — provide a script that exits 0 (good) or non-zero (bad):

```bash
git bisect start HEAD v1.2.0
git bisect run pytest tests/test_regression.py::test_x
```

Git will binary-search through commits, running your script each time. With 1024 suspect commits, you'll find the culprit in 10 steps.

**Bisect is gold for "this used to work last month."** Especially in ML where model behavior regressed silently — bisect the training-code commit history with an automated validation script.

---

## 8. Patch your way out of a bad commit on shared history

You pushed a commit that leaked a secret. You can't rebase main. Options:

1. **Rotate the secret immediately.** This is step 1 always. Treat any commit-leaked secret as compromised forever, regardless of cleanup.
2. **Revert the commit.** `git revert <SHA>` + push. The secret stays in history but is removed from the current code. For an internal repo with short-lived clones, this is usually sufficient.
3. **Rewrite history with `git filter-repo`.** The nuclear option. Coordinate with everyone on the repo. They'll need to re-clone or hard-reset. GitHub keeps cached views for some time even after history is rewritten.

```bash
pip install git-filter-repo
git filter-repo --path secrets.json --invert-paths   # remove file from all history
git push --force-with-lease --all
git push --force-with-lease --tags
```

`git filter-repo` superseded `git filter-branch` (which was slow and bug-prone). BFG Repo-Cleaner is an alternative for the same task.

Repeat: **rotate the secret first.** History rewrite is hygiene, not security.

---

## 9. The mid-rebase escape hatch

In the middle of a rebase or merge that's going sideways:

```bash
git rebase --abort               # return to pre-rebase state
git merge --abort                # cancel a merge mid-conflict
git cherry-pick --abort          # cancel a cherry-pick
git revert --abort               # cancel a revert
```

These return your working tree, index, and HEAD to the pre-operation state. Always safe to use.

---

## 10. The senior-engineer's recovery toolkit

The minimum kit you should have memorized:

```bash
git reflog                                       # find the lost SHA
git reset --hard <SHA>                           # go back to it (local-only)
git revert <SHA>                                 # safely undo a shared commit
git restore --staged <file>                      # unstage
git restore <file>                               # discard working-tree changes (DANGER)
git push --force-with-lease                      # safe force-push
git rebase --abort                               # cancel a rebase in progress
git bisect start; git bisect bad; git bisect good <SHA>  # find the bad commit
git blame -L <range> <file>                      # who last touched this line
```

Drill these until they're reflexive. The night you need them, you won't have time to look them up.

---

## 11. Cross-references

- The branching commands that get you into trouble in the first place → [module 04](04_branching_merging_rebasing.md).
- How to prevent destructive operations via branch protection → [module 11](11_branch_protection_rulesets_codeowners.md).
- Restoring a deleted PR branch (gh CLI) → [module 14](14_gh_cli_fundamentals.md).
- Secrets-in-history specifically (push protection, GHAS) → [module 32](32_ghas_secret_scanning.md).
