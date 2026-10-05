# Chapter 49 — Grid Search: Complete and Exhaustive, and Why It Fails

> **Goal of this chapter:** to develop grid search from its most natural form, prove that it has exactly the property its name promises (every grid point gets tried), derive the model-fit counting formulas that appear directly on the exam, and then show — geometrically and with worked examples — why grid search is the wrong default for modern ML even though it is the most obvious algorithm anyone could invent.

---

## 49.1 The most natural impulse

You have a hyperparameter to tune. Maybe it's a regularization strength `C` for logistic regression. You suspect the right value lies somewhere between 0.001 and 100, and you want to find it.

Your natural impulse is: **try a bunch of values, evaluate each one, keep the best**. Maybe try `C ∈ {0.001, 0.01, 0.1, 1, 10, 100}` — six values, six evaluations. Whichever gives the best validation F1 wins. Done.

Now suppose you have two hyperparameters: `C` and `solver_max_iter ∈ {100, 200, 500, 1000}`. You'd naturally try every combination — six `C` values times four `max_iter` values = 24 evaluations. A 2D grid.

This is grid search. The algorithm is so natural that you would invent it on the spot without ever having heard of HPO as a discipline.

```
            max_iter →
              100   200   500  1000
       0.001   ●     ●     ●     ●
       0.01    ●     ●     ●     ●
   C → 0.1     ●     ●     ●     ●
       1       ●     ●     ●     ●
       10      ●     ●     ●     ●
       100     ●     ●     ●     ●
```

Each `●` is one model fit (or, with cross-validation, $k$ model fits). The grid is the Cartesian product of the per-axis grids. The algorithm is: visit every point, evaluate, sort, pick the best.

For low-dimensional problems, this is genuinely the right tool. So why is grid search considered obsolete in modern ML practice?

Two answers, both of which we will develop carefully in this chapter:

1. **In high dimensions, the grid explodes faster than your budget grows.**
2. **Even at the right size, the grid wastes most of its evaluations exploring directions that don't matter.**

The first is obvious arithmetic. The second is the Bergstra-Bengio insight that we will preview here and treat in full in Ch 50.

---

## 49.2 The algorithm, written out

The algorithm is two lines of pseudocode, but let's write it carefully because the details matter when we get to model-fit counting.

```
Input:
    - Per-hyperparameter grids G_1, G_2, ..., G_d
      (each G_j is a list of candidate values for hyperparameter j)
    - Cross-validation scheme (k-fold, say)
    - Inner training procedure A
    - Validation metric M

Procedure:
    candidates = G_1 × G_2 × ... × G_d            # Cartesian product
    for theta in candidates:
        cv_scores = []
        for fold in 1..k:
            train_fold, val_fold = split(data, fold)
            model = A(train_fold, theta)
            cv_scores.append(M(model, val_fold))
        record(theta, mean(cv_scores))
    best_theta = argmax over recorded (theta, mean)
    final_model = A(all_train_data, best_theta)
    return final_model, best_theta
```

The number of candidates is $|G_1| \cdot |G_2| \cdots |G_d| = \prod_{j=1}^d |G_j|$. With 5-fold CV, the total number of model fits inside the HPO loop is $k \cdot \prod_j |G_j|$. Add one for the final refit, and we have the master formula:

$$
\text{total\_fits} = k \cdot \prod_{j=1}^{d} |G_j| \; + \; 1.
$$

This formula is worth committing to muscle memory. Most exam questions on "how many models will be trained" reduce to plugging numbers into it.

### 49.2.1 The 6×3+1 = 19 formula

Here is the most quoted version of the formula in Spark ML practice. Suppose you have a `CrossValidator` with `numFolds = 3` wrapping a `ParamGridBuilder` with two hyperparameter grids of sizes 3 and 2:

```python
paramGrid = (ParamGridBuilder()
    .addGrid(rf.numTrees,  [50, 100, 200])     # size 3
    .addGrid(rf.maxDepth,  [5, 10])             # size 2
    .build())                                    # total 6 ParamMaps

cv = CrossValidator(estimator=rf,
                    estimatorParamMaps=paramGrid,
                    numFolds=3)                  # k = 3
```

How many model fits will Spark do?

- 6 hyperparameter configurations (the Cartesian product)
- 3 folds each → $6 \times 3 = 18$ fits inside the CV loop
- 1 final refit on the entire training data at the best configuration

**Total: $6 \times 3 + 1 = 19$ fits.**

The 19 is famous because it shows up on the Databricks ML Associate exam in a variety of disguised forms. Variations:

- "ParamGridBuilder with three axes of sizes 4, 3, 2; 5-fold CV." → $4 \cdot 3 \cdot 2 = 24$ configs × 5 folds = 120 + 1 = 121.
- "TrainValidationSplit instead of CrossValidator with 6 configs." → TrainValidationSplit uses a single train/val split (not $k$ folds), so it's $6 \times 1 + 1 = 7$ fits.
- "ParamGridBuilder with no grid added (empty)." → 1 config × $k$ folds + 1 = $k + 1$.

The principle is always the same. Multiply the grid size by the number of folds, add one for the refit. The formula doesn't change.

### 49.2.2 Parallelism

Spark's `CrossValidator` accepts a `parallelism` parameter (and so does `TrainValidationSplit`). Setting `parallelism = 4` means up to 4 of the inner model fits can run concurrently as separate Spark jobs. This does not change the *total number* of fits — it changes the wall-clock time. With 19 fits and `parallelism = 4`, ignoring scheduling overhead, you'd expect about $\lceil 19 / 4 \rceil = 5$ rounds of fits. (In practice it's messier because fits have different durations.)

A subtle point: parallelism makes Spark schedule more fits at once, which consumes more cluster cores. If your cluster has 16 cores and a single fit uses 4 cores, you have 4 effective slots. Setting `parallelism = 8` doesn't help — there isn't room. The right setting is roughly `cluster_cores / cores_per_fit`.

We will return to this in Ch 53 where we discuss SparkTrials's parallelism, which is the same idea applied to Hyperopt.

---

## 49.3 A worked numerical example

Let's do a small grid search by hand, with real arithmetic, to make sure the procedure is concrete.

We have 1000 training examples for a binary classification problem. We want to tune a gradient-boosted tree with two hyperparameters: `learning_rate ∈ {0.01, 0.1, 0.5}` and `n_estimators ∈ {50, 100, 200}`. Nine combinations. We use 5-fold CV.

For each combination, we train the model on 800 examples (4 folds of 200) and evaluate on the remaining 200. We repeat for all 5 folds and take the mean validation F1.

Suppose the per-fold validation F1 numbers look like this (fabricated but plausible):

| `learning_rate` | `n_estimators` | F1 fold 1 | F1 fold 2 | F1 fold 3 | F1 fold 4 | F1 fold 5 | Mean F1 |
|----:|----:|----:|----:|----:|----:|----:|----:|
| 0.01 |  50 | 0.71 | 0.69 | 0.72 | 0.70 | 0.71 | **0.706** |
| 0.01 | 100 | 0.78 | 0.76 | 0.79 | 0.77 | 0.78 | **0.776** |
| 0.01 | 200 | 0.83 | 0.81 | 0.82 | 0.84 | 0.82 | **0.824** |
| 0.10 |  50 | 0.82 | 0.81 | 0.83 | 0.80 | 0.82 | **0.816** |
| 0.10 | 100 | 0.85 | 0.84 | 0.86 | 0.85 | 0.84 | **0.848** |
| 0.10 | 200 | 0.86 | 0.85 | 0.87 | 0.85 | 0.86 | **0.858** |
| 0.50 |  50 | 0.79 | 0.78 | 0.80 | 0.77 | 0.79 | **0.786** |
| 0.50 | 100 | 0.80 | 0.79 | 0.81 | 0.78 | 0.80 | **0.796** |
| 0.50 | 200 | 0.80 | 0.79 | 0.81 | 0.79 | 0.80 | **0.798** |

Total fits: $9 \times 5 = 45$ inner fits + 1 final refit = **46** total.

Reading the column of means: the best configuration is `learning_rate = 0.10, n_estimators = 200` with F1 = 0.858. Train a final model at those settings on all 1000 examples and you have your shipped model.

The structure of the results is also informative:

- At `learning_rate = 0.01`, F1 keeps rising as `n_estimators` increases — we haven't yet trained enough trees. We should probably try `n_estimators = 500` to see if it keeps improving.
- At `learning_rate = 0.5`, F1 is mediocre and plateaus quickly — the high learning rate is causing the model to overshoot good minima and not improve with more trees.
- At `learning_rate = 0.1`, we are clearly in the sweet spot.

This is the kind of thing you learn *from looking at the full table*, not from "the best one." Grid search has the virtue of producing this informative tableau. Random search does not (the grid is not aligned, so you can't read off "what happens as I vary one axis at a time"). Bayesian optimization does even less of this — the samples are non-uniform on purpose, so individual-axis trends are obscured. The legibility of grid results is one underrated reason it persists.

### 49.3.1 The "wrong levels" problem

Now look at the table again. Suppose the true optimal `learning_rate` is 0.07 (not 0.1, not 0.01). And the true optimal `n_estimators` is 350 (not 200, not 100). Your grid will *never find these values*. You will report the best of `{0.01, 0.1, 0.5} × {50, 100, 200}` as if it were the answer to "what is the best configuration?", when really it's the answer to a much narrower question: "among these nine specific configurations, which is best?"

This is the **wrong-levels problem**. The grid is only as good as the levels you put on it.

You can address this with a **two-pass refinement**: do a coarse grid first, then a finer grid centered around the best point from the coarse pass.

Pass 1 (coarse, as above): best is `(0.1, 200)` with F1 = 0.858.  
Pass 2 (refined): `learning_rate ∈ {0.05, 0.075, 0.1, 0.15, 0.2}`, `n_estimators ∈ {150, 250, 350, 500}` — 5 × 4 = 20 new configurations.

The two-pass approach is reasonable but has two issues:

1. **It doesn't help in high dimensions.** Each pass still scales as $\prod_j |G_j|$, and the second pass has the same dimensionality as the first.
2. **It commits you to a region early.** The coarse pass might pick a local minimum that is worse than another local minimum the coarse grid happened to miss. By refining around the coarse-pass best, you exclude the un-explored region forever.

A defensible practice for very low-dimensional problems (1–2 hyperparameters): start coarse, refine. For anything higher-dimensional, don't bother — use random search or TPE instead.

---

## 49.4 Why grid search breaks in higher dimensions

We have alluded to this but let's make it concrete.

Suppose you want to tune the 8 main XGBoost hyperparameters: `learning_rate`, `n_estimators`, `max_depth`, `min_child_weight`, `subsample`, `colsample_bytree`, `gamma`, `reg_lambda`. With 5 levels per hyperparameter — a respectable but not extravagant grid — you have

$$
5^8 = 390{,}625 \text{ configurations.}
$$

With 5-fold CV, that is just under 2 million fits. At 1 minute per fit, that's 4 years of compute on a single machine. Even with 100-fold parallelism, it's 14 days.

You don't have 14 days. You have 24 hours.

Even worse: 5 levels per hyperparameter is not enough. For a continuous hyperparameter on a wide range (`learning_rate ∈ [1e-5, 1e-1]`), 5 levels means you sample 5 points across 5 orders of magnitude. The optimal value, if it lies between any two of your levels, is invisible to you.

For higher-dimensional HPO, grid search has a curse-of-dimensionality problem so severe that *no practitioner uses it*. The grids you can afford are too coarse; the grids that would be fine-grained enough are too large. Random search and TPE escape this by not even trying to cover the space — they sample stochastically and rely on the geometry of the loss surface to converge anyway.

### 49.4.1 The "most hyperparameters don't matter" insight

There is a deeper reason grid search is wasteful, due to Bergstra and Bengio (2012), which we will treat at length in Ch 50. The preview:

In most real models, only a few hyperparameters strongly affect the validation loss. The others matter less or not at all. For an XGBoost model on tabular data, the "important" hyperparameters are typically `learning_rate`, `n_estimators`, `max_depth` — about three. The other five mostly don't move the needle much.

But you don't know in advance *which three matter*. So you tune all eight.

Grid search treats all axes equally — it spends the same number of distinct values along the dead axes as the live axes. That's the waste. If `gamma` doesn't matter, then every value of `gamma` in the grid produces essentially the same F1 score, and the 5 distinct values you sampled along the `gamma` axis are no better than 1 distinct value would have been. The other 4 levels were burned.

Random search avoids this. Because samples are drawn uniformly, every sample has a *different* value of each hyperparameter. With 25 random samples, you have 25 distinct values of *every* hyperparameter, including the important ones. With 25 grid samples on a 2D grid, you have $\sqrt{25} = 5$ distinct values of each. If only one matters, grid samples 5 distinct values of the important one; random samples 25.

We will derive this rigorously in Ch 50. For now, internalize: **grid search assumes all hyperparameters are equally important. They are not. Therefore grid search wastes evaluations.**

---

## 49.5 When grid search is still defensible

It's not all bad. Grid search has genuine virtues that make it the right tool for a few specific situations.

**Very low dimension (1–2 hyperparameters).** With 1 or 2 hyperparameters, grid search is fine. You can afford a 10-level or 15-level grid per axis. The grid is small. The wrong-levels problem can be addressed with a quick second pass. There is no compelling reason to use random search here.

**Reproducibility under audit.** Grid search is deterministic (no random seeds). The same grid, run twice, produces the same results. For regulated environments — finance, healthcare — where you might be asked to justify why you chose a particular configuration, "I ran a grid over these exact points" is a clean answer. Random search's "I sampled uniformly from this distribution" is also defensible but less concrete to a non-technical reviewer.

**Parallel-bounded settings.** If you have, say, 32 parallel workers and a fixed wall-clock budget, you might as well throw all 32 workers at a 32-cell grid. The lack of sequential dependency in grid search means you get full parallelism with no overhead. Random search has the same property. Bayesian optimization, by contrast, is harder to parallelize cleanly (Ch 51) because each suggestion depends on past observations.

**Categorical or discrete-only hyperparameters with small cardinality.** If your only hyperparameters are something like `solver ∈ {"lbfgs", "saga", "newton-cg"}` and `penalty ∈ {"l1", "l2", "elasticnet"}`, you have a 9-cell grid. Just run it.

**Pyspark.ml's idiomatic API uses ParamGridBuilder.** The pyspark.ml ecosystem is structured around grid-style HPO. The default `CrossValidator` takes a `ParamGridBuilder` output. Hyperopt-on-Spark (SparkTrials, Ch 53) is the modern alternative, but a lot of legacy Databricks notebooks use the grid pattern, and the exam tests it. Knowing the grid pattern is non-negotiable for the exam.

---

## 49.6 The pyspark.ml `ParamGridBuilder` pattern

Since the exam tests this pattern specifically, let's walk through it with code.

```python
from pyspark.ml import Pipeline
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
from pyspark.ml.feature import VectorAssembler

# (Assume df has columns "feature1", "feature2", ..., "label")

assembler = VectorAssembler(inputCols=["feature1", "feature2"], outputCol="features")
rf = RandomForestClassifier(labelCol="label", featuresCol="features")

pipeline = Pipeline(stages=[assembler, rf])

# Build the grid: 3 numTrees × 2 maxDepth = 6 configurations
paramGrid = (ParamGridBuilder()
    .addGrid(rf.numTrees, [50, 100, 200])
    .addGrid(rf.maxDepth, [5, 10])
    .build())

evaluator = BinaryClassificationEvaluator(labelCol="label", metricName="areaUnderROC")

cv = CrossValidator(
    estimator=pipeline,
    estimatorParamMaps=paramGrid,
    evaluator=evaluator,
    numFolds=3,
    parallelism=2,   # up to 2 fits run concurrently
    seed=42
)

cv_model = cv.fit(df)
```

What happens when you call `cv.fit(df)`:

1. Spark splits `df` into 3 folds.
2. For each of the 6 configurations in `paramGrid`, Spark trains the pipeline (assembler + random forest) on 2 folds and evaluates on the held-out fold. Repeat for each of the 3 fold-assignments.
3. With `parallelism = 2`, up to 2 of these (configuration, fold) jobs can run at once.
4. Spark averages the 3 fold scores per configuration to get a mean validation AUC.
5. Spark picks the configuration with the highest mean AUC.
6. Spark refits the pipeline at that configuration on the full input DataFrame.
7. `cv_model` is the final fitted pipeline, ready to call `.transform(test_df)` on.

Total fits: $6 \times 3 + 1 = 19$.

You can inspect:

- `cv_model.avgMetrics` — array of 6 mean AUC values, one per configuration, in the order they appear in `paramGrid`.
- `cv_model.bestModel` — the pipeline trained at the best configuration on all training data.
- `cv_model.getEstimatorParamMaps()[i]` — the actual hyperparameter dictionary for configuration `i`.

The exam loves to ask: "Given this code, how many models are trained?" The answer is always derived from the formula in Section 49.2. Memorize the pattern.

### 49.6.1 TrainValidationSplit — the lighter alternative

`pyspark.ml` also exposes `TrainValidationSplit`, which does the same thing but with a single train/val split instead of $k$-fold CV. With 6 configurations and an 80/20 split:

- 6 fits inside the validation loop (each config trained on 80% of data, evaluated on 20%).
- 1 final refit on all training data.
- Total: **7 fits**.

`TrainValidationSplit` is faster but noisier — single splits have higher variance than $k$-fold averages. Use it when data is plentiful (so a single 20% holdout is statistically reliable) and time is short. The exam will sometimes set up a `TrainValidationSplit` scenario specifically to test that you know it doesn't multiply by $k$.

---

## 49.7 The scikit-learn equivalent

For completeness, the sklearn version of grid search:

```python
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestClassifier

param_grid = {
    "n_estimators": [50, 100, 200],
    "max_depth":    [5, 10]
}

grid = GridSearchCV(
    estimator=RandomForestClassifier(random_state=42),
    param_grid=param_grid,
    cv=3,
    scoring="roc_auc",
    n_jobs=-1   # use all CPU cores
)

grid.fit(X_train, y_train)

print(grid.best_params_)          # e.g., {"n_estimators": 200, "max_depth": 10}
print(grid.best_score_)           # mean CV AUC at best params
best_model = grid.best_estimator_  # already refit on the full training data
```

The behavior is identical to the Spark version. `n_jobs=-1` says use all cores; this is sklearn's analog of Spark's `parallelism`. The total fits formula is the same: $6 \times 3 + 1 = 19$.

The `cv_results_` dictionary is more verbose than Spark's `avgMetrics` — sklearn gives you per-fold scores, fit times, and so on. For analysis, sklearn's results are easier to slice; for production scale, Spark's parallelism is better.

---

## 49.8 Engineering tradeoffs

A few practical notes that don't fit cleanly elsewhere:

**Refit cost is small.** That `+1` in the formula is one fit on the full training data. People sometimes treat it as negligible, but it can be the biggest single fit in the whole HPO — because it's on all data, not just a fold. Be aware of it for time budgeting.

**Failed configurations.** If a configuration causes the training to crash (e.g., `max_depth=1000000` runs out of memory, or `learning_rate=0` produces a numerical error), your HPO loop should handle it. Spark's `CrossValidator` doesn't have a clean failure-skip mechanism (it tends to throw and abort). Hyperopt has `STATUS_FAIL` (Ch 53). Optuna has `TrialState.FAIL` (Ch 54). With grid search you'd want to wrap each fit in try/except and record a sentinel "infinite loss" for failures.

**Reproducibility seeds.** If your model is stochastic (random forests, neural nets), set a seed and include it in the configuration (or fix it globally). Two grid runs with different seeds will produce slightly different rankings, especially at the noise floor. Pick the convention and stick with it.

**Picking grid levels well.** A grid is only as good as the levels you choose. For continuous hyperparameters on a wide range:
- Use a *log scale* for `learning_rate`, regularization strengths, batch sizes — quantities that span orders of magnitude.
- Use a *linear scale* for `subsample`, `colsample_bytree`, dropout rates — quantities between 0 and 1.
- Use rough powers of 2 for `n_estimators`, `max_iter`, `n_neighbors` — quantities where you care about relative size more than absolute.

For categorical hyperparameters: include all of them, since there's no interpolation between, say, `kernel="linear"` and `kernel="rbf"`.

---

## 49.9 What this builds on / where this returns

**Builds on:**

- *Chapter 48* — the HPO problem formulation and the cost arithmetic.
- *Chapter 22* — cross-validation, the inner loop of every grid search evaluation.

**Returns in:**

- *Chapter 50* — random search and Bergstra-Bengio. Grid search is the foil we will compare against.
- *Chapter 53* — Hyperopt offers `rand.suggest` as the random-search baseline, which is grid search's natural successor.
- *Chapter 65* — `CrossValidator` and `TrainValidationSplit` in pyspark.ml in depth. The model-fit counting from this chapter is exam-ready there.

---

## 49.10 Exercises

1. **Basic counting.** A `ParamGridBuilder` adds three grids of sizes 4, 3, and 2. A `CrossValidator` wraps it with `numFolds = 5`. How many model fits total?

2. **TrainValidationSplit counting.** Same grid as Q1, but with `TrainValidationSplit` (single train/val split, `trainRatio = 0.8`) instead of `CrossValidator`. How many fits?

3. **Empty grid.** A `ParamGridBuilder().build()` is passed (no `addGrid` calls). With a 5-fold `CrossValidator`, how many fits? What does this evaluate?

4. **Refit cost.** A grid produces 50 configurations × 5 folds = 250 fits. Each fold uses 80% of the data; the final refit uses 100% of the data. If a single fold-fit takes 60 seconds, roughly how long does the refit take, and what fraction of total HPO time is the refit?

5. **Wrong levels.** You grid-search `min_samples_leaf ∈ {1, 5, 10, 20}` for a random forest. The true optimum is 3. You report `min_samples_leaf = 5` as the best from your search. How could you tell, from the grid output, that you might be missing a better value? Outline a second-pass refinement.

6. **High-dimension grid math.** You want to grid-search XGBoost with 8 hyperparameters at 4 levels each, with 5-fold CV. On a cluster with 32 parallel workers where each fit takes 90 seconds, how long would this take in wall-clock time, assuming perfect parallelism?

7. **`parallelism` choice.** Your Spark cluster has 24 cores. Your `RandomForestClassifier` fit uses 6 cores per fit. You're running a `CrossValidator` with 12 configurations and 4 folds. What's a reasonable value for `parallelism`? Why is `parallelism = 12` wrong?

8. **Reading `avgMetrics`.** After fitting a `CrossValidator` you call `cv_model.avgMetrics` and see `[0.81, 0.84, 0.79, 0.85, 0.83, 0.82]`. The `ParamGridBuilder` was built with `.addGrid(rf.numTrees, [50, 100]).addGrid(rf.maxDepth, [5, 10, 20])`. Which `(numTrees, maxDepth)` configuration scored best? (Hint: the ordering of `avgMetrics` matches the order configurations were generated by `ParamGridBuilder`.)

9. **Coarse-then-fine.** You have a budget for 100 fits (1-fold validation, no CV). Two hyperparameters, both continuous. Design a two-pass grid: pass 1 coarse, pass 2 fine. What's a reasonable split of the budget?

10. **The lever question.** Your boss says: "I want you to tune 15 hyperparameters of our deep learning model. Use grid search." How do you respond? What's the actual answer to the underlying question?

11. **Tradeoff with budget.** You have 30 minutes of compute. A single fit takes 1 minute. With a 2D grid and 5-fold CV, what's the largest grid you can afford? What if you switched to 3-fold CV?

12. **Categorical-only grid.** Your only hyperparameters are `solver ∈ {"lbfgs", "saga", "newton-cg"}`, `penalty ∈ {"l1", "l2"}`, `multi_class ∈ {"auto", "ovr", "multinomial"}`. Some combinations are invalid (`l1` doesn't work with `lbfgs`, for instance). With 5-fold CV, how many fits would naive grid search attempt, and how do you handle invalid combinations?

<details>
<summary>Answers</summary>

1. $4 \times 3 \times 2 = 24$ configs × 5 folds + 1 refit = **121 fits**.

2. 24 configs × 1 (single validation split) + 1 refit = **25 fits**. The `trainRatio` is irrelevant to the count.

3. 1 config × 5 folds + 1 refit = **6 fits**. With an empty grid, the "configuration" is the estimator's default hyperparameters; you are essentially doing a cross-validated evaluation of the default settings (no tuning).

4. The refit uses 1/0.8 = 1.25× the data, so it takes roughly $60 \times 1.25 = 75$ seconds. Total HPO time = 250 × 60 + 75 = 15075 seconds. Refit fraction: $75 / 15075 \approx 0.5\%$. Refit cost is negligible at this budget but becomes more significant for small grids.

5. The output around `min_samples_leaf = 5` should show F1 declining as you move to 10 and 20, and (if you also tried 1) you'd see F1 also slightly worse at 1 than at 5 — suggesting an interior optimum near 5. The refinement: a second pass with `min_samples_leaf ∈ {2, 3, 4, 5, 6, 7, 8}` to find the local peak.

6. $4^8 = 65{,}536$ configs × 5 folds = 327,680 fits + 1. At 90s per fit, that's $327{,}681 \times 90 = 29{,}491{,}290$ seconds of work. With 32 workers in perfect parallelism: $29{,}491{,}290 / 32 \approx 921{,}603$ seconds $\approx 10.7$ days. This is the curse of dimensionality concretely — almost two weeks of perfect parallelism to tune a single model. Don't grid-search 8 hyperparameters.

7. With 24 cores total and 6 cores per fit, you have 4 concurrent fit slots. So `parallelism = 4`. Setting `parallelism = 12` would queue up 12 fits but Spark would only actually run 4 at a time — the other 8 wait. You'd consume the same wall-clock time but with more scheduling overhead.

8. The order from `ParamGridBuilder` typically iterates the last-added axis fastest. With `numTrees` added first and `maxDepth` added second, the iteration order is: (50, 5), (50, 10), (50, 20), (100, 5), (100, 10), (100, 20). Best metric 0.85 is the 4th entry → **(numTrees=100, maxDepth=5)**. (Caveat: confirm with `cv_model.getEstimatorParamMaps()[3]` in practice.)

9. Pass 1 (coarse): a 10×10 grid = 100 fits. That uses up all the budget — too much. Reduce. Pass 1: 7×7 = 49 fits. Pass 2: a finer 7×7 grid in the neighborhood of the best point from pass 1 = another 49 fits. Total: 98 fits. Leaves a small reserve for the final refit. Alternative split: pass 1: 5×5 = 25; pass 2: 9×9 = 81; total 106 — slightly over budget. Use $5 \times 5 + 8 \times 8 = 25 + 64 = 89$ for a more conservative budget.

10. Push back. Grid search over 15 hyperparameters at any meaningful resolution is impractical (with just 3 levels each, that's 14M configurations). The actual answer: use random search or, better, TPE (Hyperopt/Optuna) with $N$ in the hundreds. Push back on the manager and explain dimensionality. If they insist on grid search, suggest tuning only the 3–5 most impactful hyperparameters and fixing the others to sensible defaults.

11. With 5-fold CV: $5 \cdot G + 1 \leq 30$, so $G \leq 5.8$, meaning at most 5 grid cells. A 2×2 grid (4 cells) fits in 21 minutes — your tightest option. With 3-fold CV: $3 \cdot G + 1 \leq 30$, so $G \leq 9.67$, meaning up to 9 grid cells. A 3×3 grid fits in 28 minutes. The trade is more configurations vs more reliable per-config estimates; for small budgets, 3-fold CV is the usual choice.

12. Naive grid: $3 \times 2 \times 3 = 18$ configs × 5 folds + 1 = 91 fits. To handle invalid combinations: either filter them out before passing to `CrossValidator` (sklearn's `GridSearchCV` does this with a list of param_grids; pyspark.ml does not have a clean equivalent — you'd compute the valid Cartesian product manually) or catch exceptions in the inner loop and assign a sentinel bad score. The second is fragile. Better: use `param_grid = [{...lbfgs-valid...}, {...saga-valid...}, ...]` and let the framework iterate the union.

</details>
