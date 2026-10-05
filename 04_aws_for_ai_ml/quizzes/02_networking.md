# Quiz 02 — Networking from Zero (Modules 5-9)

> Take cold (no peeking). Spend ~3 min per question.

---

## Recall

1. A `/24` subnet in a VPC — how many usable IPs? Why?
2. What is RFC 1918, and name the three IPv4 ranges.
3. Stateful vs stateless firewall — which is AWS Security Group and which is NACL?
4. What's the difference between an Internet Gateway and a NAT Gateway?
5. Name the 7 Route 53 routing policies.

## Apply

6. Design a VPC for a SageMaker training workload that **cannot reach the public internet** but needs S3, KMS, and ECR. What VPC endpoints do you create?
7. You have 3 AZs and want to deploy 30 Interface endpoints. What's the monthly cost before any data transfer? Show your math.
8. A NACL allows port 443 outbound but the application can't establish HTTPS to a remote server. What's the most likely cause?
9. Design a hub-and-spoke topology connecting 50 VPCs across 3 AWS regions. Which connectivity service do you choose, and what's the cost driver?

## Diagnose

10. A SageMaker notebook in VPC-only mode times out trying to read from an S3 bucket. Walk through the 7-step troubleshooting checklist.
11. You enabled Multi-Region Access Points on S3 but cross-region clients see ~50% of requests fail with timeouts. What might be wrong?
12. After a Multi-AZ Aurora failover, half your Lambda functions can't connect to the database. Why?

## Defend

13. When would you pick PrivateLink over a Transit Gateway route to expose an internal service to another account?
14. Argue for or against using a Gateway Load Balancer for stateful inspection of egress traffic.
15. You're being told "use NAT Gateway, it's simpler than VPC endpoints for S3." Argue against.

---

## Answers (don't peek until done)

1. **251 usable IPs.** AWS reserves 5 (.0 network, .1 router, .2 DNS, .3 future, .255 broadcast).
2. **RFC 1918** = private IP space: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`.
3. **SG = stateful** (return traffic auto-allowed). **NACL = stateless** (must allow both directions including ephemeral ports).
4. **IGW** allows bidirectional internet access for public IPs; **NAT GW** only allows egress, hides private IPs behind a public Elastic IP.
5. Simple, Weighted, Latency-based, Failover, Geolocation, Geoproximity, Multi-value answer.
6. **Gateway endpoint** for S3 (free). **Interface endpoints** for KMS, ECR.api, ECR.dkr, STS, CloudWatch Logs, SageMaker.api, SageMaker.runtime, Secrets Manager (if used).
7. 3 AZs × 30 endpoints × $0.01/hr × 730 hr/mo ≈ **$657/month** before any traffic.
8. **NACL is stateless**: allowing 443 outbound doesn't allow the return ephemeral ports inbound. Must also allow inbound 32768-60999 (Linux ephemeral range).
9. **Transit Gateway** in each region, peered across regions — or Cloud WAN for declarative segmentation. Cost driver: per-attachment hourly + per-GB processed.
10. (1) VPC-only mode? (2) Route table has `pl-s3 → vpce-...`? (3) Endpoint policy allows bucket+action? (4) Bucket policy allows role+VPC endpoint? (5) SG outbound 443 to S3 prefix list? (6) NACL allows 443 out and ephemeral in? (7) KMS Interface endpoint + key policy for SSE-KMS buckets.
11. MRAP requires Replication Time Control (RTC); without it, the replica may not have the object yet → 404, perceived as failure. Or the bucket replication didn't include pre-existing objects.
12. **Connection storm**: Lambda functions cached the old writer endpoint IP; after failover, the IP changed but cached DNS still routes to old. **RDS Proxy** in front would have absorbed this — Lambda invocations hit Proxy, Proxy maintains connection to current writer.
13. PrivateLink = least-privilege at L4 level. Each consumer has an explicit endpoint resource (auditable, revocable). TGW = broad reachability. Use PrivateLink when you want narrow access to one specific service rather than network-level connectivity.
14. **For** GWLB: transparent insertion of inspection appliances (Palo Alto, Suricata, Fortinet); centralized firewall fleet for egress filtering. **Against**: complexity, GENEVE encapsulation troubleshooting, additional pricing line item. The verdict depends on whether you need stateful inspection at L7.
15. NAT GW is $0.045/hr + $0.045/GB processed. **S3 traffic over NAT is expensive at scale** — a TB/month of egress costs $45 just in processing on top of the hourly. VPC Gateway endpoint for S3 is **free** and gives the same access pattern. Architecturally, NAT GW for S3 traffic is a cost-anti-pattern.
