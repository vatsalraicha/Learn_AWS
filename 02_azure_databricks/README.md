# Topic 02 — Azure Databricks

> **Audience:** Senior AI/ML Engineer (Optum, Azure-shop) targeting AI Architect or Engineering Manager. Already fluent in Python and PySpark. Already done Topic 01 (RAG/Vector DBs/Reranking).
>
> **Goal:** A teaching corpus that goes beyond marketing — production reality, performance discipline, admin operations, healthcare/HIPAA architecture, and the strategic lens for an architect-track engineer.
>
> **Last updated:** 2026-05-10

---

## Learning path

| # | Module | Why it matters |
|---|--------|----------------|
| **Foundations (1–7)** | | |
| 1 | [Lakehouse foundations & platform anatomy](01_foundations.md) | Why Databricks exists, control plane vs data plane, account vs workspace, the 2026 product map |
| 2 | [Compute model deep dive](02_compute_model.md) | Clusters, Photon, serverless, cluster policies, instance pools, init scripts, Photon ROI math |
| 3 | [Delta Lake fundamentals + 2025-2026 reality](03_delta_lake.md) | ACID, transaction log, Liquid Clustering, Predictive Optimization, deletion vectors, UniForm |
| 4 | [Notebooks vs Jobs vs Workflows vs Lakeflow Declarative Pipelines](04_notebooks_jobs_workflows_lakeflow.md) | When to use which orchestration surface; the DLT→Lakeflow rebrand |
| 5 | [Spark on Databricks — practitioner discipline](05_spark_practitioner.md) | Spark UI diagnostics, MERGE/SCD2, Auto Loader, streaming watermarks, schema evolution |
| 6 | [PySpark + SQL performance on Databricks](06_performance.md) | Joins, skew, AQE, shuffle, caching layers, Photon-aware code, file layout for query speed |
| 7 | [Databricks SQL & DBSQL](07_dbsql.md) | Warehouses, Photon SQL, materialized views & streaming tables, predictive I/O |
| **Governance & catalog (8–10)** | | |
| 8 | [Lakeflow Connect & ingestion](08_ingestion.md) | Managed connectors, Auto Loader, Structured Streaming patterns; vs Fivetran/Airbyte |
| 9 | [Unity Catalog deep](09_unity_catalog.md) | Three-level namespace, ABAC, dynamic views, the three-permission collision, Azure RBAC bypass |
| 10 | [HMS → UC migration reality](10_uc_migration.md) | UCX, HMS Federation, the 10-month timeline, war stories |
| 11 | [UC adjacency products](11_uc_adjacency.md) | Lineage (and what it misses), Lakehouse Federation, Delta Sharing, Volumes & FUSE |
| **ML/AI track (12–15)** | | |
| 12 | [MLflow 3.0 deep](12_mlflow3.md) | Tracking + registry + GenAI tracing + prompt registry + eval harness |
| 13 | [Mosaic AI Vector Search & RAG-on-Databricks](13_vector_search_rag.md) | Delta Sync, hybrid BM25+ANN, scale limits, healthcare ICD/CPT use case |
| 14 | [FMAPI + Model Serving + AI Gateway](14_serving_gateway.md) | Pay-per-token vs PT, the HIPAA breakthrough, Anthropic native, scale-to-zero reality |
| 15 | [Agent Framework / Agent Bricks / AI Functions / fine-tuning](15_agents_finetune.md) | Lakeguard, MCP bridging, IFT/CPT/LoRA, why pre-training is not the enterprise pattern |
| **Operations (16–20)** | | |
| 16 | [Cost & FinOps for AI architects](16_cost_finops.md) | DBU mechanics, system tables, attribution, Photon/serverless ROI, DBCU forfeit trap |
| 17 | [Admin playbook — accounts, workspaces, identity, audit](17_admin_playbook.md) | Role hierarchy, cluster policies, budget policies, identity ops, audit pipeline, runbooks |
| 18 | [Production pain, anti-patterns, war stories](18_production_pain.md) | What teams hit, who left and why, happy-path vs reality |
| 19 | [CI/CD with Asset Bundles + Terraform](19_cicd.md) | DABs, Brickflow, OIDC federation, environment promotion, testing in CI |
| 20 | [Networking, Private Link, SCC, VNet](20_networking.md) | Six-PE HIPAA topology, NCC limits, browser-auth PE footgun, Mar 31 2026 NAT change |
| **Healthcare & regulated (21–22)** | | |
| 21 | [HIPAA on Azure Databricks 2026](21_hipaa.md) | CSP permanent setting, three CMK products, BAA scope, audit retention vs HIPAA's 6 yrs |
| 22 | [Healthcare reference architectures](22_healthcare_archs.md) | Payor patterns (claims X12, Member 360, HEDIS, HCC), FHIR + AHDS de-id, two-workspace split |
| **Strategic (23–25)** | | |
| 23 | [Disaster Recovery & multi-region](23_dr_multiregion.md) | Customer-driven reality, active-passive vs active-active, deep clone, GRS gotchas |
| 24 | [Ecosystem & integration](24_ecosystem.md) | Observability (Datadog/Splunk/MC), DQ (DQX/GE/Soda), security wrappers (Privacera/Immuta) |
| 25 | [Cert paths & decision framework](25_certs_decisions.md) | DBX DE/ML/GenAI Engineer Associate vs AZ-305/AI-102; the 12-17 week recommended path |

## Companion files

- [`FACTS.md`](FACTS.md) — atomic, citable facts (numbers, model names, GA dates, retirements). Single source of truth, updated whenever something stale gets caught.
- [`quizzes/`](quizzes/) — per-module questions. Recall + apply + diagnose + defend. Use to test understanding after reading.
- [`code/`](code/) — runnable artifacts (`.py` notebooks via `# %%` cells, JSON cluster policies, Terraform modules, SQL queries).
- [`references/`](references/) — downloaded papers and archived blog posts where licensing allows.

## How to use this

1. Read modules in order **1 → 7** for foundations and Spark-on-Databricks discipline. **6** is the "make code fast" module worth a slow read.
2. **8 → 11** is the governance/catalog cluster — Unity Catalog dominates the architect interview.
3. **12 → 15** is the ML/AI track — builds on Topic 01's RAG/eval material with Databricks-specific surfaces.
4. **16 → 20** is operations — Cost, Admin, CI/CD, Networking. Read sequentially.
5. **21 → 22** is the Optum lens — regulated industry / HIPAA / healthcare.
6. **23 → 25** closes the corpus with strategic decisions: DR, ecosystem fit, cert paths.

Each module ends with a **Sanity check** — 3–5 questions you should be able to answer in your head before moving on. After finishing a module, take its quiz cold (no peeking).

Cross-reference [`FACTS.md`](FACTS.md) anytime you want a number, GA date, or citation.

## Scope notes

- **Cutoff:** content reflects **2025–early 2026** state of the art. Databricks ships features fast — re-verify GA/preview status before betting a roadmap on a single feature. `FACTS.md` carries "Last verified" dates.
- **Bias:** Azure Databricks (Optum is an Azure shop). AWS-specific differences are flagged where they matter; GCP is essentially ignored.
- **Anti-bias:** treats marketing critically. War stories, anti-patterns, and "why teams left" sit alongside the official path.
- **Stack convention:** no OpenAI in code samples; prefer Anthropic Claude or open-source models. PySpark code assumes fluency (no DataFrame intro).
- **Healthcare lens:** HIPAA, BAA scope, Compliance Security Profile, audit-log retention, naming-pollution discipline are woven throughout, not bolted on at the end.

## Stack baseline (additions to the project `.venv`)

```
databricks-sdk
databricks-connect    # version-pinned per cluster DBR
databricks-cli        # >=0.218
pyspark               # for local Spark fallback
delta-spark           # local Delta
mlflow                # >=3.0 for GenAI features
anthropic             # for AI Functions / Claude as judge examples
```

## Research provenance

This corpus is built from 11 deep research reports under [`../../.claude/worktrees/gifted-kilby-e6bd76/research_inputs/`](../../.claude/worktrees/gifted-kilby-e6bd76/research_inputs/) covering: production pain (`01`), third-party ecosystem (`02`), Unity Catalog governance (`03`), healthcare/HIPAA (`04`), 2024-2026 features (`05`), AI/ML for engineers (`06`), cost & FinOps (`07`), certs/networking/CI-CD (`08`), PySpark+SQL performance (`09`), Delta internals & data modeling (`10`), and admin operations (`12`). Plus a consolidated mid-research checkpoint (`00`) with 176 items beyond the original prompt seeds.
