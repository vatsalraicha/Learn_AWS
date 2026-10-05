# Module 5 — Spark on Databricks: Practitioner Discipline

> **Goal of this module:** the Databricks-specific operational muscle a senior PySpark engineer needs — reading the Spark UI to diagnose problems, MERGE / SCD patterns that don't blow up at scale, Auto Loader and Structured Streaming on Databricks specifically, schema-evolution gotchas, and the diagnostic loop ("this job is slow / this bill is wrong" → which tab in which UI → what to change).
>
> **Assumes:** you can write PySpark and SQL daily. We skip DataFrame basics and go to the discipline level.

---

## Why this module exists separately from "Performance" (Module 6)

Module 6 is the **performance cookbook** — join strategies, AQE, Photon-friendly code, file layout for query speed. This module is the **diagnostic operational muscle** — given a problem you didn't expect, what UI do you open, what do you look for, and what do you change. The two are companions; this one is "how to operate Spark on Databricks day-to-day."

---

## Reading the Spark UI on Databricks

Databricks routes the Spark UI per cluster. From a notebook attached to a cluster, click "Spark UI" to open it. The five tabs that matter, in order of most-frequently-useful:

### 1. SQL / DataFrame tab — start here for DataFrame jobs

For every Spark SQL or DataFrame query, this tab shows the **query plan** as a graph plus an **execution timeline**. The plan annotates each node with:
- `numFilesPruned` / `numFilesRead` — how much data skipping fired (Module 3). Big mismatch (low pruning, high read) means your filter columns aren't in the indexed-cols set.
- `dataSize` per stage — bytes shuffled, bytes broadcast.
- `BroadcastHashJoin` vs `SortMergeJoin` vs `ShuffleHashJoin` — the join strategy. Module 6 covers when each fires.
- AQE (Adaptive Query Execution) annotations — when AQE kicked in mid-query to coalesce partitions, switch a join strategy, or split a skewed partition.

**The first thing to look for:** "expected to broadcast, actually shuffled" or vice versa. Broadcasting a large table OOMs the driver; shuffling a small dimension that should have been broadcast wastes time.

### 2. Stages tab — for shuffle / skew problems

Each stage's detail page shows **task duration distribution** as a histogram + a sortable table.

**Skew detection look-fors:**
- **Long-tail in the duration histogram** — most tasks finish in 30s, two tasks take 12 minutes. That's skew.
- **`shuffle read remote bytes` per task heavily skewed** — same diagnosis from a different angle.
- **One task with >5× the median input size** — explicit skew.

**The fix paths** (Module 6 has the cookbook):
- AQE skew join (default-on in DBR 17.3) auto-splits skewed partitions
- Manual salting if AQE doesn't catch it
- Repartitioning by a different key
- Pre-aggregating before the join

### 3. Storage tab — caching diagnostics

Lists cached RDDs/DataFrames and their memory + disk consumption. **Use this when** you see `OutOfMemory` errors or sluggish reads on a job that should hit cache.

Common findings:
- **Cache evicted but query still expects it** — happens when memory pressure forces eviction; the next read regenerates from source.
- **Disk spill** — items in cache spilled to local SSD because they didn't fit in memory; reads are slower than expected.
- **Photon row cache vs Delta disk cache vs `df.cache()`** — three different layers. Module 6 unpacks them.

### 4. Executors tab — node-level health

Per-executor view of RAM used, GC time, shuffle write/read, task counts.

**The two important columns:**
- **GC Time** — if a task spent 30% of its time in GC, the executor is memory-pressured. Add memory or reduce per-task data.
- **Failed Tasks** — node-local failures often signal Spot preemption, init-script flakiness, or driver-worker network issues.

### 5. Jobs / Stages tab — for job-level timing

The first tab, but actually the least useful for diagnosis once you know the others. Use it to find the slow stage, then drill into the SQL/DataFrame tab for the query plan and the Stages tab for the task distribution.

### Photon UI annotations

When Photon is enabled, query plans annotate which operators ran in Photon (the C++ kernel) vs JVM Spark. **Operators that fall back to JVM are typically Python UDFs, certain expressions, or unsupported types** — these defeat Photon's value (Module 6). The UI doesn't shout at you about it; you have to look. Make a habit of it.

---

## The diagnostic loop — "this job is slow"

A senior practitioner has a mental loop they run when something is slow:

```
1. SQL/DataFrame tab → query plan
   - Is the join strategy what I expected? (BHJ vs SMJ vs SHJ)
   - Is data skipping firing? (numFilesPruned vs numFilesRead)
   - Are AQE annotations showing up? (coalesce, skew split)
   - Is Photon doing the work, or did it fall back?

2. Stages tab → slow stage
   - Task duration histogram — long tail = skew
   - Shuffle read/write sizes — am I shuffling more than I should?
   - Spill metrics — disk spill = memory pressure

3. Executors tab
   - GC time > 20% = memory pressure
   - Failed tasks pattern = node-level issue

4. Storage tab (if caching is involved)
   - Did the cache evict?

5. Cluster page
   - Right size for the workload?
   - Photon worth the 2× DBU here? (Module 6)
   - Spot fallback hit? (Module 2)
```

**The discipline that separates intermediate from senior practitioners:** *forming a hypothesis from the symptom before opening the UI*, then opening the specific tab to confirm. "Job is slow on a 10× larger input" → suspect skew → open Stages → confirm or reject. "Job is slow on a workload that runs nightly fine" → suspect data growth crossing a threshold → check `system.billing.usage` for input size growth, then open Stages.

---

## MERGE patterns and SCD2 implementation

MERGE is the single most cost-driving operation in Silver-layer pipelines. The Module 3 internals (Low-Shuffle Merge, Deletion Vectors, `WHEN NOT MATCHED BY SOURCE`) are the engine; this section is the practitioner code.

### Pattern 1 — Idempotent insert / upsert

Every Silver-layer ingest must be idempotent — reruns must produce the same state. The pattern:

```python
from delta.tables import DeltaTable

target = DeltaTable.forName(spark, "silver.claim_line")

(target.alias("t")
   .merge(updates_df.alias("s"), 
          "t.claim_id = s.claim_id AND t.claim_line_id = s.claim_line_id")
   .whenMatchedUpdate(
       condition="s.row_hash <> t.row_hash",  # only update if actual change
       set={
         "billed_amount": "s.billed_amount",
         "paid_amount":   "s.paid_amount",
         "row_hash":      "s.row_hash",
         "ingestion_ts":  "current_timestamp()",
       })
   .whenNotMatchedInsert(values={
         "claim_id":        "s.claim_id",
         "claim_line_id":   "s.claim_line_id",
         "billed_amount":   "s.billed_amount",
         "paid_amount":     "s.paid_amount",
         "row_hash":        "s.row_hash",
         "ingestion_ts":    "current_timestamp()",
       })
   .execute())
```

The `row_hash` discipline is what makes the MERGE truly idempotent — `WHEN MATCHED UPDATE` only fires when something *actually changed*, not on every rerun. Compute `row_hash` upstream as `sha2(concat_ws('|', col1, col2, ...), 256)` over the business attributes.

### Pattern 2 — SCD Type 2 (member dimension with history)

```python
# Member SCD2 with WHEN NOT MATCHED BY SOURCE for full closure
target = DeltaTable.forName(spark, "silver.dim_member")

(target.alias("t")
   .merge(member_updates.alias("s"),
          "t.member_id = s.member_id AND t.is_current = true")
   .whenMatchedUpdate(
       condition="s.row_hash <> t.row_hash",
       set={"is_current": "false", "valid_to": "s.effective_date"})
   .whenNotMatchedInsert(values={
       "member_sk":     "uuid()",
       "member_id":     "s.member_id",
       "is_current":    "true",
       "valid_from":    "s.effective_date",
       "valid_to":      "lit('9999-12-31')",
       "row_hash":      "s.row_hash",
       # ... other attributes ...
       })
   # Close out members no longer in feed (e.g., termed members)
   .whenNotMatchedBySourceUpdate(
       condition="t.is_current = true",
       set={"is_current": "false", "valid_to": "current_date()"})
   .execute())

# Insert new "current" rows for members that had a change above
new_currents = (member_updates.alias("s")
                  .join(target.toDF().alias("t"), 
                        ["member_id"])
                  .where("s.row_hash <> t.row_hash AND t.is_current = false")
                  .select(...))
new_currents.write.format("delta").mode("append").saveAsTable("silver.dim_member")
```

The two-step pattern is needed because MERGE's `whenMatchedUpdate` can only update existing rows, not insert a new one. So you (a) close the old "current" version, (b) close out any members no longer in the feed, (c) insert new "current" rows in a follow-up step.

DLT/Lakeflow's `APPLY CHANGES INTO ... STORED AS SCD TYPE 2` is the declarative shortcut that handles this for you — when applicable, it's cleaner.

### Pattern 3 — Cancel-and-replace (HL7 / X12 corrections)

```python
# When upstream sends a correction message that supersedes a prior message
(target.alias("t")
   .merge(corrections.alias("c"),
          "t.message_control_id = c.original_message_control_id")
   .whenMatchedUpdate(set={
       "is_canceled":          "true",
       "canceled_by_msg_id":   "c.message_control_id",
       "canceled_ts":          "current_timestamp()",
   })
   .execute())

# Insert the new corrected message
corrections.write.format("delta").mode("append").saveAsTable("silver.message")
```

Pre-DV, this was painful because every cancel rewrote the file containing the canceled message. With DV (`delta.enableDeletionVectors = true`), it's cheap.

### MERGE-key cardinality discipline

The MERGE join column(s) must be **at least one high-cardinality key**. If you absolutely have to merge on a low-cardinality column (e.g., `payer_id`), add a high-cardinality column to the join condition (`payer_id AND claim_id`) or you'll cause the planner to consider every file as a candidate. Module 3 covers this.

---

## Auto Loader — file ingestion that scales

### Why Auto Loader specifically

`spark.readStream.format("cloudFiles")` is Databricks' file-source connector with two improvements over vanilla Structured Streaming on object storage:
1. **File listing optimization** — uses cloud-native notification or efficient listing instead of repeatedly listing the directory.
2. **Schema evolution** — auto-detects new columns and either fails / drops / rescues them based on configuration.

### File discovery modes

```python
# Directory listing mode (default) — list directory each trigger
df = (spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaLocation", "/Volumes/_admin/schemas/claims_bronze/")
        .load("/Volumes/raw/edi/claims/"))

# File notification mode — uses Azure Event Grid + Storage Queue
df = (spark.readStream.format("cloudFiles")
        .option("cloudFiles.useNotifications", "true")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.schemaLocation", "/Volumes/_admin/schemas/claims_bronze/")
        .load("/Volumes/raw/edi/claims/"))
```

**Directory listing** is fine up to ~10K files in the directory; beyond that, listing dominates the trigger time. **File notification mode** uses cloud-native events (Event Grid → Storage Queue on Azure) and scales to millions of files, but requires:
- Permission to provision Event Grid topics on the source storage account
- An ongoing cost for the queue infrastructure
- DR considerations (the queue is a failure point)

For Optum-scale workloads with high file fan-in (real-time claims drops, lab feeds), **file notification mode** is usually the right answer.

### Schema evolution modes

```python
df = (spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.schemaLocation", "/Volumes/_admin/schemas/claims_bronze/")
        .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
        # other options: "rescue", "failOnNewColumns", "none"
        .load(...))
```

- **`addNewColumns`** (default) — auto-add new columns of compatible types. Fails the stream on the first occurrence, then resumes (the new column appears).
- **`rescue`** — captures unexpected columns into a `_rescued_data` STRING column. The stream doesn't fail. Use when you want forward progress over schema fidelity.
- **`failOnNewColumns`** — strict; fails on any new column. Use for highly governed feeds where unexpected schema is a contract violation.
- **`none`** — ignores new columns. Don't use; you lose data silently.

### `cloudFiles.maxFilesPerTrigger`

Caps how many files each trigger ingests. Without it, a backfill of 100K files in one trigger overwhelms the cluster. Default in 2026 is 1000 — explicit control is recommended.

---

## Structured Streaming — the operational levers

### Triggers

Three trigger modes:
- **`Trigger.ProcessingTime("30 seconds")`** — micro-batch every N seconds. Default if unspecified, default interval ~500ms. Best for steady-state streaming with bounded latency SLO.
- **`Trigger.AvailableNow()`** — process all currently-available data, then stop. The 2025+ recommended default for "incremental batch" — replaces the old `Trigger.Once()`. Run nightly, process whatever arrived since the last run, exit.
- **`Trigger.Continuous("1 second")`** — true continuous (sub-second latency), limited operator coverage; rarely used.

For most healthcare ETL, **`Trigger.AvailableNow()` triggered nightly** is the right answer. Continuous-streaming mode only when latency SLO < 5 minutes.

### Watermarks

```python
df_with_watermark = df.withWatermark("event_time", "2 hours")
```

Watermarks tell the engine "data older than this is expected to have arrived; you can drop state for it." Required for stateful operations (aggregations, stream-stream joins, deduplication) that retain state across micro-batches. Without watermarks, state grows unbounded.

**The trade:** smaller watermark = lower latency but data older than the watermark is dropped (lost late events). Larger watermark = better late-data tolerance but bigger state.

For healthcare claims (where late corrections can arrive 90+ days later), watermarks aren't a substitute for cancel-and-replace MERGE patterns on Silver. Use watermarks on real-time aggregations (last-hour denials, this-shift admissions); use MERGE for late-arriving corrections.

### Output modes

- **`append`** — only new rows are output. Default. Most common.
- **`update`** — only changed rows are output. Required for stateful aggregations on streaming sinks that support upsert.
- **`complete`** — full result table on each trigger. Expensive; only for small-cardinality aggregations.

### State store backends

- **Default state store** — in-memory + checkpointed to object storage. Fine for small state.
- **RocksDB state store** — disk-backed, lower memory footprint, default for large-state pipelines in DBR 17.3+. Enable via `spark.sql.streaming.stateStore.providerClass`.

For multi-million-state pipelines (hundreds of millions of unique keys in a streaming aggregation), **RocksDB is mandatory** — the in-memory store will OOM the cluster.

---

## Schema evolution gotchas

### Auto-merge in production

`spark.databricks.delta.schema.autoMerge.enabled = true` lets writes auto-add new columns. **Don't enable globally in production.** Schema drift becomes invisible — a typo in a column name silently creates a new column. Use it explicitly in CI test environments and require explicit `ALTER TABLE` in prod.

### Type widening

```sql
ALTER TABLE silver.claim_line SET TBLPROPERTIES ('delta.enableTypeWidening' = true);
```

Without this, an `int → bigint` change requires a full rewrite. With it, it's a metadata-only operation. **Enable on every Silver+ table by default.** Module 3 has the full coverage.

### Column rename — requires column mapping

```sql
ALTER TABLE silver.member SET TBLPROPERTIES ('delta.columnMapping.mode' = 'name');
ALTER TABLE silver.member RENAME COLUMN old_name TO new_name;
```

Once column mapping is on, the table requires column-mapping-aware readers (Delta 1.2+). **Streaming readers need schema tracking** (Delta 3.0+) on column-mapped tables; otherwise streams fail. Module 3.

### The "I added a column at position 35" silent failure

Discussed in Module 3: `delta.dataSkippingNumIndexedCols = 32` means columns at position 33+ get no stats. Schema growth past 32 columns silently breaks data skipping for filters on the late columns. **Detection:** look at Spark UI for `numFilesPruned = 0` despite predicate filtering. **Fix:** `dataSkippingStatsColumns` to name the hot filter columns explicitly.

---

## Notebook hygiene that survives PR review

(Module 4 covered the notebook-format and tooling decisions. This section is the *coding* discipline.)

### Code organization pattern

```
my-bundle/
  databricks.yml
  src/
    __init__.py
    silver/
      __init__.py
      member_month.py        # pure function: build_member_month(spark, catalog, schema)
      claim_line.py
    bronze/
      claims_loader.py
    common/
      delta_helpers.py
      io.py
  notebooks/
    silver/
      member_month_runner.py # 30 lines: import, call, log
      claim_line_runner.py
  tests/
    silver/
      test_member_month.py   # pytest + chispa
```

The notebook calls a pure function. The function is pytest-testable. The notebook is a thin orchestrator that reads parameters, calls the function, logs MLflow tags, and exits.

```python
# notebooks/silver/member_month_runner.py
# Databricks notebook source

# COMMAND ----------
import mlflow
from src.silver.member_month import build_member_month

# COMMAND ----------
catalog = dbutils.widgets.get("catalog")
schema  = dbutils.widgets.get("schema")
run_id  = dbutils.widgets.get("run_id")

# COMMAND ----------
with mlflow.start_run(run_name=f"silver_member_month_{run_id}"):
    mlflow.log_param("catalog", catalog)
    mlflow.log_param("schema", schema)
    n_rows = build_member_month(spark, catalog=catalog, schema=schema)
    mlflow.log_metric("rows_written", n_rows)
```

```python
# src/silver/member_month.py
from pyspark.sql import SparkSession, DataFrame, functions as F

def build_member_month(spark: SparkSession, catalog: str, schema: str) -> int:
    claims = spark.table(f"{catalog}.{schema}.claim_line")
    eligibility = spark.table(f"{catalog}.{schema}.eligibility")
    
    member_month = (
        claims
        .alias("c")
        .join(eligibility.alias("e"), 
              (F.col("c.member_id") == F.col("e.member_id")) &
              (F.col("c.service_date").between(F.col("e.eff_dt"), F.col("e.term_dt"))),
              "inner")
        .groupBy("c.member_id", F.date_trunc("month", "c.service_date").alias("year_month"))
        .agg(F.sum("c.paid_amount").alias("paid"),
             F.count("c.claim_line_id").alias("claim_count"))
    )
    
    member_month.write.format("delta").mode("overwrite").saveAsTable(f"{catalog}.{schema}.member_month")
    return member_month.count()
```

```python
# tests/silver/test_member_month.py
from chispa.dataframe_comparer import assert_df_equality
from src.silver.member_month import build_member_month
# ... build a small fixture DataFrame, call the function, assert
```

The benefit: **the logic is reviewable in plain Python**, the test runs without a cluster (local Spark or Databricks Connect), and the notebook becomes a 30-line wrapper that any reviewer can scan in seconds.

### Avoid in notebooks

- **Hardcoded paths** — use `dbutils.widgets` parameters
- **`display()` on huge DataFrames** — triggers a query and pulls 1000 rows; cost surprise. Use `.limit(10).show()` for cheap eyeballing
- **`.collect()` on production data** — pulls all rows to driver; OOMs the cluster
- **Mutating state across cells** — order-dependent code that breaks on re-run
- **Inline secrets** — use `dbutils.secrets.get(scope, key)`

### `dbutils` mocking for tests

```python
# tests/conftest.py
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_dbutils():
    dbutils = MagicMock()
    dbutils.widgets.get.side_effect = lambda key: {
        "catalog": "test_catalog",
        "schema":  "test_schema",
        "run_id":  "test_run",
    }[key]
    dbutils.secrets.get.return_value = "fake-secret"
    return dbutils
```

When your notebook code uses `dbutils`, mock it in tests so they run without a cluster.

---

## Production reality

### The `databricks-connect` setup pain

The local `databricks-connect` package's major.minor must match the cluster's DBR version. Installing `databricks-connect` removes local `pyspark` (mutually exclusive). The VS Code extension defaulted to the wrong version for over a year ([GitHub #1391](https://github.com/databricks/databricks-vscode/issues/1391)). Module 2 flagged this; the practitioner habit is:
- **Pin `databricks-connect==<DBR major>.<DBR minor>.*` in pyproject.toml**
- **Coordinate DBR upgrades team-wide** — every engineer's local env must move together
- **Use `uv` or `poetry` for env management** so the swap is easy

### `display()` is expensive — `.show()` is cheaper

`display()` triggers a query, materializes results, renders rich HTML, and pulls 1000 rows by default. On a streaming source it spawns a streaming query. **For quick eyeballing in dev, prefer `df.limit(10).show()`** — it pulls only 10 rows and skips the HTML rendering.

### Library install conflicts on shared clusters

Module 2 covered this: Databricks "cannot guarantee the order in which specific libraries are installed." Built-in DBR libs override user libs; one community report had a wheel installed as a JAR. **The discipline:** pin all deps in a `pyproject.toml`-driven wheel built in CI, install that wheel as the cluster's only library, let DBR provide everything else.

### Cluster restart kills notebook state

`%pip install` at notebook level installs a library *for that session*; cluster restart kills it. Workaround: cluster libraries (persistent) or init scripts. For experimentation, `%pip install` is fine; for production, use cluster libraries via Asset Bundles.

---

## When NOT to use these patterns

- **Shallow MERGE on insert-only Bronze** — appending is faster; only MERGE when you actually need upsert semantics.
- **Watermarks on tables with 90+ day correction windows** — use cancel-and-replace MERGE on Silver instead.
- **File notification mode for low-volume feeds** — directory listing is simpler and free; only switch when listing dominates trigger time.
- **`Trigger.Continuous` for non-real-time SLOs** — pay for the latency you need, not more.
- **Custom RocksDB tuning when defaults work** — only when you've verified the default state store can't fit your state.

---

## Sanity check

1. Walk through your diagnostic loop for "the same job that ran in 20 min last week is now taking 90 min." Which UI tab first, what do you look for?
2. What's the discipline that makes a MERGE truly idempotent across re-runs, and why is `WHEN NOT MATCHED BY SOURCE` useful for SCD2 specifically?
3. When would you use Auto Loader's `useNotifications` mode vs default directory listing?
4. What does `Trigger.AvailableNow()` give you that `Trigger.Once()` didn't?
5. A schema-rename on a Silver table broke the streaming reader. What feature should have been enabled, and what's the recovery path?
6. A junior engineer's notebook PR has a 600-line single notebook with `display()` calls everywhere. Walk through the refactor.
7. Why is `databricks-connect` version coupling a team-coordination problem rather than a per-engineer problem?

---

## Further reading

- [Spark UI overview — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/compute/access-mode-limitations) (linked from cluster pages)
- [Auto Loader — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/ingestion/cloud-object-storage/auto-loader/)
- [Structured Streaming on Databricks](https://learn.microsoft.com/en-us/azure/databricks/structured-streaming/)
- [Schema evolution — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/data-engineering/schema-evolution)
- [Delta MERGE — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/delta/merge)
- [chispa — DataFrame comparison for tests](https://github.com/MrPowers/chispa)
- [Databricks Connect v2 — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-connect/)
- [Notebooks testing best practices — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/notebooks/testing)
- [Delta MERGE billions of records lessons — Confessions of a Data Guy](https://www.confessionsofadataguy.com/lessons-learned-from-merge-operations-with-billions-of-records-on-databricks-spark/)
