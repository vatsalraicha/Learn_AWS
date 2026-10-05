# Module 6 — VPC Deep

> **What this is:** the AWS Virtual Private Cloud in production detail — subnets by routing intent, IGW vs NAT GW, VPC endpoints (Gateway + Interface), IPAM, shared VPCs via RAM.
>
> **Why it matters:** the VPC is the boundary every workload sits in. Capital One workload VPCs are **isolated** (no IGW) by default — getting AWS service access to that workload means VPC endpoints and PrivateLink. The PrivateLink endpoint bill alone is a non-trivial line item at scale.
>
> **Cert mapping:** SAA-C03 (Resilient + Secure 56%), SAP-C02 (heavily), SCS-C03 (network controls), MLA-C01 (Domain 4).

---

## 1. VPC anatomy

A **VPC** is a logically isolated virtual network in **one AWS region**. It has:

- One or more **CIDR blocks** (primary + up to 4 secondary IPv4; plus an Amazon-provided `/56` IPv6 if enabled).
- **Subnets** — one per AZ; classification (public/private/isolated) is by route table, **not by AWS itself**.
- **Route tables**, **Internet Gateway**, **NAT Gateway(s)**, **VPC endpoints**, **DHCP options set**, **Network ACLs**, **Security Groups**.
- **Elastic Network Interfaces (ENIs)** — virtual NICs attached to EC2, Lambda-in-VPC, SageMaker, RDS, ECS task, etc.

**Default VPC:** every AWS account gets one per region with a `172.31.0.0/16` block, public subnets in each AZ, and an IGW. **Capital One disables/deletes default VPCs via SCP** — production workloads never sit in them.

## 2. Subnet classes (by routing intent)

There are three patterns. None of them are AWS objects — they're emergent from the route table:

| Class | Default route | Hosts |
|---|---|---|
| **Public** | `0.0.0.0/0 → IGW` | NLBs, ALBs, NAT GWs, bastions |
| **Private (with egress)** | `0.0.0.0/0 → NAT GW` | App servers, SageMaker training, EKS nodes that pull container images from the internet |
| **Isolated** | no default route | RDS, DynamoDB-via-endpoint, anything regulated. **Capital One's default for PCI/PII workloads.** |

## 3. IPv4/IPv6 dual stack

A VPC can have an Amazon-provided `/56` IPv6 block. Every IPv6 address is **globally routable** — there is no NAT for IPv6 in AWS.

To make a subnet "private" for IPv6, use an **Egress-Only Internet Gateway (EIGW)** — stateful, one-way like a NAT but **free**. The IPv6 future-proof equivalent of a NAT GW.

## 4. NAT Gateway vs NAT Instance

**NAT Gateway** (managed):
- Scales to 45 Gbps and 1M packets/sec **per AZ**.
- Deploy **one per AZ** to avoid cross-AZ data charges.
- $0.045/hr (~$32/mo per GW) **plus $0.045/GB processed**.
- **The data-processing charge is what blows up bills** — 1 TB/month of egress costs $45 just in processing on top of the $32 hourly.

**NAT Instance** (EC2 you manage):
- Cheaper at tiny scale.
- No managed failover, capped by instance NIC bandwidth.
- Use only if you need a special routing trick (source-NAT to a fixed allowlisted IP for a partner) or at very small scale.

## 5. VPC endpoints — the regulated-cloud essential

VPC endpoints let instances reach AWS service APIs **without leaving the AWS network** (no IGW, no NAT, no internet).

### Gateway endpoints

- **Free** ✓
- Only for **S3 and DynamoDB**.
- Implemented as a prefix-list route (e.g., `pl-63a5400a` for S3) in the route table. Traffic uses the existing ENI. **No DNS magic** — you target the regional S3 hostname normally.

### Interface endpoints (PrivateLink)

- **ENI inserted into your subnets**, given a private IP, hooked to the service via PrivateLink.
- Works for ~150+ AWS services: SageMaker API/runtime, Bedrock, ECR API/dkr, STS, KMS, Secrets Manager, CloudWatch Logs, SSM, etc.
- **$0.01/hr per endpoint per AZ + $0.01/GB processed.**
- **Bill math:** 3 AZs × 30 endpoints × $0.01/hr × 730h ≈ **$657/mo before any traffic**.

**DNS behavior:** Interface endpoints support "Private DNS" — when enabled, the public DNS name (`sagemaker.us-east-1.amazonaws.com`) resolves to private endpoint IPs inside your VPC. This is what makes SDK code work unmodified.

### Endpoint policies

Endpoint policies let you scope what's accessible via the endpoint. The post-2019 baseline:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": "*",
    "Action": "*",
    "Resource": "*",
    "Condition": {
      "StringEquals": {
        "aws:PrincipalOrgID": "o-xxxxxxxxxx"
      }
    }
  }]
}
```

This single statement enforces "only my org's principals can use this endpoint to reach S3." The Capital One 2019 breach exfiltrator's principal was outside the org — this would have blocked it.

## 6. IPAM and shared VPCs via RAM

**IPAM (IP Address Manager)** — a service for planning, allocating, and auditing CIDRs across accounts and regions. Hierarchical pools (top-level → region → environment → account). Free tier; advanced tier ($0.0001/IP/hr ≈ $0.072/IP/mo) adds compliance tracking and IPv6 BYOIP.

**RAM (Resource Access Manager)** — share a VPC's subnets with other accounts in your Organization. The owner manages networking; participants launch resources.

**Capital One pattern:** one **network account** owns shared VPCs, dozens of workload accounts launch SageMaker/EKS into them. This centralizes network design while keeping workloads in their own accounts.

## 7. Pitfalls and anti-patterns

- **Forgetting the per-AZ Interface endpoint charge** → bill shock.
- **Single-AZ NAT GW with multi-AZ workloads** → cross-AZ data-transfer charges ($0.01/GB each way) silently eat the savings.
- **Secondary CIDR overlap** with a peered VPC or on-prem network → invisible blackhole.
- **Private DNS enabled** on an Interface endpoint **and** a private hosted zone with the same name → resolution conflict.
- **Using NAT GW when a VPC Gateway endpoint to S3 would do** — S3 traffic over NAT costs $0.045/GB; over the gateway endpoint, free.
- **Not having an isolated subnet tier** at all — every workload ends up "private with NAT egress" and the bill reflects it.

## 8. Capital One lens

- **Hub-and-spoke**: a centralized "network" account owns transit-VPCs and TGW attachments.
- All workload VPCs are **isolated** (no IGW). Egress (if any) goes via a **centralized egress VPC** with proxies, AWS Network Firewall, and per-domain allow-listing.
- Every AWS service call goes through **PrivateLink Interface endpoints**, often centralized via private hosted zones in Route 53 and shared across accounts.
- **IPAM enforces non-overlapping `/16`s per business unit** — critical at 600+ accounts.
- The "no NAT GW in PCI zones" rule means SageMaker training jobs in PCI workloads need pre-staged container images in ECR with an Interface endpoint for `ecr.dkr` and `ecr.api`.

## 9. Sanity check

1. What makes a subnet "public" vs "private" vs "isolated"?
2. When would you use a Gateway endpoint vs an Interface endpoint?
3. Why is the data-processing charge on NAT GW often larger than the hourly charge?
4. Walk through the math: 3 AZs, 30 Interface endpoints, no traffic. What's the monthly cost?
5. What's the role of `aws:PrincipalOrgID` in an endpoint policy, and how does it relate to the 2019 breach?

## 10. Cross-references

- **Module 5** — primer, prerequisite for this module
- **Module 7** — SGs, NACLs, Flow Logs
- **Module 8** — Transit Gateway, PrivateLink for inter-VPC/hybrid
- **Module 41** — SageMaker VPC mode + no-internet egress
- **Module 47** — Databricks on AWS BYO VPC

## Primary sources

- [`VPC_Connectivity_Options.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/VPC_Connectivity_Options.pdf)
- Research report: [`03_networking.md`](../../research_inputs/04_aws_for_ai_ml/03_networking.md)
