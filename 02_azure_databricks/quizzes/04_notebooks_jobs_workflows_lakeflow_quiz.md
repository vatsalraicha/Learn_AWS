# Quiz — Module 4: Notebooks vs Jobs vs Workflows vs Lakeflow Declarative Pipelines

## Recall

**Q1.** What are the four orchestration surfaces in Databricks 2026, and what's the one-line role of each?

<details><summary>Answer</summary>

- **Notebooks** — interactive prototyping; not the production deployment artifact
- **Jobs / Workflows** — imperative, multi-task DAG of notebooks/wheels/scripts/SQL with retries/alerts/parameterization (the general-purpose orchestrator)
- **Lakeflow Declarative Pipelines** (formerly DLT) — declarative, decorator-based, automatic dependency graph, automatic streaming/CDC, automatic data quality (the Spark-shaped ETL specialist)
- **Lakeflow Designer** — no-code drag-and-drop with GenAI assistance; generates real Lakeflow code under the hood (Public Preview June 2025)
</details>

**Q2.** What's the difference between `.py` and `.ipynb` notebook format, and which should you use for version-controlled work?

<details><summary>Answer</summary>

- **`.ipynb`** — Jupyter JSON format with embedded outputs. Default Databricks display format. Hard to review in Git (JSON diffs).
- **`.py` (Databricks-format)** — uses `# Databricks notebook source` headers and `# COMMAND ----------` separators. Plain Python. Git-friendly diffs.

**Use `.py` for any notebook destined for review or production.** Convert from `.ipynb` with `databricks workspace export-dir … --format SOURCE`.
</details>

**Q3.** What is the rebrand history of "DLT" in 2024–2026, and what's still backward compatible?

<details><summary>Answer</summary>

- **DLT → Lakeflow Declarative Pipelines (SDP)** — rename in 2024–2025
- **DAIS 2025**: Databricks open-sourced the core declarative engine to the Apache Spark project ("Spark Declarative Pipelines"); lands fully in **Apache Spark 4.1**

**Backward compat:** existing DLT pipelines run unchanged. Code can migrate from `import dlt` to `from pyspark import pipelines as dp`, with `@dp.table` for streaming tables and `@materialized_view` for materialized views — but the old `@dlt.table` decorators continue to work.

**What still says "DLT":** SKU codes still begin with "DLT" and the event log schema still says `dlt`. The term lingers in admin/billing surfaces.
</details>

---

## Apply

**Q4.** Write the Asset Bundle YAML for a Workflow with three tasks: `ingest_claims` and `ingest_eligibility` running in parallel on a shared Job cluster, then `build_member_month` running after both succeed. Include failure alerting.

<details><summary>Answer</summary>

```yaml
resources:
  jobs:
    silver_refresh:
      name: silver_refresh
      job_clusters:
        - job_cluster_key: silver
          new_cluster:
            spark_version: "17.3.x-scala2.13"
            node_type_id: Standard_DS5_v5
            num_workers: 4
            data_security_mode: SINGLE_USER
            runtime_engine: PHOTON
            custom_tags:
              cost_center: cc-123456
              business_unit: claims
              workload: etl
      tasks:
        - task_key: ingest_claims
          job_cluster_key: silver
          notebook_task: { notebook_path: ./src/ingest/claims.py }
        - task_key: ingest_eligibility
          job_cluster_key: silver
          notebook_task: { notebook_path: ./src/ingest/eligibility.py }
        - task_key: build_member_month
          depends_on:
            - { task_key: ingest_claims }
            - { task_key: ingest_eligibility }
          job_cluster_key: silver
          notebook_task: { notebook_path: ./src/silver/member_month.py }
      schedule: { quartz_cron_expression: "0 0 6 * * ?" }
      email_notifications:
        on_failure: [data-platform-oncall@optum.com]
        no_alert_for_skipped_runs: true
      max_concurrent_runs: 1
```

Notes:
- Single shared **Job cluster** keyed `silver` — all three tasks share it (cheaper than starting three independent clusters), and **Job Compute** at $0.15/DBU vs All-Purpose's $0.55/DBU is a 3.6× cost cut.
- `max_concurrent_runs: 1` prevents a slow nightly run from starting on top of itself.
- `no_alert_for_skipped_runs: true` reduces alert noise — failed runs alert; skipped runs don't.
</details>

**Q5.** A team is debating whether to use Lakeflow Declarative Pipelines or a regular Workflow with notebook tasks for a new claims-ingestion pipeline. The pipeline reads JSON from ADLS, dedupes by `claim_id`, validates `paid_amount >= 0`, and writes to a Silver Delta table. Which would you recommend, and why?

<details><summary>Answer</summary>

**Lakeflow Declarative Pipelines.** This is exactly the workload it's optimized for:

- **Streaming ingestion from object storage** — `cloudFiles` (Auto Loader) integration is built in; you write `spark.readStream.format("cloudFiles")` and Lakeflow handles the rest.
- **Tabular dedup** — declarative; no manual checkpoint management.
- **Data quality validation** — `@dp.expect_or_drop("positive_paid", "paid_amount >= 0")` enforces the constraint inline; quarantined rows go to a separate path automatically.
- **Multi-table downstream growth** — when you add `member_month`, `claim_line_aggregates`, etc., the framework derives the dependency graph from `dp.read("claims_silver")` references; you don't author the DAG.

**When you'd reach for Workflows + notebooks instead:**
- The pipeline needs to call an external API (e.g., enrich with a third-party provider directory) — that's imperative work, fits Workflows better.
- The pipeline needs branching logic (e.g., "if file is from payer X, run alternate parser") — declarative isn't the right shape.

**The canonical 2026 pattern** is often a hybrid: a Workflow that orchestrates (a) a Lakeflow pipeline task for the tabular ETL, (b) a notebook task for any imperative enrichment, (c) a SQL task to refresh downstream views.
</details>

---

## Diagnose

**Q6.** A team's Lakeflow pipeline is stuck — every run fails with a schema-evolution error after an upstream source added a column. They've already tried re-deploying the bundle. What's the likely root cause and the fix?

<details><summary>Answer</summary>

**Likely root cause:** Lakeflow pipelines maintain CDC checkpoints in the pipeline storage location. When an upstream schema change happens that the pipeline can't auto-handle (e.g., a type change that's not covered by `delta.enableTypeWidening`), the checkpoint becomes inconsistent with the current source schema. Re-deploying the bundle doesn't reset the checkpoint — the bundle code is fine; it's the *pipeline state* that's stuck.

**The fix sequence:**
1. **Check whether type widening would have prevented this.** Set `delta.enableTypeWidening = true` upstream so int→bigint, float→double, etc. happen as metadata-only changes.
2. **For the existing stuck pipeline**, you'll likely need to manually reset the CDC checkpoint and recreate the pipeline storage. The Lakeflow UI has a "Full refresh" option that resets state and recomputes from source — costs a full reprocess but unblocks.
3. **Verify the `target` vs `schema` config** — common confusion. Modern pipelines should set `schema`; legacy `target` works but creates ambiguity. Ensure your DABs deployment sets only one.
4. **Document the recovery in the runbook** for the on-call team.

**Production discipline:** monitor for upstream schema changes proactively (e.g., a dashboard on `system.access.column_lineage` plus `INFORMATION_SCHEMA.COLUMNS` deltas), and gate them through a controlled change process. A surprise column-type change should not be the first you hear of it.

**Source:** [Community thread 127147](https://community.databricks.com/t5/data-engineering/problems-and-questions-with-deploying-lakeflow-declarative/td-p/127147).
</details>

**Q7.** Code review on a notebook PR is taking 45+ minutes per review. The reviewers complain the JSON diff is unreadable and outputs blow up the GitHub diff viewer. What changes would you make?

<details><summary>Answer</summary>

The fix is process + tooling, not philosophy:

1. **Switch all version-controlled notebooks to `.py` (Databricks source format).** Convert with `databricks workspace export-dir … --format SOURCE`. Plain Python, readable Git diffs.
2. **Strip notebook outputs before commit.** For `.ipynb`, use `nbstripout` as a pre-commit hook. For `.py`, configure the save mode so outputs aren't embedded.
3. **Move reusable logic into `src/` Python modules.** The notebook becomes a thin orchestrator: `from src.silver import build_member_month; build_member_month(catalog, schema)`. Now the *logic* is reviewed in regular `.py` files, not notebook cells.
4. **Add `blackbricks`** as a pre-commit hook — applies `black` to Python cells and `sqlparse` to SQL cells. Vanilla `black` doesn't parse Databricks headers correctly.
5. **Add `databricks-pylint-plugin`** to catch `dbutils` misuse, hardcoded cluster IDs, and other anti-patterns.
6. **Limit notebook size.** A 1000-line notebook is reviewer poison. Split into smaller notebooks or — better — move logic into modules and have the notebook be 30 lines that call the modules.
7. **Repos discipline.** No production code in `/Workspace/Users/<name>/...` — production lives in a Repo with PR review enforced.

These changes typically cut review time by 60–80% and make the PR diff useful. The hard part is the political move of getting the team to accept "you can't just commit a 600-line notebook with outputs anymore."
</details>

---

## Defend

**Q8.** A peer engineer says "we should put everything in Lakeflow Declarative Pipelines — it's the future, it has built-in data quality and lineage, and it's getting open-sourced into Apache Spark anyway." Defend or refute.

<details><summary>Answer</summary>

**Refute, with calibration.**

Where the peer is right:
- Lakeflow's declarative model genuinely simplifies CDC ingestion, multi-table dependency graphs, and data quality enforcement. For Spark-shaped ETL on tabular data, it's excellent.
- The OSS landing in Spark 4.1 means the pattern won't be locked to Databricks long-term — you have an exit option.
- Built-in lineage and event log give you observability without building it yourself.

Where the peer is wrong:
- **Imperative logic doesn't fit.** Branching, looping, calling external APIs, ML training, complex state machines all fight the declarative model. Forcing them into Lakeflow produces awkward code that's harder to debug than the same logic in Workflows + notebook tasks.
- **Debugging is genuinely harder.** Errors propagate through generated Spark code; stack traces don't read like the imperative source.
- **The `target` vs `schema` config confusion** in DABs deployments is real ([Community 127147](https://community.databricks.com/t5/data-engineering/problems-and-questions-with-deploying-lakeflow-declarative/td-p/127147)).
- **Schema-change stuck-pipeline pain** is documented and recurring.
- **Cost** — Serverless DLT/Lakeflow has had documented 3–5× cost explosions vs classic ([Zipher analysis](https://zipher.cloud/databricks-serverless-pros-cons/)).

**The right framing:** **Lakeflow is a specialist, not a generalist.** Use it where it shines (streaming/CDC ingestion, multi-table tabular DAGs, data quality, materialized views) and use Workflows-with-notebook-tasks where the workload is imperative. The canonical 2026 pattern is **Workflows orchestrating Lakeflow pipelines + Python tasks + SQL tasks**, not "everything in Lakeflow."

The "future + OSS" part of the peer's argument is true and supports adoption *for the right workloads*. It doesn't make Lakeflow the answer for everything.
</details>
