# Chapter 38 — K-Means Clustering

> **Goal of this chapter:** to derive the workhorse algorithm of unsupervised learning from scratch. By the end you should be able to: state K-means as the alternating minimisation of a specific objective; prove (informally but rigorously) that it is guaranteed to converge; explain why it can converge to a bad answer; explain why K-means++ initialisation usually fixes that; choose $k$ with the elbow method, the silhouette score, and the gap statistic, and know what each method actually measures; predict the kinds of data on which K-means will quietly produce nonsense; and run K-means on real data with both scikit-learn and `pyspark.ml`. The math is small. The intuition is geometric. Most engineers who "know K-means" know the algorithm but not the failure modes — we will not let you graduate into that category.

---

## 38.1 The motivating problem

Suppose you are an analyst at a retailer. You have a table of one hundred thousand customers. For each customer, you have a handful of behavioural numbers — average order value, purchases per month, fraction of returns, days since last order, browsing-session length. Your marketing director walks over with the kind of problem that has no clean answer:

> "I'm pretty sure our customers segment naturally into about five groups. The price-sensitive deal-hunters. The loyal regulars. The occasional bulk-buyers. Maybe two more flavours of the above. I want a campaign tuned to each group. But I don't know which customer is in which group, and I'm not going to label a hundred thousand of them."

This is the classic *clustering* problem. We have data $\{x_1, x_2, \ldots, x_n\}$ — but no labels. The hypothesis is that the data are not uniformly distributed across feature space; they cluster, in some loose sense, into a small number of groups. Our job is to discover the groups.

Discovery is doing a lot of work in that sentence. There is no oracle to tell us what "five groups" means, or whether five is the right number, or whether the groupings are real or an artefact of our representation. Unsupervised learning is *exploratory*: we are looking for structure, not validating a hypothesis against ground truth. That changes how we evaluate, what we deliver, and how the rest of the business uses our output. But before we worry about any of that, let's get the simplest, most influential clustering algorithm right.

The algorithm is K-means. It was independently invented several times in the late 1950s and early 1960s — by Steinhaus, by Lloyd, by MacQueen — and the version we use today is essentially the one Lloyd wrote down in an unpublished 1957 Bell Labs report. Seventy years later it is still the first clustering algorithm anyone reaches for. It is fast, it is simple, it scales, it has only one hyperparameter that matters, and it does the right thing on a startling fraction of real problems. It also fails in instructive ways, which we will eventually exploit to motivate the algorithms in the next two chapters.

---

## 38.2 The setup, geometrically

Fix a number $k$. We will assume, for now, that we have been told $k$; the question of choosing it lives in section 38.7. Our problem:

We have $n$ points $x_1, \ldots, x_n$ in $\mathbb{R}^d$. We want to partition them into $k$ groups $C_1, C_2, \ldots, C_k$ — every point belongs to exactly one group — such that points in the same group are "close together" and points in different groups are "far apart". Each group will also have a representative point $\mu_j$, called its **centroid**, which lives in $\mathbb{R}^d$.

A picture in two dimensions is worth a thousand words:

```
         feature 2
            ▲
            │       ●●●
            │      ● ● ●        Cluster 1
            │     ●●μ₁●●
            │      ●●●
            │
            │
            │                       ●
            │                     ●●●●●  Cluster 3
            │     ●●               ●μ₃●
            │    ●●●●               ●●●
            │   ●●μ₂●●
            │    ●●●●
            │     ●●
            │  Cluster 2
            └─────────────────────────►  feature 1
```

Three clusters, three centroids. Each point belongs to the cluster whose centroid is nearest. Each centroid sits at the geometric centre of its cluster's points. Both halves of that sentence are doing work — and they are mutually defining. The cluster assignment depends on where the centroid is; the centroid depends on which points are in the cluster.

K-means cuts that circular definition with an alternating-minimisation procedure. We will write down the objective first, then the algorithm.

---

## 38.3 The objective: within-cluster sum of squares

K-means is not "just an algorithm". It is the optimisation of a specific, well-defined objective function. This matters because once you know what is being minimised, you can reason about when it will work, when it will fail, and what alternatives are doing differently.

Let $C = (C_1, \ldots, C_k)$ be a partition of the $n$ points into $k$ non-empty subsets, and let $\mu = (\mu_1, \ldots, \mu_k)$ be a tuple of $k$ centroids in $\mathbb{R}^d$. Define

$$
J(C, \mu) \;=\; \sum_{j=1}^{k} \sum_{x \in C_j} \| x - \mu_j \|^2
$$

This is the **within-cluster sum of squares**, often abbreviated WCSS, sometimes called the *inertia* (which is what scikit-learn's `KMeans.inertia_` attribute reports). In words: for each cluster, sum the squared Euclidean distance from each point in the cluster to that cluster's centroid; then add those numbers across all clusters.

K-means is the procedure that tries to minimise $J(C, \mu)$ jointly over $C$ and $\mu$:

$$
\min_{C, \mu} \;\; \sum_{j=1}^{k} \sum_{x \in C_j} \| x - \mu_j \|^2
$$

A few things to notice immediately.

First, the objective uses **squared Euclidean distance**. Not absolute distance, not cosine distance, not Mahalanobis. The squared part is essential — it makes the centroid update step have a closed form, as we'll see. If you change the distance metric, you change the algorithm; "K-means with cosine distance" is a different algorithm called *spherical K-means*, and "K-means with absolute distance" is a different algorithm called *K-medoids* or *K-medians* depending on the variant. We will get to those briefly later.

Second, the objective is jointly non-convex in $(C, \mu)$. This is what makes the problem hard. If you fixed $C$, $\mu$ would have a unique optimum (we'll derive it). If you fixed $\mu$, $C$ would have a unique optimum. But optimising both at once is, in general, NP-hard. K-means does not solve the joint problem; it does a clever alternating thing that gets a local optimum and hopes that's close enough.

Third, the absolute value of $J$ depends on the scale of the features. Doubling every coordinate multiplies $J$ by four. So $J$ is meaningful for *comparing* different clusterings of the same data, not as an absolute "goodness" number.

---

## 38.4 The algorithm: Lloyd's alternating minimisation

Here is K-means, in five lines:

> 1. Initialise $k$ centroids $\mu_1, \ldots, \mu_k$ somehow (we'll discuss how, in 38.6).
> 2. **Assignment step:** For each point $x_i$, assign it to the cluster $j$ whose centroid is nearest:
> $$ C_j \leftarrow \{ x_i : \|x_i - \mu_j\| \leq \|x_i - \mu_{j'}\| \text{ for all } j' \neq j \} $$
> 3. **Update step:** Move each centroid to the mean of the points currently assigned to it:
> $$ \mu_j \leftarrow \frac{1}{|C_j|} \sum_{x \in C_j} x $$
> 4. If no point changed cluster in step 2 (or centroids moved less than some threshold), stop.
> 5. Otherwise, go to step 2.

That's it. The two steps alternate until convergence. The algorithm is sometimes called **Lloyd's algorithm** after the Bell Labs engineer who wrote it down in 1957.

Now let's prove three things, in order: the assignment step minimises $J$ for fixed $\mu$; the update step minimises $J$ for fixed $C$; therefore the algorithm makes $J$ non-increasing; therefore (since $J \geq 0$) it converges.

### 38.4.1 The assignment step minimises $J$ for fixed $\mu$

Hold the centroids fixed at $\mu_1, \ldots, \mu_k$ and ask: how should we assign points to clusters to minimise $J$?

$$
J(C, \mu) = \sum_{j=1}^{k} \sum_{x \in C_j} \| x - \mu_j \|^2 = \sum_{i=1}^{n} \| x_i - \mu_{c(i)} \|^2
$$

where $c(i)$ is the cluster $x_i$ is assigned to. The right-hand side decomposes per-point: each $x_i$ contributes $\| x_i - \mu_{c(i)} \|^2$. We can therefore optimise per-point. For each $x_i$, we want to pick $c(i)$ to minimise $\| x_i - \mu_{c(i)} \|^2$. That is achieved by setting $c(i)$ to the index of the centroid nearest $x_i$. Done.

This is the assignment step. It is provably optimal *given the current centroids*. Ties (when a point is exactly equidistant from two centroids) can be broken arbitrarily; in practice they almost never occur in real-valued data.

### 38.4.2 The update step minimises $J$ for fixed $C$

Hold the assignments fixed and ask: for each cluster, where should the centroid go to minimise $J$?

Look at one cluster $C_j$. Its contribution to $J$ is

$$
J_j(\mu_j) = \sum_{x \in C_j} \| x - \mu_j \|^2
$$

This is a function of $\mu_j$ alone (the other centroids contribute nothing to $C_j$'s term). Expand the squared norm coordinate-wise. For coordinate $\ell$ of $\mu_j$,

$$
\frac{\partial J_j}{\partial \mu_j^{(\ell)}} = \sum_{x \in C_j} 2 \cdot (\mu_j^{(\ell)} - x^{(\ell)})
$$

Setting this to zero:

$$
\sum_{x \in C_j} (\mu_j^{(\ell)} - x^{(\ell)}) = 0 \;\;\Longrightarrow\;\; |C_j| \cdot \mu_j^{(\ell)} = \sum_{x \in C_j} x^{(\ell)} \;\;\Longrightarrow\;\; \mu_j^{(\ell)} = \frac{1}{|C_j|} \sum_{x \in C_j} x^{(\ell)}
$$

So the optimal centroid is the coordinate-wise mean of the cluster's points — the **centroid**, in the elementary-school sense. The second derivative is positive (it equals $2 |C_j|$), so this is a minimum, not a saddle point or a maximum.

This is the update step. It is provably optimal *given the current assignments*. Notice that the closed-form mean fell out because the objective was a sum of squared Euclidean distances. If we had used absolute distance instead, the optimal "centre" for each cluster would be the geometric median, which has no closed form.

### 38.4.3 Convergence

Together, the two facts above tell us that *each step of K-means weakly decreases $J$*. The assignment step picks the assignment that minimises $J$ given current $\mu$; this can only lower or keep $J$ the same. The update step picks the $\mu$ that minimises $J$ given current $C$; same story. So $J$ is monotonically non-increasing across iterations.

$J$ is also bounded below by zero (it's a sum of squares). A monotonically non-increasing sequence bounded below converges. Therefore $J$ converges.

But that's not quite the same as the *algorithm* converging — $J$ could keep decreasing by tiny amounts forever. Here is the stronger argument. There are only finitely many possible partitions of $n$ points into $k$ groups — at most $k^n$ of them. Each partition induces a unique optimal $\mu$ (the per-cluster means). So there are only finitely many distinct $(C, \mu)$ pairs that can occur as the state of the algorithm after an update step. Since $J$ is strictly decreasing whenever the state changes, and since $J$ takes only finitely many values across these finitely many states, the algorithm must reach a state from which neither step can decrease $J$ further. At that point, no point changes cluster and no centroid moves. The algorithm has converged.

How fast? In practice K-means converges very quickly — typically 10 to 50 iterations on real data, regardless of how big $n$ is. There are pathological synthetic datasets where it takes exponentially many iterations, but you will essentially never encounter them in industrial work.

### 38.4.4 The catch: local minima

Convergence is guaranteed. **Convergence to a global minimum is not.** K-means is solving a non-convex problem, and what it actually finds is a *local* minimum of $J$. Depending on where the centroids were initialised, the algorithm can converge to wildly different local minima with wildly different values of $J$ — some of them genuinely terrible.

A toy example. Suppose you have a dataset of three obvious clusters arranged in a line:

```
  ●●●●            ●●●●            ●●●●
   A              B               C
```

Run K-means with $k = 3$ and initial centroids at the three correct locations: it converges in one step to the right answer.

Run it again with initial centroids placed (badly) like this:

```
  ●●●●            ●●●●            ●●●●
   A              B               C
    μ₁            μ₂                       μ₃
```

— $\mu_3$ is somewhere off to the right of cluster C. The assignment step puts all of C into $\mu_3$'s cluster, fine. But the assignment step *also* might put much of B into $\mu_2$'s cluster, and split A between $\mu_1$ and $\mu_2$. The update step then moves $\mu_1$ to roughly the centre of "left half of A", $\mu_2$ to "right half of A plus most of B", $\mu_3$ to "all of C". You can end up in a converged state where one of the natural clusters has been split across two centroids and another natural cluster has been merged with a neighbour — a stable, suboptimal local minimum.

This is not a hypothetical worry. Bad initialisation is the dominant practical failure mode of K-means. We solve it two ways: run K-means many times with different random initialisations and keep the best result (cheap), and use a smarter initialisation procedure (K-means++) that probabilistically gets you a good start. Both are standard. We cover K-means++ in 38.6.

---

## 38.5 A worked numerical example

Now let's actually run K-means by hand. Take six points in 2D:

| Point | $x_1$ | $x_2$ |
|------:|------:|------:|
| $p_1$ | 1     | 1     |
| $p_2$ | 1     | 2     |
| $p_3$ | 2     | 1     |
| $p_4$ | 8     | 8     |
| $p_5$ | 8     | 9     |
| $p_6$ | 9     | 8     |

Two obvious clusters: $\{p_1, p_2, p_3\}$ in the bottom-left, $\{p_4, p_5, p_6\}$ in the top-right.

We will run K-means with $k = 2$ and somewhat awkward initial centroids:
$\mu_1^{(0)} = (0, 0)$ and $\mu_2^{(0)} = (5, 5)$.

### Iteration 1

**Assignment step.** For each point, compute the squared distance to each centroid. (Using squared distance, not distance, because the comparison is the same and the arithmetic is easier.)

| Point | $\|p - \mu_1\|^2 = \|p - (0,0)\|^2$ | $\|p - \mu_2\|^2 = \|p - (5,5)\|^2$ | Assign to |
|------:|---:|---:|:---:|
| $p_1 = (1,1)$ | $1 + 1 = 2$ | $16 + 16 = 32$ | $C_1$ |
| $p_2 = (1,2)$ | $1 + 4 = 5$ | $16 + 9 = 25$ | $C_1$ |
| $p_3 = (2,1)$ | $4 + 1 = 5$ | $9 + 16 = 25$ | $C_1$ |
| $p_4 = (8,8)$ | $64 + 64 = 128$ | $9 + 9 = 18$ | $C_2$ |
| $p_5 = (8,9)$ | $64 + 81 = 145$ | $9 + 16 = 25$ | $C_2$ |
| $p_6 = (9,8)$ | $81 + 64 = 145$ | $16 + 9 = 25$ | $C_2$ |

So $C_1 = \{p_1, p_2, p_3\}$ and $C_2 = \{p_4, p_5, p_6\}$.

Compute $J$ at this state:
- Contributions from $C_1$: $2 + 5 + 5 = 12$.
- Contributions from $C_2$: $18 + 25 + 25 = 68$.
- Total: $J = 80$.

**Update step.** New centroids are the means of the assigned points.

$$ \mu_1^{(1)} = \left(\frac{1+1+2}{3}, \frac{1+2+1}{3}\right) = \left(\frac{4}{3}, \frac{4}{3}\right) \approx (1.33, 1.33) $$

$$ \mu_2^{(1)} = \left(\frac{8+8+9}{3}, \frac{8+9+8}{3}\right) = \left(\frac{25}{3}, \frac{25}{3}\right) \approx (8.33, 8.33) $$

Now recompute $J$ at the new centroids (assignments unchanged):

- $\|p_1 - \mu_1\|^2 = (1 - 1.33)^2 + (1 - 1.33)^2 \approx 0.11 + 0.11 = 0.22$
- $\|p_2 - \mu_1\|^2 = (1 - 1.33)^2 + (2 - 1.33)^2 \approx 0.11 + 0.45 = 0.56$
- $\|p_3 - \mu_1\|^2 = (2 - 1.33)^2 + (1 - 1.33)^2 \approx 0.45 + 0.11 = 0.56$
- $C_1$ contribution: $\approx 1.33$.

- $\|p_4 - \mu_2\|^2 = (8 - 8.33)^2 + (8 - 8.33)^2 \approx 0.22$
- $\|p_5 - \mu_2\|^2 = (8 - 8.33)^2 + (9 - 8.33)^2 \approx 0.56$
- $\|p_6 - \mu_2\|^2 = (9 - 8.33)^2 + (8 - 8.33)^2 \approx 0.56$
- $C_2$ contribution: $\approx 1.33$.

Total: $J \approx 2.67$. We went from $80$ to $2.67$ in one iteration.

### Iteration 2

**Assignment step.** Compute distances from each point to the new centroids:

| Point | $\|p - \mu_1^{(1)}\|^2$ | $\|p - \mu_2^{(1)}\|^2$ | Assign to |
|------:|---:|---:|:---:|
| $p_1 = (1,1)$ | $\approx 0.22$ | $\approx (7.33)^2 \cdot 2 = 107.4$ | $C_1$ |
| $p_2 = (1,2)$ | $\approx 0.56$ | $\approx 53.7 + 40.1 = 93.8$ | $C_1$ |
| $p_3 = (2,1)$ | $\approx 0.56$ | $\approx 40.1 + 53.7 = 93.8$ | $C_1$ |
| $p_4 = (8,8)$ | $\approx 89.0$ | $\approx 0.22$ | $C_2$ |
| $p_5 = (8,9)$ | $\approx 103.4$ | $\approx 0.56$ | $C_2$ |
| $p_6 = (9,8)$ | $\approx 103.4$ | $\approx 0.56$ | $C_2$ |

No point changed cluster. The algorithm has converged. The final clustering is $C_1 = \{p_1, p_2, p_3\}, C_2 = \{p_4, p_5, p_6\}$, with centroids $(1.33, 1.33)$ and $(8.33, 8.33)$, and $J \approx 2.67$.

Two iterations. That's K-means.

If you instead initialised with $\mu_1 = (1, 8)$ and $\mu_2 = (8, 1)$ — both centroids placed in the "wrong corners" — you would still converge, but to a *different* local optimum: one centroid ends up averaging $\{p_2, p_5\}$ and the other averaging $\{p_3, p_6\}$ (or some other diagonal split), depending on ties. The final $J$ would be much larger. This is the local-minimum trap, in miniature.

---

## 38.6 Initialisation: random vs. K-means++

Random initialisation — pick $k$ points uniformly at random from the dataset and use them as initial centroids — works often enough that it was the default for decades. But on hard datasets it gets stuck in bad local minima a non-trivial fraction of runs.

The fix that turned out to matter is **K-means++**, introduced by Arthur and Vassilvitskii in 2007. It is the default initialisation in scikit-learn's `KMeans` and in `pyspark.ml.clustering.KMeans` (the default for the `initMode` parameter is `k-means||`, the distributed version of K-means++). It is provably better — gives an $O(\log k)$ approximation to the global optimum in expectation — and in practice it just *works*. You almost never want to use plain random initialisation.

The K-means++ procedure:

> 1. Pick the first centroid $\mu_1$ uniformly at random from the data points.
> 2. For each remaining centroid $\mu_2, \mu_3, \ldots, \mu_k$:
>    - Compute, for each data point $x_i$, the squared distance $D(x_i)^2$ to the nearest *already-chosen* centroid.
>    - Sample the next centroid from the data, with probability proportional to $D(x_i)^2$.

So the first centroid is random, but subsequent centroids are *biased toward points that are far from already-chosen centroids*. Intuitively, this spreads the initial centroids out across the dataset, which is exactly what you want — you don't want all your initial centroids clumped on the same side of the data.

The "squared" in $D(x_i)^2$ is important. If we sampled with probability proportional to $D(x_i)$, we'd over-weight outliers. The squared weighting gives a bit more bias toward far-away points but not so much that single outliers dominate. The combinatorics that produce the $O(\log k)$ approximation guarantee use this exact weighting.

### 38.6.1 Why the squared-distance weighting works (intuition)

The idea: after we've placed some centroids, the regions of feature space they cover well are exactly the regions where $D(x)^2$ is small. The regions they cover badly are where $D(x)^2$ is large. A new centroid should go where coverage is bad. Sampling with probability proportional to $D(x)^2$ probabilistically does exactly that, while still allowing the occasional "exploration" of moderately-covered regions to avoid getting trapped by outliers.

### 38.6.2 The cost

K-means++ initialisation does $k$ passes over the data (one for each new centroid, to recompute $D$ values). For most datasets, the cost is tiny compared to the actual K-means iterations afterwards. For very large datasets, Spark uses a parallelised variant called *K-means||* (k-means parallel), which selects more candidates per pass to reduce the number of passes. Conceptually identical, just engineered for distributed compute.

### 38.6.3 N-restart in practice

Even with K-means++, a single run can still get unlucky. The standard practice is to run K-means several times with different random seeds and keep the result with the lowest $J$. Scikit-learn's `KMeans(n_init=10)` does ten restarts and returns the best. `n_init=1` is rarely a good idea; if you're tempted, you probably want `n_init='auto'` (the modern default — uses 1 for k-means++ initialisation, 10 for random — based on the assumption that k-means++ is usually good enough on its own).

---

## 38.7 Choosing $k$: the unsolved problem

So far we've assumed someone handed us $k$. They almost never do. Choosing $k$ is the central nuisance of K-means, and there is no clean answer — every method is a heuristic with its own assumptions and failure modes. We'll cover the three you'll see most often.

### 38.7.1 The elbow method

Plot $J$ (the within-cluster sum of squares) as a function of $k$, for $k = 1, 2, 3, \ldots, k_{\max}$, and pick the $k$ where the curve "bends" — the elbow.

The picture in your head:

```
  J (WCSS)
    |\
    | \
    |  \
    |   \
    |    \
    |     \
    |      ●  ← elbow
    |       \____
    |            \____
    |                 \____
    +─────────────────────────►  k
       1  2  3  4  5  6  7  8
```

The argument: as $k$ increases, $J$ monotonically decreases. (At the extreme, $k = n$ gives $J = 0$ — each point is its own cluster, distance zero to its "centroid", which is itself.) The marginal benefit of adding another cluster shrinks as $k$ grows. There's typically a regime where adding clusters substantially reduces $J$ (we're carving out genuine structure), followed by a regime where adding clusters barely helps (we're just subdividing existing clusters). The transition is the elbow.

In our six-point worked example, the curve would have an elbow at $k = 2$:

```
  J
   |
80 |●
   |
70 |
   |
60 |
   |
   |
20 |
   |
 3 |   ●
   |       ●__●__●__●
 0 +─────────────────► k
      1   2  3  4  5
```

Most of the variance is captured by the first two centroids. Going from $k=2$ to $k=3$ buys a little improvement; going from $k=3$ onward buys very little.

Strengths: simple, fast (you have to run K-means a few times anyway), intuitive.

Weaknesses: the elbow is often **not sharp**. On many real datasets the curve declines smoothly without a clear bend, and "where the elbow is" becomes a Rorschach test. Different people, looking at the same plot, will name different $k$'s. The elbow method is best as a first sniff, not a final answer.

### 38.7.2 Silhouette score

The **silhouette score** is a better-behaved diagnostic — it has a fixed range ($-1$ to $1$) and a clear interpretation. For each point $x_i$, define two quantities:

- $a(i)$ = the mean distance from $x_i$ to all other points in *its own* cluster.
- $b(i)$ = the minimum, over all *other* clusters, of the mean distance from $x_i$ to the points in that other cluster.

In words: $a(i)$ is "how cosy is this point inside its own cluster" (small is good); $b(i)$ is "how close is the nearest other cluster" (large is good — far from the next cluster means the current cluster is well-separated).

The **silhouette coefficient** of point $i$ is then

$$
s(i) = \frac{b(i) - a(i)}{\max(a(i), b(i))}
$$

The denominator normalises so that $s(i) \in [-1, 1]$. If $a(i) \ll b(i)$ — the point is much closer to its own cluster than to any other — then $s(i) \approx 1$. If $a(i) \approx b(i)$ — the point is on the boundary between two clusters — then $s(i) \approx 0$. If $a(i) > b(i)$ — the point is, on average, *closer* to a different cluster than to its own — then $s(i) < 0$, suggesting it has been assigned to the wrong cluster.

The **silhouette score** for a whole clustering is the average of $s(i)$ across all points:

$$
S = \frac{1}{n} \sum_{i=1}^n s(i)
$$

To choose $k$, run K-means for $k = 2, 3, 4, \ldots$ and pick the $k$ that maximises $S$. Typical good clusterings score $S > 0.5$; below $0.2$ the clusters are weak; negative average $S$ means the clustering is worse than random assignment.

Strengths: $S$ is normalised, interpretable, and unambiguous. Silhouette plots (per-cluster silhouette distributions) reveal which clusters are tight and which are loose, which is useful diagnostic information beyond a single number.

Weaknesses: silhouette is $O(n^2)$ in the number of points (it needs all pairwise distances within and between clusters). On very large datasets you compute it on a sample. Silhouette is biased toward convex, well-separated clusters; on data where K-means is the wrong algorithm in the first place, silhouette will not save you.

### 38.7.3 Gap statistic

The **gap statistic**, introduced by Tibshirani, Walther, and Hastie in 2001, compares the observed WCSS to the WCSS you'd expect from data with no real cluster structure.

Procedure:

1. Run K-means on the observed data for $k = 1, 2, \ldots, k_{\max}$. Record $W_k = \log(J_k)$.
2. Generate $B$ reference datasets of the same size and dimensionality as the observed data, where each reference dataset is drawn from a uniform distribution covering the same coordinate ranges (or from PCA-aligned uniform — the Tibshirani et al. paper is slightly more careful about how to construct the reference).
3. For each reference dataset, run K-means for $k = 1, \ldots, k_{\max}$ and record $W_k^{\text{ref}}$.
4. The **gap** at $k$ is

$$
\text{Gap}(k) = \mathbb{E}_{\text{ref}}[W_k^{\text{ref}}] - W_k
$$

A larger gap means the observed data has noticeably more cluster structure (lower $J$) than uniform reference data — so $k$ clusters captures real structure.

5. Pick the smallest $k$ such that $\text{Gap}(k) \geq \text{Gap}(k+1) - s_{k+1}$, where $s_{k+1}$ accounts for the standard deviation of the gap estimate. This is the "first $k$ where adding more clusters doesn't statistically help" rule.

Strengths: principled — it explicitly compares the data to a "no structure" null. Has a built-in stopping rule. Handles $k = 1$ (i.e., "there is no clustering structure") cleanly, which the other methods do not.

Weaknesses: computationally expensive ($B$ replicas of the K-means runs, typically $B = 10$ to $50$). Sensitive to how the reference distribution is constructed. Less standardised than silhouette.

### 38.7.4 Domain knowledge

Whatever the methods say, **domain knowledge often wins**. The marketing director from section 38.1 said five groups; she may be right. The right answer to "what $k$" is often "what $k$ makes the resulting clusters operationally useful?", which is a business question, not a math question. A clustering that scores marginally better on silhouette but produces clusters too small to staff a campaign for is worse than a clustering that scores slightly worse but produces actionable segments.

A practical workflow:

1. Compute the elbow plot and the silhouette score for $k = 2, 3, \ldots, 15$.
2. Note the $k$ values where the methods agree (or disagree).
3. Run K-means at the top candidates and *eyeball the clusters* — what's in each, how big is each, do they make sense to the domain expert?
4. Pick the $k$ that produces usable clusters.

Resist the temptation to treat $k$ as a hyperparameter to tune by cross-validation. There is no held-out test set for unsupervised clustering — there are no labels to score against.

---

## 38.8 Where K-means fails

K-means is a workhorse, but it has very specific assumptions baked into its objective, and when those assumptions are violated the algorithm produces confidently wrong clusters. Naming the failure modes is the difference between an engineer who reaches for K-means and one who knows when to reach for something else.

### 38.8.1 Non-spherical clusters

The objective minimises sum of squared *Euclidean* distances to a centroid. This means K-means implicitly assumes clusters are roughly spherical (isotropic) and roughly the same size. When clusters are elongated, K-means slices them up or merges them with neighbours.

```
    K-means on two elongated clusters:

   Truth                       K-means output (k=2)

   ●●●●●●●●●●●●               ●●●●●●●  ●●●●●●●
                    →
   ○○○○○○○○○○○○               ○○○○●●  ●●○○○○○○
```

The right-side picture is one of the canonical embarrassments of K-means. The algorithm sees the "natural" boundary as a vertical line (because Euclidean distance is symmetric), not as the horizontal separation between the two stripes. **Gaussian Mixture Models** (which model each cluster as a Gaussian with its own covariance matrix, allowing elongated shapes) and **DBSCAN** (which uses density rather than centroid-distance) handle this better. Both are out of scope for the ML Associate exam, but you should know they exist.

### 38.8.2 Clusters of very different sizes

K-means tends to split large clusters and merge small ones, because its objective summed over points is dominated by the big clusters. If you have one cluster of 10,000 points and one of 100 points, the algorithm will often slice the big one in two and lose the small one entirely.

### 38.8.3 Clusters of very different densities

Same root cause. Dense regions contribute more to $J$ than sparse regions, so the algorithm preferentially "spends" centroids on dense regions.

### 38.8.4 Sensitivity to outliers

A single outlier — a point much further from everything than the rest — drags the nearest centroid toward itself, because squared distance penalises it heavily. The centroid moves; the cluster boundary shifts; potentially other points get reassigned. K-means has *no robustness* to outliers. Detect and treat them before clustering.

(K-medoids, mentioned earlier, replaces "centroid = mean" with "medoid = the actual data point in the cluster that minimises total distance to others", which is more robust to outliers. It is slower and less common.)

### 38.8.5 The curse of dimensionality

In very high-dimensional spaces (hundreds or thousands of features), Euclidean distance becomes less and less informative — distances between *any* two random points become approximately equal. K-means doesn't break per se, but the clusters it finds may be largely meaningless. Pre-process with dimensionality reduction (Chapter 40's PCA, for instance, or Chapter 41's UMAP) before clustering high-dimensional data.

### 38.8.6 Scale dependence

Because the objective is the sum of squared *Euclidean* distances, features with larger numerical ranges dominate. If feature 1 is "age in years" (range 0-100) and feature 2 is "income in dollars" (range 0-1,000,000), the income axis contributes 10^8 times as much to every squared distance computation. The clustering will effectively be based on income, ignoring age.

**You must standardise the features before running K-means.** Subtract the mean and divide by the standard deviation per feature (i.e., StandardScaler from Chapter 26). This is not a "nice to have" — it is a correctness requirement. The single most common K-means bug in industrial code is forgetting to standardise.

### 38.8.7 Categorical features

K-means is defined for continuous features. Categorical features one-hot-encoded into K-means produce nonsense — the "centroid" of a one-hot column becomes a fractional value, which has no meaning. For mixed data, use K-prototypes (which extends K-means to categorical features) or first convert categoricals to embeddings.

---

## 38.9 Variants you should know exist

**MiniBatchKMeans.** Standard K-means scans the entire dataset on every iteration. For very large datasets, this is wasteful. MiniBatchKMeans samples a small batch (a few thousand points) at each iteration, updates centroids based on that batch, and continues. The result is approximately K-means with much lower per-iteration cost. Scikit-learn provides `MiniBatchKMeans`; the convergence is slightly worse than full K-means but the speed-up is enormous on large data.

**K-medians.** Replaces "centroid = mean" with "centroid = coordinate-wise median". More robust to outliers; minimises $\sum |x - \mu|$ (absolute distance) rather than squared distance.

**K-medoids (PAM, Partitioning Around Medoids).** Forces the centre to be an actual data point. Useful when you need centres to be interpretable as actual examples (e.g., representative customers). Slower; doesn't scale as well.

**Spherical K-means.** Replaces Euclidean distance with cosine distance. Useful for text data, where you usually care about angle (direction of the TF-IDF vector) rather than magnitude.

**Bisecting K-means.** Start with one cluster containing all data. Recursively split the largest cluster using 2-means. Builds a hierarchy similar to agglomerative clustering (Chapter 39) but top-down. Spark's MLlib offers this as `BisectingKMeans`.

None of these are interchangeable with K-means; each fits a slightly different objective. The point of knowing they exist is to know which one to reach for when standard K-means is the wrong tool.

---

## 38.10 Code

We've earned the right to write code. Three implementations, increasing in production-readiness.

### 38.10.1 K-means from scratch in NumPy

For pedagogy, here's the entire algorithm in 30 lines of NumPy. (Not for production — use scikit-learn — but reading this should feel like an extension of what we derived.)

```python
import numpy as np

def kmeans(X, k, max_iter=100, tol=1e-4, seed=0):
    rng = np.random.default_rng(seed)
    n, d = X.shape

    # K-means++ initialisation
    centroids = np.empty((k, d))
    centroids[0] = X[rng.integers(n)]
    for j in range(1, k):
        # squared distance from each point to nearest centroid so far
        d2 = ((X[:, None, :] - centroids[None, :j, :])**2).sum(axis=2).min(axis=1)
        probs = d2 / d2.sum()
        centroids[j] = X[rng.choice(n, p=probs)]

    for it in range(max_iter):
        # Assignment step
        d2 = ((X[:, None, :] - centroids[None, :, :])**2).sum(axis=2)
        labels = d2.argmin(axis=1)

        # Update step
        new_centroids = np.empty_like(centroids)
        for j in range(k):
            mask = labels == j
            if mask.any():
                new_centroids[j] = X[mask].mean(axis=0)
            else:
                # empty cluster — re-seed to a far-away point
                new_centroids[j] = X[d2.min(axis=1).argmax()]

        shift = np.linalg.norm(new_centroids - centroids)
        centroids = new_centroids
        if shift < tol:
            break

    inertia = ((X - centroids[labels])**2).sum()
    return labels, centroids, inertia
```

Every line corresponds to something we derived. The assignment step is `d2.argmin(axis=1)`. The update step is `X[mask].mean(axis=0)`. The K-means++ block samples with probability proportional to squared distance. The empty-cluster handling at the bottom is a small detail K-means implementations have to deal with — if all points are assigned away from a centroid, it has no mean to compute, so we re-seed.

### 38.10.2 scikit-learn

In practice you don't write the loop. You call:

```python
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# Always standardise first
X_scaled = StandardScaler().fit_transform(X)

km = KMeans(
    n_clusters=5,
    init='k-means++',   # default, but spelled out
    n_init=10,          # 10 random restarts; keep the best
    max_iter=300,
    tol=1e-4,
    random_state=42,
)
km.fit(X_scaled)

labels = km.labels_
centroids = km.cluster_centers_       # in standardised space!
inertia = km.inertia_                  # the J we minimised

# Predict cluster for new data
new_labels = km.predict(X_new_scaled)
```

Two things to note. First, `cluster_centers_` lives in the *scaled* space. If you want centroids in the original feature space (e.g., to interpret them), inverse-transform: `scaler.inverse_transform(km.cluster_centers_)`. Second, `predict` works on new data, so K-means is one of the few unsupervised models you can deploy: train once, predict on production traffic.

For very large datasets:

```python
from sklearn.cluster import MiniBatchKMeans

km = MiniBatchKMeans(n_clusters=5, batch_size=1024, n_init=10, random_state=42)
km.fit(X_scaled)
```

Same interface; underneath it processes the data in batches.

### 38.10.3 Choosing $k$ in code

```python
from sklearn.metrics import silhouette_score
import numpy as np

ks = range(2, 11)
inertias = []
silhouettes = []
for k in ks:
    km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(X_scaled)
    inertias.append(km.inertia_)
    # silhouette on a sample for large datasets
    sample_idx = np.random.choice(len(X_scaled), size=min(5000, len(X_scaled)), replace=False)
    silhouettes.append(silhouette_score(X_scaled[sample_idx], km.labels_[sample_idx]))

# Plot inertias for elbow; pick k that maximises silhouette
best_k = ks[int(np.argmax(silhouettes))]
```

### 38.10.4 `pyspark.ml`

The Spark version, for when your data doesn't fit on one machine:

```python
from pyspark.ml.clustering import KMeans
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml import Pipeline

assembler = VectorAssembler(inputCols=feature_cols, outputCol="features_raw")
scaler = StandardScaler(inputCol="features_raw", outputCol="features",
                        withMean=True, withStd=True)
kmeans = KMeans(featuresCol="features", k=5, seed=42, initMode="k-means||")

pipeline = Pipeline(stages=[assembler, scaler, kmeans])
model = pipeline.fit(df)

# Add cluster labels to the DataFrame
clustered = model.transform(df)
clustered.select("customer_id", "prediction").show()

# Inspect centroids
final_model = model.stages[-1]
centroids = final_model.clusterCenters()    # list of numpy arrays
print(f"WCSS (cost): {final_model.summary.trainingCost}")
```

A few `pyspark.ml`-specific notes that surprise newcomers, foreshadowing Chapter 65:

- The default `initMode` in Spark is `k-means||` (k-means parallel), not `k-means++`. They are equivalent in spirit but k-means|| is engineered for distributed execution.
- The "inertia" is called `trainingCost` in the model summary.
- The cluster labels appear in the `prediction` column of the transformed DataFrame, not a `labels_` attribute. (Spark ML uses a uniform "prediction" column convention across all its estimators.)
- `StandardScaler` in `pyspark.ml` defaults to `withStd=True, withMean=False`. You almost always want both `True` for K-means. Set them explicitly.

We will revisit `pyspark.ml.KMeans` in Chapter 65 alongside the rest of pyspark.ml's clustering API. For now, what matters is that the algorithm is the same; the API is different.

---

## 38.11 Summary

1. K-means is the workhorse clustering algorithm: given $n$ points and a target number of clusters $k$, find a partition into $k$ groups and a centroid per group such that within-cluster squared distance is minimised.

2. The objective is $J = \sum_j \sum_{x \in C_j} \|x - \mu_j\|^2$. The algorithm is Lloyd's alternating minimisation: assign each point to its nearest centroid (the **assignment step**), then move each centroid to the mean of its assigned points (the **update step**). Repeat until no point changes cluster.

3. Both steps are provably optimal *given the other half fixed*, so $J$ is monotonically non-increasing across iterations. Since $J \geq 0$ and there are only finitely many possible partitions, the algorithm converges in finitely many steps.

4. Convergence is to a *local* minimum, not the global minimum. Initialisation determines which local minimum. Random initialisation can land badly. **K-means++** picks the first centroid uniformly and subsequent centroids with probability proportional to squared distance from the already-chosen centroids — provably an $O(\log k)$ approximation to the global optimum in expectation.

5. Choosing $k$ has no clean answer. The **elbow method** plots $J$ versus $k$ and picks the bend, often subjectively. The **silhouette score** measures how cohesive each cluster is relative to the next-nearest cluster; pick $k$ maximising the average. The **gap statistic** compares observed $J$ to $J$ on uniform reference data. Domain knowledge often beats all three.

6. K-means assumes spherical, equal-size, equal-density clusters. It fails on elongated clusters, badly mismatched cluster sizes, very high dimensions, and outliers. It is sensitive to feature scaling — always standardise before clustering. For categorical features, use K-prototypes or embeddings.

7. Variants worth knowing exist: MiniBatchKMeans for scale, K-medians/K-medoids for robustness, spherical K-means for text, BisectingKMeans for top-down hierarchies.

8. In practice you reach for `sklearn.cluster.KMeans` or `pyspark.ml.clustering.KMeans`. Both default to K-means++ initialisation. Both will silently produce nonsense if you forget to scale.

---

## 38.12 What this builds on / where this returns

**Builds on:**
- *Chapter 12* — dot products, Euclidean distance, the geometric notion of "nearest". K-means is, at heart, repeated nearest-centroid computation.
- *Chapter 26* — standardisation. K-means requires standardised features; the chapter that derived StandardScaler set up the prerequisite.
- *Chapter 7* — covariance and variance. The WCSS objective is closely related to the within-group variance of an ANOVA decomposition; if you remember the analysis of variance from statistics, K-means is essentially "find the partition that minimises within-group variance".

**Returns:**
- *Chapter 39* — hierarchical clustering, an alternative that doesn't require you to pick $k$ up front and that produces a tree (dendrogram) of clusterings at every granularity.
- *Chapter 40* — PCA. PCA is often run *before* K-means in high-dimensional settings to mitigate the curse of dimensionality.
- *Chapter 65* — `pyspark.ml.KMeans` with the full pipeline pattern, the K-means|| initialisation in distributed detail, and CrossValidator gotchas for unsupervised models.

---

## 38.13 Exercises

Attempt all of these cold. Answers are in a fold at the bottom. For the by-hand ones, write out the arithmetic — you should be able to derive the centroid updates without consulting the chapter.

1. **The empty cluster.** In an iteration of K-means, suppose every point gets assigned to one of $k-1$ clusters, leaving one cluster empty. What happens at the update step? Name two reasonable strategies the algorithm could take.

2. **Convergence by counting.** We argued that K-means converges in finitely many steps because there are only finitely many distinct $(C, \mu)$ pairs. Roughly how many partitions of $n$ points into $k$ non-empty groups are there? Why does this number not show up in the practical run-time of K-means?

3. **By hand: one iteration.** Four 1D points: $1, 2, 9, 10$. Initial centroids: $\mu_1 = 0$, $\mu_2 = 5$. Run K-means with $k=2$ for one full iteration. Give the new assignments, new centroids, and the value of $J$ before and after.

4. **By hand: bad initialisation.** Same four points, but now $\mu_1 = 1$ and $\mu_2 = 10$. Compare the final clustering and $J$ to the result of exercise 3. Then try $\mu_1 = 9$ and $\mu_2 = 10$. What happens?

5. **The role of squaring.** Why does the K-means update step produce the **mean** of the cluster (rather than the median or the geometric median)? Trace it to the specific form of the objective.

6. **Scale invariance.** Suppose you have two features, $x_1 \in [0, 1]$ and $x_2 \in [0, 10000]$. Without standardisation, the K-means clustering is dominated by $x_2$. Explain why in one sentence using the form of the squared distance.

7. **Elbow ambiguity.** You run K-means for $k = 1, \ldots, 10$ and get $J = 800, 450, 250, 160, 120, 100, 88, 80, 75, 72$. Is there an elbow? Where?

8. **Silhouette interpretation.** A clustering has silhouette score $S = 0.05$. A colleague describes the clusters as "well-separated". Are they likely right? Why or why not?

9. **K-means++ probability.** Suppose the first centroid has been placed at the origin in 2D. Three candidate points exist at distances 1, 2, and 3 from the origin. What is the probability of each being chosen as the second centroid under K-means++?

10. **A non-spherical disaster.** You cluster customer features that form two elongated stripes: high-income/low-engagement and low-income/high-engagement. K-means gives you back two clusters split *vertically* (by income, ignoring engagement). Explain why, and name an algorithm you'd reach for instead.

11. **Standardisation pitfall.** You standardise your data, fit K-means, and want to interpret the centroids in the original units. How do you recover original-scale centroids from the standardised model and the scaler?

12. **Spark default.** Spark's `KMeans` has `initMode='k-means||'` and `n_init` not as a top-level parameter. Why might Spark not offer multiple restarts as cheaply as scikit-learn does?

<details>
<summary>Answers</summary>

1. The empty cluster has no points, so the mean is undefined ($0/0$). Two reasonable strategies: (a) re-initialise that centroid to a randomly chosen point — or, better, to the point with the highest distance to its currently-assigned centroid (a "rescue" strategy that pushes the empty centroid to an under-served region). (b) Reduce $k$ by one and continue with $k-1$ clusters. Most implementations choose (a). Scikit-learn re-initialises to the most distant point in the dataset.

2. The number of partitions of $n$ points into $k$ non-empty groups is the Stirling number of the second kind, $S(n, k)$, which grows roughly like $k^n / k!$ — astronomical for large $n$. This number does not show up in run-time because K-means converges in tens of iterations, not by enumerating partitions. The finite-partition argument is for *convergence guarantees*, not for run-time analysis.

3. Initial assignment: $1 \to \mu_2$ (distance to $\mu_1 = 0$ is 1; to $\mu_2 = 5$ is 4 — wait, 1 is closer to $\mu_1 = 0$ than to $\mu_2 = 5$. Let me redo.) Distances: $|1-0|=1, |1-5|=4$ → $C_1$. $|2-0|=2, |2-5|=3$ → $C_1$. $|9-0|=9, |9-5|=4$ → $C_2$. $|10-0|=10, |10-5|=5$ → $C_2$. So $C_1 = \{1, 2\}$, $C_2 = \{9, 10\}$. $J_{\text{before}} = 1^2 + 2^2 + 4^2 + 5^2 = 1+4+16+25 = 46$. Update: $\mu_1 = (1+2)/2 = 1.5$, $\mu_2 = (9+10)/2 = 9.5$. $J_{\text{after}} = (1-1.5)^2 + (2-1.5)^2 + (9-9.5)^2 + (10-9.5)^2 = 0.25 + 0.25 + 0.25 + 0.25 = 1.0$.

4. With $\mu_1 = 1, \mu_2 = 10$: same final clusters $\{1,2\}, \{9,10\}$, same $J=1.0$ (this initialisation is reasonable). With $\mu_1 = 9, \mu_2 = 10$: distances put $\{1, 2, 9\}$ closer to $\mu_1 = 9$ than to $\mu_2 = 10$ — assignment $C_1 = \{1, 2, 9\}, C_2 = \{10\}$. Update: $\mu_1 = 4, \mu_2 = 10$. Next iteration: distances $|1-4|=3, |1-10|=9 \to C_1$; $|2-4|=2, |2-10|=8 \to C_1$; $|9-4|=5, |9-10|=1 \to C_2$; $|10-4|=6, |10-10|=0 \to C_2$. Now $C_1 = \{1, 2\}, C_2 = \{9, 10\}$. We recover. K-means is somewhat self-correcting from this initialisation. But there exist worse initialisations (both centroids inside one cluster) where it converges to a bad split.

5. Because the objective is $\sum \|x - \mu\|^2$ — squared Euclidean distance. The gradient with respect to $\mu$ is linear in $\mu$, so setting it to zero gives a linear equation whose solution is the mean. With absolute distance ($\sum |x - \mu|$), the optimum is the median. With Mahalanobis or cosine distance, neither.

6. Squared distance is $\sum_d (x_d - \mu_d)^2$ — every feature contributes additively, with no normalisation by its scale. A feature ranging over $[0, 10000]$ contributes terms up to $10^8$; a feature over $[0,1]$ contributes terms up to $1$. The first dominates the sum by eight orders of magnitude, so the clustering is effectively one-dimensional in the larger-range feature.

7. The largest gap is from $k=1$ ($J=800$) to $k=2$ ($J=450$). Then $250, 160, 120, 100$ — decreasing meaningfully through $k=4$ or $k=5$. The curve flattens by $k=6$. Most analysts would call the elbow at $k = 4$ or $k = 5$. There is no canonical right answer — that's the point of the elbow method's weakness.

8. Probably not. A silhouette of $0.05$ means the average point is barely closer to its own cluster than to the next-nearest cluster. The clusters are not well-separated; they're heavily overlapping. A score above ~0.5 indicates reasonably separated clusters; above 0.7 is strong separation. $S = 0.05$ suggests either bad $k$ or that the data doesn't cluster well at all.

9. The probability is proportional to squared distance: $1^2 = 1$, $2^2 = 4$, $3^2 = 9$. Total: $14$. Probabilities: $1/14, 4/14, 9/14 \approx 0.071, 0.286, 0.643$. The far point is far more likely to be chosen than the near point, which is the spreading-out behaviour we want.

10. K-means with $k=2$ partitions space by a *perpendicular bisector* between the two centroids — a straight line. The natural separation between the two stripes is horizontal (income), so the algorithm picks the boundary that minimises squared distance from each point to its centroid, which is a vertical cut (since centroids end up at the two horizontal halves' means, perpendicular to the income axis). The algorithm cannot represent an elongated cluster boundary. Reach for **Gaussian Mixture Models** (which can model elongated clusters with full covariance matrices) or **DBSCAN** (which uses density rather than centroid distance).

11. If `scaler` is the StandardScaler used during preprocessing, recover original-scale centroids with `scaler.inverse_transform(km.cluster_centers_)`. The shape is `(k, d)` — one row per cluster centroid in the original feature units.

12. Multiple restarts on a single machine are cheap because each run is fast. In a distributed setting, every "run" incurs the same network shuffle cost. Running K-means 10 times distributed is 10x the cluster work. Spark's `k-means||` initialisation is designed to produce a single very good initial state with high probability, reducing the need for multiple restarts. You can run multiple restarts in Spark, but it's less idiomatic — and `k-means||` is good enough in practice that you rarely need to.

</details>
