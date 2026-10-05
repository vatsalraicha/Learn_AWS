# Module 22 — Redshift Deep

> **What this is:** Amazon Redshift — RA3 nodes (managed storage), Redshift Serverless, Spectrum (query S3), Data Sharing, Zero-ETL integrations, Streaming Ingestion, Redshift ML.

---

## 1. Node types

| | Description |
|---|---|
| **RA3** | Managed storage (decoupled from compute). Sizes: ra3.xlplus, ra3.4xlarge, ra3.16xlarge. The current default. |
| **DC2** | Legacy compute-storage coupled nodes. **Deprecation** announced; migrate to RA3. |

## 2. Redshift Serverless (GA 2022)

- Pay per **RPU (Redshift Processing Unit)**-second.
- **Base capacity** (min, default 32 RPU; 2024 added 8 RPU floor for smaller workloads) and **max capacity** ceiling.
- Auto-scales between base and max.
- No cluster management.
- **Crossover vs provisioned:** Serverless wins under ~30-40% sustained utilization.

## 3. Redshift Spectrum

Query **S3 directly** from Redshift using external tables (Glue Data Catalog as metastore). No data movement needed.

- Pricing: $5/TB scanned (same as Athena).
- Supports Parquet, ORC, JSON, CSV, Iceberg (since 2023).
- Use case: hybrid Redshift-cluster + S3-lake architectures.

## 4. Data Sharing

Cross-cluster, cross-account, cross-region data sharing **without data movement**.

- Live read-only views into another cluster's data.
- Producer/consumer model.
- Enables a "share data across LOBs without copies" pattern critical at Capital One scale.

## 5. Zero-ETL integrations (the 2024 story)

Aurora → Redshift, RDS for MySQL/Postgres → Redshift, DynamoDB → Redshift, Salesforce → Redshift. **Continuously replicates** without you building pipelines.

| Source | GA |
|---|---|
| Aurora MySQL → Redshift | 2023 |
| Aurora Postgres → Redshift | 2024 |
| RDS MySQL → Redshift | 2024 |
| DynamoDB → Redshift | 2024 |
| Salesforce → Redshift | 2024 |

## 6. Materialized views

Pre-computed aggregations refreshed on a schedule or **auto-refresh** (Redshift detects underlying changes).

## 7. Concurrency Scaling

When a workload exceeds cluster capacity, Redshift transparently spins up additional clusters to absorb the overflow. **1 hour/day free** per cluster.

## 8. Workload Management (WLM)

- **Automatic WLM** (default, 2024+) — Redshift sizes queues based on workload.
- **Manual WLM** — you define queues with memory, concurrency, query timeouts.

## 9. Streaming Ingestion

Native ingestion from **Kinesis Data Streams** and **MSK**. Sub-second latency for incoming records to be queryable. Replaces "Kinesis → S3 → COPY into Redshift" pipelines.

## 10. Redshift ML

In-database ML via **SageMaker integration**. SQL:

```sql
CREATE MODEL my_model
FROM (SELECT * FROM training_data)
TARGET label_column
FUNCTION my_predict_fn
IAM_ROLE 'arn:...'
SETTINGS (S3_BUCKET '...');

SELECT my_predict_fn(features) FROM scoring_data;
```

Trains in SageMaker behind the scenes; SQL function calls the deployed model.

**2024**: Bedrock invocation from SQL (`SELECT bedrock_invoke('claude-3-5', prompt)`).

## 11. MERGE

Standard SQL MERGE for upserts (GA in Redshift 2023). Replaces older staging+delete+insert patterns.

## 12. AQUA (folded)

**Advanced Query Accelerator** (announced 2020) — quietly folded into RA3 nodes as a performance enhancement, not a separate purchase. Don't worry about it as a separate feature in 2026.

## 13. 2024-2026 changes

- **Zero-ETL** integrations multiplied (above).
- **Iceberg on Spectrum**.
- **Serverless 8 RPU floor** for small workloads.
- **MERGE** statement GA.
- **Bedrock invocation from SQL**.

## 14. Pitfalls

- **DC2 deprecation** — migrate to RA3.
- **Forgetting to enable Concurrency Scaling** — workloads queue.
- **Spectrum without partitioning** — scans entire data lake; $$$.
- **Wrong distribution style** (`DISTSTYLE`) on a large table — joins shuffle entire data.
- **Materialized view staleness** — auto-refresh is best-effort, not real-time.

## 15. Capital One lens

Capital One runs **both** Redshift and Snowflake (Module 23). Likely pattern:
- **Redshift Serverless** for service-team marts.
- **Snowflake** for enterprise-shared analytics (data marketplace).
- **Zero-ETL** for OLTP-to-warehouse where it fits.

## 16. Sanity check

1. RA3 vs DC2 — what's deprecating?
2. When does Redshift Serverless beat provisioned?
3. What's the difference between Data Sharing and Spectrum?
4. Walk through the Redshift ML pattern.
5. What's Concurrency Scaling, and what's the free tier?

## 17. Cross-references

- **Module 23** — Snowflake on AWS (the alternative warehouse)
- **Module 24** — Athena (the serverless lake-query alternative)
- **Module 12** — Glue Catalog + Iceberg
- **Module 28, 29** — MSK / Kinesis (streaming ingest sources)

## Primary sources

- [`Redshift_Best_Practices.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/Redshift_Best_Practices.html)
- [`Redshift_RA3_Nodes.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/Redshift_RA3_Nodes.html)
- [`Redshift_Zero_ETL.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/Redshift_Zero_ETL.html)
- Research report: [`06c_analytical_vector_graph.md`](../../research_inputs/04_aws_for_ai_ml/06c_analytical_vector_graph.md)
