# Module 23 — Disaster Recovery & Multi-Region

> **Goal of this module:** the customer-driven reality of Databricks DR, the three RTO/RPO patterns (backup-restore, active-passive, active-active), what's NOT covered by Databricks-managed DR, and the HIPAA contingency-plan requirement that makes this non-optional for healthcare.

---

## The fundamental fact

> *"Azure Databricks requires a customer-driven approach to disaster recovery."* — [DR docs](https://learn.microsoft.com/en-us/azure/databricks/admin/disaster-recovery)

A Databricks workspace is **regional.** The control plane is regional. The Unity Catalog metastore is regional and singleton. **DR is the customer's responsibility** — Databricks doesn't auto-fail-over your workspace cross-region.

For an Optum-grade healthcare org with paired-region RTO/RPO requirements (HIPAA contingency-plan rule, 45 CFR 164.308(a)(7)), this is a **multi-quarter platform-engineering project**, not a checkbox.

---

## Three DR patterns by RTO/RPO tier

| Pattern | RTO | RPO | Cost | Best for |
|---|---|---|---|---|
| **Backup-and-restore** (single region, restore from ADLS GRS) | hours-to-days | hours | $ | Cheap; not real DR for healthcare |
| **Active-passive** (warm secondary workspace, replicated artifacts, on-demand promote) | 1–4 hours | 15 min – 1 hour | $$ | **Most common for healthcare** |
| **Active-active** (two workspaces serving, traffic split) | minutes | seconds-to-minutes | $$$ | Rare; pricing/operational complexity high |

**For Optum healthcare**: Active-passive is the standard. RTO 1-4 hours typically meets HIPAA contingency requirements.

---

## What you have to replicate (the customer's checklist)

The customer owns **all** of:

1. **Workspace re-provisioning** in DR region (Terraform — Module 19, 20)
2. **UC metastore content replication** — catalogs, schemas, grants. **Not auto-replicated cross-region.** Catalogs/schemas/grants must be re-applied via Terraform or scripted UC API calls in the secondary region.
3. **Cluster policies, instance pools, init scripts** — re-deploy via Terraform / DABs
4. **Job and pipeline definitions** — DABs in a DR target
5. **Notebooks and code** — git is the source of truth; redeploy via DABs
6. **Secrets** — Key Vault GRS or re-create on failover
7. **Network artifacts**: VNets, NSGs, route tables, private endpoints, Private DNS in the DR region
8. **Service principals and SCIM groups** — mostly tenant-global (Entra ID), but workspace assignments must be re-applied
9. **Data** — Delta deep clones or GRS, both with caveats (see below)
10. **Identity-provider integrations** — Entra ID conditional access policies must be present in DR region's user-flow

**For a healthcare org:** HIPAA contingency-plan rule (**45 CFR 164.308(a)(7)**) requires documented data backup, disaster recovery, and emergency-mode operation plans. **The Databricks layer of that plan must be explicit in your IRP** (Incident Response Plan).

---

## Workspace-level replication

### Code is in git, config is in IaC

The discipline:
- **Source code** in git (private repo)
- **Workspace artifacts** (jobs, pipelines, notebooks, dashboards) in Asset Bundles
- **Workspace and account topology** in Terraform
- **No artifact in only-one-place** — if it's not in git or Terraform, it's not part of DR

### UC metastore in DR

Each region has its own UC metastore. **Catalogs/schemas/grants are not auto-replicated.** Your options:

1. **Terraform re-apply** — same Terraform that built primary applies to DR; re-creates catalogs, schemas, grants. Run periodically (nightly?) so DR metastore tracks primary changes.
2. **Scripted UC API calls** — a custom script that reads `system.information_schema.*` and applies via UC API in DR. More fragile than Terraform.
3. **Manual** — only for very stable estates; not Optum-scale.

### Secrets

- **Azure Key Vault GRS** — automatic geo-replication, manual failover. ~15 min RPO typical.
- **Cross-region Key Vault replication** — set up paired KVs; sync secret values via script.
- **Re-create on failover** — for low-secret-count workspaces; manual but simple.

### Service principals / SCIM groups

Entra ID is **global** — SPs and groups exist in your tenant, not per-region. **No replication needed.** What needs replication:
- **Workspace assignments** of those SPs/groups (per-workspace)
- **Conditional Access policies** apply at tenant scope; verify they cover the DR region URLs

---

## Data-layer DR

### Delta Deep Clone

```sql
CREATE TABLE silver.claim_line 
DEEP CLONE silver.claim_line LOCATION 'abfss://dr-data@drstorage.dfs.core.windows.net/silver/claim_line/';
```

Incremental — re-running clones only new files. **Standard cross-region replication primitive.**

**Patterns:**
- **Nightly deep clone** to secondary region; incremental cost
- **Cross-region replication for healthcare BCP** (Business Continuity Planning)

### Delta Sharing for DR

Emerging pattern: share prod tables read-only to DR workspace. Faster cutover; doesn't replicate writes. Useful for read-heavy workloads.

### ADLS GRS / RA-GRS

- **GRS** (Geo-Redundant Storage) — paired region, manual failover, ~15 min RPO typical
- **RA-GRS** (Read-Access GRS) — read access to secondary at any time. **The right default for DR-readable Delta tables.**

### The transaction-log ordering trap

**GRS replicates the Delta files but transaction log ordering across regions is eventually consistent.** After a real failover, you may need:
- `FSCK REPAIR TABLE` — reconciles the log against the actual file inventory
- A fresh checkpoint
- Possibly time-travel restore to a known-good version

**Build this into your runbook.** The first time you discover this is during a real failover is too late.

---

## DR runbook patterns

### Active-passive runbook (healthcare-grade)

```
PRE-FAILOVER (continuous):
  1. Terraform applies to both prod and DR regions
  2. DABs deploys to both prod and DR (DABs target = dr-region)
  3. UC catalog re-creation script runs nightly in DR
  4. Delta Deep Clone of all hot tables runs nightly to DR ADLS
  5. Key Vault GRS for secrets
  6. SIEM forwarding from BOTH regions for audit unification

FAILOVER TRIGGER:
  - Azure region declared down (>X minutes)
  - OR planned failover exercise (quarterly)

DURING FAILOVER:
  1. DNS / traffic failover to DR region (Front Door / Traffic Manager)
  2. UC metastore admin verifies DR metastore is current
  3. Promote DR workspace to "primary" — change client connection strings
  4. Start jobs in DR (DABs already deployed; just trigger schedules)
  5. Verify dashboards work
  6. Communicate to stakeholders

POST-FAILOVER:
  1. Reconcile the transaction log if GRS lag created inconsistency
  2. Document any data loss (RPO actual vs target)
  3. Plan reverse-failover when primary region is restored
  4. Post-mortem within 5 business days

REVERSE-FAILOVER (when primary recovered):
  1. Sync any data changes from DR back to primary
  2. Test primary in shadow mode
  3. Switch traffic back
  4. Decommission temporary DR mode
```

### Quarterly DR drill

- **Tabletop exercise**: walk through the runbook with the on-call team
- **Functional test**: actually fail over a non-prod workspace; measure RTO/RPO
- **Document gaps**: every drill finds at least one undocumented step

For HIPAA: quarterly drills are a compliance expectation; document them in your IRP.

---

## What's NOT covered by Databricks-managed DR

The customer owns ALL of (from the docs):
1. Workspace re-provisioning in DR region (Terraform)
2. UC metastore content replication (catalogs, schemas, grants)
3. Cluster policies, instance pools, init scripts
4. Job and pipeline definitions (DABs in a DR target)
5. Notebooks and code (git)
6. Secrets (Key Vault replication strategy)
7. Network artifacts: VNets, NSGs, route tables, private endpoints, Private DNS in the DR region
8. Service principals and SCIM groups (mostly tenant-global, but workspace assignments must be re-applied)
9. Data: Delta deep clones or GRS, both with caveats
10. Identity-provider integrations (Entra ID conditional access policies must be present in DR region's user-flow)

**There is no "enable DR" toggle.** Plan accordingly.

---

## When NOT to invest in full DR

- **Dev / staging workspaces** — recreate from Terraform; no DR needed
- **Workspaces with no PHI and no regulatory contingency requirement** — backup-and-restore is enough
- **One-time analytical workspaces** for short projects — cost of DR exceeds value

For prod PHI workspaces at Optum: **always.** HIPAA contingency-plan rule makes it non-optional.

---

## Sanity check

1. Why does the docs page say "Azure Databricks requires a customer-driven approach to disaster recovery"?
2. Walk through the customer's 10-item replication checklist.
3. Active-passive vs Active-active — what's the cost/RTO tradeoff, and which fits Optum?
4. The transaction-log ordering trap with GRS — what is it, and what's the recovery action?
5. UC metastore replication: name two options for keeping DR metastore current.
6. HIPAA contingency-plan rule — what's the regulatory basis for DR being non-optional?

---

## Further reading

- [Disaster recovery on Azure Databricks — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/admin/disaster-recovery)
- [Azure Databricks + Fabric DR — MS Tech Community](https://techcommunity.microsoft.com/blog/analyticsonazure/azure-databricks--fabric-disaster-recovery-the-better-together-story/4481323)
- [Delta clones for DR — Databricks blog](https://www.databricks.com/blog/2021/04/20/attack-of-the-delta-clones-against-disaster-recovery-availability-complexity.html)
- [Azure Storage GRS](https://learn.microsoft.com/en-us/azure/storage/common/storage-redundancy)
- [HIPAA Security Rule §164.308](https://www.hhs.gov/hipaa/for-professionals/security/laws-regulations/index.html)
- [Azure Front Door for traffic failover](https://learn.microsoft.com/en-us/azure/frontdoor/)
