# Quiz 02 — ML Workflows / Data Processing (Domain 2, 19%)

> ~28 questions covering Spark DataFrame data prep, pyspark.pandas, feature engineering primitives (Imputer, StringIndexer, OneHotEncoder, VectorAssembler, scaling), log transformations.
>
> Take cold. Budget ~52 minutes (28 × 1m 52s).

---

## Recall

1. `df.describe()` returns count, mean, stddev, min, max. What does `df.summary()` add?
2. The Databricks notebook helper that renders a visual data profile: `dbutils.____(df)`.
3. The Spark ML class that fills missing values via mean / median / mode: `____`.
4. `StringIndexer` becomes a Transformer after `.____(df)` is called.
5. The `OneHotEncoder` class became an Estimator (needs `.fit`) starting in Spark version ____.
6. The Transformer-only class that concatenates multiple columns into a single Vector column: `____`.
7. The pyspark.pandas import: `import pyspark.____ as ps`.
8. The pyspark.pandas method to convert to a Spark DataFrame: `psdf.____()`.
9. The argument to set on `StringIndexer` so unseen test categories don't throw: `handleInvalid="____"`.
10. The Spark DataFrame call to split into train/val/test with reproducibility: `df.randomSplit([...], ____=42)`.

## Apply

11. Income in your data spans $5,000 to $1,500,000 and is heavily right-skewed. Which transformation is appropriate?
12. Your validation set has cities not seen in training. The pipeline throws when you `transform()` it. Fix?
13. You have null values in numeric `age` and `income` columns. The data is skewed. Which `Imputer.strategy` do you pick?
14. Compute the 90th percentile of `revenue` on a 1 TB Spark DataFrame efficiently.
15. You're scaling features before a `RandomForestClassifier`. Is `StandardScaler` necessary?
16. You have a `gender` column with values `M`, `F`, `Other`. You're training a logistic regression. Which encoding stages do you need (in order)?
17. Same data, but the model is XGBoost. Which stages from Q16 can you drop?
18. Your data has the column `txn_amount` ranging from $0 to $50,000 with most transactions under $100. You'll model this as a regression target. What transformation should you consider?
19. You compute `mlflow.log_metric("rmse", 0.42)` after training on `log1p(txn_amount)`. The number is in what units?
20. Sketch the order of stages in a Pipeline that handles: imputation of `age`/`income` (median), encoding of `city` (high cardinality), and a logistic regression on `is_active`.
21. You have 200 MB of data in a pandas DataFrame. Should you convert it to `pyspark.pandas` to "scale"?
22. You want pandas idioms but the dataset is 800 GB. Which API?

## Diagnose

23. After `randomSplit([0.7, 0.15, 0.15])`, the validation accuracy is wildly different on every run. Diagnose.
24. You fit `StandardScaler` on the full DataFrame, then split. Train MSE is fine; validation MSE is way worse than expected. Diagnose.
25. Your IQR outlier removal on a normally-distributed feature drops 0% of rows; on a heavily skewed feature it drops 18%. Is the heavy-skew result OK?
26. You impute the `marital_status` (string column) with `strategy="mean"`. What happens?

## Defend

27. Argue why `pyspark.pandas` is the wrong tool for an 80 MB CSV file on a laptop.
28. Defend the choice of median over mean imputation for transaction amounts.

---

## Answers

1. **25th / 50th / 75th percentiles** (and works on string columns too).
2. `dbutils.data.summarize(df)`.
3. `Imputer`.
4. `.fit(df)` — `StringIndexer` is an Estimator; `.fit` returns a `StringIndexerModel` Transformer.
5. **Spark 3.0**. In Spark 2.x, `OneHotEncoder` was a Transformer; the Estimator was called `OneHotEncoderEstimator` and was renamed in 3.0.
6. `VectorAssembler`.
7. `import pyspark.pandas as ps`.
8. `psdf.to_spark()`.
9. `handleInvalid="keep"`.
10. `seed=42`.
11. **Log transformation** (`log1p` to handle any zeros) — right-skewed + multi-order-of-magnitude range.
12. Set `handleInvalid="keep"` on the `StringIndexer` (and on the `OneHotEncoder` if present). Unseen labels get a new index instead of throwing.
13. **Median.** Skewed data has outliers; mean is pulled by them. Median is robust.
14. `df.approxQuantile("revenue", [0.9], 0.01)` — relative error of 1% is plenty for exam scale and is fast on huge data.
15. **No.** Tree splits are scale-invariant. Scaling has no effect on RF. Skip it.
16. `StringIndexer` (gender → integer) → `OneHotEncoder` (integer → sparse vector) → `VectorAssembler` (combine into features) → `LogisticRegression`.
17. **Drop `OneHotEncoder`.** XGBoost (and any tree-based method) handles integer-encoded categoricals fine. The `StringIndexer` is still needed to get from string to integer.
18. **Log transformation** (`log1p` because of zeros). Heavy right skew, multi-order-of-magnitude.
19. **Log units of dollars**, not dollars. To report RMSE in dollars, exponentiate predictions with `np.expm1` before computing the metric.
20. ```
    Imputer(age, income, strategy=median)
    → StringIndexer(city, handleInvalid="keep")
    → OneHotEncoder(city_idx, handleInvalid="keep")  # for logistic regression
    → VectorAssembler(features)
    → LogisticRegression(featuresCol="features", labelCol="is_active")
    ```
21. **No.** 200 MB is small. pandas is faster on driver. Spark overhead would dominate. Stay in pandas.
22. **`pyspark.pandas`** (or native Spark DataFrame). 800 GB doesn't fit on a single node.
23. **No `seed`** argument was set. `randomSplit` is stochastic; without a seed, each call gives a different split. Add `seed=42`.
24. **Data leakage.** The scaler's mean and stddev include val/test data. Split FIRST, then fit the scaler on train only, then transform all three.
25. Heavily-skewed data has many values flagged as outliers by IQR by design. 18% may be too aggressive; consider a wider multiplier (e.g., `Q1 − 3*IQR`) or log-transform first then IQR. Not strictly wrong, but worth examining.
26. Either an error (Imputer can't compute mean on a string column) or nonsensical behavior. Use `strategy="mode"` for categorical columns.
27. (a) 80 MB fits comfortably on one machine. (b) Spark adds task scheduling, JVM serialization, and Catalyst overhead — slower on this scale. (c) Local pandas with sklearn is the native fit-on-array workflow. (d) Distributed processing has value only when data exceeds single-node memory.
28. (a) Transaction amounts are right-skewed; mean is pulled by large transactions. (b) Median represents the "typical" transaction and is robust to outliers. (c) Filling missing values with the median doesn't distort the distribution as much as filling with an inflated mean. (d) Production data may have outlier behavior absent in training; median imputation generalizes better.
