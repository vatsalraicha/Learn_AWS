# Module 1 — AWS Account, Organizations & Landing-Zone Model

> **What this is:** the multi-account topology that 99% of regulated-finance AWS estates use, why it exists, and how Capital One operates ~600+ accounts under it.
>
> **Why it matters:** an AWS account is the security, billing, and quota boundary. "One big account with namespaces" does not survive regulatory audit. Architects are expected to fluently describe Organizations, OUs, Control Tower vs Landing Zone Accelerator, and the SCP/RCP model. This shows up in the SAA-C03 exam (security domain), SAP-C02 (heavily), and every Capital One architecture review.
>
> **Cert mapping:** SAA-C03 (Security 30%), SAP-C02 (Org & multi-account heavily), SCS-C03 (governance).

---

## 1. The account is the boundary

A single AWS account is a hard security boundary. Inside one account, everything shares IAM, default VPCs, service quotas, and one root credential. You **cannot** subdivide an account into independent control planes — IAM policies, SCPs, and tagging are *not* substitutes for account separation.

The "many small accounts under one Organization" model has been the AWS best practice since at least 2018, codified in [`Organizations_Multi_Account_Strategy.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/Organizations_Multi_Account_Strategy.pdf). The pattern:

- **One management account** (formerly called the "master account") — holds Organizations, billing, payer, IAM Identity Center, GuardDuty/SecurityHub/Config delegated admins. *Never* run workloads here.
- **One Log Archive account** — locked-down S3 bucket destination for org-wide CloudTrail and Config.
- **One Audit account** — read-only access for SecurityHub, GuardDuty, Access Analyzer findings aggregation.
- **N workload accounts** — one per environment-stage × business unit (or finer).

Capital One operates **600+ accounts** under this model. The exact count is not public, but their re:Invent talks confirm a hundreds-of-accounts estate organized by line of business and environment tier.

## 2. AWS Organizations

**AWS Organizations** (GA **2017-02-28**) provides the tree:

```
Root
├── Security OU
│   ├── Audit account
│   └── Log Archive account
├── Infrastructure OU
│   ├── Network account (Transit Gateway hub)
│   └── Shared Services account
├── Sandbox OU
├── Workloads/Non-Prod OU
│   ├── card-ml-dev
│   ├── card-ml-stage
│   └── ...
├── Workloads/Prod OU
│   ├── card-ml-prod
│   └── ...
├── Exceptions OU      ← regulated/exempted accounts
├── Suspended OU       ← lifecycle holding pen
└── PolicyStaging OU   ← rehearse SCP/RCP changes here
```

Limits: max **1,000 OUs** per org, OU nesting depth **5**, soft limit on accounts (raisable to thousands), max **5 SCPs per entity**, max policy size **5,120 bytes** (whitespace-stripped).

**Pattern rule:** organize by **policy zone**, not team. Teams move; policy zones don't. "Card-ML Team OU" is wrong; "Workloads/Prod OU" is right.

## 3. SCPs and RCPs

These are the two policy types that bound the *org*, not individual identities.

### Service Control Policies (SCPs)

SCPs are **guardrails** that set the *maximum* permissions an IAM principal in a member account can have. **SCPs do not grant** — they are filters on what identity policies can grant. The classic SCP set for a regulated-finance estate:

- Deny region usage outside `us-east-1`, `us-east-2`, `us-west-2` (with narrow Bedrock exceptions when a model is only available elsewhere).
- Deny `ec2:RunInstances unless aws:RequestTag/CostCenter is present`.
- Deny `ec2:RunInstances unless MetadataHttpTokens=required` (mandates IMDSv2 — the post-2019-breach control).
- Deny disabling CloudTrail, GuardDuty, Config, Security Hub.
- Deny `s3:PutBucketPolicy` actions that grant `Principal: *` (block public S3).
- Deny use of the **root user** except via a specific MFA condition.

### Resource Control Policies (RCPs)

RCPs (GA **2024-11-13**) are the dual of SCPs. SCPs constrain **principals**; RCPs constrain **resources**. Before RCPs, you could not centrally enforce "no S3 bucket in this org may be public" — SCPs only bound your own principals, not anonymous or cross-account callers hitting your resources.

RCPs initially cover **S3, SQS, KMS, Secrets Manager, STS**, with more services planned. They attach to root/OU/account like SCPs. A typical RCP:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "DenyExternalAccessToS3",
    "Effect": "Deny",
    "Principal": "*",
    "Action": "s3:*",
    "Resource": "*",
    "Condition": {
      "StringNotEqualsIfExists": {
        "aws:PrincipalOrgID": "o-xxxxxxxxxx"
      },
      "BoolIfExists": {
        "aws:PrincipalIsAWSService": "false"
      }
    }
  }]
}
```

This single RCP would have prevented the 2019 Capital One breach exfil step — the attacker's principal was outside the org.

## 4. Control Tower vs Landing Zone Accelerator

Two AWS-provided multi-account orchestrators. They are not interchangeable.

| | **AWS Control Tower** | **Landing Zone Accelerator (LZA)** |
|---|---|---|
| GA | 2019-06-24 | 2022-03-22 |
| Form | Managed AWS service | Solutions Library reference deployment (CDK) |
| Config | Console-driven | YAML declarative |
| Audit profiles | Generic | PCI-DSS, HIPAA, NIST 800-53, CMMC, CIS, PBMM, CCCS Medium |
| Partitions | `aws` only | `aws`, `aws-us-gov`, `aws-cn` |
| Ceiling | ~300 accounts smoothly | Thousands |
| Customization | Account Factory Customization (AFC), AFT | YAML, full CDK extension |
| Who picks it | SMB, mid-market, simple orgs | Banks, federal, healthcare |

Capital One predates Control Tower and runs a custom account-vending pipeline closer in spirit to LZA. New regulated-finance shops in 2026 building from scratch should look at **LZA + AFT (Account Factory for Terraform)** rather than Control Tower.

## 5. IAM Identity Center

Renamed from "AWS SSO" on **2022-07-26**. The workforce-identity layer:

- SAML/OIDC federation to Okta, Azure AD, Ping, Google Workspace.
- **Permission sets** = templated IAM roles, materialized in each member account as `AWSReservedSSO_<Name>_<hash>` roles.
- **Account assignments** — which users/groups get which permission set in which accounts/OUs.
- **Session policies** — set at AssumeRole time, scope down further.
- **Delegated administration** — run Identity Center from a non-management account (almost always required).
- **Trusted identity propagation** (GA 2023-11; expanded 2024–25) — lets QuickSight, Redshift, EMR, S3 Access Grants, Athena consume the *user's* identity end-to-end. Big for fine-grained data access in banking.

The rule: **zero IAM Users for humans**. Identity Center for all human access. IAM Users only for break-glass and the small set of third-party integrations that cannot federate.

## 6. 2024–2026 changes worth knowing

- **RCPs GA** (2024-11-13) — resource-perimeter enforcement.
- **Declarative policies** (re:Invent 2024) — enforce account-wide defaults (IMDSv2, EBS encryption, default-VPC blocking) that survive user toggling.
- **AI services opt-out policies** (2024) — control Bedrock/Q data collection at the org level.
- **Centralized root access management** (GA 2024-11) — remove root credentials from member accounts entirely; assume root from management when needed.
- **Control Tower Account Factory Customization (AFC)** GA; **AFT (Account Factory for Terraform)** widely adopted.
- **Bedrock cross-region inference profiles** (2024-08) — service-specific multi-region access pattern relevant for region-locked models.

## 7. Pitfalls and anti-patterns

- Running workloads in the **management account**.
- **OU = team** instead of **OU = policy zone**.
- Treating SCPs as grants. They are filters.
- Skipping the **delegated admin** pattern for Identity Center, GuardDuty, Config, Security Hub — leaves the management account doing operational work.
- **Single CloudTrail in the management account** with no org-trail — tamper-evident logging gone if mgmt-account access is compromised.
- IAM Users for humans (despite SSO existing).
- Buying RIs across the org and discovering RI sharing pooled the discount somewhere unexpected.

## 8. Capital One lens

Capital One's public reference architecture and re:Invent talks describe:

- **600+ AWS accounts** with custom landing zone predating Control Tower.
- **Per-LOB OUs nested under environment-tier OUs** — Card-ML-Prod, Auto-ML-NonProd, etc.
- **Account-vending automation** (similar in spirit to AFT) — new accounts spawn with org-baseline policies, IAM Identity Center permission sets, mandatory tags, and a default VPC topology.
- **Mandatory SCPs**: deny non-US regions, deny root, deny IMDSv1, deny non-Capital-One-approved AMIs.
- **Hub-and-spoke Transit Gateway** in a dedicated Networking account.
- **RCPs adoption** — natural fit to harden the S3 estate against the historical SSRF exposure pattern.

Interview talking point: *"I'd expect Capital One to run delegated admin from the Security OU for GuardDuty + Config + Access Analyzer + Security Hub, with org-trail in CloudTrail to a locked Log Archive account, and RCPs on S3/KMS to enforce `aws:PrincipalOrgID` boundaries — those are the post-2019 baseline."*

## 9. Sanity check

1. What's the difference between an SCP and an RCP, and why couldn't SCPs alone prevent the 2019 Capital One breach exfiltration?
2. When would you pick Landing Zone Accelerator over Control Tower?
3. Why is "OU = team" wrong?
4. What is delegated administration and why is it almost always required?
5. What does centralized root access management (2024) actually do?

## 10. Cross-references

- **Module 2** — IAM deep, IRSA, the 2019 breach lessons in IAM detail
- **Module 6, 8** — VPC + multi-VPC + hub-and-spoke TGW in a Networking account
- **Module 51** — Cloud Custodian (Capital One's own org-governance OSS) layered on top of SCPs/RCPs
- **Module 57** — exam-domain mapping for SAA-C03 and SAP-C02

## Primary sources

- [`Organizations_Multi_Account_Strategy.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/Organizations_Multi_Account_Strategy.pdf) — official multi-account whitepaper
- [`AWS_SRA.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/AWS_SRA.pdf) — AWS Security Reference Architecture
- [`Control_Tower_UserGuide.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/Control_Tower_UserGuide.pdf)
- [`Landing_Zone_Accelerator.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/Landing_Zone_Accelerator.html)
- [`RCP_announcement.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/RCP_announcement.html) — 2024-11-13 RCP launch
- Research report: [`02_aws_foundations.md`](../../research_inputs/04_aws_for_ai_ml/02_aws_foundations.md)
