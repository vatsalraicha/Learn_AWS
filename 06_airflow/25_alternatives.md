# 25 — Alternative orchestrators: Prefect, Dagster, Argo, Mage, Flyte, Step Functions, Databricks Workflows, Snowflake Tasks, ADF, Temporal

> *"The architect-grade insight: knowing when NOT to pick Airflow."*

## Why this module exists

Airflow is right for many things and wrong for others. This module is the honest comparison.

---

## 1. Prefect 3

- Rewrite of Prefect engine 2024.
- Pythonic (decorators).
- Strong cloud offering (Prefect Cloud).
- **Better at**: ad-hoc / event-driven workflows; modern Python ergonomics; pricing for small-medium teams.
- **Worse at**: ecosystem breadth (fewer providers); operator-grade auditability.

When to pick: Python-first shop, modern data stack, want lower ops than self-hosted Airflow.

---

## 2. Dagster

- Asset-centric model **from the start** (predates Airflow Datasets).
- Strong typing of inputs/outputs.
- Dagster+ cloud offering.
- Excellent lineage and observability.
- **Better at**: data platforms designed asset-first; rich UI for lineage.
- **Worse at**: classic ETL with many heterogeneous operators (smaller provider ecosystem).

When to pick: greenfield data platform, lineage-first design, willing to invest in Dagster patterns.

---

## 3. Argo Workflows

- CNCF Graduated.
- **YAML/CUE-based** workflow definitions.
- **K8s-native** — workflows are CRs; tasks are pods.
- Used heavily for ML / data pipelines on K8s.
- **Better at**: K8s-first shops; pure pipeline-of-pods; fits with Argo CD / Events ecosystem.
- **Worse at**: Python ergonomics; rich operator ecosystem.

When to pick: K8s-native shop, ML pipelines as DAGs of containers, want CNCF-aligned tooling.

---

## 4. Mage AI

- Newer entrant. Notebook-as-pipeline UI.
- Python + SQL.
- **Better at**: data engineer with notebook habits.
- **Worse at**: scale; smaller community; uncertain sustainability.

When to pick: small team, notebook-heavy workflow, willing to take adoption risk.

---

## 5. Flyte

- From Lyft. CNCF Incubating.
- **Strongly typed** Python pipelines.
- K8s-native execution.
- ML-leaning use cases.
- **Better at**: typed ML pipelines; reproducibility-first; tight K8s integration.
- **Worse at**: classic ETL ergonomics; smaller ecosystem.

When to pick: ML-platform team building typed reproducible pipelines on K8s.

---

## 6. AWS Step Functions

- **JSON state machines** (or CDK / SAM / Terraform definitions).
- AWS-native; serverless.
- **Capital One's published MLOps spine** uses Step Functions.
- **Better at**: AWS-native serverless workflows; integrates with every AWS service; cheap at low volume; auditable.
- **Worse at**: Python ergonomics; non-AWS systems; complex DAG visualization.

When to pick: AWS-only shop, simple-to-medium complexity, serverless economics matter.

For Capital One: **Step Functions is the right answer for ML pipelines** even if Airflow remains for data engineering.

---

## 7. Databricks Workflows / Lakeflow Jobs

- Built into the Databricks Lakehouse.
- JSON / UI / SDK.
- **Better at**: pipelines fully inside Databricks; cheaper DBU rate; tight Unity Catalog lineage.
- **Worse at**: orchestrating non-Databricks systems.

When to pick: pipeline is 100% Databricks; lakehouse-native.

---

## 8. Snowflake Tasks/Streams

- Inside-Snowflake DAGs of SQL.
- **Better at**: SQL transformations inside the warehouse; no external orchestrator needed.
- **Worse at**: anything outside Snowflake.

When to pick: warehouse-only data platform; transformation logic is SQL.

---

## 9. Azure Data Factory / Synapse Pipelines / Fabric Pipelines

- Microsoft-native low-code orchestration.
- **Better at**: drag-and-drop pipelines; Azure-service integrations; non-engineer users.
- **Worse at**: code-first ergonomics; reproducibility.

When to pick: Azure-only shop with mixed-skill users.

---

## 10. Temporal

- Workflow engine (different category).
- Code in Go / TypeScript / Python / Java.
- **Better at**: long-running stateful workflows (sagas, payment processing, user journeys).
- **Worse at**: data pipelines (wrong category).

When to pick: business workflows that span days/weeks with retries (orders, KYC, claims). Not data pipelines.

---

## 11. The 9-criteria decision matrix

| | Airflow 2/3 | Prefect 3 | Dagster | Argo | Step Functions | DBX Workflows |
|---|---|---|---|---|---|---|
| Python ergonomics | ✅ | ✅✅ | ✅✅ | ❌ (YAML) | ❌ (JSON) | ❌ (JSON) |
| K8s-native | ⚠️ | ⚠️ | ⚠️ | ✅✅ | N/A | N/A |
| Asset/lineage-first | ⚠️ (3.0) | ✅ | ✅✅ | ❌ | ⚠️ | ✅ (UC) |
| Provider ecosystem | ✅✅ | ⚠️ | ⚠️ | ❌ | AWS only | DBX only |
| Multi-tenancy | ⚠️ | ⚠️ | ✅ | ✅ | ✅ | ✅ |
| Regulated audit | ✅ | ⚠️ | ✅ | ⚠️ | ✅✅ | ✅ |
| Cost (steady state) | $$ | $$ | $$$ | $ | $ | $$$ |
| Multi-cloud | ✅ | ✅ | ✅ | ✅ | AWS | DBX |
| Community size | ✅✅ | ✅ | ✅ | ✅ | N/A | N/A |

---

## 12. Capital One verdict

Step Functions is the explicit answer for the **ML serving spine** + complex AWS workflows. Airflow lives at the **data engineering boundary** (warehouse loads, dbt orchestration).

For a Sr Lead candidate, the interview-defining framing:

> "I'd start by asking what's primary: warehouse-centric ETL with many provider integrations (Airflow), AWS-native serverless workflows with auditability (Step Functions), asset-first lineage (Dagster), or K8s-pure ML pipelines (Argo). At Capital One, I'd default to Step Functions for ML and Airflow for data engineering — exactly the pattern your engineering blog has published."

That answer demonstrates the architect-grade thinking the role rewards.

---

## Sanity check

1. Three scenarios where Step Functions beats Airflow on AWS.
2. Dagster's "asset-centric from the start" — what does that change in practice vs Airflow?
3. Argo Workflows — language? Execution model?
4. Temporal is a workflow engine, not an orchestrator. What's the practical difference?
5. Capital One's ML spine uses what, and why?

---

## Sources

- [Prefect 3](https://docs.prefect.io/3.0/)
- [Dagster](https://docs.dagster.io/)
- [Argo Workflows](https://argo-workflows.readthedocs.io/)
- [Mage AI](https://docs.mage.ai/)
- [Flyte](https://flyte.org/)
- [AWS Step Functions](https://docs.aws.amazon.com/step-functions/)
- [Databricks Workflows](https://docs.databricks.com/workflows/)
- [Temporal](https://docs.temporal.io/)

→ Next: [26 — CI/CD for DAGs](26_cicd_dags.md)
