# Quiz — Module 6: PySpark + Spark SQL Performance on Databricks

## Recall

**Q1.** Name the four physical join strategies in Spark and the one-line "when does each fire" rule.

<details><summary>Answer</summary>

- **Broadcast Hash Join (BHJ)** — fires when one side fits under `spark.sql.autoBroadcastJoinThreshold` (10 MB OSS / ~30 MB Databricks AQE-time).
- **Sort-Merge Join (SMJ)** — default for big-big joins; both sides shuffled, sorted, merged.
- **Shuffle Hash Join (SHJ)** — niche; force with `/*+ SHUFFLE_HASH(t) */` when one side is meaningfully smaller per partition than the other but too large to broadcast.
- **Broadcast Nested Loop Join (BNLJ)** — non-equi joins; **almost always a bug**. O(N×M).

AQE can demote a planned SMJ to BHJ at runtime once it observes actual post-shuffle size — this is why even stale stats don't kill you.
</details>

**Q2.** What are the four caching layers on Databricks?

<details><summary>Answer</summary>

1. **`df.cache()` / `df.persist()`** — JVM/Photon executor memory; lazy, lost on cluster restart. Use for iterative algorithms.
2. **Disk Cache (formerly Delta cache)** — auto-managed cache of remote Parquet on worker NVMe SSDs. Default-on with SSD instances. The most useful default cache.
3. **Photon's columnar in-memory cache** — complements disk cache for hot data, off-heap.
4. **DBSQL result cache** (per-warehouse local + cross-warehouse remote) + DBSQL UI cache — exclusive to Databricks SQL.
</details>

**Q3.** What does `spark.sql.adaptive.skewJoin.enabled` actually do, and what are the two thresholds that must both be exceeded for skew to be detected?

<details><summary>Answer</summary>

When enabled (default), AQE detects a partition as skewed when **both**:
- `partition_size > skewedPartitionFactor * median_partition_size` (default factor=5)
- `partition_size > skewedPartitionThresholdInBytes` (default 256 MB)

Skewed partitions are split into smaller subpartitions and replicated against the matching partition on the other side.

**Limitations:**
- Only operates after a shuffle; only on SMJ and SHJ
- Won't help if skew is below 256 MB but still hurting tail latency
- Doesn't apply to stream-stream joins
- Doesn't apply to window function partitionBy skew (use salting for that)
</details>

**Q4.** Why does Photon NOT accelerate Python UDFs, and what's the typical performance penalty?

<details><summary>Answer</summary>

Python UDFs execute in a Python process **outside Photon's address space** (and outside the JVM's). The query engine has to round-trip data between Photon (C++ / off-heap) and the Python interpreter (Python objects), which:
1. Forces a per-row format conversion
2. Disables Photon's vectorized execution for the operator containing the UDF
3. Means the entire query stage falls back to JVM Spark for that operator, with format conversion at the boundary

**Typical penalty:** a simple `lambda x: x.upper()` Python UDF can run **100× slower** than the equivalent `F.upper()` built-in once Photon kicks in. Pandas (Arrow) UDFs are better than plain Python UDFs because of vectorized batch transfer via Arrow, but still cause Photon fallback for the UDF operator.

**The discipline rule:** replace Python UDFs with Spark SQL built-ins whenever possible.
</details>

---

## Apply

**Q5.** A claims fact table is being joined to a 50K-row payer dimension. The query plan shows `SortMergeJoin`. The query takes 12 minutes. What would you change?

<details><summary>Answer</summary>

50K rows is well within broadcast territory. The likely issues:
1. **The optimizer's size estimate is off** — wide row size or stale stats may make 50K rows look bigger than they are.
2. **Broadcast threshold not raised** — even with a hint, the threshold can refuse the broadcast.

**Fix sequence:**
1. **Force the broadcast** with `df.join(broadcast(payer_dim), "payer_id")` or `/*+ BROADCAST(payer_dim) */`.
2. **Raise the threshold** if the hint alone doesn't take effect: `SET spark.sql.autoBroadcastJoinThreshold = 100MB` for the session.
3. **Refresh stats** on the dimension: `ANALYZE TABLE silver.dim_payer COMPUTE STATISTICS FOR ALL COLUMNS`.
4. **Verify in the plan** post-change — Spark UI should show `BroadcastHashJoin` instead of `SortMergeJoin`.
5. **Driver size** — if the broadcast is non-trivial, ensure the driver has 4× the broadcast size in memory.

**Expected outcome:** the 12-minute SMJ becomes a 1–2 minute BHJ (or faster), because the entire shuffle on the fact-table side is eliminated.

**Anti-pattern to avoid:** broadcasting a wide table that's "small in row count but huge in bytes" because of long string columns — that OOMs the driver.
</details>

**Q6.** Write a salting pattern for joining a 100M-row claim_line to a 1M-row provider table where one provider (`pcp_id = '99'`) accounts for 60% of claims.

<details><summary>Answer</summary>

```python
from pyspark.sql import functions as F

NUM_SALTS = 50

# Skewed left (claim_line): assign random salt
claim_salted = (
    claim_line
    .withColumn("salt", (F.rand() * NUM_SALTS).cast("int"))
    .withColumn("pcp_salted", F.concat_ws("-", F.col("pcp_id"), F.col("salt")))
)

# Right (provider): replicate N times so every salt has a match
provider_salted = (
    provider
    .withColumn("salt", F.explode(F.array([F.lit(i) for i in range(NUM_SALTS)])))
    .withColumn("pcp_salted", F.concat_ws("-", F.col("pcp_id"), F.col("salt")))
)

joined = (claim_salted
            .join(provider_salted, "pcp_salted")
            .drop("pcp_salted", "salt"))
```

**Why this works:** the original `pcp_id = '99'` rows are now spread across 50 different salted keys (`99-0`, `99-1`, ..., `99-49`), each going to a different shuffle partition. The provider table is replicated 50× so that every salted key has a matching row. The skew is eliminated at the cost of a 50× explosion of the smaller side (1M → 50M rows, still small enough).

**Tradeoffs:**
- Pick `NUM_SALTS` to balance shuffle reduction against small-side inflation. 50 is a reasonable default; 10 may not be enough for severe skew, 200+ inflates the small side too much.
- Try AQE skew detection first (`spark.sql.adaptive.skewJoin.enabled = true`) before manually salting. AQE handles many cases automatically.
- This pattern is for SMJ/SHJ; doesn't apply to BHJ (no shuffle to skew on).
</details>

---

## Diagnose

**Q7.** A team's Power BI dashboard is timing out at 60 seconds. The query is a 5-table join. The team is on a **Classic** SQL warehouse with Photon enabled. They've added more warehouse cluster size; it didn't help. Walk through the diagnosis.

<details><summary>Answer</summary>

**Hypothesis menu:**

1. **Warehouse type missing Predictive I/O.** Classic warehouse has Photon but **no Predictive I/O and no Intelligent Workload Management**. For analytical queries with selective filters, Predictive I/O is a real win — it's Photon-exclusive but only available on **Pro and Serverless** warehouses.
   - **Fix:** move to Serverless SQL warehouse (recommended default for BI workloads anyway).

2. **Stale statistics on dimension tables.** With CBO making bad join-order decisions, even Photon can't save the plan.
   - **Check:** open the DBSQL Query Profile, look at the plan tree. Are joins reordered by the CBO?
   - **Fix:** `ANALYZE TABLE ... COMPUTE STATISTICS FOR ALL COLUMNS` on the dimensions. Or enable Predictive Optimization (UC managed tables get this automatically).

3. **No Liquid Clustering on filter columns.** The dashboard probably filters on `service_date`, `member_state`, `payer_id` — if the fact table isn't clustered on those, every query scans the whole table.
   - **Fix:** `ALTER TABLE silver.claim_line CLUSTER BY (service_date, payer_id)`. PO will incrementally cluster.

4. **DPP not firing.** Are dimension filters being pushed into the fact-table scan? Sometimes a UDF on the dimension side breaks DPP.
   - **Check:** Spark UI plan; look for `dynamicPruning` annotations.
   - **Fix:** rewrite the dimension predicate without UDFs.

5. **Materialize the dashboard query.** If the query is hot and re-runs frequently, a Materialized View is the cleanest fix.
   - **Cost:** small — MVs run on serverless DLT/Lakeflow with cost model picking incremental vs full.

6. **More warehouse size doesn't help if the bottleneck is per-query**, not concurrency. Adding clusters scales concurrency horizontally; making each cluster bigger only helps if the query is parallelizable. For a single query, **bigger T-shirt size on the cluster** (2X-Small → Small → Medium) is the right lever, not more clusters.

**Likely root cause for this scenario:** Classic warehouse missing Predictive I/O. **Move to Serverless** is the highest-ROI change.
</details>

---

## Defend

**Q8.** A peer says "we should turn on `spark.sql.shuffle.partitions = 800` for all our jobs to be safe." Defend or refute.

<details><summary>Answer</summary>

**Refute, with calibration.**

The peer is *partially right* in spirit: 200 (the OSS default) is too low for many large jobs on modern hardware. But pinning to 800 globally is misguided:

1. **AQE coalesces post-shuffle.** With `spark.sql.adaptive.coalescePartitions.enabled = true` (default-on Databricks), AQE looks at actual map output sizes and merges small partitions. Setting 800 is just the *initial* count — AQE will coalesce down to whatever the advisory size dictates (default 64 MB target). So setting 800 vs 200 vs 4000 mostly doesn't matter for the *post-shuffle* world.

2. **The real lever** for "I want bigger or smaller post-shuffle partitions" is `spark.sql.adaptive.advisoryPartitionSizeInBytes` (default 64 MB), not `shuffle.partitions`.

3. **Auto-Optimized Shuffle** (`spark.databricks.adaptive.autoOptimizeShuffle.enabled = true`) is the Databricks-specific feature that picks the initial number based on data size and executor count — strictly better than a global default. Enable that and stop tuning `shuffle.partitions` manually.

4. **Pinning a high number can hurt small jobs** — for a 100MB job, you don't need 800 initial partitions; you'll spend the time shuffling tiny things.

**Production discipline:**
- Leave `shuffle.partitions` at default (or whatever Databricks LTS picks).
- Let AQE coalesce do the work.
- Tune `advisoryPartitionSizeInBytes` (rare; default is fine for most workloads).
- Enable `autoOptimizeShuffle.enabled` on jobs you've benchmarked it for.

**The 2026 mental model:** AQE makes most pre-Spark-3.0 shuffle-tuning advice obsolete. Stay out of AQE's way; don't hand-tune what the engine corrects automatically.
</details>

**Q9.** A peer says "we should put `cache()` on every DataFrame in our pipeline, just to be safe." Defend or refute.

<details><summary>Answer</summary>

**Refute, decisively.**

`df.cache()` is **not free.** It costs:
1. **Memory** — the cached DataFrame occupies executor memory or local SSD, evicting things that might genuinely benefit from caching.
2. **Materialization** — the first action triggers a full compute and write of the cached representation. If you don't reuse the DataFrame, that's pure waste.
3. **Eviction risk** — under memory pressure, Spark evicts cached partitions. The next read regenerates from source, often **slower** than if you'd never cached because of disk-spill overhead.

**When `df.cache()` is right:**
- **Iterative algorithms** that scan the same DataFrame many times (ML training loops, graph algorithms).
- **DataFrames used by multiple downstream transformations** in a single query (a single `count()` would re-execute upstream lazily).
- **Diagnostic / profiling work** where you want to inspect the same data multiple times in a notebook.

**When `df.cache()` is wrong:**
- **One-shot pipelines** — read, transform, write. The disk cache (auto-managed) handles "I read the same file twice" cases automatically.
- **Wide DataFrames** that consume too much memory.
- **`cache()` immediately followed by a single `count()` and never used again.**

**The disk cache (automatic, free, on by default with SSD instances) handles the "I'm reading the same Parquet file multiple times" case for you.** That's the case 80% of the time. Adding explicit `cache()` calls is usually performance theater that the disk cache already handles better.

**Production discipline:**
- Default to no `cache()`.
- Add it deliberately for iterative or multi-action use cases.
- Verify with the Storage tab in Spark UI that the cache is actually reused.
- Remove caches that don't show measurable benefit.

**The peer's "just to be safe" framing is the tell** — they're treating cache like belt-and-suspenders, but it's a tradeoff with real costs.
</details>
