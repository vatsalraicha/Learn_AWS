# Chapter 34 — Random Forests — Bagging, OOB Error, Feature Importance

> **Goal of this chapter:** to understand why averaging many decision trees produces one of the most reliable, broadly-useful ML algorithms ever invented — and to understand the *specific* mechanisms (bootstrap sampling, feature subsampling) that make a random forest more than just "a tree, but more of it." The variance-reduction story is one of the few ideas in classical ML where a precise probabilistic argument leads directly to a practical algorithm that wins on real data. We'll walk that argument.

---

## 34.1 The variance problem with single trees

Chapter 33 ended on a frustration: single decision trees are *high-variance*. Re-sample the training data slightly and the tree can change drastically — different splits, different subtrees, different predictions. The bias-variance decomposition of Chapter 19 told us that high-variance models have high test error even when bias is low.

This frustration was unresolved until 1996, when Leo Breiman published two papers that, together, gave us what is now called the Random Forest. The trick is *averaging* many high-variance, low-bias trees so that their individual idiosyncrasies cancel out, while their shared signal persists.

The argument is precise and worth following carefully.

---

## 34.2 The variance-reduction calculation

Suppose we have $B$ predictors $\hat{y}_1, \hat{y}_2, \ldots, \hat{y}_B$, each with the same mean $\mu$ and same variance $\sigma^2$. Their average is

$$
\bar{y} = \frac{1}{B} \sum_{b=1}^B \hat{y}_b
$$

What's the variance of $\bar{y}$?

**Case 1: predictors are independent (uncorrelated).**

$$
\text{Var}(\bar{y}) = \frac{1}{B^2} \sum_b \text{Var}(\hat{y}_b) = \frac{1}{B^2} \cdot B \sigma^2 = \frac{\sigma^2}{B}
$$

Variance shrinks by a factor of $B$. With 100 independent predictors, variance is 1/100 of a single predictor's.

**Case 2: predictors are correlated, with pairwise correlation $\rho$.**

$$
\text{Var}(\bar{y}) = \frac{1}{B^2} \left[ B \sigma^2 + B(B-1) \rho \sigma^2 \right] = \rho \sigma^2 + \frac{(1 - \rho) \sigma^2}{B}
$$

Two-term decomposition. As $B \to \infty$, the second term vanishes — but the first term, $\rho \sigma^2$, *doesn't*. The correlation between predictors sets a floor on how much variance averaging can reduce.

**Implication.** To make averaging effective, we need many predictors AND we need them to be uncorrelated. Both. Lots of correlated predictors don't help much; few uncorrelated predictors do.

This is the entire intellectual content of the Random Forest. Everything else is engineering to produce many trees that are individually fine but mutually as uncorrelated as possible.

---

## 34.3 Bagging — the first variance-reduction trick

**Bagging** stands for **B**ootstrap **Agg**regat**ing**. The recipe:

1. From the training set of size $n$, draw $B$ **bootstrap samples** — each of size $n$, sampled *with replacement*. Each bootstrap sample has the same size as the original but contains some duplicates and is missing some rows.
2. Train a separate predictor on each bootstrap sample. Get $\hat{f}_1, \ldots, \hat{f}_B$.
3. For prediction, average (regression) or vote (classification).

For regression: $\bar{f}(x) = \frac{1}{B} \sum_b \hat{f}_b(x)$.

For classification: $\bar{f}(x) = \text{majority vote of } \hat{f}_1(x), \ldots, \hat{f}_B(x)$. Or, more commonly, average the predicted *probabilities* and then threshold — this gives smoother, better-calibrated outputs.

### 34.3.1 Why bootstrap sampling?

The bootstrap is a clever trick from Efron (1979). It produces $B$ training sets that *look like* independent samples from the underlying data-generating distribution, even though they're all derived from one finite training set. Each bootstrap sample contains roughly $1 - 1/e \approx 63\%$ of the unique rows from the original (the rest are duplicates). The math:

For one row, the probability it is NOT picked on any given draw is $(n-1)/n = 1 - 1/n$. After $n$ draws (with replacement), the probability it's still not picked is $(1 - 1/n)^n \to 1/e \approx 0.368$ as $n \to \infty$. So about $36.8\%$ of rows are absent from any given bootstrap sample, and the rest ($\sim 63\%$ of unique rows) appear at least once.

This 37% "left out" fact is what powers out-of-bag estimation (§34.5).

### 34.3.2 Why bagging *should* work

If our predictors were trained on truly independent samples from the data distribution, variance would shrink by $1/B$. Bootstrap samples are *not* independent (they all draw from the same finite training set), so the variance reduction is less than $1/B$. But it's still substantial — empirically, for decision trees, bagging cuts test error meaningfully.

### 34.3.3 The catch — trees are too correlated

Bagging works on any base learner, but it works *especially well* on high-variance learners like decision trees. Linear regression, for instance, is already low-variance — bagging linear regression is a waste of compute.

For trees, though, bagging has a limitation. Bootstrap samples share a lot of rows — about 63% in common between any two. The trees trained on them tend to *agree on the most important splits* — typically the same root split, often the same first few splits. This correlation means $\rho$ in §34.2 is high — maybe 0.4-0.6 — and the variance reduction is bounded by $\rho \sigma^2$.

We need to decorrelate the trees more.

---

## 34.4 The second trick: random feature subsampling

Breiman's second insight (1999, in the Random Forest paper proper): at every split, only let the tree consider a *random subset* of features, not all of them.

The recipe modification: when training each tree, at each node, draw a random subset of $m$ features (out of $d$ total), and find the best split among only those $m$. The other $d - m$ features are ignored for that node. The random subset is drawn afresh at every node, so the same tree might use different subsets at different splits.

Why this helps: it forces different trees to look at the problem from different angles. The strongest predictor (say, "credit score" for loan default) was being picked at the root of every bagged tree, making them correlated. With random subsampling, the strongest predictor is only available in $m/d$ of the splits — about $m/d$ of trees will pick it at the root, but the rest are forced to use the next-best predictors, exploring different subtrees.

The result: lower $\rho$, more variance reduction from averaging.

### 34.4.1 Choice of $m$

The standard defaults:

- **Classification**: $m = \lfloor \sqrt{d} \rfloor$. For $d = 100$ features, $m = 10$.
- **Regression**: $m = \lfloor d/3 \rfloor$. For $d = 100$, $m = 33$.

These defaults trace back to Breiman's experiments. The intuition: classification trees benefit from more aggressive decorrelation ($m$ small) because they're more prone to lock onto the strongest predictor. Regression trees need a bit more access to features per split.

In practice, $m$ is a hyperparameter to cross-validate (`max_features` in sklearn, `featureSubsetStrategy` in Spark MLlib). Reasonable values to try: $\sqrt{d}$, $\log_2 d$, $d/3$, $d/2$. Going lower than $\sqrt{d}$ usually hurts; going higher gives less decorrelation.

### 34.4.2 Putting bagging + feature subsampling together

That's the Random Forest algorithm:

```
For b = 1 to B:
    Draw bootstrap sample D_b of size n from training set
    Build a decision tree on D_b, but at every node only consider
        a random subset of m features for the best split.
    No pruning — let each tree grow deep.
Return the ensemble {tree_1, ..., tree_B}

Predict on new x:
    For classification: majority vote (or mean probability + threshold).
    For regression: mean prediction.
```

The "no pruning" choice is deliberate. Individual trees overfit (high variance), but the ensemble averages this out. A pruned tree has lower variance but higher bias; pruning is wasted effort if you're averaging.

---

## 34.5 Out-of-bag (OOB) error — almost-free cross-validation

This is one of the most elegant tricks in classical ML.

Recall from §34.3.1: each bootstrap sample omits about 37% of the original rows. These "out-of-bag" rows are training examples that the corresponding tree never saw.

For any row $i$ in the training set, let $B_i$ be the set of trees that did NOT include $i$ in their bootstrap sample (a random ~37% of the $B$ trees). We can compute an **out-of-bag prediction** for row $i$ using only those trees:

$$
\hat{y}_i^{\text{OOB}} = \frac{1}{|B_i|} \sum_{b \in B_i} \hat{f}_b(x_i)
$$

(For classification, take majority vote among $B_i$.)

Aggregating across all training rows gives the **OOB error** — an honest estimate of the forest's generalization error, computed *without holding out any data and without cross-validation*. Each row was held out from some trees and predicted by them; the prediction is honest in the same sense a CV prediction is.

The catch: each row is predicted by only ~37% of the trees, so the OOB error slightly overestimates the true error (the full forest of $B$ trees would do marginally better than a 0.37B sub-forest). The bias is small for large $B$.

OOB error is computed *during training*, at almost no extra cost (you already know which rows were in each bootstrap sample). For large datasets where 10-fold CV would be expensive, this is a major advantage of random forests. sklearn's `RandomForestClassifier(oob_score=True)` enables it; the estimate is in `clf.oob_score_`.

### 34.5.1 Worked example of OOB

Tiny example: $n = 5$ training rows, $B = 10$ trees. Each bootstrap sample is size 5, drawn with replacement. Suppose:

- Tree 1's bootstrap sample: rows {1, 2, 2, 3, 5} → trees NOT including row 4
- Tree 2's: {1, 1, 3, 4, 5} → not including row 2
- Tree 3's: {2, 3, 3, 4, 5} → not including row 1
- ... etc.

After all 10 trees are trained, for row 4, find the trees whose bootstrap excluded row 4 (say trees 1, 5, 7 — for instance). Predict row 4 using only those trees and average. Now you have an honest prediction for row 4 that uses ~3 trees. Do the same for every row. Compute the resulting error.

For a real forest with $B = 200$ and $n = 100{,}000$, each row gets predicted by ~74 trees on average ($200 \cdot 0.37 = 74$). That's plenty of trees to average for a stable prediction.

---

## 34.6 Hyperparameters

Random forests have few hyperparameters and they're forgiving — getting one slightly wrong rarely catastrophic.

**`n_estimators` (B)**: number of trees. More is always better (less variance), with diminishing returns. 100 is a reasonable default; 500 is fine; 1000 rarely helps significantly more than 500. The marginal cost is linear — 1000 trees take 10× the compute of 100 trees. Common practice: start at 100, increase if you have budget.

**`max_features` (m)**: number of features per split. The decorrelation knob. Defaults $\sqrt{d}$ (classification) and $d/3$ (regression). Worth tuning.

**`max_depth`**: per-tree depth limit. By default, trees are grown to full depth (no limit). For very large datasets where memory is a concern, you might cap. For small datasets, capping can help slightly. Less impactful than for single trees because averaging absorbs overfitting.

**`min_samples_leaf`** / **`min_samples_split`**: per-tree leaf/split constraints. Defaults of 1/2 (sklearn) are fine for most cases. Increasing these regularizes individual trees, which can help with very noisy data.

**`bootstrap`**: whether to use bootstrap sampling. Default True. Setting False uses the full training set for every tree, sacrificing OOB error but reducing variance differently. Rarely beneficial.

**`max_samples`**: if you don't want each bootstrap sample to be size $n$, set this to a fraction. Useful for very large datasets where size-$n$ bootstrap is expensive.

Compared to gradient boosting (~10 important hyperparameters), random forest is much more forgiving. This is part of why it's a *great default* for unfamiliar tabular problems.

---

## 34.7 Feature importance

A trained random forest gives you, for free, a measure of how important each feature is.

### 34.7.1 Mean Decrease in Impurity (MDI)

For each feature, sum the impurity reduction (information gain for classification, variance reduction for regression) achieved by every split on that feature, across all trees. Weight by the fraction of training samples passing through that node. Sum across trees. Normalize so all importances add to 1.

This is what `clf.feature_importances_` gives you in sklearn. It's fast (computed during training, no extra work) and intuitive.

**The bias.** MDI is biased toward *high-cardinality* features and *continuous* features (Chapter 33.14). A categorical with many levels offers more candidate splits, gets picked more often, accumulates more "importance." This can be misleading — a feature with many levels and lots of noise can look more important than a feature with few levels and clean signal.

The Strobl et al. (2007) paper is the canonical reference for this bias. It is not a minor effect — in problems with mixed-cardinality categoricals, MDI can rank a useless high-cardinality feature above a useful low-cardinality one.

### 34.7.2 Permutation importance

The much better alternative, also model-agnostic (works for any model, not just random forests):

1. Compute baseline performance on the validation set (or OOB set for a random forest).
2. For each feature $j$:
   a. Shuffle the values of feature $j$ across rows (breaking its relationship with $y$).
   b. Re-evaluate performance on the shuffled validation set.
   c. Importance of feature $j$ = baseline performance − shuffled performance.
3. Optional: repeat the shuffle several times and average.

If shuffling a feature destroys performance, the feature was important. If shuffling doesn't change performance, the feature was irrelevant.

**Pros:** unbiased w.r.t. cardinality. Works on any model. Honest because it measures the *effect on actual predictions*.

**Cons:** Computationally more expensive (one forward pass per feature). When features are highly correlated, shuffling one doesn't break the signal (the correlated feature still carries it), so permutation importance can underestimate. Conditional / grouped permutation methods address this.

We covered the general permutation-importance machinery in Chapter 29 (feature selection). It's worth using for any model where you care about feature attribution.

sklearn provides `sklearn.inspection.permutation_importance`. Use it.

---

## 34.8 Why random forests rarely overfit (in practice)

This is the headline practical claim, and it deserves scrutiny.

**The intuition.** Individual trees overfit (high variance, low bias). Averaging $B$ noisy trees reduces variance toward $\rho \sigma^2 / B$. As long as $\rho < 1$, the average is less overfit than any single tree.

**More precisely.** Adding more trees never *hurts* validation performance — it monotonically reduces variance and converges. There is no analog of the "early stopping" needed in gradient boosting. You can set $B = 10{,}000$ if you have the compute; you won't overfit.

**The actual overfitting risk.** RF *can* overfit when:
1. Trees are grown unconstrained AND data is small AND noisy. With $n = 100$ rows and full-depth trees, each tree memorizes its bootstrap sample; averaging helps but doesn't fully cancel out memorized patterns.
2. The features include leaky information (Chapter 22). RF will happily memorize the leakage just like any other model.

The first case is detected by OOB error: if training error is near zero and OOB error is much higher, you're overfitting. Increase `min_samples_leaf` or `max_depth` constraints.

**The folk wisdom.** "Random forests are robust to overfitting" is *practically* true for moderate-to-large tabular datasets. It is not literally always true. The discipline of monitoring OOB / validation error still applies.

---

## 34.9 When random forests win and lose

### 34.9.1 RF's home turf

- **Tabular data with mixed feature types** (numeric + categorical + ordinal).
- **Moderate size** (thousands to millions of rows; $d$ up to a few thousand).
- **Non-linear relationships and interactions** that you don't want to engineer by hand.
- **You want a strong default** with few hyperparameters to tune.
- **You need feature importance** for exploratory analysis.
- **You can afford latency in inference** (RF is slower than logistic regression at prediction time).

### 34.9.2 Where RF loses

- **Very high-dimensional sparse data** (text with TF-IDF, $d = 50{,}000$, mostly zeros). RF doesn't exploit sparsity well; linear models and neural nets typically beat.
- **Images, audio, sequences.** RF treats each pixel/sample as an independent feature, losing all spatial / temporal structure. Convolutional or recurrent neural nets dominate here.
- **Smooth extrapolation needed.** RF (like single trees) can't extrapolate beyond training range. Linear models and Gaussian processes can.
- **You need calibrated probabilities.** RF outputs are voting fractions, which aren't well-calibrated. Logistic regression or Platt-scaled outputs are better.
- **Tight inference latency budget.** Walking 500 trees is slower than one dot product.
- **Need explainability of individual predictions.** A single tree is interpretable; 500 trees is not. SHAP values help but add complexity.

### 34.9.3 RF vs. gradient boosting

On most tabular benchmarks, well-tuned gradient boosting (Chapter 36) beats random forest by 1-3 points of accuracy. But:

- RF needs much less hyperparameter tuning.
- RF is harder to overfit.
- RF has free OOB error.
- RF parallelizes trivially (independent trees); GBT is sequential.

For a quick baseline, RF. For squeezing out the last few points of accuracy where it matters, GBT. For deciding what to deploy: depends on your operational constraints.

---

## 34.10 Code

### 34.10.1 scikit-learn

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance

rf = RandomForestClassifier(
    n_estimators=200,
    max_features="sqrt",      # = sqrt(d), classification default
    max_depth=None,           # full-depth trees
    min_samples_leaf=1,
    bootstrap=True,
    oob_score=True,           # compute OOB error
    n_jobs=-1,                # parallel
    random_state=0,
)
rf.fit(X_train, y_train)

print(f"Train accuracy:  {rf.score(X_train, y_train):.3f}")
print(f"OOB accuracy:    {rf.oob_score_:.3f}")
print(f"Test accuracy:   {rf.score(X_test, y_test):.3f}")

# MDI importance (biased but free)
for name, imp in zip(feature_names, rf.feature_importances_):
    print(f"{name}: {imp:.4f}")

# Permutation importance (better)
perm = permutation_importance(rf, X_test, y_test, n_repeats=10, random_state=0)
for name, imp_mean, imp_std in zip(feature_names, perm.importances_mean, perm.importances_std):
    print(f"{name}: {imp_mean:.4f} ± {imp_std:.4f}")
```

The `oob_score=True` enables the free generalization estimate. `n_jobs=-1` parallelizes across all CPU cores — random forests are embarrassingly parallel because the trees are independent.

For regression, use `RandomForestRegressor` with `max_features="auto"` (which is $d/3$ for regression — note: in newer sklearn versions, you may need to set this explicitly).

### 34.10.2 PySpark MLlib preview

```python
from pyspark.ml.classification import RandomForestClassifier as SparkRF

rf = SparkRF(
    featuresCol="features", labelCol="label",
    numTrees=200,
    maxDepth=20,
    featureSubsetStrategy="sqrt",  # or "auto", "log2", "onethird", "n", "(0.0-1.0]"
    subsamplingRate=1.0,            # the bootstrap fraction
    impurity="gini",
    maxBins=32,
)
model = rf.fit(train_df)
predictions = model.transform(test_df)
```

Spark MLlib's RF does NOT compute OOB error (the bootstrap+OOB bookkeeping doesn't fit Spark's lazy execution model cleanly). For Spark, use CrossValidator (Chapter 65) or a held-out validation set.

`featureSubsetStrategy`: `"sqrt"` for classification default, `"onethird"` for regression default. `"auto"` picks the right default based on whether it's classification or regression.

---

## 34.11 What this builds on / where this returns

**Builds on:**
- Chapter 19 — bias-variance decomposition. The variance-reduction story is the *core* of why RF works.
- Chapter 22 — cross-validation. OOB is RF's substitute for CV.
- Chapter 29 — permutation importance.
- Chapter 33 — decision trees as the base learner.

**Returns:**
- Chapter 35-36 — boosting as a different way to combine trees (sequential, not parallel).
- Chapter 65 — Spark MLlib RandomForestClassifier in depth.

---

## 34.12 Exercises

1. **Variance reduction calc.** You have 100 predictors, each with variance 1, pairwise correlation 0.3. What's the variance of their average? What if correlation were 0? What if correlation were 0.9?

2. **Bootstrap-sample math.** With $n = 1000$ training rows and a bootstrap sample of size 1000, what's the expected number of unique rows in the sample? What's the expected number of rows that are completely absent from the bootstrap sample?

3. **Why feature subsampling decorrelates.** Suppose one feature is much more predictive than all others. Without feature subsampling, every bagged tree picks it at the root. What happens to $\rho$? With feature subsampling, what fraction of trees can NOT pick that feature at the root?

4. **OOB intuition.** You train an RF with $B = 500$ trees. For a particular training row $i$, about how many trees did *not* include row $i$ in their bootstrap sample? Hence, how many trees vote on the OOB prediction for row $i$?

5. **When does the OOB estimate fail?** Name two situations where OOB error would mislead you about test performance.

6. **MDI bias intuition.** Why is MDI biased toward high-cardinality features? Give a concrete example.

7. **Permutation importance for one feature.** Baseline accuracy is 0.92. After shuffling feature `age`, accuracy drops to 0.86. After shuffling `customer_id` (which should be irrelevant), accuracy drops to 0.91. Interpret.

8. **Random forest depth.** Two RFs trained on the same data: one with `max_depth=10`, one with `max_depth=None`. Which is more likely to overfit? Which would you expect to have lower bias?

9. **Feature subsampling for regression.** Why is $m = d/3$ the default for regression but $m = \sqrt{d}$ for classification? (Speculative — there's no proof, but offer an intuition.)

10. **Parallelism comparison.** You have 8 CPU cores and want to train a random forest with 200 trees in the least wall-clock time. How does training time scale with cores? Why doesn't gradient boosting parallelize the same way?

11. **OOB vs. validation set.** You have a moderate dataset (n=20,000). Should you use a held-out validation set or rely on OOB? Discuss tradeoffs.

12. **Calibration check.** A random forest predicts probability 0.8 for some examples. Among those, only 65% are actually positive. Is the RF well-calibrated? What can you do?

<details>
<summary>Answers</summary>

1. $\text{Var}(\bar{y}) = \rho \sigma^2 + (1-\rho)\sigma^2/B = 0.3 + 0.7/100 = 0.307$. With $\rho = 0$: $0.01$. With $\rho = 0.9$: $0.9 + 0.1/100 = 0.901$. The correlation matters enormously.

2. Expected unique = $n(1 - (1-1/n)^n) \approx n(1 - 1/e) \approx 1000 \cdot 0.632 = 632$. Expected absent = $n(1-1/n)^n \approx n/e \approx 368$.

3. $\rho$ stays high because all trees agree on the dominant root split, making them very similar. With feature subsampling at rate $m/d$, the fraction of trees that *can* use the dominant feature at the root is $m/d$. So about $1 - m/d$ of trees must root on something else, increasing tree diversity.

4. $500 \cdot (1 - 1/e) = $ wait, that's the included count. Excluded ≈ $500 / e \approx 184$. So about 184 trees did *not* see row $i$; they vote on its OOB prediction.

5. (a) Leakage in features — OOB shares the leakage as much as a CV fold would, so it would underestimate true test error in the leakage-fixed world. (b) Distribution shift between training and deployment — OOB measures generalization to the *training distribution*, not future / deployment distribution.

6. A high-cardinality feature offers many candidate split thresholds. Even if pure noise, *some* threshold will happen to split well by chance, accumulating impurity reduction across trees. Example: customer_id (random) has $n$ unique values and will get split on often despite being meaningless.

7. `age` matters (5-point drop = real importance). `customer_id` doesn't matter much (1-point drop within noise — exactly what you'd expect from an irrelevant feature). This is the correct, unbiased ranking — MDI might have flagged customer_id as important purely due to cardinality.

8. `max_depth=None` (full-depth) has lower bias because each tree fits its bootstrap sample exactly. It's also more variance — but averaging absorbs that. `max_depth=10` has higher bias (stops splitting early) but each tree has lower variance. With many trees, the unconstrained version typically wins.

9. Speculative: classification splits often have a dominant feature (one with strong class separation), so aggressive decorrelation ($\sqrt{d}$, small $m$) helps a lot. Regression often has multiple predictors with moderate signal, so $d/3$ keeps more features in play per split, getting better individual trees without sacrificing much decorrelation.

10. RF training time scales nearly linearly with cores (each tree is independent). 200 trees on 8 cores ≈ 25 sequential trees of work. GBT is sequential because each tree depends on the residuals from previous trees — you can parallelize within a single tree's split-finding but not across trees in the boosting sequence.

11. OOB is essentially free, so the question is whether OOB is accurate enough. For RF, OOB is well-known to be a good estimator. Use OOB for the bulk of model selection (max_features, min_samples_leaf), and reserve a held-out test set for the final unbiased estimate. CV is wasteful on top of OOB for an RF.

12. Not well-calibrated — at predicted 0.8, you'd expect ~80% positives but observed 65%. The RF is overconfident. Fix: post-hoc calibration with Platt scaling (logistic regression on the RF's outputs) or isotonic regression. `CalibratedClassifierCV` in sklearn wraps this.

</details>
