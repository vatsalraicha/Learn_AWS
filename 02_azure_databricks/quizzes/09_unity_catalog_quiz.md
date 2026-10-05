# Quiz — Module 9: Unity Catalog Deep

## Recall

**Q1.** What is UC's three-level namespace, and how does the metastore relate to it?

<details><summary>Answer</summary>

**`catalog.schema.object`** — replaces `database.table` of `hive_metastore`. Catalogs are securable; schemas inherit from catalogs; tables, views, materialized views, streaming tables, volumes, functions, models, and metric views all sit at the third level.

**The metastore** is the regional container for catalogs — **one UC metastore per cloud region per Databricks account.** All catalogs in a region share that single metastore. Lineage and permissions don't cross metastore boundaries.
</details>

**Q2.** What does workspace-catalog binding do, and how does it interact with regular GRANTs?

<details><summary>Answer</summary>

Workspace-catalog binding restricts which workspaces can access a catalog. **It supersedes user-level grants.** Even if a user has SELECT on a catalog, they cannot read from a non-bound workspace.

For healthcare PHI/analytics isolation, this is the **load-bearing primitive** — it makes "PHI workspace" a hard isolation boundary, not just a grant pattern. Even if ABAC policies fail or a grant is overly permissive, workspace binding acts as a second-layer veto.

```sql
ALTER CATALOG prod_phi_claims 
  SET WORKSPACE BINDING (WORKSPACES = ['ws-phi-001', 'ws-phi-002'])
  ISOLATED;
```
</details>

**Q3.** What are the three permission systems that coexist in a Databricks workspace, and what's the debugging order when a user says "I can't read X"?

<details><summary>Answer</summary>

Three systems:
1. **Workspace-level ACLs** (legacy; cluster ACLs, job ACLs, notebook ACLs at workspace scope)
2. **Unity Catalog grants** (account-level on securables: catalog, schema, table, view, volume, function, model)
3. **Workspace-catalog bindings** (override individual UC grants)

**Debugging order when access fails:**
1. Is **`USE CATALOG`** granted? (separate from SELECT)
2. Is **SELECT** granted on the table (or inheritable from schema/catalog)?
3. Is the **workspace bound** to the catalog (if isolation is on)?
4. Is there a **workspace-level deny** lurking from the legacy ACL system?
5. For external tables: does the user have access to the **storage credential / external location**?
</details>

---

## Apply

**Q4.** Set up a UC storage credential and external location for a healthcare PHI ADLS container, with managed identity (not service principal) and the right permissions.

<details><summary>Answer</summary>

```sql
-- 1. Account admin creates the storage credential backed by an Azure Managed Identity
-- (the MI must have Storage Blob Data Contributor on the ADLS account)
CREATE STORAGE CREDENTIAL prod_phi_credential
  WITH (AZURE_MANAGED_IDENTITY = '/subscriptions/<sub-id>/resourceGroups/optum-uc-prod/providers/Microsoft.ManagedIdentity/userAssignedIdentities/uc-mi-phi-prod')
  COMMENT 'Production PHI UC storage credential';

-- Grant the storage credential to a metastore admin or specific catalog admins
GRANT CREATE EXTERNAL LOCATION ON STORAGE CREDENTIAL prod_phi_credential 
  TO `metastore-admins-group`;

-- 2. Create the external location bound to that credential
CREATE EXTERNAL LOCATION prod_phi_claims_root
  URL 'abfss://phi-claims@optumphiprod.dfs.core.windows.net/'
  WITH (CREDENTIAL prod_phi_credential)
  COMMENT 'Root path for prod_phi_claims catalog';

GRANT CREATE TABLE, CREATE VOLUME ON EXTERNAL LOCATION prod_phi_claims_root 
  TO `dataeng-claims-writers`;

-- 3. Create the catalog using the external location for managed-table storage
CREATE CATALOG prod_phi_claims
  MANAGED LOCATION 'abfss://phi-claims@optumphiprod.dfs.core.windows.net/'
  COMMENT 'Production PHI claims catalog — bound to PHI workspaces only';

-- 4. Workspace-bind the catalog (the hard isolation primitive)
ALTER CATALOG prod_phi_claims
  SET WORKSPACE BINDING (WORKSPACES = ['ws-phi-east-001', 'ws-phi-central-002'])
  ISOLATED;
```

**Critical Azure-side prerequisite (the gotcha):** the principal creating the storage credential needs **`User Access Administrator`** on the ADLS storage account (not just Owner) — to delegate `Storage Blob Data Contributor` to the managed identity.

**The Azure RBAC bypass risk** — to close it, **only `uc-mi-phi-prod`** should have data-plane RBAC on the storage account. No human `Storage Blob Data Reader` grants. UC governance is bypassed if anyone can read the bytes directly.
</details>

---

## Diagnose

**Q5.** A user complains they can `SELECT * FROM prod_phi_claims.silver.claim_line` from one workspace but not from another. They have the same group memberships in both. What's likely happening, and how would you confirm?

<details><summary>Answer</summary>

**Most likely cause:** workspace-catalog binding. The catalog `prod_phi_claims` is bound to a specific set of workspaces (probably the dedicated PHI workspaces), and the second workspace where the user is trying to query isn't in the binding list.

**How to confirm:**
```sql
-- From either workspace, check the binding
SHOW WORKSPACES IN CATALOG prod_phi_claims;
```

If the second workspace ID isn't in the result, that's the cause.

**The architect's lens:** this is **working as intended** for healthcare. The user wants PHI data; you've intentionally restricted PHI to specific workspaces. The fix isn't to widen the binding — it's to either:
1. Have the user do PHI-touching work from the bound PHI workspace
2. Provide a de-identified version of the data in `prod_deid_claims` accessible from the broader analytics workspace
3. If there's a legitimate business need to widen, follow the change-control process for adding the workspace to the binding (with security review)

**Don't bypass the binding casually.** Workspace-catalog binding is the load-bearing isolation primitive — every "let me just add this workspace" request weakens it.

**Document this in the runbook** so the user-facing message ("you need to use the PHI workspace for this work") is explicit and not surprising.
</details>

---

## Defend

**Q6.** A peer says "we should disable ABAC and stick with row filters and column masks — they're more mature." Defend or refute.

<details><summary>Answer</summary>

**Refute, with calibration.**

Where the peer is right:
- **ABAC is Public Preview** as of April 2026. Some features may shift before GA.
- **Row filters and column masks have been GA longer** — more battle-tested.
- **ABAC doesn't yet cover all securables** — model serving endpoints, volumes, functions are not in scope for ABAC policies (only tables, materialized views, streaming tables).

Where the peer is wrong (which is the bigger picture):
- **Row filters and column masks don't scale.** At an Optum-grade healthcare org with hundreds of PHI-bearing tables, you'd need hundreds of `CREATE FUNCTION` definitions and `ALTER TABLE` calls. Maintaining them as the schema evolves is a multi-FTE job.
- **ABAC's value is exactly the scaling problem.** Tag once at ingest (`phi_class = high`), define one policy at the catalog level, and it applies to every current and future table. New tables that get tagged correctly inherit the policy automatically. The maintenance overhead drops by 100×.
- **The audit trail with ABAC is cleaner** — `system.access.audit` shows policy applications uniformly across all tagged objects.

**The architect's pragmatic call:**
- **Use ABAC for the common case** — column masks based on PHI class, row filters based on payer assignment.
- **Use row filters / column masks for ABAC's not-yet-covered surfaces** — model serving (until ABAC catches up), purpose-based access, complex multi-condition policies.
- **Use Immuta or Privacera** for purpose-based access (HIPAA Minimum Necessary) until ABAC matures.

**Production discipline:**
- Adopt ABAC on greenfield catalogs as Public Preview matures
- Migrate row filters / column masks to ABAC where the use case fits
- Layer Immuta on top for the cases neither covers
- Track ABAC GA — it's the strategic direction; row filters / column masks are the legacy bridge

**Source:** [ABAC docs](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/abac/), [Immuta UC integration](https://www.immuta.com/blog/scaling-secure-data-access-with-immuta-databricks-unity-catalog/).
</details>

**Q7.** A peer says "we don't need to worry about Azure RBAC because UC governs everything." Defend or refute.

<details><summary>Answer</summary>

**Refute, decisively. This is the most-missed gap in healthcare UC deployments.**

UC's enforcement only applies when access goes *through* UC. **A user with Azure-portal `Storage Blob Data Reader` on the same container can read the raw Parquet directly, bypassing UC row filters and column masks.**

This means:
- Your ABAC policies don't apply
- Your column masks don't apply
- Your row filters don't apply
- Your audit log shows the bytes were read but not by whom (Azure-side audit, not UC audit)

**The fix is non-negotiable for healthcare:**
- **Lock down the storage account** so that **only the UC managed identity** has data-plane RBAC.
- **No `Storage Blob Data Reader`, `Contributor`, or `Owner`** at the data plane for any human user or group on PHI containers.
- **Humans get UC-mediated access only.**

**The audit checklist** (Module 21):
- Quarterly review of `Microsoft.Storage/.../blobServices/containers/` role assignments
- Alert on any new role assignment to a non-UC-MI principal
- Document the policy that human storage-side access is forbidden

**Other Azure RBAC gotchas worth flagging:**
- **Service-principal-based credentials don't work with storage firewalls or private endpoints** — must use managed identities
- **`User Access Administrator`** on the storage account is required to *create* the storage credential (not just Owner)
- **Storage account access keys** must be disabled (otherwise they bypass even the RBAC layer)

**Production discipline:**
- The architect owns this checklist. Don't assume the cloud-IAM team is handling it; their default reflex is "give the team Storage Blob Data Reader for ad-hoc access" — which destroys UC governance.
- Document the UC governance pattern in writing. Make storage-side RBAC for humans a **policy violation**, not just a discouraged pattern.
</details>
