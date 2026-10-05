# Chapter 36 — Gradient Boosted Trees — GBM, XGBoost, LightGBM

> **Goal of this chapter:** to understand the algorithm family that, more than any other, defines what "state of the art on tabular data" means in 2026. Gradient boosting generalizes AdaBoost to arbitrary differentiable losses — and the practical implementations (XGBoost, LightGBM, CatBoost) added engineering tricks that turned it into the dominant tool. XGBoost won so many Kaggle competitions that it became a meme. LightGBM is now common. CatBoost is excellent for categorical-heavy data. All three are descendants of Friedman's 2001 Gradient Boosting Machine. This chapter unpacks the lineage.

---

## 36.1 From AdaBoost to gradient boosting

Chapter 35 showed that AdaBoost is gradient descent on the exponential loss, in function space. The natural question: what if we replace the exponential loss with something else?

That's the entire idea of **gradient boosting**, due to Friedman (2001). The framework:

- Pick any differentiable loss function $L(y, \hat{f}(x))$ — squared error for regression, log-loss for classification, Huber for robust regression, etc.
- Build the ensemble greedily, one tree at a time, with each tree fitting the *negative gradient* of the loss with respect to the current ensemble's predictions.

That's it. AdaBoost is a special case (exponential loss, sign-based classification). Squared-error GBM is another special case. Log-loss GBM is another. All driven by the same machinery.

---

## 36.2 The gradient boosting framework

Let's derive it step by step. We have training data $\{(x_i, y_i)\}$. We want to build a predictor $\hat{f}(x) = \sum_m \nu \cdot h_m(x)$ where each $h_m$ is a weak learner (typically a shallow tree) and $\nu$ is a small **learning rate** or **shrinkage** parameter (we'll come back to this).

**Step 0: initialize.** Set $\hat{f}_0(x) = \arg\min_c \sum_i L(y_i, c)$ — the constant that best fits the data under the chosen loss. For squared error, this is the mean of $y$; for log-loss, it's the log-odds of the positive class.

**Step m (for m = 1, 2, ..., M):**

1. **Compute pseudo-residuals.** For each training example $i$, compute the negative gradient of the loss w.r.t. the current prediction:
$$
r_{im} = -\left.\frac{\partial L(y_i, \hat{f}(x_i))}{\partial \hat{f}(x_i)}\right|_{\hat{f} = \hat{f}_{m-1}}
$$

   These are called **pseudo-residuals** because for squared-error loss they're literally the residuals $y_i - \hat{f}_{m-1}(x_i)$.

2. **Fit a weak learner $h_m(x)$ to the pseudo-residuals.** Use a regression tree to predict the $r_{im}$ from the $x_i$. (Always regression, even when the original problem is classification — because we're predicting gradient values, which are continuous.)

3. **Compute a step size.** Some implementations re-optimize the step size per leaf; others just use a fixed shrinkage.

4. **Update the ensemble.**
$$
\hat{f}_m(x) = \hat{f}_{m-1}(x) + \nu \cdot h_m(x)
$$

**Final predictor:** $\hat{f}(x) = \hat{f}_M(x)$ (for regression) or $\sigma(\hat{f}(x))$ (for binary classification using log-loss).

This is **gradient descent in function space**. At each iteration, we're moving the prediction function in the direction of steepest descent of the loss — and we're using a tree as a piecewise-constant approximation of that descent direction.

---

## 36.3 Two important special cases

### 36.3.1 Squared-error regression

Loss: $L(y, \hat{f}) = (y - \hat{f})^2 / 2$. Gradient: $\partial L / \partial \hat{f} = \hat{f} - y$. Negative gradient: $r = y - \hat{f}$. The pseudo-residuals are the actual residuals.

Algorithm: fit a tree to the residuals, add to the ensemble, repeat.

**Worked example by hand.** 5-row dataset:

| $i$ | $x_i$ | $y_i$ |
|----:|------:|------:|
| 1 | 1 | 2 |
| 2 | 2 | 3 |
| 3 | 3 | 6 |
| 4 | 4 | 8 |
| 5 | 5 | 9 |

Use shallow trees (depth 1, stumps) and learning rate $\nu = 0.5$.

**Initialize:** $\hat{f}_0 = \bar{y} = 28/5 = 5.6$. Predictions for all rows: 5.6.

Residuals: $y - 5.6 = (-3.6, -2.6, 0.4, 2.4, 3.4)$.

**Round 1.** Fit a stump to predict these residuals from $x$. The best stump: "split at $x = 2.5$" gives left = {1, 2} with mean residual $(-3.6 - 2.6)/2 = -3.1$, right = {3, 4, 5} with mean residual $(0.4 + 2.4 + 3.4)/3 = 2.07$.

Variance reduction: parent SS = $\sum (r_i - \bar{r})^2 = (-3.6)^2 + (-2.6)^2 + 0.4^2 + 2.4^2 + 3.4^2 = 12.96 + 6.76 + 0.16 + 5.76 + 11.56 = 37.2$ (and $\bar{r} = 0$). After split: left SS = $(-3.6 + 3.1)^2 + (-2.6 + 3.1)^2 = 0.25 + 0.25 = 0.5$. Right SS = $(0.4 - 2.07)^2 + (2.4 - 2.07)^2 + (3.4 - 2.07)^2 = 2.79 + 0.11 + 1.77 = 4.67$. Total residual SS: $5.17$, reduction $32.0$.

That's a strong split. $h_1(x)$ predicts $-3.1$ if $x \leq 2.5$, else $+2.07$.

Update with $\nu = 0.5$:

- $\hat{f}_1(x_1) = 5.6 + 0.5 \cdot (-3.1) = 5.6 - 1.55 = 4.05$
- $\hat{f}_1(x_2) = 5.6 + 0.5 \cdot (-3.1) = 4.05$
- $\hat{f}_1(x_3) = 5.6 + 0.5 \cdot 2.07 = 6.63$
- $\hat{f}_1(x_4) = 6.63$
- $\hat{f}_1(x_5) = 6.63$

New residuals: $2 - 4.05 = -2.05$; $3 - 4.05 = -1.05$; $6 - 6.63 = -0.63$; $8 - 6.63 = 1.37$; $9 - 6.63 = 2.37$.

**Round 2.** Fit a stump to these new residuals. Best split: "$x \leq 4.5$" gives left = {1,2,3,4} with mean residual $(-2.05 - 1.05 - 0.63 + 1.37)/4 = -0.59$, right = {5} with mean $2.37$. Update with $\nu = 0.5$:

- $\hat{f}_2(x_1) = 4.05 + 0.5 \cdot (-0.59) = 3.76$
- $\hat{f}_2(x_2) = 4.05 + 0.5 \cdot (-0.59) = 3.76$
- $\hat{f}_2(x_3) = 6.63 + 0.5 \cdot (-0.59) = 6.34$
- $\hat{f}_2(x_4) = 6.63 + 0.5 \cdot (-0.59) = 6.34$
- $\hat{f}_2(x_5) = 6.63 + 0.5 \cdot 2.37 = 7.82$

**Round 3.** New residuals: $-1.76, -0.76, -0.34, 1.66, 1.18$. Best split somewhere around $x = 3.5$ — let me just track conceptually. The ensemble is iteratively refining toward the true linear relationship.

The point: each round shrinks the residuals on average. After enough rounds (and with small enough learning rate), the ensemble approaches a good fit. The function space gradient descent is doing its job.

### 36.3.2 Log-loss binary classification

Loss: $L(y, \hat{f}) = \log(1 + \exp(-y \hat{f}))$ where $y \in \{-1, +1\}$ and $\hat{f}$ is the raw log-odds. Equivalently for $y \in \{0, 1\}$: $L = -y \log p - (1-y) \log(1-p)$ where $p = \sigma(\hat{f})$.

Gradient (using the $\{0, 1\}$ form): $\partial L / \partial \hat{f} = p - y$. Negative gradient: $y - p$. So the pseudo-residuals are *label minus predicted probability* — exactly the same gradient as logistic regression (Chapter 32), but at every iteration.

Algorithm: fit a regression tree to $(y - p)$, add to the ensemble (scaled by $\nu$), update probabilities, repeat.

Note that the trees are still *regression* trees — they predict the gradient values, not class labels. The final prediction is a *probability* obtained by applying the sigmoid to the cumulative ensemble.

---

## 36.4 Key hyperparameters

Gradient boosting has many more hyperparameters than random forest, and they interact. The big ones:

### 36.4.1 Number of boosting rounds (n_estimators, num_boost_rounds)

More rounds = more capacity = more risk of overfitting. Unlike random forest, where more trees never hurts, more boosting rounds *can* hurt — the validation loss eventually starts increasing.

The right way to set this: use **early stopping**. Train on the training set, evaluate on a validation set after each round, stop when validation loss hasn't improved for $k$ rounds (typical $k = 50$ to $100$). All modern gradient boosting libraries (XGBoost, LightGBM, sklearn's `HistGradientBoosting*`) support early stopping natively.

Without early stopping, you have to guess. With it, you can set `n_estimators = 10000` and let the algorithm figure out when to stop.

### 36.4.2 Learning rate (shrinkage, eta)

The multiplier $\nu$ in $\hat{f}_m = \hat{f}_{m-1} + \nu \cdot h_m$. Smaller learning rate = more rounds needed for the same fit = better generalization.

The classic ML wisdom: **$\eta = 0.01$ with thousands of rounds beats $\eta = 0.1$ with hundreds**. This is empirically true across many problems and is the most important single hyperparameter to tune correctly.

Why? Each tree fits some noise as well as signal. With a large learning rate, the noise gets a large weight too. With a small learning rate, each tree contributes less, and the ensemble averages over more trees, smoothing out the noise.

The price is compute. $\eta = 0.01$ means ~10x more rounds than $\eta = 0.1$, which is ~10x more training time.

Default starting points: $\eta = 0.1$ for quick experiments, $\eta = 0.05$ or $0.01$ for production runs with budget.

### 36.4.3 Tree depth (max_depth)

Per-tree complexity. Gradient boosting works best with **shallow trees** — depth 3 to 8 is the typical range. This contrasts with random forest, which uses full-depth trees.

Why shallow? Because in boosting, you want each tree to capture a *small* aspect of the residual structure, leaving room for subsequent trees to add their corrections. Deep trees fit too much per round and the ensemble has nothing to build on.

LightGBM uses `num_leaves` instead of `max_depth` because it grows trees leaf-wise (more on this in §36.6). Roughly, `num_leaves = 2^max_depth`, but the leaf-wise growth can produce very asymmetric trees.

### 36.4.4 Subsample / row sampling (subsample)

What fraction of the training set to use for each tree. Setting this < 1.0 (typical: 0.5 to 0.9) adds stochasticity — each tree sees a random subset of rows. This is variance reduction like bagging, applied within the boosting framework. Friedman (2002) showed this generally improves test performance and called it "Stochastic Gradient Boosting."

### 36.4.5 Column sampling (colsample_bytree, colsample_bylevel, colsample_bynode)

Same idea but for features. Useful when you have many correlated features.

### 36.4.6 Regularization (reg_alpha, reg_lambda, gamma)

L1 (`reg_alpha`) and L2 (`reg_lambda`) regularization on the *leaf weights* of each tree. `gamma` is the minimum loss reduction required to make a split — a complexity penalty.

In XGBoost, the regularized objective for a single tree is:

$$
\text{obj} = \sum_i L(y_i, \hat{f}(x_i)) + \gamma \cdot T + \frac{1}{2} \lambda \sum_j w_j^2 + \alpha \sum_j |w_j|
$$

where $T$ is the number of leaves and $w_j$ are the leaf values. This is the "regularized boosting" view that XGBoost explicitly formalized.

### 36.4.7 Minimum samples per leaf (min_child_weight, min_data_in_leaf)

Same role as in single trees — prevent leaves from being too small. For classification with log-loss, `min_child_weight` is the minimum sum of *Hessian* values per leaf (because XGBoost uses the second-order Taylor expansion — see §36.5), which corresponds to "effective number of samples weighted by their gradient sensitivity."

---

## 36.5 XGBoost's specific innovations

XGBoost (Chen and Guestrin, 2016) was the first widely-used implementation to combine several improvements. The key ones:

### 36.5.1 Second-order Taylor expansion

Friedman's original gradient boosting uses only the first derivative (the gradient). XGBoost expands the loss to *second order* around the current prediction:

$$
L(\hat{f}_{m-1} + h) \approx L(\hat{f}_{m-1}) + g_i \cdot h(x_i) + \frac{1}{2} h_i^{(2)} \cdot h(x_i)^2
$$

where $g_i$ is the gradient and $h_i^{(2)}$ is the Hessian (second derivative) at example $i$. The tree $h$ then minimizes this quadratic approximation, with closed-form optimal leaf weights:

$$
w_j^* = -\frac{\sum_{i \in \text{leaf } j} g_i}{\sum_{i \in \text{leaf } j} h_i^{(2)} + \lambda}
$$

This is a more accurate gradient step than first-order alone — analogous to Newton's method vs. gradient descent. Empirically, this improves convergence and accuracy.

### 36.5.2 Sparsity-aware split finding

When a feature has missing values, XGBoost learns at each split whether missing values should go left or right — by computing the loss reduction both ways and picking the better. This is automatic and free; no imputation needed.

### 36.5.3 Cache-aware histogram-based split finding

For large datasets, instead of considering every distinct feature value as a candidate threshold, XGBoost bins each feature into ~256 buckets and considers bucket boundaries. This is $\sim 10\times$ faster than the exact algorithm with minimal accuracy loss. (LightGBM and modern XGBoost both do this; XGBoost's `tree_method='hist'`.)

### 36.5.4 Parallelization within trees

Although boosting is inherently sequential across rounds, within a single tree's split-finding you can parallelize: each feature can be searched independently for the best split. XGBoost uses multi-threading aggressively for this.

---

## 36.6 LightGBM's specific innovations

LightGBM (Microsoft, 2017) targeted speed and memory for very large datasets.

### 36.6.1 Leaf-wise tree growth

XGBoost (and most older boosters) grow trees **level-wise**: split every node at the current depth before moving down. This produces balanced trees.

LightGBM grows **leaf-wise**: at each step, find the leaf in the *entire current tree* whose split would maximally reduce loss, and split *that* one. This produces unbalanced, deeper trees on the side where structure is dense, and shallower on the side where it's not.

The argument: leaf-wise can achieve lower training loss with the same number of leaves. Empirically faster on large data; risks overfitting on small data (the tree can get very deep in one branch).

LightGBM controls overfitting with `num_leaves` (cap on total leaves) and `min_data_in_leaf` (per-leaf example minimum).

### 36.6.2 Histogram-based with gradient-based one-side sampling (GOSS)

LightGBM's sampling trick. Examples with large gradients (the model is wrong about them) are kept; examples with small gradients (the model is right) are sampled. This keeps most of the information about "hard" examples while reducing data size for splits.

### 36.6.3 Exclusive Feature Bundling (EFB)

For sparse data (lots of zeros), LightGBM bundles mutually-exclusive features (features that are rarely nonzero together — like one-hot encoded levels of a single categorical) into a single column for split-finding. Major speedup on sparse high-cardinality categoricals.

### 36.6.4 Native categorical handling

LightGBM supports categorical features directly. You pass an `categorical_feature` list and it uses the Fisher (1958) optimal-binary-split-of-categories algorithm internally. No one-hot encoding needed.

This last point is genuinely big for tabular data with high-cardinality categoricals (zip codes, product SKUs). XGBoost added similar support in v1.5 (2022).

---

## 36.7 CatBoost — briefly

CatBoost (Yandex, 2017) emphasized two things:

**Symmetric (oblivious) decision trees.** Every node at the same depth uses the same feature and threshold. This is a very constrained tree class — but it's extremely fast to train and predict, and CatBoost's other tricks compensate for the constraint.

**Better default categorical encoding.** CatBoost uses **ordered target statistics** — for each categorical level, compute the mean target *using only training examples that came before this one in a random permutation*. This avoids the leakage that plain target encoding has. They go further with combinations of categorical features.

CatBoost is generally the best out-of-the-box on data with many categorical features. LightGBM is the best on very large numerical data. XGBoost is the most mature and has the widest ecosystem. The three are mostly interchangeable for most problems.

---

## 36.8 Why gradient boosting dominates tabular ML

Three reasons.

**Handles mixed feature types automatically.** No scaling needed. Categorical handling (in LightGBM, CatBoost, and recent XGBoost) is native. Missing values handled natively. The feature engineering burden is dramatically lower than for linear models.

**Captures non-linearity and interactions automatically.** Trees naturally partition the feature space and discover interactions. You don't have to construct polynomial features by hand.

**Robust to outliers (depending on loss).** Squared-error GBM is sensitive to outliers; Huber-loss GBM is not. The flexibility of choosing the loss function lets you tune for your problem.

The empirical evidence is overwhelming. The Kaggle "Winning Solutions" announcements from 2015-2020 are dominated by XGBoost. The recent KDD Cup-style benchmarks consistently show LightGBM or XGBoost on top for tabular tasks. Deep learning has not displaced this; on most tabular datasets, well-tuned GBT beats well-tuned neural nets.

---

## 36.9 The overfitting story — and why you need early stopping

Gradient boosting *can* overfit, and will if you let it.

The mechanism: each new tree fits the residuals (or pseudo-residuals) of the current ensemble. With enough rounds, even with shallow trees and small learning rate, the ensemble will start fitting the noise in the residuals.

Diagnostic: train and validation losses diverge after some round. Training loss keeps going down; validation loss bottoms out and then rises.

Fix: **early stopping**. Set a maximum number of rounds (large — 1000 or 10000), and stop when validation loss hasn't improved for $k$ rounds (`early_stopping_rounds = 50` or `100`).

This is the single most important production discipline for gradient boosting. Without it, you're either undertraining (too few rounds, leaving accuracy on the table) or overtraining (too many rounds, hurting test performance).

---

## 36.10 Practical hyperparameter tuning advice

The set of GBT hyperparameters is large enough to be intimidating. A pragmatic approach:

1. **Set learning rate to 0.05 and use early stopping with a large max rounds.** This eliminates one hyperparameter and gives reasonable defaults for `n_estimators`.

2. **Tune `max_depth` (XGBoost) or `num_leaves` (LightGBM).** Start at depth 5 / 31 leaves. Try a few values: 3, 5, 7, 10.

3. **Tune `min_child_weight` / `min_data_in_leaf`.** Start at the default (1 / 20). Larger values regularize.

4. **Tune `subsample` and `colsample_bytree`.** Start at 1.0 / 1.0; try 0.8 / 0.8 and 0.5 / 0.5.

5. **Tune regularization (`reg_alpha`, `reg_lambda`).** Start at 0. Try small values (0.01, 0.1, 1.0) if validation curve shows overfitting.

6. **At the end, lower the learning rate** (to 0.01 or 0.005) and retrain with more rounds for the final model. This usually picks up another 0.5-1 point of accuracy at the cost of training time.

Tools like Optuna or Hyperopt (Part I) automate this. For most problems, ~50-100 trials of Bayesian optimization over the above hyperparameters gets you within 0.5 percentage points of the optimum.

---

## 36.11 Code

### 36.11.1 XGBoost

```python
import xgboost as xgb

# Binary classification with early stopping
dtrain = xgb.DMatrix(X_train, label=y_train)
dval = xgb.DMatrix(X_val, label=y_val)

params = {
    "objective": "binary:logistic",
    "eval_metric": "logloss",
    "learning_rate": 0.05,
    "max_depth": 5,
    "min_child_weight": 5,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "reg_lambda": 1.0,
    "tree_method": "hist",  # histogram-based, fast
}

model = xgb.train(
    params,
    dtrain,
    num_boost_round=10000,
    evals=[(dtrain, "train"), (dval, "val")],
    early_stopping_rounds=50,
    verbose_eval=100,
)
```

The sklearn-compatible API:

```python
from xgboost import XGBClassifier

clf = XGBClassifier(
    n_estimators=10000,
    learning_rate=0.05,
    max_depth=5,
    early_stopping_rounds=50,
    eval_metric="logloss",
)
clf.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
print(f"Best iteration: {clf.best_iteration}")
```

### 36.11.2 LightGBM

```python
import lightgbm as lgb

train_data = lgb.Dataset(X_train, label=y_train)
val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)

params = {
    "objective": "binary",
    "metric": "binary_logloss",
    "learning_rate": 0.05,
    "num_leaves": 31,
    "min_data_in_leaf": 20,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq": 5,
}

model = lgb.train(
    params,
    train_data,
    num_boost_round=10000,
    valid_sets=[train_data, val_data],
    callbacks=[lgb.early_stopping(50), lgb.log_evaluation(100)],
)
```

### 36.11.3 PySpark MLlib

```python
from pyspark.ml.classification import GBTClassifier

gbt = GBTClassifier(
    featuresCol="features", labelCol="label",
    maxIter=100,            # number of boosting rounds
    maxDepth=5,
    stepSize=0.1,           # learning rate
    subsamplingRate=0.8,
    minInstancesPerNode=20,
    lossType="logistic",    # for classification
)
model = gbt.fit(train_df)
```

**Critical exam knowledge:** Spark's `GBTClassifier` supports **only binary classification**. For multi-class, you have to wrap it in a `OneVsRest` classifier:

```python
from pyspark.ml.classification import OneVsRest

ovr = OneVsRest(classifier=gbt)
ovr_model = ovr.fit(multiclass_train_df)
```

This trains $K$ binary GBT classifiers (one per class vs. the rest). Slow but works.

For regression: `GBTRegressor`, which supports `lossType="squared"` (MSE) or `lossType="absolute"` (MAE).

Spark MLlib's GBT does not have all the tricks of XGBoost (no second-order Taylor, no sparsity-aware splits, no categorical native support — you have to `StringIndexer` and `VectorAssembler` everything). If you need state-of-the-art GBT on Spark, the standard pattern is to use `xgboost4j-spark` or `synapseml`'s LightGBM integration, not native Spark GBT.

---

## 36.12 What this builds on / where this returns

**Builds on:**
- Chapter 17 — gradient descent (the function-space view).
- Chapter 33 — decision trees as the base learner.
- Chapter 34-35 — bagging and AdaBoost as the predecessors.

**Returns:**
- Chapter 65 — `pyspark.ml.classification.GBTClassifier` and its binary-only constraint.
- Part I — hyperparameter optimization, where GBT is the canonical example of "many hyperparameters that interact."

---

## 36.13 Exercises

1. **The pseudo-residual derivation.** For squared-error loss $L = (y - \hat{f})^2 / 2$, derive the pseudo-residuals.

2. **Pseudo-residuals for log-loss.** For binary cross-entropy with $y \in \{0, 1\}$ and $\hat{f}$ = log-odds (so $p = \sigma(\hat{f})$), derive the pseudo-residuals.

3. **One round of squared-error GBT.** Use the 5-row dataset from §36.3.1 and verify the residuals after round 1.

4. **Learning rate intuition.** Why does $\eta = 0.01$ with 5000 rounds usually beat $\eta = 0.1$ with 500 rounds, despite producing similar total "model capacity"?

5. **Tree depth in GBT vs. RF.** Random forests typically use full-depth trees; gradient boosting uses depth-3 to depth-8 trees. Explain why each makes sense given how the trees are combined.

6. **Early stopping necessity.** Suppose you run GBT for 10000 rounds without early stopping. Training loss is monotonically decreasing. Validation loss bottomed out at round 1500 and is now at round 10000. What's the best model? What if you'd used early stopping?

7. **XGBoost's second-order trick.** Why does using the Hessian (second derivative) of the loss give a better gradient step than using only the gradient? (Hint: think Newton's method.)

8. **LightGBM leaf-wise vs. level-wise.** Suppose you have a dataset where most signal is in one corner of feature space. Which growth strategy will use its depth budget more efficiently? Why?

9. **Native categorical encoding.** Why does LightGBM's native categorical encoding usually beat one-hot encoding for a feature with 1,000 levels?

10. **The Spark GBT trap.** You have a 5-class classification problem on Spark. You want to use GBT. What's the gotcha and how do you handle it?

11. **Overfitting diagnostic.** Your XGBoost model has training log-loss 0.05 and validation log-loss 0.42. What's likely happening? Name three hyperparameter adjustments to try.

12. **Bagging on top of boosting.** Some implementations support `subsample < 1.0` (row sampling) and `colsample_bytree < 1.0` (column sampling). Why might using both help even when you already have early stopping?

<details>
<summary>Answers</summary>

1. $\partial L / \partial \hat{f} = \hat{f} - y$. Negative gradient: $r = y - \hat{f}$. The pseudo-residual IS the actual residual.

2. Loss: $L = -y \log p - (1-y)\log(1-p)$ with $p = \sigma(\hat{f})$. Use $\partial p / \partial \hat{f} = p(1-p)$. Chain rule: $\partial L / \partial \hat{f} = (-y/p + (1-y)/(1-p)) \cdot p(1-p) = -y(1-p) + (1-y)p = p - y$. Negative gradient: $y - p$.

3. See §36.3.1 worked example. Initial $\hat{f}_0 = 5.6$. Residuals after init: $(-3.6, -2.6, 0.4, 2.4, 3.4)$. After round 1 with $\nu = 0.5$ and stump predicting $-3.1$ left, $+2.07$ right: predictions $(4.05, 4.05, 6.63, 6.63, 6.63)$. New residuals $(-2.05, -1.05, -0.63, 1.37, 2.37)$ — magnitude reduced from average $|r| = 2.6$ to $|r| = 1.49$.

4. With small $\eta$, each tree contributes little, so noise in any one tree is averaged with many subsequent corrections. With large $\eta$, the first few trees pick up significant noise that subsequent trees can't fully undo (because they have limited room to correct). Same total "capacity," but the small-$\eta$ ensemble is smoother and generalizes better.

5. RF: trees are averaged with equal weight, so each tree should have low bias (full depth) — variance is what averaging fixes. GBT: trees are added sequentially, so each tree should add a small correction (shallow depth) leaving room for subsequent trees. Deep trees in GBT each overfit and dominate the ensemble; shallow trees in RF are too biased.

6. Without early stopping: the model at round 10000 is overfit (validation worse than round 1500). With early stopping at rounds=50 patience: the model halts shortly after round 1500 with the best validation loss. Always use early stopping.

7. Newton's method finds the minimum of a quadratic approximation in one step; gradient descent makes a linear step. The second-order approximation captures curvature: where the loss is highly curved, the step is small; where it's flat, the step is large. Faster convergence and more accurate steps. For boosting, this means each tree more accurately approximates the optimal direction.

8. Leaf-wise will keep splitting the dense corner, building deep structure there, while not wasting effort on the sparse / featureless regions. Level-wise has to keep all branches at the same depth even where there's nothing to learn. Leaf-wise is more efficient on this data. (But more prone to overfitting if not capped.)

9. With one-hot, the 1000 binary columns each have very weak signal per column. The tree wastes splits on these. Native categorical: the tree can split "is the category in {Spain, France, Germany} vs. {everything else}" in one step, using the optimal binary partition. Much higher information gain per split.

10. Spark's `GBTClassifier` is binary-only. Wrap it in `OneVsRest` to handle 5 classes, training 5 binary GBTs. Or use a non-Spark GBT (`xgboost4j-spark`).

11. Severe overfitting. Try: (a) increase `min_child_weight` / `min_data_in_leaf` (require more samples per leaf); (b) decrease `max_depth` (shallower trees); (c) increase regularization (`reg_lambda`, `gamma`); (d) decrease `subsample` and `colsample_bytree` (more stochasticity); (e) increase the early-stopping patience to catch the overfitting earlier.

12. Even with early stopping, the trees themselves can be slightly overfit. Row and column sampling are bagging-style variance reduction *within* boosting — they make each tree see a slightly different problem, decorrelating the trees and improving generalization on top of early stopping. Stochastic gradient boosting (Friedman 2002) showed this empirically.

</details>
