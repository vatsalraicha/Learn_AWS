# 20 — ConfigMaps & Secrets: etcd encryption, sealed-secrets, external-secrets

## Why this module exists

K8s Secrets are **base64-encoded plaintext in etcd by default**. That sentence shocks new operators. This module covers the four production patterns that fix it: etcd encryption-at-rest, Sealed Secrets, External Secrets Operator, and SOPS.

---

## 1. ConfigMap vs Secret

Both store key/value config. The differences:

- **Secret** values are auto-base64-decoded when mounted; ConfigMap values are mounted as-is.
- **Secret** has a `type` field (`Opaque`, `kubernetes.io/dockerconfigjson`, `kubernetes.io/tls`, ...).
- **Secret** is opt-in for etcd encryption-at-rest.
- **Audit log** treats them differently (Secret reads can be redacted/audited more aggressively).
- **`kubectl get secret`** redacts values by default (but `-o yaml` shows base64; `-o jsonpath` decodes).

ConfigMap: app config (feature flags, paths, log levels). Secret: passwords, tokens, certs.

```yaml
apiVersion: v1
kind: Secret
metadata: { name: db-creds }
type: Opaque
data:
  password: aHVudGVyMg==          # base64("hunter2") — NOT encryption
```

base64 is **not encryption**. Anyone with the YAML has the plaintext. Stop pretending otherwise.

---

## 2. Mounting

```yaml
spec:
  containers:
    - name: app
      image: myapp
      env:
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef: { name: db-creds, key: password }
      volumeMounts:
        - name: cfg
          mountPath: /etc/cfg
          readOnly: true
        - name: tls
          mountPath: /etc/tls
          readOnly: true
  volumes:
    - name: cfg
      configMap: { name: app-config }
    - name: tls
      secret:
        secretName: tls-cert
        defaultMode: 0400
```

**Prefer mounted files** over env vars (module 08). The `defaultMode: 0400` makes the file readable only by the container's UID.

---

## 3. etcd encryption-at-rest

By default etcd stores Secrets as plaintext (well, base64-encoded). An attacker with read access to etcd (stolen backup, control plane compromise) gets every secret. **Enable encryption-at-rest** via EncryptionConfiguration on the API server:

```yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources: [secrets]
    providers:
      - kms:                              # KMS v2 — GA in K8s 1.29
          apiVersion: v2
          name: kms-provider
          endpoint: unix:///var/run/kmsplugin/socket.sock
          timeout: 3s
      - aescbc:                           # fallback: file-key
          keys:
            - { name: key1, secret: <base64-32-byte-key> }
      - identity: {}                      # last: no encryption (read existing)
```

**On managed K8s**: encryption is provider-side.

- **EKS** — enable KMS envelope encryption at cluster create; uses your KMS CMK to wrap a DEK.
- **GKE** — Application-layer Secrets Encryption with a Cloud KMS key.
- **AKS** — KMS etcd encryption with Azure Key Vault key.

For regulated finance: **always** enable. Use a CMK / customer key. Audit usage.

---

## 4. The "Secrets in Git" problem

K8s manifests are GitOps. Plain Secret YAMLs in git = secrets in git = SOC2 finding. Three solutions:

### 4.1 Sealed Secrets (Bitnami)

A controller (`sealed-secrets-controller`) holds a private key in-cluster. You encrypt secrets with the public key:

```bash
echo -n hunter2 | kubectl create secret generic db-creds \
  --dry-run=client --from-file=password=/dev/stdin -o yaml | \
  kubeseal --controller-namespace=sealed-secrets \
           --controller-name=sealed-secrets-controller \
           -o yaml > db-creds.sealed.yaml
```

Commit `db-creds.sealed.yaml`. Only the controller can decrypt. Pros: stupid simple, no external system. Cons: cluster-bound (can't reuse SealedSecret across clusters easily); key rotation requires re-sealing all.

### 4.2 SOPS + age (or KMS)

[SOPS](https://github.com/getsops/sops) (Mozilla) encrypts YAML/JSON values with AWS KMS / GCP KMS / Azure Key Vault / age / PGP. Decryption requires the matching key. Combine with **helm-secrets** or **kustomize-sops** for GitOps.

```bash
sops --age age1abc... -e secret.yaml > secret.enc.yaml
git add secret.enc.yaml
```

At deploy time: `sops -d secret.enc.yaml | kubectl apply -f -`. Pros: cloud-native KMS integration, file-level encryption (not field-level for SealedSecrets). Cons: still produces a K8s Secret object at the end — only the storage-in-git is fixed.

### 4.3 External Secrets Operator (ESO)

The cleanest production pattern: don't put secrets in git or in etcd at all. ESO is a controller that **pulls** from your real secret store and creates K8s Secret objects on the fly.

```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata: { name: aws-secrets }
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef: { name: eso-sa }     # IRSA
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata: { name: db-creds }
spec:
  refreshInterval: 1h
  secretStoreRef: { name: aws-secrets, kind: SecretStore }
  target: { name: db-creds }
  data:
    - secretKey: password
      remoteRef: { key: prod/db/postgres, property: password }
```

ESO supports: AWS Secrets Manager + Parameter Store, GCP Secret Manager, Azure Key Vault, HashiCorp Vault, 1Password, Akeyless, Doppler, IBM, Oracle, Pulumi ESC. The current de facto standard for K8s secret integration.

### 4.4 Secrets Store CSI Driver

Alternative: **don't create a K8s Secret at all.** Mount directly from the secret store at pod start:

```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata: { name: db-creds }
spec:
  provider: aws                                   # or gcp, azure, vault
  parameters:
    objects: |
      - objectName: "prod/db/postgres"
        objectType: "secretsmanager"
        jmesPath:
          - path: "password"
            objectAlias: "password"
---
# In the pod spec:
volumes:
  - name: db-creds
    csi:
      driver: secrets-store.csi.k8s.io
      readOnly: true
      volumeAttributes: { secretProviderClass: "db-creds" }
```

Secret mounted at a file path; no K8s Secret object in etcd at all. Optional `syncSecret: true` mode also creates a K8s Secret for compatibility.

ESO vs CSI Driver: ESO produces native K8s Secrets (more compatible, env-var works); CSI Driver doesn't (no etcd exposure, but env-var injection requires a small bootstrap).

For regulated finance: **ESO is the typical default** because most apps need env vars, and the K8s Secret is encrypted-at-rest in etcd via KMS. CSI Driver is for apps that can read from files (the cleaner pattern).

---

## 5. Vault on K8s — three integration patterns

### 5.1 Vault Agent Injector

A mutating webhook that injects a `vault-agent` sidecar into pods (based on annotations). The sidecar authenticates to Vault using the pod's SA token, fetches secrets, writes them as files into a shared volume.

```yaml
metadata:
  annotations:
    vault.hashicorp.com/agent-inject: "true"
    vault.hashicorp.com/agent-inject-secret-db: "database/creds/myapp-role"
    vault.hashicorp.com/role: "myapp"
```

### 5.2 Vault Secrets Store CSI Provider

Same CSI pattern as above, with Vault as the backend.

### 5.3 External Secrets Operator with Vault backend

ESO talks to Vault. Same UX as AWS/GCP/Azure.

For new shops standardizing on Vault: ESO is the unified pattern. For shops with existing Vault Agent investment: keep it.

---

## 6. SPIFFE/SPIRE — workload identity for the heterogeneous world

Beyond cloud-IAM federation, **SPIFFE** is a standard for cross-cluster workload identity. **SPIRE** is the reference implementation. A workload running in any environment can prove its identity (a SPIFFE ID like `spiffe://example.org/ns/ml-serving/sa/infer-server`) and get a short-lived X.509 SVID.

Use SPIFFE/SPIRE when:
- Multi-cluster / multi-cloud / hybrid identity federation.
- Service mesh (Istio uses SPIRE under the hood).
- Workload-to-workload mTLS without a service mesh.

For most K8s shops, cloud-IAM federation (IRSA/WIF/Entra Workload ID) is enough. SPIFFE/SPIRE adopt when you outgrow it.

---

## 7. Secret rotation — the production lever

Rotation strategies:

- **App-driven**: app fetches latest secret on every connection (clean but DB-pool unfriendly).
- **Sidecar-driven**: Vault Agent / Secrets Manager Agent rotates the mounted file; app re-reads (with signal handler `SIGHUP` to reload).
- **Operator-driven**: ESO re-reconciles every `refreshInterval`; updates the K8s Secret; you must restart the pods to pick it up (or use a sidecar reloader).
- **Database-side rotation**: rotate at the DB (cred-rotator Lambda / Cloud Function); app fetches fresh on next connection.

For regulated finance: **all DB credentials are short-lived (1-hour TTL) via Vault dynamic secrets or AWS Secrets Manager rotation**. No static credentials.

---

## 8. Pull-secrets — image pull credentials

A specific Secret type for image-pull auth:

```yaml
apiVersion: v1
kind: Secret
metadata: { name: ghcr-pull }
type: kubernetes.io/dockerconfigjson
data:
  .dockerconfigjson: <base64-of-docker-config>
```

Reference via `imagePullSecrets` on the pod or ServiceAccount. Module 05 covers cloud-registry alternatives (node IAM, IRSA-based ECR auth) which eliminate the need.

---

## 9. TLS Secrets

```yaml
apiVersion: v1
kind: Secret
metadata: { name: api-tls }
type: kubernetes.io/tls
data:
  tls.crt: ...
  tls.key: ...
```

Used by Ingress, Gateway, services that need server certs. Generate via **cert-manager** which:
- Watches Ingress/Gateway resources.
- Requests certs from Let's Encrypt (ACME) / AWS ACM / GCP Cert Manager / Vault PKI.
- Renews automatically.

cert-manager is the standard K8s cert lifecycle solution. Module 32 (service mesh) builds on it.

---

## 10. Auditing secret access

The K8s **audit log** records every API call. Filter for Secret access:

```yaml
# audit-policy.yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  - level: Metadata
    resources:
      - group: ""
        resources: ["secrets"]
```

Set on the kube-apiserver via `--audit-policy-file`. Logs go to file or webhook (typically forwarded to your SIEM).

For "who read which secret when" — this is the audit primitive.

---

## Sanity check

1. K8s Secrets are base64. Why is base64 not encryption?
2. What does etcd encryption-at-rest protect against, and what does it NOT protect against?
3. Sealed Secrets vs External Secrets Operator — which is better for multi-cluster GitOps and why?
4. The Secrets Store CSI Driver bypasses etcd entirely. What's the trade-off vs ESO?
5. Name three short-lived-credential patterns that eliminate static DB passwords.
6. Why is `defaultMode: 0400` on a mounted Secret a defensive control?

---

## Sources

- [K8s Secret docs](https://kubernetes.io/docs/concepts/configuration/secret/)
- [Encrypting Confidential Data at Rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/)
- [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets)
- [External Secrets Operator](https://external-secrets.io/)
- [Secrets Store CSI Driver](https://secrets-store-csi-driver.sigs.k8s.io/)
- [HashiCorp Vault on K8s](https://developer.hashicorp.com/vault/docs/platform/k8s)
- [SOPS](https://github.com/getsops/sops)
- [SPIFFE/SPIRE](https://spiffe.io/)
- [cert-manager](https://cert-manager.io/)

→ Next: [21 — RBAC & ServiceAccounts](21_rbac_serviceaccounts.md)
