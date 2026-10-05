# Quiz 03 — Data Processing & Transformations (31%)

> Take cold. ~42 questions. ~2 min per question. Covers Structured Streaming, watermarks/state, Lakeflow Declarative Pipelines (LDP), expectations, APPLY CHANGES INTO.

---

## Recall

1. Which trigger replaced `Trigger.Once` as the recommended batch-style streaming trigger?
2. What are the three valid output modes for a Structured Streaming query?
3. Which option controls exactly-once semantics for a streaming write to Delta?
4. In Structured Streaming, which API declares the maximum lateness allowed for event-time data?
5. In an LDP SQL pipeline, what's the keyword to declare an incrementally-refreshed table from a streaming source?
6. In an LDP SQL pipeline, what's the keyword to declare a fully-recomputed table from a batch source?
7. What is the LDP SQL command that performs CDC upserts (replacing hand-rolled MERGE)?
8. Name the three `ON VIOLATION` actions for LDP expectations.
9. What is the default state store backend in newer DBR (post-DBR 13)?
10. What's the LDP equivalent of "SCD Type 1" (overwrite-in-place) vs "SCD Type 2" (history-preserving) in an `APPLY CHANGES INTO` statement?
11. What was Delta Live Tables (DLT) renamed to in July 2025?
12. Which LDP construct produces a row that violates an expectation but does NOT fail the pipeline and does NOT drop the row?
13. For a stream-stream join, on how many sides of the join is `withWatermark` required?

## Apply

14. You need to stream-process new files but the source has historical backlog of 5 million files. You want all data processed once, then the stream exits. Which trigger?
15. You want a long-running stream that emits a micro-batch every 30 seconds. Which trigger?
16. You're writing LDP SQL. You need a bronze table that incrementally ingests JSON files from `/Volumes/main/landing/orders`. Write the DDL.
17. You're writing LDP SQL. You need a gold table that recomputes total revenue per region on every run. STREAMING TABLE or MATERIALIZED VIEW?
18. You need CDC from a Bronze CDC feed into a Silver `customers` table with full history preserved. Which LDP construct + SCD type?
19. You want rows where `amount IS NULL` to be silently dropped from the Silver layer with a metric tracked. Write the LDP expectation.
20. You want rows where `customer_id IS NULL` to fail the whole pipeline immediately. Write the LDP expectation.
21. You want bad rows to be kept and visible in the table but logged as violations. Which `ON VIOLATION` action?
22. The team wants a quarantine pattern — bad rows routed to a separate table, good rows pass through. Sketch the approach in LDP.
23. You have a stream-stream join of clicks and impressions on `user_id` within a 10-minute window. Write the watermark + join condition outline.
24. A team wants exactly-once semantics for a streaming write to Delta. What two things must be set?
25. You need to read a CDC feed produced by a Lakeflow Connect ingestion. The feed has columns `op` (I/U/D), `ts`, and the business columns. Write the `APPLY CHANGES INTO` statement, ignoring deletes for now and storing as SCD1.
26. Same as Q25 but honor deletes: when `op = 'D'`, the row should be removed.
27. You want to use a tumbling 5-minute window aggregation on event time with 10-minute lateness tolerance. Sketch the PySpark.
28. An LDP pipeline references upstream LDP table `bronze_orders`. Inside the pipeline SQL, how do you reference it as a streaming source?
29. The team is migrating an old `@dlt.table` Python pipeline. Do they have to rewrite to `@dp.table` immediately? Why or why not?

## Diagnose

30. A streaming query was set with `.trigger(processingTime="1 hour")`. The team is paying for 24/7 compute. They expected the cluster to spin down between runs. Why didn't it?
31. A team's stream-stream join is producing no output even though both inputs have rows. Watermark is set on the click stream but not the impression stream. Why?
32. A team's LDP pipeline failed with "expectation violation" but they want the bad rows kept in the table and only logged. They have `ON VIOLATION FAIL UPDATE`. What's the fix?
33. A team is using hand-rolled `MERGE INTO` inside an LDP pipeline for CDC. It works but is brittle and re-implements features LDP already provides. What should they switch to?
34. Two structured streaming queries share the same `checkpointLocation`. State is mysteriously corrupted and queries restart from unexpected offsets. Why?
35. A stream is producing duplicates after a cluster restart. Checkpoint exists. What could be wrong?
36. An `APPLY CHANGES INTO ... SCD TYPE 2` target has too many history rows — every minor update creates a new version. The team only cares about a subset of columns triggering a new version. What option helps?
37. A team set `.trigger(once=True)` in their job. The exam reviewer marked it wrong. Why?
38. An LDP expectation `EXPECT (status IN ('OK','PENDING'))` is logged as failing on rows where status is `'ok'` lowercase. What's going on?

## Defend

39. Defend `APPLY CHANGES INTO` over hand-rolled `MERGE INTO` in an LDP pipeline.
40. Defend `availableNow` over `processingTime` for a nightly scheduled ingestion job.
41. Defend `MATERIALIZED VIEW` over `STREAMING TABLE` for a Gold layer aggregation that joins multiple Silver sources.
42. Defend keeping `ON VIOLATION DROP ROW` for `id IS NOT NULL` constraints but `ON VIOLATION FAIL UPDATE` for schema-shape violations like a totally missing column.

---

## Answers

1. **`.trigger(availableNow=True)`**. `Trigger.Once` is deprecated — `availableNow` is the modern replacement that handles backlogs by batching them into multiple micro-batches rather than trying to do it all in one. ⚠️ **Exam trap:** Any answer choice that uses `Trigger.Once` or `.trigger(once=True)` is now wrong by construction.
2. **`append`** (default; only new rows), **`complete`** (full state; requires aggregation), **`update`** (only changed rows).
3. **`checkpointLocation`** — exactly-once requires it to be set, unique per query, and persistent across restarts.
4. **`withWatermark("event_time_column", "<delay>")`** — declares the lateness threshold beyond which state can be evicted.
5. **`CREATE OR REFRESH STREAMING TABLE ...`** in LDP SQL.
6. **`CREATE OR REFRESH MATERIALIZED VIEW ...`** in LDP SQL.
7. **`APPLY CHANGES INTO ... FROM ... KEYS (...) SEQUENCE BY ... STORED AS SCD TYPE 1|2`** — a.k.a. AutoCDC.
8. **`DROP ROW`** (drop the offending row, keep pipeline running), **`FAIL UPDATE`** (fail the entire pipeline update), and the implicit "log only" action when no `ON VIOLATION` clause is specified (row is kept, violation is logged as a metric). ⚠️ **Exam trap:** Some sources call the log-only mode "WARN" colloquially, but the LDP SQL grammar has no `ON VIOLATION WARN` keyword — omitting `ON VIOLATION` is how you log-and-keep.
9. **RocksDB state store** — default in newer DBR; replaced the older HDFS-backed in-memory state store for better scaling on large state.
10. **`STORED AS SCD TYPE 1`** = overwrite latest row (no history). **`STORED AS SCD TYPE 2`** = preserve history with start/end timestamps. Both are clauses inside `APPLY CHANGES INTO`.
11. **Lakeflow Declarative Pipelines (LDP)**. ⚠️ **Exam trap:** The old `import dlt` syntax and `@dlt.table` decorator still work for backward compatibility — but exam answer choices prefer the new `pyspark.pipelines` Python API and `CREATE OR REFRESH STREAMING TABLE` SQL.
12. **An expectation declared without an `ON VIOLATION` clause** — e.g., `CONSTRAINT valid_status EXPECT (status IS NOT NULL)`. The row passes through, but the violation is counted in metrics.
13. **Both sides** — stream-stream joins require `withWatermark` on both DataFrames AND a time-range condition (often via interval join) so Spark knows when state can be evicted.
14. **`.trigger(availableNow=True)`** — handles the 5M-file backlog by chunking it into multiple micro-batches, then stops.
15. **`.trigger(processingTime="30 seconds")`** — keeps the stream running, firing a micro-batch every 30 seconds.
16. ```sql
    CREATE OR REFRESH STREAMING TABLE bronze_orders
      AS SELECT * FROM STREAM read_files('/Volumes/main/landing/orders', format => 'json');
    ```
17. **`MATERIALIZED VIEW`** — gold aggregations are typically full-refresh recomputations of batch data, not incremental. Use `STREAMING TABLE` only when you want strictly incremental processing and the upstream is itself streaming.
18. **`APPLY CHANGES INTO ... STORED AS SCD TYPE 2`**.
19. ```sql
    CONSTRAINT amount_present EXPECT (amount IS NOT NULL) ON VIOLATION DROP ROW
    ```
20. ```sql
    CONSTRAINT customer_required EXPECT (customer_id IS NOT NULL) ON VIOLATION FAIL UPDATE
    ```
21. **Omit the `ON VIOLATION` clause** (the implicit "log-only" mode). Row stays, violation counted in pipeline metrics.
22. Two streaming tables fed by the same Bronze: `silver_good` filters `WHERE quality_check_passes`, `silver_bad_quarantine` filters `WHERE NOT quality_check_passes`. Expectations can drive the filter columns.
23. ```python
    clicks_w   = clicks.withWatermark("click_ts", "10 minutes")
    impr_w    = impressions.withWatermark("impr_ts", "10 minutes")
    joined = clicks_w.join(
        impr_w,
        expr("clicks.user_id = impressions.user_id AND clicks.click_ts BETWEEN impressions.impr_ts AND impressions.impr_ts + interval 10 minutes")
    )
    ```
24. **(a) `checkpointLocation` set and unique** per query, and **(b) idempotent sink** (Delta is idempotent by design — it dedupes writes by batch id stored in the transaction log).
25. ```sql
    APPLY CHANGES INTO LIVE.silver_customers
    FROM STREAM(LIVE.bronze_customers_cdc)
    KEYS (customer_id)
    SEQUENCE BY ts
    COLUMNS * EXCEPT (op, ts)
    STORED AS SCD TYPE 1;
    ```
26. Add `APPLY AS DELETE WHEN op = 'D'` before `STORED AS SCD TYPE 1`.
27. ```python
    (df.withWatermark("event_time", "10 minutes")
       .groupBy(window("event_time", "5 minutes"), "user_id")
       .count())
    ```
28. **`STREAM(LIVE.bronze_orders)`** — `LIVE.` references another table in the same pipeline; `STREAM(...)` makes the read incremental.
29. **No, not immediately.** `@dlt.table` still works — full backward compatibility. New code should use `from pyspark import pipelines as dp` and `@dp.table` (or SQL). Migration is recommended but not forced. ⚠️ **Exam trap:** Exam answer choices generally prefer the new LDP form.
30. **`processingTime` keeps the stream running 24/7**, firing micro-batches on the cadence. For "run once an hour, terminate compute" the right pattern is a scheduled Lakeflow Job triggering a stream with `.trigger(availableNow=True)` — the job cluster spins up, processes, tears down.
31. **Stream-stream joins require watermarks on BOTH sides.** With only one side watermarked, Spark can't reason about when to evict state and may not emit results at all, or output is incomplete. Fix: add `withWatermark(...)` to the impressions stream and add a time-range constraint in the join.
32. **Change `ON VIOLATION FAIL UPDATE` to either `ON VIOLATION DROP ROW`** (if you want them excluded) **or remove the `ON VIOLATION` clause entirely** (if you want them kept and logged). ⚠️ **Exam trap:** `FAIL UPDATE` is rarely the right answer outside of critical schema-level invariants.
33. **`APPLY CHANGES INTO`** (AutoCDC). It handles SCD1/SCD2, sequencing, deletes, idempotency, and integrates with LDP's data quality framework — none of which a hand-rolled MERGE gives for free.
34. **Two queries cannot share a checkpoint.** Each writes batch metadata and offsets to the same files; they race and clobber each other's state. Fix: distinct `checkpointLocation` per query.
35. Possible causes: (a) checkpoint was deleted/moved between restarts, forcing a from-scratch reprocess; (b) the source isn't deterministic (e.g., a non-immutable file path that gets rewritten); (c) sink isn't idempotent (only an issue with non-Delta sinks). For Delta + checkpoint preserved + immutable source, exactly-once is guaranteed.
36. **`TRACK HISTORY ON (col1, col2, ...)`** clause in `APPLY CHANGES INTO ... STORED AS SCD TYPE 2` — only changes to listed columns create new history rows. Other column changes update in place.
37. **`Trigger.Once` (and equivalent `.trigger(once=True)`) is deprecated.** Use `.trigger(availableNow=True)` instead. ⚠️ **Exam trap:** Any answer that uses `Once` is wrong.
38. **`IN` is case-sensitive** for string literals in Spark SQL. `'ok'` ≠ `'OK'`. Fix: normalize with `upper(status) IN ('OK','PENDING')` or include lowercase variants.
39. **`APPLY CHANGES INTO`:** declarative, handles SCD1/SCD2, sequencing, deletes, out-of-order events, idempotency, and integrates with expectations. Hand-rolled `MERGE` re-implements all of these (often with bugs) and doesn't compose with LDP's lifecycle. Inside LDP, default to `APPLY CHANGES INTO`. Reserve `MERGE` for non-LDP Delta tables when you need full DML control.
40. **`availableNow`:** processes everything new since last checkpoint then exits, so the job cluster can terminate — pay for compute only while data is being processed. **`processingTime`:** keeps the stream alive and pays for compute 24/7 even when there's no data. For nightly scheduled work, `availableNow` is dramatically cheaper.
41. **MATERIALIZED VIEW** is fully recomputed on each refresh — perfect for Gold-layer joins over Silver state that may itself have been updated (CDC restating history). **STREAMING TABLE** is strictly incremental and assumes append-only / monotonic upstream. Using STREAMING TABLE on a source that gets back-restated produces wrong results.
42. **`DROP ROW`** is the right answer when a single bad row is benign and the pipeline should keep running with the remaining good rows (`id IS NOT NULL` — a few null IDs are operationally tolerable). **`FAIL UPDATE`** is the right answer when the violation indicates the contract itself is broken (missing column means upstream schema regressed — running on bad data is worse than halting). Match severity to action.
