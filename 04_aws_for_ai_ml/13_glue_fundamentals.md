# Module 13 — Glue Fundamentals

> **What this is:** AWS Glue — crawlers, Data Catalog, jobs (Spark + Python shell + Ray), Glue Studio, DataBrew, bookmarks, triggers, workflows.

---

## 1. The core components

**Glue Data Catalog** — see Module 12. Metastore consumed by everything.

**Crawlers** — automated schema-discovery jobs that scan a data source (S3 path, RDS, Aurora, etc.) and create/update Glue Catalog tables. Run on schedule or on-demand. Common pattern: hourly crawler on a partitioned S3 path.

**Glue Jobs** — three runtimes:
- **Spark** (Apache Spark on Glue's managed cluster).
- **Python shell** — single-node Python for small ETL.
- **Ray** — distributed Python via Ray (newer, niche).

**Glue Studio** — visual editor that compiles to PySpark or Scala. Useful for discovery; engineers tend to graduate to handwritten scripts.

**DataBrew** — visual data prep with 300+ transformations, recipes that compile to processing jobs. Targeted at data analysts; the "I want to clean a dataset without writing code" surface.

**Bookmarks** — Glue's incremental-ETL primitive. Tracks processed files / partitions / rows so re-runs skip already-processed data. **The single best feature of Glue for cost discipline.**

**Triggers** — schedule (cron) or event-based (job state changes).

**Workflows** — DAG of jobs + crawlers + triggers. Simpler than Step Functions but limited; usually outgrown.

## 2. DynamicFrame vs DataFrame

Glue introduces a `DynamicFrame` on top of Spark `DataFrame`:

- **`DynamicFrame`** — schema is *per record* (handles inconsistent schemas in semi-structured data), supports `ResolveChoice` for type ambiguity, integrates with Glue Catalog + bookmarks.
- **`DataFrame`** — standard Spark DataFrame; faster for known schemas.

**Practical rule:** start with DynamicFrame for source ingest (raw data has schema drift); convert to DataFrame for transformations once schema is stable; convert back to DynamicFrame for write-out via Glue Catalog if you need bookmarks.

## 3. Schema evolution

- Crawlers detect added columns and partition values.
- Glue 4.0+ writes Iceberg natively, which gives proper schema evolution semantics (rename, drop, reorder).
- For non-Iceberg outputs, schema evolution is by Glue Catalog version, with manual reconciliation.

## 4. Example pipeline (raw to curated)

```python
# Glue 5.0 Spark job
from awsglue.context import GlueContext
from pyspark.context import SparkContext
from awsglue.job import Job

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Read raw with bookmarks
raw = glueContext.create_dynamic_frame.from_catalog(
    database="raw", table_name="card_transactions",
    transformation_ctx="raw_card_transactions"  # enables bookmarks
)

# Standardize
df = raw.toDF().filter("amount > 0").withColumn("event_date", to_date("ts"))

# Write Iceberg
df.writeTo("curated.card_transactions") \
  .using("iceberg") \
  .partitionedBy(days("event_date")) \
  .createOrReplace()

job.commit()
```

## 5. 2024–2026 changes

- **Glue 5.0** GA — Spark 3.5, Python 3.11.
- **Glue Iceberg REST Catalog** (GA 2024).
- **Glue Data Quality** built-in (DQDL — Data Quality Definition Language).
- **Amazon Q in Glue** — natural-language-to-Glue-job generation.

## 6. Pitfalls

- **Crawler discovers a new partition** but the job hasn't seen it → bookmark misses it.
- **DynamicFrame everywhere** — slow vs DataFrame.
- **Glue Studio code drift** — engineers edit the generated script, then Studio overwrites it on next save.
- **Workflows for complex orchestration** — outgrow it; switch to Step Functions.

## 7. Capital One lens

Glue is a core piece of the MLOps spine — feature engineering jobs that feed SageMaker training. Step Functions + Glue + EMR + SageMaker is the pattern (Sr Lead MLE JD).

## 8. Sanity check

1. When would you pick a DynamicFrame over a DataFrame?
2. What does a Glue bookmark track, and why does it matter for cost?
3. Why might a crawler discover a partition that a job then misses?
4. Glue Workflows vs Step Functions — when do you outgrow Workflows?
5. What does Glue 5.0 change vs Glue 4.0?

## 9. Cross-references

- **Module 12** — Glue Catalog + Lake Formation
- **Module 14** — Glue Spark performance deep
- **Module 15** — orchestration alternatives (Step Functions, MWAA)
- **Module 22** — Redshift consuming Glue-cataloged data via Spectrum

## Primary sources

- [`Glue_DeveloperGuide.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/Glue_DeveloperGuide.pdf)
- [`Glue_Best_Practices.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/Glue_Best_Practices.pdf)
- Research report: [`05_glue_etl.md`](../../research_inputs/04_aws_for_ai_ml/05_glue_etl.md)
