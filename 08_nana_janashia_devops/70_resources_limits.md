# 70 — Resource Requests + Limits

## 1. Why requests + limits matter

K8s uses these to:
- **Schedule** pods (request = guaranteed reservation; needs enough free)
- **Cap usage** (limit = max; CPU throttled; memory exceeded → OOMKilled)
- **Determine QoS class** (BestEffort / Burstable / Guaranteed)

## 2. The syntax

```yaml
resources:
  requests:
    cpu: 100m           # 0.1 vCPU
    memory: 128Mi       # 128 mebibytes
    ephemeral-storage: 1Gi
  limits:
    cpu: 500m           # 0.5 vCPU
    memory: 256Mi
    ephemeral-storage: 2Gi
```

### CPU units
- `1` = 1 vCPU (1 core)
- `100m` = 100 millicores = 0.1 vCPU
- `1500m` = 1.5 vCPU
- Fractions allowed: `0.5` = `500m`

### Memory units
- `Mi` = mebibytes (2^20 bytes) — preferred
- `Gi` = gibibytes
- `M` = megabytes (10^6 bytes, less common)
- `Ki`, `Pi`, `Ti` — kibibytes, pebibytes, tebibytes

## 3. QoS classes (derived from requests + limits)

| QoS | Condition |
|---|---|
| **Guaranteed** | Every container has equal requests = limits for CPU AND memory |
| **Burstable** | At least one container has requests OR limits set, but not Guaranteed |
| **BestEffort** | No requests or limits set at all |

Eviction order under pressure: BestEffort first, then Burstable, then Guaranteed last. Set Guaranteed for the most critical workloads.

## 4. CPU vs Memory limits — different behavior

| | CPU | Memory |
|---|---|---|
| **Over-limit** | Throttled (slow) | OOMKilled (exit 137) |
| **Compressible** | Yes | No |
| **Burstable** | Can use unused CPU briefly | No memory bursting |

This asymmetry matters:
- CPU limit slightly low → app slow but alive
- Memory limit slightly low → app killed → restarts → may CrashLoopBackOff

**Many practitioners drop CPU limits** (keep requests) and only set memory limits. Argument: CPU throttling causes worse outcomes than letting bursts happen.

## 5. Setting per-namespace defaults — LimitRange

```yaml
apiVersion: v1
kind: LimitRange
metadata: { name: defaults, namespace: my-app }
spec:
  limits:
  - type: Container
    default:                # used when pod doesn't specify a limit
      cpu: "500m"
      memory: "256Mi"
    defaultRequest:         # used when pod doesn't specify a request
      cpu: "50m"
      memory: "64Mi"
    max:                    # caps pod-specified limits
      cpu: "2"
      memory: "2Gi"
    min:                    # floor on pod-specified requests
      cpu: "10m"
      memory: "16Mi"
```

Now pods in `my-app` namespace without explicit resources get sane defaults.

## 6. Namespace capacity — ResourceQuota

```yaml
apiVersion: v1
kind: ResourceQuota
metadata: { name: my-app-quota, namespace: my-app }
spec:
  hard:
    requests.cpu: "10"
    requests.memory: "20Gi"
    limits.cpu: "20"
    limits.memory: "40Gi"
    pods: "50"
    persistentvolumeclaims: "10"
    services.loadbalancers: "2"
    secrets: "20"
```

Pods that exceed the quota fail to create. Use ResourceQuota to bound namespace usage in shared clusters.

```bash
k describe ns my-app             # shows quotas + usage
k get resourcequotas -A
```

## 7. Reading resource usage — metrics-server

```bash
# Install metrics-server (one-time per cluster)
k apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Now you can use top
k top nodes
k top pods
k top pods -A
k top pod my-pod --containers
```

## 8. Right-sizing — the discipline

The pattern:
1. Deploy with conservative requests (low) + memory limit (slightly above expected peak)
2. Observe for 1-2 weeks via Prometheus / `kubectl top`
3. Use **Vertical Pod Autoscaler (VPA)** in recommendation mode:
   ```bash
   k apply -f https://github.com/kubernetes/autoscaler/raw/master/vertical-pod-autoscaler/deploy/vpa-v1-crd.yaml
   ```
4. Look at p95 / p99 actual usage
5. Set request ≈ p95 typical; limit ≈ p99 + headroom

## 9. Horizontal Pod Autoscaler (HPA)

```bash
k autoscale deployment web --min=3 --max=20 --cpu-percent=70
```

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata: { name: web }
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target: { type: Utilization, averageUtilization: 70 }
  - type: Resource
    resource:
      name: memory
      target: { type: Utilization, averageUtilization: 80 }
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - { type: Percent, value: 50, periodSeconds: 60 }
```

HPA requires:
- metrics-server installed
- Pods have `resources.requests` set (HPA computes utilization relative to requests)

## 10. The 4 autoscalers

| Scaler | Scales |
|---|---|
| **HPA** | Replicas (horizontal) |
| **VPA** | Pod resource requests (vertical) |
| **CA / Karpenter** | Nodes |
| **KEDA** | Replicas based on custom metrics (queue depth, etc.) |

VPA + HPA conflict — don't use both for the same metric.

## 11. Capacity planning + headroom

Practical rule: keep node CPU utilization < 70% average, memory < 80%, to absorb spikes. K8s scheduler will refuse to schedule pods if their requests would exceed node capacity even if actual usage is fine — keep enough headroom.

## 12. Quick self-check

1. What does QoS class Guaranteed require?
2. Why is CPU limit considered controversial?
3. What's the difference between LimitRange and ResourceQuota?
4. Why does HPA require pods to have `resources.requests` set?
5. What's the exit code for OOMKilled?

(Answers: every container has requests = limits for CPU AND memory; CPU throttling causes hard-to-diagnose perf issues — many practitioners only set memory limits and CPU requests; LimitRange sets defaults + min/max for pods within a namespace, ResourceQuota caps total resources usable within a namespace; HPA computes utilization as actual_usage / requested — without requests it has no denominator; 137.)
