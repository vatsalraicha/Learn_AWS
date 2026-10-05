# Topic 11 — Databricks Certified Machine Learning Professional

> **Audience:** Sr AI/ML Engineer (Vatsal — Optum, 10+ yrs Python/PySpark). **Assumes you have already worked through [Topic 09 — Databricks ML Associate](../09_databricks_ml_associate/README.md).** This Pro cert builds directly on Associate knowledge: Spark ML basics, MLflow tracking 101, AutoML, AVF, Hyperopt-as-historical-context, registry stages-as-historical-context.
>
> **Goal:** Pass the **Databricks Certified Machine Learning Professional** exam (Sept 30 2025 refresh — three sections, MLOps-heavy) and, more importantly, be the person at Optum/Capital One/any regulated-data shop who actually runs ML in production on Databricks the way the platform team intends.
>
> **Last updated:** 2026-05-23

---

## What this topic guarantees

If you read all 16 modules in this corpus and can answer the **mini-quiz, output-prediction drill, and decision-rule** questions for each module from memory, you will have direct coverage of **every verbatim objective from the September 30, 2025 exam guide**. Each module begins with a **Coverage map** that maps the objectives it owns to the section anchors that teach them — use it to verify you're not skipping anything.

**This corpus is sufficient prep on its own** for an experienced ML engineer (Topic 09 Associate-level baseline assumed). External resources are useful for reinforcement, but the modules here are designed so a reader who studies only this material + the quizzes is genuinely ready to sit the exam.

Specifically, every module contains:
- **Coverage map** — verbatim Sept 30 2025 objectives → section anchors in the module.
- **Full API surface** — method signatures + parameter tables for the APIs the exam grills.
- **Look-alike comparison tables** — the API pairs the exam uses as distractors (e.g., `FeatureStoreClient` vs `FeatureEngineeringClient`, `transition_model_version_stage` vs `set_registered_model_alias`, `served_models` vs `served_entities`).
- **Worked walkthroughs** — production-shape code with the exam-tested patterns.
- **Output-prediction drills** — given a snippet, predict what runs / fails / gets logged.
- **Decision rules** — `> 🎯 **How to recognize on the exam:** ...` callouts that match prompt phrasing to the right API.
- **End-to-end mini-scenarios** — full pipelines that combine the module's APIs with adjacent modules.
- **Mini quiz + sanity check** — 6–10 questions with explained answers.

Heaviest-weighted modules: **10 (Lakehouse Monitoring — 10 objectives)**, **08 (DABs)**, **11 (Drift detection statistics)**, **07 (UC model registry — alias vs stages)**. Read them twice.

---

## Exam logistics

| Field | Value |
|---|---|
| Items (scored) | **59 multiple-choice** + a small number of unscored, unidentified |
| Time | **120 minutes** |
| Registration fee | **USD $200** (+ local tax) |
| Passing score | **70%** (community-confirmed; not on official PDF) |
| Delivery | Online proctored only (Webassessor / Kryterion) |
| Validity | **2 years**, must retake current live exam to renew |
| Retake policy | 14-day wait after first fail, 14 days after second, longer after that. Pay full fee each attempt |
| Test aides | **None allowed** |
| Prerequisite | None. ML Associate is **not required** but is the de-facto baseline |

**Recommended prep (verbatim from the official guide):**
- Instructor-led: *Machine Learning at Scale* + *Advanced Machine Learning Operations*
- Self-paced (Databricks Academy): same two courses
- Working knowledge of Python, scikit-learn, SparkML, MLflow
- Working knowledge of **Lakehouse Monitoring** and **Mosaic AI Model Serving**

The pre-2025 single course *Machine Learning in Production* has been split into the two courses above.

---

## What changed in the Sept 30 2025 refresh — read this first

> If you studied this cert before Sept 2025, **roughly 30% of what you memorized is now wrong or deprecated**. Skim this table before anything else.

| Change | Old (pre-Sept 2025) | New (Sept 2025 refresh) |
|---|---|---|
| Section count | 4 (Experimentation / Lifecycle / Deployment / Monitoring) | **3** (Model Development / MLOps / Model Deployment) |
| Section weights | Roughly balanced | **~45% Dev / ~43% MLOps / ~12% Deploy** |
| Tuner of record | **Hyperopt** + SparkTrials | **Optuna** + MLflowCallback + MLflowSparkStudy. **Ray** is also explicit |
| Promotion mechanism | Stage transitions (`None`/`Staging`/`Production`/`Archived`) | **UC aliases** — `@champion`, `@challenger`, `@archived`. Stages = legacy answer |
| Feature platform | `databricks-feature-store` + `FeatureStoreClient` | **`databricks-feature-engineering`** + **`FeatureEngineeringClient`**. Old pkg deprecated |
| Infra as code | Terraform-only / mostly absent | **DABs (Databricks Asset Bundles)** — heavy emphasis, brand new objectives |
| Drift | Ad-hoc Spark code | **Lakehouse Monitoring** with named tests (KS, Chi-sq, JS, Wasserstein, TVD) |
| Deployment | Generic "endpoints" | **Blue-green and canary by name**, served entities + traffic config, Route Optimization, shadow |
| Online serving feature store | "Online Stores" (DynamoDB/Cosmos) | **Online Tables** (UC-native, serverless) |
| MLflow assumptions | 2.x | **3.x** — UC three-level namespace, signatures required for registration |
| Webhooks | Central to promotion | Still tested as concept but **alias + Jobs gate is the new canonical answer** |

⚠️ **Distractor pattern:** wrong choices on the new exam disproportionately come from the *old* APIs (`FeatureStoreClient`, `transition_model_version_stage`, `SparkTrials`, "Online Stores"). If an answer looks "right from 2023," it's probably the wrong answer on the 2025 exam.

---

## Domain weight table

Databricks does not publish exact percentages on the Sept 2025 PDF. Community cross-verification yields:

| # | Section | Approx weight | Objective count | Trend vs Apr 2024 |
|---|---|---|---|---|
| 1 | **Model Development** | ~45% | ~22 objectives | UP (absorbs old "Experimentation") |
| 2 | **MLOps** | ~43% | ~24 objectives (largest) | UP heavily (DABs, monitoring new) |
| 3 | **Model Deployment** | ~12% | ~6 objectives | DOWN (but deep scenarios) |

Largest single subsection: **Drift / Lakehouse Monitoring (10 objectives)** inside Section 2. Plan your study time around it — see Module 10.

---

## Learning path — 16 modules

| # | Module | Why it matters |
|---|---|---|
| **Section 1 — Model Development (~45%)** | | |
| 01 | [Advanced MLflow tracking](01_advanced_mlflow_tracking.md) | Nested runs, custom artifacts, signatures, input examples, search experiments, autolog gotchas |
| 02 | [Custom PyFunc models](02_custom_pyfunc_models.md) | `mlflow.pyfunc.PythonModel`, `load_context`, dependency packaging, real-time feature lookups |
| 03 | [Optuna + Ray distributed tuning](03_optuna_advanced.md) | Samplers, pruners, MLflowCallback, MLflowSparkStudy, Ray Tune, multi-objective. **Hyperopt is out.** |
| 04 | [Feature Engineering in UC — deep](04_feature_engineering_uc_deep.md) | `FeatureEngineeringClient`, point-in-time lookups, online tables, on-demand features, streaming features |
| 05 | [Advanced Spark ML](05_advanced_spark_ml.md) | Pipelines, custom transformers/estimators, CrossValidator parallelism, evaluators |
| 06 | [Ensembles & stacking via PyFunc](06_ensembles_stacking.md) | Voting/stacking custom models, multi-model ensembles, per-request routing logic |
| **Section 2 — MLOps (~43%) — biggest section, slow read** | | |
| 07 | [UC model registry lifecycle](07_uc_model_registry_lifecycle.md) | Registered models, versions, aliases (@champion/@challenger), tags, transitions, webhook concept |
| 08 | [Databricks Asset Bundles for ML](08_dabs_for_ml.md) | `databricks.yml`, resources, targets, ML jobs + endpoints + models as bundle resources. **New, heavy** |
| 09 | [CI/CD with DABs + GitHub Actions](09_ci_cd_with_dabs.md) | Bundle deploy on PR merge, env promotion (dev→staging→prod), gated promotion patterns |
| 10 | [Lakehouse Monitoring — deep](10_lakehouse_monitoring_deep.md) | Snapshot / TimeSeries / InferenceLog monitors, profile + drift tables, custom metrics, slicing. **Largest module, 10 objectives** |
| 11 | [Drift detection deep](11_drift_detection.md) | Feature / label / prediction / concept drift; KS / Chi-sq / JS / Wasserstein selection; alerting; retraining triggers |
| 12 | [Model governance in UC](12_model_governance.md) | Permissions on models, lineage (model→table), tags, approval workflows, deploy-code strategy |
| 13 | [Inference tables](13_inference_tables.md) | Auto-logging requests + responses on serving endpoints, joining feedback labels, foundation for monitoring |
| **Section 3 — Model Deployment (~12%)** | | |
| 14 | [Serving: blue-green & canary](14_serving_blue_green_canary.md) | Served entities, traffic config, canary 90/10, blue-green via traffic rebalance, scale-to-zero, autoscale |
| 15 | [Batch & streaming serving](15_batch_streaming_serving.md) | `mlflow.pyfunc.spark_udf`, Lakeflow Jobs for batch, Structured Streaming inference |
| 16 | [Serving observability](16_serving_observability.md) | Endpoint metrics, p50/p95/p99 latency, error rates, request logging, debugging |

## Companion files

- [`FACTS.md`](FACTS.md) — atomic citable claims. Exam logistics, drift test mappings, alias semantics, DABs CLI, monitor types. Updated whenever a number gets caught stale.
- [`quizzes/`](quizzes/) — ~177 practice questions (59 × 3 sittings worth), split by section weight.
- Cross-links to [Topic 09 — Databricks ML Associate](../09_databricks_ml_associate/README.md) for prerequisites and to [Topic 02 — Azure Databricks](../02_azure_databricks/README.md) for platform-level depth (Unity Catalog, MLflow 3, Mosaic AI Serving, DABs).

## How to use this corpus

1. **Take a baseline cold quiz** from `quizzes/01_model_development.md` (just the Recall section) before reading anything. Note what you don't know — that's your honest starting point.
2. Read modules **01 → 06** for Section 1. If you've shipped MLflow + Spark ML for years, much of this is fast review; **slow down on PyFunc (02) and Optuna (03) — both have changed**.
3. Read modules **07 → 13** for Section 2. **This is where points live.** Module 10 (Lakehouse Monitoring) deserves two passes.
4. Read modules **14 → 16** for Section 3. Shorter section but deep scenarios.
5. Take each section's quiz cold. Score below 80% → re-read the relevant module.
6. Final week: re-read the 8 sample questions in the official PDF and explain each answer in your own words.

Each module ends with a **Sanity check** — 3–5 questions you should answer in your head before moving on.

## Scope notes

- **Cutoff:** content reflects the **September 30 2025** exam guide and **MLflow 3.x** + **`databricks-feature-engineering` ≥ 0.2.0**. The cert refreshes roughly yearly; re-verify before scheduling.
- **NDA discipline:** every quiz question in this folder is **original**. No leaked / dumped / verbatim exam content. We test the same objectives the exam tests, not the same wording.
- **Stack convention:** PySpark / scikit-learn / MLflow / UC three-level names. Anthropic-style LLMs only where relevant (Module 02 ensemble examples). No OpenAI imports.
- **Lens:** healthcare-regulated context where it sharpens an answer (e.g., why `@champion` alias + audit trail > stage transitions for HIPAA workflows). Not heavy-handed.

## Stack baseline (additions to project `.venv`)

```
databricks-sdk          # latest
databricks-cli          # >=0.218 (for `databricks bundle ...`)
mlflow                  # >=3.0
databricks-feature-engineering  # >=0.2.0 — NOT databricks-feature-store
optuna                  # >=3.5
optuna-integration      # MLflowCallback + Ray
ray[tune]               # >=2.10 — distributed HP search
scikit-learn
pyspark                 # matches DBR version on cluster
pytest
```

## Cross-references

- **[Topic 02 — Azure Databricks](../02_azure_databricks/README.md)** — platform foundations. Module 09 (Unity Catalog), Module 12 (MLflow 3 deep), Module 14 (Model Serving + AI Gateway), Module 19 (CI/CD with DABs).
- **[Topic 09 — Databricks ML Associate](../09_databricks_ml_associate/README.md)** — the prerequisite. AutoML, Hyperopt (legacy), Feature Store 1.0 (legacy), workspace registry stages (legacy).
- **[Topic 10 — Databricks GenAI Associate](../10_databricks_genai_associate/README.md)** — sister cert, GenAI-focused. Useful background but **does not overlap** with ML Pro objectives.

---

**Next step:** open [`FACTS.md`](FACTS.md) for the single-source-of-truth numbers, then start [Module 01](01_advanced_mlflow_tracking.md).
