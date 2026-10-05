# Module 21 — HIPAA on Azure Databricks 2026

> **Goal of this module:** the architect-level discipline for running PHI on Databricks — Compliance Security Profile, the three CMK products, BAA scope reality, audit log retention vs HIPAA's 6-year requirement, naming pollution, the AI-on-PHI dangers (Genie, inference tables, BAA scope on previews), and the 12-line "what does HIPAA-eligible mean in 2026" answer.

---

## Why this is its own module

HIPAA on Databricks isn't a feature toggle — it's an architecture. Get it wrong and you have a finding waiting to happen. Get it right and Databricks becomes a credible payor-grade platform. This module is the discipline.

---

## HIPAA-eligible workspaces — the actual gating (May 2026)

HIPAA eligibility is a **combination** of three things, all set at workspace creation, and one is **permanent** ([HIPAA on Azure Databricks docs](https://learn.microsoft.com/en-us/azure/databricks/security/privacy/hipaa)):

1. **Premium pricing tier** — Standard tier is unusable for PHI (no UC ABAC, no CMK, no audit log forwarding, no Private Link).
2. **Enhanced Security and Compliance add-on** purchased on the account (separate line item beyond Premium).
3. **Compliance Security Profile (CSP)** enabled on the workspace, with the `HIPAA` standard added to `complianceStandards`. *"Enabling the compliance security profile or adding compliance standards to a workspace is intended to be a permanent change... To revert, you must delete the workspace and create a new one."*

### What CSP enforces

- **CIS Level 1 hardened compute image** for all classic clusters
- **Automatic cluster updates** on a configurable maintenance window — design jobs to tolerate restart
- **Enhanced Security Monitoring** — agents on cluster nodes generate file/process/network logs
- **TLS 1.2+ enforced** for all intra-cluster, egress, and metastore communication
- **Instance type allowlist** — only a subset of Azure VM SKUs permitted; **ARM64 explicitly blocked**; Azure Virtual Network encryption required (D, DS, E, ES v4/v5+ generation)
- **Port 2443 must be allowed outbound** if egress is restricted
- **Preview features blocked by default.** Only an explicit list of preview features can process PHI. The 2026-05-07 list of HIPAA-allowed preview features includes:
  - `LLM batch inference with ai_query`
  - `ai_forecast()`
  - `Agent Framework: On-behalf-of-user authorization`
  - …but pointedly NOT several Genie features, several agent features, many connectors
- **AI assistive features (Genie Code, Partner-powered AI features) disabled by default** on CSP workspaces — admin must consciously turn them back on
- **Account-level Genie does not aggregate data from CSP workspaces** — cross-workspace natural-language analytics is silently degraded for HIPAA workspaces

---

## BAA scope reality — what the BAA covers and doesn't

> *"You are solely responsible for verifying that sensitive information is never entered in customer-defined input fields, such as workspace names, compute resource names, tags, job names, job run names, network names, credential names, storage account names, and Git repository IDs or URLs. These fields might be stored, processed, or accessed outside the compliance boundary."*
>
> — [HIPAA on Azure Databricks docs](https://learn.microsoft.com/en-us/azure/databricks/security/privacy/hipaa)

**The architect implication for Optum:** the BAA boundary is the *VM instance and control-plane data path* — NOT "anything I type into Databricks." Naming a job `claims_member_12345_run_for_jane_doe` puts PHI into telemetry **outside the BAA**.

### Naming pollution — the lint discipline

You need a **naming-standards lint in CI** that rejects PHI-shaped job/cluster/tag names. The discipline:

- Reject names matching MRN-shaped patterns (`MBR-?\d{6,12}`, `\d{9}` for SSN-shaped)
- Reject names from a known-name dictionary
- Reject names containing date-of-birth-shaped patterns
- Audit existing artifacts for non-compliant names

This is a **CI gate**, not a documentation suggestion. Without it, engineers will name things by member ID for "convenience" and PHI leaks into the control plane.

---

## Customer-managed keys — three CMK products with distinct gaps

Azure Databricks has **three** separate CMK features (CMK overview, updated 2026-05-04). Premium plan required for all. Both Azure Key Vault and **Azure Key Vault Managed HSM** supported (Managed HSM = FIPS 140-2 Level 3, what UHG/Optum-tier security teams expect).

| CMK feature | Encrypts | Key location |
|---|---|---|
| **Managed services CMK** | Notebook source/metadata, secrets, Git PATs, AI/BI dashboards (only those created after Nov 1, 2024), Genie Spaces (only those created after Apr 10, 2025), Vector Search indexes, Lakebase project data, SQL queries and query history, model serving container images | Control plane |
| **DBFS root CMK** | DBFS root data, FileStore, Job results, Databricks SQL results, MLflow model artifacts, Lakeflow pipelines storage, notebook revisions, system data not accessible through DBFS | Workspace storage account in your subscription |
| **Managed disks CMK** | Temporary disk storage on cluster VMs (classic compute only) | Customer Azure subscription (managed disks) |

### The subtle, important gaps

**Serverless compute does not use the managed-disks CMK.** *"Customer-managed keys for managed disk storage do not apply to serverless compute resources. Disks for serverless compute resources are short-lived and tied to the lifecycle of the serverless workload."* For PHI workloads on serverless SQL warehouses, serverless jobs, or Model Serving, you cannot bring your own disk-encryption key — you accept platform default.

**Older AI/BI dashboards (pre-Nov 2024) and older Genie Spaces (pre-Apr 2025) are NOT encrypted with CMK at all.** If your Optum org spun up a Databricks workspace in 2023 with member-data dashboards, those dashboard objects in the control plane are **not** covered by your CMK. **Recreating them is the only fix.** Migration debt.

**Double encryption** on the workspace storage account is a separate setting (`Configure double encryption for DBFS root`), independent of CMK. Healthcare audit teams typically expect both.

**Storage account firewall** on the workspace storage account is yet another separate setting (Module 20).

**Key rotation is on you** — Azure Key Vault rotation policies apply, and Databricks picks up the new key version automatically on next access. There is no service-side rotation for managed-services CMK that Databricks owns.

---

## Audit log architecture for HIPAA

There are **two audit log surfaces**, and the difference matters legally.

### `system.access.audit` (Public Preview as of 2026-04-22)

Schema includes `event_time`, `user_identity`, `service_name`, `action_name`, `request_params` (a map), `response`, `source_ip_address`, `user_agent`, `audit_level` (WORKSPACE_LEVEL or ACCOUNT_LEVEL), `identity_metadata` (with `run_by` and `run_as` for service principals).

**This is the complete record** — every Unity Catalog action, every cluster, every job, every Genie operation, every model serving call, every secret access. Account-level events (workspace creation, account-admin actions) only appear here, with `workspace_id=0`.

### Azure Monitor diagnostic settings

Workspace-level only, missing `groups`, `clusterPolicies`, `vectorSearch`. Native Splunk/Sentinel/Chronicle integration via Event Hub or Log Analytics is here, but you're missing data.

### Two practical issues for HIPAA

**1. Retention.** The audit-logs reference page states *"Azure Databricks retains a copy of audit logs for up to 1 year"*. **HIPAA Security Rule 45 CFR §164.316(b)(2)(i) requires 6 years.** Native retention is **insufficient.**

**The architect's job:**
- Configure diagnostic settings to forward to a Log Analytics workspace, OR Event Hub → Splunk/Sentinel — with **6-year retention enforced on the destination**
- *Plus* schedule a `system.access.audit` ETL job snapshotting to a long-retention Delta table in a `_compliance` catalog with object replication or immutability policies

(Module 17 has the DLT pipeline shape.)

**2. Whether PHI ends up in audit logs.** `request_params` is a map of every parameter to every API call. SQL queries are logged in audit events; **literal values inlined into a query (e.g., `WHERE member_id = '12345678'`) will appear in `request_params`.** This means **audit logs themselves can contain PHI.**

The compliance boundary for the audit log destination must be at least as strict as the source workspace. For Splunk-bound logs, this is typically why payors send audit logs to a *separate, equally-locked-down* Splunk index with PHI handling controls, **or use a tokenizing forwarder.**

---

## Network isolation — the only architecture pattern a payor should accept

Module 20 covered the network architecture. The HIPAA-relevant summary:

- **VNet injection** + **SCC** (no public IP)
- **Six Private Endpoints**: front-end, back-end (control plane), back-end (SCC relay), ADLS Gen2, Key Vault, other PaaS
- **Workspace storage account firewall** with `dfs` and `blob` PEs
- **Browser-auth dedicated workspace per region** (single-PE-per-region constraint)
- **Azure Firewall Premium with TLS inspection** on egress
- **NAT Gateway** mandatory after March 31, 2026

For HIPAA, this is **all required.** Anything less and the security architects will (rightly) reject the design.

---

## PHI handling patterns

### Tokenization & column-level controls

UC ABAC (Public Preview, updated 2026-05-08) is the modern pattern (Module 9):

- **Governed tags** on columns (`pii.phi`, `hipaa.identifier_type=mrn`) propagate via tag inheritance, evaluated at query time
- **Row filter policies** and **column mask policies** attached at catalog/schema/table level — *one policy can cover thousands of tables*
- VARIANT-based UDFs for multi-type masking and struct redaction
- Limitation: workloads in R don't support dynamic views for row/column-level security on compute running DBR 15.3 and below

### De-identification through Azure Health Data Services

- **Azure API for FHIR is being retired Sept 30, 2026** (no new deployments after Apr 1, 2025); path forward = **Azure Health Data Services FHIR service**
- `$export` operation with `_anonymizationConfig=anonymizationConfig.json` (FHIR-Tools-for-Anonymization, HIPAA Safe Harbor sample)
- Standard payor pattern (Module 22 covers in detail):
  1. Source systems → AHDS FHIR service (PHI)
  2. `$export` with anonymization → ADLS deid container
  3. Databricks Auto Loader → Bronze → Silver → Gold (de-identified path)
  4. Original PHI Bronze in separate UC catalog `phi_raw_*` workspace-bound to PHI workspace; de-identified views feed analytics workspace

Microsoft is explicit: *"Microsoft is unable to evaluate de-identified export outputs or determine the acceptability for your use cases and compliance needs. The FHIR service's de-identified export is not guaranteed to meet any specific legal, regulatory, or compliance requirements."* The Safe Harbor config is a *starting point*; **privacy office signs off on final fhirPathRules.**

### dbignite (Databricks Labs) — legacy path

`github.com/databrickslabs/dbignite` was Databricks' OSS library for FHIR Bundle parsing, OMOP CDM landing, DICOM helpers; activity slowed after 2023 as Databricks shifted to proprietary "Lakehouse for Healthcare and Life Sciences" + partnerships. **Treat as legacy; verify 2026 status before depending on it.**

### Alternative payor pattern

- **HL7v2 ingestion** via Rhapsody or Mirth → Event Hubs / Kafka → Databricks Auto Loader → custom HL7 parser UDF → Bronze tables
- **OMOP CDM** as a Silver-layer model on top
- **John Snow Labs** for clinical NLP, de-id models, ICD-10 coding via foundation models in Model Serving

---

## AI/ML on PHI — the section where most teams break

### RAG over clinical notes

Vector Search indexes are control-plane objects encrypted by managed-services CMK. **Available in HIPAA regions.** Pattern is fine *if* source documents have been de-identified before indexing **or** chat surface restricted to authorized clinical users with end-to-end audit.

**Commonly-overlooked failure:** embedding models hosted as Foundation Models Pay-Per-Token are a third-party API call. Per HIPAA preview list, `Model Serving - Foundation Models Pay-Per-Token` is gated to HIPAA-supported regions — **but you must still confirm with Databricks whether the specific foundation model endpoint is BAA-covered.** **Default position: use Provisioned Throughput endpoints running inside your workspace, not pay-per-token, for any prompt containing PHI.**

### Foundation model APIs and BAA scope

The HIPAA list now explicitly includes:
- `LLM batch inference with ai_query` (HIPAA-only preview)
- `Agent Framework: On-behalf-of-user authorization` (HIPAA-only preview)

Recent — these were not HIPAA-eligible in 2024. **Implication: modern agent patterns are now compatible with HIPAA on Databricks**, where 18 months ago they were not.

### Model Serving inference logs

Inference Tables capture every request/response. **Will contain PHI if prompts contain PHI.** Stored in workspace storage account → covered by DBFS-root CMK. **Must be tagged in UC and protected with row filters or column masks.** Many teams forget the tables exist.

### Genie over PHI is genuinely dangerous

Genie's prompts and chat history are stored in the control plane (managed-services CMK applies, but only for spaces created after Apr 10, 2025). User questions like "show me member 12345's claims" become persisted artifacts. The Genie page makes clear that *"Row filters and column masks defined in Unity Catalog are automatically enforced per user"*, which is good — **but the natural-language question itself is not row-filtered.** A user with no access to a member can still type the member's MRN into the chat box and have it persisted.

**Recommendation for Optum: do not enable Genie on PHI catalogs at all; enable only on the de-identified analytics catalog or aggregate views.** The CSP-default of disabling AI assistive features supports this stance.

### BAAs typically exclude Beta and Preview features

Agent Bricks was Beta as of summit; flag for the security team. **Maintain a canonical list of BAA-covered features per workspace** (Module 17).

### Federated learning / privacy-preserving ML

Not native to Databricks. Pattern:
- **NVIDIA FLARE** or Azure Confidential Computing-based VMs
- Databricks orchestrates the federation rounds via jobs
- Confidential VMs (DCasv5/ECasv5 with AMD SEV-SNP) are supported as cluster instance types on Azure
- Architect must verify each is on the CSP allowlist

---

## Other compliance frames

From the security-profile page, Azure Databricks supports the following compliance standards via CSP:

- **GA (CSP required to process regulated data)**: C5, K-FSI (Korean Financial Security Institute), PCI-DSS, UK Cyber Essentials Plus, CCCS Medium (Protected B), TISAX
- **Public Preview (CSP strongly recommended, will be required at GA)**: HITRUST, IRAP, ISMAP
- **HIPAA**: CSP strongly recommended but technically not required (in practice, your privacy office will require it)
- **SOC 2 Type II**: held at platform level; not a workspace-level toggle

### Notable absences vs payor leadership asks

- **HITRUST CSF certification** is Public Preview only — meaningful because UHG-tier orgs frequently demand HITRUST attestation for new platforms. Serverless HITRUST support is even more limited, restricted to: `australiaeast`, `australiasoutheast`, `canadacentral`, `eastus`, `eastus2`, `germanywestcentral`, `northeurope`, `uksouth`.
- **FedRAMP High / IL5 / IL6** — Azure Databricks is available in Azure Government (`usgovvirginia`, `usgovarizona`) under FedRAMP High; IL5 available through specific configurations. **IL6 NOT covered by commercial Azure Databricks** — requires Azure Government Secret/Top Secret clouds with separate procurement.
- **NHS DSPT** — not a CSP toggle; covered by Microsoft's overall NHS DSPT attestation for Azure but no Databricks-specific certification.
- **GDPR** — handled via Microsoft DPA / Databricks DPA; no technical CSP toggle.

**For Optum specifically, HITRUST is the one to watch.** As long as Public Preview, "is HITRUST certified" gets a "no, not for the workspace itself yet" answer.

---

## What doesn't work well — architect's risk register

1. **Naming pollution.** Workspace/cluster/job/tag/repo names sit *outside* BAA. PHI sneaks in via convenience naming. **No platform-level lint.** Build your own.
2. **Notebook artifact auditability.** Cell outputs persist with PHI. Workspace setting *"Store interactive notebook results in customer account"* mitigates; rarely enabled.
3. **Genie's chat history** persisting natural-language questions about PHI.
4. **Model Serving inference tables** containing PHI.
5. **Audit log retention 1 year native vs HIPAA's 6.**
6. **DBFS mounts and legacy `/mnt/` paths** routinely violate UC isolation.
7. **Pre-Nov 2024 dashboards / pre-Apr 2025 Genie spaces** not encrypted with CMK. Migration debt.
8. **Egress without inspection.** SCC enables egress, but unless 0.0.0.0/0 forced through Azure Firewall Premium with TLS inspection, can't detect PHI exfiltration.
9. **Permanent CSP setting.** Cannot turn HIPAA off. Test workspaces should NOT have CSP+HIPAA enabled.
10. **March 31, 2026 outbound default change.** Module 20.
11. **Browser-auth single point of failure.** Module 20.
12. **NCC limits.** 50 workspaces per NCC, 100 PEs per region per account. At Optum scale, plan multi-account topology.
13. **Workspace-level SCIM is being deprecated** — must move to account-level SCIM.

---

## The 12-line "what does HIPAA-eligible mean in 2026" answer

For when you need to explain to a CISO or audit team in one breath:

1. Premium tier workspace
2. Enhanced Security and Compliance add-on (paid)
3. Compliance Security Profile enabled with `HIPAA` standard (permanent)
4. VNet injection + Secure Cluster Connectivity (no public IP)
5. Front-end + back-end Private Link, public network access disabled, NSG mode `NoAzureDatabricksRules`
6. Workspace storage account firewall enabled with `dfs` and `blob` private endpoints
7. CMK on managed services + DBFS root + managed disks (Azure Key Vault Managed HSM)
8. Unity Catalog with workspace-catalog binding splitting PHI from de-identified
9. ABAC governed tags + row filters + column masks for PHI
10. Audit logs forwarded via Event Hub to SIEM with 6-year retention (HIPAA), independent of Databricks's 1-year native retention
11. Naming standards lint to keep PHI out of BAA-external metadata fields
12. AHDS FHIR service for the authoritative PHI store, with `$export` de-identification feeding the analytics workspace

---

## Sanity check

1. Why is CSP enablement "permanent," and what's the operational implication for test workspaces?
2. Walk through the three CMK products and their gaps (especially serverless and pre-Nov 2024 dashboards).
3. The audit log retention gap: native = 1 year, HIPAA = 6 years. What's the architect's pipeline?
4. Why is Genie over PHI categorically dangerous, and what's the recommendation?
5. The naming-pollution lint — what does it check, and why is it a CI gate?
6. Foundation Model APIs pay-per-token under HIPAA — what's the Anthropic Claude caveat?
7. Recite the 12-line "HIPAA-eligible in 2026" answer.

---

## Further reading

- [HIPAA on Azure Databricks](https://learn.microsoft.com/en-us/azure/databricks/security/privacy/hipaa)
- [Compliance security profile](https://learn.microsoft.com/en-us/azure/databricks/security/privacy/security-profile)
- [Configure enhanced security and compliance settings](https://learn.microsoft.com/en-us/azure/databricks/security/privacy/enhanced-security-compliance)
- [Customer-managed keys for encryption](https://learn.microsoft.com/en-us/azure/databricks/security/keys/customer-managed-keys)
- [Audit log system table reference](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/audit-logs)
- [Unity Catalog ABAC](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/abac/)
- [FMAPI compliance / HIPAA](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/compliance)
- [Genie Spaces](https://learn.microsoft.com/en-us/azure/databricks/genie/)
- [Azure Health Data Services FHIR de-identified export](https://learn.microsoft.com/en-us/azure/healthcare-apis/fhir/deidentified-export)
- [Accountable HQ — Databricks HIPAA compliance write-up](https://www.accountablehq.com/post/databricks-hipaa-compliance-requirements-baa-and-best-practices-for-protecting-phi)
