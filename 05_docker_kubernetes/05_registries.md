# 05 — Container registries: ECR, GAR, ACR, Harbor, JFrog

> *"Your registry is your single point of distribution. Treat it like production."*

## Why this module exists

The registry is the choke point between "code that built" and "container that runs." It's where signing/SBOM/scanning evidence lives, where pull credentials are validated, and where regulated audit trails are anchored. This module covers the four cloud registries you'll actually use (ECR, GAR, ACR, GHCR) plus the two heavyweight self-hosted options (Harbor, JFrog Artifactory). For each: auth mechanism, geo-replication, immutability/retention, scanning hooks, and the per-cloud IAM gotchas.

---

## 1. Amazon ECR (Elastic Container Registry)

ECR is the AWS-native registry. Two flavors:

- **ECR Private** — per-region, IAM-authenticated, the default.
- **ECR Public** (`public.ecr.aws/...`) — global CDN-fronted, anonymous read; used to publish public base images (think `public.ecr.aws/lambda/python:3.12`).

### 1.1 Auth model

Pull/push is **AWS IAM only**. The CLI flow:

```bash
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
```

The token is **a 12-hour bearer token**, not a long-lived password. The Docker credential helper (`amazon-ecr-credential-helper`) refreshes it transparently — install it on developer laptops to avoid re-running `get-login-password` every shift.

For K8s on EKS, pulling works **automatically** when the node IAM role has `AmazonEC2ContainerRegistryReadOnly`. No `imagePullSecrets` needed. For cross-account pulls, configure ECR repository policy to allow the puller account, or use **ECR pull-through cache** (see below).

### 1.2 ECR features

| Feature | Notes |
|---|---|
| **Image scanning — Basic** | Free; scans on push; OS packages only |
| **Image scanning — Enhanced** | Paid (via Inspector); continuous + OS + language libs + KEV alerts |
| **Cross-region replication** | Configure per-repo; latency to replica is asynchronous |
| **Cross-account replication** | Same mechanism + destination account permission |
| **Pull-through cache** | Proxy through to upstream registry (Docker Hub, Quay, GCR, GHCR); caches in your ECR. Cuts Docker Hub rate limit risk. |
| **Image tag mutability** | `MUTABLE` (default) or `IMMUTABLE` — set IMMUTABLE for prod repos |
| **Lifecycle policies** | JSON rules: "expire images older than 30 days," "keep last 10 of tag prefix `v`" |
| **Repository encryption** | AES-256 default; CMK option for compliance |
| **VPC interface endpoint** | `com.amazonaws.<region>.ecr.api` + `.ecr.dkr` + `.s3` (the layers live in S3) |
| **Signing** | AWS Signer integration; also supports Cosign via the standard OCI referrers API |

### 1.3 The "ECR + S3" gotcha

Image layers are stored in **a regional S3 bucket managed by ECR**. For a private VPC endpoint to fully work, you need three endpoints: `ecr.api`, `ecr.dkr`, **and `s3`**. Skip the S3 endpoint and pulls will silently fall back to the public internet — a common audit finding.

### 1.4 ECR for Capital One–style regulated shops

- IMMUTABLE tags on prod repos.
- CMK encryption.
- VPC interface endpoints (all three).
- Lifecycle policy: expire `dev-*` and `pr-*` tags after 14 days.
- Replication to DR region.
- Enhanced scanning + Inspector findings → Security Hub.
- Cloud Custodian policy: `no-public-ecr-repos`, `ecr-without-lifecycle-policy`, `ecr-without-cmk`.

---

## 2. Google Artifact Registry (GAR)

**GAR** replaces the older **GCR** (Google Container Registry). All new projects should use GAR; GCR is deprecated and migrating to GAR for new pushes by default since 2024.

### 2.1 Differences vs GCR

- Multi-format: containers, Maven, npm, Python, apt, yum — not just OCI.
- Per-region, multi-region, or virtual repositories.
- VPC Service Controls compatible (GCR was not).
- IAM via Artifact Registry roles (`roles/artifactregistry.reader`, `roles/artifactregistry.writer`).
- Cost model is per-GB-stored + egress; GCR was free-storage.

### 2.2 Auth model

Auth flows:

- **Workload Identity Federation** (preferred for CI and workloads): no JSON keys. The workload trades an OIDC token for a GCP access token via STS.
- **gcloud SDK ADC** for developer laptops:
  ```bash
  gcloud auth configure-docker us-central1-docker.pkg.dev
  ```
  Sets the Docker credential helper to call gcloud.
- **Service account JSON keys** — explicitly discouraged by GCP since 2024; org policy can ban creation entirely.

For GKE, **Workload Identity Federation** on the pod's KSA binds to a GSA with the reader role on the repo. No `imagePullSecrets` needed when the GKE node service account has reader (the lazy/insecure pattern); for least-privilege, configure per-namespace pull credentials via WIF.

### 2.3 GAR features

| Feature | Notes |
|---|---|
| **Container Analysis API** | Vulnerability scanning, supports SBOM upload |
| **Binary Authorization integration** | First-class; attestations are stored as Grafeas notes |
| **CMEK** | Yes |
| **Virtual repositories** | Aggregate multiple upstreams behind one endpoint (useful for "Docker Hub via our proxy") |
| **Remote repositories** | Pull-through caching for Docker Hub, Quay, etc. |
| **Cleanup policies** | Per-repo TTL rules |
| **Region selection** | Single-region (cheap), multi-region (resilient), specific multi-region (US, EU, ASIA) |

---

## 3. Azure Container Registry (ACR)

### 3.1 Tiers

| Tier | Storage included | Geo-replication | Use case |
|---|---|---|---|
| **Basic** | 10 GB | No | Dev/test only |
| **Standard** | 100 GB | No | Default for most apps |
| **Premium** | 500 GB | **Yes** | Production, multi-region, regulated workloads |

Geo-replication, image signing, customer-managed keys, private endpoints, and content trust **require Premium**. For Capital One–style postures, you must run Premium.

### 3.2 Auth model

- **Microsoft Entra ID** (RBAC) — preferred. Roles: `AcrPull`, `AcrPush`, `AcrDelete`.
- **Admin user** — a username/password pair with full push/pull; **disable in production**.
- **Repository-scoped tokens** — narrower than the admin user; rotate them.
- **Managed Identity** (for AKS / VMs / ACI) — the production path. Assign `AcrPull` to the kubelet identity or pod-level managed identity.

For AKS, `az aks update --attach-acr <name>` is the one-liner that grants the kubelet's managed identity `AcrPull` on the registry. After that, image pulls "just work" — no `imagePullSecrets`.

### 3.3 ACR features

| Feature | Notes |
|---|---|
| **ACR Tasks** | Built-in image build/test/deploy automation (alternative to GitHub Actions / Azure DevOps) |
| **Content trust** | Docker Notary v1 (legacy). Use Cosign instead for new signing. |
| **Microsoft Defender for Cloud** | Vulnerability scanning (paid). Free baseline available. |
| **Quarantine pattern** | Push to a quarantined tag, scan, then promote |
| **Private endpoint** | Premium only |
| **Geo-replication** | Premium; per-region replicas |
| **Repository delete protection** | Lock policy + tag immutability |

---

## 4. GitHub Container Registry (GHCR)

`ghcr.io` is the GitHub-native registry. Tightly coupled to GitHub Actions: a push from a workflow auto-authenticates with `GITHUB_TOKEN`.

| Feature | Notes |
|---|---|
| **Auth** | PATs, `GITHUB_TOKEN` in Actions, OIDC tokens for Cosign keyless |
| **Visibility** | Public or private; private requires paid GitHub Org plan |
| **Scanning** | Dependabot for the source repo; no native image scanner |
| **SBOM/attestation storage** | Native via OCI referrers API |
| **Pricing** | Free unlimited storage for public; per-GB for private |
| **Geo-replication** | None (GitHub-managed regional) |

For a small org or a project that lives on GitHub, GHCR is the lowest-friction registry. For regulated finance, the lack of geo-replication and the GitHub-cloud dependency push you toward ECR/GAR/ACR.

---

## 5. Harbor — the OSS self-hosted standard

[**Harbor**](https://goharbor.io) is a **CNCF Graduated** OCI registry, originally from VMware/Project Pacific. The de facto choice when you need an on-prem or air-gapped registry.

### 5.1 Capabilities

- OCI registry (containers + Helm charts + OPA bundles + WASM via OCI artifact)
- RBAC with projects and roles
- Vulnerability scanning via Trivy (built-in)
- Image signing verification (Cosign)
- Image immutability and retention policies
- Replication to/from other registries (DockerHub, Harbor, ECR, GAR, ACR, GHCR, Quay)
- Proxy cache (pull-through)
- LDAP/AD, OIDC integration
- Audit logs to syslog or kafka

### 5.2 Deployment

Helm chart, runs on K8s. Backed by Postgres for metadata, Redis for cache, and S3-compatible (or filesystem) for blobs. Production deploys typically use **MinIO** or **Ceph S3** for the blob backend so the registry itself can be HA across AZs.

### 5.3 Why a regulated shop runs Harbor in addition to cloud registries

- Air-gapped environments require a self-hosted registry.
- Cross-cloud workloads pull from one canonical source.
- Strict policy enforcement (signed + scanned + retention) under your control.
- Replication: production-blessed images sync from Harbor to ECR/GAR/ACR in each region.

---

## 6. JFrog Artifactory

Commercial, omnivorous (any artifact type, including OCI). Two SKUs: **Artifactory Pro** (self-hosted) and **Artifactory Cloud** (SaaS).

- Manages OCI + Maven + npm + PyPI + Helm + Conan + Cargo + Debian + RPM + ... 30+ formats.
- Strong replication and cross-region HA.
- Tight integration with JFrog **Xray** (scanning) and **Distribution** (CDN).
- Common at enterprises that already standardized on JFrog for Maven/Python before containers — the "we already pay them" pattern.

For new shops without an existing Artifactory footprint, **Harbor + the cloud-native registry per cloud** is the lower-cost path. JFrog wins when the org has 10+ artifact types to manage.

---

## 7. Other registries you'll meet

| Registry | Who runs it | When you'll see it |
|---|---|---|
| **Docker Hub** | Docker Inc. | Default pull source; the rate-limit problem |
| **Quay.io** | Red Hat | OpenShift shops; Project Quay (OSS) for self-hosted |
| **nvcr.io** | NVIDIA | NGC catalog — PyTorch/TensorFlow/Triton optimized images |
| **registry.k8s.io** | Kubernetes | Official K8s system images (kube-apiserver, kube-proxy, etc.) |
| **mcr.microsoft.com** | Microsoft | .NET / SQL Server / Azure agent images |
| **public.ecr.aws** | AWS | Public ECR (e.g., AWS Lambda runtimes) |

### Docker Hub rate limits

Anonymous pulls: **100 per 6h per IP**. Authenticated free: **200/6h**. Paid: unlimited. This is the #1 cause of CI failures with cryptic "toomanyrequests" errors in 2020-2024. Mitigations:
- ECR/GAR/ACR pull-through cache for Docker Hub.
- Replicate hot base images to your own registry.
- Use Chainguard / Distroless images (different registries).

---

## 8. Pull credentials in Kubernetes

Three patterns:

### 8.1 Node-IAM pulls (the lazy default)

Pods inherit the node's cloud credentials. Works for EKS+ECR, GKE+GAR, AKS+ACR when the cluster is configured per the previous sections. **Pro**: no per-pod secret management. **Con**: all pods on the node can pull from the same set of repos.

### 8.2 `imagePullSecrets` (the granular fallback)

For pulling from registries the node doesn't have credentials for (Docker Hub, third-party, cross-account ECR):

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: dockerhub-creds
  namespace: ml-serving
type: kubernetes.io/dockerconfigjson
data:
  .dockerconfigjson: <base64-encoded-docker-config>
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ml-server
  namespace: ml-serving
imagePullSecrets:
  - name: dockerhub-creds
```

Then pods using `serviceAccountName: ml-server` get the pull secret automatically.

### 8.3 IRSA / Workload Identity for cross-account pulls (the right way)

For cross-account ECR pulls without long-lived secrets, use IRSA: the pod's SA assumes a role in the target ECR account; the kubelet uses **EKS Pod Identity** (or IRSA) to broker the ECR auth token. Module 26 covers this in depth.

---

## 9. The registry mirror pattern for ML images

ML images often pull from **Docker Hub** (the default for `python:3.12`, `pytorch/pytorch:...`) and **nvcr.io** (NGC PyTorch/Triton). Both can become availability liabilities in regulated environments — what happens to your CI if Docker Hub has an outage?

Mirror pattern:

1. Run **Harbor** (or use ECR/GAR/ACR pull-through cache) in-cluster.
2. Cache `python`, `nvidia/cuda`, `nvcr.io/nvidia/pytorch` on first pull.
3. CI configured to pull through Harbor only — no direct Docker Hub / NGC pulls.
4. Replicate Harbor across regions for DR.

Cost: storage for cached images. Benefit: independent of upstream availability, full audit trail, no rate-limit surprises.

---

## 10. Capital One signal

Capital One is AWS-native, so the default is **ECR with Enhanced scanning, IMMUTABLE prod tags, CMK encryption, VPC endpoints**, replicated cross-region, with **Cloud Custodian policies** enforcing no-public-repos and no-non-CMK. K8s-level admission verifies signatures (Kyverno or Sigstore policy-controller).

For multi-tenant ML images, the pattern likely involves Harbor (or JFrog) as the canonical internal mirror, with ECR per region as the K8s-facing endpoint.

---

## Sanity check

1. Why does ECR require an S3 VPC endpoint in addition to the ECR endpoints?
2. What's the difference between ECR Image Scanning Basic and Enhanced, and what does Enhanced add that Basic doesn't?
3. What does `az aks update --attach-acr <name>` actually do under the hood?
4. Why is "Workload Identity Federation" preferred over service-account JSON keys for pulling from GAR?
5. What's the practical reason to use Harbor in front of cloud registries?
6. Docker Hub rate limit: what is it, and what are two mitigations?

---

## Sources

- [AWS ECR docs](https://docs.aws.amazon.com/AmazonECR/)
- [GCP Artifact Registry docs](https://cloud.google.com/artifact-registry/docs)
- [Azure Container Registry docs](https://learn.microsoft.com/azure/container-registry/)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Harbor](https://goharbor.io/docs/)
- [JFrog Artifactory](https://jfrog.com/artifactory/)
- [Docker Hub rate limits](https://docs.docker.com/docker-hub/download-rate-limit/)
- [NGC Container Catalog](https://catalog.ngc.nvidia.com/)
- [`amazon-ecr-credential-helper`](https://github.com/awslabs/amazon-ecr-credential-helper)

→ Next: [06 — Docker networking — bridge, host, overlay, macvlan, port publishing](06_docker_networking.md)
