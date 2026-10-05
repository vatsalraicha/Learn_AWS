# Chapter 41 — t-SNE and UMAP (a Light Touch)

> **Goal of this chapter:** to introduce the two dominant non-linear dimensionality-reduction methods used for visualisation — t-SNE and UMAP — at a working level. Not a derivation from the ground up (that would be its own book), but enough that you can explain what they do, when to reach for them instead of PCA, what their hyperparameters mean, and — critically — what their visualisations *do not* tell you. Misreading a t-SNE plot is one of the most common interpretation errors in modern data analysis, and we will be specific about which features of these plots carry information and which features are artefacts. By the end you should be able to use t-SNE and UMAP responsibly, and just as importantly, push back when somebody else uses them irresponsibly.

---

## 41.1 The motivating problem

In Chapter 40 we derived PCA. PCA finds the linear subspace that maximises variance — it is, geometrically, the best orthogonal projection of the data into $k$ dimensions in a precise variance-preserving sense.

But PCA is *linear*. It works beautifully when the data's interesting structure can be captured by a linear projection. When the data lies on a non-linear manifold — a curved surface, a spiral, a sphere embedded in higher dimensions — PCA can't unwind it.

The canonical thought experiment: take a 2D dataset arranged on a Swiss roll — a flat 2D sheet rolled up into 3D space. The intrinsic dimensionality of the data is 2 (it's a sheet); the ambient dimensionality is 3 (it's been rolled into 3D). What you'd *want* a dimensionality-reduction method to do is unroll the sheet — recover the 2D structure. PCA cannot do this. Its three eigenvalues are all of similar magnitude (the roll occupies all three ambient dimensions roughly evenly), and projecting onto its top two eigenvectors gives you a *flattened* roll, not an unrolled one.

```
   Swiss roll in 3D:                    What PCA gives you:

      ╔══════════════╗                   (the data, flattened
     ╔                ╗                   from the side — the
    ║   ╔═════════╗   ║                   roll is still rolled,
    ║  ╔           ╗  ║                   just viewed end-on)
    ║  ║   ╔════   ║  ║         vs.
    ║  ║   ║       ║  ║                   ●●●●●●●●●●●
    ║  ║   ╚════   ║  ║                   ●●●●●●●●●●●
    ║  ╚           ╝  ║                   ●●●●●●●●●●●
    ║   ╚═════════╝   ║
     ╚                ╝                   (you wanted: an unrolled
      ╚══════════════╝                     2D rectangle)
```

For the kinds of high-dimensional datasets that come up in real ML work — embeddings from neural networks, gene-expression profiles, document-vector representations — the linear-projection assumption of PCA is often violated. The most informative 2D view of an embedding space is *not* a linear projection.

Enter t-SNE and UMAP. Both are non-linear methods, designed explicitly for **visualisation** of high-dimensional data in 2 or 3 dimensions. They do something fundamentally different from PCA: instead of preserving global geometry (variance, distances), they preserve **local neighbourhood structure**. The result is plots that tend to reveal cluster structure dramatically — but at the cost of distorting global relationships in ways we'll be careful about.

This chapter is shorter and lighter than the PCA chapter. We will not derive t-SNE or UMAP from scratch — their derivations involve enough probability theory and optimisation tricks to fill their own chapters, and you will rarely need to derive them from scratch. What you need is to understand what they're optimising, what their outputs mean, and where the standard interpretation gotchas live.

---

## 41.2 t-SNE: t-distributed Stochastic Neighbour Embedding

t-SNE was introduced by van der Maaten and Hinton in 2008 as a refinement of Hinton and Roweis's earlier Stochastic Neighbour Embedding (SNE). It has become the de facto standard visualisation tool for high-dimensional data in the deep-learning era.

### 41.2.1 The core idea

t-SNE asks: given pairwise similarities of points in the original high-dimensional space, find a configuration of points in 2D (or 3D) that *reproduces those similarities as closely as possible*.

There are two halves to that statement. We need to define similarities in the high-dimensional space, and we need to define similarities in the low-dimensional space, and then we need an objective function that measures how closely they match.

### 41.2.2 High-dimensional similarities

For two points $x_i, x_j$ in high-dimensional space, define a conditional probability that point $j$ is "a neighbour" of point $i$ as a Gaussian over their distance:

$$
p_{j|i} = \frac{\exp(-\|x_i - x_j\|^2 / 2 \sigma_i^2)}{\sum_{k \neq i} \exp(-\|x_i - x_k\|^2 / 2 \sigma_i^2)}
$$

This is a softmax over distances. Points close to $x_i$ get high probability; far points get low probability. The bandwidth $\sigma_i$ is set adaptively per point so that the effective number of neighbours equals a user-chosen hyperparameter called the **perplexity** (more on this in a moment). The joint probability is then symmetrised: $p_{ij} = (p_{j|i} + p_{i|j}) / (2n)$.

### 41.2.3 Low-dimensional similarities — the t-distribution trick

In the low-dimensional space (where we're trying to place the points), define an analogous probability — but using a **Student's t-distribution with one degree of freedom** (a Cauchy distribution) instead of a Gaussian:

$$
q_{ij} = \frac{(1 + \|y_i - y_j\|^2)^{-1}}{\sum_{k \neq \ell} (1 + \|y_k - y_\ell\|^2)^{-1}}
$$

Why the t-distribution? Because of the **crowding problem**. In high dimensions, the "volume" available for far-away points is enormous (the volume of a sphere grows as $r^d$). When you compress to 2D, that volume collapses dramatically — there isn't room for all the moderately-distant high-dimensional neighbours of a point to also be moderately distant in 2D. Something has to give. With a Gaussian in low-dim, the algorithm tries to put moderately-distant high-dim points at moderate distances in 2D, and the resulting configurations are forced to crush distant points into a single blob.

The t-distribution has **heavier tails** than a Gaussian. This means in 2D, points that are moderately far in high-dimensional space are *allowed* to be very far in 2D without incurring much cost. The algorithm can put dissimilar points way out at the edges of the plot — separating clusters dramatically — while still preserving local neighbourhood structure.

This is the trick that makes t-SNE work. It is also the trick that makes t-SNE *systematically distort global structure*. The price of getting clean cluster separation is that distances between clusters in the t-SNE plot have no quantitative meaning.

### 41.2.4 The objective: KL divergence

t-SNE places the low-dim points by minimising the **Kullback-Leibler divergence** between the high-dim and low-dim distributions:

$$
\text{KL}(P \| Q) = \sum_{i \neq j} p_{ij} \log \frac{p_{ij}}{q_{ij}}
$$

KL divergence is asymmetric. The form above penalises *underestimating* $q_{ij}$ when $p_{ij}$ is high — that is, having low similarity in 2D when there was high similarity in high-dim. This means t-SNE works hard to preserve *local* structure (high-similarity neighbours stay neighbours) and is more relaxed about global structure (low-similarity pairs in high-dim can be placed almost arbitrarily in 2D).

Optimisation is by gradient descent. The full algorithm is iterative; on most modern implementations using Barnes-Hut approximations, it runs in $O(n \log n)$ per iteration rather than the naive $O(n^2)$.

### 41.2.5 Perplexity

The main hyperparameter is **perplexity**. Mathematically it controls the bandwidth $\sigma_i$ — specifically, $\sigma_i$ is chosen for each point so that the effective number of neighbours (a quantity called the perplexity of the distribution $p_{\cdot|i}$) equals the user-specified value.

Intuitively, perplexity is *how many neighbours to consider* when deciding what's close to each point. Typical values are 5 to 50. Low perplexity emphasises very local structure (small clusters within clusters); high perplexity emphasises broader structure (larger groupings). 30 is a common default.

t-SNE's output is **sensitive** to perplexity. The same dataset with perplexity 5 and perplexity 50 can produce very different visualisations. The standard advice is to try several values and look for features that are stable across them — those are the "real" structures in the data, as opposed to artefacts of any single perplexity choice.

### 41.2.6 What t-SNE plots can and cannot tell you

This is the most important section in the chapter. Even sophisticated practitioners regularly over-interpret t-SNE plots.

**What t-SNE plots tell you:**

- **Which points are in similar local neighbourhoods in the high-dimensional space.** If two points are nearby in the t-SNE plot, they are likely also nearby in high-dim. Cluster membership is generally informative.
- **Whether clusters are distinct.** If t-SNE produces several clearly separated blobs, that strongly suggests the data has cluster structure. The opposite is also informative — if t-SNE produces one giant blob, the data may not cluster cleanly.

**What t-SNE plots do not tell you:**

- **The sizes of clusters.** The "spread" of points within a cluster in the t-SNE plot is largely determined by the algorithm's optimisation dynamics, not by the actual intra-cluster variance. A dense cluster in high-dim and a loose cluster in high-dim can produce visually similar-sized blobs.
- **The distances between clusters.** The space between clusters in the plot has no quantitative meaning. Two clusters appearing close together in t-SNE may be far apart in high-dim, or vice versa. This is a direct consequence of the heavy-tail trick — far points are deliberately allowed to be placed at arbitrary distances.
- **The shapes of clusters.** t-SNE has a tendency to produce roughly round blobs regardless of the actual cluster geometry. If you see a curved cluster in a t-SNE plot, it may or may not reflect curved structure in the data.

The single most common mistake: looking at a t-SNE plot, seeing two well-separated clusters, and concluding "they're far apart in the data". Maybe. Maybe not.

### 41.2.7 Other gotchas

**Stochastic.** t-SNE includes random initialisation; different runs of the same algorithm on the same data give different visualisations (the same overall structure, but rotated, reflected, with different absolute positions). Set a `random_state` for reproducibility.

**Not a feature engineering tool.** t-SNE does not have a "transform" operation for new data. The output coordinates only exist for the points that were in the training set; to "project" a new point you would have to rerun the optimisation, which is not what users expect. **t-SNE is for visualisation only.** Do not use it as a preprocessing step for downstream supervised models.

**Slow.** Naive t-SNE is $O(n^2)$ per iteration, with hundreds of iterations to converge. Barnes-Hut t-SNE is $O(n \log n)$ per iteration. Even so, for $n > 100{,}000$ or so it becomes slow. The standard workflow on large datasets is to **subsample** to 10,000-50,000 points before running t-SNE.

**Cluster ordering doesn't mean anything.** The fact that cluster A is "to the left of" cluster B in a t-SNE plot is meaningless. Different runs will reorder them.

---

## 41.3 UMAP: Uniform Manifold Approximation and Projection

UMAP, introduced by McInnes, Healy, and Melville in 2018, is the newer challenger to t-SNE. In a few years it has displaced t-SNE in many workflows — partly because it's faster, partly because it preserves more global structure, and partly because, unlike t-SNE, it has a `transform` operation for new data.

### 41.3.1 The core idea

UMAP's mathematical foundation is more involved than t-SNE's — it comes from Riemannian geometry and algebraic topology, specifically the theory of simplicial sets and fuzzy topological structures. We will not go there. What you need to know:

UMAP constructs a **weighted graph** of the high-dimensional data, where each point is connected to its $k$ nearest neighbours with weights that capture local distances. It then constructs a similar graph in low-dim and optimises the layout to make the two graphs as similar as possible (using a cross-entropy-like loss).

The optimisation does not use the same KL divergence as t-SNE. The result is that UMAP:

- Runs faster, often dramatically so. UMAP on 100,000 points takes minutes; t-SNE takes an hour or more.
- Preserves more global structure than t-SNE. Inter-cluster distances in UMAP have *more* meaning than in t-SNE, though they are still not directly comparable to high-dim distances.
- Provides a `transform` method: you can apply a trained UMAP model to new data, projecting it into the same 2D space as the training data. This means UMAP, unlike t-SNE, can be used as a feature engineering preprocessor for downstream models.

### 41.3.2 Hyperparameters

UMAP has two main hyperparameters:

- **`n_neighbors`** (default 15) — analogous to t-SNE's perplexity. How many neighbours to consider when constructing the local graph. Higher values capture broader structure; lower values capture finer structure.
- **`min_dist`** (default 0.1) — how tightly UMAP packs points in low-dim. Lower values produce tighter clusters; higher values produce more spread-out visualisations.

Like t-SNE, UMAP's output depends on hyperparameters and on random initialisation. Try several settings; trust features that are stable across them.

### 41.3.3 Same gotchas, with one less

UMAP shares most of t-SNE's interpretation caveats:

- Cluster sizes in the plot are not directly meaningful.
- Inter-cluster distances are *more* meaningful than in t-SNE but are still distorted.
- Cluster shapes are partly an artefact of the algorithm.
- It's stochastic.

But UMAP can be used as a transform — meaning new data can be projected into the same space — which makes it usable as a preprocessor for downstream models, not just a visualisation tool. This is a real practical difference.

---

## 41.4 When to use which

A practical rule of thumb, in decreasing order of common applicability:

**PCA when:**
- You're doing downstream linear or near-linear modelling.
- You need the dimensionality reduction to be interpretable (each new feature is a linear combination of original features).
- You want speed and don't want to tune hyperparameters.
- The intrinsic structure of your data is well-approximated by a linear subspace.
- You'll deploy the reducer on new data (PCA is fully transformable).

**t-SNE when:**
- You want to visualise high-dimensional data to look for cluster structure.
- You don't need to transform new data.
- Your dataset is small to medium (under 50,000 points, or you'll subsample).
- You're producing a one-off plot for a paper or a report, not a deployment pipeline.

**UMAP when:**
- You want to visualise high-dimensional data and t-SNE is too slow.
- You want a transform method to apply to new data.
- You want better preservation of global structure than t-SNE offers.
- You're feeding the reduced representation into a downstream model (though benchmark this carefully — UMAP's preservation of structure is empirical, not provable).

For the Databricks ML Associate exam — which leans toward classical, tabular ML — PCA is by far the most likely to be tested. t-SNE and UMAP are worth knowing about, but they are unlikely to come up in detail. The reason this chapter is included is that they are *industry-standard* tools you'll encounter in any modern ML team's analysis workflows, even if they're not on the syllabus.

---

## 41.5 A conceptual worked example: MNIST digits

Imagine the MNIST handwritten-digit dataset. 70,000 images, each $28 \times 28 = 784$ pixels. Each image is labelled with its digit, 0 through 9.

If you PCA this dataset down to 2 dimensions, you get a plot where the digits are somewhat-but-not-cleanly separated. There's overlap; some digits (e.g., 4 and 9) blend into each other. PCA finds linear combinations of pixels that capture variance, but variance is dominated by global intensity and ink-coverage patterns, not by the subtler structural differences between digits.

If you run t-SNE on the same data (or its 50-dim PCA-reduced form, which is what most practitioners do — PCA to 50, then t-SNE to 2 — for speed), you get a famous visualisation: ten clean, well-separated blobs, one per digit. The cluster structure leaps off the page.

Here is the careful interpretation:

- The **fact that there are ten clusters** is real. The digits are 10 distinct classes; the algorithm is recovering that.
- The **identity of which cluster is which digit** is recoverable by looking at a few labelled points in each cluster.
- The **separation between clusters** is *not* directly meaningful — t-SNE has likely exaggerated it. Two digit classes that are visually similar in high-dim (e.g., 4 and 9) may appear closer in the t-SNE plot than two unrelated classes, but the distances are not quantitative.
- The **shape of each cluster** (its size, its elongation, its position in the plot) is mostly an artefact of the algorithm.

A common over-interpretation: "Look, the 4 and 9 clusters are right next to each other — they must be confusable!" Maybe. Or maybe t-SNE just happened to place them adjacently. Verify by looking at a confusion matrix from a classifier trained on the actual data; do not infer from the t-SNE plot alone.

UMAP on MNIST gives a qualitatively similar picture — ten clusters, separated — but the inter-cluster distances are slightly more meaningful (UMAP tries harder to preserve global structure), and the whole thing runs in 30 seconds rather than 30 minutes.

---

## 41.6 PySpark and big-data note

Neither t-SNE nor UMAP is in `pyspark.ml`. There are technical reasons for this:

- Both algorithms have an inherent $O(n)$ memory requirement for the low-dim coordinates (you have to hold $n$ low-dim points and update them iteratively). On distributed clusters, this is awkward.
- Both algorithms have iterative dependencies that don't parallelise cleanly. The optimisation at each step depends on the previous step's full embedding.
- The visualisation use case — produce a 2D plot — fundamentally doesn't scale. You can't usefully plot a million points.

The standard workflow on big data:

1. Use Spark to subsample (or aggregate) your data down to 10,000-50,000 representative points.
2. Pull the subsample onto a single machine (one driver, no executors needed).
3. Run t-SNE or UMAP locally.
4. Plot.

For embeddings — which is most of what people use t-SNE and UMAP for in modern ML — this is fine. The point of the visualisation is to look at the structure, not to embed every example in your dataset.

For the ML Associate exam: if a question describes using t-SNE or UMAP on a distributed Spark DataFrame directly, that's wrong. They are single-machine tools.

---

## 41.7 Code

### 41.7.1 t-SNE in scikit-learn

```python
import numpy as np
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt

# Standard pipeline: standardise, PCA to 50, then t-SNE
X_scaled = StandardScaler().fit_transform(X)
X_pca = PCA(n_components=50).fit_transform(X_scaled)

tsne = TSNE(
    n_components=2,
    perplexity=30,
    n_iter=1000,
    random_state=42,
    init='pca',         # initialise with PCA — more reproducible, often better
)
X_tsne = tsne.fit_transform(X_pca)

# Plot
plt.figure(figsize=(10, 8))
scatter = plt.scatter(X_tsne[:, 0], X_tsne[:, 1], c=labels, s=2, alpha=0.7, cmap='tab10')
plt.colorbar(scatter)
plt.title('t-SNE visualization')
plt.show()
```

A few things in this code worth understanding:

- **PCA to 50 first.** This is the standard preprocessing for t-SNE. Doing t-SNE directly on the original 784-dim (or higher) data is slow and often gives worse results — the PCA step both speeds up t-SNE and acts as a noise filter, since PCA's tail components are mostly noise.
- **`init='pca'`** instead of the default random initialisation. This makes the result more reproducible across runs and often produces better embeddings.
- **`perplexity=30`** is the most common default. Try `perplexity=10` and `perplexity=50` for the same data and compare — features that appear in all three are real; features that appear in only one are artefacts.

### 41.7.2 UMAP

UMAP is in a separate package, `umap-learn` (PyPI name: `umap-learn`, imported as `umap`):

```python
import umap

reducer = umap.UMAP(
    n_components=2,
    n_neighbors=15,
    min_dist=0.1,
    random_state=42,
)
X_umap = reducer.fit_transform(X_pca)

# UMAP supports transform on new data
X_new_umap = reducer.transform(X_new_pca)

plt.figure(figsize=(10, 8))
plt.scatter(X_umap[:, 0], X_umap[:, 1], c=labels, s=2, alpha=0.7, cmap='tab10')
plt.title('UMAP visualization')
plt.show()
```

The interface is intentionally similar to scikit-learn's. You can drop it into a `Pipeline`. You can use the resulting reducer for new data via `transform`, which is the main practical advantage over t-SNE.

### 41.7.3 Comparing PCA, t-SNE, UMAP side-by-side

A useful exercise on any new dataset is to run all three and look at them together:

```python
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import umap

X_pca50 = PCA(n_components=50).fit_transform(X_scaled)  # for t-SNE/UMAP speed

embeddings = {
    'PCA (2 components)': PCA(n_components=2).fit_transform(X_scaled),
    't-SNE': TSNE(n_components=2, perplexity=30, random_state=42).fit_transform(X_pca50),
    'UMAP': umap.UMAP(n_components=2, random_state=42).fit_transform(X_pca50),
}

fig, axes = plt.subplots(1, 3, figsize=(18, 6))
for ax, (name, X_emb) in zip(axes, embeddings.items()):
    ax.scatter(X_emb[:, 0], X_emb[:, 1], c=labels, s=2, alpha=0.7, cmap='tab10')
    ax.set_title(name)
plt.show()
```

Three views of the same data. PCA often shows blurry overlap; t-SNE and UMAP often show tight, well-separated clusters. The story they tell is different, and *each tells a different aspect of the truth*. PCA is honest about the limits of linear structure; t-SNE and UMAP reveal cluster structure at the cost of distorting global geometry.

---

## 41.8 Summary

1. **PCA is linear; t-SNE and UMAP are non-linear.** When data lies on a non-linear manifold (a spiral, a Swiss roll, an embedding from a neural network), PCA cannot recover the structure but t-SNE and UMAP can — for *visualisation purposes*.

2. **t-SNE** defines pairwise similarities in high-dim using Gaussians and in low-dim using a heavy-tailed t-distribution, then minimises the KL divergence between them. The heavy tail prevents the crowding problem and produces dramatic cluster separation.

3. **Perplexity** is t-SNE's main hyperparameter — roughly the effective number of neighbours considered, typically 5 to 50. Output is sensitive to it. Try several values.

4. **t-SNE's main limitations:** stochastic (different runs give different layouts); slow on large data ($O(n \log n)$ with Barnes-Hut, but the constant is large); **not transformable** to new data (you cannot apply a trained t-SNE to new examples without retraining); cluster sizes and inter-cluster distances are *not directly meaningful*.

5. **UMAP** is the newer alternative, based on Riemannian geometry. Hyperparameters: `n_neighbors` (15 default) and `min_dist` (0.1 default). Faster than t-SNE, preserves more global structure, and **supports `transform()`** on new data — usable as a preprocessor for downstream models.

6. **What these plots *do* tell you:** local neighbourhood structure, presence/absence of cluster structure, rough class separability.

7. **What they *do not* tell you:** cluster sizes (the spread within a cluster in the plot is largely an algorithm artefact); inter-cluster distances (especially in t-SNE — the heavy-tail trick deliberately exaggerates them); cluster shapes; the orientation of clusters relative to each other.

8. **Standard practice on real data:** PCA first to 50 dimensions (for speed and noise filtering), then t-SNE or UMAP to 2 (for visualisation). Subsample to ~10,000-50,000 points if your dataset is larger.

9. **No Spark support.** Neither t-SNE nor UMAP is in `pyspark.ml`. They are single-machine tools by nature. For big data, subsample first.

10. **For deploy-able dimension reduction**, PCA is still the right choice. For *just looking at* high-dimensional data, t-SNE and UMAP are dominant.

---

## 41.9 What this builds on / where this returns

**Builds on:**
- *Chapter 40* — PCA. The motivating problem for t-SNE/UMAP is exactly PCA's limitation: linear projections can't unwind non-linear manifolds.
- *Chapter 12* — distances and the geometric notion of neighbourhood, which both algorithms use.
- *Chapter 26* — standardisation. Like PCA, t-SNE and UMAP are scale-sensitive; standardise first.

**Returns:**
- These tools are visualisation aids and don't deeply return in the corpus. They will appear, briefly, in any chapter where we want to look at high-dimensional embeddings — but no algorithm we cover later in the book builds on them.
- *Chapter 65* — `pyspark.ml` clustering. We will note there that the visualisation step of a clustering workflow (eyeballing the clusters) routinely uses t-SNE or UMAP, even though they're not in Spark MLlib.

---

## 41.10 Exercises

Shorter exercise set than usual, in keeping with the lighter touch of this chapter.

1. **Why heavy tails?** Why does t-SNE use a t-distribution in low-dim instead of a Gaussian? What problem does this solve?

2. **Perplexity sensitivity.** You run t-SNE with perplexity 5 and see ten tiny well-separated clusters. You rerun with perplexity 50 and see three big blobs. Which is "right"? What does this tell you about choosing perplexity?

3. **The "two clusters are close" fallacy.** Your t-SNE plot shows two well-separated clusters, with cluster A noticeably closer to cluster B than to cluster C. Can you conclude that A and B are similar in high-dim?

4. **No transform.** Why doesn't scikit-learn's `TSNE` have a `transform` method (only `fit_transform`)? What problem does this create for using t-SNE as a feature engineering step?

5. **UMAP vs. t-SNE on a million points.** You have 1 million 512-dim embeddings from a neural network. You want to visualise them. Which tool do you reach for, and what preprocessing do you do first?

6. **Run-to-run reproducibility.** You run t-SNE twice with the same `random_state`. Will you get exactly the same plot? Now run twice without setting `random_state`. What's likely to be the same across the two runs, and what's likely to differ?

7. **PCA → t-SNE pipeline.** Why is the standard practice to do PCA to ~50 dimensions before t-SNE, rather than running t-SNE on the original data?

8. **What can you NOT infer.** List three things that should never be inferred from a t-SNE plot alone.

9. **Big-data workflow.** Your company has 10 million user embeddings. The CEO wants a visualisation showing the user segments. Describe the workflow.

10. **PCA still wins.** Name three situations where, despite t-SNE and UMAP being available, you'd still reach for PCA.

<details>
<summary>Answers</summary>

1. The Gaussian's tails are too light. In high dimensions, points moderately far from each other in the original space need to be far in the low-dim embedding too — but in 2D there isn't enough "room" for them all to be moderately distant. With a Gaussian in low-dim, the algorithm tries to make moderately-distant points moderately distant in 2D, which forces the layout into a crowded blob (the "crowding problem"). The t-distribution's heavy tails let the algorithm place dissimilar points very far apart with low cost — they can spread out into the corners of the plot — which produces the dramatic cluster separation t-SNE is known for.

2. Neither is "right" — both are showing different scales of structure. Perplexity 5 emphasises very local structure (finds tiny sub-clusters); perplexity 50 emphasises broader structure (groups them up). The fact that the visualisations are so different at different perplexities is a warning that the data may not have a single clean cluster structure — or that you should look for features stable across multiple perplexity values.

3. **No.** Inter-cluster distances in t-SNE plots are essentially decorative; they are not quantitative. The heavy-tail trick deliberately allows dissimilar pairs to be placed at arbitrary distances. To check whether A and B are similar in high-dim, compute the actual pairwise distances or train a classifier — don't trust the t-SNE plot.

4. t-SNE's output coordinates are the result of an optimisation over the *full set of training points* — the position of each point depends on every other point. To "transform" a new point you'd have to re-run the optimisation including that point, which doesn't have a constant-time formulation. **Implication**: t-SNE cannot be used as a preprocessing step for downstream models that need to make predictions on new data. UMAP, which has a `transform()` method, can.

5. UMAP, almost certainly. t-SNE would take a very long time on 1M points. Preprocessing: standardise the embeddings (probably already done — neural net embeddings often have norm-1), then optionally PCA to 50 dimensions for speed, then UMAP. You might also subsample to 100,000 points first if you don't need to see every point individually in the final plot.

6. With the same `random_state`, you get the same plot (deterministic). Without setting it, the *cluster structure* will be similar but the *absolute positions, rotations, and reflections* of the clusters will differ. A given cluster might be in the upper-left in one run and the lower-right in the next; that location is meaningless.

7. (a) Speed — t-SNE's per-iteration cost depends on the dimensionality of the input; 50-dim is much cheaper than 784-dim. (b) Noise filtering — PCA's tail components are mostly noise; throwing them away gives t-SNE cleaner inputs. (c) Distance preservation — PCA preserves global Euclidean structure linearly, which then provides a sensible neighbourhood graph for t-SNE to refine non-linearly.

8. (a) That distance between clusters in the plot reflects distance in high-dim. (b) That cluster size in the plot reflects intra-cluster variance. (c) That cluster shape (round, elongated, etc.) reflects high-dim cluster geometry. (d) That cluster positions are stable across runs — they're not. Any one of these is a valid answer.

9. (a) Aggregate or subsample 10 million down to maybe 50,000 representative users — sample stratified by some segmentation if you already have one, or random. (b) Pull the sample onto a single machine. (c) Standardise; PCA to ~50 dimensions. (d) UMAP to 2D (faster than t-SNE for this size). (e) Plot, colour by some interpretable variable (acquisition date, revenue tier, geography). (f) If the CEO wants to deploy a segmentation, follow up with a K-means clustering on the original 10 million using $k$ informed by the visualisation.

10. (a) When you need to deploy the reducer on new data — PCA has a clean `transform()`, t-SNE does not. (b) When you need interpretable components — each PC is a linear combination of original features, while t-SNE/UMAP coordinates are opaque non-linear functions. (c) When the data really is linear-subspace structured and you just want compression — PCA is provably optimal for that, t-SNE/UMAP are designed for a different objective (local structure preservation) and over-engineered for it. (d) When speed matters and you're processing many datasets — PCA is dramatically faster and has no hyperparameters to tune.

</details>
