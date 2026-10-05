# Quiz 12 — Observability + Cert Roadmap (Modules 56-57)

---

## Recall

1. What does CUR 2.0 add over CUR 1.0?
2. AMP + AMG — what are they?
3. Name three SageMaker cost gotchas and the fix for each.
4. What replaced MLS-C01, and when did it retire?
5. What's the recommended cert sequence for a Sr Lead AI/ML at Capital One?

## Apply

6. Estimate the monthly cost of an idle SageMaker real-time endpoint on `ml.g5.xlarge`.
7. Bedrock Provisioned Throughput break-even — at what token volume does it pay off?
8. Set up Cost Anomaly Detection for a new ML workload.
9. Design a self-paced AWS lab budget under $150/month.

## Diagnose

10. The AWS bill jumped $30k last month on a service that wasn't there before. What's your first three places to check?
11. SAP-C02 candidates frequently report running out of time. Why, and how do you mitigate?
12. Your SCS-C03 study course doesn't cover the GenAI guardrails task statement. What did you miss?

## Defend

13. Defend AMP + AMG over self-hosted Prometheus on EKS.
14. Defend taking DEA-C01 right after MLA-C01.

---

## Answers

1. **CUR 2.0 (GA 2024-06)** adds split cost allocation for shared services (EKS containers, ECR pull-through), FOCUS 1.0 format, and improved schema. Use Athena/Glue/QuickSight on CUR.
2. **AMP** = Amazon Managed Prometheus (scalable metrics backend with PromQL). **AMG** = Amazon Managed Grafana (visualization, queries CloudWatch + AMP + X-Ray + OpenSearch + Datadog + etc.).
3. **Idle real-time endpoint** ($/hr per instance even at 0 RPS) → auto-scale to 0 (serverless) or schedule shutdown. **NAT GW** in VPC → VPC endpoints. **Idle Studio Apps** → lifecycle hooks for auto-shutdown.
4. **MLA-C01 + AIF-C01 + AIP-C01** replaced MLS-C01. **MLS-C01 retired March 31, 2026.**
5. **SAA-C03 → MLA-C01 → DEA-C01 → SCS-C03 → SAP-C02 → AIP-C01.** Skip AIF-C01 (beneath your level) and ANS-C01 (SAP covers).
6. `ml.g5.xlarge` ≈ $1.40/hr × 730 = ~$1,022/mo, even at 0 RPS.
7. Roughly **8-12M output tokens / Model Unit / month**. Below that, on-demand wins; above, Provisioned Throughput.
8. Create Cost Anomaly Detection monitor scoped to **service / tag / cost category**; SNS topic for alerts; email/Slack subscription; threshold 1 std dev above baseline.
9. **AWS Budgets alert at $100**, **NAT GW only when needed** (use VPC endpoints), **stop all training/inference at end of day** via lifecycle config, **`terraform destroy` after each lab session**, **S3 IA for cold lab data**.
10. **(1) Cost Explorer** — group by service, find the spike. **(2) Cost Anomaly Detection** — if configured, it told you already. **(3) CUR 2.0** — drill into the specific resource (use Athena on CUR).
11. SAP-C02 = **75 questions in 180 min = 2.4 min/q**. Most candidates run out of time. Mitigate: time-box ruthlessly, flag-and-return for hard questions, AWS exam elimination heuristics (cross out two clearly-wrong answers first).
12. **SCS-C03 Dec 2025 refresh** added "Implement protections and guardrails for generative AI applications (GenAI OWASP Top 10 for LLM Applications)" under Domain 3.2. Most prep courses haven't caught up. Supplement with **AWS re:Inforce 2025 talks**.
13. **AMP + AMG: zero ops, fully managed, integrated with AWS services.** Self-hosted Prom on EKS requires ongoing maintenance, alerting on the monitoring stack, scaling Prom Thanos/Mimir at very high scale. AMP+AMG wins unless you have specific reasons (cost at huge scale, specific Prom features).
14. **Significant content overlap** — both cover S3, Glue, Athena, IAM, KMS, encryption, governance, VPC. DEA adds Redshift/Kinesis/streaming/MWAA depth. Taking DEA right after MLA reuses fresh knowledge. **Stacking play**: passing SAP-C02 later recerts both Associate-level certs.
