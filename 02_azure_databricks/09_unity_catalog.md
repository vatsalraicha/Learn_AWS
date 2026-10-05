# Module 9 — Unity Catalog Deep

> **Goal of this module:** internalize the UC mental model an architect lives in — the three-level namespace, the permissions model (GRANT + dynamic views + ABAC + workspace-catalog binding), the three-permission collision (workspace ACL ↔ UC ↔ workspace binding), the storage-credential layer that brokers ADLS access, and the Azure RBAC bypass risk healthcare orgs need to close.

---

## Why UC dominates the architect interview

For an architect role on Databricks at a healthcare org, **Unity Catalog is the single most important topic.** It governs:
- Who can read what data (PHI vs non-PHI)
- Where data physically lives (UC managed vs external)
- What lineage and audit you can produce
- What the BAA boundary looks like in operational terms
- How identities flow from Entra ID through to GRANTs

Get UC wrong, and the rest of the platform is a security incident waiting to happen. Get it right, and Databricks becomes a credible HIPAA platform.

---

## Three-level namespace: `catalog.schema.object`

UC's first hard rule: **`catalog.schema.object`** replaces the legacy two-level `database.table` of `hive_metastore`. Catalogs are securable, schemas inherit from catalogs, and tables/views/volumes/models/functions/metrics all sit at the third level.

The metastore itself is **regional and singleton** — one UC metastore per cloud region per Databricks account ([UC best practices](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/best-practices)).

### What a catalog represents — the design choice

The architect-relevant decision: **what does a catalog mean in your org?** Two patterns dominate:

**Per-environment** (`dev_finance`, `staging_finance`, `prod_finance`)
- Recommended starting point because workspace-catalog binding can hard-block prod access from dev workspaces
- Maps cleanly to dev/stage/prod promotion lifecycles
- The default for most teams ([Leigh Robertson on UC structure](https://medium.com/@leighrobertson512/how-should-you-structure-your-databricks-unity-catalog-91e633651e18))

**Per-domain** (`claims`, `member`, `provider`, `pharmacy`)
- Better for data-mesh shops with strict business-line isolation
- Doubles your environment dimension into schemas (`claims.dev_silver`, `claims.prod_silver`), which many find awkward
- Common in large orgs with autonomous data-product teams

**The healthcare hybrid:** for an Optum-scale org, a useful pattern is `prod_phi_<domain>` catalogs bound to a small set of workspaces with stricter network ACLs, plus `prod_deidentified_<domain>` catalogs bound broadly. This is the **two-workspace PHI/analytics split** the healthcare reference architecture (Module 22) builds on.

Daniel Beach's blunt summary: ["catalogs become your primary isolation boundary, and schemas and tables inherit from those decisions"](https://www.confessionsofadataguy.com/migrating-to-databricks-a-guide/) — get this wrong and you'll be re-cataloging two years in.

### Schema and object hierarchy

Inside a catalog, schemas group objects logically (analogous to a "database" in legacy SQL terms). Each schema contains:
- **Tables** (managed Delta, managed Iceberg, external Delta/Iceberg/Parquet, foreign tables via Lakehouse Federation)
- **Views** (regular and dynamic)
- **Materialized views**
- **Streaming tables**
- **Volumes** (managed and external) — for unstructured data
- **Functions** (UDFs, AI Functions registered as UC objects)
- **Models** (MLflow models, registered in UC)
- **Metric views** (semantic-layer measures + dimensions)

Each is a **securable** with its own GRANT lattice.

---

## Permissions model

### GRANT semantics — ANSI plus a few twists

```sql
-- Grant SELECT at catalog level — applies to all schemas/tables unless overridden
GRANT SELECT ON CATALOG prod_phi_claims TO `actuaries-group`;

-- Grant USE CATALOG — needed for any read in the catalog
GRANT USE CATALOG ON CATALOG prod_phi_claims TO `actuaries-group`;

-- Grant at schema level
GRANT SELECT ON SCHEMA prod_phi_claims.silver TO `data-engineers-group`;

-- Grant at table level
GRANT SELECT ON TABLE prod_phi_claims.silver.claim_line TO `actuaries-group`;

-- Show effective grants
SHOW GRANTS ON TABLE prod_phi_claims.silver.claim_line;
```

Key points:
- **`USE CATALOG` is a separate privilege** from `SELECT` — users need both to query.
- **Privileges flow downward** — grants at catalog apply to all schemas/tables unless overridden.
- **Every securable has an `OWNER`.** Owner can grant. Default is the principal who created it.
- **Group-based grants are the production discipline** — never grant to named users; always to Entra/SCIM groups.

### Dynamic views — pre-ABAC fine-grained access

Pre-ABAC, fine-grained access used **dynamic views** with `current_user()` or `is_account_group_member()` predicates:

```sql
CREATE OR REPLACE VIEW silver.claim_line_secured AS
SELECT 
  claim_id,
  claim_line_id,
  service_date,
  CASE 
    WHEN is_account_group_member('clinical-staff') THEN diagnosis_code
    ELSE 'REDACTED'
  END AS diagnosis_code,
  -- mask member_id for non-clinical groups
  CASE 
    WHEN is_account_group_member('clinical-staff') THEN member_id
    WHEN is_account_group_member('actuaries') THEN sha2(member_id, 256)
    ELSE NULL
  END AS member_id,
  paid_amount
FROM silver.claim_line;
```

These work but require per-table wiring and quickly explode in a large estate. **ABAC is the modern answer.**

### Row filters and column masks (pre-ABAC)

```sql
-- Column mask
CREATE FUNCTION mask_member_id(member_id STRING)
RETURNS STRING
RETURN CASE 
  WHEN is_account_group_member('clinical-staff') THEN member_id
  ELSE sha2(member_id, 256)
END;

ALTER TABLE silver.claim_line ALTER COLUMN member_id 
  SET MASK mask_member_id;

-- Row filter
CREATE FUNCTION filter_by_payer(payer_id STRING)
RETURNS BOOLEAN
RETURN payer_id IN (SELECT payer_id FROM admin.user_payer_assignments 
                    WHERE user_email = current_user());

ALTER TABLE silver.claim_line SET ROW FILTER filter_by_payer ON (payer_id);
```

Row filters and column masks are functional but per-table — at scale you have hundreds of tables and dozens of policy variations. **ABAC is the scaling answer.**

### ABAC (Public Preview April 2026)

ABAC is the big 2026 governance move. **Tags ("governed tags") attach to securables, then policies attach at catalog/schema/table level and are evaluated dynamically.** Currently scoped to **column masks and row filters on tables, materialized views, streaming tables**. Not yet: model serving, volumes, functions ([ABAC docs](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/abac/)).

```sql
-- Define a governed tag taxonomy
CREATE TAG SCOPE phi_class WITH VALUES ('high', 'medium', 'low', 'none');
CREATE TAG SCOPE retention_class WITH VALUES ('7yr', '6yr', '3yr', '1yr');

-- Tag a column
ALTER TABLE silver.claim_line 
  ALTER COLUMN member_id SET TAGS ('phi_class' = 'high');

-- Define a policy that applies based on tag
CREATE POLICY mask_high_phi
ON COLUMN MASKED WITH SHA2
WHEN tag('phi_class') = 'high' AND NOT is_account_group_member('clinical-staff')
APPLY TO TABLES IN CATALOG prod_phi_claims;
```

**Tag once at ingest, policy at catalog, audit centrally.** Key wins:
- One policy covers thousands of tables
- New tables that get tagged correctly inherit the policy automatically
- Audit trail: `system.access.audit` shows policy applications

**Realistic gap:** ABAC doesn't yet cover **purpose-based access** (research vs operations vs billing). Healthcare with HIPAA Minimum Necessary still bolts on Immuta or Privacera ([Immuta UC integration](https://www.immuta.com/blog/scaling-secure-data-access-with-immuta-databricks-unity-catalog/)).

### Workspace-catalog binding — the hard isolation primitive

```sql
-- Bind a catalog to specific workspaces only
ALTER CATALOG prod_phi_claims 
  SET WORKSPACE BINDING (WORKSPACES = ['ws-phi-001', 'ws-phi-002'])
  ISOLATED;
```

**This supersedes user-level grants.** Even if a user has SELECT on the catalog, they cannot read from a non-bound workspace ([UC access control](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/access-control/workspace-catalog-binding)).

**For healthcare:** the load-bearing primitive that makes "PHI workspace" vs "analytics workspace" a hard isolation boundary, not just a grant pattern. Even if ABAC policies fail or a grant is overly permissive, workspace binding acts as a second-layer veto.

### The three-permission collision

In a real Databricks workspace at any reasonable scale, **three permission systems coexist:**

1. **Workspace-level ACLs** (legacy; cluster ACLs, job ACLs, notebook ACLs at workspace scope)
2. **Unity Catalog grants** (account-level on securables: catalog, schema, table, etc.)
3. **Workspace-catalog bindings** (which can override individual UC grants)

Mid-migration from `hive_metastore` to UC, dashboards break and engineers lose access to data they previously owned. The field anti-pattern is "migrate tables first, then grant broadly when people complain" ([Polestar Analytics](https://www.polestaranalytics.com/blog/unity-catalog-migration)).

**The architect's debugging mental model:** when a user says "I can't read X," check in this order:
1. Is `USE CATALOG` granted?
2. Is `SELECT` granted on the table (or inheritable from schema/catalog)?
3. Is the workspace bound to the catalog (if isolation is on)?
4. Is there a workspace-level deny lurking from the legacy ACL system?
5. Does the user need access to the storage credential / external location (for external tables)?

Module 17 (Admin Playbook) has the full troubleshooting tree.

---

## Storage credentials and external locations

UC sits *above* storage and brokers access via:

- **Storage credential** — an Azure managed identity (preferred) or service principal (legacy) that has data-plane RBAC on ADLS.
- **External location** — a path under that credential's authority (e.g., `abfss://container@account.dfs.core.windows.net/`).

External tables register against an external location; UC managed tables get a generated path under the metastore's root location.

```sql
-- Create the storage credential (one-time, account admin)
CREATE STORAGE CREDENTIAL prod_uc_credential
  WITH (AZURE_MANAGED_IDENTITY = '/subscriptions/.../managedIdentities/uc-mi-prod')
  COMMENT 'Production UC storage credential';

-- Create an external location backed by it
CREATE EXTERNAL LOCATION prod_phi_data
  URL 'abfss://phi-data@prodstg.dfs.core.windows.net/'
  WITH (CREDENTIAL prod_uc_credential)
  COMMENT 'PHI data root';

-- Register an external table against that location
CREATE TABLE prod_phi_claims.silver.claim_line_external (
  ...
)
USING DELTA
LOCATION 'abfss://phi-data@prodstg.dfs.core.windows.net/silver/claim_line/';
```

**Service principals are now "legacy"** because they can't reach storage accounts behind firewall rules; **managed identities are the modern default.** Full identity flow:

```
Azure Entra ID → Azure Managed Identity → Storage Blob Data Contributor on ADLS
                                       ↓
UC Storage Credential (wraps the MI)
                                       ↓
UC External Location (defines the path scope)
                                       ↓
UC Tables / Volumes (point at paths under that location)
                                       ↓
UC GRANTs decide WHO can use the table → UC issues short-lived access to ADLS
```

### The Azure RBAC bypass risk

This is the single most-missed gap in healthcare UC deployments:

**A user with Azure-portal `Storage Blob Data Reader` on the same container can read the raw Parquet directly, bypassing UC row filters and column masks.**

The UC layer's enforcement only applies when access goes *through* UC. If anyone has direct storage-side RBAC, they have an end-run around governance.

**The fix:** lock down the storage account so **only the UC managed identity** has data-plane RBAC. Humans get UC-mediated access only. No `Storage Blob Data Reader` on PHI containers for individuals or groups; the UC managed identity is the single principal that touches the bytes.

For healthcare, this is non-negotiable. Module 21 covers the audit checklist.

### Other Azure-RBAC gotchas

- **Service-principal-based credentials don't work with storage firewalls or private endpoints** — must switch to managed identities.
- **`User Access Administrator`** on the storage account (not just Owner) is required to *create* the storage credential, which trips up shops where networking and IAM are owned by different teams.

---

## Identity federation with Entra ID

### Account-level identity is mandatory

UC requires **account-level** identities, not workspace-local. **Workspace-level groups don't appear in `GRANT` statements** ([UC requirements](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/get-started)). Workspace-level SCIM is being deprecated in favor of account-level SCIM.

### Automatic Identity Management (Public Preview 2026)

Replaces the SCIM-connector dance. Users, groups, and SPs flow from Entra ID into the Databricks account console **without a separate sync app** ([AIM docs](https://learn.microsoft.com/en-us/azure/databricks/admin/users-groups/automatic-identity-management/)). This was a major pain point through 2024 (group drift, deletes-not-propagating, nested-group flattening) and is now mostly solved on Azure.

### Recommended pattern

From [Databricks identity best practices](https://learn.microsoft.com/en-us/azure/databricks/admin/users-groups/best-practices):

1. **Manage all access through groups** (never named users)
2. **Assign one Entra group containing all Databricks users** to the account-level SCIM (the umbrella group)
3. **Assign sub-groups to specific workspaces** (workspace assignment is per-group)
4. **Use sub-groups for GRANTs** — `actuaries-claims-readers`, `clinicians-phi-readers`, etc.

Group naming pattern that works at scale: `<role>-<domain>-<access-level>` (e.g., `dataeng-claims-writers`, `analyst-member-readers`, `oncall-platform-admins`).

---

## Lineage — what it captures, what it misses

UC lineage is automatic for SQL run on Databricks compute and surfaces in Catalog Explorer up to **column level** ([lineage docs](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/data-lineage)). Backed by `system.access.column_lineage` and `system.access.table_lineage`.

### What it captures well

- SQL queries, notebook SQL cells, Spark DataFrame ops with native functions, DLT/Lakeflow pipelines, dbt-on-Databricks runs
- Reads/writes through Spark on UC-enabled compute

### What it misses (in practice)

- **Python UDFs and Scala UDFs** — "obscure the mapping between source and target columns." The mapping is captured as a coarse table-to-table edge, not column-level.
- **Pandas / non-Spark Python** that reads via direct file API misses lineage entirely.
- **External jobs** — anything that pulls a Delta table over Delta Sharing or a JDBC reader from outside doesn't record lineage on the UC side.
- **BI tools** — Power BI / Tableau queries are recorded as "BI tool reads" but the downstream report graph is opaque to UC. [Microsoft Q&A confirms](https://learn.microsoft.com/en-us/answers/questions/5773525/end-to-end-lineage-not-visible-between-azure-datab) Purview cannot stitch end-to-end Databricks→Power BI lineage today.
- **Cross-metastore / cross-region** lineage is hard-broken: ["Lineage graphs are created at the metastore level, and do not cross region or platform boundaries"](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/best-practices).
- **30/90-day windows** in the UI; the system tables go further but the pretty graph clips.

### How teams supplement

- Pipe `system.access.*` to a side store (Snowflake or another Delta), build column-lineage stitching for UDFs by parsing notebook AST
- Accept that Power BI lineage lives in Purview/Fabric and federate manually
- Use OpenLineage + DataHub or Marquez for an end-to-end view (Module 24)

---

## Multi-workspace patterns

Three real-world buckets:

- **One workspace** (rare past 50 users) — fast to set up, becomes a noisy-neighbor blob. Cost attribution and security blast radius both suffer.
- **3–10 workspaces** (most common) — typical layout: `dev`, `stage`, `prod_general`, `prod_phi`, `analytics`, `ml`, `shared_services`. Each bound to specific catalogs.
- **100+ workspaces** (large enterprises, hub-and-spoke per business line) — each business line owns its own workspace with bound prod catalog; a shared `governance` workspace owns the metastore admin role and runs UCX/audit/policy jobs.

Account-level identity federation makes this tractable in 2026: one Entra group → account console → assigned to whichever workspaces apply.

**Practical tip:** the metastore-admin role is **powerful** — on Azure it's a workspace-local admin in one designated workspace, by design. **Treat that workspace like a tier-0 admin host:** locked-down, MFA, conditional access, no notebooks for general work. Module 17 covers the admin playbook.

---

## Production reality

### The catalog-naming decisions you can't reverse cheaply

Catalog names are sticky. You can rename a catalog, but every downstream reference (notebooks, dbt projects, Power BI semantic models, MLflow run IDs) breaks. Pick names that age well — avoid version numbers (`prod_v2_claims`), avoid project codenames that change, avoid anything tied to a specific team org chart.

A pattern that ages well: **`<env>_<phi-class>_<domain>`** (`prod_phi_claims`, `prod_deid_claims`, `dev_deid_member`).

### The "I migrated to UC but my dashboards broke" story

Discussed in Module 10 (next). Briefly: dashboards reference tables by their three-part name (`hive_metastore.default.claims` becomes `prod_catalog.silver.claim_line`). Without rewriting every dashboard, dbt model, and notebook, the dashboards break.

### The "metastore admin is the most powerful role in your org" reality

A metastore admin can grant themselves access to any catalog, read any table, modify any policy. **Treat metastore admin like a tier-0 production credential** — short list (3–5 people), require MFA + conditional access, audit every action, rotate annually.

---

## When NOT to use UC features

- **Workspace-level groups for GRANTs** — UC requires account-level. Migrate.
- **Column-mapping mode without testing readers** — older Delta readers can't open column-mapped tables.
- **ABAC for purpose-based access** — Public Preview only covers tables/MVs/streaming tables; volumes, functions, model serving aren't yet supported.
- **Lineage as the audit trail** — it's an engineering tool; for HIPAA audit, use `system.access.audit` forwarded to immutable storage.

---

## Sanity check

1. What does workspace-catalog binding *actually do*, and why is it the load-bearing primitive for PHI/non-PHI isolation?
2. What's the Azure RBAC bypass risk with UC, and how do you close it?
3. What three permissions systems coexist in a Databricks workspace, and what's the debugging order when a user says "I can't read X"?
4. ABAC is in Public Preview as of April 2026. What does it cover, and what's NOT yet covered?
5. Why is `User Access Administrator` on the storage account the gotcha for creating a UC storage credential?
6. Lineage doesn't work for what four classes of operation? How do teams supplement?
7. The metastore-admin role: what makes it tier-0 and what's the operational discipline?

---

## Further reading

- [Unity Catalog overview — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/)
- [Best practices — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/best-practices)
- [Manage privileges](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/manage-privileges/)
- [ABAC — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/abac/)
- [Workspace-catalog binding](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/access-control/workspace-catalog-binding)
- [Row filters / column masks](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/filters-and-masks/)
- [Azure managed identities for UC](https://learn.microsoft.com/en-us/azure/databricks/connect/unity-catalog/cloud-storage/azure-managed-identities)
- [Automatic Identity Management for Entra](https://learn.microsoft.com/en-us/azure/databricks/admin/users-groups/automatic-identity-management/)
- [Identity best practices](https://learn.microsoft.com/en-us/azure/databricks/admin/users-groups/best-practices)
- [Daniel Beach — Migrating to Databricks](https://www.confessionsofadataguy.com/migrating-to-databricks-a-guide/)
- [Karlo Kotarac — UC migration lessons](https://medium.com/valcon-consulting/unity-catalog-migration-best-practices-lessons-learned-from-two-implementations-part-1-f692811643a6)
