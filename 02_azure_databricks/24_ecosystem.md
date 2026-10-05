# Module 24 — Ecosystem & Integration

> **Goal of this module:** know the third-party tooling teams build *around* Databricks because the platform either doesn't ship it, ships it incompletely, or healthcare orgs have already standardized on it. Cost, lineage, observability, DQ, security, orchestration, reverse ETL.
>
> **The "what's outside the Databricks brochure" map.**

---

## Why this module exists

Databricks ships a lot of "official" answers (DABs, Unity Catalog lineage, Lakehouse Monitoring, Workflows, Lakehouse Apps). For each of those, **there is an ecosystem of third-party and OSS replacements that exist for a reason** — rate limits, missing column-level lineage hooks, single-workspace assumptions, or simply that healthcare orgs already standardized on Datadog / Splunk / Immuta and aren't rebuilding their stack around UC.

This module is the map of what to know.

---

## CI/CD & deployment frameworks

(Module 19 covered this in detail; reprise:)

- **Databricks Asset Bundles** — Databricks-blessed; the default for new projects
- **Brickflow** (Nike OSS) — Pythonic DSL on top of DABs; for when YAML gets unwieldy
- **dbx** — DEAD; deprecated late 2023; never start new projects there
- **MLOps Stacks** — cookiecutter templates for ML projects on top of DABs
- **Terraform databricks/databricks provider** — for platform topology + account-level resources

---

## Cost optimization

### Native: System Tables

`system.billing.usage` + `system.compute.*` + `system.access.audit`. The API for FinOps. Most teams build their **own** Lakeview dashboard on top because the built-in cost dashboards are coarse.

### Sync Computing Gradient

[synccomputing.com](https://synccomputing.com/introducing-gradient-for-databricks/) — auto-tunes cluster shape (instance type, node count, spot vs on-demand) using ML. **Reported 30–60% production savings**, occasionally 5x vs serverless on classic clusters per [Sync benchmark](https://medium.com/sync-computing/optimizing-ec2-costs-on-databricks-fa67a02505ab). 2025 added job-level cost breakdown.

### Unravel

[unraveldata.com](https://www.unraveldata.com/solutions/technologies/databricks/) — APM-style observability + FinOps "Cost 360 for Databricks." Multi-platform (Databricks + Snowflake + EMR + BigQuery), which matters in healthcare conglomerates running multiple stacks. **Up to 70% wasted-spend reduction reported in 6 months.**

### Capital One Slingshot

[capitalone.com/software/products/slingshot](https://www.capitalone.com/software/products/slingshot/) — Databricks + Snowflake unified cost console. **Up to 40% savings**; 50K+ engineering hours saved/yr at Capital One itself.

### CloudZero

Cost-per-customer / cost-per-feature attribution. Best when you're building a SaaS on top of Databricks and need unit economics.

### Vantage.sh

Multi-cloud cost aggregation including Databricks. Good for multi-cloud shops.

### Dead/deprecated to know

- **Overwatch** (Databricks Labs) — was the canonical OSS cost+observability pipeline; **deprecated**, replaced by `system.billing.usage`. Plenty of orgs still run it; phase out.

### Architect take

- Native system tables + a Lakeview chargeback dashboard + cluster policies covers **80% of FinOps for under $50K orgs**.
- Add **Unravel** or **Slingshot** when DBU spend crosses ~$2M/yr — the human time saved becomes the ROI.

---

## Lineage & observability beyond Unity Catalog

UC ships table-level lineage and (since 2024) column-level lineage *for queries that ran in UC-governed compute*. **Gaps** (Module 11 covered):
- Cross-workspace lineage
- Spark structured streaming with custom sinks
- Lineage to/from non-UC systems (Kafka topics, S3 buckets via legacy mounts, external tools)
- Richer impact analysis

### OpenLineage + Marquez

[OpenLineage/OpenLineage](https://github.com/OpenLineage/OpenLineage) — installs as a Spark listener via init script ([Databricks integration folder](https://github.com/OpenLineage/OpenLineage/tree/main/integration/spark/databricks)). Marquez = LF AI & DATA reference backend.

**Open-spec escape hatch** — emit lineage to *any* backend (Marquez, DataHub, Atlan, Astronomer, Microsoft Purview).

### DataHub (Acryl)

[datahub-project/datahub](https://github.com/datahub-project/datahub) — Databricks/UC source documented at [docs.datahub.com](https://docs.datahub.com/docs/generated/ingestion/sources/databricks). Real-time Spark agent: [acryl-spark-lineage](https://docs.datahub.com/docs/metadata-integration/java/acryl-spark-lineage). **Column-level lineage native since v0.14.**

### Monte Carlo

[montecarlodata.com](https://www.montecarlodata.com) — most widely deployed data observability; pharma/financial services use cases. Now adds unstructured/LLM observability ([2025 expansion](https://www.techtarget.com/searchdatamanagement/news/366625053/Monte-Carlo-adds-observability-for-unstructured-data)).

### Other observability tools to know

- **Acceldata** ([acceldata.io/databricks](https://www.acceldata.io/databricks)) — Databricks-specific perf+cost+quality angle
- **Bigeye** — deep Databricks integration; SLA-precision pitch
- **Anomalo** — unsupervised ML anomaly detection; strong in regulated industries
- **Sifflet** — lineage + cataloging + observability bundled
- **Metaplane** — ACQUIRED by Datadog April 2025; now part of Datadog's data observability story
- **Atlan** ([atlan.com](https://atlan.com/databricks-lineage/)) — modern data catalog often paired with Databricks; positioned against DataHub for "active metadata"

### Datadog & Splunk

- **Datadog Databricks integration** ([docs.datadoghq.com/integrations/databricks](https://docs.datadoghq.com/integrations/databricks/)) — Spark metrics + cluster logs. Strong fit for healthcare orgs already paying Datadog.
- **Splunk** — many shops route Databricks **audit log delivery** (S3/ADLS) into Splunk for SIEM coverage. Module 17.

### Spline (legacy)

[absaoss/spline](https://absaoss.github.io/spline/) — older Spark lineage agent + UI, pre-OpenLineage. Mostly historical; still encountered in long-running European banking/insurance stacks.

### Architect take

- **UC lineage is necessary but not sufficient.** OpenLineage + DataHub or Monte Carlo is what you actually present to a healthcare compliance auditor when asked "show me where this PHI flows."
- **Don't fight Datadog / Splunk in healthcare.** Audit log delivery → Splunk is a fixed assumption in nearly every regulated org. Databricks's native dashboards lose to existing SOC tooling.

---

## Testing frameworks

### Nutter (Microsoft)

[microsoft/nutter](https://github.com/microsoft/nutter) — notebook test runner with `nutter run` CLI for CI; still maintained as of late 2025. Best for teams that *insist* on testing notebooks rather than refactoring to packages.

### chispa

[MrPowers/chispa](https://github.com/MrPowers/chispa) — pretty-printed PySpark DataFrame assertions. **De facto pytest companion for PySpark testing.**

### pytest-spark

pytest fixtures for SparkSession. Pair with chispa.

### Databricks Connect v2 + pytest (the "modern" pattern)

Run pytest *locally* against a remote serverless or all-purpose cluster. See [docs.databricks.com testing](https://docs.databricks.com/aws/en/notebooks/testing) and the [Databricks Community technical blog](https://community.databricks.com/t5/technical-blog/writing-unit-tests-for-pyspark-in-databricks-approaches-and-best/ba-p/122398).

### dbt-databricks tests

[databricks/dbt-databricks](https://github.com/databricks/dbt-databricks) — built-in test framework + `databricks_copy_into` macro. SQL-side answer for transformation correctness.

### DLT-META (data product test seam)

[databrickslabs/dlt-meta](https://github.com/databrickslabs/dlt-meta) — metadata-driven Lakeflow Declarative pipeline framework; `onboarding.json` schema is testable independently of pipeline runtime.

---

## Local dev / IDE story

- **Databricks Connect v2** — rewritten on Spark Connect protocol. Works with PyCharm, IntelliJ, VS Code, Cursor.
- **Official VS Code Extension** ([marketplace](https://marketplace.visualstudio.com/items?itemName=databricks.databricks)) — notebook sync, debugger via Databricks Connect, bundle deploy/run.
- **Third-party VS Code Extension** [paiqo/Databricks-VSCode](https://github.com/paiqo/Databricks-VSCode) — predates the official extension; still useful for cluster/job UX features the official one lacks.
- **JetBrains plugin** — shipped 2024; both IDEs use Databricks Connect under the hood.
- **Databricks CLI v0.218+** — single binary (Go); old Python CLI (≤0.18) is incompatible.

---

## Orchestration alternatives

Healthcare orgs almost always have an existing scheduler (Airflow, Control-M, IBM Workload Automation). **Databricks Workflows rarely *replaces* that;** it more often becomes a target invoked by the existing scheduler.

### Airflow + Databricks

- `apache-airflow-providers-databricks` ships `DatabricksRunNowOperator`, `DatabricksSubmitRunOperator`, `DatabricksSqlOperator`, `DatabricksWorkflowTaskGroup`
- **Astronomer Cosmos** for dbt-on-Databricks-via-Airflow: [astronomer/astronomer-cosmos](https://github.com/astronomer/astronomer-cosmos) — **200M+ downloads in 2025**

### Dagster + Databricks

Asset-centric model fits the lakehouse paradigm well; cross-workspace control plane is a real selling point.

### Prefect + Databricks

`prefect-databricks` block; smaller footprint than Airflow.

### dbt Cloud calling Databricks

Common pattern: dbt Cloud orchestrates dbt-databricks runs against a SQL Warehouse. Decouples transformation logic from Workflows.

### Reverse ETL (out of Databricks)

- **Hightouch** ([databricks integration](https://hightouch.com/docs/sources/databricks))
- **Census** (now part of Fivetran)
- **Multiwoven** ([multiwoven/multiwoven](https://github.com/Multiwoven/multiwoven)) — open-source alternative to Hightouch/Census; relevant if procurement blocks SaaS reverse ETL

Healthcare use: pushing curated cohorts to Salesforce Health Cloud, Epic-adjacent CRMs, payer outreach systems.

---

## Migration tooling

### UCX (Unity Catalog migration)

[databrickslabs/ucx](https://github.com/databrickslabs/ucx) — see Module 10. **No SLA, Labs project.**

### Remorph / Lakebridge (SQL transpilation)

[databrickslabs/remorph](https://github.com/databrickslabs/remorph) (renamed to **Lakebridge**) — SQL transpiler from **Snowflake/Teradata/Oracle/Synapse to Databricks SQL** + reconciliation tool. **Crucial for EDW migrations** at Optum scale.

---

## Notebook governance & code review

### blackbricks

[inspera/blackbricks](https://github.com/inspera/blackbricks) — runs `black` on Python cells + `sqlparse` on SQL cells of Databricks-format notebooks. **Vanilla `black` does NOT parse Databricks notebook headers.**

### nbstripout

[kynan/nbstripout](https://github.com/kynan/nbstripout) — strips notebook outputs before commit. Critical for `.ipynb` exports.

### Databricks Labs Pylint plugin

[databrickslabs](https://github.com/databrickslabs) — pylint checks for Databricks-specific anti-patterns (dbutils misuse, hardcoded cluster IDs).

### Databricks Labs Blueprint

[databrickslabs/blueprint](https://github.com/databrickslabs/blueprint) — internal building blocks (path handling, install logic, telemetry) used by UCX and other Labs projects.

---

## Data quality

### DLT / Lakeflow Declarative Expectations (native)

`EXPECT … ON VIOLATION DROP/FAIL` syntax inside Lakeflow Declarative Pipelines. Validation runs *during* the write transaction, not after. **Best for pipeline-shaped DQ.**

### Lakehouse Monitoring (native)

Time-series profile + drift metrics auto-generated for tables and ML models. **Best for "watch this table change over time" not "validate this batch right now."**

### DQX (Databricks Labs)

[databrickslabs/dqx](https://github.com/databrickslabs/dqx) — Spark-native DQ framework with row- *and* dataset-level checks, in-transit & at-rest validation, and a no-code **"DQX Studio"** Databricks App with AI-assisted rule generation. Newer than UCX, gaining traction.

### Great Expectations

[Great Expectations](https://greatexpectations.io) — pre-existing standard. Strong profiling and Data Docs. **Pattern: GX on raw zone, DLT expectations downstream.**

### Soda (Soda Core / Soda Cloud)

[soda.io/integrations/databricks](https://www.soda.io/integrations/databricks) — SodaCL config language; Metrics Observability + Collaborative Data Contracts launched 2025.

### Capital One DataProfiler (PII-focused)

[capitalone/DataProfiler](https://github.com/capitalone/DataProfiler) — pre-trained DL model for PII/NPI detection; useful in healthcare ingest before data hits the lakehouse.

### Deequ / PyDeequ (AWS Labs, adjacent)

Older but still encountered; constraint-suggestion is unique to Deequ's anomaly detection.

---

## Security / compliance wrappers

### Privacera

[privacera.com](https://privacera.com/blog/privacera-databricks-unity-catalog-a-secure-combination-for-open-data-sharing/) — extends UC with cross-platform fine-grained access control (when an org uses Databricks *plus* Snowflake, Trino, EMR, BigQuery). **Pitched as enterprise-wide vs UC's intra-Databricks scope.** HIPAA scenario: provider → payer Delta Sharing with row/column policy enforcement at the wire.

### Immuta

[immuta.com](https://www.immuta.com/blog/how-to-provision-access-in-databricks-unity-catalog-with-immuta/) — ABAC layer with dynamic masking, row filters, **purpose-based access**. Recent architecture changes made Immuta *additive* to UC grants ([Immuta changelog](https://changelog.immuta.com/en/architecture-improvements-and-updates-for-databricks-unity-catalog-integration-KyU8Qh6h)). Healthcare uses: **HIPAA Safe Harbor / Expert Determination tokenization at query time without copying tables.**

### BlueTalon — DEFUNCT

Acquired by Microsoft in 2019, folded into Purview. Mentioned only because older RFPs still reference it.

### Databricks Compliance Security Profile + BAA

Module 21 covered. The "official" answer.

### Microsoft Purview

Native catalog-level governance on Azure; integrates with UC via metadata sync. Healthcare orgs already on Microsoft 365 / Azure tend to use Purview as the enterprise catalog with UC as the lakehouse-local metastore.

---

## Bonus: Databricks Labs broader set

Worth knowing:
- **[databrickslabs/sandbox](https://github.com/databrickslabs/sandbox)** — experimental playground (often source of next-gen Labs projects)
- **[databrickslabs/lsql](https://github.com/databrickslabs/lsql)** — lightweight SQL execution wrapper on the SDK; valuable for serverless/Lambda apps that need to query Databricks without dragging in PySpark
- **[databrickslabs/mosaic](https://github.com/databrickslabs/mosaic)** — geospatial extension. **End of support with DBR 13.3 in August 2026** — successor is **GeoBrix**. Critical to know if you have geospatial workloads.
- **[databrickslabs/tempo](https://github.com/databrickslabs/tempo)** — time-series PySpark abstractions (sensor data, EHR vitals)
- **[databrickslabs/blueprint](https://github.com/databrickslabs/blueprint)** — see notebook governance section

---

## Other tools worth knowing

- **Polytomic** — ETL + reverse ETL combined; positioned against Hightouch/Census
- **ChaosSearch** — log/event analytics specifically against Databricks logs in object storage
- **Coalesce Quality** (formerly SYNQ), **DQLabs**, **Lightup**, **OvalEdge** — adjacent observability vendors with Databricks connectors
- **Rakuten SixthSense** — newer entrant against Monte Carlo / Bigeye / Acceldata

---

## Honest takeaways for an architect at Optum

1. **DABs is "good enough" for greenfield, painful for multi-tenant healthcare.** If you have multiple regulated workspaces (per business unit, per BAA scope), expect Terraform underneath DABs, plus Brickflow if your team writes Python.

2. **Cost optimization is mostly a process problem.** System tables + a Lakeview dashboard built in-house beat most third-party tools for awareness; **Sync Computing or Unravel earn their keep when you cross ~$1M/year DBU spend** or when ML-driven cluster shape tuning pays back its license fee.

3. **UC lineage is necessary but not sufficient.** OpenLineage + DataHub or Monte Carlo is what you actually present to a healthcare compliance auditor when asked "show me where this PHI flows."

4. **Don't fight Datadog / Splunk in healthcare.** Audit log delivery → Splunk is a fixed assumption in nearly every regulated org. Databricks's native dashboards lose to existing SOC tooling.

5. **Immuta vs Privacera vs UC-only is a procurement question, not a tech one.** UC alone covers the Databricks-only org. Multi-platform orgs (Databricks + Snowflake + Trino) almost universally pick Immuta or Privacera. **Healthcare slants toward Immuta because of its strong purpose-based access primitives matching IRB / 21 CFR Part 11 use-case framing.**

6. **Watch the deprecations:** dbx (dead), Overwatch (dead), Mosaic (dying Aug 2026 → GeoBrix), BlueTalon (acquired-and-buried). **Citing these in a roadmap doc dates you.**

7. **Bet your roadmap on Lakeflow + DABs + UC + Lakehouse Monitoring as the spine**, with **OpenLineage, Immuta or Privacera, Datadog/Splunk, and Sync/Unravel** as the *opinionated* additions. **That story sells in an architecture review.**

---

## Sanity check

1. Why is "system tables + a Lakeview dashboard" the right starting answer for FinOps before reaching for Sync or Unravel?
2. UC lineage + OpenLineage — what does each cover, and why do you usually need both for healthcare?
3. Immuta vs Privacera vs UC-only — what's the procurement-vs-tech framing?
4. Which Databricks Labs projects are dead or dying in 2026, and what should replace them?
5. Why does Databricks Workflows rarely *replace* an existing healthcare scheduler (Control-M, IBM Workload Automation)?

---

## Further reading

- [databricks/cli (Asset Bundles)](https://github.com/databricks/cli)
- [Nike-Inc/brickflow](https://github.com/Nike-Inc/brickflow)
- [Sync Computing — Gradient for Databricks](https://synccomputing.com/introducing-gradient-for-databricks/)
- [Unravel for Databricks](https://www.unraveldata.com/solutions/technologies/databricks/)
- [Capital One Slingshot](https://www.capitalone.com/software/products/slingshot/)
- [OpenLineage Spark integration](https://github.com/OpenLineage/OpenLineage/tree/main/integration/spark/databricks)
- [DataHub Databricks source](https://docs.datahub.com/docs/generated/ingestion/sources/databricks)
- [Monte Carlo data observability](https://www.montecarlodata.com)
- [Datadog Databricks integration](https://docs.datadoghq.com/integrations/databricks/)
- [Microsoft nutter (notebook tests)](https://github.com/microsoft/nutter)
- [MrPowers/chispa](https://github.com/MrPowers/chispa)
- [databrickslabs/ucx (UC migration)](https://github.com/databrickslabs/ucx)
- [databrickslabs/remorph (Lakebridge)](https://github.com/databrickslabs/remorph)
- [databrickslabs/dqx](https://github.com/databrickslabs/dqx)
- [Privacera Databricks integration](https://privacera.com/blog/privacera-databricks-unity-catalog-a-secure-combination-for-open-data-sharing/)
- [Immuta UC integration](https://www.immuta.com/blog/how-to-provision-access-in-databricks-unity-catalog-with-immuta/)
- [astronomer/astronomer-cosmos (Airflow + dbt + Databricks)](https://github.com/astronomer/astronomer-cosmos)
