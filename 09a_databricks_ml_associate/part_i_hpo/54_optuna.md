# Chapter 54 — Optuna: Studies, Samplers, Pruners, Multi-Objective

> **Goal of this chapter:** to give you a working command of Optuna, the modern HPO library that is replacing Hyperopt across the Python ML ecosystem and on Databricks Runtime ML 17+. By the end you should be able to (a) write a complete Optuna study with TPE, (b) take advantage of the define-by-run search space pattern, (c) configure a pruner to early-stop bad trials, (d) run multi-objective optimization, and (e) explain why the ML Professional certification (Topic 11) tests Optuna where the Associate tests Hyperopt.

---

## 54.1 Why a different library

You've just learned Hyperopt. It works. It implements TPE. It has SparkTrials. It integrates with MLflow. What's wrong with it?

A few things, accumulated over a decade of usage:

1. **The `hp.choice` index trap (Ch 53.4.3)** is a constant source of bugs. Returning indices instead of values is not a small ergonomic issue; it's a design flaw that has cost the global ML community an enormous amount of debugging time.

2. **The declarative search space (`space = {...}`)** is rigid. You cannot make hyperparameter $b$ depend on a *value* of hyperparameter $a$ that hasn't been sampled yet. Conditional search spaces (Ch 53.4.4) require nesting `hp.choice` over entire dicts, which is awkward.

3. **No native early-stopping (pruning).** Hyperopt evaluates every proposed configuration to completion. For deep learning workloads where you can tell within 10% of training that a configuration is bad, this is wasteful.

4. **Sequential-friendly but parallel-painful.** SparkTrials works but with the round-based parallelism we saw in Ch 53.7. Modern HPO libraries (Optuna, Ray Tune) support asynchronous parallelism — workers continuously pull new trials and report results — which is more efficient.

5. **Maintenance.** Hyperopt's development has been minimal since around 2019. The codebase is harder to extend and the GitHub issues queue is long. Optuna, by contrast, has had active development by Preferred Networks since 2018 and is the de facto standard in Kaggle competitions and academic ML.

Optuna is Hyperopt's clean reimplementation. The core algorithm (TPE) is the same. The API is different in ways that matter. We'll work through it.

---

## 54.2 The Optuna model

Optuna's vocabulary is:

- **Study** — one HPO run. Persists across processes. Resumable.
- **Trial** — one evaluation. The object passed to your objective function.
- **Sampler** — the algorithm choosing the next trial. Default is `TPESampler`.
- **Pruner** — the algorithm deciding to early-stop a trial. Default is no pruning.
- **Storage** — where the study's history is stored. Default is in-memory; can be SQLite/RDB for persistence.

The minimum working example:

```python
import optuna

def objective(trial):
    # Define hyperparameters inside the objective via trial.suggest_*
    learning_rate = trial.suggest_float("learning_rate", 1e-5, 1e-1, log=True)
    max_depth = trial.suggest_int("max_depth", 3, 15)

    model = train_model(learning_rate, max_depth)
    loss = evaluate(model)
    return loss

study = optuna.create_study(direction="minimize")
study.optimize(objective, n_trials=50)

print(study.best_params)   # {"learning_rate": 0.0023, "max_depth": 7}
print(study.best_value)    # the best loss
```

A few things to notice already:

1. **No separate `space` dict.** The search space is constructed *inside* the objective by calls to `trial.suggest_*`. This is the *define-by-run* style.

2. **`trial.suggest_float(..., log=True)`** is the analog of `hp.loguniform`, but the arguments are in *natural scale*, not log-space. You pass `1e-5, 1e-1`, not `np.log(1e-5), np.log(1e-1)`. This eliminates a class of bugs from Hyperopt.

3. **`trial.suggest_int(...)`** returns an actual int, not a float. No casting required.

4. **`trial.suggest_categorical(...)`** (we'll see it shortly) returns the *value*, not an index. The choice trap is gone.

5. **`study.best_params`** is a clean dict of hyperparameter name to value. No `space_eval` needed.

The API is, simply, better. Let's go through the pieces.

---

## 54.3 Define-by-run search spaces

The most significant API change. In Hyperopt, you declare the entire search space up front:

```python
space = {"learning_rate": hp.loguniform(...), "max_depth": hp.quniform(...)}
```

In Optuna, you build it by calling `trial.suggest_*` methods inside the objective:

```python
def objective(trial):
    learning_rate = trial.suggest_float("learning_rate", 1e-5, 1e-1, log=True)
    max_depth = trial.suggest_int("max_depth", 3, 15)
    ...
```

This seems like the same thing in a different syntax. It's not. Define-by-run is *strictly more expressive* than declarative spaces, because the sampling order is now under your control — you can sample hyperparameter $b$ conditionally on the *value* of hyperparameter $a$.

### 54.3.1 Conditional search spaces

```python
def objective(trial):
    classifier = trial.suggest_categorical("classifier", ["svm", "rf"])

    if classifier == "svm":
        C = trial.suggest_float("C", 1e-3, 1e3, log=True)
        kernel = trial.suggest_categorical("kernel", ["linear", "rbf"])
        if kernel == "rbf":
            gamma = trial.suggest_float("gamma", 1e-4, 1e0, log=True)
            model = SVC(C=C, kernel="rbf", gamma=gamma)
        else:
            model = SVC(C=C, kernel="linear")
    else:
        n_estimators = trial.suggest_int("n_estimators", 50, 500)
        max_depth = trial.suggest_int("max_depth", 3, 15)
        model = RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth)

    return -cross_val_score(model, X, y, cv=5).mean()
```

The branches don't share hyperparameters. Optuna's TPESampler estimates densities only over the parameters that were actually sampled in each trial. For trials where `classifier = "svm"`, the densities cover `C`, `kernel`, and (if rbf) `gamma`. For trials where `classifier = "rf"`, the densities cover `n_estimators` and `max_depth`. The two branches are independent in TPE's eyes — exactly as we wanted with hierarchical search spaces in Ch 52.

The convenience is huge: the search space is *just Python code*, and you don't need any special structure declarations.

### 54.3.2 Data-dependent hyperparameters

A subtle benefit. Suppose you want `max_features ∈ [1, n_features]` where `n_features` is determined by your dataset's preprocessing. In Hyperopt's declarative space, you'd have to compute `n_features` *before* declaring the space. In Optuna:

```python
def objective(trial):
    # Maybe n_features depends on preprocessing choices
    n_features = X.shape[1]
    max_features = trial.suggest_int("max_features", 1, n_features)
    ...
```

This works because the suggestion happens *inside* the objective, where you have access to runtime data.

### 54.3.3 The `suggest_*` methods

| Method | Returns | Equivalent in Hyperopt |
|---|---|---|
| `trial.suggest_float(name, low, high)` | float in $[low, high]$, linearly | `hp.uniform` |
| `trial.suggest_float(name, low, high, log=True)` | float in $[low, high]$, log-uniform | `hp.loguniform` (but with linear bounds, not log!) |
| `trial.suggest_float(name, low, high, step=q)` | float in $[low, high]$, stepped | `hp.quniform` |
| `trial.suggest_int(name, low, high)` | int in $[low, high]$ inclusive | `hp.quniform` with q=1 (and cast) |
| `trial.suggest_int(name, low, high, log=True)` | int in $[low, high]$, log-uniform | `hp.qloguniform` (and cast) |
| `trial.suggest_int(name, low, high, step=q)` | int in $[low, high]$, in steps of $q$ | — |
| `trial.suggest_categorical(name, choices)` | one of the choices (the value, not the index) | `hp.choice` (but no index trap) |

Two things to remember:

- For log-uniform sampling, pass `log=True` and use *natural scale bounds*. `trial.suggest_float("lr", 1e-5, 1e-1, log=True)` is sampling $\log(\text{lr}) \sim U(\log(1e-5), \log(1e-1))$. The user just writes the bounds in natural scale; Optuna handles the log.
- The deprecated `trial.suggest_uniform`, `trial.suggest_loguniform`, etc. still work in current Optuna but are scheduled for removal. Use the parameterized `trial.suggest_float(..., log=True, step=...)` form.

---

## 54.4 Study and direction

```python
study = optuna.create_study(direction="minimize")
# or
study = optuna.create_study(direction="maximize")
```

Optuna takes a `direction` argument. This is more honest than Hyperopt's "always minimize, return negative if maximizing." If your metric is F1 (which you want to maximize), return F1 directly and create the study with `direction="maximize"`. No more `-f1` in your objective.

For multi-objective optimization (Section 54.7), you can pass `directions=["maximize", "minimize"]` for multiple goals.

---

## 54.5 Samplers

The sampler is the search algorithm. Optuna ships several:

| Sampler | Type | Use case |
|---|---|---|
| `TPESampler` (default) | Bayesian (TPE) | General-purpose default; same algorithm as Hyperopt's `tpe.suggest` |
| `CmaEsSampler` | Evolutionary (CMA-ES) | Pure continuous, $\leq 30$ dimensions, can outperform TPE in this regime |
| `RandomSampler` | Random | Baseline; comparison against fancier methods |
| `GridSampler` | Grid | Backwards-compat with grid search |
| `NSGAIISampler` | Multi-objective | When optimizing multiple objectives jointly |
| `QMCSampler` | Quasi-Monte-Carlo | More uniform than `RandomSampler`; used for initialization |

Configuring the sampler:

```python
from optuna.samplers import TPESampler

sampler = TPESampler(
    n_startup_trials=20,        # number of random startup trials (default 10)
    n_ei_candidates=24,         # number of candidates per acquisition step (default 24)
    seed=42,                    # reproducibility
    multivariate=True,          # NEW in Optuna: fit joint density (not marginals)
)

study = optuna.create_study(sampler=sampler, direction="minimize")
```

The `multivariate=True` flag is genuinely useful. Recall from Ch 52.4.5 that vanilla TPE assumes parameters are independent — it estimates each parameter's density marginally. Optuna's multivariate TPE estimates the *joint* density (using copulas under the hood), capturing interactions between hyperparameters. This often improves results for problems where hyperparameters interact (`learning_rate` and `n_estimators` in gradient boosting, for example).

`multivariate=True` is slower per trial but usually better. For ML Associate-style problems, it's a good default; for very wide search spaces (20+ parameters), it can become unwieldy.

### 54.5.1 CMA-ES

`CmaEsSampler` is worth knowing about for continuous-only HPO. CMA-ES (Covariance Matrix Adaptation Evolution Strategy) is a non-Bayesian algorithm that maintains a multivariate Gaussian over the search space and adapts its covariance based on successful samples. It's particularly good when:

- All hyperparameters are continuous.
- Dimension is moderate (typically 5–30).
- The loss surface is unimodal or has a clear dominant basin.
- The evaluation budget is moderate to large (>50 trials).

For tabular ML on Databricks, this set of conditions is rare — most search spaces have categorical / integer parameters. But for tuning continuous neural network hyperparameters (learning rate, weight decay, dropout, etc.) where you have many trials, CMA-ES is competitive with TPE.

```python
from optuna.samplers import CmaEsSampler
sampler = CmaEsSampler(seed=42)
study = optuna.create_study(sampler=sampler, direction="minimize")
```

---

## 54.6 Pruners — early stopping of bad trials

This is the biggest functional improvement over Hyperopt. **Pruners let you abort trials that are clearly going to be bad, without running them to completion.**

The idea: most models can produce intermediate evaluations during training. A gradient-boosted tree gives you a validation loss after each boosting round. A neural network gives you a validation loss after each epoch. A random forest can be evaluated as you add more trees.

If at some intermediate point the trial's loss is already much worse than other trials' losses at the same point, you don't need to keep going. Kill it. Free up compute for a new trial.

### 54.6.1 The pruning API

You report intermediate values via `trial.report(value, step)` and check `trial.should_prune()`:

```python
import optuna

def objective(trial):
    n_estimators = trial.suggest_int("n_estimators", 50, 1000)
    max_depth = trial.suggest_int("max_depth", 3, 15)

    model = GradientBoostingClassifier(
        n_estimators=n_estimators, max_depth=max_depth,
        warm_start=True   # so we can train incrementally
    )

    # Train incrementally; report after each chunk
    chunk_size = 50
    for n_so_far in range(chunk_size, n_estimators + 1, chunk_size):
        model.n_estimators = n_so_far
        model.fit(X_train, y_train)
        val_loss = 1 - model.score(X_val, y_val)

        trial.report(val_loss, step=n_so_far)
        if trial.should_prune():
            raise optuna.exceptions.TrialPruned()

    return val_loss

study = optuna.create_study(
    direction="minimize",
    pruner=optuna.pruners.MedianPruner(n_startup_trials=5, n_warmup_steps=100),
)
study.optimize(objective, n_trials=100)
```

The pruner gets the report at each step. It looks at the history of *all completed trials* at the same step and decides whether the current trial is worse than the median (or some other criterion). If so, the trial is pruned.

Pruned trials show up in `study.trials` with `state = optuna.trial.TrialState.PRUNED`. The TPE sampler can be configured to either include pruned trials (using their last reported value) or exclude them — usually you include them, treating pruned trials as a known-bad signal.

### 54.6.2 The standard pruners

| Pruner | Logic |
|---|---|
| `MedianPruner` | Prune if intermediate value > median of all completed trials at same step. The simplest and most robust. |
| `PercentilePruner(percentile=75)` | Prune if intermediate value is in the worst 25% (i.e., worse than the 75th percentile) at this step. More aggressive than MedianPruner. |
| `HyperbandPruner` | Bandit-based. Runs many trials with small budgets, promotes top fraction to larger budgets. Sophisticated. Good for deep learning. |
| `SuccessiveHalvingPruner` | Like Hyperband but simpler. Halve the population at each rung. |
| `ThresholdPruner` | Prune if intermediate value exceeds (or falls below) an absolute threshold. Useful when you have a known acceptable range. |
| `NopPruner` | Never prune. Default. |

For starter Optuna usage on tabular ML, `MedianPruner` is the right pruner: simple, robust, and gives meaningful speedups (often 2–5× faster overall HPO for the same number of "effective" trials).

For deep learning with expensive epoch-level training, `HyperbandPruner` is essentially state-of-the-art. The Hyperband algorithm comes from Li et al. 2017 and is one of the few HPO methods to clearly outperform Bayesian optimization on standard benchmarks.

### 54.6.3 What pruning does to total compute

If you have `n_trials = 100` and pruning aborts roughly half of them at 30% completion:

- Without pruning: 100 full evaluations.
- With pruning: 50 full evaluations + 50 × 0.30 partial = 65 "trial-equivalents."

You can use the saved compute to run more trials, or just accept the wall-clock savings. Either way, pruning is essentially free improvement for any model with intermediate evaluations available.

---

## 54.7 Multi-objective optimization

Sometimes you have multiple goals you'd like to optimize jointly. The canonical example: maximize accuracy AND minimize inference latency. There is no single "best" model — there is a *Pareto front* of models, each dominating others on at least one objective.

Optuna supports this natively:

```python
def objective(trial):
    n_estimators = trial.suggest_int("n_estimators", 50, 1000)
    max_depth = trial.suggest_int("max_depth", 3, 15)

    model = RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth)
    model.fit(X_train, y_train)
    accuracy = model.score(X_val, y_val)

    import time
    t0 = time.time()
    _ = model.predict(X_val)
    latency = (time.time() - t0) / len(X_val) * 1000   # ms per prediction

    return accuracy, latency   # tuple — multi-objective

study = optuna.create_study(
    directions=["maximize", "minimize"],   # max accuracy, min latency
    sampler=optuna.samplers.NSGAIISampler(),   # multi-objective sampler
)
study.optimize(objective, n_trials=100)

# Inspect Pareto front
for t in study.best_trials:   # best_trials (plural) returns the Pareto front
    print(t.params, t.values)
```

`study.best_trials` (plural) returns a list — the Pareto-optimal set. For each trial in this set, there is no other trial that beats it on all objectives. The user (or downstream system) picks one based on their preferred trade-off — for example, the most accurate model with latency < 5 ms.

Multi-objective is a real production technique but not on the ML Associate exam. It's tested on the ML Professional exam (Topic 11 of this repo) and worth knowing about for your career.

---

## 54.8 Persistence and parallelism

### 54.8.1 RDB-backed storage

By default, Optuna keeps the study in memory. For long runs or parallel runs, you want a persistent backend:

```python
study = optuna.create_study(
    storage="sqlite:///optuna_study.db",
    study_name="xgb_tuning",
    direction="maximize",
    load_if_exists=True,
)
```

The `storage` argument can be SQLite (single-file, fine for solo work), or a real RDB URL (PostgreSQL, MySQL) for production. The `load_if_exists=True` means: if the study already exists, resume it; otherwise create a new one.

With persistent storage, you can:

- Crash-recover: the study survives process death.
- Inspect interactively: open the SQLite file from another process while the study is running.
- Hand off: train a study on a beefy machine, then continue on another machine pointing to the same RDB.

### 54.8.2 Parallel trials

The simplest parallelism: run multiple Optuna *processes*, all pointing to the same RDB. Each process pulls the next trial from the storage, runs it, and writes back. Optuna's RDB-backed storage handles the coordination via row locking.

```bash
# On worker 1:
python my_optuna_script.py
# On worker 2:
python my_optuna_script.py
# ...
```

Each script calls `study.optimize(objective, n_trials=K)` independently; the total number of trials across workers is approximately `K * num_workers`, but you can also pass a global limit via `study.optimize(..., n_trials=200)` and the workers will cooperatively stop once the total reaches 200.

For Spark-based parallelism, Optuna can be combined with a `JoblibBackend` or you can use the `optuna-integration` package's helpers. The setup is more involved than Hyperopt's `SparkTrials`, but more flexible.

---

## 54.9 MLflow integration

Optuna integrates with MLflow via `MLflowCallback`:

```python
import optuna
from optuna.integration.mlflow import MLflowCallback

mlflow_callback = MLflowCallback(
    tracking_uri="databricks",
    metric_name="f1_score",
)

study = optuna.create_study(direction="maximize")
study.optimize(objective, n_trials=50, callbacks=[mlflow_callback])
```

Each trial becomes an MLflow run. The parameters and the final metric are logged. The integration is more explicit than Hyperopt's auto-nesting, but it's also more customizable — you can pass additional log functions, choose which metrics to track, etc.

On Databricks ML Runtime 17+, the recommended pattern is Optuna + MLflowCallback. The ML Professional exam tests this pattern.

---

## 54.10 A full Optuna example

Let's tune an XGBoost classifier with pruning, parallel-ready storage, and MLflow.

```python
import optuna
import xgboost as xgb
import numpy as np
import mlflow
from sklearn.model_selection import train_test_split
from optuna.integration.mlflow import MLflowCallback

# Data
# X_train_full, y_train_full assumed loaded
X_train, X_val, y_train, y_val = train_test_split(
    X_train_full, y_train_full, test_size=0.2, random_state=42, stratify=y_train_full
)

def objective(trial):
    params = {
        "objective":        "binary:logistic",
        "eval_metric":      "logloss",
        "learning_rate":    trial.suggest_float("learning_rate", 0.005, 0.3, log=True),
        "max_depth":        trial.suggest_int("max_depth", 3, 12),
        "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
        "subsample":        trial.suggest_float("subsample", 0.5, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
        "reg_lambda":       trial.suggest_float("reg_lambda", 0.01, 10.0, log=True),
    }

    dtrain = xgb.DMatrix(X_train, label=y_train)
    dval = xgb.DMatrix(X_val, label=y_val)

    # The pruning callback reports validation loss to Optuna after each boosting round
    pruning_callback = optuna.integration.XGBoostPruningCallback(trial, "validation-logloss")

    model = xgb.train(
        params,
        dtrain,
        num_boost_round=500,
        evals=[(dval, "validation")],
        callbacks=[pruning_callback],
        verbose_eval=False,
    )

    # The final validation loss
    val_loss = model.eval(dval).split(":")[1]
    val_loss = float(val_loss)

    return val_loss   # minimize

# Create or resume study
study = optuna.create_study(
    study_name="xgb_pruning_demo",
    storage="sqlite:///optuna_xgb.db",
    direction="minimize",
    sampler=optuna.samplers.TPESampler(seed=42, multivariate=True),
    pruner=optuna.pruners.MedianPruner(n_startup_trials=10, n_warmup_steps=50),
    load_if_exists=True,
)

# MLflow integration
mlflow_callback = MLflowCallback(tracking_uri="databricks", metric_name="val_logloss")

study.optimize(objective, n_trials=100, callbacks=[mlflow_callback])

print("Best params:", study.best_params)
print("Best value:", study.best_value)
print("Number of pruned trials:", sum(1 for t in study.trials
                                       if t.state == optuna.trial.TrialState.PRUNED))
```

What's happening:

1. The search space is defined inside `objective`. Six hyperparameters, types selected appropriately, log scaling where appropriate.
2. `XGBoostPruningCallback` is one of many Optuna integrations — it wires XGBoost's per-boosting-round evaluation into `trial.report` automatically. Optuna also has integrations for Keras, PyTorch Lightning, sklearn (with partial_fit), LightGBM, and others.
3. The pruner is `MedianPruner` with 10 startup trials (no pruning for the first 10 — need history to compare against) and 50 warmup steps (don't prune before round 50 — early in training is unreliable).
4. The TPE sampler uses `multivariate=True` for joint density estimation.
5. The study is RDB-backed; can be resumed or run from multiple processes.
6. MLflow callback logs every trial.

In practice, this kind of setup runs 100 trials with maybe 40 pruned, taking about half the compute of running 100 trials without pruning, and finds a configuration comparable to or better than the unpruned version. Free improvement.

---

## 54.11 Optuna vs Hyperopt: the side-by-side

For your career, internalize the comparison:

| Aspect | Hyperopt | Optuna |
|---|---|---|
| Algorithm | TPE | TPE (default); CMA-ES, NSGA-II, Random, Grid also available |
| Multivariate TPE | No (independence assumption) | Yes (with `multivariate=True`) |
| Search space style | Declarative (`space = {...}`) | Define-by-run (`trial.suggest_*` inside objective) |
| Conditional search spaces | Yes, but awkward (nested `hp.choice` over dicts) | Trivial (just use Python `if` in objective) |
| Categorical return | Index (use `space_eval` to recover values) | Value directly |
| Pruning | No | Yes (MedianPruner, HyperbandPruner, etc.) |
| Multi-objective | No | Yes (NSGAIISampler) |
| Persistence | Pickle Trials | RDB-backed (SQLite, PostgreSQL, etc.) |
| Parallelism | `SparkTrials` (round-based) | RDB-coordinated (asynchronous) |
| MLflow integration | Automatic on Databricks | Via `MLflowCallback` |
| Active development | Minimal since ~2019 | Active (Preferred Networks) |
| ML Associate exam | Tested | Not tested (yet) |
| ML Professional exam | Tested | Tested |
| Databricks Runtime ML 17+ | Removed | Default |

For the ML Associate exam: **know Hyperopt cold**. The questions are still on Hyperopt.

For your job: **prefer Optuna**. Cleaner API, better algorithm options, free pruning, better long-term support.

For the ML Professional exam: **know both**. Especially Optuna's pruners and multi-objective.

---

## 54.12 Engineering notes

A few practical reminders:

**`load_if_exists=True` is your friend.** Always use it. It makes restarts and resumption trivial.

**Set `seed` on the sampler.** Optuna's TPE has its own random state. Setting `seed` on the sampler makes runs reproducible.

**Pruning makes trial counts misleading.** "100 trials" doesn't mean 100 full evaluations when pruning is on. Track compute time, not trial count, for budget planning.

**Multi-objective comes with overhead.** NSGA-II is more expensive per step than TPE. For two objectives with 100 trials and a fast model, fine; for two objectives with 1000 trials and a slow model, the sampler overhead can become noticeable.

**`study.trials_dataframe()` is great for analysis.** Returns all trials as a pandas DataFrame, with columns for each parameter and the value. Easy to inspect, sort, plot.

**Visualization.** Optuna ships visualization helpers (`optuna.visualization.*`) — `plot_optimization_history`, `plot_param_importances`, `plot_parallel_coordinate`, `plot_slice`. Run them in a notebook to inspect a study. The `plot_param_importances` is especially valuable — it tells you which hyperparameters actually mattered, which informs whether to keep them in future searches or fix them.

**Optuna is slowly absorbing Ray Tune's role.** For very-large-scale HPO (1000+ trials, multi-node clusters), Ray Tune used to be the answer. Optuna with RDB-backed parallelism is catching up. For most ML Associate-style problems, you don't need Ray Tune.

---

## 54.13 What this builds on / where this returns

**Builds on:**

- *Chapter 52* — TPE, the algorithm under both Hyperopt and Optuna.
- *Chapter 53* — Hyperopt, the predecessor that Optuna improves upon.
- *Chapter 51* — Bayesian optimization framework, of which Optuna provides multiple instances (TPE, CMA-ES).

**Returns in:**

- *Chapter 65* — pyspark.ml HPO; Optuna's role as a Spark-friendly alternative.
- *Chapter 72* — MLflow integration (`MLflowCallback`).
- *Chapter 75* — exam-day strategy; this is the chapter where we discuss Optuna's likely future on the exam.
- Topic 11 of this repo (ML Professional curriculum) — Optuna in production, with pruning and multi-objective tested directly.

---

## 54.14 Exercises

1. **API translation.** Translate the following Hyperopt search space to Optuna's `trial.suggest_*` calls inside an objective:
   ```python
   space = {
       "lr": hp.loguniform("lr", np.log(1e-4), np.log(1e-1)),
       "n_layers": hp.quniform("n_layers", 1, 5, 1),
       "activation": hp.choice("activation", ["relu", "tanh", "elu"]),
   }
   ```

2. **The choice trap revisited.** Suppose `best = study.best_params` after an Optuna run with `trial.suggest_categorical("kernel", ["linear", "rbf"])`. What is `best["kernel"]`? How does this differ from Hyperopt?

3. **Pruning savings.** A study runs 200 trials, of which 80 are pruned at an average of 25% completion. If a full trial takes 60 seconds, what is the total compute time saved by pruning?

4. **Conditional search.** Write an Optuna objective for the search space: `optimizer ∈ {"adam", "sgd"}`; if adam, also tune `beta1 ∈ [0.5, 0.99]` and `beta2 ∈ [0.9, 0.999]`; if sgd, also tune `momentum ∈ [0.0, 0.99]` and `nesterov ∈ {True, False}`. Use `if`/`else` in the objective.

5. **Multi-objective.** You want to tune a random forest to maximize accuracy *and* minimize the number of trees (a proxy for inference latency). Write the objective function signature and create the study with the right directions.

6. **Pruner choice.** For each scenario, pick the most appropriate Optuna pruner: (a) training a small XGBoost model with 200 trees; (b) training a deep neural network for 100 epochs; (c) you know any val loss above 0.9 is unusable. Justify briefly.

7. **Resume.** Your study with `storage="sqlite:///study.db"` ran 50 trials and the process was killed. Write code that resumes the study and runs 50 more trials (so the study ends with 100 total).

8. **TPE multivariate.** Why might `multivariate=True` help on a problem where `learning_rate` and `n_estimators` interact (low LR + high n_est is good; high LR + low n_est is also good; mixing is bad)? Sketch the difference between marginal TPE and multivariate TPE on this kind of landscape.

9. **MLflow logging.** Sketch the relationship between Optuna's `MLflowCallback` and Optuna's `study.trials`. Are they the same data? When might they diverge?

10. **The samplers compared.** For each of the following problems, which Optuna sampler is most appropriate? (a) 3 continuous hyperparameters, 200 trial budget; (b) 8 mixed-type hyperparameters, 50 trial budget; (c) 5 continuous hyperparameters, 1000 trial budget; (d) baseline run for comparison purposes.

11. **The pruning callback.** For a sklearn model that doesn't support intermediate evaluations (no `warm_start`, no per-epoch tracking), can you still use pruning? Why or why not?

12. **The choice question.** Your manager asks you to add HPO to a project. You have Databricks ML Runtime 16 (Hyperopt still available, Optuna also available, both are options). Which do you choose for: (a) a one-off model that will be retrained quarterly; (b) a model that will be part of a long-running production training pipeline; (c) a model where you need pruning to handle long training runs. Justify each.

<details>
<summary>Answers</summary>

1. ```python
   def objective(trial):
       lr = trial.suggest_float("lr", 1e-4, 1e-1, log=True)
       n_layers = trial.suggest_int("n_layers", 1, 5)
       activation = trial.suggest_categorical("activation", ["relu", "tanh", "elu"])
       ...
   ```

2. `best["kernel"]` is the string `"linear"` or `"rbf"` (the value, not an index). In Hyperopt with `hp.choice`, you'd get `0` or `1` (the index) and need `space_eval` to recover. Optuna eliminates this trap entirely.

3. Full trials saved: 80 trials × (1 - 0.25) = 60 full trial-equivalents saved. At 60 seconds each: 3600 seconds ≈ 60 minutes of compute saved.

4. ```python
   def objective(trial):
       optimizer = trial.suggest_categorical("optimizer", ["adam", "sgd"])
       if optimizer == "adam":
           beta1 = trial.suggest_float("beta1", 0.5, 0.99)
           beta2 = trial.suggest_float("beta2", 0.9, 0.999)
           opt = Adam(beta1=beta1, beta2=beta2)
       else:
           momentum = trial.suggest_float("momentum", 0.0, 0.99)
           nesterov = trial.suggest_categorical("nesterov", [True, False])
           opt = SGD(momentum=momentum, nesterov=nesterov)
       # ... train with opt, return loss
   ```

5. ```python
   def objective(trial):
       n_est = trial.suggest_int("n_estimators", 50, 1000)
       max_depth = trial.suggest_int("max_depth", 3, 20)
       model = RandomForestClassifier(n_estimators=n_est, max_depth=max_depth)
       model.fit(X_train, y_train)
       accuracy = model.score(X_val, y_val)
       return accuracy, n_est   # maximize accuracy, minimize n_est

   study = optuna.create_study(
       directions=["maximize", "minimize"],
       sampler=optuna.samplers.NSGAIISampler(),
   )
   ```

6. (a) `MedianPruner` — simple, works well for tree-count tracking. (b) `HyperbandPruner` — designed for expensive trials with epoch-level reports. (c) `ThresholdPruner(upper=0.9)` — explicit threshold-based.

7. ```python
   study = optuna.create_study(
       study_name="my_study",
       storage="sqlite:///study.db",
       load_if_exists=True,   # this resumes
       direction="minimize",
   )
   study.optimize(objective, n_trials=50)
   # Now 100 total: the original 50 plus 50 more.
   ```

8. Marginal TPE estimates "good `learning_rate`" and "good `n_estimators`" separately. In the described XOR-like landscape, marginal stats say "any LR is fine; any n_est is fine" — no marginal signal. TPE proposes random-ish combinations and might never lock onto the two good basins. Multivariate TPE estimates the joint density, capturing "good pairs are (low LR, high n_est) OR (high LR, low n_est)". TPE then samples from these two modes specifically.

9. They are mostly the same data — each `trial` in `study.trials` corresponds to one MLflow run created by the callback. They can diverge if (a) the MLflow callback fails for some trials (network error, etc.) but the trial still completes — the trial is in `study.trials` but not in MLflow; or (b) MLflow has runs that aren't from Optuna (e.g., your manual training runs from before HPO).

10. (a) **CmaEsSampler** — continuous, moderate dim, decent budget; CMA-ES shines here. (b) **TPESampler with multivariate=True** — mixed types, modest budget; TPE handles mixed natively. (c) **TPESampler** or **CmaEsSampler** — large budget, continuous; either works, CMA-ES probably slightly better for pure continuous. (d) **RandomSampler** — the baseline.

11. You can still use pruning, but only with a single "intermediate" report at the end of the trial — which is the same as no pruning. The point of pruning is to abort *during* training. If the model can't be evaluated mid-training, there's no information to act on. You'd need to either find a way to report intermediate values (e.g., for sklearn, `partial_fit` for some models) or accept that pruning won't help for that model.

12. (a) **Either works**; Optuna is slightly nicer ergonomically, no migration cost since it's one-off. (b) **Optuna**, because the pipeline will outlive Hyperopt's support window (DBR 17 removes it). Migrating later is more painful than starting on Optuna now. (c) **Optuna**, definitively. Hyperopt has no pruning; Optuna's `MedianPruner` or `HyperbandPruner` provides what you need for long training runs.

</details>
