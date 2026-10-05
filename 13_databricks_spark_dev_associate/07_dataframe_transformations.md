# Module 07 — DataFrame Transformations

> **Domain 3 of 7 — DataFrame/Dataset API (30%).**
> **Goal:** Master the narrow transformations that compose 80% of PySpark code — `select`, `filter`, `withColumn`, `drop`, `distinct`, `sample`, `limit`, `sort`. The exam mostly tests code recognition; this module is about exact method signatures.

---

## Coverage map

Verbatim Oct 2025 exam objectives covered by this module:

| Objective (Section 3 — DataFrame/Dataset API, 30%) | Section |
|---|---|
| "Manipulate columns, rows, and table structures by adding, dropping, splitting, renaming column names, applying filters, and exploding arrays." | [select](#select--column-projection), [filter / where](#filter--where), [withColumn / withColumnRenamed / withColumns](#withcolumn--withcolumnrenamed--withcolumns), [drop](#drop), [explode / posexplode (refresh)](#explode--posexplode-refresh) |
| "Perform data deduplication and validation operations on DataFrames." | [distinct vs dropDuplicates](#distinct-vs-dropduplicates), null handling via `na.drop` (covered below) |
| "Perform operations on DataFrames such as sorting, iterating, printing schema, and conversion between DataFrame and sequence/list formats." | [Sorting](#sorting), [printSchema, dtypes, columns](#printschema-dtypes-columns), [Iteration patterns](#iteration-patterns), [DataFrame to/from list/sequence](#dataframe-tofrom-listsequence) |

---

> 🎯 **How to recognize this on the exam:**
> - If question shows `na.drop()` with no args → drops rows with **ANY** null (same as `na.drop("any")`).
> - If question shows `na.drop("all")` → drops only rows where **ALL** columns are null. This is counter-intuitive.
> - If question shows `na.drop(thresh=N)` → drops rows with **fewer than N non-null** values.
> - If `filter` vs `where` appears → they're **aliases** (identical).
> - If `sort` vs `orderBy` appears → also **aliases**.
> - If `distinct()` vs `dropDuplicates()` (no args) appears → identical behavior; both are WIDE.
> - If `dropDuplicates(subset)` appears → wide; keeps an **arbitrary row** (non-deterministic). For deterministic, use window+`row_number`.
> - If `drop("missing_col")` appears → **silent**, no error.
> - If `monotonically_increasing_id` vs `row_number` → former is unique-but-not-consecutive; latter is consecutive (and requires a window).
> - If chained `withColumn` (5+ calls) vs `select` → exam may prefer single `select` for performance.

---

## The core verbs

```python
# Projection
df.select(*cols)
df.selectExpr(*exprs)

# Filtering
df.filter(cond)
df.where(cond)

# Column manipulation
df.withColumn(name, expr)
df.withColumns({name: expr, ...})
df.withColumnRenamed(old, new)
df.withColumnsRenamed({old: new, ...})        # Spark 3.4+
df.drop(*cols)

# Deduplication
df.distinct()
df.dropDuplicates(subset=None)
df.drop_duplicates(subset=None)                # alias

# Sampling and limits
df.sample(fraction, seed=None)
df.sampleBy(col, fractions_dict, seed=None)    # stratified
df.limit(n)

# Sorting
df.sort(*cols)
df.orderBy(*cols)
df.sortWithinPartitions(*cols)
```

All except `sample` are deterministic. All are **transformations** (lazy).

---

## select — column projection

```python
df.select("a", "b", "c")                       # by name
df.select(F.col("a"), F.col("b"))              # by Column
df.select("a", F.col("b") + 1, F.lit(0).alias("zero"))   # mixed

# Star expansion
df.select("*", F.lit(1).alias("flag"))         # all + new col
df.select("a.*")                               # all fields of struct 'a'

# Aliasing
df.select(F.col("salary").alias("annual_salary"))
df.select((F.col("a") + F.col("b")).alias("sum_ab"))
```

### selectExpr — SQL strings

```python
df.selectExpr("a", "b + 1 AS b_plus_one", "upper(name) AS name_upper")
```

Equivalent to `df.select(F.expr(e) for e in [...])`. Useful when you want SQL flavor.

⚠️ **`select` is narrow.** Just a column projection — no row movement.

---

## filter / where

```python
df.filter(F.col("age") > 30)
df.filter("age > 30")                              # SQL string
df.where(F.col("age") > 30)                        # alias for filter
df.filter((F.col("age") > 30) & (F.col("dept") == "ENG"))
df.filter(F.col("dept").isin("ENG", "DS", "ML"))
df.filter(F.col("name").startswith("Mr"))
df.filter(F.col("name").contains("Smith"))
df.filter(F.col("age").between(20, 60))
df.filter(F.col("notes").isNull())
df.filter(F.col("notes").isNotNull())
df.filter("ts BETWEEN '2025-01-01' AND '2025-12-31'")
```

### filter vs where — they're aliases

```python
df.filter(cond) is df.where(cond)  # same method
```

No semantic difference. Use whichever reads better.

⚠️ **Combine multiple filters with `&`** (not `,` and not chaining):

```python
# Good
df.filter((F.col("a") > 0) & (F.col("b") < 100))

# Also fine (Catalyst combines them)
df.filter("a > 0").filter("b < 100")

# WRONG — Python's `and` doesn't work on Columns
df.filter(F.col("a") > 0 and F.col("b") < 100)  # incorrect; treats first as truthy
```

### Predicate pushdown

Spark pushes filters **down to the file scan** when possible:

```python
df = spark.read.parquet("path")
df.filter(F.col("year") == 2025).explain()
# == Physical Plan ==
# FileScan parquet [..., year] PushedFilters: [IsNotNull(year), EqualTo(year,2025)]
```

The Parquet reader uses min/max statistics in file footers to **skip files entirely** that can't contain matching rows. Module 10 covers this in detail.

---

## withColumn / withColumnRenamed / withColumns

```python
# Add or replace one column
df.withColumn("c", F.col("a") + F.col("b"))
df.withColumn("c_doubled", F.col("c") * 2)     # if c exists, replaces; else adds

# Rename one column
df.withColumnRenamed("old_name", "new_name")

# Add/replace multiple (Spark 3.3+)
df.withColumns({
    "a_plus_1": F.col("a") + 1,
    "b_squared": F.col("b") ** 2,
    "name_upper": F.upper(F.col("name")),
})

# Rename multiple (Spark 3.4+)
df.withColumnsRenamed({"a": "alpha", "b": "beta"})
```

### Chained withColumn anti-pattern (refresh)

```python
# Anti-pattern — N logical-plan nodes
df = (df.withColumn("a", F.col("a") + 1)
        .withColumn("b", F.col("b") * 2)
        .withColumn("c", F.upper(F.col("c"))))

# Better — 1 node
df = df.select(
    (F.col("a") + 1).alias("a"),
    (F.col("b") * 2).alias("b"),
    F.upper(F.col("c")).alias("c"),
    *[c for c in df.columns if c not in ("a", "b", "c")]
)

# Or — withColumns (single call, single node)
df = df.withColumns({
    "a": F.col("a") + 1,
    "b": F.col("b") * 2,
    "c": F.upper(F.col("c")),
})
```

⚠️ **Exam framing:** "Which is more efficient for 10 column derivations?" → single `select` or `withColumns`. Each `withColumn` adds a logical-plan node.

---

## drop

```python
df.drop("c")                                   # one column
df.drop("c", "d", "e")                         # multiple
df.drop(F.col("c"))                            # by Column ref

# Drop fails silently if column doesn't exist
df.drop("nonexistent")                         # OK, no error
```

⚠️ **`drop` is silent on missing columns** — no error if the column isn't there. This is sometimes a source of subtle bugs.

To check existence:

```python
if "c" in df.columns:
    df = df.drop("c")
```

---

## distinct vs dropDuplicates

```python
df.distinct()                                  # full-row dedup
df.dropDuplicates()                            # same as distinct
df.dropDuplicates(["user_id"])                 # dedup by subset
df.dropDuplicates(["user_id", "event_date"])
df.drop_duplicates(subset=["user_id"])         # snake_case alias
```

⚠️ **Both are wide transformations.**

⚠️ **`dropDuplicates(subset)` keeps an arbitrary row per group** — non-deterministic order. If you need a specific row (e.g., latest by timestamp), use window functions:

```python
from pyspark.sql import Window

w = Window.partitionBy("user_id").orderBy(F.col("ts").desc())
df_latest = (df.withColumn("rn", F.row_number().over(w))
               .filter("rn = 1")
               .drop("rn"))
```

---

## Sampling

```python
df.sample(0.1)                                # 10% sample, no seed
df.sample(0.1, seed=42)                       # deterministic with seed
df.sample(withReplacement=False, fraction=0.1, seed=42)
df.sample(withReplacement=True, fraction=2.0, seed=42)   # bootstrap-like

# Stratified sampling
df.sampleBy("country", {"US": 0.1, "CA": 0.2, "MX": 0.05}, seed=42)
```

⚠️ **`sample` is approximate** — `fraction=0.1` doesn't guarantee exactly 10% of rows. Uses Bernoulli sampling per row.

⚠️ **`sample` is narrow** — per-partition sampling, no shuffle.

---

## limit

```python
df.limit(100)                                 # first 100 rows
```

⚠️ **`limit` is a NARROW transformation that becomes an ACTION-like operation due to its semantics.**

In Spark 3.5:
- `limit(n)` runs the query but stops as soon as `n` rows are collected.
- Implemented as `LocalLimit(n)` at executor level → `GlobalLimit(n)` at driver.
- For large pipelines, `limit(10)` can be much cheaper than `count()` because Spark short-circuits.

```python
df.limit(10).show()    # very cheap — stops after 10 rows
```

---

## Sorting

```python
df.sort("salary")                                  # ascending (default)
df.sort("salary", "age")
df.sort(F.col("salary").desc())                    # descending
df.sort(F.col("salary").desc(), F.col("age").asc())
df.orderBy("salary", ascending=False)
df.orderBy("salary", "age", ascending=[False, True])

# Null ordering
df.sort(F.col("salary").desc_nulls_last())         # nulls go last
df.sort(F.col("salary").asc_nulls_first())

# Within-partition sort (NARROW)
df.sortWithinPartitions("ts")
df.sortWithinPartitions(F.col("ts").desc())
```

### sort vs orderBy

**`sort` and `orderBy` are aliases.** Same method. Use whichever reads better in context.

### orderBy is WIDE

`orderBy` produces a globally sorted result, requiring a **range-partition shuffle**. For a 100M-row DataFrame, this is expensive.

### sortWithinPartitions is NARROW

`sortWithinPartitions` sorts each partition's rows independently. Useful for:
- Pre-sorting before a window function with the same partition key.
- Improving Parquet min/max statistics for data skipping on read.
- Bucketed table writes.

```python
# Sort within partition for better data skipping
df.repartition(100, "country") \
  .sortWithinPartitions("event_date") \
  .write.parquet("path")
```

---

## printSchema, dtypes, columns

```python
df.printSchema()
# root
#  |-- id: integer (nullable = true)
#  |-- name: string (nullable = true)
#  |-- address: struct (nullable = true)
#  |    |-- street: string (nullable = true)
#  |    |-- city: string (nullable = true)

df.schema                  # StructType object
df.dtypes                  # [(name, type_str), ...]
df.columns                 # [name, name, ...]
```

### Reading dtypes

```python
df.dtypes
# [('id', 'int'), ('name', 'string'), ('address', 'struct<street:string,city:string>')]
```

⚠️ `printSchema()` does NOT trigger a job. Only inspects the logical plan's schema.

---

## Iteration patterns

```python
# Local iteration (driver-side)
for row in df.collect():
    print(row)

# Lazy iteration (streams partitions to driver)
for row in df.toLocalIterator():
    process(row)

# Per-row action (executor-side, no return)
df.foreach(lambda row: write_to_external_db(row))

# Per-partition (more efficient for batch operations)
def write_partition(rows):
    conn = open_connection()
    for row in rows:
        conn.write(row)
    conn.close()

df.foreachPartition(write_partition)
```

⚠️ **`foreach` and `foreachPartition` are actions** — they trigger execution. They return None (run for side effects).

⚠️ **`foreach` runs in PARALLEL on executors** — order is non-deterministic. For deterministic iteration, `collect()` or `toLocalIterator()`.

---

## Combining DataFrames (preview — full coverage in Module 09)

```python
# union — by POSITION, requires same number of columns
df1.union(df2)
df1.unionAll(df2)                                  # alias

# unionByName — by COLUMN NAME
df1.unionByName(df2)
df1.unionByName(df2, allowMissingColumns=True)     # Spark 3.1+
```

⚠️ **`union` matches by POSITION**:

```python
# df1 schema: id, name
# df2 schema: name, id  ← same column NAMES but DIFFERENT ORDER

df1.union(df2)  # Wrong! Mixes IDs with names
df1.unionByName(df2)  # Correct — matches by column name
```

This is a sample-question topic.

---

## Converting between Row and dict

```python
# Row → dict
row.asDict()                  # {"id": 1, "name": "Alice"}
row.asDict(recursive=True)    # nested structs/arrays also as dicts

# dict → Row
from pyspark.sql import Row
Row(**{"id": 1, "name": "Alice"})
Row(id=1, name="Alice")

# Construct DataFrame from rows
spark.createDataFrame([Row(id=1, name="Alice"), Row(id=2, name="Bob")])
```

---

## DataFrame to/from list/sequence

The exam objective: "Perform operations on DataFrames such as ... conversion between DataFrame and sequence/list formats."

```python
# DataFrame → Python list
rows = df.collect()                       # list of Row
data = [r.asDict() for r in rows]         # list of dict
tuples = [tuple(r) for r in rows]         # list of tuple

# Python list → DataFrame
df = spark.createDataFrame([(1, "a"), (2, "b")], ["id", "name"])
df = spark.createDataFrame([{"id": 1, "name": "a"}], schema="id INT, name STRING")
```

⚠️ **`createDataFrame` on large lists is slow** — Python → Java serialization for every row. For testing, fine; for production, no.

---

## explode / posexplode (refresh)

```python
df.withColumn("tag", F.explode(F.col("tags")))      # array → rows
df.withColumn("tag", F.explode_outer(F.col("tags")))  # keeps null/empty
df.withColumn("idx_tag", F.posexplode(F.col("tags")))  # adds position

# For maps
df.withColumn("kv", F.explode(F.col("attrs")))  # produces struct (key, value)
```

⚠️ `explode` is a **wide-looking but actually narrow** operation in terms of data flow — it doesn't shuffle, but it does change row count. Catalyst classifies it as a generator function.

---

## Column expressions

You can build columns from other columns:

```python
df.withColumn("derived", F.col("a") + F.col("b") * 2)
df.withColumn("conditional",
    F.when(F.col("a") > 100, F.col("a")).otherwise(F.lit(0)))

# String concatenation
df.withColumn("full_name", F.concat_ws(" ", F.col("first"), F.col("last")))

# Multiplication/arithmetic
df.withColumn("price_with_tax", F.col("price") * F.lit(1.08))

# Comparison
df.withColumn("is_adult", F.col("age") >= 18)
```

⚠️ **Operator overload caveats:**
- `+`, `-`, `*`, `/`, `%`, `**`, comparison operators work on Columns.
- Boolean: `&`, `|`, `~`.
- Don't use Python's `and`, `or`, `not`.

---

## Adding row identifiers

```python
# Monotonically increasing ID — UNIQUE but NOT consecutive
df.withColumn("id", F.monotonically_increasing_id())

# Row number per partition (use window for global)
from pyspark.sql import Window
df.withColumn("rn", F.row_number().over(Window.orderBy("ts")))
```

⚠️ **`monotonically_increasing_id` is NOT consecutive** across partitions. The values are unique but have gaps (each partition gets a range). It's not equivalent to SQL's `ROW_NUMBER()`.

---

## Worked example: typical transformation pipeline

```python
df_clean = (df
    .filter(F.col("amount").isNotNull())
    .filter(F.col("amount") > 0)
    .withColumn("year", F.year(F.col("created_at")))
    .withColumn("month", F.month(F.col("created_at")))
    .withColumn("amount_usd", F.col("amount") * F.col("exchange_rate"))
    .drop("exchange_rate")
    .dropDuplicates(["order_id"])
    .sortWithinPartitions("created_at"))

# All of the above is lazy. Nothing executes until:
df_clean.write.partitionBy("year", "month").parquet("output/")
```

Notice:
- All steps are **narrow** until `dropDuplicates` (which is wide).
- `sortWithinPartitions` is narrow — sorts each shuffle-result partition.
- The final `.write` triggers execution.

---

## `na.drop` variants — the table to memorize

The sample Q6 trap (`na.drop("all")` vs `na.drop()`) lives here.

```python
df = spark.createDataFrame([
    (1, "a", 100),       # no nulls
    (2, None, 200),      # 1 null
    (3, None, None),     # 2 nulls
    (None, None, None),  # all null
], ["id", "name", "amount"])
```

| Call | Behavior | Rows kept | Result count |
|---|---|---|---|
| `df.na.drop()` | Drop ANY row with at least one null (default) | row 1 only | **1** |
| `df.na.drop("any")` | Same as default | row 1 only | **1** |
| `df.na.drop("all")` | Drop only rows where **ALL** cols are null | rows 1, 2, 3 | **3** |
| `df.na.drop(thresh=2)` | Drop rows with fewer than 2 non-null values | rows 1, 2 (3 has 1 non-null) | **2** |
| `df.na.drop(subset=["name"])` | Drop rows where `name` is null | row 1 only (row 2-4 have null name) | **1** |
| `df.na.drop("any", subset=["id"])` | Drop rows where `id` is null | rows 1, 2, 3 | **3** |
| `df.na.drop("all", subset=["name", "amount"])` | Drop rows where BOTH name AND amount are null | rows 1, 2 | **2** |

⚠️ **`"all"` means "the row must be ENTIRELY null to be dropped"** — opposite of what English intuition suggests.

---

## Output-prediction drills

### Drill 1 — `na.drop` row counts

```python
data = [
    ("a", 1, 100),
    (None, 2, 200),
    ("c", None, 300),
    (None, None, 400),
    (None, None, None),
]
df = spark.createDataFrame(data, ["name", "id", "amount"])

df.na.drop().count()                                    # ?
df.na.drop("all").count()                               # ?
df.na.drop(thresh=2).count()                            # ?
df.na.drop(subset=["name"]).count()                     # ?
df.na.drop("any", subset=["name", "id"]).count()        # ?
```

**A:**
- `.na.drop()` → **1** (only the first row has zero nulls).
- `.na.drop("all")` → **4** (only the last row is entirely null).
- `.na.drop(thresh=2)` → **4** (need ≥2 non-null values; row 1 has 3, rows 2,3 have 2, row 4 has 1 — DROPPED, row 5 has 0 — DROPPED). Wait: rows with ≥2 non-null: row 1 (3), row 2 (2), row 3 (2), row 4 (1 - drop), row 5 (0 - drop). So **3**.

Let me redo: row 1 = (a, 1, 100) 3 non-null. Row 2 = (None, 2, 200) 2 non-null. Row 3 = (c, None, 300) 2 non-null. Row 4 = (None, None, 400) 1 non-null. Row 5 = all null, 0. With thresh=2, keep rows with ≥2 non-null: rows 1, 2, 3 → **3**.

- `.na.drop(subset=["name"])` → **2** (rows where name is non-null: rows 1, 3).
- `.na.drop("any", subset=["name", "id"])` → **1** (rows where BOTH name AND id are non-null: row 1).

### Drill 2 — `distinct` vs `dropDuplicates`

```python
df = spark.createDataFrame([
    (1, "a", 100), (1, "a", 100), (1, "a", 200),
    (2, "b", 200), (2, "c", 200),
], ["id", "name", "amt"])

df.distinct().count()                              # ?
df.dropDuplicates().count()                        # ?
df.dropDuplicates(["id"]).count()                  # ?
df.dropDuplicates(["id", "name"]).count()          # ?
```

**A:**
- `distinct()` → **4** (full-row dedup; only the two identical (1,a,100) rows collapse).
- `dropDuplicates()` → **4** (same as distinct).
- `dropDuplicates(["id"])` → **2** (one row per id).
- `dropDuplicates(["id", "name"])` → **3** ((1,a), (2,b), (2,c)).

### Drill 3 — `sample` with seed

```python
df = spark.range(0, 1000).repartition(4)
df.sample(0.5, seed=42).count()                    # approximately?
df.sample(withReplacement=False, fraction=0.1, seed=1).count()    # approximately?
df.sample(withReplacement=True, fraction=2.0, seed=1).count()     # approximately?
```

**A:**
- `sample(0.5)` → **~500** (50% Bernoulli sample; could be 480, 510, etc.).
- `sample(0.1)` → **~100**.
- `sample(withReplacement=True, fraction=2.0)` → **~2000** (Poisson sampling with replacement; expected = N × fraction).

Sampling is approximate, NOT exactly N × fraction rows.

### Drill 4 — `limit` and stage skipping

```python
df = spark.read.parquet("100_GB/")
df.limit(10).count()      # how much data does Spark scan?
df.limit(10).show()       # how much data does Spark scan?
```

**A:** Spark short-circuits with `limit`. It scans only enough partitions to produce 10 rows (typically one partition). May scan as little as a few MB on a 100 GB dataset.

### Drill 5 — `sort` vs `sortWithinPartitions`

```python
df = spark.range(0, 100).repartition(4)

df.sort("id").rdd.getNumPartitions()                  # ?
df.sortWithinPartitions("id").rdd.getNumPartitions()  # ?
df.sort("id").rdd.glom().collect()                    # globally sorted?
df.sortWithinPartitions("id").rdd.glom().collect()    # globally sorted?
```

**A:**
- `sort("id")` → **200** partitions (default `spark.sql.shuffle.partitions`); globally sorted (each partition has a disjoint range).
- `sortWithinPartitions("id")` → **4** partitions (unchanged); each partition's rows sorted internally, but NOT globally sorted.

### Drill 6 — `monotonically_increasing_id` gaps

```python
df = spark.range(0, 10).repartition(3)
df.withColumn("mono_id", F.monotonically_increasing_id()).show()
```

**A:** Each partition gets a base offset, then values are 0, 1, 2... within partition. So you might see IDs like:
- Partition 0: 0, 1, 2, 3
- Partition 1: 8589934592, 8589934593, 8589934594 (offset = 2^33)
- Partition 2: 17179869184, 17179869185, 17179869186

**Unique but NOT consecutive.** For consecutive 0,1,2,…, use `row_number().over(Window.orderBy(...))` — but that forces a single partition. Costly.

### Drill 7 — `union` after `repartition`

```python
df1 = spark.range(0, 100).repartition(4)
df2 = spark.range(100, 200).repartition(6)
combined = df1.union(df2)

combined.rdd.getNumPartitions()       # ?
combined.distinct().rdd.getNumPartitions()  # ?
```

**A:**
- `union` partitions → **10** (4 + 6; narrow concatenation).
- `union.distinct()` → **200** (`distinct` is wide → shuffles to `spark.sql.shuffle.partitions`).

---

## Mini-quiz

1. Is `filter` the same as `where`?
2. What's the difference between `withColumn` and `withColumnRenamed`?
3. When you call `df.dropDuplicates(["user_id"])`, which row in each group is kept?
4. Is `df.sortWithinPartitions("ts")` narrow or wide?
5. Why is `df.sample(0.1)` an approximate operation?
6. What does `F.monotonically_increasing_id()` return?
7. What's the difference between `union` and `unionByName`?
8. Does `df.drop("nonexistent_col")` raise an error?
9. Why is chained `withColumn` slower than a single `select`?
10. What does `selectExpr("a + 1 AS b")` do?

### Answers

1. **Yes** — aliases of the same method.
2. **`withColumn(name, expr)`** adds or replaces a column with the given expression. **`withColumnRenamed(old, new)`** renames a column (schema-only, no data change).
3. **Arbitrary row** — non-deterministic. For a specific row (e.g., latest), use window functions.
4. **Narrow.** Sorts within each partition independently; no shuffle.
5. Spark uses **Bernoulli sampling** per row — each row is independently kept with probability `fraction`. Total count is approximately `n × fraction` but not exact.
6. A **unique but NOT consecutive** Long ID per row. Different partitions get different ranges; gaps between ranges.
7. **`union` matches columns by POSITION**; **`unionByName` matches by column NAME**.
8. **No error.** `drop` is silent on missing columns.
9. Each `withColumn` adds a logical-plan node; Catalyst traverses more nodes during optimization. A single `select` (or `withColumns`) produces one node.
10. Equivalent to `df.select(F.expr("a + 1").alias("b"))`. Parses the SQL expression and returns the result as a Column named `b`.

---

## Exam-day cheat sheet

- **`filter` and `where` are aliases.**
- **`sort` and `orderBy` are aliases.**
- **`distinct` ≡ `dropDuplicates()` (no subset).**
- **`union` matches by POSITION**; **`unionByName` matches by NAME.**
- **`drop` is silent on missing columns.**
- **`limit(n)` is cheap** — Spark short-circuits.
- **`sample(fraction)` is approximate** — Bernoulli per row.
- **`monotonically_increasing_id` is NOT consecutive.**
- **`sortWithinPartitions` is NARROW**; **`orderBy` is WIDE.**
- **`withColumns({...})`** (3.3+) replaces many chained `withColumn` calls.
- **`F.col("a") & F.col("b")`** — use `&` not Python `and`.
- **`dropDuplicates(subset)` keeps an arbitrary row** — use window for deterministic.

Next: [Module 08 — Aggregations and Window Functions](08_aggregations_window.md).
