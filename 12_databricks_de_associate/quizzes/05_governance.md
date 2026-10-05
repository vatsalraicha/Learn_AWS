# Quiz 05 — Data Governance & Quality (11%)

> Take cold. ~15 questions. ~2 min per question. Covers Unity Catalog (UC), privileges, dynamic views, row filters, column masks, Delta Sharing, Lakehouse Federation.

---

## Recall

1. What are the three levels of the Unity Catalog namespace?
2. Name the three privileges in the UC read-privilege chain required to `SELECT` from a table.
3. What is the difference in `DROP TABLE` behavior between a UC-managed table and an external table?
4. Which UC feature lets a recipient outside the Databricks ecosystem read your shared data through an open protocol?
5. Which UC feature lets you query a remote PostgreSQL or Snowflake database as if it were a UC catalog, without ingesting?

## Apply

6. The `analysts` group needs to read all current and future tables in schema `main.sales`. Write the three GRANT statements.
7. The team wants `analysts` to read only existing tables in `main.sales` — new tables should require an explicit grant. Which GRANT command shape?
8. You need to give the `eu_team` group access to only the rows where `region = 'EU'`. Sketch the dynamic view definition.
9. You need to mask the `ssn` column for all non-members of the `pii_readers` group, returning `'***-**-****'`. Sketch the column mask function.
10. You want to share three Delta tables read-only with an external partner who does NOT use Databricks. Which UC feature and which sharing protocol?
11. You need to read live Snowflake data from a Databricks SQL query without copying it into Delta. Which UC feature?

## Diagnose

12. A user has `SELECT` on table `main.sales.orders` but gets "object does not exist" when querying. They don't have `USE CATALOG` or `USE SCHEMA`. What's the actual problem?
13. The team ran `GRANT SELECT ON ALL TABLES IN SCHEMA main.sales TO analysts`. Three weeks later they create a new table in `main.sales` and the analysts can't read it. Why?
14. A Delta Sharing recipient on Databricks reports unexpectedly high cross-cloud egress costs. They're reading the share frequently. What's going on, and what's the mitigation?

## Defend

15. Defend Delta Sharing (the open protocol) over giving partners a Databricks account each.

---

## Answers

1. **catalog.schema.table** (3 levels). ⚠️ **Exam trap:** Pre-UC code uses 2 levels (`database.table`) backed by Hive metastore — new work should always use the 3-level form.
2. **`USE CATALOG` on the catalog**, **`USE SCHEMA` on the schema**, **`SELECT` on the table** — ALL three are required. ⚠️ **Exam trap:** This chain is one of the most-tested concepts. A user with `SELECT` but no `USE CATALOG` gets a misleading "object does not exist" error.
3. **Managed:** `DROP TABLE` removes both metadata AND the underlying data files (subject to retention). **External:** `DROP TABLE` removes metadata only — the data files remain in the external location. ⚠️ **Exam trap:** "External" means UC owns the table definition but the storage is in a customer-managed `LOCATION`.
4. **Delta Sharing — open protocol (D2X / Open Sharing)**. Uses a bearer-token credential file the recipient downloads and reads with any Delta Sharing client (Python, Spark, Power BI, Tableau, etc.). Recipient does NOT need a Databricks workspace.
5. **Lakehouse Federation** — creates a foreign catalog backed by JDBC to MySQL, PostgreSQL, Snowflake, Redshift, BigQuery, SQL Server, etc. Read-only.
6. ```sql
   GRANT USE CATALOG ON CATALOG main TO `analysts`;
   GRANT USE SCHEMA  ON SCHEMA  main.sales TO `analysts`;
   GRANT SELECT      ON SCHEMA  main.sales TO `analysts`;
   ```
   ⚠️ **Exam trap:** `GRANT SELECT ON SCHEMA` covers existing AND future tables. `GRANT SELECT ON ALL TABLES IN SCHEMA` covers only existing tables at grant time.
7. **`GRANT SELECT ON ALL TABLES IN SCHEMA main.sales TO analysts`** — applies only to tables that already exist when run. New tables created later do NOT inherit the grant.
8. ```sql
   CREATE OR REPLACE VIEW main.sales.orders_eu AS
   SELECT *
   FROM main.sales.orders
   WHERE CASE WHEN is_member('eu_team') THEN region = 'EU'
              ELSE FALSE
         END;
   ```
   Then grant `SELECT` on the view to `eu_team`. The `is_member()` function evaluates per-query against the executing user's group memberships.
9. ```sql
   CREATE OR REPLACE FUNCTION main.sec.mask_ssn(ssn STRING)
   RETURNS STRING
   RETURN CASE WHEN is_member('pii_readers') THEN ssn
               ELSE '***-**-****'
          END;

   ALTER TABLE main.sales.customers
     ALTER COLUMN ssn SET MASK main.sec.mask_ssn;
   ```
10. **Delta Sharing using the open protocol** (D2X / Open Sharing). The provider creates a share, adds the three tables, defines a recipient (which generates a credential file), and the partner uses any Delta Sharing client. ⚠️ **Exam trap:** Delta Sharing is read-only by design — recipients cannot write back. Also note D2D (Databricks-to-Databricks) uses UC identities; D2X uses bearer tokens.
11. **Lakehouse Federation** — create a connection to Snowflake, then a foreign catalog. Query via standard 3-level names: `snowflake_catalog.schema.table`. Reads are pushed down to Snowflake; no copy in Delta.
12. **Missing `USE CATALOG` and/or `USE SCHEMA`.** All three privileges (`USE CATALOG` + `USE SCHEMA` + `SELECT`) are required to read a table. Without `USE CATALOG`, UC won't even let you see the object exists — hence the confusing "object does not exist" error rather than "permission denied." Fix: grant the `USE` privileges.
13. **`GRANT ... ON ALL TABLES IN SCHEMA` applies to existing tables only.** New tables created after the grant don't inherit it. Fix: use `GRANT SELECT ON SCHEMA main.sales TO analysts` instead — this covers existing AND future tables.
14. **Delta Sharing reads transfer the underlying Parquet/Delta files** from the provider's cloud storage to the recipient's compute. If the recipient is in a different cloud or region, each read incurs **cross-cloud / cross-region egress fees** charged by the provider's cloud. Mitigations: (a) co-locate recipient compute in the same region/cloud as the share storage; (b) cache reads at the recipient side (CTAS into a recipient-local Delta table); (c) reduce read frequency. ⚠️ **Exam trap:** The exam explicitly tests "cost considerations of cross-cloud sharing."
15. **Delta Sharing (open protocol):** zero overhead for the partner (no Databricks account, no IAM mapping, no workspace provisioning), uses an industry-standard protocol with clients for Python/Spark/Power BI/Tableau, is read-only by design (safe), and is governed by UC on the provider side (audit, lineage, revocation in one place). **Per-partner Databricks accounts:** procurement and admin overhead per partner, partner must learn Databricks, you bear identity and workspace governance for each, no clean revocation. Open Delta Sharing is the clear winner for arms-length data distribution.
