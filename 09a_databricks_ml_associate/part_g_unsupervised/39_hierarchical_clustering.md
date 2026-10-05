# Chapter 39 — Hierarchical Clustering

> **Goal of this chapter:** to introduce the second major family of clustering algorithms, one that produces not a single partition but a *tree* of partitions at every level of granularity. By the end you should be able to: explain agglomerative (bottom-up) clustering as a sequence of merges; reproduce the dendrogram of a small dataset by hand; choose between single, complete, average, and Ward linkage based on what they do geometrically; cut a dendrogram to pick $k$ visually; characterise when hierarchical clustering is the right tool and when it isn't (mostly: not at scale); and run it in scipy and scikit-learn. We will be honest about the fact that hierarchical clustering is a small-data analyst's tool — Spark MLlib does not implement it, for principled reasons we'll explain.

---

## 39.1 The motivating problem

In the previous chapter we built K-means. It works, it is fast, it scales to millions of points. But it demands one thing up front, before you have ever looked at the data: *the number of clusters $k$.*

This is a problem. The marketing director from Chapter 38 may have said "I'm pretty sure five groups." She may also have said this with no real evidence — five is a guess, and her real question was "how many groups *are* there?" K-means cannot answer that question. It can only tell you "given that I told you $k=5$, here is the best 5-clustering I can find". To compare $k = 3$ to $k = 5$ to $k = 8$ you have to re-run the algorithm three separate times, then squint at elbow plots and silhouette scores, none of which gives a confident answer.

There is another path. Instead of committing to a fixed $k$, you build a *tree* — a hierarchy — that records, at every level, what cluster each point belongs to:

- At the **bottom** of the tree, every point is its own cluster. $n$ clusters of size one.
- At the **top** of the tree, all points belong to a single cluster of size $n$.
- In between, at each height, you have some partition of the data — fewer, larger clusters as you go up.

The tree is called a **dendrogram** (from Greek *dendron*, tree, and *gramma*, drawing). A picture:

```
height (merge distance)
    │
    │                                    ┌──────┐
    │                                    │      │
    │                              ┌─────┘      │
    │                              │            │
    │             ┌────────────────┘            │
    │             │                             │
    │             │                  ┌──────────┘
    │       ┌─────┘                  │
    │       │                ┌───────┘
    │   ┌───┘            ┌───┘
    │ ┌─┘            ┌───┘
    │ │ │   ┌──┐   ┌─┘ │
    │ │ │ ┌─┘  │   │   │
    │ │ │ │    │ ┌─┘   │
    └─┴─┴─┴────┴─┴─────┴───────────────────────────
       a b c    d e    f g       h i j  k l
```

Each leaf at the bottom is one data point. Each horizontal bar represents a merge: two clusters joined into one. The height of the bar tells you the distance at which they were joined. As you move up, more and more merges happen, eventually fusing everything into a single root cluster.

This is the central object of **hierarchical clustering**. Once you have the tree, you can pick *any* number of clusters you like by drawing a horizontal line through the dendrogram: every vertical line the cut intersects is one cluster. Want 3 clusters? Draw the line high. Want 8? Draw it lower. You don't pre-commit to $k$. You see the structure at every granularity at once.

For exploration, this is invaluable. For taxonomy ("what is the natural group structure of these biological species?"), it is exactly the right tool. For production segmentation of 100 million customers, it is the wrong tool — for reasons that will become clear.

---

## 39.2 Two flavours

Hierarchical clustering comes in two directions.

**Agglomerative (bottom-up).** Start with each point as its own singleton cluster. At each step, find the two closest clusters and merge them. Repeat until only one cluster remains. This is *by far* the more common variant, and the one every implementation defaults to. We'll spend almost all of this chapter on it.

**Divisive (top-down).** Start with all points in a single cluster. At each step, split the most "spread out" cluster into two. Repeat until every point is alone. Conceptually clean, computationally harder (deciding *how* to split a cluster optimally is itself NP-hard, so divisive methods rely on heuristics — usually running K-means with $k=2$ to do the splitting). Divisive methods are rare in practice. The one exception is Spark's `BisectingKMeans`, which is a top-down K-means-based hierarchy aimed at scaling — not really "hierarchical clustering" in the dendrogram sense, but the family resemblance is there.

For the rest of this chapter, "hierarchical clustering" means agglomerative unless otherwise noted.

---

## 39.3 The algorithm in five lines

Agglomerative hierarchical clustering, in its entire generality:

> 1. Start with $n$ clusters, each containing one point.
> 2. Compute the pairwise distance between every pair of clusters.
> 3. Find the two closest clusters and merge them into one. Record the merge (which two clusters, at what distance).
> 4. Update the distances between the new cluster and all remaining clusters.
> 5. Repeat steps 3-4 until one cluster remains.

That's it. The output is a sequence of merges; the dendrogram is just a visualisation of that sequence.

The two ambiguities in the recipe are step 2 and step 4: *what does "distance between two clusters" mean*? When two clusters each contain a single point, the answer is the obvious one — the distance between the two points. When clusters contain multiple points, we have a choice to make. That choice is called the **linkage criterion**, and different choices produce dramatically different clusterings.

---

## 39.4 Linkage criteria

We will define four. They differ in how they aggregate "distances from points in one cluster to points in another" into a single cluster-to-cluster distance.

Suppose we want the distance between cluster $A$ (containing points $a_1, a_2, \ldots$) and cluster $B$ (containing points $b_1, b_2, \ldots$).

### 39.4.1 Single linkage

$$
d_{\text{single}}(A, B) = \min_{a \in A, b \in B} \|a - b\|
$$

The distance between two clusters is the distance between their *closest* pair of points. If even one point in $A$ is close to one point in $B$, the clusters are considered close.

What this produces, geometrically: long, chain-like clusters. The "single nearest pair" semantics means that if two clusters have any thread connecting them, they merge. This is called the **chaining effect** and it is often a problem: a single bridge of points between two otherwise distinct groups will cause the groups to be merged.

```
   Cluster A: ● ● ● ● ● ● ● ● ● ● ● ● ● ●

   Single bridge: ● ● ●

   Cluster B:                    ● ● ● ● ● ● ● ● ● ●

   Single linkage sees A, bridge, B as one long cluster.
```

When single linkage is the right tool: when the natural clusters really are elongated, like spirals or curves. Single linkage is closely related to the *minimum spanning tree* of the points — both are computed by greedy nearest-neighbour merging. For most practical clustering problems, single linkage is not what you want.

### 39.4.2 Complete linkage

$$
d_{\text{complete}}(A, B) = \max_{a \in A, b \in B} \|a - b\|
$$

The distance between two clusters is the distance between their *furthest* pair of points. Two clusters are considered close only if even their most distant members are reasonably near.

What this produces, geometrically: compact, similar-diameter clusters. Complete linkage will not merge two clusters until the diameter of the combined cluster is small. This avoids the chaining effect — but it can also be overly conservative, refusing to merge clusters that "should" be merged because one outlier in each makes them seem far apart.

### 39.4.3 Average linkage

$$
d_{\text{average}}(A, B) = \frac{1}{|A| \cdot |B|} \sum_{a \in A, b \in B} \|a - b\|
$$

Average distance between all pairs across the two clusters. A reasonable compromise between single and complete — less prone to chaining than single, less conservative than complete.

(There are several variants: UPGMA — Unweighted Pair-Group Method with Arithmetic mean — is the version above; WPGMA, UPGMC, WPGMC are weighted variants. For most purposes UPGMA is what people mean by "average linkage".)

### 39.4.4 Ward linkage

This one is different. Ward doesn't define a cluster-to-cluster distance over points at all. Instead, it asks: *of all pairs of clusters I could merge next, which merge would cause the smallest increase in within-cluster variance?*

Formally, for a candidate merge of $A$ and $B$, define the *increase in WCSS* (within-cluster sum of squares, exactly the K-means objective from Chapter 38):

$$
\Delta J(A, B) = J(A \cup B) - J(A) - J(B)
$$

where $J(C) = \sum_{x \in C} \|x - \mu_C\|^2$ is the within-cluster sum of squares for cluster $C$ with centroid $\mu_C$. Ward linkage merges the pair with the smallest $\Delta J$ at each step.

A bit of algebra (which we'll skip — see the Lance-Williams algorithm if you want the full derivation) gives a closed form:

$$
\Delta J(A, B) = \frac{|A| \cdot |B|}{|A| + |B|} \|\mu_A - \mu_B\|^2
$$

This is the cost of the merge — the more the merge moves points away from their centroid, the higher the cost.

Ward linkage produces clusters that look very similar to K-means clusters: roughly spherical, roughly equal-sized. This makes sense — both algorithms are minimising within-cluster variance, just by different procedures. **Ward is the most common default in practice**, including in scikit-learn and scipy's defaults.

### 39.4.5 Picking a linkage

| Linkage | Geometric tendency | When to use |
|---------|-------------------|-------------|
| Single | Long chains | Elongated, curved clusters; minimum spanning tree applications |
| Complete | Compact, equal-diameter | Tight, well-separated clusters; sensitive to outliers |
| Average | Middle ground | Reasonable default for biology/genomics where the metric matters |
| Ward | K-means-like, spherical | Default for general numeric clustering, the most common choice |

If you don't have a strong reason to pick something else, use Ward. The clustering will look much like what K-means would have produced, but you get the dendrogram (and the freedom to choose $k$ later) for free.

---

## 39.5 A worked numerical example

Five points in 2D. We'll do agglomerative clustering with Ward linkage by hand.

| Point | $x_1$ | $x_2$ |
|------:|------:|------:|
| $p_1$ | 1 | 1 |
| $p_2$ | 2 | 1 |
| $p_3$ | 4 | 5 |
| $p_4$ | 5 | 5 |
| $p_5$ | 5 | 6 |

We'll need pairwise squared distances:

|   | $p_1$ | $p_2$ | $p_3$ | $p_4$ | $p_5$ |
|---|-----:|-----:|-----:|-----:|-----:|
| $p_1$ |  0 | 1 | 25 | 32 | 41 |
| $p_2$ |  1 | 0 | 20 | 25 | 34 |
| $p_3$ | 25 | 20 | 0 | 1 | 2 |
| $p_4$ | 32 | 25 | 1 | 0 | 1 |
| $p_5$ | 41 | 34 | 2 | 1 | 0 |

(For example, $\|p_1 - p_2\|^2 = (1-2)^2 + (1-1)^2 = 1$. $\|p_1 - p_3\|^2 = (1-4)^2 + (1-5)^2 = 9 + 16 = 25$.)

### Step 1: initial clusters

Each point is its own singleton: $\{p_1\}, \{p_2\}, \{p_3\}, \{p_4\}, \{p_5\}$.

### Step 2: first merge

For singletons, $\Delta J$ between two clusters $\{a\}, \{b\}$ simplifies. With $|A|=|B|=1$:

$$
\Delta J(\{a\}, \{b\}) = \frac{1 \cdot 1}{1 + 1} \|a - b\|^2 = \frac{1}{2} \|a - b\|^2
$$

So we just look for the pair with the smallest squared distance. The smallest entries in the table above (off-diagonal) are $1$, appearing at $(p_1, p_2)$, $(p_3, p_4)$, and $(p_4, p_5)$. We pick one — say $(p_1, p_2)$. (Tie-breaking is implementation-dependent. The dendrogram will still look the same in spirit.)

Merge cost: $\Delta J = 0.5 \cdot 1 = 0.5$. This becomes the height of the first horizontal bar in the dendrogram.

New cluster: $C_{12} = \{p_1, p_2\}$, with centroid $\mu_{12} = (1.5, 1)$.

### Step 3: second merge

Now the candidate clusters are $\{C_{12}, \{p_3\}, \{p_4\}, \{p_5\}\}$. We need $\Delta J$ for each pair. Among singleton-singleton pairs, the smallest distance is still $1$, between $(p_3, p_4)$ and between $(p_4, p_5)$. Pick $(p_3, p_4)$: $\Delta J = 0.5$.

Between $C_{12}$ and any singleton, the cost is larger (because $|A|=2, |B|=1$ gives a coefficient of $2/3$, and the centroid distances are larger). Sample: $\Delta J(C_{12}, \{p_3\}) = (2 \cdot 1)/(2+1) \cdot \|(1.5,1) - (4,5)\|^2 = (2/3)(6.25 + 16) = (2/3)(22.25) \approx 14.83$. Much bigger.

So the second merge is $(p_3, p_4)$ at height $0.5$. New cluster: $C_{34} = \{p_3, p_4\}$, centroid $\mu_{34} = (4.5, 5)$.

### Step 4: third merge

Candidates: $\{C_{12}, C_{34}, \{p_5\}\}$.

- $\Delta J(C_{34}, \{p_5\}) = (2 \cdot 1)/(2+1) \cdot \|(4.5,5) - (5,6)\|^2 = (2/3)(0.25 + 1) = (2/3)(1.25) \approx 0.833$.
- $\Delta J(C_{12}, \{p_5\}) = (2 \cdot 1)/(2+1) \cdot \|(1.5,1) - (5,6)\|^2 = (2/3)(12.25 + 25) = (2/3)(37.25) \approx 24.83$.
- $\Delta J(C_{12}, C_{34}) = (2 \cdot 2)/(2+2) \cdot \|(1.5,1) - (4.5,5)\|^2 = 1 \cdot (9 + 16) = 25$.

Smallest is $C_{34}$ merged with $\{p_5\}$, at height $\approx 0.833$. New cluster: $C_{345} = \{p_3, p_4, p_5\}$, centroid $\mu_{345} = ((4+5+5)/3, (5+5+6)/3) = (14/3, 16/3) \approx (4.67, 5.33)$.

### Step 5: fourth (final) merge

Last two clusters left: $C_{12}$ and $C_{345}$. $\Delta J(C_{12}, C_{345}) = (2 \cdot 3)/(2+3) \cdot \|\mu_{12} - \mu_{345}\|^2 = (6/5) \cdot ((1.5 - 4.67)^2 + (1 - 5.33)^2)$. Compute: $(1.5 - 4.67)^2 = 10.05$, $(1 - 5.33)^2 = 18.75$, sum $= 28.8$. So $\Delta J = (6/5)(28.8) = 34.56$.

Merge at height $34.56$. Final cluster: everything.

### The dendrogram

```
height
       │
 34.56 │       ┌───────────────┐
       │       │               │
       │       │               │
       │       │               │
       │       │               │
       │       │               │
       │       │               │
       │       │           ┌───┴───┐
   0.83│       │           │       │
       │       │           │       │
   0.5 │   ┌───┴───┐   ┌───┴───┐   │
       │   │       │   │       │   │
       │   │       │   │       │   │
       │   ●       ●   ●       ●   ●
           p1      p2  p3      p4  p5
```

(Heights drawn schematically.) The dendrogram shows: $p_1$ and $p_2$ fuse early (close, in their own bottom-left cluster). $p_3$ and $p_4$ fuse early (close, in the top-right cluster). $p_5$ joins them shortly after. The two top-right clusters then sit there until the very end, when they finally fuse with the bottom-left pair at height $34.56$ — reflecting that the two natural groups are quite far apart.

If we wanted **2 clusters**, we'd cut the dendrogram somewhere between heights $0.83$ and $34.56$ — say at height $5$ — yielding $\{p_1, p_2\}$ and $\{p_3, p_4, p_5\}$. Exactly the natural grouping.

If we wanted **3 clusters**, we'd cut between heights $0.5$ and $0.83$ — say at $0.7$ — yielding $\{p_1, p_2\}$, $\{p_3, p_4\}$, $\{p_5\}$. A reasonable finer division.

If we wanted **5 clusters**, we'd cut at height $0$ — every point its own cluster.

The dendrogram has shown us all of these at once. We didn't have to pre-commit to $k$.

---

## 39.6 Reading a dendrogram

The dendrogram contains a great deal of information beyond just "where to cut to get $k$ clusters". Some things to look for.

**Tall bars are informative.** A merge that happens at a much greater height than the merges below it indicates that the two sub-clusters being joined are *substantially different*. The bigger the height gap between consecutive merges, the more "natural" the cut above it. In our worked example, the gap between the third merge (height 0.83) and the fourth (height 34.56) is enormous, which is the dendrogram screaming "two clusters!" at you.

**The "biggest gap" heuristic.** A common informal procedure is to find the largest vertical gap between consecutive merge heights and cut just above the previous merge. This is the dendrogram equivalent of K-means' elbow method — and shares the same weakness: gaps are not always clear.

**Cluster sizes matter.** A merge at low height that produces a cluster with thousands of points is more meaningful than one at the same height producing a cluster of three. Most dendrogram plotters cut off the bottom (showing only the top, say, 50 merges) to keep the picture readable. Be aware: the lowest leaves represent thousands of individual points each.

**Outliers stand out.** A single point that doesn't fuse with anyone until very high heights is probably an outlier. Single linkage will pull such points into the rest of the tree gradually (via chaining); complete and Ward linkages will leave them dangling, which is often what you want.

---

## 39.7 The catch: it doesn't scale

Now the honest part. Agglomerative hierarchical clustering has a fundamental scaling problem.

**Memory.** You need the pairwise distance matrix, which is $O(n^2)$ in memory. For $n = 100{,}000$ that's a 10-billion-entry matrix — 80 GB at 8 bytes per entry. For $n = 1{,}000{,}000$ it's 8 TB. You cannot hold it.

**Time.** The naive algorithm is $O(n^3)$ — $n$ merges, each requiring an $O(n^2)$ search through the distance matrix for the closest pair. Smarter algorithms (using priority queues and the *nearest-neighbour chain* algorithm) bring it down to $O(n^2)$ time. This is still infeasible past about 10,000 points.

So hierarchical clustering is a **small-data tool**. For exploratory analysis on a dataset of a few thousand points — bioinformatics, marketing segmentation on a sample, taxonomy — it shines. For production clustering on millions of customers, it cannot be used.

This is why Spark MLlib does not implement hierarchical clustering. There is no obvious way to parallelise the algorithm: the merges are inherently sequential (each depends on the previous), and the $O(n^2)$ distance matrix doesn't shard cleanly. You can fudge it with approximations — sample the data, cluster the sample hierarchically, propagate the cluster structure to the full dataset — but the result is not really "hierarchical clustering of the full data" in any honest sense. For big data, you use K-means (or Bisecting K-means, which is the closest Spark-native approximation to a hierarchy).

This will not be a tested concept on the Databricks ML Associate exam — but it is the kind of thing that will arise in the exam's wording. If a question describes a big-data clustering problem and the options include hierarchical clustering, that option is wrong on architectural grounds.

---

## 39.8 Hierarchical vs. K-means

A side-by-side, since you now know both.

| Property | K-means | Hierarchical (agglomerative) |
|----------|---------|------------------------------|
| Output | A single partition into $k$ clusters | A dendrogram (tree of partitions) |
| Must pick $k$ in advance? | Yes | No — pick at cut time |
| Deterministic? | No (depends on initialisation) | Yes (given a tie-breaking rule) |
| Time complexity | $O(n \cdot k \cdot t)$, $t$ iterations | $O(n^2)$ best case, $O(n^3)$ naive |
| Memory complexity | $O(n + k)$ | $O(n^2)$ distance matrix |
| Scalability | Millions to billions | Up to ~10,000 points |
| Handles non-spherical clusters? | No (without modification) | Yes, with single or average linkage |
| Sensitive to feature scaling? | Yes | Yes |
| Sensitive to outliers? | Yes | Depends on linkage — Ward and complete are sensitive; single is *very* sensitive (chaining) |
| Spark support? | Yes (`pyspark.ml.clustering.KMeans`) | No |
| Typical use | Production segmentation | Small-data exploration, taxonomy |

The two algorithms are complementary, not competing. A common pattern in practice: run hierarchical on a *sample* of your data to explore the structure and pick $k$, then run K-means on the *full* data with that $k$ for production.

---

## 39.9 Other practical considerations

### 39.9.1 Distance metric

Most implementations let you choose a distance metric besides Euclidean. Manhattan ($L_1$) and cosine are the most common alternatives. Cosine distance is particularly useful for high-dimensional sparse data (text TF-IDF vectors, for instance) where you care about direction rather than magnitude.

A note: **Ward linkage assumes Euclidean distance**. The closed form for $\Delta J$ we derived only holds for the squared-Euclidean WCSS objective. Most implementations enforce this — scikit-learn's `AgglomerativeClustering(linkage='ward')` requires `metric='euclidean'`. With other linkages (single, complete, average) you are free to use any metric you like.

### 39.9.2 Feature scaling

Same caveat as K-means: features with larger ranges dominate the distance calculation. Standardise before clustering, unless you have a specific reason to weight features differently.

### 39.9.3 The Lance-Williams update formula

When you merge two clusters $A$ and $B$ into $A \cup B$, you need new cluster-to-cluster distances $d(A \cup B, C)$ for every remaining cluster $C$. The naive approach is to recompute from scratch. The **Lance-Williams formula** gives a recursive update in terms of the existing distances $d(A, C)$, $d(B, C)$, $d(A, B)$:

$$
d(A \cup B, C) = \alpha_A \cdot d(A, C) + \alpha_B \cdot d(B, C) + \beta \cdot d(A, B) + \gamma \cdot |d(A, C) - d(B, C)|
$$

The coefficients $\alpha_A, \alpha_B, \beta, \gamma$ depend on the linkage criterion. For Ward, $\alpha_A = (|A| + |C|) / (|A| + |B| + |C|)$, similarly for $\alpha_B$, with $\beta = -|C|/(|A|+|B|+|C|)$ and $\gamma = 0$. For single linkage, $\alpha_A = \alpha_B = 1/2, \beta = 0, \gamma = -1/2$.

You will not be tested on these coefficients. The point of mentioning Lance-Williams is that all the linkage criteria fall out of one parameterised family, which is what makes a single implementation able to support all of them. The neat unification was discovered in 1967.

### 39.9.4 Constrained clustering

Sometimes you want to enforce that certain points *must* be in the same cluster (or *must not* be). Hierarchical clustering with **connectivity constraints** lets you specify a graph (e.g., spatial adjacency) such that only neighbouring points can be merged. Scikit-learn supports this via the `connectivity` parameter. Useful for, e.g., image segmentation where you only want spatially contiguous regions.

---

## 39.10 Code

### 39.10.1 SciPy

SciPy's `linkage` is the canonical implementation. It returns a matrix describing the dendrogram, which you can plot with `dendrogram` and cut with `fcluster`.

```python
import numpy as np
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
import matplotlib.pyplot as plt

# Five points from our worked example
X = np.array([[1, 1], [2, 1], [4, 5], [5, 5], [5, 6]])

# Build the linkage matrix
Z = linkage(X, method='ward', metric='euclidean')
# Z is shape (n-1, 4): each row is [cluster_a, cluster_b, distance, n_in_merged]

print(Z)
# [[0.   1.   1.   2.  ]
#  [2.   3.   1.   2.  ]
#  [4.   6.   1.29 3.  ]
#  [5.   7.   8.27 5.  ]]

# Draw the dendrogram
plt.figure(figsize=(8, 5))
dendrogram(Z, labels=['p1', 'p2', 'p3', 'p4', 'p5'])
plt.ylabel('Ward distance')
plt.show()

# Cut to get exactly 2 clusters
labels_2 = fcluster(Z, t=2, criterion='maxclust')
print(labels_2)  # array([1, 1, 2, 2, 2], dtype=int32)

# Cut at a specific height
labels_h = fcluster(Z, t=5.0, criterion='distance')
print(labels_h)  # cluster IDs for the partition at height 5
```

(The exact numbers SciPy returns will differ slightly from our by-hand computation because SciPy uses the actual Ward distance — the square root of $\Delta J$ scaled — not the raw $\Delta J$ value. The clustering hierarchy is the same.)

### 39.10.2 scikit-learn

For when you just want labels and don't need the dendrogram:

```python
from sklearn.cluster import AgglomerativeClustering
from sklearn.preprocessing import StandardScaler

X_scaled = StandardScaler().fit_transform(X)

agg = AgglomerativeClustering(n_clusters=2, linkage='ward')
labels = agg.fit_predict(X_scaled)
```

A few things to know about scikit-learn's API:

- It does not return a dendrogram by default. If you want one, use SciPy or call scikit-learn with `distance_threshold=0, n_clusters=None` and inspect `agg.children_`, then construct the linkage matrix manually. SciPy is honestly easier.
- It does not implement a `predict()` method, only `fit_predict()`. Unlike K-means, you cannot use it to label new points after training. (Conceptually, "where would this new point go in the dendrogram?" requires extending the tree — possible in principle, but scikit-learn doesn't expose it.) **This is a key limitation** for production use: a hierarchical clustering is not directly deployable. You'd typically refit on each new data refresh, or use it to bootstrap a K-means model.
- For very small datasets, the `linkage='ward'` default is fine. For larger or non-spherical data, try `linkage='average'` or `'complete'`.

### 39.10.3 Visualising and choosing $k$

```python
from scipy.cluster.hierarchy import linkage, dendrogram
import numpy as np
import matplotlib.pyplot as plt

Z = linkage(X_scaled, method='ward')

# Truncate the dendrogram for legibility on large datasets
plt.figure(figsize=(12, 6))
dendrogram(
    Z,
    truncate_mode='lastp',  # show only the last p merges
    p=30,
    leaf_rotation=90,
    leaf_font_size=8,
    show_contracted=True,
)
plt.title('Dendrogram (last 30 merges)')
plt.xlabel('Sample index or cluster size')
plt.ylabel('Ward distance')
plt.axhline(y=4.0, color='red', linestyle='--')  # candidate cut height
plt.show()
```

A pragmatic workflow:

1. Run hierarchical clustering on a sample of your data (e.g., 5,000 points).
2. Inspect the dendrogram for a "natural" cut.
3. Validate by computing silhouette scores at the chosen $k$.
4. Use that $k$ to run K-means on the full dataset.

This sample-then-K-means pattern is how most teams use hierarchical clustering in practice on data that's too large for the algorithm to handle directly.

### 39.10.4 PySpark note

There is no `pyspark.ml.clustering.AgglomerativeClustering`. There is `BisectingKMeans`, which is a top-down K-means-based hierarchy — different from agglomerative clustering, but the closest big-data approximation to a hierarchical method that Spark provides:

```python
from pyspark.ml.clustering import BisectingKMeans

bkm = BisectingKMeans(k=5, featuresCol='features', seed=42)
model = bkm.fit(df)
clustered = model.transform(df)
```

`BisectingKMeans` produces a flat partition (like K-means), but the tree of splits is recorded internally. It scales because each "split" is a 2-means run, parallelisable per cluster. We mention it for completeness; if you need clustering on Spark, you reach for `KMeans` or `BisectingKMeans`, not agglomerative.

---

## 39.11 Summary

1. **Hierarchical clustering** builds a tree of partitions — at the bottom, every point is its own cluster; at the top, all points form a single cluster; at every height in between, you have some natural intermediate clustering.

2. **Agglomerative** (bottom-up) starts with singletons and merges the two closest clusters at each step until one remains. It is by far the more common variant. **Divisive** (top-down) goes the other direction and is rarely used.

3. The **dendrogram** is the visualisation of the sequence of merges. The y-axis is the distance at which each merge happened. Cutting the dendrogram at any height produces a particular clustering — visual choice of $k$, no need to pre-commit.

4. The choice of "distance between two clusters" is the **linkage criterion**. Single linkage (min) produces long chains. Complete linkage (max) produces compact clusters. Average linkage is in between. **Ward linkage** (minimum increase in within-cluster variance) is the most common default and produces K-means-like clusters.

5. By-hand procedure: compute pairwise distances; merge the closest pair; update distances; repeat. The **Lance-Williams formula** gives a parameterised update for all linkages.

6. **Doesn't scale.** $O(n^2)$ memory for the distance matrix, $O(n^2)$ to $O(n^3)$ time. Practical limit ~10,000 points. Spark does not provide it; there is no obvious parallelisation.

7. Compared to K-means: hierarchical doesn't require $k$, is deterministic, can handle non-spherical clusters with the right linkage — but is dramatically slower and not directly deployable on new data.

8. In practice, hierarchical is used for **exploration on small data or samples**, often to choose $k$ for a subsequent K-means run on the full data.

9. Always standardise features before clustering. Ward linkage requires Euclidean distance; other linkages support arbitrary metrics. For text, consider cosine distance.

---

## 39.12 What this builds on / where this returns

**Builds on:**
- *Chapter 38* — K-means, the WCSS objective, the assignment/update dichotomy. Ward linkage is essentially "K-means merging done bottom-up".
- *Chapter 12* — distance and the geometric definition of "nearest".
- *Chapter 26* — feature scaling. Hierarchical clustering is as scale-sensitive as K-means.

**Returns:**
- Hierarchical clustering is a small-data exploratory tool; it doesn't return deeply in later chapters. You'll see references to dendrograms in a few feature-importance contexts (some interpretability methods cluster features hierarchically), but the bulk of clustering for the rest of the book is K-means.
- *Chapter 65* — pyspark.ml clustering. We'll briefly touch on `BisectingKMeans` as Spark's "tree-shaped" clustering alternative.

---

## 39.13 Exercises

Attempt all of these cold. Some are by-hand arithmetic; others are conceptual.

1. **Linkage by example.** You have four 1D points: $1, 2, 8, 9$. Compute the pairwise distance matrix. Run agglomerative clustering with single linkage by hand. Then redo it with complete linkage. Do you get the same merge order?

2. **Ward by hand.** Three 1D points: $1, 2, 9$. Run Ward-linkage agglomerative clustering by hand. Give the merge sequence and heights.

3. **Single-linkage chaining.** Sketch a dataset where single linkage would produce a single long cluster but Ward linkage would correctly produce two clusters.

4. **Cut to $k$.** Given a dendrogram, you want exactly 4 clusters. How many merges (counting from the top) do you "undo"? Generalise: for $k$ clusters, how many merges from the top of the tree?

5. **Reading a dendrogram.** A dendrogram shows merges at heights $0.5, 0.6, 0.8, 1.0, 8.5, 10.0$. Where is the most natural cut? Why?

6. **Why no Spark implementation?** Spark MLlib has K-means but no agglomerative clustering. Give two reasons. What does Spark offer as the closest analogue?

7. **Predict on new data.** Why is scikit-learn's `AgglomerativeClustering` missing a `predict()` method when its `KMeans` has one? What does this imply for using hierarchical clustering in production?

8. **Distance metric and linkage.** You want to cluster TF-IDF vectors of news articles. You'd like to use cosine distance. Which linkages support cosine distance, and which don't?

9. **Outlier behaviour.** Single linkage and complete linkage behave very differently in the presence of outliers. Describe how each handles a single very distant point.

10. **Scaling.** Your dataset has 50,000 customers and 30 features. You want to do hierarchical clustering. Is this feasible? If not, propose a workaround.

11. **Comparing partitions.** You cut the dendrogram at height 1.0 to get 3 clusters. You then cut at height 2.0 to get 2 clusters. Can a point be in different "natural clusters" between the two cuts? Why or why not? (Hint: think about what the hierarchical structure guarantees.)

12. **Ward vs. K-means.** A dataset has two natural clusters that are roughly spherical and similar in size. You run K-means with $k=2$ and Ward-linkage hierarchical clustering cut at $k=2$. How similar would you expect the two outputs to be? What would make them differ?

<details>
<summary>Answers</summary>

1. Pairwise distances: |1−2|=1, |1−8|=7, |1−9|=8, |2−8|=6, |2−9|=7, |8−9|=1. **Single linkage**: closest pair is (1,2) or (8,9), both at distance 1; merge one, say (1,2). Now clusters {1,2}, {8}, {9}. Distances: d({1,2}, {8}) = min(|1-8|, |2-8|) = 6; d({1,2}, {9}) = min(|1-9|, |2-9|) = 7; d({8}, {9}) = 1. Smallest is (8,9): merge. Clusters: {1,2}, {8,9}. Distance d({1,2}, {8,9}) = min(|1-8|, |1-9|, |2-8|, |2-9|) = 6. Final merge at height 6. **Complete linkage**: same first two merges (since for singleton pairs single = complete). After merging (1,2) and (8,9): d({1,2}, {8,9}) = max(|1-8|, |1-9|, |2-8|, |2-9|) = 8. Final merge at height 8. Same *order*, different final heights — complete linkage merges the two natural clusters at a greater height, reflecting that their farthest points are farther apart.

2. Points: 1, 2, 9. First merge: (1, 2), Ward cost $= (1 \cdot 1)/(1+1) \cdot (1-2)^2 = 0.5$. New centroid 1.5. Now clusters {1,2}, {9}. Ward cost $= (2 \cdot 1)/(2+1) \cdot (1.5 - 9)^2 = (2/3)(56.25) = 37.5$. Final dendrogram has heights 0.5 and 37.5. The gap is enormous, confirming "{1,2} together, {9} alone" is the natural 2-cluster cut.

3. Two parallel rows of points connected by a thin bridge:
```
●●●●●●●●●●
        ●●
●●●●●●●●●●
```
Single linkage will chain through the bridge, producing one big cluster. Ward (and complete) would keep the two rows distinct because their centroids are well-separated, regardless of the bridge.

4. For $k$ clusters at the top of the tree, you undo $k-1$ merges from the top. Equivalently, you keep the *first* $n - k$ merges (counting from the bottom). For $k=4$ on a dataset of $n$ points: undo 3 merges from the top.

5. The most natural cut is between heights 1.0 and 8.5 — the gap from 1.0 to 8.5 is much larger than any other gap. This cut produces 2 clusters (because there are 6 merges total, and the gap is at merge 5 — so 6 − 4 = 2 clusters above the cut). The "biggest-gap" heuristic.

6. (a) The $O(n^2)$ distance matrix doesn't fit in memory for big data. (b) The merges are inherently sequential — each depends on the previous — so they don't parallelise across executors. Spark offers `BisectingKMeans`, a top-down K-means-based hierarchy that scales because each split is a parallelisable 2-means run.

7. Hierarchical clustering's output is a *tree*, not a function. To assign a new point you'd have to extend the tree, which means re-running agglomeration with the new point — not a constant-time prediction. K-means, in contrast, just computes the nearest centroid for any new point. **Implication for production**: hierarchical clustering is for analysis, not inference. To deploy, you typically refit on each batch, or use hierarchical to choose $k$ and then deploy K-means.

8. Single, complete, and average linkages support arbitrary distance metrics, including cosine. **Ward linkage does not** — it is mathematically tied to Euclidean distance (the closed form for $\Delta J$ requires squared Euclidean). To use cosine for text, use average or complete linkage.

9. **Single linkage** is very sensitive to outliers in a particular way: the outlier eventually joins the rest via a single thread, but the *order* of merges is largely unchanged until that point. The outlier just dangles until late. **Complete linkage** is also affected — a single distant point can prevent a cluster from merging with another, because the "max distance" between clusters is pulled up by the outlier. Ward is sensitive too, but more gracefully: outliers contribute to WCSS as part of their cluster's variance.

10. 50,000 points × 50,000 distances × 8 bytes = 20 GB just for the distance matrix. Feasible only on a very large machine, and the $O(n^2)$ to $O(n^3)$ runtime makes it impractical. **Workaround**: take a random sample of, say, 5,000 customers, do hierarchical clustering on the sample, identify the structure and the right $k$, then run K-means with that $k$ on the full 50,000 customers.

11. **No, a point cannot be in different "natural clusters" between cuts of the same dendrogram.** The hierarchy guarantees nesting: at any given height, each cluster is either entirely contained in or entirely outside any cluster at a greater height. So cutting higher can only *merge* clusters from a lower cut, never re-shuffle membership. If the dendrogram says points X and Y are in the same cluster at height 2.0, they were also in the same cluster at every height below where their merge happened.

12. For spherical, similar-size clusters, K-means with $k=2$ and Ward-linkage at $k=2$ should produce **very similar partitions** — possibly identical. Both are minimising within-cluster variance, just via different procedures. Differences would arise from: (a) K-means' sensitivity to initialisation (it might find a slightly different local optimum); (b) edge points equidistant from cluster boundaries getting flipped between the two methods; (c) Ward's greedy merge order producing slightly suboptimal partitions in edge cases (since each merge is locally optimal but the sequence might not be globally optimal).

</details>
