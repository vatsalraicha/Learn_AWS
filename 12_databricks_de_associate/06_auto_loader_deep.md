# Module 06 — Auto Loader Deep Dive: cloudFiles, schema evolution, hints, triggers

> **Domain 2 (30%) — Development and Ingestion**
>
> **Exam objectives covered:**
> - Classify valid Auto Loader sources and use cases.
> - **Demonstrate knowledge of Auto Loader syntax.** ← highest-yield in this domain
>
> **What you must walk away with:** Every Auto Loader option that shows up in exam code. The four schema-evolution modes and which is default in which case. The two file-detection modes. The `_rescued_data` column. The `schemaLocation` requirement. Trigger choices. The interaction with LDP via `STREAM read_files(...)`.

---

## Coverage map (verbatim July 25, 2025 objectives → where taught here)

| Verbatim objective | Taught in section |
|---|---|
| Classify valid Auto Loader sources and use cases | §2 "`cloudFiles.format` — supported source formats" + §7 "File detection modes" |
| Demonstrate knowledge of Auto Loader syntax | §1 query shape; §3 schemaLocation; §4 schema inference; §5 schemaHints; §6 schemaEvolutionMode (4 modes + defaults); §8 triggers; §9 checkpointLocation; §10 `.toTable`; §11 full example; §12 LDP SQL form |

Cross-references: Module 05 for COPY INTO vs Auto Loader trade-offs; Module 08 for trigger semantics and checkpointing; Module 10 for `STREAM read_files` inside LDP.

---

## 1. The shape of an Auto Loader query

```python
df = (spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.schemaLocation", "/Volumes/main/_schemas/orders")
        .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
        .load("/Volumes/main/landing/orders/"))

(df.writeStream
   .option("checkpointLocation", "/Volumes/main/_chk/orders")
   .trigger(availableNow=True)
   .toTable("main.bronze.orders"))
```

Three groups of options:
1. **Source options** (`.format("cloudFiles")` + `cloudFiles.*` options) — what to read, how to infer schema, how to detect new files.
2. **Sink options** (`.option("checkpointLocation", …)`, `.trigger(...)`) — where to write, how often, how durably.
3. **The `.toTable(...)` sink** — the simplest sink for Delta in UC.

---

## 2. `cloudFiles.format` — supported source formats

```python
.option("cloudFiles.format", "json")
```

Supported values: `json`, `csv`, `parquet`, `avro`, `orc`, `text`, `binaryFile`.

| Format | Notes |
|--------|-------|
| `json` | Default schema-inference target |
| `csv` | Add `header`, `delimiter`, `multiLine` as needed |
| `parquet` | Schema is in the file; less need for schema hints |
| `avro` | Avro schema is in the file |
| `orc` | Less common |
| `text` | One column `value` STRING per line |
| `binaryFile` | One row per file with `path`, `modificationTime`, `length`, `content BINARY` |

---

## 3. `cloudFiles.schemaLocation` — REQUIRED for inference

```python
.option("cloudFiles.schemaLocation", "/Volumes/main/_schemas/orders")
```

If you're letting Auto Loader **infer** the schema (the common case for JSON / CSV), you **must** provide a schemaLocation. Without it, the query errors.

What's stored at this path:
- `_schemas/` subdirectory holding versioned schema snapshots.
- Each schema-evolution event creates a new schema version.

If you provide a schema directly (`.schema(struct_type)`), the schemaLocation is optional — but it's still recommended for tracking.

```python
# Schema provided directly — schemaLocation optional but recommended
schema = StructType([
    StructField("order_id", StringType()),
    StructField("amount", DecimalType(18, 2)),
    StructField("ts", TimestampType())
])

df = (spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .schema(schema)
        .load("/Volumes/main/landing/orders/"))
```

### ⚠️ Exam trap — schemaLocation is required for inference

If you don't provide a schema and you don't provide `cloudFiles.schemaLocation`, the query won't start. An exam question with a code snippet missing schemaLocation but inferring the schema is broken — likely a distractor.

---

## 4. Schema inference details

Auto Loader samples files to infer the schema:

- **First 50 GB OR first 1000 files**, whichever comes first.
- Tuned via `cloudFiles.schemaInferenceParallelism` and `cloudFiles.schemaInferenceSizeMB` for very large folders.
- Sampling happens at **query start** and on **schema-evolution events**.

By default, **all columns are inferred as STRING** for JSON / CSV (preserves precision; avoids accidental type narrowing). To enable type inference:

```python
.option("cloudFiles.inferColumnTypes", "true")
```

This option doesn't affect schema hints — hints always take effect.

---

## 5. Schema hints — explicit type overrides

```python
.option("cloudFiles.schemaHints", "order_id LONG, amount DECIMAL(18,2), ts TIMESTAMP")
```

- Comma-separated list of `col_name TYPE` pairs.
- Hints are applied **on top of** inference. Columns not in the hints are inferred normally.
- Hints work whether `inferColumnTypes` is on or off.
- Use to force a column to a specific type without writing the entire schema.

**Use case:** JSON files have an `amount` field that's sometimes a number, sometimes a quoted string. Without a hint, Auto Loader might pick STRING and you'd cast downstream. With `schemaHints = "amount DECIMAL(18,2)"`, Auto Loader parses it as decimal from the start.

### ⚠️ Exam trap — schema hints vs full schema

- **Hints** = partial overrides; Auto Loader still infers other columns.
- **Full schema (`.schema(...)`)** = explicit; no inference happens. Default schema-evolution mode in this case is `none`.

---

## 6. Schema evolution modes — the highest-frequency trap

`cloudFiles.schemaEvolutionMode` controls what happens when a new file arrives with a column the schema doesn't know about.

Five values, but you really memorize four:

| Mode | Behavior on new column | Default when |
|------|-----------------------|--------------|
| `addNewColumns` | **Restart the stream** with the new schema; new column added | **No schema provided** (inference case) |
| `rescue` | Place unknown columns in the `_rescued_data` JSON column; **no restart**, **no failure** | — (must be set explicitly) |
| `failOnNewColumns` | **Fail the stream** | — (set explicitly when you want strict schema control) |
| `none` | Silently ignore new columns | **Schema provided directly via `.schema(...)`** |
| `addNewColumnsWithTypeWidening` | Like `addNewColumns` but also widens int→long, float→double on type drift | Newer DBR (table feature dependent) |

### Defaults — MEMORIZE

| Schema source | Default mode |
|---------------|--------------|
| No schema provided (Auto Loader infers) | **`addNewColumns`** |
| Schema provided directly via `.schema(...)` | **`none`** |
| Schema hints used (no full schema) | Still `addNewColumns` (hints don't change the default) |

### What `addNewColumns` actually does

1. Stream is running on schema v1.
2. File arrives with an extra column `discount`.
3. Auto Loader detects the new column; throws a special exception (`UnknownFieldException`).
4. The stream **stops**.
5. Schema v2 is written to `schemaLocation/_schemas/`.
6. **The stream auto-restarts** (in Lakeflow Jobs / LDP) — picks up schema v2 and proceeds.
7. From this point, `discount` is in the table.

In raw Structured Streaming (not LDP), the auto-restart depends on your job framework. Lakeflow Jobs / LDP handles it; a manual `spark-submit` may not. For exam purposes, `addNewColumns` does cause a restart, but in LDP that restart is transparent.

### What `rescue` actually does

1. Stream is running on schema v1.
2. File arrives with an extra column `discount`.
3. Auto Loader writes the row with `discount` value packed into the **`_rescued_data`** column (a JSON STRING).
4. No restart. No failure. The Bronze table accumulates a `_rescued_data` column where applicable.

```json
// _rescued_data value for the row above
{"discount": 5.0, "_file_path": "/Volumes/.../file_123.json"}
```

Downstream consumers can parse `_rescued_data` later when they're ready to add the column to Silver.

### What `failOnNewColumns` does

The stream fails the moment a new column appears. Use when you want a human to make a conscious schema decision (e.g., regulated environments).

### What `none` does

New columns in the source files are **dropped silently.** No error, no rescue, no restart. The Bronze table never sees the new column. This is the default when you provided a full schema — the assumption is "I declared the schema; I want only those columns."

### ⚠️ Exam trap — "I provided a schema, why am I missing data?"

Scenario: developer sets `.schema(my_schema)` and sees new columns in the source files not appearing in the Bronze table. The default `schemaEvolutionMode` for a provided schema is `none` — new columns are silently ignored. Fix: set `schemaEvolutionMode = "rescue"` to capture them in `_rescued_data`, or remove the explicit schema to let Auto Loader infer.

### `_rescued_data` column

Special column that captures:
- Columns present in the source file but not in the table schema.
- Values that fail to parse to the expected type.
- The original file path (`_file_path`).

Always a STRING (JSON-serialized). Available in `rescue` mode automatically; in other modes only `rescuedDataColumn` setting opts it in.

```python
.option("cloudFiles.schemaEvolutionMode", "rescue")
.option("cloudFiles.rescuedDataColumn", "_rescued_data")  # optional rename
```

In a Silver-layer transformation, you typically:
```sql
SELECT *,
       get_json_object(_rescued_data, '$.discount') AS rescued_discount
FROM main.bronze.orders
WHERE _rescued_data IS NOT NULL;
```

---

## 7. File detection modes — directory listing vs file notification

How does Auto Loader know a new file has arrived?

### 7.1 Directory listing mode (default)

```python
# Default — no need to set explicitly
.option("cloudFiles.useNotifications", "false")
```

Auto Loader lists the source directory on each micro-batch trigger and compares to the checkpoint to find new files.

**Pros:** Simple. No cloud setup required.
**Cons:** Listing cost scales with directory size. For directories with hundreds of thousands of files, listing becomes the bottleneck.

**Optimizations:**
- `cloudFiles.useIncrementalListing = "auto"` (or `true`) — on supported clouds, uses incremental listing APIs (S3 `ListObjectsV2` with `start-after`, ADLS `BlobChangeFeed`) to skip files older than the last-seen marker.

### 7.2 File notification mode

```python
.option("cloudFiles.useNotifications", "true")
```

Auto Loader registers a notification subscription on the source bucket:
- **AWS S3** → SNS topic + SQS queue.
- **Azure ADLS Gen2** → Event Grid subscription + Storage Queue.
- **GCP GCS** → Pub/Sub subscription.

New files trigger notifications; Auto Loader consumes from the queue.

**Pros:** Scales to billions of files; no listing cost.
**Cons:** Requires setting up cloud-side notification resources (Databricks can do this for you with the right IAM/RBAC; or pre-create and reference). Slight per-message overhead.

### When to choose which

| File volume | Choice |
|-------------|--------|
| < 100K files in source path | Directory listing (default) |
| > 100K files, or directory listing latency is a problem | File notification |
| You can't grant Databricks the IAM to create notification resources | Directory listing with incremental listing |

### ⚠️ Exam trap — file notification vs directory listing

If a question describes a high-throughput ingestion scenario with millions of files and asks "how do you scale Auto Loader?" — the answer is **file notification mode**. If the question says "simplest setup, low volume" — directory listing.

---

## 8. Triggers

The **trigger** controls when Auto Loader processes the next batch.

### 8.1 `availableNow=True` — the modern batch-style trigger

```python
.trigger(availableNow=True)
```

- Process **all currently available** new files, then **stop**.
- Replaces the **deprecated `Trigger.Once`**.
- Right answer for: scheduled-job style ingestion ("every hour, pick up new files, exit").

### 8.2 `processingTime` — fixed cadence

```python
.trigger(processingTime="5 minutes")
```

- Run a micro-batch every N seconds/minutes.
- Stream **stays running** between batches.
- Right answer for: always-on streaming with predictable cadence.

### 8.3 Default — micro-batch ASAP

```python
# No .trigger() call — default is micro-batch ASAP
```

- Stream runs continuously; each batch starts as soon as the previous finishes.
- Right answer for: low-latency streaming with no cadence requirements.

### 8.4 `continuous` — experimental, sub-second latency

```python
.trigger(continuous="1 second")
```

- Continuous (not micro-batch) execution; very low latency.
- Experimental, narrower feature support, rare on exam.

### ⚠️ Exam trap — `availableNow` vs `processingTime`

| Scenario phrase | Trigger |
|-----------------|---------|
| "scheduled hourly job, process new files, exit" | **`availableNow=True`** |
| "always-on stream every 5 minutes" | **`processingTime="5 minutes"`** |
| "low-latency continuous processing" | default (or `continuous` for sub-second) |
| "Trigger.Once" in the answers | **Deprecated — pick `availableNow` instead** |

If `Trigger.Once` appears as an answer choice, it's likely the distractor for someone studying with pre-2024 material.

---

## 9. `checkpointLocation` — required for the write side

```python
.option("checkpointLocation", "/Volumes/main/_chk/orders")
```

- **Required** for `writeStream` to guarantee fault tolerance.
- Stores: source offsets, commit metadata, state (if stateful).
- **Never share a checkpoint between two queries** — they'll corrupt each other.
- **One checkpoint per writeStream** (a `.toTable(...)` produces one).

If you delete the checkpoint, the stream restarts from the beginning — reading all source files again. This is recovery-time-only behavior.

---

## 10. The `.toTable("...")` shortcut

```python
.toTable("main.bronze.orders")
```

- Creates the table if it doesn't exist (with inferred schema).
- Appends new data on each batch.
- The most concise sink for Delta tables.

Equivalent to:
```python
.format("delta")
.option("path", "...")    # optional for managed tables
.outputMode("append")
.start("main.bronze.orders")
```

### ⚠️ Exam trap — `.toTable` vs `.start`

`.toTable("name")` is shorthand for `.start()` against a UC table name. Both work; `.toTable` is more idiomatic for UC.

---

## 11. Full Auto Loader example with all the options

```python
from pyspark.sql.functions import col, current_timestamp

bronze = (spark.readStream
            .format("cloudFiles")
            .option("cloudFiles.format", "json")
            .option("cloudFiles.schemaLocation", "/Volumes/main/_schemas/orders")
            .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
            .option("cloudFiles.schemaHints", "order_id LONG, amount DECIMAL(18,2)")
            .option("cloudFiles.inferColumnTypes", "true")
            .option("cloudFiles.useNotifications", "true")  # high-throughput
            .load("/Volumes/main/landing/orders/")
            .withColumn("ingest_ts", current_timestamp())
            .withColumn("source_file", col("_metadata.file_path")))

(bronze.writeStream
   .option("checkpointLocation", "/Volumes/main/_chk/orders")
   .option("mergeSchema", "true")     # tolerate Bronze schema additions
   .trigger(availableNow=True)        # scheduled batch
   .toTable("main.bronze.orders"))
```

The `_metadata` struct exposes per-row file metadata (`file_path`, `file_name`, `file_modification_time`, `file_size`). Useful for audit columns.

---

## 12. Auto Loader inside LDP — SQL form

Most exam questions about LDP-with-Auto-Loader use the SQL form:

```sql
CREATE OR REFRESH STREAMING TABLE main.bronze.orders
AS SELECT
     *,
     _metadata.file_path AS source_file,
     current_timestamp() AS ingest_ts
   FROM STREAM read_files(
     '/Volumes/main/landing/orders/',
     format       => 'json',
     schemaHints  => 'order_id LONG, amount DECIMAL(18,2)',
     schemaEvolutionMode => 'addNewColumns'
   );
```

`read_files(...)` is the SQL equivalent of `spark.readStream.format("cloudFiles")`. Inside `STREAM(...)`, it becomes incremental (uses Auto Loader's checkpointing automatically).

The SQL options map directly:
- Python `.option("cloudFiles.format", "json")` ↔ SQL `format => 'json'`
- Python `.option("cloudFiles.schemaLocation", "...")` ↔ implicit; LDP manages it
- Python `.option("cloudFiles.schemaEvolutionMode", "addNewColumns")` ↔ SQL `schemaEvolutionMode => 'addNewColumns'`
- Python `.option("cloudFiles.schemaHints", "...")` ↔ SQL `schemaHints => 'order_id LONG, amount DECIMAL(18,2)'`

---

## 13. Mini quiz (cold)

1. Auto Loader is reading JSON files; no schema provided. A file arrives with a new column `discount`. What happens by default?
2. Same scenario but schema is provided via `.schema(...)`. What happens by default?
3. You want unexpected columns captured but don't want the stream to restart. Which `schemaEvolutionMode`?
4. A scheduled job should process all currently-available files and exit. Which trigger?
5. An always-on stream should run a micro-batch every 5 minutes. Which trigger?
6. You're ingesting 50M files from S3 and directory listing is taking 20 minutes per batch. What fix?
7. Where is the `_rescued_data` column populated by default?
8. Translate this to Python form: `STREAM read_files('/Volumes/main/landing/', format => 'json', schemaHints => 'id LONG')`.
9. What's the difference between `cloudFiles.schemaLocation` and `checkpointLocation`?

### Answers

1. **`addNewColumns` (default for inferred schema).** Stream stops, schema updated to include `discount`, stream auto-restarts. In LDP this is transparent.
2. **`none` (default for provided schema).** New column silently dropped — `discount` is not written to the table.
3. **`rescue`** — places unexpected data in `_rescued_data`, no restart, no failure.
4. **`.trigger(availableNow=True)`** — process all available, then stop. Replaces deprecated `Trigger.Once`.
5. **`.trigger(processingTime="5 minutes")`**.
6. **Switch to `cloudFiles.useNotifications = true`** (file notification mode). Or enable `cloudFiles.useIncrementalListing` if you can't set up notifications.
7. **`rescue` mode** populates it by default. In other modes, set `cloudFiles.rescuedDataColumn` explicitly to opt in.
8. ```python
   (spark.readStream
      .format("cloudFiles")
      .option("cloudFiles.format", "json")
      .option("cloudFiles.schemaHints", "id LONG")
      .option("cloudFiles.schemaLocation", "<some path>")  # required for inference
      .load("/Volumes/main/landing/"))
   ```
9. **`schemaLocation`** stores schema-inference history (versions of the inferred schema). **`checkpointLocation`** stores the streaming offset / state / commit metadata. Two separate paths, two separate concerns. Don't conflate.

---

## 14. Sanity check before moving on

You should be able to:
- Write a full Auto Loader query from scratch.
- Recite the four schema-evolution modes and the two defaults.
- Choose between directory listing and file notification based on scale.
- Choose between `availableNow` and `processingTime` based on the scenario.
- Recognize `STREAM read_files(...)` as the LDP-SQL equivalent.
- Explain `_rescued_data` in one sentence.

If any of those are fuzzy, re-read Sections 6, 7, and 8.
