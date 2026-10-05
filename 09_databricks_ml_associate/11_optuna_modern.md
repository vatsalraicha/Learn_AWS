# Module 11 — Optuna: The Modern Replacement

> **Goal of this module:** Learn enough Optuna to write production HPO code on Databricks today (DBR ML 17+), and to recognize Optuna patterns if/when the next exam revision swaps in Optuna. The current March 2025 exam tests Hyperopt explicitly — Optuna is contextual knowledge plus the recommended path forward.
>
> **Maps to exam objectives:** *Implicit support for "perform random/grid/Bayesian search · parallelize · choose tuning method"* (Domain 3, 31%). Direct Optuna questions are unlikely on the current exam but probable on the next revision.

---

## Coverage map

The current Mar 2025 exam explicitly tests Hyperopt (Module 10). Optuna's direct objective coverage:
- "Perform random or grid or Bayesian search" — Optuna offers all three via samplers (TPESampler / RandomSampler / GridSampler)
- "Parallelize single node models for HPO" — `n_jobs=K` / storage-coordinated distributed

You learn Optuna so that if your exam window slips past the next exam guide revision (expected late 2026, may drop Hyperopt), you're covered.

---

## Why Optuna replaced Hyperopt on Databricks

- **Hyperopt is unmaintained.** Last meaningful release was 2021. Bug reports go unanswered.
- **Optuna is actively developed** with pruners, multi-objective, distributed coordination via storage backends.
- **Better integration with modern ML stacks** — first-class support for scikit-learn, XGBoost, LightGBM, PyTorch, TensorFlow, Keras pruner callbacks.
- **MLflow autolog support** — `mlflow.optuna.autolog()` since MLflow 2.16.
- **Cleaner trial API** — `trial.suggest_*` is more readable than `hp.*`.

Databricks recommends Optuna for new HPO code as of DBR ML 17+. Hyperopt is removed from the runtime.

---

## Mental model comparison

| Concept | Hyperopt | Optuna |
|---------|----------|--------|
| Top-level orchestrator | `fmin(...)` | `study.optimize(...)` |
| Search space | nested dict of `hp.*` | inline calls `trial.suggest_*` inside objective |
| Algorithm | `tpe.suggest`, `rand.suggest` | `TPESampler`, `RandomSampler`, `GridSampler`, `CmaEsSampler` |
| Trial storage | `Trials()` / `SparkTrials()` | `optuna.create_study(storage=...)` |
| Parallelism | `SparkTrials(parallelism=K)` | `study.optimize(..., n_jobs=K)` (joblib) or via Ray |
| Loss direction | Minimize only (negate to maximize) | `direction="maximize"` or `"minimize"` — explicit |
| Pruning (early stop bad trials) | Not built-in | First-class via pruners |

---

## Minimum viable Optuna

```python
import optuna
import math

def objective(trial):
    params = {
        'max_depth': trial.suggest_int('max_depth', 3, 15),
        'learning_rate': trial.suggest_float('lr', 1e-5, 1e-1, log=True),
        'optimizer': trial.suggest_categorical('opt', ['adam', 'sgd', 'rmsprop']),
        'subsample': trial.suggest_float('subsample', 0.5, 1.0),
    }
    model = train(**params)
    auc = eval_model(model)
    return auc   # return what you want optimized

study = optuna.create_study(direction="maximize")   # no negation needed
study.optimize(objective, n_trials=50)

print(study.best_params)
# {'max_depth': 7, 'lr': 0.0023, 'opt': 'adam', 'subsample': 0.78}
# Note: best_params returns ACTUAL VALUES, not indices!
```

> ⚠️ **Optuna advantage over Hyperopt #1:** `best_params` returns actual values, not indices. No `space_eval` step needed.
>
> **Optuna advantage #2:** `direction="maximize"` is explicit. You return AUC directly and it's clear what you mean. No negation pitfalls.

---

## The `trial.suggest_*` API

All `suggest_*` calls take `name` (string) as first arg, then range parameters.

| Call | Returns | Example |
|------|---------|---------|
| `trial.suggest_int(name, low, high)` | int in [low, high] | `'n_estimators': trial.suggest_int('n', 50, 500)` |
| `trial.suggest_int(name, low, high, step=K)` | int in [low, high] step K | `trial.suggest_int('depth', 3, 15, step=2)` |
| `trial.suggest_int(name, low, high, log=True)` | int log-uniformly | `trial.suggest_int('batch', 16, 512, log=True)` |
| `trial.suggest_float(name, low, high)` | float in [low, high] uniform | `'dropout': trial.suggest_float('d', 0.0, 0.5)` |
| `trial.suggest_float(name, low, high, log=True)` | float log-uniform | `'lr': trial.suggest_float('lr', 1e-5, 1e-1, log=True)` |
| `trial.suggest_float(name, low, high, step=Q)` | float quantized to multiples of Q | `trial.suggest_float('alpha', 0.1, 1.0, step=0.1)` |
| `trial.suggest_categorical(name, choices)` | one of the choices (actual value) | `trial.suggest_categorical('opt', ['adam', 'sgd'])` |

Note: `suggest_uniform`, `suggest_loguniform`, `suggest_discrete_uniform` are **deprecated aliases** for `suggest_float` with appropriate kwargs. New code uses `suggest_float`.

---

## Samplers — Optuna's algorithm zoo

Pass via `optuna.create_study(sampler=...)`:

| Sampler | Algorithm |
|---------|-----------|
| `TPESampler` (default) | Tree-structured Parzen — same family as Hyperopt's `tpe.suggest` |
| `RandomSampler` | Random search |
| `GridSampler({'param': [values, ...]})` | Exhaustive grid search |
| `CmaEsSampler` | CMA-ES (covariance matrix adaptation) — for continuous spaces |
| `NSGAIISampler` | Multi-objective evolutionary |
| `BoTorchSampler` | Gaussian process via BoTorch |

```python
from optuna.samplers import TPESampler, GridSampler

# Bayesian (default)
study = optuna.create_study(direction="maximize", sampler=TPESampler(seed=42))

# Grid search
study = optuna.create_study(
    sampler=GridSampler({
        'max_depth': [3, 5, 7, 10],
        'lr': [0.01, 0.1, 0.3],
    })
)
study.optimize(objective, n_trials=12)   # 4 × 3 = 12 combinations
```

> ⚠️ **Note:** Optuna has **built-in grid search** via `GridSampler`. Hyperopt does not. This is the technical reason Optuna can replace both Hyperopt and Spark ML's `ParamGridBuilder` if you want a unified API.

---

## Pruners — kill bad trials early

This is Optuna's killer feature that Hyperopt lacks. Pruners stop unpromising trials early based on intermediate metrics (e.g., per-epoch validation loss).

```python
from optuna.pruners import MedianPruner

study = optuna.create_study(
    direction="maximize",
    pruner=MedianPruner(n_startup_trials=5, n_warmup_steps=10),
)

def objective(trial):
    lr = trial.suggest_float('lr', 1e-5, 1e-1, log=True)
    model = build_model(lr)
    for epoch in range(50):
        train_one_epoch(model)
        val_auc = compute_val_auc(model)
        trial.report(val_auc, step=epoch)
        if trial.should_prune():
            raise optuna.TrialPruned()
    return val_auc

study.optimize(objective, n_trials=50)
```

Common pruners:
- `MedianPruner` — kill trials worse than the median at each step
- `PercentilePruner` — kill trials below a percentile
- `HyperbandPruner` — multi-fidelity, aggressive pruning
- `SuccessiveHalvingPruner` — kill all but top half repeatedly

This is huge for deep learning HPO. Hyperopt can't natively do this.

---

## Parallelism

### Single-machine (joblib)

```python
study.optimize(objective, n_trials=100, n_jobs=4)
# 4 parallel workers via joblib
```

Simple but limited to one machine's cores.

### Distributed via storage backend

```python
study = optuna.create_study(
    study_name="my-search",
    storage="sqlite:///optuna.db",
    direction="maximize",
)
# Run from multiple processes/notebooks — they coordinate via SQLite
study.optimize(objective, n_trials=100)
```

Storage backends: SQLite (local), MySQL, PostgreSQL. Multiple Python processes can connect to the same study and run trials in parallel.

### Spark integration

There's no native `SparkTrials` equivalent. Approaches:

1. **`joblibspark` backend** — `with joblib.parallel_backend("spark", n_jobs=K): study.optimize(...)`.
2. **Ray Tune integration** — `OptunaSearch` algorithm passed to Ray Tune.
3. **Manual distribution** — multiple Databricks jobs hitting one shared storage.

Databricks' recommendation post-Hyperopt: **use Optuna with Ray Tune** for cluster-wide HPO of single-node models.

---

## MLflow integration

### Automatic via `mlflow.optuna.autolog()`

```python
import mlflow

mlflow.set_experiment("/Users/vatsal/optuna")
mlflow.optuna.autolog()   # NEW: auto-logs every Optuna trial

with mlflow.start_run(run_name="optuna_run"):
    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=50)
```

Each trial becomes a nested MLflow run with params/metrics. The parent run holds the best result.

### Manual

```python
def objective(trial):
    params = {...}
    with mlflow.start_run(nested=True):
        mlflow.log_params(params)
        score = train_and_eval(**params)
        mlflow.log_metric('auc', score)
        return score
```

---

## Optuna study object — useful attributes

```python
study = optuna.create_study(direction="maximize")
study.optimize(objective, n_trials=50)

study.best_value          # 0.92
study.best_params         # {'max_depth': 7, 'lr': 0.001, ...}
study.best_trial          # Trial object
study.trials              # list of all Trial objects

# DataFrame view
df = study.trials_dataframe()
# columns: number, value, params_*, datetime_start, state, ...

# Visualize via plotly
import optuna.visualization as vis
vis.plot_optimization_history(study)
vis.plot_param_importances(study)
vis.plot_parallel_coordinate(study)
vis.plot_slice(study)
```

---

## Side-by-side comparison

Same problem, two libraries:

### Hyperopt
```python
from hyperopt import fmin, tpe, hp, STATUS_OK, Trials
from hyperopt.pyll import scope

def objective(params):
    score = train_and_eval(params)
    return {'loss': -score, 'status': STATUS_OK}

space = {
    'max_depth': scope.int(hp.quniform('max_depth', 3, 15, 1)),
    'lr': hp.loguniform('lr', math.log(1e-5), math.log(1e-1)),
    'optimizer': hp.choice('optimizer', ['adam', 'sgd']),
}

best = fmin(fn=objective, space=space, algo=tpe.suggest, max_evals=50,
            trials=Trials())
best_values = space_eval(space, best)   # need this to resolve choice index
```

### Optuna
```python
import optuna

def objective(trial):
    params = {
        'max_depth': trial.suggest_int('max_depth', 3, 15),
        'lr': trial.suggest_float('lr', 1e-5, 1e-1, log=True),
        'optimizer': trial.suggest_categorical('optimizer', ['adam', 'sgd']),
    }
    return train_and_eval(params)   # return what to maximize

study = optuna.create_study(direction="maximize")
study.optimize(objective, n_trials=50)
print(study.best_params)
```

The Optuna version is shorter, has no negation pitfall, returns actual values not indices, and supports pruners.

---

## When the exam scope might shift

The current March 2025 exam guide tests Hyperopt. A future revision (expected late 2026 based on Databricks' Hyperopt removal in DBR ML 17 + typical exam guide cadence) likely:

1. Removes "Hyperopt's `fmin`" from objectives.
2. Adds "use Optuna for hyperparameter tuning."
3. Possibly removes the explicit "Bayesian/random/grid" objective wording (Optuna unifies all three under `GridSampler`/`RandomSampler`/`TPESampler`).
4. Adds pruner-related concepts.

For now: **know Hyperopt for the exam, use Optuna in your day job.** Both are 1-2 hours of study to be solid on.

---

## Common pitfalls

### Returning `-score` in Optuna

You don't need to negate. Use `direction="maximize"` and return the actual score.

### Confusing `suggest_loguniform` (deprecated) with `suggest_float(..., log=True)`

Old Optuna code used `trial.suggest_loguniform`. New code uses `suggest_float(..., log=True)`. Both work; the new form is preferred.

### Forgetting `seed` on the sampler

For reproducibility: `TPESampler(seed=42)`. Without it, runs differ.

### Trying to use `SparkTrials` with Optuna

No such thing. Use `n_jobs`, `joblibspark`, Ray Tune, or distributed storage.

### Pruning inside Spark ML

Pruning works for iterative algorithms with per-epoch metrics. Spark ML's `RandomForestClassifier.fit` is one call — nothing to prune mid-training. Use pruners with deep learning, XGBoost (per-round eval), LightGBM, etc.

---

## What the exam tests on this module

The current exam doesn't directly test Optuna, but recognize patterns for the future:

> 🎯 **Likely exam-tested in 2026-2027 revisions:**
> - `optuna.create_study(direction="maximize"|"minimize")`
> - `trial.suggest_int / suggest_float / suggest_categorical`
> - `study.optimize(objective, n_trials=N, n_jobs=K)`
> - `study.best_params`, `study.best_value`
> - Optuna pruners as the modern feature Hyperopt lacks
> - `mlflow.optuna.autolog()` integration

If you see "Optuna" on an answer choice on the current exam (it shouldn't be the correct answer to a tuning question — that's Hyperopt — but it may appear as a distractor or in a "best practice" framing), the right answer is whichever the question scopes to.

---

## Mini quiz

1. Convert this Hyperopt space to Optuna:
   ```python
   space = {
       'max_depth': hp.quniform('max_depth', 3, 15, 1),
       'lr': hp.loguniform('lr', math.log(1e-5), math.log(1e-1)),
       'optimizer': hp.choice('optimizer', ['adam', 'sgd']),
   }
   ```
2. You want to maximize ROC AUC. Your objective returns AUC directly. In Optuna, what `direction` do you pass to `create_study`?
3. You're doing 200 trials of XGBoost with 1000 boost rounds each. Half the trials hit a clearly-bad local minimum by round 100. Which Optuna feature should you use?
4. Optuna study runs across 4 notebooks coordinating via what kind of backend?
5. In Optuna, `study.best_params['optimizer']` returns `'adam'`. In Hyperopt, what would `best['optimizer']` return for the same parameter `hp.choice('optimizer', ['adam', 'sgd'])`?

### Answers

1. ```python
   def objective(trial):
       max_depth = trial.suggest_int('max_depth', 3, 15)
       lr = trial.suggest_float('lr', 1e-5, 1e-1, log=True)
       optimizer = trial.suggest_categorical('optimizer', ['adam', 'sgd'])
       ...
   ```
2. `direction="maximize"`. No negation needed.
3. **A pruner.** `MedianPruner` or `HyperbandPruner` will kill trials performing worse than the median at intermediate steps. Use `trial.report(value, step=round)` and `if trial.should_prune(): raise optuna.TrialPruned()` inside the objective.
4. **A shared storage backend** — typically SQLite (`sqlite:///optuna.db`), MySQL, or PostgreSQL. Multiple processes connect to the same study via `optuna.create_study(storage=...)`.
5. Hyperopt returns the **index** (`0` for adam, `1` for sgd). You'd need `space_eval(space, best)` to recover `'adam'`. Optuna returns the actual chosen value directly.
