# Module 12 — Lake Formation, Glue Catalog, Iceberg, DataZone

> **What this is:** the AWS data-governance stack — Glue Data Catalog as metastore, Lake Formation as FGAC enforcer, Iceberg as table format, DataZone as federated governance. Compared to Databricks Unity Catalog.

---

## 1. Glue Data Catalog (the metastore)

The canonical Hive-Metastore-compatible metastore for AWS analytics. Athena, EMR, Glue ETL, Redshift Spectrum, and EMR Serverless all read it.

- Supports **Iceberg, Hudi, Delta Lake** table formats. Iceberg has the deepest integration; Glue 4.0+ writes Iceberg natively.
- **Federation**: Glue Catalog can federate to Hive Metastore, Snowflake, and (via Iceberg REST) other catalogs.
- **Glue Iceberg REST Catalog** (GA 2024) makes the Glue Catalog accessible to any Iceberg-compliant engine — Trino, Spark on K8s, Databricks.

## 2. Lake Formation

Centralized fine-grained access control (FGAC) on Glue Catalog tables.

### Three grant modes

1. **Named-resource grants** — explicit `GRANT SELECT ON db.table TO principal`.
2. **LF-Tag-Based Access Control (LF-TBAC)** — tags on databases/tables/columns; policies grant by tag expression. Scales to thousands of tables.
3. **Hybrid mode** (2023+) — coexistence with IAM-only access for tables not yet onboarded.

### Granularity

- Database
- Table
- Column
- Row
- Cell

Row/cell-level via **data filters** (predicate + column projection).

### Cross-account sharing

Lake Formation grants to an AWS account or org via **RAM** (Resource Access Manager). The receiving account creates a **resource link** to consume.

### The grant-order pitfall

If a table is registered with Lake Formation **but the IAM principal also has direct S3 read on the underlying bucket**, the user bypasses FGAC by reading raw S3.

**Fix:** remove direct S3 IAM to LF-managed prefixes; rely on LF temporary credentials vending (`lakeformation:GetTemporaryGlueTableCredentials`).

## 3. Iceberg on AWS (2024–2026)

- Apache Iceberg 1.5+ supported by Glue, Athena v3, EMR 6.15+, Redshift, SageMaker Processing.
- **S3 Tables** is the managed-Iceberg substrate (Module 10).
- **Schema evolution**, **partition evolution**, **time travel** (snapshot-id / as-of-timestamp), **branching/tagging** are first-class.
- **Compaction**: automatic in S3 Tables; in raw-S3 Iceberg you run Glue table optimization (`ALTER TABLE ... COMPACT`) — without it, small-file proliferation kills query perf within weeks.

## 4. AWS DataZone

GA Sep 2023; 2024–2025 additions: business glossary, ML Model Catalog, GenAI subscription workflows.

Layers on top of Lake Formation + Glue Catalog:

- **Domains** — LOB boundaries.
- **Projects** — cross-functional groups.
- **Data assets** — tables, dashboards, models.
- **Subscriptions** — audited access requests with publisher approval.

Approval workflows route to a *publisher*; once approved, DataZone calls Lake Formation to grant access — **LF remains the enforcement plane**.

**SageMaker Unified Studio** (re:Invent 2024 → GA 2025) embeds DataZone as the governance backbone for the unified data + AI workspace.

## 5. DataZone vs Unity Catalog

| | **DataZone** (AWS-native) | **Unity Catalog** (Databricks) |
|---|---|---|
| Where it lives | AWS; sits above Lake Formation | Inside Databricks control plane |
| Enforcement | Delegates to LF | Cluster-level (Photon, SQL Warehouse) |
| Scope | Tables, dashboards, notebooks, models | Tables, ML features, registered models |
| Open source? | No | Yes — Unity Catalog OSS (2024) with Iceberg REST endpoints |

**Interop:** Iceberg REST is the bridge. Both Unity (since 2024) and Glue (since 2024) expose Iceberg REST endpoints, so Spark on Databricks can read a Glue-cataloged Iceberg table with LF credentials vending, and Athena can read a Unity-cataloged Iceberg table.

## 6. Capital One lens

Strategic stack pattern:

```
S3 raw → Iceberg curated (→ S3 Tables) → Glue Catalog metastore →
Lake Formation FGAC with LF-Tags → DataZone for discovery & subscription →
Databricks Unity Catalog for ML/feature pipelines via Iceberg REST
```

- PCI-DSS posture: every table tagged `data_classification = PCI | NPI | Confidential | Public`; LF-TBAC denies non-PCI roles.
- KMS keys per LOB; CMK rotation 90 days.
- Databolt tokenization gates landing — Lake Formation enforces post-tokenization views (raw-PAN columns physically absent).

## 7. Pitfalls

- **Hybrid mode confusion** — users see both LF-managed and IAM-only tables and don't know which enforces. Fix: split databases, name them `_lf_` vs `_iam_`.
- **Forgetting `lakeformation:GetDataAccess`** — Athena returns "Insufficient Lake Formation permissions" even when grants look correct.
- **Glue Catalog version drift** — Glue 3.0 vs 4.0 vs 5.0 Iceberg behavior differs; pin EMR / Glue versions in PR templates.
- **DataZone subscription latency** — grants are asynchronous (seconds to minutes), unsuitable for break-glass workflows.
- **Iceberg compaction skipped** in self-managed buckets → query times degrade within weeks.

## 8. Sanity check

1. What are the three Lake Formation grant modes, and when does Hybrid bite?
2. Walk through the cross-account sharing flow — what does RAM do, and what does the receiving account create?
3. Why does Iceberg + S3 Tables solve the compaction problem?
4. DataZone vs Unity Catalog — what's the Iceberg REST interop story?
5. How does LF-TBAC scale better than named-resource grants in a 600-account estate?

## 9. Cross-references

- **Module 10** — S3 (the substrate, S3 Tables)
- **Module 14** — Glue Spark writes/reads via the catalog
- **Module 22, 24** — Redshift Spectrum + Athena consume catalog
- **Module 46** — Unity Catalog on AWS (the Databricks side of the interop)
- **Module 52** — Databolt-style tokenization upstream of LF

## Primary sources

- [`Lake_Formation_DG.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/Lake_Formation_DG.pdf)
- [`Glue_DeveloperGuide.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/Glue_DeveloperGuide.pdf)
- [`DataZone_UserGuide.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/DataZone_UserGuide.pdf)
- Research report: [`04_storage_data_lake.md`](../../research_inputs/04_aws_for_ai_ml/04_storage_data_lake.md)
