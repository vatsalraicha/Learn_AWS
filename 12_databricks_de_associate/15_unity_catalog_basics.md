# Module 15 — Unity Catalog Basics

> **Domain 5 (11%) — Data Governance & Quality** — THE governance topic
>
> **Exam objectives covered:**
> - Explain the difference between **managed and external tables**.
> - **Identify the grant of permissions** to users and groups within UC.
> - **Identify key roles in UC.**
> - Identify **how audit logs are stored.**
> - Use **lineage features** in UC.
>
> **What you must walk away with:** The three-level namespace. The `USE CATALOG / USE SCHEMA / SELECT` privilege chain. GRANT vs REVOKE. The difference between `GRANT SELECT ON SCHEMA` and `GRANT SELECT ON ALL TABLES IN SCHEMA`. Ownership. Dynamic views, row filters, column masks. Audit and lineage.

---

## Coverage map (verbatim July 25, 2025 objectives → where taught here)

| Verbatim objective | Taught in section |
|---|---|
| Explain the difference between managed and external tables | §7 "Managed vs external tables (recap from Module 04)" — DROP semantics, PO scope, recovery |
| Identify the grant of permissions to users and groups within UC | §2 privilege chain (USE CATALOG → USE SCHEMA → SELECT); §3 `GRANT SELECT ON SCHEMA` vs `ON ALL TABLES IN SCHEMA`; §4 full privilege list + securables + ALL PRIVILEGES; §11 putting-it-together |
| Sample Question 2 (GRANT SELECT ON SCHEMA — read-only) | §2 + §3 exam-trap |
| Identify key roles in UC | §5 "Key roles in UC" (Account / Metastore / Workspace admin; Catalog / Schema / Table owners; group as principal; ownership prerequisite for GRANT) |
| Identify how audit logs are stored | §8 "Audit logs" — `system.access.audit` AND cloud-storage log delivery (also revisited in Module 14) |
| Use lineage features in Unity Catalog | §9 "Lineage" — Catalog Explorer UI + `system.access.table_lineage` / `system.access.column_lineage` |
| Identify DDL features (CREATE FUNCTION + ROW FILTER, SET MASK, dynamic views with `is_member`) | §6 "Dynamic views, row filters, and column masks — fine-grained access" |
| Tag-based discovery | §10 "Tags" |

Cross-references: Module 04 for managed/external table fundamentals; Module 11 for the LDP expectations vs UC row-filter distinction; Module 14 for system-table observability; Module 16 for Delta Sharing privileges.

---

## 1. The three-level namespace

Every UC-governed object lives at three levels:

```
catalog . schema . table
```

Examples:
- `main.sales.orders`
- `dev_finance.bronze.invoices`
- `analytics.gold.daily_revenue`

This replaces the legacy two-level `database.table` (where the catalog was implicit, usually `hive_metastore`).

### What lives at each level

| Level | Examples |
|-------|----------|
| **Catalog** | `main`, `dev_main`, `prod_main`, `analytics`, `hive_metastore` (legacy) |
| **Schema** | `bronze`, `silver`, `gold`, `sales`, `finance` |
| **Table-level objects** | Tables, views, materialized views, functions, volumes, models |

### Why three levels

- Catalog = environment / business unit boundary (`prod_main` vs `dev_main`).
- Schema = domain (`sales`, `finance`, `hr`).
- Table = the data object.

You can switch context:

```sql
USE CATALOG main;
USE SCHEMA sales;
SELECT * FROM orders;        -- resolves to main.sales.orders
```

Or always fully qualify:
```sql
SELECT * FROM main.sales.orders;
```

### ⚠️ Exam trap — `hive_metastore` catalog

Pre-UC tables live under the `hive_metastore` catalog by default. New UC catalogs (like `main`) are the modern home. If a question shows `database.table` (two-level), it's typically pre-UC; UC questions show `catalog.schema.table` (three-level).

---

## 2. The privilege chain — `USE CATALOG → USE SCHEMA → SELECT`

To **read** a table at `main.sales.orders`, a user needs **three** privileges:

1. **`USE CATALOG`** on the catalog `main`.
2. **`USE SCHEMA`** on the schema `main.sales`.
3. **`SELECT`** on the table `main.sales.orders`.

All three are required. Missing any one → "object does not exist" or "permission denied."

```sql
GRANT USE CATALOG ON CATALOG main TO `analysts`;
GRANT USE SCHEMA  ON SCHEMA  main.sales TO `analysts`;
GRANT SELECT      ON TABLE   main.sales.orders TO `analysts`;
```

### ⚠️ Exam trap — the privilege chain is REQUIRED

**This is the highest-frequency UC trap on the exam.**

A common scenario: the team grants `SELECT` on a table, but the user can't see it. Why? Because they don't have `USE CATALOG` and `USE SCHEMA` on the upstream levels.

If a question hands you `GRANT SELECT ON SCHEMA <s> TO <group>` as the answer and **explicitly mentions that USE CATALOG and USE SCHEMA are already granted**, that's the canonical Question-2-style answer (the official sample question states "assuming that the analyst group already has USE CATALOG and USE SCHEMA permissions").

---

## 3. The `GRANT SELECT ON SCHEMA` shortcut — vs `ON ALL TABLES IN SCHEMA`

Two superficially similar statements with different semantics:

### 3.1 `GRANT SELECT ON SCHEMA <schema> TO <principal>`

```sql
GRANT SELECT ON SCHEMA main.sales TO `analysts`;
```

- Grants SELECT on **all current AND future** tables and views in the schema.
- **Inherits forward** — a table created tomorrow in `main.sales` is automatically readable.
- The exam-canonical answer for "team needs read access to a schema."

### 3.2 `GRANT SELECT ON ALL TABLES IN SCHEMA <schema> TO <principal>`

```sql
GRANT SELECT ON ALL TABLES IN SCHEMA main.sales TO `analysts`;
```

- Grants SELECT on **only the tables that exist right now**.
- **Does NOT inherit forward** — tables created tomorrow are NOT automatically readable.

### Why this matters

If you grant `ON ALL TABLES IN SCHEMA` and a new table is created, the team can't read it until someone runs ANOTHER `GRANT`. This is operationally a pain.

`ON SCHEMA` is the right grain for "this team owns/reads this domain."

### ⚠️ Exam trap — `ON SCHEMA` vs `ON ALL TABLES IN SCHEMA`

If the prompt says "team needs read access to existing AND future tables," → **`GRANT SELECT ON SCHEMA`**.

If the prompt says "team needs read access to specific existing tables only" → could be `GRANT SELECT ON ALL TABLES IN SCHEMA` or per-table grants.

---

## 4. Privileges — the full list

The privileges you must recognize:

### Top-level
- **`USE CATALOG`** — see and navigate within a catalog
- **`USE SCHEMA`** — see and navigate within a schema
- **`CREATE CATALOG`** — at the metastore level, create catalogs
- **`CREATE SCHEMA`** — at the catalog level, create schemas
- **`MANAGE`** — admin-level management on the target

### Table-level
- **`SELECT`** — read rows
- **`MODIFY`** — write (INSERT, UPDATE, DELETE, MERGE)
- **`CREATE TABLE`** — at the schema level, create tables
- **`CREATE VIEW`** — at the schema level, create views
- **`CREATE FUNCTION`** — at the schema level, create functions

### Volume-level
- **`READ VOLUME`** — read files
- **`WRITE VOLUME`** — write files

### Function-level
- **`EXECUTE`** — call the function

### Everything
- **`ALL PRIVILEGES`** — superset of everything available on the target type. Grants every privilege at once.

### Examples

```sql
-- Read-only access to a table
GRANT SELECT ON TABLE main.sales.orders TO `analysts`;

-- Write access (insert/update/delete)
GRANT MODIFY ON TABLE main.sales.orders TO `data_engineers`;

-- Read everything in a schema (existing + future)
GRANT SELECT ON SCHEMA main.sales TO `analysts`;

-- Schema owner gets everything
GRANT ALL PRIVILEGES ON SCHEMA main.sales TO `sales_team_lead`;

-- Revoke
REVOKE SELECT ON SCHEMA main.sales FROM `analysts`;
```

### ⚠️ Exam trap — `ALL PRIVILEGES` vs `SELECT`

Sample Question 2 (the official one) tests this: "the analyst group needs read-only access." Distractors include `GRANT ALL PRIVILEGES`. **Read-only = `SELECT`**, not `ALL PRIVILEGES`. ALL is too much.

`INSERT` (as a distractor) is also wrong — INSERT is write, not read. UC doesn't actually use the word `INSERT` as a privilege name (it's `MODIFY`), but third-party prep questions sometimes write it that way.

---

## 5. Key roles in UC

| Role | Scope | What they can do |
|------|-------|------------------|
| **Account admin** | Account | Manage all workspaces, create metastores, manage users |
| **Metastore admin** | Per metastore | Create catalogs, grant on metastore root |
| **Workspace admin** | Per workspace | Manage workspace resources, users in workspace |
| **Catalog owner** | Per catalog | All privileges on the catalog, can GRANT on it |
| **Schema owner** | Per schema | All privileges on the schema, can GRANT on it |
| **Table owner** | Per table | All privileges on the table, can GRANT on it |
| **Group** | — | Container for users; grants apply to groups |

### Ownership is required to grant

To `GRANT SELECT ON TABLE main.sales.orders`, you must be the **owner** of the table (or have `MANAGE` privilege, or be an admin at a higher level).

A common operational pattern:
- Service principal creates tables → becomes owner.
- Service principal is in a "data_engineering_admins" group → effective owner via the group.
- Admin group GRANTs to consumer groups.

### Transfer ownership

```sql
ALTER TABLE main.sales.orders OWNER TO `data_team_admins`;
ALTER SCHEMA main.sales OWNER TO `data_team_admins`;
ALTER CATALOG main OWNER TO `data_team_admins`;
```

### ⚠️ Exam trap — admin roles

"Metastore admin" vs "account admin" vs "workspace admin" are distinct. **Metastore admin** is the canonical UC admin role (catalog-creation, metastore-level grants). **Account admin** is the super-admin role across all workspaces in the account.

---

## 6. Dynamic views, row filters, and column masks — fine-grained access

For finer-than-table access control, UC supports three mechanisms.

### 6.1 Dynamic views

```sql
CREATE VIEW main.sales.orders_dyn AS
SELECT
  order_id,
  customer_id,
  amount,
  -- Hide SSN from non-HR users
  CASE WHEN is_member('hr_admins') THEN ssn ELSE 'XXX-XX-XXXX' END AS ssn,
  -- Hide cost data from non-finance users
  CASE WHEN is_member('finance') THEN cost ELSE NULL END AS cost,
  -- Restrict to EU rows for EU-only users
  region
FROM main.sales.orders_internal
WHERE is_member('global') OR region = current_user_region();
```

Functions you'll see:
- **`is_member('group_name')`** — true if the current user is in the group.
- **`current_user()`** — the user's email.
- **`is_account_group_member('group')`** — same as is_member but for account-level groups.

### 6.2 Row filters — modern declarative ABAC

```sql
CREATE FUNCTION main.sec.region_filter(region STRING)
RETURN
  is_member('global_admins') OR region = 'EU';

ALTER TABLE main.sales.orders
SET ROW FILTER main.sec.region_filter ON (region);
```

The function gets called per row at query time. Returns true → row visible; false → row hidden.

Attached to a column via `ON (region)`.

### 6.3 Column masks

```sql
CREATE FUNCTION main.sec.mask_ssn(ssn STRING)
RETURN
  CASE WHEN is_member('hr_admins') THEN ssn ELSE 'XXX-XX-XXXX' END;

ALTER TABLE main.sales.orders
ALTER COLUMN ssn SET MASK main.sec.mask_ssn;
```

The mask function transforms the column value per query. Visible only as the masked value to users who don't pass the predicate.

### Comparison

| Mechanism | Granularity | Where applied |
|-----------|-------------|---------------|
| Dynamic view | Row + column | `SELECT * FROM view` |
| Row filter (function) | Row | Attached to the table directly |
| Column mask (function) | Column | Attached to the column |

The exam tests recognition — "hide column X from group Y at query time" → column mask or dynamic view. "Restrict rows by region" → row filter or dynamic view. **Not** an LDP expectation (that's ingestion-time quality).

---

## 7. Managed vs external tables (recap from Module 04)

```sql
-- Managed
CREATE TABLE main.sales.orders (...);

-- External
CREATE TABLE main.sales.orders_ext (...)
LOCATION 'abfss://lake@stg.dfs.core.windows.net/orders';
```

- **Managed:** UC owns storage. `DROP TABLE` deletes data after retention.
- **External:** You own storage. `DROP TABLE` deletes only metadata.

Managed tables get Predictive Optimization automatically; external tables do not.

### ⚠️ Exam trap — DROP semantics (revisited)

The exam often phrases this: "team accidentally drops a table; can they recover?"
- **Managed:** No (data is gone after retention).
- **External:** Yes (the files remain; recreate the external table pointing at the same LOCATION).

---

## 8. Audit logs

UC logs every administrative and data access action. Two storage locations:

### 8.1 `system.access.audit` system table

```sql
SELECT
  event_time,
  user_identity.email AS user,
  action_name,
  request_params,
  response.status_code
FROM system.access.audit
WHERE service_name = 'unityCatalog'
  AND event_time >= current_date() - INTERVAL 1 DAY
ORDER BY event_time DESC;
```

- Queryable as a Delta table.
- Updated near-real-time.
- Retention: limited (typically 1 year on system tables).

### 8.2 Cloud-storage log delivery (raw)

Configured at the account level — audit logs are delivered as JSON files to a customer-controlled cloud bucket (S3 / ADLS / GCS).

- Long-term retention (you control it).
- Raw JSON.
- Read by SIEM tools (Splunk, Datadog, Sentinel).

### ⚠️ Exam trap — audit log storage

If the exam asks "where are audit logs stored?", the expected answers:
- **`system.access.audit`** (queryable, near-real-time, time-limited retention).
- **Customer cloud storage via log delivery** (long-term, raw).

Both are valid. Pick whichever matches the question's focus.

---

## 9. Lineage

UC automatically captures **table-to-table lineage** and **column-level lineage** for queries running against UC-governed tables.

### Where to see lineage

- **Catalog Explorer UI** — open a table → "Lineage" tab → graph of upstream/downstream tables.
- **`system.access.table_lineage`** — queryable.
- **`system.access.column_lineage`** — column-level lineage.

```sql
-- Find every table downstream of main.bronze.orders
SELECT DISTINCT
  target_table_full_name AS downstream
FROM system.access.table_lineage
WHERE source_table_full_name = 'main.bronze.orders'
  AND event_time >= current_date() - INTERVAL 7 DAYS;
```

### What captures lineage

- Spark SQL queries.
- DataFrame writes that produce a Delta table in UC.
- LDP pipelines.
- DBSQL queries.

### What does NOT capture lineage

- Queries through legacy `hive_metastore` (non-UC).
- External tools writing directly to cloud storage (Spark or otherwise) that bypass UC.
- JDBC reads/writes through Lakehouse Federation (lineage is limited).

### ⚠️ Exam trap — lineage requires UC

"Lineage is automatic" is true **only for UC-governed objects**. A team using `hive_metastore` won't see lineage in the Catalog Explorer.

---

## 10. Tags

UC objects can be tagged for organization, discovery, and access policies:

```sql
ALTER TABLE main.sales.orders SET TAGS ('domain' = 'sales', 'pii' = 'true');
ALTER SCHEMA main.sales SET TAGS ('owner_team' = 'sales-eng');

-- Find all PII-tagged tables
SELECT *
FROM system.information_schema.tag_assignments
WHERE tag_name = 'pii' AND tag_value = 'true';
```

Useful for "find all tables containing PII" or "all tables owned by the sales team."

---

## 11. Putting it together — granting a team read access

```sql
-- Assumed: `analysts` is a UC group, `main.sales.orders` exists.

-- Step 1: catalog-level
GRANT USE CATALOG ON CATALOG main TO `analysts`;

-- Step 2: schema-level — covers existing + future tables
GRANT USE SCHEMA  ON SCHEMA  main.sales TO `analysts`;
GRANT SELECT      ON SCHEMA  main.sales TO `analysts`;

-- That's it. Analysts can now read every current and future table in main.sales.
```

For column-level redaction:

```sql
-- Hide SSN from non-HR
CREATE FUNCTION main.sec.mask_ssn(ssn STRING)
RETURN CASE WHEN is_member('hr_admins') THEN ssn ELSE 'XXX-XX-XXXX' END;

ALTER TABLE main.sales.customers
ALTER COLUMN ssn SET MASK main.sec.mask_ssn;
```

For row-level restriction:

```sql
CREATE FUNCTION main.sec.region_filter(region STRING)
RETURN is_member('global') OR region = current_user_region();

ALTER TABLE main.sales.orders
SET ROW FILTER main.sec.region_filter ON (region);
```

---

## 12. Mini quiz (cold)

1. To read a table at `main.sales.orders`, what THREE privileges are required?
2. The team grants `SELECT` on the table but the analyst still can't see it. What's likely missing?
3. To grant read access to a schema including future tables, which command?
4. To grant read access to only existing tables, which command?
5. The sample question asks "read-only access, assuming USE CATALOG and USE SCHEMA are granted." Which grant?
6. To hide the `ssn` column from non-HR users at query time, which mechanism?
7. The team drops a managed table by mistake. Can they recover?
8. The team drops an external table by mistake. Can they recover?
9. Where are UC audit logs stored?
10. Which system table holds table-to-table lineage?

### Answers

1. **`USE CATALOG` on `main`, `USE SCHEMA` on `main.sales`, `SELECT` on `main.sales.orders`.** All three required.
2. **`USE CATALOG` or `USE SCHEMA`** is likely missing. The privilege chain requires all three.
3. **`GRANT SELECT ON SCHEMA main.sales TO <group>`** — covers existing AND future tables.
4. **`GRANT SELECT ON ALL TABLES IN SCHEMA main.sales TO <group>`** — only existing tables.
5. **`GRANT SELECT ON SCHEMA sales_data TO analysts`** — the canonical Question-2 answer.
6. **Column mask** (or dynamic view). Not an LDP expectation.
7. **No** (canonically) — DROP on a managed table removes the data after retention.
8. **Yes** — DROP on an external table removes only metadata. Recreate the external table at the same LOCATION.
9. **`system.access.audit`** (queryable) AND/OR **customer cloud storage via log delivery** (long-term).
10. **`system.access.table_lineage`**. Column lineage is in `system.access.column_lineage`.

---

## 13. Sanity check before moving on

You should be able to:
- Recite the 3-level namespace and the 3-privilege chain.
- Choose `GRANT SELECT ON SCHEMA` for "existing AND future tables."
- Differentiate dynamic view / row filter / column mask vs LDP expectation.
- Recite managed-vs-external DROP semantics.
- Know `system.access.audit` and `system.access.table_lineage` exist.
- Identify ownership as the prerequisite for granting.

If any of those are fuzzy, re-read Sections 2, 3, 4, and 6.
