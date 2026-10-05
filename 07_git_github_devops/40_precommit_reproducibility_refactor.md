# 40 — ⭐ Pre-commit ecosystem + reproducibility + notebook→module refactoring

> *"Pre-commit is the catch-it-locally layer that saves you from 20-minute CI cycles. Reproducibility is what separates research code from production code. Refactoring notebooks into modules is what separates a senior from a researcher."*

## Why this module exists

Three habits that compound: pre-commit hooks catch most issues locally (no CI roundtrip), reproducibility patterns let your work be re-run by anyone at any time, and notebook→module refactoring keeps your codebase shippable. All three are Sr-Lead-level expectations.

---

## 1. The pre-commit framework

[pre-commit](https://pre-commit.com/) is a Python tool that manages git hooks for you. One YAML file, many languages, easy team adoption.

```bash
brew install pre-commit          # or pip install pre-commit
cd my-repo
pre-commit install               # installs into .git/hooks/pre-commit
pre-commit install --hook-type commit-msg       # also commit-msg hook
pre-commit install --hook-type pre-push         # also pre-push hook
pre-commit run --all-files       # run on every file (great for first-time setup)
pre-commit autoupdate            # bump all hook revs
```

---

## 2. The canonical ML `.pre-commit-config.yaml`

```yaml
default_language_version:
  python: python3.11

default_stages: [pre-commit]

repos:
  # General hygiene
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
        args: [--unsafe]            # allow custom YAML tags
      - id: check-toml
      - id: check-json
      - id: check-added-large-files
        args: ['--maxkb=500']
      - id: check-merge-conflict
      - id: check-case-conflict
      - id: detect-private-key
      - id: debug-statements        # finds pdb.set_trace, breakpoint()
      - id: mixed-line-ending
        args: ['--fix=lf']

  # Python: ruff (linter + formatter, replaces flake8+black+isort+pyupgrade)
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff
        args: [--fix]
        types_or: [python, pyi, jupyter]
      - id: ruff-format
        types_or: [python, pyi, jupyter]

  # Type checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.2
    hooks:
      - id: mypy
        additional_dependencies: [types-requests, pydantic, sqlalchemy[mypy]]
        args: [--strict, --ignore-missing-imports]
        exclude: ^(tests/|notebooks/|scripts/)

  # Python security
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.10
    hooks:
      - id: bandit
        args: [-c, pyproject.toml]
        additional_dependencies: ["bandit[toml]"]
        exclude: ^tests/

  # Secret detection — local first line of defense
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.4
    hooks:
      - id: gitleaks

  # Notebook output stripping
  - repo: https://github.com/kynan/nbstripout
    rev: 0.7.1
    hooks:
      - id: nbstripout

  # Jupytext auto-sync (if using paired notebooks)
  - repo: https://github.com/mwouts/jupytext
    rev: v1.16.4
    hooks:
      - id: jupytext
        args: [--sync]

  # YAML formatting
  - repo: https://github.com/adrienverge/yamllint
    rev: v1.35.1
    hooks:
      - id: yamllint
        args: [-d, '{extends: default, rules: {line-length: {max: 120}}}']

  # Workflows linting
  - repo: https://github.com/rhysd/actionlint
    rev: v1.7.3
    hooks:
      - id: actionlint

  # Dockerfile linting
  - repo: https://github.com/hadolint/hadolint
    rev: v2.13.0-beta
    hooks:
      - id: hadolint-docker

  # Conventional commits (commit-msg hook)
  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v3.4.0
    hooks:
      - id: conventional-pre-commit
        stages: [commit-msg]
        args: [feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert]
```

This catches at commit time: formatting, lint, type errors, security smells (bandit), leaked secrets (gitleaks), workflow YAML errors (actionlint), Dockerfile issues (hadolint), notebook outputs, non-Conventional commits.

CI then re-runs everything as a safety net (in case someone bypassed local hooks with `--no-verify`).

---

## 3. Run pre-commit in CI

```yaml
# .github/workflows/ci.yml
jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - uses: pre-commit/action@v3.0.1
        with:
          extra_args: --all-files
```

The `pre-commit/action@v3.0.1` action handles caching and runs the same config. CI failure tells the dev to run locally first.

Make it a required status check on branch protection so unsanitized PRs can't merge.

---

## 4. Reproducibility — the foundations

Reproducible = "anyone, any time, can rebuild the same artifact from the same inputs."

### Pin everything

- **Python version**: `.python-version`, `pyproject.toml` `requires-python`, Docker base image tag.
- **Dependencies**: lock file (`uv.lock`, `poetry.lock`, `requirements.lock`). Committed.
- **System packages**: Docker base image with explicit version + apt packages pinned in Dockerfile.
- **External services**: pin model IDs (e.g., `gpt-4-turbo-2024-04-09`, not `gpt-4`), API versions.
- **Random seeds**: set explicit seeds in training code (`torch.manual_seed`, `np.random.seed`, `random.seed`).
- **Data version**: pin via DVC pointer file or explicit S3 URI with version.

### Avoid implicit state

- Don't depend on `~/.cache/...` or `$ENV_VARS` set externally — declare them.
- Don't rely on filesystem ordering — sort explicitly.
- Don't use system time for randomness — use seeded RNG.
- Don't rely on global state in tests — fixtures per test.

### Deterministic builds

```dockerfile
FROM python:3.11-slim AS base
ENV PYTHONHASHSEED=0
ENV PIP_NO_CACHE_DIR=1
ENV SOURCE_DATE_EPOCH=315532800   # 1980-01-01 (for build timestamps)

# Pin everything
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1=12.2.0-14 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen --no-dev
```

`SOURCE_DATE_EPOCH` is the reproducible-builds standard env var — many tools honor it for deterministic timestamps in artifacts.

### Reproducible ML training

Beyond seeds:
- Pin GPU type (different architectures produce different floating-point outputs).
- Disable nondeterministic ops where possible:
  ```python
  torch.backends.cudnn.deterministic = True
  torch.backends.cudnn.benchmark = False
  torch.use_deterministic_algorithms(True)
  ```
- Log every hyperparameter, every data version, every commit SHA to MLflow.

100% reproducibility on GPU is hard (some CUDA ops are inherently nondeterministic). Aim for ≤1e-4 difference in eval metrics; document residual nondeterminism.

---

## 5. The notebook → module refactoring discipline

### Symptoms of "notebook code that should be a module"

- Same function copy-pasted across 3+ notebooks
- A cell longer than 30 lines that's not exploratory
- Logic you'd want to unit test
- Code another team member needs to call

### Refactoring steps

1. **Identify**: cell or block of cells that's reusable logic (not exploration).
2. **Extract**: move into `src/my_pkg/<domain>/<name>.py`. Add type hints.
3. **Replace** the notebook cell with `from my_pkg.<domain> import <fn>`.
4. **Test**: write `tests/unit/test_<name>.py` covering happy path + edge cases.
5. **Document**: docstring on the function (Google or NumPy style).
6. **Re-run notebook**: verify behavior unchanged.

Now the function:
- Is tested
- Is importable by training scripts, inference services, other notebooks
- Has a clear name and docstring
- Can be reviewed independently
- Has version history

### The pre-commit-grade check

A custom check: "no production paths import from `notebooks/`."

```yaml
- repo: local
  hooks:
    - id: no-notebook-imports-in-src
      name: "src/ shouldn't import from notebooks/"
      entry: bash -c 'grep -r "from notebooks" src/ tests/ && exit 1 || exit 0'
      language: system
      pass_filenames: false
```

A simple but effective discipline.

---

## 6. Reproducibility in CI for ML

```yaml
- name: Train baseline (smoke test)
  run: |
    python -m my_pkg.training.train \
      --config configs/baseline.yaml \
      --epochs 1 \
      --output /tmp/model.pt \
      --seed 42
    # Hash the output; should be identical across runs (with same seed + same data)
    sha256sum /tmp/model.pt | tee model.sha256
```

If you can hash-match a 1-epoch model across CI runs (same seed, same data, same image), you've achieved deterministic builds — a strong reproducibility guarantee.

Full-training reproducibility is usually not run in CI (too slow). Instead, validate per release with a benchmark training job that produces a known-good metric within tolerance.

---

## 7. Capital One-grade summary

The repo standard:
- ✅ `.pre-commit-config.yaml` with the full ML stack (ruff, mypy, bandit, gitleaks, nbstripout, actionlint, hadolint, conventional-pre-commit)
- ✅ `pyproject.toml` with all tool configs
- ✅ `uv.lock` (or equivalent) committed
- ✅ `.python-version` pinned
- ✅ Dockerfile pinned (base image with version + apt packages pinned)
- ✅ Random seeds set in training code
- ✅ Determinism flags set (torch.use_deterministic_algorithms)
- ✅ MLflow / SageMaker Tracking records every commit SHA + data version + params
- ✅ CI runs `pre-commit run --all-files` as a required check
- ✅ CODEOWNERS prevents touching `src/` without proper review
- ✅ Notebook → module refactoring enforced in code review

---

## 8. Cross-references

- The repo skeleton holding all this → [module 18](18_python_ml_repo_structure.md).
- Notebook discipline (the notebook side) → [module 38](38_notebook_discipline.md).
- CI for ML in detail → [module 41](41_mlops_ci_for_ml.md).
- Conventional Commits + release-please for changelog automation → [module 19](19_templates_adr_docs_conventional_commits.md).
- The Capital One InnerSource template that bakes all of this in → [module 56](56_capital_one_devops_deep.md).
