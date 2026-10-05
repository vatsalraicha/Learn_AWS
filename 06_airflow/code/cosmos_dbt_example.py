"""
Astronomer Cosmos + dbt example — the modern data-stack pattern.
References: Topic 06 module 24 (dbt + Airflow).
"""
from datetime import datetime
from pathlib import Path

from airflow.decorators import dag
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor

from cosmos import DbtTaskGroup, ProjectConfig, ProfileConfig, ExecutionConfig, RenderConfig
from cosmos.constants import LoadMode
from cosmos.profiles import SnowflakeUserPasswordProfileMapping


@dag(
    dag_id="dbt_curated_models",
    start_date=datetime(2026, 1, 1),
    schedule="0 4 * * *",          # after upstream raw load
    catchup=False,
    tags=["dbt", "snowflake"],
)
def dbt_curated_models():
    wait_for_raw = S3KeySensor(
        task_id="wait_for_raw",
        bucket_name="myorg-raw",
        bucket_key="sales/{{ ds }}/_SUCCESS",
        deferrable=True,
    )

    transform = DbtTaskGroup(
        group_id="transform",
        project_config=ProjectConfig(
            dbt_project_path=Path("/opt/dbt/myorg"),
            manifest_path=Path("/opt/dbt/myorg/target/manifest.json"),
        ),
        profile_config=ProfileConfig(
            profile_name="myorg",
            target_name="prod",
            profile_mapping=SnowflakeUserPasswordProfileMapping(
                conn_id="snowflake_prod",
                profile_args={"database": "PROD", "schema": "ANALYTICS"},
            ),
        ),
        execution_config=ExecutionConfig(
            execution_mode="kubernetes",        # run each model in its own pod
        ),
        render_config=RenderConfig(
            load_method=LoadMode.DBT_MANIFEST,  # use pre-built manifest (faster parse)
            select=["+tag:daily"],              # only daily-tagged models
        ),
    )

    wait_for_raw >> transform


dbt_curated_models()
