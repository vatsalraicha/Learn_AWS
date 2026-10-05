# 14 — Python Basics for DevOps

> **Skim module** for Vatsal — he is Python-fluent. Included for curriculum completeness. The next module (15 — Boto3 automation) is the actual DevOps Python content.

## Why this module exists in Nana's curriculum

Nana's DevOps Bootcamp Module 13 teaches Python from zero. For DevOps specifically, the relevant Python skills are:
1. **Scripting** (replace bash when logic gets complex)
2. **Boto3** (AWS SDK — Module 15)
3. **Click / Typer** for CLIs
4. **Requests / httpx** for REST APIs
5. **PyYAML / ruamel.yaml** for manifest manipulation
6. **kubernetes Python client** for K8s automation
7. **Jinja2** for templating

## 1. Why Python wins DevOps scripting

- Cross-platform (one script runs on macOS dev box + Linux CI agent + Windows where forced)
- Huge ecosystem (boto3, kubernetes, requests, pyyaml, jinja2)
- Readable (the team-lead's case for picking it over bash)
- The same language as the data/ML side of the house

When to pick bash over Python: short, single-machine, shell-pipe-friendly. When to pick Python: anything involving APIs, JSON/YAML, > 30 lines of logic, retries/error handling.

## 2. Setting up modern Python (2026)

```bash
# Install Python via conda (the project's standard)
conda create -n devops-py python=3.13 -y
conda activate devops-py

# Or just use uv directly — it manages Python versions too
brew install uv
uv python install 3.13
uv venv .venv
source .venv/bin/activate

# Install packages
uv pip install boto3 click pyyaml requests jinja2

# Modern project mgmt
uv init my-project
cd my-project
uv add click boto3
uv run my-script.py
```

**uv** is Astral's Rust-written tool replacing pip + pip-tools + venv + pyenv in one binary. ~10-100x faster. The 2026 default.

## 3. The patterns you'll write

### A CLI with Click
```python
import click

@click.group()
def cli(): pass

@cli.command()
@click.argument("env")
@click.option("--dry-run", is_flag=True)
def deploy(env, dry_run):
    """Deploy app to ENV."""
    click.echo(f"Deploying to {env} (dry_run={dry_run})")
    # ...

if __name__ == "__main__":
    cli()
```

```bash
$ python deploy.py deploy prod --dry-run
Deploying to prod (dry_run=True)
```

### Reading + manipulating YAML
```python
import yaml
from pathlib import Path

manifest = yaml.safe_load(Path("deployment.yaml").read_text())
manifest["spec"]["replicas"] = 5
Path("deployment.yaml").write_text(yaml.safe_dump(manifest))
```

### Calling a REST API with retry
```python
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(5), wait=wait_exponential(min=1, max=30))
def get_status(url):
    r = httpx.get(url, timeout=10.0)
    r.raise_for_status()
    return r.json()
```

### Error handling with try/except
```python
try:
    result = risky_op()
except SpecificError as e:
    logger.error("op failed: %s", e)
    raise
except Exception:
    logger.exception("unexpected")
    raise
```

### Type hints (write them)
```python
from typing import Iterable

def deploy_to(envs: Iterable[str], version: str) -> dict[str, bool]:
    return {e: True for e in envs}
```

Use `mypy` or `pyright` in CI. Modern code without type hints is a code smell.

## 4. Python project structure

```
my-tool/
├── pyproject.toml
├── README.md
├── src/
│   └── my_tool/
│       ├── __init__.py
│       ├── cli.py
│       └── core.py
└── tests/
    └── test_core.py
```

`pyproject.toml`:
```toml
[project]
name = "my-tool"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
  "click>=8.1",
  "boto3>=1.35",
]

[project.scripts]
my-tool = "my_tool.cli:cli"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = ["pytest>=8", "ruff>=0.8", "mypy>=1.13"]

[tool.ruff]
line-length = 100
```

See [Topic 07 Module 18 — Python ML repo structure](../07_git_github_devops/18_python_ml_repo_structure.md) for the full layout.

## 5. Testing with pytest

```python
# tests/test_core.py
from my_tool.core import deploy_to

def test_deploy_to_returns_dict():
    result = deploy_to(["dev", "prod"], "1.2.3")
    assert result == {"dev": True, "prod": True}

def test_deploy_to_empty():
    assert deploy_to([], "1.2.3") == {}
```

```bash
pytest -v
pytest --cov=my_tool --cov-report=term-missing
```

## 6. Modules + Packages + PyPI

```python
# At top of file
from boto3 import client
import json
from collections import defaultdict

# Or relative
from .core import deploy_to
```

PyPI publishing (when you have a tool worth sharing):
```bash
uv build
uv publish --token <pypi-token>
```

For internal: publish to **Nexus** (Module 7), **AWS CodeArtifact**, **GitHub Packages**, or **GitLab Package Registry**. Configure `pip` / `uv` to use the private index URL.

## 7. OOP — when to use classes

For DevOps scripts: **rarely**. Prefer functions + dataclasses for state. Use classes when:
- Resource with lifecycle (connection, file handle) → `__init__` + `close()` + context manager
- Plugin/strategy pattern with multiple implementations
- Long-lived state across methods

```python
from dataclasses import dataclass

@dataclass
class Deployment:
    name: str
    version: str
    replicas: int = 1
```

## 8. The "Countdown App" / "Spreadsheet automation" / "GitLab API" projects (Nana's)

These are intro projects in her curriculum. Equivalents for senior engineers:
- **Countdown** → systemd timer + Python script
- **Spreadsheets** → openpyxl, pandas-to-Excel for reports
- **GitLab API** → `python-gitlab` library; great for "audit all repos for X"

Skip these unless you want the muscle memory.

## 9. Quick self-check

1. Why is `uv` displacing pip + Poetry + pyenv?
2. When should you write Python instead of bash?
3. What's the modern alternative to setup.py?
4. Why use type hints in DevOps Python?
5. Where do you publish a private Python package?

(Answers: single binary, ~10-100x faster, lockfile-first, manages Python versions; > 30 lines, API calls, JSON/YAML, retries, cross-platform; pyproject.toml; catches bugs at lint/CI time and serves as API documentation; Nexus, AWS CodeArtifact, GitHub Packages, GitLab Package Registry.)
