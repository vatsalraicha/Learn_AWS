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
