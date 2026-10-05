# 19 — Storage in K8s: PV, PVC, StorageClass, CSI, ephemeral, projected

## Why this module exists

K8s storage is layered. Apps request via **PVC**; a **PV** is the actual storage; a **StorageClass** is the parametrized recipe; a **CSI driver** is the cloud/storage integration. Knowing where each layer fits unblocks every "my pod can't mount X" debugging session.

---

## 1. The 4-tuple — PVC, PV, StorageClass, CSI

```
Pod        →  uses        →  PVC (a claim, namespaced)
PVC        →  binds to    →  PV  (cluster-scoped, real storage)
PV         →  created by  →  StorageClass + provisioner
Provisioner →  is part of →  CSI driver (in-tree drivers all migrated out by 2024-2025)
```

A user creates a PVC. The PVC binds to a PV. If `volumeBindingMode: WaitForFirstConsumer`, the PV isn't provisioned until a pod actually claims the PVC — important for topology (you want the PV in the AZ of the scheduled pod).

---

## 2. PVC example

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata: { name: model-cache, namespace: ml-serving }
spec:
  storageClassName: gp3
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 50Gi
```

`accessModes`:

- **ReadWriteOnce (RWO)** — single node mount. EBS, GCE PD, Azure Disk.
- **ReadWriteOncePod (RWOP, GA 1.29)** — single pod mount (stricter).
- **ReadWriteMany (RWX)** — multiple nodes. EFS, Azure Files, GCS Fuse, Filestore, NFS.
- **ReadOnlyMany (ROX)** — read-only mount on multiple nodes.

For ML training (8+ pods reading same data) → RWX. For DB data (StatefulSet) → RWO.

---

## 3. StorageClass — the recipe

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata: { name: gp3 }
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  encrypted: "true"
  kmsKeyId: "arn:aws:kms:us-east-1:123456789012:key/abc..."
volumeBindingMode: WaitForFirstConsumer
reclaimPolicy: Delete
allowVolumeExpansion: true
```

`reclaimPolicy: Delete` — delete the underlying storage when PVC is deleted. **For prod data: use `Retain`** so an accidental PVC delete doesn't wipe the disk; you reclaim manually.

`allowVolumeExpansion: true` — lets you `kubectl edit pvc` to grow the volume online (most CSI drivers support).

`volumeBindingMode: WaitForFirstConsumer` — delays provisioning until a pod schedules to a specific AZ. **Always use this on cloud disks** (otherwise PV may land in wrong AZ).

---

## 4. CSI — the plug-in spec

Container Storage Interface. Every storage backend ships a driver. Two pods per driver:

- **Controller** (one or two replicas, often as a Deployment): handles provisioning (CreateVolume API call), attach/detach orchestration, snapshot.
- **Node** (DaemonSet): runs on every node, handles mounting on demand.

Common drivers:

| Cloud | Driver | Notes |
|---|---|---|
| AWS | ebs.csi.aws.com | EBS (RWO) |
| AWS | efs.csi.aws.com | EFS (RWX) |
| AWS | fsx.csi.aws.com | FSx for Lustre |
| AWS | s3.csi.aws.com | Mountpoint for S3 |
| GCP | pd.csi.storage.gke.io | PD (RWO) |
| GCP | filestore.csi.storage.gke.io | Filestore (RWX) |
| GCP | gcs.csi.storage.gke.io | GCS Fuse |
| Azure | disk.csi.azure.com | Azure Disk (RWO) |
| Azure | file.csi.azure.com | Azure Files (RWX) |
| Azure | blob.csi.azure.com | Azure Blob |
| On-prem | rook-ceph.rbd.csi.ceph.com | Ceph RBD |
| On-prem | longhorn.io | Longhorn |
| On-prem | mayastor.openebs.io | OpenEBS Mayastor |
| On-prem | portworx.io | Portworx |

`kubectl get csidrivers` lists what's installed.

---

## 5. Ephemeral volumes — the underused category

Not everything needs to persist. Three ephemeral types:

### 5.1 `emptyDir`

Allocated on the node, gone when pod is gone. Default backed by node disk:

```yaml
volumes:
  - name: scratch
    emptyDir: { sizeLimit: 50Gi }
```

For RAM-backed (tmpfs):

```yaml
volumes:
  - name: tmpfs-scratch
    emptyDir: { medium: Memory, sizeLimit: 8Gi }
```

For ML: `emptyDir: { medium: Memory }` is essential for PyTorch DataLoader `/dev/shm` problem — without it, you get those "Bus error" crashes from module 09.

### 5.2 Generic ephemeral volumes

PVC-backed but lifetime is bound to the pod:

```yaml
volumes:
  - name: temp-pvc
    ephemeral:
      volumeClaimTemplate:
        spec:
          accessModes: [ReadWriteOnce]
          storageClassName: gp3
          resources: { requests: { storage: 100Gi } }
```

Used for: per-pod scratch on a real PV (e.g., 500Gi NVMe for training intermediate data).

### 5.3 CSI ephemeral volumes

CSI drivers can expose ephemeral inline (no PVC). The Secret Store CSI driver (modules 20, 26-28) is the canonical example.

---

## 6. Projected volumes — secrets, configmaps, SA tokens

Project multiple sources into one volume:

```yaml
volumes:
  - name: app-config
    projected:
      sources:
        - configMap:
            name: app-cm
            items: [{ key: app.yaml, path: config/app.yaml }]
        - secret:
            name: app-secret
            items: [{ key: token, path: secrets/token }]
        - serviceAccountToken:
            audience: api.internal.example.com
            expirationSeconds: 3600
            path: token/sa-token
        - downwardAPI:
            items:
              - path: meta/podname
                fieldRef: { fieldPath: metadata.name }
```

The `serviceAccountToken` projection (GA 1.20) is the modern pattern: short-lived (1-hour default), audience-scoped tokens — exactly what cloud IAM federation needs (IRSA, Workload Identity).

---

## 7. CSI snapshots & restore

Most production CSI drivers support snapshots:

```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata: { name: training-data-2026-05-21 }
spec:
  volumeSnapshotClassName: ebs-snap
  source:
    persistentVolumeClaimName: training-data
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata: { name: training-data-restore }
spec:
  storageClassName: gp3
  accessModes: [ReadWriteOnce]
  dataSource:
    name: training-data-2026-05-21
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
  resources: { requests: { storage: 100Gi } }
```

Velero builds on this for cluster-wide backup (module 29).

---

## 8. Local PVs

A `local` PV is a node-local disk, statically provisioned. Used for:

- High-perf NVMe attached to a node (databases, ClickHouse, vector indices).
- Distributed-storage systems (Cassandra, ScyllaDB, OpenSearch).

```yaml
apiVersion: v1
kind: PersistentVolume
metadata: { name: nvme-1 }
spec:
  capacity: { storage: 1Ti }
  volumeMode: Filesystem
  accessModes: [ReadWriteOnce]
  persistentVolumeReclaimPolicy: Retain
  storageClassName: local-nvme
  local: { path: /mnt/disks/nvme-1 }
  nodeAffinity:
    required:
      nodeSelectorTerms:
        - matchExpressions:
            - { key: kubernetes.io/hostname, operator: In, values: [node-1] }
```

Pods using this PV will only schedule to `node-1` — local storage doesn't move with pods.

---

## 9. Common gotchas

- **`volumeBindingMode: Immediate`** (the default in old StorageClasses) creates a PV before pod is scheduled — often in the wrong AZ. **Always use `WaitForFirstConsumer`**.
- **Pod can't write to a mounted volume** — UID mismatch. Set `fsGroup` in pod security context to chown.
- **`fsGroup` on a 10TB EFS** — chown'ing 10M files takes forever. Use `fsGroupChangePolicy: OnRootMismatch` (GA 1.23+) to only fix the root.
- **Stuck terminating PVC** — finalizer not removed. `kubectl patch pvc <name> -p '{"metadata":{"finalizers":null}}'`.
- **CSI driver pod evicted** — your storage operations grind to a halt. Pin CSI drivers as `priorityClassName: system-node-critical`.

---

## 10. The Capital One signal

For regulated finance ML on EKS:
- EBS CSI with CMK encryption + `reclaimPolicy: Retain`.
- EFS CSI for shared training data + Access Points for multi-tenancy.
- FSx for Lustre CSI for high-perf training (1k+ GPU).
- Mountpoint-for-S3 CSI for cold training data read.
- Velero for backup.
- Cloud Custodian / Kyverno policy: "no PVC without `storageClassName`" / "no PVC without `Retain` policy in prod."

Module 26 has the full EKS deep dive.

---

## Sanity check

1. Why is `volumeBindingMode: WaitForFirstConsumer` mandatory on cloud disks?
2. RWO vs RWOP — when do you actually need RWOP?
3. The PyTorch DataLoader bug is fixed by which exact `emptyDir` setting?
4. Why does `fsGroup` need `fsGroupChangePolicy: OnRootMismatch` on large EFS volumes?
5. A `local` PV is rigidly bound to one node — what does that mean for pod scheduling?
6. CSI driver controller vs node — which is a Deployment, which is a DaemonSet, and what does each do?

---

## Sources

- [PV / PVC concepts](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)
- [Storage Classes](https://kubernetes.io/docs/concepts/storage/storage-classes/)
- [CSI](https://kubernetes-csi.github.io/docs/)
- [VolumeSnapshot](https://kubernetes.io/docs/concepts/storage/volume-snapshots/)
- [Projected Volumes](https://kubernetes.io/docs/concepts/storage/projected-volumes/)
- [Ephemeral Volumes](https://kubernetes.io/docs/concepts/storage/ephemeral-volumes/)

→ Next: [20 — ConfigMaps & Secrets — etcd encryption-at-rest, sealed-secrets, external-secrets](20_configmap_secrets.md)
