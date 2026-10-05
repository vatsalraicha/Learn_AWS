# Chapter 52 — Tree-Structured Parzen Estimator (TPE) From First Principles

> **Goal of this chapter:** to derive TPE — Hyperopt's default algorithm — not as a black box but as a concrete information-theoretic procedure. By the end you should be able to (a) state the modeling inversion that defines TPE ($p(x \mid y)$, not $p(y \mid x)$), (b) explain why TPE's acquisition ratio $\ell(x) / g(x)$ corresponds to Expected Improvement, (c) describe how TPE handles continuous, categorical, and hierarchical parameters with the same machinery, and (d) work a small TPE step by hand on a 1D problem.

---

## 52.1 Why a different surrogate

We closed Ch 51 with three reasons TPE deserves its own treatment:

1. Hyperopt's default. The Databricks ML Associate exam tests Hyperopt. The exam tests TPE by name.
2. Mathematically different from GP-based BO. The "inversion" — modeling $p(x \mid y)$ rather than $p(y \mid x)$ — is genuinely novel.
3. Handles mixed-type and hierarchical search spaces natively. No kernel adaptation needed.

Let's make those three points concrete before diving in.

A Gaussian process predicts $p(y \mid x)$: for each candidate $x$, the GP gives a Gaussian distribution over the loss. This is the "natural" framing — you input hyperparameters, you ask for a loss prediction.

TPE flips this. It models $p(x \mid y)$: given a particular loss level (or range of loss levels), what distribution of $x$ values does it correspond to?

At first this seems backwards. Why would you want to know "given the loss is 0.3, what are the hyperparameters that produced it?" — the model already gives you the hyperparameters; the loss is the output, not the input.

The answer is that TPE doesn't try to predict the loss at all. It tries to **separate "good" hyperparameters from "bad" hyperparameters** based on the loss threshold. It then picks the next $x$ to be a sample that is likely to be "good" and unlikely to be "bad." That's the algorithm.

The exact rule — pick $x$ that maximizes the *ratio* of good-density to bad-density — turns out to be, surprisingly, exactly equivalent to Expected Improvement (up to a constant). So TPE is doing the same thing as GP-EI conceptually; it's just computing it differently.

This chapter unpacks all of that.

---

## 52.2 The TPE setup

Let's set notation. We have a history of $n$ observations: $\{(x_i, y_i)\}_{i=1}^n$. Each $y_i$ is the validation loss at hyperparameters $x_i$. We want to choose the next $x_{n+1}$.

**Step 1: Pick a threshold $\gamma$.**

Sort the observations by $y_i$. Pick a percentile — say the 25th percentile — as the threshold $y^*$. So $\gamma = 0.25$ means: the bottom 25% of observed losses are "good"; the top 75% are "bad". The actual $y^*$ value is whatever loss is at the 25th-percentile mark in your history.

In Hyperopt's default, $\gamma = 0.25$. Variations are explored, but 0.25 is the convention. (Note: some papers and implementations use $\gamma$ to mean the threshold value $y^*$ itself rather than the percentile; we'll use $\gamma$ for the percentile and $y^*$ for the threshold value.)

**Step 2: Split history into "good" and "bad".**

- Good set: $\{(x_i, y_i) : y_i < y^*\}$. The hyperparameter values that produced good losses.
- Bad set: $\{(x_i, y_i) : y_i \geq y^*\}$. The hyperparameter values that produced bad losses.

With $n = 20$ history points and $\gamma = 0.25$, good has 5 points and bad has 15.

**Step 3: Fit density estimates.**

- $\ell(x)$ = density of $x$ over the good set. "What does $x$ look like for good observations?"
- $g(x)$ = density of $x$ over the bad set. "What does $x$ look like for bad observations?"

These are densities over the hyperparameter space, not the loss. They tell us where good and bad hyperparameters live in $\Theta$, ignoring exactly *how* good or bad.

For continuous $x$: kernel density estimation (KDE) with Gaussian kernels.  
For categorical $x$: smoothed empirical frequencies (multinomial with a Dirichlet prior).  
For integer $x$: KDE on the integer scale, with rounding at the end.

We'll do the math for the continuous case below.

**Step 4: Acquisition — maximize $\ell(x) / g(x)$.**

The next sample is

$$
x_{n+1} = \arg\max_x \; \frac{\ell(x)}{g(x)}.
$$

Pick the $x$ that is *most likely to come from the good set* relative to the bad set.

That's the algorithm. The rest of this chapter is (a) why this acquisition is equivalent to EI, (b) how the density estimates are actually computed, (c) how the four types of search space dimensions work, and (d) a worked numerical example.

---

## 52.3 Why $\ell / g$ is Expected Improvement (in disguise)

This is the part that justifies TPE's design choice. We'll sketch it; the full derivation is in Bergstra et al. 2011.

Recall EI:

$$
\text{EI}(x) = \int_{-\infty}^{y^*} (y^* - y) \cdot p(y \mid x) \, dy.
$$

This integral is "expected improvement over the threshold $y^*$, weighted by the probability of each $y$ given $x$."

By Bayes' rule:

$$
p(y \mid x) = \frac{p(x \mid y) \cdot p(y)}{p(x)},
$$

so

$$
\text{EI}(x) = \int_{-\infty}^{y^*} (y^* - y) \cdot \frac{p(x \mid y) p(y)}{p(x)} \, dy.
$$

Define the conditional densities:

- For $y < y^*$ (good): the density $\ell(x) := p(x \mid y < y^*)$ marginalized over the good losses.
- For $y \geq y^*$ (bad): the density $g(x) := p(x \mid y \geq y^*)$ marginalized over the bad losses.

The denominator $p(x)$ is

$$
p(x) = \int p(x \mid y) p(y) \, dy = \gamma \, \ell(x) + (1 - \gamma) \, g(x),
$$

where $\gamma = P(y < y^*)$. (By definition of the threshold percentile, $\gamma$ is the fraction of $y$ values below $y^*$.)

So we can write

$$
p(x) = \gamma \ell(x) + (1 - \gamma) g(x).
$$

Now the EI integral becomes

$$
\text{EI}(x) = \frac{\gamma}{p(x)} \int_{-\infty}^{y^*} (y^* - y) p(y \mid y < y^*) \, dy.
$$

The integral inside is just $\mathbb{E}[y^* - y \mid y < y^*]$, a positive scalar that does not depend on $x$. Call it $C$. Then:

$$
\text{EI}(x) = \frac{\gamma C}{p(x)} = \frac{\gamma C}{\gamma \ell(x) + (1 - \gamma) g(x)}.
$$

Maximizing EI over $x$ is the same as maximizing $\frac{1}{\gamma \ell(x) + (1-\gamma) g(x)}$, which is the same as *minimizing* the denominator. Dividing both numerator and denominator of EI by $g(x)$:

$$
\text{EI}(x) \propto \frac{1}{\gamma \, \ell(x)/g(x) + (1-\gamma)}.
$$

To maximize EI, we want $\ell(x)/g(x)$ to be **large** — because a large $\ell/g$ makes the denominator dominated by the (negative-weighted) $\gamma \ell/g$ in disguise, but more directly: when $\ell/g$ is large, EI is large.

The conclusion: **maximizing EI is equivalent to maximizing $\ell(x)/g(x)$**, up to monotone transformations. TPE's acquisition rule is exactly Bayesian-optimization EI, computed by a different route.

The route matters because computing $\ell$ and $g$ separately via density estimation is *easier and more flexible* than computing a GP posterior over $p(y \mid x)$. That's TPE's pitch.

### 52.3.1 Why this is conceptually beautiful

Notice what TPE achieves. It never has to model the loss function $p(y \mid x)$ directly. It only ever needs to estimate two densities over $\Theta$ — the density of "good" hyperparameters and the density of "bad" hyperparameters. Both are routine 1D problems (for each parameter independently, in vanilla TPE), and densities of any type of variable can be estimated.

Compare to GP: every new query requires computing $\mu(x)$ and $\sigma(x)$ from the full history through matrix algebra, with a kernel that must respect the joint structure of all dimensions. GPs solve the harder problem of full conditional regression. TPE punts on regression and solves the easier problem of binary density estimation.

---

## 52.4 The density estimates, concretely

How does TPE actually compute $\ell(x)$ and $g(x)$? Per parameter, by parameter type.

### 52.4.1 Continuous parameters: KDE

For a continuous hyperparameter (e.g., `learning_rate` on a log scale, treated as a real number $\log_{10} \eta$), TPE uses **kernel density estimation** with Gaussian kernels.

Given the good observations $\{x_1, x_2, \ldots, x_m\}$ (just the $x$ values from the good set, for this single dimension), the KDE is

$$
\ell(x) = \frac{1}{m} \sum_{i=1}^m \mathcal{N}(x; x_i, \sigma_i^2),
$$

a mixture of $m$ Gaussians, each centered at an observed good point. The bandwidth $\sigma_i$ is chosen heuristically — Hyperopt uses an adaptive bandwidth based on distance to the nearest neighbor. Smaller bandwidth = sharper density; larger bandwidth = smoother density.

Same for $g(x)$ with the bad observations.

For our learning-rate example, suppose the good observations are at $\log_{10} \eta = \{-2.3, -2.0, -2.1, -1.8, -2.5\}$. The KDE puts a small Gaussian at each, summing to a single hump centered around $-2.1$. The density $\ell$ is high near $-2.1$, low far from it.

If the bad observations are at $\log_{10} \eta = \{-0.5, 0.0, -3.5, -3.0, 0.3, 0.5, -3.2, -0.3, -0.1, 0.1, ...\}$, the KDE produces a bimodal density — high at the extremes ($\log \eta$ very small or very large), low in the middle.

The ratio $\ell(x) / g(x)$ is then:
- Large around $\log \eta = -2.1$ (good is dense, bad is sparse).
- Small at $\log \eta = -3.5$ (bad is dense, good is sparse).
- Small at $\log \eta = 0$ (bad is dense, good is absent).

TPE picks the argmax, which is $\log \eta \approx -2.1$. The next evaluation goes near the current best region, with some sampling spread (TPE samples from $\ell$, not just argmax — see §52.5).

### 52.4.2 Categorical parameters: smoothed multinomial

For a categorical hyperparameter like `kernel ∈ {"linear", "rbf", "poly"}`, TPE estimates a multinomial distribution over the categories from the good and bad sets.

Naive: among the good observations, what fraction had `kernel = "linear"`? What fraction `"rbf"`? What fraction `"poly"`? These three fractions are $\ell$ for this parameter.

The naive estimate is unreliable when the good set is small (a category might have count 0 by chance). The fix is smoothing — add a small "prior" count to each category before normalizing:

$$
\ell(\text{kernel}) = \frac{\text{count(kernel) in good} + \alpha}{\text{total good} + 3 \alpha},
$$

with $\alpha$ a small smoothing constant (e.g., 1). This guarantees every category has a nonzero $\ell$ — TPE will sometimes pick a kernel that has never appeared in the good set, by exploration.

### 52.4.3 Integer parameters

Two strategies. Either treat as continuous (apply KDE on the integer scale, round at sampling time), or treat as a categorical with as many levels as there are distinct integer values. For wide ranges (e.g., `n_estimators` from 50 to 1000), KDE on the underlying log or linear scale is more efficient.

Hyperopt's `hp.quniform(name, low, high, q)` does this — it stores values internally as continuous but rounds to the nearest multiple of $q$ at the end.

### 52.4.4 Hierarchical (tree-structured) parameters

Here's where TPE gets its name. Consider a search space:

```
optimizer ∈ {"adam", "sgd"}
if optimizer == "adam":
    beta1 ∈ [0.5, 0.99]
    beta2 ∈ [0.9, 0.999]
if optimizer == "sgd":
    momentum ∈ [0.0, 0.99]
```

The space is a **tree**. Some leaves have more parameters than others. The full configuration depends on which branch you're in.

TPE handles this by estimating densities *conditional on the branch*. Concretely:

- $\ell(\text{optimizer})$: marginal density of `optimizer` over good observations (e.g., "60% of good observations used adam").
- $\ell(\text{beta1} \mid \text{optimizer} = \text{adam})$: density of `beta1` over the good observations *that used adam* (filtered subset, KDE).
- $\ell(\text{momentum} \mid \text{optimizer} = \text{sgd})$: density of `momentum` over the good observations *that used sgd*.

Same for $g$. When sampling the next $x$, TPE first samples `optimizer` from $\ell / g$ for that decision; then, conditional on the choice, samples the relevant sub-parameters from the conditional densities.

This conditional decomposition is what makes TPE handle complex real-world search spaces gracefully. GP-based BO requires you to either flatten the search space (lose conditional structure) or implement a structured kernel (hard). TPE just recurses on the tree.

### 52.4.5 The independence assumption

A note of caution. Vanilla TPE estimates the density of each parameter *independently*. That is, for hyperparameters $x_1, x_2$:

$$
\ell(x_1, x_2) \approx \ell_1(x_1) \cdot \ell_2(x_2).
$$

TPE assumes the good set has independent marginals. It can't detect interactions like "high `learning_rate` AND high `n_estimators` is good only together" — it sees the marginal "high `learning_rate` is good" and "high `n_estimators` is good" and proposes both, possibly without recognizing that *together* they might be bad.

This is a real limitation. Some extensions (Tree of Parzen Estimators with multivariate kernels, or copula-based methods) address it. Hyperopt's default does not.

In practice, the independence assumption is often forgivable — hyperparameter interactions are weak in most tabular ML problems. For deep learning, interactions are stronger and TPE's limitations become more visible. Optuna's multivariate sampler (Ch 54) tries to fix this.

---

## 52.5 The sampling step

We said TPE picks the $x$ that maximizes $\ell(x) / g(x)$. In practice, the maximization is done by *sampling*, not gradient ascent.

The algorithm:

1. Draw $n_{\text{candidates}}$ samples from $\ell(x)$ (say 24 samples).
2. For each, compute the ratio $\ell(x) / g(x)$.
3. Return the sample with the highest ratio.

Why not pure argmax? Two reasons.

- **Computational.** Maximizing $\ell / g$ analytically would require gradient methods that fail on non-smooth densities (especially with categorical components). Sampling is more robust.
- **Stochasticity.** Drawing from $\ell$ naturally introduces variation across iterations of TPE, helping it explore.

The 24 candidates are sampled from $\ell$ specifically because $\ell$ is the "good" distribution — these are all likely to be good *a priori*. Then we choose the most-good-relative-to-bad one. This biases TPE toward exploitation but with some natural spread.

For categorical parameters, the same logic applies: sample 24 candidates from $\ell$ (a multinomial), evaluate $\ell/g$ for each, return the argmax. For tree-structured spaces, sample from the conditional $\ell$ structure.

---

## 52.6 Initialization: the startup random phase

TPE cannot start from zero history — the densities $\ell$ and $g$ have nothing to estimate when there are no observations.

Hyperopt's default: **run $n_{\text{startup}}$ random evaluations first**, where $n_{\text{startup}} = 20$ by default. These 20 random samples seed the history. After that, TPE takes over.

This is identical in spirit to the BO initial-samples step (Ch 51). With fewer than ~15 history points, the densities are unreliable; with 20+, they start to mean something.

A consequence: TPE's *first 20 trials* are random search trials. If your total budget is 25, you're doing 20 random + 5 TPE — barely using the TPE benefit. If your total budget is 100, you're doing 20 random + 80 TPE — getting the full benefit.

For very small budgets (< 30), TPE isn't much different from random search. The crossover is around $N = 40$-$50$, where TPE's selection from accumulated history starts to dominate the initial random scatter.

---

## 52.7 The threshold $\gamma$

TPE's threshold percentile $\gamma$ is a hyperparameter of TPE itself (a meta-hyperparameter). Default is $\gamma = 0.25$. Variations:

- **Smaller $\gamma$ (e.g., 0.10)**: fewer points are "good", more are "bad". TPE becomes more exploitative — it tries to refine the small good region. Risk: the good set is too small to estimate density well.
- **Larger $\gamma$ (e.g., 0.50)**: more points are "good". TPE becomes more exploratory — it has a fuzzier sense of where "good" is. Risk: dilutes the signal.

In Hyperopt, $\gamma$ is the algorithm parameter `gamma` passed to `tpe.suggest`. Most users leave it at the default.

There's also a related parameter, `n_EI_candidates` (the number of candidates sampled from $\ell$ before picking the argmax, mentioned in §52.5). Hyperopt's default is 24. Larger values give a sharper argmax (closer to true maximum of $\ell/g$); smaller values are more stochastic and faster.

For the exam: know that $\gamma$ is a percentile (Hyperopt default 0.25), the threshold splits good from bad observations, and TPE's acquisition is the ratio $\ell/g$.

---

## 52.8 A worked numerical example

Let's do a TPE step with real numbers. 1D problem: tune the regularization strength $C$ for a logistic regression. We've observed 10 trials so far, all using uniform-random sampling (Hyperopt's startup):

| Trial | $\log_{10} C$ | $C$ | Loss (1 − F1) |
|---|---|---|---|
| 1 | -2.0 | 0.01  | 0.30 |
| 2 | -1.5 | 0.032 | 0.22 |
| 3 |  1.0 | 10    | 0.45 |
| 4 | -0.5 | 0.316 | 0.20 |
| 5 |  0.5 | 3.16  | 0.32 |
| 6 | -2.5 | 0.003 | 0.40 |
| 7 |  0.0 | 1.0   | 0.18 |
| 8 |  1.5 | 31.6  | 0.55 |
| 9 | -1.0 | 0.1   | 0.21 |
| 10 | -3.0 | 0.001 | 0.48 |

(These are 10 observations because the example is small. In practice TPE would have switched on at trial 20 or 21.)

**Step 1: Pick threshold $\gamma = 0.25$.** Sort losses ascending: 0.18, 0.20, 0.21, 0.22, 0.30, 0.32, 0.40, 0.45, 0.48, 0.55. The 25th percentile of 10 sorted values is between the 2nd and 3rd values: roughly 0.21 (rounding to a clean number). Three good observations (losses ≤ 0.21): trials 7, 4, 9. Seven bad observations (losses > 0.21): the rest.

| Category | Trials | $\log_{10} C$ values |
|---|---|---|
| Good (3) | 7, 4, 9 | 0.0, -0.5, -1.0 |
| Bad (7) | 1, 2, 3, 5, 6, 8, 10 | -2.0, -1.5, 1.0, 0.5, -2.5, 1.5, -3.0 |

**Step 2: Fit KDEs.**

For the good set (3 points: -1.0, -0.5, 0.0), the KDE is a sum of three small Gaussians, with a peak around $\log_{10} C = -0.5$. The good density is concentrated in the range $[-1.0, 0.0]$.

For the bad set (7 points: -3.0, -2.5, -2.0, -1.5, 0.5, 1.0, 1.5), the KDE is bimodal — a cluster at the low end ($-3.0$ to $-1.5$) and another at the high end ($0.5$ to $1.5$). The bad density is concentrated at the extremes.

**Step 3: Sample 24 candidates from $\ell$, evaluate $\ell/g$.**

The candidates will mostly fall in $[-1.0, 0.0]$ (because that's where $\ell$ is concentrated). For each candidate $x_c$:

- At $x_c = -0.5$: $\ell(-0.5)$ is large (right at the peak of good). $g(-0.5)$ is small (between the two bad clusters). Ratio $\ell/g$ is large.
- At $x_c = -1.0$: $\ell(-1.0)$ is moderate (edge of good). $g(-1.0)$ is small but climbing toward the low-end bad cluster. Ratio is moderate.
- At $x_c = 0.0$: $\ell(0.0)$ is moderate (right edge of good). $g(0.0)$ is small. Ratio is large.

The argmax of $\ell/g$ is around $\log_{10} C = -0.5$, possibly slightly toward 0.0 (since $g$ is even smaller there). Let's say TPE picks $\log_{10} C = -0.3$, or $C = 0.50$.

**Step 4: Evaluate.** Train logistic regression with $C = 0.50$. Suppose it gives loss = 0.17 (best so far).

| Trial | $\log_{10} C$ | $C$ | Loss |
|---|---|---|---|
| ... | ... | ... | ... |
| 11 | -0.3 | 0.50 | **0.17** |

**Step 5: Update.** New best. Re-sort, re-pick threshold (now between values 0.17 and 0.20), re-fit densities. The "good" set now includes trial 11 (and possibly trials 4 and 7 also stay; trial 9 might drop out). The peak of $\ell$ moves slightly toward $\log_{10} C = -0.3$. The next TPE proposal will be very close.

After 20 more iterations, TPE will have concentrated around $\log_{10} C \approx -0.5$ to $-0.3$, with a few exploratory probes elsewhere (driven by the natural variation of KDE-based sampling). The best observed loss will be close to the true minimum.

This is what TPE does. Each step: split history by quantile, fit two densities, sample from "good" density, pick the candidate that's most good-relative-to-bad, evaluate, update.

---

## 52.9 Strengths and weaknesses, summarized

**Strengths:**

1. **Scales linearly with history.** No matrix inversion. 1000 evaluations don't slow it down.
2. **Mixed types.** Continuous, categorical, integer, hierarchical — all handled with the same machinery.
3. **No kernel hyperparameters to tune.** KDE bandwidth is adaptive; multinomial smoothing is fixed.
4. **Robust in practice.** Beats random search across a wide range of problems with reasonable budgets (50+).

**Weaknesses:**

1. **Independence assumption.** Vanilla TPE treats parameters as marginally independent. Misses interactions.
2. **No native uncertainty.** TPE doesn't produce calibrated uncertainty estimates the way GPs do. The threshold $\gamma$ is a coarse stand-in for "where are we sure vs unsure."
3. **Parallelism limitations.** Sequential TPE is best; parallel TPE (multiple proposals at once) loses some quality, similar to parallel BO (Ch 51.8).
4. **Sensitive to $n_{\text{startup}}$.** With too few startup samples, the densities are poor and TPE degrades to almost random.

For ML Associate tabular HPO with 50–500 evaluations, TPE is essentially optimal. For deep learning with 10 evaluations, TPE barely warms up before the budget is exhausted. For 10,000 evaluations, the constant factor in TPE's overhead becomes annoying.

---

## 52.10 A note on TPE vs the rest of the BO family

We should be clear that TPE *is* Bayesian optimization. The category includes any algorithm that fits a probabilistic surrogate to history and uses an acquisition function. GPs are one surrogate; TPE is another. The recent SMAC algorithm uses random forests as the surrogate.

The right mental model: BO is a framework. GP, TPE, random forest, neural net are all valid choices of surrogate. EI, PI, UCB, Thompson sampling are all valid choices of acquisition. The literature is a matrix of (surrogate × acquisition) combinations, and TPE happens to be the (KDE-based-on-percentile-split, EI-derived-ratio) entry.

For the exam: know that TPE is Bayesian optimization, that its surrogate models $p(x|y)$ instead of $p(y|x)$, and that its acquisition is $\ell(x)/g(x)$ which is equivalent to EI.

---

## 52.11 Implementation pointer: how to read Hyperopt's source

If you want to verify any of this, Hyperopt's source is readable. The relevant module is `hyperopt.tpe`. The main function is `tpe_suggest` (or `suggest` in older versions), which:

1. Takes the trial history.
2. Splits by the `gamma` quantile.
3. Calls density-estimation routines per parameter (different for `hp.uniform`, `hp.loguniform`, `hp.choice`, etc.).
4. Samples `n_EI_candidates` candidates from the good densities.
5. Computes log-ratios $\log \ell(x) - \log g(x)$ for each candidate.
6. Returns the argmax candidate.

You don't need to read it for the exam. But knowing the source is real and tractable is worth something — TPE is not magic, just code.

---

## 52.12 What this builds on / where this returns

**Builds on:**

- *Chapter 51* — Bayesian optimization framework. TPE is one instance.
- *Chapter 8* — Bayes' theorem. The $p(y|x) \to p(x|y)$ inversion is exactly Bayes.
- *Chapter 9* — sampling. TPE samples from $\ell$ to find acquisition candidates.

**Returns in:**

- *Chapter 53* — Hyperopt's API. The `tpe.suggest` algorithm we've just derived is what you'll invoke in code.
- *Chapter 54* — Optuna's `TPESampler`. Similar mechanics, different API. Optuna also offers multivariate TPE that fixes the independence assumption.

---

## 52.13 Exercises

1. **State the inversion.** In your own words (no formulas), what does TPE model that distinguishes it from GP-based BO? What are the two densities $\ell$ and $g$ over?

2. **Bayes derivation.** Starting from EI and applying Bayes' rule, derive the relationship between $\text{EI}(x)$ and $\ell(x)/g(x)$. You can use the sketch in §52.3 as a guide.

3. **Choosing $\gamma$.** What happens to TPE's behavior if you set $\gamma = 0.5$ instead of $0.25$? Half of observations become "good", half "bad". Is TPE more or less exploitative? Why?

4. **The startup phase.** With Hyperopt's default `n_startup_jobs = 20` and your `max_evals = 30`, how many of your evaluations are TPE-guided and how many are random? What does this tell you about minimum budgets for TPE to be worthwhile?

5. **Categorical density.** Your good set contains 8 observations, of which 5 used `kernel = "rbf"`, 2 used `linear`, and 1 used `poly`. Without smoothing, what is $\ell(\text{kernel})$? With smoothing $\alpha = 1$, what is $\ell(\text{kernel})$?

6. **Independence assumption.** Suppose two hyperparameters $x_1, x_2$ are *strongly interacting* — good values occur only when both are simultaneously moderate. Will vanilla TPE pick up this interaction? Why or why not? Sketch an example where it fails.

7. **Worked split.** Given history losses [0.41, 0.32, 0.55, 0.27, 0.61, 0.29, 0.39, 0.44, 0.30, 0.52, 0.36, 0.48], with $\gamma = 0.25$: which losses are in the "good" set? What is the threshold $y^*$?

8. **Acquisition by sampling.** Why does TPE sample from $\ell$ (not from $g$, not uniformly) when looking for the next configuration? What would go wrong if TPE sampled uniformly?

9. **Hierarchical example.** Sketch the TPE density-estimation procedure for the search space: `optimizer ∈ {"adam", "sgd"}`; if "adam", also tune `beta1 ∈ [0.5, 0.99]`; if "sgd", also tune `momentum ∈ [0.0, 0.99]`. With 15 good observations total, 9 of which used adam and 6 of which used sgd, what densities does TPE fit and over what subsets?

10. **TPE vs random at low budget.** You have a budget of 25 evaluations. Will TPE clearly outperform random search? Why or why not? At what budget would you expect a clear separation?

11. **Comparison with GP.** Name two specific characteristics of a search space that make TPE preferable to GP-based BO, and two that make GP preferable.

12. **The minimization convention.** Hyperopt's `fmin` minimizes by convention. If your objective is to maximize F1, what do you return from your objective function? How does this interact with the "good" set being losses below a threshold?

<details>
<summary>Answers</summary>

1. GP-based BO models $p(y \mid x)$ — given hyperparameters, what's the distribution of loss? TPE models $p(x \mid y)$ — given a loss range (good or bad), what's the distribution of hyperparameters? $\ell$ is the density of $x$ values that produced good losses (below threshold); $g$ is the density of $x$ values that produced bad losses (at or above threshold).

2. See §52.3. The key steps: write EI as an integral over $y < y^*$ of $(y^* - y) p(y \mid x) dy$; apply Bayes to write $p(y \mid x) = p(x \mid y) p(y)/p(x)$; separate the $y < y^*$ part as $\gamma$ times the good distribution; observe that maximizing EI over $x$ reduces to maximizing $1/p(x)$, which (given the mixture structure) reduces to maximizing $\ell(x)/g(x)$.

3. With $\gamma = 0.5$, half the observations are "good", which dilutes the good signal — $\ell$ becomes broader (more observations span more of the space, less concentrated). This makes TPE more exploratory and less greedy. Default $\gamma = 0.25$ keeps the good set tight (the truly best 25%), so $\ell$ is sharper and TPE exploits more. Larger $\gamma$ → more exploration.

4. With `max_evals = 30`: 20 random + 10 TPE. Only 10 trials benefit from TPE's history-aware selection. For meaningful TPE benefit, you want `max_evals` significantly above `n_startup_jobs` — at minimum 40 or so, ideally 100+.

5. Without smoothing: $\ell(\text{rbf}) = 5/8 = 0.625$, $\ell(\text{linear}) = 2/8 = 0.25$, $\ell(\text{poly}) = 1/8 = 0.125$. With smoothing $\alpha = 1$: $\ell(\text{rbf}) = (5 + 1)/(8 + 3) = 6/11 \approx 0.545$, $\ell(\text{linear}) = 3/11 \approx 0.273$, $\ell(\text{poly}) = 2/11 \approx 0.182$. Smoothing pulls the multinomial toward uniform; the smaller the sample, the bigger the pull.

6. No. Vanilla TPE assumes independence: $\ell(x_1, x_2) = \ell_1(x_1) \cdot \ell_2(x_2)$. If interaction matters, TPE sees that "moderate $x_1$" is good (marginal) and "moderate $x_2$" is good (marginal), and proposes moderate-moderate combinations correctly. But if the truth is "extreme-extreme is good and moderate-moderate is bad" (e.g., XOR-like landscape), TPE's marginals say "moderate is bad" for each axis, and TPE will sample extremes — which TPE might then accidentally find work *together*. The pathology is that TPE can't *purposefully* go for the interaction; it'd find it by luck. Example: $f(x_1, x_2) = \text{small if } |x_1 + x_2| \text{ near 1}$ — TPE sees no clear marginal preference for either axis and explores randomly.

7. Sorted ascending: 0.27, 0.29, 0.30, 0.32, 0.36, 0.39, 0.41, 0.44, 0.48, 0.52, 0.55, 0.61. The 25th percentile of 12 values is between positions 3 and 4 — approximately 0.31. The "good" set (3 observations) contains losses 0.27, 0.29, 0.30. The threshold $y^* \approx 0.31$.

8. TPE samples from $\ell$ because $\ell$ is the distribution over hyperparameters that have produced *good* losses. Sampling from $\ell$ ensures the candidates are *a priori plausible* — they look like configurations that have worked before. Then we pick the one most-good-relative-to-bad. If TPE sampled uniformly, most candidates would be in regions $\ell$ knows nothing about, and TPE's selection of the argmax-by-ratio would be poorly informed. Sampling from $\ell$ focuses the candidate set on plausibly good regions.

9. TPE fits:
- $\ell(\text{optimizer})$: multinomial over {adam, sgd}, with counts 9 adam and 6 sgd in the good set.
- $\ell(\text{beta1} \mid \text{optimizer} = \text{adam})$: KDE over `beta1` values from the 9 adam good observations.
- $\ell(\text{beta2} \mid \text{optimizer} = \text{adam})$: KDE over `beta2` values from the same 9 observations.
- $\ell(\text{momentum} \mid \text{optimizer} = \text{sgd})$: KDE over `momentum` from the 6 sgd good observations.
And the symmetric $g$ densities from the bad set. When sampling a new configuration, TPE first samples `optimizer` from the ratio $\ell/g$ over {adam, sgd}, then samples the conditional sub-parameters.

10. At budget 25 with `n_startup_jobs = 20`, only 5 TPE-guided trials happen — barely enough to differ from random. You'd expect TPE ≈ random search at this budget. Clear separation appears around 50-100 evaluations (i.e., 30-80 TPE trials post-startup), where the accumulated history is large enough for TPE's density estimates to meaningfully guide search.

11. TPE preferable: (a) mixed-type spaces with categorical / hierarchical structure; (b) large budgets (1000+) where GP's $O(n^3)$ cost becomes prohibitive. GP preferable: (a) smooth, low-dimensional continuous spaces (e.g., tuning 3 continuous hyperparameters of a neural net); (b) when calibrated uncertainty estimates matter for downstream reasoning (active learning, calibrated stopping).

12. Hyperopt minimizes, so to maximize F1 you return $-F1$ (or equivalently $1 - F1$, the loss). The "good" set then becomes the configurations with the *lowest* $-F1$ (i.e., *highest* F1), which is what you want. TPE doesn't care that the objective is called "loss" — it just sorts and splits.

</details>
