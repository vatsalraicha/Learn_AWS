# 36 — Service Mesh — Istio (mTLS + AuthZ)

## Why this module exists

A service mesh is an infrastructure layer that handles service-to-service communication: mTLS, traffic routing, retries, observability, authorization. Istio is the dominant mesh (CNCF Graduated April 2025). Alternatives: Linkerd (lighter), Cilium Service Mesh (eBPF-based, sidecar-less).

## 1. What problem a mesh solves

Without a mesh, every service has to handle (in code, per language):
- TLS between services
- Retries + timeouts + circuit breaking
- Load balancing
- Authentication (mTLS)
- Authorization (who can call what)
- Tracing instrumentation
- Metrics

A mesh handles all of this in a sidecar (or via eBPF), so apps don't have to.

## 2. Istio architecture

Two flavors:

### Sidecar mode (classic)
Each pod gets an **Envoy sidecar** auto-injected. All traffic in/out passes through Envoy. Control plane (Istiod) configures the sidecars.

### Ambient mode (GA Q4 2024 with 1.24)
**No sidecar.** Per-node ztunnel (L4 + mTLS) + optional per-namespace waypoint proxy (L7). Cheaper, lower latency, but newer.

```
┌─────────────────────────────────────────────────────────┐
│                       Istiod                            │  control plane
│       (PILOT - config, CITADEL - certs, GALLEY - val)   │
└─────────────────────────────────────────────────────────┘
                          │
            xDS APIs      │ configures
                          ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Pod A      │    │   Pod B      │    │   Pod C      │
│  ┌────────┐  │    │  ┌────────┐  │    │  ┌────────┐  │
│  │  app   │  │    │  │  app   │  │    │  │  app   │  │
│  └────────┘  │    │  └────────┘  │    │  └────────┘  │
│  ┌────────┐  │ →  │  ┌────────┐  │ →  │  ┌────────┐  │
│  │ envoy  │──┼────┼─▶│ envoy  │──┼────┼─▶│ envoy  │  │
│  └────────┘  │mTLS│  └────────┘  │mTLS│  └────────┘  │
└──────────────┘    └──────────────┘    └──────────────┘
```

## 3. Install (sidecar mode)

```bash
istioctl install --set profile=default -y
kubectl label namespace my-app istio-injection=enabled
# Restart pods → sidecars injected
```

For ambient:
```bash
istioctl install --set profile=ambient -y
kubectl label namespace my-app istio.io/dataplane-mode=ambient
```

## 4. mTLS — the killer feature

Istio gives you **automatic mTLS** between all meshed services. Certs issued by Istiod's built-in CA (or external like cert-manager + SPIRE). Rotation handled automatically.

### Modes
- **STRICT** — only mTLS allowed; non-mTLS rejected
- **PERMISSIVE** — accept both mTLS + plain (transitional default)
- **DISABLE** — no mTLS

```yaml
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata:
  name: default
  namespace: my-app
spec:
  mtls:
    mode: STRICT
```

This single object enforces mTLS for every pod in `my-app`. Pods that aren't in mesh can't talk to it; mesh pods authenticate each other automatically.

## 5. Traffic Routing

### VirtualService — routing rules
```yaml
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: reviews
  namespace: my-app
spec:
  hosts: [reviews]
  http:
  - match:
    - headers:
        x-canary: { exact: "true" }
    route:
    - destination: { host: reviews, subset: v2 }
  - route:
    - destination: { host: reviews, subset: v1, weight: 80 }
    - destination: { host: reviews, subset: v2, weight: 20 }
```

### DestinationRule — subsets + load balancing
```yaml
apiVersion: networking.istio.io/v1
kind: DestinationRule
metadata: { name: reviews, namespace: my-app }
spec:
  host: reviews
  subsets:
  - name: v1
    labels: { version: v1 }
  - name: v2
    labels: { version: v2 }
  trafficPolicy:
    connectionPool:
      tcp: { maxConnections: 100 }
      http: { http1MaxPendingRequests: 1000 }
    outlierDetection:
      consecutive5xxErrors: 5
      interval: 30s
      baseEjectionTime: 30s
```

This combination = 20% canary + sticky failover routing per service.

## 6. Gateway — ingress for the mesh

```yaml
apiVersion: networking.istio.io/v1
kind: Gateway
metadata: { name: web-gateway }
spec:
  selector: { istio: ingressgateway }
  servers:
  - port: { number: 443, name: https, protocol: HTTPS }
    tls:
      mode: SIMPLE
      credentialName: web-tls-cert
    hosts: ["app.example.com"]
---
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata: { name: web }
spec:
  hosts: ["app.example.com"]
  gateways: [web-gateway]
  http:
  - route:
    - destination: { host: web, port: { number: 80 } }
```

Istio Gateway is now being superseded by **K8s Gateway API** (vendor-neutral). Istio supports both.

## 7. Authorization Policies

```yaml
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata: { name: allow-frontend-to-api, namespace: my-app }
spec:
  selector:
    matchLabels: { app: api }
  action: ALLOW
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/my-app/sa/frontend-sa"]
    to:
    - operation:
        methods: [GET, POST]
        paths: ["/api/*"]
    when:
    - key: request.headers[x-tenant]
      values: ["tenant-a", "tenant-b"]
```

`principals` uses **SPIFFE IDs** derived from the K8s ServiceAccount. Authorization at L7 + workload-identity-based — far more granular than NetworkPolicy.

## 8. Istio AuthZ vs K8s NetworkPolicy

| | NetworkPolicy | Istio AuthorizationPolicy |
|---|---|---|
| **Layer** | L3/L4 (IP, port) | L7 (HTTP method, path, headers) |
| **Identity** | Labels / namespaces (IP-based) | SPIFFE / ServiceAccount (cryptographic) |
| **Encryption** | No | mTLS via PeerAuthentication |
| **Granularity** | Pod-to-pod port allow/deny | HTTP-method-and-path level |
| **Deny-all default** | Yes | No (you opt in) |
| **Cost** | Cheap (CNI feature) | Sidecar/ambient overhead |

Use both: NetworkPolicy as broad allow/deny; Istio AuthZ for HTTP-level rules + identity-based.

## 9. Observability for free

Istio out-of-the-box:
- **Metrics** — RED metrics per service via Envoy → Prometheus
- **Tracing** — request spans → Jaeger / Zipkin / Tempo
- **Access logs** — per request → log aggregator
- **Service mesh dashboard** — Kiali (separate, works with Istio)

Install Kiali:
```bash
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.24/samples/addons/kiali.yaml
```

## 10. Linkerd alternative

Linkerd 2.16 (mid-2024) is the simpler alternative:
- Rust-written proxy (vs Envoy in C++)
- Smaller resource footprint
- Simpler config + CLI
- **Buoyant (creator) moved to paid model for stable releases** in 2024 — controversial; some teams forked back

Choose Linkerd if Istio's complexity isn't justified. Linkerd does mTLS + traffic shifting + observability with much less surface area.

## 11. Cilium Service Mesh

Cilium 1.16+ provides service mesh via **eBPF** (kernel-level) instead of sidecars or per-node proxies. Same L4 mTLS + L7 routing. Pros: lowest overhead. Cons: less mature, fewer features than Istio.

If you already run Cilium as CNI (which is the default for new clusters in 2026), Cilium SM is a serious option.

## 12. Service mesh complexity trade-off

The honest question: **do you need a mesh**?

Skip a mesh if:
- < 20 services
- No mTLS requirement
- Simple L3/L4 NetworkPolicy is enough
- No need for L7 routing / canary at mesh layer

Get a mesh if:
- Strict mTLS compliance requirement (PCI-DSS, HIPAA, regulated)
- Many services with complex routing
- Need workload-identity-based AuthZ (zero trust)
- Multi-cluster federation

Capital One: Istio (ambient mode adoption in progress 2026) — required for SR 11-7 + PCI compliance posture.

## 13. Quick self-check

1. What does Istio's PeerAuthentication object do?
2. What's the difference between Istio sidecar mode and ambient mode?
3. What's a SPIFFE ID and why does Istio use them for AuthZ?
4. What's the difference between NetworkPolicy and Istio AuthorizationPolicy?
5. When should you skip a service mesh?

(Answers: configures mTLS mode (STRICT/PERMISSIVE/DISABLE) for pods in scope; sidecar = Envoy per pod, ambient = ztunnel per node + waypoint per namespace — less overhead but newer; cryptographically-secure workload identity derived from ServiceAccount — far stronger than IP/label-based identity; NetworkPolicy is L3/L4 + IP-based + cheap, Istio AuthZ is L7 + identity-based + mTLS — use both layered; small service count + no mTLS need + no L7 routing complexity.)
