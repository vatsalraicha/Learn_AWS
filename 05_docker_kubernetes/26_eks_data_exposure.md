# 26 — EKS deep: IRSA, EKS Pod Identity, EFS/FSx/S3 CSI, ASCP, KMS, VPC CNI

> *"This is THE module for the Capital One Sr Lead AI/ML role. EKS + KServe + IRSA + KMS is the stack."*

## Why this module exists

EKS is Capital One's K8s. The published Lead MLE job posting names KServe + EKS + PyTorch + TensorFlow explicitly. This module is the depth on the EKS-specific data-exposure primitives: IRSA, Pod Identity, the four CSI drivers (EBS, EFS, FSx-Lustre, S3-Mountpoint), ASCP for secrets, KMS for at-rest, and the VPC CNI's identity-per-pod model.

---

## 1. Identity — IRSA vs EKS Pod Identity

### 1.1 IRSA (2019, the established standard)

**IRSA (IAM Roles for Service Accounts)** uses an OIDC provider per cluster. A KSA (Kubernetes ServiceAccount) annotated with `eks.amazonaws.com/role-arn` becomes a holder of that IAM role's credentials.

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: infer-server
  namespace: ml-serving
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/ml-serving-infer
```

Under the hood:

1. EKS issues SA tokens with the OIDC issuer as audience.
2. AWS SDK in the pod sees env vars `AWS_ROLE_ARN` + `AWS_WEB_IDENTITY_TOKEN_FILE` (injected by a mutating admission webhook).
3. SDK calls `sts:AssumeRoleWithWebIdentity` — STS validates the JWT against the cluster's OIDC provider and returns 1-hour role credentials.

Trust policy on the IAM role:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "Federated": "arn:aws:iam::123456789012:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/EXAMPLED539D4633E53DE1B71EXAMPLE" },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "oidc.eks.us-east-1.amazonaws.com/id/EXAMPLED:sub": "system:serviceaccount:ml-serving:infer-server",
        "oidc.eks.us-east-1.amazonaws.com/id/EXAMPLED:aud": "sts.amazonaws.com"
      }
    }
  }]
}
```

The `sub` condition pins the role to exactly one ns/sa pair. The `aud` condition ensures the token was minted for STS.

### 1.2 EKS Pod Identity (Nov 2023, the modern alternative)

EKS Pod Identity ditches the OIDC chain. The cluster runs an `eks-pod-identity-agent` DaemonSet that intercepts AWS SDK metadata-service-lookups and returns role credentials directly.

```bash
aws eks create-pod-identity-association \
  --cluster-name prod \
  --namespace ml-serving \
  --service-account infer-server \
  --role-arn arn:aws:iam::123456789012:role/ml-serving-infer
```

Trust policy:

```json
{ "Effect": "Allow", "Principal": { "Service": "pods.eks.amazonaws.com" }, "Action": ["sts:AssumeRole","sts:TagSession"] }
```

### 1.3 Choosing

| Aspect | IRSA | EKS Pod Identity |
|---|---|---|
| Setup overhead | Per-role OIDC trust policy | Per-association call (simpler) |
| Cross-cluster reuse of role | Hard (OIDC issuer per cluster) | Easy |
| Cross-account | Possible | Easier |
| AWS SDK support | Old + Universal | Newer SDKs (v3 for JS, recent boto3) |
| Capital One stack? | Pre-2024 standard | New deploys, post-2024 |

**Use Pod Identity for new clusters.** Migrate IRSA where convenient. Both work.

### 1.4 The IMDS hop-limit reminder

Independent of IRSA/Pod-Identity, set `httpPutResponseHopLimit=1` on EKS nodes. Capital One 2019 lesson. The EKS launch template should include:

```hcl
resource "aws_launch_template" "eks_node" {
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }
}
```

Pods talking to IMDS = bad. Pods talking to IRSA / Pod Identity endpoint = good (separate endpoint, `169.254.170.23` for Pod Identity).

---

## 2. EBS CSI — block storage for stateful pods

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata: { name: gp3-encrypted }
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  encrypted: "true"
  kmsKeyId: arn:aws:kms:us-east-1:123456789012:key/<cmk-id>
volumeBindingMode: WaitForFirstConsumer
reclaimPolicy: Retain                # prod: never auto-delete data
allowVolumeExpansion: true
```

The CSI controller is a Deployment + Node DaemonSet. Install via EKS add-on:

```bash
aws eks create-addon --cluster-name prod --addon-name aws-ebs-csi-driver \
  --service-account-role-arn arn:aws:iam::123:role/AmazonEKS_EBS_CSI_DriverRole
```

The controller's SA gets EC2 permissions to create/attach/delete volumes via IRSA.

For ML training checkpoints / vector indices / databases: gp3 is the default; io2 Block Express for high-IOPS DBs.

---

## 3. EFS CSI — RWX shared file storage

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata: { name: efs-sc }
provisioner: efs.csi.aws.com
parameters:
  provisioningMode: efs-ap                # use Access Points (recommended)
  fileSystemId: fs-0123456789abcdef0
  directoryPerms: "0750"
  gidRangeStart: "10000"
  gidRangeEnd: "20000"
```

The driver creates EFS Access Points (module 13) dynamically per PVC, with random GIDs in the range — multi-tenant safe.

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata: { name: training-data, namespace: ml-serving }
spec:
  storageClassName: efs-sc
  accessModes: [ReadWriteMany]
  resources: { requests: { storage: 1Ti } }       # EFS is elastic; this is just a label
```

Pod mounts EFS via NFSv4.1 with `tls`. The EFS file system has:
- Encryption at rest with CMK.
- Encryption in transit (stunnel-wrapped NFS).
- IAM-based access (`iam: ENABLED` on the access point + IRSA-rolled task permissions).

For ML training where 8-256 GPU pods read the same dataset: EFS is the cleanest cloud-native answer.

---

## 4. FSx for Lustre CSI — high-perf parallel training

For 1000+ GPU training where EFS bandwidth saturates: FSx for Lustre.

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata: { name: fsx-lustre-1200-ssd }
provisioner: fsx.csi.aws.com
parameters:
  subnetId: subnet-abc...
  securityGroupIds: sg-abc...
  s3ImportPath: s3://myorg-training-data/2026-q2/
  s3ExportPath: s3://myorg-training-checkpoints/
  deploymentType: PERSISTENT_2
  perUnitStorageThroughput: "1000"
  storageType: SSD
```

Lustre provisioned with `s3ImportPath` lazy-loads data from S3 on first read (Data Repository Association). After training, dirty data evicts back to `s3ExportPath`. This is the **canonical large-scale training pattern**: S3 as cold storage + FSx Lustre as hot cache.

Pod mounts the Lustre FS at startup; reads stream from S3 transparently on first touch.

---

## 5. Mountpoint for Amazon S3 CSI — read-mostly S3 as filesystem

GA April 2024. For ML training where you want POSIX read but the dataset is S3:

```yaml
apiVersion: v1
kind: PersistentVolume
metadata: { name: s3-mountpoint }
spec:
  capacity: { storage: 1Ti }
  accessModes: [ReadOnlyMany]
  mountOptions:
    - allow-delete
    - region=us-east-1
    - prefix=2026-q2/
  csi:
    driver: s3.csi.aws.com
    volumeHandle: training-bucket-mount
    volumeAttributes: { bucketName: myorg-training-data }
```

POSIX limitations: no random writes, no in-place modifications, no rename in same prefix (which is fine for read-mostly). Significantly cheaper than provisioning Lustre, especially for occasional-read workloads.

---

## 6. ASCP — AWS Secrets and Configuration Provider for CSI

The K8s **Secrets Store CSI Driver** (vendor-neutral) + AWS provider (ASCP) lets pods mount Secrets Manager / SSM Parameter Store entries as files.

```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata: { name: db-creds, namespace: ml-serving }
spec:
  provider: aws
  parameters:
    objects: |
      - objectName: "prod/db/postgres"
        objectType: "secretsmanager"
        jmesPath:
          - { path: "password", objectAlias: "db_password" }
          - { path: "username", objectAlias: "db_username" }
```

```yaml
# Pod spec
spec:
  serviceAccountName: infer-server            # IRSA-rolled to allow SM access
  containers:
    - name: app
      volumeMounts:
        - { name: db-creds, mountPath: /run/secrets, readOnly: true }
  volumes:
    - name: db-creds
      csi:
        driver: secrets-store.csi.k8s.io
        readOnly: true
        volumeAttributes: { secretProviderClass: db-creds }
```

The Secrets Manager IAM permission on the IRSA role:

```json
{ "Effect": "Allow", "Action": "secretsmanager:GetSecretValue", "Resource": "arn:aws:secretsmanager:us-east-1:123:secret:prod/db/*" }
```

Alternative: **External Secrets Operator with AWS provider**. Picks the same secret, but creates a K8s Secret object (which then goes through KMS-encrypted etcd). Pick ESO if your app needs an env var; pick ASCP if it can read a file.

---

## 7. KMS envelope encryption for etcd

When creating an EKS cluster:

```hcl
resource "aws_eks_cluster" "prod" {
  encryption_config {
    provider { key_arn = aws_kms_key.eks_secrets.arn }
    resources = ["secrets"]
  }
}
```

K8s Secrets in etcd are now KMS-encrypted. EKS uses KMS v2 (since K8s 1.29). Required for any regulated-finance cluster.

---

## 8. VPC CNI — pod = ENI = VPC IP

The AWS VPC CNI gives each pod a routable VPC IP via a secondary IP on the node's ENI. Effects:

- Pods are **directly addressable from the VPC** — same network as anything else in your VPC. No overlay; no NAT.
- **Security groups per pod** — supported on Nitro instances. Attach SGs to KSA via `SecurityGroupPolicy` CRD.
- **Pod limits per node** — based on ENI count × IPs-per-ENI. A `m5.large` can hold 29 pods; an `m5.4xlarge` 234; a GPU `p4d.24xlarge` ~ 600. Beyond that, you need a larger instance or **prefix delegation** (an ENI can carry an IP prefix instead of individual IPs).

### 8.1 Security Group per Pod

```yaml
apiVersion: vpcresources.k8s.aws/v1beta1
kind: SecurityGroupPolicy
metadata: { name: pg-client-sg, namespace: ml-serving }
spec:
  podSelector:
    matchLabels: { app: pg-client }
  securityGroups:
    groupIds: [sg-abc...]
```

Now pods labeled `app: pg-client` get an additional SG attached, useful for granting access to RDS without opening the whole node CIDR.

### 8.2 The VPC CNI alternative — Cilium

Some teams replace VPC CNI with **Cilium** for richer NetworkPolicy, L7 visibility, kube-proxy replacement, and service-mesh-without-sidecar. AWS now has a **first-class Cilium support** (Cilium Distribution for EKS) since 2024.

For Capital One's KServe stack: **Cilium for L7 + Istio for mesh** is plausible; **VPC CNI + Calico-policy + Istio** is the historical pattern. Either is defensible.

---

## 9. EKS Auto Mode (Dec 2024)

EKS Auto Mode bundles:
- Karpenter for node autoscaling.
- ALB controller for ingress.
- EBS CSI + EFS CSI.
- Pod Identity preconfigured.
- KMS encryption.

A "managed everything" tier. For non-regulated workloads, accelerates time-to-cluster. For Capital One: typically you want explicit control of these so Auto Mode may be over-managed.

---

## 10. Karpenter for GPU autoscaling

```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata: { name: gpu-h100 }
spec:
  template:
    metadata:
      labels: { workload: ml-training }
    spec:
      taints:
        - { key: nvidia.com/gpu, value: "true", effect: NoSchedule }
      requirements:
        - { key: kubernetes.io/arch,           operator: In, values: [amd64] }
        - { key: node.kubernetes.io/instance-type, operator: In, values: [p5.48xlarge, p5e.48xlarge] }
        - { key: karpenter.sh/capacity-type,   operator: In, values: [on-demand] }
      nodeClassRef: { name: gpu-default }
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 5m              # don't churn GPU nodes
    expireAfter: 720h
  limits:
    cpu: "1000"
    memory: 4000Gi
    nvidia.com/gpu: "32"
```

Karpenter provisions nodes on demand based on pending pods. Critical for GPU economics — you only pay for active training capacity.

`consolidateAfter: 5m` avoids the "kill the GPU node we just spun up because a pod went away for a second" thrash. Capital One's KServe deployments would tune this to match their training churn.

---

## 11. The reference EKS+KServe architecture

```
┌──────────────────────────────────────────────────────────────────┐
│ EKS cluster (with KMS envelope for etcd)                         │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ ml-serving namespace                                       │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │ InferenceService (KServe)                            │  │  │
│  │  │  ServiceAccount with IRSA → S3 model bucket          │  │  │
│  │  │  PSA: restricted                                     │  │  │
│  │  │  Pod: read-only FS + tmpfs + cap-drop ALL            │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ kube-system (PSA: privileged)                              │  │
│  │  VPC CNI, Karpenter, EBS/EFS/FSx/S3 CSI, ASCP, OTel        │  │
│  │  Falco, Cilium (if installed), Kyverno                     │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Node Launch Template: IMDSv2 + hop-limit 1                      │
└──────────────────┬──────────────────┬──────────────────┬─────────┘
                   │                  │                  │
            ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐
            │ ECR (CMK,   │    │ S3 (SSE-KMS,│    │ Secrets Mgr │
            │ IMMUTABLE)  │    │ Block Pub,  │    │ + CMK       │
            │             │    │ VPC GW EP)  │    │             │
            └─────────────┘    └─────────────┘    └─────────────┘
```

Cross-cuts:
- **Identity**: IRSA / Pod Identity per workload.
- **Egress**: VPC endpoints; no NAT GW reachable from pods (Cloud Custodian rule).
- **Admission**: Kyverno enforcing PSA-restricted + image signing.
- **Audit**: K8s audit log → CloudWatch → Security Hub.
- **Observability**: kube-prometheus-stack + DCGM + Falco + Hubble.

---

## Sanity check

1. IRSA vs EKS Pod Identity — name two reasons to choose Pod Identity for a new cluster.
2. What's the practical difference between EFS CSI and FSx-for-Lustre CSI for ML training data?
3. Mountpoint-for-S3 vs s3fs — name two reasons Mountpoint is the safer choice for K8s.
4. What does Security Group per Pod give you that node-level SG does not?
5. Why does Karpenter need `consolidateAfter: 5m` for GPU node pools but not for CPU?
6. EKS KMS envelope encryption protects what specifically?

---

## Sources

- [IRSA](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html)
- [EKS Pod Identity](https://docs.aws.amazon.com/eks/latest/userguide/pod-identities.html)
- [EBS CSI driver](https://github.com/kubernetes-sigs/aws-ebs-csi-driver)
- [EFS CSI driver](https://github.com/kubernetes-sigs/aws-efs-csi-driver)
- [FSx for Lustre CSI](https://github.com/kubernetes-sigs/aws-fsx-csi-driver)
- [Mountpoint S3 CSI](https://github.com/awslabs/mountpoint-s3-csi-driver)
- [Secrets Store CSI ASCP](https://github.com/aws/secrets-store-csi-driver-provider-aws)
- [VPC CNI](https://github.com/aws/amazon-vpc-cni-k8s)
- [Karpenter](https://karpenter.sh/)
- [EKS Auto Mode](https://aws.amazon.com/eks/auto-mode/)

→ Next: [27 — **GKE deep — Workload Identity Federation, GCS Fuse CSI, BinAuth**](27_gke_data_exposure.md)
