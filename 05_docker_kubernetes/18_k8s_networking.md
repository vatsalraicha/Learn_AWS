# 18 — K8s services & networking: ClusterIP, Ingress, Gateway API, NetworkPolicy, CNI

## Why this module exists

K8s networking is layered: pod network, service abstraction, ingress/gateway for external traffic, and NetworkPolicy for segmentation. Each layer has its own primitives — and every CNI plugin implements them differently.

---

## 1. The flat-pod-network promise

K8s requires: **every pod can talk to every other pod without NAT**. The CNI plugin implements this. Three families:

| Family | Examples | Datapath |
|---|---|---|
| **Overlay** (tunneled) | Flannel VXLAN, Calico VXLAN | Encapsulated UDP between nodes |
| **Routed (no overlay)** | Calico BGP, Cilium native routing | Underlying network knows pod CIDRs |
| **Cloud-native** (per-pod ENI) | AWS VPC CNI, Azure CNI | Pod gets an actual VPC IP |

Cloud-native CNIs (VPC CNI, Azure CNI) give pods routable VPC IPs — clean for SG-per-pod, NSG-per-pod. Tradeoff: pods-per-node limited by ENI/NIC capacity.

---

## 2. Service types

A **Service** is a stable virtual endpoint in front of a set of pods (selected by label).

| Type | Reachable from | Mechanism |
|---|---|---|
| **ClusterIP** (default) | Inside cluster only | kube-proxy / Cilium installs iptables/eBPF rules |
| **NodePort** | Any node IP on a high port (30000-32767) | iptables redirects nodeport → ClusterIP |
| **LoadBalancer** | External | Cloud-provided LB (ELB/ALB/NLB, GCP LB, Azure LB) |
| **ExternalName** | DNS CNAME only (no proxying) | CoreDNS returns CNAME |

ClusterIP is the default and most-used. For external traffic prefer **Ingress** or **Gateway API** (a higher abstraction on top of LoadBalancer).

### 2.1 Service discovery

CoreDNS resolves:
- `<svc>` (within namespace).
- `<svc>.<ns>` (cross-namespace).
- `<svc>.<ns>.svc.cluster.local` (FQDN).

Headless Service (`clusterIP: None`) returns pod IPs directly, not a VIP — required for StatefulSet member-by-DNS access.

---

## 3. Ingress vs Gateway API

### 3.1 Ingress (legacy but still everywhere)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
    - hosts: [api.example.com]
      secretName: api-tls
  rules:
    - host: api.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: api-server
                port: { number: 80 }
```

An **Ingress Controller** (nginx, Traefik, Envoy/Contour, AWS Load Balancer Controller, GCP GLB Controller, Azure Application Gateway Ingress Controller) watches Ingress resources and configures the actual data path.

Ingress is HTTP-only (mostly). For non-HTTP, you fell back to NLB or Service LoadBalancer with raw TCP.

### 3.2 Gateway API — the successor (v1.0 Oct 2023)

Gateway API is the next-gen replacement. Three layers:

- **GatewayClass** — vendor-specific config (e.g., AWS ALB, Cilium, Envoy Gateway).
- **Gateway** — an instance: listeners, ports, certs.
- **HTTPRoute / TCPRoute / TLSRoute / GRPCRoute / UDPRoute** — routing rules to backend services.

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata: { name: prod-gateway }
spec:
  gatewayClassName: aws-alb
  listeners:
    - name: https
      protocol: HTTPS
      port: 443
      tls: { mode: Terminate, certificateRefs: [{ name: api-tls }] }
---
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata: { name: api-route }
spec:
  parentRefs: [{ name: prod-gateway }]
  hostnames: ["api.example.com"]
  rules:
    - matches: [{ path: { type: PathPrefix, value: "/" } }]
      backendRefs: [{ name: api-server, port: 80 }]
```

Advantages over Ingress:
- Role-oriented (cluster operator owns GatewayClass+Gateway; app owns HTTPRoute).
- Native non-HTTP support (TCP/UDP/TLS/gRPC).
- Header-based / query-based routing, traffic-splitting (canary, A/B), and more — all standardized.

For new clusters: prefer Gateway API. The ingress controllers are migrating (Envoy Gateway, Contour, Cilium are early adopters; nginx-ingress is slower).

---

## 4. NetworkPolicy — the in-cluster firewall

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-allow
  namespace: ml-serving
spec:
  podSelector: { matchLabels: { app: api-server } }
  policyTypes: [Ingress, Egress]
  ingress:
    - from:
        - namespaceSelector: { matchLabels: { name: ml-clients } }
          podSelector: { matchLabels: { tier: client } }
      ports: [{ port: 8080, protocol: TCP }]
  egress:
    - to: [{ podSelector: { matchLabels: { app: postgres } } }]
      ports: [{ port: 5432 }]
    - to: [{ namespaceSelector: { matchLabels: { name: kube-system } }
            ,podSelector: { matchLabels: { k8s-app: kube-dns } } }]
      ports: [{ port: 53, protocol: UDP }]
```

Properties:

- **Default-deny is not automatic** — a vanilla cluster has no NetworkPolicy enforcement.
- The first NetworkPolicy that selects a pod **switches that pod to default-deny** for the policy types listed. Pods not selected by any policy: still allow-all.
- Egress rules must explicitly allow DNS (UDP/53 to kube-system kube-dns pods) — or every outbound resolution breaks.

### 4.1 CNIs that enforce NetworkPolicy

- **Calico** — full support, in BGP / VXLAN / eBPF modes.
- **Cilium** — full + L7 (HTTP method/path-aware).
- **Antrea** — full.
- **Weave Net** — full but project is unmaintained.

The default CNIs on managed K8s:
- **AWS VPC CNI** — basic NetworkPolicy support added in 2023 (also supports SG-per-pod, an AWS-specific belt-and-braces).
- **Azure CNI** — supports via Calico or Cilium addon.
- **GKE Dataplane V2** — Cilium-based, full support.

### 4.2 Beyond NetworkPolicy

L7-aware policy (e.g., "only POST /v1/predict, not /admin") is **not** in the K8s NetworkPolicy spec. For that you need:

- **Cilium L7 policy** — `httpRules` in CiliumNetworkPolicy CRD.
- **Service mesh** (Istio, Linkerd) — AuthorizationPolicy CRD.

For regulated finance: NetworkPolicy default-deny at namespace level + service mesh AuthorizationPolicy for L7. Both. Belt and braces.

---

## 5. The Cilium / eBPF revolution

Cilium replaces kube-proxy and CNI with an eBPF-based dataplane. Key wins:

- **Kube-proxy-less mode** — services implemented in eBPF, no iptables chains.
- **Identity-based policy** — instead of IP-based (IPs change with pod restarts).
- **L7 visibility** — Hubble (Cilium's observability) shows HTTP method/path/status without sidecars.
- **Mesh** without sidecar — Cilium Service Mesh provides mTLS without a per-pod proxy.

On modern GKE (Dataplane V2), EKS (`vpc-cni` with Cilium chained for policy, or AWS Cilium support), AKS (Azure CNI Powered by Cilium), Cilium is the default network-policy + visibility plane.

For the architect interview: knowing "Cilium replaces kube-proxy" + "Hubble gives L7 flow logs" + "Cilium can act as the service mesh too" is the modern stack.

---

## 6. CoreDNS — the cluster's DNS

CoreDNS runs as a Deployment (usually 2 replicas) in `kube-system`. It resolves:

- `<svc>.<ns>.svc.cluster.local` → ClusterIP.
- `<pod>.<ns>.pod.cluster.local` → pod IP (less common).
- External names — forwarded to upstream (cloud DNS, your corp DNS).

Performance pitfall: pods do many DNS lookups per second. **NodeLocal DNS Cache** is a DaemonSet pattern that caches DNS on each node — install it on any cluster doing serious traffic.

---

## 7. East-west TLS / mTLS

By default, pod-to-pod traffic in the cluster is **plaintext**. Most regulated shops want mTLS everywhere east-west.

Options:

- **Service mesh** (Istio, Linkerd) — automatic sidecar mTLS.
- **Cilium ambient mesh / mTLS** — sidecarless.
- **Application-level TLS** — apps mint and rotate their own certs (e.g., via cert-manager) and talk HTTPS to each other.

For Capital One–style postures: service mesh (Istio or Linkerd) is the standard answer. Module 32 covers this.

---

## 8. Ingress security checklist

- TLS termination at the ingress (cert-manager + Let's Encrypt or ACM/GAR-certs/AKV).
- HTTP→HTTPS redirect.
- HSTS header.
- WAF in front (AWS WAF on ALB, GCP Cloud Armor, Azure App Gateway WAF, or in-cluster ModSecurity).
- Rate limiting per IP / per user.
- Auth at the ingress where possible (OIDC via oauth2-proxy, IAP on GCP).

---

## 9. Common ingress controllers

| Controller | License | Notable |
|---|---|---|
| **ingress-nginx** | Apache 2.0 | The community default; widely deployed |
| **NGINX Inc.** | Mixed | Commercial; not the same project as ingress-nginx |
| **Traefik** | MIT | Auto-discovery, friendly |
| **Envoy/Contour** | Apache 2.0 | Heritage in cloud-native; Gateway API leader |
| **Envoy Gateway** | Apache 2.0 | Pure Gateway API impl on Envoy |
| **HAProxy Ingress** | Apache 2.0 | High-perf |
| **AWS Load Balancer Controller** | Apache 2.0 | Provisions ALB/NLB |
| **GKE Ingress / GCP Gateway** | Closed | Provisions GCP LB |
| **AGIC (Application Gateway Ingress Controller)** | Closed | Provisions Azure App Gateway |
| **Cilium Ingress / Gateway** | Apache 2.0 | Native to Cilium dataplane |

---

## 10. The networking-data-exposure summary

For a regulated ML workload:

1. **CNI**: Cilium (or VPC CNI + Cilium overlay for policy).
2. **Pod IPs**: VPC-routable if cloud (EKS, AKS, GKE); pod-network-only on-prem (Calico).
3. **Service mesh**: Istio (sidecar or ambient) or Linkerd for mTLS east-west.
4. **NetworkPolicy**: namespace-default-deny, explicit allows.
5. **Egress**: allowed only to declared destinations (cloud APIs via VPC endpoints, internal services).
6. **Ingress**: TLS terminated, WAF in front, OIDC auth, rate-limited.
7. **DNS**: NodeLocal DNS Cache; controlled upstream resolver.
8. **Observability**: Hubble for flow logs, Falco for runtime, OpenTelemetry for traces.

---

## Sanity check

1. Why is "NetworkPolicy default-deny" not automatic on a fresh cluster?
2. What's the migration story from Ingress to Gateway API for a team using `ingress-nginx` today?
3. Cilium replaces kube-proxy. What does it gain by doing so?
4. Why does an Egress NetworkPolicy that doesn't allow UDP/53 break the pod completely?
5. How does a Service mesh provide mTLS that NetworkPolicy doesn't?
6. AWS VPC CNI gives pods VPC IPs. What's the per-node limit, and how does it bite?

---

## Sources

- [K8s Services](https://kubernetes.io/docs/concepts/services-networking/service/)
- [Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/)
- [Gateway API](https://gateway-api.sigs.k8s.io/)
- [NetworkPolicy](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
- [Cilium docs](https://docs.cilium.io/)
- [Calico docs](https://docs.tigera.io/calico/latest/)
- [CoreDNS](https://coredns.io/)
- [NodeLocal DNS Cache](https://kubernetes.io/docs/tasks/administer-cluster/nodelocaldns/)

→ Next: [19 — Storage in K8s — PV, PVC, StorageClass, CSI, ephemeral, projected](19_k8s_storage.md)
