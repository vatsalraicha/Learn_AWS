# 46 — Deploy to Kubernetes from GitLab

## 1. Two ways to deploy to K8s from GitLab

| Method | When |
|---|---|
| **Push from CI (`kubectl set image`)** | Simple; CI has cluster credentials |
| **GitOps via GitLab Agent** | Modern; cluster pulls; better security |

## 2. The legacy push pattern

```yaml
deploy:
  image: alpine/k8s:1.31
  script:
    - mkdir -p ~/.kube
    - echo "$KUBECONFIG_DATA" | base64 -d > ~/.kube/config
    - kubectl set image deployment/app app=$IMAGE_TAG -n my-app
    - kubectl rollout status deployment/app -n my-app --timeout=5m
```

Problems:
- Kubeconfig stored in GitLab CI variables — sensitive credential persistence
- Pipeline has direct write access to the cluster
- Cluster trusts pipeline IPs by NetworkPolicy (or doesn't)

## 3. GitLab Agent for Kubernetes — the modern way

GitLab Agent (formerly KAS = Kubernetes Agent Server) reverses the trust direction:
- **Agent installed in cluster** as a Deployment
- Agent **dials out** to GitLab over WebSocket
- GitLab sends commands through the channel
- No inbound traffic to cluster; no kubeconfig in CI variables

### Install agent
1. GitLab UI → Operate → Kubernetes clusters → Connect → Configure agent
2. Get token + install command
3. Apply Helm chart to cluster:

```bash
helm repo add gitlab https://charts.gitlab.io
helm upgrade --install my-agent gitlab/gitlab-agent \
  --namespace gitlab-agent --create-namespace \
  --set image.tag=v17.10.0 \
  --set config.token=<agent-token> \
  --set config.kasAddress=wss://kas.gitlab.com
```

4. Configure agent in repo: `.gitlab/agents/<agent-name>/config.yaml`:
```yaml
ci_access:
  groups:
    - id: my-group   # Allow this group's pipelines to use the agent
gitops:
  manifest_projects:
    - id: my-group/k8s-manifests
      default_namespace: my-app
      paths:
        - glob: 'overlays/prod/*.yaml'
```

### Use in pipeline
```yaml
deploy:
  image: alpine/k8s:1.31
  script:
    - kubectl config use-context my-group/my-project:my-agent
    - kubectl set image deployment/app app=$IMAGE_TAG -n my-app
```

`kubectl config use-context <group/project>:<agent-name>` — auth handled transparently.

## 4. GitOps mode of the Agent

The Agent can be configured in **GitOps mode**: it watches a manifest repo and applies changes itself. No push-from-CI at all.

```yaml
# .gitlab/agents/my-agent/config.yaml
gitops:
  manifest_projects:
    - id: my-group/k8s-manifests
      default_namespace: my-app
      paths:
        - glob: 'apps/my-app/**.yaml'
      reconcile_timeout: 1m
      dry_run_strategy: server
```

The agent polls the manifest repo + applies changes. Updates to `my-app:1.2.3` in the manifest → agent pulls + applies. Same idea as ArgoCD/Flux but GitLab-native.

## 5. CI updates the manifest repo (the GitOps loop)

```yaml
# In application repo .gitlab-ci.yml
update-manifest:
  image: alpine/git
  before_script:
    - apk add --no-cache git curl yq
  script:
    - git clone https://gitlab-ci-token:$CI_JOB_TOKEN@gitlab.com/my-group/k8s-manifests.git
    - cd k8s-manifests
    - yq -i '.spec.template.spec.containers[0].image = strenv(IMAGE)' apps/my-app/deployment.yaml
    - git config user.email "ci@example.com"
    - git config user.name "CI"
    - git add . && git commit -m "deploy my-app $IMAGE_TAG"
    - git push origin main
  variables:
    IMAGE: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
```

The agent's GitOps poller picks up the commit + applies. Pipeline doesn't touch the cluster.

## 6. Create K8s cluster on Linode (LKE) — Nana's bootcamp

For learners + small projects, **Linode Kubernetes Engine (LKE)** is cheap:
- Free control plane
- ~$36/mo for a 3-node small cluster
- DigitalOcean DOKS, Civo, OVHcloud similar

```bash
# Linode CLI
linode-cli lke cluster-create --label test-cluster --region us-east \
  --k8s_version 1.31 --node_pools '[{"type":"g6-standard-2","count":3}]'
```

For real production: EKS / GKE / AKS / managed-K8s (your cloud).

## 7. Creating a GitLab User with restricted K8s permissions

In manifest GitOps mode, the agent uses its ServiceAccount in-cluster. Grant least-privilege:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: gitlab-agent
  namespace: gitlab-agent
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: gitlab-agent-app
  namespace: my-app
rules:
- apiGroups: ["", "apps", "networking.k8s.io"]
  resources: ["deployments", "services", "configmaps", "ingresses", "pods"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: gitlab-agent-app
  namespace: my-app
subjects:
- kind: ServiceAccount
  name: gitlab-agent
  namespace: gitlab-agent
roleRef:
  kind: Role
  name: gitlab-agent-app
  apiGroup: rbac.authorization.k8s.io
```

The agent can manage only the `my-app` namespace. No cluster-admin.

## 8. Deploying to multiple clusters

Register one Agent per cluster; pipelines pick context per environment:

```yaml
deploy-dev:
  script: kubectl config use-context my-group/my-project:dev-agent && kubectl apply -f manifests/dev/

deploy-staging:
  script: kubectl config use-context my-group/my-project:stg-agent && kubectl apply -f manifests/staging/

deploy-prod:
  script: kubectl config use-context my-group/my-project:prd-agent && kubectl apply -f manifests/prod/
  when: manual
```

## 9. Helm deploy from GitLab CI

```yaml
deploy:
  image: alpine/helm:3.16
  script:
    - helm upgrade --install my-app ./charts/my-app \
        --namespace my-app --create-namespace \
        --set image.tag=$CI_COMMIT_SHORT_SHA \
        --wait --timeout 5m
```

For GitLab Agent + Helm: `kubectl config use-context <agent>` then `helm` works.

## 10. Decision: push from CI vs GitOps

| | Push from CI | GitOps (Agent or ArgoCD) |
|---|---|---|
| **Cluster credentials in CI** | Yes (risk) | No |
| **Audit** | CI logs | Git history |
| **Drift detection** | None | Yes (reconciliation) |
| **Multi-cluster** | One credential per cluster in CI | One agent per cluster |
| **Rollback** | Re-run old pipeline | Git revert |
| **Setup complexity** | Lower | Higher upfront |
| **2026 recommendation** | Only for small / experimental | The default |

## 11. Quick self-check

1. What problem does GitLab Agent solve over kubeconfig-in-CI?
2. What's the difference between Agent CI access mode and GitOps mode?
3. Why grant the Agent only namespace-scoped permissions?
4. What does `kubectl config use-context my-group/my-project:my-agent` do?
5. Why is GitOps deploy preferred over push-from-CI in 2026?

(Answers: Agent dials out from cluster to GitLab, no inbound traffic and no kubeconfig stored in CI vars; CI access lets pipelines call kubectl via the agent (push mode), GitOps mode has the agent pull manifests from a repo + apply autonomously; least privilege — Agent compromise → only that namespace at risk, not the whole cluster; sets kubectl context to authenticate via the agent — no kubeconfig file needed; pipeline doesn't need cluster credentials, drift detection, Git-history audit, easy rollback.)
