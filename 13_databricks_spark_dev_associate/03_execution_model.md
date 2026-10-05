# Module 03 — Execution Model: Jobs, Stages, Tasks

> **Domain 1 of 7 — Architecture & Components (20%).**
> **Goal:** Operationalize the execution hierarchy. Speculative execution. Dynamic allocation. Spill mechanics. How task failures retry. What "stage retry" means. The runtime behaviors the exam asks about indirectly via "why is this happening?" questions.

---

## Coverage map

Verbatim Oct 2025 exam objectives covered by this module:

| Objective (Section 1 — Architecture, 20%) | Section |
|---|---|
| "Explain the Apache Spark Architecture execution hierarchy." | [Recap: the hierarchy](#recap-the-hierarchy), [The job lifecycle in detail](#the-job-lifecycle-in-detail) |
| "Configure Spark partitioning in distributed data processing, including shuffles and partitions." | [Where the "200" comes from](#where-the-200-comes-from), [Partitioning at read time](#partitioning-at-read-time), [Repartitioning vs coalescing](#repartitioning-vs-coalescing-refresh) |
| "Describe the architecture of Apache Spark, including ... garbage collection." | [Garbage collection patterns](#garbage-collection-patterns) |
| "Describe the execution patterns of the Apache Spark engine, including actions, transformations, and lazy evaluation." | [Task scheduling](#task-scheduling), [Task failures and retries](#task-failures-and-retries) |

---

> 🎯 **How to recognize this on the exam:**
> - "What does `spark.sql.shuffle.partitions=200` set?" → **Post-shuffle** partition count, NOT read-side. Sample Q5.
> - "How many tasks in a stage with N partitions?" → **N**.
> - "Default task retry count?" → **4** (`spark.task.maxFailures`).
> - "Is speculative execution on by default?" → **No** in OSS Spark.
> - "Is dynamic allocation on by default?" → **No** in OSS Spark (yes on Databricks).
> - "Read-side partition size config?" → `spark.sql.files.maxPartitionBytes` = **128 MB**.
> - "Why is `.collect()` risky?" → driver OOM; rows all materialize in driver heap.
> - "What happens when an executor dies?" → tasks rescheduled; cached partitions lost; lineage recomputes.
> - "What causes Spill (Disk) in Spark UI?" → execution memory insufficient; spills sort/hash state to local disk.
> - If `repartition(500)` on a DataFrame with 200 partitions → **500** (full shuffle, can increase). If `coalesce(500)` → **200** (cannot increase).

---

## Recap: the hierarchy

```
Application                      (one per SparkSession)
  └─ Job                         (one per action)
       └─ Stage                  (one per shuffle boundary; "ShuffleMapStage" or final "ResultStage")
            └─ Task              (one per partition)
                 └─ runs as a thread on an executor core
```

Module 02 covered how the DAG is built from lazy transformations and which transformations trigger stage boundaries. This module covers **what actually happens at runtime** — speculative execution, failure recovery, dynamic allocation, spill behavior, the diagnostic signals.

---

## The job lifecycle in detail

```mermaid
sequenceDiagram
    participant U as User
    participant D as Driver (DAG + Task Scheduler)
    participant CM as Cluster Manager
    participant E as Executor

    U->>D: df.count() (action)
    D->>D: Compile logical → physical plan
    D->>D: Decompose into stages by shuffle boundary
    D->>CM: Request executors (if dynamic alloc on)
    CM->>E: Launch executor JVM
    E->>D: Register; heartbeat starts
    D->>E: Submit Stage 1 tasks (one per partition)
    E->>E: Run tasks; cache blocks; write shuffle files
    E->>D: Task status (success / fail / retry needed)
    D->>D: Stage 1 complete → submit Stage 2
    D->>E: Submit Stage 2 tasks (post-shuffle)
    E->>E: Read shuffle files from Stage 1; compute
    E->>D: Stage 2 complete → final result rows
    D->>U: Return result (or write)
```

### Stage types

| Stage type | What it produces |
|---|---|
| **ShuffleMapStage** | Writes shuffle files for the next stage |
| **ResultStage** | Produces the final result (for the action) |

The last stage is always a ResultStage; everything before it is a ShuffleMapStage.

### Where the "200" comes from

Default `spark.sql.shuffle.partitions = 200`. After any wide transformation, the downstream stage has 200 tasks unless AQE coalesces them (Module 10).

```python
spark.conf.set("spark.sql.shuffle.partitions", "400")
```

⚠️ **Exam trap:** `spark.sql.shuffle.partitions` controls **post-shuffle** partition count, NOT every DataFrame's partition count. The official sample Q5 tests this — many candidates think it sets the read-side partition count.

The number of partitions when you **read** a file is determined by:
- File size and `spark.sql.files.maxPartitionBytes` (128 MB default).
- Number of files and `spark.sql.files.openCostInBytes` (4 MB default, used as a per-file overhead estimate).
- Cluster's `spark.default.parallelism`.

---

## Task scheduling

The driver's **TaskScheduler** sends tasks to executors based on:

### Locality preferences

Spark schedules tasks to **maximize data locality** — running a task on the executor that already has the data in memory.

| Locality level | Meaning |
|---|---|
| **PROCESS_LOCAL** | Data is already in the executor's JVM (cached) |
| **NODE_LOCAL** | Data is on the same node (HDFS replica, or cached on another executor on same node) |
| **RACK_LOCAL** | Data is on the same rack |
| **ANY** | Anywhere |

If the preferred locality isn't available, Spark **waits** for a configurable timeout (`spark.locality.wait` default 3s) before falling back to the next-best locality.

⚠️ Not deeply exam-tested but can appear: "Which locality level is best?" → PROCESS_LOCAL.

### FIFO vs FAIR scheduling

| | FIFO (default) | FAIR |
|---|---|---|
| Multiple concurrent jobs | First-in queues block later jobs | Round-robin between job pools |
| Use case | Single-user batch | Shared cluster, multiple users |

Set via `spark.scheduler.mode`. Most exam questions assume FIFO.

---

## Task failures and retries

```mermaid
flowchart TB
    T[Task launched] -->|completes| OK[Task SUCCESS]
    T -->|exception| FAIL[Task FAILED]
    FAIL --> CHECK{Retries < spark.task.maxFailures (default 4)?}
    CHECK -->|yes| RETRY[Re-launch task<br/>(possibly on different executor)]
    CHECK -->|no| STAGE_FAIL[Stage FAILED]
    STAGE_FAIL --> JOB_FAIL[Job FAILED]
    RETRY --> T
```

### Settings

- `spark.task.maxFailures` (default 4): per-task retry limit. After 4 failures of the same task, the **stage fails** and the job fails.
- `spark.stage.maxConsecutiveAttempts` (default 4): how many stage-level retries before giving up.

### Executor death

When an executor dies (OOM, network failure, spot preemption):
- All tasks running on it fail.
- All cached blocks on it are lost (and must be recomputed via lineage if needed downstream).
- The cluster manager may relaunch the executor.

⚠️ **Exam framing:** "What happens if an executor dies mid-stage?" → tasks rescheduled to surviving executors; cached partitions lost; lineage recomputes them as needed.

---

## Speculative execution

```python
spark.conf.set("spark.speculation", "true")
```

**Default: OFF in OSS Spark.** When ON:

- Spark monitors task duration within a stage.
- If a task is running significantly slower than the median (controlled by `spark.speculation.quantile`, `spark.speculation.multiplier`), Spark **launches a duplicate** of that task on another executor.
- Whichever finishes first wins; the other is killed.

**When useful:**
- Heterogeneous cluster nodes (some slower than others).
- Spot/preemptible instances with variable performance.
- Stragglers from minor data skew where AQE skew handling didn't catch the issue.

**When harmful:**
- Tasks have **side effects** (e.g., writing to non-idempotent sinks) — could double-write.
- Pure compute jobs with predictable timing — adds overhead without benefit.

⚠️ **Exam framing:** "What is speculative execution?" → Spark launches duplicate copies of slow-running tasks to mitigate stragglers; off by default.

---

## Dynamic allocation

```python
spark.conf.set("spark.dynamicAllocation.enabled", "true")
```

**Default: OFF in OSS Spark; ON on Databricks (where it's called "autoscaling").**

When ON, the driver requests more executors when there's a backlog of pending tasks, and releases executors that have been idle for `spark.dynamicAllocation.executorIdleTimeout` (default 60s).

### Key configs

- `spark.dynamicAllocation.minExecutors`
- `spark.dynamicAllocation.maxExecutors`
- `spark.dynamicAllocation.initialExecutors`
- `spark.dynamicAllocation.executorIdleTimeout` (default 60s)
- `spark.dynamicAllocation.schedulerBacklogTimeout` (default 1s; how long to wait for backlog before requesting more)

### Requirement: external shuffle service

When executors are removed, their **shuffle files would be lost** — but downstream stages still need them. So dynamic allocation requires an **external shuffle service** running on each worker (independent of the executor's lifecycle), OR shuffle tracking (`spark.dynamicAllocation.shuffleTracking.enabled` since 3.0).

⚠️ **Not deeply exam-tested**, but useful to know: dynamic allocation needs either the external shuffle service or shuffle tracking, otherwise executors can't be safely removed when they hold shuffle data.

---

## Spill mechanics

When in-memory operations exceed available execution memory, Spark spills to local disk.

### Operations that can spill

| Operation | Why it spills |
|---|---|
| Sort (within partition) | Sort buffer can't fit in memory |
| Hash aggregation (`groupBy`) | Hash table too big |
| Hash join build side (SHJ) | Build-side hash table too big |
| Window function | Within-partition buffer too big |
| Shuffle write | Output partition buffers too big |

### What's spilled

- **Sorted runs** for sort-based operations: spilled, then merged from disk during the final pass.
- **Hash partitions** for hash aggregations: when memory runs out, current partition flushed to disk; later merged.

### Reading spill in the Spark UI

The Stages tab shows per-task:
- **Spill (Memory)**: in-memory size of spilled data before serialization.
- **Spill (Disk)**: on-disk size of spilled data (post-serialization, usually smaller).

Heavy spill is a signal to:
- Increase executor memory (`spark.executor.memory`).
- Increase shuffle partitions (`spark.sql.shuffle.partitions`) to reduce per-task data.
- Pre-aggregate before the wide step.

⚠️ **Exam framing:** "What causes disk spill?" → execution memory insufficient for the operation; Spark spills sorted/hashed state to local disk.

---

## Partitioning at read time

When you do `spark.read.parquet("path")`, the number of partitions in the resulting DataFrame depends on file layout:

### One partition per file (usually)

- For **splittable formats** (Parquet, ORC), Spark may read multiple files in one partition or split a single large file into multiple partitions.
- Target partition size: `spark.sql.files.maxPartitionBytes` (default **128 MB**).
- Per-file overhead estimate: `spark.sql.files.openCostInBytes` (default **4 MB**) — added to each file's size for the partition-packing calculation.

### Reading 1000 small files

If you read 1000 × 1 MB Parquet files:
- Each file is 1 MB; openCost is 4 MB; effective per-file "size" = 5 MB.
- Spark packs files into 128 MB partitions → ~25 files per partition.
- You get ~40 partitions.

But if you've **also** set `spark.sql.shuffle.partitions=200` and the next op is a shuffle, the downstream stage will have 200 tasks.

⚠️ **Exam framing:** "I read 1000 files but only get 40 partitions" → file packing into 128 MB partitions is the explanation.

---

## Repartitioning vs coalescing (refresh)

```python
df.rdd.getNumPartitions()      # current count
df.repartition(400)            # WIDE — full shuffle, balanced
df.coalesce(50)                # NARROW — combine on executors, can only decrease
df.repartition("region")       # WIDE — hash by region
df.repartition(50, "region")   # WIDE — hash by region into 50 partitions
df.sortWithinPartitions("ts")  # NARROW — sort within each partition
```

| Want to... | Use |
|---|---|
| Reduce partition count (small data, write fewer files) | `coalesce(n)` |
| Increase partition count | `repartition(n)` |
| Co-locate rows with same key (pre-join optimization) | `repartition(col)` |
| Balance partitions after a skewed shuffle | `repartition(n)` |

⚠️ **`coalesce` cannot increase** partition count. If you call `df.coalesce(1000)` on a 200-partition DataFrame, you still get 200.

---

## The "small files problem" and the "too few partitions" problem

### Too few partitions (under-parallelism)

```
Executors: 20 cores
Partitions: 4

Result: 16 cores idle; 4 tasks running serial-ish on 4 executors
Fix: repartition(40-200) — let Spark distribute work
```

### Too many partitions (overhead-dominated)

```
Executors: 20 cores
Partitions: 100,000

Result: scheduling overhead, tiny tasks (~10ms each), GC pressure
Fix: coalesce(200-400) — bigger tasks
```

Rule of thumb: aim for partitions where each task processes **~100 MB to 1 GB** of data and takes **30s-3min**. Smaller and you're scheduling-bound; larger and you risk memory/spill.

---

## What "shuffle write" and "shuffle read" mean in the UI

In the Spark UI Stages tab, each stage shows:

| Column | Meaning |
|---|---|
| **Shuffle Write** | Bytes written to local disk by tasks in this stage (consumed by downstream stage) |
| **Shuffle Read** | Bytes fetched from upstream stages' shuffle files |
| **Input Size / Records** | Bytes/rows read from data sources |
| **Output Size / Records** | Bytes/rows written to data sinks |
| **Spill (Memory) / Spill (Disk)** | Per-task spill |

Diagnostic signals:
- Huge **Shuffle Read** in a single task → skew.
- Huge **Spill (Disk)** → memory pressure; increase memory or partitions.
- Huge **Input Size** but small **Output** in early stages → consider predicate pushdown.

---

## Driver-side execution

Some operations happen entirely on the driver:

| Operation | Why driver-only |
|---|---|
| `df.collect()` | All rows shipped to driver |
| `df.toPandas()` | All rows + conversion to pandas |
| `df.toLocalIterator()` | Streams partitions to driver |
| `df.head(n)` / `take(n)` | Pulls first N rows |
| `df.first()` | Pulls one row |
| Broadcast variable creation | Driver materializes value before shipping |
| Catalyst optimization | Driver-side query planning |

⚠️ **Driver OOM is real.** `.collect()` on a 10 GB DataFrame OOMs the driver. Sample question: "What happens when you call `.collect()` on a large dataset?" → driver-side OOM risk.

Use `.show(n)`, `.take(n)`, or write to storage if you don't need all rows.

---

## Garbage collection patterns

```
Healthy:
  GC time per executor < 10% of task time
  Young-gen collections only

Memory-pressured:
  Full GCs occurring
  GC time > 30%
  
Solutions:
  - Increase executor memory
  - Use Kryo serializer
  - Reduce cached data
  - Move to MEMORY_AND_DISK_SER caching
  - Reduce per-task data (more partitions)
```

⚠️ Not deeply exam-tested. Just know "long GC = memory pressure" and "Kryo serializer compresses better than Java serializer."

---

## Broadcast variables and accumulators (preview)

These are SparkContext-level constructs, not DataFrame-level:

```python
sc = spark.sparkContext

# Broadcast variable — read-only, shipped to all executors
lookup = {"A": 1, "B": 2, "C": 3}
bv = sc.broadcast(lookup)

@F.udf("int")
def lookup_udf(key):
    return bv.value.get(key, -1)

# Accumulator — write-only counter
ac = sc.accumulator(0)

def count_rows(row):
    ac.add(1)

df.foreach(count_rows)
print(ac.value)  # approximate; may double-count on retries
```

### Restrictions

- **Spark Connect clients have NO `sc.broadcast` or `sc.accumulator`** (Module 12).
- **Accumulators are NOT fault-tolerant for business logic** — task retries may increment them multiple times.
- **`F.broadcast(df)`** is a totally different concept — a join hint to broadcast a DataFrame for a broadcast hash join (Module 09).

---

## Mini-quiz

1. How many tasks run in a stage with 50 partitions?
2. What's the default `spark.sql.shuffle.partitions`?
3. What's the difference between `repartition(50)` and `coalesce(50)` on a 200-partition DataFrame?
4. What does speculative execution do?
5. Is dynamic allocation on by default in OSS Spark?
6. After a task fails 4 times (default), what happens?
7. What causes a Spill (Disk) entry in the Spark UI?
8. Why is `.collect()` risky on a large DataFrame?
9. What's the difference between a broadcast variable and `F.broadcast(df)`?
10. Can `coalesce(500)` increase partitions from 200 to 500?

### Answers

1. **50.**
2. **200.**
3. `repartition(50)` is a **full shuffle** to exactly 50 balanced partitions. `coalesce(50)` is **narrow**, combining partitions on the same executor to get to 50 (or fewer, if executors don't have enough partitions). Can leave unbalanced.
4. Spark launches **duplicate copies of slow-running tasks** on other executors; whichever finishes first wins.
5. **No, off by default.** Databricks turns it on (autoscaling).
6. The **stage fails** and the job fails.
7. Execution memory was insufficient for sort/hash/window state, so Spark spilled to local disk.
8. Driver-side OOM — all rows materialize in driver heap.
9. **`sc.broadcast(value)`** is a read-only Python value shipped to executors. **`F.broadcast(df)`** is a join hint that causes Spark to broadcast a DataFrame for a broadcast hash join. Same word, very different mechanisms.
10. **No.** `coalesce` can only decrease.

---

## Exam-day cheat sheet

- **`spark.sql.shuffle.partitions` = 200 by default; controls POST-shuffle partition count, not read-side.** ⚠️
- **Read partitioning** controlled by `spark.sql.files.maxPartitionBytes` (128 MB default).
- **Task retries**: 4 by default; then stage fails.
- **Speculative execution**: OFF by default in OSS Spark.
- **Dynamic allocation**: OFF by default in OSS Spark; ON on Databricks.
- **One task per partition per stage.**
- **`.collect()` on large DF → driver OOM.** Use `.show()`, `.take(n)`, or write to storage.
- **Spill (Disk) in Spark UI = memory pressure.**
- **`coalesce` only decreases; `repartition` always shuffles.**

Next: [Module 04 — Spark SQL Basics](04_spark_sql_basics.md).
