# 73 — Deployment Strategies — Rolling Update + ReplicaSet

## 1. The Deployment object — what it gives you

- **Declarative scale** (`replicas: N`)
- **Rolling updates** — gradually replace old pods with new
- **Rollback** — revert to a previous revision
- **History** — track which version is which

```yaml
apiVersion: apps/v1
kind: Deployment
metadata: { name: web }
spec:
  replicas: 5
  revisionHistoryLimit: 10
  selector: { matchLabels: { app: web } }
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%          # up to 25% extra pods during update
      maxUnavailable: 25%    # up to 25% can be unavailable
  template:
    metadata: { labels: { app: web } }
    spec:
      containers:
      - { name: web, image: my-app:1.2.3 }
```

## 2. ReplicaSet — managed by Deployment

You almost never create ReplicaSets directly. Deployment creates them:
```bash
k get deploy,rs,pods
# deployment.apps/web   5/5   5   5   2m
# replicaset.apps/web-abc   5   5   5   2m       (current)
# replicaset.apps/web-xyz   0   0   0   10m      (previous; kept for rollback)
```

When you update the Deployment's template:
1. Deployment creates a new ReplicaSet
2. New RS scales up, old RS scales down (rolling)
3. Old RS kept (at 0 replicas) for rollback up to `revisionHistoryLimit`

## 3. Deployment strategies

### RollingUpdate (default)
Gradually replace old pods with new. Configurable via `maxSurge` + `maxUnavailable`.

### Recreate
Delete all old pods first, then create new. Causes downtime.
```yaml
spec:
  strategy:
    type: Recreate
```
Use when:
- App can't run multiple versions simultaneously (e.g., schema migration that breaks old version)
- Single-replica apps where downtime is acceptable

## 4. Beyond Deployments — Argo Rollouts (Module 33)

For more advanced strategies (canary, blue-green, A/B):
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata: { name: web }
spec:
  strategy:
    canary:
      steps:
      - { setWeight: 20 }
      - { pause: { duration: 5m } }
      - { setWeight: 50 }
      - { pause: {} }     # wait for manual continue
      - { setWeight: 100 }
```

Or blue-green:
```yaml
spec:
  strategy:
    blueGreen:
      activeService: web-active
      previewService: web-preview
      autoPromotionEnabled: false
```

## 5. Performing an update

```bash
# Imperative (quick)
k set image deployment/web web=my-app:1.2.4

# Declarative
# (edit YAML, then)
k apply -f web.yaml

# Wait for rollout
k rollout status deployment/web --timeout=5m

# Watch
k rollout status deployment/web --watch
```

## 6. Rollback

```bash
# View history
k rollout history deployment/web

# Check a specific revision's spec
k rollout history deployment/web --revision=3

# Rollback to previous
k rollout undo deployment/web

# Rollback to specific revision
k rollout undo deployment/web --to-revision=3

# Pause / resume (useful for multi-step changes)
k rollout pause deployment/web
# Make multiple changes
k rollout resume deployment/web
```

## 7. The change-cause annotation

```bash
k annotate deployment web kubernetes.io/change-cause="upgrade to 1.2.4" --overwrite
k set image deployment/web web=my-app:1.2.4
```

The change-cause shows in `rollout history`:
```
REVISION  CHANGE-CAUSE
1         <none>
2         upgrade to 1.2.4
```

## 8. RollingUpdate parameters in depth

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 25%           # extra pods during update
    maxUnavailable: 25%     # how many can be unavailable
```

With 8 replicas:
- `maxSurge: 25%` → up to 2 extra pods (10 max during update)
- `maxUnavailable: 25%` → up to 2 fewer pods (6 min during update)

Tuning:
- **High velocity, no downtime tolerated**: `maxSurge: 50%, maxUnavailable: 0`
- **Limited capacity**: `maxSurge: 0, maxUnavailable: 25%`
- **Default**: `maxSurge: 25%, maxUnavailable: 25%`

## 9. Scaling

```bash
# Imperative
k scale deployment web --replicas=10

# Declarative (in YAML)
spec:
  replicas: 10

# Autoscaling (HPA — Module 70)
k autoscale deployment web --min=3 --max=20 --cpu-percent=70
```

If HPA is set, don't fight it in the YAML (HPA wins; manual scale only takes effect transiently).

## 10. DaemonSet — one pod per node

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata: { name: fluent-bit, namespace: logging }
spec:
  selector: { matchLabels: { app: fluent-bit } }
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
  template:
    metadata: { labels: { app: fluent-bit } }
    spec:
      tolerations:
      - { operator: Exists, effect: NoSchedule }      # run on tainted nodes too
      containers:
      - name: fluent-bit
        image: fluent/fluent-bit:3
```

DaemonSets are how you run "one pod per node": logging agents, metrics agents, CSI drivers, CNI components.

## 11. StatefulSet — ordered, stable

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata: { name: postgres }
spec:
  serviceName: postgres-headless
  replicas: 3
  selector: { matchLabels: { app: postgres } }
  template:
    metadata: { labels: { app: postgres } }
    spec:
      containers:
      - { name: postgres, image: postgres:17 }
  volumeClaimTemplates:
  - metadata: { name: data }
    spec:
      accessModes: [ReadWriteOnce]
      resources: { requests: { storage: 10Gi } }
```

StatefulSet guarantees:
- Pods named `postgres-0`, `postgres-1`, `postgres-2` (stable)
- Ordered startup (0 → 1 → 2)
- Ordered shutdown (2 → 1 → 0)
- Stable DNS: `postgres-0.postgres-headless.<ns>.svc.cluster.local`
- Per-pod PVC (templated)

For databases + anything requiring stable identity.

## 12. CKA Exam tasks

Common rolling-update tasks:
1. Create a Deployment with N replicas
2. Update image
3. Roll back
4. Set maxSurge / maxUnavailable
5. Pause / resume

Practice the imperative + declarative flows until both are muscle memory.

## 13. Quick self-check

1. What's the difference between a Deployment and a ReplicaSet?
2. What's the difference between RollingUpdate and Recreate strategy?
3. What does `revisionHistoryLimit: 10` give you?
4. When would you use a DaemonSet?
5. What does StatefulSet guarantee that Deployment doesn't?

(Answers: Deployment manages rolling updates by creating multiple ReplicaSets; ReplicaSet maintains N replicas of a pod template; RollingUpdate gradually replaces old with new (no downtime), Recreate deletes all old then creates new (downtime, but safe for incompatible versions); keeps last 10 old ReplicaSets at 0 replicas so you can roll back to any of them; one pod per node — for agents like logging/metrics/CSI/CNI; stable network identity per replica + ordered start/stop + per-pod PVC.)
