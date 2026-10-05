# Module 24 — Athena & Query Federation

> **What this is:** Athena v3 (Trino-based), Iceberg/Hudi/Delta support, federated query connectors, workgroups, performance tuning, Athena for Apache Spark.

---

## 1. Athena v3 engine

Athena's query engine since 2023 is **Trino-based** (formerly Presto). Compatible SQL surface with significant performance improvements over v2.

- **Pricing**: $5 per TB scanned (same as Spectrum).
- **No infrastructure to manage** — fully serverless.
- **Glue Data Catalog** as the metastore.

## 2. Table formats supported

- **Hive-style external tables** (Parquet, ORC, JSON, CSV).
- **Apache Iceberg** — full read + write, including MERGE, time travel, branching.
- **Apache Hudi** — read.
- **Delta Lake** — read.

Iceberg is the most active path — Athena v3 supports the latest Iceberg spec features.

## 3. Federated query

Athena can query data **outside S3** via Lambda-based connectors:

- **RDS / Aurora** (MySQL, Postgres)
- **DynamoDB**
- **Redshift**
- **DocumentDB**
- **MSK / Kafka**
- **OpenSearch**
- **CMDB sources** (Vertica, MS SQL Server, etc.)
- **Snowflake**

Use case: **join data across stores without ETL** — e.g., join an S3 transaction table with a DynamoDB customer profile.

The Lambda connector is a community/AWS-provided package; you deploy it once per source type.

## 4. Workgroups

Workgroups give you:
- **Cost separation** — bill per workgroup tag.
- **Query result location** — each workgroup writes to its own S3 prefix.
- **Result reuse** — queries can reuse prior results (within TTL).
- **Engine version pinning** — pin v2 or v3.
- **Query limits** — max scan limits per workgroup.

## 5. Performance tuning

| Optimization | Impact |
|---|---|
| **Columnar format** (Parquet/ORC vs CSV) | 10-100× cheaper |
| **Partitioning** | Skip data — major reduction in scan |
| **Partition projection** | Avoid Glue catalog 1M partition limit; project partitions from name pattern |
| **File size** (256 MB - 1 GB target) | Fewer files = faster scan |
| **Predicate pushdown** | Filter early via WHERE clause on partition columns |
| **CTAS** to materialize aggregations | Pay scan cost once, reuse |

## 6. Partition projection

Tell Athena how to project partition values from a key pattern, avoiding the need to list partitions in the Glue Catalog. For tables with 1M+ partitions, this is the only viable approach.

```sql
ALTER TABLE my_table SET TBLPROPERTIES (
  'projection.enabled'='true',
  'projection.date.type'='date',
  'projection.date.range'='2020-01-01,NOW',
  'projection.date.format'='yyyy-MM-dd'
);
```

## 7. Athena ACID via Iceberg

INSERT, UPDATE, DELETE, MERGE on Iceberg tables. Time travel via `AS OF VERSION` / `AS OF TIMESTAMP`. The path for warehouse-style operations on lake data.

## 8. CTAS (CREATE TABLE AS SELECT)

Materialize query results as new tables. Pattern: define an Iceberg table; CTAS to populate it with aggregations; downstream queries hit the smaller table.

## 9. Athena for Apache Spark

Notebook-style serverless Spark inside Athena. Useful for ad-hoc Python/Spark workloads without spinning up Glue or EMR.

## 10. 2024-2026 changes

- **Athena v3 (Trino)** is the current engine.
- **Iceberg MERGE + time travel** GA.
- **Federated query** continues expanding source list.
- **Athena for Spark** matured.

## 11. Pitfalls

- **Forgetting partitioning** — full table scans on TB-scale data are expensive.
- **CSV instead of Parquet** — 10× cost.
- **Many small files** — slower than fewer big files.
- **Partition projection on a tiny table** — overengineering.
- **Joining federated sources without filters** — pulls all data through Lambda connector.

## 12. Capital One lens

Athena is the natural lake-query surface for ad-hoc analytical work and exploratory data science. Federated query likely used to join S3 lake data with DynamoDB / RDS without ETL.

## 13. Sanity check

1. What engine does Athena v3 use?
2. When does partition projection beat Glue partition listing?
3. What does the Lambda-based federated query connector do?
4. When would you use CTAS?
5. What's the cost difference between scanning Parquet vs CSV?

## 14. Cross-references

- **Module 12** — Glue Catalog (the metastore)
- **Module 10** — S3 + Iceberg
- **Module 22** — Redshift Spectrum (same scan cost; cluster-attached)
- **Module 23** — Snowflake (cross-engine Iceberg interop)

## Primary sources

- [`Athena_Performance_Tuning.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/Athena_Performance_Tuning.html)
- [`Athena_Federated_Query.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/Athena_Federated_Query.html)
- Research report: [`06c_analytical_vector_graph.md`](../../research_inputs/04_aws_for_ai_ml/06c_analytical_vector_graph.md)
