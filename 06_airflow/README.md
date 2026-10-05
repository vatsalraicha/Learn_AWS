# Topic 06 — Apache Airflow for AI/ML Engineers (Multi-cloud + security + data-exposure lens)

> **Audience:** Senior AI/ML Engineer (Optum, Azure shop) preparing for **Sr Lead AI/ML Engineer at Capital One** (AWS-native, regulated finance, Snowflake + Databricks + EKS-KServe spine). Already comfortable authoring Airflow DAGs, but needs **operational, security, and architectural depth** to be credible at the Lead/Architect level.
>
> **Goal:** A teaching corpus where every module is research-backed. The unifying thread is *how Airflow safely exposes data and credentials* — to workers, to downstream systems (Snowflake/Databricks/SageMaker/Vertex/Azure ML), to operators (the humans), and across cloud boundaries. We cover **MWAA, Cloud Composer, Azure Managed Airflow, Astronomer, and self-hosted on-prem** in depth.
>
> **Branch:** `topic-06-airflow`
>
> **Last updated:** 2026-05-21

---

## Promise

Same standard as Topic 04 and 05. Research-before-writing. Citable facts in [`FACTS.md`](FACTS.md) with last-verified dates. Primary sources (Airflow Improvement Proposals, AWS/GCP/Azure pricing pages, Astronomer docs, OpenLineage spec) archived under [`../../research_inputs/06_airflow/downloads/`](../../research_inputs/06_airflow/downloads/).

The **explicit user ask** for this topic is:

> *"Cover all possible scenarios on how people use and expose data within Airflow safely and securely. Cover this for on-premise, AWS, GCP, Azure."*

That ask drives the module structure. **Every** Airflow primitive module addresses the data-exposure / credential-exposure angle; Parts D and E carry the cloud-specific deep dives.

## Learning path

| # | Module | Why it matters |
|---|--------|----------------|
| **Part A — Airflow fundamentals (1–6)** | | |
| 1 | [History & landscape — why Airflow, where it fits, where it doesn't](01_history_landscape.md) | Airbnb origin → 2.x rewrite → 3.0 deep change; honest comparison vs Prefect/Dagster/Argo/Step Functions/Databricks Workflows |
| 2 | [Core concepts — DAG, Task, Operator, Sensor, Hook, Connection, Variable, XCom, Pool, SLA/Deadline, Dataset/Asset](02_core_concepts.md) | The 30-minute mental model. Get these right, the rest is mechanics. |
| 3 | [Architecture — Webserver, Scheduler, Triggerer, Workers, Metadata DB, DAG storage](03_architecture.md) | Where does code actually run? What's HA, what's a single-point-of-failure? |
| 4 | [Executors deep — Sequential / Local / Celery / Kubernetes / CeleryKubernetes / Edge](04_executors.md) | The choice that determines your security boundary, scale ceiling, and ops burden |
| 5 | [DAG authoring — TaskFlow API, dynamic task mapping, deferrable operators, setup/teardown](05_dag_authoring.md) | Modern Pythonic Airflow vs Airflow-1.x-style classic operators |
| 6 | [Scheduling deep — logical date, data interval, timetables, catchup, backfill, Datasets/Assets](06_scheduling.md) | The single most misunderstood part of Airflow. Get it right or suffer. |
| **Part B — Sensors, secrets, and security (7–10)** | | |
| 7 | [Sensors & triggers — poke vs reschedule vs deferrable; Triggerer process](07_sensors_triggers.md) | Why your scheduler is dying: too many poke-mode sensors. Deferrable is the fix. |
| 8 | [Connections, Variables, and Secrets Backends](08_secrets_backends.md) | The fernet_key, the secrets_backend interface, AWS/GCP/Azure/Vault wiring, rotation patterns |
| 9 | [**Securing Airflow** — RBAC, Auth Manager, FAB, OIDC/SAML/LDAP, audit logs, the DAG-author = admin problem](09_securing_airflow.md) | The honest security story: DAG code is arbitrary execution. How do regulated shops actually control this? |
| 10 | [**Networking Airflow** — private webserver, mTLS, VPC endpoints, egress controls, blast-radius scoping](10_networking.md) | What does "Airflow on a private network" actually mean across clouds? |
| **Part C — Data flow, lineage, observability (11–14)** | | |
| 11 | [XCom & data passing — limits, custom XCom backend (S3/GCS/Azure), anti-patterns](11_xcom_data_passing.md) | The 48KB warning, the 1GB hard ceiling, and the right way to pass data between tasks |
| 12 | [Data-flow design — idempotency, hash-based skip, sensors→triggers, dataset-driven scheduling](12_data_flow_design.md) | The patterns that separate "DAG that works in dev" from "DAG that survives prod for 3 years" |
| 13 | [Lineage with OpenLineage — Marquez, Atlan/DataHub integration, Unity Catalog interop](13_lineage_openlineage.md) | OpenLineage is GA in Airflow; lineage is now a compliance requirement, not nice-to-have |
| 14 | [Observability — StatsD, Prometheus, OpenTelemetry, structured logs, callbacks, log handlers per cloud](14_observability.md) | Where logs actually go on MWAA vs Composer vs Azure Managed vs self-hosted |
| **Part D — Managed Airflow per cloud (15–19)** | | |
| 15 | [Airflow on Kubernetes — KubernetesExecutor, KubernetesPodOperator, in-cluster auth, KEDA scaling](15_airflow_on_k8s.md) | The pattern that underlies *every* managed offering and most self-hosted deployments today |
| 16 | [**MWAA — AWS Managed Workflows for Apache Airflow**](16_mwaa_aws.md) | Environment classes, VPC requirements, S3 DAG bucket, requirements.txt constraints, IAM execution role vs DAG IAM, Secrets Manager backend, CloudWatch logs, scaling, cost |
| 17 | [**Cloud Composer — GCP**](17_composer_gcp.md) | Composer 2 vs Composer 3; Workload Identity; Private IP env; PSC; Secret Manager backend; CMEK |
| 18 | [**Azure Managed Airflow** — Workflow Orchestration Manager in ADF + Fabric Apache Airflow Jobs](18_azure_managed_airflow.md) | Git-sync DAG model, Key Vault backend, MSI vs SP, ADF integration patterns |
| 19 | [**Astronomer (Astro Hosted vs Astro Hybrid)** + self-hosted on-prem (official Helm chart, HA Postgres, KEDA workers, Vault, air-gap)](19_astro_and_onprem.md) | The two non-cloud-native paths: managed-Astro and DIY-Helm. Trade-offs, cost, security posture |
| **Part E — Integrations (20–25)** | | |
| 20 | [Snowflake + Redshift + BigQuery + Synapse — DWH operator patterns, auth (key-pair, OAuth, IAM)](20_dwh_integrations.md) | The 80% case for Airflow at most shops. Capital One uses Snowflake heavily. |
| 21 | [Databricks integration — RunNow/SubmitRun/Notebook/Task operators, DBX Workflows interop, DAB + Airflow](21_databricks_integration.md) | Capital One runs Databricks; how Airflow conducts it without becoming the bottleneck |
| 22 | [Spark family — EMR, EMR Serverless, EMR on EKS, Dataproc Serverless, HDInsight, AWS Glue](22_spark_emr_dataproc_glue.md) | When to push compute to Spark instead of running it in an Airflow worker |
| 23 | [ML platform operators — SageMaker, Vertex AI, Azure ML, MLflow, Kubeflow Pipelines](23_ml_platforms.md) | What's first-class and what isn't; SageMaker has the deepest provider, Azure ML is thinnest |
| 24 | [Airflow + dbt — Astronomer Cosmos (the right way), dbt Cloud operator, BashOperator (the wrong way)](24_dbt_airflow.md) | Cosmos renders each dbt model as a task; you finally get task-level retries on dbt |
| 25 | [Alternative orchestrators — Prefect 3, Dagster, Argo, Mage, Flyte, Step Functions, Databricks Workflows, Snowflake Tasks, ADF, Temporal — decision matrix](25_alternatives.md) | An honest "when not to pick Airflow" guide. Capital One's MLOps spine uses Step Functions, not Airflow. |
| **Part F — Production, scale, future (26–32)** | | |
| 26 | [CI/CD for DAGs — pytest + dag_maker, `airflow dags test`, image-based deploy, blue/green DAGs](26_cicd_dags.md) | DAGs are code; treat them like code |
| 27 | [SRE — stuck queues, scheduler heartbeat, zombie tasks, sql_alchemy_pool, sensor deadlocks](27_sre_failure_modes.md) | The on-call playbook for Airflow at scale |
| 28 | [Cost & scaling — worker autoscaling, KEDA on K8s, deferrable for cost, multi-tenant patterns](28_cost_scaling.md) | The $50k/mo MWAA bill that becomes $8k/mo with deferrable operators + right-sizing |
| 29 | [Multi-tenancy patterns — namespaced executors, one-Airflow-per-team vs one-big-cluster](29_multi_tenancy.md) | The org-design question that determines your security model |
| 30 | [**Airflow 3.0 deep — Task SDK, deadlines, multi-cluster scheduler, asset-centric, UI rewrite, DAG versioning**](30_airflow_3.md) | The biggest change since 1.x → 2.x. Released April 2025. |
| 31 | [Migration & version strategy — 1.x → 2.x → 3.x; LTS lines; provider package versioning](31_migration.md) | When to upgrade, what breaks, who's still on 2.x |
| 32 | [Certifications — Astronomer Certified Astronomer (3 levels), DEA-C01 / Pro Data Engineer / DP-700 / DP-203 Airflow coverage](32_certifications.md) | Recommended sequence with buy/skip verdicts |

## Companion files

- [`FACTS.md`](FACTS.md) — atomic citable facts (provider package versions, MWAA env class pricing, Composer 3 GA, Airflow 3 release date, exam costs)
- [`00_Table_Of_Contents.md`](00_Table_Of_Contents.md) — master index of all modules + companion files + quizzes + code
- [`quizzes/`](quizzes/) — grouped per part
- [`code/`](code/) — example DAGs (TaskFlow, deferrable, dynamic task mapping), Helm values fragments, Terraform for MWAA/Composer, custom XCom backend, OpenLineage wiring, Cosmos+dbt example, KubernetesPodOperator + IRSA example, Secrets Backend examples per cloud
- [`../../research_inputs/06_airflow/`](../../research_inputs/06_airflow/) — deep-research reports + [`downloads/`](../../research_inputs/06_airflow/downloads/) archive

## How to use this

1. **Modules 1–6** are the conceptual core. Read in order even if you have authored DAGs before — scheduling (module 6) and executors (module 4) are where most Airflow users have shaky mental models.
2. **Modules 7–10** are the security/networking/secrets block. This is what makes the difference between "engineer who uses Airflow" and "engineer who designs Airflow deployments."
3. **Modules 11–14** cover the data plane. Lineage (module 13) and OpenLineage in particular are now compliance-grade tooling.
4. **Modules 15–19** are the managed-Airflow comparison. Module 15 (K8s) is the conceptual prerequisite for all four managed offerings — they're all KubernetesExecutor underneath.
5. **Modules 20–25** are integrations. Module 25 (alternatives) is the most important one for an architect — knowing when *not* to pick Airflow is a senior skill.
6. **Modules 26–29** are the production / SRE / cost block.
7. **Module 30** (Airflow 3) and **Module 31** (migration) are the forward-looking block.
8. **Module 32** maps to certs.

## Scope notes

- **Cutoff:** **2025–early 2026**. Airflow 3.0 released April 2025; provider package versions reflect the 2026 state. `FACTS.md` carries last-verified dates.
- **Cross-references to Topic 04 & 05:** Airflow rides on top of K8s/EKS/GKE/AKS (Topic 05) and talks to S3/EFS/EMR/Redshift/SageMaker (Topic 04). We don't re-derive concepts already covered there — we link.
- **Stack convention:** Airflow 2.10+ / Airflow 3 for new content; we call out 2.x-only features explicitly.
- **Cert mapping:** in module 32.

## Stack baseline (additions to the project `.venv`)

```
apache-airflow[celery,kubernetes,amazon,google,microsoft.azure,snowflake,databricks,dbt-cloud,openlineage]==2.10.*
# (we install 2.x for stable examples; Airflow 3 install instructions in module 30)

astronomer-cosmos                 # dbt + Airflow done right
openlineage-airflow               # lineage
apache-airflow-providers-snowflake
apache-airflow-providers-databricks
apache-airflow-providers-amazon
apache-airflow-providers-google
apache-airflow-providers-microsoft-azure

# Dev / testing
pytest-airflow
pytest
ruff

# Local
astro-cli                         # Astronomer CLI, installed separately (brew on macOS)
```

## Research provenance

This corpus is built from research reports under [`../../research_inputs/06_airflow/`](../../research_inputs/06_airflow/), plus archived primary-source documents under [`../../research_inputs/06_airflow/downloads/`](../../research_inputs/06_airflow/downloads/) (Airflow docs, AIPs, provider package READMEs, AWS/GCP/Azure managed-service docs, Astronomer documentation, OpenLineage spec, CNCF state-of-the-orchestration reports).
