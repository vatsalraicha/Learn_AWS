# 68 — Volumes — PV / PVC / SC + HostPath + emptyDir

## 1. The K8s storage layer

```
StorageClass (SC) — "how to provision a PV when asked"
  ↓ (defines provisioner)
PersistentVolume (PV) — "an actual chunk of storage backed by something real"
  ↓ (bound to)
PersistentVolumeClaim (PVC) — "user's request for storage"
  ↓ (mounted by)
Pod
```

## 2. emptyDir — ephemeral pod-scoped

Lives for pod's lifetime. Lost on pod deletion. Used for:
- Sidecar ↔ main container shared scratch
- Cache that survives container restart but not pod restart
- Stream buffer

```yaml
volumes:
- name: cache
  emptyDir:
    sizeLimit: 1Gi              # K8s 1.27+ accounts against ephemeral storage
    medium: Memory              # tmpfs — faster, counts against memory limit
```

## 3. HostPath — mount a host path

Maps a directory from the node into the pod. Dangerous: pod escape risk, breaks if pod moves to another node.

```yaml
volumes:
- name: data
  hostPath:
    path: /data/myapp
    type: DirectoryOrCreate
```

Used for:
- Logging agents reading `/var/log/`
- Monitoring agents reading `/proc/` or `/sys/`
- Local development (Minikube)

For CKA tasks: know how to mount it. For production: avoid.

## 4. PV / PVC — persistent storage

```yaml
# Admin creates a PV
apiVersion: v1
kind: PersistentVolume
metadata: { name: pv-1 }
spec:
  capacity: { storage: 10Gi }
  accessModes: [ReadWriteOnce]
  persistentVolumeReclaimPolicy: Retain
  storageClassName: standard
  hostPath: { path: /mnt/data }       # backing storage
```

```yaml
# User creates a PVC requesting storage
apiVersion: v1
kind: PersistentVolumeClaim
metadata: { name: data, namespace: my-app }
spec:
  accessModes: [ReadWriteOnce]
  storageClassName: standard
  resources:
    requests: { storage: 5Gi }
```

```yaml
# Pod mounts the PVC
spec:
  containers:
  - name: app
    image: my-app
    volumeMounts:
    - { name: data, mountPath: /var/lib/app }
  volumes:
  - name: data
    persistentVolumeClaim: { claimName: data }
```

K8s binds the PVC to a PV that matches (size + accessMode + storageClass).

## 5. Access modes

| Mode | Means |
|---|---|
| **ReadWriteOnce (RWO)** | One node can mount RW (multiple pods on that node OK) |
| **ReadOnlyMany (ROX)** | Many nodes can mount RO |
| **ReadWriteMany (RWX)** | Many nodes can mount RW (NFS / EFS / CephFS, not EBS) |
| **ReadWriteOncePod (RWOP)** | Only one pod can mount (K8s 1.27+ GA) |

Cloud reality:
- EBS = RWO only
- EFS / FSx for Lustre = RWX
- GCS Fuse / Azure Files = RWX
- Local SSD = RWO

## 6. StorageClass — dynamic provisioning

Without SC: admin pre-creates PVs manually.
With SC: PVC requests storage; SC's provisioner creates a PV automatically.

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata: { name: gp3 }
provisioner: ebs.csi.aws.com
volumeBindingMode: WaitForFirstConsumer    # delay binding until pod scheduled
reclaimPolicy: Delete
allowVolumeExpansion: true
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  fsType: ext4
  encrypted: "true"
```

```yaml
# PVC uses SC
spec:
  storageClassName: gp3          # default SC used if omitted (and one marked default)
```

`WaitForFirstConsumer` binding mode: don't provision until a pod actually needs it (lets scheduler pick a node first, then provision EBS in that AZ).

## 7. CSI drivers (the modern storage layer)

In-tree drivers (kubernetes/kubernetes repo) are deprecated. **CSI (Container Storage Interface)** drivers run as separate controllers + DaemonSets.

Cloud CSI drivers:
- **AWS EBS CSI** (ebs.csi.aws.com) — for EBS volumes
- **AWS EFS CSI** (efs.csi.aws.com) — for EFS file systems
- **GCE PD CSI** (pd.csi.storage.gke.io) — for GCP persistent disks
- **Azure Disk CSI**
- **Azure File CSI**

Multi-cloud / on-prem:
- **Rook-Ceph** — full Ceph cluster on K8s
- **Longhorn** — Rancher's distributed block storage
- **Portworx** — commercial
- **NetApp Trident** — for NetApp ONTAP

## 8. Configuring HostPath Volume (CKA exam-style)

```yaml
apiVersion: v1
kind: Pod
metadata: { name: hostpath-pod }
spec:
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: data
      mountPath: /usr/share/nginx/html
  volumes:
  - name: data
    hostPath:
      path: /tmp/web-data
      type: DirectoryOrCreate
```

`type:`
- `DirectoryOrCreate` — create if missing
- `Directory` — must already exist as directory
- `FileOrCreate` — create file if missing
- `File` — must exist as file
- `Socket`, `CharDevice`, `BlockDevice`

## 9. Configuring emptyDir Volume

```yaml
apiVersion: v1
kind: Pod
metadata: { name: scratch }
spec:
  containers:
  - name: writer
    image: alpine
    command: ['sh', '-c', 'while true; do date >> /data/log.txt; sleep 5; done']
    volumeMounts: [{ name: shared, mountPath: /data }]
  - name: reader
    image: alpine
    command: ['sh', '-c', 'tail -f /data/log.txt']
    volumeMounts: [{ name: shared, mountPath: /data }]
  volumes:
  - name: shared
    emptyDir: {}
```

## 10. PVC binding lifecycle

```
Pending → Bound → (PV/PVC bound) → Mounted → (in use)
                                              ↓
                                          Released (PVC deleted)
                                              ↓
                                Reclaim Policy:
                                  - Delete → PV deleted (and backing storage gone)
                                  - Retain → PV kept (manual cleanup)
                                  - Recycle → DEPRECATED
```

Common task: PVC stuck Pending.
- No StorageClass + no matching PV → manually create PV
- StorageClass exists but provisioner fails → check CSI controller logs
- accessMode mismatch → PVC wants RWX, only RWO PVs available

```bash
k get pvc
k describe pvc my-data
k get pv
k describe pv pv-1
k get sc
k get pods -n kube-system | grep csi
```

## 11. Volume expansion

```bash
# Patch PVC to request more storage
k patch pvc my-data -p '{"spec":{"resources":{"requests":{"storage":"20Gi"}}}}'
# SC must have allowVolumeExpansion: true
# Online expansion (no pod restart) supported by EBS, EFS, etc.
```

## 12. ConfigMap + Secret as volumes (preview Module 69)

```yaml
volumes:
- name: config
  configMap:
    name: app-config
- name: secrets
  secret:
    secretName: app-secrets
    defaultMode: 0400
```

Each ConfigMap/Secret key becomes a file in the volume.

## 13. Quick self-check

1. What's the difference between emptyDir and a PVC?
2. What's the difference between ReadWriteOnce and ReadWriteMany?
3. What does `volumeBindingMode: WaitForFirstConsumer` do and when use it?
4. What's a CSI driver vs in-tree driver?
5. What's the reclaim policy and what are the two options that aren't deprecated?

(Answers: emptyDir lives for pod lifetime + lost on pod delete, PVC is persistent + survives pod restarts/recreations; RWO = one node mounts (EBS-style), RWX = many nodes mount simultaneously (EFS/NFS-style); delays PV provisioning until a pod is scheduled — lets scheduler pick the node first, then provision storage in that AZ — essential for zonal storage like EBS; CSI is out-of-tree pluggable storage driver, in-tree was baked into K8s source — CSI is the modern path, in-tree is being removed; Delete (PV deleted with backing storage when PVC deleted) and Retain (PV kept, manual cleanup needed).)
