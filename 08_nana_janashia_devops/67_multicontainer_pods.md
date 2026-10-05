# 67 — Multi-container Pods — Sidecar + Init

## 1. The 3 multi-container patterns

| Pattern | When |
|---|---|
| **Sidecar** | Helper alongside main container (log shipper, proxy) |
| **Init container** | Runs to completion BEFORE main containers start |
| **Adapter** | Transforms output of main container (normalizes metrics format) |
| **Ambassador** | Proxies main container's outbound traffic |

## 2. Init containers

Init containers run sequentially before main containers. Each must complete (exit 0) before the next starts. Used for:
- Wait for a dependency to be ready
- Run a migration / seed data
- Generate config files
- Pre-warm cache

```yaml
apiVersion: v1
kind: Pod
metadata: { name: web }
spec:
  initContainers:
  - name: wait-for-db
    image: busybox
    command: ['sh', '-c', 'until nslookup db; do echo waiting; sleep 2; done']
  - name: migrate
    image: my-app:1.2.3
    command: ['python', '-m', 'app.migrate']
  containers:
  - name: app
    image: my-app:1.2.3
    command: ['python', '-m', 'app.main']
```

Sequence:
1. `wait-for-db` runs until DB DNS resolves
2. `migrate` runs migrations and exits
3. `app` starts (main container)

If any init container fails, pod restarts (re-runs from init container 1).

## 3. Sidecar containers (the K8s 1.28+ way)

Pre-1.28: a sidecar was just "another container in `containers:`". This had problems:
- No ordering — main + sidecar started at same time
- Pod ready when *all* containers ready (sidecar startup delayed main readiness)
- No graceful shutdown ordering

K8s 1.28 added **first-class sidecar containers** — init containers with `restartPolicy: Always`:

```yaml
apiVersion: v1
kind: Pod
metadata: { name: web }
spec:
  initContainers:
  - name: log-shipper            # sidecar (init container with restartPolicy: Always)
    image: fluent-bit:3
    restartPolicy: Always         # ← makes it a sidecar
    volumeMounts:
    - { name: logs, mountPath: /var/log }
  containers:
  - name: app
    image: my-app:1.2.3
    volumeMounts:
    - { name: logs, mountPath: /app/logs }
  volumes:
  - { name: logs, emptyDir: {} }
```

Sidecar:
- Starts before main containers
- Pod is ready when main containers are ready (sidecar doesn't gate readiness)
- Sidecar lives for the pod's lifetime
- On pod shutdown: main container terminates first, then sidecar

## 4. Common sidecar use cases

### Log shipping
```yaml
- name: fluent-bit
  image: fluent/fluent-bit:3
  restartPolicy: Always
  volumeMounts:
  - { name: logs, mountPath: /var/log }
  - { name: fluent-config, mountPath: /fluent-bit/etc }
```

### Service mesh proxy (Istio sidecar)
Istio in sidecar mode auto-injects an Envoy sidecar into every pod (`istio-injection=enabled` namespace label).

### Reverse proxy / cache
```yaml
- name: nginx
  image: nginx:1.27-alpine
  ports: [{ containerPort: 80 }]
  volumeMounts:
  - { name: app-cache, mountPath: /cache }
- name: app
  image: my-app:1.2.3
  ports: [{ containerPort: 8000 }]    # only accessed via sidecar
```

### Secrets refresher / cert renewer
A sidecar polls Vault and refreshes mounted credentials.

## 5. Containers share what?

In one pod:
- **Same network namespace** — they share IP + can talk via localhost
- **Same volume mounts** (if specified) — share filesystem state via emptyDir
- **Same lifecycle** — start/stop together (with sidecar ordering for K8s 1.28+)
- **Same IPC** — by default share IPC namespace
- **Independent process namespace** by default; `shareProcessNamespace: true` to share

```yaml
spec:
  shareProcessNamespace: true   # both containers see each other's processes
```

## 6. Exposing Pod Information — Downward API

Containers can read pod metadata via env vars or volumes:

```yaml
containers:
- name: app
  image: my-app
  env:
  - name: POD_NAME
    valueFrom: { fieldRef: { fieldPath: metadata.name } }
  - name: POD_IP
    valueFrom: { fieldRef: { fieldPath: status.podIP } }
  - name: NODE_NAME
    valueFrom: { fieldRef: { fieldPath: spec.nodeName } }
  - name: POD_CPU_REQUEST
    valueFrom: { resourceFieldRef: { containerName: app, resource: requests.cpu } }
  volumeMounts:
  - { name: podinfo, mountPath: /etc/podinfo }
volumes:
- name: podinfo
  downwardAPI:
    items:
    - { path: labels, fieldRef: { fieldPath: metadata.labels } }
    - { path: annotations, fieldRef: { fieldPath: metadata.annotations } }
```

Use case: app logs include POD_NAME, structured logging can include node + pod IP without app-level config.

## 7. Inter-container communication patterns

### Same pod: localhost
```python
# app container connects to sidecar nginx on same pod:
requests.get("http://localhost:80")
```

### Same pod: shared file system (emptyDir)
```yaml
volumes:
- { name: shared, emptyDir: {} }
containers:
- name: producer
  volumeMounts: [{ name: shared, mountPath: /out }]
  command: ['sh', '-c', 'while true; do date >> /out/log; sleep 5; done']
- name: consumer
  volumeMounts: [{ name: shared, mountPath: /in }]
  command: ['sh', '-c', 'tail -f /in/log']
```

### Across pods: through Service
Use a Service; not direct pod-to-pod.

## 8. The `kubectl exec` with multi-container pods

```bash
# Default: first container
k exec -it my-pod -- bash

# Specific container
k exec -it my-pod -c sidecar -- bash

# Logs of specific container
k logs my-pod -c app
k logs my-pod -c app --previous
```

## 9. Init containers vs sidecar containers — exam questions

```yaml
spec:
  initContainers:
  - name: setup
    image: alpine
    command: ['sh', '-c', 'echo ready']      # exits → main containers can start
  - name: telegraf
    image: telegraf
    restartPolicy: Always                     # ← sidecar in K8s 1.28+
  containers:
  - name: app
    image: my-app
```

The `restartPolicy: Always` on an init container is the discriminator.

## 10. Common pitfalls

- **Sidecar not starting before main** — use restartPolicy: Always on init container (K8s 1.28+) or accept legacy parallel startup
- **Init container failure loop** — pod restarts everything; check init container logs
- **Resources counted per pod** — sum of all containers' requests/limits; large pods schedule less easily
- **One bad container in `containers:` doesn't fail others** — but pod isn't Ready unless all are Ready

## 11. Quick self-check

1. What's the difference between an init container and a sidecar?
2. What changed in K8s 1.28 about sidecars?
3. How do containers in the same pod communicate?
4. What does the Downward API expose?
5. Why does `restartPolicy: Always` on an init container make it a sidecar?

(Answers: init runs to completion before main starts, sidecar runs alongside main for pod lifetime; first-class sidecar via init container with restartPolicy: Always — gets ordering, doesn't gate pod readiness, graceful shutdown; via localhost (same network ns) or via emptyDir volumes (shared filesystem); pod metadata (name, IP, namespace, labels, annotations) + container resource limits — exposed as env vars or volume files; init container with always-restart becomes long-running but still has init-ordering semantics — that's the sidecar contract.)
