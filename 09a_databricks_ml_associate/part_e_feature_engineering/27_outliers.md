# Chapter 27 — Outlier Detection and Treatment

> **Goal of this chapter:** to give you the discipline of treating outliers as a *modeling decision*, not a cleaning chore. A model trained on data with 1% extreme outliers can behave like a model trained on a corrupted dataset — coefficients shift, splits go wrong, predictions on normal rows degrade. *Detecting* outliers is easy; *deciding what to do about them* is where experienced practitioners earn their salary. This chapter teaches both.

---

## 27.1 What an outlier even is

The word "outlier" is doing a lot of work. It conflates three quite different things:

1. **A measurement error.** Someone typed the wrong number. A sensor failed and reported the maximum value. A unit-conversion bug emitted millimetres where it should have emitted metres. The "outlier" is *not real data* — it's a corruption.

2. **A rare-but-real value.** The billionaire's bank account has $1.2B in it. The data is real; the value is just extreme. Removing it would bias your model toward not understanding billionaires, and on the rare cases when you predict on a billionaire, you'd be wrong.

3. **A genuinely different mechanism.** A subset of your rows comes from a fundamentally different process. For instance, in fraud data, fraudulent transactions are not "outliers" from the legitimate-transaction distribution — they're samples from a *different* distribution. The right model is one that knows about both.

These three look identical in the data: a value far from the median. The decision of what to do about them depends *entirely* on which of the three you're dealing with. The detection methods can't tell them apart — only domain knowledge can.

You will use the methods in this chapter to *identify candidates* for outlier treatment. The decision of what to actually do with each candidate is a human decision, informed by talking to the data owner and understanding the data-generating process.

---

## 27.2 Why outliers hurt models

Before we detect, let's see *why* it matters.

### 27.2.1 Linear regression: the leverage effect

A linear regression minimises squared error: $\sum_i (y_i - \hat{y}_i)^2$. A single point that's far from the fit contributes a *squared* deviation. Multiply by a big distance and you get an outsized penalty. The regression line shifts to reduce the outlier's contribution, sometimes dramatically.

**Worked example.** A small dataset:

```
x:  1   2   3   4   5
y:  2   4   6   8   10
```

The relationship is exactly $y = 2x$. Fit a linear regression: slope = 2, intercept = 0.

Now we add one outlier:

```
x:  1   2   3   4   5   6
y:  2   4   6   8   10  50    ← outlier
```

The point at $(6, 50)$ deviates from the original relationship by $50 - 12 = 38$ units. Squared error = $38^2 = 1444$, dwarfing the contribution of every other point. The fit shifts: the new slope becomes about 6.4 and the intercept becomes about $-9$ — a dramatically wrong fit for the first five points. The single outlier has corrupted the model's predictions on every other row.

This is **leverage**: a single extreme observation pulls the regression line toward it. The more extreme the outlier, the more leverage.

### 27.2.2 Distance-based models: outlier-dominated distances

For KNN, K-means, and any algorithm that uses Euclidean distance, a single outlier in a feature column inflates all the pairwise distances involving that row. The outlier's nearest neighbours are determined by its proximity in the *other* (non-outlier) features, but the magnitude of its contribution to the distance calculation is enormous. K-means may dedicate an entire cluster to the outlier; KNN's neighbour set may exclude rows that should be neighbours.

### 27.2.3 Standardisation amplification

Recall from Chapter 26 that $\sigma$ — the standard deviation — appears in the denominator of standardisation. An outlier *inflates* $\sigma$ (the sum of squared deviations gets a huge contribution). After standardisation, the non-outlier values are compressed into a small range near the mean, while the outlier ends up extremely far away. The model now sees most of the data as nearly identical and one row as extremely different — exactly the wrong perception.

This is one of the strongest arguments for either (a) handling outliers *before* standardising, or (b) using robust scaling (Chapter 26 §26.4).

### 27.2.4 Tree models: more robust, but not invulnerable

Tree-based models are more robust than linear models. A single outlier at $(x=6, y=50)$ produces, at worst, a single isolated leaf with that one point — most of the tree learns from the rest of the data. But this isn't free: gradient-boosted trees (Chapter 36) fit residuals iteratively, and an outlier with a huge residual will dominate the loss for the first several trees. The ensemble spends its early capacity chasing the outlier rather than the true signal.

The takeaway: tree models tolerate outliers better than linear models but are not immune. Handling outliers helps tree models too, just less.

---

## 27.3 Univariate detection: z-score and IQR

The two textbook methods for flagging outliers in a single column.

### 27.3.1 Z-score

Compute the z-score of each value:

$$z_i = \frac{x_i - \mu}{\sigma}$$

Flag any $i$ with $|z_i| > 3$ (or 2, or 4 — pick a threshold). The intuition is the normal distribution: under a true normal, less than 0.27% of values have $|z| > 3$, so anything exceeding that is "suspicious."

**Problems.**

- *Assumes normality.* For heavy-tailed distributions (income, latencies, anything with a long tail), the genuine non-outlier data extends well past $|z| = 3$. Many high-income earners are legitimately $5\sigma$ above the mean. Flagging them as outliers is wrong.
- *Sensitive to the outliers themselves.* The outliers inflate $\sigma$. So the z-score threshold becomes too lenient — the outliers raise $\sigma$ enough that they no longer have a $|z| > 3$. This is a classic problem of "the contaminated statistic can't see the contamination."

The fix for both is to use a robust statistic.

### 27.3.2 The IQR (interquartile range) method

This is what a boxplot does. Compute:

- $Q_1$: the 25th percentile.
- $Q_3$: the 75th percentile.
- IQR = $Q_3 - Q_1$.

Flag values below $Q_1 - 1.5 \cdot \text{IQR}$ or above $Q_3 + 1.5 \cdot \text{IQR}$. Some practitioners use $3 \cdot \text{IQR}$ for a more conservative threshold ("extreme outliers").

**Why this is better than z-score.**

- *Robust.* The quartiles and IQR are not inflated by a few extreme values. An outlier doesn't increase the IQR much (it might shift $Q_3$ slightly but not by orders of magnitude).
- *Distribution-agnostic.* No normality assumption.

**Worked example.** A column with values:
$\{1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 1000\}$

- $Q_1 = 3$ (25th percentile of 11 values).
- $Q_3 = 8$ (75th percentile).
- IQR = 5.
- Lower fence: $3 - 1.5 \times 5 = -4.5$. No values below.
- Upper fence: $8 + 1.5 \times 5 = 15.5$. The 1000 is above. Flag it.

Compare to z-score: mean = 95.9, std ≈ 299. The outlier has $z = (1000 - 95.9)/299 \approx 3.0$ — right at the threshold, easy to miss. The IQR method sees it clearly.

### 27.3.3 The boxplot

The boxplot visualises this:

```
         ┌────┐
   ───── │  ▒ │ ──────                    *   *
         └────┘                              (outliers)

      Q1     Q3      Q3 + 1.5·IQR
          median        ↓
                        upper "whisker"
```

The box covers $Q_1$ to $Q_3$. The line inside is the median. The "whiskers" extend to the most extreme non-outlier values (within $1.5 \cdot \text{IQR}$ of the box). Points beyond are plotted individually as outliers.

A boxplot is the fastest visual check for univariate outliers. Generate one for every numeric column during EDA (Chapter 23).

---

## 27.4 Multivariate detection: Mahalanobis distance

Univariate methods miss outliers that are extreme *in combination* even if each individual feature is in range.

**Example.** Height = 7'2" (very tall, but possible). Weight = 90 lbs (very light, but possible). Individually each is plausible. *Together*, a 7'2" person who weighs 90 lbs is medically impossible. The univariate methods can't see this; we need a multivariate detector.

### 27.4.1 The math (sketched)

For a vector $x \in \mathbb{R}^d$, the **Mahalanobis distance** from the data centre $\mu$ is

$$D_M(x) = \sqrt{(x - \mu)^T \Sigma^{-1} (x - \mu)}$$

where $\Sigma$ is the covariance matrix of the data.

Geometrically: Euclidean distance treats all directions equally. Mahalanobis distance accounts for the *spread and correlation* of the data. If feature 1 and feature 2 are highly correlated, points along that correlation direction are "common" and points perpendicular to it are "rare" — even if their Euclidean distance from the mean is the same.

Imagine a cloud of points oriented along a diagonal (positive correlation between two features). A point far from the centre *along* the diagonal is normal; a point far from the centre *perpendicular* to the diagonal is anomalous. Mahalanobis distance reflects this. Euclidean distance does not.

**Threshold.** Under multivariate normality, $D_M^2$ follows a chi-squared distribution with $d$ degrees of freedom. So you flag observations with $D_M^2$ exceeding the 0.999 quantile of $\chi^2_d$, or similar.

In practice, the multivariate-normal assumption is wrong for most data — but the *direction* of the test (penalise being off-manifold) is still useful, and the threshold becomes a tuning knob.

### 27.4.2 In scikit-learn

```python
from scipy.spatial.distance import mahalanobis
import numpy as np

mu = X_train.mean(axis=0)
cov = np.cov(X_train, rowvar=False)
inv_cov = np.linalg.inv(cov)

distances = [mahalanobis(x, mu, inv_cov) for x in X_train]
```

Or use `sklearn.covariance.EllipticEnvelope`, which wraps this in an estimator interface.

### 27.4.3 Limitations

- Requires inverting $\Sigma$, which is expensive in high dimensions and fails if features are collinear.
- The covariance estimate is itself contaminated by outliers (the "breakdown point" problem). Robust covariance estimators (e.g., the minimum covariance determinant) help.
- Multivariate normality is a strong assumption.

For high-dimensional or non-Gaussian data, prefer the methods in §27.5.

---

## 27.5 Modern detectors: Isolation Forest and LOF

Two methods that handle high-dimensional, non-Gaussian data more gracefully.

### 27.5.1 Isolation Forest

The intuition: outliers are *easy to isolate*. If you randomly pick a feature and randomly pick a split value, an outlier (being far from the rest of the data) gets separated quickly. A normal point requires many splits to be isolated from its neighbours.

Algorithm sketch:

1. Build many random binary trees. Each split picks a random feature and a random threshold.
2. For each point, measure the average path length from root to leaf across all trees.
3. Short average path → easy to isolate → likely outlier. Long average path → buried in the dense region → likely normal.

The output is an anomaly score per point.

**Pros.**

- Works in high dimensions.
- No distributional assumptions.
- Fast (logarithmic per-point cost).
- Handles mixed feature types reasonably (after encoding).

**Cons.**

- Sensitive to the random seeds; ensemble averaging mitigates.
- No clear interpretability — you know a point is an outlier but not *why* (which feature is anomalous).

In scikit-learn:

```python
from sklearn.ensemble import IsolationForest

iso = IsolationForest(contamination=0.01, random_state=0)
labels = iso.fit_predict(X)  # -1 for outliers, 1 for inliers
scores = iso.score_samples(X)  # lower = more anomalous
```

`contamination` is the assumed proportion of outliers. Setting it to 0.01 means "I expect about 1% of my data to be outliers."

### 27.5.2 Local Outlier Factor (LOF)

LOF is *density-based*. A point is an outlier if its local neighbourhood is much less dense than its neighbours' neighbourhoods.

Formally: for each point, compute the average density of its $k$ nearest neighbours, and compare to its own local density. A ratio significantly greater than 1 means the point is in a sparser region than its neighbours — an outlier.

LOF captures outliers that *are* close to some data but are far from the *bulk* of the data — e.g., a point sitting just outside a tight cluster.

In scikit-learn:

```python
from sklearn.neighbors import LocalOutlierFactor

lof = LocalOutlierFactor(n_neighbors=20, contamination=0.01)
labels = lof.fit_predict(X)
```

LOF is more sensitive than Isolation Forest to the choice of $k$ (number of neighbours).

### 27.5.3 Choosing between them

- Large dataset, high dimensions, want speed: Isolation Forest.
- Moderate dataset, want sensitivity to local density variations: LOF.
- Multivariate-normal-ish data: Mahalanobis + EllipticEnvelope.
- Univariate inspection: IQR / boxplot.

Often you use multiple. A row flagged by *all* of IQR, Isolation Forest, and LOF is almost certainly an outlier; a row flagged by only one is more ambiguous.

---

## 27.6 Treatment: what to actually do

You've identified outlier candidates. Now: what?

The decision tree:

```
For each flagged outlier:
  Is it a measurement error / data corruption?
    YES → Fix it if possible, drop the row if not.
  
  Is it rare-but-real?
    YES → Keep it. The model needs to see it.
          Optionally robustify the model (Huber loss, tree models).
  
  Is it from a different mechanism?
    YES → Either model the mechanisms separately, 
          or include a feature that captures the mechanism.
```

The methods below are the *tools* you reach for after deciding which case you're in.

### 27.6.1 Dropping

`df = df[df['income'] < 1e7]`

Removes rows above an income threshold.

**When OK.** When you've verified the rows are measurement errors. When the outlier is so rare that retaining it doesn't change the model and might destabilise it (e.g., a literal one-off).

**When dangerous.** When the outlier is rare-but-real. You've now told the model that there are no billionaires, and predictions on actual billionaires will be wrong. Also: dropping outliers can introduce selection bias if the dropping is correlated with the target (e.g., very high earners both default less *and* are more likely to be "outliers" → dropping them makes your training set systematically biased).

**Never drop based on the target.** Dropping rows because their target value is extreme is a form of label leakage — you've manipulated the training distribution based on $y$, and your model's predictions on rows that look extreme will be miscalibrated.

### 27.6.2 Capping (winsorising)

Replace values above (or below) a threshold with the threshold.

```python
upper = df['income'].quantile(0.99)
df['income_capped'] = df['income'].clip(upper=upper)
```

This *preserves the row* — its other features still contribute — while limiting the influence of the outlier value. The 99th percentile is a common choice; sometimes 95th or 99.5th.

**When OK.** When you believe the outlier values are real but extreme enough to dominate the model's behavior unfairly. Capping caps their influence without erasing them.

**When dangerous.** When the high-end values have important *signal*. If the difference between "earning $200K" and "earning $5M" is what makes the model accurate on a high-income segment, capping at $200K erases that.

A common refinement: cap *and* add an indicator feature for "was capped." The model can then learn that capped rows are different.

### 27.6.3 Transforming

The log transform (Chapter 26 §26.5) often *eliminates* the outlier problem by compressing the right tail. If your `income` distribution has outliers because it's right-skewed across orders of magnitude, $\log(\text{income})$ has no comparable outliers — every order-of-magnitude difference becomes an additive constant.

This is often the cleanest fix for right-skewed positive data: no rows lost, no values capped, the distribution becomes well-behaved.

### 27.6.4 Robust loss functions

Some loss functions are *designed* to be insensitive to outliers. The most common is **Huber loss** (you'll see this formally in Chapter 16):

$$L_\delta(r) = \begin{cases} \frac{1}{2} r^2 & \text{if } |r| \leq \delta \\ \delta(|r| - \frac{1}{2}\delta) & \text{otherwise} \end{cases}$$

where $r = y - \hat{y}$ is the residual. For small residuals, it's squared error (smooth). For large residuals, it switches to linear loss (no extra penalty for being farther off). An outlier's contribution to the loss is bounded — it can't dominate.

Scikit-learn's `HuberRegressor` implements this. Some gradient-boosting libraries support Huber loss as an option.

The tradeoff: Huber loss is more robust to outliers but slightly less efficient on clean data. For noisy real-world data, the tradeoff is often worth it.

### 27.6.5 Using a robust model

The simplest "robust" choice is often: switch from a linear model to a tree-based model. Trees, as discussed in §27.2.4, are far less sensitive to outliers than linear models. If you're worried about outliers and you don't strictly need a linear model, switching algorithms is often the easiest fix.

### 27.6.6 Doing nothing

Sometimes the right answer is to leave them alone. If the model is going to be used in production and outliers will appear in production, the model needs to handle them. Removing them from training only ensures the model has *never seen* an outlier — which means its predictions on production outliers are completely untested.

If outliers are rare-but-real and the model is robust enough to absorb them, do nothing.

---

## 27.7 A worked example: the $50M earner

A toy dataset of incomes:

| i | income     |
|--:|-----------:|
| 1 | $30,000    |
| 2 | $45,000    |
| 3 | $52,000    |
| 4 | $68,000    |
| 5 | $75,000    |
| 6 | $82,000    |
| 7 | $95,000    |
| 8 | $110,000   |
| 9 | $250,000   |
|10 | $50,000,000|

The tenth row's income is two orders of magnitude above the others. Likely a real high-net-worth individual, but possibly a unit error.

**Univariate detection.**

- Mean = $5,083,700. Std = $15,742,000. Z-score of row 10: $(50M - 5.08M)/15.7M = 2.85$. Below the typical $|z| > 3$ threshold. Misses it.
- Median = $78,500. $Q_1 \approx 52,000$, $Q_3 \approx 110,000$, IQR ≈ 58,000. Upper fence: $110,000 + 1.5 \times 58,000 = 197,000$. Row 9 ($250,000$) is flagged; row 10 ($50,000,000$) is dramatically flagged. The IQR method works.

**Linear regression effect.** Suppose we're predicting `loan_default_probability` from income with these 10 rows. Without row 10, the linear regression fits a sensible negative slope (higher income → lower default). With row 10, the fitted slope tilts dramatically toward making default depend on tiny variations in the millions — the model becomes dominated by where row 10 lies, and its predictions on rows 1–9 become poor.

Numerically: regress a binary `default` (say, the first 5 rows defaulted, the rest didn't) on `income`. Without row 10, slope ≈ $-7 \cdot 10^{-6}$, intercept ≈ 0.8. With row 10, slope drops to ≈ $-1 \cdot 10^{-8}$ — essentially zero. The single outlier has flattened the regression.

**Treatments to try.**

- **Drop.** Drops row 10. Sensible *if* we've verified it's bad data; problematic if it's a real billionaire. Slope returns to ≈ $-7 \cdot 10^{-6}$.
- **Cap at 99th percentile.** Replace $50M with the 99th-percentile value (≈ $200K, given so few rows). Now row 10 looks like row 9. Slope ≈ $-6 \cdot 10^{-6}$. Model retains the row's contribution to count and other features without being dominated by the extreme value.
- **Log transform.** Replace `income` with $\log(\text{income})$. Row 10 becomes $\log(50,000,000) \approx 17.7$, vs row 1's $\log(30,000) \approx 10.3$. The range is now 10.3 to 17.7 — a factor of $\sim 1.7$, not $\sim 1700$. The regression in log-space behaves sensibly.
- **Switch to a tree model.** A random forest will simply put row 10 in its own leaf and learn from the other 9. Predictions on rows 1–9 are unaffected by row 10's presence.

The right move depends on whether row 10 is real and whether you want the model to make predictions for high-income earners. In most practical settings, the log transform is the cleanest move because it preserves the row, retains its information, and lets the linear model work.

---

## 27.8 Avoiding the most common outlier-treatment mistakes

Three mistakes I see repeatedly:

1. **Dropping based on the target.** "These rows have very high default rates, they must be outliers, let's drop them." No. Outlier detection should be based on the *features*, not the target. Dropping rows because of their target values is a form of training-set manipulation that biases the model's predictions.

2. **Fitting outlier-detection on the full dataset.** Like all preprocessing, the parameters of outlier detection (means, IQRs, isolation forest models) should be fit on the training set only. If you fit on the full dataset including test, the test set's "outlier status" leaks into the training process — and worse, the model gets tested only on inliers, hiding any failure to handle outliers in production.

3. **Treating outliers in features differently than in serving.** If your training pipeline caps `income` at $200K but your serving pipeline doesn't, you have training-serving skew. The model sees one distribution at training and a different one at inference. Encapsulate outlier treatment as a pipeline stage so it's identical in both paths.

---

## 27.9 Code: a consolidated checklist

```python
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor

# 1. Univariate detection: IQR method
def iqr_outliers(series, k=1.5):
    q1, q3 = series.quantile([0.25, 0.75])
    iqr = q3 - q1
    lower, upper = q1 - k*iqr, q3 + k*iqr
    return (series < lower) | (series > upper)

# 2. Capping (winsorising) at percentiles, fit on train
def winsorize_fit(series, lower_q=0.01, upper_q=0.99):
    return series.quantile(lower_q), series.quantile(upper_q)

def winsorize_transform(series, lower, upper):
    return series.clip(lower=lower, upper=upper)

# 3. Multivariate detection: Isolation Forest
iso = IsolationForest(contamination=0.01, random_state=42)
iso.fit(X_train.select_dtypes(include='number'))
X_train['outlier_score'] = -iso.score_samples(X_train.select_dtypes(include='number'))
# Higher = more anomalous

# 4. Pipeline-style winsorisation (within sklearn)
from sklearn.preprocessing import FunctionTransformer

class Winsoriser:
    def __init__(self, lower_q=0.01, upper_q=0.99):
        self.lower_q = lower_q
        self.upper_q = upper_q
    def fit(self, X, y=None):
        self.lower = np.percentile(X, self.lower_q * 100, axis=0)
        self.upper = np.percentile(X, self.upper_q * 100, axis=0)
        return self
    def transform(self, X):
        return np.clip(X, self.lower, self.upper)
```

In Spark ML, there is no built-in `IsolationForest` (as of writing); you implement detection in pandas before bringing data into Spark, or use a Databricks-native library. Capping is straightforward: `pyspark.sql.functions.least` and `greatest` clip values to thresholds computed via `df.approxQuantile(...)`.

---

## 27.10 What this builds on / where it returns

**Builds on:**

- Chapter 23 (EDA): outliers are first noticed during EDA.
- Chapter 24 (missing data): sentinel values (-1, 9999999) are often outliers and missing-data markers wearing the same hat.
- Chapter 26 (transformations): log and Yeo-Johnson often eliminate outlier pathologies entirely.

**Returns in:**

- Chapter 16 (loss functions): Huber loss as a robust alternative to squared error.
- Chapter 31 (linear regression): leverage and influence diagnostics.
- Chapter 36 (gradient boosting): how GBT loss functions interact with outliers.
- Chapter 38 (K-means): the impact of outliers on cluster centroids.

---

## 27.11 Exercises

1. **Z-score vs. IQR.** A column has these 10 values: $\{5, 6, 7, 8, 9, 10, 11, 12, 13, 200\}$. Compute the mean, std, $Q_1$, $Q_3$, and IQR. Identify the outlier using each method.

2. **The contaminated z-score.** Repeat #1 with the outlier increased to 2000. What is its z-score now? Why didn't the z-score change as much as you might have expected?

3. **Three categories of outlier.** For each scenario, classify as measurement-error, rare-but-real, or different-mechanism:
   (a) A `temperature` reading of -999 in a weather dataset.
   (b) A `transaction_amount` of $10M in a credit card fraud dataset, on a card that normally sees $50 transactions.
   (c) A `bank_account_balance` of $1.5B for a customer who is in fact a hedge fund's prime broker account.
   (d) A `latency_ms` reading of 60,000 on an API that normally responds in 20 ms.

4. **Multivariate vs. univariate.** A row has height = 6'5" (97th percentile) and weight = 110 lbs (3rd percentile). Each individually is plausible. Together, this is medically implausible. Which detector catches it?

5. **The capping decision.** You cap `income` at the 99th percentile. The 1% capped rows include a few legitimate high earners and a few unit-conversion bugs. What problem does this create, and how would you address it?

6. **Dropping based on the target.** Why is dropping rows because they have extreme target values methodologically wrong? Give a specific scenario where this would create biased predictions.

7. **Huber loss intuition.** Why does Huber loss behave like squared error for small residuals and like absolute error for large ones? What's the geometric/optimisation reason?

8. **Tree robustness.** Why is a random forest more robust to outliers than a linear regression?

9. **Isolation Forest contamination parameter.** You set `contamination=0.01` in `IsolationForest` but your data actually has 5% outliers. What happens? What if you set `contamination=0.10` but only 1% are real outliers?

10. **Training-serving outlier handling.** Your training pipeline winsorises `loan_amount` at the 99th percentile (computed on training data). At serving time, you receive a loan with amount 3× the 99th percentile. What should the pipeline do?

11. **The leverage problem.** A linear regression has a single outlier with extreme leverage. The fit completely changes when the outlier is removed. What does this tell you about the *fit's reliability* on the other rows?

12. **Outliers and PCA.** PCA finds directions of maximum variance. What does a single extreme outlier do to PCA's first principal component? Hint: think about what direction in feature space has the highest variance after the outlier is added.

<details>
<summary>Answers</summary>

1. Mean = (5+6+7+8+9+10+11+12+13+200)/10 = 28.1. Variance ≈ $(5-28.1)^2 + (6-28.1)^2 + ... + (200-28.1)^2)/10 \approx 3000$. Std ≈ 55. Z-score of 200: $(200-28.1)/55 \approx 3.13$ — just barely flagged. Q1 ≈ 7.25, Q3 ≈ 12.75, IQR = 5.5. Upper fence: 12.75 + 1.5×5.5 = 21. 200 is dramatically above. The IQR method flags it cleanly; the z-score method just barely does.

2. New mean ≈ 208.1, std ≈ 597. Z-score of 2000: $(2000 - 208.1)/597 \approx 3.0$. Same z-score essentially! The outlier inflated both the mean *and* the std, so its own z-score barely budged. This is the contamination problem of z-scores.

3. (a) Measurement-error (clearly impossible). (b) Could be measurement-error or fraud (different-mechanism — fraudulent transactions come from a different distribution). (c) Rare-but-real. (d) Different-mechanism or rare-but-real (a real spike caused by something, but possibly a different mechanism like a downstream system stall).

4. Multivariate (Mahalanobis, Isolation Forest, LOF). Univariate methods check each column independently and find no extreme values. The implausibility is in the *combination*, which only multivariate detectors see.

5. The unit-conversion bugs are being treated identically to the legitimate high earners. The bugs should ideally be detected and fixed (or the rows dropped) before reaching the capping stage. Addressing: use a multivariate detector (Isolation Forest) to identify the bugs by their off-manifold position in feature space, then handle them separately.

6. The model is trained on a distribution that excludes high-target rows. At inference time, you don't know in advance which rows will have high targets — the target is what you're predicting. Rows that *would have had* high targets are still in your serving data. Your model's predictions on them will be miscalibrated because it never saw similar training rows. Specific scenario: dropping rows where `loan_amount` is very high because their default rates were "abnormally high." The model now systematically under-predicts default for high-amount loans in production.

7. Geometrically: for small residuals, squared error and absolute error agree (both increase smoothly). For large residuals, squared error grows quadratically (penalising outliers a lot), while absolute error grows linearly (penalising them moderately). Huber is squared near zero (so the gradient is well-behaved and the loss is smooth and differentiable) and switches to linear far from zero (so outliers don't dominate). It's a compromise between the smoothness of squared and the robustness of absolute.

8. A random forest splits on threshold conditions. An outlier ends up in its own leaf (or a leaf with very few rows), absorbing only the loss from that handful of rows. The other rows are unaffected by the outlier's existence — its predictions are isolated. A linear regression's coefficients, by contrast, are computed from a global objective; the outlier shifts the global fit and corrupts predictions on every row.

9. With `contamination=0.01` but 5% real outliers: the model flags only the top 1% as outliers, missing many. With `contamination=0.10` but 1% real: the model flags 10% of rows as outliers, mostly normal points that are merely "less central." Setting contamination accurately matters; in practice, sweep over values and inspect what's flagged.

10. Cap the loan amount to the 99th-percentile threshold computed at training. The trained model has never seen anything above that threshold, and its predictions for above-threshold values are extrapolations the model has no basis for. Optionally, also flag the row for review. *Don't* recompute the threshold using serving data; the training-time threshold is part of the model artifact.

11. The fit is unreliable on the other rows too. The presence or absence of the outlier should not, in general, change the slope significantly — if it does, the fit is being driven by the outlier rather than by the underlying relationship. Use influence diagnostics (Cook's distance, leverage scores) to identify high-influence points and either remove them, robustify the loss, or fit a different model.

12. The outlier creates a direction in feature space along which variance is maximised — the direction from the centroid to the outlier itself. PCA's first principal component will point along that direction (or close to it), capturing essentially the outlier vs. everything else rather than the structure of the rest of the data. The "interesting" directions in the data get pushed to PC2, PC3, etc., with much smaller variance. This is why PCA is often used *after* outlier handling.

</details>
