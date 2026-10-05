---
title: "Apache Airflow for AI/ML Engineers"
subtitle: "Multi-cloud + security + data-exposure lens (Career_upskill — Topic 06)"
author: "Compiled for Vatsal Raicha"
date: "2026"
lang: "en-US"
---

# How to read this ebook

This is the consolidated reading copy of **Topic 06 — Apache Airflow for AI/ML Engineers**, from the **Career_upskill** project. Source markdown files live at `topics/06_airflow/` and remain canonical.

**Audience:** A Senior/Lead AI/ML engineer preparing to credibly operate, secure, and architect Airflow at the Lead/Architect level — across MWAA, Cloud Composer, Azure Managed Airflow, Astronomer, and self-hosted on-prem. The unifying thread is **how Airflow safely exposes data and credentials** — to workers, downstream systems (Snowflake/Databricks/SageMaker/Vertex), operators (humans), and across cloud boundaries.

**Ordering:** natural numeric sequence — Modules 1 through 32, organized into 6 Parts (A–F).

**Included:** all 32 modules + FACTS.md as an appendix.

**Not included:** example DAGs and Terraform (in `code/`), quizzes (in `quizzes/`).

\newpage


\newpage

# 01 — Airflow history & landscape: why Airflow, where it fits, where it doesn't

> *"Airflow won because Python won. Pick it for orchestration in a Python shop. Don't pick it just because everyone else did."*

## Why this module exists

Airflow is the most-deployed open-source workflow orchestrator. It's also the one most-cargo-culted. A senior engineer needs to know its history (why it exists), its strengths (Python-native, vast ecosystem), its weaknesses (scheduler heaviness, DAG=arbitrary-code), and its competitors (Prefect, Dagster, Argo, Step Functions, Databricks Workflows, Snowflake Tasks). This module is the honest 30-min orientation.

---

## 1. History — the milestones

| Year | Event |
|---|---|
| **2014** | Maxime Beauchemin starts Airflow at Airbnb |
| **2015 Jun** | Open-sourced under Apache License 2.0 |
| **2016 Mar** | Joins Apache Incubator |
| **2019 Jan** | Promoted to Apache Top-Level Project |
| **2020 Dec 17** | **Airflow 2.0** released — TaskFlow API, HA scheduler, DAG serialization |
| **2021** | Astronomer is the dominant commercial sponsor; AWS launches MWAA |
| **2022** | Airflow 2.3 → dynamic task mapping; 2.4 → Datasets |
| **2023** | Triggerer + deferrable operators GA; 2.7 → setup/teardown; 2.8 → Auth Manager |
| **2024** | 2.10 → DAG-level dataset events, hybrid executors |
| **2025 Apr 22** | **Airflow 3.0** — Task SDK, multi-cluster scheduler, React UI, deadlines, asset-centric scheduling, DAG versioning |

Airflow's evolution mirrors the data community's: started as a cron-on-steroids; became a full orchestrator; in 2025 became asset-centric (data-aware).

---

## 2. What problem Airflow solves

Pipelines that:

- Run on a schedule.
- Have task dependencies (DAG).
- Need retries, alerting, observability.
- Span heterogeneous systems (S3 → Glue → Snowflake → SageMaker).
- Need backfills.
- Need audit trails for regulated environments.

Airflow's value is the **operator ecosystem**: 1000+ pre-built operators (Snowflake, Databricks, SageMaker, S3, Slack, ...) — each is a Python class that handles auth, retries, and error semantics for one system. You compose them in Python; Airflow handles the rest.

---

## 3. What Airflow is NOT

- **Not a stream processor.** Airflow runs at minute-granularity scheduler heartbeats; for sub-second event processing, use Flink / Spark Structured Streaming.
- **Not a data-transformation engine.** It orchestrates other engines (Spark, Snowflake, Databricks) but DOESN'T execute transforms in the scheduler.
- **Not a queue.** It triggers tasks; it doesn't broker messages.
- **Not a CI/CD pipeline.** Argo Workflows / Tekton / Jenkins / GitHub Actions cover that.
- **Not a low-code "drag and drop" tool.** It's code-first; analysts who want point-and-click belong in ADF / Step Functions / Dagster Cloud's UI.

---

## 4. The "DAG file is arbitrary code" reality

Airflow DAGs are **Python files in a directory**. The scheduler imports them on every refresh. Implications:

- Top-level imports run in the scheduler — expensive imports slow everything down.
- Top-level code with side effects runs constantly — `requests.get(...)` at module level is a disaster.
- A DAG author with commit access can run arbitrary code in the scheduler context — **DAG authors == cluster admins**.

This is the single biggest security pain. Airflow 3.0's Task SDK fixes part of it (tasks run in an isolated execution interface), but the scheduler still imports DAG files.

For regulated finance: PR review every DAG; CI lints for top-level expensive operations; no `eval`, no `exec`.

---

## 5. The alternative orchestrators (honest comparison)

| Tool | Python? | K8s-native? | Asset/lineage-first? | Best for | Worst for |
|---|---|---|---|---|---|
| **Airflow 2.x** | Yes | Optional | Datasets (added 2.4) | General orchestration in Python shops | Stream / asset-first / multi-tenant security |
| **Airflow 3.x** | Yes | Optional | Yes (Assets) | Same + cleaner security model | Cutting edge; less battle-tested |
| **Prefect 3** | Yes | Optional | Yes | Pythonic, modern API; cloud good | Smaller community |
| **Dagster** | Yes | Optional | **Yes (asset-centric from the start)** | Modern data platforms with lineage-first design | Existing Airflow shops; cost |
| **Argo Workflows** | YAML/CUE | **Yes (K8s-native)** | No | ML/data pipelines on K8s | Non-K8s shops |
| **Mage AI** | Yes | Optional | Yes | SQL+Python notebooks-as-pipelines | Heavy enterprise scale |
| **Flyte** | Yes | **Yes** | Yes (typed pipelines) | ML pipelines, Lyft-style | Pure ETL |
| **AWS Step Functions** | JSON/CDK | No (serverless) | No | AWS-native; **Capital One's actual choice** | Multi-cloud, complex Python |
| **Databricks Workflows / Lakeflow Jobs** | JSON | Databricks | Limited | If you live in Databricks | Outside Databricks |
| **Snowflake Tasks/Streams** | SQL | No | Inside Snowflake | In-warehouse SQL DAGs | Cross-system |
| **ADF / Synapse Pipelines** | JSON/UI | Azure | Limited | Azure-first shops | Multi-cloud |
| **Temporal** | Multi-lang | Optional | No | Long-running workflows / sagas | Data pipelines |

For Capital One: **Step Functions is the published MLOps spine.** Airflow appears in data-engineering teams orchestrating ETL into Snowflake / Redshift. Knowing both — and when to pick which — is the architect-grade insight.

---

## 6. When to pick Airflow (the senior-engineer judgment)

✅ **Pick Airflow when**:
- Heavy Python shop with existing Airflow investment.
- Many heterogeneous systems to orchestrate (Snowflake + Databricks + SageMaker + email + ...).
- Strong operator ecosystem matters.
- Team can operate it (or has Astronomer / MWAA budget).
- Multi-day backfills are common (Airflow's `catchup` model fits).

❌ **Don't pick Airflow when**:
- Pure AWS-native shop with simple workflows → **Step Functions**.
- K8s-native data platform → **Argo Workflows** + Argo Events.
- Asset/lineage-first modern data platform from scratch → **Dagster**.
- Workflows are inside a single warehouse → **Snowflake Tasks / dbt + Airflow's narrower role**.
- Sub-second event-driven → **Flink / Kafka Streams**.

---

## 7. Airflow at Capital One — honest take

The published MLOps spine at Capital One (per Topic 04 research):

```
S3 → Glue / EMR → S3 → SageMaker Pipelines / Step Functions → KServe on EKS
```

**Step Functions is the headline orchestrator.** Airflow likely runs in data-engineering teams for nightly ETL into Snowflake / Redshift. Both coexist.

For the architect interview, the framing:

> "Airflow remains valuable for cross-system ETL where the Python operator ecosystem and audit trail matter — that's likely where C1's data engineering teams run it. For the ML production spine, Step Functions wins on AWS-nativity, JSON-based state machines that map cleanly to Cloud Custodian-style policy, and serverless economics. I would not introduce Airflow into a greenfield MLOps system at C1; I would use Step Functions + EKS + KServe."

This is a more credible answer than "Airflow is the best."

---

## 8. The 2025-2026 trends

- **Airflow 3.0** brings asset-centric scheduling, security improvements (Task SDK isolation), DAG versioning. Released April 2025; adoption ramping.
- **OpenLineage** is now the standard for lineage events; Airflow has it built-in.
- **dbt + Airflow via Cosmos** is the modern data-stack pattern.
- **Managed Airflow (MWAA, Composer, Astro)** dominates over self-host for new deployments.
- **Asset-first orchestrators** (Dagster) are gaining at the high end.

---

## Sanity check

1. Why was Airflow created (in one sentence)?
2. What changed conceptually between Airflow 2.x and 3.0?
3. "DAG authors == cluster admins" — why is this the case, and what's the practical mitigation in a regulated shop?
4. Capital One's published MLOps spine uses what orchestrator, not Airflow?
5. Three scenarios where you should pick something other than Airflow.
6. What's the role of OpenLineage in modern Airflow?

---

## Sources

- [Apache Airflow homepage](https://airflow.apache.org/)
- [Airflow blog: 2.0 announcement](https://airflow.apache.org/blog/airflow-two-point-oh-is-here/)
- [Airflow 3.0 announcement](https://airflow.apache.org/blog/airflow-3-0/)
- [Airflow Improvement Proposals (AIPs)](https://cwiki.apache.org/confluence/display/AIRFLOW/Airflow+Improvement+Proposals)
- [Capital One tech blog](https://www.capitalone.com/tech/)

→ Next: [02 — Core concepts](02_core_concepts.md)


\newpage

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


\newpage

# 03 — Airflow architecture: Webserver, Scheduler, Triggerer, Workers, Metadata DB, DAG storage

## Why this module exists

Knowing where code actually runs is the difference between "Airflow works" and "I can debug Airflow at 2am." This module maps the components.

---

## 1. Components

```
┌─────────────────────────────────────────────────────────────────┐
│ ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │
│ │ Webserver   │  │ Scheduler(s)│  │ Triggerer   │               │
│ │ (FAB/React) │  │ HA capable  │  │ async       │               │
│ └──────┬──────┘  └──────┬──────┘  └──────┬──────┘               │
│        │                │                │                       │
│        └────────────────┼────────────────┘                       │
│                         │                                        │
│ ┌────────────────────────▼────────────────────────────┐          │
│ │              Metadata Database                      │          │
│ │              (Postgres recommended)                 │          │
│ └────────────────────────┬────────────────────────────┘          │
│                         │                                        │
│        ┌────────────────┼────────────────┐                       │
│        │                │                │                       │
│ ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐                │
│ │ Worker 1    │  │ Worker 2    │  │ Worker N    │                │
│ │ Celery /K8s │  │             │  │             │                │
│ └─────────────┘  └─────────────┘  └─────────────┘                │
│                                                                  │
│ DAG storage: shared FS / git-sync / S3 sync / image-baked        │
└──────────────────────────────────────────────────────────────────┘
```

### 1.1 Webserver (Flask AppBuilder until 2.x; React in 3.x)

- Serves the UI and REST API.
- Reads metadata DB; rarely writes.
- Behind a load balancer with TLS.
- Can run multiple replicas — all stateless (sessions in metadata DB).

### 1.2 Scheduler (the heart)

- Imports DAG files; parses; serializes to metadata DB.
- Triggers DAG runs on schedule.
- Examines task dependencies; sends tasks to executor when ready.
- **HA supported since 2.0** — multiple schedulers coordinate via Postgres `SELECT FOR UPDATE SKIP LOCKED`.

The scheduler is the most resource-intensive component for large DAG counts. If it's heartbeat-timing-out, you have too many DAGs / heavy top-level imports / too few resources.

### 1.3 Triggerer (async deferrable-operator handler)

- Single async (asyncio) process per Triggerer pod.
- Handles **deferrable operators** — operators that yield control while waiting for an external event.
- One Triggerer pod can manage thousands of concurrent "waits."
- Introduced in 2.2; mandatory for cost-efficient sensor patterns.

### 1.4 Workers

- Execute tasks.
- Executor-dependent (Celery, K8s, etc.) — see module 04.
- Each task is a separate process (the Celery/K8s task lifecycle).

### 1.5 Metadata Database

- Postgres recommended (MySQL 8.0+ supported; SQLite for testing only).
- Stores: DagModel (serialized DAGs), DagRun, TaskInstance, XCom, Connection, Variable, Pool, Job, Log, User, Permission.
- The single source of truth.

### 1.6 DAG storage

How DAG files reach the scheduler + workers. Patterns:

- **Shared filesystem** (NFS, EFS, etc.) — schedulers + workers mount the same path.
- **git-sync sidecar** — sidecar pulls latest from git into a shared volume.
- **S3 / GCS / Blob sync** — MWAA pattern; bucket sync.
- **Image-baked** — Astronomer pattern; DAGs in the container image.

---

## 2. Resource sizing (rules of thumb)

For 100 DAGs, 1000 tasks/day:

- Scheduler: 1 pod, 2 vCPU, 4 GB.
- Webserver: 2 replicas (HA), 1 vCPU, 2 GB each.
- Triggerer: 1 pod, 1 vCPU, 2 GB. (Add more if you have thousands of deferred tasks.)
- Workers: Celery pool of 4-8 pods at start; scale on Celery queue length.
- Postgres: `db.t3.medium` for small loads; up to `db.r5.large` for large.

For 10,000 DAGs:
- Scheduler: 2+ pods, 8 vCPU, 32 GB.
- Postgres: `db.r5.xlarge`+ with read replicas.
- DAG parsing optimization is critical — see module 27 (SRE).

---

## 3. The DAG parsing loop

The scheduler parses DAGs at intervals (default 30s; `dag_dir_list_interval`). Each parse:

1. List Python files in `dag_folder`.
2. Import each file (this is where top-level code runs!).
3. Extract DAG objects.
4. Compare to metadata DB; update if changed.

**Heavy top-level imports** kill scheduler throughput. The rule:

```python
# WRONG — top-level
import pandas as pd                           # 200 MB import every parse cycle
heavy_data = pd.read_csv("/path/to/big.csv")  # runs every parse

# RIGHT — inside task
@task
def my_task():
    import pandas as pd
    df = pd.read_csv(...)
```

For 100 DAGs with 200 MB imports each: 30s × 100 × 200 MB = unworkable. Move imports inside tasks.

---

## 4. The serialized DAG model

Since Airflow 2.0, the scheduler **serializes** DAGs to the metadata DB (`dag_pickle` table). The webserver renders from the serialized form — it doesn't re-import DAGs. This decouples UI from DAG parsing.

Implication: a DAG that fails to parse won't break the webserver; it just won't update.

---

## 5. Scheduler HA mechanics

Multiple schedulers coordinate via Postgres row-level locks:

```sql
SELECT * FROM dag_run WHERE state = 'queued' AND ... FOR UPDATE SKIP LOCKED;
```

Schedulers grab disjoint sets of DAG runs; no master/coordinator process. Postgres-only feature originally; MySQL 8.0+ supports SKIP LOCKED.

For HA: run **2-3 schedulers** in production. Webserver: 2+. Triggerer: 1+ (each is single-threaded but async-internally fast).

---

## 6. Metadata DB choice

| Option | Notes |
|---|---|
| **Postgres** | The standard. RDS, Cloud SQL, Azure Database for Postgres. |
| **MySQL 8.0+** | Supported; not preferred. |
| **SQLite** | **Test only.** No HA, no concurrency. |
| **Oracle / MSSQL** | Supported but rarely seen. |

For production: Postgres 14+. Provision with `max_connections >= scheduler_replicas * 60 + workers * pool_size * 2`. The metadata DB is your bottleneck at scale.

---

## 7. Log handlers

Logs go to:

- Default: local filesystem (per worker).
- S3 (`s3://airflow-logs/...`), GCS, Azure Blob.
- ElasticSearch / OpenSearch.
- CloudWatch (MWAA), Cloud Logging (Composer), Log Analytics (Azure Managed Airflow).

Configure via `[logging]` in `airflow.cfg`:

```ini
[logging]
remote_logging = True
remote_log_conn_id = aws_default
remote_base_log_folder = s3://myorg-airflow-logs/
encrypt_s3_logs = False
```

For regulated finance: KMS-encrypted log bucket; lifecycle policy to S3 Glacier.

---

## 8. Single points of failure

Even with HA scheduler/webserver:

- **Metadata DB**: if it goes down, Airflow stops. Use multi-AZ RDS / replicated Postgres / managed offering.
- **DAG storage**: if git-sync sidecar fails or S3 is unavailable, no new DAG versions deploy.
- **External secret backend**: if Vault is down, tasks fail to fetch credentials at runtime.
- **Worker queue (Celery → Redis/Rabbit)**: if down, tasks queue but don't execute.

For SRE-grade: HA each layer + monitor Postgres replication lag + alert on `scheduler heartbeat > 60s`.

---

## 9. The Airflow 3.0 architectural change — Task SDK

In 2.x, every task runs by loading the entire DAG file again in the worker. In 3.0, the **Task SDK** decouples this:

- Tasks run in isolated processes/containers via the Task SDK.
- They don't need access to the full DAG or metadata DB.
- Permissions are scoped per-task.

This addresses the "DAG authors == cluster admins" problem. Module 30 covers Airflow 3.0 in detail.

---

## Sanity check

1. Where does a `@task`'s Python code actually execute, and on which Airflow component?
2. The Triggerer was introduced in 2.2 — what problem does it solve?
3. "Multiple schedulers" — what database feature is required for HA?
4. Why does heavy top-level `import` in DAG files kill scheduler throughput?
5. The metadata DB is a single point of failure — what's the standard mitigation?
6. Airflow 3.0's Task SDK addresses what conceptual problem in 2.x?

---

## Sources

- [Airflow architecture overview](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/overview.html)
- [HA Scheduler](https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/scheduler.html)
- [Triggerer](https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/deferring.html)
- [DAG Serialization](https://airflow.apache.org/docs/apache-airflow/stable/internal-api/dag-serialization.html)
- [Production logging configuration](https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/logging-monitoring/index.html)

→ Next: [04 — Executors deep](04_executors.md)


\newpage

# 04 — Executors deep: Sequential, Local, Celery, Kubernetes, CeleryKubernetes, Edge

## Why this module exists

The executor is the architectural decision with the biggest cost and security implications. Pick wrong and you'll fight Airflow for a year.

---

## 1. The executors

| Executor | Concurrency | Where tasks run | Use case |
|---|---|---|---|
| **SequentialExecutor** | 1 task | Same process as scheduler | Smoke tests, SQLite only |
| **LocalExecutor** | N parallel processes | On the scheduler host | Single-machine dev / small prod |
| **CeleryExecutor** | Distributed | Celery workers + Redis/RabbitMQ | The most-deployed production executor |
| **KubernetesExecutor** | One Pod per task | Each task is a K8s Pod | Cloud-native, elastic scale |
| **CeleryKubernetesExecutor** | Hybrid | Celery for short, K8s for long | Best of both worlds |
| **EdgeExecutor** (2.10+) | Remote agents | Hosts outside the cluster | On-prem agents talking to a cloud scheduler |

For new prod deployments in 2025-2026: **KubernetesExecutor** is the dominant pick. CeleryExecutor remains for low-resource shops + workloads with very short tasks (overhead of pod-per-task hurts).

---

## 2. SequentialExecutor

Single-threaded. SQLite as metadata DB. **Test only.** Mentioned for completeness.

---

## 3. LocalExecutor

Multi-process on the scheduler host:

```ini
[core]
executor = LocalExecutor
parallelism = 32
max_active_runs_per_dag = 16
```

Pros: simple; no extra infra; up to ~32 concurrent tasks.

Cons: all tasks run on the scheduler box; one runaway task crashes others; no isolation; can't scale horizontally.

When OK: small teams, < 100 DAGs, < 32 concurrent tasks at peak.

---

## 4. CeleryExecutor — the workhorse

```ini
[core]
executor = CeleryExecutor
[celery]
broker_url = redis://redis:6379/0
result_backend = db+postgresql://airflow:...@postgres:5432/airflow
```

Architecture:
- **Celery workers** (separate Deployment/Pod-set) pull from Redis/RabbitMQ.
- Scheduler enqueues tasks.
- Workers pick up and execute.

Pros:
- Mature; widely understood.
- Workers can scale horizontally.
- Short task overhead is low (worker stays warm).

Cons:
- Workers are long-lived processes — Python package conflicts across tasks.
- Workers idle between tasks consume resources.
- Need Redis + result backend infra.
- No per-task isolation (one bad pickle can crash a worker).

For ETL with 1000+ short tasks/hour: Celery wins.

### 4.1 Celery scaling — Flower + KEDA

[Flower](https://flower.readthedocs.io/) is the Celery monitoring UI. Shows worker count, queue length, task state.

For autoscaling: **KEDA** with Celery queue length metric scales worker pods up/down. Standard pattern on K8s self-host.

---

## 5. KubernetesExecutor — one Pod per task

```ini
[core]
executor = KubernetesExecutor
[kubernetes]
namespace = airflow
worker_container_repository = myorg/airflow
worker_container_tag = 2.10.3
```

Each task runs in a **freshly-spawned K8s Pod**. The Pod uses the image specified by the operator or DAG (via `executor_config={"pod_override": ...}`).

Pros:
- Per-task isolation — each task gets its own Pod with own Python deps.
- Elastic scale — pods are created on demand, terminated when done.
- Right-size resources per task — heavy tasks get big pods, light tasks tiny pods.
- Composes with Karpenter for autoscaling.

Cons:
- Pod startup overhead (~5-15s per task) — bad for many short tasks.
- Image management overhead — each task's image must be available.
- More moving parts to debug.

For ML pipelines, heavy ETL, GPU jobs: K8sExecutor is the right answer.

### 5.1 Pod override pattern

```python
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from kubernetes.client.models import V1Pod, V1Container, V1ResourceRequirements

@task(executor_config={
    "pod_override": V1Pod(
        spec=V1PodSpec(
            containers=[V1Container(
                name="base",
                resources=V1ResourceRequirements(
                    requests={"cpu": "2", "memory": "8Gi"},
                    limits={"cpu": "4", "memory": "16Gi", "nvidia.com/gpu": "1"},
                ),
            )],
            service_account_name="ml-tasks-sa",            # IRSA / WIF
            tolerations=[V1Toleration(key="nvidia.com/gpu", operator="Exists")],
            node_selector={"workload": "gpu-training"},
        ),
    ),
})
def train_model():
    ...
```

Each task can be a different "shape" of pod. Combined with Karpenter, you get cost-efficient per-task scaling.

---

## 6. CeleryKubernetesExecutor — the hybrid

```ini
[core]
executor = CeleryKubernetesExecutor
```

Tasks declared with `queue="kubernetes"` run on K8sExecutor; everything else on Celery. Lets you reserve K8sExecutor for heavy / GPU / long tasks while keeping Celery for high-throughput short tasks.

The pragmatic production pattern when you have both kinds of workloads.

---

## 7. EdgeExecutor (2.10+, experimental)

Long-running edge agents pull tasks from the scheduler over HTTPS. Tasks run on-prem or in restricted networks. Useful for:

- On-prem agents pulling work from MWAA / Astro.
- Air-gapped tasks triggered by central scheduler.
- IoT / edge data collection.

Still maturing as of 2026.

---

## 8. The executor choice matrix

| | LocalExecutor | CeleryExecutor | KubernetesExecutor |
|---|---|---|---|
| Low ops overhead | ✅ | ⚠️ Redis + Flower | ⚠️ K8s cluster |
| Per-task isolation | ❌ | ❌ | ✅ |
| Cost-efficient at scale | ❌ | ⚠️ idle workers | ✅ (with autoscale) |
| Short tasks (<10s) | ✅ | ✅ | ❌ pod overhead |
| Long tasks (>30min) | ❌ resource sharing | ⚠️ ties up worker | ✅ |
| Custom dep per task | ❌ | ❌ same image | ✅ pod_override |
| GPU per task | ❌ | ❌ | ✅ |
| Regulated environment | ⚠️ | ⚠️ | ✅ best audit trail |

---

## 9. Executor and the security boundary

- **LocalExecutor**: task code runs as the scheduler user. Compromised task = compromised scheduler. Don't use for untrusted DAGs.
- **CeleryExecutor**: task runs as the worker user. Compromised task = compromised worker (and the Celery worker's entire deps). Still wide blast radius.
- **KubernetesExecutor**: task runs in its own Pod with its own SA, image, network policy. The strongest isolation. **The right choice for multi-tenant Airflow.**

For Capital One–style: K8sExecutor + per-task IRSA SA + per-task PSA-restricted enforcement is the path.

---

## 10. Managed offerings and executors

| Service | Executor | Choice? |
|---|---|---|
| MWAA | **Celery only** | No choice |
| Cloud Composer 2/3 | **CeleryKubernetes** (Composer 2), **Celery + K8sPodOperator** (Composer 3) | Limited |
| Azure Managed Airflow | KubernetesExecutor | Yes |
| Astronomer Astro | KubernetesExecutor (default) | Yes |
| Self-host Helm chart | Any | Yes |

For Capital One AWS context: **MWAA is Celery-only**. If you need K8sExecutor, you self-host on EKS or use Astro on AWS Hybrid.

---

## Sanity check

1. Pod startup overhead is ~5-15s on K8sExecutor. When does that matter?
2. Why is K8sExecutor the strongest isolation choice for multi-tenant Airflow?
3. What does CeleryKubernetesExecutor give you that pure K8s doesn't?
4. Celery + KEDA — what does KEDA scale on?
5. What's the executor option in MWAA, and why does that constrain architectural choices?
6. `pod_override` lets you customize what per task?

---

## Sources

- [Airflow Executors](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/executor/index.html)
- [Celery Executor](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/executor/celery.html)
- [Kubernetes Executor](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/executor/kubernetes.html)
- [Edge Executor (2.10+)](https://airflow.apache.org/docs/apache-airflow-providers-edge/)
- [Flower](https://flower.readthedocs.io/)
- [KEDA](https://keda.sh/)

→ Next: [05 — DAG authoring](05_dag_authoring.md)


\newpage

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


\newpage

# 06 — Scheduling deep: logical date, data interval, timetables, catchup, backfill, Datasets/Assets

## Why this module exists

Scheduling is the most-misunderstood part of Airflow. Get it right or wake up at 3am.

---

## 1. Logical date vs data interval

Critical distinction. For `schedule="@daily"` starting 2026-01-01:

| Field | Value for first run |
|---|---|
| `logical_date` | `2026-01-01T00:00:00` |
| `data_interval_start` | `2026-01-01T00:00:00` |
| `data_interval_end` | `2026-01-02T00:00:00` |
| Actual wall-clock execution | **`2026-01-02T00:00:00`** (after interval ends) |

A daily DAG "for 2026-01-01" runs **at the end** of 2026-01-01 — when that day's data is complete. Templates use `data_interval_start` (the logical "what day is this run about?").

This is why backfills work consistently: re-running logical_date=2026-01-01 processes the same data interval regardless of when it runs.

---

## 2. Schedule formats

- **Cron**: `"0 3 * * *"` — at 03:00 daily.
- **Preset**: `"@daily"`, `"@hourly"`, `"@weekly"`, `"@monthly"`, `"@yearly"`, `"@once"`.
- **Timedelta**: `timedelta(hours=4)` — every 4 hours from start_date.
- **List of Datasets**: `[dataset_A, dataset_B]` — run when ANY dataset updates.
- **Custom Timetable** (2.2+): for unusual schedules (business days, specific times).
- **None**: trigger-only DAGs.

---

## 3. Catchup — the source of "365 runs at once"

`catchup=True` (the historical default): on first deploy, Airflow runs every interval between `start_date` and now.

- DAG with `start_date=2025-01-01` + `schedule="@daily"` + `catchup=True` deployed today → ~500 runs queued.
- Recipe for disaster on a real warehouse.

**Always set `catchup=False` for new DAGs.** Use explicit backfills when needed (`airflow dags backfill`).

---

## 4. Backfill

```bash
airflow dags backfill -s 2026-01-01 -e 2026-01-31 sales_etl
```

Runs the DAG for each logical date in the range. Use for:
- Filling gaps from outages.
- Reprocessing data with corrected logic.
- Loading historical data on a new pipeline.

For large backfills: use `--reset-dagruns` carefully (deletes prior runs first); throttle with pools to avoid warehouse overload.

---

## 5. Custom Timetables (AIP-39)

For schedules cron can't express:

```python
from airflow.timetables.trigger import CronTriggerTimetable
from pendulum import timezone

@dag(
    timetable=CronTriggerTimetable("0 9 * * 1-5", timezone=timezone("America/New_York")),
    start_date=datetime(2026, 1, 1),
    catchup=False,
)
def weekday_morning_etl():
    ...
```

Business-day-only, NY timezone, 9am. CronTriggerTimetable handles DST.

For more complex schedules (e.g., "last business day of month"): write a custom Timetable subclass.

---

## 6. Dataset-driven scheduling (the modern way)

```python
ds_sales = Dataset("snowflake://prod.staging.sales")
ds_inventory = Dataset("snowflake://prod.staging.inventory")

# Producer
@dag(schedule="0 2 * * *", catchup=False)
def load_sales():
    @task(outlets=[ds_sales])
    def load(): ...

# Consumer — runs when BOTH datasets update
@dag(schedule=[ds_sales, ds_inventory], catchup=False)
def aggregate():
    @task
    def agg(): ...
```

The consumer DAG triggers when both datasets have been updated since the last run. Replaces cron-coordinated dependencies between DAGs.

Limitation: requires producer DAGs to declare `outlets=` on their final tasks. No automatic detection.

In Airflow 3.0: Datasets renamed to **Assets** with richer metadata (`@asset` decorator, more conditions).

---

## 7. `max_active_runs` + `max_active_tasks`

```python
@dag(
    max_active_runs=1,                  # only one run at a time per DAG
    max_active_tasks=10,                # max tasks running per run
    ...
)
```

For DAGs that touch a shared resource (e.g., Snowflake staging table) — `max_active_runs=1` prevents data races on backfills.

`max_active_tasks` (formerly `concurrency`) protects against fan-out blowing up the worker pool.

---

## 8. Schedule + DAG-run states

| State | Meaning |
|---|---|
| `queued` | Scheduled but no tasks yet started |
| `running` | At least one task is in progress |
| `success` | All tasks succeeded |
| `failed` | A task failed |
| `up_for_retry` | Task failed but will retry |
| `upstream_failed` | A predecessor failed |
| `skipped` | Branched away |

Failure propagation: a task failure marks downstream as `upstream_failed` unless `trigger_rule="all_done"` etc.

`trigger_rule` options: `all_success` (default), `all_failed`, `all_done`, `one_success`, `one_failed`, `none_failed`, `none_skipped`, `always`.

---

## 9. Time zones

Airflow stores all timestamps in UTC. Schedules can be specified in local zones via Timetables. Templates render in UTC by default.

Best practice: write all SQL/code in UTC; convert at the boundary (UI display, business reports).

---

## 10. The scheduling decision tree

```
Need to run when external data lands?
   → Dataset-driven schedule

Need to run on a fixed clock?
   → Cron string (UTC) or CronTriggerTimetable (with tz)

Need to run after another DAG?
   → Dataset (preferred) or ExternalTaskSensor

Need to run irregularly?
   → schedule=None + TriggerDagRunOperator from a controlling DAG / API

Need to run once for a one-shot migration?
   → schedule="@once", catchup=False
```

---

## Sanity check

1. For `schedule="@daily"` with `logical_date=2026-05-20`, when does the run actually start (wall-clock)?
2. Why is `catchup=False` the safe default for new DAGs?
3. Dataset-driven scheduling replaces what older pattern?
4. `max_active_runs=1` — when is this important?
5. CronTriggerTimetable handles what that a raw cron string doesn't?
6. The default `trigger_rule` is what, and what does it imply for branching?

---

## Sources

- [Scheduling and Timetables](https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/timetable.html)
- [Datasets and Data-aware scheduling](https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/datasets.html)
- [Backfill](https://airflow.apache.org/docs/apache-airflow/stable/dag-run.html#backfill)
- [AIP-39 Custom Timetables](https://cwiki.apache.org/confluence/display/AIRFLOW/AIP-39+Richer+scheduler_interval)

→ Next: [07 — Sensors & triggers](07_sensors_triggers.md)


\newpage

# 07 — Sensors & triggers: poke vs reschedule vs deferrable; the Triggerer process

## Why this module exists

Sensors are how Airflow waits for external state. Done wrong, they bankrupt your cluster. Deferrable operators (2.2+) are the production answer.

---

## 1. Three modes for a Sensor

### 1.1 `mode="poke"` (the default — DON'T)

```python
S3KeySensor(task_id="wait", mode="poke", poke_interval=60, timeout=3600, ...)
```

The sensor **holds a worker slot for the full timeout** while polling. 100 simultaneous sensors waiting an hour = 100 worker slots gone.

For a small DAG count: fine. For a real production Airflow: cluster death.

### 1.2 `mode="reschedule"`

```python
S3KeySensor(task_id="wait", mode="reschedule", poke_interval=300, timeout=86400, ...)
```

Between pokes, the task is **rescheduled** — released the worker slot, queued again later. Worker only used during the brief check.

Trade-off: each poke pays scheduling overhead. `poke_interval >= 60s` recommended.

### 1.3 `deferrable=True` (the modern answer)

```python
S3KeySensor(task_id="wait", deferrable=True, poke_interval=60, timeout=86400, ...)
```

The task hands off to the **Triggerer process** (a single async event loop). Worker slot released; no per-poke scheduling overhead. One Triggerer can manage **thousands of concurrent waits**.

For any production with many sensors: **deferrable everywhere**. Both `S3KeySensor` and many other sensors / operators have `deferrable=True` parameter.

---

## 2. The Triggerer mechanics

- Asyncio-based — one Triggerer process runs many awaitable triggers concurrently.
- Each deferred task creates a `Trigger` row in the metadata DB with serialized state.
- Triggerer picks up triggers from the DB, runs them, signals completion back via DB.
- On completion: scheduler picks up the task again, re-runs (typically from a continuation point in the operator).

A single Triggerer pod can manage thousands of triggers. For very large deployments, run multiple Triggerer pods.

---

## 3. Common sensors

| Sensor | Use | Deferrable? |
|---|---|---|
| `S3KeySensor` | Wait for S3 object | Yes |
| `GCSObjectExistenceSensor` | GCS object | Yes |
| `WasbBlobSensor` | Azure Blob | Yes |
| `ExternalTaskSensor` | Another DAG's task | Yes (2.7+) |
| `SqlSensor` | SQL query result | Yes |
| `HttpSensor` | HTTP endpoint | Yes |
| `FileSensor` | Local file (don't use in prod) | No |
| `KubernetesPodOperator` (sync via wait) | K8s pod completion | Has `deferrable` mode |
| `DatabricksRunSensor` | Databricks run | Yes |
| `EmrJobFlowSensor` | EMR cluster | Yes |
| `RedshiftClusterSensor` | Redshift cluster ready | Yes |
| `BigQueryTableSensor` | BQ table existence | Yes |

---

## 4. The Triggerer's failure modes

- **Triggerer crashes**: deferred tasks are picked up by another Triggerer (HA) or wait until it restarts. No data loss; just delay.
- **Triggerer overloaded**: thousands of triggers in a single asyncio loop can cause backlog. Run multiple Triggerers; partition by `kubernetes.trigger_id_hash` or similar.
- **Network partition between Triggerer and the external service it's polling**: triggers retry; eventually time out.

For SRE: alert on `triggers_pending` > threshold and `trigger_processing_time` p95.

---

## 5. Custom deferrable operators

Write your own:

```python
from airflow.triggers.base import BaseTrigger, TriggerEvent

class MyTrigger(BaseTrigger):
    def __init__(self, conn_id: str, poll_interval: int):
        super().__init__()
        self.conn_id = conn_id
        self.poll_interval = poll_interval

    def serialize(self):
        return ("my_package.MyTrigger", {"conn_id": self.conn_id, "poll_interval": self.poll_interval})

    async def run(self):
        while True:
            if await self.condition_met():
                yield TriggerEvent({"status": "success"})
                return
            await asyncio.sleep(self.poll_interval)
```

For wrapping any "wait for external thing" — REST API polls, custom event sources, message queue depth.

---

## 6. The "smart sensors" history note

Airflow once had "smart sensors" (2.0-2.2) — a separate sensor pool. Removed in 2.4 in favor of deferrable operators. If you see references in old material: ignore.

---

## 7. Common patterns

### 7.1 Wait for file then process

```python
wait = S3KeySensor(
    task_id="wait_for_export",
    bucket_key="exports/{{ ds }}/data.parquet",
    bucket_name="myorg-data",
    deferrable=True,
    poke_interval=300,
    timeout=86400,
)

@task
def process(): ...

wait >> process()
```

### 7.2 Wait for another DAG's task

```python
from airflow.sensors.external_task import ExternalTaskSensor

wait_for_upstream = ExternalTaskSensor(
    task_id="wait_for_upstream",
    external_dag_id="upstream_etl",
    external_task_id="load_to_dwh",
    deferrable=True,
    execution_delta=timedelta(hours=1),     # upstream's logical_date offset
    timeout=86400,
)
```

**Better alternative for new DAGs**: use Datasets. ExternalTaskSensor is the legacy pattern.

### 7.3 Wait for SQL condition

```python
from airflow.providers.common.sql.sensors.sql import SqlSensor

wait_for_data = SqlSensor(
    task_id="wait_for_data_ready",
    conn_id="snowflake_prod",
    sql="SELECT count(*) > 100000 FROM staging.events WHERE ds='{{ ds }}'",
    deferrable=True,
    poke_interval=600,
)
```

For data-quality gates: simple and powerful.

---

## 8. The "deferrable everywhere" rule

For any production Airflow:

- **Sensors**: always `deferrable=True`.
- **Long-running operators with wait** (SageMaker training, Databricks job, EMR step): use the `deferrable=True` variant.
- **`poke_interval`**: typically 60-600s. Lower = more polling overhead; higher = stale wakeup.
- **`timeout`**: set conservatively. A sensor stuck forever should fail loudly via SLA / deadline.

---

## Sanity check

1. `mode="poke"` vs `mode="reschedule"` vs `deferrable=True` — describe what each costs.
2. The Triggerer is asyncio. Why does that let it manage thousands of concurrent triggers on one pod?
3. ExternalTaskSensor vs Dataset-driven scheduling — when to pick which?
4. SqlSensor with `deferrable=True` — what runs the SQL query during the wait?
5. "Smart sensors" — what happened to them?

---

## Sources

- [Deferrable Operators & Triggers](https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/deferring.html)
- [Sensors](https://airflow.apache.org/docs/apache-airflow/stable/howto/sensor-howto.html)
- [Common SQL Sensors](https://airflow.apache.org/docs/apache-airflow-providers-common-sql/stable/sensors/index.html)
- [External Task Sensor](https://airflow.apache.org/docs/apache-airflow/stable/howto/sensor-howto.html#external-task-sensor)

→ Next: [08 — Connections, Variables, Secrets Backends](08_secrets_backends.md)


\newpage

# 08 — Connections, Variables, and Secrets Backends

## Why this module exists

Connections + Variables are the primitives Airflow uses for runtime config and credentials. Where they live (metadata DB vs Secrets Backend) is a security decision.

---

## 1. Connection

A Connection is a typed record: conn_id, type, host, port, schema, login, password, extras (JSON).

```bash
airflow connections add snowflake_prod \
  --conn-type snowflake \
  --conn-host myorg.snowflakecomputing.com \
  --conn-login svc_airflow \
  --conn-password '<from-vault>' \
  --conn-schema ANALYTICS \
  --conn-extra '{"warehouse":"ETL_WH","database":"PROD","role":"airflow_etl"}'
```

Stored in `connection` table; password column encrypted with **Fernet key**.

For an operator: `SnowflakeOperator(conn_id="snowflake_prod", sql="...")`.

The Hook for a given type looks up the conn, extracts auth, builds the client.

---

## 2. Variable

Key-value strings in `variable` table (encrypted with Fernet).

```python
threshold = Variable.get("quality_threshold", default_var="0.95")
team = Variable.get("team_routing", deserialize_json=True)  # parses JSON
```

Use for: env-specific paths, feature flags, thresholds.

**Don't put secrets in Variables.** Use Connections (audited better) or Secrets Backend.

---

## 3. Fernet key

`fernet_key` in `airflow.cfg` (or env `AIRFLOW__CORE__FERNET_KEY`) encrypts:
- Connection passwords
- Variables (their values)

If you lose the Fernet key: encrypted values are unrecoverable. **Treat it like a master key.** Rotate via `airflow rotate-fernet-key` with the new key appended to the config (old key still readable during transition).

---

## 4. Secrets Backend — the production answer

A Secrets Backend pulls secrets from an external system at runtime. **Replaces the metadata DB** for secret storage.

### 4.1 Order of precedence

When `conn_id` is looked up:

1. Environment variables (`AIRFLOW_CONN_X=`).
2. **Secrets Backend** (if configured).
3. Metadata DB (the legacy default).

Variables similarly via `AIRFLOW_VAR_X=`.

### 4.2 Configuration

```ini
[secrets]
backend = airflow.providers.amazon.aws.secrets.secrets_manager.SecretsManagerBackend
backend_kwargs = {"connections_prefix": "airflow/connections", "variables_prefix": "airflow/variables", "profile_name": null}
```

Now `conn_id=snowflake_prod` → look up `airflow/connections/snowflake_prod` in AWS Secrets Manager. JSON like:

```json
{
  "conn_type": "snowflake",
  "host": "myorg.snowflakecomputing.com",
  "login": "svc_airflow",
  "password": "<secret>",
  "schema": "ANALYTICS",
  "extra": "{\"warehouse\":\"ETL_WH\",\"database\":\"PROD\"}"
}
```

### 4.3 Built-in backends

| Backend | Provider |
|---|---|
| `SecretsManagerBackend` | AWS Secrets Manager |
| `SystemsManagerParameterStoreBackend` | AWS SSM Parameter Store |
| `CloudSecretManagerBackend` | GCP Secret Manager |
| `AzureKeyVaultBackend` | Azure Key Vault |
| `VaultBackend` | HashiCorp Vault |
| `LocalFilesystemBackend` | Plain files (dev only) |

Each from the provider package (`apache-airflow-providers-amazon`, etc.).

---

## 5. AWS Secrets Manager backend — wiring

```ini
[secrets]
backend = airflow.providers.amazon.aws.secrets.secrets_manager.SecretsManagerBackend
backend_kwargs = {
  "connections_prefix": "airflow/connections",
  "variables_prefix":   "airflow/variables",
  "config_prefix":      "airflow/config"
}
```

Airflow scheduler/worker IAM role needs `secretsmanager:GetSecretValue` on `airflow/*`. On MWAA: the execution role (module 16).

Pattern: put secret in Secrets Manager once; reference by conn_id everywhere; rotate via Secrets Manager rotation Lambda.

---

## 6. GCP Secret Manager backend

```ini
backend = airflow.providers.google.cloud.secrets.secret_manager.CloudSecretManagerBackend
backend_kwargs = {
  "connections_prefix": "airflow-connections",
  "variables_prefix":   "airflow-variables",
  "project_id":         "my-airflow-proj"
}
```

GCP Secret Manager secret names like `airflow-connections-snowflake_prod`. Workload Identity / service account permission for the secret.

---

## 7. Azure Key Vault backend

```ini
backend = airflow.providers.microsoft.azure.secrets.key_vault.AzureKeyVaultBackend
backend_kwargs = {
  "vault_url":           "https://my-kv.vault.azure.net/",
  "connections_prefix":  "airflow-connections",
  "variables_prefix":    "airflow-variables",
  "sep":                 "-"
}
```

KV secret names like `airflow-connections-snowflake-prod` (note: KV doesn't allow `/`; use `-` separator).

Managed Identity / workload identity for KV access.

---

## 8. Vault backend

```ini
backend = airflow.providers.hashicorp.secrets.vault.VaultBackend
backend_kwargs = {
  "url":                 "https://vault.corp.example:8200",
  "auth_type":           "kubernetes",
  "kubernetes_role":     "airflow",
  "connections_path":    "airflow/connections",
  "variables_path":      "airflow/variables",
  "mount_point":         "secret"
}
```

Vault K8s auth: the pod's projected SA token authenticates to Vault; Vault returns secrets. Supports dynamic secrets (Vault generates a new DB password per request).

---

## 9. Dynamic secrets — the Vault advantage

```hcl
# Vault config
path "database/creds/airflow-snowflake" {
  capabilities = ["read"]
}
```

Vault generates a fresh Snowflake password for each read; password expires after lease. Airflow scheduler/worker reads at task start, uses for the connection lifetime.

For regulated finance: dynamic secrets eliminate static creds. The bar.

---

## 10. Connection lookup precedence (worth memorizing)

```
For conn_id="snowflake_prod":

1. env var: AIRFLOW_CONN_SNOWFLAKE_PROD=snowflake://user:pass@host/db?warehouse=X
   → if set, this WINS

2. Secrets Backend lookup at connections_prefix + "snowflake_prod"
   → returns Connection if found

3. Metadata DB SELECT * FROM connection WHERE conn_id='snowflake_prod'
   → final fallback
```

In MWAA / Composer / Astronomer: env-var setup happens via their UI; production secrets always in backend.

---

## 11. Anti-patterns

| Anti-pattern | Why bad | Fix |
|---|---|---|
| Hardcoded creds in DAG | Image leak, git leak | Connection + Secrets Backend |
| Plaintext password in Connection | Encrypted at rest, but visible to anyone with DB access | Secrets Backend |
| Putting tokens in Variables | Audited less than Connections | Connections or Secrets Backend |
| Same conn_id across envs | Dev creds == prod creds | Env-specific conn_ids |
| Long-lived static creds in Snowflake | Insider risk + rotation pain | Dynamic creds via Vault |

---

## 12. Provider Lookup Pattern

You can extend lookup with patterns:

```ini
backend_kwargs = {
  "connections_lookup_pattern": "^airflow_.*",
  "variables_lookup_pattern":   "^secret_.*"
}
```

Only call Secrets Backend for matching IDs; non-matching fall through to metadata DB. Cuts unnecessary API calls.

---

## Sanity check

1. The Fernet key encrypts what, and what's lost if the key is lost?
2. Lookup order for a `conn_id` — list the three sources in precedence.
3. Why is Vault's "dynamic secrets" pattern superior to a rotated static secret?
4. Azure Key Vault has a quirk that requires a config-level workaround. What is it?
5. What permission does the AWS Secrets Manager backend need from the Airflow IAM role?
6. Why is putting secrets in Variables an anti-pattern even though Variables are encrypted-at-rest?

---

## Sources

- [Secrets Backend overview](https://airflow.apache.org/docs/apache-airflow/stable/security/secrets/secrets-backend/index.html)
- [AWS Secrets Manager Backend](https://airflow.apache.org/docs/apache-airflow-providers-amazon/stable/secrets-backends/aws-secrets-manager.html)
- [GCP Secret Manager Backend](https://airflow.apache.org/docs/apache-airflow-providers-google/stable/secrets-backends/google-cloud-secret-manager-backend.html)
- [Azure Key Vault Backend](https://airflow.apache.org/docs/apache-airflow-providers-microsoft-azure/stable/secrets-backends/azure-key-vault.html)
- [Vault Backend](https://airflow.apache.org/docs/apache-airflow-providers-hashicorp/stable/secrets-backends/hashicorp-vault.html)
- [Connections concept](https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/connections.html)

→ Next: [09 — **Securing Airflow**](09_securing_airflow.md)


\newpage

# 09 — Securing Airflow: RBAC, Auth Manager, FAB, OIDC/SAML/LDAP, audit logs, the DAG-author=admin problem

## Why this module exists

Airflow's security story is **not great by default**. This module is the honest "how regulated shops actually control Airflow" guide.

---

## 1. The structural problem: DAG code = arbitrary execution

Airflow DAGs are Python files. The scheduler imports them. Anyone with commit access to the DAG folder runs arbitrary Python in the scheduler process context. **DAG authors are effectively cluster admins.**

Mitigations (none perfect for 2.x):
- PR review every DAG change.
- CI lints for `eval`, `exec`, `subprocess.run(...)` at top level.
- Run scheduler with restricted IAM / SA permissions (so RCE in scheduler is bounded).
- Use **KubernetesExecutor** so tasks run in isolated Pods with their own SAs.
- **Airflow 3.0 Task SDK** finally isolates task execution from the scheduler — module 30.

For multi-team Airflow: each team should have **its own DAG folder + its own scheduler/worker pool** unless 3.0's Task SDK is in play.

---

## 2. Auth Manager — the 2.8+ abstraction

Auth Manager is an extension point for authentication and authorization. Default is **FAB Auth Manager** (Flask-AppBuilder). Alternative: **AWS Auth Manager** (uses IAM).

```ini
[core]
auth_manager = airflow.providers.fab.auth_manager.fab_auth_manager.FabAuthManager
```

In 3.0 the abstraction is more flexible.

---

## 3. FAB Auth Manager — the default

[Flask-AppBuilder](https://flask-appbuilder.readthedocs.io/) ships with Airflow. Provides:

- **Built-in roles**: Admin, Op, User, Viewer, Public.
- **Custom roles**: define + assign.
- **Per-DAG access control**: `dag.access_control = {"team_a": {"can_read", "can_edit"}}`.
- **Auth backends**: password (DB), LDAP, OAuth (Google/Okta/Azure AD/GitHub), Kerberos, SAML.

### 3.1 Configure OIDC (e.g., Okta)

In `webserver_config.py`:

```python
from flask_appbuilder.security.manager import AUTH_OAUTH
AUTH_TYPE = AUTH_OAUTH
AUTH_USER_REGISTRATION = True
AUTH_USER_REGISTRATION_ROLE = "Viewer"
AUTH_ROLES_MAPPING = {
    "Airflow-Admins":   ["Admin"],
    "Data-Engineers":   ["Op"],
    "ML-Engineers":     ["User"],
}
AUTH_ROLES_SYNC_AT_LOGIN = True
OAUTH_PROVIDERS = [{
    "name": "okta",
    "icon": "fa-circle-o",
    "token_key": "access_token",
    "remote_app": {
        "client_id":     "<>",
        "client_secret": "<>",
        "api_base_url":  "https://<tenant>.okta.com/oauth2/default/v1/",
        "client_kwargs": {"scope": "openid profile email groups"},
        "access_token_url": "https://<tenant>.okta.com/oauth2/default/v1/token",
        "authorize_url":    "https://<tenant>.okta.com/oauth2/default/v1/authorize",
    },
}]
```

User logs in via Okta; groups claim maps to Airflow roles.

---

## 4. Per-DAG access control

```python
@dag(
    access_control={
        "team-finance": {"can_read"},
        "team-data-eng": {"can_read", "can_edit", "can_delete"},
    },
    ...
)
def finance_etl():
    ...
```

Users in `team-finance` see this DAG (read-only); users in `team-data-eng` can pause/trigger/edit. Useful for multi-tenant.

---

## 5. The webserver_secret_key

```ini
[webserver]
secret_key = <random-32-bytes>
```

Signs session cookies. **MUST be identical across webserver replicas.** Generate via `openssl rand -hex 32`. Store in Secrets Backend; mount as env var.

---

## 6. `expose_config = False`

```ini
[webserver]
expose_config = False
```

Default in modern Airflow. Prevents UI from rendering `airflow.cfg` contents (which may include secrets, DB URLs).

---

## 7. API authentication

Airflow REST API (`/api/v1/`) auth options:

- Basic auth (DB-backed).
- JWT (2.9+).
- Kerberos.
- OAuth (via FAB session).

For machine clients: JWT or basic auth with a service-account user. Behind an API gateway / WAF.

---

## 8. Audit logging

Airflow logs UI/API actions to its `log` table:

- DAG triggered, paused, deleted.
- User login/logout.
- Variable / Connection added/changed/deleted.
- Pool changes.

Forward to SIEM:

```python
# Custom log handler that ships to Splunk/Datadog
```

Or use the OpenTelemetry log support (2.9+).

Tasks log to the configured log handler (S3, GCS, ES, etc.) — separate from audit log.

---

## 9. The scheduler's IAM/SA permissions

Scheduler does:
- Read/write metadata DB.
- Read DAG storage.
- Talk to Triggerer / workers via DB.
- Push logs to remote backend.
- Fetch secrets from Secrets Backend.

**Scheduler does NOT need access to actual data systems** (Snowflake, S3 buckets, Databricks). Those are accessed by tasks (via task IAM / SA in K8sExecutor).

Lock down scheduler IAM/SA accordingly. If scheduler is RCE'd, blast radius is `airflow/*` secrets and DAG storage, not your data warehouse.

---

## 10. Webserver hardening

- Behind LB only (no public IP).
- TLS terminated at LB; redirect HTTP→HTTPS.
- `secure: True` cookies; `SameSite=Strict`; `HttpOnly`.
- CSP headers via reverse proxy.
- mTLS if internal-only.
- OIDC auth (no DB passwords).
- Rate limit per IP.
- Health-check endpoint exempt from auth (for K8s probes).

For regulated finance: webserver behind oauth2-proxy + WAF + private network.

---

## 11. Known CVEs

- **CVE-2020-11978** — Example DAG `example_trigger_target_dag` RCE; `load_examples = False` in any non-dev env. Mandatory.
- **CVE-2022-24288** — improper neutralization of params in some operators (BashOperator).
- **Various 2023-2024 advisories** — usually patched within weeks. Subscribe to `security@airflow.apache.org`.

LTS lines: Airflow 2.6 LTS (security patches without features). Stay on a supported version; 2.10 is current at 2026-05-21.

---

## 12. The regulated-finance hardening checklist

- [ ] `load_examples = False`.
- [ ] `expose_config = False`.
- [ ] `secret_key` and `fernet_key` from Secrets Backend, distinct per env.
- [ ] OIDC auth (no password DB).
- [ ] OIDC groups → Airflow roles mapping.
- [ ] Per-DAG `access_control` for sensitive DAGs.
- [ ] Secrets Backend configured (AWS/GCP/Azure/Vault).
- [ ] Webserver behind oauth2-proxy + WAF + private network.
- [ ] mTLS for API.
- [ ] Audit log to SIEM.
- [ ] Task logs to KMS-encrypted bucket.
- [ ] Scheduler/worker IAM scoped to Secrets Backend + DAG storage only.
- [ ] KubernetesExecutor with per-task SA (IRSA / WIF / Entra Workload ID).
- [ ] PSA-restricted on the K8s namespace.
- [ ] Kyverno admission for image signing + resource limits.
- [ ] CI lints: no top-level `import` of heavyweights; no `eval`/`exec`.
- [ ] PR review for every DAG change with security-side reviewer for high-privilege DAGs.

---

## Sanity check

1. The "DAG authors == cluster admins" problem — why does it exist in Airflow 2.x?
2. What does the `secret_key` sign, and why must it be identical across webservers?
3. FAB Auth Manager + OIDC + group mapping — describe the login flow.
4. Why does `expose_config = False` matter even if you trust your team?
5. Scheduler IAM should NOT include direct access to what data systems?
6. KubernetesExecutor + per-task SA addresses the DAG-author-RCE problem how?

---

## Sources

- [Airflow Security](https://airflow.apache.org/docs/apache-airflow/stable/security/index.html)
- [Auth Manager](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/auth-manager/index.html)
- [Flask-AppBuilder OAuth](https://flask-appbuilder.readthedocs.io/en/latest/security.html#oauth-authentication)
- [Apache Airflow Security advisories](https://airflow.apache.org/docs/apache-airflow/stable/security/index.html#security-advisories)
- [NVD: CVE-2020-11978](https://nvd.nist.gov/vuln/detail/CVE-2020-11978)

→ Next: [10 — Networking Airflow](10_networking.md)


\newpage

# 10 — Networking Airflow: private webserver, mTLS, VPC endpoints, egress controls

## Why this module exists

Airflow's network surface is wider than most realize — webserver, scheduler, triggerer, workers, metadata DB, plus all the systems tasks talk to. Each is a control point.

---

## 1. The components' network roles

| Component | Inbound | Outbound |
|---|---|---|
| Webserver | UI clients (humans), API clients | Metadata DB, Secrets Backend |
| Scheduler | (none from outside) | Metadata DB, Secrets Backend, DAG storage, executor (Celery broker / K8s API) |
| Triggerer | (none from outside) | Metadata DB, External APIs being polled |
| Workers | (none) | All data sources (very wide!) |
| Metadata DB | Webserver, Scheduler, Triggerer, Workers | (storage only) |

**Workers have the widest egress surface** because they need to talk to Snowflake, Databricks, S3, EMR, custom APIs, Slack, etc. This is the blast radius if a worker is compromised.

---

## 2. Webserver: private deployment

Production Airflow webserver should:

- Have no public IP.
- Be behind an internal LB (AWS ALB, GCP Internal LB, Azure App Gateway).
- TLS terminated at the LB.
- OIDC auth (via oauth2-proxy if FAB-OIDC is insufficient).
- WAF in front for L7 protection.
- API rate limited.

For MWAA `PRIVATE_ONLY` mode: webserver only reachable via VPC. For Composer 3: Private IP environments with PSC. For Astro Hybrid: data-plane in customer VPC.

---

## 3. Scheduler / Worker egress

Workers need outbound:

- Cloud APIs (S3, KMS, Secrets Manager) → **VPC endpoints** (AWS) / **Private Google Access** (GCP) / **Private endpoints** (Azure).
- Data systems (Snowflake, Databricks) → **PrivateLink** (Snowflake, Databricks).
- Internal services (custom APIs) → VPC routing.

For a regulated shop: **default-deny outbound; allowlist per destination.**

```hcl
# AWS NSG / SG for worker
egress {
  from_port = 443
  to_port = 443
  protocol = "tcp"
  prefix_list_ids = [data.aws_prefix_list.s3.id]  # S3
}
egress {
  from_port = 443
  to_port = 443
  protocol = "tcp"
  cidr_blocks = ["10.50.0.0/16"]                  # internal services
}
```

---

## 4. Snowflake PrivateLink

For Snowflake from Airflow workers, **don't use the public Snowflake endpoint**. Configure Snowflake PrivateLink:

```
worker (VPC) → PrivateLink endpoint → Snowflake
```

Snowflake conn host: `myorg.privatelink.snowflakecomputing.com`. No internet egress for queries.

Same pattern for Databricks (PrivateLink), Confluent Cloud, MongoDB Atlas, etc.

---

## 5. mTLS

Webserver: TLS in (from clients). For mTLS within Airflow components: typically not needed for K8s-internal (service mesh handles east-west). For external API calls, mTLS at the boundary if the service requires it.

For Airflow REST API + machine clients: TLS + JWT auth; mTLS optional via API gateway.

---

## 6. Metadata DB networking

The metadata DB is the single most-sensitive backing store. Protect:

- Only reachable from scheduler/webserver/triggerer/worker subnets.
- TLS-enabled (Postgres `sslmode=require`).
- IAM auth where supported (RDS Postgres / Aurora IAM auth) — eliminates static DB password.
- Audit logging to CloudWatch / Cloud Logging / Log Analytics.
- Encrypted at rest with CMK.

For MWAA: AWS manages the DB; it's already private. For Composer: same. For self-host: own this.

---

## 7. DAG storage networking

Depending on deployment:

- **MWAA**: S3 bucket; access via S3 Gateway Endpoint.
- **Composer**: GCS bucket; Private Google Access.
- **Azure Managed Airflow**: git-sync from Azure DevOps / GitHub.
- **Self-host with git-sync**: outbound to git provider (allowlist `github.com` / your GitLab).
- **Self-host with image-baked**: pulls image; same path as image pulls.

For air-gapped self-host: internal git mirror; internal registry.

---

## 8. KubernetesExecutor — pod-level network

In K8sExecutor, each task pod has:

- Its own ServiceAccount (with IRSA / WIF / Entra MI).
- Its own NetworkPolicy (potentially).
- Pod-level SG (AWS).
- Mesh-injected sidecar (if Istio/Linkerd present).

This is **per-task network isolation**. You can have different DAGs with different egress allowlists. The strongest model.

---

## 9. The "Airflow on a private network" pattern

```
┌─────────────────────────────────────────────────────────────────┐
│ Private VPC (regulated zone)                                    │
│                                                                  │
│  ┌──────────────┐    ┌─────────────────┐                         │
│  │ Internal ALB │    │ EKS cluster     │                         │
│  │ (with WAF)   │    │ (private API)   │                         │
│  └──────┬───────┘    │                 │                         │
│         │            │  Airflow:       │                         │
│   ┌─────▼──────┐     │   - Webserver   │                         │
│   │ Webserver  │ ◀───┼─────────────────┘                         │
│   │ (FAB+OIDC) │     │   - Scheduler   │                         │
│   └────────────┘     │   - Triggerer   │                         │
│                      │   - Workers     │                         │
│                      └────────┬────────┘                         │
│                               │                                  │
│         ┌─────────────────────┼─────────────────────┐            │
│         │                     │                     │            │
│  ┌──────▼──────┐  ┌───────────▼─────────┐  ┌────────▼─────┐      │
│  │ RDS Postgres│  │ S3 (Gateway EP)    │  │ Snowflake    │      │
│  │ (TLS, CMK)  │  │ S3 / EFS / FSx     │  │ PrivateLink  │      │
│  └─────────────┘  │ Secrets Mgr (IFC)  │  └──────────────┘      │
│                   │ KMS (IFC)          │                         │
│                   └────────────────────┘                         │
└──────────────────────────────────────────────────────────────────┘
       ↑
       │ (only via Bastion / Zero-Trust gateway)
   Human admin
```

No internet egress. Human access via Bastion or zero-trust gateway (Cloudflare Access, Zscaler, AWS Verified Access).

---

## 10. Egress filtering for the worker — the Cloud Custodian–style policy

A common policy enforced by network firewall + IaC linting:

- Workers can egress to: KMS, Secrets Manager, S3 (specific prefixes), CloudWatch Logs, RDS (own DB), Snowflake (specific account), Databricks (own workspace).
- Workers CANNOT egress to: `0.0.0.0/0`, `169.254.169.254` (IMDS — task IAM role replaces), other accounts' resources, public DockerHub.

For a regulated FinOps + security shop: Falco rule + Cloud Custodian rule, both enforced.

---

## Sanity check

1. The worker is the widest egress surface. Why?
2. Snowflake PrivateLink — what does it replace and why?
3. Metadata DB networking — what's the lockdown checklist?
4. K8sExecutor + per-task NetworkPolicy — what does this give you that Celery doesn't?
5. Why is `169.254.169.254` blocked from worker pods?

---

## Sources

- [Snowflake PrivateLink](https://docs.snowflake.com/en/user-guide/private-snowflake-service)
- [Databricks PrivateLink](https://docs.databricks.com/security/network/classic/privatelink.html)
- [MWAA networking](https://docs.aws.amazon.com/mwaa/latest/userguide/networking-about.html)
- [Composer 3 networking](https://cloud.google.com/composer/docs/composer-3/configure-private-ip)

→ Next: [11 — XCom & data passing](11_xcom_data_passing.md)


\newpage

# 11 — XCom & data passing: limits, custom XCom backend, anti-patterns

## Why this module exists

XCom is for **small** task-to-task data. Use it wrong and you DDoS your metadata DB.

---

## 1. XCom mechanics

`@task` return values → stored in metadata DB `xcom` table → next task reads.

```python
@task
def a() -> dict:
    return {"count": 1234, "checksum": "abc"}

@task
def b(stats: dict):
    log.info(stats["count"])

b(a())
```

Under the hood: `a` writes `{"count":1234,"checksum":"abc"}` to xcom; `b` reads it via the `task_instance.xcom_pull()` API.

Default backend: metadata DB, serialized as JSON.

---

## 2. Size limits

| Backend | Soft warning | Practical max |
|---|---|---|
| Postgres `bytea` | 48 KB | ~1 GB (but DB-slow) |
| MySQL `LONGBLOB` | 48 KB | ~4 GB (very slow) |
| SQLite | 48 KB | ~1 GB |

**Production target: keep XCom < 1 MB. Ideal: < 100 KB.**

Logs warn at 48 KB; `enable_xcom_pickling=False` (default) blocks pickle.

---

## 3. Custom XCom Backend

For data > 100 KB, write a custom backend that stages data to object storage:

```python
# my_xcom.py
from typing import Any
import json, uuid
from airflow.models.xcom import BaseXCom
import boto3

class S3XComBackend(BaseXCom):
    PREFIX = "xcom://"
    BUCKET = "myorg-airflow-xcom"

    @staticmethod
    def serialize_value(value, **kwargs) -> str:
        # Small values: native serialization
        if isinstance(value, (int, float, str, bool)) or (isinstance(value, dict) and len(json.dumps(value)) < 1024):
            return BaseXCom.serialize_value(value)
        # Large: stage to S3
        key = f"xcom/{uuid.uuid4()}.json"
        boto3.client("s3").put_object(
            Bucket=S3XComBackend.BUCKET, Key=key,
            Body=json.dumps(value).encode(),
            ServerSideEncryption="aws:kms",
        )
        return BaseXCom.serialize_value(f"{S3XComBackend.PREFIX}{key}")

    @staticmethod
    def deserialize_value(result) -> Any:
        v = BaseXCom.deserialize_value(result)
        if isinstance(v, str) and v.startswith(S3XComBackend.PREFIX):
            key = v[len(S3XComBackend.PREFIX):]
            obj = boto3.client("s3").get_object(Bucket=S3XComBackend.BUCKET, Key=key)
            return json.loads(obj["Body"].read())
        return v
```

Configure:

```ini
[core]
xcom_backend = my_xcom.S3XComBackend
```

Now any return value larger than a threshold is staged to S3 transparently; smaller stays in metadata DB. Apps don't change.

Built-in alternatives:
- **Airflow's S3 XCom backend** in `apache-airflow-providers-amazon` (since 2.7).
- **GCS XCom backend** in providers-google.
- **Azure Blob XCom backend** in providers-microsoft-azure.

For Airflow 2.8+ the Object Storage abstraction makes this simpler.

---

## 4. Anti-patterns

| Anti-pattern | Why bad | Fix |
|---|---|---|
| Returning a Pandas DataFrame | Blows up metadata DB | Write to S3/Parquet; return path |
| Returning a NumPy array | Same | Write to S3; return path |
| Returning a Pickled custom class | Security + version-skew risk | JSON-serializable types only |
| `xcom_push` of secrets | Logged + visible in UI | Use Secrets Backend |
| Chaining many tasks with growing XCom payloads | Each task duplicates the data | Stage to S3 once; downstream tasks read from path |
| XCom as a queue | Wrong primitive; use Pool or message queue | Pool / external queue |

---

## 5. The data-flow design pattern

For a pipeline processing 100K records → 10K aggregations → final report:

**Anti-pattern**:
```python
records = extract()       # 100K rows in XCom — disaster
agg     = aggregate(records)
report  = build(agg)
```

**Right pattern**:
```python
@task
def extract() -> str:
    # write to S3, return path
    path = f"s3://myorg-pipelines/{{ run_id }}/records.parquet"
    write_parquet(records, path)
    return path

@task
def aggregate(input_path: str) -> str:
    # read from S3, write to S3
    df = pd.read_parquet(input_path)
    out_path = f"s3://myorg-pipelines/{{ run_id }}/agg.parquet"
    df.groupby(...).agg(...).to_parquet(out_path)
    return out_path

@task
def report(agg_path: str): ...
```

XCom carries S3 paths (a few hundred bytes). Data lives in S3. Scales.

---

## 6. The Object Storage abstraction (2.8+)

Airflow now ships a portable `ObjectStoragePath`:

```python
from airflow.io.path import ObjectStoragePath

base = ObjectStoragePath("s3://myorg-pipelines/", conn_id="aws_default")

@task
def write(data):
    path = base / "{{ run_id }}" / "records.parquet"
    with path.open("wb") as f:
        f.write(serialize(data))
    return str(path)
```

Works with `s3://`, `gs://`, `abfs://` (Azure Data Lake Gen2), `file://`. Avoids hard-coupling to one cloud provider in DAG code.

---

## 7. Datasets vs XCom

For larger inter-DAG data flow, **Datasets are the right primitive** (module 06). XCom is for within-a-DAG-run task communication; Datasets are for cross-DAG dataflow with built-in triggering.

---

## Sanity check

1. The 48 KB threshold is what — a hard limit or a warning?
2. Why does returning a Pandas DataFrame via XCom hurt?
3. Custom XCom backend — what's the canonical pattern for "small values inline, large values to object storage"?
4. Object Storage abstraction (2.8+) — what does it give you over hard-coded S3 SDK?
5. Datasets vs XCom — when do you reach for each?

---

## Sources

- [XCom docs](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/xcoms.html)
- [Custom XCom Backends](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/xcoms.html#custom-backends)
- [Object Storage](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/objectstorage.html)
- [Airflow Improvement Proposal AIP-58 (Object Storage)](https://cwiki.apache.org/confluence/display/AIRFLOW/AIP-58+Airflow+Object+Storage)

→ Next: [12 — Data-flow design](12_data_flow_design.md)


\newpage

# 12 — Data-flow design: idempotency, hash-based skip, sensors→triggers, dataset-driven scheduling

## Why this module exists

Anyone can write a DAG that works once. The seniors write DAGs that survive 3 years of partial failures, schema changes, late data, and team turnover. This module is the patterns.

---

## 1. Idempotency — the foundational rule

A task is **idempotent** if running it twice produces the same final state as running it once.

```python
# NON-idempotent — appends rows
INSERT INTO sales VALUES (...)

# Idempotent — overwrites rows for the partition
DELETE FROM sales WHERE ds = '{{ ds }}';
INSERT INTO sales VALUES (...);

# Or MERGE
MERGE INTO sales s USING staging.sales st ON s.id = st.id ...
```

If a DAG run fails midway, retry must be safe. Idempotent SQL is how.

For S3/GCS writes: use deterministic paths (`s3://bucket/{{ run_id }}/file.parquet`). Overwrite, don't append. Or use Iceberg / Delta tables (ACID).

---

## 2. Hash-based skip

When you can detect "this work was already done":

```python
@task
def maybe_extract(source_url: str) -> str:
    source_hash = sha256(get_metadata(source_url))
    state_key = f"extract_state/{source_hash}"
    if s3.head_object(Bucket="state", Key=state_key, IfMatch="*"):
        log.info(f"Already extracted {source_hash}; skip")
        return f"s3://output/{source_hash}.parquet"
    # do the work
    ...
```

For sources that may not have changed: skip cleanly. Saves money and time.

---

## 3. Catchup vs Backfill discipline

- **Catchup on first deploy**: `catchup=False`. Always.
- **Targeted backfill**: `airflow dags backfill -s ... -e ...` with `--pool small_pool` to throttle.
- **Backfill while live**: be careful — the live DAG may also be running for "today." `max_active_runs=1` prevents overlap.

For idempotent DAGs, backfill is safe. For non-idempotent: backfill creates duplicates. Idempotency is what enables casual backfill.

---

## 4. Late data handling

"Data for 2026-05-20 arrived at 2026-05-22 06:00." Strategies:

- **Reactive sensors**: a DAG waits with `deferrable=True` + a deadline; if data arrives, runs.
- **Watermark + backfill**: scheduled DAG processes "high watermark + 1 day" only; periodic backfill catches late data.
- **Datasets**: producer DAG signals dataset update; consumer runs reactively.

For real-time-ish: Datasets. For batch with late tolerance: reactive sensors + retry. Document the SLA.

---

## 5. Schema evolution

Pipelines break when schemas change. Patterns:

- **Schema-on-read** in the warehouse (Snowflake, Iceberg, Delta) — tolerant to additions.
- **Explicit schema validation** in Airflow tasks (Great Expectations / dbt tests).
- **Data contracts** — producer commits to a schema; CI enforces; breaking change requires version bump.

For ML pipelines: features dropping or appearing silently is the #1 source of model drift. Validate at extraction time.

---

## 6. Retries and exponential backoff

```python
default_args = {
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(hours=1),
}
```

For flaky external APIs / transient errors: retries soak it up. For deterministic logic failures: retries are theater (and waste).

Set retries per task class:
- DB writes: 3 retries with exponential backoff.
- External API calls: 5 retries with backoff.
- ML training: 0 retries (let observability handle re-launch).

---

## 7. SLA / Deadlines (3.0+)

In 2.x: `sla` field per task + `sla_miss_callback`. **Deprecated** in 3.0.

In 3.0: **Deadlines** — declarative time-from-trigger constraints with structured outcomes.

```python
@dag(deadline_alert=timedelta(hours=2), ...)
```

For ETL: SLA = "by 06:00 next day." Missed SLA → PagerDuty.

---

## 8. Dataset-driven scheduling — the modern dataflow

Already covered in module 06. Recap as a design principle:

- Replace `ExternalTaskSensor` chains with Datasets.
- Producers declare `outlets=[ds]`.
- Consumers declare `schedule=[ds_a, ds_b]`.
- Scheduler triggers consumers when datasets update.

For complex data lineage: this is how you keep dependencies tractable.

---

## 9. Common data-flow pitfalls

| Pitfall | Fix |
|---|---|
| Non-idempotent writes | MERGE / partition-overwrite / object-store overwrite |
| Hardcoded date in SQL | Use `{{ ds }}` templating |
| Re-extracting unchanged data | Hash + skip |
| Catchup avalanche | `catchup=False` |
| Cron coordination between DAGs | Datasets |
| Tight timeout on a flaky API | Retries with exponential backoff |
| No SLA on critical DAG | Deadline + alert |
| Backfill creates dupes | Make tasks idempotent |
| XCom of large data | Object Storage; return paths |
| DAG run takes 8 hours, scheduler thinks it's stuck | `execution_timeout` per task; not the whole DAG |

---

## 10. The architect-grade DAG review checklist

Before merging:

- [ ] Idempotent tasks (state writes use MERGE / overwrite).
- [ ] `catchup=False`.
- [ ] `max_active_runs` appropriate.
- [ ] Retries + exponential backoff.
- [ ] `execution_timeout` per task.
- [ ] No top-level expensive code.
- [ ] Variables / Connections via Secrets Backend.
- [ ] XCom payloads small; object-storage offload for large.
- [ ] Datasets used where cross-DAG triggering is needed.
- [ ] OpenLineage extractors emit (most operators do automatically).
- [ ] Tests in CI (pytest with `dag.test()` or `dag_maker`).
- [ ] Owner + alert email set.
- [ ] Documentation in DAG docstring + `dag.doc_md`.

---

## Sanity check

1. Idempotency at SQL level — `INSERT` vs `MERGE`. Why is `MERGE` idempotent?
2. Hash-based skip — what's the trade-off vs always re-extracting?
3. Late data — name two patterns to handle it.
4. SLA in 2.x is replaced by what in 3.0?
5. Why does Dataset-driven scheduling beat ExternalTaskSensor for cross-DAG dataflow?

---

## Sources

- [Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html)
- [Datasets](https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/datasets.html)
- [Dynamic Task Mapping](https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/dynamic-task-mapping.html)
- [Airflow 3.0 Deadlines AIP](https://cwiki.apache.org/confluence/display/AIRFLOW/AIP-72+Deadlines)

→ Next: [13 — Lineage with OpenLineage](13_lineage_openlineage.md)


\newpage

# 13 — Lineage with OpenLineage: Marquez, Atlan/DataHub, Unity Catalog interop

## Why this module exists

For regulated finance, "where did this number come from" is a compliance question, not a curiosity. OpenLineage is the standard for capturing it from Airflow.

---

## 1. OpenLineage in one paragraph

OpenLineage is an **open standard** (LF AI & Data) for capturing data lineage events. Each event names:

- A **job** (a pipeline / task).
- One or more **input datasets**.
- One or more **output datasets**.
- A **run** (instance of the job execution).
- **Facets** — typed metadata (schema, SQL, run metrics).

Tools EMIT OpenLineage events; backends INGEST them. Decoupled.

---

## 2. The Airflow + OpenLineage integration

`apache-airflow-providers-openlineage` (2.7+). Once installed and configured, **lineage is automatic** for many operators:

- SQL operators (Snowflake, BigQuery, Redshift, Postgres) — extract `INSERT INTO ... SELECT FROM ...` to lineage.
- S3, GCS, Blob operators — file inputs/outputs.
- Spark / Databricks / EMR / Dataproc operators — job + dataset lineage.
- Custom operators — implement `get_openlineage_facets_on_start` / `_on_complete`.

```python
# airflow.cfg
[openlineage]
transport = '{"type": "http", "url": "https://marquez.internal/api/v1/lineage"}'
namespace = "airflow-prod"
```

Done. Events flow.

---

## 3. Marquez — the reference backend

[Marquez](https://marquezproject.ai/) (LF AI & Data Sandbox) ingests OpenLineage events, stores in Postgres, exposes UI + API.

Visualization: graph of datasets + jobs; per-run details; schema history.

For small-to-medium teams: Marquez is great. Self-hostable via Helm chart.

---

## 4. Commercial OpenLineage consumers

| Tool | Notes |
|---|---|
| **DataHub** (Acryl) | LinkedIn open source + commercial; broad catalog + lineage |
| **Atlan** | Modern data catalog; OpenLineage native |
| **Collibra** | Enterprise data governance; OpenLineage support added 2023 |
| **Alation** | Enterprise catalog; OpenLineage support |
| **OpenMetadata** | OSS competitor to DataHub |
| **Amundsen** | LinkedIn-Lyft OSS catalog (predates OpenLineage; bridge exists) |

For Capital One–style regulated finance: catalog choice often Collibra (legacy enterprise) or DataHub (modern). OpenLineage feeds both.

---

## 5. Unity Catalog + OpenLineage

Databricks Unity Catalog has **native lineage** for Databricks-internal queries (notebooks, jobs, SQL warehouses). For end-to-end lineage that spans Airflow → Databricks → Snowflake:

- Airflow emits OpenLineage.
- Databricks emits Unity Catalog lineage natively + OpenLineage via the Spark Listener.
- Snowflake emits via Object Lineage / Account Usage views.
- A catalog (DataHub, Collibra) merges sources.

Unity Catalog → OpenLineage export was GA in 2024.

---

## 6. AWS Glue Data Catalog + Lake Formation lineage

AWS DataZone (now AWS SageMaker Catalog) added lineage in 2024. Glue ETL jobs emit lineage. Combined with OpenLineage from Airflow, end-to-end on AWS works.

---

## 7. The data-contract angle

OpenLineage + a data catalog tells you **what** happened. Data contracts add **expectations**:

- Producer commits: schema, freshness, SLA.
- Consumer asserts: schema match, freshness check, null rate.
- Catalog enforces: schema-change PRs require consumer ack.

Tools: **Soda**, **Great Expectations**, **dbt tests**, **Acryl DataHub Contracts**, **Snowflake Data Contracts**.

For ML: feature contracts are critical — silent schema changes destabilize models.

---

## 8. Operator coverage status (2026)

Most major operators have OpenLineage extractors. Coverage gaps where you'd write your own:

- Custom REST API calls (PythonOperator with `requests`).
- Internal-only data systems.
- Pre-2020 operators that pre-date the OL effort.

For PythonOperator: implement extractors via the OL Python library:

```python
from openlineage.airflow.utils import DagUtils

@task
def my_task():
    # ... do stuff ...
    DagUtils.emit_lineage(
        input_datasets=[Dataset(namespace="s3://myorg-data", name="input.parquet")],
        output_datasets=[Dataset(namespace="snowflake://prod.analytics", name="sales_curated")],
    )
```

---

## 9. rubicon-ml + OpenLineage at Capital One

Capital One's rubicon-ml (Topic 04 reference) is an experiment-tracking tool that focuses on lineage + auditability for ML training artifacts. It's complementary to OpenLineage:

- **OpenLineage**: dataset + job graph at the data layer.
- **rubicon-ml**: experiment artifacts (model + metrics + code git SHA) at the ML layer.

Together they answer: "this model in production was trained on this dataset version using this code commit." For SR 11-7 model governance, both halves are required.

---

## 10. The lineage stack for a regulated shop

```
Airflow → OpenLineage → DataHub (or Collibra)
Spark / Databricks → OpenLineage + Unity Catalog → DataHub
Snowflake → ACCOUNT_USAGE.OBJECT_DEPENDENCIES + OpenLineage → DataHub
S3 + Glue → AWS DataZone → DataHub
ML training → MLflow + rubicon-ml → DataHub (custom emitter)
```

Single pane in DataHub. Drill from "PII column appears in this dashboard" to "Airflow DAG that loaded it" to "S3 object it came from."

---

## Sanity check

1. OpenLineage is a standard. Marquez is what?
2. Most Airflow operators emit OpenLineage automatically. Which would you need to instrument manually?
3. Unity Catalog + OpenLineage — what's the bridging story for cross-system lineage?
4. Data contracts answer what question that OpenLineage alone does not?
5. Where does rubicon-ml fit alongside OpenLineage at Capital One?

---

## Sources

- [OpenLineage spec](https://openlineage.io/docs/)
- [Marquez](https://marquezproject.ai/)
- [Airflow OpenLineage provider](https://airflow.apache.org/docs/apache-airflow-providers-openlineage/stable/index.html)
- [DataHub](https://datahubproject.io/)
- [Databricks Unity Catalog lineage](https://docs.databricks.com/data-governance/unity-catalog/data-lineage.html)
- [rubicon-ml](https://github.com/capitalone/rubicon-ml)
- [SR 11-7 (Federal Reserve model risk guidance)](https://www.federalreserve.gov/supervisionreg/srletters/sr1107.htm)

→ Next: [14 — Observability](14_observability.md)


\newpage

# 14 — Observability: StatsD, Prometheus, OpenTelemetry, log handlers per cloud

## Why this module exists

Airflow is hard to operate without observability. This module covers the stack and the alert thresholds that catch real problems.

---

## 1. The metrics signal

Airflow emits ~50 metrics via **StatsD protocol** by default. Common ones:

| Metric | Meaning | Alert threshold |
|---|---|---|
| `scheduler.heartbeat` | Scheduler heartbeat count | Missing for > 60s = scheduler dead |
| `dagbag.import_errors` | DAG parse failures | > 0 = at least one DAG broken |
| `dag_processing.last_runtime.{dag_id}` | DAG parse time | > 30s for any single DAG |
| `scheduler.tasks.executable` | Tasks ready to run | Stuck high = capacity issue |
| `executor.queued_tasks` | Tasks in queue | Stuck high = worker capacity |
| `executor.running_tasks` | Tasks currently executing | Below max = healthy |
| `ti.start.{dag_id}.{task_id}` | Task instance start counter | — |
| `ti.duration.{dag_id}.{task_id}` | Task duration | p99 deviation = regression |
| `pool.open_slots.{pool}` | Available slots in pool | Stuck at 0 = pool exhausted |
| `dag_run.duration.success.{dag_id}` | DAG run duration | p99 deviation = drift |

Ship to Prometheus via `statsd_exporter` or use Datadog/New Relic agent. Most managed offerings (MWAA, Composer) ship these to CloudWatch/Cloud Monitoring directly.

---

## 2. OpenTelemetry (GA 2.9+)

```ini
[traces]
otel_on = True
otel_host = otel-collector
otel_port = 4318
otel_service = airflow

[metrics]
otel_on = True
otel_host = otel-collector
otel_port = 4318
otel_service = airflow
otel_interval_milliseconds = 60000
```

Replaces / supplements StatsD with OTel-native emission. Send to OTel Collector, then to Tempo / Jaeger / Datadog / etc.

For Capital One–style: prefer OTel over StatsD for new deployments.

---

## 3. Structured task logs

Default log format is multi-line text. For SIEM ingestion, switch to JSON:

```ini
[logging]
log_format = %(asctime)s %(levelname)s %(message)s         # default
# Better:
[logging]
log_format_json = True
```

Each log line is a JSON object — searchable in Splunk / Elastic / Loki / CloudWatch Logs Insights.

---

## 4. Log handlers per cloud

| Backend | Config |
|---|---|
| Local FS | Default; not for multi-replica deployments |
| **S3** | `remote_logging=True; remote_log_conn_id=aws_default; remote_base_log_folder=s3://...` |
| **GCS** | Same with `gs://...` |
| **Azure Blob** | `wasb://...` |
| **CloudWatch Logs** | `aws-cloudwatch:///log-group/...` |
| **ElasticSearch / OpenSearch** | `airflow.providers.elasticsearch.log...` |
| **Stackdriver / Cloud Logging** | GCP-managed |

For regulated finance: encrypted bucket (KMS CMK); lifecycle to Glacier / GCS Archive after 90 days; SIEM ingest from the bucket.

---

## 5. Callbacks

```python
def on_failure(context):
    slack_alert(f"DAG {context['dag'].dag_id} failed: {context['exception']}")

@dag(
    on_failure_callback=on_failure,
    on_success_callback=on_success,
    sla_miss_callback=on_sla_miss,   # 2.x — deprecated in 3.0 for Deadlines
    ...
)
```

Per-task callbacks too. Useful for:
- PagerDuty / Slack notifications.
- Updating dashboards.
- Marking downstream as skipped under specific conditions.

---

## 6. Alerts that matter

A regulated shop's alert set:

| Alert | Symptom | Action |
|---|---|---|
| Scheduler heartbeat missing > 60s | Scheduler crashed/wedged | Page on-call; restart scheduler |
| DAG parse errors > 0 | Bad DAG deployed | Page DAG owner |
| DAG run failed (production tag) | Pipeline failed | Page on-call; rerun |
| DAG run SLA missed | SLA violation | Page on-call |
| Worker queue depth > N | Worker capacity issue | Scale workers; investigate |
| Pool open_slots = 0 for > 30 min | Pool exhausted | Page pool owner |
| Postgres CPU > 80% sustained | DB scaling needed | Increase RDS class |
| XCom rows > 1M | XCom abuse | Find the DAG; refactor |

---

## 7. Tracing — what a real trace looks like

OpenTelemetry traces in Airflow:

```
DAG: sales_etl
└── Task: extract                            (5s)
    └── HTTP call to source API              (4s)
└── Task: transform                          (10s)
    └── Snowflake SQL                        (8s)
└── Task: load                               (15s)
    └── Snowflake MERGE                      (12s)
```

For latency hotspots in pipelines: trace shows exactly which task / call dominates.

---

## 8. Managed-offering observability

| Service | Stack |
|---|---|
| **MWAA** | StatsD → CloudWatch; logs in CloudWatch Logs |
| **Composer** | Stackdriver; logs in Cloud Logging |
| **Azure Managed Airflow** | Log Analytics |
| **Astro** | Astro Observe (built-in); also exports to your stack |
| **Self-host** | Whatever you build |

Each managed offering has dashboards; complement with your SIEM and APM (Datadog, Dynatrace, etc.).

---

## 9. The dashboards every Airflow needs

1. **Cluster health** — scheduler heartbeat, parse times, queue depth.
2. **Per-DAG SLA** — last 30 days of run duration + SLA misses + failure count.
3. **Resource consumption** — pod-level (K8sExecutor) / worker-level (Celery).
4. **Pool utilization** — slot usage trend.
5. **Cost** — per-DAG, per-team (OpenCost / Kubecost integration).

For a Sr Lead interview: ability to articulate this dashboard set is signal of operator-grade experience.

---

## Sanity check

1. Three Airflow metrics whose deviation indicates real problems.
2. OpenTelemetry in 2.9+ — what does it give over StatsD?
3. JSON log format — why does it matter for SIEM?
4. The deprecated `sla_miss_callback` is replaced in 3.0 by what?
5. Cluster-health dashboard — name three panels.

---

## Sources

- [Logging & Monitoring](https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/logging-monitoring/index.html)
- [Metrics](https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/logging-monitoring/metrics.html)
- [OpenTelemetry support](https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/logging-monitoring/otel.html)
- [`statsd_exporter`](https://github.com/prometheus/statsd_exporter)

→ Next: [15 — Airflow on Kubernetes](15_airflow_on_k8s.md)


\newpage

# 15 — Airflow on Kubernetes: KubernetesExecutor, KubernetesPodOperator, KEDA scaling

## Why this module exists

Every managed Airflow offering is K8s under the hood. Self-hosted production almost always means Helm on K8s. This module is the K8s-specific Airflow knowledge.

---

## 1. The two K8s patterns

### 1.1 KubernetesExecutor (every task = pod)

```ini
[core]
executor = KubernetesExecutor
```

Already covered in module 04. Recap: each task is a pod. Pros: isolation, per-task resources, per-task SA. Cons: 5-15s pod startup overhead.

### 1.2 KubernetesPodOperator (one task = one pod)

Used with **any** executor (Celery, K8s, etc.). Spawns a one-off pod for THIS task:

```python
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator

train_step = KubernetesPodOperator(
    task_id="train_step",
    namespace="ml-training",
    name="train",
    image="myorg/train:1.0",
    cmds=["python", "train.py"],
    arguments=["--epochs=10"],
    service_account_name="train-sa",                   # IRSA / WIF / Entra MI
    resources={"requests": {"cpu": "4", "memory": "16Gi", "nvidia.com/gpu": "1"},
               "limits":   {"cpu": "8", "memory": "32Gi", "nvidia.com/gpu": "1"}},
    tolerations=[{"key": "nvidia.com/gpu", "operator": "Exists"}],
    node_selector={"workload": "gpu-training"},
    is_delete_operator_pod=True,
    in_cluster=True,
    config_file=None,
    deferrable=True,
    get_logs=True,
)
```

Used with Celery executor: scheduler runs lightweight orchestration in Celery; heavy/specialized work goes to pods.

This is the **Capital One–compatible** pattern: MWAA's Celery + K8sPodOperator hitting an EKS cluster for the actual ML work.

---

## 2. IRSA / WIF / Entra Workload ID for tasks

Each task pod has its own SA. The SA is bound to a cloud IAM principal:

- AWS: IRSA annotation on the SA → IAM role.
- GCP: Workload Identity annotation → GSA.
- Azure: Workload ID annotation → Managed Identity.

The task gets cloud credentials without static keys. Modules 26-28 in Topic 05 cover the binding.

For MWAA + K8sPodOperator on EKS:

```python
KubernetesPodOperator(
    ...
    service_account_name="train-sa",
    in_cluster=False,
    config_file=None,
    kubernetes_conn_id="eks_cluster",        # Airflow Connection with eks config
)
```

MWAA worker uses its execution role to assume into the EKS cluster's IAM; spawns pod with `train-sa`.

---

## 3. The DAG-on-K8s pattern (K8sExecutor + Helm)

For self-host: deploy via the official Apache Airflow Helm chart (or Astronomer's):

```bash
helm install airflow apache-airflow/airflow -n airflow --create-namespace \
  -f values.yaml
```

`values.yaml` highlights:

```yaml
executor: KubernetesExecutor

webserver:
  replicas: 2
  service: { type: ClusterIP }

scheduler:
  replicas: 2

triggerer:
  enabled: true
  replicas: 1

postgresql:
  enabled: false              # use external managed Postgres
data:
  metadataConnection:
    user: airflow
    pass: ""                   # from k8s secret
    host: postgres.internal
    port: 5432
    db: airflow

dags:
  gitSync:
    enabled: true
    repo: git@github.com:myorg/airflow-dags.git
    branch: main
    subPath: dags
    sshKeySecret: airflow-dags-deploy-key
    period: 60s

workers:
  enabled: false              # K8sExecutor — no Celery workers

logs:
  persistence:
    enabled: false
  remote:
    enabled: true
    classRef: airflow.providers.amazon.aws.log.s3_task_handler.S3TaskHandler
    config:
      remote_log_conn_id: aws_default
      remote_base_log_folder: s3://myorg-airflow-logs/

secrets:
  - airflow-fernet-key
  - airflow-secret-key
  - airflow-db-password

extraEnv: |
  - name: AIRFLOW__SECRETS__BACKEND
    value: airflow.providers.amazon.aws.secrets.secrets_manager.SecretsManagerBackend
  - name: AIRFLOW__SECRETS__BACKEND_KWARGS
    value: '{"connections_prefix": "airflow/connections", "variables_prefix": "airflow/variables"}'
```

---

## 4. KEDA autoscaling for Celery workers

If you stick with Celery for short tasks:

```yaml
# KEDA ScaledObject
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata: { name: airflow-worker, namespace: airflow }
spec:
  scaleTargetRef: { name: airflow-worker }
  minReplicaCount: 0          # scale to zero off-hours
  maxReplicaCount: 20
  triggers:
    - type: postgresql
      metadata:
        connectionFromEnv: KEDA_DB_CONNECTION
        query: |
          SELECT count(*) FROM task_instance
          WHERE state = 'queued' AND queue = 'default'
        targetQueryValue: '4'
```

KEDA scales workers based on queue depth in metadata DB. Saves money when idle.

`persistence: false` on workers — they're ephemeral; logs to S3 directly.

---

## 5. Pod templates

For K8sExecutor, define a default pod template:

```yaml
podTemplate: |
  apiVersion: v1
  kind: Pod
  metadata:
    labels: { airflow-worker: "true" }
  spec:
    serviceAccountName: airflow-task
    securityContext:
      runAsNonRoot: true
      runAsUser: 50000
      fsGroup: 50000
    containers:
      - name: base
        image: myorg/airflow-tasks:2.10.3
        resources:
          requests: { cpu: "100m", memory: "256Mi" }
          limits:   { cpu: "500m", memory: "1Gi" }
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: false   # Airflow writes to /opt/airflow
          capabilities: { drop: [ALL] }
```

Each task pod inherits this. Override per task via `executor_config={"pod_override": ...}`.

---

## 6. The DAG sync patterns on K8s

| Pattern | Notes |
|---|---|
| **git-sync sidecar** | Sidecar in scheduler + worker pods that pulls latest from git. Most common. |
| **Image-baked** | DAGs included in custom Docker image; deploy by image tag. Astronomer / regulated shops. |
| **PVC-shared** | Single PVC mounted into all pods; CI writes DAGs there. Now uncommon. |
| **S3/GCS/Blob sync** | MWAA / Composer pattern; not standard for self-host but possible. |

Image-baked is the most secure (DAGs are immutable, signed); git-sync is the most agile.

---

## 7. Networking

Airflow on K8s lives in its own namespace with:

- **NetworkPolicy default-deny** + explicit allows.
- **PSA restricted** (with exception for scheduler/worker pods that need PVC writes — use baseline).
- **Service mesh sidecar** (Istio/Linkerd) for mTLS to internal services.
- **Webserver Ingress** behind oauth2-proxy / API gateway.

---

## 8. The Capital One angle

For C1's AWS-native shop: **MWAA + K8sPodOperator hitting EKS** is the cleanest pattern. MWAA's Celery handles short scheduling work; heavy ML tasks fan out as pods on EKS with their own IRSA SAs.

Alternative: **Astro Hybrid on EKS** — Astronomer manages the control plane; data plane runs in your VPC. More flexibility but pricier.

Module 16 covers MWAA specifically.

---

## Sanity check

1. KubernetesExecutor vs KubernetesPodOperator — when does each fit?
2. KEDA scales Celery workers based on what?
3. Pod template via Helm — what defaults does it set, and how do you override per task?
4. DAG sync via git-sync vs image-baked — trade-offs.
5. MWAA + K8sPodOperator pattern — what does the MWAA worker contribute vs what does the EKS pod contribute?

---

## Sources

- [Apache Airflow Helm Chart](https://airflow.apache.org/docs/helm-chart/stable/index.html)
- [KubernetesPodOperator](https://airflow.apache.org/docs/apache-airflow-providers-cncf-kubernetes/stable/operators.html)
- [KEDA](https://keda.sh/)
- [Astronomer Helm Chart](https://github.com/astronomer/airflow-chart)

→ Next: [16 — **MWAA — AWS Managed Workflows for Apache Airflow**](16_mwaa_aws.md)


\newpage

# 16 — MWAA: Amazon Managed Workflows for Apache Airflow

> *"For Capital One's AWS-native posture, MWAA + PRIVATE_ONLY + Secrets Manager backend + KMS + K8sPodOperator-to-EKS is the conventional answer."*

## Why this module exists

MWAA is the AWS-native managed Airflow. This module is the depth on its environment classes, networking, IAM, secrets, and limits. Critical for the Capital One target.

---

## 1. The MWAA architecture

- Fargate-based (workers run as Fargate tasks).
- VPC-injected — runs in YOUR VPC; reaches YOUR private resources.
- Hidden control plane (AWS-managed RDS Postgres, MQ for Celery, scheduler).
- Webserver: separate Fargate task.
- Triggerer: supported since 2.7+ MWAA versions.

You don't manage K8s; AWS handles it.

---

## 2. Environment classes (2026)

| Class | vCPU / Memory | $/hr (us-east-1) | Use case |
|---|---|---:|---|
| `mw1.small` | 1 / 2 GB | ~$0.49 | Dev / very small |
| `mw1.medium` | 2 / 4 GB | ~$0.79 | Small teams |
| `mw1.large` | 4 / 8 GB | ~$1.59 | Standard prod |
| `mw1.xlarge` | 8 / 16 GB | ~$2.97 | Many DAGs |
| `mw1.2xlarge` | 16 / 32 GB | ~$5.78 | Largest |

Plus the metadata DB storage + worker autoscaling counts. Pricing is per-environment-hour; minimum spend even when idle.

For comparison: `mw1.large` × 730 hrs = ~$1,160/mo baseline + workers.

---

## 3. Supported Airflow versions

MWAA supports a rolling subset of Airflow 2.x. As of 2026-05: 2.8.1, 2.9.2, 2.10.1, 2.10.3 typically.

**MWAA does NOT support Airflow 3.0 yet** as of mid-2026 — confirm at quote time. For 3.0, alternatives: self-host on EKS or Astronomer.

---

## 4. VPC requirements

MWAA injects into your VPC. Requirements:

- **Two private subnets in different AZs**.
- **Route to internet** (NAT GW) OR all required services via **VPC endpoints**.
- **Security group** allowing intra-environment communication.

For regulated finance: VPC endpoints (no NAT). The endpoints needed:

- `com.amazonaws.<region>.s3` (Gateway endpoint — for DAG bucket).
- `com.amazonaws.<region>.ecr.api` + `.ecr.dkr` (for image pulls if using K8sPodOperator).
- `com.amazonaws.<region>.secretsmanager`.
- `com.amazonaws.<region>.logs` (CloudWatch).
- `com.amazonaws.<region>.kms`.
- `com.amazonaws.<region>.monitoring` (CloudWatch metrics).
- `com.amazonaws.<region>.sqs` (for the internal queue).
- Plus per-service endpoints (Snowflake PrivateLink, etc.).

---

## 5. Webserver access modes

- **`PUBLIC_ONLY`** — webserver reachable via internet (with IAM auth).
- **`PRIVATE_ONLY`** — webserver reachable only from VPC. Requires Direct Connect / VPN / VPN-via-bastion for human access.

For regulated finance: `PRIVATE_ONLY` + Bastion / zero-trust gateway.

---

## 6. DAG storage — S3

MWAA reads DAGs from a designated S3 bucket:

- `dags/` folder — DAG `.py` files (synced ~30s).
- `plugins.zip` — custom operators/hooks (synced on env restart).
- `requirements.txt` — PyPI deps (synced on env restart).
- `startup.sh` (2.10+) — custom startup script (synced on env restart).

**Versioning MUST be enabled** on the bucket. MWAA pins to a specific version per `requirements.txt` / `plugins.zip` upload.

CMK encryption on the bucket. KMS key policy must allow the MWAA execution role.

---

## 7. requirements.txt — the constraints rule

```
# requirements.txt
--constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.3/constraints-3.11.txt"

apache-airflow-providers-snowflake==5.5.1
apache-airflow-providers-databricks==6.7.0
dbt-core==1.8.0
dbt-snowflake==1.8.0
astronomer-cosmos==1.5.0
```

Must reference the constraints URL for the exact Airflow version. Otherwise pip resolves wildly. MWAA will reject builds that don't pin to Airflow's constraints.

No system-level packages (no apt-install). For C libraries (e.g., psycopg2 wheels): use the wheel built for manylinux; works.

---

## 8. plugins.zip

Custom Airflow plugins: operators, hooks, macros. Zipped, uploaded. Synced on env restart (~5-20 min).

Use sparingly. Prefer:
- Provider packages from PyPI (via requirements.txt).
- Custom code in `dags/` (DAG-private classes).

---

## 9. IAM — execution role vs worker permissions

Two roles:

- **Execution role** — the role MWAA itself uses (S3 access to DAG bucket, secrets, KMS, logs, ECR for K8sPodOperator).
- **Task role** — what DAG tasks actually use to call AWS APIs.

Common pattern: same role for both, scoped tight. Or split for least privilege.

```json
// Execution role - example minimum
{
  "Version": "2012-10-17",
  "Statement": [
    {"Effect": "Allow", "Action": ["airflow:*"], "Resource": "*"},
    {"Effect": "Allow", "Action": ["s3:GetObject*","s3:GetBucket*","s3:List*"],
     "Resource": ["arn:aws:s3:::myorg-mwaa-dags-prod","arn:aws:s3:::myorg-mwaa-dags-prod/*"]},
    {"Effect": "Allow", "Action": "kms:Decrypt",
     "Resource": "arn:aws:kms:us-east-1:123:key/<cmk>"},
    {"Effect": "Allow", "Action": "secretsmanager:GetSecretValue",
     "Resource": "arn:aws:secretsmanager:us-east-1:123:secret:airflow/*"},
    {"Effect": "Allow", "Action": ["logs:CreateLogStream","logs:PutLogEvents"],
     "Resource": "arn:aws:logs:us-east-1:123:log-group:airflow-*"}
  ]
}
```

For DAGs that call SageMaker / Snowflake / Databricks: add those permissions on the role. Or use **AssumeRole** to a per-DAG role from within tasks.

---

## 10. Secrets Manager backend

```python
# Set as env var in MWAA UI:
AIRFLOW__SECRETS__BACKEND="airflow.providers.amazon.aws.secrets.secrets_manager.SecretsManagerBackend"
AIRFLOW__SECRETS__BACKEND_KWARGS='{"connections_prefix":"airflow/connections","variables_prefix":"airflow/variables"}'
```

Now `conn_id=snowflake_prod` → `airflow/connections/snowflake_prod` in Secrets Manager.

This is the **mandatory pattern** for regulated MWAA. Don't put real credentials in the MWAA UI's Connections tab.

---

## 11. Logging — CloudWatch

MWAA ships 5 log groups:

- `airflow-<env>-DAGProcessing`
- `airflow-<env>-Scheduler`
- `airflow-<env>-WebServer`
- `airflow-<env>-Worker`
- `airflow-<env>-Task`

Enable per log group; `INFO` is the floor; `DEBUG` is expensive (lots of bytes). Encrypt with CMK; lifecycle to Glacier.

For volume: a busy production env can produce $500-1000/mo in CloudWatch costs if not tuned.

---

## 12. Scaling

MWAA autoscales workers between 1 and `MaxWorkers` (set on env). Triggerer is fixed.

Worker count scales based on queued tasks. Cold worker startup ~2 min, so very short DAGs see scheduling lag. For consistent throughput: set `MinWorkers` > 1.

---

## 13. The Capital One MWAA pattern

```
Capital One AWS account (regulated VPC)
│
├── MWAA env (mw1.large)
│   ├── PRIVATE_ONLY webserver (reached via Bastion / Verified Access)
│   ├── S3 DAG bucket (CMK + versioning + VPC GW endpoint)
│   ├── Execution role: Secrets Manager + KMS + logs + ECR-pull
│   ├── Secrets Backend: airflow/connections/* in Secrets Manager
│   ├── No NAT — all access via VPC endpoints
│   └── Logs → CloudWatch (CMK)
│
├── DAGs:
│   - Snowflake ETL (SnowflakeOperator with conn from Secrets Mgr)
│   - Databricks job trigger (DatabricksRunNowOperator)
│   - SageMaker pipeline trigger (PythonOperator → SageMaker SDK)
│   - K8sPodOperator → EKS cluster (heavy ML work)
│
└── Cloud Custodian policies:
    - "MWAA env must be PRIVATE_ONLY in prod"
    - "DAG bucket must have CMK + versioning"
    - "MWAA execution role: no wildcards"
```

---

## 14. Limitations of MWAA

- No Airflow 3.0 yet.
- No shell into the workers / scheduler (debugging via logs + env restart).
- No custom Postgres / metadata DB tuning.
- No Celery customization.
- Plugin sync is slow (env restart required for `plugins.zip` / `requirements.txt` changes).
- Triggerer scaling is fixed (no horizontal scaling).
- No per-DAG resource limits — pools and `max_active_runs` only.

When you outgrow MWAA: Astro Hybrid (Astronomer in your VPC) or self-host on EKS.

---

## 15. Cost optimization

- `MinWorkers` = 1, `MaxWorkers` per peak.
- Right-size environment class — `mw1.medium` is enough for many shops.
- Aggressive log rotation; turn off DEBUG.
- Deferrable operators reduce worker hours dramatically.
- K8sPodOperator into spot EKS nodes for the actual heavy lifting.

---

## Sanity check

1. PRIVATE_ONLY webserver — how do humans reach it?
2. The S3 DAG bucket must have what setting enabled, and why?
3. requirements.txt constraints — why does MWAA enforce them?
4. Two IAM roles in MWAA — what does each cover?
5. Secrets Manager backend wiring — what env vars do you set in MWAA?
6. When do you outgrow MWAA?

---

## Sources

- [MWAA docs](https://docs.aws.amazon.com/mwaa/)
- [MWAA pricing](https://aws.amazon.com/managed-workflows-for-apache-airflow/pricing/)
- [MWAA networking](https://docs.aws.amazon.com/mwaa/latest/userguide/networking-about.html)
- [MWAA + Secrets Manager](https://docs.aws.amazon.com/mwaa/latest/userguide/connections-secrets-manager.html)
- [MWAA versions](https://docs.aws.amazon.com/mwaa/latest/userguide/airflow-versions.html)

→ Next: [17 — Cloud Composer (GCP)](17_composer_gcp.md)


\newpage

# 17 — Cloud Composer (GCP)

## Why this module exists

GCP's managed Airflow. The Composer 3 generation (GA April 2024) brought serverless components and simpler networking. This module covers both Composer 2 and 3.

---

## 1. Composer 2 vs Composer 3

| | Composer 2 | Composer 3 |
|---|---|---|
| Architecture | GKE Autopilot cluster | Serverless components |
| Scaling | Up + down within env | Smaller baseline, scales to near-zero |
| Identity | Workload Identity | Workload Identity Federation (new model) |
| Networking | Private IP / Public | Private Service Connect (PSC) |
| Custom images | Limited | Full custom container option |
| Pricing | Per-env infra | Per vCPU-hour + storage |

For new deployments in 2025-2026: **Composer 3**.

---

## 2. Architecture (Composer 3)

- Airflow components run in a Google-managed project (the **service producer project**).
- Connects to **your** project via PSC.
- DAG bucket in **your** project (GCS).
- Logs to **your** Cloud Logging.

Trade-off: opaque control plane vs predictable cost.

---

## 3. Supported Airflow versions

Composer 3 typically supports the latest 2-3 Airflow 2.x lines + early support for 3.0 (rolling). Confirm at quote.

---

## 4. Workload Identity Federation for Composer 3

Each Composer env binds a **Kubernetes service account** to a **GCP service account**:

```bash
gcloud composer environments update my-env --location us-central1 \
  --update-airflow-configs core-default_pool_task_slot_count=64

# To use a per-DAG GSA (Composer 3):
gcloud iam service-accounts add-iam-policy-binding \
  ml-tasks@my-proj.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:my-proj.svc.id.goog[composer-user-workloads/airflow-worker]"
```

Tasks now run as the per-task GSA — no JSON keys.

---

## 5. DAG storage — GCS

Composer auto-provisions a GCS bucket per env:

- `dags/` — auto-synced.
- `plugins/` — synced on env update.
- `data/` — your scratch area.

Pattern: CI pushes DAGs via `gsutil rsync` or `gcloud storage cp`. Sync is fast (~30s).

CMEK encryption on the bucket; bucket retention if required.

---

## 6. PyPI packages

```bash
gcloud composer environments update my-env --location us-central1 \
  --update-pypi-packages-from-file requirements.txt
```

Composer triggers a rolling image rebuild (~10-20 min). For custom system packages: use the **custom container image** option in Composer 3.

---

## 7. Secrets backend — GCP Secret Manager

```bash
gcloud composer environments update my-env --location us-central1 \
  --update-airflow-configs \
    secrets-backend=airflow.providers.google.cloud.secrets.secret_manager.CloudSecretManagerBackend,\
    secrets-backend_kwargs='{"connections_prefix":"airflow-connections","variables_prefix":"airflow-variables","project_id":"my-proj"}'
```

The Composer env's GSA needs `roles/secretmanager.secretAccessor` on the secrets.

---

## 8. Networking — private environments

Composer 3 with private IP:

```bash
gcloud composer environments create my-env --location us-central1 \
  --image-version composer-3-airflow-2.10.3 \
  --enable-private-environment \
  --enable-private-endpoint \
  --network my-vpc --subnetwork my-subnet
```

Connects via **Private Service Connect** — no need to peer VPCs. Cleaner than Composer 2's VPC-peering model.

For VPC-SC: place project in a service perimeter; Composer can be inside.

---

## 9. CMEK and at-rest encryption

Pass CMEK on environment create:

```bash
gcloud composer environments create my-env --location us-central1 \
  --kms-key projects/.../keyRings/.../cryptoKeys/composer
```

Applies to:
- GKE cluster (Composer 2) / control plane state.
- GCS DAG bucket.
- Cloud SQL metadata DB.
- Pub/Sub queue.

---

## 10. Logging — Cloud Logging

Default destination. Filter by logName + DAG ID. Export sinks to BigQuery / GCS for long-term retention. CMEK on log buckets.

---

## 11. Comparison vs MWAA

| | MWAA | Composer 3 |
|---|---|---|
| Pricing model | Per env-hour (fixed) | Per vCPU-hour (variable) |
| Idle cost | Always-on baseline | Scales to near-zero |
| Custom image | No | **Yes** |
| Airflow 3.0 support | No (2026-05) | Earlier |
| Private network | PRIVATE_ONLY mode | PSC-based |
| Secrets | AWS Secrets Manager | GCP Secret Manager |
| Region selection | Per env | Per env |
| Composer ergonomics | Fewer moving parts | More flexible |

For greenfield GCP shops: Composer 3 is the default. For multi-cloud: Astronomer Astro often wins on consistency.

---

## 12. The Composer 3 reference architecture

```
Project: data-platform
├── VPC (private subnets only)
├── Cloud Composer 3 env (private IP, PSC)
│   ├── GCS DAG bucket (CMEK)
│   ├── Cloud SQL metadata (CMEK)
│   ├── Workload Identity binding per task
│   ├── Secret Manager backend
│   └── Cloud Logging (CMEK)
│
└── Org Policy: 
    - disable SA JSON keys
    - require CMEK on all resources
    - VPC-SC perimeter
```

---

## Sanity check

1. Composer 2 vs Composer 3 — name two architectural differences.
2. How does Composer 3 connect to customer projects?
3. Custom container images — Composer 3 supports them; Composer 2?
4. Composer's auto-provisioned GCS bucket — what lives there and at what sync cadence?
5. CMEK on Composer covers what at-rest stores?

---

## Sources

- [Cloud Composer docs](https://cloud.google.com/composer/docs)
- [Composer 3 overview](https://cloud.google.com/composer/docs/composer-3/composer-overview)
- [Composer Workload Identity](https://cloud.google.com/composer/docs/composer-3/use-workload-identity)
- [Composer Secret Manager backend](https://cloud.google.com/composer/docs/composer-3/configure-secret-manager)
- [Composer pricing](https://cloud.google.com/composer/pricing)

→ Next: [18 — Azure Managed Airflow](18_azure_managed_airflow.md)


\newpage

# 18 — Azure Managed Airflow: ADF Workflow Orchestration Manager + Fabric Apache Airflow Jobs

## Why this module exists

Azure's managed Airflow story has shifted: the original **ADF Workflow Orchestration Manager** (WOM) launched 2023, was renamed/integrated into **Microsoft Fabric Data Factory** as "Apache Airflow Jobs" in 2024-2025, with WOM scheduled for retirement at the end of 2025. This module covers the transition and the current path.

---

## 1. The product line confusion

| Product | Status | Notes |
|---|---|---|
| **ADF Workflow Orchestration Manager** | **Retiring Dec 31, 2025** | Original managed Airflow in Azure Data Factory |
| **Fabric Data Factory Apache Airflow Jobs** | GA / preview late 2024-2025 | Successor — runs in Microsoft Fabric |
| **Astronomer Astro on Azure** | GA | Third-party managed (the practical alternative) |
| **Self-host on AKS** | DIY | Helm chart on AKS |

For new deployments: **Fabric Apache Airflow Jobs** OR **Astro on Azure** OR **self-host on AKS**. WOM is sunset.

---

## 2. Fabric Apache Airflow Jobs — architecture

- Runs inside **Microsoft Fabric** workspace.
- AKS-backed under the hood (managed by Microsoft).
- Uses **KubernetesExecutor** (not Celery).
- Tight integration with Fabric Data Factory pipelines, Lakehouse, OneLake.

For shops already on Fabric: this is the natural choice. For non-Fabric Azure shops: it's an awkward dependency.

---

## 3. DAG sync — git-based

Unlike MWAA's S3-blob upload model, Azure Managed Airflow syncs DAGs from a **git repository** (Azure DevOps, GitHub):

```
Azure DevOps repo
└── dags/
    ├── my_dag.py
    └── ...
```

Fabric polls the repo on a schedule. DAG changes propagate without an env restart.

This is **closer to the modern best practice** than MWAA's bucket-upload model.

---

## 4. Authentication

Microsoft Entra ID:
- UI auth via Entra (SSO).
- DAG-task auth via Managed Identity / Service Principal.
- Multi-tenant access via role assignments at the Fabric workspace level.

---

## 5. Secrets backend — Azure Key Vault

```
AIRFLOW__SECRETS__BACKEND=airflow.providers.microsoft.azure.secrets.key_vault.AzureKeyVaultBackend
AIRFLOW__SECRETS__BACKEND_KWARGS={"vault_url":"https://my-kv.vault.azure.net/", "connections_prefix":"airflow-connections", "variables_prefix":"airflow-variables", "sep":"-"}
```

Same caveat as module 08: KV secret names use `-` separator, not `/`.

---

## 6. Networking

- **Managed VNet** (default) — Microsoft-provided.
- **Customer VNet** integration — DAGs can reach private resources in your VNet.

For regulated workloads: customer VNet + private endpoints to all data resources.

---

## 7. When to choose Azure Managed Airflow

✅ **Choose Fabric Apache Airflow Jobs when**:
- Already on Microsoft Fabric.
- Need Airflow → Fabric Lakehouse / OneLake integration.
- Want managed without operational responsibility.

❌ **Pick Astro / self-host on AKS instead when**:
- Not on Fabric.
- Need flexibility WOM doesn't offer.
- Need newer Airflow versions earlier.

For a Sr Lead AI/ML candidate: **be aware** that Azure's managed Airflow is the youngest of the three big clouds and the most in-flux. A candid interview answer is: "On Azure, for regulated workloads, I'd lean to Astro Hybrid on AKS or self-host on AKS; Fabric Apache Airflow Jobs is a fit for Fabric-first shops."

---

## 8. The Optum / current-employer angle

The user's current shop (Optum) is heavy Azure + Databricks. If they use managed Airflow, it's likely:

- **Self-host on AKS** with Astronomer's Helm chart (most operationally mature).
- **Astro Hybrid** if budget allows.
- **Fabric Apache Airflow Jobs** if migration to Fabric is in progress.

WOM (the legacy) is being decommissioned; anyone on it is migrating.

---

## 9. Comparison

| | MWAA | Composer 3 | Fabric Airflow Jobs | Astro |
|---|---|---|---|---|
| Cloud | AWS | GCP | Azure | Any |
| Maturity | High | High | Newer | High (vendor) |
| Executor | Celery | KubernetesExecutor (Composer 3) | KubernetesExecutor | Yes |
| Custom image | No | Yes | Limited | Yes |
| Pricing | Per env-hour | Per vCPU-hour | Bundled with Fabric | Per AU-hour |
| Private network | PRIVATE_ONLY | PSC | Customer VNet | Hybrid VPC |

---

## Sanity check

1. The original Azure managed Airflow product is retiring. What replaces it?
2. Fabric Apache Airflow Jobs uses which executor?
3. DAG sync model in Azure Managed Airflow — how does it differ from MWAA?
4. Azure Key Vault as Secrets Backend — what naming quirk requires a config tweak?
5. When does Astro on Azure beat Fabric Apache Airflow Jobs?

---

## Sources

- [Fabric Data Factory Apache Airflow Jobs](https://learn.microsoft.com/en-us/fabric/data-factory/apache-airflow-jobs-concepts)
- [ADF Workflow Orchestration Manager (legacy)](https://learn.microsoft.com/en-us/azure/data-factory/workflow-orchestration-manager)
- [Azure Key Vault Secrets Backend](https://airflow.apache.org/docs/apache-airflow-providers-microsoft-azure/stable/secrets-backends/azure-key-vault.html)

→ Next: [19 — Astronomer + self-hosted on-prem](19_astro_and_onprem.md)


\newpage

# 19 — Astronomer (Astro) + self-hosted on-prem (Helm)

## Why this module exists

Two non-cloud-native managed paths: **Astronomer Astro** (the dominant commercial Airflow vendor) and **self-host on K8s via Helm**. For regulated finance that outgrows MWAA/Composer/Azure Managed: this is where you go.

---

## 1. Astronomer (Astro) — the offerings

| Offering | Hosted by | Data plane | Use case |
|---|---|---|---|
| **Astro Hosted** | Astronomer | Astronomer's AWS account | Fastest start; multi-tenant SaaS |
| **Astro Hybrid** | Astronomer (control plane) | **Customer's** AWS / GCP / Azure account | Regulated data stays in your VPC |
| **Astro Software** | Customer | Customer | Fully self-host with Astronomer's Helm chart |

For regulated finance: **Astro Hybrid**. Control plane in Astronomer; workers + DAGs + data in your cloud account.

---

## 2. Why Astro

- **Latest Airflow versions** — fast track to 2.10+, 3.0+ (often weeks faster than MWAA).
- **Astro CLI** — local dev with `astro dev start` (Docker Compose stack).
- **Image-based deploys** — `astro deploy` builds a Docker image with your DAGs + deps, pushes to Astro registry, rolls out. Cleaner than git-sync.
- **Astro Workspaces + Deployments** — multi-team, multi-env hierarchy.
- **Astro Observe** — built-in observability.
- **Astro Cloud IDE** — web-based DAG authoring (optional).

---

## 3. Astro CLI workflow

```bash
# Initialize project
astro dev init
# Adds: Dockerfile, requirements.txt, packages.txt, dags/, plugins/

# Local dev
astro dev start                  # spawns Docker Compose: Postgres + Airflow

# Deploy
astro login
astro deploy <deployment-id>     # builds image, pushes, rolls out
```

Image-based deploys mean a deploy is immutable — promotion = digest pin. Cleaner than MWAA's bucket model.

---

## 4. Astro pricing

Astro Units (AU) — each ~ $0.30-0.50/hr. A dev env: ~$0.35/hr → ~$255/mo. A prod env: $1500-5000/mo minimum.

More expensive than MWAA/Composer for steady state. Justified by:
- Newer Airflow earlier.
- Better observability.
- Image-based deploy.
- 24/7 support.

For Capital One: budget exists; Astro Hybrid is plausible if MWAA's limits bite.

---

## 5. Self-host with Helm — the alternative

For the budget-conscious or already-on-K8s shop:

```bash
helm install airflow apache-airflow/airflow -n airflow --create-namespace -f values.yaml
```

Module 15 covered the patterns. Recap of the operational burden:

- HA Postgres (CloudNativePG / RDS / managed).
- Redis (if Celery; not needed for K8sExecutor).
- DAG sync (git-sync sidecar OR image-baked).
- Vault for secrets.
- KEDA for autoscaling.
- Falco / runtime security.
- Velero for backup.
- Cert-manager for ingress TLS.
- Monitoring stack (Prom / Grafana / Loki / OTel).

You operate every layer. For mature ops teams: cheaper. For small teams: false economy — Astro or MWAA wins.

---

## 6. Astro Hybrid for regulated finance

```
Customer AWS account (regulated VPC)
├── EKS cluster (operated by Astronomer)
│   ├── KubernetesExecutor
│   ├── DAGs run as K8s pods (per-task IRSA)
│   ├── Astro images with your code
│   └── Vault / Secrets Manager backend
│
├── S3 buckets (CMK)
├── Snowflake PrivateLink
└── Databricks PrivateLink

Astronomer SaaS (cross-account)
├── Control plane: API, UI, deployment orchestration
└── Observability platform
```

Customer's data never leaves their VPC. Control plane handles UI + Deployment lifecycle. Best of both worlds when budget allows.

---

## 7. The on-prem path (air-gapped)

If you can't even use Astro Hybrid (regulated air-gap):

- **Astro Software**: fully self-host with Astronomer's Helm chart + on-prem Postgres + on-prem registry.
- **Apache Helm chart**: pure OSS, no Astronomer.

Air-gap requirements:
- Internal git mirror for DAGs.
- Internal PyPI mirror for deps.
- Internal Docker registry (Harbor).
- Vault for secrets.
- All Airflow Helm-chart image pulls from internal registry.

---

## 8. The decision matrix

| Need | Pick |
|---|---|
| AWS-native, willing to live with MWAA's limits | **MWAA** |
| Need latest Airflow + better dev UX | **Astro Hybrid on AWS** |
| GCP-native | **Composer 3** |
| Azure + already on Fabric | **Fabric Apache Airflow Jobs** |
| Azure + not Fabric | **Astro on Azure** or self-host |
| Air-gapped regulated | **Astro Software** or self-host Helm |
| Tiny team, big budget | **Astro Hosted** |
| Tiny team, small budget | **Self-host on managed K8s** |

For Capital One: MWAA covers most needs; Astro Hybrid for teams that need 3.0 or richer dev UX earlier.

---

## 9. Migration paths

- **MWAA → Astro Hybrid on AWS**: lift-and-shift DAGs; rewire connections; migrate secrets backend (typically same Secrets Manager). Days.
- **Composer 2 → Composer 3**: in-place upgrade via gcloud; some breaking changes around custom container. Weeks.
- **Self-host → Astro Hybrid**: image-based deploy migration; Astro takes over operations.
- **2.x → 3.0**: regardless of host, see module 31 (Migration).

---

## Sanity check

1. Astro Hosted vs Astro Hybrid vs Astro Software — which is right for "regulated data must stay in our VPC"?
2. Astro's deploy model is image-based. Why is that an upgrade over MWAA's S3-bucket-upload?
3. Self-host Helm — list five operational responsibilities you take on.
4. For an air-gapped shop, what's the deployment path?
5. When does Astro Hybrid beat MWAA for Capital One?

---

## Sources

- [Astronomer Astro docs](https://docs.astronomer.io/astro/)
- [Astro CLI](https://docs.astronomer.io/astro/cli/install-cli)
- [Astro Hybrid](https://docs.astronomer.io/astro/hybrid-overview)
- [Apache Airflow Helm Chart](https://airflow.apache.org/docs/helm-chart/stable/)

→ Next: [20 — DWH integrations](20_dwh_integrations.md)


\newpage

# 20 — Snowflake, Redshift, BigQuery, Synapse — DWH operator patterns & auth

## Why this module exists

Data warehouses are the 80% destination for Airflow ETL. This module covers the operators and auth patterns for each.

---

## 1. Snowflake (Capital One uses heavily)

Provider: `apache-airflow-providers-snowflake`.

```python
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator

load_sales = SnowflakeOperator(
    task_id="load_sales",
    snowflake_conn_id="snowflake_prod",
    sql="""
        MERGE INTO analytics.sales s
        USING staging.sales_raw st
        ON s.id = st.id
        WHEN MATCHED THEN UPDATE SET ...
        WHEN NOT MATCHED THEN INSERT ...
    """,
)
```

### Auth options (in order of safety)

- **Key-pair auth** (RSA): recommended. No password rotation; revoke key in Snowflake to revoke access.
- **OAuth (M2M)** with external IdP (Okta/Azure AD).
- **Username + password** with SSO: legacy; avoid for service accounts.

Connection extras for key-pair:

```json
{
  "account": "myorg-prod",
  "warehouse": "ETL_WH",
  "database": "PROD",
  "role": "AIRFLOW_ETL_ROLE",
  "authenticator": "snowflake_jwt",
  "private_key_file": "/run/secrets/snowflake_private_key.p8"
}
```

### Snowflake PrivateLink

Connection host: `myorg.privatelink.snowflakecomputing.com`. Traffic stays inside cloud backbone.

### Async SnowflakeSqlApiOperator

For long-running queries (>1min): `SnowflakeSqlApiOperator` returns immediately; Triggerer polls async. Workers stay free.

### Snowpipe pattern

For continuous loads: Snowpipe (Snowflake-managed) loads automatically from S3. Airflow merely triggers and monitors.

---

## 2. Redshift

Provider: `apache-airflow-providers-amazon`.

Two operators:
- **`RedshiftSQLOperator`** — connects via JDBC.
- **`RedshiftDataOperator`** — uses the **Redshift Data API** (HTTP, IAM-auth, async).

For serverless-friendly: `RedshiftDataOperator`. No long-lived JDBC connection; IAM auth via task role.

```python
from airflow.providers.amazon.aws.operators.redshift_data import RedshiftDataOperator

load = RedshiftDataOperator(
    task_id="load",
    workgroup_name="my-serverless-workgroup",       # for Redshift Serverless
    database="dev",
    sql="COPY analytics.sales FROM 's3://...' IAM_ROLE '...' FORMAT AS PARQUET",
    deferrable=True,                                 # async polling
)
```

Copy from S3 with IAM role (no static creds). Standard pattern.

---

## 3. BigQuery

Provider: `apache-airflow-providers-google`.

```python
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator

load = BigQueryInsertJobOperator(
    task_id="load",
    configuration={
        "query": {
            "query": "INSERT INTO dataset.sales SELECT * FROM dataset.staging_sales WHERE ds='{{ ds }}'",
            "useLegacySql": False,
        },
    },
    location="US",
    deferrable=True,
)
```

`BigQueryInsertJobOperator` is the modern operator (subsumed many older ones). Connection uses Workload Identity Federation or service account.

For partitioned tables: write directly to the partition (`mytable$20260520`).

---

## 4. Azure Synapse / Fabric Warehouse

Provider: `apache-airflow-providers-microsoft-azure`.

Synapse Pipelines + Airflow rarely overlap (Synapse Pipelines IS an orchestrator). The Airflow + Synapse pattern:

- Synapse SQL Pool: `MsSqlOperator` with Synapse connection.
- Synapse Spark: `AzureSynapseRunPipelineOperator` (calls Synapse Pipelines).
- Fabric Warehouse: SQL operators via the Fabric Warehouse SQL endpoint.

For Optum-style Azure shops: Airflow orchestrating Synapse / Fabric is common.

---

## 5. Databricks SQL Warehouse

Provider: `apache-airflow-providers-databricks`.

```python
from airflow.providers.databricks.operators.databricks_sql import DatabricksSqlOperator

query = DatabricksSqlOperator(
    task_id="query",
    databricks_conn_id="databricks_default",
    sql="SELECT count(*) FROM gold.sales WHERE ds='{{ ds }}'",
    sql_endpoint_name="prod_sql_warehouse",
)
```

For SQL-first lakehouse queries: Databricks SQL Warehouse with PrivateLink.

---

## 6. The anti-pattern: transforming in Airflow Python

```python
# WRONG
@task
def transform(records: list) -> list:
    return [{"id": r["id"], "amount": r["amount"] * 1.1} for r in records]
```

10K rows in XCom → blow up metadata DB. For warehouse-targeted ETL: **transform in the warehouse**.

```python
# RIGHT
transform_in_sf = SnowflakeOperator(
    task_id="transform",
    sql="INSERT INTO analytics.priced SELECT id, amount * 1.1 FROM staging.raw",
)
```

Snowflake / BQ / Redshift have unlimited compute relative to your Airflow worker. Push down.

---

## 7. Provider package versioning

For 2.10 + Snowflake: `apache-airflow-providers-snowflake==5.5.1` (or latest). Pin in requirements.txt.

Provider packages have their own version lifecycle independent of Airflow core. Major version bumps may break operator signatures.

---

## 8. Connection management at scale

For 100+ Connection objects across envs: declare them in Terraform / Infrastructure-as-Code:

```hcl
resource "aws_secretsmanager_secret" "snowflake_conn" {
  name = "airflow/connections/snowflake_prod"
}
resource "aws_secretsmanager_secret_version" "snowflake_conn" {
  secret_id = aws_secretsmanager_secret.snowflake_conn.id
  secret_string = jsonencode({
    conn_type = "snowflake"
    host      = "myorg.privatelink.snowflakecomputing.com"
    login     = "svc_airflow"
    extra     = jsonencode({
      account = "myorg-prod"
      warehouse = "ETL_WH"
      role = "AIRFLOW_ETL_ROLE"
      authenticator = "snowflake_jwt"
      private_key_file = "/run/secrets/snowflake.p8"
    })
  })
}
```

Apply Terraform → Connections appear in Airflow (via Secrets Backend). No manual UI clicking.

---

## Sanity check

1. Snowflake key-pair vs OAuth vs username/password — order of preference and why.
2. `RedshiftDataOperator` deferrable mode — what does it free?
3. Why is "transform in Airflow Python" an anti-pattern for warehouse loads?
4. Snowflake PrivateLink — what does the connection host look like?
5. Connection-as-code via Terraform — what's the win?

---

## Sources

- [Snowflake provider](https://airflow.apache.org/docs/apache-airflow-providers-snowflake/stable/)
- [Amazon provider — Redshift operators](https://airflow.apache.org/docs/apache-airflow-providers-amazon/stable/operators/redshift/)
- [Google provider — BigQuery operators](https://airflow.apache.org/docs/apache-airflow-providers-google/stable/operators/cloud/bigquery.html)
- [Databricks provider](https://airflow.apache.org/docs/apache-airflow-providers-databricks/stable/)
- [Microsoft Azure provider](https://airflow.apache.org/docs/apache-airflow-providers-microsoft-azure/stable/)

→ Next: [21 — Databricks integration](21_databricks_integration.md)


\newpage

# 21 — Databricks integration: operators, auth, DBX Workflows interop, DAB

## Why this module exists

Capital One uses Databricks. Optum uses Databricks. Knowing the Airflow ↔ Databricks operator zoo is muscle memory for this user.

---

## 1. The operator zoo

Provider: `apache-airflow-providers-databricks`.

| Operator | Use |
|---|---|
| `DatabricksRunNowOperator` | Trigger an **existing** Databricks Workflow job by job_id |
| `DatabricksSubmitRunOperator` | One-shot run (no persistent job) |
| `DatabricksNotebookOperator` | Run a notebook directly with params |
| `DatabricksTaskOperator` + `DatabricksWorkflowTaskGroup` | **Orchestrate a Databricks Workflows job from Airflow tasks** — the modern pattern |
| `DatabricksSqlOperator` | SQL on a Databricks SQL Warehouse |
| `DatabricksRunSensor` | Wait for a Databricks job |
| `DatabricksJobRunSensor` | Same with deferrable |

---

## 2. Auth — the ladder

| Auth | Mechanism | When |
|---|---|---|
| PAT (Personal Access Token) | Static token in Connection | Dev only |
| Service Principal (M2M OAuth) | Client ID + secret → OAuth | Standard prod |
| Azure MSI | Managed Identity (Azure-only) | Azure-native Databricks |
| AWS IRSA → cross-account | EKS pod assumes role in Databricks-account | EKS+Databricks-on-AWS |

For Capital One: SP+OAuth M2M is the typical pattern.

Connection extras:

```json
{
  "host": "https://myorg.cloud.databricks.com",
  "auth_type": "service_principal_oauth",
  "client_id": "<sp-app-id>",
  "client_secret": "<from-vault>",
  "tenant_id": "<aad-tenant>"
}
```

---

## 3. DatabricksWorkflowTaskGroup — the cost saver

```python
from airflow.providers.databricks.operators.databricks_workflow import DatabricksWorkflowTaskGroup
from airflow.providers.databricks.operators.databricks import DatabricksTaskOperator

with DAG(...) as dag:
    with DatabricksWorkflowTaskGroup(
        group_id="dbx_workflow",
        databricks_conn_id="databricks_prod",
        job_clusters=[{
            "job_cluster_key": "main",
            "new_cluster": {
                "spark_version": "15.4.x-scala2.12",
                "node_type_id": "i3.xlarge",
                "num_workers": 4,
            },
        }],
    ) as dbx_group:
        notebook1 = DatabricksTaskOperator(
            task_id="prep", notebook_task={"notebook_path": "/Workspace/Repos/prod/prep"},
            job_cluster_key="main",
        )
        notebook2 = DatabricksTaskOperator(
            task_id="train", notebook_task={"notebook_path": "/Workspace/Repos/prod/train"},
            job_cluster_key="main",
        )
        notebook1 >> notebook2
```

Databricks renders this as a **single Workflows job with multiple tasks** — billed at the cheaper **Jobs** rate (~$0.07/DBU) instead of **All-Purpose** (~$0.40/DBU). 5-6x cost reduction for production pipelines.

Critical pattern. Bring up in interviews.

---

## 4. The Databricks Workflows alternative

Databricks has its own orchestrator: **Workflows / Lakeflow Jobs**. For workflows fully inside Databricks:

✅ **Use Databricks Workflows when**:
- Pipeline is 100% Databricks notebooks/jobs.
- You want lakehouse-native cost (Jobs rate).
- No need to coordinate non-Databricks systems.

✅ **Use Airflow when**:
- Pipeline spans Databricks + Snowflake + S3 + SageMaker + Slack.
- You need Airflow's audit trail / SLA tooling.
- You're already on Airflow.

Both coexist at Capital One: Databricks Workflows for in-platform, Airflow for cross-platform.

---

## 5. DAB (Databricks Asset Bundles) + Airflow

DAB is Databricks' IaC for jobs/notebooks/workflows. Pattern:

1. DABs define the Databricks job in YAML (`databricks.yml`).
2. `databricks bundle deploy` ships it.
3. Airflow `DatabricksRunNowOperator(job_id="${{ dab.job_id }}")` triggers.

Separates job definition (DAB, owned by Databricks team) from orchestration (Airflow DAG, owned by data eng).

---

## 6. Cluster patterns

- **Job cluster** — ephemeral, created for one job, terminated after. Best cost.
- **All-purpose cluster** — long-lived, shared. Convenient but expensive.
- **Serverless SQL warehouse** — for SQL queries.
- **Serverless Jobs compute** — newer; auto-scaled.

For Airflow-triggered: **job cluster** unless you have specific reasons.

---

## 7. Anti-patterns

| Anti-pattern | Fix |
|---|---|
| `DatabricksSubmitRunOperator` for every task (orphan clusters) | `DatabricksWorkflowTaskGroup` (shared cluster) |
| PAT auth in prod | Service Principal OAuth |
| All-purpose cluster (DBU rate) | Job cluster |
| Hardcoded notebook paths | Use git-backed Repos + ref by path |
| Long-poll sync wait | `DatabricksJobRunSensor` with `deferrable=True` |

---

## Sanity check

1. `DatabricksWorkflowTaskGroup` saves what cost factor over `DatabricksSubmitRunOperator` per task?
2. Service Principal OAuth vs PAT — why prefer SP?
3. When does Databricks Workflows beat Airflow?
4. DAB + Airflow pattern — who owns what?
5. Deferrable `DatabricksJobRunSensor` — what does it save?

---

## Sources

- [Databricks provider](https://airflow.apache.org/docs/apache-airflow-providers-databricks/stable/)
- [DatabricksWorkflowTaskGroup](https://airflow.apache.org/docs/apache-airflow-providers-databricks/stable/operators/workflow.html)
- [Databricks Asset Bundles](https://docs.databricks.com/en/dev-tools/bundles/index.html)

→ Next: [22 — Spark family — EMR, EMR Serverless, Dataproc, Glue](22_spark_emr_dataproc_glue.md)


\newpage

# 22 — Spark family: EMR, EMR Serverless, EMR-on-EKS, Dataproc, HDInsight, AWS Glue

## Why this module exists

Pushing compute to Spark (vs running it in Airflow workers) is the canonical "don't transform in Python" pattern for big jobs.

---

## 1. AWS EMR

Operators in `apache-airflow-providers-amazon`:

| Operator | Use |
|---|---|
| `EmrCreateJobFlowOperator` | Spin up an EMR cluster |
| `EmrAddStepsOperator` | Add Spark steps to cluster |
| `EmrStepSensor` | Wait for step completion |
| `EmrTerminateJobFlowOperator` | Kill cluster |
| `EmrServerlessStartJobOperator` | EMR Serverless — preferred for ad-hoc |
| `EmrContainerOperator` | EMR on EKS — submit jobs to managed K8s |

The "create cluster → add steps → terminate" pattern is the classic EMR-on-EC2 flow. For setup/teardown semantics (module 05), wrap in setup/teardown.

For modern AWS Spark: **EMR Serverless** or **EMR on EKS** beats EC2.

```python
from airflow.providers.amazon.aws.operators.emr import EmrServerlessStartJobOperator

spark_job = EmrServerlessStartJobOperator(
    task_id="run_etl",
    application_id="00abcd...",                  # pre-created EMR Serverless app
    execution_role_arn="arn:aws:iam::...:role/emr-serverless-job",
    job_driver={
        "sparkSubmit": {
            "entryPoint": "s3://myorg-jobs/etl.py",
            "sparkSubmitParameters": "--conf spark.executor.cores=4",
        },
    },
    configuration_overrides={
        "monitoringConfiguration": {
            "s3MonitoringConfiguration": {"logUri": "s3://myorg-emr-logs/"},
        },
    },
    deferrable=True,
)
```

---

## 2. EMR on EKS

For shops already on EKS: run Spark via EMR on EKS — get EKS's elasticity + IAM model.

```python
from airflow.providers.amazon.aws.operators.emr import EmrContainerOperator

spark_step = EmrContainerOperator(
    task_id="run_etl",
    virtual_cluster_id="virt-cluster-id",
    execution_role_arn="arn:aws:iam::...:role/emr-on-eks-job",
    release_label="emr-7.0.0-latest",
    job_driver={"sparkSubmitJobDriver": {"entryPoint": "s3://..."}},
    deferrable=True,
)
```

Alternative: **SparkKubernetesOperator** (via Spark-on-K8s operator) for non-EMR. Less managed.

---

## 3. GCP Dataproc

Provider: `apache-airflow-providers-google`.

| Operator | Use |
|---|---|
| `DataprocSubmitJobOperator` | Submit job to existing Dataproc cluster (Jobs v1 API) |
| `DataprocCreateBatchOperator` | **Dataproc Serverless** — preferred path |
| `DataprocCreateClusterOperator` | Spin up cluster |
| `DataprocDeleteClusterOperator` | Kill cluster |

```python
from airflow.providers.google.cloud.operators.dataproc import DataprocCreateBatchOperator

spark_batch = DataprocCreateBatchOperator(
    task_id="spark_batch",
    project_id="my-proj",
    region="us-central1",
    batch_id="etl-{{ ds_nodash }}",
    batch={
        "pyspark_batch": {
            "main_python_file_uri": "gs://myorg-jobs/etl.py",
        },
        "runtime_config": {"version": "2.2"},
        "environment_config": {
            "execution_config": {
                "service_account": "dataproc-job@my-proj.iam.gserviceaccount.com",
                "subnetwork_uri": "projects/.../subnetworks/dataproc-subnet",
            },
        },
    },
    deferrable=True,
)
```

Dataproc Serverless = no cluster management. The right default.

---

## 4. Azure HDInsight / HDInsight on AKS

Legacy HDInsight is fading; **HDInsight on AKS** (GA 2024) is the newer path. Provider: `apache-airflow-providers-microsoft-azure`.

For most Azure Spark: people use Databricks. HDInsight is for shops that picked it pre-Databricks-Azure-launch.

---

## 5. AWS Glue

| Operator | Use |
|---|---|
| `GlueJobOperator` | Run a Glue Spark/Python job |
| `GlueJobSensor` | Wait for completion |
| `GlueCrawlerOperator` | Run a crawler |
| `GlueDataBrewStartJobOperator` | Run DataBrew |
| `GlueDataQualityRulesetEvaluationRunOperator` | Run a Glue Data Quality ruleset |

Glue ETL jobs are Spark + AWS-managed. Airflow's role: trigger + monitor.

```python
from airflow.providers.amazon.aws.operators.glue import GlueJobOperator

glue_etl = GlueJobOperator(
    task_id="glue_etl",
    job_name="my_etl_job",
    script_location="s3://myorg-glue/scripts/etl.py",
    iam_role_name="GlueETLRole",
    create_job_kwargs={"GlueVersion": "4.0", "NumberOfWorkers": 10},
    deferrable=True,
)
```

---

## 6. SparkKubernetesOperator (generic)

For Spark on K8s without EMR/Dataproc:

```python
from airflow.providers.cncf.kubernetes.operators.spark_kubernetes import SparkKubernetesOperator

spark = SparkKubernetesOperator(
    task_id="spark",
    application_file="spark-app.yaml",                # SparkApplication CRD manifest
    namespace="spark-jobs",
    kubernetes_conn_id="kubernetes_default",
)
```

Requires the [Spark Operator](https://github.com/GoogleCloudPlatform/spark-on-k8s-operator) installed. For shops self-managing Spark on K8s.

---

## 7. Decision tree

```
Need Spark on AWS?
  → Modest scale, intermittent: EMR Serverless
  → Already on EKS: EMR on EKS
  → Long-lived ETL: EMR on EC2
  → Lake-house centric: Databricks (module 21)

Need Spark on GCP?
  → Dataproc Serverless (Batch)
  → Or Databricks on GCP

Need Spark on Azure?
  → Databricks on Azure (most common)
  → HDInsight on AKS (rarely greenfield)

Need pure K8s Spark?
  → SparkKubernetesOperator with Spark Operator
```

---

## 8. The Capital One context

Capital One uses EMR (their Topic 04 references include EMR jobs orchestrating data into Snowflake), Databricks, and Glue. Airflow as the orchestrator above all of them.

The decision criterion Cap One favors: **serverless > managed > cluster**. EMR Serverless and Glue over EMR-on-EC2 where workloads fit.

---

## Sanity check

1. EMR Serverless vs EMR on EKS vs EMR on EC2 — when does each fit?
2. Dataproc Serverless replaces what older Dataproc pattern?
3. `SparkKubernetesOperator` requires what to be installed in the cluster?
4. AWS Glue + Airflow — Airflow's role is what?
5. Capital One favors what compute model for Spark?

---

## Sources

- [Amazon provider — EMR operators](https://airflow.apache.org/docs/apache-airflow-providers-amazon/stable/operators/emr/)
- [Amazon provider — EMR Serverless](https://airflow.apache.org/docs/apache-airflow-providers-amazon/stable/operators/emr/emr_serverless.html)
- [Google provider — Dataproc](https://airflow.apache.org/docs/apache-airflow-providers-google/stable/operators/cloud/dataproc.html)
- [Amazon provider — Glue](https://airflow.apache.org/docs/apache-airflow-providers-amazon/stable/operators/glue.html)
- [Spark Operator for K8s](https://github.com/GoogleCloudPlatform/spark-on-k8s-operator)

→ Next: [23 — ML platform operators](23_ml_platforms.md)


\newpage

# 23 — ML platform operators: SageMaker, Vertex AI, Azure ML, MLflow, Kubeflow Pipelines

## Why this module exists

Airflow as orchestrator of ML training/serving systems. AWS has the deepest providers; Azure ML is thinnest.

---

## 1. AWS SageMaker

Provider: `apache-airflow-providers-amazon`. The richest ML operator suite.

| Operator | Use |
|---|---|
| `SageMakerProcessingOperator` | Run a Processing Job (data prep) |
| `SageMakerTrainingOperator` | Training job |
| `SageMakerTuningOperator` | Hyperparameter tuning |
| `SageMakerModelOperator` | Register a model |
| `SageMakerEndpointConfigOperator` + `SageMakerEndpointOperator` | Deploy real-time endpoint |
| `SageMakerTransformOperator` | Batch transform |
| `SageMakerStartPipelineOperator` | Trigger an SM Pipelines pipeline (preferred for compound flows) |
| `SageMakerPipelineSensor` | Wait for SM Pipelines run |
| `SageMakerAutoMLOperator` | Autopilot job |

```python
from airflow.providers.amazon.aws.operators.sagemaker import SageMakerStartPipelineOperator

trigger_sm_pipeline = SageMakerStartPipelineOperator(
    task_id="trigger_sm",
    pipeline_name="prod-ml-pipeline",
    pipeline_params={"InputDataLocation": "s3://myorg/data/{{ ds }}/"},
    deferrable=True,
)
```

For Capital One MLE work: Airflow triggers SageMaker Pipelines; SM Pipelines runs the multi-step ML flow internally; Airflow waits.

---

## 2. GCP Vertex AI

Provider: `apache-airflow-providers-google`.

| Operator | Use |
|---|---|
| `CustomTrainingJobOperator` | Train via custom container |
| `CreatePipelineJobOperator` | Run Vertex AI Pipeline |
| `BatchPredictionJobOperator` | Batch predictions |
| `ModelDeployOperator` | Deploy to endpoint |
| `AutoMLTrainingJobOperator` | AutoML |
| `GenerativeModelGenerateContentOperator` (2024+) | Vertex AI Generative |

```python
from airflow.providers.google.cloud.operators.vertex_ai.custom_job import CreateCustomContainerTrainingJobOperator

train = CreateCustomContainerTrainingJobOperator(
    task_id="train",
    project_id="my-proj",
    region="us-central1",
    display_name="train-{{ ds_nodash }}",
    container_uri="gcr.io/my-proj/train:1.0",
    machine_type="a3-highgpu-8g",
    accelerator_type="NVIDIA_H100_80GB",
    accelerator_count=8,
    args=["--epochs=10"],
)
```

---

## 3. Azure ML

Provider: `apache-airflow-providers-microsoft-azure`. Thinner.

| Operator | Use |
|---|---|
| `AzureMachineLearningOperator` | Submit a job (limited) |

For richer integration: use `PythonOperator` calling Azure ML SDK directly. Or `KubernetesPodOperator` with an Azure ML-aware container.

---

## 4. MLflow

No first-class operators. Use `PythonOperator` + `mlflow` client:

```python
@task
def log_to_mlflow(metrics: dict):
    import mlflow
    mlflow.set_tracking_uri("databricks")          # or http://mlflow.internal
    with mlflow.start_run(run_name="airflow-{{ run_id }}"):
        mlflow.log_metrics(metrics)
```

Lineage challenge: MLflow runs aren't automatically linked to Airflow runs. Add the run_id as a tag.

---

## 5. Kubeflow Pipelines (KFP)

Provider: `apache-airflow-providers-cncf-kubernetes` includes KFP integration patterns.

The common pattern: KFP runs inside K8s; Airflow triggers via the KFP SDK in a PythonOperator. Less common than SageMaker/Vertex.

---

## 6. HuggingFace + Airflow

No first-class. Common pattern: `KubernetesPodOperator` launching a HF Transformers training container.

---

## 7. The Capital One pattern

For ML at Capital One:

```
Airflow DAG (data prep) → Step Functions → SageMaker Pipelines (train) → S3 (model) → KServe deploy via ArgoCD
```

Airflow lives in data engineering (ETL into curated layer). The ML side runs on Step Functions + SageMaker. Airflow's role is at the **data preparation boundary**, not the ML training/serving spine.

This is the architect-grade nuance: don't shoehorn Airflow into ML orchestration when Step Functions is the better fit on AWS.

---

## 8. Anti-patterns

| Anti-pattern | Fix |
|---|---|
| Training in Airflow PythonOperator | Use SageMaker / Vertex / Databricks operator |
| Long-running sync training waits | `deferrable=True` |
| Hardcoded model artifact paths | Templated paths via XCom (small path strings) |
| No model lineage | OpenLineage emit + MLflow tags |

---

## Sanity check

1. SageMaker has the deepest provider. What does `SageMakerStartPipelineOperator` wrap?
2. Vertex AI training — what's the canonical operator for custom containers?
3. Azure ML provider is thinnest. What's the pragmatic workaround?
4. MLflow integration — what lineage challenge needs explicit work?
5. Capital One: where does Airflow fit in their ML stack?

---

## Sources

- [Amazon provider — SageMaker](https://airflow.apache.org/docs/apache-airflow-providers-amazon/stable/operators/sagemaker/)
- [Google provider — Vertex AI](https://airflow.apache.org/docs/apache-airflow-providers-google/stable/operators/cloud/vertex_ai.html)
- [Microsoft Azure provider — ML](https://airflow.apache.org/docs/apache-airflow-providers-microsoft-azure/stable/)
- [MLflow Tracking](https://mlflow.org/docs/latest/tracking.html)

→ Next: [24 — Airflow + dbt (Cosmos)](24_dbt_airflow.md)


\newpage

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


\newpage

# 25 — Alternative orchestrators: Prefect, Dagster, Argo, Mage, Flyte, Step Functions, Databricks Workflows, Snowflake Tasks, ADF, Temporal

> *"The architect-grade insight: knowing when NOT to pick Airflow."*

## Why this module exists

Airflow is right for many things and wrong for others. This module is the honest comparison.

---

## 1. Prefect 3

- Rewrite of Prefect engine 2024.
- Pythonic (decorators).
- Strong cloud offering (Prefect Cloud).
- **Better at**: ad-hoc / event-driven workflows; modern Python ergonomics; pricing for small-medium teams.
- **Worse at**: ecosystem breadth (fewer providers); operator-grade auditability.

When to pick: Python-first shop, modern data stack, want lower ops than self-hosted Airflow.

---

## 2. Dagster

- Asset-centric model **from the start** (predates Airflow Datasets).
- Strong typing of inputs/outputs.
- Dagster+ cloud offering.
- Excellent lineage and observability.
- **Better at**: data platforms designed asset-first; rich UI for lineage.
- **Worse at**: classic ETL with many heterogeneous operators (smaller provider ecosystem).

When to pick: greenfield data platform, lineage-first design, willing to invest in Dagster patterns.

---

## 3. Argo Workflows

- CNCF Graduated.
- **YAML/CUE-based** workflow definitions.
- **K8s-native** — workflows are CRs; tasks are pods.
- Used heavily for ML / data pipelines on K8s.
- **Better at**: K8s-first shops; pure pipeline-of-pods; fits with Argo CD / Events ecosystem.
- **Worse at**: Python ergonomics; rich operator ecosystem.

When to pick: K8s-native shop, ML pipelines as DAGs of containers, want CNCF-aligned tooling.

---

## 4. Mage AI

- Newer entrant. Notebook-as-pipeline UI.
- Python + SQL.
- **Better at**: data engineer with notebook habits.
- **Worse at**: scale; smaller community; uncertain sustainability.

When to pick: small team, notebook-heavy workflow, willing to take adoption risk.

---

## 5. Flyte

- From Lyft. CNCF Incubating.
- **Strongly typed** Python pipelines.
- K8s-native execution.
- ML-leaning use cases.
- **Better at**: typed ML pipelines; reproducibility-first; tight K8s integration.
- **Worse at**: classic ETL ergonomics; smaller ecosystem.

When to pick: ML-platform team building typed reproducible pipelines on K8s.

---

## 6. AWS Step Functions

- **JSON state machines** (or CDK / SAM / Terraform definitions).
- AWS-native; serverless.
- **Capital One's published MLOps spine** uses Step Functions.
- **Better at**: AWS-native serverless workflows; integrates with every AWS service; cheap at low volume; auditable.
- **Worse at**: Python ergonomics; non-AWS systems; complex DAG visualization.

When to pick: AWS-only shop, simple-to-medium complexity, serverless economics matter.

For Capital One: **Step Functions is the right answer for ML pipelines** even if Airflow remains for data engineering.

---

## 7. Databricks Workflows / Lakeflow Jobs

- Built into the Databricks Lakehouse.
- JSON / UI / SDK.
- **Better at**: pipelines fully inside Databricks; cheaper DBU rate; tight Unity Catalog lineage.
- **Worse at**: orchestrating non-Databricks systems.

When to pick: pipeline is 100% Databricks; lakehouse-native.

---

## 8. Snowflake Tasks/Streams

- Inside-Snowflake DAGs of SQL.
- **Better at**: SQL transformations inside the warehouse; no external orchestrator needed.
- **Worse at**: anything outside Snowflake.

When to pick: warehouse-only data platform; transformation logic is SQL.

---

## 9. Azure Data Factory / Synapse Pipelines / Fabric Pipelines

- Microsoft-native low-code orchestration.
- **Better at**: drag-and-drop pipelines; Azure-service integrations; non-engineer users.
- **Worse at**: code-first ergonomics; reproducibility.

When to pick: Azure-only shop with mixed-skill users.

---

## 10. Temporal

- Workflow engine (different category).
- Code in Go / TypeScript / Python / Java.
- **Better at**: long-running stateful workflows (sagas, payment processing, user journeys).
- **Worse at**: data pipelines (wrong category).

When to pick: business workflows that span days/weeks with retries (orders, KYC, claims). Not data pipelines.

---

## 11. The 9-criteria decision matrix

| | Airflow 2/3 | Prefect 3 | Dagster | Argo | Step Functions | DBX Workflows |
|---|---|---|---|---|---|---|
| Python ergonomics | ✅ | ✅✅ | ✅✅ | ❌ (YAML) | ❌ (JSON) | ❌ (JSON) |
| K8s-native | ⚠️ | ⚠️ | ⚠️ | ✅✅ | N/A | N/A |
| Asset/lineage-first | ⚠️ (3.0) | ✅ | ✅✅ | ❌ | ⚠️ | ✅ (UC) |
| Provider ecosystem | ✅✅ | ⚠️ | ⚠️ | ❌ | AWS only | DBX only |
| Multi-tenancy | ⚠️ | ⚠️ | ✅ | ✅ | ✅ | ✅ |
| Regulated audit | ✅ | ⚠️ | ✅ | ⚠️ | ✅✅ | ✅ |
| Cost (steady state) | $$ | $$ | $$$ | $ | $ | $$$ |
| Multi-cloud | ✅ | ✅ | ✅ | ✅ | AWS | DBX |
| Community size | ✅✅ | ✅ | ✅ | ✅ | N/A | N/A |

---

## 12. Capital One verdict

Step Functions is the explicit answer for the **ML serving spine** + complex AWS workflows. Airflow lives at the **data engineering boundary** (warehouse loads, dbt orchestration).

For a Sr Lead candidate, the interview-defining framing:

> "I'd start by asking what's primary: warehouse-centric ETL with many provider integrations (Airflow), AWS-native serverless workflows with auditability (Step Functions), asset-first lineage (Dagster), or K8s-pure ML pipelines (Argo). At Capital One, I'd default to Step Functions for ML and Airflow for data engineering — exactly the pattern your engineering blog has published."

That answer demonstrates the architect-grade thinking the role rewards.

---

## Sanity check

1. Three scenarios where Step Functions beats Airflow on AWS.
2. Dagster's "asset-centric from the start" — what does that change in practice vs Airflow?
3. Argo Workflows — language? Execution model?
4. Temporal is a workflow engine, not an orchestrator. What's the practical difference?
5. Capital One's ML spine uses what, and why?

---

## Sources

- [Prefect 3](https://docs.prefect.io/3.0/)
- [Dagster](https://docs.dagster.io/)
- [Argo Workflows](https://argo-workflows.readthedocs.io/)
- [Mage AI](https://docs.mage.ai/)
- [Flyte](https://flyte.org/)
- [AWS Step Functions](https://docs.aws.amazon.com/step-functions/)
- [Databricks Workflows](https://docs.databricks.com/workflows/)
- [Temporal](https://docs.temporal.io/)

→ Next: [26 — CI/CD for DAGs](26_cicd_dags.md)


\newpage

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


\newpage

# 27 — SRE: stuck queues, scheduler heartbeat, zombie tasks, sql_alchemy_pool, sensor deadlocks

## Why this module exists

The Airflow on-call playbook. Memorize the symptoms and root causes.

---

## 1. Symptom: Scheduler heartbeat missing > 60s

Causes:
- Scheduler OOM.
- DAG parse taking too long (`dagbag_import_timeout` exceeded).
- Postgres slow / connection pool exhausted.
- Triggerer or worker holding a lock.

Triage:
- `kubectl logs <scheduler-pod>` / CloudWatch scheduler logs.
- Check Postgres connection count.
- Check `dag_processing.last_runtime.{dag_id}` metric.

Fix:
- Restart scheduler.
- Find the slow DAG (heavy top-level import); move imports into tasks.
- Increase scheduler resources.

---

## 2. Symptom: Tasks queued forever (Celery)

Causes:
- All workers dead / unhealthy.
- Redis / RabbitMQ broker unreachable.
- Worker pod startup failed.

Triage:
- `flower` UI / Celery inspect commands.
- Worker pod logs.
- Broker (Redis) connection status.

Fix:
- Restart workers.
- Reach broker.
- Increase `worker_concurrency` if workers are healthy but slot-starved.

---

## 3. Symptom: Tasks queued forever (KubernetesExecutor)

Causes:
- Pods stuck `Pending` — no node capacity / scheduling constraint unmet.
- Karpenter / Cluster Autoscaler not scaling up.
- Wrong PSA on the namespace blocking the pod.
- `imagePullBackOff`.

Triage:
- `kubectl get pods -n airflow -o wide`.
- `kubectl describe pod <pod>`.

Fix:
- Resolve pod scheduling failure.

---

## 4. Symptom: Zombie tasks

Task marked `running` but worker is dead. Cleanup:
- `airflow tasks states-for-dag-run ...`.
- Mark as failed: scheduler does this on detect (`scheduler.zombie_task_check_threshold`).

Prevention:
- Worker liveness probes.
- Save state to S3 mid-run; idempotent restart.

---

## 5. Symptom: DAG run never triggers

Causes:
- Wrong `start_date` (future).
- `paused=True` on the DAG.
- `catchup=False` skipped intermediate intervals.
- Schedule misconfigured.

Triage:
- `airflow dags details <dag_id>`.
- UI DAG details → schedule info.

Fix: unpause; correct schedule.

---

## 6. Symptom: Connection pool exhausted

Symptom: `sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 10 reached`.

Cause: Postgres connection pool too small.

Fix:
```ini
[database]
sql_alchemy_pool_size = 30
sql_alchemy_max_overflow = 20
sql_alchemy_pool_pre_ping = True
sql_alchemy_pool_recycle = 1800
```

For multiple schedulers: each opens up to `pool_size + max_overflow`. Postgres `max_connections` must accommodate.

---

## 7. Symptom: Sensor deadlock (worker starvation)

Many `poke`-mode sensors holding worker slots.

Fix:
- Switch all to `deferrable=True` (module 07).
- Or `mode="reschedule"` as second-best.

---

## 8. Symptom: Worker OOM

```
Killed (signal 9)
```

Causes:
- Heavy task pulled too much data into memory (DataFrame in worker).
- Multiple parallel tasks on same worker each hitting memory limit.

Fix:
- Increase worker memory.
- Push transforms to warehouse (don't process in worker).
- For K8sExecutor: per-task `pod_override` with explicit resources.

---

## 9. Symptom: Scheduler slow / heartbeat-late

Causes:
- Too many DAGs (1000+).
- Heavy top-level imports.
- Large `min_file_process_interval`.
- Slow Postgres (large `xcom` table, no compaction).

Fix:
- Move top-level imports into tasks.
- Set `dag_dir_list_interval = 300` (parse every 5 min, not 30s).
- Set `min_file_process_interval = 30` (don't re-parse the same file every loop).
- Compact metadata DB (`VACUUM FULL` on xcom).
- More schedulers / more CPU per scheduler.

---

## 10. Symptom: Migration failed (Airflow upgrade)

Causes:
- DB schema migration timeout (large `xcom` / `task_instance` tables).
- Provider package version conflict.

Fix:
- Run `airflow db migrate` manually with longer timeout.
- Restore from backup if catastrophic.
- Use **backward-compatible providers** during upgrade window.

For prod: **dry-run migrations on a copy of prod DB** before the real upgrade.

---

## 11. The on-call dashboard

Minimum panels:
- Scheduler heartbeat staleness.
- DAG parse times (top 20 slowest).
- Queue depth (Celery / K8s).
- Postgres connections + CPU.
- Task duration p99 deltas (regression).
- DAG failure counts (24h).
- Triggers pending.

Alert thresholds in module 14.

---

## 12. The post-mortem template

For every Airflow incident:

1. Timeline (with timestamps).
2. Root cause.
3. Detection lag (how quickly we knew).
4. Impact (DAGs affected, downstream consumers).
5. Remediation (immediate fix, follow-ups).
6. Prevention (process, code, monitor).

For regulated finance: post-mortems are a SOC2 / FFIEC artifact.

---

## Sanity check

1. Scheduler heartbeat missing > 60s — three causes and the triage path.
2. Zombie task — how does Airflow detect it?
3. `sql_alchemy_pool_size = 5` (default) — when does this start hurting?
4. The deferrable-everywhere rule replaces what older sensor mode pattern?
5. Worker OOM — three structural fixes (not "give it more RAM").

---

## Sources

- [Airflow administration & deployment](https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/index.html)
- [Scheduler tuning](https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/scheduler.html)
- [Database backends](https://airflow.apache.org/docs/apache-airflow/stable/howto/set-up-database.html)

→ Next: [28 — Cost & scaling](28_cost_scaling.md)


\newpage

# 28 — Cost & scaling: KEDA, deferrable, right-sizing, multi-tenant

## Why this module exists

A typical mid-sized Airflow runs $5-50K/mo. Half of that is usually waste — idle workers, oversized envs, poke-mode sensors. This module is the cost lever set.

---

## 1. The cost levers

| Lever | Saving | Effort |
|---|---|---|
| Switch sensors to `deferrable=True` | 30-70% worker hours | Low |
| KEDA autoscale workers (Celery) | 40-60% baseline | Medium |
| Right-size MWAA env class | 30% | Low |
| `MinWorkers = 1` (vs default higher) | 20% | Low |
| Move heavy work to EMR Serverless / Glue / SageMaker | 50%+ | Medium-high |
| Aggressive log retention | 10-30% CloudWatch cost | Low |
| Disable DEBUG logs | 50% CloudWatch | Low |
| Cosmos with `dbt_manifest` (not file scan) | Lower scheduler load | Low |

---

## 2. Deferrable everywhere = the biggest win

A typical ETL has 10-50 sensors waiting for data. With `mode="poke"` each holds a worker slot for hours. With `deferrable=True` they cost a tiny fraction in the Triggerer.

Real numbers: a shop with 30 hourly sensors-each-waiting-1-hour-with-`poke`-mode = 30 worker slots permanently occupied. Switching to deferrable: 30 sensors managed by a single Triggerer pod.

---

## 3. KEDA on Celery workers

Already covered (module 15). Scale to zero off-hours; scale up on queue depth.

```yaml
# excerpt
minReplicaCount: 0
maxReplicaCount: 20
triggers:
  - type: postgresql
    metadata:
      query: SELECT count(*) FROM task_instance WHERE state='queued'
      targetQueryValue: '4'
```

Saves the night/weekend cost of idle workers.

---

## 4. K8sExecutor right-sizing

Per-task `pod_override`. Don't request 4 CPU + 8GB for tasks that need 0.5 CPU + 512 MB.

For LARGE task envelopes: separate Karpenter pool (cheap CPU vs expensive GPU). Scale on demand.

---

## 5. MWAA cost optimization

- `MinWorkers = 1`.
- `MaxWorkers` tuned to peak DAG concurrency.
- Smallest env class that meets scheduler need.
- Webserver in `PRIVATE_ONLY` doesn't reduce cost but saves NAT egress.
- CloudWatch log retention: 30 days (or whatever compliance allows); export to S3 Glacier for longer.
- Set `WARN` level on `airflow-DAGProcessing` log group (the chattiest).

---

## 6. Composer cost optimization

- Composer 3 with smallest baseline.
- Scale-to-near-zero off-hours.
- CMEK adds cost but is non-negotiable for regulated; ack it.
- Use the cluster outside the customer project mode (reduces customer K8s cost).

---

## 7. Astro cost optimization

- Right-size AU per deployment.
- Pause dev/staging envs when not in use.
- Image-bake DAGs (no git-sync overhead).
- Use Astro's "smart caching" features.

---

## 8. Compute placement

The biggest waste is doing transforms in Airflow:

```python
# COST: pulls 100M rows into worker RAM
df = pd.read_sql("SELECT * FROM huge_table", conn)
df = df.groupby(...).agg(...)
df.to_sql("agg_table", conn)
```

```python
# RIGHT: warehouse does the work
SnowflakeOperator(sql="""
  INSERT INTO agg_table
  SELECT ... FROM huge_table GROUP BY ...
""")
```

Snowflake's compute is way cheaper than your Airflow worker for tabular transforms.

---

## 9. Multi-tenancy patterns

Three approaches:

### 9.1 One Airflow per team

Each team has its own env (MWAA / Astro deployment / K8s namespace).

Pros: complete isolation; per-team cost; per-team upgrade cadence.
Cons: N×ops; idle envs.

### 9.2 One shared Airflow

Single env; namespaces / pools / per-DAG access control / per-task K8s SA.

Pros: cost-efficient; ops once.
Cons: noisy neighbors; harder upgrades; one DAG can stall scheduler for all.

### 9.3 Hybrid

Critical / regulated DAGs on dedicated env; "the rest" on shared.

For Capital One: hybrid is plausible — finance team has dedicated, generic data eng shares.

---

## 10. The architect-grade cost dashboard

- $ per DAG (with cost-allocation tags / labels).
- $ per team.
- Worker utilization (% of slots used).
- Triggerer load (triggers per second).
- Compute placement breakdown — Airflow worker / EMR / Snowflake / Databricks.

For Capital One–style FinOps: Cloud Custodian rule "DAGs without `team` and `cost-center` tags fail policy."

---

## Sanity check

1. Deferrable-everywhere — what's the saving on a typical sensor-heavy DAG?
2. KEDA + Celery — what does scale-to-zero off-hours actually save?
3. The "transform in Python" anti-pattern's cost lever — push transforms to where?
4. One Airflow per team vs one shared — describe trade-offs.
5. Cloud Custodian rule for DAG cost-allocation tagging — what's the policy?

---

## Sources

- [KEDA](https://keda.sh/docs/2.13/scalers/postgresql/)
- [Airflow Helm chart KEDA support](https://airflow.apache.org/docs/helm-chart/stable/keda.html)
- [MWAA pricing optimization](https://docs.aws.amazon.com/mwaa/latest/userguide/mwaa-environment-pricing.html)

→ Next: [29 — Multi-tenancy patterns](29_multi_tenancy.md)


\newpage

# 29 — Multi-tenancy patterns: namespaced executors, one-Airflow-per-team vs shared

## Why this module exists

Org-shape determines architecture. This module covers the three Airflow multi-tenancy patterns + the controls each requires.

---

## 1. Pattern A: One Airflow per team

Each team has a dedicated MWAA env / Composer env / Astro deployment / Helm install.

**Pros**:
- Hard isolation (separate cluster, separate metadata DB).
- Per-team budget / cost allocation easy.
- Per-team upgrade cadence.
- DAG author = cluster admin is bounded to the team.

**Cons**:
- N envs to operate.
- N idle baselines.
- N upgrade paths to track.

When right: regulated finance with strong separation requirements; teams with very different needs (one team on 2.7, one on 3.0).

---

## 2. Pattern B: One shared Airflow

Single env serves all teams. Use:

- **Namespaces** in K8sExecutor (one ns per team).
- **Pools** to limit per-team concurrency.
- **Per-DAG `access_control`** (FAB roles).
- **Per-task IRSA/WIF/Entra SA** (different cloud identity per team).
- **NetworkPolicy** per team namespace.
- **Tag-based cost allocation** (`team`, `cost-center`).

**Pros**: single env, single ops burden, cheaper.

**Cons**:
- DAG-author-as-cluster-admin problem widens (any DAG can take down scheduler).
- Upgrade is org-wide.
- Pool contention.

When right: many teams with low isolation needs; org with strong code-review culture.

---

## 3. Pattern C: Hybrid

Sensitive / regulated DAGs on dedicated env; remainder on shared.

For Capital One: finance team or trading-systems team gets dedicated; data eng + ML teams share.

---

## 4. The K8sExecutor + per-task SA pattern

The strongest in-cluster tenancy:

```python
@dag(...)
def team_alpha_dag():
    @task(executor_config={
        "pod_override": V1Pod(spec=V1PodSpec(
            service_account_name="team-alpha-tasks",     # IRSA → team-alpha role
            namespace="airflow-team-alpha",
        )),
    })
    def secure_task(): ...
```

Each team's DAGs run pods with team-specific SAs in team-specific namespaces with team-specific IAM. The scheduler is shared but task execution is isolated.

This is the modern multi-tenant model.

---

## 5. RBAC + access_control

```python
@dag(
    access_control={
        "team-alpha-developers": {"can_read", "can_edit", "can_delete"},
        "team-alpha-viewers":    {"can_read"},
    },
    ...
)
def alpha_dag(): ...
```

Combined with OIDC group → FAB role mapping (module 09), users see only DAGs they're entitled to.

---

## 6. Pool + queue isolation

```yaml
pools:
  - name: team-alpha-snowflake
    slots: 5
  - name: team-bravo-snowflake
    slots: 10

queues:
  - team-alpha
  - team-bravo
```

Tasks declare `pool=team-alpha-snowflake` + `queue=team-alpha`. K8sExecutor can run team-alpha tasks on dedicated worker nodes (via node selector).

---

## 7. The shared-Airflow security checklist

For shared:
- [ ] K8sExecutor (not Celery).
- [ ] Per-team namespace.
- [ ] Per-team K8s SA + cloud IAM binding.
- [ ] NetworkPolicy default-deny per namespace.
- [ ] Per-team DAG folder in shared bucket / git repo.
- [ ] Per-team OIDC group → FAB role mapping.
- [ ] Per-team `access_control` on DAGs.
- [ ] Pool per team's resource budget.
- [ ] PR review by team-aware reviewer.
- [ ] CI lints for forbidden patterns per team.
- [ ] Cost allocation tags enforced via Kyverno.
- [ ] Audit log per-team segments.

---

## 8. Capital One context

Capital One likely runs **hybrid**:

- Critical regulated DAGs (compliance reporting, model risk) → dedicated MWAA env.
- General data eng → shared MWAA / Astro / EKS-Helm Airflow.

The architectural principle: **isolate by blast radius, not by org chart.**

---

## 9. Multi-tenancy and Airflow 3.0

Airflow 3.0's Task SDK + multi-cluster scheduler are designed for multi-tenancy:

- Tasks run with scoped permissions.
- Multiple teams' DAGs can share a scheduler without sharing execution context.
- Easier upgrades (DAGs less tied to specific Airflow version).

This is the architectural direction. For new shared Airflow in 2026+: design for 3.0 even if you start on 2.10.

---

## Sanity check

1. One Airflow per team vs one shared — three trade-offs.
2. K8sExecutor + per-task SA — what does this give multi-tenancy?
3. `access_control` on DAGs — how does this interact with FAB OIDC groups?
4. Hybrid pattern — when do you put a DAG on the dedicated env?
5. Airflow 3.0 multi-tenancy direction — what's the Task SDK's contribution?

---

## Sources

- [Airflow security](https://airflow.apache.org/docs/apache-airflow/stable/security/index.html)
- [Per-DAG access control](https://airflow.apache.org/docs/apache-airflow/stable/security/access-control.html)
- [Airflow 3.0 design docs](https://airflow.apache.org/blog/airflow-3-0/)

→ Next: [30 — **Airflow 3.0 deep**](30_airflow_3.md)


\newpage

# 30 — Airflow 3.0 deep: Task SDK, Deadlines, multi-cluster, asset-centric, UI rewrite, DAG versioning

## Why this module exists

Airflow 3.0 (April 2025) is the biggest change since 2.0. This module covers what changed, what broke, and what to use it for.

---

## 1. Task SDK — task execution decoupled from scheduler

The headline change. Tasks now run via the **Task SDK** — a clean Python interface that:

- Doesn't require the full DAG file to be loaded.
- Doesn't require direct metadata DB access.
- Communicates with the scheduler via a defined API (Task Execution Interface).
- Can run in completely isolated containers / processes.

For the architect: this **finally** addresses "DAG authors == cluster admins." A 3.0 task can run with scoped permissions; an RCE in a task doesn't grant scheduler access.

---

## 2. Multi-cluster scheduler

3.0 supports federated execution across clusters. One "control" Airflow can dispatch tasks to multiple "worker" clusters:

- Worker clusters can be in different VPCs, accounts, even clouds.
- Audit trail centralized.
- DAGs declare which cluster they want execution on.

For Capital One: multi-region Airflow becomes practical. For Optum: cross-environment workflows.

---

## 3. Deadlines — replacing SLAs

```python
@dag(deadline_alert=timedelta(hours=3), ...)
def my_pipeline():
    @task(deadline=timedelta(hours=1))
    def critical_task(): ...
```

Deadlines are richer than 2.x SLAs:
- Per-task and per-DAG.
- Structured outcomes (timeout vs late completion).
- Better callbacks.
- `sla_miss_callback` deprecated.

---

## 4. Assets (renamed from Datasets)

The Dataset concept is generalized into **Assets** with:

- Richer metadata.
- Asset conditions (`AND`, `OR`, custom).
- Asset events with structured payloads.
- Asset versioning.

```python
@asset(uri="snowflake://prod.curated.sales")
def sales_curated():
    ...
```

Asset-first pipelines are the direction Dagster pioneered; Airflow 3.0 catches up.

---

## 5. UI rewrite — React

The Flask-AppBuilder UI (which felt 2017-ish) is replaced with a React-based UI:

- Faster.
- Modern look.
- Better task-instance debugging.
- Better lineage visualization.
- Mobile-friendly.

FAB Auth Manager remains for auth; only the UI is rewritten.

---

## 6. DAG Versioning

A DAG can have multiple versions running simultaneously:

- v1 handles in-flight runs.
- v2 handles new runs.
- Backfill can target specific version.

Blue/green deploys become first-class.

---

## 7. Removed

- **SubDAGs** — gone. Use TaskGroups.
- **SLA misses** (the metric) — replaced by Deadlines.
- Various deprecated operators.

---

## 8. Breaking changes from 2.x

Migration concerns:

- DAG file parsing changes (top-level access to scheduler-only objects removed).
- Some Hooks/Operators have signature changes.
- `airflow.cfg` config keys renamed in places.
- Provider package versions need to be 3.0-compatible.

For 2.x users: don't expect a flag-flip upgrade. Plan for a migration project (module 31).

---

## 9. EOL of 2.x lines

- Airflow 2.10 EOL ~ April 2026 (one-year support after 3.0 release).
- 2.6 LTS continues to receive security patches.
- For prod stuck on 2.x: stay on 2.10; plan 3.x migration.

---

## 10. Managed offering status (2026-05)

- **MWAA**: 3.0 not yet supported.
- **Composer 3**: early support.
- **Azure (Fabric)**: lagging.
- **Astro**: leading; supports 3.0 first.
- **Self-host**: free to upgrade.

For early 3.0 adoption: Astro or self-host. MWAA users wait.

---

## 11. The "should I upgrade?" decision

✅ Upgrade when:
- You're starting fresh.
- You need multi-cluster.
- Deadlines matter (SLA tooling not adequate).
- Asset-first design is your direction.
- DAG versioning solves real problems.

⏸ Wait when:
- 2.10 is meeting needs.
- Provider package ecosystem lag on 3.0 (check what you depend on).
- MWAA / Composer don't support yet.

---

## 12. Architect-grade summary

Airflow 3.0 is the platform's answer to Dagster's asset-centric model and Prefect 3's modern Python ergonomics. It also addresses real security flaws (Task SDK isolation).

For interviews: knowing 3.0's direction signals you've been paying attention to the ecosystem in 2025-2026. Don't oversell adoption — it's early for most enterprises.

---

## Sanity check

1. Task SDK — what scheduler-related problem does it solve?
2. Deadlines — replacing what 2.x mechanism?
3. Assets vs Datasets — what's the conceptual change?
4. DAG versioning enables what production pattern?
5. MWAA 3.0 support status as of mid-2026?

---

## Sources

- [Airflow 3.0 announcement](https://airflow.apache.org/blog/airflow-3-0/)
- [Airflow 3.0 upgrade guide](https://airflow.apache.org/docs/apache-airflow/stable/migration-guide.html)
- [AIP-72 Deadlines](https://cwiki.apache.org/confluence/display/AIRFLOW/AIP-72)
- [AIP-74 Multi-cluster](https://cwiki.apache.org/confluence/display/AIRFLOW/AIP-74)

→ Next: [31 — Migration & version strategy](31_migration.md)


\newpage

# 31 — Migration & version strategy: 1.x → 2.x → 3.x

## Why this module exists

Most Airflow shops are on 2.x. The 2.x → 3.x migration is non-trivial. This module is the playbook.

---

## 1. 1.x → 2.x (history)

The big change in Dec 2020:
- TaskFlow API.
- HA scheduler.
- New `airflow` CLI (most subcommands moved).
- DAG serialization.

If you're still on 1.x in 2026: you have a serious upgrade debt. Sequence: 1.10 → 2.0 → 2.10. Don't skip 2.0.

---

## 2. 2.x line history (relevant for shops choosing a starting point)

- 2.0 (Dec 2020) — the rewrite.
- 2.3 (Apr 2022) — dynamic task mapping.
- 2.4 (Sep 2022) — Datasets.
- 2.6 (Apr 2023) — LTS line.
- 2.7 (Aug 2023) — setup/teardown.
- 2.8 (Dec 2023) — Auth Manager.
- 2.9 (Apr 2024) — OTel GA, OpenLineage v2.
- 2.10 (Aug 2024) — DAG-level dataset events.

For new deployments stuck on 2.x: **2.10** is current best.

---

## 3. 2.10 → 3.0 — the migration

Estimated effort: **2-12 weeks** depending on:

- Number of DAGs (each may need touch-ups).
- Custom plugins / operators (need 3.0 compatibility).
- Provider package versions used.
- Managed-offering support timeline.

---

## 4. Pre-migration checklist

- [ ] Upgrade to 2.10 first.
- [ ] Audit `dag_processing.last_runtime` — DAGs that take > 30s to parse will be slower in 3.0 (Task SDK overhead in places).
- [ ] List all custom operators / hooks; check 3.0 compat.
- [ ] List provider packages; check 3.0 versions exist.
- [ ] Identify uses of `sla_miss_callback`, SubDAGs (removed), other deprecated features.
- [ ] Inventory plugins/macros.
- [ ] Test backfill behavior for catchup DAGs.

---

## 5. Migration path

Option A: **In-place upgrade** (high risk)
- Backup metadata DB.
- Upgrade Airflow.
- Migrate schema (`airflow db migrate`).
- Re-deploy DAGs.
- Hope.

Option B: **Parallel envs** (recommended)
- Stand up new 3.0 env beside existing 2.10.
- Migrate DAGs in waves.
- Validate each wave.
- Cut over to 3.0; decommission 2.10.

Option C: **Strangler-fig with multi-cluster scheduler** (advanced)
- Use 3.0's multi-cluster to attach 2.10 cluster as a worker.
- Gradually migrate scheduling.

For prod: option B. Slower but safer.

---

## 6. Common breaking changes to address

- `SubDagOperator` → use `TaskGroup`.
- `sla_miss_callback` → Deadlines.
- Some operator signatures changed in providers.
- DAG file imports of scheduler-internal APIs may break.
- `airflow.cfg` keys renamed in places.

Run `airflow upgrade-check` (the official upgrade checker) for your DAGs. Reports incompatibilities.

---

## 7. Provider package version compatibility

Each provider has a 3.0-compatible version line. For 2.x → 3.x, you may need to also bump providers — sometimes the latest provider doesn't support old Airflow.

Example: `apache-airflow-providers-snowflake` 6.x for Airflow 3.0; 5.x for 2.10.

Pin in `requirements.txt` for the target Airflow version.

---

## 8. Test strategy

- Run the same DAGs in 2.10 and 3.0 envs.
- Compare task duration / outcome.
- Verify XCom backend compatibility.
- Verify auth migration (FAB → 3.0 auth manager).
- Verify provider operators still produce equivalent outputs.

---

## 9. Provider package upgrade discipline

Independent of Airflow version, providers have their own version churn:

- Lock provider versions in `requirements.txt`.
- Test before upgrading.
- Watch for deprecation warnings; address before they fail.

For shops on Airflow 2.x: upgrading providers regularly is the path that minimizes pain at the eventual 3.0 jump.

---

## 10. Database migrations — what to expect

`airflow db migrate` rewrites schema. Large tables (`xcom`, `task_instance`, `dag_run`, `log`) may take **hours**. Plan a maintenance window:

- Estimate row counts: `SELECT pg_size_pretty(pg_total_relation_size('xcom'))`.
- Pre-compact: `VACUUM FULL xcom` (may need downtime).
- Run migration off-hours.
- Have backup ready.

---

## 11. The migration is also a refactor opportunity

Coming up to 3.0, take the chance to:

- Move from FAB OIDC to Workload Auth Manager.
- Switch all sensors to `deferrable=True`.
- Move to image-based deploys (if not already).
- Adopt Datasets/Assets for cross-DAG flow.
- Tighten secrets backend posture.

Bundle these with the upgrade rather than as separate projects.

---

## Sanity check

1. From 1.x: what's the safe upgrade path?
2. Estimated effort for a typical 2.10 → 3.0 migration?
3. Option A (in-place) vs Option B (parallel envs) — when to pick each?
4. `airflow upgrade-check` — what does it produce?
5. Why is a metadata DB migration potentially hours-long?

---

## Sources

- [Airflow upgrade guides](https://airflow.apache.org/docs/apache-airflow/stable/installation/upgrading.html)
- [Airflow 3.0 migration guide](https://airflow.apache.org/docs/apache-airflow/stable/migration-guide.html)
- [Provider package compatibility matrix](https://airflow.apache.org/docs/apache-airflow-providers/)

→ Next: [32 — Certifications](32_certifications.md)


\newpage

# 32 — Certifications: Astronomer (Fundamentals / DAG Authoring / Operations), DEA-C01, PDE, DP-700, DP-203

> *"For the Capital One target: take **AWS DEA-C01** (covers MWAA) and **Astronomer DAG Authoring**. Skip Fundamentals (too basic). Skip Azure/GCP certs unless you're targeting those clouds."*

## Why this module exists

Airflow has no Apache-issued cert; **Astronomer** is the de facto vendor. AWS / GCP / Azure cover their managed Airflow inside broader data certs.

---

## 1. The cert landscape

| Cert | Issuer | Cost USD | Format | Time | Validity |
|---|---|---:|---|---|---|
| **Apache Airflow Fundamentals** | Astronomer | $150 | 75 MCQ, 60 min | 60 min | 2 yr |
| **DAG Authoring for Apache Airflow** | Astronomer | $150 | 75 MCQ, 60 min | 60 min | 2 yr |
| **Astronomer Certification for Airflow Operations** | Astronomer | $150 | 75 MCQ, 60 min | 60 min | 2 yr |
| **AWS DEA-C01** (Data Engineer Associate) | AWS | $150 | ~65 questions, 130 min | 130 min | 3 yr |
| **GCP Professional Data Engineer (PDE)** | GCP | $200 | ~50 q, 120 min | 120 min | 2 yr |
| **Azure DP-700** (Fabric Data Engineer) | Microsoft | $165 | ~45-65 q, 100 min | 100 min | 1 yr |
| **Azure DP-203** (Azure Data Engineer) | Microsoft | $165 | **Retired Mar 2025** | — | — |

---

## 2. Verdict for "Sr AI/ML Engineer → Capital One"

| Cert | Verdict |
|---|---|
| Apache Airflow Fundamentals | **Skip** — too basic for a Sr engineer |
| DAG Authoring | **Buy** — validates production DAG patterns |
| Astronomer Operations | **Skip-or-bundle** — useful if you operate Airflow; covered tangentially by CKA |
| AWS DEA-C01 | **Buy** — covers MWAA + broader AWS data eng |
| GCP PDE | **Skip** unless you're targeting GCP |
| Azure DP-700 | **Skip** unless Optum mandates Fabric |

Recommended 2-cert set for Capital One target: **AWS DEA-C01 + Astronomer DAG Authoring**.

---

## 3. AWS DEA-C01 (the credibility cert)

GA Nov 2023. Domains:

- Data Ingestion + Transformation (~34%).
- Data Store Management (~26%).
- Data Operations + Support (~22%).
- Data Security & Governance (~18%).

MWAA covered ~5%. Glue, Lambda, Step Functions, EMR, Athena, Redshift, S3, Kinesis, DynamoDB — all in scope.

For Capital One: more relevant than the AI Engineer (AIP-C01) cert for the data-engineering-adjacent Sr Lead AI/ML role.

Study: ~50 hours. Stéphane Maarek's course; AWS official sample questions; Tutorials Dojo practice tests.

---

## 4. Astronomer DAG Authoring (the depth cert)

Tests DAG authoring patterns specifically:
- TaskFlow API.
- Dynamic task mapping.
- Sensors + deferrable.
- XCom patterns.
- Connections + Secrets Backend.
- Datasets.
- Setup/teardown.
- Trigger rules.

Study: ~10 hours. Astronomer Academy has the official prep course (free).

Passing demonstrates **you write production-grade DAGs**. The right cert for the Lead role.

---

## 5. Astronomer Fundamentals (the "I just used Airflow once" cert)

Tests Airflow basics:
- What's a DAG.
- Operators vs Tasks.
- Basic scheduling.

Skip for a Sr engineer. Pass the DAG Authoring cert directly.

---

## 6. Astronomer Operations (the SRE cert)

Tests operating Airflow:
- Executors.
- Scaling.
- Failure modes.
- Astro-specific patterns.

Useful if you'll operate (not just author). Skip if your shop is on MWAA / Composer / Astro Hosted (you don't operate it).

---

## 7. GCP Professional Data Engineer

If you're targeting a GCP shop. Covers Cloud Composer + BigQuery + Dataproc + Dataflow + Pub/Sub.

For Capital One: not the right cert.

---

## 8. Azure DP-700 (Fabric Data Engineer)

Replaces DP-203. Covers Fabric (the new bundled platform): Lakehouse, Data Factory, Pipelines, Apache Airflow Jobs.

Skip for Capital One. Buy if Optum directs you to Fabric.

---

## 9. The 18-month plan augmented for Topic 06

If you're doing the cert plan from Topic 05's module 33 (CKAD/CKA/CKS + DOP-C02):

| Months | Cert | Topic |
|---|---|---|
| 1-2 | CKAD | K8s app dev |
| 3-5 | CKA | K8s admin |
| 6-9 | CKS | K8s security |
| 10-11 | **AWS DEA-C01** | Data eng (covers MWAA) |
| 12-13 | **Astronomer DAG Authoring** | Airflow depth |
| 14-15 | AWS DOP-C02 | DevOps (covers EKS) |
| 16-18 | AWS MLA-C01 / AIP-C01 | ML platform / GenAI |

The full set in 18 months at 3 hr/week.

---

## 10. Study resources

- **Astronomer Academy** (free) — official Airflow prep + courses.
- **Marc Lamberti's Airflow course** (Udemy, ~$15) — most popular.
- **AWS Skill Builder** — official AWS prep.
- **Tutorials Dojo** — practice exams for AWS.
- **A Cloud Guru / Pluralsight** — supplementary.

For Astronomer DAG Authoring: Marc Lamberti's course on Astronomer Academy is the canonical prep. ~10 hours of video + practice.

---

## 11. Real interview signal

Certs are the door; conversation is the room. Pair certs with:

- **Personal lab** running Airflow on K8s (CKS + Airflow combo).
- **OSS contribution** — a provider PR or a bug fix.
- **Blog post / talk** — explain a tricky pattern you implemented.

For Capital One: a personal lab showing "I deployed Airflow on EKS with IRSA + Cosmos + dbt + OpenLineage + Cosign-signed images" beats any cert.

---

## Sanity check

1. Two certs for Capital One target — which?
2. AWS DEA-C01 covers MWAA at what depth?
3. Astronomer Fundamentals — skip for a Sr engineer. Why?
4. Azure DP-203 status as of mid-2026?
5. Replacement for DP-203 covering Apache Airflow Jobs in Fabric?

---

## Sources

- [Astronomer Academy](https://academy.astronomer.io/)
- [AWS Certified Data Engineer – Associate](https://aws.amazon.com/certification/certified-data-engineer-associate/)
- [GCP Professional Data Engineer](https://cloud.google.com/certification/data-engineer)
- [Microsoft DP-700 (Fabric Data Engineer)](https://learn.microsoft.com/credentials/certifications/exams/dp-700/)
- [Marc Lamberti's Airflow course](https://marclamberti.com/)

→ End of Topic 06.


\newpage

# Appendix A — FACTS.md

_Atomic, citable facts. Provider package versions, MWAA env classes, Composer GA/EOL dates, Airflow 3.0 release, exam metadata._

# Topic 06 — FACTS.md (Apache Airflow)

> Atomic, citable facts. Provider package versions, MWAA env classes, Composer GA/EOL dates, Airflow 3 release, exam metadata.
>
> **Format:** one fact per line, citation in square brackets, last-verified date.
>
> **Last updated:** 2026-05-21 (seed)

---

## Airflow core release history

- **Apache Airflow** open-sourced by Airbnb **June 2015**; Apache Incubator **March 2016**; **Top-Level Project January 2019**. [Source: airflow.apache.org/history; ASF press release] [Verified 2026-05-21]
- **Airflow 2.0** released **December 17, 2020**. TaskFlow API, scheduler HA (multiple active schedulers), DAG serialization, smart sensors (later retired). [Source: airflow.apache.org/blog/airflow-two-point-oh-is-here] [Verified 2026-05-21]
- **Airflow 2.3** (Apr 2022): dynamic task mapping. **2.4** (Sep 2022): Datasets + data-driven scheduling. **2.5** (Dec 2022): Object Storage abstraction. **2.6** (Apr 2023): callbacks improvements. **2.7** (Aug 2023): setup/teardown, cluster activity dashboard. **2.8** (Dec 2023): listener API, Object Storage XCom backend. **2.9** (Apr 2024): Dataset events UI, OpenLineage v2.x. **2.10** (Aug 2024): DAG-level dataset events, hybrid executors. [Source: airflow.apache.org changelogs] [Verified 2026-05-21]
- **Airflow 3.0** released **April 22, 2025** at Airflow Summit. Headline changes: **Task SDK** (task execution decoupled from scheduler DB), **multi-cluster scheduler**, **React-based UI** (replaces FAB UI), **deadlines** (replaces SLA misses), **Assets** (renamed from Datasets), **DAG versioning**, multiple breaking changes from 2.x. [Source: airflow.apache.org/blog 2025; Airflow Summit 2025 keynote] [Verified 2026-05-21]
- **Python support**: Airflow 2.10 supports 3.8–3.12; Airflow 3.0 supports 3.9–3.12. [Source: airflow.apache.org/docs] [Verified 2026-05-21]

## Architecture limits & defaults

- **XCom soft warning** at **48 KB** (default for `xcom_max_size`); **hard ceiling** depends on metadata DB BLOB column — PostgreSQL `bytea` ~1 GB, MySQL `LONGBLOB` ~4 GB but slow. **Production target: keep XCom < 1 MB.** [Source: airflow.apache.org/docs configuration reference; PostgreSQL bytea docs] [Verified 2026-05-21]
- **Default `sql_alchemy_pool_size` = 5**; production typically 15–30 with `pool_pre_ping = True`. [Source: airflow.apache.org/docs] [Verified 2026-05-21]
- **`scheduler_heartbeat_sec` default = 5s**. Heartbeat timeout `scheduler_health_check_threshold` default 30s. [Source: airflow.apache.org/docs] [Verified 2026-05-21]
- **Multiple schedulers** supported since Airflow 2.0; uses Postgres row-level locks (`SELECT FOR UPDATE SKIP LOCKED`). MySQL requires 8.0+ with same locks. [Source: airflow.apache.org/docs HA scheduler] [Verified 2026-05-21]
- **Triggerer** process introduced in 2.2 for deferrable operators. Async (asyncio) — one process handles thousands of triggers. [Source: AIP-40, Airflow docs] [Verified 2026-05-21]

## Security baseline

- **`fernet_key`** encrypts Connection passwords and Variables in metadata DB. **Rotation** via `airflow rotate-fernet-key` after appending new key to `AIRFLOW__CORE__FERNET_KEY`. [Source: airflow.apache.org/docs/apache-airflow/stable/security] [Verified 2026-05-21]
- **`webserver_secret_key`** signs session cookies — MUST be identical across webserver replicas. [Source: airflow.apache.org/docs] [Verified 2026-05-21]
- **Auth Manager** abstraction GA 2.8 (Dec 2023). FAB Auth Manager is default. **AWS Auth Manager** plugs IAM-based access. **Simple Auth Manager** is for testing only. [Source: airflow.apache.org/docs auth-manager] [Verified 2026-05-21]
- **FAB built-in roles**: Admin, Op, User, Viewer, Public. Custom roles + per-DAG `access_control` field for granular control. [Source: airflow.apache.org/docs security/access-control] [Verified 2026-05-21]
- **`expose_config = False`** (recommended): prevents UI from showing airflow.cfg contents which may include secrets. [Source: airflow.apache.org/docs configuration] [Verified 2026-05-21]
- **Known CVE-2020-11978** — Example DAG `example_trigger_target_dag` RCE; example DAGs should be disabled (`load_examples=False`) in any non-dev environment. [Source: nvd.nist.gov; airflow security advisory] [Verified 2026-05-21]

## Secrets backends (built-in to provider packages)

- **AWS Secrets Manager + Parameter Store** via `apache-airflow-providers-amazon` (`SecretsManagerBackend`, `SystemsManagerParameterStoreBackend`). [Source: airflow.apache.org/docs/apache-airflow-providers-amazon] [Verified 2026-05-21]
- **GCP Secret Manager** via `apache-airflow-providers-google` (`CloudSecretManagerBackend`). [Source: airflow.apache.org/docs/apache-airflow-providers-google] [Verified 2026-05-21]
- **Azure Key Vault** via `apache-airflow-providers-microsoft-azure` (`AzureKeyVaultBackend`). [Source: airflow.apache.org/docs/apache-airflow-providers-microsoft-azure] [Verified 2026-05-21]
- **HashiCorp Vault** via `apache-airflow-providers-hashicorp` (`VaultBackend`). [Source: airflow.apache.org/docs/apache-airflow-providers-hashicorp] [Verified 2026-05-21]
- **Order of precedence**: Secrets Backend → Environment Variables (AIRFLOW_CONN_*, AIRFLOW_VAR_*) → Metadata DB. [Source: airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/connections] [Verified 2026-05-21]

## MWAA — Amazon Managed Workflows for Apache Airflow

- **GA**: November 24, 2020 (re:Invent 2020). [Source: aws.amazon.com/blogs Nov 2020] [Verified 2026-05-21]
- **Environment classes & pricing (us-east-1, 2026)**: mw1.small ~$0.49/hr, mw1.medium ~$0.79/hr, mw1.large ~$1.59/hr, mw1.xlarge ~$2.97/hr, mw1.2xlarge ~$5.78/hr (storage + metadata DB IO billed separately). [Source: aws.amazon.com/managed-workflows-for-apache-airflow/pricing] [Verified 2026-05-21]
- **Supported Airflow versions in MWAA** (2026-05): 2.8.1, 2.9.2, 2.10.1, **2.10.3** (latest GA). MWAA does **not** support Airflow 3.0 yet — confirm at quote time. [Source: docs.aws.amazon.com/mwaa/latest/userguide/airflow-versions.html] [Verified 2026-05-21]
- **Webserver access modes**: PUBLIC_ONLY (internet-accessible UI), PRIVATE_ONLY (VPC-only, requires VPN/Direct Connect). [Source: docs.aws.amazon.com/mwaa] [Verified 2026-05-21]
- **DAG storage**: S3 bucket with **versioning enabled (mandatory)**. `dags/`, `plugins.zip`, `requirements.txt`, `startup.sh`. [Source: docs.aws.amazon.com/mwaa] [Verified 2026-05-21]
- **`requirements.txt` constraints**: must include the Airflow constraints URL (`-c https://raw.githubusercontent.com/apache/airflow/constraints-X.Y.Z/constraints-3.X.txt`); no system packages, no compiled deps not on PyPI. [Source: docs.aws.amazon.com/mwaa/latest/userguide/working-dags-dependencies] [Verified 2026-05-21]
- **Triggerer process**: supported in MWAA for Airflow 2.7+ environments. [Source: docs.aws.amazon.com/mwaa] [Verified 2026-05-21]
- **CloudWatch log groups**: webserver, scheduler, worker, task, DAGProcessor. [Source: docs.aws.amazon.com/mwaa] [Verified 2026-05-21]

## Cloud Composer (GCP)

- **GA**: 2018. [Source: cloud.google.com/composer history] [Verified 2026-05-21]
- **Composer 2**: GKE Autopilot-based, GA 2021. **Composer 3**: GA April 2024; serverless control-plane components, PSC networking, smaller environments, scale-to-near-zero. [Source: cloud.google.com/blog Apr 2024] [Verified 2026-05-21]
- **Composer 1 EOL**: scheduled 2024–2025; users migrated to Composer 2 then 3. [Source: cloud.google.com/composer/docs/composer-1] [Verified 2026-05-21]
- **Composer 3 Workload Identity Federation**: KSA-to-GSA binding via annotations; no JSON keys. [Source: cloud.google.com/composer/docs/composer-3/use-workload-identity] [Verified 2026-05-21]
- **DAG storage**: GCS bucket auto-provisioned per environment, `dags/`, `plugins/`, `data/`. [Source: cloud.google.com/composer/docs] [Verified 2026-05-21]
- **Composer 3 pricing**: per-vCPU-hour for environment components + storage. Cheaper baseline than Composer 2 for low-utilization envs. [Source: cloud.google.com/composer/pricing] [Verified 2026-05-21]

## Azure Managed Airflow (Workflow Orchestration Manager)

- **GA**: ADF **Workflow Orchestration Manager** GA April 2024; also surfaces in **Microsoft Fabric Data Factory** as "Apache Airflow Jobs" (preview/GA 2024–2025 — confirm at quote time). [Source: learn.microsoft.com/azure/data-factory/airflow-overview] [Verified 2026-05-21]
- **DAG sync model**: git-sync from Azure DevOps / GitHub repo (different from MWAA's S3-blob upload). [Source: learn.microsoft.com/azure/data-factory] [Verified 2026-05-21]
- **Auth**: Azure AD / Entra ID via FAB OIDC; per-env Managed Identity or Service Principal for DAG-side auth. [Source: learn.microsoft.com/azure/data-factory] [Verified 2026-05-21]
- **Key Vault Backend** wiring documented. [Source: learn.microsoft.com/azure/data-factory] [Verified 2026-05-21]

## Astronomer

- **Astronomer** founded 2018; Astro Cloud platform GA. **Astro Hosted** (multi-tenant SaaS) and **Astro Hybrid** (data-plane in customer cloud account) are the two flavors. [Source: astronomer.io/product] [Verified 2026-05-21]
- **Astro Runtime** = Apache Airflow + Astronomer additions (extra providers, smart caching, better logging defaults). Versioned independently. [Source: docs.astronomer.io/astro/runtime-image-architecture] [Verified 2026-05-21]
- **Astro CLI** (`astro`) — local dev via Docker, `astro dev start`, push via `astro deploy`. [Source: docs.astronomer.io/astro/cli/install-cli] [Verified 2026-05-21]
- **Astronomer Cosmos** — community library that renders dbt projects as Airflow tasks dynamically. [Source: astronomer.github.io/astronomer-cosmos] [Verified 2026-05-21]

## Lineage & observability

- **OpenLineage**: LF AI & Data project (incubation); 1.0 spec released Aug 2022. `openlineage-airflow` provider extracts lineage automatically for many operators. [Source: openlineage.io spec] [Verified 2026-05-21]
- **Marquez**: reference OpenLineage backend. LF AI & Data project. [Source: marquezproject.ai] [Verified 2026-05-21]
- **OpenTelemetry support**: GA in Airflow 2.9 (Apr 2024) for traces and metrics. [Source: airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/logging-monitoring/otel.html] [Verified 2026-05-21]
- **StatsD metrics**: long-standing; emit to Datadog StatsD or to Prometheus via statsd_exporter. [Source: airflow.apache.org/docs] [Verified 2026-05-21]

## Provider packages (latest as of 2026-05-21 — confirm at quote)

- `apache-airflow-providers-amazon` 9.x line
- `apache-airflow-providers-google` 12.x line
- `apache-airflow-providers-microsoft-azure` 11.x line
- `apache-airflow-providers-snowflake` 6.x line
- `apache-airflow-providers-databricks` 7.x line
- `apache-airflow-providers-dbt-cloud` 4.x line
- `apache-airflow-providers-openlineage` 2.x line
- `apache-airflow-providers-cncf-kubernetes` 9.x line

[Source: pypi.org/project/apache-airflow-providers-*] [Verified 2026-05-21]

## Certifications

| Cert | Issuer | Cost USD | Format | Validity |
|---|---|---:|---|---|
| Apache Airflow Fundamentals | Astronomer | $150 | 60 min / 75 MCQ, online proctored | 2 years |
| DAG Authoring for Apache Airflow | Astronomer | $150 | 60 min / 75 MCQ, online proctored | 2 years |
| Astronomer Certification for Apache Airflow Operations | Astronomer | $150 | 60 min / 75 MCQ, online proctored | 2 years |

[Source: academy.astronomer.io] [Verified 2026-05-21]

- **AWS DEA-C01** covers MWAA basics (~5% of exam blueprint). [Source: aws.amazon.com/certification/certified-data-engineer-associate] [Verified 2026-05-21]
- **GCP Professional Data Engineer** covers Cloud Composer in the Orchestration domain. [Source: cloud.google.com/certification/data-engineer] [Verified 2026-05-21]
- **Azure DP-700 (Fabric Data Engineer)** covers Apache Airflow Jobs in Fabric. **DP-203** (legacy, retiring early 2026) covered ADF but not Airflow specifically. [Source: learn.microsoft.com/certifications] [Verified 2026-05-21]

## Capital One Airflow / orchestration signal

- Capital One **published MLOps spine** is **Step Functions + EKS + KServe + SageMaker + Glue + Snowflake/Databricks**. Airflow is used in some data-engineering teams for ETL into the warehouse but is **not** the dominant orchestrator. [Inference from public C1 tech blog + job postings — see Topic 04 CAPITAL_ONE.md] [Verified 2026-05-21]
- **Snowflake is heavily used at Capital One** for analytics + features; this is where Airflow most often appears in their stack (data engineering teams). [Source: capitalone.com/software; C1 + Snowflake partner case studies] [Verified 2026-05-21]
