# Module 11 — UC Adjacency Products: Lineage, Federation, Delta Sharing, Volumes

> **Goal of this module:** the UC features that orbit the catalog — lineage and what it actually captures, Lakehouse Federation for live access to non-Databricks sources, Delta Sharing for outbound data products, Volumes for governed unstructured data, and the Iceberg interop story post-Tabular acquisition.

---

## Lineage — what it captures, what it misses

UC lineage is automatic for SQL run on Databricks compute and surfaces in Catalog Explorer up to **column level** ([lineage docs](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/data-lineage)). Backed by `system.access.column_lineage` and `system.access.table_lineage` system tables.

### What it captures well

- SQL queries, notebook SQL cells
- Spark DataFrame operations with native functions
- DLT/Lakeflow pipelines (declarative)
- dbt-on-Databricks runs
- Reads/writes through Spark on UC-enabled compute
- AI Functions (`ai_query`, `ai_classify`, etc.) input/output edges

### What it misses (in practice)

- **Python UDFs and Scala UDFs** "obscure the mapping between source and target columns" — the mapping is captured as a coarse table-to-table edge, not column-level
- **Pandas / non-Spark Python** that reads via direct file API misses lineage entirely
- **External jobs** — anything that pulls a Delta table over Delta Sharing or a JDBC reader from outside doesn't record lineage on the UC side
- **BI tools** — Power BI / Tableau queries are recorded as "BI tool reads" but the downstream report graph is opaque to UC. [Microsoft Q&A confirms](https://learn.microsoft.com/en-us/answers/questions/5773525/end-to-end-lineage-not-visible-between-azure-datab) Purview cannot stitch end-to-end Databricks→Power BI lineage today
- **Cross-metastore / cross-region** lineage is hard-broken: ["Lineage graphs are created at the metastore level, and do not cross region or platform boundaries"](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/best-practices)
- **30/90-day windows** in the UI; the system tables go further but the pretty graph clips

### How teams supplement

- **OpenLineage + Marquez or DataHub** — installed as a Spark listener via init script ([OpenLineage Spark integration](https://github.com/OpenLineage/OpenLineage/tree/main/integration/spark/databricks)). Captures what UC misses.
- **Pipe `system.access.*` to a side store** — extend retention beyond UI clipping; build cross-region stitching.
- **DataHub with `acryl-spark-lineage`** — column-level lineage for non-Databricks-native flows. Module 24 covers the ecosystem options.

For a healthcare audit conversation, **don't promise UC lineage as the audit trail.** It's an engineering tool. Use `system.access.audit` forwarded to immutable storage for actual audit, and supplement UC lineage with OpenLineage for cross-platform visibility.

---

## Lakehouse Federation — live access to other engines

[GA'd as Lakehouse Federation](https://www.databricks.com/blog/announcing-general-availability-lakehouse-federation), supporting:
- Snowflake, Postgres, MySQL, Redshift, SQL Server, Synapse, BigQuery
- Salesforce Data Cloud, SAP BDC

Each shows up as a **foreign catalog** in UC with normal three-level naming.

### What works

- **Predicate, projection, aggregation, and limit pushdown** for the major engines — analytical joins on small dimensions work fine.
- **Snowflake Catalog Federation** ([docs](https://learn.microsoft.com/en-us/azure/databricks/query-federation/snowflake-catalog-federation)) is a meaningful upgrade over query federation: UC reads Snowflake-managed Iceberg tables directly from cloud storage, so compute is Databricks-only. Cheaper and faster than going through Snowflake compute.
- **Latency** quoted as 100–500 ms for federated catalogs and ~150 ms for cross-region — fine for analytics, **not fine for OLTP-style point lookups**.

### Where it breaks down

- **Wide joins** between a Databricks fact and a remote 100M-row table — pushdown helps but you're still pulling significant data. Most teams snapshot daily into a UC table once it matters.
- **Governance is per-catalog** — UC permissions you grant on a foreign catalog *do not* propagate to the source. A user with UC SELECT on `snowflake_fc.public.claims` is using the *connection's* credentials at the source. **Don't confuse "UC governs the federated view" with "UC governs Snowflake."**
- **Write-back is limited** — federation is read-mostly; not a substitute for ETL.
- For Postgres specifically, [Daniel Beach's streaming-from-Postgres post](https://www.confessionsofadataguy.com/streaming-postgres-data-to-databricks-delta-lake-in-unity-catalog/) lays out why CDC-to-Delta still beats federation for large tables.

### Rule of thumb

**Federate to discover, replicate to operate.** Use federation for ad-hoc cross-platform queries and small-dimension joins; replicate (via Lakeflow Connect, CDC, or scheduled snapshot) for any production workload.

---

## Delta Sharing — outbound data products

Two flavors:

### Databricks-to-Databricks (D2D)

Provider and recipient both on Databricks. Recipient sees shares as a UC catalog. Identity, audit, and notebook sharing native.

**For healthcare:** D2D is **fine for BAA-covered partners** (other Databricks shops with HIPAA-mode workspaces). PHI in a D2D share is bound by the recipient's UC, not just a token.

### Open protocol

Provider issues a recipient profile (token + endpoint); any [delta-sharing](https://delta.io/sharing/) client connects (Pandas, Spark OSS, Power BI, Tableau, etc.).

**Why open protocol is rarely used for PHI:**
- Bearer-token model concentrates risk on a long-lived secret rotated manually
- Audit on the recipient side is best-effort (provider can see *who* downloaded, not what they did with it downstream)
- BAA coverage doesn't transit the open protocol cleanly
- Most regulated shops use Delta Sharing for **de-identified or aggregate** data (research datasets, public health rollups, vendor analytics feeds)

### Documented limits worth knowing

- **Cannot share liquid-clustered tables with partition filtering**
- **Cannot share row-filtered or column-masked tables**
- **Cannot share SHALLOW CLONE tables**
- **View-sharing recipients can't query >20 shared views per query or from >5 different provider-shares**
- **Cross-environment** (commercial → GovCloud, AWS GovCloud → Azure China) is unsupported

[Create share docs](https://docs.databricks.com/aws/en/delta-sharing/create-share).

### Audit

Both flavors audit through provider-side `system.access.audit` and `system.access.outbound_*` tables ([audit logs docs](https://learn.microsoft.com/en-us/azure/databricks/delta-sharing/audit-logs)).

---

## Volumes — governed unstructured data

[Volumes GA'd](https://www.databricks.com/blog/announcing-general-availability-unity-catalog-volumes) as the answer to "where do my PDFs live in UC."

### Two flavors

- **Managed volumes** — UC-managed storage location, fully governed lifecycle. Drop the volume → data is deleted (after retention).
- **External volumes** — point at an existing ADLS path, governance only. Drop the volume → data stays.

### FUSE access

Volumes are addressable as `/Volumes/<catalog>/<schema>/<volume>/...` via [FUSE](https://learn.microsoft.com/en-us/azure/databricks/volumes/) — Python's `open()`, PIL, PyMuPDF, transformers' `from_pretrained`, etc. all just work. **This is what unlocks GenAI on PDFs/images as a governed UC workload:** chunking pipelines read `/Volumes/clinical/raw/notes/*.pdf`, write embeddings to a UC Delta table, and the whole pipeline is permissioned and audited.

### Use cases

- **Clinical notes / FHIR Bundles** in raw form (PDF, JSON, XML)
- **Init scripts** (the modern pattern — Module 2)
- **Cluster libraries** (custom wheels mirrored internally)
- **Model artifacts** (large checkpoints that don't belong in MLflow's `artifacts` folder)
- **Reference datasets** (ICD-10 vocabularies, CMS code lists)

### Limits

- **ABAC doesn't apply to volumes yet** (only tables, materialized views, streaming tables). Volume-level access control is GRANT-based, not policy-based.
- **Lineage on volumes is coarser than tables** — you'll see "volume read by job X" but not which file.
- **FUSE mounts are per-cluster and respect UC ACLs**, but path-traversal-style code in init scripts can still escape.

For healthcare: volumes are the right place for raw clinical PDFs / images / structured documents. Module 22 covers the FHIR de-id pipeline that lands in volumes.

---

## Iceberg interop — UniForm and managed Iceberg

### UniForm (now "Iceberg reads on Delta")

UniForm writes Delta as the system of record and **asynchronously generates Iceberg v2 metadata** on the same compute that did the Delta commit. Iceberg readers (Trino, Snowflake, Athena) see the table after the async generation lands, with some lag (seconds to minutes depending on commit rate). ([UniForm docs](https://learn.microsoft.com/en-us/azure/databricks/delta/uniform))

```sql
ALTER TABLE silver.claim_line SET TBLPROPERTIES (
  'delta.universalFormat.enabledFormats' = 'iceberg'
);
```

### UC managed Iceberg tables

**Public Preview from DBR 16.4 LTS:** Unity Catalog can manage *native* Iceberg tables alongside Delta, with a federation layer (Iceberg REST Catalog) so the same governed catalog serves both. UniForm is the Delta-first path; UC managed Iceberg is for shops that pick Iceberg as system of record.

### Iceberg REST Catalog API

External engines read managed Delta with Iceberg reads enabled, **and read/write managed Iceberg tables** (Public Preview). Snowflake's Iceberg-write-to-UC went GA on Azure on **2026-04-06** ([Snowflake release note](https://docs.snowflake.com/en/release-notes/2026/other/2026-04-06-iceberg-write-support-azure-unity-catalog)).

### Practical caution for healthcare

If you publish to external readers (Snowflake for the analytics team, Athena for ad-hoc), the lag in async metadata generation means your readers can be a commit or two behind. **Don't promise sub-minute SLAs on the Iceberg path; document the lag.**

For greenfield in May 2026:
- **Pick Delta** as default (more mature, more Databricks features)
- **Enable UniForm** when you have Iceberg-reader consumers
- **Pick UC managed Iceberg** only when Iceberg is the strategic choice (multi-engine shop standardized on Iceberg)

### Apache XTable

[XTable](https://xtable.apache.org/) (incubating) — Onehouse-led omni-directional translation across Delta, Hudi, Iceberg, Paimon. Useful when you need to bridge to Hudi-shop partners; less critical now that Iceberg is first-class in UC.

---

## OneLake / Microsoft Fabric integration

Three integration stories with three quality levels:

### OneLake / Fabric — the cleanest

**Mirrored Azure Databricks Catalog** is GA — mirror a UC catalog into OneLake; Fabric creates shortcuts (no data copy) per table. Fabric SQL endpoint, semantic models, Power BI Direct Lake all read from those shortcuts. **UC remains the source of truth and ACL enforcer.** This is the integration the Microsoft↔Databricks alliance actually shipped well.

### Microsoft Purview — mediocre but improving

[Purview can register UC as a data source](https://learn.microsoft.com/en-us/purview/register-scan-azure-databricks-unity-catalog) and pull metadata + lineage. But the [known limits](https://learn.microsoft.com/en-us/answers/questions/5510715/issue-with-unity-catalog-lineage-not-appearing-in) bite:
- External tables are not lineage-supported by the UC scanner
- Cannot scan a subset of *tables* — only catalogs
- No end-to-end Databricks→Power BI lineage (each side's lineage is captured but not stitched)
- Notebook transformation logic (Python/SQL inside cells) is not extracted — you see edges but not the "why"
- China region not supported for system-table-based lineage extraction

### Recommended posture

**UC is the operational governance plane; Purview is the enterprise catalog of *catalogs*** — useful for discovery and classification across non-Databricks sources (Synapse, on-prem, SaaS), but **don't double-write policy in both.** For column classification, do it in UC governed tags, sync labels to Purview, not the other way.

---

## Production patterns

### Pattern: outbound data product to a payor partner

```
Source: prod_phi_claims.gold.claim_summary (UC managed Delta, ABAC-policied)
   │
   ↓ De-identify via Silver→Gold pipeline
   │
   ↓
Target: prod_deid_claims.gold.claim_summary_deid
   │
   ↓ CREATE SHARE outbound_payer_x
   │   ADD TABLE prod_deid_claims.gold.claim_summary_deid;
   │
   ↓ D2D recipient registration (partner is on Databricks)
   │
Partner receives: their_workspace.shared.claim_summary_deid
```

**Audit trail:** `system.access.outbound_*` shows every access by partner.

**Governance discipline:**
- Never share PHI tables directly — always de-identify into a Gold table first
- Use D2D when partner is on Databricks; reserve open protocol for non-PHI / aggregate
- Set token expiration short (24-48 hr) and rotate on schedule
- Document the share in the data-products catalog

### Pattern: live federation to legacy Snowflake

```
Snowflake EDW (legacy, decade of tables) ──→ Lakehouse Federation foreign catalog
                                                       │
                                                       ↓
                                          UC: snowflake_legacy.public.member
                                                       │
                                                       ↓
Federated query in Databricks dashboard
```

**When to federate vs replicate:**
- Federate for **ad-hoc cross-platform queries** and **small-dimension joins** with predicate pushdown
- Replicate (CDC into UC) for **production analytics**, **wide joins**, or **anything ML-bound**
- Recognize **federation isn't a path to "UC governs Snowflake"** — it's a path to "UC sees Snowflake metadata"

### Pattern: GenAI on clinical PDFs

```
Source PDFs (provider documents, prior-auth letters)
         │
         ↓
ADLS landing → UC managed Volume
   /Volumes/clinical/raw/pdfs/
         │
         ↓ Auto Loader streams new files
         │
         ↓ Chunking pipeline (PyMuPDF + chunker)
         │
         ↓ Embeddings (Foundation Model APIs / BGE-large)
         │
         ↓ Mosaic AI Vector Search index (Module 13)
         │
         ↓ Agent retrieves
         │
Clinical user asks question in app
```

The volume is the **governed unstructured data layer** that anchors the whole pipeline. Module 13 covers Vector Search; Module 22 has the full healthcare reference architecture.

---

## When NOT to use these features

- **Lineage as the HIPAA audit trail** — engineering tool, not compliance tool. Use `system.access.audit` forwarded to immutable storage.
- **Federation for production OLTP-style queries** — latency is too high; replicate instead.
- **Delta Sharing open protocol for PHI** — bearer-token model is the wrong governance shape.
- **UC managed Iceberg as default** in May 2026 — Public Preview, less mature than Delta. Pick Delta unless Iceberg is the strategic choice.
- **Volumes as a general-purpose file mount** — they're for governed unstructured data; for ephemeral cluster scratch, use `/tmp` or DBFS.

---

## Sanity check

1. UC lineage misses four classes of operation. Name them, and explain how teams supplement.
2. What's the difference between Lakehouse Federation and Snowflake Catalog Federation, and why does the latter matter?
3. Why is Delta Sharing's open protocol rarely used for PHI?
4. What does FUSE access on Volumes give you that DBFS mounts didn't?
5. UniForm vs UC managed Iceberg — when do you pick each?
6. The Microsoft Fabric / OneLake integration with UC: what works well, and what's your governance discipline around Purview?

---

## Further reading

- [Lineage on UC — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/data-lineage)
- [Lakehouse Federation GA blog](https://www.databricks.com/blog/announcing-general-availability-lakehouse-federation)
- [Snowflake Catalog Federation](https://learn.microsoft.com/en-us/azure/databricks/query-federation/snowflake-catalog-federation)
- [Delta Sharing — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/delta-sharing/)
- [Delta Sharing audit](https://learn.microsoft.com/en-us/azure/databricks/delta-sharing/audit-logs)
- [Volumes — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/volumes/)
- [Volumes GA blog](https://www.databricks.com/blog/announcing-general-availability-unity-catalog-volumes)
- [UniForm / Iceberg reads](https://learn.microsoft.com/en-us/azure/databricks/delta/uniform)
- [UC managed tables](https://docs.databricks.com/aws/en/tables/managed)
- [Iceberg REST Catalog](https://docs.databricks.com/aws/en/external-access/iceberg)
- [OneLake-UC integration](https://learn.microsoft.com/en-us/fabric/onelake/onelake-unity-catalog)
- [Purview UC integration](https://learn.microsoft.com/en-us/purview/register-scan-azure-databricks-unity-catalog)
- [Apache XTable](https://xtable.apache.org/)
