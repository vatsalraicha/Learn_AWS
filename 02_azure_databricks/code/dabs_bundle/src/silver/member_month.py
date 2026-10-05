"""Build the silver.member_month aggregate from claim_line + eligibility.

Pure function — testable with chispa + local Spark, deployed via DABs.
Pairs with Module 4 (Notebooks/Workflows) and Module 5 (Spark practitioner).
"""
from __future__ import annotations

from pyspark.sql import SparkSession, DataFrame
import pyspark.sql.functions as F


def build_member_month(spark: SparkSession, catalog: str, schema: str) -> int:
    """Build silver.member_month from claim_line and eligibility. Returns row count."""
    claims = spark.table(f"{catalog}.{schema}.claim_line")
    eligibility = spark.table(f"{catalog}.{schema}.eligibility")

    member_month = (
        claims.alias("c")
        .join(
            eligibility.alias("e"),
            (F.col("c.member_id") == F.col("e.member_id"))
            & (F.col("c.service_date").between(F.col("e.eff_dt"), F.col("e.term_dt"))),
            "inner",
        )
        .groupBy(
            "c.member_id",
            F.date_trunc("month", F.col("c.service_date")).alias("year_month"),
        )
        .agg(
            F.sum("c.paid_amount").alias("paid"),
            F.sum("c.billed_amount").alias("billed"),
            F.count("c.claim_line_id").alias("claim_count"),
            F.countDistinct("c.claim_id").alias("unique_claims"),
        )
    )

    target = f"{catalog}.{schema}.member_month"
    member_month.write.format("delta").mode("overwrite").saveAsTable(target)
    return member_month.count()
