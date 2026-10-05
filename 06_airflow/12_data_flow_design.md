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
