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
