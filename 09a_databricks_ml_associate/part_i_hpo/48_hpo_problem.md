# Chapter 48 — The HPO Problem: Search Space, Objective, Budget

> **Goal of this chapter:** to define, precisely, what *hyperparameter optimization* is — what is being optimized, what is being varied, what is being measured, and what is being spent. By the end you should be able to look at any random-forest call, any gradient-boosted tree configuration, any neural network training loop, and answer three questions about it: what are the hyperparameters, what is the search space, and what would it cost to optimize them honestly. The next six chapters all assume that this framing is in your head.

---

## 48.1 The motivating moment

You have just trained your first random forest on a real problem. You set `n_estimators=100`, `max_depth=10`, `min_samples_leaf=5`, and you accepted the rest of scikit-learn's defaults. You ran a 5-fold cross-validation. The mean validation F1 came out to 0.82.

You stare at that 0.82 for a minute and ask yourself the question that every working ML engineer eventually asks: *is this a good model?* Or, more precisely: *could this model be better if I had chosen different settings?*

You don't know. You can't know — not by looking at the model. There is no inspection you can perform on a fitted random forest that tells you "you should have used 200 trees and `max_depth=15`." The only way to find out whether different settings produce a better model is to **try them**.

But how many settings are there to try? Let's see.

`n_estimators` is an integer; you might consider {50, 100, 200, 500, 1000}.  
`max_depth` is an integer or `None`; you might consider {5, 10, 20, 50, None}.  
`min_samples_leaf` is an integer; you might consider {1, 2, 5, 10, 20}.  
`min_samples_split` is an integer; you might consider {2, 5, 10, 20}.  
`max_features` is a fraction or `"sqrt"` or `"log2"`; you might consider {`"sqrt"`, `"log2"`, 0.3, 0.5, 0.7}.  
`class_weight` is `None`, `"balanced"`, or a dict; you might consider {`None`, `"balanced"`}.

Already, with six hyperparameters and modest grids per hyperparameter, you have $5 \times 5 \times 5 \times 4 \times 5 \times 2 = 5{,}000$ combinations. With 5-fold cross-validation, each combination costs five model fits. The grid would take 25,000 model fits. On a dataset where a single fit takes one minute, that is 17 days of compute.

You don't have 17 days. And we haven't even gotten to gradient boosting, which has *more* hyperparameters and where each fit is slower. We haven't gotten to neural networks, where each fit takes hours.

This is the hyperparameter optimization (HPO) problem in a sentence: **the space of model configurations is vast, evaluating any one of them is expensive, and we need to find a good one with a finite budget**. Everything in this Part — grid search (Ch 49), random search (Ch 50), Bayesian optimization (Ch 51–52), Hyperopt (Ch 53), Optuna (Ch 54) — is a different strategy for navigating that tension.

---

## 48.2 What a hyperparameter actually is

Before we can optimize hyperparameters, we have to be crisp about what they are. The word is one of those that sounds technical but, when you press on it, often gets used loosely. Let's pin it down.

Recall from Chapter 1 the picture of ML as function approximation: there is a learning algorithm $A$ that takes a training set $D$ and produces a model $\hat{f}$. The model $\hat{f}$ is parameterized by some collection of numbers we will call $w$ — for a linear regression, $w$ is the coefficient vector and intercept; for a decision tree, $w$ is the full set of splits and leaf values; for a random forest, $w$ is the entire collection of trees.

These numbers $w$ are what we call the **parameters** of the model. The defining property of a parameter is this: **the learning algorithm determines its value from the data**. You do not tell logistic regression what its coefficients should be — gradient descent finds them by minimizing the loss. You do not tell a decision tree which feature to split on at the root — the algorithm finds the best split by maximizing information gain.

Now, the learning algorithm itself has knobs. Logistic regression's gradient descent has a learning rate. The decision tree's recursive splitting has a maximum depth, a minimum-samples-per-leaf, a choice of splitting criterion. The random forest has a number of trees and the size of the random feature subset to consider at each split.

These knobs are the **hyperparameters**. The defining property of a hyperparameter is this: **you set its value before training begins, and you cannot change it without re-training**.

> Parameter: learned by the algorithm from data.  
> Hyperparameter: chosen by you, frozen for the run.

To change a parameter, you call `model.fit(...)`. To change a hyperparameter, you destroy the current model and call `RandomForestClassifier(n_estimators=200).fit(...)` again, from scratch. This asymmetry — that changing hyperparameters is expensive because it costs a full re-train — is what makes HPO hard.

Three quick examples to fix the picture:

| Model | Parameter (learned) | Hyperparameter (set) |
|---|---|---|
| Linear regression | coefficients $\beta$, intercept | regularization strength $\lambda$ (if Ridge), L1 vs L2 (if ElasticNet) |
| Random forest | every tree's structure and leaf values | `n_estimators`, `max_depth`, `min_samples_leaf`, `max_features` |
| Logistic regression | coefficients $w$, bias $b$ | learning rate, number of epochs, regularization $\lambda$, choice of `solver` |
| Gradient-boosted tree (XGBoost) | every tree's structure | `learning_rate`, `n_estimators`, `max_depth`, `min_child_weight`, `subsample`, `colsample_bytree`, `gamma`, `lambda` |
| K-means | the cluster centroids | `n_clusters`, the initialization scheme, `max_iter` |

A subtler case: in random forests, the **random seed** is a hyperparameter in the sense that you set it before training. But you would normally not *optimize over it*, because varying the seed across many random forests just measures the variance of the algorithm, not anything you want to ship. We'll come back to this distinction.

### 48.2.1 The grey zone

There are knobs that don't fit cleanly on one side. The number of epochs of training in a neural network is a hyperparameter in the sense that you set it, but if you use **early stopping** (stop training when validation loss stops improving), the *effective* number of epochs is data-determined — it has been promoted from hyperparameter to parameter. Similarly, the trees in a gradient-boosted ensemble are added one at a time, and you can use early stopping to determine `n_estimators` from the validation loss rather than tuning it externally. We'll discuss this in Ch 54 when we cover Optuna's pruners.

The point is not to win a definition argument. The point is: **anything you set before the algorithm starts and that affects how the algorithm produces its model is a hyperparameter**, and you have to choose its value somehow. The HPO problem is the discipline of choosing it well.

---

## 48.3 The HPO problem, formally

Let $\theta$ denote a hyperparameter setting — a single configuration, i.e., a specific choice for every hyperparameter we are tuning. So $\theta$ is a point in some space $\Theta$, which we will call the **search space**. For our random forest above with six hyperparameters, $\theta$ is a 6-tuple and $\Theta$ is the product of the six sets.

For any $\theta$, we can run the full training procedure — train a model with hyperparameters $\theta$ on the training data, then measure its loss on validation data. Call this $\mathcal{L}_{\text{val}}(\theta)$. The HPO problem is:

$$
\theta^* = \arg\min_{\theta \in \Theta} \; \mathcal{L}_{\text{val}}(\theta).
$$

This looks innocuous. It is the formal statement of an optimization problem you have seen written in this same shape many times. But the problem has four properties that make it different from, say, fitting a logistic regression. We will spend the rest of this section on each.

### 48.3.1 The objective is black-box

When you fit logistic regression, you minimize a cross-entropy loss, and you can compute the *gradient* of that loss with respect to the parameters. The gradient tells you which direction to move. Gradient descent (Ch 17) exploits this brutally: it just walks downhill until it reaches a minimum.

You cannot do that here. To know what $\mathcal{L}_{\text{val}}(\theta + \delta)$ is at a nearby point $\theta + \delta$, you have to *train a whole new model* with the new hyperparameters and measure its validation loss. There is no analytic gradient. You evaluate the function by running it.

This is the defining feature of HPO: the objective $\mathcal{L}_{\text{val}}$ is a **black box**. We can query it (expensively) but we cannot differentiate it. The entire field of HPO is the study of how to optimize a black-box function on a small budget of queries.

Three immediate consequences:

1. Gradient-based methods (SGD, Adam, BFGS) are off the table directly. We can sometimes approximate gradients (e.g., finite differences) but the cost is prohibitive in high dimensions.
2. Any algorithm we use must trade off **exploration** (trying new regions of $\Theta$ to see what's there) and **exploitation** (focusing on regions we already think are good). This trade-off shows up everywhere in HPO and is the central theme of Bayesian optimization (Ch 51).
3. We need to make every evaluation count. Spending one evaluation in a region we have already established is bad is wasteful.

### 48.3.2 Each evaluation is expensive

How expensive? Concretely:

| Model class | Typical time per fit | Budget for serious HPO |
|---|---|---|
| Logistic regression, small data | seconds | thousands of evaluations |
| Random forest, medium data (1M rows) | minutes | hundreds of evaluations |
| Gradient-boosted trees, medium data | tens of minutes | 50–200 evaluations |
| Deep neural network, large data | hours to days | 10–50 evaluations |
| Foundation-model fine-tuning | days to weeks | 3–10 evaluations |

The right HPO algorithm depends on which row you are in. For the top row, grid search and random search are fine — throw evaluations at the problem. For the bottom row, every evaluation must be chosen *very* carefully — Bayesian optimization, multi-fidelity, and learning-curve extrapolation become essential.

For the ML Associate exam, the canonical setting is the middle row: random forests and gradient-boosted trees on tabular data, with budgets in the dozens to low hundreds of evaluations. That's the range where TPE-via-Hyperopt (Ch 53) is the right default tool, and it's the range the exam questions live in.

### 48.3.3 Each evaluation is noisy

Suppose you train a random forest with the same hyperparameters $\theta$ twice. Do you get the same validation loss?

Almost never exactly. Two sources of noise:

**Algorithmic noise.** Many learning algorithms are stochastic. A random forest's bootstrap samples and random feature subsets depend on a random seed. Two random forests with the same `n_estimators=100` and `max_depth=10` will give different validation losses depending on the seed. Stochastic gradient descent introduces noise from mini-batch sampling. Neural network initialization is random. For all of these, the validation loss is a random variable, not a deterministic number.

**Data-split noise.** If your "validation loss" is computed on a single held-out split, then a different split would give a different number. Even with $k$-fold cross-validation (Ch 22), you get a *mean over folds* which is itself a random variable — a different choice of $k$ or a different shuffle would give a different mean.

The practical effect: $\mathcal{L}_{\text{val}}(\theta)$ is not a function; it is a random variable whose expectation we care about. We are really trying to minimize $\mathbb{E}[\mathcal{L}_{\text{val}}(\theta)]$, but we only have noisy samples of it.

What can we do about this?

1. Use cross-validation rather than a single split, so each evaluation is the *average* over $k$ folds — this reduces variance by a factor of roughly $\sqrt{k}$.
2. Fix the random seed of the learner where possible, so algorithmic noise is suppressed (the seed becomes part of $\theta$).
3. When two configurations look similar, don't get excited — the difference might be noise. Bayesian optimization (Ch 51) handles this gracefully by maintaining a posterior over $\mathcal{L}_{\text{val}}$ that includes uncertainty; grid search and naive random search do not.

A cautionary number to keep in your head: for a random forest on a typical medium-sized tabular problem, the standard deviation of validation F1 across random seeds is often around 0.003–0.01 (i.e., 0.3 to 1 F1 point). If your HPO algorithm declares that configuration A (F1 = 0.823) is better than configuration B (F1 = 0.821), you should be suspicious. You are within the noise floor. Differences of 0.001 mean very little.

### 48.3.4 The search space is structured

We have been writing $\Theta$ as if it were a generic set. It is not. It has structure that the HPO algorithm needs to respect.

**Continuous hyperparameters** live in intervals: `learning_rate ∈ [1e-5, 1e-1]`, `subsample ∈ [0.5, 1.0]`. These are real numbers. Sometimes they are best treated on a linear scale (`subsample`) and sometimes on a log scale (`learning_rate` — see Ch 50).

**Discrete hyperparameters** live in finite ordered sets: `n_estimators ∈ {50, 100, 200, 500}`, `max_depth ∈ {3, 5, 7, 10, 15, 20}`. The ordering matters — `max_depth = 5` is more similar to `max_depth = 7` than to `max_depth = 50` — so the algorithm should exploit that locality.

**Categorical hyperparameters** live in finite unordered sets: `criterion ∈ {"gini", "entropy", "log_loss"}`, `kernel ∈ {"linear", "rbf", "poly"}`. There is no ordering. The algorithm cannot interpolate between `"linear"` and `"rbf"`.

**Hierarchical (conditional) hyperparameters** depend on the value of other hyperparameters. If `solver = "saga"`, then `l1_ratio ∈ [0, 1]` applies; otherwise it doesn't. If `kernel = "poly"`, then `degree ∈ {2, 3, 4, 5}` applies; if `kernel = "rbf"`, then `gamma ∈ [1e-4, 1]` applies. The search space is not a flat product — it is a *tree* of choices, where some leaves contain more hyperparameters than others.

```
                      solver
                    /        \
                "lbfgs"     "saga"
                  |          / \
                  C      l1_ratio
                            |
                            C
```

This structure shows up in real models all the time. XGBoost has `booster ∈ {"gbtree", "gblinear", "dart"}`, and each booster has its own sub-hyperparameters. Random forest has `class_weight = "balanced"` or a dict (and if it's a dict, every class has its own weight — that's hierarchical). Neural networks have `optimizer ∈ {"sgd", "adam"}`, and if `optimizer = "adam"`, you also get `beta1` and `beta2`.

The HPO algorithm has to handle this. Grid search and random search handle it trivially (just enumerate the tree). Bayesian optimization handles it less trivially — Gaussian processes are awkward over hierarchical spaces, which is one of the reasons TPE (Ch 52) became popular: it handles hierarchical, mixed-type spaces natively.

### 48.3.5 Dimensionality

The total number of hyperparameters you are tuning is the **dimensionality** of $\Theta$. For a single decision tree, you might have 3–5. For a gradient-boosted tree (XGBoost or LightGBM), 8–12. For a small neural network with some architecture choices, 10–20. For a transformer with full architecture search, 30+.

Dimensionality matters because the **curse of dimensionality** is brutal in HPO. The volume of the search space grows exponentially in the number of dimensions. With 10 hyperparameters and 5 levels each, you have $5^{10} \approx 10 \text{ million}$ grid points. With a budget of 100 evaluations, you have covered $10^{-5}$ of the space.

This is why the answer to "should I use grid search?" depends heavily on dimensionality. For 1–2 hyperparameters, grid search is fine. For 3, it's borderline. For 4+, it is essentially always wrong. We will see why in Ch 49 and what to do about it in Ch 50.

---

## 48.4 The budget

The budget is the amount of compute you are willing to spend on the HPO procedure. We measure it in number of evaluations — i.e., number of full model fits — because that's the dominant cost.

A useful framing: your HPO procedure is going to spend $N$ evaluations, where each evaluation is one fit of the inner model. If you use $k$-fold cross-validation, "one evaluation" means $k$ fits, so the total fit count is $N \cdot k$. If you also do a final retrain on all training data at the chosen best $\theta$, add one more. The grand total is $N \cdot k + 1$ fits.

Choosing $N$ is a business decision dressed up as a technical one. Considerations:

- **How long does one fit take?** If a fit is 1 minute and you have 24 hours and 8 parallel workers, you can do $24 \cdot 60 \cdot 8 = 11{,}520$ fits in parallel, so $N$ on the order of 2000 (with $k = 5$) is feasible.
- **How important is the model?** If this is a one-off experiment, $N = 50$ may be plenty. If you are shipping a model that will run for two years, spend more.
- **How sensitive is the algorithm to hyperparameters?** A random forest is robust — the default settings work surprisingly often, so HPO gives modest improvement. XGBoost is more sensitive — HPO routinely improves F1 by 2–5 points. A deep neural network is exquisitely sensitive — HPO can be the difference between a useless model and a great one.
- **Diminishing returns.** Empirically, the first 20 evaluations of a Bayesian-style HPO often find 80% of the eventual improvement. The next 80 evaluations find the remaining 20%. After 200 evaluations, you are usually well into the noise floor. Spending $N = 1000$ is often pointless and sometimes counterproductive (you'll overfit to the validation set).

The exam typically asks you to think about $N$ in the range 16–100, with budgets like "max_evals = 32" or "max_evals = 50". These are realistic numbers for tabular models.

### 48.4.1 The hidden cost: the outer loop

There is one more thing to internalize about the budget. Each HPO evaluation is itself an inner loop that contains the model training. So the structure is:

```
for n in 1..N:                   # outer loop: HPO
    theta = pick_next_config()
    cv_losses = []
    for k_fold in 1..K:           # inner loop: CV
        model = train(theta, train_fold)
        loss = evaluate(model, val_fold)
        cv_losses.append(loss)
    mean_loss = mean(cv_losses)
    record(theta, mean_loss)
best_theta = argmin over recorded (theta, mean_loss)
final_model = train(best_theta, all_train_data)
return final_model
```

The HPO procedure is an **outer loop** around the cross-validation procedure, which is itself a loop around the training procedure. Three nested loops, multiplicative cost. This is also why parallelism matters so much in HPO (Ch 53): the outer loop's iterations are mostly independent and can run on separate workers.

---

## 48.5 The hyperparameter / validation / test discipline

Now is the right moment to revisit a piece of discipline from Chapter 22 (cross-validation) that becomes critical in HPO.

**Never tune hyperparameters using the test set.**

It sounds obvious. It is violated constantly, including by experienced practitioners, because the violation is subtle. Here is the picture done correctly:

```
Full dataset
    │
    ├── Test set (15%, locked away)
    │
    └── Train+Val pool (85%)
            │
            └── HPO inner loop runs k-fold CV on this pool
                   ├── Pick theta* by lowest mean CV loss
                   │
                   └── Retrain at theta* on the full Train+Val pool
                              │
                              └── Evaluate ONCE on test set → report number
```

The test set is touched exactly once, at the very end, to produce the number you report. The HPO algorithm — Hyperopt, Optuna, grid search, whatever — works entirely on the Train+Val pool.

Why this matters: every time you peek at the test set, you have implicitly used it to make a decision. If you ran HPO using the test loss as the objective, you would (a) find a configuration that happens to perform well on the test set specifically, and (b) lose the ability to honestly estimate how the model will perform on truly unseen data. Your "test loss" would be an overestimate, just as your "validation loss" was an overestimate during HPO.

This is sometimes called the **selection effect** or **silent overfitting to the validation set**. With enough HPO trials — say, thousands — you can actually overfit to the validation set even without touching the test set. The classical fix is **nested cross-validation** (Ch 22): an outer CV loop for evaluation, an inner CV loop for HPO. It's expensive but it's honest.

For the exam: know that HPO tunes against the validation set (or the CV mean over training data), and that final reporting uses the test set, once.

---

## 48.6 The strategy taxonomy

We close this chapter with a preview of the algorithms we will study, ordered roughly by sophistication.

**Grid search (Ch 49).** Enumerate the Cartesian product of per-hyperparameter grids; evaluate each. Exhaustive, deterministic, easy to parallelize. Breaks badly in high dimensions.

**Random search (Ch 50).** Sample $N$ points uniformly (or log-uniformly, where appropriate) from $\Theta$; evaluate each. The Bergstra-Bengio result shows this is almost always better than grid search in dimensions $\geq 4$.

**Bayesian optimization (Ch 51).** Fit a surrogate model to the (hyperparameter, loss) history; choose the next point by maximizing an acquisition function that trades off exploration and exploitation. The surrogate can be a Gaussian process (classical) or a Tree-structured Parzen Estimator (TPE — Ch 52).

**Evolutionary methods.** Genetic algorithms (mutate and recombine configurations) and CMA-ES (covariance matrix adaptation evolution strategy — Ch 54 mentions it in Optuna's sampler list). Useful in moderate continuous dimensions; less common for tabular ML.

**Bandit-based methods.** Hyperband and BOHB run many configurations with small budgets in parallel, kill bad ones early, and promote the survivors. Especially powerful when the model can be trained with intermediate evaluations (e.g., gradient-boosted trees adding one tree at a time, neural networks adding epochs). Optuna's pruners are this idea (Ch 54).

For the ML Associate exam, the names that matter are: **grid**, **random**, **TPE-via-Hyperopt**, and **Optuna**. The exam also tests the *math* of grid+CV (how many model fits — see Ch 49) and the *behavior* of SparkTrials parallelism (how parallelism trades off against Bayesian benefit — see Ch 53).

For your career, all of them matter. The choice depends on the cost per evaluation, the dimensionality, and how much structure you can exploit.

---

## 48.7 What this builds on / where this returns

**Builds on:**

- *Chapter 22* — cross-validation. Every HPO evaluation is a CV run.
- *Chapter 21* — the three-way split (train, validation, test) and why each set exists.
- *Chapter 18* — overfitting. HPO is precisely the discipline that, done wrong, lets you overfit to the validation set.

**Returns in:**

- *Chapter 49* — grid search and its specific failure modes.
- *Chapter 50* — random search and the Bergstra-Bengio argument.
- *Chapters 51–52* — Bayesian optimization and TPE.
- *Chapter 53* — Hyperopt's API and the SparkTrials parallelism math.
- *Chapter 54* — Optuna and the modern HPO toolkit.
- *Chapter 65* — `pyspark.ml`'s `CrossValidator` and `ParamGridBuilder`, where the model-count arithmetic from Ch 49 becomes an exam-favorite question.

---

## 48.8 Exercises

1. **Parameter vs hyperparameter.** For each of the following, decide whether it is a parameter or a hyperparameter of the model: (a) the weight on the "unsubscribe" feature in a logistic regression spam classifier; (b) the L2 regularization strength `C` in scikit-learn's `LogisticRegression`; (c) the choice of `solver = "lbfgs"` vs `"saga"`; (d) the splitting threshold at the root of a fitted decision tree; (e) `max_depth = 10` in the random forest that produced that decision tree; (f) the centroid coordinates in K-means; (g) `n_clusters` in K-means; (h) the random seed.

2. **Counting the grid.** You decide to tune a gradient-boosted tree with the following grid: `learning_rate ∈ {0.01, 0.05, 0.1}`, `max_depth ∈ {3, 5, 7, 10}`, `n_estimators ∈ {100, 200, 500}`, `subsample ∈ {0.7, 0.85, 1.0}`, `colsample_bytree ∈ {0.7, 0.85, 1.0}`. How many configurations does grid search visit? With 5-fold CV, how many model fits is that, plus the final refit on all training data?

3. **Hierarchy.** Consider an SVM with `kernel ∈ {"linear", "rbf", "poly"}`, `C ∈ [0.01, 100]` (always), `gamma ∈ [1e-4, 1]` (only if kernel is `"rbf"` or `"poly"`), `degree ∈ {2, 3, 4, 5}` (only if kernel is `"poly"`). Describe the search space as a tree. How many leaves does the tree have, and what is the "dimensionality" along each leaf?

4. **Black box.** Why can't you use gradient descent directly to optimize a random forest's `n_estimators`? List at least two reasons that are *not* "because it's an integer."

5. **Noise floor.** You run HPO on a random forest with 50 configurations. The best configuration scores F1 = 0.847. The 5th-best configuration scores F1 = 0.843. You re-run the entire HPO procedure from scratch (different seed) and the rankings change — now a *different* configuration scores 0.846 and the original "best" only scores 0.842. What happened, and what should you conclude about HPO's selection?

6. **Budget triage.** You have 24 hours and one machine (no parallelism). Each fit of your model takes 3 minutes. You want to tune 5 hyperparameters. How many evaluations $N$ can you afford with 5-fold CV? Is grid search practical? Is random search? Is TPE?

7. **Test set discipline.** Your colleague trained a model. They report: "I split data 70/30 train/test. I used the test set to pick hyperparameters, then refit on all the data with those hyperparameters. The final F1 on the test set is 0.91." Why is this 0.91 not a trustworthy estimate of production performance? Sketch the correct procedure.

8. **Dimensionality intuition.** Suppose hyperparameter $\theta_1$ has a strong effect on validation loss (changing it by 10% changes the loss by 0.05) and hyperparameter $\theta_2$ has zero effect (changing it does nothing). Both have 5 levels in your grid. With grid search at $5 \times 5 = 25$ trials, how many *distinct values of $\theta_1$* will you have evaluated? With random search at 25 trials, how many?

9. **Stochasticity audit.** Your gradient boosting library exposes `subsample` (row subsampling), `colsample_bytree` (column subsampling), and `seed`. Two configurations with the same hyperparameters but different `seed` produce slightly different models. Should `seed` be a hyperparameter you tune, a hyperparameter you fix, or something else?

10. **The outer loop again.** Write out (in pseudocode, like Section 48.4.1) what nested cross-validation looks like — an outer CV loop for honest evaluation, an inner CV loop for HPO. How many total model fits does it cost with $K_\text{outer} = 5$, $K_\text{inner} = 5$, $N = 20$ HPO evaluations?

<details>
<summary>Answers</summary>

1. (a) parameter — learned during training; (b) hyperparameter — set before training; (c) hyperparameter — set before training; (d) parameter — the threshold value is chosen by the tree algorithm from the data; (e) hyperparameter — you set it; (f) parameter — learned by K-means; (g) hyperparameter — you set it; (h) hyperparameter, technically, but not one you'd "optimize" — you'd typically fix it for reproducibility or average over it.

2. $3 \times 4 \times 3 \times 3 \times 3 = 324$ configurations. With 5-fold CV: $324 \times 5 = 1620$ fits, plus 1 final refit = **1621** total fits.

3. Three branches: linear (just `C`), rbf (`C`, `gamma`), poly (`C`, `gamma`, `degree`). Dimensionality: 1, 2, 3 respectively (counting active continuous + categorical dims). The tree has 3 leaves; this is what "hierarchical search space" means concretely.

4. (i) `n_estimators` is integer, so a gradient is not naturally defined; (ii) the validation loss as a function of `n_estimators` is not analytically expressible — each evaluation requires actually training and validating; (iii) the function is noisy, so even finite differences would be unreliable; (iv) the function is expensive, so even if we approximated gradients we couldn't afford to take many small steps.

5. The two HPO runs are sampling from the noise floor of the model. The differences between F1 = 0.847 and F1 = 0.843 are smaller than the natural variance across random seeds and CV splits. The "selection" of one configuration over another at this precision is essentially random. You should report the *range* of plausible performance, not a single number, and recognize that any of the top configurations is equally defensible. In practice: pick the one that's simplest or fastest at inference.

6. 24 hours $\times$ 60 min = 1440 min total. With 5-fold CV, each evaluation is $5 \times 3 = 15$ min, plus 3 min for the final refit. So $N$ such that $15 N + 3 \leq 1440$, giving $N \leq 95$. Round down to about $N = 90$.  
With 5 dimensions and 90 budget: grid search with 3 levels per dim gives $3^5 = 243$ — too many. Random search at 90 is reasonable. TPE at 90 (with 20 startup random + 70 model-guided) is the right answer for serious tuning.

7. The test set was used to pick the hyperparameters, so the reported test F1 is inflated by the selection effect — it's an optimistic estimate of out-of-sample performance. The correct procedure: split into train/val/test (e.g., 60/20/20) or train/test (e.g., 70/30), then do HPO using $k$-fold CV on the train portion only. The test set is touched exactly once, at the end.

8. Grid search at $5 \times 5 = 25$ trials: 5 distinct values of $\theta_1$ (because the grid only has 5 levels of $\theta_1$, and every level of $\theta_2$ wastes evaluations along the dead axis). Random search at 25 trials: 25 distinct values of $\theta_1$ (each sample picks $\theta_1$ uniformly). This is the Bergstra-Bengio argument in miniature; we'll see it in full in Ch 50.

9. Fix it. The seed is not a meaningful HPO variable — varying it tells you nothing about the model's design. Fixing it makes runs reproducible and removes one axis of meaningless variation. The right way to handle seed-sensitivity is to repeat evaluations at different seeds and *average*, treating the average as $\mathcal{L}_{\text{val}}(\theta)$. (Some practitioners do tune over seeds for ensembling, but that's a different game — model averaging, not HPO.)

10. Pseudocode:  
   ```
   for k_outer in 1..K_outer:           # honest evaluation loop
       outer_train, outer_test = split k_outer
       for n in 1..N:                    # HPO loop
           theta = pick_next_config()
           cv_losses = []
           for k_inner in 1..K_inner:    # CV loop
               inner_tr, inner_val = split k_inner from outer_train
               model = train(theta, inner_tr)
               cv_losses.append(eval(model, inner_val))
           record(theta, mean(cv_losses))
       best_theta_k = argmin
       final_model_k = train(best_theta_k, outer_train)
       outer_loss_k = eval(final_model_k, outer_test)
   report mean of outer_loss_k over k_outer
   ```
   Fit count: outer CV does $K_\text{outer} = 5$ iterations. Each inner HPO loop does $N \cdot K_\text{inner} = 20 \cdot 5 = 100$ fits. Plus one final refit per outer fold. Total: $5 \cdot (100 + 1) = 505$ fits. This is the price of honesty.

</details>
