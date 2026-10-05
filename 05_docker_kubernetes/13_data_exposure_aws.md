# 13 — Data exposure for containers — AWS

> *"Capital One 2019 was a single missing config: `MetadataHttpTokens=required` and `http_put_response_hop_limit=1`. Everything else amplified it."*

## Why this module exists

The user's explicit ask: how to use and expose data within Docker containers safely on AWS. This module covers Docker-on-EC2 + ECS (EC2 + Fargate). EKS gets its own deep dive in module 26.

The AWS data-exposure story has five mandatory disciplines:

1. **No long-lived AWS credentials in containers** — use IAM roles via IMDS or task roles.
2. **IMDSv2-only with hop limit = 1** — the Capital One lesson.
3. **VPC endpoints** for S3 and other services to keep traffic off the public internet.
4. **KMS** for encryption at rest, with CMKs for compliance.
5. **Bucket policies + S3 Block Public Access** as last-line defense.

---

## 1. Identity — how containers get AWS credentials

### 1.1 EC2 instance profile (the foundation)

An EC2 instance can have an **IAM instance profile** attached. The role's credentials are exposed via the **Instance Metadata Service (IMDS)** at `http://169.254.169.254/`. Any process on the instance — including any container — can fetch these credentials.

```bash
# Inside any container on the host
TOKEN=$(curl -X PUT -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" \
        http://169.254.169.254/latest/api/token)
ROLE=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" \
        http://169.254.169.254/latest/meta-data/iam/security-credentials/)
curl -H "X-aws-ec2-metadata-token: $TOKEN" \
        http://169.254.169.254/latest/meta-data/iam/security-credentials/$ROLE
```

This is **convenient and dangerous**. Every container shares the instance role.

### 1.2 ECS Task IAM Role (the right pattern for ECS)

ECS gives each *task* its own IAM role. Credentials are served on `169.254.170.2/v2/credentials/<token>` — different endpoint than IMDS. The AWS SDK detects this automatically via `AWS_CONTAINER_CREDENTIALS_RELATIVE_URI` env var that ECS sets in the task.

```jsonc
// task-definition.json
{
  "family": "infer-server",
  "taskRoleArn": "arn:aws:iam::123456789012:role/InferServerTaskRole",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  // ...
}
```

Two distinct roles:

- **`executionRoleArn`** — used by the ECS agent to pull the image, push logs to CloudWatch, fetch secrets from Secrets Manager *for the task definition*. Permissions: `AmazonECSTaskExecutionRolePolicy` plus `secretsmanager:GetSecretValue` for any secrets referenced.
- **`taskRoleArn`** — used by the application itself for AWS API calls (read S3, query DynamoDB, etc.). This is where application IAM policies live.

This separation is essential: the executor doesn't need application data permissions; the application doesn't need image-pull permissions.

### 1.3 EC2-on-ECS vs Fargate

For tasks on **EC2 capacity providers**, the host's IMDS is still reachable from containers if you don't block it. For **Fargate**, the host is a Firecracker MicroVM, and IMDS is restricted by AWS to only the task role endpoint by default. Fargate is the **safer choice** if you don't otherwise need EC2.

### 1.4 IMDSv2 — the Capital One fix

IMDSv1 was a simple HTTP GET. IMDSv2 requires a **session token** obtained via PUT request first. The token is bound to the session and (crucially) has a **TTL hop-limit** for forwarding.

Hardening for EC2 instances running containers:

```hcl
resource "aws_instance" "container_host" {
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"     # IMDSv2 only — rejects IMDSv1
    http_put_response_hop_limit = 1              # token has 1 hop max
  }
}
```

The hop-limit=1 is the lever: when a containerized process makes the PUT to get a token, the response packet's TTL is set to 1. The packet has to traverse the veth interface to leave the container — and veth interfaces decrement TTL. The token never reaches the container. **No IMDS access from containers, period.**

The AWS-launched default for new EC2 since 2024 is IMDSv2-required, but you must set `http_put_response_hop_limit=1` explicitly to fully block containers.

For ECS-on-EC2, this means containers must use the **task role endpoint** (`169.254.170.2`), not IMDS — exactly the desired posture.

For EKS, same posture, plus IRSA / Pod Identity (module 26).

### 1.5 The Capital One incident re-told as one IaC fix

```hcl
# What Capital One missed (pre-2019):
resource "aws_instance" "waf" {
  # ... no metadata_options block ...
}

# What would have prevented it:
resource "aws_instance" "waf" {
  metadata_options {
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }
}
```

That single block. Capital One's published response built **Cloud Custodian rules** (now CNCF Incubating) that detect missing `http_tokens=required` across the org and remediate automatically. Module 23 covers the policy-as-code angle.

---

## 2. Object storage — Amazon S3

### 2.1 Access patterns

For ML, S3 is the canonical object store. Three access patterns:

| Pattern | Use case | Trade-offs |
|---|---|---|
| **SDK calls (boto3, AWS Python SDK)** | App-level reads/writes, batch ETL | Cleanest; explicit; full IAM control |
| **Mountpoint for Amazon S3** | Training data, read-heavy mount | GA Apr 2024; POSIX-limited (no rename in same prefix); ML training is the headline use case |
| **s3fs / goofys (FUSE)** | Legacy apps that need a file path | NOT recommended; performance unpredictable; CAP_SYS_ADMIN required |

**Mountpoint for S3** is the safer modern choice when filesystem semantics are needed. For ECS-on-EC2 or EC2-Docker:

```bash
# Install mount-s3 on the host
yum install -y mount-s3                       # AL2023
mount-s3 mybucket /mnt/mybucket --read-only

# Bind-mount into container
docker run -v /mnt/mybucket:/data:ro myimage
```

For EKS, the **Mountpoint for S3 CSI driver** does this declaratively (module 26).

### 2.2 S3 IAM patterns

The IAM policy attached to the task role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": "arn:aws:s3:::myorg-ml-data/training/2026/*"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": "arn:aws:s3:::myorg-ml-data",
      "Condition": {
        "StringLike": {"s3:prefix": ["training/2026/*"]}
      }
    },
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject"],
      "Resource": "arn:aws:s3:::myorg-ml-artifacts/models/${aws:PrincipalTag/Team}/*"
    }
  ]
}
```

Three discipline points:

- **No bucket-level wildcards in prod** — restrict to prefixes.
- **Separate read and write resources** — never `s3:*` on the same role.
- **Tag-conditional resources** — `${aws:PrincipalTag/Team}` enforces per-team isolation in shared buckets.

### 2.3 S3 encryption & VPC endpoints

- **Bucket encryption at rest**: SSE-S3 (free, AWS-managed key), SSE-KMS (CMK, billed per call), or SSE-C (you supply key). For regulated finance, **SSE-KMS with a CMK** is the floor. Bucket policy should `Deny` `s3:PutObject` without `s3:x-amz-server-side-encryption=aws:kms`.
- **In transit**: TLS to S3 is the default; bucket policy should `Deny` `aws:SecureTransport=false`.
- **VPC Gateway Endpoint for S3**: free, no public-internet egress. Configure your VPC route table; S3 traffic stays inside AWS backbone.
- **S3 Block Public Access**: account-level + bucket-level. Set at the account level via Service Control Policy for an org-wide guarantee.
- **S3 Object Ownership = Bucket Owner Enforced**: disables ACLs; everything is owned by the bucket account. Removes a class of misconfig (cross-account objects with broken ACLs).

### 2.4 The S3 read-only-from-container pattern

For ML serving containers that pull a model artifact at startup:

```dockerfile
# In the container's startup script
#!/bin/bash
set -euo pipefail
aws s3 sync s3://myorg-ml-artifacts/models/sentiment/v1.4/ /opt/model/
exec python -m server.app
```

The container's IAM role grants only `s3:GetObject` on `s3://myorg-ml-artifacts/models/sentiment/*`. No write permission, no other bucket, no other prefix. If the container is compromised, the blast radius is one model version.

---

## 3. EFS for shared file access

**Amazon EFS** is NFSv4 as a service. Multi-AZ replicated, scales to petabytes, mounts to many hosts/containers concurrently (RWX). Perfect for:

- Shared training data on ECS / EKS / EC2.
- Notebook home directories for SageMaker Studio (uses EFS underneath).
- Any "Linux filesystem we want many containers to share" pattern.

### 3.1 EFS mount on ECS (`efsVolumeConfiguration`)

```jsonc
// task-definition.json
{
  "volumes": [
    {
      "name": "training-data",
      "efsVolumeConfiguration": {
        "fileSystemId": "fs-0123456789abcdef0",
        "rootDirectory": "/training",
        "transitEncryption": "ENABLED",
        "authorizationConfig": {
          "accessPointId": "fsap-0a1b2c3d4e5f67890",
          "iam": "ENABLED"
        }
      }
    }
  ],
  "containerDefinitions": [
    {
      "mountPoints": [
        {"sourceVolume": "training-data", "containerPath": "/data", "readOnly": true}
      ]
    }
  ]
}
```

Three security knobs:

- **`transitEncryption: ENABLED`** — TLS for the NFS connection (port 2049 via stunnel).
- **`accessPointId`** — restricts the mount to one POSIX-uid-owned subdirectory of the EFS.
- **`iam: ENABLED`** — IAM authorization on top of NFS — the task role must have `elasticfilesystem:ClientMount`.

### 3.2 EFS Access Points — the multi-tenant pattern

An EFS Access Point lets you carve a single EFS file system into per-tenant slices, each with its own:

- Root directory (the tenant's view)
- POSIX UID/GID enforced at mount time
- Creation permissions

```hcl
resource "aws_efs_access_point" "team_alpha" {
  file_system_id = aws_efs_file_system.shared.id
  root_directory {
    path = "/teams/alpha"
    creation_info { owner_uid = 10001, owner_gid = 10001, permissions = "0750" }
  }
  posix_user { uid = 10001, gid = 10001 }
}
```

Now a task with this access point sees only `/teams/alpha` as `/`. Even with `cd ..`, the kernel keeps it confined. This is **the** multi-tenant primitive for shared EFS.

### 3.3 EFS performance modes

- **Throughput**: Bursting (default, scales with size) or Provisioned (pay for guaranteed MB/s).
- **Performance**: General Purpose (default) or Max I/O (higher concurrent but higher per-op latency — usually NOT what you want).
- **`nconnect=`**: NFS option, set via mount options. Boosts throughput from a single client.

For ML training that fits the "many containers reading the same dataset" pattern, EFS is the closest cloud-native equivalent to on-prem NFS.

---

## 4. FSx variants

| FSx flavor | Use |
|---|---|
| **FSx for Lustre** | High-perf parallel FS for HPC + ML training (1k+ GPU). Native S3 integration ("data repository association"). |
| **FSx for OpenZFS** | NFS with ZFS features (snapshots, clones). |
| **FSx for NetApp ONTAP** | Lift-and-shift from on-prem NetApp; same protocols (NFS, SMB, iSCSI). |
| **FSx for Windows File Server** | SMB for Windows containers. |

**FSx for Lustre** is the ML-training high-perf primitive. Provision a 1.2 TB+ filesystem, link to an S3 bucket; reads from the FS pull lazily from S3; writes can be evicted back to S3. The container mounts Lustre via the Lustre kernel client on the host, then bind-mounts.

For ECS/EC2-Docker training: mount FSx on the host, bind-mount into the container. For EKS: FSx for Lustre CSI driver (module 26).

---

## 5. Secrets — Secrets Manager and Parameter Store

### 5.1 Secrets Manager pattern in ECS

```jsonc
// task-definition.json — container definition
{
  "secrets": [
    {
      "name": "DB_PASSWORD_FILE",
      "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:prod/db/postgres-xxxx"
    }
  ]
}
```

ECS fetches the secret using the **execution role** (not the task role!), and exposes it as an env var. Permission needed on the execution role:

```json
{"Effect": "Allow", "Action": "secretsmanager:GetSecretValue", "Resource": "arn:aws:secretsmanager:...:secret:prod/db/*"}
```

**The env-var pattern is suboptimal** (env-var leak surface — module 08). For better hygiene, the application should fetch the secret directly from Secrets Manager using the task role at runtime, write to a tmpfs path, and reference that path. AWS Secrets Manager Agent (Sep 2024 GA) automates this — runs as a sidecar, exposes a local HTTP/Unix-socket cache.

### 5.2 SSM Parameter Store

The cheaper option (free tier exists). Same mechanism, different ARN format (`ssm:parameter/...`). Use SecureString type with KMS encryption.

```bash
aws ssm get-parameter --name /prod/myapp/db_url --with-decryption --query 'Parameter.Value' --output text
```

For high-frequency reads, Parameter Store has rate limits — use Secrets Manager + caching for high-traffic services.

### 5.3 KMS — the encryption backbone

All AWS data-at-rest options use **KMS**: S3 SSE-KMS, EBS volume encryption, RDS, Secrets Manager. Three key types:

- **AWS managed key** (`aws/s3`, `aws/secretsmanager`) — free, can't audit usage at key level, can't restrict who uses it across accounts.
- **Customer managed key (CMK)** — paid ($1/month/key + $0.03 per 10k API calls), full key policy control, KMS Grants for fine-grained.
- **AWS CloudHSM** — your own FIPS 140-2 Level 3 HSM. Required for some payment/healthcare contexts.

For regulated finance (Capital One pattern): **CMK per workload / data class**, with key policy restricting `kms:Decrypt` to the specific task role + S3 service + bucket condition.

---

## 6. ECR — covered in module 05, recap for containers

For ECS / EKS, pulling from ECR works automatically when the **execution role** has `AmazonEC2ContainerRegistryReadOnly` (or the IRSA / Pod Identity equivalent in EKS).

For cross-account pulls: ECR Repository Policy on the source allows the puller account; the puller's execution role gets `ecr:GetAuthorizationToken` + `ecr:BatchGetImage` + `ecr:GetDownloadUrlForLayer`.

For VPC isolation: ECR API endpoint + ECR DKR endpoint + **S3 Gateway Endpoint** (image layers live in S3 — module 05 reminder).

---

## 7. VPC endpoints — the data-plane firewall

Without VPC endpoints, every API call from a container to AWS services goes over the public internet (or via NAT gateway). With VPC endpoints, the API call stays in AWS's network. For containers:

| Service | Endpoint type | Why containers need it |
|---|---|---|
| S3 | Gateway (free) | Object reads/writes |
| DynamoDB | Gateway (free) | Key-value reads/writes |
| ECR API + DKR | Interface (paid) | Image pulls |
| Secrets Manager | Interface | Secret reads |
| SSM | Interface | Parameter reads |
| CloudWatch Logs | Interface | Log shipping |
| KMS | Interface | Encryption ops |
| STS | Interface | Cross-account assume-role |
| Bedrock | Interface | LLM API calls |
| SageMaker Runtime | Interface | Inference endpoint calls |

VPC endpoint **policies** scope what API calls can be made through them. E.g., the S3 endpoint policy can restrict to specific buckets: `"Resource": "arn:aws:s3:::myorg-*"`. This is a powerful belt-and-braces control over the per-task IAM role.

---

## 8. ECS network modes

| Mode | Container networking | Use case |
|---|---|---|
| `awsvpc` | Each task gets its own ENI in the VPC | The default; required for Fargate; lets per-task SG work |
| `bridge` | docker0 bridge | Legacy EC2-mode tasks |
| `host` | Host network namespace | Performance, but loses task isolation |
| `none` | No networking | Batch jobs talking only to volumes |

**Always use `awsvpc` in production.** Per-task ENI gives:

- Per-task security group (fine-grained ingress/egress control).
- IPv4 (and IPv6) address per task — clean for service discovery.
- VPC Flow Logs at task level.

---

## 9. Security groups — task-level egress controls

```hcl
resource "aws_security_group" "task_egress" {
  name = "ml-task-egress"
  vpc_id = var.vpc_id

  # Allow S3 via Gateway endpoint
  egress {
    from_port = 443
    to_port   = 443
    protocol  = "tcp"
    prefix_list_ids = [data.aws_prefix_list.s3.id]
  }
  # Allow KMS via Interface endpoint
  egress {
    from_port = 443
    to_port   = 443
    protocol  = "tcp"
    cidr_blocks = [data.aws_vpc.this.cidr_block]
  }
  # Allow logs
  egress {
    from_port = 443
    to_port   = 443
    protocol  = "tcp"
    cidr_blocks = [data.aws_vpc.this.cidr_block]
  }
  # Deny everything else — implicit
}
```

Default-deny outbound + explicit allows. Cloud Custodian rules detect "security group with `0.0.0.0/0` egress" and remediate.

---

## 10. Logs — to CloudWatch via `awslogs`

```jsonc
{
  "containerDefinitions": [
    {
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/infer-server",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "infer-server",
          "awslogs-create-group": "true"
        }
      }
    }
  ]
}
```

Permission on execution role: `logs:CreateLogStream`, `logs:PutLogEvents` (+ `logs:CreateLogGroup` if `awslogs-create-group` is true).

Encrypt log groups with KMS CMK if logs may contain sensitive data: `aws logs associate-kms-key`.

---

## 11. The reference architecture

```
┌──────────────────────────────────────────────────────────────────┐
│ VPC (10.0.0.0/16)                                                │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐        │
│  │ ECS Fargate  │    │ ECS Fargate  │    │ ECS EC2      │        │
│  │ infer-server │    │ pipeline     │    │ training     │        │
│  │              │    │              │    │ (GPU)        │        │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘        │
│         │ awsvpc ENI         │ awsvpc ENI       │ awsvpc ENI     │
│         │ per-task SG        │ per-task SG      │ per-task SG    │
│         │                    │                  │                │
│  ┌──────▼────────────────────▼──────────────────▼─────────────┐  │
│  │ Private subnet                                             │  │
│  └──────┬─────────────────────┬───────────────────────────────┘  │
│         │ S3 Gateway Endpoint │ Interface Endpoints              │
│         │                     │ (ECR, KMS, SecretsMgr, Logs)     │
└─────────┼─────────────────────┼──────────────────────────────────┘
          │                     │
   ┌──────▼──────┐         ┌────▼──────┐
   │ S3 buckets  │         │ Secrets   │
   │ (SSE-KMS    │         │ Manager   │
   │  + Block    │         │ + KMS CMK │
   │  Public)    │         └───────────┘
   └─────────────┘
```

All flows stay inside the VPC + AWS backbone. No NAT gateway egress to the internet for AWS service calls. IMDS unreachable from containers (hop-limit=1). Per-task IAM roles enforce least privilege. KMS encrypts at rest. Cloud Custodian enforces all of this with policy.

---

## 12. Capital One signal

Capital One's published security posture on AWS includes:

- **Cloud Custodian** policies enforcing `MetadataHttpTokens=required`, `BlockPublicAcls=true`, no `0.0.0.0/0` SG egress, no untagged resources.
- **Databolt** for at-rest tokenization (PCI/PII protection).
- **cfn-guard / cdk-nag** as CI-side IaC linting.
- **SCPs** at the org level enforcing region restrictions, deny-by-default services.

For an interviewee, the muscle memory should be: when asked "how would you secure container data on AWS?", you walk through IMDSv2 + IRSA/Task-Role + VPC endpoints + KMS CMK + S3 Block Public Access + Cloud Custodian — in that order — and you reference the Capital One 2019 breach as the canonical lesson for the first one.

---

## Sanity check

1. What's the exact mechanism by which `http_put_response_hop_limit=1` prevents a container from reading IMDS?
2. ECS task role vs execution role — what does each cover, and why is the separation important?
3. Mountpoint for S3 vs s3fs — name two reasons Mountpoint is the safer choice.
4. What does an EFS Access Point give you that a vanilla EFS mount does not?
5. Why is `aws:SecureTransport=false` deny in a bucket policy a defense in depth even if all clients use HTTPS?
6. List the seven VPC endpoints a typical ECS task needs (S3 + six interface endpoints).
7. KMS CMK vs AWS-managed key — list two reasons regulated finance requires CMK.

---

## Sources

- [AWS IMDSv2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html)
- [ECS Task IAM Role](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html)
- [Mountpoint for Amazon S3](https://aws.amazon.com/blogs/aws/mountpoint-for-amazon-s3-generally-available-and-ready-for-production-workloads/)
- [EFS Access Points](https://docs.aws.amazon.com/efs/latest/ug/efs-access-points.html)
- [FSx for Lustre](https://docs.aws.amazon.com/fsx/latest/LustreGuide/what-is.html)
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)
- [AWS VPC Endpoints](https://docs.aws.amazon.com/vpc/latest/privatelink/concepts.html)
- [AWS KMS](https://docs.aws.amazon.com/kms/)
- [Capital One OCC consent order, Aug 2020](https://www.occ.treas.gov/news-issuances/news-releases/2020/nr-occ-2020-101a.pdf)
- [Cloud Custodian](https://cloudcustodian.io/)

→ Next: [14 — **Data exposure — GCP**](14_data_exposure_gcp.md)
