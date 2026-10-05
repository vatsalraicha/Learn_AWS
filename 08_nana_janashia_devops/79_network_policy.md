# 79 — NetworkPolicy Deep

## 1. What NetworkPolicy is

Pod-level firewall rules. By default, K8s pods can talk to any other pod. NetworkPolicy lets you restrict traffic.

**Requires a CNI plugin that implements NetworkPolicy** — Calico, Cilium, Weave do; some CNI plugins don't (flannel for example, unless paired with Calico).

## 2. The default state

Without any NetworkPolicy:
- All pods can reach all other pods
- All pods can reach all Services
- Pods can reach external internet (subject to node-level routing)

**NetworkPolicy adds restrictions, never grants.** Once one NP applies to a pod, only what's explicitly allowed is allowed.

## 3. The basic structure

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: my-policy
  namespace: my-app
spec:
  podSelector:                        # which pods this applies to (empty = all in namespace)
    matchLabels: { app: web }
  policyTypes: [Ingress, Egress]      # which directions
  ingress:                            # rules for inbound
  - from:
    - podSelector:
        matchLabels: { app: frontend }
    ports:
    - protocol: TCP
      port: 80
  egress:                             # rules for outbound
  - to:
    - podSelector:
        matchLabels: { app: db }
    ports:
    - protocol: TCP
      port: 5432
```

## 4. Default-deny (the recommended baseline)

```yaml
# Deny ALL ingress + egress to all pods in namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: default-deny-all, namespace: my-app }
spec:
  podSelector: {}                     # all pods
  policyTypes: [Ingress, Egress]
  # no ingress or egress rules = deny everything
```

Then add explicit allows for traffic you want.

## 5. Allow DNS (always needed)

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: allow-dns, namespace: my-app }
spec:
  podSelector: {}
  policyTypes: [Egress]
  egress:
  - to:
    - namespaceSelector:
        matchLabels: { kubernetes.io/metadata.name: kube-system }
      podSelector:
        matchLabels: { k8s-app: kube-dns }
    ports:
    - { protocol: UDP, port: 53 }
    - { protocol: TCP, port: 53 }
```

Without DNS allowed, pods can't resolve any name. First thing to add after default-deny.

## 6. Allow internal app traffic

```yaml
# Allow frontend → backend on port 8000
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: frontend-to-backend, namespace: my-app }
spec:
  podSelector:
    matchLabels: { app: backend }
  policyTypes: [Ingress]
  ingress:
  - from:
    - podSelector:
        matchLabels: { app: frontend }
    ports:
    - { protocol: TCP, port: 8000 }
```

## 7. Allow Ingress controller traffic

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: allow-ingress-controller, namespace: my-app }
spec:
  podSelector:
    matchLabels: { app: web }
  policyTypes: [Ingress]
  ingress:
  - from:
    - namespaceSelector:
        matchLabels: { kubernetes.io/metadata.name: ingress-nginx }
    ports:
    - { protocol: TCP, port: 80 }
```

## 8. Egress to external service

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: allow-egress-to-postgres, namespace: my-app }
spec:
  podSelector:
    matchLabels: { app: backend }
  policyTypes: [Egress]
  egress:
  - to:
    - ipBlock:
        cidr: 10.0.5.0/24       # RDS subnet
        except: [10.0.5.42/32]  # except this IP
    ports:
    - { protocol: TCP, port: 5432 }
```

## 9. Cross-namespace allow

```yaml
ingress:
- from:
  - namespaceSelector:
      matchLabels: { team: frontend }
    podSelector:
      matchLabels: { app: web }
```

This allows pods labeled `app=web` in any namespace labeled `team=frontend`. Combined namespace + pod selector = AND. Multiple `from:` entries = OR.

## 10. Cilium NetworkPolicy (richer, L7)

Cilium extends NetworkPolicy with **L7 rules** (HTTP method/path-based):

```yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata: { name: api-l7, namespace: my-app }
spec:
  endpointSelector:
    matchLabels: { app: api }
  ingress:
  - fromEndpoints:
    - matchLabels: { app: frontend }
    toPorts:
    - ports: [{ port: "8000", protocol: TCP }]
      rules:
        http:
        - method: "GET"
          path: "/api/users/.*"
        - method: "POST"
          path: "/api/login"
```

The standard K8s NP is L3/L4 only; Cilium NP can do L7. The K8s upstream is adding L7 features in 2025-2026.

## 11. Debugging NetworkPolicy

```bash
# Confirm CNI supports it
k get pods -A | grep -E "cilium|calico|weave"

# List policies
k get networkpolicy -A
k describe netpol my-policy

# Test connectivity from a debug pod
k run debug --rm -it --image=nicolaka/netshoot -n my-app -- bash
nc -zv backend 8000      # OK or denied?
curl -v http://backend:8000

# Cilium-specific: Hubble for observability
hubble observe --pod my-app/frontend-abc --to-pod my-app/backend-xyz
```

## 12. CKA exam — NetworkPolicy tasks

Common task:
> "Create a NetworkPolicy in namespace `my-app` that allows traffic from pods labeled `app=frontend` to pods labeled `app=backend` on TCP port 8000. Block all other ingress to backend pods."

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: allow-frontend-to-backend, namespace: my-app }
spec:
  podSelector: { matchLabels: { app: backend } }
  policyTypes: [Ingress]
  ingress:
  - from:
    - podSelector: { matchLabels: { app: frontend } }
    ports:
    - { protocol: TCP, port: 8000 }
```

When you apply this NP, it implicitly denies all other ingress to backend pods (because once any NP selects a pod for Ingress, only allowed traffic is permitted).

## 13. The model — once a NP applies, default-deny

A pod's traffic is **default-allow** UNTIL any NP selects it. Then:
- Pod is **default-deny** for that direction
- Only traffic explicitly allowed by all applying NPs is allowed
- Multiple NPs are **additive** (OR)

This is a common point of confusion: adding one restrictive NP doesn't deny the pod — it denies what's NOT covered by *any* NP rule on the pod.

## 14. Quick self-check

1. What's the default pod-to-pod connectivity in K8s?
2. What happens to a pod once any NetworkPolicy selects it?
3. Why must you allow DNS explicitly after a default-deny?
4. What's the difference between K8s NetworkPolicy and Cilium NetworkPolicy?
5. What CNI plugins implement NetworkPolicy?

(Answers: all pods can reach all other pods + Services + external (subject to host routes); pod becomes default-deny for the direction(s) the NP covers — only explicitly allowed traffic permitted; without DNS pod can't resolve any names — first allow after default-deny; K8s NP is L3/L4 (IP + port), Cilium NP adds L7 (HTTP method/path/header); Calico, Cilium, Weave, Antrea — Flannel does NOT alone (needs Calico for NP).)
