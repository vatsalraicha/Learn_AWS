# 75 — Kubernetes REST API

## 1. Everything is a REST call

`kubectl` is a CLI wrapper around HTTP REST calls to `kube-apiserver`. Knowing this:
- Lets you debug "kubectl says X" by inspecting the raw API
- Lets you write tools in any language
- Lets you understand watch streams, paging, server-side apply

## 2. The API tree

```
/api/v1/...                       # core API group (Pods, Services, etc.)
/apis/apps/v1/...                 # apps group (Deployment, StatefulSet)
/apis/networking.k8s.io/v1/...    # networking
/apis/rbac.authorization.k8s.io/v1/...
/apis/batch/v1/...
/apis/storage.k8s.io/v1/...
/apis/policy/v1/...
/apis/<group>/<version>/...       # custom resources via CRDs
```

```bash
k api-resources                   # all resources + their groups
k api-versions                    # all group/versions enabled
```

## 3. URL structure

```
GET  /api/v1/namespaces/my-app/pods
GET  /api/v1/namespaces/my-app/pods/my-pod
GET  /apis/apps/v1/namespaces/my-app/deployments
GET  /apis/apps/v1/namespaces/my-app/deployments/my-deploy
POST /api/v1/namespaces/my-app/pods        # body = pod spec
DELETE /api/v1/namespaces/my-app/pods/my-pod
PATCH  /api/v1/namespaces/my-app/pods/my-pod
```

## 4. Accessing API with `kubectl proxy`

The easiest way (handles auth for you):
```bash
k proxy &
# Starts a local proxy at http://127.0.0.1:8001

curl http://127.0.0.1:8001/api/v1/namespaces/default/pods
curl http://127.0.0.1:8001/apis/apps/v1/namespaces/default/deployments
```

Use this for ad-hoc exploration or scripts running on the same host as kubectl.

## 5. Direct access (without proxy)

```bash
APISERVER=$(kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}')
TOKEN=$(kubectl create token default --namespace=my-app)

curl -X GET "$APISERVER/api/v1/namespaces/my-app/pods" \
  -H "Authorization: Bearer $TOKEN" \
  --cacert /path/to/ca.crt
```

For ServiceAccount in a pod (the typical case):
```bash
# Inside a pod
TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
CACERT=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
NAMESPACE=$(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace)

curl --cacert $CACERT \
  -H "Authorization: Bearer $TOKEN" \
  https://kubernetes.default.svc/api/v1/namespaces/$NAMESPACE/pods
```

## 6. Verbs (HTTP methods)

| HTTP | K8s verb |
|---|---|
| GET (collection) | list |
| GET (single) | get |
| GET ?watch=1 | watch |
| POST | create |
| PUT | update (full replace) |
| PATCH (merge / strategic) | patch |
| DELETE | delete |
| DELETE (collection) | deletecollection |

## 7. Listing + filtering

```bash
# All pods cluster-wide
curl http://127.0.0.1:8001/api/v1/pods

# Pods in namespace
curl http://127.0.0.1:8001/api/v1/namespaces/my-app/pods

# Filter by label
curl "http://127.0.0.1:8001/api/v1/namespaces/my-app/pods?labelSelector=app=web"

# Filter by field
curl "http://127.0.0.1:8001/api/v1/namespaces/my-app/pods?fieldSelector=status.phase=Running"

# Page through large collections
curl "http://127.0.0.1:8001/api/v1/pods?limit=500&continue=<continueToken>"
```

## 8. Watch streams

```bash
# Long-poll for changes
curl "http://127.0.0.1:8001/api/v1/namespaces/my-app/pods?watch=1"
# Stream emits ADDED / MODIFIED / DELETED events
```

This is how controllers + operators stay synchronized with cluster state.

## 9. The `kubectl --v=N` debug

Add verbosity to see HTTP calls kubectl is making:
```bash
k get pods --v=8
# Shows the actual HTTP request + response

k get pods --v=10
# Shows even more (request body for POSTs)
```

Useful for "what is kubectl actually sending?" debugging.

## 10. Creating resources via API

```bash
cat <<EOF | curl -X POST \
  -H "Content-Type: application/yaml" \
  --data-binary @- \
  http://127.0.0.1:8001/api/v1/namespaces/default/pods
apiVersion: v1
kind: Pod
metadata: { name: api-created-pod }
spec:
  containers:
  - { name: nginx, image: nginx:1.27-alpine }
EOF
```

Or JSON:
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"apiVersion":"v1","kind":"Pod","metadata":{"name":"x"},"spec":{"containers":[{"name":"n","image":"nginx"}]}}' \
  http://127.0.0.1:8001/api/v1/namespaces/default/pods
```

## 11. Patches

Three patch types:
- **Strategic Merge Patch** (default; K8s-aware, smart on arrays)
- **JSON Merge Patch** (RFC 7396; simple object merge)
- **JSON Patch** (RFC 6902; operations: add/remove/replace)

```bash
k patch deployment web -p '{"spec":{"replicas":10}}'

k patch deployment web --type=json -p='[{"op": "replace", "path": "/spec/replicas", "value": 10}]'

k patch deployment web --type=merge -p '{"spec":{"replicas":10}}'
```

## 12. Server-Side Apply

The modern way to apply changes:
```bash
k apply -f deployment.yaml --server-side
```

Each "manager" (user or controller) owns specific fields. K8s tracks ownership; conflicts surface explicitly. Better for GitOps + multi-controller scenarios.

## 13. CRDs — extending the API

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata: { name: backups.acme.io }
spec:
  group: acme.io
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              schedule: { type: string }
              retention: { type: integer }
  scope: Namespaced
  names:
    plural: backups
    singular: backup
    kind: Backup
    shortNames: [bkp]
```

Once applied: `kubectl get backups`, `kubectl create -f backup.yaml`. CRDs are how operators extend K8s.

## 14. Quick self-check

1. What does `kubectl proxy` do?
2. How do you authenticate from a pod to the K8s API?
3. What's the difference between Strategic Merge Patch and JSON Patch?
4. What does `kubectl --v=8` show you?
5. What's a CRD and what does it enable?

(Answers: starts a local HTTP proxy that handles auth — you can curl http://localhost:8001 without managing tokens/certs; mount ServiceAccount token + ca.crt + namespace at /var/run/secrets/kubernetes.io/serviceaccount/ + use bearer token; Strategic is K8s-aware (knows arrays are lists vs sets), JSON Patch is operation-based (add/remove/replace at paths); the actual HTTP request kubectl makes to the API — useful for debugging; Custom Resource Definition — extends the API with new resource kinds — what operators use.)
