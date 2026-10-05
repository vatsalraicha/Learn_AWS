# Module 57 — AWS Cert Paths for Sr Lead AI/ML

> **What this is:** the cert sequence (SAA → MLA → DEA → SCS → SAP → AIP), domain-to-module mapping, study plan, hands-on lab budget, exam-day strategy, recertification policy.

---

## 1. Recommended sequence

| # | Cert | Code | Why now |
|---|---|---|---|
| 1 | **Solutions Architect – Associate** | SAA-C03 | Recruiter-scannable baseline |
| 2 | **Machine Learning Engineer – Associate** | MLA-C01 | Strongest AI/ML signal (replaces retired MLS-C01) |
| 3 | **Data Engineer – Associate** | DEA-C01 | Glue/Redshift/Athena/Streaming credibility |
| 4 | **Security – Specialty** | SCS-C03 | Regulated-finance differentiator (Dec 2025 refresh adds GenAI) |
| 5 | **Solutions Architect – Professional** | SAP-C02 | EM / Architect track promotion lever |
| 6 | **Generative AI Developer – Professional** | AIP-C01 | Capstone for AI Architect targeting RAG/Bedrock/agents |

**Skip**: AIF-C01 (beneath your level), ANS-C01 (SAP covers enough networking).

## 2. Domain-to-module mapping

### SAA-C03 (Solutions Architect Associate)

| Domain | Weight | Modules |
|---|---|---|
| Design Secure Architectures | 30% | 1, 2, 6-9, 50, 51 |
| Design Resilient Architectures | 26% | 3, 6, 8, 9, 16-18 |
| Design High-Performing Architectures | 24% | 10-14, 22, 28-33 |
| Design Cost-Optimized Architectures | 20% | 4, 56 |

### MLA-C01 (ML Engineer Associate)

| Domain | Weight | Modules |
|---|---|---|
| Data Preparation for ML | 28% | 11-15, 27, 35 |
| ML Model Development | 26% | 36, 39 |
| Deployment and Orchestration | 22% | 15, 37, 38 |
| ML Solution Monitoring, Maintenance, Security | 24% | 2, 38, 41, 50, 56 |

### DEA-C01 (Data Engineer Associate)

| Domain | Weight | Modules |
|---|---|---|
| Data Ingestion and Transformation | 34% | 13-15, 28, 29 |
| Data Store Management | 26% | 10-12, 16-27 |
| Data Operations and Support | 22% | 4, 15, 24, 56 |
| Data Security and Governance | 18% | 2, 12, 50-52 |

### SCS-C03 (Security Specialty)

| Domain | Weight | Modules |
|---|---|---|
| Threat Detection and Incident Response | 14% | 50, 52 |
| Security Logging and Monitoring | 18% | 7, 50, 56 |
| Infrastructure Security | 20% | 6-9, 50, 51 |
| Identity and Access Management | 16% | 2, 50, 51 |
| Data Protection | 18% | 10, 50, 52 |
| Management and Security Governance | 14% | 1, 51, 52 |

**Dec 2025 refresh:** the SCS-C03 added an explicit "Implement protections and guardrails for generative AI applications (GenAI OWASP Top 10 for LLM Applications)" task statement under Domain 3.2. **This is brand new and most third-party prep courses haven't caught up.** Supplement with AWS re:Inforce 2025 talks.

### SAP-C02 (Solutions Architect Professional)

| Domain | Weight | Modules |
|---|---|---|
| Design for Org Complexity | 26% | 1, 2, 8 |
| Design for New Solutions | 29% | All Part C-N modules apply |
| Continuous Improvement for Existing Solutions | 25% | 4, 56, 51 |
| Accelerate Workload Migration & Modernization | 20% | 16, 17, 22 |

## 3. Study plan (46-week ladder)

| Cert | Weeks | Hours/week |
|---|---|---|
| **SAA-C03** | 4-6 | 10-12 |
| **MLA-C01** | 4-6 | 10-12 |
| **DEA-C01** | 3-5 (overlap with MLA) | 10-12 |
| **SCS-C03** | 4-6 | 10-12 |
| **SAP-C02** | 8-10 | 12-15 |
| **AIP-C01** | 4-6 (after GA stabilizes) | 10-12 |
| **Total** | ~9-12 months part-time | |

## 4. Hands-on lab plan per cert

### SAA-C03
Deploy a multi-tier app:
- VPC + public/private subnets across 3 AZs.
- ALB → ECS Fargate or Lambda → Aurora Postgres.
- S3 for static assets + CloudFront.
- IAM roles for each tier.

### MLA-C01
End-to-end SageMaker pipeline:
- Glue ETL → Feature Store ingest.
- SageMaker Training Job (PyTorch or built-in).
- SageMaker Pipeline orchestrating preprocessing → train → evaluate → register.
- Real-time endpoint deployment + Model Monitor.

### DEA-C01
Lake house:
- Glue crawlers + ETL into S3 Iceberg.
- Lake Formation FGAC.
- Athena queries + Redshift Spectrum.
- Kinesis Firehose for streaming ingest.

### SCS-C03
Multi-account security:
- Control Tower or LZA landing zone.
- Cloud Custodian policies (encryption enforcement, tag enforcement).
- KMS CMKs with rotation.
- Security Hub conformance pack (PCI-DSS).
- GuardDuty + Macie + Inspector enabled.

### SAP-C02
Multi-region landing zone:
- Transit Gateway hub-spoke.
- DMS / MGN-style migration scenario.
- Multi-region active-passive failover.
- Network Firewall + egress filtering.

## 5. Hands-on lab budget

- **SageMaker Studio Lab** — free (no AWS account).
- **SageMaker Free Tier** — 2 months × 250 hours `ml.t3.medium`.
- **Realistic monthly spend after free tier**: $75-150/month.
- Biggest line items to watch: NAT GW, idle SageMaker endpoints/Studio domains, idle EKS clusters, Capacity Blocks.

**Discipline:** AWS Budgets alert at $100; `terraform destroy` after each lab session.

## 6. Mock-exam strategy

Two highest-signal resources:
- **Tutorials Dojo** — practice exams.
- **AWS Skill Builder Exam Prep** — official AWS-aligned questions.

Readiness gates: **78-82% on Tutorials Dojo** sustained across multiple practice tests indicates real-exam readiness.

Other useful: Stephane Maarek Udemy (well-paced), Adrian Cantrill (deep-dive video courses).

## 7. Exam-day strategy

- **Pearson VUE in-person testing center** > online proctoring (fewer issues, less stress).
- **Time per question budgets**:
  - SAA-C03 (130 min / 65 Q): ~2 min/question.
  - MLA-C01 (170 min / 85 Q): ~2 min/question.
  - SAP-C02 (180 min / 75 Q): **2.4 min/question** — this is the real bottleneck.
- **Flag and return** — flag any question you spend > 3 min on; return after first pass.
- **Elimination heuristics** — AWS exam answers typically eliminate two wrong answers easily (clearly out of scope, deprecated, wrong service). Pick between the remaining two.

## 8. Recertification

- **3-year validity** from date earned.
- **Auto-recert via higher-tier cert** — passing SAP-C02 automatically recerts SAA-C03 for another 3 years.
- **Skill Builder Recertification Assessment** — alternative to re-taking; shorter free assessment.

**Stacking play:** time DEA-C01 right after MLA-C01 so they both recert together when you take SAP-C02. Maximizes cert-window coverage with minimum exam re-takes.

## 9. Pitfalls

- **Skipping SAA-C03** — common mistake. It's the recruiter-scannable baseline.
- **Studying too much theory, not enough hands-on**.
- **Mock-exam % bias** — Tutorials Dojo tends to track AWS exam difficulty; if you're below 78%, you're not ready.
- **Going straight to Professional** without Associate foundation — possible but high-risk.

## 10. The Capital One signal

Job postings don't strictly require certs but list AWS Solutions Architect Pro + AWS ML Specialty as fit. With MLS-C01 retired, **the modern signal is SAA + MLA + DEA + SCS**, then SAP for AI Architect / EM tracks.

Cloud Custodian familiarity is a separate cultural plus that no cert covers.

## 11. Sanity check

1. What replaced MLS-C01?
2. What's new in SCS-C03's Dec 2025 refresh?
3. SAP-C02 bottleneck — what is it?
4. What's the auto-recert-via-higher-tier play?
5. What's the budget alarm threshold you'd set for self-paced labs?

## 12. Cross-references

- **CAPITAL_ONE.md** — section 7 lists Capital One hiring-bar cert priorities
- **FACTS.md** — exam costs, durations, retirement dates
- All modules in this topic — feed into one or more cert domains

## Primary sources

- All exam guide PDFs in [`downloads/certs/`](../../research_inputs/04_aws_for_ai_ml/downloads/certs/)
- AWS Skill Builder pages (archived)
- Research reports: [`01_certification_landscape.md`](../../research_inputs/04_aws_for_ai_ml/01_certification_landscape.md) and [`15_cert_roadmap_synthesis.md`](../../research_inputs/04_aws_for_ai_ml/15_cert_roadmap_synthesis.md)
