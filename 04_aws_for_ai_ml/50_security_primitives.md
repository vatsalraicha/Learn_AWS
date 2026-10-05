# Module 50 — AWS Security Primitives

> **What this is:** KMS, CloudHSM, Secrets Manager, Parameter Store, Macie, GuardDuty, Inspector, Security Hub, Config, IAM Access Analyzer, CloudTrail Lake.

---

## 1. KMS (Key Management Service)

The cryptographic foundation.

**Key types:**
- **AWS Owned** — invisible; AWS manages, no charge. Used by default for some services.
- **AWS Managed** — visible (`aws/s3`, `aws/rds`), AWS owns rotation. Free.
- **Customer Managed Keys (CMKs)** — you create, control policy, rotate. **Required for PCI-DSS-scoped data.**

**Key sym/asym:**
- **Symmetric** — most common; encrypt/decrypt.
- **Asymmetric** — sign/verify (RSA, ECC, SM2), encrypt/decrypt.
- **HMAC** — MAC keys for authentication.

**Multi-region keys** — replicate a key to other regions for cross-region encryption with the same key ID.

**Envelope encryption** — encrypt a Data Encryption Key (DEK) with KMS; encrypt actual data with DEK. KMS only ever sees the DEK. **This is how S3 SSE-KMS and Bucket Keys work.**

**Key policies vs IAM policies** — both must allow the action. **The biggest KMS pitfall**: thinking IAM alone is sufficient. Key policy must explicitly allow the principal (or `kms:ViaService`).

**Rotation** — automatic annual rotation for AWS-managed (free); customer-managed can be manual or automatic. **2024**: support for shorter rotation periods (down to 90 days).

## 2. CloudHSM

FIPS 140-2 Level 3 HSM, dedicated to you. Use when:
- Regulatory requirement for **single-tenant** hardware.
- Cryptographic operations not supported by KMS.

KMS Custom Key Store can use CloudHSM as backing store. Expensive ($1+/hr per HSM); justify carefully.

## 3. Secrets Manager vs Parameter Store

| | **Secrets Manager** | **SSM Parameter Store** |
|---|---|---|
| Use case | Database passwords, API keys with rotation | App config, non-rotating settings |
| Rotation | Built-in Lambda-based | Manual |
| Cost | $0.40/secret/month + $0.05/10k API calls | Free (Standard); $0.05/advanced parameter/mo + API calls |
| KMS encryption | Yes | Yes |
| **Best for** | **Rotated database creds** | **App config, feature flags** |

## 4. Macie

S3 sensitive-data discovery.

- **150+ identifiers** for PII patterns (SSN, credit card, names, financial account numbers).
- **Automated discovery** (2024) — scans new S3 data automatically.
- **Cost**: per-GB scanned.

Use case: alert if PII lands in unexpected buckets (a post-2019-breach signal).

## 5. GuardDuty

Threat detection across multiple data sources:
- **CloudTrail events**.
- **VPC Flow Logs**.
- **DNS logs**.
- **S3 access patterns**.
- **EKS audit logs** (extended).
- **RDS login events** (extended).
- **Lambda execution patterns** (extended).
- **Runtime Monitoring** (eBPF agent for EKS, ECS, EC2).

**GuardDuty Extended Threat Detection** (GA Dec 2024) — correlates findings across data sources with MITRE ATT&CK mapping.

The detection engine for credential exfiltration patterns (`UnauthorizedAccess:IAMUser/InstanceCredentialExfiltration`).

## 6. Inspector v2

Vulnerability scanning:
- **EC2** — OS package CVEs.
- **ECR** — container image CVEs.
- **Lambda** — function package CVEs + code security.

Integrates with Security Hub.

## 7. Security Hub

**Aggregated security findings** across GuardDuty, Inspector, Macie, IAM Access Analyzer, Config, partner integrations.

- **Conformance packs**: AWS Foundational Security Best Practices, CIS, PCI-DSS, NIST 800-53, etc.
- **Custom insights** — query findings.
- **Auto-remediation** via EventBridge → SSM Automation / Lambda.

The "single pane of glass" for AWS security posture.

## 8. AWS Config

Compliance posture over time.

- **Config Rules** — managed (e.g., `s3-bucket-public-write-prohibited`) or custom (Lambda or Guard).
- **Conformance Packs** — bundles of rules + remediation.
- **Aggregator** — multi-account view.
- **Compliance change history** — point-in-time state of every resource.

## 9. IAM Access Analyzer

(See Module 2 for IAM detail.)

- **External access** — what's reachable from outside the account/org.
- **Unused access** — dormant IAM users/roles/permissions.
- **Custom policy checks** — CI gate for new permissions.
- **Internal access** (2024) — within-org access surface.

## 10. CloudTrail and CloudTrail Lake

**CloudTrail**:
- Captures all AWS API calls.
- Multi-region trail recommended.
- S3 + CloudWatch Logs destinations.
- **Org trail** — captures across all org accounts.

**CloudTrail Lake** (managed event lake):
- SQL queries against captured events.
- 7-year retention.
- Replaces the "CloudTrail to S3 to Athena" pattern.

## 11. 2024-2026 changes

- **GuardDuty Extended Threat Detection** GA Dec 2024.
- **Macie automated discovery** GA 2024.
- **Audit Manager** with new AI/ML, GenAI frameworks.
- **Inspector** code security (2024).
- **KMS rotation periods** down to 90 days.

## 12. Pitfalls

- **KMS key policy vs IAM policy** interaction — both must allow.
- **GuardDuty without all data sources enabled** → blind spots.
- **Secrets Manager rotation Lambda failures** silently — alert on rotation failures.
- **Config aggregator missing accounts** — incomplete compliance picture.

## 13. Capital One lens

Post-2019-breach posture, almost certainly:
- **CMK per LOB** with 90-day rotation.
- **GuardDuty Extended Threat Detection** enabled org-wide.
- **Macie automated discovery** on every S3 bucket.
- **Security Hub** with PCI-DSS + NIST conformance packs.
- **CloudTrail Lake** for forensics.
- **Cloud Custodian** (their OSS) for continuous policy enforcement on top of all this.

## 14. Sanity check

1. KMS key policy vs IAM policy — what's the trap?
2. Secrets Manager vs Parameter Store — when does each win?
3. What does GuardDuty Extended Threat Detection add over plain GuardDuty?
4. Macie's job — when would you use it?
5. Security Hub conformance packs — name three relevant for regulated finance.

## 15. Cross-references

- **Module 2** — IAM (the access principals)
- **Module 51** — Cloud Custodian (policy-as-code on top of these primitives)
- **Module 52** — compliance frameworks

## Primary sources

- [`KMS_Cryptographic_Details.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/KMS_Cryptographic_Details.pdf)
- [`AWS_Audit_Manager_User_Guide.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/AWS_Audit_Manager_User_Guide.pdf)
- Research report: [`12_security_compliance.md`](../../research_inputs/04_aws_for_ai_ml/12_security_compliance.md)
