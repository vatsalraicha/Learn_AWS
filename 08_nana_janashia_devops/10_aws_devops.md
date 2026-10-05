# 10 — AWS Services for DevOps

> Cross-link: [Topic 04 — AWS for AI/ML Engineers (57 modules)](../04_aws_for_ai_ml/) is the deep dive. This module is the **DevOps-focused subset** — the 12 services every CI/CD pipeline touches.

## 1. The DevOps-essential AWS services

| Service | Why DevOps cares |
|---|---|
| **IAM** | Who can do what; principle of least privilege |
| **EC2** | Compute for build agents, deploys |
| **VPC + Subnets + SGs** | Network isolation |
| **S3** | Artifact storage, Terraform state, log archives |
| **ECR** | Private container registry |
| **EKS / ECS / Fargate** | Container orchestration |
| **Lambda** | Event-driven automation |
| **CloudWatch** | Logs + metrics + alarms |
| **CloudTrail** | API audit log (security) |
| **Secrets Manager + Parameter Store** | Secret storage |
| **Systems Manager (SSM)** | Patch, SSH-less shell, parameter store |
| **CodeBuild / CodePipeline / CodeDeploy** | AWS-native CI/CD (less popular than Jenkins/GitLab/Actions but exists) |

See [Topic 04 README](../04_aws_for_ai_ml/README.md) for full scope.

## 2. Creating an AWS account (the production way)

Don't use the root account for daily work. Set up:
1. Root account: MFA on a hardware key (YubiKey), used only for billing changes.
2. **AWS Organizations** + multiple accounts (one per env: dev/staging/prod or one per team).
3. **AWS Control Tower** (preferred for new orgs in 2026) sets up baseline guardrails.
4. **IAM Identity Center** (formerly AWS SSO) for human user access.
5. **Service Control Policies (SCPs)** at OU level for deny-by-default policies.

Capital One: hundreds of AWS accounts under a single Organization, with Control Tower + Custodian governance.

## 3. IAM essentials for DevOps

- **Users** — long-lived identities; humans should use Identity Center SSO instead
- **Groups** — collections of users sharing permissions
- **Roles** — temporary credentials, assumed by services or federated principals
- **Policies** — JSON documents granting/denying actions
- **Permission Boundaries** — max-permissions cap on a role
- **Resource-based policies** — attached to S3 buckets, KMS keys, etc.

The 2026 pattern for CI/CD: **OIDC + IAM Role**, never long-lived access keys.
- GitHub Actions → OIDC → AssumeRoleWithWebIdentity → role
- GitLab CI → OIDC → role
- Jenkins on EC2/EKS → instance profile or pod identity → role

See [Topic 07 Module 46](../07_git_github_devops/46_aws_oidc_trust_policy_deep.md) for the trust-policy deep dive.

## 4. Regions, AZs, Edge

- **Region** — a geographic area (us-east-1, eu-west-1). Independent failure domain.
- **Availability Zone (AZ)** — datacenter cluster within a region. 3+ AZs per region. Independent power/network within a region.
- **Edge locations** — CloudFront PoPs (200+ globally).
- **Local Zones** — sub-region extensions (us-east-1-bos-1a in Boston).
- **Outposts** — AWS hardware in your data center.

DevOps rule: **multi-AZ by default** for prod workloads. Multi-region only when business requires it (cost + complexity).

## 5. VPC + networking essentials

A VPC is your private network in AWS. Default VPC exists per region; for serious work, create your own.

```
VPC: 10.0.0.0/16
├── Public Subnet (us-east-1a): 10.0.1.0/24    → has route to IGW
├── Public Subnet (us-east-1b): 10.0.2.0/24    → has route to IGW
├── Private Subnet (us-east-1a): 10.0.11.0/24  → routes via NAT GW
├── Private Subnet (us-east-1b): 10.0.12.0/24  → routes via NAT GW
└── Subnets per service tier (db, lb, app)
```

- **Internet Gateway (IGW)** — public subnets attach to this for inbound/outbound internet
- **NAT Gateway** — private subnets reach internet outbound only
- **VPC Endpoints (Gateway + Interface)** — reach AWS services privately (S3, ECR, SSM)
- **Security Groups** — stateful instance-level firewall
- **NACLs** — stateless subnet-level firewall (use sparingly)

See [Topic 04 Part B](../04_aws_for_ai_ml/) for the full networking depth.

## 6. CIDR blocks (the math you'll do)

`10.0.0.0/16` = 65,536 IPs. `/24` = 256 IPs. `/28` = 16 IPs.

VPC must be in RFC1918 ranges: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`. Don't use overlapping CIDRs across VPCs you'll peer.

## 7. EC2 essentials

- **Instance type families** — t (burstable, cheap), m (general), c (compute), r (memory), p/g (GPU)
- **Pricing models** — On-Demand, Spot (up to 90% off, can be reclaimed), Reserved, Savings Plans
- **AMI** — Amazon Machine Image; Ubuntu/Amazon Linux 2023/RHEL
- **Key Pairs** — SSH keys for initial access (prefer Session Manager + SSM for prod)
- **Instance Profile** — IAM role attached to instance (so app code uses temporary creds)
- **User Data** — cloud-init script on first boot
- **IMDSv2** — instance metadata service; v2 is token-required, mandatory for new instances (mitigates SSRF, Capital One 2019 breach root cause)

## 8. AWS CLI essentials

```bash
aws configure                          # legacy: stores ~/.aws/credentials
aws configure sso                      # modern: SSO-based
aws sts get-caller-identity            # who am I
aws s3 ls                              # list buckets
aws s3 cp local.txt s3://bucket/        # upload
aws ec2 describe-instances --query "Reservations[].Instances[].[InstanceId,State.Name,PublicIpAddress]" --output table
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 1234.dkr.ecr.us-east-1.amazonaws.com
```

CLI v2 is current (v1 EOL'd 2024). Use `--profile` to switch between roles/accounts.

## 9. ECR (Elastic Container Registry)

- **Private** by default; public registry separate (public.ecr.aws).
- IAM-controlled push/pull.
- Image scanning: basic (Clair-based) + enhanced (Inspector, paid).
- Lifecycle policies for cleanup.
- Cross-region replication.
- ECR Public for OSS images.

Authenticate via short-lived token:
```bash
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  1234.dkr.ecr.us-east-1.amazonaws.com
```

## 10. Container services on AWS — the decision matrix

| Service | When |
|---|---|
| **ECS on EC2** | Container orchestration without K8s complexity; AWS-native; deep in 2026 still |
| **ECS on Fargate** | Serverless containers; no node management |
| **EKS** | Kubernetes; cross-cloud portability; ecosystem |
| **App Runner** | Simple PaaS for containers |
| **Lambda (Container image)** | Function as image, max 15min runtime |
| **Batch** | Long-running batch jobs |

Capital One: EKS-dominant for ML serving (KServe), some ECS for legacy.

## 11. AWS + Terraform (preview — full in Module 13)

```hcl
provider "aws" {
  region = "us-east-1"
}

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags = { Name = "main" }
}

resource "aws_instance" "web" {
  ami           = "ami-0c7217cdde317cfec"  # Ubuntu 24.04 us-east-1
  instance_type = "t3.micro"
  user_data     = file("bootstrap.sh")
}
```

## 12. Quick self-check

1. What's the difference between a Security Group and a NACL?
2. Why is IMDSv2 strictly required in 2026?
3. What's the modern alternative to AWS access keys for CI/CD authentication?
4. Name three reasons to prefer Session Manager over SSH for EC2 access.
5. What's the difference between EKS and ECS?

(Answers: SG is stateful + instance-level, NACL is stateless + subnet-level; mitigates SSRF→credential theft (Capital One 2019); OIDC + IAM Role; no inbound ports, IAM-based auth, fully audited via CloudTrail; EKS is Kubernetes — portable, ecosystem; ECS is AWS-native — simpler ops, locked to AWS.)
