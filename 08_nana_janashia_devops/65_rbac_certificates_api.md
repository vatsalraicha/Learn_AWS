# 65 — RBAC + ServiceAccounts + Certificates API

## 1. The K8s authorization layers

```
Request → API Server → Authentication → Authorization → Admission → etcd
                          ↓                ↓                ↓
                       who you are    can you do this   should you do this
                       (cert/token)   (RBAC/ABAC/Node)  (validating webhooks)
```

## 2. Authentication mechanisms

- **X.509 client certs** — most common for human admins
- **Bearer tokens** — ServiceAccount tokens (pods)
- **OIDC** — via Identity Center / Okta / etc.
- **Webhook** — custom (EKS uses this for aws-auth)
- **ServiceAccount tokens** — JWT bearer tokens

## 3. Authorization modes

| Mode | What |
|---|---|
| **RBAC** | Roles + Bindings; the default + recommended |
| **Node** | Built-in: kubelets get permissions only on their own node's resources |
| **ABAC** | Attribute-based, JSON policy file; rarely used |
| **AlwaysAllow / AlwaysDeny** | Don't use; AlwaysAllow is gaping security hole |
| **Webhook** | External authorization (rare) |

API server runs with `--authorization-mode=Node,RBAC` typically.

## 4. RBAC objects

| Object | Scope |
|---|---|
| **Role** | Permissions within a namespace |
| **ClusterRole** | Cluster-wide permissions OR a Role template usable in multiple namespaces |
| **RoleBinding** | Grants a Role to a subject (User/Group/SA) within a namespace |
| **ClusterRoleBinding** | Grants a ClusterRole to a subject cluster-wide |

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata: { name: pod-reader, namespace: my-app }
rules:
- apiGroups: [""]
  resources: ["pods", "pods/log"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["pods/exec"]
  verbs: ["create"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata: { name: alice-reader, namespace: my-app }
subjects:
- kind: User
  name: alice
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

Verbs: `get`, `list`, `watch`, `create`, `update`, `patch`, `delete`, `deletecollection`.

## 5. ServiceAccounts

Every pod runs as a ServiceAccount (default: `default` SA in its namespace).

```yaml
apiVersion: v1
kind: ServiceAccount
metadata: { name: my-app-sa, namespace: my-app }
automountServiceAccountToken: false   # don't mount unless pod needs K8s API
```

```yaml
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      serviceAccountName: my-app-sa
      containers: [...]
```

## 6. Bind a Role to a ServiceAccount

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata: { name: my-app-pod-reader, namespace: my-app }
subjects:
- kind: ServiceAccount
  name: my-app-sa
  namespace: my-app
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

The pod, when calling the K8s API, gets `pod-reader` permissions.

## 7. The `kubectl auth can-i` check (exam-critical)

```bash
# As current user
kubectl auth can-i list pods --namespace=my-app
# yes / no

# Impersonate (admin only)
kubectl auth can-i create deployments --as=alice --namespace=my-app
kubectl auth can-i list pods --as=system:serviceaccount:my-app:my-app-sa --namespace=my-app
```

Use this constantly during RBAC exam tasks to verify your bindings worked.

## 8. Certificates in Kubernetes

K8s uses PKI everywhere:
- **API server cert** — TLS for API
- **etcd certs** — peer + client TLS
- **kubelet certs** — auth between kubelet ↔ API server
- **front-proxy** certs — aggregation API
- **Client certs** — for human admins, e.g., kubeadm-generated admin.conf

All under `/etc/kubernetes/pki/` on control plane nodes.

## 9. Certificates API (creating user certs)

For a new human user, you need a client cert. The flow:

```bash
# 1. Generate private key + CSR
openssl genrsa -out alice.key 2048
openssl req -new -key alice.key -out alice.csr -subj "/CN=alice/O=dev"

# 2. Create K8s CertificateSigningRequest
cat <<EOF | kubectl apply -f -
apiVersion: certificates.k8s.io/v1
kind: CertificateSigningRequest
metadata: { name: alice }
spec:
  request: $(cat alice.csr | base64 | tr -d '\n')
  signerName: kubernetes.io/kube-apiserver-client
  expirationSeconds: 86400      # 24 hours
  usages: [client auth]
EOF

# 3. Approve
kubectl certificate approve alice

# 4. Retrieve signed cert
kubectl get csr alice -o jsonpath='{.status.certificate}' | base64 -d > alice.crt

# 5. Add to kubeconfig
kubectl config set-credentials alice --client-certificate=alice.crt --client-key=alice.key
kubectl config set-context alice-context --cluster=<cluster> --user=alice --namespace=my-app

# 6. Test
kubectl --context=alice-context get pods -n my-app
# error: alice has no permissions yet — bind a role
```

## 10. Creating a User Account end-to-end

```bash
# Above flow + bind a role
kubectl create role pod-reader --verb=get,list,watch --resource=pods -n my-app
kubectl create rolebinding alice-reader --role=pod-reader --user=alice -n my-app

# Test
kubectl --context=alice-context auth can-i list pods -n my-app    # yes
kubectl --context=alice-context auth can-i delete pods -n my-app  # no
```

## 11. Connecting to Cluster with a User

```bash
# Set context (alias for cluster+user+namespace)
kubectl config use-context alice-context

# Or explicit
kubectl --context=alice-context get pods -n my-app
```

In the kubeconfig:
```yaml
contexts:
- name: alice-context
  context:
    cluster: kubernetes
    user: alice
    namespace: my-app
users:
- name: alice
  user:
    client-certificate: /home/alice/alice.crt
    client-key: /home/alice/alice.key
```

## 12. Giving User permissions (ClusterRole + binding)

For cross-namespace: use ClusterRole + RoleBinding (per namespace) — grants ClusterRole's permissions but scoped to the namespace.

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata: { name: alice-view, namespace: my-app }
subjects:
- { kind: User, name: alice, apiGroup: rbac.authorization.k8s.io }
roleRef:
  kind: ClusterRole       # using built-in `view` ClusterRole
  name: view
  apiGroup: rbac.authorization.k8s.io
```

Built-in ClusterRoles: `cluster-admin`, `admin`, `edit`, `view`.

## 13. ServiceAccount + Permissions creation

Common exam task: create SA, role, and binding in one go.

```bash
# All in one
kubectl create sa pipeline -n my-app
kubectl create role deployer -n my-app \
  --verb=get,list,create,update,patch,delete \
  --resource=deployments,services,configmaps,secrets
kubectl create rolebinding pipeline-deployer -n my-app \
  --role=deployer --serviceaccount=my-app:pipeline

# Verify
kubectl auth can-i create deployments \
  --as=system:serviceaccount:my-app:pipeline -n my-app
```

## 14. Quick self-check

1. What's the difference between Authentication and Authorization?
2. What's the difference between Role and ClusterRole?
3. What's `kubectl auth can-i` for and when use it?
4. What's the CSR + approve + retrieve flow for creating a new user cert?
5. What's the canonical SA + Role + Binding triplet for least-privilege pod access to K8s API?

(Answers: AuthN verifies who, AuthZ checks what they can do; Role is namespace-scoped, ClusterRole is cluster-wide OR used cross-namespace via RoleBinding; verify whether the current (or impersonated) identity can do an action without actually trying it — fast check during RBAC exam tasks; create K8s CSR with CSR data → approve → retrieve signed cert → add to kubeconfig; ServiceAccount in app namespace + Role with narrow verbs/resources + RoleBinding tying them together — pod uses serviceAccountName.)
