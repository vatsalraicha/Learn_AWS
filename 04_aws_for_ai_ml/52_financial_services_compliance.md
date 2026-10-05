# Module 52 — Financial-Services Compliance Lens

> **What this is:** PCI-DSS v4 on AWS, SOC, FFIEC, OCC, **SR 11-7 model risk management**, GLBA, Databolt-style tokenization patterns, and the 2019 Capital One breach postmortem mapping each lesson to a specific AWS feature.

---

## 1. The regulatory stack

A US bank operating on AWS must satisfy:

| | What it constrains |
|---|---|
| **PCI-DSS v4.0** | Cardholder data protection (active Mar 31 2024; mandatory Mar 31 2025) |
| **SOC 1/2/3** | Operational controls (AWS provides; you provide on top) |
| **FFIEC** | Federal financial institution exam framework + 2020 cloud computing statement |
| **OCC** | Bank supervision (the 2019 enforcement action against Capital One) |
| **SR 11-7** | Federal Reserve / OCC guidance on **model risk management** |
| **GLBA Safeguards Rule** | Customer financial info privacy (FTC's 2023 update) |

## 2. PCI-DSS v4 on AWS

Shared responsibility:
- **AWS** provides PCI-DSS-certified infrastructure (regions, services).
- **You** configure encryption, access, logging, network segmentation.

Key v4 requirements:
- **4.x** — Encryption at rest and in transit.
- **8.x** — Access control (MFA, no shared credentials).
- **10.x** — Logging and monitoring.

**For a SageMaker workload:** VPC isolation, KMS CMK for S3 + EFS, IAM Identity Center MFA, CloudTrail with file integrity validation.

## 3. SOC reports

In **AWS Artifact**:
- **SOC 1** — financial controls.
- **SOC 2** — security, availability, confidentiality, processing integrity, privacy.
- **SOC 3** — public summary.

Banks consume these from AWS and produce their own to customers/regulators.

## 4. FFIEC Cloud Computing Statement

The FFIEC's joint statement (originally 2020, updated since) on cloud computing for financial institutions. Covers:
- Governance (who owns the cloud relationship).
- Cloud security management.
- Change management.
- Resilience and recovery.
- Audit.

The "compliance baseline" examiners reference.

## 5. OCC supervision

The OCC supervises banks; Capital One was fined **$80M in Aug 2020** in the post-2019-breach consent order. The order specified controls Capital One had to implement — many became broader industry best practice (IMDSv2, IAM Access Analyzer, etc.).

## 6. SR 11-7 — Model Risk Management

Federal Reserve / OCC supervisory guidance on model risk. Three pillars:

1. **Model development** — sound theory, robust validation against alternatives.
2. **Model validation** — independent review (not by model developers).
3. **Governance** — policies, roles, documented risk appetite.

### Mapping to AWS services

| SR 11-7 requirement | AWS feature |
|---|---|
| Documented model purpose, data, methodology | **SageMaker Model Cards** |
| Versioned model artifacts | **Model Registry** |
| Bias and fairness analysis | **Clarify** (bias detection, SHAP) |
| Experiment lineage (which data, code, hyperparams trained which model) | **Lineage Tracking** + **rubicon-ml** (Capital One OSS) |
| Production monitoring for drift | **Model Monitor** |
| Approval gates | **Model Registry approval status** |
| Audit trail | **CloudTrail + CloudTrail Lake** |

This is **the** map for regulated-finance ML engineering. Capital One's rubicon-ml is purpose-built for the experiment-lineage piece.

## 7. GLBA Safeguards Rule (FTC 2023 update)

Required controls for non-bank financial institutions and applicable safeguards for banks:
- Risk assessment.
- Information security program.
- Designated qualified individual.
- Access controls.
- Encryption at rest and in transit.
- MFA.
- Secure development.
- Service-provider oversight.

## 8. Databolt-style tokenization

**Tokenization** replaces sensitive data (credit card numbers, SSNs) with surrogate tokens. The mapping is held in a secure vault.

**Vaulted** — tokens map to vault entries (lookup required).
**Vaultless** — tokens generated algorithmically (often FPE — Format-Preserving Encryption: same length, same characters as original).

**FPE algorithms**: FF1, FF3-1 (NIST-recommended).

**Capital One Databolt** is the vaultless / FPE solution they productized. Designed to:
- Keep raw PCI data **out of analytic systems** entirely.
- Allow downstream queries on tokenized data (joins, filters).
- Preserve formats for compatibility.
- Reduce PCI-DSS audit scope to the tokenization layer.

**Pattern**: Databolt sits **upstream of S3** — raw PAN never lands; only tokens persist.

## 9. The 2019 Capital One breach postmortem

The breach (detail in Module 2):
1. SSRF via misconfigured WAF.
2. IMDSv1 returned EC2 instance role creds.
3. Instance role had over-permissive S3 access.
4. ~106M records exfiltrated.

### Each lesson → AWS feature

| Lesson | Defense |
|---|---|
| SSRF + IMDSv1 | **IMDSv2 required** (now default on new instance types) |
| Over-permissive instance role | **Least privilege + permission boundaries** |
| Bucket policy didn't constrain to org principals | **RCPs (GA Nov 2024)** + `aws:PrincipalOrgID` |
| No detection of unusual S3 access patterns | **GuardDuty Extended Threat Detection** |
| Sensitive data discoverable in compromised bucket | **Macie** + **Databolt tokenization upstream** |
| Public S3 bucket | **Block Public Access** at org level via RCP |

Every regulated-finance AWS architecture review now references the breach (whether named or not).

## 10. AWS Artifact

The portal where you download AWS' compliance reports — SOC, PCI AOC, ISO 27001 audit reports, FedRAMP packages, etc. Required reading for audit packages.

## 11. Capital One lens

Compliance posture inferred from public sources:

- **PCI-DSS scope reduction** via Databolt tokenization upstream.
- **SR 11-7 alignment** via Model Cards + Model Registry + Clarify + rubicon-ml.
- **GLBA Safeguards** mapped to standard AWS controls.
- **FFIEC examiner-ready** architecture artifacts (audit reports, IR runbooks).
- **OCC consent-order controls** integrated and exceeded.

## 12. Sanity check

1. What's the PCI-DSS v4 mandatory date?
2. What are the three SR 11-7 pillars, and what AWS feature maps to each?
3. Vaulted vs vaultless tokenization — what's FPE?
4. Name three controls that would have stopped the 2019 breach.
5. What's in AWS Artifact, and who uses it?

## 13. Cross-references

- **Module 2** — IAM, IMDSv2, breach chain
- **Module 35, 38** — SageMaker Model Cards, Model Registry, Clarify
- **Module 50, 51** — Security primitives + Cloud Custodian
- **Module 53** — Capital One MLOps spine (where rubicon-ml lives)
- **CAPITAL_ONE.md** — breach context

## Primary sources

- [`OCC_2020_Consent_Order_Capital_One.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/regulatory/OCC_2020_Consent_Order_Capital_One.pdf)
- [`FFIEC_Cloud_Computing_Statement.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/regulatory/FFIEC_Cloud_Computing_Statement.pdf)
- [`SR_11-7_Model_Risk_Management.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/regulatory/SR_11-7_Model_Risk_Management.pdf) (2026 revision: SR 26-02)
- [`PCI_DSS_v4_0_Quick_Reference.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/regulatory/PCI_DSS_v4_0_Quick_Reference.pdf)
- Research report: [`12_security_compliance.md`](../../research_inputs/04_aws_for_ai_ml/12_security_compliance.md)
