# Topic 04 — AWS for AI/ML Engineers — Table of Contents

> Master index. All 57 modules complete.
>
> **Last updated:** 2026-05-15

## Top-level

- [`README.md`](README.md) — Overview, learning path, scope, stack baseline
- [`FACTS.md`](FACTS.md) — Atomic citable facts (service GA dates, costs, retirements, C1 OSS repos)
- [`CAPITAL_ONE.md`](CAPITAL_ONE.md) — **Curated Capital One dossier (interview/role prep)**

---

## Modules

### Part A — AWS foundations
- [Module 1 — AWS account, org & landing-zone model](01_account_org_landing_zone.md)
- [Module 2 — IAM deep](02_iam_deep.md)
- [Module 3 — Regions, AZs, edge](03_regions_azs_edge.md)
- [Module 4 — Billing, pricing & tagging](04_billing_pricing_tagging.md)

### Part B — Networking from zero
- [Module 5 — Networking primer for ML engineers](05_networking_primer.md)
- [Module 6 — VPC deep](06_vpc_deep.md)
- [Module 7 — Security groups, NACLs, flow logs](07_sg_nacl_flow_logs.md)
- [Module 8 — Multi-VPC & hybrid (TGW, PrivateLink, DX, VPN)](08_multi_vpc_hybrid.md)
- [Module 9 — DNS, load balancing & edge](09_dns_lb_edge.md)

### Part C — Storage & data lake
- [Module 10 — S3 deep](10_s3_deep.md)
- [Module 11 — EFS, FSx (Lustre), EBS](11_efs_fsx_ebs.md)
- [Module 12 — Lake Formation + Glue Catalog + Iceberg + DataZone](12_lake_governance.md)

### Part D — Glue & ETL orchestration
- [Module 13 — Glue fundamentals](13_glue_fundamentals.md)
- [Module 14 — Glue Spark deep](14_glue_spark_deep.md)
- [Module 15 — ETL orchestration choices](15_etl_orchestration.md)

### Part E — AWS Database services
- [Module 16 — Relational basics (RDS family)](16_rds_relational.md)
- [Module 17 — Aurora deep (Serverless v2, Limitless, DSQL, Babelfish)](17_aurora_deep.md)
- [Module 18 — DynamoDB deep](18_dynamodb_deep.md)
- [Module 19 — DocumentDB deep](19_documentdb_deep.md)
- [Module 20 — Amazon Keyspaces (Cassandra)](20_keyspaces_cassandra.md)
- [Module 21 — ElastiCache & MemoryDB](21_elasticache_memorydb.md)
- [Module 22 — Redshift deep](22_redshift_deep.md)
- [Module 23 — Snowflake on AWS](23_snowflake_on_aws.md)
- [Module 24 — Athena & query federation](24_athena_federation.md)
- [Module 25 — Neptune — graph database](25_neptune_graph.md)
- [Module 26 — OpenSearch — search & vector](26_opensearch.md)
- [Module 27 — Vector capabilities decision framework](27_vector_decision_framework.md)

### Part F — Streaming & event-driven
- [Module 28 — Amazon MSK deep](28_msk_deep.md)
- [Module 29 — Kinesis family + Flink](29_kinesis_flink.md)

### Part G — Compute for ML
- [Module 30 — EC2 & accelerators](30_ec2_accelerators.md)
- [Module 31 — ECS + Fargate + Batch](31_ecs_fargate_batch.md)
- [Module 32 — AWS Lambda deep](32_lambda_deep.md)
- [Module 33 — EKS foundations](33_eks_foundations.md)

### Part H — SageMaker deep
- [Module 34 — SageMaker platform map](34_sagemaker_platform.md)
- [Module 35 — SageMaker data](35_sagemaker_data.md)
- [Module 36 — SageMaker training](36_sagemaker_training.md)
- [Module 37 — SageMaker inference](37_sagemaker_inference.md)
- [Module 38 — SageMaker MLOps](38_sagemaker_mlops.md)
- [Module 39 — SageMaker JumpStart, Canvas, Autopilot](39_jumpstart_canvas_autopilot.md)
- [Module 40 — SageMaker HyperPod](40_hyperpod.md)
- [Module 41 — SageMaker networking & security](41_sagemaker_networking_security.md)

### Part I — Generative AI on AWS
- [Module 42 — Amazon Bedrock](42_bedrock.md)
- [Module 43 — Amazon Q family](43_amazon_q.md)
- [Module 44 — Self-hosted FM training & serving](44_self_hosted_fm.md)

### Part J — Databricks on AWS
- [Module 45 — Databricks on AWS architecture & control plane](45_databricks_aws_architecture.md)
- [Module 46 — Unity Catalog on AWS](46_unity_catalog_aws.md)
- [Module 47 — Databricks networking on AWS](47_databricks_networking.md)
- [Module 48 — EMR vs Databricks decision](48_emr_vs_databricks.md)
- [Module 49 — Databricks-AWS admin & ops](49_databricks_aws_admin.md)

### Part K — Security & compliance
- [Module 50 — AWS security primitives](50_security_primitives.md)
- [Module 51 — Governance & policy-as-code](51_governance_policy_as_code.md)
- [Module 52 — Financial-services compliance lens](52_financial_services_compliance.md)

### Part L — MLOps & C1 patterns
- [Module 53 — The Capital One MLOps spine](53_c1_mlops_spine.md)
- [Module 54 — EKS for ML serving — KServe deep](54_kserve_deep.md)
- [Module 55 — CI/CD for ML on AWS](55_cicd_for_ml.md)

### Part M — Observability & cost
- [Module 56 — Observability & cost for AI workloads](56_observability_cost.md)

### Part N — Certifications & roadmap
- [Module 57 — AWS cert paths for Sr Lead AI/ML](57_cert_roadmap.md)

---

## Quizzes

- [`quizzes/README.md`](quizzes/README.md) — Quiz index
- [Quiz 02 — Networking (Modules 5-9)](quizzes/02_networking.md)
- [Quiz 05 — Databases (Modules 16-27)](quizzes/05_databases.md)
- [Quiz 08 — SageMaker (Modules 34-41)](quizzes/08_sagemaker.md)
- [Quiz 11 — Security & MLOps (Modules 50-55)](quizzes/11_security_mlops.md)
- [Quiz 12 — Observability + Certs (Modules 56-57)](quizzes/12_observability_certs.md)

(Quizzes 01, 03, 04, 06, 07, 09, 10 — pending future expansion)

---

## Code

- [VPC Terraform module (regulated-finance pattern)](code/vpc_terraform.tf)
- [KServe InferenceService (Capital One pattern with Triton + Databolt + Karpenter)](code/kserve_inference_service.yaml)
- [Cloud Custodian policies (C1-style governance)](code/cloud_custodian_policies.yml)
- [SageMaker Pipeline (end-to-end with rubicon-ml + MLflow + Clarify)](code/sagemaker_pipeline.py)

---

## Research inputs

- [`../../research_inputs/04_aws_for_ai_ml/`](../../research_inputs/04_aws_for_ai_ml/) — 14 deep-research reports
- [`../../research_inputs/04_aws_for_ai_ml/downloads/`](../../research_inputs/04_aws_for_ai_ml/downloads/) — 100+ archived primary-source PDFs
- [`../../research_inputs/04_aws_for_ai_ml/downloads/INDEX.md`](../../research_inputs/04_aws_for_ai_ml/downloads/INDEX.md) — manifest

### Research reports

| # | Report | Modules covered |
|---|---|---|
| 00 | [Capital One AWS usage](../../research_inputs/04_aws_for_ai_ml/00_capital_one_aws_usage.md) | CAPITAL_ONE.md |
| 01 | [Certification landscape](../../research_inputs/04_aws_for_ai_ml/01_certification_landscape.md) | 57 |
| 02 | [AWS foundations](../../research_inputs/04_aws_for_ai_ml/02_aws_foundations.md) | 1-4 |
| 03 | [Networking](../../research_inputs/04_aws_for_ai_ml/03_networking.md) | 5-9 |
| 04 | [Storage & data lake](../../research_inputs/04_aws_for_ai_ml/04_storage_data_lake.md) | 10-12 |
| 05 | [Glue & ETL](../../research_inputs/04_aws_for_ai_ml/05_glue_etl.md) | 13-15 |
| 06a | [Relational + DynamoDB](../../research_inputs/04_aws_for_ai_ml/06a_relational_dynamodb.md) | 16-18 |
| 06b | [NoSQL siblings](../../research_inputs/04_aws_for_ai_ml/06b_nosql_siblings.md) | 19-21 |
| 06c | [Analytical + Vector + Graph](../../research_inputs/04_aws_for_ai_ml/06c_analytical_vector_graph.md) | 22-27 |
| 07 | [Streaming](../../research_inputs/04_aws_for_ai_ml/07_streaming.md) | 28-29 |
| 08 | [Compute for ML](../../research_inputs/04_aws_for_ai_ml/08_compute_for_ml.md) | 30-33 |
| 09 | [SageMaker](../../research_inputs/04_aws_for_ai_ml/09_sagemaker.md) | 34-41 |
| 10 | [GenAI on AWS](../../research_inputs/04_aws_for_ai_ml/10_genai_on_aws.md) | 42-44 |
| 11 | [Databricks on AWS](../../research_inputs/04_aws_for_ai_ml/11_databricks_on_aws.md) | 45-49 |
| 12 | [Security & compliance](../../research_inputs/04_aws_for_ai_ml/12_security_compliance.md) | 50-52 |
| 13 | [MLOps & C1 patterns](../../research_inputs/04_aws_for_ai_ml/13_mlops_c1_patterns.md) | 53-55 |
| 14 | [Observability & cost](../../research_inputs/04_aws_for_ai_ml/14_observability_cost.md) | 56 |
| 15 | [Cert roadmap synthesis](../../research_inputs/04_aws_for_ai_ml/15_cert_roadmap_synthesis.md) | 57 |
