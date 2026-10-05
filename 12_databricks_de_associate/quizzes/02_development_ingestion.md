# Quiz 02 — Development & Ingestion (30%)

> Take cold. ~40 questions. ~2 min per question. Covers Delta DDL/DML, Auto Loader, ingestion methods, notebooks, Databricks Connect.

---

## Recall

1. Which command creates an empty Delta table regardless of whether one already exists with that name?
2. Which command appends a single row `('a1', 6, 9.4)` to existing Delta table `my_table`?
3. What is the default value of `cloudFiles.schemaEvolutionMode` when no schema is provided to Auto Loader?
4. What is the default value of `cloudFiles.schemaEvolutionMode` when a schema IS provided via `.schema(...)`?
5. Auto Loader samples how many files / how much data to infer schema, whichever comes first?
6. What is the default VACUUM retention?
7. What is the default OPTIMIZE target file size?
8. Liquid Clustering supports up to how many clustering keys?
9. Name the four useful Auto Loader schema-evolution modes (ignore the typeWidening variant).
10. Where in a UC-enabled workspace should new file ingestion land (DBFS, workspace files, or UC Volume)?

## Apply

11. Files arrive continuously in object storage. You want streaming ingestion with exactly-once semantics. Which tool?
12. You have 50 JSON files that drop daily on a predictable schedule. Which tool is the simplest fit?
13. You need to ingest Salesforce data with CDC into a Bronze Delta table. Which tool?
14. You want to run a scheduled job hourly: pick up all new files, process them, exit. Which trigger?
15. You want an always-on stream that runs a micro-batch every 5 minutes. Which trigger?
16. You're inside an LDP SQL pipeline and want to declare a streaming Bronze table reading JSON. Which function do you reference inside `STREAM(...)`?
17. Schema inference is happening. Where must `cloudFiles.schemaLocation` point?
18. Auto Loader is reading 50 million files from S3 and directory listing takes 20 minutes per batch. What's the fix?
19. You want unexpected columns in source files captured but the stream NOT to restart or fail. Which `schemaEvolutionMode`?
20. After a bad MERGE corrupted the table, you want to roll back to before the MERGE. Which command?
21. To pass parameters from a Lakeflow Job to a notebook, the notebook reads them via which API?
22. To share Python utility functions across notebooks (same REPL scope), which command?

## Diagnose

23. The team set `.schema(my_schema)` on an Auto Loader query. New source columns appear but never make it to the Bronze table. Why? Fix?
24. Two streams share the same `checkpointLocation`. They corrupt each other. Why?
25. A team's COPY INTO loads the same files repeatedly every day, producing duplicates. They expected idempotent behavior. What's wrong?
26. A scheduled streaming job set `.trigger(processingTime="1 hour")` — they wanted "run once an hour." Bills are higher than expected. What's wrong?
27. `spark.read.json(path).write.saveAsTable(t)` is in a job that runs hourly. Why is it producing duplicates?
28. The team accidentally deleted the Delta table's `_delta_log/` directory. What does the table look like now?
29. The user runs `SELECT * FROM t VERSION AS OF 100`, but the query errors. The current version is 200, default VACUUM has been running. Why?
30. A team tries `CREATE TABLE my_table AS SELECT id STRING, dt DATE, score FLOAT` and gets a syntax error. Why?

## Defend

31. The official sample question asks for the SQL to "create an empty Delta table regardless of whether one already exists." Why is `CREATE OR REPLACE TABLE` correct and `CREATE TABLE IF NOT EXISTS` wrong?
32. Why is `count_distinct("billing_id")` correct vs `count("billing_id")` when the prompt says "unique invoices"?
33. Why is `INSERT INTO t VALUES (...)` correct vs `UPDATE t VALUES (...)` for appending a new row?
34. Why should a team always use UC Volumes over DBFS for new ingestion?
35. The question asks why `Trigger.Once` is wrong as an answer in 2026. What replaced it and why?
36. Defend `read_files()` inside `STREAM(...)` as the LDP SQL canonical way to do Auto Loader ingestion.
37. Argue why `.toTable("name")` is preferable to `.start()` when writing a streaming Delta table.
38. Lakeflow Connect vs Auto Loader — defend each as the right tool for a specific use case.
39. Why does `cloudFiles.useNotifications` matter for high-volume directories?
40. Defend keeping Bronze schemas wide and tolerant (e.g., use `rescue` mode) vs strict (`failOnNewColumns`).

---

## Answers

1. **`CREATE OR REPLACE TABLE …`** — drops-and-recreates if it exists; creates fresh if it doesn't.
2. **`INSERT INTO my_table VALUES ('a1', 6, 9.4)`**.
3. **`addNewColumns`** — when no schema is provided.
4. **`none`** — when schema is provided via `.schema(...)`.
5. **1000 files or 50 GB**, whichever comes first.
6. **168 hours (7 days)**.
7. **1 GB** (`spark.databricks.delta.optimize.maxFileSize`).
8. **4**.
9. **`addNewColumns`, `rescue`, `failOnNewColumns`, `none`**.
10. **UC Volume**, e.g., `/Volumes/main/landing/orders/`.
11. **Auto Loader (`cloudFiles`)** with `.trigger(availableNow=True)` for scheduled-batch or `.trigger(processingTime=...)` for cadence.
12. **`COPY INTO`** — bounded, idempotent, simple. Auto Loader also works but is overkill.
13. **Lakeflow Connect** — managed Salesforce connector with CDC.
14. **`.trigger(availableNow=True)`** — process all available, then exit.
15. **`.trigger(processingTime="5 minutes")`**.
16. **`read_files(...)`** — `STREAM read_files('/path', format => 'json')`. Internally uses Auto Loader.
17. **A UC Volume or external location path that Auto Loader can write the `_schemas/` history to**, e.g., `/Volumes/main/_schemas/orders`.
18. **Enable `cloudFiles.useNotifications = true`** (file notification mode) so Auto Loader gets cloud events instead of listing the directory. Alternative: `cloudFiles.useIncrementalListing` if you can't set up notifications.
19. **`rescue`** — places unexpected data in `_rescued_data` column, no restart, no failure.
20. **`RESTORE TABLE t TO VERSION AS OF <pre-merge version>`** — find the right version via `DESCRIBE HISTORY` first.
21. **`dbutils.widgets`** — declare with `dbutils.widgets.text("env", "dev")`, read with `dbutils.widgets.get("env")`.
22. **`%run /path/to/notebook`** — shares the Python REPL scope. `dbutils.notebook.run` runs in a separate context and only returns a string.
23. **Default mode for provided schema is `none` — new columns are silently ignored.** Fix: set `schemaEvolutionMode = "rescue"` to capture them in `_rescued_data`, or remove the explicit schema to let Auto Loader infer (default then becomes `addNewColumns`).
24. **Each writes offsets and commits to the same location**; they race and clobber each other's state. Solution: distinct `checkpointLocation` per query.
25. **They're using `spark.read.json().write.saveAsTable` instead of `COPY INTO`.** `COPY INTO` tracks loaded file paths and is idempotent; raw `spark.read` is not. Switch to `COPY INTO` or Auto Loader.
26. **`processingTime` keeps the stream running 24/7**, with a 1-hour micro-batch cadence — but compute is always provisioned. For "run once an hour," use a scheduled Lakeflow Job with `.trigger(availableNow=True)` — job cluster spins up, processes, tears down.
27. **`spark.read` has no incremental tracking.** Every run re-reads the entire path. Solutions: (a) Auto Loader with `.trigger(availableNow=True)`, (b) `COPY INTO`, (c) hand-rolled MERGE with idempotent key.
28. **The Delta table is gone.** Without `_delta_log/`, the Parquet files are an unstructured dump. The data can theoretically be recovered into a new table (via `CONVERT TO DELTA` or just re-pointing a CREATE TABLE), but the original table's history, schema, version metadata are lost.
29. **VACUUM has deleted the data files for version 100.** Time travel is bounded by VACUUM retention (default 7 days). Files older than the retention are physically removed. The query errors because the files version 100 needs no longer exist.
30. **CTAS doesn't accept a column-type list.** With `CREATE TABLE … AS SELECT`, the schema is inferred from the SELECT. The DDL has either explicit columns OR an AS SELECT, not both.
31. **`CREATE OR REPLACE TABLE` works whether the table exists or not** — drops-and-recreates if it does, creates fresh if it doesn't. **`CREATE TABLE IF NOT EXISTS`** is a no-op if the table exists; doesn't satisfy "regardless of whether it exists."
32. **"Unique invoices" maps to distinct.** If `billing_id` can repeat (multi-line invoices, corrections), `count` includes duplicates. `count_distinct` returns the number of distinct billing IDs per group — the right semantic.
33. **`INSERT INTO`** is the append form for new rows. **`UPDATE`** modifies existing rows; it cannot insert. `UPDATE … VALUES` is not even valid syntax.
34. **UC Volumes are governed by UC** (subject to UC GRANTs / lineage / audit). **DBFS bypasses UC authorization** — anyone on the workspace can read DBFS root by default. New work should always be UC Volumes; DBFS is legacy.
35. **`Trigger.Once` is deprecated.** `.trigger(availableNow=True)` replaced it because `availableNow` handles backlog batching more gracefully on large queues (batches the backlog into multiple micro-batches; `Once` tried to do it all in one).
36. **LDP SQL pipelines are SQL-first**, so the SQL equivalent of Auto Loader is `read_files()`. Wrapping in `STREAM(...)` makes it incremental — LDP manages the checkpoint internally. This is the canonical LDP form; raw `spark.readStream` Python is for non-LDP code.
37. **`.toTable("catalog.schema.table")` is UC-idiomatic** — uses the UC name directly. `.start()` requires you to set `.format("delta")` and either a path or a table name. `.toTable` is shorter and clearer.
38. **Lakeflow Connect** wins for managed SaaS / operational-DB connectors with CDC (Salesforce, SQL Server, Postgres CDC, etc.) — no custom code. **Auto Loader** wins for files in cloud object storage — JSON / CSV / Parquet at scale. They're complementary, not alternatives.
39. **Directory listing scales O(file count).** At ~50M files, listing is the bottleneck. File notifications use cloud events (SNS/SQS, Event Grid, Pub/Sub) — Auto Loader gets notified of new files instead of listing. Scales to billions of files.
40. **Bronze should preserve the source verbatim.** Strict mode (`failOnNewColumns`) breaks the pipeline on benign schema additions and requires human intervention each time. Tolerant mode (`rescue` or `addNewColumns`) lets Bronze absorb new columns and lets Silver decide what to expose. Strict failure should be reserved for cases where unknown columns indicate a serious upstream regression.
