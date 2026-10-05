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
