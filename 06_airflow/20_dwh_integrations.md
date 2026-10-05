# 20 — Snowflake, Redshift, BigQuery, Synapse — DWH operator patterns & auth

## Why this module exists

Data warehouses are the 80% destination for Airflow ETL. This module covers the operators and auth patterns for each.

---

## 1. Snowflake (Capital One uses heavily)

Provider: `apache-airflow-providers-snowflake`.

```python
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator

load_sales = SnowflakeOperator(
    task_id="load_sales",
    snowflake_conn_id="snowflake_prod",
    sql="""
        MERGE INTO analytics.sales s
        USING staging.sales_raw st
        ON s.id = st.id
        WHEN MATCHED THEN UPDATE SET ...
        WHEN NOT MATCHED THEN INSERT ...
    """,
)
```

### Auth options (in order of safety)

- **Key-pair auth** (RSA): recommended. No password rotation; revoke key in Snowflake to revoke access.
- **OAuth (M2M)** with external IdP (Okta/Azure AD).
- **Username + password** with SSO: legacy; avoid for service accounts.

Connection extras for key-pair:

```json
{
  "account": "myorg-prod",
  "warehouse": "ETL_WH",
  "database": "PROD",
  "role": "AIRFLOW_ETL_ROLE",
  "authenticator": "snowflake_jwt",
  "private_key_file": "/run/secrets/snowflake_private_key.p8"
}
```

### Snowflake PrivateLink

Connection host: `myorg.privatelink.snowflakecomputing.com`. Traffic stays inside cloud backbone.

### Async SnowflakeSqlApiOperator

For long-running queries (>1min): `SnowflakeSqlApiOperator` returns immediately; Triggerer polls async. Workers stay free.

### Snowpipe pattern

For continuous loads: Snowpipe (Snowflake-managed) loads automatically from S3. Airflow merely triggers and monitors.

---

## 2. Redshift

Provider: `apache-airflow-providers-amazon`.

Two operators:
- **`RedshiftSQLOperator`** — connects via JDBC.
- **`RedshiftDataOperator`** — uses the **Redshift Data API** (HTTP, IAM-auth, async).

For serverless-friendly: `RedshiftDataOperator`. No long-lived JDBC connection; IAM auth via task role.

```python
from airflow.providers.amazon.aws.operators.redshift_data import RedshiftDataOperator

load = RedshiftDataOperator(
    task_id="load",
    workgroup_name="my-serverless-workgroup",       # for Redshift Serverless
    database="dev",
    sql="COPY analytics.sales FROM 's3://...' IAM_ROLE '...' FORMAT AS PARQUET",
    deferrable=True,                                 # async polling
)
```

Copy from S3 with IAM role (no static creds). Standard pattern.

---

## 3. BigQuery

Provider: `apache-airflow-providers-google`.

```python
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator

load = BigQueryInsertJobOperator(
    task_id="load",
    configuration={
        "query": {
            "query": "INSERT INTO dataset.sales SELECT * FROM dataset.staging_sales WHERE ds='{{ ds }}'",
            "useLegacySql": False,
        },
    },
    location="US",
    deferrable=True,
)
```

`BigQueryInsertJobOperator` is the modern operator (subsumed many older ones). Connection uses Workload Identity Federation or service account.

For partitioned tables: write directly to the partition (`mytable$20260520`).

---

## 4. Azure Synapse / Fabric Warehouse

Provider: `apache-airflow-providers-microsoft-azure`.

Synapse Pipelines + Airflow rarely overlap (Synapse Pipelines IS an orchestrator). The Airflow + Synapse pattern:

- Synapse SQL Pool: `MsSqlOperator` with Synapse connection.
- Synapse Spark: `AzureSynapseRunPipelineOperator` (calls Synapse Pipelines).
- Fabric Warehouse: SQL operators via the Fabric Warehouse SQL endpoint.

For Optum-style Azure shops: Airflow orchestrating Synapse / Fabric is common.

---

## 5. Databricks SQL Warehouse

Provider: `apache-airflow-providers-databricks`.

```python
from airflow.providers.databricks.operators.databricks_sql import DatabricksSqlOperator

query = DatabricksSqlOperator(
    task_id="query",
    databricks_conn_id="databricks_default",
    sql="SELECT count(*) FROM gold.sales WHERE ds='{{ ds }}'",
    sql_endpoint_name="prod_sql_warehouse",
)
```

For SQL-first lakehouse queries: Databricks SQL Warehouse with PrivateLink.

---

## 6. The anti-pattern: transforming in Airflow Python

```python
# WRONG
@task
def transform(records: list) -> list:
    return [{"id": r["id"], "amount": r["amount"] * 1.1} for r in records]
```

10K rows in XCom → blow up metadata DB. For warehouse-targeted ETL: **transform in the warehouse**.

```python
# RIGHT
transform_in_sf = SnowflakeOperator(
    task_id="transform",
    sql="INSERT INTO analytics.priced SELECT id, amount * 1.1 FROM staging.raw",
)
```

Snowflake / BQ / Redshift have unlimited compute relative to your Airflow worker. Push down.

---

## 7. Provider package versioning

For 2.10 + Snowflake: `apache-airflow-providers-snowflake==5.5.1` (or latest). Pin in requirements.txt.

Provider packages have their own version lifecycle independent of Airflow core. Major version bumps may break operator signatures.

---

## 8. Connection management at scale

For 100+ Connection objects across envs: declare them in Terraform / Infrastructure-as-Code:

```hcl
resource "aws_secretsmanager_secret" "snowflake_conn" {
  name = "airflow/connections/snowflake_prod"
}
resource "aws_secretsmanager_secret_version" "snowflake_conn" {
  secret_id = aws_secretsmanager_secret.snowflake_conn.id
  secret_string = jsonencode({
    conn_type = "snowflake"
    host      = "myorg.privatelink.snowflakecomputing.com"
    login     = "svc_airflow"
    extra     = jsonencode({
      account = "myorg-prod"
      warehouse = "ETL_WH"
      role = "AIRFLOW_ETL_ROLE"
      authenticator = "snowflake_jwt"
      private_key_file = "/run/secrets/snowflake.p8"
    })
  })
}
```

Apply Terraform → Connections appear in Airflow (via Secrets Backend). No manual UI clicking.

---

## Sanity check

1. Snowflake key-pair vs OAuth vs username/password — order of preference and why.
2. `RedshiftDataOperator` deferrable mode — what does it free?
3. Why is "transform in Airflow Python" an anti-pattern for warehouse loads?
4. Snowflake PrivateLink — what does the connection host look like?
5. Connection-as-code via Terraform — what's the win?

---

## Sources

- [Snowflake provider](https://airflow.apache.org/docs/apache-airflow-providers-snowflake/stable/)
- [Amazon provider — Redshift operators](https://airflow.apache.org/docs/apache-airflow-providers-amazon/stable/operators/redshift/)
- [Google provider — BigQuery operators](https://airflow.apache.org/docs/apache-airflow-providers-google/stable/operators/cloud/bigquery.html)
- [Databricks provider](https://airflow.apache.org/docs/apache-airflow-providers-databricks/stable/)
- [Microsoft Azure provider](https://airflow.apache.org/docs/apache-airflow-providers-microsoft-azure/stable/)

→ Next: [21 — Databricks integration](21_databricks_integration.md)
