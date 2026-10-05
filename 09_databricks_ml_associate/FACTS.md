# FACTS — Topic 09 Databricks Certified ML Associate

> Atomic, citable claims. Exam logistics, API names, current vs deprecated APIs, version cutoffs. Each entry has a "Last verified" date. Re-verify volatile items (especially exam guide and API deprecations) before the exam.
>
> **Convention:** if something changed and a previous fact is stale, mark the old one ~~struck-through~~ and add the new one with a fresh date below.

---

## Exam logistics

- **Current exam version: March 1, 2025 revision.** Cover page of the official PDF. _Last verified: 2026-05-23. Source: [Databricks Certified ML Associate Exam Guide PDF](https://www.databricks.com/sites/default/files/2025-02/databricks-certified-machine-learning-associate-exam-guide-1-mar-2025.pdf)._
- **Question count: 48 scored multiple-choice or multiple-select.** Multi-select questions explicitly say "Select TWO" in the stem and are less common. _Last verified: 2026-05-23._
- **Duration: 90 minutes.** Per-question budget = 1m 52s. _Last verified: 2026-05-23._
- **Passing score: 70% (widely cited; not officially published by Databricks).** Score scaling is possible — aim for 80%+ on practice for safety margin. _Last verified: 2026-05-23._
- **Cost: $200 USD per attempt + tax.** No free retakes. _Last verified: 2026-05-23. Source: [databricks.com/learn/certification/machine-learning-associate](https://www.databricks.com/learn/certification/machine-learning-associate)._
- **Retake wait: 14 days mandatory between attempts.** Effective Nov 1, 2023. Unlimited attempts (full fee each time). _Last verified: 2026-05-23. Source: [Databricks Community announcement post 50296](https://community.databricks.com/t5/certifications/official-certification-exam-retake-policy-announcement/td-p/50296)._
- **Validity: 2 years from pass date.** Recert = retake current full exam. _Last verified: 2026-05-23._
- **Delivery: online proctored via Kryterion WebAssessor.** Webcam + screen-share required. No test centers in current materials. _Last verified: 2026-05-23. Source: [webassessor.com/databricks](http://webassessor.com/databricks)._
- **Test aides allowed: NONE.** No scratch paper, no calculator, no notes, no second monitor. _Last verified: 2026-05-23._
- **Languages: English, Japanese, Portuguese (BR), Korean.** _Last verified: 2026-05-23._
- **Code language: all ML code is Python.** SQL may appear for non-ML data manipulation tasks. _Last verified: 2026-05-23._
- **Unscored experimental items may appear** — additional time is built into the 90 minutes for these. _Last verified: 2026-05-23._

## Domain weights (March 1, 2025)

| # | Domain | Weight | Approx Qs |
|---|--------|-------:|----------:|
| 1 | Databricks Machine Learning | **38%** | ~18 |
| 2 | ML Workflows / Data Processing | **19%** | ~9 |
| 3 | Model Development | **31%** | ~15 |
| 4 | Model Deployment | **12%** | ~6 |

_Last verified: 2026-05-23. Source: [databricks.com/learn/certification/machine-learning-associate](https://www.databricks.com/learn/certification/machine-learning-associate). The PDF labels Domain 2 as "Data Processing"; the certification web page labels it "ML Workflows". Same objectives._

### Obsolete (do not use)

- ~~Pre-2024 weights: 29% / 29% / 33% / 9% with explicit "Spark ML" top-level domain at 33%.~~ _Obsolete since the March 1, 2025 revision. Practice exams listing "Spark ML 33%" target the prior scope and are stale._

---

## Feature Store / Feature Engineering — current vs deprecated APIs

- **Current API: `databricks.feature_engineering.FeatureEngineeringClient`** — Unity Catalog–native, supports cross-workspace sharing, ACL inheritance, central lineage. _Last verified: 2026-05-23. Source: [FeatureEngineeringClient API reference](https://api-docs.databricks.com/python/feature-engineering/latest/feature_engineering.client.html)._
- **Deprecated API: `databricks.feature_store.FeatureStoreClient`** — workspace-local feature store. Deprecated since `databricks-feature-store` package version 0.17.0. Still functional but new code should use FeatureEngineeringClient. _Last verified: 2026-05-23. Source: [Databricks Feature Store release notes](https://docs.databricks.com/aws/en/release-notes/feature-store/databricks-feature-store)._
- **Import paths:**
  ```python
  # CURRENT (UC)
  from databricks.feature_engineering import FeatureEngineeringClient, FeatureLookup
  fe = FeatureEngineeringClient()

  # LEGACY (workspace, deprecated)
  from databricks.feature_store import FeatureStoreClient, FeatureLookup
  fs = FeatureStoreClient()
  ```
- **Method name parity:** `create_table` (UC) vs `register_table` (legacy). Exam tests this distinction. _Last verified: 2026-05-23._

## UC Model Registry — aliases vs stages

- **UC Registry uses ALIASES, not stages.** Aliases are arbitrary string labels (e.g., `@champion`, `@challenger`, `@dev`). Multiple aliases can point to one version; multiple versions can carry one alias. _Last verified: 2026-05-23. Source: [Databricks docs — Manage model lifecycle in UC](https://docs.databricks.com/aws/en/machine-learning/manage-model-lifecycle/)._
- **Legacy workspace registry uses STAGES.** `None → Staging → Production → Archived` lifecycle. Stages are deprecated for new work. _Last verified: 2026-05-23._
- **Pointing MLflow at UC:** `mlflow.set_registry_uri("databricks-uc")`. Without this, MLflow writes to the workspace registry. _Last verified: 2026-05-23._
- **Alias-setting method:** `MlflowClient.set_registered_model_alias(name, alias, version)`. _Last verified: 2026-05-23._
- **Resolving a model by alias:** `models:/catalog.schema.model@champion`. The `@alias` syntax replaces the legacy `models:/model/Production`. _Last verified: 2026-05-23._
- **Tag CRUD:** `set_registered_model_tag(name, key, value)` / `delete_registered_model_tag(name, key)`. Tags are key/value metadata, separate from aliases. _Last verified: 2026-05-23._

---

## Hyperopt timeline — read carefully

- **Hyperopt is REMOVED from Databricks Runtime ML 17.0 and later.** Recommended replacement is Optuna or Ray Tune. _Last verified: 2026-05-23. Source: [Databricks hyperparameter tuning docs](https://docs.databricks.com/aws/en/machine-learning/automl-hyperparam-tuning)._
- **Hyperopt is STILL ON THE MARCH 1, 2025 EXAM.** Section 3 objective: "Use Hyperopt's `fmin` operation to tune a model's hyperparameters." _Last verified: 2026-05-23._
- **Exam keywords for Hyperopt:** `fmin`, `hp.choice`, `hp.uniform`, `hp.loguniform`, `tpe.suggest`, `SparkTrials`, `STATUS_OK`. If the stem contains any of these, it's a Hyperopt question. _Last verified: 2026-05-23._
- **Last DBR ML to include Hyperopt by default: 16.4 LTS (May 2025).** Beyond that, you must `pip install hyperopt` yourself if you want it. _Last verified: 2026-05-23._

## Optuna — modern recommendation

- **Optuna is the recommended replacement for Hyperopt on Databricks** (post-DBR ML 17). _Last verified: 2026-05-23._
- **Core API:** `optuna.create_study(direction="maximize")`, `study.optimize(objective, n_trials=N, n_jobs=K)`, `trial.suggest_int / suggest_float / suggest_categorical`. _Last verified: 2026-05-23. Source: [Optuna docs](https://optuna.readthedocs.io/)._
- **Optuna does not have a SparkTrials equivalent.** Use `n_jobs` (joblib) for single-machine parallelism, or Optuna's Ray Tune integration for distributed. _Last verified: 2026-05-23._
- **MLflow autologging integrates with Optuna via `mlflow.optuna.autolog()` (since MLflow 2.16) or manual `mlflow.start_run(nested=True)` per trial.** _Last verified: 2026-05-23._

---

## AutoML — 2026 state

- **AutoML supports: classification, regression, forecasting.** Forecasting uses Prophet and ARIMA. _Last verified: 2026-05-23._
- **Generated artifacts:** (1) Data Exploration notebook, (2) Best Trial notebook (editable, "glass box"), (3) MLflow Experiment containing all trial runs. _Last verified: 2026-05-23._
- **Best Trial notebook is fully editable Python** — this is the "glass box" differentiator from black-box AutoML competitors. _Last verified: 2026-05-23._
- **Trigger via UI** (Experiments → Create AutoML Experiment) **or API** (`databricks.automl.classify()`, `.regress()`, `.forecast()`). _Last verified: 2026-05-23._
- **AutoML logs to a single MLflow Experiment** containing all trial runs as nested children. _Last verified: 2026-05-23._
- **MLflow 3 integration (2025-2026):** AutoML uses MLflow 3 for tracing on supported runtimes; exam still tests MLflow 2.x patterns. _Last verified: 2026-05-23._

---

## MLflow — version-relevant facts for the exam

- **Exam tests MLflow 2.x API surface.** Specifically: `mlflow.start_run`, `mlflow.log_param/metric/artifact`, `mlflow.<flavor>.log_model`, `mlflow.<flavor>.autolog`, `MlflowClient.search_runs`. _Last verified: 2026-05-23._
- **`MlflowClient.search_runs` signature (exam-relevant):**
  ```python
  client.search_runs(
      experiment_ids=[<id>],
      filter_string="metrics.auc > 0.8",
      order_by=["metrics.auc DESC"],
      max_results=1
  )
  ```
  _Last verified: 2026-05-23._

### Autologging defaults per flavor

| Flavor | Autolog call | Logs by default |
|--------|---|---|
| scikit-learn | `mlflow.sklearn.autolog()` | model, params, training_score, input_example, signature |
| Spark ML | `mlflow.pyspark.ml.autolog()` | pipeline stages, params, evaluator metrics |
| XGBoost | `mlflow.xgboost.autolog()` | model, params, eval metrics per round, feature importance |
| LightGBM | `mlflow.lightgbm.autolog()` | model, params, eval metrics per round |
| PyTorch | `mlflow.pytorch.autolog()` | model, params, training loss (manual metric logging still needed) |
| TensorFlow/Keras | `mlflow.tensorflow.autolog()` | model, history, params, tensorboard events |

_Last verified: 2026-05-23. Source: [MLflow autologging docs](https://mlflow.org/docs/latest/tracking/autolog.html)._

- **`mlflow.autolog()` (no flavor) auto-detects** which flavor is in use and enables the right one. _Last verified: 2026-05-23._

---

## Spark ML (`pyspark.ml`) — exam-relevant facts

- **`pyspark.ml` is the DataFrame-based ML library.** Current and maintained. _Last verified: 2026-05-23._
- **`pyspark.mllib` is the RDD-based ML library.** In maintenance-only mode since Spark 2.0; **frozen** since Spark 3.0. Not exam-tested for new code, but recognize the name. _Last verified: 2026-05-23. Source: [Spark MLlib docs](https://spark.apache.org/docs/latest/mllib-guide.html)._
- **Estimator vs Transformer:**
  - **Estimator** = has `.fit(df)` → returns a Transformer. Examples: `StringIndexer`, `OneHotEncoder` (since Spark 3.0), `Imputer`, `StandardScaler`, `RandomForestClassifier`, `LogisticRegression`.
  - **Transformer** = has `.transform(df)` only, no learned state. Examples: `VectorAssembler`, `Tokenizer`, `HashingTF`, any fitted `*Model`.
  - `Pipeline(stages=[...])` is itself an Estimator (calling `.fit` returns a `PipelineModel` Transformer).
  _Last verified: 2026-05-23._
- **`OneHotEncoder` requires `.fit()` since Spark 3.0** (became an Estimator). In Spark 2.x it was a Transformer. _Last verified: 2026-05-23._
- **`VectorAssembler` is Transformer-only.** No fit step. _Last verified: 2026-05-23._
- **`StringIndexer.handleInvalid`** options: `"error"` (default, throw), `"skip"` (drop row), `"keep"` (assign new index). _Last verified: 2026-05-23._

## Spark DataFrame APIs the exam tests

- **`df.summary()`** — count, mean, stddev, min, **25%, 50%, 75%**, max. Works on string columns too. _Last verified: 2026-05-23._
- **`df.describe()`** — count, mean, stddev, min, max **only**. No percentiles. _Last verified: 2026-05-23._
- **`dbutils.data.summarize(df)`** — visual profile in the notebook (histograms, missing-value counts). Databricks-only. _Last verified: 2026-05-23._
- **Train/val/test split:** `df.randomSplit([0.7, 0.15, 0.15], seed=42)`. The `seed` argument is required for reproducibility. _Last verified: 2026-05-23._

---

## Pandas API on Spark

- **Import:** `import pyspark.pandas as ps`. _Last verified: 2026-05-23._
- **Formerly known as Koalas** (standalone package); merged into PySpark 3.2 in 2021. _Last verified: 2026-05-23._
- **Coverage:** ~90% of pandas API surface. Some advanced indexing and pandas-extension-array features are missing. _Last verified: 2026-05-23._
- **Conversion:**
  ```python
  psdf = ps.from_pandas(pdf)   # pandas → pyspark.pandas
  pdf = psdf.to_pandas()       # pyspark.pandas → pandas (DRIVER memory!)
  psdf = sdf.pandas_api()      # Spark DF → pyspark.pandas
  sdf = psdf.to_spark()        # pyspark.pandas → Spark DF
  ```
  _Last verified: 2026-05-23._
- **`compute.ops_on_diff_frames`** must be enabled (via `ps.set_option`) to perform operations between two different pyspark.pandas frames. _Last verified: 2026-05-23._

---

## Cross-validation and grid-search math

- **`CrossValidator`:** k-fold CV. Trains `(grid_size × k)` models. Returns the best `Pipeline`/`Estimator` refit on the full training data. _Last verified: 2026-05-23._
- **`TrainValidationSplit`:** single hold-out split. Trains `grid_size` models. Cheaper but less robust than CV. _Last verified: 2026-05-23._
- **Default folds for `CrossValidator`:** `numFolds=3`. _Last verified: 2026-05-23._
- **`parallelism` parameter:** how many models train concurrently per fold. Default 1. Higher values trade memory for time. _Last verified: 2026-05-23._

### Grid math (exam pattern)

For a grid with hyperparameter value counts `n1, n2, ..., nm` and `k` folds:
- **`CrossValidator` total fits = n1 × n2 × ... × nm × k** *plus 1* (the final refit on full training data).
- **`TrainValidationSplit` total fits = n1 × n2 × ... × nm**, plus 1 refit.

_Last verified: 2026-05-23. The exam guide sample question 4 tests this calculation exactly._

---

## Evaluators in Spark ML

| Evaluator | Metric names |
|-----------|--------------|
| `BinaryClassificationEvaluator` | `areaUnderROC` (default), `areaUnderPR` |
| `MulticlassClassificationEvaluator` | `f1` (default), `accuracy`, `weightedPrecision`, `weightedRecall`, `logLoss` |
| `RegressionEvaluator` | `rmse` (default), `mse`, `mae`, `r2` |
| `RankingEvaluator` | `meanAveragePrecision`, `precisionAtK`, `ndcgAtK` |
| `ClusteringEvaluator` | `silhouette` (default), distance measure `squaredEuclidean` or `cosine` |

_Last verified: 2026-05-23. Source: [pyspark.ml.evaluation docs](https://spark.apache.org/docs/latest/api/python/reference/api/pyspark.ml.evaluation.html)._

---

## Model Serving — exam-relevant facts

- **Product name:** Mosaic AI Model Serving. Formerly "Databricks Model Serving" / "Serverless Real-Time Inference". _Last verified: 2026-05-23._
- **Endpoint type:** managed, autoscaling HTTPS REST endpoint for UC-registered models. _Last verified: 2026-05-23._
- **Served entity:** a registered model version (or external model). One endpoint can host multiple served entities with traffic splits. _Last verified: 2026-05-23._
- **Traffic split:** `traffic_percentage` per served entity, must sum to 100. This is the "split data between endpoints for realtime inference" exam objective. _Last verified: 2026-05-23._
- **REST endpoint:** `POST /serving-endpoints/{name}/invocations` with body `{"dataframe_records": [...]}` or `{"inputs": {...}}`. _Last verified: 2026-05-23._
- **Workload sizes:** Small (4 concurrency), Medium (16), Large (64). Scales to zero after inactivity (default 30 min). _Last verified: 2026-05-23._

## Batch / streaming inference

- **Batch inference via `mlflow.pyfunc.spark_udf`:**
  ```python
  predict_udf = mlflow.pyfunc.spark_udf(
      spark, model_uri="models:/catalog.schema.model@champion", env_manager="virtualenv"
  )
  scored = df.withColumn("prediction", predict_udf(struct(*feature_cols)))
  ```
  _Last verified: 2026-05-23._
- **`fe.score_batch()`** is the Feature Engineering Client batch-scoring helper. It automatically performs feature lookups for the model's training_set. _Last verified: 2026-05-23._
- **Streaming inference: DLT pipelines** (now branded "Lakeflow Declarative Pipelines") with a Spark UDF wrapping the model. Use for tens-of-thousands-of-events-per-second elastic throughput. _Last verified: 2026-05-23._
- **Streaming inference is NOT Model Serving.** Model Serving is request/response at low latency. DLT is elastic throughput. _Last verified: 2026-05-23._

---

## Databricks Runtime (DBR) — ML variants

- **DBR 17.3 LTS ML** — Oct 2025; Spark 4.0; **no Hyperopt** (removed). Use Optuna or Ray Tune. _Last verified: 2026-05-23. Source: [DBR 17.3 LTS release notes](https://docs.databricks.com/aws/en/release-notes/runtime/17.3lts)._
- **DBR 16.4 LTS ML** — May 2025; Spark 3.5; **last LTS with Hyperopt by default**. _Last verified: 2026-05-23._
- **DBR 15.4 LTS ML** — Spark 3.5; commonly used in production today. _Last verified: 2026-05-23._
- **DBR ML vs DBR plain:** DBR ML pre-installs MLflow, Hyperopt (≤16.4), Optuna, XGBoost, LightGBM, scikit-learn, TensorFlow, PyTorch, Horovod, and includes ML-specific Databricks utilities. _Last verified: 2026-05-23._
- **GPU runtimes:** DBR ML GPU variants ship with CUDA, cuDNN, NCCL pre-configured. _Last verified: 2026-05-23._

---

## Common imputation, encoding, transformation patterns

- **Mean imputation:** continuous, **symmetrically distributed** features. Distorts variance and is sensitive to outliers. _Last verified: 2026-05-23._
- **Median imputation:** continuous, **skewed or outlier-heavy** features. Default safe choice when in doubt. _Last verified: 2026-05-23._
- **Mode imputation:** categorical features. Mean/median don't apply. _Last verified: 2026-05-23._
- **`Imputer.strategy`** options: `"mean"`, `"median"`, `"mode"`. _Last verified: 2026-05-23._
- **One-hot encoding REQUIRED for:** linear models (regression, logistic), SVM, k-NN, neural networks, k-means clustering. _Last verified: 2026-05-23._
- **One-hot encoding NOT REQUIRED for:** tree-based models (DecisionTree, RandomForest, GBT, XGBoost, LightGBM) — they split on the integer-encoded value just fine. OHE on trees explodes feature count without benefit. _Last verified: 2026-05-23._
- **Log scale transformation appropriate when:** target or feature is **right-skewed** (long right tail), spans multiple orders of magnitude, or where multiplicative effects matter more than additive (e.g., price, income, count data). _Last verified: 2026-05-23._
- **Remember to `np.exp()` (or equivalent) predictions back to original scale** before computing RMSE/MAE on the test set. RMSE in log space ≠ RMSE on original scale. _Last verified: 2026-05-23._

---

## Class imbalance — exam-relevant techniques

- **Class weights (`weightCol` in Spark ML)** — cost-sensitive learning at training time. Native to Spark ML estimators. **Databricks-preferred answer when it's an option.** _Last verified: 2026-05-23._
- **Random oversampling of minority class** — duplicate minority rows. Risk of overfitting on duplicates.
- **Random undersampling of majority class** — discard majority rows. Risk of information loss.
- **SMOTE (Synthetic Minority Over-sampling Technique)** — synthesize minority examples in feature space. Not native to Spark ML — requires `imblearn` (pandas-only). _Last verified: 2026-05-23._
- **Threshold tuning** — choose a non-0.5 classification threshold based on the precision/recall tradeoff for your business. _Last verified: 2026-05-23._

---

## Metric → scenario mapping

- **Binary classification, balanced classes:** Accuracy, ROC AUC.
- **Binary classification, imbalanced classes:** F1, Precision/Recall, PR AUC, Log Loss.
- **Multiclass classification:** F1 (macro or weighted), Log Loss, multiclass ROC AUC.
- **Regression, units matter:** RMSE, MAE.
- **Regression, units irrelevant, want comparability:** R-squared.
- **Regression, large outliers should not dominate:** MAE (more robust than RMSE).
- **Recommendation / ranking:** MAP, NDCG, Precision@K.

_Last verified: 2026-05-23._

---

## Other things the exam tests that don't fit elsewhere

- **`mlflow.set_experiment(name)`** — sets the experiment for subsequent `mlflow.start_run` calls. Creates the experiment if it doesn't exist. _Last verified: 2026-05-23._
- **Nested runs:** `with mlflow.start_run(nested=True):` inside a parent run. Used for HPO trials. _Last verified: 2026-05-23._
- **`mlflow.<flavor>.load_model(model_uri)`** — load for inference. `mlflow.pyfunc.load_model(uri)` — load any flavor as a generic pyfunc. _Last verified: 2026-05-23._
- **Pandas UDFs (vectorized UDFs):** `@pandas_udf("double")` over `pd.Series` for batch-wise inference in Spark. Faster than row-at-a-time UDFs (Arrow batches). _Last verified: 2026-05-23._

---

## Things the exam does NOT test (don't waste time)

- Mosaic AI Agent Framework / Agent Bricks (Generative AI Engineer Associate exam)
- MLflow 3.0 traces and prompt registry (GenAI exam)
- Spark Connect / Serverless compute internals
- TorchDistributor / Horovod (Professional exam)
- DBR runtime tuning (Professional exam)
- Networking, Private Link, Unity Catalog ACLs (Data Engineer Associate exam)
- Delta Lake internals (Data Engineer Associate exam)

_Last verified: 2026-05-23. Source: official exam guide explicit objectives + research synthesis._
