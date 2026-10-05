# FACTS — Databricks Certified Associate Developer for Apache Spark

> Atomic, citable claims. Use this as the single source of truth when writing modules or answering quiz questions. Anything not in here that "feels true" should be verified before relying on it.
>
> **Last verified:** 2026-05-23 (against the Oct 30, 2025 official exam guide PDF + Apache Spark 3.5.0 docs).

---

## 1. Exam logistics

| Fact | Value | Source |
|---|---|---|
| Official name | Databricks Certified Associate Developer for Apache Spark | Exam guide Oct 2025 |
| Question count | 45 scored multiple-choice + a few unscored statistical items (time-adjusted) | Exam guide Oct 2025 |
| Duration | 90 minutes | Exam guide Oct 2025 |
| Passing score | Not publicly disclosed by Databricks; community-reported **~70%** `[ASSUMED]` | Community |
| Cost | $200 USD (+ local taxes) | Databricks cert page |
| Language (UI) | English | Exam guide |
| Language (code) | **Python only** — Scala removed | Exam guide: "All learning code/code snippets within this exam will be in Python" |
| Delivery | Online proctored OR test-center proctored | Databricks cert page |
| Prerequisites | None; 6+ months hands-on recommended | Databricks cert page |
| Validity | **2 years** | Databricks cert page |
| Recertification | Retake currently-live exam | Databricks cert page |
| Test aides | None — no API docs, no scratch paper, no calculator | Exam guide |
| Registration platform | Webassessor (webassessor.com/databricks) | Databricks cert page |
| Result delivery | Immediate pass/fail + per-section % breakdown | Community + standard Databricks practice |

**Relaunch date:** April 2025. **Current guide version:** October 30, 2025.

---

## 2. Spark version and scope

| Fact | Value |
|---|---|
| Spark version tested | **Apache Spark 3.5.x** (Spark Connect features from 3.4) |
| Spark 4.0 tested? | **No** — Spark 4.0 ANSI mode default, Variant type, collations, Arbitrary Stateful Processing V2 are NOT in scope |
| Spark 3.5.0 release date | September 13, 2023 |
| Spark 3.5.1 release date | February 23, 2024 |
| Spark 3.5.2 release date | August 10, 2024 |
| Spark 3.5.3 release date | September 24, 2024 |
| Databricks-platform features tested? | **No** — Unity Catalog, Delta Lake operations (time travel/OPTIMIZE/ZORDER), DBFS, Photon, Workflows are not tested |
| Delta Lake tested? | Only as a *readable file format* via `delta.\`path\`` — no Delta-specific operations |

**Spark 3.5 headline features** (in scope):
- Spark Connect: GA in 3.4, expanded coverage in 3.5
- English SDK for Spark (out of scope for cert)
- Distributed training with `DeepSpeedTorchDistributor` (out of scope for cert)
- New PySpark testing utilities (`assertDataFrameEqual`, `assertSchemaEqual`) — could appear
- Arrow-optimized Python UDFs as default (relevant for Pandas UDF section)

---

## 3. Exam domains and weights

| # | Domain | Weight | ~Qs (of 45) |
|---|--------|--------|-------------|
| 1 | Apache Spark Architecture and Components | **20%** | ~9 |
| 2 | Using Spark SQL | **20%** | ~9 |
| 3 | Developing Apache Spark DataFrame/Dataset API Applications | **30%** ← largest | ~14 |
| 4 | Troubleshooting and Tuning Apache Spark DataFrame API Applications | **10%** | ~5 |
| 5 | Structured Streaming | **10%** | ~5 |
| 6 | Using Spark Connect to Deploy Applications | **5%** | ~2 |
| 7 | Using Pandas API on Spark | **5%** | ~2 |

Both the official exam guide AND the public certification page list these exact weights.

---

## 4. Architecture facts

### Cluster topology

| Component | What it does | Process model |
|---|---|---|
| **Driver** | Runs `SparkSession`, holds DAG, schedules tasks, collects results | Single JVM process |
| **Executor** | Runs tasks in parallel threads (one per CPU core); caches partitions in memory | JVM process per executor |
| **Cluster manager** | Allocates resources to driver and executors | One of: Standalone, YARN, Kubernetes, Mesos (deprecated, removed in 3.2) |

### Deployment modes

| Mode | Driver location | Executor location | Use case |
|---|---|---|---|
| **Client mode** | On the submitting machine (laptop, edge node) | Cluster | Interactive dev, notebooks |
| **Cluster mode** | On a worker node in the cluster | Cluster | Production batch jobs |
| **Local mode** | Single JVM on local machine | **All executors run on a single worker node** (same JVM) | Dev, testing, unit tests |

The "local mode = single worker node" fact is on the exam (official sample Q7).

### SparkContext vs SparkSession

- `SparkContext` — the original (Spark 1.x) entry point; still accessible via `spark.sparkContext` in 3.5.
- `SparkSession` — the modern (Spark 2.0+) unified entry point. Wraps `SparkContext`, `SQLContext`, `HiveContext`.
- Spark Connect clients have **no `SparkContext` access** — only `SparkSession`.

---

## 5. Execution hierarchy

```
Application
  └─ Job             (one per action: count, collect, show, write...)
       └─ Stage      (one per shuffle boundary)
            └─ Task  (one per partition)
```

- **Action** → triggers a Job.
- **Wide transformation** → creates a new Stage (shuffle boundary).
- **Task** processes exactly one partition. Number of tasks in a stage = number of partitions.
- One executor core runs one task at a time. Total parallelism = sum of cores across executors.

---

## 6. Narrow vs wide transformations (HIGH-VALUE — exam trap territory)

| Transformation | Narrow or Wide | Notes |
|---|---|---|
| `select` | **Narrow** | Column projection |
| `filter` / `where` | **Narrow** | Predicate eval |
| `withColumn` | **Narrow** | Single-column derivation |
| `withColumnRenamed` | **Narrow** | Schema-only change |
| `drop` | **Narrow** | Column removal |
| `map`, `flatMap`, `mapPartitions` | **Narrow** | RDD-level (not exam-heavy but valid) |
| `sample` | **Narrow** | Per-partition sampling |
| `union` / `unionAll` | **⚠️ Narrow** | Concatenates partitions; **no shuffle** — common exam trap |
| `unionByName` | **Narrow** | Same as union, by column name |
| `coalesce(n)` (decreasing) | **Narrow** | Combines partitions on the same executor, no shuffle |
| **`groupBy` + agg** | **Wide** | Shuffles by group key |
| **`distinct`** | **Wide** | Implemented as `groupBy(*cols).agg()` |
| **`dropDuplicates`** | **Wide** | Same as distinct over subset |
| **`orderBy` / `sort`** | **Wide** | Range-partitions for global ordering |
| **`repartition(n)`** | **Wide** | Always a full shuffle, even if `n` matches current count |
| **`repartition(col)`** | **Wide** | Hash-partitions by column |
| **`join` (sort-merge, shuffle hash)** | **Wide** | Both sides shuffled by key |
| **`join` (broadcast)** | **Narrow on the large side** | Small side is broadcast, large side not shuffled |
| **Window functions** | **Wide** | Shuffle by `partitionBy` keys (except unbounded global window) |

⚠️ **Exam traps in this list:**
- `union` is narrow (people commonly mark it as wide because "joining tables = shuffle").
- `coalesce` (the *DataFrame method* for partition reduction) is narrow. The *SQL function* `coalesce` (returning first non-null) is unrelated.
- A broadcast join is wide *overall* (the small side is broadcast across the cluster) but narrow on the large side (no shuffle of the large DataFrame).

---

## 7. Lazy evaluation and DAG

- **Transformations are lazy**: building `df.filter(...).select(...).join(...)` does **no** work — it builds a logical plan.
- **Actions trigger execution**: `count`, `collect`, `take`, `show`, `first`, `head`, `foreach`, `write...`, `toPandas`.
- **Logical plan → optimized logical plan → physical plan → executed DAG**: the Catalyst optimizer + the planner do this.
- **Lineage** (the chain of transformations on RDDs/DataFrames) enables **fault tolerance**: if a partition is lost, Spark recomputes from the source via the lineage.

---

## 8. Shuffle mechanics

- A shuffle has two halves:
  - **Shuffle write**: map-side tasks write partitioned output to local disk (shuffle files).
  - **Shuffle read**: reduce-side tasks pull their assigned shuffle files over the network.
- **Spill to disk**: when an in-memory operation (sort, aggregate, hash table for join) exceeds the available memory, Spark spills sorted/partial state to local disk. Spills are visible in the Spark UI Stages tab.
- **Speculative execution** (`spark.speculation=false` by default): when enabled, Spark relaunches slow-running tasks on other executors and uses whichever finishes first.
- **Dynamic allocation** (`spark.dynamicAllocation.enabled`): executors are added/removed based on backlog. Off by default in OSS Spark; commonly enabled on Databricks.

---

## 9. Adaptive Query Execution (AQE)

| Config Key | Default | What it does |
|---|---|---|
| `spark.sql.adaptive.enabled` | `true` (since 3.2) | Master AQE switch |
| `spark.sql.adaptive.coalescePartitions.enabled` | `true` | Combine small post-shuffle partitions |
| `spark.sql.adaptive.coalescePartitions.initialPartitionNum` | `spark.sql.shuffle.partitions` | Initial number before coalesce |
| `spark.sql.adaptive.advisoryPartitionSizeInBytes` | **64 MB** | Target partition size after coalesce |
| `spark.sql.adaptive.skewJoin.enabled` | `true` | Auto-split skewed join partitions |
| `spark.sql.adaptive.skewJoin.skewedPartitionFactor` | `5` | Partition is "skewed" if its size > factor × median |
| `spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes` | **256 MB** | AND its size > this threshold |
| `spark.sql.adaptive.autoBroadcastJoinThreshold` | **(disabled by default; falls back to non-AQE threshold)** | AQE-time runtime broadcast threshold |
| `spark.sql.autoBroadcastJoinThreshold` | **10 MB** | Planner-time broadcast threshold |
| `spark.sql.adaptive.localShuffleReader.enabled` | `true` | Use local shuffle reader when AQE demotes SMJ to BHJ |

⚠️ **The AQE config-key trap.** Candidates confuse:
- `spark.sql.adaptive.enabled` — correct.
- `spark.adaptive.enabled` — **does not exist**, exam distractor.
- `spark.sql.adaptive.autoBroadcastJoinThreshold` (AQE runtime) vs `spark.sql.autoBroadcastJoinThreshold` (planner). Both exist; they mean different things.

AQE three pillars:
1. **Coalesce shuffle partitions** — combine small post-shuffle partitions to target ~64 MB each.
2. **Switch join strategies** — promote a planned sort-merge join to a broadcast hash join if runtime size proves small enough.
3. **Skew join handling** — split skewed partitions into smaller subpartitions and replicate the matching partition on the other side.

---

## 10. Join strategies

| Strategy | When it fires | Cost |
|---|---|---|
| **Broadcast Hash Join (BHJ)** | One side ≤ `spark.sql.autoBroadcastJoinThreshold` (10 MB default), OR a `broadcast()` hint | No shuffle of the large side; small side replicated to all executors |
| **Sort-Merge Join (SMJ)** | Default for two large sides | Both sides shuffled by key, sorted within partitions, merged |
| **Shuffle Hash Join (SHJ)** | One side meaningfully smaller per partition than the other, both too large to broadcast (requires `spark.sql.join.preferSortMergeJoin=false`) | Both shuffled; hash table built on smaller side |
| **Broadcast Nested Loop Join (BNLJ)** | Non-equi join (e.g., `BETWEEN`) with broadcast hint or small-table threshold | O(N×M); almost always a bug if slow |
| **Cartesian Product** | Cross join, no condition | Massive; rarely intentional |

### Broadcast join + outer-join restrictions ⚠️

| Outer-join type | Which side can be broadcast |
|---|---|
| `left outer` (left side preserved) | Only the **right** side can be broadcast |
| `right outer` (right side preserved) | Only the **left** side can be broadcast |
| `full outer` | **Neither** side can be broadcast |
| `inner` | Either side |
| `left semi` | Only the **right** side |
| `left anti` | Only the **right** side |

Rule: the **non-preserved** side can be broadcast.

---

## 11. Cache and persist

| Storage Level | Memory | Disk | Serialized | Replicated |
|---|---|---|---|---|
| `MEMORY_ONLY` | ✓ | ✗ | ✗ | ✗ |
| **`MEMORY_AND_DISK`** (default for DataFrame `.cache()`) | ✓ | ✓ | ✗ | ✗ |
| `MEMORY_ONLY_SER` | ✓ | ✗ | ✓ | ✗ |
| `MEMORY_AND_DISK_SER` | ✓ | ✓ | ✓ | ✗ |
| `DISK_ONLY` | ✗ | ✓ | (always serialized) | ✗ |
| `MEMORY_ONLY_2` etc. | — | — | — | ✓ (replicated to 2 nodes) |
| `OFF_HEAP` | off-heap | ✗ | ✓ | ✗ |

⚠️ **The cache default trap:**
- **RDD `.cache()`** = `persist(MEMORY_ONLY)`.
- **DataFrame/Dataset `.cache()`** = `persist(MEMORY_AND_DISK)`.
- This is **NOT** symmetric. Exam can test this.

`unpersist(blocking=False)` removes from cache. `blocking=True` waits for completion.

---

## 12. Partitioning

| Fact | Value |
|---|---|
| `spark.sql.shuffle.partitions` default | **200** |
| `spark.default.parallelism` | Depends on cluster manager; usually total executor cores |
| `df.repartition(n)` | **Full shuffle**, even if `n` equals current count; round-robin partitions |
| `df.repartition(col)` | **Full shuffle**, hash-partitions by column |
| `df.repartition(n, col)` | **Full shuffle**, hash-partitions by column into `n` partitions |
| `df.coalesce(n)` | **No shuffle**, can ONLY decrease partitions, NOT balanced |
| `df.sortWithinPartitions(col)` | **Narrow**, sorts each partition independently (does NOT trigger a shuffle) |
| `df.orderBy(col)` / `df.sort(col)` | **Wide**, global ordering via range partitioning |

⚠️ **`coalesce` traps:**
- `df.coalesce(n)` is narrow and cannot *increase* partition count.
- The SQL/DataFrame function `F.coalesce(col1, col2)` returns the first non-null — totally unrelated to the partition method.

---

## 13. Spark SQL specifics

### Temp views

| Type | Scope | API |
|---|---|---|
| Temporary view | Current SparkSession only | `df.createOrReplaceTempView("name")` |
| Global temporary view | All SparkSessions sharing the cluster | `df.createOrReplaceGlobalTempView("name")`; access via `global_temp.name` |
| Persistent table | Catalog (Hive metastore / UC) | `df.write.saveAsTable("name")` |

- `createTempView("name")` **fails** if the view already exists.
- `createOrReplaceTempView("name")` always succeeds.
- Global temp views live in the reserved database `global_temp`: `spark.sql("SELECT * FROM global_temp.myview")`.

### Querying files directly via SQL

```sql
SELECT * FROM parquet.`/path/to/file.parquet`
SELECT * FROM json.`/path/to/file.json`
SELECT * FROM csv.`/path/to/file.csv`
SELECT * FROM delta.`/path/to/delta_table`
SELECT * FROM orc.`/path/to/file.orc`
SELECT * FROM text.`/path/to/file.txt`
```

The backtick-wrapped path is the literal file system path. Exam-testable.

### Save modes

| Mode | Behavior |
|---|---|
| `errorIfExists` (default) | Fails if target exists |
| `overwrite` | Replaces target |
| `append` | Adds to target |
| `ignore` | Silently does nothing if target exists |

### Partition vs bucket

| | partitionBy | bucketBy |
|---|---|---|
| **API** | `df.write.partitionBy("col").parquet(...)` | `df.write.bucketBy(N, "col").sortBy("col").saveAsTable("name")` |
| **Storage** | Subdirectories per partition value | N hash-bucketed files |
| **Use case** | Low-cardinality predicates (`region`, `event_date`) | High-cardinality join keys |
| **Requires** | Path-based writes OK | **Must use `saveAsTable`** — bucketing is Hive-table metadata |

---

## 14. Date/time functions (Spark SQL)

| Function | Returns |
|---|---|
| `current_date()` | `DateType` (today, UTC) |
| `current_timestamp()` | `TimestampType` (now) |
| `to_date(col, fmt)` | Parses string → DateType |
| `to_timestamp(col, fmt)` | Parses string → TimestampType |
| `date_add(date, days)` | Adds days |
| `date_sub(date, days)` | Subtracts days |
| `datediff(end, start)` | Days between |
| `months_between(end, start)` | Months between (float) |
| `unix_timestamp(col, fmt)` | Epoch seconds |
| `from_unixtime(epoch)` | TimestampType string |
| `year(date)`, `month(date)`, `dayofweek(date)`, `dayofmonth(date)`, `dayofyear(date)` | Extracted components |
| `date_format(date, fmt)` | Formatted string |
| `trunc(date, "MONTH")` | Truncates to unit |
| `date_trunc("hour", ts)` | Truncates timestamp to unit |

---

## 15. Window functions

```python
from pyspark.sql import Window
import pyspark.sql.functions as F

w = Window.partitionBy("dept").orderBy(F.col("salary").desc())
df.withColumn("rk", F.row_number().over(w))
```

| Function | Returns |
|---|---|
| `row_number()` | Unique 1..N within window |
| `rank()` | 1, 2, 2, 4 (gaps after ties) |
| `dense_rank()` | 1, 2, 2, 3 (no gaps) |
| `percent_rank()` | (rank - 1) / (rows - 1) |
| `cume_dist()` | Cumulative distribution (0 to 1) |
| `ntile(n)` | Bucket number 1..n |
| `lag(col, offset, default)` | Value from `offset` rows earlier |
| `lead(col, offset, default)` | Value from `offset` rows later |
| `first(col)` / `last(col)` | First/last in window |

### Frame specifications

- `rowsBetween(start, end)` — physical row offsets.
- `rangeBetween(start, end)` — logical value-based range (requires ordering).
- `Window.unboundedPreceding`, `Window.currentRow`, `Window.unboundedFollowing`.

Default frame (when only `orderBy` set, no explicit frame):
- For ranking functions (`row_number`, `rank`): full partition.
- For aggregate functions (`sum`, `avg` over a window): `rangeBetween(unboundedPreceding, currentRow)` — running totals.

---

## 16. Null handling

| API | Behavior |
|---|---|
| `df.na.drop()` or `df.dropna()` | Drop any row with ANY null (default `how="any"`) |
| `df.na.drop("all")` or `df.dropna("all")` | Drop rows where ALL columns are null |
| `df.na.drop(thresh=N)` | Drop rows with fewer than N non-null values |
| `df.na.drop(subset=["col1","col2"])` | Drop rows with nulls in those specific columns |
| `df.na.fill(value)` | Replace nulls with value (typed) |
| `df.na.fill({"col1": 0, "col2": "x"})` | Per-column fill |
| `df.na.replace([old], [new])` | Generic replace |
| `F.coalesce(c1, c2, c3)` | First non-null **value** (not partition method!) |
| `F.isnull(col)`, `F.isnan(col)` | Predicates |

⚠️ `na.drop("all")` is a recurring exam trap (official sample Q6).

---

## 17. Approximate functions

- `F.approx_count_distinct(col, rsd=0.05)` — HyperLogLog++, ~5% relative error by default. **The speed comes from the algorithm avoiding a global distinct shuffle**, not from compression or null-handling.
- `F.approxQuantile("col", [0.5, 0.95], relativeError=0.01)` — Greenwald-Khanna.

---

## 18. UDFs

- **Python UDF** (`@udf` or `udf(func, returnType)`): row-by-row, serializes to Python via Py4J → slow; Catalyst can't optimize across it.
- **Pandas UDF** (`@pandas_udf`): Arrow-based, vectorized; receives `pd.Series` or `pd.DataFrame`. Four types:
  1. **Scalar** (`pd.Series → pd.Series`)
  2. **Scalar Iterator** (`Iterator[pd.Series] → Iterator[pd.Series]`) — for expensive init (model loading).
  3. **Grouped Map** (`applyInPandas`, deprecated alias: `pandas_udf(GROUPED_MAP)`): `pd.DataFrame → pd.DataFrame`, applied per group.
  4. **Grouped Aggregate** (`pd.Series → scalar`): used in `groupBy().agg(udf(col))`.
- **`mapInPandas`**: streams `pd.DataFrame` chunks per partition (no group key).

⚠️ Pandas UDFs are PySpark constructs, NOT the same as `pyspark.pandas`. Don't confuse them on the exam.

---

## 19. Broadcast variables vs broadcast joins

- **Broadcast variable** (`sc.broadcast(value)`): read-only Python object shipped to every executor, accessed via `bv.value`. Use for lookup dicts. **Not available in Spark Connect clients.**
- **`F.broadcast(df)`**: join hint, marks small DF for broadcast hash join. **Different mechanism; same name "broadcast".**
- **Accumulator** (`sc.accumulator(0)`): write-only counter aggregated across executors. NOT fault-tolerant (may double-count on task retry) → use for metrics, not business logic. **Not available in Spark Connect clients.**

---

## 20. Structured Streaming

### Programming model

Treat a stream as an unbounded table; queries produce a result table that updates incrementally with each micro-batch.

### Triggers

| Trigger | Behavior |
|---|---|
| Default (no trigger specified) | Process as fast as possible; new micro-batch fires when previous completes |
| `trigger(processingTime="10 seconds")` | Fire micro-batch every 10s (skip if previous still running) |
| `trigger(availableNow=True)` | Process all available data in multiple batches, then stop |
| `trigger(once=True)` | **Deprecated in 3.5**; use `availableNow` |
| `trigger(continuous="1 second")` | Continuous processing (experimental, limited operations) |

### Output modes

| Mode | When valid |
|---|---|
| **`append`** | Only new rows added. Required for queries without aggregations OR with watermarked aggregations |
| **`update`** | Only rows updated this micro-batch. Required for non-aggregated streaming queries that produce updates |
| **`complete`** | Entire result table. **Only valid for aggregations** |

### Watermarks

```python
stream.withWatermark("event_time", "10 minutes") \
      .groupBy(F.window("event_time", "5 minutes"), "key") \
      .count()
```

- Data with `event_time < max_seen_event_time - 10 minutes` is dropped (state can be cleaned up).
- Required for `append` mode with aggregations.
- Required to bound state in stream-stream joins.
- Required to bound state in `dropDuplicates` (otherwise state grows unbounded).

### Streaming deduplication

```python
# Without watermark: state grows unbounded
stream.dropDuplicates(["event_id"])

# With watermark: bounded state
stream.withWatermark("ts", "10 minutes").dropDuplicates(["event_id", "ts"])
```

### Checkpointing

- `checkpointLocation` is **required** for fault-tolerant queries.
- Stores: offsets per source, query metadata, state store snapshots.
- Sinks store committed-batches log to ensure exactly-once.

### Exactly-once requirements

(1) Replayable source (Kafka, file source with offsets, Delta), (2) Idempotent sink (Delta, Kafka with transactions, foreachBatch with idempotent writes), (3) Checkpoint location.

### Streaming output sinks

- `console`, `memory` — dev only.
- `file` (Parquet, JSON, CSV, ORC) — append-only.
- `kafka` — exactly-once via Kafka transactions.
- `foreachBatch(fn)` — custom logic per micro-batch; the only way to write to arbitrary sinks while preserving fault tolerance.
- `foreach(writer)` — row-level.

### Stream-stream joins

- Inner: both sides need watermarks + time-bound condition (state bounded).
- Outer: same + watermark must be on the side that's allowed to emit nulls.
- **Output mode restricted to `append`** for streaming aggregations + joins.

---

## 21. Spark Connect

### Architecture

```
[Thin Python client (1.5 MB)] ──gRPC──▶ [Spark Connect server (runs the driver)] ──▶ [Spark cluster]
```

- GA in Spark 3.4 (Python). Scala client GA in 3.5. Go client in development.
- Client sends a logical plan (Protobuf-encoded) to the server; server compiles and executes.

### Usage

```python
from pyspark.sql import SparkSession
spark = SparkSession.builder.remote("sc://hostname:15002").getOrCreate()
```

URI scheme: `sc://`. Default port: 15002.

### Benefits

- Lightweight client (~1.5 MB vs ~355 MB full PySpark).
- Decoupled lifecycle: client crashes don't kill the driver.
- Multi-language: Python, Scala, Go.
- IDE-friendly (PyCharm, VS Code).
- Mismatched client/server versions tolerated within a supported range.

### Restrictions (not available in Spark Connect clients)

- **No RDD API** — `.rdd` is not callable from a Connect client.
- **No `SparkContext`** — `spark.sparkContext` is None in Connect.
- **No client-side broadcast variables** (`sc.broadcast(...)` unavailable).
- **No client-side accumulators**.
- **No JVM access** (`spark._jvm`) — no calling into JVM APIs from Python.
- **Some legacy DataFrame internals** unavailable (e.g., `df.rdd.getNumPartitions()` — use `df.rdd.getNumPartitions()` substitute via `spark._jsparkSession` — not available; use the DataFrame `.repartition(n)` and trust the count).

---

## 22. Pandas API on Spark (pyspark.pandas)

- Formerly **Koalas** (pre-Spark 3.2), now integrated as `pyspark.pandas` and imported as `ps` by convention.
- Drop-in pandas-compatible API that runs on Spark under the hood.

### Key API

```python
import pyspark.pandas as ps

psdf = ps.read_csv("path/to/file.csv")
psdf['new_col'] = psdf['a'] * 2          # works pandas-style
result = psdf.groupby('dept').mean()
pdf = psdf.to_pandas()                   # materialize to pandas — collects to driver
sdf = psdf.to_spark()                    # convert to PySpark DataFrame
psdf2 = ps.from_pandas(pdf)              # pandas → pandas-on-Spark
```

### Differences from real pandas

- **No in-place ops by default** (e.g., `df.fillna(0, inplace=True)` raises) unless you set `ps.set_option("compute.ops_on_diff_frames", True)`.
- **Index is computed**, not free: certain ops are slower than pandas if they require an index.
- **Default index type**: `sequence` (slow, requires shuffle). Better: `distributed-sequence` or `distributed`.
- Some pandas methods raise `NotImplementedError`.
- Sorting requires a shuffle; pandas's free sort is expensive in pandas-on-Spark.

### When to use

| Scenario | Best choice |
|---|---|
| Data fits on one machine, single-threaded | **pandas** |
| Data too big for one machine, pandas-style code preferred | **pandas-on-Spark** |
| Data too big, performance-critical | **PySpark DataFrame** |
| ML inference batch with pre-trained model | **Pandas UDF (scalar iterator)** on PySpark DataFrame |

---

## 23. Pandas UDFs (different from pandas-on-Spark!)

```python
import pandas as pd
from pyspark.sql.functions import pandas_udf
from pyspark.sql.types import LongType

@pandas_udf(LongType())
def plus_one(s: pd.Series) -> pd.Series:
    return s + 1

df.withColumn("incr", plus_one(F.col("v")))
```

| Type | Signature | Trigger |
|---|---|---|
| Scalar | `pd.Series → pd.Series` | Vectorized column transform |
| Scalar iterator | `Iterator[pd.Series] → Iterator[pd.Series]` | Expensive init (model loading) |
| Grouped Map | `pd.DataFrame → pd.DataFrame` | Used via `df.groupBy("k").applyInPandas(fn, schema)` |
| Grouped Aggregate | `pd.Series → scalar` | Used in `groupBy().agg(udf(col))` |

`mapInPandas(fn, schema)` — applies a function to each partition as a stream of `pd.DataFrame`s, no group key.

---

## 24. File formats and I/O

| Format | Schema | Splittable | Predicate Pushdown | Use case |
|---|---|---|---|---|
| **Parquet** | Embedded | Yes | Yes | Default for analytics |
| **ORC** | Embedded | Yes | Yes | Analytics; Hive-native |
| **Delta** | Embedded (via _delta_log) | Yes | Yes | Lakehouse (exam treats as readable format only) |
| **JSON** | Inferred or explicit | Yes (line-delimited) | Limited | Semi-structured |
| **CSV** | Inferred or explicit | Yes | None (string scan) | Last-resort |
| **Text** | Single `value` column | Yes (line-delimited) | None | Log files |
| **Avro** | External `.avsc` | Yes | Limited | Row-based, schema evolution |

### Read API

```python
spark.read.parquet("path")
spark.read.option("header", True).option("inferSchema", True).csv("path")
spark.read.schema(my_schema).json("path")
spark.read.format("delta").load("/path")
```

### Schema specification

```python
from pyspark.sql.types import StructType, StructField, StringType, IntegerType

# Programmatic
schema = StructType([
    StructField("name", StringType(), nullable=True),
    StructField("age", IntegerType(), nullable=False),
])

# DDL string (concise)
schema = "name STRING, age INT NOT NULL"

df = spark.read.schema(schema).json("path")
```

---

## 25. Spark UI tabs (referenced by official sample Q2)

| Tab | Use case |
|---|---|
| Jobs | Job-level timing, failed jobs |
| Stages | Per-stage task duration distribution (skew detection), shuffle metrics, spill |
| Storage | Cached RDDs/DataFrames, memory vs disk consumption |
| Environment | Spark configuration (effective values) |
| Executors | Per-executor RAM, GC time, shuffle write/read, task counts, **driver logs + executor logs (stdout/stderr)** |
| SQL / DataFrame | Query plan graph + execution timeline, AQE annotations, broadcast vs SMJ decisions |
| Streaming (if active) | Per-query rates, batch durations |

**Executor logs access**: Spark UI → Executors tab → click executor ID → stderr or stdout. (Not via `spark-submit --verbose`.)

---

## 26. Sample-question patterns (from official guide)

| Pattern | Example | What it tests |
|---|---|---|
| A. Code identification | "Which code block writes a DataFrame partitioned by `country` with overwrite mode?" | Method signatures, parameter order, mode/partitionBy presence |
| B. Behavior prediction | "What does setting `spark.sql.shuffle.partitions=200` do?" | Config-key semantics; common misconception (it's POST-shuffle, not source) |
| C. Best-method selection | "For 50M rows, dashboard, 2-3% tolerance — why `approx_count_distinct()`?" | When-to-use; HLL algorithm |
| D. Conceptual/architectural | "Which deployment mode requires all executors on one worker?" | Local mode definition |
| E. Troubleshooting | "How to retrieve executor logs?" | Spark UI navigation |
| F. Streaming scenario | "Why streaming over batch for rolling 2-min agg?" | Incremental processing model |

---

## 27. Common pitfalls (exam-graded)

| # | Pitfall | Notes |
|---|---|---|
| 1 | `union` marked as wide | NARROW — concatenation, no shuffle |
| 2 | `coalesce` (DataFrame method) confused with `F.coalesce` (function) | Different things; same name |
| 3 | DataFrame `.cache()` default = `MEMORY_ONLY` | NO — it's `MEMORY_AND_DISK`. RDD default is `MEMORY_ONLY` |
| 4 | `.union()` matches by column name | NO — by **position**; use `unionByName` for name-based |
| 5 | `na.drop()` drops rows where ALL columns are null | NO — that's `na.drop("all")`. Default `na.drop()` drops ANY null |
| 6 | AQE config key `spark.adaptive.enabled` | DOES NOT EXIST — correct key is `spark.sql.adaptive.enabled` |
| 7 | `spark.sql.shuffle.partitions=200` controls every partition count | NO — only post-shuffle |
| 8 | Broadcast OK on any outer join | NO — only the **non-preserved** side can be broadcast; full outer cannot broadcast either side |
| 9 | Local mode = no executors | NO — has executors, all on the same JVM/worker |
| 10 | `approx_count_distinct` works via compression | NO — works via **HyperLogLog++** algorithm |
| 11 | Window functions ≡ groupBy | NO — windows preserve every input row |
| 12 | Executor logs via `spark-submit --verbose` | NO — via Spark UI → Executors tab |
| 13 | Chained `withColumn` is fine | Often anti-pattern; prefer single `select` for Catalyst |
| 14 | Accumulator counts are exact | NO — may double-count on task retry; use for metrics, not business logic |
| 15 | `F.broadcast(df)` guarantees broadcast | NO — it's a hint; Spark may ignore if size > threshold or `maxResultSize` exceeded |
| 16 | Pandas UDF = pandas-on-Spark | NO — `pandas_udf` is a vectorized PySpark UDF; `pyspark.pandas` is a pandas-compatible API on Spark. Different things. |
| 17 | Spark Connect supports RDDs | NO — Connect clients have no RDD API, no SparkContext, no broadcast variables |
| 18 | `trigger(once=True)` is current best practice | DEPRECATED in 3.5 — use `availableNow` |

---

## 28. Sources (Last verified: 2026-05-23)

- **[Databricks Exam Guide PDF, Oct 30 2025](https://www.databricks.com/sites/default/files/2025-10/databricks-certified-associate-developer-apache-spark-exam-guide-oct-2025.pdf)** — local copy at `research_inputs/13_databricks_spark_dev_associate/databricks_spark_dev_associate_exam_guide.pdf`
- **[Databricks Certification Page](https://www.databricks.com/learn/certification/apache-spark-developer-associate)**
- **[Apache Spark 3.5.0 Release Notes](https://spark.apache.org/releases/spark-release-3-5-0.html)**
- **[Apache Spark 3.5.0 SQL Performance Tuning](https://spark.apache.org/docs/3.5.0/sql-performance-tuning.html)**
- **[Apache Spark 3.5.0 Spark Connect Overview](https://spark.apache.org/docs/3.5.0/spark-connect-overview.html)**
- **[Apache Spark 3.5.0 Pandas API Docs](https://spark.apache.org/docs/3.5.0/api/python/user_guide/pandas_on_spark/index.html)**
- **[Apache Spark 3.5.0 Structured Streaming Guide](https://spark.apache.org/docs/3.5.0/structured-streaming-programming-guide.html)**
