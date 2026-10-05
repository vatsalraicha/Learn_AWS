# Chapter 23 — Exploratory Data Analysis: What to Look At and Why

> **Goal of this chapter:** to teach you the habit, the discipline, and the specific moves of Exploratory Data Analysis — the unglamorous, slow, irreplaceable step that comes before any feature engineering and before any model. If you finish this chapter and only remember one sentence, let it be this: *the best ML practitioners are the ones who spend the most time looking at their data.* Not the most time tuning hyperparameters. Not the most time arguing about which gradient-boosted tree library to use. The most time looking — really looking — at the rows and the columns and the distributions and the joins. This chapter teaches you what to look at, in what order, and why each look matters.

---

## 23.1 A short story about why EDA is non-negotiable

Imagine, for a moment, that we hand you a CSV file called `loans.csv`. We tell you: "Build a model that predicts whether each loan will default. The label is in the `default` column. Three hundred thousand rows. Have it ready by next Friday." We then walk away.

You are a competent engineer. You know your way around `scikit-learn` and `pandas`. The temptation — and it is enormous, and you will feel it every single time — is to skip straight to the modeling. Read the CSV. Fit a logistic regression. Look at the accuracy. Maybe a random forest if you have time. Friday is only five days away.

Here is what happens if you give in to that temptation.

You read the CSV. You notice a `pd.read_csv` warning about mixed dtypes in column 17. You ignore it. You drop the `default` column off the side of the DataFrame to use as your label, fit a logistic regression with a `OneHotEncoder` on every string column, and on the validation set you get an AUC of **0.998**. You are delighted. You message your manager: "Done. 99.8% AUC."

Your manager, who has been doing this for fifteen years, asks one question: "Which feature is doing the work?"

You print the top weights. The biggest one, by a factor of ten, is a column called `recovery_amount`. You look at it. It is the dollar amount the bank recovered after the loan defaulted. It is, in other words, *only ever non-zero after a default*. The model didn't learn to predict default; it learned that `recovery_amount > 0 ⇒ default = 1`. Tautologically. Your AUC is a lie. Your model is useless. You have built nothing.

If you had spent thirty minutes looking at the data before fitting anything, you would have caught this in minute four. EDA is not a checkbox. It is the cheapest insurance against the most expensive class of mistake in ML — *training a model on a dataset you don't actually understand*.

This chapter, then, is a working catalogue of the things to look at, the questions to ask, and the bugs to catch, **before any line of model code is written.**

---

## 23.2 What EDA is, and what it is not

EDA — exploratory data analysis — is a term that goes back to John Tukey in the 1970s. Tukey's framing, which has aged extraordinarily well, was that *data analysis is two-phase*: first an exploratory phase, where you let the data tell you what's there, what's surprising, what's broken; and then a confirmatory phase, where you test specific hypotheses or fit specific models. The phases are not interchangeable. You cannot confirm what you have not first explored.

For our purposes — building an ML model — EDA has three concrete goals:

1. **Understand the shape, content, and quality of the data.** What columns are there? What are their types? How many nulls? How many distinct values? What does a typical row look like? These questions sound trivial. Skipping them is the most common rookie error.
2. **Discover problems before the model does.** Missing data with a pattern, columns mislabelled as numeric when they're actually categorical, leakage features that are too predictive, duplicates, outliers, time-shifts, units inconsistencies. The model will not tell you about these. It will silently fit around them and give you bad predictions or — worse — a brilliantly good number that is actually a leakage artifact.
3. **Form hypotheses about what features will matter.** EDA is where intuition is built. Looking at how `income` distributes for defaulters vs. non-defaulters is what tells you whether income is going to be useful. The model will eventually agree or disagree, but going in with a prior — informed by EDA — makes you much harder to fool.

EDA is **not**:

- A formal statistical test. We are not computing p-values here. We are sketching the landscape.
- A modeling step. We are not fitting models to make decisions. We may fit a *diagnostic* model (see §23.9 on leakage detection), but that's a probe, not a product.
- A finished product. EDA is a sketchbook. It is for *you*. The polished notebook you eventually share with stakeholders is downstream of EDA, not the same artifact.

A senior engineer with twenty years of ML experience and an undergraduate intern doing their first project both do EDA. The senior just does it faster, catches more, and knows what they're not seeing. The intern, given the same data, will write `df.head()` and then immediately train a model. The difference is taste, and taste is built by repetition.

---

## 23.3 The shape of the data: rows, columns, types

The first three lines of any EDA notebook are, essentially universally:

```python
df.shape
df.dtypes
df.head()
```

`shape` returns `(n_rows, n_cols)`. You want to know this before doing anything else. Three hundred thousand rows and 27 columns is one situation. Thirty-eight rows and 800 columns is a completely different situation (you are in the "more features than examples" regime, which Chapter 19's bias-variance picture warns you about). Three billion rows is a third situation — you are not going to load the whole thing into memory, and the rest of this chapter has to be done in Spark or in chunks.

`dtypes` returns the data type of each column. Pandas will infer types from the file. **These inferences are routinely wrong.** A column that contains `"01001"` (a Massachusetts zip code) will be read as an integer, dropping the leading zero. A column that contains `"$1,200"` will be read as a string because of the comma and the dollar sign. A column of dates stored as `"2024-03-15"` will be read as a string until you `pd.to_datetime` it. A column that *should* be categorical (`{"low", "medium", "high"}`) is correctly read as a string but might just as easily be encoded as `{1, 2, 3}` and silently treated as continuous.

`head()` returns the first five rows. The first thing to do with `head()` is to look at it and check that every column's contents matches what its name suggests. The `age` column should have numbers in a sane range (zero to a hundred-ish). The `created_at` column should have dates. The `state` column should have two-letter abbreviations or full state names. If anything is off — `age` contains the value `-999` (sentinel for missing? real?), `created_at` is the year 1900 (Unix epoch leak?), `state` contains `"unknown"` — you have caught your first problem.

I will also routinely run `df.tail()` and `df.sample(20)`. The reason for `tail()` is that data files are often sorted by time, and the last rows show what the *latest* data looks like, which is what your model will be predicting on. The reason for `sample(20)` is that `head()` and `tail()` show you the extremes; `sample` shows you what's in the middle, where most of your data actually lives. Twenty random rows will reveal patterns that five head rows never will.

### 23.3.1 The "schema interview"

Beyond looking at the data, there is one move that absolutely no online tutorial will teach you and that the most senior practitioners do religiously: **interview the data owner**.

For every column, ask:

- What does this column *mean*? Not "what is its name" — what is its operational definition? What does `total_account_balance` *actually* measure? Is it the balance at the moment the row was generated, or at end of month, or at some other point?
- *When* is this value populated? At application time? At loan origination? Later, as the loan matures?
- *Who* fills it in? A user? A system? An offline batch job?
- What are the *legitimate values*? What sentinel values represent missing or unknown?
- Can it change after the row is created? If yes, what triggers the change?

That last question is the most important and the most often missed. If `total_account_balance` is *updated* whenever the user takes any action, then the value you see for a given loan at training time is *not* the value that was visible at the moment of decision. Using it as a feature is leakage. The model will use information from the future. You will get a wonderful AUC and a useless model.

Every column has a story. EDA is where you learn the story. If the data owner is unavailable, you have to read code, read docs, and sometimes resort to reading the raw event logs. Skipping this is how you ship the `recovery_amount` model from §23.1.

---

## 23.4 Per-column summaries: nulls, uniques, ranges

After looking at the data globally, you look at it column by column. The standard pandas one-liner is:

```python
df.describe(include='all')
```

For numeric columns this returns count, mean, std, min, the 25/50/75 percentiles, and max. For object columns it returns count, unique count, top value, and frequency of the top value. The results are imperfect — `describe` has a habit of pretending integer-coded categoricals are continuous — but it's a starting point.

The four checks I run on every column, regardless of type, are:

1. **Null count.** `df.isnull().sum()`. How many missing values are there in this column? Is it 0% (suspicious — is null really impossible, or are nulls encoded as something else, like `-1` or `"N/A"` or `0`)? Is it 5% (manageable, see Chapter 24)? Is it 80% (the column is probably useless or requires special handling)?
2. **Unique count.** `df['col'].nunique()`. How many distinct values does this column take? For a categorical column with 50 US states, you expect ~50 uniques. For a numeric column you expect many (every row potentially different). For a binary column you expect 2. A `gender` column with 17 unique values is a problem; a `state` column with 1 unique value is a problem; a `customer_id` column with 300,000 unique values across 300,000 rows is — possibly correct, but you should check whether it's actually the primary key, in which case you should not be feeding it as a feature.
3. **Min and max** (numeric columns). What's the range? If `age` ranges from -3 to 273, you have a data problem. If `loan_amount` ranges from 0 to 999999, the 999999 is probably a sentinel for "missing" rather than a real loan amount.
4. **Value counts of the top 10** (categorical / low-cardinality columns). `df['col'].value_counts().head(10)`. What are the most common values? Is the distribution roughly what you'd expect, or is one value 95% of the data?

These checks routinely reveal:

- Sentinel values for missing data (`-1`, `999`, `"unknown"`, empty string, `"N/A"`).
- Tail-heavy columns where most rows have one value and a few have wild outliers.
- Columns that look numeric but are really IDs (and therefore meaningless as features).
- Categorical columns with absurd cardinality (a `user_id` column with millions of values, when the data owner thought it was a small enum).

---

## 23.5 Univariate distributions: histograms and bar charts

After summarising columns numerically, you visualise them. For numeric columns, a histogram. For categorical columns, a bar chart of the value counts.

For a numeric column `income`:

```python
import matplotlib.pyplot as plt
df['income'].hist(bins=50)
plt.xlabel('income')
plt.ylabel('count')
plt.show()
```

What you are looking for, in rough order of frequency:

- **Skew.** Most real-world distributions of money, counts, durations, sizes, and so on are right-skewed: a long tail of large values pulling the mean up. The histogram will show a peak near the low end and a long tail to the right. This matters because most statistical models behave best on roughly symmetric distributions — a log transform (Chapter 26) often helps.
- **Bimodality or multimodality.** Two peaks in the histogram suggests two underlying subpopulations. For `income`, this might be employed vs. retired, or US vs. international. Often a sign that you should split the data and analyse the subpopulations separately, or that you're missing a categorical feature that would let the model treat them differently.
- **Spikes at suspicious values.** A spike at exactly 0 might be real (people with no income) or might be a missing-data sentinel. A spike at exactly 100,000 might be that the loan application's slider topped out at $100k and many people who actually earn more reported the maximum. A spike at exactly `mean` is a sign that someone mean-imputed and didn't tell you.
- **Boundaries.** Where does the distribution start and end? If `age` ranges from 0 to 120, is that all of those values plausible, or is 0 actually "unknown"?

For a categorical column `loan_purpose`:

```python
df['loan_purpose'].value_counts().plot.bar()
plt.show()
```

What you are looking for:

- **Cardinality.** Five categories, twenty, two hundred, twenty million? Each is a different beast (Chapter 25).
- **Imbalance.** Is one category 90% of the data? That category will dominate any encoding.
- **Suspicious entries.** Values like `""`, `" "`, `"N/A"`, `"unknown"`, `"OTHER"`, `"other"` (yes, the case-difference will trip you up — those are different categories to pandas).
- **Typos.** `"California"`, `"california"`, `"Calif"`, `"CA"` — same state, four categories. Without normalisation, your encoder will treat them as four separate things.

---

## 23.6 Bivariate analysis: how features relate to the target and to each other

Univariate is necessary but insufficient. The really interesting questions are bivariate: how does feature X relate to the target Y, and how do features relate to each other?

### 23.6.1 Numeric feature × binary target

For a numeric feature like `income` and a binary target like `default`, the right first plot is a **comparative histogram or boxplot**:

```python
df.boxplot(column='income', by='default')
plt.show()
```

A boxplot shows the median, the IQR (25th to 75th percentile), and outliers, for each value of `default`. If defaulters have a noticeably lower median income than non-defaulters, the feature carries signal. If the two boxplots overlap almost completely, the feature has weak or no marginal signal — though it might still be useful in combination with others (this is what Chapter 28 on interactions is about).

A common refinement is to look at **conditional histograms**:

```python
df[df['default'] == 1]['income'].hist(bins=50, alpha=0.5, label='defaulted')
df[df['default'] == 0]['income'].hist(bins=50, alpha=0.5, label='did not default')
plt.legend()
plt.show()
```

Overlaid, with transparency. If the two distributions are visibly different, the feature is informative. If they are nearly identical, it isn't.

### 23.6.2 Categorical feature × binary target

For a categorical feature like `state` and a binary target like `default`, the question is: does the default rate vary by state?

```python
df.groupby('state')['default'].agg(['mean', 'count']).sort_values('mean')
```

The `mean` of a 0/1 column is just the rate of 1s. So this groups by state, computes the default rate in each state, and the count of rows. Look at the variance across states. If default rates are 6% in every state, the feature is uninformative. If they range from 1% in Hawaii to 22% in Mississippi, the feature carries signal — but check the counts (a state with only 12 rows and a 25% default rate has a noisy estimate; don't be fooled).

This is the basic logic behind **target encoding**, which Chapter 25 will explore.

### 23.6.3 Numeric × numeric: scatter and correlation

For two numeric features, a scatter plot. For many numeric features, a correlation matrix:

```python
df.select_dtypes(include='number').corr()
```

This returns the Pearson correlation between every pair of numeric columns. A heatmap of this matrix is a standard EDA artefact:

```python
import seaborn as sns
sns.heatmap(df.select_dtypes(include='number').corr(), annot=True, cmap='coolwarm', center=0)
```

What to look for:

- **Pairs of features with very high correlation** (|r| > 0.9). These are largely redundant. Linear models will give them unstable, opposite-signed coefficients (multicollinearity). Tree models will be confused about which to split on. Often you want to drop one or combine them.
- **Features with high correlation to the target.** Promising. But check whether the correlation is *suspiciously* high — see §23.9.
- **The diagonal.** Always 1. Sanity check that the function ran.

Be aware: Pearson correlation measures only *linear* relationships. A feature with a strong U-shaped relationship to the target will have Pearson correlation near zero. Scatter plots catch this; correlation tables don't. **Look at the scatter** before trusting the matrix.

---

## 23.7 Class balance for classification

For classification problems, *immediately* compute the class distribution:

```python
df['default'].value_counts(normalize=True)
```

For a binary problem, you want to know whether you have a 50/50 dataset (rare and luxurious), a 90/10 dataset (common — most real classification problems are imbalanced), or a 99.9/0.1 dataset (fraud, ad-click, medical screening).

The class balance affects:

- **What metrics you can trust.** Accuracy on a 99.9/0.1 dataset is meaningless — predicting "no" always gets 99.9%. You will need precision, recall, F1, AUC, PR-AUC. Chapter 42 covers this.
- **Whether you need resampling or class weights.** Chapter 46. Severely imbalanced datasets often benefit from up-sampling the minority class, down-sampling the majority, or using class weights in the loss function.
- **How big a sample size you have for the minority class.** A 0.1% positive rate in 100,000 rows means 100 positive examples. That is not enough to fit a meaningful model on a high-dimensional feature space.

For multiclass problems, the same logic — look at the counts of every class. A class with 12 rows in a 1M-row dataset is a class you will not learn well.

---

## 23.8 Time-based patterns: drift and seasonality

If your data has a timestamp — and most real-world data does — you must look at it over time. Three plots, every time:

**Plot 1: row count by time.** How many rows per day, week, month? Is the data evenly distributed in time? If you suddenly see 10x as many rows starting in March, something happened — a new data source, a marketing campaign, a system change. Whatever it is, you need to understand it before training. Often the right move is to *filter* to the period where the data is stable.

**Plot 2: target rate by time.** What is the rate of the positive class over time? Is it flat? Trending up? Seasonal? If your default rate was 5% all of 2022 and 12% all of 2023, the model trained on 2022 data will under-predict defaults in 2023. This is concept drift, previewed in Chapter 3 §3.12, and is one of the strongest arguments for time-based train/test splits (Chapter 21).

**Plot 3: feature distribution by time.** Pick a few important features and plot their mean (or median) over time. If `income` was right-skewed and stable until October, and then suddenly the median jumped 30%, something changed — a new data source, a unit change (dollars to thousands), a parsing bug. You want to know.

These three plots, run on every dataset, will catch a class of problem that no amount of cross-validation will reveal. Cross-validation assumes the data is i.i.d.; time series almost never is.

---

## 23.9 The leakage scan: features that are too good to be true

This is the single most important EDA move I have not yet given you, and the one this chapter opened with.

After understanding the data, but before fitting any "real" model, fit a *diagnostic* model and look at the per-feature predictive power. Specifically: for each numeric or one-hot-encoded categorical feature, fit a *single-feature* logistic regression and compute its AUC on the training set.

```python
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

for col in numeric_cols:
    x = df[[col]].fillna(df[col].median())
    y = df['default']
    model = LogisticRegression().fit(x, y)
    p = model.predict_proba(x)[:, 1]
    print(col, roc_auc_score(y, p))
```

Now read the output. A typical feature might have a single-feature AUC of 0.55–0.70. Strong features might hit 0.80. **An AUC of 0.95 or higher on a single feature is a red flag.** No legitimate feature is *that* predictive on its own. The most likely explanations are, in order:

1. **Direct leakage:** the feature contains information about the label by construction (the `recovery_amount` example from §23.1, or a feature like `days_since_default` which is only computable after default).
2. **Indirect leakage:** the feature is computed *after* the label is determined (e.g., `account_status_today` reflects post-default changes).
3. **A perfect proxy for the label:** the feature is a different label from a different system that says exactly the same thing.

When you find one, you do not delete it silently. You go back to the data owner and ask, "is this feature available at decision time?" The answer is often "no" — and you remove the feature. Sometimes the answer is "yes, actually it is, and the strong signal is genuine," in which case keep it and be grateful. The conversation is the point; the AUC is just the trigger.

This scan also catches:

- **Duplicate columns** (perfect AUC).
- **Encoding of the target into the features** (perfect AUC).
- **ID columns that happen to correlate with the target** because of how data was sampled (suspiciously high AUC for something that should be meaningless).

I cannot emphasise enough how often this scan catches a model-killing bug in the first thirty minutes of EDA. If you skip it, you will eventually train a model with an AUC of 0.998 and ship it before someone asks the question your manager asked.

---

## 23.10 Outliers: a preview

Outliers deserve a chapter of their own (Chapter 27), but EDA is where you first notice them. The diagnostics:

- **For numeric columns:** `df['col'].describe()` shows min and max. If the max is many standard deviations above the 75th percentile, you have outliers. A boxplot makes them visible.
- **For categorical columns:** value counts. Categories with only a handful of occurrences are "rare categories" — a kind of outlier.
- **For rows:** are there rows where every numeric feature is suspiciously extreme? Multivariate outliers — Mahalanobis distance, Chapter 27.

The decision *what to do* about outliers is for Chapter 27. The EDA step is just to notice they exist.

---

## 23.11 A worked example: the loans dataset

Let me put all this together on a concrete (fictitious but realistic) dataset.

We are given `loans.csv`. Three hundred thousand rows. The data owner says: "Each row is a loan application; predict the `default` column, which is 1 if the borrower defaulted within 36 months and 0 otherwise."

**Step 1: shape, dtypes, head.**

```python
df.shape
# (300000, 23)

df.dtypes
# loan_id           int64
# application_date  object
# applicant_age     int64
# state             object
# loan_amount       float64
# loan_purpose      object
# income            float64
# credit_score      object       ← suspicious! should be numeric
# employment_years  float64
# home_ownership    object
# debt_to_income    float64
# delinq_count      int64
# fico_band         object
# recovery_amount   float64       ← suspicious! see §23.1
# late_payments     int64
# ...
# default           int64
```

Two flags already: `credit_score` is read as object (something non-numeric is in there), and `recovery_amount` exists in the feature set.

`df.head()` confirms: `credit_score` has values like `"720"`, `"680"`, and sometimes `"--"`. The `"--"` is a missing-data sentinel. The application_date column has values like `"2021-03-15"`. We `pd.to_datetime` it.

**Step 2: per-column summaries.**

```python
df.isnull().sum()
# loan_id              0
# application_date     0
# applicant_age        0
# ...
# employment_years 84120     ← 28% null!
# ...
# recovery_amount 285200     ← 95% null (it's only populated for defaults)
```

`employment_years` is 28% null. Why? Probably because it doesn't apply to retired borrowers, students, or self-employed people. This is **MAR** (missing at random — see Chapter 24): the missingness depends on other observable features, but is informative.

`recovery_amount` is 95% null because it is only populated for the ~5% of loans that defaulted. This is the leakage smoking gun.

**Step 3: distributions.**

`applicant_age` is normal-ish, peaking around 40, ranging 18 to 75. Sane.

`loan_amount` ranges from $500 to $40,000, right-skewed. Sane.

`income` ranges from $0 to $9,999,999. The maximum is suspicious — `9999999` is the kind of value that screams "field maxed out" or "system sentinel." Looking at the histogram, there's a spike of about 200 rows at exactly $9,999,999. We will need to handle these (likely set to NaN and impute, or cap at a reasonable maximum).

`credit_score` is read as object. We coerce: `df['credit_score'] = pd.to_numeric(df['credit_score'], errors='coerce')`. The values that were `"--"` become NaN. Now it's numeric. Range 300–850, peaks around 700. Sane.

`state` has 51 unique values. Good — 50 states plus DC. Default rate by state varies from 3% to 14%. Informative.

**Step 4: bivariate.**

Default rate by `loan_purpose`:

```
debt_consolidation     12.1%
credit_card             9.4%
home_improvement        4.2%
medical                15.7%
small_business         19.3%
wedding                 8.1%
moving                 11.5%
car                     5.6%
other                  14.0%
```

A 4x spread. Strongly informative.

Default rate by `applicant_age` (binned into deciles): younger borrowers default more — about 14% in the 18-25 bin, dropping to 5% in the 55+ bin. Monotonic, informative.

**Step 5: leakage scan.**

```
loan_amount        AUC: 0.61
applicant_age      AUC: 0.58
income             AUC: 0.62
credit_score       AUC: 0.71
employment_years   AUC: 0.62
debt_to_income     AUC: 0.66
delinq_count       AUC: 0.74
late_payments      AUC: 0.81     ← strong, but is it OK?
recovery_amount    AUC: 0.99     ← LEAKAGE
fico_band          AUC: 0.71
```

`recovery_amount` is the obvious one. We confirm with the data owner: yes, it's populated only after default. Remove.

`late_payments` is suspiciously high (0.81). We ask: at what time is `late_payments` computed? Answer: *at the end of the loan*, not at origination. It includes late payments that happened *during* the 36-month observation window. Leakage. Remove.

After removing these two, the strongest single feature is `credit_score` at 0.71 — a believable number.

**Step 6: time.**

Plotting `default` rate over time: stable around 8% from 2018 through early 2020, jumps to 14% in mid-2020, settles back to 9% by 2021. COVID-19. We make a note: the train/test split must be time-aware, and the model will need a feature that captures *when* the loan was originated, or we will mispredict cross-period.

We have spent a couple of hours. We have caught two leakage features that would have given us a fake AUC of 0.999. We have identified a missing-data column that needs careful handling. We have noticed an outlier sentinel in `income`. We have noticed COVID-era drift. **We have not yet trained any model.**

This is what EDA gets you. Without it, you would have spent five days fitting models, shipping the recovery_amount classifier, and only catching it (if you were lucky) at the post-mortem.

---

## 23.12 Where to spend the most EDA time

EDA can expand to fill any amount of time you give it. Some practical heuristics for where to spend it:

**Spend the most time on:**

- **Features the model will rely on most.** The leakage scan tells you which features have the highest single-feature AUC. Those are the features whose semantics you must understand cold.
- **Features with missing data.** A 30%-null column needs more thought than a 0%-null column.
- **Features with high cardinality.** A `state` column with 50 values is one thing; a `merchant_id` column with 2 million values is a different problem (Chapter 25).
- **Features that are derived/computed by upstream systems.** These are most likely to leak.
- **The label itself.** Spend time understanding *exactly* how the label was constructed. Most leakage bugs are label-encoding bugs.

**Spend less time on:**

- **Features that are obviously low-signal and stable.** A `loan_id` column doesn't need a deep dive.
- **Features with values within the expected range and no nulls.** Note them and move on.

**Always do regardless:**

- The shape/dtypes/head triad.
- Per-column null and unique counts.
- The leakage scan.
- The class balance check (for classification).
- Time-based plots (if there's a timestamp).

A good EDA notebook is 100–300 cells. A bad one is 5 or 5000. The 5-cell version skipped everything; the 5000-cell version got lost in the weeds and never built a model. The 100–300 zone is where you have looked carefully without losing the plot.

---

## 23.13 Tools: pandas, matplotlib, and friends

The minimum useful toolset:

- **`pandas`** for data manipulation. `df.describe()`, `df.info()`, `df.isnull().sum()`, `df.value_counts()`, `df.groupby(...).agg(...)`, `df.corr()`. Learn these cold.
- **`matplotlib`** for plotting. Crude but universal. `plt.hist`, `plt.scatter`, `plt.plot`, `plt.bar`, `plt.boxplot`.
- **`seaborn`** for prettier and slightly higher-level plots. `sns.heatmap`, `sns.boxplot`, `sns.histplot`, `sns.pairplot`.
- **`pandas-profiling` / `ydata-profiling`** for an automated EDA report. Useful as a starting point but not a substitute for looking at the data.

For larger-than-memory data, you trade pandas for PySpark (Part J–K). The conceptual moves are the same; the syntax changes. `df.describe()` becomes `df.describe().show()`. `df.groupby(...).agg(...)` becomes `df.groupBy(...).agg(...)`. Histograms become a bit more painful because you have to bin manually and `collect` the result. But the *thinking* is the same.

---

## 23.14 Where this builds on / where it returns

**Builds on:**

- Chapter 5–7 (Part B): probability distributions, mean and variance, the language we use to describe what a column looks like.
- Chapter 3: the spam example introduced "look at the data" informally — this chapter makes it a discipline.

**Returns in:**

- **Chapter 24** (missing data): we *noticed* missing data in §23.4 and §23.11; Chapter 24 is what to do about it.
- **Chapter 25** (categorical encoding): we *noticed* high-cardinality categoricals; Chapter 25 covers how to encode them.
- **Chapter 26** (numerical transformations): we *noticed* skewed numeric distributions; Chapter 26 covers log/Box-Cox/scaling.
- **Chapter 27** (outliers): we *noticed* outlier values; Chapter 27 covers what to do.
- **Chapter 29** (feature selection): the leakage scan in §23.9 is a primitive form of single-feature filtering.
- **Chapter 22** (CV/leakage): the leakage detection here is the EDA-time complement to the splitting discipline in CV.
- **Every subsequent chapter** in Part E: EDA is the prerequisite step.

---

## 23.15 Exercises

1. **The "everything is fine" trap.** You read a CSV. Every column's `df.describe()` looks reasonable. There are no nulls. The class balance is 50/50. Should you proceed straight to modeling? Why or why not?

2. **Sentinel hunt.** You see a histogram of `income` with a noticeable spike at exactly $1. What are three possible explanations? How would you distinguish among them?

3. **Cardinality decision.** Your `merchant_id` column has 1.2 million unique values across 5 million rows. What does this tell you, and what should you do with the column for modeling?

4. **The leakage scan.** Why fit *single-feature* models for the leakage scan, rather than a single multi-feature model and looking at the coefficients?

5. **Boxplot interpretation.** A boxplot of `loan_amount` by `default` shows that the median is $12,000 for non-defaulters and $14,000 for defaulters, with heavy overlap in the IQRs. Is `loan_amount` a useful feature?

6. **Time-based drift.** Plotting `default` rate by month shows a sudden jump from 6% to 14% in March 2020 and a slow decline back to 8% by 2022. Name three implications for how you should train and evaluate your model.

7. **The data-owner interview.** Write out five questions you would ask the data owner about a column called `cumulative_late_payments` before using it as a feature.

8. **Conditional histograms.** You overlay the histograms of `income` for defaulters and non-defaulters. They are nearly identical. Is `income` useless? Justify briefly.

9. **Multimodality.** A histogram of `applicant_age` has two clear peaks, at 28 and at 58. What might be going on?

10. **The "0% null" surprise.** A column reports 0% null. What are at least three reasons this might be deceptive?

11. **Correlation matrix limitations.** Two numeric features have Pearson correlation of 0.02 with the target. Should you conclude they have no predictive value? What plot or test would you do next?

12. **EDA in PySpark.** Why is `df.describe().show()` more expensive in Spark than `df.describe()` is in pandas?

<details>
<summary>Answers</summary>

1. No. "Everything looks fine" is the most dangerous state of an EDA. You have not yet checked: leakage (single-feature AUC scan); time-based drift; the data owner's understanding of column semantics; whether columns are encoded as the right type (numeric vs. categorical vs. date); whether sentinel values are masquerading as real values; whether duplicates exist. A clean-looking summary statistic is necessary but not sufficient.

2. (a) Real — there's a category of "low-income" applicants reporting near-zero. (b) Sentinel — the form treats blank as $1 instead of NaN. (c) Default value — the application defaulted income to $1 when the user skipped the field. To distinguish: check whether the $1 rows correlate with other "skipped" indicators (zero employment_years, missing other fields). Also ask the data owner.

3. The column is essentially an identifier with very high cardinality (1.2M values, ~4 rows per merchant on average). One-hot encoding is impossible. Target encoding (Chapter 25) is risky with so few rows per category. Hashing (Chapter 25) is a possibility. More likely: the column is too granular to use directly, and you should look for hierarchical features (merchant category, merchant geography) that aggregate to something usable. Or treat it like a primary key and drop it.

4. A multi-feature model with regularization will *spread* attribution across correlated features, masking the offender. A single-feature model isolates each feature's standalone predictive power, which is the right diagnostic for "is this feature suspiciously good on its own?" Leakage features typically have very high standalone AUC because they encode the label directly.

5. Marginally. The $2K median difference is signal, but the heavy overlap in IQRs means it's a weak feature on its own. It may be useful in combination with other features (interactions — Chapter 28) or after a transformation (log — Chapter 26). Don't drop it yet.

6. (a) A random train/test split will mix pre- and post-COVID data, hiding the model's failure to handle the regime change. Use a time-based split. (b) The model needs a feature that captures the temporal regime (e.g., a "post-COVID" indicator or a continuous time feature) — or you train separate models per regime. (c) Production performance will likely drift as the regime continues to evolve. Set up monitoring (Chapter 3 §3.12, Part L) to catch it.

7. Examples: (1) "Cumulative over what window? Loan lifetime? Last 12 months? Origination-to-now?" (2) "Is this updated as new late payments happen, or frozen at some point in time?" (3) "Is this available *at the time of application* or only computed later?" (4) "What's the definition of 'late' — 30 days past due? 60? 90?" (5) "Are there imputation rules — e.g., what value does this take for borrowers with no payment history?"

8. Probably yes — at least, *marginally* useless. But "feature interactions" can rescue a marginally useless feature: maybe `income / loan_amount` is informative even if `income` alone is not. Don't drop in EDA; the model will decide.

9. Possibly two subpopulations: young first-time borrowers (peak at 28) and older borrowers refinancing or consolidating (peak at 58). A multimodal distribution is a strong hint that a categorical feature exists that you haven't yet identified — finding it will probably help your model.

10. (a) Nulls are encoded as a sentinel value like `-1` or `"unknown"` instead of `NaN`. (b) The data was filtered upstream to exclude null rows (selection bias — what *kind* of rows were excluded?). (c) The pipeline silently imputes nulls before they reach you (you don't know what was originally null). (d) The column is computed from other columns by a deterministic rule that never produces null. None of these mean "the data is clean" — they mean "you need to investigate further."

11. No. Pearson measures only *linear* monotonic correlation. A feature with a U-shaped relationship (e.g., the default rate is high for very low and very high incomes) will have near-zero Pearson r despite being highly informative. Next steps: scatter plot (to see the shape); mutual information (which captures nonlinear dependence — Chapter 29); a single-feature decision tree (will split on it if there's any signal).

12. `df.describe()` in pandas is a single-machine, single-pass operation over an in-memory DataFrame — fast. In Spark, it triggers a distributed job: every executor reads its partition from storage, computes local statistics, and the driver aggregates them. The cost is distributed I/O plus shuffling for global aggregates. For a 100GB dataset, this can take minutes vs. milliseconds for an in-memory pandas frame.

</details>
