# 64 — External Services — NodePort, LoadBalancer, Ingress

## 1. Three ways to expose a Service externally

| Type | How | When |
|---|---|---|
| **NodePort** | Opens port 30000-32767 on every node | Dev/test; not for production |
| **LoadBalancer** | Cloud provisions external LB | Cloud K8s; one LB per Service |
| **Ingress** | HTTP/L7 routing via Ingress Controller | Many services share one LB; host/path routing |

## 2. NodePort

```yaml
apiVersion: v1
kind: Service
metadata: { name: web }
spec:
  selector: { app: web }
  type: NodePort
  ports:
  - port: 80           # ClusterIP port
    targetPort: 80     # Container port
    nodePort: 30080    # Optional; auto-allocated 30000-32767 if omitted
```

Access from outside: `http://<any-node-ip>:30080`.

Drawbacks:
- Limited port range
- Direct node IPs exposed
- No L7 routing
- Cumbersome at scale

## 3. LoadBalancer

```yaml
apiVersion: v1
kind: Service
metadata: { name: web }
spec:
  selector: { app: web }
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 80
```

On cloud K8s (EKS/GKE/AKS): provisions a cloud LB (NLB/ALB on AWS, GCP LB on GCP). On bare-metal K8s: stuck in Pending unless you install **MetalLB**.

Get the assigned IP:
```bash
k get svc web
# NAME   TYPE          CLUSTER-IP    EXTERNAL-IP     PORT(S)
# web    LoadBalancer  10.96.0.42    1.2.3.4         80:30123/TCP
```

Cost reality: one cloud LB per Service. 30 Services = 30 LBs = $$$. Hence Ingress.

## 4. Ingress + Ingress Controller

Ingress is an *abstract* HTTP routing rule. An **Ingress Controller** (Nginx, Traefik, HAProxy, AWS ALB Controller, GCP GLBC) implements it.

### Install Nginx Ingress Controller
```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace
```

This creates a single LoadBalancer Service for the controller; all your Ingress rules share it.

### Ingress object
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web
            port: { number: 80 }
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api
            port: { number: 8000 }
  tls:
  - hosts: [app.example.com]
    secretName: app-tls
```

## 5. The Ingress → Service → Pod chain

```
Client → DNS → cloud LB (Ingress Controller) → routes by host/path → Service (ClusterIP) → Pods
```

## 6. cert-manager — automatic TLS

```bash
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager --create-namespace \
  --set crds.enabled=true
```

Configure a ClusterIssuer:
```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata: { name: letsencrypt-prod }
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: ops@example.com
    privateKeySecretRef: { name: letsencrypt-prod-pk }
    solvers:
    - http01:
        ingress: { ingressClassName: nginx }
```

Annotate Ingress:
```yaml
metadata:
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts: [app.example.com]
    secretName: app-tls           # cert-manager will create this Secret
```

cert-manager issues + renews automatically.

## 7. Gateway API — the Ingress replacement (GA 2024)

K8s Gateway API (https://gateway-api.sigs.k8s.io) is the **modern replacement for Ingress**, GA in K8s 1.31 (Aug 2024).

Three CRDs:
- **Gateway** — listener (port + TLS); replaces "Ingress + LB Service"
- **HTTPRoute / GRPCRoute / TCPRoute / TLSRoute / UDPRoute** — routing rules
- **GatewayClass** — controller (like IngressClass)

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata: { name: web-gateway }
spec:
  gatewayClassName: nginx
  listeners:
  - name: https
    protocol: HTTPS
    port: 443
    tls:
      mode: Terminate
      certificateRefs:
      - { name: web-tls }
---
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata: { name: web }
spec:
  parentRefs: [{ name: web-gateway }]
  hostnames: [app.example.com]
  rules:
  - matches:
    - path: { type: PathPrefix, value: / }
    backendRefs:
    - { name: web, port: 80 }
```

Most exam content still uses Ingress (since CKA exam tracks K8s versions but slowly).

## 8. Path-based vs host-based routing

```yaml
# Host-based: different hosts → different services
rules:
- host: api.example.com
  http: { paths: [{ path: /, pathType: Prefix, backend: { service: { name: api, port: { number: 8000 }}}}] }
- host: web.example.com
  http: { paths: [{ path: /, pathType: Prefix, backend: { service: { name: web, port: { number: 80 }}}}] }

# Path-based: same host, different paths
rules:
- host: example.com
  http:
    paths:
    - path: /api
      pathType: Prefix
      backend: { service: { name: api, port: { number: 8000 }}}
    - path: /
      pathType: Prefix
      backend: { service: { name: web, port: { number: 80 }}}
```

## 9. ingressClassName matters

Multiple Ingress controllers can coexist in a cluster. `ingressClassName` selects which:
```yaml
spec:
  ingressClassName: nginx     # or "traefik" or "alb"
```

For exam: usually just `nginx`.

## 10. Common CKA Ingress tasks

```bash
# Create Ingress
k create ingress web --rule="app.example.com/*=web:80" --class=nginx

# View
k get ingress
k describe ingress web

# Debug: pods can't be reached through Ingress
k get ingress web -o yaml          # spec correct?
k get svc web                       # service exists?
k get endpoints web                 # has endpoints? (selector matching pods?)
k get pods -n ingress-nginx         # controller running?
k logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx   # controller errors?
```

## 11. Quick self-check

1. Why is one LoadBalancer Service per app a cost problem at scale?
2. What's the relationship between an Ingress object and an Ingress Controller?
3. What does `ingressClassName` do?
4. What's Gateway API replacing and when did it GA?
5. What does cert-manager add to an Ingress setup?

(Answers: each is a cloud LB charge ~$15-25/mo on AWS + ENIs + IPs; Ingress is the abstract routing spec, Controller is the actual proxy implementation (nginx, traefik, ALB controller); selects which Ingress Controller in a multi-controller cluster handles this Ingress; replacing Ingress with Gateway + HTTPRoute + GatewayClass — GA in K8s 1.31 Aug 2024; automatic Let's Encrypt TLS — issues + renews certs into K8s Secrets that Ingress mounts.)
