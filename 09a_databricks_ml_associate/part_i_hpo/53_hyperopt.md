# Chapter 53 — Hyperopt: API, Search Spaces, fmin, SparkTrials

> **Goal of this chapter:** to bring all of Part I down to specific code. Now that you understand TPE (Ch 52), Hyperopt's API will read like a thin wrapper around the algorithm. By the end of this chapter you should be able to (a) write a complete Hyperopt search from scratch, (b) avoid the `hp.choice` index trap, (c) reason about SparkTrials parallelism, (d) configure MLflow integration on Databricks, and (e) explain to a colleague why Hyperopt is being deprecated in Databricks Runtime ML 17+ while still being on the current ML Associate exam.

---

## 53.1 Why Hyperopt is the exam's HPO tool

The Databricks Certified Machine Learning Associate exam (March 2025 guide) tests Hyperopt by name. Not Optuna, not scikit-optimize, not Ray Tune. Hyperopt. The reasons are partly historical (Hyperopt was the dominant Python HPO library when the exam was first designed) and partly because Hyperopt has good Spark integration via the `SparkTrials` class.

Hyperopt is the Python library by James Bergstra et al. that implements TPE, with a small but powerful API surface. Its three core concepts are:

1. **The objective function** — a Python function you write that takes a `params` dict and returns a loss.
2. **The search space** — a tree of `hp.*` primitives describing the hyperparameters.
3. **The `fmin` driver** — the function that runs the optimization loop.

A complete Hyperopt example is about 30 lines of code. Once you've seen one, you've seen them all. The rest is engineering — choosing distributions, structuring the objective, configuring parallelism.

---

## 53.2 The minimum working example

```python
from hyperopt import fmin, tpe, hp, Trials, STATUS_OK

# 1. Define the objective function.
def objective(params):
    learning_rate = params["learning_rate"]
    max_depth = int(params["max_depth"])   # quniform returns float; cast to int

    model = train_model(learning_rate, max_depth)   # your code
    loss = evaluate(model)                          # the value to minimize
    return {"loss": loss, "status": STATUS_OK}

# 2. Define the search space.
space = {
    "learning_rate": hp.loguniform("learning_rate", -5, -1),   # [e^-5, e^-1]
    "max_depth":     hp.quniform("max_depth", 3, 15, 1),       # integer 3..15
}

# 3. Run the optimization.
trials = Trials()
best = fmin(
    fn=objective,
    space=space,
    algo=tpe.suggest,
    max_evals=50,
    trials=trials,
    rstate=np.random.default_rng(42),    # reproducibility
)

print(best)   # e.g., {"learning_rate": 0.0034, "max_depth": 8.0}
```

That's it. The structure is:

- `objective(params)` is called once per trial. Hyperopt picks `params` (by TPE), passes it in, you train and evaluate, return the loss.
- `space` describes the search space declaratively. Each entry is an `hp.*` call wrapped with a name.
- `fmin` runs the optimization. `algo=tpe.suggest` says use TPE; `algo=rand.suggest` would use random search.
- `Trials()` is the history container.
- `best` is the best configuration found, *as a dict*. (Important: `hp.choice` returns indices, not values — more on this below.)

Let's now unpack each piece.

---

## 53.3 The objective function

The objective function is the most flexible piece. Its only constraint is the signature: takes a `params` dict, returns a `loss` (a scalar) or a dict.

### 53.3.1 The two acceptable return formats

**Scalar return** — return just the loss:

```python
def objective(params):
    ...
    return loss   # a float, the value to minimize
```

**Dict return** — return a structured object:

```python
def objective(params):
    ...
    return {
        "loss": loss,                 # required
        "status": STATUS_OK,           # required if dict; can be STATUS_FAIL
        "model": fitted_model,         # any extra keys are stored in Trials
        "cv_scores": [0.81, 0.83, ...]
    }
```

The dict return is preferred in practice because (a) it lets you record `STATUS_FAIL` for crashed runs and (b) you can attach arbitrary metadata to each trial for later inspection.

### 53.3.2 STATUS_OK and STATUS_FAIL

```python
from hyperopt import STATUS_OK, STATUS_FAIL

def objective(params):
    try:
        loss = train_and_eval(params)
        return {"loss": loss, "status": STATUS_OK}
    except Exception as e:
        # E.g., training crashed because learning rate was too high
        return {"loss": float("inf"), "status": STATUS_FAIL, "error": str(e)}
```

A trial with `STATUS_FAIL` is recorded but not used by TPE for fitting densities — TPE skips failed trials. This is essential robustness: in real HPO runs, some hyperparameter combinations will inevitably crash (out of memory, numerical instability, NaN gradients), and the algorithm should continue rather than abort.

### 53.3.3 Minimization, not maximization

Hyperopt minimizes. If your metric is something you want to maximize (accuracy, F1, AUC), return its negative:

```python
def objective(params):
    f1 = cross_val_score(...)
    return -f1   # negate because fmin minimizes
```

Or equivalently, return $1 - F1$ as the "loss". TPE doesn't care about the absolute scale; only the ordering matters.

### 53.3.4 What you actually compute in the objective

For a real Hyperopt run on a Spark MLlib model:

```python
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator
import mlflow

def objective(params):
    with mlflow.start_run(nested=True):
        # log hyperparameters
        mlflow.log_params(params)

        rf = RandomForestClassifier(
            labelCol="label",
            featuresCol="features",
            numTrees=int(params["numTrees"]),
            maxDepth=int(params["maxDepth"]),
            minInstancesPerNode=int(params["minInstancesPerNode"]),
        )

        # Manual k-fold CV (or use CrossValidator with paramMap of one)
        scores = []
        for fold in range(5):
            train_fold, val_fold = split_fold(train_df, fold)
            model = rf.fit(train_fold)
            preds = model.transform(val_fold)
            evaluator = BinaryClassificationEvaluator(labelCol="label")
            scores.append(evaluator.evaluate(preds))

        mean_auc = sum(scores) / len(scores)
        mlflow.log_metric("mean_auc", mean_auc)

        return {"loss": -mean_auc, "status": STATUS_OK}
```

Notice:

1. Each call to `objective` runs a full 5-fold CV and returns the mean negative AUC.
2. The MLflow `with` block creates a nested run — each Hyperopt trial becomes a child run of the parent `fmin` run.
3. The `int(...)` casts are necessary because `hp.quniform` returns floats even for integer parameters.

This pattern — Hyperopt + MLflow + nested runs — is the idiomatic Databricks pattern, and the exam tests pieces of it.

---

## 53.4 Search spaces: the hp.* primitives

The search space is a Python dict where each value is a Hyperopt primitive. The primitives correspond to the distributions discussed in Ch 50.

### 53.4.1 The continuous primitives

| Function | Distribution | Range | Use for |
|---|---|---|---|
| `hp.uniform(name, low, high)` | Uniform on $[low, high]$ | continuous | fractions, small ranges |
| `hp.loguniform(name, low, high)` | $e^X$ where $X \sim U(low, high)$; **note: `low` and `high` are passed in log-space (base $e$)** | continuous, log-scale | learning rates, regularization strengths |
| `hp.normal(name, mu, sigma)` | $\mathcal{N}(\mu, \sigma^2)$ | continuous, unbounded | rare; centered prior |
| `hp.lognormal(name, mu, sigma)` | $e^X$ where $X \sim \mathcal{N}(\mu, \sigma^2)$ | continuous, positive | log-normal prior |

**The `loguniform` gotcha:** the arguments are in *natural log* space. To sample `learning_rate ∈ [1e-5, 1e-1]`, you write `hp.loguniform("lr", -5*ln(10), -1*ln(10))` or equivalently `hp.loguniform("lr", np.log(1e-5), np.log(1e-1))`. Many bugs come from passing `-5, -1` (base 10) when Hyperopt expects natural log. Be careful.

```python
import numpy as np
from hyperopt import hp

# Correct: lr sampled in [1e-5, 1e-1] log-uniformly
space = {
    "learning_rate": hp.loguniform("learning_rate", np.log(1e-5), np.log(1e-1)),
}
```

### 53.4.2 The discrete primitives

| Function | Distribution | Range | Use for |
|---|---|---|---|
| `hp.quniform(name, low, high, q)` | Uniform on $[low, high]$, quantized to multiples of $q$ | discrete (returns float!) | integer or stepped continuous |
| `hp.qloguniform(name, low, high, q)` | Log-uniform, quantized | discrete, log-scale | wide-range integers |
| `hp.qnormal(name, mu, sigma, q)` | Normal, quantized | discrete | rare |
| `hp.choice(name, options)` | Categorical | unordered set | discrete choices |

**The `quniform` gotcha:** despite "q" suggesting quantized integers, `hp.quniform` **returns a float**. You must cast to int in your objective if you want an integer:

```python
space = {"n_estimators": hp.quniform("n_estimators", 50, 500, 10)}

def objective(params):
    n_est = int(params["n_estimators"])   # cast!
    ...
```

`50 ≤ n_est ≤ 500`, step 10. Possible values: 50, 60, 70, …, 500. But the value Hyperopt hands you is `100.0`, not `100`. Cast.

### 53.4.3 The `hp.choice` index trap

This is the single biggest API trap in Hyperopt, and it absolutely shows up in exam questions.

`hp.choice` returns an *index into the options list*, not the value itself.

```python
space = {"kernel": hp.choice("kernel", ["linear", "rbf", "poly"])}

def objective(params):
    kernel = params["kernel"]   # this is 0, 1, or 2 — NOT a string!
    ...
```

To recover the actual value, you need to either index into the list manually:

```python
def objective(params):
    kernel = ["linear", "rbf", "poly"][params["kernel"]]
```

Or — and this is the recommended pattern — use `space_eval` after `fmin` returns:

```python
from hyperopt import fmin, space_eval

best = fmin(fn=objective, space=space, algo=tpe.suggest, max_evals=50)
best_full = space_eval(space, best)
print(best_full)   # {"kernel": "rbf"}  — actual values
print(best)        # {"kernel": 1}      — indices
```

`space_eval` walks the space tree and substitutes indices with values. This is critical to know:

- **Inside the objective**: handle indices manually (or pre-define lookup tables).
- **After `fmin` returns `best`**: use `space_eval(space, best)` to recover human-readable values.

A real bug scenario: you write `kernel = params["kernel"]; sklearn_estimator = SVC(kernel=kernel)`. Sklearn gets `kernel=1`. Sklearn raises `ValueError: 1 is not a valid kernel`. The trail is hard to follow if you don't know about the index trap.

### 53.4.4 Hierarchical (conditional) search spaces

`hp.choice` can return entire dicts, enabling conditional structure:

```python
space = {
    "classifier": hp.choice("classifier", [
        {
            "type": "svm",
            "C": hp.loguniform("svm_C", -3, 3),
            "kernel": hp.choice("svm_kernel", ["linear", "rbf"]),
        },
        {
            "type": "rf",
            "n_estimators": hp.quniform("rf_n_estimators", 50, 500, 50),
            "max_depth": hp.quniform("rf_max_depth", 3, 15, 1),
        },
    ])
}

def objective(params):
    cfg = params["classifier"]   # dict with one of the two structures
    if cfg["type"] == "svm":
        model = SVC(C=cfg["C"], kernel=["linear", "rbf"][cfg["kernel"]])
    else:
        model = RandomForestClassifier(
            n_estimators=int(cfg["n_estimators"]),
            max_depth=int(cfg["max_depth"]),
        )
    ...
```

TPE handles this correctly — it estimates the conditional densities for the SVM-branch parameters separately from the RF-branch parameters (recall §52.4.4). This is the "tree-structured" in TPE.

For real ML, hierarchical spaces let you do "model selection AND hyperparameter tuning in one fmin call." Useful but also more prone to bugs in the objective dispatch.

---

## 53.5 Algorithms: `tpe.suggest`, `rand.suggest`, `anneal.suggest`

Hyperopt exposes three search algorithms:

```python
from hyperopt import tpe, rand, anneal

# TPE (default for serious work)
fmin(fn=objective, space=space, algo=tpe.suggest, max_evals=100)

# Random search (a useful baseline)
fmin(fn=objective, space=space, algo=rand.suggest, max_evals=100)

# Simulated annealing (rare, mostly historical)
fmin(fn=objective, space=space, algo=anneal.suggest, max_evals=100)
```

`tpe.suggest` is the canonical choice. `rand.suggest` is what you use to baseline TPE — if `tpe.suggest` doesn't beat `rand.suggest`, your problem is either too easy (random found the answer immediately) or too hard (TPE's density estimates aren't picking up signal). `anneal.suggest` is essentially never used; mention only for completeness.

You can also pass algorithm options:

```python
from functools import partial

tpe_with_more_startup = partial(tpe.suggest, n_startup_jobs=30, gamma=0.20)
fmin(fn=objective, space=space, algo=tpe_with_more_startup, max_evals=100)
```

Hyperopt's TPE has a few knobs (defaults shown):

- `n_startup_jobs = 20` — random samples before TPE kicks in.
- `gamma = 0.25` — quantile split.
- `n_EI_candidates = 24` — candidates sampled from $\ell$ per acquisition step.

Most users leave these at defaults. The exam doesn't generally test their values, but knowing they exist helps if you read someone's tuning code.

---

## 53.6 The Trials object

`Trials()` is the history container. It records every evaluation, the chosen hyperparameters, the loss, the status, and any extra dict keys you returned.

```python
trials = Trials()
best = fmin(fn=objective, space=space, algo=tpe.suggest, max_evals=50, trials=trials)

# Inspect after the fact
for trial in trials.trials:
    print(trial["misc"]["vals"])    # parameter values for this trial
    print(trial["result"]["loss"])  # loss for this trial

# Convenience accessors
print(trials.losses())              # list of all losses
print(trials.best_trial["result"])  # best trial's full result
```

For each `trial`, `trial["misc"]["vals"]` is a dict mapping parameter name to a list of length 1 containing the value. (Yes — list of length 1. Hyperopt's internal representation. To get the scalar, do `trial["misc"]["vals"]["learning_rate"][0]`.)

### 53.6.1 Saving and resuming

`Trials` is picklable:

```python
import pickle
with open("trials.pkl", "wb") as f:
    pickle.dump(trials, f)

# Resume later
with open("trials.pkl", "rb") as f:
    trials = pickle.load(f)

# Continue from where we left off
more = fmin(fn=objective, space=space, algo=tpe.suggest,
            max_evals=100, trials=trials)
# max_evals counts ALL trials including the loaded ones.
# So if trials has 50 already, this adds another 50.
```

This is genuinely useful for long HPO runs — if your job crashes at trial 80 of 200, you can resume rather than restart. (In practice on Databricks, the MLflow tracking layer often makes this less necessary, but pickling Trials is the lower-level mechanism.)

---

## 53.7 SparkTrials — parallelism on Spark

`SparkTrials` is the Spark-aware variant of `Trials`. Instead of running trials sequentially on the driver, it dispatches each trial as a Spark task on the cluster.

```python
from hyperopt import SparkTrials

spark_trials = SparkTrials(parallelism=8)

best = fmin(
    fn=objective,
    space=space,
    algo=tpe.suggest,
    max_evals=64,
    trials=spark_trials,   # use SparkTrials instead of Trials
)
```

What happens:

1. `fmin` runs in **rounds**. In each round, TPE proposes `parallelism` configurations (here, 8) and dispatches them as parallel Spark tasks.
2. Each task runs the `objective` on a Spark worker, with access to the full Spark cluster (the `objective` can use Spark APIs internally).
3. Once all 8 tasks complete, `fmin` updates the history with all 8 results, then TPE proposes the next 8.
4. With `max_evals = 64` and `parallelism = 8`, that's **8 rounds of 8 trials each**.

### 53.7.1 The parallelism / Bayesian-benefit trade-off

This is the heart of the SparkTrials exam questions and is a real engineering decision in practice.

**Sequential (parallelism=1) Hyperopt:** Each trial is informed by every previous trial's result. Maximum Bayesian benefit per trial. Slowest in wall-clock.

**Fully parallel (parallelism=max_evals):** All trials chosen in a single round, none informed by any other. Equivalent to random search (TPE's density estimates can't differ much across trials proposed in the same round before any results are known). Fastest in wall-clock.

**Middle (parallelism = some intermediate value):** Trade-off.

The Hyperopt documentation and folklore recommends:

$$
\text{parallelism} \approx \sqrt{\text{max\_evals}}
$$

With `max_evals = 64`, parallelism = 8. With `max_evals = 100`, parallelism = 10. With `max_evals = 25`, parallelism = 5. The rationale: $\sqrt{N}$ rounds is enough to get meaningful Bayesian updates between rounds; $\sqrt{N}$ trials per round is enough to actually use the cluster.

This is the recommendation; it's not a theorem. In practice, the optimal parallelism depends on:

- Cost of a single trial (longer trials → benefit more from parallelism since wall-clock is the bottleneck).
- Cluster capacity (don't set parallelism above what your cluster can run concurrently).
- How many "good" trials you've already accumulated (early in the run, parallel rounds are mostly random; later, they're more TPE-informed).

### 53.7.2 Counting fits with SparkTrials

The total number of objective evaluations is always `max_evals`. The wall-clock time is approximately `max_evals / parallelism × time_per_evaluation` (plus overhead).

If each evaluation runs CV internally (say 5-fold), the *total number of model fits* is `max_evals × k`, plus any final refit you do manually. Hyperopt doesn't do a "final refit at best" automatically — you have to do that yourself after `fmin` returns.

### 53.7.3 Each objective call must be self-contained

When using `SparkTrials`, each call to `objective` runs on a Spark worker, in a fresh process. Variables defined in the driver notebook are not automatically available — you have to either pass them through the `space` dict or use Spark's broadcast mechanism. A common bug: defining `train_df` in the notebook and referencing it inside `objective` without broadcasting works locally (Trials) but fails on SparkTrials.

Robust pattern: define your data loading and preprocessing inside the objective, or broadcast explicitly:

```python
broadcast_train = sc.broadcast(train_df_pandas)   # if data is small

def objective(params):
    train_df = broadcast_train.value
    ...
```

For larger datasets, keep the data in Spark and access it via the SparkSession (`spark` is available in worker processes when using SparkTrials, though there are subtleties).

---

## 53.8 MLflow integration

On Databricks Runtime ML, Hyperopt has built-in MLflow integration. Each call to `objective` runs in an MLflow child run automatically, with the parent run being the `fmin` invocation.

You don't need to explicitly start MLflow runs unless you want extra control:

```python
import mlflow

mlflow.set_experiment("/Users/me/hyperopt_runs")

def objective(params):
    # Hyperopt auto-creates a child run here
    mlflow.log_params(params)
    mlflow.log_metric("loss", loss)
    mlflow.log_metric("accuracy", acc)
    return {"loss": loss, "status": STATUS_OK}

with mlflow.start_run(run_name="hyperopt_parent"):
    best = fmin(fn=objective, space=space, algo=tpe.suggest, max_evals=50,
                trials=SparkTrials(parallelism=8))
```

This produces a parent run named `hyperopt_parent` with 50 child runs, one per trial. In the MLflow UI you can see the full trial table, sort by loss, and inspect individual trials' parameters and metrics.

The MLflow integration is the most important reason Hyperopt remained dominant on Databricks for so long. Optuna has comparable integration now (Ch 54), but for years, "Hyperopt + MLflow + SparkTrials" was the only well-supported tuning stack on Databricks.

---

## 53.9 The Hyperopt deprecation story

For exam preparation, the timeline matters:

- **Databricks Runtime ML 14.x and 15.x:** Hyperopt and `SparkTrials` are first-class. The exam is built around this assumption.
- **Databricks Runtime ML 16.x:** Hyperopt is still available but officially deprecated; the docs recommend migrating to Optuna.
- **Databricks Runtime ML 17.x (announced):** Hyperopt is removed from the runtime. Optuna becomes the default HPO library.

The ML Associate exam (March 2025 version) still tests Hyperopt because most existing Databricks customers and certifications are pinned to older runtimes. The exam will probably switch to Optuna in a future revision (likely the next major exam update). For now: **learn Hyperopt for the exam, learn Optuna for the job**.

For your career: Optuna's API is, frankly, nicer than Hyperopt's. The define-by-run search space (Ch 54) is more flexible than Hyperopt's declarative space. The pruners are more useful than anything in Hyperopt. If you have a choice, prefer Optuna. We'll cover it in Ch 54.

---

## 53.10 A full worked Hyperopt example

Let's tune an XGBoost classifier with 5 hyperparameters using TPE on a tabular classification problem.

```python
import numpy as np
import xgboost as xgb
from hyperopt import fmin, tpe, hp, Trials, STATUS_OK, space_eval
from sklearn.model_selection import cross_val_score
import mlflow

# Assume X_train, y_train are loaded already
# Assume X_train is a pandas DataFrame, y_train is a Series

# Search space
space = {
    "learning_rate":    hp.loguniform("learning_rate", np.log(0.005), np.log(0.3)),
    "n_estimators":     hp.quniform("n_estimators", 50, 500, 50),
    "max_depth":        hp.quniform("max_depth", 3, 12, 1),
    "min_child_weight": hp.quniform("min_child_weight", 1, 10, 1),
    "subsample":        hp.uniform("subsample", 0.5, 1.0),
    "colsample_bytree": hp.uniform("colsample_bytree", 0.5, 1.0),
    "reg_lambda":       hp.loguniform("reg_lambda", np.log(0.01), np.log(10.0)),
}

# Objective
def objective(params):
    # Cast integer-valued quniform results
    int_params = {"n_estimators", "max_depth", "min_child_weight"}
    for k in int_params:
        params[k] = int(params[k])

    model = xgb.XGBClassifier(
        objective="binary:logistic",
        eval_metric="logloss",
        n_jobs=-1,
        random_state=42,
        **params,
    )

    cv_scores = cross_val_score(
        model, X_train, y_train,
        cv=5, scoring="f1",
        n_jobs=1,   # leave parallelism to Hyperopt at the trial level
    )
    mean_f1 = cv_scores.mean()

    return {"loss": -mean_f1, "status": STATUS_OK,
            "cv_f1_mean": float(mean_f1),
            "cv_f1_std": float(cv_scores.std())}

# Run
trials = Trials()

with mlflow.start_run(run_name="xgb_tpe_hpo"):
    best = fmin(
        fn=objective,
        space=space,
        algo=tpe.suggest,
        max_evals=80,
        trials=trials,
        rstate=np.random.default_rng(42),
    )

best_params = space_eval(space, best)
print("Best parameters:", best_params)
print("Best CV F1:", -trials.best_trial["result"]["loss"])

# Cast integers for the final model
for k in {"n_estimators", "max_depth", "min_child_weight"}:
    best_params[k] = int(best_params[k])

# Final fit on the full training data
final_model = xgb.XGBClassifier(**best_params, random_state=42)
final_model.fit(X_train, y_train)
```

This is roughly what production Hyperopt code looks like. 70-ish lines, mostly boilerplate. The thing that changes between projects is the search space and the objective; the rest is template.

If we run this on Databricks with `SparkTrials`:

```python
from hyperopt import SparkTrials

spark_trials = SparkTrials(parallelism=8)
with mlflow.start_run(run_name="xgb_tpe_hpo_distributed"):
    best = fmin(fn=objective, space=space, algo=tpe.suggest,
                max_evals=80, trials=spark_trials,
                rstate=np.random.default_rng(42))
```

The 80 trials run in 10 rounds of 8 parallel each. On a cluster where one trial takes 2 minutes, total wall-clock is roughly 20 minutes (vs 160 minutes sequential).

---

## 53.11 Exam-pattern questions

The Databricks ML Associate exam asks Hyperopt questions in a few standard shapes.

**"Given this `fmin` call, how many model evaluations will occur?"** — Answer: `max_evals`. The number of trials is exactly `max_evals`. The number of *model fits* depends on what the objective does (e.g., a 5-fold CV inside the objective means `max_evals × 5` fits).

**"What is the role of `parallelism` in `SparkTrials`?"** — Answer: it controls how many trials run concurrently in each round of `fmin`. Higher parallelism = faster wall-clock but less Bayesian information shared between concurrent trials. Recommended: $\sqrt{\text{max\_evals}}$.

**"You called `fmin` and got `best = {"kernel": 1, "C": 2.5}`. What is the actual kernel?"** — Answer: the second item in the `hp.choice` options list (since indexing is 0-based). Use `space_eval(space, best)` to resolve.

**"Your objective returned `STATUS_FAIL` for several trials. How does this affect TPE?"** — Answer: failed trials are recorded but not used in the density estimation. TPE skips them.

**"Why might you use `tpe.suggest` over `rand.suggest`?"** — Answer: TPE uses the history of past evaluations to guide future ones (it fits density estimates and proposes points that are likely-good and unlikely-bad), while random samples uniformly. TPE typically finds better configurations than random for the same `max_evals`, especially for $N \geq 50$.

---

## 53.12 Engineering notes

A few things that don't fit cleanly elsewhere:

**Always set `rstate`.** Hyperopt's TPE includes randomness (the candidate sampling from $\ell$, the startup random phase). Setting `rstate=np.random.default_rng(seed)` makes runs reproducible. Without it, two `fmin` calls with the same `space` and `max_evals` produce different results.

**The Trials object grows in memory.** Each trial stores its full parameter dict, loss, status, and any metadata you returned. For 500 trials with rich metadata, this can be megabytes. Not usually a problem; can be if you attach huge objects to results.

**MLflow autologging interacts subtly.** If you have `mlflow.autolog()` on, Hyperopt's per-trial child runs will also auto-log the inner model's parameters and metrics, which can be helpful or noisy depending on what your objective trains. Test on a small run first.

**SparkTrials in shared-state objectives.** Avoid mutating global state inside the objective. The objective is called on worker processes; mutations don't propagate. If you need shared state (counters, caches), use Spark accumulators or external storage.

**Don't tune integer hyperparameters as continuous.** A common bug: `hp.uniform("max_depth", 3, 15)` and casting to int in the objective. This works but TPE will keep treating max_depth as continuous in its density estimation, leading to oversampling near the boundary integers. Use `hp.quniform("max_depth", 3, 15, 1)` properly.

---

## 53.13 What this builds on / where this returns

**Builds on:**

- *Chapter 52* — TPE, the algorithm Hyperopt uses by default.
- *Chapter 51* — Bayesian optimization framework. Hyperopt is its production implementation.
- *Chapter 22* — cross-validation, run inside the objective.
- *Chapter 28* — feature pipelines (recall TF-IDF) that often need to be inside the objective.

**Returns in:**

- *Chapter 54* — Optuna, the modern successor with a cleaner API and more features.
- *Chapter 65* — pyspark.ml's `CrossValidator`, which is grid-based. Hyperopt is the random/TPE alternative on Spark.
- *Chapter 72* — MLflow Tracking, the deeper picture of how Hyperopt + MLflow integrate.

---

## 53.14 Exercises

1. **Counting evaluations.** A Hyperopt run is configured with `max_evals = 60` and `SparkTrials(parallelism = 6)`. The objective runs a 3-fold CV internally. (a) How many trials are evaluated? (b) How many rounds does `fmin` run? (c) How many total model fits inside the objective, across the full HPO run?

2. **The choice trap.** Given the search space `space = {"a": hp.choice("a", ["x", "y", "z"]), "b": hp.uniform("b", 0, 1)}` and the call `best = fmin(fn=obj, space=space, algo=tpe.suggest, max_evals=20)`, you inspect `best` and see `{"a": 2, "b": 0.71}`. What is the actual value of `a` in the best configuration? How would you have written the objective to use this safely?

3. **Distribution choice.** Write a Hyperopt search space for: `learning_rate` log-uniform between $10^{-4}$ and $10^{-1}$; `n_estimators` integer in $\{100, 200, ..., 1000\}$ in steps of 100; `subsample` continuous in $[0.6, 1.0]$; `boosting_type` categorical in `{"gbdt", "dart"}`. Be careful about the loguniform argument scale.

4. **Parallelism arithmetic.** You have `max_evals = 200`. Suggest a `parallelism` value following the $\sqrt{N}$ heuristic. With this parallelism, how many rounds of TPE proposals will occur?

5. **The startup phase and `max_evals`.** Hyperopt's TPE has `n_startup_jobs = 20` by default. With `max_evals = 25`, what is the algorithm essentially doing? With `max_evals = 100`?

6. **MLflow nested runs.** Sketch the structure of MLflow runs produced by a Hyperopt search with `max_evals = 50`, wrapped in an outer `mlflow.start_run(run_name="parent")` context. How would the UI display them?

7. **STATUS_FAIL.** Write an objective that catches `MemoryError` from training and returns `STATUS_FAIL` cleanly. What does TPE do with the failed trials?

8. **Reproducibility.** Two team members run the same Hyperopt code and report different best configurations. Both used `algo=tpe.suggest` and `max_evals=100`. What is the likely cause and how would you fix it?

9. **Reading Trials.** Given `trials.best_trial`, write code to extract: the best loss, the best hyperparameter dict (with indices, not values), and the trial index.

10. **From sklearn to Spark MLlib.** Convert this sklearn-style Hyperopt objective to a pyspark.ml-style objective: ```python def objective(params): rf = RandomForestClassifier(**params); return {"loss": -cross_val_score(rf, X, y, cv=5).mean(), "status": STATUS_OK} ```. Use a pyspark.ml `CrossValidator` with `numFolds=5`.

11. **Resume a crashed run.** Your Hyperopt run crashed at trial 40 of 100. The `trials` object was pickled at trial 38. Sketch code that resumes the run and completes the remaining trials, ensuring `max_evals = 100` total.

12. **Choose-the-tool.** For each scenario, recommend Hyperopt vs random search vs pyspark.ml `CrossValidator`, with one-sentence justification: (a) 3 hyperparameters, all integer with 4 values each, want full reproducibility for audit; (b) 8 hyperparameters of mixed types, 100 evaluations budget, Spark cluster; (c) Quick first cut, 5 hyperparameters, 20 evaluations.

<details>
<summary>Answers</summary>

1. (a) 60 trials. (b) `60 / 6 = 10` rounds. (c) `60 × 3 = 180` model fits inside the objectives. (Plus any final refit you do manually after `fmin`, which is not counted in `max_evals`.)

2. The actual value of `a` is `"z"` (index 2 → third item). Safe pattern: `value_of_a = ["x", "y", "z"][params["a"]]` inside the objective. After `fmin` returns: `space_eval(space, best)` gives `{"a": "z", "b": 0.71}`.

3. ```python
   import numpy as np
   from hyperopt import hp
   space = {
       "learning_rate":   hp.loguniform("learning_rate", np.log(1e-4), np.log(1e-1)),
       "n_estimators":    hp.quniform("n_estimators", 100, 1000, 100),
       "subsample":       hp.uniform("subsample", 0.6, 1.0),
       "boosting_type":   hp.choice("boosting_type", ["gbdt", "dart"]),
   }
   ```
   Remember `loguniform` takes natural-log arguments and `quniform` returns floats.

4. $\sqrt{200} \approx 14$, so `parallelism = 14`. Rounds: $\lceil 200 / 14 \rceil = 15$ rounds (last round may have fewer than 14).

5. `max_evals = 25`: 20 random + 5 TPE — barely uses TPE. Essentially random search. `max_evals = 100`: 20 random + 80 TPE — meaningful Bayesian benefit.

6. The MLflow UI would show one parent run "parent" with 50 child runs nested under it. The parent contains overall metadata; each child contains the params and metrics for one trial. The UI's "Compare runs" feature is especially useful — sort children by loss to see the best trials.

7. ```python
   from hyperopt import STATUS_OK, STATUS_FAIL
   def objective(params):
       try:
           loss = train_and_eval(params)
           return {"loss": loss, "status": STATUS_OK}
       except MemoryError as e:
           return {"loss": float("inf"), "status": STATUS_FAIL,
                   "error": "OOM: " + str(e)}
   ```
   TPE skips failed trials when fitting its density estimates — they are recorded in Trials but not used to update $\ell$ or $g$.

8. The likely cause is that one or both did not set `rstate=np.random.default_rng(seed)`. Fix: both pass the same `rstate` with the same seed. Note: even with the same `rstate`, results can differ if the inner objective has unseeded randomness (e.g., a sklearn model without `random_state`).

9. ```python
   best_trial = trials.best_trial
   loss = best_trial["result"]["loss"]
   # vals are stored as {param_name: [value]}; flatten to scalars
   params_dict = {k: v[0] for k, v in best_trial["misc"]["vals"].items()}
   # The trial index (1-based in trials.trials):
   tid = best_trial["tid"]
   ```

10. ```python
    from pyspark.ml.classification import RandomForestClassifier
    from pyspark.ml.evaluation import BinaryClassificationEvaluator
    from pyspark.ml.tuning import CrossValidator, ParamGridBuilder

    def objective(params):
        # Build a single-config grid (just the params we want)
        rf = RandomForestClassifier(labelCol="label", featuresCol="features",
                                    numTrees=int(params["numTrees"]),
                                    maxDepth=int(params["maxDepth"]))
        # CrossValidator requires a paramGrid; provide a singleton
        param_grid = ParamGridBuilder().build()   # empty grid = 1 config
        cv = CrossValidator(estimator=rf,
                            estimatorParamMaps=param_grid,
                            evaluator=BinaryClassificationEvaluator(labelCol="label"),
                            numFolds=5)
        cv_model = cv.fit(train_df)
        mean_auc = cv_model.avgMetrics[0]
        return {"loss": -mean_auc, "status": STATUS_OK}
    ```
    (Note: this pattern uses `CrossValidator` somewhat awkwardly — for production, you'd typically do the fold split manually for more control.)

11. ```python
    import pickle
    with open("trials.pkl", "rb") as f:
        trials = pickle.load(f)
    # trials has 38 entries; fmin treats max_evals as a global count.
    best = fmin(fn=objective, space=space, algo=tpe.suggest,
                max_evals=100,   # not 62 — fmin checks against trials length
                trials=trials,
                rstate=np.random.default_rng(42))
    # Now adds 100 - 38 = 62 more trials, total 100.
    ```

12. (a) **pyspark.ml CrossValidator with ParamGridBuilder** — small reproducible grid, exhaustive, audit-friendly. (b) **Hyperopt with TPE on SparkTrials** — mixed types and a serious budget on a cluster. (c) **Random search** (sklearn `RandomizedSearchCV` or Hyperopt with `rand.suggest`) — fast, no fancy machinery, good baseline.

</details>
