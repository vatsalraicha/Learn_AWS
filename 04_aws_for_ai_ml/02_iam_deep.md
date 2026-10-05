# Module 2 — IAM Deep

> **What this is:** the IAM model, the six-layer policy evaluation chain, the IMDSv2 / Access Analyzer / IRSA / Pod Identity story, and the 2019 Capital One breach in IAM detail.
>
> **Why it matters:** every Capital One architecture review starts with IAM. The 2019 breach was an IAM failure. Every cert in the recommended ladder (SAA, MLA, DEA, SCS, SAP) tests IAM heavily. As a Sr Lead at Capital One, you will be expected to design role boundaries that survive a regulator audit and to spot over-permissive policies in code review.
>
> **Cert mapping:** SAA-C03 (Security 30%), MLA-C01 (Domain 4 ML Security), DEA-C01 (Data Security 18%), SCS-C03 (heavily), SAP-C02.

---

## 1. The six-layer policy evaluation chain

When a principal makes a request to an AWS API, IAM evaluates a chain in roughly this order:

1. **SCP** — Org-level, bounds member-account principals.
2. **RCP** — Org-level, bounds resource access (GA 2024-11-13).
3. **Resource policy** — Attached to the resource (S3 bucket policy, KMS key policy, IAM role trust policy).
4. **Identity policy** — Attached to the principal (managed, customer-managed, or inline).
5. **Permissions boundary** — Caps the principal's *effective* permissions.
6. **Session policy** — Set at AssumeRole time, scopes further down.

**The rules:**
- The request succeeds **only if every applicable layer allows it**.
- An **explicit deny** anywhere wins. Always.
- **Implicit deny** is the default — if no layer explicitly allows, it's denied.
- **Permissions boundaries do not apply to resource policies** — a bucket policy can still grant access wider than the boundary intends.

## 2. Users, roles, and what to use when

| Construct | Lifetime | Use case |
|---|---|---|
| **IAM User** | Long-lived (access key) | Break-glass + third-party integrations that can't federate. Near zero count in a regulated org. |
| **IAM Role (assumed via STS)** | Short-lived session (1h default, max 12h) | Everything else — humans (via Identity Center), workloads (via IRSA/Pod Identity/IAM Roles Anywhere), cross-account, federation |
| **Managed policy** (AWS-managed) | Versioned by AWS | Quick start; never use `*:FullAccess` in production |
| **Managed policy** (customer-managed) | You version | The default for reusable identity policies |
| **Inline policy** | Anonymous, attached directly | Avoid — no reuse, hard to audit |

## 3. ABAC vs RBAC at scale

**RBAC** = role per persona × per environment. At 600 accounts × 20 personas × 4 environments × 30 services, RBAC explodes combinatorially. Capital One–scale orgs cannot operate it.

**ABAC** tags principals and resources (e.g., `cost-center=card-ml`, `data-classification=restricted`, `env=prod`) and uses condition keys like `aws:PrincipalTag/...` and `aws:ResourceTag/...`:

```json
{
  "Effect": "Allow",
  "Action": "s3:GetObject",
  "Resource": "*",
  "Condition": {
    "StringEquals": {
      "aws:ResourceTag/CostCenter": "${aws:PrincipalTag/CostCenter}"
    }
  }
}
```

This single policy lets a Card-ML principal read only Card-ML resources. The number of policies stays O(1) as the org scales. Capital One heavily favors ABAC for workload access; RBAC remains for human personas via Identity Center permission sets.

## 4. STS endpoints, IRSA, Pod Identity, IAM Roles Anywhere

**STS endpoints** — regional (`sts.us-east-1.amazonaws.com`) is preferred. The global endpoint is a SPoF and slower in many regions. Make global STS tokens valid in all regions only if you explicitly opt in.

**IRSA (IAM Roles for Service Accounts)** — GA **2019-09-03** for EKS. Maps a K8s ServiceAccount to an IAM role via OIDC federation. The pod gets short-lived credentials via projected service-account token. Replaced `kiam`/`kube2iam`.

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: card-ml-trainer
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/CardMLTrainerRole
```

The role's trust policy must allow `sts:AssumeRoleWithWebIdentity` for the cluster's OIDC provider, conditioned on the namespace+SA pair.

**EKS Pod Identity** — GA **2023-11-26**. Simpler alternative using an EKS-managed agent instead of OIDC + cluster trust policy. Easier cross-account, fewer trust-policy edits at scale. New EKS clusters should default to Pod Identity in 2026 unless you have specific OIDC requirements.

**IAM Roles Anywhere** — GA **2022-07-13**. On-prem servers or non-AWS workloads obtain temporary AWS creds via X.509 certs signed by a CA you register as a Trust Anchor. The replacement for "store an IAM access key in a bare-metal datacenter."

## 5. The 2019 Capital One breach in IAM detail

This is the canonical IAM teaching case study. Disclosed **2019-07-29**; $80M OCC civil penalty **2020-08-06**; $190M class-action settlement Dec 2021.

**Chain of failure:**

1. A **WAF / reverse-proxy EC2 instance** had a role with permissions to `s3:ListBucket` and `s3:GetObject` against customer-data buckets — way too broad.
2. The attacker exploited an **SSRF vulnerability** in the WAF to make the instance call `http://169.254.169.254/latest/meta-data/iam/security-credentials/...` — the **IMDSv1** endpoint.
3. **IMDSv1** returned the role's temporary credentials with no token/header challenge.
4. Attacker exfiltrated ~100 GB from S3 across ~106 million customer records.

**Defenses now considered table stakes** (every one of these is something a Capital One architecture review will check):

- **IMDSv2 required** — token-based, hop-limit=1. Enforce via SCP `Deny ec2:RunInstances unless MetadataHttpTokens=required`. Default-on for new instance types from **2024-03**. Declarative policies (2024) make this account-level default.
- **VPC endpoint policies** on S3 — restrict bucket access to org-owned principals only via `aws:PrincipalOrgID`.
- **S3 Block Public Access** at account *and* org level (now via RCP).
- **Least-privilege role**: scope to a single bucket prefix, not `s3:*`.
- **GuardDuty** detects credential exfil patterns (`UnauthorizedAccess:IAMUser/InstanceCredentialExfiltration`, `Recon:IAMUser/MaliciousIPCaller.Custom`).
- **No EC2 instance role with broad S3 access** — instead, use signed S3 presigned URLs from a control plane.

**Interview framing:** name the chain (SSRF → IMDSv1 → role creds → broad S3 grant) not the company. The industry learned this; everyone uses these defenses now.

## 6. IAM Access Analyzer

GA **2019-12-02**. Uses **Zelkova** (automated reasoning / SMT) to *prove* whether a resource policy permits external access.

2023–24 additions worth knowing:
- **Unused access findings** (GA 2023-11-26) — flags unused IAM users, roles, role permissions, access keys.
- **Custom policy checks** (GA 2024) — CI gate: "does this PR grant new permissions?" Reject if so.
- **Internal access analyzers** (GA 2024) — scan within the org boundary, not just external.
- **Policy generation from CloudTrail** — auto-generate scoped policies based on what a role actually used.

This is the engine that lets a CI pipeline say "this PR introduces over-broad permissions" without manual review.

## 7. Permission Boundaries (the delegated-admin enabler)

A **permissions boundary** is an advanced feature that caps the *effective* permissions of a user or role regardless of identity policy. Heavily used for **delegated administration**: developers can create roles, but only within the boundary you defined.

Critical pattern in CI/CD where pipelines mint application roles:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": "iam:CreateRole",
    "Resource": "*",
    "Condition": {
      "StringEquals": {
        "iam:PermissionsBoundary":
          "arn:aws:iam::123456789012:policy/CardMLAppBoundary"
      }
    }
  }]
}
```

Without this condition, your pipeline can create god-mode roles. With it, every role the pipeline mints is hard-bounded by `CardMLAppBoundary`.

**Note:** boundaries apply to the principal, not to resource policies. A bucket policy can still grant access wider than the boundary suggests.

## 8. 2024–2026 changes worth knowing

- **EKS Pod Identity** preferred over IRSA for new clusters (2024+).
- **Access Analyzer unused-access** and **policy generation from CloudTrail** widely adopted; integrated with Identity Center to flag dormant permission sets.
- **Centralized root management** via Organizations (2024-11) lets you delete root creds on member accounts.
- **IAM Identity Center → trusted identity propagation** for S3 Access Grants, Redshift, Athena (2024) — finally true end-user identity propagation, not role-pooling.
- **Verified Permissions** (Cedar policy language) — maturing as the answer for **app-layer authz**, separate from IAM. AWS's pitch for in-app authorization.

## 9. Pitfalls and anti-patterns

- `"Action": "*", "Resource": "*"` in identity policies — the #1 finding in any audit.
- **IMDSv1 enabled** — must die.
- **Wildcard trust policies** (`"Principal": "*"`) without a condition.
- **Cross-account roles** without `aws:PrincipalOrgID` or `sts:ExternalId`.
- Long-lived access keys in CI/CD instead of OIDC federation (GitHub Actions OIDC → `AssumeRoleWithWebIdentity` is the modern pattern).
- Forgetting **permission boundaries don't bind resource policies** — a bucket policy can still grant wider access.
- Letting `AWSReservedSSO_*` roles accumulate from defunct permission sets.

## 10. Capital One lens

Post-breach, Capital One is publicly on record (re:Inforce 2021/2022 talks, *"Building security with developer velocity"*) about:

- **Org-wide IMDSv2 enforcement** via SCP.
- **Mandatory permission boundaries** on all dev-created roles.
- **Centralized Access Analyzer** with policy-as-code gates in CI.
- **Cedar / Verified Permissions** for in-app authz.
- **Zero IAM users for humans** — Identity Center for all human access.
- **Internal "paved road" pipeline** that mints IRSA / Pod Identity roles automatically with prefix-scoped S3 grants.
- **Cloud Custodian** policies (their OSS) detect drift from these baselines and auto-remediate or alert.

Talking point: *"My first IAM check on any AWS architecture is the metadata hop limit on EC2 — if MetadataHttpTokens isn't 'required' the design is incomplete."*

## 11. Sanity check

1. What is the six-layer IAM evaluation chain, and which type of "deny" always wins?
2. Walk through the 2019 breach attack chain in IAM terms. Name three controls that would have prevented it.
3. When should you pick EKS Pod Identity over IRSA?
4. What does Zelkova do, and what's the practical value of "custom policy checks" in 2024?
5. Why is `aws:PrincipalOrgID` a more useful condition than `aws:SourceAccount` for blocking cross-org access?

## 12. Cross-references

- **Module 1** — Organizations, SCPs, RCPs (the org-level container for IAM)
- **Module 33** — EKS, where IRSA/Pod Identity live
- **Module 50, 52** — KMS key policies, the breach response, compliance
- **Module 51** — Cloud Custodian for IAM drift detection
- **Module 55** — GitHub Actions OIDC federation pattern

## Primary sources

- [`IAM_Best_Practices.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/IAM_Best_Practices.html)
- [`AWS_SRA.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/AWS_SRA.pdf) — Security Reference Architecture
- [`SCS-C03_Exam_Guide.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/certs/SCS-C03_Exam_Guide.pdf)
- Research report: [`02_aws_foundations.md`](../../research_inputs/04_aws_for_ai_ml/02_aws_foundations.md)
- [`CAPITAL_ONE.md`](CAPITAL_ONE.md) — 2019 breach context
