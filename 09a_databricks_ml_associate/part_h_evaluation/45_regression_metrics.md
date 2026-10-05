# Chapter 45 — Regression Metrics

> **Goal of this chapter:** to do for regression what Chapters 42–44 did for classification — make every regression metric precise, geometric, and connected to its assumptions. Classification's central question is *which class did you predict?* Regression's is *how far off was your number?* The metrics differ along axes you have not yet had to think about: are large errors more painful than small ones (and how much more)? are errors interpretable in the target's units? are we comparing against a trivial baseline or against "perfect"? are outliers dominating the score?
>
> Picking the wrong regression metric is less obviously catastrophic than picking the wrong classification metric — there is no equivalent of "always predict the majority class" for regression. But it still makes a difference. A model optimized for MSE will systematically over-attend to outliers; a model optimized for MAE will not. A team reporting MAPE on revenue prediction will see a great number even when the model is dreadful at small accounts. Knowing which metric is honest for which problem is the working competence this chapter is after.

---

## 45.1 The setup

We have a regression problem. Each example has features $x_i \in \mathbb{R}^d$ and a continuous target $y_i \in \mathbb{R}$. The model produces predictions $\hat{y}_i = \hat{f}(x_i)$. For evaluation we have $n$ examples (typically the validation or test set), each with a true $y_i$ and a predicted $\hat{y}_i$. The **residual** is $e_i = y_i - \hat{y}_i$ — the signed error.

Every regression metric in this chapter is some function of the residuals. The functions differ in:

- Whether they square the residuals (MSE, RMSE, R²) — punishing big errors more than proportionally.
- Whether they take the absolute value (MAE) — treating all errors equally per unit of magnitude.
- Whether they normalize by the target's magnitude (MAPE) — making errors scale-invariant.
- Whether they compare against a baseline (R²) or report errors as absolutes (MSE, RMSE, MAE, MAPE).

Each choice encodes a different *error philosophy*. Pick deliberately.

For the worked examples in this chapter, we'll use a 4-row table:

| i | $y_i$ (true) | $\hat{y}_i$ (pred) | $e_i = y_i - \hat{y}_i$ |
|--:|---:|---:|---:|
| 1 | 100 | 90  | +10 |
| 2 | 150 | 160 | −10 |
| 3 | 200 | 220 | −20 |
| 4 | 250 | 245 | +5 |

Tiny on purpose — you can carry it in your head while we run every metric.

---

## 45.2 Mean Squared Error (MSE) — the default in textbooks, for a reason

The most-textbook regression metric is **mean squared error**:

$$
\text{MSE} = \frac{1}{n} \sum_{i=1}^n (y_i - \hat{y}_i)^2 = \frac{1}{n} \sum_{i=1}^n e_i^2
$$

For our 4-row example:

$$
\text{MSE} = \frac{10^2 + (-10)^2 + (-20)^2 + 5^2}{4} = \frac{100 + 100 + 400 + 25}{4} = \frac{625}{4} = 156.25
$$

### 45.2.1 Why MSE is the default

Three reasons MSE keeps appearing as the canonical regression loss:

1. **It is the maximum-likelihood loss under Gaussian noise.** We derived this all the way back in Chapter 16 (and again in Chapter 31 for OLS). If you model the target as $y = f(x) + \varepsilon$ with $\varepsilon \sim \mathcal{N}(0, \sigma^2)$, then the negative log-likelihood reduces to (a constant times) the sum of squared residuals. MLE-flavored derivations naturally produce MSE.

2. **It is differentiable everywhere and convex.** Easy to optimize — gradient descent has no trouble. The closed-form solution for OLS exists because the loss is quadratic in the parameters.

3. **It penalizes large errors disproportionately.** A residual of 20 contributes 400 to MSE; two residuals of 10 contribute 100 each, total 200. A single outlier of magnitude 20 "weighs as much" as four residuals of magnitude 10. This is a feature when large errors really are disproportionately bad (a $50k prediction error on a $500k house is much worse than ten $5k errors on the same houses), and a bug when outliers are noise rather than signal.

### 45.2.2 The unit problem

MSE has the wrong units. If $y$ is dollars, then $y^2$ is dollars squared — a quantity nobody can interpret. "Our model has MSE of $156$ dollar-squared" is true but uninformative.

This is why MSE is rarely the *reported* metric, even when it's the *optimized* loss. The reported metric is usually RMSE.

---

## 45.3 Root Mean Squared Error (RMSE) — MSE in honest units

**RMSE** is just the square root of MSE:

$$
\text{RMSE} = \sqrt{\text{MSE}} = \sqrt{\frac{1}{n} \sum_{i=1}^n (y_i - \hat{y}_i)^2}
$$

For our 4-row example:

$$
\text{RMSE} = \sqrt{156.25} \approx 12.5
$$

The unit is now dollars (same as $y$). You can say: "the model's RMSE is about $12.5$, which means on a typical example we're off by roughly $12.5$." That's interpretable. A house-price model with RMSE = $25,000 misses by about $25k per house on average.

Why "roughly"? Because RMSE is not the mean of absolute residuals — it's the square root of the mean of squared residuals. Mathematically that's a different number, and it weights large errors more. For our example, the mean absolute residual is $(10 + 10 + 20 + 5)/4 = 11.25$, while RMSE is $12.5$ — slightly higher because the squaring penalty inflated the average via the residual of 20.

The general fact: **RMSE ≥ MAE**, with equality only when all residuals are equal in magnitude. The gap between RMSE and MAE is a quick diagnostic for "how outlier-dominated is my error distribution?" — large gap means a few big residuals are inflating the score.

---

## 45.4 Mean Absolute Error (MAE) — the outlier-robust alternative

**MAE** uses absolute values instead of squares:

$$
\text{MAE} = \frac{1}{n} \sum_{i=1}^n |y_i - \hat{y}_i|
$$

For our example:

$$
\text{MAE} = \frac{|10| + |-10| + |-20| + |5|}{4} = \frac{10 + 10 + 20 + 5}{4} = \frac{45}{4} = 11.25
$$

### 45.4.1 Why MAE instead of MSE/RMSE?

The deep reason is *robustness to outliers*. Squaring magnifies large residuals; absolute value does not. A single residual of 100 contributes 10,000 to MSE (and pulls RMSE up by 100/√n if it's added to a previously-good set) but only 100 to the absolute-residual sum (pulling MAE up by 100/n).

Operationally, if your dataset has a handful of legitimately weird examples — a $5M mansion in a dataset of $500K houses, or a hospital length-of-stay of 90 days when the typical is 3 — those examples will dominate MSE and barely move MAE. Whether that's a feature or a bug depends on what you're trying to do:

- If outliers are noise (data entry errors, true black-swan events you don't want the model contorted around) → MAE punishes the model less for them; you may get a more *typical* fit. Prefer MAE.
- If outliers are signal you care about (the $5M mansion is a real customer your model needs to handle; a 90-day hospital stay is exactly the high-risk patient you most need to predict) → MSE makes the model attend to them. Prefer MSE/RMSE.

This decision is *not* secondary. It changes which predictions the optimizer is willing to sacrifice. The squared-error loss says "I'd rather be off by 10 on each of two examples than by 20 on one." The absolute-error loss is indifferent — total error 20 vs. 20.

### 45.4.2 The estimator that MAE implicitly chooses

A small but important fact. If you have a constant model $\hat{y} = c$ that you fit by minimizing MSE on a dataset $\{y_i\}$, the optimal $c$ is the **mean** $\bar{y}$. (We derived this in Chapter 16: $\frac{d}{dc} \sum (y_i - c)^2 = 0 \Rightarrow c = \bar{y}$.)

If you fit the same constant model by minimizing MAE, the optimal $c$ is the **median**, not the mean.

This generalises: optimizing MSE estimates the conditional **mean** of $y$ given $x$ (under model assumptions). Optimizing MAE estimates the conditional **median**. The two coincide for symmetric error distributions but diverge in the presence of skew. For predicting median income vs. mean income in a region — quite different numbers — your loss choice is the choice between which you're estimating.

In Spark ML, the default regression loss is squared error (OLS). For median regression (a.k.a. quantile regression at $\tau = 0.5$), you'd use a quantile loss or a specialized estimator — out of scope for the Associate exam but worth knowing exists.

---

## 45.5 Mean Absolute Percentage Error (MAPE) — the scale-invariant cousin

When the target $y$ spans many orders of magnitude — say, predicting revenue from $100 customers to $10M customers — absolute errors are meaningless. Being off by $1,000 is catastrophic on a $100 customer (1000% error) and trivial on a $10M customer (0.01% error). You want a *percentage* error.

**MAPE** is the mean of absolute percentage errors:

$$
\text{MAPE} = \frac{100\%}{n} \sum_{i=1}^n \left| \frac{y_i - \hat{y}_i}{y_i} \right|
$$

For our 4-row example:

| i | $y_i$ | $\hat{y}_i$ | $|y_i - \hat{y}_i|/|y_i|$ | percent |
|--:|---:|---:|---:|---:|
| 1 | 100 | 90  | 10/100 = 0.100 | 10.0% |
| 2 | 150 | 160 | 10/150 = 0.067 | 6.7% |
| 3 | 200 | 220 | 20/200 = 0.100 | 10.0% |
| 4 | 250 | 245 | 5/250  = 0.020 | 2.0% |

$$
\text{MAPE} = \frac{10.0 + 6.7 + 10.0 + 2.0}{4} = \frac{28.7}{4} \approx 7.2\%
$$

So the model is off by about 7.2% on average.

### 45.5.1 Why MAPE matters — and where it fails

MAPE is scale-invariant. Multiplying every $y$ and every $\hat{y}$ by 10 doesn't change MAPE. So you can report one MAPE number across a dataset with hugely varying target magnitudes, and it's interpretable.

But MAPE has two important failure modes:

1. **When $y$ can be zero or near zero, MAPE explodes.** $1/y$ is undefined at $y = 0$ and huge when $y$ is small. A model that predicts $\hat{y} = 5$ when $y = 0.01$ has a percentage error of 49,900% — and that single example dominates the entire MAPE calculation. For targets that can legitimately be zero (e.g., next-week's sales for new products), MAPE is unusable.

2. **Asymmetric in over- vs. under-prediction.** MAPE penalizes under-predictions more than over-predictions. If $y = 100$ and $\hat{y} = 50$: MAPE error is 50%. If $\hat{y} = 200$: MAPE error is 100%. The "same" absolute error in opposite directions produces different percentage errors when computed against the true $y$. (Some variants — sMAPE, symmetric MAPE — fix this by normalizing against $(|y| + |\hat{y}|)/2$ instead.)

For revenue prediction with positive targets and moderate spread, MAPE is informative. For demand forecasting with frequent zeros, or for residual prediction with sign-changing targets, MAPE is a trap.

### 45.5.2 The log-transform alternative

A common alternative when targets are multiplicative is to transform the target — predict $\log y$ instead of $y$. Then errors in log-space are roughly percentage errors in original space (because $\log y - \log \hat{y} = \log(y/\hat{y})$, and small log-differences correspond to small percentage differences). MSE/MAE on log-transformed targets behaves like a scale-invariant metric without MAPE's divide-by-zero pathology.

You'd then either report MSE in log-space (and explain that to your audience) or back-transform predictions and report MAPE on the back-transformed numbers. We touch on log-transforms in Chapter 26 (numerical transformations). For now: if MAPE is the metric you want but $y$ can be zero, consider $\log(y + 1)$ transformation and report MSE/MAE on the transformed target.

---

## 45.6 R-squared — variance explained, with caveats

So far our metrics have been absolute. R² is *relative* — it compares the model against a baseline.

$$
R^2 = 1 - \frac{SS_{\text{res}}}{SS_{\text{tot}}} = 1 - \frac{\sum_i (y_i - \hat{y}_i)^2}{\sum_i (y_i - \bar{y})^2}
$$

where:

- $SS_{\text{res}} = \sum (y_i - \hat{y}_i)^2$ is the sum of squared residuals — how badly the model fits.
- $SS_{\text{tot}} = \sum (y_i - \bar{y})^2$ is the total sum of squares — the variability of $y$ around its mean.
- $\bar{y}$ is the mean of the observed targets.

For our 4-row example, $\bar{y} = (100 + 150 + 200 + 250) / 4 = 175$.

$SS_{\text{tot}}$:
- $(100 - 175)^2 = 5625$
- $(150 - 175)^2 = 625$
- $(200 - 175)^2 = 625$
- $(250 - 175)^2 = 5625$
- Sum: $12{,}500$

$SS_{\text{res}}$:
- $10^2 + 10^2 + 20^2 + 5^2 = 100 + 100 + 400 + 25 = 625$

$$
R^2 = 1 - \frac{625}{12{,}500} = 1 - 0.05 = 0.95
$$

So R² = 0.95. The model explains 95% of the variance in $y$.

### 45.6.1 Interpretation: "fraction of variance explained"

A model that predicts perfectly has $SS_{\text{res}} = 0$, so $R^2 = 1$. A model that predicts $\bar{y}$ for every input — the no-information baseline — has $SS_{\text{res}} = SS_{\text{tot}}$, so $R^2 = 0$.

R² is most usefully read as: **what fraction of the variance in $y$ is the model capturing, beyond what you'd get by always predicting the mean?**

This is the regression analog of accuracy's "trivial baseline." For classification, the trivial baseline is "always predict the majority class," and accuracy compares against an *implicit* expectation set by that baseline. For regression, the trivial baseline is "always predict the mean," and R² explicitly anchors the model against that baseline.

### 45.6.2 R² can be negative

A common surprise: R² can be negative. This means $SS_{\text{res}} > SS_{\text{tot}}$ — the model fits worse than predicting the mean. A negative R² is the regression equivalent of a classifier scoring below the trivial-baseline accuracy.

Negative R² happens when the model is *bad on the test set*. It does not happen on the training set (assuming you include an intercept term — OLS with intercept always has $R^2 \geq 0$ on the training data, because the OLS solution can always "fall back" to predicting the mean). On the test set, a model that fits the training data well but generalizes poorly can absolutely produce negative test-set R². If you see negative R² on the test set, you have an overfitting (or model-spec) problem — the model is worse than nothing.

### 45.6.3 R² is *not* a comparison to "perfect"

A common misreading: "R² = 0.95 means our model is 95% of the way to perfect." This is wrong. R² = 0.95 means the model captures 95% of the variance *not captured by predicting the mean*. The remaining 5% includes irreducible noise, model misspecification, and missing features — all of which can be substantial. The gap from 0.95 to 1.0 is not "the model needs to be 5% better"; it's "the model is leaving 5% of the variance on the table, which may or may not be reducible."

Conversely, R² near 1 doesn't mean the model is good in absolute terms. It means it's much better than the mean-predictor. If the data is high-variance and easy to predict (perfect linear data with a tiny bit of noise), R² will be very close to 1 even for a simple model. If the data is low-variance and hard to predict, R² will be modest even for a sophisticated model.

R² is a *relative* metric and should be reported alongside absolute metrics (RMSE, MAE) for full context.

### 45.6.4 The outlier inflation problem

Here's a subtle and underappreciated R² pitfall: **outliers inflate $SS_{\text{tot}}$, making R² look better than the model deserves.**

Suppose your dataset has 100 normal examples with target values in $[0, 100]$, plus one outlier with $y = 10{,}000$. The mean $\bar{y}$ is pulled up, and the outlier alone contributes most of $SS_{\text{tot}}$ — the variance "around the mean" is dominated by that one point.

If your model predicts the outlier reasonably well (say, $\hat{y} = 10{,}050$), $SS_{\text{res}}$ stays small relative to $SS_{\text{tot}}$. Even if the model is mediocre on the 100 normal examples, R² will be very high because the outlier inflated the denominator.

The diagnostic: always look at residual plots alongside R². If the residuals are dominated by a few large points, R² is misleading. RMSE and MAE will be similarly affected (for MSE/RMSE) or unaffected (for MAE) — looking at all three together tells a more honest story.

---

## 45.7 Adjusted R² — fairness across model complexity

R² has a property that's sometimes a feature, sometimes a bug: it never decreases when you add more features to a linear regression. Adding any feature — even a useless one — can only improve R² (or leave it unchanged), because the OLS solution can always set the new feature's weight to zero and recover the previous fit.

This means R² is not a fair criterion for *comparing models of different complexity*. A 20-feature model will always have R² ≥ a 5-feature model on the training set, even if the extra 15 features are random noise.

**Adjusted R²** corrects for this by penalizing the number of features:

$$
R^2_{\text{adj}} = 1 - (1 - R^2) \cdot \frac{n - 1}{n - p - 1}
$$

where $n$ is the sample size and $p$ is the number of features (not counting the intercept).

The penalty factor $\frac{n-1}{n-p-1}$ is $\geq 1$ and grows as $p$ grows, so $(1 - R^2)$ is multiplied by a larger number, decreasing adjusted R² unless the new feature's contribution to R² is large enough to overcome the penalty.

For our 4-row example with, say, $p = 2$ features and $n = 4$:

$$
R^2_{\text{adj}} = 1 - (1 - 0.95) \cdot \frac{3}{1} = 1 - 0.15 = 0.85
$$

The adjustment is significant for small $n$ relative to $p$ (look at the $n - p - 1 = 1$ in the denominator — adjustment is large). For $n$ much greater than $p$, the adjustment is small. The metric is mostly useful for comparing nested linear-regression models with moderate sample sizes; for non-linear models (trees, ensembles), adjusted R² is less standard.

In practice: for linear regression with a small number of candidate features, report adjusted R² alongside R² when comparing nested models. For everything else, use cross-validation (Chapter 22) for a more principled fairness check.

---

## 45.8 Choosing the right metric

Synthesizing the chapter so far, here is the working decision rule for which regression metric to use:

| Situation | Recommended metric | Why |
|-----------|---|-----|
| Large errors are disproportionately bad (house prices, demand forecasting where stockout costs scale with unmet demand) | MSE / RMSE | Squaring penalizes outliers heavily |
| All errors are roughly equally bad per unit (engineering tolerances, robust point predictions) | MAE | Equal weight per unit residual |
| Targets span orders of magnitude and percentage-error is the right notion of "off" | MAPE (if $y$ never near zero) or MSE on $\log y$ | Scale-invariant |
| Targets sometimes zero or sign-changing | NOT MAPE; consider MAE, log-transform with offset, or scaled relative error | MAPE blows up |
| Comparing models of different complexity | Adjusted R² (or cross-validated metrics) | R² always favors more features |
| Reporting to non-technical audience | RMSE or MAE (in target units) | Interpretable; "off by about $X$" |
| Anchoring against trivial baseline | R² (with prevalence context) | Explicitly relative |
| When you don't know which to pick | Report MAE and RMSE both | Pair captures both robust-mean and outlier-sensitive perspectives |

The advice of "report multiple" is genuinely the right answer most of the time. A single regression metric can mislead; two or three together usually triangulate to the truth.

---

## 45.9 Worked example — all five metrics on a 6-row table

Let's do one more, slightly larger, to make sure every formula sticks. A model is evaluated on 6 examples:

| i | $y_i$ | $\hat{y}_i$ | $e_i = y - \hat{y}$ | $e^2$ | $|e|$ | $|e/y|$ |
|--:|---:|---:|---:|---:|---:|---:|
| 1 | 10 | 12 | −2  | 4   | 2  | 0.200 |
| 2 | 20 | 18 | +2  | 4   | 2  | 0.100 |
| 3 | 30 | 35 | −5  | 25  | 5  | 0.167 |
| 4 | 40 | 38 | +2  | 4   | 2  | 0.050 |
| 5 | 50 | 55 | −5  | 25  | 5  | 0.100 |
| 6 | 100 | 70 | +30 | 900 | 30 | 0.300 |

Sums: $\sum e^2 = 962$. $\sum |e| = 46$. $\sum |e/y| = 0.917$. Mean of $y$: $\bar{y} = (10+20+30+40+50+100)/6 = 250/6 \approx 41.67$.

**MSE:** $962 / 6 = 160.33$.

**RMSE:** $\sqrt{160.33} \approx 12.66$.

**MAE:** $46/6 \approx 7.67$.

**MAPE:** $0.917 / 6 \approx 0.153 = 15.3\%$.

**R²:** Need $SS_{\text{tot}}$. Squared deviations from $\bar{y} = 41.67$:

- $(10 - 41.67)^2 \approx 1003$
- $(20 - 41.67)^2 \approx 470$
- $(30 - 41.67)^2 \approx 136$
- $(40 - 41.67)^2 \approx 2.8$
- $(50 - 41.67)^2 \approx 69.4$
- $(100 - 41.67)^2 \approx 3402$

Sum $SS_{\text{tot}} \approx 5083$.

$R^2 = 1 - 962/5083 \approx 1 - 0.189 = 0.811$.

Notice the big residual on example 6 ($e = 30$) is doing most of the work in MSE/RMSE — 900 of the 962 squared-residual total. Without it, MSE would be $62/5 = 12.4$, RMSE ≈ 3.5 — a very different picture.

Notice also that MAE is a much milder $7.67$ — the big residual contributes 30 out of 46, not 900 out of 962. The MAE/RMSE gap (~5 vs. ~13) is your hint that "one large residual is inflating the squared-error metric."

Notice MAPE is 15.3% — pulled up by examples 1 (20% off relatively) and 6 (30% off relatively).

Notice R² = 0.81 — but the outlier inflates $SS_{\text{tot}}$ heavily. Without example 6, the model's fit would be nearly perfect on the 5 remaining examples — but R² would also be different (lower in absolute terms because $SS_{\text{tot}}$ shrinks more than $SS_{\text{res}}$). The point is that the single big-error example is doing a lot of work in two of the metrics.

**The reporting:** "RMSE ≈ 12.7 with MAE ≈ 7.7 indicates one or two outliers; R² = 0.81 explains most of the variance; MAPE = 15.3% means we're off by about 15% relatively." A reader given all four can construct an honest picture; a reader given only R² = 0.81 might be misled into thinking the model is uniformly good.

---

## 45.10 Pitfalls and engineering notes

A few practitioner-grade pitfalls beyond the per-metric ones above:

### 45.10.1 Aggregating per-group

A model might have great overall R² but terrible R² on a critical subset. House-price models can have 0.95 R² overall but 0.40 R² on the bottom decile of homes (because that's where the noise concentrates). Always compute per-segment metrics in addition to overall metrics.

### 45.10.2 Train vs. test gap

Compute every metric on both train and test sets. A large gap (train R² = 0.95, test R² = 0.50) is overfitting; a small gap (train 0.85, test 0.80) is healthy. This is the regression analog of the classification train/val gap we used in Chapter 3.

### 45.10.3 Sample-size noise

For small test sets, regression metrics are noisy. A test RMSE of 12 with $n = 50$ could be 10 or 15 just by sample variance. Use cross-validation to reduce noise (Chapter 22).

### 45.10.4 The conditional mean vs. the prediction interval

A regression metric measures point-prediction quality. It says nothing about *uncertainty*. A model that confidently predicts 100 ± 5 and a model that predicts 100 ± 50 might have identical RMSE; their downstream usefulness differs dramatically. Predicting "between 95 and 105" is a different problem from predicting "100" — prediction intervals and quantile regression are out of scope for the Associate exam but worth knowing about.

---

## 45.11 The Spark and sklearn surface

### 45.11.1 sklearn

```python
from sklearn.metrics import (
    mean_squared_error, mean_absolute_error,
    mean_absolute_percentage_error, r2_score
)
import numpy as np

mse = mean_squared_error(y_true, y_pred)
rmse = np.sqrt(mse)   # sklearn ≤ 1.3
# sklearn ≥ 1.4 has mean_squared_error(..., squared=False) for RMSE, but that's deprecated;
# easiest portable form is np.sqrt(mse) or root_mean_squared_error.

mae = mean_absolute_error(y_true, y_pred)
mape = mean_absolute_percentage_error(y_true, y_pred)  # returns fraction, not percent
r2 = r2_score(y_true, y_pred)
```

A few practical notes:

- `mean_squared_error` accepts a `squared` argument; setting `squared=False` returns RMSE. Some sklearn versions deprecate this in favor of a new `root_mean_squared_error` function. Check your version.
- `mean_absolute_percentage_error` was added in sklearn 0.24; before that, you had to compute it by hand. It also has the divide-by-zero behavior — if any $y_i$ is zero, sklearn skips that term and warns; you should not rely on this silently.
- For adjusted R², sklearn does not have a built-in; compute it manually from `r2_score` and the formula in 45.7.

### 45.11.2 pyspark.ml — RegressionEvaluator

Spark's `RegressionEvaluator` is the workhorse:

```python
from pyspark.ml.evaluation import RegressionEvaluator

# Available metric names: "rmse", "mse", "r2", "mae", "var"
# (var = explained variance, slightly different from R²)

evaluator = RegressionEvaluator(
    labelCol="label",
    predictionCol="prediction",
    metricName="rmse"
)
rmse = evaluator.evaluate(predictions_df)

# Reuse the evaluator with different metricName via setMetricName:
evaluator.setMetricName("mae")
mae = evaluator.evaluate(predictions_df)

evaluator.setMetricName("r2")
r2 = evaluator.evaluate(predictions_df)
```

Notes:

- Spark's default metric is `"rmse"`.
- `"var"` (explained variance) is $1 - \text{Var}(y - \hat{y})/\text{Var}(y)$ — closely related to R² but uses variance of residuals rather than sum of squared residuals. The two coincide when the residuals have mean zero (which OLS guarantees on the training set but not necessarily on the test set).
- MAPE is **not** in Spark's RegressionEvaluator. If you want MAPE in Spark, compute it manually:

  ```python
  from pyspark.sql import functions as F
  predictions_df.withColumn("ape", F.abs((F.col("label") - F.col("prediction"))/F.col("label"))) \
      .agg(F.mean("ape").alias("mape")) \
      .show()
  ```

  And be careful about $y = 0$ rows (filter them out or use sMAPE).

We'll see Spark evaluators in detail in Chapter 66.

---

## 45.12 Summary

The bones:

1. **MSE** = mean of squared residuals. The default optimization loss, MLE under Gaussian noise. Penalizes large errors more than proportionally. Units are squared — not directly interpretable.
2. **RMSE** = $\sqrt{\text{MSE}}$. Same penalty structure as MSE; same units as $y$. The default *reported* metric.
3. **MAE** = mean of absolute residuals. Robust to outliers; estimates the conditional median rather than mean. Use when outliers are noise.
4. **MAPE** = mean of $|e/y|$, as a percentage. Scale-invariant. Useful when targets span orders of magnitude. Fails when $y$ can be near zero; asymmetric on over- vs. under-prediction.
5. **R²** = $1 - SS_{\text{res}}/SS_{\text{tot}}$. The "variance explained" relative to predicting the mean. Can be negative on the test set. Inflated by outliers in $SS_{\text{tot}}$.
6. **Adjusted R²** penalizes model complexity; useful when comparing nested linear-regression models.
7. **Choose by error philosophy.** Large errors disproportionately bad → MSE/RMSE. Equal weight per unit → MAE. Multiplicative target → MAPE or log-transform.
8. **Report multiples.** MAE + RMSE + R² in combination tells you both about absolute error, outlier influence, and explained variance.
9. **Spark's RegressionEvaluator** exposes `rmse, mse, r2, mae, var`. MAPE you compute by hand.

If you can compute every metric in this chapter from a residual list by hand, on a whiteboard, and explain which one is honest for a given problem context — you have the chapter.

---

## 45.13 What this builds on / where this returns

**Builds on:** Chapter 16 (loss functions — MSE as MLE under Gaussian noise). Chapter 18 (overfitting — manifests as train-test metric gap). Chapter 22 (cross-validation — for stable metric estimates). Chapter 31 (OLS — the closed-form MSE-minimizer; intercept ensures $R^2 \geq 0$ on train).

**Returns:**

- **Imbalanced classification** doesn't apply to regression directly, but the "report multiple metrics for honest picture" lesson does — *Chapter 46*.
- **Multi-output regression** (predicting multiple targets simultaneously) — briefly in Part F.
- **Spark evaluators in depth** — *Chapter 66*.
- **End-to-end project metrics** (when we evaluate the capstone Lending Club model) — *Chapter 74*.

---

## 45.14 Exercises

Attempt all cold.

1. **By hand, on a tiny dataset.** A model predicts on 5 examples:

   | i | $y_i$ | $\hat{y}_i$ |
   |--:|---:|---:|
   | 1 | 5 | 6 |
   | 2 | 10 | 11 |
   | 3 | 15 | 12 |
   | 4 | 20 | 22 |
   | 5 | 25 | 21 |

   Compute MSE, RMSE, MAE, MAPE, R².

2. **MSE vs. MAE on an outlier.** Two models are evaluated on 4 examples. The residuals are:
   - Model A: 1, 1, 1, 1.
   - Model B: 0, 0, 0, 4.

   Compute MSE, RMSE, MAE for each. Which model has lower MSE? Lower MAE? Discuss which is "better" and how it depends on whether the outlier in B is signal or noise.

3. **R² can be negative.** Construct a tiny test set and a model where $R^2 < 0$. Explain in words what this means.

4. **The conditional-mean property.** Show that for a constant model $\hat{y} = c$ fit on data $\{y_i\}$, the MSE-minimizing $c$ is the mean $\bar{y}$. (Set derivative to zero, solve.) Then argue informally that the MAE-minimizing $c$ is the median.

5. **MAPE asymmetry.** A model predicts $\hat{y} = 50$ when $y = 100$. Then for a different example, $\hat{y} = 200$ when $y = 100$. The absolute errors are both 100. Compute MAPE for each. Discuss the asymmetry.

6. **Log-transform.** A revenue prediction problem has targets ranging from $100 to $1M. You fit two models: one in raw $\$$ scale optimizing MSE, one in $\log_{10} \$$ scale optimizing MSE. What do you expect each model to be good at? Which would be better for predicting small-account revenue accurately?

7. **R² and outliers.** A model has 100 examples with residuals around ±1 (and corresponding $y$ values around 5-10), plus 1 example with $y = 100$ and $\hat{y} = 110$. Compute (or estimate) the R² and discuss whether the outlier inflates the result.

8. **Adjusted R² calculation.** A linear regression with $n = 50$ examples and $p = 3$ features has $R^2 = 0.85$. Compute adjusted R². Now suppose you add 2 more features and R² rises to 0.86. Has the model improved by the adjusted-R² standard?

9. **Spark MAPE.** Write the PySpark code to compute MAPE on a DataFrame with columns `label` and `prediction`. Handle the case where `label == 0`.

10. **Choosing the metric.** For each of the following problems, recommend the primary regression metric and explain in one sentence:
    1. Predicting house prices in the $100K–$10M range.
    2. Predicting the number of bytes downloaded by a website visitor (highly skewed, can be zero).
    3. Predicting the temperature of an industrial reactor in degrees Celsius for safety control.
    4. Predicting customer lifetime value, where the most important customers are the high-value outliers.
    5. Communicating model quality to a non-technical CFO.

11. **The RMSE/MAE gap.** A test set yields RMSE = 50 and MAE = 30. Another test set yields RMSE = 32 and MAE = 30. What does the gap tell you about the residual distribution in each case?

12. **A regression metric trap.** A team reports "Our model's MAPE is 4%." You learn the test set is heavily skewed toward large $y$ values. Why might this MAPE be misleading?

<details>
<summary>Answers</summary>

1. Residuals: -1, -1, 3, -2, 4. Squared: 1, 1, 9, 4, 16. Sum = 31. MSE = 31/5 = 6.2. RMSE = √6.2 ≈ 2.49. Abs: 1, 1, 3, 2, 4. Sum = 11. MAE = 11/5 = 2.2. Percentage errors: 1/5=0.2, 1/10=0.1, 3/15=0.2, 2/20=0.1, 4/25=0.16. Mean = 0.152 = 15.2%. R²: $\bar{y} = 15$. $SS_{\text{tot}} = (5-15)^2 + (10-15)^2 + (15-15)^2 + (20-15)^2 + (25-15)^2 = 100+25+0+25+100 = 250$. $SS_{\text{res}} = 31$. $R^2 = 1 - 31/250 = 0.876$.

2. Model A: MSE = 4/4 = 1, RMSE = 1, MAE = 1. Model B: MSE = 16/4 = 4, RMSE = 2, MAE = 1. Both have the same MAE (total absolute error 4). But Model B has much worse MSE/RMSE because the single big error dominates. Which is "better"? If the outlier in B is real (you genuinely need to handle that example), Model A is better — it has small consistent errors. If the outlier in B is noise (corrupted label, atypical event), Model B is better on the "real" 3 examples — it nailed them. MSE prefers A (penalizes B's big error heavily); MAE is indifferent.

3. Construct: training set perfectly linear, test set with completely different distribution. E.g., train on $y = 2x$ for $x \in [0, 10]$, predict on test set where $y$ ranges 100-200 but model predicts 0-20. $SS_{\text{res}}$ is huge; $SS_{\text{tot}}$ on test (variance around test mean) is modest; $R^2 < 0$. It means: the model is worse on this test set than just predicting the test set's mean $\bar{y}_{\text{test}}$ would be. A negative R² is a flag for severe distribution shift, model bug, or overfitting.

4. $\frac{d}{dc} \sum (y_i - c)^2 = -2 \sum (y_i - c) = 0 \Rightarrow \sum y_i = nc \Rightarrow c = \bar{y}$. For MAE, $\frac{d}{dc} \sum |y_i - c| = \sum (-\text{sign}(y_i - c))$. This is zero when half the $y_i$ are above $c$ and half below — i.e., $c$ is the median. (Technically the derivative isn't defined at $c = y_i$, but the median minimizes the subgradient.)

5. First: |50 - 100|/100 = 50%. Second: |200 - 100|/100 = 100%. The same absolute error of 100 in opposite directions produces 50% vs. 100% MAPE. This is because MAPE divides by the *true* $y$, and over-predictions can be arbitrarily large in absolute terms without bound, while under-predictions are bounded by $y$ itself. sMAPE (symmetric MAPE) divides by $(|y| + |\hat{y}|)/2$ to fix this.

6. Raw-MSE model is good at predicting the *high* end (since residuals contribute as $|e|^2$ in absolute scale, the optimizer focuses on the large-$y$ examples). Log-MSE model treats percentage errors equally, so it's good at multiplicative accuracy — meaning small accounts get equal attention. For predicting small-account revenue accurately, log-MSE is better (it doesn't sacrifice small-account accuracy to nail large-account dollars).

7. $SS_{\text{res}} \approx 100 \cdot 1 + 100 = 200$ (assuming average squared residual ≈ 1 on the 100 small examples plus 10² = 100 on the outlier). $SS_{\text{tot}}$ is dominated by the outlier: 100 examples with $y \approx 7.5$, so $\sum (y - \bar{y})^2$ for them is small; the one example at 100 contributes $(100 - \bar{y})^2 \approx (100 - 8.4)^2 \approx 8400$. $SS_{\text{tot}} \approx 8500$. $R^2 \approx 1 - 200/8500 \approx 0.976$. R² looks excellent — but the model has a 10-unit error on the one outlier and ±1 errors on 100 other examples. The R² is inflated by the outlier's contribution to $SS_{\text{tot}}$. RMSE = √2 ≈ 1.4 for the small examples alone is a more honest signal.

8. Original: $R^2_{\text{adj}} = 1 - (1 - 0.85) \cdot (49)/(46) = 1 - 0.15 \cdot 1.065 = 1 - 0.160 = 0.840$. With more features: $R^2_{\text{adj}} = 1 - (1 - 0.86) \cdot (49)/(44) = 1 - 0.14 \cdot 1.114 = 1 - 0.156 = 0.844$. Adjusted R² rose slightly (0.840 → 0.844). The extra features were worth their cost, but barely.

9. ```python
   from pyspark.sql import functions as F

   predictions_df.filter(F.col("label") != 0) \
       .withColumn("ape", F.abs((F.col("label") - F.col("prediction")) / F.col("label"))) \
       .agg(F.mean("ape").alias("mape")) \
       .show()
   ```
   Filter out zero labels (or use sMAPE: `2 * |y - ŷ| / (|y| + |ŷ|)`).

10. (a) RMSE (interpretable, errors weighted by squared dollars — but worth pairing with MAPE since range is wide). (b) NOT MAPE (zeros); MAE or log-transformed MSE. (c) RMSE (large errors are catastrophic for safety; squared penalty is correct). (d) MSE/RMSE (high-value outliers are signal; squared penalty makes the model attend to them). (e) RMSE in dollars, paired with R² for "variance explained" framing.

11. First test set: RMSE much higher than MAE → distribution has outliers; a few big residuals are inflating squared error. Second test set: RMSE ≈ MAE → residuals are roughly equal in magnitude, no dominating outliers. The ratio RMSE/MAE is a quick outlier-influence diagnostic.

12. If the test set is skewed toward large $y$, the denominators in MAPE are all large, so percentage errors are mechanically small (residuals divided by big numbers). The model could have terrible relative accuracy on the (rare) small-$y$ examples — which might be the operationally important ones — while reporting 4% MAPE because the average is dominated by accurate big-account predictions. Always look at MAPE per-segment, or use a metric that weights examples equally per-example.

</details>
