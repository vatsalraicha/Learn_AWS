"""Unit test for build_member_month using local Spark + chispa.

Runs in CI without a Databricks cluster.
"""
import pytest
from chispa.dataframe_comparer import assert_df_equality
from pyspark.sql import SparkSession
import pyspark.sql.functions as F

from src.silver.member_month import build_member_month


@pytest.fixture(scope="session")
def spark():
    return (
        SparkSession.builder
        .master("local[2]")
        .appName("test_member_month")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.sql.warehouse.dir", "/tmp/spark-warehouse")
        .getOrCreate()
    )


def test_basic_member_month(spark):
    """Two members, simple eligibility, two months of claims."""
    catalog, schema = "test_catalog", "test_schema"
    spark.sql(f"CREATE DATABASE IF NOT EXISTS {catalog}.{schema}")

    # Fixture: claim_line
    claim_data = [
        ("MBR1", "CLM1", "L1", "2026-01-15", 100.0, 80.0),
        ("MBR1", "CLM2", "L1", "2026-01-20", 50.0, 40.0),
        ("MBR1", "CLM3", "L1", "2026-02-10", 200.0, 150.0),
        ("MBR2", "CLM4", "L1", "2026-01-05", 75.0, 60.0),
    ]
    claim_df = spark.createDataFrame(
        claim_data,
        "member_id string, claim_id string, claim_line_id string, service_date string, billed_amount double, paid_amount double",
    ).withColumn("service_date", F.to_date("service_date"))
    claim_df.write.format("delta").mode("overwrite").saveAsTable(f"{catalog}.{schema}.claim_line")

    # Fixture: eligibility (everyone eligible all of 2026)
    elig_data = [
        ("MBR1", "2026-01-01", "2026-12-31"),
        ("MBR2", "2026-01-01", "2026-12-31"),
    ]
    elig_df = spark.createDataFrame(
        elig_data,
        "member_id string, eff_dt string, term_dt string",
    ).withColumn("eff_dt", F.to_date("eff_dt")).withColumn("term_dt", F.to_date("term_dt"))
    elig_df.write.format("delta").mode("overwrite").saveAsTable(f"{catalog}.{schema}.eligibility")

    # Run
    n = build_member_month(spark, catalog=catalog, schema=schema)
    assert n == 3  # MBR1-2026-01, MBR1-2026-02, MBR2-2026-01

    result = spark.table(f"{catalog}.{schema}.member_month").orderBy("member_id", "year_month")

    # Expected
    expected_data = [
        ("MBR1", "2026-01-01", 120.0, 150.0, 2, 2),
        ("MBR1", "2026-02-01", 150.0, 200.0, 1, 1),
        ("MBR2", "2026-01-01", 60.0, 75.0, 1, 1),
    ]
    expected = spark.createDataFrame(
        expected_data,
        "member_id string, year_month string, paid double, billed double, claim_count bigint, unique_claims bigint",
    ).withColumn("year_month", F.to_timestamp("year_month"))

    assert_df_equality(result, expected, ignore_row_order=True, ignore_nullable=True)
