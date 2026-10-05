# 61 — K8s Core Concepts (CKA Refresher)

> Cross-link: [Topic 05 Module 16 — K8s architecture](../05_docker_kubernetes/16_k8s_architecture.md) and [Module 11](11_k8s_overview.md) of this topic. This module is the **CKA-exam-shaped refresher** of the essentials.

## 1. The architecture (control plane + nodes)

```
Control Plane (manage cluster state):
- kube-apiserver — REST API (only thing talking to etcd)
- etcd — distributed KV store; the source of truth
- kube-scheduler — assigns pods to nodes
- kube-controller-manager — runs controllers (deployment, replicaset, etc.)
- cloud-controller-manager (cloud) — talks to cloud APIs

Worker Node (run pods):
- kubelet — node agent; receives pod specs; tells runtime to start containers
- container runtime — containerd / CRI-O
- kube-proxy — implements Service IPs via iptables/IPVS/nftables
```

## 2. The objects (and what tests them)

| Object | CKA tasks |
|---|---|
| Pod | scheduling, troubleshooting |
| Deployment | rolling update, rollback, scale |
| StatefulSet | ordered start, stable identity |
| DaemonSet | one-pod-per-node tasks |
| Job / CronJob | run-to-completion |
| Service | networking, ClusterIP/NodePort/LoadBalancer |
| Ingress | host/path routing, TLS |
| ConfigMap / Secret | env + volume injection |
| PV / PVC / StorageClass | storage tasks |
| RBAC (Role/ClusterRole/RoleBinding) | access control |
| ServiceAccount | identity inside cluster |
| NetworkPolicy | pod-level firewall |
| Namespace | isolation |

## 3. kubectl + config file

```bash
# Where kubectl looks
echo $KUBECONFIG          # if set, this path
# else
~/.kube/config

# View config
kubectl config view
kubectl config get-contexts
kubectl config current-context
kubectl config use-context my-cluster
```

The kubeconfig has 3 sections:
- **clusters** — cluster endpoints + CA certs
- **users** — credentials (cert / token / exec)
- **contexts** — combinations of (cluster, user, namespace)

## 4. The minimal K8s YAML object

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
  namespace: default
spec:
  containers:
  - name: nginx
    image: nginx:1.27-alpine
```

Every object has:
- `apiVersion` — group/version (e.g., `v1`, `apps/v1`, `networking.k8s.io/v1`)
- `kind` — type
- `metadata` — name, namespace, labels, annotations
- `spec` — desired state
- `status` — current state (set by controllers, you don't write this)

## 5. YAML basics for the exam

```yaml
# Scalars
name: nginx
count: 3
ready: true
note: "quoted string"

# Lists (block + flow)
items:
  - a
  - b
items: [a, b, c]

# Maps (block + flow)
labels:
  app: web
  tier: frontend
labels: {app: web, tier: frontend}

# Multiline string
script: |
  set -e
  echo "hello"
  date

# Folded
description: >
  This is a
  long sentence on
  one line
```

For exam: master indentation discipline (2 spaces, consistent). YAML errors waste minutes.

## 6. The kubectl shortcuts the exam expects you to know

```bash
k get pods                           # list
k get pods -o wide                   # more
k get pods -A                        # all namespaces
k get pods -o yaml                   # YAML output
k get pods -o json                   # JSON
k get pods -o jsonpath='{.items[*].metadata.name}'
k describe pod <name>                # events + spec
k logs <pod>                         # logs
k logs -f <pod> -c <container>       # follow
k exec -it <pod> -- bash             # shell
k run debug --rm -it --image=alpine -- sh   # ephemeral debug pod

# Imperative create + dry-run scaffold
k create deployment web --image=nginx --replicas=3 --dry-run=client -o yaml > web.yaml
k create service clusterip web --tcp=80:80 --dry-run=client -o yaml
k create role app-reader --verb=get,list --resource=pods --dry-run=client -o yaml
k create rolebinding app-reader-binding --role=app-reader --serviceaccount=default:default --dry-run=client -o yaml
k create configmap app-config --from-literal=LOG_LEVEL=info --dry-run=client -o yaml
k create secret generic db-creds --from-literal=password=secret --dry-run=client -o yaml
k create cronjob hello --image=busybox --schedule="*/1 * * * *" -- /bin/sh -c "date"

# Edit live
k edit deployment web                # opens YAML in $EDITOR; live-applies on save
k scale deployment web --replicas=5
k rollout status deployment web
k rollout history deployment web
k rollout undo deployment web --to-revision=2

# Apply / delete
k apply -f file.yaml
k apply -f directory/
k delete -f file.yaml
k delete pod <name> --grace-period=0 --force      # force delete stuck pod

# Find things
k get pods --selector app=web                     # by label
k get pods -l app=web,tier=frontend
k get pods --field-selector status.phase=Running

# Resource inspection
k api-resources                                    # all resource kinds
k explain pod.spec.containers.livenessProbe       # docs
```

## 7. Labels + selectors

```yaml
metadata:
  labels:
    app: web
    tier: frontend
    version: v1
```

```bash
kubectl get pods -l app=web                       # equality
kubectl get pods -l 'tier in (frontend,backend)'  # set
kubectl get pods -l 'app=web,!cache'              # not
```

Labels drive: Deployment → ReplicaSet → Pod selection, Service → Pod selection, NetworkPolicy targets.

## 8. Namespaces

```bash
k get namespaces
k get ns
k create ns my-app
k delete ns my-app                                # deletes everything in ns

# Set default namespace for kubectl
k config set-context --current --namespace=my-app
```

Built-in namespaces:
- `default` — everything you don't specify
- `kube-system` — control plane components
- `kube-public` — readable by all (rarely used)
- `kube-node-lease` — node heartbeat data

## 9. Common Pod fields

```yaml
spec:
  containers:
  - name: app
    image: my-app:1.2.3
    imagePullPolicy: IfNotPresent          # Always | IfNotPresent | Never
    command: ["python"]
    args: ["-m", "my_app"]
    ports:
    - containerPort: 8000
    env:
    - name: DATABASE_URL
      value: postgresql://...
    - name: API_KEY
      valueFrom:
        secretKeyRef: { name: secrets, key: api-key }
    resources:
      requests: { cpu: "100m", memory: "128Mi" }
      limits:   { cpu: "500m", memory: "256Mi" }
    livenessProbe:
      httpGet: { path: /healthz, port: 8000 }
      initialDelaySeconds: 30
    readinessProbe:
      httpGet: { path: /readyz, port: 8000 }
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    emptyDir: {}
  restartPolicy: Always
  serviceAccountName: my-app-sa
```

## 10. The "show me what's in there" workflow

When you don't remember the syntax:
```bash
k explain deployment.spec.template.spec.containers
k explain pod.spec.containers.lifecycle
k explain ingress.spec.rules
k api-resources                # all resource short names + groups
k api-versions                 # available API versions
```

Use this constantly during the exam.

## 11. Quick self-check

1. What's the only component that talks to etcd?
2. What's the difference between `apiVersion: v1` and `apiVersion: apps/v1`?
3. What does `kubectl config use-context` do?
4. What's `kubectl explain pod.spec.containers.livenessProbe` for?
5. What's the difference between `imagePullPolicy: Always` and `IfNotPresent`?

(Answers: kube-apiserver — all other components go through it; v1 is the core API group, apps/v1 is the apps group (Deployment, StatefulSet, etc.); switches the active context — which cluster + user + default namespace kubectl uses; offline help — shows the schema for any nested field; Always re-pulls every time even if cached, IfNotPresent only pulls if image not local — use IfNotPresent for stable tags, Always when using `latest` (which you shouldn't in production).)
