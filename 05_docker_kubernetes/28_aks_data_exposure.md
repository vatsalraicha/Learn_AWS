# 28 — AKS deep: Entra Workload ID, Azure Files / Disk / Blob CSI, Key Vault CSI, private clusters

## Why this module exists

AKS is Optum's K8s and the K8s flavor the user has the strongest existing exposure to (Topic 02). This module covers the AKS-specific data primitives — what the user already knows in production, with explicit framing as the AKS counterpart of the EKS module.

---

## 1. Identity — Microsoft Entra Workload ID

GA July 2023. Replaces the deprecated AAD Pod Identity v1.

### 1.1 The model

1. AKS cluster has an OIDC issuer URL.
2. You create a **user-assigned managed identity** in Entra.
3. You add a **federated identity credential** on the MI that trusts the cluster's OIDC issuer + a specific KSA.
4. KSA annotated with the MI's client ID.
5. Pod uses the KSA; `DefaultAzureCredential` picks up the federated token via the projected SA token.

```bash
# Create a managed identity
az identity create --name ml-infer-mi --resource-group my-rg

# Configure federated credential
az identity federated-credential create \
  --name ml-infer-fc \
  --identity-name ml-infer-mi \
  --resource-group my-rg \
  --issuer $(az aks show -n prod -g my-rg --query oidcIssuerProfile.issuerUrl -o tsv) \
  --subject system:serviceaccount:ml-serving:infer-server
```

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: infer-server
  namespace: ml-serving
  annotations:
    azure.workload.identity/client-id: <MI client ID>
  labels:
    azure.workload.identity/use: "true"
```

Pod gets env vars `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_FEDERATED_TOKEN_FILE`. The Azure SDK exchanges the federated token for an MI access token. No client secret.

---

## 2. Azure Disk CSI — block storage

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata: { name: managed-premium-cmk }
provisioner: disk.csi.azure.com
parameters:
  skuName: Premium_LRS
  diskEncryptionSetID: /subscriptions/.../diskEncryptionSets/my-des
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
reclaimPolicy: Retain
```

Disk Encryption Set (DES) pairs an Azure Key Vault key with disks for CMK encryption at rest.

For ML serving / databases / vector indices: Premium SSD v2 or Ultra Disk.

---

## 3. Azure Files CSI — RWX

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata: { name: azurefile-csi-premium }
provisioner: file.csi.azure.com
parameters:
  skuName: Premium_LRS
  protocol: nfs                # or "smb"
allowVolumeExpansion: true
```

SMB 3.1.1 by default; NFSv4.1 with Premium tier + the `nfs` protocol parameter.

For ML training where many pods read the same data: Azure Files Premium NFS. Less performant than Lustre but managed.

---

## 4. Azure Blob CSI — object storage as a volume

[Azure Blob CSI](https://learn.microsoft.com/azure/aks/azure-blob-csi):

- **blobfuse2** mount mode — FUSE; POSIX-friendly.
- **NFS 3.0** mount mode — kernel-level mount; faster but limited semantics.

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata: { name: training-data }
spec:
  storageClassName: azureblob-fuse-premium
  accessModes: [ReadWriteMany]
  resources: { requests: { storage: 100Gi } }
```

For ML training data: blobfuse2 mode is what you want. Modeled on the same pattern as GCS Fuse / Mountpoint-S3.

---

## 5. Azure Key Vault Provider for Secrets Store CSI

```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata: { name: db-creds, namespace: ml-serving }
spec:
  provider: azure
  parameters:
    usePodIdentity: "false"
    useVMManagedIdentity: "false"
    clientID: <workload-identity-client-id>
    keyvaultName: my-kv
    cloudName: AzurePublicCloud
    objects: |
      array:
        - |
          objectName: db-password
          objectType: secret
          objectVersion: ""
    tenantId: <tenant-id>
  secretObjects:                               # optional: sync to native K8s Secret
    - secretName: db-creds-k8s
      type: Opaque
      data: [{ key: db_password, objectName: db-password }]
```

The `secretObjects` block creates a native K8s Secret for env-var-style consumption while also mounting the file.

---

## 6. Private clusters

```bash
az aks create --name prod --resource-group my-rg \
  --enable-private-cluster \
  --enable-managed-identity \
  --network-plugin azure \
  --network-plugin-mode overlay \
  --network-policy cilium \
  --enable-oidc-issuer \
  --enable-workload-identity
```

Private cluster = API server has no public IP. Reached via:
- VNet peering from a jumpbox.
- VPN / ExpressRoute.
- AKS Private Link.

For regulated workloads, this is mandatory. Pair with Azure Bastion for human admin access.

---

## 7. Azure CNI flavors

- **Kubenet** — deprecated path; overlay-style.
- **Azure CNI Overlay** — overlay model with VNet-routable pod IPs via NAT.
- **Azure CNI Pod Subnet** — each pod gets a real VNet IP (analogous to AWS VPC CNI). Limited pod density per node.
- **Azure CNI Powered by Cilium** — Cilium eBPF dataplane. The modern default.

For modern AKS: pick **Azure CNI Powered by Cilium**. Gets you NetworkPolicy + L7 visibility + kube-proxy replacement.

---

## 8. Confidential containers on AKS

Confidential Containers on AKS uses **Kata Containers** + **AMD SEV-SNP** to give per-pod VM isolation with memory encryption. For PII / regulated processing:

```yaml
spec:
  runtimeClassName: kata-cc-isolation
```

Comparable to GCP Confidential GKE Nodes and AWS Nitro Enclaves (in spirit, though Nitro is different in execution).

---

## 9. ACR integration

```bash
az aks update --name prod --resource-group my-rg --attach-acr myacr
```

Adds `AcrPull` role to the kubelet identity. Image pulls "just work."

For private network setups: ACR Premium with Private Endpoint + Private DNS Zone.

---

## 10. The reference AKS+KServe architecture (the parallel of EKS)

```
┌──────────────────────────────────────────────────────────────────┐
│ AKS (private cluster, KMS etcd, OIDC issuer enabled)             │
│                                                                  │
│  ml-serving namespace                                            │
│   ServiceAccount (workload-identity/client-id annotated)         │
│   InferenceService (KServe)                                      │
│   PSA: restricted                                                │
└────────┬────────────────┬──────────────────┬────────────────────┘
         │                │                  │
   ┌─────▼─────┐    ┌─────▼─────┐      ┌─────▼─────┐
   │ ACR       │    │ Blob/Files│      │ Key Vault │
   │ Premium   │    │ + CMK     │      │ + HSM     │
   │ + PE      │    │ + PE      │      │ + PE      │
   └───────────┘    └───────────┘      └───────────┘
```

Cross-cuts:
- **Identity**: Entra Workload ID per workload.
- **Egress**: NSG default-deny + Azure Firewall.
- **Admission**: Kyverno + Defender for Cloud signals.
- **Audit**: K8s audit → Log Analytics + Microsoft Sentinel.

---

## Sanity check

1. AKS Workload ID uses what kind of federated credential under the hood?
2. Azure Files SMB vs NFSv4.1 — when does each fit?
3. Why does Azure Blob CSI offer two modes (blobfuse2 vs NFS 3.0), and when do you pick each?
4. What does a **private AKS cluster** mean exactly, and how do humans reach the API server?
5. Confidential Containers on AKS — what hardware feature underpins them?
6. Map: AWS EFS → Azure ?, AWS Secrets Manager → Azure ?, IRSA → Azure ?

---

## Sources

- [Microsoft Entra Workload ID for AKS](https://learn.microsoft.com/azure/aks/workload-identity-overview)
- [Azure Disk CSI](https://learn.microsoft.com/azure/aks/azure-disk-csi)
- [Azure Files CSI](https://learn.microsoft.com/azure/aks/azure-files-csi)
- [Azure Blob CSI](https://learn.microsoft.com/azure/aks/azure-blob-csi)
- [Azure Key Vault Provider for Secrets Store CSI](https://learn.microsoft.com/azure/aks/csi-secrets-store-driver)
- [Private clusters](https://learn.microsoft.com/azure/aks/private-clusters)
- [Azure CNI Powered by Cilium](https://learn.microsoft.com/azure/aks/azure-cni-powered-by-cilium)
- [Confidential Containers on AKS](https://learn.microsoft.com/azure/aks/confidential-containers-overview)

→ Next: [29 — **On-prem K8s — Rook-Ceph, Longhorn, Velero, Vault, MetalLB, air-gap**](29_onprem_k8s_data.md)
