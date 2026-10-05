# Module 7 — Databricks SQL & DBSQL Warehouses

> **Goal of this module:** know when to use DBSQL warehouses vs Spark clusters, pick the right warehouse type, understand the 2026 caching layers and performance levers (Predictive I/O, IWM, Materialized Views, Streaming Tables), and not get surprised by the Snowflake-vs-Databricks SQL benchmark conversation.

---

## Why DBSQL exists separately from Spark

Databricks SQL warehouses are a **purpose-built compute layer for SQL workloads** — BI dashboards, ad-hoc analyst queries, embedded analytics in apps. They share the same underlying data (Delta in UC) and the same Photon engine, but they're packaged differently from Spark clusters:

- **Always-on Photon** on Pro and Serverless tiers (no decision to make).
- **SQL-only interface** — no notebook, no PySpark, no ML.
- **Connection model is JDBC/ODBC + REST** — Power BI, Tableau, dbt, Hightouch, Airflow connect over standard endpoints.
- **Concurrency-oriented sizing** — clusters scale horizontally for concurrent queries, not vertically for one big query.
- **Result caches and predictive I/O** that don't exist on Spark clusters.

The architect's job: route SQL workloads (BI, analytics, dbt transformations) to DBSQL; route ML, ETL, and complex Python to Spark clusters; let UC make the data the same on both sides.

---

## Warehouse types — three flavors

| Type | Photon | Predictive I/O | Intelligent Workload Management | Cold start | Use |
|---|---|---|---|---|---|
| **Classic** | Yes | No | No | 4–10 min | Legacy / cost-sensitive Pro alternative |
| **Pro** | Yes | Yes | No | 4–10 min | Mid-tier; Photon + Predictive I/O without serverless premium |
| **Serverless** | Yes | Yes | **Yes** | 5–10 sec | **Recommended default** for BI |

Source: [SQL warehouse types — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/compute/sql-warehouse/warehouse-types).

**The 2026 default for any new BI workload is Serverless.** Classic exists only for legacy / very cost-tight scenarios; Pro is a niche middle ground. The cost premium of Serverless ($0.70/DBU vs $0.55 SQL Pro on Azure Premium) is more than offset by Intelligent Workload Management and 5-second cold starts on bursty workloads.

---

## Sizing and concurrency

### T-shirt sizes

Warehouse sizes go from **2X-Small → X-Small → Small → Medium → Large → X-Large → 2X-Large → 3X-Large → 4X-Large.** Each step roughly doubles the cluster size (vCPU + memory) and DBU rate.

**Sizing rule:** pick the smallest size that handles your **slowest acceptable single query**. Bigger size = bigger per-query cluster = each query gets more parallelism. *Concurrency* scales by adding clusters horizontally (auto-scaling), not by going bigger.

### Auto-scaling and Intelligent Workload Management

On Serverless, **IWM auto-scales the warehouse up to a configured max** based on queued queries. Set:
- **Cluster count** — min and max (e.g., 1 minimum, 8 maximum)
- **Auto-stop** — minutes idle before stopping (default 10 minutes)

For a BI dashboard hit by 500 analysts during 9 AM Monday, set max=10; IWM scales out, then scales back during quiet hours. This is one of the things Pro/Classic don't get — you'd manage cluster count manually.

### Concurrency on a single cluster

Each warehouse cluster handles a configurable number of concurrent queries. **Default ~10 per cluster.** Beyond that, queries queue. IWM (serverless only) decides whether to scale clusters or let queries queue based on observed patterns.

---

## Caching layers (DBSQL-specific)

Module 6 covered the four caching layers; the DBSQL-specific ones to remember:

### Disk cache

Same as on Spark clusters — auto-managed cache of remote Parquet on local NVMe SSDs. **On by default** for all warehouse types. Survives across queries within a warehouse session.

### Local query result cache

Per-warehouse cache of query results for **identical queries within the same warehouse session.** A second analyst running the same SQL (same query text, same parameters) gets the cached result back in milliseconds. Configurable per query via `RESULT_CACHE_ENABLED` SQL hint.

### Remote query result cache

**Persists results across warehouse restarts** when the underlying data hasn't changed. Powered by table-version metadata — if the source Delta tables haven't been written to since the cached result was computed, the cache is valid.

### UI caches

The web UI itself caches dashboard queries — separate from SQL warehouse caching. For embedded analytics in Apps or Power BI, this layer doesn't apply; only the warehouse layers do.

[Databricks blog: caching in DBSQL](https://www.databricks.com/blog/understanding-caching-databricks-sql-ui-result-and-disk-caches) is the canonical reference.

---

## Predictive I/O

Photon-exclusive feature on Pro and Serverless. Two modes:

**Predictive I/O for SELECT** — minimizes data read by predicting which files are likely needed and prefetching them; combined with Liquid Clustering and data skipping, lights up selective queries on large fact tables.

**Predictive I/O for UPDATE / DELETE / MERGE** — minimizes file rewrites via deletion vectors. A targeted UPDATE that touches 0.1% of rows touches ~0.1% of bytes (Module 3 covered DV).

**Why this matters for SQL workloads:** the dominant cost in BI is full-table scans hidden behind selective predicates. Predictive I/O turns those into selective scans.

[Photon docs](https://docs.databricks.com/aws/en/compute/photon).

---

## Materialized Views and Streaming Tables

Both run on **serverless Lakeflow Spark Declarative Pipelines under the hood**, billed independently of the warehouse you submit from.

### Materialized Views

```sql
CREATE MATERIALIZED VIEW gold.member_month_mv AS
SELECT 
  member_id,
  date_trunc('month', service_date) AS year_month,
  SUM(paid_amount) AS paid,
  COUNT(claim_line_id) AS claim_count
FROM silver.claim_line
GROUP BY member_id, year_month;

-- Refresh on schedule
ALTER MATERIALIZED VIEW gold.member_month_mv 
  SET SCHEDULE EVERY 1 HOUR;
```

**The 2025 Databricks-internal benchmark** ([MV/ST GA blog](https://www.databricks.com/blog/announcing-the-general-availability-of-materialized-views-and-streaming-tables-databricks-sql)): on a 200B-row workload, **MV refresh was 98% cheaper and 85% faster than full table rebuild**, with ~7× better data freshness at 1/50th cost vs CREATE TABLE AS.

The default refresh strategy uses a cost model to pick incremental vs full. Most refreshes are incremental, materializing only the deltas via Delta CDF.

### Streaming Tables

```sql
CREATE STREAMING TABLE bronze.claims_landing
AS SELECT *, current_timestamp() AS ingestion_ts
FROM STREAM read_files('/Volumes/raw/edi/claims/', format => 'json');
```

Continuously appends new data from a streaming source. Runs serverless under the hood. The SQL-side answer to "I want incremental Bronze ingestion without Lakeflow Python."

### When to materialize

- **Hot dashboards** that get hit hundreds of times per hour — materialize, refresh hourly.
- **Heavy aggregations on large fact tables** that take >10 sec to compute — materialize.
- **Cross-table joins that are stable** (fact + 5 dimensions, run thousands of times) — materialize.

**Don't materialize:**
- Queries that are run rarely (compute-on-demand is cheaper).
- Queries over rapidly-changing data with stale-data tolerance < refresh frequency.
- Queries that take <1 second already (the materialization cost won't pay back).

---

## Statistics and the optimizer

With Predictive Optimization on UC managed tables, ANALYZE runs automatically — collected once during Photon writes, then re-collected as data degrades from UPDATE/DELETE ([PO for Statistics blog](https://www.databricks.com/blog/introducing-predictive-optimization-statistics)). Reported impact: **~22% average speedup** across observed workloads.

Manual `ANALYZE TABLE … COMPUTE STATISTICS FOR COLUMNS …` is still relevant for:
- Non-UC-managed tables (PO doesn't apply)
- Freshly migrated tables before the first write
- Cases where the CBO is making bad join-order decisions (verify via Query Profile)

---

## Production patterns — DBSQL-specific

### Pattern: BI on a payor's claims data

Architecture:
- **Silver tables** in UC — `silver.claim_line`, `silver.dim_member`, `silver.dim_provider`, etc.
- **Gold materialized views** — `gold.member_month_mv`, `gold.utilization_summary_mv`. Refresh hourly.
- **Serverless SQL warehouse** sized Medium with auto-scale up to 5 clusters.
- **Power BI / Tableau** connect via JDBC.

Performance discipline:
- **Liquid Clustering** on Silver tables for the dashboard filter columns (service_date, payer_id).
- **Predictive Optimization** on. PO handles ANALYZE, OPTIMIZE, VACUUM.
- **Photon always on** (default for Serverless).
- **MV refresh schedule** aligned to dashboard SLA — not "every minute" if the SLA is "yesterday's data."

### Pattern: dbt-on-Databricks

dbt-databricks (`dbt-databricks` provider) is the recommended adapter. Pattern:
- dbt models compile to SQL DDL/DML
- Run via dbt Cloud or Airflow against a **Pro or Serverless warehouse** (avoid Classic for transformation workloads — no Predictive I/O)
- Materialization strategy matters: `incremental` for fact tables, `view` for thin lookups, `materialized_view` for hot Gold tables.

### Pattern: embedded analytics in a Databricks App

A Streamlit / React app on Databricks Apps queries DBSQL via the SQL connector:
- **Serverless warehouse** with auto-stop set short (e.g., 5 min) to scale to zero between users
- **Result cache** is your friend — repeat user queries hit the cache and don't pay compute
- **Materialized views** for dashboard widgets that are hit on every page load

---

## Cost economics — when DBSQL wins, when it loses

**Wins:**
- Bursty BI workloads that are quiet 70%+ of the time
- Embedded analytics with sub-100-query/min steady-state
- Use cases where 5-second cold start is acceptable
- Multi-tenant analyst pools that benefit from result caching

**Loses:**
- 24/7 saturated warehouses where classic + Reserved VMs underneath SQL Pro is cheaper
- Workloads that need Photon + non-SQL compute (Spark cluster wins because you're not paying twice)
- Single-user heavy SQL that doesn't benefit from concurrency scaling

**The Snowflake comparison.** [Akincilar's 2025 benchmark](https://medium.com/@nickakincilar/snowflake-is-cheaper-faster-than-databricks-serverless-with-real-data-by-a-lot-dc2fe021838a): 24B-row dataset, 16 test queries. **Databricks Large 636s vs Snowflake XL Gen1 266s — 58% faster, 28% cheaper on Snowflake.** Caveat: SQL-only benchmarks. On ML training, Spark, data engineering with custom Python, Snowflake has no comparable native answer.

**The architect's defensible position:** Databricks SQL is competitive but **not category-leading** on pure SQL price/performance. The value defense is co-location with Spark/ML/AI workloads on the same governed data — you avoid copying data to a separate warehouse. For shops that want best-in-class SQL only, Snowflake is honestly cheaper and faster on the SQL workloads tested.

---

## When NOT to use DBSQL

- **For ETL workloads** — Spark + Lakeflow is more expressive and cheaper.
- **For ML feature engineering** — needs Spark + Python.
- **When 24/7 saturation makes Reserved VMs underneath classic Spark cheaper than $0.70/DBU Serverless** — rare, but exists.
- **For pure ad-hoc on small data** (< 1 GB) — DuckDB on a single VM beats spinning a warehouse.

---

## Sanity check

1. A team's BI dashboard is slow and they're using a Classic warehouse. What's the lowest-effort win, and why?
2. What's the Snowflake-vs-Databricks SQL benchmark answer for your CFO, in two sentences?
3. When does Materialized View refresh cost less than recomputing each query, with rough order-of-magnitude reasoning?
4. The remote query result cache invalidates when … what? Be precise.
5. A peer wants to put a 100K-query/hour analyst pool on a Classic warehouse. Why is that wrong?

---

## Further reading

- [SQL warehouse types — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/compute/sql-warehouse/warehouse-types)
- [Materialized Views & Streaming Tables GA — Databricks blog](https://www.databricks.com/blog/announcing-the-general-availability-of-materialized-views-and-streaming-tables-databricks-sql)
- [Photon docs](https://docs.databricks.com/aws/en/compute/photon)
- [Caching in Databricks SQL](https://www.databricks.com/blog/understanding-caching-databricks-sql-ui-result-and-disk-caches)
- [High-concurrency DBSQL architecture](https://www.databricks.com/blog/architecting-high-concurrency-low-latency-data-warehouse-databricks-scales)
- [Predictive Optimization for Statistics](https://www.databricks.com/blog/introducing-predictive-optimization-statistics)
- [Akincilar — Snowflake vs Databricks Serverless benchmark](https://medium.com/@nickakincilar/snowflake-is-cheaper-faster-than-databricks-serverless-with-real-data-by-a-lot-dc2fe021838a)
