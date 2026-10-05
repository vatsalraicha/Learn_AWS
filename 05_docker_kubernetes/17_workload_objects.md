# 17 — K8s workload objects: Pod, Deployment, StatefulSet, DaemonSet, Job, CronJob

> *"Pick the right workload object. Half of K8s 'failures' are someone using a Deployment where they needed a StatefulSet."*

## Why this module exists

A Pod is the unit of execution. Five higher-level controllers wrap Pods for different lifecycles. Picking correctly is a senior-engineer judgment call.

---

## 1. Pod — the atom

A Pod is **one or more containers** that share network namespace, IPC, and (optionally) volumes. The containers are co-scheduled on one node and live/die together.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
  namespace: default
spec:
  containers:
    - name: nginx
      image: nginx:1.27
      ports:
        - containerPort: 80
      resources:
        requests: { cpu: "100m", memory: "128Mi" }
        limits:   { cpu: "500m", memory: "512Mi" }
```

You **rarely** create Pods directly in production. You create a higher-level controller (Deployment, etc.) that creates Pods for you. Reason: a bare Pod has no self-healing — if it dies, it's gone.

### 1.1 Multi-container patterns

| Pattern | Sidecar example | Lifecycle |
|---|---|---|
| **Init container** | DB migration before app starts | Runs to completion, then app starts |
| **Sidecar** (init-style, but stays running, since 1.28) | Log forwarder, mesh proxy, Vault Agent | Lifecycle bound to main container |
| **Ambassador** | Proxy for external service auth (e.g., Cloud SQL Proxy) | Same as sidecar |
| **Adapter** | Format-conversion proxy (e.g., Prom exporter for legacy app) | Same |

K8s 1.28 added **sidecar containers** as first-class init containers with `restartPolicy: Always` — they start before the main container and live as long as it does. This is the right primitive for Istio/Linkerd proxies, Vault Agent, fluent-bit. Before 1.28, sidecars were just regular containers with a startup-race risk.

### 1.2 Probes

- **livenessProbe** — restart the container if this fails (the "is it alive?" check).
- **readinessProbe** — remove from Service endpoints if this fails (the "ready for traffic?" check).
- **startupProbe** — give a slow-starting container time before liveness kicks in.

Probe types: `httpGet`, `tcpSocket`, `exec`, `grpc`.

The most common mistake: confusing liveness and readiness. Liveness = "kill and restart"; readiness = "stop sending traffic." A slow-loading model server needs **readiness** (don't send traffic until model loaded) and a generous **startup** probe (don't kill while loading).

---

## 2. Deployment — stateless replicas

The workhorse. Wraps a Pod template in a ReplicaSet, manages rolling updates.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: infer-server
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels: { app: infer-server }
  template:
    metadata:
      labels: { app: infer-server }
    spec:
      containers:
        - name: infer
          image: myorg/infer:1.2.3
          ports: [{ containerPort: 8080 }]
```

`maxUnavailable: 0, maxSurge: 1` is the safe default for production: never go below desired replicas; add one extra during rollout. The default (`25%, 25%`) is fine for many workloads.

When to use Deployment: stateless web apps, model servers, API gateways, anything where Pod-1 and Pod-2 are interchangeable.

### 2.1 Rollback

```bash
kubectl rollout undo deployment/infer-server
kubectl rollout history deployment/infer-server
kubectl rollout status deployment/infer-server
```

The ReplicaSet history (10 revisions by default) is what enables rollback. Don't `kubectl delete rs` casually.

---

## 3. StatefulSet — stable identity per replica

When pod identity matters: Pod 0 is "the leader," Pod 1 is "follower 1," and pods need stable network names and persistent storage.

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres-headless   # required headless Service
  replicas: 3
  selector:
    matchLabels: { app: postgres }
  template: { ... }
  volumeClaimTemplates:
    - metadata: { name: data }
      spec:
        accessModes: [ReadWriteOnce]
        storageClassName: gp3
        resources: { requests: { storage: 100Gi } }
```

Properties:

- Pods named `<sts>-0`, `<sts>-1`, ... (stable).
- DNS: `postgres-0.postgres-headless.ns.svc.cluster.local`.
- PVCs auto-created from `volumeClaimTemplates`, one per pod, **persistent across pod replace** (the volume sticks to ordinal).
- Ordered startup/teardown by default (Pod 0 ready before Pod 1 starts).
- Pod deletion does NOT delete PVCs (you must opt in to that).

When to use StatefulSet: databases (Postgres HA, Cassandra, MongoDB), distributed message queues (Kafka, NATS JetStream), distributed caches (Redis Cluster), distributed FS (CephFS), some Spark + Flink configs.

For ML: vLLM with tensor-parallelism may want StatefulSet (rank 0 vs rank N matters), but most serving workloads are stateless Deployments.

---

## 4. DaemonSet — one Pod per node

Used for node agents: log forwarders (Fluent Bit), monitoring agents (Prometheus node-exporter, Datadog agent), CNI dataplane (Cilium agent), CSI driver components, GPU operator's device plugin.

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-exporter
spec:
  selector:
    matchLabels: { app: node-exporter }
  template:
    spec:
      hostNetwork: true                  # often needed for node-level metrics
      tolerations:
        - operator: Exists               # tolerate ALL taints (run on every node, period)
      containers: [...]
```

DaemonSet is **the** privileged workload type — its pods often need `hostNetwork`, `hostPID`, or privileged containers. PSA `restricted` policy disallows these; DaemonSets typically live in a `kube-system`-like namespace labeled with PSA `privileged` (module 22).

---

## 5. Job — one-shot task

Runs a Pod (or N Pods) to completion. Retries on failure up to `backoffLimit`.

```yaml
apiVersion: batch/v1
kind: Job
metadata: { name: db-migrate }
spec:
  backoffLimit: 3
  ttlSecondsAfterFinished: 600       # auto-delete 10 min after success
  template:
    spec:
      restartPolicy: OnFailure
      containers:
        - name: migrate
          image: myorg/migrate:1.0
          command: ["python", "manage.py", "migrate"]
```

For batch jobs:

- `completions: N` — total successful pod runs needed.
- `parallelism: M` — how many in parallel.
- `completionMode: Indexed` — gives each pod a `JOB_COMPLETION_INDEX` env var (since 1.21). Useful for distributed ML training where rank == index.

### 5.1 ML training as Job

```yaml
apiVersion: batch/v1
kind: Job
metadata: { name: train-bert-2026-05-21 }
spec:
  completions: 8
  parallelism: 8
  completionMode: Indexed
  backoffLimit: 0                      # don't retry ML training; let observability re-launch
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: train
          image: nvcr.io/nvidia/pytorch:24.06-py3
          command: ["torchrun", "--nproc-per-node=8", "--nnodes=8",
                    "--node-rank=$(JOB_COMPLETION_INDEX)",
                    "--rdzv-backend=c10d", "train.py"]
          resources:
            limits: { nvidia.com/gpu: 8 }
```

For more sophisticated training, use **Kubeflow Training Operator's PyTorchJob** (module 31) which handles rendezvous, rank assignment, and failure modes.

---

## 6. CronJob — scheduled jobs

```yaml
apiVersion: batch/v1
kind: CronJob
metadata: { name: nightly-etl }
spec:
  schedule: "0 2 * * *"                # 02:00 UTC daily
  timeZone: "America/New_York"          # k8s 1.27+
  concurrencyPolicy: Forbid             # don't overlap
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 5
  jobTemplate: { spec: { ... } }
```

Cron expression is standard POSIX. `timeZone` field is opt-in since 1.27.

When NOT to use CronJob: anything you need observability/retries/lineage on. Use Airflow (Topic 06) or Argo Workflows for ETL/ML pipelines. CronJob is for "run this script nightly" with no parents/dependencies.

---

## 7. ReplicaSet — almost never directly

ReplicaSet is what Deployment manages under the hood. Don't create directly.

---

## 8. Resource requests vs limits

Every container should declare:

```yaml
resources:
  requests:
    cpu: "100m"          # 0.1 CPU
    memory: "256Mi"
  limits:
    cpu: "500m"
    memory: "512Mi"
    nvidia.com/gpu: 1
```

- **Requests** affect scheduling (the scheduler reserves this much).
- **Limits** affect runtime (cgroups enforce; over-limit memory = OOM-kill; over-limit CPU = throttling).

For ML serving: tight memory limits (no over-allocation = no node OOM crash); cpu limits generous (CPU throttling causes p99 latency spikes).

For training: requests == limits == node capacity (you want exclusive use of the GPU).

### 8.1 QoS classes

K8s derives a QoS class from your requests/limits:

- **Guaranteed** — requests == limits for both cpu and memory. Last to be evicted under pressure.
- **Burstable** — requests set, limits set higher (or unset).
- **BestEffort** — nothing set. First to be evicted.

For prod, always set requests and limits (Guaranteed or close to it).

---

## 9. Pod scheduling primitives

- **nodeSelector** — simple label match (`disktype: ssd`).
- **nodeAffinity** — richer expression (`In`, `NotIn`, `Exists`, ...) with required vs preferred.
- **podAffinity / podAntiAffinity** — "schedule near / away from pods matching label."
- **taints + tolerations** — keep workloads off certain nodes unless they tolerate the taint.
- **topologySpreadConstraints** — spread pods across zones/nodes evenly.

For GPU nodes:
```yaml
nodeSelector:
  nvidia.com/gpu.product: H100
tolerations:
  - key: nvidia.com/gpu
    operator: Exists
    effect: NoSchedule
```

Karpenter (module 31) provisions GPU nodes with these taints automatically.

---

## 10. PodDisruptionBudget (PDB) — protecting availability

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata: { name: infer-server-pdb }
spec:
  minAvailable: 2
  selector: { matchLabels: { app: infer-server } }
```

PDB blocks **voluntary** disruptions (node drain, scaling down, upgrades) if they would violate the budget. **Involuntary** disruptions (node crash) still happen. PDB is what keeps a careless `kubectl drain` from taking the whole service down.

For prod services with > 1 replica, **always** define a PDB.

---

## Sanity check

1. When do you need a StatefulSet instead of a Deployment? Name two real workloads.
2. Why do K8s 1.28+ sidecars (init container with `restartPolicy: Always`) fix problems that the older sidecar pattern had?
3. What's the difference between a livenessProbe and a readinessProbe, and which one do you need for a model server that takes 90s to load?
4. CronJob is the wrong tool when you need what?
5. QoS class Guaranteed requires what exact configuration?
6. Why is a PDB needed even on a managed K8s service like EKS?

---

## Sources

- [Pod concept](https://kubernetes.io/docs/concepts/workloads/pods/)
- [Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [StatefulSets](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/)
- [DaemonSets](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/)
- [Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/)
- [CronJobs](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/)
- [Sidecar containers (1.28+)](https://kubernetes.io/blog/2023/08/25/native-sidecar-containers/)
- [PodDisruptionBudget](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/)
- [QoS classes](https://kubernetes.io/docs/concepts/workloads/pods/pod-qos/)

→ Next: [18 — Services & networking — Ingress, Gateway API, NetworkPolicy, CNI](18_k8s_networking.md)
