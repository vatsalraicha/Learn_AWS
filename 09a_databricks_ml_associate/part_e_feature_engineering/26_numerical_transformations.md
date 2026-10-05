# Chapter 26 — Numerical Transformations

> **Goal of this chapter:** to teach you how to reshape numeric columns so models can actually use them — and to explain *why* some models need this and others don't. Standardisation, min-max scaling, robust scaling, log, Box-Cox, Yeo-Johnson, binning — by the end of this chapter you should know which transform to reach for, what it does geometrically, and what the leakage rules are. The treatment is mostly practical, but we'll derive enough of the math that you understand what each transform is doing rather than memorising a recipe.

---

## 26.1 Why scaling matters: a small disaster

Suppose you're predicting house prices. Your features:

- `square_feet`: ranges from 500 to 6,000.
- `bedrooms`: ranges from 1 to 6.
- `lot_size_acres`: ranges from 0.05 to 5.0.
- `years_since_built`: ranges from 0 to 120.
- `median_neighborhood_income`: ranges from 25,000 to 250,000.

A linear regression — Chapter 31 will derive it formally — fits

$$\hat{y} = w_1 x_1 + w_2 x_2 + w_3 x_3 + w_4 x_4 + w_5 x_5 + b$$

The coefficients $w_j$ have units of (output per unit of $x_j$). For `square_feet`, the coefficient $w_1$ is "additional dollars per additional square foot." For `median_neighborhood_income`, the coefficient $w_5$ is "additional dollars per additional dollar of neighborhood income."

The training procedure (gradient descent — Chapter 17) doesn't know units. It iteratively adjusts $w_j$ to reduce the loss. **Features with larger magnitudes produce larger gradients.** With `median_neighborhood_income` ranging up to 250,000 and `bedrooms` ranging up to 6, a step that moves all the $w_j$ by the same small amount affects the prediction by hundreds of thousands of dollars through $w_5$ and by tens of dollars through $w_2$.

The optimizer struggles. Either it takes huge steps in $w_2$ to make any meaningful difference (and overshoots in $w_5$), or it takes tiny steps in $w_5$ to control $w_5$'s contribution (and never moves $w_2$ at all). The training is slow, unstable, and the final solution depends heavily on the optimizer's settings rather than on what the data should tell us.

There's a worse pathology. Distance-based algorithms — KNN (Chapter 37), K-means (Chapter 38), PCA (Chapter 40) — compute *Euclidean distance* between rows:

$$d(x_i, x_j) = \sqrt{(x_{i,1} - x_{j,1})^2 + (x_{i,2} - x_{j,2})^2 + \cdots}$$

A difference of 100,000 in `income` and a difference of 100 in `square_feet` and a difference of 2 in `bedrooms` all square and add. The `income` difference *completely dominates* the sum — a hundred thousand squared is ten billion; one hundred squared is ten thousand; two squared is four. Almost all the "distance" between two houses is just the difference in neighborhood income. The other features may as well not exist.

The fix is **scaling**: transform each feature so it lives on a comparable scale before feeding it to the model. The rest of this chapter is the catalogue of how to do that, and the related transformations for distributions that are skewed or otherwise awkward.

---

## 26.2 Standardisation (z-score)

The default for most numeric features in most situations: **standardisation**, also called z-score normalisation.

$$x' = \frac{x - \mu}{\sigma}$$

Where $\mu$ is the mean of the feature (over the training set) and $\sigma$ is the standard deviation.

**Result:** the transformed feature has mean 0 and standard deviation 1.

**Worked example.** A column with values $\{8, 10, 12, 14, 16\}$. Mean $\mu = 12$, variance $\sigma^2 = \frac{(8-12)^2 + (10-12)^2 + (12-12)^2 + (14-12)^2 + (16-12)^2}{5} = \frac{16+4+0+4+16}{5} = 8$. So $\sigma = \sqrt{8} \approx 2.83$.

Transformed: $\{(8-12)/2.83, (10-12)/2.83, \ldots\} = \{-1.41, -0.71, 0, 0.71, 1.41\}$.

The new column is centred at 0 (mean) with spread 1 (std). Any other column standardised the same way will also be centred at 0 with spread 1 — they're now comparable.

### 26.2.1 What standardisation preserves and what it loses

Standardisation is a *linear* transformation: it shifts and scales. It preserves:

- The shape of the distribution (skew, kurtosis, multimodality).
- The ranks of the data — the largest value is still the largest, the median is still the median.
- The relative spacings — the difference between any two values, divided by $\sigma$, is unchanged.

It doesn't preserve the magnitudes. A coefficient learned on standardised data is no longer "dollars per additional square foot" but "dollars per additional *standard deviation* of square feet."

This makes coefficients **comparable across features**, which is one of the underappreciated benefits of scaling. After standardisation, a coefficient of 2.0 on `square_feet` and a coefficient of 0.5 on `income` means square_feet has 4x the effect per unit-of-feature-variation as income — a meaningful, interpretable comparison.

### 26.2.2 When to use it

Standardisation is the right default for:

- **Linear and logistic regression** (Chapters 31–32). The optimizer converges faster and more stably.
- **Neural networks** (out of scope here but worth knowing). Activations and gradients propagate cleanly with standardised inputs.
- **Support vector machines** (Chapter 37 lightly). SVMs use distances and dot products.
- **PCA** (Chapter 40). PCA decomposes the covariance matrix; if features are on different scales, the largest-magnitude feature dominates the principal components.
- **Ridge and lasso regression** (Chapter 20). Regularization penalises large coefficients; unscaled features lead to imbalanced penalties.

### 26.2.3 When not to use it

- **Tree models** (Chapters 33–36). Decision trees, random forests, and gradient-boosted trees split on threshold values: "is feature $j$ above $t$ or below?" The choice of $t$ is invariant under any monotonic transformation of $x_j$ — standardising doesn't change anything for trees. So you can skip standardisation when using tree models. It's not wrong to standardise; it's just wasted work.
- **Sparse data**. Standardisation will center the data around zero, destroying sparsity (the zeros become non-zero values). For very high-dimensional sparse data (text, hashed features), use `MaxAbsScaler` instead, which scales by the maximum absolute value and preserves sparsity.

### 26.2.4 The fit-on-train rule

```python
# WRONG
df['feature'] = (df['feature'] - df['feature'].mean()) / df['feature'].std()
X_train, X_test = train_test_split(df, ...)

# RIGHT
X_train, X_test = train_test_split(df, ...)
mu = X_train['feature'].mean()
sigma = X_train['feature'].std()
X_train['feature'] = (X_train['feature'] - mu) / sigma
X_test['feature']  = (X_test['feature']  - mu) / sigma
```

The mean and standard deviation are computed on the training set only and applied to the test set. This is the same discipline as Chapter 24's imputation: any parameter learned from data must be learned only from training data. In sklearn, use a `StandardScaler` inside a pipeline so the fold-by-fold refitting happens automatically.

---

## 26.3 Min-max scaling

$$x' = \frac{x - x_{\min}}{x_{\max} - x_{\min}}$$

Maps the feature to $[0, 1]$.

**Worked example.** A column with values $\{10, 30, 50, 70, 90\}$. Min 10, max 90. Range = 80. Transformed: $\{(10-10)/80, (30-10)/80, ...\} = \{0, 0.25, 0.5, 0.75, 1.0\}$.

### 26.3.1 When to use it

- When you have a hard, known range and want to preserve it. For example, pixel intensities (0–255) → [0,1].
- When the algorithm expects inputs in [0, 1] (some neural-net activations).
- When you want feature contributions to be on a fixed, bounded scale.

### 26.3.2 The outlier vulnerability

Min-max scaling is dangerously sensitive to outliers. Consider:

```
x = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10000]
```

Min = 1, max = 10000. Range = 9999. The transformed first nine values are essentially zero: $(1-1)/9999 = 0$, $(2-1)/9999 \approx 0.0001$, $(9-1)/9999 \approx 0.0008$. Only the outlier is meaningfully nonzero.

You've crushed your real data into a tiny corner of the [0, 1] range and given a single outlier all the room. The model sees nine essentially-identical rows and one outlier. That's catastrophic.

Standardisation has a similar problem but less extreme: $\sigma$ is inflated by outliers but not as much as the range is.

**Fix:** detect and handle outliers before min-max scaling (Chapter 27), or use robust scaling instead.

---

## 26.4 Robust scaling

$$x' = \frac{x - \text{median}(x)}{\text{IQR}(x)}$$

Where IQR is the interquartile range ($Q_3 - Q_1$).

The median and IQR are *robust* to outliers: a single extreme value doesn't move the median (much) and doesn't change the IQR (much). So robust scaling does what standardisation does but without being thrown off by tails.

**Worked example.** A column with values $\{1, 2, 3, 4, 5, 6, 7, 8, 9, 10000\}$.

- Median = 5.5 (midpoint of 5 and 6).
- $Q_1$ = 3.25, $Q_3$ = 7.75 — computed by linear interpolation. IQR = 4.5.
- Transformed first nine values: $(1-5.5)/4.5 = -1.0$, $(2-5.5)/4.5 \approx -0.78$, ..., $(9-5.5)/4.5 \approx 0.78$.
- Transformed outlier: $(10000-5.5)/4.5 \approx 2221$. Still an outlier, but the *rest* of the data is no longer crushed.

Robust scaling is the right default when:

- You suspect or have detected outliers.
- You want a scale-comparable feature but not necessarily zero-mean unit-variance.
- The data distribution is heavy-tailed.

It's not a fix for outliers — the outlier is still an outlier. It's a way to keep your non-outlier data on a sensible scale despite the outliers.

---

## 26.5 The log transform

Money. Counts. Latencies. Sizes. File sizes. View counts. Income. Loan amounts. These have something in common: they are right-skewed, with a peak near the low end and a long tail to the right.

A histogram of `income`:

```
count
  │
  │ █                                                   
  │ █                                                  
  │ █                                                  
  │ █ █                                                 
  │ █ █ █                                              
  │ █ █ █                                              
  │ █ █ █ █                                            
  │ █ █ █ █ █                                          
  │ █ █ █ █ █ █                                        
  │ █ █ █ █ █ █ ▌ ▌                                    
  │ █ █ █ █ █ █ █ ▌ ▌ ▌ ▌                              
  │ █ █ █ █ █ █ █ █ ▌ ▌ ▌ ▌ ▌ ▌ ▌ ▌ ▌                   
  └─────────────────────────────────────►  income
   0   50K 100K          500K       2M
```

The peak is around $50K. Most rows are in [$0, $200K]. But the data extends to $2M+ — a long tail of high earners. Modeling this with a linear feature is hard: a linear coefficient has to be the right slope across both the dense low-end and the sparse high-tail.

**The log transform** compresses high values and expands low ones.

$$x' = \log(x)$$

Why log? Because for right-skewed data, the *log-scale distribution is often roughly symmetric* (sometimes called "log-normal"). After taking logs, income that ranged 1 to 10,000,000 now ranges 0 to 7 ($\log_{10}$) — and most of the mass is in the middle of that range.

A histogram of $\log(\text{income})$:

```
count
  │       █ █ █ █                                     
  │     █ █ █ █ █ █                                   
  │   █ █ █ █ █ █ █ █                                 
  │ █ █ █ █ █ █ █ █ █ █                               
  │ █ █ █ █ █ █ █ █ █ █ █                             
  │ █ █ █ █ █ █ █ █ █ █ █ █                           
  └─────────────────────────────────►   log(income)
    3   4   5   6   7
```

Roughly symmetric. The kinds of statistical models that assume approximate normality (linear regression, Gaussian Naive Bayes) now work better.

### 26.5.1 The $\log(x + 1)$ variant

Income can be zero (someone reports no income). $\log(0) = -\infty$. We need a fix.

The standard one is **log-plus-one**:

$$x' = \log(1 + x)$$

Equivalent to `np.log1p` in numpy. $\log(1 + 0) = 0$, well-defined; $\log(1 + 999) = \log(1000) \approx 6.9$, basically the same as $\log(999)$. For values near zero, the +1 matters; for large values, it's negligible.

The variant choice ($\log$, $\log_{10}$, $\log_2$, $\ln$, $\log_{1+}$) doesn't fundamentally matter for ML — they differ by a constant factor and a constant shift. Any reasonable model will absorb the constants into its coefficients.

### 26.5.2 What the log transform does geometrically

Imagine the original axis (income, dollars) and the log axis side by side:

```
original:   0 ─────── 100K ─────── 1M ─────── 10M ───
                                                  
log10:      ──── 5 ──── 6 ───── 7 ────
```

A factor-of-10 increase in income maps to an additive increase of 1 in $\log_{10}(\text{income})$. So in log-space, *equal multiplicative differences are equal additive differences*. This is exactly the right thing for many phenomena: the difference between $10K and $20K earners is, in some sense, equivalent to the difference between $1M and $2M earners — both are factor-of-2 differences. The log transform makes that explicit.

### 26.5.3 When the log transform is useful

- Right-skewed positive data with values spanning multiple orders of magnitude.
- When the underlying generating process is multiplicative (compound growth, scaling laws, etc.).
- When you suspect the *ratio* of two values matters more than their absolute difference.

### 26.5.4 When it's not appropriate

- The data isn't right-skewed. Logging a normal distribution gives you a *left*-skewed distribution, which is worse.
- The data includes negatives. $\log$ is undefined on negative numbers. You can shift first (add a constant to make everything positive) — but if the data spans negatives, see the Yeo-Johnson transform below.
- The data is bounded above (proportions, percentages). Use a logit transform instead: $\log(p / (1 - p))$.
- The model doesn't need it. Tree models don't care about distributional shape; they only care about ordering.

---

## 26.6 The Box-Cox transform

Box-Cox is a parametric family of power transformations:

$$x' = \begin{cases} \dfrac{x^\lambda - 1}{\lambda} & \text{if } \lambda \neq 0 \\ \log(x) & \text{if } \lambda = 0 \end{cases}$$

Parameter $\lambda$ controls the shape:

- $\lambda = 1$: identity ($x' = x - 1$, essentially no transform).
- $\lambda = 0.5$: square root.
- $\lambda = 0$: log.
- $\lambda = -1$: reciprocal ($x' = -1/x + 1$).

So Box-Cox is a *family* of transforms, and the log is one instance.

**The clever part:** we pick the $\lambda$ that maximises the normality of the transformed data. The procedure is to try many $\lambda$ values, transform the data with each, measure how close to normal each result is (typically via the log-likelihood of a normal distribution fit to the data), and pick the best.

In scikit-learn: `PowerTransformer(method='box-cox')`. The fit step searches over $\lambda$.

**Limitation:** Box-Cox requires *strictly positive* values. If your data has zeros or negatives, Box-Cox fails.

---

## 26.7 The Yeo-Johnson transform

Yeo-Johnson is Box-Cox's generalisation that handles non-positive values:

$$x' = \begin{cases}
\dfrac{(x + 1)^\lambda - 1}{\lambda} & \text{if } x \geq 0, \lambda \neq 0 \\
\log(x + 1) & \text{if } x \geq 0, \lambda = 0 \\
-\dfrac{(-x + 1)^{2-\lambda} - 1}{2-\lambda} & \text{if } x < 0, \lambda \neq 2 \\
-\log(-x + 1) & \text{if } x < 0, \lambda = 2
\end{cases}$$

You don't need to memorise the formula. The point is: it's a continuous, differentiable transformation that behaves like Box-Cox for positive values and gracefully extends to negatives.

In scikit-learn: `PowerTransformer(method='yeo-johnson')` (the default).

**When to use it:** when you want Box-Cox's distributional benefits but your data has zeros or negatives.

For most practical work, this is the heavy-hitter of the power-transform family. Reach for it when you have skew you want to normalise and you can't guarantee positivity.

---

## 26.8 Binning (discretisation)

Sometimes the right move with a numeric feature is to *throw away its precision* and convert it to a categorical or ordinal feature.

For `age`, instead of using the raw integer 18–90, you might bin into:
- young: 18–25
- adult: 26–40
- middle-age: 41–60
- senior: 60+

The model now sees a categorical feature instead of a continuous one. Each bin can have its own effect, independent of the others.

### 26.8.1 When binning helps

- **Non-monotonic relationships.** If `age` has a U-shaped relationship with default rate (young and old both default more than middle-aged), a linear model on raw `age` cannot capture that — it'll fit a single slope. Binning lets the model learn a different effect per bin. Tree models can already do this with deep splits; binning is mainly for non-tree models.
- **Robustness to outliers.** A wild outlier in `age` (someone's age recorded as 273) lands in the "senior" bin along with everyone over 60, and its effect is absorbed.
- **Aligning with domain.** Sometimes the business cares about the categories ("retired" vs. "working") more than the raw number, and binning makes that explicit.
- **Communicating to stakeholders.** A model whose features include "young / adult / senior" is easier to explain than one with a polynomial in age.

### 26.8.2 When it hurts

You're throwing away information. A continuous feature that genuinely has a monotonic relationship with the target loses precision when binned, and any signal within a bin is lost. Tree models, in particular, can find arbitrarily fine-grained thresholds; binning forces them into your chosen boundaries.

### 26.8.3 Binning strategies

- **Equal-width:** divide the range into $k$ equal-width buckets. Simple but sensitive to outliers (one wide bucket holds the bulk of the data).
- **Equal-frequency (quantiles):** each bucket has the same number of rows. Robust to outliers; each bucket is well-populated.
- **Domain-defined:** human-meaningful boundaries (e.g., "retirement age = 65").
- **Optimal binning:** find the boundaries that maximally separate the target — algorithms like ChiMerge or MDLP. Used in credit-scoring "WOE binning."

scikit-learn's `KBinsDiscretizer` supports equal-width and equal-frequency.

---

## 26.9 Where scaling does and doesn't matter, by algorithm

A consolidated table — refer back to this when you're deciding whether to bother scaling for a given model.

| Algorithm                       | Needs scaling? | Why |
|---------------------------------|:--------------:|-----|
| Linear regression               | Yes (for convergence and regularization) | Gradient descent + coefficient interpretation |
| Logistic regression             | Yes            | Same |
| Ridge / lasso                   | **Especially yes** | Penalty applies uniformly; unscaled features get unfair penalties |
| SVM (RBF or linear)             | Yes            | Distance- and dot-product-based |
| K-nearest neighbors             | Yes            | Distance-based |
| K-means clustering              | Yes            | Distance-based |
| PCA                             | Yes            | Decomposes covariance; scale matters |
| Naive Bayes (Gaussian)          | Sometimes       | The Gaussian assumption is about distributional shape, not scale |
| Decision tree                   | **No**         | Threshold splits are invariant to monotonic transforms |
| Random forest                   | **No**         | Same |
| Gradient-boosted trees (XGBoost, LightGBM) | **No**  | Same |
| Neural networks                 | Yes            | Activations/gradients propagate cleanly with scaled inputs |

The rule of thumb: **anything that uses Euclidean distance, dot products, or penalises coefficients needs scaling.** Anything that uses thresholds doesn't.

---

## 26.10 A worked end-to-end example

We have a `loans` DataFrame with `income`, `loan_amount`, `applicant_age`, `debt_to_income`, and a binary `default` target.

Inspect:

- `income`: heavily right-skewed, range $0$ to $5,000,000$, peak around $50,000$.
- `loan_amount`: right-skewed, range $500$ to $40,000$.
- `applicant_age`: 18 to 75, roughly normal.
- `debt_to_income`: 0 to 0.95, roughly normal.

We plan to fit a logistic regression. Logistic regression cares about scale (Chapter 32) and benefits from approximately-symmetric features.

**Decisions:**

- `income`: log-transform first (handle the skew), then standardise (put on the same scale as other features).
- `loan_amount`: same — log-transform, then standardise.
- `applicant_age`: standardise (already symmetric).
- `debt_to_income`: standardise.

**Code (scikit-learn).**

```python
from sklearn.preprocessing import StandardScaler, FunctionTransformer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
import numpy as np

log_then_scale = Pipeline([
    ('log', FunctionTransformer(np.log1p)),
    ('scale', StandardScaler()),
])

preprocess = ColumnTransformer([
    ('log_scale', log_then_scale, ['income', 'loan_amount']),
    ('scale', StandardScaler(), ['applicant_age', 'debt_to_income']),
])

model = Pipeline([
    ('preprocess', preprocess),
    ('logreg', LogisticRegression(max_iter=1000)),
])

model.fit(X_train, y_train)
```

The `FunctionTransformer(np.log1p)` is the log-plus-one transform. The `Pipeline` ensures every parameter is fit on the training portion and applied to test/validation.

**The result.** All four features now have approximately mean zero, unit variance. The logistic regression coefficients are now comparable — they represent the effect of a one-standard-deviation change in each feature. The optimizer converges in a few iterations.

If instead you'd plugged the raw `income` column (ranging 0 to 5M) into the logistic regression, the optimizer would have either failed to converge or settled on a tiny coefficient that produced absurd predictions on the high-income rows.

---

## 26.11 Tree models: why you can usually skip scaling

A decision tree (Chapter 33) recursively splits the data based on threshold conditions: "is $x_j < t$?" The choice of $t$ depends only on the *ordering* of values in $x_j$, not their magnitudes.

Claim: **any monotonic transformation $f$ of $x_j$ leaves the tree unchanged.** If the tree before transformation was splitting at $t$, then after transforming $x_j \to f(x_j)$, the equivalent split would be $f(x_j) < f(t)$. The same rows go left, the same rows go right. The tree's predictions are identical.

This holds for any monotonic $f$: linear scaling, log, Box-Cox, anything that preserves order. Tree models are completely scale-invariant.

**Implication.** If you're training a tree model (XGBoost, Random Forest, LightGBM, GBT), don't waste time scaling. The transforms add no value. Skip the pipeline stage entirely.

The one exception is when *the same pipeline* will feed both a tree and a non-tree model (e.g., an ensemble that combines XGBoost with logistic regression). Then you scale because the linear model needs it, and the tree just ignores the irrelevant scaling.

---

## 26.12 Order of operations

A common question: do you scale before or after handling missing values, outliers, categorical encoding?

The rough order, for a typical pipeline:

1. **Handle missing values first** (impute or drop). Scaling assumes the column has values.
2. **Handle outliers** (cap, winsorize, or transform). Don't standardise data with extreme outliers — your $\sigma$ will be inflated and the transformed non-outlier data will be crushed.
3. **Apply non-linear transforms** (log, Box-Cox). These reshape the distribution.
4. **Scale** (standardise, min-max, robust). Final step before the model.
5. **Encode categoricals separately**. They have their own pipeline (Chapter 25) that doesn't intersect with numeric scaling.

In a `ColumnTransformer`-based scikit-learn pipeline, each column or column group gets its own sub-pipeline of these stages. The whole thing is fit once on training and applied to test/validation/serving.

---

## 26.13 PySpark scaling, briefly

In Spark ML:

```python
from pyspark.ml.feature import StandardScaler, MinMaxScaler, RobustScaler
from pyspark.ml.feature import VectorAssembler

# Spark ML scalers operate on a single Vector column.
# So first assemble the numeric columns into a vector.
assembler = VectorAssembler(inputCols=['income','loan_amount','age','dti'],
                            outputCol='features_raw')

scaler = StandardScaler(inputCol='features_raw', outputCol='features',
                        withMean=True, withStd=True)

# In a Pipeline:
from pyspark.ml import Pipeline
pipeline = Pipeline(stages=[assembler, scaler, ...])
```

A few quirks:
- Spark's scalers operate on `Vector`-type columns, not individual columns. You assemble first.
- `withMean=True` requires dense vectors (or it densifies sparse ones, which can be memory-painful at scale). For sparse data, leave `withMean=False`.
- Spark has no built-in `PowerTransformer` (Box-Cox / Yeo-Johnson). You implement these yourself via UDFs or precompute in pandas before Spark.

For most exam-relevant work, `StandardScaler` and `MinMaxScaler` are what you'll see in Spark ML pipelines.

---

## 26.14 What this builds on / where it returns

**Builds on:**

- Chapter 5–6 (Part B): mean, variance, standard deviation, the normal distribution.
- Chapter 23 (EDA): you discovered skew, outliers, and disparate scales during EDA. Now you fix them.
- Chapter 17 (gradient descent): the convergence argument for why scaling matters in optimisation.
- Chapter 20 (regularization): the penalty argument for why scaling matters with ridge/lasso.

**Returns in:**

- Chapter 27 (outliers): the relationship between scaling and outlier handling.
- Chapter 31–32 (linear/logistic regression): the coefficient interpretation under scaling.
- Chapter 37 (KNN): why distance-based algorithms are particularly scale-sensitive.
- Chapter 38–40 (clustering, PCA): why these unsupervised algorithms need scaling.
- Chapter 62–63 (Spark Pipelines / Transformers): how Spark ML wires up scaling stages.

---

## 26.15 Exercises

1. **Standardisation by hand.** A column has values $\{2, 4, 6, 8, 10\}$. Compute the mean, variance, std, and the standardised values. Verify the standardised values have mean 0 and variance 1.

2. **Min-max disaster.** A column has values $\{1, 2, 3, 4, 5, 1000000\}$. Compute the min-max transformed values. Comment on what the model will see.

3. **Robust vs. standard.** For the same column $\{1, 2, 3, 4, 5, 1000000\}$, compute the robust-scaled values (using median and IQR). Compare to the standardised values.

4. **The log transform with zero.** A `purchase_count` column has values $\{0, 0, 1, 3, 5, 200\}$. Apply $\log(x+1)$ transform. What are the resulting values?

5. **Which scaler.** For each algorithm, name the scaler you'd reach for (or "none"):
   (a) Linear regression with L2 regularization.
   (b) Random forest.
   (c) K-means clustering.
   (d) XGBoost.
   (e) PCA.
   (f) KNN with k=5.

6. **Scaling and tree models.** Prove (briefly) that standardisation leaves the predictions of a decision tree unchanged.

7. **The leakage trap.** A junior data scientist standardises the entire dataset, then does a 5-fold CV. What's the problem? How bad is it in practice?

8. **Log of negatives.** A `account_balance` column has both positive and negative values (debt vs. credit). You want a log-like transform. Which transform do you reach for, and why?

9. **Box-Cox vs. Yeo-Johnson.** Your `income` column has a small number of rows with zero income. Can you use Box-Cox? What about Yeo-Johnson?

10. **Binning vs. raw.** When would you bin a continuous feature even if your model is a gradient-boosted tree?

11. **The coefficient comparison.** After standardising, your logistic regression has coefficients: `income_z = 0.8`, `age_z = 0.3`, `debt_ratio_z = -1.1`. Interpret what these tell you about the relative importance of the features.

12. **Sparse data and standardisation.** Why is `StandardScaler` with `with_mean=True` a bad idea on a sparse text feature matrix?

13. **Multiple transforms in sequence.** Why do we log-then-scale `income` rather than scale-then-log, or just one?

<details>
<summary>Answers</summary>

1. Mean = 6, variance = $((2-6)^2 + (4-6)^2 + (6-6)^2 + (8-6)^2 + (10-6)^2)/5 = (16+4+0+4+16)/5 = 8$, std = $\sqrt{8} \approx 2.83$. Standardised: $\{(2-6)/2.83, ...\} = \{-1.41, -0.71, 0, 0.71, 1.41\}$. Mean of these is 0, sum of squares is $1.41^2 + 0.71^2 + 0 + 0.71^2 + 1.41^2 = 1.99 + 0.50 + 0 + 0.50 + 1.99 = 4.98 \approx 5$, divided by 5 gives variance 1.

2. Min = 1, max = 1,000,000. Range = 999,999. Transformed: $\{0, 1.0\text{e-}6, 2.0\text{e-}6, 3.0\text{e-}6, 4.0\text{e-}6, 1.0\}$. The first five values are essentially zero from the model's perspective. The outlier has all the room. Disastrous: the model sees five identical values and one outlier instead of five-graded values and one outlier.

3. Median = 3.5. $Q_1 = 1.75$, $Q_3 = 4.75$, IQR = 3. Robust-scaled: $\{-0.83, -0.50, -0.17, 0.17, 0.50, 332{,}832\}$. The first five values now have meaningful spread. The outlier is still extreme but the rest of the data isn't crushed.

4. $\{\log(1), \log(1), \log(2), \log(4), \log(6), \log(201)\} = \{0, 0, 0.69, 1.39, 1.79, 5.30\}$. The 200 is no longer 200× the others; it's about 8× the next-largest.

5. (a) StandardScaler. (b) None. (c) StandardScaler or RobustScaler. (d) None. (e) StandardScaler. (f) StandardScaler or RobustScaler (any scaler — KNN just needs comparable scales).

6. A decision tree's splits are of the form $x_j < t$. Standardising replaces $x_j$ with $(x_j - \mu)/\sigma$. The equivalent split is $(x_j - \mu)/\sigma < t'$, where $t' = (t - \mu)/\sigma$. The same rows go left/right because the ordering of values in $x_j$ is preserved by standardisation. The tree finds an equivalent split with a different threshold, yielding the same predictions.

7. The mean and std are computed using test-set rows. Test information leaks into the training process via the scaler. In practice, the leak via $\mu$ and $\sigma$ is usually small — they're well-estimated and stable — but the *discipline* matters: more sophisticated transforms (like target encoding) have far worse leakage when the same mistake is made. Always fit on train only.

8. Yeo-Johnson, because $\log$ and Box-Cox are undefined on non-positive values. Yeo-Johnson is designed for this case: it behaves like Box-Cox for positives and gracefully extends to zero and negatives.

9. Box-Cox no — requires strictly positive values. Yeo-Johnson yes — it handles zero (and negative) values cleanly.

10. (a) You want to constrain the splits to specific business-meaningful boundaries (regulatory or interpretability reasons). (b) You want to reduce overfitting on fine-grained noise — a deeply-split tree may overfit; binning forces a coarser view. (c) You're combining the tree's output with a linear model that needs categorical features. (d) The continuous feature has heavy-tailed outliers and binning absorbs them.

11. The coefficients are now on the same "per-standard-deviation" scale. `debt_ratio_z` has the largest absolute coefficient (1.1), so a one-std-deviation increase in `debt_ratio` has the biggest effect on the log-odds of default — and it's *negative* (lowering predicted default probability). `income_z` has the second-largest effect (0.8, positive). `age_z` has a moderate positive effect (0.3). Without standardisation, the raw coefficients would be uncomparable.

12. Sparse text data is mostly zeros. Centering subtracts the mean from every value, turning the zeros into non-zero numbers. The matrix is no longer sparse, blowing up memory by 100× or more. Use `StandardScaler(with_mean=False)` or `MaxAbsScaler` instead for sparse data.

13. Scale-then-log doesn't help: scaling is linear, log is non-linear, so the order matters. If you scale first, the resulting values include zeros and negatives (because we've centered around the mean), and $\log$ won't work. Logging first reshapes the distribution; scaling afterward puts the (now-symmetric) values on the standard scale. You need both: log fixes the skew; scaling fixes the magnitude. Skipping either leaves a problem.

</details>
