# Quiz — Module 5: Spark on Databricks: Practitioner Discipline

## Recall

**Q1.** Name the five Spark UI tabs that matter and what each one is best for.

<details><summary>Answer</summary>

1. **SQL / DataFrame** — query plan, join strategies (BHJ/SMJ/SHJ), data skipping (numFilesPruned vs numFilesRead), AQE annotations, Photon vs JVM operators. **First stop for any DataFrame job.**
2. **Stages** — task-duration histograms, shuffle read/write per task, spill metrics. **Best for skew detection.**
3. **Storage** — cached RDDs/DataFrames, memory + disk consumption. **Caching diagnostics.**
4. **Executors** — per-node memory, GC time, failed-task pattern. **Node-level health.**
5. **Jobs / Stages summary** — job-level timing. **Find the slow stage, then drill into the others.**
</details>

**Q2.** What's the difference between `Trigger.AvailableNow()`, `Trigger.ProcessingTime()`, and `Trigger.Continuous()`?

<details><summary>Answer</summary>

- **`Trigger.AvailableNow()`** — process all currently-available data, then stop. The 2025+ recommended default for incremental batch (replaces the older `Trigger.Once()`). Run nightly; processes whatever arrived since the last run.
- **`Trigger.ProcessingTime("30 seconds")`** — micro-batch every N seconds. Default if unspecified (~500ms). Best for steady-state streaming with bounded latency SLO.
- **`Trigger.Continuous("1 second")`** — true continuous mode (sub-second latency). Limited operator coverage; rarely used in practice.

For most healthcare ETL, **`Trigger.AvailableNow()` triggered nightly via Workflows** is the right pattern.
</details>

**Q3.** What two improvements does `cloudFiles` (Auto Loader) give you over vanilla Structured Streaming on object storage?

<details><summary>Answer</summary>

1. **File listing optimization** — uses cloud-native notifications (`useNotifications=true`, Event Grid + Storage Queue on Azure) or efficient listing instead of repeatedly listing the directory. Critical when the source dir has > 10K files.
2. **Schema evolution** — auto-detects new columns and either fails / drops / rescues them based on `cloudFiles.schemaEvolutionMode` (`addNewColumns` default, `rescue`, `failOnNewColumns`, `none`).
</details>

---

## Apply

**Q4.** Write a MERGE statement that's truly idempotent across re-runs, using a `row_hash` column for change detection on a Silver claim_line target.

<details><summary>Answer</summary>

```python
from delta.tables import DeltaTable
import pyspark.sql.functions as F

# Compute row_hash on the source upstream
updates_df = (raw_df
              .withColumn("row_hash",
                          F.sha2(
                              F.concat_ws("|", 
                                          F.col("billed_amount"),
                                          F.col("paid_amount"),
                                          F.col("status"),
                                          F.col("adjustment_code")), 
                              256)))

target = DeltaTable.forName(spark, "silver.claim_line")

(target.alias("t")
  .merge(updates_df.alias("s"),
         "t.claim_id = s.claim_id AND t.claim_line_id = s.claim_line_id")
  .whenMatchedUpdate(
      condition="s.row_hash <> t.row_hash",   # only update if actual change
      set={
          "billed_amount":  "s.billed_amount",
          "paid_amount":    "s.paid_amount",
          "status":         "s.status",
          "adjustment_code":"s.adjustment_code",
          "row_hash":       "s.row_hash",
          "ingestion_ts":   "current_timestamp()",
      })
  .whenNotMatchedInsert(values={
          "claim_id":       "s.claim_id",
          "claim_line_id":  "s.claim_line_id",
          "billed_amount":  "s.billed_amount",
          "paid_amount":    "s.paid_amount",
          "status":         "s.status",
          "adjustment_code":"s.adjustment_code",
          "row_hash":       "s.row_hash",
          "ingestion_ts":   "current_timestamp()",
      })
  .execute())
```

**Why idempotent:** the `condition="s.row_hash <> t.row_hash"` on `whenMatchedUpdate` makes re-running the same source produce zero updates after the first run. With `delta.enableDeletionVectors`, even the first run's updates touch only the bytes that changed.
</details>

**Q5.** Refactor this 200-line notebook anti-pattern into the recommended `src/` modules + thin notebook + pytest pattern.

```python
# silver_member_month.py (notebook, .ipynb)
spark.sql("USE prod_catalog.silver")
claims = spark.table("claim_line")
elig = spark.table("eligibility")
df = claims.join(elig, ...).groupBy("member_id", ...).agg(...)
df.write.mode("overwrite").saveAsTable("member_month")
display(df)  # 1000-row render in notebook
```

<details><summary>Answer</summary>

**Module:**

```python
# src/silver/member_month.py
from pyspark.sql import SparkSession, DataFrame
import pyspark.sql.functions as F

def build_member_month(spark: SparkSession, catalog: str, schema: str) -> int:
    """Build member-month aggregate. Returns row count."""
    claims = spark.table(f"{catalog}.{schema}.claim_line")
    elig   = spark.table(f"{catalog}.{schema}.eligibility")
    
    member_month = (
        claims.alias("c")
        .join(elig.alias("e"),
              (F.col("c.member_id") == F.col("e.member_id")) &
              (F.col("c.service_date").between(F.col("e.eff_dt"), F.col("e.term_dt"))),
              "inner")
        .groupBy("c.member_id", 
                 F.date_trunc("month", F.col("c.service_date")).alias("year_month"))
        .agg(F.sum("c.paid_amount").alias("paid"),
             F.count("c.claim_line_id").alias("claim_count"))
    )
    
    target = f"{catalog}.{schema}.member_month"
    member_month.write.format("delta").mode("overwrite").saveAsTable(target)
    return member_month.count()
```

**Notebook (thin runner):**

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
    print(f"Wrote {n_rows} rows to {catalog}.{schema}.member_month")
```

**Test:**

```python
# tests/silver/test_member_month.py
import pytest
from chispa.dataframe_comparer import assert_df_equality
from pyspark.sql import SparkSession
from src.silver.member_month import build_member_month

@pytest.fixture(scope="session")
def spark():
    return (SparkSession.builder
              .master("local[2]")
              .appName("test")
              .config("spark.sql.warehouse.dir", "/tmp/spark-warehouse")
              .getOrCreate())

def test_basic_member_month(spark, tmp_path):
    # ... build small fixture claims and eligibility DataFrames
    # ... write them to a test catalog/schema
    # ... call build_member_month
    # ... assert the result matches expected
    pass
```

**What changed:**
- Logic moved to **`src/silver/member_month.py`** — reviewable as plain Python, testable without a cluster.
- Notebook is **30 lines** that orchestrate parameters + MLflow + the call. Reviewable in seconds.
- **`display()` removed** — the notebook output isn't a debugging tool; if reviewers need to see the data, they query the result table.
- **`pytest` test** runs in CI without a cluster (local Spark or Databricks Connect).

The PR review burden drops from ~45 minutes to ~5 minutes.
</details>

---

## Diagnose

**Q6.** A streaming Bronze pipeline that processes claims has been running for 6 months. The team gets paged because tasks are taking 4× longer than baseline. The cluster Storage tab shows nothing in cache. The data volume hasn't increased. Walk through the diagnosis.

<details><summary>Answer</summary>

**Hypothesis menu** (in order of likelihood):

1. **Small file accumulation** — 6 months of streaming Bronze writes. If Auto-Compact alone is enabled (no scheduled OPTIMIZE), files cap at ~128 MB and accumulate as thousands per partition. Reads slow as the file count grows.
   - **Check:** count files per partition: `DESCRIBE DETAIL table` shows `numFiles`. Or in the Spark UI's SQL plan, look at `numFilesRead`.
   - **Fix:** schedule weekly OPTIMIZE; enable Predictive Optimization on UC managed tables.

2. **Data skipping silently broke** — schema grew over 6 months; filter columns drifted past the first 32. `delta.dataSkippingNumIndexedCols = 32` default means stats stopped being collected for the new columns.
   - **Check:** Spark UI SQL plan — `numFilesPruned = 0` despite the WHERE clause? Yes → no skipping.
   - **Fix:** `delta.dataSkippingStatsColumns` to name the hot filter columns explicitly.

3. **State store growth** — if the streaming pipeline does aggregation or stream-stream joins, state grows over time without watermark cleanup.
   - **Check:** Executors tab — GC time elevated? RAM pressure?
   - **Fix:** add or shorten watermarks; switch to RocksDB state store.

4. **Spot preemption frequency increased** — Azure region hitting Spot capacity pressure.
   - **Check:** `system.compute.clusters` for cluster events; Executors tab for failed-task pattern.
   - **Fix:** more On-Demand workers, or move to Serverless Jobs.

5. **Cluster start time degraded** — instance pool or cluster pool changes.
   - **Check:** cluster event log.
   - **Fix:** instance pools, or move to Serverless.

**The discipline:** form the hypothesis from the symptom, then *verify* in the right UI tab. Don't randomly tune.
</details>

**Q7.** A team has 50 engineers, all running their own All-Purpose dev clusters. The bill is huge. The platform team rolls out Databricks Connect with VS Code as the recommended local-dev path. Two weeks later, half the team's local environments are broken. What happened, and how do you fix it?

<details><summary>Answer</summary>

**Most likely cause:** `databricks-connect` version mismatch with cluster DBR.

The package's major.minor must match the cluster's DBR (`databricks-connect==17.3.*` for DBR 17.3 LTS). Installing `databricks-connect` also removes local `pyspark` (mutually exclusive). The VS Code extension defaulted to a fixed version for a long stretch ([GitHub #1391](https://github.com/databricks/databricks-vscode/issues/1391)).

What probably happened:
- Some engineers installed `databricks-connect` with `pip install databricks-connect` (gets latest) on a workspace with DBR 16.4 LTS clusters → mismatch errors
- Others had local `pyspark` installed for non-Databricks projects, and `databricks-connect` install removed it
- Some clusters were recently upgraded to DBR 17.3 but local envs weren't updated → mismatch on the other direction

**The fix:**
1. **Pin `databricks-connect==<DBR-major>.<DBR-minor>.*`** in a project `pyproject.toml`. Use `uv` or `poetry` for env management.
2. **Document the canonical DBR per project** in the README. When the cluster upgrades, update the pinned dep and bump everyone's local env in coordinated fashion.
3. **Use Databricks Connect with the new IDE features** (the 2025 IDE) which manages this automatically for greenfield projects.
4. **For projects that need local PySpark separately**, isolate them in their own venv — don't share with `databricks-connect` projects.

**The systemic point:** this is a *team-coordination* problem, not a per-engineer problem. DBR upgrades are infrastructure events that touch every engineer's local env. Treat them like any other coordinated-rollout change. Module 17 has the DBR upgrade runbook.
</details>

---

## Defend

**Q8.** A peer engineer says "we should put `display(df)` calls everywhere in our pipeline notebooks for visibility." Defend or refute.

<details><summary>Answer</summary>

**Refute, with calibration.**

`display(df)` is fine for **interactive exploration in dev**. In production pipeline notebooks, it's an anti-pattern for at least four reasons:

1. **It triggers a full Spark query** — even on a "preview" expectation, it materializes 1000 rows by default. Cost surprise on large DataFrames.
2. **It renders rich HTML** — embedded in notebook output, blowing up notebook revision storage and Git diff size.
3. **It commits PHI to control-plane storage** — for any healthcare workspace, `display(df)` on a DataFrame containing member-level data persists that data in the notebook revision history (control plane). The notebook source is governed under managed-services CMK, but it's still a place PHI is written that the architect didn't necessarily intend. The workspace setting *"Store interactive notebook results in customer account"* mitigates this but is rarely enabled.
4. **It pulls data to the driver** — `display()` is similar to `collect()` for the rendered subset; on a sufficiently large frame it triggers OOM.

**The right pattern:**
- For pipeline observability: write summary metrics to MLflow (`mlflow.log_metric`) or to a dedicated `_observability.pipeline_metrics` Delta table. Both are queryable, governed, and don't pollute notebook outputs.
- For per-run debugging: use `df.printSchema()` and `df.limit(10).show()` (cheaper than `display()`).
- For dashboards: build a Lakeview dashboard or a Databricks SQL alert on the pipeline metrics table.

**Where `display()` is fine:** Dev notebooks during initial development, throwaway analyses, demo content. Anywhere it isn't going through code review and doesn't persist past the session.

**Production discipline:** treat `display()` calls in PR'd code the way you'd treat `print()` statements in production Python — almost always wrong, occasionally justified with a comment explaining why.
</details>

**Q9.** A peer engineer says "watermarks are the answer to all our late-data problems." Defend or refute, in the context of a healthcare claims pipeline where corrections can arrive 90+ days after the original message.

<details><summary>Answer</summary>

**Refute, with calibration.**

Watermarks are the right tool for **streaming aggregations / stateful operations** where:
- The latency requirement is real-time (minutes to seconds)
- Late data beyond the watermark is acceptable to drop
- Continuous state cleanup is required to keep memory bounded

For healthcare claims with **90+ day correction windows**, watermarks are the wrong tool because:

1. **A 90-day watermark = 90 days of state** in the streaming engine. Memory grows; state-store performance degrades; cluster cost balloons.
2. **Dropping data beyond the watermark loses claim corrections** — a HIPAA / accounting / audit problem.
3. **Watermark semantics are about *event time* state cleanup, not corrections** — a "correction" in claims is logically a new message that supersedes a prior one, not a late-arrival of the original.

**The right pattern for healthcare:**
- **Use watermarks** on truly real-time aggregations: last-hour denials, this-shift admissions, current-day in-network utilization. Watermark of 1–4 hours is appropriate.
- **Use cancel-and-replace MERGE** on Silver tables for the correction case. The original message stays in Bronze (immutable, regulator-friendly); a correction comes in as a new message; the Silver pipeline applies a MERGE that marks the original as `is_canceled = true` and inserts the new message.
- **Use Change Data Feed** to feed downstream consumers (audit pipeline, ML feature store, Gold aggregations) with the row-level change events.

**The synthesis:** watermarks aren't *the* answer to late data; they're one tool with a specific use. For long-horizon corrections, MERGE on Silver + CDF for downstream propagation is the right architecture. Module 3 has the patterns; Module 22 has the healthcare-specific reference architecture.
</details>
