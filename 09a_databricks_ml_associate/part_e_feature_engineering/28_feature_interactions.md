# Chapter 28 — Feature Interactions, Polynomial Features, and Basis Expansions

> **Goal of this chapter:** to teach you how to give a linear model a fighting chance at non-linear problems. Linear models combine features *linearly* — their predictions are weighted sums. If the world is not linear in your features, you have two choices: abandon the linear model, or *engineer features that linearise the relationship*. This chapter teaches the second option. By the end, you'll be able to construct interaction terms, polynomial features, cyclical encodings, and basis expansions — and you'll understand why "with enough features, a linear model can fit anything," and why that is both wonderful and dangerous.

---

## 28.1 The setup: why a linear model isn't enough

Recall the linear regression form from Chapter 3 and (formally) Chapter 31:

$$\hat{y} = w_1 x_1 + w_2 x_2 + \cdots + w_d x_d + b$$

The prediction is a *linear function* of the features. The model can choose $w_j$ freely, but the *form* — weights times features, added up — is fixed.

This is enough when the world is approximately linear in the features. Predict house price from square footage and number of bedrooms; the relationship is roughly linear in both. A linear model handles it gracefully.

It is *not* enough when the world is non-linear. Three examples:

1. **The cost of a sale price on demand depends on whether it's a holiday.** Cutting the price by 10% during the post-holiday slump barely moves the needle. Cutting the price by 10% on Black Friday increases demand by 50%. The effect of `discount` on `demand` *depends* on `is_holiday`. A linear model says `demand = w_d * discount + w_h * is_holiday + b`. It cannot express "the effect of discount changes based on holiday status." It will fit some compromise that's wrong everywhere.

2. **Medical costs depend on age in a non-monotonic way.** Costs are high for the very young (births, pediatric care), low in middle age, and rise sharply after 65 (chronic disease). A linear model fits a single slope across age and gets every region wrong.

3. **Pricing on time-of-day has a sin/cos shape.** Demand for ride-sharing peaks at 8 am and 6 pm and dips in the middle of the night. A linear model on `hour_of_day` (0–23) fits a single slope and misses everything.

You have two choices. The first is to use a fundamentally non-linear model: a tree, a kernel SVM, a neural network. We'll get to those.

The second is to *create features that capture the non-linearity*, so that the linear model now has the raw material to express the relationship as a linear combination. This is feature engineering at its most elegant.

---

## 28.2 Interaction terms

Suppose two features $x_1$ and $x_2$ have an interaction: the effect of $x_1$ on $y$ depends on $x_2$. Mathematically, the true relationship is

$$y = f(x_1, x_2) = a \cdot x_1 + b \cdot x_2 + c \cdot x_1 \cdot x_2 + \text{noise}$$

The $c \cdot x_1 \cdot x_2$ term is the *interaction*: a product of the two features.

A linear model on raw $x_1$ and $x_2$ cannot express this. But if we *give* the model a new feature $x_3 = x_1 \cdot x_2$, then the model becomes

$$\hat{y} = w_1 x_1 + w_2 x_2 + w_3 x_3 + b$$

and the model can learn $w_3 \approx c$. We've made a non-linear relationship learnable by a linear model, simply by handing it the right product feature.

### 28.2.1 A worked example: medical costs

Predict annual medical cost from `age` and `smoker_status` (binary 0/1).

Naive linear model:

$$\hat{\text{cost}} = w_a \cdot \text{age} + w_s \cdot \text{smoker} + b$$

Suppose the true relationship is: medical cost = $200 \cdot \text{age} + 1000 \cdot \text{smoker} + 50 \cdot \text{age} \cdot \text{smoker}$. (Smoking is more dangerous for older people.)

The linear model fits *some* $w_a$ and $w_s$ but cannot capture the interaction. The fit will be poor — it'll over-predict for young non-smokers and under-predict for old smokers (or vice versa).

Add an interaction term: `age_smoker = age * smoker`.

$$\hat{\text{cost}} = w_a \cdot \text{age} + w_s \cdot \text{smoker} + w_{as} \cdot \text{age\_smoker} + b$$

Now the model can learn $w_a = 200$, $w_s = 1000$, $w_{as} = 50$. Perfect fit (in the noiseless case).

The interaction *unlocked* the linear model.

### 28.2.2 When to look for interactions

You don't blindly multiply every pair of features (combinatorial explosion — see §28.5). You hypothesise interactions based on:

- **Domain knowledge.** Smoking × age. Price × holiday. Education × experience.
- **EDA evidence.** A scatter plot where the slope of $x_1$ vs. $y$ visibly changes depending on $x_2$.
- **Stratified analysis.** Group by $x_2$, compute the correlation of $x_1$ with $y$ in each group. If the correlations differ substantially, there's an interaction.
- **Model diagnostics.** Tree models implicitly find interactions through their splits; you can use feature importance and partial dependence (out of scope, but worth knowing) to identify which interactions the tree found, then engineer them as explicit features for a linear model.

### 28.2.3 Higher-order interactions

You can also have three-way interactions: $x_1 \cdot x_2 \cdot x_3$. The effect of $x_1$ on $y$ depends on $x_2$ *and* $x_3$ jointly.

These are rare in practice (and hard to interpret). Most of the value of interactions comes from two-way products.

---

## 28.3 Polynomial features

A different non-linearity: the relationship between *one* feature and the target is non-monotonic or non-linear.

Take the medical-cost-by-age example from §28.1. Costs are high at both ends of the age spectrum. A linear model on `age` fits a single slope — choose any slope and you're wrong somewhere.

The fix: give the model both `age` and `age²`. Now it can fit a parabola.

$$\hat{\text{cost}} = w_1 \cdot \text{age} + w_2 \cdot \text{age}^2 + b$$

With $w_1 < 0$ and $w_2 > 0$, the parabola opens upward with a minimum somewhere in middle age — exactly the right shape.

If the relationship is more complex, add `age³`, `age⁴`, etc. Each higher-degree term gives the model another "bend" it can fit.

### 28.3.1 Polynomial expansion in scikit-learn

`PolynomialFeatures(degree=k)` automatically generates all terms up to degree $k$.

For input $\{x_1, x_2\}$ with degree=2, it produces:

$$\{1, x_1, x_2, x_1^2, x_1 x_2, x_2^2\}$$

(The 1 is the intercept term; the linear terms are $x_1$ and $x_2$; the quadratic terms are $x_1^2$, $x_2^2$; the interaction is $x_1 x_2$.)

For degree=3 with $\{x_1, x_2\}$:

$$\{1, x_1, x_2, x_1^2, x_1 x_2, x_2^2, x_1^3, x_1^2 x_2, x_1 x_2^2, x_2^3\}$$

Notice that `PolynomialFeatures` produces *both* the polynomial terms (squared, cubed) *and* the interactions (products). With `interaction_only=True`, it skips the same-feature powers and produces only the cross-products.

### 28.3.2 The bias-variance trap returns

Higher-degree polynomials fit more aggressively. This is Chapter 19's bias-variance picture: low-degree models underfit, high-degree models overfit.

A 10th-degree polynomial fit to 20 noisy points will wiggle wildly through every point, fitting noise as if it were signal. The training error is near zero, the validation error is huge. Classic overfitting.

Regularization (Chapter 20) is your friend here. A 10th-degree polynomial with L2 regularization (Ridge regression) often outperforms a 3rd-degree polynomial without regularization — the regularizer keeps the high-order coefficients small, fitting the smooth signal without chasing the noise.

In practice, polynomial degree is a hyperparameter you cross-validate (Chapter 22). Degrees 2 and 3 are common; degree 4 occasionally; degree 5+ rarely useful and dangerous without strong regularization.

### 28.3.3 A worked example: medical costs by age, again

We have noisy synthetic data: cost depends on age via a parabola, plus noise.

```python
import numpy as np

age = np.linspace(0, 80, 50)
cost = 0.5 * (age - 40)**2 + 100 + np.random.normal(0, 20, 50)
# Minimum at age 40, parabola opening upward.
```

Fit a linear regression on `age` alone: gets a roughly flat line — terrible fit, R² near 0.

Add `age**2`:

```python
X = np.column_stack([age, age**2])
# Linear regression on [age, age²]
# Coefficients: -40, 0.5
# Intercept: ~900
```

The model perfectly captures the parabola. R² near 1 (modulo the noise).

Without the engineered feature, the linear model is helpless. With it, the linear model is exactly right.

---

## 28.4 Basis expansions: the general idea

Polynomial features are one instance of a broader pattern: replace your single feature $x$ with a vector of *basis functions* $\phi_1(x), \phi_2(x), \ldots, \phi_k(x)$.

$$\hat{y} = w_1 \phi_1(x) + w_2 \phi_2(x) + \cdots + w_k \phi_k(x) + b$$

The model is still *linear in the parameters* $w_j$ — so it's still a linear model from the optimisation perspective — but it's *non-linear in $x$*. The non-linearity is entirely in your choice of $\phi$.

Different choices of $\phi$ give different model families:

- **Polynomial basis:** $\phi_j(x) = x^j$. Polynomial regression.
- **Radial basis functions:** $\phi_j(x) = \exp(-(x - c_j)^2 / \sigma^2)$, centred at preset locations $c_j$. Useful for local features.
- **Spline basis:** piecewise polynomials joined smoothly at preset "knots." Most flexible for non-monotonic continuous relationships.
- **Fourier basis:** $\phi_j(x) = \sin(jx), \cos(jx)$. Useful for periodic data.
- **B-splines, natural splines, cubic splines:** specific spline parameterisations. `patsy` and `scipy.interpolate.BSpline` for Python; `splines` in R.

The kernel trick in SVMs (mentioned lightly here, deeper in Chapter 37) is a way to do basis expansion *implicitly*: instead of computing $\phi(x)$ explicitly, you only compute $\phi(x_i)^T \phi(x_j)$ as a "kernel function" $K(x_i, x_j)$. This lets you use infinite-dimensional bases (radial-basis kernel) without ever materialising the features. For the ML Associate exam, you don't need the kernel trick deeply — just know that it exists and that the basis-expansion intuition extends to SVMs.

---

## 28.5 The combinatorial explosion

Here's the catch. `PolynomialFeatures(degree=3)` on 10 input features produces:

- The constant: 1 term.
- The linear terms: 10 terms.
- The quadratic terms (squared + cross-products): $\binom{10+1}{2} = 55$ terms.
- The cubic terms: $\binom{10+2}{3} = 220$ terms.

Total: 286 features from the original 10. With degree=4: ~715. With degree=5: ~3,003.

The number of polynomial features grows roughly as $\binom{d + k - 1}{k - 1}$ for $d$ features and degree $k$. Cubic of 100 features: ~176,000.

**Consequences:**

- **Memory.** A dataset of 100,000 rows × 176,000 features is 17.6 billion floats — about 70 GB at single-precision. Impractical.
- **Estimation.** With 176,000 coefficients to estimate, you need vastly more rows than that for the fit to be reliable. The bias-variance tradeoff tips hard toward variance.
- **Multicollinearity.** Polynomial features are highly correlated (e.g., $x$ and $x^2$ are correlated when $x$ has limited range). The design matrix becomes nearly singular; coefficients become unstable.
- **Interpretation.** A model with 176,000 features is not interpretable.

The standard mitigations:

1. **Only generate interactions you suspect.** Don't blindly use `PolynomialFeatures(degree=3)`. Manually craft the interactions that domain knowledge suggests.
2. **Use `interaction_only=True`.** Skips the same-feature powers; keeps only cross-products. Fewer features.
3. **Regularize.** L1 (lasso) will drive most coefficients to zero, performing implicit feature selection on the polynomial expansion.
4. **Use a tree model instead.** Trees automatically find interactions through their splits, without you having to enumerate them. For high-dimensional problems with many possible interactions, this is usually the right answer.

---

## 28.6 Cyclical features: encoding hour, day, month

Some features are *periodic*: they wrap around. The hour 23 and the hour 0 are one hour apart, not 23 hours apart. The same applies to day-of-week (Sunday → Monday), month (December → January), and any angular measurement.

A linear model treating `hour` as 0–23 sees 23 and 0 as the most distant possible values — exactly wrong.

The fix: encode the cyclical feature as a pair of (sin, cos) of its angular position.

$$x_{\sin} = \sin\left(\frac{2 \pi \cdot \text{hour}}{24}\right)$$

$$x_{\cos} = \cos\left(\frac{2 \pi \cdot \text{hour}}{24}\right)$$

The (sin, cos) representation puts each hour on a circle. Hour 23 sits at angle $\sim 345°$; hour 0 sits at angle $0°$; their (sin, cos) coordinates are close. Hour 12 sits at angle $180°$ — opposite hour 0.

**Worked example.** A few hours:

| hour | angle (°) | sin    | cos    |
|-----:|----------:|-------:|-------:|
| 0    | 0         | 0      | 1      |
| 6    | 90        | 1      | 0      |
| 12   | 180       | 0      | -1     |
| 18   | 270       | -1     | 0      |
| 23   | 345       | -0.26  | 0.97   |

Hour 0 and hour 23 have (sin, cos) = (0, 1) and (-0.26, 0.97) — Euclidean distance about 0.26. Hour 0 and hour 12 have distance 2.0. The encoding correctly captures cyclic proximity.

A linear model on (sin, cos) of hour can fit any single-cycle pattern: a peak at any time of day, two peaks per day, monotonic trends through the day. For higher-frequency patterns (peaks every 4 hours), you'd add $\sin(2 \cdot 2\pi \cdot h / 24)$ and $\cos(2 \cdot 2\pi \cdot h / 24)$ — the higher harmonics. This is essentially a Fourier basis.

**Apply this to:**

- `hour_of_day` (period 24).
- `day_of_week` (period 7).
- `day_of_year` (period 365 or 366).
- `month_of_year` (period 12).
- `angle_of_arrival`, `wind_direction`, any angular sensor reading (period 360°).

**Don't apply this to:**

- Truly linear time (`days_since_epoch`). It's monotonic, not cyclic.
- Time features where the cycle isn't relevant (e.g., the model only cares about "is it business hours" — a single boolean is fine).

---

## 28.7 Domain-specific feature engineering

A few patterns that come up over and over in real ML projects:

### 28.7.1 Ratios

For features that scale together, a ratio is often more informative than either alone.

- `debt / income`: the debt-to-income ratio. More meaningful than debt or income alone for credit risk.
- `purchases_last_30d / purchases_last_365d`: a measure of recent activity. Captures velocity changes.
- `clicks / impressions`: click-through rate. More meaningful than raw clicks (which scale with impressions).

Linear models cannot compute ratios from raw features (a linear combination of $x_1$ and $x_2$ never gives you $x_1 / x_2$). Tree models can approximate ratios with deep splits, but it's expensive. Engineering the ratio explicitly is almost always a win.

### 28.7.2 Differences

For features measured at different times or in different places, the *difference* is often what matters.

- `current_balance - balance_30d_ago`: change in balance.
- `today_price - yesterday_price`: price delta.
- `expected_arrival - actual_arrival`: delay.

Same reasoning as ratios: linear models can express linear differences (a difference of two features is just a linear combination with coefficients $+1, -1$), so a linear model can learn a "difference feature" *if you regularise properly*. But making the difference explicit is faster and more interpretable.

### 28.7.3 Aggregations

For each row, summarise some related window of data.

- `transactions_count_last_30d`: number of transactions for this user in the last 30 days.
- `avg_purchase_amount_last_365d`: average purchase amount.
- `max_late_payment_days_last_24mo`: worst late payment.
- `unique_merchants_last_90d`: count of distinct merchants.

These are *temporal* aggregations: you have a stream of events and you summarise the window leading up to the current moment. The feature store (Chapter 30 and Chapter 71) is the right architectural home for these — they need to be computed consistently between training and serving, and they're the same features used by many models.

### 28.7.4 Date and time deltas

- `days_since_last_login`: how recently was the user active?
- `days_until_payment_due`: how far ahead are we predicting?
- `customer_tenure_months`: how long has this customer been with us?

The raw timestamps themselves are usually not what you want — they're large, monotonic numbers that don't generalise across time. Deltas from a reference point (now, the event time, etc.) are much more useful.

### 28.7.5 Indicator features for structural conditions

- `has_attachments`: boolean derived from `attachment_count > 0`.
- `is_weekend`: boolean derived from `day_of_week ∈ {Sat, Sun}`.
- `is_first_loan`: boolean derived from "this customer has no prior loans in the data."

Indicators turn continuous or categorical structure into binary flags that linear models can incorporate naturally.

---

## 28.8 A worked example: cyclical + interaction together

Predicting Uber demand from `hour_of_day` and `is_weekend`.

Phenomenon: demand peaks at 8 am and 6 pm on weekdays (commutes); peaks at midnight on weekends (nightlife). The peaks are at *different hours* depending on day-type — a classic interaction.

**Naive linear features:** `hour`, `is_weekend`. Linear model:

$$\hat{\text{demand}} = w_h \cdot \text{hour} + w_w \cdot \text{is\_weekend} + b$$

Can't capture either the cyclicity *or* the interaction. Bad fit.

**Cyclical encoding:** $(\sin(2\pi h/24), \cos(2\pi h/24))$.

$$\hat{\text{demand}} = w_s \cdot \sin(\cdot) + w_c \cdot \cos(\cdot) + w_w \cdot \text{is\_weekend} + b$$

Captures cyclicity but not the interaction. The model assumes the same daily pattern shifts up or down on weekends, not that the *pattern itself* changes.

**Cyclical + interaction:** add cross terms.

$$\hat{\text{demand}} = w_s \cdot \sin + w_c \cdot \cos + w_w \cdot \text{is\_weekend} + w_{sw} \cdot (\sin \cdot \text{is\_weekend}) + w_{cw} \cdot (\cos \cdot \text{is\_weekend}) + b$$

The interaction terms let the model learn one (sin, cos) pattern for weekdays and a *different* (sin, cos) pattern for weekends. Now the model captures both the cyclic structure and the day-type modulation.

Without the engineered features, you'd need a non-linear model (tree, neural net). With them, a linear model with 6 features handles the problem cleanly.

---

## 28.9 Code patterns

scikit-learn:

```python
from sklearn.preprocessing import PolynomialFeatures

# All polynomial terms up to degree 2 (including same-feature squares and cross-products)
poly = PolynomialFeatures(degree=2, include_bias=False)
X_poly = poly.fit_transform(X)
print(poly.get_feature_names_out())
# ['x0', 'x1', 'x0^2', 'x0 x1', 'x1^2']

# Only cross-products, no same-feature squares
poly = PolynomialFeatures(degree=2, interaction_only=True, include_bias=False)
X_inter = poly.fit_transform(X)
# ['x0', 'x1', 'x0 x1']
```

Manual interactions in pandas:

```python
df['age_smoker'] = df['age'] * df['smoker']
df['debt_to_income'] = df['debt'] / (df['income'] + 1)  # +1 to avoid divide-by-zero
```

Cyclical encoding:

```python
import numpy as np

df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)

df['dow_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
df['dow_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
```

In PySpark:

```python
from pyspark.sql.functions import sin, cos, col, lit
import math

df = df.withColumn('hour_sin', sin(2 * math.pi * col('hour') / 24))
df = df.withColumn('hour_cos', cos(2 * math.pi * col('hour') / 24))
df = df.withColumn('age_smoker', col('age') * col('smoker'))
```

Spark ML's `Interaction` transformer can compute cross-products between feature vectors. `PolynomialExpansion` produces polynomial terms. Both operate on `Vector`-typed columns (after `VectorAssembler`).

---

## 28.10 Trees vs. engineered features

A philosophical aside.

Tree-based models — random forests, gradient-boosted trees — find interactions and non-linearities *automatically*. Every split in a tree, on a feature $x_j$, is implicitly conditioned on the splits above it (on possibly different features). With enough depth, a tree can model an arbitrarily complex interaction without you ever engineering it.

So for tree models, do you still bother with interactions, polynomial features, and cyclical encodings?

The answer is *sometimes*. Specifically:

- **Cyclical encoding for trees**: still helpful. A tree on raw `hour` (0–23) will spend many splits to learn that hour 23 and hour 0 are similar; the (sin, cos) encoding gives it the right geometry up front. Cyclical encoding helps tree models on periodic data.
- **Domain ratios (debt/income, etc.)**: still helpful. A tree could *approximate* a ratio with many splits, but the explicit ratio is far more efficient.
- **Polynomial features**: usually not helpful for trees. The tree finds non-monotonic relationships naturally through depth.
- **Cross-product interactions**: usually not helpful for trees. The tree finds interactions naturally through depth.

The general principle: any feature that makes a complex relationship *trivial* (or near-trivial) for a tree to split on is helpful. Features that just expand the search space without making anything easier add cost without benefit.

For linear models, the calculus is opposite: you *must* engineer the non-linearities, because the linear model cannot find them itself.

---

## 28.11 What this builds on / where it returns

**Builds on:**

- Chapter 3, Chapter 31: the linear model form $\hat{y} = w^T x + b$.
- Chapter 19, Chapter 20: bias-variance and regularization, the controls on polynomial overfitting.
- Chapter 25–26: encoding and scaling, the precursors to engineering interactions.

**Returns in:**

- Chapter 32 (logistic regression): the same trick works there — engineered features let logistic regression fit non-linear decision boundaries.
- Chapter 33–34 (trees): trees find these structures natively, motivating the comparison in §28.10.
- Chapter 37 (SVMs, briefly): the kernel trick is implicit basis expansion.
- Chapter 40 (PCA): a different perspective on linear combinations of features.

---

## 28.12 Exercises

1. **Interaction by hand.** A model predicts `tip` from `meal_cost` and `is_holiday`. The true relationship is `tip = 0.15 * meal_cost + 0.05 * meal_cost * is_holiday`. What features must a linear model see to fit this exactly? Write the model equation.

2. **Polynomial features count.** `PolynomialFeatures(degree=3)` is applied to 5 input features. How many output features does it produce (including the bias term)?

3. **The cyclical question.** Encode the hour 23 and the hour 1 with $(\sin(2\pi h/24), \cos(2\pi h/24))$. Compute their Euclidean distance. Now encode them naively as just `hour` and compute the distance. Comment.

4. **Day-of-week.** Why might you encode `day_of_week` cyclically for predicting restaurant demand, but linearly for predicting Friday-only-promotions outcome?

5. **The overfitting trap.** You fit a 10th-degree polynomial to 20 training points. Training R² is 0.99; validation R² is -0.4. What's going on? What's the fix?

6. **A ratio feature.** You have `debt` and `income`. You add `debt / income`. Your tree model's performance improves slightly. Why might this be?

7. **Combinatorial pruning.** You have 50 features and you want all pairwise interactions. How many cross-products are there? How would you decide which subset to actually use?

8. **L1 regularization on polynomials.** You apply `PolynomialFeatures(degree=4)` to 10 features (715 polynomial features). You fit a Lasso regression. What does Lasso do to most of those 715 coefficients?

9. **The (sin, cos) limit.** A demand curve has *two* peaks per day (morning and evening). A single (sin, cos) pair captures only one cycle per period. What do you add to capture two cycles per day?

10. **Trees and interactions.** Explain why a random forest, in principle, does not require you to engineer interaction terms.

11. **Tree and cyclical.** Despite the answer to #10, you decide to add (sin, cos) of `hour` to your random forest. The performance still improves. Why?

12. **Date deltas.** You're predicting whether a user will churn. You have `signup_date` and `last_login_date`. What engineered features would you create from these two columns?

13. **Multicollinearity from polynomials.** $x$ and $x^2$ are highly correlated when $x$ ranges over a narrow interval. Why? What can you do to reduce this issue before fitting?

<details>
<summary>Answers</summary>

1. The model needs the cross-product `meal_cost * is_holiday` as a feature. The model equation: $\hat{\text{tip}} = w_1 \cdot \text{meal\_cost} + w_2 \cdot \text{is\_holiday} + w_3 \cdot (\text{meal\_cost} \cdot \text{is\_holiday}) + b$. With the right coefficients, the model fits exactly: $w_1 = 0.15$, $w_3 = 0.05$, $w_2 = 0$, $b = 0$.

2. For $d=5$ features and degree $k=3$, the number of polynomial features (including the bias term) is $\binom{d+k}{k} = \binom{8}{3} = 56$.

3. Cyclical: $h=23 \to (\sin(23\pi/12), \cos(23\pi/12)) \approx (-0.26, 0.97)$. $h=1 \to (\sin(\pi/12), \cos(\pi/12)) \approx (0.26, 0.97)$. Distance ≈ $\sqrt{(0.26 - (-0.26))^2 + 0^2} = 0.52$. Naively: distance = $|23 - 1| = 22$. The cyclical encoding correctly captures that hours 23 and 1 are 2 hours apart on the clock; the naive encoding wrongly says 22 hours apart.

4. Restaurant demand is periodic (similar patterns each week, weekend effect), so cyclical encoding lets the model treat Sunday and Monday as adjacent. Friday-only promotion outcome is *not* cyclic in `day_of_week` — Friday is a specific feature value, and you might prefer a one-hot of day-of-week so the model can learn a Friday-specific effect.

5. Overfitting. With 20 points and 11 polynomial coefficients (the degree-10 polynomial), the model has nearly as many parameters as data points and fits the noise rather than the signal. The fix: reduce the degree (try 2, 3, 4 and cross-validate); add L2 regularization (Ridge); get more data.

6. Tree models can in principle express ratios through nested splits, but it's expensive (many splits needed). An explicit ratio feature makes the relationship a single threshold split. The tree no longer has to "discover" the ratio; it uses it directly.

7. There are $\binom{50}{2} = 1225$ pairwise cross-products. Don't use all of them — too many features, likely overfitting, multicollinearity issues. Decide by: (a) domain knowledge (which interactions does the business hypothesise?); (b) EDA (which feature pairs show interaction in stratified analysis?); (c) fit a tree model and look at the interactions it finds; (d) L1-regularized model on the full expansion and let Lasso select.

8. L1 (Lasso) penalises the sum of absolute coefficient values, with a sparsity-inducing geometry (Chapter 20). Most of the 715 coefficients are driven to *exactly* zero; only a small subset of polynomial terms survive. Lasso is effectively doing feature selection within the polynomial expansion.

9. Add the second harmonic: $\sin(2 \cdot 2\pi h / 24), \cos(2 \cdot 2\pi h / 24)$. With both the first and second harmonics, the linear model can fit any two-peak shape. This generalises to a Fourier basis: add as many harmonics as you have peaks per period (up to a frequency limit).

10. Each split in a tree conditions the next splits. A tree that first splits on `age > 50` and then, within the `age > 50` branch, splits on `smoker`, has implicitly learned the interaction effect of age and smoking. Trees discover interactions through hierarchical splits, without you having to write `age * smoker` explicitly.

11. The (sin, cos) encoding gives the tree the right geometry up front. A tree on raw `hour` (0–23) might split at hour ≥ 12, putting hour 23 and hour 0 in opposite branches — incorrect for periodic data. With (sin, cos), the tree splits on the continuous coordinates that already encode the cyclic adjacency. It avoids splits that would split adjacent hours apart.

12. Examples: `days_since_signup = today - signup_date` (tenure), `days_since_last_login = today - last_login_date` (recency), `engagement_ratio = days_active / days_since_signup` (proportion of tenure they've been engaged), `is_new_user = days_since_signup < 30`. Each captures a different facet of the time data.

13. The correlation comes from how $x$ and $x^2$ track each other when $x$ is in a narrow interval. If $x \in [10, 20]$, both $x$ and $x^2$ increase together — Pearson correlation is high. To reduce: (a) center $x$ first ($x - \bar{x}$ before squaring) — this is what `PolynomialFeatures` does optionally with the `interaction_only` and similar flags. (b) Standardise $x$ before generating the polynomial expansion. (c) Use orthogonal polynomials (Hermite, Legendre) instead of raw monomials — these are designed to be uncorrelated by construction.

</details>
