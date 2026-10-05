# 26 — CI/CD for DAGs: pytest + dag_maker, `airflow dags test`, image-based deploy, blue/green

## Why this module exists

DAGs are code. Treat them like code: lint, test, version, deploy via pipelines.

---

## 1. Test layers

| Layer | Tool | What it catches |
|---|---|---|
| **Syntax / import** | `python -c "import my_dag"` | Python syntax errors, missing imports |
| **DAG validation** | `airflow dags list-import-errors` | DAG-level issues |
| **Unit test (logic)** | `pytest` + `dag.test()` or `dag_maker` | Task callable correctness |
| **Integration test** | `astro dev start` + smoke run | End-to-end in local |
| **Lint** | `ruff`, `black`, `mypy` | Style + types |
| **Security** | `bandit`, `safety`, `pip-audit` | Vuln deps; insecure patterns |

---

## 2. `dag.test()` — the in-process simulator

```python
# tests/test_my_dag.py
import pendulum
from my_dag import my_dag

def test_my_dag_runs():
    dag = my_dag()
    result = dag.test(
        execution_date=pendulum.datetime(2026, 5, 20),
        run_conf={"param": "value"},
    )
    assert result.success
```

`dag.test()` runs the DAG in-process — no scheduler, no metadata DB. Fast.

---

## 3. `dag_maker` fixture (pytest-airflow)

```python
def test_extract_returns_dict(dag_maker):
    with dag_maker(dag_id="test") as dag:
        from my_dag import extract
        ti = extract()

    dr = dag.test()
    assert dr.success
```

For testing individual tasks with a controlled DAG context.

---

## 4. Mocking external systems

```python
def test_snowflake_load(mocker):
    mock_hook = mocker.patch("airflow.providers.snowflake.hooks.snowflake.SnowflakeHook")
    # ... run dag.test(), assert mock was called with expected SQL
```

Mock at the Hook level. Don't hit real Snowflake in unit tests.

---

## 5. CI pipeline

GitHub Actions example:

```yaml
name: airflow-dags-ci
on:
  pull_request:
    paths: [dags/**, plugins/**, requirements.txt]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt --constraint constraints-2.10.3-py3.11.txt
      - run: ruff check dags/
      - run: python -m pytest tests/ -v
      - name: Validate DAGs
        run: |
          export AIRFLOW__CORE__LOAD_EXAMPLES=False
          export AIRFLOW_HOME=$(mktemp -d)
          airflow db init
          airflow dags list-import-errors
```

For Astro: `astro dev parse` validates without running.

---

## 6. Image-based deploy (Astronomer-style)

```dockerfile
# Dockerfile
FROM quay.io/astronomer/astro-runtime:11.4.0
COPY dags/ /usr/local/airflow/dags/
COPY plugins/ /usr/local/airflow/plugins/
COPY requirements.txt /usr/local/airflow/
RUN pip install -r /usr/local/airflow/requirements.txt
```

CI builds the image, pushes to registry, signs with Cosign. Deploy = pin to image digest.

Pros vs MWAA's S3-bucket-upload:
- Immutable: digest pinned.
- Atomic: rollout is image swap.
- Verifiable: image signed + scanned.

---

## 7. Blue/green for DAGs (Airflow 3.0)

3.0 supports **DAG versioning**. Multiple versions of the same DAG coexist:

- Old version handles in-flight runs.
- New version handles future runs after deploy.
- Backfill against specific version.

Pre-3.0: blue/green is awkward (rename DAG → new dag_id; deprecate the old). Most shops just deploy in-place and accept brief mismatches.

---

## 8. Connection / Variable / Pool sync

Don't manage in the UI. Sync from IaC:

```hcl
# Terraform
resource "aws_secretsmanager_secret" "snowflake_conn" {
  name = "airflow/connections/snowflake_prod"
}
```

Pools and Variables: declare in code, apply via airflow CLI or REST API in CI:

```bash
airflow pools set snowflake 5 "Limit concurrency"
airflow variables set quality_threshold 0.95
```

CI applies these on deploy. No manual UI clicks.

---

## 9. The full release pipeline

```
PR opened
  → CI: lint + unit tests + DAG validation
  → Reviewer approves (security reviewer for high-privilege DAGs)
  → Merge to main
  → CI: build image, sign Cosign, push
  → CD: deploy to dev (Astro / MWAA / Helm)
  → Smoke test
  → Promote to staging (image digest, not new build)
  → Smoke test
  → Promote to prod
  → Tag git commit
```

Promote by digest, never rebuild. Same image, same behavior, same signature.

---

## 10. Common DAG lint rules (Ruff + custom)

- No top-level `import` of heavyweights (pandas, sklearn at module-level).
- No top-level `Variable.get` / API calls.
- All DAGs have `tags`, `owner`, `start_date`, `catchup=False`.
- All operators have `retries` set.
- No `latest` image tags in `KubernetesPodOperator`.

Tools: `airflow-dag-lint`, `ruff` with custom rules.

---

## Sanity check

1. `dag.test()` runs where, and what does it skip?
2. CI pipeline — what does `airflow dags list-import-errors` catch?
3. Image-based deploy vs S3-bucket-upload — three wins for image-based.
4. Airflow 3.0 DAG versioning enables what production pattern?
5. Connection sync from Terraform — why not manage in the UI?

---

## Sources

- [Testing DAGs](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html#testing-a-dag)
- [`dag.test()` method](https://airflow.apache.org/docs/apache-airflow/stable/howto/testing-dags.html)
- [Astro deploy](https://docs.astronomer.io/astro/deploy-code)

→ Next: [27 — SRE — failure modes & on-call playbook](27_sre_failure_modes.md)
