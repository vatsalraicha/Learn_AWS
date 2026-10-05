# Module 9 — Spark ML Algorithms

> **Goal of this module:** Recognize the Spark ML algorithm classes by name + signature, know what's tunable on each, and pick the right algorithm for a given scenario. The exam doesn't test deep ML theory (you already have that); it tests **Databricks-specific API knowledge** plus the "select algorithm for scenario" reasoning.
>
> **Maps to exam objectives:** *Use ML foundations to select the appropriate algorithm for a given model scenario · Compare estimators and transformers · Develop a training pipeline · Identify methods to mitigate data imbalance* (Domain 3, 31%).

---

## Coverage map (verbatim exam objectives → where taught here)

| Verbatim objective | Taught in section |
|---|---|
| Use ML foundations to select the appropriate algorithm for a scenario | "Algorithm selection — exam patterns" |
| Compare estimators and transformers | (Cross-references Module 8) "All Spark ML algorithm classes are Estimators" |
| Develop a training pipeline | "Training pipeline pattern — algorithm at the end" |
| Identify methods to mitigate data imbalance in training data | "Handling class imbalance" (5 options) |

---

## Look-alike API comparison — algorithms edition

| Pair | Difference | Exam tell |
|------|------------|-----------|
| `LogisticRegression` vs `LinearRegression` | classification vs regression | Targets are classes vs continuous |
| `LogisticRegression(family="binomial")` vs `family="multinomial"` | binary vs >2 classes | Multi-class problem with LR → multinomial |
| `RandomForestClassifier` vs `RandomForestRegressor` | discrete labels vs continuous target | Different `impurity` options |
| `GBTClassifier` vs `RandomForestClassifier` | sequential boosting vs bagged averaging; **GBTClassifier is BINARY ONLY** | Multi-class problem → use RF, NOT GBT |
| `GBTRegressor` vs `LinearRegression` | nonlinear boosted trees vs linear | Linear assumption → LR; complex relationships → GBT |
| `weightCol` vs class balancing via resampling | native Spark ML support vs preprocessing | Question says "Spark ML native" → weightCol |
| `KMeans(k=5)` vs `BisectingKMeans(k=5)` | flat k-means vs hierarchical (top-down splits) | Hierarchical structure desired → BisectingKMeans |
| `ALS` vs `KMeans` for recommendations | matrix factorization (user-item ratings) vs cluster-then-recommend | Explicit ratings → ALS |
| `pyspark.ml.LogisticRegression` vs `pyspark.mllib.classification.LogisticRegressionWithLBFGS` | DataFrame API (current) vs RDD API (frozen) | Always `pyspark.ml` for new code |

> ⚠️ **Exam trap — GBTClassifier is binary only:** `GBTClassifier` in Spark ML supports **binary classification only**. For multi-class boosting, use `OneVsRest(classifier=GBTClassifier(...))` or switch to XGBoost. The exam may give a multi-class scenario and offer GBT as a distractor.

---

## Algorithm catalog — `pyspark.ml`

All Spark ML algorithm classes are **Estimators**. Calling `.fit(df)` returns a fitted `*Model` Transformer.

### Classification

| Class | Algorithm | Typical use |
|-------|-----------|-------------|
| `LogisticRegression` | Logistic regression (binary + multinomial) | Linear baseline, interpretable coefficients |
| `DecisionTreeClassifier` | Single decision tree | Interpretable, low-variance baseline |
| `RandomForestClassifier` | Random forest | Strong baseline, handles nonlinearity, low tuning |
| `GBTClassifier` | Gradient-boosted trees | High accuracy on tabular |
| `LinearSVC` | Linear support vector classifier | Linear separator (binary only) |
| `NaiveBayes` | Naive Bayes (multinomial/Gaussian/Bernoulli) | Text classification baseline |
| `MultilayerPerceptronClassifier` | Feedforward neural network | Rare on Spark ML; deep learning typically uses PyTorch |
| `OneVsRest` | Wraps a binary classifier for multiclass | Adapter pattern |

### Regression

| Class | Algorithm |
|-------|-----------|
| `LinearRegression` | OLS / regularized (Ridge / Lasso / ElasticNet) |
| `DecisionTreeRegressor` | Single regression tree |
| `RandomForestRegressor` | Random forest for regression |
| `GBTRegressor` | Gradient-boosted regression trees |
| `GeneralizedLinearRegression` | GLM (Gaussian, Poisson, Gamma, Binomial families) |
| `IsotonicRegression` | Monotonic regression |
| `AFTSurvivalRegression` | Accelerated failure time (survival) |

### Clustering

| Class | Algorithm |
|-------|-----------|
| `KMeans` | k-means clustering |
| `BisectingKMeans` | Hierarchical variant of k-means |
| `GaussianMixture` | Gaussian mixture model |
| `LDA` | Latent Dirichlet Allocation (topic modeling) |
| `PowerIterationClustering` | Graph-based clustering |

### Recommendation

| Class | Algorithm |
|-------|-----------|
| `ALS` | Alternating Least Squares matrix factorization |

### Other

| Class | Algorithm |
|-------|-----------|
| `FPGrowth` | Frequent itemset mining (association rules) |
| `IsolationForest` | (in some Databricks distributions) anomaly detection |

---

## Algorithm selection — exam patterns

Section 3 starts with: *"Use ML foundations to select the appropriate algorithm for a given model scenario."*

### Pattern: "tabular data, predict yes/no"

→ **Random Forest** or **GBT** classifier. RF for ease and low tuning; GBT for accuracy with proper tuning.

### Pattern: "predict a continuous value, interpretable"

→ **Linear regression** (with regularization for many features).

### Pattern: "predict a continuous value, nonlinear relationships"

→ **GBT regressor** or **Random Forest regressor**.

### Pattern: "cluster customers into segments"

→ **k-means** (most common) or **bisecting k-means** for hierarchical structure.

### Pattern: "recommend items to users from interactions"

→ **ALS** (matrix factorization).

### Pattern: "predict survival time / time to event"

→ **AFTSurvivalRegression**.

### Pattern: "text classification"

→ **NaiveBayes** for fast baseline or **LogisticRegression** with TF-IDF features.

### Pattern: "rare class, want probability calibration"

→ **LogisticRegression** (well-calibrated by design) or **GBT with isotonic post-calibration**.

> ⚠️ **Exam trap — picking deep learning:** Spark ML's `MultilayerPerceptronClassifier` exists but the exam doesn't recommend it for tabular classification. The expected answer for tabular is tree-based (RF / GBT). Deep learning is for unstructured data (text, image), which is largely out of scope for the Associate exam.

---

## Common API pattern — train a classifier

```python
from pyspark.ml.classification import RandomForestClassifier

rf = RandomForestClassifier(
    featuresCol="features",          # Vector column name
    labelCol="churned",
    predictionCol="prediction",      # default
    probabilityCol="probability",    # default
    rawPredictionCol="rawPrediction",# default
    numTrees=100,
    maxDepth=10,
    minInstancesPerNode=5,
    seed=42,
)

rf_model = rf.fit(train_df)
predictions = rf_model.transform(test_df)

# predictions has: original cols + features + rawPrediction + probability + prediction
```

### Standard column names you'll see on every classifier

- `featuresCol` (input) — a Vector column
- `labelCol` (input) — the target
- `predictionCol` (output) — single predicted class index
- `probabilityCol` (output) — probability vector across classes
- `rawPredictionCol` (output) — raw scores (logits)

---

## Hyperparameters worth knowing per algorithm

The exam doesn't quiz exact defaults, but recognize the parameter names.

### `RandomForestClassifier` / `RandomForestRegressor`

- `numTrees` — number of trees in the forest (default 20; 100+ for good models)
- `maxDepth` — max depth of each tree (default 5; trees deeper than 10-15 overfit)
- `minInstancesPerNode` — minimum samples to split (default 1)
- `featureSubsetStrategy` — `"auto"`, `"all"`, `"sqrt"`, `"log2"`, fraction (e.g., `"0.3"`)
- `subsamplingRate` — row sampling fraction per tree (default 1.0)
- `impurity` — `"gini"` (default, classifier) or `"entropy"`; for regressor: `"variance"`

### `GBTClassifier` / `GBTRegressor`

- `maxIter` — number of boosting rounds (default 20; often 100+)
- `maxDepth` — depth per tree (often shallower than RF: 4-6)
- `stepSize` — learning rate (default 0.1)
- `subsamplingRate` — row sampling per round

### `LogisticRegression`

- `maxIter` — max iterations of LBFGS/L-BFGS optimizer (default 100)
- `regParam` — regularization strength (default 0.0)
- `elasticNetParam` — 0=Ridge, 1=Lasso, in-between=ElasticNet (default 0.0)
- `family` — `"auto"`, `"binomial"`, `"multinomial"`
- `weightCol` — column with per-row weights (for class imbalance — see below)
- `threshold` — classification threshold (default 0.5 for binary)

### `LinearRegression`

- `maxIter` (default 100)
- `regParam` (default 0.0)
- `elasticNetParam` (default 0.0 = Ridge; 1.0 = Lasso)
- `weightCol`
- `solver` — `"auto"`, `"l-bfgs"`, `"normal"`

### `KMeans`

- `k` — number of clusters (required)
- `maxIter` (default 20)
- `tol` — convergence tolerance
- `seed`
- `initMode` — `"k-means||"` (default, parallel kmeans++ ) or `"random"`

---

## Handling class imbalance

Section 3 explicitly tests *"Identify methods to mitigate data imbalance in training data."*

### Option 1: `weightCol` — cost-sensitive learning (Spark ML native, preferred)

Add a column to your DataFrame that weights each row inversely to its class frequency:

```python
from pyspark.sql import functions as F

# Compute per-class weight
class_counts = train_df.groupBy("churned").count().collect()
total = sum(c["count"] for c in class_counts)
weights = {c["churned"]: total / (2 * c["count"]) for c in class_counts}

# Add weight column
train_df = train_df.withColumn(
    "weight",
    F.when(F.col("churned") == 1, weights[1]).otherwise(weights[0]),
)

# Pass weightCol to the estimator
lr = LogisticRegression(
    featuresCol="features",
    labelCol="churned",
    weightCol="weight",
)
```

> ⚠️ **Exam trap:** When the exam lists multiple imbalance mitigations, **`weightCol` is usually the Databricks-preferred answer**. It works natively in Spark ML (LR, RF, GBT, NaiveBayes all support it), doesn't require resampling, and is a first-class hyperparameter.

### Option 2: Undersample the majority class

```python
majority = train_df.filter(F.col("churned") == 0)
minority = train_df.filter(F.col("churned") == 1)

# Sample majority down to ~ same size as minority
majority_sample = majority.sample(fraction=minority.count() / majority.count(), seed=42)
balanced = majority_sample.union(minority)
```

Risk: information loss. Use when majority is overwhelmingly large.

### Option 3: Oversample the minority class

```python
# Naive: just sample with replacement
minority_oversampled = minority.sample(withReplacement=True, fraction=5.0, seed=42)
balanced = majority.union(minority_oversampled)
```

Risk: overfits on duplicates. Less common in production than weight-col approach.

### Option 4: SMOTE — synthetic minority oversampling

Not native to Spark ML. Requires `imblearn` on pandas data:

```python
from imblearn.over_sampling import SMOTE

X_train_pd = train_df.toPandas().drop("churned", axis=1)
y_train_pd = train_df.toPandas()["churned"]
X_res, y_res = SMOTE(random_state=42).fit_resample(X_train_pd, y_train_pd)
```

Only viable if your training data fits on driver memory. Out of native Spark ML scope.

### Option 5: Threshold tuning

Train on imbalanced data with default 0.5 threshold; then lower the threshold based on precision/recall tradeoff:

```python
# Predict probabilities, choose a custom threshold
predictions = model.transform(val_df)

# Vary threshold and observe precision/recall
custom_threshold = 0.3
predictions_at_t = predictions.withColumn(
    "prediction_custom",
    F.when(F.col("probability")[1] > custom_threshold, 1.0).otherwise(0.0),
)
```

This is post-hoc — doesn't change training.

---

## `LogisticRegression` — exam recall

```python
from pyspark.ml.classification import LogisticRegression

lr = LogisticRegression(
    featuresCol="features",
    labelCol="label",
    maxIter=100,
    regParam=0.01,
    elasticNetParam=0.5,    # ElasticNet (Ridge + Lasso)
    family="binomial",
    weightCol="weight",
)

lr_model = lr.fit(train_df)
print(lr_model.coefficients)   # feature weights
print(lr_model.intercept)
print(lr_model.summary.roc.show())   # built-in evaluation
```

**`summary` attribute** on the fitted model gives a `BinaryLogisticRegressionTrainingSummary` (or multinomial counterpart) with ROC curve data, areaUnderROC, accuracy, F1 — all computed on training data.

---

## `LinearRegression` — exam recall

```python
from pyspark.ml.regression import LinearRegression

lr = LinearRegression(
    featuresCol="features",
    labelCol="target",
    maxIter=100,
    regParam=0.1,
    elasticNetParam=1.0,    # pure Lasso
)

lr_model = lr.fit(train_df)
print(lr_model.coefficients)
print(lr_model.intercept)
print(lr_model.summary.rootMeanSquaredError)
print(lr_model.summary.r2)
```

---

## `KMeans` — exam recall

```python
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator

km = KMeans(featuresCol="features", k=5, seed=42)
km_model = km.fit(train_df)

predictions = km_model.transform(test_df)
# predictions has: features + prediction (cluster index 0..k-1)

print(km_model.clusterCenters())   # list of NumPy arrays

evaluator = ClusteringEvaluator(featuresCol="features", predictionCol="prediction")
silhouette = evaluator.evaluate(predictions)
```

### Choosing `k`

- **Elbow method** — plot WSS (within-set-sum-squared-error) vs k; pick the "elbow."
- **Silhouette score** — choose k that maximizes silhouette (range [-1, 1]; higher = better).
- `km_model.summary.trainingCost` gives WSS.

---

## `pyspark.mllib` — the frozen legacy

`pyspark.mllib` is the RDD-based ML library. It exists for backward compatibility and is **frozen** since Spark 3.0 — no new features, only bug fixes.

You should:
- **Recognize the name** on the exam (if it shows up as a distractor)
- **Never use it for new code** — use `pyspark.ml` (DataFrame-based) instead

The exam may test "`pyspark.ml` vs `pyspark.mllib`" — the answer is always `pyspark.ml` for new work.

---

## Training pipeline pattern — algorithm at the end

```python
from pyspark.ml import Pipeline
from pyspark.ml.feature import Imputer, StringIndexer, VectorAssembler
from pyspark.ml.classification import GBTClassifier

imputer = Imputer(
    inputCols=["age", "income"],
    outputCols=["age_imp", "income_imp"],
    strategy="median",
)
indexer = StringIndexer(
    inputCols=["city", "gender"],
    outputCols=["city_idx", "gender_idx"],
    handleInvalid="keep",
)
assembler = VectorAssembler(
    inputCols=["age_imp", "income_imp", "city_idx", "gender_idx"],   # no OHE — GBT handles ints
    outputCol="features",
)
gbt = GBTClassifier(
    featuresCol="features",
    labelCol="churned",
    maxIter=100,
    maxDepth=5,
    seed=42,
)

pipeline = Pipeline(stages=[imputer, indexer, assembler, gbt])
pipeline_model = pipeline.fit(train_df)

predictions = pipeline_model.transform(test_df)
```

The algorithm sits at the **end** of the pipeline. All preprocessing happens before; only the algorithm's `*Model` does inference.

---

## Common pitfalls

### Picking deep learning for tabular

Spark ML's `MultilayerPerceptronClassifier` is rarely the right answer on the exam. Tree-based methods dominate tabular ML. Save deep learning for unstructured data.

### Forgetting `featuresCol` is a Vector

All Spark ML algorithms expect a single Vector column for input features, not multiple scalar columns. That's why every pipeline ends with `VectorAssembler` before the algorithm.

### Using class weights AND oversampling

Pick one. Combining can produce nonsensical effective class distributions.

### Confusing `pyspark.ml` and `pyspark.mllib`

`pyspark.ml` is current (DataFrame-based). `pyspark.mllib` is frozen (RDD-based). Don't mix imports.

### Setting `seed` inconsistently

For reproducibility, set `seed` on **every** stochastic component: `randomSplit`, every `*Classifier`/`*Regressor`/`KMeans`. One missing seed and your "reproducible" pipeline isn't.

---

## Worked exam-question walkthroughs

### Worked example (verbatim official Q3): "Mitigate imbalance bias toward non-churn"

**Options:**
A. Normalize features — wrong; doesn't address imbalance
B. Cost-sensitive learning with higher cost for minority — **CORRECT**
C. Collect MORE non-churn data — makes imbalance WORSE
D. Simpler model — doesn't address imbalance

**Answer:** B. Cost-sensitive = `weightCol` in Spark ML (higher weight on minority class). Matches official answer B.

### Worked example: "GBT for 5-class problem"

**Pattern:** Question lists `GBTClassifier(...)` for a 5-class target.

**Bug:** GBTClassifier is binary-only.

**Fix:** `OneVsRest(classifier=GBTClassifier(...))` to wrap for multi-class. Or use `RandomForestClassifier` directly.

### Worked example: "Choose algorithm for tabular regression with nonlinear effects"

**Reasoning:** Tabular + nonlinear → GBT or RF regressor. Tabular + linear → LinearRegression with regularization. Tabular + tiny data → ridge regression (LinearRegression with `regParam`).

### Worked example: "Pipeline order — what comes last?"

**Decision rule:** Algorithm (estimator producing the predictions) always at the END. Preprocessing transformers (Imputer, StringIndexer, OneHotEncoder, VectorAssembler) come BEFORE the algorithm.

---

## Output prediction drills

### Drill 1
```python
rf = RandomForestClassifier(numTrees=100, maxDepth=5)
rf_model = rf.fit(train_df)
preds = rf_model.transform(test_df)
preds.columns
```
**Q:** Output columns added?
**A:** Original columns + `rawPrediction` (vector) + `probability` (vector) + `prediction` (scalar class).

### Drill 2
```python
gbt = GBTClassifier(featuresCol="features", labelCol="multiclass_target")
gbt.fit(df_with_5_classes)
```
**Q:** Result?
**A:** **Error or undefined behavior.** GBTClassifier is binary-only.

### Drill 3
```python
LinearRegression(elasticNetParam=0.0)   # vs elasticNetParam=1.0
```
**Q:** Difference in regularization?
**A:** `elasticNetParam=0.0` = pure Ridge (L2). `elasticNetParam=1.0` = pure Lasso (L1). In-between = ElasticNet mix.

### Drill 4
```python
km = KMeans(k=5, seed=42).fit(df)
print(km.summary.trainingCost)
```
**Q:** What does `trainingCost` represent?
**A:** WSS (Within-Set Sum of Squared errors). Lower = tighter clusters. Used for elbow method.

---

## What the exam tests on this module

> 🎯 **Exam tests here:**
> - Algorithm by name: `RandomForestClassifier`, `GBTRegressor`, `LogisticRegression`, `LinearRegression`, `KMeans`
> - Algorithm selection for scenario: tabular → trees; recommendation → ALS; clustering → KMeans
> - Class imbalance methods: `weightCol` (preferred), undersampling, oversampling, threshold tuning
> - `pyspark.ml` (current) vs `pyspark.mllib` (frozen — don't use)
> - Common hyperparameters: `numTrees`/`maxDepth`/`maxIter`/`regParam`/`elasticNetParam`
> - Pipeline has algorithm at the end

---

## Mini quiz

1. Your data is heavily imbalanced (1% positive). The hiring manager asks you to handle this in Spark ML "natively." What do you do?
2. Recommend an algorithm for: 50 GB tabular data, binary classification, want best accuracy with reasonable training time.
3. `pyspark.mllib.classification.LogisticRegressionWithLBFGS` — is this safe to use for new code?
4. You want to cluster customers and pick the right number of clusters. Name two methods.
5. Why does every Spark ML algorithm take exactly one `featuresCol`?

### Answers

1. **Use `weightCol`.** Add a per-row weight column inverse to class frequency, pass it to `LogisticRegression(weightCol="weight")` (or any classifier that supports it — most do). Native to Spark ML, no resampling required.
2. **GBT classifier** (`GBTClassifier`). Tabular + accuracy-focused → boosted trees. For even better accuracy on the same data, XGBoost via the `xgboost-spark` integration; for the exam, stick with `GBTClassifier`.
3. **No.** `pyspark.mllib` is frozen since Spark 3.0. Use `pyspark.ml.classification.LogisticRegression` (DataFrame-based) for new code.
4. **Elbow method** (plot WSS vs k, pick the elbow) and **silhouette score** (choose k that maximizes silhouette via `ClusteringEvaluator`).
5. Spark ML algorithms consume a single Vector column for features. `VectorAssembler` is the universal stage that concatenates multiple scalar columns into that one Vector. This unification is why Pipelines compose cleanly.
