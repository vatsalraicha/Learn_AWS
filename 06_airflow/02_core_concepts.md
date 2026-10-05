# 02 — Core concepts: DAG, Task, Operator, Sensor, Hook, Connection, Variable, XCom, Pool, Dataset/Asset

## Why this module exists

These ten primitives are the entire vocabulary of Airflow. Get the mental model right; the rest is just operator manuals.

---

## 1. DAG — Directed Acyclic Graph

A DAG is a Python object representing a workflow:

```python
from airflow import DAG
from airflow.decorators import task
from datetime import datetime, timedelta

with DAG(
    dag_id="nightly_etl",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    default_args={
        "owner": "data-eng",
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
    },
    tags=["etl", "snowflake"],
) as dag:
    ...
```

Key fields:

- `dag_id` — globally unique.
- `schedule` — cron, preset (`@daily`), `timedelta`, list of Datasets, or `None` (trigger-only).
- `start_date` — anchor for scheduling intervals. **Do not move once set.**
- `catchup` — if `True`, runs intervals between `start_date` and now on first deploy. Almost always `False` in prod.
- `tags` — UI filtering.
- `default_args` — defaults applied to all tasks.

DAG file is just a Python module that **declares** the workflow. The scheduler imports it on each refresh.

---

## 2. Task — a single unit of work

```python
@task
def extract():
    return fetch_from_api()

@task
def transform(data):
    return clean(data)

@task
def load(data):
    write_to_snowflake(data)

with DAG(...) as dag:
    data = extract()
    cleaned = transform(data)
    load(cleaned)
```

The TaskFlow API (2.0+ decorators) inferences dependencies from the Python flow. `extract` → `transform` → `load`.

Each `@task` becomes a `PythonOperator` instance under the hood.

---

## 3. Operator — the action library

Operators are pre-built task classes for specific actions:

- `BashOperator` — run a bash command.
- `PythonOperator` — run a Python callable.
- `SnowflakeOperator` — run SQL on Snowflake.
- `DatabricksRunNowOperator` — trigger a Databricks job.
- `SageMakerTrainingOperator` — kick off SageMaker training.
- `EmrCreateJobFlowOperator` — start an EMR cluster.
- `S3KeySensor` — wait for an S3 object.
- ... 1000+ more across provider packages.

Choosing the right operator > writing custom Python is the Airflow muscle memory.

```python
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator

load_to_dwh = SnowflakeOperator(
    task_id="load_to_dwh",
    snowflake_conn_id="snowflake_prod",
    sql="INSERT INTO sales SELECT * FROM staging.sales WHERE ds = '{{ ds }}'",
)
```

`{{ ds }}` is **Jinja templating** — the execution date as `YYYY-MM-DD`. Many more templating fields available (`{{ data_interval_start }}`, `{{ task_instance }}`).

---

## 4. Sensor — wait for a condition

A Sensor is an Operator that polls. Subtypes:

- `S3KeySensor` — wait for an S3 object to exist.
- `ExternalTaskSensor` — wait for another DAG's task to complete.
- `HttpSensor` — poll an HTTP endpoint.
- `SqlSensor` — poll a SQL query result.

```python
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor

wait_for_file = S3KeySensor(
    task_id="wait_for_file",
    bucket_name="myorg-data",
    bucket_key="exports/{{ ds }}/data.csv",
    mode="reschedule",                       # release slot between checks
    poke_interval=60,
    timeout=60 * 60 * 4,
)
```

`mode="reschedule"` is critical for scale — see module 07 (Sensors deep). Deferrable operators are the modern alternative.

---

## 5. Hook — the auth + client wrapper

A Hook wraps an external client (Snowflake, S3, Slack) with auth lookup. Operators use Hooks internally; you can also use them in `PythonOperator`:

```python
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook

@task
def custom_query():
    hook = SnowflakeHook(snowflake_conn_id="snowflake_prod")
    return hook.get_records("SELECT count(*) FROM sales")
```

Hooks fetch credentials from the **Connections** system (module 08).

---

## 6. Connection — credentials + endpoint config

A Connection is a named, encrypted record:

- Type (e.g., `snowflake`, `aws`, `postgres`).
- Host, port, schema, login, password.
- Extras (JSON).

Stored in metadata DB (encrypted via Fernet key) or in a **Secrets Backend** (module 08).

Reference by `conn_id` in operators / hooks.

---

## 7. Variable — string key/value config

```python
from airflow.models import Variable

threshold = Variable.get("etl_quality_threshold", default_var="0.95")
```

Variables are a key/value table in the metadata DB. Used for environment-specific config, feature flags, paths.

- Encrypted at rest (via Fernet).
- Replaceable by Secrets Backend (with `variables_lookup_pattern`).
- Anti-pattern: putting secrets in Variables (use Connections or Secrets Backend instead — Variables aren't audit-logged the same way).

---

## 8. XCom — task-to-task small data passing

```python
@task
def extract() -> dict:
    return {"row_count": 1234, "checksum": "abc"}

@task
def report(stats: dict):
    log.info(f"Loaded {stats['row_count']} rows")

stats = extract()
report(stats)
```

The return value is stored in XCom (metadata DB by default). `report` reads from XCom transparently.

**Size limits**:
- Default soft warning at 48 KB.
- Postgres BLOB max ~1 GB; MySQL up to 4 GB but very slow.
- **Production target: keep XCom < 1 MB.**

For larger data: **Custom XCom backend** that stores in S3/GCS/Blob and puts a reference in metadata DB (module 11).

---

## 9. Pool — concurrency limit

```python
# Set up a pool via CLI / UI / API
# airflow pools set snowflake 5 "Limit Snowflake concurrent queries"

@task(pool="snowflake", pool_slots=1)
def snowflake_query():
    ...
```

Pools throttle concurrent task execution across DAGs. Use for:
- DB connection limits (Snowflake warehouse query slots).
- Cloud rate limits (Databricks API).
- Cost control (limit parallel EMR clusters).

---

## 10. Dataset (2.4+) / Asset (3.0+)

A Dataset/Asset is a **URI-named data product** that DAGs can produce and consume:

```python
from airflow.datasets import Dataset

sales_dataset = Dataset("s3://myorg-warehouse/sales/")

# Producer DAG
with DAG("sales_etl", schedule="@daily") as etl:
    load_task = SnowflakeOperator(
        task_id="load",
        sql="...",
        outlets=[sales_dataset],          # marks this dataset as updated
    )

# Consumer DAG
with DAG("sales_aggregate", schedule=[sales_dataset]) as agg:
    aggregate = SnowflakeOperator(task_id="aggregate", sql="...")
```

The consumer DAG runs whenever the producer DAG updates the dataset. **Data-driven scheduling.**

In Airflow 3.0, Dataset is renamed to **Asset** with richer metadata.

---

## 11. Logical date vs data interval

The most-misunderstood concept in Airflow.

- A DAG run for `schedule="@daily"` with logical_date `2026-05-20` actually runs at **`2026-05-21 00:00`** (the END of the interval).
- The **data_interval_start** = `2026-05-20 00:00`; **data_interval_end** = `2026-05-21 00:00`.
- The run is processing data from May 20 (after it's all available); the logical date represents the data being processed.

This is why backfills work: rerunning logical_date `2026-05-20` processes May 20 data regardless of wall-clock time.

In SQL templates: `WHERE event_date = '{{ ds }}'` uses `data_interval_start` (May 20), not the wall-clock day the DAG ran (May 21).

---

## 12. Setup / Teardown (2.7+)

Tasks declared as setup/teardown have special semantics:

```python
@task
def create_cluster() -> str: ...

@task
def run_job(cluster_id: str): ...

@task
def delete_cluster(cluster_id: str): ...

with DAG(...) as dag:
    setup = create_cluster()
    work = run_job(setup)
    teardown = delete_cluster(setup)
    setup >> work >> teardown
    teardown.as_teardown(setups=setup)   # marks teardown
```

Teardown runs **even if work fails** (unlike a regular downstream that's skipped). Critical for "spin up EMR → train → spin down" patterns to avoid orphan clusters.

---

## 13. The minimal sane DAG

```python
from datetime import datetime, timedelta
from airflow.decorators import dag, task
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
from airflow.datasets import Dataset

dataset_sales = Dataset("s3://myorg/sales/")

@dag(
    dag_id="sales_etl",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5), "owner": "data-eng"},
    tags=["etl", "snowflake"],
)
def sales_etl():
    @task
    def extract():
        # ...
        return {"rows": 1234}

    @task(outlets=[dataset_sales])
    def load(stats: dict):
        hook = SnowflakeHook(snowflake_conn_id="snowflake_prod")
        hook.run("INSERT INTO sales SELECT * FROM staging.sales WHERE ds = '{{ ds }}'")
        return stats["rows"]

    stats = extract()
    load(stats)

sales_etl()
```

Decorators, type hints, dataset outlets, conn_id-based auth, templated SQL. This is the modern minimal sane DAG.

---

## Sanity check

1. What's the difference between `logical_date` and the wall-clock time the DAG runs?
2. What's the right size cap for XCom in production, and what's the production pattern for larger data?
3. Setup/Teardown — what's the practical use case?
4. `mode="reschedule"` on a Sensor — what does it change vs `mode="poke"`?
5. Variables vs Connections vs Secrets Backend — which is for what?
6. Dataset/Asset-driven scheduling — give one concrete use case.

---

## Sources

- [Airflow Concepts](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/index.html)
- [TaskFlow API](https://airflow.apache.org/docs/apache-airflow/stable/tutorial/taskflow.html)
- [Datasets](https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/datasets.html)
- [Pools](https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/pools.html)
- [Setup and Teardown](https://airflow.apache.org/docs/apache-airflow/stable/howto/setup-and-teardown.html)

→ Next: [03 — Architecture](03_architecture.md)
