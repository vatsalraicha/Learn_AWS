# 24 — Airflow + dbt: Astronomer Cosmos (the right way) vs BashOperator (the wrong way)

## Why this module exists

dbt + Airflow is the modern data-stack default. Done wrong (one BashOperator), you lose task-level retries and observability. Done right (Cosmos), you get model-level granularity.

---

## 1. The old way — BashOperator

```python
# WRONG
run_dbt = BashOperator(
    task_id="run_dbt",
    bash_command="cd /opt/dbt && dbt run --profiles-dir .",
)
```

Problems:
- One opaque task — no per-model visibility.
- Failure means "dbt failed somewhere"; you re-run the whole thing.
- No task-level retries on transient model failures.
- No lineage at model level.

---

## 2. Astronomer Cosmos — the modern way

[Cosmos](https://astronomer.github.io/astronomer-cosmos/) parses your `dbt` project and **renders each dbt model as an Airflow task**.

```python
from cosmos import DbtTaskGroup, ProjectConfig, ProfileConfig, ExecutionConfig

dbt_group = DbtTaskGroup(
    group_id="dbt_models",
    project_config=ProjectConfig("/opt/dbt/myproject"),
    profile_config=ProfileConfig(
        profile_name="myproject",
        target_name="prod",
        profiles_yml_filepath="/opt/dbt/profiles.yml",
    ),
    execution_config=ExecutionConfig(
        execution_mode="local",          # or "kubernetes", "docker", "virtualenv"
    ),
)
```

Now each dbt model appears as a task in Airflow:

```
dbt_models
├── stg_customers
├── stg_orders
├── int_orders_enriched
├── fct_revenue
└── dim_customers
```

You get per-model retries, OpenLineage emissions, task-level UI visibility.

---

## 3. Cosmos execution modes

- **`local`** — `dbt` runs in the Airflow worker (need dbt installed there).
- **`virtualenv`** — Cosmos creates a venv per dbt model run (heavy but isolated).
- **`docker`** — runs dbt in a Docker container (avoids dep conflicts).
- **`kubernetes`** — runs dbt in a K8s pod (KubernetesPodOperator-style).

For prod: **`kubernetes` execution mode** + dedicated dbt image with model dependencies. Isolated; can scale.

---

## 4. dbt Cloud Operator

If you use dbt Cloud (managed):

```python
from airflow.providers.dbt.cloud.operators.dbt import DbtCloudRunJobOperator

dbt_cloud = DbtCloudRunJobOperator(
    task_id="dbt_cloud_run",
    dbt_cloud_conn_id="dbt_cloud_default",
    job_id=12345,
    deferrable=True,
)
```

Simpler than Cosmos but you lose per-model task granularity in Airflow's UI.

---

## 5. Performance — the dbt manifest

Cosmos parses `manifest.json` (the dbt artifact) every parse cycle. For large dbt projects (1000+ models), this is slow.

Optimization: **`load_method=LoadMode.DBT_LS_FILE`** with a pre-computed `manifest.json` written to S3 by CI.

```python
from cosmos.constants import LoadMode
dbt_group = DbtTaskGroup(
    render_config=RenderConfig(
        load_method=LoadMode.DBT_MANIFEST,
        dbt_manifest_path="s3://myorg-dbt-artifacts/manifest.json",
    ),
    ...
)
```

CI runs `dbt parse` to produce the manifest; uploads to S3. Cosmos reads from S3 on parse. Cuts scheduler load.

---

## 6. Tests + sources + freshness

dbt has rich semantics: tests, sources, snapshots, exposures. Cosmos renders these too:

- `dbt test` → test task per model.
- `dbt source freshness` → freshness task.
- Snapshots → snapshot task.

Each becomes an Airflow task with per-failure retries.

---

## 7. The full dbt + Cosmos DAG

```python
from cosmos import DbtTaskGroup, ProjectConfig, ProfileConfig, ExecutionConfig
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor

@dag(schedule="@daily", catchup=False, start_date=datetime(2026, 1, 1))
def dbt_pipeline():
    wait_for_data = S3KeySensor(
        task_id="wait",
        bucket_key="raw/{{ ds }}/_SUCCESS",
        bucket_name="myorg-raw",
        deferrable=True,
    )

    transform = DbtTaskGroup(
        group_id="transform",
        project_config=ProjectConfig("/opt/dbt/project"),
        profile_config=ProfileConfig(
            profile_name="snowflake",
            target_name="prod",
        ),
        execution_config=ExecutionConfig(execution_mode="kubernetes"),
    )

    wait_for_data >> transform

dbt_pipeline()
```

Wait for source data → run all dbt models with per-model visibility.

---

## 8. Lineage

Cosmos emits OpenLineage events per model — input/output datasets identified. Combined with the dbt manifest's `depends_on` graph, you get fully connected lineage from raw → staging → marts.

This is the architect-grade modern data stack: Airflow + dbt + Cosmos + OpenLineage + DataHub.

---

## Sanity check

1. Why is `BashOperator` for dbt an anti-pattern?
2. Cosmos execution modes — `local` vs `kubernetes`. When to pick K8s?
3. dbt Cloud Operator vs Cosmos — what do you trade in choosing dbt Cloud?
4. The "1000 models = slow scheduler parse" problem — what's the fix?
5. Cosmos + OpenLineage gives you what specifically?

---

## Sources

- [Astronomer Cosmos](https://astronomer.github.io/astronomer-cosmos/)
- [dbt docs](https://docs.getdbt.com/)
- [dbt Cloud Provider](https://airflow.apache.org/docs/apache-airflow-providers-dbt-cloud/stable/)

→ Next: [25 — Alternative orchestrators](25_alternatives.md)
