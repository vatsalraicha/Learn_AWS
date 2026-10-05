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
