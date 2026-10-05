# 71 — Scheduling — NodeSelector, Affinity, Taints, Tolerations

## 1. How the K8s scheduler decides

When a pod is unscheduled, kube-scheduler:
1. **Filter** — drop nodes that don't meet hard constraints (resources, nodeSelector, taints without tolerations, PV zone)
2. **Score** — rank remaining by soft preferences (affinity, balanced resource use, image locality)
3. **Pick** the highest-scoring node
4. **Bind** the pod to it

## 2. NodeName (force a node)

```yaml
spec:
  nodeName: worker-3
  containers: [...]
```

Bypasses scheduler entirely. Use sparingly — pod won't move if node fails.

## 3. NodeSelector (match by label)

```yaml
spec:
  nodeSelector:
    disktype: ssd
    region: us-east-1a
  containers: [...]
```

Only nodes with matching labels are candidates. Simple, but `equality only`.

Label nodes:
```bash
k label node worker-1 disktype=ssd
k get nodes --show-labels
```

## 4. Node Affinity (richer matching)

```yaml
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:      # hard
        nodeSelectorTerms:
        - matchExpressions:
          - { key: disktype, operator: In, values: [ssd] }
          - { key: zone, operator: In, values: [us-east-1a, us-east-1b] }
      preferredDuringSchedulingIgnoredDuringExecution:     # soft
      - weight: 100
        preference:
          matchExpressions:
          - { key: instance-type, operator: In, values: [m5.xlarge] }
```

Operators: `In`, `NotIn`, `Exists`, `DoesNotExist`, `Gt`, `Lt`.

Note: `IgnoredDuringExecution` means after scheduling, if labels change, pod stays put.

## 5. Inter-Pod Affinity / Anti-Affinity

```yaml
spec:
  affinity:
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchLabels: { app: web }
        topologyKey: kubernetes.io/hostname        # don't put 2 web pods on same node
```

Common use cases:
- **Anti-affinity**: spread replicas across nodes/zones for HA
- **Affinity**: co-locate pods that communicate heavily (rarely useful in K8s)

`topologyKey` defines the topology level: `kubernetes.io/hostname`, `topology.kubernetes.io/zone`, `topology.kubernetes.io/region`.

## 6. Pod Topology Spread Constraints (the modern replacement)

```yaml
spec:
  topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: topology.kubernetes.io/zone
    whenUnsatisfiable: DoNotSchedule
    labelSelector:
      matchLabels: { app: web }
```

Forces pods to be spread evenly across zones (max skew = 1 pod difference between any two zones). Replaces awkward pod-anti-affinity for spread use cases.

## 7. Taints + Tolerations

**Taint a node** = no pods land there unless they explicitly tolerate it.

```bash
# Taint
k taint nodes worker-1 dedicated=ml-training:NoSchedule

# Remove
k taint nodes worker-1 dedicated-

# View
k describe node worker-1 | grep Taints
```

Effects:
- `NoSchedule` — won't schedule new pods (existing stay)
- `PreferNoSchedule` — soft "avoid"
- `NoExecute` — evict existing pods that don't tolerate, won't schedule new

```yaml
# Pod with toleration
spec:
  tolerations:
  - key: dedicated
    operator: Equal
    value: ml-training
    effect: NoSchedule
  containers: [...]
```

Common taints:
- Control plane nodes auto-tainted with `node-role.kubernetes.io/control-plane:NoSchedule`
- Spot instances tagged `karpenter.sh/disruption=...`
- GPU nodes often tainted to prevent non-GPU workloads landing there

## 8. The NodeSelector / Affinity / Taint matrix

| Question | Use |
|---|---|
| "Only put workload X here" | Taints on node + tolerations on pod |
| "Prefer to put workload X here" | nodeAffinity preferred |
| "Pod must run on nodes with label L" | nodeSelector or required affinity |
| "Spread pods across zones" | Pod Topology Spread Constraints |
| "Avoid co-locating these pods" | podAntiAffinity |

Taint-based isolation is **the strongest**: even if a pod has matching node selector but no toleration, it won't land on tainted nodes.

## 9. Common scheduling exam tasks

### Schedule on a specific node
```yaml
spec:
  nodeName: worker-1
```
Or:
```yaml
spec:
  nodeSelector: { kubernetes.io/hostname: worker-1 }
```

### Taint + toleration
```bash
k taint node worker-1 env=prod:NoSchedule
```
```yaml
spec:
  tolerations:
  - { key: env, operator: Equal, value: prod, effect: NoSchedule }
```

### Schedule on a labeled set of nodes
```bash
k label node worker-1 gpu=true
k label node worker-2 gpu=true
```
```yaml
spec:
  nodeSelector: { gpu: "true" }
```

### Require pod to run on amd64 nodes only
```yaml
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - { key: kubernetes.io/arch, operator: In, values: [amd64] }
```

## 10. Cordon + Drain (operator's tools)

```bash
# Cordon — mark node unschedulable (existing pods stay, no new pods)
k cordon worker-1

# Drain — cordon + evict pods (for maintenance)
k drain worker-1 --ignore-daemonsets --delete-emptydir-data

# Uncordon — make schedulable again
k uncordon worker-1
```

Common workflow: node maintenance / upgrade:
```bash
k drain node-x --ignore-daemonsets --delete-emptydir-data
# ... do maintenance ...
k uncordon node-x
```

## 11. PodDisruptionBudget (PDB)

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata: { name: web-pdb, namespace: my-app }
spec:
  minAvailable: 2          # always keep 2 healthy
  # OR
  maxUnavailable: 1        # max 1 down at a time
  selector:
    matchLabels: { app: web }
```

PDB blocks voluntary disruptions (drains, upgrades) that would violate the budget. Critical for HA workloads during cluster ops.

## 12. Quick self-check

1. What's the difference between nodeSelector and nodeAffinity?
2. What's the difference between a taint with effect `NoSchedule` and `NoExecute`?
3. What's the modern replacement for pod-anti-affinity for spreading pods across zones?
4. What's a PodDisruptionBudget for?
5. What's the command to evict pods from a node for maintenance?

(Answers: nodeSelector is equality-only label match, nodeAffinity supports In/NotIn/Exists/operators + required vs preferred; NoSchedule prevents new pods landing, NoExecute also evicts existing pods that don't tolerate; Pod Topology Spread Constraints; blocks voluntary disruptions like drains/upgrades that would violate minAvailable / maxUnavailable; `kubectl drain <node> --ignore-daemonsets --delete-emptydir-data`.)
