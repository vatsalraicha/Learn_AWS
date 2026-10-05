# Topic 12 — Databricks Certified Data Engineer Associate

> **Audience:** Senior AI/ML Engineer with 10+ years of PySpark in production, less depth on Lakeflow / Delta Live Tables / DAB / Unity Catalog operations. This is **exam prep**, not a from-zero data engineering primer. PySpark fluency is assumed; the curriculum front-loads what is **specific to the Databricks platform** and the **July 25, 2025 exam refresh**.
>
> **Goal:** Pass the Databricks Certified Data Engineer Associate (DEA) — currently the **July 25, 2025** exam guide — on the first attempt with ≥85% margin (the bar is 80%, so leave headroom). Secondarily, leave the prep cycle with production-grade knowledge of Lakeflow Declarative Pipelines, Lakeflow Jobs, Unity Catalog, Delta Sharing, and Databricks Asset Bundles — the post-2025 platform stack.
>
> **Last updated:** 2026-05-23

---

## What this topic guarantees

A reader who studies **only** these 16 modules + the 5 quiz packs (no external books, no Udemy course) is genuinely prepared for the July 25, 2025 exam. Specifically:

- Every verbatim exam objective from the July 25, 2025 guide is mapped, at the top of the module that owns it, in a `## Coverage map` table — open any module and you can see which official objective each section satisfies.
- Every API / SQL clause / option that the exam can quote back at you in a code-completion question is enumerated in the relevant module's body — Auto Loader's `cloudFiles.*` options (Module 06), MERGE's WHEN-MATCHED clauses and APPLY CHANGES INTO's STORED AS SCD TYPE (Modules 03 + 10), expectation actions (Module 11), the UC privilege chain and GRANT-ON-SCHEMA vs GRANT-ON-ALL-TABLES distinction (Module 15), Lakeflow Jobs task types + `run_if` + repair runs (Module 12), DAB top-level blocks + `mode: development`/`production` (Module 13).
- Every look-alike pair that has been observed to trip candidates is explicitly contrasted in a side-by-side table or "⚠️ Exam trap" callout — `availableNow` vs `processingTime` (Module 08), `addNewColumns` vs `rescue` vs `failOnNewColumns` vs `none` and their defaults (Module 06), STREAMING TABLE vs MATERIALIZED VIEW (Module 10), `count` vs `count_distinct` (Module 07), `repartition` vs `coalesce` (Module 07), `%run` vs `dbutils.notebook.run` (Module 02), DROP on managed vs external (Modules 04 + 15), ZORDER vs Liquid Clustering (Module 04), file_arrival trigger vs cron (Module 12), expectation vs row filter / column mask (Modules 11 + 15), D2D vs D2X Delta Sharing (Module 16).
- All five retired official sample questions are walked through, with the correct answer and the trap each distractor sets — Q1 in Module 07 (count_distinct for unique invoices), Q2 in Module 15 (GRANT SELECT ON SCHEMA when USE perms are already granted), Q3 in Module 16 (Delta Sharing config across internal + external), Q4 in Module 03 (CREATE OR REPLACE TABLE), Q5 in Module 03 (INSERT INTO … VALUES).
- Every module ends with a cold mini-quiz with answers, plus a "Sanity check before moving on" recall block. The 5 quiz packs in `quizzes/` mirror the live exam's domain mix (10 / 30 / 31 / 18 / 11) and question style (single-select, scenario stem + four near-identical clauses).
- Decision rules — what scenario phrase points to what answer — are surfaced consistently in the same `⚠️ Exam trap` and "How to recognize this on the exam" callout style across modules, so you build a single decision vocabulary across the topic.

If you finish the modules + quizzes and you cannot, from memory: write a `CREATE OR REFRESH STREAMING TABLE … FROM STREAM read_files(...)` with a CONSTRAINT EXPECT clause, write `GRANT SELECT ON SCHEMA … TO …` and recite why it's different from `ON ALL TABLES IN SCHEMA`, choose `availableNow` for "scheduled, run-to-completion", choose `APPLY CHANGES INTO … STORED AS SCD TYPE 2` over hand-rolled MERGE inside LDP, name the four cluster types and their cost ordering, and explain why managed-table DROP is destructive but external-table DROP is recoverable — then you are not yet ready. Re-read the relevant sections.

---

## Exam logistics — what to know before you book

| Item | Value |
|------|-------|
| **Scored questions** | **45 multiple-choice** (single-select only) |
| **Time limit** | **90 minutes** (= 2 min/question) |
| **Passing score** | **80%** — 36 of 45 scored (**raised from 70%** in July 25 2025 refresh) |
| **Registration fee** | **USD $200** (+ local taxes) |
| **Validity** | **2 years**; recertification = retake the full live exam |
| **Delivery** | Online proctored (Kryterion / Webassessor) or test center |
| **Test aides** | None — no scratch paper, no notes, no second monitor |
| **Prerequisite** | None required; Databricks recommends 6 months hands-on |
| **Languages** | English, Japanese, Portuguese (Brazil), Korean |
| **Code language in questions** | SQL when possible, otherwise Python (PySpark) |
| **Retake policy** | 14-day wait after first fail; 30-day after subsequent attempts |
| **Unscored items** | A few statistical items, not identified, extra time accounted for |
| **Third-party exam code** | `DEA-C01` (Udemy/FlashGenius label; Databricks does not use this code) |

> ⚠️ **80% is a high bar.** The pre-July-2025 exam passed at 70%. If your practice scores are sitting at 80–82%, you are not ready. Target 85–90% sustained across two full-length practice exams before booking.

---

## What changed in the July 25, 2025 refresh

The exam was significantly rewritten to align with the post-rebrand Databricks Data Intelligence Platform. If your prep material was written before mid-2025, expect **every** product name to have moved, and four exam objectives to be entirely new.

| Change | Old (pre-July 2025) | New (current) |
|--------|---------------------|---------------|
| **Passing score** | 70% | **80%** |
| **ETL / declarative pipelines product** | Delta Live Tables (DLT) | **Lakeflow Declarative Pipelines (LDP)** — backward compatible; `dlt` Python API and `LIVE` SQL keyword still work |
| **Orchestration product** | Workflows / multi-task jobs | **Lakeflow Jobs** — UI rename; same underlying engine |
| **Default governance** | Workspace ACL / Hive metastore optional | **Unity Catalog assumed by default** |
| **CI/CD path** | Repos + manual deploy / Terraform | **Databricks Asset Bundles (DABs)** — the new exam-canonical answer for "promote dev → prod" |
| **Default compute** | Job cluster | **Serverless** preferred in any "hands-off / auto-optimized" scenario |
| **Ingestion family** | Auto Loader only | Auto Loader **plus Lakeflow Connect** (managed connectors — Salesforce, Workday, SQL Server CDC, etc.) |
| **Layout / file management** | OPTIMIZE + ZORDER | **Liquid Clustering** (new default) + **Predictive Optimization** (auto OPTIMIZE/VACUUM on UC-managed tables) |
| **New topics added** | — | **Delta Sharing**, **Lakehouse Federation**, **Liquid Clustering**, **Predictive Optimization** |
| **De-emphasized** | Hive metastore details, legacy Repos workflow | — |

> ⚠️ **Exam trap (DLT → LDP rename):** Both syntaxes work at runtime, but **multiple-choice answers prefer the LDP form** (`CREATE OR REFRESH STREAMING TABLE`, `CREATE OR REFRESH MATERIALIZED VIEW`, `APPLY CHANGES INTO`). If you see `CREATE LIVE TABLE` as an answer, it's a distractor for someone studying with pre-2025 material.

---

## Domain weights (July 25, 2025 guide)

| # | Domain | Weight | Approx. questions (of 45) |
|---|--------|--------|---------------------------|
| 1 | Databricks Intelligence Platform | **10%** | ~4–5 |
| 2 | Development and Ingestion | **30%** | ~13–14 |
| 3 | **Data Processing & Transformations** | **31%** | **~14 (largest)** |
| 4 | Productionizing Data Pipelines | **18%** | ~8 |
| 5 | Data Governance & Quality | **11%** | ~5 |
| | **Total** | **100%** | **45 scored** |

**Domains 2 + 3 = 61% of the exam.** Auto Loader, PySpark transformations, Structured Streaming, and Lakeflow Declarative Pipelines are where two-thirds of your questions live. Allocate your study time accordingly — do not over-invest in the platform/governance domains.

---

## Learning path — 16 modules

### Domain 1 — Databricks Intelligence Platform (10%)

| # | Module | Why it matters |
|---|--------|----------------|
| 1 | [Lakehouse platform & compute model](01_lakehouse_platform.md) | Control plane vs compute plane vs storage; workspace anatomy; all-purpose vs job vs serverless; DBR variants (LTS, ML, Photon) |
| 2 | [Workspace basics — notebooks, repos, file system](02_databricks_workspace_basics.md) | Notebooks (.py vs .ipynb), Git folders, DBFS legacy vs UC Volumes, magic commands (`%sql`, `%python`, `%run`, `%pip`) |

### Domain 2 — Development & Ingestion (30%)

| # | Module | Why it matters |
|---|--------|----------------|
| 3 | [Delta Lake fundamentals](03_delta_lake_fundamentals.md) | CREATE/REPLACE/IF NOT EXISTS semantics, MERGE, time travel, DESCRIBE HISTORY, schema evolution, generated columns |
| 4 | [Delta table management — OPTIMIZE, VACUUM, Liquid Clustering, managed vs external](04_delta_table_management.md) | The DROP-semantics trap, VACUUM 7-day floor, Predictive Optimization, CONVERT TO DELTA |
| 5 | [Data ingestion methods — COPY INTO, Auto Loader, CTAS](05_data_ingestion_methods.md) | When to use which; idempotency model; bounded vs unbounded |
| 6 | [Auto Loader deep — schema evolution, hints, triggers](06_auto_loader_deep.md) | cloudFiles options, the four schema-evolution modes (and which is default in which case), `_rescued_data`, file detection modes, schemaLocation |
| 7 | [ETL with PySpark + SQL — multi-hop, UPSERT, repartition](07_etl_with_pyspark_sql.md) | Bronze/Silver/Gold transformations, MERGE patterns, repartition vs coalesce, common aggregations and DataFrame APIs |

### Domain 3 — Data Processing & Transformations (31%) — **largest domain**

| # | Module | Why it matters |
|---|--------|----------------|
| 8 | [Structured Streaming — triggers, output modes, checkpoints](08_structured_streaming.md) | DataStreamReader/Writer, triggers (`processingTime`, `availableNow`, deprecated `Once`, `continuous`), output modes, checkpointLocation, exactly-once |
| 9 | [Watermarks & stateful streaming](09_watermarks_state.md) | `withWatermark`, late data, stream-stream joins, CDC handling, RocksDB state store |
| 10 | [Lakeflow Declarative Pipelines (formerly DLT)](10_lakeflow_declarative_pipelines.md) | STREAMING TABLE vs MATERIALIZED VIEW, APPLY CHANGES INTO (SCD1/2), expectations, DLT → LDP migration (full backward compat), serverless pipelines |
| 11 | [Data quality with expectations](11_data_quality_expectations.md) | EXPECT clauses, ON VIOLATION DROP ROW / FAIL UPDATE / WARN, quarantine table pattern |

### Domain 4 — Productionizing Data Pipelines (18%)

| # | Module | Why it matters |
|---|--------|----------------|
| 12 | [Lakeflow Jobs — multi-task, repair, triggers](12_lakeflow_jobs.md) | Multi-task DAG, dependencies, parameters, retries, repair runs, file-arrival triggers, job cluster vs all-purpose cost trap |
| 13 | [Databricks Asset Bundles for DE](13_dabs_for_de.md) | `databricks.yml`, bundle/targets/resources/variables, `databricks bundle validate/deploy/run`, dev vs prod overrides |
| 14 | [Monitoring & observability — Spark UI, system tables](14_monitoring_observability.md) | Job run history, query history in SQL warehouses, Spark UI tabs (SQL, Stages, Storage, Executors), system tables for cost/lineage |

### Domain 5 — Data Governance & Quality (11%)

| # | Module | Why it matters |
|---|--------|----------------|
| 15 | [Unity Catalog basics](15_unity_catalog_basics.md) | 3-level namespace, USE CATALOG/USE SCHEMA/SELECT privilege chain, GRANT/REVOKE, ownership, dynamic views, row filters, column masks, audit logs |
| 16 | [Delta Sharing & Lakehouse Federation](16_delta_sharing_federation.md) | Sharing (provider/recipient/share, D2D vs open/D2X), Lakehouse Federation (foreign catalogs over JDBC to Postgres/MySQL/Snowflake/Redshift/BigQuery) |

---

## Companion files

- [`FACTS.md`](FACTS.md) — atomic, citable claims. Exam logistics, version numbers, defaults, syntax forms. "Last verified" dates.
- [`quizzes/`](quizzes/) — practice questions per domain (~135 total, distributed by domain weight). Recall / Apply / Diagnose / Defend.

---

## How to study with this corpus

1. **Week 1 — Foundation:** Read modules 1–2, then 3–4. Take quiz 01 (platform) and the first half of quiz 02. You should walk away knowing exactly what `CREATE OR REPLACE TABLE` does vs `CREATE TABLE IF NOT EXISTS`.
2. **Week 2 — Ingestion:** Modules 5–7. Drill Auto Loader options. Take the rest of quiz 02. Be able to write an Auto Loader stream from memory (the exam expects code recognition, not full code authoring, but recognition follows from authoring).
3. **Week 3 — Streaming + LDP:** Modules 8–11. This is the **31% of the exam.** Spend the most time here. Take quiz 03 cold; retake until ≥85%.
4. **Week 4 — Productionizing:** Modules 12–14. DAB structure is a high-yield area (4–5 questions cluster around DABs and CI/CD). Take quiz 04.
5. **Week 5 — Governance + full-length practice:** Modules 15–16. Take quiz 05. Then take **all five quizzes back-to-back as a simulated 90-min exam.** If you score ≥85%, book the exam. If not, identify the weakest domain and revisit.

> ⚠️ **Spark UI is on the exam.** PySpark engineers who have never opened the Spark UI in a Databricks notebook will struggle on the diagnosis questions. Open the SQL/DataFrame tab and the Stages tab on any non-trivial job you run during prep. Module 14 walks the four tabs you must recognize.

---

## Scope notes

- **Cutoff:** Reflects the **July 25, 2025** exam guide as the currently-live version. A "May 4, 2026" reference appears in one third-party source — re-verify the official PDF on `databricks.com/learn/certification/data-engineer-associate` ~2 weeks before your booked date.
- **Bias:** Cloud-agnostic where Databricks is cloud-agnostic. AWS / Azure / GCP cloud-specific differences are flagged when they matter to an exam scenario.
- **Anti-bias:** This is exam prep — not architecture school. Production tangents are kept short. The Topic 02 (Azure Databricks) corpus is the place for architect-level depth.
- **Convention:** SQL is the primary language in modules (the exam prefers SQL); Python/PySpark appears where the exam requires it (DataFrame aggregations, Auto Loader, Structured Streaming, LDP Python decorators).

## Stack baseline

```
databricks-sdk
databricks-cli           # >= 0.218 — DAB commands require this
databricks-connect       # version-matched to your DBR
pyspark                  # for local fallback
delta-spark              # local Delta tinkering
```

A free Databricks Community / Free Edition workspace is sufficient for the labs in this corpus. Lakeflow Declarative Pipelines and Lakeflow Jobs are available; serverless features depend on region availability.

---

## Research provenance

Built from the July 25 2025 official exam guide (verbatim objectives extracted to `research_inputs/12_databricks_de_associate/exam_guide.txt`) and a deep research report (`research_inputs/12_databricks_de_associate/RESEARCH.md`) that cross-references community pitfall threads, FlashGenius / OpenExamPrep study notes, Databricks Community Dec-2025 threads, and the official `docs.databricks.com` API references for Auto Loader, Lakeflow, Unity Catalog, and DABs.
