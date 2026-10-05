# 13 — Lineage with OpenLineage: Marquez, Atlan/DataHub, Unity Catalog interop

## Why this module exists

For regulated finance, "where did this number come from" is a compliance question, not a curiosity. OpenLineage is the standard for capturing it from Airflow.

---

## 1. OpenLineage in one paragraph

OpenLineage is an **open standard** (LF AI & Data) for capturing data lineage events. Each event names:

- A **job** (a pipeline / task).
- One or more **input datasets**.
- One or more **output datasets**.
- A **run** (instance of the job execution).
- **Facets** — typed metadata (schema, SQL, run metrics).

Tools EMIT OpenLineage events; backends INGEST them. Decoupled.

---

## 2. The Airflow + OpenLineage integration

`apache-airflow-providers-openlineage` (2.7+). Once installed and configured, **lineage is automatic** for many operators:

- SQL operators (Snowflake, BigQuery, Redshift, Postgres) — extract `INSERT INTO ... SELECT FROM ...` to lineage.
- S3, GCS, Blob operators — file inputs/outputs.
- Spark / Databricks / EMR / Dataproc operators — job + dataset lineage.
- Custom operators — implement `get_openlineage_facets_on_start` / `_on_complete`.

```python
# airflow.cfg
[openlineage]
transport = '{"type": "http", "url": "https://marquez.internal/api/v1/lineage"}'
namespace = "airflow-prod"
```

Done. Events flow.

---

## 3. Marquez — the reference backend

[Marquez](https://marquezproject.ai/) (LF AI & Data Sandbox) ingests OpenLineage events, stores in Postgres, exposes UI + API.

Visualization: graph of datasets + jobs; per-run details; schema history.

For small-to-medium teams: Marquez is great. Self-hostable via Helm chart.

---

## 4. Commercial OpenLineage consumers

| Tool | Notes |
|---|---|
| **DataHub** (Acryl) | LinkedIn open source + commercial; broad catalog + lineage |
| **Atlan** | Modern data catalog; OpenLineage native |
| **Collibra** | Enterprise data governance; OpenLineage support added 2023 |
| **Alation** | Enterprise catalog; OpenLineage support |
| **OpenMetadata** | OSS competitor to DataHub |
| **Amundsen** | LinkedIn-Lyft OSS catalog (predates OpenLineage; bridge exists) |

For Capital One–style regulated finance: catalog choice often Collibra (legacy enterprise) or DataHub (modern). OpenLineage feeds both.

---

## 5. Unity Catalog + OpenLineage

Databricks Unity Catalog has **native lineage** for Databricks-internal queries (notebooks, jobs, SQL warehouses). For end-to-end lineage that spans Airflow → Databricks → Snowflake:

- Airflow emits OpenLineage.
- Databricks emits Unity Catalog lineage natively + OpenLineage via the Spark Listener.
- Snowflake emits via Object Lineage / Account Usage views.
- A catalog (DataHub, Collibra) merges sources.

Unity Catalog → OpenLineage export was GA in 2024.

---

## 6. AWS Glue Data Catalog + Lake Formation lineage

AWS DataZone (now AWS SageMaker Catalog) added lineage in 2024. Glue ETL jobs emit lineage. Combined with OpenLineage from Airflow, end-to-end on AWS works.

---

## 7. The data-contract angle

OpenLineage + a data catalog tells you **what** happened. Data contracts add **expectations**:

- Producer commits: schema, freshness, SLA.
- Consumer asserts: schema match, freshness check, null rate.
- Catalog enforces: schema-change PRs require consumer ack.

Tools: **Soda**, **Great Expectations**, **dbt tests**, **Acryl DataHub Contracts**, **Snowflake Data Contracts**.

For ML: feature contracts are critical — silent schema changes destabilize models.

---

## 8. Operator coverage status (2026)

Most major operators have OpenLineage extractors. Coverage gaps where you'd write your own:

- Custom REST API calls (PythonOperator with `requests`).
- Internal-only data systems.
- Pre-2020 operators that pre-date the OL effort.

For PythonOperator: implement extractors via the OL Python library:

```python
from openlineage.airflow.utils import DagUtils

@task
def my_task():
    # ... do stuff ...
    DagUtils.emit_lineage(
        input_datasets=[Dataset(namespace="s3://myorg-data", name="input.parquet")],
        output_datasets=[Dataset(namespace="snowflake://prod.analytics", name="sales_curated")],
    )
```

---

## 9. rubicon-ml + OpenLineage at Capital One

Capital One's rubicon-ml (Topic 04 reference) is an experiment-tracking tool that focuses on lineage + auditability for ML training artifacts. It's complementary to OpenLineage:

- **OpenLineage**: dataset + job graph at the data layer.
- **rubicon-ml**: experiment artifacts (model + metrics + code git SHA) at the ML layer.

Together they answer: "this model in production was trained on this dataset version using this code commit." For SR 11-7 model governance, both halves are required.

---

## 10. The lineage stack for a regulated shop

```
Airflow → OpenLineage → DataHub (or Collibra)
Spark / Databricks → OpenLineage + Unity Catalog → DataHub
Snowflake → ACCOUNT_USAGE.OBJECT_DEPENDENCIES + OpenLineage → DataHub
S3 + Glue → AWS DataZone → DataHub
ML training → MLflow + rubicon-ml → DataHub (custom emitter)
```

Single pane in DataHub. Drill from "PII column appears in this dashboard" to "Airflow DAG that loaded it" to "S3 object it came from."

---

## Sanity check

1. OpenLineage is a standard. Marquez is what?
2. Most Airflow operators emit OpenLineage automatically. Which would you need to instrument manually?
3. Unity Catalog + OpenLineage — what's the bridging story for cross-system lineage?
4. Data contracts answer what question that OpenLineage alone does not?
5. Where does rubicon-ml fit alongside OpenLineage at Capital One?

---

## Sources

- [OpenLineage spec](https://openlineage.io/docs/)
- [Marquez](https://marquezproject.ai/)
- [Airflow OpenLineage provider](https://airflow.apache.org/docs/apache-airflow-providers-openlineage/stable/index.html)
- [DataHub](https://datahubproject.io/)
- [Databricks Unity Catalog lineage](https://docs.databricks.com/data-governance/unity-catalog/data-lineage.html)
- [rubicon-ml](https://github.com/capitalone/rubicon-ml)
- [SR 11-7 (Federal Reserve model risk guidance)](https://www.federalreserve.gov/supervisionreg/srletters/sr1107.htm)

→ Next: [14 — Observability](14_observability.md)
