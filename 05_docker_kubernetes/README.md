# Topic 05 — Docker & Kubernetes for AI/ML Engineers (Multi-cloud security & data exposure lens)

> **Audience:** Senior AI/ML Engineer (currently Optum, Azure shop) preparing for **Sr Lead AI/ML Engineer at Capital One** (AWS-native, regulated finance, explicitly mentions **EKS + KServe** in their MLE job postings). Already fluent in Python, PySpark, Azure Databricks, and now AWS (Topic 04). Needs Docker/Kubernetes depth from first principles, with relentless focus on **how to expose data to and from containers safely** across **on-prem, AWS, GCP, and Azure**.
>
> **Goal:** A teaching corpus where every module is research-backed and where the unifying thread is *data exposure* — how does the workload see secrets, configs, training data, model artifacts, and outbound network destinations, and how is each of those surfaces secured on each cloud?
>
> **Branch:** `topic-05-docker-kubernetes`
>
> **Last updated:** 2026-05-21

---

## Promise

Same standard as Topic 04. Every module is backed by a research pass *before* the module is written. Citable facts go to [`FACTS.md`](FACTS.md) with "last verified" dates. Time-sensitive content (CVE numbers, GA dates, cert exam costs, CSI driver versions) is re-verified at write-time. Primary-source documents (CIS benchmarks, NIST SP 800-190, kernel docs, cloud-provider whitepapers, CNCF project docs) are archived under [`../../research_inputs/05_docker_kubernetes/downloads/`](../../research_inputs/05_docker_kubernetes/downloads/).

The **explicit user ask** for this topic is:

> *"Cover all possible scenarios on how people use and expose data within docker containers safely and securely. Cover this for on-premise, AWS, GCP, Azure."*

That ask drives the module structure — Parts D and F below carry the cloud-specific data-exposure deep dives, and **every** Docker/K8s primitive module includes a "data-exposure implications" section.

## Learning path

| # | Module | Why it matters |
|---|--------|----------------|
| **Part A — Container fundamentals (1–5)** | | |
| 1 | [Linux primitives: namespaces, cgroups, capabilities, seccomp, LSMs](01_linux_primitives.md) | Containers are not VMs — they're Linux kernel features. Understand the substrate before the runtime. |
| 2 | [Docker architecture & runtime: dockerd → containerd → runc → OCI](02_docker_architecture.md) | Why `docker.sock` is dangerous, where the trust boundary actually sits, what containerd actually does |
| 3 | [Dockerfile & image layers — building production images](03_dockerfile_images.md) | Multi-stage, distroless/Chainguard, layer caching, `.dockerignore`, image size discipline |
| 4 | [Image security: scanning, SBOM, signing, supply chain](04_image_security.md) | Trivy/Grype/Snyk, syft/SBOM, Cosign/Sigstore, SLSA attestations, vulnerability gating |
| 5 | [Container registries: ECR, GAR, ACR, Harbor, JFrog](05_registries.md) | Auth flows per cloud, replication, immutability, retention, vulnerability scanning at push |
| **Part B — Docker networking & storage (6–9)** | | |
| 6 | [Docker networking — bridge, host, overlay, macvlan, port publishing](06_docker_networking.md) | What `-p` actually does (NAT + iptables), localhost-only binding, network namespaces, DNS resolution |
| 7 | [Docker storage — bind mounts, volumes, tmpfs, volume drivers](07_docker_storage.md) | The volume taxonomy, anti-patterns (host root mount, docker.sock mount), encrypted volumes |
| 8 | [Secrets in Docker — BuildKit secrets, Swarm secrets, runtime patterns](08_docker_secrets.md) | Why `ENV`/`ARG` for secrets is a CVE waiting to happen, BuildKit `--mount=type=secret`, runtime mounted-file pattern |
| 9 | [Docker Compose & local development](09_docker_compose.md) | Compose v2 (no more docker-compose), profiles, secrets in Compose, healthchecks, devcontainers |
| **Part C — Container security & hardening (10–11)** | | |
| 10 | [Container hardening checklist — rootless, no-new-privs, read-only FS, capability dropping](10_hardening_checklist.md) | The 20-point checklist that turns "ships your laptop" into "passes a regulated audit" |
| 11 | [CIS Docker Benchmark + docker-bench-security; common CVEs (runc, Leaky Vessels)](11_cis_cves.md) | What auditors look for; CVE-2019-5736, CVE-2024-21626, the 2018 Tesla cryptojack, Capital One 2019 IMDS pivot |
| **Part D — Exposing data IN/OUT of containers, per cloud (12–15)** | | |
| 12 | [**Data exposure — on-premise**](12_data_exposure_onprem.md) | NFS, CIFS/SMB, iSCSI, Ceph, GlusterFS, MinIO, Longhorn, Portworx, LUKS, restic/Velero backup, air-gapped registry |
| 13 | [**Data exposure — AWS (ECS + EC2 + ECR)**](13_data_exposure_aws.md) | ECS task IAM role, EFS-on-ECS, FSx-on-ECS, Mountpoint-S3 vs s3fs, IMDSv2 enforcement, VPC endpoints |
| 14 | [**Data exposure — GCP (Compute Engine + Cloud Run + GAR)**](14_data_exposure_gcp.md) | Workload Identity Federation, GCS Fuse, Filestore, SA-JSON anti-pattern, GAR auth, Cloud Run revisions |
| 15 | [**Data exposure — Azure (VMs + ACI + ACR)**](15_data_exposure_azure.md) | Managed Identity, Azure Files SMB/NFS, Azure Disks, blobfuse2, ACR token auth, ACI confidential containers |
| **Part E — Kubernetes fundamentals (16–20)** | | |
| 16 | [K8s architecture — control plane, kubelet, kube-proxy, etcd, scheduler, CRDs](16_k8s_architecture.md) | The 30-minute version that makes everything else click |
| 17 | [Workload objects — Pod, Deployment, StatefulSet, DaemonSet, Job, CronJob](17_workload_objects.md) | When to pick which; stateful pitfalls; Job parallelism for ML batch |
| 18 | [Services & networking — ClusterIP/NodePort/LB, Ingress, Gateway API, NetworkPolicy, CNI choices](18_k8s_networking.md) | Service mesh-lite via NetworkPolicy; Calico vs Cilium vs cloud-native CNIs |
| 19 | [Storage in K8s — PV, PVC, StorageClass, CSI, ephemeral volumes, projected volumes](19_k8s_storage.md) | The CSI mental model; RWX vs RWO; ephemeral patterns for ML training |
| 20 | [ConfigMaps & Secrets — etcd encryption-at-rest, sealed-secrets, external-secrets, KMS providers](20_configmap_secrets.md) | Why base64 is not encryption; how production secret backends actually plug in |
| **Part F — Kubernetes security (21–25)** | | |
| 21 | [RBAC & ServiceAccounts — roles, cluster-roles, audit, least-privilege](21_rbac_serviceaccounts.md) | The 90% of "how did this get hacked" cases trace to a too-broad ServiceAccount |
| 22 | [Pod Security — PSA (privileged/baseline/restricted), SecurityContext, runtime classes (gVisor, Kata)](22_pod_security.md) | The replacement for PSP; runtime sandboxing for multi-tenant or untrusted workloads |
| 23 | [Admission control — OPA Gatekeeper, Kyverno, validating/mutating webhooks](23_admission_control.md) | How regulated-finance shops actually enforce policy (Cloud Custodian is AWS-API; Gatekeeper/Kyverno is K8s-API) |
| 24 | [Supply chain on K8s — image signing, admission with Cosign, SBOM, BinAuth](24_k8s_supply_chain.md) | Verify what's running came from your CI, not a typosquatted lookalike |
| 25 | [Observability & runtime security — Prom/Grafana, OTel, Falco, Tracee, Cilium Hubble](25_observability_runtime.md) | DCGM for GPU; Falco for syscalls; Hubble for eBPF flow logs |
| **Part G — Exposing data in K8s, per cloud (26–29)** | | |
| 26 | [**EKS deep — IRSA, EKS Pod Identity, EFS/FSx/EBS CSI, Mountpoint-S3, ASCP, KMS, VPC CNI**](26_eks_data_exposure.md) | The Capital One stack: IRSA → S3/EFS → KMS envelope; IMDSv2-only |
| 27 | [**GKE deep — Workload Identity Federation, GCS Fuse CSI, Filestore CSI, Secret Manager CSI, BinAuth, Autopilot**](27_gke_data_exposure.md) | KSA→GSA federation; GCS Fuse sidecar; Confidential GKE Nodes |
| 28 | [**AKS deep — Entra Workload ID, Azure Files/Disk/Blob CSI, Key Vault CSI, private clusters**](28_aks_data_exposure.md) | The federated identity model; SMB vs NFSv4.1 Files; SecretProviderClass pattern |
| 29 | [**On-prem K8s — Rook-Ceph, Longhorn, OpenEBS, Portworx, Velero, Vault, MetalLB, air-gap**](29_onprem_k8s_data.md) | What "production K8s" looks like when there is no managed cloud beneath you |
| **Part H — AI/ML on Kubernetes (30–32)** | | |
| 30 | [Model serving on K8s — KServe deep, Seldon, BentoML, Triton, vLLM, Ray Serve](30_model_serving_k8s.md) | The KServe InferenceService CRD model that Capital One runs in prod |
| 31 | [Training on K8s — Training Operator, Volcano, NVIDIA GPU Operator, MIG, NCCL, EFA, Karpenter](31_training_k8s.md) | Distributed PyTorch on K8s, GPU autoscaling discipline, MIG vs time-slicing |
| 32 | [Service mesh & zero-trust — Istio (sidecar + ambient), Linkerd, Cilium mesh, SPIFFE/SPIRE](32_service_mesh.md) | Where mTLS comes from; how identity federates across clusters |
| **Part I — Certifications & roadmap (33)** | | |
| 33 | [Certification roadmap — KCNA, KCSA, CKAD, CKA, CKS, plus AWS/GCP/Azure equivalents](33_cert_roadmap.md) | Recommended sequence with buy/skip verdicts for a Sr AI/ML engineer at a regulated-finance shop |

## Companion files

- [`FACTS.md`](FACTS.md) — atomic citable facts (CVE numbers, CSI driver GA dates, exam costs, KMS provider versions)
- [`00_Table_Of_Contents.md`](00_Table_Of_Contents.md) — master index of all modules + companion files + quizzes + code
- [`quizzes/`](quizzes/) — grouped per part
- [`code/`](code/) — Dockerfiles, K8s manifests, Helm fragments, Terraform per cloud, KServe InferenceService examples, Karpenter NodePool examples, Falco rules
- [`../../research_inputs/05_docker_kubernetes/`](../../research_inputs/05_docker_kubernetes/) — deep-research reports + [`downloads/`](../../research_inputs/05_docker_kubernetes/downloads/) archive

## How to use this

1. **Start with module 1** (Linux primitives) even if you've used Docker for years. The 20 minutes here saves hours of confusion later.
2. **Modules 2–11** are Docker proper. If you only have a week, this is the must-read block.
3. **Modules 12–15** are the on-prem/AWS/GCP/Azure data-exposure deep dives that the user explicitly asked for. Read all four even if you only care about one cloud — the comparisons sharpen the mental model.
4. **Modules 16–25** are K8s fundamentals + security. Pair with the CKAD/CKA practice (see module 33).
5. **Modules 26–29** are the cloud-specific K8s deep dives.
6. **Modules 30–32** are the AI/ML-specific K8s patterns. Module 30 (KServe) is the differentiator for the Capital One role.
7. **Module 33** maps everything to certs. The recommended sequence is **KCNA → CKAD → CKS**, with **KCSA** optional.

## Scope notes

- **Cutoff:** content reflects **2025–early 2026** state of the art. CNCF projects move fast; `FACTS.md` carries "Last verified" dates.
- **Bias:** treats container/K8s security with regulated-finance rigor. Anti-patterns and incident lessons sit alongside the official path.
- **Stack convention:** Anthropic Claude on Bedrock for any AI examples (matches Topic 04). Terraform first, Helm second, kubectl last.
- **Networking lens:** assumes Topic 04 networking modules (5–9) are completed first. Cross-references provided.
- **Cert mapping:** every relevant module tagged with the exam domain in module 33.

## Stack baseline (additions to the project `.venv`)

```
docker                 # SDK for Python (also: `pip install docker`)
kubernetes             # official Python client
pykube-ng              # alternative K8s client
kfp                    # Kubeflow Pipelines SDK
kserve                 # KServe Python client
fastapi                # for model-serving containers in code examples
uvicorn
locust                 # for load testing example deployments
ruamel.yaml            # for YAML round-tripping in code examples
checkov                # IaC + Dockerfile lint
hadolint               # via subprocess for examples
```

Tools assumed installed locally (outside .venv):
- `docker` (Docker Desktop or rootless), `containerd`, `kind` or `minikube` for local K8s
- `kubectl`, `helm`, `kustomize`
- `aws`, `gcloud`, `az` CLIs
- `trivy`, `cosign`, `syft`

## Research provenance

This corpus is built from research reports under [`../../research_inputs/05_docker_kubernetes/`](../../research_inputs/05_docker_kubernetes/), plus archived primary-source documents under [`../../research_inputs/05_docker_kubernetes/downloads/`](../../research_inputs/05_docker_kubernetes/downloads/) (NIST SP 800-190, CIS Docker/K8s benchmarks, CNCF whitepapers, cloud-provider docs).
