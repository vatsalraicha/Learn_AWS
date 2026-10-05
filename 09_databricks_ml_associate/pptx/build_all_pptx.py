#!/usr/bin/env python3
"""
Build study-deck PPTX for all 5 Databricks cert topics (09-13).

Writes per-topic build_deck.py (regenerable) AND the final .pptx file.
Each deck: ~25-30 slides with title, exam blueprint, per-domain overview,
look-alike traps, key facts, pitfalls, study plan, resources, final reminder.
"""
import json
import sys
from pathlib import Path

ROOT = Path("/Users/vr/Code/Career_upskill")
TOPICS = ROOT / "topics"

# ── Per-topic deck content ──────────────────────────────────────────────────
DECKS = {
    "09_databricks_ml_associate": {
        "slug": "Databricks_ML_Associate",
        "cert_name": "Databricks Certified Machine Learning Associate",
        "exam_version": "March 1, 2025",
        "logistics": {
            "Question count": "48 scored (multiple-choice, occasional multi-select)",
            "Duration": "90 minutes (~1m 52s / question)",
            "Passing score": "~70% (not officially published)",
            "Cost": "$200 USD + tax",
            "Validity": "2 years",
            "Retake wait": "14 days between attempts",
            "Delivery": "Online proctored (Kryterion WebAssessor)",
            "Code language": "Python (SQL may appear for data manipulation)",
        },
        "domains": [
            ("Domain 1 — Databricks Machine Learning", "38%", [
                "DBR ML runtime, GPU runtimes, cluster types",
                "AutoML UI + API, glass-box generated notebooks",
                "Feature Engineering in UC (FeatureEngineeringClient, FeatureLookup)",
                "MLflow tracking: runs, autologging per flavor, MlflowClient",
                "UC Model Registry: aliases (@champion/@challenger), tags, set_registry_uri('databricks-uc')",
            ]),
            ("Domain 2 — ML Workflows / Data Processing", "19%", [
                "Spark DataFrame .summary(), outlier removal (std-dev / IQR)",
                "Missing-value imputation (mean / median / mode by shape)",
                "Pandas API on Spark (pyspark.pandas) — when to use vs pandas vs Spark DF",
                "StringIndexer, OneHotEncoder, VectorAssembler, Imputer",
                "When NOT to OHE (tree-based models don't need it)",
            ]),
            ("Domain 3 — Model Development", "31%", [
                "RandomForestClassifier, GBTRegressor, LogisticRegression, KMeans",
                "Estimators vs transformers — pattern recognition",
                "Hyperopt fmin, hp.choice (returns INDEX!), tpe.suggest, SparkTrials",
                "Optuna create_study, trial.suggest_*, n_jobs (no SparkTrials equivalent)",
                "CrossValidator vs TrainValidationSplit, ParamGridBuilder",
                "Total fits math: |grid| × k folds × (+1 final refit)",
            ]),
            ("Domain 4 — Model Deployment", "12%", [
                "mlflow.pyfunc.spark_udf for batch scoring",
                "Streaming inference via DLT",
                "Mosaic AI Model Serving: endpoints, served entities, traffic split",
                "Choose batch vs streaming vs real-time by latency/throughput",
            ]),
        ],
        "lookalikes": [
            ("hp.choice", "Returns the INDEX (int), NOT the value — wrap result if you want the actual choice"),
            ("set_registered_model_alias", "Sets @alias — multi-version, multi-alias allowed"),
            ("set_model_version_tag", "Per-version key/value metadata — does NOT promote"),
            ("FeatureEngineeringClient (UC)", "create_table — Unity Catalog-native — current API"),
            ("FeatureStoreClient (workspace)", "register_table — DEPRECATED since 0.17.0"),
            ("CrossValidator", "k-fold; trains numFolds × |grid| + 1 models"),
            ("TrainValidationSplit", "Single holdout; trains |grid| + 1 models"),
            ("BinaryClassificationEvaluator", "AUC, areaUnderROC, areaUnderPR"),
            ("MulticlassClassificationEvaluator", "f1, accuracy, weightedPrecision/Recall"),
            ("@champion (UC alias)", "Replaces 'Production' stage; resolve via models:/cat.sch.mdl@champion"),
            ("None → Staging → Production → Archived", "LEGACY workspace registry — deprecated"),
        ],
        "facts_to_memorize": [
            "MLflow registry URI for UC: mlflow.set_registry_uri('databricks-uc')",
            "Three-level namespace: catalog.schema.model — required for UC",
            "Hyperopt removed from DBR ML 17+; last shipped in 16.4 LTS (May 2025)",
            "Hyperopt STILL on the March 1 2025 exam — know fmin, hp.*, tpe.suggest, SparkTrials",
            "Optuna parallelism: n_jobs (joblib) — there is NO SparkTrials equivalent",
            "AutoML generates glass-box notebooks — you can edit them",
            "Tree-based models do NOT need OneHotEncoding; linear/distance/NN models DO",
            "Median imputation for skewed; mean for symmetric; mode for categorical",
            "Mosaic AI Model Serving — 'served entities' replaces 'served models' terminology",
        ],
        "pitfalls": [
            "hp.choice returns INDEX — easy 1-point loss if you forget",
            "Forgetting mlflow.set_registry_uri('databricks-uc') writes to workspace registry instead",
            "Confusing CrossValidator's 'trains numFolds models' (it trains numFolds × |grid| + 1)",
            "Using FeatureStoreClient instead of FeatureEngineeringClient in new code",
            "Assuming Hyperopt is gone — it's still tested on March 1, 2025 guide",
            "Using legacy stages (Staging/Production) instead of UC aliases",
            "Confusing pyspark.pandas (Pandas API on Spark) with pandas-on-databricks",
            "Forgetting that XGBoost/sklearn flavors autolog parameters but NOT the full best model from hyperopt",
        ],
        "study_weeks": [
            ("Week 1", "Domain 1 (38%) — modules 01-05; quiz 01"),
            ("Week 2", "Domains 2+3 — modules 06-12; quizzes 02-03"),
            ("Week 3", "Domain 4 — modules 13-14; quiz 04; FACTS.md skim; book exam"),
            ("Exam week", "Full-length timed practice + targeted weakness review"),
        ],
        "resources": [
            "Official exam guide PDF (March 1, 2025): databricks.com/sites/default/files/2025-02/databricks-certified-machine-learning-associate-exam-guide-1-mar-2025.pdf",
            "Databricks Academy: Machine Learning Associate self-paced",
            "Career_upskill Topic 09 modules 01-14 + 4 quizzes (~145 Qs, 3× exam length)",
            "FACTS.md — atomic facts with last-verified dates",
            "Verify exam guide URL 2 weeks before exam date",
        ],
    },
    "10_databricks_genai_associate": {
        "slug": "Databricks_GenAI_Associate",
        "cert_name": "Databricks Certified Generative AI Engineer Associate",
        "exam_version": "March 18, 2026",
        "logistics": {
            "Question count": "45 scored (multi-choice + multi-select: 'Select TWO/THREE')",
            "Duration": "90 minutes (~2 min / question)",
            "Passing score": "~70% (≈ 32/45) [community]",
            "Cost": "$200 USD + tax",
            "Validity": "2 years",
            "Retake wait": "~14 days [community]",
            "Delivery": "Online proctored (Kryterion WebAssessor)",
            "Languages": "English, JP, BR-PT, KR",
        },
        "domains": [
            ("Domain 1 — Design Applications", "14%", [
                "Use case framing: when GenAI vs classical ML",
                "RAG vs fine-tuning vs prompting tradeoffs",
                "Choosing chunk strategy by document type",
                "Latency / cost / quality tradeoffs",
            ]),
            ("Domain 2 — Data Preparation", "14%", [
                "Chunking strategies: fixed, semantic, recursive, document-aware",
                "Embedding model selection (BGE, E5, OpenAI, Databricks GTE)",
                "Vector index types: Delta Sync (auto-update) vs Direct Access",
                "Mosaic AI Vector Search hybrid retrieval (vector + keyword)",
            ]),
            ("Domain 3 — Application Development", "30%", [
                "Prompt engineering: few-shot, CoT, structured output",
                "RAG chains: ChatModel + retriever + prompt",
                "Mosaic AI Agent Framework (mlflow.langchain.log_model)",
                "Agent Bricks for low-code agent assembly",
                "Tool calling and structured outputs",
            ]),
            ("Domain 4 — Assembling & Deploying", "22%", [
                "Mosaic AI Model Serving endpoints — pay-per-token vs provisioned throughput",
                "Foundation Model APIs: DBRX, Llama, Mixtral, GTE",
                "Databricks Apps as UI layer (Streamlit, Dash, Gradio, Flask)",
                "CI/CD for agents via DABs (Databricks Asset Bundles)",
            ]),
            ("Domain 5 — Governance", "8%", [
                "AI Gateway: rate limits, budget caps, audit logs",
                "Guardrails: input/output content filtering",
                "PII detection and redaction",
                "UC permissions on models, indexes, functions",
            ]),
            ("Domain 6 — Evaluation & Monitoring", "12%", [
                "MLflow LLM Evaluate, mlflow.evaluate() with judges",
                "Custom metrics + LLM-as-judge",
                "Inference Tables for production monitoring",
                "Lakehouse Monitoring for endpoint drift",
            ]),
        ],
        "lookalikes": [
            ("Delta Sync Index", "Auto-syncs with source Delta table — managed embeddings"),
            ("Direct Access Index", "You manage embedding writes — manual upsert API"),
            ("Pay-per-token endpoint", "No infra cost; per-1k-token billing; shared capacity"),
            ("Provisioned throughput", "Dedicated capacity; predictable latency; hourly cost"),
            ("mlflow.langchain.log_model", "Logs LC chain as MLflow PyFunc"),
            ("mlflow.pyfunc.log_model", "Generic wrapper; manual code"),
            ("Agent Framework", "Code-first: build chains with code"),
            ("Agent Bricks", "Low-code wizard: declarative agent assembly"),
            ("RAG", "Retrieve-then-generate; cheap, current, citable"),
            ("Fine-tuning", "Weight updates; expensive; style/domain shift"),
        ],
        "facts_to_memorize": [
            "Vector Search index types: Delta Sync (managed) vs Direct Access (manual)",
            "Mosaic AI Vector Search supports HYBRID search out of the box",
            "Foundation Model APIs: pay-per-token shared vs provisioned dedicated",
            "DBRX, Llama 3.x, Mixtral, GTE embeddings available as FM APIs",
            "Agents are logged via mlflow.langchain.log_model or mlflow.pyfunc.log_model",
            "AI Gateway: rate limits, budget caps, PII detection, audit logs",
            "Inference Tables auto-capture request/response for endpoints",
            "Lakehouse Monitoring detects drift on endpoint Inference Tables",
            "Databricks Apps replace Mosaic AI App; deploy via DABs",
        ],
        "pitfalls": [
            "Choosing fine-tuning when RAG would solve it (cost trap)",
            "Forgetting hybrid search exists — pure semantic misses keyword-anchored queries",
            "Using a Direct Access index when Delta Sync would auto-update for free",
            "Skipping signature on agent log_model — endpoint Test UI breaks",
            "Confusing AI Gateway with Model Serving (gateway sits in front)",
            "Forgetting MLflow evaluate() built-in metrics (toxicity, faithfulness, answer_correctness)",
            "Provisioning throughput for traffic too low to amortize the hourly cost",
            "Not enabling Inference Tables before launch — no monitoring data afterward",
        ],
        "study_weeks": [
            ("Week 1", "Domains 1-2 (28%) — design + data prep; chunking + embeddings"),
            ("Week 2", "Domain 3 (30%) — prompt eng, RAG chains, agents"),
            ("Week 3", "Domain 4 (22%) — serving + apps + CI/CD"),
            ("Week 4", "Domains 5-6 (20%) — governance + evaluation; final quizzes + exam"),
        ],
        "resources": [
            "Official exam guide PDF (March 18, 2026)",
            "Databricks Academy: Generative AI Engineering Associate Pathway",
            "Career_upskill Topic 10 modules 01-15 + 6 quizzes",
            "FACTS.md — exam logistics + objective mapping",
            "Mosaic AI docs: Agent Framework, Agent Bricks, Vector Search",
        ],
    },
    "11_databricks_ml_professional": {
        "slug": "Databricks_ML_Professional",
        "cert_name": "Databricks Certified Machine Learning Professional",
        "exam_version": "September 30, 2025",
        "logistics": {
            "Question count": "59 scored multiple-choice",
            "Duration": "120 minutes (~2 min / question)",
            "Passing score": "~70% [community]",
            "Cost": "$200 USD + tax",
            "Validity": "2 years",
            "Retake wait": "14 days after 1st fail, longer after subsequent fails",
            "Delivery": "Online proctored (Webassessor / Kryterion)",
            "Prereq": "None; ~1 yr Databricks hands-on highly recommended",
        },
        "domains": [
            ("Section 1 — Model Development", "~45%", [
                "Advanced MLflow tracking: nested runs, tag CRUD, log_dict",
                "Custom PyFunc: load_context() + predict() pattern",
                "Model signatures REQUIRED for UC registration",
                "Optuna advanced: pruners, samplers, distributed via Ray",
                "Feature Engineering in UC: point-in-time joins, online tables",
                "Advanced Spark ML, ensembles, stacking",
            ]),
            ("Section 2 — MLOps", "~43%", [
                "DABs (Databricks Asset Bundles) for ML: bundle.yml, resources",
                "CI/CD with DABs: validate, deploy, run via CLI",
                "Lakehouse Monitoring deep: snapshot vs time-series profiles",
                "Drift metrics: KS, JS divergence, PSI, chi-square",
                "Custom drift metrics via SQL on profile/drift tables",
                "Model governance: UC ACLs, lineage, lineage queries",
            ]),
            ("Section 3 — Model Deployment", "~12%", [
                "Inference Tables auto-capture for endpoints",
                "Blue/green and canary deployment via traffic split",
                "Batch + streaming serving patterns",
                "Endpoint observability and latency budgets",
            ]),
        ],
        "lookalikes": [
            ("mlflow.start_run(nested=True)", "Child run under active parent; use for HPO trials"),
            ("mlflow.start_run()", "New parent run; nested=False is default"),
            ("infer_signature(X, y_pred)", "Required for UC registration"),
            ("log_model(input_example=...)", "Enables Test UI on Model Serving endpoint"),
            ("Snapshot profile", "Point-in-time stats; non-temporal data"),
            ("Time-series profile", "Windowed stats; requires timestamp column"),
            ("KS divergence", "Continuous distributions"),
            ("JS divergence", "Discrete distributions"),
            ("PSI", "Population Stability Index — bucketed; threshold 0.1/0.25"),
            ("DAB validate", "Lints bundle.yml; no deploy"),
            ("DAB deploy", "Pushes resources to target workspace"),
        ],
        "facts_to_memorize": [
            "Custom PyFunc: load_context(self, context) + predict(self, context, model_input)",
            "Hyperopt/Optuna autolog params but NOT the best model — explicit re-fit + log_model required",
            "log_model(registered_model_name='cat.sch.name') one-shot register",
            "Two-level name = workspace registry; three-level = UC",
            "DABs CLI: databricks bundle validate / deploy / run",
            "Inference Tables: enable on endpoint config — request/response auto-captured",
            "Lakehouse Monitoring: CREATE MONITOR via SQL on Delta table",
            "Drift threshold defaults: PSI 0.1 (warn) / 0.25 (alarm)",
            "MLflow nested runs: mlflow.start_run(nested=True) inside active parent",
        ],
        "pitfalls": [
            "Forgetting model signature → UC registration fails silently",
            "Logging from Hyperopt's objective without nested=True (flat run pollution)",
            "Custom PyFunc loading artifacts in __init__ instead of load_context",
            "Confusing bundle validate (lint only) with bundle deploy (push)",
            "Using PSI on continuous data without bucketing",
            "Setting traffic split before warming up the new endpoint version",
            "Inference Tables enabled but never wired to monitoring",
            "Two-level model name registers to workspace, not UC — silent fork",
        ],
        "study_weeks": [
            ("Week 1", "Section 1 (45%) — modules 01-06; advanced MLflow + PyFunc + Optuna"),
            ("Week 2", "Section 2 part 1 (MLOps platform) — modules 07-09; DABs"),
            ("Week 3", "Section 2 part 2 (Monitoring) — modules 10-12; drift + governance"),
            ("Week 4", "Section 3 + final review — modules 13-16; full timed practice"),
        ],
        "resources": [
            "Official exam guide PDF (Sept 30, 2025)",
            "Databricks Academy: Machine Learning at Scale + Advanced ML Operations",
            "Career_upskill Topic 11 modules 01-16 + 3 quizzes",
            "FACTS.md — drift metrics + DABs + PyFunc patterns",
            "MLflow 2.x docs (exam tests 2.x surface; MLflow 3 not on this version)",
        ],
    },
    "12_databricks_de_associate": {
        "slug": "Databricks_DE_Associate",
        "cert_name": "Databricks Certified Data Engineer Associate",
        "exam_version": "July 25, 2025",
        "logistics": {
            "Question count": "45 scored (ALL single-select)",
            "Duration": "90 minutes (~2 min / question)",
            "Passing score": "80% (≈ 36/45) — RAISED from 70% in July 2025 refresh",
            "Cost": "$200 USD + tax",
            "Validity": "2 years",
            "Retake wait": "14 days after 1st fail; 30 days after subsequent",
            "Delivery": "Online proctored OR in-person test center",
            "Code language": "SQL when possible; otherwise Python (PySpark)",
        },
        "domains": [
            ("Domain 1 — Databricks Intelligence Platform", "10%", [
                "Lakehouse architecture, medallion (bronze/silver/gold)",
                "Workspace, clusters (all-purpose vs job), DBR runtime",
                "Notebooks, SQL Warehouses, repos",
                "Pricing: DBU types, photon multiplier",
            ]),
            ("Domain 2 — Development and Ingestion", "30%", [
                "Delta Lake: ACID, transaction log _delta_log, VACUUM, OPTIMIZE",
                "Auto Loader: cloudFiles, schema inference, evolution modes",
                "COPY INTO vs Auto Loader tradeoffs",
                "Ingestion patterns: append, merge, upsert",
                "Schema evolution: rescue, addNewColumns, failOnNewColumns",
            ]),
            ("Domain 3 — Data Processing & Transformations", "31%", [
                "PySpark + Spark SQL transformations",
                "Structured Streaming: trigger modes, watermarks, state",
                "MERGE INTO syntax: matched/not matched / by source",
                "Window functions, joins, CTEs",
                "Photon acceleration scope",
            ]),
            ("Domain 4 — Productionizing Data Pipelines", "18%", [
                "LakeFlow Declarative Pipelines (formerly DLT)",
                "LakeFlow Jobs (formerly Workflows)",
                "DABs for DE: bundle.yml, resources.pipelines, resources.jobs",
                "Triggers, dependencies, retries, alerts",
            ]),
            ("Domain 5 — Data Governance & Quality", "11%", [
                "Unity Catalog: catalog.schema.table, grants, lineage",
                "Delta Sharing (open source vs Databricks-to-Databricks)",
                "Lakehouse Federation (foreign catalogs)",
                "Expectations: EXPECT, EXPECT...DROP, EXPECT...FAIL",
            ]),
        ],
        "lookalikes": [
            ("COPY INTO", "Idempotent batch ingest; SQL syntax; remembers files"),
            ("Auto Loader (cloudFiles)", "Incremental streaming ingest; file notification or directory listing"),
            ("EXPECT", "Log violation; row passes through (default)"),
            ("EXPECT ... ON VIOLATION DROP", "Filter out violating rows"),
            ("EXPECT ... ON VIOLATION FAIL", "Abort the update"),
            ("OPTIMIZE", "Compacts small files (default ~1GB target)"),
            ("VACUUM", "Removes files past retention threshold (default 7 days)"),
            ("ZORDER BY", "Multi-column data skipping; combined with OPTIMIZE"),
            ("Liquid Clustering", "Replaces ZORDER + partitioning; auto-evolves"),
            ("MERGE INTO ... WHEN MATCHED", "Update/delete existing rows"),
            ("MERGE INTO ... WHEN NOT MATCHED BY SOURCE", "Delete rows missing from source"),
            ("LakeFlow Declarative Pipelines", "New name for DLT"),
            ("LakeFlow Jobs", "New name for Workflows"),
        ],
        "facts_to_memorize": [
            "Passing score is 80% — RAISED in July 2025 refresh",
            "All questions are single-select — no multi-select on this exam",
            "VACUUM default retention: 7 days (cannot go below 0; force needed under 7d)",
            "OPTIMIZE default target file size: ~1 GB (auto-tunes by table size)",
            "Auto Loader schema modes: addNewColumns (default), rescue, failOnNewColumns, none",
            "Delta transaction log = _delta_log/*.json + *.checkpoint.parquet",
            "checkpoint every 10 commits by default",
            "DLT renamed to LakeFlow Declarative Pipelines; Workflows → LakeFlow Jobs",
            "UC three-level namespace required; INFORMATION_SCHEMA per-catalog",
            "Delta Sharing: open protocol + recipient credential",
        ],
        "pitfalls": [
            "Assuming 70% passing score — it's 80% on July 2025 guide",
            "Confusing COPY INTO (batch, idempotent) with Auto Loader (streaming, incremental)",
            "VACUUM with retention <7 days requires retentionDurationCheck.enabled=false",
            "Forgetting that MERGE BY SOURCE clauses are separate from BY TARGET",
            "Using DLT terminology when the exam now uses LakeFlow naming",
            "Schema evolution: 'rescue' silently captures bad data — read the column!",
            "Photon doesn't accelerate every operation — UDFs and some functions opt-out",
            "Expectations without ON VIOLATION just log — rows still pass through",
        ],
        "study_weeks": [
            ("Week 1", "Domains 1+2 (40%) — platform basics + Delta + Auto Loader"),
            ("Week 2", "Domain 3 (31%) — transformations + Structured Streaming"),
            ("Week 3", "Domain 4 (18%) — LakeFlow pipelines + jobs + DABs"),
            ("Week 4", "Domain 5 + final review — UC, Delta Sharing, expectations"),
        ],
        "resources": [
            "Official exam guide PDF (July 25, 2025)",
            "Databricks Academy: Data Engineer Associate Learning Path",
            "Career_upskill Topic 12 modules 01-16 + 5 quizzes",
            "FACTS.md — 80% pass threshold, single-select, LakeFlow naming",
            "Delta Lake docs + Auto Loader docs",
        ],
    },
    "13_databricks_spark_dev_associate": {
        "slug": "Databricks_Spark_Dev_Associate",
        "cert_name": "Databricks Certified Associate Developer for Apache Spark",
        "exam_version": "October 30, 2025",
        "logistics": {
            "Question count": "45 scored multiple-choice",
            "Duration": "90 minutes (~2 min / question)",
            "Passing score": "~70% [community, not officially published]",
            "Cost": "$200 USD + tax",
            "Validity": "2 years",
            "Spark version": "Apache Spark 3.5.x (NOT 4.0)",
            "Code language": "Python ONLY — Scala removed",
            "Delivery": "Online proctored OR in-person",
        },
        "domains": [
            ("Domain 1 — Spark Architecture and Components", "20%", [
                "Driver, executor, cluster manager, application/job/stage/task",
                "Cluster modes; standalone vs YARN vs Kubernetes",
                "Lazy evaluation, DAG, narrow vs wide transformations",
                "Shuffle, partitioning, RDD lineage",
            ]),
            ("Domain 2 — Using Spark SQL", "20%", [
                "Catalog, database, table, view",
                "createOrReplaceTempView vs createGlobalTempView",
                "Built-in functions: pyspark.sql.functions module",
                "Window functions: partitionBy, orderBy, rowsBetween, rangeBetween",
            ]),
            ("Domain 3 — DataFrame / Dataset API", "30%", [
                "DataFrame creation, schema (StructType, StructField, types)",
                "select / filter / where / withColumn / drop",
                "groupBy + agg with multiple aggregations",
                "join types: inner, outer, left, right, semi, anti, cross",
                "union vs unionByName",
                "Reading/writing: csv, json, parquet, delta",
            ]),
            ("Domain 4 — Troubleshooting and Tuning", "10%", [
                "Spark UI: jobs, stages, SQL tabs",
                "AQE (Adaptive Query Execution) defaults",
                "Broadcast join hints, skew join handling",
                "Caching: persist, cache, unpersist, storage levels",
            ]),
            ("Domain 5 — Structured Streaming", "10%", [
                "DataStreamReader / DataStreamWriter",
                "Trigger modes: default, processingTime, once, availableNow",
                "Output modes: append, complete, update",
                "Watermarks: withWatermark, late data handling",
            ]),
            ("Domain 6 — Spark Connect", "5%", [
                "Client/server decoupled architecture",
                "Spark Connect client: pyspark[connect]",
                "Remote SparkSession.builder.remote('sc://host:port')",
                "Limitations: no SparkContext, no RDD API",
            ]),
            ("Domain 7 — Pandas API on Spark", "5%", [
                "import pyspark.pandas as ps",
                "ps.DataFrame vs pandas.DataFrame",
                "to_pandas() vs to_spark() conversions",
                "Index types: sequence (default), distributed, distributed-sequence",
            ]),
        ],
        "lookalikes": [
            ("union", "Union by COLUMN POSITION — same schema required"),
            ("unionByName", "Union by COLUMN NAME — allowMissingColumns optional"),
            ("createOrReplaceTempView", "Session-scoped; lost when SparkSession ends"),
            ("createGlobalTempView", "Cross-session; lives in global_temp database"),
            ("cache()", "Equivalent to persist(MEMORY_AND_DISK)"),
            ("persist(level)", "Choose StorageLevel (DISK_ONLY, MEMORY_ONLY_SER, etc.)"),
            ("groupBy().agg()", "Wide transformation; triggers shuffle"),
            ("groupByKey", "Avoid — collects values; prefer reduceByKey/agg"),
            ("inner join", "Default — only matching rows"),
            ("left_anti", "Rows in left WITHOUT a match in right"),
            ("left_semi", "Rows in left WITH a match in right (no right columns)"),
            ("trigger(processingTime='1 minute')", "Micro-batch every minute"),
            ("trigger(availableNow=True)", "Process all available data once, then stop"),
            ("trigger(once=True)", "DEPRECATED — use availableNow"),
        ],
        "facts_to_memorize": [
            "Spark version tested: 3.5.x — NOT 4.0; Variant type, default ANSI, collations are OUT of scope",
            "Code language: Python ONLY — Scala removed from this exam",
            "DBR/Unity Catalog/Delta operations are NOT tested — pure OSS Spark",
            "Delta is in scope only as readable format: delta.`path`",
            "AQE is ON by default in Spark 3.5",
            "Narrow transformations: map, filter, select, withColumn (no shuffle)",
            "Wide transformations: groupBy, join, distinct, orderBy (shuffle)",
            "Default shuffle partitions: 200 (spark.sql.shuffle.partitions)",
            "withWatermark required for stateful aggregations with append mode",
            "Spark Connect: remote() URI scheme is sc://",
        ],
        "pitfalls": [
            "Assuming Spark 4.0 features are tested — they are NOT",
            "Expecting Scala code — Python only",
            "Using union when columns are in different order — use unionByName",
            "Confusing cache() with persist() — cache is just persist(MEMORY_AND_DISK)",
            "Forgetting withWatermark on streaming aggregations → unbounded state",
            "Using trigger(once=True) on the exam — it's deprecated, expect availableNow",
            "Mixing up output mode 'append' vs 'complete' for stateful streams",
            "Expecting Delta-specific operations like OPTIMIZE on the exam (not tested)",
            "Using SparkContext under Spark Connect (not available)",
        ],
        "study_weeks": [
            ("Week 1", "Domain 1 (20%) — architecture + lazy eval + DAG"),
            ("Week 2", "Domains 2+3 (50%) — Spark SQL + DataFrame API"),
            ("Week 3", "Domain 4 (10%) — tuning + Spark UI + AQE"),
            ("Week 4", "Domains 5-7 (20%) — Streaming + Spark Connect + Pandas API"),
            ("Exam week", "Official sample questions + timed practice"),
        ],
        "resources": [
            "Official exam guide PDF (October 30, 2025)",
            "Apache Spark 3.5 docs: spark.apache.org/docs/3.5.0/",
            "Career_upskill Topic 13 modules 01-14 + 5 quizzes (incl. official sample walkthrough)",
            "FACTS.md — Spark 3.5 scope boundaries; Python-only confirmation",
            "Databricks Academy: Spark Programming with Python",
        ],
    },
}


# ── Deck builder ─────────────────────────────────────────────────────────────
def build_deck(out_path: Path, cfg: dict) -> int:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    DBX_ORANGE = RGBColor(0xFF, 0x36, 0x21)
    DARK = RGBColor(0x1C, 0x26, 0x38)
    SUBTLE = RGBColor(0x4A, 0x5A, 0x75)

    BLANK = prs.slide_layouts[6]   # blank
    TITLE_CONTENT = prs.slide_layouts[1]

    def add_title_slide(title, subtitle):
        slide = prs.slides.add_slide(BLANK)
        # Orange accent band on left
        from pptx.shapes.autoshape import Shape
        from pptx.enum.shapes import MSO_SHAPE
        band = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.6), prs.slide_height)
        band.fill.solid()
        band.fill.fore_color.rgb = DBX_ORANGE
        band.line.fill.background()

        # Title
        tb = slide.shapes.add_textbox(Inches(1.0), Inches(1.5), Inches(11.5), Inches(2.5))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(40)
        p.font.bold = True
        p.font.color.rgb = DARK

        # Subtitle
        sub = slide.shapes.add_textbox(Inches(1.0), Inches(4.2), Inches(11.5), Inches(2.5))
        stf = sub.text_frame
        stf.word_wrap = True
        sp = stf.paragraphs[0]
        sp.text = subtitle
        sp.font.size = Pt(20)
        sp.font.color.rgb = SUBTLE

    def add_bullet_slide(title, bullets, title_size=28, bullet_size=18):
        slide = prs.slides.add_slide(BLANK)
        # Title bar
        tb = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.5), Inches(0.9))
        tf = tb.text_frame
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(title_size)
        p.font.bold = True
        p.font.color.rgb = DBX_ORANGE

        # Body
        body = slide.shapes.add_textbox(Inches(0.5), Inches(1.4), Inches(12.5), Inches(5.7))
        btf = body.text_frame
        btf.word_wrap = True
        for i, b in enumerate(bullets):
            if i == 0:
                para = btf.paragraphs[0]
            else:
                para = btf.add_paragraph()
            para.text = f"• {b}"
            para.font.size = Pt(bullet_size)
            para.font.color.rgb = DARK
            para.space_after = Pt(6)

    def add_two_col_slide(title, left_header, right_header, rows):
        """rows = list of (left, right) tuples; renders as 2-column 'cheat sheet'."""
        slide = prs.slides.add_slide(BLANK)
        tb = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.5), Inches(0.9))
        p = tb.text_frame.paragraphs[0]
        p.text = title
        p.font.size = Pt(28)
        p.font.bold = True
        p.font.color.rgb = DBX_ORANGE

        # Use a table for clean layout
        n_rows = len(rows) + 1
        table_shape = slide.shapes.add_table(n_rows, 2, Inches(0.5), Inches(1.3), Inches(12.5), Inches(5.9))
        table = table_shape.table
        # column widths
        table.columns[0].width = Inches(4.5)
        table.columns[1].width = Inches(8.0)

        # header
        h_left = table.cell(0, 0)
        h_left.text = left_header
        h_right = table.cell(0, 1)
        h_right.text = right_header
        for cell in (h_left, h_right):
            cell.fill.solid()
            cell.fill.fore_color.rgb = DBX_ORANGE
            for para in cell.text_frame.paragraphs:
                for run in para.runs:
                    run.font.bold = True
                    run.font.size = Pt(14)
                    run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

        for i, (a, b) in enumerate(rows, start=1):
            ca = table.cell(i, 0)
            ca.text = a
            cb = table.cell(i, 1)
            cb.text = b
            for cell in (ca, cb):
                for para in cell.text_frame.paragraphs:
                    for run in para.runs:
                        run.font.size = Pt(11)
                        run.font.color.rgb = DARK

    # ── Slide 1: Title ─────────────────────────────────────────────────────
    add_title_slide(
        cfg["cert_name"],
        f"Study deck · Exam version {cfg['exam_version']} · Career_upskill 2026",
    )

    # ── Slide 2: Exam logistics ────────────────────────────────────────────
    log_rows = [(k, v) for k, v in cfg["logistics"].items()]
    add_two_col_slide("Exam logistics", "Item", "Value", log_rows)

    # ── Slide 3: Exam blueprint (domain weights) ───────────────────────────
    blueprint_rows = [(d[0], d[1]) for d in cfg["domains"]]
    add_two_col_slide("Exam blueprint — domain weights", "Domain", "Weight", blueprint_rows)

    # ── Per-domain overview + objectives ────────────────────────────────────
    # Each domain gets TWO slides: (a) overview/objectives, (b) key APIs / what to drill
    for dom_name, weight, bullets in cfg["domains"]:
        add_bullet_slide(f"{dom_name}  ({weight})", bullets, title_size=24, bullet_size=18)
        # Drill slide: a focused "what to memorize for this domain" view
        drill = [f"Weight: {weight} — allocate study time proportionally"] + [
            f"Drill: {b}" for b in bullets[:4]
        ]
        add_bullet_slide(f"{dom_name} — what to drill", drill, title_size=22, bullet_size=18)

    # ── Look-alikes cheat sheet ────────────────────────────────────────────
    # Split into smaller chunks for legibility and more slides
    lookalikes = cfg["lookalikes"]
    chunk_size = 5
    for i in range(0, len(lookalikes), chunk_size):
        chunk = lookalikes[i:i + chunk_size]
        suffix = "" if len(lookalikes) <= chunk_size else f" ({i // chunk_size + 1})"
        add_two_col_slide(f"Look-alike APIs / traps cheat sheet{suffix}", "Term / API", "Behavior", chunk)

    # ── Key facts to memorize ──────────────────────────────────────────────
    add_bullet_slide("Key facts to memorize", cfg["facts_to_memorize"], title_size=28, bullet_size=16)

    # ── Common exam pitfalls ───────────────────────────────────────────────
    add_bullet_slide("Common exam pitfalls", cfg["pitfalls"], title_size=28, bullet_size=16)

    # ── Study plan ─────────────────────────────────────────────────────────
    plan_rows = cfg["study_weeks"]
    add_two_col_slide("Study plan (4 weeks)", "Period", "Focus", plan_rows)

    # ── Resources ──────────────────────────────────────────────────────────
    add_bullet_slide("Resources", cfg["resources"], title_size=28, bullet_size=16)

    # ── Final reminder ─────────────────────────────────────────────────────
    add_bullet_slide(
        "Final reminder — exam day",
        [
            f"Passing score: see logistics slide (varies per cert)",
            "Manage time: ~2 min per question; flag and move on if stuck",
            "Read multi-select stems carefully ('Select TWO/THREE')",
            "Eliminate distractors first — usually 2 of 4 are obviously wrong",
            "Trust the look-alike traps you memorized — they reappear verbatim",
            "Re-read this deck the morning of the exam; skip new material",
            "Webcam + clean desk + photo ID ready 30 min before slot",
        ],
        title_size=28,
        bullet_size=16,
    )

    prs.save(str(out_path))
    return len(prs.slides.__iter__.__self__._sldIdLst)  # crude slide count


def main():
    total_built = 0
    for dir_name, cfg in DECKS.items():
        topic_dir = TOPICS / dir_name
        pptx_dir = topic_dir / "pptx"
        pptx_dir.mkdir(exist_ok=True)
        out = pptx_dir / f"{cfg['slug']}_study_deck.pptx"
        # Persist this script's config so the deck is regenerable
        cfg_out = pptx_dir / "deck_config.json"
        cfg_out.write_text(json.dumps(cfg, indent=2))
        # Also drop a minimal build_deck.py per topic for regeneration
        build_py = pptx_dir / "build_deck.py"
        build_py.write_text(
            "#!/usr/bin/env python3\n"
            '"""Regenerate this topic\'s study deck from deck_config.json."""\n'
            "import json, sys\n"
            "from pathlib import Path\n"
            "HERE = Path(__file__).parent\n"
            "sys.path.insert(0, '/tmp')\n"
            "from build_all_pptx import build_deck  # noqa\n"
            "cfg = json.loads((HERE / 'deck_config.json').read_text())\n"
            f"out = HERE / '{cfg['slug']}_study_deck.pptx'\n"
            "build_deck(out, cfg)\n"
            "print(f'Wrote {out}')\n"
        )

        n = build_deck(out, cfg)
        size = out.stat().st_size
        print(f"  {dir_name} → {out.name}  ({n} slides, {size:,} bytes)")
        total_built += 1
    print(f"\nBuilt {total_built} decks.")


if __name__ == "__main__":
    main()
