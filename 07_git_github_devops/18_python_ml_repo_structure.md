# 18 — Python ML repo structure (`pyproject.toml`, src layout, packaging)

> *"The 2026 standard is `pyproject.toml` + src layout + uv/hatch/poetry. Stop fighting it."*

## Why this module exists

Python's packaging story consolidated. `setup.py` is legacy; `setup.cfg` is legacy. **`pyproject.toml` is the standard** (PEP 517 / 518 / 621). For ML repos specifically, the structure decisions are: src vs flat layout, where notebooks go, where data goes, how to express dev vs prod dependencies. This module gives the 2026 canonical answer.

---

## 1. The canonical layout

```
my-ml-service/
├── .github/
│   └── workflows/
├── docs/
├── notebooks/
│   ├── 00_explore_data.ipynb       (numbered for ordering)
│   ├── 01_baseline_model.ipynb
│   └── README.md                    (explains the notebook progression)
├── src/
│   └── my_ml_service/               (the importable package; underscores not dashes)
│       ├── __init__.py
│       ├── data/
│       │   ├── __init__.py
│       │   ├── loaders.py
│       │   └── schemas.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── baseline.py
│       │   └── transformer.py
│       ├── training/
│       │   ├── __init__.py
│       │   └── train.py
│       ├── inference/
│       │   ├── __init__.py
│       │   └── predict.py
│       ├── api/
│       │   ├── __init__.py
│       │   └── app.py
│       ├── cli.py
│       └── _version.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── scripts/
│   ├── train_baseline.sh
│   └── deploy.sh
├── infra/                           (CDK / Terraform / Helm)
├── data/                            (gitignored — actual data, fixtures, samples)
│   ├── raw/
│   ├── interim/
│   └── processed/
├── .gitignore
├── .gitattributes
├── .editorconfig
├── .pre-commit-config.yaml
├── .python-version                  (for pyenv/uv)
├── pyproject.toml
├── uv.lock     OR   poetry.lock     OR   requirements.lock
├── Dockerfile
├── Makefile
├── README.md
├── LICENSE
└── CHANGELOG.md
```

---

## 2. `src/` layout vs flat layout

```
# Flat layout (older, simpler)               # src layout (2026 standard)
my-ml-service/                              my-ml-service/
├── my_ml_service/                          ├── src/
│   ├── __init__.py                          │   └── my_ml_service/
│   └── ...                                  │       ├── __init__.py
└── tests/                                   │       └── ...
                                             └── tests/
```

**Why src layout wins**:
- Prevents accidentally importing your package from the project root before it's installed (which masks packaging bugs).
- Forces you to install the package (`pip install -e .`) before testing — testing the installed version, not the source tree.
- Tests can never accidentally rely on relative imports.
- PyPA's official recommendation since ~2020.

The downside: imports are slightly less convenient in notebooks (you need `pip install -e .` first; we get into this in [module 40](40_precommit_reproducibility_refactor.md)).

---

## 3. `pyproject.toml` — the canonical file

```toml
[build-system]
requires = ["hatchling>=1.21"]
build-backend = "hatchling.build"

[project]
name = "my-ml-service"
version = "0.1.0"                            # or use dynamic versioning (see below)
description = "ML service for X"
readme = "README.md"
requires-python = ">=3.11"
license = { text = "Apache-2.0" }
authors = [
    { name = "Vatsal Raicha", email = "vatsal.raicha@gmail.com" },
]
dependencies = [
    "torch>=2.2,<3",
    "transformers>=4.40",
    "pandas>=2.2",
    "numpy>=1.26",
    "fastapi>=0.110",
    "uvicorn[standard]>=0.27",
    "boto3>=1.34",
    "mlflow>=2.12",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "ruff>=0.6",
    "mypy>=1.10",
    "pre-commit>=4.0",
    "ipykernel>=6.29",
    "jupyter>=1.0",
    "nbstripout>=0.7",
    "nbdime>=4.0",
    "jupytext>=1.16",
]
gpu = [
    "torch[cuda12]>=2.2,<3",
]
train = [
    "wandb>=0.17",
    "tensorboard>=2.16",
    "datasets>=2.20",
]

[project.scripts]
my-ml-service = "my_ml_service.cli:main"
my-ml-train = "my_ml_service.training.train:main"

[project.urls]
Repository = "https://github.com/capitalone/my-ml-service"
Documentation = "https://github.com/capitalone/my-ml-service#readme"

[tool.hatch.version]
path = "src/my_ml_service/_version.py"

# Tool configs (linters, formatters, type-checker) below — instead of separate dotfiles
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "SIM", "C4", "RUF"]
ignore = ["E501"]   # line length handled by formatter

[tool.ruff.format]
quote-style = "double"

[tool.mypy]
python_version = "3.11"
strict = true
ignore_missing_imports = true   # ML libs often have no stubs

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra --cov=src/my_ml_service --cov-report=term-missing"
filterwarnings = [
    "ignore::DeprecationWarning",
    "error::pytest.PytestUnraisableExceptionWarning",
]
```

That ONE file replaces `setup.py`, `setup.cfg`, `requirements.txt`, `requirements-dev.txt`, `pytest.ini`, `mypy.ini`, `.ruff.toml`. Less config sprawl.

---

## 4. Dependency manager — pick one

| Tool | What it is | When |
|---|---|---|
| **pip + requirements.txt** | Classic; no lockfile by default; use `pip-tools` for lock | Legacy; replace when you can |
| **Poetry** | `pyproject.toml`-native; integrates resolver + lock + env. Slow resolution; bad PyTorch integration | Still common; OK for mid-size projects |
| **Hatch** | PyPA-blessed; pyproject.toml-native; modern, simple | Lightweight choice |
| **PDM** | Like Poetry but PEP 621-compliant; supports PEP 582 (no venv) | Niche but solid |
| **uv** (Astral, of ruff fame) | Written in Rust; 10–100× faster than pip/poetry; pyproject.toml-native; pip-compatible | **The 2026 default — adopt this** |

uv compatibility example:

```bash
# Install uv
brew install uv
# or: curl -LsSf https://astral.sh/uv/install.sh | sh

# Initialize a project
uv init --package my-ml-service
cd my-ml-service

# Add deps (auto-updates pyproject.toml + uv.lock)
uv add torch transformers pandas
uv add --dev pytest ruff mypy pre-commit
uv add --optional gpu "torch[cuda12]"

# Install everything
uv sync
uv sync --extra dev --extra train

# Run a command in the project env
uv run pytest

# Lock + upgrade
uv lock --upgrade

# Build wheel + sdist
uv build
```

`uv.lock` is committed; reproducible across machines.

At Capital One scale, you'd probably standardize on one (Poetry or uv) via the InnerSource template repos.

---

## 5. Where data, models, artifacts go

**Inside the repo** (small fixtures only):
- `data/sample/*.csv` — tiny CSV/JSON samples for tests. <1 MB total. Committed.

**Outside the repo** (everything else):
- Real datasets — S3 / GCS / Azure Blob, versioned in DVC or LakeFS (see [module 39](39_lfs_dvc_lakefs_hf.md)).
- Trained models — S3 / SageMaker Model Registry / MLflow Model Registry (see [module 43](43_mlops_mlflow_sagemaker.md)).
- Experiment logs — MLflow tracking server, W&B, Neptune.

In `.gitignore`:

```gitignore
data/raw/
data/interim/
data/processed/
!data/sample/                     # except sample fixtures
models/                            # local trained models
checkpoints/
mlruns/                            # MLflow local tracking
wandb/                             # W&B local
outputs/                           # generic experiment outputs
*.pt
*.pth
*.h5
*.parquet
*.feather
```

In `.gitattributes`:

```gitattributes
data/sample/*.csv  text eol=lf
data/sample/*.bin  binary

# If using Git LFS for moderate-size artifacts (rare; prefer DVC/S3):
*.pkl              filter=lfs diff=lfs merge=lfs -text
```

---

## 6. Versioning options

Three sane patterns:

### Static version

```toml
[project]
version = "0.1.0"
```

Bump manually on releases. Boring but works.

### Single source of truth

```toml
[tool.hatch.version]
path = "src/my_ml_service/_version.py"
```

```python
# src/my_ml_service/_version.py
__version__ = "0.1.0"
```

`my_ml_service.__version__` always matches `pyproject.toml`. Useful in API responses (`GET /version`).

### Git-tag-derived

```toml
[tool.hatch.version]
source = "vcs"  # via hatch-vcs plugin
```

Version derived from latest git tag. `v1.2.3` tag → version `1.2.3`. Combined with `release-please` automation (see [module 19](19_templates_adr_docs_conventional_commits.md)), you never edit a version number by hand.

---

## 7. The `Makefile` or `Taskfile`

Even with pyproject.toml, a `Makefile` (or [Taskfile](https://taskfile.dev)) is the universal "what commands does this repo support":

```makefile
.PHONY: help install fmt lint test test-cov train serve clean
.DEFAULT_GOAL := help

help:                ## Show this help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install:             ## Install all deps including dev
	uv sync --extra dev --extra train

fmt:                 ## Format code
	uv run ruff format src tests
	uv run ruff check --fix src tests

lint:                ## Run linters
	uv run ruff check src tests
	uv run mypy src

test:                ## Run unit tests
	uv run pytest tests/unit -x -v

test-cov:            ## Run tests with coverage
	uv run pytest --cov=src/my_ml_service --cov-report=term-missing

train:               ## Train baseline model
	uv run my-ml-train --config configs/baseline.yaml

serve:               ## Start the API locally
	uv run uvicorn my_ml_service.api.app:app --reload --port 8000

clean:               ## Remove caches + build artifacts
	rm -rf .pytest_cache .mypy_cache .ruff_cache dist build *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
```

Anyone clones, runs `make install && make test`, and is working. No tribal knowledge.

---

## 8. The `src/<pkg>/__init__.py`

```python
"""my_ml_service — production ML service for X."""

from my_ml_service._version import __version__

__all__ = ["__version__"]
```

Re-export public API from `__init__.py` if you want users to do `from my_ml_service import TokenCache` instead of `from my_ml_service.token import TokenCache`. Use sparingly — too many re-exports = confusing star-imports.

---

## 9. Lambda / container / SageMaker packaging

For deployment targets:

- **Lambda**: package via `uv build` or `pip install --target=./build`; zip + upload (`sam build`, AWS Lambda Powertools).
- **Container (Docker)**: multi-stage Dockerfile, `uv pip install --system` in builder, copy site-packages to slim runtime image.
- **SageMaker training**: `sagemaker.estimator.PyTorch(...)` with `source_dir="src/my_ml_service"` and `entry_point="training/train.py"`. SageMaker auto-installs `requirements.txt` (or you bake them into a custom image).
- **SageMaker inference**: similar — `model_data` from S3, `source_dir`, `entry_point`. Or BYO container.

Example Dockerfile (uv-based, multi-stage):

```dockerfile
FROM python:3.11-slim AS builder
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen --no-dev

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY src/ /app/src/
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["uvicorn", "my_ml_service.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 10. Cross-references

- The repo skeleton with all standard files → [module 08](08_repo_setup_standards.md).
- Pre-commit config for ML → [module 40](40_precommit_reproducibility_refactor.md).
- Notebook handling → [module 38](38_notebook_discipline.md).
- Data + model versioning → [module 39](39_lfs_dvc_lakefs_hf.md).
- Conventional Commits + release-please for auto-versioning → [module 19](19_templates_adr_docs_conventional_commits.md).
- SageMaker deploy from CI → [module 47](47_aws_deploy_sagemaker_ecs_eks_lambda.md).
