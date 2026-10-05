# Quiz — Module 1: Lakehouse Foundations & Platform Anatomy

> Take this cold, no peeking. Answers in collapsed `<details>` blocks.

---

## Recall

**Q1.** What is the difference between the *control plane* and *data plane* in Azure Databricks, and which Azure subscription does each live in?

<details><summary>Answer</summary>

The **control plane** runs in **Databricks' own Azure subscription**. It hosts the workspace UI / REST API, account console, Unity Catalog metastore, MLflow experiments and model registry, the job scheduler, secret metadata, and notebook source. It does not see your data — it sees commands and stores derived metadata about runs, lineage edges, and audit events.

The **data plane** runs in **your Azure subscription, in your VNet**. Cluster VMs, serverless workers, your ADLS Gen2 storage accounts, and the workspace storage account live here. Your data stays here and never crosses into Databricks' subscription.
</details>

**Q2.** How many Unity Catalog metastores can you have in a single Azure region under one Databricks account?

<details><summary>Answer</summary>

**Exactly one.** UC metastores are regional and singleton — one per cloud region per Databricks account. This means lineage doesn't cross region boundaries, permissions don't cross region boundaries, and cross-region disaster recovery is a customer-driven workspace replication exercise (Module 23 covers it).
</details>

**Q3.** What are the two distinct line items in a Databricks bill, and roughly what's the rule of thumb for total spend relative to DBU spend?

<details><summary>Answer</summary>

**DBU charge** (Databricks software fee) + **Azure compute/storage/network charge** (Microsoft). They appear in different places in Azure Cost Management. Practitioner rule of thumb: **budget $2–$3 of total spend per $1 of DBU spend**. Forecasts that count only DBUs are systematically low.
</details>

**Q4.** Name three Databricks acquisitions and what each became.

<details><summary>Answer</summary>

Any three of:
- **MosaicML** (Jun 2023, ~$1.4B) → Mosaic AI brand and the foundation-model training/serving stack
- **Arcion** (Oct 2023, ~$100M) → Lakeflow Connect's CDC engine
- **Lilac** (Mar 2024) → Mosaic AI dataset/eval tooling
- **Tabular** (Jun 2024, $1B+) → UC managed Iceberg + UniForm + Iceberg REST (the Iceberg creators)
- **BladeBridge** (early 2025) → DW migration tooling (Teradata/Netezza → Databricks)
- **Neon** (May 2025, ~$1B) → Lakebase
- **Mooncake Labs** (2025) → Lakebase acceleration
</details>

**Q5.** What is the recommended Databricks Runtime LTS to standardize new pipelines on for 2026 greenfield work, and why?

<details><summary>Answer</summary>

**DBR 17.3 LTS** (released October 2025). It ships **Apache Spark 4.0**, has 2 years of support runway, and includes the current Photon improvements and full UC managed Iceberg support. DBR 16.4 LTS is acceptable if there's a hard dependency on Spark 3.5; 14.x and earlier are end-of-support and should not be in greenfield work.
</details>

---

## Apply

**Q6.** A new Optum business unit has just inherited a Standard-tier Databricks workspace via an acquisition. The acquired team uses it heavily for interactive notebook work on All-Purpose Compute. What's going to happen on or before October 1, 2026, and what's the cost implication?

<details><summary>Answer</summary>

The Standard workspace will **auto-upgrade to Premium** (no new Standard-tier workspaces have been creatable since April 1, 2026). For the All-Purpose-heavy interactive workload, expect a **~35% DBU rate increase** at migration. Plan for: (a) a finance conversation about the cost shift, (b) an audit of Premium-only features now available (UC ABAC, customer-managed keys, IP access lists) that the team should adopt to extract value from the price increase, and (c) a healthcare-specific compliance review since the team is now joining an Optum BAA scope.
</details>

**Q7.** You're designing the workspace topology for a new healthcare AI initiative on Optum's Azure tenant. Why is "one big workspace for everything" the wrong answer, and what topology would you propose instead?

<details><summary>Answer</summary>

One big workspace fails for at least four reasons:

1. **PHI vs non-PHI isolation** — workspace-catalog binding is the load-bearing primitive for "even with a bad grant, this user cannot reach PHI from this workspace." Collapse the workspaces, you collapse that boundary.
2. **Cost attribution at the team level** — single-workspace tagging is doable but inferior to per-team workspaces for chargeback clarity.
3. **Blast radius of admin error** — a misconfigured cluster policy or budget policy in a single workspace hits everyone; sharded workspaces contain the damage.
4. **Browser-auth PE single-point-of-failure** — one PE per region per DNS zone; deleting the host workspace breaks SSO for every dependent workspace, so you actually want a *dedicated* private-web-auth workspace per region.

Proposed topology for an Optum-grade healthcare initiative:
- **Tier-0 governance workspace** (per region) — metastore admin role, UCX runs, audit jobs, locked-down, MFA + conditional access, no general user notebooks
- **Browser-auth workspace** (per region) — hosts the browser-auth PE, no general work
- **PHI workspace** (per business unit) — CSP=HIPAA, VNet-injected, SCC, full PE topology, bound to `prod_phi_*` catalogs only
- **Analytics workspace** (per business unit) — bound to `prod_deidentified_*` catalogs, where ML / Genie / dashboards live
- **Dev/stage workspaces** — shared subscription, separate from prod subscriptions
</details>

---

## Diagnose

**Q8.** A junior engineer on your team proudly shows you a notebook called `claims_member_12345_run_for_jane_doe.ipynb` running in your HIPAA-eligible workspace. The notebook itself contains no PHI in its source code. Is there a problem? What is it?

<details><summary>Answer</summary>

**Yes — there's a real HIPAA problem.** The BAA boundary follows the data plane, not the entire Databricks platform. **Customer-defined fields that flow to the control plane — workspace names, cluster names, job names, notebook names, tags, secret-scope names, query parameters — are *outside* the BAA scope.** The notebook source code may be free of PHI, but the *filename* is itself a control-plane artifact: it gets stored in notebook revision history, appears in audit logs, surfaces in workspace search results, and travels with the artifact in any export. Embedding `member_12345_for_jane_doe` in the filename is a PHI disclosure outside the BAA boundary.

Fixes: (a) rename the notebook to a member-anonymous identifier; (b) introduce a **naming-standards lint** in CI that rejects PHI-shaped names (member IDs, SSN-like patterns, names from a known-name dictionary) in workspace assets; (c) include this in the platform team's quarterly compliance review.
</details>

**Q9.** Your team is debating whether to commit to Databricks for a 5-year roadmap. The CFO is worried about lock-in and wants to know what's reversible vs irreversible. Walk through the answer.

<details><summary>Answer</summary>

**Reversible (data layer):**
- Delta tables in your own ADLS — readable by Spark OSS, by Iceberg-aware engines via UniForm, by DuckDB, by Trino. Storage lock-in is essentially zero.
- UC-managed Iceberg tables — readable+writable from external engines via Iceberg REST Catalog API. Snowflake's Iceberg-write-to-UC is GA on Azure as of April 6, 2026.
- Unstructured files in UC Volumes — Parquet/ORC/PDF/etc, exit is straightforward.

**Reproducible-with-engineering:**
- Notebooks (exportable but format-shifted)
- Lakeflow pipelines (re-implementable on OSS Spark Declarative Pipelines once Spark 4.1 ships)
- DBSQL warehouses (rewrite for Snowflake or Trino)
- MLflow run history (exportable but lineage links break)
- Mosaic AI Vector Search indexes (rebuild on Pinecone, Azure AI Search, Qdrant)
- Mosaic AI Model Serving endpoints (re-deploy on Azure ML / vLLM-on-AKS / Bedrock)
- Agent Framework wrappers (rewrite to LangGraph + your own gateway)

**Hardest to rebuild — the moat:**
- Unity Catalog grants, ABAC policies, governed tags, lineage, audit history. UC itself.
- AI Functions in SQL (`ai_query`, `ai_classify`, `ai_extract`) embedded in production logic
- Agent Bricks template optimizations

**Discipline to reduce the risk:** keep your data in Delta or UC-managed Iceberg, transformation logic in dbt or as portable PySpark, your model registry exportable, and your governance documented in catalog metadata that's exportable. Avoid putting irreplaceable IP into Mosaic-only constructs until they have multi-year track records.

**Vendor risk:** Series L (Sept 2025) raised >$4B at $134B valuation with $4.8B revenue run-rate at 55% YoY growth. The company is well-funded; vendor risk for a 5-year commitment is low.
</details>

---

## Defend

**Q10.** A peer architect argues "lakehouse is just marketing — it's all open-source Spark + Parquet underneath, the platform is replaceable." Defend or refute.

<details><summary>Answer</summary>

**Both partially right.**

Where the peer is right:
- The storage layer (Parquet + Delta or Iceberg) is genuinely open. You can leave Databricks-the-platform without leaving your data.
- Spark is OSS. Photon is proprietary, but the workload runs on Spark APIs.
- Benn Stancil's [*Category collapse*](https://benn.substack.com/p/category-collapse) makes the case that lakehouse marketing is denser than the engineering substance because the substance is mostly OSS.
- A determined platform team with vLLM-on-AKS can match Mosaic AI Model Serving on $/token at the cost of platform engineering.

Where the peer is wrong:
- **Unity Catalog is not OSS-replaceable** at the same maturity. ABAC, governed tags, the three-level namespace, system tables, and lineage form a governance plane that takes years to rebuild.
- **The integrated ML lifecycle** — MLflow tracking + UC model registry + Vector Search + Model Serving + AI Gateway, all governed by UC — is operationally cheaper than assembling the equivalent from OSS components, and a healthcare org will value the cohesion over the OSS-purity argument.
- **The one-platform-for-data+ML+AI claim is real** for workloads that genuinely span all three. The Akincilar SQL benchmark (Snowflake 58% faster, 28% cheaper on pure SQL) is real, *and* it's not the workload Databricks is optimized for.
- **Mosaic AI's HIPAA-eligible Foundation Model APIs** (the 2025 unlock) eliminate a class of architecture that previously required AOAI as the only BAA-covered LLM path. That's a substantive product win, not marketing.

The honest synthesis: **the storage moat is small, the governance + integration moat is large, the cost is real.** The right move for an architect is to use Databricks' best parts seriously while keeping the data layer portable, so you have an exit option you don't need.
</details>

**Q11.** Your CFO asks: *"Why are we not just consolidating on Microsoft Fabric, since we're an Azure shop and it would be one less vendor?"* Make the case for keeping Databricks alongside Fabric.

<details><summary>Answer</summary>

The honest answer is *workload-specific.* Frame it this way:

**Where Fabric wins:**
- Steady-state, high-utilization BI and analytics workloads — Fabric's capacity-unit pricing model beats Databricks PAYG when utilization is consistently >70%.
- Power BI integration is tighter (same vendor, same identity, OneLake shortcuts).
- Lower-floor cost for BI-focused teams not doing ML or large-scale Spark.

**Where Databricks wins:**
- ML/AI workloads — Mosaic AI (Vector Search, Model Serving, FMAPI, MLflow 3, Agent Framework) is a mature stack; Fabric's AI story is thinner.
- Large-scale Spark ETL — Photon, AQE, Liquid Clustering, Predictive Optimization are real engineering wins on petabyte-scale workloads.
- Multi-cloud optionality — Databricks runs on Azure, AWS, GCP. Fabric is Azure-only. Healthcare orgs operating across cloud regions or with M&A history value this.
- HIPAA-eligible Foundation Model APIs (the 2025 BAA unlock).

**The 2026 enterprise pattern that's emerging:**
*"Successful enterprises in 2025 aren't choosing one platform — they're orchestrating two or three"* ([Polestar Analytics](https://medium.com/@polestaranalytics/comparing-databricks-snowflake-and-fabric-why-all-three-are-the-best-approach-b04e814caa86)). Snowflake or Fabric for governed BI, Databricks for ML/AI, with **Unity Catalog as the source of truth and OneLake mirrors / Iceberg interop bridging to other engines.**

**Concrete number** (for the CFO conversation): the Aimpoint Digital benchmark showed a low-utilization workload at $915 on Databricks vs $8,409 on Fabric, while at over-utilization the gap closed to $13,735 vs $16,818. Capacity-unit pricing on Fabric is great when you're saturated; PAYG on Databricks wins on bursty. **Pick the engine that fits the workload shape, not the vendor that fits the procurement org chart.**

That said, if the CFO's real concern is "one less vendor relationship," the architecturally clean answer is: **use both, with Databricks as the data + ML platform of record, OneLake as the BI-mirror layer, Power BI on top, and Unity Catalog as the universal governance plane.** That's the multi-platform pattern healthcare orgs are actually shipping in 2026.
</details>
