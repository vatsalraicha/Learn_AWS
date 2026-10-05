# Chapter 33 — Decision Trees — Information Gain, Splitting, Pruning

> **Goal of this chapter:** to understand decision trees from the ground up — what they compute, why they choose the splits they do, when they overfit, and how to control them. A decision tree is, by some distance, the most *human-interpretable* ML model. "If income > $50K and age < 35 then predict default-risk = LOW" — that's a tree. Beyond their immediate interpretability, trees are the building block of the two algorithms that dominate tabular ML in 2026: random forests (Chapter 34) and gradient-boosted trees (Chapter 36). You cannot understand either without first understanding a single tree.

---

## 33.1 What a tree is

Picture a flowchart. At each non-leaf node, ask a yes/no question about one feature: "is age > 35?" Branch left for yes, right for no. Recurse until you hit a leaf, which holds a prediction.

```
                        is income > 50K?
                       /                \
                     yes                 no
                    /                      \
            is age < 35?              is debt > 10K?
            /         \                /         \
          yes         no             yes         no
         /             \             /             \
   LOW risk    MEDIUM risk     HIGH risk    LOW risk
```

That's a decision tree. Four things to notice.

**The questions are about individual features.** Each split looks at one feature and one threshold. No combinations, no transformations, just $x_j \lessgtr t$. (Almost all popular tree libraries restrict to this; you *can* build trees with multi-feature splits — "oblique" trees — but they're rare in practice.)

**The structure is hierarchical.** A split high in the tree partitions the entire dataset; splits lower down only see the rows that reached them. Different subtrees can split on different features at different thresholds — the tree adapts to local structure.

**Leaves predict values.** For classification, each leaf holds a class label (or a class probability distribution — usually the empirical frequency of training labels that fell into that leaf). For regression, each leaf holds a number (typically the mean of training labels that fell into that leaf).

**The model is a piecewise constant function.** Within a leaf, the prediction doesn't depend on $x$ at all — every example that lands in that leaf gets the same prediction. This is a striking limitation we'll come back to.

---

## 33.2 The training problem

We have $n$ training examples. We want to build a tree from them. Two questions:

1. **What's the best tree?** ("Best" by what criterion?)
2. **How do we find it?**

For question 1: the "best" tree is one that, on the training data, separates examples by class (for classification) or groups them by similar target values (for regression), *while staying small enough to generalize* (this is the bias-variance tradeoff of Chapter 19, in a new guise).

For question 2: finding the *globally optimal* tree is NP-hard. The number of possible trees with $d$ features and $n$ examples is astronomical, and the optimization landscape is wildly discontinuous (small changes to a split change which examples each subtree sees). So we don't try to find the global optimum. We use a **greedy** algorithm: at each node, pick the single best split (by some local criterion), recurse on the two children, and stop when a stopping criterion fires.

The greedy algorithm is called **CART** (Classification and Regression Trees, Breiman et al. 1984) or **ID3 / C4.5** (Quinlan, depending on which variant). They differ in details — what split criterion they use, whether they handle multi-way categorical splits — but the skeleton is the same.

---

## 33.3 How to choose a split — classification

At a single node, we have a set $S$ of training examples that reached that node. For each possible feature $j$ and each possible threshold $t$, the candidate split partitions $S$ into

$$
S_L = \{i \in S : x_{ij} \leq t\}, \quad S_R = \{i \in S : x_{ij} > t\}
$$

We want to pick the $(j, t)$ that produces the "best" partition — one where $S_L$ and $S_R$ are each as **pure** as possible (mostly one class) compared to $S$.

We need a quantitative measure of impurity.

### 33.3.1 Entropy

The first measure, from information theory: **Shannon's entropy**. For a set $S$ where class $c$ has empirical frequency $p_c$ (i.e., $p_c = \frac{|\{i \in S : y_i = c\}|}{|S|}$),

$$
H(S) = -\sum_c p_c \log_2 p_c
$$

(By convention $0 \log 0 = 0$.) Entropy is 0 when $S$ contains only one class (one $p_c = 1$, all others 0 — $-1 \log_2 1 = 0$) and maximized at $\log_2 K$ when all $K$ classes are equally represented ($p_c = 1/K$). It measures, in a precise information-theoretic sense, the disorder of the distribution.

The base of the logarithm only changes units (bits if base 2, nats if base $e$). Most ML implementations use natural log.

### 33.3.2 Information gain

The **information gain** of a candidate split is the reduction in entropy:

$$
\text{IG}(S, j, t) = H(S) - \frac{|S_L|}{|S|} H(S_L) - \frac{|S_R|}{|S|} H(S_R)
$$

The second and third terms are the weighted average entropy of the children. We compare $H(S)$ (the parent's entropy) to that weighted average — if the split makes the children purer on average, IG is positive.

Choose the $(j, t)$ that maximizes IG.

### 33.3.3 Gini impurity

An alternative measure, faster to compute (no logarithms):

$$
G(S) = 1 - \sum_c p_c^2
$$

Same shape as entropy — zero on pure sets, maximum on uniform distributions. Gini reaches a max of $1 - 1/K$ for $K$ equally-likely classes (compared to entropy's $\log_2 K$).

Gini impurity is the *probability that two randomly drawn examples from $S$ have different classes*. To see this: pick example $i$, with probability $p_c$ it's class $c$; pick example $j$ independently, with probability $1 - p_c$ it's a *different* class. Sum over $c$: $\sum_c p_c (1 - p_c) = \sum_c p_c - \sum_c p_c^2 = 1 - \sum_c p_c^2 = G(S)$.

This interpretation is one reason Gini is so popular: it's a probabilistic notion of impurity that's easy to explain.

For binary classification: $G(S) = 2p(1-p)$ where $p$ is the frequency of class 1. Maximum 0.5 at $p = 0.5$. Entropy is $-p \log p - (1-p)\log(1-p)$. Maximum 1 (bit) at $p = 0.5$. The two are *monotonically related* over $p \in [0, 1]$ — they agree on the ordering of candidate splits. For binary classification, Gini and entropy give nearly identical trees.

For multi-class, they can occasionally disagree on which split is best, but rarely in ways that matter.

**Which to use?** Gini is faster (no `log`), so it's the default in scikit-learn and most other libraries. Entropy is more theoretically motivated. The choice rarely changes results; pick Gini and stop worrying.

---

## 33.4 How to choose a split — regression

For regression, the natural notion of "impurity" is the variance of the target within the node:

$$
\text{Var}(S) = \frac{1}{|S|} \sum_{i \in S} (y_i - \bar{y}_S)^2
$$

where $\bar{y}_S$ is the mean target in $S$. A pure node (all targets equal) has variance 0. A node with widely varying targets has high variance.

The split criterion is to minimize the weighted sum of children's variances:

$$
\text{Score}(S, j, t) = \frac{|S_L|}{|S|} \text{Var}(S_L) + \frac{|S_R|}{|S|} \text{Var}(S_R)
$$

Choose the $(j, t)$ minimizing this. Equivalently, maximize the variance reduction.

This is also equivalent to minimizing the **mean squared error** of the predictions: if the tree predicts $\bar{y}_S$ for every example in leaf $S$, the MSE on that leaf is exactly $\text{Var}(S)$. So variance reduction = MSE reduction. The tree is greedily minimizing training MSE at each split.

For regression, the prediction at a leaf is the mean of training targets in that leaf. For *robust* regression you can use the median (less sensitive to outliers); some implementations support this.

---

## 33.5 The recursive partitioning algorithm

Putting it together:

```
def build_tree(S, depth):
    if stopping_criterion(S, depth):
        return Leaf(prediction=majority_class(S) or mean(y_S))

    best_score = -infinity
    best_split = None
    for j in features:
        for t in candidate_thresholds(S, j):
            score = information_gain(S, j, t)   # or variance_reduction
            if score > best_score:
                best_score = score
                best_split = (j, t)

    if best_score <= 0:  # no improving split found
        return Leaf(prediction=majority_class(S))

    j, t = best_split
    S_L = {i in S : x_ij <= t}
    S_R = {i in S : x_ij > t}
    left = build_tree(S_L, depth + 1)
    right = build_tree(S_R, depth + 1)
    return Node(feature=j, threshold=t, left=left, right=right)
```

A few subtleties.

**Candidate thresholds.** In principle, for a continuous feature with $|S|$ distinct values, you could try $|S| - 1$ thresholds (between each pair of adjacent values). In practice, libraries either do this exactly, or — for large datasets — bin the feature into a fixed number of buckets first and try the bucket boundaries. This is what `LightGBM` and modern XGBoost do, and it's also what enables Spark MLlib's `maxBins` parameter.

**Greedy is suboptimal.** A split that looks bad locally might enable two great splits one level down. Greedy doesn't consider this. Looking ahead more than one level is computationally hard, so we accept the greedy choice. This is one reason ensembles (random forests, GBT) outperform single trees: the ensemble effectively averages over many greedy-but-different paths.

**Complexity.** For $n$ rows and $d$ features, with the natural threshold-per-row strategy, each level of the tree costs $O(nd)$ to find the best split (sort by each feature once, then a single linear pass). A tree of depth $D$ costs $O(nd \cdot D)$. Fast in practice for sane $D$.

---

## 33.6 Stopping criteria — when to stop splitting

Without any stopping rule, the algorithm will keep splitting until every leaf contains exactly one training example (impurity = 0). That tree has zero training error. It also has near-zero generalization ability — it has memorized the training set, with a separate "rule" for each training row. This is overfitting at its purest.

Standard stopping criteria, applied at every node:

- **`max_depth`**: don't split if depth ≥ some limit.
- **`min_samples_split`**: don't split if $|S|$ < some threshold (e.g., 2 or 20).
- **`min_samples_leaf`**: don't split if either child would have < some threshold examples.
- **`min_impurity_decrease`**: don't split if the impurity reduction is below some threshold (the split has to be "worth it").
- **All examples have the same label**: $H(S) = 0$, no further improvement possible.

These are all **pre-pruning** rules — they prevent splits from happening in the first place. They're cheap and effective. scikit-learn's `DecisionTreeClassifier` exposes all four as hyperparameters.

The values matter. `max_depth=3` gives a model so simple it usually underfits; `max_depth=None` (no limit) gives a model that overfits. Cross-validation chooses the right value.

A useful intuition: each leaf produces one prediction. With $n$ training examples and a leaf containing $m$ examples, the leaf is "averaging" over $m$ examples. The variance of the leaf prediction is $\sigma^2 / m$ (Chapter 19). So bigger leaves → more stable predictions → less variance. The price is bias: bigger leaves can't capture fine-grained structure.

---

## 33.7 Pruning — the post-hoc alternative

Pre-pruning has a flaw: it has to decide *up front* whether a split is worthwhile, before seeing what the deeper subtree would look like. Sometimes a split that looks mediocre on its own enables great splits below.

**Post-pruning** addresses this by growing the tree large (e.g., until every leaf is pure or has $< 5$ examples) and then *removing* subtrees that don't help.

### 33.7.1 Cost-complexity pruning

The most popular post-pruning algorithm. Define the cost-complexity of a tree $T$ as

$$
R_\alpha(T) = R(T) + \alpha \cdot |T|
$$

where $R(T)$ is the training error (or impurity) and $|T|$ is the number of leaves. $\alpha \geq 0$ is the complexity parameter — larger $\alpha$ penalizes more leaves.

For each subtree of $T$, compute the "link strength" — the ratio of impurity reduction to size reduction. The **weakest link** is the subtree whose removal increases $R(T)$ the least per leaf removed. Remove it. Repeat. The result is a *sequence* of nested trees, from the fully-grown $T$ down to a single-leaf tree.

Cross-validation picks the $\alpha$ (equivalently, the position in the sequence) that minimizes held-out error. scikit-learn implements this as `ccp_alpha` on `DecisionTreeClassifier`/`Regressor`.

### 33.7.2 Pre-pruning vs. post-pruning

- **Pre-pruning** is faster (you don't grow what you don't need), simpler to implement, and what most modern libraries default to. The downsides: it can miss good deep structure (the "splits-that-need-other-splits" issue).
- **Post-pruning** is more principled but more expensive. It's what scikit-learn's `ccp_alpha` does; what `R`'s `rpart` does by default.

In practice, the two give similar trees for similar amounts of regularization. The hyperparameter you cross-validate is different (`max_depth` for pre, `ccp_alpha` for post) but the *amount of regularization you arrive at* is what matters.

---

## 33.8 Handling categorical features

Categorical features (city, product category, customer segment) need special handling. Two approaches.

### 33.8.1 One-hot encode first

Convert a $k$-level categorical into $k$ binary columns. Now every feature is numeric and the regular splitting algorithm works. Each split is on one of the binary columns: "is city == NYC?"

**Pro:** simple, works with any tree library.

**Con:** when $k$ is large (zip code with 40,000 levels), you get 40,000 sparse features. Each one is a candidate split, and most have near-zero information gain individually. The tree wastes its depth budget on one-hot splits and never gets to the "real" features.

### 33.8.2 Native categorical splits (CART-style)

A more efficient approach for tree libraries that support it: at each node, consider all possible *binary partitions* of the $k$ category levels. With $k$ levels, there are theoretically $2^{k-1} - 1$ ways to split them into two non-empty groups, which is intractable for large $k$.

Two tricks make it tractable:

- For *binary classification*, Breiman showed that the optimal partition is found by ordering categories by their per-category $P(y=1)$ frequency and trying all $k-1$ adjacent partitions — linear in $k$, not exponential. The same trick works for regression with the per-category mean target.
- For *multi-class*, similar but more involved heuristics (e.g., LightGBM's `cat_smooth`, CatBoost's ordered target statistics).

LightGBM and CatBoost handle categoricals natively. XGBoost added native categorical support in v1.5 (2022). scikit-learn's `DecisionTreeClassifier` does NOT support native categoricals — you have to one-hot encode. Spark MLlib's tree implementations *do* handle categoricals natively, marked by `StringIndexer` followed by `VectorAssembler` (more in Chapter 64).

**The exam knowledge:** trees do NOT inherently need one-hot encoding the way linear models do. Whether you OHE depends on your library's capabilities. If you're using sklearn trees, you OHE; if you're using LightGBM, you don't.

---

## 33.9 A worked numerical example

Consider an 8-row dataset for classifying loan default:

| $i$ | Income | Age | Default? |
|----:|-------:|----:|:--------:|
| 1 | 30  | 25 | Y |
| 2 | 35  | 28 | Y |
| 3 | 40  | 30 | N |
| 4 | 45  | 35 | N |
| 5 | 55  | 40 | N |
| 6 | 60  | 22 | Y |
| 7 | 75  | 45 | N |
| 8 | 80  | 50 | N |

5 N's, 3 Y's. Compute the root's entropy:

$$
p_N = 5/8, \quad p_Y = 3/8
$$

$$
H(\text{root}) = -\frac{5}{8} \log_2 \frac{5}{8} - \frac{3}{8} \log_2 \frac{3}{8}
$$

$\log_2 (5/8) = \log_2 0.625 \approx -0.678$. $\log_2 (3/8) = \log_2 0.375 \approx -1.415$.

$H = -0.625 \cdot (-0.678) - 0.375 \cdot (-1.415) = 0.424 + 0.531 = 0.955$ bits.

**Candidate split 1: Income ≤ 35.** $S_L$ = rows 1, 2 (both Y). $S_R$ = rows 3-8 (5 N, 1 Y).

$H(S_L) = 0$ (pure). $H(S_R)$: $p_N = 5/6$, $p_Y = 1/6$. $H = -(5/6)\log_2(5/6) - (1/6)\log_2(1/6) = 0.833 \cdot 0.263 + 0.167 \cdot 2.585 = 0.219 + 0.432 = 0.651$.

Weighted average: $(2/8) \cdot 0 + (6/8) \cdot 0.651 = 0.488$.

Information gain: $0.955 - 0.488 = 0.467$.

**Candidate split 2: Income ≤ 50.** $S_L$ = rows 1-4 (2 N, 2 Y). $S_R$ = rows 5-8 (3 N, 1 Y).

$H(S_L)$: $p_N = 0.5$, $p_Y = 0.5$. $H = 1$ (max entropy for binary).

$H(S_R)$: $p_N = 0.75$, $p_Y = 0.25$. $H = -0.75 \cdot \log_2 0.75 - 0.25 \cdot \log_2 0.25 = 0.311 + 0.5 = 0.811$.

Weighted: $(4/8) \cdot 1 + (4/8) \cdot 0.811 = 0.906$.

Information gain: $0.955 - 0.906 = 0.049$. Much worse than split 1.

**Candidate split 3: Age ≤ 30.** $S_L$ = rows 1, 2, 3, 6 (2 N misordered — wait, let me re-check the data). Looking at age column: rows 1 (25), 2 (28), 3 (30), 6 (22) have age ≤ 30. That's rows 1 (Y), 2 (Y), 3 (N), 6 (Y). $S_L$: 1 N, 3 Y. $S_R$: rows 4, 5, 7, 8, all N. 4 N, 0 Y.

$H(S_L)$: $p_N = 0.25$, $p_Y = 0.75$. $H = -0.25 \log_2 0.25 - 0.75 \log_2 0.75 = 0.5 + 0.311 = 0.811$.

$H(S_R) = 0$ (pure N).

Weighted: $(4/8) \cdot 0.811 + (4/8) \cdot 0 = 0.406$.

Information gain: $0.955 - 0.406 = 0.549$. Better than split 1!

So among these three candidates, "Age ≤ 30" wins with IG = 0.549. The algorithm would try all features and all thresholds (here, all between-row thresholds for Income and Age) and pick the best. In this small example, "Age ≤ 30" is a strong split because it cleanly isolates the older-non-defaulter group.

**Recurse on $S_L$ (rows 1, 2, 3, 6).** $S_L$ has 1 N (row 3, income 40) and 3 Y (rows 1, 2, 6, incomes 30, 35, 60). Try "Income ≤ 37.5": $S_{LL}$ = rows 1, 2 (Y, Y, pure). $S_{LR}$ = rows 3, 6 (1 N, 1 Y, impure). Then another split on $S_{LR}$: "Age ≤ 26" puts row 6 (age 22) on the left (Y) and row 3 (age 30) on the right (N), both pure. Done — the left subtree is fully separated.

**Recurse on $S_R$ (rows 4, 5, 7, 8).** All N — pure already, becomes a leaf predicting N.

Final tree:

```
                Age ≤ 30?
               /         \
              yes         no
             /             \
       Income ≤ 37.5?     [predict N]
         /        \
        yes        no
       /            \
   [predict Y]    Age ≤ 26?
                  /      \
                 yes      no
                /          \
           [predict Y]  [predict N]
```

This tree achieves zero training error on 8 examples. With only 8 training rows, it's almost certainly overfit — but it demonstrates the mechanics.

---

## 33.10 Why trees overfit

Trees are *high-variance* models. A small change in the training data can produce a very different tree, because a marginal change in one split's information gain can change which feature is chosen at that node, which cascades down the whole subtree.

The deeper failure: with enough depth, a tree can memorize. With $n$ training examples and a tree of depth $\log_2 n$, you have potentially $n$ leaves and can route each training example to its own leaf with 100% accuracy. That tree has zero training error and zero generalization ability — every leaf represents one row.

**Diagnostics:**
- Training accuracy ≫ validation accuracy → overfitting.
- Tree is "deep" relative to data size — depth > $\log_2 n$ is a warning sign.
- Leaves with very few examples (< 5, < 20 — depends on noise level).

**Treatments:**
- Reduce `max_depth`.
- Increase `min_samples_leaf` or `min_samples_split`.
- Use `ccp_alpha` to prune.
- Use cross-validation to choose the regularization strength.

---

## 33.11 Why trees can also underfit

The other failure mode: stopping too early. A `max_depth=3` tree has at most 8 leaves. If your problem has more than 8 distinguishable regions in feature space, this tree can't represent them. Training and validation accuracy will both be mediocre.

The art of tree tuning is finding the depth (or `ccp_alpha`) where the bias-variance tradeoff balances. Cross-validate.

---

## 33.12 Trees can't extrapolate

A subtle limitation of trees: **each leaf is a constant prediction**. The tree partitions the input space into rectangles (in 2D — hyperrectangles in higher dimensions), and within each rectangle, the prediction is the leaf's value.

This means trees **cannot extrapolate beyond the training data range**. If your training data has $x \in [0, 100]$ and you predict on $x = 1000$, the tree routes you to whichever leaf contains the largest training $x$ value — typically a leaf that says "the mean of $y$ for $x$ values near 100." It cannot, even in principle, fit a linear extrapolation.

For regression problems with smooth, extrapolatable structure (price vs. square footage continues smoothly into mansions), linear models or polynomial models do better. For problems with complicated non-linear structure but stable distribution (most tabular classification, fraud, churn), trees and tree ensembles are excellent.

```
  Regression on y = 2x + 1, training data x ∈ [0, 10]

    y                              actual:       /
                                    y = 2x + 1  /
    20 ┤                                       /
    18 ┤  tree prediction          ━━━━━━━━━━ <- tree saturates here
    15 ┤                          ━━━━━━
    12 ┤                    ━━━━━━
     9 ┤             ━━━━━━━
     6 ┤      ━━━━━━━
     3 ┤━━━━━━
       └─────────────┬─────────────┬──────────► x
                    10            20         30
                   train edge    extrapolate
```

The tree's prediction is exactly horizontal beyond the training range. Linear regression would track the line.

---

## 33.13 What's good about trees

Despite their flaws, trees have real virtues that justify their prominence.

**No feature scaling needed.** Splits are based on comparisons; scaling doesn't change ordering, so it doesn't change splits. You can mix "income in dollars" and "age in years" with no preprocessing. Compare to linear/logistic regression with gradient descent, where unscaled features tank optimization.

**Handles non-linearity automatically.** Trees partition the feature space into axis-aligned rectangles. Within each rectangle, the prediction is constant — but across rectangles, the prediction varies. This piecewise-constant approximation can capture arbitrary non-linear patterns (with enough depth).

**Handles interactions automatically.** Once a node splits on $x_1$, the deeper splits in each subtree are conditional on $x_1$. So "split on $x_2 < 5$ if $x_1 > 10$, else split on $x_3 > 7$" is automatically representable. No need to construct interaction features by hand.

**Handles missing values (some libraries).** XGBoost and LightGBM route missing values to the side that minimizes loss during training — automatic, no imputation needed.

**Fast inference.** A prediction is a few comparisons (one per tree depth). Microseconds.

**Interpretable.** You can print the tree, walk it, explain a prediction. "This loan was flagged because age < 35 AND credit_score < 600 AND requested_amount > $20K." This is the *only* model in this book where you can show a domain expert the model itself and have them sanity-check it.

---

## 33.14 What's bad about trees

**High variance.** Small data changes → very different trees. The classic remedy is to *average* many trees — bagging (Chapter 34) and boosting (Chapters 35-36).

**Can't extrapolate.** Covered in §33.12.

**Bias toward features with many distinct values.** A high-cardinality continuous feature offers many candidate thresholds; a low-cardinality categorical offers few. The continuous feature has more "chances" to score well at any given node, so it tends to be picked even when it's no more informative. This bias propagates into feature importance scores too (Chapter 34).

**Discontinuous predictions.** Predictions change abruptly at split boundaries. For smooth real-world phenomena, this can be jarring (the predicted house price jumps by $5,000 when square footage crosses 1,500). Linear and kernel models give smooth predictions.

---

## 33.15 Code

### 33.15.1 scikit-learn

```python
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor, plot_tree
import matplotlib.pyplot as plt

# Classification
clf = DecisionTreeClassifier(
    criterion="gini",          # or "entropy"
    max_depth=5,
    min_samples_leaf=20,
    ccp_alpha=0.001,           # cost-complexity pruning
    random_state=0
)
clf.fit(X_train, y_train)

# Visualize the tree
fig, ax = plt.subplots(figsize=(12, 8))
plot_tree(clf, feature_names=feature_names, class_names=["no", "yes"],
          filled=True, ax=ax)
plt.show()

# Feature importance (Mean Decrease in Impurity — biased!)
print(dict(zip(feature_names, clf.feature_importances_)))

# Path of a single prediction
path = clf.decision_path(X_test[0:1])  # which nodes were visited
```

`plot_tree` is your friend — visualizing the actual tree is a great way to sanity-check that the model is doing something sensible.

For regression: `DecisionTreeRegressor` with `criterion="squared_error"` (the default) or `"absolute_error"` for median-based splits.

### 33.15.2 PySpark MLlib preview

```python
from pyspark.ml.classification import DecisionTreeClassifier as SparkDT

dt = SparkDT(featuresCol="features", labelCol="label",
             maxDepth=5, minInstancesPerNode=20, impurity="gini",
             maxBins=32)
model = dt.fit(train_df)
predictions = model.transform(test_df)
```

Spark's `maxBins` parameter controls the number of bins used to discretize continuous features for split-finding — a tradeoff between accuracy and speed. For high-cardinality categoricals, `maxBins` must be at least the number of categories. We'll see more in Chapter 64.

---

## 33.16 What this builds on / where this returns

**Builds on:**
- Chapter 18 — capacity and overfitting.
- Chapter 19 — bias-variance tradeoff (trees as a high-variance model class).
- Chapter 22 — cross-validation for picking `max_depth` or `ccp_alpha`.

**Returns:**
- Chapter 34 — random forests average many trees to reduce variance.
- Chapter 35 — AdaBoost builds trees sequentially, focusing on hard examples.
- Chapter 36 — gradient-boosted trees: the dominant tabular ML algorithm.
- Chapter 64-65 — Spark MLlib tree implementations.

---

## 33.17 Exercises

1. **Entropy by hand.** Compute the entropy of $S = \{1, 1, 1, 0, 0\}$ (three 1s, two 0s).

2. **Gini by hand.** Same set. Compute Gini.

3. **Information gain.** A node has 6 spam, 4 ham. A candidate split sends 5 spam + 1 ham left, 1 spam + 3 ham right. Compute information gain (using entropy).

4. **Why pure splits are picked.** Show that a split that produces two pure children (one entirely spam, the other entirely ham) achieves the *maximum* possible information gain for that node. What is it?

5. **Variance reduction for regression.** A node has targets $\{2, 3, 5, 8, 10\}$. A candidate split sends $\{2, 3, 5\}$ left and $\{8, 10\}$ right. Compute the parent variance, child variances, and the reduction.

6. **Stopping criteria.** Why does `min_samples_leaf=1` lead to overfitting?

7. **Pruning intuition.** A fully-grown tree has training error 0% and validation error 22%. After pruning with $\alpha = 0.01$, training error is 5% and validation error is 14%. Which tree should you ship and why?

8. **Categorical encoding.** A feature "zip_code" has 40,000 unique values. You want to use it in a sklearn `DecisionTreeClassifier`. What do you do? What's the problem with this approach?

9. **Extrapolation.** A regression tree was trained on house prices for homes 800-2,300 sq ft. What will it predict for a 5,000 sq ft house? Why?

10. **Tree depth and number of leaves.** A complete binary tree of depth $D$ has at most how many leaves? Given $n = 100{,}000$ training examples, what is the maximum depth that allows every leaf to have at least 10 examples (assuming a balanced tree)?

11. **Gini vs. entropy for binary.** Show that for binary classification, Gini and entropy are monotonically related — i.e., they always agree on which of two splits is better.

12. **Greedy suboptimality.** Construct a small 2D example where the greedy split at the root is *not* the same as the root split of the globally-optimal tree of depth 2.

<details>
<summary>Answers</summary>

1. $p_1 = 3/5$, $p_0 = 2/5$. $H = -(3/5)\log_2(3/5) - (2/5)\log_2(2/5) = 0.6 \cdot 0.737 + 0.4 \cdot 1.322 = 0.442 + 0.529 = 0.971$ bits.

2. $G = 1 - (3/5)^2 - (2/5)^2 = 1 - 0.36 - 0.16 = 0.48$.

3. Parent: $p_{\text{spam}} = 0.6$, $H(P) = -0.6 \log_2 0.6 - 0.4 \log_2 0.4 = 0.442 + 0.529 = 0.971$. Left (5 spam, 1 ham): $p = 5/6, 1/6$. $H(L) = 0.65$. Right (1 spam, 3 ham): $p = 1/4, 3/4$. $H(R) = 0.811$. Weighted: $(6/10) \cdot 0.65 + (4/10) \cdot 0.811 = 0.390 + 0.324 = 0.714$. IG = $0.971 - 0.714 = 0.257$.

4. Pure children have $H = 0$, so weighted children entropy is 0. IG = $H(\text{parent}) - 0 = H(\text{parent})$. That's the max possible — you can't reduce entropy below zero.

5. Mean: $(2+3+5+8+10)/5 = 5.6$. Variance: $[(2-5.6)^2 + (3-5.6)^2 + (5-5.6)^2 + (8-5.6)^2 + (10-5.6)^2]/5 = [12.96 + 6.76 + 0.36 + 5.76 + 19.36]/5 = 45.2/5 = 9.04$. Left $\{2,3,5\}$: mean 3.33, var = [(1.33)^2 + (0.33)^2 + (1.67)^2]/3 = [1.77 + 0.11 + 2.78]/3 = 1.55. Right $\{8,10\}$: mean 9, var = [1 + 1]/2 = 1. Weighted: (3/5)(1.55) + (2/5)(1) = 0.93 + 0.40 = 1.33. Reduction: 9.04 − 1.33 = 7.71.

6. Each leaf can have one example, allowing the tree to memorize the training set (zero training error, terrible generalization). With $n$ leaves there's no averaging, no smoothing, no robustness.

7. The pruned tree. Training error rose by 5 points but validation error *dropped* by 8 points — the unpruned tree was overfitting. Validation error is what matters for deployment; ship the simpler model.

8. One-hot encode → 40,000 binary columns. Problems: (a) memory blow-up; (b) the tree wastes depth on individual zip-code splits, never reaching the "real" features; (c) each zip code carries little statistical signal because there are few training examples per zip. Better: target-encode the zip (replace with mean target per zip) or use a library with native categorical handling (LightGBM, CatBoost).

9. It will predict the leaf value for whichever leaf contains the largest training square footages (likely homes near 2,300 sq ft). The prediction is a constant — the mean price of those homes, roughly. The tree literally cannot extrapolate to mansion-size; it has no leaf that represents "well beyond what I've seen."

10. A complete binary tree of depth $D$ has up to $2^D$ leaves. For $n = 100{,}000$ and ≥10 per leaf, max leaves = $10{,}000$, max depth $\log_2 10{,}000 \approx 13.3$, so $D \leq 13$.

11. For binary, let $p$ be the frequency of class 1. Gini = $2p(1-p)$. Entropy = $-p\log p - (1-p)\log(1-p)$. Both are zero at $p = 0$ and $p = 1$, both maximal at $p = 0.5$, both symmetric, both monotonically increasing on $[0, 0.5]$ and decreasing on $[0.5, 1]$. Any comparison between two impurity values $p_1 < p_2$ (without loss of generality on the same side of 0.5) goes the same way under both. They never disagree on the *ordering* of splits.

12. Consider XOR: 4 points at $(0,0)\to 0, (0,1)\to 1, (1,0)\to 1, (1,1)\to 0$. The greedy split at the root: splitting on $x_1$ (or $x_2$) gives 2 zeros + 2 ones in each child — zero information gain. Greedy is stuck. But the *optimal* tree of depth 2 splits on $x_1$ first, then on $x_2$ in each subtree — and the bottom level achieves zero error. Greedy literally can't find this because the first split has IG = 0. This is the classic XOR example for why depth-1 trees can't solve every problem.

</details>
