# Module 23 — Snowflake on AWS

> **What this is:** Snowflake the data platform, running on AWS. Why Capital One picked Snowflake despite Redshift being native, and how the two coexist.

---

## 1. The three-layer architecture

Snowflake's signature design:

1. **Storage layer** — S3 (when running on AWS). Snowflake-managed; you don't see buckets directly.
2. **Compute layer — Virtual Warehouses** — independent compute clusters that read/write the same shared storage.
3. **Cloud services layer** — metadata, query planning, security, access control. Runs in Snowflake's account.

**Key consequence:** storage and compute scale independently. You spin up a 4XL warehouse for one heavy query, kill it after, and the data stays put.

## 2. Virtual Warehouse sizes

| Size | Credits/hr | Use |
|---|---|---|
| **XS** | 1 | Dev, small ad-hoc |
| **S** | 2 | Small teams |
| **M** | 4 | Standard analytical |
| **L** | 8 | Heavy ETL |
| **XL** | 16 | Large queries |
| **2XL** | 32 | Very large |
| **3XL** | 64 | Massive ETL |
| **4XL** | 128 | Edge cases |
| **5XL** | 256 | (some regions) |
| **6XL** | 512 | (some regions) |

**Multi-cluster warehouses** auto-scale horizontally (add clusters of the same size for concurrency).

## 3. Snowpipe and Snowpipe Streaming

- **Snowpipe** — file-based continuous ingest (S3 → Snowflake table). Latency: ~60-90 sec.
- **Snowpipe Streaming** (newer, 2023) — row-based, sub-second latency. For real-time analytics.

## 4. Snowpark

DataFrame API + Python/Java/Scala UDFs running inside Snowflake. Replaces "extract data → process in Spark → write back" for many use cases.

**Snowpark Container Services** (GA 2024) — run containerized workloads inside Snowflake (closest analog to SageMaker training in-warehouse).

## 5. Time Travel and zero-copy cloning

- **Time Travel** — query data as of any moment in the last 90 days (Enterprise edition+).
- **Zero-copy cloning** — instantly create a clone of a table/schema/database without copying data. Critical for dev-prod parity.

## 6. Streams + Tasks

- **Streams** — CDC: track inserts/updates/deletes on a table.
- **Tasks** — scheduled SQL execution (cron-like).
- Combined: continuous ELT pipelines inside Snowflake.

## 7. Iceberg tables

Snowflake added **read + write support for Apache Iceberg** in 2024.

- Reads: external Iceberg tables on S3 (Glue Catalog or other catalogs).
- Writes: Snowflake can write Iceberg tables that other engines can read.

This is the **bridge to Redshift, Athena, Databricks** — Iceberg becomes the lingua franca.

## 8. Horizon governance

Snowflake's data governance pillar: object tagging, masking policies, row access policies, lineage, anomaly detection, classification. Roughly equivalent to Lake Formation + DataZone for the Snowflake-native side.

## 9. Cortex (Snowflake's AI/ML surface)

Snowflake **Cortex** (GA 2024) — built-in functions for embeddings, LLM completions, semantic search, document AI. Operates on Snowflake-resident data without exporting.

```sql
SELECT cortex.complete('claude-3-5', 'Summarize:' || review_text)
FROM customer_reviews;
```

## 10. Why Capital One picked Snowflake

Per [the HBR 2021 sponsor piece](https://hbr.org/sponsored/2021/06/from-data-to-insights-the-capital-one-journey) and inferred from their commercial Slingshot product:

- **Separation of compute and storage** at extreme scale (PB-class).
- **Time Travel** for compliance/audit recovery.
- **Cross-team concurrency** via multi-cluster warehouses.
- **Data marketplace** for sharing datasets across LOBs (and externally).
- **Existing investment** when the AWS migration completed in 2020 — Redshift was less mature in zero-ETL and concurrency at the time.

**Slingshot** is Capital One Software's commercial Snowflake cost-governance product — they built it to manage their own large Snowflake spend, then productized it.

## 11. Snowflake vs Redshift (decision points)

| | Snowflake | Redshift |
|---|---|---|
| Cost model | Credits per warehouse-second | Per RPU-second (Serverless) or instance-hour (Provisioned) |
| Compute isolation | Per-warehouse | Per-cluster |
| Cross-team concurrency | Multi-cluster warehouses | Concurrency Scaling |
| Time Travel | 90 days (Enterprise) | 35 days (PITR-like via UNDROP) |
| Iceberg | Native read+write | Spectrum (read) + native (write) |
| Pricing predictability | Less (varied query cost) | More (predictable Serverless RPU) |
| AWS-native integration | Limited (BYO IAM, KMS via key pair auth) | Deep |

## 12. 2024-2026 changes

- **Cortex** GA 2024.
- **Iceberg** read+write GA 2024.
- **Snowpark Container Services** GA 2024.
- **Snowpipe Streaming** matured.

## 13. Pitfalls

- **Auto-suspend warehouse** misconfigured → idle credits burn.
- **Result cache** illusion — query results cached 24h; clients can think a slow query is fast.
- **Cross-region replication cost** — significant data transfer.
- **Many small warehouses** vs one large multi-cluster — usually the latter wins for throughput.

## 14. Capital One lens

Both **Redshift and Snowflake-on-AWS** in production. Snowflake for enterprise-shared analytics (the data marketplace pattern); Redshift for service-team marts and tight-loop OLTP-to-warehouse via Zero-ETL.

**Interview talking point:** *"I expect Capital One to run Snowflake as the enterprise-shared warehouse (the data marketplace) and Redshift for service-team marts with Zero-ETL from Aurora — the choice depends on whether cross-team concurrency or AWS-native integration is the dominant requirement."*

## 15. Sanity check

1. What are the three layers of Snowflake's architecture?
2. What's the difference between Snowpipe and Snowpipe Streaming?
3. What does zero-copy cloning enable?
4. Why is Iceberg interoperability with Redshift/Athena strategically important?
5. Snowflake vs Redshift — name three decision factors.

## 16. Cross-references

- **Module 22** — Redshift (the AWS-native alternative)
- **Module 24** — Athena (serverless query on lake)
- **Module 12** — Iceberg, Glue Catalog (the interop layer)
- **Module 56** — Slingshot (Snowflake cost governance)
- **CAPITAL_ONE.md** — Snowflake strategic context

## Primary sources

- [`Snowflake_on_AWS.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/Snowflake_on_AWS.html)
- Research report: [`06c_analytical_vector_graph.md`](../../research_inputs/04_aws_for_ai_ml/06c_analytical_vector_graph.md)
