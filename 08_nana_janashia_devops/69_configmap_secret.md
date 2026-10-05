# 69 — ConfigMap + Secret (env + volume)

## 1. ConfigMap basics

```bash
# Create from literals
k create configmap app-config \
  --from-literal=LOG_LEVEL=info \
  --from-literal=ENV=prod

# From a file
k create configmap nginx-conf --from-file=nginx.conf

# From a directory
k create configmap config-files --from-file=./configs/

# From an env file
k create configmap envs --from-env-file=.env

# Scaffold YAML
k create configmap app-config --from-literal=X=1 --dry-run=client -o yaml
```

```yaml
apiVersion: v1
kind: ConfigMap
metadata: { name: app-config, namespace: my-app }
data:
  LOG_LEVEL: info
  ENV: prod
  app.conf: |
    server {
      listen 80;
      server_name example.com;
    }
binaryData:
  cert.bin: <base64>
```

## 2. Secret basics

```bash
# Generic (Opaque)
k create secret generic db-creds \
  --from-literal=username=app \
  --from-literal=password=super-secret

# TLS cert/key
k create secret tls web-tls \
  --cert=path/to/tls.crt --key=path/to/tls.key

# Docker registry creds
k create secret docker-registry regcred \
  --docker-server=registry.example.com \
  --docker-username=user --docker-password=pass

# Scaffold
k create secret generic db-creds --from-literal=password=x --dry-run=client -o yaml
```

```yaml
apiVersion: v1
kind: Secret
metadata: { name: db-creds }
type: Opaque
data:                              # base64-encoded values
  username: YXBw
  password: c3VwZXItc2VjcmV0
# Or use stringData for plain values
stringData:
  username: app
  password: super-secret
```

**Secrets are base64-encoded, NOT encrypted.** See Module 35 for proper secrets management.

Secret types:
- `Opaque` — generic
- `kubernetes.io/service-account-token` — auto-created for SAs
- `kubernetes.io/dockerconfigjson` — registry creds
- `kubernetes.io/tls` — TLS cert + key
- `kubernetes.io/basic-auth`, `kubernetes.io/ssh-auth`

## 3. Passing as Environment Variables

```yaml
containers:
- name: app
  image: my-app
  env:
  # From literal
  - name: APP_NAME
    value: my-app
  # From ConfigMap
  - name: LOG_LEVEL
    valueFrom:
      configMapKeyRef:
        name: app-config
        key: LOG_LEVEL
  # From Secret
  - name: DATABASE_PASSWORD
    valueFrom:
      secretKeyRef:
        name: db-creds
        key: password
  # All keys from a ConfigMap as env vars
  envFrom:
  - configMapRef: { name: app-config }
  - secretRef: { name: db-creds }
  # With a prefix
  - configMapRef: { name: app-config }
    prefix: CONFIG_
```

`envFrom` is the bulk way: every key in the ConfigMap becomes an env var.

## 4. Passing as Volumes

```yaml
spec:
  containers:
  - name: nginx
    image: nginx
    volumeMounts:
    - name: nginx-config
      mountPath: /etc/nginx/conf.d
      readOnly: true
    - name: tls-cert
      mountPath: /etc/nginx/tls
      readOnly: true
  volumes:
  - name: nginx-config
    configMap:
      name: nginx-conf
      defaultMode: 0644
      items:
      - { key: nginx.conf, path: default.conf }   # rename key→path
  - name: tls-cert
    secret:
      secretName: web-tls
      defaultMode: 0400
```

Each key in the ConfigMap/Secret becomes a file under the mount path.

## 5. Volume vs env — when to use which

| | Env vars | Volumes |
|---|---|---|
| **Visibility** | `env` in process; logged sometimes | Filesystem; explicit reads |
| **Update without restart** | No (env baked at start) | Yes (K8s syncs the volume) |
| **Multi-line values** | Awkward | Natural (`app.conf` file) |
| **Binary data** | No | Yes |
| **Security** | Often logged accidentally | Better (don't appear in process env) |

For secrets: prefer **volume mounts**. Env vars get logged.

## 6. Updating ConfigMaps / Secrets

```bash
k edit configmap app-config
# Modify, save
```

Behavior:
- **Env-var consumers**: don't see the update until pod restart
- **Volume consumers**: K8s syncs the volume (~minutes); app must re-read

To force pod restart on ConfigMap change:
- **kustomize**: configMapGenerator + hash suffix
- **Helm**: checksum annotation on Deployment
- **Reloader** (CNCF): watches ConfigMaps + restarts dependent Deployments

## 7. Immutable ConfigMaps + Secrets

```yaml
apiVersion: v1
kind: ConfigMap
metadata: { name: app-config }
immutable: true                  # locked; can't be modified
data: { ... }
```

Immutable benefits:
- Performance (kubelet doesn't watch for changes)
- Stability (no accidental modification)
- Use kustomize or helm-style hash-suffixed names for "updates" (create new immutable one, swap reference)

## 8. CKA exam tasks

Common asks:
- Create a ConfigMap from a literal
- Create a Secret from a file
- Make a Pod read a ConfigMap key as an env var
- Make a Pod mount a Secret as a volume
- Use a registry Secret for image pull

```bash
# Quick scaffold
k create cm app-config --from-literal=LOG=debug --dry-run=client -o yaml > cm.yaml
k create secret generic db-creds --from-literal=pw=secret --dry-run=client -o yaml > sec.yaml
k apply -f cm.yaml -f sec.yaml

# Pod consuming both
cat <<EOF | k apply -f -
apiVersion: v1
kind: Pod
metadata: { name: web }
spec:
  containers:
  - name: web
    image: nginx
    envFrom:
    - configMapRef: { name: app-config }
    - secretRef: { name: db-creds }
EOF

# Verify
k exec web -- env | grep -E "LOG|pw"
```

## 9. Encryption at rest for Secrets

Default: Secrets stored in etcd unencrypted (just base64). Better:
- **Envelope encryption with KMS** — etcd encrypts Secret values with a key from KMS
- Configure via `--encryption-provider-config` on apiserver

EKS: enable in cluster creation:
```hcl
cluster_encryption_config = {
  provider_key_arn = aws_kms_key.eks.arn
  resources        = ["secrets"]
}
```

## 10. Quick self-check

1. Why is `secret` base64 not encryption?
2. What's the difference between `env` and `envFrom`?
3. What happens to a pod's env vars when the source ConfigMap is updated?
4. Why prefer volume mounts over env vars for Secrets?
5. What does `immutable: true` give you on a ConfigMap?

(Answers: encoding is reversible without a key — anyone with API access can decode; env picks specific keys, envFrom imports all keys from a ConfigMap/Secret as env vars at once; nothing — env vars baked at pod start; restart needed to pick up changes; env vars are easier to accidentally log + show up in process listings, volumes require explicit reads; performance (no watch) + stability (can't modify) — must create new and swap reference for updates.)
