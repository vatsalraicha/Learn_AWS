# 21 — Databricks integration: operators, auth, DBX Workflows interop, DAB

## Why this module exists

Capital One uses Databricks. Optum uses Databricks. Knowing the Airflow ↔ Databricks operator zoo is muscle memory for this user.

---

## 1. The operator zoo

Provider: `apache-airflow-providers-databricks`.

| Operator | Use |
|---|---|
| `DatabricksRunNowOperator` | Trigger an **existing** Databricks Workflow job by job_id |
| `DatabricksSubmitRunOperator` | One-shot run (no persistent job) |
| `DatabricksNotebookOperator` | Run a notebook directly with params |
| `DatabricksTaskOperator` + `DatabricksWorkflowTaskGroup` | **Orchestrate a Databricks Workflows job from Airflow tasks** — the modern pattern |
| `DatabricksSqlOperator` | SQL on a Databricks SQL Warehouse |
| `DatabricksRunSensor` | Wait for a Databricks job |
| `DatabricksJobRunSensor` | Same with deferrable |

---

## 2. Auth — the ladder

| Auth | Mechanism | When |
|---|---|---|
| PAT (Personal Access Token) | Static token in Connection | Dev only |
| Service Principal (M2M OAuth) | Client ID + secret → OAuth | Standard prod |
| Azure MSI | Managed Identity (Azure-only) | Azure-native Databricks |
| AWS IRSA → cross-account | EKS pod assumes role in Databricks-account | EKS+Databricks-on-AWS |

For Capital One: SP+OAuth M2M is the typical pattern.

Connection extras:

```json
{
  "host": "https://myorg.cloud.databricks.com",
  "auth_type": "service_principal_oauth",
  "client_id": "<sp-app-id>",
  "client_secret": "<from-vault>",
  "tenant_id": "<aad-tenant>"
}
```

---

## 3. DatabricksWorkflowTaskGroup — the cost saver

```python
from airflow.providers.databricks.operators.databricks_workflow import DatabricksWorkflowTaskGroup
from airflow.providers.databricks.operators.databricks import DatabricksTaskOperator

with DAG(...) as dag:
    with DatabricksWorkflowTaskGroup(
        group_id="dbx_workflow",
        databricks_conn_id="databricks_prod",
        job_clusters=[{
            "job_cluster_key": "main",
            "new_cluster": {
                "spark_version": "15.4.x-scala2.12",
                "node_type_id": "i3.xlarge",
                "num_workers": 4,
            },
        }],
    ) as dbx_group:
        notebook1 = DatabricksTaskOperator(
            task_id="prep", notebook_task={"notebook_path": "/Workspace/Repos/prod/prep"},
            job_cluster_key="main",
        )
        notebook2 = DatabricksTaskOperator(
            task_id="train", notebook_task={"notebook_path": "/Workspace/Repos/prod/train"},
            job_cluster_key="main",
        )
        notebook1 >> notebook2
```

Databricks renders this as a **single Workflows job with multiple tasks** — billed at the cheaper **Jobs** rate (~$0.07/DBU) instead of **All-Purpose** (~$0.40/DBU). 5-6x cost reduction for production pipelines.

Critical pattern. Bring up in interviews.

---

## 4. The Databricks Workflows alternative

Databricks has its own orchestrator: **Workflows / Lakeflow Jobs**. For workflows fully inside Databricks:

✅ **Use Databricks Workflows when**:
- Pipeline is 100% Databricks notebooks/jobs.
- You want lakehouse-native cost (Jobs rate).
- No need to coordinate non-Databricks systems.

✅ **Use Airflow when**:
- Pipeline spans Databricks + Snowflake + S3 + SageMaker + Slack.
- You need Airflow's audit trail / SLA tooling.
- You're already on Airflow.

Both coexist at Capital One: Databricks Workflows for in-platform, Airflow for cross-platform.

---

## 5. DAB (Databricks Asset Bundles) + Airflow

DAB is Databricks' IaC for jobs/notebooks/workflows. Pattern:

1. DABs define the Databricks job in YAML (`databricks.yml`).
2. `databricks bundle deploy` ships it.
3. Airflow `DatabricksRunNowOperator(job_id="${{ dab.job_id }}")` triggers.

Separates job definition (DAB, owned by Databricks team) from orchestration (Airflow DAG, owned by data eng).

---

## 6. Cluster patterns

- **Job cluster** — ephemeral, created for one job, terminated after. Best cost.
- **All-purpose cluster** — long-lived, shared. Convenient but expensive.
- **Serverless SQL warehouse** — for SQL queries.
- **Serverless Jobs compute** — newer; auto-scaled.

For Airflow-triggered: **job cluster** unless you have specific reasons.

---

## 7. Anti-patterns

| Anti-pattern | Fix |
|---|---|
| `DatabricksSubmitRunOperator` for every task (orphan clusters) | `DatabricksWorkflowTaskGroup` (shared cluster) |
| PAT auth in prod | Service Principal OAuth |
| All-purpose cluster (DBU rate) | Job cluster |
| Hardcoded notebook paths | Use git-backed Repos + ref by path |
| Long-poll sync wait | `DatabricksJobRunSensor` with `deferrable=True` |

---

## Sanity check

1. `DatabricksWorkflowTaskGroup` saves what cost factor over `DatabricksSubmitRunOperator` per task?
2. Service Principal OAuth vs PAT — why prefer SP?
3. When does Databricks Workflows beat Airflow?
4. DAB + Airflow pattern — who owns what?
5. Deferrable `DatabricksJobRunSensor` — what does it save?

---

## Sources

- [Databricks provider](https://airflow.apache.org/docs/apache-airflow-providers-databricks/stable/)
- [DatabricksWorkflowTaskGroup](https://airflow.apache.org/docs/apache-airflow-providers-databricks/stable/operators/workflow.html)
- [Databricks Asset Bundles](https://docs.databricks.com/en/dev-tools/bundles/index.html)

→ Next: [22 — Spark family — EMR, EMR Serverless, Dataproc, Glue](22_spark_emr_dataproc_glue.md)
