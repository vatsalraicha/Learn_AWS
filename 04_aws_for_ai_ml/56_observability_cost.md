# Module 56 — Observability & Cost for AI Workloads

> **What this is:** CloudWatch, X-Ray, Prometheus / Grafana on EKS, Datadog patterns, AWS Cost Anomaly Detection, CUR 2.0, FOCUS 1.0, **the SageMaker cost gotchas hit list**, GenAI cost discipline, EKS / Lambda cost shapes.

---

## 1. CloudWatch — the AWS-native backbone

- **Metrics** — namespace per service, custom metrics via `PutMetricData`.
- **Alarms** — static, anomaly-detection-based, composite (combining multiple alarms).
- **Dashboards** — multi-service views.
- **Metric Streams** — push metrics to Kinesis Firehose for forwarding to Datadog, Splunk, etc.
- **CloudWatch Logs** — log groups with retention, **Logs Insights** (SQL-like queries), subscription filters.
- **Container Insights** — for ECS/EKS, per-cluster/per-pod metrics.
- **Application Signals** (GA Nov 2024) — APM-style auto-instrumentation for Lambda, ECS, EKS, EC2.

## 2. X-Ray

Distributed tracing.
- **Service map** — visualizes service dependencies.
- **Trace analytics** — query traces.
- **Sampling rules** — control trace volume.
- **OTel convergence** — X-Ray supports OTLP ingest (2024+).

## 3. AWS Distro for OpenTelemetry (ADOT)

AWS's OTel distribution. Instrument Lambda / EC2 / EKS / ECS workloads → send to CloudWatch + X-Ray + AMP + AMG.

## 4. AMP + AMG (Managed Prometheus + Managed Grafana)

- **Amazon Managed Service for Prometheus (AMP)** — scalable metrics backend with PromQL.
- **Amazon Managed Grafana (AMG)** — visualization on top of AMP, CloudWatch, X-Ray, OpenSearch, etc.

**Decision rule**: if you'd build it yourself with Prom + Grafana on K8s, use AMP + AMG instead unless you have specific reasons to self-host (cost at huge scale, customization).

## 5. Datadog and Splunk forwarding patterns

Most AWS-heavy shops still use Datadog or Splunk for unified observability. Forwarding patterns:

- **Datadog Lambda forwarder** — Lambda triggered on CloudWatch Logs subscription, forwards to Datadog.
- **Kinesis Firehose to Datadog** — Metric Streams → Firehose → Datadog HTTP endpoint.
- **Kinesis Firehose to Splunk** — same pattern; Splunk consumes HEC.

## 6. AWS Cost Anomaly Detection

ML-based anomaly detection on the bill. Cheap insurance:
- Detects unexpected spikes per service / account / tag / cost category.
- Free.
- Alert via SNS / Slack / email.

Set this up day-one in every account.

## 7. Cost Explorer + Budgets + Budget Actions

(Module 4.) The standard cost-management toolkit.

**Budget Actions** — auto-stop EC2/RDS, auto-apply SCP — underused for non-prod environments.

## 8. CUR 2.0 + FOCUS 1.0

- **CUR 2.0** — Cost and Usage Report, parquet on S3, hourly.
- **FOCUS 1.0** — FinOps Open Cost & Usage Specification; vendor-neutral cost data format. AWS exports CUR in FOCUS format.

Capital One almost certainly pipes CUR 2.0 to Snowflake/Redshift for per-LOB chargeback dashboards.

## 9. Application Signals

(2024+.) APM-style auto-instrumentation:
- Service-level objectives (SLOs).
- Service map with golden signals.
- Per-method latency/error rate.

The AWS-native APM offering, alternative to Datadog APM.

## 10. The SageMaker cost gotchas hit list

The line items that blow up bills for ML teams (the most-tested cost question in interviews):

| Gotcha | Why expensive | Fix |
|---|---|---|
| **Idle Studio domain** | Always-on EFS + IDE compute | Lifecycle hooks to shutdown idle apps |
| **Idle real-time endpoint** | $/hr per instance even at 0 RPS | Auto-scale to 0 (serverless inference) or scheduled shutdown |
| **Idle Notebook Instance** | $/hr forever | Auto-shutdown lifecycle config (well-known script) |
| **NAT GW** for SageMaker in VPC | $0.045/GB + $0.045/hr per AZ | Use VPC endpoints |
| **Unused EC2 Capacity Blocks** | Pay-for-reserved-window regardless | Cancellation policy + accurate forecasting |
| **Cross-AZ data transfer** | $0.01-$0.02/GB | Same-AZ placement for training data + instances |
| **S3 Standard for cold training data** | 1.5-3x cost vs IA | Lifecycle policies |
| **PrivateLink endpoint hours** | $/hr × every region × every service × every AZ | Consolidate, share endpoints via RAM |
| **EBS orphans** | Volumes left after instance terminates | DLM policies + Custodian cleanup |

## 11. GenAI cost discipline

Bedrock + Q cost levers:

- **Provisioned Throughput break-even**: roughly **8-12M output tokens / MU / month**. Below that, on-demand wins.
- **Application Inference Profiles** for per-app/per-tenant chargeback.
- **Guardrails cost per text unit** — non-trivial at high volume.
- **Knowledge Bases ingestion cost** — re-ingest on every doc change can add up.
- **OpenSearch Serverless OCU floor** — 2 OCU min ~$700/mo.
- **Q Business per-user** — $20/user × 50k employees = $12M/year.
- **Custom model hosting** requires Provisioned Throughput (no on-demand).

## 12. EKS and Lambda cost shapes

**EKS**:
- $0.10/hr control plane × $730 = $73/mo per cluster.
- Plus nodes (EC2 or Fargate).
- Plus EBS for PVs.
- Plus NAT GW + Interface endpoints.
- **Extended support** for old K8s versions: $0.60/hr per cluster (×6 = additional ~$430/mo).
- **Karpenter consolidation** is the biggest cost lever — terminates underutilized nodes proactively.

**Lambda**:
- Per request + per duration.
- Provisioned concurrency adds fixed cost.
- VPC endpoints avoid NAT GW cost.

## 13. Capital One pattern — cost-optimizing GenAI

Brent Segner's re:Invent 2024 talk *"Control the cost of your generative AI services"* reveals:

- **Application Inference Profiles** for per-app cost attribution.
- **Tag-based chargeback**.
- **Dedicated FinOps-for-AI team**.
- **Pre-deployment cost gate** (estimate token cost before launching).

## 14. Slingshot insight (the Capital One product)

**Slingshot** is Capital One Software's commercial Snowflake cost-optimization product. Concepts that almost certainly apply to their internal AWS cost governance:

- **Overprovisioning detection** (warehouses too big for workload).
- **Idle resource shutdown**.
- **Tag-based chargeback**.
- **Policy governance** (auto-apply rules).

These are the patterns you'd see on top of CloudWatch + Cost Anomaly Detection + Custodian internally.

## 15. Pitfalls

- **No baseline metrics** before optimizing → can't tell if you improved.
- **Datadog cost** at AWS scale can exceed the AWS bill it monitors.
- **Forgetting NAT GW + VPC endpoint costs** in SageMaker / Lambda VPC workloads.
- **Provisioned Throughput** for sub-break-even Bedrock usage.

## 16. Sanity check

1. Name three SageMaker cost gotchas and the fix for each.
2. When does Bedrock Provisioned Throughput beat on-demand?
3. What's CUR 2.0 + FOCUS 1.0 about?
4. Lambda in VPC — what's the NAT GW trap, and what's the fix?
5. What does Capital One's Slingshot product tell you about their cost approach?

## 17. Cross-references

- **Module 4** — billing fundamentals
- **Module 8** — VPC endpoints (cost vs NAT)
- **Module 37** — SageMaker inference (idle endpoint gotcha)
- **Module 42** — Bedrock Provisioned Throughput
- **Module 51** — Cloud Custodian for cost policies

## Primary sources

- [`CloudWatch_User_Guide.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/CloudWatch_User_Guide.pdf)
- [`X-Ray_Developer_Guide.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/X-Ray_Developer_Guide.pdf)
- [`AWS_Cost_Management_Whitepaper.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/AWS_Cost_Management_Whitepaper.pdf)
- Research report: [`14_observability_cost.md`](../../research_inputs/04_aws_for_ai_ml/14_observability_cost.md)
