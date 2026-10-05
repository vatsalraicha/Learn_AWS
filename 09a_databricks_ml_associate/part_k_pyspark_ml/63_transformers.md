# Chapter 63 — Common Transformers: What Each One Computes

> **Goal of this chapter:** to develop a working knowledge of the dozen-or-so `pyspark.ml` Transformers (and a few Estimators-that-produce-Transformers) you will actually use in 95% of projects. The point is not to enumerate APIs — that's what the documentation is for — but to know, for each one, what mathematical operation it performs, when you reach for it, what it looks like on a small concrete example, and what trap is waiting if you misuse it. By the end of the chapter you should be able to read a 5–10 stage feature-engineering pipeline and predict the shape of every intermediate DataFrame.

---

## 63.1 Why this chapter is necessary

`pyspark.ml.feature` is wide. The official module listing has more than fifty classes. Newcomers experience this as paralysis: every problem could be solved with three different Transformers and it's not always obvious which to pick. The fix is to anchor each Transformer to *what it computes*, not to its API surface. Once you know what the operation is, the API name and arguments are easy to recover.

We will tour Transformers in the order you typically apply them in a project:

1. **Assembling features** — taking many columns and producing one Vector column. The convention `pyspark.ml` insists on (Chapter 62).
2. **Encoding categoricals** — turning strings or unordered integers into numerical representations the model can consume.
3. **Scaling numerics** — equalising the magnitudes across features so optimisation behaves.
4. **Discretisation** — turning continuous columns into bucketed ones.
5. **Imputation** — handling missing values.
6. **Text** — tokenising, dropping stopwords, vectorising bags of words.
7. **Vector tools** — slicing, normalising, expanding.

We close with a fully worked five-stage example so you can see the schema evolve.

A small notational reminder: in the table that follows, an "E" means the class is an Estimator (must `.fit` before use) and "T" means it is a Transformer (use directly). The Model produced by an Estimator is always the corresponding `*Model` class.

| Operation | Class | E/T |
|---|---|---|
| Assemble columns → Vector | `VectorAssembler` | T |
| String → integer index | `StringIndexer` | E |
| Integer index → string | `IndexToString` | T |
| Integer → one-hot Vector | `OneHotEncoder` | E |
| Per-column standardisation | `StandardScaler` | E |
| Per-column min-max scale | `MinMaxScaler` | E |
| Robust scaling (medians/IQR) | `RobustScaler` | E |
| Discretise by user splits | `Bucketizer` | T |
| Discretise by quantiles | `QuantileDiscretizer` | E |
| Impute missing | `Imputer` | E |
| Whitespace tokenise | `Tokenizer` | T |
| Regex tokenise | `RegexTokenizer` | T |
| Drop stopwords | `StopWordsRemover` | T |
| Bag-of-words counts | `CountVectorizer` | E |
| Hashed bag-of-words | `HashingTF` | T |
| TF-IDF weighting | `IDF` | E |
| Polynomial feature expansion | `PolynomialExpansion` | T |
| Subset columns of a Vector | `VectorSlicer` | T |
| Row-wise normalise (L1/L2/Linf) | `Normalizer` | T |

The rest of this chapter takes each in turn.

---

## 63.2 Assembling: `VectorAssembler`

This is the Transformer you cannot avoid. Every `pyspark.ml` estimator expects a single Vector column for features. `VectorAssembler` is the operation that turns N numeric columns into that one Vector column.

```python
from pyspark.ml.feature import VectorAssembler

va = VectorAssembler(
    inputCols=["age", "income", "tenure"],
    outputCol="features",
)
out = va.transform(df)
```

What happened, row by row: for each row, `pyspark.ml` reads `age`, `income`, `tenure`, and constructs a `Vector(age, income, tenure)` of length 3. That Vector becomes the value in the new `features` column.

A small numerical example. Input:

```
+---+------+------+
|age|income|tenure|
+---+------+------+
| 35| 75000|     5|
| 29| 62000|     2|
+---+------+------+
```

Output:

```
+---+------+------+------------------+
|age|income|tenure|         features |
+---+------+------+------------------+
| 35| 75000|     5| [35.0, 75000.0, 5.0]|
| 29| 62000|     2| [29.0, 62000.0, 2.0]|
+---+------+------+------------------+
```

The original columns are still there; the new one is appended.

Three subtleties.

**Mixing scalar and Vector inputs.** You can include a column that is *itself* a Vector in `inputCols`. `VectorAssembler` will concatenate it onto the rest. This is how you combine, say, hand-engineered numeric features with the output of a `OneHotEncoder` (which produces a Vector per row):

```python
va = VectorAssembler(inputCols=["age", "income", "gender_ohe"], outputCol="features")
```

If `gender_ohe` is a length-2 OHE vector, the resulting `features` column will be length 4 (`[age, income, gender_ohe[0], gender_ohe[1]]`).

**Null handling.** By default, if any of the input columns is null in a row, `VectorAssembler` errors out for that row. You can change this with the `handleInvalid` parameter: `"skip"` (drop the row), `"keep"` (produce a Vector containing `NaN`s — which most downstream models hate), or `"error"` (the default). The right move is almost always to impute upstream (section 63.7) and let `VectorAssembler` default-error if anything slips through.

**Memory.** Assembling creates a new column; the old columns persist. For large pipelines this is a minor cost — Spark's columnar representation deduplicates — but if you `.cache()` an intermediate DataFrame, that cache holds both the original columns and the assembled vector. Drop columns you don't need before caching.

---

## 63.3 Encoding categoricals: `StringIndexer` and friends

Most real datasets have string-valued columns: country, gender, product category, marital status. The model wants numbers, so we encode.

### 63.3.1 `StringIndexer`

`StringIndexer` is an Estimator that walks a string column and assigns each distinct value an integer.

```python
from pyspark.ml.feature import StringIndexer

idx = StringIndexer(inputCol="country", outputCol="country_idx")
idx_model = idx.fit(df)
df2 = idx_model.transform(df)
```

If `country` has values `{"US", "UK", "IN", "US", "DE", "US", "UK"}`, by default `StringIndexer` assigns the most frequent value to index 0:

```
"US" → 0   (3 occurrences)
"UK" → 1   (2 occurrences)
"IN" → 2   (1 occurrence)
"DE" → 3   (1 occurrence)
```

Ties are broken alphabetically. You can change the order with `stringOrderType`: `"frequencyDesc"` (default), `"frequencyAsc"`, `"alphabetDesc"`, `"alphabetAsc"`.

The Model carries the dictionary in `idx_model.labels` — a list of strings, where the *index* of each string in the list is its integer encoding.

**The unseen-category problem.** What if at serve time you see `"FR"`, a country that wasn't in the training set? The Estimator learned nothing about `"FR"`. By default, `StringIndexer` raises a `SparkException`. You can change this with `handleInvalid`:

- `"error"` (default) — throw.
- `"skip"` — drop the row.
- `"keep"` — assign the unseen value a fresh integer (= the number of seen labels). This is usually what you want, because dropping rows in production is bad and erroring is worse.

For label columns — when you're encoding the *target* variable — `"skip"` makes more sense, because an unseen label at serve time usually means a bug upstream.

### 63.3.2 `IndexToString`

The inverse. Given the integer-encoded predictions from a classifier, you want to decode them back to strings for the end user:

```python
from pyspark.ml.feature import IndexToString

i2s = IndexToString(inputCol="prediction", outputCol="prediction_label", labels=label_idx_model.labels)
final_df = i2s.transform(predictions_df)
```

`IndexToString` is a pure Transformer (no fit). You hand it the labels list, it does the lookup. The labels list is usually the `.labels` attribute of the `StringIndexerModel` that produced the integer column in the first place.

### 63.3.3 `OneHotEncoder`

`StringIndexer` gives you integers, but integers carry a *false ordering* — a linear model sees `country_idx=3` as three times bigger than `country_idx=1`, which is nonsense for nominal categories. The standard fix for linear and distance-based models is one-hot encoding: each category becomes its own indicator column.

In `pyspark.ml`, `OneHotEncoder` is an Estimator that operates on the *integer-indexed* column (not the original string). The reason is that Spark needs to know the cardinality up front to size the output Vector; `.fit` scans the column to learn that.

```python
from pyspark.ml.feature import OneHotEncoder

ohe = OneHotEncoder(inputCols=["country_idx"], outputCols=["country_ohe"])
ohe_model = ohe.fit(df2)
df3 = ohe_model.transform(df2)
```

Output: a `SparseVector` per row, with a `1` at the position of the row's category and zeros elsewhere.

**The dropLast trap.** By default, `OneHotEncoder` produces vectors of length $K - 1$, not $K$, where $K$ is the number of categories. The last category is dropped (so for `{US, UK, IN, DE}`, you get a length-3 vector, and `DE` is encoded as `[0, 0, 0]`).

Why? Because in linear models with an intercept, the full one-hot is multicollinear with the constant column — every row's OHE entries sum to 1, which is exactly the intercept. Dropping the last category breaks this collinearity. Statisticians call this the "reference category" — `DE` becomes the implicit baseline against which the others are compared.

For tree models, this collinearity doesn't matter (trees don't care about linear combinations), and you might want the full $K$ columns. Set `dropLast=False`.

```python
ohe = OneHotEncoder(inputCols=["country_idx"], outputCols=["country_ohe"], dropLast=False)
```

A small concrete example. Suppose the integer-indexed column is `[0, 1, 2, 0]` and there are 3 distinct categories. With `dropLast=True` (default) the output is length-2:

```
0 → [1, 0]
1 → [0, 1]
2 → [0, 0]    ← the dropped reference category
0 → [1, 0]
```

With `dropLast=False`, it's length-3:

```
0 → [1, 0, 0]
1 → [0, 1, 0]
2 → [0, 0, 1]
0 → [1, 0, 0]
```

For most exam questions, the answer pattern is "did you remember dropLast?" The right move on the job: explicitly pass `dropLast=` so the reader doesn't have to remember the default.

### 63.3.4 What about tree models?

`pyspark.ml`'s tree algorithms (`DecisionTreeClassifier`, `RandomForestClassifier`, `GBTClassifier` and their regression analogues) can handle categorical features *without* one-hot encoding, if you tell them which features are categorical. You do this by attaching a `nominal` attribute via `VectorIndexer`, or by labelling columns through `StringIndexer` + setting `featureSubsetStrategy` appropriately. Practically, most teams still OHE because it Just Works for both linear and tree models — at the cost of a few extra columns. We'll see the categorical-feature path again in Chapter 64.

---

## 63.4 Scaling: `StandardScaler`, `MinMaxScaler`, `RobustScaler`

Linear models, gradient-descent-trained models, distance-based models (k-means, k-NN), and SVMs are *scale-sensitive*. If one feature ranges over $[0, 1{,}000{,}000]$ and another over $[0, 1]$, the first dominates every dot product and every Euclidean distance, and the model effectively ignores the second. Scaling brings features onto comparable magnitudes.

(Tree models, by contrast, are scale-invariant — they only look at thresholds on individual features. You don't need to scale features for `RandomForestClassifier`.)

### 63.4.1 `StandardScaler`

Subtract the per-feature mean and divide by the per-feature standard deviation:

$$
x'_j = \frac{x_j - \mu_j}{\sigma_j}
$$

After scaling, each feature has mean 0 and std 1 *across the training set*.

```python
from pyspark.ml.feature import StandardScaler

scaler = StandardScaler(inputCol="features", outputCol="features_std",
                        withMean=True, withStd=True)
scaler_model = scaler.fit(train_df)
scaled_df = scaler_model.transform(train_df)
```

The Estimator's `.fit` computes the means and stds; the Model's `.transform` applies the (frozen) statistics.

`withMean` defaults to `False`, `withStd` defaults to `True`. The non-obvious default is `withMean=False` — *the default does not center*. The reason is the densification pitfall:

**The densification pitfall.** If your input `features` Vector is sparse (e.g., a TF-IDF representation of text, which is 99%+ zeros), subtracting a non-zero mean turns every zero into `-mu_j`, producing a dense vector. For text data with a 10,000-word vocabulary, this can blow up memory by 100×. So `pyspark.ml`'s default is "scale only, don't center" — preserving sparsity.

For dense numeric data (age, income, etc.), centering is fine and often helpful; set `withMean=True` explicitly. For text/sparse data, leave `withMean=False`.

### 63.4.2 `MinMaxScaler`

Scale each feature linearly to a fixed range, by default $[0, 1]$:

$$
x'_j = \frac{x_j - \min_j}{\max_j - \min_j}
$$

```python
from pyspark.ml.feature import MinMaxScaler

mm = MinMaxScaler(inputCol="features", outputCol="features_mm", min=0.0, max=1.0)
mm_model = mm.fit(train_df)
```

Use when you want bounded outputs (some neural network input layers expect $[0, 1]$ or $[-1, 1]$), or when your data has no outliers. With outliers, `MinMaxScaler` compresses the bulk of the data into a small slice of the range — one extreme value at $x_j = 10^9$ will push everything else near zero.

### 63.4.3 `RobustScaler`

Subtract the median, divide by the interquartile range (IQR = Q3 − Q1):

$$
x'_j = \frac{x_j - \text{median}_j}{Q3_j - Q1_j}
$$

```python
from pyspark.ml.feature import RobustScaler

rs = RobustScaler(inputCol="features", outputCol="features_rs", withCentering=True, withScaling=True)
rs_model = rs.fit(train_df)
```

Use when outliers are present and you don't want them to dominate the scaling statistics. The mean and std are sensitive to outliers; the median and IQR are not. This is the right default for raw real-world numeric data that you haven't audited for extremes.

### 63.4.4 The fit-on-train, transform-on-test discipline

For *every* scaler, the discipline is the same: `.fit` only on training data. `.transform` on both training and test. The statistics (mean, std, min, max, median, IQR) are learned from training and frozen.

If you accidentally fit the scaler on the union of train+test, you have leaked test-set information into the training pipeline. Section 3.6.3 already complained about this. Pipelines (Chapter 62) make it hard to make this mistake; loose ad-hoc code makes it easy.

A small numerical example. Training data: `features = [10, 20, 30, 40, 50]` (5 rows of a single feature). Mean = 30, std = 14.14. After `StandardScaler(withMean=True, withStd=True)`:

```
10 → (10 - 30) / 14.14 = -1.414
20 → (20 - 30) / 14.14 = -0.707
30 → (30 - 30) / 14.14 =  0.000
40 → (40 - 30) / 14.14 =  0.707
50 → (50 - 30) / 14.14 =  1.414
```

Test data has a value of 60. The fitted scaler produces `(60 - 30) / 14.14 = 2.121`. Note the test value's scaled magnitude is larger than any training value's — that's correct behaviour, because the test value was larger than anything in training.

---

## 63.5 Discretisation: `Bucketizer` and `QuantileDiscretizer`

Sometimes you want to convert a continuous column into a discrete one — for example, you want age to be a categorical "age band" rather than a number. Two Transformers do this; they differ in how the bin boundaries are determined.

### 63.5.1 `Bucketizer` — splits you supply

```python
from pyspark.ml.feature import Bucketizer

bk = Bucketizer(
    splits=[-float("inf"), 18.0, 30.0, 50.0, 65.0, float("inf")],
    inputCol="age",
    outputCol="age_bucket",
)
bucketed_df = bk.transform(df)
```

The splits define $K$ buckets from $K+1$ split points. The bucket for value $x$ is the index $i$ such that `splits[i] <= x < splits[i+1]`. The first and last splits are usually `-float("inf")` and `float("inf")` to cover the entire real line; values outside the provided range otherwise cause errors (use `handleInvalid` to control).

For the splits above and `age = 35`, the bucket is `2` (since `30 <= 35 < 50`). For `age = 17`, the bucket is `0`. For `age = 90`, the bucket is `4`.

`Bucketizer` is a pure Transformer — no `.fit`. You're saying "I know where the boundaries should be; use these." Common when you have domain knowledge ("children 0-12, teens 13-19, adults 20-64, seniors 65+").

### 63.5.2 `QuantileDiscretizer` — splits learned from data

```python
from pyspark.ml.feature import QuantileDiscretizer

qd = QuantileDiscretizer(numBuckets=4, inputCol="income", outputCol="income_q", relativeError=0.001)
qd_model = qd.fit(df)
quantized_df = qd_model.transform(df)
```

`QuantileDiscretizer` is an Estimator. It scans the training column, computes approximate quantiles (the algorithm is Greenwald-Khanna by default), and constructs the splits internally. With `numBuckets=4`, each bucket holds roughly a quarter of the training data — Q1, Q2-Q3, Q3-median... in other words, this is *equal-frequency* binning.

The `relativeError` parameter trades off accuracy vs. speed: smaller value → more precise quantile estimates, more work. The default (0.001 = 0.1% error) is fine for almost everything.

Use `QuantileDiscretizer` when you don't have a priori reason to pick boundaries and you want roughly balanced bin populations. Use `Bucketizer` when you have domain-derived boundaries.

---

## 63.6 Imputation: `Imputer`

Missing values are everywhere in real data. Chapter 24 dissected the taxonomy (MCAR/MAR/MNAR) and strategies. `pyspark.ml`'s `Imputer` is the simplest, most common implementation: replace nulls with the column's mean, median, or mode.

```python
from pyspark.ml.feature import Imputer

imp = Imputer(
    inputCols=["age", "income"],
    outputCols=["age_imp", "income_imp"],
    strategy="median",   # or "mean", "mode"
)
imp_model = imp.fit(train_df)
imputed_df = imp_model.transform(train_df)
```

`Imputer` is an Estimator — it computes the per-column statistic on training data, freezes it, and applies it at transform time. This is exactly the right behaviour: at serve time, missing values are imputed with the *training* statistic, not with whatever stats happen to apply to the small serving batch.

Three notes.

**Numeric only.** `Imputer` operates on numeric columns. For string columns with nulls, you typically `.fillna("UNKNOWN")` upstream (using DataFrame API) and then `StringIndex` as usual.

**`missingValue` parameter.** Some datasets encode missingness as a sentinel like `-999` rather than null. Set `missingValue=-999` and `Imputer` will treat that as missing.

**Outside-Pipeline use is dangerous.** If you `.fit(train_df)` and then forget to `.transform(test_df)` with the *fitted* model, you're either (a) leaving test nulls in place or (b) refitting on test data — both bugs. Always wire `Imputer` into a Pipeline so the framework remembers to use the fitted version.

---

## 63.7 Text: the classic NLP stack

The spam pipeline of Chapter 3 used five text Transformers in sequence: tokenize, drop stopwords, hash to feature vector, weight by IDF, train logistic regression. Let's walk through them.

### 63.7.1 `Tokenizer` and `RegexTokenizer`

`Tokenizer` splits a string column on whitespace and lowercases:

```python
from pyspark.ml.feature import Tokenizer

tok = Tokenizer(inputCol="body", outputCol="tokens")
df_tok = tok.transform(df)
```

For `body = "Hello WORLD, this is spam"`, you get `tokens = ["hello", "world,", "this", "is", "spam"]`. Notice: punctuation is *attached* to neighbouring words because the split is purely on whitespace.

`RegexTokenizer` is the more general (and usually more correct) choice. You specify a regex pattern that defines either the token boundaries (`gaps=True`, default) or the tokens themselves (`gaps=False`):

```python
from pyspark.ml.feature import RegexTokenizer

tok = RegexTokenizer(
    inputCol="body",
    outputCol="tokens",
    pattern=r"\W+",      # split on non-word characters
    toLowercase=True,
    minTokenLength=1,
)
```

For the same input, this produces `["hello", "world", "this", "is", "spam"]` — punctuation gone. Use `RegexTokenizer` whenever your text has any non-trivial punctuation.

### 63.7.2 `StopWordsRemover`

Drop the very common words ("the", "a", "of") that appear in almost every document and don't carry discriminative signal.

```python
from pyspark.ml.feature import StopWordsRemover

remover = StopWordsRemover(inputCol="tokens", outputCol="filtered", caseSensitive=False)
df_no_stop = remover.transform(df_tok)
```

`StopWordsRemover` ships with default English stopword lists; you can override with `stopWords=[...]` or load a different language with `StopWordsRemover.loadDefaultStopWords("german")`.

This is a pure Transformer — no fit. The stopword list is fixed at construction time.

### 63.7.3 `CountVectorizer` vs `HashingTF`

These two Transformers both produce a "bag of words" vector representation, but they differ in a fundamental way.

**`CountVectorizer`** is an Estimator. `.fit` walks the corpus, builds a vocabulary (the top-K most frequent terms, optionally with frequency cutoffs), and assigns each term a fixed index. The resulting `CountVectorizerModel` has a `.vocabulary` attribute. `.transform` produces a SparseVector per row whose length is the vocabulary size and whose entries are word counts.

```python
from pyspark.ml.feature import CountVectorizer

cv = CountVectorizer(inputCol="filtered", outputCol="raw_features", vocabSize=10000, minDF=5)
cv_model = cv.fit(df_no_stop)
df_cv = cv_model.transform(df_no_stop)
print(cv_model.vocabulary[:10])  # top-10 terms by frequency
```

Pros: interpretable (you know which index is which word). Cons: requires a fit pass over the corpus to learn the vocabulary, and the vocabulary must be persisted with the model. Memory grows with vocab size.

**`HashingTF`** is a pure Transformer. There is no vocabulary. Instead, each token is hashed to one of `numFeatures` buckets and counted. The output Vector is length `numFeatures` regardless of the actual vocabulary size.

```python
from pyspark.ml.feature import HashingTF

htf = HashingTF(inputCol="filtered", outputCol="raw_features", numFeatures=10000)
df_htf = htf.transform(df_no_stop)
```

This is the *hashing trick* from Chapter 25. Pros: no fit pass, no vocabulary to persist, constant memory. Cons: collisions — two different words can hash to the same bucket and become indistinguishable. With `numFeatures` an order of magnitude larger than the effective vocabulary, collisions are rare and models tolerate them well.

The choice: `CountVectorizer` if you want interpretability (you'll look at coefficients per word) and your vocabulary fits comfortably in memory; `HashingTF` if you want to skip the fit pass and don't care about per-feature interpretation. For large-scale text, `HashingTF` is the workhorse.

### 63.7.4 `IDF`

Either flavour of "term frequency" Vector gets weighted by inverse document frequency to downweight terms that appear in many documents. This is the TF-IDF reweighting of section 3.5.4.

```python
from pyspark.ml.feature import IDF

idf = IDF(inputCol="raw_features", outputCol="features", minDocFreq=2)
idf_model = idf.fit(df_htf)
df_idf = idf_model.transform(df_htf)
```

`IDF` is an Estimator: `.fit` computes the per-feature IDF weight (one number per output dimension) from the training corpus. `.transform` multiplies each row's TF by the per-feature IDF.

`minDocFreq`: ignore terms appearing in fewer than this many documents (treated as zero). Useful for filtering noise.

### 63.7.5 The classic text pipeline

Putting it together:

```python
from pyspark.ml import Pipeline
from pyspark.ml.feature import RegexTokenizer, StopWordsRemover, HashingTF, IDF
from pyspark.ml.classification import LogisticRegression

tok = RegexTokenizer(inputCol="body", outputCol="tokens", pattern=r"\W+")
remover = StopWordsRemover(inputCol="tokens", outputCol="filtered")
htf = HashingTF(inputCol="filtered", outputCol="raw_features", numFeatures=10000)
idf = IDF(inputCol="raw_features", outputCol="features", minDocFreq=2)
lr = LogisticRegression(featuresCol="features", labelCol="label", regParam=0.01)

pipeline = Pipeline(stages=[tok, remover, htf, idf, lr])
model = pipeline.fit(train_df)
```

This is exactly the Chapter 3 spam pipeline. Two Transformers (tok, remover, htf), two Estimators (idf, lr). After `.fit`, the PipelineModel contains: tok, remover, htf (unchanged), idfModel, lrModel.

---

## 63.8 Polynomial expansion: `PolynomialExpansion`

For a length-$d$ input vector, the degree-$k$ polynomial expansion adds all monomials up to degree $k$:

```python
from pyspark.ml.feature import PolynomialExpansion

px = PolynomialExpansion(inputCol="features", outputCol="poly", degree=2)
```

For `features = [a, b]` (length 2), degree 2, you get `[a, b, a^2, a*b, b^2]` — adding the squared and cross terms.

**Combinatorial blowup.** For length-$d$ input, the number of monomials up to degree $k$ grows as $\binom{d+k}{k}$. With $d = 100$ and $k = 3$, that's already $\binom{103}{3} = 176{,}851$. With $d = 1000$, you cannot afford even degree 2 in dense form. Use polynomial expansion only on a *small* selected subset of features, paired with regularisation, and never blindly on a wide feature vector.

In practice, `PolynomialExpansion` is rare in pyspark.ml pipelines — most teams either add hand-crafted interaction features or use tree models (which discover interactions for free).

---

## 63.9 Vector tools: `VectorSlicer`, `Normalizer`

### 63.9.1 `VectorSlicer`

Pick a subset of columns *from a Vector* (after you've assembled). Useful when you want to feed different subsets of the same feature vector to different models, or when you want to ablate features for diagnostic purposes.

```python
from pyspark.ml.feature import VectorSlicer

slicer = VectorSlicer(inputCol="features", outputCol="features_subset", indices=[0, 2, 5])
df2 = slicer.transform(df)
```

You can also slice by named features if the input column has name attributes (set during `VectorAssembler` with `inputCols`).

### 63.9.2 `Normalizer`

Row-wise normalisation: rescale each row's Vector to have unit norm.

```python
from pyspark.ml.feature import Normalizer

norm = Normalizer(inputCol="features", outputCol="features_norm", p=2.0)  # L2 default
```

After L2 normalisation, every row's Vector has Euclidean length 1. After L1 normalisation (`p=1.0`), every row's Vector has entries summing to 1 (treating it as a probability distribution).

`Normalizer` is a Transformer (no fit) because it operates row by row — no corpus statistics needed.

Use cases:

- **Cosine similarity setup.** Cosine similarity is the dot product of L2-normalised vectors. If you L2-normalise once, dot products downstream behave like cosine.
- **Probability-style inputs.** If you want to feed a histogram vector to a model and have the model see "shape" not "magnitude," L1-normalise.

Don't confuse `Normalizer` (row-wise) with `StandardScaler` (column-wise). They are different operations with similar-sounding names. `Normalizer` doesn't fit; `StandardScaler` does. `Normalizer` doesn't care about other rows; `StandardScaler` uses per-column statistics.

---

## 63.10 A full worked feature-engineering pipeline

Let's run a five-stage pipeline on a small synthetic DataFrame and watch the schema evolve.

```python
from pyspark.sql import SparkSession
from pyspark.ml import Pipeline
from pyspark.ml.feature import (
    StringIndexer, OneHotEncoder, Imputer, VectorAssembler, StandardScaler,
)

spark = SparkSession.builder.appName("ch63").getOrCreate()

df = spark.createDataFrame([
    ("US", 35,  75000.0),
    ("UK", 29,  62000.0),
    ("US", 41,  85000.0),
    ("DE", None, 110000.0),    # missing age
    ("US", 23,  None),         # missing income
    ("UK", 47,  95000.0),
], ["country", "age", "income"])
```

Schema and content after each stage. The pipeline:

```python
country_idx = StringIndexer(inputCol="country", outputCol="country_idx", handleInvalid="keep")
country_ohe = OneHotEncoder(inputCols=["country_idx"], outputCols=["country_ohe"], dropLast=False)
imp         = Imputer(inputCols=["age", "income"], outputCols=["age_imp", "income_imp"], strategy="median")
va          = VectorAssembler(inputCols=["age_imp", "income_imp", "country_ohe"], outputCol="features_raw")
sc          = StandardScaler(inputCol="features_raw", outputCol="features", withMean=True, withStd=True)

pipeline = Pipeline(stages=[country_idx, country_ohe, imp, va, sc])
model = pipeline.fit(df)
out = model.transform(df)
```

After `country_idx`: a new column `country_idx`. Mapping: `"US" → 0` (3 occurrences), `"UK" → 1` (2), `"DE" → 2` (1).

After `country_ohe`: a new column `country_ohe`, length-3 sparse Vector (`dropLast=False`).

After `imp`: two new columns `age_imp` and `income_imp` with medians filled in. Median age (from non-null values 35, 29, 41, 23, 47) = 35; median income (from 75000, 62000, 85000, 110000, 95000) = 85000.

After `va`: a new column `features_raw` of length 5: `[age_imp, income_imp, country_ohe[0], country_ohe[1], country_ohe[2]]`.

After `sc`: a new column `features`, the standardised version of `features_raw`. Each of the 5 dimensions is now mean-0 and std-1 across the training rows.

The final DataFrame has the original 3 columns plus 6 added columns. Most pipelines end with a model stage that consumes `features` and produces `prediction`.

What you should appreciate from the trace: every stage adds exactly one or two columns. The shape evolves monotonically. There is no in-place mutation; the original `country`, `age`, `income` are still there. This is the immutable-DataFrame discipline from Chapter 58, applied to feature engineering.

---

## 63.11 Pitfalls, gathered

A few traps not already called out:

1. **`Imputer` on string columns.** It doesn't work. Use `fillna` on the DataFrame for strings, then `StringIndexer`.
2. **`StringIndexer` fit on training, then test row has unseen value.** Default behaviour: throw. Solution: set `handleInvalid="keep"` (recommended for features) or `"skip"` (for labels).
3. **Scaler `withMean=True` on a sparse Vector.** Densifies. Memory explodes for text data. Solution: set `withMean=False` for sparse features.
4. **`OneHotEncoder` consumed before `StringIndexer`.** OHE wants integer-indexed input, not strings. Wire `StringIndexer` first.
5. **Forgetting that scaling is fit on train only.** Don't `.fit` a scaler on the union of train and test; that leaks test statistics. Pipelines + CrossValidator handle this for you.
6. **Reordering stages in a way that breaks column dependencies.** Spark catches most of these at fit time with a clear error, but the message can be cryptic. Build pipelines bottom-up and run a tiny `.fit` early to validate the wiring before scaling up data.
7. **Confusing `Normalizer` with `StandardScaler`.** Both have "normalise" in their colloquial meaning. Different operations. `Normalizer` is row-wise; `StandardScaler` is column-wise.

---

## 63.12 What this chapter taught you, in one sentence

**The fifteen-or-so Transformers and small-Estimators in `pyspark.ml.feature` cover the feature-engineering vocabulary of 95% of projects; knowing what each one computes (assembling, indexing, encoding, scaling, bucketing, imputing, tokenising, vectorising, weighting, normalising) and how the Estimator/Transformer distinction shapes their behaviour is the foundation for every pipeline you will build.**

---

## 63.13 What this builds on / where this returns

**Builds on:**

- Chapter 24 (missing data taxonomy) — informs choices when wiring `Imputer`.
- Chapter 25 (categorical encoding, hashing trick) — `StringIndexer`, `OneHotEncoder`, `HashingTF` are the pyspark.ml expression of that material.
- Chapter 26 (numerical transformations) — `StandardScaler`, `MinMaxScaler`, `RobustScaler` are the toolbox.
- Chapter 28 (interactions, polynomial features) — `PolynomialExpansion` is the API.
- Chapter 62 — the Transformer/Estimator/Pipeline framework that lets us chain these.

**Returns:**

- Chapter 64 — Estimators that consume the `features` Vector this chapter teaches you to assemble.
- Chapter 65 — CrossValidator over Pipelines that contain these Transformers.
- Chapter 67 — when you outgrow built-in Transformers and write your own.

---

## 63.14 Exercises

1. **`VectorAssembler` with a Vector input.** Your DataFrame has columns `age`, `income`, and a `country_ohe` of type Vector (length 3). What does `VectorAssembler(inputCols=["age", "income", "country_ohe"], outputCol="features")` produce as the length of `features`?

2. **`StringIndexer` default behaviour on unseen value.** You fit a `StringIndexer` on training data containing `{"US", "UK", "IN"}`. At serve time you see `"FR"`. What happens with default `handleInvalid`, and what should you have set it to?

3. **`OneHotEncoder` length math.** You have a categorical with 8 distinct values. With default `dropLast`, what is the length of the OHE Vector? With `dropLast=False`?

4. **The collinearity argument.** Explain in two sentences why dropping the last OHE category prevents multicollinearity with the intercept in a linear regression with an `intercept=True`.

5. **Sparse-densification trap.** You apply `StandardScaler(withMean=True, withStd=True)` to a TF-IDF Vector column with 10,000 dimensions, 99.5% sparse. Estimate the memory footprint per row before and after the scaler. Suggest a fix.

6. **`Bucketizer` vs `QuantileDiscretizer`.** You want to bin `age` into "young / middle / old" using cutoffs 30 and 60. Which class do you use? You want to bin `income` into quartiles. Which class do you use? Justify each choice.

7. **`Imputer` strategy choice.** Your income column is right-skewed (long upper tail). Should you impute missing with mean or median? Justify.

8. **`CountVectorizer` vs `HashingTF`.** You're building a spam classifier for a streaming service that sees a million emails per hour. You don't care which specific words drive predictions. You do care about latency. Pick one and justify in 2-3 sentences.

9. **`PolynomialExpansion` on text.** A teammate suggests applying `PolynomialExpansion(degree=2)` to a 10,000-dimensional TF-IDF Vector to capture word co-occurrences. Why is this a bad idea? What's the right approach?

10. **`Normalizer` vs `StandardScaler` on text.** For a TF-IDF Vector intended for use with logistic regression and cosine-similarity-style coefficients, would you pick `Normalizer(p=2)` or `StandardScaler`? Why?

11. **Pipeline schema evolution.** Given the pipeline at section 63.10, list all columns in the output DataFrame in order. (Don't worry about exact column ordering; list the column names.)

12. **The dropLast default.** Why does `pyspark.ml`'s `OneHotEncoder` default to `dropLast=True` while scikit-learn's `OneHotEncoder` defaults to including all categories? What does this tell you about the audience each library expects?

<details>
<summary>Answers</summary>

1. `2 + 3 = 5`. `VectorAssembler` concatenates the lengths of all input Vectors with the scalar columns counted as length 1 each.

2. With default `handleInvalid="error"`, Spark raises a `SparkException`. For feature columns, set `handleInvalid="keep"` (assigns the unseen value a fresh integer); for label columns, `"skip"` is sometimes used.

3. With `dropLast=True`: length 7. With `dropLast=False`: length 8.

4. The intercept is the constant column. Without `dropLast`, every row's OHE entries sum to 1, which is exactly the intercept's value — so the design matrix is rank-deficient and the linear system has no unique solution. Dropping one category breaks the dependence, the design matrix becomes full-rank, and the model fits cleanly.

5. Before: sparse, ~50 non-zero entries × ~12 bytes each ≈ 600 bytes per row. After centering: dense, 10,000 × 8 bytes = 80,000 bytes per row — about 130× larger. Fix: set `withMean=False`. Center elsewhere if you need centering, or accept that for sparse data you should only scale (divide by std).

6. `Bucketizer` for age with `splits=[-inf, 30, 60, inf]` — you have domain-given cutoffs. `QuantileDiscretizer(numBuckets=4)` for income — quartiles are by definition equal-frequency, learned from data.

7. Median. The mean is pulled toward the long upper tail by extreme high-income values, so imputing missing entries with the mean overstates the typical missing value. The median is the robust choice for skewed distributions.

8. `HashingTF`. No fit pass, no vocabulary to persist, constant memory regardless of corpus growth. Since you don't need per-word interpretability, the collision cost is small with `numFeatures` set to an order of magnitude above expected effective vocabulary size.

9. The resulting Vector would have $\binom{10000+2}{2} \approx 5 \times 10^7$ dimensions per row. Memory and compute both explode. The right approach: use a model that finds interactions for you (tree ensembles, factorization machines) or hand-engineer a small number of meaningful pair features.

10. `Normalizer(p=2)` — it L2-normalises each row, which makes dot products with the learned coefficient vector behave like cosine similarity. `StandardScaler` would densify the sparse TF-IDF vector (the centering pitfall) and isn't the right semantic operation.

11. `country, age, income, country_idx, country_ohe, age_imp, income_imp, features_raw, features`. Nine columns: the original three plus six added by the five stages.

12. `pyspark.ml` expects linear models with `intercept=True` to be the default audience and chose to handle the collinearity problem for the user. scikit-learn assumes the user knows their model class and may want all categories (e.g., for tree models or for `intercept=False` regressions). It's a defaults-for-the-common-case choice on both sides.

</details>
