# 76 — Cluster Upgrade with kubeadm

## 1. Why upgrades matter

- K8s ships 3 minor versions/year (Apr / Aug / Dec)
- Each version supported ~14 months
- Falling behind = unsupported (no security patches) + can't take advantage of new features
- Compliance requires current minor for many regulated workloads

## 2. The upgrade rule

**Upgrade one minor at a time.** v1.30 → v1.31 → v1.32. Never skip (e.g., v1.30 → v1.32 directly).

Patches within a minor (v1.31.0 → v1.31.5) are safe to do in one shot.

## 3. Upgrade order on a kubeadm cluster

```
1. Drain + upgrade FIRST control-plane node
2. Drain + upgrade REMAINING control-plane nodes (if HA)
3. Drain + upgrade WORKER nodes (one at a time)
4. Update kubeconfig clients on your workstation
```

The control plane upgrades before workers. **Kubelet on workers must not be newer than the control plane** (skew policy: control-plane >= node).

## 4. Pre-upgrade checks

```bash
# Current versions
k get nodes -o wide
k version

# Check workloads health
k get pods -A | grep -v Running

# Backup etcd (Module 74)
sudo etcdctl snapshot save /tmp/pre-upgrade.db

# Check for deprecated APIs
kubectl api-resources --verbs=list --namespaced -o name | \
  xargs -n 1 kubectl get --show-kind --ignore-not-found -A
```

Tools for deprecation scanning:
- **kubent** (`kubent` / `kube-no-trouble`) — scans manifests + cluster for deprecated APIs
- **pluto** (Fairwinds) — same idea

## 5. Upgrade first control-plane node

```bash
# 1. Update kubeadm to target version
sudo apt-mark unhold kubeadm
sudo apt-get update
sudo apt-cache madison kubeadm | head -10        # see versions available
sudo apt-get install -y kubeadm=1.31.3-1.1
sudo apt-mark hold kubeadm

# 2. Verify
kubeadm version

# 3. Plan the upgrade
sudo kubeadm upgrade plan

# 4. Drain the node
kubectl drain <cp-node> --ignore-daemonsets

# 5. Apply
sudo kubeadm upgrade apply v1.31.3

# 6. Uncordon
kubectl uncordon <cp-node>

# 7. Update kubelet + kubectl
sudo apt-mark unhold kubelet kubectl
sudo apt-get install -y kubelet=1.31.3-1.1 kubectl=1.31.3-1.1
sudo apt-mark hold kubelet kubectl
sudo systemctl daemon-reload
sudo systemctl restart kubelet
```

## 6. Upgrade remaining control-plane nodes (HA)

Same as above EXCEPT use `kubeadm upgrade node` (not `apply`):
```bash
sudo kubeadm upgrade node
```

## 7. Upgrade worker nodes

For each worker:
```bash
# 1. Drain (from any control-plane node)
kubectl drain <worker> --ignore-daemonsets --delete-emptydir-data

# 2. SSH into worker

# 3. Update kubeadm
sudo apt-mark unhold kubeadm
sudo apt-get install -y kubeadm=1.31.3-1.1
sudo apt-mark hold kubeadm

# 4. Upgrade kubelet config
sudo kubeadm upgrade node

# 5. Update kubelet + kubectl
sudo apt-mark unhold kubelet kubectl
sudo apt-get install -y kubelet=1.31.3-1.1 kubectl=1.31.3-1.1
sudo apt-mark hold kubelet kubectl
sudo systemctl daemon-reload
sudo systemctl restart kubelet

# 6. Uncordon
kubectl uncordon <worker>
```

## 8. Verify

```bash
k get nodes
# All should show new version
# control-plane01   Ready   1.31.3
# worker01          Ready   1.31.3
# worker02          Ready   1.31.3

k version
k get pods -A | grep -v Running     # everything healthy?
```

## 9. Common upgrade pitfalls

- **Skipping minor versions** — supported skew is +1 minor only; v1.30 → v1.32 will fail
- **Forgetting to drain** — pods on the node get killed unpredictably
- **CNI conflicts** — some CNI plugins require their own upgrade in concert
- **Deprecated APIs in manifests** — `pluto` / `kubent` to check before
- **kubelet hold** — if you don't `apt-mark hold`, an unrelated `apt upgrade` can break the cluster
- **DaemonSet pods not draining** — must use `--ignore-daemonsets`
- **Stateful workloads with `emptyDir`** — `--delete-emptydir-data` for drain to proceed

## 10. EKS upgrade (the easier path)

EKS:
- Control plane: AWS upgrades; you click "upgrade" in console / Terraform
- Node groups: AWS upgrades; rolling update of EC2 instances
- Add-ons: separately versioned (VPC CNI, CoreDNS, kube-proxy) — upgrade alongside

```bash
aws eks update-cluster-version --name my-cluster --kubernetes-version 1.31

# For managed node groups
aws eks update-nodegroup-version --cluster-name my-cluster --nodegroup-name workers

# For Karpenter-managed nodes
# Update Karpenter NodePool's image; Karpenter rolls nodes
```

EKS supports skipping minor versions in some cases — but follow the AWS guide carefully.

## 11. CKA exam — upgrade tasks

Typical exam task:
> "Upgrade the cluster's control plane and nodes from v1.30 to v1.31. Make sure to drain the nodes before upgrading and uncordon them after."

Run the 10 commands above. Don't forget:
- `kubeadm` → upgrade plan → upgrade apply / upgrade node
- `kubelet` + `kubectl` packages
- `systemctl daemon-reload` + restart kubelet
- `drain` before, `uncordon` after

## 12. Quick self-check

1. What's the version skew policy between control plane and nodes?
2. Why use `kubeadm upgrade apply` on first CP node vs `upgrade node` on others?
3. What tools detect deprecated API usage before an upgrade?
4. Why `apt-mark hold kubelet kubeadm kubectl`?
5. What's different about an EKS upgrade vs kubeadm?

(Answers: control plane >= node, max 1 minor version skew; first CP defines the new control plane state, subsequent CPs and workers just sync; pluto, kubent (kube-no-trouble); prevents `apt upgrade` from accidentally updating these to incompatible versions; EKS = AWS handles control plane upgrade in place, you only roll node groups + add-ons.)
