# Quiz 03 — DataFrame / Dataset API

> 40 questions covering Domain 3 (30% — ~14 questions on the real exam, scaled to 40 for practice; THIS IS THE LARGEST QUIZ).
> Topics: reading & writing (CSV/JSON/Parquet/Delta), schemas (`inferSchema`, explicit StructType, DDL string), core transformations (`select`/`selectExpr`/`filter`/`where`/`withColumn`/`withColumnRenamed`/`drop`/`distinct`/`dropDuplicates`/`sample`/`limit`/`sort`/`orderBy`), aggregations (`groupBy`/`agg`/`pivot`/`approx_count_distinct`), window functions (`partitionBy`/`orderBy`/`rowsBetween`/`rangeBetween`/`row_number`/`rank`/`dense_rank`/`percent_rank`/`cume_dist`/`lag`/`lead`), joins (inner/left/right/full_outer/semi/anti/cross + broadcast restrictions), and `union` (NARROW!) vs `unionByName`.

---

## Recall

1. Which read option toggles automatic schema inference for CSV?
2. What is the default value of `inferSchema` for `spark.read.csv(...)`?
3. Provide a DDL-string schema specifying `id LONG, name STRING, created TIMESTAMP`.
4. What's the difference between `df.distinct()` and `df.dropDuplicates(["id"])`?
5. What's the difference between `df.filter(...)` and `df.where(...)`?
6. Is `df.union(df2)` narrow or wide?
7. What does `df.unionByName(df2, allowMissingColumns=True)` do that `union` does not?
8. Which window function returns the same rank for ties and leaves gaps after?
9. Which window function returns the same rank for ties and does NOT leave gaps?
10. Which window function returns a unique sequential integer ignoring ties?
11. Default save mode for `df.write...` (if you don't call `.mode(...)`)?
12. List the four valid arguments to `.mode(...)`.

## Apply

13. Read a CSV at `/data/users.csv` with a header row and inferred schema.
14. Read the same CSV but with an explicit schema (`StructType` with two fields: `user_id: LongType`, `name: StringType`).
15. Write `df` to Parquet at `/data/out`, partitioned by `country`, overwriting any existing data.
16. Drop rows where ANY column is null.
17. Drop rows ONLY where ALL columns are null.
18. Drop rows where `email` or `phone` is null.
19. Replace nulls in column `score` with 0 and nulls in column `name` with `"unknown"` in one call.
20. Group by `dept` and compute count, mean salary, and approximate distinct user count.
21. Pivot a DataFrame so that distinct values of column `quarter` become columns of summed `revenue` per `region`.
22. Add a column `row_num` ranking rows within each `region` by `revenue` descending, breaking ties by `id` ascending.
23. Add a column `prev_revenue` containing the previous row's `revenue` within each `region`, ordered by `date`.
24. Compute a rolling 7-row sum of `revenue` per `region` ordered by `date` (current row + 6 preceding rows).
25. Perform a left semi join between `orders` and `customers` on `customer_id`.
26. Broadcast `dim_country` (small) when joining to fact `fact_sales` (large) on `country_code`.

## Diagnose

27. Your engineer claims `union` shuffles the data. Refute with one sentence and show how to test it.
28. ```python
    df1 = spark.createDataFrame([(1, "a")], ["id", "name"])
    df2 = spark.createDataFrame([("b", 2)], ["name", "id"])
    df1.union(df2).show()
    ```
    What does this print, and what's the bug?
29. After `df.dropDuplicates(["email"])`, downstream code complains that two rows share the same `email`. Diagnosis?
30. A user tries to broadcast the **right** side of a `left_outer` join:
    ```python
    df1.join(F.broadcast(df2), "id", "left_outer")
    ```
    This works. But they then try a `right_outer`:
    ```python
    df1.join(F.broadcast(df2), "id", "right_outer")
    ```
    Spark ignores the hint. Why?
31. A window query without `partitionBy` works in dev (10k rows) but warns "WARN WindowExec: No Partition Defined for Window operation! Moving all data to a single partition" in production. Diagnosis and fix?
32. ```python
    df.orderBy("revenue", ascending=False)
    ```
    Compared to:
    ```python
    df.orderBy(F.col("revenue").desc())
    ```
    Same result? Any preference?
33. A user reports that after `df.sample(0.1)`, calling `.count()` twice returns different numbers. Why?
34. Joining two 10TB tables on a high-cardinality key produces 200 output partitions, but one is 500GB and the rest are <100MB. Diagnose and propose two fixes.

## Defend

35. Defend or refute: "`withColumn` is always preferable to `select` when adding columns because it's more readable."
36. Why does Spark prohibit broadcasting the **outer** side of an outer join?
37. When would you prefer `dropDuplicates(["id"])` over `distinct()`?
38. Defend or refute: "Window functions are narrow because they only operate within a single partition."

---

## Answers

1. **`option("inferSchema", "true")`** or `inferSchema=True` as a keyword arg.

2. **`False`.** Without `inferSchema=True`, all CSV columns are read as strings. Inferring requires an extra pass over the file (read once for schema, again for data) — expensive on large files.

3. ```python
    schema = "id LONG, name STRING, created TIMESTAMP"
    spark.read.schema(schema).csv("path")
    ```

4. **`distinct()`** dedups based on ALL columns (full-row uniqueness). **`dropDuplicates(["id"])`** dedups based on the subset — keeps an arbitrary row per `id`. `distinct()` is equivalent to `dropDuplicates()` with no argument.

5. **None — they are aliases.** `where` is a SQL-style alias for `filter`. Use whichever reads better.

6. **NARROW.** `union` concatenates partitions; no shuffle. This is a top-3 exam trap — many candidates wrongly assume "merging two datasets must shuffle." It doesn't. (SQL `UNION` dedup semantics come from a follow-up `.distinct()`, which IS wide.)

7. **`unionByName`** matches columns by NAME, not position. With `allowMissingColumns=True`, columns present in one side and absent in the other get nulls; without it, a column mismatch raises. `union` is **strictly positional** — column count must match, names are ignored.

8. **`rank()`** — gives 1, 2, 2, 4, 5 (gap after a tie).

9. **`dense_rank()`** — gives 1, 2, 2, 3, 4 (no gap).

10. **`row_number()`** — gives 1, 2, 3, 4, 5 regardless of ties (ties broken by `orderBy` and physical ordering).

11. **`errorIfExists`** (also spelled `error` or just default). Throws if the path or table already has data.

12. **`overwrite`**, **`append`**, **`ignore`**, **`errorIfExists`** (alias: `error`).

13. ```python
    df = (spark.read
          .option("header", True)
          .option("inferSchema", True)
          .csv("/data/users.csv"))
    ```

14. ```python
    from pyspark.sql.types import StructType, StructField, LongType, StringType

    schema = StructType([
        StructField("user_id", LongType(), True),
        StructField("name", StringType(), True),
    ])
    df = spark.read.option("header", True).schema(schema).csv("/data/users.csv")
    ```

15. ```python
    df.write.mode("overwrite").partitionBy("country").parquet("/data/out")
    ```
    **Note the EXACT call chain order** — `mode` then `partitionBy` then `parquet`. Common distractor patterns swap or omit one.

16. ```python
    df.na.drop()  # default how="any"
    ```

17. ```python
    df.na.drop(how="all")
    ```
    **Trap:** `na.drop("all")` (positional) and `na.drop(how="all")` both work; `na.drop()` defaults to `"any"`. Sample question #6 in the official guide tests this exact distinction.

18. ```python
    df.na.drop(subset=["email", "phone"])
    ```
    Default `how="any"` — drops if ANY of the listed cols is null. Add `how="all"` to drop only when ALL listed cols are null.

19. ```python
    df.na.fill({"score": 0, "name": "unknown"})
    ```

20. ```python
    df.groupBy("dept").agg(
        F.count("*").alias("n"),
        F.mean("salary").alias("avg_sal"),
        F.approx_count_distinct("user_id").alias("uniq"),
    )
    ```
    `approx_count_distinct` uses HyperLogLog — sublinear memory, no full distinct shuffle. Sample question #10 in the official guide tests this exact use case.

21. ```python
    df.groupBy("region").pivot("quarter").agg(F.sum("revenue"))
    ```

22. ```python
    w = Window.partitionBy("region").orderBy(F.col("revenue").desc(), F.col("id").asc())
    df.withColumn("row_num", F.row_number().over(w))
    ```

23. ```python
    w = Window.partitionBy("region").orderBy("date")
    df.withColumn("prev_revenue", F.lag("revenue", 1).over(w))
    ```
    `lag(col, n=1, default=None)` — lookback. `lead` is the forward analog.

24. ```python
    w = (Window.partitionBy("region")
                .orderBy("date")
                .rowsBetween(-6, 0))  # 6 preceding + current = 7 rows
    df.withColumn("rolling_7d", F.sum("revenue").over(w))
    ```
    **Trap:** `rowsBetween` uses positional offsets (-6 = 6 rows back); `rangeBetween` uses value-based ranges (only valid on numeric/timestamp ordered columns).

25. ```python
    orders.join(customers, on="customer_id", how="left_semi")
    ```
    Semi join returns rows from the LEFT side whose key matches at least one row in the right; right-side columns are NOT included.

26. ```python
    fact_sales.join(F.broadcast(dim_country), on="country_code", how="inner")
    ```

27. **Refute** — `union` is narrow, no shuffle. **Test**: look at the physical plan: `df1.union(df2).explain()` shows `Union` directly, no `Exchange` (shuffle) node. Or check Spark UI — the resulting stage will have the SUM of input partition counts, no shuffle dependency.

28. **It prints two rows with mismatched columns** — but the bug is that `union` is **positional**, so `("b", 2)` gets placed as `id="b", name=2`. The fix:
    ```python
    df1.unionByName(df2)
    ```
    which matches on column NAME and produces correct `(1, "a")` + `(2, "b")`.

29. **Hash collision after a previous shuffle, or non-deterministic source.** `dropDuplicates` keeps an *arbitrary* row per key — if downstream re-runs see different "arbitrary" picks, they may believe duplicates exist. Real cause is usually: (a) the source itself returns different rows on retry (e.g., streaming sources, non-idempotent UDFs), or (b) downstream is comparing two snapshots taken at different times.

30. **You can broadcast only the side that is NOT the "preserving" side of an outer join.**
    - `left_outer` preserves the LEFT side → can only broadcast the RIGHT side ✓
    - `right_outer` preserves the RIGHT side → can only broadcast the LEFT side
    - `full_outer` preserves both → CANNOT broadcast either side
    Spark silently falls back to sort-merge or shuffle-hash when the hint is invalid. **High-value exam trap.**

31. **Window with no `partitionBy` forces ALL data into a single partition.** With 10k rows, this works (one task). In production at 100M+ rows, one executor OOMs. Fix: add a meaningful `partitionBy`. If the analytic genuinely needs a global window (e.g., overall ranking), reconsider — usually you can `repartition` by a coarse bucket or compute global aggregates differently.

32. **Same result.** `ascending=False` and `.desc()` are equivalent. Use `.desc()` when ordering by multiple cols with mixed direction — clearer per-column intent. `ascending=[False, True, False]` is supported as a list aligned to the column args.

33. **`sample` is not deterministic by default.** Without `seed`, each evaluation re-runs the sampling. Fix:
    ```python
    df.sample(fraction=0.1, seed=42)
    ```
    Even with a seed, recomputing the lineage produces the same sample within ONE session — but reading underlying files in a different order can still shift results across sessions.

34. **Data skew on the join key.** Two fixes:
    1. **Enable AQE skew join**: `spark.sql.adaptive.enabled=true` + `spark.sql.adaptive.skewJoin.enabled=true`. Spark splits the skewed partition into smaller sub-partitions automatically at runtime.
    2. **Salt the skewed side**: append a random integer 0..N to the join key on both sides, expanding hot keys across N partitions; aggregate to remove salt after the join.

35. **Refute.** For 1-3 added columns, `withColumn` is clearer. For 5+ additions, `select` (with `*` plus the new exprs) gives Catalyst a flatter plan AND is more readable. The exam favors `select` for multi-add scenarios in its code-identification questions.

36. **Broadcast joins build a hash table on the broadcast side, then probe with the streaming side.** The outer-preserving side MUST emit nulls for non-matches — this requires iterating the preserving side fully, which only works if it's the streaming side, not the hashed side. Hash side rows have no way to emit "I had no match" because the hash side is consumed lookup-by-lookup, not row-by-row.

37. **When duplicates on a key column are the dedup criterion but the row payload varies** (e.g., latest update per user). `dropDuplicates(["user_id"])` keeps one row per `user_id`; you typically combine with `orderBy` + `Window` + `row_number()=1` for deterministic "which row wins."

38. **Refute.** Window functions are **WIDE** — they require shuffling rows so all rows with the same `partitionBy` value land on the same partition. Without `partitionBy`, ALL rows shuffle to a single partition (often catastrophically). The name "partitionBy" within a Window is unrelated to physical partition layout; it forces a shuffle to group rows logically.
