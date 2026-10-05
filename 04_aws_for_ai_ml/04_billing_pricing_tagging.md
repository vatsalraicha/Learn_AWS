# Module 4 — Billing, Pricing Models & Tagging Discipline

> **What this is:** the pricing models that actually matter (Savings Plans, Spot, On-Demand), Cost Explorer + Budgets + Cost Anomaly Detection, CUR 2.0, and tagging discipline as an enforceable policy.
>
> **Why it matters:** Capital One's annual AWS spend is estimated at $1B+. At that scale, FinOps is a dedicated function and SageMaker cost gotchas (idle endpoints, NAT GW, Capacity Blocks commitments) routinely run into seven figures. As a Sr Lead, you will design pipelines under Compute Savings Plan commitments, defend Spot-vs-OD choices, and explain why an untagged GPU instance costs the team $30k/month.
>
> **Cert mapping:** SAA-C03 (Cost-Optimized Architectures 20%), SAP-C02 (cost governance heavily), DEA-C01 (operations 22%).

---

## 1. Pricing models for compute

The choices matter most for ML — training and inference are where the bill lives.

| Model | Commit | Max discount | Flexibility |
|---|---|---|---|
| **On-Demand** | none | 0% | full |
| **Reserved Instance (Standard)** | 1y / 3y, no/partial/all upfront | ~72% (3y all-upfront) | locked to instance family/region/tenancy |
| **Reserved Instance (Convertible)** | 1y / 3y | ~54% | exchangeable to any family |
| **Compute Savings Plan** | 1y / 3y hourly $-commit | ~66% | EC2 + Fargate + Lambda; any region, family, OS, tenancy |
| **EC2 Instance Savings Plan** | 1y / 3y hourly $-commit | ~72% | locked to instance family + region; OS/size flexible |
| **SageMaker Savings Plan** | 1y / 3y $-commit | ~64% | SageMaker training, inference, processing, notebook |
| **Spot** | none | ~90% | interruptible (2-min warning) |

**The rule:** **Compute Savings Plans** dominate in practice. Same max-discount tier as Convertible RIs but with Lambda/Fargate coverage and no exchange ceremony. Use EC2 Instance SPs only when you have rigid steady-state demand on one family.

**Spot for ML training** is real money — large-scale checkpointed training (SageMaker Managed Spot Training, EKS Karpenter with spot pools) routinely saves 70-90%. Spot interruptions on `p4d`/`p5` GPU instances are not theoretical (10-20% in busy regions), so you need checkpointing every 10-30 minutes. SageMaker Managed Spot Training handles this for you.

## 2. The cost-management toolkit

### Cost Explorer

UI + API (`ce:GetCostAndUsage`). 12 months default, up to **38 months** retention. **Hourly granularity** for the last 14 days. The first place to look when a bill spikes.

### AWS Budgets

Alert on actual or forecasted spend. **Budget Actions** — auto-stop EC2/RDS, auto-apply an SCP, auto-disable an IAM policy. Underused feature: a $100 dev-account budget action that suspends instances when crossed is a fantastic guardrail.

### AWS Cost Anomaly Detection

GA **2020-12**. ML-based detection on cost/usage segmented by service, account, tag, or cost category. The cheapest insurance for catching a runaway SageMaker endpoint left on overnight. Set it up day one in every account.

### AWS Cost Categories

Virtual dimensions that group accounts/tags/services into a logical rollup (e.g., "Card-ML-Platform"). Compose into Cost Explorer for chargeback that doesn't depend on perfect tag discipline.

### Cost and Usage Report (CUR / CUR 2.0)

Parquet to S3, hourly granularity, every column. **CUR 2.0** (GA **2024-06**) is the new schema with split cost allocation for shared services (e.g., EKS containers, ECR) and **FOCUS 1.0**-compliant exports (FinOps Open Cost & Usage Specification). Capital One almost certainly pipes CUR 2.0 to Snowflake or Redshift for per-LOB chargeback dashboards.

## 3. Consolidated billing

Organizations automatically aggregates invoices to the management (payer) account. Three knobs:

- **Volume discounts** on S3, data transfer, and CloudFront — tier across the entire org.
- **RI sharing** — RIs and Savings Plans pool across accounts by default. Can be configured per-account (RI sharing on/off). Useful for: keeping one team's discount from being absorbed by another.
- **Credits** — applied org-wide unless pinned to specific accounts.

## 4. Tagging discipline (as policy)

Tagging is not optional. Untagged resources are the largest cost-allocation hole — typically **15-30% "unallocated"** without enforcement.

**Mandatory tag taxonomy** for a regulated finance org:

| Tag | Values |
|---|---|
| `CostCenter` | numeric code |
| `BusinessUnit` | card, auto, retail, ... |
| `Project` | free-form |
| `Environment` | prod / nonprod / sandbox |
| `Owner` | email |
| `DataClassification` | public / internal / confidential / restricted |
| `Compliance` | pci / sox / glba / none |
| `AutoShutdown` | true / false |
| `BackupPolicy` | tier-0 / tier-1 / tier-2 / none |

**Enforce via:**

- **Tag Policies** (Organizations feature) — define required keys and allowed values.
- **SCPs** — `Deny ec2:RunInstances if RequestTag/CostCenter is missing`.
- **AWS Config rules** — `required-tags`, with auto-remediation via SSM Automation.
- **Resource Groups Tagging API** — for retro-tagging existing resources.
- **Cloud Custodian** (Capital One's OSS) — `mark-for-op` policies that warn at T-7 days and stop at T-0.

Tags must be **activated** in the Billing console before they appear in Cost Explorer / CUR. There's a 24-hour lag.

## 5. ML-specific cost gotchas

The line items that blow up bills for ML teams:

| Line item | Why it's expensive | Fix |
|---|---|---|
| **Idle SageMaker Studio domain** | Always-on storage + IDE compute | Lifecycle hooks to shut down idle apps |
| **Idle SageMaker real-time endpoint** | $/hr per instance even at 0 RPS | Auto-scaling to 0 (serverless inference) or scheduled shutdown |
| **Idle SageMaker Notebook Instance** | $/hr forever | Auto-shutdown lifecycle config (well-known script) |
| **NAT Gateway** | $0.045/GB + $0.045/hr per AZ | VPC endpoints for AWS services (S3 + DynamoDB gateway endpoints are free) |
| **EC2 Capacity Blocks** | Reserved GPU windows — pay even if unused | Cancellation policy + accurate forecasting |
| **Cross-AZ data transfer** | $0.01-$0.02/GB | Place training datasets in the same AZ as training instances |
| **S3 Standard for cold training data** | 1.5-3x the cost of IA or Glacier | Lifecycle policies; archive raw inputs once features are computed |
| **PrivateLink endpoint hours** | $/hr × every region × every service × every AZ | Consolidate, share endpoints across accounts via RAM |

## 6. 2024–2026 changes worth knowing

- **CUR 2.0** GA **2024-06** with split cost allocation for shared services (EKS containers, ECR pull through).
- **FOCUS 1.0** published **2024-06-13**; AWS FOCUS export GA same window.
- **Savings Plans for SageMaker** expanded coverage 2024.
- **Bedrock cost allocation by inference profile / tenant** improvements 2024-25 (Application Inference Profiles).
- **Compute Optimizer for SageMaker** (newer recommendations).
- **AWS re:Post billing console redesign** 2024.

## 7. Pitfalls and anti-patterns

- **Untagged resources** — 15-30% unallocated bill at most orgs without enforcement.
- **Tag drift** between IaC and console mutations.
- Buying **RIs without first analyzing SP fit** — you almost always want Compute SPs now.
- Forgetting that **Savings Plans apply to compute usage across the org payer**, so a high-discount account can "absorb" another account's bill — desirable for pooling, confusing for chargeback.
- **Idle SageMaker endpoints / Studio domains** — the silent killer.
- **NAT GW egress for S3** — should be a VPC gateway endpoint (free).
- Letting **Bedrock provisioned throughput** sit when on-demand would be cheaper at current volume.

## 8. Capital One lens

Capital One discloses ~$1B+ annual AWS spend (analyst estimates, post-data-center-exit 2020). At that scale they almost certainly run:

- A dedicated **FinOps team**.
- **Org-wide Compute Savings Plan** portfolio managed at the payer.
- **Tag policies enforced via SCPs and preventive Config rules**.
- **CUR 2.0 piped to Snowflake/Redshift** for per-LOB chargeback dashboards (their Slingshot product is the commercial version of this insight applied to Snowflake).
- **Budget actions auto-stopping non-prod after-hours**.
- **Cost Anomaly Detection scoped per cost category**.
- **SageMaker Savings Plans** for the training fleet; **Spot + Karpenter** for batch model training jobs.
- The re:Invent 2024 talk "Control the cost of your generative AI services" (Brent Segner) suggests **Bedrock cost governance** via Application Inference Profiles, per-app tags, and provisioned-throughput break-even analysis.

Interview talking point: *"At Capital One scale, the FinOps lever I'd reach for first is Compute Savings Plans pooled at the payer, then SageMaker Savings Plans for the training fleet, then Cost Anomaly Detection scoped per LOB cost category, and Cloud Custodian to enforce auto-shutdown on tagged non-prod resources."*

## 9. Sanity check

1. When would you pick EC2 Instance Savings Plans over Compute Savings Plans?
2. Why is Spot a credible option for SageMaker training but not for a low-latency real-time endpoint?
3. What does CUR 2.0 add over CUR 1.0?
4. Name three ML-specific cost gotchas and the fix for each.
5. Tag policies vs SCPs for tag enforcement — which is preventive and which is detective?

## 10. Cross-references

- **Module 30** — EC2 instance pricing detail
- **Module 32** — Lambda pricing model
- **Module 37** — SageMaker inference endpoint pricing (the big cost gotcha)
- **Module 42** — Bedrock per-token vs Provisioned Throughput break-even
- **Module 51** — Cloud Custodian policies for tag enforcement, idle cleanup
- **Module 56** — Observability + cost (the operational follow-through)

## Primary sources

- [`Savings_Plans_UserGuide.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/Savings_Plans_UserGuide.pdf)
- [`Tagging_Best_Practices.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/Tagging_Best_Practices.pdf)
- Research report: [`02_aws_foundations.md`](../../research_inputs/04_aws_for_ai_ml/02_aws_foundations.md)
