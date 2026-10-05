# Module 45 — Databricks on AWS Architecture & Control Plane

> **What this is:** Databricks-on-AWS deltas from Azure Databricks — control plane regions, classic vs serverless compute, MWS account model.

---

## 1. The control plane / data plane split (recap from Topic 02)

- **Control plane** — Databricks-hosted: web UI, Jobs scheduler, REST API, metastore.
- **Data plane** — your cloud (AWS in this module): compute clusters, storage access.

## 2. AWS deltas from Azure

| | **AWS** | **Azure** |
|---|---|---|
| Identity | IAM Identity Center / Okta / IAM Users | Azure AD / Entra |
| Compute auth | **Instance profiles** (IAM role attached to EC2) | Managed identities |
| Storage | **S3** | ADLS Gen2 |
| DNS | Route 53 | Azure DNS |
| Workspace deployment | **MWS (Multi-Workspace Service) Account API** | Azure portal / ARM |
| PrivateLink terms | "AWS PrivateLink" | "Private Endpoint" |
| Networking | Customer VPC (BYO) | Customer VNet |

## 3. Control plane regions (AWS)

Databricks runs control plane in specific AWS regions (us-east-1, us-east-2, us-west-2, eu-central-1, etc.). Your **workspace is bound to one control plane region**; data plane can be co-region.

## 4. Classic vs Serverless compute

| | **Classic** | **Serverless** |
|---|---|---|
| Data plane location | **Your AWS account / VPC** | Databricks' AWS account |
| Compute startup | 3-5 min | Seconds |
| Instance management | You see EC2 instances | None visible |
| Networking | BYO VPC; PrivateLink available | NCC (Network Connectivity Config) for egress |
| Cost | EC2 + DBUs | All-in DBUs |
| Compliance scope | Easier (workloads in your account) | Trickier (data plane outside your account) |

**The trade-off:** classic gives full control and stays in your AWS account; serverless is faster but the compute lives in Databricks' AWS account (not yours).

## 5. The MWS Account API

The **Multi-Workspace Service Account API** is how you programmatically deploy workspaces on AWS:

- **Account-level resources**: credentials (cross-account IAM role), networks (VPC + subnets + SG), storage (S3 bucket for root storage), encryption keys (KMS).
- **Workspaces** — created with references to above.
- **Logs** — log delivery to S3.

**Terraform provider**: `databricks/databricks`. Two-provider pattern:
- One provider at **account level** (`account_id`, `host = https://accounts.cloud.databricks.com`).
- One provider per **workspace** (`host = https://<workspace-url>`, `token = ...`).

## 6. Deployment architecture (typical Capital One pattern)

```
AWS Account: Databricks Networking
  └── VPC (BYO, /16)
      ├── Private subnets (for clusters)
      └── PrivateLink endpoints

AWS Account: Databricks Workspace A (Card LOB)
  └── Cross-account IAM role allows Databricks to provision EC2
  └── S3 bucket (root storage)
  └── KMS key (encryption)

Databricks Account API
  └── Creates workspace using above resources
```

## 7. 2024-2026 changes

- **Serverless on AWS** matured (general availability for SQL, Jobs, DLT, Notebooks).
- **Mosaic AI** features (Vector Search, Model Serving) on AWS.
- **Self-assuming IAM role** mandate (Jan 2025) — Databricks now requires the cross-account role to be self-assuming for security.

## 8. Pitfalls

- **Two-provider Terraform** complexity — easy to misconfigure account vs workspace.
- **Cross-account role permission scope** — too broad lets Databricks do too much.
- **Confusing classic and serverless cost models** — DBU rates differ.
- **Workspace bound to one control plane region** — multi-region requires multi-workspace.

## 9. Capital One lens

Confirmed via job posting "Snowflake, Databricks on AWS, Data Ops, Data Lakes." Likely setup:
- **Multi-workspace per LOB** (Card, Auto, Retail).
- **Classic compute in their AWS accounts** for sensitive workloads.
- **Serverless for non-sensitive analytical workloads** where control plane access is acceptable.

## 10. Sanity check

1. What's the workspace vs control plane region relationship?
2. Classic vs serverless data plane — where does each live?
3. What does the MWS Account API let you do?
4. Self-assuming IAM role — what changed in 2025?
5. Azure-to-AWS Databricks substitutions (identity, storage, compute auth) — name three.

## 11. Cross-references

- **Topic 02** — Azure Databricks deep (the contrast)
- **Module 46** — Unity Catalog on AWS
- **Module 47** — Databricks networking on AWS
- **Module 2** — IAM (instance profiles, self-assuming roles)

## Primary sources

- [`databricks_on_aws_overview.html`](../../research_inputs/04_aws_for_ai_ml/downloads/databricks_on_aws/databricks_on_aws_overview.html)
- Research report: [`11_databricks_on_aws.md`](../../research_inputs/04_aws_for_ai_ml/11_databricks_on_aws.md)
