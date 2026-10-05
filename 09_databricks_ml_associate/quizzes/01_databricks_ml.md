# Quiz 01 — Databricks Machine Learning (Domain 1, 38%)

> ~55 questions covering DBR ML runtime, AutoML, Feature Engineering in UC, MLflow tracking, UC Model Registry, MLOps strategy.
>
> Take cold (no peeking). Budget ~52 minutes (1m 52s × 28 questions if you split into two sessions, or ~100 minutes for the full quiz).

---

## Recall

1. The current Databricks ML Associate exam version (as of 2026-05) is dated ____.
2. Pass cost is **$____** USD per attempt; retake wait is **____ days**.
3. The Python class that creates a UC feature table is `____`. The legacy workspace equivalent is `____`.
4. The UC Registry uses **aliases**; the workspace registry uses **____**.
5. The one line of Python that switches MLflow to UC: `mlflow.____("databricks-uc")`.
6. Promoting model version 4 to champion in UC: `client.____(name="...", alias="champion", version=4)`.
7. The MLflow API method to find the best run by metric: `client.____(...)`.
8. The order-by direction string to maximize a metric in `search_runs`: `____`.
9. AutoML generates two notebooks: the **Data Exploration** notebook and the **____** notebook.
10. AutoML's "glass box" differentiator means the Best Trial notebook is _______ Python.
11. AutoML forecasting uses what two underlying algorithms (name either)?
12. UC feature tables can be published to a low-latency online store via `fe.____(name, online_store=...)`.
13. The MLflow URI to load a UC-registered model by alias: `models:/catalog.schema.model____champion` (fill in the separator).
14. DBR ML 17.0+ no longer ships **Hyperopt**; the recommended replacement is **____**.
15. To set a key/value tag on a registered model (not a run): `client.____(name, key, value)`.
16. The MLflow function that auto-detects the active ML library and enables the right autolog: `mlflow.____()`.

## Apply

17. You log a model via `mlflow.sklearn.log_model(model, "model", registered_model_name="catalog.schema.churn")`. Where does it land if you forgot to call `mlflow.set_registry_uri("databricks-uc")`?
18. You want to register a model and immediately mark it as `@challenger`. Write the two-step Python:
19. Three notebooks all write to MLflow without calling `set_experiment`. Where do their runs land?
20. The `customer_id` column is in your labels DataFrame but you don't want it in features. Where in the `fe.create_training_set(...)` signature do you declare this?
21. A model was logged with `fe.log_model(... training_set=ts ...)`. To batch-score new customers given only their IDs, which method do you call?
22. The Data Engineering team renames a feature column in the underlying Delta table. Your `fe.score_batch` call now produces nonsense. Why? What's the fix?
23. You're tuning a sklearn model with Hyperopt across the cluster. Which `Trials` subclass parallelizes single-node training across workers?
24. You want to attach `data_version="2026-05-23"` to the **registered model itself** (not any specific run). Which API call?
25. Set `@champion` from v3 to v5 in UC; show the single line.
26. Your team uses `models:/retail.churn/Production` in a notebook. The notebook fails after you migrate to UC. Why?
27. You want every Hyperopt trial to appear as a nested MLflow run with its own params/metrics. Sketch the structure (pseudocode).
28. The model is a sklearn `RandomForestClassifier` trained outside Databricks. You want to log it as version 1 of a UC-registered model. What does the `log_model` call look like?
29. Inside a notebook, you have a fitted sklearn model and want to compare 5 different hyperparameter configurations. Each should be a separate run under a single parent run. Outline.
30. You want to view all runs from a Hyperopt sweep sorted by validation AUC descending in the UI. Where in the UI, and what do you sort by?
31. A team wants to do A/B testing with two model versions in production. UC registry. Name two competing strategies for managing this (one at the model layer, one at the serving layer).

## Diagnose

32. `mlflow.log_param("learning_rate", 0.01)` after running the loop with `mlflow.log_metric("learning_rate", 0.01, step=epoch)`. The MLflow UI shows a flat horizontal line for learning_rate. Diagnose.
33. `client.search_runs(experiment_ids=[42], order_by=["metrics.loss DESC"], max_results=1)` returns a run with `loss=2.4`. Other runs in the experiment have lower loss. What's wrong?
34. Your training code: `mlflow.set_tag("owner", "alice")`. In the UC Models UI, the registered model card doesn't show "owner". Diagnose.
35. `fe.create_table(name="churn_features", primary_keys=["customer_id"], df=df)`. The call fails with a name-validation error. What's the likely cause?
36. AutoML completed in 30 minutes. The reported best AUC is 0.92, but when you load the best model and predict on a separate test set, AUC is 0.71. Diagnose.
37. You call `client.set_registered_model_alias("retail.churn", "champion", 4)` and get an error: "Cannot set alias on workspace registry model." Diagnose.
38. A teammate logs every Hyperopt trial as a top-level run (not nested). The MLflow Experiment has 50 unrelated-looking runs and is hard to navigate. What did they do wrong?
39. Your `FeatureLookup` returns NULL feature values for some customer IDs in scoring. Diagnose two possible causes.
40. The MLflow UI's "Compare runs" parallel-coordinates plot is empty for your HPO sweep, even though you have 30 runs. Diagnose.
41. `fe.score_batch(model_uri="models:/retail.churn@champion", df=lookup_df)` raises "model has no training_set metadata". Diagnose.
42. AutoML's Best Trial notebook hardcodes `pd.read_csv(...)` against a path that no longer exists. Diagnose and propose a fix.
43. Your endpoint code uses `models:/retail.churn/4` (version number). Your team promotes via aliases. After a champion swap, predictions still come from v4. Why?

## Defend

44. Argue why "always promote code, never promote models" is wrong.
45. Defend the UC registry's alias model against a teammate who says "stages were simpler."
46. Argue against using `FeatureStoreClient` for any new code on Databricks in 2026.
47. Defend AutoML as a starting point for an experienced ML engineer who says "I can write this in 10 minutes."
48. A junior engineer suggests storing the same feature data in both UC and the workspace feature store "for redundancy." Argue why this is a bad idea.
49. Defend the choice to use `mlflow.set_tag` (not `set_registered_model_tag`) when logging metadata about a specific training run vs the model lineage.
50. Argue why a single UC `catalog.schema.churn` registered model with multiple versions is better governance than per-environment registered models (`retail_dev.models.churn`, `retail_prod.models.churn`).

## Mixed (52-55)

51. Multi-select: Which are true of UC feature tables? (Select all that apply.)
    - a) Use three-level namespace `catalog.schema.table`
    - b) Support online publishing
    - c) Created via `FeatureStoreClient.register_table()`
    - d) Inherit UC's grant model
    - e) Are workspace-local
52. You run `display(df)` in a notebook and pick "Histogram" from the chart picker. Is this an MLflow log? Where is the chart stored?
53. Your AutoML run's MLflow Experiment has 100 nested runs. Write Python to find the run with the highest `val_f1_score` and load its model.
54. The Spark UI doesn't show MLflow data. What surface does show MLflow data, and how is it accessed?
55. You're asked: "Can we put MLflow runs from notebook A and notebook B into the same experiment for comparison?" Answer yes/no and how.

---

## Answers (don't peek until done)

1. **March 1, 2025.**
2. **$200** USD; **14 days** retake wait.
3. UC: `FeatureEngineeringClient`. Legacy: `FeatureStoreClient`.
4. **Stages** (`None / Staging / Production / Archived`).
5. `mlflow.set_registry_uri("databricks-uc")`.
6. `client.set_registered_model_alias(name="...", alias="champion", version=4)`.
7. `client.search_runs(...)`.
8. `"DESC"` (descending).
9. **Best Trial** notebook.
10. **Editable** (the Best Trial notebook is fully editable Python code).
11. **Prophet** and **ARIMA**.
12. `fe.publish_table(name=..., online_store=...)`.
13. `@` (e.g., `models:/catalog.schema.model@champion`).
14. **Optuna** (or Ray Tune).
15. `client.set_registered_model_tag(name, key, value)`.
16. `mlflow.autolog()` (no flavor).
17. In the **workspace registry**, not UC. The `catalog.schema.churn` name is treated as a literal model name in the workspace registry, not a three-level UC reference. Always call `set_registry_uri` first.
18. ```python
    mv = mlflow.register_model(f"runs:/{run_id}/model", name="catalog.schema.churn")
    client.set_registered_model_alias("catalog.schema.churn", "challenger", version=mv.version)
    ```
19. In **three separate notebook experiments**, one at each notebook's workspace path. Default experiment scope is per-notebook.
20. `exclude_columns=["customer_id"]` argument to `create_training_set`.
21. `fe.score_batch(model_uri=..., df=...)` — it does feature lookups automatically based on the training_set metadata in the logged model.
22. The model logged a specific feature schema. After the rename, the lookup either fails or pulls wrong data. Fix: re-register the feature table with the new schema and re-log the model (or update the feature table to keep the old column name as an alias).
23. `SparkTrials(parallelism=K)`.
24. `client.set_registered_model_tag(name="...", key="data_version", value="2026-05-23")`.
25. `client.set_registered_model_alias("catalog.schema.churn", "champion", version=5)` — reassigns the alias from whatever version had it before.
26. UC doesn't have stages. `models:/.../Production` is the legacy stage URI syntax. Use `models:/catalog.schema.churn@champion` (with `@`) in UC.
27. ```python
    with mlflow.start_run(run_name="hpo-parent"):
        def objective(params):
            with mlflow.start_run(nested=True):
                mlflow.log_params(params)
                score = train_eval(params)
                mlflow.log_metric("auc", score)
                return {'loss': -score, 'status': STATUS_OK}
        best = fmin(fn=objective, space=space, algo=tpe.suggest, max_evals=50)
    ```
28. ```python
    mlflow.set_registry_uri("databricks-uc")
    with mlflow.start_run():
        mlflow.sklearn.log_model(model, "model", registered_model_name="catalog.schema.churn")
    ```
29. ```python
    with mlflow.start_run(run_name="grid"):
        for cfg in configs:
            with mlflow.start_run(nested=True):
                mlflow.log_params(cfg)
                model = RandomForestClassifier(**cfg).fit(X_train, y_train)
                mlflow.log_metric("auc", score)
                mlflow.sklearn.log_model(model, "model")
    ```
30. **In the MLflow Experiment UI**, click the experiment, then sort the Runs table by `metrics.auc` (click the column header to toggle direction to DESC).
31. (a) **Multiple model versions** with aliases (`@champion`, `@challenger`) at the registry layer. (b) **Multiple served entities** with traffic split at the serving endpoint. The latter is the runtime A/B; the former is the registry's view.
32. Same key was used for both `log_param` and `log_metric`. A param is a single string value; a metric is a time series. Mixing names is confusing — pick one. The UI may show only the param's single value or be inconsistent.
33. `loss DESC` returns the highest loss = worst run. To get the **lowest** loss, use `order_by=["metrics.loss ASC"]`.
34. `mlflow.set_tag` writes to the **active run**, not the registered model. Use `client.set_registered_model_tag(name, key, value)` to tag the model itself.
35. UC requires a three-level name: `catalog.schema.churn_features`. Single-level names like `"churn_features"` aren't valid in UC.
36. Likely overfit on the validation split AutoML used. Independent test data shows the true generalization gap. Either AutoML's validation split was unrepresentative, or the chosen model overfit. Inspect the Best Trial notebook and evaluate on your separate test set.
37. The model `retail.churn` exists in the **workspace registry**, not UC. Either you forgot `set_registry_uri("databricks-uc")` before registering, or this is a separate legacy model. Aliases are UC-only.
38. They didn't use `mlflow.start_run(nested=True)` inside the objective function. Each trial became a separate top-level run. Wrap with `nested=True` under a parent run for organization.
39. (1) Feature table doesn't have rows for those customer_ids (lookup miss). (2) Primary key column in the lookup DF doesn't match the feature table's `primary_keys`. (3) Feature table uses `timestamp_keys` and the lookup didn't provide `timestamp_lookup_key`.
40. The 30 runs are not in the same experiment, OR they don't share enough params to plot together, OR the UI requires you to click "Compare" with multiple runs selected. Most often: runs are in different experiments because `set_experiment` was missing.
41. The model was logged via `mlflow.<flavor>.log_model`, not `fe.log_model`. There's no training_set metadata to drive automatic feature lookups. Re-train using `fe.log_model(..., training_set=ts)`.
42. AutoML's Best Trial notebook is meant to be edited. The hardcoded path was the source of the AutoML data. Replace the load with `spark.table("catalog.schema.table")` reading from your Delta source, then run.
43. The URI `models:/retail.churn/4` pins to version 4 specifically — it doesn't follow alias changes. Change the URI to `models:/retail.churn@champion` to track the alias.
44. Some scenarios require promoting the model artifact, not the code: (a) production env has no GPU but training needs one, (b) raw training data is sensitive and not in prod, (c) training is uneconomical to repeat (LLM fine-tunes), (d) byte-exact reproducibility is required and re-running training has non-determinism.
45. Aliases are **flexible labels**, not lifecycle states. You can have `@dev`, `@shadow`, `@champion`, `@challenger`, `@previous_champion` simultaneously, point them at any versions, and swap them by reassignment. Stages were rigid (only 4 named states) and required `transition` operations. Aliases also work across workspaces via UC's account-level model.
46. (1) `FeatureStoreClient` is deprecated since pkg v0.17.0. (2) Workspace-local — no cross-workspace sharing. (3) No UC ACL inheritance. (4) Cannot publish to managed online tables. (5) Will eventually be removed; new code on it accrues migration debt.
47. (a) Speed of getting a baseline — minutes vs hours. (b) Algorithm sweep across XGBoost/LightGBM/RF/LR in one shot for comparison. (c) Auto-generated MLflow Experiment for the hyperparameter trials, which you'd otherwise build manually. (d) Generated editable notebook gives you the data prep pipeline you'd otherwise hand-write. The "10 minutes" claim usually skips proper preprocessing and HPO.
48. UC and workspace store are different governance models. Duplicating data introduces drift, doubles storage cost, complicates lineage, and makes "which is source of truth?" a recurring question. Pick UC; deprecate workspace store.
49. Run tags describe **training execution facts** — Git SHA, training start time, dataset version snapshot used. Model tags describe **the model's identity** — owner, compliance status, intended use. The two serve different audiences (debugger vs governance reviewer).
50. (a) **Lineage across environments** — one model identity, all promotions traceable. (b) **Promotion by alias swap** — same artifact moves up the funnel without rebuild. (c) **No duplicate registered models** to drift apart. (d) UC ACLs control who can promote vs who can read.
51. **a, b, d** are true. (c) is false — that's the legacy `FeatureStoreClient` API. (e) is false — UC tables are account-level, not workspace-local.
52. **No**, the chart from `display()` is a notebook visualization, not an MLflow artifact. To log it, you'd save the underlying data or the rendered image and call `mlflow.log_artifact("/tmp/chart.png")`.
53. ```python
    runs = client.search_runs(
        experiment_ids=[automl_exp_id],
        order_by=["metrics.val_f1_score DESC"],
        max_results=1,
    )
    best_run_id = runs[0].info.run_id
    model = mlflow.sklearn.load_model(f"runs:/{best_run_id}/model")
    ```
54. The **MLflow UI** (sidebar → Experiments). Each experiment opens a run table with sortable columns for params, metrics, source, and links to artifacts.
55. **Yes.** Call `mlflow.set_experiment("/shared/path/to/experiment")` in both notebooks before `start_run`. Both notebooks' runs land in the same experiment.
