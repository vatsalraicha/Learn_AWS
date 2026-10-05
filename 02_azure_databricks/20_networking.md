# Module 20 — Networking, Private Link, SCC, VNet

> **Goal of this module:** the Azure-specific networking topology a healthcare-grade Databricks workspace requires — VNet injection, Secure Cluster Connectivity, the six Private Endpoints, NCC limits, the browser-auth single-point-of-failure, and the March 31 2026 NAT Gateway change.

---

## Why this matters

For an Optum-grade HIPAA workspace, **only the "Complete private isolation" pattern is defensible.** Anything less and your security architects will reject it. This module is the architectural detail behind that pattern.

---

## The four network patterns

The Private Link concepts page ([Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/security/network/concepts/private-link), updated May 2026) lays out four patterns:

| | Front-end only | Outbound serverless only | Back-end only | **Complete private isolation** |
|---|---|---|---|---|
| User connectivity | Private or public | Public | Public | **Private only** |
| Serverless data access | Public | Private | Public | **Private** |
| Cluster→control plane | Public | Public | Private | **Private** |
| Workspace public access | Enabled | n/a | Enabled | **Disabled** |
| Required NSG rules | AllRules | n/a | NoAzureDatabricksRules | **NoAzureDatabricksRules** |

**For Optum / a payor handling claims and clinical data, only Complete private isolation is defensible.** The rest of this module is the components.

---

## VNet injection (mandatory)

Workspace deployed into your own VNet with a host subnet and container subnet, each `/26` minimum.

**Subnet rules:**
- Both subnets delegated to `Microsoft.Databricks/workspaces`
- *"You can't share subnets across workspaces or deploy other Azure resources on the subnets used by your Azure Databricks workspace"*
- **`/26` minimum each**, **`/24` recommended** for prod
- Each cluster node consumes ~2 IPs (host + container). A 100-node job cluster uses 200 IPs. **Size for peak concurrent.**

**NSG:** Databricks injects required rules automatically when subnets are delegated. **Do not hand-edit** — additions are fine, but altering platform rules breaks the workspace silently.

**Once deployed, irreversible:**
- Cannot convert public workspace to VNet-injected in place — delete-and-redeploy (UC data preserves via metastore reattachment)
- Cannot change host/container subnet CIDRs after creation

For HIPAA: VNet injection is non-negotiable. Always.

---

## Secure Cluster Connectivity (SCC) — no public IP

**Mechanism:**
- **Without SCC**: data plane VMs have public IPs and the Databricks control plane reaches them inbound over those IPs (with NSG-locked source ranges).
- **With SCC**: data plane VMs have **no public IPs**. They establish an **outbound TLS tunnel to the regional control plane** over port 443. The control plane sends commands down that already-open tunnel — classic reverse-proxy pattern. **No inbound from internet.**
- Required outbound: workspace control-plane FQDN, **SCC relay FQDN** (region-specific), webapp/REST endpoints, log-blob, artifact-blob, system tables backend.

**Default-on for new workspaces** created via portal or ARM `2024-05-01+`. For healthcare/regulated, SCC is effectively mandatory. **Most enterprise Azure landing zones disallow public IP on PaaS-adjacent compute by policy.**

---

## Six Private Endpoints (the HIPAA layout)

A hardened workspace needs six PEs. Plan the topology before building.

```
┌──────────────────────────────────────────────────────────────┐
│ Transit VNet (hub)                                           │
│   ┌─────────────────────────────────────────────────────┐   │
│   │ user-access subnet                                  │   │
│   │   • Front-end PE (workspace UI/REST)                │   │
│   │   • Browser-auth PE (DEDICATED workspace per region)│   │
│   └─────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
                              │ peered
┌──────────────────────────────────────────────────────────────┐
│ Workspace VNet (spoke)                                       │
│   ┌─────────────────────────────────────────────────────┐   │
│   │ workspace host subnet (delegated)                   │   │
│   │ workspace container subnet (delegated)              │   │
│   │ classic PE subnet (/28)                             │   │
│   │   • Back-end PE (data plane → control plane REST)   │   │
│   │   • Back-end PE (data plane → SCC relay)            │   │
│   │   • PE to ADLS Gen2 (each PHI storage account)      │   │
│   │   • PE to Key Vault                                 │   │
│   │   • PE to other PaaS (Event Hubs, ADX, etc.)        │   │
│   └─────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

The six PEs:

1. **Front-end PE** (workspace UI/REST) — users → workspace, in user-access VNet (often hub)
2. **Back-end PE** (data plane → control plane REST) — clusters → control plane, in workspace VNet
3. **Back-end PE** (data plane → SCC relay) — separate sub-resource on the same workspace, often the same VNet
4. **PE to ADLS Gen2** for each storage account housing UC external locations / managed storage
5. **PE to Key Vault** holding CMKs
6. **PE to other PaaS** the workspace integrates with: Event Hubs, ADX, Azure SQL, OpenAI, AI Search

**DNS:** Azure Private DNS zones — one per PaaS family — must resolve correctly from both the workspace VNet and any spoke that holds users. Most enterprises route through a central DNS resolver in the hub.

**Why this matters for Optum:** PHI data path is fully private. Audit can prove no public network egress from data plane.

### Workspace storage account firewall

Separate setting (`default-storage-firewall Enabled`). Requires separate `dfs` and `blob` PEs on a dedicated `/28` subnet. **Public network access to the workspace storage account is blocked.** Module 21 covers the HIPAA dependency on this.

---

## The browser-auth PE single-point-of-failure

The most operationally dangerous gotcha in the entire networking story:

**`browser_authentication`** sub-resource: only one such endpoint can exist per Azure region per private DNS zone, and **deleting the host workspace breaks SSO for every other workspace using it in that region.**

Production guidance: **dedicate a "private web auth workspace" per region** whose only purpose is hosting this endpoint. This workspace:
- Hosts the browser-auth PE
- Has no other production workloads
- Locked-down: no notebooks, no jobs, no data
- Lives in the tier-0 governance pattern (Module 17)
- Treated as critical infrastructure — deletion is a P1 incident

If you don't dedicate a workspace to this, the first time someone deletes a workspace that happened to host the PE, **SSO breaks for every other workspace in the region.** A 3am incident.

---

## NCC (Network Connectivity Configuration) limits

**Network Connectivity Configuration** is the account-level construct that owns serverless private endpoints. Limits to plan around:

- **10 NCCs per region per account**
- **100 PEs per region distributed across NCCs**
- **Up to 50 workspaces per NCC**

At Optum scale (likely hundreds of workspaces across business units), **this pinches.** Plan multi-account topology — splitting Optum's Databricks footprint across multiple Databricks accounts (e.g., one per major business unit) sidesteps the per-account NCC limits.

---

## Stable egress and the March 31 2026 change

**Default managed VNet uses an auto-created NAT gateway in the managed RG.** With VNet injection, the architect must provide an Azure NAT Gateway.

### The breaking change

**After March 31, 2026, new Azure VNets default to no outbound internet access.** This means:
- New Databricks workspace deployments after that date *must* have an explicit NAT Gateway
- Without it, clusters can't reach pypi, the Databricks control plane, or any other internet endpoint
- Result: dead clusters that fail at startup

**Egress load balancers are explicitly forbidden under SCC due to port exhaustion.**

For Optum: existing workspaces are unaffected; new deployments must include NAT Gateway provisioning in the Terraform.

### Outbound allowlist (Azure Firewall Premium)

For workspaces routing 0.0.0.0/0 through Azure Firewall:

- `*.azuredatabricks.net`
- regional control-plane FQDN
- regional SCC relay FQDN
- `*.cloud.databricks.com`
- log/artifact/system-tables blob endpoints
- Container Registry (`*.azurecr.io` if using custom containers)
- PyPI/Maven mirrors if you don't run an internal repo
- GitHub if you use Repos

The exact list lives in [User-defined route settings for Azure Databricks](https://learn.microsoft.com/azure/databricks/security/network/udr) — **recheck before publishing, it changes.**

---

## Service principals and managed identities

(Module 9 covered the UC storage credential layer; this section is the network-side identity decisions.)

- **Workspace-level SPs** — created in Azure Entra ID, granted to workspace via SCIM, used by jobs that call REST APIs or write to ADLS
- **Managed identity for UC storage credentials** — modern pattern. UC metastore creates a **storage credential** backed by an **Azure Managed Identity**, then **external locations** point at ADLS containers. Removes secret-management entirely.
- **Workload Identity Federation [D26]** — Databricks supports OIDC federation so GitHub Actions / Azure DevOps pipelines authenticate to Databricks **without long-lived PATs.** The 2025+ recommended CI/CD auth pattern (Module 19).
- **Account-level SPs** (added 2024) — SPs scoped at the Databricks account, used for cross-workspace and account-API operations (provisioning, UC, billing).

**Service principals are now "legacy"** for storage access because they can't reach storage accounts behind firewall rules — **managed identities are mandatory** for the SCC + storage-firewall combo.

---

## Two-VNet topology — the canonical diagram

For Optum-scale healthcare, the topology that lands:

```
┌─ Subscription: optum-platform-network ────────────────────────────┐
│                                                                    │
│  ┌─ Hub VNet ─────────────────────────────────────────────────┐  │
│  │  Azure Firewall Premium (TLS inspection)                    │  │
│  │  Azure Private DNS Resolver                                 │  │
│  │  ExpressRoute Gateway (to on-prem)                          │  │
│  │  user-access subnet (front-end PE, browser-auth PE)         │  │
│  └─────────────────────────────────────────────────────────────┘  │
│              │ peered                                              │
│              ↓                                                     │
│  ┌─ Spoke VNet (per workspace) ───────────────────────────────┐   │
│  │  workspace host subnet (delegated) /24                     │   │
│  │  workspace container subnet (delegated) /24                │   │
│  │  classic PE subnet /28 (back-end PEs, ADLS, KV)            │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

**Why two VNets:**
- **Hub** holds shared infrastructure: firewall, DNS resolver, ExpressRoute, user PEs
- **Spoke per workspace** holds workspace-specific: data plane subnets, workspace PEs
- Peering connects them; UDRs route through the firewall

This is the canonical Azure landing-zone pattern; Databricks fits into it as a regulated PaaS spoke.

---

## Workspace deployment vehicles

Three options ([Module 17 covered the lifecycle](17_admin_playbook.md)):

1. **Azure Portal** — fine for sandboxes, never for prod.
2. **ARM/Bicep** — `Microsoft.Databricks/workspaces` resource. The `parameters` block decides public-vs-VNet-injected and SCC. Bicep modules from `Azure-Samples/azure-databricks-pre-deployment-template` are common.
3. **Terraform** — `azurerm_databricks_workspace` for the Azure plane + the **databricks/databricks** provider for workspace-internal objects (clusters, jobs, UC). The dual-provider pattern.

**For Optum-grade prod: Terraform.** Reproducibility, code review, multi-environment.

---

## Production discipline

### "What's irreversible" checklist

Before running `terraform apply` on a new workspace:

- ☐ **Public vs VNet-injected** — cannot convert public to VNet-injected in place; delete-and-redeploy
- ☐ **CSP=HIPAA** — permanent; cannot be removed once enabled (Module 21)
- ☐ **Subnet CIDRs** — cannot change after creation; size for peak concurrent IP demand
- ☐ **Workspace storage account region** — cannot move; pick the right region
- ☐ **Metastore region** — once attached, expensive to migrate

Get these right on day 1. Mistakes here are weeks of rework.

### The browser-auth workspace pattern

Per region, dedicate a workspace solely to hosting the `browser_authentication` PE. This workspace:
- Has CSP enabled (HIPAA)
- Has no general user access
- Has no notebooks, jobs, or data
- Is monitored as tier-0 infrastructure
- Documented as "do not delete" in every relevant runbook

If you skip this and use a regular workspace's PE, **the first deletion of that workspace breaks SSO for every dependent workspace.**

### Audit network controls quarterly

Module 17 + 21 covers the compliance review checklist. The network-specific items:
- ☐ VNet injection enabled
- ☐ SCC enabled
- ☐ Front-end + back-end Private Link operational
- ☐ Public network access disabled
- ☐ NSG mode `NoAzureDatabricksRules`
- ☐ Workspace storage account firewall on
- ☐ DFS + blob PEs on the storage account
- ☐ NAT Gateway present (mandatory after Mar 31 2026)
- ☐ Outbound allowlist on Azure Firewall Premium current

---

## When NOT to use the full topology

- **Dev / sandbox environments** — full PE topology is overkill; single VNet + public-but-NSG-restricted is fine for cost
- **Customer demos / training environments** — same
- **Workspaces that genuinely don't process PHI** — non-PHI workspaces can be lighter, though most healthcare orgs standardize for consistency

For anything that touches PHI: **full Complete Private Isolation, no exceptions.**

---

## Sanity check

1. Why is "Complete private isolation" the only defensible network pattern for Optum-grade healthcare?
2. Walk through the six Private Endpoints needed for a HIPAA workspace.
3. The browser-auth PE single-point-of-failure: what is it, and what's the production discipline?
4. NCC limits at Optum scale — what's the architectural implication?
5. The March 31, 2026 NAT Gateway change — what breaks, and what's the fix?
6. What's irreversible about workspace deployment that you must get right on day 1?

---

## Further reading

- [Azure Private Link concepts](https://learn.microsoft.com/en-us/azure/databricks/security/network/concepts/private-link)
- [Secure cluster connectivity (SCC)](https://learn.microsoft.com/en-us/azure/databricks/security/network/classic/secure-cluster-connectivity)
- [VNet injection](https://learn.microsoft.com/en-us/azure/databricks/security/network/classic/vnet-inject)
- [Workspace storage firewall](https://learn.microsoft.com/en-us/azure/databricks/security/network/storage/firewall-support)
- [User-defined route settings](https://learn.microsoft.com/azure/databricks/security/network/udr)
- [Network Connectivity Configurations (NCC)](https://learn.microsoft.com/en-us/azure/databricks/security/network/serverless-network-security)
- [terraform-databricks-modules](https://github.com/databricks/terraform-databricks-modules)
- [Azure-Samples/azure-databricks-pre-deployment-template](https://github.com/Azure-Samples/azure-databricks-pre-deployment-template)
