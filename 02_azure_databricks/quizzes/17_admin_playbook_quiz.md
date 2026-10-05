# Quiz — Module 17: Admin Playbook

## Recall

**Q1.** Name the five distinct administrative roles in Databricks 2026 and the key thing each *cannot* do.

<details><summary>Answer</summary>

1. **Account admin** — account console: billing, identity (account-level SCIM), workspaces, NCCs, metastore admin assignment. **Cannot:** automatically have data access in workspaces.
2. **Metastore admin** — UC metastore: catalogs, ABAC policies, governed tags, system table access. **Cannot:** create workspaces or manage Azure resources.
3. **Workspace admin** — one workspace: clusters, jobs, ACLs, instance pools, cluster policies. **Cannot:** grant UC catalog access (separate role); cannot reach other workspaces.
4. **Catalog owner** — a single UC catalog: grants on schemas/tables in that catalog. **Cannot:** create catalogs or modify ABAC policies (unless also metastore admin).
5. **Cluster policy admin** — cluster policy permissions only. **Cannot:** manage clusters directly.

**Don't collapse them.** A single person with all five roles is a single point of compromise.
</details>

**Q2.** What's the `_v<n>` init script versioning pattern, and why does it matter?

<details><summary>Answer</summary>

**Pattern:** name init scripts in UC Volumes with a version suffix:
- `/Volumes/_admin/init/analyst_v3.sh`
- `/Volumes/_admin/init/analyst_v4.sh` (next version)

Reference in cluster policy by full path: `"init_scripts.0.volumes.destination": {"type": "fixed", "value": "/Volumes/_admin/init/analyst_v3.sh"}`.

**Why it matters:**
- **Rollforward without overwrite** — write `_v4.sh` alongside `_v3.sh`; update policy; bounce clusters as they cycle.
- **Rollback if v4 is bad** — flip policy back to `_v3.sh`; bounce again. Old version is still there.
- **Audit trail** — every cluster's init script reference is auditable in `system.access.audit`.

**The discipline: never edit init scripts in place.** A wave of cluster restarts touching a bad in-place edit is hard to undo.
</details>

**Q3.** What are the two retention layers for audit logs, and which one handles HIPAA's 6-year requirement?

<details><summary>Answer</summary>

**Layer 1 — Long-retention Delta sink (handles HIPAA's 6-year requirement):**
- Custom DLT/Lakeflow pipeline reads `system.access.audit` and writes to `_compliance.audit.events`
- Stored in tier-0 governance catalog with 6-year retention enforced via Azure Storage immutability + Delta retention
- **Full record kept** (don't redact; this is the compliance copy)
- Tagged `phi_class=high` because `request_params` can contain PHI

**Layer 2 — SIEM forwarding for real-time alerting:**
- Azure Monitor diagnostic settings → Event Hub → Splunk/Sentinel
- For alerting on suspicious patterns
- Often filtered or tokenized to remove PHI from `request_params` before SIEM ingestion

**Why two layers:** native Databricks audit log retention is **~1 year** — insufficient for HIPAA (45 CFR §164.316(b)(2)(i) requires 6 years). The compliance Delta layer extends retention; the SIEM layer enables alerting.
</details>

---

## Apply

**Q4.** Write the cluster policy JSON for a "GenAI engineer" persona who needs:
- DBR 17.3 LTS or 18.x
- A10 or A100 GPU instances
- Spot workers, On-Demand driver
- Mandatory cost_center tag (regex `^cc-[0-9]{6}$`)
- Allowed data_classification: non-phi, deid, phi
- Auto-term 30-180 min, default 90
- Max 16 workers

<details><summary>Answer</summary>

```json
{
  "spark_version": {
    "type": "regex",
    "pattern": "^(17\\.3\\.x|18\\.[0-9]+\\.x)-(gpu-)?ml-scala2\\.13$"
  },
  "node_type_id": {
    "type": "allowlist",
    "values": [
      "Standard_NC4ads_T4_v3",
      "Standard_NC8ads_A10_v4",
      "Standard_NC24ads_A100_v4",
      "Standard_ND96isr_H100_v5"
    ]
  },
  "data_security_mode": {
    "type": "allowlist",
    "values": ["SINGLE_USER", "USER_ISOLATION"]
  },
  "autotermination_minutes": {
    "type": "range",
    "minValue": 30,
    "maxValue": 180,
    "defaultValue": 90
  },
  "num_workers": {
    "type": "range",
    "maxValue": 16
  },
  "azure_attributes.availability": {
    "type": "fixed",
    "value": "SPOT_WITH_FALLBACK_AZURE"
  },
  "azure_attributes.first_on_demand": {
    "type": "fixed",
    "value": 1
  },
  "azure_attributes.spot_bid_max_price": {
    "type": "fixed",
    "value": -1
  },
  "custom_tags.cost_center": {
    "type": "regex",
    "pattern": "^cc-[0-9]{6}$"
  },
  "custom_tags.business_unit": {
    "type": "allowlist",
    "values": ["claims", "member", "provider", "rx", "stars", "actuarial"]
  },
  "custom_tags.workload": {
    "type": "fixed",
    "value": "genai"
  },
  "custom_tags.data_classification": {
    "type": "allowlist",
    "values": ["non-phi", "deid", "phi"]
  }
}
```

**Apply via Terraform:**

```hcl
resource "databricks_cluster_policy" "genai_engineer" {
  name              = "genai-engineer"
  policy_family_id  = "" # custom policy
  definition        = file("policies/genai_engineer.json")
}

resource "databricks_permissions" "genai_engineer" {
  cluster_policy_id = databricks_cluster_policy.genai_engineer.id
  
  access_control {
    group_name       = "genai-engineers"
    permission_level = "CAN_USE"
  }
}
```

**Discipline notes:**
- `first_on_demand = 1` — driver always On-Demand (driver preemption kills the cluster mid-run, much worse than worker preemption)
- `SPOT_WITH_FALLBACK_AZURE` — Spot workers, fall back to On-Demand if Spot is unavailable in the region
- `autotermination_minutes` range with default 90 — long enough for fine-tune jobs, bounded for forgotten clusters
- `data_classification: phi` allowed — this persona may work with PHI; the workspace they're in (PHI workspace) restricts catalogs at the binding layer
</details>

---

## Diagnose

**Q5.** A user complains: "I can't run my notebook on my favorite cluster anymore." What's likely happened, and what's the diagnosis tree?

<details><summary>Answer</summary>

**Likely causes (in order of frequency):**

1. **Cluster was deleted** — common after a workspace cleanup or DBR upgrade.
   - **Check:** `system.compute.clusters` for the cluster ID.
   - **Fix:** create a new cluster from a job_cluster definition, or attach the notebook to a new cluster.

2. **Cluster is in a bad state** (failed to start, terminating).
   - **Check:** the cluster events page in the UI; `system.compute.cluster_events`.
   - **Fix:** terminate and recreate; or wait for terminate to complete.

3. **The user's group membership changed** — they no longer have CAN_USE on the cluster's policy.
   - **Check:** group membership in account console; cluster policy ACLs.
   - **Fix:** restore the group membership or move to a policy they can use.

4. **DBR upgrade broke the cluster** — the cluster now references a deprecated DBR.
   - **Check:** cluster's spark_version vs supported list.
   - **Fix:** update spark_version in the cluster definition.

5. **`databricks-connect` version mismatch** — local env doesn't match cluster DBR (Module 5).
   - **Check:** local `databricks-connect` version vs cluster DBR.
   - **Fix:** pip install the matching version.

6. **Workspace-catalog binding changed** — the cluster's notebook references catalogs the user can't access from this workspace.
   - **Check:** which catalogs the notebook reads from; binding for those catalogs.
   - **Fix:** move work to the bound workspace; or update binding (with security review).

7. **CSP feature gate** — a feature the notebook uses is now restricted on the HIPAA workspace's CSP.
   - **Check:** the HIPAA-allowed preview features list; the notebook's feature usage.
   - **Fix:** rewrite the notebook without the disallowed feature; or use a non-CSP workspace for the experiment.

**The triage discipline:** ask the user for the cluster ID and the exact error. **Don't guess** — open `system.compute.cluster_events` for the cluster, read the latest event. The error message names the issue 80% of the time; the diagnosis tree above handles the other 20%.
</details>

---

## Defend

**Q6.** A peer says "we should give the on-call SRE group permanent metastore admin so they can fix things at 3am." Defend or refute.

<details><summary>Answer</summary>

**Refute, decisively. This is a tier-0 separation-of-duties violation.**

Where the peer's instinct is right:
- **3am incidents need fast resolution.** Waiting for a metastore admin to be paged delays MTTR.
- **The on-call group has the technical chops** to fix UC issues.

Where the peer is wrong:
- **Metastore admin is the single most powerful role in the workspace.** They can grant themselves access to any catalog, read any PHI table, modify any ABAC policy. **For healthcare, this role's blast radius is catastrophic if compromised.**
- **Permanent broad access widens the attack surface.** A compromised SRE laptop becomes a path to PHI exfiltration. The least-privilege principle says SREs get scoped access, not metastore admin.
- **Compliance audit findings.** SOC 2 / HITRUST / HIPAA auditors look specifically for "who has god access?" Permanent on-call metastore admin is a red flag finding.
- **Mid-incident, the SRE doesn't know the system well enough.** Metastore admin operations (changing GRANTs, modifying ABAC) require knowledge of the data classification, the team that owns the catalog, the BAA scope. SREs don't have that context at 3am.

**The right pattern:**
- **Permanent metastore admin** = a tier-0 service account + 2 named individuals (security architect + data platform lead). MFA + conditional access. Activity audited continuously.
- **Break-glass procedure for the on-call SRE:**
  - Documented runbook for what they CAN do at 3am (cluster restart, Spark UI access, log inspection)
  - For any action requiring metastore admin: page the on-call metastore admin
  - If the metastore admin can't be reached: documented escalation to a C-level for break-glass approval
- **Time-bounded elevation** — if you absolutely must give SRE temporary metastore admin during an incident, scope it to that incident with a defined end time and audit trail.

**The architect's pitch to the peer:**
- "I hear the 3am pain. The fix isn't broader access; it's a better triage tree + clear escalation paths."
- "Document what the on-call SRE CAN fix without metastore admin (probably 80% of incidents). For the 20% that need it, page the metastore admin or trigger break-glass."
- "Every quarter, audit how often the SRE actually needed metastore admin. If it's rare, the friction was worth it. If it's frequent, fix the underlying gap (probably a missing automation, not a missing permission)."

**The systemic point:** for healthcare, **separation of duties is a compliance requirement, not a nice-to-have.** Permanent god access for the on-call group fails that requirement in writing.

**Sources:** [Identity best practices](https://learn.microsoft.com/en-us/azure/databricks/admin/users-groups/best-practices), [HIPAA Security Rule §164.308](https://www.hhs.gov/hipaa/for-professionals/security/laws-regulations/index.html).
</details>
