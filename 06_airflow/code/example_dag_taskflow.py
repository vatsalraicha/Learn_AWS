"""
Production-grade TaskFlow DAG example.

References: Topic 06 modules 02 (concepts), 05 (DAG authoring), 06 (scheduling),
07 (deferrable), 11 (XCom), 12 (data-flow design), 20 (Snowflake).
"""
from datetime import datetime, timedelta

from airflow.decorators import dag, task
from airflow.datasets import Dataset
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook

# ── Datasets (Assets in Airflow 3) ──────────────────────────────────────
dataset_sales_raw = Dataset("s3://myorg-raw/sales/")
dataset_sales_curated = Dataset("snowflake://prod.curated.sales")


@dag(
    dag_id="sales_etl_v2",
    description="Daily sales ETL into Snowflake curated layer",
    start_date=datetime(2026, 1, 1),
    schedule="0 3 * * *",
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "data-eng",
        "retries": 3,
        "retry_delay": timedelta(minutes=5),
        "retry_exponential_backoff": True,
        "max_retry_delay": timedelta(hours=1),
        "execution_timeout": timedelta(hours=2),
    },
    tags=["etl", "snowflake", "sales", "production"],
    doc_md=__doc__,
)
def sales_etl_v2():
    """Daily sales ETL pipeline."""

    # 1. Wait for source data — deferrable to free worker slot
    wait_for_export = S3KeySensor(
        task_id="wait_for_export",
        bucket_name="myorg-raw",
        bucket_key="sales/{{ ds }}/_SUCCESS",
        deferrable=True,
        poke_interval=300,
        timeout=86400,
    )

    @task(retries=3, retry_delay=timedelta(minutes=5))
    def discover_partitions() -> list[str]:
        """Discover partition list for parallel processing."""
        return [f"sales_p{i:03d}" for i in range(10)]

    @task(
        pool="snowflake_etl",      # limit concurrent Snowflake load
        pool_slots=1,
    )
    def load_partition(partition: str) -> dict:
        """Idempotent partition load to staging."""
        hook = SnowflakeHook(snowflake_conn_id="snowflake_prod")
        # MERGE = idempotent; safe to retry
        hook.run(
            f"""
            DELETE FROM staging.{partition} WHERE ds = '{{{{ ds }}}}';
            INSERT INTO staging.{partition}
            SELECT * FROM raw.{partition}_raw
            WHERE ds = '{{{{ ds }}}}';
            """
        )
        rows = hook.get_first(f"SELECT count(*) FROM staging.{partition} WHERE ds='{{{{ ds }}}}'")
        return {"partition": partition, "rows": rows[0] if rows else 0}

    promote_to_curated = SnowflakeOperator(
        task_id="promote_to_curated",
        snowflake_conn_id="snowflake_prod",
        sql="""
            MERGE INTO curated.sales c
            USING (SELECT * FROM staging.sales_p000 UNION ALL ...) s
            ON c.id = s.id
            WHEN MATCHED THEN UPDATE SET ...
            WHEN NOT MATCHED THEN INSERT (...) VALUES (...);
        """,
        outlets=[dataset_sales_curated],   # signal data-aware downstream DAGs
    )

    # Wire the DAG
    partitions = discover_partitions()
    stats = load_partition.expand(partition=partitions)
    wait_for_export >> stats >> promote_to_curated


sales_etl_v2()
