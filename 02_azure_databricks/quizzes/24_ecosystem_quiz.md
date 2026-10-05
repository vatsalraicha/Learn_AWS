# Quiz — Module 24: Ecosystem & Integration

## Recall

**Q1.** Why is "system tables + a Lakeview dashboard" the right starting FinOps answer before reaching for Sync Computing or Unravel?

<details><summary>Answer</summary>

**Because system tables (`system.billing.usage`, `system.compute.*`, `system.access.audit`) ARE the API for FinOps.** A Lakeview dashboard built on top covers ~80% of FinOps for orgs under $50K/yr DBU spend.

**Add third-party tools when:**
- **DBU spend crosses ~$2M/yr** — the human time saved tuning cluster configs across hundreds of jobs becomes the ROI
- **You need ML-driven cluster shape recommendations** — Sync Gradient learns from past runs
- **You need cross-platform cost** (Databricks + Snowflake + EMR + BigQuery in one view) — Unravel, Capital One Slingshot
- **Your team doesn't have data engineering capacity** to build the dashboards

**Don't reach for tools first.** Build the system-tables dashboard, get familiar with the data, identify the cost concentrators. The tools provide automation on top of the awareness; the awareness comes first.
</details>

**Q2.** Which Databricks Labs projects are dead or dying in 2026, and what replaces them?

<details><summary>Answer</summary>

- **dbx** — DEAD; deprecated late 2023. Replaced by **Databricks Asset Bundles (DABs).** Never start new projects on dbx.
- **Overwatch** — DEAD/deprecated; was the canonical OSS cost+observability pipeline. Replaced by **`system.billing.usage`** and friends (the system tables).
- **Databricks Labs Mosaic** — geospatial extension; **end of support with DBR 13.3 in August 2026.** Successor is **GeoBrix.** If you have geospatial workloads, plan migration.
- **BlueTalon** — DEFUNCT; acquired by Microsoft in 2019, folded into Purview. Mentioned because older RFPs still reference it.

**Citing these in a 2026 roadmap doc dates you.** Architects review docs to find these references and replace them.

**Still alive and recommended:**
- **UCX** — UC migration tool (Module 10)
- **DQX** — newer DQ framework, gaining traction
- **lsql** — lightweight SQL exec wrapper on the SDK
- **Tempo** — time-series PySpark
- **Blueprint** — internal building blocks for Labs projects
- **Lakebridge** (renamed from remorph) — SQL transpiler for EDW migrations
- **dlt-meta** — metadata-driven Lakeflow pipeline framework
</details>

---

## Apply

**Q3.** A peer asks you to recommend the third-party stack for a new Optum-scale Databricks platform. Walk through your tier-by-tier recommendation.

<details><summary>Answer</summary>

**The architect's recommended 2026 stack at Optum scale:**

**Tier 1 — Data platform spine (Databricks-native):**
- **Lakeflow** (Connect + Declarative Pipelines) for ETL
- **Unity Catalog** for governance
- **Databricks SQL Serverless** for BI
- **MLflow 3** for ML/GenAI lifecycle
- **Lakehouse Monitoring** for native DQ observability
- **DABs** for application deploy + **Terraform** for platform topology

**Tier 2 — Observability & cost (mostly third-party):**
- **Datadog Databricks integration** — Spark metrics + cluster logs (Optum already pays Datadog)
- **Splunk** — audit log forwarding for SIEM (industry standard)
- **Sync Computing Gradient** OR **Unravel** — once DBU spend > $2M/yr; pick based on workload mix and ML-driven recommendation appetite
- **Native system-tables Lakeview dashboard** — for cost attribution + chargeback (built in-house)

**Tier 3 — Lineage & catalog (UC + supplemental):**
- **UC native lineage** — for SQL/Spark-native operations
- **OpenLineage + DataHub** — for cross-platform lineage to/from non-Databricks systems and to support compliance "show me where PHI flows" questions
- **Microsoft Purview** — for enterprise catalog of catalogs (where Optum's Synapse, on-prem, SaaS sources are catalogued); **don't double-write policy**

**Tier 4 — Data quality (multi-layer):**
- **Lakeflow Declarative Expectations** at the pipeline level
- **Lakehouse Monitoring** for drift / time-series profile
- **DQX** (Databricks Labs) for row + dataset-level checks
- **Capital One DataProfiler** for PII/NPI detection at ingest

**Tier 5 — Access control (UC + Immuta):**
- **UC ABAC + row filters + column masks** for the Databricks-only paths
- **Immuta** for purpose-based access (HIPAA Minimum Necessary) and cross-platform extension if Optum has Snowflake/Trino footprint
- **Privacera** alternative if procurement prefers it; technically equivalent for healthcare

**Tier 6 — Orchestration:**
- **Databricks Workflows** for Databricks-internal scheduling
- **Existing Optum scheduler (Control-M / Airflow)** continues to invoke Databricks for jobs that span multiple systems
- **Astronomer Cosmos** if dbt-on-Databricks-via-Airflow becomes the pattern

**Tier 7 — Reverse ETL:**
- **Hightouch or Census** for pushing curated cohorts to Salesforce Health Cloud, Epic-adjacent CRMs, payer outreach systems

**Tier 8 — Local dev / IDE:**
- **Databricks Connect v2 + VS Code official extension** as the standard
- **`pyproject.toml` with pinned `databricks-connect` version** for team coordination
- **`uv` or `poetry`** for env management

**The pitch:**
- "Databricks spine + observability with what we already pay for (Datadog/Splunk) + targeted third-party tools where they earn their keep (Sync/Unravel for cost, OpenLineage + Immuta for compliance lineage and purpose-based access)."
- "Avoid the dead tools (dbx, Overwatch, Mosaic, BlueTalon)."
- "Build the system-tables Lakeview dashboard before reaching for SaaS — most FinOps awareness comes from looking at the right query, not from buying a tool."
</details>

---

## Defend

**Q4.** A peer says "we should use Workflows for everything — replace our Control-M scheduler entirely." Defend or refute for an Optum-scale healthcare org.

<details><summary>Answer</summary>

**Refute, decisively.**

Where the peer's instinct is right:
- **Workflows is the right scheduler for Databricks-internal jobs.** Cluster lifecycle, dependency graphs, retries, alerting all integrated.
- **For Databricks-only workloads,** Workflows beats invoking from an external scheduler — fewer moving parts.

Where the peer is wrong for Optum:
- **Healthcare orgs almost always have an existing scheduler** (Control-M, IBM Workload Automation, Airflow). These coordinate jobs across **many systems**: mainframes, claims engines, EDI gateways, EHR integration layers, ERP, Databricks. **Replacing Control-M with Workflows means rebuilding all those non-Databricks integrations.**
- **The existing scheduler has years of operational maturity** — runbooks, on-call training, monitoring integrations, vendor support contracts.
- **Cross-system dependencies** (e.g., "Databricks job runs after EDI ingest completes from Optum's claims system") need a scheduler that sees both sides.
- **Compliance and audit posture** — auditors are familiar with the existing scheduler's audit trail; Workflows-only is a new audit story.

**The right pattern (and the canonical 2026 healthcare pattern):**

- **Existing scheduler as the meta-orchestrator** — Control-M / Airflow runs the cross-system DAG.
- **Databricks Workflows as the destination** — Control-M invokes a Databricks Workflow via REST or Airflow's `DatabricksRunNowOperator`.
- **Astronomer Cosmos** for the dbt-on-Databricks-via-Airflow pattern — 200M+ downloads in 2025; battle-tested.
- **dbt Cloud** for SQL-transformation orchestration; calls Databricks SQL Warehouse.
- **Databricks Workflows owns the within-Databricks DAG** — task dependencies, cluster sharing, retries within a single Databricks run.

**The architect's pitch:**
- "Workflows is the right answer for the Databricks-internal dimension. Control-M is the right answer for the cross-system dimension. They compose."
- "Replacing Control-M with Workflows means rebuilding our integration with the EDI gateway, the EHR layer, the mainframe claim cycle. That's months of platform engineering for no real benefit."
- "Use Workflows where it shines (Databricks-internal); leave Control-M / Airflow for cross-system coordination."

**Where you might consolidate:** if a team is greenfield-Databricks-only with no existing scheduler dependency, Workflows-only is fine. **Most healthcare teams aren't greenfield.**

**Sources:** [Apache Airflow providers Databricks](https://airflow.apache.org/docs/apache-airflow-providers-databricks/stable/index.html), [Astronomer Cosmos](https://github.com/astronomer/astronomer-cosmos).
</details>
