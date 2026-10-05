# Module 09 — Watermarks & Stateful Streaming

> **Domain 3 (31%) — Data Processing & Transformations**
>
> **What you must walk away with:** What watermarks do (bound state). The `withWatermark(col, threshold)` syntax. Stream-stream joins require watermarks on BOTH sides. Late-data behavior. CDC handling via Auto Loader / APPLY CHANGES INTO. State stores (RocksDB vs HDFS).

---

## Coverage map (verbatim July 25, 2025 objectives → where taught here)

| Verbatim objective | Taught in section |
|---|---|
| Implement data pipelines (stateful streaming foundation for LDP) | §2 watermark contract; §3 windowed aggregations; §4 stream-stream joins; §5 dedup; §9 stateful ops cheat-sheet |
| Classify cluster/configuration for stateful workloads | §7 "State stores" (RocksDB vs HDFS) + §6 late-data tuning |
| Use debugging tools (late-data drops, state metrics) | §6 "Late data behavior" (numRowsDroppedByWatermark) |
| Identify DDL/DML features for CDC | §8 "CDC handling — three patterns" (Auto Loader CDC files, Lakeflow Connect, CDF reader) |

Cross-references: Module 03 for `delta.enableChangeDataFeed` and `table_changes`; Module 10 for `APPLY CHANGES INTO` (the LDP-canonical CDC path).

---

## 1. Why state is the hard part of streaming

A stateless transformation (filter, projection, join with a static table) is easy — each row is processed in isolation. A **stateful** transformation needs to remember information across rows:

- `groupBy(col).agg(sum(...))` — must remember running sums per group.
- `dropDuplicates(keys)` — must remember keys seen so far.
- `df1.join(df2, ...)` where both are streams — must remember rows from each side until a match appears.
- Window aggregations (`window(col, "10 minutes")`) — must remember rows until the window closes.

Without bounds, the state grows forever. With bounds, you risk dropping data that arrived late. **Watermarks** are the mechanism for declaring those bounds.

---

## 2. Watermarks — the contract

A watermark is a **promise to the engine** of the form:
> "I assert that no row will arrive with `event_time` more than N minutes earlier than the latest event_time I've seen."

```python
df_with_wm = df.withWatermark("event_time", "10 minutes")
```

Semantics:
- The engine tracks the **maximum `event_time` observed** across all rows seen so far.
- The current watermark = `max_event_time - threshold` (e.g., 10 minutes).
- State for windows / groups whose end-time is below the watermark can be **dropped** — safely, because no row earlier than that should appear.
- Rows that arrive **later than the watermark** are dropped silently (they're "late data").

```mermaid
gantt
    title Watermark example (10-minute threshold)
    dateFormat HH:mm
    axisFormat %H:%M
    section Arrived rows
    row at event_time 10:00 :done, 10:00, 1m
    row at event_time 10:08 :done, 10:08, 1m
    row at event_time 10:15 :done, 10:15, 1m
    row at event_time 10:00 (late, dropped) :crit, 10:16, 1m
    section Watermark
    watermark = 10:00 - 10:00 :active, 10:00, 8m
    watermark = 10:08 - 10:00 :active, 10:08, 7m
    watermark = 10:15 - 10:05 :active, 10:15, 1m
```

When event_time hits 10:15, the watermark = 10:05. Any row with event_time < 10:05 arriving afterward is dropped.

### `withWatermark` syntax

```python
df.withWatermark("event_time_col", "10 minutes")
df.withWatermark("event_time_col", "30 seconds")
df.withWatermark("event_time_col", "1 hour")
```

- The first argument is the **event-time column** (must be `TimestampType`).
- The second is the **threshold** (Spark interval string).

---

## 3. Windowed aggregations

```python
from pyspark.sql.functions import window, sum, count_distinct

# 10-minute tumbling window, watermark = 5 minutes late
windowed = (df_stream
    .withWatermark("event_time", "5 minutes")
    .groupBy(
        window("event_time", "10 minutes"),
        "customer_id"
    )
    .agg(sum("amount").alias("total"), count_distinct("order_id").alias("orders")))
```

Window types:
- **Tumbling** — `window("event_time", "10 minutes")` — fixed, non-overlapping.
- **Sliding** — `window("event_time", "10 minutes", "5 minutes")` — overlapping (slides every 5 min).
- **Session** — `session_window("event_time", "30 minutes")` — variable size based on activity gap.

A window's state can be dropped only when the watermark passes the window's end + threshold.

### Output mode for windowed aggregations

- **`append`** — emit each window's row **once, when it's finalized** (watermark crosses end). Latency = window size + watermark threshold.
- **`update`** — emit each window's row whenever it changes. Lower latency, but more sink writes.
- **`complete`** — emit the entire result table on each batch. Heavy memory.

### ⚠️ Exam trap — append + windowed aggregation

Append mode + windowed aggregation **does not emit a window's row until the watermark crosses the end.** If you set a 1-hour window with a 10-minute watermark, results are 1h10m delayed. Use `update` mode for lower latency or accept the lag.

---

## 4. Stream-stream joins — watermarks on BOTH sides

Joining two streams requires bounding state on both sides:

```python
clicks_wm  = clicks.withWatermark("click_time", "1 hour")
purchases_wm = purchases.withWatermark("purchase_time", "30 minutes")

joined = (clicks_wm.join(
    purchases_wm,
    expr("""
        clicks_wm.user_id = purchases_wm.user_id
        AND purchases_wm.purchase_time BETWEEN clicks_wm.click_time AND clicks_wm.click_time + INTERVAL 2 HOURS
    """),
    "inner"
))
```

Requirements:
- **Watermark on both DataFrames.**
- **A time-range condition in the join predicate** (`BETWEEN`, `<`, `<=` involving the event-time columns).

Without both, the join state grows unbounded — the engine refuses to compile such a join.

### Outer joins

- **Left outer / right outer** with watermarks — emit the outer side row with NULLs on the inner side **once the watermark on the outer side advances past the join's time window**. Latency = watermark threshold.
- **Full outer** — supported but rarely used in production streaming.

### ⚠️ Exam trap — "stream-stream join without watermark"

If a question shows a stream-stream join code with no `withWatermark` and asks why it doesn't work — the answer is "missing watermarks; state is unbounded; Spark errors at planning time."

---

## 5. Deduplication with watermarks

```python
dedup = (df_stream
    .withWatermark("event_time", "1 hour")
    .dropDuplicates(["user_id", "event_id"]))
```

The engine remembers seen `(user_id, event_id)` pairs only as long as the watermark hasn't passed their event_time + threshold. Without a watermark, dedup remembers everything forever — eventually OOM.

---

## 6. Late data behavior

Rows arriving later than the watermark are **silently dropped** by stateful operations. The dropped count is exposed in the streaming progress metrics:

```
"watermark": "2026-05-23T10:05:00Z",
"stateOperators": [{
    "operatorName": "stateStoreSave",
    "numRowsDroppedByWatermark": 42
}]
```

If you can't afford to drop late data, options are:
1. **Increase the watermark threshold** — `withWatermark("event_time", "1 day")`. Costs more state memory.
2. **Process late data separately** in a downstream job that reads CDF from the main output.
3. **Use `update` mode** so a row can be re-emitted if a late update arrives within the watermark window.

---

## 7. State stores

The streaming engine stores state somewhere. Two implementations:

### 7.1 HDFS-backed state store (legacy default)

- State held in JVM heap.
- Spills to disk via HDFS API (sounds odd, but the API is HDFS-style regardless of underlying FS).
- Limited by executor memory.

### 7.2 RocksDB state store (newer default on DBR)

```python
spark.conf.set("spark.sql.streaming.stateStore.providerClass",
               "com.databricks.sql.streaming.state.RocksDBStateStoreProvider")
```

- State held in a RocksDB embedded LSM tree.
- Spills to local SSD efficiently.
- Handles much larger state (10s of GB per executor) before OOM.
- Higher per-row latency than in-heap, but scales further.

On newer DBR / serverless, **RocksDB is the default** and you typically don't configure this.

### ⚠️ Exam trap — RocksDB vs HDFS state store

The exam mostly tests "RocksDB exists, it's the default on newer DBR, it handles larger state." Don't get into byte-level config — that's beyond DE Associate scope.

---

## 8. CDC handling — three patterns

The exam doesn't deeply test CDC, but it tests recognition of the three approaches.

### 8.1 Read CDC events via Auto Loader from CDC-emitted files

A source system (Debezium, AWS DMS, Azure Data Factory) writes CDC events to object storage. Auto Loader reads them as JSON/Avro/Parquet files. Downstream MERGE / APPLY CHANGES INTO upserts to a target.

### 8.2 Read CDC events via Lakeflow Connect

Lakeflow Connect's SQL Server / Postgres / MySQL connectors handle CDC natively. The Bronze table is automatically maintained as a row-level mirror.

### 8.3 Read Change Data Feed from a Delta table

If the upstream is a Delta table with `delta.enableChangeDataFeed = true`, downstream consumers can read changes with:

```sql
SELECT * FROM table_changes('main.silver.orders', 42, 100);
```

The CDF rows include `_change_type` ∈ {`insert`, `update_preimage`, `update_postimage`, `delete`}.

### Downstream CDC application

Once CDC events arrive, you upsert them:

**Outside LDP** — `foreachBatch` + MERGE.

```python
def apply_cdc(batch_df, batch_id):
    # Latest event per key only
    from pyspark.sql.window import Window
    from pyspark.sql.functions import row_number, col
    latest = (batch_df
        .withColumn("rn", row_number().over(Window.partitionBy("id").orderBy(col("ts").desc())))
        .filter("rn = 1")
        .drop("rn"))
    latest.createOrReplaceTempView("updates")
    spark.sql("""
        MERGE INTO main.silver.customers t
        USING updates s
        ON t.id = s.id
        WHEN MATCHED AND s.op = 'D' THEN DELETE
        WHEN MATCHED AND s.op = 'U' THEN UPDATE SET *
        WHEN NOT MATCHED AND s.op = 'I' THEN INSERT *
    """)

cdc_stream.writeStream.foreachBatch(apply_cdc).option("checkpointLocation", "...").start()
```

**Inside LDP** — `APPLY CHANGES INTO` (Module 10).

```sql
APPLY CHANGES INTO LIVE.customers
FROM STREAM(LIVE.cdc_events)
KEYS (id)
APPLY AS DELETE WHEN op = 'D'
SEQUENCE BY ts
STORED AS SCD TYPE 1;
```

---

## 9. Stateful operations cheat-sheet

| Operation | State held | Bound by |
|-----------|-----------|----------|
| `groupBy(...).agg(...)` | Running aggregate per group | Watermark (if used) |
| `dropDuplicates(keys)` | Seen keys | Watermark on event-time column |
| Stream-stream join | Buffered rows from both sides | Watermarks on both sides + time-range condition |
| Windowed aggregation | Per-window running aggregate | Watermark + window-end |
| `mapGroupsWithState` / `flatMapGroupsWithState` | Custom per-key state | Programmer-defined (`GroupStateTimeout`) |

### Without watermarks

- Aggregations work but state grows unbounded → eventually fail.
- Stream-stream join → planner error.
- Dedup → unbounded memory.

---

## 10. Mini quiz (cold)

1. What does `withWatermark("event_time", "10 minutes")` declare to the engine?
2. A row arrives with event_time 30 minutes before the current watermark. What happens to it?
3. Can you do a stream-stream join without watermarks?
4. A windowed aggregation in `append` mode with 1-hour windows and a 10-minute watermark. How long after window end does a result appear?
5. The exam shows `df1.join(df2, "key")` where both are streams. What's missing?
6. Which state store is the default on newer DBR — HDFS or RocksDB?
7. To handle CDC inside an LDP pipeline, do you write MERGE or APPLY CHANGES INTO?
8. To enable CDF on a Delta table, what property do you set?

### Answers

1. **"No row will arrive with event_time more than 10 minutes earlier than the latest event_time seen."** This bounds the engine's state.
2. **Dropped silently** (counted in `numRowsDroppedByWatermark`).
3. **No.** Stream-stream joins require watermarks on both sides plus a time-range join condition.
4. **About 1h10m** — the window closes at end + watermark threshold.
5. **Both watermarks AND a time-range condition.** `df1.withWatermark(...)` and `df2.withWatermark(...)` on event-time columns plus `df1.event_time BETWEEN df2.event_time - INTERVAL X AND df2.event_time + INTERVAL Y` in the join expression.
6. **RocksDB** — default on newer DBR.
7. **`APPLY CHANGES INTO`** — the LDP-canonical form.
8. **`delta.enableChangeDataFeed = true`**.

---

## 11. Sanity check before moving on

You should be able to:
- Define a watermark in one sentence.
- State the two requirements for a stream-stream join (watermarks on both + time-range condition).
- Pick `RocksDB` as the modern default state store.
- Choose APPLY CHANGES INTO over MERGE inside an LDP pipeline.

If any of those are fuzzy, re-read Sections 2, 4, and 8.
