# Module 48 — EMR vs Databricks Decision

> **What this is:** the decision framework for EMR Serverless / EMR on EKS / EMR on EC2 vs Databricks. Photon-on-AWS economics. Mosaic AI Vector Search on AWS.

---

## 1. The four contenders

| | **EMR Serverless** | **EMR on EKS** | **EMR on EC2** | **Databricks** |
|---|---|---|---|---|
| Form factor | Pay-per-job, no infra | Spark on your EKS cluster | Persistent EC2 cluster | Managed platform |
| Best for | Bursty, one-shot jobs | EKS-native shops | Steady-state ETL | ML/data engineering with broad ecosystem |
| Cost shape | Per-vCPU-second | EKS pricing + Spark | EC2 + EMR markup | DBU + EC2 (classic) or DBU only (serverless) |
| Spark engine | Apache Spark | Apache Spark | Apache Spark | **Photon** (proprietary, ~2× faster) |
| ML stack | Self-built | Self-built | Self-built | Mosaic AI (Vector Search, MLflow, Model Serving) |
| Notebooks | Basic | Basic | Basic | Polished |
| Governance | Lake Formation | Lake Formation | Lake Formation | Unity Catalog (or LF interop) |

## 2. When EMR wins

- **AWS-native commitment** — fewer vendor relationships.
- **One-shot batch jobs** — EMR Serverless is cheaper than spinning up a Databricks job cluster.
- **EKS-native shops** — EMR on EKS lives alongside your other workloads.
- **Iceberg-first** — simpler integration in some respects.

## 3. When Databricks wins

- **Photon performance** — when query time × hourly cost favors Photon's ~2× speedup.
- **Mosaic AI ecosystem** — Vector Search, AutoML, model serving, MLflow tightly integrated.
- **Cross-team analytical platform** — UC governance, notebooks, SQL Warehouses, Workflows.
- **Multi-language workloads** — Python + Scala + SQL + R in same notebook.

## 4. Photon on AWS economics

Photon is Databricks' C++ rewrite of Spark's vectorized engine. AWS Databricks (and Azure) charges a **Photon premium DBU rate** (~2-3× the standard rate).

**Break-even rule of thumb:** If Photon makes a query 2× faster, the premium roughly cancels out — total cost stays similar. The win comes when:
- Query is **>2× faster** (often true for large scans, joins, aggregations).
- You value **wall-clock time** (interactive analytics, SLA-bound jobs).

For ETL where time is flexible, vanilla Spark (no Photon) is usually cheaper.

## 5. Mosaic AI Vector Search on AWS

Databricks' managed vector search:
- **Delta-Sync** — keeps a vector index synced to a Delta source table.
- **Hybrid BM25 + ANN** search.
- **Storage-optimized vs compute-optimized endpoints**.

Comparable to AWS-native OpenSearch + Aurora pgvector. The pick depends on whether your data lives in Databricks-managed Delta tables or in S3 with Glue Catalog.

## 6. Cost-per-DBU on AWS

DBU rates vary by SKU:

| SKU | $/DBU (us-east-1, May 2026) |
|---|---|
| **Jobs Compute (classic)** | ~$0.10 |
| **All-Purpose Compute (classic)** | ~$0.40 |
| **DLT (Delta Live Tables)** | ~$0.20 |
| **SQL Pro** | ~$0.55 |
| **Serverless SQL** | ~$0.70 |
| **Serverless Compute (Jobs)** | ~$0.65 |

Plus EC2 cost in classic. Serverless folds compute into DBU rate.

**Rule:** Jobs Compute (classic) for cost-sensitive batch ETL; All-Purpose / Serverless for interactive.

## 7. Decision tree

```
Need Mosaic AI / MLflow / Vector Search?
  → Databricks

Want lowest-cost bursty one-shot Spark?
  → EMR Serverless

Already heavy EKS investment, want Spark co-located?
  → EMR on EKS

Need Photon-speed analytical workloads, SLA-bound?
  → Databricks with Photon

Steady-state large ETL, cost-sensitive?
  → EMR on EC2 (with Spot)

Standard ETL, no ML, AWS-native shop?
  → EMR Serverless
```

## 8. Pitfalls

- **Photon premium on workloads that don't benefit** — wastes money.
- **All-Purpose clusters left on overnight** — biggest Databricks bill surprise.
- **EMR Serverless cold start** — first job has init latency.
- **EMR on EKS without Karpenter** — slow scale-up.

## 9. Capital One lens

Confirmed both Databricks and EMR (and Snowflake) in their stack. Likely pattern:
- **EMR (some flavor)** for AWS-native batch ETL where Databricks isn't justified.
- **Databricks** for ML/data engineering with Mosaic AI features.
- **Snowflake** for enterprise warehousing.

Cost discipline matters at their scale — Photon premium on the wrong workload is real money.

## 10. Sanity check

1. EMR Serverless vs Databricks Jobs Compute — when does each win?
2. What's the Photon break-even rule?
3. Mosaic AI Vector Search vs OpenSearch — when does each win?
4. What's the DBU cost spread across Jobs / All-Purpose / Serverless?
5. Why is "All-Purpose cluster left overnight" the biggest cost gotcha?

## 11. Cross-references

- **Module 26** — OpenSearch (vector alternative)
- **Module 14** — Glue Spark (yet another Spark option)
- **Module 23** — Snowflake (the warehouse player)

## Primary sources

- [`aws_emr_serverless.html`](../../research_inputs/04_aws_for_ai_ml/downloads/databricks_on_aws/aws_emr_serverless.html)
- [`aws_emr_on_eks.html`](../../research_inputs/04_aws_for_ai_ml/downloads/databricks_on_aws/aws_emr_on_eks.html)
- Databricks pricing page (live, time-sensitive)
- Research report: [`11_databricks_on_aws.md`](../../research_inputs/04_aws_for_ai_ml/11_databricks_on_aws.md)
