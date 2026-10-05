# 03 — Core workflows + .gitignore + .gitattributes

> *"`git status`, `git diff`, `git log` — your three windows into what's happening. Run them constantly."*

## Why this module exists

This is the 80% of Git you do every day. Most of it is muscle memory. The parts worth re-teaching are: the **partial staging** patterns (`git add -p`, `git reset -p`), reading `git log`/`git diff` filters fluently, and using `.gitignore` + `.gitattributes` correctly — most repos misuse the latter.

---

## 1. Starting a repo

```bash
# From scratch
mkdir my-project && cd my-project
git init                                          # creates .git/
git init --initial-branch=main                    # explicit (or use init.defaultBranch=main)

# From a remote
git clone git@github.com:org/repo.git
git clone --depth 1 git@github.com:org/repo.git   # shallow — only latest commit, fast for CI
git clone --filter=blob:none git@github.com:org/repo.git   # partial clone — fetch blobs on demand
git clone --branch v1.2.0 --single-branch ...     # only one branch's history
```

**Shallow clones** (`--depth 1`) are right in CI. They're wrong locally — you can't see history, can't bisect, can't blame. **Partial clones** (`--filter=blob:none`) are the modern alternative — keeps all commits and trees but lazy-fetches blobs. Microsoft uses this pattern (their Scalar tool) for monorepos.

---

## 2. The status / add / commit loop

```bash
git status            # full status
git status -sb        # short format with branch info — better for daily use

git add file.py                  # stage entire file
git add -p file.py               # stage hunk-by-hunk (interactive) — use this constantly
git add -A                       # stage everything (incl. deletions) — careful!
git add .                        # stage everything in CWD (no deletions outside CWD)

git restore --staged file.py     # unstage (Git 2.23+; replaces `git reset HEAD file.py`)
git restore file.py              # discard working-tree changes (LOSES WORK)

git commit                       # opens $EDITOR for message
git commit -m "feat: add token caching"
git commit -am "fix: typo"       # add+commit tracked files only (NOT new files)
git commit --amend               # rewrite the LAST commit (don't do this on shared history)
git commit --amend --no-edit     # add staged changes to last commit, keep message
```

**`git add -p` (or `--patch`)** is the under-used senior move. It shows you each diff hunk and asks `y/n/s/e`:
- `y` — stage
- `n` — skip
- `s` — split this hunk into smaller pieces
- `e` — edit the hunk manually (rare but powerful)

Use it to craft **atomic commits**: one logical change per commit. Reviewers thank you.

---

## 3. Reading diffs

```bash
git diff                         # working tree vs index
git diff --cached  # (or --staged)# index vs HEAD (what `git commit` will record)
git diff HEAD                    # working tree + index vs HEAD
git diff <SHA1> <SHA2>           # any two refs
git diff main..feature           # what's in feature but not in main
git diff main...feature          # what's in feature since it diverged from main (triple-dot)
git diff --stat                  # summary: files changed + line counts
git diff --name-only             # just filenames
git diff -- '*.py'               # only Python files (note the --)
git diff -w                      # ignore whitespace
git diff --word-diff             # word-level instead of line-level (good for prose)
```

`..` vs `...` is the most-confused diff syntax. **`A..B`** = commits reachable from B but not A. **`A...B`** = commits reachable from either but not both (the symmetric difference). For PR diffs, `git diff main...HEAD` is what you want — it shows your branch's changes from where it diverged.

---

## 4. Reading log

```bash
git log                                          # default
git log --oneline                                # one line per commit
git log --oneline --graph --all --decorate       # the classic visualization — alias as `git lg`
git log -n 10                                    # last 10
git log --since="2 weeks ago"
git log --author="Vatsal"
git log --grep="JIRA-1234"                       # search commit messages
git log -S "function_name"                       # pickaxe: commits that add/remove this string
git log -G "regex"                               # pickaxe with regex
git log -p                                       # show patch for each commit
git log --stat                                   # summary stats
git log --follow path/to/file                    # follow renames
git log main..feature                            # commits in feature not in main
git log --merges                                 # only merge commits
git log --no-merges
git log path/to/dir/                             # commits touching this path

# JSON-like custom format (great for scripts)
git log --pretty=format:'%H|%an|%ae|%at|%s'
```

The **pickaxe** (`-S` / `-G`) is the senior superpower. "When did this function appear?" / "When was this string removed?" — `git log -S "MyClass" -- src/` answers in seconds.

---

## 5. `.gitignore`

A line per ignore pattern, root-relative (or per-directory if you put `.gitignore` in subdirs):

```gitignore
# Comments start with #

# Files
.env
.env.*
!.env.example                      # negation — don't ignore this even if matched above

# Directories
node_modules/                      # trailing / = directory only
__pycache__/
.venv/
dist/
build/

# Patterns
*.pyc
*.egg-info
**/*.tfstate                       # ** = anywhere in tree
data/raw/*                         # everything in data/raw/ ...
!data/raw/.gitkeep                 # ... except this placeholder

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db
```

**Things to know**:
- `.gitignore` only affects **untracked** files. If you accidentally committed `secrets.env`, adding it to `.gitignore` doesn't remove it from history — you need `git rm --cached secrets.env` AND `git filter-repo` (or BFG) for the historical removal.
- Use `git check-ignore -v <path>` to debug why (or why not) a file is being ignored.
- Global ignore (your personal junk, not the repo's): `git config --global core.excludesfile ~/.gitignore_global` — put `.DS_Store`, `*.swp`, `.idea/` there, not in every repo's `.gitignore`.
- For an ML repo specifically: ignore `data/`, `models/`, `checkpoints/`, `wandb/`, `mlruns/`, `outputs/`, large notebook output cells (use `nbstripout` — see [module 38](38_notebook_discipline.md)).

---

## 6. `.gitattributes` — the under-used file

Tells Git how to handle specific files: line endings, diff/merge drivers, LFS, export rules.

```gitattributes
# Default: treat as text, normalize line endings
*           text=auto

# Force LF for code (avoid Windows CRLF chaos)
*.py        text eol=lf
*.sh        text eol=lf
*.yml       text eol=lf

# Binaries — don't try to diff
*.png       binary
*.jpg       binary
*.pdf       binary
*.parquet   binary

# Notebook smart diff (uses nbdime)
*.ipynb     diff=jupyternotebook merge=jupyternotebook

# Filter — strip notebook outputs at commit (paired with .git/config: filter.nbstripout.clean = nbstripout)
*.ipynb     filter=nbstripout

# Linguist — tell GitHub how to count this file in language stats
docs/*      linguist-documentation
*.generated.py linguist-generated

# Git LFS — large files go to LFS instead of object store
*.bin       filter=lfs diff=lfs merge=lfs -text
*.pt        filter=lfs diff=lfs merge=lfs -text
*.h5        filter=lfs diff=lfs merge=lfs -text

# `git archive` exclusions (e.g., GitHub tarball downloads)
.gitattributes  export-ignore
.github/        export-ignore
tests/          export-ignore
```

**Line endings** are a real problem on cross-platform teams. `text=auto` + `eol=lf` + `.editorconfig` is the canonical solution. The pain is that Windows users sometimes have `core.autocrlf=true` globally, which translates LF→CRLF on checkout. `.gitattributes` overrides per-file behavior reliably.

---

## 7. The "I just want to see what changed" command catalog

| Question | Command |
|---|---|
| What did I change since the last commit? | `git diff HEAD` |
| What did I change since I branched off main? | `git diff main...HEAD` |
| What will be in my next commit? | `git diff --cached` |
| What files changed in the last commit? | `git show --stat HEAD` |
| Show me the full patch of the last commit | `git show HEAD` |
| Who last touched this line? | `git blame -L 42,42 file.py` |
| When did this string appear in the repo? | `git log -S "string" --all` |
| What's the divergence between my branch and main? | `git log --oneline --graph main...HEAD` |
| What files exist in the repo at a past commit? | `git ls-tree -r <SHA>` |
| What's the diff between two tags? | `git diff v1.0.0..v1.1.0` |
| How big is each file in HEAD? | `git ls-tree -lr HEAD \| sort -k4 -n -r \| head` |

Memorize these and you'll outperform engineers who reach for the GitHub UI for every question.

---

## 8. Cross-references

- Branching & merging (the next step up) → [module 04](04_branching_merging_rebasing.md).
- The patterns for staging large refactors → atomic commits + `git add -p` is the answer.
- Notebook-specific .gitattributes (nbstripout filter) → [module 38](38_notebook_discipline.md).
- LFS pointer files → [module 39](39_lfs_dvc_lakefs_hf.md).
