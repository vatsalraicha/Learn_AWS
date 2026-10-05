# Module 14 — Glue Spark Deep

> **What this is:** Glue Spark architecture, worker types, autoscaling, Glue 3.0 vs 4.0 vs 5.0, performance tuning. The depth a Sr Lead needs to optimize a slow Glue job.

---

## 1. Worker types (2026)

| Worker | vCPU | Memory | Use case |
|---|---|---|---|
| **G.025X** | 2 | 4 GB | Streaming (small) |
| **G.1X** | 4 | 16 GB | Default ETL |
| **G.2X** | 8 | 32 GB | Memory-hungry ETL |
| **G.4X** | 16 | 64 GB | Large joins, wide DataFrames |
| **G.8X** | 32 | 128 GB | Very large memory-pressure workloads |
| **Z.2X** | 8 | 64 GB | Ray (distributed Python) |

A **DPU** (Data Processing Unit) = 4 vCPU + 16 GB ≈ a G.1X worker. Pricing is per-DPU-second.

## 2. Autoscaling

Glue autoscales Spark executors based on Spark task scheduler signals. The autoscaling is *additive only by default* — once scaled up, Glue tends to hold workers. Enable **`--enable-auto-scaling true`** and pair with **`--enable-job-insights true`** for visibility.

## 3. Glue 3.0 vs 4.0 vs 5.0

| | Spark | Python | Highlights |
|---|---|---|---|
| **Glue 3.0** | 3.1 | 3.7 | Photon-equivalent Glue runtime |
| **Glue 4.0** | 3.3 | 3.10 | Native Iceberg/Hudi/Delta, Adaptive Query Execution defaults, ~30% faster than 3.0 |
| **Glue 5.0** | 3.5 | 3.11 | Iceberg REST catalog, improved auto-tune, Arrow-based shuffle |

**Pin Glue version in PR templates.** Behavior differences in Iceberg writes, AQE behavior, and Catalog interactions across versions are real.

## 4. Glue Streaming

Spark Structured Streaming on Glue with windowing, watermarking, exactly-once. Sources: Kinesis, MSK, Kafka. Sinks: S3 (Iceberg), Redshift, OpenSearch.

Worker type **G.025X** is purpose-built for streaming (low memory, fan-out).

## 5. Pushdown predicates

`pushdownPredicate` in `create_dynamic_frame.from_catalog` — Glue translates the filter into a partition predicate that filters Glue Catalog partitions *before* Spark sees them. **Critical for large partitioned tables** — without it, Glue scans every partition.

```python
glueContext.create_dynamic_frame.from_catalog(
    database="raw", table_name="txns",
    push_down_predicate="dt >= '2026-05-01' AND dt < '2026-05-15'"
)
```

## 6. Partitioning rules

- Partition keys should be **low-cardinality** (year/month/day, region) and **frequently filtered on**.
- Avoid partitioning by high-cardinality fields (user_id) — too many tiny files.
- Aim for **~256 MB - 1 GB** per output file.

## 7. Performance tuning checklist

1. **Enable Job Insights** (`--enable-job-insights true`) for Spark UI access.
2. **Push down predicates** via `push_down_predicate`.
3. **Watch the Spark UI** for skew (long tail tasks).
4. **Increase parallelism** with `spark.sql.shuffle.partitions` (default 200; bump to 800-2000 for big jobs).
5. **Coalesce output** before write to avoid small files: `df.coalesce(N)` with N = total_size / 512MB.
6. **Use DataFrame over DynamicFrame** for known-schema transformations.
7. **Flex execution** (Glue 4.0+) — runs on spare capacity at 35% lower cost, with longer latency. Good for non-urgent batches.

## 8. Flex execution

`--execution-class FLEX` — Glue tries to run on idle capacity; takes longer to start but cheaper. Standard runs immediately at full price.

## 9. Pitfalls

- **Forgetting `push_down_predicate`** on partitioned tables → full scan.
- **Tiny output files** → query slowness downstream.
- **Skewed joins** → one task takes 90% of the job's time.
- **DynamicFrame for transformations** that don't need it → 2-3x slowdown.
- **G.1X workers for memory-pressured jobs** → executor OOMs.
- **Bookmark not configured** on incremental jobs → re-process everything.

## 10. Capital One lens

Feature engineering jobs run as Glue Spark with **Flex execution for non-urgent batches**, full price for SLA-bound jobs. Pinned Glue version per PR. Iceberg writes via Glue 4.0/5.0 with the Iceberg REST catalog.

## 11. Sanity check

1. What's a DPU and how does it map to worker types?
2. How does `push_down_predicate` change query performance?
3. When does Flex execution pay off vs standard?
4. How do you tune `spark.sql.shuffle.partitions` for a 10 TB join?
5. Why is partitioning by user_id usually a mistake?

## 12. Cross-references

- **Module 13** — Glue fundamentals (prerequisite)
- **Module 12** — Glue Catalog + Iceberg
- **Module 22** — Redshift Spectrum consumes Glue-managed Iceberg
- **Module 35** — SageMaker Processing Jobs as an alternative for ML preprocessing

## Primary sources

- [`Glue_DeveloperGuide.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/Glue_DeveloperGuide.pdf)
- Research report: [`05_glue_etl.md`](../../research_inputs/04_aws_for_ai_ml/05_glue_etl.md)
