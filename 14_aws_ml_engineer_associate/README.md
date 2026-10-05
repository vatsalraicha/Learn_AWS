# AWS Certified Machine Learning Engineer – Associate (MLA-C01) — Mastery Track

> A textbook for engineers preparing to sit the **AWS Certified Machine Learning Engineer – Associate (MLA-C01)** exam — written to teach the underlying systems and engineering tradeoffs, not to drill exam objectives. SageMaker is the syntactic surface; the depth lives in the data architecture, the deployment topologies, the security posture, the cost levers, and the failure modes underneath. If you finish this book, no question on this material should surprise you, and you will be genuinely better at building production ML on AWS.
>
> **Audience:** strong Python assumed; ML fundamentals assumed (we link back to [Topic 9a](../09a_databricks_ml_associate/README.md) for first-principles math). AWS taught from a working level — IAM, S3, VPC are reviewed but not from zero.
>
> **Exam under the hood:** MLA-C01, 65 questions (50 scored + 15 unscored), 130 minutes, passing scaled score 720/1000, no per-section minimums. 4 content domains: Data Prep (28%) / Model Dev (26%) / Deployment & Orchestration (22%) / Monitoring + Security (24%).

---

## How this book relates to Topic 9a

Topic 9a — *Databricks ML Associate Mastery* — already covers ML foundations from first principles: probability & statistics, linear algebra & calculus, the bias-variance decomposition, gradient descent, loss functions, regularization, cross-validation, every major supervised/unsupervised algorithm, the full evaluation-metric zoo, and the science of hyperparameter optimization. **Topic 14 does not re-teach any of that.** Where a chapter needs an ML concept, it links directly to the Topic 9a chapter that explains it. The math is there if you need it — go read it once, come back here, and stay focused on AWS.

| If you need… | Read this Topic 9a chapter first |
|---|---|
| Probability, distributions, hypothesis testing | [Part B (chs 5-10)](../09a_databricks_ml_associate/README.md#part-b--probability--statistics-primer) |
| Vectors, dot products, eigenvalues, gradients | [Part C (chs 11-15)](../09a_databricks_ml_associate/README.md#part-c--linear-algebra--calculus-essentials) |
| Loss, gradient descent, bias-variance, regularization | [Part D (chs 16-22)](../09a_databricks_ml_associate/README.md#part-d--the-fundamental-ml-problem) |
| Feature engineering taxonomy | [Part E (chs 23-30)](../09a_databricks_ml_associate/README.md#part-e--feature-engineering-as-a-discipline) |
| Linear/logistic/tree/RF/GBM/XGBoost/LightGBM | [Part F (chs 31-37)](../09a_databricks_ml_associate/README.md#part-f--supervised-algorithms--from-the-math) |
| K-means, hierarchical, PCA, t-SNE | [Part G (chs 38-41)](../09a_databricks_ml_associate/README.md#part-g--unsupervised-algorithms) |
| Confusion matrix, ROC/AUC, F1, RMSE, R² | [Part H (chs 42-47)](../09a_databricks_ml_associate/README.md#part-h--model-evaluation-theory) |
| Grid/Random/Bayesian/TPE HPO | [Part I (chs 48-54)](../09a_databricks_ml_associate/README.md#part-i--hyperparameter-optimization--the-science) |

The MLA-C01 exam includes a few ML-theory questions — confusion matrix, F1, RMSE, ROC/AUC, overfitting/underfitting, regularization (dropout, L1/L2, weight decay), Bayesian optimization vs random search. Topic 9a covers every one of these in depth. We will not duplicate that work here.

---

## Contents

| Part | Theme | Chapters | Exam domain |
|------|-------|---------:|------------:|
| **A** | [Why cloud-native ML — the MLA-C01 landscape](#part-a--why-cloud-native-ml--the-mla-c01-landscape) | 4 | meta |
| **B** | [AWS foundations every ML engineer must own](#part-b--aws-foundations-every-ml-engineer-must-own) | 5 | foundations |
| **C** | [Data ingestion & storage on AWS](#part-c--data-ingestion--storage-on-aws) | 6 | D1 (28%) |
| **D** | [Data preparation, transformation & feature engineering](#part-d--data-preparation-transformation--feature-engineering) | 6 | D1 (28%) |
| **E** | [Model development on SageMaker](#part-e--model-development-on-sagemaker) | 9 | D2 (26%) |
| **F** | [Hyperparameter tuning & distributed training](#part-f--hyperparameter-tuning--distributed-training) | 4 | D2 (26%) |
| **G** | [Deployment & inference infrastructure](#part-g--deployment--inference-infrastructure) | 8 | D3 (22%) |
| **H** | [Orchestration & CI/CD for ML](#part-h--orchestration--cicd-for-ml) | 5 | D3 (22%) |
| **I** | [Monitoring, drift & governance](#part-i--monitoring-drift--governance) | 5 | D4 (24%) |
| **J** | [Security, IAM, networking & cost optimization](#part-j--security-iam-networking--cost-optimization) | 6 | D4 (24%) |
| **K** | [AWS AI services & generative AI](#part-k--aws-ai-services--generative-ai) | 4 | D2 + D3 |
| **L** | [Capstone & exam strategy](#part-l--capstone--exam-strategy) | 2 | meta |

**Total: ~64 chapters.** Numbered consecutively, intended to be read in order — later chapters assume earlier ones.

---

## Part A — Why Cloud-Native ML — the MLA-C01 Landscape

> **Goal:** Before any service, understand the *problem* MLA-C01 was created to validate — that you can build, operationalize, deploy, and maintain ML pipelines on AWS. Every later chapter is in service of one of those four verbs.

| # | Chapter | What you'll be able to do after |
|---|---------|---------------------------------|
| 1 | [What an "ML Engineer" actually does on AWS](part_a_landscape/01_what_is_mle.md) | Distinguish the ML engineer's job from data scientist, ML researcher, platform engineer; situate the MLE role inside an AWS-native team |
| 2 | [The MLA-C01 exam dissected](part_a_landscape/02_exam_dissected.md) | Recite the 4 domains and 12 task statements; understand question formats (multi-choice, multi-response, ordering, matching); pace yourself for 50 scored + 15 unscored in 130 min |
| 3 | [The AWS ML stack — a 30,000 ft map](part_a_landscape/03_aws_ml_stack_map.md) | Draw the AWS ML stack: infra layer (EC2, S3, VPC, IAM) → data layer (Glue, Athena, EMR, Kinesis) → ML platform (SageMaker, Bedrock) → AI services (Comprehend, Rekognition, etc.); know which services are in-scope vs out-of-scope |
| 4 | [SageMaker as the spine — anatomy in one chapter](part_a_landscape/04_sagemaker_anatomy.md) | Name every SageMaker AI surface (Studio, Training, HPO, Pipelines, Registry, Model Monitor, Clarify, Feature Store, etc.) and connect each to its exam-relevant tasks |

---

## Part B — AWS Foundations Every ML Engineer Must Own

> **Goal:** You cannot pass MLA-C01 without competent IAM, S3, and VPC. We compress these into a working-engineer's review — not from zero, but tight enough that nothing about them will trip you on the exam.

| # | Chapter | What you'll be able to do after |
|---|---------|---------------------------------|
| 5 | [IAM for ML — roles, policies, the pass-role trap](part_b_aws_foundations/05_iam_for_ml.md) | Build a least-privilege SageMaker execution role; explain explicit-deny > explicit-allow > implicit-deny; debug `iam:PassRole` failures; use SageMaker Role Manager |
| 6 | [S3 deep dive for ML workloads](part_b_aws_foundations/06_s3_for_ml.md) | Choose between S3 storage classes for hot/warm/cold ML data; configure encryption (SSE-S3 / SSE-KMS / DSSE-KMS); use S3 Object Lock, Versioning, Transfer Acceleration; understand prefix design for high-throughput training |
| 7 | [VPC, subnets, security groups, endpoints](part_b_aws_foundations/07_vpc_for_ml.md) | Architect a private VPC for ML: private subnets, NAT-less egress via VPC endpoints, SageMaker Studio in VPC-only mode, interface vs gateway endpoints |
| 8 | [KMS, Secrets Manager & encryption-in-depth](part_b_aws_foundations/08_kms_secrets.md) | Distinguish AWS-managed keys vs CMKs vs multi-region keys; envelope encryption; how `KmsKeyId` flows through SageMaker training/processing/endpoint resources; when to use Secrets Manager vs SSM Parameter Store |
| 9 | [Compute primitives — EC2 families, containers, Lambda](part_b_aws_foundations/09_compute_primitives.md) | Pick the right EC2 family for ML (compute-optimized, GPU, Inf/Trn, Graviton); container basics (ECR, ECS, EKS); when Lambda is the right host for inference |

---

## Part C — Data Ingestion & Storage on AWS  *(Domain 1, weight 28%)*

| # | Chapter | What you'll be able to do after |
|---|---------|---------------------------------|
| 10 | [Data formats for ML — Parquet, ORC, Avro, RecordIO, TFRecord, JSON, CSV](part_c_data_ingestion_storage/10_data_formats.md) | Choose a format by access pattern (columnar reads → Parquet; streaming → Avro; SageMaker training → RecordIO-protobuf); know which formats SageMaker built-in algos prefer |
| 11 | [S3, EFS, FSx for Lustre, FSx for ONTAP — the training-data storage matrix](part_c_data_ingestion_storage/11_storage_for_training.md) | Pick the right storage for the training input mode (Pipe vs File vs FastFile); reason about throughput, IOPS, $/GB, and warm-up time |
| 12 | [Streaming ingestion — Kinesis Data Streams, Data Firehose, MSAF, MSK](part_c_data_ingestion_storage/12_streaming_ingestion.md) | Distinguish KDS vs Firehose vs MSAF vs MSK; design a real-time feature pipeline that lands in S3 + Feature Store; understand shard count math and enhanced fan-out |
| 13 | [AWS Glue catalog, Athena, Lake Formation](part_c_data_ingestion_storage/13_glue_athena_lakeformation.md) | Use Glue crawlers to register S3 datasets; query with Athena; layer Lake Formation fine-grained permissions and LF-tags on top |
| 14 | [Amazon EMR for ML data processing](part_c_data_ingestion_storage/14_emr_for_ml.md) | Choose EMR-on-EC2 vs EMR Serverless vs EMR on EKS; use Spark to prep features at scale; integrate EMR with SageMaker Pipelines |
| 15 | [Operational data — DynamoDB, RDS, OpenSearch, Redshift for ML](part_c_data_ingestion_storage/15_operational_stores.md) | Decide when DynamoDB serves online features; when Redshift powers training data extraction; when OpenSearch hosts vector search for RAG |

---

## Part D — Data Preparation, Transformation & Feature Engineering  *(Domain 1, weight 28%)*

| # | Chapter | What you'll be able to do after |
|---|---------|---------------------------------|
| 16 | [AWS Glue jobs — Spark, Python shell, Ray](part_d_data_prep_features/16_glue_jobs.md) | Write a Glue Spark job for ML data prep; use bookmarks; understand DPU pricing; know when Glue Studio's visual editor is the right tool |
| 17 | [AWS Glue DataBrew — recipes, profiles, jobs](part_d_data_prep_features/17_glue_databrew.md) | Build a 250-step DataBrew recipe for cleansing; export to S3, Glue Catalog, or SageMaker; use profile jobs for column statistics + PII detection |
| 18 | [SageMaker Data Wrangler — visual feature engineering](part_d_data_prep_features/18_data_wrangler.md) | Build a Data Wrangler flow; ingest from 40+ sources; export to Feature Store, Pipelines, Python notebook, Spark; understand data quality + insights reports |
| 19 | [SageMaker Feature Store — online + offline](part_d_data_prep_features/19_feature_store.md) | Design feature groups; choose Standard vs In-memory online store; point-in-time correctness via the offline store on S3 with Iceberg; TTL configuration |
| 20 | [Data labeling — SageMaker Ground Truth, Ground Truth Plus, A2I, Mechanical Turk](part_d_data_prep_features/20_data_labeling.md) | Pick the labeling workflow for the job (built-in task types, custom UI, vendor workforce, MTurk, GT Plus); apply active learning to reduce labeling cost |
| 21 | [Bias detection & data-integrity — SageMaker Clarify, Glue Data Quality, Macie](part_d_data_prep_features/21_bias_integrity.md) | Compute pre-training bias metrics (CI, DPL, KL, JS, LP, TVD, KS); use Glue Data Quality with DQDL; detect PII/PHI with Macie |

---

## Part E — Model Development on SageMaker  *(Domain 2, weight 26%)*

| # | Chapter | What you'll be able to do after |
|---|---------|---------------------------------|
| 22 | [SageMaker Studio anatomy & training-job lifecycle](part_e_model_development/22_studio_lifecycle.md) | Navigate Studio Classic vs Studio (Code Editor, JupyterLab, RStudio); spin up a training job; understand the `/opt/ml/` container contract |
| 23 | [SageMaker built-in algorithms — what each is for](part_e_model_development/23_builtin_algorithms.md) | Pick the right built-in for the problem (XGBoost, Linear Learner, Object Detection, BlazingText, DeepAR, Random Cut Forest, IP Insights, etc.); know input formats and instance recommendations |
| 24 | [Script mode — TensorFlow, PyTorch, HuggingFace, Sklearn](part_e_model_development/24_script_mode.md) | Wrap your own training code in script mode; structure `train.py`; pass hyperparameters; checkpoint to S3; resume from spot interruption |
| 25 | [BYOC — bring your own container](part_e_model_development/25_byoc.md) | Build a SageMaker-compatible container (training and serving); use the SageMaker Toolkit; push to ECR; debug container-contract errors |
| 26 | [SageMaker JumpStart — foundation models & pre-built solutions](part_e_model_development/26_jumpstart.md) | Browse JumpStart's model hub; deploy and fine-tune an FM; use solution templates; understand cost model vs Bedrock |
| 27 | [SageMaker Autopilot — AutoML done right](part_e_model_development/27_autopilot.md) | Run Autopilot in ensembling vs HPO mode; interpret the candidate notebook; know when AutoML is appropriate (and when not) |
| 28 | [SageMaker Experiments + MLflow on SageMaker](part_e_model_development/28_experiments_mlflow.md) | Track runs, trials, trial components; use managed MLflow on SageMaker (2024 GA); compare experiments; build reproducibility |
| 29 | [SageMaker Clarify — interpretability + bias for trained models](part_e_model_development/29_clarify_explainability.md) | Configure Clarify processing jobs; compute SHAP values; produce model explainability reports; enable online explainability for endpoints |
| 30 | [SageMaker Debugger & Profiler — convergence diagnostics](part_e_model_development/30_debugger_profiler.md) | Wire Debugger rules (vanishing gradients, exploding tensors, overfit); enable Profiler; read profiler reports; debug a stuck training job |

---

## Part F — Hyperparameter Tuning & Distributed Training  *(Domain 2, weight 26%)*

| # | Chapter | What you'll be able to do after |
|---|---------|---------------------------------|
| 31 | [SageMaker Automatic Model Tuning (AMT)](part_f_hpo_distributed_training/31_amt.md) | Define a tuning job: search space, objective metric, strategy (Bayesian, Random, Grid, Hyperband); warm start; early stopping |
| 32 | [Distributed training — data parallel, model parallel, SMDDP, FSDP](part_f_hpo_distributed_training/32_distributed_training.md) | Choose data-parallel vs model-parallel; configure SMDDP or HF Accelerate; understand the cost of inter-node communication; use SageMaker HyperPod for >100-node training |
| 33 | [Spot training, managed warm pools, checkpointing](part_f_hpo_distributed_training/33_spot_warmpools.md) | Cut training cost ~70% with Spot; survive interruption via S3 checkpointing; use Managed Warm Pools to avoid cold-start overhead |
| 34 | [Training-cost optimization patterns](part_f_hpo_distributed_training/34_training_cost.md) | Right-size training instances; mix Spot + On-Demand; pre-resize datasets; use Pipe mode + FastFile mode; understand SageMaker Training Compiler |

---

## Part G — Deployment & Inference Infrastructure  *(Domain 3, weight 22%)*

| # | Chapter | What you'll be able to do after |
|---|---------|---------------------------------|
| 35 | [The four SageMaker endpoint types — real-time, serverless, async, batch](part_g_deployment_orchestration/35_endpoint_types.md) | Pick the right endpoint type given latency, payload, traffic-shape, cost; build a comparison table from memory |
| 36 | [Real-time endpoints — production variants, A/B, shadow tests](part_g_deployment_orchestration/36_realtime_endpoints.md) | Deploy multiple variants behind one endpoint; configure `InitialVariantWeight`; run shadow tests; promote a winner |
| 37 | [Serverless inference & provisioned concurrency](part_g_deployment_orchestration/37_serverless_inference.md) | Deploy a serverless endpoint with memory tier + max-concurrency; understand cold starts; add provisioned concurrency when needed |
| 38 | [Async inference & batch transform](part_g_deployment_orchestration/38_async_batch.md) | Use async for >1-min inference or >6MB payloads; set up SNS notifications; understand batch transform's manifest format and instance fan-out |
| 39 | [Multi-model endpoints (MME) & multi-container endpoints (MCE)](part_g_deployment_orchestration/39_mme_mce.md) | Host hundreds of models on one endpoint with MME (model isolation, S3 model cache); use MCE for chained pipelines |
| 40 | [Endpoint auto-scaling, deployment strategies, rollback](part_g_deployment_orchestration/40_autoscale_deploy.md) | Configure target-tracking + step scaling; pick blue/green vs canary vs linear vs rolling; auto-rollback on CloudWatch alarm |
| 41 | [SageMaker Inference Recommender + Neo + edge](part_g_deployment_orchestration/41_inference_optimization.md) | Run an Inference Recommender job (default vs advanced load test); compile a model with Neo for edge; deploy to Greengrass |
| 42 | [Inference outside SageMaker — Lambda, ECS, EKS, Kubernetes](part_g_deployment_orchestration/42_inference_outside.md) | Decide when Lambda is the right inference host; deploy with SageMaker Operators for Kubernetes; trade off SageMaker convenience vs EKS control |

---

## Part H — Orchestration & CI/CD for ML  *(Domain 3, weight 22%)*

| # | Chapter | What you'll be able to do after |
|---|---------|---------------------------------|
| 43 | [SageMaker Pipelines — step types, parameters, conditions](part_h_monitoring_governance/43_sagemaker_pipelines.md) | Build a SageMaker Pipeline end-to-end (processing → training → eval → conditional registration); use caching; trigger from EventBridge |
| 44 | [Step Functions vs SageMaker Pipelines vs MWAA](part_h_monitoring_governance/44_orchestrator_comparison.md) | Recite the decision tree: SageMaker Pipelines for ML-only, Step Functions for cross-service, MWAA for Airflow shops; build a Step Functions DAG that calls SageMaker training |
| 45 | [EventBridge — schedule, rules, Pipes, Scheduler](part_h_monitoring_governance/45_eventbridge.md) | Trigger retraining on a schedule or event (e.g., S3 new file, model-drift alarm); use EventBridge Scheduler for time-driven retraining; chain with EventBridge Pipes |
| 46 | [CI/CD — CodePipeline + CodeBuild + CodeDeploy + CodeArtifact](part_h_monitoring_governance/46_codepipeline_codebuild.md) | Build a model-build / model-deploy pipeline with CodePipeline; write `buildspec.yml`; configure CodeDeploy canary deployments for SageMaker endpoints |
| 47 | [Infrastructure as code — CloudFormation, CDK, SageMaker Projects](part_h_monitoring_governance/47_iac.md) | Author CloudFormation/CDK for a full ML stack (S3 + IAM role + SageMaker model + endpoint + alarms); use SageMaker Projects MLOps templates; manage drift |

---

## Part I — Monitoring, Drift & Governance  *(Domain 4, weight 24%)*

| # | Chapter | What you'll be able to do after |
|---|---------|---------------------------------|
| 48 | [SageMaker Model Monitor — the four monitor types](part_i_security_iam_networking/48_model_monitor.md) | Configure Data Quality, Model Quality, Bias Drift, Feature Attribution Drift monitors; create baseline jobs; schedule monitoring; emit CloudWatch metrics |
| 49 | [Drift fundamentals — covariate, label, concept](part_i_security_iam_networking/49_drift_fundamentals.md) | Distinguish covariate shift / label shift / concept drift; compute KL divergence, PSI, Wasserstein, KS test; map detection technique to drift type |
| 50 | [CloudWatch, X-Ray, CloudTrail for ML observability](part_i_security_iam_networking/50_cloudwatch_xray_cloudtrail.md) | Set up CloudWatch dashboards + alarms for endpoint metrics; trace with X-Ray; use CloudTrail Lake to query control-plane events |
| 51 | [SageMaker Model Registry, Model Cards, Lineage](part_i_security_iam_networking/51_registry_cards_lineage.md) | Register model packages with approval workflows; populate Model Cards; query Lineage; build a multi-account model-promotion pattern |
| 52 | [A/B testing & shadow variants in production](part_i_security_iam_networking/52_ab_shadow_testing.md) | Run statistically valid A/B tests on production traffic; configure shadow variants for risk-free comparison; promote winners |

---

## Part J — Security, IAM, Networking & Cost Optimization  *(Domain 4, weight 24%)*

| # | Chapter | What you'll be able to do after |
|---|---------|---------------------------------|
| 53 | [The least-privilege ML execution role](part_j_ai_services_genai/53_least_privilege_role.md) | Construct a SageMaker execution role with only the permissions you need; debug `AccessDenied`; partition S3 paths by purpose; use SCPs for org-wide guardrails |
| 54 | [Network isolation for ML — VPC-only Studio, private endpoints](part_j_ai_services_genai/54_network_isolation.md) | Configure a VPC-only Studio domain; use interface endpoints to keep SageMaker API traffic off the public internet; turn on `EnableNetworkIsolation` for training and endpoints; build a no-egress training environment |
| 55 | [Encryption end-to-end — KMS keys across the ML lifecycle](part_j_ai_services_genai/55_encryption_lifecycle.md) | Wire KMS CMKs for: S3 inputs/outputs, EBS volumes on training instances, EFS/FSx training data, model artifacts, endpoint volumes, inter-container traffic |
| 56 | [Compliance & data residency — PII, PHI, GDPR, HIPAA](part_j_ai_services_genai/56_compliance.md) | Identify PII/PHI in datasets with Macie + Comprehend PII detection + DataBrew; configure anonymization/masking; enforce data-residency via region selection + Glacier Vault Lock + Macie |
| 57 | [Cost optimization — Spot, Reserved, Savings Plans, right-sizing](part_j_ai_services_genai/57_cost_optimization.md) | Apply Spot to training, Savings Plans to inference, right-size with Compute Optimizer + Inference Recommender; build a tagging strategy that powers Cost Explorer dashboards |
| 58 | [Observability for cost — Cost Explorer, Budgets, Trusted Advisor](part_j_ai_services_genai/58_cost_observability.md) | Build per-team, per-model cost dashboards; set cost-anomaly alarms; configure Budgets actions; interpret Trusted Advisor checks |

---

## Part K — AWS AI Services & Generative AI  *(supports Domain 2 + Domain 3)*

| # | Chapter | What you'll be able to do after |
|---|---------|---------------------------------|
| 59 | [The "which AI service?" decision tree](part_k_capstone/59_ai_services_decision_tree.md) | Given a business problem, name the right AWS AI service in one step: sentiment → Comprehend; OCR → Textract; recs → Personalize; fraud → Fraud Detector; vision → Rekognition; voice → Polly/Transcribe; translation → Translate; predictive maintenance → Lookout for Equipment; vector search → OpenSearch + Bedrock KB |
| 60 | [Amazon Bedrock — the foundation-model platform](part_k_capstone/60_bedrock_platform.md) | Use Bedrock Converse API with Claude/Llama/Titan/Nova; configure provisioned throughput vs on-demand; set up Guardrails; build with Bedrock Agents and Knowledge Bases |
| 61 | [Generative AI patterns on AWS — RAG, fine-tuning, agents](part_k_capstone/61_genai_patterns.md) | Architect a RAG pipeline: ingestion → embeddings → vector store (OpenSearch / pgvector / Pinecone) → retriever → Bedrock LLM → Guardrails; choose RAG vs fine-tune vs continued pre-training |
| 62 | [Bedrock vs SageMaker JumpStart — when each wins](part_k_capstone/62_bedrock_vs_jumpstart.md) | Decide: API simplicity + multi-model (Bedrock) vs control + custom training (JumpStart); compare pricing models; reason about data privacy and customization depth |

---

## Part L — Capstone & Exam Strategy

| # | Chapter | What you'll be able to do after |
|---|---------|---------------------------------|
| 63 | [End-to-end project — fraud-detection ML pipeline on AWS](part_k_capstone/63_capstone_project.md) | Architect, implement (in pseudocode + IaC), and operate a full production ML system: ingest from Kinesis, prep with Glue, train with SageMaker XGBoost + AMT, deploy to a real-time endpoint behind API Gateway, monitor with Model Monitor, retrain on drift via EventBridge → Pipelines |
| 64 | [Exam-day strategy + self-assessment](part_k_capstone/64_exam_strategy.md) | Pace yourself (1m 56s per scored question); recognize question-pattern archetypes; manage multi-response and ordering questions; build a self-assessment checklist mapped to all 12 task statements |

---

The chapters are numbered consecutively (1 through 64) and intended to be read in order — later chapters assume earlier ones. Each chapter ends with **exercises** (do them cold before moving on) and **mermaid diagrams** for architectures and decision trees. Exam-flavored gotchas are called out inline with **⚠️ Exam alert** boxes.

After Topic 14, the **Practice Exam** (500 questions, weighted to match the four domains: 140 / 130 / 110 / 120) lives at [practice_exam/](practice_exam/) — served by a Flask + waitress production WSGI app you can run locally.
