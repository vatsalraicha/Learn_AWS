# Capital One on AWS — Dossier for Sr Lead AI/ML Engineer

> **Audience:** You — preparing for the Sr Lead AI/ML Engineer role at Capital One.
> **Purpose:** A single document you can read before an interview, recruiter call, or architecture discussion to ground yourself in Capital One's AWS reality.
> **Source:** Curated from [`../../research_inputs/04_aws_for_ai_ml/00_capital_one_aws_usage.md`](../../research_inputs/04_aws_for_ai_ml/00_capital_one_aws_usage.md) and continually refined as more research lands.
> **Last updated:** 2026-05-14

---

## Strategic posture in one paragraph

Capital One closed its last on-premises data center in **November 2020**, completing a five-year migration begun in 2015 and becoming the **first US bank to publicly run 100% on public cloud**. They are AWS-only for production — no Azure, no GCP, no hybrid story. Their commercial software arm (Capital One Software) sells **Slingshot** (Snowflake cost governance) and **Databolt** (vaultless tokenization for Redshift / Aurora / RDS / now unstructured GenAI data) — both betting on the AWS + Snowflake + Databricks stack. Their internal culture is "**serverless-first**" (Lambda + Step Functions + Fargate + DynamoDB), and they self-host AI/ML model serving on **EKS with KServe** rather than relying solely on SageMaker endpoints.

---

## 1. Strategic posture & migration history

| Year | Event |
|---|---|
| 2015 | All-in-on-AWS strategy announced |
| 2015 | Hygieia released as their first open-source DevOps tooling (OSCON 2015) |
| 2017 | Eno (AI assistant) launched |
| 2019 | March/April breach: misconfigured WAF SSRF + permissive IAM → ~106M customer records exfiltrated from S3 |
| 2020 (Aug) | OCC $80M fine; consent order outlines failures |
| 2020 (Nov) | Last data center decommissioned; 41 tons of copper recycled |
| 2021 | Capital One Software arm launches; Slingshot enters market |
| 2024 | Eno upgraded to LLM-backed; re:Invent 2024 dominated by C1 sessions on cost-optimizing GenAI, IaC governance, FM deployment, serverless 10-year retrospective |
| 2025 | NVIDIA GTC EXS74442 — Generative AI Agent Servicing Tool; Eno adds Spanish |
| 2026 (Mar) | Databolt expanded to unstructured data for GenAI |

**Implication for you:** Capital One has lived the cloud-native journey at scale longer than almost any other regulated-finance org. They expect that you've internalized the discipline that comes from a 5-year migration and a public breach — not just feature familiarity.

---

## 2. AWS service-by-service map

Each row cites the primary public source. Where multiple talks mention a service, the most authoritative is named.

### Compute & orchestration
| Service | Capital One usage | Source |
|---|---|---|
| **Lambda** | Centerpiece of serverless-first strategy; re:Invent 2024 "10 years of pioneering serverless" with Catherine McGarvey | re:Invent 2024 |
| **Step Functions** | Powers check-processing pipeline (80% latency reduction); orchestrates ML pipelines | re:Invent + tech blog |
| **API Gateway + SAM** | Public API surface for microservices | AWS case study |
| **CodeDeploy** | Gradual 2%/min traffic shifting on Lambda | re:Invent 2024 |
| **Fargate, ECS** | Containers without managing servers; pairs with Lambda | re:Invent 2024 |
| **EKS** | Self-managed Kubernetes — explicit in MLE postings; backs **KServe** model serving | Workday R239877 |
| **Step Functions** | ML orchestration alongside SageMaker Pipelines | C1 Sr Lead MLE JD |

### Data services
| Service | Capital One usage | Source |
|---|---|---|
| **S3** | Primary data lake; target of 2019 breach (now wrapped in Cloud Custodian + KMS + access analyzer + Macie) | universal |
| **DynamoDB** | Operational KV, low-latency transactional store | AWS case study |
| **Aurora, RDS** | Relational, including Postgres + Oracle migration targets | AWS case study |
| **DocumentDB** | Document workloads | AWS case study |
| **Redshift** | Analytic warehouse | tech blog |
| **Snowflake on AWS** | Primary analytics data warehouse per HBR sponsor piece (2021); Slingshot targets it | Capital One Software docs |
| **Databricks on AWS** | ML/data engineering workloads; commercial Slingshot supports it | Sr Platform Eng JD |

### Streaming & event-driven
| Service | Capital One usage | Source |
|---|---|---|
| **Kinesis** | Primary serverless event bus; internal SDK abstracts Kinesis + Lambda source/processing/sink | capitalone.com/tech/cloud/serverless-streaming |
| **MSK / Kafka** | Referenced in patterns; Kinesis is the named production service publicly | tech blog |

### ML/AI
| Service | Capital One usage | Source |
|---|---|---|
| **SageMaker** | Named in re:Invent 2024 ("Reduce FM deployment costs and latency with SageMaker", Grant Gillary); Sr Lead MLE JDs list it explicitly | re:Invent 2024 + JDs |
| **EMR** | Big-data feature engineering | Sr Lead MLE JD |
| **Bedrock** | re:Invent 2024 "Control the cost of your generative AI services" (Brent Segner) | re:Invent 2024 |
| **Amazon Q Business** | Same talk | re:Invent 2024 |
| **QuickSight + Amazon Q** | BI | re:Invent 2024 |
| **EKS + KServe** | Self-hosted model serving — the differentiator | Workday R239877 |

### Networking, IaC, governance
| Service / Tool | Capital One usage | Source |
|---|---|---|
| **Route 53** | Multi-region active-active | AWS case study |
| **CloudFormation + AWS CDK** | Primary IaC for AWS resources | re:Invent 2024 (Ishu Gupta) |
| **cdk-nag** | CDK guardrails | same |
| **cfn-guard** | CloudFormation policy-as-code | same |
| **CloudFormation hooks** | Deployment-time policy enforcement | same |
| **HashiCorp Terraform** | "VPC bones" — networking is Terraform; app stacks are CDK | inference from JDs |

---

## 3. Open-source signals (read the code, learn the idioms)

| Project | Repo | What it reveals about Capital One |
|---|---|---|
| **Cloud Custodian** | [github.com/cloud-custodian](https://github.com/cloud-custodian) | YAML policy-as-code for AWS governance. **CNCF Incubating** (Apache 2.0). C1 enforces guardrails continuously at scale, integrated with Security Hub. *The single most important repo to read before interviewing.* |
| **rubicon-ml** | [github.com/capitalone/rubicon-ml](https://github.com/capitalone/rubicon-ml) | Model experiment tracking with git integration. Designed for **auditability and reproducibility** — a direct response to SR 11-7 model risk management. |
| **DataProfiler** | [github.com/capitalone/DataProfiler](https://github.com/capitalone/DataProfiler) | Schema + statistics + entity extraction for sensitive-data scanning. ~1.6k stars. Used to identify PII before it lands in analytic systems. |
| **datacompy** | [github.com/capitalone/datacompy](https://github.com/capitalone/datacompy) | Dataframe diff across Pandas / Polars / Spark / Snowpark. **Pipeline validation pattern.** |
| **locopy** | [github.com/capitalone/locopy](https://github.com/capitalone/locopy) | Redshift + Snowflake load/unload helper. Direct signal both warehouses are in production. |
| **Hygieia** | [github.com/Hygieia](https://github.com/Hygieia) | DevOps dashboard, OSCON 2015. Their earliest OSS release. |
| **edgetest** | [github.com/capitalone/edgetest](https://github.com/capitalone/edgetest) | Dependency-update testing — supply-chain hygiene. |
| **Stratum-Observability** | github.com/capitalone | Observability instrumentation library. |

**Action:** before any interview, spend 90 minutes reading the Cloud Custodian docs and skimming three example policy YAMLs. You will impress interviewers by referencing the project by name and identifying which AWS APIs Custodian wraps.

---

## 4. AI/ML platform shape

### Products users interact with
- **Eno** — AI assistant, launched 2017 (SMS / Alexa). LLM upgrade in 2024; Spanish in 2025. Credited with ~50% call-center volume reduction.
- **Generative AI Agent Servicing Tool** — internal tool that helps human call-center agents retrieve account info in real time. Presented at **NVIDIA GTC 2025** (session EXS74442) and re:Invent 2024.

### Internal teams
- **Intelligent Foundations and Experiences (IFX)** — the named internal ML platform team per the Lead MLE job posting. This is who you'll work with or near.

### MLOps spine (inferred from public talks + JDs)
1. **Feature engineering**: EMR + Glue + Spark
2. **Experimentation & training**: SageMaker (Training Jobs, Studio) + Databricks (distributed PyTorch / TensorFlow)
3. **Lineage & auditability**: **rubicon-ml**
4. **Orchestration**: Step Functions + Airflow (Kubeflow appears in JDs)
5. **Model serving**: **EKS + KServe** (their differentiator) + SageMaker endpoints (selectively)
6. **Governance**: Cloud Custodian + cfn-guard + cdk-nag + CloudFormation hooks
7. **Observability**: CloudWatch + likely Datadog (industry norm at scale)
8. **Tokenization for PII**: **Databolt** (their own product) — sits between data lake and analytical / ML systems

### Public ML focus areas (per C1 Tech blog)
- **Graph ML for fraud** (Neptune + Neptune ML + custom transformers)
- **NLP for assistants** (Eno + Servicing Tool)
- **Explainable AI** (SR 11-7 alignment)
- **Anomaly detection** (fraud + ops)
- **Privacy-preserving ML**
- **ML at scale** (the platform problems IFX solves)

### University partnerships
- Global graph transformers
- Dynamic customer embeddings

---

## 5. Regulatory & compliance posture

Capital One operates under **PCI-DSS, SOC 2, FFIEC, GLBA, OCC** oversight, plus the structural memory of the **2019 breach**. This shapes every public statement they make about AWS:

| Regulation/Standard | What it constrains | How C1 implements on AWS |
|---|---|---|
| **PCI-DSS** | Cardholder data protection | Network segmentation via VPC + SGs; tokenization (Databolt); KMS for at-rest; TLS for in-transit |
| **SOC 2** | Operational controls | CloudTrail + CloudTrail Lake; Cloud Custodian; Audit Manager |
| **FFIEC** | Federal financial institution exam framework | Multi-region active-active (Route 53); documented recovery objectives |
| **OCC** | Bank supervision (the 2019 breach was their enforcement action) | Cloud Custodian for continuous compliance; IAM Access Analyzer; SCP-enforced guardrails |
| **GLBA** | Customer financial info privacy | Macie for sensitive-data discovery; tokenization |
| **SR 11-7** | Model risk management (Fed/OCC guidance) | **rubicon-ml** for lineage; Model Cards; Clarify for bias; documented validation processes |

### The 2019 breach lessons
The breach was a **misconfigured WAF SSRF** combined with **over-permissive IAM** that allowed an attacker to retrieve EC2 metadata credentials and exfiltrate ~106M customer records from S3. Everything in their public security posture is downstream of this:

- **Cloud Custodian** — *continuous* policy enforcement, not point-in-time audits
- **IMDSv2 enforcement** — the SSRF vector is dead with IMDSv2 token-required mode
- **IAM Access Analyzer** — surface unintended public/cross-account access
- **Macie** — alert if PII ends up in unexpected buckets
- **cfn-guard / cdk-nag / CloudFormation hooks** — catch the misconfiguration *before* deploy
- **Databolt** — even if exfiltrated, tokenized data is useless without the vault

**Interview signal:** if asked about the breach, do not name-drop it as "the Capital One incident." Frame it as: *"the industry learned that SSRF + over-permissive instance profiles is the classic exfiltration chain; IMDSv2 + least-privilege roles + Access Analyzer + tokenization are the layered response."*

---

## 6. 2024–2026 GenAI direction

The most useful single artifact is the re:Invent 2024 round-up page on capitalone.com/tech: https://www.capitalone.com/tech/cloud/aws-reinvent-2024/

| Session theme | Speaker | What it tells you |
|---|---|---|
| Control the cost of your generative AI services | Brent Segner | Bedrock + Q Business cost governance is a *first-class* discipline |
| Reduce FM deployment costs and latency with SageMaker | Grant Gillary | SageMaker is their managed-inference path |
| 10 years of pioneering serverless | Catherine McGarvey | Lambda + Fargate is core to their culture |
| Governance and security with IaC | Ishu Gupta | CDK + cdk-nag + cfn-guard + CloudFormation hooks |
| Advancing state-of-the-art science and AI in financial services | James Montgomery | They invest in research, not just productionizing |
| AI-driven value | Prem Natarajan + NVIDIA | NVIDIA partnership is real (likely G5/P5/Capacity Blocks) |

### GenAI stack signals
- **Bedrock** (managed FMs)
- **Amazon Q Business** (enterprise assistant)
- **EC2 GPU + NVIDIA AI Enterprise** (self-hosted FM workloads)
- **EKS + KServe** (self-hosted model serving)
- **Nemo Guardrails** (named in Sr Distinguished MLE preferred quals)
- **Cost governance** specifically called out as a discipline

### Databolt expanded to unstructured data (March 2026)
This is the most recent public move — they're productizing **"safe data for GenAI"**: keeping PII out of vector indexes, prompt logs, and fine-tuning corpora. If GenAI work is part of your scope, expect Databolt to come up.

---

## 7. Sr Lead AI/ML Engineer — hiring bar

### What three current postings require

| Posting | Tech surface called out |
|---|---|
| **Sr Lead MLE — GenAI/Python/AWS** | Lambda, Step Functions, EMR, SageMaker, S3; HuggingFace; vector DBs; Nemo Guardrails; LLM optimization; AWS Ultraclusters |
| **Lead MLE — MLOps/KServe** | KServe, Kubernetes (self-managed clusters!), PyTorch, TensorFlow on AWS; Kubeflow; Airflow; Docker; CI/CD |
| **Sr Distinguished MLE — Personalization** | Distributed computing 6–10+ years; explainable + responsible AI; production retraining; low-latency event-driven systems |

### Compensation bands (McLean, VA, 2026)
- **Sr Lead MLE**: $229k – $262k
- **Sr Distinguished MLE**: $315k – $359k

### What to study (priority order)
1. **SageMaker** — every component (Training, Inference, Pipelines, Feature Store, Studio). Modules 34-41 in this topic.
2. **EKS + KServe** — Kubernetes for model serving, including IRSA, Karpenter, GPU operator. Modules 33 + 54.
3. **Lambda + Step Functions** — serverless-first patterns. Modules 32, 15.
4. **Networking** — VPC, PrivateLink, NAT GW patterns. Modules 5-9. *You said this is your gap; close it.*
5. **Cloud Custodian** — read policies, write one. Module 51.
6. **Bedrock + cost governance** — Modules 42, 56.
7. **rubicon-ml + Model Cards + Clarify** — model governance for SR 11-7. Module 35, 38.
8. **Databricks on AWS** — UC + PrivateLink + instance profiles. Modules 45-49.

### Cert priorities (rank by signal-to-effort for this specific role)
1. **SAA-C03** — baseline credibility, recruiter-scannable
2. **MLA-C01** — strongest current AI/ML signal
3. **SCS-C03** — regulated-finance differentiator
4. **DEA-C01** — data platform fluency
5. **SAP-C02** — promotion lever toward Architect/EM
6. **AIP-C01** — capstone once stable

### Interview talking points (memorize)
- "I know Capital One has been 100% on AWS since November 2020 — first US bank — and that the migration shaped a serverless-first culture I want to be part of."
- "I've read through Cloud Custodian and understand why policy-as-code is the backbone of compliant infrastructure at scale."
- "I see the EKS + KServe path in your MLE postings — coming from Azure Databricks, I'm interested in how you split workloads between managed SageMaker endpoints and self-hosted KServe."
- "I've followed Databolt's evolution from structured tokenization to unstructured-data support in March 2026 — the GenAI safety story matters."
- "Eno's 2024 LLM upgrade and the Servicing Tool at NVIDIA GTC 2025 show production GenAI at scale in finance — that's the work I want to do."

---

## 8. Open questions to ask in interviews

Things public sources don't fully reveal. Asking *one* of these well demonstrates depth:

1. **"How does the team decide between SageMaker endpoints and KServe-on-EKS for a given model?"** — they have both; the criteria are the interesting part.
2. **"How is Unity Catalog (Databricks on AWS) reconciled with Lake Formation for the same S3 data?"** — there's a known interop tension; how they solve it reveals their data-governance maturity.
3. **"What's the multi-region DR posture for SageMaker training and inference workloads?"** — public talks emphasize active-active for app tier, but ML platform DR is rarely discussed publicly.
4. **"How does rubicon-ml integrate with Model Registry and Model Cards in practice?"** — they're related but not identical; the integration is custom.
5. **"What's the breakdown of Bedrock vs Anthropic-direct vs self-hosted FM usage?"** — they use all three; the proportions reveal their tradeoffs.
6. **"How is Databolt deployed at the data-plane layer — sidecar, library, gateway?"** — implementation detail not public.
7. **"What's Cloud Custodian's coverage of EKS + Kubernetes resources today, given the legacy is AWS-resource policies?"** — Custodian's reach into K8s is evolving.
8. **"How is the IFX platform team structured — federated MLEs embedded in product teams, or centralized platform with self-service?"** — org design tells you what your day-to-day will look like.

---

## 9. Reading list (priority order)

### Must-read before any interview
1. [Capital One AWS case study](https://aws.amazon.com/solutions/case-studies/innovators/capital-one/) — the executive narrative
2. [Capital One Tech — re:Invent 2024 roundup](https://www.capitalone.com/tech/cloud/aws-reinvent-2024/) — 2024 lineup
3. [Capital One Tech — AI page](https://www.capitalone.com/tech/ai/) — Eno + Servicing Tool + ML focus
4. [Capital One Tech — serverless streaming](https://www.capitalone.com/tech/cloud/serverless-streaming/) — internal Kinesis SDK pattern
5. [Cloud Custodian docs](https://cloudcustodian.io/docs/) — at minimum, the AWS provider page and 5 example policies
6. [rubicon-ml README](https://github.com/capitalone/rubicon-ml) — what it tracks, how it integrates with git

### Strongly recommended
7. [Databolt for AWS product page](https://www.capitalone.com/software/products/databolt/aws/) — tokenization story
8. [Capital One open-source org](https://github.com/capitalone) — skim repo names
9. AWS Well-Architected Framework — Machine Learning Lens (PDF) — what AWS officially expects from an ML architect
10. AWS Well-Architected Framework — Security Pillar (PDF) — the foundation for regulated workloads
11. OCC consent order against Capital One (Aug 2020) — what the regulator actually wrote

### Background (if time)
12. Re:Invent 2024 session videos — Brent Segner (GenAI cost), Grant Gillary (FM on SageMaker), Catherine McGarvey (serverless), Ishu Gupta (IaC governance)
13. NVIDIA GTC 2025 session EXS74442 — Generative AI Agent Servicing Tool
14. HBR 2021 piece (sponsored) on Capital One + Snowflake — strategic data architecture narrative

---

## Cross-references in this topic

- Cloud Custodian deep-read: **Module 51** (Governance & policy-as-code)
- KServe + EKS production setup: **Module 33** (EKS foundations) + **Module 54** (KServe deep)
- Databolt-style tokenization patterns: **Module 52** (Financial-services compliance lens)
- rubicon-ml integration: **Module 38** (SageMaker MLOps) + **Module 53** (C1 MLOps spine)
- Snowflake on AWS strategic choice: **Module 23**
- Bedrock cost governance: **Module 42** + **Module 56**
- 2019 breach lessons (IMDSv2, Access Analyzer, etc.): **Module 2** (IAM deep) + **Module 50** (Security primitives) + **Module 52**
- Cert sequence: **Module 57**
