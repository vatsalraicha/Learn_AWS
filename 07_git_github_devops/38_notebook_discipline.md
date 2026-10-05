# 38 — ⭐ Notebook discipline (jupytext, nbdime, nbstripout, ReviewNB)

> *"Production code lives in modules. Notebooks live in the repo for exploration. Without discipline, notebooks become a `git blame` graveyard and a merge-conflict factory."*

## Why this module exists

Jupyter notebooks are JSON files containing code + outputs + metadata. They diff terribly, merge worse, and bloat repos with rendered output. Three+ tools fix this: **nbstripout** (strip outputs at commit), **nbdime** (semantic diffs), **jupytext** (pair with .py/.md). ReviewNB adds in-PR notebook rendering. This module is the canonical 2026 stack.

---

## 1. Why raw .ipynb files are awful in git

A notebook cell looks like:
```json
{
  "cell_type": "code",
  "execution_count": 42,
  "id": "a1b2c3d4",
  "metadata": {"scrolled": true, "tags": []},
  "outputs": [
    {"name": "stdout", "output_type": "stream", "text": "..."},
    {"data": {"image/png": "iVBORw0KGgo...base64-encoded-image..."}}
  ],
  "source": ["import pandas as pd\n", "df = pd.read_csv('data.csv')\n"]
}
```

Problems:
- Outputs change every run — every commit shows huge diffs unrelated to code.
- Embedded base64 images are 100KB+ each.
- Execution counts and IDs change per run.
- Merge conflicts in JSON are unparseable for humans.
- `git blame` on the raw JSON tells you nothing about which line of *code* changed.

---

## 2. nbstripout — strip outputs at commit time

Removes all outputs + execution counts + metadata noise from .ipynb files BEFORE they're committed. Cleanest cell stays in git; you still see outputs locally as you work.

```bash
pip install nbstripout

# Configure for current repo
nbstripout --install
# This sets a git attribute filter that runs nbstripout on .ipynb files

# OR — set it up via .pre-commit-config.yaml (preferred for teams)
- repo: https://github.com/kynan/nbstripout
  rev: 0.7.1
  hooks:
    - id: nbstripout
```

After setup, `git status` shows no diff for output-only changes. Commits contain only your code changes.

---

## 3. .gitattributes for notebook filtering

`nbstripout --install` writes this to `.git/info/attributes`:

```
*.ipynb filter=nbstripout
*.zpln filter=nbstripout
*.ipynb diff=ipynb
```

To version-control the filter setup (so every team member benefits without running `nbstripout --install`):

```gitattributes
# .gitattributes — committed to repo
*.ipynb filter=nbstripout
*.ipynb diff=ipynb
```

Each person still needs `pip install nbstripout` once. Pre-commit hook ensures consistency.

---

## 4. nbdime — semantic notebook diffs

`git diff` on notebooks shows raw JSON. Useless. `nbdime` shows cell-by-cell diff with renderable outputs.

```bash
pip install nbdime
nbdime config-git --enable    # makes git diff use nbdime for .ipynb files
```

Now:

```bash
git diff notebooks/explore.ipynb
# Opens a side-by-side cell diff in browser (nbdiff-web)

nbdiff notebooks/explore.ipynb notebooks/explore_v2.ipynb    # CLI version
```

For merges:
```bash
nbmerge LOCAL BASE REMOTE OUTPUT   # 3-way merge with cell-level conflict resolution
```

GitHub UI also shows rendered notebook diffs (since 2023) but nbdime is better for complex diffs.

---

## 5. jupytext — pair .ipynb with .py

The killer move: keep notebooks for interactive work, but ALSO have a parallel `.py` (or `.md`) representation. The `.py` is what gets committed and reviewed; the `.ipynb` is gitignored (or kept but auto-synced).

```bash
pip install jupytext

# Pair a notebook
jupytext --set-formats ipynb,py:percent notebooks/explore.ipynb
# Creates notebooks/explore.py paired with notebooks/explore.ipynb
```

The `.py` looks like:

```python
# %% [markdown]
# # Explore the data
#
# Load and inspect.

# %%
import pandas as pd
df = pd.read_csv("data.csv")
df.head()

# %% [markdown]
# ## Distribution

# %%
df.describe()
```

`# %%` separates cells. Both VS Code and Jupyter understand this format and can run cells from the `.py` directly.

Now:
- Edit either file → run `jupytext --sync explore.ipynb` (or auto-sync in JupyterLab via Jupytext plugin) → both stay in sync.
- Commit only the `.py` — git blame, diffs, merges all work great.
- `.ipynb` is gitignored.

For pre-commit auto-sync:

```yaml
- repo: https://github.com/mwouts/jupytext
  rev: v1.16.4
  hooks:
    - id: jupytext
      args: [--sync]
```

### Three text-pair format choices

| Format | Best for |
|---|---|
| `py:percent` | Most common; works in VS Code Interactive + PyCharm |
| `py:light` | Cleaner Python that runs as plain script |
| `md` | Best for prose-heavy notebooks |
| `ipynb` only | Default; what you start with |

---

## 6. ReviewNB — in-PR notebook rendering

[ReviewNB](https://www.reviewnb.com/) is a GitHub App that adds a "Notebook Diff" tab to every PR. Renders cell-level diff with images, plots, etc. Better than GitHub's native diff for visual-heavy notebooks.

For Capital One: viable if your security team approves the GitHub App. Otherwise, GitHub's native rendered diff (improved since 2023) suffices for most reviews.

---

## 7. The Capital One-grade ML notebook setup

`.pre-commit-config.yaml`:

```yaml
repos:
  # Strip outputs
  - repo: https://github.com/kynan/nbstripout
    rev: 0.7.1
    hooks:
      - id: nbstripout

  # Auto-sync jupytext pairs
  - repo: https://github.com/mwouts/jupytext
    rev: v1.16.4
    hooks:
      - id: jupytext
        args: [--sync]

  # Lint notebook code with ruff
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff
        types_or: [python, pyi, jupyter]
        args: [--fix]
      - id: ruff-format
        types_or: [python, pyi, jupyter]
```

`.gitattributes`:

```gitattributes
*.ipynb filter=nbstripout
*.ipynb diff=ipynb
*.ipynb linguist-detectable=true
```

`.gitignore` (if using jupytext-paired):

```
# Notebooks are paired; only commit the .py
notebooks/**/*.ipynb
!notebooks/.gitkeep
```

`Makefile`:

```makefile
notebooks-sync:
	jupytext --sync notebooks/**/*.py
notebooks-strip:
	nbstripout notebooks/**/*.ipynb
```

---

## 8. The notebook-to-module refactoring discipline

Notebooks are for exploration. **Production code goes in `src/`**. Refactor before merging.

Workflow:
1. Explore in `notebooks/00_explore_data.ipynb` (paired with `.py`).
2. When a function emerges that you'll reuse: extract to `src/my_pkg/data/loaders.py`.
3. Notebook now imports from `my_pkg.data.loaders` instead of defining inline.
4. Function gets tests in `tests/unit/`.
5. Notebook becomes a thin "demo" or "report" — calls into library code.

Without this discipline, every team rediscovers the same data-loading code in 12 notebooks, and no one tests any of it.

Capital One pattern: notebooks for exploration + ad-hoc analysis; production training/inference code is plain `.py` modules with full test coverage. Model code path: experiment in notebook → extract to module → write tests → CI → deploy.

---

## 9. CI for notebooks

```yaml
# In your CI workflow
- name: Test notebooks execute
  run: |
    pip install nbmake
    pytest --nbmake notebooks/

# Or use Papermill for parametrized runs
- name: Run baseline notebook
  run: |
    pip install papermill
    papermill notebooks/01_baseline.ipynb output.ipynb \
      -p data_path data/sample/ -p output_dir /tmp/
```

For notebooks that should always execute cleanly (e.g., README "quick start"): `pytest --nbmake` catches regressions.

---

## 10. Cross-references

- Pre-commit ecosystem in depth → [module 40](40_precommit_reproducibility_refactor.md).
- Repo structure for ML Python → [module 18](18_python_ml_repo_structure.md).
- Data versioning (the data side) → [module 39](39_lfs_dvc_lakefs_hf.md).
- CI for ML (testing the code → modules) → [module 41](41_mlops_ci_for_ml.md).
