# 11 — Kubernetes Orchestration

> Cross-link: [Topic 05 Modules 16–25](../05_docker_kubernetes/16_k8s_architecture.md) cover K8s exhaustively. This module is the **Nana-curriculum sweep** — touching every concept her DevOps Bootcamp covers in one pass.
>
> Full CKA depth lives in [Part 5 — Modules 60–80](60_cka_exam_logistics.md).

## 1. What problem does K8s solve

You have 50 containers across 10 nodes. Things to do that don't scale manually:
- Place containers across nodes optimally
- Restart crashed containers
- Replace dead nodes
- Roll out new versions safely (with rollback)
- Scale up/down based on load
- Route traffic to healthy instances
- Expose secrets + config
- Persist data across pod restarts

Kubernetes is the **distributed-systems answer**. Born inside Google (Borg → Omega → K8s), open-sourced 2014, CNCF since 2015, v1.0 in July 2015.

## 2. Core architecture

```
┌──────────────────────────────────────────┐    ┌─────────────────┐
│        Control Plane (HA: 3 nodes)        │    │   Worker Node   │
│  ┌─────────────────────────────────────┐ │    │  ┌───────────┐  │
│  │  kube-apiserver (REST API)         │ │◀───┤  │  kubelet  │  │
│  │  etcd (state)                       │ │    │  └─────┬─────┘  │
│  │  kube-scheduler                      │ │    │        │       │
│  │  kube-controller-manager             │ │    │  ┌─────▼─────┐  │
│  │  cloud-controller-manager (cloud)    │ │    │  │ container │  │
│  └─────────────────────────────────────┘ │    │  │  runtime  │  │
└──────────────────────────────────────────┘    │  │  (cri-o,  │  │
                                                  │  │ containerd│  │
                                                  │  └───────────┘  │
                                                  │  ┌───────────┐  │
                                                  │  │ kube-proxy│  │
                                                  │  └───────────┘  │
                                                  └─────────────────┘
```

- **etcd** — the single source of truth; everything else is stateless
- **kube-apiserver** — the only thing that talks to etcd; all components go through it
- **kube-scheduler** — assigns pods to nodes based on resources + constraints
- **controller-manager** — runs the controllers (Deployment, ReplicaSet, etc.)
- **kubelet** — node agent; receives pod specs, asks runtime to start containers
- **kube-proxy** — implements Service IPs via iptables/IPVS

## 3. The objects you'll use weekly

| Object | What |
|---|---|
| **Pod** | The smallest deployable unit; 1+ containers sharing network + storage |
| **Deployment** | Manages a ReplicaSet which manages pod replicas; supports rolling updates |
| **StatefulSet** | Stable identity per replica (pod-0, pod-1); ordered start/stop |
| **DaemonSet** | One pod per node (logging agent, GPU driver) |
| **Job / CronJob** | Run-to-completion; cron-scheduled jobs |
| **Service** | Stable virtual IP + DNS pointing to a set of pods |
| **Ingress** | HTTP routing into the cluster (alternative: Gateway API) |
| **ConfigMap** | Non-secret config injected as env or file |
| **Secret** | Secret data, base64-encoded, ideally external-secrets-mounted |
| **PersistentVolume / PersistentVolumeClaim** | Storage provisioning |
| **Namespace** | Logical isolation within cluster |
| **Role / ClusterRole / RoleBinding / ClusterRoleBinding** | RBAC |
| **NetworkPolicy** | Pod-level firewall rules |

## 4. Minikube + kubectl (local-cluster setup)

```bash
# Mac
brew install minikube kubectl
minikube start --driver=docker --cpus=4 --memory=8192

# verify
kubectl get nodes
kubectl get pods -A
```

Alternatives in 2026: **kind** (Kubernetes-in-Docker, faster than minikube), **k3d** (k3s-in-Docker, lighter), **Docker Desktop** (built-in K8s toggle), **Rancher Desktop** (alt to Docker Desktop).

## 5. kubectl essentials

```bash
kubectl get pods                                # list pods in current namespace
kubectl get pods -A                             # all namespaces
kubectl get pods -o wide                        # more info
kubectl get pods --watch                        # follow
kubectl describe pod <name>                     # events + spec
kubectl logs <pod>                              # logs
kubectl logs -f <pod> -c <container>            # follow specific container
kubectl exec -it <pod> -- bash                  # shell into pod
kubectl apply -f manifest.yaml                  # declarative create/update
kubectl delete -f manifest.yaml
kubectl rollout status deploy/my-app
kubectl rollout undo deploy/my-app              # rollback
kubectl scale deploy my-app --replicas=5
kubectl port-forward svc/my-svc 8080:80         # local port → service
kubectl run debug --rm -it --image=alpine -- sh # ephemeral debug pod
```

## 6. Sample Deployment + Service manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 3
  selector:
    matchLabels: { app: web }
  template:
    metadata:
      labels: { app: web }
    spec:
      containers:
      - name: web
        image: nginx:1.27-alpine
        ports: [{ containerPort: 80 }]
        resources:
          requests: { cpu: 100m, memory: 64Mi }
          limits:   { cpu: 500m, memory: 256Mi }
        readinessProbe:
          httpGet: { path: /, port: 80 }
        livenessProbe:
          httpGet: { path: /, port: 80 }
---
apiVersion: v1
kind: Service
metadata:
  name: web
spec:
  selector: { app: web }
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
```

```bash
kubectl apply -f web.yaml
kubectl get pods,svc
kubectl port-forward svc/web 8080:80
curl http://localhost:8080
```

## 7. Service types

| Type | When |
|---|---|
| **ClusterIP** | Internal-only (default) |
| **NodePort** | Exposes on every node at a high port; rarely used in production |
| **LoadBalancer** | Cloud-provider LB (AWS NLB/ALB, GCP TCP/HTTP LB, Azure LB); production |
| **ExternalName** | DNS CNAME alias |

Modern alternative: **Gateway API** (GA in K8s 1.31, late 2024) replacing Ingress for HTTP/L7.

## 8. Ingress (HTTP routing into cluster)

Need: an Ingress Controller (nginx, Traefik, HAProxy, AWS Load Balancer Controller).

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
          service: { name: web, port: { number: 80 } }
  tls:
  - hosts: [app.example.com]
    secretName: web-tls
```

## 9. Volumes + ConfigMap + Secret

```yaml
volumes:
- name: config
  configMap:
    name: my-config
- name: secrets
  secret:
    secretName: my-secret

volumeMounts:
- name: config
  mountPath: /etc/app/
- name: secrets
  mountPath: /etc/secrets/
  readOnly: true
```

PersistentVolumeClaim → PersistentVolume (statically or dynamically provisioned by StorageClass):

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: data
spec:
  accessModes: [ReadWriteOnce]
  storageClassName: gp3
  resources:
    requests: { storage: 10Gi }
```

## 10. Helm — the K8s package manager

```bash
helm install my-app ./chart
helm upgrade my-app ./chart
helm list
helm rollback my-app 1
```

Charts are templated YAML manifests with values. Standard charts: kube-prometheus-stack, ingress-nginx, cert-manager, ArgoCD. See [Topic 05 Modules](../05_docker_kubernetes/).

## 11. Managed K8s services

| Cloud | Service |
|---|---|
| AWS | EKS (covered Module 12) |
| GCP | GKE |
| Azure | AKS |
| Oracle | OKE |
| Linode | LKE (Nana uses this in her bootcamp) |
| DigitalOcean | DOKS |

All of them give you a managed control plane; you bring worker nodes (or use Fargate-like serverless).

## 12. Microservices in K8s + Best Practices preview

Patterns covered deeper in Part 5 (CKA modules):
- Pod Security Standards (restricted profile)
- NetworkPolicy default-deny
- ResourceQuotas + LimitRanges per namespace
- HPA / VPA / KEDA for autoscaling
- Cilium / Calico as CNI
- Prometheus + Grafana for monitoring
- ArgoCD / Flux for GitOps deploys

## 13. Quick self-check

1. What does etcd store?
2. What's the difference between a Deployment and a StatefulSet?
3. Why does a Service need to exist if Pods have IPs?
4. What's the difference between a ClusterIP and a LoadBalancer Service?
5. What's the modern alternative to Ingress as of late 2024?

(Answers: all cluster state — the source of truth; StatefulSet has stable identity + ordered start/stop for stateful workloads like databases; Pod IPs are ephemeral, Service IPs are stable; ClusterIP is internal-only, LoadBalancer provisions a cloud LB for external traffic; Gateway API.)
