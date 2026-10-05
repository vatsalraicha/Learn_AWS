# 01 — Airflow history & landscape: why Airflow, where it fits, where it doesn't

> *"Airflow won because Python won. Pick it for orchestration in a Python shop. Don't pick it just because everyone else did."*

## Why this module exists

Airflow is the most-deployed open-source workflow orchestrator. It's also the one most-cargo-culted. A senior engineer needs to know its history (why it exists), its strengths (Python-native, vast ecosystem), its weaknesses (scheduler heaviness, DAG=arbitrary-code), and its competitors (Prefect, Dagster, Argo, Step Functions, Databricks Workflows, Snowflake Tasks). This module is the honest 30-min orientation.

---

## 1. History — the milestones

| Year | Event |
|---|---|
| **2014** | Maxime Beauchemin starts Airflow at Airbnb |
| **2015 Jun** | Open-sourced under Apache License 2.0 |
| **2016 Mar** | Joins Apache Incubator |
| **2019 Jan** | Promoted to Apache Top-Level Project |
| **2020 Dec 17** | **Airflow 2.0** released — TaskFlow API, HA scheduler, DAG serialization |
| **2021** | Astronomer is the dominant commercial sponsor; AWS launches MWAA |
| **2022** | Airflow 2.3 → dynamic task mapping; 2.4 → Datasets |
| **2023** | Triggerer + deferrable operators GA; 2.7 → setup/teardown; 2.8 → Auth Manager |
| **2024** | 2.10 → DAG-level dataset events, hybrid executors |
| **2025 Apr 22** | **Airflow 3.0** — Task SDK, multi-cluster scheduler, React UI, deadlines, asset-centric scheduling, DAG versioning |

Airflow's evolution mirrors the data community's: started as a cron-on-steroids; became a full orchestrator; in 2025 became asset-centric (data-aware).

---

## 2. What problem Airflow solves

Pipelines that:

- Run on a schedule.
- Have task dependencies (DAG).
- Need retries, alerting, observability.
- Span heterogeneous systems (S3 → Glue → Snowflake → SageMaker).
- Need backfills.
- Need audit trails for regulated environments.

Airflow's value is the **operator ecosystem**: 1000+ pre-built operators (Snowflake, Databricks, SageMaker, S3, Slack, ...) — each is a Python class that handles auth, retries, and error semantics for one system. You compose them in Python; Airflow handles the rest.

---

## 3. What Airflow is NOT

- **Not a stream processor.** Airflow runs at minute-granularity scheduler heartbeats; for sub-second event processing, use Flink / Spark Structured Streaming.
- **Not a data-transformation engine.** It orchestrates other engines (Spark, Snowflake, Databricks) but DOESN'T execute transforms in the scheduler.
- **Not a queue.** It triggers tasks; it doesn't broker messages.
- **Not a CI/CD pipeline.** Argo Workflows / Tekton / Jenkins / GitHub Actions cover that.
- **Not a low-code "drag and drop" tool.** It's code-first; analysts who want point-and-click belong in ADF / Step Functions / Dagster Cloud's UI.

---

## 4. The "DAG file is arbitrary code" reality

Airflow DAGs are **Python files in a directory**. The scheduler imports them on every refresh. Implications:

- Top-level imports run in the scheduler — expensive imports slow everything down.
- Top-level code with side effects runs constantly — `requests.get(...)` at module level is a disaster.
- A DAG author with commit access can run arbitrary code in the scheduler context — **DAG authors == cluster admins**.

This is the single biggest security pain. Airflow 3.0's Task SDK fixes part of it (tasks run in an isolated execution interface), but the scheduler still imports DAG files.

For regulated finance: PR review every DAG; CI lints for top-level expensive operations; no `eval`, no `exec`.

---

## 5. The alternative orchestrators (honest comparison)

| Tool | Python? | K8s-native? | Asset/lineage-first? | Best for | Worst for |
|---|---|---|---|---|---|
| **Airflow 2.x** | Yes | Optional | Datasets (added 2.4) | General orchestration in Python shops | Stream / asset-first / multi-tenant security |
| **Airflow 3.x** | Yes | Optional | Yes (Assets) | Same + cleaner security model | Cutting edge; less battle-tested |
| **Prefect 3** | Yes | Optional | Yes | Pythonic, modern API; cloud good | Smaller community |
| **Dagster** | Yes | Optional | **Yes (asset-centric from the start)** | Modern data platforms with lineage-first design | Existing Airflow shops; cost |
| **Argo Workflows** | YAML/CUE | **Yes (K8s-native)** | No | ML/data pipelines on K8s | Non-K8s shops |
| **Mage AI** | Yes | Optional | Yes | SQL+Python notebooks-as-pipelines | Heavy enterprise scale |
| **Flyte** | Yes | **Yes** | Yes (typed pipelines) | ML pipelines, Lyft-style | Pure ETL |
| **AWS Step Functions** | JSON/CDK | No (serverless) | No | AWS-native; **Capital One's actual choice** | Multi-cloud, complex Python |
| **Databricks Workflows / Lakeflow Jobs** | JSON | Databricks | Limited | If you live in Databricks | Outside Databricks |
| **Snowflake Tasks/Streams** | SQL | No | Inside Snowflake | In-warehouse SQL DAGs | Cross-system |
| **ADF / Synapse Pipelines** | JSON/UI | Azure | Limited | Azure-first shops | Multi-cloud |
| **Temporal** | Multi-lang | Optional | No | Long-running workflows / sagas | Data pipelines |

For Capital One: **Step Functions is the published MLOps spine.** Airflow appears in data-engineering teams orchestrating ETL into Snowflake / Redshift. Knowing both — and when to pick which — is the architect-grade insight.

---

## 6. When to pick Airflow (the senior-engineer judgment)

✅ **Pick Airflow when**:
- Heavy Python shop with existing Airflow investment.
- Many heterogeneous systems to orchestrate (Snowflake + Databricks + SageMaker + email + ...).
- Strong operator ecosystem matters.
- Team can operate it (or has Astronomer / MWAA budget).
- Multi-day backfills are common (Airflow's `catchup` model fits).

❌ **Don't pick Airflow when**:
- Pure AWS-native shop with simple workflows → **Step Functions**.
- K8s-native data platform → **Argo Workflows** + Argo Events.
- Asset/lineage-first modern data platform from scratch → **Dagster**.
- Workflows are inside a single warehouse → **Snowflake Tasks / dbt + Airflow's narrower role**.
- Sub-second event-driven → **Flink / Kafka Streams**.

---

## 7. Airflow at Capital One — honest take

The published MLOps spine at Capital One (per Topic 04 research):

```
S3 → Glue / EMR → S3 → SageMaker Pipelines / Step Functions → KServe on EKS
```

**Step Functions is the headline orchestrator.** Airflow likely runs in data-engineering teams for nightly ETL into Snowflake / Redshift. Both coexist.

For the architect interview, the framing:

> "Airflow remains valuable for cross-system ETL where the Python operator ecosystem and audit trail matter — that's likely where C1's data engineering teams run it. For the ML production spine, Step Functions wins on AWS-nativity, JSON-based state machines that map cleanly to Cloud Custodian-style policy, and serverless economics. I would not introduce Airflow into a greenfield MLOps system at C1; I would use Step Functions + EKS + KServe."

This is a more credible answer than "Airflow is the best."

---

## 8. The 2025-2026 trends

- **Airflow 3.0** brings asset-centric scheduling, security improvements (Task SDK isolation), DAG versioning. Released April 2025; adoption ramping.
- **OpenLineage** is now the standard for lineage events; Airflow has it built-in.
- **dbt + Airflow via Cosmos** is the modern data-stack pattern.
- **Managed Airflow (MWAA, Composer, Astro)** dominates over self-host for new deployments.
- **Asset-first orchestrators** (Dagster) are gaining at the high end.

---

## Sanity check

1. Why was Airflow created (in one sentence)?
2. What changed conceptually between Airflow 2.x and 3.0?
3. "DAG authors == cluster admins" — why is this the case, and what's the practical mitigation in a regulated shop?
4. Capital One's published MLOps spine uses what orchestrator, not Airflow?
5. Three scenarios where you should pick something other than Airflow.
6. What's the role of OpenLineage in modern Airflow?

---

## Sources

- [Apache Airflow homepage](https://airflow.apache.org/)
- [Airflow blog: 2.0 announcement](https://airflow.apache.org/blog/airflow-two-point-oh-is-here/)
- [Airflow 3.0 announcement](https://airflow.apache.org/blog/airflow-3-0/)
- [Airflow Improvement Proposals (AIPs)](https://cwiki.apache.org/confluence/display/AIRFLOW/Airflow+Improvement+Proposals)
- [Capital One tech blog](https://www.capitalone.com/tech/)

→ Next: [02 — Core concepts](02_core_concepts.md)
