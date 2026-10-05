# Module 7 — Pandas API on Spark

> **Goal of this module:** Understand `pyspark.pandas` well enough to recognize when it's the right tool, when it's wrong, and the conversion patterns to/from pandas and Spark DataFrames. The Mar 2025 exam de-emphasizes explicit `pyspark.pandas` bullets but the concept still shows up in scenario questions.
>
> **Maps to exam objectives:** *(Implicit — supports the "compute summary statistics" and "feature engineering" objectives when pandas semantics are used at scale.)* Domain 2.

---

## Coverage map

The Mar 2025 exam guide does NOT have an explicit `pyspark.pandas` objective — it was removed from the explicit bullets. This module supports:
- "Compute summary statistics" objective when using pandas-API expressions on Spark
- General architecture awareness for scenario questions ("data too big for pandas")

If a scenario question mentions "pandas-style code on big data," the answer involves `pyspark.pandas`.

---

## What `pyspark.pandas` is

`pyspark.pandas` is a **pandas-compatible API surface on top of Spark DataFrames**. You write code that looks like pandas, but it executes distributed across the cluster.

```python
import pyspark.pandas as ps

psdf = ps.read_csv("/Volumes/retail/raw/transactions.csv")
psdf["amount"].mean()
psdf.groupby("customer_id")["amount"].sum().reset_index()
```

This used to be a separate project called **Koalas**, which was merged into PySpark in version 3.2 (2021). Today it's a first-class part of PySpark.

---

## Mental model — three DataFrame types

| Type | Lives where | Use case |
|------|-------------|----------|
| `pandas.DataFrame` | Driver memory (single node) | Small data (<1 GB), final analysis, sklearn fit |
| `pyspark.pandas.DataFrame` | Distributed (Spark partitions) | Big data with pandas idioms |
| `pyspark.sql.DataFrame` | Distributed (Spark partitions) | Big data with Spark idioms |

```mermaid
flowchart LR
    A[pandas.DataFrame<br/>driver-only] -- ps.from_pandas --> B[pyspark.pandas.DataFrame<br/>distributed]
    B -- .to_pandas --> A
    B -- .to_spark --> C[pyspark.sql.DataFrame<br/>distributed]
    C -- .pandas_api --> B
```

### Conversion patterns

```python
import pandas as pd
import pyspark.pandas as ps

# pandas → pyspark.pandas
pdf = pd.DataFrame({"a": [1, 2, 3]})
psdf = ps.from_pandas(pdf)

# pyspark.pandas → pandas (DRIVER MEMORY — danger on big data)
pdf2 = psdf.to_pandas()

# Spark DataFrame → pyspark.pandas
sdf = spark.read.table("retail.silver.transactions")
psdf = sdf.pandas_api()        # alias: ps.DataFrame(sdf)

# pyspark.pandas → Spark DataFrame
sdf2 = psdf.to_spark()
```

> ⚠️ **Exam trap — `to_pandas()`:** This call **collects to the driver**. For a 100 GB DataFrame, this OOMs the driver. Treat `to_pandas()` like `collect()` — only on data you know fits in driver memory.

---

## When to use `pyspark.pandas`

| Use it when… | Use plain pandas when… | Use Spark DataFrame when… |
|--------------|------------------------|---------------------------|
| Data is too big for one node | Data fits comfortably on driver (<~1 GB) | You want max performance + Spark idioms |
| You / your team write pandas natively | You're using a pandas-only library (sklearn fit directly on full data) | Performance-critical pipelines |
| You want to leverage Spark but minimize rewrite cost | Quick exploratory work | Code is already Spark; new code joins it |
| Workflow has joins/groupbys that scale | Small in-memory transformations | Window functions, SQL idioms preferred |

### Gotchas

1. **Operations between two different `pyspark.pandas` frames** require enabling a flag:
   ```python
   ps.set_option("compute.ops_on_diff_frames", True)
   psdf_a["foo"] = psdf_b["bar"]   # assignment across frames
   ```
   By default this is disabled (because cross-frame ops require an expensive Spark join).

2. **Index handling differs from pandas.** pandas relies heavily on the index for joins, lookups, and sort. `pyspark.pandas` simulates indices but the underlying Spark DataFrame has no concept of a row index. Some pandas idioms that depend on index lookup are O(n) or worse on pyspark.pandas.

3. **Not all pandas features supported.** ~90% of the API surface is covered. Some advanced indexing (multi-level boolean indexing), pandas extension arrays, and obscure dtypes are missing. Check with `psdf.spark.print_schema()` and the [pyspark.pandas compatibility matrix](https://spark.apache.org/docs/latest/api/python/user_guide/pandas_on_spark/index.html).

4. **`apply()` falls back to pandas UDF semantics.** Custom Python in `psdf.apply(lambda row: ...)` runs as a pandas UDF — fine, but introduces serialization overhead. For high-volume row-level logic, prefer a native Spark expression.

---

## When NOT to use `pyspark.pandas`

- **Data fits on one node.** Spark overhead (task scheduling, serialization, JVM startup) is not worth it for sub-GB data. Use plain pandas.
- **Workflow needs a pandas-only library.** sklearn's `fit(X, y)` expects a NumPy array or pandas DataFrame *in driver memory*. You'd convert to pandas anyway — no win.
- **Performance-critical Spark pipeline.** Native Spark DataFrame ops with Catalyst optimization and Photon support outperform the `pyspark.pandas` translation layer.
- **Heavy index manipulation.** pandas-style index ops are expensive in distributed land.

---

## Pandas UDFs (vectorized UDFs) — distinct from `pyspark.pandas`

Sometimes the exam conflates these. They're different mechanisms:

- **`pyspark.pandas`** = a pandas-API-compatible *DataFrame*. You write `psdf.groupby(...)`.
- **Pandas UDF** = a *function* that takes/returns pandas Series/DataFrames, applied to a Spark DataFrame via Arrow. You decorate with `@pandas_udf(...)`.

```python
from pyspark.sql.functions import pandas_udf
import pandas as pd

@pandas_udf("double")
def predict_udf(features: pd.Series) -> pd.Series:
    return pd.Series(model.predict(features.values.reshape(-1, 1)))

scored = sdf.withColumn("prediction", predict_udf(F.col("feature")))
```

Pandas UDFs are how Spark batches Python execution efficiently — Arrow serialization, batch-wise pandas operations inside the UDF, then the batch results returned to Spark. **They are significantly faster than row-at-a-time Python UDFs.**

Pandas UDFs come in flavors:
- **Scalar UDF** (`pd.Series → pd.Series`)
- **Iterator UDF** (`Iterator[pd.Series] → Iterator[pd.Series]`) — for stateful init like loading a model once
- **Grouped Map UDF** (`pd.DataFrame → pd.DataFrame` per group)
- **Grouped Aggregate UDF** (`pd.Series → scalar` per group)

The exam touches on Pandas UDFs in the context of inference (Module 13).

---

## Example — pyspark.pandas data prep

```python
import pyspark.pandas as ps

psdf = ps.read_csv("/Volumes/retail/raw/customers.csv")

# pandas-style ops, distributed under the hood
psdf["age_bucket"] = ps.cut(psdf["age"], bins=[0, 18, 30, 50, 100], labels=["minor", "young", "mid", "senior"])

# Group + aggregate
summary = psdf.groupby("age_bucket")["income"].agg(["mean", "median", "count"]).reset_index()

# Conversion for model fit (collect to driver)
sample = psdf.sample(frac=0.01).to_pandas()   # 1% sample, small enough for driver

# Or convert back to Spark DataFrame for the next step
sdf = psdf.to_spark()
```

---

## Performance comparison — quick rule of thumb

| Operation | Plain pandas | pyspark.pandas | Spark DF | Notes |
|-----------|--------------|----------------|----------|-------|
| Group-by sum on 100 MB | <1 sec | 5-15 sec | 5-15 sec | pandas wins; Spark overhead dominates |
| Group-by sum on 100 GB | OOM | 30-60 sec | 30-60 sec | pandas can't; the two Spark variants are similar |
| Join two 10 GB tables | OOM | 20-40 sec | 15-30 sec | Native Spark slightly faster (Catalyst) |
| Single-column transform | <1 sec | 5-10 sec | 5-10 sec | pandas wins on small data |

Numbers are illustrative — they depend on cluster size. The point: **size of data is the deciding factor**.

---

## Common pitfalls

### `to_pandas()` on big DataFrames

Crashes the driver with OOM. If you need pandas at the end, **sample first** or aggregate to a small result before collecting.

### Mixing the two index models

```python
# This silently joins on indices — which in pyspark.pandas land
# means an expensive Spark operation
psdf_combined = psdf_a + psdf_b
```

Always be explicit about join keys in distributed land. Use `psdf_a.merge(psdf_b, on="key")` rather than relying on aligned indices.

### Forgetting `compute.ops_on_diff_frames`

```python
psdf_a["new_col"] = psdf_b["foo"]
# AnalysisException unless you've set the option
```

### Using pyspark.pandas just because the data is "big-ish"

100 MB is not big. Drive-memory pandas is faster. Profile before reaching for the distributed variant.

---

## What the exam tests on this module

> 🎯 **Exam tests here:**
> - `import pyspark.pandas as ps` — recognize the import
> - When to use pyspark.pandas vs pandas vs Spark DataFrame (size of data, idiom familiarity)
> - The conversion calls: `ps.from_pandas`, `psdf.to_pandas`, `psdf.to_spark`, `sdf.pandas_api`
> - `to_pandas()` collects to driver — danger on large data
> - Pandas UDFs (`@pandas_udf`) are distinct from pyspark.pandas — both use Arrow but solve different problems

---

## Mini quiz

1. You have a 500 GB Delta table and want to write pandas-idiomatic code on it. Which API do you use?
2. After 30 minutes of feature engineering in `pyspark.pandas`, you call `psdf.to_pandas()`. The cluster crashes. What happened?
3. `psdf_a["new"] = psdf_b["foo"]` throws an `AnalysisException`. What flag do you set?
4. Your data is 80 MB. You're a long-time pandas user. Should you use `pyspark.pandas`?
5. Name the four flavors of Pandas UDF.

### Answers

1. **`pyspark.pandas`.** 500 GB doesn't fit on one driver, so plain pandas is out. Native Spark DataFrame works too, but if you want pandas idioms, pyspark.pandas is the answer.
2. `to_pandas()` collects the entire DataFrame to the driver's memory. 30 minutes of feature engineering can balloon a small input into many GBs. The driver OOMed. **Sample first** or aggregate before collecting.
3. `ps.set_option("compute.ops_on_diff_frames", True)`. This enables operations across two different pyspark.pandas frames (which require a Spark join under the hood and are off by default for safety).
4. **No.** 80 MB fits comfortably on driver. Spark overhead would slow you down. Stick with pandas.
5. **Scalar, Iterator, Grouped Map, Grouped Aggregate.**
