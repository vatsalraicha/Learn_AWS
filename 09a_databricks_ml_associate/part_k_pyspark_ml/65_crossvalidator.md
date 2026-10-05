# Chapter 65 — CrossValidator and TrainValidationSplit: With Model-Count Math

> **Goal of this chapter:** to teach the two `pyspark.ml.tuning` classes you will encounter on every real project and on every exam — `CrossValidator` and `TrainValidationSplit` — and to make absolutely sure you can compute *how many models a CV run trains* in your head, given a grid size and a fold count. The model-count formula is the single most exam-tested arithmetic in this curriculum, and it is also the most useful sanity check for "is this going to finish in time?" on a real job.

---

## 65.1 Why this chapter exists

In Chapter 22 you learned cross-validation as a *theoretical idea*: split training data into $k$ folds, hold out each in turn, train on the other $k-1$, evaluate on the held-out fold, average the metric across folds. In Chapter 49 you learned grid search as a *theoretical idea*: enumerate the Cartesian product of hyperparameter values, evaluate each, pick the best.

Now we do them together, on Spark, in production. `pyspark.ml.tuning.CrossValidator` is the API that wraps both ideas into one Estimator. Calling `.fit` runs the whole machinery: for each grid combination, run $k$-fold CV; pick the best combination by average metric; refit on the full training set with the best combination; return a `CrossValidatorModel` whose `.bestModel` is the production-ready Transformer.

There are three things you need to walk away knowing:

1. **The model-count formula** — given a grid of size $G$ and $F$ folds, how many models does CV train? (Answer: $G \times F + 1$. We will derive and rehearse this.)
2. **The wiring** — how `ParamGridBuilder`, `CrossValidator`, the Pipeline, and the Evaluator click together.
3. **When to use `TrainValidationSplit` instead** — and the slightly different model-count math that implies.

We will also spend a careful section on `parallelism` because the math of "how long this will take wall-clock" depends on it as much as on the model count.

---

## 65.2 Building the grid: `ParamGridBuilder`

The grid is a list of `ParamMap` objects, each one a specific assignment of hyperparameters. You build it with `ParamGridBuilder`:

```python
from pyspark.ml.tuning import ParamGridBuilder
from pyspark.ml.classification import LogisticRegression

lr = LogisticRegression(featuresCol="features", labelCol="label")

grid = (ParamGridBuilder()
        .addGrid(lr.regParam, [0.0, 0.01, 0.1, 1.0])
        .addGrid(lr.elasticNetParam, [0.0, 0.5, 1.0])
        .build())

print(len(grid))   # 4 * 3 = 12
```

Each call to `.addGrid` adds an axis to the Cartesian product. `.build()` materialises the list of `ParamMap`s — 12 of them in this case, one for every combination of `(regParam, elasticNetParam)`:

```
{regParam=0.0,  elasticNetParam=0.0}
{regParam=0.0,  elasticNetParam=0.5}
{regParam=0.0,  elasticNetParam=1.0}
{regParam=0.01, elasticNetParam=0.0}
{regParam=0.01, elasticNetParam=0.5}
{regParam=0.01, elasticNetParam=1.0}
... (12 total)
```

You can also use `.baseOn({ ... })` to lock parameters that are fixed across the whole grid (less common in practice).

Note that the grid axes refer to *the actual parameter object on the Estimator*: `lr.regParam`, not the string `"regParam"`. This is how the CrossValidator later knows which stage of which Pipeline to inject the value into. If your `lr` is inside a Pipeline of 5 stages, the grid will still target the `lr` stage specifically because the parameter reference points to it.

### 65.2.1 Cross-stage grids

A common pattern: tune both feature-engineering hyperparameters and model hyperparameters jointly. For example, tune the `numFeatures` of `HashingTF` *and* the `regParam` of `LogisticRegression` in the same grid:

```python
from pyspark.ml.feature import HashingTF

htf = HashingTF(inputCol="filtered", outputCol="raw_features")
lr  = LogisticRegression(featuresCol="features", labelCol="label")
# Pipeline assembled with htf, idf, lr stages

grid = (ParamGridBuilder()
        .addGrid(htf.numFeatures, [5000, 10000, 20000])
        .addGrid(lr.regParam,     [0.01, 0.1, 1.0])
        .build())

print(len(grid))   # 3 * 3 = 9
```

This is the *right* way to tune feature-engineering hyperparameters: jointly with model hyperparameters, under cross-validation. If you tune `numFeatures` in isolation outside the CV loop, you risk picking a value that overfits the held-out evaluation, and you also pay $G \times F$ extra trainings for nothing.

---

## 65.3 The CrossValidator: assembling the pieces

```python
from pyspark.ml.tuning import CrossValidator
from pyspark.ml.evaluation import BinaryClassificationEvaluator

evaluator = BinaryClassificationEvaluator(labelCol="label",
                                          rawPredictionCol="rawPrediction",
                                          metricName="areaUnderROC")

cv = CrossValidator(
    estimator=pipeline,            # any Estimator — typically a Pipeline
    estimatorParamMaps=grid,       # the list from ParamGridBuilder
    evaluator=evaluator,           # the metric to optimise
    numFolds=5,                    # k in k-fold
    parallelism=4,                 # how many fits to run concurrently
    seed=42,
    collectSubModels=False,        # default; True would keep every fold's model
)

cv_model = cv.fit(train_df)
```

Four pieces clicked together:

- The **estimator** is what gets fit on each fold. Usually a `Pipeline`. Crucially, when a grid value targets a stage *inside* the pipeline, the entire pipeline (all stages, fitted from scratch) is re-fit for that grid combination on that fold. This is the leakage-protection property from Chapter 62: feature-engineering Estimators re-fit on each fold's training portion.
- The **grid** is the list of `ParamMap`s to evaluate.
- The **evaluator** is the metric — Chapter 66 covers the three Evaluator classes in detail.
- **numFolds** is the $k$ in k-fold; **parallelism** is wall-clock-speed knob; **seed** is the fold-shuffling random seed; **collectSubModels** is whether to keep all sub-models for later inspection (memory-expensive; usually leave `False`).

### 65.3.1 What `cv.fit(train_df)` actually does

Let's spell out the loop. With grid size $G$ and fold count $F$:

```
Split train_df into F folds (stratified for classification by default? -- no,
  pyspark.ml's CrossValidator does a plain random split; if you need stratification,
  do it upstream).

best_avg_metric = -infinity
best_param_map = None
avg_metrics = []

For each param_map in grid:                          # G iterations
    metrics_this_param_map = []
    For each fold_i in 0..F-1:                       # F iterations per param_map
        train_fold = union of all folds except fold_i
        val_fold   = fold_i
        # APPLY the param_map to estimator's parameters
        # FIT the estimator on train_fold
        model_i = estimator.fit(train_fold, params=param_map)
        # EVALUATE on val_fold
        preds = model_i.transform(val_fold)
        metric_i = evaluator.evaluate(preds)
        metrics_this_param_map.append(metric_i)
    avg = mean(metrics_this_param_map)
    avg_metrics.append(avg)
    if avg > best_avg_metric:
        best_avg_metric = avg
        best_param_map = param_map

# After all G*F model trainings, do ONE MORE training:
# refit on the FULL training data with the best param_map.
final_model = estimator.fit(train_df, params=best_param_map)

return CrossValidatorModel(bestModel=final_model,
                           avgMetrics=avg_metrics,
                           ...)
```

Pause and count the `estimator.fit` calls. There are $G \times F$ inside the double loop, plus 1 at the end. That gives us:

### 65.3.2 The model-count formula

$$
\boxed{\text{number of trainings} = G \cdot F + 1}
$$

where $G$ is the number of `ParamMap`s in the grid and $F$ is `numFolds`.

This is *the* formula. It will appear on the exam. It will appear in conversations with your team lead when you propose a CV run. It will appear in your budget meetings.

Some quick worked examples to lock it in:

- 4 grid combinations × 5 folds: $4 \times 5 + 1 = 21$ trainings.
- 6 grid combinations × 3 folds: $6 \times 3 + 1 = 19$ trainings.
- A grid of $\{regParam = [0.01, 0.1, 1], maxIter = [50, 100]\}$ × 5 folds: $(3 \times 2) \times 5 + 1 = 31$ trainings.
- 12 grid combinations × 10 folds: $12 \times 10 + 1 = 121$ trainings.

If each training of your model takes 3 minutes, a 121-training CV is about 6 hours of wall-clock work (sequentially — see `parallelism` below).

### 65.3.3 Why the "+1" matters

The $+1$ is the final refit on the full training set with the chosen hyperparameters. It is *not* optional and it is *not* one of the cross-validated models. It exists because the cross-validated models are each fit on $\frac{k-1}{k}$ of the data, which means none of them has seen the full training set. The final model — the one you actually ship — is the one trained on everything.

Some people get confused and write $G \times F$, dropping the +1. The exam may be looking for either, but the right answer with the final refit is $G \times F + 1$. If a question asks specifically "how many *cross-validation* trainings", the answer is $G \times F$; if it asks "how many models does CrossValidator fit *in total*", the answer is $G \times F + 1$. Read carefully.

A useful mnemonic: **"every cell in the G-by-F grid, plus the champion takes one more victory lap."**

---

## 65.4 The parallelism knob

The model-count tells you how many trainings happen. It does *not* tell you how long they take wall-clock — that depends on whether they run sequentially or concurrently.

By default, `parallelism=1`: all $G \times F + 1$ trainings run sequentially. This is the safe default — no two models compete for the same executors. With a 30-minute model and 121 trainings, that's 60 hours of wall-clock work. Painful.

`parallelism=N` runs up to $N$ trainings concurrently. Each trained model takes the same amount of CPU work; what changes is whether they overlap.

```python
cv = CrossValidator(estimator=pipeline, estimatorParamMaps=grid, evaluator=evaluator,
                    numFolds=5, parallelism=4)
```

Things to think about when setting `parallelism`:

1. **Concurrent models compete for cluster resources.** Each model trains on Spark workers. If you have 16 executor cores and 4 concurrent trainings, each training has 4 cores. Setting `parallelism` too high can make each individual training *slower* by starving it of resources, so the wall-clock benefit shrinks (or inverts).
2. **The fold and grid axes are both parallelizable.** `parallelism` is over the cross product of (grid, fold) pairs — any subset of those $G \times F$ pairs can run in parallel.
3. **The final refit (the +1) is not parallelizable with the others.** It only starts after the best param_map is known. So even with `parallelism=infinity`, total wall time is at least one CV-fold-training plus one full-refit-training.
4. **A good rule of thumb is `parallelism ≤ executor count`.** Or more carefully: `parallelism` × cores-per-training ≤ total executor cores. Otherwise you over-subscribe.

For a small project on Databricks Community Edition, leave parallelism at 1 (or 2). For a serious production CV run on a 16-core cluster, `parallelism=4` is reasonable.

---

## 65.5 What `CrossValidatorModel` gives you

After `cv_model = cv.fit(train_df)` returns, you have:

```python
cv_model.bestModel        # the final-refit model (a Transformer)
cv_model.avgMetrics       # list of length G with the avg metric per grid combination
cv_model.subModels        # if collectSubModels=True; otherwise None
```

`bestModel` is what you want to ship. It is the result of the +1 refit, with the best `ParamMap` applied. Call `.transform(test_df)` on it to predict.

`avgMetrics` is your CV table. The $i$-th entry corresponds to the $i$-th `ParamMap` in your grid. You can pair them up to see which combination won and by how much:

```python
for params, metric in zip(grid, cv_model.avgMetrics):
    print(metric, params)
```

`subModels[i][j]` (if collected) is the model trained for grid combination $i$ on fold $j$. Useful for diagnostics — looking at variance across folds, e.g., is one fold's performance much worse than the others? But it costs $G \times F$ models in memory, which is rarely worth it.

### 65.5.1 Reading `avgMetrics`

Suppose you ran:

```python
grid = (ParamGridBuilder()
        .addGrid(lr.regParam, [0.0, 0.01, 0.1, 1.0])
        .build())

cv = CrossValidator(estimator=lr, estimatorParamMaps=grid,
                    evaluator=BinaryClassificationEvaluator(metricName="areaUnderROC"),
                    numFolds=3)

cv_model = cv.fit(train_df)
print(cv_model.avgMetrics)
# [0.812, 0.844, 0.871, 0.823]
```

That tells you:

- `regParam=0.0`: average AUROC across 3 folds = 0.812. Too little regularisation — high variance.
- `regParam=0.01`: 0.844. Better.
- `regParam=0.1`: 0.871. Best.
- `regParam=1.0`: 0.823. Too much regularisation — under-fit.

The best model uses `regParam=0.1`. The U-shape in the metric — increasing, peaking, then decreasing — is exactly the bias-variance picture of Chapter 19. The CV machinery picked the sweet spot for you.

Total trainings: $G \times F + 1 = 4 \times 3 + 1 = 13$.

---

## 65.6 TrainValidationSplit: the cheaper cousin

`CrossValidator` is expensive — $G \times F$ trainings is a lot when $F$ is large. Sometimes you don't have the budget. `TrainValidationSplit` is the lower-cost option: instead of $k$ folds, it uses *one* train/validation split.

```python
from pyspark.ml.tuning import TrainValidationSplit

tvs = TrainValidationSplit(
    estimator=pipeline,
    estimatorParamMaps=grid,
    evaluator=evaluator,
    trainRatio=0.75,         # 75% train, 25% val
    parallelism=4,
    seed=42,
)
tvs_model = tvs.fit(train_df)
```

The loop is just:

```
Split train_df into train_part (75%) and val_part (25%).

For each param_map in grid:                    # G iterations
    model = estimator.fit(train_part, params=param_map)
    preds = model.transform(val_part)
    metric = evaluator.evaluate(preds)
    record (param_map, metric)

best_param_map = argmax over metrics
final_model = estimator.fit(train_df, params=best_param_map)
```

Total trainings: $G + 1$. With the same grid that cost you $4 \times 3 + 1 = 13$ trainings under 3-fold CV, you'd pay $4 + 1 = 5$ trainings under TrainValidationSplit.

### 65.6.1 The tradeoff: variance vs. cost

CV gives you a *less noisy* estimate of each grid combination's metric because you average over $k$ folds. With $k=5$, each grid combination's metric is the mean of 5 independent estimates. The standard error of that mean is $\sigma / \sqrt{5}$ where $\sigma$ is the per-fold noise.

TrainValidationSplit gives you *one* estimate per grid combination. Standard error is $\sigma$ — no $\sqrt{k}$ reduction. So your ranking of grid combinations is noisier; with a small data set and a tight metric race, you can end up picking the wrong combination simply because that combination got lucky on this one split.

When to pick which:

- **Large dataset (millions of rows), expensive model.** TrainValidationSplit is fine — the one split is already a precise estimate because the validation set is huge.
- **Small dataset, fast model.** CrossValidator is the right answer — variance matters, cost is small.
- **Medium dataset and you're prototyping.** Start with TrainValidationSplit to iterate quickly on which hyperparameters to even bother tuning, then switch to CrossValidator for the final tune.

A reasonable practitioner heuristic: if a CV run would take more than half a day of wall clock, replace it with TVS.

### 65.6.2 The pyspark.ml.tuning trio

So far we have:

- `CrossValidator`: $G \times F + 1$ trainings, low-variance metric estimates, high cost.
- `TrainValidationSplit`: $G + 1$ trainings, higher-variance metric estimates, low cost.

There is no `pyspark.ml`-builtin Bayesian optimisation or hyperband; for those, you reach for Hyperopt (with the SparkTrials backend, Chapter 53) or Optuna (Chapter 54). Within the bounds of `pyspark.ml.tuning` proper, these two classes are the entire toolkit.

---

## 65.7 A complete worked example, end to end

Let's run a full CV on a small dataset so you can see every piece in context.

```python
from pyspark.sql import SparkSession
from pyspark.ml import Pipeline
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
from pyspark.ml.evaluation import BinaryClassificationEvaluator
import random

spark = SparkSession.builder.appName("ch65-cv").getOrCreate()
random.seed(42)

# Synthetic dataset: 800 rows, 4 features, binary label
rows = []
for _ in range(800):
    x = [random.gauss(0, 1) for _ in range(4)]
    z = 1.5 * x[0] + 0.7 * x[1] - 0.5 * x[2] + 0.0 * x[3] + random.gauss(0, 0.5)
    label = 1 if z > 0 else 0
    rows.append(x + [label])

df = spark.createDataFrame(rows, ["x0", "x1", "x2", "x3", "label"])
train, test = df.randomSplit([0.8, 0.2], seed=42)

# Pipeline
va  = VectorAssembler(inputCols=["x0", "x1", "x2", "x3"], outputCol="features_raw")
sc  = StandardScaler(inputCol="features_raw", outputCol="features",
                     withMean=True, withStd=True)
lr  = LogisticRegression(featuresCol="features", labelCol="label", maxIter=100)
pipeline = Pipeline(stages=[va, sc, lr])

# Grid: 4 regParam values × 3 elasticNetParam values = 12 combinations
grid = (ParamGridBuilder()
        .addGrid(lr.regParam, [0.0, 0.01, 0.1, 1.0])
        .addGrid(lr.elasticNetParam, [0.0, 0.5, 1.0])
        .build())

# Evaluator
evaluator = BinaryClassificationEvaluator(
    labelCol="label",
    rawPredictionCol="rawPrediction",
    metricName="areaUnderROC",
)

# CrossValidator
cv = CrossValidator(estimator=pipeline,
                    estimatorParamMaps=grid,
                    evaluator=evaluator,
                    numFolds=5,
                    parallelism=2,
                    seed=42)

cv_model = cv.fit(train)
```

Model-count check: $G = 12$, $F = 5$, total = $12 \times 5 + 1 = 61$ pipeline fits. Each pipeline fit includes the StandardScaler refit (because it's an Estimator inside the pipeline) and the LR fit.

After the run:

```python
import numpy as np

idx_best = int(np.argmax(cv_model.avgMetrics))
print("Best grid index:", idx_best)
print("Best avg metric:", cv_model.avgMetrics[idx_best])
print("Best params:", grid[idx_best])

# Evaluate on held-out test data
test_preds = cv_model.transform(test)
test_auroc = evaluator.evaluate(test_preds)
print("Test AUROC:", test_auroc)
```

Expected: the best grid combination uses a small-but-non-zero `regParam` (something like 0.01-0.1) and probably `elasticNetParam=0.0` or `0.5`. The held-out test AUROC will be slightly lower than the best CV AUROC (which is expected — CV averages are slightly optimistic since you picked the best of 12).

The full CV table:

```python
for i, (params, metric) in enumerate(zip(grid, cv_model.avgMetrics)):
    reg = params[lr.regParam]
    en = params[lr.elasticNetParam]
    print(f"  reg={reg:>6}, en={en:>4}  →  AUROC = {metric:.4f}")
```

You will see the metric form a "ridge" — high in the middle of the regParam range, lower at the extremes — and the elastic net dimension will show less sensitivity (because the data is small and the L1/L2 mix doesn't matter much here).

---

## 65.8 Pitfalls

A consolidated trap list:

1. **Forgetting parallelism.** Default `parallelism=1` means strictly sequential. For a 61-fit CV on a non-trivial dataset, you may sit through hours of wall-clock when you could have finished in 20 minutes. Always think about `parallelism`.

2. **Grid combinations that don't apply to the estimator.** If you have `RandomForestClassifier` and you write `.addGrid(rf.regParam, [0.0, 0.1])`, you'll get a `NoSuchElementException` because RF doesn't have a `regParam`. The error is at fit time. Read your estimator's parameters before building the grid.

3. **Stratified folds.** `CrossValidator` does *not* automatically stratify by label. For imbalanced classification, the random folds can produce one fold with no positive examples in it, which is a disaster for both training (some folds may have no positives) and evaluation (AUROC undefined on the no-positives fold). Workarounds: stratify your data into k folds yourself and use TrainValidationSplit per pair, or upsample the minority class upstream.

4. **Excessive memory with `collectSubModels=True`.** Default is False, which discards sub-models after extracting metrics. Setting True keeps $G \times F$ models in memory. For a $4 \times 3 + 1 = 13$-fit CV with a small model, fine. For a $100 \times 10 + 1$ CV with a big RF, you'll OOM.

5. **The Evaluator metric direction.** Pyspark's CV always *maximises* the evaluator metric. For metrics where "lower is better" (like RMSE, log loss), the evaluator returns a value such that higher is still better — for `RegressionEvaluator(metricName="rmse")`, this is unfortunately *not* automatically negated, so you'd need to wrap the evaluator or remember to argmin instead of argmax when reading `avgMetrics`. Actually — let me correct that. In modern pyspark, the evaluator has an `isLargerBetter()` method that the CV respects, so it does the right thing for RMSE (minimise). But the API surface is subtle here; if the CV result looks inverted, this is the suspect.

6. **Mismatched evaluator columns.** Your model produces `rawPrediction`, but you wrote `BinaryClassificationEvaluator(predictionCol=...)`. The evaluator wants `rawPredictionCol`. Chapter 66 dissects which evaluator wants which column.

7. **The +1 surprise.** A teammate says "we ran 12 grid × 5 folds = 60 trainings." Wrong by one. The total is 61 because of the final refit. For exam questions, count carefully.

---

## 65.9 What this chapter taught you, in one sentence

**`CrossValidator(estimator, grid, evaluator, numFolds=F).fit(df)` trains exactly $G \times F + 1$ models (where $G$ = grid size), refits the best on full training data as `bestModel`, and exposes `avgMetrics` of length $G$ for inspecting the metric across the grid; `TrainValidationSplit` is the cheaper $G + 1$-training variant with one held-out split instead of $k$ folds, with proportionally higher metric variance.**

---

## 65.10 What this builds on / where this returns

**Builds on:**

- Chapter 22 — k-fold cross-validation theory.
- Chapter 49–50 — grid search and the curse of dimensionality.
- Chapter 62 — the Pipeline pattern, since the CV estimator is almost always a Pipeline.
- Chapter 64 — every Estimator whose hyperparameters appear in a grid.

**Returns:**

- Chapter 66 — Evaluators in detail (the missing piece of the CV puzzle).
- Chapter 67 — saving the `bestModel` for production.
- Chapter 53 — Hyperopt + SparkTrials, when the simple grid+CV machinery isn't expressive enough.
- Part L — logging CV runs to MLflow, including the avgMetrics table.

---

## 65.11 Exercises

1. **Model count, small grid.** You have a grid with 3 values of `regParam` and 4 values of `numFeatures`, using 5-fold CV. How many model trainings does CrossValidator perform?

2. **Model count, bigger grid.** 5 values of `maxDepth` × 4 values of `numTrees` × 3 values of `subsamplingRate` with 10-fold CV. How many trainings?

3. **The exam question pattern.** You have 4 grid combinations and 5 folds. How many models does CrossValidator train in total? How many would TrainValidationSplit train with the same grid?

4. **Stage-specific grids.** You have a Pipeline with stages `[tokenizer, hashingTF, idf, lr]`. You want to tune `hashingTF.numFeatures ∈ {5000, 10000}` AND `lr.regParam ∈ {0.01, 0.1, 1.0}` AND `lr.elasticNetParam ∈ {0.0, 1.0}` with 5-fold CV. What's the model count?

5. **Parallelism choice.** Your cluster has 16 executor cores. Your model trains best with 4 cores. What's a reasonable `parallelism` setting?

6. **The +1 reasoning.** Why does CrossValidator perform a final refit on the full training set instead of just keeping one of the per-fold models? Be specific.

7. **CV vs TVS for a tight budget.** You have a grid of 30 combinations. Each training takes ~10 minutes. You want to finish within 4 hours, sequentially. CV or TVS, and with what fold count if CV?

8. **Stratification.** Your dataset is 95% class 0 / 5% class 1. You run 10-fold CV and notice that one fold's AUROC is 0.5 (random). What's likely happening and how do you fix it?

9. **avgMetrics interpretation.** Your `cv_model.avgMetrics` (with grid in `regParam` order [0.0, 0.01, 0.1, 1.0, 10.0]) is `[0.74, 0.78, 0.82, 0.85, 0.71]`. Which regParam wins, and what does the shape tell you about the regularisation landscape?

10. **The leakage protection.** Why is it important that CrossValidator re-fits *the entire Pipeline* on each fold, not just the final stage? Sketch a leakage scenario that would happen if the feature-engineering Estimators were fit outside the CV loop.

11. **`subModels=True` cost.** You run a $50 \times 10$ CV with `collectSubModels=True`. Each model is ~200MB serialized. What's the rough memory footprint? Is this a good idea?

12. **The wall-clock estimate.** A $G \times F + 1 = 61$-training CV at 4 minutes per training with `parallelism=4`. Rough wall-clock estimate?

<details>
<summary>Answers</summary>

1. $G = 3 \times 4 = 12$. Total = $12 \times 5 + 1 = 61$.

2. $G = 5 \times 4 \times 3 = 60$. Total = $60 \times 10 + 1 = 601$.

3. CrossValidator: $4 \times 5 + 1 = 21$. TrainValidationSplit: $4 + 1 = 5$.

4. $G = 2 \times 3 \times 2 = 12$. Total = $12 \times 5 + 1 = 61$.

5. `parallelism=4`. That gives 4 concurrent trainings × 4 cores each = 16 cores total, matching the cluster.

6. Each per-fold model was trained on $\frac{k-1}{k}$ of the data, so none has seen the full training set. The +1 refit produces a model trained on everything, with the hyperparameters chosen by CV — that's the best estimate of what production performance will look like.

7. 30 combinations × 10 minutes = 300 minutes per "fold pass". CV with 5 folds: $30 \times 5 + 1 = 151$ trainings × 10 min = 1510 min ≈ 25 hours. Too slow. CV with 3 folds: $30 \times 3 + 1 = 91$ × 10 min ≈ 15 hours. Still too slow. TVS: $30 + 1 = 31$ × 10 min ≈ 5 hours. Closer; with parallelism=2 you'd hit ~3 hours. Pick TVS, parallelism=2.

8. One fold likely has zero positive examples, making AUROC undefined or 0.5. CrossValidator doesn't stratify. Fix: pre-stratify your data into k folds with `randomSplit` per class, or upsample the minority class, or use TVS with a stratified split done manually.

9. `regParam=1.0` wins with AUROC 0.85. The shape is an inverted-U: too little regularisation (regParam=0) under-performs, too much (regParam=10) under-performs even more, and the sweet spot is around regParam=1. This is the bias-variance tradeoff visible directly in the CV metric.

10. If you fit feature-engineering Estimators (like StandardScaler) on the full dataset before splitting into folds, the scaling statistics are computed using data that will end up in the held-out fold — that's information leaking from validation into training. With the entire Pipeline as the CV estimator, the StandardScaler is refit on each fold's training portion only, and the held-out fold is scaled using statistics that never saw it.

11. $50 \times 10 = 500$ sub-models × 200MB = 100GB. Almost certainly OOM unless you have a very fat driver. Leave `collectSubModels=False` unless you have a specific diagnostic reason to keep them.

12. Best case: 61 / 4 ≈ 15.25 trainings per worker × 4 min = ~61 minutes. Plus the final +1 refit (1 training × 4 min) since it runs after = ~65 minutes total. Realistically with overhead and the final refit not parallelizing with the others, budget 70-80 minutes.

</details>
