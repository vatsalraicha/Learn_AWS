# Quiz 01 — Model Development (Section 1, ~45%)

> Covers modules **01-06**: Advanced MLflow tracking, custom PyFunc, Optuna + Ray, Feature Engineering in UC, advanced Spark ML, ensembles via PyFunc.
>
> **80 questions** — Recall (24) / Apply (32) / Diagnose (16) / Defend (8). Target: ≥ 80% before scheduling. ~2 min/question.
>
> All questions are **ORIGINAL** — written from the verbatim Sept 30 2025 exam objectives. No NDA content.

---

## Recall (Qs 1-24)

1. Which Python statement opens a child run nested under an active MLflow parent run?
2. Which two parameters of `mlflow.start_run()` together let you resume an existing run rather than start a new one?
3. Name the two methods of `mlflow.pyfunc.PythonModel` that a custom model MUST implement.
4. Which MLflow function infers a model signature from a sample input and prediction output?
5. What is the canonical `model_uri` syntax to load the model version aliased `@champion` from UC registered model `prod.ml.churn`?
6. Which client class replaces the deprecated `FeatureStoreClient` in 2025?
7. Name the two `FeatureLookup` keyword arguments required for **point-in-time correctness**.
8. Which Optuna sampler is Optuna's default and is described as a Bayesian-style Tree-structured Parzen Estimator?
9. Which Optuna integration class lets each trial log to a separate MLflow run?
10. Which Optuna class distributes trials across a Databricks Spark cluster?
11. Name three Optuna pruners commonly used to early-stop unpromising trials.
12. What MLflow flavor are you forced to use when you need request-time preprocessing + a custom artifact + multi-model routing?
13. Which file does `mlflow.pyfunc.log_model` generate to declare runtime dependencies?
14. Which Spark ML class chains feature transformers + an estimator into a serializable workflow?
15. Which two Spark ML evaluator classes cover binary classification vs multiclass classification?
16. Which Spark ML class performs k-fold cross-validation with a parameter grid?
17. Which `CrossValidator` parameter controls **how many models train in parallel** per fold?
18. What is the default value of `CrossValidator.parallelism` if you don't set it?
19. Which Pandas Function API method runs a Python function once per group on partitioned data?
20. To register a model in **Unity Catalog**, what optional-elsewhere argument is now **required** by `log_model`?
21. Which MLflow API searches across runs in an experiment with a filter string?
22. In Optuna, which built-in result attribute lets you retrieve the best-performing trial after `study.optimize` completes?
23. Which MLflow flavor function packages feature-store metadata into a logged model so inference auto-joins features?
24. Name the two artifact-logging functions for (a) an arbitrary file on disk and (b) a matplotlib `Figure`.

## Apply (Qs 25-56)

25. You want to run a parent MLflow run that contains 50 child runs (one per HP set) and a final "best-retrained" run. Sketch the `with` / `start_run` structure in 5 lines or fewer.

26. You need a model that, at predict-time, queries a feature table by `customer_id`, applies a custom transformation, then calls an XGBoost model. Which MLflow construct do you use, and what goes in `load_context` vs `predict`?

27. You want to launch 200 Optuna trials, each trying a different `learning_rate` / `n_estimators` combo, distributed across a 4-worker Spark cluster, with each trial visible as a separate MLflow run. List the four objects/callables you wire together.

28. A teammate proposes `SparkTrials` from Hyperopt with `parallelism=8`. The cert exam is the Sept 2025 refresh. What's the correct modern replacement and why?

29. You're training a feature table over a streaming source. Which `FeatureEngineeringClient` method writes the streaming output to a UC feature table with **merge** semantics?

30. A `FeatureLookup` is configured with `lookup_key="customer_id"` but **no** `timestamp_lookup_key`. What kind of data leakage can occur, and what does adding `timestamp_lookup_key="event_ts"` prevent?

31. You need sub-10ms feature retrieval at request-time for a model-serving endpoint. Which UC-native construct backs the offline feature table and how is it created?

32. You're computing haversine distance between a user-supplied pickup point and a precomputed driver location. The transformation must run identically at training and serving time. Which feature-store construct fits, and what decorator is used?

33. You want to score a registered UC model on a 500M-row Delta table. Provide the one-line MLflow call that creates the Spark UDF and the `spark.read.table(...).withColumn(...)` invocation.

34. Per the official sample question, the answer to "distribute Optuna trials and log each trial to MLflow on Databricks" is which **two** integration objects?

35. Write the `mlflow.pyfunc.log_model` call (3-4 lines) that registers a custom model to UC under `prod.ml.recommender`, including a signature and an input example.

36. You're training one XGBoost model per `store_id` (1000+ stores), each with its own data slice. Which Pandas Function API method is appropriate, and what's the function signature shape?

37. A `Pipeline` contains a `StringIndexer` + `OneHotEncoder` + `VectorAssembler` + `LogisticRegression`. After fitting on training data, you save it. Which file format does Spark ML use, and how do you reload it?

38. You log a model with `mlflow.sklearn.log_model(..., registered_model_name="prod.ml.churn")`. Then you want to mark this newly created version as the challenger. Which client method sets the `@challenger` alias?

39. You want a `CrossValidator` to run 5 folds × 12 hyperparameter combinations = 60 models. You have 8 worker cores. What value of `parallelism` would you set, and what's the tradeoff vs `parallelism=1`?

40. You need to ensemble three sklearn classifiers (LR, RF, XGB) with per-class weighted soft voting + a custom rule that overrides predictions when one feature exceeds a threshold. Which MLflow flavor are you required to use, and why is `sklearn.VotingClassifier` insufficient here?

41. You want to compare TPESampler vs CmaEsSampler on the same objective function within one Optuna study. Is that possible in a single `Study`, or do you need two studies? Justify in one sentence.

42. Inside `objective(trial)`, you call `mlflow.start_run(nested=True)`. Where must the parent `mlflow.start_run()` live for nesting to take effect?

43. You enable `mlflow.autolog()` before calling `optuna.create_study().optimize(...)`. After 100 trials, you find the experiment has only HPs and metrics logged — **no** model artifacts. What's the missing manual step?

44. Write the 3-line code block that uses `mlflow.models.infer_signature` on `X_test` and `model.predict(X_test)` and passes it into `log_model`.

45. You want to serve a custom PyFunc model on Model Serving. The model needs a large embedding file (200 MB). Where do you point it from, and which PyFunc method loads it once at endpoint start rather than every request?

46. A teammate wants to use **`FeatureStoreClient.create_feature_table`** in 2026. You tell them the API is deprecated and point them at the modern equivalent. Provide the import line and the modern method name.

47. You want to define a **custom transformer** in Spark ML that adds an interaction column (`featA * featB`). Which two base classes do you subclass, and what is the single method you must override?

48. The training set is 80 GB; you have an r5.4xlarge driver with 128 GB RAM. The model is a gradient-boosted tree. Vertical or horizontal scaling — and which framework matches that choice?

49. You're using Optuna for multi-objective optimization (minimize loss AND minimize inference latency). Which sampler class supports multi-objective natively, and what does `study.best_trial` return in that case?

50. You want a `Pipeline` with hyperparameter tuning over (a) `LogisticRegression.regParam` and (b) `StringIndexer.handleInvalid`. Sketch the `ParamGridBuilder` and explain whether tuning *transformer* params via `ParamGridBuilder` works.

51. You want to call `study.optimize(objective, n_trials=500, callbacks=[mlflc])` where `mlflc` is `MLflowCallback(...)`. Which two keyword arguments of `MLflowCallback` matter most: experiment_name and what else?

52. You're versioning training code in Git. The same code runs in dev, staging, and prod. Which Databricks construct lets you parameterize **catalog name** so the dev run writes to `dev.ml.tbl` and the prod run writes to `prod.ml.tbl` without any code change?

53. You want to write a UC feature table from a streaming DataFrame and have it served by an online table. Which `FeatureEngineeringClient` method writes the offline table, and what additional CLI/SDK call creates the online sibling?

54. You need to log a confusion matrix as a model artifact during training. Which two API calls in sequence accomplish this?

55. Which Spark ML class outputs both a model and a `bestModel` attribute exposing the winning hyperparameters?

56. Sketch the `databricks-feature-engineering` `create_training_set` call that joins a labels DataFrame (`labels_df` with `customer_id` + `event_ts` + `y`) with a feature table `prod.ml.cust_features` using point-in-time correctness on `event_ts`.

## Diagnose (Qs 57-72)

57. A teammate registers a model to UC and it fails with `MlflowException: Model signature is required for models in Unity Catalog`. What did they forget, and how do they fix it without re-training?

58. An Optuna study runs all 100 trials but the MLflow experiment shows only ONE run with 100 sets of HPs concatenated. What's misconfigured?

59. `CrossValidator.fit()` is set with `parallelism=4` on a single-node driver-only cluster. You see no parallelism in the Spark UI — only sequential model training. Why?

60. A custom PyFunc model serves correctly locally but on Model Serving it errors with `ModuleNotFoundError: No module named 'company_utils'`. What did the developer forget in `log_model`?

61. A `FeatureLookup` with `timestamp_lookup_key` set still produces data leakage in production. The lookup is configured against a feature table that has `timestamp_keys=["update_ts"]` but the label DataFrame uses an `event_ts` column 30 minutes after each customer event. Why is leakage still possible, and what config change fixes it?

62. You wrap a sklearn model in PyFunc and override `predict`. The model is registered, but `spark_udf` raises `TypeError: predict() got an unexpected keyword argument 'params'`. What is the cause and the fix?

63. `study.optimize(callbacks=[MLflowCallback(...)])` runs but every trial logs to the **default** experiment instead of the one you specified. What's wrong with the callback init?

64. A `Pipeline` saved with `pipeline.save(path)` cannot be reloaded — `Spark Pipeline expected meta.json`. What is the most likely root cause and the fix?

65. `mlflow.autolog()` is on. A Hyperopt search runs 200 trials. The "best model" recorded in the MLflow experiment under `@champion` alias is wrong — it points at trial 47, not the actual best. Diagnose. (Hint: there is no auto-promotion in Hyperopt autologging.)

66. A `pandas_udf` is misused: someone wraps a model and passes a `pd.DataFrame` in and expects a `pd.DataFrame` out. The UDF errors `Schema mismatch`. Which Pandas Function API method should they have used instead, and why?

67. `fe.score_batch(model_uri, df)` returns NaN for 30% of rows. The feature table has 100% coverage on the lookup keys. What is the next thing to check?

68. A model serving endpoint with a custom PyFunc model takes 8s to cold-start. The team blames Model Serving. What in the PyFunc class is the likely culprit, and where should heavy initialization actually live?

69. `mlflow.search_runs(experiment_ids=[..], filter_string="metrics.loss < 0.5")` returns 0 rows, but the UI clearly shows 50 such runs. What might be wrong with `experiment_ids` or with how `loss` was logged?

70. `mlflow.pyfunc.spark_udf(spark, model_uri)` works in a notebook but the same call inside a Jobs task raises `MlflowException: Could not resolve URI`. Diagnose two probable causes.

71. A `CrossValidator` with `numFolds=5` and 50 HP combos is set to `parallelism=20`. The cluster has 16 worker cores. The driver OOMs after 4 hours. Diagnose: where did parallelism go wrong?

72. After registering a UC model, the team's monitoring job cannot find it via `mlflow.models.get_model_info("models:/ml.churn@champion")`. The two-level name only references schema + model — what's missing for UC?

## Defend (Qs 73-80)

73. Defend the choice of `MLflowSparkStudy` over `MLflowCallback` alone when launching 1000 Optuna trials on Databricks.

74. Argue against using `sklearn.VotingClassifier` as a registered UC model, when at request-time you also need a feature-store lookup. What's the right pattern?

75. Defend using **single-node sklearn on a beefy driver** over SparkML on a multi-worker cluster for a 12 GB training set and a single XGBoost model.

76. Argue against logging the best Hyperopt/Optuna model as the "winner" using only autologging.

77. Defend point-in-time joins as a non-negotiable design constraint in regulated industries (e.g., healthcare claims, financial fraud).

78. Defend the use of `FeatureEngineeringClient.create_training_set` over a hand-written join in PySpark, even though both produce the same DataFrame.

79. Argue for (or against) tuning *transformer* parameters (like `StringIndexer.handleInvalid`) inside a `ParamGridBuilder` rather than fixing them up front.

80. Defend the answer "custom PyFunc + `load_context`" over "vanilla `mlflow.sklearn.log_model`" for a model that hits an external service (e.g., a low-latency cache) at inference time.

---

## Answers (don't peek until done)

1. `mlflow.start_run(nested=True)` — only works if a parent run is already active.
2. `run_id` (the existing run to resume) and `nested=False` is unrelated; the relevant pair is `run_id` + `experiment_id`.
3. `load_context(self, context)` and `predict(self, context, model_input)`.
4. `mlflow.models.infer_signature(model_input, model_output)`.
5. `models:/prod.ml.churn@champion`.
6. `databricks.feature_engineering.FeatureEngineeringClient`. > ⚠️ **Exam trap:** `FeatureStoreClient` from `databricks.feature_store` is deprecated.
7. `lookup_key` and `timestamp_lookup_key`.
8. `TPESampler`.
9. `optuna.integration.mlflow.MLflowCallback`.
10. `MLflowSparkStudy` (in `optuna-integration[mlflow]`).
11. `MedianPruner`, `SuccessiveHalvingPruner`, `HyperbandPruner`.
12. `mlflow.pyfunc` with a custom `PythonModel`.
13. `conda.yaml` (plus `python_env.yaml` / `requirements.txt`).
14. `pyspark.ml.Pipeline`.
15. `BinaryClassificationEvaluator` and `MulticlassClassificationEvaluator`.
16. `CrossValidator` (and `TrainValidationSplit` for a single split).
17. `parallelism`.
18. `1` (sequential by default).
19. `applyInPandas` (called via `groupBy(...).applyInPandas(fn, schema=...)`).
20. `signature` (or use `infer_signature`). UC enforces it.
21. `mlflow.search_runs(experiment_ids=[...], filter_string=...)`.
22. `study.best_trial` (and `study.best_value`, `study.best_params`).
23. `databricks.feature_engineering.FeatureEngineeringClient.log_model` (a.k.a. `fe.log_model`).
24. `mlflow.log_artifact(path)` and `mlflow.log_figure(fig, "name.png")`.

25.
```python
with mlflow.start_run(run_name="parent") as parent:
    for hp in hp_grid:
        with mlflow.start_run(nested=True, run_name=f"trial-{hp['lr']}"):
            mlflow.log_params(hp); mlflow.log_metric("cv_loss", train(hp))
    with mlflow.start_run(nested=True, run_name="best-refit"):
        mlflow.sklearn.log_model(best_model, "model", signature=sig)
```

26. **Custom PyFunc**. `load_context` loads the XGBoost model artifact + a feature-store client/connection (one-time). `predict` does the feature lookup + transformation + inference per request. This avoids re-loading the model on every call.

27. (a) `optuna.create_study(sampler=TPESampler())`, (b) `MLflowCallback(tracking_uri=..., metric_name=...)`, (c) `MLflowSparkStudy` distributing trials, (d) the `objective(trial)` function logging via the callback. The official sample answer endorses MLflowCallback + MLflowSparkStudy.

28. **Hyperopt is OUT in the Sept 2025 refresh.** Use **Optuna** with `MLflowSparkStudy` for Spark-distributed trials + `MLflowCallback` for per-trial MLflow logging. > ⚠️ **Exam trap:** Any answer choice using `SparkTrials` or `hyperopt.fmin` is the wrong 2025 answer.

29. `fe.write_table(name="cat.sch.feat", df=streaming_df, mode="merge")`.

30. **Training/serving skew via future-leaking features.** Without a timestamp key, the lookup returns the *current* (latest) feature value, which may be from after the event you're predicting. `timestamp_lookup_key="event_ts"` forces a point-in-time join: only feature values with `feature_ts <= event_ts` are returned.

31. An **Online Table** — UC-native, serverless, replicated from the offline Delta feature table. Create it via the Databricks SDK (`w.online_tables.create(...)`) or the UC UI. > ⚠️ **Exam trap:** "Online Stores" (legacy DynamoDB/Cosmos) is deprecated and a distractor.

32. **On-demand feature** via `@feature_function` decorator. Defined as a Python UDF over the request payload; the same Python runs at training and serving — no skew possible.

33.
```python
udf = mlflow.pyfunc.spark_udf(spark, "models:/prod.ml.scorer@champion")
spark.read.table("prod.silver.events").withColumn("pred", udf("f1", "f2", "f3"))
```

34. `MLflowCallback` (per-trial MLflow logging) + `MLflowSparkStudy` (Spark-distributed trials).

35.
```python
mlflow.pyfunc.log_model(
    artifact_path="model",
    python_model=MyRecommender(),
    signature=infer_signature(X_sample, y_sample),
    input_example=X_sample.iloc[:2],
    registered_model_name="prod.ml.recommender",
)
```

36. `groupBy("store_id").applyInPandas(train_one_store, schema=...)`. The function takes `pd.DataFrame -> pd.DataFrame`.

37. Spark ML uses a **directory** (not a single file) containing `metadata`, stage subdirs, `data` parquet. Reload with `PipelineModel.load(path)`.

38. `client.set_registered_model_alias(name="prod.ml.churn", alias="challenger", version=new_version)`.

39. Set `parallelism=8` (one per worker core). Tradeoff: faster wall-clock but each model gets less Spark parallelism internally; with `parallelism=1` each model can use all 8 cores but training is sequential.

40. **Custom PyFunc**. `VotingClassifier` doesn't support per-class weight overrides + threshold-rule overrides + custom voting logic. PyFunc lets you express arbitrary aggregation in `predict`. > ⚠️ **Exam trap:** "Use VotingClassifier + log_model" is wrong when you need conditional rules.

41. **Two studies** — `sampler` is a `Study`-level attribute set at creation. To compare samplers you create one study per sampler with the same objective and seed.

42. The parent must be active **on the same Python process / driver thread**. In Optuna with `MLflowCallback`, you typically don't wrap `optimize` in a parent run — the callback creates one run per trial. If you want true nesting under a parent, you must wrap `study.optimize` itself in `mlflow.start_run()` and pass `nested=True` to the callback (or wrap the per-trial run inside `objective`).

43. **Manually re-fit the best model and `mlflow.<flavor>.log_model(best_model, ...)`.** > ⚠️ **Exam trap:** Hyperopt/Optuna autologging logs trial HPs/metrics but does **NOT** auto-log the best model.

44.
```python
from mlflow.models import infer_signature
sig = infer_signature(X_test, model.predict(X_test))
mlflow.sklearn.log_model(model, "model", signature=sig)
```

45. Store the embedding as an MLflow **artifact** (`artifacts={"emb": "/dbfs/..."}` passed to `log_model`); access via `context.artifacts["emb"]` in `load_context`. Heavy loading goes in `load_context` (once at endpoint start), NOT `predict` (per request).

46. `from databricks.feature_engineering import FeatureEngineeringClient` then `fe.create_table(name=..., primary_keys=..., timestamp_keys=..., df=...)`.

47. Subclass `Transformer` and one of `HasInputCols` / `HasOutputCol` (plus `DefaultParamsReadable`/`Writable` for save/load). Override `_transform(self, dataset)`.

48. **Vertical** — 80 GB fits within 128 GB RAM after partitioning. Use **single-node sklearn / XGBoost** on the driver (or Pandas API on Spark for the wrangling, single-node fit). Distributing a single tree-boosting model adds shuffle cost without speedup at this size.

49. `NSGAIISampler` for multi-objective. `study.best_trial` is **undefined** for multi-objective — use `study.best_trials` (Pareto front, list of trials).

50.
```python
grid = (ParamGridBuilder()
    .addGrid(lr.regParam, [0.01, 0.1])
    .addGrid(idx.handleInvalid, ["skip", "keep"])
    .build())
```
Yes — `ParamGridBuilder` tunes any `Param`-typed attribute, including those on transformers, as long as the transformer is a stage in the `Pipeline` passed to `CrossValidator`.

51. `experiment_name` and `metric_name` (the trial's optimization metric to log under that name).

52. **Databricks Asset Bundle (DAB) targets**: `${var.catalog}` parameterized per target (`dev`, `staging`, `prod`). One codebase, three configs.

53. Offline: `fe.create_table(...)` or `fe.write_table(...)`. Online: `w.online_tables.create(name=..., spec=OnlineTableSpec(...))` via Databricks SDK.

54.
```python
fig, ax = plt.subplots(); ConfusionMatrixDisplay.from_predictions(y_true, y_pred, ax=ax)
mlflow.log_figure(fig, "confusion_matrix.png")
```

55. `CrossValidatorModel` (and `TrainValidationSplitModel`) — both expose `.bestModel`.

56.
```python
training_set = fe.create_training_set(
    df=labels_df,
    feature_lookups=[FeatureLookup(
        table_name="prod.ml.cust_features",
        lookup_key="customer_id",
        timestamp_lookup_key="event_ts",
    )],
    label="y",
)
train_df = training_set.load_df()
```

57. They omitted `signature=` (and didn't pass `input_example` either, from which a signature could be inferred). Fix without re-training: load the model object, `infer_signature(X_sample, model.predict(X_sample))`, and `mlflow.<flavor>.log_model(model, "model", signature=sig, registered_model_name="cat.sch.name")`.

58. The `MLflowCallback` was not passed to `study.optimize(..., callbacks=[mlflc])`, OR the callback was instantiated with `nest_trials=False` and the parent run wasn't closed between trials.

59. Driver-only cluster has no executors. `CrossValidator.parallelism` parallelizes via Spark; with no executors the work falls back to driver-side sequential training. Fix: add workers, or switch to a single-node multi-core sklearn solution.

60. `extra_pip_requirements=["company_utils==1.2"]` (or `pip_requirements=[...]`) on `log_model`. Without it, the conda.yaml omits the dependency and the endpoint can't import it.

61. `timestamp_lookup_key` matches against the feature table's `timestamp_keys` value-by-value, but feature_table updates lag the event by minutes. The leakage path is: feature_ts was set to the *processing* timestamp on a backfill, which is **after** the event. Fix: ensure feature_table's timestamp_keys reflect feature *validity time* (when the value first became known), and use a **lookback** in `FeatureLookup` if needed.

62. The PyFunc `predict` signature must accept `(self, context, model_input)` only (or `(..., model_input, params)` in MLflow 3 with `params` declared in the signature). Older `predict(self, context, model_input, params)` without `params` declared in the signature breaks `spark_udf`. Fix: align signature with MLflow 3 conventions, declare `params` schema, or drop the `params` arg.

63. The callback was instantiated as `MLflowCallback(metric_name="loss")` without `tracking_uri` or `experiment_name`. Fix: `MLflowCallback(tracking_uri=mlflow.get_tracking_uri(), metric_name="loss", create_experiment=False)` and set the experiment via `mlflow.set_experiment(name=...)` before `study.optimize`.

64. Spark ML save uses a directory; if it was copied as a single file (or saved via `pickle`), the metadata structure is lost. Re-save with `pipeline.write().overwrite().save(path)` to a directory; reload with `PipelineModel.load(path)`.

65. **Hyperopt autologging logs trial metadata only — it does NOT promote a best model.** Whoever set the `@champion` alias did so manually, possibly on the wrong run. Fix: query `mlflow.search_runs(filter_string="...", order_by=["metrics.loss ASC"]).iloc[0]`, re-fit on full train data, `log_model`, then `set_registered_model_alias("champion", new_version)`.

66. `applyInPandas` (DataFrame → DataFrame per group). `pandas_udf` is Series → Series and doesn't carry group-level batching for one-model-per-group training.

67. The label DataFrame's `lookup_key` rows include values that **don't exist** in the feature table at all (referential integrity issue), OR the join's `timestamp_lookup_key` is finding no feature record valid before each event_ts. Inspect the join coverage by joining manually and counting nulls.

68. Heavy initialization (model file load, embedding load, DB connection) is in `predict` instead of `load_context`. Move it to `load_context` so it runs once at endpoint start.

69. `experiment_ids` is a list of *IDs* (strings), not names. If the user passed an experiment **name** it returns 0 rows. Or `loss` was logged as a *param* (string), not a metric, so the filter type-coerces wrong.

70. (a) `model_uri` uses a relative path or a `runs:/...` URI that's only valid in the original notebook context. (b) The Job's principal lacks UC `EXECUTE` permission on the registered model. Fix: use the canonical `models:/cat.sch.name@alias` URI and grant the Job's service principal `EXECUTE`.

71. `parallelism=20` > cluster cores. Spark schedules 20 model trainings concurrently; each contends for the same 16 cores, all run, all keep state on driver, driver heap fills. Set `parallelism` ≤ worker-cores / model-internal-parallelism.

72. UC requires **three-level** name: `catalog.schema.model`. The URI `models:/ml.churn@champion` is two-level (Workspace Registry legacy). Use `models:/prod.ml.churn@champion`.

73. `MLflowCallback` alone runs trials sequentially in one Python process. `MLflowSparkStudy` distributes trials to executors so 1000 trials run in parallel across the cluster. For tuning at scale, parallelism is the bottleneck — that's exactly what Spark-distributed Optuna addresses.

74. `VotingClassifier` is a static sklearn ensemble — it can't perform an online feature-store lookup at predict time. The right pattern: **custom PyFunc** that, in `predict`, performs the feature lookup (via on-demand feature serving or an online table) and then routes to the wrapped voter. Wraps the ensemble + the I/O side-effect cleanly.

75. SparkML adds shuffle and JVM serialization overhead. For 12 GB on a 128 GB driver, sklearn's optimized C++ pathways and single-process state outperform distributed XGBoost on Spark. Horizontal scaling is justified when data > RAM or model parallelism is genuinely required.

76. Autologging logs **trial telemetry only**. The "best model" is computed from the trials table but not persisted as an MLflow model artifact. If you alias `@champion` based on autologged metadata, the alias points to a run with no model. Always re-fit the winner with full data and `log_model` it explicitly.

77. In claims or fraud, a training row labelled `event_ts = 2024-01-15` must NOT see features computed from data the model wouldn't have had on Jan 15 (e.g., the final claim amount adjudicated on Jan 30). Without point-in-time correctness, the model implicitly cheats in training, validation looks great, production fails. Regulators (HIPAA / SOX / FCRA) explicitly disallow this kind of lookahead in model documentation.

78. `create_training_set` records **feature lineage metadata** in the resulting model: which feature tables, which lookup keys, which timestamp keys. At serving time `fe.score_batch` / endpoint auto-joins features the same way. A hand-written join produces the same DF but no lineage → cannot guarantee training/serving parity.

79. **For**: lets you explore "is `skip` better than `keep` for unseen categories?" without two manual training scripts. **Against**: increases search space without clear ROI; transformer params are usually known a priori. Tune them only when ROI is real (e.g., comparing imputation strategies).

80. Vanilla `log_model` serializes the model only — there's no place to put per-request I/O. A custom PyFunc has `load_context` (open the cache connection once) and `predict` (call the cache per request). Without PyFunc you'd have to do the cache lookup in the calling code, which couples application logic to the model and breaks the "model is a black box" contract.
