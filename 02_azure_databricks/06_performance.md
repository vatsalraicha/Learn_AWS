# Module 6 — PySpark + Spark SQL Performance on Databricks

> **Goal of this module:** the practitioner cookbook for making PySpark and Spark SQL fast on Databricks specifically. Joins, skew, shuffle, caching, Photon-aware code, file layout for query speed, AQE 2024–2026, DBSQL warehouse tuning. The "best ways to join two tables" answer for the lakehouse era.
>
> **Assumes:** you can read `df.explain(extended=True)` and recognize a `BroadcastHashJoin` vs a `SortMergeJoin`. We start at the discipline level.

---

## Why this module is its own thing

Module 5 covered *operational* discipline — how to use the Spark UI to diagnose problems. This module is the **performance cookbook** — given a workload, how do you make it run as fast as it can on Databricks. The two are companions. The diagnostic loop in Module 5 sends you here when the answer is "the job is slow because the join strategy is wrong" or "the file layout is wrong for the query pattern."

The 2026 hierarchy of who optimizes what:
1. **CBO (Cost-Based Optimizer)** picks the initial plan from stats.
2. **AQE (Adaptive Query Execution)** corrects at runtime based on actual stage outputs.
3. **Photon** executes whatever plan survives, falling back to JVM Spark per-operator when needed.
4. **Liquid Clustering + Predictive Optimization** keep the file layout aligned with query patterns automatically.

Your job as the engineer: (a) **stay out of AQE's way** (don't pin shuffle partition counts unnecessarily, don't use legacy hints), (b) **write Photon-friendly code** (built-ins, not Python UDFs), and (c) **declare the right cluster keys** for the join and filter patterns the workload actually does.

---

## Join strategies — knowing which one fires and why

Spark physically executes joins as one of four strategies. The choice (or letting AQE choose) is the single biggest lever in PySpark performance.

### Broadcast Hash Join (BHJ) — the default for small-side joins

The optimizer ships the small side to every executor and avoids a shuffle entirely. The threshold is governed by `spark.sql.autoBroadcastJoinThreshold` (OSS default 10 MB) plus an additional Databricks AQE-time threshold `spark.databricks.adaptive.autoBroadcastJoinThreshold` (~30 MB) that allows broadcasting based on **actual** post-shuffle size, not just the optimizer's estimate ([Databricks AQE docs](https://docs.databricks.com/aws/en/optimizations/aqe)).

**Practitioner discipline:**

- The threshold operates on **estimated size**, not row count. Wide tables with many string columns blow up beyond their on-disk Parquet size after decompression — that's why a broadcast you forced via hint can still OOM the driver.
- Databricks documents the absolute upper bounds: roughly **8 GB and 512 million records** per broadcast ([Databricks community](https://community.databricks.com/t5/data-engineering/what-is-the-maximum-limit-of-data-that-can-be-broadcasted-using/td-p/18600)).
- Force a broadcast with `from pyspark.sql.functions import broadcast; df.join(broadcast(small_df), "k")` or the SQL hint `/*+ BROADCAST(small_df) */`.
- Disable broadcasting completely (useful when a `BroadcastNestedLoopJoin` appears — almost always a sign of a missing equi-join key) by setting the threshold to `-1` ([Databricks KB](https://kb.databricks.com/sql/disable-broadcast-when-broadcastnestedloopjoin)).
- **The hint alone doesn't override the threshold** — you also have to raise `spark.sql.autoBroadcastJoinThreshold` if the table size estimate exceeds the configured threshold ([Databricks KB on broadcast hint not used](https://kb.databricks.com/execution/broadcast-join-hash-not-being-used-despite-hints)).
- **Driver OOM on broadcast** is a Databricks-support classic. The driver materializes the broadcast variable before shipping; pick a driver with at least 4× the broadcast size in memory ([Databricks KB](https://kb.databricks.com/sql/bchashjoin-exceeds-bcjointhreshold-oom)).

```python
from pyspark.sql.functions import broadcast

# Force broadcast even if AQE doesn't pick it
big = spark.table("silver.claim_line")
small = spark.table("silver.dim_payer")  # 200 rows
result = big.join(broadcast(small), "payer_id")
```

### Sort-Merge Join (SMJ) — the default for big-big joins

Both sides are shuffled by the join key, sorted within each partition, and merged. Safe default but expensive — pays for both shuffle and sort. The way to make SMJ cheaper is rarely to fight Spark; it's to **make the inputs smaller before they hit the join** (predicate pushdown, projection pruning, partition pruning, pre-aggregation) and to use **Liquid Clustering on the join key** so co-located ranges skip shuffle entirely ([Spark perf tuning](https://spark.apache.org/docs/latest/sql-performance-tuning.html)).

### Shuffle Hash Join (SHJ) — niche but useful

Builds a hash table per partition without sorting. Spark prefers SMJ over SHJ by default because SMJ has better memory-spill behavior, but SHJ wins when one side is meaningfully smaller per partition than the other but still too large to broadcast. Force with `/*+ SHUFFLE_HASH(t) */`.

### Broadcast Nested Loop Join (BNLJ) — almost always a bug

Fires for non-equi joins (`a.ts BETWEEN b.start AND b.end`) when no broadcast hint disables it. **O(N×M).** If the Spark UI shows a `BroadcastNestedLoopJoin` node and the query is slow, the fix is usually to rewrite the predicate as an equality join via bucketing the time range, or to apply a range-join optimization.

### Runtime join strategy switching (AQE)

The biggest 2020+ improvement: with AQE on (default in DBR 7.3+), Spark can **demote a planned SMJ to a BHJ at runtime** once it observes the actual post-shuffle size of one side ([AQE blog](https://www.databricks.com/blog/2020/05/29/adaptive-query-execution-speeding-up-spark-sql-at-runtime.html)). Even if your optimizer-time stats are stale, AQE catches up after the first stage and avoids the second shuffle.

### Dynamic Partition Pruning (DPP) — fact-dimension joins

DPP fires when joining a large partitioned (or clustered) fact table with a filtered dimension table on the partition column. Spark builds a broadcast filter from the dimension's filtered values and pushes it as a runtime predicate to the fact-table scan, **pruning entire partitions that can't match** ([Databricks DFP blog](https://www.databricks.com/blog/2020/04/30/faster-sql-queries-on-delta-lake-with-dynamic-file-pruning.html)).

The Databricks-specific extension: `spark.databricks.optimizer.dynamicFilePruning` (default `true`) extends DPP from partition columns to **any column with statistics** — so a `WHERE region = 'US'` filter on a non-partitioned but Liquid-Clustered fact table still skips files at runtime. **DPP silently fails when the dimension filter is non-deterministic or wrapped in a UDF.**

### Streaming joins

- **Stream-static** — cheap; the static side is broadcast or read fresh per micro-batch. No state.
- **Stream-stream** — requires watermarks on **both** sides plus a time-bound join condition; otherwise state grows unbounded ([Databricks watermark docs](https://docs.databricks.com/aws/en/structured-streaming/watermarks)). Output mode restricted to append. The engine maintains one global watermark — the slowest stream sets it.

---

## Skew handling

Skew = a few partition keys have orders of magnitude more rows than the median. The Spark UI signature: **one or two stragglers in the join stage running 10× longer than peers, with massively imbalanced shuffle reads.**

### AQE skew join — try this first

`spark.sql.adaptive.skewJoin.enabled` is `true` by default. AQE detects a partition as skewed when both:
- `partition_size > skewedPartitionFactor * median_partition_size` (default factor=5)
- `partition_size > skewedPartitionThresholdInBytes` (default 256 MB)

Skewed partitions are **split into smaller subpartitions and replicated against the matching partition on the other side.** Databricks recommends relying on AQE skew handling rather than the legacy `/*+ SKEW */` hint ([Databricks AQE docs](https://docs.databricks.com/aws/en/optimizations/aqe)).

### When AQE skew handling doesn't fire — salting

AQE only operates **after a shuffle, only on SMJ and SHJ**, and won't help if your skew is below the absolute threshold but still hurting tail latency, or in stream-stream joins where AQE doesn't apply ([Community on AQE limitations](https://community.databricks.com/t5/community-articles/understanding-coalesce-skewed-joins-and-why-aqe-doesn-t-always/td-p/115586)).

The salting pattern in PySpark:

```python
from pyspark.sql import functions as F

NUM_SALTS = 50

# Skewed left side: assign random salt
left_salted = (
    df_large
    .withColumn("salt", (F.rand() * NUM_SALTS).cast("int"))
    .withColumn("k_salted", F.concat_ws("-", F.col("k"), F.col("salt")))
)

# Right side: replicate N times so every salt has a match
right_salted = (
    df_small
    .withColumn("salt", F.explode(F.array([F.lit(i) for i in range(NUM_SALTS)])))
    .withColumn("k_salted", F.concat_ws("-", F.col("k"), F.col("salt")))
)

joined = left_salted.join(right_salted, "k_salted").drop("k_salted", "salt")
```

The cost is a `NUM_SALTS`× explosion of the small side. Pick the salt count to balance shuffle reduction against the inflation of the smaller table.

### Photon and skew

Photon's columnar shuffle is generally more memory-efficient under skew because it processes batches rather than rows, but **skew is a partitioning problem, not an engine problem** — Photon does not magically dissolve a hot key.

### Don't partition by a high-cardinality, skew-prone column

A common healthcare-data anti-pattern: partitioning a claims table by `member_id` or `patient_id`. You get millions of tiny partitions, the metastore chokes on listing, and joins remain skewed because the partition column is also the join column. **Use Liquid Clustering** on `member_id` instead.

---

## Shuffle and AQE in detail

### The default-200 myth

`spark.sql.shuffle.partitions` defaults to 200. With AQE on, this is the **initial** count after shuffle; AQE then coalesces post-shuffle partitions into reasonably-sized ones based on actual map output sizes. So the practical advice on Databricks is to **set the initial number high (1000–4000 for large jobs) and let AQE coalesce down** ([Databricks community](https://community.databricks.com/t5/data-engineering/tuning-shuffle-partitions/td-p/22378), [Confessions of a Data Guy](https://www.confessionsofadataguy.com/how-to-tune-spark-shuffle-partitions/)).

### Auto-Optimized Shuffle (Databricks-specific)

`spark.databricks.adaptive.autoOptimizeShuffle.enabled`. **Off by default.** When enabled, picks the initial shuffle partition number based on data size and executor count, removing the need to tune `spark.sql.shuffle.partitions` manually. Suitable for "the vast majority of use cases."

### AQE coalesce post-shuffle partitions

`spark.sql.adaptive.coalescePartitions.enabled` (true by default). After each shuffle, AQE looks at map output stats and merges adjacent small partitions. Target output partition size: `spark.sql.adaptive.advisoryPartitionSizeInBytes` (default **64 MB**).

### Photon shuffle vs JVM shuffle

Photon implements its own **columnar shuffle** that's incompatible with JVM Spark's row-based shuffle format — once a stage is Photon, the next read must also be Photon. When Photon falls back (UDFs, unsupported operators), the boundary incurs a **format conversion**. Photon uses off-heap memory and coordinates with Spark's unified memory manager, so insufficient cluster memory shows up as shuffle spills regardless of which engine is running ([Databricks Photon docs](https://docs.databricks.com/aws/en/compute/photon)).

---

## Caching — there are actually four layers

Engineers conflate these. They behave differently and live in different places.

### `df.cache()` / `df.persist()` — JVM/Photon executor memory

In-memory or memory-and-disk on the **executor JVM** (or Photon's off-heap). **Lazy:** only materializes when an action triggers it. `df.cache().count()` is the idiomatic force. Lost on cluster restart, lost when an executor dies. Useful for iterative algorithms (ML training loops) where the same DataFrame is scanned repeatedly.

### Disk Cache (formerly Delta cache / IO cache) — local SSD

Auto-managed cache of remote Parquet files on the worker's local NVMe SSDs. **Enabled by default** on Databricks compute that uses SSD-backed instance types. Configuration: `spark.databricks.io.cache.enabled`. Works for all Parquet (including Delta), uses up to half of local SSD by default ([Disk cache docs](https://docs.databricks.com/aws/en/optimizations/disk-cache)).

The name was changed from "Delta cache" to "disk cache" specifically to reduce confusion that it was part of the Delta protocol.

### Photon's columnar in-memory cache

Photon also leverages a columnar in-memory representation that complements the disk cache for hot data. Provides "faster repeat access via the disk cache and improves throughput for concurrent queries in interactive BI workloads."

### DBSQL result cache and UI cache

Two distinct DBSQL-only caches:
- **Local query result cache** (per-warehouse): caches results for repeated queries within a warehouse session.
- **Remote / cross-warehouse result cache**: persists results across warehouse restarts when the underlying data hasn't changed.
- Plus the disk cache layer above.

### Common misuse

- **`df.cache()` with no subsequent reuse** — pure overhead; you paid the materialization cost for nothing.
- **Caching wide DataFrames** — eats executor memory that could be doing real work.
- **Using `cache()` for "I'm reading the same file twice"** — disk cache already handles this; redundant.

---

## File layout for query performance

### Target file size

Databricks autotunes based on table size:
- **256 MB** for tables under 2.56 TB
- **256 MB → 1 GB** linearly scaled between 2.56 TB and 10 TB
- **1 GB** above 10 TB

Override with table property `delta.targetFileSize` ([Databricks file size docs](https://docs.databricks.com/aws/en/delta/tune-file-size)).

### Optimized Writes and Auto Compaction

Two distinct Databricks-specific knobs (Module 3 covered them; quick recap here):

- `spark.databricks.delta.optimizeWrite.enabled` — pre-shuffles writes so each file is closer to target size, reducing the small-file output rate per write.
- `spark.databricks.delta.autoCompact.enabled` — runs a synchronous, opportunistic compaction after each write succeeds; combines small files within partitions. Output file size controlled by `spark.databricks.delta.autoCompact.maxFileSize`.

The legacy combined alias `delta.autoOptimize` is retired.

### Liquid Clustering — the new default for join keys

Liquid Clustering replaces both static partitioning and ZORDER for most tables. Declare cluster keys (`CLUSTER BY (member_id, claim_date)`); Databricks maintains the layout incrementally.

Key 2025 numbers: **7× faster writes** than partition+ZORDER on incrementally ingested tables, and **2.5× faster clustering** than ZORDER on a 1 TB warehouse benchmark ([Liquid Clustering GA blog](https://www.databricks.com/blog/announcing-general-availability-liquid-clustering)).

**For joins specifically:** when both tables share a cluster key, data is co-located by key range and Spark can skip shuffle for portions of the join.

Liquid Clustering is **incompatible with partitioning and ZORDER on the same table** — all-or-nothing. 2025 added **Automatic Liquid Clustering** (`CLUSTER BY AUTO`) — Databricks picks cluster keys based on observed query patterns.

### When partitioning still makes sense

Time-series append-mostly tables where you query date ranges and lifecycle data per partition (drop old partitions). Date partitioning is cheap because cardinality is bounded. **Never partition by user_id, member_id, account_id, or any high-cardinality column** — use Liquid Clustering instead.

### Predictive Optimization — auto OPTIMIZE/VACUUM/ANALYZE

For UC managed tables, PO automatically runs ANALYZE, OPTIMIZE, and VACUUM on serverless compute. **Default-on for accounts created after Nov 11, 2024.** 2025 added an optimized VACUUM path that uses the Delta log directly to identify removable files instead of doing directory listings ([PO at scale blog](https://www.databricks.com/blog/predictive-optimization-scale-year-innovation-and-whats-next)).

PO does **not** auto-tune cluster keys (that's Automatic Liquid Clustering's job) and does not change file sizes per partition.

### Data Skipping — column statistics

Delta collects min/max/null-count stats on the first `delta.dataSkippingNumIndexedCols` columns (default **32**). Each nested field counts as a separate column. Set to `-1` to collect on all (rarely correct — penalizes writes for wide tables).

DBR 13.3+ supports `delta.dataSkippingStatsColumns`, which lets you name the columns to collect stats on explicitly — strictly better than relying on column position. **Pick your top 10–20 most frequently filtered columns.**

```sql
ALTER TABLE silver.claim_line SET TBLPROPERTIES (
  'delta.dataSkippingStatsColumns' = 
    'service_date,member_id,payer_id,procedure_code,paid_amount,claim_id'
);
```

---

## Predicate / projection pushdown

Pushdown means filters and column selections are evaluated at the file-reader layer rather than after data is materialized into Spark.

For Delta on Databricks, **pushdown silently fails** in these cases:
- The filter wraps a Python or Scala UDF — the executor has no way to push UDF logic into the Parquet reader.
- The filter uses non-deterministic functions (`rand()`, row-wise `current_timestamp()`).
- Aggregation pushdown is available in Photon for some shapes but is more limited than scan/filter pushdown.

Photon explicitly implements filter pushdown, dictionary pruning, and row-group skipping at the Parquet level, but a UDF-containing filter forces fallback to JVM Spark for that operator.

---

## Photon-aware code

### What Photon does (2024–2026)

Photon is a vectorized C++ query engine compatible with Spark APIs. Operator coverage in 2024–2026 includes Scan, Filter, Project, Hash Aggregate, Hash Join, Shuffle, Nested-Loop Join, Null-Aware Anti Join, Union, Expand, ScalarSubquery, with date/timestamp coverage ~95% ([Photon docs](https://docs.databricks.com/aws/en/compute/photon), [Photon SIGMOD 2022 paper](https://people.eecs.berkeley.edu/~matei/papers/2022/sigmod_photon.pdf)).

The native Parquet writer (rolled out 2024+) accelerates DML — INSERT, UPDATE, DELETE, MERGE INTO, CTAS — for Delta, Iceberg, and plain Parquet tables. **Wide tables with thousands of columns benefit most.** Predictive I/O for read and write is Photon-exclusive.

### What Photon does NOT accelerate

- **Python UDFs** — execute in a Python process outside Photon's address space. The query falls back to JVM Spark for that operator.
- **Pandas (Arrow) UDFs** — better than plain Python UDFs because of vectorized batch transfer via Arrow, but still cause Photon fallback for the UDF operator.
- **RDD APIs and Dataset APIs** in Scala.
- **MLlib / scikit-learn UDFs** — Photon doesn't accelerate ML training or inference paths inside Spark.

**The discipline rule: replace Python UDFs with Spark SQL built-ins whenever possible.** A simple `lambda x: x.upper()` UDF runs **100× slower** than `F.upper()` after Photon kicks in.

### When Photon's 2× DBU premium pays back

Photon clusters cost roughly 2× the DBU rate of standard runtime. Pays back when:
- Workload is dominated by SQL/DataFrame operations on large data (>tens of GB scanned per query).
- Lots of joins, aggregations, window functions on columnar data.
- You're writing large Delta tables (native writer benefits MERGE/UPDATE/DELETE).
- Concurrent BI on DBSQL warehouses (Photon is always on for serverless and pro warehouses).

**Does NOT pay back when:** heavy Python UDF workloads, ML training, or RDD-API code.

---

## DataFrame API idioms (the kind that bite in code review)

### Don't `.collect()` or `.toPandas()` on large DataFrames

Both pull all data to the driver. `.toPandas()` is especially seductive in notebooks. With Arrow-based PyArrow integration enabled (`spark.sql.execution.arrow.pyspark.enabled=true`) it's faster but **still bounded by driver memory.**

### `display()` triggers a query and pulls 1000 rows

`display(df)` in a notebook is an action — runs the query plan and materializes 1000 rows. Calling `display()` after every transformation in a notebook is a hidden cost surprise: each call re-executes the plan unless you've cached upstream.

### Lazy vs eager — `cache()` does not materialize

`df.cache()` is a lazy hint. Force materialization with `df.cache().count()` or follow it with the action you actually want to cache for.

### `repartition()` vs `coalesce()`

- **`repartition(n)`** — full shuffle; can increase or decrease partitions; produces evenly sized partitions.
- **`coalesce(n)`** — no shuffle; can only **decrease** partitions; produces unevenly sized partitions because it merges adjacent ones without rebalancing.

Use `coalesce()` to reduce partitions before write to avoid tiny output files. Use `repartition()` when input is skewed and you need rebalancing, or when you need to repartition by a specific key prior to a join (`df.repartition(N, "join_key")`).

### `withColumn` chained 50 times = analyzer cost

Each `withColumn` creates a new logical plan node. Catalyst optimization is roughly O(plan depth × passes). 50+ chained `withColumn` calls (a real pattern in feature engineering pipelines) can cause analysis-phase delays of seconds. Prefer:

```python
# Better: one select with multiple expressions
df = df.select(
    "*",
    (F.col("a") + F.col("b")).alias("c"),
    F.when(F.col("x") > 0, "pos").otherwise("neg").alias("sign"),
    # ...
)
```

### Don't loop over DataFrames in Python

`for row in df.collect():` defeats the entire point of Spark. Use `selectExpr`, built-in functions, or as a last resort a Pandas UDF.

---

## Spark configs that actually matter on Databricks

| Config | Default | Notes |
|---|---|---|
| `spark.sql.adaptive.enabled` | `true` | AQE on by default in DBR 7.3+ |
| `spark.sql.adaptive.coalescePartitions.enabled` | `true` | Post-shuffle coalescing |
| `spark.sql.adaptive.skewJoin.enabled` | `true` | AQE skew handling |
| `spark.sql.adaptive.skewJoin.skewedPartitionFactor` | `5` | Skew detection multiplier |
| `spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes` | 256 MB | Absolute floor for skew detection |
| `spark.sql.adaptive.advisoryPartitionSizeInBytes` | 64 MB | Target post-coalesce size |
| `spark.sql.shuffle.partitions` | 200 | Initial; AQE coalesces down |
| `spark.sql.autoBroadcastJoinThreshold` | 10 MB | OSS broadcast threshold |
| `spark.databricks.adaptive.autoBroadcastJoinThreshold` | ~30 MB | Databricks AQE-time threshold |
| `spark.databricks.adaptive.autoOptimizeShuffle.enabled` | `false` | Auto-tune initial shuffle partitions |
| `spark.databricks.delta.optimizeWrite.enabled` | varies | Pre-shuffle for target file size |
| `spark.databricks.delta.autoCompact.enabled` | varies | Synchronous post-write compaction |
| `spark.databricks.io.cache.enabled` | `true` on SSD types | Disk cache |
| `spark.databricks.optimizer.dynamicFilePruning` | `true` | DPP extended to non-partition columns |
| `spark.databricks.photon.enabled` | depends on cluster | Photon engine |
| `delta.dataSkippingNumIndexedCols` | 32 | Stats collection scope |
| `delta.dataSkippingStatsColumns` | unset | DBR 13.3+; named-column stats |

---

## Window functions

Window functions (`row_number`, `rank`, `lag`, running aggregates) shuffle by `partitionBy` columns, then sort by `orderBy`. The skew rules apply: partitioning a window over `customer_id` when one customer has 100M events is a skew incident.

- **Range frames vs row frames** — `rangeBetween` operates on the order column's value range; `rowsBetween` operates on row offsets. Range frames over timestamp columns can be expensive when groups are huge — Spark must scan the frame.
- **Sort within partitions** — use `sortWithinPartitions` rather than full `orderBy` when you don't need a global sort; skips one shuffle.
- AQE skew handling does **not** rebalance window function shuffles the same way as joins — salting is the answer for skewed partitionBy keys.

---

## Streaming performance

### State store backend — RocksDB is the default in DBR 17.3+

Pre-17.3 the JVM HDFS state store was default; large state (>1M keys) caused GC pressure. **RocksDB stores state off-heap in an embedded LSM-backed store, persisted via stream checkpointing** ([RocksDB state store docs](https://docs.databricks.com/aws/en/structured-streaming/rocksdb-state-store)). Switch with `spark.sql.streaming.stateStore.providerClass=com.databricks.sql.streaming.state.RocksDBStateStoreProvider`. **Use it for any stateful streaming workload large enough to matter.**

### Watermarks and state TTL

Watermark = `max(event_time_seen) - allowed_late_threshold`. State older than the watermark plus the join/window bound is dropped. **Smaller watermark threshold = smaller state and lower latency, but more dropped late records.** This is a business-data tradeoff, not a tuning knob.

### Output modes

- **Append** — only new rows; the only mode supported for stream-stream joins.
- **Update** — changed rows; cheaper than complete for aggregations.
- **Complete** — full result set per batch; only for small aggregations.

### Trigger modes

- **`Trigger.AvailableNow`** is the recommended mode for incremental batch processing — processes everything currently available, then stops, in multiple batches (replaces `Trigger.Once` which forced a single batch and is deprecated in DBR 11.3+ LTS).
- **`ProcessingTime("30 seconds")`** for steady micro-batch streaming.
- **`Continuous`** is largely abandoned for production; AvailableNow + frequent scheduling has replaced it.
- On serverless compute, **only `AvailableNow` and `Once` are supported.**

### Micro-batch sizing

Use `maxFilesPerTrigger` (file sources) or `maxOffsetsPerTrigger` (Kafka) to bound batch size. Without bounds, a stream restart after downtime processes a giant catch-up batch that can OOM the executors.

---

## DBSQL warehouse tuning

### Warehouse types

Three flavors, in increasing capability:
- **Classic** — Photon supported, but no Predictive I/O, no Intelligent Workload Management.
- **Pro** — Photon + Predictive I/O.
- **Serverless** — Photon + Predictive I/O + Intelligent Workload Management; instant startup; **recommended default** ([Warehouse types docs](https://docs.databricks.com/aws/en/compute/sql-warehouse/warehouse-types)).

### Sizing and concurrency

Warehouse "T-shirt sizes" (2X-Small through 4X-Large) determine cluster size; **concurrency scales by adding clusters horizontally.** Intelligent Workload Management (serverless only) auto-scales clusters up to a configured max based on queued queries.

### Predictive I/O for SELECT/UPDATE/DELETE/MERGE

Photon-exclusive feature that minimizes data read and file rewrites. For SELECT it drives selective-scan acceleration; for DELETE/UPDATE/MERGE it minimizes the number of files rewritten via deletion vectors.

### Materialized Views and Streaming Tables

Both run on serverless Lakeflow Spark Declarative Pipelines, billed independently of the warehouse you submit from. **Materialized view refresh on a 200B-row Databricks-internal benchmark was 98% cheaper and 85% faster** than full table rebuild, ~7× better data freshness at 1/50th cost vs CREATE TABLE AS ([MV/ST GA blog](https://www.databricks.com/blog/announcing-the-general-availability-of-materialized-views-and-streaming-tables-databricks-sql)). Default refresh strategy uses a cost model to pick incremental vs full.

### Statistics — when manual ANALYZE matters

With Predictive Optimization on, ANALYZE runs automatically — collected once during Photon writes, then re-collected as data degrades from UPDATE/DELETE ([PO for Statistics blog](https://www.databricks.com/blog/introducing-predictive-optimization-statistics)). Manual `ANALYZE TABLE … COMPUTE STATISTICS FOR COLUMNS …` is still relevant for non-UC-managed tables, freshly migrated tables before the first write, and any case where the CBO is making bad join-order decisions. Reported impact: **~22% average speedup** across observed workloads.

---

## Production patterns — putting it together

### Pattern: optimize a slow MERGE on a 100M-row Silver

Symptom: nightly MERGE takes 4 hours.

Diagnosis (from Module 5's loop):
1. **Spark UI SQL plan** — what's the join strategy? `BroadcastHashJoin`? `SortMergeJoin`?
2. **Stages tab** — task duration histogram. Long tail = skew.
3. **Storage tab** — disk cache hit rate.
4. **Executors tab** — GC time elevated?

Common causes and fixes:
- **MERGE-key cardinality too low** — fix the join condition to include a high-cardinality key.
- **No Liquid Clustering on merge key** — `ALTER TABLE … CLUSTER BY (member_id, service_date)`.
- **DV not enabled** — `delta.enableDeletionVectors = true` makes selective MERGE 10–100× faster.
- **Skew on the source side** — AQE skew, or salt manually.
- **Photon not enabled but workload is SQL-shaped** — turn Photon on for this job.
- **File size too small** — schedule weekly OPTIMIZE; enable PO.

### Pattern: optimize a slow analytical query

Symptom: a Power BI dashboard query takes 90 seconds.

Diagnosis:
1. **DBSQL Query Profile** — show the plan, file pruning, shuffle sizes.
2. **Is the warehouse on Serverless?** Predictive I/O only on Pro/Serverless.
3. **Photon active?** Should be by default on Pro/Serverless.
4. **Stats fresh?** ANALYZE TABLE if manual.
5. **File layout aligned with the query?** Liquid Clustering on filter columns.

Common fixes:
- Move warehouse to Serverless (Predictive I/O, IWM).
- Materialize the query as a Materialized View if it's a hot dashboard.
- Liquid Clustering on the dashboard filter columns.
- Pre-aggregate to a Streaming Table if real-time isn't required.

### Pattern: a stream-stream join with growing state

Symptom: streaming pipeline gets slower week over week; cluster RAM under pressure.

Diagnosis:
1. **Executors tab** — GC time growing; RAM near limit.
2. Are watermarks set on **both** sides of the join?
3. Is the time-bound join condition tight enough?
4. Is RocksDB the state store?

Fixes:
- Set / shorten watermarks.
- Tighten the time-bound condition.
- Switch to RocksDB state store backend.
- Monitor with `streaming.lastProgress()` for `inputRowsPerSecond` vs `processedRowsPerSecond`.

---

## Sanity check

1. A peer says "increase `spark.sql.shuffle.partitions` to 4000 to make this job faster." When is that right, and when is it superstition?
2. Walk through the AQE skew detection thresholds and explain why they sometimes fail to fire on real skew.
3. Why does forcing a broadcast with `broadcast(df)` sometimes still not produce a BHJ in the plan?
4. Name the four caching layers on Databricks and one valid use case for each.
5. A peer wants to partition `claim_line` by `member_id` for query speed. What's wrong, and what would you do instead?
6. The 2× DBU premium for Photon: when does it pay back, and when is it actively wasteful?
7. A stream-stream join's state is growing unbounded. What three things do you check?

---

## Further reading

- [Spark SQL Performance Tuning (4.x) — Apache Spark](https://spark.apache.org/docs/latest/sql-performance-tuning.html)
- [Adaptive Query Execution — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/optimizations/aqe)
- [Photon — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/compute/photon)
- [Photon SIGMOD 2022 paper](https://people.eecs.berkeley.edu/~matei/papers/2022/sigmod_photon.pdf)
- [Liquid Clustering — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/delta/clustering)
- [Liquid Clustering GA blog](https://www.databricks.com/blog/announcing-general-availability-liquid-clustering)
- [Disk cache — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/optimizations/disk-cache)
- [Data skipping — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/delta/data-skipping)
- [Predictive Optimization — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/optimizations/predictive-optimization)
- [SQL warehouse types — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/compute/sql-warehouse/warehouse-types)
- [Confessions of a Data Guy — Tuning shuffle partitions](https://www.confessionsofadataguy.com/how-to-tune-spark-shuffle-partitions/)
- [Canadian Data Guy — Skewed joins deep dive](https://www.canadiandataguy.com/p/a-deep-dive-into-skewed-joins-groupby)
- [B EYE — Photon optimization guide](https://b-eye.com/blog/databricks-photon-performance-optimization-guide/)
- [TantusData — Photon internals](https://tantusdata.com/insights/databricks-photon/)
- [Databricks comprehensive Optimize Workloads guide](https://www.databricks.com/discover/pages/optimize-data-workloads-guide)
