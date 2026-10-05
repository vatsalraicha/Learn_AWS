# 63 — Deployments, Services & DNS

## 1. Deploying nginx (the canonical exam example)

```bash
# Imperative
k create deployment nginx --image=nginx:1.27-alpine --replicas=3

# Or scaffold YAML + edit
k create deployment nginx --image=nginx:1.27-alpine --replicas=3 \
  --dry-run=client -o yaml > nginx-deploy.yaml
```

```yaml
apiVersion: apps/v1
kind: Deployment
metadata: { name: nginx }
spec:
  replicas: 3
  selector: { matchLabels: { app: nginx } }
  template:
    metadata: { labels: { app: nginx } }
    spec:
      containers:
      - name: nginx
        image: nginx:1.27-alpine
        ports: [{ containerPort: 80 }]
        resources:
          requests: { cpu: "50m", memory: "32Mi" }
          limits:   { cpu: "200m", memory: "128Mi" }
```

```bash
k apply -f nginx-deploy.yaml
k get deploy,rs,pods                # Deployment + ReplicaSet + Pods
```

## 2. The Deployment → ReplicaSet → Pod hierarchy

```
Deployment (rolling-update controller)
   └── ReplicaSet (maintains N replicas)
        └── Pod (× N)
```

Deployment manages multiple ReplicaSets during rolling updates (old + new versions coexist briefly).

## 3. Creating an nginx Service

```bash
k expose deployment nginx --port=80 --target-port=80 --name=nginx-svc
# Creates ClusterIP Service
```

```yaml
apiVersion: v1
kind: Service
metadata: { name: nginx-svc }
spec:
  selector: { app: nginx }
  ports:
  - port: 80          # Service port
    targetPort: 80    # Container port
    protocol: TCP
  type: ClusterIP     # internal-only
```

Service types:
- **ClusterIP** (default) — internal only
- **NodePort** — exposes on every node at port 30000-32767
- **LoadBalancer** — provisions cloud LB
- **ExternalName** — DNS CNAME alias

## 4. Labels — the glue

Service selects Pods by label:
```yaml
spec:
  selector:
    app: nginx     # matches Pods with `metadata.labels.app: nginx`
```

If labels don't match, Service has no endpoints:
```bash
k get endpoints nginx-svc
# nginx-svc   <none>   <none>      # zero endpoints — selector mismatch
```

Debug:
```bash
k get pods --show-labels
k get svc nginx-svc -o yaml | grep -A 3 selector
```

## 5. Scaling Deployments

```bash
k scale deployment nginx --replicas=5
k get deploy nginx                  # READY 5/5

# Auto-scaling (HPA)
k autoscale deployment nginx --min=3 --max=10 --cpu-percent=70
k get hpa
```

HPA requires metrics-server installed.

## 6. Recording commands (legacy `--record` is deprecated)

To track which command made which rollout:
```bash
# Old (deprecated)
k set image deployment/nginx nginx=nginx:1.28-alpine --record

# Modern (use annotations)
k annotate deployment/nginx \
  kubernetes.io/change-cause="upgrade to 1.28" --overwrite
k set image deployment/nginx nginx=nginx:1.28-alpine
```

View history:
```bash
k rollout history deployment nginx
k rollout history deployment nginx --revision=2
```

## 7. Connecting to a Pod

```bash
# Exec into running pod
k exec -it <pod-name> -- bash

# Port forward (local 8080 → pod 80)
k port-forward pod/<pod-name> 8080:80
# Or to Service
k port-forward svc/nginx-svc 8080:80
# Browse http://localhost:8080

# Run an ephemeral debug pod
k run debug --rm -it --image=alpine -- sh

# From inside the cluster (debug pod)
apk add curl
curl http://nginx-svc:80
curl http://nginx-svc.default.svc.cluster.local:80
```

## 8. DNS basics in Kubernetes

K8s has built-in DNS (CoreDNS in kube-system). The naming convention:
```
<service>.<namespace>.svc.cluster.local
```

Resolution patterns:
- Same namespace: `nginx-svc` (short form)
- Cross-namespace: `nginx-svc.production` (mid form)
- Fully qualified: `nginx-svc.production.svc.cluster.local`

For pods (with stable hostname via subdomain):
```
<pod-hostname>.<service>.<namespace>.svc.cluster.local
```

This is how StatefulSets get stable network identity per replica.

## 9. CoreDNS

```bash
k get pods -n kube-system | grep coredns
# coredns-...   Running

# CoreDNS config
k get configmap coredns -n kube-system -o yaml
```

The default Corefile:
```
.:53 {
    errors
    health { lameduck 5s }
    ready
    kubernetes cluster.local in-addr.arpa ip6.arpa {
        pods insecure
        fallthrough in-addr.arpa ip6.arpa
        ttl 30
    }
    prometheus :9153
    forward . /etc/resolv.conf {
        max_concurrent 1000
    }
    cache 30
    loop
    reload
    loadbalance
}
```

Common exam task: a pod can't resolve `nginx-svc.production`. Debug:
```bash
k exec -it debug-pod -- nslookup nginx-svc.production
k get svc -n production           # confirm svc exists
k get endpoints -n production nginx-svc   # confirm has endpoints (labels match?)
k get pods -n kube-system -l k8s-app=kube-dns   # CoreDNS running?
k logs -n kube-system -l k8s-app=kube-dns       # CoreDNS errors?
```

## 10. Configuring Service IP address (ClusterIP range)

The control plane allocates ClusterIPs from `--service-cluster-ip-range` (default `10.96.0.0/12`). Configured via kubeadm config.

You can also set a specific IP per Service:
```yaml
spec:
  clusterIP: 10.96.0.100
```

Useful only for static-IP services with external dependencies. Otherwise let K8s allocate.

## 11. kubectl pro tips (exam-time speedups)

```bash
# Output format options
k get pods -o wide
k get pods -o yaml
k get pods -o jsonpath='{.items[*].metadata.name}'
k get pods -o custom-columns=NAME:.metadata.name,STATUS:.status.phase
k get pods --sort-by=.metadata.creationTimestamp

# Field selectors (not selectors on labels — different namespace)
k get pods --field-selector=status.phase=Running
k get pods --field-selector=spec.nodeName=worker01

# Multiple resources
k get deployments,services,pods

# Watch
k get pods --watch
k get pods -w

# All namespaces
k get pods -A

# Show resource quotas + limits
k describe ns my-app
k get resourcequotas -A
k get limitranges -A

# Save bash history
history > ~/exam-history.txt
```

## 12. Quick self-check

1. What's the Deployment → ReplicaSet → Pod hierarchy and what does each do?
2. What's a Service selector and what makes a Service have zero endpoints?
3. What's the FQDN format for a K8s Service?
4. What ConfigMap holds CoreDNS configuration?
5. What's the difference between `--selector` and `--field-selector` in kubectl?

(Answers: Deployment manages rolling updates, ReplicaSet maintains N replicas, Pod is the actual unit; label-based query that picks Pods to forward traffic to — zero endpoints when selector labels don't match any pod's labels; `<service>.<namespace>.svc.cluster.local`; coredns ConfigMap in kube-system namespace; --selector matches `metadata.labels`, --field-selector matches built-in fields like `status.phase` or `spec.nodeName`.)
