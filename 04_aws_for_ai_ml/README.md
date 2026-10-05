# Topic 04 — AWS for AI/ML Engineers (Capital One lens)

> **Audience:** Senior AI/ML Engineer (currently Optum, Azure shop) preparing for **Sr Lead AI/ML Engineer at Capital One** — a 100%-AWS, regulated-finance shop. Already fluent in Python, PySpark, and Azure Databricks (Topic 02). Needs AWS depth, networking from first principles, and an AWS AI/ML certification roadmap.
>
> **Goal:** A teaching corpus that goes beyond marketing — production reality at Capital One specifically, networking taught from zero, deep SageMaker treatment, AWS database breadth (12 dedicated modules), Glue + ETL fluency, streaming/Kafka depth, Kubernetes depth, Lambda depth, and direct mapping to AWS AI/ML certifications.
>
> **Branch:** `topic-04-aws-for-ai-ml`
>
> **Last updated:** 2026-05-14

---

## Promise

Every module is backed by a focused research pass *before* the module is written. Citable facts go to [`FACTS.md`](FACTS.md) with "last verified" dates. Time-sensitive content (pricing, GA, exam domains) is re-verified at write-time, not pulled from memory. Primary-source documents (whitepapers, exam guides, re:Invent decks, Capital One Tech blog posts) are archived under [`../../research_inputs/04_aws_for_ai_ml/downloads/`](../../research_inputs/04_aws_for_ai_ml/downloads/) so the corpus is self-contained.

## Learning path

| # | Module | Why it matters |
|---|--------|----------------|
| **Part A — AWS foundations (1–4)** | | |
| 1 | AWS account, org & landing-zone model | Multi-account topology, Control Tower, SCPs, IAM Identity Center |
| 2 | IAM deep | Users vs roles, STS, permission boundaries, ABAC, IRSA, common footguns |
| 3 | Regions, AZs, edge | Global infrastructure, Local Zones, Outposts, Wavelength |
| 4 | Billing, pricing & tagging | On-demand vs RI vs Savings Plans vs Spot, Cost Explorer, Budgets, cost allocation |
| **Part B — Networking from zero (5–9)** | | |
| 5 | Networking primer for ML engineers | CIDR, subnets, routing, NAT vs IGW, DNS — first principles, zero AWS |
| 6 | VPC deep | Subnets, route tables, IGW, NAT GW, VPC endpoints |
| 7 | Security groups, NACLs, flow logs | Stateful vs stateless, layered defense, troubleshooting |
| 8 | Multi-VPC & hybrid | Peering, Transit Gateway, PrivateLink, Direct Connect, VPN |
| 9 | DNS, load balancing & edge | Route 53, ALB/NLB/GWLB, CloudFront, WAF + Shield |
| **Part C — Storage & data lake (10–12)** | | |
| 10 | S3 deep | Storage classes, S3 Tables/Iceberg, Object Lambda, Access Points |
| 11 | EFS, FSx, EBS | Block + file for ML; FSx for Lustre for training |
| 12 | Lake Formation + Glue Catalog + Iceberg + DataZone | Catalog model, FGAC, RAM, federation |
| **Part D — Glue & ETL orchestration (13–15)** | | |
| 13 | Glue fundamentals | Crawlers, catalog, jobs, DataBrew, bookmarks |
| 14 | Glue Spark deep | DynamicFrame, pushdown, partitioning, Glue 4.0/5.0 |
| 15 | ETL orchestration choices | Step Functions vs MWAA vs EventBridge Pipes vs SM Pipelines vs Glue Workflows |
| **Part E — AWS Database services (16–27)** | | |
| 16 | Relational basics — RDS family | RDS Postgres/MySQL/Oracle/SQL Server, RDS Proxy, Multi-AZ, Blue/Green |
| 17 | Aurora deep | Aurora Serverless v2, Limitless, DSQL, Global Database, Babelfish |
| 18 | DynamoDB deep | Partition keys, GSI/LSI, single-table design, DAX, hot-partition pathologies |
| 19 | DocumentDB deep | MongoDB-compatible, sharding, vector search, change streams |
| 20 | Amazon Keyspaces (Cassandra) | Managed Cassandra, vs DynamoDB, partition design, multi-region |
| 21 | ElastiCache & MemoryDB | Redis/Valkey/Memcached; MemoryDB as durable primary; vector capability |
| 22 | Redshift deep | RA3, Serverless, Spectrum, data sharing, zero-ETL, Redshift ML |
| 23 | Snowflake on AWS | Why C1 picked it, Snowpark, Horizon, Iceberg tables, vs Redshift |
| 24 | Athena & query federation | Athena v3, Iceberg/Hudi/Delta, federated query connectors |
| 25 | Neptune — graph database | Property graph + RDF, Neptune Analytics, Neptune ML, GraphRAG |
| 26 | OpenSearch — search & vector | Serverless, k-NN engines, HNSW vs IVF, hybrid search |
| 27 | Vector capabilities decision framework | pgvector vs DocumentDB vs MemoryDB vs OpenSearch vs Neptune for RAG |
| **Part F — Streaming & event-driven (28–29)** | | |
| 28 | Amazon MSK deep | Kafka on AWS, MSK Serverless, MSK Connect, IAM auth, Schema Registry |
| 29 | Kinesis family + Flink | KDS, Firehose, MSF, EventBridge, EventBridge Pipes; MSK-vs-Kinesis decision |
| **Part G — Compute for ML (30–33)** | | |
| 30 | EC2 & accelerators | G5/G6/P4/P5/P5e, Trainium, Inferentia, EC2 Capacity Blocks, Spot |
| 31 | ECS + Fargate + Batch | Task defs, capacity providers, AWS Batch backends |
| 32 | AWS Lambda deep | Cold starts, container images, SnapStart, concurrency, C1 serverless-first |
| 33 | EKS foundations | Clusters, node groups, VPC CNI, IRSA, Karpenter, EKS Auto Mode |
| **Part H — SageMaker Deep (34–41)** | | |
| 34 | SageMaker platform map | Studio classic vs new, domains, spaces, Unified Studio, 2024–2026 evolution |
| 35 | SageMaker data | Data Wrangler, Feature Store, Processing Jobs, Ground Truth, Clarify |
| 36 | SageMaker training | Distributed, SMDDP, FSDP, spot, Trainium, Heterogeneous Clusters |
| 37 | SageMaker inference | Real-time, serverless, async, batch, MME, inference recommender, shadow |
| 38 | SageMaker MLOps | Pipelines, Projects, Model Registry, Model Monitor, Lineage |
| 39 | SageMaker JumpStart, Canvas, Autopilot | Pretrained model hub + low-code surfaces + AutoML |
| 40 | SageMaker HyperPod | Slurm vs EKS-based, recipes, resilience |
| 41 | SageMaker networking & security | VPC mode, no-internet, KMS, private endpoints, multi-account ML |
| **Part I — Generative AI on AWS (42–44)** | | |
| 42 | Amazon Bedrock | Catalog, Knowledge Bases, Agents, Guardrails, Flows, custom models |
| 43 | Amazon Q family | Developer, Business, Apps, in QuickSight |
| 44 | Self-hosted FM training & serving | NIM/Triton, EC2 Capacity Blocks, NVIDIA AI Enterprise, Nemo Guardrails |
| **Part J — Databricks on AWS (45–49)** | | |
| 45 | Databricks on AWS architecture & control plane | Control plane regions, classic vs serverless, deltas from Azure |
| 46 | Unity Catalog on AWS | S3 backing, instance profiles vs Azure SPs, Lake Formation interop |
| 47 | Databricks networking on AWS | PrivateLink, Secure Cluster Connectivity, BYO VPC |
| 48 | EMR vs Databricks decision | EMR Serverless / EMR on EKS / EMR on EC2 vs Databricks; Photon-on-AWS economics |
| 49 | Databricks-AWS admin & ops | MWS Account API, Terraform provider, billing & DBU economics, audit logs |
| **Part K — Security & Compliance (50–52)** | | |
| 50 | AWS security primitives | KMS, CloudHSM, Secrets Manager, Macie, GuardDuty, Security Hub, Config |
| 51 | Governance & policy-as-code | Control Tower, SCPs, Cloud Custodian (C1 OSS), cfn-guard, cdk-nag |
| 52 | Financial-services compliance lens | PCI-DSS, SOC, FFIEC, OCC, SR 11-7, Databolt-style tokenization, 2019-breach |
| **Part L — MLOps & C1 patterns (53–55)** | | |
| 53 | The Capital One MLOps spine | SageMaker + Step Functions + Glue + EMR + EKS/KServe + rubicon-ml |
| 54 | EKS for ML serving — KServe deep | CRDs, KEDA, Karpenter for GPU, Istio, IRSA, GPU operator |
| 55 | CI/CD for ML on AWS | CodePipeline, GitHub Actions + OIDC, SM Pipelines vs Step Functions, CDK + TF |
| **Part M — Observability & cost (56)** | | |
| 56 | Observability & cost for AI workloads | CloudWatch, X-Ray, Prom/Grafana on EKS, Datadog, GenAI cost discipline |
| **Part N — Certifications & roadmap (57)** | | |
| 57 | AWS cert paths for Sr Lead AI/ML | SAA → MLA → DEA → SCS → SAP → AIP, domain-to-module mapping, study plan |

## Companion files

- [`FACTS.md`](FACTS.md) — atomic citable facts (service GA dates, instance prices, exam costs, retirement dates, C1 OSS repos)
- [`CAPITAL_ONE.md`](CAPITAL_ONE.md) — **curated Capital One dossier** written for interview/role prep
- [`00_Table_Of_Contents.md`](00_Table_Of_Contents.md) — master index of all 57 modules + companion files + quizzes + code
- [`quizzes/`](quizzes/) — grouped per part (~12 quizzes total)
- [`code/`](code/) — Terraform modules, Python SageMaker notebooks, Glue jobs, Step Functions, Cloud Custodian policies, KServe manifests, MSK producer/consumer, Lambda templates
- [`../../research_inputs/04_aws_for_ai_ml/`](../../research_inputs/04_aws_for_ai_ml/) — 17 deep-research reports + [`downloads/`](../../research_inputs/04_aws_for_ai_ml/downloads/) archive of primary-source PDFs

## How to use this

1. **Start with [`CAPITAL_ONE.md`](CAPITAL_ONE.md)** — interview-ready dossier. Read this before any module if you have an interview coming up.
2. Modules **1 → 9** are foundations + networking. If you're weak on networking, do not skip module 5.
3. Modules **10 → 29** cover the data plane: storage, ETL, databases (12 dedicated modules), streaming.
4. Modules **30 → 33** cover compute primitives — read **Lambda (32)** carefully; Capital One is famously serverless-first.
5. Modules **34 → 41** are SageMaker — the longest run in this topic.
6. Modules **42 → 49** cover GenAI + Databricks-on-AWS.
7. Modules **50 → 55** are security, governance, and Capital One MLOps patterns. **EKS+KServe (54)** is the differentiator vs SageMaker-endpoint shops.
8. **Module 57** maps everything you've learned to the cert sequence (SAA → MLA → DEA → SCS → SAP → AIP).

Each module ends with a **Sanity check** (3–5 questions you should be able to answer before moving on). After finishing a module, take its quiz cold (no peeking).

Cross-reference [`FACTS.md`](FACTS.md) anytime you want a number, GA date, or citation. Cross-reference [`CAPITAL_ONE.md`](CAPITAL_ONE.md) when you want a "how does this map to the role I'm interviewing for?" lens.

## Scope notes

- **Cutoff:** content reflects **2025–early 2026** state of the art. AWS ships features fast — `FACTS.md` carries "Last verified" dates.
- **Bias:** AWS-native. Capital One lens for production reality. Regulated-finance lens for compliance. Azure-specific differences from Topic 02 are referenced when meaningful (esp. in Part J Databricks-on-AWS).
- **Anti-bias:** treats marketing critically. Production pain, anti-patterns, and "why teams hit walls" sit alongside the official path.
- **Stack convention:** Anthropic Claude on Bedrock (not OpenAI), Terraform + CDK for IaC, Python first.
- **Networking lens:** assumes zero starting knowledge — first-principles in module 5, building to PrivateLink/Transit Gateway by module 8.
- **Cert mapping:** every module tagged with the exam domain(s) it covers (table in module 57).

## Stack baseline (additions to the project `.venv`)

```
boto3
awscli
sagemaker             # Python SDK
sagemaker-studio
mlflow                # for cross-comparison with Topic 02
anthropic             # Bedrock + direct API parity
langchain-aws         # if/when LangChain examples appear
pyspark
delta-spark
cloud-custodian       # C1 OSS — read the policies
rubicon-ml            # C1 OSS — lineage examples
opensearch-py
pinecone-client       # for cross-comparison only
```

## Research provenance

This corpus is built from 17 deep research reports under [`../../research_inputs/04_aws_for_ai_ml/`](../../research_inputs/04_aws_for_ai_ml/), plus archived primary-source documents under [`../../research_inputs/04_aws_for_ai_ml/downloads/`](../../research_inputs/04_aws_for_ai_ml/downloads/) (AWS whitepapers, exam guides, re:Invent decks, Capital One Tech blog posts, NIST/FFIEC PDFs, arXiv papers, Cloud Custodian and rubicon-ml docs).
