# Module 3 — Regions, Availability Zones, Edge

> **What this is:** AWS's global infrastructure — partitions, regions, AZs, Local Zones, Outposts, Wavelength, and edge — with the regional quirks that bite ML workloads.
>
> **Why it matters:** SageMaker, Bedrock, Trainium, and HyperPod availability varies sharply by region. You will design multi-region active-active for tier-0 systems, deal with Bedrock model-access requests per region/account/model, and explain the difference between an AZ letter and an AZ ID to people who think they're the same.

---

## 1. Partitions — the highest boundary

AWS is divided into **partitions** — entirely separate trust roots and ARN namespaces:

| Partition | ARN prefix | What it is |
|---|---|---|
| `aws` | `arn:aws:...` | Commercial, 34 regions as of 2026-05 |
| `aws-us-gov` | `arn:aws-us-gov:...` | GovCloud (West, East). FedRAMP High, ITAR. |
| `aws-cn` | `arn:aws-cn:...` | China (Beijing operated by Sinnet, Ningxia by NWCD). Separate console, separate accounts. |
| `aws-iso`, `aws-iso-b`, `aws-isof` | (restricted) | Air-gapped for U.S. intelligence community |

You **cannot** federate identity, peer VPCs, or replicate S3 across partitions. An account in `aws` is a different universe from an account in `aws-us-gov`.

## 2. Regions and AZs

A **Region** is a geographic area with **3–6 Availability Zones**.

An **AZ** is one or more discrete data centers with independent power, cooling, and networking, interconnected via sub-millisecond fiber to the others in the region.

**AZs are randomized per account.** `us-east-1a` for your account may be a different physical AZ than `us-east-1a` for someone else's. Use **AZ IDs** (`use1-az1`, `use1-az2`, etc.) when correlating across accounts (e.g., when peering or sharing subnets via RAM).

```bash
aws ec2 describe-availability-zones --query "AvailabilityZones[].[ZoneName,ZoneId]"
# Returns the mapping for your account
```

## 3. Edge, Local Zones, Outposts, Wavelength

- **Edge locations** — 600+ PoPs for CloudFront, Route 53, Global Accelerator, WAF.
- **Local Zones** — single-AZ extensions of a parent region in metro areas (LA, Boston, Chicago, Phoenix, Las Vegas, Atlanta, etc.). Sub-10 ms latency to specific cities. Limited service catalog: EC2, EBS, VPC, ELB, RDS, ECS/EKS data plane. Use for low-latency to a metro that's not a region.
- **AWS Outposts** — AWS-managed hardware shipped to your data center. Two flavors: Outposts rack (42U) and Outposts servers (1U/2U). Same APIs as the region; control plane stays in AWS, data plane is on-prem. Used by banks for trading-floor latency and data-residency that even GovCloud can't satisfy.
- **AWS Wavelength** — EC2/EKS embedded in carrier 5G networks (Verizon, KDDI, Vodafone). Niche for ML inference at carrier edge (AR/VR, V2X).

## 4. Regional service quirks (the ML-specific ones)

This is where engineers actually get burned:

- **Bedrock model availability** varies sharply by region. Anthropic Claude Opus is in `us-east-1`, `us-west-2`, `eu-central-1`, etc. — but not all models everywhere. **Cross-region inference profiles** (GA 2024-08) bridge the gap by routing requests to whichever region currently has capacity for that model.
- **SageMaker HyperPod**, **Trainium / Trainium2**, **P5/P5e**, and **Capacity Blocks** are only in select regions. Plan training-cluster location early.
- **IAM is global** but its data plane has regional replicas. STS, ACM, Route 53 have regional/global modes — be deliberate.
- **CloudFront, WAF Global, Shield** are edge-attached; their config lives in `us-east-1` even when serving globally.
- **us-east-1** has the broadest service set *and* the worst blast radius — the December 2021 outage took down half the internet. Banks treat `us-east-1` as a hot region but actively design for `us-east-2` and `us-west-2` failover.
- **Opt-in regions** (Hong Kong, Bahrain, Cape Town, Milan, Jakarta, UAE, Hyderabad, Zurich, Spain, Tel Aviv, Melbourne, Calgary, Malaysia, Thailand, Mexico, Taipei) must be explicitly enabled per account. In a regulated org these are SCP-controlled.

## 5. VPC endpoints and PrivateLink (preview)

(Full treatment in Module 8.)

- **Gateway VPC endpoints** — free; only S3 and DynamoDB. Routed via prefix list in the route table.
- **Interface VPC endpoints** — ENI-based. ~$0.01/hr per endpoint per AZ + $0.01/GB. The currency of "S3/KMS/Bedrock/SageMaker traffic must stay on AWS backbone."
- **Endpoint policies** + `aws:PrincipalOrgID` — the post-2019 baseline: lock down endpoint usage to org-owned principals only.

## 6. 2024–2026 changes worth knowing

- **New regions GA**: Malaysia (`ap-southeast-5`) 2024-08, Mexico (`mx-central-1`) 2025-01, Thailand (`ap-southeast-7`) 2025-01, Taipei (`ap-east-2`) GA 2025.
- **Bedrock cross-region inference profiles** GA 2024-08.
- **Cross-region PrivateLink** GA 2024-06 — interface endpoints can target services in another region without VPC peering.
- **Outposts servers** broader instance type support.

## 7. Pitfalls and anti-patterns

- Treating **AZ letter as identity** across accounts. Use AZ IDs.
- Assuming a service is in every region. **Always check the regional services table.**
- Forgetting Bedrock model access is **per-region, per-account, per-model**. Capital One's account-vending pipeline has to handle these requests programmatically.
- Running production in **only us-east-1**.
- Forgetting that CloudFront/WAF Global config is "global" but anchored in `us-east-1`.
- Pinning data residency to a partition you can't actually use (a Brazilian bank can't suddenly use `aws-cn`).

## 8. Capital One lens

Capital One operates primarily in **us-east-1**, **us-east-2**, **us-west-2**. Multi-AZ across 3 AZs for every prod workload, **active-active across regions** for tier-0 systems.

Heavy PrivateLink usage — S3, KMS, Bedrock, SageMaker runtime endpoints all flow over PrivateLink with endpoint policies pinning `aws:PrincipalOrgID`.

SCPs deny `ec2:RunInstances` outside the allowed three regions, with narrow Bedrock-only exceptions when a model is region-locked. They likely manage Bedrock model-access requests via automation since they're in production with many model variants.

## 9. Sanity check

1. Why is `us-east-1a` not the same as another account's `us-east-1a`?
2. Name three ML services whose regional availability you'd check before designing a new training pipeline.
3. What's the difference between Local Zones and Outposts?
4. Why is `us-east-1` simultaneously the most-used and most-feared region?
5. What does Bedrock cross-region inference profiles solve?

## 10. Cross-references

- **Module 4** — billing, where partition + region differences manifest in invoices
- **Module 8** — VPC peering, Transit Gateway, PrivateLink (incl. cross-region)
- **Module 30** — EC2 instance types per region (P5e/Trainium availability)
- **Module 36, 40** — SageMaker training, HyperPod regional considerations
- **Module 42** — Bedrock model regional availability

## Primary sources

- AWS Global Infrastructure page (live)
- Research report: [`02_aws_foundations.md`](../../research_inputs/04_aws_for_ai_ml/02_aws_foundations.md)
