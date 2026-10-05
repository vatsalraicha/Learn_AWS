# Quiz — Module 23: Disaster Recovery & Multi-Region

## Recall

**Q1.** Why does the Databricks DR docs page say "Azure Databricks requires a customer-driven approach to disaster recovery"?

<details><summary>Answer</summary>

Because **Databricks does not auto-fail-over workspaces cross-region.** A workspace is regional; the control plane is regional; the Unity Catalog metastore is regional and singleton. The architecture choice is intentional — different customers have different DR tolerances, cost budgets, and compliance needs.

**The customer owns:**
1. Workspace re-provisioning in DR region (Terraform)
2. UC metastore content replication (catalogs, schemas, grants — NOT auto-replicated)
3. Cluster policies, instance pools, init scripts
4. Job and pipeline definitions (DABs)
5. Notebooks and code (git)
6. Secrets (Key Vault replication)
7. Network artifacts: VNets, NSGs, route tables, PEs, Private DNS in DR region
8. Service principals and SCIM groups (workspace assignments)
9. Data (Delta deep clones or GRS)
10. Identity-provider integrations (Entra Conditional Access)

For HIPAA: **45 CFR 164.308(a)(7) (HIPAA contingency-plan rule)** requires documented data backup, disaster recovery, and emergency-mode operation plans. **The Databricks layer of that plan must be explicit in your IRP.**
</details>

**Q2.** What's the transaction-log ordering trap with GRS, and what's the recovery action?

<details><summary>Answer</summary>

**The trap:** GRS replicates the Delta files but **transaction log ordering across regions is eventually consistent.** After a real failover from primary to DR region, the secondary region may have:
- All the data files (Parquet)
- Most of the transaction log (`_delta_log/*.json`)
- BUT the latest few commits may be missing or out-of-order

This means **the table appears corrupted** after failover — readers see "log version N exists but referenced files don't" or vice versa.

**Recovery action:**
1. **`FSCK REPAIR TABLE silver.claim_line`** — reconciles the log against actual file inventory; removes orphan log entries.
2. **Generate a fresh checkpoint** if the log is truncated.
3. **`RESTORE TABLE silver.claim_line VERSION AS OF <known-good>`** if the log is too damaged — restores to a known-good point in time (within the retention window).
4. **Document data loss** — RPO actual vs target.

**Build this into the runbook.** The first time you discover this is during a real failover is too late. Quarterly DR drills should include "simulate GRS lag" scenarios so the team has practiced.
</details>

---

## Apply

**Q3.** Sketch the active-passive DR runbook for a HIPAA workspace pair (East US primary, East US 2 DR).

<details><summary>Answer</summary>

```
PRE-FAILOVER STATE (continuous):

Primary (East US):
  • ws-phi-east-001 (workspace; CSP=HIPAA; users connect here)
  • UC metastore: optum-eastus-metastore
  • Catalogs: prod_phi_claims, prod_deid_claims, etc.
  • ADLS Gen2: GRS to East US 2
  • Key Vault: GRS to East US 2

DR (East US 2):
  • ws-phi-eastus2-001 (warm standby workspace; CSP=HIPAA)
  • UC metastore: optum-eastus2-metastore
  • Catalogs replicated nightly via Terraform + script
  • ADLS Gen2 secondary (RA-GRS)
  • Network: full PE topology mirrored

CONTINUOUS REPLICATION:
  - Terraform applies to BOTH regions on every infra change
  - DABs deploys to both regions (target = primary, target = dr)
  - UC catalog re-creation script runs nightly in DR (re-applies grants)
  - Delta Deep Clone of all hot tables to DR storage nightly
  - SIEM forwarding from BOTH regions to unified destination

────────────────────────────────────────────────────────────────────

FAILOVER TRIGGER:
  - Azure declares East US down for >30 min OR planned drill (quarterly)

DURING FAILOVER (target RTO 1-2 hours):

  T+0: Incident declared. On-call platform admin acknowledges.
  
  T+5: 
    - Verify DR readiness: 
      • DR Terraform state current?
      • UC metastore replication ran in last 24h?
      • Delta Deep Clones current? (last successful clone time)
      • Key Vault GRS status?
    - If any "no", document RPO impact.
  
  T+15:
    - DNS / traffic failover via Azure Front Door:
      adb-phi-east.optum.com → ws-phi-eastus2-001
    - Notify users via incident channel
  
  T+30:
    - Promote DR workspace: change client connection strings 
      (DBSQL warehouse endpoints, app config, dashboard data sources)
    - Verify CSP=HIPAA still enforced in DR (it's permanent, so yes)
    - Verify ABAC policies, workspace-catalog bindings active
  
  T+45:
    - Trigger DR-region Lakeflow pipelines (DABs already deployed)
    - Verify scheduled jobs run on DR Job Compute
    - Run smoke tests on top-10 dashboards
  
  T+60:
    - Reconcile any transaction log issues from GRS lag (FSCK REPAIR)
    - Communicate "DR active" to all stakeholders
    - Document timeline + actual RTO

POST-FAILOVER:
  - Within 24h: incident review meeting
  - Within 5 days: post-mortem document
  - Plan reverse-failover when primary is healthy

REVERSE-FAILOVER (when East US recovered):
  - Sync DR-region data changes back to primary (Delta Deep Clone reverse direction)
  - Test primary in shadow mode (run jobs, no traffic)
  - Switch DNS back to primary
  - Decommission temp DR mode
  - Document any data loss in reverse-failover RPO
```

**Production discipline:**
- **Quarterly DR drill** — tabletop + functional test on a non-prod workspace pair
- **Document the runbook** in IRP (Incident Response Plan)
- **Train the on-call team** — every quarter has rotating drill leadership
- **Update the runbook** after every drill or real failover

**HIPAA-specific:**
- Audit logs from BOTH regions stream to the same SIEM destination — auditor wants unified view
- Workspace IDs and member-bound resources should be DR-symmetric (same catalog names, same workspace-binding patterns)
- Document RTO/RPO targets in the IRP and verify quarterly that drill outcomes meet them
</details>

---

## Defend

**Q4.** A peer says "we should do active-active across regions for sub-minute RTO — anything less doesn't meet HIPAA." Defend or refute.

<details><summary>Answer</summary>

**Refute, with calibration.**

**Where the peer is wrong on the HIPAA claim:**
- HIPAA contingency-plan rule (45 CFR 164.308(a)(7)) requires **documented** plans for data backup, disaster recovery, and emergency-mode operation. **It doesn't specify RTO/RPO numbers.** Each covered entity defines what's appropriate for their risk profile.
- For most healthcare workloads (claims processing, member 360, HEDIS), an RTO of 1-4 hours via **active-passive** is well within HIPAA expectations. Real-time clinical decision support might need tighter RTO; ETL/analytics doesn't.

**Where active-active is genuinely worse for most cases:**
- **2-3× the cost** — full warm cluster + storage + serving in both regions
- **Operational complexity** — two writeable copies = consistency challenges, conflict resolution, dual-write failure modes
- **UC metastore complexity** — catalogs/schemas/grants must be perfectly synced; drift produces silent data divergence
- **Audit complexity** — auditing across two writeable systems adds doubling of audit pipelines

**Where active-active is right:**
- **Real-time clinical chat / decision support** with sub-minute SLO
- **Customer-facing apps** where any downtime is brand-damaging
- **Workloads where the cost premium is justified by the business case**

**For Optum-scale healthcare ETL/ML/RAG workloads:**
- **Active-passive** with 1-4 hour RTO is the default
- HIPAA contingency-plan rule satisfied by documented plan + quarterly drills
- Cost is roughly 1.3-1.5× single-region (warm secondary + replication overhead), not 2-3×

**The architect's pitch:**
- "Active-active is the right call for clinical-decision-support latency-critical paths. For ETL/BI/ML workloads (which is most of our footprint), active-passive at 1-4 hour RTO meets HIPAA and saves us 50%+ of DR cost."
- "We can migrate specific workloads to active-active later if the business case justifies it. Default is active-passive."

**Production discipline:**
- Categorize each workload by tolerance: real-time-critical (active-active candidate) vs analytical (active-passive)
- Justify the active-active premium with a specific business case
- Don't default to active-active for all workloads "to be safe" — the cost penalty is real and not always justified

**Source:** [HIPAA Security Rule §164.308](https://www.hhs.gov/hipaa/for-professionals/security/laws-regulations/index.html), [Disaster recovery on Azure Databricks](https://learn.microsoft.com/en-us/azure/databricks/admin/disaster-recovery).
</details>
