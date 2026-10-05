# Module 12 — Cross-Validation, Grid Search, and Evaluation Metrics

> **Goal of this module:** Master `CrossValidator` vs `TrainValidationSplit`, the `ParamGridBuilder` for grid search, the "how many models trained" math the exam tests directly, and the metric selection logic (F1 vs ROC AUC vs Log Loss, RMSE vs MAE vs R²).
>
> **Maps to exam objectives:** *Describe the benefits and downsides of using cross-validation over a train-validation split · Perform cross-validation as a part of model fitting · Identify the number of models being trained in conjunction with a grid-search and cross-validation process · Use common classification metrics: F1, Log Loss, ROC/AUC · Use common regression metrics: RMSE, MAE, R² · Choose the most appropriate metric for a given scenario · Assess the impact of model complexity and the bias variance tradeoff* (Domain 3, 31%).

---

## Coverage map (verbatim exam objectives → where taught here)

| Verbatim objective | Taught in section |
|---|---|
| Describe the benefits and downsides of CV over train-val split | "Cross-validation BENEFITS / DOWNSIDES" |
| Perform cross-validation as a part of model fitting | "CrossValidator (k-fold CV)" + "Putting it together" |
| Identify the number of models being trained in conjunction with a grid-search and CV process | "The model-count math — exam favorite" + drills |
| Use common classification metrics: F1, Log Loss, ROC/AUC | "Evaluators in Spark ML" + "Choosing the right metric — Binary/Multiclass" |
| Use common regression metrics: RMSE, MAE, R-squared | "Evaluators" + "Choosing the right metric — Regression" |
| Choose the most appropriate metric for a given scenario | "Choosing the right metric" tables |
| Identify the need to exponentiate log-transformed variables before computing metrics | (Covered also in Module 8) "Common pitfalls" + worked example |
| Assess the impact of model complexity and the bias-variance tradeoff | "Bias-variance tradeoff" |

---

## Cross-Validation vs Train-Validation Split

### TrainValidationSplit (single hold-out)

Splits the training data once into train and validation by a fraction. Trains each grid point on the train portion, evaluates on the validation portion.

```python
from pyspark.ml.tuning import TrainValidationSplit

tvs = TrainValidationSplit(
    estimator=pipeline,
    estimatorParamMaps=grid,
    evaluator=BinaryClassificationEvaluator(labelCol="label"),
    trainRatio=0.8,        # 80% train, 20% val
    parallelism=4,
    seed=42,
)
tvs_model = tvs.fit(train_df)
```

**Pros:** Cheap. Trains `grid_size` models.
**Cons:** High variance in the selected hyperparameters because results depend on which 20% landed in val.

### CrossValidator (k-fold CV)

Splits training data into `k` folds. For each grid point, trains `k` models, each on `k-1` folds and validated on the held-out fold. The grid point with the best **average** validation score wins. Then the final model is refit on the full training data with the winning params.

```python
from pyspark.ml.tuning import CrossValidator

cv = CrossValidator(
    estimator=pipeline,
    estimatorParamMaps=grid,
    evaluator=BinaryClassificationEvaluator(labelCol="label"),
    numFolds=5,             # k-fold = 5
    parallelism=4,
    seed=42,
)
cv_model = cv.fit(train_df)
```

**Pros:** Lower variance — every row is used for validation in some fold. Better signal of true performance.
**Cons:** **K times more compute.** Trains `grid_size × k` models.

### Side-by-side

| Property | TrainValidationSplit | CrossValidator |
|----------|----------------------|----------------|
| Models trained | `grid_size` | `grid_size × k` |
| Variance in HPO choice | Higher | Lower |
| Best for | Quick first pass; very large training sets where one split is reliable | Small/medium training sets where you need robust HPO |
| Default split | `trainRatio=0.75` | `numFolds=3` |

> ⚠️ **Exam trap — small data favors CV:**
> - On a **small training set**, single split has high variance → **CV is more robust**.
> - On a **massive training set**, even one split is statistically reliable → **TVS is fine and saves k× compute**.
> The exam may phrase as "you have 100 rows of training data" → CV. "You have 50 million rows" → TVS is acceptable.

---

## ParamGridBuilder — building the grid

```python
from pyspark.ml.tuning import ParamGridBuilder

grid = (ParamGridBuilder()
        .addGrid(rf.numTrees, [50, 100, 200])
        .addGrid(rf.maxDepth, [5, 10, 15])
        .addGrid(rf.minInstancesPerNode, [1, 5])
        .build())

# grid is a list of dicts — one per Cartesian combo: 3 × 3 × 2 = 18 maps
```

`.addGrid(param, values)` adds one hyperparameter to the Cartesian product. `.build()` materializes the full list.

### Single-value `.addGrid` for fixed params

```python
grid = (ParamGridBuilder()
        .addGrid(rf.maxDepth, [5, 10])
        .addGrid(rf.numTrees, [100])       # fixed at 100 for all combos
        .build())
# 2 combos
```

Equivalent to baking `numTrees=100` into the estimator construction, but explicit in the grid.

---

## The model-count math — exam favorite

Given a grid with hyperparameter value counts `n1, n2, ..., nm` and `k` folds:

- **TrainValidationSplit:** trains `n1 × n2 × ... × nm` models (one per grid point), plus a final refit. Often the exam ignores the final refit and just asks the search count.
- **CrossValidator:** trains `n1 × n2 × ... × nm × k` models, plus a final refit on full data with winning params.

### Example (the canonical exam question)

```python
grid = (ParamGridBuilder()
        .addGrid(rf.numTrees, [50, 100])         # 2 values
        .addGrid(rf.maxDepth, [5, 10, 15])       # 3 values
        .build())

cv = CrossValidator(estimator=rf, estimatorParamMaps=grid,
                    evaluator=evaluator, numFolds=3)
```

**How many models does `cv.fit(train_df)` train?**

`2 × 3 × 3 = 18 models` during CV, plus **1 final refit** on full train data = **19 fits total**.

> ⚠️ **Exam trap — counting the refit:** Some exam questions count only the CV models (18 in this case); others include the final refit (19). **Read the question carefully.** "How many CV iterations / how many models during cross-validation" → 18. "Total model fits" → 19. The unambiguous formula `grid_size × k` covers the CV phase.

### Another example (sample Q4 pattern)

```python
grid = (ParamGridBuilder()
        .addGrid(lr.regParam, [0.01, 0.1, 1.0])         # 3
        .addGrid(lr.elasticNetParam, [0.0, 0.5, 1.0])   # 3
        .addGrid(lr.maxIter, [10, 50, 100, 200])        # 4
        .build())

cv = CrossValidator(estimator=lr, estimatorParamMaps=grid,
                    evaluator=evaluator, numFolds=5)
```

`3 × 3 × 4 × 5 = 180 CV models` (+ 1 refit).

---

## `parallelism` parameter

Both `TrainValidationSplit` and `CrossValidator` accept `parallelism`:

```python
cv = CrossValidator(estimator=pipeline, estimatorParamMaps=grid,
                    evaluator=evaluator, numFolds=5,
                    parallelism=4,    # up to 4 model fits concurrently
                    seed=42)
```

- `parallelism=1` (default) — sequential. Easy to reason about; full cluster per fit.
- `parallelism=N > 1` — N models fit simultaneously. Each gets fewer cluster resources but the total wall-clock time goes down.

> ⚠️ **Exam trap — parallelism choice:** Higher `parallelism` is not always better. If each model already saturates the cluster (e.g., training a deep RF on huge data), `parallelism=1` actually finishes faster than `parallelism=4`. Higher `parallelism` helps when individual fits are fast and the bottleneck is sequential scheduling overhead.

---

## Evaluators in Spark ML

| Class | Default metric | Other metric options |
|-------|----------------|----------------------|
| `BinaryClassificationEvaluator` | `areaUnderROC` | `areaUnderPR` |
| `MulticlassClassificationEvaluator` | `f1` | `accuracy`, `weightedPrecision`, `weightedRecall`, `weightedFMeasure`, `logLoss` |
| `RegressionEvaluator` | `rmse` | `mse`, `mae`, `r2`, `var` |
| `RankingEvaluator` | `meanAveragePrecision` | `precisionAtK`, `ndcgAtK`, `meanAveragePrecisionAtK` |
| `ClusteringEvaluator` | `silhouette` | distance: `squaredEuclidean` or `cosine` |

```python
from pyspark.ml.evaluation import (
    BinaryClassificationEvaluator,
    MulticlassClassificationEvaluator,
    RegressionEvaluator,
)

bin_evaluator = BinaryClassificationEvaluator(
    labelCol="label",
    rawPredictionCol="rawPrediction",
    metricName="areaUnderROC",
)

multi_evaluator = MulticlassClassificationEvaluator(
    labelCol="label",
    predictionCol="prediction",
    metricName="f1",
)

reg_evaluator = RegressionEvaluator(
    labelCol="label",
    predictionCol="prediction",
    metricName="rmse",
)

score = bin_evaluator.evaluate(predictions)
```

> ⚠️ **Exam trap — column names matter:**
> - `BinaryClassificationEvaluator` consumes `rawPredictionCol` (or `probabilityCol` depending on Spark version) — NOT `predictionCol`. ROC AUC needs scores, not hard predictions.
> - `MulticlassClassificationEvaluator` consumes `predictionCol`.
> - `RegressionEvaluator` consumes `predictionCol`.

---

## Choosing the right metric

Section 3 explicitly asks: *"Choose the most appropriate metric for a given scenario objective."*

### Binary classification

| Scenario | Metric |
|----------|--------|
| Balanced classes, "how good overall" | **Accuracy** or **ROC AUC** |
| **Imbalanced classes** | **F1** (or **PR AUC**) — accuracy is misleading |
| Imbalanced + need calibrated probabilities | **Log Loss** |
| Want a single number that captures classifier "skill" across thresholds | **ROC AUC** |
| Costs of FP and FN are very different | F1 with appropriate beta, or threshold-tuned precision/recall |

### Multiclass classification

| Scenario | Metric |
|----------|--------|
| Balanced | **Accuracy** |
| Imbalanced or per-class matters | **F1-macro** (unweighted average per class) |
| Imbalanced and class size proportional | **F1-weighted** (size-weighted average) |
| Calibration matters | **Log Loss** |

### Regression

| Scenario | Metric |
|----------|--------|
| Want units (dollars, days), penalize large errors more | **RMSE** |
| Want units, robust to outliers | **MAE** |
| Want unitless, comparability across datasets | **R²** |
| Want percent error | **MAPE** (custom; Spark doesn't have native MAPE) |
| Errors are constant percent (heteroscedastic) | **RMSE on log(target)**, exponentiate predictions for original-scale interpretation |

### Recommendation / Ranking

- **MAP** — mean average precision
- **NDCG@K** — normalized discounted cumulative gain
- **Precision@K** — top-K relevance

> ⚠️ **Exam trap — accuracy on imbalanced data:** "A model with 99% accuracy on a fraud detection problem" sounds great until you realize 1% of transactions are fraud — predicting all-not-fraud gets 99% accuracy. The exam tests this. For imbalanced binary classification, default to **F1 or PR AUC**.

---

## Bias-variance tradeoff

Section 3 asks "*Assess the impact of model complexity and the bias variance tradeoff on model performance.*" The exam tests recognition, not mathematical derivation.

### Symptoms

| Symptom | Diagnosis | Fix |
|---------|-----------|-----|
| Training error LOW, validation error HIGH | Overfitting (high variance, low bias) | Regularize, reduce model complexity, more data, simpler features |
| Training error HIGH, validation error HIGH (similar) | Underfitting (high bias, low variance) | More complex model, more features, longer training, less regularization |
| Training error LOW, validation error LOW | Just right | Ship it |
| Training error LOW, validation error close but a bit higher | Slight overfitting (still good) | Optional: light regularization |

### Knobs that affect bias/variance

- **More trees in RF/GBT** → typically lower variance (averaging effect), no bias change.
- **Deeper trees** → lower bias, higher variance. Trees of depth 1 underfit; depth 50 overfits.
- **Higher learning rate (GBT)** → faster fitting, higher variance.
- **Higher `regParam` (LR)** → more bias, less variance.
- **More training data** → lower variance for free.
- **Fewer features** → higher bias, lower variance.

---

## Cross-validation BENEFITS — exam recall

| Benefit | Why |
|---------|-----|
| Uses all data for training AND validation | Every row is in val exactly once, in train k-1 times |
| Reduces variance of the hyperparameter selection | Average of k scores is more stable than one |
| Detects high-variance models (overfit) | A model that's good on one fold and bad on another is unstable |
| Robust on small/medium data | Single split can be unrepresentative on small data |

## Cross-validation DOWNSIDES

| Downside | Why |
|----------|-----|
| **k× compute** | k fits per grid point |
| **Doesn't help if your CV split contradicts train/test distribution** | E.g., time-series data with random folds — folds will have look-ahead bias. Use TimeSeriesSplit semantics manually |
| **Overlapping folds for tiny data** | With 10 rows and k=5, each fold has 2 rows — meaningless evaluation |

---

## Putting it together — pipeline + CV + grid

```python
from pyspark.ml import Pipeline
from pyspark.ml.feature import Imputer, StringIndexer, VectorAssembler
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
from pyspark.ml.evaluation import BinaryClassificationEvaluator

imputer = Imputer(inputCols=["age", "income"], outputCols=["age_imp", "income_imp"], strategy="median")
indexer = StringIndexer(inputCols=["city"], outputCols=["city_idx"], handleInvalid="keep")
assembler = VectorAssembler(inputCols=["age_imp", "income_imp", "city_idx"], outputCol="features")
rf = RandomForestClassifier(featuresCol="features", labelCol="label", seed=42)

pipeline = Pipeline(stages=[imputer, indexer, assembler, rf])

grid = (ParamGridBuilder()
        .addGrid(rf.numTrees, [50, 100])
        .addGrid(rf.maxDepth, [5, 10])
        .build())   # 4 combos

evaluator = BinaryClassificationEvaluator(labelCol="label", metricName="areaUnderROC")

cv = CrossValidator(
    estimator=pipeline,
    estimatorParamMaps=grid,
    evaluator=evaluator,
    numFolds=3,        # 4 × 3 = 12 fits during CV
    parallelism=2,
    seed=42,
)

cv_model = cv.fit(train_df)
print(cv_model.avgMetrics)           # length-4 list, one avg score per grid point
print(cv_model.bestModel)            # the refit Pipeline trained on full data
```

`cv_model` is a `CrossValidatorModel`. `cv_model.bestModel` is the refit `PipelineModel` trained on full training data with the winning hyperparameters — this is what you `.transform()` for inference.

---

## Complete metric-name catalog — memorize the strings

The exam tests exact `metricName` string values. Multiple-choice answers may differ only in the string.

### `BinaryClassificationEvaluator(metricName=...)`

| String | What it computes | Default? |
|--------|------------------|----------|
| `"areaUnderROC"` | ROC AUC | **Yes (default)** |
| `"areaUnderPR"` | Precision-Recall AUC | No |

### `MulticlassClassificationEvaluator(metricName=...)`

| String | What it computes | Default? |
|--------|------------------|----------|
| `"f1"` | F1 weighted by class support | **Yes** |
| `"accuracy"` | Plain accuracy | No |
| `"weightedPrecision"` | Precision weighted by class support | No |
| `"weightedRecall"` | Recall weighted by class support | No |
| `"weightedFMeasure"` | Custom-beta F-measure, weighted | No |
| `"truePositiveRateByLabel"` | Per-label TPR (specify `metricLabel=`) | No |
| `"falsePositiveRateByLabel"` | Per-label FPR | No |
| `"precisionByLabel"`, `"recallByLabel"`, `"fMeasureByLabel"` | Per-class | No |
| `"logLoss"` | Cross-entropy / log loss (Spark 3.0+) | No |
| `"hammingLoss"` | Element-wise loss | No |

### `RegressionEvaluator(metricName=...)`

| String | What it computes | Default? |
|--------|------------------|----------|
| `"rmse"` | Root Mean Squared Error | **Yes** |
| `"mse"` | Mean Squared Error | No |
| `"mae"` | Mean Absolute Error | No |
| `"r2"` | R² coefficient of determination | No |
| `"var"` | Explained variance | No |

### `ClusteringEvaluator(metricName=...)`

| String | What it computes |
|--------|------------------|
| `"silhouette"` | Silhouette score (default) |

> ⚠️ **Exam trap — string capitalization:** `"areaUnderROC"` not `"AreaUnderROC"` not `"area_under_roc"`. Spark ML's metric strings are camelCase. Wrong case throws `IllegalArgumentException`.

> ⚠️ **Exam trap — `logLoss` is on MULTICLASS evaluator, not binary:** `BinaryClassificationEvaluator` does NOT have `logLoss`. For binary log loss, use `MulticlassClassificationEvaluator(metricName="logLoss")` (binary is just 2-class multiclass).

### Which output column does each evaluator read?

| Evaluator | Reads | Why |
|-----------|-------|-----|
| `BinaryClassificationEvaluator` | `rawPredictionCol` (default `"rawPrediction"`) | ROC needs continuous scores |
| `MulticlassClassificationEvaluator` | `predictionCol` (default `"prediction"`) AND optionally `probabilityCol` (for logLoss) | F1/accuracy work on hard predictions |
| `RegressionEvaluator` | `predictionCol` | Regression has one continuous output |
| `ClusteringEvaluator` | `featuresCol` + `predictionCol` | Silhouette needs original features + cluster assignment |

---

## Model-count math drills — exam favorite pattern

The Mar 2025 official sample Q4 is exactly this pattern (SVM with C × kernel × gamma × 5-fold). Drill until automatic.

### General formula

```
# scikit-learn GridSearchCV / Spark ML CrossValidator
total_CV_fits        = Π(value_counts) × num_folds
total_including_refit = total_CV_fits + 1    # sklearn + Spark ML both do final refit

# TrainValidationSplit (no folds)
total_TVS_fits = Π(value_counts) + 1         # one fit per grid point + final refit
```

### Drill A — official sample Q4

```python
# C in [0.1, 1, 10]  (3)
# kernel in ['linear', 'rbf']  (2)
# gamma in [0.01, 0.1, 1]  (3)
# k = 5 folds
```
**Q:** Total models trained?
**A:** `3 × 2 × 3 × 5 = 90` CV fits (the official answer A). Including the final refit on full data with best params: **91**. Exam answer for sample Q4 is **90**, so the question is counting only CV phase.

### Drill B
```python
.addGrid(rf.numTrees, [50, 100, 200])      # 3
.addGrid(rf.maxDepth, [5, 10])             # 2
.addGrid(rf.minInstancesPerNode, [1, 5, 10])  # 3
numFolds=4
```
**A:** `3 × 2 × 3 × 4 = 72` CV fits; 73 with refit.

### Drill C
```python
.addGrid(lr.regParam, [0.01, 0.1, 1.0])         # 3
.addGrid(lr.elasticNetParam, [0.0, 0.5, 1.0])   # 3
# TrainValidationSplit, not CV
```
**A:** `3 × 3 = 9` grid fits + 1 refit = 10. NO multiplication by k because TVS uses one hold-out.

### Drill D — partial grid (random search)
```python
# Hyperopt with max_evals=50, no CV inside objective
```
**A:** Exactly **50** model trainings. Hyperopt doesn't do CV unless the objective explicitly wraps `cross_val_score` (in which case multiply by inner cv).

### Drill E — Hyperopt + CV inside objective
```python
def objective(params):
    scores = cross_val_score(model, X, y, cv=5)
    ...
# max_evals=50
```
**A:** `50 × 5 = 250` total trainings.

---

## Stratified split — NOT in Spark ML's `randomSplit`

> ⚠️ **Exam trap:** `df.randomSplit([0.7, 0.3], seed=42)` is **non-stratified**. For a 99/1 imbalanced classification, random splits can land 0 positive examples in test by chance.

### Manual stratification with `sampleBy`

```python
# Keep class proportions in train
fractions_train = {0: 0.7, 1: 0.7}   # same fraction per class
train = df.sampleBy("label", fractions=fractions_train, seed=42)
test  = df.subtract(train)
```

`sampleBy(col, fractions: dict)` samples per-key. Setting equal fractions per key preserves the original class ratio in `train` and `test`.

---

## `parallelism` deep-dive — when it helps and when it hurts

```python
cv = CrossValidator(estimator=pipeline, estimatorParamMaps=grid, evaluator=evaluator,
                    numFolds=5, parallelism=4)
```

| Scenario | Recommended `parallelism` |
|----------|---------------------------|
| Each fit is small (fast); cluster has many idle cores | High (8-16) — saturate cluster |
| Each fit is large (slow); cluster is small | Low (1-2) — give each fit max resources |
| Pipeline includes a Spark ML estimator (RF, GBT) | Low (1) — the estimator already uses cluster |
| Pipeline wraps a sklearn estimator via custom wrapper | High — sklearn doesn't use cluster |

> 🎯 **How to recognize this on the exam:** If the question describes a Spark ML pipeline AND asks about `parallelism`, the right answer is usually `parallelism=1` (default) for the reason above. If the question shows a single-node sklearn model wrapped somehow, higher parallelism may apply.

---

## Look-alike API comparison — CV & metrics edition

| Pair | Difference | Exam tell |
|------|------------|-----------|
| `CrossValidator` vs `TrainValidationSplit` | k-fold (k× compute) vs single split | "k-fold" / "cross-validation" → CV. "train ratio 0.8" → TVS |
| `numFolds` (CrossValidator) vs `trainRatio` (TVS) | int (k) vs float (fraction) | Different param names; different types |
| `BinaryClassificationEvaluator` vs `MulticlassClassificationEvaluator` | binary-only metrics (ROC, PR) vs multiclass | Two-class problem still works on multiclass evaluator; opposite is NOT true |
| `RegressionEvaluator` vs `ClusteringEvaluator` | supervised vs unsupervised | Predicting continuous = Regression. Cluster assignment = Clustering |
| `areaUnderROC` vs `areaUnderPR` | threshold-rank metric vs precision-recall AUC | Imbalanced → areaUnderPR is more informative |
| `metricName="f1"` vs `"weightedFMeasure"` | f1 = weighted F-measure with β=1 (default); weightedFMeasure exposes β | Custom beta → weightedFMeasure |
| `ParamGridBuilder().addGrid(p, [v])` vs `.baseOn({p: v})` | grid axis vs constant across all grid points | "fix this hyperparam" → baseOn (less common) or single-element addGrid |
| `cv.fit(df).bestModel` vs `cv.fit(df).avgMetrics` | fitted best Pipeline vs per-grid-point avg score | "the model" → bestModel. "scores list" → avgMetrics |
| `cv_model.subModels` (if `collectSubModels=True`) | per-fold per-grid-point fitted models | Rarely tested but exists |

---

## Worked exam-question walkthroughs

### Worked example: "How many models will be trained?"

**Pattern (matches Sample Q4 verbatim):**
```python
C       in [0.1, 1, 10]
kernel  in ['linear', 'rbf']
gamma   in [0.01, 0.1, 1]
k-fold  = 5
```
**Reasoning:** Total combinations = `3 × 2 × 3 = 18`. Each combination trains `k=5` models. Total = `18 × 5 = 90`.
**Answer:** **90** (matches official answer A).

### Worked example: "Which evaluator for binary classification with imbalanced data?"

**Reasoning:** `BinaryClassificationEvaluator(metricName="areaUnderPR")` is the standard for imbalanced binary. `areaUnderROC` is OK but less informative when positive class is rare. `MulticlassClassificationEvaluator(metricName="f1")` also works for binary.

**Pick the most precise answer the question allows.** If the choices are "ROC vs PR", pick **PR** for imbalanced.

### Worked example: "Diagnose train AUC=0.99, val AUC=0.62"

**Pattern:** Bias-variance reasoning.
**Reasoning:** Huge gap = high variance = overfitting. Low bias (train is great). Fixes: regularize (`regParam`), reduce model complexity (lower `maxDepth`, fewer trees), more training data, simpler features.
**Answer:** Overfitting (high variance, low bias). Apply regularization or reduce capacity.

### Worked example: "Best evaluator for a log-transformed regression target?"

**Pattern:** Model predicts `log(price)`. You want to report RMSE in dollars.

**Reasoning:** Spark's `RegressionEvaluator(metricName="rmse")` computes RMSE in the prediction-column's units — which are LOG-units if you trained on log target. To report dollar-scale RMSE, you must exponentiate first:

```python
preds = model.transform(test_df) \
    .withColumn("prediction_orig", F.expm1("prediction")) \
    .withColumn("label_orig", F.expm1("label"))

evaluator = RegressionEvaluator(
    labelCol="label_orig",
    predictionCol="prediction_orig",
    metricName="rmse",
)
rmse_dollars = evaluator.evaluate(preds)
```

### Worked example: "CrossValidator with `parallelism=8` on a Spark ML pipeline"

**Pattern:** Pipeline ends with `RandomForestClassifier`. `parallelism=8`. Cluster has 8 workers.
**Reasoning:** Each RF fit already uses all 8 workers. Running 8 fits concurrently creates 64-way contention.
**Better:** `parallelism=1` so each RF fit has the full cluster, sequentially.

---

## Output prediction drills

### Drill 1
```python
grid = (ParamGridBuilder()
        .addGrid(rf.numTrees, [50, 100])
        .addGrid(rf.maxDepth, [5, 10, 15])
        .build())
print(len(grid))
```
**Q:** Length?
**A:** `2 × 3 = 6`. Cartesian product.

### Drill 2
```python
cv = CrossValidator(estimator=lr, estimatorParamMaps=grid,
                    evaluator=BinaryClassificationEvaluator(),
                    numFolds=3)
cv_model = cv.fit(train_df)
print(len(cv_model.avgMetrics))
```
**Q:** Length of `avgMetrics`?
**A:** Same as grid size = 6 (one average score per grid point, averaged across the 3 folds).

### Drill 3
```python
evaluator = BinaryClassificationEvaluator(
    labelCol="label",
    metricName="logLoss",   # NOT a valid metric for this evaluator
)
```
**Q:** Result of construction?
**A:** **Error.** `logLoss` is on `MulticlassClassificationEvaluator`, not `BinaryClassificationEvaluator`.

### Drill 4
```python
# Spark's randomSplit on heavily imbalanced data
train, test = df.randomSplit([0.9, 0.1], seed=42)
# Original: 1% positive class
```
**Q:** Guaranteed that test set has positives?
**A:** **No.** `randomSplit` is non-stratified. With 1% positives, you could land 0 in test by chance. Use `sampleBy` for stratification.

### Drill 5
```python
preds = model.transform(test_df)
evaluator = RegressionEvaluator(labelCol="log_price", predictionCol="prediction",
                                metricName="rmse")
rmse = evaluator.evaluate(preds)
# Reported as "the model's RMSE = 0.42"
```
**Q:** Is `0.42` the dollar RMSE?
**A:** **No.** It's the log-space RMSE (because `labelCol="log_price"`). Exponentiate both label and prediction first to get dollar-scale RMSE.

---

## End-to-end mini-scenario

```python
from pyspark.ml import Pipeline
from pyspark.ml.feature import StringIndexer, VectorAssembler
from pyspark.ml.classification import GBTClassifier
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
from pyspark.ml.evaluation import BinaryClassificationEvaluator
import mlflow

train_df, test_df = df.randomSplit([0.8, 0.2], seed=42)

indexer = StringIndexer(inputCol="city", outputCol="city_idx", handleInvalid="keep")
assembler = VectorAssembler(inputCols=["age", "income", "city_idx"], outputCol="features")
gbt = GBTClassifier(featuresCol="features", labelCol="churned", seed=42)

pipeline = Pipeline(stages=[indexer, assembler, gbt])

grid = (ParamGridBuilder()
        .addGrid(gbt.maxDepth, [3, 5, 7])          # 3
        .addGrid(gbt.maxIter, [50, 100, 200])      # 3
        .build())                                   # 9 total

evaluator = BinaryClassificationEvaluator(labelCol="churned", metricName="areaUnderROC")

cv = CrossValidator(
    estimator=pipeline, estimatorParamMaps=grid,
    evaluator=evaluator, numFolds=5,
    parallelism=1,    # GBT is distributed; parallelism=1
    seed=42,
)

with mlflow.start_run(run_name="gbt_cv"):
    cv_model = cv.fit(train_df)                     # 9 × 5 = 45 CV fits + 1 refit = 46
    test_preds = cv_model.transform(test_df)
    test_auc = evaluator.evaluate(test_preds)
    mlflow.log_metric("test_auc", test_auc)
    mlflow.log_param("best_maxDepth",
        cv_model.bestModel.stages[-1].getOrDefault("maxDepth"))
```

**Exam-relevant points exercised:**
- Split BEFORE fitting (no leakage)
- `parallelism=1` because GBT is distributed
- Model count: `3 × 3 × 5 = 45` + 1 refit = 46
- `bestModel.stages[-1]` reaches into the pipeline to grab the chosen GBT
- `avgMetrics` length would be 9 (one per grid point)

---

## Common pitfalls

### Confusing the column the evaluator reads

`BinaryClassificationEvaluator` defaults to `rawPredictionCol="rawPrediction"`, not `predictionCol`. If your model writes its raw scores to a different column, override.

### Counting CV models without folds

"3 grid points, 5-fold CV" → **15** models, not 3. Multiply by k.

### Using CV on time-series with random folds

Random folds break temporal ordering — fold 3 may contain dates that come *after* fold 5 training data. The exam doesn't deeply test time-series CV, but be aware that `CrossValidator` is **random k-fold** by default.

### Reporting CV's avg validation metric as "test performance"

The CV metric is a *proxy* for test performance, computed on held-out folds *within* the training set. Always evaluate the final `cv_model.bestModel` on an **independent test set** (the test split from your original `randomSplit`) for the true generalization estimate.

### Forgetting the refit

`cv_model.bestModel` is automatically refit on the FULL training data (all folds combined) with the winning params. You don't need to refit manually.

---

## What the exam tests on this module

> 🎯 **Exam tests here:**
> - **Model-count math:** `grid_size × k` for CV, `grid_size` for TVS
> - CV vs TVS tradeoffs (variance vs compute)
> - `ParamGridBuilder().addGrid(...).build()` syntax
> - `CrossValidator` parameters: `estimator`, `estimatorParamMaps`, `evaluator`, `numFolds`, `parallelism`
> - Evaluator selection (which class for binary/multiclass/regression)
> - Metric column the evaluator reads (rawPrediction vs prediction vs probability)
> - Metric choice for scenarios (F1 for imbalanced, RMSE for units-matter regression, ROC AUC for threshold-agnostic)
> - Bias-variance tradeoff symptoms and fixes
> - `cv_model.bestModel` is the refit best Pipeline

---

## Mini quiz

1. You define a grid with 4 values for `maxDepth`, 3 values for `numTrees`, 2 values for `minInstancesPerNode`, and run 5-fold CV. How many models train?
2. Your training data is 100 million rows. Should you prefer CV or TVS for HPO? Why?
3. `BinaryClassificationEvaluator(metricName="areaUnderROC")` is reading from which column on the predictions DataFrame?
4. Fraud detection: 0.5% positive class. Your model achieves 99.5% accuracy. Is this good?
5. You have a model with train AUC=0.99 and val AUC=0.65. Diagnose.
6. Convert `ParamGridBuilder().addGrid(rf.numTrees, [50, 100, 200]).addGrid(rf.maxDepth, [5, 10]).build()` into a model count for 3-fold CV.

### Answers

1. `4 × 3 × 2 = 24` grid points × `5` folds = **120 CV fits**, plus 1 final refit = **121 total**.
2. **TVS** is acceptable. 100M rows × even a 20% val split = 20M val rows — statistically reliable. CV's variance-reduction benefit doesn't justify 5× compute. (CV is more critical on small/medium data.)
3. `rawPredictionCol`, default `"rawPrediction"`. ROC AUC needs continuous scores, not hard 0/1 predictions.
4. **No.** Predicting "not fraud" for every transaction gives 99.5% accuracy. The model may not have learned anything. Use **F1** or **PR AUC** for imbalanced classification.
5. **Severe overfitting** (low bias, high variance). Fixes: increase regularization, reduce model complexity (lower `maxDepth`, fewer trees), get more training data, simpler features, or use early stopping.
6. `3 × 2 = 6` grid points × `3` folds = **18 CV fits** + 1 refit = **19 total**.
