# Topic 09 — Databricks Certified Machine Learning Associate

> **Audience:** Senior AI/ML Engineer (10+ yrs Python/PySpark) preparing for the **Databricks Certified Machine Learning Associate** exam. You already know how to build ML systems — this corpus is the *Databricks-specific* layer you need to clear the exam in two weeks of focused study.
>
> **Goal:** Pass the exam in one attempt with a margin (target 80%+ on practice), and walk away with the operational vocabulary of Databricks ML — Unity Catalog Feature Engineering, MLflow tracking + UC Registry aliases, Spark ML pipelines, Hyperopt-vs-Optuna pragmatics, batch/streaming/realtime serving patterns.
>
> **Last updated:** 2026-05-23

---

## What this topic guarantees

This corpus is built to a completeness standard, not a length standard. Every verbatim exam objective in the **March 1, 2025 official exam guide** is mapped to a specific section in a specific module via a "Coverage map" header at the top of each module file. For each objective, you'll find:

1. The **full API surface** the exam may test (every parameter, not just the popular ones).
2. **Look-alike API comparison tables** — pairs of APIs that look similar but differ (e.g., `set_registered_model_alias` vs `set_model_version_tag`, `BinaryClassificationEvaluator` vs `MulticlassClassificationEvaluator`).
3. **Worked exam-question walkthroughs** — 3-5 per module, including the verbatim official sample questions (Q1-Q5).
4. **Output prediction drills** — "given this code, what does it return?" because the exam tests this constantly.
5. **Decision rules** in `🎯 How to recognize this on the exam` callouts.
6. **End-to-end mini-scenarios** showing the module's APIs in realistic combination.
7. **Common wrong-answer traps** explicitly enumerated.

**Promise:** If you read every module + take every quiz, you have everything tested on the exam. There is no hidden chapter, no "you should also know X" gap. The Coverage maps make this auditable — point to any exam objective, and the map tells you which section teaches it.

If you find an objective in the official PDF that has no module section behind it, that's a bug — file an issue.

---

## Exam at a glance

| Item | Value |
|------|-------|
| **Exam version (current)** | March 1, 2025 revision |
| **Question count** | 48 (multiple-choice + occasional multi-select) |
| **Duration** | 90 minutes |
| **Passing score** | ~70% (Databricks does not officially publish, scaled) |
| **Cost** | $200 USD per attempt + tax |
| **Retake wait** | 14 days between attempts (Nov 1, 2023 policy) |
| **Validity** | 2 years |
| **Delivery** | Online proctored via Kryterion WebAssessor |
| **Test aides** | None — no scratch paper, no calculator, no notes |
| **Code language** | All ML code in Python; SQL may appear for data manipulation |
| **Prerequisites** | None required; 6+ months hands-on Databricks ML recommended |

**Per-question budget:** 90 min ÷ 48 Q = **1m 52s per question.** Practice with a timer.

> ⚠️ **Watch the exam version.** This corpus targets the March 1, 2025 guide, which still tests **Hyperopt's `fmin`** even though Hyperopt is removed from Databricks Runtime ML 17+. A future guide revision (expected late 2026) will likely drop Hyperopt and add MLflow 3 features. Re-check the official exam guide PDF ~2 weeks before your exam date.

---

## Domain weights and module map

| Domain | Weight | Approx Qs | Modules |
|--------|-------:|----------:|---------|
| 1. Databricks Machine Learning | **38%** | ~18 | [01](01_databricks_ml_platform.md), [02](02_automl_2026.md), [03](03_feature_engineering_uc.md), [04](04_mlflow_tracking_basics.md), [05](05_uc_model_registry.md) |
| 2. ML Workflows / Data Processing | **19%** | ~9 | [06](06_data_prep_with_spark.md), [07](07_pandas_api_on_spark.md), [08](08_feature_engineering_techniques.md) |
| 3. Model Development | **31%** | ~15 | [09](09_spark_ml_algorithms.md), [10](10_hyperopt_legacy.md), [11](11_optuna_modern.md), [12](12_cross_validation_metrics.md) |
| 4. Model Deployment | **12%** | ~6 | [13](13_batch_streaming_inference.md), [14](14_real_time_serving_basics.md) |

> **Note:** Domain 1 is **the biggest single domain.** Master Feature Engineering Client, MLflow tracking, UC Registry aliases, and AutoML — together they're 38% of your grade.

---

## Learning path — 14 modules

| # | Module | What it covers |
|---|--------|----------------|
| **Domain 1 — Databricks ML (38%)** | | |
| 1 | [Databricks ML platform & runtime](01_databricks_ml_platform.md) | DBR ML runtime, GPU runtimes, workspace anatomy, cluster types for ML, what "ML runtime advantages" means on the exam |
| 2 | [AutoML in 2026](02_automl_2026.md) | UI + API, glass-box generated notebooks, MLflow integration, when to use vs not |
| 3 | [Feature Engineering in Unity Catalog](03_feature_engineering_uc.md) | `FeatureEngineeringClient`, UC feature tables, training sets, point-in-time, online tables — HIGH YIELD |
| 4 | [MLflow tracking basics](04_mlflow_tracking_basics.md) | Runs, experiments, params/metrics/artifacts, autologging per flavor, `MlflowClient` API |
| 5 | [Unity Catalog Model Registry](05_uc_model_registry.md) | Registered models in UC, **aliases** (`@champion`, `@challenger`), tags, deprecation of legacy stages |
| **Domain 2 — Data Processing / ML Workflows (19%)** | | |
| 6 | [Data prep with Spark DataFrames](06_data_prep_with_spark.md) | `.summary()`, outlier removal (std-dev / IQR), missing-value imputation, train/val/test split |
| 7 | [Pandas API on Spark](07_pandas_api_on_spark.md) | `pyspark.pandas`, when to use it vs pandas vs Spark DataFrame, gotchas |
| 8 | [Feature engineering techniques](08_feature_engineering_techniques.md) | `StringIndexer`, `OneHotEncoder`, `VectorAssembler`, `Imputer`, log scale, when NOT to OHE |
| **Domain 3 — Model Development (31%)** | | |
| 9 | [Spark ML algorithms](09_spark_ml_algorithms.md) | `RandomForestClassifier`, `GBTRegressor`, `LogisticRegression`, `LinearRegression`, `KMeans`, estimators vs transformers |
| 10 | [Hyperopt (legacy but still on exam)](10_hyperopt_legacy.md) | `fmin`, `hp.choice`/`uniform`/`loguniform`, `tpe.suggest`, `SparkTrials`, parallelism |
| 11 | [Optuna (modern replacement)](11_optuna_modern.md) | Studies, trials, `suggest_*`, MLflow integration, joblib/Ray parallelism |
| 12 | [Cross-validation, grid search, metrics](12_cross_validation_metrics.md) | `CrossValidator` vs `TrainValidationSplit`, `ParamGridBuilder`, evaluators, the "models trained" math |
| **Domain 4 — Model Deployment (12%)** | | |
| 13 | [Batch & streaming inference](13_batch_streaming_inference.md) | `mlflow.pyfunc.spark_udf`, batch scoring patterns, streaming via DLT, Spark ML transform vs sklearn loaded |
| 14 | [Real-time serving basics](14_real_time_serving_basics.md) | Mosaic AI Model Serving endpoints, served entities, traffic split — just what the exam tests |

---

## Companion files

- [`FACTS.md`](FACTS.md) — atomic, citable claims with "Last verified" dates. Exam logistics, API names, version cutoffs, current vs deprecated APIs. **Cross-reference this whenever you want a number or an API signature.**
- [`quizzes/`](quizzes/) — 5 quiz files, ~145 questions total (≈ 3× exam length).
  - [`quizzes/01_databricks_ml.md`](quizzes/01_databricks_ml.md) — ~55 Qs (Domain 1, 38%)
  - [`quizzes/02_ml_workflows.md`](quizzes/02_ml_workflows.md) — ~28 Qs (Domain 2, 19%)
  - [`quizzes/03_model_development.md`](quizzes/03_model_development.md) — ~45 Qs (Domain 3, 31%)
  - [`quizzes/04_model_deployment.md`](quizzes/04_model_deployment.md) — ~17 Qs (Domain 4, 12%)
  - [`quizzes/README.md`](quizzes/README.md) — how to score, what 70% looks like, weak-area drill plan

---

## How to use this topic

### Study order (recommended 2-week part-time plan, ~35-40 hours)

1. **Day 1 — Calibration.** Read this README + skim `FACTS.md`. Skim the official PDF in [`../../research_inputs/09_databricks_ml_associate/exam_guide_excerpt.md`](../../research_inputs/09_databricks_ml_associate/exam_guide_excerpt.md). Don't take any quizzes yet.
2. **Days 2-4 — Domain 1 (the biggest).** Read modules 01 → 05 in order. Take quiz `01_databricks_ml.md` cold at the end.
3. **Days 5-6 — Domain 2.** Modules 06 → 08, then quiz `02_ml_workflows.md`.
4. **Days 7-9 — Domain 3 (second biggest).** Modules 09 → 12. Hyperopt (10) and Optuna (11) are paired — read together; the exam tests Hyperopt explicitly but you should know both. Then quiz `03_model_development.md`.
5. **Day 10 — Domain 4.** Modules 13 → 14, then quiz `04_model_deployment.md`.
6. **Day 11 — Full-length timed practice.** Re-take all four quizzes back-to-back in 90 minutes (treat as exam dress rehearsal). Score yourself.
7. **Days 12-13 — Targeted review.** Re-read modules covering your weakest 1-2 domains. Re-do failed questions.
8. **Day 14 — Exam day.** Skim `FACTS.md` in the morning. Don't cram new material. Take the exam.

### Quiz discipline

- **Take quizzes cold** — no peeking at modules, no Google. Treat each like the real exam.
- **Time yourself** at ~1m 52s per question. The exam's biggest killer is time pressure, not difficulty.
- **Read every answer explanation, even on questions you got right.** The explanation often surfaces a trap you happened to avoid.
- **Re-take failed quizzes 48 hours later.** Memory consolidation matters more than first-pass score.

### What you should be able to do after this corpus

- Explain UC Feature Tables vs workspace Feature Store, and name the client class for each (`FeatureEngineeringClient` vs deprecated `FeatureStoreClient`).
- Promote a model from `@challenger` to `@champion` in the UC registry using `MlflowClient.set_registered_model_alias`.
- Calculate total model fits for a grid search × k-fold CV setup in your head.
- Read a code stub and identify whether it's using Hyperopt, Optuna, or Spark ML's `CrossValidator`.
- Choose between batch inference (Spark UDF), streaming inference (DLT), and real-time inference (Model Serving endpoint) given a latency/throughput spec.
- Recognize the difference between online and offline feature tables and when each is required.
- Explain why one-hot encoding is **not** required for tree-based models but **is** required for linear/distance/NN models.
- Know when to use median vs mean vs mode imputation based on distribution shape.
- Identify the correct MLflow flavor + autologging defaults for sklearn, Spark ML, XGBoost, and PyTorch.

---

## Scope notes & biases

- **Cutoff:** Content reflects the **March 1, 2025 exam guide** and Databricks platform state as of **2026-05-23**. Re-verify the exam guide URL before your exam.
- **Bias toward the exam, not the platform.** Real Databricks ML production uses MLflow 3.0, Mosaic AI Agent Framework, and Optuna. The exam still tests MLflow 2.x patterns, UC Registry aliases, and Hyperopt. We teach the **exam-relevant** version explicitly and call out the modern version as context.
- **No NDA violations.** All practice questions are original, derived from public exam objectives and patterns surfaced in the research — never from real exam content.
- **Code conventions.** All code blocks use PySpark / MLflow Python API / SQL. We use `catalog.schema.table` three-level namespaces consistently. No legacy `dbfs:/` paths.

---

## Stack baseline (additions to project `.venv`)

```
pyspark>=3.5             # local Spark for offline practice
delta-spark              # local Delta tables
mlflow>=2.15,<3          # exam tests 2.x API surface
databricks-feature-engineering  # FeatureEngineeringClient
hyperopt                 # legacy but exam-tested
optuna                   # modern replacement
scikit-learn
xgboost
pandas
```

> If you have a Databricks workspace (Free Edition or employer-provided), run the code snippets there for the highest-fidelity practice. Local Spark is fine for ~80% of the module code but doesn't cover UC Feature Engineering, Model Serving endpoints, or AutoML — those require a workspace.

---

## Research provenance

This corpus is built from the research report at [`../../research_inputs/09_databricks_ml_associate/RESEARCH.md`](../../research_inputs/09_databricks_ml_associate/RESEARCH.md), the official exam guide PDF, the domain breakdown at [`domain_breakdown.md`](../../research_inputs/09_databricks_ml_associate/domain_breakdown.md), and the verbatim objectives at [`exam_guide_excerpt.md`](../../research_inputs/09_databricks_ml_associate/exam_guide_excerpt.md). Cross-references to Topic 02 (Azure Databricks) appear where the platform foundations overlap with the exam-tested ML stack.
