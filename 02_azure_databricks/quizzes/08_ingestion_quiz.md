# Quiz — Module 8: Lakeflow Connect & Ingestion Patterns

## Recall

**Q1.** Name the four ingestion paths and the canonical use case for each.

<details><summary>Answer</summary>

- **Lakeflow Connect** — managed connectors for SaaS sources (Salesforce, Workday, ServiceNow, SQL Server, NetSuite, GA4, SharePoint). GA at DAIS June 2025.
- **Auto Loader (`cloudFiles`)** — files landed in object storage (ADLS, S3) — JSON, CSV, Parquet, etc.
- **Structured Streaming** — real-time streaming sources (Kafka, Event Hubs, Kinesis).
- **COPY INTO** — one-shot SQL bulk load (historical backfill, manual ops loads).
</details>

**Q2.** What are the two file-discovery modes in Auto Loader, and when do you switch from one to the other?

<details><summary>Answer</summary>

- **Directory listing** (default) — lists the directory each trigger. Simpler. Fine up to ~10K files.
- **File notification mode** (`useNotifications=true`) — uses Azure Event Grid + Storage Queue for cloud-native file events. Scales to millions of files. Requires permission to provision Event Grid topics + ongoing queue cost + DR considerations.

**Switch when** directory listing dominates trigger time (typically beyond ~10K files), or when you have very high file fan-in (thousands per minute).
</details>

---

## Apply

**Q3.** Write an Auto Loader streaming read for partner claim files in ADLS, with explicit schema-evolution control (strict — fail on new columns), max 1000 files per trigger, and writing to Bronze with Auto-Compact enabled.

<details><summary>Answer</summary>

```python
from pyspark.sql.functions import current_timestamp, lit

bronze_table = "bronze.claims_landing"

(spark.readStream.format("cloudFiles")
   .option("cloudFiles.format", "json")
   .option("cloudFiles.useNotifications", "true")
   .option("cloudFiles.schemaLocation", "/Volumes/_admin/schemas/claims/")
   .option("cloudFiles.schemaEvolutionMode", "failOnNewColumns")
   .option("cloudFiles.maxFilesPerTrigger", 1000)
   .option("cloudFiles.includeExistingFiles", "false")  # only new arrivals
   .load("/Volumes/raw/edi/claims/")
   .withColumn("ingestion_ts", current_timestamp())
   .withColumn("source", lit("partner_payer_x"))
   .writeStream
   .format("delta")
   .option("checkpointLocation", "/Volumes/_admin/checkpoints/claims_landing/")
   .option("mergeSchema", "false")  # never auto-merge in prod
   .toTable(bronze_table))

# Pre-create the table with the right properties
spark.sql(f"""
ALTER TABLE {bronze_table} SET TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact'   = 'true',
  'delta.enableChangeDataFeed'       = 'false'  -- insert-only Bronze
)
""")
```

**Key choices:**
- **`failOnNewColumns`** — alerts you when partner schema changes; never silently lose data.
- **`useNotifications=true`** — assumes high enough file volume to justify Event Grid setup.
- **`maxFilesPerTrigger=1000`** — bounded restart safety.
- **Bronze append-only** — no CDF; raw immutable history.
- **`mergeSchema=false`** on the write — explicit ALTER TABLE for any schema change.
- **Optimized Writes + Auto Compact** — for streaming Bronze, both should be on.
</details>

---

## Diagnose

**Q4.** A team uses Lakeflow Connect for Salesforce ingestion. After a Salesforce admin added a custom field to the Account object, the next pipeline run failed with a schema-mismatch error. Walk through the diagnosis and fix.

<details><summary>Answer</summary>

**Likely cause:** schema drift between source (Salesforce) and the Lakeflow Connect pipeline's known schema. Lakeflow Connect tracks the source schema in its pipeline config; an upstream change requires the pipeline to re-discover the schema.

**Fix sequence:**
1. **Check the pipeline event log** — confirm the failure is schema-related vs an auth or rate-limit issue.
2. **Trigger a schema refresh** in the Lakeflow Connect UI (or via the REST API) — re-discovers source columns.
3. **Verify the destination Delta table** — the new column gets added (Lakeflow handles `ALTER TABLE ADD COLUMN`).
4. **Resume the pipeline.**

**Prevention:**
- **Coordinate with source-system admins** so schema changes flow through change control. A Salesforce admin adding a custom field shouldn't surprise Data Engineering.
- **Monitor `system.access.column_lineage`** for unexpected schema changes downstream — gives a window into which sources changed.
- **Document the runbook** — when a Salesforce schema change happens, here's the recovery procedure.

**Architectural note:** this is one of the gaps Lakeflow Connect has compared to Fivetran. Fivetran's larger QA team and longer history with these connectors mean fewer surprises on schema evolution. For mission-critical SaaS sources where every schema change is a production incident, Fivetran's track record may justify the additional vendor relationship despite the UC-governance loss.
</details>

---

## Defend

**Q5.** A peer says "we should standardize on Lakeflow Connect for all SaaS ingestion — one vendor, UC-native governance, no Fivetran license." Defend or refute for an Optum-scale healthcare org.

<details><summary>Answer</summary>

**Refute, with calibration.**

**Where the peer is right:**
- For sources on the **GA connector list** (Salesforce, Workday, ServiceNow, SQL Server, NetSuite, GA4, SharePoint), Lakeflow Connect is the right answer. UC-native governance, lineage end-to-end, no extra vendor relationship.
- The HIPAA-eligible workspace path includes Lakeflow Connect.

**Where the peer is wrong:**
- **Connector breadth is much narrower than Fivetran.** Lakeflow Connect has ~10 GA connectors + a roadmap. Fivetran has 500+. For an Optum-scale org with many SaaS partners (provider directories, network adequacy systems, member outreach platforms, vendor analytics, third-party care management), most won't be in Lakeflow's GA list.
- **Custom connector capability is limited.** If the source is exotic (a partner's proprietary REST API), you're going to write Spark code anyway.
- **Connector quality is maturing.** Fivetran has years of QA on each connector; Lakeflow's are newer. For sources where every schema change is a production incident, the maturity gap matters.

**The architect's decision rule:**
- **Use Lakeflow Connect** for the GA-list sources where UC governance is a substantive win.
- **Use Fivetran** for the long-tail SaaS sources outside the GA list. Treat the second vendor relationship as the price of breadth.
- **Use custom Spark + Auto Loader** for partner file feeds (EDI, SFTP-dropped CSV) — neither managed-connector vendor is designed for this.
- **Use custom Spark + REST clients** for proprietary APIs.

**The pragmatic 2026 healthcare ingestion stack:**
- **Lakeflow Connect** for ~30% of SaaS sources
- **Fivetran or Airbyte** for ~50% of long-tail SaaS
- **Auto Loader** for partner files
- **Structured Streaming** for HL7/X12 over Event Hubs
- **Lakehouse Federation** for live access to Snowflake / Postgres without copy

**Don't try to force everything onto one ingestion path.** The "one vendor" argument is procurement-shaped, not architecture-shaped.
</details>
