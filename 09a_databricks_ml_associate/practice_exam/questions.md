# Databricks Certified Machine Learning Associate — Practice Question Bank

> **Scope:** 200 exam-realistic questions covering the four official domains of the Databricks Certified Machine Learning Associate exam (live version: March 1, 2025).
>
> **Weighting (matches real exam):**
> - **Section 1 — Databricks Machine Learning (38%)** → Q1–Q76 (76 questions)
> - **Section 2 — Data Processing / ML Workflows (19%)** → Q77–Q114 (38 questions)
> - **Section 3 — Model Development (31%)** → Q115–Q176 (62 questions)
> - **Section 4 — Model Deployment (12%)** → Q177–Q200 (24 questions)
>
> **Format:** Each question is single-answer multiple choice (A–D) unless prefixed with "(Select TWO)" or "(Select THREE)". The real exam is 48 questions in 90 minutes (1m 52s per question); pace yourself accordingly.
>
> **Parseable format** — used by the companion Flask quiz app:
> ```
> ## Q{n} — Section {N}: {section name}
> **Objective:** {one-line objective from the exam guide}
>
> {question stem}
>
> - A. {option}
> - B. {option}
> - C. {option}
> - D. {option}
>
> **Answer:** {letter or comma-separated letters for multi-select}
>
> **Explanation:** {why correct + why distractors fail}
> ```

---

# Section 1 — Databricks Machine Learning (38%)

## Q1 — Section 1: Databricks Machine Learning
**Objective:** Create a feature store table in Unity Catalog

A data scientist wants to create a feature table in a workspace with Unity Catalog enabled, with the table governed by UC. Which approach is correct?

- A. Create a Delta table, then call `FeatureStoreClient().register_table()` to register it as a feature table.
- B. Run `CREATE TABLE ... AS FEATURE STORE` in SQL, then write data to it.
- C. Use `FeatureEngineeringClient().create_table(name=..., primary_keys=..., df=...)` to create the table.
- D. Create a Delta table, then run `ALTER TABLE ... SET AS FEATURE STORE` in SQL.

**Answer:** C

**Explanation:** `FeatureEngineeringClient` is the Unity-Catalog-aware client; `create_table` both creates the UC Delta table and registers it as a feature table in one call. `FeatureStoreClient` is the legacy workspace-store client (deprecated after `databricks-feature-store` 0.17.0). There is no `AS FEATURE STORE` SQL clause.

---

## Q2 — Section 1: Databricks Machine Learning
**Objective:** Identify benefits of registering models in the Unity Catalog registry over the workspace registry

Which is a benefit of the Unity Catalog model registry that the legacy workspace model registry does NOT provide?

- A. Ability to log metrics to MLflow runs
- B. Cross-workspace model sharing and centralized governance via three-level namespace
- C. Ability to register a model from a Python notebook
- D. Support for sklearn flavor models

**Answer:** B

**Explanation:** UC registry models live at `catalog.schema.model` and can be shared across workspaces in the same metastore, with ACLs enforced at catalog/schema level. The legacy workspace registry is scoped to a single workspace. The other options are supported by both registries.

---

## Q3 — Section 1: Databricks Machine Learning
**Objective:** Promote a challenger model to a champion model using aliases

A data scientist has a UC-registered model `prod.ml.churn` with version 4 currently aliased as `@challenger` and version 3 aliased as `@champion`. They want to promote v4 to champion. Which call accomplishes this?

- A. `client.transition_model_version_stage(name="prod.ml.churn", version=4, stage="Production")`
- B. `client.set_registered_model_alias(name="prod.ml.churn", alias="champion", version=4)`
- C. `client.update_model_version(name="prod.ml.churn", version=4, alias="champion")`
- D. `client.promote_model_version(name="prod.ml.churn", version=4, to="champion")`

**Answer:** B

**Explanation:** UC registry uses **aliases**, not stages. `set_registered_model_alias` reassigns an alias to a different version (this also implicitly moves the alias off the old version, since an alias points to exactly one version). `transition_model_version_stage` is the legacy workspace-registry API.

---

## Q4 — Section 1: Databricks Machine Learning
**Objective:** Identify the advantages of using ML runtimes

Which is an advantage of using the Databricks Runtime for Machine Learning (DBR ML) over the standard Databricks Runtime?

- A. DBR ML supports SQL queries; standard DBR does not.
- B. DBR ML comes pre-installed with common ML libraries (scikit-learn, XGBoost, MLflow) and GPU drivers, eliminating cluster init time spent installing them.
- C. DBR ML is required for Unity Catalog access.
- D. DBR ML is the only runtime that can read Delta tables.

**Answer:** B

**Explanation:** DBR ML is a layer on top of standard DBR with curated, version-compatible ML libraries pre-installed. SQL, UC, and Delta all work on standard DBR as well.

---

## Q5 — Section 1: Databricks Machine Learning
**Objective:** Identify how AutoML facilitates model/feature selection

Which of the following is true about Databricks AutoML?

- A. AutoML returns only the trained model object; users cannot inspect or modify the training code.
- B. AutoML evaluates multiple algorithms and feature transformations, logs every trial to MLflow, and produces editable Python notebooks for both data exploration and the best trial.
- C. AutoML supports only classification problems, not regression or forecasting.
- D. AutoML only writes its best trial to MLflow; intermediate trials are discarded.

**Answer:** B

**Explanation:** AutoML is "glass box" — it produces an editable Python notebook for the best trial *and* a Data Exploration notebook. Every trial is logged to MLflow. It supports classification, regression, and forecasting.

---

## Q6 — Section 1: Databricks Machine Learning
**Objective:** Identify the best practices of an MLOps strategy

Which is the BEST description of an MLOps strategy that promotes **code** rather than promoting **models** across dev/staging/prod environments?

- A. Train the model once in dev; copy the model artifact into staging and prod and serve it from there.
- B. Maintain a single registry across all environments and assign aliases per environment.
- C. Commit training code to a Git repo; each environment retrains the model on its own data using the same code, producing a separate model artifact per environment.
- D. Use AutoML in each environment independently with different settings.

**Answer:** C

**Explanation:** "Promoting code" means the *code* moves between environments and the *model* is retrained in each. This is best when training is cheap, reproducibility matters, and environments have different data (e.g., dev has masked PII, prod has real data). Option A describes promoting models.

---

## Q7 — Section 1: Databricks Machine Learning
**Objective:** Identify scenarios where promoting code is preferred over promoting models and vice versa

A team trains a 200-billion-parameter model on a 1,000-GPU cluster over 3 weeks. They want to deploy this model to prod. Should they promote code or promote the model?

- A. Promote code — retrain in prod for reproducibility.
- B. Promote the model — training is too expensive to repeat in each environment.
- C. Promote both code and model simultaneously.
- D. Promote neither; train from scratch on every prediction.

**Answer:** B

**Explanation:** When training is prohibitively expensive or non-deterministic, promoting the model artifact (the trained weights / MLflow model) is preferred over re-running training in each environment. Code-promotion is for inexpensive, reproducible training jobs.

---

## Q8 — Section 1: Databricks Machine Learning
**Objective:** Describe the differences between online and offline feature tables

Which statement correctly distinguishes online from offline feature tables in Databricks?

- A. Online tables are Delta tables in UC used for training; offline tables are stored in a key-value store for inference.
- B. Offline tables are the Delta-table source-of-truth in UC; online tables are published copies in a low-latency key-value store (e.g., DynamoDB, Cosmos DB) used by realtime serving endpoints to look up features by primary key.
- C. Online tables can only store categorical features; offline tables can store any feature.
- D. Online and offline tables are identical; the terms are interchangeable.

**Answer:** B

**Explanation:** Offline = Delta in UC for batch training/scoring. Online = published KV-store copy for sub-100ms feature lookups during realtime inference. `publish_table()` synchronizes offline → online.

---

## Q9 — Section 1: Databricks Machine Learning
**Objective:** Train a model with features from a feature store table

Which method on `FeatureEngineeringClient` builds a training DataFrame by joining label data with one or more UC feature tables?

- A. `fe.merge_features(labels_df, feature_tables=[...])`
- B. `fe.create_training_set(df=labels_df, feature_lookups=[...], label=..., exclude_columns=[...])`
- C. `fe.join_features(labels_df, ...)`
- D. `fe.build_training_df(labels_df, feature_table_names=[...])`

**Answer:** B

**Explanation:** `create_training_set()` accepts the labels DataFrame, a list of `FeatureLookup` objects describing which features to join from which tables on which keys, the label column name, and columns to exclude (e.g., the join key). Calling `.load_df()` on the result materializes the training DataFrame.

---

## Q10 — Section 1: Databricks Machine Learning
**Objective:** Identify the best run using the MLflow Client API

You ran 100 trials of an XGBoost model in an experiment with ID `e1`, logging metric `val_auc` per run. Which call returns the single run with the highest `val_auc`?

- A. `client.search_runs(experiment_ids=["e1"], order_by=["metrics.val_auc ASC"], max_results=1)`
- B. `client.search_runs(experiment_ids=["e1"], order_by=["metrics.val_auc DESC"], max_results=1)`
- C. `client.list_runs(experiment_ids=["e1"], sort="val_auc")[-1]`
- D. `mlflow.get_best_run("e1", "val_auc")`

**Answer:** B

**Explanation:** `search_runs` is the canonical API; `order_by=["metrics.val_auc DESC"]` sorts highest-first; `max_results=1` returns just the top run. ASC would give you the worst run.

---

## Q11 — Section 1: Databricks Machine Learning
**Objective:** Manually log metrics, artifacts, and models in an MLflow Run

Inside `with mlflow.start_run():`, which call logs a trained scikit-learn model so it can be loaded later with `mlflow.sklearn.load_model()`?

- A. `mlflow.log_model(model)`
- B. `mlflow.log_artifact(model)`
- C. `mlflow.sklearn.log_model(model, "model")`
- D. `mlflow.log_param("model", model)`

**Answer:** C

**Explanation:** Each ML framework has a flavor-specific `log_model` (e.g., `mlflow.sklearn.log_model`, `mlflow.pyspark.ml.log_model`, `mlflow.xgboost.log_model`). The second arg is the artifact path within the run. `log_artifact` is for arbitrary files (e.g., a plot), not models.

---

## Q12 — Section 1: Databricks Machine Learning
**Objective:** Set or remove a tag for a model

To attach a tag `owner=ml-platform` to a UC-registered model `prod.ml.churn`, which call is correct?

- A. `client.set_tag(run_id, "owner", "ml-platform")`
- B. `client.set_registered_model_tag("prod.ml.churn", "owner", "ml-platform")`
- C. `client.add_model_tag(model="prod.ml.churn", tag={"owner": "ml-platform"})`
- D. `mlflow.set_model_tag("prod.ml.churn", "owner", "ml-platform")`

**Answer:** B

**Explanation:** `set_registered_model_tag(name, key, value)` is the MLflow Client API for tagging a registered model. `set_tag` (without `_registered_model_`) tags an MLflow run, not a model.

---

## Q13 — Section 1: Databricks Machine Learning
**Objective:** Score a model using features from a feature store table

A model has been logged using `fe.log_model(...)` with feature lookups embedded in its metadata. To batch-score new data with feature lookups happening automatically, which call is correct?

- A. `mlflow.pyfunc.load_model(model_uri).predict(new_df)`
- B. `fe.score_batch(model_uri="models:/prod.ml.churn@champion", df=new_df_with_keys)`
- C. `spark.read.format("mlflow").load(model_uri).join(new_df).select("prediction")`
- D. `fe.create_training_set(df=new_df, ...).load_df()`

**Answer:** B

**Explanation:** `score_batch` reads the feature-lookup metadata baked into the model at `log_model` time and automatically joins features from the UC feature tables before invoking the model. You only need to pass a DataFrame containing the lookup keys.

---

## Q14 — Section 1: Databricks Machine Learning
**Objective:** Identify the benefits of creating feature store tables at the account level in Unity Catalog vs at the workspace level

A company has three Databricks workspaces — dev, staging, prod — sharing a single Unity Catalog metastore. Which is a benefit of UC (account-level) feature tables over workspace-level feature tables for this org?

- A. UC feature tables can be accessed from any workspace in the metastore, with consistent permissions and lineage across workspaces.
- B. UC feature tables are stored on the driver node, making lookups faster.
- C. UC feature tables require no primary key.
- D. UC feature tables cost less per query.

**Answer:** A

**Explanation:** The whole point of UC is cross-workspace governance: one feature table, three workspaces, single source of truth. Workspace feature tables would have to be duplicated or shared via brittle external Delta paths.

---

## Q15 — Section 1: Databricks Machine Learning
**Objective:** Write data to a feature store table

Once a feature table `cat.sch.cust_feats` exists, which `FeatureEngineeringClient` method writes a fresh batch of rows to it (overwriting matching primary keys or appending new rows)?

- A. `fe.update_table("cat.sch.cust_feats", df)`
- B. `fe.write_table(name="cat.sch.cust_feats", df=new_features_df, mode="merge")`
- C. `fe.refresh_table("cat.sch.cust_feats", df)`
- D. `spark.sql("INSERT INTO cat.sch.cust_feats SELECT * FROM ...")`

**Answer:** B

**Explanation:** `write_table(name, df, mode="merge")` upserts rows by primary key. `mode="overwrite"` replaces the entire table. Raw SQL inserts bypass the feature-table metadata bookkeeping.

---

## Q16 — Section 1: Databricks Machine Learning
**Objective:** Identify how AutoML facilitates model/feature selection

You ran AutoML on a regression problem. After it completes, AutoML produces two notebooks. What does each notebook contain?

- A. A training notebook and a deployment notebook.
- B. A Data Exploration notebook (summary statistics, distributions, target relationship) and a Best Trial notebook (the editable Python code that produced the highest-scoring trial).
- C. An evaluation notebook and a serving notebook.
- D. A schema notebook and a metrics notebook.

**Answer:** B

**Explanation:** AutoML emits a Data Exploration notebook (for understanding the input data) and a Best Trial notebook (you can read, modify, and re-run the actual training code that won). This "glass box" approach is the explicit AutoML design philosophy on Databricks.

---

## Q17 — Section 1: Databricks Machine Learning
**Objective:** Register a model using the MLflow Client API in the Unity Catalog registry

To register an MLflow model to the UC registry, which Python step is required BEFORE calling `mlflow.sklearn.log_model(..., registered_model_name="cat.sch.model")`?

- A. `mlflow.set_tracking_uri("databricks-uc")`
- B. `mlflow.set_registry_uri("databricks-uc")`
- C. `mlflow.set_experiment("databricks-uc")`
- D. No setup needed; UC is the default registry.

**Answer:** B

**Explanation:** `mlflow.set_registry_uri("databricks-uc")` tells MLflow to use the UC model registry rather than the workspace one. Without this, registration falls back to the workspace registry. `tracking_uri` configures runs/experiments, not the registry.

---

## Q18 — Section 1: Databricks Machine Learning
**Objective:** Identify information available in the MLflow UI

Which of the following is NOT directly visible on a single MLflow run page in the UI?

- A. Logged parameters and metrics
- B. Logged artifacts (files) and the logged model with its signature
- C. The Spark DAG of the cluster that ran the job
- D. The user, source notebook, git commit, and run duration

**Answer:** C

**Explanation:** MLflow UI shows parameters, metrics, artifacts, model, tags, environment info (user, source, git), and run metadata. The Spark DAG belongs to the Spark UI, not MLflow.

---

## Q19 — Section 1: Databricks Machine Learning
**Objective:** Identify the advantages AutoML brings to the model development process

A team needs a quick baseline model before investing in a custom solution. Which is the strongest argument for using AutoML here?

- A. AutoML always produces a better model than a hand-tuned one.
- B. AutoML evaluates many algorithm/HPO combinations, automatically logs all trials, produces editable code, and runs without manual setup — giving a fast, reproducible baseline.
- C. AutoML eliminates the need for any data preparation.
- D. AutoML deploys models to serving endpoints automatically.

**Answer:** B

**Explanation:** AutoML's value is speed and breadth for a baseline. It does not (A) always beat custom models, (C) skip feature engineering of unclean data, or (D) deploy automatically.

---

## Q20 — Section 1: Databricks Machine Learning
**Objective:** Promote a challenger model to a champion model using aliases

After promoting v4 to `@champion` via `set_registered_model_alias`, what happens to v3 which was previously `@champion`?

- A. v3 is automatically deleted.
- B. v3 is automatically re-aliased to `@archived`.
- C. v3 still exists in the registry; it simply no longer has the `@champion` alias (the alias points to v4 now).
- D. v3 is automatically demoted to `@challenger`.

**Answer:** C

**Explanation:** Aliases are pointers: assigning `@champion` to v4 simply moves the pointer. v3 still exists and remains queryable by its version number. No automatic re-aliasing happens.

---

## Q21 — Section 1: Databricks Machine Learning
**Objective:** Identify the best run using the MLflow Client API

To find the top 5 runs by `f1` across two experiments, sorted highest-first, which call works?

- A. `client.search_runs(experiment_ids=["e1","e2"], order_by=["metrics.f1 DESC"], max_results=5)`
- B. `client.search_runs(experiment_ids=["e1","e2"], filter="metrics.f1 >= top 5")`
- C. `client.get_best_runs(experiments=["e1","e2"], metric="f1", k=5)`
- D. `mlflow.search_runs("e1", "e2").nlargest(5, "f1")`

**Answer:** A

**Explanation:** `search_runs` accepts a list of experiment IDs, an `order_by` list, and `max_results`. There is no built-in "top N" filter and no `get_best_runs` method on the client.

---

## Q22 — Section 1: Databricks Machine Learning
**Objective:** Set or remove a tag for a model

To DELETE the `owner` tag from a UC-registered model:

- A. `client.set_registered_model_tag("cat.sch.model", "owner", None)`
- B. `client.delete_registered_model_tag("cat.sch.model", "owner")`
- C. `client.remove_tag("cat.sch.model", "owner")`
- D. `mlflow.delete_tag("cat.sch.model", "owner")`

**Answer:** B

**Explanation:** `delete_registered_model_tag(name, key)` is the symmetric API for removing the tag. Setting a tag's value to `None` does not delete it.

---

## Q23 — Section 1: Databricks Machine Learning
**Objective:** Identify scenarios where promoting code is preferred over promoting models and vice versa

Which scenario is the STRONGEST case for **code promotion** rather than model promotion?

- A. Training the model takes one week on 100 GPUs.
- B. The model is a deterministic logistic regression on tabular data; training takes 10 minutes per environment; staging and prod use different but representative datasets that must each produce their own model.
- C. The model uses random weight initialization with no fixed seed.
- D. The same exact artifact must be deployed across all environments.

**Answer:** B

**Explanation:** Code promotion shines when training is cheap, deterministic (or seeded), and each environment should be trained on its own data. (A) and (D) favor model promotion; (C) makes code promotion unreliable.

---

## Q24 — Section 1: Databricks Machine Learning
**Objective:** Create a feature store table in Unity Catalog

Which arguments are REQUIRED when calling `FeatureEngineeringClient().create_table(...)`?

- A. `name` and `df` only
- B. `name`, `primary_keys`, and either `df` or `schema`
- C. `name` only
- D. `name`, `df`, `primary_keys`, `online_store`, and `tags`

**Answer:** B

**Explanation:** A feature table MUST have a name (UC three-level), at least one primary key (for joins/lookups), and either a DataFrame (which seeds the schema and data) or an explicit schema (for an empty table to be populated later). `online_store` is optional.

---

## Q25 — Section 1: Databricks Machine Learning
**Objective:** Manually log metrics, artifacts, and models in an MLflow Run

A data scientist wants to log a single scalar value `val_loss=0.42` and a list of training losses over 20 epochs. Which is the correct pair of MLflow calls?

- A. Use `mlflow.log_metric("val_loss", 0.42)` once and `mlflow.log_metric("train_loss", loss, step=epoch)` inside a loop.
- B. Use `mlflow.log_param("val_loss", 0.42)` and a single `mlflow.log_metric("train_loss", train_loss_list)`.
- C. Use `mlflow.log_metric("val_loss", 0.42)` and `mlflow.log_artifact("train_loss")`.
- D. Use `mlflow.set_tag("val_loss", 0.42)` and `mlflow.log_metric("train_loss", 0.4)`.

**Answer:** A

**Explanation:** `log_metric` accepts an optional `step` argument so the same metric name can be logged repeatedly across epochs and appears as a time-series in the UI. Parameters (`log_param`) are scalar configs, not metrics; artifacts are files.

---

## Q26 — Section 1: Databricks Machine Learning
**Objective:** Identify the advantages AutoML brings to the model development process

A senior data scientist objects to using AutoML, arguing it's a "black box." Which response BEST addresses the objection?

- A. "You're right; AutoML is black box and uneditable, but it's faster."
- B. "AutoML is glass-box on Databricks — it generates an editable Python notebook for every trial, so you can inspect, modify, and own the code."
- C. "AutoML is fully open source on Databricks; the code is in the platform repo."
- D. "AutoML hides feature engineering but exposes only the final model."

**Answer:** B

**Explanation:** "Glass box" is the explicit Databricks marketing and engineering position on AutoML. Every trial produces an editable notebook, so the team can take ownership.

---

## Q27 — Section 1: Databricks Machine Learning
**Objective:** Identify benefits of registering models in the Unity Catalog registry over the workspace registry

Which of the following is NOT a benefit of the UC model registry over the workspace registry?

- A. Models live in three-level UC namespace with ACLs at catalog/schema level.
- B. Models can be shared cross-workspace within the same metastore.
- C. Lineage from feature tables → model → serving endpoint is tracked.
- D. Models in UC support stages (None/Staging/Production/Archived).

**Answer:** D

**Explanation:** UC registry **removes** stages in favor of **aliases**. (A), (B), and (C) are real benefits.

---

## Q28 — Section 1: Databricks Machine Learning
**Objective:** Identify the advantages of using ML runtimes

A team wants the most cost-effective cluster for distributed training of an XGBoost model. Which configuration is best?

- A. Standard DBR with `pip install xgboost` in a `%pip` cell each cluster start.
- B. DBR ML — comes with XGBoost pre-installed and version-compatible with PySpark/MLlib.
- C. Standard DBR with manual JVM tuning.
- D. DBR ML with a `pip uninstall xgboost` cell at startup.

**Answer:** B

**Explanation:** DBR ML pre-installs XGBoost (along with sklearn, MLflow, etc.) compatible with the rest of the ML stack. (A) works but is slower at startup and risks library-version drift.

---

## Q29 — Section 1: Databricks Machine Learning
**Objective:** Describe the differences between online and offline feature tables

Which of the following BEST justifies adding an online feature table on top of an existing offline UC feature table?

- A. The training set is too large; online tables compress better.
- B. The model is deployed behind a realtime REST endpoint that must look up per-customer features in <100ms during each request.
- C. Offline tables don't support tags.
- D. Online tables remove the need for primary keys.

**Answer:** B

**Explanation:** The online store (DynamoDB / Cosmos DB / Aurora / Online Tables) exists specifically to give realtime serving endpoints sub-100ms feature lookups by primary key. Batch training/scoring uses the offline Delta table directly.

---

## Q30 — Section 1: Databricks Machine Learning
**Objective:** Identify the best practices of an MLOps strategy

Which of the following is a CORE MLOps best practice on Databricks?

- A. Train all production models in dev notebooks and copy them by hand to prod.
- B. Version every artifact (code in Git, data in Delta time travel, models in MLflow registry) and automate promotion with CI/CD.
- C. Avoid Unity Catalog because it adds latency.
- D. Re-train the prod model every minute regardless of trigger.

**Answer:** B

**Explanation:** Versioning + automation is the MLOps backbone. Manual copies (A), avoiding governance (C), and uncoordinated retraining (D) are anti-patterns.

---

## Q31 — Section 1: Databricks Machine Learning
**Objective:** Promote a challenger model to a champion model using aliases

(Select TWO) Which two statements about UC registry aliases are correct?

- A. Each version can have at most one alias.
- B. Each alias points to exactly one version at a time.
- C. Aliases are arbitrary labels (e.g., `@champion`, `@canary_eu`).
- D. Aliases are restricted to the set {`@staging`, `@production`, `@archived`}.

**Answer:** B, C

**Explanation:** Aliases are pointers (one alias → one version) but a version can carry multiple aliases (so A is wrong). Aliases are free-form (B and C correct). (D) describes legacy stages.

---

## Q32 — Section 1: Databricks Machine Learning
**Objective:** Identify the best run using the MLflow Client API

A data scientist wants the run with the lowest `rmse` from experiment `e1`, but only among runs where `params.model_type = "xgboost"`. Which call works?

- A. `client.search_runs(experiment_ids=["e1"], filter_string="params.model_type = 'xgboost'", order_by=["metrics.rmse ASC"], max_results=1)`
- B. `client.search_runs(experiment_ids=["e1"], filter="rmse_min", order_by="model_type=xgboost")`
- C. `mlflow.search_runs(filter="xgboost").min("rmse")`
- D. `client.get_runs("e1").filter(model_type="xgboost").nsmallest(1, "rmse")`

**Answer:** A

**Explanation:** `search_runs` accepts a `filter_string` using MLflow's SQL-like syntax (`params.X = 'Y'`, `metrics.X > N`, `tags.X = 'Y'`). Order by `rmse ASC` for lowest first.

---

## Q33 — Section 1: Databricks Machine Learning
**Objective:** Identify the benefits of creating feature store tables at the account level in Unity Catalog vs at the workspace level

Which of the following is a benefit ONLY available with UC feature tables (not workspace feature tables)?

- A. Feature tables can be queried via Spark.
- B. Feature tables can be shared across workspaces under the same UC metastore with unified ACLs.
- C. Feature tables support primary keys.
- D. Feature tables can be backed by Delta.

**Answer:** B

**Explanation:** Workspace feature tables are scoped to a single workspace and have workspace-local ACLs. UC tables are metastore-level. (A), (C), (D) are common to both.

---

## Q34 — Section 1: Databricks Machine Learning
**Objective:** Train a model with features from a feature store table

`FeatureLookup` accepts a `lookup_key` parameter. What does it represent?

- A. The MLflow run ID used to log the feature table.
- B. The column(s) in the labels DataFrame that join to the feature table's primary key.
- C. The UC catalog and schema of the feature table.
- D. The cluster ID used to materialize features.

**Answer:** B

**Explanation:** `lookup_key` is how `create_training_set` knows which columns in the labels DataFrame to join on. If your labels DF has `customer_id` and the feature table's primary key is also `customer_id`, `lookup_key="customer_id"`.

---

## Q35 — Section 1: Databricks Machine Learning
**Objective:** Manually log metrics, artifacts, and models in an MLflow Run

You want to log a matplotlib figure (saved as `confusion_matrix.png`) to an MLflow run. Which call works?

- A. `mlflow.log_metric("confusion_matrix.png", fig)`
- B. `mlflow.log_artifact("confusion_matrix.png")`
- C. `mlflow.log_model(fig, "confusion_matrix.png")`
- D. `mlflow.set_tag("confusion_matrix.png", fig)`

**Answer:** B

**Explanation:** `log_artifact(local_path)` uploads any file to the run's artifact store. Metrics are numeric scalars; models are framework-flavored. (You could also use `mlflow.log_figure(fig, "confusion_matrix.png")` to skip the manual save step.)

---

## Q36 — Section 1: Databricks Machine Learning
**Objective:** Identify the advantages of using ML runtimes

Which library is typically NOT pre-installed on DBR ML?

- A. scikit-learn
- B. MLflow
- C. XGBoost
- D. TensorFlow Decision Forests version that exactly matches your custom build

**Answer:** D

**Explanation:** DBR ML pre-installs sklearn, MLflow, XGBoost, PyTorch, and TensorFlow at curated versions. Custom builds of specialty libraries are not pre-installed; you'd `%pip install` them.

---

## Q37 — Section 1: Databricks Machine Learning
**Objective:** Identify how AutoML facilitates model/feature selection

Which is true about how AutoML handles features?

- A. AutoML requires the user to manually one-hot encode all categorical features before running.
- B. AutoML automatically detects column types, applies appropriate encodings (numeric scaling, categorical encoding), evaluates many algorithms, and reports the best-trial code that includes those transformations.
- C. AutoML drops all categorical columns by default.
- D. AutoML only accepts pre-vectorized inputs.

**Answer:** B

**Explanation:** AutoML's value is in automating encoding + algorithm selection together. The Best Trial notebook shows exactly which transformations were applied.

---

## Q38 — Section 1: Databricks Machine Learning
**Objective:** Score a model using features from a feature store table

A model was logged with `fe.log_model(...)` referencing feature tables for `recency`, `frequency`, `monetary` features keyed by `customer_id`. To batch-score `new_customers_df` (which contains only `customer_id`), what must `new_customers_df` include for `fe.score_batch` to work?

- A. The full set of RFM features, pre-computed.
- B. Only the primary key column(s) — `customer_id` — that match the feature table's keys; `score_batch` looks up the features.
- C. The MLflow run ID of the original training run.
- D. A column named `prediction`.

**Answer:** B

**Explanation:** `score_batch` reads the model's feature-lookup metadata and automatically joins features from the registered feature tables using the keys provided. You only supply the keys (and any "online" features computed at request time).

---

## Q39 — Section 1: Databricks Machine Learning
**Objective:** Identify benefits of registering models in the Unity Catalog registry over the workspace registry

Which API call would FAIL when targeting a UC-registered model?

- A. `client.set_registered_model_alias("cat.sch.model", "champion", 5)`
- B. `client.transition_model_version_stage(name="cat.sch.model", version=5, stage="Production")`
- C. `client.search_registered_models(filter_string="name = 'cat.sch.model'")`
- D. `client.set_registered_model_tag("cat.sch.model", "owner", "ml")`

**Answer:** B

**Explanation:** Stages are a legacy workspace-registry concept. The UC registry rejects `transition_model_version_stage` calls — you use aliases instead.

---

## Q40 — Section 1: Databricks Machine Learning
**Objective:** Identify scenarios where promoting code is preferred over promoting models and vice versa

A team uses a generative model where training is non-deterministic (no fixed seed support in the framework) and takes 48 hours. Which strategy is BEST?

- A. Promote code; retrain in each environment.
- B. Promote the model; train once, deploy the same artifact to staging and prod.
- C. Train in prod only; skip staging.
- D. Promote both code and a fresh model per environment.

**Answer:** B

**Explanation:** Non-determinism + expensive training = model promotion. You train once and ship the same artifact so staging and prod behavior are identical.

---

## Q41 — Section 1: Databricks Machine Learning
**Objective:** Identify the best practices of an MLOps strategy

Which is the BEST high-level analogy for MLOps?

- A. MLOps is the same as DevOps; rename "code" to "model" and you're done.
- B. MLOps extends DevOps with explicit handling of three artifacts — code, data, and models — including versioning, lineage, and drift monitoring for each.
- C. MLOps is purely about Kubernetes for ML.
- D. MLOps is exclusively the data scientist's responsibility.

**Answer:** B

**Explanation:** MLOps is DevOps-plus-data-plus-models. Each of the three needs versioning, testing, and monitoring; they interact (e.g., data drift requires a model retrain).

---

## Q42 — Section 1: Databricks Machine Learning
**Objective:** Create a feature store table in Unity Catalog

A team needs a feature table that will be populated later by a streaming pipeline (no data at create time). Which `create_table` invocation works?

- A. `fe.create_table(name="cat.sch.feats", primary_keys=["id"], df=spark.createDataFrame([], schema))`
- B. `fe.create_table(name="cat.sch.feats", primary_keys=["id"], schema=schema)`
- C. Both A and B work.
- D. Neither — you must have data to create a feature table.

**Answer:** C

**Explanation:** `create_table` accepts either a `df` (whose schema seeds the table) or an explicit `schema` (for an empty table). Both are valid; passing an empty DF with an explicit schema is functionally equivalent to passing `schema=`.

---

## Q43 — Section 1: Databricks Machine Learning
**Objective:** Identify the best run using the MLflow Client API

What does `client.search_runs()` return by default if you don't pass `order_by`?

- A. An empty list.
- B. Runs in creation order (no specific guarantee on tie-breaking).
- C. Runs sorted by `metrics.accuracy` descending.
- D. Only the most recent run.

**Answer:** B

**Explanation:** Without `order_by`, runs come back roughly in creation order. To get a deterministic "best", always pass an explicit `order_by=["metrics.X DESC"]`.

---

## Q44 — Section 1: Databricks Machine Learning
**Objective:** Describe the differences between online and offline feature tables

Which trigger publishes an offline feature table to its online store?

- A. `fe.publish_table(name="cat.sch.feats", online_store=OnlineStoreSpec(...))`
- B. `fe.sync_online(name="cat.sch.feats")`
- C. `fe.create_table(..., online=True)`
- D. `spark.sql("REFRESH TABLE cat.sch.feats")`

**Answer:** A

**Explanation:** `publish_table()` is the explicit API to push the offline Delta table contents (or just-changed rows in streaming mode) to a registered online store like DynamoDB / Cosmos DB / Aurora.

---

## Q45 — Section 1: Databricks Machine Learning
**Objective:** Set or remove a tag for a model

A team uses tags to mark which models have been approved by Risk. Which API call adds a tag `risk_approved=true` to model `prod.ml.churn`?

- A. `client.set_tag("prod.ml.churn", "risk_approved", "true")`
- B. `client.set_registered_model_tag("prod.ml.churn", "risk_approved", "true")`
- C. `mlflow.set_model_tag("prod.ml.churn", "risk_approved", True)`
- D. `client.add_tag(model="prod.ml.churn", risk_approved=True)`

**Answer:** B

**Explanation:** Tags on a *registered model* use `set_registered_model_tag(name, key, value)`. `set_tag` is for runs, not models. Tag values must be strings (so `"true"` not `True`).

---

## Q46 — Section 1: Databricks Machine Learning
**Objective:** Identify the advantages AutoML brings to the model development process

A data scientist wants AutoML to evaluate XGBoost, LightGBM, and Random Forest but NOT logistic regression on a classification problem. Which AutoML configuration mechanism supports this?

- A. AutoML always tries every algorithm; you cannot exclude any.
- B. The AutoML UI (and API) exposes an `exclude_frameworks` option (and analogously `include_frameworks`) to restrict the algorithm pool.
- C. AutoML only ever tries one algorithm chosen heuristically from the data.
- D. AutoML algorithm selection is opaque; cannot be customized.

**Answer:** B

**Explanation:** AutoML exposes both inclusion and exclusion lists of frameworks (e.g., `xgboost`, `lightgbm`, `sklearn_logistic_regression`). It's not fully opaque.

---

## Q47 — Section 1: Databricks Machine Learning
**Objective:** Write data to a feature store table

When calling `fe.write_table(name=..., df=..., mode=...)`, which `mode` values are supported?

- A. `"merge"` (upsert by PK), `"overwrite"` (replace table contents)
- B. `"append"` only
- C. `"insert"` and `"delete"`
- D. `"create"` and `"alter"`

**Answer:** A

**Explanation:** `write_table` supports `"merge"` (upsert by primary key) and `"overwrite"` (full replacement). For a streaming source it also supports streaming writes via `df.writeStream`.

---

## Q48 — Section 1: Databricks Machine Learning
**Objective:** Manually log metrics, artifacts, and models in an MLflow Run

A junior engineer writes:
```python
mlflow.log_metric("max_depth", 5)
mlflow.log_param("rmse", 0.42)
```
What is wrong?

- A. Nothing; these are equivalent.
- B. The names are swapped — `max_depth` is a hyperparameter (use `log_param`) and `rmse` is a metric (use `log_metric`). The UI will be confusing and `rmse` won't appear as a time-series.
- C. `log_metric` requires a string for the value.
- D. `log_param` is deprecated; use `set_tag`.

**Answer:** B

**Explanation:** Conceptually: params = inputs to training (fixed during a run); metrics = outputs / scalars you might log many times (per-epoch). Swapping them breaks search and the UI.

---

## Q49 — Section 1: Databricks Machine Learning
**Objective:** Identify the best practices of an MLOps strategy

Which is the LEAST aligned with MLOps best practice on Databricks?

- A. Storing training data as Delta tables in UC for time travel and lineage.
- B. Logging every training run with MLflow autologging or manual `log_metric` / `log_param`.
- C. Manually editing the production serving endpoint config by hand every release without recording the change anywhere.
- D. Using a Git-backed Databricks repo for all training code.

**Answer:** C

**Explanation:** Manual untracked changes to prod are the canonical MLOps anti-pattern. Changes should go through version control and an automated promotion process.

---

## Q50 — Section 1: Databricks Machine Learning
**Objective:** Promote a challenger model to a champion model using aliases

A model serving endpoint references `models:/cat.sch.churn@champion`. The team updates the `@champion` alias to point to a new version. What is the impact on the endpoint?

- A. The endpoint is permanently broken until manually reconfigured.
- B. On the next endpoint update (or auto-refresh), the endpoint loads the new version pointed to by `@champion`. Until then, the previously-loaded version continues to serve.
- C. The endpoint never picks up alias changes; you must redeploy with a hardcoded version.
- D. The endpoint immediately and atomically swaps to the new version within milliseconds.

**Answer:** B

**Explanation:** Aliases give the endpoint an indirection point — when you ask the endpoint to update, it resolves the alias to the current version. It's not instantaneous (endpoints take seconds to minutes to roll a new served entity), but it's also not "permanently broken" or "hardcoded".

---

## Q51 — Section 1: Databricks Machine Learning
**Objective:** Identify the advantages AutoML brings to the model development process

(Select TWO) Which two statements about AutoML on Databricks are correct?

- A. AutoML logs every trial to a single MLflow Experiment for the AutoML run.
- B. AutoML produces a Best Trial notebook with editable Python code.
- C. AutoML automatically deploys the best model to a serving endpoint.
- D. AutoML's trials are hidden and cannot be reviewed.

**Answer:** A, B

**Explanation:** A and B describe AutoML's actual behavior. C is false: deployment is a separate step. D is false: it's explicitly glass-box.

---

## Q52 — Section 1: Databricks Machine Learning
**Objective:** Identify benefits of registering models in the Unity Catalog registry over the workspace registry

A team's compliance officer asks: "Where do I see exactly which feature tables a deployed model uses?" Which Databricks capability answers this DIRECTLY?

- A. The MLflow UI run page.
- B. The Spark UI DAG view.
- C. Unity Catalog lineage — visible on the model and feature-table pages when the model was logged via `fe.log_model` and registered in UC.
- D. The cluster event log.

**Answer:** C

**Explanation:** UC lineage tracks the relationship: feature tables → training set → model → serving endpoint. The compliance officer can navigate from the model to its source feature tables in the UC UI.

---

## Q53 — Section 1: Databricks Machine Learning
**Objective:** Train a model with features from a feature store table

Inside `create_training_set(...)`, why is `exclude_columns=["customer_id"]` commonly passed?

- A. To save memory by dropping the join key after the join.
- B. Because the model should not be trained on the customer_id itself (it's an identifier, not a predictive feature) — otherwise the model can memorize IDs and overfit.
- C. To force online lookup of the column.
- D. To convert customer_id from string to int.

**Answer:** B

**Explanation:** Identifier columns are leakage risks and uninformative as features. `exclude_columns` removes them from the resulting DataFrame's feature set after the join is performed.

---

## Q54 — Section 1: Databricks Machine Learning
**Objective:** Identify the best run using the MLflow Client API

You logged a custom metric `weighted_f1`. Which filter string would `search_runs` accept to find runs where `weighted_f1 > 0.85`?

- A. `"metrics.weighted_f1 > 0.85"`
- B. `"weighted_f1 > 0.85"`
- C. `"runs.weighted_f1 > 0.85"`
- D. `"metric: weighted_f1, value: 0.85"`

**Answer:** A

**Explanation:** MLflow filter syntax requires the namespace prefix `metrics.`, `params.`, `tags.`, or `attributes.` followed by the key and a comparison.

---

## Q55 — Section 1: Databricks Machine Learning
**Objective:** Describe the differences between online and offline feature tables

A realtime fraud-detection endpoint must look up a user's `recent_avg_transaction_amount` in under 20ms. Which feature-table strategy fits?

- A. Read directly from the offline Delta table at request time.
- B. Publish the offline feature table to a registered online store and configure the serving endpoint to look up features automatically.
- C. Pre-compute features into a pandas DataFrame inside the model.
- D. Skip the feature store entirely and re-aggregate from raw transactions on every request.

**Answer:** B

**Explanation:** Delta reads at request time miss the latency target by orders of magnitude. The online store is purpose-built for this exact case.

---

## Q56 — Section 1: Databricks Machine Learning
**Objective:** Identify how AutoML facilitates model/feature selection

AutoML detected a date column and a free-text column in your dataset. What does it typically do?

- A. Throws an error and stops.
- B. Drops both columns silently.
- C. Extracts date features (year, month, dayofweek, etc.) from the date column and applies text feature extraction (e.g., TF-IDF/embeddings) on the text column.
- D. One-hot-encodes the date and ignores the text.

**Answer:** C

**Explanation:** AutoML applies type-appropriate feature engineering automatically — that's a core part of its value.

---

## Q57 — Section 1: Databricks Machine Learning
**Objective:** Identify the advantages of using ML runtimes

Why might a team standardize on a specific DBR ML LTS version (e.g., 15.4 LTS ML) across all training jobs?

- A. LTS versions are cheaper.
- B. LTS versions get long-term security and bug patches, and pinning ensures reproducibility of trained models across re-runs.
- C. Only LTS versions support MLflow.
- D. LTS versions are the only versions that allow GPU clusters.

**Answer:** B

**Explanation:** LTS = Long Term Support. Pinning the DBR ML version (and so pinning the entire set of pre-installed library versions) is a reproducibility win.

---

## Q58 — Section 1: Databricks Machine Learning
**Objective:** Manually log metrics, artifacts, and models in an MLflow Run

What happens if you call `mlflow.log_metric("loss", v)` outside of a `with mlflow.start_run():` block (and no run is active)?

- A. It logs to a default "global" run.
- B. It raises an exception or implicitly starts a new run that immediately ends — behavior depends on context (notebook vs script) and can be surprising; best practice is always to wrap in an explicit `start_run`.
- C. It logs to MLflow autolog only.
- D. It silently no-ops.

**Answer:** B

**Explanation:** Best practice is to always use `with mlflow.start_run():`. Implicit behavior is brittle and changes between MLflow versions.

---

## Q59 — Section 1: Databricks Machine Learning
**Objective:** Identify the best practices of an MLOps strategy

A team wants to "trust but verify" each model before promoting to `@champion`. Which workflow BEST implements this?

- A. Skip staging entirely; promote dev → prod.
- B. Register the new version, assign `@challenger`, run shadow inference against a labelled holdout, and only assign `@champion` once metrics meet thresholds.
- C. Always overwrite `@champion` immediately to avoid stale models.
- D. Train daily and deploy whichever model trains last.

**Answer:** B

**Explanation:** Shadow / canary evaluation via challenger alias is the standard MLOps gate. (A), (C), and (D) skip the gate.

---

## Q60 — Section 1: Databricks Machine Learning
**Objective:** Create a feature store table in Unity Catalog

What happens if you call `create_table` with a `name` that already exists in UC?

- A. It silently overwrites the existing table.
- B. It raises an error; you must explicitly drop or alter the existing table, or call `write_table` instead.
- C. It appends new columns to the existing table.
- D. It returns the existing table unchanged.

**Answer:** B

**Explanation:** `create_table` is for first-time creation. If the table exists, use `write_table` to add data or drop & recreate explicitly. This prevents accidental schema changes.

---

## Q61 — Section 1: Databricks Machine Learning
**Objective:** Promote a challenger model to a champion model using aliases

The team's CI/CD pipeline promotes a new model version to `@champion` only after the integration test passes. The integration test compares the new model's metrics on a held-out batch to the current `@champion`'s metrics. What happens to the previous `@champion` after promotion?

- A. It is automatically tagged with `@archived`.
- B. It loses the `@champion` alias (since the alias now points to a different version) but remains in the registry — you may want to manually re-alias it to `@previous_champion` for rollback.
- C. It is deleted.
- D. It is automatically demoted to `@challenger`.

**Answer:** B

**Explanation:** Aliases are reassignable pointers. Best practice is to re-alias the previous champion as `@previous_champion` or `@archived` so you can roll back via alias swap rather than searching for the old version.

---

## Q62 — Section 1: Databricks Machine Learning
**Objective:** Identify the advantages AutoML brings to the model development process

Which is NOT a benefit AutoML provides?

- A. Fast baselining across many algorithms.
- B. Automatic logging of every trial to MLflow.
- C. Editable Best Trial notebook the team can iterate on.
- D. Guarantee that the best-trial model meets the team's business KPIs out of the box.

**Answer:** D

**Explanation:** AutoML maximizes a chosen ML metric (e.g., F1, RMSE). It does not guarantee business KPIs are met — that's the team's responsibility.

---

## Q63 — Section 1: Databricks Machine Learning
**Objective:** Set or remove a tag for a model

Tags vs Aliases — which statement is correct?

- A. Tags are key-value labels (e.g., `owner=ml`); aliases are pointers to specific model versions (e.g., `@champion → v5`).
- B. Tags and aliases are interchangeable.
- C. Tags point to versions; aliases are key-value labels.
- D. Both tags and aliases are only available in the workspace registry.

**Answer:** A

**Explanation:** They serve different purposes. Tags annotate; aliases point. Both are first-class concepts in the UC registry.

---

## Q64 — Section 1: Databricks Machine Learning
**Objective:** Score a model using features from a feature store table

A serving endpoint serves a model registered via `fe.log_model(...)`. The endpoint receives a request body `{"customer_id": 42}`. How does Databricks know to look up the RFM features for customer 42?

- A. The feature lookups are embedded in the model's MLflow metadata; the serving runtime reads the online feature store for that customer at request time.
- B. The client must look up features and pass them in the request body.
- C. The endpoint joins offline Delta tables at request time.
- D. The endpoint always returns the latest training feature values.

**Answer:** A

**Explanation:** The "automatic feature lookup" is the whole point of `fe.log_model`. The model carries its feature dependencies; the endpoint resolves them via the configured online store.

---

## Q65 — Section 1: Databricks Machine Learning
**Objective:** Identify scenarios where promoting code is preferred over promoting models and vice versa

Which is a downside of model promotion compared to code promotion?

- A. Model promotion always produces worse models.
- B. Model promotion can hide environment-data drift, because the same artifact is used everywhere — it does not validate that the model retrains correctly with each environment's pipeline.
- C. Model promotion is not supported on Databricks.
- D. Model promotion requires Git.

**Answer:** B

**Explanation:** With model promotion you may not catch issues where the training code can't actually be re-run in staging or prod due to environment drift; code promotion forces re-execution and surfaces such issues.

---

## Q66 — Section 1: Databricks Machine Learning
**Objective:** Identify the best run using the MLflow Client API

Which is the simplest way to get the URI of the model artifact logged in the best run?

- A. `runs[0].info.artifact_uri + "/model"`
- B. `runs[0].info.model_uri`
- C. `mlflow.get_artifact_uri()` from inside the run
- D. There is no way; you must construct the URI manually from registry name + version.

**Answer:** A

**Explanation:** `run.info.artifact_uri` gives the run's artifact root; you append the `artifact_path` you used when logging (default `"model"`) to get the model URI. There is no `info.model_uri` attribute on a run.

---

## Q67 — Section 1: Databricks Machine Learning
**Objective:** Identify the advantages of using ML runtimes

When would you NOT want DBR ML?

- A. When running interactive notebooks with mostly SQL ETL and no ML training; standard DBR is leaner and starts faster.
- B. When training scikit-learn models.
- C. When using MLflow tracking.
- D. When deploying to a Model Serving endpoint.

**Answer:** A

**Explanation:** DBR ML carries extra library weight you don't need for pure ETL. For ML, use DBR ML. (Model Serving is a managed endpoint and not directly a "DBR ML or not" choice.)

---

## Q68 — Section 1: Databricks Machine Learning
**Objective:** Manually log metrics, artifacts, and models in an MLflow Run

Which call enables MLflow autologging for scikit-learn (so params, metrics, and the model are logged without explicit calls)?

- A. `mlflow.sklearn.autolog()`
- B. `mlflow.autolog(sklearn=True)`
- C. `mlflow.enable_autolog("sklearn")`
- D. `mlflow.sklearn.enable_autolog()`

**Answer:** A

**Explanation:** Each MLflow flavor exposes `autolog()` via its module: `mlflow.sklearn.autolog()`, `mlflow.xgboost.autolog()`, `mlflow.pyspark.ml.autolog()`. There is also a flavorless `mlflow.autolog()` that auto-detects.

---

## Q69 — Section 1: Databricks Machine Learning
**Objective:** Describe the differences between online and offline feature tables

For batch training, which feature table form does the training pipeline read?

- A. Online store (DynamoDB / Cosmos DB / Aurora).
- B. Offline Delta table in UC.
- C. The MLflow model artifact.
- D. Neither — features must be pandas DataFrames.

**Answer:** B

**Explanation:** Training reads the offline Delta table (cheap, high-throughput scan). The online store is for low-latency per-key lookups at inference time.

---

## Q70 — Section 1: Databricks Machine Learning
**Objective:** Identify benefits of registering models in the Unity Catalog registry over the workspace registry

A model in UC registry can be promoted across environments by:

- A. Recreating the same registered model name in each workspace's local registry.
- B. Using aliases (e.g., `@champion`) that any workspace in the metastore can resolve; or by sharing via Delta Sharing for cross-metastore sharing.
- C. Manually copying the model artifact between workspaces.
- D. Email attachment.

**Answer:** B

**Explanation:** Single source of truth + aliases = cross-workspace promotion. Cross-metastore is via Delta Sharing.

---

## Q71 — Section 1: Databricks Machine Learning
**Objective:** Identify the best practices of an MLOps strategy

Which of the following is NOT typically part of a Databricks MLOps reference architecture?

- A. Git-backed code repositories and CI/CD pipelines.
- B. MLflow tracking + UC model registry.
- C. Unity Catalog feature tables.
- D. Manually typing serving endpoint URLs into the model code at training time.

**Answer:** D

**Explanation:** Hard-coded endpoint URLs in training code violate environment separation. Use registry aliases + endpoint configuration instead.

---

## Q72 — Section 1: Databricks Machine Learning
**Objective:** Identify the advantages AutoML brings to the model development process

Which scenarios are AutoML's sweet spot? (Select TWO)

- A. Quick baseline on a tabular classification problem with 50K rows and 30 features.
- B. Training a 100-billion-parameter LLM.
- C. Forecasting daily sales for 500 SKUs over 3 years.
- D. Real-time bid optimization with sub-millisecond latency.

**Answer:** A, C

**Explanation:** AutoML supports tabular classification/regression and forecasting. LLM training is out of scope. Real-time bid serving is a deployment concern, not a training one.

---

## Q73 — Section 1: Databricks Machine Learning
**Objective:** Train a model with features from a feature store table

What happens at `fe.log_model(...)` that does NOT happen at a plain `mlflow.<flavor>.log_model(...)`?

- A. Nothing; they are equivalent.
- B. The feature lookups (table names, keys, and feature names) are persisted as part of the model artifact, enabling automatic feature joins at score time.
- C. The model is automatically promoted to `@champion`.
- D. The training DataFrame is logged as an artifact.

**Answer:** B

**Explanation:** `fe.log_model` packages the feature-engineering metadata so the model knows its dependencies. Without it, you'd have to re-derive features in your scoring code.

---

## Q74 — Section 1: Databricks Machine Learning
**Objective:** Identify how AutoML facilitates model/feature selection

Which of the following is NOT a problem type supported by Databricks AutoML?

- A. Binary classification
- B. Multi-class classification
- C. Regression
- D. Reinforcement learning

**Answer:** D

**Explanation:** AutoML supports classification (binary, multi-class), regression, and forecasting. RL is not in scope.

---

## Q75 — Section 1: Databricks Machine Learning
**Objective:** Promote a challenger model to a champion model using aliases

You can query a UC-registered model by alias using which MLflow model URI?

- A. `models:/cat.sch.model/champion`
- B. `models:/cat.sch.model@champion`
- C. `models://cat.sch.model:champion`
- D. `mlflow-models://cat.sch.model.champion`

**Answer:** B

**Explanation:** The UC model URI uses `@aliasname`. `/<integer>` is also valid for a specific version. The legacy `/Production` stage syntax does NOT apply to UC.

---

## Q76 — Section 1: Databricks Machine Learning
**Objective:** Identify benefits of registering models in the Unity Catalog registry over the workspace registry

Which UC concept is NEW (not present in the workspace registry)?

- A. Model versioning.
- B. Three-level namespace (catalog.schema.model) + cross-workspace governance.
- C. The ability to log a model from an MLflow run.
- D. The concept of a "registered model".

**Answer:** B

**Explanation:** The legacy workspace registry has versions, registered models, and run-to-registration. The catalog/schema namespace and the metastore-level scope are UC additions.

---

# Section 2 — Data Processing / ML Workflows (19%)

## Q77 — Section 2: Data Processing
**Objective:** Compute summary statistics on a Spark DataFrame using `.summary()` or dbutils data summaries

Which method on a Spark DataFrame returns count, mean, stddev, min, 25/50/75% percentiles, and max for every column (including strings)?

- A. `df.describe()`
- B. `df.summary()`
- C. `df.stats()`
- D. `df.profile()`

**Answer:** B

**Explanation:** `summary()` returns percentiles in addition to the basics, and computes string-column stats too. `describe()` is numeric-only and omits percentiles.

---

## Q78 — Section 2: Data Processing
**Objective:** Compute summary statistics on a Spark DataFrame using `.summary()` or dbutils data summaries

To get a rich, visual profile of a Spark DataFrame in a Databricks notebook (histograms, missing values, correlations), which call is BEST?

- A. `df.summary()`
- B. `df.describe()`
- C. `dbutils.data.summarize(df)`
- D. `df.show()`

**Answer:** C

**Explanation:** `dbutils.data.summarize(df)` opens an interactive visual profile in the notebook output. The other methods print plain numeric tables.

---

## Q79 — Section 2: Data Processing
**Objective:** Remove outliers from a Spark DataFrame based on standard deviation or IQR

A team uses the standard-deviation rule: drop rows where `|x - mean(x)| > 3 * stddev(x)`. Which approach correctly removes outliers from the `amount` column?

- A. ```python
   stats = df.select(F.mean("amount").alias("m"), F.stddev("amount").alias("s")).first()
   df_clean = df.filter(F.abs(F.col("amount") - stats.m) <= 3 * stats.s)
   ```
- B. ```python
   df_clean = df.filter("amount < mean(amount) + 3 * stddev(amount)")
   ```
- C. ```python
   df_clean = df.dropna(subset=["amount"], thresh=3)
   ```
- D. ```python
   df_clean = df.sample(0.99)
   ```

**Answer:** A

**Explanation:** Compute the scalar mean and stddev first, then use them in a `filter`. (B) doesn't work because Spark SQL filter expressions don't reuse aggregate functions row-wise on the unaggregated DF. (C) and (D) don't implement the rule.

---

## Q80 — Section 2: Data Processing
**Objective:** Remove outliers from a Spark DataFrame based on standard deviation or IQR

Using the IQR rule, you remove rows outside `[Q1 - 1.5*IQR, Q3 + 1.5*IQR]`. Q1 = 25th percentile; Q3 = 75th percentile; IQR = Q3 - Q1. Which approach correctly computes Q1 and Q3 in PySpark?

- A. `df.summary("25%","75%").collect()` — parse from the result.
- B. `df.approxQuantile("amount", [0.25, 0.75], 0.01)` — returns `[Q1, Q3]`.
- C. Either A or B works.
- D. Neither — you must use pandas.

**Answer:** C

**Explanation:** Both work; `approxQuantile` is more direct for getting just the quantiles. Either yields `Q1` and `Q3`; IQR is then computed and the filter applied.

---

## Q81 — Section 2: Data Processing
**Objective:** Compare and contrast imputing missing values with the mean or median or mode value

A continuous feature has a heavily right-skewed distribution with extreme outliers. Which imputation strategy is MOST appropriate?

- A. Mean — uses all the data, including outliers.
- B. Median — robust to outliers and skew.
- C. Mode — the most frequent value.
- D. Zero — convenient default.

**Answer:** B

**Explanation:** Median is robust to outliers and skew. Mean is pulled toward the long tail. Mode is more appropriate for categorical or near-discrete data. Zero is arbitrary.

---

## Q82 — Section 2: Data Processing
**Objective:** Compare and contrast imputing missing values with the mean or median or mode value

A data scientist wants to impute missing values with the LEAST effort but CORRECT results. Which approach is appropriate?

- A. Always use mean — it's the most common default.
- B. Examine the distribution of the feature first; choose mean for symmetric, median for skewed, mode for categorical / heavily peaked.
- C. Always use mode — it's the safest choice.
- D. Drop all rows with missing values.

**Answer:** B

**Explanation:** This is verbatim a sample exam question. There is no universally correct imputer; "examine then choose" is the right answer. Reflex defaults to mean fail on skewed data.

---

## Q83 — Section 2: Data Processing
**Objective:** Impute missing values with the mode, mean, or median value

Which Spark ML estimator imputes missing values with `mean`, `median`, or `mode`?

- A. `pyspark.ml.feature.MissingValueHandler`
- B. `pyspark.ml.feature.Imputer(strategy=...)`
- C. `pyspark.sql.functions.coalesce`
- D. `pyspark.ml.feature.NullFiller`

**Answer:** B

**Explanation:** `pyspark.ml.feature.Imputer` is the correct class with `strategy="mean"|"median"|"mode"`. It fits per-column statistics then transforms.

---

## Q84 — Section 2: Data Processing
**Objective:** Impute missing values with the mode, mean, or median value

By default, what value does `Imputer` treat as the "missing" marker?

- A. NaN
- B. None / null
- C. NaN OR null (configurable via `missingValue` parameter; default treats NaN as missing).
- D. 0

**Answer:** C

**Explanation:** `Imputer` treats NaN as missing by default. The `missingValue` parameter lets you specify another sentinel (e.g., -999) if your data encodes missingness that way.

---

## Q85 — Section 2: Data Processing
**Objective:** Use one-hot encoding for categorical features

To one-hot encode a string column `city` in Spark ML, which two-step transformation is correct?

- A. `OneHotEncoder` directly on the string column.
- B. `StringIndexer` (string → numeric index) followed by `OneHotEncoder` (index → sparse vector).
- C. `VectorAssembler` only.
- D. `StandardScaler` then `OneHotEncoder`.

**Answer:** B

**Explanation:** Spark ML's `OneHotEncoder` operates on integer-indexed inputs, not strings. You must first `StringIndexer` then `OneHotEncoder`.

---

## Q86 — Section 2: Data Processing
**Objective:** Identify and explain the model types or data sets for which one-hot encoding is or is not appropriate

For which of the following models is one-hot encoding LEAST useful (or even counterproductive)?

- A. Logistic regression.
- B. K-nearest neighbors using Euclidean distance.
- C. A gradient boosted tree model (`GBTClassifier`).
- D. A feedforward neural network.

**Answer:** C

**Explanation:** Trees split on a single feature at a time; they handle integer-encoded categoricals natively (Spark ML's tree estimators also accept categorical metadata directly). OHE just explodes the feature count without adding signal. Linear/distance-based/NN models need OHE.

---

## Q87 — Section 2: Data Processing
**Objective:** Identify and explain the model types or data sets for which one-hot encoding is or is not appropriate

A team is training a random forest classifier on a column with 10,000 distinct user agents. Which encoding strategy is MOST appropriate?

- A. One-hot encode all 10,000 — gives the model full information.
- B. Use `StringIndexer` to integer-encode; trees can split on the index. Optionally hash to a smaller dimensionality.
- C. Drop the column entirely.
- D. Convert the user agent string to its length in characters.

**Answer:** B

**Explanation:** 10,000-way OHE creates 10,000 sparse features — wasteful for trees. Index or hash; trees can split on the integer-encoded value.

---

## Q88 — Section 2: Data Processing
**Objective:** Identify scenarios where log scale transformation is appropriate

When is a `log1p` (or `log`) transform on a feature MOST appropriate?

- A. The feature is normally distributed already.
- B. The feature is right-skewed and spans several orders of magnitude (e.g., income, prices, counts).
- C. The feature contains negative values without bound.
- D. The feature is a binary indicator.

**Answer:** B

**Explanation:** Log transforms compress long right tails — useful for income/prices/counts. Already-normal features need no transform. Negative values break `log`; use `log1p` only for nonneg with possible zeros, or use signed log / Yeo-Johnson.

---

## Q89 — Section 2: Data Processing
**Objective:** Identify scenarios where log scale transformation is appropriate

A regression target `house_price` is right-skewed. You train a model on `log1p(price)` and predict `log1p(price_pred)`. To report RMSE in dollars, what must you do FIRST?

- A. Compute RMSE directly on the predictions — log RMSE equals dollar RMSE.
- B. `np.expm1(prediction)` (or `np.exp(prediction) - 1`) to invert `log1p`, THEN compute RMSE against the original-scale target.
- C. Multiply by 100.
- D. Compute `log(RMSE)`.

**Answer:** B

**Explanation:** Log-space RMSE ≠ dollar RMSE. You must invert the transform before computing the original-scale metric. `expm1` is the exact inverse of `log1p`.

---

## Q90 — Section 2: Data Processing
**Objective:** Create visualizations for categorical or continuous features

Which visualization is MOST appropriate for understanding the distribution of a SINGLE continuous variable?

- A. Bar chart.
- B. Histogram (or density / KDE) plot.
- C. Pie chart.
- D. Heatmap.

**Answer:** B

**Explanation:** Histograms (or density plots) show the empirical distribution of a continuous variable. Bar charts and pies are for categorical counts.

---

## Q91 — Section 2: Data Processing
**Objective:** Create visualizations for categorical or continuous features

Which is BEST for visualizing the distribution of a categorical variable with 8 distinct levels?

- A. Bar chart of counts (or proportions) per level.
- B. Histogram with 100 bins.
- C. Scatter plot.
- D. Line plot over time.

**Answer:** A

**Explanation:** Bar charts are the canonical categorical-distribution visualization.

---

## Q92 — Section 2: Data Processing
**Objective:** Compare two categorical or two continuous features using the appropriate method

You want to test whether two categorical variables are independent. Which test is appropriate?

- A. Pearson correlation
- B. Chi-square test of independence (on the contingency table)
- C. Student's t-test
- D. One-way ANOVA

**Answer:** B

**Explanation:** Chi-square on the contingency table tests independence of two categoricals. Pearson and t-test are for continuous. ANOVA compares continuous means across categorical groups.

---

## Q93 — Section 2: Data Processing
**Objective:** Compare two categorical or two continuous features using the appropriate method

To measure the linear relationship between two continuous features, which is appropriate?

- A. Chi-square
- B. Pearson correlation (or Spearman if you suspect monotonic-but-nonlinear)
- C. ANOVA
- D. Box plot only

**Answer:** B

**Explanation:** Pearson measures linear correlation; Spearman is its rank-based monotonic counterpart for nonlinear-but-monotonic relationships.

---

## Q94 — Section 2: Data Processing
**Objective:** Compare two categorical or two continuous features using the appropriate method

To compare a continuous feature across levels of a categorical feature (e.g., `salary` by `department`), which is MOST appropriate?

- A. Pearson correlation
- B. Chi-square
- C. Box plot for visualization + ANOVA (or Welch's t-test for 2 groups) for inference
- D. Scatter plot

**Answer:** C

**Explanation:** Box plots show distributions per group; ANOVA (or t-test for k=2) tests whether group means differ. Pearson and chi-square don't fit this case.

---

## Q95 — Section 2: Data Processing
**Objective:** Use one-hot encoding for categorical features

The `OneHotEncoder` in `pyspark.ml.feature` produces what data type as the output column?

- A. A list of integers.
- B. A `Vector` (typically sparse) suitable for `VectorAssembler` and downstream estimators.
- C. A string of one-hot bits.
- D. A separate column per category.

**Answer:** B

**Explanation:** Spark ML's `OneHotEncoder` outputs a single `SparseVector` column representing the one-hot encoding. This is then combined with other features via `VectorAssembler` into the final `features` vector.

---

## Q96 — Section 2: Data Processing
**Objective:** Compute summary statistics on a Spark DataFrame using `.summary()` or dbutils data summaries

What does `df.describe()` return that `df.summary()` does NOT?

- A. Percentiles.
- B. Nothing — `summary()` is a strict superset of `describe()`'s information.
- C. String column counts.
- D. Histogram bins.

**Answer:** B

**Explanation:** `summary()` returns count/mean/stddev/min/25/50/75/max; `describe()` returns count/mean/stddev/min/max. `summary` is a strict superset.

---

## Q97 — Section 2: Data Processing
**Objective:** Remove outliers from a Spark DataFrame based on standard deviation or IQR

A common stddev rule uses k=3 (drop |x-µ|>3σ). What is the practical implication of choosing k=1 instead of k=3?

- A. k=1 drops far more rows (~32% of a normal distribution) and may discard non-outlier signal.
- B. k=1 drops fewer rows than k=3.
- C. k=1 and k=3 are equivalent.
- D. k=1 is the standard; k=3 is too aggressive.

**Answer:** A

**Explanation:** ~68% of a normal distribution lies within 1σ; using k=1 drops the other ~32% as "outliers", which is way too aggressive and discards real signal. k=3 retains ~99.7% and is the typical conservative choice.

---

## Q98 — Section 2: Data Processing
**Objective:** Compare and contrast imputing missing values with the mean or median or mode value

For a categorical feature `country` with 5% missing values, which imputation strategy is MOST appropriate?

- A. Mean
- B. Median
- C. Mode (most frequent category) or a new explicit category `"unknown"`
- D. Drop all rows with missing `country`.

**Answer:** C

**Explanation:** Mean/median don't apply to categoricals. Mode (or an "unknown" sentinel) is the canonical choice. Dropping rows is appropriate only when missing-at-random and you can afford the data loss.

---

## Q99 — Section 2: Data Processing
**Objective:** Impute missing values with the mode, mean, or median value

`Imputer(inputCols=["age"], outputCols=["age_imputed"], strategy="median")` — what happens at `.fit(df)`?

- A. The transformer is applied to `df` immediately.
- B. The estimator computes the median of `age` and returns an `ImputerModel` containing that median; calling `.transform(df)` applies the imputation.
- C. It modifies the input DataFrame in place.
- D. It returns the input DataFrame unchanged.

**Answer:** B

**Explanation:** `Imputer` is an estimator; `.fit()` returns a model. The model is a transformer that applies the stored imputation values to any input DataFrame.

---

## Q100 — Section 2: Data Processing
**Objective:** Create visualizations for categorical or continuous features

Which Databricks notebook feature is the FASTEST way to generate quick visualizations of a Spark DataFrame without writing matplotlib code?

- A. `df.show(100)`
- B. The notebook's built-in "Visualization" / "Data Profile" tabs after a `display(df)` call.
- C. `df.toPandas().plot()`
- D. Writing the DataFrame to S3 and loading into Tableau.

**Answer:** B

**Explanation:** `display(df)` in a Databricks notebook produces an interactive grid with one-click chart and profile views.

---

## Q101 — Section 2: Data Processing
**Objective:** Remove outliers from a Spark DataFrame based on standard deviation or IQR

A team computes `Q1=10, Q3=30` for a feature using `approxQuantile`. What is the IQR-rule outlier filter?

- A. Drop rows where `x < 10 - 1.5*20` or `x > 30 + 1.5*20`, i.e., drop `x < -20` or `x > 60`.
- B. Drop rows where `x < Q1` or `x > Q3`, i.e., `x < 10` or `x > 30`.
- C. Drop rows where `x < Q1 - Q3` or `x > Q3 + Q1`.
- D. Drop rows where `x is null`.

**Answer:** A

**Explanation:** IQR = Q3 - Q1 = 20. The rule is `[Q1 - 1.5*IQR, Q3 + 1.5*IQR]` = `[-20, 60]`. Anything outside is an outlier.

---

## Q102 — Section 2: Data Processing
**Objective:** Identify scenarios where log scale transformation is appropriate

Which of the following is a feature where log transformation is typically NOT helpful?

- A. Annual household income.
- B. Population of cities.
- C. A binary `is_active` indicator.
- D. Movie box-office gross.

**Answer:** C

**Explanation:** Binary features have a degenerate distribution (0 or 1); a log transform does nothing useful (or fails on 0). The other three are heavy-tailed positive quantities where log helps.

---

## Q103 — Section 2: Data Processing
**Objective:** Identify and explain the model types or data sets for which one-hot encoding is or is not appropriate

Which is a downside of one-hot encoding a high-cardinality categorical column?

- A. It increases the feature dimensionality by N (number of categories), which can be huge and slow training.
- B. It always reduces model accuracy.
- C. It only works for binary classification.
- D. It corrupts the data.

**Answer:** A

**Explanation:** OHE on a 10,000-category column adds 10,000 sparse features. Memory and training-time costs balloon, and for tree models there's no gain. (B) and (C) are false.

---

## Q104 — Section 2: Data Processing
**Objective:** Use one-hot encoding for categorical features

Why does `OneHotEncoder` in Spark ML drop the LAST category by default (`dropLast=True`)?

- A. To save memory.
- B. To avoid multicollinearity in linear models (the "dummy variable trap"); the dropped category becomes the reference / baseline.
- C. It's a bug.
- D. Because the last category is always the most rare.

**Answer:** B

**Explanation:** With K categories, K dummy variables are linearly dependent (sum to 1). Dropping one prevents collinearity in linear/logistic regression. You can set `dropLast=False` for tree models (where collinearity doesn't matter).

---

## Q105 — Section 2: Data Processing
**Objective:** Compute summary statistics on a Spark DataFrame using `.summary()` or dbutils data summaries

`df.summary("count", "min", "max")` — what does this return?

- A. An error; `summary` doesn't accept arguments.
- B. A DataFrame containing only count, min, and max rows for each numeric column.
- C. The first three rows of the input.
- D. A pandas DataFrame.

**Answer:** B

**Explanation:** `summary` accepts a variable list of statistic names. Common ones: `"count"`, `"mean"`, `"stddev"`, `"min"`, `"25%"`, `"50%"`, `"75%"`, `"max"`, and percentiles like `"99%"`.

---

## Q106 — Section 2: Data Processing
**Objective:** Compare two categorical or two continuous features using the appropriate method

Which test is appropriate for comparing the MEAN of a continuous feature across TWO independent groups?

- A. Pearson correlation
- B. Two-sample t-test (or Welch's t-test for unequal variances)
- C. Chi-square
- D. Mann-Whitney U is the only valid option, t-test is never appropriate.

**Answer:** B

**Explanation:** Two-sample t-test (or Welch's variant) tests difference in means for two groups. Mann-Whitney is a nonparametric alternative used when normality fails — but t-test is appropriate for normal-enough data.

---

## Q107 — Section 2: Data Processing
**Objective:** Impute missing values with the mode, mean, or median value

What happens if you call `Imputer.fit(df)` on a column with 100% missing values?

- A. It silently sets imputation value to 0.
- B. It raises an error or produces NaN as the imputation value (since no non-missing data exists to compute mean/median); a downstream `transform` will leave those values unchanged or fail.
- C. It uses the median of all other columns.
- D. It drops the column.

**Answer:** B

**Explanation:** With no non-missing data, there is no statistic to compute. Behavior varies but is never silently helpful; investigate why a column is 100% missing before imputing.

---

## Q108 — Section 2: Data Processing
**Objective:** Identify and explain the model types or data sets for which one-hot encoding is or is not appropriate

For a Spark ML `GBTClassifier`, what is the cleanest way to handle a categorical feature with 50 levels?

- A. One-hot encode all 50 levels.
- B. `StringIndexer` to integer-encode (and provide `categoricalCols` metadata so the tree treats the column as categorical, not numeric).
- C. Drop the column.
- D. Convert to a binary `is_top_10` flag only.

**Answer:** B

**Explanation:** Spark ML tree estimators handle integer-encoded categoricals natively when category metadata is provided (e.g., via `StringIndexer` output which carries metadata). OHE inflates dimensionality for no gain.

---

## Q109 — Section 2: Data Processing
**Objective:** Compare two categorical or two continuous features using the appropriate method

You see a contingency table:
```
        | bought | did_not |
country |        |         |
US      |   400  |   600   |
UK      |    50  |   950   |
```
You want to test if `country` is associated with `bought`. Which test?

- A. Pearson correlation.
- B. Chi-square test of independence.
- C. ANOVA.
- D. Logistic regression coefficient significance test (only valid if you already have a model).

**Answer:** B

**Explanation:** Two categorical variables, contingency table → chi-square. (D) would work if framed as a model coefficient, but for a stand-alone independence test, chi-square is the textbook answer.

---

## Q110 — Section 2: Data Processing
**Objective:** Use one-hot encoding for categorical features

You forgot to handle UNSEEN categories in `StringIndexer`. What happens at `transform` time when an unseen value appears?

- A. Silently maps to 0.
- B. Raises an exception by default. Use `handleInvalid="keep"` to map unseen values to an extra index (or `"skip"` to drop those rows).
- C. Maps to the most frequent index.
- D. Maps to NaN.

**Answer:** B

**Explanation:** `handleInvalid` controls behavior on unseen values; the default `"error"` throws. `"keep"` adds an extra "unknown" index slot; `"skip"` drops rows.

---

## Q111 — Section 2: Data Processing
**Objective:** Identify scenarios where log scale transformation is appropriate

For a regression task with a heavily right-skewed target, applying `log1p` to the target and training a linear regression has what effect?

- A. The model's coefficients become uninterpretable.
- B. The training objective becomes a Gaussian-likelihood approximation in log space, which often improves accuracy on right-skewed targets — but you must `expm1` predictions before reporting metrics in original units.
- C. The model can no longer fit.
- D. The R² becomes meaningless.

**Answer:** B

**Explanation:** Log-transforming a skewed target is a standard regression trick. Predictions must be inverse-transformed for original-scale metrics and interpretability.

---

## Q112 — Section 2: Data Processing
**Objective:** Remove outliers from a Spark DataFrame based on standard deviation or IQR

When is IQR-based outlier removal MORE robust than stddev-based?

- A. When the data is normally distributed.
- B. When the data is skewed or heavy-tailed — IQR uses quantiles (robust to extremes) whereas mean/stddev are themselves pulled by outliers.
- C. IQR is always less robust.
- D. The two are mathematically equivalent.

**Answer:** B

**Explanation:** Mean and stddev are sensitive to outliers — the very thing you're trying to detect. Quantiles are not. IQR is the preferred choice for skewed data.

---

## Q113 — Section 2: Data Processing
**Objective:** Compare and contrast imputing missing values with the mean or median or mode value

What is a downside of MEAN imputation that MEDIAN imputation does not share?

- A. Mean is more expensive to compute.
- B. Mean is pulled by outliers, so on skewed data the imputed value may not represent the central tendency well; median is robust.
- C. Mean cannot be computed on Spark DataFrames.
- D. Mean only works on integers.

**Answer:** B

**Explanation:** This is the central reason to prefer median over mean on skewed data: outlier robustness.

---

## Q114 — Section 2: Data Processing
**Objective:** Identify and explain the model types or data sets for which one-hot encoding is or is not appropriate

True or False: For a deep neural network with embedding layers, one-hot encoding of a 50,000-cardinality categorical feature is typically replaced by a learned embedding layer.

- A. True — embeddings are dense, low-dimensional, and trainable; far more efficient than 50,000-D one-hot.
- B. False — neural nets require one-hot inputs.
- C. False — embeddings are only for text.
- D. True, but only for image models.

**Answer:** A

**Explanation:** Embedding layers map high-cardinality categoricals to dense low-dimensional vectors that the network learns jointly with the prediction task. OHE is wasteful at that cardinality.

---

# Section 3 — Model Development (31%)

## Q115 — Section 3: Model Development
**Objective:** Identify methods to mitigate data imbalance in training data

A churn dataset has 10% churners and 90% non-churners. The team wants the model to learn the minority class well without changing the data. Which technique addresses this DIRECTLY at training time?

- A. Normalize the features.
- B. Use class weights / cost-sensitive learning (e.g., `weightCol` on the Spark ML estimator), assigning higher cost to misclassifying the minority class.
- C. Collect more non-churn data.
- D. Use a simpler model.

**Answer:** B

**Explanation:** Class weights / cost-sensitive learning is the canonical "easy" answer that requires no data changes. Spark ML estimators support `weightCol` directly. (A) doesn't address imbalance. (C) makes imbalance worse. (D) is unrelated.

---

## Q116 — Section 3: Model Development
**Objective:** Identify methods to mitigate data imbalance in training data

(Select TWO) Which two techniques mitigate class imbalance via DATA-level changes?

- A. Oversampling the minority class (e.g., SMOTE).
- B. Class weights in the loss function.
- C. Threshold tuning on the predicted probability.
- D. Random undersampling of the majority class.

**Answer:** A, D

**Explanation:** Oversampling and undersampling change the training data. Class weights change the loss (algorithm-level). Threshold tuning is post-hoc on the trained model. The question asks specifically about data-level changes.

---

## Q117 — Section 3: Model Development
**Objective:** Compare estimators and transformers

In Spark ML, which is the correct pairing of estimator → fitted transformer?

- A. `StringIndexer` → `StringIndexerModel`
- B. `OneHotEncoder` → `OneHotEncoderModel`
- C. `RandomForestClassifier` → `RandomForestClassificationModel`
- D. All of the above.

**Answer:** D

**Explanation:** Every estimator's `.fit()` returns a model with `.transform()`. Naming is consistent: `EstimatorName` → `EstimatorNameModel`.

---

## Q118 — Section 3: Model Development
**Objective:** Compare estimators and transformers

Which Spark ML class is a TRANSFORMER (no `.fit()` required)?

- A. `Imputer`
- B. `StringIndexer`
- C. `VectorAssembler`
- D. `StandardScaler`

**Answer:** C

**Explanation:** `VectorAssembler` is pure transformation — it stacks columns into a vector with no learned state. The other three are estimators that compute statistics during `fit`.

---

## Q119 — Section 3: Model Development
**Objective:** Develop a training pipeline

Which call applies a fitted `PipelineModel` to a test DataFrame, returning predictions?

- A. `pipeline_model.predict(test_df)`
- B. `pipeline_model.transform(test_df)`
- C. `pipeline_model.fit(test_df)`
- D. `pipeline_model.score(test_df)`

**Answer:** B

**Explanation:** Pipelines (and all Spark ML models) use `.transform()` — every stage either transforms or has a model that transforms. There is no `.predict()` on Spark ML models.

---

## Q120 — Section 3: Model Development
**Objective:** Use Hyperopt's `fmin` operation to tune a model's hyperparameters

Hyperopt's `fmin(fn=objective, space=space, algo=tpe.suggest, max_evals=50, trials=SparkTrials(parallelism=4))` — what does `SparkTrials(parallelism=4)` do?

- A. Trains one model 4 times.
- B. Runs up to 4 trials in parallel across the Spark cluster, each trial training a single-node model on a worker.
- C. Distributes the gradient calculation of a single model across 4 workers.
- D. Splits the data into 4 folds.

**Answer:** B

**Explanation:** `SparkTrials` is Hyperopt's Databricks-aware backend for parallel HPO: many trials in parallel, each training a single-node model on one worker. It does NOT make a model itself distributed.

---

## Q121 — Section 3: Model Development
**Objective:** Use Hyperopt's `fmin` operation to tune a model's hyperparameters

The objective function in Hyperopt must return what?

- A. A scalar metric value only.
- B. A dictionary like `{"loss": value_to_minimize, "status": STATUS_OK}` (or just the float to minimize, in basic usage).
- C. The trained model.
- D. The hyperparameters used.

**Answer:** B

**Explanation:** Hyperopt minimizes `loss`. For a metric where higher is better (AUC, F1), return `-metric` as the loss. `STATUS_OK` indicates the trial succeeded.

---

## Q122 — Section 3: Model Development
**Objective:** Perform random or grid search or Bayesian search as a method for tuning hyperparameters

Which `algo` value enables Bayesian (TPE) search in Hyperopt?

- A. `hyperopt.rand.suggest`
- B. `hyperopt.tpe.suggest`
- C. `hyperopt.grid.suggest`
- D. `hyperopt.bayes.suggest`

**Answer:** B

**Explanation:** TPE = Tree-structured Parzen Estimator, Hyperopt's Bayesian-style sampler. `rand.suggest` is random search. There is no built-in `grid.suggest` or `bayes.suggest` in Hyperopt.

---

## Q123 — Section 3: Model Development
**Objective:** Identify the number of models being trained in conjunction with a grid-search and cross-validation process

GridSearchCV with `C ∈ [0.1, 1, 10]`, `kernel ∈ [linear, rbf]`, `gamma ∈ [0.01, 0.1, 1]`, and 5-fold CV. How many models are trained in total during CV?

- A. 18
- B. 90
- C. 60
- D. 5

**Answer:** B

**Explanation:** Grid size = 3 × 2 × 3 = 18 combinations. Each combination trained across 5 folds = 18 × 5 = 90 total fits. (Plus a final refit on full training set if `refit=True`, but the canonical question asks for CV fits = 90.)

---

## Q124 — Section 3: Model Development
**Objective:** Identify the number of models being trained in conjunction with a grid-search and cross-validation process

`ParamGridBuilder().addGrid(rf.numTrees, [50, 100]).addGrid(rf.maxDepth, [5, 10]).build()` combined with a `CrossValidator(numFolds=3)` — how many models are trained?

- A. 4
- B. 12
- C. 24
- D. 7

**Answer:** B

**Explanation:** Grid = 2 × 2 = 4. Folds = 3. Total = 12.

---

## Q125 — Section 3: Model Development
**Objective:** Describe the benefits and downsides of using cross-validation over a train-validation split

Which is a downside of k-fold CV vs train-validation split?

- A. k-fold CV gives a less reliable estimate of generalization.
- B. k-fold CV is roughly k× more expensive to train.
- C. k-fold CV cannot be used with grid search.
- D. k-fold CV requires the data to be normally distributed.

**Answer:** B

**Explanation:** CV trains k models instead of 1. More compute for a more reliable estimate.

---

## Q126 — Section 3: Model Development
**Objective:** Describe the benefits and downsides of using cross-validation over a train-validation split

Which is the strongest BENEFIT of k-fold CV over a single train/val split?

- A. It is faster.
- B. The estimate of generalization performance averages across k different validation folds, reducing variance and giving a more reliable estimate.
- C. It always finds the best hyperparameters.
- D. It guarantees the model will not overfit.

**Answer:** B

**Explanation:** Variance reduction in the metric estimate is the key win. CV doesn't itself prevent overfitting and doesn't always find the best HPs (that depends on the search method).

---

## Q127 — Section 3: Model Development
**Objective:** Perform cross-validation as a part of model fitting

In Spark ML, which class performs k-fold CV with hyperparameter tuning?

- A. `KFoldEvaluator`
- B. `CrossValidator(estimator=..., estimatorParamMaps=..., evaluator=..., numFolds=...)`
- C. `GridSearchCV`
- D. `ParamGridSearch`

**Answer:** B

**Explanation:** `CrossValidator` is the Spark ML class. `GridSearchCV` is sklearn's. `TrainValidationSplit` is the single-split alternative.

---

## Q128 — Section 3: Model Development
**Objective:** Use common classification metrics: F1, Log Loss, ROC/AUC, etc.

Which metric is BEST suited to evaluate a binary classifier on a heavily IMBALANCED dataset (e.g., 1% positives)?

- A. Accuracy
- B. F1 score (or PR-AUC) — focuses on minority-class performance
- C. Mean squared error
- D. R²

**Answer:** B

**Explanation:** Accuracy is misleading on imbalanced data (you can hit 99% by predicting the majority class). F1 (or PR-AUC) balances precision and recall on the minority class.

---

## Q129 — Section 3: Model Development
**Objective:** Use common regression metrics: RMSE, MAE, R-squared, etc.

You're evaluating a regression model where outliers are present and you want a metric that is NOT dominated by a few large errors. Which is MOST appropriate?

- A. RMSE
- B. MAE (Mean Absolute Error) — linear in error, robust to large deviations
- C. R²
- D. MSE

**Answer:** B

**Explanation:** RMSE/MSE square the errors, so outliers dominate. MAE is linear in the error magnitude — more robust to outliers.

---

## Q130 — Section 3: Model Development
**Objective:** Choose the most appropriate metric for a given scenario objective

For a fraud-detection model where false positives are 100x more expensive than false negatives (you'd rather miss fraud than block a legitimate customer), which evaluation focus is appropriate?

- A. Maximize recall, accept low precision.
- B. Maximize precision (or use a high decision threshold) to minimize false positives, even at the cost of recall.
- C. Maximize accuracy.
- D. Use R².

**Answer:** B

**Explanation:** "FP > FN cost" means false positives must be minimized → precision-focused. Conversely, "FN > FP cost" (e.g., missing a cancer diagnosis) would prioritize recall.

---

## Q131 — Section 3: Model Development
**Objective:** Identify the need to exponentiate log-transformed variables before calculating evaluation metrics or interpreting predictions

A model predicts `log1p(price)`. To report RMSE in dollars:

- A. Compute RMSE on the log-space predictions; the answer is in log-dollars.
- B. Apply `np.expm1` to both predictions and targets (or just predictions if targets are already in original scale) before computing RMSE.
- C. Multiply RMSE by `e`.
- D. Compute MSE first, then sqrt — that converts back.

**Answer:** B

**Explanation:** RMSE must be computed in the units of the target you care about. Always inverse-transform before metric computation.

---

## Q132 — Section 3: Model Development
**Objective:** Assess the impact of model complexity and the bias variance tradeoff on model performance

A model has very LOW training error and very HIGH validation error. What does this indicate?

- A. Underfitting / high bias.
- B. Overfitting / high variance.
- C. Both training and validation are wrong.
- D. The model is well-calibrated.

**Answer:** B

**Explanation:** Low train + high val = the model memorized training but doesn't generalize. Classic overfitting / high variance.

---

## Q133 — Section 3: Model Development
**Objective:** Assess the impact of model complexity and the bias variance tradeoff on model performance

To reduce variance (overfitting), which is LEAST likely to help?

- A. Add regularization (L1/L2).
- B. Reduce model complexity (lower tree depth, smaller network).
- C. Get more training data.
- D. Add more polynomial / interaction features.

**Answer:** D

**Explanation:** Adding more features (especially polynomial / interaction terms) generally INCREASES variance — the opposite of what's needed.

---

## Q134 — Section 3: Model Development
**Objective:** Use ML foundations to select the appropriate algorithm for a given model scenario

A team needs an interpretable baseline model for predicting customer lifetime value (a continuous target). Which is the BEST first choice?

- A. Deep neural network.
- B. Linear regression (with optional regularization).
- C. K-means.
- D. PCA.

**Answer:** B

**Explanation:** Interpretable + continuous target = linear regression. Coefficients are directly inspectable. Deep nets are not interpretable; k-means is unsupervised; PCA is not a predictor.

---

## Q135 — Section 3: Model Development
**Objective:** Use ML foundations to select the appropriate algorithm for a given model scenario

For tabular data with mixed numeric and categorical features and ~100k rows where strong nonlinear interactions are likely, which model often gives the BEST out-of-the-box accuracy on a Databricks workflow?

- A. Linear regression
- B. Gradient boosted trees (XGBoost / LightGBM / Spark ML GBT)
- C. K-means clustering
- D. Naive Bayes

**Answer:** B

**Explanation:** GBTs are the canonical strong baseline for tabular ML. They handle mixed types, capture nonlinearity, and require minimal preprocessing.

---

## Q136 — Section 3: Model Development
**Objective:** Identify methods to mitigate data imbalance in training data

(Select TWO) Which two are valid Spark ML approaches for handling class imbalance?

- A. Set the `weightCol` parameter on the estimator (e.g., `LogisticRegression(weightCol="class_weight")`) with per-row weights inversely proportional to class frequency.
- B. Manually undersample the majority class before training.
- C. Always use accuracy as the metric.
- D. Disable all features for the majority class.

**Answer:** A, B

**Explanation:** Class weights (A) and undersampling (B) are valid. Accuracy is the WRONG metric on imbalanced data. Feature ablation by class is incoherent.

---

## Q137 — Section 3: Model Development
**Objective:** Parallelize single node models for hyperparameter tuning

A team wants to tune a single-node sklearn model's hyperparameters using Hyperopt. They want 4 trials running in parallel across the Databricks cluster, each training one sklearn model. Which Trials backend is correct?

- A. `Trials()` — serial.
- B. `SparkTrials(parallelism=4)` — parallel across the cluster, one trial per executor.
- C. `MultiprocessingTrials(n_jobs=4)`.
- D. `JoblibTrials`.

**Answer:** B

**Explanation:** `SparkTrials` is the Databricks-blessed way to parallelize single-node Hyperopt trials. `Trials()` runs serially on the driver. The others are not standard.

---

## Q138 — Section 3: Model Development
**Objective:** Develop a training pipeline

A pipeline contains stages: `[Imputer, StringIndexer, OneHotEncoder, VectorAssembler, GBTClassifier]`. Calling `pipeline.fit(train_df)` — how many of these stages will perform a `fit` operation?

- A. 0
- B. 4 (Imputer, StringIndexer, OneHotEncoder, GBTClassifier all fit; VectorAssembler is a pure transformer).
- C. 5 (all of them).
- D. 1 (only GBTClassifier).

**Answer:** B

**Explanation:** `Imputer`, `StringIndexer`, `OneHotEncoder` (in Spark 3.x), and `GBTClassifier` are estimators (they fit). `VectorAssembler` is a transformer (no fit). Total estimators in this pipeline = 4.

---

## Q139 — Section 3: Model Development
**Objective:** Use common classification metrics: F1, Log Loss, ROC/AUC, etc.

Which metric is the area under the ROC curve and represents the probability that the classifier ranks a random positive higher than a random negative?

- A. F1
- B. AUC (ROC AUC)
- C. Log loss
- D. Accuracy

**Answer:** B

**Explanation:** AUC = "rank a random positive above a random negative" is the textbook interpretation. F1 is the harmonic mean of precision and recall. Log loss is the negative log-likelihood.

---

## Q140 — Section 3: Model Development
**Objective:** Use common classification metrics: F1, Log Loss, ROC/AUC, etc.

If a model outputs probabilities and you want to penalize confident wrong predictions HEAVILY, which metric is appropriate?

- A. Accuracy
- B. Log loss (cross-entropy)
- C. F1
- D. AUC

**Answer:** B

**Explanation:** Log loss is unbounded above for confidently-wrong predictions (predicting probability ~0 for the true class incurs huge loss). Accuracy and F1 use the hard label only.

---

## Q141 — Section 3: Model Development
**Objective:** Use common regression metrics: RMSE, MAE, R-squared, etc.

Which regression metric is the proportion of variance in the target explained by the model?

- A. MAE
- B. RMSE
- C. R²
- D. MAPE

**Answer:** C

**Explanation:** R² = 1 - SS_res / SS_tot. 1 = perfect, 0 = no better than predicting the mean, negative = worse than mean.

---

## Q142 — Section 3: Model Development
**Objective:** Perform cross-validation as a part of model fitting

`CrossValidator(numFolds=5, parallelism=3)` — what does `parallelism=3` do?

- A. Trains 3-fold CV instead of 5.
- B. Splits each fold into 3 sub-folds.
- C. Runs up to 3 (param-grid combo × fold) trainings in parallel across the cluster.
- D. Uses 3 GPUs.

**Answer:** C

**Explanation:** `parallelism` parallelizes the individual training jobs across the cluster. With grid size 4 and folds 5 = 20 jobs, `parallelism=3` runs 3 at a time.

---

## Q143 — Section 3: Model Development
**Objective:** Compare estimators and transformers

Which is a TRUE statement about Spark ML pipelines?

- A. Once fit, a `PipelineModel` is itself a transformer (`.transform()`-only) that applies all stage transformations in order.
- B. A `PipelineModel` must be refit before each `transform`.
- C. A `Pipeline` cannot mix estimators and transformers.
- D. A `Pipeline` runs each stage in parallel.

**Answer:** A

**Explanation:** `PipelineModel.transform(df)` applies all stages (fitted estimators are now models = transformers; original transformers stay as-is). Stages are run sequentially.

---

## Q144 — Section 3: Model Development
**Objective:** Use Hyperopt's `fmin` operation to tune a model's hyperparameters

In Hyperopt's `space`, which expression draws an integer from {3, 5, 7}?

- A. `hp.choice("max_depth", [3, 5, 7])`
- B. `hp.uniform("max_depth", 3, 7)`
- C. `hp.normal("max_depth", 5, 2)`
- D. `hp.quniform("max_depth", 3, 7, 0.5)`

**Answer:** A

**Explanation:** `hp.choice` samples from a discrete set. `uniform` is continuous. `normal` is normal-distributed. `quniform` samples a continuous range quantized to a step.

---

## Q145 — Section 3: Model Development
**Objective:** Perform random or grid search or Bayesian search as a method for tuning hyperparameters

Which is a key ADVANTAGE of Bayesian HPO (TPE / Optuna) over random or grid search?

- A. It explores all possible combinations.
- B. It uses past trial results to choose new promising hyperparameters, often finding good configurations in fewer trials than random or grid.
- C. It is deterministic and reproducible.
- D. It works only with integer hyperparameters.

**Answer:** B

**Explanation:** Bayesian methods build a surrogate model of the objective and use it to select promising points — sample-efficient compared to blind random or exhaustive grid.

---

## Q146 — Section 3: Model Development
**Objective:** Assess the impact of model complexity and the bias variance tradeoff on model performance

A model has high training error AND high validation error. What does this indicate?

- A. Overfitting.
- B. Underfitting / high bias — model is too simple for the data.
- C. Data leakage.
- D. The validation set is too small.

**Answer:** B

**Explanation:** High error on both train and val = the model isn't even fitting the training data → underfitting / high bias. Add capacity (more features, deeper model, fewer regularizers).

---

## Q147 — Section 3: Model Development
**Objective:** Identify the number of models being trained in conjunction with a grid-search and cross-validation process

If you use Hyperopt with `max_evals=50` and 5-fold CV INSIDE the objective function, how many model fits occur?

- A. 50
- B. 250 (50 trials × 5 folds each)
- C. 55
- D. 10

**Answer:** B

**Explanation:** Hyperopt's `max_evals` is the number of HP trials. If each trial does k-fold CV internally, multiply by k.

---

## Q148 — Section 3: Model Development
**Objective:** Use Hyperopt's `fmin` operation to tune a model's hyperparameters

Which call returns the best hyperparameters after `fmin(...)` runs?

- A. The return value of `fmin` itself — a dict of best parameter values.
- B. `trials.best`
- C. `tpe.best_params()`
- D. There is no direct API; you must iterate manually.

**Answer:** A

**Explanation:** `best = fmin(...)` returns the dict of best parameter values directly. (`hp.choice` returns the chosen index — use `space_eval(space, best)` to get the actual values.)

---

## Q149 — Section 3: Model Development
**Objective:** Compare estimators and transformers

What does `fitted_indexer = StringIndexer(...).fit(df)` return?

- A. A new DataFrame with the indexed column.
- B. A `StringIndexerModel` (a transformer) that holds the learned label-to-index mapping.
- C. None (mutates in place).
- D. A list of distinct categories.

**Answer:** B

**Explanation:** Estimators' `.fit()` returns a Model, which is a transformer that carries the learned state.

---

## Q150 — Section 3: Model Development
**Objective:** Perform random or grid search or Bayesian search as a method for tuning hyperparameters

Random search is often surprisingly competitive with grid search because:

- A. Random search trains fewer models.
- B. In high-dimensional HP spaces, only a few hyperparameters truly matter; random search explores many distinct values for each important HP, while grid search wastes trials on a dense sweep of unimportant ones (Bergstra & Bengio 2012).
- C. Random search is more deterministic.
- D. Random search always uses TPE under the hood.

**Answer:** B

**Explanation:** The Bergstra & Bengio paper is the classic citation. Random search dominates grid in high-D because effective dimensionality is usually low.

---

## Q151 — Section 3: Model Development
**Objective:** Use ML foundations to select the appropriate algorithm for a given model scenario

For a binary classification problem where you need calibrated probabilities (the predicted probability should be interpretable as a true frequency), which algorithm is naturally well-calibrated WITHOUT additional steps?

- A. Logistic regression — directly models log-odds.
- B. Random forest (raw vote frequency is often miscalibrated).
- C. SVM with hinge loss.
- D. K-nearest neighbors.

**Answer:** A

**Explanation:** Logistic regression's output is a probability by construction (sigmoid of a linear function). Random forests / SVMs often need probability calibration (Platt scaling, isotonic) before use.

---

## Q152 — Section 3: Model Development
**Objective:** Use Hyperopt's `fmin` operation to tune a model's hyperparameters

The Mar 2025 exam guide still references Hyperopt's `fmin` as an objective. What is the current Databricks recommendation for HPO going forward (post DBR ML 16.4 LTS)?

- A. Continue using Hyperopt forever.
- B. Use Optuna for single-node HPO and Ray Tune for distributed HPO; Hyperopt is removed from DBR ML after 16.4 LTS.
- C. Use scikit-learn's `GridSearchCV` only.
- D. Use AutoML for all HPO; manual HPO is deprecated.

**Answer:** B

**Explanation:** Databricks docs state Hyperopt is removed from DBR ML after 16.4 LTS; the new recommendation is Optuna or Ray Tune. The exam still tests Hyperopt because the Mar 2025 guide does.

---

## Q153 — Section 3: Model Development
**Objective:** Use common classification metrics: F1, Log Loss, ROC/AUC, etc.

F1 is the harmonic mean of precision and recall. For a model with precision 0.8 and recall 0.4, what is F1?

- A. 0.6
- B. 0.533...
- C. 0.4
- D. 0.8

**Answer:** B

**Explanation:** F1 = 2 × (P × R) / (P + R) = 2 × (0.8 × 0.4) / (0.8 + 0.4) = 0.64 / 1.2 ≈ 0.533.

---

## Q154 — Section 3: Model Development
**Objective:** Use ML foundations to select the appropriate algorithm for a given model scenario

You have 1 million tabular rows and need a model that handles missing values natively, doesn't require feature scaling, and captures nonlinear interactions. Which is the BEST choice?

- A. Linear regression
- B. K-means
- C. Gradient boosted trees (e.g., LightGBM / XGBoost / Spark ML GBT)
- D. Principal component analysis

**Answer:** C

**Explanation:** GBTs handle missing values (LightGBM/XGBoost natively; Spark ML GBT after explicit handling), don't need scaling, and model nonlinearity. (B) and (D) are unsupervised; (A) needs scaling and won't capture nonlinearity.

---

## Q155 — Section 3: Model Development
**Objective:** Develop a training pipeline

Why is it BETTER to wrap preprocessing and model in a single Spark ML Pipeline rather than running steps manually?

- A. It is faster at runtime.
- B. The Pipeline guarantees the SAME preprocessing is applied at train and inference time, preventing train/serve skew; the entire pipeline is one MLflow-loggable artifact.
- C. Pipelines reduce memory usage by half.
- D. Pipelines automatically deploy to serving endpoints.

**Answer:** B

**Explanation:** Train/serve skew (different preprocessing at train vs inference) is one of the most common silent ML bugs. A Pipeline packages it all together.

---

## Q156 — Section 3: Model Development
**Objective:** Identify methods to mitigate data imbalance in training data

A team has a 1:1000 class imbalance. After applying SMOTE oversampling, what is one risk?

- A. Loss of all minority examples.
- B. The synthetic minority examples may not reflect the true distribution and can cause the model to overfit to artifacts of SMOTE's interpolation in feature space.
- C. The model can no longer be trained.
- D. SMOTE always reduces accuracy.

**Answer:** B

**Explanation:** SMOTE synthesizes examples by interpolating between minority points. With very heavy imbalance or low-quality features, those synthetics can be unrealistic, causing overfitting to SMOTE's interpolation pattern.

---

## Q157 — Section 3: Model Development
**Objective:** Perform random or grid search or Bayesian search as a method for tuning hyperparameters

Which search method evaluates EVERY combination in the parameter grid?

- A. Random search
- B. Grid search
- C. Bayesian / TPE
- D. Hyperband

**Answer:** B

**Explanation:** Grid search is exhaustive over the Cartesian product.

---

## Q158 — Section 3: Model Development
**Objective:** Use common regression metrics: RMSE, MAE, R-squared, etc.

A model has RMSE=10 and MAE=5. What does this gap suggest?

- A. The model is poorly calibrated.
- B. There are a few large errors (outliers in the residuals) — RMSE is more sensitive than MAE to large errors, so the gap reflects their presence.
- C. The metrics were computed incorrectly.
- D. RMSE and MAE should always be equal.

**Answer:** B

**Explanation:** RMSE >> MAE indicates heavy-tailed residuals. RMSE squares before averaging, amplifying outliers; MAE is linear and robust.

---

## Q159 — Section 3: Model Development
**Objective:** Compare estimators and transformers

Which is the SIMPLEST way to verify whether a Spark ML class is an estimator or a transformer?

- A. Look at the class name suffix.
- B. Check if it has a `.fit()` method (estimator) or only `.transform()` (transformer).
- C. Check the documentation tag.
- D. Run it and see if it errors.

**Answer:** B

**Explanation:** Estimators have `.fit()`. Transformers have only `.transform()`. (Models — produced by `.fit()` — are transformers.)

---

## Q160 — Section 3: Model Development
**Objective:** Assess the impact of model complexity and the bias variance tradeoff on model performance

To reduce bias (underfitting), which is LEAST likely to help?

- A. Add more features or interactions.
- B. Use a more flexible model (deeper tree, larger network).
- C. Train longer / more epochs.
- D. Increase L2 regularization.

**Answer:** D

**Explanation:** Increasing regularization REDUCES variance and INCREASES bias — opposite of what underfitting needs.

---

## Q161 — Section 3: Model Development
**Objective:** Identify the number of models being trained in conjunction with a grid-search and cross-validation process

`TrainValidationSplit(estimator=..., estimatorParamMaps=grid_of_size_8)` — how many models are trained?

- A. 1
- B. 8 (one per parameter combination, single split)
- C. 16
- D. 40

**Answer:** B

**Explanation:** `TrainValidationSplit` is a single train/val split (no k folds), so model count = grid size. Cheaper than `CrossValidator` but higher variance in the estimate.

---

## Q162 — Section 3: Model Development
**Objective:** Choose the most appropriate metric for a given scenario objective

For evaluating a regression model where the target spans 5 orders of magnitude, which metric communicates RELATIVE error better than absolute error?

- A. RMSE
- B. MAE
- C. MAPE (Mean Absolute Percentage Error) or RMSLE (Root Mean Squared Log Error)
- D. R²

**Answer:** C

**Explanation:** When values span orders of magnitude, a $5 error matters very differently for a $10 vs a $1M item. MAPE/RMSLE express relative error.

---

## Q163 — Section 3: Model Development
**Objective:** Use ML foundations to select the appropriate algorithm for a given model scenario

For a strictly LINEAR relationship between features and target, with thousands of features and possible multicollinearity, which is BEST?

- A. Linear regression with L2 regularization (Ridge) — handles multicollinearity by shrinking coefficients.
- B. Random forest.
- C. K-means.
- D. KNN.

**Answer:** A

**Explanation:** Ridge is the textbook fix for multicollinearity in linear regression. Trees and clustering aren't the right tool for a known-linear relationship.

---

## Q164 — Section 3: Model Development
**Objective:** Use Hyperopt's `fmin` operation to tune a model's hyperparameters

You want to log every Hyperopt trial as a nested MLflow run under one parent. What is the standard pattern?

- A. `with mlflow.start_run(): fmin(..., trials=...)` — Hyperopt + MLflow autologging automatically nests if MLflow autolog is enabled in Databricks.
- B. Hyperopt cannot integrate with MLflow.
- C. You must call `mlflow.log_metric` outside of `fmin`.
- D. Nesting is unsupported in MLflow.

**Answer:** A

**Explanation:** Databricks autologging with Hyperopt + `SparkTrials` nests each trial as a child run of the active parent run.

---

## Q165 — Section 3: Model Development
**Objective:** Identify methods to mitigate data imbalance in training data

Threshold tuning is a post-hoc imbalance-handling technique. What does it involve?

- A. Retraining the model with new data.
- B. Choosing a decision threshold (other than 0.5) on the predicted probability to optimize a chosen metric — e.g., lowering the threshold to capture more minority-class positives.
- C. Adding more features.
- D. Stratified k-fold.

**Answer:** B

**Explanation:** A well-calibrated classifier outputs probabilities; the decision threshold is a hyperparameter you can tune AFTER training to trade precision for recall.

---

## Q166 — Section 3: Model Development
**Objective:** Use common classification metrics: F1, Log Loss, ROC/AUC, etc.

Precision = TP / (TP + FP). Recall = TP / (TP + FN). Which describes a CHARACTERISTIC TRADEOFF?

- A. Increasing recall almost always increases precision.
- B. Increasing the decision threshold typically increases precision and decreases recall.
- C. F1 is always between precision and recall.
- D. AUC and accuracy are equivalent.

**Answer:** B

**Explanation:** Raising the threshold = predicting positive less often = fewer FPs (higher precision) and more FNs (lower recall). This is the classic PR tradeoff.

---

## Q167 — Section 3: Model Development
**Objective:** Develop a training pipeline

Where in a Spark ML Pipeline should the `VectorAssembler` typically go?

- A. First — before any other transformations.
- B. After all feature encoding / imputation / scaling / one-hot stages and immediately BEFORE the final estimator.
- C. Last — after the model.
- D. Order doesn't matter.

**Answer:** B

**Explanation:** `VectorAssembler` stacks pre-processed feature columns into the single `features` vector that the downstream estimator (e.g., `RandomForestClassifier(featuresCol="features")`) consumes. Order matters: encoding before assembly; assembly before model.

---

## Q168 — Section 3: Model Development
**Objective:** Perform cross-validation as a part of model fitting

After `cv_model = CrossValidator(...).fit(train_df)`, what is `cv_model.bestModel`?

- A. The PipelineModel from the best hyperparameter combination, refit on the FULL training data after CV.
- B. The PipelineModel from the best fold's training only.
- C. The CV scores dictionary.
- D. A list of all PipelineModels trained.

**Answer:** A

**Explanation:** `CrossValidator` selects the best HP combination by mean CV metric, then refits the estimator on the FULL training set with those HPs. That refit model is `bestModel`.

---

## Q169 — Section 3: Model Development
**Objective:** Identify the need to exponentiate log-transformed variables before calculating evaluation metrics or interpreting predictions

A team trains a model with `log1p(sales)` as the target. To get the predicted SALES (not log-sales), apply:

- A. `np.log(predictions)`
- B. `np.expm1(predictions)`
- C. `np.exp(predictions)`
- D. `10 ** predictions`

**Answer:** B

**Explanation:** `log1p(x) = log(1+x)`. Its inverse is `expm1(x) = exp(x) - 1`. Using `exp` alone gives `1 + sales` rather than `sales`.

---

## Q170 — Section 3: Model Development
**Objective:** Compare estimators and transformers

A `StandardScaler` in Spark ML is an estimator. What state does its `.fit()` learn?

- A. Nothing.
- B. The mean and standard deviation of each input column, stored in the resulting `StandardScalerModel`.
- C. The full distribution of each column.
- D. The number of rows.

**Answer:** B

**Explanation:** `StandardScaler` learns per-column mean (if `withMean=True`) and stddev (if `withStd=True`); the model applies `(x - mean) / std` per column at transform time.

---

## Q171 — Section 3: Model Development
**Objective:** Use Hyperopt's `fmin` operation to tune a model's hyperparameters

What does `hp.loguniform("lr", -5, -1)` sample?

- A. A linear value between -5 and -1.
- B. A value `x` such that `log(x)` is uniformly distributed in `[-5, -1]`, i.e., `x` lies in `[exp(-5), exp(-1)] ≈ [0.0067, 0.367]`.
- C. An integer in {-5, ..., -1}.
- D. A random log file.

**Answer:** B

**Explanation:** `loguniform(low, high)` samples in log-space so the distribution is uniform on a log scale — appropriate for learning rates, regularization strengths, etc., that span orders of magnitude.

---

## Q172 — Section 3: Model Development
**Objective:** Assess the impact of model complexity and the bias variance tradeoff on model performance

A learning curve shows training error plateauing high and validation error similarly high, with little gap. What does this typically indicate?

- A. Overfitting; reduce model complexity.
- B. High bias / underfitting; more data alone won't help; need a more flexible model or better features.
- C. Class imbalance.
- D. Data leakage.

**Answer:** B

**Explanation:** High floor on both curves = the model is not flexible enough to fit the signal. More data converges asymptotically to the same plateau. Increase capacity or improve features.

---

## Q173 — Section 3: Model Development
**Objective:** Parallelize single node models for hyperparameter tuning

Which is the KEY assumption that lets `SparkTrials` parallelize HPO?

- A. Each HP trial trains a SINGLE-NODE model (e.g., sklearn) — these can run independently on different workers.
- B. The model is distributed across the entire cluster.
- C. The data is unbounded.
- D. The cluster has GPUs.

**Answer:** A

**Explanation:** Each trial = one model on one worker. Many workers = many trials in parallel. If the model itself were distributed (e.g., Spark ML estimator using the whole cluster), trials couldn't run in parallel.

---

## Q174 — Section 3: Model Development
**Objective:** Perform random or grid search or Bayesian search as a method for tuning hyperparameters

A team has a small budget of 15 HPO trials and a 7-dimensional hyperparameter space. Which strategy is LIKELY to give the best result?

- A. Grid search with one value per dimension (2^7 = 128 combinations) — but they can only afford 15.
- B. Bayesian (TPE) or random search — they're sample-efficient in high dimensions, while a coarse grid would massively underrepresent each axis.
- C. Train a single hand-tuned model.
- D. Use defaults; HPO is unnecessary.

**Answer:** B

**Explanation:** In high-D HP spaces with tight budgets, Bayesian (or even random) search beats grid. Grid would need 2^7 = 128 minimum.

---

## Q175 — Section 3: Model Development
**Objective:** Use common regression metrics: RMSE, MAE, R-squared, etc.

R² can be negative if:

- A. The data is small.
- B. The model performs WORSE than just predicting the mean of the target.
- C. The target is normalized to [0,1].
- D. Never — R² is always between 0 and 1.

**Answer:** B

**Explanation:** R² = 1 - SS_res / SS_tot. If the model's SS_res > SS_tot (worse than predicting the mean), R² is negative.

---

## Q176 — Section 3: Model Development
**Objective:** Identify methods to mitigate data imbalance in training data

For a Spark ML logistic regression with class imbalance, the simplest mitigation is to set `weightCol`. How do you typically compute the per-row weights?

- A. Set `weightCol` to a column of 1s.
- B. Set `weightCol` to a column of values inversely proportional to the row's class frequency — e.g., minority rows weighted as `N / (k * n_minority)`, majority as `N / (k * n_majority)`.
- C. Set `weightCol` to the row index.
- D. Set `weightCol` to the predicted probability.

**Answer:** B

**Explanation:** Balanced class weights = inverse-frequency weighting. Sklearn calls this `class_weight="balanced"`; in Spark ML you compute it manually and put it in a column.

---

# Section 4 — Model Deployment (12%)

## Q177 — Section 4: Model Deployment
**Objective:** Identify the differences and advantages of model serving approaches: batch, realtime, and streaming

Which deployment mode is BEST for nightly scoring of 100 million records?

- A. Batch — scheduled Job that loads the model and runs predictions over the Delta table.
- B. Realtime — Model Serving endpoint, one HTTP request per record.
- C. Streaming with DLT and per-record latency requirements.
- D. Manual SQL queries.

**Answer:** A

**Explanation:** Nightly + bulk = batch. Realtime / streaming are overkill (and far more expensive) for this access pattern.

---

## Q178 — Section 4: Model Deployment
**Objective:** Identify the differences and advantages of model serving approaches: batch, realtime, and streaming

A platform receives 50,000 events per second from Kafka and needs to apply an anomaly-detection model to each event in near-realtime, with autoscaling on burst traffic. Which design fits BEST?

- A. Batch Job triggered hourly.
- B. Delta Live Tables pipeline reading the Kafka source and applying the model as a Spark UDF.
- C. Model Serving endpoint, one HTTP request per event.
- D. A single Python script on a small VM.

**Answer:** B

**Explanation:** Tens of thousands of events/sec + autoscaling + near-realtime = streaming on Databricks = DLT + Spark UDF. Model Serving is for per-request HTTP; not throughput-elastic at this volume.

---

## Q179 — Section 4: Model Deployment
**Objective:** Identify the differences and advantages of model serving approaches: batch, realtime, and streaming

Which deployment mode does Databricks Model Serving (a REST endpoint) BEST fit?

- A. Daily batch over a Delta table.
- B. Sub-second per-request realtime inference, e.g., fraud-scoring a single transaction as part of a synchronous web flow.
- C. Throughput-elastic streaming of millions of events per second.
- D. None of the above.

**Answer:** B

**Explanation:** Model Serving endpoints are low-latency, per-request HTTP. For batch and high-throughput streaming, use Jobs and DLT respectively.

---

## Q180 — Section 4: Model Deployment
**Objective:** Use pandas to perform batch inference

To use a UC-registered model `cat.sch.churn@champion` to score a pandas DataFrame `new_df`, which is correct?

- A. `mlflow.pyfunc.load_model("models:/cat.sch.churn@champion").predict(new_df)`
- B. `mlflow.sklearn.load_model("models:/cat.sch.churn@champion")(new_df)`
- C. `mlflow.spark.load_model("models:/cat.sch.churn@champion").predict(new_df)`
- D. `spark.read.model("cat.sch.churn").predict(new_df)`

**Answer:** A

**Explanation:** `mlflow.pyfunc.load_model` works for any logged model flavor and exposes a unified `.predict(df)` interface. The pyfunc abstraction is the recommended general-purpose loader.

---

## Q181 — Section 4: Model Deployment
**Objective:** Use pandas to perform batch inference

To distribute batch inference across a Spark cluster (rather than running on the driver), what is the BEST approach?

- A. Convert the Spark DataFrame to pandas with `.toPandas()` (driver only) and call `.predict`.
- B. Use `mlflow.pyfunc.spark_udf(spark, model_uri)` to create a Spark UDF and apply it to the Spark DataFrame.
- C. Loop row-by-row with a Python `for` loop.
- D. Save the model as JSON and parse it manually in Spark.

**Answer:** B

**Explanation:** `mlflow.pyfunc.spark_udf` makes the model callable as a Spark UDF (loaded once per worker), enabling distributed batch inference at scale.

---

## Q182 — Section 4: Model Deployment
**Objective:** Identify how streaming inference is performed with Delta Live Tables

In a DLT pipeline applying a model to streaming data, what is the canonical pattern?

- A. Load the model on every record.
- B. Define a `@dlt.table` (or `@dlt.view`) that reads the streaming source and applies the model as a Spark UDF; the UDF loads the model once per worker.
- C. Call a Model Serving endpoint over HTTP for every record.
- D. Use pandas iterrows inside the DLT pipeline.

**Answer:** B

**Explanation:** DLT + Spark UDF (model loaded once per worker) is the canonical streaming-inference pattern on Databricks. Per-record HTTP would saturate at high throughput; per-record model loading would crater throughput.

---

## Q183 — Section 4: Model Deployment
**Objective:** Deploy and query a model for realtime inference

To query a Databricks Model Serving endpoint named `churn_ep` with a row of features `{"age": 35, "income": 50000}`, the request body format is approximately:

- A. `{"churn_ep": {"age": 35, "income": 50000}}`
- B. `{"dataframe_records": [{"age": 35, "income": 50000}]}` posted to `/serving-endpoints/churn_ep/invocations`.
- C. `{"sql": "SELECT predict(35, 50000)"}`
- D. `[35, 50000]` as a raw array.

**Answer:** B

**Explanation:** Databricks Model Serving accepts MLflow's standard payloads: `dataframe_records`, `dataframe_split`, or `instances`. The endpoint is `POST /serving-endpoints/{name}/invocations`.

---

## Q184 — Section 4: Model Deployment
**Objective:** Split data between endpoints for realtime inference

To A/B test two versions of a model on a single serving endpoint, splitting 80% traffic to v3 and 20% to v4:

- A. Deploy two separate endpoints and ask the client to randomly choose.
- B. Configure the endpoint with two served entities (v3 and v4) and set `traffic_percentage` to 80 and 20 respectively (summing to 100).
- C. Set up DNS round-robin.
- D. Train one combined model.

**Answer:** B

**Explanation:** Multiple served entities under one endpoint, each with a `traffic_percentage`, is the native Databricks way to do canary / A/B. The endpoint routes incoming requests by the configured proportions.

---

## Q185 — Section 4: Model Deployment
**Objective:** Deploy a custom model to a model endpoint

A team has a custom inference function that pre-processes inputs, calls a scikit-learn model, and post-processes outputs. They want to deploy this end-to-end as one MLflow model. Which approach is correct?

- A. Subclass `mlflow.pyfunc.PythonModel`, implement `predict(self, context, model_input)`, then `mlflow.pyfunc.log_model(python_model=..., artifacts={"sklearn_model": ...})`.
- B. Call `mlflow.sklearn.log_model(model, "model")` directly — sklearn flavor will run all the pre/post-processing.
- C. Pickle the entire pre/post/model chain manually.
- D. There is no way to deploy custom inference logic with MLflow.

**Answer:** A

**Explanation:** `mlflow.pyfunc.PythonModel` is the canonical "custom Python model" abstraction. You package the artifacts and the wrapper logic; MLflow serves them as one model.

---

## Q186 — Section 4: Model Deployment
**Objective:** Use pandas to perform batch inference

What is a benefit of loading the model with `mlflow.pyfunc.load_model` over `mlflow.sklearn.load_model`?

- A. pyfunc is faster.
- B. pyfunc abstracts the flavor — the same calling code works regardless of whether the model is sklearn, xgboost, pyspark, or a custom PythonModel.
- C. pyfunc is the only way to score on Databricks.
- D. pyfunc requires no input schema.

**Answer:** B

**Explanation:** pyfunc gives flavor-agnostic loading and a uniform `.predict()` interface. This is what `mlflow.pyfunc.spark_udf` uses under the hood for distributed scoring.

---

## Q187 — Section 4: Model Deployment
**Objective:** Identify the differences and advantages of model serving approaches: batch, realtime, and streaming

Approximate latency targets — which pairing is CORRECT?

- A. Batch: minutes to hours; Streaming: seconds; Realtime: milliseconds.
- B. Batch: milliseconds; Streaming: hours; Realtime: minutes.
- C. All three: milliseconds.
- D. Batch and streaming both target hours; realtime targets days.

**Answer:** A

**Explanation:** The canonical latency hierarchy: batch jobs operate in minutes-to-hours; streaming aims for seconds end-to-end; realtime endpoints target sub-second.

---

## Q188 — Section 4: Model Deployment
**Objective:** Deploy a custom model to a model endpoint

Inside `PythonModel.predict(self, context, model_input)`, where do persistent artifacts (e.g., a pickled sklearn model used internally) come from?

- A. They must be hardcoded as paths inside the predict method.
- B. They are passed via the `artifacts={"name": "path"}` arg of `log_model` and accessed at runtime via `context.artifacts["name"]`, which resolves to the locally-extracted path.
- C. They are auto-detected from a `requirements.txt`.
- D. Artifacts cannot be used inside `PythonModel`.

**Answer:** B

**Explanation:** `context.artifacts["name"]` gives you a local filesystem path to the artifact MLflow extracted at serving time. This is the standard pattern.

---

## Q189 — Section 4: Model Deployment
**Objective:** Identify how streaming inference is performed with Delta Live Tables

Which is a benefit of using DLT for streaming inference vs writing a Structured Streaming job by hand?

- A. DLT requires more boilerplate.
- B. DLT handles autoscaling, dependency tracking, checkpointing, schema enforcement, and data-quality expectations declaratively, freeing the data scientist to focus on inference logic.
- C. DLT only works for batch.
- D. DLT does not support Spark UDFs.

**Answer:** B

**Explanation:** DLT is declarative and handles the operational concerns of streaming pipelines. You declare what each table should be (including model-UDF application); DLT manages the rest.

---

## Q190 — Section 4: Model Deployment
**Objective:** Identify the differences and advantages of model serving approaches: batch, realtime, and streaming

A model team wants to compute predictions for an entire Delta table once a day and write results to another Delta table. Which is the SIMPLEST appropriate pattern?

- A. Provision a Model Serving endpoint and hammer it with millions of requests.
- B. Schedule a Databricks Job that loads the model, applies it via Spark UDF over the Delta source, and writes results to a Delta target.
- C. Start a DLT pipeline running 24/7.
- D. Run inference manually each day in the notebook UI.

**Answer:** B

**Explanation:** Daily batch over Delta = Job + Spark UDF + Delta write. DLT is more powerful but overkill for a simple daily batch.

---

## Q191 — Section 4: Model Deployment
**Objective:** Deploy and query a model for realtime inference

When creating a Databricks Model Serving endpoint via the REST API, which field specifies the model version to serve?

- A. `model_uri` (e.g., `"models:/cat.sch.model@champion"` or `"models:/cat.sch.model/3"`) on the served entity.
- B. `experiment_id` only.
- C. `run_id` only.
- D. Endpoints serve all versions automatically.

**Answer:** A

**Explanation:** Each served entity in an endpoint config references the model URI — either by alias (`@champion`) or by version (`/3`).

---

## Q192 — Section 4: Model Deployment
**Objective:** Use pandas to perform batch inference

A scoring pipeline is failing because the input Spark DataFrame columns are in a different order than the model expects. Which is the BEST fix?

- A. Reorder the DataFrame columns manually before scoring.
- B. Log the model with a `signature` (input/output schema) so MLflow can enforce / coerce the input shape; or apply the model via `mlflow.pyfunc.spark_udf` which validates the schema.
- C. Drop all columns and start over.
- D. Convert to pandas first.

**Answer:** B

**Explanation:** MLflow model signatures capture the expected input/output schema. At score time MLflow validates and (where possible) coerces inputs. This is more robust than relying on column ordering.

---

## Q193 — Section 4: Model Deployment
**Objective:** Split data between endpoints for realtime inference

You have a Model Serving endpoint with two served entities, A (60% traffic) and B (40%). After observing B perform better, you want B at 100%. What's the change?

- A. Delete the endpoint and create a new one.
- B. Update the endpoint config to set B's `traffic_percentage` to 100 and A's to 0 (or remove A entirely).
- C. Update the model registry alias only.
- D. Restart the cluster.

**Answer:** B

**Explanation:** Traffic split is a property of the served entities list on the endpoint config. You update it (via UI or REST PUT) to move traffic.

---

## Q194 — Section 4: Model Deployment
**Objective:** Deploy a custom model to a model endpoint

Which is a valid use case for a custom `PythonModel` (vs a flavor-specific log_model)?

- A. Logging a vanilla sklearn pipeline with no custom logic.
- B. Wrapping a model with pre-processing (e.g., featurization not done in the Spark ML Pipeline), business logic, post-processing (e.g., applying a price floor), or chaining multiple models.
- C. Logging a model that uses no Python code.
- D. Logging a SQL query.

**Answer:** B

**Explanation:** `PythonModel` is the escape hatch for any Python logic around the actual ML inference. For vanilla sklearn, the flavor-specific log_model is sufficient.

---

## Q195 — Section 4: Model Deployment
**Objective:** Identify how streaming inference is performed with Delta Live Tables

Where in a DLT pipeline does the model get LOADED?

- A. Once per record, inside the UDF.
- B. Once per worker (per executor JVM) the first time the UDF is invoked, then reused — this is what makes the UDF performant at high throughput.
- C. Once per partition.
- D. Once globally on the driver, never on workers.

**Answer:** B

**Explanation:** Spark broadcasts the model artifact and loads it once per executor; subsequent batches reuse the cached model. Loading per-record would destroy throughput.

---

## Q196 — Section 4: Model Deployment
**Objective:** Use pandas to perform batch inference

What is the simplest single-line for scoring a pandas DataFrame with a UC-registered model on a single node?

- A. `mlflow.pyfunc.load_model("models:/cat.sch.model@champion").predict(pdf)`
- B. `spark.predict("cat.sch.model", pdf)`
- C. `databricks.predict("cat.sch.model@champion", pdf)`
- D. `mlflow.serve("cat.sch.model").run(pdf)`

**Answer:** A

**Explanation:** Load via pyfunc, call `.predict(pdf)`. This works on the driver for small data. For large data, switch to `pyfunc.spark_udf`.

---

## Q197 — Section 4: Model Deployment
**Objective:** Deploy and query a model for realtime inference

A served endpoint should auto-scale up to handle bursts and scale back down to save cost. Which option enables this on Databricks Model Serving?

- A. There is no auto-scaling on Model Serving.
- B. Set `min_provisioned_concurrency` and `max_provisioned_concurrency` (or workload size + scale-to-zero) on the served entity / endpoint configuration.
- C. Manually restart the endpoint each hour.
- D. Use a fixed VM count.

**Answer:** B

**Explanation:** Model Serving supports configurable min/max concurrency and scale-to-zero. The exact field names evolve; the principle is that auto-scaling is a first-class feature.

---

## Q198 — Section 4: Model Deployment
**Objective:** Identify the differences and advantages of model serving approaches: batch, realtime, and streaming

(Select TWO) Which two statements are TRUE about Databricks Model Serving endpoints?

- A. They serve UC-registered models over HTTP.
- B. They auto-scale based on traffic.
- C. They are best for tens-of-thousands-of-events-per-second streaming.
- D. They run jobs only on a fixed schedule.

**Answer:** A, B

**Explanation:** A and B describe Model Serving. C describes a streaming use case (use DLT). D describes Jobs.

---

## Q199 — Section 4: Model Deployment
**Objective:** Deploy a custom model to a model endpoint

After logging a custom `PythonModel` and registering it in UC, what additional step is needed to make it queryable over HTTP?

- A. Nothing; UC registration auto-creates the endpoint.
- B. Create a serving endpoint and configure it with a served entity pointing to the registered model URI (by version or alias); start the endpoint.
- C. Manually copy the model artifact to S3.
- D. Run `pip install` on the production cluster.

**Answer:** B

**Explanation:** Registration ≠ serving. You must explicitly create a Model Serving endpoint pointing at the model. Serving endpoints can be created in the UI or via REST.

---

## Q200 — Section 4: Model Deployment
**Objective:** Identify how streaming inference is performed with Delta Live Tables

A team designs a streaming-inference pipeline with these requirements: 30,000 events/sec, sub-second per-event latency budget, elastic scaling, schema enforcement, and built-in checkpointing. Which Databricks pattern fits BEST?

- A. Databricks Job scheduled every minute reading from S3 and applying a pandas UDF.
- B. DLT pipeline reading from the streaming source (e.g., Kafka or Auto Loader on Delta) and applying the model as a Spark UDF; DLT handles autoscaling, checkpointing, and expectations.
- C. A Model Serving endpoint receiving an HTTP request per event.
- D. A manual `Structured Streaming` job written from scratch on a single-node VM.

**Answer:** B

**Explanation:** This is the canonical streaming use case — DLT + Spark UDF gives you autoscaling, checkpointing, schema enforcement, and data quality with minimal boilerplate. Per-event HTTP would saturate; minute-scheduled jobs miss the latency target.
