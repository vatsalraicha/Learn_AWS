# merge_scd2.py
# Production MERGE patterns: idempotent upsert + SCD Type 2 with WHEN NOT MATCHED BY SOURCE.
# Pairs with Module 3 (Delta Lake) and Module 5 (Spark practitioner discipline).
#
# Run via Databricks Connect or as a notebook attached to a cluster.
# Requires: DBR 14+ for WHEN NOT MATCHED BY SOURCE; delta.enableDeletionVectors recommended.

# %% [markdown]
# # MERGE patterns — production discipline
#
# This module shows three patterns:
# 1. Idempotent upsert with `row_hash` change detection
# 2. SCD Type 2 with `WHEN NOT MATCHED BY SOURCE` for closure
# 3. Cancel-and-replace (HL7v2 / X12 corrections)

# %% Setup
from delta.tables import DeltaTable
from pyspark.sql import SparkSession, DataFrame
import pyspark.sql.functions as F

# Spark session is provided by Databricks Connect or notebook environment
# spark: SparkSession is in scope


# %% Pattern 1 — Idempotent upsert with row_hash
def upsert_claim_line(spark: SparkSession, updates_df: DataFrame, target_table: str) -> None:
    """
    Idempotent MERGE: re-running with the same source produces zero updates after first.

    The `row_hash` column on the source must be computed upstream (see compute_row_hash below).
    With delta.enableDeletionVectors=true, this is 10-100× faster than pre-DV MERGE.
    """
    target = DeltaTable.forName(spark, target_table)

    (
        target.alias("t")
        .merge(
            updates_df.alias("s"),
            "t.claim_id = s.claim_id AND t.claim_line_id = s.claim_line_id",
        )
        .whenMatchedUpdate(
            # Only update if the row actually changed — true idempotency
            condition="s.row_hash <> t.row_hash",
            set={
                "billed_amount": "s.billed_amount",
                "paid_amount": "s.paid_amount",
                "status": "s.status",
                "adjustment_code": "s.adjustment_code",
                "row_hash": "s.row_hash",
                "ingestion_ts": "current_timestamp()",
            },
        )
        .whenNotMatchedInsert(
            values={
                "claim_id": "s.claim_id",
                "claim_line_id": "s.claim_line_id",
                "billed_amount": "s.billed_amount",
                "paid_amount": "s.paid_amount",
                "status": "s.status",
                "adjustment_code": "s.adjustment_code",
                "row_hash": "s.row_hash",
                "ingestion_ts": "current_timestamp()",
            }
        )
        .execute()
    )


def compute_row_hash(df: DataFrame, business_columns: list[str]) -> DataFrame:
    """
    Compute a SHA-256 row_hash over the business attributes.
    Use this to drive idempotent MERGE: only update when row_hash actually changed.
    """
    return df.withColumn(
        "row_hash",
        F.sha2(F.concat_ws("|", *[F.col(c).cast("string") for c in business_columns]), 256),
    )


# %% Pattern 2 — SCD Type 2 with closure via WHEN NOT MATCHED BY SOURCE
def merge_scd2_member(spark: SparkSession, member_updates: DataFrame, target_table: str) -> None:
    """
    SCD Type 2 with full closure logic.

    - WHEN MATCHED + row_hash changed → close the existing 'current' row
    - WHEN NOT MATCHED → insert a new 'current' row
    - WHEN NOT MATCHED BY SOURCE (current rows in target with no source match)
      → close them out (member terminated / no longer in feed)

    The follow-up insert (new 'current' rows for changed members) is a separate write.
    """
    target = DeltaTable.forName(spark, target_table)

    (
        target.alias("t")
        .merge(
            member_updates.alias("s"),
            "t.member_id = s.member_id AND t.is_current = true",
        )
        # Close out members whose attributes changed
        .whenMatchedUpdate(
            condition="s.row_hash <> t.row_hash",
            set={
                "is_current": "false",
                "valid_to": "s.effective_date",
                "row_hash": "t.row_hash",  # preserve old hash on closed row
            },
        )
        # New members never seen before
        .whenNotMatchedInsert(
            values={
                "member_sk": "uuid()",
                "member_id": "s.member_id",
                "is_current": "true",
                "valid_from": "s.effective_date",
                "valid_to": "lit('9999-12-31')",
                "row_hash": "s.row_hash",
                "first_name_redacted": "s.first_name_redacted",
                "last_name_redacted": "s.last_name_redacted",
                "dob_year": "s.dob_year",
                "gender": "s.gender",
                "state": "s.state",
                "plan_id": "s.plan_id",
                "ingestion_ts": "current_timestamp()",
            }
        )
        # Members no longer in source feed (termed) — close them
        .whenNotMatchedBySourceUpdate(
            condition="t.is_current = true",
            set={
                "is_current": "false",
                "valid_to": "current_date()",
            },
        )
        .execute()
    )

    # Step 2: insert new "current" rows for members that had attribute changes.
    # MERGE's whenMatchedUpdate can only modify; we must INSERT the new active version separately.
    new_currents = (
        member_updates.alias("s")
        .join(
            spark.table(target_table).alias("t"),
            on=["member_id"],
        )
        .where("s.row_hash <> t.row_hash AND t.is_current = false")
        .select(
            F.expr("uuid()").alias("member_sk"),
            F.col("s.member_id"),
            F.lit(True).alias("is_current"),
            F.col("s.effective_date").alias("valid_from"),
            F.lit("9999-12-31").alias("valid_to"),
            F.col("s.row_hash"),
            F.col("s.first_name_redacted"),
            F.col("s.last_name_redacted"),
            F.col("s.dob_year"),
            F.col("s.gender"),
            F.col("s.state"),
            F.col("s.plan_id"),
            F.current_timestamp().alias("ingestion_ts"),
        )
    )

    new_currents.write.format("delta").mode("append").saveAsTable(target_table)


# %% Pattern 3 — Cancel-and-replace (HL7v2 / X12 corrections)
def cancel_and_replace_message(spark: SparkSession, corrections: DataFrame, target_table: str) -> None:
    """
    Healthcare correction pattern: a new message supersedes a prior message.
    - Mark the original as canceled (don't delete; preserve history)
    - Append the corrected message as a new row

    With Deletion Vectors, this is cheap. Pre-DV every cancel rewrote the file.
    """
    target = DeltaTable.forName(spark, target_table)

    # Step 1: mark originals as canceled
    (
        target.alias("t")
        .merge(
            corrections.alias("c"),
            "t.message_control_id = c.original_message_control_id",
        )
        .whenMatchedUpdate(
            set={
                "is_canceled": "true",
                "canceled_by_msg_id": "c.message_control_id",
                "canceled_ts": "current_timestamp()",
            }
        )
        .execute()
    )

    # Step 2: append the corrected messages
    (
        corrections.write.format("delta")
        .mode("append")
        .saveAsTable(target_table)
    )


# %% Sanity-check usage
if __name__ == "__main__":
    spark = SparkSession.builder.appName("merge_scd2_demo").getOrCreate()

    # Build a small fixture DataFrame (replace with real data in production)
    sample = spark.createDataFrame(
        [
            ("CLM001", "1", 100.0, 80.0, "PAID", "00"),
            ("CLM001", "2", 50.0, 40.0, "PAID", "00"),
            ("CLM002", "1", 200.0, 150.0, "DENIED", "10"),
        ],
        schema="claim_id string, claim_line_id string, billed_amount double, paid_amount double, status string, adjustment_code string",
    )
    sample_with_hash = compute_row_hash(
        sample,
        business_columns=["billed_amount", "paid_amount", "status", "adjustment_code"],
    )
    sample_with_hash.show()
