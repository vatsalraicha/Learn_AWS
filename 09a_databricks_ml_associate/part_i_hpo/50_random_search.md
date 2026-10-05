# Chapter 50 — Random Search: Bergstra & Bengio's Argument

> **Goal of this chapter:** to develop random search not as "the lazy alternative to grid search" but as a *principled improvement* with a specific theoretical justification. By the end you should be able to prove, in roughly 200 words and with arithmetic, why random search beats grid search in dimensions $\geq 4$, design a sensible random search by picking the right per-axis distributions (including when to use log-uniform), and articulate the narrow conditions under which grid search is still the right tool.

---

## 50.1 An unexpected result

In 2012, James Bergstra and Yoshua Bengio published a paper called *Random Search for Hyperparameter Optimization* in JMLR. The result was unintuitive enough that it took the field by surprise: **random search is almost always at least as good as grid search, and often substantially better**.

For a decade prior, grid search had been the default in scientific publications and in practitioner workflows. Random search was treated as a poor cousin — fine if you couldn't afford a real grid, but obviously inferior because it sometimes missed regions that a regular grid would cover.

Bergstra and Bengio's contribution was to show that this "obvious" intuition is wrong, and to give a precise reason why. The reason is geometric. The geometry is simple. Once you see it, you cannot unsee it.

This chapter walks through the argument. We start with the algorithm, we develop the geometric picture, we work through the probability arithmetic that quantifies the advantage, and we close with the practical recommendations — what distributions to sample from, when to use log-uniform, and when grid search is nevertheless the right choice.

---

## 50.2 The algorithm

The algorithm is even simpler than grid search. Three lines of pseudocode.

```
Input:
    - Per-hyperparameter distributions D_1, D_2, ..., D_d
      (each D_j is a probability distribution over candidate values for hyperparameter j)
    - Total budget N (number of evaluations)
    - Cross-validation scheme (k-fold, say)
    - Inner training procedure A
    - Validation metric M

Procedure:
    for n in 1..N:
        theta_n = (sample(D_1), sample(D_2), ..., sample(D_d))
        cv_scores = []
        for fold in 1..k:
            train_fold, val_fold = split(data, fold)
            model = A(train_fold, theta_n)
            cv_scores.append(M(model, val_fold))
        record(theta_n, mean(cv_scores))
    best_theta = argmax over recorded (theta_n, mean)
    final_model = A(all_train_data, best_theta)
    return final_model, best_theta
```

That's it. Sample $N$ configurations independently from the per-axis distributions, evaluate each with CV, keep the best.

Total fit count is the same formula as grid search, with $N$ replacing the grid size:

$$
\text{total\_fits} = k \cdot N + 1.
$$

If $N = 30$ and $k = 5$, that's 151 fits. The arithmetic is identical to grid search — what changes is *which 30 configurations* you visit.

---

## 50.3 The geometric picture

Here is the simplest way to see what random search does differently.

Consider a 2D search space: two hyperparameters, both continuous, both normalized to $[0, 1]$. We will visit 9 points. Grid search lays them out on a regular $3 \times 3$ grid:

```
  Grid search (9 evaluations):
                                   
  1.0 ┤   ●         ●         ●    
      │                            
  0.6 ┤   ●         ●         ●    
      │                            
  0.3 ┤   ●         ●         ●    
      │                            
   0  └────────┬────────┬─────────►
       0.2    0.5      0.8
```

Random search samples 9 points uniformly:

```
  Random search (9 evaluations):
                                   
  1.0 ┤        ●                   
      │   ●            ●           
  0.6 ┤              ●             
      │     ●               ●      
  0.3 ┤              ●             
      │   ●                     ●  
   0  └──────────────────────────►
       0   0.3  0.5  0.7  1.0
```

Now project these point sets onto each axis. The grid samples three distinct values of $\theta_1$ (the x-axis values 0.2, 0.5, 0.8) and three distinct values of $\theta_2$ (the y-axis values 0.3, 0.6, 1.0). The grid is structured: every value of $\theta_1$ pairs with every value of $\theta_2$.

The random sample, projected onto $\theta_1$, gives **nine distinct values** of $\theta_1$ (one per sample, with very high probability). Projected onto $\theta_2$, again **nine distinct values**. Each random sample explores a new point in *both* coordinates.

Now here is the question that determines everything:

> **What if only one of the two hyperparameters actually matters?**

Suppose $\theta_2$ is irrelevant — the validation loss does not depend on it. The loss is a function of $\theta_1$ alone. Then:

- Grid search has effectively only sampled the loss at **3 distinct values** of $\theta_1$ (the rest are duplicates from grid's perspective).
- Random search has sampled the loss at **9 distinct values** of $\theta_1$.

Random search has explored the *important* axis three times more thoroughly, using the same budget. The 6 wasted evaluations along the $\theta_2$ axis in grid search are *not* wasted in random search, because each one contributed a new $\theta_1$ value as a side effect.

This is the entire Bergstra-Bengio argument in one diagram and one paragraph. The rest is making it precise.

### 50.3.1 Why "only one hyperparameter matters" is realistic

The argument above sounds like a strawman: surely both hyperparameters matter, at least a little? In practice, the empirical claim of the Bergstra-Bengio paper is stronger: **across a wide variety of ML models, only 1–3 hyperparameters strongly affect the validation loss, even when you are tuning 5–10**.

For neural networks (the paper's setting), the dominant hyperparameters tend to be learning rate, number of hidden units, and weight decay. The activation function, the optimizer's momentum, the initialization scheme, the gradient clip — these matter, but typically much less. If your HPO budget is 100 evaluations and 7 of your 10 hyperparameters barely matter, you would much rather spend those 100 evaluations exploring 100 distinct values of the 3 important ones than 100 distinct values of the irrelevant 7.

For tabular ML (random forests, gradient-boosted trees), the dominant hyperparameters tend to be `learning_rate`, `max_depth`, `n_estimators`, and possibly `min_samples_leaf` or `min_child_weight`. The others (`max_features`, `class_weight`, `criterion`, …) matter less.

In the deep learning era, this insight has been validated again and again. Random search has been shown — across image classification, language modeling, RL — to match or beat grid search at the same budget. It is *not* unusual for random search at 100 trials to match grid search at 1000 trials.

---

## 50.4 Quantifying the advantage

Let's put numbers to it.

Suppose there is a "good" region of the search space — a region in which $\theta_1$ produces a validation loss within the top 5% of the achievable range. Geometrically, this region covers some fraction of the $\theta_1$ axis. Say it's the top 5% of $\theta_1$ values (the rest are mediocre or worse). We will call $p = 0.05$ the *target quantile*.

**Grid search.** With a grid of $m$ levels along $\theta_1$, what is the probability that at least one of the levels falls in the good region?

If the grid is regularly spaced — say at quantiles $1/(m+1), 2/(m+1), \ldots, m/(m+1)$ — and the good region happens to span 5% of the axis, then *whether or not* the good region is hit depends on its position relative to the grid. Often the grid misses the good region entirely. If we randomize the grid's offset, then the probability that at least one grid point lies in the good region is approximately the probability that the good region's length (0.05) exceeds the grid spacing ($1/(m+1) \approx 1/m$):

- $m = 3$: grid spacing 0.33; good region width 0.05. Grid points hit the good region with probability $\approx 0.05 \times 3 = 0.15$. Often miss.
- $m = 10$: grid spacing 0.10; good region width 0.05. Probability $\approx 0.05 \times 10 = 0.5$. Coin flip.
- $m = 20$: grid spacing 0.05; good region width 0.05. Probability $\approx 1.0$. Always hits.

The point is: for a fixed good-region width $p$, grid search needs roughly $m \geq 1/p$ levels along the important axis to reliably hit the good region. With $p = 0.05$, you need $m \geq 20$.

**Random search.** With $N$ uniformly-sampled points, the probability that *at least one* sample falls in the good region is:

$$
P(\text{at least one hit}) = 1 - (1 - p)^N.
$$

This is the *complement* of "none of the samples hit": each sample independently misses with probability $1 - p$, and $N$ independent misses have probability $(1 - p)^N$.

For $p = 0.05$:
- $N = 10$: $1 - 0.95^{10} = 1 - 0.599 = 0.401$ — 40% chance.
- $N = 20$: $1 - 0.95^{20} = 1 - 0.358 = 0.642$ — 64% chance.
- $N = 30$: $1 - 0.95^{30} = 1 - 0.215 = 0.785$ — 79% chance.
- $N = 60$: $1 - 0.95^{60} = 1 - 0.046 = 0.954$ — 95% chance.

To be 95% confident of hitting the top 5% of $\theta_1$, you need $N = 60$ random samples *regardless of the dimension of $\Theta$*. This is the key property: in random search, the per-axis hit probability does not depend on how many other axes you have. Grid search's hit probability, by contrast, *does* depend on other axes — because the grid budget is split across them.

### 50.4.1 Working a numerical example

Let's redo the calculation for a 3D grid vs random search of equal budget.

Suppose you have $N = 27$ evaluations. With grid search, you might lay out a $3 \times 3 \times 3$ cube. With random search, you sample 27 points uniformly from the 3D cube.

Now suppose only one of the three hyperparameters is important. Question: what is the probability that the best sample (in either method) falls in the top 5% of the important axis?

**Grid search.** Three distinct values along the important axis. Probability that at least one of the three is in the top 5% = $1 - 0.95^3 = 1 - 0.857 = 0.143$ ≈ **14%**.

**Random search.** Twenty-seven distinct values along the important axis (each sample picks $\theta_{\text{important}}$ uniformly). Probability that at least one is in the top 5% = $1 - 0.95^{27} = 1 - 0.250 = 0.750$ ≈ **75%**.

Same budget. Grid: 14% chance of getting a near-optimal value of the important hyperparameter. Random: 75% chance.

This 5× improvement is not magic. It comes from the simple geometric fact that random samples each contribute a new value to *every* axis, while grid samples reuse the same per-axis values across the grid.

### 50.4.2 Generalizing to higher dimensions

The advantage of random search grows as the dimension of $\Theta$ grows.

Suppose you have $d$ hyperparameters and a grid budget of $N$. To keep the grid balanced, you have $m = N^{1/d}$ levels per axis. With $N = 27$ and $d = 3$, $m = 3$. With $N = 27$ and $d = 5$, $m = 27^{1/5} \approx 1.93$ — so the grid is essentially 2 levels per axis (and you can only afford $2^5 = 32$ cells, close to 27).

The number of distinct values per axis grid search samples is $m = N^{1/d}$, which decays rapidly in $d$.

Random search, by contrast, always samples $N$ distinct values per axis, independent of $d$.

The ratio of distinct values: random search samples $N / N^{1/d} = N^{(d-1)/d}$ times more distinct values per axis than grid search.

| $d$ | grid distinct values/axis (m = N^{1/d}) | random distinct values/axis | ratio |
|--:|--:|--:|--:|
| 1 | 27 | 27 | 1× |
| 2 | 5.2 | 27 | 5× |
| 3 | 3 | 27 | 9× |
| 5 | 2 | 27 | ~14× |
| 8 | 1.5 | 27 | ~18× |

For $d = 1$, random and grid sample exactly the same set of distinct values along the (only) axis — there is no advantage. For $d \geq 2$, random pulls ahead, and the advantage grows with dimension.

This is why the practical rule is: **random search ≥ grid search for $d \geq 2$, and the advantage becomes overwhelming for $d \geq 4$**.

---

## 50.5 The distributions matter

Random search is "sample uniformly from the search space" — but what does uniform mean? The answer is not always obvious, and getting it wrong can waste most of your budget.

### 50.5.1 Linear-uniform

The simplest case. For a hyperparameter on a bounded interval where you have no prior preference, sample uniformly:

$$
\theta \sim \text{Uniform}(a, b).
$$

Use this for: `subsample` ∈ [0.5, 1.0], `colsample_bytree` ∈ [0.5, 1.0], `dropout_rate` ∈ [0, 0.5], `momentum` ∈ [0.7, 0.99]. Anything where each point in the interval is, a priori, equally plausible.

### 50.5.2 Log-uniform

The most common pitfall in random search is forgetting log scaling for hyperparameters that span orders of magnitude.

Consider `learning_rate` for an SGD optimizer. The plausible range might be $[10^{-5}, 10^{-1}]$ — four orders of magnitude. If you sample *linearly uniformly*:

$$
\text{lr} \sim \text{Uniform}(10^{-5}, 10^{-1}),
$$

then 90% of your samples will land in $[10^{-2}, 10^{-1}]$ — the top decade. You will essentially never sample $[10^{-5}, 10^{-4}]$, the bottom decade. If the true optimum lies in the bottom decade, you'll miss it.

The fix is to sample on a log scale:

$$
\log_{10}(\text{lr}) \sim \text{Uniform}(-5, -1).
$$

Equivalently, $\text{lr} = 10^u$ where $u \sim \text{Uniform}(-5, -1)$. With this distribution, each decade gets equal density: roughly 25% of samples in $[10^{-5}, 10^{-4}]$, 25% in $[10^{-4}, 10^{-3}]$, and so on. Log-uniform is the right default for any hyperparameter where the *order of magnitude* is what matters.

Use log-uniform for: learning rates, regularization strengths (`C` in SVMs, `lambda` in regularized regression), `gamma` in RBF kernels, batch sizes (in some treatments), variance hyperparameters in Gaussian processes.

Use linear-uniform for: fractions, probabilities, anything on a small bounded interval where each value is equally plausible.

A useful check: if your hyperparameter ranges from "small" to "big" by a factor of 10× or more, use log-uniform. If it ranges by less than 2×, log vs linear doesn't matter much; use linear for clarity.

### 50.5.3 Quantized uniform (qUniform)

For an integer hyperparameter on a wide range, sometimes you want uniform sampling restricted to a step size. For example, `n_estimators ∈ [50, 1000]` in steps of 50 — so the candidates are 50, 100, 150, …, 1000.

Hyperopt calls this `hp.quniform(name, low, high, q)`, where `q` is the quantization step. Optuna's equivalent is `trial.suggest_int(name, low, high, step=q)`.

For very wide integer ranges, you might want **log-quantized**: `n_estimators ∈ [10, 10000]` on a log scale with step 10. Hyperopt: `hp.qloguniform`. Useful when the hyperparameter is integer-valued *and* spans orders of magnitude.

### 50.5.4 Categorical (choice)

For categorical hyperparameters with no ordering, sample uniformly from the set:

$$
\theta \sim \text{Uniform}\{\text{option}_1, \text{option}_2, \ldots, \text{option}_k\}.
$$

Hyperopt: `hp.choice(name, options)`. Optuna: `trial.suggest_categorical(name, options)`.

If you have prior reasons to prefer some options, you can use a non-uniform distribution — but this requires you to know the answer ahead of time, which defeats the purpose of search. Stick with uniform unless you have strong prior knowledge.

### 50.5.5 Normal-around-a-guess

Sometimes you have a prior estimate — "the right learning rate is probably around $10^{-3}$" — and want to focus search there. You can sample from a normal distribution:

$$
\log_{10}(\text{lr}) \sim \mathcal{N}(-3, \sigma^2).
$$

Hyperopt: `hp.lognormal` or `hp.qlognormal`. This is less common in practice. It is mostly useful in a two-stage workflow: first random-uniform search to find an approximate optimum, then normal-around-that-optimum for refinement. Bayesian optimization (Ch 51) basically does this automatically.

---

## 50.6 A worked random search example

Let's redo the gradient-boosted tree example from Ch 49.3 with random search, with the same budget.

**Search space:**
- `learning_rate ~ LogUniform(1e-3, 1.0)` (so $\log_{10}(\text{lr}) \sim U(-3, 0)$)
- `n_estimators ~ qLogUniform(50, 500, q=50)` (integers, 50 to 500 in steps of 50, log-scaled)

**Budget:** 9 evaluations (matching the $3 \times 3$ grid). Five-fold CV.

We sample 9 configurations. Hypothetical realizations might be:

| Trial | `learning_rate` | `n_estimators` | Mean F1 (5-fold CV) |
|:-:|----:|----:|----:|
| 1 | 0.041 | 150 | 0.831 |
| 2 | 0.298 | 100 | 0.842 |
| 3 | 0.008 | 350 | 0.798 |
| 4 | 0.123 | 250 | **0.861** |
| 5 | 0.617 | 50  | 0.769 |
| 6 | 0.072 | 450 | 0.853 |
| 7 | 0.187 | 200 | 0.856 |
| 8 | 0.026 | 400 | 0.842 |
| 9 | 0.453 | 150 | 0.812 |

Best: trial 4, `learning_rate = 0.123, n_estimators = 250` with F1 = 0.861.

Compare to grid search's best from Ch 49.3 (F1 = 0.858 at `learning_rate = 0.1, n_estimators = 200`). The random search found a slightly better configuration with the same budget — because it explored an off-grid point. It also found 9 different values of `learning_rate` and 9 different values of `n_estimators`, compared to grid's 3 distinct values of each. If you wanted to visualize "how does loss vary with learning rate?" you'd get a much richer answer from the random data.

Of course, this single example doesn't prove anything — random search is, well, random, and could have gotten unlucky. Bergstra-Bengio is an *expectation* result, not a guarantee per run. But across many problems and many runs, random search systematically outperforms grid search of the same budget.

### 50.6.1 The downside of random search

Looking at the table above, you might notice something inconvenient: the trials are *not aligned*. You cannot read off "what happens as I vary `n_estimators` holding `learning_rate` constant" because no two trials share the same `learning_rate`. Grid search's results are easier to inspect and visualize.

For *interpretability of the search itself*, grid search wins. For *finding a good configuration*, random search wins. If you care about understanding the loss landscape (for a paper, for a deep dive), grid search has a place. If you just need a good model, random search is better.

---

## 50.7 The scikit-learn API

```python
from sklearn.model_selection import RandomizedSearchCV
from sklearn.ensemble import GradientBoostingClassifier
from scipy.stats import loguniform, randint

param_distributions = {
    "learning_rate": loguniform(1e-3, 1.0),
    "n_estimators":  randint(50, 501),          # uniform integer in [50, 500]
    "max_depth":     randint(3, 11),            # uniform integer in [3, 10]
    "subsample":     loguniform(0.5, 1.0),      # actually arguable — depends on prior
    "min_samples_leaf": randint(1, 21),
}

random_search = RandomizedSearchCV(
    estimator=GradientBoostingClassifier(random_state=42),
    param_distributions=param_distributions,
    n_iter=50,                                   # N = 50 random samples
    cv=5,
    scoring="f1",
    n_jobs=-1,
    random_state=42                              # reproducibility
)

random_search.fit(X_train, y_train)

print(random_search.best_params_)
print(random_search.best_score_)
best_model = random_search.best_estimator_
```

Total fits: $50 \times 5 + 1 = 251$.

The `param_distributions` dict accepts scipy `rv_frozen` distributions. `loguniform(a, b)` from `scipy.stats` is the log-uniform distribution on $[a, b]$. `randint(a, b)` is uniform integer on $[a, b-1]$ (sklearn's `randint` is half-open).

Setting `random_state=42` makes the run reproducible — same seed, same samples. This is essential for audit logs and for comparing different HPO algorithms on the same problem.

### 50.7.1 Pyspark.ml does not have a direct equivalent

`pyspark.ml` does not include a built-in `RandomizedSearchCV`. The `ParamGridBuilder` interface is grid-only. If you want random search in Spark, your options are:

1. Build the random configurations manually as a list of `ParamMap`s and pass them to `CrossValidator`'s `estimatorParamMaps`:
   ```python
   import random
   random_configs = []
   for _ in range(50):
       config = {rf.numTrees: random.choice([50, 100, 200, 500]),
                 rf.maxDepth: random.randint(3, 15)}
       random_configs.append(config)
   # Then build ParamMaps from these dicts
   ```
   This works but is awkward — you lose the ParamGridBuilder convenience.

2. Use Hyperopt with `algo=rand.suggest` and `SparkTrials` (Ch 53). This is the idiomatic Databricks path for random search on Spark.

For the exam, know that pyspark.ml's HPO primitive is the grid (`ParamGridBuilder`); random search on Spark goes through Hyperopt.

---

## 50.8 When grid search is still defensible

We argued in Ch 49 that grid search is fine for very low-dimensional problems. Let's restate this in light of the Bergstra-Bengio result.

**$d = 1$.** With one hyperparameter, grid and random sample the same number of distinct values per axis (namely $N$). There is no Bergstra-Bengio advantage. Grid is fine and more interpretable.

**$d = 2$, small grid.** With $d = 2$ and a 5×5 = 25 grid, random search has roughly a 5× distinct-values-per-axis advantage. But the grid is small enough that the advantage barely matters if both hyperparameters are important. If you suspect both matter, grid is fine. If you suspect one dominates, prefer random.

**Categorical-only spaces.** If all your hyperparameters are categorical with small cardinality (say 3 options each, 3 axes = 27 combinations), there is no "level granularity" issue — you can enumerate the full space. Just run the grid.

**Audit/reproducibility regimes.** If you need to be able to defend each evaluation point to a regulator, grid search's deterministic structure is easier to explain than "we sampled from a uniform distribution with seed 42." Both are reproducible, but grid is more concrete.

**Parallelism-bounded with cheap evaluations.** If you have 32 parallel workers and a 1-second model fit, you can afford 32 evaluations in 1 second. Just run a 32-cell grid; the dimensionality advantage doesn't matter at this budget.

For everything else — $d \geq 3$, non-trivial fit costs, expectation of unequal hyperparameter importance — random search dominates grid search and should be the default. Better still: Bayesian optimization / TPE (next two chapters), which dominates random search.

---

## 50.9 The "intermediate result" — random vs TPE

It's worth noting where random search sits in the larger landscape. The Bergstra-Bengio paper is a 2012 result. The same authors went on to introduce TPE (the same year) and Hyperopt (the library implementing it). The trajectory was:

1. **Grid search** — what everyone was doing.
2. **Random search** — Bergstra-Bengio, 2012. Surprisingly competitive.
3. **TPE** — Bergstra et al., the same year. Beats random.
4. **GP-based Bayesian optimization** — Snoek et al., 2012 ("Practical Bayesian Optimization of Machine Learning Algorithms"). Different surrogate, often better in low dimensions.
5. **Multi-fidelity / Hyperband / BOHB** — Falkner et al., 2018. Adds the early-stopping idea.

Random search is now seen as the *baseline* HPO algorithm — the thing you compare a fancier method against. If your fancier method doesn't beat random search, your fancier method isn't earning its complexity.

A practical implication: when you're benchmarking a new HPO setup, *include random search* as a baseline. Many published "new HPO methods" turn out to only barely beat random — and the "barely" is sometimes within the noise floor of the validation metric.

---

## 50.10 What this builds on / where this returns

**Builds on:**

- *Chapter 48* — the HPO problem, especially the "expensive black-box" framing.
- *Chapter 49* — grid search, the foil for this chapter.
- *Chapter 9* (sampling, CLT) — the probability arithmetic in §50.4 assumes basic comfort with the binomial / geometric calculations.

**Returns in:**

- *Chapter 51* — Bayesian optimization, which uses random search results as the initial seed.
- *Chapter 52* — TPE, which begins with $n_\text{startup}$ random evaluations before switching to model-guided sampling.
- *Chapter 53* — Hyperopt's `rand.suggest` algorithm and the search space primitives (`hp.uniform`, `hp.loguniform`).
- *Chapter 65* — pyspark.ml's lack of native random search, and the workaround via Hyperopt-on-Spark.

---

## 50.11 Exercises

1. **The basic probability.** With $N = 40$ random search samples and a target region covering 5% of the important axis, what is the probability of at least one sample falling in the target region? Show your work.

2. **Bergstra-Bengio in 2 dimensions.** You have 16 evaluations. Compare grid search (4×4) and random search (16 uniform samples) on a problem where only one of two hyperparameters matters. With "good region" defined as the top 10% of the important axis: what is the probability each method finds a good point?

3. **Scaling.** You're tuning 5 hyperparameters. With a budget of $N = 32$ evaluations: how many levels per axis does grid search give? How many distinct values per axis does random search give? What's the ratio?

4. **Log vs linear.** You're choosing a learning rate range $[10^{-4}, 10^{-1}]$. If you sample $\text{lr} \sim \text{Uniform}(10^{-4}, 10^{-1})$, what fraction of samples fall in the range $[10^{-4}, 10^{-3}]$? If you sample $\log_{10}(\text{lr}) \sim \text{Uniform}(-4, -1)$, what fraction?

5. **Choosing distributions.** For each hyperparameter, recommend `uniform`, `loguniform`, `quniform`, `qloguniform`, or `choice` and justify briefly: (a) `dropout_rate ∈ [0, 0.5]`, (b) `weight_decay ∈ [1e-6, 1e-2]`, (c) `n_layers ∈ {1, 2, 3, 4, 5}`, (d) `activation ∈ {"relu", "tanh", "elu"}`, (e) `n_estimators ∈ [50, 1000]`, (f) `momentum ∈ [0.5, 0.99]`.

6. **The same hot-streak.** You run random search twice on the same problem with different seeds. Run 1 finds best F1 = 0.857. Run 2 finds best F1 = 0.851. The "true" optimum, if you ran 10000 evaluations, would converge to about F1 = 0.860. Is this variation between Run 1 and Run 2 a problem? What does it tell you about how many random search trials you should budget?

7. **Counting fits.** A random search with $N = 30$ trials and 5-fold CV. How many model fits total? Compare to a $5 \times 6$ grid with 5-fold CV.

8. **When to refuse grid search.** Your colleague proposes grid-searching XGBoost with these grids: `learning_rate ∈ {0.01, 0.05, 0.1, 0.2}`, `max_depth ∈ {3, 5, 7, 9, 12}`, `n_estimators ∈ {100, 200, 500, 1000}`, `subsample ∈ {0.7, 0.85, 1.0}`, `colsample_bytree ∈ {0.7, 0.85, 1.0}`, `min_child_weight ∈ {1, 3, 5}`. With 5-fold CV, how many fits is that? On a cluster where each fit takes 2 minutes with 10× parallelism, how long? Propose a random search alternative.

9. **Reading off bias.** You run random search at budget 50 on a 10-hyperparameter problem. The best three configurations found are: F1 = 0.842, 0.838, 0.835. Configurations 4 through 50 score between 0.65 and 0.83. Two of the top three configurations have `max_depth = 7`; one has `max_depth = 8`. All other axes are spread out. What does this suggest about `max_depth`? How would you refine?

10. **Hyperopt search space construction.** Write a Hyperopt-style search space for a random forest that includes: `n_estimators` (integer, 50 to 500, qUniform), `max_depth` (integer, 3 to 30, qUniform), `min_samples_leaf` (integer, 1 to 20, qUniform), `max_features` (float, 0.1 to 1.0, uniform), `class_weight` (categorical, `None` or `"balanced"`). Use `hp.*` syntax.

11. **Variance from CV.** You report random search's best as F1 = 0.846. The per-fold values for that configuration are 0.81, 0.85, 0.84, 0.87, 0.85. What is the standard deviation of the per-fold F1? Is the gap between this configuration and the second-best (F1 = 0.842) statistically meaningful?

12. **The seed trap.** You run random search with seed 1 and find the best is `learning_rate = 0.078`. You run it again with seed 2 and find the best is `learning_rate = 0.124`. Both have F1 in the range [0.84, 0.85]. Are these really different optima, or is something else going on?

<details>
<summary>Answers</summary>

1. $P(\text{at least one hit}) = 1 - 0.95^{40} = 1 - 0.129 = 0.871$ → **87.1%**.

2. Grid (4×4): 4 distinct values along the important axis. $P = 1 - 0.9^4 = 1 - 0.656 = 0.344 \approx$ **34%**. Random (16): 16 distinct values along the important axis. $P = 1 - 0.9^{16} = 1 - 0.185 = 0.815 \approx$ **82%**.

3. Grid: $m = 32^{1/5} \approx 2$ levels per axis (you can only afford $2^5 = 32$ cells). Random: 32 distinct values per axis. Ratio: 16×.

4. Linear: 0.1% of the range — $10^{-4}$ to $10^{-3}$ is a width of $0.0009$, and the full range is $0.0999$. So $\approx 0.0009/0.0999 \approx 0.9\%$ of samples fall there. Log-uniform: the range $[10^{-4}, 10^{-3}]$ is one decade out of three, so $1/3 \approx 33\%$ of samples fall there.

5. (a) `uniform` — small bounded interval, all values equally plausible. (b) `loguniform` — spans 4 orders of magnitude. (c) `quniform` with q=1 or `choice` — small integer range. (d) `choice` — categorical. (e) `qloguniform` with q=50 — wide integer range, log-scaled. (f) `uniform` — small interval. (For (f), one could argue for `1 - loguniform(0.01, 0.5)` to focus on values close to 1, but uniform is fine.)

6. The variation between 0.857 and 0.851 is about 0.006 — well within typical noise for random search. It tells you 50 trials may not be enough to consistently find the best configuration. Budget more trials, or use multiple seeds and report the median.

7. Random: $30 \times 5 + 1 = 151$ fits. Grid 5×6: $30 \times 5 + 1 = 151$ fits. *Same total*. The difference is which 30 configurations you visit.

8. Grid size: $4 \times 5 \times 4 \times 3 \times 3 \times 3 = 2160$. With 5-fold CV: $2160 \times 5 = 10800$ fits + 1 = 10801. At 2 min per fit, that's 21,602 minutes ÷ 10 parallelism = 2160 wall-clock minutes ≈ **36 hours**. Not practical for a single experiment.  
Random search alternative: $N = 100$ trials, log-uniform on `learning_rate`, qUniform on the integers, uniform on the fractions. With 5-fold CV: 501 fits, 100 minutes ÷ 10 = 10 minutes wall-clock. About 200× faster and likely a better result.

9. `max_depth` near 7-8 appears to be the sweet spot. The signal is weak (only 3 of 50 trials look "best") but the locality is suggestive. Refine by doing a second random search with `max_depth ∈ {6, 7, 8, 9}` more heavily weighted, holding other hyperparameters in their full ranges. Or use TPE, which will naturally concentrate sampling in the high-density regions found so far.

10. ```python
   from hyperopt import hp
   space = {
       "n_estimators": hp.quniform("n_estimators", 50, 500, 1),
       "max_depth":    hp.quniform("max_depth", 3, 30, 1),
       "min_samples_leaf": hp.quniform("min_samples_leaf", 1, 20, 1),
       "max_features": hp.uniform("max_features", 0.1, 1.0),
       "class_weight": hp.choice("class_weight", [None, "balanced"]),
   }
   ```
   Note: `hp.quniform` returns floats — you'll need to cast to int inside the objective. And `hp.choice` returns an *index* into the list, not the value — you'll need `space_eval` to recover the value (we'll cover this in Ch 53).

11. Per-fold values: [0.81, 0.85, 0.84, 0.87, 0.85], mean 0.844, std = $\sqrt{((0.81-0.844)^2 + (0.85-0.844)^2 + (0.84-0.844)^2 + (0.87-0.844)^2 + (0.85-0.844)^2)/5} = \sqrt{(0.00116 + 0.000036 + 0.000016 + 0.000676 + 0.000036)/5} = \sqrt{0.0003848} \approx 0.0196$. So the fold-to-fold std is about 0.02. The 0.846 vs 0.842 gap is 0.004 — much smaller than the fold-to-fold std. *Not* statistically meaningful at this sample size. The two configurations are essentially equivalent.

12. They're sampling from the same loss landscape, and the loss landscape near the optimum is relatively flat. Both `lr = 0.078` and `lr = 0.124` are in a "basin" of good values. Different seeds find different points within the basin. The CV-fold noise (≈ 0.005) is comparable to the difference between the configurations. The right answer is "either is fine; the model is robust in this region." Practical implication: run multiple seeds, or use TPE which converges to the same basin more reliably.

</details>
