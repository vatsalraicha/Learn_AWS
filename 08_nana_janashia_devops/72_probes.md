# 72 — Liveness + Readiness Probes

## 1. Three kinds of probes

| Probe | Question | What if it fails |
|---|---|---|
| **Startup** | "Is the container ready to start receiving liveness/readiness probes?" | Container not killed yet — liveness deferred |
| **Liveness** | "Is the container still alive (not deadlocked)?" | Container restarted |
| **Readiness** | "Is the container ready to serve traffic?" | Pod removed from Service endpoints |

## 2. Probe types — HTTP, TCP, exec, gRPC

```yaml
# HTTP probe
livenessProbe:
  httpGet:
    path: /healthz
    port: 8000
    httpHeaders:
    - { name: X-Probe, value: liveness }
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 2
  successThreshold: 1
  failureThreshold: 3

# TCP probe (port open?)
livenessProbe:
  tcpSocket: { port: 5432 }
  initialDelaySeconds: 5

# Exec probe (command exit 0?)
livenessProbe:
  exec:
    command: [cat, /tmp/healthy]
  initialDelaySeconds: 5

# gRPC probe (K8s 1.24+)
livenessProbe:
  grpc:
    port: 50051
    service: my-service
```

## 3. Tuning probe parameters

- `initialDelaySeconds` — wait this long after container start before first probe
- `periodSeconds` — how often (default 10)
- `timeoutSeconds` — how long before probe times out (default 1)
- `successThreshold` — consecutive successes to consider healthy (default 1)
- `failureThreshold` — consecutive failures to declare unhealthy (default 3)

Common bug: `initialDelaySeconds: 0` + slow-starting app → liveness fails before app boots → restart loop.

## 4. Startup probes (the slow-start fix)

For apps that take 30s-5min to start (Java apps, complex initialization):
```yaml
startupProbe:
  httpGet: { path: /healthz, port: 8000 }
  failureThreshold: 30          # 30 × 10s = 5min max startup time
  periodSeconds: 10

livenessProbe:
  httpGet: { path: /healthz, port: 8000 }
  periodSeconds: 10              # only runs after startupProbe succeeds
```

Startup probe gives long startup window without making liveness probe wait that long every time.

## 5. Liveness vs Readiness — when each matters

- **Liveness fails** → container restarted (the K8s self-heal)
- **Readiness fails** → traffic stops being sent to pod (Service endpoint removed) but pod stays alive

**Common mistake**: same endpoint for both. Then:
- Liveness fails because DB is slow → container restarted (which doesn't fix the DB)
- Cascading restarts hide the real issue

**Better pattern**:
- **Liveness** = "am I deadlocked / unable to serve at all" (rare check, simple)
- **Readiness** = "can I serve a request right now (DB connected, etc.)"

```yaml
livenessProbe:
  httpGet: { path: /liveness, port: 8000 }   # /liveness only checks the app's own process
readinessProbe:
  httpGet: { path: /readiness, port: 8000 }  # /readiness checks DB, cache, dependencies
```

## 6. The "no liveness probe" school

Some teams argue: don't use liveness probes at all. Reasoning:
- Restarts mask the real issue
- Better to alert + investigate than to silently restart
- Crash + actual unrecoverable state → app should `exit(1)` itself, then K8s restarts

Use liveness probe only when you know a real deadlock condition exists that restart fixes.

## 7. Health endpoint patterns

```python
# Python Flask example
@app.route('/liveness')
def liveness():
    return jsonify({"status": "ok"}), 200

@app.route('/readiness')
def readiness():
    try:
        db.execute("SELECT 1")
        cache.ping()
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "not ready", "error": str(e)}), 503
```

Or use a library like `py-healthcheck`. Frameworks (FastAPI, NestJS, Spring Boot) have built-in.

## 8. Service traffic + readiness

K8s Service routes only to **Ready** endpoints:
```bash
k get endpoints my-svc
# NAME    ENDPOINTS              AGE
# my-svc  10.244.0.5:80,...      5m

# Endpoints with NotReady (failing readiness)
k get endpointslices -A
```

A pod stuck NotReady = no traffic; safe to investigate without user impact.

## 9. PreStop hooks (graceful shutdown)

```yaml
lifecycle:
  preStop:
    exec:
      command: ['sh', '-c', 'sleep 15 && /app/graceful-shutdown.sh']
```

Sequence on pod shutdown:
1. Pod marked Terminating
2. **Removed from Service endpoints** (no more new traffic)
3. PreStop hook runs
4. SIGTERM sent to PID 1
5. `terminationGracePeriodSeconds` (default 30) countdown
6. If still running, SIGKILL

For LB latency (~5-10s for SG → endpoint update propagation), a `sleep 10` in preStop avoids dropping in-flight requests.

## 10. CKA exam: configuring probes

```yaml
apiVersion: v1
kind: Pod
metadata: { name: web }
spec:
  containers:
  - name: web
    image: nginx
    ports: [{ containerPort: 80 }]
    livenessProbe:
      httpGet: { path: /, port: 80 }
      initialDelaySeconds: 5
      periodSeconds: 5
    readinessProbe:
      httpGet: { path: /, port: 80 }
      initialDelaySeconds: 2
      periodSeconds: 5
```

Quick imperative-edit pattern:
```bash
k run web --image=nginx --dry-run=client -o yaml > web.yaml
# Edit web.yaml to add probes
k apply -f web.yaml
```

Verify:
```bash
k get pod web                     # READY column should be 1/1
k describe pod web | grep -i liveness
```

## 11. Probes + autoscaling interaction

HPA scales based on metrics. Without readiness probes:
- New pods join Service endpoints immediately
- New pods get traffic before they're warm
- Latency spike on each scale-up

With readiness probes: new pods get traffic only when actually ready. **Always configure readiness for autoscaled workloads.**

## 12. Quick self-check

1. What happens when a liveness probe fails?
2. What happens when a readiness probe fails?
3. Why is using the same endpoint for both probes an anti-pattern?
4. What problem do startup probes solve?
5. What does the preStop hook give you?

(Answers: container is restarted; pod is removed from Service endpoints (no traffic) but stays alive; liveness check failing because DB slow causes restart that doesn't fix DB — cascading restarts hide root cause; gives long startup window without making liveness probe wait that long every interval — for slow-starting apps; chance to gracefully drain in-flight work before SIGTERM — typically a sleep to wait for LB to stop routing traffic + the actual shutdown.)
