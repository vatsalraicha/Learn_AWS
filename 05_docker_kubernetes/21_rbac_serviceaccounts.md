# 21 — RBAC & ServiceAccounts: roles, cluster-roles, audit, least-privilege

## Why this module exists

90% of K8s "how did this get hacked" stories trace to a too-broad ServiceAccount or ClusterRoleBinding. RBAC is binary: either you understand it and grant least privilege, or you don't and grant `cluster-admin`.

---

## 1. The four RBAC primitives

| Object | Scope | Defines |
|---|---|---|
| `Role` | Namespaced | Verbs (get, list, ...) on resources (pods, secrets, ...) within one namespace |
| `ClusterRole` | Cluster | Same, but cluster-wide; can also reference cluster-scoped resources (Nodes, PVs, ...) |
| `RoleBinding` | Namespaced | Binds a Role (or ClusterRole) to subjects (User, Group, ServiceAccount) in one namespace |
| `ClusterRoleBinding` | Cluster | Binds a ClusterRole to subjects across the cluster |

Subjects:
- **User** — comes from auth (cert CN, OIDC sub, etc.).
- **Group** — also from auth (cert O, OIDC groups claim).
- **ServiceAccount** — a Pod's identity inside the cluster.

---

## 2. A least-privilege example

```yaml
# Namespace-scoped: this SA can read configmaps in ns ml-serving
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata: { name: cm-reader, namespace: ml-serving }
rules:
  - apiGroups: [""]
    resources: [configmaps]
    verbs: [get, list, watch]
---
apiVersion: v1
kind: ServiceAccount
metadata: { name: infer-server, namespace: ml-serving }
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata: { name: infer-cm-reader, namespace: ml-serving }
subjects:
  - kind: ServiceAccount
    name: infer-server
    namespace: ml-serving
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: cm-reader
```

Pod uses `serviceAccountName: infer-server`. Its in-pod kubeconfig (via projected SA token) lets it `get configmaps` in `ml-serving` only.

---

## 3. The default-everything anti-pattern

A fresh pod gets the **default** SA of its namespace, which has **no permissions** by default. But the legacy pre-1.6 behavior was to give it broad rights. Two related anti-patterns persist:

- **`automountServiceAccountToken: true`** (the default for pods) — the SA token is mounted at `/var/run/secrets/kubernetes.io/serviceaccount/`, and any process can talk to the API server. Set to `false` for pods that don't need API access (most app pods).
- **Binding `cluster-admin` to `system:serviceaccounts`** — gives every SA full power. Found in many "let's just get it working" sandboxes; never in prod.

### 3.1 The hardening default

```yaml
apiVersion: v1
kind: ServiceAccount
metadata: { name: infer-server, namespace: ml-serving }
automountServiceAccountToken: false
---
spec:
  serviceAccountName: infer-server
  automountServiceAccountToken: false             # also at pod level (overrides SA)
```

For pods that don't talk to the K8s API at all (most ML serving pods), disable the token mount entirely. Reduces blast radius if compromised.

---

## 4. Aggregating ClusterRoles

K8s ships several **system-** ClusterRoles. The default "viewer / editor / admin" three:

| ClusterRole | Verbs | Notes |
|---|---|---|
| `view` | get, list, watch on most resources except Secrets and Roles | Read-only |
| `edit` | get, list, watch, create, update, delete on most resources except RBAC and Namespaces | Most-used for developers |
| `admin` | edit + RBAC within namespace | Per-namespace "team admin" |
| `cluster-admin` | * on * | The big red button |

Custom roles can **aggregate**:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: monitoring-viewer
  labels:
    rbac.authorization.k8s.io/aggregate-to-view: "true"
rules:
  - apiGroups: [monitoring.coreos.com]
    resources: [prometheuses, servicemonitors]
    verbs: [get, list, watch]
```

This auto-aggregates into `view` — anyone with `view` now also has read access to PrometheusRules. Operators like kube-prometheus-stack use this pattern.

---

## 5. Audit the actual permissions

```bash
# What can this SA do in this namespace?
kubectl auth can-i --list --as=system:serviceaccount:ml-serving:infer-server -n ml-serving

# What can this user do?
kubectl auth can-i create pods --as=alice
kubectl auth can-i '*' '*' --as=alice -n ml-serving

# Who/what has cluster-admin?
kubectl get clusterrolebinding -o yaml | yq '.items[] | select(.roleRef.name == "cluster-admin")'
```

Tools to find over-permissive bindings:

- **[rbac-lookup](https://github.com/FairwindsOps/rbac-lookup)** — list all subjects and their permissions.
- **[rbac-tool](https://github.com/alcideio/rbac-tool)** — visualize and audit.
- **[KubiScan](https://github.com/cyberark/KubiScan)** — find risky pods/SAs.
- **[kubectl-who-can](https://github.com/aquasecurity/kubectl-who-can)** — answer "who can X on Y?"

For an architect interview: knowing these by name is enough to credibly say "I'd run an RBAC audit with rbac-lookup, find the broad bindings, and tighten."

---

## 6. The principal-of-least-privilege ladder

For a typical app pod, the SA needs:

- **Most pods: NOTHING.** They serve traffic and write logs; no K8s API call. `automountServiceAccountToken: false`.
- **Pods that read ConfigMaps/Secrets** — already do that via projected volumes; no API call needed.
- **Pods that need to discover services** — DNS works without API; no SA needed.
- **Pods that read other pods' state** (rare — usually only an operator does this) — explicit Role.
- **Pods that need cloud API access** — that's IRSA / Workload Identity, not K8s API.

If you're tempted to give a pod `list pods` permission: ask why. The answer is usually "I'm building an operator," and operators belong in their own namespace with explicit RBAC.

---

## 7. ServiceAccount projected tokens — the audience scoping

Modern (1.22+) ServiceAccount tokens are **projected volumes** with TokenRequest API. Crucially, they can have **audiences**:

```yaml
volumes:
  - name: api-token
    projected:
      sources:
        - serviceAccountToken:
            audience: api.internal.example.com
            expirationSeconds: 3600
            path: token
```

The token is valid only for the specified audience — so even if it leaks, you can't replay it against the K8s API. This is the mechanism IRSA / Workload Identity Federation use under the hood to federate K8s-issued tokens into cloud IAM tokens (modules 26-28).

---

## 8. RBAC for cluster admins — the human side

K8s authenticates users via:

- **Client certificates** (the kubeadm default; cert CN = user, cert O = group).
- **Static tokens** (rarely; only for testing).
- **OIDC** (the production default — Google, Okta, Azure AD, Auth0).
- **Authentication webhooks** (custom backends).

Most managed services have their own glue: EKS uses **AWS IAM mapped to RBAC via the `aws-auth` ConfigMap** (or the newer Access Entries API GA 2024); GKE uses **Google IAM mapped to K8s groups**; AKS uses **Microsoft Entra ID with K8s groups**.

For regulated finance: **OIDC + SCIM-managed groups + audit log to SIEM** is the minimum. No long-lived kubeconfig files; users authenticate per-session.

---

## 9. The aws-auth / Access Entries gotcha (EKS-specific)

For years, EKS clusters managed user/role to K8s identity via the `aws-auth` ConfigMap. This was infamous for being a single point of failure ("Bob edited the ConfigMap, locked everyone out, now we have to delete the cluster").

In 2024 AWS released **EKS Access Entries** — a proper API for "this IAM principal has this access policy." Migrate to it; deprecate the ConfigMap.

```bash
aws eks create-access-entry --cluster-name my-cluster --principal-arn arn:aws:iam::123:role/dev
aws eks associate-access-policy --cluster-name my-cluster --principal-arn arn:aws:iam::123:role/dev \
  --access-scope type=namespace,namespaces=ml-serving \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSEditPolicy
```

---

## 10. The audit log — what RBAC events look like

Sample audit policy:

```yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  - level: Metadata
    omitStages: [RequestReceived]
    resources:
      - group: "rbac.authorization.k8s.io"
        resources: [roles, rolebindings, clusterroles, clusterrolebindings]
  - level: RequestResponse
    verbs: [create, update, patch, delete]
    resources: [{group: "", resources: ["secrets"]}]
```

Every RBAC change is logged. Every Secret create/update/delete is logged with the request body. Ship to SIEM, alert on `system:masters` (= cluster-admin) bindings being created.

---

## 11. Hands-on detection lab

Find suspicious bindings (run on any cluster you administer):

```bash
# Bindings of cluster-admin
kubectl get clusterrolebindings -o json | \
  jq '.items[] | select(.roleRef.name == "cluster-admin") | .subjects'

# SAs that can list secrets cluster-wide
kubectl get clusterroles -o json | \
  jq '.items[] | select(.rules[]? | select(.resources[]? == "secrets" and .verbs[]? == "list")) | .metadata.name'

# Default SAs that have non-default bindings
for ns in $(kubectl get ns -o name); do
  ns=${ns#namespace/}
  kubectl get rolebindings -n $ns -o json | \
    jq --arg ns "$ns" '.items[] | select(.subjects[]? | select(.kind=="ServiceAccount" and .name=="default")) | {ns:$ns, name:.metadata.name, role:.roleRef.name}'
done
```

Combine with rbac-lookup output for the architect-grade audit.

---

## Sanity check

1. Why is `automountServiceAccountToken: false` a recommended default for app pods?
2. RoleBinding vs ClusterRoleBinding — when do you use each?
3. The `view` ClusterRole excludes Secrets by design. Why?
4. EKS Access Entries replaced the `aws-auth` ConfigMap. What problem did the ConfigMap have?
5. How does the `audience` field on a projected SA token reduce credential-replay risk?
6. Name three tools to audit "who can do what" on a cluster.

---

## Sources

- [Using RBAC Authorization](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
- [ServiceAccounts](https://kubernetes.io/docs/concepts/security/service-accounts/)
- [TokenRequest API](https://kubernetes.io/docs/reference/access-authn-authz/service-accounts-admin/)
- [Audit logging](https://kubernetes.io/docs/tasks/debug/debug-cluster/audit/)
- [EKS Access Entries](https://docs.aws.amazon.com/eks/latest/userguide/access-entries.html)
- [rbac-lookup](https://github.com/FairwindsOps/rbac-lookup)
- [KubiScan](https://github.com/cyberark/KubiScan)

→ Next: [22 — Pod Security — PSA, SecurityContext, runtime classes](22_pod_security.md)
