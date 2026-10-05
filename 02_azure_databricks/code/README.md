# Code artifacts — Topic 02 Azure Databricks

> Runnable artifacts paired with the modules. Some run locally (.venv at the project root, Python 3.11); others require a Databricks workspace via `databricks-connect`.

## Inventory

| Artifact | Pairs with module | Runs |
|---|---|---|
| [`cluster_policies/`](cluster_policies/) | M2, M17 | JSON; apply via Terraform or Databricks API |
| [`chargeback.sql`](chargeback.sql) | M16 | DBSQL (system tables) |
| [`merge_scd2.py`](merge_scd2.py) | M3, M5 | Databricks Connect or workspace |
| [`ai_query_batch.py`](ai_query_batch.py) | M14, M15 | Databricks Connect or workspace |
| [`mlflow3_tracing.py`](mlflow3_tracing.py) | M12, M15 | Databricks Connect; needs MLflow 3.0+ |
| [`vector_search_demo.py`](vector_search_demo.py) | M13 | Databricks workspace required |
| [`audit_log_pipeline.py`](audit_log_pipeline.py) | M17, M21 | Lakeflow/DLT pipeline definition |
| [`hipaa_csp_check.py`](hipaa_csp_check.py) | M21 | Local — uses Databricks SDK |
| [`liquid_clustering_demo.py`](liquid_clustering_demo.py) | M3, M6 | Databricks workspace |
| [`dabs_bundle/`](dabs_bundle/) | M4, M19 | Bundle template + GHA workflow |

## Setup

```bash
# At the project root:
cd /Users/vr/Code/Career_upskill
source .venv/bin/activate

# Install Databricks-specific deps
pip install -r topics/02_azure_databricks/code/requirements.txt
```

## Stack convention

- No OpenAI; uses Anthropic Claude via Databricks FMAPI for LLM examples
- Targets DBR 17.3 LTS (Spark 4.0)
- Uses Databricks Connect v2 for local development against a remote cluster
- All examples assume Unity Catalog is enabled
