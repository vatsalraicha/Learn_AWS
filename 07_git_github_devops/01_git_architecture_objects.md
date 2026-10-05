# 01 — Git history, architecture & object model

> *"Git is a content-addressable filesystem with a VCS user interface bolted on top."* — Scott Chacon, Pro Git

## Why this module exists

Most senior engineers can use Git. Few can explain *what's actually happening* when they `git commit`. The internal model — **blobs, trees, commits, refs** — is the single source of truth for every higher-level command. Reset, rebase, cherry-pick, bisect, reflog: every one of them is moving these four object types around. If you know the model, the commands are obvious. If you don't, they look like magic and break unpredictably.

This module is the 30-minute mental model. The remaining six modules in Part A are how you wield it.

---

## 1. History — the milestones

| Year | Event |
|---|---|
| **2005 Apr 7** | Linus Torvalds writes Git in ~10 days after Larry McVoy revokes BitKeeper's free-for-Linux license |
| **2005 Jul** | Junio Hamano takes over as maintainer (still maintains Git in 2026) |
| **2008** | GitHub launches; Git becomes the dominant DVCS within ~3 years |
| **2014** | Microsoft, Google, Facebook all internalize Git for monorepos (Microsoft's GVFS becomes Scalar) |
| **2017 Feb** | **Shattered** — Google + CWI publish first practical SHA-1 collision |
| **2020 Oct** | Git 2.29 — opt-in SHA-256 repos |
| **2020 Jul** | Git 2.28 — `init.defaultBranch` config; the migration from `master` → `main` |
| **2024** | Reftable backend lands (Git 2.48, Jan 2025); production-ready by 2.51 |
| **2025–2026** | Git 2.50–2.54 series; Git **3.0 targeted late 2026** with SHA-256 as default (blocked on GitHub catching up) |

Junio Hamano still cuts the releases — one of the longest tenures of any open-source maintainer.

---

## 2. The four areas

```
┌──────────────────┐  git add   ┌──────────────────┐  git commit   ┌──────────────────┐
│  Working Tree    │ ─────────► │  Staging Area    │ ────────────► │  Local Repo      │
│  (.your files)   │            │  (.git/index)    │               │  (.git/objects)  │
└──────────────────┘            └──────────────────┘               └──────────────────┘
                                                                         │
                                                                         │ git push
                                                                         ▼
                                                                  ┌──────────────────┐
                                                                  │  Remote Repo     │
                                                                  │  (origin)        │
                                                                  └──────────────────┘
```

- **Working tree** — the files on disk you're editing.
- **Staging area / index** — `.git/index`, a binary file listing what will be in the next commit. `git add` updates it. `git diff` shows working-vs-index; `git diff --cached` shows index-vs-HEAD.
- **Local repo** — the `.git/` directory: objects (immutable), refs (mutable), config, hooks.
- **Remote repo** — another Git repo, usually accessed over `https` or `ssh`. `origin` is the conventional name for the default remote.

The staging area is what people confuse most. It exists so you can **craft a commit** that's not the same as your working tree (e.g., `git add -p` to stage only some hunks of a file). Use it deliberately — it's a feature, not friction.

---

## 3. The four object types

Every object in `.git/objects/` is one of:

| Object | Contains | Example |
|---|---|---|
| **blob** | File contents (no filename — that's in the tree) | The bytes of `README.md` |
| **tree** | Directory listing — entries of `(mode, name, sha)` | The root of your repo at one commit |
| **commit** | `tree` SHA + parent commit SHA(s) + author + committer + message | A snapshot |
| **tag** | (Annotated) — points to a commit + tagger + message | `v1.2.3` annotated tag |

Each object is identified by the **SHA-1 hash of its content** (40 hex chars; SHA-256 is 64 hex chars). Identical content → same SHA. Two repos with the same file content store it once globally. **Immutable.** Modifying anything = a new object with a new SHA.

```
.git/objects/
├── 1a/    ← first 2 chars of SHA = subdirectory
│   └── 23b4f...  (zlib-compressed object content)
├── 4f/
│   └── ...
└── pack/
    └── pack-abc123...idx   (packed objects after `git gc`)
```

A commit looks like this (run `git cat-file -p HEAD`):

```
tree 5e8b3...      ← root tree at this commit
parent 4f9a2...    ← previous commit (none for initial, two for merge commit)
author Vatsal Raicha <v@e.com> 1716315600 -0700
committer Vatsal Raicha <v@e.com> 1716315600 -0700

Module 1: write git architecture explainer
```

Notice — **the commit doesn't store a diff**. It stores a pointer to a complete tree. Diffs are computed on demand by comparing the parent's tree to this commit's tree. This is why Git is so fast at history navigation.

---

## 4. Refs — the only mutable thing

A **ref** is a pointer to a commit, stored as a text file under `.git/refs/` (or in the new reftable backend):

```
.git/
├── HEAD                 → ref: refs/heads/main
├── refs/
│   ├── heads/
│   │   ├── main         → 4f9a2...     (the local branch tips)
│   │   └── feature-x    → 1a23b4...
│   ├── remotes/
│   │   └── origin/
│   │       └── main     → 4f9a2...     (what we last saw on origin)
│   └── tags/
│       └── v1.2.3       → 5e8b3...
└── packed-refs          (compressed form for many refs)
```

- A **branch** is just a ref. `git branch feature-x` creates a file with one line — a commit SHA. That's all.
- **`HEAD`** is a symbolic ref pointing to whichever branch you have checked out (or detached, pointing directly at a commit).
- **Reftable** (Git 2.48+, production-ready 2.51) replaces the loose-ref / packed-refs files with a compressed binary format. Critical for monorepos with millions of refs (Microsoft, Google). Most people will never notice.

> 💡 **Why so many things break the way they break**: branches and tags are *just* pointers. `git reset --hard <sha>` moves the branch ref. `git rebase` rewrites commits (creating new ones with new SHAs) then moves the ref to the last new commit. `git cherry-pick` creates a new commit with the same diff as the source. **None of this destroys the old commits** — they're still in `.git/objects/`, just not reachable from any ref. The reflog remembers them for 90 days.

---

## 5. The DAG (directed acyclic graph)

Commits form a DAG via their `parent` pointers:

```
main:       A ── B ── C ── D
                  \         \
feature:           E ── F ── G   (merged into D via merge commit)
```

- Commit `D` has two parents (it's a merge commit).
- A **fast-forward merge** = no merge commit; just moves the branch ref forward. Possible only if the branch tip is a direct ancestor of the merging branch.
- A **rebase** = take a series of commits and reapply them on a different base, creating *new* commits with *new* SHAs (same diffs, same messages, new commit objects).

When you `git log --graph --oneline --all`, you're walking this DAG.

---

## 6. Where SHA-1 is going

SHA-1's collision weakness (Shattered 2017, Shambles 2020) is the reason Git 3.0 will default to SHA-256. The exposure for Git specifically is limited because:

- Git's storage uses `SHA-1DC` — collision-detecting SHA-1 — since 2017. Forced collisions cause `git fsck` to abort.
- An attacker would need write access to a repo AND the ability to insert a malicious object — and the collision would be visible in transparency log integrations.
- Still — the cryptographic horizon is real. The slow migration to SHA-256 is the right call.

**For your day job in 2026**: nothing changes. Repos remain SHA-1. Watch for GitHub's announcement of SHA-256 repo support — when that lands, Git 3.0 becomes practical.

---

## 7. The mental-model checks

Can you answer these without thinking?

1. **What does `git commit` create?** A new commit object whose `tree` SHA points to a snapshot of your staged changes, with `parent` = the previous `HEAD` commit. It then moves the current branch ref forward.
2. **What happens to "deleted" commits after `git reset --hard HEAD~3`?** They're still in `.git/objects/`. The branch ref moved back. The reflog still references them. `git gc --prune=now` after 90 days will actually delete them.
3. **Why does `git rebase` change SHAs?** A new commit's SHA is a function of its content + its parent. Rebase changes the parent → new SHA. Even with the same diff and message, the SHA is different.
4. **What's `HEAD`?** A pointer to the currently checked-out ref. Usually `ref: refs/heads/<branch>`. In detached HEAD mode, points directly at a commit SHA — any new commits in this state are unreachable once you check out another branch (this is the most common way junior engineers lose work).
5. **Why is `git status` slow on a huge repo?** It walks the working tree comparing mtimes/sizes against the index. Fixed by `core.untrackedCache` (since 2.18) and `core.fsmonitor` (since 2.36, uses platform file-watching APIs).

If any of those took >5 seconds to answer, re-read this module before continuing to module 4 (branching/rebasing).

---

## 8. Cross-references

- The repo layout in detail → Pro Git book ch. 10 ([git-scm.com](https://git-scm.com/book/en/v2/Git-Internals-Git-Objects)) is the canonical reference. Read it once.
- Reset/revert/restore semantics → [module 06](06_undo_recovery.md).
- Submodules + worktrees → [module 07](07_stash_tags_hooks_submodules_worktrees.md).
- Performance on huge monorepos → [module 17](17_monorepo_vs_polyrepo.md).
