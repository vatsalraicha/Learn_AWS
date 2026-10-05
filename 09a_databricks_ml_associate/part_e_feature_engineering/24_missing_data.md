# Chapter 24 — Missing Data: MCAR, MAR, MNAR, and What to Do

> **Goal of this chapter:** to teach you to think about missing data as a *first-class* part of the modeling problem rather than a nuisance to dispose of with a one-liner. By the end of the chapter you'll be able to (a) classify a missing-data situation as MCAR, MAR, or MNAR; (b) choose an imputation strategy that matches the mechanism; (c) avoid the most common imputation-related leakage bugs; and (d) recognise when missingness itself is a feature.

---

## 24.1 The wrong answer everyone reaches for first

You are mid-EDA on the `loans.csv` dataset from Chapter 23. You discover that the `employment_years` column is 28% null. You have a meeting in twenty minutes and you need to keep moving. The wrong answer — the one that almost everyone reaches for first, and that costs more than they realise — is one of these three things:

1. **Drop the rows.** `df = df.dropna(subset=['employment_years'])`. The dataset went from 300,000 to 216,000 rows; you've thrown away 28% of your data, and you've thrown it away *non-randomly* — you kept exactly the rows where the column was populated, which may be a different population from your full dataset.
2. **Drop the column.** `df = df.drop(columns=['employment_years'])`. You've lost a potentially informative feature for everyone, just because some people don't have it.
3. **Fill with the mean.** `df['employment_years'] = df['employment_years'].fillna(df['employment_years'].mean())`. You've made 84,000 rows have *the same value* — the dataset's average employment years — for a feature that is fundamentally about employment history. The model can now see that value and not know whether it's "this person has the average employment history" or "this person didn't tell us." Worse, you've reduced the column's variance, which biases any linear model's coefficient toward zero.

Each of those three reflexes is *sometimes* the right move. The point of this chapter is that you cannot decide which is right without first asking: *why is the data missing?*

---

## 24.2 The three mechanisms: MCAR, MAR, MNAR

In 1976, the statistician Donald Rubin formalised a taxonomy that is still the foundation of every serious treatment of missing data. The taxonomy is about the *mechanism* generating missingness — the process that decided whether each value would be observed or hidden.

Let $X$ denote the true (complete, hypothetical) data, $X_\text{obs}$ the observed portion, $X_\text{miss}$ the missing portion, and $M$ a binary indicator vector that flags which entries are missing. The three mechanisms are:

### 24.2.1 MCAR — Missing Completely At Random

Missingness is independent of *everything* — the observed data, the missing data, and any feature in the dataset.

$$P(M \mid X_\text{obs}, X_\text{miss}) = P(M)$$

In words: whether a value is missing has nothing to do with what the value is or with any other variable. It's a coin flip.

**Example.** A laboratory machine randomly drops 1% of measurements due to read errors. The drops are uncorrelated with the patient, the sample, or the value itself.

**Why it matters.** If your data is truly MCAR, the observed data is a *random subsample* of the complete data. Statistical estimates computed on the observed data are unbiased. You can drop the rows, drop the column, or impute with any reasonable strategy, and your conclusions will be approximately correct.

**Why it almost never happens.** Real missing data is almost never MCAR. Surveys have nonresponse correlated with demographics. Sensors fail more in heat. Forms have skipped fields that correlate with what was being asked. The hypothesis "the missing data is independent of everything else" is almost always wrong, and treating non-MCAR data as MCAR introduces silent bias.

You can *test* whether MCAR is plausible. Little's MCAR test is one option. A more practical move is what we'll describe in §24.3: train a classifier to predict $M$ from $X_\text{obs}$. If you can predict missingness from the observed features, you have at least MAR, not MCAR.

### 24.2.2 MAR — Missing At Random

Missingness depends on the *observed* data but not, conditional on it, on the missing value itself.

$$P(M \mid X_\text{obs}, X_\text{miss}) = P(M \mid X_\text{obs})$$

In words: knowing the *other* features (the observed ones) tells you whether a value is missing; knowing the *missing value itself* adds no further information.

**Example.** Elderly patients are more likely to refuse a blood pressure test (because the procedure is uncomfortable for them). Missingness depends on `age` (observed) but not, conditional on age, on the missing blood-pressure value. Among 80-year-olds, both healthy and unhealthy ones refuse at the same rate.

**Why it matters.** MAR is the regime under which most modern imputation methods are *unbiased*. If you can model missingness as a function of the observed features, you can impute the missing values using those features and recover unbiased estimates. Methods like MICE (multiple imputation by chained equations) and KNN imputation rely on MAR.

**The naming is unfortunate.** "MAR" sounds like it means "random missingness," but it actually means "random *given the observed features*." The fully-random case is MCAR; MAR is a weaker, more realistic condition.

**Diagnosing MAR.** If your missingness predictor (§24.3) achieves an AUC clearly above 0.5 using only observed features, you have MAR. If you cannot predict missingness from the observed features, you might still have MNAR — see below.

### 24.2.3 MNAR — Missing Not At Random

Missingness depends on the *missing value itself*, even after conditioning on the observed features.

$$P(M \mid X_\text{obs}, X_\text{miss}) \neq P(M \mid X_\text{obs})$$

In words: the very thing you're missing influences whether it's missing.

**Example.** Very high-income people decline to report their income on a survey, *because* their income is high. Even controlling for everything else you can see (age, occupation, location), high earners are systematically more likely to skip the question. The missingness is correlated with the missing value.

**Why it matters.** MNAR is the hardest case. You cannot, in general, recover unbiased estimates from the observed data alone, no matter how clever your imputation. The information you need is in the rows where the data is missing — and that's exactly the information you don't have.

**Diagnosing MNAR.** This is the hard part. Strictly, you cannot diagnose MNAR from data alone — by definition, the data you'd need is missing. You diagnose MNAR through **domain knowledge**: knowing that high earners decline to answer, or that depressed patients drop out of psychiatric studies, or that defective products skip QA inspection. The data alone never tells you "this is MNAR"; the world tells you.

**What to do.** Several options, none entirely satisfying:

1. **Selection models** that jointly model the data and the missingness mechanism. Requires assumptions you cannot fully verify.
2. **Sensitivity analysis:** impute under multiple plausible assumptions about the missing-value distribution and see how much your conclusions change. If they're robust, you're probably OK; if they swing wildly, you have a problem.
3. **Get the missing data.** Sometimes this is genuinely possible — return to the data source, recontact survey respondents, instrument the sensor differently. If feasible, this is the best fix.
4. **Acknowledge the bias.** If you can't fix it, at minimum document that the estimates are biased and in which direction. This is what serious statisticians do; it's what most ML practitioners do not.

### 24.2.4 A picture of the three mechanisms

Imagine `income` and a missing-data indicator $M$ for `income`.

- **MCAR:** the dots that are missing are scattered uniformly across the entire `income` distribution. A random sample.
- **MAR:** the dots that are missing are concentrated among certain values of *other* observed variables — e.g., among older people. Within "older people," the missingness is uncorrelated with income.
- **MNAR:** the dots that are missing are concentrated at the *high end* of the income distribution. The missingness depends on income itself.

```
         MCAR:    o x o x o o x o o x o x o o x      (missing scattered)
         MAR:     o o x x x o o o o o o o o o o      (missing in one subgroup)
         MNAR:    o o o o o o o o o o o x x x x      (missing at one end)

         o = observed, x = missing
         x-axis = income, low → high
```

---

## 24.3 Diagnosing the mechanism in practice

You have a dataset with missing values. How do you decide which of the three you're dealing with?

### 24.3.1 The missingness classifier

Create a binary column `is_missing_income = df['income'].isnull()`. Drop `income` itself. Train a classifier (any will do — random forest is a good default) to predict `is_missing_income` from the other columns.

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score

mask = df['income'].isnull()
X = df.drop(columns=['income', 'default'])
X = pd.get_dummies(X)  # crude encoding for diagnostic purposes
score = cross_val_score(RandomForestClassifier(n_estimators=100),
                        X, mask, cv=5, scoring='roc_auc').mean()
print(f"Missingness-prediction AUC: {score:.3f}")
```

Interpret the result:

- **AUC ≈ 0.5.** You cannot predict missingness from the observed features. *Either* MCAR *or* MNAR. Domain knowledge has to break the tie.
- **AUC > 0.5 (say, 0.7).** Missingness is predictable from observed features. Likely MAR. You can use those features to impute.
- **AUC ≈ 1.0.** Missingness is *deterministically* predicted by some observed feature. Often a sign that missingness is structural — e.g., `recovery_amount` is null exactly when `default = 0`. The column has a deterministic meaning, not a random one, and the right action is usually to encode the structure (e.g., `was_default_recovered` boolean) rather than impute.

### 24.3.2 Cross-tabs

For categorical missingness, a simple cross-tabulation often reveals the mechanism. Suppose 20% of `income` is missing. We tabulate the missingness rate by `employment_status`:

```
employment_status   missing income %
employed                 5%
self-employed           18%
retired                 45%
student                 38%
unemployed              22%
```

Hugely uneven. The missingness is concentrated among retirees and students — populations that may genuinely lack a single "income" value. MAR is a strong hypothesis. The imputation strategy should use `employment_status` (and probably more) to inform the imputed value.

### 24.3.3 Domain knowledge: the trump card

Statistical diagnostics tell you *something*, but they cannot tell you the difference between MCAR and MNAR (because the missing values themselves are unavailable). The trump card is asking the data owner. *Why* is `income` missing for these rows? "The user clicked through the form without filling it" is MCAR-ish. "Self-employed users see a different form that doesn't have an income field" is MAR. "We hide the income field from users earning above $X to comply with a regulation" is MNAR.

Spending fifteen minutes with the data owner will routinely give you more useful information than a week of statistical analysis. Do this.

---

## 24.4 Strategies for handling missing data

You've diagnosed (or at least hypothesised) the mechanism. Now the action.

### 24.4.1 Listwise deletion (drop the rows)

`df.dropna()` removes any row with any missing value. Equivalent to "complete-case analysis."

**When OK.** MCAR (genuinely), and the fraction missing is small (under ~5%). You lose a bit of data but no bias.

**When dangerous.** Anything not MCAR. You introduce bias proportional to how strongly missingness correlates with anything else. With 28% missing, dropping 28% of rows *and* selectively dropping the rows where (in our `employment_years` example) the borrower is self-employed or retired is exactly the kind of bias that produces a model that fails on those subpopulations in production.

**Special case: missing target.** If $y$ is missing for some rows in training, those rows cannot be used to learn the supervised mapping anyway. Drop them (or use semi-supervised methods, out of scope).

### 24.4.2 Pairwise deletion (drop values, keep the row)

Use each row to the extent you can, ignoring its missing entries. Mainly relevant for computing summary statistics ("compute the correlation between `income` and `loan_amount` using only the rows where *both* are observed"). For ML models, the model needs a complete feature vector, so this doesn't really apply — you have to either drop the row or impute.

### 24.4.3 Mean / median / mode imputation

Fill each missing value with the column's mean (or median, or mode for categoricals).

**Pros.** Trivial. Doesn't lose rows. Each row remains usable.

**Cons.**

1. *Reduces variance.* You've concentrated mass on one value. Linear-model coefficients get biased toward zero.
2. *Distorts the distribution.* The histogram now has a giant spike at the mean.
3. *Loses signal.* If missingness was MAR — predictable from other features — you've thrown away that signal by imputing a constant.
4. *Doesn't tell the model anything happened.* The imputed values look identical to genuine values.

When OK: MCAR, small fraction missing, you don't care about variance estimates. Or as a baseline you'll improve on.

### 24.4.4 The missingness indicator (always do this)

Whatever imputation you do, *also* add a binary column flagging whether the value was originally missing.

```python
df['employment_years_was_missing'] = df['employment_years'].isnull().astype(int)
df['employment_years'] = df['employment_years'].fillna(df['employment_years'].median())
```

The model can now use both the imputed value *and* the fact of imputation. If "was missing" itself carries signal (and it often does — in our loans example, missing `employment_years` correlates with being self-employed, which correlates with default risk), the model can learn from it directly.

This trick costs you one column and a few CPU cycles. The upside is large. I do it by reflex on any column with non-trivial missingness.

### 24.4.5 KNN imputation

For each row with a missing value, find the $k$ nearest non-missing rows (in the space of the other features), and impute with the mean (or median, or weighted average) of their values.

**Intuition.** If a 35-year-old employed Texan with a $50K loan is missing `income`, find the most similar 35-year-old employed Texans with $50K loans whose income *is* observed, and average their incomes.

**Pros.** Preserves local structure. Doesn't crush the variance the way mean imputation does. Reasonable under MAR.

**Cons.** Slow on large datasets (every imputation requires a nearest-neighbour search). Requires defining "nearest" — typically a Euclidean distance on standardised numeric features, which means you need to scale first (Chapter 26), and categorical features need encoding (Chapter 25). Sensitive to the choice of $k$.

### 24.4.6 Model-based imputation: MICE

MICE — Multiple Imputation by Chained Equations — is the heavyweight champion of imputation when you take it seriously.

The idea, sketched:

1. Initial-fill all missing values with the column means.
2. For each column $X_j$ with missing values, in order:
   a. Treat the rows where $X_j$ was originally observed as a "training set."
   b. Fit a regression model predicting $X_j$ from all the other columns.
   c. Use that model to *re-predict* the originally-missing values in $X_j$.
3. Cycle through all columns multiple times until imputations stabilise.

The "multiple" part comes from running the whole procedure several times with stochasticity, yielding multiple imputed datasets that capture the uncertainty about the imputed values. For ML, we usually use a single MICE run (sklearn's `IterativeImputer`) and ignore the multiple-imputation machinery.

**Pros.** Generally produces the best imputations under MAR. Handles complex dependencies between columns. The implementation in sklearn is one line of code.

**Cons.** Slow (multiple passes, each fitting many regressions). Iterative, so can fail to converge in pathological cases. Sensitive to the choice of regression model used for each column.

### 24.4.7 Domain-specific imputation

Sometimes you know what missing means.

- `transaction_count_last_30d` is null because the user has no transactions in the last 30 days. *The right "imputation" is 0*, not the mean.
- `is_phone_verified` is null because the field wasn't asked of legacy users. The right imputation might be "false" or might be a special "unknown" category.
- `latest_payment_date` is null because no payments have been made. The right imputation isn't a date at all — you might create a derived `days_since_last_payment` feature where null becomes the max value (= "infinity," = "never").

When you understand the data-generating process, hand-coded imputations often dominate any statistical method.

### 24.4.8 Tree models: native handling

Some tree-based libraries — XGBoost, LightGBM, CatBoost — handle missing values natively. The algorithm learns, at each split, which side missing values should go. This is often the simplest approach: skip the imputation entirely and let the model handle it.

(scikit-learn's `RandomForestClassifier`, historically, did *not* handle missing values; recent versions support it via `HistGradientBoostingClassifier`. Spark ML's tree algorithms generally require imputation upstream.)

When this works, it's wonderful — no imputation pipeline, no decisions to make, the model figures it out. The downside is that "the model figures it out" is a black box; if you wanted to understand or audit what was happening to missing values, the answer is "look at every split in every tree."

---

## 24.5 The leakage trap: fitting imputation on train only

This is one of those subtle, expensive bugs.

The wrong code:

```python
# WRONG
df['income'] = df['income'].fillna(df['income'].mean())
X_train, X_test = train_test_split(df, test_size=0.2)
```

You've computed the imputation value (the mean) using *all* the data, including the test set. The test set's information has leaked into the training set. This is a small leak — the mean of a column doesn't usually carry much info — but it is leakage nonetheless, and for more complex imputers (KNN, MICE), the leak becomes serious.

The right code:

```python
# RIGHT
X_train, X_test = train_test_split(df, test_size=0.2)
imputer = SimpleImputer(strategy='mean')
imputer.fit(X_train[['income']])  # fit on train only
X_train['income'] = imputer.transform(X_train[['income']])
X_test['income'] = imputer.transform(X_test[['income']])
```

Fit the imputer on the training set. Apply (transform) it to both train and test. The test set never participates in fitting any parameter — its job is to estimate generalisation, and any contamination ruins the estimate.

Same logic applies to cross-validation: the imputer must be re-fit on each fold's training subset, not on the whole dataset. The cleanest way to enforce this in scikit-learn is to wrap imputation inside a `Pipeline` and pass the pipeline to `cross_val_score`:

```python
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression

pipe = Pipeline([
    ('impute', SimpleImputer(strategy='median')),
    ('model', LogisticRegression()),
])
cross_val_score(pipe, X, y, cv=5)  # imputation re-fit each fold, automatically
```

This pattern — pipelines that include preprocessing — is the right shape for any non-trivial ML project. Spark ML's `Pipeline` (Chapter 62) has the same conceptual structure.

### 24.5.1 The asymmetric case

What if your test set has missing values in a column where your training set had none? Your imputer was fit on training and has no statistic for that column. Some choices: (a) impute with a global constant decided in advance (e.g., 0 or the median of the training set's overall numeric values); (b) refuse to predict and return a sentinel score; (c) train a separate imputer on a held-out subset of "complete" data and ship it as part of the artifact. Most production systems use option (a) — every imputer has a fallback value for unseen columns or row patterns.

### 24.5.2 Never impute the target

Categorically: do not impute $y$. The target is the thing you are trying to learn. If $y$ is missing, you cannot supervise on that row. Either drop it (in training) or accept that you cannot evaluate the model on it. Trying to impute $y$ creates a feedback loop where your model trains on its own predictions, which collapses.

The only exception is in *semi-supervised* learning, where you have a small labeled set and a large unlabeled set, and you bootstrap labels through a careful procedure. This is out of scope for the ML Associate exam and a different topic from imputation.

---

## 24.6 A worked example

Let's work through a small, concrete numerical example.

A 100-row dataset with three columns: `age`, `employment_status`, `income`. Twenty rows have `income` missing.

The full true distribution (which in real life we wouldn't see):

| employment_status | n  | true mean income |
|-------------------|---:|-----------------:|
| employed          | 70 | $75,000          |
| self-employed     | 20 | $120,000         |
| retired           | 10 | $40,000          |

The 20 missing rows are distributed disproportionately among self-employed (15 missing) and retired (5 missing). Employed people answer the question reliably. The mechanism is MAR: missingness depends on `employment_status` (observed), but not on `income` itself once we know status.

**Method 1: mean imputation.**

The dataset's overall mean income, computed on the 80 observed rows, is heavily weighted toward employed people. We fill all 20 missing rows with that mean — let's say $72,000.

The post-imputation column statistics:
- True mean of `income` (if we could see all 100 rows): $77,500.
- Mean-imputed value: $72,000.
- Imputed self-employed person's "income": $72,000 (true mean: $120,000).
- Imputed retired person's "income": $72,000 (true mean: $40,000).

The imputed values are systematically biased: too low for self-employed, too high for retired.

**Method 2: group-mean imputation.**

We compute, for each `employment_status`, the mean of the observed rows with that status, and impute missing rows accordingly.

- Self-employed observed (5 rows, mean): $118,000. Imputed: $118,000 (true mean: $120,000). Close.
- Retired observed (5 rows, mean): $42,000. Imputed: $42,000 (true mean: $40,000). Close.

Much better. We've used the MAR-relevant information (employment status) to inform the imputation.

**Method 3: MICE.**

`IterativeImputer` fits a regression of `income` on `age` and `employment_status` using the 80 observed rows, and predicts the 20 missing values. If `age` carries some additional signal beyond `employment_status` (perhaps within self-employed, older people earn more), MICE uses it. The resulting imputations are typically slightly better than group-mean, with the cost of more compute and complexity.

**Method 4: do nothing, use HistGradientBoosting.**

Skip imputation. Let the model handle missing values natively. At training time, the gradient-boosted trees learn, at each split involving `income`, which way the missing rows should go — effectively learning the imputation as part of the model.

In our small example, all of methods 2–4 produce reasonable predictions. Method 1 (the naive mean) is meaningfully worse, especially for the model's predictions on self-employed and retired borrowers.

---

## 24.7 Missingness as a feature

A pattern I cannot emphasise enough: missingness is often *itself* the signal.

Consider a job application form. A field for "current employer" is missing. What does that tell you? Likely: this person is unemployed, or doesn't want to disclose. Either way, that's relevant to whether the person will repay a loan. The *value* you would impute matters less than the *fact* that the value was missing.

The missingness indicator (§24.4.4) captures this. In some problems, the indicator is the most predictive feature you have, and the imputed value adds little.

You can take this further with **patterns of missingness**. If certain *combinations* of columns tend to be missing together (e.g., a row missing both `phone` and `email` is qualitatively different from a row missing only `email`), you can engineer features for those patterns. Group rows by their "missingness pattern" and one-hot encode the patterns. For datasets with extensive structured missingness, this can be powerful.

The takeaway: do not treat missingness only as a problem to clean up. Sometimes it is the most honest feature in the dataset.

---

## 24.8 Multivariate imputation in scikit-learn

For completeness, the standard scikit-learn snippets.

**`SimpleImputer`** — mean, median, most-frequent, or constant.

```python
from sklearn.impute import SimpleImputer

imputer = SimpleImputer(strategy='median')
imputer.fit(X_train)
X_train_imputed = imputer.transform(X_train)
X_test_imputed = imputer.transform(X_test)
```

**`KNNImputer`** — KNN-based.

```python
from sklearn.impute import KNNImputer

imputer = KNNImputer(n_neighbors=5, weights='distance')
imputer.fit(X_train)
```

**`IterativeImputer`** (MICE).

```python
from sklearn.experimental import enable_iterative_imputer  # noqa
from sklearn.impute import IterativeImputer

imputer = IterativeImputer(max_iter=10, random_state=0)
imputer.fit(X_train)
```

**`MissingIndicator`** — explicit missingness flagging.

```python
from sklearn.impute import MissingIndicator

indicator = MissingIndicator()
M_train = indicator.fit_transform(X_train)
```

You typically combine these in a `FeatureUnion` or `ColumnTransformer` so that you keep both the imputed values and the indicators.

For PySpark, the equivalent is `pyspark.ml.feature.Imputer` (median / mean / mode), which works at scale; for more sophisticated imputation in Spark you typically code it yourself or use a UDF.

---

## 24.9 The summary table

A practical decision aid:

| Situation | First-try strategy |
|---|---|
| MCAR, small fraction | Listwise deletion, or simple mean/median imputation, plus indicator |
| MAR, fraction <30% | Group-mean or KNN imputation, plus indicator |
| MAR, fraction <30%, complex inter-feature dependencies | MICE (`IterativeImputer`), plus indicator |
| MNAR | Domain-specific handling; sensitivity analysis; document bias |
| Missing has clear meaning (e.g., "no transactions") | Encode the meaning explicitly (e.g., 0 or "never") |
| Using XGBoost / LightGBM / HistGradientBoosting | Often just leave it; the model handles missingness natively |
| Tree models in Spark ML | Impute upstream (median for numeric, mode for categorical) |
| Target column ($y$) missing | Drop the row (or use semi-supervised methods, out of scope) |

This is a *first-try* table, not a final answer. The right strategy is the one that you've validated by comparing models trained with each approach and seeing which performs best on a held-out set. Try a few. Choose by evidence.

---

## 24.10 What this builds on / where it returns

**Builds on:**

- Chapter 22 on the leakage discipline — imputation is the most common silent-leakage path.
- Chapter 23 on EDA — you discovered missingness during EDA, and the leakage scan caught features whose missingness was tightly correlated with the target.
- Chapter 7 (probability): the MAR/MCAR/MNAR taxonomy is a statement about conditional independence.

**Returns in:**

- Chapter 25 (categorical encoding): categorical columns also have a "missing" category that has to be handled.
- Chapter 27 (outliers): outliers and missing values are sometimes the same thing wearing different costumes (e.g., the $9,999,999 spike from Chapter 23's `income` column).
- Chapter 62 (Spark pipelines): the imputer becomes a stage in a pipeline that is fit on train, applied to test.
- Chapter 71 (Feature Store): consistent imputation between training and serving is one of the things feature stores solve.

---

## 24.11 Exercises

1. **Classify the mechanism.** For each scenario, say MCAR, MAR, or MNAR, and justify.
   (a) A laboratory machine drops 0.5% of readings due to occasional read errors.
   (b) A weight scale fails for people above 350 lb; readings are missing for those individuals.
   (c) An online survey has a "Do you smoke?" question; people who skip it are more likely to be smokers.
   (d) A clinic measures blood pressure on every patient, but the BP cuff doesn't fit children, so under-5s have no BP measurement.

2. **The classifier diagnostic.** You train a random forest to predict whether `income` is missing from the other columns. The cross-validated AUC is 0.62. What does this tell you?

3. **Mean imputation bias.** A column `loan_amount` has true mean $15,000 across the population. Missingness is correlated with low income: low-income borrowers are more likely to skip the field, and they also take smaller loans on average ($10,000). After mean imputation on the observed data (where the observed mean is $17,000), what direction is the bias in the model's prediction for low-income borrowers?

4. **The indicator trick.** You add a `was_missing` indicator. Your model's AUC goes up by 2 points. What does this tell you?

5. **The leakage trap.** Identify the bug in this code:
   ```python
   df['income'] = df['income'].fillna(df['income'].median())
   X_train, X_test = train_test_split(df, test_size=0.2)
   ```
   Rewrite it correctly.

6. **Domain-specific imputation.** A column `days_since_last_purchase` is null for new customers. What value would you impute, and why?

7. **The hidden MNAR.** Your missingness classifier shows AUC = 0.51 (essentially random) for `income`'s missingness. Can you conclude MCAR? Why or why not?

8. **MICE vs. mean.** On a synthetic dataset, you compare mean imputation against MICE. Mean imputation gives an RMSE of 18,000 on the imputed values; MICE gives 12,000. Are you guaranteed that MICE will produce a better final ML model?

9. **Tree models and missingness.** Why can HistGradientBoosting handle missing values "natively" but a vanilla decision tree cannot?

10. **The wrong fix.** A data scientist sees 30% nulls in a column and immediately drops the column. What information have they lost, and what should they have done first?

11. **Multiple imputation outcome.** MICE produces multiple imputed datasets and you take the average across them as your final imputation. What aspect of imputation are you losing by averaging, and when does that matter?

12. **The classifier you trained.** In §24.3.1 you trained a random forest to predict missingness. Why would using *single-column* leakage models (Chapter 23 §23.9) not be enough for this diagnosis?

<details>
<summary>Answers</summary>

1. (a) MCAR — random hardware error, unrelated to anything. (b) MNAR — missingness depends on the value itself (weight). (c) MNAR — missingness depends on the smoking status, which is the missing variable. (d) MAR — depends on `age` (observed), not on the missing BP value itself (within the under-5 group, all have missing BP regardless of actual BP).

2. The missingness is *predictable* from other features, well above chance (AUC > 0.5). This rules out MCAR; the situation is at least MAR. You should use those features to inform imputation (e.g., group-mean by the most predictive feature, or MICE).

3. The imputed value ($17,000, the observed mean) is *higher* than the true mean ($15,000) because the missing rows are systematically low-loan rows. So the model sees low-income borrowers' loan amounts as being around $17,000 when they actually are around $10,000. Predictions for low-income borrowers will be biased toward higher predicted loan amounts, and any downstream metric (e.g., predicting default from loan amount) will be miscalibrated for that subpopulation.

4. The fact of missingness itself is predictive of the target — beyond whatever signal the imputed value provides. This is a hallmark of MAR or MNAR. Always include the indicator; it costs almost nothing and frequently helps.

5. The imputation parameter (the median) is computed on the *entire* dataset including the test rows, so the test set's information has leaked into training. Correct version:
   ```python
   X_train, X_test = train_test_split(df, test_size=0.2)
   median = X_train['income'].median()
   X_train['income'] = X_train['income'].fillna(median)
   X_test['income'] = X_test['income'].fillna(median)
   ```
   Or, better, inside a `Pipeline` so cross-validation handles the refit per-fold.

6. Probably zero or a domain-specific sentinel (or a very large value if "long time" is the semantic intent). New customers literally have no purchases; the right value depends on whether your downstream model is using "small days_since_last" as "active" (then null → infinity or large) or "large days_since_last" as "active" (rare). Adding a `is_new_customer` indicator is usually the cleanest approach.

7. No. AUC = 0.5 is consistent with both MCAR ("truly random") and MNAR (the missingness depends only on the missing value, which by definition you don't have to predict from). Domain knowledge is required to distinguish.

8. No. The metric you care about is downstream model performance, not imputation RMSE. Two effects: (a) the model may not need the imputed values to be highly accurate — it may use them in coarse ways where a 6,000-RMSE difference doesn't matter; (b) imputation introduces correlations between the imputed values and other features, which can bias models in subtle ways even when the imputed values are accurate. Always validate by comparing end-to-end model performance.

9. HistGradientBoosting bins features into discrete bins, and missingness becomes one of the bin values. At each tree split, the algorithm tries sending missing values to either the left or right child and picks the direction that minimises loss. A vanilla decision tree, as classically defined, computes splits on real-valued thresholds and has no built-in notion of where missing values should go — so it crashes or silently does the wrong thing without explicit handling.

10. They lose the *entire* feature, including the 70% of rows where it was observed. If the feature is informative — and we don't know yet whether it is — they have given up that information for everyone. They should have: (a) checked the mechanism of missingness; (b) tried imputation plus an indicator; (c) compared model performance with and without the column; (d) only then decided whether to drop it.

11. Averaging collapses the *uncertainty* in the imputation. MICE's full procedure yields multiple plausible imputed datasets representing what the missing values *could* be; averaging treats them as a single point estimate. You lose the ability to propagate imputation uncertainty into your final predictions. For most ML applications we ignore this and use the average, but for confidence-interval estimation or other inferential tasks, the multiple-imputation machinery matters.

12. The single-column leakage scan from Chapter 23 looks at one feature's relationship to the *target*. The missingness diagnostic looks at one column's missingness pattern's relationship to *all other features* — a multi-feature classification. You want the multivariate signal because missingness often depends on combinations: a row missing `income` might have a particular combination of `age` and `employment_status` that no single feature reveals.

</details>
