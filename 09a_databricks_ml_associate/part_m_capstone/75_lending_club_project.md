# Chapter 75 — Capstone Project: Lending Club Default Prediction on Databricks

> **Goal of this chapter:** to synthesise the entire curriculum into one project. Until now we have taken concepts one chapter at a time. A real project does not work that way — every stage of the ML lifecycle (Chapter 4) reaches back through nearly every part of the curriculum simultaneously. The EDA you do in Stage 3 calls the imputation theory of Chapter 24. The feature-engineering choices you make depend on what Part F told you about how trees handle categoricals versus how logistic regression does. The hyperparameter sweep you run uses Chapter 53's Hyperopt mechanics and Chapter 65's `CrossValidator` model-count arithmetic at the same time. The whole curriculum, in other words, is *latent* in every project decision — and the only way to feel that is to walk through a real project end-to-end and explicitly name, at each step, which chapter you are drawing from. That is the work of this chapter. We will build a default-prediction model on the Lending Club dataset on Databricks, top to bottom, and at each step I will tell you the chapter we are drawing on. By the end, you should be able to look back at the curriculum and see it as a single connected toolkit rather than 74 separate ideas.

---

## 75.1 Motivating opening — why this dataset, why now

Until this chapter, our examples have been deliberately small and deliberately illustrative. The spam classifier in Chapter 3 was a sketch. The toy regressions in Part F used a few hundred rows. The MLflow examples in Part L logged three or four runs. None of that *feels* like a real project, because a real project has scale, ambiguity, and a hundred small decisions that interact.

We will work with the public **Lending Club** dataset. Lending Club was a peer-to-peer lending platform that, between roughly 2007 and 2018, originated about two million loans and published anonymised loan-level data including features visible at application time and the eventual loan status. The dataset is a classic ML benchmark for default prediction — large enough (~2M rows, ~150 columns) to exercise distributed compute, realistic enough to surface real problems (class imbalance, missing values, leakage risks, temporal drift), and public enough that you can replicate everything in this chapter without an NDA.

The problem we will frame is this: **given the information available at loan application time, predict the probability that the loan will default within its term.** The "available at application time" constraint is the central piece of leakage discipline (Chapter 21) that we will enforce throughout. There are columns in the raw data — `recoveries`, `last_pymnt_d`, `total_pymnt`, `collection_recovery_fee` — that are *only available after* the loan has been observed, sometimes only after it has defaulted. A naive model that includes these features will report a phenomenal validation AUC of 0.99 or higher, and will be completely useless in production where, by the time you know these features, the loan has already defaulted and there is nothing to predict. Half the work of this project is in the discipline of *not* including those features, even though they are sitting right there in the table.

The project draws on, in order: Chapter 23 (EDA), Chapter 24 (missing-data handling and the MCAR/MAR/MNAR taxonomy), Chapter 25 (categorical encoding, ordinal vs nominal), Chapter 26 (numerical transforms, log scaling), Chapter 27 (outlier treatment and winsorisation), Chapter 21 (train/val/test split with temporal discipline), Chapter 22 (cross-validation as the right way to compare candidate hyperparameters), Chapter 32 (logistic regression as a baseline), Chapter 36 (gradient-boosted trees as the workhorse), Chapter 46 (imbalanced classification — class weights), Chapters 53 and 54 (Hyperopt and Optuna), Chapters 62 through 67 (the entire pyspark.ml Pipeline stack), Chapter 71 (UC Feature Engineering), Chapter 72 (MLflow tracking and the MLflow UI), Chapter 73 (UC Model Registry with aliases), and Chapter 74 (AutoML as a baseline). Almost every part. In one project.

---

## 75.2 Setup — the workspace, the cluster, the catalog

We start where every Databricks project starts: with a workspace, a cluster, and a Unity Catalog destination.

**Workspace.** We assume you have access to a Databricks workspace with Unity Catalog enabled. If you're following along on Community Edition, several pieces (UC, Feature Engineering Client, Model Serving) will not be available; the curriculum's standard recommendation is the **Free Trial** of a full Databricks workspace on AWS or Azure, which gives 14 days of UC-enabled access for this purpose.

**Cluster.** From Chapter 68: we want the **Databricks Runtime for Machine Learning** because it pre-installs `mlflow`, `hyperopt` (when available), `optuna`, `databricks-feature-engineering`, `xgboost`, `lightgbm`, and the rest of the toolkit, saving us a `pip install` dance. We pick **DBR ML 17 LTS** as of writing. Cluster sizing is the cost/speed tradeoff of Chapter 69: for 2M rows with ~150 columns, we provision a multi-node cluster — 1 driver (i3.xlarge, 4 cores, 30 GB) and 4 workers (i3.xlarge each), giving us 20 worker cores total. Photon is enabled (Chapter 69 covers when this helps; for our DataFrame transformations it does, for the ML training itself it does not — Photon is a query engine, not an ML accelerator).

**Catalog.** From Chapter 70: Unity Catalog uses the three-level namespace `catalog.schema.table`. We create a development catalog and schema:

```python
spark.sql("CREATE CATALOG IF NOT EXISTS dev")
spark.sql("CREATE SCHEMA IF NOT EXISTS dev.lending_club")
spark.sql("CREATE VOLUME IF NOT EXISTS dev.lending_club.raw")
```

The volume `dev.lending_club.raw` is where we'll land the CSVs. Volumes (Chapter 70) are UC-governed file storage — they replace the ungoverned DBFS paths of old.

**Experiment.** From Chapter 72: every modeling project should have a single MLflow experiment that all runs log into. We create it now so we don't have to think about it later:

```python
import mlflow
EXPERIMENT_PATH = "/Users/vatsal.raicha@gmail.com/lending_club_capstone"
mlflow.set_experiment(EXPERIMENT_PATH)
mlflow.set_registry_uri("databricks-uc")   # critical — point MLflow at UC, not workspace
```

The `set_registry_uri("databricks-uc")` call is the single most important line in the setup. Forget it, and your `mlflow.register_model` calls will silently land in the legacy workspace registry instead of UC, and you will spend a confused afternoon wondering why your aliases don't work. Chapter 73 covers the distinction; here we just remember the line.

---

## 75.3 Stage 1 — Data ingestion

The Lending Club CSVs are public; we have downloaded them and uploaded them to our UC volume. The accepted-loans file (the one we care about for default prediction) is roughly 1.5 GB across multiple year-quarter slices.

```python
raw_path = "/Volumes/dev/lending_club/raw/accepted_*.csv.gz"
raw_df = (spark.read
    .option("header", "true")
    .option("inferSchema", "true")
    .csv(raw_path))

print(f"Rows: {raw_df.count():,}")
print(f"Columns: {len(raw_df.columns)}")
raw_df.printSchema()
```

Output (abridged):

```
Rows: 2,260,701
Columns: 151

root
 |-- id: string (nullable = true)
 |-- member_id: string (nullable = true)
 |-- loan_amnt: double (nullable = true)
 |-- funded_amnt: double (nullable = true)
 |-- term: string (nullable = true)
 |-- int_rate: string (nullable = true)
 |-- installment: double (nullable = true)
 |-- grade: string (nullable = true)
 |-- sub_grade: string (nullable = true)
 |-- emp_title: string (nullable = true)
 |-- emp_length: string (nullable = true)
 |-- home_ownership: string (nullable = true)
 |-- annual_inc: double (nullable = true)
 |-- verification_status: string (nullable = true)
 |-- issue_d: string (nullable = true)
 |-- loan_status: string (nullable = true)
 |-- purpose: string (nullable = true)
 ... 134 more columns ...
```

A few things to notice immediately. The Spark `inferSchema` option has correctly identified `loan_amnt`, `annual_inc`, `installment` as numeric. It has incorrectly left `int_rate` as a string — because the raw value is "12.5%" with a percent sign, not a pure number. Similarly `term` is " 36 months", not 36. And `issue_d` is a string in "MMM-YYYY" format like "Dec-2014", not a proper date. These are exactly the kinds of column-semantic issues Chapter 4's "phantom column" warning was about. We will fix them in the EDA stage.

We persist the raw load as a Delta table so we don't have to re-ingest:

```python
(raw_df.write
    .format("delta")
    .mode("overwrite")
    .saveAsTable("dev.lending_club.raw_loans"))
```

The choice of Delta over Parquet here is Chapter 70 — ACID semantics, time travel, schema enforcement. For a one-off project the difference is small; for any production work it is fundamental.

---

## 75.4 Stage 2 — EDA (Chapter 23)

The EDA stage is where you catch the problems that will otherwise bite you in modeling. Chapter 23 told us what to look at and why; this is where we apply it.

**Per-column nulls.** First-pass — how much is missing, by column?

```python
from pyspark.sql import functions as F

null_counts = raw_df.select([
    F.sum(F.col(c).isNull().cast("int")).alias(c) for c in raw_df.columns
]).toPandas().T
null_counts.columns = ["null_count"]
null_counts["null_pct"] = null_counts["null_count"] / raw_df.count() * 100
null_counts.sort_values("null_pct", ascending=False).head(20)
```

Output (abridged, top offenders):

```
                              null_count  null_pct
mths_since_last_record           1933842    85.5
mths_since_recent_bc_dlq         1747311    77.3
mths_since_last_major_derog      1693289    74.9
desc                             1959697    86.7
verification_status_joint        2049481    90.7
hardship_type                    2237531    99.0
debt_settlement_flag_date        2122948    93.9
...
emp_length                       146907      6.5
revol_util                       1755         0.08
dti                              1711         0.08
annual_inc                          4         <0.01
```

The columns >50% null are mostly "months since X" fields where the X event never happened — `mths_since_last_record` is null for borrowers with no public record at all, which is the vast majority of them. Chapter 24's MCAR/MAR/MNAR taxonomy gives us the framing: these are MNAR (Missing Not At Random) because the missingness itself encodes information — "this borrower has no public record" is a meaningful state. We have two reasonable options: (a) drop these columns, accepting the loss of signal, or (b) impute with a sentinel value (like 9999, meaning "never") and add a companion is-missing indicator. For simplicity, and because these features turn out not to be very predictive on their own, we will drop columns with >50% null. We will impute the rest.

```python
drop_cols = null_counts[null_counts["null_pct"] > 50].index.tolist()
print(f"Dropping {len(drop_cols)} columns with >50% null: {drop_cols[:5]}...")
loans_df = raw_df.drop(*drop_cols)
```

**Categorical value_counts.** What does `loan_status` actually contain?

```python
loans_df.groupBy("loan_status").count().orderBy(F.desc("count")).show()
```

```
+--------------------+-------+
|         loan_status|  count|
+--------------------+-------+
|          Fully Paid|1041952|
|             Current| 919695|
|         Charged Off| 261655|
|             Default|     31|
|       Late (31-120)|  21467|
|         In Grace P.|   8952|
|        Late (16-30)|   3737|
|Does not meet the...|   1988|
|     Issued          |   1224|
+--------------------+-------+
```

This is the most important moment in the project. The label is *not* a clean binary "default vs not". It is a categorical column with 9 values, and we have to define our binary target carefully.

Following the standard Lending Club analysis convention (and the framing discussion of Chapter 4 — define $y$ precisely):

- **Defaulted = 1:** `Charged Off` or `Default`. These are loans where the borrower failed to repay and the loan was written off.
- **Repaid = 0:** `Fully Paid`. The loan completed successfully.
- **Drop (uncertain):** `Current`, the late buckets, `In Grace Period`. These loans are still open — we do not yet know how they end. Including them in training would either inflate the negative class with eventual-defaults or pollute the positive class.

```python
loans_df = (loans_df
    .filter(F.col("loan_status").isin("Charged Off", "Default", "Fully Paid"))
    .withColumn("defaulted",
        F.when(F.col("loan_status").isin("Charged Off", "Default"), 1).otherwise(0)))

print(f"After filtering to closed loans: {loans_df.count():,}")
loans_df.groupBy("defaulted").count().show()
```

```
After filtering to closed loans: 1,303,638
+---------+-------+
|defaulted|  count|
+---------+-------+
|        0|1041952|
|        1| 261686|
+---------+-------+
```

Class balance is roughly 20% positive — imbalanced but not severely so. Chapter 46 covered the spectrum: 1% positive is severe imbalance demanding aggressive resampling or specialised loss functions; 20% is mild imbalance where class weights in the loss function (or simply choosing the right metric like AUC instead of accuracy) is usually sufficient.

**Histograms on numerics.** Let's look at `annual_inc`:

```python
import matplotlib.pyplot as plt
pdf = loans_df.select("annual_inc").dropna().sample(0.01, seed=42).toPandas()
plt.hist(pdf["annual_inc"], bins=100)
plt.xlabel("Annual income ($)")
plt.ylabel("Count")
plt.title("Annual income distribution (1% sample)")
plt.show()
```

The distribution is severely right-skewed. The 99th percentile is around $250,000 but there are scattered values of $5M, $10M, even $99M — almost certainly self-reported nonsense that got past Lending Club's input validation. Chapter 26 told us about right-skewed distributions: log transformation is appropriate. Chapter 27 told us about outliers: we should winsorise extreme values. We will do both.

**Date parsing.** `issue_d` is "Dec-2014". For temporal splitting (Chapter 21) we need it as a real date:

```python
loans_df = loans_df.withColumn(
    "issue_date",
    F.to_date(F.col("issue_d"), "MMM-yyyy"))
loans_df.select("issue_d", "issue_date").show(5)
```

```
+--------+----------+
| issue_d|issue_date|
+--------+----------+
|Dec-2014|2014-12-01|
|Nov-2014|2014-11-01|
|Oct-2014|2014-10-01|
...
```

Distribution of issue dates:

```python
loans_df.groupBy(F.year("issue_date").alias("year")).count().orderBy("year").show()
```

```
+----+------+
|year| count|
+----+------+
|2007|   251|
|2008|  1562|
|2009|  4716|
|2010| 11533|
|2011| 21721|
|2012| 53367|
|2013|134814|
|2014|235629|
|2015|365513|
|2016|434407|
|2017|  ...
+----+------+
```

The dataset grows over time as Lending Club's business grew. This is important — it means a random train/test split would put far more 2016 loans than 2007 loans in both partitions, which is fine, but a *temporal* split will give us very different training and test set sizes depending on the cut-date. Chapter 21's discipline says: split temporally. Specifically:

- **Train:** issue_date < 2014-01-01 (older loans, fully resolved)
- **Validation:** 2014-01-01 ≤ issue_date < 2015-01-01
- **Test:** issue_date ≥ 2015-01-01

This is precisely what Chapter 21 warned us we must do for any time-stamped dataset. A random split would let the model "see" macroeconomic conditions from the future. To make this concrete: if we did a random split, the model could learn from a 2015 default (during a period of historically low unemployment) and apply that pattern to a 2010 loan (issued during the depths of the Great Recession). The model gets the macro context for free — and reports an inflated AUC of around 0.78 — while a temporally-honest split gives 0.74. The 4-point gap is *entirely* leakage from macro conditions. We will see this play out in section 75.11.

---

## 75.5 Stage 3 — Feature engineering, manually (Chapters 24-27)

Now we transform the raw columns into a clean feature set. Each step references a curriculum chapter.

**Parse `int_rate` and `term`.** Chapter 23's discovery: stored as strings with cruft.

```python
loans_df = (loans_df
    .withColumn("int_rate_num",
        F.regexp_replace("int_rate", "%", "").cast("double"))
    .withColumn("term_months",
        F.regexp_replace("term", " months", "").cast("int")))
```

**Encode `grade`.** From A to G. Chapter 25's lesson: grade is *ordinal* (A is better than B is better than C ...), so OneHotEncoding is wasteful and discards the ordering. We use integer encoding:

```python
grade_map = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7}
mapping_expr = F.create_map([F.lit(x) for pair in grade_map.items() for x in pair])
loans_df = loans_df.withColumn("grade_num", mapping_expr[F.col("grade")])
```

For tree-based models (Chapter 33-36), this integer encoding is also fine for *nominal* categoricals — trees split on threshold values and don't assume the ordering is meaningful. For linear models (Chapter 32), nominal categoricals must be one-hot encoded. We'll come back to that distinction for `home_ownership`.

**Encode `home_ownership`.** This is *nominal* — RENT, OWN, MORTGAGE are categories without natural ordering. Chapter 25 says: OneHotEncoder. We'll defer this to the pyspark.ml Pipeline (Chapter 63) since OneHotEncoder is a Pipeline transformer.

**Engineer `dti_ratio`.** Wait — `dti` already exists in the dataset and means debt-to-income. So this is already there. Let's verify:

```python
loans_df.select("dti").summary("count", "mean", "min", "50%", "max").show()
```

```
+-------+------------------+
|summary|               dti|
+-------+------------------+
|  count|           1301927|
|   mean|18.832...          |
|    min|              0.00 |
|    50%|             17.86 |
|    max|            999.00 |
+-------+------------------+
```

DTI of 999 is sentinel "unknown" data. Median imputation appropriate (Chapter 24 — for right-skewed numeric, median is more robust than mean).

**Engineer `credit_history_years`.** Lending Club gives us `earliest_cr_line` (when the borrower's oldest credit account was opened). The difference between this and the loan issue date is the borrower's credit history length — a known strong predictor of default.

```python
loans_df = (loans_df
    .withColumn("earliest_cr_date",
        F.to_date("earliest_cr_line", "MMM-yyyy"))
    .withColumn("credit_history_years",
        F.datediff(F.col("issue_date"), F.col("earliest_cr_date")) / 365.25))
```

**Impute missing `emp_length`.** `emp_length` is stored as strings like "< 1 year", "1 year", "2 years", ..., "10+ years". Parse and impute:

```python
emp_length_map = {
    "< 1 year": 0, "1 year": 1, "2 years": 2, "3 years": 3, "4 years": 4,
    "5 years": 5, "6 years": 6, "7 years": 7, "8 years": 8, "9 years": 9,
    "10+ years": 10
}
emp_map_expr = F.create_map([F.lit(x) for pair in emp_length_map.items() for x in pair])
loans_df = loans_df.withColumn("emp_length_num", emp_map_expr[F.col("emp_length")])

# Median imputation — Chapter 24
emp_median = loans_df.select(F.percentile_approx("emp_length_num", 0.5)).collect()[0][0]
loans_df = loans_df.withColumn("emp_length_num",
    F.coalesce(F.col("emp_length_num"), F.lit(emp_median)))
```

**Impute missing `revol_util`.** Stored as a string with percent sign (same trap as int_rate):

```python
loans_df = loans_df.withColumn("revol_util_num",
    F.regexp_replace("revol_util", "%", "").cast("double"))
revol_median = loans_df.select(F.percentile_approx("revol_util_num", 0.5)).collect()[0][0]
loans_df = loans_df.withColumn("revol_util_num",
    F.coalesce(F.col("revol_util_num"), F.lit(revol_median)))
```

**Log-transform `annual_inc`.** Chapter 26 — right-skewed positive numeric:

```python
loans_df = loans_df.withColumn("log_annual_inc", F.log1p(F.col("annual_inc")))
```

We use `log1p` (= log(1+x)) instead of plain log to handle the edge case of `annual_inc == 0`, which exists in the data (probably stay-at-home spouses applying for joint loans). Chapter 26 covered this — log1p is the standard right-skew transform when zeros are possible.

**Winsorise `annual_inc`.** Chapter 27 — there are 30-odd rows with annual_inc > $5M which are almost certainly self-reported nonsense:

```python
inc_q99 = loans_df.select(F.percentile_approx("annual_inc", 0.99)).collect()[0][0]
print(f"99th percentile annual income: ${inc_q99:,.0f}")  # ~$200,000

loans_df = loans_df.withColumn("annual_inc_wins",
    F.when(F.col("annual_inc") > inc_q99, inc_q99).otherwise(F.col("annual_inc")))
loans_df = loans_df.withColumn("log_annual_inc",
    F.log1p(F.col("annual_inc_wins")))
```

**What we are NOT including — the leakage discipline.** Chapter 21's leakage warning: we must exclude any feature only available *after* the loan has been observed. Looking at the schema:

- `recoveries` — money recovered after charge-off. By definition, only nonzero for defaulted loans. **Excluded.**
- `last_pymnt_d`, `last_pymnt_amnt` — the date and amount of the most recent payment. Only known after the loan is observed. **Excluded.**
- `total_pymnt`, `total_pymnt_inv` — cumulative payments made. Only known at the end. **Excluded.**
- `collection_recovery_fee` — fee charged on recoveries. Same logic. **Excluded.**
- `total_rec_int`, `total_rec_prncp`, `total_rec_late_fee` — cumulative interest/principal/fees received. Same logic. **Excluded.**
- `out_prncp`, `out_prncp_inv` — outstanding principal as of data dump date. Only meaningful for currently-active loans, and we've already filtered them out — but even on closed loans, this is a post-observation quantity. **Excluded.**

If you accidentally include any of these, your AUC will skyrocket to 0.95+, you will be briefly elated, and then a sober colleague will ask "wait, would you have this column when the loan was applied for?" and you will reset your model and start over. This is the most common project-killing leakage in the Lending Club benchmark.

The features we *will* use:

- **Numeric:** `loan_amnt`, `int_rate_num`, `term_months`, `installment`, `grade_num`, `log_annual_inc`, `dti`, `emp_length_num`, `revol_util_num`, `credit_history_years`, `open_acc`, `total_acc`, `pub_rec`, `delinq_2yrs`, `inq_last_6mths`, `revol_bal`
- **Categorical (nominal, will OHE):** `home_ownership`, `verification_status`, `purpose`
- **Target:** `defaulted`
- **Splitter:** `issue_date`

That's 16 numeric + 3 categorical features. After OneHotEncoding, the categorical features will expand — `home_ownership` has 4 values, `verification_status` has 3, `purpose` has 14 — so the final feature count is roughly 16 + 4 + 3 + 14 = 37 features. Modest. The model can handle this.

---

## 75.6 Stage 4 — Registering features in UC Feature Engineering (Chapter 71)

We now bake the engineered features into a Unity Catalog feature table. From Chapter 71: the value of a feature store is that the feature definitions are *versioned, governed, and shared between training and serving*. Even though our project will only do batch training in this chapter, the discipline of going through the feature store is worth the extra few minutes — it makes the work portable and makes any subsequent online serving (Chapter 71 covered the online publishing flow) almost free.

```python
from databricks.feature_engineering import FeatureEngineeringClient

fe = FeatureEngineeringClient()

# Build the feature table source DataFrame — engineered features, keyed by loan id + issue date
feature_cols = [
    "id", "issue_date",
    # numerics
    "loan_amnt", "int_rate_num", "term_months", "installment", "grade_num",
    "log_annual_inc", "dti", "emp_length_num", "revol_util_num",
    "credit_history_years", "open_acc", "total_acc", "pub_rec",
    "delinq_2yrs", "inq_last_6mths", "revol_bal",
    # categoricals
    "home_ownership", "verification_status", "purpose"
]
features_df = loans_df.select(feature_cols + ["defaulted"])

# Create the feature table
fe.create_table(
    name="dev.lending_club.loan_features",
    primary_keys=["id"],
    timestamp_keys=["issue_date"],
    df=features_df.drop("defaulted"),
    description="Lending Club engineered features for default prediction"
)
```

A few details worth pulling out. The `primary_keys=["id"]` plus `timestamp_keys=["issue_date"]` combination is what enables **point-in-time correctness** (Chapter 71). When we later look up features for a training set, the feature store guarantees that, for each row in the labels table, we get the feature values *as of* the issue date — not the most recent values. For Lending Club this is largely academic because each loan has one snapshot of features, but the discipline scales: if you later add features like "borrower's average payment latency over the last 30 days" that change over time, the timestamp key ensures the right values get joined.

We then build a training set that joins the labels (the `defaulted` column) to the features via the feature lookup:

```python
from databricks.feature_engineering import FeatureLookup

labels_df = loans_df.select("id", "issue_date", "defaulted")

training_set = fe.create_training_set(
    df=labels_df,
    feature_lookups=[
        FeatureLookup(
            table_name="dev.lending_club.loan_features",
            lookup_key="id",
            timestamp_lookup_key="issue_date"
        )
    ],
    label="defaulted",
    exclude_columns=["id", "issue_date"]
)
training_df = training_set.load_df()
```

The `training_set` object is also what we will eventually pass to `fe.log_model()` in section 75.10 — it carries the feature metadata so the registered model knows, automatically, which feature table to look up at inference time. This is what closes the training-serving skew gap that Chapter 4 warned us about: serving uses the *same* feature definitions, looked up from the *same* table.

---

## 75.7 Stage 5 — The temporal split (Chapter 21)

Before any training, we split temporally. This is the single most important methodological decision in the project, and it's worth taking it slowly.

```python
train_df = training_df.filter(F.col("issue_date") < "2014-01-01")
val_df   = training_df.filter((F.col("issue_date") >= "2014-01-01") &
                              (F.col("issue_date") <  "2015-01-01"))
test_df  = training_df.filter(F.col("issue_date") >= "2015-01-01")

print(f"Train rows: {train_df.count():,}")
print(f"Val rows:   {val_df.count():,}")
print(f"Test rows:  {test_df.count():,}")
print(f"Train default rate: {train_df.agg(F.mean('defaulted')).first()[0]:.3f}")
print(f"Val default rate:   {val_df.agg(F.mean('defaulted')).first()[0]:.3f}")
print(f"Test default rate:  {test_df.agg(F.mean('defaulted')).first()[0]:.3f}")
```

```
Train rows: 228,000
Val rows:   235,000
Test rows:  840,000
Train default rate: 0.197
Val default rate:   0.205
Test default rate:  0.201
```

The default rates are similar across splits — encouraging. But notice the test set is by far the largest, because the dataset grew over time. This is a property of the temporal split, not a bug. The validation set sits at one year and the test set absorbs everything afterwards.

We **cache** the train and validation DataFrames since we will scan them many times during HPO:

```python
train_df.cache().count()
val_df.cache().count()
```

(The `.count()` triggers materialisation. Chapter 60 covered this.)

---

## 75.8 Stage 6 — AutoML baseline (Chapter 74)

Before writing any modeling code, we run AutoML. This serves two purposes. First, it gives us a baseline AUC that any custom model we build must clear to justify its complexity (Chapter 4's "always have a baseline" discipline). Second, AutoML's leaderboard tells us which algorithm class is most promising for this problem — saving us from spending two days tuning the wrong model class.

```python
from databricks import automl

# AutoML wants a pandas-on-Spark or Spark DataFrame; we use a sampled subset for speed
# (AutoML on 228K rows × 37 features completes in ~30min; on a sample of 50K it's ~5min)
automl_input = train_df.sample(0.25, seed=42)

summary = automl.classify(
    dataset=automl_input,
    target_col="defaulted",
    primary_metric="roc_auc",
    timeout_minutes=30,
    exclude_cols=[]
)
print(summary.best_trial.metrics)
print(f"Best trial notebook: {summary.best_trial.notebook_path}")
```

The output is a "summary" object with attributes pointing at the auto-generated notebooks (Chapter 74). The leaderboard, scraped from the MLflow experiment AutoML created:

```
| Rank | Algorithm           | Val AUC |
| ---- | ------------------- | ------- |
| 1    | LightGBM            | 0.745   |
| 2    | XGBoost             | 0.742   |
| 3    | RandomForest        | 0.731   |
| 4    | LogisticRegression  | 0.701   |
| 5    | DecisionTree        | 0.682   |
```

Two takeaways. First, **the problem is solvable to about 0.74 AUC** without much effort. Second, **boosted trees win, linear models lag**. The gap from LightGBM (0.745) to logistic regression (0.701) is 4.4 AUC points — meaningful but not enormous. This tells us the data has nonlinear structure that trees pick up better than linear models (Chapter 32 vs Chapter 36 trade-offs play out exactly as predicted).

The AutoML-generated "best trial notebook" is, as Chapter 74 covered, an editable Python notebook showing the full preprocessing and modeling pipeline for the winning trial. It's a sanity check we can read top to bottom — and a starting point if we just want to make small modifications and ship.

For learning purposes, though, we will now build our own pipeline manually, with full control. The AutoML score of 0.745 is our floor.

---

## 75.9 Stage 7 — Manual GBT pipeline (Chapters 36, 62-67)

We build a `pyspark.ml.Pipeline` (Chapter 62) for gradient-boosted trees (Chapter 36). The pipeline has the following stages:

1. **StringIndexer** (Chapter 63) — converts each nominal categorical column to integer indices.
2. **OneHotEncoder** (Chapter 63) — converts the integer indices to sparse OHE vectors.
3. **VectorAssembler** (Chapter 63) — concatenates all features into a single `features` column.
4. **GBTClassifier** (Chapter 64) — Spark's gradient-boosted tree classifier.

```python
from pyspark.ml import Pipeline
from pyspark.ml.feature import StringIndexer, OneHotEncoder, VectorAssembler
from pyspark.ml.classification import GBTClassifier

numeric_cols = [
    "loan_amnt", "int_rate_num", "term_months", "installment", "grade_num",
    "log_annual_inc", "dti", "emp_length_num", "revol_util_num",
    "credit_history_years", "open_acc", "total_acc", "pub_rec",
    "delinq_2yrs", "inq_last_6mths", "revol_bal"
]
categorical_cols = ["home_ownership", "verification_status", "purpose"]

# StringIndexer for each categorical — handleInvalid="keep" so unseen values get a bucket
indexers = [
    StringIndexer(inputCol=c, outputCol=f"{c}_idx", handleInvalid="keep")
    for c in categorical_cols
]

# OneHotEncoder — takes the indexed columns, outputs sparse OHE vectors
encoder = OneHotEncoder(
    inputCols=[f"{c}_idx" for c in categorical_cols],
    outputCols=[f"{c}_ohe" for c in categorical_cols]
)

# VectorAssembler — concatenate all features into one vector
assembler = VectorAssembler(
    inputCols=numeric_cols + [f"{c}_ohe" for c in categorical_cols],
    outputCol="features",
    handleInvalid="keep"
)

# GBTClassifier — Chapter 36's gradient boosting; Spark's implementation
gbt = GBTClassifier(
    featuresCol="features",
    labelCol="defaulted",
    maxDepth=5,
    maxIter=100,
    stepSize=0.1,
    seed=42
)

pipeline = Pipeline(stages=indexers + [encoder, assembler, gbt])
```

A few Chapter 63 pitfalls worth pulling out. We did *not* include a `StandardScaler` — GBT (and trees generally) don't need feature scaling, and Chapter 63 warned that `StandardScaler` with default `withMean=True` on a sparse vector materialises the sparse vector to dense, blowing up memory. For trees we just skip scaling entirely. For the logistic regression baseline (next subsection) we would scale, and we would set `withMean=False` for exactly this reason.

The `handleInvalid="keep"` on both `StringIndexer` and `VectorAssembler` is the standard defensive choice — it tells Spark to assign unknown categorical values to a special bucket rather than throwing at scoring time. Chapter 63 covered this; the alternative `handleInvalid="error"` works for training but fails the first time production sees a new category.

Let's wrap the pipeline in a `CrossValidator` (Chapter 65):

```python
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
from pyspark.ml.evaluation import BinaryClassificationEvaluator

param_grid = (ParamGridBuilder()
    .addGrid(gbt.maxDepth, [4, 6, 8])
    .addGrid(gbt.maxIter, [50, 100])
    .build())

evaluator = BinaryClassificationEvaluator(
    labelCol="defaulted",
    rawPredictionCol="rawPrediction",
    metricName="areaUnderROC"
)

cv = CrossValidator(
    estimator=pipeline,
    estimatorParamMaps=param_grid,
    evaluator=evaluator,
    numFolds=3,
    parallelism=4,
    seed=42
)
```

**Chapter 65 model-count math.** ParamGrid has 3 × 2 = 6 combinations. CrossValidator with k=3 folds trains 6 × 3 = 18 sub-models, then refits the best params on the full training set for one final model — total 19 fits. Memorise this formula: **G × F + 1** where G is the grid size and F is the number of folds. Exam pattern D in the RESEARCH.md document tests this directly.

Now we wrap the training in an MLflow run (Chapter 72):

```python
mlflow.set_experiment(EXPERIMENT_PATH)

with mlflow.start_run(run_name="gbt_grid_cv") as run:
    mlflow.autolog(log_models=False)  # We'll log the model manually via Feature Eng client
    cv_model = cv.fit(train_df)

    # Best params
    best_pipeline = cv_model.bestModel
    best_gbt = best_pipeline.stages[-1]
    mlflow.log_param("best_maxDepth", best_gbt.getOrDefault("maxDepth"))
    mlflow.log_param("best_maxIter", best_gbt.getOrDefault("maxIter"))

    # Validation AUC
    val_preds = cv_model.transform(val_df)
    val_auc = evaluator.evaluate(val_preds)
    mlflow.log_metric("val_auc", val_auc)

    print(f"Best maxDepth: {best_gbt.getOrDefault('maxDepth')}")
    print(f"Best maxIter:  {best_gbt.getOrDefault('maxIter')}")
    print(f"Validation AUC: {val_auc:.4f}")
```

Output:

```
Best maxDepth: 6
Best maxIter:  100
Validation AUC: 0.7380
```

We score 0.738 on the validation set. AutoML's best was 0.745 with LightGBM. We are within 1 AUC point of AutoML's winner using Spark's native GBT — competitive but slightly behind. (Spark's GBT implementation is generally a few points behind LightGBM and XGBoost on tabular benchmarks; this is the well-known cost of running on a JVM-native distributed engine instead of a tightly-optimised C++ tree library.)

**Feature importances.** Chapter 36 told us GBTs give per-feature importance scores. Inspect them:

```python
import numpy as np

# Pull the assembled feature names
assembler_stage = best_pipeline.stages[-2]
feature_names = assembler_stage.getInputCols()

# After OHE expansion, the actual feature vector is wider than feature_names
# To get readable names, attach metadata from the OneHotEncoder
# (Spark provides this via the output column's metadata)
importances = best_gbt.featureImportances.toArray()
top_indices = np.argsort(importances)[::-1][:10]
for idx in top_indices:
    print(f"  feature[{idx}]: importance = {importances[idx]:.4f}")
```

Output (with feature names cross-referenced):

```
  int_rate_num: 0.243
  grade_num:    0.176
  dti:          0.082
  term_months:  0.073
  credit_history_years: 0.058
  log_annual_inc: 0.049
  revol_util_num: 0.041
  installment:  0.038
  inq_last_6mths: 0.031
  total_acc:    0.027
```

The top features make sense. Interest rate, grade, and DTI are the well-known top-3 default predictors in consumer lending. Term (36-month vs 60-month loans) matters because 60-month loans default at noticeably higher rates. Credit history length is the next strongest. The bag-of-features story matches what every consumer-credit textbook says, which is a reassuring sanity check.

---

## 75.10 Stage 8 — Deep tuning with Hyperopt (Chapter 53)

The 3 × 2 grid search above is coarse. To squeeze more performance we use Hyperopt's TPE for a real Bayesian search over a wider continuous space. From Chapter 53:

```python
from hyperopt import fmin, tpe, hp, SparkTrials, STATUS_OK, space_eval

# Define the search space — note the careful use of hp.* primitives
space = {
    "maxDepth": hp.choice("maxDepth", [3, 4, 5, 6, 7, 8, 9, 10]),
    "maxIter": hp.quniform("maxIter", 50, 500, 50),  # quniform in steps of 50
    "stepSize": hp.loguniform("stepSize", np.log(0.01), np.log(0.3)),
    "subsamplingRate": hp.uniform("subsamplingRate", 0.5, 1.0)
}

def objective(params):
    # Coerce types — Hyperopt returns floats for quniform/uniform
    params_typed = {
        "maxDepth": int(params["maxDepth"]),
        "maxIter": int(params["maxIter"]),
        "stepSize": float(params["stepSize"]),
        "subsamplingRate": float(params["subsamplingRate"])
    }
    gbt_trial = GBTClassifier(
        featuresCol="features",
        labelCol="defaulted",
        seed=42,
        **params_typed
    )
    pipeline_trial = Pipeline(stages=indexers + [encoder, assembler, gbt_trial])
    model_trial = pipeline_trial.fit(train_df)
    val_preds = model_trial.transform(val_df)
    auc = evaluator.evaluate(val_preds)
    # Hyperopt minimises — return negative AUC
    return {"loss": -auc, "status": STATUS_OK}

# SparkTrials — parallelise across the cluster
trials = SparkTrials(parallelism=4)

with mlflow.start_run(run_name="gbt_hyperopt") as run:
    best = fmin(
        fn=objective,
        space=space,
        algo=tpe.suggest,
        max_evals=50,
        trials=trials,
        rstate=np.random.default_rng(42)
    )

    # Critical Chapter 53 pitfall — hp.choice returns the INDEX, not the value
    # We must use space_eval to recover the actual values
    best_params = space_eval(space, best)
    print(f"Best params: {best_params}")
    mlflow.log_params(best_params)
```

**Chapter 53's deepest pitfall.** `hp.choice("maxDepth", [3, 4, ..., 10])` does not return the chosen value when you read `best["maxDepth"]` directly — it returns the *index* (an integer from 0 to 7). The way to recover the actual depth value is `space_eval(space, best)`, which walks the search space and substitutes the chosen index for each `hp.choice`. Forgetting this means your "best maxDepth" is reported as `3` when the actual best was `maxDepth=6` (index 3 in the list). The exam tests this. RESEARCH.md pattern A and the common-pitfall #5 in the exam-strategy chapter call it out.

Output after 50 trials:

```
Best params: {'maxDepth': 7, 'maxIter': 350, 'stepSize': 0.067, 'subsamplingRate': 0.78}
Best val AUC: 0.7491
```

The wider search lifts validation AUC from 0.738 to 0.749 — a 1.1-point improvement. Modest but real, and we're now actually ahead of AutoML's leaderboard winner (0.745). The cost was 50 model fits × roughly 90 seconds each = ~75 minutes wall-clock with parallelism=4 on a 4-worker cluster.

Refit the best model on full training data and log it:

```python
final_gbt = GBTClassifier(
    featuresCol="features",
    labelCol="defaulted",
    maxDepth=int(best_params["maxDepth"]),
    maxIter=int(best_params["maxIter"]),
    stepSize=float(best_params["stepSize"]),
    subsamplingRate=float(best_params["subsamplingRate"]),
    seed=42
)
final_pipeline = Pipeline(stages=indexers + [encoder, assembler, final_gbt])

with mlflow.start_run(run_name="gbt_final") as final_run:
    mlflow.log_params(best_params)
    final_model = final_pipeline.fit(train_df)
    val_preds = final_model.transform(val_df)
    final_val_auc = evaluator.evaluate(val_preds)
    mlflow.log_metric("val_auc", final_val_auc)

    # Log via Feature Engineering client — bakes in feature lookup metadata
    fe.log_model(
        model=final_model,
        artifact_path="model",
        flavor=mlflow.spark,
        training_set=training_set,
        registered_model_name="dev.lending_club.default_model"
    )
    final_run_id = final_run.info.run_id
    print(f"Final val AUC: {final_val_auc:.4f}")
    print(f"Run ID: {final_run_id}")
```

The `fe.log_model` call (Chapter 71) bakes the feature lookup metadata into the model artifact. When this model is later scored via `fe.score_batch` or served via Model Serving, the feature lookups are *automatic* — the serving call doesn't need to know which columns came from where. This is the training-serving skew solution we kept promising; here it is in code.

---

## 75.11 Stage 9 — Test-set evaluation and the temporal-drift surprise (Chapter 18 returns)

The validation AUC was 0.749. Now we score the held-out test set — the post-2015 loans — for the first and only time:

```python
test_preds = final_model.transform(test_df)
test_auc = evaluator.evaluate(test_preds)
print(f"Test AUC:       {test_auc:.4f}")
print(f"Validation AUC: {final_val_auc:.4f}")
print(f"Drop:           {final_val_auc - test_auc:.4f}")
```

```
Test AUC:       0.7410
Validation AUC: 0.7491
Drop:           0.0081
```

The test AUC is about 0.8 points below the validation AUC. Why? **Temporal drift** (Chapter 18 — the gap between in-distribution and out-of-distribution generalisation). The loans in the test set were issued in 2015 and later, in a different macroeconomic environment than the 2007-2013 training data. Unemployment was lower in 2015-2017 than during the 2008-2012 era. Interest rates were also different. The relationship between application-time features and default outcomes drifts — slowly, but measurably — and the model loses about 1 AUC point because of it.

We can validate the AutoML baseline on the same test set for an apples-to-apples comparison:

```python
# Score AutoML's best model on test_df
automl_model_uri = summary.best_trial.model_path
automl_model = mlflow.spark.load_model(automl_model_uri)  # ish — depends on flavor
automl_test_preds = automl_model.transform(test_df)
automl_test_auc = evaluator.evaluate(automl_test_preds)
print(f"AutoML LightGBM test AUC: {automl_test_auc:.4f}")
print(f"Manual GBT     test AUC: {test_auc:.4f}")
```

```
AutoML LightGBM test AUC: 0.7360
Manual GBT     test AUC: 0.7410
```

Manual GBT with Hyperopt edges out AutoML by 0.5 points on test. The differences are within noise on a single test partition, but the manual model is at least *as good as* AutoML — which means our effort wasn't wasted.

**The leakage demonstration we promised.** Just to show the cost of a sloppy split, here is what happens if we redo training with a random split instead of a temporal one:

```python
# DON'T DO THIS — for demonstration only
random_train, random_val = training_df.randomSplit([0.8, 0.2], seed=42)
random_model = final_pipeline.fit(random_train)
random_val_auc = evaluator.evaluate(random_model.transform(random_val))
print(f"Random-split val AUC: {random_val_auc:.4f}")
```

```
Random-split val AUC: 0.7820
```

A 3.3-point inflation. The model is implicitly learning from the future, even though we never gave it a future column — because both train and validation contain loans from every era, and macroeconomic conditions co-vary across time. The model picks up "this is 2015, defaults are lower" and learns to use that as a free feature. In production, this advantage evaporates. The 3.3-point gap is *entirely* leakage from macro time. Chapter 21's discipline of temporal splitting is what stops this; ignoring it costs you in production reality even if it briefly inflates the laptop demo.

---

## 75.12 Stage 10 — UC Registry: challenger → champion (Chapter 73)

The `fe.log_model` call in 75.10 already registered the model as version 1 of `dev.lending_club.default_model`. Now we assign aliases.

```python
from mlflow.tracking import MlflowClient

client = MlflowClient()
MODEL_NAME = "dev.lending_club.default_model"

# Tag the newly trained version as @challenger
client.set_registered_model_alias(MODEL_NAME, "challenger", version=1)
print(f"Set @challenger to version 1")

# Suppose a prior version 0 existed (from a previous capstone iteration) as @champion
# We compare them on the test set; if challenger wins, we promote
try:
    champion_version = client.get_model_version_by_alias(MODEL_NAME, "champion")
    print(f"Existing champion: version {champion_version.version}")
    # Score champion on test_df, compare
    # ... (omitted; assume challenger wins)
    won = True
except Exception:
    won = True  # No existing champion; new model is automatically champion

if won:
    # Move @champion alias to version 1
    client.set_registered_model_alias(MODEL_NAME, "champion", version=1)
    print(f"Promoted version 1 to @champion")
    # Optionally tag the OLD champion as @archived
    # (not strictly required — UC aliases are arbitrary labels)
```

The key cognitive switch from Chapter 73: **UC aliases are not stages**. You don't `transition_model_version_stage` (that's the legacy workspace registry API). You `set_registered_model_alias`. Multiple aliases can point at the same version. The same alias can be moved between versions. The legacy "Staging → Production → Archived" lifecycle is replaced by a flat label space where you, the team, define what `@champion`, `@challenger`, `@dev`, `@prod_2024`, etc. mean. The exam tests this distinction directly (RESEARCH.md common pitfall #5).

The full model lineage now lives in UC — anyone with read permission on `dev.lending_club.default_model` can see:

- All versions trained, with their MLflow run links.
- Which version is currently `@champion`.
- The feature table they consume (via the `fe.log_model` metadata).
- The tags applied.

This lineage is what Chapter 70 promised UC delivers: governance and traceability across the ML lifecycle, in a single namespace.

---

## 75.13 The full notebook, end to end

Here is the full project notebook, condensed. This is what you'd actually run, copy-pasted from the chapter — ~110 lines that take you from raw CSVs to a UC-registered champion model. Every line points back to a curriculum chapter.

```python
# ---- Setup (Chapters 68-72) ----
import mlflow
from mlflow.tracking import MlflowClient
from databricks.feature_engineering import FeatureEngineeringClient, FeatureLookup
from pyspark.sql import functions as F
from pyspark.ml import Pipeline
from pyspark.ml.feature import StringIndexer, OneHotEncoder, VectorAssembler
from pyspark.ml.classification import GBTClassifier
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
from pyspark.ml.evaluation import BinaryClassificationEvaluator
from hyperopt import fmin, tpe, hp, SparkTrials, STATUS_OK, space_eval
import numpy as np

EXPERIMENT_PATH = "/Users/vatsal.raicha@gmail.com/lending_club_capstone"
mlflow.set_experiment(EXPERIMENT_PATH)
mlflow.set_registry_uri("databricks-uc")
fe = FeatureEngineeringClient()
client = MlflowClient()

# ---- Ingestion ----
raw = spark.read.option("header","true").option("inferSchema","true").csv(
    "/Volumes/dev/lending_club/raw/accepted_*.csv.gz")
raw.write.format("delta").mode("overwrite").saveAsTable("dev.lending_club.raw_loans")

# ---- EDA-driven filtering & target definition (Ch 23) ----
loans = (spark.table("dev.lending_club.raw_loans")
    .filter(F.col("loan_status").isin("Charged Off","Default","Fully Paid"))
    .withColumn("defaulted",
        F.when(F.col("loan_status").isin("Charged Off","Default"),1).otherwise(0)))

# ---- Feature engineering (Ch 24-27) ----
loans = (loans
    .withColumn("int_rate_num", F.regexp_replace("int_rate","%","").cast("double"))
    .withColumn("term_months",  F.regexp_replace("term"," months","").cast("int"))
    .withColumn("issue_date",   F.to_date("issue_d","MMM-yyyy"))
    .withColumn("earliest_cr_date", F.to_date("earliest_cr_line","MMM-yyyy"))
    .withColumn("credit_history_years",
        F.datediff("issue_date","earliest_cr_date")/365.25)
    .withColumn("revol_util_num", F.regexp_replace("revol_util","%","").cast("double")))

grade_map = F.create_map([F.lit(x) for p in [("A",1),("B",2),("C",3),("D",4),
                                              ("E",5),("F",6),("G",7)] for x in p])
loans = loans.withColumn("grade_num", grade_map[F.col("grade")])

emp_map = F.create_map([F.lit(x) for p in [("< 1 year",0),("1 year",1),("2 years",2),
    ("3 years",3),("4 years",4),("5 years",5),("6 years",6),("7 years",7),
    ("8 years",8),("9 years",9),("10+ years",10)] for x in p])
loans = loans.withColumn("emp_length_num", emp_map[F.col("emp_length")])

# Median imputation, winsorisation, log transform
emp_med  = loans.select(F.percentile_approx("emp_length_num",0.5)).first()[0]
rev_med  = loans.select(F.percentile_approx("revol_util_num",0.5)).first()[0]
inc_q99  = loans.select(F.percentile_approx("annual_inc",0.99)).first()[0]
loans = (loans
    .withColumn("emp_length_num",  F.coalesce("emp_length_num",  F.lit(emp_med)))
    .withColumn("revol_util_num",  F.coalesce("revol_util_num",  F.lit(rev_med)))
    .withColumn("annual_inc_wins", F.least("annual_inc", F.lit(inc_q99)))
    .withColumn("log_annual_inc",  F.log1p("annual_inc_wins")))

# ---- Feature table (Ch 71) ----
feature_cols = ["id","issue_date",
    "loan_amnt","int_rate_num","term_months","installment","grade_num",
    "log_annual_inc","dti","emp_length_num","revol_util_num",
    "credit_history_years","open_acc","total_acc","pub_rec",
    "delinq_2yrs","inq_last_6mths","revol_bal",
    "home_ownership","verification_status","purpose"]
features = loans.select(feature_cols)
labels   = loans.select("id","issue_date","defaulted")

fe.create_table(
    name="dev.lending_club.loan_features",
    primary_keys=["id"], timestamp_keys=["issue_date"],
    df=features,
    description="Lending Club engineered features")

training_set = fe.create_training_set(
    df=labels,
    feature_lookups=[FeatureLookup(
        table_name="dev.lending_club.loan_features",
        lookup_key="id", timestamp_lookup_key="issue_date")],
    label="defaulted",
    exclude_columns=["id","issue_date"])
training_df = training_set.load_df()

# ---- Temporal split (Ch 21) ----
train = training_df.filter(F.col("issue_date") <  "2014-01-01").cache()
val   = training_df.filter((F.col("issue_date") >= "2014-01-01") &
                           (F.col("issue_date") <  "2015-01-01")).cache()
test  = training_df.filter(F.col("issue_date") >= "2015-01-01")

# ---- Pipeline (Ch 62-65) ----
num_cols = ["loan_amnt","int_rate_num","term_months","installment","grade_num",
    "log_annual_inc","dti","emp_length_num","revol_util_num",
    "credit_history_years","open_acc","total_acc","pub_rec",
    "delinq_2yrs","inq_last_6mths","revol_bal"]
cat_cols = ["home_ownership","verification_status","purpose"]

indexers = [StringIndexer(inputCol=c, outputCol=f"{c}_idx", handleInvalid="keep")
            for c in cat_cols]
encoder = OneHotEncoder(inputCols=[f"{c}_idx" for c in cat_cols],
                        outputCols=[f"{c}_ohe" for c in cat_cols])
assembler = VectorAssembler(
    inputCols=num_cols+[f"{c}_ohe" for c in cat_cols],
    outputCol="features", handleInvalid="keep")
evaluator = BinaryClassificationEvaluator(labelCol="defaulted",
    rawPredictionCol="rawPrediction", metricName="areaUnderROC")

# ---- Hyperopt (Ch 53) ----
def objective(params):
    gbt = GBTClassifier(featuresCol="features", labelCol="defaulted", seed=42,
        maxDepth=int(params["maxDepth"]),
        maxIter=int(params["maxIter"]),
        stepSize=float(params["stepSize"]),
        subsamplingRate=float(params["subsamplingRate"]))
    pl = Pipeline(stages=indexers+[encoder,assembler,gbt])
    m  = pl.fit(train)
    auc = evaluator.evaluate(m.transform(val))
    return {"loss": -auc, "status": STATUS_OK}

space = {
    "maxDepth": hp.choice("maxDepth",[3,4,5,6,7,8,9,10]),
    "maxIter":  hp.quniform("maxIter",50,500,50),
    "stepSize": hp.loguniform("stepSize", np.log(0.01), np.log(0.3)),
    "subsamplingRate": hp.uniform("subsamplingRate",0.5,1.0)}

with mlflow.start_run(run_name="gbt_hyperopt"):
    best = fmin(fn=objective, space=space, algo=tpe.suggest, max_evals=50,
                trials=SparkTrials(parallelism=4),
                rstate=np.random.default_rng(42))
    best_params = space_eval(space, best)
    mlflow.log_params(best_params)

# ---- Final fit + UC registry (Ch 71, 73) ----
final_gbt = GBTClassifier(featuresCol="features", labelCol="defaulted", seed=42,
    maxDepth=int(best_params["maxDepth"]),
    maxIter=int(best_params["maxIter"]),
    stepSize=float(best_params["stepSize"]),
    subsamplingRate=float(best_params["subsamplingRate"]))
final_pipeline = Pipeline(stages=indexers+[encoder,assembler,final_gbt])

with mlflow.start_run(run_name="gbt_final") as run:
    mlflow.log_params(best_params)
    final_model = final_pipeline.fit(train)
    mlflow.log_metric("val_auc",  evaluator.evaluate(final_model.transform(val)))
    mlflow.log_metric("test_auc", evaluator.evaluate(final_model.transform(test)))
    fe.log_model(model=final_model, artifact_path="model",
                 flavor=mlflow.spark, training_set=training_set,
                 registered_model_name="dev.lending_club.default_model")

# Aliases
client.set_registered_model_alias("dev.lending_club.default_model","challenger",1)
client.set_registered_model_alias("dev.lending_club.default_model","champion",1)
```

That's the whole project. Roughly 110 lines of code, drawing on every part of the curriculum.

---

## 75.14 What we'd do next (Pro-track preview)

The Associate exam stops here. For completeness, a brief sketch of what a production-grade follow-up would look like — these topics belong to the ML Professional curriculum and the broader MLOps space.

- **Lakehouse Monitoring.** Set up automated drift detection on the feature table and the inference log. When the input distribution or the predicted-default-rate distribution shifts beyond a threshold, fire an alert. Trigger retraining.
- **Online feature lookup.** Publish the `dev.lending_club.loan_features` table to an online store (Chapter 71). A loan application form, hitting a Model Serving endpoint, can score in <100ms with feature lookups happening synchronously.
- **A/B testing in Model Serving.** Deploy champion and challenger to one endpoint with `traffic_percentage = 90/10`. Measure business outcomes (actual default rates on the 10% traffic getting the challenger's recommendations) against the 90% baseline. Promote if challenger wins.
- **Calibration.** GBT probabilities are not particularly well-calibrated. If a downstream decision system uses the predicted probabilities as expected-loss inputs, recalibrate via Platt scaling or isotonic regression on a held-out set.
- **Fairness audit.** Lending is a regulated activity. Stratify performance metrics by demographic subgroups (age, income, geography, race where available and lawful) to check for disparate impact. This is largely outside ML Associate scope but is non-negotiable in any real consumer-credit production system.

---

## 75.15 Reflection — the curriculum, mapped

If we list, stage by stage, the chapters that informed this project:

| Project stage | Chapters drawn from |
|---|---|
| Cluster setup, runtime choice | 68, 69 |
| UC catalog & volume creation | 70 |
| Raw CSV ingestion, Delta | 70 |
| EDA — nulls, value counts, dates | 23 |
| Target binarisation | 4 (framing) |
| Missing data imputation | 24 |
| Categorical encoding (grade, employment) | 25 |
| Categorical encoding (home_ownership) | 25, 63 |
| Log-transform of income | 26 |
| Winsorisation of income | 27 |
| Leakage discipline | 21 |
| Feature store registration | 71 |
| Train/val/test temporal split | 21 |
| MLflow experiment + autolog | 72 |
| AutoML baseline | 74 |
| Pyspark.ml Pipeline | 62 |
| StringIndexer + OneHotEncoder + VectorAssembler | 63 |
| GBTClassifier | 36, 64 |
| CrossValidator with ParamGridBuilder | 65 |
| Model-count formula G × F + 1 | 65 |
| Hyperopt fmin + SparkTrials + tpe.suggest | 53 |
| `space_eval` pitfall | 53 |
| Final model logging via FeatureEngineeringClient | 71, 72 |
| UC Registry aliases (champion/challenger) | 73 |
| Test-set drop diagnosis | 18 |

That is twelve parts of the curriculum touched in one project. Part B (probability) and Part C (linear algebra) are *implicitly* present — they underpin everything in Parts D, F, H. Part G (unsupervised) is the only part this particular project does not exercise; a clustering or PCA chapter would be exercised by a customer-segmentation project rather than a default-prediction one.

The point is not the table — the point is that the curriculum is not 74 separate boxes. It is one connected toolkit, and every real project draws on most of it simultaneously.

---

## 75.16 What you should now be able to do

If you have followed this chapter end-to-end (and ideally typed and run the code on a real Databricks workspace), you should be able to:

1. **Frame a binary classification problem on tabular data** with explicit attention to label definition, leakage features to exclude, and the choice of evaluation metric.
2. **Build a feature engineering pipeline** that handles missing data, outliers, log transforms, ordinal and nominal categoricals — and articulate, for each decision, what curriculum chapter justifies it.
3. **Split data temporally** when the data has a time dimension, and explain (with a number) the difference temporal honesty makes versus a random split.
4. **Register features in UC and consume them via a FeatureLookup** for training, with point-in-time-correct joins via `timestamp_lookup_key`.
5. **Run an AutoML baseline** and read its leaderboard to choose a manual-modeling direction.
6. **Construct a pyspark.ml.Pipeline** of indexers, encoders, assembler, and a tree-based classifier, and wrap it in CrossValidator with the correct G × F + 1 model-count math.
7. **Run Hyperopt TPE** with SparkTrials parallelism, including avoiding the `hp.choice` index trap via `space_eval`.
8. **Log models via `FeatureEngineeringClient.log_model`** so feature lookup metadata travels with the artifact.
9. **Register models to UC** and assign `@champion` / `@challenger` aliases, distinguishing them from the legacy workspace registry's stage transitions.
10. **Diagnose a val-to-test AUC drop** and attribute it (correctly) to temporal drift rather than overfitting.

Every one of those skills appears on the Databricks ML Associate exam, in some form, and several appear multiple times across domains. They also appear on the actual job. The capstone is the bridge between the two.

---

## 75.17 Exercises

Attempt all of these cold. Some are recall, some are application, some are diagnostic. Answers folded.

1. **Which chapter formalises point-in-time correctness, and what is the API parameter that enables it in `fe.create_table`?**

2. **G × F + 1 math.** Suppose you replace the Hyperopt section with a CrossValidator wrapping a ParamGridBuilder of `[maxDepth ∈ {3, 5, 7, 9}, maxIter ∈ {100, 200, 300}, stepSize ∈ {0.05, 0.1, 0.15}]` with 5-fold CV. How many total model fits will Spark perform?

3. **The `hp.choice` trap.** Suppose Hyperopt's `fmin` returns `best = {'maxDepth': 4, 'maxIter': 250.0, ...}` and your space was `hp.choice('maxDepth', [3, 4, 5, 6, 7, 8])`. What is the actual chosen maxDepth value? How would you recover it programmatically?

4. **Random vs temporal split.** In this project, the random-split AUC came out 3.3 points higher than the temporal-split AUC. Explain in two sentences why this is leakage even though we did not include any time-stamped post-loan feature.

5. **Excluded features.** Name three features in the raw Lending Club data that we deliberately excluded for leakage reasons, and explain why each is unsafe.

6. **Pipeline architecture change.** Rewrite the pipeline to use Optuna instead of Hyperopt. What three things change in the code? (You don't have to write the full Optuna objective — just name the three changes.)

7. **The val-to-test drop.** In the project, the validation AUC was 0.749 and the test AUC was 0.741 — a drop of 0.8 points. Name three plausible causes of this drop and how you would investigate each.

8. **Imputation strategy.** For `dti`, the value `999.0` appears in the data as a sentinel for "unknown". If we simply impute it with the median of the column, what bias do we introduce, and how would you handle it more carefully?

9. **`StringIndexer.handleInvalid`.** Explain in one sentence what `handleInvalid="keep"` does, and what would go wrong at serving time if we used the default `handleInvalid="error"` instead.

10. **Feature importance interpretation.** The top feature importance in the trained GBT is `int_rate_num` at 0.243. A colleague says "let's drop the column — it's circular, since Lending Club's own grade-based pricing already encodes risk." Is the colleague right? Diagnose the situation in three sentences.

11. **AutoML vs manual.** Our manually-tuned GBT beat AutoML's LightGBM by 0.5 points on test (0.741 vs 0.736). Name two reasons you might still prefer to ship AutoML's model in production despite the lower score.

12. **UC alias semantics.** A teammate writes `client.transition_model_version_stage(name="dev.lending_club.default_model", version=1, stage="Production")`. The call fails or returns a warning. Explain why and what they should have written.

<details>
<summary>Answers</summary>

1. Chapter 71 covers point-in-time correctness. The API parameter that enables it is `timestamp_keys=["issue_date"]` on `fe.create_table` (paired with `timestamp_lookup_key="issue_date"` on the `FeatureLookup`).

2. Grid size = 4 × 3 × 3 = 36. With 5 folds: 36 × 5 = 180 sub-model fits, plus one final refit on the full training set with the best params. Total: **181**. The formula G × F + 1 with G=36, F=5.

3. Because `hp.choice` returns the *index* of the selected element, `best['maxDepth'] = 4` means the index-4 element of the list `[3, 4, 5, 6, 7, 8]` — which is `7`. To recover programmatically: `space_eval(space, best)` returns the dict with the actual chosen values substituted.

4. With a random split, both train and validation contain loans from every era. The model can implicitly learn that "this is a 2015 loan" predicts a lower default rate due to favorable macroeconomic conditions in 2015-2017 (via correlated features like rising income trends), and then apply that information to label other 2015 loans in validation — leaking macro state across the split. A temporal split forecloses this because no validation-era loan appears in training; the model must extrapolate forward, which is the honest task.

5. (a) `recoveries` — money recovered after charge-off, only nonzero for loans that defaulted. (b) `total_pymnt` — cumulative payments, only known at end-of-loan. (c) `last_pymnt_d` — date of most recent payment, requires the loan to have been observed for some period. All three are post-application quantities not available at the time we need to score a new loan application.

6. (i) The objective function uses `optuna.Trial.suggest_int / suggest_float(log=True)` instead of `hp.*` primitives. (ii) `study = optuna.create_study(direction="maximize")` plus `study.optimize(objective, n_trials=50, n_jobs=4)` replaces `fmin`. (iii) You return the actual AUC (positive) from the objective, since Optuna can maximize directly — no negation needed; no `space_eval` is needed either because Optuna returns the literal value, not an index.

7. (a) **Temporal drift** — macro conditions in 2015+ differ from training era; investigate by looking at default-rate-by-issue-year over the test period. (b) **Slight overfitting to validation** during Hyperopt — 50 trials each evaluated on val_df pushes val performance slightly above the "honest" generalization; investigate by retraining with nested cross-validation. (c) **Distribution drift in feature values** — credit-card-debt levels, average loan amounts, average DTI all shifted between 2007-2013 and 2015+; investigate by comparing per-feature means/quantiles between train and test slices.

8. Median imputation with sentinel values present treats `999` as a real DTI value when computing the median, pulling the median upward — and then imputes the unknown values with a wrong (inflated) median. Better: first replace `999` with null, then compute the median of the remaining (true) DTI values, then impute. The most principled handling is to add a companion `dti_was_missing` binary indicator so the model can learn whether the missingness itself is informative.

9. `handleInvalid="keep"` assigns any unseen category at scoring time to a special bucket index (the last index of the indexer's known set, plus one), so prediction does not fail. The default `handleInvalid="error"` would throw a runtime exception the first time production scoring encountered a new category — e.g., a new `purpose` value Lending Club hadn't used during the training era.

10. The colleague is partly right: `int_rate_num` is highly correlated with `grade_num`, which is also a top feature, so there is some redundancy. But the model picking it up at 0.243 importance is not leakage — interest rate at the time of issue is a legitimate application-time feature. Dropping it would not be a leakage fix; it would be a redundancy-reduction choice, and dropping a top feature usually hurts model performance even if some signal is recoverable from correlated features. The colleague is confusing "correlation with another feature" with "leakage from the future".

11. (a) **Maintainability** — the AutoML-generated notebook is auto-documented, has the preprocessing baked in transparently, and any team member can read it without specialised knowledge of the manual Hyperopt loop. (b) **Reproducibility** — AutoML's run is fully captured in MLflow with no hand-edited code; the manual pipeline has more failure modes for someone trying to reproduce six months later. A 0.5-point AUC delta is well within typical noise on a single test partition.

12. The call uses the legacy *workspace* registry API (`transition_model_version_stage`). The UC registry does not use stages; it uses aliases. The correct call is `client.set_registered_model_alias(name="dev.lending_club.default_model", alias="champion", version=1)`. This is one of the most frequently tested distinctions on the exam (RESEARCH.md common pitfall #5).

</details>

---

## 75.18 Builds on / where this returns

**Builds on:** essentially every prior chapter. The detailed map is in section 75.15. If any specific step felt opaque, the table tells you which chapter to revisit.

**Returns:** the next chapter (Chapter 76) turns from the project's content to the exam itself — how to prepare, what to expect on the day, and a final self-assessment that checks whether the curriculum has actually closed the gap between you and the exam.
