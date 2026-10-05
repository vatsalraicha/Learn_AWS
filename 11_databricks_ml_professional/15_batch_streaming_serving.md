# Module 15 — Batch & Streaming Serving

> **Goal of this module:** batch and streaming inference patterns on Databricks — `mlflow.pyfunc.spark_udf`, Lakeflow Jobs for batch, Structured Streaming for near-real-time. Real-time HTTP is Module 14; this module is the other two-thirds of inference.
>
> **Assumes:** Modules 02 (PyFunc), 05 (Spark ML), 14 (real-time serving for contrast).
>
> **Exam relevance:** Section 1's "Select SparkML model or single node model for an inference based on type: batch, real-time, streaming" lives here, plus several Spark ML scoring objectives.

---

## Coverage map (verbatim Sept 30 2025 exam objectives → where taught)

| Verbatim objective | Section anchor |
|---|---|
| Score a Spark ML model for a batch or streaming use case | "Batch inference — `mlflow.pyfunc.spark_udf`" + "Streaming inference" |
| Select SparkML model or single node model for an inference based on type: batch, real-time, streaming | "The three inference patterns — when each fits" |

> Cross-references: Module 14 (real-time serving — the third pattern); Module 04 (`fe.score_batch` for feature-aware batch scoring); Module 02 (PyFunc loaded via `spark_udf`).

> 🎯 **Decision rules:**
> - **"Score 100M rows nightly" → Lakeflow Job + `mlflow.pyfunc.spark_udf` (or `fe.score_batch` if features come from UC feature table).**
> - **"Score events as they arrive in Delta" → Structured Streaming + `spark_udf` with `.writeStream`.**
> - **"Synchronous per-request <100ms" → Mosaic AI Model Serving endpoint (Module 14). Never SparkML for real-time.**
> - **`spark_udf` argument order = signature column order.** Positional, not kwargs.
> - **Distractor: deploy SparkML model to real-time endpoint.** Spark startup latency makes it non-viable; convert to PyFunc / sklearn-equivalent for real-time, keep SparkML for batch.

---

## The three inference patterns — when each fits

| Pattern | When | Tooling | Latency | Throughput |
|---|---|---|---|---|
| **Batch** | "Score everything in this Delta table once a day" | Lakeflow Job + `spark_udf` or `fe.score_batch` | Hours OK | Millions of rows/min |
| **Streaming** | "Score events as they arrive in a Delta table" | Structured Streaming + `spark_udf` | Seconds | Thousands of events/sec |
| **Real-time** | "Synchronous per-request, p50 < 100ms" | Mosaic AI Model Serving | <100ms | Up to thousands of QPS |

**Roughly 80% of production ML inference is batch.** It's the default; only reach for streaming or real-time when the latency requirement demands it.

⚠️ **Exam trap:** suggesting Mosaic AI Model Serving for a "nightly score 100M rows" workload. Overkill — batch via `spark_udf` is faster, cheaper, and natural for Delta-backed data.

---

## Batch inference — `mlflow.pyfunc.spark_udf`

The default pattern on Databricks. Wraps any MLflow model as a Spark UDF, applies row-wise across a Spark DataFrame.

```python
import mlflow

# Load the model as a Spark UDF
spark_udf = mlflow.pyfunc.spark_udf(
    spark,
    model_uri="models:/prod.ml.fraud_classifier@champion",
    result_type="double",  # or "integer", "string", or a complex type
)

# Apply to a Delta table
features_df = spark.read.table("prod.fraud.features_for_scoring")
scored = features_df.withColumn(
    "fraud_score",
    spark_udf("amount", "merchant_category", "txn_count_30d"),  # ← positional args matching signature
)

# Write results to Delta
(scored
 .select("transaction_id", "fraud_score", "customer_id")
 .write
 .mode("overwrite")
 .saveAsTable("prod.fraud.scored_transactions_daily"))
```

**Three details to memorize:**

1. **`model_uri` accepts the alias-based URI** — `models:/<full-name>@<alias>`. So the same code points to the current champion automatically.
2. **Args are positional** — must match the order in the model signature.
3. **`result_type`** — set explicitly. The default may not match what your model returns.

⚠️ **Exam trap:** passing args as a dict (`spark_udf({"amount": ..., "category": ...})`). The UDF expects positional Spark columns.

⚠️ **Exam trap 2:** loading by run URI (`runs:/<run_id>/model`) for production batch. Brittle — the run URI is immutable, breaks when you retrain. Always use alias URIs.

---

## Batch via `fe.score_batch` — when feature lookups are needed

For models logged with `fe.log_model` (feature lookups baked in), batch scoring auto-joins from the offline feature table.

```python
from databricks.feature_engineering import FeatureEngineeringClient
fe = FeatureEngineeringClient()

# Caller passes only keys + non-feature inputs
events_to_score = spark.read.table("prod.fraud.events_to_score").select(
    "event_id", "customer_id", "event_ts"  # no features
)

scored = fe.score_batch(
    model_uri="models:/prod.fraud.classifier@champion",
    df=events_to_score,
)
# `scored` now has the original cols + the joined features + `prediction`
scored.write.mode("overwrite").saveAsTable("prod.fraud.scored_events")
```

`fe.score_batch` reads the feature lookups baked into the model artifact, joins from the offline feature table (with point-in-time semantics if `timestamp_lookup_key` was used at training), and predicts.

⚠️ **Exam trap:** using `spark_udf` with a feature-lookup-baked model. `spark_udf` doesn't auto-join features; the model receives only the inputs the caller passed and errors on missing feature columns. Use `fe.score_batch` for feature-lookup models.

---

## Streaming inference

`spark_udf` works seamlessly on Structured Streaming DataFrames. The model loads once per executor and applies per-microbatch.

```python
import mlflow

spark_udf = mlflow.pyfunc.spark_udf(
    spark,
    model_uri="models:/prod.fraud.classifier@champion",
    result_type="double",
)

stream = (
    spark.readStream
    .format("delta")
    .table("prod.raw.transactions")
    .withColumn("fraud_score", spark_udf("amount", "merchant_category", "txn_count_30d"))
)

query = (
    stream
    .writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", "/dbfs/checkpoints/fraud_streaming_scoring")
    .trigger(processingTime="30 seconds")
    .toTable("prod.fraud.scored_transactions_streaming")
)
```

**Two details exam-relevant:**

- **`checkpointLocation`** — required for fault-tolerant streaming. Lost checkpoint = lost state.
- **`trigger(processingTime="30 seconds")`** — sets the microbatch cadence. Lower = lower latency, higher cost.

`outputMode="append"` is the default and only mode supported for streaming inference into a target table (since rows are immutable predictions).

⚠️ **Exam trap:** assuming the model auto-reloads when `@champion` changes. **It does not.** The model is bound at job start. To pick up a new champion, restart the streaming query (or implement a custom refresh).

---

## Picking a model for each pattern

Section 1 objective: *"Select SparkML model or single node model for an inference based on type: batch, real-time, streaming."*

| Pattern | SparkML model | Single-node (sklearn/XGB/LGB) via PyFunc |
|---|---|---|
| **Batch** | ✓ Native; PipelineModel.transform | ✓ Via `spark_udf` |
| **Streaming** | ✓ Native; supports Structured Streaming | ✓ Via `spark_udf` |
| **Real-time** | ✗ Spark overhead too high | ✓ Native fit for Mosaic AI Serving |

**Decision tree:**

- Real-time → single-node model on Mosaic AI Model Serving.
- Streaming → either works; `spark_udf` is simpler when starting from a single-node model.
- Batch → either works; SparkML if data already in DataFrame pipeline; single-node + `spark_udf` if model was developed in sklearn.

⚠️ **Exam trap:** "Real-time inference with a Spark ML pipeline." Wrong — Spark startup cost dominates. Use sklearn / XGB on a serving endpoint.

---

## Lakeflow Jobs for batch — production cadence

The exam frames batch as a scheduled Lakeflow Job (not an ad-hoc notebook):

```yaml
resources:
  jobs:
    fraud_daily_scoring:
      name: "fraud-${bundle.target}-daily-scoring"
      tasks:
        - task_key: load_features
          notebook_task: { notebook_path: ./src/load_features }
          job_cluster_key: scoring_cluster

        - task_key: score
          depends_on: [{ task_key: load_features }]
          notebook_task: { notebook_path: ./src/score_batch }
          job_cluster_key: scoring_cluster

        - task_key: publish
          depends_on: [{ task_key: score }]
          notebook_task: { notebook_path: ./src/publish_results }
          job_cluster_key: scoring_cluster

      job_clusters:
        - job_cluster_key: scoring_cluster
          new_cluster:
            spark_version: "15.4.x-cpu-ml-scala2.12"
            node_type_id: "Standard_E16ds_v5"
            num_workers: 4
            runtime_engine: "PHOTON"

      schedule:
        quartz_cron_expression: "0 0 2 * * ?"   # 2 AM UTC daily
        timezone_id: UTC
```

Why a job over an interactive notebook on a schedule:

- **Job clusters** — cheaper, ephemeral, no shared state.
- **Repair runs** if a task fails (Module 09).
- **Audit trail** in the job runs UI.
- **Notification on failure**.

⚠️ **Exam trap:** scheduling an interactive notebook on an all-purpose cluster for nightly batch. Job clusters are the exam-correct answer.

---

## Re-using the offline feature table for batch

When training used `FeatureLookup` with `timestamp_lookup_key`, batch scoring must respect the same temporal logic. `fe.score_batch` does this automatically; manual joins must mimic the as-of-time semantics.

```python
# Manual point-in-time join (when not using fe.score_batch)
from pyspark.sql import Window
import pyspark.sql.functions as F

events = spark.read.table("prod.fraud.events_to_score").select(
    "event_id", "customer_id", "event_ts"
)
features = spark.read.table("prod.fraud.customer_features")

# As-of-time: pick the most recent feature row per customer per event_ts
joined = (
    events.alias("e")
    .join(features.alias("f"), F.col("e.customer_id") == F.col("f.customer_id"))
    .where(F.col("f.computed_at") <= F.col("e.event_ts"))
    .withColumn(
        "rank",
        F.row_number().over(
            Window.partitionBy("e.event_id")
            .orderBy(F.col("f.computed_at").desc())
        ),
    )
    .where(F.col("rank") == 1)
    .drop("rank", "f.customer_id")
)
```

The exam can ask about this — most candidates haven't written a manual as-of-time join. **The canonical correct answer is `fe.score_batch`**, but understanding the underlying SQL is useful for debugging when results look off.

---

## Performance tuning batch inference

A few patterns the exam expects you to recognize:

### Co-locate features with events

If the features table is small enough, broadcast-join it:

```python
from pyspark.sql.functions import broadcast
joined = events.join(broadcast(features), "customer_id")
```

Avoids the shuffle.

### Partition output by date

```python
scored.write.mode("overwrite").partitionBy("scoring_date").saveAsTable("prod.fraud.scored_transactions")
```

Downstream consumers can filter by partition.

### Sized cluster

For a 100M-row batch, plan ~4-8 workers of moderate size. Photon enabled. Watch the Spark UI for skew (one task taking forever) — usually fixed with salting or repartitioning on the join key.

⚠️ **Exam trap:** "Use a single all-purpose cluster with 64 GB of memory for batch inference of 100M rows." Single-node + 100M rows = OOM. Distribute via SparkML or `spark_udf` on a multi-worker cluster.

---

## Common batch / streaming failure modes

1. **Schema drift** — the production data adds a column the model wasn't trained on. `spark_udf` either errors or silently passes wrong types. Solution: schema validation step before scoring; alert on drift.
2. **Stale champion** — streaming job started with v5 cached; new `@champion` is v6 but the streaming query doesn't pick it up. Solution: restart the query on alias change, or implement custom refresh.
3. **Wrong `result_type`** — model returns a struct but UDF declared `"double"`. Solution: match the result_type to the model's actual output.
4. **No checkpoint** — streaming inference job restarts and re-processes everything. Solution: always specify `checkpointLocation`.
5. **Late-arriving labels** — joining labels for monitoring (Module 13) but labels arrive after the partition was already monitored. Solution: monitor a rolling window with sufficient lookback for label arrival.

---

## Mini quiz

1. Default inference pattern (covers ~80% of cases) — batch / streaming / real-time?
2. Which API auto-joins feature lookups for batch?
3. Args to `spark_udf` — dict, positional, or named?
4. Streaming inference query — what's the single required option besides `outputMode`?
5. The model's `@champion` alias was reassigned. What happens to a long-running streaming inference job?
6. Why is SparkML wrong for real-time per-request inference?
7. You're scoring 100M rows nightly. What compute strategy?
8. Schema drift kills your batch job — what step should be in the pipeline before scoring?

**Answers:**

1. **Batch.** Roughly 80% of production ML inference.
2. `fe.score_batch(model_uri, df)` — the FE-in-UC API. The feature lookups baked into the model artifact handle the join.
3. **Positional**, in the order the model signature declares the inputs.
4. **`checkpointLocation`**. Without it, no fault tolerance; restart re-processes everything.
5. Nothing happens automatically — the model is bound at query start. To pick up the new champion, restart the streaming query. (Or implement custom alias-change detection.)
6. SparkSession startup overhead is too high for sub-100ms per-request synchronous inference. Real-time endpoints run single-node frameworks (sklearn / XGB / LGB) on Mosaic AI Model Serving.
7. Multi-worker Spark cluster (4-8 workers, moderate size, Photon enabled) running a Lakeflow Job with a `spark_udf` or SparkML PipelineModel transformation. Job cluster, not all-purpose.
8. **Schema validation** — read a sample, compare to the expected schema (the model's input signature), fail fast if columns are missing or types mismatch. Alert; don't silently score with garbage inputs.

---

## Sanity check

- Could you write the `spark_udf` batch pattern from memory?
- Do you remember `fe.score_batch` for feature-lookup models?
- Could you write a streaming inference query with checkpoint and trigger?
- Do you know why real-time needs single-node, not SparkML?
- Can you list the 5 common batch/streaming failure modes?

Move on to [Module 16 — Serving Observability](16_serving_observability.md) — the last module.
