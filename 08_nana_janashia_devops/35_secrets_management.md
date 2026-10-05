# 35 — Secrets Management — Vault + ESO + AWS Secrets Manager

## Why this module exists

K8s Secrets are base64, **not encrypted** at rest by default. Committing them to Git is malpractice. The 2026 stack: cloud-managed secret store (AWS Secrets Manager / Azure Key Vault / GCP Secret Manager / HashiCorp Vault) + **External Secrets Operator (ESO)** to sync them into K8s.

## 1. The K8s Secret problem

```yaml
apiVersion: v1
kind: Secret
metadata: { name: db-creds }
type: Opaque
data:
  password: c3VwZXItc2VjcmV0  # base64 of "super-secret"
```

Problems:
- `c3VwZXItc2VjcmV0` is **not encrypted**, just encoded — anyone with API access reads it
- Stored unencrypted in etcd by default (EKS encrypts via KMS if configured)
- **You cannot commit this to Git** without exposing the secret
- **You cannot rotate easily** — every consumer needs re-deploy

## 2. The secrets-stack pattern

```
Cloud secret store (Secrets Manager / Vault / Key Vault)
   ↑               ↓
   │ (audit)       │ (ESO sync)
   │               ↓
   │           K8s Secret
   │               ↓
   │           Pod mounts Secret as env or volume
   │               ↓
   └─── App reads value
```

Single source of truth = the cloud store. ESO syncs to K8s; pods consume normally.

## 3. HashiCorp Vault — the cross-cloud option

Vault (HashiCorp, BUSL since 2023; OSS fork **OpenBao** from Linux Foundation) is the long-standing multi-cloud secret store.

Capabilities:
- **KV** secrets engine (static)
- **Database** secrets engine (dynamic DB creds with TTL)
- **AWS / Azure / GCP** secrets engines (dynamic cloud creds)
- **PKI** engine (issue certs on demand)
- **Transit** engine (encryption-as-a-service; never store the key)
- **SSH** engine (SSH cert authority)
- **Identity** engine (entities + groups + aliases)

Auth methods: Kubernetes (use SA tokens), AWS IAM, JWT/OIDC, AppRole, LDAP, Okta, etc.

```bash
# CLI basics
vault server -dev   # dev mode
export VAULT_ADDR=http://127.0.0.1:8200
vault kv put secret/myapp password=super-secret
vault kv get secret/myapp
```

## 4. AWS Secrets Manager — the AWS-native default

```bash
aws secretsmanager create-secret \
  --name myapp/prod/db \
  --secret-string '{"username":"app","password":"super-secret"}'

aws secretsmanager get-secret-value --secret-id myapp/prod/db
```

Features:
- **Automatic rotation** (Lambda-based; RDS rotation built-in)
- **Cross-region replication**
- **KMS-encrypted** at rest
- **Versioning + staging labels** (AWSCURRENT, AWSPREVIOUS, AWSPENDING)
- IAM-controlled access; CloudTrail audit
- Cost: $0.40/secret/mo + $0.05/10k API calls

Alternative: **SSM Parameter Store** — free standard tier (4KB), no rotation; use for config, light secrets.

## 5. External Secrets Operator (ESO)

ESO bridges cloud secret stores → K8s Secrets. CRDs:
- **SecretStore** — connection to a secret backend (per namespace)
- **ClusterSecretStore** — cluster-wide version
- **ExternalSecret** — what to pull and where to put it

```yaml
# SecretStore — connection to AWS Secrets Manager
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-sm
  namespace: my-app
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:    # IRSA-based
          serviceAccountRef:
            name: my-app-sa
---
# ExternalSecret — pull a secret into the cluster
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: db-creds
  namespace: my-app
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-sm
    kind: SecretStore
  target:
    name: db-creds                    # creates K8s Secret with this name
    creationPolicy: Owner
  data:
    - secretKey: username
      remoteRef:
        key: myapp/prod/db
        property: username
    - secretKey: password
      remoteRef:
        key: myapp/prod/db
        property: password
```

Result: K8s Secret `db-creds` is auto-created and refreshed every hour from AWS Secrets Manager. Rotate in Secrets Manager → ESO syncs → pods see new value (assuming `restartPodsOnSecretChange` or pod reads at runtime).

## 6. ESO providers

ESO supports 30+ backends:
- AWS Secrets Manager, AWS SSM Parameter Store
- Azure Key Vault, Azure App Configuration
- GCP Secret Manager
- HashiCorp Vault, OpenBao
- 1Password, Doppler, Infisical
- Akeyless, Conjur
- Generic webhook + Kubernetes (cross-cluster)

## 7. Vault with K8s auth

```bash
# Enable K8s auth in Vault
vault auth enable kubernetes
vault write auth/kubernetes/config \
  kubernetes_host="https://kubernetes.default.svc"

# Create policy
vault policy write myapp - <<EOF
path "secret/data/myapp/*" { capabilities = ["read"] }
EOF

# Bind policy to K8s SA
vault write auth/kubernetes/role/myapp \
  bound_service_account_names=myapp-sa \
  bound_service_account_namespaces=my-app \
  policies=myapp \
  ttl=1h
```

Then ESO `SecretStore` references this:
```yaml
spec:
  provider:
    vault:
      server: "https://vault.example.com"
      path: "secret"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "myapp"
          serviceAccountRef: { name: "myapp-sa" }
```

## 8. Secrets that should never be in K8s Secret

Some patterns that ESO doesn't quite fix:
- **DB credentials with rotation** — better: use IAM auth (RDS IAM auth, Aurora IAM)
- **AWS credentials** — IRSA / Pod Identity (Module 30); no Secret at all
- **TLS certs** — cert-manager; no manual handling
- **Encryption keys for app-layer encryption** — Vault transit engine (encrypt-as-a-service)

The hierarchy: **eliminate the secret > rotate the secret > store the secret well**.

## 9. Sealed Secrets + SOPS (when you want secrets in Git)

When you can't run ESO, but still want Git-stored secrets:

### Sealed Secrets (Bitnami)
- Controller in cluster has a private key
- Encrypt secrets with public key → can commit ciphertext to Git
- Controller decrypts and creates plain K8s Secret

```bash
kubectl create secret generic db-creds --from-literal=password=secret \
  --dry-run=client -o yaml | \
  kubeseal -o yaml > sealed-db-creds.yaml
# Commit sealed-db-creds.yaml
kubectl apply -f sealed-db-creds.yaml
```

### SOPS (Mozilla, now CNCF)
- Encrypt fields in YAML/JSON files with KMS / Vault / age / pgp
- Edit with `sops file.yaml` → opens decrypted in editor → re-encrypts on save
- Works with helm-secrets, sops-secrets-operator, GitOps tools

Both are stepping stones to "secrets in cloud secret store + ESO."

## 10. Rotation strategy

The hardest part of secrets management. Strategies:
- **Dynamic credentials** (Vault DB engine, AWS Secrets Manager rotation) — credentials issued per-use, expire automatically
- **Scheduled rotation** — Lambda updates secret in Secrets Manager every N days; app reads at runtime
- **Manual rotation** — least bad; rotate on incident
- **App-level: rotate on read** — fetch fresh from Secrets Manager every N min; never cache long

## 11. Quick self-check

1. Why are K8s Secrets not actually secret?
2. What does ESO do?
3. What's the difference between AWS Secrets Manager and SSM Parameter Store?
4. What's Sealed Secrets and when use it?
5. Why is IRSA / Pod Identity better than storing AWS credentials in a K8s Secret?

(Answers: base64-encoded only — not encrypted — anyone with API access reads them; syncs cloud secret stores → K8s Secrets with refresh interval; Secrets Manager has rotation + cross-region + larger size, Parameter Store is free standard tier + 4KB max + no rotation; encrypts secrets so you can commit ciphertext to Git, controller in cluster decrypts at apply; no secret at all — pod gets temporary credentials via IAM, no rotation needed, no leak surface.)
