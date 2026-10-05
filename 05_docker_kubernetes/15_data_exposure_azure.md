# 15 — Data exposure for containers — Azure

> *"In Azure, managed identity is the lever. Once a container has the right MI, every other primitive — Key Vault, Storage, ACR — slots in for free."*

## Why this module exists

Azure's container-data story is built around two primitives:

- **Microsoft Entra ID Managed Identities** (system-assigned or user-assigned). Identity binding to compute, no secrets in code.
- **Azure Resource Manager (ARM) role-based access control (RBAC)**. Roles assigned at resource, resource-group, subscription, or management-group scope.

This module covers Docker on Azure VMs, Azure Container Instances (ACI), and Azure Container Apps. AKS is in module 28.

This module also relates to Topic 02 (Azure Databricks), which uses Azure Files / ADLS Gen2 / Managed Identities heavily — same primitives in a different consumption model.

---

## 1. Identity — Managed Identities

A **Managed Identity** (MI) is a special service principal in Entra ID, automatically managed (rotated, lifecycle-bound to the resource).

### 1.1 System-assigned vs user-assigned

- **System-assigned MI** — bound 1:1 to a resource (VM, ACI, App Service). Deleted when the resource is. Simple.
- **User-assigned MI** — a standalone resource. Can be attached to multiple resources. Lives independently. The production choice for containers that may run on many VMs.

For VM hosts running Docker:

```bash
az identity create --name my-ml-mi --resource-group my-rg
az vm identity assign --name my-vm --resource-group my-rg \
  --identities /subscriptions/.../resourcegroups/my-rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/my-ml-mi
```

Inside any container on the VM, the **Azure Instance Metadata Service (IMDS)** at `http://169.254.169.254/metadata/identity/oauth2/token` provides tokens:

```bash
curl -H "Metadata: true" \
  "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://vault.azure.net/&mi_res_id=/subscriptions/.../my-ml-mi"
```

The Azure SDK does this automatically via **DefaultAzureCredential** in any supported language.

### 1.2 The same IMDS-trust problem as AWS

Azure's IMDS is also at `169.254.169.254` (different paths than AWS), and the same containerization-pivot risk applies. Mitigation:

- **Block IMDS from containers** via `iptables -A DOCKER-USER -d 169.254.169.254 -j DROP`.
- Use **Microsoft Entra Workload ID** for AKS workloads (module 28) instead of host IMDS.
- For VMs, **assign per-workload user-assigned MIs** so the blast radius of an IMDS leak is one MI, not the host's full identity.

### 1.3 Service principals — the legacy / explicit pattern

Before MI, you used a **service principal** (an Entra app registration with a client ID + client secret or cert). These are still used for cross-tenant scenarios, CI/CD systems outside Azure, and integrations.

Anti-pattern: bake SP client secret into image. Right pattern: store secret in Key Vault, fetch via MI at runtime.

For containers running outside Azure but needing Azure resources: **Federated Identity Credentials** (the Azure equivalent of WIF) — your CI's OIDC token → Azure user-assigned MI → access tokens. No client secret.

---

## 2. Object storage — Azure Blob Storage

Blob Storage has three "blob types":

| Blob type | Use |
|---|---|
| **Block blobs** | Most use cases — files, images, model artifacts |
| **Append blobs** | Log files |
| **Page blobs** | Random read/write, backing for VHDs |

Storage account tiers: Standard (HDD/SSD) and Premium (block blobs SSD-only). For ML data: Premium block blob.

### 2.1 Access patterns

| Pattern | Use case | Notes |
|---|---|---|
| **Azure SDK / boto3-equivalent (azure-storage-blob)** | App-level | Default |
| **blobfuse2** | Mount as filesystem | Microsoft-supported FUSE; better than s3fs's reliability |
| **AzCopy** | Bulk transfer | CLI; performance |
| **NFS 3.0 mount on Blob** | Container fs | Specific account configuration; Premium tier with NFS feature enabled |
| **HDFS protocol via ABFS driver** (ADLS Gen2) | Spark / Databricks | Topic 02 territory |

`blobfuse2` is the production-grade FUSE for Azure Blob:

```bash
blobfuse2 mount /mnt/blob --config-file=/etc/blobfuse2-config.yaml
docker run -v /mnt/blob:/data:ro myimage
```

Config file format auths via MI (no secrets in config):

```yaml
# /etc/blobfuse2-config.yaml
azstorage:
  type: block
  account-name: mystorageacct
  container: ml-data
  mode: msi
  msi:
    resource-id: /subscriptions/.../my-ml-mi
file_cache:
  path: /var/cache/blobfuse2
  timeout-sec: 240
```

For AKS, the **Blob CSI driver** does this declaratively (module 28).

### 2.2 Blob RBAC

Roles (modern, AAD-RBAC; ignore the legacy SAS-token model where possible):

| Role | Grants |
|---|---|
| `Storage Blob Data Reader` | Read blobs |
| `Storage Blob Data Contributor` | Read/write/delete blobs |
| `Storage Blob Data Owner` | Same + ACL management |
| `Storage Account Contributor` | Manage account (not data plane!) |

Assignment is scoped: management-group / subscription / resource-group / account / container / blob-prefix.

```bash
az role assignment create \
  --role "Storage Blob Data Reader" \
  --assignee-object-id $MI_PRINCIPAL_ID \
  --scope "/subscriptions/.../mystorageacct/blobServices/default/containers/ml-data"
```

### 2.3 Encryption

- **Default at rest**: AES-256, Microsoft-managed keys.
- **CMK** via Azure Key Vault — encryption scope per storage account or per blob container.
- **Double encryption** (Microsoft 256-bit AES + your CMK) for compliance.
- **In transit**: TLS 1.2+ required (storage account setting `minimumTlsVersion: TLS1_2`).
- **Storage account firewall**: deny by default; allowlist trusted Azure services + VNet subnets.

### 2.4 Storage account hardening

The defensive baseline (Azure Policy can enforce):

- `minimumTlsVersion: TLS1_2`.
- `supportsHttpsTrafficOnly: true`.
- `allowBlobPublicAccess: false` (anonymous read blocked).
- `allowSharedKeyAccess: false` (forces AAD auth — the strongest setting).
- `networkAcls.defaultAction: Deny` + explicit VNet rules.
- Private endpoint for the storage account; DNS overrides to point to the private IP.
- Diagnostic logs → Log Analytics workspace.

`allowSharedKeyAccess: false` is the **most important** — it disables the storage-account-key auth (the historic "key A and key B" model), forcing all access through AAD. Eliminates a huge class of leaked-key incidents.

### 2.5 ADLS Gen2 = Blob with hierarchical namespace

ADLS Gen2 is Blob with a hierarchical namespace (HNS) enabled. Adds:

- POSIX-style folder hierarchy (not just flat key/value).
- POSIX ACLs alongside RBAC (fine-grained per-folder permissions).
- ABFS driver for Hadoop/Spark/Databricks.

For ML/Spark workloads on Azure, **ADLS Gen2 with HNS is the default**. Topic 02's Databricks corpus goes deeper.

---

## 3. Azure Files — SMB and NFS as a service

Azure Files offers SMB (default) and NFS 4.1 (Premium tier required). Mount on a VM host and bind-mount into container:

```bash
# SMB mount (the common case)
mount -t cifs //mystorageacct.file.core.windows.net/share /mnt/share \
  -o vers=3.1.1,credentials=/etc/smbcreds,uid=10001,gid=10001,iocharset=utf8,nosharesock

# Or with AAD-Kerberos (no static creds)
mount -t cifs //mystorageacct.file.core.windows.net/share /mnt/share \
  -o vers=3.1.1,sec=krb5,iocharset=utf8

docker run -v /mnt/share:/data myimage
```

For NFS 4.1:

```bash
mount -t nfs -o vers=4,minorversion=1,sec=sys mystorageacct.file.core.windows.net:/share /mnt/share
```

Encryption in transit:
- SMB 3.1.1 has end-to-end encryption — enable on the share.
- NFS over Azure Files **does NOT support encryption in transit at the protocol layer** — requires the network to be inside a VNet with private endpoints. Configure storage account to require private endpoints.

For AKS, **Azure Files CSI driver** (module 28).

---

## 4. Azure Disks

Block storage. Tiers:

- **Standard HDD** — cheap.
- **Standard SSD** — better.
- **Premium SSD v2** — high IOPS.
- **Ultra Disk** — premium for high-IOPS DBs.

Attach to VM, format, mount. Same pattern as on-prem block / EBS / PD: not multi-host RWX.

Encryption: Server-Side Encryption (SSE) by default with Microsoft-managed keys. Customer-Managed Keys via Disk Encryption Set (DES) — a resource that pairs an Azure Key Vault key with the disk. **Required for regulated workloads.**

```bash
az disk-encryption-set create --name my-des --resource-group my-rg --source-vault my-kv --key-url $KEY_URL
az disk create --name my-disk --resource-group my-rg --size-gb 100 --disk-encryption-set my-des
```

---

## 5. Azure Key Vault

Azure's managed secret/key/cert store. Three modes:

- **Standard** — software-protected keys.
- **Premium** — HSM-protected keys (FIPS 140-2 Level 2).
- **Managed HSM** — dedicated HSM (FIPS 140-2 Level 3).

For regulated finance, Premium or Managed HSM.

### 5.1 Pattern: container fetches secret from KV via MI

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://my-kv.vault.azure.net/", credential=credential)
db_pass = client.get_secret("db-pass").value
```

`DefaultAzureCredential` walks the credential chain: env vars → managed identity → CLI auth → etc. In a container on a VM with MI attached, it picks up the MI token automatically. No client secret in code, no JSON key on disk.

The KV access policy (or RBAC role assignment) grants the MI `Get` permission on secrets. Least-privilege:

```bash
az keyvault set-policy --name my-kv --object-id $MI_PRINCIPAL_ID --secret-permissions get
# Or via RBAC: az role assignment create --role "Key Vault Secrets User" --assignee-object-id $MI_PRINCIPAL_ID --scope "/subscriptions/.../my-kv"
```

### 5.2 Key Vault references — Azure App Service / Container Apps pattern

For Azure App Service / Container Apps / Functions, you can put `@Microsoft.KeyVault(SecretUri=...)` in env-var definitions. The platform fetches and substitutes at start.

For raw Docker on a VM: write your own bootstrap that fetches and writes to a tmpfs file (module 08).

For AKS: **Key Vault Secrets Store CSI driver** (module 28).

### 5.3 KV networking

- **Private endpoint** for the vault — no public access.
- **Firewall** with allowed VNets if no PE.
- **Soft delete** + **purge protection** — once enabled, secrets can be recovered for 7-90 days even after delete. Regulated requirement.
- **Diagnostic logs** to Log Analytics.

---

## 6. Azure Container Instances (ACI)

ACI is "run a container, no infrastructure." Single-container or pod-of-containers. Used for batch jobs, CI/CD runners, and one-off compute.

### 6.1 Identity in ACI

ACI containers can have a **user-assigned managed identity**:

```bash
az container create \
  --name infer-job \
  --resource-group my-rg \
  --image myacr.azurecr.io/infer:1.0 \
  --assign-identity /subscriptions/.../my-ml-mi \
  --acr-identity   /subscriptions/.../my-acr-pull-mi
```

Two MIs:
- `--acr-identity` — used to pull the image from ACR.
- `--assign-identity` — used by the application code.

`DefaultAzureCredential` in the container picks up `--assign-identity` automatically.

### 6.2 ACI data exposure

- Volume mounts: Azure Files (SMB), GitRepo (deprecated), secret volumes, emptyDir.
- No bind mounts to host (no host concept).
- Outbound networking: through the assigned subnet if you use the `--vnet` flag, otherwise public.
- For private ACI: use the **VNet integration** + private endpoints for everything ACI touches.

### 6.3 Confidential containers on ACI

ACI supports **confidential containers** on AMD SEV-SNP / Intel TDX. The container runs in a hardware-encrypted memory region; even Microsoft operators can't read it. Attestation tokens prove the container runs in a confidential environment before secrets are released.

For PII / regulated workloads, this is a strong primitive — though it adds friction to debugging.

---

## 7. Azure Container Apps

Azure Container Apps (ACA) is a managed Kubernetes-on-the-side serverless container runtime. Used for:

- Microservices that need auto-scaling (KEDA built in).
- Background jobs (Jobs feature).
- Long-running workloads.

ACA's data exposure:

- **Volume mounts**: Azure Files, ephemeral, secrets.
- **Identity**: system or user-assigned MI.
- **Secrets**: native ACA secrets (encrypted, bound to revision) + Key Vault references.
- **Networking**: managed VNet (default) or your VNet; internal-only ingress option.
- **Ingress**: HTTPS endpoint with managed cert; can be internal-only.

ACA is the **Cloud Run analogue on Azure**. Same trade-offs: simple, opinionated, fits HTTP/gRPC/jobs.

---

## 8. ACR — Azure Container Registry

Covered in module 05. For data-exposure purposes:

- Use Premium tier for VNet integration via private endpoint.
- Disable admin user.
- Use AAD/RBAC.
- Attach to AKS via managed identity: `az aks update --attach-acr`.
- Enable image scanning via Microsoft Defender for Cloud.
- ACR Tasks for CI; consider Azure Pipelines or GitHub Actions for sophisticated workflows.

---

## 9. Azure networking primitives for containers

- **VNet** — your virtual network. Containers on VMs / ACI / ACA all live in subnets.
- **NSG (Network Security Group)** — the firewall, applied per-subnet or per-NIC. Default-deny outbound is the regulated baseline.
- **Private Endpoint** — a private IP in your VNet that connects to an Azure PaaS service (Storage, Key Vault, ACR, Cosmos DB, ...). Replaces public endpoints.
- **Service Endpoint** (older) — a route from a subnet to a PaaS service; the PaaS still has a public IP. Private Endpoint is the modern replacement.
- **Azure Firewall** — managed L7 firewall; good for egress filtering with FQDN rules.
- **Application Gateway / Front Door** — L7 load balancer for ingress (WAF included).

### 9.1 The private-everything pattern

For regulated finance:

- Storage account, Key Vault, ACR, Cosmos DB, SQL DB — **all have private endpoints**, all have `publicNetworkAccess: Disabled`.
- VNet subnet for containers has NSG with default-deny outbound + allowlist for the private endpoint subnet.
- DNS: Private DNS Zones override the public DNS for these resources.

---

## 10. Logging

Container logs (stdout/stderr) collected by:

- **Azure Monitor Container Insights** for AKS / ACA.
- **Diagnostic settings** on ACI → Log Analytics.
- **For raw Docker on VMs**: install the **Azure Monitor Agent** + Log Analytics workspace.

Log Analytics workspaces support CMK for encryption at rest. Data Export rules ship logs to Storage for retention.

---

## 11. Azure Policy — the equivalent of Cloud Custodian / Org Policy

Azure Policy enforces resource configuration at scope (subscription / RG / MG). Built-in policies include:

- "Storage accounts should restrict network access."
- "Storage accounts should require minimum TLS version 1.2."
- "Key Vault should have soft delete enabled."
- "Container registries should not allow unrestricted network access."
- "Disks should use customer-managed keys."

Plus you can write **custom policies** in the Azure Policy JSON definition language. Combined with **Deploy-If-Not-Exists** effects, policy auto-remediates.

For Sr Architect interviews: know that Azure Policy is the canonical answer for "how would you enforce X across the subscription," and `Microsoft Defender for Cloud` is the analogue of AWS Security Hub.

---

## 12. The reference architecture for ML containers on Azure (VM-based)

```
┌────────────────────────────────────────────────────────────────────┐
│ VNet (my-vnet)                                                     │
│                                                                    │
│  ┌──────────────────────────┐                                      │
│  │ VM Scale Set             │                                      │
│  │ user-assigned MI         │                                      │
│  │ + Docker rootless        │                                      │
│  │ + iptables: drop IMDS    │                                      │
│  │   from containers        │                                      │
│  │ + custom-script: bootstrap│                                     │
│  │   secret to tmpfs        │                                      │
│  └──────┬───────────────────┘                                      │
│         │ NSG (default-deny egress + allowlist via PE subnet)      │
│         │                                                          │
│  ┌──────▼───────────────────────────────────────────────────┐      │
│  │ Private Endpoint subnet                                  │      │
│  └──────┬────────────────────────────────────────────────────┘     │
│         │                                                          │
└─────────┼──────────────────────────────────────────────────────────┘
          │ Private endpoint links (per resource)
   ┌──────▼──────┐    ┌──────────────┐   ┌──────────────┐
   │ Storage Acct│    │ Key Vault    │   │ ACR (Premium)│
   │ + CMK       │    │ + HSM        │   │ + PE         │
   │ + shared-key│    │ + purge prot │   │ + admin off  │
   │   DISABLED  │    │ + PE         │   │              │
   │ + PE        │    │              │   │              │
   └─────────────┘    └──────────────┘   └──────────────┘
```

Cross-cuts:

- **Image source**: ACR with private endpoint.
- **Identity**: user-assigned MI per workload.
- **Secrets**: Key Vault references via MI.
- **Egress**: NSG default-deny + Azure Firewall for FQDN allowlist.
- **Audit**: diagnostic settings → Log Analytics with CMK.
- **Posture**: Microsoft Defender for Cloud + Azure Policy.

---

## 13. Capital One angle for Azure

Capital One is AWS, not Azure. But Optum (the user's current employer) is **Microsoft Azure heavy**. The user has authored extensive Azure-Databricks material already (Topic 02). For an architect interview, framing Azure-fluency as a **transferable skill** ("I designed the Azure-native ML platform at Optum and can apply the same principles to AWS") plays well.

The Azure→AWS translation:

| Azure | AWS |
|---|---|
| Managed Identity | IAM Role + STS / IRSA |
| Microsoft Entra Workload ID | EKS Pod Identity |
| Azure Key Vault | AWS Secrets Manager + KMS |
| Blob Storage / ADLS Gen2 | S3 |
| Azure Files | EFS |
| Azure Disks | EBS |
| ACR | ECR |
| ACI / Container Apps | ECS Fargate / App Runner |
| AKS | EKS |
| Azure Policy | Cloud Custodian + SCPs + Config |
| Private Endpoint | VPC Endpoint (Interface) |
| Microsoft Defender for Cloud | Security Hub + GuardDuty + Inspector |

---

## Sanity check

1. Why is `allowSharedKeyAccess: false` the most security-impactful Azure storage account setting?
2. System-assigned vs user-assigned managed identity — name two scenarios where user-assigned is the right call.
3. What does `DefaultAzureCredential` actually do under the hood, and why is it the recommended pattern?
4. NFS 4.1 over Azure Files doesn't encrypt in transit. How do regulated shops compensate?
5. What's a Disk Encryption Set (DES), and why is it needed for CMK on Azure Disks?
6. Name the Azure equivalent of: VPC endpoint, Org Policy, IAM Role, S3, EFS, Cloud Custodian.

---

## Sources

- [Managed Identities](https://learn.microsoft.com/azure/active-directory/managed-identities-azure-resources/overview)
- [Federated Identity Credentials](https://learn.microsoft.com/entra/workload-id/workload-identity-federation)
- [Azure Blob Storage](https://learn.microsoft.com/azure/storage/blobs/)
- [blobfuse2](https://github.com/Azure/azure-storage-fuse)
- [ADLS Gen2](https://learn.microsoft.com/azure/storage/blobs/data-lake-storage-introduction)
- [Azure Files](https://learn.microsoft.com/azure/storage/files/)
- [Azure Disks](https://learn.microsoft.com/azure/virtual-machines/managed-disks-overview)
- [Azure Key Vault](https://learn.microsoft.com/azure/key-vault/)
- [Azure Container Instances](https://learn.microsoft.com/azure/container-instances/)
- [Azure Container Apps](https://learn.microsoft.com/azure/container-apps/)
- [Confidential containers on ACI](https://learn.microsoft.com/azure/container-instances/container-instances-confidential-overview)
- [Azure Policy](https://learn.microsoft.com/azure/governance/policy/)
- [Microsoft Defender for Cloud](https://learn.microsoft.com/azure/defender-for-cloud/)

→ Next: [16 — K8s architecture — control plane, kubelet, kube-proxy, etcd, CRDs](16_k8s_architecture.md)
