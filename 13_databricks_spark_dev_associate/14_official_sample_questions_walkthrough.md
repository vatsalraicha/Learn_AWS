# Module 14 — Official Sample Questions Walkthrough

> **Synthesis module — work through the 10 sample questions from the Oct 2025 exam guide.**
> Per Databricks NDA, the exact wording of questions cannot be reproduced. Each question below is **paraphrased** to preserve the testing intent while remaining NDA-compliant. Each walkthrough cites the original module covering the underlying concept.

---

## How to use this module

1. **Read each question.** Try to answer cold (don't peek at the explanation).
2. **Pick your answer** from the 4 paraphrased options.
3. **Read the walkthrough** to understand WHY each option is right or wrong.
4. **Note the source module** for any topic you're shaky on; revisit.

Work through all 10. Then take it again 24 hours later — if you don't get 10/10 second pass, your weak spots are clear.

---

## Question 1 — Code identification: write a partitioned Parquet with overwrite

> A data engineer needs to write a DataFrame `df` to a Parquet file at `/data/output`, partitioned by `country`, overwriting any existing data. Which code block accomplishes this?

**Options:**

- **A.** `df.write.partitionBy("country").parquet("/data/output")`
- **B.** `df.write.mode("overwrite").partitionBy("country").parquet("/data/output")`
- **C.** `df.write.partitionBy("country").mode("overwrite").parquet("/data/output")`
- **D.** `df.write.mode("overwrite").parquet("/data/output").partitionBy("country")`

### Walkthrough

**Correct: B (and C — both work).** The `mode()` and `partitionBy()` calls return the writer builder, so they can be chained in either order. The terminal method is `.parquet(path)`.

- **A.** ❌ Missing `mode("overwrite")` — will fail if `/data/output` exists (default mode is `errorIfExists`).
- **B.** ✅ Correct.
- **C.** ✅ Also valid — order of `mode()` and `partitionBy()` doesn't matter; both return the builder.
- **D.** ❌ `.parquet(path)` is the terminal method — it returns `None` (or initiates the write). Calling `.partitionBy()` after it is invalid.

⚠️ **Exam framing:** if there are two correct-looking options (B and C), check whether the exam offers both as "valid" or expects one. The actual exam typically has only one valid option in the answer set (e.g., D becomes a distractor, leaving only B or only C as valid).

**Source:** [Module 06 — DataFrame Basics](06_dataframe_basics.md) (save modes, partitioning).

---

## Question 2 — Troubleshooting: retrieve executor logs

> A Spark engineer wants to retrieve the executor logs to diagnose a performance issue in a recent run. How should they do this?

**Options:**

- **A.** Run `spark-submit --verbose` to enable detailed logging.
- **B.** Print to stdout from inside the executor code.
- **C.** Navigate to the Spark UI → Executors tab → click an executor ID → choose stderr or stdout.
- **D.** Check the system log files on each worker node manually.

### Walkthrough

**Correct: C.**

- **A.** ❌ `spark-submit --verbose` logs the submitter side (driver argument resolution, classpath). Doesn't capture executor logs.
- **B.** ❌ Printing helps for debugging custom logic but doesn't help post-hoc diagnostics of an existing failed run.
- **C.** ✅ The canonical path. Spark UI → Executors tab → executor ID → stderr (errors) or stdout. All Spark executor logs are routed here.
- **D.** ❌ Possible but tedious and not the recommended approach. Also fails if you don't have shell access to workers.

⚠️ **This is sample Q2 of the official guide.** Memorize the path: **Spark UI → Executors tab → click executor → stderr/stdout**.

**Source:** [Module 10 — Performance Tuning](10_performance_tuning.md) (Spark UI tabs).

---

## Question 3 — Behavior prediction: `spark.sql.shuffle.partitions`

> What is the effect of setting `spark.sql.shuffle.partitions = 200`?

**Options:**

- **A.** Sets the number of partitions for all DataFrame reads.
- **B.** Sets the initial number of partitions after a shuffle operation (groupBy, join, etc.).
- **C.** Sets the number of executor JVMs to launch.
- **D.** Sets the maximum number of concurrent tasks.

### Walkthrough

**Correct: B.**

- **A.** ❌ Read-side partitioning is controlled by `spark.sql.files.maxPartitionBytes` (128 MB default) for file sources.
- **B.** ✅ Correct. This config is **post-shuffle** — the initial partition count after any wide transformation. AQE may coalesce these to fewer, larger partitions at runtime.
- **C.** ❌ Executor count is controlled by `spark.executor.instances` or dynamic allocation.
- **D.** ❌ Concurrent task count = total executor cores; unrelated to this config.

⚠️ **Common misconception:** people think this config controls all partitioning. It controls only shuffle (post-wide-transformation) partitioning.

**Source:** [Module 03 — Execution Model](03_execution_model.md) (shuffle partitions).

---

## Question 4 — Code identification: `withColumn` then conditional

> Which code block adds a column `tier` that is `"premium"` when `amount > 1000`, `"standard"` when `100 < amount <= 1000`, and `"basic"` otherwise?

**Options:**

- **A.** `df.withColumn("tier", F.if(F.col("amount") > 1000, "premium", "standard"))`
- **B.** `df.withColumn("tier", F.when(F.col("amount") > 1000, "premium").when(F.col("amount") > 100, "standard").otherwise("basic"))`
- **C.** `df.withColumn("tier", F.case(F.col("amount") > 1000, "premium").case(F.col("amount") > 100, "standard").default("basic"))`
- **D.** `df.withColumn("tier", if F.col("amount") > 1000 then "premium" elif F.col("amount") > 100 then "standard" else "basic")`

### Walkthrough

**Correct: B.**

- **A.** ❌ `F.if` doesn't exist. There's `F.when(...).otherwise(...)` and `F.expr("IF(...)")`.
- **B.** ✅ Correct. Chain `.when(...)` calls, ending with `.otherwise(...)` for the default.
- **C.** ❌ `F.case` doesn't exist as a chained API. SQL CASE is expressed via `F.when`.
- **D.** ❌ Not valid Python syntax; mixes `if/then/else` (which isn't Python) with PySpark.

⚠️ **Each `.when(cond, value)`** returns a column that can be further chained. The final `.otherwise(value)` provides the default. Without `otherwise`, non-matching rows get NULL.

**Source:** [Module 05 — Spark SQL Functions](05_spark_sql_functions.md) (conditional expressions).

---

## Question 5 — Best-method selection: `approx_count_distinct`

> A data engineer needs to count distinct user IDs in a 50-million-row table for a dashboard, with a 2-3% tolerance for error in exchange for speed. Which function should they use, and why?

**Options:**

- **A.** `F.count_distinct("user_id")` — exact count is always preferable.
- **B.** `F.approx_count_distinct("user_id", rsd=0.03)` — uses HyperLogLog++ to avoid shuffling the full distinct set.
- **C.** `F.countDistinct("user_id")` — uses bitmap indexing for speed.
- **D.** `F.approx_count_distinct("user_id")` — only counts non-null values, which is faster.

### Walkthrough

**Correct: B.**

- **A.** ❌ `count_distinct` is exact but expensive — requires a full shuffle of distinct values.
- **B.** ✅ Correct. **HyperLogLog++** (HLL) is the algorithmic reason it's fast — each partition computes a small sketch, and sketches are merged in a single step. The `rsd` parameter controls relative standard deviation (~0.05 = 5% error by default; 0.03 = 3%).
- **C.** ❌ `countDistinct` is the same as `count_distinct` (case difference; both exist). It does NOT use bitmap indexing.
- **D.** ❌ "Only counts non-null" is true of both `approx_count_distinct` AND `count_distinct` — that's not the speed reason. The speed reason is **HyperLogLog**, not null handling.

⚠️ **This is sample Q10.** The key fact: speed comes from **HyperLogLog++ algorithm avoiding a global distinct shuffle**, not from compression, null handling, or bitmap indexing.

**Source:** [Module 08 — Aggregations](08_aggregations_window.md) (approx_count_distinct).

---

## Question 6 — Behavior prediction: `na.drop("all")`

> What does `df.na.drop("all")` do?

**Options:**

- **A.** Drops all rows in the DataFrame.
- **B.** Drops rows where ANY column is null.
- **C.** Drops rows where ALL columns are null.
- **D.** Drops all null values, replacing them with defaults.

### Walkthrough

**Correct: C.**

- **A.** ❌ Doesn't drop all rows; only specific ones.
- **B.** ❌ That's the **default** behavior — `df.na.drop()` or `df.na.drop("any")` drops rows with at least one null.
- **C.** ✅ Correct. The `"all"` argument means drop a row only if ALL its columns are null. A row with even one non-null value is kept.
- **D.** ❌ Replacement is `df.na.fill(...)`, not `drop`.

⚠️ **The trap:** people assume `"all"` means "drop all rows with any null" because "all" sounds inclusive. It's the opposite — `"all"` means "the row must be entirely null to be dropped."

| Call | Behavior |
|---|---|
| `df.na.drop()` or `df.na.drop("any")` | Drop rows with ANY null (default) |
| `df.na.drop("all")` | Drop rows where ALL cols are null |
| `df.na.drop(thresh=N)` | Drop rows with fewer than N non-null values |
| `df.na.drop(subset=["col1"])` | Drop rows where `col1` is null |

**Source:** [Module 05 — Spark SQL Functions](05_spark_sql_functions.md) (null handling) and FACTS.md §16.

---

## Question 7 — Conceptual: deployment mode definition

> Which Apache Spark deployment mode requires all executors to run on a single worker node?

**Options:**

- **A.** Client mode
- **B.** Cluster mode
- **C.** Local mode
- **D.** Standalone mode

### Walkthrough

**Correct: C.**

- **A.** ❌ Client mode runs the driver on the submitting machine; executors run on the cluster, distributed across nodes.
- **B.** ❌ Cluster mode runs the driver on a worker node; executors run on other worker nodes, distributed.
- **C.** ✅ Correct. **Local mode** runs the driver AND all executors as threads in a single JVM on the local machine. Specified via `spark.master = "local[N]"`.
- **D.** ❌ Standalone is a **cluster manager** (Spark's own), not a deployment mode. Easy to confuse.

⚠️ **Deployment mode** is orthogonal to **cluster manager**. You can have:
- Client mode on YARN
- Cluster mode on Kubernetes
- Local mode (no cluster manager involved)

The exam tests deployment modes; "standalone" appears as a distractor.

**Source:** [Module 12 — Spark Connect](12_spark_connect.md) (deployment modes) and [Module 01 — Spark Architecture](01_spark_architecture.md).

---

## Question 8 — Code identification: streaming output mode

> A streaming query computes a rolling 2-minute aggregation of events. The data engineer wants to write the entire aggregated result to a console sink. Which output mode should they use?

**Options:**

- **A.** `outputMode("append")` without watermarks.
- **B.** `outputMode("update")` to emit only changed rows.
- **C.** `outputMode("complete")` since the query is an aggregation.
- **D.** `outputMode("full")` to write the entire table.

### Walkthrough

**Correct: C.**

- **A.** ❌ Append mode for aggregations REQUIRES a watermark. Without one, Spark rejects the query.
- **B.** ✅ Actually valid — update mode emits changed rows. But the question asks for "entire aggregated result" → C is the better fit.
- **C.** ✅ Correct. `complete` mode emits the **entire result table** every micro-batch. Only valid for aggregations. The console sink works well with complete mode for dashboard-style output.
- **D.** ❌ `"full"` is not a valid output mode. Valid modes: `append`, `update`, `complete`.

⚠️ **Output modes recap:**
- `append`: only new rows. For agg, requires watermark.
- `update`: only changed rows. For agg, valid without watermark.
- `complete`: entire result table. Only for agg.

**Source:** [Module 11 — Structured Streaming](11_structured_streaming.md) (output modes).

---

## Question 9 — Conceptual: streaming vs batch

> A data engineer needs to compute a rolling 2-minute count of events. Why use Spark Structured Streaming over batch?

**Options:**

- **A.** Streaming is always faster than batch processing.
- **B.** Streaming uses less memory than batch.
- **C.** Streaming maintains state incrementally — each new micro-batch only processes new data, not the entire history.
- **D.** Streaming runs on a separate Spark engine optimized for low latency.

### Walkthrough

**Correct: C.**

- **A.** ❌ Streaming has per-micro-batch overhead. For one-shot computation, batch is faster.
- **B.** ❌ Streaming actually uses more memory (state stores, checkpoints).
- **C.** ✅ Correct. **Incremental computation** is the defining advantage. A 2-minute rolling count over a continuous stream processes only the last 2 minutes' new data per trigger, vs batch which would reprocess everything.
- **D.** ❌ Structured Streaming runs on the SAME Spark engine as batch (unified API). It's not a separate engine.

⚠️ **Sample Q (likely paraphrased Q9 type):** the answer hinges on understanding the **unified, incremental** nature of Structured Streaming.

**Source:** [Module 11 — Structured Streaming](11_structured_streaming.md) (programming model).

---

## Question 10 — Code identification: read CSV with explicit schema

> Which code block reads a pipe-delimited CSV file at `/data/events.csv` with header, applying an explicit schema (`event_id INT, user_id INT, ts TIMESTAMP`)?

**Options:**

- **A.** `spark.read.csv("/data/events.csv").schema("event_id INT, user_id INT, ts TIMESTAMP")`
- **B.** `spark.read.option("header", True).option("delimiter", "|").schema("event_id INT, user_id INT, ts TIMESTAMP").csv("/data/events.csv")`
- **C.** `spark.read.csv("/data/events.csv", header=True, delimiter="|", schema="event_id INT, user_id INT, ts TIMESTAMP")`
- **D.** `spark.read.option("inferSchema", True).option("header", True).option("delimiter", "|").csv("/data/events.csv")`

### Walkthrough

**Correct: B (or C — both work; B is the canonical builder form).**

- **A.** ❌ The `.schema(...)` call AFTER the terminal `.csv(...)` is invalid — terminal methods return the DataFrame, not the builder.
- **B.** ✅ Correct builder pattern: chain `.option()` and `.schema()` calls, then call the terminal `.csv(path)`.
- **C.** ✅ Also valid in PySpark — `spark.read.csv()` accepts keyword arguments for options. (PySpark-specific convenience.)
- **D.** ❌ Uses `inferSchema=True` — works, but doesn't APPLY the explicit schema. The question requires explicit schema.

⚠️ **Two valid answers (B and C) typically don't appear together** on the exam — one will be slightly broken. Read carefully.

**Source:** [Module 06 — DataFrame Basics](06_dataframe_basics.md) (reading CSV).

---

## Synthesis — patterns to internalize

After working through all 10, you'll notice patterns:

### Pattern A: Code identification (Q1, Q4, Q10)

- Method signatures matter.
- Terminal method (`.parquet`, `.csv`, `.save`) must come LAST.
- Builder chain order rarely matters between `.option`/`.mode`/`.partitionBy`/`.schema`.

### Pattern B: Behavior prediction (Q3, Q6)

- Read config keys carefully — `spark.sql.shuffle.partitions` is post-shuffle, not read.
- `na.drop("all")` means ALL columns null (counter-intuitive).

### Pattern C: Best-method selection (Q5)

- Read the constraint: "tolerates 3% error" → approx_count_distinct.
- Memorize the ALGORITHM behind the speedup (HyperLogLog++), not vague phrases.

### Pattern D: Conceptual (Q7, Q9)

- Know definitions cold: local mode = all executors in one JVM.
- "Why streaming?" → incremental computation.

### Pattern E: Troubleshooting (Q2)

- Spark UI → Executors tab → stderr/stdout. Memorize this path.

### Pattern F: Streaming scenarios (Q8, Q9)

- Output modes: append (no agg or watermarked agg), update (changed), complete (agg only).
- Watermark required for append + agg.

---

## What to study if you got X wrong

| Wrong | Revisit |
|---|---|
| Q1 (write/partition) | Module 06 |
| Q2 (executor logs) | Module 10 |
| Q3 (shuffle partitions) | Module 03 |
| Q4 (when/otherwise) | Module 05 |
| Q5 (approx_count_distinct) | Module 08 |
| Q6 (na.drop "all") | Module 05, FACTS §16 |
| Q7 (local mode) | Modules 01, 12 |
| Q8 (output modes) | Module 11 |
| Q9 (streaming vs batch) | Module 11 |
| Q10 (read CSV schema) | Module 06 |

---

## Extended walkthrough — additional question patterns

These aren't from the official guide but follow the same patterns and test the same trap topics.

### Bonus 1: union semantics

> Which statement about `df1.union(df2)` is true?

**Options:**

- A. It triggers a shuffle by the join key.
- B. It is a wide transformation.
- C. It matches columns by name.
- D. It is a narrow transformation that concatenates partitions.

**Correct: D.** `union` is narrow. ⚠️ Common trap — people pick B because "joining tables = wide."

Module 02 + Module 09.

### Bonus 2: cache default

> What is the default storage level when calling `df.cache()` on a DataFrame?

**Options:**

- A. MEMORY_ONLY
- B. DISK_ONLY
- C. MEMORY_AND_DISK
- D. MEMORY_AND_DISK_SER

**Correct: C.** DataFrame `.cache()` defaults to `MEMORY_AND_DISK` (NOT MEMORY_ONLY — that's the RDD default).

Module 10 + FACTS §11.

### Bonus 3: broadcast outer-join restriction

> For a left outer join `df_large.join(df_small, "k", "left")`, which side can be broadcast?

**Options:**

- A. The left side (df_large).
- B. The right side (df_small).
- C. Either side.
- D. Neither — broadcast joins don't support outer joins.

**Correct: B.** Only the **non-preserved** (right) side can be broadcast in a left outer.

Module 09.

### Bonus 4: AQE config key

> Which Spark configuration enables Adaptive Query Execution?

**Options:**

- A. `spark.adaptive.enabled`
- B. `spark.sql.adaptive.enabled`
- C. `spark.sql.aqe.enabled`
- D. `spark.sql.optimizer.adaptive`

**Correct: B.** All AQE configs start with `spark.sql.adaptive.`. Distractors A, C, D don't exist.

Module 10.

### Bonus 5: Spark Connect restriction

> Which API is NOT available when using Spark Connect?

**Options:**

- A. DataFrame `.filter()`
- B. `spark.sql()`
- C. RDD API (`df.rdd`)
- D. `pandas_udf`

**Correct: C.** RDD API is not available in Spark Connect clients (no JVM access). DataFrame, SQL, and pandas_udf all work.

Module 12.

---

## Exam-day strategy

When you encounter a question on the actual exam:

1. **Read the question twice.** The constraint matters (e.g., "with 3% error tolerance" → approx).
2. **Eliminate obviously wrong** options first (wrong function names, invalid syntax).
3. **Among remaining**, pick the one that matches the CANONICAL pattern (the simplest, idiomatic answer).
4. **Watch for traps:**
   - "All" in `na.drop("all")` means ALL columns null (counter-intuitive).
   - "Union" is narrow (counter-intuitive).
   - "Local mode" = single JVM (not "no executors").
   - "AQE config" starts with `spark.sql.adaptive.` (not `spark.adaptive.`).
5. **Don't over-think.** If two answers look equally valid, the canonical one is usually correct.
6. **Mark and return** if unsure — 90 minutes / 45 questions = 2 min each; you have buffer.

---

## Final check — are you ready?

Before booking the exam, you should be able to answer **without referring to notes**:

| Topic | Self-test |
|---|---|
| Narrow vs wide transformations | List 5 each |
| Output modes for streaming | What watermark requires what |
| AQE config keys | Cite 4 with defaults |
| Storage levels | Default for DataFrame `.cache()` |
| Broadcast outer join | Which side for left/right/full |
| Local mode definition | Where executors run |
| Spark Connect | URI scheme, protocol, restrictions |
| Pandas API on Spark vs Pandas UDF | The distinction |
| `na.drop()` variants | `"any"` vs `"all"` semantics |
| `approx_count_distinct` | Why it's fast (HyperLogLog) |

If you stumble on any of these, **revisit the corresponding module before the exam**.

---

## Exam-day cheat sheet (consolidated)

Pull this up the morning of the exam:

- **45Q / 90 min / 70% pass / Python only / Spark 3.5.**
- **AQE: `spark.sql.adaptive.enabled = true` since 3.2.**
- **`spark.sql.autoBroadcastJoinThreshold = 10 MB` default.**
- **`spark.sql.shuffle.partitions = 200` default (POST-shuffle).**
- **DataFrame `.cache()` = MEMORY_AND_DISK** (RDD = MEMORY_ONLY).
- **`union` is NARROW; matches by POSITION; doesn't dedupe.**
- **`coalesce(n)` is NARROW** (DataFrame method); **`F.coalesce(c1, c2)`** is first-non-null function.
- **Broadcast outer-join: only the NON-PRESERVED side.**
- **Full outer cannot broadcast either side.**
- **Local mode = all executors in one JVM on single machine.**
- **Spark Connect: `sc://`, gRPC, no RDD, no SparkContext, no broadcast vars.**
- **Pandas API on Spark = `pyspark.pandas` (replacement); Pandas UDF = `pandas_udf` (decorator).** Different things.
- **Streaming output modes: append (no agg or watermark+agg), update, complete (agg only).**
- **`na.drop("all")` drops rows where ALL columns are null.**
- **`approx_count_distinct` uses HyperLogLog++; avoids global distinct shuffle.**
- **Executor logs: Spark UI → Executors tab → click → stderr/stdout.**
- **`spark.sql.files.maxPartitionBytes = 128 MB` (read).**
- **Trigger `availableNow=True` over deprecated `once=True`.**

Good luck. You've put in the work.

---

## Companion quizzes

After this synthesis, take the full quiz set in `quizzes/`:
- [`01_architecture.md`](quizzes/01_architecture.md) — 27 Qs (20%)
- [`02_spark_sql.md`](quizzes/02_spark_sql.md) — 27 Qs (20%)
- [`03_dataframe_api.md`](quizzes/03_dataframe_api.md) — 40 Qs (30%)
- [`04_tuning.md`](quizzes/04_tuning.md) — 14 Qs (10%)
- [`05_streaming_connect_pandas.md`](quizzes/05_streaming_connect_pandas.md) — 27 Qs (20%)

Target 85%+ on each before booking.
