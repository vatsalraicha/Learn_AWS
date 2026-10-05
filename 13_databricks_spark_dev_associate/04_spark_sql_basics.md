# Module 04 — Spark SQL Basics

> **Domain 2 of 7 — Using Spark SQL (20%).**
> **Goal:** Master `spark.sql()`, temp views (regular, global, the differences), SQL on files directly, the catalog, save modes, persistent tables vs temp views. The "how do I get SQL semantics on top of DataFrames" surface.

---

## Coverage map

Verbatim Oct 2025 exam objectives covered by this module:

| Objective (Section 2 — Spark SQL, 20%) | Section |
|---|---|
| "Utilize common data sources such as JDBC, files, etc., to efficiently read from and write to Spark DataFrames using Spark SQL, including overwriting and partitioning by column." | [Reading from JDBC](#reading-from-jdbc), [Reading from files — refresh](#reading-from-files--refresh), [Writing to files — modes and options](#writing-to-files--modes-and-options) |
| "Execute SQL queries directly on files, including ORC Files, JSON Files, CSV Files, Text Files, and Delta Files, and understand the different save modes for outputting data in Spark SQL." | [Querying files directly via SQL](#querying-files-directly-via-sql), [Save modes](#save-modes) |
| "Save data to persistent tables while applying sorting and partitioning to optimize data retrieval." | [Persistent tables — saveAsTable](#persistent-tables--saveastable), [Persistent tables — sorting and partitioning](#persistent-tables--sorting-and-partitioning) |
| "Register DataFrames as temporary views in Spark SQL, allowing them to be queried with SQL syntax." | [Temp views](#temp-views) |

---

> 🎯 **How to recognize this on the exam:**
> - "Query files directly via SQL" → backtick syntax: `` SELECT * FROM parquet.`/path/to/file.parquet` ``. NOT single quotes, NOT square brackets.
> - `createTempView` vs `createOrReplaceTempView` → former **throws** if exists; latter idempotent.
> - "Access global temp view" → must qualify as **`global_temp.view_name`**.
> - "Default save mode?" → **`errorIfExists`** (throws if target exists).
> - "Save modes spelling" → `overwrite`, `append`, `ignore`, `errorIfExists` (camelCase, lowercase 'o').
> - "Can `bucketBy` use `save(path)`?" → **No** — bucketing requires `saveAsTable`.
> - "Partition overwrite affects only matching partitions?" → set `spark.sql.sources.partitionOverwriteMode=dynamic`. Default is `static` (full overwrite).
> - "What does `inferSchema=True` do?" → runs an **extra job** to infer types. Prefer explicit schema.
> - "Is `pivot` narrow or wide?" → **wide** (implicit groupBy).
> - "Faster pivot?" → pass **explicit values** to skip the discovery job.

---

## Why this module exists

Two of the seven exam domains are Spark SQL. Most senior PySpark engineers default to DataFrame API for everything and rarely write `spark.sql()`. The exam *does* test:

- `createTempView` vs `createOrReplaceTempView` vs **global** temp view.
- SQL queries on files directly: `SELECT * FROM parquet.` `path` ``.
- Save modes (`overwrite`, `append`, `ignore`, `errorIfExists`).
- `saveAsTable` (persistent) vs temp views.
- The catalog: `spark.catalog.listDatabases()`, `spark.catalog.listTables()`.

Brush up these and you'll get the SQL questions cold.

---

## The two equivalent surfaces

```python
# DataFrame API
result = (df.filter(F.col("age") > 30)
            .groupBy("dept")
            .agg(F.count("*").alias("n")))

# SQL — same query
df.createOrReplaceTempView("people")
result = spark.sql("""
    SELECT dept, COUNT(*) AS n
    FROM people
    WHERE age > 30
    GROUP BY dept
""")
```

Both compile to the **same Catalyst logical plan**. Same optimizations. Same physical plan. Same performance.

Choose by:
- **DataFrame API** — programmatic generation, IDE autocomplete, type hints, easier composition with Python.
- **SQL** — analyst familiarity, complex queries with joins/subqueries are more readable.
- **Mixed** — common: use SQL for the "shape" of the query, DataFrame for transformations.

---

## SparkSession.sql() — the gateway

```python
df_result = spark.sql("SELECT * FROM my_table WHERE x > 10")
```

`spark.sql(query_string)` returns a **DataFrame** — lazy, same as any DataFrame construction. Nothing executes until an action.

You can interpolate Python variables (carefully — SQL injection risk for user input):

```python
threshold = 100
df = spark.sql(f"SELECT * FROM events WHERE score > {threshold}")

# Better — parameter substitution (Spark 3.4+)
df = spark.sql("SELECT * FROM events WHERE score > :t", args={"t": 100})
```

---

## Temp views

Spark SQL needs tables to query. DataFrames can be registered as **temporary views** that exist for the SparkSession's lifetime.

### Three view types

| View type | Scope | API |
|---|---|---|
| **Temporary view** | Current SparkSession only | `df.createOrReplaceTempView("name")` |
| **Global temporary view** | All SparkSessions on the cluster (cross-session) | `df.createOrReplaceGlobalTempView("name")` |
| **Persistent table** | Catalog (Hive metastore / Unity Catalog) — survives cluster restart | `df.write.saveAsTable("name")` |

### `createTempView` vs `createOrReplaceTempView`

```python
df.createTempView("my_view")            # FAILS if view already exists
df.createOrReplaceTempView("my_view")   # always succeeds (replaces if exists)
```

⚠️ **Exam trap:** know that `createTempView` raises `AnalysisException` if the view exists. `createOrReplaceTempView` is the idempotent option used in 99% of real code.

### Global temp views

Global temp views are special:
- They live in a **reserved database called `global_temp`**.
- Access them as `global_temp.<view_name>` — always.
- Shared across SparkSessions on the same Spark application (rare in practice but exam-testable).

```python
df.createOrReplaceGlobalTempView("shared_view")

# Access — must qualify with global_temp
spark.sql("SELECT * FROM global_temp.shared_view")

# This FAILS — no qualifier
spark.sql("SELECT * FROM shared_view")  # AnalysisException: Table not found
```

### Dropping views

```python
spark.catalog.dropTempView("my_view")
spark.catalog.dropGlobalTempView("shared_view")
```

---

## Querying files directly via SQL

You don't need to register a view to query a file. Spark SQL supports:

```sql
SELECT * FROM parquet.`/path/to/file.parquet`
SELECT * FROM json.`/path/to/file.json`
SELECT * FROM csv.`/path/to/file.csv`
SELECT * FROM delta.`/path/to/delta_table`
SELECT * FROM orc.`/path/to/file.orc`
SELECT * FROM text.`/path/to/file.txt`
```

- The format name (`parquet`, `json`, `csv`, `delta`, `orc`, `text`) is the **data source identifier**.
- The path is **backtick-quoted** (because it contains `/` and `.` — characters that SQL would otherwise interpret).
- Schema is **inferred** from the file (or, for Delta, read from the transaction log).

⚠️ **CSV special case:** without options, CSV is read with no header and string-typed columns. You can't pass options through the SQL `parquet.` `path` `` syntax — for non-default options, fall back to `spark.read.option(...).csv(...)` and create a temp view.

⚠️ **Exam trap:** the exact syntax is `format.` `path` `` (backticks around path). NOT quotes; NOT square brackets; NOT `FROM 'path' WITH (format='parquet')`.

### Why this works

The SQL parser sees `parquet.X` where X is a backtick-quoted identifier; it interprets `parquet` as a "database-like" namespace and routes the resolution to the data source registry.

This is mostly an exam-trivia feature in real code — most teams use temp views or persistent tables. But the exam loves it because it tests SQL fluency.

---

## The catalog

The **catalog** is Spark's metadata store — tracking databases, tables, views, functions.

### In-memory catalog (default)

Without configuration, Spark uses an **in-memory catalog** scoped to the SparkSession. Temp views live here. Persistent tables (created with `saveAsTable`) also live here but persist via the underlying metadata store.

### Hive metastore (optional but common)

When `spark.sql.catalogImplementation=hive` (default in Databricks/EMR), Spark uses a Hive-compatible metastore (often a database like MySQL/PostgreSQL backing it). Persistent tables survive cluster restarts.

### Catalog API

```python
spark.catalog.listDatabases()    # all databases
spark.catalog.listTables()       # tables in current database
spark.catalog.listTables("my_db")  # tables in specific database
spark.catalog.listColumns("my_table")
spark.catalog.listFunctions()

spark.catalog.currentDatabase()
spark.catalog.setCurrentDatabase("my_db")

spark.catalog.databaseExists("x")
spark.catalog.tableExists("x")

spark.catalog.dropTempView("v")

# Cache management
spark.catalog.cacheTable("table_name")
spark.catalog.uncacheTable("table_name")
spark.catalog.clearCache()       # uncache everything
spark.catalog.isCached("table_name")
```

⚠️ **Exam framing:** the catalog API isn't deeply tested, but you should recognize names like `listTables()` and `cacheTable()`. Pattern A "which method does X" questions sometimes include catalog distractors.

---

## Persistent tables — `saveAsTable`

```python
df.write.saveAsTable("my_db.my_table")
df.write.mode("overwrite").saveAsTable("my_db.my_table")
df.write.format("parquet").mode("overwrite").saveAsTable("my_db.my_table")
df.write.partitionBy("country").saveAsTable("my_db.my_table")
df.write.bucketBy(10, "user_id").sortBy("ts").saveAsTable("my_db.bucketed_table")
```

### saveAsTable vs save

| | `save(path)` | `saveAsTable(name)` |
|---|---|---|
| Output | Files at a path | Files + catalog entry |
| Discoverable via `spark.catalog.listTables()`? | No | Yes |
| Survives cluster restart? | Files survive; not registered | Yes (if persistent catalog) |
| Bucketing supported? | **No** — bucketing is a Hive/catalog feature | **Yes** |

⚠️ **Bucketing requires `saveAsTable`.** `df.write.bucketBy(...).save(path)` is not supported. This is an exam-testable subtlety.

---

## Save modes

```python
df.write.mode("overwrite").parquet("path")
```

| Mode | Behavior if target exists |
|---|---|
| `errorIfExists` (default) | **Throws `AnalysisException`** |
| `overwrite` | Replaces target (deletes existing files/partitions) |
| `append` | Adds new files to target |
| `ignore` | Silently does nothing |

### Mode names — exam-pedantic

The exact spellings matter:
- `"overwrite"` (one word, lowercase)
- `"append"` (lowercase)
- `"ignore"` (lowercase)
- `"errorIfExists"` (camelCase) OR `"error"` (alias)

Capital-O `"Overwrite"` is not accepted by string-based mode setting — though there is also a `SaveMode` enum in Scala.

### Overwrite + partitionBy interaction

```python
df.write.mode("overwrite").partitionBy("country").parquet("/data/output")
```

By default, this **overwrites the ENTIRE output directory** — not just the partitions present in `df`.

To overwrite only the partitions present in `df` (preserving other partitions):

```python
spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")
df.write.mode("overwrite").partitionBy("country").parquet("/data/output")
```

With `dynamic` mode, only partitions matching `df`'s `country` values are overwritten; others remain.

⚠️ **Exam-testable:** the default `partitionOverwriteMode` is `static` (full directory overwrite). `dynamic` is opt-in.

---

## SQL DDL — creating tables from scratch

```sql
CREATE TABLE my_db.events (
    id BIGINT,
    user_id STRING,
    event_type STRING,
    ts TIMESTAMP
) USING PARQUET
PARTITIONED BY (country STRING)
LOCATION '/data/events'

CREATE TABLE my_db.events_clone AS SELECT * FROM my_db.events  -- CTAS

CREATE TABLE IF NOT EXISTS ...
DROP TABLE IF EXISTS my_table

CREATE OR REPLACE TEMP VIEW my_view AS SELECT * FROM events WHERE x > 10
```

### CREATE TABLE USING vs CREATE TABLE

- `CREATE TABLE ... USING <format>` — Spark-native syntax. Works with Spark data sources (parquet, json, delta, csv).
- `CREATE TABLE` without `USING` — Hive-style; uses `spark.sql.sources.default` (parquet by default).

### Common SQL DDL on the exam

```sql
-- Insert from query
INSERT INTO my_table SELECT * FROM staging
INSERT OVERWRITE TABLE my_table SELECT * FROM staging

-- Insert with column list
INSERT INTO my_table (id, name) VALUES (1, 'Alice')

-- Truncate
TRUNCATE TABLE my_table

-- Alter
ALTER TABLE my_table ADD COLUMN new_col STRING
ALTER TABLE my_table RENAME TO renamed_table

-- Describe
DESCRIBE TABLE my_table
DESCRIBE EXTENDED my_table
SHOW TABLES IN my_db
SHOW PARTITIONS my_table
```

---

## Pivot and unpivot

### Pivot

```python
# Long → wide
df.groupBy("country").pivot("year").sum("revenue")
df.groupBy("country").pivot("year", [2023, 2024, 2025]).sum("revenue")  # explicit values (faster)
```

```sql
SELECT * FROM (
  SELECT country, year, revenue FROM sales
)
PIVOT (
  SUM(revenue) FOR year IN (2023, 2024, 2025)
)
```

⚠️ Pivot is a **wide transformation** — it implicitly groups.

⚠️ **Performance tip**: passing explicit values to `pivot()` (the second argument) avoids a job that scans the data to discover distinct values. Without explicit values, Spark first runs a `SELECT DISTINCT year` job before the actual pivot.

### Unpivot (Spark 3.4+)

```python
# Wide → long
df.unpivot(ids=["country"], values=["2023", "2024", "2025"],
           variableColumnName="year", valueColumnName="revenue")
```

```sql
SELECT * FROM wide_sales
UNPIVOT (revenue FOR year IN (`2023`, `2024`, `2025`))
```

---

## Reading from JDBC

```python
df = (spark.read
      .format("jdbc")
      .option("url", "jdbc:postgresql://host:5432/db")
      .option("dbtable", "schema.table")
      .option("user", "user")
      .option("password", "pwd")
      .load())

# Parallel read with partitioning
df = (spark.read
      .format("jdbc")
      .option("url", "...")
      .option("dbtable", "transactions")
      .option("partitionColumn", "id")
      .option("lowerBound", "1")
      .option("upperBound", "1000000")
      .option("numPartitions", "10")
      .load())
```

When `numPartitions > 1`, Spark issues `numPartitions` parallel queries with WHERE clauses on `partitionColumn` to split the work.

### Writing back

```python
(df.write
   .format("jdbc")
   .option("url", "...")
   .option("dbtable", "output_table")
   .mode("append")
   .save())
```

⚠️ The exam mentions "JDBC, files, etc." as data sources. Knowing the option names (`url`, `dbtable`, `user`, `password`, `numPartitions`, `partitionColumn`) is enough.

---

## Reading from files — refresh

```python
# CSV with options
df = (spark.read
      .option("header", True)
      .option("inferSchema", True)
      .option("delimiter", "|")
      .option("nullValue", "NA")
      .option("dateFormat", "yyyy-MM-dd")
      .csv("path/to/file.csv"))

# JSON
df = spark.read.json("path/to/file.json")
df = spark.read.json("path/to/file.json", multiLine=True)  # multi-line JSON objects

# Parquet
df = spark.read.parquet("path/to/file.parquet")
df = spark.read.parquet("path/to/dir/*.parquet")  # globbing

# Multiple paths
df = spark.read.parquet("path/2024", "path/2025")

# With explicit schema
schema = "id INT, name STRING, ts TIMESTAMP"
df = spark.read.schema(schema).csv("path/to/file.csv")
```

⚠️ **`inferSchema=True` triggers a job** — Spark reads the data once to infer types, then again to load. For known schemas, **always pass `.schema()` explicitly** — faster and avoids type mistakes.

---

## Writing to files — modes and options

```python
# Basic
df.write.parquet("path")
df.write.mode("overwrite").parquet("path")

# With partitioning
df.write.partitionBy("country", "year").parquet("path")

# Bucketing (requires saveAsTable)
df.write.bucketBy(10, "user_id").sortBy("ts").saveAsTable("my_db.bucketed")

# Format
df.write.format("parquet").save("path")        # equivalent to df.write.parquet("path")
df.write.format("delta").save("path")          # Delta Lake
df.write.format("orc").save("path")
df.write.format("json").save("path")
df.write.format("csv").option("header", True).save("path")
```

### Sort within partitions before write

```python
df.sortWithinPartitions("ts").write.parquet("path")
```

Improves min/max statistics for predicate pushdown.

---

## Persistent tables — sorting and partitioning

```python
# Partition by country (subdirectories: country=US, country=CA, ...)
df.write.partitionBy("country").saveAsTable("my_db.events")

# Bucket by user_id into 10 buckets (for join optimization)
df.write.bucketBy(10, "user_id").sortBy("ts").saveAsTable("my_db.events_bucketed")
```

### partitionBy vs bucketBy

| | partitionBy | bucketBy |
|---|---|---|
| **Storage layout** | Subdirectories per value (`country=US/`) | N hash-bucketed files within table dir |
| **Cardinality** | Low-medium (countries, months) | High (user_ids, item_ids) |
| **Pruning** | Yes — at directory level | Yes — at bucket level (during join) |
| **Use case** | Filter pushdown by partition column | Co-located joins on bucket key |
| **Requires** | Either `save` or `saveAsTable` | **Only `saveAsTable`** |

⚠️ **Bucketing on a column eliminates shuffle for joins on that column** (between two tables bucketed the same way) — but only when both tables are bucketed identically.

---

## SQL on partitioned tables

```sql
SELECT * FROM events WHERE country = 'US' AND year = 2025
```

If `events` is `PARTITIONED BY (country, year)`, Spark **prunes** to only the `country=US/year=2025/` directory at planning time. The Spark UI scan node shows `numPartitionsRead` (matched) vs `numPartitions` (total).

---

## Caching SQL tables

```python
spark.catalog.cacheTable("my_table")          # cache by name
spark.catalog.uncacheTable("my_table")
spark.catalog.isCached("my_table")
spark.catalog.clearCache()                    # uncache all
```

Equivalent to `spark.table("my_table").cache()`. Cached at first access (lazy).

---

## SQL functions vs DataFrame methods (preview)

```python
# DataFrame method
df.coalesce(10)             # partition reduction (narrow transform)

# SQL function
df.select(F.coalesce(F.col("a"), F.col("b"), F.lit(0)))   # first-non-null value
```

Same name, different things. Module 05 dives into this.

---

## Mini-quiz

1. What's the difference between `createTempView` and `createOrReplaceTempView`?
2. What's the qualifier for global temp views in a SQL query?
3. Write the SQL syntax to read `/data/file.parquet` directly without registering a view.
4. What's the default save mode if you don't specify one?
5. Does `saveAsTable` write files? Does it write metadata?
6. Does `df.write.bucketBy(10, "id").parquet("path")` work?
7. What does `spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")` do?
8. What's the side effect of `inferSchema=True` on `spark.read.csv()`?
9. Which transformation does `pivot` qualify as — narrow or wide?
10. How do you uncache a registered table?

### Answers

1. `createTempView` **throws** if the view name exists. `createOrReplaceTempView` always succeeds.
2. `global_temp.<view_name>`.
3. ``SELECT * FROM parquet.`/data/file.parquet` ``
4. **`errorIfExists`** — throws if the target exists.
5. **Yes to both.** Writes files at the table location AND registers metadata in the catalog.
6. **No.** Bucketing requires `saveAsTable`. The line raises an error.
7. Changes overwrite behavior to only overwrite partitions present in the DataFrame, preserving others. Default is `static` (full directory overwrite).
8. Spark **runs a job** to scan the data and infer types before the actual read. Always prefer explicit `.schema(...)`.
9. **Wide** — pivot implicitly groups.
10. `spark.catalog.uncacheTable("name")`.

---

## Exam-day cheat sheet

- **`spark.sql(query)` returns a DataFrame (lazy).**
- **`createTempView`** fails if exists; **`createOrReplaceTempView`** always succeeds.
- **Global temp views live in `global_temp.` database.**
- **Query files via SQL:** `` SELECT * FROM parquet.`path` `` (backticks around path).
- **Save modes:** `errorIfExists` (default), `overwrite`, `append`, `ignore`.
- **`saveAsTable`** writes files AND registers metadata.
- **`bucketBy` requires `saveAsTable`.**
- **`partitionOverwriteMode=dynamic`** only overwrites partitions present in DF.
- **`inferSchema=True`** triggers a separate scan job — prefer explicit schema.
- **`pivot` is wide** (implicit groupBy).
- **`partitionBy`** = low-cardinality subdirectories; **`bucketBy`** = high-cardinality hash buckets.

Next: [Module 05 — Spark SQL Functions](05_spark_sql_functions.md).
