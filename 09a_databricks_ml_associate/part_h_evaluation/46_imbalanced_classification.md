# Chapter 46 — Imbalanced Classification

> **Goal of this chapter:** to take the metrics we developed in Chapters 42–44 and use them as the foundation for an engineering response to the most common pathology in real-world classification: **imbalance**. Fraud is 0.1% of transactions. Churn is 5% of customers per month. Manufacturing defects are 1% of units. Rare-disease screening is 0.01% positive. Most real classification problems are imbalanced, often severely. Standard out-of-the-box training procedures — fit a logistic regression, threshold at 0.5, ship — degrade catastrophically on imbalanced data. The model learns to predict the majority class for everything, scores 99% accuracy, and is operationally useless.
>
> This chapter is the layered response. Stratified sampling. Class weights. Threshold tuning. Random resampling (under and over). SMOTE and its variants. Anomaly detection when positives are *extremely* rare. We will see that no single technique is a silver bullet — the practitioner's job is to apply the right combination for the data and downstream cost structure. By the end of this chapter you should be able to (a) diagnose when imbalance is the problem, (b) reach for the right tool from a tiered checklist, and (c) avoid the bone-deep pitfalls (especially: never resample the validation or test set).

---

## 46.1 What "imbalanced" means, precisely

Class imbalance means the positive and negative classes have very different prevalences. There's a spectrum:

- **Mild imbalance** (60/40 or 70/30): standard methods mostly work. Accuracy is misleading; report precision/recall. No special techniques needed.
- **Moderate imbalance** (90/10 or 95/5): churn-prediction territory. Class weights help. Threshold tuning matters. Default $\tau = 0.5$ is rarely optimal.
- **Severe imbalance** (99/1 to 99.9/0.1): fraud, manufacturing defect detection. Class weights + threshold tuning are necessary. Resampling becomes worth considering. Stratified CV is mandatory.
- **Extreme imbalance** (>99.99/<0.01): rare-disease screening, click prediction at the long-tail. Classification may not be the right framing — consider anomaly detection or two-stage approaches.

The treatment intensifies as you move down this spectrum. The diagnostic for "is imbalance hurting my model" is simple: does the model predict the minority class at all? If recall on the positive class is near zero — the model is essentially always predicting negative — imbalance is your problem. If recall is moderate but precision is poor, the imbalance still affects you (because FP volume scales with the negative class), but the model is at least *trying* to predict positives.

For the rest of this chapter we'll use **prevalence** $p = P(y = 1)$ as the parameter governing how aggressively to apply imbalance techniques. We'll work through a running example: a churn-prediction problem with $n = 10{,}000$, $p = 5\%$ — so 500 positives and 9,500 negatives.

---

## 46.2 Tier 1 — Stratified sampling everywhere

The first defense is mechanical: ensure your train/val/test splits and cross-validation folds preserve the class proportions.

A naive random 70/15/15 split on 10,000 examples with 5% positives will, in expectation, put 350 positives in train, 75 in validation, 75 in test. In practice, sampling variance means you could get 65 positives in test (or 85). For *extreme* imbalance — say, 50 positives in 10,000 — a random fold could easily end up with 0 positives, and your metrics would be degenerate.

**Stratified sampling** splits each class separately:

- Of the 500 positives, take 70% (350) for train, 15% (75) for val, 15% (75) for test.
- Of the 9,500 negatives, take 70% (6,650) for train, 15% (1,425) for val, 15% (1,425) for test.
- Recombine.

The class proportions are now exactly preserved across all three splits. This is the default for sklearn's `train_test_split(..., stratify=y)` and for `StratifiedKFold` cross-validation. It is *not* the default for sklearn's plain `KFold` or for Spark's `randomSplit`.

### 46.2.1 The Spark gotcha — randomSplit does NOT stratify

This catches teams new to PySpark. The standard idiom for splitting a DataFrame is:

```python
train, val, test = df.randomSplit([0.7, 0.15, 0.15], seed=42)
```

This is a **per-row independent sample**, not a stratified split. The probability that a given row ends up in `train` is 70%, regardless of label. For balanced or mildly imbalanced data this is fine; for severely imbalanced data it can produce splits with very different positive counts than the population.

For stratified splitting in PySpark, you have two options.

**Option A: split each class separately, then union.**

```python
positives = df.filter("label = 1")
negatives = df.filter("label = 0")

pos_train, pos_val, pos_test = positives.randomSplit([0.7, 0.15, 0.15], seed=42)
neg_train, neg_val, neg_test = negatives.randomSplit([0.7, 0.15, 0.15], seed=42)

train = pos_train.union(neg_train)
val = pos_val.union(neg_val)
test = pos_test.union(neg_test)
```

Now each split has exactly 70/15/15 of *each* class.

**Option B: use `sampleBy` with per-class fractions.**

```python
fractions = {0: 0.7, 1: 0.7}
train = df.sampleBy("label", fractions, seed=42)
remainder = df.subtract(train)
# Continue similarly for val/test from the remainder.
```

`sampleBy` is a stratified sample, but the standard cookbook is Option A — it's clearer and easier to reason about. For cross-validation, Spark ML's `CrossValidator` does **not** stratify either; if you need stratified CV in Spark, you must either implement it yourself or use scikit-learn for CV (with the Spark model trained on each fold's data).

### 46.2.2 Stratification for CV

The same logic applies to k-fold CV. Standard k-fold creates $k$ folds where every row has 1/k probability of being in each fold; stratified k-fold creates folds with the same class proportions as the overall data. For imbalanced classification, **always use stratified k-fold**. sklearn:

```python
from sklearn.model_selection import StratifiedKFold
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
for train_idx, val_idx in skf.split(X, y):
    ...
```

For Spark's `CrossValidator`, you'd need to construct stratified folds manually and pass them via a custom fold-assignment column. Chapter 65 covers this when we treat CrossValidator in depth.

The recurring theme: stratification is free, mechanical, and the first line of defense. It doesn't fix the underlying training problem — that's the next tier — but it ensures evaluation isn't compromised by sampling noise.

---

## 46.3 Tier 2 — Class weights

Most classifiers compute a loss that is summed over training examples:

$$
L(\theta) = \frac{1}{n} \sum_i \ell(y_i, \hat{y}_i; \theta)
$$

In an imbalanced training set, this sum is dominated by the majority class. If 95% of examples are negative, 95% of the loss comes from negatives — the model "tries hardest" to fit them, which is exactly why it learns to predict the majority class for everything.

The fix: **weight each example by the inverse of its class's frequency**. The new loss is:

$$
L_w(\theta) = \frac{1}{n} \sum_i w_{y_i} \cdot \ell(y_i, \hat{y}_i; \theta)
$$

where $w_y$ is the weight for class $y$. Common scheme: $w_y \propto 1/p_y$, so the positive class (rare) gets a high weight and the negative class (common) gets a low weight. Specifically, `class_weight='balanced'` in sklearn uses:

$$
w_y = \frac{n}{K \cdot n_y}
$$

where $K$ is the number of classes and $n_y$ is the count of class $y$. For a 95/5 problem with $n = 10{,}000$:

- $w_0 = 10{,}000 / (2 \cdot 9{,}500) = 0.526$.
- $w_1 = 10{,}000 / (2 \cdot 500) = 10.0$.

So positive examples have weight 10 and negative examples have weight 0.526. The ratio is about 19:1, exactly inverse to the class ratio. Each positive example "counts as much" as 19 negative examples in the loss. The model now has equal incentive to fit both classes.

### 46.3.1 What class weights actually do

Geometrically, class weights are equivalent to **upweighting the minority class**. You can think of it as:

> Pretending we have $w_y$ copies of each example of class $y$, then training on the augmented dataset.

That's a useful mental model, and it implies an important nuance: class weights *modify the loss function*, they do not change the data. So they're available in any classifier that supports weighted examples — which is most. They also work cleanly for *gradient-based* training; for closed-form solvers, they modify the weighted least-squares normal equations.

### 46.3.2 Pros and cons

**Pros:**

- Free — no resampling, no new data, no preprocessing.
- Conceptually clean — you're just changing what the optimizer cares about.
- Works for any algorithm that supports sample weights (logistic regression, SVMs, trees, GBMs, neural networks).
- Provably equivalent to certain types of resampling under mild assumptions.

**Cons:**

- Models trained with class weights are still "trained on the natural distribution" of the data — i.e., the score function calibration is slightly off. Predicted probabilities tend to be too high for the positive class. If you need calibrated probabilities, you may need to re-calibrate post-hoc.
- Some algorithms have idiosyncratic interactions with weights. Tree splits, for example, use weighted impurity — usually fine but worth checking.

### 46.3.3 Class weights in sklearn

```python
from sklearn.linear_model import LogisticRegression

# Option A: built-in 'balanced' (inversely proportional to class frequency)
clf = LogisticRegression(class_weight='balanced').fit(X_train, y_train)

# Option B: explicit weights
clf = LogisticRegression(class_weight={0: 1.0, 1: 19.0}).fit(X_train, y_train)
```

Most sklearn classifiers accept `class_weight`. Some (gradient boosting, random forests) support both `class_weight` and an explicit `sample_weight=` argument to `.fit()`.

### 46.3.4 Class weights in pyspark.ml — the weightCol pattern

Spark uses a different pattern: instead of a `class_weight` parameter, you add a **weight column** to your DataFrame, with each row's weight as a value:

```python
from pyspark.sql import functions as F

# Compute weights from class frequencies
n_total = df.count()
n_pos = df.filter("label = 1").count()
n_neg = n_total - n_pos
K = 2
w_pos = n_total / (K * n_pos)
w_neg = n_total / (K * n_neg)

df_weighted = df.withColumn(
    "weight",
    F.when(F.col("label") == 1, w_pos).otherwise(w_neg)
)

from pyspark.ml.classification import LogisticRegression
lr = LogisticRegression(
    labelCol="label",
    featuresCol="features",
    weightCol="weight"   # tells the model to use this column as sample weights
)
model = lr.fit(df_weighted)
```

Quirks:

- Not all pyspark.ml estimators support `weightCol`. LogisticRegression and DecisionTreeClassifier do; some others don't or have different mechanisms.
- The weights are *per-row*, not per-class. You can compute them however you want (inverse frequency, custom cost-based weights, sample-importance weights, etc.).
- Compute the weights from the *training* data, not the full dataset, to avoid leakage.

---

## 46.4 Tier 3 — Threshold tuning

We covered the threshold dial in Chapter 42, but in the imbalanced-classification context it deserves emphasis: the default $\tau = 0.5$ is even less appropriate when the data is imbalanced.

Logistic regression on imbalanced data tends to produce *score distributions* concentrated on the negative class. With 95% negatives, the score for most examples will be well below 0.5; only the most clear-cut positives will exceed 0.5. At $\tau = 0.5$, recall will be poor.

**Empirical rule of thumb:** for an imbalanced problem with prevalence $p$ trained *without* class weights, the F1-optimal threshold is often close to $p$. For prevalence 5%, try $\tau \approx 0.05$ as a starting point. For 1%, try $\tau \approx 0.01$. This is informal — the true optimum depends on the score distribution — but it's a useful starting heuristic.

With class weights, the score distribution shifts and the optimal threshold creeps back up toward 0.5. The two interventions interact: if you use class weights AND retune the threshold, you may find the threshold settles around 0.3–0.5 even on imbalanced data.

### 46.4.1 The proper procedure

Don't guess the threshold. Compute it from the validation set:

1. Train the model (with class weights or without).
2. Score all validation examples.
3. Sweep the threshold from 0 to 1 in small increments.
4. At each threshold, compute the metric you care about (F1, F-beta, expected cost, recall-at-fixed-FPR, etc.).
5. Pick the threshold that optimises the metric.
6. **Lock that threshold for production**, with the model.

The validation set's threshold should generalise to the test set (and to production). If it doesn't — if the optimal threshold shifts substantially between validation and test — you have either too small a validation set or a distribution-shift problem.

A common pattern in production code:

```python
# After training:
val_scores = model.predict_proba(X_val)[:, 1]

best_threshold = 0.5
best_f1 = 0
for tau in np.linspace(0.01, 0.99, 99):
    preds = (val_scores >= tau).astype(int)
    f1 = f1_score(y_val, preds)
    if f1 > best_f1:
        best_f1, best_threshold = f1, tau

# Store best_threshold alongside the model artifact.
# At inference time:
production_preds = (model.predict_proba(X_new)[:, 1] >= best_threshold).astype(int)
```

The threshold is part of the model artifact. Treat it accordingly — versioned, monitored, A/B-tested if you change it.

---

## 46.5 Tier 4 — Resampling: under- and oversampling

When class weights and threshold tuning aren't enough — typically at severe imbalance, prevalence < 5% — you may need to *change the training data itself*. Two basic approaches: drop majority examples, or duplicate (or synthesize) minority examples.

### 46.5.1 Random undersampling

**Random undersampling**: drop a random subset of majority examples until the classes are balanced (or have a chosen ratio).

For our running 10K-row 5%-positive example: keep all 500 positives, randomly drop 9,000 of the 9,500 negatives, ending with a 1,000-row 50/50 training set.

**Pros:**

- Simple. Easy to implement (sklearn's `RandomUnderSampler` from imbalanced-learn; or a `df.sample(...)` call).
- Much faster training on huge datasets — you're training on far fewer examples.
- Sometimes the only feasible approach when the majority class is so large it doesn't fit in memory.

**Cons:**

- Throws away data. With 9,500 negatives discarded, the model never sees most of the variability in the negative class. May underfit on negatives.
- Reduces effective sample size — variance of trained model is higher; less stable.
- Discarding doesn't change the world's true class distribution; the model's score calibration is now warped for production.

When to use: when the majority class is huge (millions+) and you can afford to lose most of it without losing class variability. Less useful when data is precious.

### 46.5.2 Random oversampling

**Random oversampling**: duplicate randomly chosen minority examples until classes are balanced.

For our example: keep all 9,500 negatives, randomly duplicate the 500 positives 19 times each, ending with a 19,000-row dataset that's 50/50.

**Pros:**

- No data thrown away.
- Conceptually simple.

**Cons:**

- The model sees identical examples repeated. For algorithms with memorization risk (trees with no depth limit, k-NN), this *guarantees* the duplicated examples are "memorized" — overfitting on the minority class.
- Doesn't add information. Just shifts the training distribution.

When to use: rarely standalone. Usually inferior to class weights, which achieve the same loss-balance without the memorization risk.

### 46.5.3 The SMOTE family — synthesizing new minority examples

**SMOTE (Synthetic Minority Over-sampling Technique)** addresses oversampling's memorization risk by *generating new* minority examples rather than duplicating existing ones.

The algorithm:

1. For each minority example $x$, find its $k$ nearest neighbors (among other minority examples).
2. Pick one neighbor $x'$ at random.
3. Synthesize a new example along the line segment from $x$ to $x'$:

   $$
   x_{\text{new}} = x + \lambda (x' - x), \quad \lambda \sim U(0, 1)
   $$

   That is, pick a random point between $x$ and $x'$ and call it a new minority example.

4. Repeat until the minority class is balanced.

The intuition is that the minority class lives in some region of feature space; the SMOTE examples *interpolate* between known minority points, filling out that region with plausible-looking new examples. The model sees a denser, more varied minority class.

### 46.5.4 SMOTE in practice — the imbalanced-learn library

SMOTE is implemented in `imbalanced-learn`:

```python
from imblearn.over_sampling import SMOTE

smote = SMOTE(sampling_strategy=1.0, k_neighbors=5, random_state=42)
X_train_resampled, y_train_resampled = smote.fit_resample(X_train, y_train)
# Now train on (X_train_resampled, y_train_resampled).
```

Variants worth knowing:

- **Borderline-SMOTE**: only synthesize from minority examples on the "borderline" (near the decision boundary). More conservative; less likely to add noise in the heart of the minority cluster.
- **ADASYN (Adaptive Synthetic Sampling)**: oversample harder-to-learn minority examples more, easier-to-learn ones less. Tries to focus the synthesis where it matters.
- **SMOTE-NC**: handles categorical features (vanilla SMOTE only does continuous features properly because interpolating categoricals doesn't make sense).
- **SMOTE + Tomek** or **SMOTE + ENN**: combine SMOTE oversampling with post-hoc cleanup of overlapping examples.

SMOTE is not available in pyspark.ml directly. If you need it on Spark, options include:

- Resample on the driver after `.toPandas()` (only works for moderate-size data).
- Use `synapse.ml` (formerly MMLSpark) — Microsoft's Spark ML extension that includes SMOTE.
- Implement it as a custom transformer (non-trivial).
- Sidestep with class weights, which often work nearly as well.

### 46.5.5 The hidden trap of resampling — never resample test data

This is the most common, most pernicious resampling pitfall:

> **Resample only the training set. Never the validation or test set.**

Why? Because resampling changes the class distribution. If you SMOTE-balance your test set to 50/50, then evaluate the model on it, you're computing metrics on a *fake* distribution. Precision, recall, F1, all of them — they'll be inflated relative to the actual production performance.

A model that achieves precision = 0.85 on a SMOTE-balanced test set (50% positives) might have precision = 0.15 on production data (1% positives). Same model, same scores. The difference is entirely the change in the FP/TP ratio when negatives are reweighted (or, in this case, undersampled by SMOTE rebalancing).

The right pattern:

1. Split into train, val, test.
2. **Resample only train.** Resampling fits and transforms on train alone.
3. Evaluate on val and test as-is, with their original class distributions.
4. Report metrics on test data as a faithful reflection of expected production performance.

If you've ever seen a tutorial that does "SMOTE the entire dataset, then train_test_split," that tutorial is wrong. It's a leading cause of "I got 99% accuracy in evaluation but the model is terrible in production" stories.

A related corollary: when you do cross-validation with resampling, the resampling step must be *inside the CV loop*, applied only to the training fold. sklearn's `Pipeline` with `imbalanced-learn`'s `Pipeline` (note: different from sklearn's) handles this correctly — the resampler is treated as a fit-only step.

```python
from imblearn.pipeline import Pipeline as ImbPipeline
from imblearn.over_sampling import SMOTE
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score, StratifiedKFold

pipeline = ImbPipeline([
    ('smote', SMOTE(random_state=42)),
    ('clf', LogisticRegression())
])

# SMOTE is applied only to the training fold of each CV iteration:
scores = cross_val_score(pipeline, X, y,
                          cv=StratifiedKFold(5),
                          scoring='f1')
```

The `imblearn.pipeline.Pipeline` (not sklearn's) knows that SMOTE is only for training and skips it at evaluation time. Using sklearn's regular `Pipeline` here would apply SMOTE to the test fold too — the trap.

---

## 46.6 Tier 5 — Reframing as anomaly detection

When positives are *extremely* rare — say, under 0.1% — the supervised-classification framing starts to break down. You don't really have enough positive examples to characterize the class, and SMOTE or class weights are stretching one-sided.

The alternative framing is **anomaly detection**:

> Train a model on the negatives only. At inference, score each new example by how "unusual" it is relative to the learned negative distribution. Flag the unusual ones for review.

This is a *one-class* learning problem. You're learning what "normal" looks like, then detecting deviations.

Common anomaly-detection algorithms:

- **Isolation Forest**: builds random trees; isolated leaves (paths from root) are "unusual." Examples that get isolated quickly are anomalies.
- **One-Class SVM**: learns a tight boundary around the negative class; examples outside the boundary are anomalies.
- **Autoencoder**: train a neural network to reconstruct examples; high reconstruction error → anomaly.
- **Gaussian Mixture / KDE**: fit a density model on negatives; low-density examples are anomalies.

When to switch from classification to anomaly detection: roughly when prevalence drops below 0.1% AND you have few enough positives that you couldn't meaningfully train a discriminative model on them (say, fewer than a few hundred positives). For 1% prevalence with 10,000 positives in 1M examples, classification is still the right framing. For 0.001% with 10 positives in 1M, anomaly detection is more honest — you don't have enough positives to learn from.

Many production fraud systems are actually *two-stage*: an anomaly-detection layer catches the bulk of the unusual cases, then a supervised classifier (trained on labels collected by the anomaly system) refines among the flagged ones.

Anomaly detection is largely out of scope for the Databricks ML Associate exam, but knowing it exists as a framing alternative is part of the working competence.

---

## 46.7 Evaluation framework for imbalanced problems

We've talked about training-side interventions. The evaluation framework is equally important:

1. **Don't use accuracy.** It's misleading at all but the most balanced prevalences.
2. **Use precision, recall, F1, F-beta** as your primary metrics. They focus on the positive class.
3. **Use PR-AUC, not just ROC-AUC.** As Chapter 44 hammered: ROC can be misleadingly high for imbalanced problems.
4. **Use stratified CV** (or train/val/test splits) to avoid sampling-variance noise in your evaluation.
5. **Tune the threshold on the validation set** for the operational metric.
6. **Report multiple metrics together.** ROC-AUC + PR-AUC + F1 + precision + recall at the deployed threshold. Five numbers tell a story; one misleads.
7. **Report the prevalence.** PR-AUC of 0.4 is dreadful at 50% prevalence and brilliant at 0.1%. Always say what the baseline is.

---

## 46.8 Worked example — logistic regression on a 5%-positive dataset

Let's run through the techniques on a single example to see them in interaction.

Setup: 10,000 rows, 5% positive (500 positives, 9,500 negatives). We split 70/15/15 stratified: training has 350 positives and 6,650 negatives; validation has 75 positives and 1,425 negatives; test has 75 positives and 1,425 negatives.

**Version 1: vanilla logistic regression, default $\tau = 0.5$.**

The model trains. On validation:

- Predictions: 30 predicted positive, 1,470 predicted negative.
- TP = 25, FP = 5, FN = 50, TN = 1,420.
- Precision = 25/30 = 83.3%. Recall = 25/75 = 33.3%. F1 = 0.476.

Recall is terrible — we catch only a third of churners. The model is biased toward predicting negative, as expected for imbalanced training.

**Version 2: add `class_weight='balanced'`.**

The model trains with class weights $w_0 \approx 0.526$, $w_1 \approx 10$. On validation at $\tau = 0.5$:

- Predictions: 150 predicted positive.
- TP = 60, FP = 90, FN = 15, TN = 1,335.
- Precision = 60/150 = 40.0%. Recall = 60/75 = 80.0%. F1 = 0.533.

Recall jumped from 33% to 80% — much better at catching churn. But precision dropped from 83% to 40% — the model is more aggressive, flagging too many false positives. The F1 improved modestly (0.476 → 0.533). Whether this trade is worth it depends on the cost matrix.

**Version 3: class weights + threshold tuning on validation.**

We sweep the threshold from 0 to 1 and find the F1-optimal value, say $\tau = 0.62$ (some threshold higher than 0.5 because class weights have inflated scores). At $\tau = 0.62$:

- Predictions: 90 predicted positive.
- TP = 55, FP = 35, FN = 20, TN = 1,390.
- Precision = 55/90 = 61.1%. Recall = 55/75 = 73.3%. F1 = 0.667.

F1 is up to 0.667 — meaningful improvement over both Version 1 and Version 2. The class weights gave the model the incentive to predict positives; the threshold sweep recovered precision by demanding higher confidence before flagging.

This is the typical pattern: **class weights + threshold tuning beats either alone**. The combination handles both training-side and inference-side imbalance.

**Version 4: SMOTE on training data + default $\tau = 0.5$.**

We SMOTE-balance the training set to 50/50, train, evaluate on the original (unresampled) validation set:

- Predictions: roughly similar to Version 2 — maybe slightly different.
- Typically: precision 38%, recall 78%, F1 0.51.

SMOTE doesn't usually outperform class weights for moderate-to-severe imbalance. It can help when class weights aren't available (uncommon) or when the minority class has complex structure that benefits from synthetic interpolation. Empirically: try class weights first, then SMOTE second if class weights underperform, then SMOTE + threshold tuning.

**Final test-set evaluation:** With Version 3's $\tau = 0.62$, evaluate on the held-out test set. Numbers should resemble validation; report precision, recall, F1, plus PR-AUC and ROC-AUC.

The end-to-end picture: a vanilla approach gave F1 = 0.48; the engineered pipeline (class weights + threshold tuning + stratified CV) gave F1 = 0.67. That's a real, substantial improvement that ships.

---

## 46.9 Anti-patterns to avoid

A consolidated list of the patterns this chapter has implicitly warned against:

1. **Optimizing accuracy on imbalanced data.** Use F1 / PR-AUC.
2. **Using vanilla `train_test_split` or `randomSplit` for imbalanced data.** Use stratified splits.
3. **Default $\tau = 0.5$.** Tune the threshold to your business metric.
4. **Resampling the test set.** Never. Resample train only.
5. **Resampling outside the CV loop.** Use imblearn's Pipeline or implement resampling inside each fold.
6. **Reporting one metric.** Report multiple — F1 + PR-AUC + precision + recall, with prevalence.
7. **Stacking interventions blindly.** Class weights + heavy SMOTE + low threshold = double-counting the imbalance fix. Apply one tier of intervention; only escalate if needed.
8. **Forgetting the prevalence shift in production.** If your test set was constructed differently from production traffic, expected metrics will be wrong.

---

## 46.10 The Spark and sklearn surface — quick reference

### sklearn

```python
# Stratified split
from sklearn.model_selection import train_test_split
X_train, X_val, y_train, y_val = train_test_split(
    X, y, test_size=0.3, stratify=y, random_state=42
)

# Stratified CV
from sklearn.model_selection import StratifiedKFold
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# Class weights
clf = LogisticRegression(class_weight='balanced')
# or:
clf = LogisticRegression(class_weight={0: 1.0, 1: 19.0})

# SMOTE
from imblearn.over_sampling import SMOTE
sm = SMOTE(random_state=42)
X_train_resampled, y_train_resampled = sm.fit_resample(X_train, y_train)

# Pipeline with resampling (resampler only fits on train data)
from imblearn.pipeline import Pipeline as ImbPipeline
pipeline = ImbPipeline([('smote', SMOTE()), ('clf', LogisticRegression())])
```

### pyspark.ml

```python
# Stratified split — manual via union of per-class splits
positives = df.filter("label = 1")
negatives = df.filter("label = 0")
pos_train, pos_test = positives.randomSplit([0.7, 0.3], seed=42)
neg_train, neg_test = negatives.randomSplit([0.7, 0.3], seed=42)
train = pos_train.union(neg_train)
test = pos_test.union(neg_test)

# Class weights via weightCol
df_weighted = df.withColumn(
    "weight",
    F.when(F.col("label") == 1, w_pos).otherwise(w_neg)
)
lr = LogisticRegression(weightCol="weight", labelCol="label", featuresCol="features")

# SMOTE — not native; use synapseml or sidestep with class weights.
```

---

## 46.11 Summary

The bones:

1. **Imbalanced classification** is when one class is far more common than the other. Standard methods fail; positives are underpredicted; accuracy is misleading.
2. **Tier 1: stratification.** Split data preserving class proportions. Default in sklearn (`stratify=y`, `StratifiedKFold`). Manual in Spark (split by class, then union).
3. **Tier 2: class weights.** Modify the loss so the minority class is upweighted (`class_weight='balanced'` in sklearn; `weightCol` in pyspark.ml). Free, simple, often sufficient.
4. **Tier 3: threshold tuning.** The default $\tau = 0.5$ is rarely optimal. Sweep thresholds on the validation set; pick the operationally-optimal one; lock it with the model.
5. **Tier 4: resampling.** Random undersampling discards majority data — fast but loses information. Random oversampling duplicates minority — risks memorization. **SMOTE** synthesizes new minority examples by interpolation. Variants (Borderline-SMOTE, ADASYN, SMOTE-NC).
6. **The unbreakable rule:** resample TRAIN data only. Never val or test. Use imblearn's Pipeline (not sklearn's) to keep this discipline within CV.
7. **Tier 5: reframe as anomaly detection** when positives are extremely rare (< 0.1%). Train on negatives; flag unusual.
8. **Evaluation framework:** PR-AUC > ROC-AUC for imbalanced problems. Report multiple metrics with prevalence.
9. The pattern in practice: class weights + threshold tuning is usually the sweet spot. SMOTE is a Tier 4 escalation. Anomaly detection is for extreme cases.

If you can diagnose imbalance (recall on positive class near zero with high accuracy is the tell), apply the tiered toolkit, and avoid the "resample the test set" trap — you have the chapter.

---

## 46.12 What this builds on / where this returns

**Builds on:** Chapter 21 (train/val/test discipline). Chapter 22 (CV, stratified CV). Chapter 32 (logistic regression — supports `class_weight` / `weightCol` natively). Chapters 42–44 (precision, recall, F1, PR-AUC — the metrics for imbalanced problems).

**Returns:**

- **pyspark.ml evaluators** that compute these metrics — *Chapter 66*.
- **CrossValidator** and stratified CV in Spark — *Chapter 65*.
- **End-to-end project on Lending Club** — a real imbalanced classification (default rate ~15%) — *Chapter 74*.

---

## 46.13 Exercises

Cold attempt.

1. **Spotting the diagnostic.** A classification model on a 1%-positive dataset reports: accuracy 99.0%, precision N/A (no predicted positives), recall 0%. What's happening, and what's your first intervention?

2. **The Spark stratified-split trap.** A teammate writes:

   ```python
   train, test = df.randomSplit([0.8, 0.2], seed=42)
   ```

   on a 0.5%-positive dataset of 100,000 rows. After the split, train has 410 positives and test has 90 — even though stratified would give 400 and 100. Why does this matter for evaluation? Rewrite to fix.

3. **Class weights — compute by hand.** For a dataset with 8,000 negative and 200 positive examples, compute the `class_weight='balanced'` weights for each class. Verify the ratio of weights matches the inverse of the class ratio.

4. **Threshold direction.** You train a logistic regression with `class_weight='balanced'` on 5%-positive data. After training, you notice positive-class scores cluster around 0.5–0.6, not 0.05 as before. Why did this happen, and what should you set the threshold to?

5. **SMOTE intuition.** Describe in your own words how SMOTE differs from random oversampling. Why is SMOTE less likely to overfit on the minority class?

6. **The test-set trap.** A team applies SMOTE to the entire dataset before splitting into train and test. They get F1 = 0.95 on the test set, ship the model, and report production F1 = 0.40. Diagnose the bug. What did they observe vs. what is the real model performance?

7. **Resample inside CV.** Write pseudocode for a 5-fold CV procedure that applies SMOTE only to each training fold and evaluates on the (unresampled) validation fold. Why is the order important?

8. **Class weights vs. SMOTE — when to escalate.** Under what circumstances would you escalate from class weights to SMOTE? Give two scenarios where SMOTE would plausibly outperform class weights, and one where it would not.

9. **Anomaly detection threshold.** Your fraud problem has 0.05% prevalence. You train a supervised classifier and it performs poorly. What does this tell you, and what's your next step?

10. **Precision–recall in production shift.** Your test set has 30% positives (you upsampled for evaluation). Production has 3% positives. Your test PR-AUC is 0.80. Will production PR-AUC be higher, lower, or the same? Why?

11. **Implementing stratified split in Spark.** Write the PySpark code to do a 70/15/15 stratified split on a DataFrame `df` with a `label` column having values 0 and 1.

12. **Combined-intervention pitfall.** A team applies all of: class weights, SMOTE oversampling to 50/50, AND threshold tuning to $\tau = 0.2$. The model's recall on training is 100% but precision is 12%. What is being double-counted? How should the team simplify?

<details>
<summary>Answers</summary>

1. The model has collapsed to "always predict negative." This is the classic imbalance failure mode. First intervention: enable class weights (`class_weight='balanced'` in sklearn, `weightCol` in Spark). If that doesn't help enough, also tune the threshold.

2. `randomSplit` is per-row independent — sampling variance can lead to class-count imbalances across splits, which compromises the test set as a reliable evaluation. With 90 positives in test instead of 100, you have less statistical power to estimate recall; your test-set metrics are noisier. Fix: stratified split (split positives and negatives separately, union).

3. K = 2. Total n = 8,200. $w_0 = 8200 / (2 \cdot 8000) = 0.5125$. $w_1 = 8200 / (2 \cdot 200) = 20.5$. Ratio: 20.5 / 0.5125 = 40. Class ratio: 8000/200 = 40. They match (inverse — the rare class gets the high weight).

4. With class weights, the minority class's loss gets multiplied by the weight ratio (here ~19×). The optimizer "pushes harder" on minority examples — their predicted scores rise. Default $\tau = 0.5$ may now be roughly OK, but it's still worth tuning on the validation set. Don't blindly set $\tau$ to the prevalence (which is the rule for *unweighted* training) — with weights, the optimal threshold is typically much closer to 0.5.

5. Random oversampling duplicates existing minority examples — the model sees the same row repeatedly. SMOTE *interpolates* between minority examples and their neighbors, creating new synthetic points along the line segments. SMOTE adds variability — the model sees a denser, smoother minority region rather than identical repeats — which reduces the risk of memorizing specific minority examples.

6. SMOTE applied to the entire dataset means synthetic positives leaked into the test set. The model evaluated on the test set was scoring on examples that were *generated from* training-time minority data. Effectively, training and test sets overlapped via the synthesis process. Real performance: closer to 0.40 (production reality); the 0.95 was inflated by the leak. Fix: split first, SMOTE only on training data, evaluate on raw test data.

7. ```
   For each of the 5 folds:
       Determine train_indices and val_indices
       X_train_fold, y_train_fold = X[train_indices], y[train_indices]
       X_val_fold, y_val_fold = X[val_indices], y[val_indices]
       
       # Apply SMOTE ONLY to training fold
       X_train_smote, y_train_smote = SMOTE().fit_resample(X_train_fold, y_train_fold)
       
       # Train on SMOTE'd training data
       model.fit(X_train_smote, y_train_smote)
       
       # Evaluate on the UNRESAMPLED validation fold
       score = evaluate(model, X_val_fold, y_val_fold)
   
   Aggregate scores across folds.
   ```
   Order matters: applying SMOTE outside the loop (to the full dataset) leaks synthetic positives into the validation folds.

8. Escalate when class weights alone produce mediocre recall AND there are enough minority examples that synthetic interpolation makes geometric sense (50+ minority examples). Scenarios where SMOTE outperforms: (a) minority class has multiple clusters that class weights can't represent well; (b) features are mostly continuous (SMOTE interpolation is well-defined). Where SMOTE underperforms: (c) high-dimensional sparse data (text/TF-IDF) — SMOTE creates synthetic examples that fall outside the manifold of real text.

9. With 0.05% prevalence, supervised classification is straining at the limits — too few positives to learn discriminative patterns from. Next step: reframe as anomaly detection. Train an isolation forest or one-class SVM on the negatives only; flag examples that look unusual. Use the supervised model as a second-stage refiner on the anomalies, if labels are available.

10. Lower. PR-AUC depends on the relative volume of FP vs. TP at each threshold. In production with 10× fewer positives per negative, FPs swamp TPs at any operating threshold, dropping precision and PR-AUC dramatically. The test PR-AUC was inflated by the (non-representative) 30%-positive evaluation. Honest reporting: re-evaluate on a held-out test set with production-like prevalence, OR explicitly correct for prevalence shift.

11. ```python
    positives = df.filter("label = 1")
    negatives = df.filter("label = 0")
    
    pos_train, pos_val, pos_test = positives.randomSplit([0.7, 0.15, 0.15], seed=42)
    neg_train, neg_val, neg_test = negatives.randomSplit([0.7, 0.15, 0.15], seed=42)
    
    train = pos_train.union(neg_train)
    val   = pos_val.union(neg_val)
    test  = pos_test.union(neg_test)
    ```

12. They're stacking imbalance corrections. Class weights upweight minority loss by ~20× (for 5% prevalence). SMOTE rebalances to 50/50, effectively adding another factor of ~10× weight. Threshold $\tau = 0.2$ further favors positive predictions. The combined effect: the model is wildly biased toward predicting positive — precision collapses, recall hits 100%. Simplify: pick ONE training-side intervention (class weights OR SMOTE, not both), then tune the threshold to the operating point you want.

</details>
