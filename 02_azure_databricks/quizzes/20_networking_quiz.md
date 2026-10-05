# Quiz — Module 20: Networking, Private Link, SCC, VNet

## Recall

**Q1.** What's the "Complete private isolation" network pattern, and why is it the only defensible posture for healthcare?

<details><summary>Answer</summary>

**Complete private isolation** is the most restrictive of the four network patterns Microsoft documents:

| Setting | Value |
|---|---|
| User connectivity | Private only |
| Serverless data access | Private |
| Cluster→control plane | Private |
| Workspace public access | Disabled |
| NSG rules | `NoAzureDatabricksRules` |

**Why it's mandatory for healthcare:**
- **No public IP on data plane** — PHI data path stays inside your network
- **No inbound from internet to clusters** — eliminates a class of attack surface
- **All control-plane traffic via Private Link** — auditable, encrypted, network-pinned
- **Compliance auditors expect it** — anything less is a finding

For Optum-grade payor data (claims, clinical records), this is the only architecture security architects will sign off on.
</details>

**Q2.** Name the six Private Endpoints needed for a HIPAA workspace.

<details><summary>Answer</summary>

1. **Front-end PE** — users → workspace UI/REST. Lives in user-access VNet (typically hub).
2. **Back-end PE — data plane → control plane REST** — clusters → control plane.
3. **Back-end PE — data plane → SCC relay** — clusters → reverse-tunnel relay.
4. **PE to ADLS Gen2** for each PHI-storage account.
5. **PE to Key Vault** holding CMKs.
6. **PE to other PaaS** — Event Hubs, ADX, Azure SQL, AI Search, etc., as integrated.

**Plus DNS plumbing** — one Azure Private DNS zone per PaaS family, resolvable from workspace VNet and user spokes via central DNS resolver in hub.
</details>

**Q3.** What's the browser-auth PE single-point-of-failure, and what's the production discipline?

<details><summary>Answer</summary>

The `browser_authentication` PE has a unique constraint: **only one can exist per Azure region per private DNS zone.** And **deleting the host workspace breaks SSO for every other workspace using it in that region.**

**Production discipline:**
- **Per region, dedicate a "private web auth workspace"** whose only purpose is hosting this endpoint
- This workspace has CSP enabled (HIPAA), no notebooks/jobs/data, locked-down access, monitored as tier-0 infrastructure
- Documented as "do not delete" in every runbook
- Treated as critical infrastructure — its deletion is a P1 incident

**The footgun:** if you skip this and use a regular production workspace's PE, the first deletion of that workspace (decommission, region migration, etc.) breaks SSO for every dependent workspace in the region. A 3am incident.
</details>

---

## Apply

**Q4.** Sketch the Terraform shape for a HIPAA-compliant new workspace with VNet injection, SCC, NAT Gateway (post-Mar 31 2026), and dual CMK.

<details><summary>Answer</summary>

```hcl
# 1. Storage credentials, key vault, MIs (assumed pre-existing)
data "azurerm_user_assigned_identity" "uc_mi" {
  name                = "uc-mi-phi-prod"
  resource_group_name = "optum-databricks-prod"
}

# 2. NAT Gateway (mandatory post Mar 31, 2026)
resource "azurerm_public_ip" "nat" {
  name                = "ws-phi-nat-pip"
  resource_group_name = "optum-databricks-prod"
  location            = "eastus2"
  allocation_method   = "Static"
  sku                 = "Standard"
}

resource "azurerm_nat_gateway" "ws_nat" {
  name                    = "ws-phi-nat"
  resource_group_name     = "optum-databricks-prod"
  location                = "eastus2"
  sku_name                = "Standard"
  idle_timeout_in_minutes = 10
}

resource "azurerm_nat_gateway_public_ip_association" "nat_pip" {
  nat_gateway_id       = azurerm_nat_gateway.ws_nat.id
  public_ip_address_id = azurerm_public_ip.nat.id
}

# 3. VNet + subnets (host, container, PE)
resource "azurerm_virtual_network" "ws_vnet" {
  name                = "ws-phi-vnet"
  resource_group_name = "optum-databricks-prod"
  location            = "eastus2"
  address_space       = ["10.20.0.0/22"]
}

resource "azurerm_subnet" "host" {
  name                 = "host"
  resource_group_name  = "optum-databricks-prod"
  virtual_network_name = azurerm_virtual_network.ws_vnet.name
  address_prefixes     = ["10.20.0.0/24"]
  delegation {
    name = "databricks"
    service_delegation {
      name = "Microsoft.Databricks/workspaces"
      actions = ["Microsoft.Network/virtualNetworks/subnets/join/action",
                 "Microsoft.Network/virtualNetworks/subnets/prepareNetworkPolicies/action",
                 "Microsoft.Network/virtualNetworks/subnets/unprepareNetworkPolicies/action"]
    }
  }
}

resource "azurerm_subnet" "container" {
  name                 = "container"
  # similar config, /24
}

resource "azurerm_subnet" "pe" {
  name                 = "private-endpoints"
  address_prefixes     = ["10.20.2.0/28"]
  private_endpoint_network_policies_enabled = true
}

resource "azurerm_subnet_nat_gateway_association" "host_nat" {
  subnet_id      = azurerm_subnet.host.id
  nat_gateway_id = azurerm_nat_gateway.ws_nat.id
}
# (similar for container subnet)

# 4. Workspace
resource "azurerm_databricks_workspace" "phi_east" {
  name                = "ws-phi-east-001"
  resource_group_name = "optum-databricks-prod"
  location            = "eastus2"
  sku                 = "premium"  # HIPAA prerequisite
  
  custom_parameters {
    no_public_ip                                         = true  # SCC
    virtual_network_id                                   = azurerm_virtual_network.ws_vnet.id
    public_subnet_name                                   = azurerm_subnet.host.name
    private_subnet_name                                  = azurerm_subnet.container.name
    public_subnet_network_security_group_association_id  = azurerm_subnet_network_security_group_association.host.id
    private_subnet_network_security_group_association_id = azurerm_subnet_network_security_group_association.container.id
    require_default_storage_account_firewall             = true
  }
  
  managed_services_cmk_key_vault_key_id = azurerm_key_vault_key.managed_services.id
  managed_disk_cmk_key_vault_key_id     = azurerm_key_vault_key.managed_disk.id
}

# 5. Compliance Security Profile (PERMANENT — cannot be undone)
resource "databricks_workspace_compliance_security_profile" "phi_csp" {
  workspace_id          = azurerm_databricks_workspace.phi_east.workspace_id
  is_enabled            = true
  compliance_standards  = ["HIPAA"]
}

# 6. Private Endpoints (front-end + back-end + storage)
resource "azurerm_private_endpoint" "front_end" {
  name                = "pe-ws-phi-front-end"
  resource_group_name = "optum-databricks-prod"
  location            = "eastus2"
  subnet_id           = azurerm_subnet.user_access.id  # in hub VNet
  
  private_service_connection {
    name                           = "front-end"
    private_connection_resource_id = azurerm_databricks_workspace.phi_east.id
    is_manual_connection           = false
    subresource_names              = ["databricks_ui_api"]
  }
}

resource "azurerm_private_endpoint" "back_end" {
  name                = "pe-ws-phi-back-end"
  subnet_id           = azurerm_subnet.pe.id  # in workspace VNet
  
  private_service_connection {
    name                           = "back-end"
    private_connection_resource_id = azurerm_databricks_workspace.phi_east.id
    is_manual_connection           = false
    subresource_names              = ["databricks_ui_api"]
  }
}

resource "azurerm_private_endpoint" "scc_relay" {
  name      = "pe-ws-phi-scc-relay"
  subnet_id = azurerm_subnet.pe.id
  private_service_connection {
    name                           = "scc-relay"
    private_connection_resource_id = azurerm_databricks_workspace.phi_east.id
    is_manual_connection           = false
    subresource_names              = ["browser_authentication"]
  }
}

# Plus PEs for ADLS, Key Vault, other PaaS — same pattern
```

**Critical irreversibles (get right on day 1):**
- Public vs VNet-injected (cannot convert in place)
- CSP=HIPAA enabled (permanent)
- Subnet CIDRs (cannot change)
- Premium tier (downgrades break HIPAA features)
- Region (cannot move)

The above is the spine; production also includes NSG rules, route tables for forced-tunneling through Azure Firewall Premium, Private DNS zones, and the dedicated browser-auth workspace per region.
</details>

---

## Diagnose

**Q5.** A team's new workspace deployed in April 2026 has clusters that fail to start with "could not reach pypi.org" errors. Walk through the diagnosis.

<details><summary>Answer</summary>

**The April 2026 timing is the giveaway.** Most likely cause: **the March 31, 2026 Azure VNet outbound default change.**

After March 31, 2026, **new Azure VNets default to no outbound internet access.** Any new Databricks workspace deployed without an explicit NAT Gateway has clusters that can't reach pypi, the Databricks control plane regional endpoints, or any other internet endpoint.

**Diagnostic steps:**

1. **Check the cluster event log** for the specific error. "Could not reach pypi.org" plus "outbound connection timeout" patterns confirm.

2. **Verify NAT Gateway provisioning** — `terraform state show` (or Azure portal) on the workspace VNet. Is there a `nat_gateway` association on the host and container subnets? If not, that's the issue.

3. **Verify outbound allowlist on Azure Firewall** if forced-tunneling — `*.azuredatabricks.net`, regional control plane FQDN, regional SCC relay FQDN, PyPI mirrors, and the rest of the [UDR list](https://learn.microsoft.com/azure/databricks/security/network/udr).

4. **Test from within the cluster's network**: a one-shot init script that does `curl -I https://pypi.org` and writes the result to a log location.

**Fix:**

```hcl
resource "azurerm_nat_gateway" "ws_nat" {
  name                    = "ws-nat"
  resource_group_name     = "..."
  location                = "..."
  sku_name                = "Standard"
  idle_timeout_in_minutes = 10
}

resource "azurerm_public_ip" "nat" {
  name                = "ws-nat-pip"
  resource_group_name = "..."
  location            = "..."
  allocation_method   = "Static"
  sku                 = "Standard"
}

resource "azurerm_nat_gateway_public_ip_association" "nat_pip" {
  nat_gateway_id       = azurerm_nat_gateway.ws_nat.id
  public_ip_address_id = azurerm_public_ip.nat.id
}

resource "azurerm_subnet_nat_gateway_association" "host" {
  subnet_id      = azurerm_subnet.host.id
  nat_gateway_id = azurerm_nat_gateway.ws_nat.id
}

resource "azurerm_subnet_nat_gateway_association" "container" {
  subnet_id      = azurerm_subnet.container.id
  nat_gateway_id = azurerm_nat_gateway.ws_nat.id
}
```

**Architectural note:** **egress load balancers are explicitly forbidden under SCC due to port exhaustion.** NAT Gateway is the right egress mechanism.

**The systemic point:** update the platform team's Terraform module to include NAT Gateway provisioning by default for any new workspace. Existing workspaces (deployed before March 31, 2026) are unaffected, but any new deployment without NAT Gateway will fail.

**Source:** [Microsoft announcement on outbound default change](https://azure.microsoft.com/en-us/updates/default-outbound-access-for-vms-in-azure-will-be-retired-transition-to-a-new-method-of-internet-access/) (the underlying Azure change).
</details>

---

## Defend

**Q6.** A peer says "we should put all our workspaces in one big VNet to simplify the topology." Defend or refute.

<details><summary>Answer</summary>

**Refute, decisively.**

Where the peer's instinct is right:
- **One VNet is operationally simpler** — one set of NSGs, one DNS zone, one routing table.
- **Less Terraform** — fewer resources to maintain.

Where the peer is wrong:

1. **Subnet sharing is forbidden.** *"You can't share subnets across workspaces or deploy other Azure resources on the subnets used by your Azure Databricks workspace."* Each workspace needs its own delegated subnets. Putting multiple workspaces in one VNet means many subnets — and you've still got per-workspace blast radius.

2. **NCC limits.** 50 workspaces per NCC; 10 NCCs per region per account; 100 PEs per region per account. At Optum scale, a single VNet doesn't help with these limits — they're account-level, not VNet-level.

3. **Blast radius of NSG / route mistakes.** A single NSG misconfiguration in a one-big-VNet topology affects all workspaces. Spoke-per-workspace contains the damage.

4. **Compliance isolation.** Auditors look for "is the PHI workspace network-isolated from non-PHI?" Per-workspace spoke topology gives a clean answer.

5. **Lifecycle independence.** Decommissioning a workspace shouldn't risk affecting others. Spoke-per-workspace makes this clean — destroy the spoke, done.

**The architect's pitch:** **hub-and-spoke is the canonical Azure landing-zone pattern, not a Databricks quirk.** Every Azure Architect Expert (AZ-305) certification curriculum teaches it. Databricks fits naturally into it as a regulated PaaS spoke.

**The right pattern:**
- **Hub VNet** — shared infrastructure: Azure Firewall Premium, DNS resolver, ExpressRoute Gateway, user-access subnets (front-end PE, browser-auth PE)
- **Spoke VNet per workspace** — workspace-specific subnets (host, container, PE)
- **Peering** — hub to each spoke, no spoke-to-spoke (forced through firewall)

**Operational simplicity** comes from **Terraform module abstraction**, not from one big VNet. A `module "databricks_workspace_spoke"` that takes a few parameters and produces the whole spoke topology gives you simplicity without giving up isolation.

**Source:** Azure Cloud Adoption Framework's hub-spoke pattern, plus [Databricks VNet injection docs](https://learn.microsoft.com/en-us/azure/databricks/security/network/classic/vnet-inject).
</details>
