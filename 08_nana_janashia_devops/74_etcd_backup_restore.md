# 74 — etcd Backup + Restore

## Why this module is high-stakes

**etcd backup + restore is the highest-anxiety CKA exam task.** It tests Linux + certs + binary tools + careful steps. ~1-2 tasks per exam attempt. Practice this 10+ times until it's muscle memory.

## 1. What etcd stores

Everything K8s knows:
- All resource objects (Pods, Deployments, Services, ConfigMaps, Secrets, etc.)
- RBAC rules
- Custom resources
- Events (recent)

If etcd dies + you have no backup: **the cluster's data is gone**. Workloads might still run (pods on nodes), but the control plane has no memory of them.

## 2. The etcd architecture on a kubeadm cluster

- etcd runs as a **static pod** on the control plane node
- Manifest at `/etc/kubernetes/manifests/etcd.yaml`
- Data dir: `/var/lib/etcd/`
- TLS certs: `/etc/kubernetes/pki/etcd/`

## 3. etcdctl + endpoint setup

`etcdctl` (the etcd CLI) talks to etcd via mTLS. You need 4 things:
- Endpoint URL (`https://127.0.0.1:2379`)
- CA cert (`/etc/kubernetes/pki/etcd/ca.crt`)
- Client cert (`/etc/kubernetes/pki/etcd/server.crt`)
- Client key (`/etc/kubernetes/pki/etcd/server.key`)

Set env vars for convenience:
```bash
export ETCDCTL_API=3
export ETCDCTL_ENDPOINTS=https://127.0.0.1:2379
export ETCDCTL_CACERT=/etc/kubernetes/pki/etcd/ca.crt
export ETCDCTL_CERT=/etc/kubernetes/pki/etcd/server.crt
export ETCDCTL_KEY=/etc/kubernetes/pki/etcd/server.key
```

## 4. Verify connection

```bash
sudo ETCDCTL_API=3 etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  endpoint health
# https://127.0.0.1:2379 is healthy: ...

# Member list
sudo etcdctl member list -w table
```

## 5. Backup — `snapshot save`

```bash
sudo ETCDCTL_API=3 etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  snapshot save /tmp/etcd-backup-$(date +%F-%H%M).db
```

Verify:
```bash
sudo etcdctl --write-out=table snapshot status /tmp/etcd-backup-*.db
# Hash, Revision, Total Keys, Total Size shown
```

## 6. Restore — `snapshot restore`

Restoring is involved because etcd must be **stopped** while you restore + the apiserver must restart.

### Steps

```bash
# 1. Stop kube-apiserver + etcd by moving their static pod manifests aside
sudo mv /etc/kubernetes/manifests/etcd.yaml /etc/kubernetes/manifests-bak/
sudo mv /etc/kubernetes/manifests/kube-apiserver.yaml /etc/kubernetes/manifests-bak/

# Wait for pods to disappear
sudo crictl ps | grep -E 'etcd|apiserver'

# 2. Move existing data dir aside
sudo mv /var/lib/etcd /var/lib/etcd-bak

# 3. Restore from snapshot
sudo ETCDCTL_API=3 etcdctl snapshot restore /tmp/etcd-backup.db \
  --data-dir=/var/lib/etcd

# 4. Fix permissions
sudo chown -R etcd:etcd /var/lib/etcd       # if etcd user exists; else stay root

# 5. Restore static pod manifests
sudo mv /etc/kubernetes/manifests-bak/etcd.yaml /etc/kubernetes/manifests/
sudo mv /etc/kubernetes/manifests-bak/kube-apiserver.yaml /etc/kubernetes/manifests/

# kubelet detects + restarts the pods
# 6. Verify
sudo crictl ps | grep -E 'etcd|apiserver'
k get nodes
k get pods -A
```

## 7. Exam shortcut: restore to a different path

The exam often asks you to restore the snapshot to a specific path, perhaps with a different etcd cluster config. If `--data-dir=/var/lib/etcd-restored`, then **edit the static pod manifest** (`/etc/kubernetes/manifests/etcd.yaml`) to point at the new dir:

```yaml
# In etcd.yaml — change hostPath:
volumes:
- name: etcd-data
  hostPath:
    path: /var/lib/etcd-restored        # ← updated
```

kubelet reapplies the static pod with the new mount.

## 8. Backup automation

Production: backup every N hours via cron + write to S3:

```bash
#!/bin/bash
set -euo pipefail
TS=$(date +%F-%H%M)
sudo ETCDCTL_API=3 etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  snapshot save /tmp/etcd-snapshot-$TS.db

aws s3 cp /tmp/etcd-snapshot-$TS.db s3://my-etcd-backups/$TS.db --sse aws:kms
rm /tmp/etcd-snapshot-$TS.db
```

Cron entry:
```
0 */6 * * * /usr/local/bin/etcd-backup.sh >> /var/log/etcd-backup.log 2>&1
```

## 9. EKS / GKE / AKS — managed etcd

For managed K8s services, **AWS/GCP/Azure manage etcd backup automatically**. You don't run `etcdctl snapshot save`. EKS retains the cluster state and disaster recovery is on AWS.

CKA exam still tests etcd backup/restore (on self-managed kubeadm clusters). It's required knowledge even if your job uses EKS.

## 10. Alternatives to managing etcd

- **EKS / GKE / AKS** — managed (don't think about etcd)
- **kOps** — Kubernetes Operations; manages etcd via the etcd-manager
- **Rancher / RKE2** — opinionated etcd setup with backup
- **k3s** — uses SQLite by default (single-node) or external etcd / Postgres / MySQL

## 11. Restoring etcd — exam-task pseudocode

A typical exam task:
> "Take a backup of etcd to `/tmp/etcd-backup.db`. Restore it to a new data dir `/var/lib/etcd-from-backup` and configure etcd to use this new dir."

```bash
# Backup (assume env vars set)
sudo etcdctl snapshot save /tmp/etcd-backup.db

# Restore
sudo etcdctl snapshot restore /tmp/etcd-backup.db \
  --data-dir=/var/lib/etcd-from-backup

# Edit /etc/kubernetes/manifests/etcd.yaml to use new data dir
# Find:
#   --data-dir=/var/lib/etcd
# Change to:
#   --data-dir=/var/lib/etcd-from-backup
# And the volume hostPath similarly

# kubelet reapplies; check
sudo crictl ps | grep etcd
k get nodes
```

## 12. Quick self-check

1. Where do etcd's TLS certs live on a kubeadm cluster?
2. What three flags must you pass to etcdctl to authenticate (besides endpoint)?
3. What environment variable selects etcdctl API v3?
4. Why must kube-apiserver be stopped during restore?
5. What's the difference between EKS-managed etcd and kubeadm-managed etcd?

(Answers: `/etc/kubernetes/pki/etcd/`; `--cacert`, `--cert`, `--key`; `ETCDCTL_API=3`; apiserver would write to old etcd while you're restoring → corruption / data inconsistency; EKS = AWS handles backup/restore/HA, kubeadm = you do it via etcdctl + cron + manifests/.)
