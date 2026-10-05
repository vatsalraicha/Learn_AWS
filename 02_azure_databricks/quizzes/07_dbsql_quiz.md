# Quiz — Module 7: Databricks SQL & DBSQL Warehouses

## Recall

**Q1.** What are the three DBSQL warehouse types and what's the key feature gap between them?

<details><summary>Answer</summary>

- **Classic** — Photon, no Predictive I/O, no Intelligent Workload Management. Cold start 4–10 min.
- **Pro** — Photon + Predictive I/O. No IWM. Cold start 4–10 min.
- **Serverless** — Photon + Predictive I/O + IWM. Cold start 5–10 sec. **Recommended default for BI.**

The 2026 picture: Classic exists only for legacy / cost-tight; Pro is niche middle; Serverless is the default. The $0.70/DBU Serverless premium is more than offset by IWM and 5-sec cold starts on bursty workloads.
</details>

**Q2.** What does Predictive I/O do, and which warehouse types have it?

<details><summary>Answer</summary>

Photon-exclusive feature, available on **Pro and Serverless** (not Classic).

Two modes:
- **Predictive I/O for SELECT** — minimizes data read by predicting which files are likely needed and prefetching them. Combined with Liquid Clustering and data skipping, lights up selective queries on large fact tables.
- **Predictive I/O for UPDATE/DELETE/MERGE** — minimizes file rewrites via deletion vectors. A targeted UPDATE that touches 0.1% of rows touches ~0.1% of bytes.

Why it matters: the dominant cost in BI is full-table scans hidden behind selective predicates. Predictive I/O turns those into selective scans.
</details>

**Q3.** What's the difference between **local query result cache** and **remote query result cache**?

<details><summary>Answer</summary>

Both are DBSQL-specific (not on Spark clusters):

- **Local query result cache** — per-warehouse, caches results for identical queries within the same warehouse session. Second analyst running the same SQL (same text, same params) gets a cached result in milliseconds.
- **Remote query result cache** — persists results **across warehouse restarts** when the underlying data hasn't changed. Powered by table-version metadata: if source Delta tables haven't been written to since the cached result was computed, the cache is valid.

Both are above the disk cache (auto-managed Parquet cache on local NVMe SSDs).

The remote cache invalidates when **any source table version changes** — even appends. So for a streaming Bronze table, the cache is constantly invalidated.
</details>

---

## Apply

**Q4.** Write a CREATE MATERIALIZED VIEW for a hot dashboard query that aggregates `silver.claim_line` to member-month grain, refreshing hourly.

<details><summary>Answer</summary>

```sql
CREATE MATERIALIZED VIEW gold.member_month_mv
AS
SELECT 
  member_id,
  date_trunc('month', service_date) AS year_month,
  SUM(paid_amount) AS paid,
  SUM(billed_amount) AS billed,
  COUNT(claim_line_id) AS claim_count,
  COUNT(DISTINCT claim_id) AS unique_claims
FROM silver.claim_line
WHERE is_void = FALSE  -- exclude voided claims
GROUP BY member_id, date_trunc('month', service_date);

ALTER MATERIALIZED VIEW gold.member_month_mv 
  SET SCHEDULE EVERY 1 HOUR;

-- Optional: cluster the MV for downstream filter patterns
ALTER MATERIALIZED VIEW gold.member_month_mv 
  CLUSTER BY (member_id, year_month);
```

The default refresh strategy uses a cost model to pick **incremental vs full**. Most refreshes will be incremental via Delta CDF on the source. The 2025 Databricks-internal benchmark on a 200B-row workload showed **98% cheaper, 85% faster** than full table rebuild for this pattern.

For a Power BI dashboard hitting this hourly, the architect's full pattern:
- Silver tables Liquid Clustered on filter columns
- Gold MV refreshed hourly
- Serverless SQL warehouse with IWM
- Power BI Direct Query against the MV — first query computes; subsequent within the hour hit the result cache
</details>

---

## Diagnose

**Q5.** A team has a 50K-row dimension table joined to a 10B-row fact table. Their dbt model takes 30 minutes nightly on a **Classic** warehouse. The data engineer increased the warehouse size from Medium to Large; runtime dropped only 5%. What's wrong?

<details><summary>Answer</summary>

**Diagnosis layers:**

1. **Classic warehouse missing Predictive I/O.** This is likely the biggest issue. Predictive I/O on Pro/Serverless prefetches selectively-needed files; without it, every query scans the whole fact table. **Move to Serverless** is probably the highest-ROI single change.

2. **Increasing warehouse size scales per-query parallelism, not query plan.** Bigger T-shirt = more vCPU per cluster, but if the query plan is fundamentally inefficient (full scans, missing data skipping), bigger compute just does the inefficient thing faster. The 5% improvement reflects that — modest scaling helps a little but doesn't fix the plan.

3. **Liquid Clustering on the fact table** — if the fact table isn't clustered on the join key or filter columns, every query is a full scan. `ALTER TABLE … CLUSTER BY (...)` would help.

4. **Stats stale** — for the CBO to pick the right join strategy, the dimension table needs accurate statistics. `ANALYZE TABLE silver.dim_payer COMPUTE STATISTICS FOR ALL COLUMNS` if the table is non-UC-managed (UC managed tables get this from PO automatically).

5. **DPP not firing** — Dynamic Partition Pruning needs the dimension filter to be deterministic and not wrapped in UDFs. If the dbt model has a UDF in the dimension `WHERE`, DPP silently fails.

6. **dbt materialization strategy** — if the model is `view`, every dashboard hit re-computes the join. Consider `materialized_view` (or dbt's `materialized_view` materialization) so the join runs once on schedule, not per-query.

**Likely root cause:** Classic warehouse + missing Predictive I/O + missing Liquid Clustering. Move to Serverless and add Liquid Clustering. Expect 5–10× speedup, not 5%.
</details>

---

## Defend

**Q6.** A peer says "we should put all our analyst SQL on a Pro warehouse to save money — Serverless is too expensive." Defend or refute.

<details><summary>Answer</summary>

**Calibrate — partially right, mostly wrong.**

Where the peer is right:
- **At sustained 70%+ utilization**, Pro at $0.55/DBU + classic VM cost can come out ahead of Serverless at $0.70/DBU. The math depends on workload utilization shape.
- For a **single dedicated analyst team** with predictable hours, Pro is reasonable.

Where the peer is wrong (which is most cases):
- **Bursty BI workloads** are common in healthcare — analysts come in 9 AM Monday, peak load for 3 hours, then quiet for 21 hours. Serverless scales to zero in minutes; Pro pays for the cluster across the quiet period.
- **5-second cold start vs 4–10 minutes** matters when an analyst opens a dashboard. Pro requires keeping the warehouse warm; that idle cost adds up.
- **No IWM on Pro** — concurrency scaling has to be managed manually. For a 50-analyst pool, that's operational overhead the peer is signing up for.
- **Result caches on Serverless are the same** — both Pro and Serverless have local + remote query result cache, so the caching argument is a wash.

**The honest framing for the CFO:**
- For **24/7 high-utilization shared warehouses** (rare in healthcare BI): Pro can be cheaper.
- For **bursty analyst pools** (common): Serverless wins on TCO once you account for cold-start productivity loss + IWM operational savings.
- For **embedded analytics in apps**: Serverless wins because of scale-to-zero between user sessions.

**Production discipline:** measure, don't assume. Pull `system.billing.usage` for the existing Pro warehouse, model the equivalent Serverless cost, factor in IWM auto-scaling savings during off-peak. The answer is workload-shape-dependent. Module 16 has the math.
</details>

**Q7.** A peer says "we should materialize every Gold table as a Materialized View." Defend or refute.

<details><summary>Answer</summary>

**Refute, with calibration.**

Materialized Views are excellent for hot dashboard queries — the 2025 benchmark showed 98% cheaper / 85% faster than CTAS on a 200B-row workload. But "materialize everything" is wrong because:

1. **MV refresh has cost.** Even incremental refresh (the default) runs serverless DLT/Lakeflow under the hood and bills DBUs. For an MV that's queried twice a week, the refresh cost dwarfs compute-on-demand.

2. **MV refresh frequency vs query frequency tradeoff.** If you refresh every minute and query once an hour, you're paying 60× more for refresh than necessary. Match the refresh schedule to the SLA.

3. **Some queries don't materialize well.** Highly parameterized queries (different filter every time) don't benefit from MV — each unique parameter combo requires a new materialization.

4. **MV staleness vs source data changes.** For rapidly-changing source data, MV refresh can lag; users see stale results between refreshes.

5. **Streaming Tables are often the better answer** for incremental Gold — `CREATE STREAMING TABLE` continuously appends from a streaming source. Use ST for "always up to date Gold," MV for "scheduled aggregates with stale-data tolerance."

**The right discipline:**
- **Measure query frequency** from `system.access.audit` and `system.query.history` (system tables). Materialize the **top 20% of queries that consume 80% of compute.**
- **Match refresh frequency to SLA.** Hourly dashboards = hourly refresh. Daily report = daily refresh.
- **Use Streaming Tables** for incremental ingestion patterns where you want "Gold mirrors Bronze + transformations" with sub-minute lag.
- **Use Views (not materialized)** for thin lookups or rarely-queried derived tables — the compute-on-demand cost is nothing compared to MV refresh.

**Production rule of thumb:** "When in doubt, view; when in dashboard, MV; when in stream, ST."
</details>
