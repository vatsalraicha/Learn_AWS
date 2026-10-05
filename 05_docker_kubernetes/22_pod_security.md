# 22 — Pod Security: PSA, SecurityContext, runtime classes (gVisor, Kata)

## Why this module exists

The Docker `run` hardening from module 10 has a K8s analogue: **Pod Security Admission (PSA)** + **SecurityContext** + (optionally) **RuntimeClass** for sandbox isolation. This module covers all three.

PodSecurityPolicy (PSP) was removed in 1.25. PSA is its replacement.

---

## 1. Pod Security Admission (PSA) — the namespace label gate

PSA is a built-in admission controller (since 1.23 beta, 1.25 GA) that classifies pods against three profiles:

| Profile | Allows |
|---|---|
| **privileged** | Unrestricted (current legacy). For DaemonSets, monitoring, CNI agents. |
| **baseline** | No privileged, no hostNetwork/hostPID/hostIPC, capabilities limited, no /proc mount tricks. |
| **restricted** | Baseline + non-root user, drop all capabilities, no privilege escalation, seccomp `RuntimeDefault`, no host volumes. |

Apply per namespace via labels:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ml-serving
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: latest
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

Three modes per profile:

- **enforce** — reject the pod at admission.
- **audit** — allow, but emit audit event.
- **warn** — allow, but `kubectl apply` shows a warning.

Typical pattern: `audit: restricted` and `warn: restricted` on every namespace (visibility); promote to `enforce: restricted` once warnings clear. DaemonSets typically run in `kube-system` with `privileged`.

---

## 2. SecurityContext — the per-pod and per-container knobs

```yaml
spec:
  securityContext:                   # pod-level
    runAsNonRoot: true
    runAsUser: 10001
    runAsGroup: 10001
    fsGroup: 10001
    fsGroupChangePolicy: OnRootMismatch
    seccompProfile: { type: RuntimeDefault }
    supplementalGroups: [10100]
  containers:
    - name: app
      securityContext:               # container-level (overrides pod where set)
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop: [ALL]
          add: [NET_BIND_SERVICE]
        runAsUser: 10001
      volumeMounts:
        - name: tmp
          mountPath: /tmp
  volumes:
    - name: tmp
      emptyDir: { sizeLimit: 64Mi }
```

This is the K8s equivalent of the module-10 `docker run` line:

- `runAsNonRoot: true` + `runAsUser: 10001` — non-root identity.
- `readOnlyRootFilesystem: true` + tmpfs `emptyDir` for writable paths — immutable runtime.
- `allowPrivilegeEscalation: false` — `no-new-privileges` equivalent.
- `capabilities.drop: [ALL]` + selective add — minimal capability set.
- `seccompProfile.type: RuntimeDefault` — default seccomp filter.

PSA `restricted` enforces all of these. The PSA → SecurityContext mapping is the "what is restricted actually checking" question.

---

## 3. AppArmor / SELinux annotations

K8s 1.30 GA'd `appArmorProfile` in SecurityContext:

```yaml
securityContext:
  appArmorProfile:
    type: RuntimeDefault             # or Localhost with localhostProfile
```

Before 1.30: an annotation `container.apparmor.security.beta.kubernetes.io/<container>: runtime/default`.

For SELinux:

```yaml
securityContext:
  seLinuxOptions:
    level: "s0:c123,c456"
```

In practice: stick with defaults (`RuntimeDefault` profile, default container_t label) unless you have a specific reason. Custom profiles are a maintenance hot mess.

---

## 4. RuntimeClass — picking the runtime per pod

A pod can specify a non-default runtime:

```yaml
spec:
  runtimeClassName: gvisor
```

Available `RuntimeClass` objects depend on the cluster:

| RuntimeClass | Runtime | Use |
|---|---|---|
| (none) | runc | Default; what 99% of pods use |
| `gvisor` | runsc | Sandboxed kernel; multi-tenant untrusted workloads |
| `kata` | Kata Containers | VM-isolated; strongest boundary |
| `nvidia` | nvidia-container-runtime | GPU pods (wrapper around runc) |

The cluster admin installs the runtime + creates the `RuntimeClass`:

```yaml
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata: { name: gvisor }
handler: runsc
scheduling:
  nodeSelector:
    sandboxed: "true"
```

For ML platforms running untrusted user notebooks (think internal "ML workspace as a service"): mandate `runtimeClassName: gvisor` or `kata` at admission (Kyverno / Gatekeeper rule). The performance hit is real (10-30% on CPU-bound workloads, more on syscall-heavy) but the boundary is qualitatively stronger.

For Capital One–style first-party ML: regular runc is fine — the workload is trusted; defense in depth comes from the surrounding controls (RBAC, NetworkPolicy, Falco).

---

## 5. seccomp profile customization

The default seccomp profile (`RuntimeDefault`) blocks ~50 historical syscalls. To go stricter:

```yaml
securityContext:
  seccompProfile:
    type: Localhost
    localhostProfile: my-app-seccomp.json
```

The file lives on each node at `/var/lib/kubelet/seccomp/my-app-seccomp.json`. Cluster admin distributes via DaemonSet that copies the file.

Generating custom profiles: tools like **[security-profiles-operator](https://github.com/kubernetes-sigs/security-profiles-operator)** record syscalls during a recording phase and emit a profile. Useful for high-value workloads.

---

## 6. Pod-level resource limits — additional security

Beyond requests/limits (module 17), `LimitRange` per namespace + `ResourceQuota` enforce caps:

```yaml
apiVersion: v1
kind: LimitRange
metadata: { name: defaults, namespace: ml-serving }
spec:
  limits:
    - type: Container
      default: { memory: 512Mi, cpu: 500m }
      defaultRequest: { memory: 128Mi, cpu: 100m }
      max: { memory: 8Gi, cpu: 4 }
---
apiVersion: v1
kind: ResourceQuota
metadata: { name: quota, namespace: ml-serving }
spec:
  hard:
    requests.cpu: "20"
    requests.memory: 40Gi
    requests.nvidia.com/gpu: "4"
    persistentvolumeclaims: "10"
```

For multi-tenant clusters, these are how you prevent one team from starving others.

---

## 7. PodSecurity exemptions

PSA has an exemptions mechanism (via admission config) — but **avoid exempting namespaces from `restricted`** unless absolutely necessary. The right pattern: keep all app namespaces `restricted`, put DaemonSets / monitoring / CNI agents in `kube-system` (PSA-privileged).

---

## 8. Beyond PSA — Kyverno / Gatekeeper

PSA covers ~80% of security baselines. For the rest (require resource limits, require labels, require image-pull policy, require non-default ServiceAccount, etc.), use **Kyverno** or **OPA Gatekeeper**. Module 23.

---

## 9. The "restricted" PSA template every team can copy

```yaml
apiVersion: apps/v1
kind: Deployment
metadata: { name: infer-server, namespace: ml-serving }
spec:
  replicas: 3
  selector: { matchLabels: { app: infer-server } }
  template:
    metadata:
      labels: { app: infer-server }
    spec:
      serviceAccountName: infer-server
      automountServiceAccountToken: false
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        fsGroup: 10001
        seccompProfile: { type: RuntimeDefault }
      containers:
        - name: app
          image: myorg/infer:1.2.3@sha256:abc...
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities: { drop: [ALL] }
          resources:
            requests: { cpu: 500m, memory: 1Gi }
            limits:   { cpu: 2,    memory: 2Gi }
          volumeMounts:
            - { name: tmp, mountPath: /tmp }
          ports: [{ containerPort: 8080 }]
          livenessProbe:
            httpGet: { path: /healthz, port: 8080 }
            initialDelaySeconds: 30
          readinessProbe:
            httpGet: { path: /readyz, port: 8080 }
      volumes:
        - { name: tmp, emptyDir: { sizeLimit: 64Mi } }
```

This passes PSA `restricted` enforcement. Use it as a template.

---

## Sanity check

1. PSA has three profiles. Map each to the kind of workload that fits.
2. Why was `PodSecurityPolicy` removed, and why is PSA easier to operate?
3. When does it make sense to use `runtimeClassName: gvisor`? `kata`?
4. Why is `readOnlyRootFilesystem: true` paired with an emptyDir for `/tmp`?
5. What does `fsGroupChangePolicy: OnRootMismatch` solve, and on what kind of volume?
6. Name two cluster-level enforcement objects (besides PSA) that multi-tenant clusters need.

---

## Sources

- [Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/)
- [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [SecurityContext](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)
- [Seccomp in K8s](https://kubernetes.io/docs/tutorials/security/seccomp/)
- [AppArmor in K8s](https://kubernetes.io/docs/tutorials/security/apparmor/)
- [RuntimeClass](https://kubernetes.io/docs/concepts/containers/runtime-class/)
- [gVisor on K8s](https://gvisor.dev/docs/user_guide/quick_start/kubernetes/)
- [Kata Containers on K8s](https://github.com/kata-containers/kata-containers/blob/main/docs/Developer-Guide.md)
- [security-profiles-operator](https://github.com/kubernetes-sigs/security-profiles-operator)

→ Next: [23 — Admission control — OPA Gatekeeper, Kyverno](23_admission_control.md)
