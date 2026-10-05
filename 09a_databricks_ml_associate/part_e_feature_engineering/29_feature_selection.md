# Chapter 29 — Feature Selection

> **Goal of this chapter:** to teach you when and how to remove features, not just add them. The instinct of beginners is to add features — more data is always better, right? Past a certain point, no: irrelevant features hurt generalisation, slow training, distort interpretations, and make production pipelines fragile. Feature selection is the discipline of identifying and removing features that the model doesn't actually need. By the end of this chapter you'll know the three families of selection methods (filter, wrapper, embedded), when each is appropriate, and the leakage pitfall that ruins many feature-selection workflows.

---

## 29.1 Why we drop features

You might think: "if a feature is irrelevant, won't the model just learn a near-zero coefficient for it?" Mostly yes, but not without cost.

**Cost 1: Variance inflation.** Every additional feature is an additional dimension along which the model can fit noise. With $d$ features and $n$ rows, the variance of the fitted model grows roughly linearly in $d$ (this is one of the strongest arguments behind Chapter 19's bias-variance picture). Adding noise features pushes the model toward overfitting. The classic "curse of dimensionality" is, in one form, exactly this.

**Cost 2: Compute.** Training scales with feature count. With a thousand redundant features, you've slowed training tenfold for no benefit. At inference, every feature requires a lookup or computation. In high-throughput serving systems, this matters.

**Cost 3: Interpretation.** A model with 5 features whose coefficients you can stare at and reason about is very different from a model with 500 features whose individual coefficients are noise-level. The former gives you a story to tell about why the model is making its decisions; the latter is a black box even when the algorithm is linear.

**Cost 4: Maintenance and fragility.** Every feature is a dependency: an upstream data source, a transformation, a feature-store contract. A feature that adds no value to the model is pure cost — it has to be computed and joined and shipped to serving, with no payoff. When that data source breaks, your model breaks for no reason.

**Cost 5: Leakage.** Adding many features, including obscure ones, increases the chance one of them silently leaks the target. Feature selection's *first* benefit, before anything statistical, is often catching the leakage features (revisit Chapter 23 §23.9 — single-feature AUC scanning is a primitive form of feature selection).

So the goal is to keep the features that matter, drop the ones that don't, and have a principled procedure for deciding which is which. This chapter is that procedure.

---

## 29.2 The three families

Feature selection methods divide into three families:

1. **Filter methods** rank features by a statistic computed independently of the model, and keep the top $k$. Fast, but blind to feature interactions.
2. **Wrapper methods** train the model with different subsets of features and pick the subset that performs best. Honest, but expensive.
3. **Embedded methods** use the model itself to do selection — e.g., L1 regularization zeroes out coefficients, tree models compute importance during training. Fast and considers interactions; usually the right default.

We'll go through each.

---

## 29.3 Filter methods

A filter method scores each feature against the target *without* fitting the model. Examples:

### 29.3.1 Correlation (for numeric features in regression)

For each numeric feature $x_j$ and a continuous target $y$, compute Pearson correlation $r_j = \text{cor}(x_j, y)$. Keep features with $|r_j|$ above a threshold or in the top $k$.

```python
correlations = df.corr()['target'].drop('target').sort_values(key=abs, ascending=False)
top_features = correlations.head(20).index.tolist()
```

**Limitations.**

- *Linear only.* Pearson misses non-linear relationships. A U-shaped feature has near-zero correlation but might be very predictive.
- *Univariate.* Two features that are individually weak but jointly strong are missed.
- *No interactions.* If $x_1$ and $x_2$ together produce a strong signal but neither alone does, correlation misses it.

A modest improvement: **Spearman correlation** captures monotonic non-linear relationships (ranks the data first). Still univariate; still misses interactions.

### 29.3.2 Mutual information

A more general measure of dependence:

$$I(X; Y) = \sum_{x, y} P(x, y) \log \frac{P(x, y)}{P(x) P(y)}$$

Captures any kind of statistical dependence, including non-linear and non-monotonic. Zero means independent; positive means dependent.

In scikit-learn:

```python
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression

scores = mutual_info_classif(X, y)  # for classification
scores = mutual_info_regression(X, y)  # for regression
```

Strictly better than Pearson for detecting *some* dependence, but still univariate.

### 29.3.3 Chi-squared (for categorical features in classification)

For a categorical feature and a categorical target, the chi-squared statistic measures how strongly they're associated. Build a contingency table (rows = feature values, columns = target classes), compare to the table you'd expect under independence.

In scikit-learn: `chi2(X, y)`. Requires non-negative inputs.

Same limitations: univariate, ignores interactions.

### 29.3.4 ANOVA F-test (numeric feature, categorical target)

`f_classif` computes the F-statistic for the hypothesis that the feature's mean differs across target classes. Higher F → bigger between-class difference relative to within-class variance → more predictive feature.

### 29.3.5 SelectKBest in scikit-learn

`SelectKBest(score_func, k=N)` is the universal filter wrapper:

```python
from sklearn.feature_selection import SelectKBest, mutual_info_classif

selector = SelectKBest(mutual_info_classif, k=20)
X_new = selector.fit_transform(X, y)
```

**When to use filter methods.**

- Initial pruning of a very large feature set (thousands+) before more expensive methods.
- When you need speed and have no time for wrapper or embedded methods.
- As a sanity check ("if Pearson correlation says this feature is useless, am I sure I want to keep it?").

**When not to.**

- When interactions matter (almost always). A filter method considers each feature in isolation; it can't tell that feature A is useless alone but powerful in combination with feature B.

---

## 29.4 Wrapper methods

A wrapper method evaluates feature subsets by *actually fitting the model* on each candidate subset.

### 29.4.1 Forward selection

Start with no features. At each step, find the feature that, when added, improves model performance the most. Add it. Repeat until performance stops improving (or you've added enough).

```
features_selected = []
while improvement is possible:
    best_new_feature = argmax over candidate features:
        train model on features_selected + [candidate]
        evaluate via cross-validation
    if score with best_new_feature > current score:
        features_selected.append(best_new_feature)
    else:
        break
```

**Pros:**
- Honest — each addition is evaluated on actual model performance.
- Captures the "feature B is useful only after we've added feature A" effect.

**Cons:**
- Slow. With $d$ features and final subset size $k$, the cost is $O(d \cdot k)$ model fits.
- Greedy. A locally-optimal choice early may not lead to a globally-optimal subset.

### 29.4.2 Backward elimination

Start with all features. At each step, remove the feature whose removal causes the smallest performance drop (or improves performance). Repeat until removing any further feature hurts.

```
features_selected = all_features
while removing helps:
    worst_feature = argmin over features_selected:
        train model on features_selected \ {feature}
        evaluate via cross-validation
    if score without worst_feature >= current score - tolerance:
        features_selected.remove(worst_feature)
    else:
        break
```

Same time complexity as forward selection but symmetric.

### 29.4.3 Recursive Feature Elimination (RFE)

A practical hybrid that scikit-learn implements. Start with all features. Train the model. Rank features by importance (using model-specific importance — coefficients for linear models, feature importances for trees). Remove the least important feature. Repeat.

```python
from sklearn.feature_selection import RFE
from sklearn.linear_model import LogisticRegression

selector = RFE(LogisticRegression(), n_features_to_select=10, step=1)
selector.fit(X, y)
X_new = selector.transform(X)
print(selector.ranking_)
```

RFE with cross-validation: `RFECV` automatically determines the optimal number of features.

**Pros and cons.**

- Faster than full backward elimination (uses importances rather than refitting from scratch each removal).
- Still expensive — $d$ model fits.
- Sensitive to the model's importance measure; the "importance" depends on the model.

### 29.4.4 When wrapper methods make sense

- Moderate feature count (10s to low 100s) — wrapper methods don't scale to thousands.
- You're committed to a particular model family and want the best subset for that model specifically.
- Compute budget allows for $O(d)$ to $O(d^2)$ model fits.

For larger problems, fall back to embedded methods.

---

## 29.5 Embedded methods

Embedded methods do feature selection *as part of model training*. The selection is intrinsic to the model.

### 29.5.1 L1 regularization (Lasso)

Recall from Chapter 20: L1 regularization adds a penalty proportional to the sum of absolute values of the coefficients.

$$L_{\text{Lasso}}(w) = \sum_i (y_i - w^T x_i)^2 + \lambda \sum_j |w_j|$$

The geometry of L1 (the diamond-shaped ball in coefficient space) causes many coefficients to be exactly zero at the optimum. Lasso performs implicit feature selection: features with $w_j = 0$ are effectively dropped from the model.

**Tuning.** $\lambda$ controls how aggressive the selection is. Large $\lambda$ → most coefficients are zero, very few features survive. Small $\lambda$ → most features kept. You tune $\lambda$ via cross-validation.

In scikit-learn:

```python
from sklearn.linear_model import LassoCV, LogisticRegressionCV

# Regression
lasso = LassoCV(cv=5)
lasso.fit(X, y)
selected = np.where(lasso.coef_ != 0)[0]

# Classification (logistic regression with L1)
logreg = LogisticRegressionCV(penalty='l1', solver='saga', cv=5)
logreg.fit(X, y)
```

**Pros.**

- Fast — selection happens during a single model fit.
- Considers interactions among the features it sees (in a linear sense).
- Built into many ML libraries.

**Cons.**

- Linear (or generalised linear). Doesn't capture non-linear feature interactions.
- Among correlated features, picks one arbitrarily and zeroes the others — which may not be the most interpretable choice. **ElasticNet** (L1 + L2) often produces more stable selection on correlated features.

### 29.5.2 Tree-based feature importance

Random forests and gradient-boosted trees compute, for each feature, how much it contributed to reducing impurity (Gini, entropy, or MSE) across the ensemble.

```python
from sklearn.ensemble import RandomForestRegressor

rf = RandomForestRegressor().fit(X, y)
importances = rf.feature_importances_
top_features = X.columns[importances.argsort()[::-1][:10]]
```

**Two flavors.**

- **MDI (Mean Decrease in Impurity).** The default `feature_importances_`. Sum of impurity reduction across all splits in all trees, weighted by the number of samples at each split. Biased toward high-cardinality features (more potential split points → more chances to reduce impurity).
- **Permutation importance.** A model-agnostic measure. Train the model. For each feature, randomly shuffle its values in the validation set, re-evaluate. The drop in performance is the feature's importance.

Permutation importance is generally more honest than MDI:

```python
from sklearn.inspection import permutation_importance

result = permutation_importance(rf, X_val, y_val, n_repeats=10)
importances = result.importances_mean
```

**Why permutation is better than MDI.**

1. *No high-cardinality bias.* MDI rewards features with many potential split points, even if those splits are spurious. Permutation evaluates against held-out performance.
2. *Model-agnostic.* Permutation importance applies to *any* model (linear, neural, tree, ensemble). MDI is tree-specific.
3. *Includes interactions and downstream effects.* When you shuffle feature $j$, you destroy not just its direct contribution but also its contribution to features that interact with it.

### 29.5.3 Combining selection with cross-validation

The single most common bug in feature selection: doing the selection on the *full dataset* and then doing cross-validation on the selected features. This is leakage.

**Wrong:**

```python
# WRONG — feature selection used the test fold's labels
selector = SelectKBest(k=20).fit(X, y)
X_selected = selector.transform(X)
scores = cross_val_score(model, X_selected, y, cv=5)
```

The `SelectKBest` was fit on the *whole dataset* including the rows that would later be in test folds. The selection therefore "saw" the test labels and chose features based on partial knowledge of them. The cross-validation score is inflated.

**Right:**

```python
from sklearn.pipeline import Pipeline

pipe = Pipeline([
    ('select', SelectKBest(mutual_info_classif, k=20)),
    ('model', LogisticRegression())
])
scores = cross_val_score(pipe, X, y, cv=5)
```

The `Pipeline` ensures that the feature selector is re-fit on each fold's training data, never seeing the fold's test labels. The cross-validation score is now an honest estimate.

This is the same discipline as Chapter 24's imputer and Chapter 25's target encoder. Any preprocessing step that learns from the target *must* be inside a pipeline so cross-validation handles it correctly. Feature selection is preprocessing, even when it doesn't feel like it.

---

## 29.6 A worked example

Consider a 20-feature toy dataset with 5 informative features and 15 noise features.

```python
import numpy as np
from sklearn.datasets import make_classification

X, y = make_classification(
    n_samples=1000, n_features=20, n_informative=5, n_redundant=0,
    n_clusters_per_class=2, random_state=0
)
```

The first 5 features carry signal; the other 15 are noise.

**Method 1: Correlation filter (Pearson).**

```python
correlations = np.array([np.corrcoef(X[:, j], y)[0, 1] for j in range(20)])
ranking = np.argsort(-np.abs(correlations))
# Output: typical ranking puts most of features 0-4 in top, but with noise mixed in.
# Example: [3, 1, 18, 0, 4, 12, 2, ...]
```

The informative features tend to bubble up but with some noise features sneaking in. Univariate methods don't see that features 1 and 4 are jointly informative even though each alone is moderately so.

**Method 2: RFE with logistic regression.**

```python
from sklearn.feature_selection import RFE
from sklearn.linear_model import LogisticRegression

rfe = RFE(LogisticRegression(), n_features_to_select=5)
rfe.fit(X, y)
ranking = rfe.ranking_
# Selected features: usually 4 out of 5 informative ones, sometimes 5.
```

Better than the filter — the model-based ranking accounts for joint signal.

**Method 3: Lasso.**

```python
from sklearn.linear_model import LassoCV

lasso = LassoCV(cv=5).fit(X, y)
selected = np.where(np.abs(lasso.coef_) > 0)[0]
# Typically: 5-8 features survive, mostly the informative ones plus a few noise.
```

Lasso typically keeps most informative features and a small number of noise features. The number kept depends on $\lambda$, chosen via CV.

**Method 4: Permutation importance from a random forest.**

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance

rf = RandomForestClassifier(n_estimators=200).fit(X, y)
result = permutation_importance(rf, X, y, n_repeats=10)
importances = result.importances_mean
# Top 5 features by importance: usually exactly the 5 informative ones.
```

Permutation importance with a random forest is often the cleanest method on this kind of synthetic problem.

**Verdict.** No method is uniformly best. Filter methods are fastest. Wrapper methods (RFE) are honest but slow. Lasso and tree-based methods are good defaults. On real problems, you'd compare several and choose by validation-set performance, not by which one you trust the most.

---

## 29.7 The leakage trap (revisited)

The single biggest mistake in feature selection workflows: doing the selection on the *full dataset* and then cross-validating on the selected subset.

Reasoning: if I select 5 features by looking at their correlation with $y$ on the whole dataset, then I'm using *all* of $y$ to decide which 5 to keep. When I subsequently cross-validate, each "test" fold is using features that were selected partly because of those same fold's targets. The selection has leaked.

The fix is *always* the same: put the selector inside a pipeline that respects fold structure. In scikit-learn, this is `Pipeline`. In Spark ML, it's also `Pipeline` (Chapter 62).

Equivalent for time-series cross-validation: the selector must be re-fit using only training data from before each fold's test period. The same logic applies.

This is one of those bugs that almost everyone makes once and then never again. Make it once, here, on a low-stakes notebook. Not on a production model.

---

## 29.8 Domain knowledge: the most underrated tool

A method I haven't discussed but which is consistently the most effective: **ask someone who understands the data which features should matter.**

The data owner, the domain expert, the business stakeholder — these people often know things that no statistical method will recover from the data alone. They know that the `branch_id` feature has been redefined recently and shouldn't be trusted before April. They know that `account_age` is the right proxy for tenure, not `customer_id_age`. They know that `loan_purpose = "small_business"` is risky for entirely non-statistical reasons (regulatory definition of "small business").

This isn't a substitute for the methods in this chapter — you should still validate domain claims with data — but it's the cheapest source of high-quality feature selection knowledge available to you. Use it.

---

## 29.9 The order in which to apply methods

A practical recipe:

1. **Remove obviously useless columns by hand.** IDs (`loan_id`, `customer_id`). Columns with no variance (a single unique value). Columns that are 99% null. These are uncontroversial.

2. **Run the leakage scan from Chapter 23 §23.9.** Single-feature AUC. Drop the features that are too good to be true (after verifying with the data owner).

3. **Talk to the data owner.** Understand the meaning of every column. Drop columns that are flagged as unreliable, deprecated, or post-decision.

4. **Use a filter method (correlation, mutual info) to rank.** This is a sanity check, not a selection — keep the top 50% as candidates, but don't commit.

5. **Train a tree-based model (random forest) and compute permutation importance.** This is your best estimate of which features really matter. Keep the top $k$ where $k$ is justified by your data size.

6. **Optionally, run RFE or Lasso to do a final selection** within the surviving candidates.

7. **Always validate the final feature set with cross-validation**, using a pipeline that includes any imputation/encoding/selection so leakage is impossible.

At any step, if you find a feature unexpectedly important, *interrogate it*. Is it leaking? Is the selection method being fooled by high cardinality? Is the data owner aware?

---

## 29.10 The "no feature selection" case

A counterpoint: in some settings, feature selection is unnecessary or counterproductive.

**When the model handles it natively.** L1-regularized linear models, regularised tree ensembles, and gradient-boosted trees all have built-in mechanisms for ignoring useless features. If you're using XGBoost with appropriate regularization, manually pre-selecting features may not help — the model is already doing it.

**When you have abundant data.** With millions of training rows, the variance-inflation cost of an extra feature is small. The model has enough data to estimate the near-zero coefficient cleanly. You can afford redundancy.

**When the feature is cheap.** A feature that's already in your training table and cheap to compute is not worth the engineering effort of removing.

**When interpretability isn't a constraint.** Some applications don't care about explaining individual predictions (recommendation systems, ad ranking, optimisation problems). Then a 500-feature model with marginally better performance is fine.

In contrast, feature selection is *very* valuable when:

- The number of features is comparable to or larger than the number of rows ("$p \geq n$" regime).
- The model is linear or otherwise sensitive to extraneous features.
- Interpretation matters (medical, financial, regulated domains).
- Inference latency is constrained.
- Production maintenance is expensive (each feature is a data-pipeline dependency).

---

## 29.11 What this builds on / where it returns

**Builds on:**

- Chapter 19, 20: bias-variance and regularization, the theoretical underpinning for "more features can hurt."
- Chapter 22: cross-validation discipline, which feature selection must respect.
- Chapter 23 §23.9: the single-feature AUC scan, a leakage-detection precursor of filter methods.
- Chapter 33–36: tree-based feature importance, an embedded method we'll deepen.

**Returns in:**

- Chapter 30 (Feature Store preview): once you've selected features, the feature store is where they live.
- Chapter 33–36 (trees and ensembles): tree-based importance is one of the main feature-selection mechanisms in practice.
- Chapter 53–54 (HPO): hyperparameter optimisation including the regularization strength is closely connected to embedded feature selection.

---

## 29.12 Exercises

1. **Filter limitations.** Why does Pearson correlation fail to detect a U-shaped relationship between a feature and the target?

2. **The cardinality bias of MDI.** A random-forest feature importance assigns high importance to a customer ID column that, by design, is a random hash. What's going on?

3. **Permutation importance robustness.** Why is permutation importance more reliable than MDI for ranking features?

4. **The leakage bug.** Find the bug:
   ```python
   selector = SelectKBest(k=20).fit(X_train, y_train)
   X_train_sel = selector.transform(X_train)
   X_test_sel = selector.transform(X_test)
   scores = cross_val_score(model, X_train_sel, y_train, cv=5)
   ```
   Wait — is there actually a bug? Justify your answer.

5. **Lasso vs. ElasticNet on correlated features.** Two features are nearly identical. Lasso keeps one and zeros the other. ElasticNet keeps both with smaller coefficients. Which behavior is preferable, and under what circumstances?

6. **Forward selection greediness.** Construct (or sketch) an example where forward selection picks a globally-suboptimal feature subset.

7. **RFE with what model.** Why does RFE with a logistic regression give different selected features than RFE with a random forest?

8. **The "I have $p = 1000$, $n = 200$" problem.** You have 1000 features and 200 training rows. Which selection methods will you reach for, and why?

9. **Selection in cross-validation, formal argument.** Show by argument that fitting feature selection on the full dataset before CV gives an optimistic (biased) estimate of generalisation.

10. **The tree-RF "absorbs irrelevant features" claim.** A common belief is that random forests are "immune" to irrelevant features because they ignore them through splits. Is this exactly true? When does it break down?

11. **Domain knowledge override.** A statistical method ranks a feature as the most important. The data owner says it shouldn't be used because of a regulatory constraint. What do you do?

12. **Feature selection in production.** You select 20 features from 200. Six months later, one of the 20 features is no longer available in the upstream data source. What's your remediation plan?

<details>
<summary>Answers</summary>

1. Pearson correlation measures linear monotonic association. A U-shaped relationship — high at the extremes, low in the middle — has zero net Pearson correlation: the positive and negative slopes cancel. The feature is highly predictive, just not in a linear way. Use mutual information or a model-based importance to detect this.

2. MDI (mean decrease in impurity) rewards features that *could* produce splits, not just useful splits. A high-cardinality feature (like a hash with many distinct values) offers many possible split points; even if none of them generalise, the impurity calculation rewards them in the training data. The forest's MDI is biased toward high-cardinality. Use permutation importance instead, which scores on out-of-bag or held-out data and isn't fooled.

3. (a) It uses out-of-sample data (validation set) to measure the feature's contribution, not the training data the model was fit on. (b) It's model-agnostic — applicable to any model, not just trees. (c) It captures contributions from interactions, not just direct effects. (d) It's not biased toward high-cardinality features the way MDI is.

4. There's no bug *if* `X_train`/`y_train` and `X_test`/`y_test` were split *before* fitting the selector. The selector fits on training only, transforms both, and CV uses only the training data. But the CV inside that final `cross_val_score` line is technically refitting the selector inside each fold... wait, no, it isn't — `cross_val_score` only fits the `model`, not the selector. The selector was fit once, outside the CV loop, using *all* the training data. That's a leak *within the training set* — the selector saw all training labels, including the labels that would later be in CV's internal test folds. The CV score is optimistic. Fix: use a `Pipeline` with both the selector and the model so CV refits both.

5. ElasticNet's "keep both" behavior is more stable across re-fits on different data subsets — Lasso's choice of which feature to zero is arbitrary among correlated features and can flip with small data perturbations, hurting reproducibility. ElasticNet is generally preferable when correlated features have similar plausibility (no domain reason to prefer one). Lasso is preferable when one of the correlated features is genuinely the "true" one and the others are noise — but you usually can't tell.

6. Two features $x_1, x_2$ are individually useless (correlation with target $\approx 0$), but $x_1 \cdot x_2$ is highly predictive. Forward selection sees that adding either $x_1$ or $x_2$ alone doesn't help; it doesn't try them together; it stops at zero features. A globally-optimal model would include both. Forward selection's greediness misses this. Wrappers that explore subsets (genetic algorithms, simulated annealing) can sometimes recover.

7. RFE ranks features by the model's importance measure. Logistic regression's importance is the magnitude of the (regularised) coefficient — a linear measure. Random forest's importance is the mean decrease in impurity across the ensemble — a non-linear, interaction-capturing measure. The two will give different rankings on the same data, because they measure different things.

8. With $p > n$, classic linear regression is ill-posed (overdetermined). You need a regularised method. Best choices: (a) L1 (Lasso) with cross-validated $\lambda$ — does selection and fitting simultaneously. (b) A tree ensemble (random forest, XGBoost) with built-in regularization — handles the ratio gracefully. (c) Univariate filter to reduce to a manageable subset, *then* fit a model. Avoid: unregularized linear regression (catastrophic), exhaustive wrapper methods (computationally infeasible).

9. The selector is fit on the full dataset, including the test rows of every CV fold. The selection criterion (e.g., correlation with $y$) is computed using those test-fold labels. The features that survive are those that happen to correlate with $y$ across the *entire* dataset, including the parts CV will later treat as "unseen." When CV evaluates the model on those held-out folds, the model uses features that were partly selected because of those very rows' targets. The performance estimate is optimistically biased.

10. Mostly true but not exactly. A random forest's splits naturally ignore features that aren't useful — irrelevant features get split on less often and contribute less to predictions. But: (a) variance in the model estimation is still inflated by irrelevant features (Chapter 19), affecting smaller datasets. (b) Computation scales with feature count even for trees. (c) MDI feature importance can still attribute spurious importance to high-cardinality irrelevant features. (d) Hyperparameters (like `max_features`) interact with feature count. So even for random forests, feature selection is sometimes worthwhile.

11. Don't use the feature. Regulatory constraints trump statistical performance. Document the constraint, retrain without the feature, and report the impact on performance to stakeholders. If the constraint is interpretable (e.g., "we cannot use protected attributes"), often there are alternative features that capture *some* of the lost signal without the constraint violation.

12. (a) Immediate: have a backup. The feature pipeline should have been monitoring data availability and alerted. (b) Short-term: refit the model without the dropped feature. Accept the small performance loss. (c) Medium-term: investigate whether the upstream change can be reversed, whether the feature can be reconstructed from other sources, or whether a similar surrogate exists. (d) Long-term: feature dependencies should be documented and versioned (feature store — Chapter 30, 71). Without that, every feature is a silent dependency that can fail. This is exactly the kind of problem the feature store solves.

</details>
