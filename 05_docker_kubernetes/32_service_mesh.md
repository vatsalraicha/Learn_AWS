# 32 — Service mesh & zero-trust: Istio, Linkerd, Cilium, SPIFFE/SPIRE

## Why this module exists

East-west traffic (pod-to-pod) is plaintext by default. Service mesh adds mTLS, traffic management, and L7 policy. For regulated finance, mesh is the standard answer for "zero-trust between services."

---

## 1. The three meshes

### 1.1 Istio

- The most-deployed. CNCF Graduated 2024.
- Two architectures: **sidecar mode** (Envoy proxy per pod) and **ambient mode** (sidecarless: `ztunnel` per node + optional `waypoint proxy` per identity).
- Strong L7 policy via **AuthorizationPolicy** CRD.
- Built on Envoy.

### 1.2 Linkerd

- CNCF Graduated. Light-weight; written in Rust.
- Sidecar only.
- Simpler config; faster; smaller resource footprint.
- mTLS automatic.

### 1.3 Cilium Service Mesh

- Sidecarless; mesh functions implemented in the eBPF dataplane.
- Identity-based (Cilium identities).
- For shops already running Cilium as CNI: it's free.

For Capital One–style: **Istio** is the most-deployed; **Linkerd** is the easier-to-operate alternative. Cilium SM is gaining ground in 2025-2026.

---

## 2. mTLS — what the mesh actually does

Service mesh automates:

1. Each pod gets a SPIFFE-style X.509 identity (`spiffe://cluster.local/ns/ml-serving/sa/infer-server`).
2. Sidecar (or eBPF datapath) terminates outbound TLS and establishes mTLS to the peer.
3. Inbound: validates peer cert against trust domain; enforces AuthorizationPolicy.
4. App code is unchanged — sidecar transparently proxies plain HTTP/gRPC to the app.

```yaml
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata: { name: default, namespace: ml-serving }
spec:
  mtls: { mode: STRICT }                  # require mTLS for all pods in this ns
```

---

## 3. AuthorizationPolicy

```yaml
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata: { name: allow-clients, namespace: ml-serving }
spec:
  selector: { matchLabels: { app: infer-server } }
  action: ALLOW
  rules:
    - from:
        - source:
            principals: ["cluster.local/ns/ml-clients/sa/client-app"]
      to:
        - operation:
            methods: [POST]
            paths: ["/v1/models/*:predict"]
```

This is **L7 zero-trust**: only client-app SA can POST to /v1/models/*:predict. NetworkPolicy can't do this (L3/L4 only); the mesh can.

---

## 4. Istio sidecar vs ambient

### 4.1 Sidecar mode

Every pod gets an injected Envoy proxy (~50-100 MB RAM, ~50ms latency penalty). The classic; battle-tested.

### 4.2 Ambient mode (Istio 1.19 GA Sep 2023)

- **ztunnel** DaemonSet per node — does L4 mTLS for all pods.
- **Waypoint proxy** per service-account (deployed only when L7 policy is needed) — Envoy-based.
- No sidecar. Pods are unchanged.

Pros: lower overhead, no app pod resource budget for proxy, simpler upgrades.
Cons: newer; some features still being added.

For new Istio installs in 2025-2026: prefer **ambient**.

---

## 5. SPIFFE / SPIRE

[**SPIFFE**](https://spiffe.io/) is the spec for workload identity. **SPIRE** is the reference implementation.

- Issues short-lived X.509 SVIDs (SPIFFE Verifiable Identity Documents).
- Cross-cluster, cross-cloud, cross-on-prem identity federation.
- Used by Istio under the hood for trust domain management.

When to adopt explicitly: multi-cluster (active-active across regions/clouds) where you want unified identity. For single-cluster, the mesh's built-in identity is enough.

---

## 6. Service mesh + IRSA / Workload Identity

These are **complementary**:

- **IRSA / WIF / Entra Workload ID** — pod's identity to **cloud APIs** (S3, GCS, Blob).
- **Service mesh** — pod's identity to **other pods** (mTLS, AuthorizationPolicy).

A KServe inference pod has both: IRSA for reading S3 model artifacts, mesh identity for serving mTLS to API gateway.

---

## 7. cert-manager — the cert lifecycle layer

The mesh handles east-west mTLS certs. For ingress + app-level TLS, **cert-manager** issues from:

- Let's Encrypt (ACME) for public-facing.
- AWS PCA, GCP Private CA, Azure Key Vault — for internal.
- Vault PKI — for fully self-hosted.

Every Ingress / Gateway / VirtualService refers to a cert by Secret reference; cert-manager renews automatically.

---

## 8. Ambient + Cilium combo

A current 2025-2026 stack: **Cilium CNI + Cilium Service Mesh**. Single project, single dataplane, no sidecar. For new clusters this is increasingly the default.

---

## 9. Capital One signal

Service mesh isn't named in the C1 job posting, but for any K8s+KServe deployment in regulated finance, **mesh is implied**. mTLS + AuthorizationPolicy is the modern answer to "how do you secure pod-to-pod?" — the alternative (app-level TLS everywhere) is operational pain.

Likely C1 stack: **Istio ambient** (for the cleanest serverless-style + L7) OR **Cilium SM** (if Cilium is the CNI).

---

## Sanity check

1. mTLS — what does the mesh actually do that NetworkPolicy can't?
2. Istio sidecar vs ambient — name two reasons ambient is the 2025-2026 default.
3. AuthorizationPolicy at L7 — what verbs/paths can you constrain?
4. SPIFFE/SPIRE — when do you adopt it explicitly vs let the mesh use it implicitly?
5. IRSA and mesh identity — how do they complement each other?
6. cert-manager — what does it solve that the mesh's mTLS doesn't?

---

## Sources

- [Istio docs](https://istio.io/latest/docs/)
- [Istio ambient mesh](https://istio.io/latest/docs/ambient/)
- [Linkerd docs](https://linkerd.io/2/overview/)
- [Cilium Service Mesh](https://docs.cilium.io/en/stable/network/servicemesh/)
- [SPIFFE / SPIRE](https://spiffe.io/)
- [cert-manager](https://cert-manager.io/)

→ Next: [33 — Certification roadmap — KCNA, KCSA, CKAD, CKA, CKS](33_cert_roadmap.md)
