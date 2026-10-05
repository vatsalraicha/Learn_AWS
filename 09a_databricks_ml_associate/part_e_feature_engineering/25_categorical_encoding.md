# Chapter 25 — Categorical Encoding

> **Goal of this chapter:** to teach you how to turn a column of strings (or categorical codes) into numbers that a model can use — and, more importantly, *which* encoding to choose for *which* column. The choice has more consequences than most practitioners realise. A column with three categories needs a different treatment from one with fifty needs a different treatment from one with two million. By the end of this chapter you will know, for any categorical column you encounter, what your default move should be, why, and what its tradeoffs are.

---

## 25.1 Why this is harder than it looks

A model — almost any model — wants a vector of numbers. The training data is a matrix of rows-by-features, every entry a real number. But your data has columns like:

- `state`: one of fifty US state abbreviations.
- `loan_purpose`: one of ten categories (debt consolidation, medical, etc.).
- `home_ownership`: one of three values (own, rent, mortgage).
- `merchant_id`: a unique identifier with two million possible values.

These cannot go into a logistic regression directly. You have to encode them as numbers. The way you encode matters — far more than people initially appreciate. The wrong encoding can:

1. **Introduce false ordering.** Coding `{red=1, green=2, blue=3}` tells the model "blue is bigger than green is bigger than red." A linear model will dutifully learn weights as though those orderings were meaningful. They aren't. The model is now corrupted by a fiction you invented.

2. **Explode dimensionality.** One-hot encoding a column with 50 categories adds 50 columns. One-hot encoding a column with two million categories adds two million columns, almost all zeros. Your design matrix becomes unmanageable.

3. **Leak the target.** Target encoding (replacing each category with the average target value in that category) is powerful but, computed on the full dataset, leaks the target into the feature. Naive implementations of this are a top source of "model AUC of 0.99 on validation, 0.65 in production" disasters.

4. **Misrepresent rare categories.** A category that appears once in the training data and four times in the test data will be a different encoding in each, or — worse — will produce an unknown-category error at inference time.

Categorical encoding is a discipline of matching the *structure of the column* (ordinal? nominal? high-cardinality? rare-tail?) to the *encoding strategy* (ordinal? one-hot? target? hashing?). Get the match right and the model will treat your categories sensibly. Get it wrong and the model will silently underperform.

---

## 25.2 First distinction: ordinal vs. nominal

Before any encoding, ask: **does this column have a natural order?**

- **Ordinal columns** have a meaningful ordering. Examples:
  - `education_level`: `{high_school, bachelor, master, phd}` — there's a clear progression.
  - `customer_tier`: `{bronze, silver, gold, platinum}`.
  - `size`: `{small, medium, large, xl}`.
  - `severity`: `{low, medium, high, critical}`.

- **Nominal columns** have no inherent order. Examples:
  - `state`: Texas is not "greater than" Florida.
  - `loan_purpose`: medical is not "greater than" car.
  - `color`: red is not "greater than" blue.
  - `country`: Canada is not "greater than" Mexico.

The encoding strategy fundamentally differs between the two. For ordinal columns, you can preserve the order with an integer encoding. For nominal columns, you must use an encoding that doesn't imply a false order.

The mistake here — coding nominal data as ordered integers — is so common and so corrosive that we'll spend the next section on it.

---

## 25.3 Ordinal encoding — and when it's the wrong tool

**Ordinal encoding** maps categories to integers in their natural order.

For `education_level`:
```
high_school → 1
bachelor    → 2
master      → 3
phd         → 4
```

For `customer_tier`:
```
bronze   → 1
silver   → 2
gold     → 3
platinum → 4
```

This is the right encoding when the column is *genuinely* ordinal. A linear model can now learn a coefficient $w$ such that the expected default rate (or whatever) changes by $w$ per unit of education. That's a sensible model: more education, lower default rate, monotonically.

### 25.3.1 The catastrophic misuse

Here is the trap. You have a `state` column with fifty US states. You're in a hurry. You do:

```python
df['state_encoded'] = df['state'].map(
    {state: i for i, state in enumerate(df['state'].unique())}
)
```

You've assigned arbitrary integers to states. `Alabama = 0`, `Alaska = 1`, ..., `Wyoming = 49`. You hand this to a linear regression.

The model now believes:
- `state_encoded` has a *linear* relationship to the target.
- The "distance" between Alabama and Wyoming is 49 units.
- The "distance" between Alabama and Alaska is 1 unit.

These are fictions. They're worse than fictions — they're fictions the model will *learn from*. The model will commit to a single slope coefficient that has to compromise between every state, when in reality each state has its own arbitrary effect on the target.

What you've done is mathematically equivalent to telling the model "default rate is a linear function of how alphabetically late the state name is." It's not. The model fits poorly. You blame the model.

### 25.3.2 Tree models and ordinal encoding

There's one important exception. Tree-based models (decision trees, random forests, gradient-boosted trees) do not assume linearity in their features. A tree can split `state_encoded < 12.5` and `state_encoded ≥ 12.5`, and then within each branch split again. With enough depth, a tree can effectively learn an arbitrary partition of integer-encoded categories.

So ordinal-encoded *nominal* features can work fine in tree models. Not because the ordering becomes meaningful, but because the tree is flexible enough to ignore it. You'll see this in practice — XGBoost trained on label-encoded categorical features often works as well as XGBoost trained on one-hot.

**However**: even for tree models, ordinal encoding of a high-cardinality column is suboptimal because the tree has to spend many splits to carve up the integer range. There are better encodings (LightGBM and CatBoost have native categorical handling that we'll mention below).

The takeaway: for ordinal data, ordinal encoding is correct. For nominal data, ordinal encoding is *only* OK in tree models, and even then it's not the best choice.

---

## 25.4 One-hot encoding (OHE)

For nominal columns with low or moderate cardinality, the workhorse encoding is **one-hot**.

The idea: for a column with $k$ categories, create $k$ new binary columns, each indicating membership in one category.

For a column `color` with values `{red, green, blue}`:

| color   | →  | color_red | color_green | color_blue |
|---------|----|-----------|-------------|------------|
| red     |    | 1         | 0           | 0          |
| blue    |    | 0         | 0           | 1          |
| green   |    | 0         | 1           | 0          |
| red     |    | 1         | 0           | 0          |
| blue    |    | 0         | 0           | 1          |

Each row has exactly one `1` and $k - 1$ zeros across the new columns. The model can now learn a separate weight for each category — the weight for `color_red` captures the effect of being red, the weight for `color_green` captures the effect of being green. No false ordering is imposed.

### 25.4.1 The dummy variable trap

For linear models specifically, there is one subtlety. The $k$ one-hot columns are *perfectly collinear*: knowing the value of $k - 1$ of them uniquely determines the $k$-th (the columns sum to 1 for every row). This collinearity makes the design matrix non-invertible — $(X^T X)$ is singular — and ordinary least-squares (Chapter 31) cannot find a unique solution.

The fix is to drop one column: encode `k-1` indicator variables instead of `k`. The dropped category becomes the *reference*: its effect is absorbed into the intercept, and the remaining $k-1$ coefficients represent the effect of each non-reference category *relative to* the reference.

```python
pd.get_dummies(df['color'], drop_first=True)
# Returns columns: color_green, color_blue
# Red is now the reference: a row of all-zeros means "red"
```

For tree models and most regularized linear models, the drop is not strictly necessary — regularization (Chapter 20) makes the singularity go away — but it is good practice and reduces the column count by one per categorical.

### 25.4.2 Why OHE doesn't scale

One-hot encoding produces $k$ columns per categorical with $k$ categories. The cost in memory and compute scales as:

- **Memory:** if your dataset has $n$ rows, the encoded matrix is $n \times k$, mostly zeros. Sparse representations help, but at some point even sparse representations break down.
- **Model parameters:** every additional column is an additional weight (and a regularization-cost-budget chunk) the model has to fit. With $k$ categories and $n$ rows, you need $n \gg k$ for the model to estimate each category's effect reliably.
- **Rare categories.** A category with only 3 rows in training will be a feature with a poorly-estimated coefficient. The model can't tell whether the coefficient should be large or whether it's just noise.

**Concretely:**

- `home_ownership` (3 categories) → 2 new columns. Fine.
- `state` (50 categories) → 49 new columns. Fine.
- `loan_purpose` (10 categories) → 9 new columns. Fine.
- `merchant_category` (~1,000 categories) → 999 new columns. Borderline. The model has to estimate 999 coefficients, many on rare categories.
- `zip_code` (~40,000 US zips) → 39,999 new columns. Painful. Most zips will have very few rows.
- `merchant_id` (2,000,000) → 1,999,999 new columns. Hopeless.

There's no fixed cutoff, but the rule of thumb is: **OHE is comfortable up to maybe 100 categories, gets uncomfortable above that, and is wrong above ~1,000.**

### 25.4.3 The `handle_unknown` problem

At inference time, you may see a category that wasn't in the training set. Your encoder fit on training has no column for it. What to do?

The conservative answer is to encode all unknown categories as the all-zeros vector — equivalent to "none of the known categories." This is what scikit-learn's `OneHotEncoder(handle_unknown='ignore')` does. Some practitioners create an explicit `other` category instead.

The right answer depends on the application, but you must *decide* — silent crashes on unknown categories are the most common production failure mode of categorical pipelines.

---

## 25.5 Target encoding (mean encoding)

For high-cardinality nominal columns where OHE is unworkable, **target encoding** is the workhorse.

The idea: replace each category with the mean of the target variable for rows in that category.

For a column `state` and a binary target `default`:

```python
state_default_rate = df.groupby('state')['default'].mean()
# {
#   'AL': 0.11,
#   'AK': 0.07,
#   'AZ': 0.09,
#   ...
#   'WY': 0.06
# }
df['state_encoded'] = df['state'].map(state_default_rate)
```

A column with 50 states becomes a single numeric column where each row's value is the empirical default rate for that state.

### 25.5.1 Why it works

Target encoding captures, in one number, what a one-hot encoding represents in $k$ columns: the empirical association between each category and the target. For a linear model, this gives a single coefficient that scales the per-category mean into a prediction. For tree models, the encoded column is now easy to split on — categories with similar default rates end up at similar values and the tree partitions efficiently.

The compression is enormous: 50,000 zip codes become one column. The model handles them as smoothly as any other numeric feature.

### 25.5.2 The leakage catastrophe

Here is the trap that ruins beginners' models and the reason I led with the leakage warning. If you compute target encoding on the *entire* dataset and then split into train/test:

```python
# WRONG
state_default_rate = df.groupby('state')['default'].mean()
df['state_encoded'] = df['state'].map(state_default_rate)
X_train, X_test = train_test_split(df, test_size=0.2)
```

The encoding for state `TX` was computed using *every* TX row in the dataset — including the test set rows. The test set's target values have leaked, through the encoding, into the training set. The model trained on the leaked encoding will look spectacular in cross-validation and crater in production.

Worse, the leakage is *within-row* if you encode each row with the mean of its own category including itself. For a category with just one row in training, the encoding for that row is exactly its own target — and you've handed the answer to the model.

**The right pattern:**

```python
X_train, X_test = train_test_split(df, test_size=0.2)
state_default_rate = X_train.groupby('state')['default'].mean()
X_train['state_encoded'] = X_train['state'].map(state_default_rate)
X_test['state_encoded']  = X_test['state'].map(state_default_rate)
```

The encoding is computed on training only. The test set looks up the encodings but does not contribute to them.

And for cross-validation, the encoding must be re-fit on each fold's training subset — same pattern as imputation in Chapter 24. Wrap target encoding inside a pipeline stage that respects the fold structure, or use a library that handles this (sklearn's `TargetEncoder`, added in 1.3, does this automatically with `cv=5`).

### 25.5.3 The within-row leakage refinement

Even with proper train/test separation, there's a subtler within-training leakage. When you compute the encoding for category `TX` from training rows where the state is TX, *each row's own target* is included in the encoding it sees. A row in TX with default=1 contributes to making TX's encoding higher, and then that row sees a high TX encoding — it's effectively been told its own answer.

For high-volume categories (1000 TX rows), one row's contribution to the encoding is 0.1%, so this leakage is negligible. For rare categories (1 TX row), this leakage is total — the encoding is exactly that row's target.

The fix is **leave-one-out (LOO) encoding**: for each row, compute the category encoding excluding that row's own target. Sklearn's `TargetEncoder` and the `category_encoders` library's `LeaveOneOutEncoder` implement this.

### 25.5.4 Smoothing for rare categories

A category with two training rows where one defaulted has an empirical default rate of 50%. Is that real signal, or noise? Almost certainly noise — you cannot estimate a 50% rate from two observations.

**Smoothing** addresses this. We blend the per-category mean with the *global* mean, weighted by how much data each is based on:

$$
\hat{p}_c = \frac{n_c \bar{y}_c + \alpha \bar{y}_{\text{global}}}{n_c + \alpha}
$$

Where:
- $n_c$ is the count of rows in category $c$.
- $\bar{y}_c$ is the mean target in category $c$.
- $\bar{y}_{\text{global}}$ is the overall mean target.
- $\alpha$ is a smoothing parameter (the "prior weight"). A typical value is 10.

When $n_c$ is large, the per-category mean dominates. When $n_c$ is small, the encoding is pulled toward the global mean — recognising that we don't have enough data to estimate the category-specific effect.

This is Bayesian shrinkage: we have a prior belief that each category's rate is the global rate, and the data updates that belief proportionally to how much data each category has.

**Worked example.** Global default rate is 9%. State `TX` has 1,000 rows with default rate 8%. State `WY` has 5 rows with default rate 20% (1 default out of 5).

Without smoothing: TX → 0.08, WY → 0.20.

With smoothing ($\alpha = 10$):
- TX: $(1000 \cdot 0.08 + 10 \cdot 0.09) / (1000 + 10) = (80 + 0.9) / 1010 = 0.0801$. Basically unchanged.
- WY: $(5 \cdot 0.20 + 10 \cdot 0.09) / (5 + 10) = (1.0 + 0.9) / 15 = 0.127$. Pulled hard toward the global mean.

The model now correctly understands that WY's 20% is noisy, not real signal. Without smoothing, WY would be a feature value of 0.20 that the model takes seriously and that misleads it.

---

## 25.6 Frequency encoding

A cheap variant: replace each category with its count (or frequency) in the training set.

```python
freq = df['state'].value_counts(normalize=True)
df['state_freq'] = df['state'].map(freq)
```

For a state with 1,000 rows out of 100,000, the encoding is 0.01.

**When useful.** When the *prevalence* of a category is itself informative. Common categories tend to be different from rare ones in many systematic ways. For instance, a `merchant_id` that appears 50,000 times in transaction data is a large merchant (likely a chain); one that appears once is a tiny merchant or a one-off transaction. The prevalence captures something real.

**When not useful.** When prevalence is unrelated to the target. Frequency encoding is a weaker signal than target encoding and shouldn't be your first move when target encoding is feasible.

**A nice property:** frequency encoding leaks nothing about the target. You can compute it on the full dataset (within reason) without any target-leakage concern. The only leakage worry is if test-set frequencies differ from train-set frequencies, which usually they don't to any consequential degree.

It's also commonly used *alongside* target encoding — you give the model both the category's mean target and its frequency, and let the model decide which to weight.

---

## 25.7 The hashing trick

For very high cardinality (think: hundreds of thousands or millions of categories — `merchant_id`, `url`, `user_agent_string`), even target encoding can be impractical. You need to know every category's mean to do the encoding, and storing a dictionary of millions of entries is feasible but slow at inference.

The **hashing trick** sidesteps this. Pick a fixed number of buckets $B$ (say, $B = 2^{20}$). Hash each category to one of the $B$ buckets via a fast hash function modulo $B$. Encode the category as a one-hot of the bucket.

```python
def hash_encode(category, n_buckets=2**20):
    return hash(category) % n_buckets
```

A column with 2,000,000 categories now maps into 1,048,576 buckets. Roughly 2 categories per bucket on average — **collisions**.

**What collisions cost.** Two unrelated categories that hash to the same bucket are *indistinguishable* to the model. If `merchant_id_abc` and `merchant_id_xyz` both map to bucket 7,142, the model sees both as the same feature. Their effects are pooled.

**Why this is OK in practice.** Most high-cardinality categories carry very little information per category. A single user-agent string out of millions doesn't tell the model much that the bucket's aggregate doesn't capture. The signal lives at the bucket level, and collisions average out.

**Implementation.** scikit-learn's `FeatureHasher`. Spark ML's `HashingTF` does the same trick for text (treating each token as a category).

The hashing trick is the standard tool when (a) cardinality is in the millions and (b) you don't have the infrastructure to compute target encodings reliably. It's used heavily in online advertising (where ad IDs and user IDs are in the billions) and in raw-text features.

---

## 25.8 Native categorical handling: a brief mention

Some modern ML libraries handle categorical features natively, without requiring you to encode them upfront:

- **LightGBM** has `categorical_feature` parameter. The library uses a histogram-based algorithm that finds the best partition of categories at each split, without one-hot encoding. Very efficient for high-cardinality categorical features.
- **CatBoost** (the name comes from "categorical boosting") was designed around clever target-encoding-with-ordering schemes that prevent leakage. It's often the strongest tabular model out of the box on categorical-heavy data.
- **XGBoost** added `enable_categorical=True` in recent versions, using a similar histogram approach to LightGBM.
- **HistGradientBoostingClassifier / Regressor** in scikit-learn also supports native categorical features.

For Spark ML, this native support is not (as of writing) built in — you encode upstream of the model. PySpark ML algorithms like `RandomForestClassifier` and `GBTClassifier` operate on numeric vectors only.

If you're free to choose the library and your problem is heavy on categoricals, native handling is often the best choice. For the Databricks ML Associate exam, expect Spark ML's API where you encode explicitly upstream of the model (Chapter 63).

---

## 25.9 The decision tree for choosing an encoding

Putting it all together, here is the practical decision logic:

```
Is the column ordinal (has a natural order)?
├── YES → Ordinal encoding. Keep the order. Done.
└── NO  → It's nominal.
         │
         ├── How many categories?
         │
         ├── ≤ ~10 → One-hot encoding. Always works.
         │
         ├── 10–100 → One-hot OR target encoding.
         │            OHE if the model is regularized (e.g., logistic regression with L2).
         │            Target encoding if you want fewer columns.
         │
         ├── 100–1000 → Target encoding (with smoothing). 
         │              Or model-native (LightGBM categorical_feature).
         │              OHE is starting to be impractical.
         │
         ├── 1000–100,000 → Target encoding with smoothing.
         │                   Or hashing trick if you also want feature crosses.
         │
         └── > 100,000 → Hashing trick. Or model-native (CatBoost). 
                          Or embeddings (out of scope, neural-net territory).
```

A few addenda:

- **Always add a `missing` category** for categorical columns that can be null. Don't let nulls fall through silently.
- **Always have a plan for unknown categories at inference time.** The `handle_unknown='ignore'` flag in sklearn's `OneHotEncoder`, or a default-to-global-mean for `TargetEncoder`. Don't crash.
- **Frequency encoding is a cheap alternative or complement.** Use it alongside other encodings, especially for high-cardinality columns where frequency is itself informative.

---

## 25.10 Worked numerical example

Let's encode `loan_purpose` (10 categories) and `state` (50 categories) for a 100,000-row dataset.

**Step 1: inspect.**

```python
df['loan_purpose'].value_counts()
# debt_consolidation    42000
# credit_card           18000
# home_improvement       9000
# other                  8000
# medical                7000
# small_business         6000
# car                    4000
# wedding                3000
# moving                 2000
# vacation               1000

df['state'].value_counts().head()
# CA   12000
# TX    9500
# NY    8200
# FL    7800
# IL    5100
df['state'].value_counts().tail()
# WY    280
# VT    260
# AK    240
# ND    210
# SD    200
```

`loan_purpose` is moderate cardinality; OHE is fine. `state` is 50 categories, similar — OHE is fine, but target encoding gives one column instead of 49.

**Step 2: OHE `loan_purpose`.**

```python
ohe = OneHotEncoder(drop='first', handle_unknown='ignore', sparse_output=False)
ohe.fit(X_train[['loan_purpose']])
X_train_lp = ohe.transform(X_train[['loan_purpose']])
X_test_lp = ohe.transform(X_test[['loan_purpose']])
# 9 new columns
```

**Step 3: target-encode `state` with smoothing.**

Let's say `default` is 9% overall.

```python
alpha = 50
global_mean = X_train['default'].mean()
state_stats = X_train.groupby('state')['default'].agg(['mean', 'count'])
state_stats['smoothed'] = (
    state_stats['count'] * state_stats['mean'] + alpha * global_mean
) / (state_stats['count'] + alpha)
```

For CA (12,000 rows, default rate 8.5%):
$$\hat{p}_{CA} = \frac{12000 \cdot 0.085 + 50 \cdot 0.09}{12000 + 50} = \frac{1020 + 4.5}{12050} = 0.0850$$
Basically unchanged — lots of data.

For SD (200 rows, default rate 14%, say):
$$\hat{p}_{SD} = \frac{200 \cdot 0.14 + 50 \cdot 0.09}{200 + 50} = \frac{28 + 4.5}{250} = 0.130$$
Pulled toward the global mean. Reasonable: 200 rows isn't quite enough to commit fully to "SD has a 14% default rate."

**Step 4: apply.**

```python
X_train['state_te'] = X_train['state'].map(state_stats['smoothed'])
X_test['state_te'] = X_test['state'].map(state_stats['smoothed']).fillna(global_mean)
# fillna handles unseen states in test
```

**Step 5: model.**

A logistic regression sees `loan_purpose` as 9 binary columns and `state` as a single numeric column. The 49-column savings from target encoding lets us avoid coefficient-budget pressure on `state`, which would have been ~50 columns of OHE. The model fits more cleanly.

---

## 25.11 Code: PySpark and scikit-learn essentials

In scikit-learn:

```python
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, TargetEncoder

ohe = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
ord_enc = OrdinalEncoder(categories=[['high_school', 'bachelor', 'master', 'phd']])
te = TargetEncoder(smooth='auto', cv=5)  # built-in CV-fold leakage prevention

# Use inside a ColumnTransformer / Pipeline:
from sklearn.compose import ColumnTransformer
preprocess = ColumnTransformer([
    ('ohe', OneHotEncoder(handle_unknown='ignore'), ['loan_purpose', 'home_ownership']),
    ('ord', OrdinalEncoder(categories=[['high_school','bachelor','master','phd']]),
            ['education']),
    ('te',  TargetEncoder(),                       ['state', 'zip_code']),
])
```

For pandas one-liners:

```python
pd.get_dummies(df, columns=['loan_purpose'], drop_first=True)
```

In PySpark ML:

```python
from pyspark.ml.feature import StringIndexer, OneHotEncoder

# Stage 1: index strings to integers
indexer = StringIndexer(inputCol='state', outputCol='state_idx', 
                        handleInvalid='keep')
# Stage 2: one-hot encode the integer index
ohe = OneHotEncoder(inputCol='state_idx', outputCol='state_ohe',
                    dropLast=True)

# Inside a Pipeline (Chapter 62):
from pyspark.ml import Pipeline
pipeline = Pipeline(stages=[indexer, ohe, ...])
```

Note the Spark idiom of two stages: `StringIndexer` (string → integer) followed by `OneHotEncoder` (integer → one-hot vector). Spark doesn't have a built-in target encoder; you implement it yourself with `groupBy().agg()` and a join.

The `category_encoders` library on PyPI offers a broader set: `BinaryEncoder`, `HelmertEncoder`, `BackwardDifferenceEncoder`, `CatBoostEncoder` (an off-the-shelf CV-respecting target encoder), `JamesSteinEncoder`. For most exam-relevant work, sklearn's three (OHE, ordinal, target) cover the territory.

---

## 25.12 What this builds on / where it returns

**Builds on:**

- Chapter 23 (EDA): you identify cardinality and class distribution during EDA — those determine the encoding choice.
- Chapter 24 (missing): nulls in categorical columns are themselves a category; handle them explicitly.
- Chapter 22 (CV/leakage): target encoding is one of the most common leakage paths; the CV-fold discipline matters here.

**Returns in:**

- Chapter 31 (linear regression): the dummy variable trap and reference categories.
- Chapter 33–36 (trees): tree-native handling and why OHE is less essential for trees.
- Chapter 62–63 (Spark Pipelines / Transformers): how Spark's `StringIndexer` + `OneHotEncoder` chain works.
- Chapter 71 (Feature Store): consistent encoding between training and serving — the right place to register encoding artifacts.

---

## 25.13 Exercises

1. **Ordinal or nominal?** For each column, say which:
   (a) `payment_status`: {`current`, `30_days_late`, `60_days_late`, `90_days_late`, `charged_off`}.
   (b) `merchant_category_code`: a four-digit code identifying merchant type.
   (c) `account_type`: {`checking`, `savings`, `money_market`}.
   (d) `risk_grade`: {`A`, `B`, `C`, `D`, `E`, `F`, `G`}, where A is best.

2. **The OHE explosion.** Your `zip_code` column has 40,000 unique values across 100,000 rows. You one-hot encode. Sketch the resulting design matrix's size in MB if you store densely (assume 8 bytes per number). Same calculation in sparse format (1 nonzero per row).

3. **Target encoding leakage.** Why is fitting the encoding on the full dataset, then splitting, a leak — even if the test set's *categories* are also present in the training set?

4. **Smoothing math.** For a category with $n_c = 3$ rows and an empirical rate of $\bar{y}_c = 0.33$, and a global rate of $\bar{y}_{\text{global}} = 0.10$ with smoothing $\alpha = 10$, compute the smoothed encoding. Is it closer to 0.10 or to 0.33? Why is that the right behavior?

5. **The hashing collision.** Two unrelated merchant IDs hash to the same bucket. What does the model see? When is this OK, and when is it a problem?

6. **Tree models and ordinal encoding.** Why is integer-encoding a 50-category nominal column "OK" for a random forest but "not OK" for a logistic regression?

7. **Reference categories.** In linear regression with OHE, you drop the reference category. The dropped category's effect ends up in the intercept. Show by argument what happens if you don't drop anything.

8. **The unknown category.** Your trained encoder has not seen state `"PR"` (Puerto Rico) during training. At inference time you encounter it. Walk through what each of OHE-with-ignore, target-encoded, and hash-encoded encoders will do.

9. **Frequency encoding for a target-uncorrelated column.** A column's frequency has essentially no relationship to the target. Would frequency encoding hurt the model? Help it? Be neutral?

10. **High-cardinality, regulated industry.** You're at a bank. You have a `customer_id` column with 5 million unique customers and you want to use it in a credit risk model. Target encoding on the raw IDs is dangerous in several ways. Name three.

11. **Within-row leakage.** A category with 1 row in training is target-encoded. What is the encoding for that row, and what is the model learning?

12. **OHE vs. target encoding on the same column.** For a 100-category column, you try both encodings in a Random Forest. OHE gives slightly higher training accuracy; target encoding gives slightly higher CV-validation accuracy. Which would you ship and why?

<details>
<summary>Answers</summary>

1. (a) Ordinal — there's a clear progression of severity. (b) Nominal — MCC codes are arbitrary identifiers. (c) Nominal. (d) Ordinal — explicit grade order.

2. Dense: $100{,}000 \times 40{,}000 \times 8\text{ bytes} = 32 \cdot 10^9 = 32\text{ GB}$. Sparse: roughly 100,000 rows × 1 nonzero × ~16 bytes per (row, col, value) entry = 1.6 MB. Sparse storage is ~20,000× smaller. This is why every serious ML library has sparse vector support.

3. Even if categories are present in both, the *encoded value for each category* is computed using the test rows' target values. The test rows have leaked their information into the per-category mean, which then appears as a feature value the model trains on. The leak isn't in *which* categories are present; it's in *what value they encode to*.

4. $\hat{p} = (3 \cdot 0.33 + 10 \cdot 0.10) / (3 + 10) = (0.99 + 1.00) / 13 = 0.153$. Closer to 0.10 than to 0.33 because $\alpha = 10$ dominates $n_c = 3$. That's right: with only 3 rows we cannot reliably estimate a category-specific rate, and shrinking toward the global rate is honest about our uncertainty.

5. The model sees both as the same feature (bucket value). OK when the categories carry mostly aggregate-level signal (e.g., user-agent strings — a tiny per-string effect, but the bucket's aggregate captures the device type roughly). A problem when individual categories carry strong, distinct signal that you want the model to separate — e.g., two large merchants with very different default rates colliding into one bucket erases that distinction.

6. Linear models impose a *linear* relationship between the feature and the target. Integer-encoded nominal data forces the model to learn a single slope across the integer encoding, which has no meaningful order. Random forests do not assume linearity: they make threshold splits and can effectively partition the integer space arbitrarily, recovering per-category effects through enough splits. The encoding is suboptimal but not pathological.

7. The $k$ one-hot columns are perfectly collinear (they sum to 1 for every row). The design matrix is rank-deficient. OLS cannot find a unique solution — $X^T X$ is singular. With regularization (L1 or L2), the solution becomes well-defined again but you've wasted a degree of freedom.

8. OHE-with-ignore: returns all zeros for the PR row — effectively, no category. The model interprets this as "none of the known categories" — predictions are based on the intercept plus other features. Target-encoded: returns NaN (no encoding learned) — must be handled (e.g., fill with global mean). Hash-encoded: hashes "PR" to whatever bucket it falls into, like any other category. No special handling needed (which is one of hashing's nicer properties).

9. Neutral, in expectation. A feature uncorrelated with the target contributes no signal, but it also doesn't hurt — regularization will shrink its coefficient toward zero (in a linear model) or it will simply not be split on (in a tree). The cost is one extra column in the design matrix and a small amount of compute.

10. (a) Customer ID is essentially a unique identifier — target encoding it with one row per customer leaks each customer's own target into their own encoding (perfectly, if not leave-one-out). (b) Even with LOO, you're effectively memorising per-customer rates, which doesn't generalise to *new* customers (everyone has never been seen before). (c) Regulatory: using a customer ID as a feature creates a discriminatory model where the model bases decisions on *who* the customer is, not on their behavior — likely illegal under fair lending laws. Customer IDs almost never belong in models as direct features.

11. The encoding for that row is exactly its own target (assuming no LOO and no smoothing). The "feature" is a perfect predictor of the target — for that row. The model learns that this particular encoding value perfectly predicts the target, which generalises to nothing.

12. Ship target encoding. Higher CV-validation accuracy is what predicts production performance; higher *training* accuracy is consistent with overfitting (Chapter 19). The OHE model is using its many columns to memorise per-category training noise, while the target encoded model has fewer parameters and a more honest signal. CV-validation is the metric to trust.

</details>
