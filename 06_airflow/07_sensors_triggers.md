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
