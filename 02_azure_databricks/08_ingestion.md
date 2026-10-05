# Module 8 — Lakeflow Connect & Ingestion Patterns

> **Goal of this module:** know the four canonical ways data lands in Databricks (Lakeflow Connect, Auto Loader, Structured Streaming, COPY INTO), pick the right one per source, and not get surprised by the Fivetran-vs-Lakeflow vs build-vs-buy conversation.

---

## The four ingestion paths

| Path | Use for | Cost shape |
|---|---|---|
| **Lakeflow Connect** (managed connectors) | SaaS sources (Salesforce, Workday, ServiceNow, SQL Server, NetSuite, GA4, SharePoint) | Per-source-row pricing + serverless compute |
| **Auto Loader** (`cloudFiles`) | Files landed in object storage (ADLS, S3, GCS) — JSON, CSV, Parquet, etc. | Spark cluster compute only |
| **Structured Streaming** (Kafka, Event Hubs) | Real-time streaming sources | Spark cluster compute only |
| **COPY INTO** | One-shot SQL bulk load | Warehouse compute |

The architect's job: route each source to the right path. Most healthcare orgs use **all four** — Lakeflow Connect for SaaS, Auto Loader for partner file feeds, Structured Streaming for real-time HL7/X12 over Event Hubs, COPY INTO for one-time loads.

---

## Lakeflow Connect — managed connectors (GA at DAIS 2025)

The youngest of the four; **GA at DAIS June 2025** for Salesforce Sales Cloud, Workday, ServiceNow, Google Analytics 4, SharePoint, Microsoft SQL Server, and Oracle NetSuite ([GA blog](https://www.databricks.com/blog/announcing-general-availability-lakeflow-connect)). PostgreSQL, SFTP, and Zerobus Ingest were on the near-term roadmap as of mid-2025.

### What it does

- **Source-aware schema discovery** — connector knows the source's catalog and pulls table-level metadata.
- **Initial snapshot + ongoing CDC** — first run pulls the full table; subsequent runs pull only changes.
- **Serverless DLT/Lakeflow under the hood** — pipeline lifecycle managed for you.
- **Unity Catalog governance** — destination is a UC managed table; lineage tracked end-to-end.
- **Incremental processing** — uses source-specific change-tracking (Salesforce log, SQL Server CDC, etc.).

### When Lakeflow Connect wins

- **You want one vendor for governance.** Data lands directly in UC; lineage and audit are unified.
- **The source is on the supported list.**
- **The volume / freshness profile matches** — minutes-of-lag is typical, not seconds.

### When it loses

- **The source isn't supported.** Lakeflow's connector breadth is much narrower than Fivetran's (~500+ connectors). For partner CRM SaaS that's not in the GA list, Fivetran or Airbyte is the answer.
- **You need second-level latency.** Lakeflow Connect is incremental-batch, not true streaming.
- **You want full data ownership end-to-end.** Some Lakeflow Connect connectors require credentials to flow through Databricks' managed plane; review for HIPAA scope.

### vs Fivetran / Airbyte

| | Lakeflow Connect | Fivetran | Airbyte |
|---|---|---|---|
| Connector breadth | ~10 GA + roadmap | 500+ | 350+ |
| Governance / lineage | UC-native | Bolt-on | Bolt-on |
| Pricing | Per-row + serverless DBUs | Per active row, transparent | OSS or Cloud per-MAR |
| HIPAA-eligible | Yes (with CSP workspace) | Yes (paid tier) | Self-host or Cloud Enterprise |
| Connector quality | Maturing | Mature, big QA team | Variable (OSS) |
| Custom connectors | Limited | Marketplace + custom | OSS connectors |

**For Optum-scale healthcare**: Lakeflow Connect for the GA-list SaaS sources (Workday HR, ServiceNow tickets, SharePoint policies, SQL Server claims systems), Fivetran for the long-tail SaaS the GA list doesn't cover, custom Spark + Auto Loader for partner file feeds and EDI gateways. Don't try to force everything onto one ingestion path.

---

## Auto Loader (`cloudFiles`) — files in object storage

The workhorse for **file-based ingestion at scale.** Module 5 covered the operational details; this section is the architectural decisions.

### Two file-discovery modes

```python
# Directory listing mode (default, simpler)
df = (spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.schemaLocation", "/Volumes/_admin/schemas/claims/")
        .load("/Volumes/raw/edi/claims/"))

# File notification mode (Event Grid + Storage Queue on Azure)
df = (spark.readStream.format("cloudFiles")
        .option("cloudFiles.useNotifications", "true")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.schemaLocation", "/Volumes/_admin/schemas/claims/")
        .load(...))
```

**Directory listing** — fine up to ~10K files in the directory; beyond that, listing dominates trigger time. The simple default.

**File notification mode** — uses cloud-native events (Azure Event Grid + Storage Queue) and scales to millions of files. Requires:
- Permission to provision Event Grid topics on the source storage account
- Ongoing cost for the queue infrastructure
- DR considerations (the queue is a failure point)

**For Optum-scale workloads with high file fan-in** (real-time claims drops, lab feeds, prior-auth files): file notification mode is usually the right answer.

### Schema evolution modes

- **`addNewColumns`** (default) — auto-add new columns of compatible types; fails the stream on first occurrence, then resumes.
- **`rescue`** — captures unexpected columns into a `_rescued_data` STRING column. Stream doesn't fail. Use when forward progress > schema fidelity.
- **`failOnNewColumns`** — strict; fails on any new column. Use for highly-governed feeds where unexpected schema is a contract violation.
- **`none`** — ignores new columns. **Don't use; you lose data silently.**

For healthcare claims feeds where schema is contractual (the payer or trading partner sends an agreed schema), **`failOnNewColumns`** is the right default — alerts you to upstream changes before they hit production.

### `cloudFiles.maxFilesPerTrigger`

Caps how many files each trigger ingests. Without it, a backfill of 100K files in one trigger overwhelms the cluster. **Default is 1000** — explicit control is recommended.

For healthcare ingestion runbooks: when an upstream system goes offline for hours and recovers with a backlog, having `maxFilesPerTrigger` set protects the downstream cluster from the catch-up wave.

---

## Structured Streaming — Kafka, Event Hubs, Kinesis

For real-time streaming sources. Module 5 covered watermarks, output modes, triggers; this section is the source-side architecture.

### Azure Event Hubs

```python
df = (spark.readStream
        .format("eventhubs")
        .option("eventhubs.connectionString", connection_string)
        .option("eventhubs.consumerGroup", "$Default")
        .load())
```

For HL7v2 ingestion via Rhapsody → Event Hubs → Databricks, this is the canonical path. Azure Event Hubs supports the Kafka API, so you can also use the Kafka connector if the team is already kafka-shaped:

```python
df = (spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", "namespace.servicebus.windows.net:9093")
        .option("subscribe", "claims-hl7")
        .option("kafka.security.protocol", "SASL_SSL")
        .option("kafka.sasl.mechanism", "PLAIN")
        .option("kafka.sasl.jaas.config", jaas_config)
        .load())
```

### Production patterns

- **Watermarks always** for stateful operations (joins, aggregations, dedup).
- **`Trigger.AvailableNow()`** for incremental batch (run nightly, process backlog, exit).
- **`Trigger.ProcessingTime("30 seconds")`** for steady micro-batch with bounded latency SLO.
- **RocksDB state store** (default in DBR 17.3+) for any large-state pipeline.
- **Checkpoint location in UC volume** (not in DBFS — UC volumes give governance and survival across cluster restarts).
- **`maxOffsetsPerTrigger`** (Kafka) or equivalent — bound batch size for restart safety.

---

## COPY INTO — one-shot SQL bulk loads

```sql
COPY INTO silver.claim_line
FROM '/Volumes/raw/edi/claims/'
FILEFORMAT = JSON
PATTERN = '*.json'
FORMAT_OPTIONS ('multiLine' = 'true');
```

**When COPY INTO wins:**
- One-time historical backfill from a known set of files.
- Manual loads triggered by ops (vendor sends a file, ops loads it).
- Cases where streaming overhead is overkill.

**When Auto Loader wins:**
- Recurring ingestion (Auto Loader checkpoints automatically; COPY INTO requires you to track what's been loaded).
- Schema evolution.
- Large file counts where notification mode pays back.

For healthcare: COPY INTO for one-time historical loads ("here are 5 years of legacy claims, load them once"); Auto Loader for ongoing partner feeds.

---

## Healthcare-specific ingestion patterns

### HL7v2 over Event Hubs

```
Provider EHRs → Rhapsody / Mirth (HL7v2 routing layer)
              → Azure Event Hubs (TLS 1.2, encrypted in transit)
              → Databricks Structured Streaming
              → Bronze: raw HL7 message text + envelope metadata
              → Silver: parsed segments (MSH, PID, OBX, etc.) per resource type
```

**Bronze table:** keep the raw HL7 string immutable (regulator-friendly). Cluster by `received_date`; CDF disabled (insert-only).

**Silver shred:** custom parser UDF (or a wrapped Java HL7 parser like HAPI). Output one row per logical entity, not one row per segment. Cluster by `(member_id, received_date)`.

### X12 EDI claims (837 / 835 / 834 / 270 / 271)

```
EDI gateway / clearinghouse → ADLS landing zone (encrypted, PHI-aware)
                            → Auto Loader (file notification mode for high volume)
                            → Bronze: raw X12 text + envelope metadata
                            → Custom parser UDF (pyx12, Edifecs, custom)
                            → Silver: claim_header, claim_line, service_line_adjustment per transaction
```

X12 is hierarchical (interchange → functional group → transaction set → loop → segment). Two reasonable Silver layouts:
1. **Wide-segment** — one Silver table per logical entity. Best for analytics. Requires good X12 parser.
2. **EAV-by-segment** — one row per segment, columns `(claim_id, loop_id, segment_id, element_position, value)`. Good for full-fidelity audit; bad for analytics. Use sparingly.

### FHIR Bundles via Azure Health Data Services

```
Provider FHIR APIs → AHDS FHIR service (BAA-covered)
                   → $export with anonymization config (Safe Harbor)
                   → ADLS deid container (CMK + PE)
                   → Auto Loader → Databricks
                   → Bronze: raw bundle JSON + meta.lastUpdated
                   → Silver: per-resourceType tables (patient, encounter, observation, condition)
```

**Anti-pattern**: landing the FHIR Bundle as one giant `STRUCT` column. Kills data skipping for everything inside. **Pattern**: shred at Silver into per-resourceType tables. Module 22 has the full reference architecture.

### Lakeflow Connect for SQL Server claims systems

For payors whose claims system is on SQL Server (legacy or IBM Curam-based), **Lakeflow Connect's SQL Server connector** is the recommended path:

- **CDC-based incremental**: configures SQL Server CDC, pulls deltas
- **Initial snapshot**: parallel reads, configurable
- **UC-managed destination**: lands directly into UC managed Delta with governance
- **Networking**: requires PE to SQL Server (Azure Private Link to SQL DB / Managed Instance, or ExpressRoute to on-prem)

Compare to the alternative: custom Spark + JDBC, which is more flexible but more operational overhead.

### Other partner systems

- **CSV / fixed-width files** dropped into SFTP — pickup via Azure Data Factory or AzCopy to ADLS, then Auto Loader.
- **REST APIs from partners** — custom Python in a Workflows task, paginate, write to Delta. Use `databricks-sdk` for orchestration; `requests` or `httpx` for the HTTP calls.
- **Partner Delta Sharing** — provider issues a recipient profile; you read directly into your UC catalog as a foreign share. No copy. Module 11.

---

## Watermarking, idempotency, and replay

The three properties every healthcare ingestion pipeline must have:

1. **Idempotent** — re-running the same source must produce the same Silver state. The MERGE-with-row-hash pattern (Module 5) is the discipline.
2. **Watermark-aware** — for streaming aggregations, late-arriving data beyond the watermark is dropped. For corrections (90+ day window), use cancel-and-replace MERGE on Silver instead.
3. **Replayable** — Bronze is immutable; you can rebuild Silver from Bronze if a transformation bug is found. Don't transform in Bronze.

For a healthcare org, **the regulator-relevant property** is replayability — "I can prove what was in the source on date X" requires Bronze that hasn't been mutated.

---

## When NOT to use each path

- **Lakeflow Connect for sources outside the GA list** — don't build custom connectors when Fivetran/Airbyte already has them.
- **Auto Loader for high-frequency streaming** (Kafka-style) — that's Structured Streaming territory.
- **Structured Streaming for one-time loads** — COPY INTO or Auto Loader's `Trigger.AvailableNow` is simpler.
- **COPY INTO for recurring ingestion** — you'll lose track of what's been loaded; checkpoints aren't free with COPY INTO.

---

## Sanity check

1. A team needs to ingest Workday HR data daily. What path, and why?
2. A partner sends 5K JSON claim files per day to your ADLS. What path, and what discovery mode?
3. An EHR system is sending HL7v2 messages to an Event Hubs topic at 10K msg/sec. What path?
4. Your team needs to do a one-time load of 5 years of historical files. What path?
5. The CFO asks "should we just use Fivetran for everything?" What's the architect's two-sentence answer?
6. A schema-evolution change in a partner JSON feed broke the Auto Loader stream. What `cloudFiles.schemaEvolutionMode` would have prevented or controlled the failure differently?

---

## Further reading

- [Lakeflow Connect — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/ingestion/lakeflow-connect/)
- [Lakeflow Connect GA blog](https://www.databricks.com/blog/announcing-general-availability-lakeflow-connect)
- [Auto Loader — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/ingestion/cloud-object-storage/auto-loader/)
- [Structured Streaming on Azure Databricks](https://learn.microsoft.com/en-us/azure/databricks/structured-streaming/)
- [Event Hubs Spark connector](https://github.com/Azure/azure-event-hubs-spark)
- [COPY INTO — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/ingestion/copy-into/)
- [SQL Server connector GA blog](https://www.databricks.com/blog/announcing-sql-server-connector-lakeflow-connect-now-generally-available)
- [Connecting FHIR Data to Databricks Delta — Microsoft Tech Community](https://techcommunity.microsoft.com/t5/healthcare-and-life-sciences/connecting-fhir-data-to-azure-databricks-delta-lake-in-azure/ba-p/3682104)
