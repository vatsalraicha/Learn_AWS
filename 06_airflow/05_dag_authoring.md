# 05 — DAG authoring: TaskFlow, dynamic task mapping, deferrable, setup/teardown

## Why this module exists

Authoring DAGs correctly matters more than any other Airflow skill. Bad DAG patterns are the #1 source of scheduler problems and pipeline incidents.

---

## 1. TaskFlow API (the 2.0+ default)

```python
from airflow.decorators import dag, task
from datetime import datetime

@dag(start_date=datetime(2026, 1, 1), schedule="@daily", catchup=False)
def my_pipeline():
    @task
    def extract() -> dict:
        return {"rows": 100}

    @task
    def transform(stats: dict) -> dict:
        return {"clean_rows": stats["rows"] - 5}

    @task
    def load(stats: dict):
        print(f"Loaded {stats['clean_rows']}")

    load(transform(extract()))

my_pipeline()
```

Wins over classic operators:

- Pythonic — looks like normal code.
- Dependencies inferred from call graph.
- Type hints work.
- XCom transparent — return value automatic.

When NOT to use TaskFlow: when you need a specific operator (`SnowflakeOperator`, `KubernetesPodOperator`, etc.). Mix freely:

```python
@dag(...)
def pipeline():
    @task
    def extract(): ...

    load_to_snowflake = SnowflakeOperator(
        task_id="load_to_snowflake",
        snowflake_conn_id="snowflake_prod",
        sql="...",
    )

    extract() >> load_to_snowflake
```

---

## 2. Dynamic Task Mapping (2.3+)

Run N copies of a task based on runtime data:

```python
@task
def get_files() -> list[str]:
    return s3_hook.list_keys("myorg-incoming")

@task
def process(file_key: str):
    process_file(file_key)

process.expand(file_key=get_files())
```

`get_files` returns a list at runtime; `process` is mapped over each element. If `get_files` returns 50 keys, Airflow creates 50 task instances.

For batch jobs over variable inputs (per-customer, per-region, per-shard): dynamic mapping is the right primitive.

### 2.1 expand_kwargs (2.4+)

```python
@task
def process(file_key: str, partition: str): ...

process.expand_kwargs([
    {"file_key": "a.csv", "partition": "2026-05-01"},
    {"file_key": "b.csv", "partition": "2026-05-02"},
])
```

For multiple args per mapped task.

---

## 3. Deferrable operators (2.2+)

The "wait without burning a worker" pattern:

```python
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor

wait_for_data = S3KeySensor(
    task_id="wait_for_data",
    bucket_key="exports/{{ ds }}/data.parquet",
    bucket_name="myorg-data",
    deferrable=True,                # offload to Triggerer
    poke_interval=300,
    timeout=86400,
)
```

`deferrable=True` makes the operator hand off to the **Triggerer process** while waiting. Frees the worker slot. One Triggerer pod handles thousands of concurrent waits.

Most modern operators have `deferrable=True` parameter. **Use it.** Old `mode="reschedule"` is a worse alternative.

For ETL with many "wait for file" sensors: deferrable is the difference between 100-worker Celery cluster and 5-worker.

---

## 4. Setup / Teardown (2.7+)

For "spin up → use → spin down" patterns where teardown MUST run even on failure:

```python
@task(retries=3)
def create_emr_cluster() -> str: ...

@task
def run_spark_job(cluster_id: str): ...

@task(trigger_rule="all_done")
def terminate_emr(cluster_id: str): ...

with DAG(...) as dag:
    cluster = create_emr_cluster()
    job = run_spark_job(cluster)
    teardown = terminate_emr(cluster)

    cluster >> job >> teardown
    teardown.as_teardown(setups=cluster)
```

`teardown.as_teardown(setups=cluster)` marks `terminate_emr` as a teardown for `create_emr_cluster`. Teardown runs even when `run_spark_job` fails — no orphan EMR cluster racking up cost.

This **replaces the old `trigger_rule="all_done"` pattern** with semantic clarity.

---

## 5. Branching

```python
from airflow.operators.python import BranchPythonOperator

def decide(**context) -> str:
    if Variable.get("env") == "prod":
        return "deploy_to_prod"
    else:
        return "deploy_to_dev"

branch = BranchPythonOperator(task_id="decide", python_callable=decide)
branch >> [deploy_to_prod, deploy_to_dev]
```

Or with TaskFlow:

```python
@task.branch
def decide() -> str: ...
```

The branch task returns a downstream task_id (or list). Other downstreams are skipped.

---

## 6. ShortCircuit + EmptyOperator + TriggerDagRun

- `ShortCircuitOperator` — if callable returns False, skip all downstream.
- `EmptyOperator` (was `DummyOperator`) — no-op node; convenient for grouping.
- `TriggerDagRunOperator` — trigger another DAG.
- `ExternalTaskSensor` — wait for another DAG's task.

The "trigger and forget" pattern:

```python
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

trigger_downstream = TriggerDagRunOperator(
    task_id="trigger_downstream",
    trigger_dag_id="downstream_dag",
    wait_for_completion=False,
)
```

For asset-driven scheduling: prefer Datasets over TriggerDagRun — more declarative.

---

## 7. Task Groups (2.0+)

Visual grouping in the UI:

```python
from airflow.utils.task_group import TaskGroup

with DAG(...) as dag:
    extract_task = extract()
    with TaskGroup("transform") as tg:
        clean = clean_data(extract_task)
        validate = validate_data(clean)
    load = load_to_dwh(tg)
```

In the UI, the `transform` group is a collapsible node. Better than the old SubDAG (which is removed in 3.0).

---

## 8. Templating with Jinja

Operators with `template_fields` accept Jinja:

```python
op = BashOperator(
    task_id="copy",
    bash_command="aws s3 cp s3://src/{{ ds }} s3://dest/{{ ds }}",
)
```

Available templates:
- `{{ ds }}` — logical date YYYY-MM-DD.
- `{{ ds_nodash }}` — YYYYMMDD.
- `{{ data_interval_start }}`, `{{ data_interval_end }}`.
- `{{ task_instance }}`, `{{ run_id }}`, `{{ dag.dag_id }}`.
- `{{ params.X }}` — user-supplied params at DAG run.
- `{{ var.value.X }}` — Variable.
- `{{ conn.X }}` — Connection extras.

Custom templates via macros.

---

## 9. Common anti-patterns

| Anti-pattern | Why bad | Fix |
|---|---|---|
| Top-level `pd.read_csv(...)` | Runs every parse cycle | Move into task |
| `Variable.get(...)` at top level | API call every parse cycle | Pass via task args; use templating |
| `time.sleep(60)` inside task | Burns worker slot | Use deferrable sensor or `mode="reschedule"` |
| XCom passing a DataFrame | DB blow-up | Custom XCom backend (S3) or stage to data lake |
| `pickle` for XCom of arbitrary objects | Security + version-skew risk | Use JSON-serializable returns |
| Trigger DAG on every event | Scheduler thrash | Use Dataset / event-driven trigger |
| `catchup=True` on a fresh DAG with old start_date | 365 simultaneous backfill DAG runs | `catchup=False` by default |
| Top-level `if Variable.get(...) == "X":` deciding DAG shape | Non-deterministic DAG | Use params at runtime |
| Returning huge data from task | XCom blow-up | Write to S3, return path |

---

## 10. The production DAG template

```python
from datetime import datetime, timedelta
from airflow.decorators import dag, task
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
from airflow.datasets import Dataset
from airflow.utils.task_group import TaskGroup

dataset_curated = Dataset("snowflake://prod.curated.sales")

@dag(
    dag_id="sales_etl_v2",
    description="Daily sales ETL into Snowflake curated layer",
    start_date=datetime(2026, 1, 1),
    schedule="0 3 * * *",
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "data-eng",
        "retries": 3,
        "retry_delay": timedelta(minutes=5),
        "retry_exponential_backoff": True,
        "max_retry_delay": timedelta(hours=1),
        "execution_timeout": timedelta(hours=2),
    },
    tags=["etl", "snowflake", "sales", "v2"],
)
def sales_etl_v2():
    @task
    def discover_partitions() -> list[str]:
        return [f"sales_{i:03d}" for i in range(10)]

    @task(pool="snowflake", pool_slots=1)
    def load_partition(partition: str) -> dict:
        hook = SnowflakeHook(snowflake_conn_id="snowflake_prod")
        rows = hook.run(f"INSERT INTO staging.{partition} ... WHERE ds='{{{{ ds }}}}'")
        return {"partition": partition, "rows": rows}

    @task(outlets=[dataset_curated])
    def promote_to_curated(stats: list[dict]):
        hook = SnowflakeHook(snowflake_conn_id="snowflake_prod")
        hook.run("MERGE INTO curated.sales AS t USING staging.sales AS s ...")

    partitions = discover_partitions()
    stats = load_partition.expand(partition=partitions)
    promote_to_curated(stats)

sales_etl_v2()
```

Notes:
- Dynamic mapping for partition parallelism.
- Pool to limit Snowflake concurrency.
- Dataset outlet for downstream DAGs.
- Reasonable retries + exponential backoff.
- `max_active_runs=1` prevents overlap.
- `execution_timeout` per-task.

---

## Sanity check

1. TaskFlow API — what's the main ergonomic win over classic Operators?
2. `expand` vs `expand_kwargs` — what does each enable?
3. `deferrable=True` — what does the operator hand off to, and what's saved?
4. `as_teardown(setups=...)` — why is this better than `trigger_rule="all_done"`?
5. List three anti-patterns that hurt scheduler performance.
6. `catchup=False` is the default in modern templates. What was the old default and what risk does it carry?

---

## Sources

- [TaskFlow Tutorial](https://airflow.apache.org/docs/apache-airflow/stable/tutorial/taskflow.html)
- [Dynamic Task Mapping](https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/dynamic-task-mapping.html)
- [Deferrable Operators](https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/deferring.html)
- [Setup and Teardown](https://airflow.apache.org/docs/apache-airflow/stable/howto/setup-and-teardown.html)
- [Task Groups](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html#taskgroups)
- [Jinja Templating](https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/templates-ref.html)

→ Next: [06 — Scheduling deep](06_scheduling.md)
