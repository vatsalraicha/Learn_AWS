# Module 05 — Spark SQL Functions

> **Domain 2 of 7 — Using Spark SQL (20%).**
> **Goal:** Master the built-in Spark SQL functions library (`pyspark.sql.functions as F`). The exam asks code-recognition questions where 3 distractors have wrong function names, wrong argument orders, or wrong return types. Memorize the canonical signatures.

---

## Coverage map

Verbatim Oct 2025 exam objectives covered by this module:

| Objective | Section |
|---|---|
| (Section 3) "Manipulate columns ... by adding, dropping, splitting, renaming column names, applying filters, and exploding arrays." | [Column references](#column-references), [withColumn vs withColumnRenamed vs withColumns](#withcolumn-vs-withcolumnrenamed-vs-withcolumns), [drop, distinct, dropDuplicates](#drop-distinct-dropduplicates), [Array functions](#array-functions), [Explode and posexplode](#explode-and-posexplode) |
| (Section 3) "Manipulate and utilize Date data type, such as Unix epoch to date string, and extract date component." | [Date and timestamp functions](#date-and-timestamp-functions) |
| (Section 2) "Execute SQL queries directly on files ... and understand the different save modes for outputting data in Spark SQL." | [expr() — embed SQL](#expr--embed-sql) and Module 04 (basics) |

---

> 🎯 **How to recognize this on the exam:**
> - If `coalesce` appears ambiguous → SQL function `F.coalesce(c1, c2)` returns first non-null **value**; DataFrame method `df.coalesce(n)` reduces **partitions**. Same name, different things.
> - If `F.concat(c1, NULL, c3)` appears → returns NULL (any null poisons). Use `F.concat_ws(sep, ...)` to skip nulls.
> - If casting bad data → returns NULL silently in Spark 3.5 (pre-ANSI default).
> - If question asks "Unix epoch to date string" → `F.date_format(F.from_unixtime(col), "yyyy-MM-dd")`. NOT `F.to_date(epoch)` (to_date expects a string).
> - If Python `and`/`or`/`not` appears in column boolean expressions → **WRONG**. Must use `&`, `|`, `~` with parens around comparisons.
> - If `F.lit(None)` appears → typed NULL column.
> - If `F.explode` vs `F.explode_outer` → former drops rows with empty/null arrays; latter keeps them (emits NULL).
> - If `when(...).when(...).otherwise()` → matches first true; without `.otherwise()`, non-matching rows get NULL.
> - If date format strings → uses Java SimpleDateFormat-ish syntax (`yyyy-MM-dd HH:mm:ss`, NOT Python's `%Y-%m-%d`).
> - If `withColumn` appears 10 times in a chain → exam may prefer single `select` or `withColumns(dict)`.

---

## Why this module exists

Spark SQL ships with 400+ built-in functions. The exam draws from a narrower set — date/time, string, conditional, type casting, JSON, arrays, structs, and the "trap" function pairs (the function `coalesce` vs the DataFrame method `coalesce`; `withColumn` vs `withColumnRenamed`).

We organize by category. By the end you should be able to write any standard transformation without IDE autocomplete.

---

## The conventional import

```python
from pyspark.sql import functions as F
from pyspark.sql import types as T
```

Functions are typically called as `F.<name>(args)`. Returns a `Column` object — chainable, composable.

---

## Column references

```python
F.col("name")             # column reference by name
df["name"]                # equivalent
F.col("a") + F.col("b")   # arithmetic returns a Column
F.expr("a + b")           # SQL expression as Column

# Aliasing
F.col("name").alias("full_name")
F.col("salary").alias("annual_salary")
```

⚠️ **`F.col` vs `df.col`:** both reference a column, but `F.col` is **table-agnostic** — useful in joins where two DataFrames have same-named columns. `df.col` (or `df["col"]`) is **bound** to a specific DataFrame.

```python
# Ambiguity in joins
df1.join(df2, df1["id"] == df2["id"]).select(df1["name"])  # safe — bound
df1.join(df2, "id").select(F.col("name"))                  # ambiguous if both have "name"
```

---

## Literals and casts

```python
F.lit(0)                  # literal Integer 0
F.lit("hello")            # literal String
F.lit(None)               # literal NULL
F.lit(True).cast("string") # "true"

F.col("amount").cast("double")
F.col("amount").cast("decimal(10, 2)")
F.col("ts").cast("timestamp")
F.col("d").cast("date")
F.col("v").cast(T.IntegerType())   # using PySpark types
```

### Common cast targets

| String | Type |
|---|---|
| `"string"` | StringType |
| `"int"` / `"integer"` | IntegerType |
| `"bigint"` / `"long"` | LongType |
| `"double"` | DoubleType |
| `"float"` | FloatType |
| `"decimal(10, 2)"` | DecimalType(10, 2) |
| `"boolean"` | BooleanType |
| `"date"` | DateType |
| `"timestamp"` | TimestampType |
| `"binary"` | BinaryType |
| `"array<int>"` | ArrayType(IntegerType) |
| `"map<string, int>"` | MapType(StringType, IntegerType) |
| `"struct<a: int, b: string>"` | StructType |

⚠️ **Cast failures** in Spark 3.5 (pre-ANSI default) return **NULL** silently. Spark 4.0 changes this default. Not on this exam.

---

## Conditional expressions

### when / otherwise

```python
df.withColumn("tier",
    F.when(F.col("amount") > 1000, "premium")
     .when(F.col("amount") > 100, "standard")
     .otherwise("basic"))
```

Equivalent SQL:

```sql
CASE
  WHEN amount > 1000 THEN 'premium'
  WHEN amount > 100 THEN 'standard'
  ELSE 'basic'
END AS tier
```

⚠️ **Without `otherwise`**, the column is `NULL` for non-matching rows. Easy bug.

### coalesce (function — NOT the partition method!)

```python
F.coalesce(F.col("a"), F.col("b"), F.lit(0))
```

Returns the **first non-null value** in the argument list. Equivalent to `CASE WHEN a IS NOT NULL THEN a WHEN b IS NOT NULL THEN b ELSE 0 END`.

⚠️ **THE big naming trap of the exam.**

| | DataFrame method `coalesce(n)` | SQL function `F.coalesce(col1, col2)` |
|---|---|---|
| Returns | DataFrame with n partitions | Column (first non-null value) |
| Purpose | Partition reduction (narrow) | Null handling |
| Signature | `df.coalesce(int)` | `F.coalesce(*cols)` |

Same name. Totally different things.

### Other null helpers

```python
F.isnan(F.col("x"))                 # is NaN (floats)
F.isnull(F.col("x"))                # is null
F.col("x").isNull()                 # equivalent
F.col("x").isNotNull()
F.col("x").eqNullSafe(F.lit(0))     # <=> null-safe equality
F.nvl(col, default)                 # alias for coalesce
F.nullif(col, value)                # NULL if col == value
```

### Boolean operators on columns

```python
F.col("a") & F.col("b")             # AND
F.col("a") | F.col("b")             # OR
~F.col("a")                         # NOT
F.col("x").isin(1, 2, 3)
F.col("x").between(10, 100)
F.col("name").like("%Smith%")
F.col("name").rlike("^[A-Z]+$")
F.col("name").startswith("Mr")
F.col("name").endswith("Jr")
F.col("name").contains("Doe")
```

⚠️ **Use `&` `|` `~` for column-level boolean — NOT `and` `or` `not`.** Python's `and`/`or` short-circuit on truthiness and don't work on Columns.

```python
# WRONG — Python evaluates and treats Column objects as truthy
df.filter(F.col("a") > 0 and F.col("b") > 0)   # incorrect

# RIGHT — & creates a column-level AND
df.filter((F.col("a") > 0) & (F.col("b") > 0))   # correct
```

Parens around each comparison are required because `&` has higher precedence than `>`.

---

## expr() — embed SQL

```python
df.withColumn("full", F.expr("first_name || ' ' || last_name"))
df.selectExpr("first_name || ' ' || last_name AS full")
df.filter(F.expr("salary > 50000 AND dept = 'ENG'"))
```

`F.expr(string)` parses a Spark SQL expression and returns a Column. Useful for:
- Concise multi-column expressions.
- SQL operators not exposed as Python (`||` for string concat, though `F.concat` exists).
- Using built-in functions by name without importing them.

⚠️ **`selectExpr(*strs)` is equivalent to `select(F.expr(s) for s in strs)`** — takes multiple SQL expression strings.

---

## String functions

```python
F.upper(col)                     # UPPER
F.lower(col)
F.length(col)                    # character length
F.trim(col), F.ltrim(col), F.rtrim(col)
F.concat(c1, c2, c3)             # concatenate (returns NULL if any input is NULL)
F.concat_ws(sep, c1, c2)         # concat with separator (skips NULLs)
F.substring(col, pos, len)       # 1-indexed
F.substr(col, pos, len)          # same; alias
F.split(col, pattern)            # returns array
F.regexp_replace(col, pattern, replacement)
F.regexp_extract(col, pattern, idx)
F.translate(col, "abc", "xyz")
F.lpad(col, n, ch), F.rpad(col, n, ch)
F.repeat(col, n)
F.format_string("%05d-%s", c1, c2)   # printf-style
F.format_number(col, decimals)
F.instr(col, substring)              # index of substring (1-based, 0 if not found)
F.locate(substring, col, pos)        # find substring starting at pos
F.initcap(col)                       # title case
F.reverse(col)
F.encode(col, "utf-8"), F.decode(col, "utf-8")
F.base64(col), F.unbase64(col)
F.md5(col), F.sha1(col), F.sha2(col, 256)
F.hash(*cols)                        # Spark hash for partitioning
```

### concat vs concat_ws — null handling trap

```python
F.concat(F.lit("a"), F.lit(None), F.lit("c"))      # → NULL (any null poisons)
F.concat_ws(",", F.lit("a"), F.lit(None), F.lit("c"))  # → "a,c" (skips null)
```

⚠️ **`concat` returns NULL if ANY arg is NULL.** `concat_ws` skips nulls.

---

## Date and timestamp functions

### Current values

```python
F.current_date()                 # DateType, UTC today
F.current_timestamp()            # TimestampType, now
F.now()                          # alias for current_timestamp
```

### Parsing strings → date/timestamp

```python
F.to_date(col, "yyyy-MM-dd")
F.to_timestamp(col, "yyyy-MM-dd HH:mm:ss")
F.to_date(F.col("d"))            # uses default format yyyy-MM-dd

F.unix_timestamp(col, fmt)       # epoch seconds
F.from_unixtime(epoch_col)       # epoch → "yyyy-MM-dd HH:mm:ss" string
F.from_unixtime(epoch_col, "yyyy-MM-dd")  # custom format
F.from_utc_timestamp(ts, "America/Los_Angeles")
F.to_utc_timestamp(ts, "America/Los_Angeles")
```

### Formatting date/timestamp → string

```python
F.date_format(col, "yyyy-MM-dd")
F.date_format(col, "EEEE, MMMM d, yyyy")   # "Friday, May 23, 2026"
```

### Arithmetic

```python
F.date_add(col, days)            # add days
F.date_sub(col, days)            # subtract days
F.datediff(end_col, start_col)   # days between (integer)
F.months_between(end, start)     # months between (double)
F.add_months(col, n)
F.next_day(col, "Sunday")        # next given day of week
F.last_day(col)                  # last day of month containing col
F.trunc(col, "MONTH")            # truncate date to month start
F.date_trunc("hour", ts)         # truncate timestamp to hour
```

### Extracting components

```python
F.year(col)
F.month(col)
F.dayofmonth(col)
F.dayofweek(col)                 # 1=Sunday, 7=Saturday (Java convention)
F.dayofyear(col)
F.weekofyear(col)
F.hour(col)
F.minute(col)
F.second(col)
F.quarter(col)
```

### Difference helpers

```python
F.datediff(F.col("end"), F.col("start"))    # days
F.months_between(F.col("end"), F.col("start"))  # months (with fractional part)
(F.col("end_ts").cast("long") - F.col("start_ts").cast("long"))  # seconds (manual)
```

⚠️ **Exam framing:** the exam guide explicitly calls out "Manipulate and utilize Date data type, such as Unix epoch to date string, and extract date component." Expect questions like:

> "Which expression converts the Unix epoch seconds column `ts_epoch` to a date string `yyyy-MM-dd`?"
>
> Correct: `F.date_format(F.from_unixtime(F.col("ts_epoch")), "yyyy-MM-dd")`
>
> Distractors: `F.to_date(F.col("ts_epoch"))` (wrong — to_date expects a string), `F.from_unixtime(F.col("ts_epoch"))` (wrong format string).

---

## Array functions

```python
F.array(c1, c2, c3)                       # construct array
F.array_contains(arr_col, value)
F.size(arr_col)                           # array length
F.array_distinct(arr_col)
F.array_intersect(arr1, arr2)
F.array_union(arr1, arr2)
F.array_except(arr1, arr2)
F.array_position(arr_col, value)          # 1-based; 0 if not found
F.array_remove(arr_col, value)
F.sort_array(arr_col, asc=True)
F.shuffle(arr_col)
F.slice(arr_col, start, length)           # 1-based
F.concat(arr1, arr2)                      # array concat (yes, overloaded!)
F.element_at(arr_col, idx)                # 1-based; supports negative (from end)
F.flatten(F.col("arr_of_arrs"))           # nested array → flat
F.aggregate(arr, F.lit(0), lambda acc, x: acc + x)  # fold over array
F.transform(arr, lambda x: x * 2)         # map over array
F.filter(arr, lambda x: x > 0)            # filter array
F.exists(arr, lambda x: x > 100)          # any
F.forall(arr, lambda x: x > 0)            # all
F.zip_with(arr1, arr2, lambda a, b: a + b)
```

### Explode and posexplode

```python
df.select("id", F.explode(F.col("tags")).alias("tag"))
df.select("id", F.posexplode(F.col("tags")).alias("idx", "tag"))
df.select("id", F.explode_outer(F.col("tags")))   # keeps rows with empty/null arrays
df.select("id", F.posexplode_outer(F.col("tags")))
```

⚠️ **`explode` vs `explode_outer`:** `explode` drops rows where the array is empty or null; `explode_outer` keeps them with a NULL value.

`explode` converts one row with an N-element array into N rows. The DataFrame gets bigger — be aware of this in joins.

---

## Map functions

```python
F.create_map(F.lit("k1"), F.col("v1"), F.lit("k2"), F.col("v2"))
F.map_keys(map_col)
F.map_values(map_col)
F.map_from_arrays(keys_arr, values_arr)
F.map_concat(m1, m2)
F.map_entries(map_col)        # array of {key, value} structs
F.element_at(map_col, "key")  # get value (alias for map[key])
```

---

## Struct functions

```python
F.struct(F.col("a"), F.col("b"))
F.struct(F.col("a").alias("x"), F.col("b").alias("y"))

# Accessing nested fields
df.select(F.col("address.street"))
df.select(F.col("address")["street"])

# Modifying struct fields
df.withColumn("address",
    F.col("address").withField("street", F.upper(F.col("address.street")))
)
```

---

## JSON functions

```python
# Parse JSON string → struct
schema = "name STRING, age INT"
df.withColumn("parsed", F.from_json(F.col("json_str"), schema))

# Or with StructType
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
schema = StructType([
    StructField("name", StringType()),
    StructField("age", IntegerType()),
])
df.withColumn("parsed", F.from_json(F.col("json_str"), schema))

# Serialize struct → JSON string
df.withColumn("json", F.to_json(F.col("struct_col")))

# Extract a single path
df.withColumn("name", F.get_json_object(F.col("json_str"), "$.name"))

# Get the schema from a JSON string
schema_str = F.schema_of_json(F.lit('{"name":"a","age":1}'))
```

⚠️ **`from_json` returns NULL** if the input is unparseable (without ANSI mode). Always check with `F.col("parsed").isNull()`.

---

## Aggregation functions (preview — covered in Module 08)

```python
F.count("*"), F.count(col), F.count_distinct(col)
F.sum(col), F.avg(col), F.mean(col)   # mean is alias for avg
F.min(col), F.max(col)
F.stddev(col), F.stddev_pop(col), F.stddev_samp(col)
F.variance(col), F.var_pop(col), F.var_samp(col)
F.first(col, ignorenulls=True)
F.last(col, ignorenulls=True)
F.collect_list(col)              # array of values (with duplicates)
F.collect_set(col)               # array of distinct values
F.approx_count_distinct(col, rsd=0.05)   # HyperLogLog
F.skewness(col), F.kurtosis(col)
F.corr(c1, c2), F.covar_pop(c1, c2), F.covar_samp(c1, c2)
F.percentile_approx(col, [0.5, 0.95], accuracy=10000)
```

⚠️ **`F.collect_list` materializes the entire group into an array** — risky for large groups (driver-side memory).

⚠️ **`approx_count_distinct`** uses HyperLogLog++ to give a ~5% error estimate without shuffling the entire distinct set. Sample question #10 in the official guide tests this.

---

## broadcast (the function — join hint)

```python
big.join(F.broadcast(small), "id")
```

`F.broadcast(df)` marks `df` for broadcast hash join. Same name as `sc.broadcast(value)` (broadcast variable) but **different mechanism**.

| | `sc.broadcast(py_value)` | `F.broadcast(df)` |
|---|---|---|
| Type | Read-only Python object | DataFrame join hint |
| Use | Lookup dicts in UDFs | Broadcast hash join |
| Access | `bv.value` on executor | Internal — Spark uses it |

Module 09 covers broadcast joins.

---

## withColumn vs withColumnRenamed vs withColumns

```python
df.withColumn("new_col", F.col("a") + 1)              # add or replace one column
df.withColumnRenamed("old_name", "new_name")          # rename one column (schema-only)
df.withColumns({"a": F.col("a") * 2, "b": F.col("b") + 1})  # multi-column add/replace (Spark 3.3+)
```

⚠️ **Many chained `withColumn` calls is anti-pattern**:

```python
# Anti-pattern — verbose, harder for Catalyst
df = df.withColumn("a", F.col("a") + 1)
df = df.withColumn("b", F.col("b") * 2)
df = df.withColumn("c", F.upper(F.col("c")))

# Better — single select
df = df.select(
    (F.col("a") + 1).alias("a"),
    (F.col("b") * 2).alias("b"),
    F.upper(F.col("c")).alias("c"),
    *[c for c in df.columns if c not in ("a", "b", "c")]
)

# Or — withColumns (Spark 3.3+)
df = df.withColumns({
    "a": F.col("a") + 1,
    "b": F.col("b") * 2,
    "c": F.upper(F.col("c")),
})
```

⚠️ **Exam framing:** "Why is chained `withColumn` slower than a single `select`?" — each `withColumn` adds a logical-plan node; Catalyst has to traverse more nodes for the same result. For pipelines with many derivations, prefer `select` or `withColumns`.

---

## drop, distinct, dropDuplicates

```python
df.drop("col1")                              # remove column
df.drop("col1", "col2")                      # multiple
df.distinct()                                # full-row dedup (WIDE)
df.dropDuplicates()                          # same as distinct
df.dropDuplicates(["user_id"])               # dedup by subset (WIDE)
df.dropDuplicates(["user_id", "event_ts"])
```

⚠️ **`distinct` and `dropDuplicates` are wide transformations** (Module 02).

⚠️ **`dropDuplicates(subset)` keeps an arbitrary row** for each group — non-deterministic. If you need a specific row (e.g., latest by timestamp), use window functions (Module 08).

---

## Filtering

```python
df.filter(F.col("age") > 30)
df.filter("age > 30")                          # SQL string
df.where(F.col("age") > 30)                    # alias for filter
df.filter((F.col("age") > 30) & (F.col("dept") == "ENG"))
df.filter(F.col("dept").isin("ENG", "DS"))
df.filter(F.col("name").like("%Smith%"))
df.filter(F.col("age").between(20, 30))
df.filter(F.col("name").isNotNull())
```

`filter` and `where` are **identical** — same method, different aliases.

---

## Sorting

```python
df.sort("salary")                              # ascending
df.sort(F.col("salary").desc())
df.orderBy("salary", "age")                    # ascending by both
df.orderBy(F.col("salary").desc(), F.col("age").asc())
df.sort(F.col("salary").desc_nulls_last())     # nulls handling
df.sort(F.col("salary").asc_nulls_first())
df.sortWithinPartitions("ts")                  # NARROW (per-partition sort)
```

`sort` and `orderBy` are **identical**.

⚠️ **`orderBy` is wide** (global ordering). **`sortWithinPartitions` is narrow.**

---

## Output-prediction drills

### Drill 1 — `coalesce` (function) and nulls

```python
df = spark.createDataFrame([(None, 1, 100), (2, None, 200), (None, None, 300), (None, None, None)],
                            ["a", "b", "c"])

df.select(F.coalesce("a", "b", "c").alias("v")).collect()
```

**A:**
```
Row 1: 1   (a is null, b is 1)
Row 2: 2   (a is 2)
Row 3: 300 (a, b null; c is 300)
Row 4: NULL (all null)
```

### Drill 2 — `concat` vs `concat_ws` null behavior

```python
df = spark.createDataFrame([("a", None, "c")], ["x", "y", "z"])

df.select(F.concat("x", "y", "z").alias("c1")).first()[0]                # ?
df.select(F.concat_ws("-", "x", "y", "z").alias("c2")).first()[0]        # ?
df.select(F.concat(F.col("x"), F.lit("|"), F.col("z")).alias("c3")).first()[0]   # ?
```

**A:**
- `concat("x", "y", "z")` → **NULL** (any null arg poisons).
- `concat_ws("-", "x", "y", "z")` → **"a-c"** (skips null).
- `concat(x, "|", z)` → **"a|c"** (no nulls in args).

### Drill 3 — Cast failures

```python
df = spark.createDataFrame([("123",), ("abc",), (None,)], ["s"])
df.withColumn("i", F.col("s").cast("int")).collect()
```

**A:** (Spark 3.5, pre-ANSI default)
```
Row 1: s="123", i=123
Row 2: s="abc", i=NULL    ← cast failure → NULL (silent)
Row 3: s=NULL,  i=NULL
```

⚠️ Spark 4.0 changes this default to throw — but exam is 3.5, so NULL is expected.

### Drill 4 — Unix epoch ↔ date

```python
df = spark.createDataFrame([(1735689600,)], ["epoch"])    # Jan 1 2025 UTC

df.select(F.from_unixtime("epoch").alias("dt_str")).first()[0]                   # ?
df.select(F.date_format(F.from_unixtime("epoch"), "yyyy-MM-dd").alias("d")).first()[0]  # ?
df.select(F.to_date(F.from_unixtime("epoch")).alias("d")).first()[0]             # ?
df.select(F.to_date(F.col("epoch")).alias("d")).first()[0]                       # ?
```

**A:**
- `from_unixtime("epoch")` → `"2025-01-01 00:00:00"` (string).
- `date_format(from_unixtime(...), "yyyy-MM-dd")` → `"2025-01-01"` (string).
- `to_date(from_unixtime(...))` → `2025-01-01` (DateType).
- `to_date(F.col("epoch"))` → **NULL** (because to_date expects a string, and the int doesn't parse via the default format `yyyy-MM-dd`).

⚠️ The exam loves this trap: `to_date` does NOT accept epoch seconds directly. You must convert via `from_unixtime` first.

### Drill 5 — Boolean column expressions

```python
df = spark.createDataFrame([(5, 50), (15, 200), (0, 0)], ["a", "b"])

df.filter(F.col("a") > 0 and F.col("b") < 100).count()           # ?
df.filter((F.col("a") > 0) & (F.col("b") < 100)).count()         # ?
df.filter(F.col("a") > 0 & F.col("b") < 100).count()             # ?
```

**A:**
- `F.col("a") > 0 and F.col("b") < 100` → **Python `and` short-circuits** on truthiness. Treats `F.col("a") > 0` as truthy → returns `F.col("b") < 100`. **Result: 1** (only the row with b<100, which is the first row, kept). BUT this is a logic bug; depends on Spark version, may also error.
- `(F.col("a") > 0) & (F.col("b") < 100)` → **1** (row 1). Correct expression.
- `F.col("a") > 0 & F.col("b") < 100` → **Operator precedence error.** `&` binds tighter than `>`, so this parses as `F.col("a") > (0 & F.col("b")) < 100` → mostly garbage; usually throws.

Always: `&`, `|`, `~` with parens.

### Drill 6 — `when` without `otherwise`

```python
df = spark.createDataFrame([(50,), (150,), (1500,)], ["amt"])

df.withColumn("tier",
    F.when(F.col("amt") > 1000, "premium")
     .when(F.col("amt") > 100, "standard")
).collect()
```

**A:**
```
Row 1: amt=50,   tier=NULL    ← no match, no otherwise → NULL
Row 2: amt=150,  tier="standard"
Row 3: amt=1500, tier="premium"
```

Without `.otherwise(default)`, non-matching rows get **NULL**.

### Drill 7 — `explode` vs `explode_outer`

```python
df = spark.createDataFrame([
    (1, ["a", "b"]),
    (2, []),
    (3, None),
], ["id", "tags"])

df.select("id", F.explode("tags")).count()         # ?
df.select("id", F.explode_outer("tags")).count()   # ?
```

**A:**
- `explode("tags")` → **2** rows (id=1 gives 2 rows; id=2 and id=3 dropped because empty/null arrays).
- `explode_outer("tags")` → **4** rows (id=1 → 2 rows; id=2 and id=3 → 1 row each with NULL tag).

### Drill 8 — `date_add` / `datediff`

```python
df = spark.createDataFrame([("2025-01-01", "2025-12-31")], ["start", "end"])

df.select(F.datediff("end", "start").alias("days")).first()[0]            # ?
df.select(F.date_add("start", 30).alias("d")).first()[0]                  # ?
df.select(F.months_between("end", "start").alias("m")).first()[0]         # ?
df.select(F.add_months("start", 3).alias("d3")).first()[0]                # ?
```

**A:**
- `datediff("end", "start")` → **364** (end minus start; positive). Note ordering: `datediff(later, earlier)`.
- `date_add("start", 30)` → `2025-01-31`.
- `months_between("end", "start")` → **~11.97** (a double, fractional part).
- `add_months("start", 3)` → `2025-04-01`.

⚠️ `datediff` and `months_between` BOTH take args as `(end, start)` — easy to swap.

### Drill 9 — `F.col("x").isin`

```python
df = spark.createDataFrame([(1,), (2,), (3,), (None,)], ["x"])

df.filter(F.col("x").isin(1, 2)).count()             # ?
df.filter(~F.col("x").isin(1, 2)).count()            # ?
df.filter(F.col("x").isin([1, 2])).count()           # ?
```

**A:**
- `isin(1, 2)` → **2** (rows with x in {1, 2}).
- `~isin(1, 2)` → **1** (x=3; NULL is excluded because `NULL IN (1,2)` is NULL, not TRUE, and negation of NULL is also NULL — filtered out).
- `isin([1, 2])` → **2** (also works with list).

⚠️ NULL handling in `IN`: `x IS NULL` will neither be in nor not-in. To include nulls explicitly: `(F.col("x").isin(1,2)) | F.col("x").isNull()`.

### Drill 10 — `F.lit(None)` typing

```python
df = spark.range(1).withColumn("n", F.lit(None))
df.printSchema()
# What type is column 'n'?
```

**A:** `n: void (nullable = true)` — `F.lit(None)` produces a column of `NullType` (sometimes shown as `void`). To get a typed null, cast: `F.lit(None).cast("string")`.

---

## Mini-quiz

1. What's the difference between `F.coalesce(col1, col2)` and `df.coalesce(10)`?
2. What does `F.concat(F.lit("a"), F.lit(None))` return?
3. What's the difference between `F.broadcast(df)` and `sc.broadcast(value)`?
4. How do you express `(a > 0 AND b < 100)` as a column-level boolean?
5. What's the difference between `explode` and `explode_outer`?
6. Why is chained `withColumn` an anti-pattern?
7. What does `F.col("x").isin(1, 2, 3)` do?
8. Is `df.distinct()` narrow or wide?
9. What does `F.to_date(F.col("d"))` use as the default format?
10. What does `F.lit(None)` produce?

### Answers

1. **`F.coalesce(col1, col2)`** is a SQL function returning the first non-null value. **`df.coalesce(10)`** is a DataFrame method that reduces partition count without shuffle.
2. **NULL.** `concat` propagates nulls. Use `concat_ws` to skip them.
3. **`F.broadcast(df)`** is a join hint marking a DataFrame for broadcast hash join. **`sc.broadcast(value)`** ships a read-only Python value to all executors. Same name, different mechanisms.
4. **`(F.col("a") > 0) & (F.col("b") < 100)`** — use `&` not `and`; parens around each comparison.
5. **`explode`** drops rows where the array is empty/null. **`explode_outer`** keeps them with a NULL value.
6. Each call adds a logical-plan node, increasing Catalyst's planning work for the same result. For multi-column derivations, prefer single `select` or `withColumns`.
7. Returns a Column boolean expressing membership in the set `{1, 2, 3}`. Equivalent to SQL `x IN (1, 2, 3)`.
8. **Wide** (implicit groupBy on all columns).
9. **`yyyy-MM-dd`**.
10. A literal NULL column. Equivalent to SQL `CAST(NULL AS <type>)` — type depends on context.

---

## Exam-day cheat sheet

- **`F.coalesce(c1, c2, ...)` is SQL function for first-non-null**; **`df.coalesce(n)` is partition reduction.** ⚠️
- **`concat` propagates nulls; `concat_ws` skips them.**
- **Use `&` `|` `~` for column boolean** (not Python `and`/`or`/`not`).
- **`F.broadcast(df)`** is join hint; **`sc.broadcast(val)`** is broadcast variable.
- **`explode` drops empty/null arrays; `explode_outer` keeps them.**
- **`F.col("x").isin(...)`** for `IN (...)`.
- **`F.col("x").between(a, b)`** for `BETWEEN`.
- **Date manipulation:** `F.to_date`, `F.to_timestamp`, `F.from_unixtime`, `F.date_format`, `F.date_add`, `F.datediff`, `F.year/month/day*`.
- **`withColumnRenamed(old, new)`** — schema-only rename.
- **`withColumns({k:v, ...})`** (Spark 3.3+) — multi-column derivation.
- **`F.lit(None)`** — literal NULL.

Next: [Module 06 — DataFrame Basics](06_dataframe_basics.md).
