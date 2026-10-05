# 41 — ⭐ CI for ML: lint, test, type-check, notebook test

> *"CI for ML is regular CI plus three things: notebook tests, data-shape tests, and model-smoke training."*

## Why this module exists

ML codebases stretch CI in ways app codebases don't. The pipelines are heavier, tests are more nuanced, and the consequence of skipping a step is a silent-broken model in prod that loses money for months. This module is the canonical CI workflow for an ML repo.

---

## 1. The four layers of ML CI

| Layer | What | Speed |
|---|---|---|
| **Static** | Lint, format, type-check, secret scan, dep review | Seconds |
| **Unit** | Pure function tests; data-loader tests with fixtures | Seconds |
| **Integration** | API roundtrips, DB queries, real boto3 against localstack | Minutes |
| **Model smoke** | Train 1 epoch on tiny data; verify model artifacts | Minutes |

Plus per-merge to main: **full nightly**: full training + validation suite.

---

## 2. The canonical workflow

```yaml
# .github/workflows/ci.yml
name: ML CI
on:
  push:
    branches: [main]
  pull_request:

concurrency:
  group: ci-${{ github.workflow }}-${{ github.head_ref || github.ref }}
  cancel-in-progress: true

permissions:
  contents: read
  pull-requests: write
  id-token: write

jobs:
  static:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v5
        with: { python-version: "3.11", cache: pip }
      - run: pip install pre-commit
      - run: pre-commit run --all-files

  unit:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    strategy:
      matrix:
        python: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v5
        with: { python-version: "${{ matrix.python }}", cache: pip }
      - run: pip install -e ".[dev]"
      - run: pytest tests/unit -v --cov=src/my_pkg --cov-report=xml --junitxml=junit.xml
      - uses: actions/upload-artifact@v4
        if: always()
        with: { name: junit-${{ matrix.python }}, path: junit.xml }

  notebooks:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v5
        with: { python-version: "3.11", cache: pip }
      - run: pip install -e ".[dev]"
      - run: pip install nbmake
      - run: pytest --nbmake notebooks/ -v

  integration:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    services:
      postgres:
        image: postgres:16
        env: { POSTGRES_PASSWORD: postgres }
        ports: ["5432:5432"]
        options: >-
          --health-cmd pg_isready --health-interval 10s
          --health-timeout 5s --health-retries 5
      redis:
        image: redis:7
        ports: ["6379:6379"]
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v5
        with: { python-version: "3.11", cache: pip }
      - run: pip install -e ".[dev]"
      - run: pytest tests/integration -v
        env:
          DATABASE_URL: "postgresql://postgres:postgres@localhost:5432/postgres"
          REDIS_URL: "redis://localhost:6379"

  smoke-train:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v5
        with: { python-version: "3.11", cache: pip }
      - run: pip install -e ".[dev,train]"
      - name: Smoke train on tiny sample
        run: |
          python -m my_pkg.training.train \
            --config configs/smoke.yaml \
            --epochs 1 \
            --data data/sample/ \
            --output /tmp/smoke-model.pt
      - name: Verify artifacts
        run: |
          python -c "
          import torch
          m = torch.load('/tmp/smoke-model.pt', weights_only=False)
          assert 'state_dict' in m
          print('OK')"
```

5 jobs in parallel; each independently times out; concurrency cancels duplicate PR runs.

---

## 3. Data shape tests

Catches data drift / schema regressions early.

```python
# tests/unit/test_data_schema.py
import pytest
import pandas as pd
from my_pkg.data.loaders import load_training_data
from pandera import DataFrameSchema, Column, Check

@pytest.fixture
def training_data():
    return load_training_data("data/sample/train.parquet")

def test_schema(training_data):
    schema = DataFrameSchema({
        "user_id": Column(int, Check.greater_than_or_equal_to(0)),
        "amount": Column(float, Check.in_range(0, 1e6)),
        "category": Column(str, Check.isin(["food", "travel", "shopping", "other"])),
        "is_fraud": Column(int, Check.isin([0, 1])),
    })
    schema.validate(training_data)

def test_target_balance(training_data):
    rate = training_data["is_fraud"].mean()
    assert 0.001 < rate < 0.1, f"Suspicious fraud rate: {rate}"

def test_no_nulls_in_critical(training_data):
    for col in ["user_id", "is_fraud"]:
        assert training_data[col].notna().all(), f"Nulls in {col}"
```

[Pandera](https://pandera.readthedocs.io/) or [Great Expectations](https://greatexpectations.io/) handle schema validation more thoroughly for prod use. Pandera is lighter; GE is full-featured.

---

## 4. Model unit tests

Test the model class without training:

```python
# tests/unit/test_model.py
import pytest
import torch
from my_pkg.models.transformer import TransformerEncoder

def test_forward_pass_shape():
    model = TransformerEncoder(d_model=128, n_heads=4, n_layers=2, vocab_size=1000)
    x = torch.randint(0, 1000, (8, 16))   # batch_size=8, seq_len=16
    out = model(x)
    assert out.shape == (8, 16, 128), f"Got {out.shape}"

def test_loss_decreases_on_overfit():
    """Sanity: model should overfit to a tiny batch."""
    torch.manual_seed(42)
    model = TransformerEncoder(d_model=64, n_heads=2, n_layers=1, vocab_size=100)
    opt = torch.optim.Adam(model.parameters(), lr=1e-2)
    x = torch.randint(0, 100, (4, 8))
    y = torch.randint(0, 100, (4, 8))

    losses = []
    for _ in range(20):
        opt.zero_grad()
        logits = model(x)
        loss = torch.nn.functional.cross_entropy(logits.reshape(-1, 100), y.reshape(-1))
        loss.backward()
        opt.step()
        losses.append(loss.item())

    assert losses[-1] < losses[0] * 0.5, f"Loss didn't decrease: {losses}"
```

The "overfit to a tiny batch" test catches dead architectures fast. If the model can't overfit 4 samples in 20 steps, something's wrong.

---

## 5. Code coverage

```yaml
- run: pytest --cov=src/my_pkg --cov-report=xml --cov-report=term

- uses: codecov/codecov-action@v4
  with:
    files: ./coverage.xml
    token: ${{ secrets.CODECOV_TOKEN }}
    fail_ci_if_error: true
```

Codecov posts a comment on the PR with coverage delta. Set a minimum coverage gate (e.g., 80% for new code) in branch protection.

For ML repos, **don't aim for 100%** — exploratory code (notebooks, scripts) doesn't need coverage. Cover library code (`src/<pkg>/`) and decision-grade utilities.

---

## 6. The `actionlint` + `zizmor` belt

Catch workflow bugs and security issues in the CI workflows themselves:

```yaml
- uses: rhysd/actionlint@v1
- run: pip install zizmor && zizmor .github/workflows/
```

Add to pre-commit and CI. Workflow YAML is code; treat it like code.

---

## 7. Status reporting

Use job summary for human-readable summary:

```yaml
- name: Summarize
  if: always()
  run: |
    echo "## Test summary" >> $GITHUB_STEP_SUMMARY
    echo "" >> $GITHUB_STEP_SUMMARY
    echo "| Suite | Status |" >> $GITHUB_STEP_SUMMARY
    echo "|-------|--------|" >> $GITHUB_STEP_SUMMARY
    echo "| Unit | ${{ steps.unit.outcome }} |" >> $GITHUB_STEP_SUMMARY
    echo "| Integration | ${{ steps.int.outcome }} |" >> $GITHUB_STEP_SUMMARY

- uses: EnricoMi/publish-unit-test-result-action@v2
  if: always()
  with:
    files: '**/junit*.xml'
```

The latter publishes a structured comment on the PR with pass/fail per test.

---

## 8. Test data hygiene

- Commit tiny test fixtures (<1 MB) directly. `data/sample/train_10rows.parquet`.
- Don't fetch from real S3 in CI — flaky + slow + needs credentials.
- For larger fixtures, store in repo via DVC + `dvc pull` in CI (with OIDC-scoped read-only role).
- Generate synthetic data deterministically in tests: `np.random.default_rng(42).integers(0, 100, size=1000)`.

---

## 9. Performance tests (sometimes)

For models with latency SLOs:

```yaml
- name: Inference latency benchmark
  run: |
    python scripts/bench_inference.py \
      --model /tmp/smoke-model.pt \
      --warmup 10 --iters 100 \
      --output bench.json
- name: Fail on regression
  run: |
    python -c "
    import json
    d = json.load(open('bench.json'))
    p99 = d['p99_ms']
    assert p99 < 100, f'p99 latency regressed: {p99}ms'
    "
```

Capture baseline; compare PR's branch vs main; alert on regression.

---

## 10. Cross-references

- Pre-commit ecosystem in depth → [module 40](40_precommit_reproducibility_refactor.md).
- Model validation gates (fairness, bias, drift) — the next layer → [module 42](42_mlops_validation_gates.md).
- Notebook tests (`nbmake`) → [module 38](38_notebook_discipline.md).
- Caching deps + matrix builds → [module 25](25_actions_cache_artifacts_matrix.md).
- The reusable workflow that packages all of this → [module 26](26_actions_reusable_workflows.md).
