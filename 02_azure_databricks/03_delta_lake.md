# Module 3 — Delta Lake Fundamentals + 2025-2026 Reality

> **Goal of this module:** internalize the Delta Lake mental model an architect needs — how the transaction log works, what data skipping costs and gives you, when Liquid Clustering replaces Z-Order, what Predictive Optimization auto-decides, why deletion vectors changed the MERGE economics, and which schema-evolution moves are free vs which require rewrites. This module is the storage-layer companion to Module 6 (PySpark/SQL performance).

---

## Why this exists

Before Delta Lake, "data on object storage" meant a pile of Parquet files in S3 or ADLS, with metadata maintained by a separate Hive metastore. The arrangement worked for read-only analytics but broke down for any workload that needed the things warehouses gave you — atomic updates, concurrent writers, transactional schema changes, time travel, lineage of writes. The "data swamp" critique landed on this gap: lake storage was cheap and open but uncoordinated.

Delta Lake (originated at Databricks, donated to the Linux Foundation in 2019, [delta.io](https://delta.io/)) is the answer that won at Databricks: a transaction log layered on top of Parquet that gives you ACID, schema enforcement, time travel, statistics-based pruning, and a clean concurrency model — without giving up the open file format underneath. Apache Iceberg (Netflix-originated) and Apache Hudi (Uber-originated) are the other open answers. The 2024 Tabular acquisition brought Iceberg's creators to Databricks, and the 2026 picture is "pick Delta or Iceberg in Unity Catalog and largely it doesn't matter for analytics" (see Module 11).

The architect-level mental model is one sentence: **a Delta table is a directory of Parquet files plus a `_delta_log/` directory whose JSON commits are the only authoritative answer to "what is this table?"** Everything in this module is a consequence of that fact.

---

## The transaction log: `_delta_log/` is the table

Drop the `_delta_log/` directory and you have an unstructured Parquet dump. Lose the Parquet and you have an empty schema. The log is the source of truth for what files exist, what schema they have, and what version of the table you're seeing.

### Physical layout

Inside `_delta_log/` you find:

- **Commit files** (`00000000000000000000.json`, `…0001.json`, …) — one per transaction, each an ordered list of `Action` records: `add` (a new file), `remove` (a tombstoned file), `metaData` (schema), `protocol` (reader/writer version), `commitInfo`, `txn` (idempotent commit ID), `cdc` (change-data-feed action), `domainMetadata`.
- **Checkpoint files** (`…0010.checkpoint.parquet`) — every 10 commits by default (`delta.checkpointInterval`), Delta materializes the full state into a Parquet checkpoint so cold readers don't have to replay every JSON. Modern Delta versions also write **multi-part checkpoints** (`*.checkpoint.NNNN.MMMM.parquet`) and **V2 checkpoints** (manifest + sidecar files) for very large tables.
- **`_last_checkpoint`** — a tiny JSON pointer to the most recent checkpoint version. Saves a directory listing on cold reads.
- **`_change_data/`** — a sibling directory holding CDF Parquet for non-insert-only commits when Change Data Feed is enabled.

A reader resolves "table at version N" by: read `_last_checkpoint` → load that checkpoint Parquet → replay JSON commits *after* it up to N. ([delta.io transaction log protocol](https://delta.io/blog/2023-07-07-delta-lake-transaction-log-protocol/), [Databricks: Diving into Delta Lake](https://www.databricks.com/blog/2019/08/21/diving-into-delta-lake-unpacking-the-transaction-log.html)).

This is why **log compaction matters**: with a million commits and no checkpoint, a cold reader pays for a million tiny JSON reads from object storage. On a streaming Bronze table that commits every minute, that's >500K commits/year. Checkpoints make state retrieval O(log N). For very high-velocity tables, raise `delta.checkpointInterval`, enable V2 checkpoints, and consider **log compactions** (`delta.logCompactionInterval`, Delta 3.2+) which collapse runs of JSON commits into single compacted JSONs without doing a full checkpoint.

### Reader / writer protocol versions

Historically, the protocol used monotonic integer versions: R1/W1 → R3/W7. The modern model is **`R3/W7` + table features** — each capability (deletion vectors, column mapping, type widening, Liquid Clustering, identity columns, V2 checkpoints, generated columns, row tracking, timestampNTZ, variant) is a named feature you opt into, and the writer advertises only the features it needs. This is why a "Delta 3.x" writer can produce a table that a "Delta 2.x" reader can't open even though the integer protocol numbers haven't changed: the missing piece is a feature flag, not a version number ([Delta PROTOCOL.md](https://github.com/delta-io/delta/blob/master/PROTOCOL.md)).

Operationally: when you enable a new table feature (e.g., `ALTER TABLE … SET TBLPROPERTIES ('delta.enableDeletionVectors' = true)`), older readers without that feature stop being able to read the table. Plan feature adoption with downstream consumers in mind — especially for Delta Sharing recipients on older clients.

### Concurrency: optimistic + log-rename

Every writer (a) reads the current latest version `V`, (b) stages its commit as `V+1.json`, (c) atomically renames into `_delta_log/` using the underlying store's putIfAbsent semantics. If two writers race, one wins the rename, the other detects the conflict, re-runs *only* the conflict-resolution rules (not the full re-execution; e.g., a concurrent INSERT of disjoint data is auto-retried), and tries `V+2`. On ABFS / ADLS Gen2 and S3 (with conditional writes / DynamoDB lock historically) this is safe; on plain S3 without conditional puts you used to need the multi-cluster lock — mostly history now, but worth knowing for legacy pipelines. ([Delta concurrency control](https://docs.delta.io/latest/concurrency-control.html))

The architect-relevant point: **Delta is ACID at the table level, not the row level.** A failed write doesn't corrupt the table; it just doesn't commit. Concurrent UPDATEs to disjoint partitions auto-retry; concurrent UPDATEs to the same partition error out with a `ConcurrentAppendException` that the application must handle.

---

## Data skipping and statistics

The cheapest optimization Delta offers. At write time, Delta computes per-file statistics — `numRecords`, `minValues`, `maxValues`, `nullCount`, `tightBounds` — and stores them in the `add` action of the commit. At query time, the planner uses min/max to **skip files**: a query for `WHERE date = '2026-05-10'` against a file with `min=2024-01-01, max=2024-12-31` skips the file entirely.

### `delta.dataSkippingNumIndexedCols` defaults to 32

Two consequences:

1. **If your filter columns are at schema position 33+, you get zero skipping.** Full-file scans every time. Move them earlier in the schema, or use `delta.dataSkippingStatsColumns` to name them explicitly.
2. **The default protects you from collecting stats on long string columns** — every `minValue`/`maxValue` is stored in the log per file. An HL7 message body or FHIR JSON column would balloon the log into uselessness.

```python
# Healthcare pattern: limit indexed columns to the hot filter set
spark.sql("""
  ALTER TABLE silver.claim_line SET TBLPROPERTIES (
    'delta.dataSkippingNumIndexedCols' = '8',
    'delta.dataSkippingStatsColumns' = 
      'service_date,member_id,payer_id,procedure_code,paid_amount'
  )
""")
```

The narrower the indexed-cols set, the smaller and faster the log, and the more useful the stats.

### Skipping by data type

- **Numeric, date, timestamp** — skip cleanly. Tight ranges, small log footprint.
- **Short categorical strings** (state codes, ICD-10 prefixes) — skip well at moderate cardinality.
- **Long strings, JSON, structs, arrays, maps** — skip poorly or not at all. Delta truncates string min/max at 32 chars by default; for high-cardinality random-looking strings (UUIDs), the min/max range covers practically the whole space, so skipping never fires.
- **Structs** — only top-level fields up to the indexed-cols budget get stats; deeply nested fields are opaque to skipping. **Anti-pattern**: dumping FHIR Bundles as a single deep `bundle: STRUCT` column kills skipping for everything inside it.

### `ANALYZE TABLE` is different from file stats

`ANALYZE TABLE … COMPUTE STATISTICS FOR ALL COLUMNS` computes **table-level** stats — histograms, NDV (number of distinct values) — used by the cost-based optimizer for join reordering, broadcast decisions, etc. Separate from the file-level min/max stats Delta auto-collects. Run ANALYZE after large loads on dimension tables that are join keys. Predictive Optimization on UC managed tables now runs this for you.

---

## File layout primitives

### Partitioning — useful, but narrower than people think

Hive-style partitioning (`/year=/month=/`) maps to physical directories and lets the planner prune directory listings before reading file stats.

**When it still wins:**
- Time-series tables filtered almost exclusively by date (`service_date`, `claim_received_date`)
- Each partition is ≥ 1 GB and ≤ a few thousand files
- Cardinality is bounded (e.g., date is fine; `member_id` is not)

**When it hurts:**
- **High cardinality** — partitioning by `member_id` in a 10M-member health plan = 10M directories, each with one tiny file. Object-store list operations dominate; OPTIMIZE can't help across partitions.
- **Small partitions** — under ~1 GB per partition you spend more on file overhead than you save on pruning.
- **Skewed cardinality** — if 80% of claims come from one payer, partitioning by `payer_id` creates one elephant partition and many crumb partitions.

The 2026 default for new tables on Databricks is **no partitioning** — use Liquid Clustering instead.

### Z-Order — multidim clustering, but rewrite-heavy

Z-Order interleaves the bits of the clustering columns ("Z-curve" / Morton order) so files contain rows that are close in the chosen multi-dimensional space. `OPTIMIZE t ZORDER BY (member_id, service_date)` rewrites every file in the affected scope to achieve this layout — every Z-Order pass is **O(table size)**.

Z-Order works best on 1–4 columns; with more, the curve fragmentation degrades skipping. Z-Order does **not** record cluster identity in the log, so subsequent OPTIMIZE passes redo the entire layout. Z-Order is being **superseded by Liquid Clustering** for new tables, but you'll see Z-Ordered tables in any Databricks shop with a >2-year history.

### Liquid Clustering — incremental, log-aware, the new default

Liquid Clustering (LC) maintains a **ZCube ID** in the transaction log, marking which files belong to which "incrementally clustered group." Subsequent OPTIMIZE passes only touch *unclustered* ZCubes, making clustering **incremental** rather than table-wide. It uses a **Hilbert curve** (better locality than Z-curve at higher dimensions) and supports up to 4 clustering keys.

Crucially:
- You specify clustering keys at table-creation time, **and you can change them later without rewriting the whole table.**
- Existing partitions on a Z-Ordered or partitioned table can be migrated to LC via `ALTER TABLE … CLUSTER BY (...)`; the OPTIMIZE that follows is incremental.
- LC is GA in DBR 15.2+ ([Liquid Clustering GA blog](https://www.databricks.com/blog/announcing-general-availability-liquid-clustering)).

```sql
-- Create-time
CREATE TABLE silver.claim_line (
  claim_id STRING, claim_line_id STRING, member_id STRING,
  service_date DATE, procedure_code STRING, paid_amount DECIMAL(18,2)
) CLUSTER BY (member_id, service_date);

-- Change later — incremental, not full rewrite
ALTER TABLE silver.claim_line CLUSTER BY (payer_id, service_date);

-- Migration from Z-Order or partitioned table
ALTER TABLE bronze.claim_837 CLUSTER BY (received_date);
-- subsequent OPTIMIZE incrementally clusters
```

**Automatic Liquid Clustering** (GA 2025): `CLUSTER BY AUTO`. Predictive Optimization observes query telemetry, models the workload, runs cost-benefit on candidate keys, and picks for you. Reported to be optimizing millions of tables in production ([Automatic LC announcement](https://www.databricks.com/blog/announcing-automatic-liquid-clustering)). For greenfield healthcare tables in 2026, default to `CLUSTER BY AUTO` and let PO learn the workload.

### Bucketing — mostly dead

Hash bucketing (Hive-era) is essentially deprecated for Delta. Liquid Clustering subsumes the use case (co-locate by key) without the rigidity (fixed bucket count, no incremental change). Don't introduce buckets on new tables.

---

## OPTIMIZE / VACUUM / Predictive Optimization

### File size targets

Default `spark.databricks.delta.optimize.maxFileSize = 1 GB`. `OPTIMIZE` runs a **bin-packing algorithm**: filters files smaller than `maxFileSize`, packs them sequentially into ~1 GB bins, rewrites. Operation is **idempotent** — running it twice does nothing the second time. ([delta.io: small-file compaction](https://delta.io/blog/2023-01-25-delta-lake-small-file-compaction-optimize/))

For very large tables (multi-TB), consider 2 GB files; for high-concurrency MERGE workloads, smaller files (256 MB–512 MB) reduce write amplification. Auto-tune with `delta.tuneFileSizesForRewrites = true` so Delta picks based on observed write/read ratio.

### Auto-Compact and Optimized Writes

Two write-path companions to OPTIMIZE:

- **Optimized Writes** (`spark.databricks.delta.optimizeWrite.enabled`) inserts a **shuffle before the final write** to coalesce small per-task partitions into larger files. Trades shuffle for fewer files. Recommended for streaming and high-fan-in batch.
- **Auto-Compact** (`spark.databricks.delta.autoCompact.enabled`) runs a **small synchronous OPTIMIZE after each commit**, packing files to ~128 MB (smaller than the manual OPTIMIZE 1 GB target — by design, to keep auto-compact cheap).

Use **both for streaming ingestion** (Bronze layer). Don't expect them to replace a scheduled OPTIMIZE; they keep things from getting *worse*, but a weekly OPTIMIZE is still needed for hot tables.

### VACUUM math

- Default file retention 7 days (`delta.deletedFileRetentionDuration`).
- Default log retention 30 days (`delta.logRetentionDuration`).
- VACUUM physically deletes files no longer referenced by *any* version younger than the retention threshold.
- **Once you VACUUM, time-travel earlier than the retention threshold is gone forever.** That's the key trade.
- With deletion vectors, VACUUM also cleans orphan DV files.

**HIPAA conversation:** retention has two opposing pressures. (a) **Right-to-be-forgotten / minimum necessary** wants data physically gone after deletion or expiry — VACUUM at the *short* retention. (b) **Audit trail** wants long history — argues for long retention, but **time-travel is the *wrong tool* for HIPAA audit.** Use Change Data Feed → an audit-log table for compliance, and keep VACUUM at 7–30 days. PHI deleted from a Delta table is *not gone* until VACUUM has run past the retention window — important for breach response and BAA conversations.

### Predictive Optimization (GA 2025)

Replaces hand-tuned OPTIMIZE/VACUUM/ANALYZE schedules on UC managed tables. **Default-on for accounts created after Nov 11, 2024**; rolling out to existing accounts through April 2026. Runs on a serverless SKU billed separately. Auto-decides:
- When to OPTIMIZE
- What file size
- When to VACUUM
- What stats to collect
- (With `CLUSTER BY AUTO`) what clustering keys to use

**When PO is wrong:**
- **Very small tables** (overhead > benefit)
- **Tables with bursty workloads** where telemetry is non-stationary
- **Tables you intentionally want at small file sizes** (e.g., for high-concurrency point lookups)

You can disable per-table. ([Predictive Optimization docs](https://docs.databricks.com/aws/en/optimizations/predictive-optimization))

For an architect's defaults: **enable PO at the catalog level for all UC managed tables**, then disable per-table where you have a documented reason.

---

## Deletion Vectors — Merge-on-Read for Delta

Pre-DV, every DELETE/UPDATE/MERGE that touched even one row in a 1 GB file rewrote the entire file. This was the dominant cost driver of Silver-layer pipelines.

DV makes Delta a **Merge-on-Read** format: row-level deletes are written as a compact bitmap (a `.bin` file) and recorded in the log as a `deletionVector` field on the `add` action. The existing data file is **untouched**. ([delta.io: Deletion Vectors](https://delta.io/blog/2023-07-05-deletion-vectors/), [Databricks docs](https://docs.databricks.com/aws/en/delta/deletion-vectors))

### Performance profile

- **DELETE/UPDATE/MERGE 10–100× faster** on selective changes (mark-not-rewrite).
- **Read-side overhead is small**: readers AND-out the DV bitmap during scan. Photon and Spark have native paths.
- **DVs accumulate.** After many small deletes, scanning a file means reading 1 GB of Parquet then masking out rows — the I/O is unchanged.

### `REORG TABLE … APPLY (PURGE)`

Rewrites only files that have DVs, materializing the deletes and clearing DVs. **Not the same as VACUUM** — REORG produces new Parquet, then VACUUM later cleans the now-unreferenced old files.

A typical schedule: **REORG monthly** on tables with heavy DV churn (Silver claim corrections, member-update tables); VACUUM after that.

### Compatibility

- **DV + Liquid Clustering** — fully compatible, recommended combination for new tables in 2026.
- **DV + UniForm/Iceberg reads** — Iceberg readers see DV-applied data via the async-generated Iceberg metadata, but only after the metadata gen run completes (lag of seconds to minutes).
- **DV + CDF** — compatible; CDF emits row-level deletes correctly.
- **DV + older OSS Delta readers** — requires `deletionVectors` writer feature, blocking pre-3.0 OSS readers.

### Healthcare angle

DVs make member-attribute corrections (gender, address fix) cheap on Silver tables. Without DV, a single member correction in a 100M-row member table could rewrite every file containing that member's claim history. With DV, the correction is metadata + a small bitmap.

---

## MERGE optimization

The MERGE operator is the workhorse of Silver-layer pipelines and dominates many Databricks bills. Three layers of optimization stack:

### 1. Low-Shuffle Merge (LSM)

Default in DBR 10.4+ ([docs](https://learn.microsoft.com/en-us/azure/databricks/optimizations/low-shuffle-merge)). Pre-LSM, MERGE shuffled both source and target through the same plan, even for unmodified rows. LSM splits the plan: a join identifies the touched files, modified rows go through a shuffle path, **unmodified rows in those files bypass shuffle** and stream directly. ~2–3× speedup average, up to 5×. LSM also preserves Z-Order/LC layout on unmodified rows on a best-effort basis.

### 2. DV-enabled MERGE

With DVs, MERGE doesn't rewrite the unmodified portion of a file at all — it writes a DV for deleted/updated rows and appends new versions to a fresh file. **Combine LSM + DV and a MERGE that updates 0.1% of rows touches ~0.1% of bytes.**

### 3. `WHEN MATCHED BY SOURCE` / `WHEN NOT MATCHED BY SOURCE`

Newer clauses (DBR 14+). Lets you act on rows in the *target* that don't match the source — the missing piece needed for full-outer-MERGE and for SCD2 closure logic. Pre-existing pattern was a separate UPDATE pass; now it's one statement.

```python
# Member SCD2 with WHEN NOT MATCHED BY SOURCE for full closure
(target.alias("t")
  .merge(updates.alias("s"), 
         "t.member_id = s.member_id AND t.is_current = true")
  .whenMatchedUpdate(
     condition="s.row_hash <> t.row_hash",
     set={"is_current": "false", "valid_to": "s.effective_date"})
  .whenNotMatchedInsert(values={
     "member_id": "s.member_id",
     "is_current": "true",
     "valid_from": "s.effective_date",
     "row_hash": "s.row_hash"})
  # close out members no longer in feed (e.g., termed members)
  .whenNotMatchedBySourceUpdate(
     condition="t.is_current = true",
     set={"is_current": "false", "valid_to": "current_date()"})
  .execute())
```

### MERGE-key cardinality is the single biggest cost driver

Merging on a low-cardinality key (e.g., `payer_id` instead of `claim_id`) makes every file a candidate; the engine rewrites broadly. If cardinality is unavoidably low, **partition or cluster by that key** to keep matched files in a narrow zone.

### MERGE write path differs by table type

- **UC managed Delta** — gets the latest optimizations (DV, LSM, predictive layouts), Photon-accelerated, Predictive Optimization runs.
- **External Delta on ADLS/S3** — same engine, but you own the layout. PO on external tables is more limited.

---

## Schema evolution

### `mergeSchema = true`

Write-side option (`mergeSchema = true`) and table-level (`delta.enableMergeSchema = true`) auto-add new columns of compatible types on append/MERGE. Existing files keep their old schema; new files have the new column; readers project NULL for missing columns.

### Type widening (Delta 3.3+)

`int → bigint`, `float → double`, `decimal(p,s) → decimal(p',s')` (wider precision), `date → timestampNTZ`. **Critically, Parquet files are not rewritten** — the metadata change updates the schema, and readers cast at scan time. Enable via `delta.enableTypeWidening = true` (a writer feature). Without this, a `bigint` overflow in a column once typed `int` requires a full rewrite. ([delta.io type widening](https://docs.delta.io/latest/delta-type-widening.html))

### Column rename / drop

Requires **column mapping** (`delta.columnMapping.mode = 'name'`). Column mapping decouples the logical column name in the schema from the **physical column ID** in the Parquet files. Once enabled:
- **Rename** — zero data movement.
- **Drop** — zero data movement; column simply hidden.

Tradeoffs: column-mapped tables require column-mapping-aware readers (Delta 1.2+, modern Iceberg via UniForm). Streaming readers need **schema tracking** (Delta 3.0+) on column-mapped tables that have undergone rename/drop, otherwise streams fail. ([Schema evolution docs](https://docs.databricks.com/aws/en/data-engineering/schema-evolution))

### Generated columns and constraints

```sql
CREATE TABLE silver.claim_line (
  ...
  service_date DATE,
  service_year INT GENERATED ALWAYS AS (year(service_date)),
  paid_amount DECIMAL(18,2),
  CONSTRAINT positive_paid CHECK (paid_amount >= 0)
) CLUSTER BY (member_id, service_date);
```

Generated columns compute on write and let the optimizer push date predicates into clustering keys without forcing the user to remember the derived column. Constraints (`CHECK`) are enforced on write and propagate to data-quality dashboards.

---

## Change Data Feed (CDF)

Enable per-table: `ALTER TABLE t SET TBLPROPERTIES ('delta.enableChangeDataFeed' = true)`. Each non-insert-only commit emits a `_change_data/` Parquet with `_change_type ∈ {insert, update_preimage, update_postimage, delete}` and `_commit_version`, `_commit_timestamp`. ([delta.io: CDF](https://delta.io/blog/2023-07-14-delta-lake-change-data-feed-cdf/))

```python
df = (spark.read.format("delta")
        .option("readChangeFeed", "true")
        .option("startingVersion", 1234)
        .table("silver.claim_line"))
# or via SQL: SELECT * FROM table_changes('silver.claim_line', 1234)
```

### Storage cost

Typically **10–30% extra** on heavy-update tables; near zero on insert-only Bronze (CDF infers from `add` actions). Insert-only and full-partition-delete commits don't write `_change_data/` at all — Delta reconstructs from the main Parquet ([Community thread on CDF cost](https://community.databricks.com/t5/data-governance/change-data-feed-cost/td-p/75871)).

Retention follows the same VACUUM rules — CDF older than the retention window is unreadable.

### Use cases beyond CDC

- **HIPAA audit trail** — persist CDF to a separate immutable audit table (the right tool for "who changed what, when").
- **ML feature stores** — incrementally refresh feature aggregations from claim_line CDF rather than full re-aggregation.
- **Streaming gold tables** — Silver CDF → DLT/Streaming Tables with stateful aggregation.

**Don't enable CDF on every table "just in case."** Pay-per-table; enable where you have a real downstream consumer.

---

## Time travel and clones

### Time travel

`SELECT * FROM t VERSION AS OF 1234` or `TIMESTAMP AS OF '2026-05-01'`. Cheap to read (one log replay), expensive to keep (every old file pinned in storage).

**HIPAA reality check.** Time travel is a great *engineering* feature (rollback after a bad ETL) and a poor *compliance* feature. Three reasons:
1. After VACUUM, the time-travel window collapses to the retention period.
2. Time-travel cannot answer "who deleted this PHI and when" — only "what did the table look like."
3. Time-travel storage cost grows monotonically until VACUUM.

**Practical pattern:** 7-day VACUUM for cost; CDF → audit_log table for the "who, what, when" trail; deep clones at quarter-end for any longer-horizon "snapshot" need.

### Clones

**Shallow clone** copies *log + manifest only*; data files are still pointed at the source. Cheap (seconds), independent metadata (separate ACLs), but **if the source VACUUMs, the shallow clone breaks** (FileNotFoundException). ([Databricks: clone](https://docs.databricks.com/aws/en/delta/clone))

**Deep clone** copies metadata + all data files. Independent. **Incremental** — re-running clone copies only changed files since last clone (uses the transaction log to compute the delta).

**Patterns:**
- **DR**: nightly deep clone to secondary region; incremental cost. Cross-region replication for healthcare BCP — see Module 23.
- **Testing**: shallow clone of prod into dev catalog, hammer with experiments, drop. **Don't VACUUM the source while a shallow clone is live.**
- **Branching / "Git for data" lite**: shallow clone, mutate, validate, then atomic-swap the catalog name.

**Limitations:** history is *not* preserved — clones start at version 0. Stream / COPY INTO checkpoints copy only with deep clones.

---

## UniForm / Iceberg reads

UniForm (now sometimes called "Iceberg reads on Delta") writes Delta as the system of record and **asynchronously generates Iceberg v2 metadata** on the same compute that did the Delta commit. Iceberg readers (Trino, Snowflake, Athena) see the table after the async generation lands, with some lag (seconds to minutes depending on commit rate). ([Databricks: Read Delta with Iceberg clients](https://learn.microsoft.com/en-us/azure/databricks/delta/uniform))

**UC managed Iceberg** (Public Preview from DBR 16.4 LTS): Unity Catalog can also manage *native* Iceberg tables alongside Delta, with a federation layer (Iceberg REST Catalog) so the same governed catalog serves both. UniForm is the Delta-first path; UC managed Iceberg is for shops that pick Iceberg as system of record.

**Practical caution for healthcare:** if you publish to external readers (Snowflake for the analytics team, Athena for ad-hoc), the lag in async metadata generation means your readers can be a commit or two behind. **Don't promise sub-minute SLAs on the Iceberg path; document the lag.**

For greenfield work in May 2026: pick **Delta** as default; enable UniForm when you have an Iceberg-reader consumer; pick **UC managed Iceberg** only when Iceberg is the strategic choice (e.g., a multi-engine shop that has standardized on Iceberg).

---

## UC managed vs external tables

**Managed (UC):** Delta only (or managed Iceberg in 2025+). UC owns the storage path, lifecycle, optimization. Drop the table → data is deleted (after retention). Predictive Optimization, full feature set. **Recommended default.** ([UC managed tables](https://docs.databricks.com/aws/en/tables/managed))

**External:** points at a path you control via a **Storage Credential** (the IAM/Service-Principal identity) + **External Location** (the path it covers). Drop the table → data stays. Required for: reading existing ADLS data you can't move, multi-engine writes (Snowflake also writes the same path), or contractual data-residency carve-outs. Predictive Optimization on external tables exists but is more limited.

**Decision rule:** **start managed**. Go external only when you have a hard requirement.

---

## Production reality

### The medallion architecture is *not* a data model

Joe Reis and Daniel Beach's critique is correct: Bronze/Silver/Gold tells you nothing about Kimball-vs-Inmon, surrogate keys, conformed dimensions, or grain. Use it as the **directory naming convention** for raw → cleansed → curated, then put real modeling underneath. ([Joe Reis: Medallion is not a data model](https://practicaldatamodeling.substack.com/p/medallion-architecture-is-not-a-data), [Confessions of a Data Guy: Medallion farce](https://www.confessionsofadataguy.com/the-medallion-architecture-farce/))

Practical rules:
- **Bronze** = raw landing, append-only, retention by regulation.
- **Silver** = conformed, grain-stable, deduped, late-binding views OK.
- **Gold** = analytics-ready; here is where you actually *model* (star, OBT, or hybrid).

Don't apply the pattern to every dataset by reflex — three layers per dataset triples storage and compute for trivial datasets.

### Star vs flat (OBT) on the lakehouse

Star schema still wins for human analysts (Power BI / Tableau). One-Big-Table (OBT) wins for ML feature pipelines and BI tools that exploit columnar pruning. With Liquid Clustering and column mapping you can have both: model star in Gold, materialize OBT views with `CREATE MATERIALIZED VIEW` for ML.

### SCD types in PySpark/SQL on Delta

- **Type 1** (overwrite): trivial MERGE … WHEN MATCHED UPDATE.
- **Type 2** (history): MERGE with `is_current` flag + `valid_from/valid_to`. Use surrogate key on the dimension. With LC on `(natural_key, is_current)` lookups stay fast.
- **Type 3** (limited history): two columns `current_x`, `previous_x`. Rare in practice.
- **Type 6** (1+2+3 hybrid): used for member-attribute lineage in healthcare where both "as-was" and "as-is" reporting are required.

### Surrogate keys

Use 64-bit BIGINT identity columns (`GENERATED BY DEFAULT AS IDENTITY`) on dimensions. Joining on surrogate keys is faster than on long natural keys, and SCD2 *requires* surrogate keys to disambiguate row-versions. **Don't use UUIDs** — they kill data skipping (high entropy) and bloat join keys.

### Late-binding views vs materialized views

Views = cheap to maintain, expensive at query. **Materialized views** (Databricks DLT or `CREATE MATERIALIZED VIEW` in DBSQL) = pre-computed, refreshed on schedule or incrementally. **Streaming Tables** (`CREATE STREAMING TABLE`) are the recommended path for incremental Gold.

---

## When NOT to use Delta features

- **CDF on every table** — pay-per-table, enable only with a real downstream consumer.
- **Shallow clones for DR** — source VACUUM kills the clone; use deep clones.
- **Time-travel as audit** — wrong tool. Use CDF → audit_log instead.
- **VACUUM RETAIN 0 HOURS** in production — permanent loss of in-flight rollback. Allowed only for explicit privacy-purge runs after legal review.
- **Z-Order on a Liquid-Clustered table** — mutually exclusive; pick LC.
- **`mergeSchema = true` in production** — silent schema drift; require explicit ALTER TABLE.

---

## Healthcare anti-patterns (specific to PHI / claims data)

1. **Over-partition by `member_id`** — 10M-member plan = 10M tiny partitions. Use Liquid Clustering on `member_id` instead.
2. **No OPTIMIZE schedule on streaming Bronze** — Auto-Compact alone leaves you at 128 MB files; reads suffer.
3. **MERGE on a low-cardinality key** — merging on `payer_id` causes the planner to consider every file as a candidate. Add `claim_id` to the merge key, even if it's not part of business logic.
4. **Time-travel-as-undo with VACUUM=0** — storage grows unbounded, and "time travel" gives a false sense of HIPAA audit compliance.
5. **Giant struct columns** — a `fhir_bundle: STRING` or `claim_837_raw: STRUCT` column with 500 nested fields = no skipping. Shred at Silver.
6. **Forgetting `dataSkippingNumIndexedCols` after schema growth** — you added 40 audit columns; your filter columns are now at position 35–45. Skipping silently stopped working.
7. **Z-Order on a Liquid-Clustered table** — pick one (LC).
8. **Shallow clone of prod for "DR"** — source VACUUM kills the clone. DR needs deep clone.
9. **Enable CDF on every table** — 10–30% extra storage on heavy-update tables.
10. **Forgetting REORG TABLE … APPLY (PURGE)** on heavy-DV tables — DV bitmaps accumulate, scans slow.

---

## Sanity check

1. What does `_delta_log/` actually contain physically, and why do checkpoints exist?
2. Why does `delta.dataSkippingNumIndexedCols` defaulting to 32 silently destroy query performance for some healthcare schemas, and how would you detect it?
3. What does Liquid Clustering do that Z-Order doesn't, and why is it the 2026 default for new tables?
4. A senior data engineer says "we should enable Predictive Optimization everywhere." When would you *not*?
5. What's the difference between a **shallow clone** and a **deep clone**, and why is shallow clone a footgun for DR specifically?
6. A MERGE on a 100M-row member table is taking 6 hours. The merge key is `payer_id`. What three things would you change?
7. You enable CDF on a heavy-update Silver table to support an ML feature store. What's the rough storage overhead, and what's the retention policy you should set?

---

## Further reading

- [Delta Lake transaction log protocol — delta.io](https://delta.io/blog/2023-07-07-delta-lake-transaction-log-protocol/)
- [Delta PROTOCOL.md — github](https://github.com/delta-io/delta/blob/master/PROTOCOL.md)
- [Diving into the Delta Lake transaction log — Databricks blog](https://www.databricks.com/blog/2019/08/21/diving-into-delta-lake-unpacking-the-transaction-log.html)
- [Internals of Delta Lake — japila-books](https://books.japila.pl/delta-lake-internals/DeltaLog/)
- [Use Liquid Clustering — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/delta/clustering)
- [Predictive Optimization — Databricks docs](https://docs.databricks.com/aws/en/optimizations/predictive-optimization)
- [Announcing Automatic Liquid Clustering — Databricks blog](https://www.databricks.com/blog/announcing-automatic-liquid-clustering)
- [Delta Lake Deletion Vectors — delta.io blog](https://delta.io/blog/2023-07-05-deletion-vectors/)
- [Low Shuffle Merge — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/optimizations/low-shuffle-merge)
- [Lessons from MERGE on billions of records — Confessions of a Data Guy](https://www.confessionsofadataguy.com/lessons-learned-from-merge-operations-with-billions-of-records-on-databricks-spark/)
- [Schema evolution in Databricks](https://docs.databricks.com/aws/en/data-engineering/schema-evolution)
- [Delta type widening — delta.io](https://docs.delta.io/latest/delta-type-widening.html)
- [Change Data Feed — delta.io blog](https://delta.io/blog/2023-07-14-delta-lake-change-data-feed-cdf/)
- [Read Delta tables with Iceberg clients — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/delta/uniform)
- [Joe Reis — Medallion Architecture is NOT a data model](https://practicaldatamodeling.substack.com/p/medallion-architecture-is-not-a-data)
- [SCD Type 2 with Delta MERGE — Sandeep Manocha](https://medium.com/@smanocha/slowly-changing-dimension-scd-type-2-with-delta-merge-in-databricks-2736fba1a10f)
