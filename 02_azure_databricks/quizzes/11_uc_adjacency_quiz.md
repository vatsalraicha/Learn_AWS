# Quiz — Module 11: UC Adjacency Products

## Recall

**Q1.** Name four classes of operation where UC lineage misses (or coarsens) the column-level mapping.

<details><summary>Answer</summary>

1. **Python UDFs and Scala UDFs** — captured as table-to-table edge, not column-level.
2. **Pandas / non-Spark Python** that reads via direct file API — misses lineage entirely.
3. **External jobs** — anything pulling Delta over Delta Sharing or JDBC from outside doesn't record lineage on the UC side.
4. **BI tools** (Power BI / Tableau) — recorded as "BI tool reads" but the downstream report graph is opaque to UC.

Plus: **cross-metastore / cross-region** lineage is hard-broken — lineage graphs are per-metastore.

**How teams supplement:** OpenLineage + Marquez or DataHub as a Spark listener; pipe `system.access.*` to a side store for cross-region stitching; accept that Power BI lineage lives in Purview/Fabric and federate manually.
</details>

**Q2.** What's the rule of thumb for Lakehouse Federation vs replication?

<details><summary>Answer</summary>

**"Federate to discover, replicate to operate."**

- **Federate** for ad-hoc cross-platform queries and small-dimension joins with predicate pushdown.
- **Replicate** (CDC into UC, Lakeflow Connect, scheduled snapshot) for production analytics, wide joins, or anything ML-bound.

Federation latency (100–500 ms typical) is fine for analytics, not for OLTP-style point lookups. Wide joins still pull data even with predicate pushdown.

**Important governance note:** federation does NOT make UC govern the source. A user with UC SELECT on `snowflake_fc.public.claims` is using the connection's credentials at the source — UC sees the federated metadata, not the underlying ACL.
</details>

**Q3.** What are the two flavors of Delta Sharing, and which is rarely used for PHI?

<details><summary>Answer</summary>

- **Databricks-to-Databricks (D2D)** — provider and recipient both on Databricks; identity, audit, notebook sharing native. **Fine for BAA-covered partners.**
- **Open protocol** — provider issues a recipient profile (token + endpoint); any open `delta-sharing` client connects.

**Open protocol is rarely used for PHI** because:
- Bearer-token model concentrates risk on a long-lived secret
- Audit on the recipient side is best-effort
- BAA coverage doesn't transit the open protocol cleanly

Most regulated shops use Delta Sharing for **de-identified or aggregate** data; PHI moves over D2D between BAA-covered tenants or stays inside the catalog.
</details>

---

## Apply

**Q4.** Set up a Delta Sharing share for an outbound de-identified claims summary to a partner who's on Databricks.

<details><summary>Answer</summary>

```sql
-- 1. Create the share
CREATE SHARE outbound_payer_x
  COMMENT 'De-identified claim summaries for Payer X — quarterly';

-- 2. Add objects to the share (must be de-identified Gold tables, not PHI)
ALTER SHARE outbound_payer_x 
  ADD TABLE prod_deid_claims.gold.claim_summary_deid;

ALTER SHARE outbound_payer_x 
  ADD TABLE prod_deid_claims.gold.member_demographics_deid;

-- 3. Create the recipient (Databricks-to-Databricks)
CREATE RECIPIENT payer_x_recipient
  USING ID 'payer-x-databricks-account-uuid'
  COMMENT 'Payer X data engineering team — D2D';

-- 4. Grant the share to the recipient
GRANT SELECT ON SHARE outbound_payer_x 
  TO RECIPIENT payer_x_recipient;

-- 5. Audit configuration — verify outbound shows up in system.access.outbound_*
SELECT * FROM system.access.outbound_share_events 
WHERE share_name = 'outbound_payer_x' 
LIMIT 10;
```

**Governance discipline:**
- **Never share PHI tables directly** — always de-identify into a Gold table first.
- **D2D when partner is on Databricks** (this case); open protocol only for non-PHI / aggregate.
- **Document the share** in the data-products catalog with a data sharing agreement (DSA) reference.
- **Set token expiration short** for open-protocol recipients (24-48 hr) and rotate on schedule.
- **Audit `system.access.outbound_*`** weekly to verify only expected access patterns.
</details>

---

## Diagnose

**Q5.** A team uses Lakehouse Federation to query a Snowflake `claims` table from a Databricks dashboard. The dashboard takes 90 seconds. They've added more warehouse cluster size; no improvement. What's likely happening?

<details><summary>Answer</summary>

**Most likely root cause:** federation is read-mostly with predicate pushdown for *some* shapes, but **wide joins between a Databricks fact and a remote 100M-row table** still pull significant data over the network — pushdown helps, but doesn't eliminate the data movement.

**Diagnosis:**
1. **Check the query plan in DBSQL Query Profile** — look for the federation node. How many rows are being read from Snowflake?
2. **Check the predicate** — if the WHERE clause is non-deterministic or wraps a UDF, pushdown may silently fail. Federation pushdown has the same UDF limitation as Delta predicate pushdown.
3. **Check the cross-region latency** — if Snowflake is in a different region, ~150ms cross-region adds up over many round trips.
4. **Check whether the join is wide** — federation works fine for "small dimension joins"; wide-fact joins are where it breaks down.

**Fixes (in order of preference):**

1. **Replicate the Snowflake table into UC** via Lakeflow Connect (SQL Server connector wraps Snowflake too) or scheduled snapshot. **"Federate to discover, replicate to operate"** — once you're in production, replication beats live federation.

2. **Use Snowflake Catalog Federation** (a different feature from query federation): UC reads Snowflake-managed Iceberg tables directly from cloud storage, so the compute is Databricks-only. Faster + cheaper than going through Snowflake compute.

3. **Materialize the federated query** as a UC Materialized View; refresh hourly. The dashboard hits the MV at single-digit-second latency.

4. **Increase warehouse size doesn't help** — the bottleneck is the network/source side, not Databricks compute. Bigger Databricks warehouse just does the inefficient remote-pull faster.

**Production discipline:** federation for ad-hoc and exploration; replication for production. **Document this rule** so teams don't keep re-discovering it.
</details>

---

## Defend

**Q6.** A peer says "we should put all our raw clinical PDFs in DBFS — it's faster than Volumes and we already know the path patterns." Defend or refute.

<details><summary>Answer</summary>

**Refute, decisively.**

Where the peer is right (limited):
- DBFS *is* faster to set up if you ignore governance.
- `dbutils.fs.ls()` against DBFS feels familiar.

Where the peer is wrong:
- **DBFS is being deprecated.** UC has been deprecating DBFS-pattern access since 2023. Init scripts already moved off DBFS; data is the next domino.
- **DBFS has no UC governance** — no GRANT, no audit, no lineage edges. For PHI-bearing PDFs, this is a HIPAA violation waiting to happen.
- **Cluster security modes block DBFS access** — UC-enabled clusters in shared/single-user mode can't reach `/dbfs/...` paths the same way. Code that depends on DBFS will break on upgrade.
- **No FUSE-based access for Python libraries** — Volumes give `open()`, `PIL`, `PyMuPDF`, `transformers.from_pretrained`, etc. that "just work." DBFS requires explicit `dbutils.fs.cp` round-tripping.

**Volumes are the right answer:**
- **Managed volume** for files UC owns the lifecycle of (raw clinical PDFs landed by ingestion).
- **External volume** for files in an existing ADLS path UC governance-only registers.
- **FUSE access** at `/Volumes/<catalog>/<schema>/<volume>/...` — Python libs work natively.
- **GRANT-based access control** — read/write permissions per group.
- **Lineage edges** — a job that reads from a volume shows in `system.access.audit`.
- **Audit-friendly** — every read/write is logged.

**For healthcare specifically:** PHI in PDFs requires GRANT-based access, audit trails, and the ability to demonstrate to an auditor that "only authorized users could read these files." DBFS gives you none of that. Volumes give you all of it.

**The systemic point:** DBFS is the legacy path. Module 21 covers the HIPAA discipline; storing PHI in ungoverned DBFS paths is a finding waiting to happen.

**Source:** [Volumes docs](https://learn.microsoft.com/en-us/azure/databricks/volumes/), [Volumes GA blog](https://www.databricks.com/blog/announcing-general-availability-unity-catalog-volumes).
</details>
