# Module 3 — Feature Engineering in Unity Catalog

> **Goal of this module:** Master the `FeatureEngineeringClient` API surface — creating UC feature tables, building training sets with point-in-time lookups, scoring batch with feature lookups, and the online-vs-offline distinction. This is the **single highest-yield module** in Domain 1; expect 3-5 questions on it.
>
> **Maps to exam objectives:** *Identify the benefits of creating feature store tables at the account level in Unity Catalog vs at the workspace level · Create a feature store table in Unity Catalog · Write data to a feature store table · Train a model with features from a feature store table · Score a model using features from a feature store table · Describe the differences between online and offline feature tables* (Domain 1).

---

## Coverage map (verbatim exam objectives → where taught here)

| Verbatim objective | Taught in section |
|---|---|
| Benefits of UC vs workspace feature store | "Why UC over workspace store" |
| Create a feature store table in Unity Catalog | "Creating a feature table in UC" — `fe.create_table()` |
| Write data to a feature store table | "Writing data to an existing table" — `fe.write_table()` |
| Train a model with features from a feature store table | "Building a training set with feature lookups" + "Logging a model with feature metadata" |
| Score a model using features from a feature store table | "Scoring batch with feature lookups" — `fe.score_batch()` |
| Describe differences between online and offline feature tables | "Online vs offline feature tables" |

---

## The two clients — burn this into memory

There are two Python clients for feature management on Databricks. The exam tests the distinction explicitly.

| Client | Package | Scope | Status |
|--------|---------|-------|--------|
| `FeatureEngineeringClient` | `databricks-feature-engineering` | **Unity Catalog** (account-level) | **CURRENT** |
| `FeatureStoreClient` | `databricks-feature-store` | Workspace-local | **DEPRECATED** (since pkg v0.17.0) |

```python
# CURRENT — what the exam expects
from databricks.feature_engineering import FeatureEngineeringClient, FeatureLookup
fe = FeatureEngineeringClient()

# LEGACY — distractor on the exam
from databricks.feature_store import FeatureStoreClient
fs = FeatureStoreClient()
```

> ⚠️ **Exam trap #1 — the first sample question on the official guide tests exactly this.** If the scenario says "Unity Catalog feature table," the answer must use `FeatureEngineeringClient`. Picking `FeatureStoreClient.register_table()` is wrong.

### Method-name distinctions you must know

| `FeatureEngineeringClient` (UC) | `FeatureStoreClient` (legacy) |
|---|---|
| `create_table(name, primary_keys, df, ...)` | `create_table(name, primary_keys, ...)` (method exists but workspace-scoped) |
| (no `register_table` equivalent) | `register_table(delta_table, primary_keys, ...)` — legacy registration of an existing Delta table |
| `write_table(name, df, mode)` | `write_table(name, df, mode)` |
| `create_training_set(...)` | `create_training_set(...)` |
| `score_batch(model_uri, df)` | `score_batch(model_uri, df)` |
| `log_model(model, artifact_path, flavor, training_set, ...)` | `log_model(...)` |
| `publish_table(name, online_store)` | `publish_table(name, online_store)` |

The verbs are similar; the **import path is the tell**. On the exam, scan the `from` line first.

---

## Why UC over workspace store

Section 1 explicitly asks: *"Identify the benefits of creating feature store tables at the account level in Unity Catalog vs at the workspace level."* The answers Databricks wants:

1. **Cross-workspace sharing** — one feature table is reachable from any workspace in the account that has UC permissions on it. The workspace store siloes features per workspace.
2. **Centralized lineage** — UC tracks the lineage from raw Delta tables through feature tables to models that consume them, in one graph.
3. **ACL inheritance** — feature tables inherit UC's grant model. `GRANT SELECT ON TABLE catalog.schema.features TO data_scientists` just works.
4. **Decoupled from any single workspace** — workspace deletion doesn't take features with it.
5. **Unified catalog** — features live in the same three-level namespace as tables and models. No separate "feature store" mental layer.
6. **Online table publishing** — UC feature tables can be published to online stores (Databricks-managed) for low-latency serving.

> ⚠️ **Exam trap #2:** "Why would you use the workspace Feature Store?" is a trick question. **There's no good answer.** The workspace store is legacy. Don't pick "because it's simpler" or "because it's region-local" — neither is true.

---

## Creating a feature table in UC

```python
from databricks.feature_engineering import FeatureEngineeringClient
import pyspark.sql.functions as F

fe = FeatureEngineeringClient()

# Build feature DataFrame
features_df = (
    spark.read.table("retail.silver.transactions")
        .groupBy("customer_id")
        .agg(
            F.sum("amount").alias("total_spend"),
            F.count("*").alias("txn_count"),
            F.max("txn_date").alias("last_txn_date"),
        )
)

# Create the UC feature table
fe.create_table(
    name="retail.features.customer_features",
    primary_keys=["customer_id"],
    df=features_df,
    description="Customer-level RFM aggregates, refreshed daily",
    schema=features_df.schema,   # optional; inferred from df if omitted
)
```

**Required:**
- `name` — three-level UC name: `catalog.schema.table`
- `primary_keys` — list of column names. **Required.** This is what `FeatureLookup` joins on at training time.

**Optional but common:**
- `df` — initial data to populate. If omitted, creates an empty table; fill later with `write_table`.
- `timestamp_keys` — for point-in-time correctness on time-series features.
- `description`, `tags` — metadata.
- `partition_columns` — for performance.

### Writing data to an existing table

```python
# Overwrite (full refresh)
fe.write_table(
    name="retail.features.customer_features",
    df=features_df,
    mode="overwrite",
)

# Append (incremental)
fe.write_table(
    name="retail.features.customer_features",
    df=incremental_df,
    mode="merge",   # upsert by primary key
)
```

`mode="merge"` performs an upsert based on the primary key. `mode="overwrite"` replaces all rows.

---

## Building a training set with feature lookups

The point of a feature store is **lookup at training time**, joining features to labels by primary key. This avoids leaking future information into your training set.

```python
from databricks.feature_engineering import FeatureLookup

# Labels DataFrame: customer_id + the target column
labels_df = spark.read.table("retail.gold.churn_labels").select(
    "customer_id", "churned", "snapshot_date"
)

# Feature lookups: pull from one or more feature tables
training_set = fe.create_training_set(
    df=labels_df,
    feature_lookups=[
        FeatureLookup(
            table_name="retail.features.customer_features",
            lookup_key="customer_id",
            feature_names=["total_spend", "txn_count"],
            # rename_outputs={"total_spend": "spend"},  # optional aliasing
        ),
        FeatureLookup(
            table_name="retail.features.product_affinity",
            lookup_key="customer_id",
            feature_names=["top_category", "avg_basket_size"],
        ),
    ],
    label="churned",
    exclude_columns=["customer_id", "snapshot_date"],
)

training_df = training_set.load_df()
```

The returned `TrainingSet` object carries:
- The resolved feature columns
- The list of feature tables it pulled from
- The lookup keys used

This metadata flows into `fe.log_model` so that **at inference time**, the system knows to re-do the same lookups automatically. You don't repeat the joins in scoring code.

### Point-in-time lookups (time-series features)

When features have a `timestamp_keys` configured, you can pass a `timestamp_lookup_key` in `FeatureLookup` to fetch the feature value **as of** the label's timestamp — preventing future leakage:

```python
FeatureLookup(
    table_name="retail.features.customer_features",
    lookup_key="customer_id",
    timestamp_lookup_key="snapshot_date",   # as-of date
    feature_names=["total_spend_30d", "txn_count_30d"],
)
```

The feature table must have been created with `timestamp_keys=["feature_timestamp"]` for this to work.

---

## Logging a model with feature metadata

`fe.log_model` wraps `mlflow.<flavor>.log_model` and additionally attaches the **feature lookup spec** to the model's MLflow run. This is how scoring later "knows" to look up features automatically.

```python
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier

# Train on the materialized training_df (excludes customer_id, etc.)
X = training_df.toPandas().drop(columns=["churned"])
y = training_df.toPandas()["churned"]

model = RandomForestClassifier(n_estimators=100, max_depth=10)
model.fit(X, y)

# Log model WITH the training_set so feature spec is preserved
fe.log_model(
    model=model,
    artifact_path="model",
    flavor=mlflow.sklearn,
    training_set=training_set,     # critical: preserves lookup metadata
    registered_model_name="retail.models.churn",
)
```

> ⚠️ **Exam trap #3:** `fe.log_model` (not `mlflow.sklearn.log_model`) is what preserves feature lookup metadata. If a question says "the model needs to do automatic feature lookups at scoring time," the training code must use `fe.log_model`. Plain `mlflow.sklearn.log_model` doesn't carry the lookup spec.

---

## Scoring batch with feature lookups

At inference, you pass a "lookup" DataFrame containing **only the primary keys** (and any non-feature columns you want passed through). `fe.score_batch` joins the features for you:

```python
new_customers_df = spark.table("retail.silver.new_signups").select("customer_id")

predictions = fe.score_batch(
    model_uri="models:/retail.models.churn@champion",
    df=new_customers_df,
)
# predictions DataFrame includes: customer_id, the looked-up features, and `prediction`
```

This is **the killer feature** of the UC Feature Engineering stack: the scoring caller doesn't need to know which features the model uses or where they live. The model carries that spec.

### Comparison to manual joining

Without `fe.score_batch`, the alternative would be:

```python
# Manual approach — DON'T do this if you logged with fe.log_model
import mlflow

# Load model
model = mlflow.pyfunc.load_model("models:/retail.models.churn@champion")

# Manual join — error-prone, drifts from training-time logic
scored = (
    new_customers_df
        .join(spark.table("retail.features.customer_features"), "customer_id")
        .join(spark.table("retail.features.product_affinity"), "customer_id")
)

# Apply model
features_for_predict = scored.select(["total_spend", "txn_count", "top_category", "avg_basket_size"])
predictions = model.predict(features_for_predict.toPandas())
```

If the feature schema evolves (a feature added, renamed, dropped), the manual path silently fails or skews. `fe.score_batch` follows the model's logged spec exactly.

---

## Online vs offline feature tables

This is a high-yield exam objective.

### Offline (default)

- **Backing store:** Delta table in UC.
- **Latency:** seconds-to-minutes (full Spark scan).
- **Use case:** Batch training, batch scoring.
- **Capacity:** Billions of rows fine.
- **Created by:** `fe.create_table()`.

### Online

- **Backing store:** Databricks-managed online table (low-latency KV store; previously DynamoDB / Cosmos DB / Aurora bridge in legacy workspace store).
- **Latency:** Single-digit ms per lookup.
- **Use case:** Real-time serving — the Model Serving endpoint can hit the online table for sub-100ms feature retrieval.
- **Created by:** `fe.publish_table(name, online_store=...)`, taking an offline UC feature table and replicating it to online.

```python
# Publish offline UC table to online
fe.publish_table(
    name="retail.features.customer_features",
    online_store=...,   # online store spec
)
```

> ⚠️ **Exam trap #4 — online vs offline:**
> - "Tens of thousands of events per second, batch dashboard" → **offline** (Delta).
> - "Realtime endpoint returns predictions in <100ms per request" → **online** required (Delta scan is too slow).
> - The serving endpoint can do lookups from online tables; **it cannot do lookups from offline (Delta) tables at request latency.**

---

## Comparing online and offline — exam-targetable table

| Dimension | Offline (Delta in UC) | Online (online table) |
|-----------|-----------------------|------------------------|
| Backing storage | Delta in object store | Low-latency KV |
| Per-lookup latency | Seconds-to-minutes | Single-digit ms |
| Throughput | Massive (batch) | Per-request |
| Cost model | Storage + compute on scan | Always-on KV cost |
| Use | Training, batch scoring | Real-time serving |
| Created by | `fe.create_table` | `fe.publish_table` (must have offline first) |
| Freshness | Whatever your batch job writes | Synced from offline (configurable lag) |

---

## Common pitfalls

### Forgetting `timestamp_keys` for time-series features

If your feature table has a `feature_timestamp` column that represents "as-of" semantics, you **must** declare `timestamp_keys=["feature_timestamp"]` at table creation. Without it, `FeatureLookup` with `timestamp_lookup_key` doesn't work, and you'll silently get the most recent value for every label — leaking future data.

### Using `mlflow.sklearn.log_model` instead of `fe.log_model`

The model artifact gets logged, but **without** the feature lookup spec. Subsequent `fe.score_batch` calls fail because the model doesn't declare its feature inputs.

### Mistaking primary key for label

`primary_keys` in `create_table` is the **lookup key** (e.g., `customer_id`), not the prediction target. The label column is on the *labels DataFrame*, not the feature table.

### Forgetting `exclude_columns` in `create_training_set`

If `labels_df` has columns you don't want in training (`customer_id`, snapshot timestamps), pass them in `exclude_columns`. Otherwise they end up as features and may cause leakage.

---

## Worked exam-question walkthroughs

### Worked example (verbatim official Q1): "Create a feature table in UC"

**Pattern:** Four options to create a UC feature table.

A. Create Delta + use `FeatureStoreClient.register_table` — **legacy/workspace**
B. SQL `CREATE TABLE ... AS FEATURE STORE` — **does not exist**
C. `FeatureEngineeringClient.create_table()` then write data — **CORRECT**
D. ALTER TABLE ... SET AS FEATURE STORE — **does not exist**

**Answer:** C (matches official answer C).

### Worked example: "Why use UC over workspace?"

**Decision-rule mapping** for picking the right benefit:
- "share across workspaces" → cross-workspace UC sharing
- "audit lineage end-to-end" → unified UC lineage
- "GRANT EXECUTE ON MODEL" → ACL inheritance
- "same namespace as tables and models" → three-level namespace
- "real-time serving lookup" → online publishing

### Worked example: "Real-time endpoint feature lookup"

**Pattern:** Model needs <100ms predictions; features in UC offline table.

**Reasoning:** Offline = Delta = seconds-to-minutes per scan. Must publish to online.

**Answer:** `fe.publish_table(name=..., online_store=...)` then configure the serving endpoint to use the online table for lookups.

### Worked example: "Why does `fe.score_batch` fail when model logged with `mlflow.sklearn.log_model`?"

**Reasoning:** `mlflow.<flavor>.log_model` saves model artifact only. The feature lookup spec lives in `training_set` metadata that ONLY `fe.log_model(model, training_set=training_set)` preserves.

**Fix:** Re-train and use `fe.log_model(training_set=training_set, ...)`. Then `fe.score_batch` auto-joins features.

---

## Output prediction drills

### Drill 1
```python
fe.create_table(name="features.customer", primary_keys=["customer_id"], df=features_df)
```
**Q:** UC three-level name?
**A:** **Error.** Name must be `catalog.schema.table` (three levels). `features.customer` is only two.

### Drill 2
```python
fe.write_table(name="retail.features.customer", df=new_rows, mode="merge")
```
**Q:** What does `mode="merge"` do?
**A:** Upsert by primary key. Rows with matching PKs are updated; new PKs are inserted. Contrast with `mode="overwrite"` (replace all).

### Drill 3
```python
training_set = fe.create_training_set(df=labels_df, feature_lookups=[...],
                                       label="churned",
                                       exclude_columns=["customer_id"])
training_df = training_set.load_df()
# training_df columns?
```
**A:** All label-side columns EXCEPT `customer_id` + all looked-up feature columns + `churned` label. The primary key was used for the join then excluded from the training data.

---

## What the exam tests on this module

> 🎯 **Exam tests here:**
> - `FeatureEngineeringClient` (UC) vs `FeatureStoreClient` (legacy) — recognize the import path
> - `fe.create_table(name, primary_keys, df, ...)` signature
> - The benefits of UC over workspace store (cross-workspace, lineage, ACL, online publishing)
> - `FeatureLookup` with `table_name`, `lookup_key`, `feature_names`
> - `fe.create_training_set(df, feature_lookups, label, exclude_columns)`
> - `fe.log_model(model, artifact_path, flavor, training_set, ...)` and why `training_set=` matters
> - `fe.score_batch(model_uri, df)` and why the scoring DF only needs primary keys
> - Online vs offline — latency, use case, how each is created

---

## Mini quiz

1. You're writing training code that pulls from a UC feature table. Which import is correct?
   - **a)** `from databricks.feature_store import FeatureStoreClient`
   - **b)** `from databricks.feature_engineering import FeatureEngineeringClient`
   - **c)** `from mlflow.feature_store import Client`
2. You called `mlflow.sklearn.log_model(model, "model")` instead of `fe.log_model(...)`. The next day, `fe.score_batch(model_uri=...)` fails. Why?
3. Your model needs <100ms predictions in a real-time endpoint. The features live in a UC offline table. Walk through what you must do.
4. Name three benefits of UC feature tables over workspace feature tables.
5. Your training set has a `customer_id` column. Do you include it as a feature? Where do you declare to exclude it?

### Answers

1. **(b)** `from databricks.feature_engineering import FeatureEngineeringClient`. (a) is the legacy/workspace store. (c) doesn't exist.
2. `mlflow.sklearn.log_model` saves the model artifact but does **not** attach the feature lookup spec from the `TrainingSet`. `fe.score_batch` needs that spec to auto-join features at scoring time. Re-train using `fe.log_model(model=..., training_set=training_set, ...)`.
3. Call `fe.publish_table(name="catalog.schema.features", online_store=...)` to materialize an **online table** synced from the offline table. Configure the Model Serving endpoint to use the online table for lookups. Offline Delta scans are too slow for <100ms latency.
4. Any three of: cross-workspace sharing, centralized lineage, UC ACL inheritance, single three-level namespace, online table publishing support, decoupled from workspace lifecycle.
5. **No, don't use `customer_id` as a feature** — it's an identifier, not a predictive feature. Declare it in `exclude_columns=["customer_id"]` when calling `fe.create_training_set(...)`.
