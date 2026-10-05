# Quiz — Part A + B: Airflow concepts & security (modules 1-10)

---

## Section 1 — Concepts (modules 1-6)

1. What does "logical_date" represent vs the wall-clock time the DAG actually runs?
2. Why was Airflow created (one sentence)?
3. The "DAG authors == cluster admins" problem — explain.
4. TaskFlow API vs classic Operators — pick one and justify.
5. Dynamic task mapping (2.3+) — when do you reach for it?
6. Custom Timetables — give one schedule that cron can't express.
7. `catchup=False` is the safe default. What does `catchup=True` cause on first deploy?
8. setup/teardown vs `trigger_rule="all_done"` — why is setup/teardown the cleaner answer?
9. Dataset-driven scheduling replaces what older pattern?

## Section 2 — Executors & sensors (modules 4, 7)

10. KubernetesExecutor vs Celery — which one for "short tasks at high throughput"?
11. `deferrable=True` on a sensor — what does the operator hand off to?
12. MWAA uses what executor (no choice)?
13. CeleryKubernetesExecutor — when does it fit?

## Section 3 — Security & networking (modules 8-10)

14. Fernet key — what does it encrypt? What's lost if you lose it?
15. Lookup precedence for a `conn_id` — list the three sources.
16. Vault dynamic secrets vs static — what's the win for regulated finance?
17. `secret_key` (Airflow webserver) — what does it sign, and what's the multi-replica constraint?
18. The worker has the widest egress surface. Why?
19. Snowflake PrivateLink — what does it replace?

---

## Answer key

1. `logical_date` = the start of the data interval being processed. Actual wall-clock execution is at the END of the interval (when the data is complete). For `@daily` with `logical_date=2026-05-20`, actual run = `2026-05-21T00:00:00`.

2. Airbnb needed cron-on-steroids with task dependencies, retries, and a UI for their data pipelines. Maxime Beauchemin built it.

3. DAG files are Python; the scheduler imports them. Top-level code runs in the scheduler. Anyone with commit access to the DAG folder runs arbitrary Python in the scheduler context — effectively cluster admin. Mitigations: K8sExecutor + per-task SA + Task SDK in 3.0.

4. TaskFlow. Pythonic; dependencies inferred; type hints work; XCom transparent. Mix freely with operators when an operator is right.

5. Variable parallel work — process N partitions in parallel where N is known at runtime (after `discover_partitions` task).

6. "Last business day of month at 09:00 NY time, except holidays" — CronTriggerTimetable / custom Timetable. Cron can't do business days or holiday exclusions.

7. Airflow runs every interval between `start_date` and now. A DAG starting from 2025-01-01 deployed today = ~500 simultaneous queued runs. Database / warehouse meltdown.

8. setup/teardown is semantically clear ("clean up this resource regardless of work outcome"); allows complex setup/work/teardown chains without manually managing `trigger_rule` on every downstream.

9. ExternalTaskSensor — cross-DAG wait. Dataset-driven scheduling is declarative; consumer DAG runs when producer's outlet updates. No polling.

10. **Celery**. K8sExecutor has 5-15s pod startup overhead per task — kills throughput for sub-minute tasks. Celery keeps a warm worker.

11. The Triggerer process. Async event loop; one Triggerer can manage thousands of concurrent waits. Worker slot freed.

12. **Celery only**. No choice in MWAA. If you need K8sExecutor: self-host on EKS or use Astro Hybrid.

13. Mixed workload — short tasks (Celery) + heavy/specialized tasks (K8s). Declare `queue="kubernetes"` on heavy tasks; default to Celery.

14. Encrypts Connection passwords and Variables in metadata DB. **If lost: all encrypted values are unrecoverable.** Backup the Fernet key.

15. (1) Env var `AIRFLOW_CONN_X` → (2) Secrets Backend → (3) Metadata DB.

16. Dynamic secrets are issued per request (e.g., 1-hour Snowflake password). No static cred to rotate; revocation = stop renewing. Eliminates the static-cred-in-DB risk entirely.

17. Signs session cookies. MUST be identical across webserver replicas (otherwise users get logged out as LB switches them between replicas). Generate via `openssl rand -hex 32`, store in Secrets Backend.

18. Workers connect to all data sources: Snowflake, Databricks, S3, EMR, Slack, custom APIs, etc. Compromised worker → wide blast radius.

19. The public Snowflake endpoint. With PrivateLink: traffic stays in AWS/Azure/GCP backbone; no internet egress for Snowflake queries.
