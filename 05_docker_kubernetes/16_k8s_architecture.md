# 16 — Kubernetes architecture: control plane, kubelet, kube-proxy, etcd, CRDs

> *"K8s is a desired-state controller loop on top of a distributed key-value store. Everything else is mechanism."*

## Why this module exists

You can use K8s for a year without knowing what etcd is. The day a CKA / CKS exam shows up — or the day prod breaks — you need the architecture in your head, not your bookmarks.

This module is the 90-minute "everything fits" map. Modules 17–25 zoom into each piece.

---

## 1. The 30-second mental model

Kubernetes is a **declarative system**:

1. You write a YAML manifest declaring desired state (e.g., "I want 3 replicas of nginx").
2. The API server stores it in etcd.
3. Controllers watch etcd, observe a divergence (zero pods vs three desired), and act to converge.
4. The kubelet on each node creates/destroys containers to match what's assigned to it.

That's the entire model. Every K8s feature is a controller watching a resource and converging.

---

## 2. Control plane components

A cluster has a **control plane** (the brain) and **worker nodes** (the muscle). On managed K8s (EKS/GKE/AKS), the control plane is hidden — you only see worker nodes. On self-managed (kubeadm, Talos), you see both.

### 2.1 The five control-plane components

| Component | Role |
|---|---|
| **kube-apiserver** | The REST/gRPC API. The ONLY thing that writes to etcd. Authenticates, validates, admission-controls. |
| **etcd** | Distributed key-value store (Raft consensus). Single source of truth for cluster state. |
| **kube-scheduler** | Decides which node a Pod runs on (based on resources, taints, affinity, topology). |
| **kube-controller-manager** | Hosts ~30 controllers (Deployment, ReplicaSet, Node, Endpoint, ...). Each is a loop. |
| **cloud-controller-manager** | Cloud-specific controllers (LoadBalancer creation, Node lifecycle on cloud VMs). |

### 2.2 etcd — the heart

- **Raft** consensus algorithm; cluster of 3 or 5 nodes for HA.
- Stores **every** K8s object — pods, secrets, configmaps, custom resources.
- **Snapshotting** for backup is critical (`etcdctl snapshot save`).
- **Encryption at rest** for K8s secrets — must be configured explicitly (module 20).
- **Compaction** — etcd's MVCC accumulates revisions; defrag periodically or it grows.

**Lose etcd = lose the cluster.** This is why etcd backup is the #1 cluster-admin task and why managed K8s services (EKS/GKE/AKS) hide etcd entirely.

### 2.3 The API server is the only path

Nothing writes directly to etcd except the API server. Every component (scheduler, controller-manager, kubelet, custom operators, even kube-proxy) **reads via the API server**. Implications:

- Auth/authorization is centralized at the API server.
- Audit logging is at the API server.
- Admission control (validating, mutating webhooks) is at the API server.
- API server reliability == cluster reliability.

---

## 3. Worker-node components

Each worker node runs three components:

### 3.1 kubelet

The node's agent. Watches the API server for pods assigned to its node, then asks the CRI runtime (containerd / CRI-O) to start/stop containers. Reports node + pod status back. Implements:

- Volume mounts (via CSI).
- Liveness, readiness, startup probes.
- Image pulls (via the container runtime).
- Pod cgroup management.
- Eviction (under resource pressure).

The kubelet is what makes a node "join" a cluster. Its config (`/var/lib/kubelet/config.yaml`) has many security knobs (CIS K8s benchmark hammers these).

### 3.2 Container runtime (CRI)

Almost always **containerd** in 2025–2026. CRI-O on OpenShift. Docker is gone (`dockershim` removed in K8s 1.24).

The kubelet talks to the runtime via the CRI gRPC interface. The runtime pulls images, manages snapshots, calls runc/runsc/kata, and reports status.

### 3.3 kube-proxy

Implements **Service** networking. Two modes:

- **iptables** (default) — installs DNAT rules per Service ClusterIP → backend pod IPs.
- **IPVS** — kernel-level virtual server; better at high service count + connection rate.
- **eBPF** (Cilium replaces kube-proxy entirely) — programmable kernel datapath; cleaner at scale.

On modern clusters with Cilium installed in "kube-proxy-replacement" mode, kube-proxy is **not running**.

---

## 4. Objects and the API hierarchy

### 4.1 The core API

Every object has: `apiVersion`, `kind`, `metadata`, `spec`, `status`.

- **`spec`** — desired state (you write this).
- **`status`** — observed state (controllers write this).

The kube-apiserver presents APIs grouped by **API group + version**:

- `/api/v1` — core group: Pod, Service, ConfigMap, Secret, Namespace, Node, PersistentVolume, ...
- `/apis/apps/v1` — Deployment, StatefulSet, DaemonSet, ReplicaSet.
- `/apis/batch/v1` — Job, CronJob.
- `/apis/networking.k8s.io/v1` — Ingress, NetworkPolicy.
- `/apis/rbac.authorization.k8s.io/v1` — Role, RoleBinding, ClusterRole, ClusterRoleBinding.
- `/apis/storage.k8s.io/v1` — StorageClass, CSIDriver, VolumeSnapshot.

Versions: `v1alpha1` → `v1beta1` → `v1`. Beta becomes default-on in 1.16+; alpha must be enabled per cluster.

### 4.2 Custom Resource Definitions (CRDs)

Anyone (you, vendors) can extend the API. A **CRD** registers a new kind. Examples in the wild:

- `Certificate` (cert-manager).
- `InferenceService` (KServe).
- `PrometheusRule` (kube-prometheus-stack).
- `KafkaTopic` (Strimzi).
- `Ingress` was once a CRD; now it's core.

The **operator pattern**: write a CRD + a controller. The controller watches the CR and reconciles to the desired state, just like built-in controllers. The vast majority of CNCF projects expose themselves this way.

---

## 5. Namespaces — the K8s multi-tenancy primitive

Namespaces partition the cluster's resources. Default namespaces:

| Namespace | Use |
|---|---|
| `default` | If you don't specify, this is where things land. Don't use in prod. |
| `kube-system` | Control-plane components and addons. Don't touch. |
| `kube-public` | Cluster-info, readable to all (auth + auth model). |
| `kube-node-lease` | Node heartbeats. |

You create namespaces per team / per environment / per workload tier:

```bash
kubectl create namespace ml-serving
kubectl create namespace ml-training
kubectl create namespace data-pipeline
```

**RBAC**, **NetworkPolicy**, **ResourceQuota**, **LimitRange**, **PodSecurity** are all namespace-scoped — they're the multi-tenancy levers.

### 5.1 Namespaces are NOT a security boundary by themselves

A `ServiceAccount` in one namespace can talk to a Service in another namespace by default. **NetworkPolicy** is what makes it a real boundary (module 18). A vanilla cluster has no NetworkPolicy enforcement — you get one (Calico, Cilium) at install.

---

## 6. The controller pattern (operator-grade understanding)

A controller is a **for-loop**:

```python
while True:
    desired = api.watch("CustomResource")  # blocks on changes
    actual  = read_world_state()
    if desired != actual:
        reconcile(desired, actual)
    sleep(0.1)
```

Every CNCF tool that "extends K8s" is this loop wearing a costume. Knowing this:

- Explains why deletes are eventually consistent.
- Explains why `kubectl get` shows stale state during reconciliation.
- Explains why operators need RBAC for the resources they reconcile.
- Explains why misconfigured admission webhooks can hard-fail the API server.

---

## 7. Networking primitives (preview of module 18)

K8s networking has three layers:

1. **Pod network** — every pod gets a routable IP. Implemented by a **CNI plugin** (Calico, Cilium, AWS VPC CNI, Azure CNI, GCP CNI).
2. **Service network** — virtual IPs (`ClusterIP`) abstracting groups of pods. Implemented by kube-proxy (or Cilium replacement).
3. **Ingress / Gateway** — external HTTP/HTTPS into the cluster. Implemented by an ingress controller (nginx, Traefik, Envoy/Contour, Cilium ingress, AWS ALB Controller, etc.).

For data exposure: the CNI choice **and** NetworkPolicy enforcement determine container-to-container blast radius.

---

## 8. Storage primitives (preview of module 19)

- **Volume** — anything mounted into a pod (emptyDir, ConfigMap, Secret, PVC, ephemeral CSI).
- **PersistentVolume (PV)** — a real storage resource (EBS volume, NFS share, Ceph RBD).
- **PersistentVolumeClaim (PVC)** — a request for storage by a workload.
- **StorageClass (SC)** — a parametrized recipe for creating PVs on demand (e.g., "gp3 in us-east-1a").
- **CSI driver** — the interface between K8s and a storage backend.

---

## 9. Identity primitives (preview of modules 20–21)

- **ServiceAccount** — pod identity. Default SA exists per namespace.
- **Role / ClusterRole** — verbs + resources.
- **RoleBinding / ClusterRoleBinding** — link a Role to a SA / User / Group.
- **TokenRequest API** — short-lived projected SA tokens (default since 1.22).

For cloud identity: **IRSA** (EKS) / **Workload Identity** (GKE) / **Entra Workload ID** (AKS) federate K8s SAs to cloud IAM. Modules 26-28.

---

## 10. The kubectl request flow

What happens on `kubectl apply -f deployment.yaml`:

```
1. kubectl reads ~/.kube/config; resolves current context.
2. kubectl POSTs to API server (HTTPS, mTLS via your client cert / OIDC token).
3. API server authenticates: cert chain / OIDC / webhook.
4. API server authorizes: RBAC (or webhook/OPA).
5. API server runs **mutating** admission webhooks (Kyverno, defaults).
6. API server runs **validating** admission webhooks (Kyverno, OPA, PSA).
7. API server writes to etcd.
8. Deployment controller wakes, creates ReplicaSet.
9. ReplicaSet controller wakes, creates Pods.
10. Scheduler watches unscheduled Pods, picks a node.
11. Kubelet on that node watches its pods, asks containerd to pull + run.
12. CNI plugin assigns pod IP.
13. CSI driver mounts requested volumes.
14. Container starts. Pod IP exposed via Service via kube-proxy / Cilium.
```

Every step is a control point you can break or harden. CKA/CKS exams test that you can trace this flow.

---

## 11. The managed-K8s delta (EKS, GKE, AKS)

| | EKS | GKE | AKS |
|---|---|---|---|
| Control plane managed by | AWS | Google | Microsoft |
| Control plane SLA | 99.95% | 99.95% (region), 99.99% (zonal) | 99.95% (paid uptime SLA) |
| etcd visible to user | No | No | No |
| Custom Admission Controllers? | Yes (webhooks) | Yes (webhooks) | Yes (webhooks) |
| Bring your own CNI? | Yes (VPC CNI default; also Cilium, Calico) | Yes (Dataplane V2 / GKE CNI / Cilium) | Yes (Azure CNI, Kubenet, Cilium) |
| Default node OS | Bottlerocket, Amazon Linux 2/2023 | Container-Optimized OS (COS), Ubuntu | Ubuntu, Mariner (Azure Linux) |
| Pod identity model | IRSA, EKS Pod Identity | Workload Identity for GKE | Entra Workload ID |
| Auto-upgrade | Optional | Optional, can be enforced | Optional |
| Cost | $0.10/hr per cluster + node costs | $0.10/hr (Standard); Autopilot priced per pod | Free (Standard) or paid SLA |

---

## 12. The single most-asked CKA question

"How would you investigate a Pod stuck in `ImagePullBackOff`?"

```bash
kubectl describe pod <name>            # Events at bottom
kubectl get events --sort-by='.lastTimestamp' -n <ns>
kubectl logs -p <name>                 # previous container logs
kubectl get nodes -o wide              # node status
kubectl describe node <node-name>      # taints, resources, kubelet status
```

Hits to investigate (the same answer repeated thousands of times):

- Image typo / tag missing.
- Registry auth (no `imagePullSecrets` or wrong one).
- Private registry without network reachability (no VPC endpoint, no NAT).
- Image bigger than node ephemeral storage.

This is **the** debugging question. Master the flow.

---

## Sanity check

1. Why is etcd backup the #1 cluster admin task?
2. What's the difference between a Pod and a Deployment, and why do you almost never `kubectl run` a Pod directly?
3. The kube-scheduler decides node placement based on what factors?
4. Why does the operator pattern work for nearly any "I want to manage X declaratively in K8s" use case?
5. In a managed K8s service, what becomes the customer's responsibility vs the cloud provider's?
6. What does `kubectl apply` actually do at the API server level (list the steps).

---

## Sources

- [Kubernetes Components](https://kubernetes.io/docs/concepts/overview/components/)
- [etcd docs](https://etcd.io/docs/)
- [Operator pattern](https://kubernetes.io/docs/concepts/extend-kubernetes/operator/)
- [Custom Resources](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/)
- [CIS Kubernetes Benchmark](https://www.cisecurity.org/benchmark/kubernetes)

→ Next: [17 — Workload objects — Pod, Deployment, StatefulSet, DaemonSet, Job, CronJob](17_workload_objects.md)
