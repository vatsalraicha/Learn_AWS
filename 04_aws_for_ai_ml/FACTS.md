# Topic 04 — FACTS.md

> Atomic, citable facts. Single source of truth for numbers, dates, model names, GA/retirement events, and exam metadata.
>
> **Format:** each fact is one line, with citation in square brackets and "last verified" date. If a fact is older than 90 days, re-verify before quoting.
>
> **Last updated:** 2026-05-14 (seed)

---

## Capital One on AWS

- Capital One completed exit from its last on-premises data center in **November 2020** — first US bank 100% all-in on public cloud. [Source: AWS case study + SiliconAngle re:Invent 2020 coverage] [Verified 2026-05-14]
- ~80% of applications were rebuilt cloud-native (microservices + REST) during the migration. [Source: AWS case study] [Verified 2026-05-14]
- Capital One runs both **Snowflake on AWS** and **Databricks on AWS** in production. Their commercial product line (Slingshot, Databolt) targets this combo. [Source: capitalone.com/software/, job postings] [Verified 2026-05-14]
- Capital One self-hosts model serving on **EKS with KServe** — confirmed in their public Lead MLE job posting titled "Lead Machine Learning Engineer (MLOps, KServe — building Kubernetes Clusters, PyTorch, TensorFlow on AWS)". [Source: capitalone.wd12.myworkdayjobs.com R239877] [Verified 2026-05-14]
- **Eno** (Capital One's AI assistant) launched 2017; received LLM upgrade in 2024; added Spanish in 2025; credited with ~50% call-center volume reduction. [Source: capitalone.com/tech/ai/] [Verified 2026-05-14]
- Capital One's internal ML platform team is called **Intelligent Foundations and Experiences (IFX)**. [Source: Lead MLE job posting] [Verified 2026-05-14]
- Compensation bands (McLean, VA, 2026): Sr Lead MLE ~$229k–$262k; Sr Distinguished MLE ~$315k–$359k. [Source: capitalonecareers.com job postings] [Verified 2026-05-14]

## Capital One open-source AWS tooling

- **Cloud Custodian** — YAML policy-as-code rules engine for AWS governance, originally from Capital One, now **CNCF Incubating** (Apache 2.0). Native Security Hub integration. [Source: github.com/cloud-custodian, cncf.io] [Verified 2026-05-14]
- **rubicon-ml** — ML experiment tracking with git integration, designed for auditability and reproducibility in regulated environments. [Source: github.com/capitalone/rubicon-ml] [Verified 2026-05-14]
- **DataProfiler** — schema/stat/entity extraction for sensitive-data scanning; ~1.6k GitHub stars. [Source: github.com/capitalone] [Verified 2026-05-14]
- **datacompy** — Pandas/Polars/Spark/Snowpark dataframe diff library for pipeline validation. [Source: github.com/capitalone/datacompy] [Verified 2026-05-14]
- **locopy** — Redshift + Snowflake load/unload helper. [Source: github.com/capitalone/locopy] [Verified 2026-05-14]
- **Hygieia** — DevOps dashboard; first OSS release at OSCON 2015. [Source: github.com/Hygieia] [Verified 2026-05-14]

## Capital One 2019 breach (compliance context)

- March/April 2019: misconfigured **WAF SSRF** vulnerability + over-permissive IAM allowed exfiltration of ~106 million customer records from S3. [Source: OCC consent order Aug 2020; SEC filings] [Verified 2026-05-14]
- $80M OCC fine (Aug 2020); $190M class-action settlement (Dec 2021). [Source: OCC and DOJ press releases] [Verified 2026-05-14]
- Aftermath shaped Capital One's emphasis on **policy-as-code (Cloud Custodian)**, **tokenization (Databolt)**, and **IaC guardrails (cfn-guard, cdk-nag, CloudFormation hooks)**. [Inference from re:Invent 2024 session content] [Verified 2026-05-14]

## AWS Certification — active (as of 2026-05-14)

| Cert | Code | Level | Cost USD | Duration |
|---|---|---|---:|---|
| Cloud Practitioner | CLF-C02 | Foundational | $100 | 90 min / 65 Q |
| AI Practitioner | AIF-C01 | Foundational | $100 | 90 min / 65 Q |
| Solutions Architect – Associate | SAA-C03 | Associate | $150 | 130 min / 65 Q |
| Machine Learning Engineer – Associate | MLA-C01 | Associate | $150 | 170 min / 85 Q |
| Data Engineer – Associate | DEA-C01 | Associate | $150 | 130 min / 65 Q |
| Solutions Architect – Professional | SAP-C02 | Professional | $300 | 180 min / 75 Q |
| Generative AI Developer – Professional | AIP-C01 | Professional | $300 | ~205 min / 85 Q (GA early 2026) |
| Advanced Networking – Specialty | ANS-C01 | Specialty | $300 | 170 min / 65 Q |
| Security – Specialty | SCS-C03 | Specialty | $300 | 170 min / 65 Q |

[Source: aws.amazon.com/certification/] [Verified 2026-05-14]

## AWS Certification — retired

- **Machine Learning – Specialty (MLS-C01)** — last exam day **March 31, 2026**. Successor: MLA-C01 + AIF-C01 + AIP-C01. [Source: AWS training & certification blog] [Verified 2026-05-14]
- **Data Analytics – Specialty (DAS-C01)** — retired April 2024. Successor: DEA-C01. [Source: AWS training & certification blog] [Verified 2026-05-14]
- **Database – Specialty (DBS-C01)** — retired April 30, 2024. No direct replacement; content absorbed into DEA-C01 + SAP-C02. [Source: AWS training & certification blog] [Verified 2026-05-14]
- **Security – Specialty (SCS-C02)** — retired December 1, 2025. Successor: SCS-C03 (adds GenAI/ML security domain). [Source: AWS training & certification blog] [Verified 2026-05-14]
- All earned certifications remain valid for **3 years** from date earned regardless of retirement. [Source: AWS recertification policy] [Verified 2026-05-14]

## Exam domain weightings (top three for this role)

**SAA-C03 (Solutions Architect Associate):**
- Design Secure Architectures: 30%
- Design Resilient Architectures: 26%
- Design High-Performing Architectures: 24%
- Design Cost-Optimized Architectures: 20%

**MLA-C01 (ML Engineer Associate):**
- Data Preparation for ML: 28%
- ML Model Development: 26%
- ML Solution Monitoring, Maintenance, and Security: 24%
- Deployment and Orchestration of ML Workflows: 22%

**DEA-C01 (Data Engineer Associate):**
- Data Ingestion and Transformation: 34%
- Data Store Management: 26%
- Data Operations and Support: 22%
- Data Security and Governance: 18%

[Source: official AWS exam guide PDFs] [Verified 2026-05-14]

## Hands-on lab budget guidance

- SageMaker Studio Lab — **free**, no AWS account needed. [Source: aws.amazon.com/sagemaker/studio-lab/] [Verified 2026-05-14]
- SageMaker 2-month Free Tier: 250 hrs of `ml.t3.medium`. [Source: aws.amazon.com/sagemaker/pricing/] [Verified 2026-05-14]
- Realistic monthly self-paced lab spend (after free tier): **$75–150/mo** covering SageMaker + Glue + Athena + Bedrock + occasional GPU. NAT Gateway and idle SageMaker endpoints/Studio domains are the three line items that blow up bills. [Source: estimation from AWS calculator + community reports] [Verified 2026-05-14]

## (Module-specific FACTS to be added as modules are written)

— Aurora DSQL GA date, Limitless Database GA date — *to be verified at module 17 write-time*
— DynamoDB on-demand vs provisioned pricing per WCU/RCU — *to be verified at module 18 write-time*
— Glue worker types and pricing — *to be verified at module 14 write-time*
— EKS pricing per cluster ($0.10/hr control plane) — *to be verified at module 33 write-time*
— Bedrock model pricing per 1k input/output tokens — *to be verified at module 42 write-time*
— SageMaker Inference latency SLAs and cold-start numbers — *to be verified at module 37 write-time*
