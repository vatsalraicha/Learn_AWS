# Quiz 05 — Structured Streaming + Spark Connect + Pandas API on Spark

> 27 questions covering Domains 5+6+7 (10%+5%+5% = 20% — ~9 questions on the real exam, scaled to 27 for practice).
> Split: ~14 streaming, ~7 Spark Connect, ~6 Pandas API on Spark.
> Topics: `readStream`/`writeStream`, triggers (default, `processingTime`, `availableNow`), output modes (`append`/`complete`/`update`), `checkpointLocation`, watermarks, `dropDuplicates`, `foreachBatch`, exactly-once semantics; Spark Connect architecture (gRPC, thin client, restrictions), deployment modes (client/cluster/local); `pyspark.pandas` (`ps`), interop, semantic differences vs real pandas.

---

## Recall

### Structured Streaming
1. Which method initiates a streaming read?
2. Name the three output modes.
3. Which output mode is the default when none is specified?
4. What configuration option is REQUIRED for exactly-once fault tolerance?
5. What does `withWatermark("event_time", "10 minutes")` do?
6. Which trigger type processes all available data, then stops?

### Spark Connect
7. What protocol does Spark Connect use between client and server?
8. Which `SparkSession` builder method connects to a remote Spark Connect server?
9. Name the three deployment modes Spark supports.

### Pandas API on Spark
10. What is the standard import alias for the Pandas API on Spark?
11. Which method converts a `pyspark.pandas` DataFrame to a real pandas DataFrame (collecting to the driver)?
12. Which method converts a `pyspark.pandas` DataFrame to a PySpark `DataFrame` (no data movement)?

## Apply

### Structured Streaming
13. Write a streaming pipeline reading from Kafka topic `events`, grouping by `userId`, counting, and writing to console with complete output mode and a 2-minute trigger.
14. Write a streaming dedup using a 30-minute watermark on column `ts` and key column `event_id`.
15. Write a streaming pipeline that uses `foreachBatch` to write each micro-batch to a Delta table at `/delta/users`.

### Spark Connect
16. Connect to a Spark Connect server at host `spark.internal` port `15002`.
17. A colleague tries `sc.broadcast(my_dict)` in a Spark Connect session and gets an error. Why?

### Pandas API on Spark
18. Read `s3://bucket/data.csv` using the Pandas API on Spark.
19. Filter a Pandas-on-Spark DataFrame `psdf` to rows where `salary > 100000` and group by `dept` to compute mean salary.
20. Convert a regular pandas DataFrame `pdf` (already in driver memory) into a Pandas-on-Spark DataFrame.

## Diagnose

### Structured Streaming
21. A streaming aggregation with `outputMode("append")` and no watermark produces no output. Diagnosis?
22. A user runs a streaming job for an hour, kills it, restarts it pointing at the same `checkpointLocation`. The job replays the entire history from the source. Why?

### Spark Connect
23. Code that works in a normal PySpark session fails with `AttributeError` in a Spark Connect session when accessing `spark.sparkContext.parallelize(...)`. Why?

### Pandas API on Spark
24. A pandas user expects `psdf.iloc[0]` to be cheap (single-row lookup). In Pandas-on-Spark it triggers a job and shuffles. Why?

## Defend

25. Defend or refute: "`outputMode("complete")` is always safe because it emits the full result table."
26. Defend or refute: "Spark Connect adds latency, so it's always slower than a co-located driver."
27. Defend or refute: "Pandas API on Spark is just a thin wrapper — code written for pandas runs unchanged."

---

## Answers

### Structured Streaming

1. **`spark.readStream`.** Returns a streaming DataFrame. Symmetric: `df.writeStream` starts a stream sink.

2. **`append`**, **`complete`**, **`update`**.
    - `append`: only newly added rows (no aggregations OR with watermark closing groups).
    - `complete`: full result table re-emitted each trigger (aggregations only; state grows with cardinality).
    - `update`: rows that changed since last trigger (most aggregations).

3. **`append`** is the default for non-aggregating streaming queries. For aggregating queries without a watermark, `append` may produce no output — see Q21.

4. **`checkpointLocation`.** Required for exactly-once. Stores offsets, query progress, and (for stateful queries) state store. Without it, fault tolerance degrades to at-least-once at best. **Sample question pattern** in the official guide tests this.

5. **Declares that records older than `(max(event_time) - 10 min)` may be dropped from state.** Bounds the state store; allows `append` mode for windowed aggregations (the window can be considered "finalized" once watermark passes its end).

6. **`AvailableNow`** — `.trigger(availableNow=True)`. Processes all unprocessed data in micro-batches then exits. Replaces deprecated `Trigger.Once` (which processed everything in ONE batch — `AvailableNow` splits into multiple bounded batches for memory safety).

### Spark Connect

7. **gRPC** (over HTTP/2). The client serializes unresolved logical plans to protobuf; the server resolves, optimizes, and executes.

8. **`SparkSession.builder.remote("sc://host:port").getOrCreate()`.** The `sc://` scheme tells the builder to use the Spark Connect client.

9. **Client, Cluster, Local.**
    - **Client mode**: driver runs on the submitting machine (laptop, edge node).
    - **Cluster mode**: driver runs on a worker node inside the cluster.
    - **Local mode**: driver + all executors as threads in a single JVM on the local machine.
    Sample question #7 in the official guide tests recognition of local-mode as "all executors on a single worker node."

### Pandas API on Spark

10. **`import pyspark.pandas as ps`.** (NOT `import koalas` — Koalas was the old project name; merged into PySpark as `pyspark.pandas` in Spark 3.2.)

11. **`.to_pandas()`** — collects all rows to the driver and returns a real `pandas.DataFrame`. **Trap:** can OOM the driver on large data; equivalent to `.collect().toPandas()` in PySpark land.

12. **`.to_spark()`** — returns the underlying PySpark `DataFrame`. No data movement (it was already a Spark DataFrame internally). Use this when you need PySpark-specific APIs.

### Apply

13. ```python
    stream = (spark.readStream
              .format("kafka")
              .option("kafka.bootstrap.servers", "broker:9092")
              .option("subscribe", "events")
              .load())

    query = (stream.groupBy("userId").count()
             .writeStream
             .outputMode("complete")
             .format("console")
             .trigger(processingTime="2 minutes")
             .option("checkpointLocation", "/chk/events")
             .start())
    ```

14. ```python
    deduped = (stream
        .withWatermark("ts", "30 minutes")
        .dropDuplicates(["event_id", "ts"]))
    ```
    With watermark, state is bounded (events older than 30 minutes past max watermark are evicted). WITHOUT watermark, `dropDuplicates` keeps state unbounded — a production hazard.

15. ```python
    def write_batch(batch_df, batch_id):
        batch_df.write.format("delta").mode("append").save("/delta/users")

    query = (stream.writeStream
             .foreachBatch(write_batch)
             .option("checkpointLocation", "/chk/users")
             .start())
    ```
    `foreachBatch` gives you a regular DataFrame per micro-batch — full API access (joins to static tables, multi-sink writes, MERGE).

16. ```python
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.remote("sc://spark.internal:15002").getOrCreate()
    ```

17. **Spark Connect does NOT support `SparkContext`-side broadcast variables.** Spark Connect clients work only with the high-level DataFrame/SQL API; there is no `sparkContext.broadcast()`, no `sparkContext.parallelize()`, no RDD API at all from the client. Use `F.broadcast(df)` (the join hint, which IS supported) instead.

18. ```python
    import pyspark.pandas as ps
    psdf = ps.read_csv("s3://bucket/data.csv")
    ```

19. ```python
    psdf[psdf["salary"] > 100000].groupby("dept")["salary"].mean()
    ```

20. ```python
    psdf = ps.from_pandas(pdf)
    ```

### Diagnose

21. **Without a watermark, Spark can never finalize a window — so `append` mode (which only emits finalized state) outputs nothing.** Fix: either switch to `outputMode("update")` or `outputMode("complete")`, OR add `withWatermark("event_time", "X minutes")` to bound the state and allow `append`.

22. **`checkpointLocation` mismatch or path was wiped.** Possible causes: (a) ran the new job with a different checkpoint path, (b) the underlying storage path was cleared, (c) the query ID changed (e.g., a different output sink format changes the query signature). Spark uses the checkpoint to read its last committed offset; if absent, it starts from the source's default starting position (Kafka: earliest or latest depending on config).

23. **Spark Connect doesn't expose `sparkContext`.** The client has only a `SparkSession`. `spark.sparkContext` raises because there's no JVM SparkContext on the client side — the server holds it. Code referencing RDD APIs, broadcast variables, accumulators, or `parallelize` will fail. Migrate to DataFrame-only equivalents.

24. **Pandas-on-Spark is distributed.** `iloc[0]` requires knowing the global row order, which means a shuffle to enforce an Index. Pandas-on-Spark uses a "default Index" (often computed lazily) that requires a job to materialize. **Best practice:** avoid positional indexing; use `.head(n)`, `.first()`, or filter by column values. Also: pandas-on-Spark Index behavior is configurable via `compute.default_index_type` (e.g., `distributed-sequence`, `sequence`).

### Defend

25. **Refute.** `outputMode("complete")` re-emits the FULL result table each trigger. For an aggregation with growing cardinality (e.g., COUNT BY user_id where users keep arriving), state grows unbounded and the sink receives ever-larger writes. Safe for SMALL result sets (e.g., counts per region); dangerous at scale. Pair with watermarks + `append` mode whenever possible.

26. **Refute.** For interactive workloads, Spark Connect can REDUCE perceived latency: the gRPC round-trip is amortized across many lazy operations (only the final action serializes the full plan), and the client doesn't need to spin up a JVM driver. For one-shot batch jobs, classic submission may be marginally faster on launch but identical at steady state — execution happens on the cluster either way. Don't pick architecture on launch latency alone.

27. **Refute.** Pandas-on-Spark has documented behavioral differences:
    - No in-place mutation by default (set `compute.ops_on_diff_frames` for some ops).
    - Default Index types differ (`sequence`, `distributed`, `distributed-sequence`) with different cost models.
    - Some operations are eager in pandas but lazy in Spark.
    - Sort stability and NaN handling can differ.
    - Not all pandas APIs are implemented (`apply` with non-vectorizable functions, some date offsets).
    Treat it as a *pandas-flavored* API on Spark, not literal pandas compatibility.
