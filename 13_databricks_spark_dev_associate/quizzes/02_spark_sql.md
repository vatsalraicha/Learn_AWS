# Quiz 02 — Spark SQL (Basics + Functions)

> 27 questions covering Domain 2 (20% — ~9 questions on the real exam, scaled to 27 for practice).
> Topics: `spark.sql()` semantics, temp views (local/global/replace), catalog API, pivot/unpivot, querying files directly, built-in functions (`cast`, `lit`, `when`, the `coalesce` trap, `expr`, `broadcast`, date/timestamp functions, regex, arrays, structs, JSON, `withColumn` vs `withColumnRenamed`).

---

## Recall

1. What does `spark.sql("SELECT * FROM my_view")` return — a DataFrame, an RDD, or a Dataset[Row]?
2. Which method registers a DataFrame as a session-scoped view that **overwrites** an existing view of the same name?
3. What is the database/schema name that holds Spark global temporary views?
4. Which catalog method lists all tables in the current database?
5. The function `F.coalesce(c1, c2, c3)` does what — at the column level?
6. The DataFrame method `df.coalesce(10)` does what — at the partition level?
7. Which built-in function returns the current date as a `DateType`?
8. Which function converts a string column like `"2026-05-23"` into a proper `DateType`?
9. What does `F.lit(0)` produce?
10. Which function combines two columns into a single struct column?

## Apply

11. Write the SQL that queries a Parquet file at `/data/events.parquet` directly without registering it as a table.
12. Given a session-scoped temp view `sales`, write the Python that runs `SELECT region, SUM(amount) FROM sales GROUP BY region` and shows the result.
13. You need a column `status_label` that is `"adult"` when `age >= 18`, `"minor"` otherwise. Write it using `F.when().otherwise()`.
14. Convert a column `epoch_seconds` (long) into a `TimestampType` column called `event_ts`.
15. Add 7 days to a date column `event_date` and call the new column `expiry`.
16. Given column `full_name = "Alice Liu"`, split it on space and explode into one row per name part.
17. You have a JSON-string column `payload`. Parse it into a struct using a schema `schema = StructType([...])`.
18. Rename column `customer_id` to `cust_id` without affecting other columns. Which method?
19. Given a struct column `addr` with fields `street`, `city`, `zip`, project just `addr.city` to the top level as `city`.
20. Replace all occurrences of `"\s+"` (one or more whitespace) in column `comment` with a single space.
21. Compute the number of days between two date columns `end_date` and `start_date`.

## Diagnose

22. A colleague writes:
    ```python
    df.coalesce(F.col("primary_email"), F.col("backup_email"), F.lit("unknown@example.com"))
    ```
    They expected a "first non-null" column. What went wrong?
23. After running `df1.createTempView("orders")` then `df2.createTempView("orders")`, the second call throws `TempTableAlreadyExistsException`. What's the right API to use?
24. A user runs `spark.sql("SELECT * FROM global_temp.metrics")` and gets `Table or view not found`. They DID call `df.createGlobalTempView("metrics")` earlier in the same session. What's the most likely cause?
25. A pipeline chains 20 `withColumn` calls. Code review flags it as an anti-pattern. Why, and what's the rewrite?
26. `df.withColumnRenamed("old", "new")` runs without error but produces a DataFrame with the original column name. Diagnosis?

## Defend

27. Defend or refute: "Because `spark.sql()` uses SQL syntax, it's slower than the equivalent DataFrame API code."

---

## Answers

1. **A DataFrame** (which, in PySpark, IS `DataFrame = Dataset[Row]` under the hood, but the public Python API surfaces it as `DataFrame`). Key point: `spark.sql(...)` is lazy — it builds a query plan, doesn't execute until an action.

2. **`createOrReplaceTempView("name")`.** `createTempView` raises if the view exists; `createOrReplaceTempView` silently overwrites.

3. **`global_temp`.** You query via `SELECT * FROM global_temp.my_view`. Global temp views live for the lifetime of the Spark *application* (not just one session) and are visible across `SparkSession`s of the same application.

4. **`spark.catalog.listTables()`** (optionally pass a database name). Other useful catalog methods: `listDatabases()`, `listColumns(table)`, `currentDatabase()`, `dropTempView(name)`.

5. **Returns the first non-null value** across the provided columns/literals per row. SQL-style `COALESCE`. **Trap:** this is `pyspark.sql.functions.coalesce`, completely different from `DataFrame.coalesce`.

6. **Reduces the partition count to 10 (narrow, no shuffle).** Cannot increase partitions. **Trap:** same name, completely different semantics from `F.coalesce`. Common exam misdirection.

7. **`F.current_date()`** (returns `DateType`). `F.current_timestamp()` returns `TimestampType`.

8. **`F.to_date(col, fmt)`.** Pattern: `F.to_date(F.col("date_str"), "yyyy-MM-dd")`. For timestamps use `F.to_timestamp(col, fmt)`.

9. **A literal column with the integer value 0**, usable in any column expression: `df.withColumn("counter", F.lit(0))`.

10. **`F.struct(c1, c2, ...)`** builds a struct column with the listed fields.

11. ```sql
    SELECT * FROM parquet.`/data/events.parquet`
    ```
    Note the **backticks** around the path. Works for `parquet`, `json`, `csv`, `orc`, `text`, `delta`.

12. ```python
    spark.sql("SELECT region, SUM(amount) AS total FROM sales GROUP BY region").show()
    ```
    `spark.sql()` returns a DataFrame; chain `.show()` (or any action) to materialize.

13. ```python
    df = df.withColumn(
        "status_label",
        F.when(F.col("age") >= 18, "adult").otherwise("minor"),
    )
    ```

14. ```python
    df = df.withColumn("event_ts", F.to_timestamp(F.from_unixtime(F.col("epoch_seconds"))))
    # Or shorter:
    df = df.withColumn("event_ts", (F.col("epoch_seconds")).cast("timestamp"))
    ```

15. ```python
    df = df.withColumn("expiry", F.date_add(F.col("event_date"), 7))
    ```

16. ```python
    df = df.withColumn("name_part", F.explode(F.split(F.col("full_name"), " ")))
    ```
    `split` returns an array; `explode` emits one row per array element. Use `posexplode` if you also need the index.

17. ```python
    df = df.withColumn("parsed", F.from_json(F.col("payload"), schema))
    ```
    `from_json` parses a JSON string into a struct (given a schema). `to_json` does the reverse.

18. **`df.withColumnRenamed("customer_id", "cust_id")`.** Note: returns a NEW DataFrame; doesn't mutate in place.

19. ```python
    df.select(F.col("addr.city").alias("city"))
    # or
    df.select("addr.city")  # auto-names as "city"
    ```
    Dot syntax navigates struct fields.

20. ```python
    df.withColumn("comment", F.regexp_replace(F.col("comment"), r"\s+", " "))
    ```

21. ```python
    df.withColumn("days_open", F.datediff(F.col("end_date"), F.col("start_date")))
    ```
    Order matters: `datediff(end, start)` returns end-start.

22. **They confused `DataFrame.coalesce` with `F.coalesce`.** `df.coalesce(...)` takes integer partition count, not columns. The intent — "first non-null email" — needs:
    ```python
    df.withColumn("email", F.coalesce(F.col("primary_email"), F.col("backup_email"), F.lit("unknown@example.com")))
    ```
    **This is one of the highest-frequency trap questions** on the exam — be ready for it in code-identification format.

23. **`createOrReplaceTempView("orders")`.** It silently replaces, so re-registering with the same name is safe.

24. **They likely queried `metrics` without the `global_temp.` prefix**, or are querying from a *different application* (global temp lives for the application but the prefix is always required). Global temp views are NOT in the current database — they're in the special `global_temp` database.

25. **Catalyst can optimize a single `select` with many expressions far better than a chain of `withColumn`s**, which generate intermediate projections. Each `withColumn` adds a `Project` node to the logical plan; chaining 20 of them creates 20 projections that Catalyst CAN often fuse, but `select` is cleaner. Rewrite:
    ```python
    df = df.select(
        "*",
        F.col("price") * F.col("qty").alias("total"),
        F.upper(F.col("name")).alias("name_upper"),
        # ... more expressions
    )
    ```

26. **They didn't reassign:**
    ```python
    df.withColumnRenamed("old", "new")  # returned new DF, discarded
    # Should be:
    df = df.withColumnRenamed("old", "new")
    ```
    All DataFrame methods are **immutable** — they return new DataFrames; they never mutate.

27. **Refute.** `spark.sql(...)` and the DataFrame API go through **the same Catalyst optimizer and the same physical execution plan**. Performance is identical. Choose based on readability and team conventions, not perceived speed. The only nuance: SQL strings can have minor parse overhead at planning time (microseconds), but at runtime they're identical.
