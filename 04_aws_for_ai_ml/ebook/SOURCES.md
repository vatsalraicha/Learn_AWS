# Appendix — Sources & References

_All material in this ebook was compiled from publicly-available primary sources. Every cited document is archived under `research_inputs/04_aws_for_ai_ml/downloads/` in the project repository so the corpus is self-contained against link rot._

This appendix lists every source consulted, grouped by category.

---

## 1. Capital One — primary sources

### Capital One Tech blog and corporate sites
- **Capital One AWS Case Study** — https://aws.amazon.com/solutions/case-studies/innovators/capital-one/
- **Capital One Tech — re:Invent 2024 roundup** — https://www.capitalone.com/tech/cloud/aws-reinvent-2024/
- **Capital One Tech — AI page** — https://www.capitalone.com/tech/ai/
- **Capital One Tech — serverless streaming SDK pattern** — https://www.capitalone.com/tech/cloud/serverless-streaming/
- **Capital One Software — Databolt for AWS** — https://www.capitalone.com/software/products/databolt/aws/
- **Capital One Software — Slingshot (Snowflake cost governance)** — https://www.capitalone.com/software/products/slingshot/

### Capital One open-source projects (read the code to learn their idioms)
- **Cloud Custodian** (CNCF Incubating, originally from Capital One) — https://github.com/cloud-custodian/cloud-custodian — docs at https://cloudcustodian.io/docs/
- **rubicon-ml** (model experiment tracking with git lineage) — https://github.com/capitalone/rubicon-ml
- **DataProfiler** (sensitive-data scanning) — https://github.com/capitalone/DataProfiler
- **datacompy** (dataframe diff) — https://github.com/capitalone/datacompy
- **locopy** (Redshift + Snowflake load/unload) — https://github.com/capitalone/locopy
- **edgetest** (dependency-update testing) — https://github.com/capitalone/edgetest
- **Hygieia** (DevOps dashboard, OSCON 2015) — https://github.com/Hygieia

### Capital One job postings (signal what the role expects)
- Sr Lead Machine Learning Engineer (GenAI / Python / AWS) — https://jobs.physicstoday.org/job/41953304/
- Lead Machine Learning Engineer (MLOps, KServe, Building Kubernetes Clusters on AWS) — https://capitalone.wd12.myworkdayjobs.com/Capital_One/job/McLean-VA/Lead-Machine-Learning-Engineer--MLOps--KServe---building-Kubernetes-Clusters--PyTorch--TensorFlow-on-AWS-_R239877-1
- Sr Distinguished Machine Learning Engineer (Personalization) — https://www.capitalonecareers.com/job/mclean/sr-distinguished-machine-learning-engineer-remote-eligible/1732/93650794080

### Conference presentations referenced
- **NVIDIA GTC 2025, Session EXS74442** — "Generative AI Agent Servicing Tool" (Capital One)
- **re:Invent 2024** — Capital One sessions on:
  - "Celebrating 10 years of pioneering serverless" (Catherine McGarvey)
  - "Reduce FM deployment costs and latency with SageMaker" (Grant Gillary)
  - "Control the cost of your generative AI services" (Brent Segner)
  - "Governance and security with infrastructure as code" (Ishu Gupta)
  - "Advancing state-of-the-art science and AI in financial services" (James Montgomery)
  - "AI-driven value" (Prem Natarajan + NVIDIA)

---

## 2. AWS official documentation (archived as PDFs/HTML)

### AWS Well-Architected Framework
- **Well-Architected Framework** (the master) — https://docs.aws.amazon.com/wellarchitected/latest/framework/wellarchitected-framework.html
- **Security Pillar** — https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/
- **Machine Learning Lens** — https://docs.aws.amazon.com/wellarchitected/latest/machine-learning-lens/
- **Generative AI Lens** — https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/
- **Financial Services Industry Lens** — https://docs.aws.amazon.com/wellarchitected/latest/financial-services-industry-lens/

### AWS Reference Architectures
- **AWS Security Reference Architecture (SRA)** — https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/
- **Organizing Your AWS Environment Using Multiple Accounts** — https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/
- **Tagging Best Practices** — https://docs.aws.amazon.com/whitepapers/latest/tagging-best-practices/
- **AWS Control Tower User Guide** — https://docs.aws.amazon.com/controltower/latest/userguide/
- **Landing Zone Accelerator on AWS** — https://aws.amazon.com/solutions/implementations/landing-zone-accelerator-on-aws/
- **AWS Resource Control Policies launch (Nov 2024)** — https://aws.amazon.com/blogs/aws/introducing-resource-control-policies-rcps-a-new-authorization-policy/

### Networking
- **Amazon VPC Connectivity Options** — https://docs.aws.amazon.com/whitepapers/latest/aws-vpc-connectivity-options/
- **Hybrid Connectivity** — https://docs.aws.amazon.com/whitepapers/latest/hybrid-connectivity/
- **Building Scalable and Secure Multi-VPC Network Infrastructure** — https://docs.aws.amazon.com/whitepapers/latest/building-scalable-secure-multi-vpc-network-infrastructure/
- **Transit Gateway Best Practices** — https://docs.aws.amazon.com/vpc/latest/tgw/tgw-best-design-practices.html
- **Route 53 Routing Policies** — https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-policy.html

### Storage & Lake
- **Amazon S3 User Guide** — https://docs.aws.amazon.com/s3/
- **AWS Lake Formation Developer Guide** — https://docs.aws.amazon.com/lake-formation/
- **AWS Glue Developer Guide** — https://docs.aws.amazon.com/glue/
- **AWS DataZone User Guide** — https://docs.aws.amazon.com/datazone/
- **Amazon EBS User Guide** — https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AmazonEBS.html
- **Amazon EFS User Guide** — https://docs.aws.amazon.com/efs/
- **Amazon FSx for Lustre** — https://docs.aws.amazon.com/fsx/latest/LustreGuide/

### Databases
- **Amazon RDS User Guide** — https://docs.aws.amazon.com/rds/
- **Aurora User Guide** — https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/
- **Aurora DSQL** — https://docs.aws.amazon.com/aurora-dsql/
- **DynamoDB Developer Guide** — https://docs.aws.amazon.com/dynamodb/
- **DocumentDB Best Practices** — https://docs.aws.amazon.com/documentdb/latest/developerguide/best_practices.html
- **DocumentDB Vector Search** — https://docs.aws.amazon.com/documentdb/latest/developerguide/vector-search.html
- **Amazon Keyspaces Developer Guide** — https://docs.aws.amazon.com/keyspaces/
- **ElastiCache User Guide** — https://docs.aws.amazon.com/elasticache/
- **Valkey announcement and adoption** — https://aws.amazon.com/blogs/database/amazon-elasticache-supports-valkey-7-2-with-a-major-price-reduction/
- **MemoryDB User Guide** — https://docs.aws.amazon.com/memorydb/
- **MemoryDB Vector Search** — https://docs.aws.amazon.com/memorydb/latest/devguide/vector-search.html
- **Amazon Redshift Best Practices** — https://docs.aws.amazon.com/redshift/latest/dg/best-practices.html
- **Redshift Zero-ETL** — https://docs.aws.amazon.com/redshift/latest/mgmt/zero-etl-using.html
- **Snowflake on AWS** — https://aws.amazon.com/snowflake/
- **Amazon Athena Performance Tuning** — https://docs.aws.amazon.com/athena/latest/ug/performance-tuning.html
- **Amazon Neptune Best Practices** — https://docs.aws.amazon.com/neptune/latest/userguide/best-practices.html
- **Neptune Analytics** — https://docs.aws.amazon.com/neptune-analytics/latest/userguide/
- **Neptune ML** — https://docs.aws.amazon.com/neptune/latest/userguide/machine-learning.html
- **OpenSearch Vector Search** — https://docs.aws.amazon.com/opensearch-service/latest/developerguide/vector-search.html
- **Aurora pgvector** — https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraPostgreSQL.VectorDB.html

### Streaming
- **Amazon MSK Developer Guide** — https://docs.aws.amazon.com/msk/
- **Amazon Kinesis Data Streams** — https://docs.aws.amazon.com/streams/
- **Amazon Data Firehose** — https://docs.aws.amazon.com/firehose/
- **Amazon Managed Service for Apache Flink** — https://docs.aws.amazon.com/managed-flink/
- **EventBridge Pipes** — https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-pipes.html
- **Streaming Data Solutions on AWS (whitepaper)** — https://docs.aws.amazon.com/whitepapers/latest/streaming-data-solutions-amazon-kinesis/

### Compute
- **EC2 Capacity Blocks for ML** — https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-capacity-blocks.html
- **AWS Lambda Operator's Guide** — https://docs.aws.amazon.com/lambda/latest/operatorguide/
- **Amazon EKS Best Practices Guide** — https://docs.aws.amazon.com/eks/latest/best-practices/
- **Karpenter** — https://karpenter.sh/docs/
- **EC2 Spot Best Practices** — https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-best-practices.html

### SageMaker (the biggest section)
- **SageMaker Developer Guide** — https://docs.aws.amazon.com/sagemaker/
- **SageMaker Best Practices** — https://docs.aws.amazon.com/sagemaker/latest/dg/best-practices.html
- **SageMaker Pipelines Developer Guide** — https://docs.aws.amazon.com/sagemaker/latest/dg/pipelines.html
- **SageMaker Studio (new) Admin Guide** — https://docs.aws.amazon.com/sagemaker/latest/dg/studio-updated.html
- **SageMaker HyperPod** — https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod.html
- **SageMaker Inference Best Practices** — https://docs.aws.amazon.com/sagemaker/latest/dg/inference-recommender.html
- **SageMaker JumpStart** — https://docs.aws.amazon.com/sagemaker/latest/dg/studio-jumpstart.html
- **SageMaker Unified Studio** — https://docs.aws.amazon.com/sagemaker-unified-studio/
- **SageMaker Feature Store** — https://docs.aws.amazon.com/sagemaker/latest/dg/feature-store.html
- **SageMaker Model Monitor** — https://docs.aws.amazon.com/sagemaker/latest/dg/model-monitor.html
- **SageMaker Clarify** — https://docs.aws.amazon.com/sagemaker/latest/dg/clarify-configure-processing-jobs.html
- **SageMaker Distributed Training** — https://docs.aws.amazon.com/sagemaker/latest/dg/distributed-training.html
- **SageMaker Inference Components** — https://aws.amazon.com/blogs/machine-learning/amazon-sagemaker-launches-inference-components/

### Generative AI
- **Amazon Bedrock User Guide** — https://docs.aws.amazon.com/bedrock/
- **Amazon Bedrock Knowledge Bases** — https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html
- **Amazon Bedrock Agents** — https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html
- **Amazon Bedrock Guardrails** — https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html
- **Bedrock pricing** — https://aws.amazon.com/bedrock/pricing/
- **Amazon Nova** — https://aws.amazon.com/nova/
- **Amazon Q Developer** — https://aws.amazon.com/q/developer/
- **Amazon Q Business** — https://aws.amazon.com/q/business/
- **NVIDIA NIM on AWS Marketplace** — https://aws.amazon.com/marketplace/seller-profile?id=c568fe05-e33b-411c-b0ab-047218431da9
- **NVIDIA NeMo Guardrails** — https://github.com/NVIDIA/NeMo-Guardrails

### Databricks on AWS
- **Databricks on AWS — High-level architecture** — https://docs.databricks.com/aws/en/getting-started/high-level-architecture
- **Databricks on AWS — Configure customer-managed VPC** — https://docs.databricks.com/aws/en/security/network/classic/customer-managed-vpc
- **Databricks on AWS — Classic PrivateLink** — https://docs.databricks.com/aws/en/security/network/classic/privatelink
- **Databricks on AWS — Serverless compute plane networking** — https://docs.databricks.com/aws/en/security/network/serverless-network-security/
- **Databricks on AWS — Unity Catalog S3 external location** — https://docs.databricks.com/aws/en/connect/unity-catalog/cloud-storage/s3/
- **AWS Glue Catalog federation to Databricks Unity Catalog** — https://aws.amazon.com/blogs/big-data/access-databricks-unity-catalog-data-using-catalog-federation-in-the-aws-glue-data-catalog/
- **Terraform Databricks Provider** — https://registry.terraform.io/providers/databricks/databricks/latest/docs
- **Mosaic AI Vector Search** — https://docs.databricks.com/aws/en/vector-search/vector-search
- **Databricks pricing** — https://www.databricks.com/product/pricing
- **Amazon EMR Serverless** — https://docs.aws.amazon.com/emr/latest/EMR-Serverless-UserGuide/
- **Amazon EMR on EKS** — https://docs.aws.amazon.com/emr/latest/EMR-on-EKS-DevelopmentGuide/

### Security & Compliance
- **AWS KMS Cryptographic Details** — https://docs.aws.amazon.com/kms/latest/cryptographic-details/
- **AWS Audit Manager User Guide** — https://docs.aws.amazon.com/audit-manager/
- **AWS GuardDuty** — https://docs.aws.amazon.com/guardduty/
- **AWS Macie** — https://docs.aws.amazon.com/macie/
- **AWS Security Hub** — https://docs.aws.amazon.com/securityhub/
- **AWS Config** — https://docs.aws.amazon.com/config/
- **AWS Inspector** — https://docs.aws.amazon.com/inspector/
- **IAM Access Analyzer** — https://docs.aws.amazon.com/IAM/latest/UserGuide/what-is-access-analyzer.html
- **CloudTrail Lake** — https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-lake.html

### Observability & Cost
- **Amazon CloudWatch User Guide** — https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/
- **AWS X-Ray Developer Guide** — https://docs.aws.amazon.com/xray/
- **AWS Cost Management** — https://docs.aws.amazon.com/cost-management/
- **AWS Cost and Usage Report (CUR 2.0)** — https://docs.aws.amazon.com/cur/
- **AWS Cost Anomaly Detection** — https://docs.aws.amazon.com/cost-management/latest/userguide/manage-ad.html
- **AWS Application Inference Profiles** — https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles.html
- **Application Signals (APM)** — https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Application-Signals.html
- **Amazon Managed Prometheus (AMP)** — https://docs.aws.amazon.com/prometheus/
- **Amazon Managed Grafana (AMG)** — https://docs.aws.amazon.com/grafana/
- **AWS Distro for OpenTelemetry (ADOT)** — https://aws-otel.github.io/
- **FOCUS 1.0 (FinOps Open Cost Specification)** — https://focus.finops.org/

---

## 3. AWS Certifications (official exam guides)

All retrieved from `https://aws.amazon.com/certification/` portal as of 2026-05.

- **AWS Certified Cloud Practitioner (CLF-C02)** — https://aws.amazon.com/certification/certified-cloud-practitioner/
- **AWS Certified AI Practitioner (AIF-C01)** — https://aws.amazon.com/certification/certified-ai-practitioner/
- **AWS Certified Solutions Architect – Associate (SAA-C03)** — https://aws.amazon.com/certification/certified-solutions-architect-associate/
- **AWS Certified Machine Learning Engineer – Associate (MLA-C01)** — https://aws.amazon.com/certification/certified-machine-learning-engineer-associate/
- **AWS Certified Data Engineer – Associate (DEA-C01)** — https://aws.amazon.com/certification/certified-data-engineer-associate/
- **AWS Certified Solutions Architect – Professional (SAP-C02)** — https://aws.amazon.com/certification/certified-solutions-architect-professional/
- **AWS Certified Generative AI Developer – Professional (AIP-C01)** — https://aws.amazon.com/certification/certified-generative-ai-developer-professional/
- **AWS Certified Advanced Networking – Specialty (ANS-C01)** — https://aws.amazon.com/certification/certified-advanced-networking-specialty/
- **AWS Certified Security – Specialty (SCS-C03)** — https://aws.amazon.com/certification/certified-security-specialty/
- **AWS Certification retirements and launches blog** — https://aws.amazon.com/blogs/training-and-certification/aws-certification-retirements-and-launches/

---

## 4. Regulatory and standards documents

- **OCC Consent Order against Capital One (Aug 2020)** — public document
- **FFIEC Cloud Computing Statement (June 2020)** — Federal Financial Institutions Examination Council
- **SR 11-7 — Federal Reserve / OCC Guidance on Model Risk Management** (with 2026 revision SR 26-02)
- **PCI-DSS v4.0** (active Mar 2024, mandatory Mar 2025) — PCI Security Standards Council
- **GLBA Safeguards Rule** (FTC, 2023 update) — https://www.ftc.gov/legal-library/browse/rules/safeguards-rule
- **FedRAMP Documentation** — https://www.fedramp.gov/
- **NIST 800-53** — https://csrc.nist.gov/Projects/risk-management/sp800-53-controls

---

## 5. Open-source projects referenced

- **Cloud Custodian (CNCF Incubating)** — https://github.com/cloud-custodian/cloud-custodian
- **KServe** — https://github.com/kserve/kserve
- **Karpenter** — https://github.com/aws/karpenter-provider-aws
- **KEDA (Kubernetes Event-Driven Autoscaling)** — https://keda.sh/
- **NVIDIA NeMo Guardrails** — https://github.com/NVIDIA/NeMo-Guardrails
- **NVIDIA Triton Inference Server** — https://github.com/triton-inference-server/server
- **Apache Iceberg** — https://iceberg.apache.org/
- **Apache Hudi** — https://hudi.apache.org/
- **Delta Lake** — https://delta.io/
- **Apache Spark** — https://spark.apache.org/
- **Apache Kafka** — https://kafka.apache.org/
- **Valkey** (open-source Redis fork) — https://valkey.io/
- **rubicon-ml** — https://github.com/capitalone/rubicon-ml
- **Istio** — https://istio.io/
- **OpenTelemetry** — https://opentelemetry.io/
- **MLflow** — https://mlflow.org/

---

## 6. Internal research reports (in this repository)

The 14 deep-research reports under `research_inputs/04_aws_for_ai_ml/` that drove each Part:

| # | Report | Covers Modules |
|---|---|---|
| 00 | Capital One AWS usage | CAPITAL_ONE.md |
| 01 | AWS Certification landscape (May 2026) | 57 |
| 02 | AWS Foundations | 1–4 |
| 03 | Networking deep dive | 5–9 |
| 04 | Storage & data lake | 10–12 |
| 05 | Glue & ETL orchestration | 13–15 |
| 06a | Relational + DynamoDB | 16–18 |
| 06b | NoSQL siblings (DocumentDB, Keyspaces, ElastiCache, MemoryDB) | 19–21 |
| 06c | Analytical + Vector + Graph DBs | 22–27 |
| 07 | Streaming (MSK + Kinesis) | 28–29 |
| 08 | Compute for ML | 30–33 |
| 09 | SageMaker | 34–41 |
| 10 | Generative AI on AWS | 42–44 |
| 11 | Databricks on AWS | 45–49 |
| 12 | Security & Compliance | 50–52 |
| 13 | MLOps & Capital One patterns | 53–55 |
| 14 | Observability & cost | 56 |
| 15 | Cert roadmap synthesis | 57 |

Each report contains a full citations section with archived primary-source URLs.

---

## 7. Books, papers, and additional references

- **Mark Brooker** — "Stable and Predictable Distributed Locks" / Aurora design papers (referenced for Aurora Limitless and DSQL background)
- **Pat Helland** — papers on consistency and distributed systems (Aurora DSQL background)
- **The Phoenix Project** + **The Unicorn Project** (Gene Kim) — DevOps culture context
- **AWS re:Invent 2024 session recordings** — Capital One session list (see Section 1)
- **HBR sponsored piece (2021)** — "From Data to Insights: The Capital One Journey" — https://hbr.org/sponsored/2021/06/from-data-to-insights-the-capital-one-journey

---

## 8. About archived documents

Every URL listed in this appendix has a corresponding file archived under `research_inputs/04_aws_for_ai_ml/downloads/` in the project repository:

```
research_inputs/04_aws_for_ai_ml/downloads/
├── aws_whitepapers/      # Well-Architected pillars, IAM, S3, Lambda, EKS, SageMaker, Bedrock, etc.
├── capital_one/          # AWS case study, Tech blog posts, Databolt product page
├── certs/                # 7 AWS exam guide PDFs
├── databricks_on_aws/    # Architecture, PrivateLink, UC, EMR docs
├── oss_tooling/          # Cloud Custodian, rubicon-ml, KServe, Karpenter
├── regulatory/           # OCC consent order, FFIEC, SR 11-7, PCI-DSS
└── INDEX.md              # Manifest mapping each file to its source URL + retrieval date + citing modules
```

**~162 files, all retrieved 2026-05-14 to 2026-05-15.** Refer to `INDEX.md` for the canonical mapping.

---

## 9. Caveats

- **AWS feature velocity is high.** Re-verify any GA dates, pricing numbers, and exam-content domains at write-time. The `FACTS.md` companion file in this topic tracks "last verified" dates per fact.
- **Some primary-source PDFs have moved or been deprecated** since archival. Where the original URL returns 404 (e.g., the SR 11-7 PDF was superseded by SR 26-02 in 2026), the archived file in `downloads/` remains as the corpus's authoritative copy of the version cited.
- **Capital One's actual internal architecture is not public.** This ebook synthesizes from public talks, job postings, open-source projects, and reasonable inference from their public engineering blog. Specifics may differ from internal reality.
- **The 2019 Capital One breach** is referenced extensively as a teaching case study. The architectural lessons are well-documented in the OCC consent order and SEC filings. The treatment in this ebook is non-attribution where possible — the patterns are now industry-wide best practices.

---

_End of ebook._
