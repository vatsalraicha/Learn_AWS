# 14 — Data exposure for containers — GCP

> *"Workload Identity Federation replaces every long-lived service-account JSON key in your stack. If you still have JSON keys, you're behind."*

## Why this module exists

GCP's container-data story is the cleanest of the three big clouds because:

1. **Workload Identity Federation** has been the default for K8s for years; no JSON keys.
2. **Service accounts** at the project level are first-class principals.
3. **GCS** is the storage spine; **gcsfuse** is now CSI-driver-grade.
4. **Secret Manager** + Workload Identity is one short hop.

This module covers Docker-on-GCE (Compute Engine), Cloud Run, and the GCP-specific identity model. GKE is in module 27.

---

## 1. Identity — service accounts everywhere

In GCP, a **service account** is an IAM principal with an email like `infer-server@my-proj.iam.gserviceaccount.com`. Roles are bound to it; resources reference it by email; workloads authenticate AS it.

Two ways to authenticate as a service account from a container:

### 1.1 Compute Engine instance default service account (the IMDS pattern)

A GCE VM has an associated service account, exposed via GCE Metadata Server at `http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token`. Any process on the VM — including containers — can fetch tokens.

Inside any container on a GCE host:

```bash
curl -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token
# Returns: {"access_token":"...","expires_in":3599,"token_type":"Bearer"}
```

This is **the GCP equivalent of EC2 IMDS**, and it has the same risk surface. Mitigation:

- **Run with the minimal service account** the workload needs (use `--service-account=...` on `gcloud compute instances create`).
- **GCE metadata blocked from container** via `--metadata-from-file=block-project-ssh-keys=true` + iptables rule on the metadata IP `169.254.169.254`.
- **Prefer Workload Identity Federation** (see below) for per-workload identity.

### 1.2 Workload Identity Federation (WIF) — the modern default

WIF lets a non-GCP workload (or a GCP workload that you want to identity-bound) **trade an OIDC token for a GCP access token via STS**, without any long-lived JSON key.

The setup:

1. Create a **Workload Identity Pool** + Provider that trusts your IdP (GitHub OIDC, AWS, Azure, OIDC of your own).
2. Bind the pool to a GCP service account: "principals from this pool can `iam.serviceAccounts.getAccessToken` on this SA."
3. Workload presents an OIDC token; STS exchanges it for a 1-hour SA access token.

For containers on GCE that should not use the VM's default SA, this is the modern path. For GKE (module 27), Workload Identity *for GKE* is a tighter integration (KSA → GSA without WIF pool).

### 1.3 The JSON-key anti-pattern

```bash
# DO NOT DO THIS
docker run -v ~/.config/gcloud:/root/.config/gcloud myimage          # leaks YOUR identity
docker run -v /etc/gcp-sa.json:/etc/gcp-sa.json -e GOOGLE_APPLICATION_CREDENTIALS=/etc/gcp-sa.json myimage  # static key on disk
```

GCP org policies can **forbid creation of service-account JSON keys** entirely (`iam.disableServiceAccountKeyCreation`). For regulated workloads, this is the right org-policy setting. Replace every JSON key with WIF.

---

## 2. Object storage — Google Cloud Storage (GCS)

### 2.1 Access patterns

| Pattern | Use case | Notes |
|---|---|---|
| **SDK calls (google-cloud-storage)** | App-level reads/writes | The default; cleanest |
| **gcsfuse** | Mount GCS as a filesystem | ML training data; supported by Google |
| **`gsutil`** | CLI scripting | Fine for batch jobs |
| **Cloud Storage Transfer Service** | Bulk loads | One-time migrations |

`gcsfuse` is officially supported and stable. Mount on the host, bind-mount into the container:

```bash
gcsfuse --implicit-dirs my-bucket /mnt/my-bucket
docker run -v /mnt/my-bucket:/data:ro myimage
```

For GKE, the **GCS Fuse CSI driver** (GA late 2023) does this declaratively as a sidecar per pod (module 27).

Caveat: `gcsfuse` is not a real POSIX FS — no random writes, no rename atomicity. For ML training (sequential reads of large files), it's fine. For database storage, never.

### 2.2 GCS IAM

GCS supports both **fine-grained ACLs** (legacy) and **Bucket Policy Only / Uniform Bucket-Level Access** (modern). Always enable Uniform — disables ACLs, simplifies the model to IAM only.

Standard roles:

| Role | What it grants |
|---|---|
| `roles/storage.objectViewer` | Read objects |
| `roles/storage.objectCreator` | Create objects (no read of existing) |
| `roles/storage.objectAdmin` | Read/write/delete objects |
| `roles/storage.admin` | Full admin including bucket settings |

For containers, the principle of least privilege: grant `objectViewer` on the specific bucket (or prefix-conditional with IAM Conditions):

```bash
gcloud storage buckets add-iam-policy-binding gs://my-bucket \
  --member="serviceAccount:infer-server@my-proj.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer" \
  --condition='expression=resource.name.startsWith("projects/_/buckets/my-bucket/objects/models/sentiment/"),title=models-sentiment-only,description="Read only sentiment model"'
```

### 2.3 Encryption

- **Default at rest**: Google-managed keys, AES-256.
- **CMEK** (Customer-Managed Encryption Key): you supply a Cloud KMS key. Bucket-level + project-level options.
- **CSEK** (Customer-Supplied Encryption Key): you supply the raw key on every request. Rare; only for extreme cases where Google never sees the key material.
- **In transit**: TLS always. No setting needed.

For regulated finance, **CMEK with project-specific KMS keys** is the floor. Org policy can require CMEK on all buckets:

```yaml
# Organization Policy
constraint: constraints/gcp.restrictNonCmekServices
listPolicy:
  allowedValues:
    - "storage.googleapis.com"
```

### 2.4 VPC Service Controls (VPC-SC)

The GCP equivalent of "no exfiltration to external buckets" — VPC-SC creates a **service perimeter** that prevents API calls from inside the perimeter to resources outside, and vice versa.

For ML data, put your project (or specific buckets) in a perimeter; containers in the same perimeter can read; nothing outside can. Even if an IAM mistake grants read to a wrong principal, VPC-SC blocks the call if the principal is outside the perimeter.

This is one of GCP's best-loved features for regulated shops — there's no exact equivalent in AWS or Azure (AWS VPC endpoints are conceptually similar but per-service).

### 2.5 Private Google Access

For GCE / Cloud Run / Compute instances in subnets without public IPs, **Private Google Access** lets them reach `storage.googleapis.com`, `secretmanager.googleapis.com`, etc. via private IP. Enable on the subnet:

```bash
gcloud compute networks subnets update my-subnet --region=us-central1 \
  --enable-private-ip-google-access
```

Together with VPC-SC, this is how you keep ML container traffic off the internet entirely.

---

## 3. Filestore — managed NFS

**Filestore** is GCP's managed NFSv3 (and v4.1 for some tiers). Tiers:

- **Basic HDD** — cheap, low IOPS.
- **Basic SSD** — better.
- **Zonal SSD** — high-perf, single-zone.
- **Enterprise** — regional HA, ~100k IOPS.

Mount on a GCE host, bind-mount into container:

```bash
mount -t nfs -o vers=3,rsize=1048576,wsize=1048576 \
  10.0.10.5:/share /mnt/share
docker run -v /mnt/share:/data myimage
```

For GKE: **Filestore CSI driver** (module 27).

Filestore is the right pick for "Linux file share with many concurrent readers" patterns. For ML training at extreme scale, **Cloud Storage with gcsfuse** or **Lustre on Compute Engine** is cheaper.

---

## 4. Persistent Disks (PD) — block storage for containers

Persistent Disks are the GCP block storage primitive. Tiers:

- **pd-standard** — HDD, cheap.
- **pd-balanced** — gp3-equivalent.
- **pd-ssd** — high IOPS.
- **pd-extreme** — provisioned IOPS.
- **Hyperdisk** — newer family with tier-specific extremes (throughput, IOPS, balanced); cleaner separation than `pd-extreme`.

Pattern: attach PD to GCE host, mkfs, mount, bind-mount into container. Single-host writer; for multi-host RWX, use Filestore or GCS.

### 4.1 Disk encryption

- **Google-managed key** by default.
- **CMEK** via Cloud KMS — enforced via org policy.
- **CSEK** for the extreme cases.

For container hosts: enable CMEK on the disks at create time.

---

## 5. Secret Manager

Google Cloud's secret store. Versions, IAM-controlled, KMS-encrypted, optionally CMEK.

```python
from google.cloud import secretmanager
client = secretmanager.SecretManagerServiceClient()
resp = client.access_secret_version(request={"name": "projects/123/secrets/db-pass/versions/latest"})
pw = resp.payload.data.decode("UTF-8")
```

Authentication is automatic via ADC (Application Default Credentials) — the container picks up the GCE metadata token or the WIF token transparently.

### 5.1 Best practices

- IAM roles per secret (`roles/secretmanager.secretAccessor` on a specific secret, not project-wide).
- Use **labels** to tag secrets by team / environment / data class.
- Enable **secret version pinning** in your code (avoid `:latest` in prod — version drift causes silent failures).
- Use **secret rotation** with Cloud Functions to rotate DB passwords periodically.
- **CMEK** for secret encryption.

### 5.2 Mounting secrets as files

A common pattern (and the safer one — module 08):

```python
# At container startup
secret_value = fetch_from_secret_manager("db-pass")
with open("/run/secrets/db_pass", "w") as f:
    f.write(secret_value)
os.chmod("/run/secrets/db_pass", 0o400)
# App reads from /run/secrets/db_pass
```

On GKE, the **Secret Manager CSI driver** does this declaratively (module 27).

---

## 6. Cloud Run — fully managed containers

Cloud Run is GCP's serverless containers product. It runs OCI images via **gVisor (runsc)** on a Google-managed infra; you provide an image, GCP scales it.

### 6.1 Identity for Cloud Run

A Cloud Run service has a service account. The container's processes can use ADC to get credentials. No JSON key, no metadata server fiddling — `gcloud auth application-default` works inside.

```bash
gcloud run deploy infer-server \
  --image=us-central1-docker.pkg.dev/my-proj/repo/infer:1.0.0 \
  --service-account=infer-server@my-proj.iam.gserviceaccount.com \
  --region=us-central1 \
  --vpc-connector=my-vpc-connector \
  --vpc-egress=all-traffic \
  --ingress=internal-and-cloud-load-balancing \
  --no-allow-unauthenticated
```

### 6.2 Data exposure from Cloud Run

Cloud Run containers can't bind-mount host paths (no host). Volume options:

- **Cloud Storage Fuse** (Cloud Run 2nd gen, GA 2024) — mount a GCS bucket as a volume.
- **Cloud SQL** via private IP + Cloud SQL Connector (Python `cloud-sql-python-connector`).
- **In-memory tmpfs** — automatic, container's writable layer is ephemeral.
- **Cloud Storage SDK** — the dominant pattern for data movement.

### 6.3 Cloud Run security defaults

- `--ingress=internal-and-cloud-load-balancing` — not reachable from public internet.
- `--no-allow-unauthenticated` — requires Google-issued JWT for invocation.
- `--vpc-connector` + `--vpc-egress=all-traffic` — egress through your VPC, subject to firewall rules + VPC-SC.
- gVisor runtime — kernel-attack-surface reduction comes free.

Cloud Run is the **simplest container compute on GCP** with the strongest defaults. For workloads that fit (HTTP/gRPC, stateless, ≤ 60 minutes), it's usually the right answer.

---

## 7. Binary Authorization for image verification

[Binary Authorization](https://cloud.google.com/binary-authorization) is GCP's image-attestation admission control — GKE-focused but also supports Cloud Run.

Pattern:

1. Build image in CI; sign with Cosign keyless via WIF.
2. CI generates an attestation (`gcloud container binauthz attestations create`).
3. Cloud Run / GKE deployment policy requires an attestation from the trusted attestor before allowing the image to run.

For regulated finance on GCP: enforce BinAuth on every prod cluster + Cloud Run service. Break-glass via labels with audit trail.

---

## 8. Firewall rules — the container egress

GCP firewall rules apply to VM network tags or service accounts. Containers inherit the VM's network identity (for GCE-Docker) or Cloud Run's egress identity.

Default-deny outbound pattern:

```bash
gcloud compute firewall-rules create deny-all-egress \
  --direction=EGRESS \
  --priority=65530 \
  --network=my-vpc \
  --action=DENY \
  --rules=all \
  --destination-ranges=0.0.0.0/0

gcloud compute firewall-rules create allow-gcp-private \
  --direction=EGRESS \
  --priority=1000 \
  --network=my-vpc \
  --action=ALLOW \
  --rules=tcp:443 \
  --destination-ranges=199.36.153.8/30   # private.googleapis.com
```

Combined with Private Google Access + VPC-SC, the container can talk to Google services only — no internet egress.

---

## 9. Logging — Cloud Logging

The default for containers on GCE / Cloud Run / GKE:

- **GCE-Docker**: install Ops Agent on the host; container stdout/stderr flows to Cloud Logging.
- **Cloud Run**: stdout/stderr → Cloud Logging automatically.
- **GKE**: GKE's logging agent (Fluent Bit) → Cloud Logging.

Logs are encrypted at rest by Google-managed keys by default; CMEK available.

Cloud Logging log buckets can be **regionally constrained** for data-residency requirements — set this at project create time.

---

## 10. The reference architecture for ML on GCP (Docker on GCE)

```
┌────────────────────────────────────────────────────────────────────┐
│ VPC (my-vpc) + VPC-SC perimeter                                    │
│                                                                    │
│  ┌──────────────────┐    ┌──────────────────┐                      │
│  │ GCE host (no     │    │ Cloud Run        │                      │
│  │ public IP)       │    │ infer-server     │                      │
│  │ + Docker         │    │ + per-SA identity│                      │
│  │ + SA (least priv)│    │ + VPC connector  │                      │
│  └──────┬───────────┘    └──────┬───────────┘                      │
│         │ private IP             │ VPC egress                      │
│         │                        │                                 │
│  ┌──────▼────────────────────────▼────────────────────────────┐    │
│  │ Private Google Access subnet                              │    │
│  └──────┬────────────────────────────────────────────────────┘    │
│         │ private.googleapis.com (199.36.153.8/30)                 │
└─────────┼──────────────────────────────────────────────────────────┘
          │
   ┌──────▼──────┐    ┌──────────────┐   ┌──────────────┐
   │ GCS buckets │    │ Filestore    │   │ Secret Mgr   │
   │ + CMEK      │    │ + CMEK       │   │ + CMEK       │
   │ + Uniform   │    │              │   │              │
   │   ACL       │    │              │   │              │
   └─────────────┘    └──────────────┘   └──────────────┘
```

Cross-cuts:

- **Image source**: Artifact Registry (GAR), signed with Cosign.
- **Identity**: per-workload service account (no JSON keys); WIF for off-GCP CI.
- **Egress**: VPC firewall default-deny; Private Google Access; VPC-SC perimeter.
- **Audit**: Cloud Audit Logs to centralized log sink.

---

## 11. Capital One angle for GCP

Capital One is AWS-first and AWS-only, so GCP isn't strictly in scope for the Sr Lead AI/ML role. But knowing the parallels is interview gold — "I would map this AWS X to GCP Y" is the kind of architect-level thinking that scores points.

| AWS | GCP |
|---|---|
| IAM Role + STS | Service Account + STS |
| IMDSv2 hop-limit=1 | GCE Metadata Server (block via FW) |
| IRSA / Pod Identity (EKS) | Workload Identity for GKE |
| Cross-account assume-role | Workload Identity Federation |
| S3 + SSE-KMS | GCS + CMEK |
| EFS | Filestore |
| FSx for Lustre | Lustre on GCE (3rd-party) / Parallelstore |
| Secrets Manager | Secret Manager |
| KMS | Cloud KMS |
| Cloud Custodian (AWS-API) | Organization Policy + Forseti (legacy) |
| VPC Endpoints | Private Google Access + VPC-SC |
| Service Control Policies | Org Policies + IAM Conditions |
| ECR | Artifact Registry |
| ECS Fargate (Firecracker per task) | Cloud Run (gVisor per request batch) |

---

## Sanity check

1. Why is Workload Identity Federation preferable to a service-account JSON key, even when the JSON key is "only in the build pipeline"?
2. What does VPC Service Controls give you that VPC firewall rules don't?
3. `gcsfuse` is fine for ML training but unsuitable for a Postgres data dir. Why?
4. Cloud Run uses gVisor by default. What attack class does that close that vanilla Docker on GCE doesn't?
5. Name three controls a regulated shop should enforce on every GCS bucket via Organization Policy.
6. How does "Private Google Access" interact with a subnet that has no public IPs?

---

## Sources

- [Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation)
- [GCS overview](https://cloud.google.com/storage/docs)
- [Cloud Storage Fuse](https://cloud.google.com/storage/docs/cloud-storage-fuse/overview)
- [Filestore](https://cloud.google.com/filestore/docs)
- [Persistent Disks](https://cloud.google.com/compute/docs/disks)
- [Secret Manager](https://cloud.google.com/secret-manager/docs)
- [Cloud Run](https://cloud.google.com/run/docs)
- [Binary Authorization](https://cloud.google.com/binary-authorization/docs)
- [VPC Service Controls](https://cloud.google.com/vpc-service-controls/docs)
- [Private Google Access](https://cloud.google.com/vpc/docs/private-google-access)

→ Next: [15 — **Data exposure — Azure**](15_data_exposure_azure.md)
