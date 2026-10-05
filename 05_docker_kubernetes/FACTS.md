# Topic 05 — FACTS.md (Docker & Kubernetes)

> Atomic, citable facts. Single source of truth for CVE numbers, CSI driver GA dates, K8s version cutoffs, certification metadata, cloud-specific identity-binding mechanisms.
>
> **Format:** one fact per line, citation in square brackets, last-verified date. If older than 90 days at quote-time, re-verify.
>
> **Last updated:** 2026-05-21 (seed)

---

## Docker / OCI

- **Docker Engine** is now a CLI + REST API on top of **containerd**; `containerd` calls **runc** (the OCI runtime). Other runtimes: `crun` (C), `youki` (Rust), `runsc` (gVisor user-space kernel), `kata-runtime` (VM-isolated). [Source: docs.docker.com architecture; containerd.io] [Verified 2026-05-21]
- **OCI Image Spec v1.1** (Feb 2024) added artifacts and reference types (Sigstore attestations land here). [Source: github.com/opencontainers/image-spec] [Verified 2026-05-21]
- **BuildKit** is the default builder since Docker 23.0 (Feb 2023). `--mount=type=secret` requires BuildKit. [Source: docs.docker.com/build/buildkit] [Verified 2026-05-21]
- **Docker Desktop license**: free for personal, small businesses (<250 employees AND <$10M revenue); paid otherwise. [Source: docker.com/pricing] [Verified 2026-05-21]
- **The `docker` group is root-equivalent** — adding a user to it gives them a path to root via mounting `/`. CIS Docker Benchmark calls this out. [Source: CIS Docker Benchmark v1.6.0] [Verified 2026-05-21]

## Docker security CVEs (must-know)

- **CVE-2019-5736** — runc container escape via overwriting the runc binary; CVSS 8.6. Patched Feb 2019. [Source: nvd.nist.gov] [Verified 2026-05-21]
- **CVE-2022-0185** — Linux kernel filesystem context heap-overflow exploitable from inside containers with CAP_SYS_ADMIN. [Source: nvd.nist.gov] [Verified 2026-05-21]
- **CVE-2024-21626 "Leaky Vessels"** — runc working-dir leak allowing container escape; CVSS 8.6. Patched Jan 2024. [Source: snyk.io/blog/leaky-vessels; runc release notes] [Verified 2026-05-21]
- **CVE-2024-23651, CVE-2024-23652, CVE-2024-23653** — BuildKit Leaky Vessels companions. Patched Jan 2024. [Source: github.com/moby/buildkit advisories] [Verified 2026-05-21]
- **Tesla cryptojacking 2018** — unauthenticated Kubernetes dashboard exposed; cryptominers deployed; root cause: dashboard service exposed without auth. [Source: RedLock CSI report Feb 2018] [Verified 2026-05-21]

## Kubernetes versions & support

- **Kubernetes 1.32** released Dec 2024 ("Penelope"). **1.33** released early 2025. **1.34** GA mid-2025 — confirm at quote time. [Source: kubernetes.io/releases] [Verified 2026-05-21]
- **Support window**: K8s maintains the last 3 minor versions with patches; ~14 months from release. [Source: kubernetes.io/releases/version-skew-policy] [Verified 2026-05-21]
- **etcd KMS v2** GA in K8s 1.29 (Dec 2023); v1 deprecated. [Source: kubernetes.io/docs/tasks/administer-cluster/kms-provider] [Verified 2026-05-21]
- **PodSecurityPolicy (PSP)** removed in K8s 1.25 (Aug 2022). Replaced by **Pod Security Admission (PSA)** namespace labels. [Source: kubernetes.io/blog Aug 2022] [Verified 2026-05-21]
- **Gateway API** v1.0 GA Oct 2023 (ingress successor); v1.1 added GRPCRoute GA, v1.2+ added more. [Source: gateway-api.sigs.k8s.io] [Verified 2026-05-21]
- **dockershim** removed in K8s 1.24 (May 2022); containerd/CRI-O are the runtimes. [Source: kubernetes.io/blog Dec 2020 + 1.24 release] [Verified 2026-05-21]
- **K8s ReadWriteOncePod** access mode GA in 1.29. [Source: kubernetes.io] [Verified 2026-05-21]

## AWS — EKS data exposure primitives

- **IRSA** (IAM Roles for Service Accounts) launched Sep 2019. OIDC-provider based; pod gets `AWS_ROLE_ARN` and `AWS_WEB_IDENTITY_TOKEN_FILE` env vars; SDK calls AssumeRoleWithWebIdentity. [Source: aws.amazon.com/blogs Sep 2019; docs.aws.amazon.com/eks] [Verified 2026-05-21]
- **EKS Pod Identity** GA Nov 2023 (re:Invent). Alternative to IRSA; uses `eks-pod-identity-agent` daemonset, no OIDC chain. Trust policy on the role allows `pods.eks.amazonaws.com`. [Source: aws.amazon.com/blogs Nov 2023] [Verified 2026-05-21]
- **Mountpoint for Amazon S3 CSI driver** GA Apr 2024. Provides PV-backed S3 with limited POSIX (no random writes, no rename in same prefix). [Source: aws.amazon.com/blogs Apr 2024] [Verified 2026-05-21]
- **EFS CSI driver** supports dynamic provisioning via Access Points; encryption-in-transit via TLS (port 2049 with stunnel). [Source: github.com/kubernetes-sigs/aws-efs-csi-driver] [Verified 2026-05-21]
- **AWS Secrets Manager + SSM Parameter Store via the Secrets Store CSI Driver (ASCP)**. [Source: github.com/aws/secrets-store-csi-driver-provider-aws] [Verified 2026-05-21]
- **EKS Auto Mode** GA Dec 2024 (re:Invent 2024). Bundles Karpenter + ALB controller + EBS CSI + EFS CSI + storage class defaults. [Source: aws.amazon.com/eks/auto-mode] [Verified 2026-05-21]
- **VPC CNI**: each pod gets a primary VPC ENI IP; security group per pod is supported on Nitro instances. [Source: github.com/aws/amazon-vpc-cni-k8s] [Verified 2026-05-21]
- **IMDSv2 enforcement** for pods via `httpPutResponseHopLimit=1` at the instance level OR via `eks.amazonaws.com/role-arn` IMDS hop-limit settings. Capital One 2019 root cause was IMDSv1 SSRF. [Source: aws.amazon.com/blogs IMDSv2; OCC consent order] [Verified 2026-05-21]

## GCP — GKE data exposure primitives

- **Workload Identity Federation for GKE** launched 2019; now the default identity binding. KSA annotated with `iam.gke.io/gcp-service-account` maps to a GSA. JSON service-account keys are explicitly discouraged and can be org-policy-blocked. [Source: cloud.google.com/kubernetes-engine/docs/how-to/workload-identity] [Verified 2026-05-21]
- **GCS Fuse CSI driver** GA late 2023; sidecar architecture, runs as a sidecar in each pod. ML training data use case. [Source: cloud.google.com/kubernetes-engine/docs/how-to/persistent-volumes/cloud-storage-fuse-csi-driver] [Verified 2026-05-21]
- **Secret Manager CSI provider** (secrets-store-csi-driver-provider-gcp). [Source: github.com/GoogleCloudPlatform/secrets-store-csi-driver-provider-gcp] [Verified 2026-05-21]
- **Binary Authorization** for GKE — image attestations checked at admission; breakglass via annotation. [Source: cloud.google.com/binary-authorization] [Verified 2026-05-21]
- **GKE Autopilot** GA Feb 2021; node management entirely managed; restricts privileged pods, hostPath, hostNetwork. [Source: cloud.google.com/blog Feb 2021] [Verified 2026-05-21]
- **Confidential GKE Nodes** GA Sep 2020 on AMD SEV; Intel TDX preview/GA expanding. [Source: cloud.google.com/confidential-computing] [Verified 2026-05-21]

## Azure — AKS data exposure primitives

- **Microsoft Entra Workload ID for AKS** GA July 2023; uses federated identity credentials on user-assigned managed identities; OIDC issuer URL per cluster. Replaces deprecated AAD Pod Identity v1. [Source: learn.microsoft.com/azure/aks/workload-identity-overview] [Verified 2026-05-21]
- **Azure Files CSI** supports SMB and NFSv4.1 (Premium tier required for NFS). [Source: learn.microsoft.com/azure/aks/azure-files-csi] [Verified 2026-05-21]
- **Azure Blob CSI** supports blobfuse2 mount mode and NFS 3.0 mount mode. [Source: learn.microsoft.com/azure/aks/azure-blob-csi] [Verified 2026-05-21]
- **Azure Key Vault Provider for Secrets Store CSI Driver**: `SecretProviderClass` CRD; optional `syncSecret` to native K8s Secret. [Source: learn.microsoft.com/azure/aks/csi-secrets-store-driver] [Verified 2026-05-21]
- **Azure CNI Powered by Cilium** (Azure's eBPF dataplane) GA 2023+; Azure CNI Overlay GA. Kubenet deprecation in progress. [Source: learn.microsoft.com/azure/aks/azure-cni-powered-by-cilium] [Verified 2026-05-21]
- **AKS private cluster** — API server has no public IP; access via Private Link, peered VNet, or VPN/ExpressRoute. [Source: learn.microsoft.com/azure/aks/private-clusters] [Verified 2026-05-21]
- **Confidential containers on AKS** preview/GA on AMD SEV-SNP via Kata. [Source: learn.microsoft.com/azure/aks/confidential-containers-overview] [Verified 2026-05-21]

## On-prem K8s storage / projects

- **Rook-Ceph**: CNCF Graduated (Oct 2020). Manages Ceph clusters as K8s resources. [Source: cncf.io project status] [Verified 2026-05-21]
- **Longhorn**: CNCF Incubating; from Rancher Labs. Block-storage CSI for K8s. [Source: longhorn.io] [Verified 2026-05-21]
- **OpenEBS** (Mayastor / cStor / Jiva engines): CNCF Sandbox. [Source: openebs.io] [Verified 2026-05-21]
- **Portworx** (commercial; acquired by Pure Storage 2020). [Source: portworx.com] [Verified 2026-05-21]
- **Velero** for backup/DR: CNCF Sandbox. Originally Heptio. [Source: velero.io] [Verified 2026-05-21]
- **MetalLB** for bare-metal LoadBalancer service type. CNCF Sandbox. [Source: metallb.io] [Verified 2026-05-21]
- **Cilium L2 announcements** as MetalLB alternative — GA in Cilium 1.14 (Aug 2023). [Source: cilium.io] [Verified 2026-05-21]

## AI/ML on K8s

- **KServe** v0.13 added LLM-serving primitives; v0.14 added vLLM-friendly templates. (Confirm latest at quote time.) [Source: kserve.io releases] [Verified 2026-05-21]
- **Karpenter** v1.0 GA Aug 2024 (Kubernetes-native node autoscaler, AWS-originated, now multi-cloud). [Source: karpenter.sh] [Verified 2026-05-21]
- **NVIDIA GPU Operator** version supports MIG (A100/H100/H200), time-slicing, GPU Feature Discovery, DCGM exporter. [Source: docs.nvidia.com/datacenter/cloud-native/gpu-operator] [Verified 2026-05-21]
- **Kubeflow 1.9** released 2024; Kubeflow Training Operator handles PyTorchJob/TFJob/MPIJob. [Source: kubeflow.org] [Verified 2026-05-21]
- **Cilium** v1.14+ ships native service mesh (sidecarless); v1.16 hardened L7 features. [Source: cilium.io blog] [Verified 2026-05-21]

## Certifications — Kubernetes / cloud-native (CNCF / Linux Foundation)

| Cert | Code | Level | Cost USD | Duration | Format | Validity |
|---|---|---|---:|---|---|---|
| Kubernetes & Cloud Native Associate | KCNA | Foundational | $250 | 90 min / 60 MCQ | Online proctored | 2 years |
| Kubernetes & Cloud Native Security Associate | KCSA | Foundational | $250 | 90 min / 60 MCQ | Online proctored | 2 years |
| Prometheus Certified Associate | PCA | Foundational | $250 | 90 min / 60 MCQ | Online proctored | 2 years |
| Istio Certified Associate | ICA | Foundational | $250 | 90 min / 60 MCQ | Online proctored | 2 years |
| Certified Kubernetes Application Developer | CKAD | Associate | $445 | 120 min / hands-on | Online proctored | 2 years |
| Certified Kubernetes Administrator | CKA | Associate | $445 | 120 min / hands-on | Online proctored | 2 years |
| Certified Kubernetes Security Specialist | CKS | Specialty (requires CKA) | $445 | 120 min / hands-on | Online proctored | 2 years |

[Source: training.linuxfoundation.org] [Verified 2026-05-21]

- **Bundle discount**: CKA + CKAD + CKS bundle commonly discounted ~30% during sales (Black Friday, KubeCon). [Source: LF training promos] [Verified 2026-05-21]
- **CKA/CKAD/CKS allow `kubectl` autocomplete + the official kubernetes.io docs during exam** in a sandboxed browser. [Source: training.linuxfoundation.org candidate handbook] [Verified 2026-05-21]
- **CKA curriculum (2025+)**: storage 10%, troubleshooting 30%, workloads & scheduling 15%, cluster architecture 25%, services & networking 20%. [Source: LF CKA curriculum PDF] [Verified 2026-05-21]
- **CKS prerequisites**: must hold an active CKA. [Source: LF CKS page] [Verified 2026-05-21]

## Capital One Kubernetes signal

- Capital One self-hosts model serving on **EKS with KServe** — see job posting R239877: "Lead Machine Learning Engineer (MLOps, KServe — building Kubernetes Clusters, PyTorch, TensorFlow on AWS)". [Source: capitalone.wd12.myworkdayjobs.com] [Verified 2026-05-21 — already in Topic 04 FACTS.md]
- **Cloud Custodian** (C1 OSS, CNCF Incubating) operates at the AWS-API layer, not the K8s layer. K8s policy at Capital One is typically OPA Gatekeeper or Kyverno. [Source: cloud-custodian docs; C1 tech blog] [Verified 2026-05-21]

