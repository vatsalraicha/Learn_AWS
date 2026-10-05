# Module 6 — Data Prep with Spark DataFrames

> **Goal of this module:** Drill the Spark DataFrame surface the exam tests in Domain 2 — summary statistics (`summary()` vs `describe()` vs `dbutils.data.summarize`), outlier removal with std-dev and IQR, missing-value imputation choices, basic visualization patterns, and the train/val/test split call.
>
> **Maps to exam objectives:** *Compute summary statistics on a Spark DataFrame · Remove outliers from a Spark DataFrame based on standard deviation or IQR · Create visualizations for categorical or continuous features · Compare two categorical or two continuous features using the appropriate method · Compare and contrast imputing missing values with the mean or median or mode value · Impute missing values* (Domain 2).

---

## Coverage map (verbatim exam objectives → where taught here)

| Verbatim objective | Taught in section |
|---|---|
| Compute summary statistics on a Spark DataFrame using `.summary()` or dbutils data summaries | "Summary statistics — three different methods" |
| Remove outliers based on standard deviation or IQR | "Outlier removal — std-dev method" + "IQR method" |
| Create visualizations for categorical or continuous features | "Visualizing categorical vs continuous features" |
| Compare two categorical or two continuous features | "Comparing two features" |
| Compare and contrast imputing missing values with mean/median/mode | "Imputation — strategy table" |
| Impute missing values with mean/median/mode | "Spark ML `Imputer`" |

---

## Look-alike API comparison — data prep edition

| Pair | Difference | Exam tell |
|------|------------|-----------|
| `df.describe(*cols)` vs `df.summary(*stats)` | count/mean/stddev/min/max ONLY vs +25%/50%/75% percentiles | "median" / "75th percentile" → summary |
| `df.summary()` vs `dbutils.data.summarize(df)` | DataFrame return vs visual UI panel | Programmatic → summary. Visual exploration → dbutils |
| `df.dropna()` vs `df.na.drop("any")` vs `df.na.drop("all")` | drop if any null vs same vs drop only if all cols null | dropna() default = "any" |
| `df.fillna(0)` vs `df.na.fill(0, subset=["age"])` | fill all nulls vs fill specific columns | subset= controls scope |
| `Imputer(strategy="mean")` vs `df.fillna(df.agg(F.mean("col")).first()[0])` | Spark ML pipeline-friendly vs manual | Imputer is exam-preferred (composable in Pipeline) |
| `df.approxQuantile(col, [0.25, 0.75], 0.01)` vs `df.summary("25%", "75%")` | returns floats vs returns DataFrame rows | Programmatic threshold computation → approxQuantile |
| `df.stat.corr(c1, c2)` vs `Correlation.corr(df, "features")` | column-pair Pearson vs matrix from a Vector column | Two columns → stat.corr. Matrix → Correlation.corr |
| `df.randomSplit([0.7, 0.3], seed=42)` vs `df.sampleBy("label", fractions={...}, seed=42)` | random fractions vs per-key fractions (stratified) | "stratified split" → sampleBy |

---

## Summary statistics — three different methods

| Call | Output | Notes |
|------|--------|-------|
| `df.describe(*cols)` | count, mean, stddev, min, max | No percentiles |
| `df.summary(*statistics)` | count, mean, stddev, min, 25%, 50%, 75%, max | Default includes percentiles; works on string columns too |
| `dbutils.data.summarize(df)` | Visual profile in notebook (histograms, missing %) | Databricks-only, UI-rendered |

```python
df.describe("age", "income").show()
# +-------+------------------+------------------+
# |summary|               age|            income|
# +-------+------------------+------------------+
# |  count|              1000|              1000|
# |   mean|             34.21|          52340.18|
# | stddev|             12.14|          18234.55|
# |    min|                18|              5000|
# |    max|                85|            245000|
# +-------+------------------+------------------+

df.summary().show()
# adds 25%, 50%, 75% percentile rows
```

> ⚠️ **Exam trap — `describe` vs `summary`:** the exam tests this distinction directly. If the question asks for **percentiles (25/50/75%) or median**, the answer is `summary()`. `describe()` does NOT compute percentiles.

### Custom summary stats

`summary()` accepts arguments to limit the stats computed:

```python
df.summary("count", "mean", "75%", "max").show()
df.summary("50%").show()   # only median
```

### `dbutils.data.summarize`

```python
dbutils.data.summarize(df)
```

Renders a **visual data profile** in the notebook — histograms per column, missing-value counts, type info. UI-only, no DataFrame return. Useful for exploration; not for programmatic use.

---

## Outlier removal — standard deviation method

The "z-score" / std-dev approach: drop rows where a column is more than `k` standard deviations from the mean (typically k=3).

```python
from pyspark.sql import functions as F

mean_income, stddev_income = df.select(
    F.mean("income").alias("mean"),
    F.stddev("income").alias("stddev"),
).first()

lower = mean_income - 3 * stddev_income
upper = mean_income + 3 * stddev_income

cleaned = df.filter((F.col("income") >= lower) & (F.col("income") <= upper))
```

### Caveats

- **Assumes near-normal distribution.** For heavily skewed data (income, transaction amounts), mean+stddev pulls toward the tail and you end up dropping ~5-15% of legitimate values. Use IQR instead.
- **Sensitive to outliers themselves** — the very outliers you want to remove inflate the stddev, widening the bounds.

---

## Outlier removal — IQR method

The "interquartile range" approach: drop rows outside `[Q1 − 1.5 × IQR, Q3 + 1.5 × IQR]` where `IQR = Q3 − Q1`.

```python
q1, q3 = df.approxQuantile("income", [0.25, 0.75], 0.01)
iqr = q3 - q1

lower = q1 - 1.5 * iqr
upper = q3 + 1.5 * iqr

cleaned = df.filter((F.col("income") >= lower) & (F.col("income") <= upper))
```

`approxQuantile(col, probabilities, relativeError)` returns approximate quantiles efficiently on a Spark DataFrame. `relativeError=0.01` is a good default — exact quantiles on large data are expensive.

### When to use which

| Method | Use when |
|--------|----------|
| Std-dev (z-score) | Data is approximately normal; few existing outliers |
| IQR | Data is skewed or has many outliers; want robust-to-outliers bounds |

> ⚠️ **Exam trap:** The exam objective lists "standard deviation or IQR" explicitly. Either is acceptable; the question may force-choose by describing the distribution. **Skewed distribution → IQR.** **Symmetric → std-dev.**

---

## Imputation — mean, median, mode

The exam tests this in two flavors: (a) **which strategy is right for which distribution**, and (b) **how to call the Spark ML `Imputer`**.

### Strategy table

| Strategy | Use for | Distribution shape |
|----------|---------|--------------------|
| **Mean** | Continuous, **symmetric** | Bell curve, no heavy tail |
| **Median** | Continuous, **skewed** or outlier-prone | Long-tail, income, prices |
| **Mode** | **Categorical** | Strings, integer codes for categories |

> ⚠️ **Exam trap — defaulting to mean:** "It's continuous, use mean" is the wrong reflex. The exam (sample Q2) tests whether you pause to consider distribution. **Skewed → median is safer.** When in doubt, median; it's robust to outliers.

### Spark ML `Imputer`

```python
from pyspark.ml.feature import Imputer

imputer = Imputer(
    inputCols=["age", "income"],
    outputCols=["age_imp", "income_imp"],
    strategy="median",      # "mean", "median", or "mode"
)
imputer_model = imputer.fit(df)
imputed = imputer_model.transform(df)
```

- `Imputer` is an **Estimator** (has `.fit`) → returns an `ImputerModel` (Transformer with `.transform`).
- `strategy="mode"` works for both numeric and string columns.
- Missing-value placeholder: by default `null` (and `NaN` for floats). Override with `missingValue=...` for custom sentinel values like `-999`.

### Tracking which rows were imputed

A common production pattern: add a sister column flagging "this value was imputed":

```python
from pyspark.sql import functions as F

flagged = df.withColumn("age_was_missing", F.col("age").isNull())
# then impute
imputed = imputer_model.transform(flagged)
```

The flag column itself becomes a feature — sometimes missingness is informative.

---

## Visualizing categorical vs continuous features

The exam asks you to recognize **the appropriate method**, not to memorize matplotlib calls. The mental model:

| Feature shape | Visualization |
|---------------|---------------|
| Continuous distribution | Histogram, box plot, density plot |
| Categorical distribution | Bar chart of counts |
| Continuous over time | Line plot |
| Continuous vs continuous (relationship) | Scatter plot |
| Continuous correlation matrix | Heatmap |
| Categorical vs categorical (contingency) | Stacked bar / mosaic plot |
| Categorical vs continuous (e.g., feature value per class) | Box plot grouped by category, violin plot |

### In Databricks specifically

Databricks notebooks render a built-in chart UI on `display(df)` — pick chart type from the dropdown. For SQL cells, the result table also has a chart picker. You don't always need matplotlib; the `display()` UI handles most exploratory plots.

```python
display(df.select("income"))
# UI chart picker: pick "Histogram"

display(df.groupBy("city").count())
# UI chart picker: pick "Bar"
```

---

## Comparing two features

The exam asks "compare two categorical or two continuous features using the appropriate method." Recognize:

### Two continuous features

- **Scatter plot** for visual inspection
- **Pearson / Spearman correlation** for a numeric summary
  ```python
  df.stat.corr("age", "income")          # Pearson by default
  df.stat.corr("age", "income", "pearson")
  df.stat.corr("rank", "score", "spearman")
  ```
- **Covariance** also available: `df.stat.cov("age", "income")`

### Two categorical features

- **Contingency table** (crosstab)
  ```python
  df.stat.crosstab("gender", "purchased").show()
  ```
- **Chi-square test of independence** for whether the two categoricals are associated (Spark MLlib stats package via `pyspark.ml.stat.ChiSquareTest`)

### One categorical, one continuous

- **Grouped box plot / violin** for visual
- **`groupBy(cat).agg(F.mean(cont))`** for numeric summary
- **ANOVA** (out of scope for the Associate exam)

---

## Train / validation / test split

The Spark idiom is `randomSplit`:

```python
train_df, val_df, test_df = df.randomSplit([0.7, 0.15, 0.15], seed=42)
```

### Things the exam tests

- The **`seed` argument is critical** for reproducibility. Same seed → same split. Without it, every call gives a different split → inconsistent metrics.
- The fractions **should sum to ~1.0**. They don't have to be exactly 1.0; Spark normalizes, but stick to summing to 1 for clarity.
- The function returns a **list of DataFrames in the same order as the fractions**.
- The split is **non-stratified**. For class-imbalanced data, do a stratified split manually:
  ```python
  fractions = {0: 0.7, 1: 0.7}
  train = df.sampleBy("label", fractions=fractions, seed=42)
  remainder = df.subtract(train)
  val, test = remainder.randomSplit([0.5, 0.5], seed=42)
  ```

> ⚠️ **Exam trap — split before transformations:** Always split **before** fitting transformers (Imputer, StringIndexer, StandardScaler). Otherwise the validation/test data leaks into the fitted state. The pattern: split → fit transformers on train only → transform all three.

---

## End-to-end data prep pipeline

```python
from pyspark.sql import functions as F
from pyspark.ml.feature import Imputer, StringIndexer, OneHotEncoder, VectorAssembler

df = spark.table("retail.silver.customers")

# Outlier removal (IQR on income)
q1, q3 = df.approxQuantile("income", [0.25, 0.75], 0.01)
iqr = q3 - q1
df = df.filter(F.col("income").between(q1 - 1.5 * iqr, q3 + 1.5 * iqr))

# Split BEFORE fitting transformers
train_df, val_df, test_df = df.randomSplit([0.7, 0.15, 0.15], seed=42)

# Imputer fit on train only
imputer = Imputer(
    inputCols=["age", "income"],
    outputCols=["age_imp", "income_imp"],
    strategy="median",
).fit(train_df)

train_df = imputer.transform(train_df)
val_df = imputer.transform(val_df)
test_df = imputer.transform(test_df)

# Encode categoricals
indexer = StringIndexer(
    inputCols=["city", "gender"],
    outputCols=["city_idx", "gender_idx"],
    handleInvalid="keep",
).fit(train_df)

for d in (train_df, val_df, test_df):
    d = indexer.transform(d)
```

(In practice you'd wrap all of this in a `Pipeline` — see Module 8.)

---

## Common pitfalls

### Computing transformations before splitting

Fitting Imputer / Scaler / Indexer on the full dataset and then splitting leaks validation/test statistics into train. Always split first.

### Using `describe()` and complaining there's no median

`describe()` only computes count/mean/stddev/min/max. Use `summary()` for percentiles (which give you median as `50%`).

### Mode imputation on continuous data

If you impute `income` with `strategy="mode"`, you get whatever single value is most common — usually meaningless and distortive. Mode is for **categorical** features.

### Std-dev outlier removal on a heavy-tailed distribution

Income, transaction amount, etc. are heavily right-skewed. `mean ± 3σ` gives bounds that drop large fractions of legitimate data. Use IQR for skewed columns.

---

## Worked exam-question walkthroughs

### Worked example (verbatim official Q2): "Impute missing values in a continuous feature with least effort but correct results"

**Options:**
A. SimpleImputer auto-selects — **wrong, no such auto-detect**
B. Examine the distribution and select appropriate imputation — **CORRECT**
C. `.mean()` is best on continuous — **wrong reflex**
D. `.mode()` is best on continuous — **wrong (mode is for categorical)**

**Answer:** B. The "least effort" trap is misdirection — the EXAM-CORRECT answer prioritizes correctness via distribution inspection. Mean is wrong for skewed data; median is robust.

### Worked example: "Skewed income — which outlier method?"

**Decision rule:** Skewed → IQR. Symmetric → std-dev.

**Reasoning:** Outliers themselves inflate stddev, widening bounds. IQR uses quartiles, robust to outliers.

### Worked example: "Pre-fit a Scaler before split"

**Pattern:** Code shows `StandardScaler.fit(df)` then `df.randomSplit(...)`. What's wrong?

**Answer:** The scaler's mean/stddev computed on the FULL data (including val/test) — data leakage. Always split first, then `fit` transformers on train ONLY.

---

## Output prediction drills

### Drill 1
```python
df.describe("income").show()
```
**Q:** Are percentiles in the output?
**A:** **No.** `describe()` shows count/mean/stddev/min/max only. Use `summary()` for percentiles.

### Drill 2
```python
Imputer(inputCols=["city"], outputCols=["city_imp"], strategy="mean").fit(df)
```
**Q:** Result?
**A:** **Error** (or nonsense). Mean cannot be computed on a string column. Use `strategy="mode"` for categorical.

### Drill 3
```python
train, val, test = df.randomSplit([0.7, 0.15, 0.15])    # no seed
```
**Q:** What changes between two runs?
**A:** Each call produces a DIFFERENT random split because the seed is not set. Specify `seed=42` for reproducibility.

---

## What the exam tests on this module

> 🎯 **Exam tests here:**
> - `df.summary()` vs `df.describe()` (percentiles vs not) vs `dbutils.data.summarize` (visual)
> - Outlier removal via std-dev (z-score) or IQR — when each is appropriate
> - Imputation: mean (symmetric continuous), median (skewed continuous), mode (categorical)
> - `Imputer` is an Estimator with strategies "mean" / "median" / "mode"
> - Visualization choice: histogram for continuous, bar for categorical, scatter for two continuous
> - `df.stat.corr` for Pearson/Spearman, `df.stat.crosstab` for two categoricals
> - `df.randomSplit([fractions], seed=)` — seed required, split before transformers

---

## Mini quiz

1. You need the 75th percentile of `customer_value`. Which call gives it: `describe()`, `summary()`, or `approxQuantile()`?
2. Income in your data is right-skewed with a few extreme outliers. Pick: mean ± 3σ trimming, or IQR trimming?
3. You impute the `marital_status` column with `strategy="mean"`. What happens?
4. Show the line of code to split into 80/10/10 train/val/test with a fixed seed.
5. You fit a `StandardScaler` on the full DataFrame, then split. What's wrong?

### Answers

1. All three work. **`summary()` (default args)** gives the 25/50/75% percentiles among other stats. **`approxQuantile("customer_value", [0.75], 0.01)`** gives just the 75th percentile efficiently. **`describe()`** does NOT — it omits percentiles.
2. **IQR.** Mean and stddev are inflated by the outliers themselves, widening the trimming bounds and admitting outliers back in. IQR is robust to outliers.
3. `Imputer.fit` will fail or produce nonsense — `mean` on a string column is undefined. Mode is the correct strategy for categorical columns.
4. `train, val, test = df.randomSplit([0.8, 0.1, 0.1], seed=42)`.
5. The scaler's mean and stddev now include validation and test data — that's data leakage. Always split first, then fit transformers on train only.
