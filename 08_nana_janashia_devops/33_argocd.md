# 33 — ArgoCD for Application Delivery

## Why this module exists

ArgoCD is the dominant GitOps engine for K8s in 2026. CNCF Graduated 2022; v3.0 GA in 2025-04. Its competitor **Flux v2** is equally capable; both have ~30-40% adoption in K8s shops.

## 1. The GitOps premise

```
Traditional CD:
  CI → kubectl apply → cluster

GitOps:
  CI → commit manifest change → Git
       ↓
  ArgoCD pulls Git → applies to cluster → reconciles
```

Why GitOps wins:
- **Pipeline has no cluster credentials** (cluster pulls from Git)
- **Git history = deploy history** (auditable, revertable)
- **Drift detection** (ArgoCD knows when cluster diverges from Git)
- **Pull model scales** (one Argo per cluster manages many apps; no fan-out from CI)
- **Multi-cluster** is just adding more ArgoCD instances or one ArgoCD with many cluster registrations

## 2. ArgoCD concepts

- **Application** — a CRD pointing at a Git repo+path; represents one deployable
- **AppProject** — a grouping with permissions/restrictions on Applications
- **ApplicationSet** — templating for many Applications from one CRD
- **Sync** — the operation that applies Git state to cluster
- **Auto-sync** — automatic sync on Git change (default off for prod)
- **Self-heal** — re-apply if cluster drifts from Git
- **Sync waves** — order applications/resources

## 3. Install ArgoCD

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f \
  https://raw.githubusercontent.com/argoproj/argo-cd/v3.0.0/manifests/install.yaml

# Or via Helm
helm repo add argo https://argoproj.github.io/argo-helm
helm install argocd argo/argo-cd -n argocd --create-namespace
```

Access:
```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
# Get initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d
```

UI at https://localhost:8080 (admin / <password>).

## 4. Define an Application

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/myorg/my-app-manifests
    targetRevision: main
    path: overlays/prod
  destination:
    server: https://kubernetes.default.svc
    namespace: my-app
  syncPolicy:
    automated:
      prune: true        # delete resources removed from Git
      selfHeal: true     # re-apply on cluster drift
    syncOptions:
      - CreateNamespace=true
      - ApplyOutOfSyncOnly=true
```

ArgoCD watches the Git path; when it changes, syncs to the destination cluster + namespace.

## 5. Kustomize + Helm support

ArgoCD natively renders:
- **Plain YAML** — apply as-is
- **Kustomize** — `kustomization.yaml` in the path
- **Helm chart** — `Chart.yaml` in the path
- **Helm chart from repo** — separate field for chart name + values
- **Plugins** (jsonnet, custom) — via configMap config

Kustomize sample:
```
manifests/
├── base/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── kustomization.yaml
└── overlays/
    ├── dev/
    │   └── kustomization.yaml   # patches replicas=1, image tag
    ├── staging/
    │   └── kustomization.yaml
    └── prod/
        └── kustomization.yaml
```

## 6. App-of-Apps pattern

```yaml
# root-app.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: root
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/myorg/cluster-config
    path: applications/
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd
  syncPolicy:
    automated: { prune: true, selfHeal: true }
```

`applications/` contains more Application manifests. Bootstrap the cluster by `kubectl apply -f root-app.yaml`, and ArgoCD creates everything else.

## 7. ApplicationSet (for multi-cluster, multi-tenant)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: team-apps
  namespace: argocd
spec:
  generators:
  - matrix:
      generators:
      - list:
          elements:
          - { team: team-a }
          - { team: team-b }
          - { team: team-c }
      - clusters: {}    # all registered clusters
  template:
    metadata:
      name: '{{.team}}-{{.cluster.name}}'
    spec:
      project: '{{.team}}'
      source:
        repoURL: https://github.com/myorg/{{.team}}
        targetRevision: main
        path: deploy
      destination:
        server: '{{.cluster.server}}'
        namespace: '{{.team}}'
```

One CRD → many Applications, one per (team × cluster).

## 8. The CI → GitOps repo update pattern

```yaml
# CI pipeline pseudo-code:
build_image()
push_image_to_ecr()

# Update GitOps repo
git clone https://github.com/myorg/cluster-config
cd cluster-config
sed -i "s|image: app:.*|image: $ECR/app:$NEW_TAG|" overlays/prod/deployment.yaml
git commit -am "deploy app $NEW_TAG"
git push

# ArgoCD detects change and syncs
```

Better: use a dedicated tool like **Argo CD Image Updater** or **renovate** that updates manifests automatically when ECR has new tags.

## 9. Progressive delivery — Argo Rollouts

For canary/blue-green deployments beyond simple rolling update:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata: { name: web }
spec:
  replicas: 5
  strategy:
    canary:
      steps:
      - setWeight: 20
      - pause: { duration: 10m }
      - setWeight: 50
      - pause: { duration: 10m }
      - setWeight: 100
      analysis:
        templates:
        - templateName: success-rate
        startingStep: 2
  selector: { matchLabels: { app: web } }
  template:
    # ... pod spec
```

The analysis template can query Prometheus, Datadog, etc., to auto-rollback on error spike.

## 10. ArgoCD vs Flux

| | ArgoCD | Flux |
|---|---|---|
| **UI** | First-class | Weave Gitops + 3rd party |
| **CLI** | `argocd` | `flux` (lighter) |
| **Multi-tenancy** | Project + RBAC | Tenant CRD |
| **Multi-source app** | Yes (v2.6+) | Native |
| **Helm** | Renders, then applies | Native Helm |
| **Image updater** | Separate project | Native Image Reflector + Image Automation controllers |
| **Notifications** | Notifications Engine | Notification controller |
| **Bootstrapping** | App-of-Apps | `flux bootstrap` |

Picking: ArgoCD has better UX + UI; Flux is more composable + lighter. Capital One uses Flux internally (per Tech blog hints).

## 11. ArgoCD anti-patterns

1. **Manual `kubectl apply` after ArgoCD installed** — drift; ArgoCD will revert
2. **Storing secrets in Git** — use ESO/Vault/Sealed Secrets
3. **Auto-sync in prod** — surprise deploys; gate prod with manual sync
4. **No notifications** — sync failures go unnoticed
5. **Cluster-admin role for ArgoCD** — scope by AppProject; least privilege

## 12. Quick self-check

1. What's the security advantage of GitOps's pull model over CI-push?
2. What's the App-of-Apps pattern?
3. What does ArgoCD self-heal do?
4. What's the difference between ArgoCD and Argo Rollouts?
5. Why might you choose Flux over ArgoCD?

(Answers: pipeline doesn't need cluster credentials, cluster pulls from Git — fewer credentials to leak; one bootstrap Application that creates many others — fully Git-described cluster; if cluster state drifts from Git (manual edit), ArgoCD re-applies Git; ArgoCD does the sync, Rollouts is the progressive delivery engine for canary/blue-green; lighter, more composable, CLI-first, native Helm.)
