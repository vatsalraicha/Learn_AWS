# Quiz 01 — Architecture, DAG, Execution Model

> 27 questions covering Domain 1 (20% — ~9 questions on the real exam, scaled to 27 for practice).
> Topics: cluster topology, driver/executor, lazy evaluation, transformations vs actions, narrow vs wide, DAG, stages, tasks, deployment modes.

---

## Recall

1. Which Spark component holds the DAG and schedules tasks?
2. How many tasks run in a stage with 80 partitions?
3. What's the default value of `spark.sql.shuffle.partitions`?
4. Name the three deployment modes.
5. In local mode, where do executors run?
6. Is `union` a narrow or wide transformation?
7. Is `df.coalesce(10)` narrow or wide?
8. What's the default storage level for DataFrame `.cache()`?
9. What's the default storage level for RDD `.cache()`?
10. Name the three cluster managers Spark 3.5 supports (excluding the deprecated one).
11. What's the unit of execution Spark schedules onto an executor core?
12. Which API replaces `SparkContext`, `SQLContext`, and `HiveContext` as the unified entry point?

## Apply

13. You have 8 executors with 4 cores each. What's the total parallelism?
14. A DataFrame has 200 partitions and your cluster has 20 cores. How many "waves" of task execution?
15. Given:
    ```python
    df = spark.read.parquet("path")
    df = df.filter("year=2025")
    df = df.groupBy("region").count()
    df.show(10)
    ```
    How many jobs does this trigger? How many stages?
16. Given a DataFrame with 100 partitions, you call `df.repartition(50)`. Is this wide or narrow? Is the result balanced?
17. You call `df.coalesce(500)` on a 200-partition DataFrame. How many partitions does the result have?
18. Which method is preferred for reducing partitions without shuffling: `coalesce` or `repartition`?

## Diagnose

19. Your job has a stage with 10,000 tasks, each processing 1 MB. Most tasks finish in ~50ms. Diagnosis?
20. Your driver runs out of memory after calling `df.collect()` on a 5 GB DataFrame. What's the fix?
21. One task in a 200-task stage runs 15 minutes; others finish in ~30 seconds. Diagnosis and fix?
22. Spark UI shows "Spill (Disk): 4 GB" for a stage. What does this mean and how do you address it?

## Defend

23. When would you choose **cluster mode** over **client mode** for a Spark job?
24. Why is **lazy evaluation** preferable to eager evaluation in distributed processing?
25. Defend or refute: "`union` shuffles data because it merges two tables."
26. Why is `df.cache()` insufficient on its own to trigger caching?
27. When would you set `spark.task.maxFailures` higher than the default 4?

---

## Answers

1. **Driver.** It hosts SparkSession, builds the DAG, schedules tasks, and collects results.

2. **80 tasks** — one task per partition per stage.

3. **200.**

4. **Client, Cluster, Local.**

5. **In the same JVM as the driver** — all threads in one process. The local machine acts as the "single worker node."

6. **Narrow.** Union concatenates partitions; no shuffle.

7. **Narrow.** Combines partitions on the same executor; no shuffle.

8. **`MEMORY_AND_DISK`.**

9. **`MEMORY_ONLY`** — asymmetric default vs DataFrame.

10. **Standalone, YARN, Kubernetes.** (Mesos deprecated.)

11. **Task** — runs on one executor core, processes one partition.

12. **`SparkSession`.**

13. **32** (8 × 4 = 32 concurrent tasks).

14. **10 waves** (200 / 20 = 10).

15. **1 job** (one action: `show`); **2 stages** (one shuffle boundary at the groupBy).

16. **Wide** (full shuffle); **yes**, the result is balanced (round-robin partitioning).

17. **200 partitions.** `coalesce` cannot INCREASE partition count — only decrease.

18. **`coalesce`** — narrow, no shuffle. Only valid for decreasing.

19. **Under-parallelism with overhead-dominated tasks.** Per-task overhead (~10-50ms scheduling) dominates over actual work. Fix: `coalesce(N)` to fewer, larger tasks (~100 MB each).

20. **`.collect()` materializes everything in driver heap.** Use `.show(20)`, `.take(n)`, write to storage, or `df.limit(N).toPandas()`. If you must collect, increase `spark.driver.memory` and `spark.driver.maxResultSize` — but better not to.

21. **Data skew.** One partition has a much larger value distribution. Fix: enable AQE skew join (default in 3.5+); if not sufficient, salt the join key.

22. **Memory pressure during sort/aggregation/hash-join.** Sort or hash table exceeded available execution memory and spilled to local disk. Fixes: increase executor memory; more shuffle partitions (smaller per-task data); pre-aggregate before the wide step.

23. **Production batch jobs.** Driver lives on a worker node — submitting machine can disconnect after submission, driver-executor RPC stays in-cluster (lower latency). Client mode is for interactive use (notebooks, REPL).

24. Lazy evaluation lets Spark **combine consecutive transformations** into a single pipeline, **push filters down** to the source (predicate pushdown), **prune columns** unused by the query (projection pruning), and **reorder operations** for cost. Eager evaluation would force materialization after every line.

25. **Refute.** Union is narrow — it concatenates partitions, no shuffle. It's NOT analogous to a join. The shuffle that some people associate with union actually comes from a follow-up `.distinct()` (if you want SQL UNION dedup semantics).

26. `cache()` is a **transformation** — it marks the DataFrame for caching but doesn't execute. The cache is populated only when the first action triggers computation. Without an action (`.count()`, `.show()`, etc.), nothing happens.

27. **Spot/preemptible instances** where node-level failures are common; tasks may need more retries before declaring true failure. Also for jobs that interact with flaky external services where transient errors are expected.
