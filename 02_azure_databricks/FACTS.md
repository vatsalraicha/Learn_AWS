# FACTS — Topic 02 Azure Databricks

> Atomic, citable claims. Numbers, model names, GA dates, retirements. Each entry has a "Last verified" date so you know how stale it is. Re-verify volatile items before teaching or betting a roadmap on them.
>
> **Convention:** if something changed and a previous fact is stale, mark the old one ~~struck-through~~ and add the new one with a fresh date below.

---

## Pricing — Azure Databricks (USD list, Premium tier, US regions)

- **Jobs Compute (classic):** $0.15/DBU-hr. _Last verified: 2026-05-10. Source: [Azure Databricks pricing](https://azure.microsoft.com/en-us/pricing/details/databricks/)._
- **Jobs Light Compute:** $0.22/DBU-hr (legacy, narrowing relevance).
- **All-Purpose Compute:** $0.55/DBU-hr — ~3.6× Jobs Compute.
- **SQL Classic:** $0.22/DBU-hr.
- **SQL Pro:** $0.55/DBU-hr.
- **SQL Serverless:** $0.70/DBU-hr (VM cost included; no separate Azure VM line).
- **DLT Core / Pro / Advanced:** $0.20 / $0.25 / $0.36 per DBU-hr.
- **Serverless Jobs:** ~$0.35/DBU-hr (VM included).
- **Model Serving CPU base:** $0.07/DBU.
- **Model Serving GPU (DBU/hr):** Small T4 = 10.48 · Medium A10G ×1 = 20 · Medium 4× = 112 · Medium 8× = 290.8 · Large 8× A100 40GB = 538.4 · Large 8× A100 80GB = 628.

## DBCU (committed use)

- **1-year discount:** typically 10–15% off list. _Source: [MS Learn — Prepay Databricks reserved capacity](https://learn.microsoft.com/en-us/azure/cost-management-billing/reservations/prepay-databricks-reserved-capacity)._
- **3-year discount:** up to ~37% off list.
- **Forfeit-not-rollover:** unused DBCUs do NOT roll over past the term — right-size to p25–p50, not p75.
- **Material enterprise discount threshold:** ~$235K+ annual committed spend (procurement intel).

## Tier retirement (2026)

- **Standard tier:** new Standard workspaces stopped **2026-04-01**; existing auto-upgrade to Premium by **2026-10-01**. Migration produces ~35% DBU rate increase for All-Purpose-heavy workloads.

## Foundation Model API token rates (DBU per million tokens, May 2026)

| Model | Input DBU/M | Output DBU/M |
|---|---:|---:|
| Llama 4 Maverick | 7.143 | 21.429 |
| Llama 3.3 70B | 7.143 | 21.429 |
| Qwen 3 Next 80B | 2.143 | 17.143 |
| GPT OSS 120B | 2.143 | 8.571 |
| Gemma 3 12B | 2.143 | 7.143 |
| Llama 3.1 8B | 2.143 | 6.429 |
| GPT OSS 20B | 1.000 | 4.286 |

**Embeddings:** Qwen 3 0.6B = 0.286 DBU/M · GTE = 1.857 DBU/M · BGE Large = 1.429 DBU/M.

## Compliance & retention

- **Audit log default retention:** ~1 year. _HIPAA Security Rule §164.316(b)(2)(i) requires 6 years_ — must forward to immutable destination. _Source: [Audit logs system table reference](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/audit-logs)._
- **CSP (Compliance Security Profile) is permanent** — cannot be removed once a workspace has processed regulated data. Must delete and recreate to revert. _Source: [Compliance security profile](https://learn.microsoft.com/en-us/azure/databricks/security/privacy/security-profile)._
- **Three CMK products** with distinct scopes: managed services CMK (control plane), DBFS root CMK (workspace storage), managed disks CMK (cluster VM disks — classic only, NOT serverless).
- **AI/BI dashboards pre-Nov 2024** and **Genie Spaces pre-Apr 2025** are NOT encrypted with CMK at all.
- **Azure VNet outbound default change:** new VNets after **2026-03-31** no longer get default outbound internet access — NAT Gateway becomes mandatory for new Databricks workspaces.
- **NCC limits (account-level):** 50 workspaces per NCC, 100 PEs per region per account, 10 NCCs per region.

## Databricks Runtime (DBR)

- **DBR 17.3 LTS** — released October 2025; Spark 4.0; **the recommended LTS to standardize on for 2026 greenfield**. _Source: [DBR 17.3 LTS](https://docs.databricks.com/aws/en/release-notes/runtime/17.3lts)._
- **DBR 16.4 LTS** — released May 2025; Spark 3.5; baseline for UC managed Iceberg (Public Preview).
- **DBR 15.4 LTS** — Spark 3.5; baseline for Liquid Clustering GA.
- **DBR 14.3 LTS and earlier** — end-of-support approaching. Avoid for new work.
- **DBR 18.x** — 18.2 GA May 2026 (non-LTS, latest features).

## Apache Spark

- **Spark 4.0** GA **2025-05-23**. ANSI SQL on by default, VARIANT type, Spark Connect parity, Python Data Source API. Adopted in DBR 17.x. _Source: [Spark 4.0 release](https://spark.apache.org/releases/spark-release-4-0-0.html)._
- **Spark 4.1** brings Apache Spark Declarative Pipelines (the OSS landing of DLT/Lakeflow tech).

## Major rebrands and renames

- **Delta Live Tables (DLT) → Lakeflow Spark Declarative Pipelines (SDP)** — rename in 2024–2025; backward compatible. SKU codes still begin with "DLT" and event log schemas still say `dlt`. _Source: [What happened to DLT?](https://learn.microsoft.com/en-us/azure/databricks/ldp/where-is-dlt)._
- **MosaicML → Mosaic AI** — the GenAI/ML stack umbrella since 2024.
- **UniForm → "Iceberg reads"** — the feature where Delta tables expose Iceberg metadata async.
- **Mosaic AI Gateway → Unity AI Gateway** — rebranded.
- **Workflows ← Jobs** — naming shifted around 2023–2024.
- **DABs ("Databricks Asset Bundles") → "Declarative Automation Bundles"** — late 2024 rename.

## Acquisitions & valuations

- **MosaicML** — Jun 2023, ~$1.4B. _Source: [Wikipedia](https://en.wikipedia.org/wiki/Databricks)._
- **Arcion** — Oct 2023, ~$100M → CDC engine in Lakeflow Connect.
- **Lilac** — Mar 2024 → Mosaic AI dataset/eval tooling.
- **Tabular** — Jun 2024, $1B+ → UC managed Iceberg + UniForm + Iceberg REST.
- **BladeBridge** — early 2025 → DW migration tooling.
- **Neon** — May 2025, ~$1B → Lakebase.
- **Mooncake Labs** — 2025 → Lakebase acceleration.
- **Total acquisitions:** 17 as of April 2026 per Tracxn.
- **Series L:** September 2025; >$4B raised at $134B valuation; $4.8B revenue run-rate; 55% YoY growth.

## GA / Preview status (May 2026)

- **Liquid Clustering:** GA in DBR 15.2 (May 22, 2024). Automatic Liquid Clustering GA 2025.
- **Predictive Optimization:** GA 2025; **default-on for new UC managed tables, workspaces, and accounts**.
- **Hive Metastore Federation:** GA March 2025.
- **Lakehouse Federation:** GA (covers Snowflake, Postgres, MySQL, Redshift, SQL Server, Synapse, BigQuery, Salesforce DC, SAP BDC).
- **Lakeflow GA + Lakeflow Connect GA:** DAIS June 2025.
- **MLflow 3.0:** GA June 2025.
- **Mosaic AI Vector Search Hybrid (BM25 + dense):** GA 2025.
- **Mosaic AI Agent Framework:** GA 2024; **Agent Bricks:** Beta/Public Preview from June 2025.
- **Lakebase:** Public Preview from June 2025; GA status as of May 2026 — verify before teaching (latest signal Feb 2026 still preview).
- **Databricks Apps:** GA August 2025.
- **Databricks One:** Public Beta from June 2025.
- **Lakeflow Designer:** Public Preview from June 2025.
- **AI/BI Genie:** GA. Verified Answers / Trusted Assets GA 2025. Genie Code (autonomous data-team agent) introduced 2025–2026.
- **UC ABAC:** Public Preview April 2026 (tables, materialized views, streaming tables only — not yet model serving / volumes / functions).
- **UC Volumes:** GA.
- **UC Metric Views:** GA + open-sourced.
- **UC managed Iceberg tables:** Public Preview from DBR 16.4 LTS.
- **Iceberg REST Catalog API in UC:** Public Preview.
- **Snowflake Iceberg-write-to-UC:** GA on Azure **2026-04-06**.
- **Automatic Identity Management for Entra ID:** Public Preview 2026.
- **Foundation Model APIs pay-per-token under HIPAA (with Compliance Security Profile):** **major 2025 unlock** — for years FMAPI was non-HIPAA.

## Retirements

- **DBRX** — retired from FMAPI pay-per-token + fine-tuning **April 2025**. Still on Hugging Face for self-host.
- **Mistral 8x7B** — retired from FMAPI 2025.
- **Claude 3.7 Sonnet via Anthropic Messages API on Databricks** — retiring **2026-04-12**.
- **dbx** (deprecated successor of DABs) — explicitly deprecated by Databricks.
- **Hyperopt** — deprecated → migrate to Optuna.
- **Overwatch (Databricks Labs cost+observability)** — deprecated; replaced by `system.billing.usage`.
- **Databricks Labs Mosaic** (geospatial) — EOL with DBR 13.3 in **August 2026** → successor is **GeoBrix**.
- **Workspace-level SCIM** — being deprecated in favor of account-level SCIM.
- **Azure API for FHIR** — retiring **2026-09-30**; no new deployments since 2025-04-01.
- **NC v3 (V100) GPU SKUs** — being deprecated for Databricks workloads.

## Healthcare partnerships

- **Anthropic 5-year native partnership** signed **March 2025** — Claude (Haiku 4.5, Sonnet 4.6, Opus 4.7 with 1M context) available natively via SQL functions and model endpoints, governed by UC, no data egress to Anthropic's API.
- **John Snow Labs** — clinical NLP, de-id models, ICD-10 coding via foundation models in Model Serving.
- Healthcare customer references on databricks.com/customers (verify directly): CVS Health, Walgreens, Humana, Regeneron, Providence, Mayo Clinic, AstraZeneca, Sanofi, Eli Lilly.
- **No publicly published Optum or UHG end-to-end Databricks architecture** as of start of 2026.

## Performance numbers worth remembering

- **Photon breakeven margin:** ~20% speedup needed to break even on cost (because speedup affects both VM and DBU hours, not just DBU). Sync TPC-DS 1TB benchmark. _Source: [Sync benchmark](https://medium.com/sync-computing/are-databricks-clusters-with-photon-and-graviton-instances-worth-it-845641d464f2)._
- **Default autoscaling worse than tuned fixed cluster:** 37% more cost AND 14% slower on TPC-DS 100GB (Sync).
- **Snowflake-vs-Databricks SQL benchmark** (Akincilar): 24B-row dataset, 16 queries — DBX Large 636s vs Snowflake XL Gen1 266s (Snowflake **58% faster, 28% cheaper**).
- **Photon DBU multiplier:** 2× (the "premium" you pay for vectorized C++).
- **Idle GPU model serving cost:** Medium A10G held warm = ~$1,400/mo; Large 8X A100 80GB = ~$32K/mo per endpoint.
- **VM cost on top of DBU:** budget **$2–$3 of total spend per $1 of DBU**.

## Vector Search numbers

- **Standard endpoint cap:** ~320M vectors. **Storage-optimized:** ~1B vectors at 768-dim, ~7× cheaper per vector, ~250ms latency.
- **Hybrid scoring:** RRF with `rrf_param=60` default.

## Migration timelines (real)

- **Databricks' own internal HMS→UC migration:** 10 months with 4-person team.
- **Ensemble (healthcare RCM):** ~10,000 tables; single-night cutover after months of prep.
- **UCX (Databricks Labs):** explicitly "no SLA" — assessment dashboards stale on re-run.

## Audit-log retention reality

- Native: ~1 year.
- HIPAA requires: 6 years (45 CFR §164.316(b)(2)(i)).
- **`request_params` field of `system.access.audit` CAN contain PHI** — literal SQL values inlined into queries persist there.

---

## Source-of-truth pages worth bookmarking

- [Azure Databricks pricing — Microsoft](https://azure.microsoft.com/en-us/pricing/details/databricks/)
- [Databricks Foundation Model APIs supported models — Azure](https://learn.microsoft.com/en-us/azure/databricks/machine-learning/foundation-model-apis/supported-models)
- [Databricks Runtime release notes — Azure](https://learn.microsoft.com/en-us/azure/databricks/release-notes/runtime/)
- [HIPAA on Azure Databricks](https://learn.microsoft.com/en-us/azure/databricks/security/privacy/hipaa)
- [Compliance security profile](https://learn.microsoft.com/en-us/azure/databricks/security/privacy/security-profile)
- [Customer-managed keys for encryption](https://learn.microsoft.com/en-us/azure/databricks/security/keys/customer-managed-keys)
- [Audit log system table reference](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/audit-logs)
- [Unity Catalog ABAC](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/abac/)
- [Disaster recovery on Azure Databricks](https://learn.microsoft.com/en-us/azure/databricks/admin/disaster-recovery)
- [Predictive Optimization docs](https://learn.microsoft.com/en-us/azure/databricks/optimizations/predictive-optimization)
- [Liquid Clustering docs](https://learn.microsoft.com/en-us/azure/databricks/delta/clustering)
- [Lakeflow / What happened to DLT?](https://learn.microsoft.com/en-us/azure/databricks/ldp/where-is-dlt)

## Last full review

2026-05-10 (initial Topic 02 build).
