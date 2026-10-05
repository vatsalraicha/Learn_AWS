# Module 22 — Healthcare Reference Architectures

> **Goal of this module:** the canonical reference architectures for payor-side healthcare workloads on Databricks — claims (X12), Member 360, HEDIS / Stars, risk adjustment / HCC coding, fraud detection, and the FHIR + AHDS de-identification pipeline. Plus what doesn't work well for healthcare specifically.

---

## The defensible payor reference architecture

The two-workspace PHI/analytics split is the load-bearing design choice — leverages workspace-catalog binding (Module 9) so a PHI catalog is unreadable from the analytics workspace even if a user has account-level grants. **The difference between "we trust ABAC" and "we have a hard isolation boundary that survives a single misconfigured policy."**

```
┌───────────────────────────────┐       ┌───────────────────────────────┐
│  Source systems               │       │  Source systems               │
│  (Epic, Optum claims, Cerner, │──────▶│  Rhapsody/Mirth + Event Hubs  │
│   external partners)          │  HL7  │  (PHI in transit, TLS 1.2)    │
└───────────────────────────────┘       └──────────────┬────────────────┘
                                                       │
                ┌──────────────────────────────────────▼─────────────────────────────────────┐
                │ Azure Health Data Services (FHIR + DICOM) — BAA, PaaS, AHDS encryption     │
                │ Authoritative PHI store, $export with anonymization config                 │
                └──────────────────────┬─────────────────────────────────┬───────────────────┘
                                       │ raw PHI export                  │ de-identified export
                                       ▼                                 ▼
              ┌──────────────────────────────┐         ┌──────────────────────────────────┐
              │  ADLS Gen2  (PHI container)  │         │  ADLS Gen2  (de-id container)    │
              │  CMK + double encryption     │         │  CMK + double encryption         │
              │  Storage firewall, PE only   │         │  PE only                         │
              └──────────────┬───────────────┘         └────────────────┬─────────────────┘
                             │                                          │
                             ▼                                          ▼
       ┌────────────────────────────────────┐    ┌─────────────────────────────────────────┐
       │ PHI Workspace (CSP=HIPAA, Premium) │    │ Analytics Workspace (CSP=HIPAA optional)│
       │ • VNet injection + SCC + back-end  │    │ • VNet injection + SCC                  │
       │   Private Link, no public IP       │    │ • Bound to UC catalogs `member_deid_*`  │
       │ • Storage firewall on              │    │ • RAG, ML training, BI, Genie           │
       │ • CMK (managed services + DBFS +   │    │                                         │
       │   managed disks via Key Vault HSM) │    │                                         │
       │ • Bound to UC catalogs `phi_raw_*` │    │                                         │
       │ • Bronze→Silver, no notebook       │    │                                         │
       │   exports, no Genie, no Model      │    │                                         │
       │   Serving                          │    │                                         │
       └────────────────────────────────────┘    └─────────────────────────────────────────┘
                             │                                          ▲
                             │  ABAC tagging + column masks +           │
                             │  row filters + de-id UDFs                │
                             └──────────────────────────────────────────┘

  Cross-cutting:
  • Audit: system.access.audit → ETL → 6-year compliance Delta → Sentinel/Splunk via Event Hub
  • Identity: Entra ID + SCIM at account level, per-workspace conditional access
  • Egress: Azure Firewall Premium with TLS inspection; UDR forces all 0.0.0.0/0 through
  • DR: paired-region UC metastore replication, separate workspaces in DR region
```

This is the architecture diagram for any Optum-grade healthcare proposal.

---

## Insurance / claims / actuarial — the Optum-shaped use cases

Most data at a payor falls into a small set of canonical workloads. Here are the patterns:

### Claims ingestion (X12 837/835/834/270/271)

```
EDI gateway / clearinghouse → ADLS landing zone (encrypted, PHI-aware)
  → Auto Loader (file notification mode for high volume)
  → Bronze: raw X12 text + envelope metadata (immutable, regulator-friendly)
  → Custom parser UDF (pyx12, Edifecs, custom)
  → Silver: claim_header, claim_line, service_line_adjustment per transaction type
  → Gold: member_month, claim_summary, denial_analysis
```

**X12 parser choice matters.** Three options:
- **`pyx12`** — OSS, decent quality, sufficient for most workloads
- **Edifecs** — commercial, used heavily in payor ETL, mature
- **Custom in Spark** — when you need specific behavior; expensive engineering

**Two reasonable Silver layouts:**
1. **Wide-segment** — one Silver table per logical entity (`claim_header`, `claim_line`, `service_line_adjustment`). Best for analytics. Requires good X12 parser.
2. **EAV-by-segment** — one row per segment, columns `(claim_id, loop_id, segment_id, element_position, value)`. Good for full-fidelity audit; bad for analytics. Use sparingly.

**Cluster `claim_header` by `(payer_id, received_date)`, `claim_line` by `(member_id, service_date)`.**

### Member 360 / Star Ratings

```
Claims (Silver) ──┐
Eligibility ──────┤
Pharmacy ─────────┤
Lab ──────────────┼─→ Gold: Member 360 (one row per member-month or member-year)
Clinical (FHIR) ──┤
Call-center ──────┤
SDOH ─────────────┘
```

Combine in a Gold layer. **ABAC tags drive who-sees-what:**
- `actuaries` group sees claims aggregates only (column mask hiding member identity)
- `care managers` group sees clinical only with consent attribute set (row filter)
- `data scientists` group sees de-identified version only (workspace-binding-enforced)

### HEDIS and Stars measures

Annual cycle; Databricks job-cluster pattern with Lakeflow Pipelines.

```
Member 360 → HEDIS measure functions (one per measure)
            → measure_results (one row per member-measure-year)
            → quality_summary (rolled up to plan / measure / year)
            → Power BI dashboards for Stars submission
```

Run on Job Compute (Module 16 — 3.6× cost cut vs All-Purpose). Schedule monthly; full annual rebuild for submissions.

### Risk adjustment / HCC coding

Clinical NLP on provider notes via John Snow Labs models in Model Serving.

```
Provider notes (UC volumes) → chunking pipeline → 
  John Snow Labs clinical NLP (Model Serving endpoint) → 
  ICD-10 + HCC code candidates → 
  human reviewer workflow (Databricks Apps) → 
  validated codes (Silver) → 
  risk score calculation
```

PHI in inference tables → CMK + ABAC. Provisioned throughput endpoint (not pay-per-token) for predictability.

### Fraud / waste / abuse detection

Graph + GBM models; classic batch and now agentic patterns reviewing flagged claims with `ai_query` over de-identified text.

```
Claims (Silver) → feature engineering → 
  GBM model (XGBoost / LightGBM) → flagged candidates → 
  Agent reviews each candidate via ai_query (de-identified): 
    "Is this claim consistent with the member's history? 
     What additional checks suggest fraud?" → 
  Investigator Databricks App for human review
```

**Use FMAPI Llama 3.3 70B at pay-per-token (HIPAA-eligible).** The agent's prompts contain de-identified flagged-claim text, not raw PHI.

### Provider directory and network adequacy

Light PHI but heavy entity-resolution work. Databricks well-suited. Lakehouse Federation can pull from Provider Master Data Management systems if those are on Snowflake or SQL Server.

### Actuarial

Historically SAS-heavy. Databricks displaces with Spark + Delta Lake for trend models, IBNR (Incurred But Not Reported), lapse/persistency. **Actuaries usually want Python or the SAS-on-Databricks bridge.**

---

## The FHIR + AHDS de-identification pipeline

Healthcare-AI architects need to know this end-to-end:

### Source layer

```
Provider EHRs → FHIR APIs / HL7v2 / X12
              → Rhapsody / Mirth (HL7v2 routing) — TLS 1.2
              → Event Hubs (PHI in transit, encrypted)
```

### Authoritative store

```
Azure Health Data Services FHIR service
  - BAA-covered PaaS
  - AHDS encryption at rest
  - PHI authoritative source
  - Receives ingested data
```

**Note:** Azure API for FHIR is being **retired Sept 30, 2026**; no new deployments after Apr 1, 2025. **Path forward = Azure Health Data Services FHIR service.**

### De-identification step

```
AHDS FHIR service → $export operation
                 → with _anonymizationConfig=anonymizationConfig.json
                 → using FHIR-Tools-for-Anonymization engine
                 → HIPAA Safe Harbor sample config (starting point)
                 → ADLS deid container (CMK + PE)
```

**Microsoft is explicit:** *"Microsoft is unable to evaluate de-identified export outputs or determine the acceptability for your use cases and compliance needs. The FHIR service's de-identified export is not guaranteed to meet any specific legal, regulatory, or compliance requirements."* The Safe Harbor config is a *starting point*; **privacy office signs off on final fhirPathRules.**

### Lakehouse layer

```
ADLS deid container → Auto Loader → 
  Bronze: raw bundle JSON + meta.lastUpdated → 
  Silver: per-resourceType tables (patient, encounter, observation, condition) → 
  Gold: analytical models (member 360, HEDIS, etc.)
```

**Critical anti-pattern:** landing the FHIR Bundle as one giant `STRUCT` column. **Kills data skipping for everything inside it.** Pattern: shred at Silver into per-resourceType tables.

### Two-workspace consumption

- **PHI workspace** binds to `phi_raw_*` catalogs — only authorized PHI users; locked-down
- **Analytics workspace** binds to `member_deid_*` catalogs — broader access for ML, BI, RAG

---

## Healthcare data products on Databricks

What Databricks ships for healthcare specifically:

### Lakehouse for Healthcare and Life Sciences solution accelerators

[`databricks.com/solutions/industries/healthcare-and-life-sciences`](https://www.databricks.com/solutions/industries/healthcare-and-life-sciences). Through 2024, accelerators for:
- HEDIS quality measures
- Real-world data (RWD) pipelines
- OMOP CDM ETL
- Drug discovery
- Clinical NLP with John Snow Labs
- ICD-10 coding with foundation models
- Claims fraud detection

### dbignite (legacy, treat with caution)

[`github.com/databrickslabs/dbignite`](https://github.com/databrickslabs/dbignite) — was Databricks Labs OSS for FHIR Bundle parsing, OMOP CDM landing, DICOM helpers. Activity slowed after 2023 as Databricks shifted to proprietary "Lakehouse for HCLS" + partnerships. **Verify current status before depending on it.**

### Partner ecosystem for healthcare

- **John Snow Labs** — clinical NLP, de-identification models, ICD-10 coding via foundation models
- **Innovaccer** — population health platform; integrates with Databricks
- **Rhapsody** — HL7v2 / FHIR routing
- **Privacera / Immuta** — column-level access control + tokenization layered on UC
- **Health Catalyst** — analytics + PHM platform

---

## Confirmed customer references

[`databricks.com/customers`](https://www.databricks.com/customers) lists healthcare customers (verify current list before quoting):
- CVS Health, Walgreens, Humana, Regeneron, Providence, Mayo Clinic, AstraZeneca, Sanofi, Eli Lilly

**Notable absence:** **no publicly published Optum or UHG end-to-end Databricks architecture** as of start of 2026. UHG/Optum has historically been more vocal about Snowflake and proprietary stacks (Optum Labs); Databricks penetration is real but largely below the public line. The user (Vatsal) is in a better position than I am to know what exists internally.

---

## Compliance frames beyond HIPAA

(Module 21 covered the breadth; recap for healthcare context.)

- **HITRUST CSF** — Public Preview only on Databricks; UHG-tier orgs frequently demand HITRUST. Serverless HITRUST is restricted to specific regions.
- **PCI-DSS** — GA via CSP for healthcare-payment workloads
- **FedRAMP High / IL5** — Azure Government Databricks under FedRAMP High; IL5 via specific configurations
- **NHS DSPT** — covered by Microsoft's overall Azure attestation; no Databricks-specific certification
- **GDPR** — handled via Microsoft DPA + Databricks DPA

For Optum specifically, **HITRUST is the one to watch.** As long as Public Preview, "is HITRUST certified" gets a "no, not for the workspace itself yet" answer.

---

## What doesn't work well for healthcare specifically

(Module 21 covered the architect's risk register; this is the healthcare lens.)

1. **Naming pollution** outside BAA — workspace/cluster/job/tag/repo names aren't BAA-covered
2. **Notebook artifact auditability** — cell outputs persist with PHI unless `Store interactive notebook results in customer account` is on
3. **Genie's chat history** persisting NL questions about PHI — categorically don't enable on PHI catalogs
4. **Model Serving inference tables** containing PHI — must be tagged + ABAC-protected
5. **Audit log retention** 1 year native vs HIPAA's 6
6. **DBFS mounts and `/mnt/` paths** routinely violate UC isolation
7. **Pre-Nov 2024 dashboards / pre-Apr 2025 Genie spaces** not encrypted with CMK — migration debt
8. **Egress without TLS inspection** — can't detect PHI exfiltration
9. **Permanent CSP setting** — test workspaces should NOT have it
10. **Browser-auth single point of failure** — Module 20
11. **NCC limits at Optum scale** — plan multi-account topology
12. **Workspace-level SCIM deprecation** — must move to account-level
13. **PHI in audit logs** — `request_params` can contain PHI; SIEM destination must match the workspace's controls

---

## When healthcare-on-Databricks is NOT the right answer

- **Clinical decision support requiring sub-100ms** — the lakehouse layer adds latency; for CDS, dedicated low-latency infrastructure
- **EHR replacement** — Databricks is for analytics + AI on EHR data, not the EHR itself
- **Real-time clinical alerting** — Event Hubs → custom Stream Analytics or Azure Data Explorer is faster
- **HL7v2 message routing** — Rhapsody / Mirth are purpose-built; don't replace with custom Spark
- **Pre-aggregated state-mandated regulatory submissions** — sometimes simpler with traditional BI tools

For Optum specifically, none of these are blockers; they exist to know where Databricks isn't the answer.

---

## Sanity check

1. Why is the two-workspace PHI/analytics split the load-bearing design choice for Optum?
2. Walk through the FHIR + AHDS de-identification pipeline end-to-end.
3. The X12 parser choice (`pyx12` vs Edifecs vs custom) — when would you pick each?
4. What does Microsoft explicitly NOT guarantee about FHIR `$export` de-identification?
5. Why is Optum's lack of public Databricks reference architecture a teaching point in itself?
6. Name three healthcare-specific anti-patterns that aren't covered by general Databricks anti-patterns.

---

## Further reading

- [HIPAA on Azure Databricks](https://learn.microsoft.com/en-us/azure/databricks/security/privacy/hipaa)
- [Lakehouse for Healthcare and Life Sciences](https://www.databricks.com/solutions/industries/healthcare-and-life-sciences)
- [databricks-industry-solutions/omop-cdm](https://github.com/databricks-industry-solutions/omop-cdm)
- [Connecting FHIR Data to Azure Databricks Delta Lake — MS Tech Community](https://techcommunity.microsoft.com/t5/healthcare-and-life-sciences/connecting-fhir-data-to-azure-databricks-delta-lake-in-azure/ba-p/3682104)
- [FHIR-Tools-for-Anonymization (Microsoft, OSS)](https://github.com/microsoft/FHIR-Tools-for-Anonymization)
- [Azure Health Data Services FHIR service](https://learn.microsoft.com/en-us/azure/healthcare-apis/fhir/)
- [FHIR de-identified export](https://learn.microsoft.com/en-us/azure/healthcare-apis/fhir/deidentified-export)
- [Azure API for FHIR retirement](https://learn.microsoft.com/en-us/azure/healthcare-apis/azure-api-for-fhir/overview) (note Sep 30 2026 retirement)
- [Databricks Customer stories](https://www.databricks.com/customers) (filter by healthcare)
- [John Snow Labs — clinical NLP](https://www.johnsnowlabs.com/healthcare/)
