# Quiz — Module 21: HIPAA on Azure Databricks 2026

## Recall

**Q1.** What three things must be set at workspace creation for HIPAA eligibility, and which is permanent?

<details><summary>Answer</summary>

1. **Premium pricing tier** — Standard tier is unusable for PHI (no UC ABAC, CMK, audit log forwarding, Private Link).
2. **Enhanced Security and Compliance add-on** purchased on the account (separate line item beyond Premium).
3. **Compliance Security Profile (CSP) enabled** with `HIPAA` in `complianceStandards` — **PERMANENT.** Cannot be removed once a workspace has processed regulated data; must delete and recreate workspace to revert.

**Operational implication of permanence:** test/sandbox workspaces should NOT have CSP=HIPAA enabled. If they do, you've permanently marked them as having processed PHI, which restricts their reuse.
</details>

**Q2.** Walk through the three CMK products and the gaps each has.

<details><summary>Answer</summary>

| CMK feature | Encrypts | Key location | Gap |
|---|---|---|---|
| **Managed services CMK** | Notebook source/metadata, secrets, Git PATs, AI/BI dashboards (only if created after Nov 1, 2024), Genie Spaces (only if created after Apr 10, 2025), Vector Search indexes, Lakebase project data, SQL queries and history, model serving container images | Control plane | Pre-Nov 2024 dashboards & pre-Apr 2025 Genie Spaces are NOT encrypted at all — recreate them |
| **DBFS root CMK** | DBFS root, FileStore, Job results, Databricks SQL results, MLflow model artifacts, Lakeflow pipelines storage, notebook revisions | Workspace storage account in your subscription | None on the encryption side; storage account firewall is a separate setting |
| **Managed disks CMK** | Temporary disk storage on cluster VMs (classic compute only) | Customer Azure subscription | **Does NOT apply to serverless compute** — accept platform default disk encryption for serverless |

**Other notes:**
- Both Azure Key Vault and Managed HSM (FIPS 140-2 Level 3) supported. UHG-tier security expects Managed HSM.
- **Key rotation is on you** — no service-side rotation; AKV rotation policies apply.
- **Double encryption** on the workspace storage account is a separate setting.

**The migration debt note:** if your org spun up a Databricks workspace in 2023-2024 and built dashboards on member data, **those dashboard objects are not covered by your current CMK.** Recreating them is the only fix.
</details>

**Q3.** What's the audit log retention gap, and what's the architect's pipeline to close it?

<details><summary>Answer</summary>

**The gap:** Azure Databricks retains audit logs natively for **~1 year**. **HIPAA Security Rule §164.316(b)(2)(i) requires 6 years.**

**The architect's pipeline (two layers):**

**Layer 1 — Long-retention compliance copy:**
- DLT/Lakeflow pipeline reads `system.access.audit` and writes to `_compliance.audit.events`
- Stored in tier-0 governance catalog
- 6-year retention enforced via Azure Storage immutability + Delta retention policy
- **Full record kept** (no redaction; this is the compliance source of truth)
- Tagged `phi_class=high` because `request_params` can contain PHI

**Layer 2 — SIEM forwarding for real-time alerting:**
- Azure Monitor diagnostic settings → Event Hub → Splunk/Sentinel
- For alerting on suspicious access patterns
- Often filtered or tokenized to remove PHI from `request_params` before SIEM ingestion

**The PHI-in-audit-logs reality:** `request_params` can contain literal SQL values inlined into queries (`WHERE member_id = '12345678'`). **Audit logs themselves are PHI.** The compliance Delta destination must have the same controls as the source workspace; the SIEM destination needs either tokenization or a locked-down PHI-aware index.
</details>

---

## Apply

**Q4.** Write the workspace tag-naming-pollution CI lint that rejects PHI-shaped names.

<details><summary>Answer</summary>

```python
# .github/workflows/lint_naming.py
"""
Lint Databricks asset names for PHI patterns.
Run as a CI gate on every PR that touches databricks.yml or terraform.
"""
import re
import sys
import yaml
from pathlib import Path

# Patterns that suggest PHI
PHI_PATTERNS = [
    re.compile(r"\b\d{9}\b"),                    # SSN-shaped (9 consecutive digits)
    re.compile(r"\bMBR-?\d{6,12}\b", re.IGNORECASE),  # Member ID
    re.compile(r"\bMRN-?\d{4,12}\b", re.IGNORECASE),  # Medical Record Number
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),        # Date-shaped (could be DOB)
    re.compile(r"\bclaim[-_]?\d{8,12}\b", re.IGNORECASE),  # Claim ID
]

# Common first-names file (load from a curated dictionary)
FIRST_NAMES = set(Path("etc/common_first_names.txt").read_text().lower().split())

def check_value(value: str, location: str) -> list[str]:
    """Return list of violations for this string value."""
    violations = []
    for pattern in PHI_PATTERNS:
        if pattern.search(value):
            violations.append(
                f"{location}: PHI pattern matched '{pattern.pattern}' in '{value}'"
            )
    # Check for first names (PHI risk if combined with other identifiers)
    words = re.findall(r"\b[a-zA-Z]+\b", value.lower())
    name_hits = [w for w in words if w in FIRST_NAMES and len(w) > 3]
    if name_hits:
        violations.append(
            f"{location}: possible name in '{value}': {name_hits}"
        )
    return violations

def lint_databricks_yml(path: Path) -> list[str]:
    """Lint a databricks.yml bundle file."""
    violations = []
    config = yaml.safe_load(path.read_text())
    
    # Check bundle name
    if 'bundle' in config and 'name' in config['bundle']:
        violations += check_value(config['bundle']['name'], f"{path}:bundle.name")
    
    # Check resource names (jobs, pipelines, models)
    for resource_type, resources in config.get('resources', {}).items():
        for resource_id, resource in (resources or {}).items():
            for field in ['name']:
                if field in resource:
                    violations += check_value(resource[field], 
                                              f"{path}:resources.{resource_type}.{resource_id}.{field}")
    
    # Check tags
    for resource_type, resources in config.get('resources', {}).items():
        for resource_id, resource in (resources or {}).items():
            for tag_key, tag_value in resource.get('tags', {}).items():
                violations += check_value(str(tag_value), 
                                          f"{path}:resources.{resource_type}.{resource_id}.tags.{tag_key}")
    
    return violations

def main():
    violations = []
    for path in Path('.').rglob('databricks.yml'):
        violations += lint_databricks_yml(path)
    for path in Path('.').rglob('*.tf'):
        # Similar check on Terraform name fields
        for line in path.read_text().splitlines():
            if 'name' in line.lower():
                violations += check_value(line, f"{path}")
    
    if violations:
        print("PHI naming pollution detected:")
        for v in violations:
            print(f"  ❌ {v}")
        sys.exit(1)
    print("✅ Naming lint passed.")

if __name__ == '__main__':
    main()
```

**CI integration (GHA):**

```yaml
- name: PHI naming lint
  run: python .github/workflows/lint_naming.py
```

**Discipline:**
- Run on every PR that touches `databricks.yml` or Terraform `*.tf`
- Block merge on violations
- Curate the `common_first_names.txt` dictionary; tune false-positive rate
- Document the policy: "PHI-shaped names in workspace artifacts are a HIPAA finding, not a style preference"
- Audit existing artifacts for non-compliant names; remediate before next compliance review

**The architect's pitch:** "PHI in workspace names sits outside the BAA. We can't expect engineers to remember this every time; we make the CI gate enforce it."
</details>

---

## Diagnose

**Q5.** A team enables Genie on a `prod_phi_claims` catalog so clinical reviewers can ask natural-language questions. Walk through your architect-level objection.

<details><summary>Answer</summary>

**This is a category mistake. Don't enable Genie on PHI catalogs.**

**The objections:**

1. **Genie's chat history persists in the control plane.** User questions like "show me member 12345's claims" become persisted artifacts in Genie space history. Even with managed-services CMK applied (only for spaces created after Apr 10, 2025), the natural-language *question* is now persistent text containing PHI.

2. **The natural-language question itself is not row-filtered.** UC row filters and column masks enforce on the resulting SQL — yes, the user can't see data they shouldn't. But they typed an MRN into the chat box; that text is now in Genie history regardless of whether the SQL succeeded. **The leak is the question, not the answer.**

3. **A user with no access to a member can still type the member's MRN.** They don't get data back, but the MRN is now persisted as a chat-history artifact. If the user shares a screenshot or exports their chat history, the MRN is exposed.

4. **CSP defaults disable AI assistive features for a reason.** The Compliance Security Profile defaults Genie OFF on HIPAA workspaces. Enabling it overrides a security-conscious default; document the override rationale and risk acceptance.

5. **BAA scope on Genie features is unclear.** Several Genie features are NOT on the HIPAA-allowed preview list. **Default position: out of BAA on PHI workspaces.**

**The architect's recommendation:**
- **Don't enable Genie on PHI catalogs.** Instead:
  - Enable Genie on a **de-identified analytics catalog** (`prod_deid_claims`)
  - For clinical review of specific members, use a **purpose-built RAG agent** with explicit tool-call to a parameterized SQL function. The agent's prompt template doesn't accept free-text MRNs; it requires a member identifier from an authorized session context.
- Document the policy: "Genie is enabled on de-identified catalogs only. PHI access requires the agent path with audit + on-behalf-of-user authorization."

**The systemic point:** **convenience features for analysts (NL-to-SQL on PHI) are a HIPAA risk surface that doesn't map cleanly onto UC's row/column-level governance.** The right tool for clinical workflows on PHI is purpose-built agents with explicit, audited tool calls — not Genie.

**Sources:** [Genie Spaces docs](https://learn.microsoft.com/en-us/azure/databricks/genie/), [HIPAA on Azure Databricks](https://learn.microsoft.com/en-us/azure/databricks/security/privacy/hipaa).
</details>

---

## Defend

**Q6.** A peer says "we should enable CSP+HIPAA on every workspace, even dev/sandbox, for consistency." Defend or refute.

<details><summary>Answer</summary>

**Refute, decisively.**

**Why this is wrong:**

CSP enablement is **permanent.** *"Enabling the compliance security profile or adding compliance standards to a workspace is intended to be a permanent change... To revert, you must delete the workspace and create a new one."*

If you enable CSP+HIPAA on a sandbox workspace:
- **The workspace is permanently marked as having been able to process regulated data.** Even if it never sees PHI, the audit-trail position is "this workspace was HIPAA-eligible."
- **You can't reuse the workspace** for non-HIPAA experimentation later without deleting and recreating.
- **CSP enforces restrictions** that make sandbox iteration painful: instance type allowlist (no ARM64), preview-feature gating (most preview features blocked), automatic cluster updates (jobs interrupted on maintenance window), CIS-hardened images (slower cold-start).
- **You're paying** for Premium tier + Enhanced Security and Compliance add-on on a workspace that doesn't need it.

**The peer's "consistency" argument is the wrong frame.** Consistency at the cost of:
- Permanent restrictions on workspace reuse
- Hampered preview-feature experimentation
- Higher cost
- Slower iteration

…is bad consistency.

**The right pattern:**
- **Production workspaces processing PHI:** CSP=HIPAA, full network controls, full CMK stack. Permanent. Documented as such.
- **Production workspaces processing non-PHI** (e.g., a public-data analytics workspace): CSP optional; if not needed, don't enable.
- **Dev / staging workspaces:** **CSP off.** Use synthetic or de-identified data only. **Production policy: never copy PHI to dev workspaces.**
- **Sandbox workspaces:** CSP off. Maximum experimentation freedom; preview features available; ARM64 if it makes sense.

**The architect's pitch:** "Consistency in *the architecture* is what matters — every PHI workspace looks the same; every non-PHI workspace looks the same. Forcing CSP on workspaces that don't process PHI burns optionality and cost for no compliance benefit. The discipline is to **never let PHI into a non-CSP workspace**, not to lock down every workspace as if it might."

**Production policy:** dev workspaces have a CI gate that blocks any data movement from prod-PHI catalogs to dev catalogs. **The discipline lives at the data-movement layer, not at the workspace-CSP layer.**

**Sources:** [Compliance security profile](https://learn.microsoft.com/en-us/azure/databricks/security/privacy/security-profile).
</details>
