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
