# FACTS — Databricks Certified Data Engineer Associate

> **Atomic, citable claims.** Single source of truth for numbers, defaults, syntax, and version-sensitive details. Cross-link from modules and quiz answers.
>
> **Last verified:** 2026-05-23 against the July 25, 2025 official exam guide and current `docs.databricks.com`.

---

## 1. Exam logistics

| ID | Fact | Source |
|----|------|--------|
| L1 | The exam has **45 scored multiple-choice questions** | Official exam guide (July 25 2025) |
| L2 | The time limit is **90 minutes** (≈ 2 min per question) | Official exam guide |
| L3 | The passing score is **80%** (≈ 36/45 scored) — **raised from 70%** in the July 2025 refresh | Community sources (FlashGenius, OpenExamPrep, Databricks Community 141905) |
| L4 | The registration fee is **USD $200** (+ local taxes) | Official exam guide |
| L5 | Certification is **valid for 2 years**; recertification requires retaking the then-current full exam | Official exam guide |
| L6 | Delivery is **online proctored (Kryterion / Webassessor) or in-person test center** | Official exam guide |
| L7 | **No test aids are allowed** (no scratch paper, no notes, no second monitor) | Official exam guide |
| L8 | **No formal prerequisites**; Databricks recommends 6 months hands-on experience and the official course | Official exam guide |
| L9 | Question languages: English, Japanese, Portuguese (Brazil), Korean | databricks.com cert page |
| L10 | Code language in code-completion questions: **SQL when possible, otherwise Python (PySpark)** | databricks.com cert page |
| L11 | Retake policy: **14-day wait after first fail, 30-day wait after subsequent attempts** | FlashGenius |
| L12 | Some exam items are **unscored** (statistical, not identified, time accounted for) | Official exam guide |
| L13 | All questions are **single-select**. No multi-select. | OpenExamPrep, FlashGenius (multiple sources) |
| L14 | The exam version referred to throughout this corpus is dated **July 25, 2025** | Official exam guide PDF filename |

## 2. Exam domains & weights

| ID | Fact |
|----|------|
| D1 | Domain 1 — **Databricks Intelligence Platform** — **10%** |
| D2 | Domain 2 — **Development and Ingestion** — **30%** |
| D3 | Domain 3 — **Data Processing & Transformations** — **31%** (largest domain) |
| D4 | Domain 4 — **Productionizing Data Pipelines** — **18%** |
| D5 | Domain 5 — **Data Governance & Quality** — **11%** |

[Weights are community-reported; not printed in the public PDF objectives list. Cross-confirmed across 5+ sources, MEDIUM-HIGH confidence.]

---

## 3. Platform architecture

| ID | Fact |
|----|------|
| P1 | The Databricks Data Intelligence Platform has three layers: **control plane** (Databricks-managed UI, REST API, job scheduler, notebook editor, cluster manager), **compute plane** (Spark clusters / SQL warehouses running in the customer cloud subscription), and **storage** (Delta tables in customer cloud object storage — S3, ADLS Gen2, GCS) |
| P2 | The control plane is operated by Databricks; the compute plane runs in the customer's cloud account; customer data never leaves customer cloud storage |
| P3 | **All-purpose clusters** are for interactive notebook work; expensive (~$0.55/DBU range); persist after use |
| P4 | **Job clusters** are ephemeral, created at job start and terminated at job end; ~half the DBU cost of all-purpose; the exam's preferred answer for scheduled jobs |
| P5 | **Serverless compute** is auto-managed by Databricks, runs in Databricks' own cloud account (not the customer's), fastest startup; the exam's preferred answer for "hands-off / auto-optimized" scenarios |
| P6 | **DBR (Databricks Runtime)** ships in variants: standard, **LTS** (long-term support, ~24 months), **ML** (pre-installed ML libraries), Photon-enabled (vectorized C++ query engine), GPU |
| P7 | LTS releases get bug fixes for ~24 months; non-LTS releases for ~6 months |
| P8 | **Pools** maintain warm idle instances to reduce cluster startup latency |
| P9 | **SQL Warehouses** come in three flavors: **Classic** (customer cloud), **Pro** (customer cloud + Photon + serverless features), **Serverless** (Databricks-managed, fastest startup) |
| P10 | SQL Warehouse sizes scale t-shirt-style: 2X-Small → 4X-Large, each step approximately doubling the cluster size |

---

## 4. Delta Lake

| ID | Fact |
|----|------|
| DL1 | **Delta Lake is a transaction log layered over Parquet.** A Delta table is a directory of Parquet data files plus a `_delta_log/` subdirectory |
| DL2 | The `_delta_log/` directory holds **JSON commit files** (`00000000000000000000.json`, `…0001.json`, …), one per transaction |
| DL3 | Every 10 commits by default, Delta materializes a **checkpoint file** (`…0010.checkpoint.parquet`). Tuned by `delta.checkpointInterval` |
| DL4 | `_last_checkpoint` is a JSON pointer file naming the most recent checkpoint version |
| DL5 | Delta provides **ACID guarantees at the table level** via optimistic concurrency + atomic file rename on the underlying object store |
| DL6 | Delta supports **time travel** via `VERSION AS OF n` and `TIMESTAMP AS OF 'ts'`; e.g. `SELECT * FROM t VERSION AS OF 42` |
| DL7 | `DESCRIBE HISTORY <table>` returns the table's commit log including version, timestamp, operation, user, operationMetrics |
| DL8 | `CREATE OR REPLACE TABLE …` **creates the table if it doesn't exist, drops and recreates it if it does** (preserves the table name in the metastore; replaces schema and data) |
| DL9 | `CREATE TABLE IF NOT EXISTS …` **creates only if the table doesn't exist; leaves an existing table unchanged** |
| DL10 | `CREATE TABLE AS SELECT …` (CTAS) creates and populates in one statement — incompatible with empty-table DDL syntax (cannot list explicit column types in the same statement as `AS SELECT`) |
| DL11 | `INSERT INTO <table> VALUES (...)` is the correct syntax to append a literal row. `UPDATE` is for modifying existing rows, not appending |
| DL12 | **MERGE INTO** performs upserts: `MERGE INTO target USING source ON cond WHEN MATCHED THEN UPDATE SET ... WHEN NOT MATCHED THEN INSERT (...) VALUES (...)` |
| DL13 | The modern CDC pattern in LDP is **`APPLY CHANGES INTO`** (a.k.a. AutoCDC), not hand-rolled MERGE |
| DL14 | Delta supports **schema evolution** on write with `.option("mergeSchema", "true")`; supports overwrite with `.option("overwriteSchema", "true")` |
| DL15 | **Generated columns**: `CREATE TABLE t (… ts TIMESTAMP, date DATE GENERATED ALWAYS AS (CAST(ts AS DATE)))` — Delta computes them on insert |
| DL16 | **Identity columns**: `id BIGINT GENERATED ALWAYS AS IDENTITY` for monotonic auto-increment (no gap guarantees) |
| DL17 | **Change Data Feed (CDF)** is enabled with `delta.enableChangeDataFeed = true`; read changes with `SELECT * FROM table_changes('table', startVersion, endVersion)` |

## 5. Table management — OPTIMIZE / VACUUM / Liquid Clustering / Predictive Optimization

| ID | Fact |
|----|------|
| TM1 | `OPTIMIZE <table>` runs **bin-packing** to compact small files into ~1 GB target files. Idempotent — running it again is a no-op |
| TM2 | The target file size for OPTIMIZE is set by `spark.databricks.delta.optimize.maxFileSize`, default **1 GB** |
| TM3 | `OPTIMIZE <table> ZORDER BY (col1, col2)` rewrites files using **Z-order curve interleaving** to co-locate values across multiple columns (multi-dim clustering). Best with 1–4 columns |
| TM4 | **Z-Order is rewrite-heavy** — every OPTIMIZE ZORDER pass rewrites the full scope from scratch. Z-Order does NOT persist cluster identity in the log |
| TM5 | **Liquid Clustering** is the new default file-layout strategy for 2024+. Specified at table creation via `CLUSTER BY (col1, col2, …)` (up to 4 keys) |
| TM6 | Liquid Clustering is **incremental** — uses ZCube identity in the log so subsequent OPTIMIZE only touches unclustered ZCubes. Uses Hilbert curve |
| TM7 | Liquid Clustering keys can be **changed without rewriting the table**: `ALTER TABLE t CLUSTER BY (new_col)` |
| TM8 | `CLUSTER BY AUTO` (2025+) lets Predictive Optimization observe queries and choose clustering keys automatically |
| TM9 | **Cannot use both partitioning and Liquid Clustering** on the same table. Liquid Clustering supersedes partitioning |
| TM10 | `VACUUM <table>` removes files no longer referenced by the transaction log and older than the retention period |
| TM11 | The **default VACUUM retention is 7 days (168 hours)** |
| TM12 | **VACUUM cannot delete data younger than 7 days** unless you override the safety check: `SET spark.databricks.delta.retentionDurationCheck.enabled = false` (dangerous — risks concurrent reader failure) |
| TM13 | `VACUUM <table> RETAIN 168 HOURS DRY RUN` lists what would be deleted without deleting |
| TM14 | **Predictive Optimization** is a UC-managed-table feature that automatically runs OPTIMIZE and VACUUM based on table usage telemetry; default on for managed tables on newer DBRs |
| TM15 | `CONVERT TO DELTA parquet.<path>` converts an existing Parquet table to Delta in-place (creates `_delta_log/`, no data rewrite) |
| TM16 | **Deletion vectors** allow DELETE / UPDATE / MERGE to mark rows as deleted without rewriting Parquet files; physical rewrite happens on next OPTIMIZE. Enabled via `delta.enableDeletionVectors = true` (default for LDP-managed tables) |

## 6. Managed vs external tables — KEY EXAM TRAP

| ID | Fact |
|----|------|
| ME1 | **Managed table** — Unity Catalog (or the metastore) owns the storage location; created without an explicit `LOCATION` clause |
| ME2 | **External table** — you specify `LOCATION '<path>'` at create time; UC tracks only metadata |
| ME3 | **`DROP TABLE` on a managed table deletes both the metadata AND the underlying data files** (after the retention window) |
| ME4 | **`DROP TABLE` on an external table deletes only the metadata; the underlying data files remain in object storage** |
| ME5 | Managed tables benefit from Predictive Optimization automatically; external tables do not (UC doesn't own the storage) |
| ME6 | Managed tables are the recommended default in UC; external tables are for cases where you need to share storage with non-Databricks tools or co-locate with another system's catalog |

---

## 7. Auto Loader (`cloudFiles`)

| ID | Fact |
|----|------|
| AL1 | Auto Loader is invoked via `spark.readStream.format("cloudFiles")` |
| AL2 | The underlying file format is set via `.option("cloudFiles.format", "json"|"csv"|"parquet"|"avro"|"orc"|"text"|"binaryFile")` |
| AL3 | Auto Loader has two **file detection modes**: **directory listing** (default; lists directory on each microbatch; OK for smaller volumes) and **file notification** (sets up cloud-native event notifications — SNS/SQS, Event Grid, Pub/Sub — for high-throughput) |
| AL4 | File notification mode is enabled with `.option("cloudFiles.useNotifications", "true")` and requires Databricks to set up cloud notification resources |
| AL5 | Auto Loader's **schemaLocation** is required for schema inference: `.option("cloudFiles.schemaLocation", "<path>")` |
| AL6 | Schema location stores `_schemas/` versions of the inferred schema over time |
| AL7 | Auto Loader samples the **first 50 GB or 1000 files**, whichever comes first, for schema inference |
| AL8 | **Schema evolution modes** (`cloudFiles.schemaEvolutionMode`): `addNewColumns`, `rescue`, `failOnNewColumns`, `none`, `addNewColumnsWithTypeWidening` (newer) |
| AL9 | **Default schema evolution mode when no schema is provided** = `addNewColumns` (new columns trigger a stream restart and are added to the schema) |
| AL10 | **Default schema evolution mode when a schema IS provided directly** = `none` (new columns are ignored silently) |
| AL11 | `rescue` mode places any data not matching the schema (including new columns and type mismatches) in a `_rescued_data` JSON column; **does not fail and does not restart the stream** |
| AL12 | `failOnNewColumns` causes the stream to fail when new columns appear, forcing a manual intervention |
| AL13 | **Schema hints**: `.option("cloudFiles.schemaHints", "col1 LONG, col2 STRING")` provide explicit typing for specific columns while letting Auto Loader infer the rest. Only effective when no full schema is provided directly |
| AL14 | Schema hints work regardless of `cloudFiles.inferColumnTypes` setting |
| AL15 | Auto Loader provides **exactly-once** semantics via the checkpoint location |
| AL16 | The two recommended Auto Loader triggers for the exam are `.trigger(availableNow=True)` (modern batch-style; replaces deprecated `Trigger.Once`) and `.trigger(processingTime="N seconds")` (always-on micro-batch) |

---

## 8. Structured Streaming

| ID | Fact |
|----|------|
| SS1 | Streams are written with `df.writeStream` and read with `spark.readStream` |
| SS2 | **Triggers**: `default` (process available data ASAP, then wait for more — micro-batch), `processingTime="N seconds"` (fixed cadence), **`availableNow=True`** (process all currently available data, then stop — batch-style), `Trigger.Once` (DEPRECATED — use `availableNow`), `continuous="N ms"` (experimental, sub-second latency) |
| SS3 | **Output modes**: `append` (default for stateless; only new rows written), `complete` (full state on every batch; requires aggregation), `update` (only changed rows written; requires aggregation) |
| SS4 | A **checkpointLocation is required** for fault-tolerant streaming: `.option("checkpointLocation", "/path/to/_checkpoint")` |
| SS5 | The checkpoint location stores offsets, commit metadata, and (for stateful queries) the state store. **Never share a checkpoint between two queries** |
| SS6 | Exactly-once semantics for the sink rely on the combination of checkpoint + idempotent sink. Delta is idempotent |
| SS7 | **Watermarks**: `df.withWatermark("event_time_col", "10 minutes")` — declares how late data can arrive before state is dropped |
| SS8 | Watermarks are **required for stateful aggregations** with bounded state (otherwise state grows unboundedly) |
| SS9 | **Stream-stream joins require watermarks on BOTH input DataFrames** plus a time-range condition in the join expression |
| SS10 | Stream-stream join types: **inner** (with watermark and time-range), **left/right outer** (with watermark on the unbounded side and a time-range — semi-supported in older DBR, full support in recent versions), **outer/outer** (limited) |
| SS11 | State stores: **RocksDB state store** (default on newer DBR; spills to disk), **HDFS-backed** (legacy, fully in JVM heap) |
| SS12 | `foreachBatch(func)` lets you apply arbitrary DataFrame operations to each micro-batch and write to non-streaming-aware sinks |

---

## 9. Lakeflow Declarative Pipelines (LDP) — formerly Delta Live Tables (DLT)

| ID | Fact |
|----|------|
| LDP1 | The product rebranded from **Delta Live Tables (DLT)** to **Lakeflow Declarative Pipelines (LDP)** in July 2025 |
| LDP2 | LDP is **backward compatible** — existing `import dlt` Python code and `CREATE LIVE TABLE` SQL still run |
| LDP3 | New Python API: `from pyspark import pipelines as dp`; decorators `@dp.table`, `@dp.materialized_view`, `@dp.temporary_view` |
| LDP4 | New SQL forms: `CREATE OR REFRESH STREAMING TABLE <name> AS SELECT … FROM STREAM(<src>)` (incremental), `CREATE OR REFRESH MATERIALIZED VIEW <name> AS SELECT …` (batch-recomputed) |
| LDP5 | A **streaming table** is incremental (each refresh processes only new data); a **materialized view** is full-recompute |
| LDP6 | **Expectations** are declarative data quality checks: `CONSTRAINT <name> EXPECT (<bool_expr>) [ON VIOLATION DROP ROW|FAIL UPDATE]` |
| LDP7 | Expectation actions: **default** = log violation and keep row; **`ON VIOLATION DROP ROW`** = drop bad rows; **`ON VIOLATION FAIL UPDATE`** = fail the pipeline |
| LDP8 | The "WARN" action is the implicit default — Python decorators call it `@dp.expect(...)`, drop is `@dp.expect_or_drop(...)`, fail is `@dp.expect_or_fail(...)` |
| LDP9 | **`APPLY CHANGES INTO`** (AutoCDC) handles CDC declaratively inside LDP, replacing hand-rolled MERGE |
| LDP10 | `APPLY CHANGES INTO` syntax: `APPLY CHANGES INTO LIVE.target FROM STREAM(LIVE.src) KEYS (id) SEQUENCE BY ts [APPLY AS DELETE WHEN op = 'D'] STORED AS SCD TYPE 1|2 COLUMNS * EXCEPT (op, ts)` |
| LDP11 | **SCD Type 1** = overwrite history (latest value only); **SCD Type 2** = preserve history with effective_from / effective_to / `__START_AT` / `__END_AT` columns |
| LDP12 | LDP pipeline modes: **Triggered** (run to completion, then stop) and **Continuous** (long-running, low-latency) |
| LDP13 | LDP **serverless** ("Standard mode") is the post-July-2025 default and is reported ~26% cheaper TCO than classic LDP per the official blog |
| LDP14 | LDP automatically manages: dependency graph between tables, retries, schema enforcement, expectations evaluation, and CDC bookkeeping |
| LDP15 | Within an LDP SQL pipeline, you reference other tables in the same pipeline with `LIVE.<name>` (legacy) or directly by name in newer LDP SQL — both work |

---

## 10. Lakeflow Jobs (formerly Workflows / Multi-Task Jobs)

| ID | Fact |
|----|------|
| LJ1 | A Lakeflow Job is a **DAG of tasks** orchestrated by the Databricks scheduler |
| LJ2 | Task types: Notebook, Python script, Python wheel, SQL (query / dashboard / alert), **Pipeline** (run an LDP), JAR, Spark Submit, dbt, "If/Else" condition |
| LJ3 | Task dependencies are declared via `depends_on` (forms the DAG) |
| LJ4 | **Repair runs** allow re-running ONLY the failed tasks (and downstream) without re-running already-successful upstream tasks |
| LJ5 | **Parameter passing** mechanisms: job-level params (`{{job.parameters.<key>}}`), task-level params, and **task values** (`dbutils.jobs.taskValues.set(...)` / `.get(...)`) for passing data between tasks |
| LJ6 | Retry options per task: `max_retries`, `min_retry_interval_millis`, `retry_on_timeout` |
| LJ7 | Triggers: **scheduled** (Quartz cron), **file arrival** (new file in a UC Volume or external location), **continuous**, **manual / REST API** |
| LJ8 | Cluster choices per task: **all-purpose** (interactive, ~$0.55/DBU range), **job cluster** (ephemeral, ~half cost), **serverless** (managed, hands-off — exam-preferred for "auto-optimized") |
| LJ9 | Per-task email/webhook alerts available on `on_start`, `on_success`, `on_failure`, `on_duration_warning_threshold_exceeded` |
| LJ10 | `max_concurrent_runs` limits how many simultaneous instances of the same job can run |
| LJ11 | **For-each tasks** iterate a child task over a list of parameter values; supports concurrency caps |

---

## 11. Databricks Asset Bundles (DABs)

| ID | Fact |
|----|------|
| DAB1 | DAB is the **declarative deployment model** for jobs, pipelines, schemas, ML experiments and other Databricks resources |
| DAB2 | The root config file is **`databricks.yml`**, with optional resource definitions split into `resources/*.yml` |
| DAB3 | Top-level sections in `databricks.yml`: **`bundle`** (name, git metadata), **`include`** (additional YAML files), **`variables`** (parameterization), **`targets`** (per-env config), **`resources`** (jobs/pipelines/etc.), **`workspace`** (host) |
| DAB4 | **`targets`** define environments (e.g. `dev`, `staging`, `prod`) with overrides on workspace, variables, and `mode` (`development` vs `production`) |
| DAB5 | `mode: development` adds dev-only safeguards: prepends `dev_<user>_` to resource names, sets schedules to paused, redirects artifact paths to user space |
| DAB6 | `mode: production` enforces no dev prefix, schedules enabled, run_as identity fixed |
| DAB7 | Core CLI commands: `databricks bundle validate`, `databricks bundle deploy -t <target>`, `databricks bundle run <resource> -t <target>`, `databricks bundle destroy -t <target>` |
| DAB8 | DAB requires `databricks-cli` ≥ **0.218** |
| DAB9 | `databricks bundle validate` checks syntax and resource references without deploying |
| DAB10 | DAB is the exam's **preferred answer** for any "promote code from dev to prod" scenario — vs. manual notebook import or click-through job UI |
| DAB11 | Variables: `${var.<name>}` references; defined under `variables:` with `default:` and per-target override under `targets.<t>.variables.<name>` |
| DAB12 | Bundle resources can be defined inline under `resources:` or in separate YAML files referenced from `include:` |

---

## 12. Unity Catalog (UC)

| ID | Fact |
|----|------|
| UC1 | UC uses a **three-level namespace**: `catalog.schema.table` (also `catalog.schema.view`, `catalog.schema.function`, `catalog.schema.volume`) |
| UC2 | The **privilege chain to read a table** is: `USE CATALOG` on the catalog **AND** `USE SCHEMA` on the schema **AND** `SELECT` on the table. **All three are required** |
| UC3 | `GRANT SELECT ON SCHEMA <s> TO <principal>` grants read access to all current AND future tables/views in the schema |
| UC4 | `GRANT SELECT ON ALL TABLES IN SCHEMA <s> TO <principal>` grants read only on existing tables; **does NOT cover future tables** |
| UC5 | Common privileges: `USE CATALOG`, `USE SCHEMA`, `SELECT`, `MODIFY` (write), `CREATE TABLE`, `CREATE VIEW`, `CREATE FUNCTION`, `EXECUTE`, `READ VOLUME`, `WRITE VOLUME`, `BROWSE`, `ALL PRIVILEGES` |
| UC6 | `REVOKE <priv> ON <object> FROM <principal>` removes a previously granted privilege |
| UC7 | **Ownership** is required to grant privileges on an object. Initial owner = creator |
| UC8 | Key UC roles: **Account admin** (account-wide), **Metastore admin** (per-metastore), **Workspace admin**, **Catalog/Schema/Table owner** |
| UC9 | **Dynamic views** apply row/column filtering at query time based on the querying user: `CREATE VIEW v AS SELECT *, CASE WHEN is_member('analysts') THEN ssn ELSE 'REDACTED' END AS ssn_safe FROM t` |
| UC10 | **Row filter functions**: `CREATE FUNCTION region_filter(region STRING) RETURN is_member('us_only') OR region = 'EU'`; attached via `ALTER TABLE t SET ROW FILTER region_filter ON (region)` |
| UC11 | **Column masks**: `CREATE FUNCTION mask_ssn(ssn STRING) RETURN CASE WHEN is_member('hr') THEN ssn ELSE 'XXX-XX-XXXX' END`; attached via `ALTER TABLE t ALTER COLUMN ssn SET MASK mask_ssn` |
| UC12 | **Lineage** is automatically captured for UC-governed tables; viewable in the UI (table/column lineage) and queryable via `system.access.table_lineage` / `system.access.column_lineage` |
| UC13 | **Audit logs** are written to `system.access.audit` (queryable via SQL) and delivered to customer-configured cloud storage for long-term retention |
| UC14 | The legacy `hive_metastore` catalog is the default location for pre-UC tables; UC migration moves them to a UC catalog (e.g. `main`) |

---

## 13. Delta Sharing

| ID | Fact |
|----|------|
| DS1 | **Delta Sharing** is Databricks' open protocol for sharing live Delta data with external recipients without copying |
| DS2 | Three core concepts: **provider** (who shares), **recipient** (who receives), **share** (the bundle of tables/views shared) |
| DS3 | Two delivery modes: **Databricks-to-Databricks (D2D)** — recipient is on UC; uses UC identities for auth. **Open (D2X)** — recipient is anywhere (BI tool, pandas, Spark OSS); uses a bearer-token credential file |
| DS4 | Delta Sharing is **read-only by design** — recipients cannot write to shared objects |
| DS5 | **Partner connectors** support reading shares from PowerBI, Tableau, pandas, Spark OSS, Apache Spark, and others |
| DS6 | **Cross-cloud or cross-region egress costs apply** when the recipient is in a different cloud region from the provider's storage |
| DS7 | Limitations: no write-back, no row-level filters on the recipient side (filter on the provider side via dynamic views), no live SQL pushdown — recipient queries fetch full file ranges |
| DS8 | Provider creates: `CREATE SHARE <name>`; adds tables: `ALTER SHARE <name> ADD TABLE main.sales.orders`; grants to recipient: `GRANT SELECT ON SHARE <name> TO RECIPIENT <recipient_name>` |

## 14. Lakehouse Federation

| ID | Fact |
|----|------|
| LF1 | **Lakehouse Federation** lets you query external databases as UC catalogs without ingesting the data |
| LF2 | Supported foreign catalog sources (current list): **PostgreSQL, MySQL, Snowflake, Redshift, BigQuery, Microsoft SQL Server, Azure SQL Database, Azure Synapse, Databricks (another workspace), Salesforce Data Cloud, Teradata, Oracle** |
| LF3 | Foreign catalogs are **read-only** (most cases) and queries are pushed down where possible |
| LF4 | Use case: federate a Postgres OLTP database into UC so analysts can JOIN it with Bronze/Silver Delta tables — no ETL |
| LF5 | Performance limitation: not all functions/operators push down; complex queries may pull large data sets through the gateway. Lakeflow Federation is not a replacement for ingestion when query patterns are heavy |

---

## 15. Reference syntax — frequently mis-remembered

```sql
-- DDL (Module 03/04)
CREATE OR REPLACE TABLE t (id STRING, ts TIMESTAMP);    -- drops + recreates
CREATE TABLE IF NOT EXISTS t (id STRING, ts TIMESTAMP); -- no-op if exists
CREATE TABLE t AS SELECT ...;                            -- CTAS, no column-type list

-- DML
INSERT INTO t VALUES ('a1', current_timestamp());
UPDATE t SET ts = current_timestamp() WHERE id = 'a1';
DELETE FROM t WHERE id = 'a1';
MERGE INTO t USING s ON t.id = s.id
  WHEN MATCHED THEN UPDATE SET *
  WHEN NOT MATCHED THEN INSERT *;

-- Time travel
SELECT * FROM t VERSION AS OF 42;
SELECT * FROM t TIMESTAMP AS OF '2026-05-01 12:00:00';
DESCRIBE HISTORY t;

-- UC grants
GRANT USE CATALOG ON CATALOG main TO `analysts`;
GRANT USE SCHEMA  ON SCHEMA  main.sales TO `analysts`;
GRANT SELECT      ON SCHEMA  main.sales TO `analysts`;

-- LDP SQL
CREATE OR REFRESH STREAMING TABLE bronze_orders
  AS SELECT * FROM STREAM read_files('/Volumes/...', format => 'json');

CREATE OR REFRESH MATERIALIZED VIEW gold_daily
  AS SELECT date, SUM(amount) FROM LIVE.silver_orders GROUP BY date;

APPLY CHANGES INTO LIVE.customers
FROM STREAM(LIVE.cdc_customers)
KEYS (customer_id)
SEQUENCE BY ts
STORED AS SCD TYPE 2;
```

```python
# Auto Loader (Module 06)
(spark.readStream
   .format("cloudFiles")
   .option("cloudFiles.format", "json")
   .option("cloudFiles.schemaLocation", "/Volumes/main/_schemas/orders")
   .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
   .load("/Volumes/main/landing/orders")
  .writeStream
   .option("checkpointLocation", "/Volumes/main/_chk/orders")
   .trigger(availableNow=True)
   .toTable("main.bronze.orders"))
```

```yaml
# DAB skeleton (Module 13)
bundle:
  name: orders_pipeline

targets:
  dev:
    mode: development
    workspace: { host: https://adb-dev.cloud.databricks.com }
  prod:
    mode: production
    workspace: { host: https://adb-prod.cloud.databricks.com }

resources:
  jobs:
    orders_daily:
      name: orders-daily-${bundle.target}
      tasks:
        - task_key: bronze
          job_cluster_key: small
          notebook_task: { notebook_path: ./src/bronze.py }
```

---

## 16. Common defaults to memorize

| Setting | Default |
|---------|---------|
| `delta.checkpointInterval` | 10 commits |
| `spark.databricks.delta.optimize.maxFileSize` | 1 GB |
| VACUUM retention | 168 hours (7 days) |
| Auto Loader schema sampling | 50 GB or 1000 files, whichever first |
| Auto Loader schema evolution mode (no schema provided) | `addNewColumns` |
| Auto Loader schema evolution mode (schema provided) | `none` |
| Streaming output mode for stateless queries | `append` |
| Streaming trigger if none specified | micro-batch ASAP (default) |
| Delta data skipping indexed columns | 32 (first 32 in schema) |
| DBR LTS support window | ~24 months |
| Liquid Clustering max keys | 4 |
| Job DBU cost vs all-purpose | ~50% (rough ratio; exact varies by cloud + region) |
| Exam pass mark | 80% |
| Cert validity | 2 years |
