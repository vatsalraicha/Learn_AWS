# Quiz — Part D + G: Data exposure (modules 12-15 + 26-29)

The user's explicit ask material. Master these.

---

## Section 1 — On-premise (module 12)

1. `sec=sys` on NFS is convenient and dangerous. What does it actually trust?
2. `nconnect=8` on NFS — what does it improve for ML training and why?
3. iSCSI is RWO only (not RWX). Why?
4. MinIO SSE-S3 vs SSE-KMS — which does compliance demand and why?
5. Vault Transit engine vs KV engine — what's the architectural difference?
6. List three on-prem CSI drivers and their target use case.
7. Air-gapped K8s + Cosign keyless signing — what's the problem and the two workarounds?

## Section 2 — AWS (module 13)

8. What does `http_put_response_hop_limit=1` on an EC2 instance do to a container's IMDS access?
9. ECS task role vs execution role — what does each cover?
10. Mountpoint for S3 vs s3fs — name two reasons Mountpoint is safer.
11. EFS Access Point gives you what beyond a vanilla EFS mount?
12. The Capital One 2019 breach pattern reduces to one IaC fix. What is it?
13. Why is `Deny aws:SecureTransport=false` in a bucket policy a defense in depth?
14. Name 6 VPC endpoints a typical containerized ECS task needs.

## Section 3 — GCP (module 14)

15. Why is Workload Identity Federation preferred over service-account JSON keys?
16. `gcsfuse` is OK for ML training but not for Postgres data dirs. Why?
17. Cloud Run uses gVisor by default. What does that close?
18. VPC Service Controls — what does it give over VPC firewall rules?
19. Three GCS bucket controls a regulated shop should enforce via Org Policy.

## Section 4 — Azure (module 15)

20. Why is `allowSharedKeyAccess: false` the most security-impactful Azure Storage account setting?
21. `DefaultAzureCredential` — what credential chain does it walk?
22. Azure Disk CMK requires what construct (and why isn't it just "use a Key Vault key")?
23. NFS 4.1 over Azure Files doesn't encrypt in transit. Compensation?

## Section 5 — Cross-cloud K8s (modules 26-28)

24. IRSA vs EKS Pod Identity — two reasons to pick Pod Identity for a new cluster.
25. Workload Identity Federation for GKE binds what to what?
26. Microsoft Entra Workload ID for AKS uses what credential type?
27. Map: AWS EFS → GCP ?, AWS Secrets Manager → Azure ?, AWS IRSA → Azure ?

## Section 6 — On-prem K8s (module 29)

28. Rook-Ceph vs Longhorn — pick a use case each.
29. Why is Local PV ideal for ML training intermediate state but wrong for application persistence?
30. Without cloud IAM, what's the on-prem "identity broker" pattern?

---

## Answer key (brief)

1. UID claim from the client; the server trusts UIDs the client sends. Anyone with root on the client can claim any UID. Not authentication.
2. Multiple parallel TCP connections per NFS mount → higher aggregate throughput. ML training data reads are network-bandwidth-bound; nconnect scales them linearly up to ~16.
3. Block storage; single-writer FS — no clustering semantics. For RWX use file (NFS) or distributed (Ceph).
4. SSE-KMS. CMK gives audit trail of key use + revocability + key policy control. SSE-S3 (server-managed) has none of these.
5. Transit: encryption-as-a-service; keys never leave Vault; apps send plaintext for encrypt/decrypt. KV: stores secret values. Different abstractions.
6. Rook-Ceph (heavy distributed file/block/object); Longhorn (block per-node replicated); OpenEBS Mayastor (NVMe-fabrics performance).
7. Rekor is public; air-gapped breaks reachability. Workarounds: (a) mirror Rekor internally; (b) use keyed signing with internal KMS, skip Rekor.
8. The PUT response token has TTL=1; container's request packet crosses the veth (TTL decrements); token never reaches the container. Effectively blocks IMDS from any container.
9. **Execution role**: ECS-agent operations (image pull, log push, secret fetch for task def). **Task role**: app-level AWS API calls (read S3, call DynamoDB).
10. Mountpoint is AWS-supplied, no CAP_SYS_ADMIN, native CSI integration. s3fs is FUSE-based, needs cap, performance unpredictable.
11. EFS AP enforces a POSIX UID/GID and root directory per mount — multi-tenancy primitive in a single EFS.
12. `metadata_options { http_tokens = "required", http_put_response_hop_limit = 1 }`. IMDSv2 + container can't reach.
13. Even if all clients use HTTPS, mistakes happen. Bucket policy `Deny aws:SecureTransport=false` ensures no HTTP-only client can ever read/write — auditable in policy.
14. S3 (Gateway), ECR API + DKR, KMS, Secrets Manager, CloudWatch Logs, plus app-specific (e.g., Snowflake PrivateLink).
15. WIF eliminates long-lived JSON keys (a frequent credential leak source); short-lived federated tokens via STS; org policy can ban JSON key creation entirely.
16. gcsfuse doesn't support random writes, no rename atomicity, eventual consistency — Postgres data file semantics require all three.
17. The kernel-attack-surface gap. gVisor reimplements syscalls in userspace; a kernel UAF in a syscall hits gVisor's Go code, not the host kernel.
18. VPC-SC creates a service perimeter — API calls from inside to outside are blocked at the API layer (not just network). Catches misconfigured IAM that would grant a wrong principal access.
19. CMEK required; uniform bucket-level access (no ACLs); public access prevention; (also: object versioning + retention + KMS for log buckets).
20. Disables the storage-account-key auth (the "key A and key B" model), forcing all access through AAD. Eliminates a huge class of leaked-key incidents.
21. Env vars → managed identity (IMDS) → CLI cached creds → VS Code → IntelliJ → AzureDeveloperCLI → InteractiveBrowser. Picks first working credential.
22. Disk Encryption Set (DES) — a separate resource pairing a Key Vault key with a disk. Indirection needed because Azure Disks need access to the key without per-disk policy plumbing.
23. Compensate with VNet-private endpoints — the network is the boundary instead of the protocol.
24. Pod Identity: simpler trust policy; no per-cluster OIDC chain; cross-account easier; new AWS SDKs first.
25. KSA (Kubernetes ServiceAccount) → GSA (GCP service account). Annotation on KSA names the GSA; IAM binding on the GSA names the KSA.
26. Federated identity credential on a user-assigned managed identity. The credential trusts the AKS OIDC issuer.
27. AWS EFS → GCP Filestore (file RWX). AWS Secrets Manager → Azure Key Vault. AWS IRSA → Azure Entra Workload ID.
28. Rook-Ceph: heavy file/block/object distributed storage when you have ops staff. Longhorn: simpler K8s-native block storage when you don't.
29. Local PV is bound to a single node; pod-replacement only schedules to that node. For training intermediate state, that's fine (ephemeral). For application persistence, you need data to survive node loss.
30. Vault as broker: K8s SA → Vault K8s auth → Vault returns dynamic creds for downstream systems (DB, MinIO, internal APIs).
