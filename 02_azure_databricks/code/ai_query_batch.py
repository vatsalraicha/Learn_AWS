# ai_query_batch.py
# Bulk extraction over a Delta table using ai_query / ai_extract / ai_classify.
# Pairs with Module 14 (FMAPI/Serving/Gateway) and Module 15 (Agents/AI Functions).
#
# The 2025 serverless batch inference release lets you run LLM inference over millions
# of rows with a SQL function. The auto-scaling serving fleet handles concurrency.
# Cost rolls up under MODEL_SERVING / BATCH_INFERENCE in system.billing.usage.

# %% [markdown]
# # AI Functions in SQL — the underrated batch-inference unlock
#
# Three patterns shown:
# 1. **`ai_extract`** — structured output via JSON schema (clinical coding from notes)
# 2. **`ai_classify`** — categorization at ETL time (claim triage tier)
# 3. **`ai_mask`** — bulk PHI de-identification

# %% Setup
from pyspark.sql import SparkSession

spark: SparkSession  # provided by Databricks Connect or notebook env


# %% Pattern 1 — Bulk ICD-10/CPT extraction with structured output
def extract_clinical_codes_bulk(catalog: str, schema: str) -> int:
    """
    Run ai_extract over a Silver clinical_notes table to derive ICD-10 / CPT codes.

    Endpoint must be:
    - In a CSP=HIPAA workspace if notes contain PHI
    - Configured with AI Gateway PII redaction (defense-in-depth)
    - Provisioned throughput recommended for production (predictability)
    """
    spark.sql(
        f"""
        INSERT INTO {catalog}.{schema}.clinical_codes_extracted
        SELECT
          note_id,
          encounter_id,
          member_id,
          ai_extract(
            endpoint => 'clinical-extract-haiku',
            text     => note_text,
            schema   => 'STRUCT<
                           icd10_codes: ARRAY<STRUCT<code: STRING, description: STRING>>,
                           cpt_codes:   ARRAY<STRUCT<code: STRING, description: STRING>>,
                           diagnoses:   ARRAY<STRING>,
                           medications: ARRAY<STRUCT<name: STRING, dosage: STRING>>
                         >'
          ) AS extracted,
          current_timestamp() AS extraction_ts
        FROM {catalog}.{schema}.clinical_notes
        WHERE encounter_date >= '2025-01-01'
          AND note_id NOT IN (SELECT note_id FROM {catalog}.{schema}.clinical_codes_extracted)
        """
    )
    n = spark.sql(
        f"SELECT count(*) AS n FROM {catalog}.{schema}.clinical_codes_extracted"
    ).collect()[0]["n"]
    return n


# %% Pattern 2 — Categorization via ai_classify
def classify_claim_triage(catalog: str, schema: str) -> int:
    """
    Categorize inbound claim notes into triage tiers for reviewer queue prioritization.
    """
    spark.sql(
        f"""
        INSERT INTO {catalog}.{schema}.claim_triage_classifications
        SELECT
          claim_id,
          ai_classify(
            endpoint   => 'classify-haiku',
            text       => claim_note,
            categories => ARRAY('routine', 'expedited', 'critical', 'fraudulent')
          ) AS triage_tier,
          current_timestamp() AS classified_ts
        FROM {catalog}.{schema}.claim_notes
        WHERE classified_ts IS NULL
        """
    )
    return spark.sql(
        f"SELECT count(*) AS n FROM {catalog}.{schema}.claim_triage_classifications WHERE classified_ts >= current_date - INTERVAL 1 DAY"
    ).collect()[0]["n"]


# %% Pattern 3 — Bulk PHI de-identification via ai_mask
def deidentify_clinical_notes(catalog: str, schema: str, src_table: str, tgt_table: str) -> int:
    """
    Use ai_mask to remove PHI from clinical free-text before downstream analytics.

    Note: this complements (not replaces) the AHDS FHIR de-identification pipeline.
    Use ai_mask for free-text fields that escape structured de-id (e.g., open-text
    note fields, complaint descriptions).
    """
    spark.sql(
        f"""
        INSERT INTO {catalog}.{schema}.{tgt_table}
        SELECT
          note_id,
          ai_mask(
            endpoint => 'mask-haiku',
            text     => note_text,
            labels   => ARRAY('NAME', 'MRN', 'SSN', 'PHONE', 'EMAIL', 'ADDRESS', 'DOB')
          ) AS deidentified_text,
          current_timestamp() AS deidentified_ts
        FROM {catalog}.{schema}.{src_table}
        WHERE note_id NOT IN (SELECT note_id FROM {catalog}.{schema}.{tgt_table})
        """
    )
    return spark.sql(
        f"SELECT count(*) AS n FROM {catalog}.{schema}.{tgt_table}"
    ).collect()[0]["n"]


# %% Production discipline notes
"""
1. Endpoint configuration matters.
   - For PHI prompts: Provisioned Throughput, AI Gateway PII redaction, FMAPI Llama
     or other HIPAA-eligible model. Don't use scale-to-zero in production.
   - For non-PHI: pay-per-token is cheaper.

2. Idempotency. Use `WHERE note_id NOT IN (SELECT note_id FROM target)` or merge
   patterns so re-runs don't double-charge. Module 5 covers idempotent MERGE.

3. Cost monitoring.
   SELECT sku_name, SUM(usage_quantity * list_price) AS cost_30d
   FROM system.billing.usage u
   JOIN system.billing.list_prices p ON u.sku_name = p.sku_name AND u.cloud = p.cloud
   WHERE sku_name LIKE 'BATCH_INFERENCE%' OR sku_name LIKE 'MODEL_SERVING%'
   GROUP BY sku_name;

4. Inference tables.
   AI Gateway can capture every request/response in an inference table.
   These contain PHI for PHI prompts — tag with phi_class=high in UC and
   protect via ABAC (Module 9). Audit retention follows your compliance pipeline (Module 17).
"""
