# Chapter 37 — Naive Bayes and K-Nearest Neighbors (for Completeness)

> **Goal of this chapter:** to give honest, working treatments of two classical algorithms — **Naive Bayes** and **K-Nearest Neighbors** — that you should know exist, when to use them, and the math that makes them tick. Neither is your daily workhorse in 2026 (logistic regression and gradient boosting dominate), but both are simple, classical, occasionally tested, and useful as baselines. Each is also a clean illustration of a different paradigm: Naive Bayes is the simplest generative classifier, and KNN is the canonical *non-parametric* model. Two more arrows in the quiver.

---

## Part I: Naive Bayes

## 37.1 The setup — Bayes' theorem applied to classification

Recall Bayes' theorem (Chapter 8): for events $A$ and $B$,

$$
P(A \mid B) = \frac{P(B \mid A) \cdot P(A)}{P(B)}
$$

In classification: given features $x$, we want the posterior $P(y = c \mid x)$ for each class $c$. Bayes' theorem gives

$$
P(y = c \mid x) = \frac{P(x \mid y = c) \cdot P(y = c)}{P(x)}
$$

The denominator $P(x)$ is the same for every class, so for picking the most likely class we can ignore it:

$$
P(y = c \mid x) \propto P(x \mid y = c) \cdot P(y = c)
$$

To use this for prediction, we'd need:

- $P(y = c)$: the **prior** — the class proportions in training data. Easy: count.
- $P(x \mid y = c)$: the **likelihood** — the probability of observing the feature vector $x$ given the class. *Hard.* For a $d$-dimensional feature vector, this is a joint distribution over $d$ variables, which generally requires $O(\prod_j |X_j|)$ parameters to fully specify. Untenable.

This is where the "naive" part kicks in.

---

## 37.2 The naive assumption

Naive Bayes assumes features are **conditionally independent given the class**:

$$
P(x \mid y = c) = \prod_{j=1}^d P(x_j \mid y = c)
$$

That is: knowing the class, the features are independent of each other.

This is **almost never literally true.** If the class is "spam," the presence of the word "viagra" is correlated with the presence of the word "free" — both are spammy. But Naive Bayes ignores this correlation and treats them as independent.

The wonder is that the algorithm *still works*. For prediction (picking the most likely class), what matters is that the conditional likelihood ratios are ordered correctly across classes — not that the absolute probabilities are accurate. Naive Bayes preserves the *ordering* of likelihoods even when the independence assumption is wrong. This is why Naive Bayes is a much better classifier than it is a probability estimator.

The complete predictor:

$$
\hat{y}(x) = \arg\max_c P(y = c) \cdot \prod_{j=1}^d P(x_j \mid y = c)
$$

In practice we work in log space to avoid underflow:

$$
\hat{y}(x) = \arg\max_c \left[ \log P(y = c) + \sum_{j=1}^d \log P(x_j \mid y = c) \right]
$$

---

## 37.3 Variants — how do we model P(xⱼ | y = c)?

The naive Bayes framework needs one piece of machinery: how do we estimate $P(x_j \mid y = c)$ for each feature? Different distributional assumptions give different variants.

### 37.3.1 Gaussian Naive Bayes (continuous features)

Assume each feature, conditional on the class, is Normally distributed: $x_j \mid y = c \sim \mathcal{N}(\mu_{jc}, \sigma_{jc}^2)$. Estimate $\mu_{jc}$ and $\sigma_{jc}^2$ from the training data — the per-class mean and variance of each feature.

At prediction time, plug into the Normal PDF:

$$
P(x_j \mid y = c) = \frac{1}{\sqrt{2\pi \sigma_{jc}^2}} \exp\left(-\frac{(x_j - \mu_{jc})^2}{2 \sigma_{jc}^2}\right)
$$

Take logs and sum.

**Strengths:** trivial to fit, fast to predict, handles continuous features naturally.

**Weaknesses:** the Normal assumption is often wrong. If a feature is bimodal, has heavy tails, or is bounded (e.g., proportions in $[0, 1]$), Gaussian NB fits poorly.

`sklearn.naive_bayes.GaussianNB`.

### 37.3.2 Multinomial Naive Bayes (count features)

For features that are non-negative counts — think of bag-of-words from Chapter 3. The model: given the class, each word has a probability $p_{cj}$ of being drawn, and the document is a multinomial sample.

$$
P(x \mid y = c) = \frac{n!}{\prod_j x_j!} \prod_j p_{cj}^{x_j}
$$

(The combinatorial factor is the same for every class — drops out of the argmax. So effectively we compute $\sum_j x_j \log p_{cj}$.)

Estimate $p_{cj}$ as the fraction of all words in class $c$ that are word $j$:

$$
\hat{p}_{cj} = \frac{N_{cj}}{\sum_{j'} N_{cj'}}
$$

where $N_{cj}$ is the count of word $j$ across all training documents of class $c$.

**Strengths:** the classical text-classification baseline. Spam detection (Chapter 3), topic classification, language identification. Very fast.

**Weaknesses:** assumes word counts are multinomially distributed, ignores word order, ignores feature correlations.

`sklearn.naive_bayes.MultinomialNB`.

### 37.3.3 Bernoulli Naive Bayes (binary features)

For features that are 0/1 — e.g., "does the word appear at all in this document?" rather than "how many times?" The model: each feature is an independent Bernoulli trial conditional on the class.

$$
P(x_j \mid y = c) = p_{cj}^{x_j} \cdot (1 - p_{cj})^{1 - x_j}
$$

Useful for short documents (where presence matters more than count) and binary indicator features.

`sklearn.naive_bayes.BernoulliNB`.

### 37.3.4 Categorical Naive Bayes (discrete features)

For features that are unordered categorical (color = red/blue/green). Maintain a full categorical distribution $P(x_j = v \mid y = c)$ for each (feature, class, value) combo. Estimate by counting.

`sklearn.naive_bayes.CategoricalNB`.

---

## 37.4 Laplace smoothing — handling zero counts

A pitfall. Suppose in our spam training set, the word "syzygy" never appears in any spam email. The MLE estimate is $\hat{p}_{\text{spam, syzygy}} = 0$. Now suppose a new email contains "syzygy" — the conditional likelihood becomes $0 \cdot (\text{everything else}) = 0$, and the model assigns probability 0 to spam regardless of any other evidence.

A single missing observation has destroyed the entire prediction. This is the classic problem with MLE on count data.

**Laplace smoothing** (also called add-one smoothing, or Lidstone smoothing for general $\alpha$): add a small pseudo-count to every cell:

$$
\hat{p}_{cj} = \frac{N_{cj} + \alpha}{\sum_{j'} N_{cj'} + \alpha \cdot d}
$$

where $\alpha > 0$ is the smoothing strength (default $\alpha = 1$ — Laplace) and $d$ is the vocabulary size. Every probability is now bounded away from zero, and the model is robust to unseen feature values.

This is, mathematically, a Bayesian estimator under a Dirichlet prior with parameter $\alpha$. We won't lean on that view, but it's where the smoothing falls out of.

scikit-learn's `MultinomialNB(alpha=1.0)` exposes this. $\alpha = 1$ is the default and is sensible; larger $\alpha$ regularizes more.

---

## 37.5 Worked example — multinomial NB on tiny text

Vocabulary: {free, money, meeting, schedule}. Training data: 4 documents.

| Doc | Words present (counts) | Label |
|----|---|------|
| 1 | free=2, money=1 | spam |
| 2 | free=1, money=2, meeting=0, schedule=0 | spam |
| 3 | meeting=1, schedule=2 | ham |
| 4 | free=0, money=0, meeting=2, schedule=1 | ham |

Aggregate per-class word counts:

| | free | money | meeting | schedule | total |
|---|-----:|------:|--------:|---------:|------:|
| spam | 3 | 3 | 0 | 0 | 6 |
| ham  | 0 | 0 | 3 | 3 | 6 |

With Laplace smoothing $\alpha = 1$:

$$
\hat{p}_{\text{spam, free}} = \frac{3 + 1}{6 + 4} = 0.4, \quad \hat{p}_{\text{spam, money}} = 0.4
$$
$$
\hat{p}_{\text{spam, meeting}} = \frac{0 + 1}{10} = 0.1, \quad \hat{p}_{\text{spam, schedule}} = 0.1
$$

(All sum to 1.0 across vocabulary, good.)

Similarly for ham: $\hat{p}_{\text{ham, free}} = 0.1$, ham, money = 0.1, ham, meeting = 0.4, ham, schedule = 0.4.

Class priors: $P(\text{spam}) = P(\text{ham}) = 0.5$.

**Predict a new doc with counts free=1, money=0, meeting=1, schedule=0.**

Log-likelihood for spam: $\log 0.5 + 1 \cdot \log 0.4 + 0 \cdot \log 0.4 + 1 \cdot \log 0.1 + 0 \cdot \log 0.1 = \log 0.5 + \log 0.4 + \log 0.1$
$= -0.693 - 0.916 - 2.303 = -3.912$.

Log-likelihood for ham: $\log 0.5 + 1 \cdot \log 0.1 + 0 + 1 \cdot \log 0.4 + 0 = -0.693 - 2.303 - 0.916 = -3.912$.

A *tie* — the new doc has one strong spam indicator (free) and one strong ham indicator (meeting), and they cancel out exactly. The prediction is ambiguous, with $P(\text{spam}) = P(\text{ham}) = 0.5$. Naive Bayes is producing the correct intuition: this doc is mixed.

If we changed the new doc to free=2, money=0, meeting=1, schedule=0, the log-likelihood for spam gains an extra $\log 0.4 = -0.916$ (total $-4.828$), and ham gains an extra $\log 0.1 = -2.303$ (total $-6.215$). Spam wins.

---

## 37.6 Pros and cons of Naive Bayes

**Pros:**
- **Very fast to train.** Just count.
- **Very fast to predict.** A few multiplications.
- **Works with small data.** No optimization, no hyperparameter tuning (mostly).
- **Decent text classification baseline.** Multinomial NB on bag-of-words is the canonical fast text classifier.
- **Handles high-dimensional sparse data** (text) naturally.
- **Online learning friendly.** Easy to update counts as new data arrives.

**Cons:**
- **The independence assumption hurts.** When features are correlated, NB's probability estimates are poorly calibrated (typically over-confident, because the model multiplies dependent likelihoods as if independent). The class *ranking* is often correct; the probabilities are not.
- **Slightly worse accuracy than logistic regression** on the same features, in most cases. NB is the asymptote of logistic regression with infinite training data IF the features really are independent given class — they're not.
- **Limited expressiveness.** Cannot capture interactions or non-additive effects.

For text classification, multinomial NB is a strong, fast baseline that takes 10 lines of code. For everything else, logistic regression or GBT will usually beat it.

---

## Part II: K-Nearest Neighbors

## 37.7 The simplest possible classifier

KNN is the simplest algorithm in this book. There's no training. The "model" is the entire training set.

**Training:** Store the training set.

**Prediction (for a new $x$):**
1. Compute the distance from $x$ to every training example.
2. Find the $k$ closest training examples.
3. For classification: predict the majority class among them.
4. For regression: predict the mean (or median) target among them.

That's it. No model parameters. No optimization. No assumption about the functional form of $f$.

This is the canonical **non-parametric** model. Compare to linear regression (parametric: $d+1$ parameters representing a hyperplane) or even decision trees (semi-parametric: the structure depends on data, but the model has finite complexity). KNN's "model" is the data itself, of unbounded size.

---

## 37.8 Distance metrics

KNN's behavior depends entirely on the choice of distance. The standard options:

**Euclidean distance** (L2):
$$
d(x, x') = \sqrt{\sum_j (x_j - x'_j)^2}
$$
The default. Implicitly assumes features have comparable scales and that "geometric distance" is meaningful.

**Manhattan distance** (L1):
$$
d(x, x') = \sum_j |x_j - x'_j|
$$
Less sensitive to outliers in any one feature. Used when features represent discrete steps (city grids — hence "Manhattan").

**Chebyshev distance** (L∞):
$$
d(x, x') = \max_j |x_j - x'_j|
$$
The maximum coordinate-wise difference. Used in chessboard-like problems.

**Mahalanobis distance:**
$$
d(x, x') = \sqrt{(x - x')^\top \Sigma^{-1} (x - x')}
$$
where $\Sigma$ is the data covariance matrix. This *automatically* handles feature scaling and correlation — it's the Euclidean distance after whitening the data (rotating and scaling so the covariance becomes the identity). Beautiful in theory; computationally expensive in practice.

**Cosine distance** (for normalized vectors):
$$
d(x, x') = 1 - \frac{x \cdot x'}{\|x\| \cdot \|x'\|}
$$
Useful for text (TF-IDF vectors) and embeddings — captures direction rather than magnitude.

**The choice matters.** A KNN classifier with Euclidean distance on un-scaled data behaves very differently from one with cosine distance, and both differ from Manhattan.

---

## 37.9 The scaling imperative

This is one of the most common KNN pitfalls. Consider 2 features:

- `age`: range 0-100.
- `income`: range 0-1,000,000.

The Euclidean distance between two people is dominated by the income coordinate — the age contribution is rounding error. A 50-year-old earning $50K is "closer" (by Euclidean distance) to a 60-year-old earning $50K than to a 51-year-old earning $51K. Almost certainly the wrong answer for any meaningful application.

**Fix: standardize features before applying KNN.** Subtract the mean, divide by the standard deviation, so every feature is on the same scale (mean 0, variance 1). Now distances reflect "how unusual is this difference, in standard-deviation units." `sklearn.preprocessing.StandardScaler` does it.

KNN without standardization is one of the most common beginner errors. Always standardize.

---

## 37.10 Choosing k

The hyperparameter that most matters. Two extremes:

- **k = 1:** the prediction is the label of the single nearest neighbor. Very low bias (the model perfectly fits training data — every training point's nearest neighbor is itself). Very high variance (a single noisy training point can flip predictions). The classic overfitting regime.

- **k = n** (all training points): the prediction is the global majority class (or mean). Very high bias (model is a constant). Zero variance. The classic underfitting regime.

The right $k$ is somewhere in between, and depends on the problem. Cross-validation finds it.

**Rules of thumb:**
- For binary classification, use odd $k$ to avoid ties.
- $k = \sqrt{n}$ is a common heuristic for moderate $n$.
- Typical values: 3, 5, 11, 21, 51.

KNN's prediction surface is piecewise-constant — within a Voronoi cell defined by the $k$ nearest training points, the prediction is constant. The decision boundary is "jagged" for small $k$, "smooth" for large $k$.

```
  k = 1: jagged decision boundary, follows every training point

  k = 25: smooth boundary, but might miss small clusters
```

---

## 37.11 Weighted KNN

Standard KNN votes equally among the $k$ neighbors. But closer neighbors are probably more relevant. **Weighted KNN** weights each neighbor by inverse distance:

$$
w_i = \frac{1}{d(x, x_i) + \epsilon}
$$

(The $\epsilon$ avoids division by zero when $x_i$ matches $x$ exactly.)

Prediction is the weighted vote / weighted mean. Often a small improvement over uniform weights.

`sklearn.neighbors.KNeighborsClassifier(weights="distance")` enables this.

---

## 37.12 The curse of dimensionality

KNN's Achilles' heel. In high dimensions, the very notion of "near" becomes meaningless.

**The geometric reason.** In $d$ dimensions, the volume of a unit hypercube is 1, but the volume of a unit hypersphere shrinks rapidly with $d$. By dimension 10, the hypersphere is only ~0.25% of the cube; by dimension 50, essentially zero. Random points uniformly distributed in the hypercube are almost all *near the corners*, far from any central point you might query.

More concretely: in high dimensions, the *ratio* between the nearest-neighbor distance and the farthest-neighbor distance approaches 1. Every point is roughly equidistant from every other point. KNN's premise — that the closest training points are the most informative — breaks down.

**Quantitative.** In $d$ dimensions with $n$ training points uniformly distributed in $[0,1]^d$, the expected distance to the nearest neighbor scales like $n^{-1/d}$. For $d = 10$ and $n = 10{,}000$, this is $10000^{-0.1} \approx 0.40$ — that's nearly half the diameter of the unit cube. The "nearest neighbor" isn't very near.

**Implications:**
- KNN works well for $d \leq 10$ or so.
- For higher dimensions, either reduce dimensionality first (PCA — Chapter 40) or use a different algorithm.
- Modern vector search systems exist precisely because dense, high-dimensional embeddings make naive KNN intractable; you need approximate nearest neighbor (ANN) methods like HNSW, IVF, ScaNN.

---

## 37.13 Compute cost

Each prediction requires computing distance to every training point — $O(nd)$ per query, $O(n)$ if you ignore the $d$ factor.

For small $n$ (thousands), this is fine. For $n = 1$ million, a single prediction takes a noticeable amount of compute. For $n = $ billions, it's intractable.

**Mitigations:**

**KD-trees.** Spatial partitioning that lets you skip parts of the training set you know are too far. Effective for $d \leq 20$; breaks down in higher dimensions (curse of dimensionality strikes again).

**Ball-trees.** Similar to KD-trees but uses balls instead of axis-aligned boxes. Better for non-uniform data.

**Approximate Nearest Neighbor (ANN).** Sacrifice exactness for speed. Modern algorithms (HNSW, LSH, IVF) return the *approximate* k nearest neighbors with high probability, achieving sub-linear query time even in high dimensions.

For ML on tabular data with $n < 10{,}000$, brute-force KNN is fine. Beyond that, use a tree structure or ANN. Beyond text/embedding scale (millions of vectors, high $d$), use a dedicated vector database (Topic 01 covers this in depth).

---

## 37.14 When KNN wins and loses

### 37.14.1 Wins

- **Few features ($d \leq 10$), many examples ($n$ large), complex non-linear decision boundary.** KNN's local-fitting nature captures arbitrary shapes — perfect for problems where the structure is non-linear but smooth.
- **Recommendation systems.** Item-item KNN (find similar items based on user co-occurrence) was the dominant collaborative filtering technique pre-deep learning.
- **Anomaly detection.** Points whose KNN distances are unusually large are anomalies.
- **Few-shot problems.** When you have very little labeled data and want to make decisions, KNN can be more useful than a heavily parametric model that needs lots of data to converge.

### 37.14.2 Loses

- **High dimensions** (curse of dimensionality).
- **Large $n$ with tight latency budget** (slow prediction).
- **Need feature importances or interpretability** (KNN gives none).
- **Need probability estimates** (KNN's "fraction of $k$ neighbors voting for class" is a poor probability estimator).
- **Mixed feature types where good distance metric is unclear** (categorical + numerical).

---

## 37.15 Worked example — KNN classification

A 6-row 2D training set:

| $i$ | $x_1$ | $x_2$ | $y$ |
|----:|------:|------:|----:|
| 1 | 1 | 1 | A |
| 2 | 2 | 1 | A |
| 3 | 1 | 2 | A |
| 4 | 4 | 4 | B |
| 5 | 5 | 4 | B |
| 6 | 4 | 5 | B |

Query: $x = (3, 3)$. Use $k = 3$ and Euclidean distance.

Compute distances:
- to (1,1): $\sqrt{4 + 4} = \sqrt{8} \approx 2.83$
- to (2,1): $\sqrt{1 + 4} = \sqrt{5} \approx 2.24$
- to (1,2): $\sqrt{4 + 1} = \sqrt{5} \approx 2.24$
- to (4,4): $\sqrt{1 + 1} = \sqrt{2} \approx 1.41$
- to (5,4): $\sqrt{4 + 1} = \sqrt{5} \approx 2.24$
- to (4,5): $\sqrt{1 + 4} = \sqrt{5} \approx 2.24$

Sort: (4,4) at 1.41, then a 4-way tie at 2.24, then (1,1) at 2.83.

The 3 nearest are (4,4) and two of the four tied points. With sklearn's `KNeighborsClassifier`, ties in distances are broken by training-set order (typically). Let's say it picks (4,4), (2,1), (1,2) — labels B, A, A.

Vote: 2 A's, 1 B → predict A.

Now try $k = 1$: nearest is (4,4) with label B → predict B.

The choice of $k$ flipped the prediction. This is the classic KNN sensitivity. With weighted KNN, (4,4) at distance 1.41 has a larger weight than the others at 2.24, which would shift things toward B even at $k = 3$.

---

## 37.16 Code

### 37.16.1 Naive Bayes

```python
from sklearn.naive_bayes import GaussianNB, MultinomialNB, BernoulliNB
from sklearn.feature_extraction.text import CountVectorizer

# For text classification — the canonical NB use case
vec = CountVectorizer(stop_words="english", max_features=5000)
X_counts = vec.fit_transform(text_train)

nb = MultinomialNB(alpha=1.0)  # Laplace smoothing
nb.fit(X_counts, y_train)
print(nb.predict(vec.transform(text_test)))
print(nb.predict_proba(vec.transform(text_test)))  # though these are poorly calibrated
```

### 37.16.2 KNN

```python
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("knn", KNeighborsClassifier(n_neighbors=5, weights="distance",
                                  metric="euclidean", algorithm="ball_tree")),
])
pipe.fit(X_train, y_train)
print(pipe.score(X_test, y_test))
```

`algorithm="ball_tree"` or `"kd_tree"` for indexed nearest-neighbor lookup; `"brute"` for brute force. `"auto"` picks based on data dimensionality.

### 37.16.3 No Spark MLlib KNN

A genuine gap in pyspark.ml: **there is no KNN classifier in Spark MLlib**. This isn't an oversight; KNN is fundamentally awkward in a distributed setting. Each query needs to compute distances to all $n$ training points, which means either broadcasting the entire training set to every executor (cost: $n$ in memory) or shuffling every query against the training data (cost: massive network). Neither fits Spark's design.

If you need KNN at Spark scale, options:

1. Use Approximate Nearest Neighbor libraries that have Spark wrappers (e.g., the `synapseml` package's LSH implementation).
2. Use a dedicated vector database (Pinecone, Weaviate, Milvus) as a side service called from Spark.
3. Compute embeddings in Spark, then index in a vector database for KNN queries.

This gap is worth knowing for the exam: if a question asks "which of these algorithms is available in pyspark.ml?", KNN is the wrong answer.

---

## 37.17 What this builds on / where this returns

**Builds on:**
- Chapter 8 — Bayes' theorem.
- Chapter 6 — Bernoulli, Multinomial distributions.
- Chapter 12 — distances in vector space.

**Returns:**
- Limited Spark return because neither algorithm has a strong distributed implementation in MLlib.
- Naive Bayes echoes again in Chapter 42 when we discuss probability calibration — NB is the canonical "poorly-calibrated but accurate-classifier" example.

---

## 37.18 Exercises

1. **Why "naive"?** Explain the independence assumption in your own words. Give an example of two features that are clearly NOT conditionally independent given the class.

2. **Multinomial NB by hand.** Using the 4-document training set from §37.5, predict the class of a new document with counts (free=0, money=0, meeting=2, schedule=1). Show the log-likelihoods.

3. **Laplace smoothing.** Why does $\alpha = 0$ (no smoothing) lead to failures? Give a specific scenario.

4. **NB calibration.** A Naive Bayes classifier predicts $P(\text{spam}) = 0.99$ for 100 emails. Of those, 80 actually are spam. Is the model well-calibrated at this probability level? Explain why NB tends to be miscalibrated.

5. **KNN with k=1.** What is the training error of a KNN classifier with $k = 1$ on any dataset? Explain.

6. **KNN with k=n.** What does a KNN classifier with $k$ = the size of the training set predict, regardless of input? Explain.

7. **Scaling effects.** Compute the Euclidean distance between $(30, 50000)$ and $(35, 51000)$. Now standardize both features (assume both means are typical and SDs are $age = 10$, $income = 20000$). Recompute. Which feature dominated before scaling? After?

8. **Choosing distance metric.** For a TF-IDF document classification problem, would you use Euclidean, Manhattan, or cosine distance? Why?

9. **Curse of dimensionality.** In 10 dimensions, suppose you have 10,000 uniformly distributed training points in $[0,1]^{10}$. Roughly what's the expected distance to the nearest neighbor? (Compare to the cube's diameter $\sqrt{10} \approx 3.16$.)

10. **KNN compute.** A nearest-neighbor query in 100 dimensions with 1 million training points using brute force takes how many distance computations? How many operations roughly?

11. **NB vs. logistic regression.** Both can do binary classification on text. On the same data, NB usually trains faster but classifies slightly worse. Why each? When would you actually prefer NB?

12. **The PySpark gap.** Why doesn't pyspark.ml have a KNN classifier? Name one alternative if you needed nearest-neighbor lookup at Spark scale.

<details>
<summary>Answers</summary>

1. The "naive" assumption is that features are conditionally independent given the class — $P(x_1, x_2 \mid y) = P(x_1 \mid y) P(x_2 \mid y)$. This is rarely true. Example: in a spam classifier, features "contains 'click'" and "contains 'here'" are highly correlated (people don't write one without the other in spammy contexts) — but NB treats them as independent.

2. Same as §37.5 in reverse. Log-likelihood for spam: $\log 0.5 + 0 \cdot \log 0.4 + 0 + 2 \log 0.1 + 1 \log 0.1 = -0.693 + 0 + 0 - 4.605 - 2.303 = -7.601$. For ham: $-0.693 + 0 + 0 + 2 \log 0.4 + 1 \log 0.4 = -0.693 - 1.833 - 0.916 = -3.442$. Ham wins decisively.

3. With $\alpha = 0$, any feature value not seen in training for a given class has $\hat{p} = 0$. At prediction, multiplying by 0 zeros out the entire likelihood for that class. A single never-seen word in a new document permanently rules out a class, even if other features overwhelmingly suggest it.

4. Among 100 emails predicted at 0.99, 80 are spam — model expects 99 to be spam. The model is overconfident — predicting 0.99 when the actual rate is 0.80. NB tends to be overconfident because it multiplies dependent likelihoods as if independent; the multiplication compounds and pushes probabilities toward 0 or 1.

5. Zero. The nearest training point to any training point is itself (distance 0), and KNN with $k=1$ predicts that point's label — which is its true label. Perfect training accuracy, often poor generalization.

6. The global majority class (or the global mean for regression). Every prediction averages over the entire training set, which is independent of $x$.

7. Original: $\sqrt{25 + 1000000^2 / 10^6} = \sqrt{25 + 10^6}$. Wait — $(51000-50000)^2 = 10^6$. Distance: $\sqrt{25 + 1{,}000{,}000} = \sqrt{1{,}000{,}025} \approx 1000.01$. Income dominates utterly. After standardization: age diff = $5/10 = 0.5$; income diff = $1000/20000 = 0.05$. Distance: $\sqrt{0.25 + 0.0025} = \sqrt{0.2525} \approx 0.503$. Now age dominates.

8. Cosine. TF-IDF vectors have meaningless magnitudes (longer documents have larger norms), but the *direction* (which words are emphasized) is what matters. Cosine ignores magnitude.

9. The expected nearest-neighbor distance in $[0,1]^d$ with $n$ uniform points scales like $n^{-1/d}$. For $d=10$, $n=10000$: $10000^{-0.1} \approx 0.40$ — almost half the diameter. The "nearest" is far.

10. 1 million distance computations, each involving 100 subtractions, squares, and a sum — say ~300 ops per distance, so $3 \times 10^8$ ops per query. At ~$10^9$ ops/sec, ~0.3 seconds per query. Untenable for online prediction.

11. NB trains in one pass (counting); logistic regression needs iterative optimization. NB's independence assumption hurts accuracy when features are correlated; logistic regression doesn't make this assumption. Prefer NB when (a) you have very little data (NB's bias regularizes), (b) you need very fast training/prediction, (c) it's a quick baseline.

12. KNN is awkward in distributed settings — each query needs distances to all $n$ training points, which means either broadcasting the entire training set (memory cost) or shuffling per query (network cost). Neither fits Spark's design. Alternative: approximate nearest-neighbor in a dedicated vector DB (Pinecone, Milvus, Weaviate), or use synapseml's LSH-based KNN approximation.

</details>
