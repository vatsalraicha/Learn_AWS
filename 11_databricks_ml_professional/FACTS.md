# FACTS — Databricks Certified ML Professional

> Atomic, citable claims. One claim per bullet. **Last verified: 2026-05-23.** Re-verify before any roadmap or exam-scheduling decision.

---

## Exam logistics (verbatim from official Sept 30 2025 PDF)

- The exam has **59 scored multiple-choice items** + a small unidentified number of unscored items (extra time factored in).
- Time limit is **120 minutes**.
- Registration fee is **USD $200** plus applicable local tax.
- Delivery: **online proctored only** via Webassessor / Kryterion.
- **No test aides** allowed.
- Certification **valid for 2 years**; recertification requires retaking the current live full exam.
- **Passing score is 70%** (not stated on official PDF; sourced from community reports + the Databricks standard across all certs).
- **Retake policy** (Databricks standard): 14-day wait after first failure, 14 days after second failure, longer cooldown after that. Full fee per attempt.
- No prerequisite is required; the exam guide notes course attendance + ~1 year hands-on in Databricks is "highly recommended."

## Recommended preparation (per official guide, Sept 2025)

- Instructor-led: **Machine Learning at Scale** + **Advanced Machine Learning Operations**.
- Self-paced equivalents in Databricks Academy carry the same names.
- The pre-2025 single course *Machine Learning in Production* was split into the two above as part of the Sept 2025 refresh.

## Exam structure — three sections (post-Sept 30 2025 refresh)

- **Section 1 — Model Development** ≈ 45% of scored items (community estimate).
- **Section 2 — MLOps** ≈ 43% of scored items.
- **Section 3 — Model Deployment** ≈ 12% of scored items.
- The prior **4-section structure** (Experimentation / Model Lifecycle / Model Deployment / Monitoring) was collapsed; Experimentation merged into Model Development and Monitoring merged into MLOps.
- The largest single subsection by objective count is **Drift Detection and Lakehouse Monitoring**, with **10 objectives** inside Section 2.

---

## MLflow facts

- The MLflow API for nested runs is **`mlflow.start_run(nested=True)`** inside an active parent run context.
- **Model signatures are required** to register a model in Unity Catalog. If not passed explicitly, infer with **`mlflow.models.infer_signature(X, y_pred)`** or registration fails.
- **Input examples** (`input_example=...` in `log_model`) are strongly recommended; they enable serving endpoint Test UI and auto-generate request schemas.
- A custom PyFunc model subclasses **`mlflow.pyfunc.PythonModel`** and implements two methods:
  - **`load_context(self, context)`** — called once at load time; load artifacts here.
  - **`predict(self, context, model_input)`** — called per request; must return a serializable result.
- One-shot register-on-log is **`mlflow.<flavor>.log_model(..., registered_model_name="<catalog>.<schema>.<name>")`**. Unity Catalog requires the full three-level namespace; two-level names target the legacy workspace registry.
- **Hyperopt / Optuna autologging logs each trial's params + metrics but does NOT log the best model** as a registered artifact. The winning model must be explicitly re-fit and `log_model`-ed.
- `mlflow.log_dict(d, "config.json")` logs a Python dict as a JSON artifact in one call.
- `mlflow.log_figure(fig, "shap.png")` logs a matplotlib Figure as an artifact.
- `mlflow.search_experiments(filter_string=...)` and `mlflow.search_runs(filter_string=..., order_by=[...])` are the canonical programmatic search APIs.

## Unity Catalog Model Registry facts

- UC model registry uses **aliases**, not stages. Canonical aliases referenced by the exam: **`@champion`**, **`@challenger`**, **`@archived`**.
- Set an alias via **`client.set_registered_model_alias(name, alias, version)`** where `client = mlflow.MlflowClient()`.
- Load by alias: **`mlflow.pyfunc.load_model("models:/<catalog>.<schema>.<name>@champion")`**.
- Load by explicit version: **`models:/<catalog>.<schema>.<name>/<version>`**.
- Tags on registered models and on model versions are key-value strings used for governance metadata (e.g., `team`, `pii_scope`, `validation_run_id`).
- **Stage transitions (`transition_model_version_stage(...)` with `None`/`Staging`/`Production`/`Archived`) are the LEGACY workspace registry API**; they remain in MLflow but are the wrong answer for UC questions on the exam.
- Webhooks via `/api/2.0/mlflow/registry-webhooks/create` remain in the platform; events include `MODEL_VERSION_CREATED` and `MODEL_VERSION_TRANSITIONED_STAGE`. The exam still tests them as an automation primitive even though the UC-native promotion path is alias-based.

---

## Drift detection — statistical test mapping (memorize)

| Test | Data type | Notes |
|---|---|---|
| **Kolmogorov-Smirnov (KS)** | Numerical / continuous | Two-sample distribution comparison; p-value-based |
| **Chi-square** | Categorical | Frequency-table comparison |
| **Jensen-Shannon (JS) divergence** | Categorical OR binned numerical | Symmetric KL; bounded in [0, log 2] |
| **Wasserstein (Earth Mover's) distance** | Numerical / continuous | Shape-sensitive distance |
| **Total Variation Distance (TVD)** | Categorical | Max-abs-difference of PMFs |

- **KS on categorical data is wrong.** **Chi-sq on continuous data is wrong** (unless binned first). The exam exploits this.
- **Concept drift (P(Y|X) shift) cannot be detected from features alone** — it requires labels. Any answer claiming concept drift is detected via KS/Chi-sq on input features is wrong.

## Drift type taxonomy

- **Feature drift / covariate shift:** P(X) changes; P(Y|X) unchanged. Detect on input columns.
- **Label drift / prior shift:** P(Y) changes. Requires ground-truth labels.
- **Prediction drift:** P(Ŷ) changes. Detect on model outputs in inference tables; available without labels — useful as an **early-warning signal**.
- **Concept drift:** P(Y|X) changes. Requires labels. Most damaging.

---

## Lakehouse Monitoring facts

- **Three monitor profile types:**
  - **Snapshot** — static / non-time-aware table; full table compared to baseline each run.
  - **TimeSeries** — table with a timestamp column; compares successive time windows.
  - **InferenceLog** — for inference-table-style data (predictions + optional joined labels); adds model performance metrics on top of drift.
- Lakehouse Monitoring writes two output Delta tables per monitor: **`<table>_profile_metrics`** and **`<table>_drift_metrics`**.
- The profile metrics table contains row-level descriptive stats per column (count, null rate, min, max, percentiles, distinct values).
- The drift metrics table contains the test statistic and p-value (where applicable) per column per slice per time window.
- **Slicing expressions** (`slicing_exprs=["region", "customer_tier"]`) compute metrics per slice — required for per-segment drift detection.
- **Custom metrics** (`MonitorCustomMetric`) can be added to the metrics table — e.g., per-segment F1 against joined labels.
- Alerts are configured by attaching a **Databricks SQL Alert** to a SQL query against the `_drift_metrics` table.
- **InferenceLog monitors are automatically created** when you enable an inference table on a Model Serving endpoint.

---

## Databricks Asset Bundles (DABs) facts

- A bundle is rooted in a **`databricks.yml`** file at the repo root.
- The CLI commands are **`databricks bundle validate`**, **`databricks bundle deploy -t <target>`**, **`databricks bundle run -t <target> <job_or_pipeline>`**, and **`databricks bundle destroy -t <target>`**.
- Bundle **resources** that the exam can ask you to declare:
  - `jobs` — Lakeflow Jobs (formerly Workflows).
  - `pipelines` — Lakeflow Declarative Pipelines (formerly DLT).
  - `experiments` — MLflow experiments.
  - `registered_models` — UC registered models with `catalog_name` + `schema_name`.
  - `model_serving_endpoints` — Mosaic AI Model Serving endpoints with `config` block (served entities + traffic).
  - `schemas` — UC schemas.
- Bundle **targets** (e.g., `dev`, `staging`, `prod`) declare workspace URL + environment-specific variable overrides.
- The `mode: development` target setting auto-prefixes resource names with the developer's username for isolation; `mode: production` requires explicit names and disallows ad-hoc edits.
- **Variables** (`variables:` block) parameterize bundle resources; reference via `${var.name}` or `${workspace.current_user.userName}`.
- **Permissions** can be set per-resource within the bundle (e.g., `permissions: [{level: CAN_MANAGE, user_name: ...}]`).

---

## Mosaic AI Model Serving facts

- An **endpoint** hosts one or more **served entities** (model versions or external endpoints).
- **`traffic_config.routes`** assigns percentages summing to 100 across served entities.
- **Canary deployment** = add a second served entity to the same endpoint and incrementally shift traffic (5% → 25% → 50% → 100%). Single endpoint, finer-grained, cheaper. **Preferred for high-traffic high-risk apps.**
- **Blue-green deployment** = either two endpoints (full DNS flip) or one endpoint with two served entities at 0%/100% then flipped 100%/0%. Instant rollback; double cost during cutover.
- **Shadow deployment** = route a copy of production traffic to the candidate without affecting user responses; compare offline.
- **Route Optimization** is a per-endpoint toggle that reduces network hops; improves throughput on high-QPS endpoints.
- **Scale-to-zero** is supported on CPU and small GPU endpoints; cold-start latency is the tradeoff.
- **Autoscale** is configured per served entity via `min_provisioned_throughput` / `max_provisioned_throughput` (provisioned-throughput PT mode) or `workload_size` (small/medium/large for CPU custom models).
- **Endpoint metrics surfaced for monitoring:** request rate, latency (**p50, p95, p99**), CPU usage, memory usage, error rate (HTTP 4xx, 5xx).
- **Inference tables** auto-log each request + response to a Delta table named `<catalog>.<schema>.<endpoint>_payload`.

---

## Feature Engineering in Unity Catalog facts

- The current client is **`from databricks.feature_engineering import FeatureEngineeringClient`** — instantiate as **`fe = FeatureEngineeringClient()`**.
- **`fe.create_table(name="cat.sch.tbl", primary_keys=["id"], timestamp_keys=["event_ts"], df=df)`** creates a feature table backed by Delta.
- **Point-in-time correctness** is enforced when a `FeatureLookup` includes both `lookup_key` and `timestamp_lookup_key`. This prevents using future feature values for past events — the canonical training/serving skew prevention pattern.
- **`fe.create_training_set(df=label_df, feature_lookups=[...], label="y")`** returns a training set object; call **`.load_df()`** to materialize a Spark DataFrame for training.
- **`fe.log_model(model, artifact_path=..., flavor=..., training_set=...)`** packages feature lookup metadata into the model. At inference time **`fe.score_batch(model_uri, df)`** auto-joins features by primary key.
- **Online tables** are UC-native, Databricks-managed serverless replicas of an offline feature table. They support sub-10ms reads and are required for real-time feature serving from a Model Serving endpoint.
- **On-demand features** are Python functions decorated with **`@feature_function`** that compute features at request time (e.g., distance from a user-supplied location). The same code runs at training and serving — eliminates training/serving skew.
- The legacy package **`databricks-feature-store`** with `FeatureStoreClient` is **deprecated** as of the FE-in-UC migration; the new package is **`databricks-feature-engineering`** (≥ 0.2.0).

---

## Optuna + Ray facts

- The MLflow integration callback is **`from optuna.integration.mlflow import MLflowCallback`**.
- Pass to `study.optimize(objective, n_trials=N, callbacks=[mlflow_callback])` to log each trial as a child run.
- **`MLflowSparkStudy`** (Optuna integration) distributes trials across the Spark cluster — the canonical answer for distributed Optuna on Databricks.
- Optuna samplers: **TPE** (default, Bayesian-style), **CmaEsSampler** (continuous), **RandomSampler**, **GridSampler**, **NSGAIISampler** (multi-objective).
- Optuna pruners: **MedianPruner**, **SuccessiveHalvingPruner**, **HyperbandPruner**, **PercentilePruner** — abandon unpromising trials early.
- **Ray on Databricks** provisions a Ray cluster on top of Spark workers via `ray.util.spark.setup_ray_cluster(...)`. Use **Ray Tune** for distributed PyTorch/TF training, RL, or search spaces Optuna can't express.
- Hyperopt + SparkTrials is the **legacy** answer on the new exam.

---

## PySpark scaling APIs

- **`applyInPandas`** — group-wise: `df.groupBy("k").applyInPandas(fn, schema=...)`. One DataFrame in (the group), one DataFrame out per group. Use for **group-specific model training** (one model per `store_id`).
- **`mapInPandas`** — partition-wise iterator API: function receives an iterator of pandas DataFrames, yields iterator of pandas DataFrames. Use for streaming-friendly batch inference.
- **`pandas_udf`** — Series-in, Series-out (scalar) or DataFrame-in, scalar-out (aggregate). Used for vectorized columnar UDFs.
- `mlflow.pyfunc.spark_udf(spark, model_uri)` returns a Spark UDF that applies the model to a DataFrame column — the **default batch inference pattern** in Databricks.

## Lakeflow Jobs facts (formerly Workflows)

- A Lakeflow Job is a DAG of **tasks**; each task has dependencies declared via `depends_on:`.
- Each task can run on a **job cluster** (ephemeral, cheaper, isolated) or an existing all-purpose cluster (more expensive, shared).
- **Repair runs** allow re-execution of failed tasks only, preserving successful task outputs and skipping retries on already-completed work.
- ML pipelines on Databricks express training, evaluation, registration, deployment, and monitoring as separate Lakeflow Job tasks with explicit dependencies.

---

## CI/CD pattern (deploy-code strategy)

- **Deploy-code strategy** = the source code that produces the model is what gets promoted across environments, not the model artifact itself. Each environment re-trains (or re-validates) from controlled code.
- This is the **exam-correct architecture** for regulated industries. Contrast with deploy-model strategy where a single artifact is promoted across envs — less auditable but cheaper to operate.
- Canonical pattern: `dev branch → DAB deploy to dev workspace → PR → CI tests + DAB deploy to staging → manual gate → DAB deploy to prod → set @champion alias`.

---

## Common pitfalls (memorize)

- Concept drift cannot be detected from features alone — requires labels.
- KS on categorical data is wrong; Chi-sq on continuous data is wrong.
- Hyperopt/Optuna autologging does NOT register the best model — manual re-fit + log_model required.
- `FeatureStoreClient` is the legacy answer; `FeatureEngineeringClient` is correct.
- `transition_model_version_stage` is the legacy answer for UC; aliases are correct.
- Online Tables (UC-native) ≠ Online Stores (deprecated DynamoDB/Cosmos backend).
- Without a model signature, UC registration fails — answers that omit it are distractors.
- "Set 100% traffic to new model immediately" is wrong for high-risk canary scenarios — incremental shift is correct.
- `applyInPandas` (group-wise) ≠ `pandas_udf` (column-wise) — choose by data shape, not familiarity.

---

## Sources (re-verify any time before using)

- **Official Databricks Certified ML Professional Exam Guide**, September 30 2025 — `/Users/vr/Code/Career_upskill/research_inputs/11_databricks_ml_professional/databricks_ml_professional_exam_guide.pdf`.
- [Databricks Certification — ML Professional landing page](https://www.databricks.com/learn/certification/machine-learning-professional)
- [MLflow Python API — mlflow.pyfunc](https://mlflow.org/docs/latest/python_api/mlflow.pyfunc.html)
- [Databricks Asset Bundles documentation](https://docs.databricks.com/aws/en/dev-tools/bundles/)
- [Lakehouse Monitoring overview](https://docs.databricks.com/aws/en/lakehouse-monitoring/index.html)
- [Mosaic AI Model Serving — custom models](https://docs.databricks.com/aws/en/machine-learning/model-serving/custom-models)
- [Feature Engineering in Unity Catalog](https://docs.databricks.com/aws/en/machine-learning/feature-store/uc/ui-uc)
- [Databricks Feature Store deprecation notes](https://docs.databricks.com/aws/en/release-notes/feature-store/databricks-feature-store)
- [Optuna MLflow callback documentation](https://optuna-integration.readthedocs.io/en/latest/reference/generated/optuna_integration.MLflowCallback.html)

**Re-verify before:** scheduling the exam, citing a number in a planning doc, or recommending an API in a code review. Databricks ships fast; the cert refreshes roughly yearly.
