# Quiz 04 — Troubleshooting & Tuning

> 14 questions covering Domain 4 (10% — ~5 questions on the real exam, scaled to 14 for practice).
> Topics: AQE configs (the config-key naming trap), broadcast join thresholds (planner vs runtime), partition tuning (`repartition` vs `coalesce` vs `sortWithinPartitions`), cache vs persist & storage levels, predicate pushdown, partition pruning, bucketing, skew handling (salting, AQE skew join), executor/driver logs.

---

## Recall

1. What is the EXACT config key to enable AQE in Spark 3.5?
2. What is the default value of `spark.sql.autoBroadcastJoinThreshold`?
3. What is the default storage level for `DataFrame.cache()`?
4. Which storage level avoids JVM heap pressure by writing serialized bytes to disk only?

## Apply

5. You have 1B rows skewed on `customer_id` joining a 5GB dim table on the same key. Write the two-config combo that enables AQE skew handling.
6. Write the config to lower the broadcast-join threshold to 50MB.
7. You want to reduce a DataFrame from 500 to 50 partitions before writing. Which method, and why?
8. You want to GROW partitions from 50 to 500 before a wide aggregation. Which method, and why?
9. Persist a DataFrame to memory with serialized bytes (Kryo-compatible), spilling to disk only if memory pressure occurs.
10. A user calls `df.cache()` and then `df.write.parquet(...)` immediately. Nothing else uses `df` later. Was caching helpful?

## Diagnose

11. A colleague writes `spark.adaptive.enabled=true` in their config and reports "AQE doesn't seem to do anything." Diagnosis?
12. A 200-task stage shows one task running 25 minutes while 199 finish in 30 seconds each. AQE is enabled. What other config might still be off?
13. A job that worked last quarter now OOMs at the same data size. Spark UI shows the Storage tab listing 80GB cached across 12 DataFrames. Diagnose and fix.

## Defend

14. Defend or refute: "Always cache a DataFrame that you reference more than once."

---

## Answers

1. **`spark.sql.adaptive.enabled`** (default `true` in Spark 3.5).
    **HIGH-VALUE TRAP:** common wrong answers include `spark.adaptive.enabled` (missing `sql`), `spark.sql.aqe.enabled` (wrong name), `spark.adaptive.aqe.enabled` (wrong namespace). The correct prefix is **`spark.sql.adaptive.*`** for every AQE config.

2. **10MB** (`10485760` bytes). Below this threshold at planning time, Spark auto-promotes a join to broadcast-hash. AQE has a SEPARATE runtime threshold at 30MB: `spark.sql.adaptive.autoBroadcastJoinThreshold`. The two are NOT the same key.

3. **`MEMORY_AND_DISK`.** Spills to local disk if memory fills up. **Trap:** the default for RDD `.cache()` is `MEMORY_ONLY` — different! DataFrame and RDD defaults diverge.

4. **`DISK_ONLY`.** Doesn't use JVM heap, fully serialized to local disk. Slowest read of all levels but zero heap pressure. (`MEMORY_ONLY_SER` is in-heap but serialized — different.)

5. ```python
    spark.conf.set("spark.sql.adaptive.enabled", "true")
    spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
    ```
    Both required: AQE itself + the skew-join sub-feature. With both on, Spark detects skewed partitions at runtime (typically 5x median + above a size threshold) and splits them into sub-partitions automatically.

6. ```python
    spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "50MB")
    # Or in bytes: 52428800
    # Disable broadcast entirely: -1
    ```

7. **`coalesce(50)`.** Narrow transformation, no shuffle. Combines existing partitions on the same executor. Cheap, but the result is **not balanced** — bigger partitions stay bigger.

8. **`repartition(500)`.** Wide transformation, full shuffle, round-robin distribution, balanced output. `coalesce` CANNOT increase partition count — calling `coalesce(500)` on a 50-partition DF returns 50 partitions (a no-op for growth).

9. ```python
    from pyspark import StorageLevel
    df.persist(StorageLevel.MEMORY_AND_DISK_SER)
    ```
    Serialized in-memory storage uses less heap (smaller objects) but costs CPU on read for deserialization. Good when memory is tight and CPU has headroom.

10. **No.** `cache()` is a transformation — it marks the DF for caching, but materialization happens on the first action. The `.write` IS the first action. Spark would write directly without populating cache for any second use that never comes. Net: pure overhead. Use `cache()` only when the DF will be used by 2+ actions.

11. **Wrong config key.** It's `spark.sql.adaptive.enabled`, not `spark.adaptive.enabled`. The misspelled key is silently accepted (Spark doesn't validate arbitrary config names), so the setting just has no effect. **This exact typo appears on the exam.**

12. **`spark.sql.adaptive.skewJoin.enabled` might be off.** AQE has multiple sub-features each gated independently:
    - `spark.sql.adaptive.coalescePartitions.enabled` (default true)
    - `spark.sql.adaptive.skewJoin.enabled` (default true in 3.5, but check)
    - `spark.sql.adaptive.localShuffleReader.enabled` (default true)
    If skew-join is disabled while AQE main is enabled, you get coalescing benefits but no skew remediation. Also check the skew-detection thresholds: `spark.sql.adaptive.skewJoin.skewedPartitionFactor` (default 5x median) and `spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes` (default 256MB).

13. **Stale cached DataFrames.** Someone is calling `.cache()` aggressively but never `.unpersist()`. Each cached DataFrame holds memory across the application lifetime. Fix:
    - Audit with `spark.catalog.clearCache()` (drops ALL cached data) or per-DF `df.unpersist()`.
    - Move to `MEMORY_AND_DISK_SER` if data must stay cached but heap is the issue.
    - Re-validate which DFs are actually re-used vs cached defensively.

14. **Refute as stated — it's a heuristic, not a rule.** Cache only when:
    - The DataFrame will be used by 2+ ACTIONS (not 2+ transformations — transformations re-stack the plan; only actions trigger work).
    - The recomputation cost > the cache-and-evict cost (e.g., expensive joins, heavy UDFs, expensive reads).
    - The DF fits in available memory + disk budget.
    Otherwise caching is overhead: memory pressure, eviction churn, possible spill, GC. For DFs used once, NEVER cache. For DFs used twice with a cheap-read source (Parquet on local SSD), often skip caching — re-read may be faster than cache management.
