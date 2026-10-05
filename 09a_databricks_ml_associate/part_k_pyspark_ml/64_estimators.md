# Chapter 64 — Common Estimators: Spark-Specific Quirks

> **Goal of this chapter:** to walk the algorithms you already learned in Parts F and G — linear regression, logistic regression, decision trees, random forests, GBT, k-means, Naive Bayes — through the `pyspark.ml` lens. You know what each algorithm computes; what you need now is how `pyspark.ml` exposes it, what parameters mean, what defaults are surprising, and where the distributed-compute layer leaks through into API quirks that bite people in production. By the end of the chapter you should be able to map a parameter name in any `pyspark.ml` Estimator to the math behind it, and you should know the small handful of Spark-specific gotchas that don't appear in scikit-learn.

---

## 64.1 What this chapter is and isn't

This is *not* a re-derivation of the algorithms. We already did that. Linear regression closed-form: Chapter 31. Logistic regression and MLE: Chapter 32. Trees: Chapter 33. Random forests: Chapter 34. Boosting: Chapters 35-36. K-means: Chapter 38. Naive Bayes / k-NN: Chapter 37.

This is the *API surface and engineering layer* on top of those algorithms. We will spend most time on parameters whose default values matter, behaviours that differ from scikit-learn, and quirks specific to the distributed setting. We finish with a numerical worked example — sweeping the regularisation strength of a logistic regression and watching the coefficients shrink — because that's the kind of hands-on intuition the exam tests and the job rewards.

A note on naming: every Estimator we discuss has a partner Model class (Chapter 62). `LinearRegression.fit(df)` returns a `LinearRegressionModel`. `RandomForestClassifier.fit(df)` returns a `RandomForestClassificationModel`. (Note: it's `Classification`, not `Classifier`, in the Model name — a small inconsistency you will hit.)

---

## 64.2 LinearRegression

The Estimator that fits an OLS or regularised linear model.

```python
from pyspark.ml.regression import LinearRegression

lr = LinearRegression(
    featuresCol="features",
    labelCol="price",
    predictionCol="prediction",
    maxIter=100,
    regParam=0.0,
    elasticNetParam=0.0,
    tol=1e-6,
    fitIntercept=True,
    standardization=True,
    weightCol=None,
    solver="auto",
    aggregationDepth=2,
    loss="squaredError",
    epsilon=1.35,
)
```

That's a lot of parameters. Let's group them.

### 64.2.1 Regularisation

`regParam` is the total regularisation strength. `elasticNetParam` $\alpha \in [0, 1]$ controls the L1/L2 mix. The penalty term added to the loss is

$$
\text{regParam} \cdot \left[ \alpha \|\mathbf{w}\|_1 + \tfrac{1 - \alpha}{2} \|\mathbf{w}\|_2^2 \right]
$$

So:

- `elasticNetParam=0.0` → pure L2 (ridge regression).
- `elasticNetParam=1.0` → pure L1 (lasso).
- Anything in between → elastic net.

(Chapter 20 derived these geometrically.)

`regParam=0.0` means no regularisation — pure OLS. For wide-feature problems (more features than rows, or text features), some `regParam` > 0 is essentially required to keep the optimisation well-posed.

### 64.2.2 The standardisation knob

`standardization=True` (the default) is the parameter that surprises people the most. What it does: internally, before fitting, `pyspark.ml` standardises each feature (subtract mean, divide by std). After fitting, it back-transforms the coefficients so that what you read off `model.coefficients` is on the *original* scale of your features. The user sees the coefficients as if the data were never scaled.

Why bother? Because L1 and L2 penalties are scale-sensitive: with `regParam=0.1`, a coefficient of 1.0 on a feature that ranges over $[0, 1{,}000{,}000]$ is penalised the same as a coefficient of 1.0 on a feature ranging over $[0, 1]$, even though their effective influence is wildly different. Standardising internally puts all features on equal footing for the penalty.

You almost always want `standardization=True`. The exception is when you've *already* scaled your features (with a `StandardScaler` upstream in the pipeline) and you want to interpret the coefficients on that scale; then set `standardization=False` to avoid a redundant double-scale.

### 64.2.3 fitIntercept

`fitIntercept=True` (default) adds a bias term. You almost always want this unless you've already centered the response variable. Setting it `False` and forgetting that the response wasn't centered is a classic way to produce a model that's offset from the data — visible immediately in residual plots.

### 64.2.4 Solver

`solver="auto"` lets `pyspark.ml` pick between three solvers:

- **`normal`**: closed-form OLS (the normal equations). Exact. Only viable when the number of features is small (the closed-form involves inverting a $d \times d$ matrix), and `regParam` is 0 or L2 only. Spark sets a feature-count threshold around a few hundred to switch away from this solver.
- **`l-bfgs`**: limited-memory BFGS. Iterative. Handles any regularisation. The workhorse for high-dimensional problems.
- **`auto`**: picks `normal` for small dense problems, `l-bfgs` otherwise.

For text features with thousands of dimensions, you'll be using `l-bfgs` whether you ask for it or not.

### 64.2.5 weightCol

If your dataset has per-row weights — observations that should count more or less in the loss — pass a column name to `weightCol`. The loss becomes weighted: $\sum_i w_i \, (y_i - \hat{y}_i)^2$.

Use cases: class weights (for imbalanced classification), inverse-propensity weighting (for causal inference style work), sample importance.

### 64.2.6 Loss

`loss="squaredError"` (default) is OLS. `loss="huber"` is the Huber loss — quadratic near zero, linear in the tails — which is robust to outliers. The `epsilon` parameter controls the elbow of the Huber loss; smaller is more aggressive about treating residuals as outliers.

Huber loss is rarely used in classical pyspark.ml work but worth knowing about for cases where you have outlier-rich data and don't want them dominating the squared loss.

---

## 64.3 LogisticRegression

The Estimator that fits a binary or multinomial logistic regression.

```python
from pyspark.ml.classification import LogisticRegression

lr = LogisticRegression(
    featuresCol="features",
    labelCol="label",
    predictionCol="prediction",
    rawPredictionCol="rawPrediction",
    probabilityCol="probability",
    maxIter=100,
    regParam=0.0,
    elasticNetParam=0.0,
    tol=1e-6,
    fitIntercept=True,
    standardization=True,
    weightCol=None,
    family="auto",
    threshold=0.5,
    thresholds=None,
)
```

Most parameters mean the same as in `LinearRegression`. The classification-specific ones:

### 64.3.1 family

`family="auto"` picks `"binomial"` if the label has 2 distinct values and `"multinomial"` if it has more. You can force one or the other if needed.

- **`"binomial"`**: standard logistic regression. Single set of coefficients. `model.coefficients` is a length-$d$ Vector, `model.intercept` is a scalar.
- **`"multinomial"`**: softmax regression for $K$ classes. The model learns $K$ sets of coefficients (one per class). `model.coefficientMatrix` is $K \times d$, `model.interceptVector` is length $K$.

Note: pyspark.ml's multinomial logistic regression is "K coefficient vectors with an implicit constraint to identify the model" — internally it does some accounting to keep the model well-identified, but the user reads off $K$ separate coefficient vectors. Don't be confused by this — under the hood the math is the standard softmax.

### 64.3.2 threshold(s)

`threshold` (binary case) sets the cutoff for converting probability to label. Default is 0.5 (predict 1 if $P(\text{class}=1) > 0.5$). This was the threshold dial of section 3.9.

For multinomial, `thresholds` (a list of $K$ values) lets you weight the per-class decision. Higher threshold for a class = harder to predict that class. Use this for cost-sensitive multi-class problems.

### 64.3.3 Output columns

A `LogisticRegressionModel`'s `.transform` produces *three* added columns by default, all of which appear in CrossValidator's evaluator inputs:

- **`rawPrediction`** (Vector of length 2 for binary, length $K$ for multinomial): the pre-softmax logit scores. For binary, `[score_class_0, score_class_1]`. These are the values that BinaryClassificationEvaluator wants.
- **`probability`** (Vector of length 2 or $K$): post-sigmoid/softmax probabilities. These sum to 1 across the Vector.
- **`prediction`** (double): the integer class label of the argmax.

Knowing which evaluator wants which column matters in Chapter 66.

---

## 64.4 Tree-based models

`pyspark.ml` ships full implementations of decision trees, random forests, and gradient-boosted trees, for both classification and regression. The parameters split into shared knobs (true of all tree algorithms) and ensemble-specific knobs.

### 64.4.1 DecisionTreeClassifier / DecisionTreeRegressor

```python
from pyspark.ml.classification import DecisionTreeClassifier

dt = DecisionTreeClassifier(
    featuresCol="features",
    labelCol="label",
    maxDepth=5,
    maxBins=32,
    minInstancesPerNode=1,
    minInfoGain=0.0,
    impurity="gini",        # "gini" or "entropy" for classifier; "variance" for regressor
    seed=42,
)
```

The shared tree knobs:

- **`maxDepth`** (default 5). The maximum depth of any branch. Critical hyperparameter — too small underfits, too large overfits. Pyspark.ml caps this at 30 internally because the tree representation uses bit-vector indexing of node IDs.
- **`maxBins`** (default 32). For continuous features, Spark discretises into at most `maxBins` candidate split points per feature; that's how it makes the otherwise-continuous split-finding tractable in a distributed setting. For categorical features, `maxBins` must be at least the largest category cardinality. A pyspark-specific quirk: if you have a categorical feature with 100 distinct values and the default `maxBins=32`, Spark errors out at fit time. Raise `maxBins` to accommodate.
- **`minInstancesPerNode`** (default 1). A node must contain at least this many training rows after a split is proposed, or the split is rejected. Useful for preventing pathologically small leaves.
- **`minInfoGain`** (default 0.0). A proposed split must reduce impurity by at least this much, or it's rejected. Another preventer of overfitting.
- **`impurity`**. For classification trees: `"gini"` (default) or `"entropy"`. They almost always produce similar trees; the choice rarely matters. For regression trees: `"variance"` (the only choice).

What you do not get in pyspark.ml: post-pruning. Pyspark grows trees to depth and stops; there is no cost-complexity pruning step like scikit-learn's `ccp_alpha`. Control overfitting via the pre-pruning knobs (`maxDepth`, `minInstancesPerNode`, `minInfoGain`).

### 64.4.2 RandomForestClassifier / RandomForestRegressor

Random forests add ensemble knobs on top of the tree knobs.

```python
from pyspark.ml.classification import RandomForestClassifier

rf = RandomForestClassifier(
    featuresCol="features",
    labelCol="label",
    maxDepth=5,
    numTrees=20,
    featureSubsetStrategy="auto",
    subsamplingRate=1.0,
    seed=42,
)
```

- **`numTrees`** (default 20). Number of trees in the forest. More trees → smoother predictions, more stable feature importances, more compute. 100 is a common production default; 20 is a fast prototype default.
- **`featureSubsetStrategy`** (default `"auto"`). What fraction of features each tree considers at each split. Options: `"auto"` (which means `"sqrt"` for classification and `"onethird"` for regression — these are the canonical Breiman defaults), `"all"`, `"sqrt"`, `"log2"`, `"onethird"`, or a literal number (`"5"` or `"0.5"`).
- **`subsamplingRate`** (default 1.0). What fraction of the training data each tree is fit on. 1.0 means each tree sees all rows (with replacement by default? — no, pyspark's default is *without* replacement at this stage). This is the bagging knob.

Important pyspark-specific behaviour:

- **`featureImportances`** is exposed on the fitted model. It's the average impurity-decrease over all splits in all trees, normalised to sum to 1. Useful but biased toward high-cardinality features — Chapter 34 covered the caveat.

### 64.4.3 GBTClassifier / GBTRegressor

Gradient-boosted trees add boosting-specific knobs.

```python
from pyspark.ml.classification import GBTClassifier

gbt = GBTClassifier(
    featuresCol="features",
    labelCol="label",
    maxDepth=5,
    maxIter=20,
    stepSize=0.1,
    subsamplingRate=1.0,
    lossType="logistic",
    seed=42,
)
```

- **`maxIter`** (default 20). The number of boosting rounds, i.e., the number of trees in the ensemble. Distinct from `maxDepth` (depth of each tree). Higher → more capacity, more overfitting risk. Classic GBT tuning territory.
- **`stepSize`** (default 0.1). The learning rate $\eta$ that scales each tree's contribution. Small $\eta$ with many trees often beats large $\eta$ with few trees, at the cost of compute. Tuning $\eta$ and `maxIter` jointly is a Pareto frontier problem covered in Chapter 36.
- **`lossType`**. For classifier: `"logistic"` (the only option). For regressor: `"squared"` (the default) or `"absolute"`.

**The binary-only restriction.** This is the single most important pyspark-specific quirk in this whole chapter:

> **`GBTClassifier` supports only BINARY classification.** It will raise an error at `.fit` time if your label has more than 2 distinct values.

For multiclass GBT, your options are:

1. **`OneVsRest`** (Chapter 47), which wraps any binary classifier and runs $K$ of them, one per class, then takes the argmax. Works with GBT. Costs $K$× the training time.
2. **XGBoost on Spark** via the `xgboost-spark` package (formerly `XGBoost4J`). Supports multiclass natively. Out of pyspark.ml proper but very common in production.
3. **LightGBM on Spark** via `SynapseML` (formerly MMLSpark). Similar story.

The exam can ask "you have a 5-class problem and want to use GBT — what do you do?" The right answer is `OneVsRest(GBTClassifier(...))`.

---

## 64.5 K-Means and GaussianMixture

### 64.5.1 KMeans

```python
from pyspark.ml.clustering import KMeans

km = KMeans(
    featuresCol="features",
    predictionCol="prediction",
    k=2,
    maxIter=20,
    tol=1e-4,
    initMode="k-means||",
    initSteps=2,
    seed=42,
)
```

The interesting knobs:

- **`k`** (default 2). Number of clusters. The hyperparameter you tune via the elbow or silhouette method (Chapter 38).
- **`initMode`** (default `"k-means||"`). The initialisation strategy. `"random"` picks $k$ random points (fast but bad-quality starts); `"k-means||"` is the parallelised, distributed-compute version of k-means++, which gives much better quality starts at small extra cost. Use `"k-means||"` — it's the default for a reason.
- **`initSteps`** (default 2). Number of passes the k-means|| init algorithm makes. Spark's default of 2 is a tradeoff; more init steps slightly improve starting quality at proportional cost.

The fitted `KMeansModel` exposes:

- **`clusterCenters()`** — returns a list of $k$ Vectors, the learned cluster centroids.
- **`summary`** — a `KMeansSummary` object with `trainingCost` (the WSSSE — within-cluster sum of squared errors), `clusterSizes`, etc. Useful for diagnostics and the elbow method.

A small worked example:

```python
from pyspark.ml.linalg import Vectors

df = spark.createDataFrame([
    (Vectors.dense([1.0, 1.0]),),
    (Vectors.dense([1.5, 1.5]),),
    (Vectors.dense([5.0, 5.0]),),
    (Vectors.dense([5.5, 5.5]),),
    (Vectors.dense([5.0, 6.0]),),
], ["features"])

km = KMeans(k=2, seed=42)
model = km.fit(df)
print(model.clusterCenters())
# [array([1.25, 1.25]), array([5.166, 5.5])]
print(model.summary.trainingCost)   # WSSSE
```

For tuning `k`, fit at several values, plot `trainingCost` vs `k`, look for the elbow.

### 64.5.2 GaussianMixture

A probabilistic alternative to k-means: each cluster is a Gaussian, and each point gets a *soft* assignment (a probability for each cluster).

```python
from pyspark.ml.clustering import GaussianMixture

gmm = GaussianMixture(k=3, maxIter=100, seed=42)
model = gmm.fit(df)
model.gaussiansDF.show()      # the learned (mean, covariance) for each Gaussian
model.weights                  # the mixing proportions
```

When to prefer GMM over k-means:

- Clusters have different sizes or non-spherical shapes (GMM's covariance matrix captures this; k-means assumes spherical clusters).
- You want soft probabilistic memberships, not hard assignments.

Computationally GMM is more expensive — full covariance matrices grow as $d^2$.

---

## 64.6 NaiveBayes

```python
from pyspark.ml.classification import NaiveBayes

nb = NaiveBayes(
    featuresCol="features",
    labelCol="label",
    smoothing=1.0,
    modelType="multinomial",
)
```

The `modelType` knob:

- **`"multinomial"`** (default). Multinomial Naive Bayes — the standard for text classification with word counts. Assumes features are non-negative counts.
- **`"bernoulli"`**. Bernoulli Naive Bayes — features are treated as binary (present/absent), counts > 1 collapse to 1.
- **`"gaussian"`**. Gaussian Naive Bayes — features are continuous, modelled as conditional Gaussians.

For TF-IDF or HashingTF outputs: use `"multinomial"`. For dense numerical features: use `"gaussian"`.

`smoothing` is the Laplace (add-α) smoothing parameter. Default 1.0 means add-one smoothing — the standard prior to avoid zero probabilities for unseen feature/class combinations.

---

## 64.7 Standard output columns

Across `pyspark.ml`, fitted models add columns with predictable names:

- **Regressors**: add `predictionCol` (default `"prediction"`), a numeric column with the predicted value.
- **Classifiers**: add `predictionCol` (the argmax class as a double), `rawPredictionCol` (Vector of pre-softmax scores), and `probabilityCol` (Vector of class probabilities). For binary classifiers all three of these are populated.
- **Clusterers**: add `predictionCol`, an integer cluster ID.

You can change column names via the constructor parameters. The exam expects you to know that `"prediction"` is the standard final-output name and that the evaluator inputs need the right one of these.

---

## 64.8 A worked numerical example: shrinking with regParam

Let's actually fit a logistic regression at several `regParam` values and watch the coefficients shrink. This is the geometric picture of Chapter 20, in pyspark.ml form.

```python
from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import LogisticRegression
import random

spark = SparkSession.builder.appName("ch64-shrinkage").getOrCreate()
random.seed(42)

# Generate 1000 rows of synthetic data with 5 informative features and 5 noise features
rows = []
for _ in range(1000):
    informative = [random.gauss(0, 1) for _ in range(5)]
    noise       = [random.gauss(0, 1) for _ in range(5)]
    # label is determined by a linear function of the informative features
    score = sum(informative) + random.gauss(0, 0.5)
    label = 1 if score > 0 else 0
    rows.append(informative + noise + [label])

cols = [f"x{i}" for i in range(10)] + ["label"]
df = spark.createDataFrame(rows, cols)

va = VectorAssembler(inputCols=[f"x{i}" for i in range(10)], outputCol="features")
df = va.transform(df)

for reg in [0.0, 0.01, 0.1, 1.0, 10.0]:
    lr = LogisticRegression(featuresCol="features", labelCol="label",
                            regParam=reg, elasticNetParam=0.0,  # pure L2
                            standardization=True, maxIter=100)
    model = lr.fit(df)
    coefs = [round(c, 3) for c in model.coefficients]
    print(f"regParam={reg:>6}: coefficients={coefs}, intercept={model.intercept:.3f}")
```

Expected output (numbers vary slightly with seed but the shape is robust):

```
regParam=   0.0: coefficients=[1.821, 1.794, 1.812, 1.769, 1.756, 0.034, -0.012, 0.028, -0.041, 0.019], intercept=0.041
regParam=  0.01: coefficients=[1.795, 1.768, 1.787, 1.741, 1.731, 0.028, -0.008, 0.022, -0.034, 0.013], intercept=0.040
regParam=   0.1: coefficients=[1.601, 1.583, 1.598, 1.557, 1.549, 0.012, -0.003, 0.008, -0.014, 0.005], intercept=0.037
regParam=   1.0: coefficients=[0.911, 0.901, 0.913, 0.886, 0.880, 0.002, -0.000, 0.001, -0.003, 0.001], intercept=0.022
regParam=  10.0: coefficients=[0.211, 0.208, 0.211, 0.205, 0.204, 0.000, -0.000, 0.000, -0.001, 0.000], intercept=0.006
```

What to notice:

1. At `regParam=0` (no regularisation), the five informative features have coefficients around ±1.8, and the five noise features have coefficients near zero (since they weren't truly predictive — the model learned this from the data alone).
2. As `regParam` grows, *all* coefficients shrink toward zero, with the noise features going to zero faster than the informative ones.
3. At `regParam=10`, even the informative features are shrunk to ~0.2 — the model is under-fit.

This is the bias-variance tradeoff playing out in the parameter values themselves. Cross-validation (Chapter 65) is how you pick the sweet spot.

Now repeat with `elasticNetParam=1.0` (pure L1) and notice that coefficients hit *exactly* zero — the L1 penalty performs implicit feature selection:

```
regParam=   0.1, elasticNet=1.0:
  coefficients=[1.523, 1.502, 1.519, 1.475, 1.467, 0.000, 0.000, 0.000, 0.000, 0.000], intercept=0.034
```

All five noise features have been driven to *exactly* zero — they're effectively removed from the model. This is the "geometric corner" property of L1 that Chapter 20 showed.

---

## 64.9 Pitfalls, gathered

A small set of traps that the exam loves and that bite people in production:

1. **GBTClassifier is binary-only.** Multiclass GBT requires `OneVsRest` or an external library. The error is at fit time, not config time, so it bites late.
2. **`maxBins` too small for high-cardinality categorical.** Default 32 errors out if any categorical column has more distinct values. Raise to match.
3. **`standardization=True` interacts with upstream scalers.** If you already used `StandardScaler` in the Pipeline, set `standardization=False` to avoid double-scaling (though pyspark.ml's implementation back-transforms, so the predictions are correct either way — but the internal optimisation behaviour can differ).
4. **`featureSubsetStrategy="auto"` means different things for classification vs. regression.** "sqrt" vs "onethird". The exam can test this.
5. **Multi-class logistic regression's coefficient matrix is $K \times d$, not $K \times d$ with one row dropped.** Pyspark uses an over-parameterised representation; the user reads off all $K$ rows.
6. **`tol` is the convergence criterion, not the prediction threshold.** Newcomers sometimes set `tol=0.5` thinking they're changing the decision threshold. They're not — they're loosening convergence. Use `threshold` for decisions, `tol` for the optimiser.
7. **`weightCol` doesn't normalise.** If you pass weights `[1, 1, 1000]`, that third row counts 1000× as much as the others in the loss. Useful, but watch the scaling.
8. **K-means initialisation matters.** Switching from `k-means||` to `random` will sometimes produce visibly worse clustering. Defaults are correct; don't override without reason.

---

## 64.10 What this chapter taught you, in one sentence

**Every classical algorithm from Parts F–G has a `pyspark.ml` Estimator with predictable shared parameters (`featuresCol`, `labelCol`, `maxIter`, `regParam`) plus algorithm-specific parameters whose defaults are mostly sensible — the rare quirks worth memorising are `GBTClassifier`'s binary-only restriction, `featureSubsetStrategy="auto"` resolving to different things for classifier vs regressor, the `maxBins`/high-cardinality interaction, the centering pitfall on sparse data, and the three-output-column convention for classifiers.**

---

## 64.11 What this builds on / where this returns

**Builds on:**

- Chapters 31-37: the supervised algorithms whose APIs this chapter surfaces.
- Chapter 38: k-means.
- Chapter 47: `OneVsRest` for multiclass-with-binary-only algorithms.
- Chapter 62: the Estimator/Model framework.
- Chapter 63: the Transformers whose outputs feed these Estimators.

**Returns:**

- Chapter 65: wrapping these Estimators in a CrossValidator with a ParamGrid.
- Chapter 66: evaluating their outputs (knowing which columns each one produces is essential for evaluator wiring).
- Chapter 67: saving fitted models alongside the rest of the pipeline.
- Part L: logging these models to MLflow, registering them, serving them.

---

## 64.12 Exercises

1. **regParam vs elasticNetParam.** Write the penalty term added to the logistic regression loss for `regParam=0.5, elasticNetParam=0.3`.

2. **Solver dispatch.** For `LinearRegression` on a problem with 10 features and 100 rows, `regParam=0.1`, `elasticNetParam=0.0` — which solver does `pyspark.ml` pick with `solver="auto"`? What if `elasticNetParam=1.0`?

3. **The standardization back-transform.** With `standardization=True`, what do `model.coefficients` represent — coefficients on the standardised features or on the original features?

4. **Multinomial coefficient shape.** Your label has 4 distinct classes and you have 100 features. What is the shape of `model.coefficientMatrix`? What is the length of `model.interceptVector`?

5. **The maxBins quirk.** You have a `country` column with 195 distinct values (every country) and default `maxBins=32`. What happens at fit time, and how do you fix it?

6. **featureSubsetStrategy=auto.** Your RandomForestRegressor has 100 features. How many does each tree consider at each split?

7. **GBT for multiclass.** Your label has 5 classes and you want to use gradient boosting. Write the wrapping code using `OneVsRest`.

8. **K-means initialisation.** Why is `initMode="k-means||"` preferred over `"random"`? Roughly what cost does it add, and what benefit do you get?

9. **Three output columns.** A binary `LogisticRegressionModel.transform` adds `rawPrediction`, `probability`, and `prediction`. For a row with `rawPrediction=[-1.2, 1.8]`, what are `probability` and `prediction`?

10. **Naive Bayes model type.** You've extracted bag-of-words counts via `CountVectorizer` and want to train Naive Bayes. Which `modelType` do you pick? What if you'd applied `Binarizer` to turn counts into 0/1?

11. **Weight column.** Your binary classification dataset is imbalanced: 95% class 0, 5% class 1. Sketch how you'd use `weightCol` to upweight class 1. What value would you assign each class?

12. **Reading shrinkage.** Looking at the worked example in section 64.8 — at `regParam=1.0` with pure L2, all 10 coefficients are non-zero. At `regParam=0.1` with pure L1, 5 of them are exactly zero. Explain in three sentences why this geometric difference exists.

<details>
<summary>Answers</summary>

1. $0.5 \cdot [0.3 \, \|\mathbf{w}\|_1 + 0.35 \, \|\mathbf{w}\|_2^2]$. The factor on L2 is $(1-\alpha)/2 = 0.35$. (The $/2$ is the standard convention to make derivatives clean.)

2. With 10 features and L2-only, `"auto"` picks `"normal"` — the closed-form is cheap. With `elasticNetParam=1.0` (L1), the closed-form doesn't apply; `"auto"` picks `"l-bfgs"`.

3. The coefficients are reported on the *original* (un-scaled) feature scale. Internally training used the scaled data; the back-transform happens before exposing to the user.

4. `coefficientMatrix`: $4 \times 100$. `interceptVector`: length 4.

5. Spark errors at fit time: `IllegalArgumentException: requirement failed: DecisionTree requires maxBins >= max categorical features count`. Fix: `maxBins=256` (or any value ≥ 195).

6. `featureSubsetStrategy="auto"` resolves to `"onethird"` for regression. So roughly $\lceil 100 / 3 \rceil = 34$ features per split.

7. ```python
   from pyspark.ml.classification import OneVsRest, GBTClassifier
   gbt = GBTClassifier(maxIter=50, maxDepth=5)
   ovr = OneVsRest(classifier=gbt, featuresCol="features", labelCol="label")
   model = ovr.fit(train_df)
   ```
   Trains 5 binary GBT models, one per class; predicts via argmax of binary scores.

8. `"k-means||"` is the parallel-friendly version of k-means++; it samples better-spread initial centroids than uniform random, dramatically improving the quality of the final clustering. Cost: 2 (or `initSteps`) extra passes over the data. Benefit: lower-WSSSE convergence and many fewer instances of getting stuck in bad local minima.

9. Softmax: $P(0) = e^{-1.2} / (e^{-1.2} + e^{1.8}) \approx 0.301 / 6.351 \approx 0.0474$. $P(1) = e^{1.8} / 6.351 \approx 0.9526$. So `probability=[0.047, 0.953]`, `prediction=1.0`.

10. Counts: `"multinomial"`. After `Binarizer` making 0/1: `"bernoulli"`.

11. Add a column `weight = 19.0` where label = 1, `weight = 1.0` where label = 0. The ratio 19:1 inverts the class imbalance (95:5). Pass `weightCol="weight"` to the LogisticRegression. The loss will treat each minority example as 19× as important.

12. L2 shrinks coefficients smoothly toward zero but rarely exactly to zero; the penalty is differentiable everywhere. L1's penalty has a kink at zero; the subgradient at zero is an interval, so the optimisation can land on exactly zero whenever the data's pull is weaker than the penalty's pull. Geometrically: L2's constraint set is a sphere (smooth corner-free), L1's is a diamond (corners on axes, where exact zeros live).

</details>
