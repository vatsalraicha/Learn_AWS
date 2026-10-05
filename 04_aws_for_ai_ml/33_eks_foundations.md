# Module 33 — EKS Foundations

> **What this is:** Amazon EKS — managed Kubernetes — cluster anatomy, Managed Node Groups vs Karpenter, Fargate Profiles, VPC CNI, IRSA / Pod Identity, EKS Auto Mode. The foundation for Capital One's KServe model serving (Module 54).

---

## 1. Cluster anatomy

EKS = AWS-managed Kubernetes control plane + your data plane.

- **Control plane** (AWS-managed): API server, etcd, controller manager, scheduler. **$0.10/hr per cluster.**
- **Data plane** (your nodes): EC2 instances (via Managed Node Groups or self-managed) or Fargate (serverless pods).

## 2. Data plane options

### Managed Node Groups (MNG)

AWS-managed EC2 instance groups. You define instance type, scaling bounds, taints, labels. AWS handles AMI updates, draining.

### Karpenter (the modern choice)

**Karpenter v1.x** GA late 2024. Replaces Cluster Autoscaler with a smarter, faster node provisioner:

- Reads pending-pod constraints (resources, taints, topology).
- Spins up the right instance type **directly** — no ASG indirection.
- Faster scale-up (10-30 sec vs minutes).
- Supports Spot + diverse instance types natively.
- Native consolidation: terminates underutilized nodes proactively.

**New clusters in 2026 should default to Karpenter** over MNG.

### Fargate Profiles

Serverless pods. You define a selector (namespace + labels); matching pods run on Fargate. No node management.

Limitations: no GPU, no `hostPath`, no DaemonSets (use Fargate sidecars instead).

## 3. EKS Auto Mode (GA Dec 2024)

A higher-level abstraction:
- **Karpenter built-in** — no manual install.
- **System add-ons managed** by AWS (kube-proxy, VPC CNI, CoreDNS, EBS CSI, etc.).
- **Compute and storage** automatically provisioned.

The "managed Kubernetes that actually feels managed." New 2026 clusters should consider Auto Mode unless you have specific reasons to manage the data plane yourself.

## 4. VPC CNI (pod networking)

The default networking plugin. **Each pod gets a VPC IP** from an ENI attached to its node.

- **Pros:** native VPC integration; security groups apply at pod level; no overlay overhead.
- **Cons:** IP exhaustion is the #1 EKS scaling pain. A `m5.large` only supports ~30 pods.

**Solutions:**
- **Prefix delegation** — allocate /28 prefixes to ENIs instead of individual IPs. Massive pod-per-node increase.
- **Secondary CIDR / custom networking** — give pods IPs from a different (e.g., 100.64.0.0/10) CIDR.

## 5. IAM Roles for Service Accounts (IRSA) vs Pod Identity

### IRSA (GA 2019-09-03)

Maps K8s ServiceAccount → IAM role via OIDC federation.

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ml-trainer
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/MLTrainerRole
```

Trust policy on the role uses the cluster's OIDC provider, conditioned on `system:serviceaccount:<namespace>:<sa-name>`.

### EKS Pod Identity (GA 2023-11-26)

Simpler alternative using an **EKS-managed agent** instead of OIDC + cluster trust policies.

- Easier cross-account.
- Fewer trust-policy edits at scale.
- **Default pick for new EKS clusters in 2026.**

## 6. GPU support

- **NVIDIA GPU Operator** — manages GPU drivers, CUDA toolkit, MIG (Multi-Instance GPU) on nodes.
- Karpenter NodePools for GPU instance types (P5, G6, Inf2, Trn2).
- **EKS Auto Mode** handles GPU drivers automatically.

## 7. Upgrades

EKS supports **Kubernetes versions for ~14 months** (4 versions). Extended support pricing ($0.60/hr per cluster) for older versions after standard support ends.

Upgrade path:
1. Upgrade control plane.
2. Upgrade managed node groups / Karpenter NodePools.
3. Upgrade add-ons.

Pin your add-on versions in IaC; surprises hurt.

## 8. EKS Anywhere & EKS Distro

- **EKS Anywhere** — Kubernetes on your bare metal / vSphere with AWS support.
- **EKS Distro** — the open-source Kubernetes distribution AWS uses; you can run it anywhere.

## 9. Pricing

- **Control plane**: $0.10/hr × 24 × 30 = ~$72/month per cluster.
- **Extended support**: $0.60/hr per cluster (after standard EOL).
- **Nodes**: standard EC2 + EBS pricing.
- **Fargate Profiles**: per-vCPU + per-memory + per-duration.

## 10. 2024-2026 changes

- **EKS Auto Mode** GA Dec 2024.
- **Karpenter v1.x** stable.
- **EKS Pod Identity** widely adopted.
- **Pod Identity Agent** replaces IRSA for new clusters.
- **EKS in 14-month version support window.**

## 11. Pitfalls

- **VPC CNI IP exhaustion** — node packs few pods unless prefix delegation enabled.
- **Cluster upgrade without testing add-ons** — version drift breaks things.
- **MNG instead of Karpenter** for new builds — slower scale-up, harder Spot.
- **GPU operator misconfig** — pods stuck `Pending` with cryptic errors.
- **Default `0.0.0.0/0` egress** on cluster nodes → NAT GW cost.

## 12. Capital One lens

Per their Sr Lead AI/ML / Lead MLE postings, **EKS is mandatory for ML model serving** (KServe specifically). Likely architecture:

- **EKS clusters per LOB or per platform team.**
- **Karpenter for GPU node provisioning** as inference traffic scales.
- **IRSA / Pod Identity** for model pod → S3 / ECR access without static creds.
- **KServe + Istio** as the serving stack (Module 54).

## 13. Sanity check

1. Karpenter vs Managed Node Groups — what's the modern default?
2. What is the VPC CNI IP exhaustion problem, and the fix?
3. IRSA vs Pod Identity — when is each preferred?
4. What does EKS Auto Mode automate?
5. What's the extended-support cost penalty for old K8s versions?

## 14. Cross-references

- **Module 2** — IAM (IRSA / Pod Identity)
- **Module 6** — VPC + CNI / secondary CIDR
- **Module 30** — EC2 + GPU instances (the node hardware)
- **Module 54** — KServe deep (the ML serving layer on EKS)

## Primary sources

- [`EKS_Best_Practices.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/EKS_Best_Practices.html)
- [`Karpenter_Best_Practices.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/Karpenter_Best_Practices.html)
- Research report: [`08_compute_for_ml.md`](../../research_inputs/04_aws_for_ai_ml/08_compute_for_ml.md)
