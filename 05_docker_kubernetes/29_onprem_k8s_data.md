# 29 — On-prem K8s: Rook-Ceph, Longhorn, OpenEBS, Portworx, Velero, Vault, MetalLB, air-gap

## Why this module exists

On-prem K8s requires you to bring everything yourself. Storage, load balancing, identity, secrets, registry, networking — all you. This module covers the dominant CNCF + commercial choices.

---

## 1. Distro selection

| Distro | License | Notes |
|---|---|---|
| **kubeadm** | Apache 2.0 | The canonical bootstrap; bring everything yourself |
| **Kubespray** | Apache 2.0 | Ansible-based; deploys kubeadm cluster with addons |
| **Rancher RKE2** | Apache 2.0 | Hardened; CIS-K8s compliant by default; FIPS option |
| **K3s** (SUSE) | Apache 2.0 | Lightweight; single binary; edge/IoT |
| **Talos** | MPL | Immutable OS; declarative; minimal attack surface |
| **OpenShift** (Red Hat) | Commercial | Most opinionated; tightly integrated; Operators-first |
| **Tanzu Kubernetes Grid** (VMware/Broadcom) | Commercial | VMware-aligned |
| **Mirantis Kubernetes Engine** | Commercial | (was Docker EE) |

For ML on-prem: **OpenShift** at regulated enterprises that already pay for it; **RKE2** for self-managed regulated finance; **Talos** for the security-pure shop.

---

## 2. Storage — the heart of on-prem K8s

The CSI ecosystem on-prem:

| Driver | Backend | Notes |
|---|---|---|
| **Rook-Ceph** | Ceph | CNCF Graduated; runs Ceph as K8s CRs (CephCluster, CephBlockPool, CephObjectStore, CephFilesystem). Heavy ops; powerful. |
| **Longhorn** | Per-node disks | CNCF Incubating (Rancher origin). Cluster-internal block storage; replicates across nodes. Simpler than Ceph. |
| **OpenEBS Mayastor** | NVMe over fabrics | CNCF Sandbox. Best perf for NVMe SSDs. |
| **OpenEBS cStor / Jiva** | Local disks | Mature OSS engines; cStor uses ZFS underneath. |
| **Portworx** | Per-node + commercial | Pure Storage product. Storage classes, replication, snapshots, DR. |
| **NetApp Trident** | NetApp appliances | If you have NetApp, use this. |
| **Pure Service Orchestrator** | Pure Storage FlashArray | Pure's CSI. |
| **Dell PowerStore / Dell EMC PowerScale CSI** | Dell appliances | If you have Dell. |

For ML on-prem: existing storage appliances (NetApp / Dell / Pure) → use their CSI. Greenfield with budget → Portworx. Greenfield with OSS → Rook-Ceph if you have ops staff; Longhorn if you don't.

### 2.1 Rook-Ceph example

```yaml
apiVersion: ceph.rook.io/v1
kind: CephCluster
metadata: { name: rook-ceph, namespace: rook-ceph }
spec:
  cephVersion: { image: quay.io/ceph/ceph:v18.2.4 }
  dataDirHostPath: /var/lib/rook
  mon: { count: 3, allowMultiplePerNode: false }
  mgr: { count: 2 }
  storage:
    useAllNodes: true
    useAllDevices: false
    deviceFilter: nvme[0-9]+n1
  network:
    provider: host                    # for performance
  resources:
    osd: { requests: { cpu: 2, memory: 4Gi }, limits: { memory: 8Gi } }
---
apiVersion: ceph.rook.io/v1
kind: CephBlockPool
metadata: { name: replicapool, namespace: rook-ceph }
spec:
  failureDomain: host
  replicated: { size: 3 }
---
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata: { name: ceph-block }
provisioner: rook-ceph.rbd.csi.ceph.com
parameters:
  pool: replicapool
  clusterID: rook-ceph
  imageFormat: "2"
  imageFeatures: layering
  csi.storage.k8s.io/provisioner-secret-name: rook-csi-rbd-provisioner
  # ...
reclaimPolicy: Retain
```

Yields a `ceph-block` StorageClass that backs PVCs with replicated Ceph RBD volumes. CephFS pools for RWX file. CephObjectStore for S3-compatible (RGW).

---

## 3. Local PV — for high-IOPS workloads

```yaml
apiVersion: v1
kind: PersistentVolume
metadata: { name: nvme-node-1 }
spec:
  capacity: { storage: 2Ti }
  volumeMode: Filesystem
  accessModes: [ReadWriteOnce]
  persistentVolumeReclaimPolicy: Retain
  storageClassName: local-nvme
  local: { path: /mnt/nvme-1 }
  nodeAffinity:
    required:
      nodeSelectorTerms:
        - matchExpressions:
            - { key: kubernetes.io/hostname, operator: In, values: [node-1] }
```

Local PVs are essential for ML training intermediate state, where 10–100 GB of fast NVMe per node beats any networked option. Combine with the **local-path-provisioner** (Rancher) or `sig-storage-local-static-provisioner` for declarative use.

---

## 4. Backups — Velero

```yaml
apiVersion: velero.io/v1
kind: Schedule
metadata: { name: nightly, namespace: velero }
spec:
  schedule: "0 2 * * *"
  template:
    includedNamespaces: ["ml-serving", "ml-training", "data-pipeline"]
    snapshotVolumes: true
    ttl: 720h
    storageLocation: minio-default
    volumeSnapshotLocations: [csi-default]
```

Velero backs up:
- K8s manifests (resources).
- PV data via **CSI snapshots** + restic for non-snapshot-capable volumes.

Target: S3-compatible (MinIO on-prem, AWS S3, Azure Blob, GCS).

Restore tested quarterly. If your cluster nukes itself, Velero is the difference between "8-hour fire drill" and "8-week reconstruction."

---

## 5. Vault on K8s

Vault HA on K8s:

```bash
helm install vault hashicorp/vault \
  --set server.ha.enabled=true \
  --set server.ha.raft.enabled=true \
  --set server.ha.replicas=5
```

5 replicas with Raft = quorum 3. Auto-unseal via cloud KMS or transit auto-unseal from another Vault.

Auth methods relevant for K8s:
- **Kubernetes auth** — pod's projected SA token authenticates to Vault.
- **AppRole** — for non-K8s callers.
- **TLS cert** — for the most security-sensitive cases.

Apps consume via:
- **Vault Agent Injector** (annotation-driven sidecar).
- **Vault CSI Provider**.
- **External Secrets Operator with Vault backend**.

For on-prem regulated finance: Vault is the standard. Topic 04 covered Cloud Custodian; on-prem the secret-management spine is Vault.

---

## 6. MetalLB — bare-metal LoadBalancer

K8s `Service type=LoadBalancer` calls a cloud-provider integration to provision an ELB/GCP-LB/Azure-LB. On-prem there's no such thing. **MetalLB** is the answer.

Two modes:

- **Layer 2** — MetalLB pods on each node ARP-respond for the assigned IPs. Simple; one node is "active" per IP.
- **BGP** — MetalLB advertises routes via BGP to upstream switches. Multi-active; load-balanced across nodes.

```yaml
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata: { name: default, namespace: metallb-system }
spec:
  addresses: ["10.0.100.50-10.0.100.100"]
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata: { name: default, namespace: metallb-system }
spec:
  ipAddressPools: [default]
```

Alternative: **kube-vip** (similar) or **Cilium L2 announcements** (Cilium 1.14+; cleanest if you're already running Cilium).

---

## 7. Air-gapped K8s

The full air-gap setup:

- **Registry mirror**: Harbor with the upstream-mirroring config. Allowlist of upstream registries; sync via secure DMZ "diode."
- **Container runtime config**: containerd mirror rules in `/etc/containerd/config.toml` to redirect all pulls to your Harbor.
- **Helm chart repo**: Harbor's Helm OCI artifact storage.
- **PyPI mirror**: Sonatype Nexus / JFrog Artifactory / pypiserver.
- **OS package mirror**: apt/yum proxy.
- **Cert authority**: internal PKI; CA bundle baked into base images.
- **DNS**: internal resolver; no public DNS.
- **Time sync**: internal NTP.
- **Validation**: CI runs in a network-isolated namespace before pulling new artifacts.

The Cosign verification gets harder air-gapped: Rekor is public. Either:
- Mirror Rekor (advanced); or
- Use Cosign keyed signing with a key from internal KMS / HSM and skip Rekor.
- Or trust attestations within a known-pinned set without verifying Sigstore log.

---

## 8. Identity on-prem

Without cloud IAM, the K8s identity-binding for "talk to Vault / talk to MinIO / talk to internal services" is:

- **K8s ServiceAccount with projected tokens** + **SPIFFE/SPIRE** for federation.
- **Vault as the broker**: SA → Vault K8s auth → Vault returns dynamic creds for MinIO / DB / API.
- **mTLS via cert-manager** with an internal CA — every workload has a cert; mTLS is the identity.

SPIFFE/SPIRE is the gold standard but op-heavy. For most on-prem K8s shops: Vault-as-broker + service mesh mTLS (Istio with SPIRE under the hood, or Linkerd's built-in identity) is the practical answer.

---

## 9. The reference on-prem K8s ML architecture

```
┌──────────────────────────────────────────────────────────────────┐
│ K8s cluster (RKE2, Talos, or OpenShift)                          │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ ml-serving (PSA restricted, NetworkPolicy default-deny)    │  │
│  │   KSA → Vault K8s auth → dynamic creds                     │  │
│  │   KServe InferenceService                                  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ kube-system  (privileged)                                  │  │
│  │   Cilium, MetalLB/cilium-L2, Rook-Ceph operator, Velero    │  │
│  │   cert-manager, Vault Agent Injector, Falco                │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
└──────────────┬──────────────┬─────────────────┬─────────────────┘
               │              │                 │
        ┌──────▼──────┐ ┌─────▼─────┐    ┌──────▼──────┐
        │ Rook-Ceph   │ │ Vault HA  │    │ Harbor      │
        │ Block/FS/RGW│ │ + HSM     │    │ + Trivy     │
        │ + LUKS OSDs │ │ + KV+Tran │    │ + Cosign    │
        └─────────────┘ └───────────┘    └─────────────┘
```

Cross-cuts:
- **Identity**: K8s SA + Vault K8s auth + (optional) SPIFFE/SPIRE.
- **Storage**: Rook-Ceph (or NetApp Trident / Portworx if the appliance is there).
- **Secrets**: Vault Agent / CSI / ESO.
- **Registry**: Harbor with image signing.
- **Backup**: Velero with MinIO/Ceph RGW.
- **Audit**: K8s audit log + Falco → on-prem SIEM (Splunk, Elastic).

---

## 10. The "do we even need on-prem K8s?" question

For Capital One: no — they're 100% AWS. For Optum / regulated healthcare / sovereign-data shops: yes. For the user's career: knowing on-prem deeply is a multiplier on cloud knowledge.

The architect-grade summary: **on-prem K8s is K8s where you pay for the abstractions cloud gave you for free.** The patterns are identical; the operators do the heavy lifting.

---

## Sanity check

1. Rook-Ceph vs Longhorn — name two reasons to pick each.
2. Why is **Local PV** the right primitive for ML training intermediate state and the wrong primitive for application persistence?
3. Velero's role — what does it actually back up, and where does it store backups?
4. MetalLB Layer 2 vs BGP — when to use each?
5. Air-gapped K8s breaks Cosign keyless signing. What are the two workaround patterns?
6. Without cloud IAM, what's the on-prem "identity broker" pattern?

---

## Sources

- [Rook-Ceph](https://rook.io/docs/rook/)
- [Longhorn](https://longhorn.io/docs/)
- [OpenEBS](https://openebs.io/docs/)
- [Portworx](https://docs.portworx.com/)
- [NetApp Trident](https://docs.netapp.com/us-en/trident/)
- [Velero](https://velero.io/docs/)
- [HashiCorp Vault on K8s](https://developer.hashicorp.com/vault/docs/platform/k8s)
- [MetalLB](https://metallb.io/)
- [cilium L2 announcements](https://docs.cilium.io/en/stable/network/l2-announcements/)
- [Talos Linux](https://www.talos.dev/)
- [Rancher RKE2](https://docs.rke2.io/)

→ Next: [30 — Model serving on K8s — KServe, Seldon, BentoML, Triton, vLLM, Ray Serve](30_model_serving_k8s.md)
