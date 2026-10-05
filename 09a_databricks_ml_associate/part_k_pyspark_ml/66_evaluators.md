# Chapter 66 — Evaluators in pyspark.ml

> **Goal of this chapter:** to teach the three Evaluator classes in `pyspark.ml.evaluation` — `BinaryClassificationEvaluator`, `MulticlassClassificationEvaluator`, `RegressionEvaluator` — and to make absolutely sure you know which Evaluator wants which input column, which metricName is the default, and what each metric actually computes. Picking the right evaluator is essential for CrossValidator to optimise the right thing. The exam tests these defaults explicitly; the job rewards knowing them cold.

---

## 66.1 What an Evaluator is and why this chapter is small but important

Chapter 65 left a hole. The CrossValidator needs to compare grid combinations. Comparison is done by an **Evaluator**: an object with one important method,

```python
evaluator.evaluate(df: DataFrame) -> float
```

It takes a DataFrame containing predictions and labels, returns a single scalar metric, and is the comparison primitive used by every CV-style API in `pyspark.ml`.

The Evaluator is conceptually simple, but two things make it a frequent source of bugs.

First, **the right Evaluator depends on the task type** (binary classification vs. multiclass vs. regression). Picking the wrong class produces either a runtime error or, worse, a *silently wrong* metric.

Second, **the right input column depends on the Evaluator**. Some want `rawPrediction`, some want `prediction`, some want `probability`. The error message when you wire the wrong column is sometimes cryptic. Knowing which is which avoids hours of debugging.

This chapter walks the three Evaluator classes and their metrics, gives you the rule for which column each wants, and shows the common patterns. It's shorter than its siblings because the conceptual machinery was already built in Part H (the chapters on classification and regression metrics). What's new here is the API surface.

---

## 66.2 The three Evaluator classes at a glance

| Task | Class | Inputs | Default `metricName` |
|---|---|---|---|
| Binary classification | `BinaryClassificationEvaluator` | `rawPredictionCol`, `labelCol` | `"areaUnderROC"` |
| Multi-class classification | `MulticlassClassificationEvaluator` | `predictionCol`, `labelCol` | `"f1"` |
| Regression | `RegressionEvaluator` | `predictionCol`, `labelCol` | `"rmse"` |

That's the entire `pyspark.ml.evaluation` surface area for the exam. (There are also `RankingEvaluator` and `ClusteringEvaluator` classes; the latter we'll touch briefly. Ranking is out of scope.)

Notice the input column difference. Binary classification's evaluator wants the **raw scores** (the pre-sigmoid Vector of class scores, or the equivalent — a Vector of length 2 with positive-class score in position 1). Multi-class and regression evaluators want the **prediction** column (the argmax class for multiclass, the predicted value for regression). The reason for the asymmetry comes next.

---

## 66.3 BinaryClassificationEvaluator

```python
from pyspark.ml.evaluation import BinaryClassificationEvaluator

evaluator = BinaryClassificationEvaluator(
    rawPredictionCol="rawPrediction",
    labelCol="label",
    metricName="areaUnderROC",   # or "areaUnderPR"
)
auroc = evaluator.evaluate(predictions_df)
```

### 66.3.1 Why it wants `rawPrediction`, not `prediction`

Both metrics that `BinaryClassificationEvaluator` supports — area under ROC and area under PR — are computed across *all possible thresholds*. The metric is a property of the *ranking* the model produces, not of any single thresholded decision.

To compute a ROC curve, you need each row's *score* (so you can sort by score and sweep the threshold). The `prediction` column is the already-thresholded 0/1 decision; sorting by that gives you no information for the curve. The `rawPrediction` column (or equivalently `probabilityCol`, which is just `rawPrediction` after sigmoid) is what you need.

Pyspark.ml classifier models output `rawPrediction` as a length-2 Vector: `[score_class_0, score_class_1]`. The evaluator uses position 1 (the positive-class score) for the ranking. If your model doesn't produce a length-2 Vector here, the evaluator will fail; this is one reason you should always use a real `pyspark.ml.classification` model, not a hand-rolled UDF, when feeding into a CV.

### 66.3.2 Supported metrics

Only two:

- **`"areaUnderROC"`** (default). Area under the ROC curve. 0.5 = random; 1.0 = perfect.
- **`"areaUnderPR"`** (a.k.a. "average precision"). Area under the precision-recall curve. Lower bound is the positive-class base rate (not 0.5).

Chapter 43 derived ROC; Chapter 44 made the case for PR over ROC when classes are imbalanced. For the exam: with 50% balance, both are reasonable; with severe imbalance (1% positives), prefer `"areaUnderPR"` because ROC will look optimistically good even for poor models.

### 66.3.3 A subtle pitfall: `probabilityCol`

You might be tempted to do this:

```python
# DOESN'T WORK
evaluator = BinaryClassificationEvaluator(probabilityCol="probability", ...)
```

There is no `probabilityCol` parameter on `BinaryClassificationEvaluator`. The parameter is `rawPredictionCol`, and you pass the column that contains either raw logits or probabilities (a length-2 Vector). The evaluator handles both. The naming is unfortunate.

For models you train via `pyspark.ml`, the default `rawPredictionCol="rawPrediction"` matches, and you don't need to set it explicitly.

---

## 66.4 MulticlassClassificationEvaluator

```python
from pyspark.ml.evaluation import MulticlassClassificationEvaluator

evaluator = MulticlassClassificationEvaluator(
    predictionCol="prediction",
    labelCol="label",
    metricName="f1",     # default
)
f1 = evaluator.evaluate(predictions_df)
```

### 66.4.1 Why it wants `prediction`, not `rawPrediction`

The metrics this evaluator supports — accuracy, precision, recall, F1, log loss — are computed on the *hard predictions*, not on the raw scores. (Log loss is the exception; we'll get to it.)

In `pyspark.ml`, the `prediction` column holds the integer-encoded class label (as a double, awkwardly). For a 4-class problem, values are `0.0`, `1.0`, `2.0`, `3.0`. The evaluator compares these to the `label` column.

### 66.4.2 The full metric menu

The `metricName` parameter accepts a long list:

```
"f1"                          (default)
"accuracy"
"weightedPrecision"
"weightedRecall"
"weightedFMeasure"
"weightedTruePositiveRate"
"weightedFalsePositiveRate"
"truePositiveRateByLabel"
"falsePositiveRateByLabel"
"precisionByLabel"
"recallByLabel"
"fMeasureByLabel"
"hammingLoss"
"logLoss"
```

Most are self-explanatory if you remember Chapters 42 and 47. The "*ByLabel" variants compute the metric for a single specified label (set `metricLabel`). The "weighted*" variants aggregate per-class metrics weighted by class support. The unweighted-aggregation variants ("macro") are *not* directly named — see below.

### 66.4.3 The micro / macro / weighted question — and pyspark's F1 default

This is the most exam-tested detail in this chapter. When you have multiple classes, there are three standard ways to aggregate a per-class metric (precision, recall, F1) into a single number:

- **Micro**: pool TP, FP, FN across all classes, then compute the metric on the pool. For multi-class, micro-averaged precision = recall = F1 = accuracy. (Yes — they're all the same number under micro.) Doesn't appear in pyspark's API as a named option; just use `"accuracy"`.
- **Macro**: compute the metric for each class independently, then take the unweighted mean. Treats every class equally regardless of class size.
- **Weighted**: compute the metric for each class, take the mean weighted by per-class support (number of true examples in that class).

Pyspark's `metricName="f1"` is **macro F1** — the unweighted mean of per-class F1 scores. Pyspark's `"weightedFMeasure"` is **weighted F1**. There is no `"microFMeasure"` named option because micro F1 = accuracy in the multi-class case.

If a question on the exam says "the default metricName for MulticlassClassificationEvaluator", the answer is `"f1"` and specifically *macro F1*. If a question says "to compute macro F1 in pyspark.ml", the answer is also `"f1"`. If a question says "to compute weighted F1", the answer is `"weightedFMeasure"`.

This is the trap most people fall into. They assume `"f1"` is weighted F1 because that's what scikit-learn's `average="weighted"` produces. Pyspark's `"f1"` is macro.

### 66.4.4 log loss

`metricName="logLoss"` is a recent addition (Spark 3.0+). It needs the *probability* column, not the prediction column — unlike the other multiclass metrics — and you set it via `probabilityCol`:

```python
evaluator = MulticlassClassificationEvaluator(
    labelCol="label",
    probabilityCol="probability",
    metricName="logLoss",
)
```

Useful when you care about calibrated probabilities, not just hard accuracy. Lower is better.

(For consistency with the rest of the evaluator API, log loss is "is larger better" = False, so CrossValidator will minimise it — but verify with `evaluator.isLargerBetter()` if you're not sure.)

---

## 66.5 RegressionEvaluator

```python
from pyspark.ml.evaluation import RegressionEvaluator

evaluator = RegressionEvaluator(
    predictionCol="prediction",
    labelCol="price",
    metricName="rmse",     # default
)
rmse = evaluator.evaluate(predictions_df)
```

### 66.5.1 The metrics

- **`"rmse"`** (default). Root mean squared error. Has the same units as your label. Lower is better.
- **`"mse"`**. Mean squared error. Same as RMSE squared. Lower is better.
- **`"r2"`**. Coefficient of determination, the fraction of variance explained. $R^2 \in (-\infty, 1]$. Higher is better. $R^2 = 0$ corresponds to predicting the mean. Negative values mean your model is worse than predicting the mean.
- **`"mae"`**. Mean absolute error. Robust to outliers compared to RMSE. Lower is better.
- **`"var"`**. Explained variance. Similar to but not identical to $R^2$ — explained variance can be high even when predictions are systematically biased; $R^2$ penalises bias.

Chapter 45 derived each of these.

### 66.5.2 Direction handling

For RMSE, MSE, MAE — lower is better. For $R^2$ and explained variance — higher is better. Pyspark's evaluator handles direction internally via `evaluator.isLargerBetter()`. CrossValidator respects this when picking the best grid combination; you don't have to manually invert RMSE.

Verify on your evaluator:

```python
print(evaluator.isLargerBetter())   # True for r2/var, False for rmse/mse/mae
```

---

## 66.6 A worked example tying everything together

Let's run a CV using each of the three Evaluator types so you can see the wiring.

### 66.6.1 Binary classification with BinaryClassificationEvaluator

```python
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
from pyspark.ml.evaluation import BinaryClassificationEvaluator

lr = LogisticRegression(featuresCol="features", labelCol="label")
grid = ParamGridBuilder().addGrid(lr.regParam, [0.01, 0.1, 1.0]).build()

evaluator = BinaryClassificationEvaluator(
    rawPredictionCol="rawPrediction",     # what the model outputs
    labelCol="label",
    metricName="areaUnderROC",
)

cv = CrossValidator(estimator=lr, estimatorParamMaps=grid, evaluator=evaluator, numFolds=5)
cv_model = cv.fit(train)
```

Total trainings: $3 \times 5 + 1 = 16$. The Evaluator wants `rawPrediction` (the length-2 Vector). The LR model produces this by default.

### 66.6.2 Multi-class with MulticlassClassificationEvaluator

```python
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
from pyspark.ml.evaluation import MulticlassClassificationEvaluator

rf = RandomForestClassifier(featuresCol="features", labelCol="label", numTrees=50)
grid = (ParamGridBuilder()
        .addGrid(rf.maxDepth, [5, 10, 15])
        .build())

evaluator = MulticlassClassificationEvaluator(
    predictionCol="prediction",      # what RF outputs (argmax class)
    labelCol="label",
    metricName="f1",                 # macro F1 — the pyspark default
)

cv = CrossValidator(estimator=rf, estimatorParamMaps=grid, evaluator=evaluator, numFolds=5)
cv_model = cv.fit(train)
```

Note: same `CrossValidator` API, different evaluator class. The evaluator's input column changed from `rawPrediction` to `prediction`. Total trainings: $3 \times 5 + 1 = 16$. (We're optimising macro F1 here; if the exam asked for "weighted F1", we'd use `"weightedFMeasure"`.)

### 66.6.3 Regression with RegressionEvaluator

```python
from pyspark.ml.regression import GBTRegressor
from pyspark.ml.evaluation import RegressionEvaluator

gbt = GBTRegressor(featuresCol="features", labelCol="price", maxIter=50)
grid = ParamGridBuilder().addGrid(gbt.maxDepth, [3, 5, 7]).build()

evaluator = RegressionEvaluator(
    predictionCol="prediction",
    labelCol="price",
    metricName="rmse",
)

cv = CrossValidator(estimator=gbt, estimatorParamMaps=grid, evaluator=evaluator, numFolds=5)
cv_model = cv.fit(train)
```

The CV will minimise RMSE (because `evaluator.isLargerBetter() == False`). After fitting, the `avgMetrics` are the per-grid RMSEs; the *smallest* one wins; `cv_model.bestModel` is the model with that smallest RMSE refit on the full training set.

---

## 66.7 Custom evaluators

`pyspark.ml`'s built-in evaluators cover the canonical metrics. If you need something the API doesn't ship — Cohen's kappa, a domain-specific cost function, a constrained metric like "F1 subject to precision ≥ 0.95" — you write a custom Evaluator.

The pattern:

```python
from pyspark.ml.evaluation import Evaluator
from pyspark.ml.param.shared import HasLabelCol, HasPredictionCol
from pyspark.ml.param import Param, Params
from pyspark.sql import functions as F

class CostSensitiveEvaluator(Evaluator, HasLabelCol, HasPredictionCol):
    """Evaluator that computes a custom cost: $1 per FP, $10 per FN."""
    
    def __init__(self, labelCol="label", predictionCol="prediction"):
        super().__init__()
        self._setDefault(labelCol=labelCol, predictionCol=predictionCol)
    
    def _evaluate(self, dataset):
        # Compute counts
        label = self.getLabelCol()
        pred  = self.getPredictionCol()
        n_fp = dataset.filter((F.col(label) == 0) & (F.col(pred) == 1)).count()
        n_fn = dataset.filter((F.col(label) == 1) & (F.col(pred) == 0)).count()
        return float(1 * n_fp + 10 * n_fn)
    
    def isLargerBetter(self):
        return False    # lower cost is better
```

Use it just like any built-in evaluator:

```python
my_evaluator = CostSensitiveEvaluator(labelCol="label", predictionCol="prediction")
cv = CrossValidator(estimator=lr, estimatorParamMaps=grid, evaluator=my_evaluator, numFolds=5)
```

Three things to internalise:

1. **Subclass `Evaluator`**, implement `_evaluate(self, dataset) -> float`, optionally override `isLargerBetter`.
2. **Use the shared mixin classes** (`HasLabelCol`, `HasPredictionCol`) so you inherit the standard parameter machinery and your evaluator integrates cleanly with the rest of pyspark.ml.
3. **Pyspark serialization quirks**. If you want your custom evaluator to be saveable as part of a pipeline (Chapter 67), you'll need to implement the read/write methods too. This is a non-trivial chunk of plumbing; for one-off CV runs, skip it.

---

## 66.8 Pitfalls

Three traps that recur:

1. **Wrong evaluator for the task.** Using `BinaryClassificationEvaluator` on a 4-class problem doesn't error — it computes the AUROC of "is class 1 vs everything else" because the underlying score column only has dimensionality 2 for the wrong reason, OR it errors at runtime depending on how the model wrote the column. Either way the result is meaningless. Use the right evaluator for the task type.

2. **Right evaluator, wrong column.** `BinaryClassificationEvaluator(predictionCol="prediction")` is wrong; that's not a valid parameter. The right one is `rawPredictionCol`. Similarly, `MulticlassClassificationEvaluator(rawPredictionCol="rawPrediction")` is wrong; use `predictionCol`. The error messages can be cryptic.

3. **The macro-vs-weighted F1 question.** Pyspark's `metricName="f1"` is macro F1. Pyspark's `"weightedFMeasure"` is weighted F1. Sklearn's `average="weighted"` is weighted F1. People who mostly use sklearn assume `"f1"` is the weighted version and get a different number than expected when classes are imbalanced. Read the docs; trust nothing.

---

## 66.9 A small note on ClusteringEvaluator

For completeness — `pyspark.ml.evaluation.ClusteringEvaluator` computes a *silhouette score* for unsupervised clustering output. The silhouette is bounded in $[-1, 1]$; higher is better; values near 0 mean overlapping clusters. Inputs: `predictionCol` (cluster ID) and `featuresCol` (the original feature vector).

```python
from pyspark.ml.evaluation import ClusteringEvaluator

evaluator = ClusteringEvaluator(predictionCol="prediction", featuresCol="features")
silhouette = evaluator.evaluate(clustered_df)
```

For k-means, this is the metric you'd use to compare clusterings at different values of $k$. Chapter 38 derived the silhouette geometrically.

---

## 66.10 What this chapter taught you, in one sentence

**`pyspark.ml`'s three classification/regression evaluators differ in (a) which input column they consume — `rawPredictionCol` for binary, `predictionCol` for multiclass and regression — (b) which metricName is the default — `areaUnderROC`, `f1` (macro), and `rmse` respectively — and (c) the direction `isLargerBetter` returns, which CrossValidator uses to decide whether to maximise or minimise; the macro-vs-weighted F1 distinction in MulticlassClassificationEvaluator is the most-tested detail.**

---

## 66.11 What this builds on / where this returns

**Builds on:**

- Chapter 42: classification metrics — confusion matrix, precision, recall, F1, F-beta.
- Chapter 43: ROC and AUROC.
- Chapter 44: precision-recall curves.
- Chapter 45: regression metrics.
- Chapter 47: micro/macro/weighted aggregation in multiclass.
- Chapter 65: CrossValidator, which consumes Evaluators.

**Returns:**

- Chapter 67: custom Evaluators with full save/load support.
- Part L: MLflow logging captures the metric name and value automatically when you log a CrossValidator run.

---

## 66.12 Exercises

1. **Match the evaluator.** For each model, which Evaluator class would you use? (a) `LogisticRegression` (binary), (b) `RandomForestClassifier` (5 classes), (c) `LinearRegression`, (d) `KMeans`, (e) `LogisticRegression` family="multinomial" with 3 classes.

2. **The columns.** Which input column does each Evaluator consume?
   (a) BinaryClassificationEvaluator
   (b) MulticlassClassificationEvaluator
   (c) RegressionEvaluator

3. **The defaults.** What is the default `metricName` for each of the three main Evaluators?

4. **Macro vs weighted.** You have a 4-class problem with class supports `[1000, 100, 50, 10]`. The per-class F1 scores are `[0.95, 0.80, 0.60, 0.30]`. Compute the macro F1 and the weighted F1.

5. **The `"f1"` trap.** Your colleague reports `"f1": 0.66` on a heavily imbalanced 5-class dataset and is surprised it's so low. They expected ~0.92. What might explain the discrepancy?

6. **The wrong column.** You write `BinaryClassificationEvaluator(predictionCol="prediction", ...)`. What goes wrong?

7. **The isLargerBetter check.** Without consulting docs, predict the value of `isLargerBetter()` for `RegressionEvaluator(metricName="rmse")` and `RegressionEvaluator(metricName="r2")`.

8. **Picking the right metric.** Your binary classifier is for a fraud detection use case with 0.5% fraud rate. Would you optimise `areaUnderROC` or `areaUnderPR` in CV, and why?

9. **Multi-class with rawPrediction.** Why does the multi-class evaluator not support AUROC? (Hint: think about what AUROC means with >2 classes.)

10. **Per-class metrics.** You want recall *for class 2 only* in a 5-class problem. What metricName and what additional parameter do you set?

11. **A custom evaluator.** Sketch the code for an evaluator that returns recall at a fixed precision threshold of 0.95 — i.e., the maximum recall achievable subject to precision ≥ 0.95. (Outline; don't write it production-ready.)

12. **Direction in CV.** Your CV optimises `RegressionEvaluator(metricName="rmse")`. The `avgMetrics` are `[2.3, 1.9, 2.7, 2.1]`. Which grid index does CrossValidator pick as best?

<details>
<summary>Answers</summary>

1. (a) `BinaryClassificationEvaluator`. (b) `MulticlassClassificationEvaluator`. (c) `RegressionEvaluator`. (d) `ClusteringEvaluator`. (e) `MulticlassClassificationEvaluator` — multinomial logistic is multi-class.

2. (a) `rawPredictionCol`. (b) `predictionCol` (and `probabilityCol` for log loss). (c) `predictionCol`.

3. `areaUnderROC`; `f1` (macro F1); `rmse`.

4. Macro F1: mean(0.95, 0.80, 0.60, 0.30) = 2.65 / 4 = 0.6625. Weighted F1: (1000×0.95 + 100×0.80 + 50×0.60 + 10×0.30) / 1160 = (950 + 80 + 30 + 3) / 1160 = 1063 / 1160 ≈ 0.916. The two diverge sharply when class sizes are uneven.

5. The colleague probably expected weighted F1 (which would be ~0.92 dominated by the majority class). Pyspark's `"f1"` is macro F1, which gives equal weight to each class — so the rare classes' poor F1 drags the mean down. To match the expectation, use `"weightedFMeasure"`.

6. `BinaryClassificationEvaluator` doesn't accept `predictionCol` — it errors with something like "params not in scope". The correct parameter is `rawPredictionCol`.

7. RMSE: False (lower is better). $R^2$: True (higher is better).

8. `areaUnderPR`. With 0.5% positive rate, ROC will look optimistically good (a model can score high AUROC just by ranking the easy negatives well). PR captures behaviour on the minority class, which is what fraud detection cares about.

9. AUROC is defined for binary classification only — it's the area under a 2-D curve of TPR vs FPR, both of which are defined relative to a single "positive" class. With more than 2 classes you can compute "AUROC against this specific class as positive" (one-vs-rest), but there's no single canonical multi-class AUROC. Hence not in MulticlassClassificationEvaluator.

10. `metricName="recallByLabel"` and `metricLabel=2.0`.

11. ```python
    class RecallAtFixedPrecisionEvaluator(Evaluator, ...):
        def __init__(self, ..., precision_threshold=0.95): ...
        def _evaluate(self, dataset):
            # For each candidate threshold tau (sweep over rawPrediction values):
            #   compute precision and recall at tau
            # Find the tau where precision >= 0.95 (the highest such tau)
            # Return recall at that tau
            ...
        def isLargerBetter(self): return True
    ```
    
12. Index 1 (RMSE = 1.9, the smallest). CrossValidator uses `isLargerBetter() == False` here, so it picks argmin.

</details>
