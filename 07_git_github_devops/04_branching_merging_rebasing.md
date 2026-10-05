# 04 — Branching, merging, rebasing, conflict resolution

> *"Merge preserves history. Rebase rewrites it. Knowing when to do which is what makes someone senior."*

## Why this module exists

This is the most-misunderstood Git topic. Engineers either (a) merge everything and end up with spaghetti history, or (b) rebase everything including shared branches and corrupt other people's work. The senior call is: **rebase your own private work; merge anything that's been shared**.

This module covers the operational tools (branch/checkout/switch/merge/rebase), the philosophical choice (merge vs rebase), and the survival skills (conflict resolution).

---

## 1. Branch commands

```bash
git branch                       # list local branches
git branch -a                    # incl. remote-tracking
git branch -vv                   # show upstream tracking info

git branch feature-x             # create branch at HEAD (doesn't switch)
git switch -c feature-x          # create + switch (since Git 2.23 — preferred over checkout -b)
git switch main                  # switch back

git branch -d feature-x          # delete (if merged; refuses if not)
git branch -D feature-x          # FORCE delete (data loss risk)
git push origin --delete feature-x   # delete on remote

# Rename current branch
git branch -m new-name
# Rename any branch
git branch -m old-name new-name
```

`git switch` and `git restore` (Git 2.23+) split the overloaded `git checkout` into two clearer verbs. **Use them.** `git checkout` works but is ambiguous (does it change branches? discard files? both?).

---

## 2. The two merge strategies (operational, not philosophical)

```bash
git switch main
git merge feature-x              # default behavior

# Fast-forward only — refuse to merge if a merge commit would be needed
git merge --ff-only feature-x

# Always create a merge commit, even if FF would work
git merge --no-ff feature-x

# Squash — combine all of feature-x's commits into a single commit on main, no merge link
git merge --squash feature-x
git commit -m "feat: add feature-x"
```

| Mode | Result |
|---|---|
| **Fast-forward** | `main` moves forward to feature's tip. No merge commit. Linear history. Only possible if `main` is an ancestor of `feature-x`. |
| **No-fast-forward (`--no-ff`)** | Always create a merge commit. History shows the branch existed. Useful for grouping commits as a "feature." |
| **Squash** | All of feature's commits become one new commit on `main`. No merge link. Loses individual commit context — only do this when the branch's individual commits are messy WIP. |

GitHub PRs offer three merge buttons: **Merge (--no-ff)**, **Squash and merge**, **Rebase and merge**. Capital One's published trunk-based pattern leans on **Squash and merge** for feature work and **Rebase and merge** for clean-commit branches. See [module 10](10_prs_code_review_merge.md).

---

## 3. Rebase — the foundational concept

```bash
# Standard rebase: take feature-x's commits, replay them on top of main
git switch feature-x
git rebase main

# Or in one command:
git rebase main feature-x
```

What happens internally:
1. Git finds the merge base (common ancestor) of `feature-x` and `main`.
2. Saves the commits unique to `feature-x` (call them C1, C2, C3).
3. Resets `feature-x` to point at `main`'s tip.
4. Replays C1, C2, C3 one at a time, creating *new* commits with *new* SHAs (because their parent changed).
5. If any replay conflicts, Git pauses and asks you to resolve before continuing.

```
Before:
main:       A ── B ── C ── D
                 \
feature-x:        E ── F ── G

After `git rebase main`:
main:       A ── B ── C ── D
                              \
feature-x:                     E' ── F' ── G'    (new commits, same diffs)
```

**Why rebase**: linear history is easier to read, bisect, and revert. The merge commit graphs at GitHub-scale projects make `git log` unreadable.

**Why NOT rebase shared branches**: your colleague's local `feature-x` still points to the old `E ── F ── G`. When they `git pull`, they'll get a confusing mess (or you'll force-push and overwrite their work). **Rule: never rebase a branch that other people have pulled.**

---

## 4. Interactive rebase — the surgery tool

```bash
git rebase -i HEAD~5             # interactive rebase the last 5 commits
```

Editor opens with:

```
pick a1b2c3d feat: add token endpoint
pick d4e5f6g feat: token tests
pick g7h8i9j WIP — broken
pick j1k2l3m fix: handle null user
pick m4n5o6p feat: add docs
```

Change `pick` to:
- `reword` (r) — keep commit, edit message
- `edit` (e) — pause to amend the commit
- `squash` (s) — combine with previous commit, prompt for combined message
- `fixup` (f) — combine with previous commit, discard this message
- `drop` (d) — delete this commit entirely
- `exec` (x) — run a shell command after this commit (great for "run tests after each rebased commit")

Reorder lines = reorder commits. Common pre-PR cleanup:

```
pick a1b2c3d feat: add token endpoint
fixup d4e5f6g feat: token tests          # squash tests into endpoint commit
drop  g7h8i9j WIP — broken
pick  j1k2l3m fix: handle null user
fixup m4n5o6p feat: add docs              # squash docs into the bugfix
```

Result: 2 clean commits instead of 5 messy ones. Review becomes pleasant.

**`git commit --fixup <SHA>` + `git rebase -i --autosquash main`** is the slick variant — mark a commit as a fixup of an earlier one and Git arranges the rebase automatically.

---

## 5. Conflict resolution

When rebase or merge can't auto-merge, Git pauses with files in **conflict state**:

```python
def authenticate(user):
<<<<<<< HEAD
    return jwt.encode({"sub": user.id}, SECRET, algorithm="HS256")
||||||| common ancestor
    return jwt.encode({"sub": user.id}, SECRET)
=======
    return jwt.encode({"sub": user.id, "iat": now()}, SECRET, algorithm="HS256")
>>>>>>> feature-x
```

(With `merge.conflictStyle = zdiff3`, you get the middle `|||||||` block showing the common ancestor — much easier to reason about.)

Resolution:

1. Edit the file to the desired final content (remove the markers).
2. `git add <file>` — marks conflict resolved.
3. If rebase: `git rebase --continue`. If merge: `git commit` (the message is pre-filled).

Tools that help:
- `git mergetool` — opens a 3-way merge tool (vimdiff, meld, kdiff3, Beyond Compare on Mac).
- VS Code, JetBrains IDEs, etc. all have built-in conflict resolution UI.
- For notebooks specifically: `nbdime` (`nbdime config-git --enable`) gives you cell-level merge.

Mid-rebase escape hatch:

```bash
git rebase --abort         # give up, return to pre-rebase state
git rebase --skip          # skip this commit (rare — usually wrong)
git merge --abort          # cancel a merge mid-conflict
```

---

## 6. The `rerere` superpower

If you resolve the same conflict repeatedly (common when long-lived branches rebase against a fast-moving main), enable `rerere` (reuse recorded resolution):

```bash
git config --global rerere.enabled true
```

Git remembers each conflict resolution and replays it automatically the next time the same conflict reappears. You still get a chance to verify, but no manual re-resolving. Saves hours over weeks.

---

## 7. Cherry-pick — surgical commit transplant

```bash
git cherry-pick <SHA>            # apply one commit from elsewhere onto current branch
git cherry-pick <SHA1>..<SHA3>   # range
git cherry-pick -x <SHA>         # add "(cherry picked from commit X)" to message
git cherry-pick --no-commit <SHA>   # apply changes, leave staged for combining
```

Use cherry-pick for:
- Backporting bug fixes from main to a release branch.
- Pulling one commit from someone's branch when you don't want their whole branch yet.
- Recovering work from a deleted branch (find SHA via reflog, cherry-pick it).

**Watch for**: cherry-pick creates a *new* commit (different SHA). Cherry-pick the same commit twice and you have two commits with the same diff → potential conflicts later if main merges the original.

---

## 8. The senior decision tree

**Should I merge or rebase my feature branch into main?**

```
Is the branch shared (has anyone else pulled it)?
├── YES → MERGE. You can't rewrite their local history.
└── NO ─→ Is the branch's commit history clean and meaningful?
         ├── YES → REBASE onto main + fast-forward merge. Linear history, no merge commit.
         └── NO ─→ INTERACTIVE REBASE to clean up, THEN rebase onto main + FF merge.
                   OR squash-merge via PR (lets GitHub handle it).
```

**Should I rebase my branch onto a fast-moving main?**

```
Has main moved since I branched?
├── No  → no action needed
└── Yes → How often does main move?
         ├── Several times/day (busy team) → rebase daily; `git rebase main` after morning sync
         └── Rarely               → rebase right before opening the PR
```

Capital One trunk-based reality: main moves several times an hour. Short-lived branches + daily rebase + small PRs is the only way to keep your branch viable.

---

## 9. The cardinal sins

❌ **Force-pushing to main** — possible only if branch protection is misconfigured. Rewrites history for every collaborator. At a bank, this is a code-red incident.

❌ **Rebasing a branch others have pulled and force-pushing** — same problem, smaller blast radius. If you must (say, to remove a leaked secret from history), coordinate with everyone on the branch, then they all need to `git fetch && git reset --hard origin/<branch>`.

❌ **Using `git pull` without understanding what it does** — by default, `git pull` = `git fetch + git merge`. This creates a merge commit you usually don't want. Set `pull.rebase = true` globally (see [module 02](02_config_identity_signing.md)) so it does `fetch + rebase` instead.

❌ **`git push --force`** — use `--force-with-lease` instead. `--force-with-lease` aborts if the remote moved since your last fetch (someone else pushed in between).

---

## 10. Cross-references

- Branching strategies (Git Flow / GH Flow / Trunk-based) → [module 15](15_branching_strategies.md).
- PR merge buttons on GitHub → [module 10](10_prs_code_review_merge.md).
- Conflict-prone notebook merges (use nbdime) → [module 38](38_notebook_discipline.md).
- The reflog as a safety net after a bad rebase → [module 06](06_undo_recovery.md).
