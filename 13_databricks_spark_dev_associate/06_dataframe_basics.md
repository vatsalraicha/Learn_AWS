# Module 06 — DataFrame Basics: Reading, Writing, Schemas

> **Domain 3 of 7 — DataFrame/Dataset API (30% — LARGEST DOMAIN).**
> **Goal:** Master file I/O, schema specification (inferred vs DDL string vs StructType), and the `read` / `write` API surface. The exam tests exact method names and option keys.

---

## Coverage map

Verbatim Oct 2025 exam objectives covered by this module:

| Objective | Section |
|---|---|
| (Section 3) "Manage input and output operations by writing, overwriting, and reading DataFrames with schemas." | [The read/write API surface](#the-readwrite-api-surface), [Schema specification](#schema-specification), [Writing — save modes](#writing--save-modes) |
| (Section 2) "Utilize common data sources such as JDBC, files, etc., ... including overwriting and partitioning by column." | [Reading Parquet](#reading-parquet), [Reading CSV](#reading-csv), [Reading JSON](#reading-json), [Writing — partitioning](#writing--partitioning) |
| (Section 2) "Save data to persistent tables while applying sorting and partitioning to optimize data retrieval." | [Writing — bucketing (requires saveAsTable)](#writing--bucketing-requires-saveastable) |

---

> 🎯 **How to recognize this on the exam:**
> - Builder chain: `.mode()`, `.partitionBy()`, `.option()`, `.schema()` all return the builder — order between them rarely matters. The **terminal method** (`.parquet(path)`, `.csv(path)`, `.save(path)`) must come **last**. Calling anything after the terminal method is invalid.
> - "Read partitioned Parquet with overwrite" → `df.write.mode("overwrite").partitionBy("country").parquet("/data/out")`. Sample Q1.
> - "Default save mode" → **`errorIfExists`**.
> - "Default Parquet compression" → **`snappy`**.
> - "Multi-line JSON?" → `option("multiLine", True)`.
> - "Bucketing with `parquet(path)`?" → **fails** — bucketing requires `saveAsTable`.
> - "Schema with DDL string" → `"id INT, name STRING, address STRUCT<street: STRING, zip: INT>"`.
> - "Reading 1000 small files but getting 40 partitions" → file packing into 128 MB partitions (`spark.sql.files.maxPartitionBytes`).
> - "Multiple paths in one read?" → `spark.read.parquet("path1", "path2", ...)` (positional args).
> - "What does `mergeSchema=True` do?" → reads metadata of all Parquet files for unified schema; expensive.
> - "`inferSchema=True` cost?" → triggers a separate scan job. Use explicit schema.

---

## Why this module exists

About 14 of the 45 exam questions are DataFrame API. Many are code-recognition: "Which block reads a CSV with explicit schema and overwrites the output as partitioned Parquet?" The four options vary in:
- Method name (`read.csv` vs `read.option(...).csv`).
- Option keys (`header` vs `headers`, `inferSchema` vs `inferschema`).
- Schema specification (DDL string vs StructType vs string in `.schema()`).
- Mode placement (`mode("overwrite")` before vs after `.parquet(path)`).

Memorize the canonical signatures. There's no clever shortcut.

---

## The read/write API surface

```python
# READ
spark.read.<format>(path)
spark.read.format(name).load(path)
spark.read.option(key, value).format(name).load(path)
spark.read.options(**kwargs).format(name).load(path)
spark.read.schema(schema).format(name).load(path)

# WRITE  
df.write.<format>(path)
df.write.format(name).save(path)
df.write.mode(mode).<format>(path)
df.write.option(key, value).format(name).save(path)
df.write.partitionBy(*cols).<format>(path)
df.write.saveAsTable(name)
df.write.bucketBy(N, *cols).sortBy(*cols).saveAsTable(name)
```

The two entry points are `spark.read` (a `DataFrameReader`) and `df.write` (a `DataFrameWriter`). Both are **builders** — chain options, then call a terminal method.

---

## Reading Parquet

```python
df = spark.read.parquet("path/to/file.parquet")
df = spark.read.parquet("path/to/dir/")              # all parquet files in dir
df = spark.read.parquet("path/2024", "path/2025")    # multiple paths
df = spark.read.parquet("path/year=2025/*/")         # globbing
df = spark.read.format("parquet").load("path")       # equivalent
```

### Options

```python
spark.read.option("mergeSchema", True).parquet("path")  # merge differing schemas across files
spark.read.option("pathGlobFilter", "*.parquet").parquet("path")
spark.read.option("recursiveFileLookup", True).parquet("path")
```

⚠️ **`mergeSchema=True` is expensive** — Spark reads metadata of every file to compute a unified schema. Default is False.

---

## Reading CSV

```python
df = spark.read.csv("path/to/file.csv")
df = (spark.read
      .option("header", True)
      .option("inferSchema", True)
      .option("delimiter", "|")
      .option("nullValue", "NA")
      .option("dateFormat", "yyyy-MM-dd")
      .option("timestampFormat", "yyyy-MM-dd HH:mm:ss")
      .option("quote", '"')
      .option("escape", '"')
      .option("multiLine", True)
      .csv("path/to/file.csv"))
```

### Common CSV options

| Option | Default | Notes |
|---|---|---|
| `header` | `false` | First row is header? |
| `inferSchema` | `false` | Triggers a separate scan job |
| `delimiter` / `sep` | `,` | Field separator |
| `quote` | `"` | Field quote char |
| `escape` | `\` | Escape inside quoted fields |
| `multiLine` | `false` | Fields contain newlines? |
| `nullValue` | `""` | String representing NULL |
| `dateFormat` | `yyyy-MM-dd` | |
| `timestampFormat` | `yyyy-MM-dd'T'HH:mm:ss[.SSS][XXX]` | |
| `mode` | `PERMISSIVE` | Parse error mode: PERMISSIVE, DROPMALFORMED, FAILFAST |
| `nanValue` | `NaN` | |
| `positiveInf` / `negativeInf` | `Inf` / `-Inf` | |
| `enforceSchema` | `true` | Validate against provided schema |

⚠️ **`inferSchema=True` runs an EXTRA JOB** to scan the file for type inference. For known schemas, pass `.schema()` explicitly.

⚠️ **Parse-error mode trap:**
- `PERMISSIVE` (default): malformed rows have all fields NULL + a "_corrupt_record" column.
- `DROPMALFORMED`: malformed rows silently dropped.
- `FAILFAST`: throws on first malformed row.

---

## Reading JSON

```python
df = spark.read.json("path/to/file.json")
df = spark.read.option("multiLine", True).json("path")    # one JSON object spanning multiple lines

# JSON Lines (default — one JSON per line)
df = spark.read.json("path/to/file.jsonl")
```

### Common JSON options

| Option | Default | Notes |
|---|---|---|
| `multiLine` | `false` | Single JSON object vs JSON Lines |
| `allowComments` | `false` | Allow Java-style comments |
| `allowSingleQuotes` | `true` | |
| `allowUnquotedFieldNames` | `false` | |
| `mode` | `PERMISSIVE` | Same as CSV |
| `primitivesAsString` | `false` | Read all primitives as strings |
| `dropFieldIfAllNull` | `false` | |
| `samplingRatio` | `1.0` | Sample fraction for schema inference |

⚠️ JSON schema inference is even more expensive than CSV — it samples the entire file by default.

---

## Reading Delta, ORC, Text

```python
# Delta (treats Delta as a readable file format)
df = spark.read.format("delta").load("path/to/delta_table")

# ORC
df = spark.read.orc("path/to/file.orc")
df = spark.read.format("orc").load("path")

# Text — each line is a row with a single 'value' column
df = spark.read.text("path/to/file.txt")
df = spark.read.text("path", wholetext=True)              # whole file as one row
```

### Reading multiple text files into one row each

```python
df = spark.read.option("wholetext", True).text("path/dir/")
# Schema: value:string  — one row per file
```

---

## Schema specification

Three ways to provide a schema:

### 1. inferSchema (lazy default)

```python
df = spark.read.option("inferSchema", True).csv("path")
```

- Triggers an extra job for the scan.
- May get types wrong if the inference sample is bad.
- Avoid in production.

### 2. DDL string (concise)

```python
schema = "id INT, name STRING, ts TIMESTAMP, amount DOUBLE"
df = spark.read.schema(schema).csv("path")
```

- Compact and readable.
- Supports `NOT NULL`: `"id INT NOT NULL"`.
- Supports nested: `"address STRUCT<street: STRING, city: STRING>"`.
- Supports arrays/maps: `"tags ARRAY<STRING>"`, `"props MAP<STRING, INT>"`.

### 3. StructType (programmatic)

```python
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType, DoubleType

schema = StructType([
    StructField("id", IntegerType(), nullable=False),
    StructField("name", StringType(), nullable=True),
    StructField("ts", TimestampType()),
    StructField("amount", DoubleType()),
])

df = spark.read.schema(schema).csv("path")
```

- Verbose but explicit.
- Easier to generate programmatically (e.g., from a config).
- Each `StructField(name, type, nullable=True, metadata={})`.

### Inspecting a DataFrame's schema

```python
df.printSchema()        # human-readable tree
df.schema               # StructType
df.dtypes               # list of (name, type_string) tuples
df.columns              # list of column names
df.schema.json()        # JSON serialization
```

⚠️ **Exam framing:** know all three forms — recognize "DDL string", "StructType", "inferSchema" in code blocks.

---

## Writing — save modes

```python
df.write.mode("overwrite").parquet("path")
df.write.mode("append").parquet("path")
df.write.mode("ignore").parquet("path")
df.write.mode("errorIfExists").parquet("path")   # default
```

| Mode | If target exists |
|---|---|
| `errorIfExists` (default) | **Throws** |
| `overwrite` | Replaces |
| `append` | Adds new files |
| `ignore` | Silently does nothing |

Aliases:
- `"error"` → `errorIfExists`
- `SaveMode.Overwrite` (Scala API; not needed in PySpark)

---

## Writing — partitioning

```python
df.write.partitionBy("country").parquet("path")
df.write.partitionBy("country", "year").parquet("path")
```

Layout on disk:

```
path/
├── country=US/
│   ├── year=2024/part-00000.parquet
│   └── year=2025/part-00000.parquet
├── country=CA/
│   ├── year=2024/part-00000.parquet
│   └── year=2025/part-00000.parquet
```

### Partition columns are removed from data

When you read partitioned data, the partition values are **inferred from the directory names** and added as columns. They're NOT stored in the Parquet files themselves — that's a storage win.

```python
spark.read.parquet("path").printSchema()
# country: STRING, year: INT, ...rest of cols
```

### Reading partitioned data

When you filter on a partition column, Spark **prunes partitions at planning time**:

```python
spark.read.parquet("path").filter("country = 'US' AND year = 2025")
# Only path/country=US/year=2025/ is read
```

This is **partition pruning** — Module 10 covers it deeper.

---

## Writing — bucketing (requires saveAsTable)

```python
df.write.bucketBy(10, "user_id").sortBy("ts").saveAsTable("my_db.bucketed")
```

- Splits data into N hash-bucketed files based on the bucket column.
- Optional `sortBy` sorts within each bucket.
- Two tables bucketed by the same column with the same N can be **joined without shuffle**.
- **Cannot use `save(path)`** — bucketing requires the table catalog to remember bucket metadata.

⚠️ **Exam-testable:** "Which write API supports bucketing?" → only `saveAsTable`. `df.write.bucketBy(...).save("path")` raises an error.

---

## Writing — common patterns

```python
# Single file output (small data, e.g., a daily report)
df.coalesce(1).write.mode("overwrite").parquet("path")

# Sort within partitions for better data skipping on read
df.sortWithinPartitions("event_date").write.partitionBy("country").parquet("path")

# Format-agnostic
df.write.format("parquet").mode("overwrite").save("path")
df.write.format("delta").mode("overwrite").option("overwriteSchema", True).save("path")

# Write specific options
df.write.option("compression", "snappy").parquet("path")
df.write.option("compression", "gzip").csv("path")

# With multiple options
df.write.options(header=True, compression="snappy").csv("path")
```

### Compression codecs

| Format | Default | Options |
|---|---|---|
| Parquet | `snappy` | `snappy`, `gzip`, `lzo`, `brotli`, `lz4`, `zstd`, `uncompressed` |
| ORC | `snappy` | `snappy`, `zlib`, `lzo`, `uncompressed` |
| CSV | `uncompressed` | `gzip`, `bzip2`, `deflate`, `xz`, `lz4`, `snappy`, `zstd` |
| JSON | `uncompressed` | same as CSV |

---

## Display and inspect (review)

```python
df.show()                     # default 20 rows, truncated
df.show(50)                   # 50 rows
df.show(20, truncate=False)   # no truncation
df.show(20, vertical=True)    # vertical layout (one column per line)

df.printSchema()              # schema tree
df.describe()                 # count, mean, stddev, min, max
df.summary()                  # describe + percentiles
df.summary("count", "min", "max", "50%", "95%")  # custom

df.dtypes
df.columns
df.first()                    # one row
df.head(5)                    # list of 5 rows
df.take(5)                    # same as head
df.tail(5)                    # last 5 rows (since 3.0)
df.count()                    # row count (ACTION)
df.distinct().count()         # distinct row count
df.isEmpty()                  # bool, since 3.3
```

⚠️ **`describe` and `summary`** are ACTIONS — they trigger jobs.

### show options

| Param | Default | Notes |
|---|---|---|
| `n` | 20 | Number of rows |
| `truncate` | True (20 chars) | True/False or integer width |
| `vertical` | False | One column per line |

---

## Converting between DataFrame and other types

```python
# DataFrame → pandas
pdf = df.toPandas()                          # collects ALL rows to driver
pdf = df.limit(1000).toPandas()              # safer

# DataFrame → RDD (not Connect-compatible)
rdd = df.rdd

# DataFrame → list of Row
rows = df.collect()

# DataFrame → list of dicts
rows = [r.asDict() for r in df.collect()]
rows = df.collect()[0].asDict()

# pandas → DataFrame
df = spark.createDataFrame(pdf)

# Python list/dict → DataFrame
df = spark.createDataFrame([(1, "a"), (2, "b")], ["id", "name"])
df = spark.createDataFrame([{"id": 1, "name": "a"}, {"id": 2, "name": "b"}])

# With explicit schema
df = spark.createDataFrame(data, schema="id INT, name STRING")
```

⚠️ **`toPandas()` collects all rows to the driver** — can OOM on large DataFrames. Use `df.limit(N).toPandas()` or `df.toLocalIterator()` for iteration.

⚠️ **`df.rdd` is not available in Spark Connect** — see Module 12.

---

## Schema evolution and mergeSchema

When reading Parquet files with different schemas (e.g., a column was added in newer files):

```python
df = spark.read.option("mergeSchema", True).parquet("path/")
```

Spark reads metadata of all files and computes a unified schema. Older files have NULL for the new columns.

⚠️ **Expensive** — proportional to file count. Off by default.

For **writes** with schema evolution (Delta-specific, not on exam):
```python
df.write.option("mergeSchema", True).format("delta").mode("append").save("path")
```

---

## Reading partitioned data with specific schema

```python
schema = "user_id INT, event STRING, country STRING, year INT"
df = spark.read.schema(schema).parquet("path/country=US/year=2025/")
```

⚠️ **Partition column types** are inferred from the directory naming by default. If you want explicit types, pass `partitionedBy` indirectly via the schema (the partition columns appear in the schema like regular columns).

---

## Common reader/writer pitfalls

| Pitfall | Fix |
|---|---|
| `inferSchema=True` slow | Pass explicit `.schema(...)` |
| CSV with header in every file | OK; `header=True` reads the first line as headers |
| Output dir already exists | Use `mode("overwrite")` or `mode("append")` |
| `partitionBy` then `bucketBy` on same write | `bucketBy` requires `saveAsTable`, not file path |
| Many small output files | `df.coalesce(N)` or `df.repartition(N)` before write |
| Reading lots of small files slow | Pre-compact upstream, or set `spark.sql.files.maxPartitionBytes` higher |
| Date column read as string | Specify schema or `dateFormat` option |
| JSON multi-line not parsed | `option("multiLine", True)` |

---

## Worked example: reading messy CSV with explicit schema

```python
from pyspark.sql.types import StructType, StructField, IntegerType, StringType, DoubleType, TimestampType

schema = StructType([
    StructField("order_id", IntegerType(), nullable=False),
    StructField("user_id", IntegerType(), nullable=False),
    StructField("status", StringType()),
    StructField("amount", DoubleType()),
    StructField("created_at", TimestampType()),
    StructField("country", StringType()),
])

df = (spark.read
      .schema(schema)
      .option("header", True)
      .option("delimiter", "|")
      .option("nullValue", "\\N")
      .option("timestampFormat", "yyyy-MM-dd HH:mm:ss")
      .option("mode", "DROPMALFORMED")
      .csv("s3://bucket/orders/*.csv"))

# Write partitioned Parquet with overwrite
(df.write
   .mode("overwrite")
   .partitionBy("country")
   .option("compression", "snappy")
   .parquet("s3://bucket/orders_parquet/"))
```

This is the kind of code block the exam will show four versions of, with three subtly broken.

---

## Mini-quiz

1. Why is `inferSchema=True` an anti-pattern in production?
2. Write a DDL-string schema for a column `address` of type struct containing `street: STRING, zip: INT`.
3. What's the default save mode?
4. Can you bucket a DataFrame with `df.write.bucketBy(10, "id").parquet("path")`?
5. What does `df.write.partitionBy("country", "year").parquet("path")` produce on disk?
6. How do you read a multi-line JSON file?
7. What's the difference between `df.show()` and `df.head()`?
8. What's the safer alternative to `df.toPandas()` when df is large?
9. Can you read multiple paths in a single `spark.read.parquet` call?
10. Is `df.describe()` an action?

### Answers

1. **Triggers an extra job** to scan the data for type inference; may infer incorrectly. Production code passes `.schema()` explicitly.
2. `"address STRUCT<street: STRING, zip: INT>"`
3. **`errorIfExists`** — throws if target exists.
4. **No.** Bucketing requires `saveAsTable`. The call raises an error.
5. Directory structure: `path/country=<value>/year=<value>/part-*.parquet`. Partition columns are removed from the file data.
6. `spark.read.option("multiLine", True).json("path")`.
7. **`show()` is an action** that prints rows to stdout. **`head()` is an action** that returns rows as a list to the driver (default 1 row; `head(n)` for n rows).
8. **`df.limit(N).toPandas()`** or `df.toLocalIterator()`.
9. **Yes** — pass multiple paths: `spark.read.parquet("path/2024", "path/2025")`.
10. **Yes.** `describe()` triggers a job to compute statistics.

---

## Exam-day cheat sheet

- **Read API:** `spark.read.<format>(path)` or `spark.read.format(name).load(path)`.
- **Write API:** `df.write.<format>(path)` or `df.write.format(name).save(path)`.
- **Schema options:** inferSchema (slow), DDL string (concise), StructType (explicit).
- **Save modes:** `errorIfExists` (default), `overwrite`, `append`, `ignore`.
- **`mergeSchema=True`** for Parquet: expensive but useful for schema evolution.
- **`partitionBy`** for low-cardinality directory-based partitioning.
- **`bucketBy` requires `saveAsTable`** — not compatible with file-path writes.
- **`toPandas()` collects all rows** to driver — OOM risk on large DFs.
- **CSV with `multiLine=True`** for fields spanning newlines.
- **JSON with `multiLine=True`** for single JSON object across multiple lines.
- **Default compression: Parquet = snappy, ORC = snappy, CSV/JSON = uncompressed.**

Next: [Module 07 — DataFrame Transformations](07_dataframe_transformations.md).
