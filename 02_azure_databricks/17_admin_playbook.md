# Module 17 — Admin Playbook: Accounts, Workspaces, Identity, Audit

> **Goal of this module:** the day-2 operations playbook for a Databricks workspace administrator at a healthcare-scale org. The role hierarchy, real cluster-policy JSON, identity ops, init script lifecycle, audit log pipeline, daily/weekly/monthly cadence, on-call patterns, compliance review.
>
> **The "how to administer Databricks properly" answer.**

---

## The role hierarchy — five distinct administrative roles

Don't collapse these into "admin." Each has a different scope and a different blast radius:

| Role | Scope | Cannot do |
|---|---|---|
| **Account admin** | Account console — billing, identity (account-level SCIM), workspaces, NCCs, metastore admin assignment | Doesn't automatically have data access in workspaces |
| **Metastore admin** | UC metastore — catalogs, ABAC policies, governed tags, system table access | Cannot create workspaces or manage Azure resources |
| **Workspace admin** | One workspace — clusters, jobs, ACLs, instance pools, cluster policies | Cannot grant UC catalog access (separate role); cannot reach other workspaces |
| **Catalog owner** | A single UC catalog — grants on schemas/tables in that catalog | Cannot create catalogs or modify ABAC policies (unless also metastore admin) |
| **Cluster policy admin** | Cluster policy permissions only | Cannot manage clusters directly |

### Healthcare separation pattern

Don't have one person hold all five roles. Reasonable separation:

- **Account admins** — 3 named individuals, MFA + conditional access, audit every action
- **Metastore admin** — 1 dedicated tier-0 service account + 2 named individuals (break-glass)
- **Workspace admins** — per-workspace, 2-3 individuals each
- **Catalog owners** — assigned to data-product teams; team-scoped
- **Cluster policy admins** — platform team

**The break-glass account** — an emergency-only account admin used during outage. Locked down; access requires C-level approval; every login alerts the security team. Module 21 covers the audit checklist.

### The Account Console vs Workspace Admin Console

**Account Console** (`accounts.azuredatabricks.net`): account-wide governance — workspaces, identity, billing, network configs, metastore admin assignment.

**Workspace Admin Console** (per-workspace): workspace-scoped — cluster policies, instance pools, ACLs, integrations.

**Different surfaces, different roles.** A workspace admin doesn't have access to the account console; they're orthogonal.

---

## Cluster policies — the central admin lever

Module 2 covered cluster policies as a *concept*; this is the operational artifact. **One policy per persona**, not per team. Personas are stable; teams come and go.

### Real production policy templates

#### 1. Analyst — interactive, smallish, hard auto-term, PHI-safe

```json
{
  "spark_version": {
    "type": "regex", 
    "pattern": "^17\\.[0-9]+\\.x-scala2\\.13$"
  },
  "node_type_id": {
    "type": "allowlist",
    "values": ["Standard_DS4_v5", "Standard_DS5_v5", "Standard_E8ds_v5"]
  },
  "data_security_mode": {"type": "fixed", "value": "USER_ISOLATION"},
  "autotermination_minutes": {
    "type": "range", "minValue": 10, "maxValue": 60, "defaultValue": 30
  },
  "num_workers": {"type": "range", "maxValue": 8},
  "custom_tags.cost_center": {
    "type": "regex", "pattern": "^cc-[0-9]{6}$"
  },
  "custom_tags.business_unit": {
    "type": "allowlist", 
    "values": ["claims", "member", "provider", "rx", "stars", "actuarial"]
  },
  "custom_tags.data_classification": {
    "type": "allowlist", "values": ["non-phi", "deid"]
  },
  "init_scripts.0.volumes.destination": {
    "type": "fixed", 
    "value": "/Volumes/_admin/init/analyst_v3.sh"
  }
}
```

Note: `data_classification` allowlist excludes `phi` — analysts don't get PHI-tagged clusters by this policy. PHI access requires the next persona.

#### 2. ML Engineer — GPU allowed, longer runtime, Spot for cost

```json
{
  "spark_version": {
    "type": "regex",
    "pattern": "^17\\.[0-9]+\\.x-(gpu-)?ml-scala2\\.13$"
  },
  "node_type_id": {
    "type": "allowlist",
    "values": [
      "Standard_DS5_v5", "Standard_E8ds_v5",
      "Standard_NC24ads_A100_v4", "Standard_ND96isr_H100_v5"
    ]
  },
  "data_security_mode": {
    "type": "allowlist", "values": ["SINGLE_USER", "USER_ISOLATION"]
  },
  "autotermination_minutes": {
    "type": "range", "minValue": 30, "maxValue": 240, "defaultValue": 120
  },
  "num_workers": {"type": "range", "maxValue": 32},
  "azure_attributes.availability": {
    "type": "fixed", "value": "SPOT_WITH_FALLBACK_AZURE"
  },
  "azure_attributes.first_on_demand": {"type": "fixed", "value": 1},
  "azure_attributes.spot_bid_max_price": {"type": "fixed", "value": -1},
  "custom_tags.cost_center": {
    "type": "regex", "pattern": "^cc-[0-9]{6}$"
  },
  "custom_tags.workload": {"type": "fixed", "value": "ml"},
  "custom_tags.data_classification": {
    "type": "allowlist", "values": ["non-phi", "deid", "phi"]
  }
}
```

#### 3. Job (production, no humans) — narrow, Photon-default, Jobs Compute

```json
{
  "cluster_type": {"type": "fixed", "value": "job"},
  "spark_version": {
    "type": "regex", "pattern": "^17\\.[0-9]+\\.x-scala2\\.13$"
  },
  "node_type_id": {
    "type": "allowlist",
    "values": [
      "Standard_DS4_v5", "Standard_DS5_v5",
      "Standard_E8ds_v5", "Standard_E16ds_v5"
    ]
  },
  "data_security_mode": {"type": "fixed", "value": "SINGLE_USER"},
  "runtime_engine": {"type": "fixed", "value": "PHOTON"},
  "azure_attributes.availability": {
    "type": "fixed", "value": "SPOT_WITH_FALLBACK_AZURE"
  },
  "azure_attributes.first_on_demand": {"type": "fixed", "value": 1},
  "num_workers": {"type": "range", "maxValue": 50},
  "custom_tags.cost_center": {
    "type": "regex", "pattern": "^cc-[0-9]{6}$"
  },
  "custom_tags.workload": {"type": "fixed", "value": "etl"},
  "custom_tags.data_classification": {
    "type": "allowlist", "values": ["non-phi", "deid", "phi"]
  }
}
```

#### 4. Platform Admin / Break-Glass — broad, audited, ticket-required

```json
{
  "spark_version": {"type": "unlimited"},
  "node_type_id": {"type": "unlimited"},
  "data_security_mode": {
    "type": "allowlist", "values": ["SINGLE_USER", "USER_ISOLATION"]
  },
  "autotermination_minutes": {
    "type": "range", "minValue": 5, "maxValue": 120, "defaultValue": 60
  },
  "num_workers": {"type": "range", "maxValue": 100},
  "custom_tags.cost_center": {
    "type": "fixed", "value": "cc-platform-admin"
  },
  "custom_tags.purpose": {
    "type": "regex",
    "pattern": "^break-glass-(incident|investigation|maintenance)-[A-Z]+-[0-9]{4}-[0-9]{2}-[0-9]{2}$"
  }
}
```

The `purpose` regex forces every cluster to carry an incident ticket reference, which lands in `system.access.audit` for compliance review. **Permission to use this policy is granted to the on-call SRE group only and audited monthly.**

### Tag enforcement — the chargeback foundation

Module 16 covered why this matters. The discipline:
- **Mandatory tags** at policy level: `cost_center`, `business_unit`, `data_classification`
- **Regex-validated `cost_center`** — prevents free-text drift
- **Allowlist-validated `business_unit` and `data_classification`** — bounds the dimension

Without policy-enforced tags, chargeback is a months-long FinOps cleanup before it's credible.

---

## Serverless usage policies — separate world

Cluster policies don't apply to serverless. **Serverless Budget Policies** ([Revefi guide](https://www.revefi.com/blog/databricks-serverless-budget-policies-2026)) enforce tags on serverless workloads. Per-team / per-project budget policy patterns are the equivalent of cluster policies for the serverless side.

**The discipline:** maintain mirror policies for cluster + serverless so the same persona's tag set applies regardless of compute path.

---

## Instance pools

Pre-warmed VM pools; clusters claim from the pool. Reduces cluster startup from 3–7 min to ~30 sec.

**When pools save money:**
- Frequent ephemeral cluster creation (CI integration jobs, ad-hoc analyst sessions)
- The idle-VM cost of the pool is offset by faster startup × frequency

**When pools waste money:**
- Low-frequency clusters
- A pool with 4 idle VMs at $0.40/hr each that gets one cluster spin-up per day burns $35/day for ~5 minutes saved

**Tag inheritance gotcha:** **cluster tags override pool tags on billing rows.** If a cluster forgets a `cost_center` tag, the pool's tag does *not* automatically backfill. Enforce both at policy level.

---

## Identity operations

### Account-level SCIM (mandatory in 2026)

UC requires account-level identities. Workspace-level SCIM is being deprecated.

### Automatic Identity Management for Entra ID (Public Preview 2026)

Replaces SCIM connector. Users, groups, SPs flow from Entra ID into the Databricks account console without a separate sync app ([AIM docs](https://learn.microsoft.com/en-us/azure/databricks/admin/users-groups/automatic-identity-management/)). The 2026 default for Azure-shop deployments.

### Service principal lifecycle

- **Creation** — provision via Terraform or account API; never click-ops in production
- **Rotation** — token rotation on schedule (e.g., quarterly); use Workload Identity Federation where possible to eliminate tokens
- **Retirement** — when a service is decommissioned, the SP must be retired; document the SP-to-service mapping in the platform inventory

### Conditional Access policies

Apply at the Entra layer:
- **MFA required** for all admin roles
- **Compliant device required** for production workspace access
- **Geographic restrictions** if applicable
- **Session timeout** — short for admin sessions

### Workload Identity Federation (the no-PAT pattern)

Databricks supports OIDC federation for CI/CD. **GitHub Actions / Azure DevOps pipelines authenticate to Databricks without long-lived PATs.** The 2025+ recommended CI/CD auth pattern; Module 19 has the details.

### Group-naming convention at scale

`<role>-<domain>-<access-level>`:
- `dataeng-claims-writers`
- `analyst-member-readers`
- `oncall-platform-admins`
- `clinicians-phi-readers`

Predictable naming makes GRANT statements grep-able and chargeback intuitive.

---

## Init script lifecycle

(Module 2 covered the deprecation history; this is the operational discipline.)

### UC Volumes pattern with version pinning

```bash
# Path: /Volumes/_admin/init/analyst_v3.sh
# Reference in cluster policy as:
# "init_scripts.0.volumes.destination": 
#   {"type": "fixed", "value": "/Volumes/_admin/init/analyst_v3.sh"}
```

The `_v<n>` suffix enables rollforward without overwriting in place:
- Version 4 ready: write `analyst_v4.sh`, update cluster policy to reference it, bounce clusters as they cycle
- v4 turns out bad: flip policy back to `analyst_v3.sh`, bounce again
- Old version stays available for rollback

**Never edit init scripts in place.** The wave of cluster restarts touching the bad version is hard to undo.

### Common init script use cases

- **Corp CA cert install** — for outbound TLS from cluster nodes
- **Library install for offline workspaces** — pip from internal mirror
- **Monitoring agent install** — Datadog, Splunk forwarder, custom OTEL collectors
- **Custom `LD_LIBRARY_PATH`** — for proprietary libs not on PyPI

### Don't-do list

- Don't put secrets in init scripts (use cluster-scoped secrets instead)
- Don't make init scripts depend on internet access if your workspace is network-restricted
- Don't store init scripts in DBFS (deprecated)
- Don't have init scripts run for >2 minutes (triggers cluster startup timeouts)

---

## System tables — the FinOps + audit pipeline backbone

The full list of `system.*` schemas:
- `system.billing` — usage, list_prices, budgets
- `system.access` — audit, table_lineage, column_lineage, outbound_share_events
- `system.compute` — clusters, cluster_events, warehouses, instance_pools
- `system.lakeflow` — pipelines, runs
- `system.marketplace` — listings, transactions
- `system.query` — history (DBSQL)
- `system.serving` — endpoints, requests, costs

### Enabling system tables

Account-admin gate. Enable per-schema via REST API:

```bash
databricks api post /api/2.0/unity-catalog/metastores/<id>/systemschemas/<schema> \
  --json '{"enabled": true}'
```

### The standard chargeback pattern

(Module 16 has the full SQL.)

### Materializing system table views into a `_admin` catalog

System table queries can be slow at scale; materialize daily snapshots into your own `_admin` catalog for dashboard performance:

```sql
CREATE OR REPLACE TABLE _admin.billing.usage_daily AS
SELECT * FROM system.billing.usage 
WHERE usage_date >= current_date - INTERVAL 90 DAYS;

-- schedule a refresh job nightly
```

For HIPAA: the long-retention compliance copy of audit logs lives in `_compliance` catalog with 6-year retention (see audit pipeline below).

### The standard "admin dashboard" every workspace should have

Lakeview dashboard with these tiles:
1. **30-day cost trend** by SKU (from `system.billing.usage`)
2. **Top 20 cost concentrators** (jobs, warehouses, endpoints)
3. **Idle cluster check** — clusters with no activity in 7 days
4. **Library inventory** — installed libraries per cluster, for CVE sweep
5. **Audit anomaly check** — unusual access patterns in last 24hrs

---

## Audit log pipeline (the HIPAA-grade version)

`system.access.audit` schema (Module 4 from research file 04 covered this):
- `event_time`, `user_identity`, `service_name`, `action_name`, `request_params` (a map), `response`, `source_ip_address`, `user_agent`, `audit_level`, `identity_metadata`

### Two retention layers

**Layer 1 — Long-retention Delta sink (6-year HIPAA compliance):**

```python
# DLT pipeline: system.access.audit → _compliance.audit.events
import dlt
from pyspark.sql.functions import current_timestamp

@dlt.table(
    name="audit_events",
    table_properties={
        "phi_class": "high",  # request_params CAN contain PHI
        "data_classification": "phi",
        "retention_years": "6",
        "delta.enableDeletionVectors": "false",  # immutable
    }
)
def audit_events():
    return (
        dlt.read_stream("system.access.audit")
        .withColumn("ingestion_ts", current_timestamp())
    )
```

The destination table:
- Lives in `_compliance` catalog
- Bound to a tier-0 governance workspace only
- Has 6-year retention via Azure Storage immutability + Delta retention
- Has PHI-redaction UDF applied to `request_params` before SIEM forwarding (don't redact in the compliance copy — keep the full record)

**Layer 2 — SIEM forwarding (real-time alerting):**

Configure Azure Monitor diagnostic settings → Event Hub → Splunk/Sentinel.

### Must-have alerting rules

1. **PHI grants** — any `GRANT` on a `prod_phi_*` catalog by a non-`metastore-admin` principal
2. **Failed login bursts** — >10 failed logins per user per minute
3. **Unrestricted-cluster creation** — cluster creation without a recognized policy
4. **`DOWNLOAD_QUERY_RESULT` from non-allowlisted users** — downloading PHI to local
5. **Admin-group changes** — any modification to `oncall-platform-admins` or other tier-0 groups

### PHI-in-audit-logs reality

`request_params` can contain PHI (literal SQL values like `WHERE member_id = '12345678'` get logged). **Audit logs themselves are PHI.**

Options:
1. **Tokenizing forwarder** — strip MRN-shaped values before SIEM
2. **Separate locked-down SIEM index** with the same controls as the source workspace
3. **Don't forward `request_params`** to non-PHI SIEM destinations

For Optum-grade healthcare: option 2 (locked SIEM index) is most common.

---

## DBR upgrade planning

The single most disruptive recurring admin event.

### Cadence

- **LTS releases** — every ~12-18 months. 2026 standard: DBR 17.3 LTS (Spark 4.0).
- **Non-LTS quarterly** — feature releases for early adopters

### The breaking-change-review process

For each release:
1. Read the release notes for breaking changes (Spark version bumps, Scala version, library defaults)
2. **Spark 4 / Scala 2.13 / `input_file_name` removal** in 17.x are real breaking changes — code that depended on legacy APIs breaks
3. Identify dependent jobs and notebooks via UCX-like tools or static analysis
4. Test on staging clusters with the new DBR
5. Coordinate the team-wide DBR upgrade (Module 5 covered the `databricks-connect` version coupling pain)

### Per-cluster vs per-job upgrade strategy

- **Job clusters** — upgrade by changing the bundle definition; staged rollout per job
- **All-purpose clusters** — coordinate with users; bounce off-hours
- **DLT/Lakeflow pipelines** — upgrade per-pipeline; CDC checkpoint state needs validation

### Rollback procedure

If a DBR upgrade breaks production:
1. Roll back the cluster policy to the previous DBR LTS
2. Bounce affected clusters
3. Investigate the breaking change; file a ticket for the next attempt

**Never roll forward through a broken DBR.** Roll back, fix, retry.

---

## Workspace lifecycle runbooks

### Create a new workspace (Terraform)

```hcl
resource "azurerm_databricks_workspace" "phi_east" {
  name                = "ws-phi-east-001"
  resource_group_name = azurerm_resource_group.databricks.name
  location            = "eastus2"
  sku                 = "premium"  # mandatory for HIPAA features
  
  custom_parameters {
    no_public_ip                = true  # SCC
    virtual_network_id           = azurerm_virtual_network.workspace.id
    public_subnet_name           = "ws-public-subnet"
    private_subnet_name          = "ws-private-subnet"
    public_subnet_network_security_group_association_id = azurerm_subnet_network_security_group_association.public.id
    private_subnet_network_security_group_association_id = azurerm_subnet_network_security_group_association.private.id
    require_default_storage_account_firewall = true
  }
  
  managed_services_cmk_key_vault_key_id = azurerm_key_vault_key.managed_services.id
  managed_disk_cmk_key_vault_key_id     = azurerm_key_vault_key.managed_disk.id
}

resource "databricks_workspace_compliance_security_profile" "phi_east_csp" {
  workspace_id          = azurerm_databricks_workspace.phi_east.workspace_id
  is_enabled            = true
  compliance_standards  = ["HIPAA"]  # PERMANENT — cannot be undone
}
```

(Module 20 has the full networking detail; Module 21 has the HIPAA detail.)

**Critical:** CSP=HIPAA is **permanent.** Test workspaces should NOT have CSP enabled, or you'll mark them as having processed regulated data.

### Decommission a workspace

10-step runbook:
1. Confirm no active jobs / streaming pipelines
2. Export notebooks and dashboards to source control
3. Migrate UC catalogs (or accept they're per-region; nothing to migrate)
4. Archive audit logs to `_compliance` catalog
5. Unbind workspace from any UC catalogs
6. Disable workspace assignments in account console (groups detach)
7. Run final cost report (closeout for finance)
8. Schedule workspace deletion (some metadata retains for audit)
9. Remove from Terraform state; delete via Azure portal or `terraform destroy`
10. Document the decommission ticket; close out

### Break-glass admin recovery

If all account admins are locked out:
1. Microsoft / Databricks support has an emergency-recovery procedure
2. Requires C-level signoff and identity verification
3. **Document the procedure in your IRP** — a 4am incident is the wrong time to discover the process

---

## Daily / weekly / monthly admin cadence

### Daily

- **Cost dashboard delta** — yesterday's DBU spend vs 7-day average
- **Failed jobs review** — what failed overnight; classify ETL, ML, system
- **Security alert triage** — Splunk/Sentinel alerts from the audit pipeline

### Weekly

- **DBU spend by team** — chargeback dashboard delta
- **Top-cost-jobs review** — anything new in the top 20?
- **Idle-cluster cleanup** — anyone forget to terminate?
- **PR backlog on shared infra** — unblock platform PRs

### Monthly

- **Group membership audit** — verify production groups match Entra source of truth
- **Library inventory + CVE sweep** — what's installed, what has vulnerabilities
- **DBR upgrade planning** — track LTS lifecycle, plan next quarter's upgrade
- **Capacity review** — NCC limits, region capacity, workspace counts
- **DR drill schedule** — tabletop exercises

### Quarterly

- **Tabletop DR exercise** — full simulation of region failure
- **Compliance review** — CSP, CMK, audit pipeline, network controls (Module 21 checklist)
- **Commitment (DBCU) right-sizing** — review against actual usage; plan renewal

---

## On-call patterns

### Common pages

- **Cluster won't start** — Azure VM provisioning, init script flake, Spot capacity
- **Job stuck** — upstream dependency, schema-change-stuck Lakeflow pipeline (Module 4)
- **User can't access UC object** — three-permission collision (Module 9)
- **SQL warehouse down** — Azure region issue, capacity, IWM misconfiguration
- **Audit log forwarding broken** — Event Hub or SIEM-side issue
- **FMAPI quota** — token-rate limit hit; check pay-per-token vs PT

### Triage trees

For each common page, document the triage tree. Example for "user can't access UC object":

```
1. Check if user has account-level SCIM membership in the relevant group
   → if no: SCIM sync issue or group membership not propagated; fix Entra side
2. Check if the relevant group has USE CATALOG + SELECT on the target
   → if no: GRANT missing; coordinate with catalog owner
3. Check if the workspace is bound to the catalog (workspace-catalog binding)
   → if no: this is intentional isolation; user needs to use the bound workspace
4. Check for legacy workspace-level ACL denies
   → rare but happens in mid-migration scenarios
5. For external tables: check the storage credential's permissions on ADLS
```

### When to engage Databricks support

- **P1** — production outage, no workaround. Engage immediately.
- **P2** — degraded production, workaround exists. Within business hours.
- **P3** — non-production or planning question. Standard response.

For Optum-grade healthcare: have a documented Solutions Architect contact at Databricks for fast escalation.

---

## Compliance review checklist (quarterly)

For each HIPAA workspace, verify:

1. ☐ Compliance Security Profile = enabled with HIPAA standard
2. ☐ Premium tier
3. ☐ Enhanced Security and Compliance add-on purchased
4. ☐ VNet injection enabled
5. ☐ Secure Cluster Connectivity enabled (no public IP)
6. ☐ Front-end + back-end Private Link operational
7. ☐ Workspace storage account firewall enabled with `dfs` and `blob` PEs
8. ☐ Three-tier CMK (managed services + DBFS + managed disks via Key Vault HSM)
9. ☐ Workspace-catalog binding for PHI catalogs
10. ☐ ABAC governed tags + row filters + column masks for PHI
11. ☐ Audit log forwarding to SIEM with 6-year retention
12. ☐ Naming standards lint in CI (PHI not in workspace/cluster/job/tag names)
13. ☐ DBR ≥ 17.3 LTS (or current supported LTS)
14. ☐ All preview features used by the workspace are on the HIPAA-allowed list

(Module 21 has the deeper HIPAA treatment.)

---

## Sanity check

1. Name the five distinct admin roles and what each cannot do.
2. Walk through the four canonical cluster policy personas and what each restricts.
3. Why is `_v<n>` suffix versioning on init scripts the discipline that survives production?
4. The audit log pipeline has two retention layers. What are they, and which one handles the HIPAA 6-year requirement?
5. The break-glass cluster policy has a `purpose` regex. What does it enforce, and why does it matter?
6. Describe the daily / weekly / monthly admin cadence in one sentence each.
7. The compliance review checklist has 14 items. Which two would you check first if you suspected a misconfiguration?

---

## Further reading

- [Databricks admin overview — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/admin/)
- [Cluster policies reference](https://learn.microsoft.com/en-us/azure/databricks/admin/clusters/policies)
- [Identity best practices](https://learn.microsoft.com/en-us/azure/databricks/admin/users-groups/best-practices)
- [Automatic Identity Management for Entra ID](https://learn.microsoft.com/en-us/azure/databricks/admin/users-groups/automatic-identity-management/)
- [System tables overview](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/)
- [Audit logs system table](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/audit-logs)
- [Compliance security profile](https://learn.microsoft.com/en-us/azure/databricks/security/privacy/security-profile)
- [Init scripts migration guidance](https://kb.databricks.com/clusters/migration-guidance-for-init-scripts-on-dbfs)
- [Disaster recovery](https://learn.microsoft.com/en-us/azure/databricks/admin/disaster-recovery)
- [databricks-industry-solutions/cluster-policy](https://github.com/databricks-industry-solutions/cluster-policy)
- [terraform-databricks-modules](https://github.com/databricks/terraform-databricks-modules)
- [Revefi — Serverless Budget Policies 2026](https://www.revefi.com/blog/databricks-serverless-budget-policies-2026)
