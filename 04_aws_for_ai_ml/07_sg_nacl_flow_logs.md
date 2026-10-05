# Module 7 — Security Groups, NACLs, Flow Logs

> **What this is:** Security Groups (stateful, allow-only, attached to ENIs), NACLs (stateless, allow + deny, attached to subnets), and VPC Flow Logs — the L3/L4 access controls and the audit trail. Plus a 7-step "SageMaker can't reach S3" troubleshooting checklist worth memorizing.

---

## 1. Security Groups

- Attach to **ENIs** (so to EC2, RDS, Lambda-in-VPC, SageMaker, ALB, etc.).
- **Stateful**: return traffic is automatically allowed.
- **Allow-only**: there is **no deny rule**. Absence of allow = block.
- Rules: protocol + port range + source/destination (CIDR, another SG, or prefix list).
- Default outbound: allow all. Default inbound: deny all.
- **Can reference another SG as source** — powerful. "Allow port 5432 from `sg-app`" means anything wearing the app SG can hit Postgres, independent of IPs.
- Quota: 60 inbound + 60 outbound rules per SG; 5 SGs per ENI by default (raisable to 16).

**The SG-as-source pattern** is the cleanest tagging-by-membership control. You don't have to know CIDRs; you tag application servers with `sg-app` and database access is automatically scoped to anything wearing that SG.

## 2. NACLs (Network ACLs)

- Attach to **subnets** (not ENIs).
- **Stateless**: must allow both directions, **including ephemeral return ports**.
- Have **both Allow and Deny rules**, evaluated in **rule-number order**, first match wins.
- Default NACL: allow all both ways. Custom NACLs default to deny all.

**Use case** in regulated finance: a coarse extra layer. Common patterns:
- Block known-bad IP ranges at the subnet level.
- Enforce "this isolated subnet can never talk to the internet."
- Add a defense-in-depth layer where SGs are the primary control.

NACLs are blunt; you should not use them for fine-grained access control. That's SGs' job.

## 3. Evaluation order

For a packet entering an ENI from outside the subnet:

1. **NACL inbound** on subnet.
2. **SG inbound** on ENI.
3. (instance processes the request, generates response)
4. **SG outbound** on ENI (stateful — return is often pre-allowed by the inbound rule).
5. **NACL outbound** on subnet — **must allow ephemeral source port back**.

The NACL outbound step is where engineers get burned. "I allowed 443 inbound but the response is dropped" → you forgot to allow ephemeral ports (32768-60999 on Linux) on the way out.

## 4. The 7-step "SageMaker notebook can't reach S3" troubleshooting checklist

This is the single most-tested troubleshooting scenario in AWS exam prep, and it's something you will use weekly in production. Memorize the order:

1. **Is the notebook in VPC-only mode?** If so, there's no internet — must use a Gateway endpoint for S3.
2. **Does the notebook's subnet route table have `pl-s3 → vpce-...`?** Without this, S3 traffic has nowhere to go.
3. **Does the endpoint policy allow the bucket and action?** Endpoint policies override; "Allow * Resource *" is fine, but if it's locked down, S3 calls fail with AccessDenied.
4. **Does the bucket policy allow the role's principal from this VPC endpoint?** Use `aws:SourceVpce` condition to allow access from your endpoint specifically.
5. **SG outbound rule allowing HTTPS (443) to the S3 prefix list?**
6. **NACL on the subnet allowing 443 out and ephemeral 1024-65535 in?**
7. **KMS** — if bucket is SSE-KMS, you need a **KMS Interface endpoint** *and* a key policy that allows the role to decrypt.

When in doubt, run **Reachability Analyzer** between the notebook ENI and an S3-related resource (e.g., a test ENI), or check **CloudTrail** for AccessDenied with reason codes.

## 5. VPC Flow Logs

Per-ENI / per-subnet / per-VPC capture of accepted/rejected/all flows.

**Destinations:**
- CloudWatch Logs (expensive at scale).
- S3 (cost-sane choice for high-volume flow logs).
- Kinesis Data Firehose (when you want to fan to SIEM in real time).

**Formats:** default v2 (14 fields); custom format up to v7 — adds:
- `vpc-id`, `subnet-id`, `instance-id`
- `tcp-flags` (SYN/ACK/FIN/RST)
- `pkt-srcaddr` (for NAT'd flows — the *real* source IP)
- `flow-direction` (ingress/egress)
- `traffic-path` (through IGW, TGW, peering, VPN, ...)

**Captures:** src/dst IP+port, protocol, packets, bytes, start/end timestamps, action (ACCEPT/REJECT), log status.

**Does NOT capture:**
- Packet payload (use Traffic Mirroring for that).
- DNS lookups (use Route 53 Resolver query logs).
- Traffic to/from `169.254.169.254` (IMDS) and `169.254.169.123` (NTP) link-local addresses.
- Traffic between endpoints of certain managed services.

**Pricing:** data-ingestion charges on the destination. CloudWatch Logs ingestion is the killer at scale. **S3 + Athena is the cost-sane pattern** for finance.

## 6. Reachability Analyzer and Network Access Analyzer

**Reachability Analyzer**:
- "Can ENI A reach ENI B on port 443?"
- Static analysis of SGs, NACLs, route tables, peering, TGW.
- Pay-per-analysis (~$0.10).
- Great for spot debugging.

**Network Access Analyzer** (newer, more powerful):
- Declarative scopes: "no resource in the PCI VPC should be reachable from the internet."
- Continuous compliance checking against invariants.
- Premium feature, but cheap compared to a breach.
- Heavily used in regulated industries to encode PCI/HIPAA reachability invariants.

## 7. Pitfalls and anti-patterns

- **NACL ephemeral-port mistake** — opening 443 outbound on a NACL but forgetting to allow ephemeral inbound on the return path.
- **SGs as the only control with `0.0.0.0/0` source** on common ports — fine for an ALB facing the internet, terrible for anything internal.
- **Flow Logs to CloudWatch Logs at scale** — ingestion bill surprise. Use S3.
- **Using NACLs for fine-grained control** — they're not the right tool. Use SGs.
- **No flow logs at all** — your audit trail is incomplete; regulators will ask why.

## 8. Capital One lens

- **SGs are the primary control**; NACLs are coarse guard rails ("this subnet can never egress").
- **VPC Flow Logs to S3** with v5+ custom format, queried via Athena + QuickSight. Retained per regulatory schedule.
- **Network Access Analyzer scopes** encode regulatory invariants ("PCI DSS scoped resources cannot reach non-PCI scope" / "isolated subnets have no path to the internet").
- **Cloud Custodian policies** (their OSS) check SG rules nightly: e.g., flag any SG with `0.0.0.0/0` on ports other than 80/443 inbound to an ALB.

## 9. Sanity check

1. SG vs NACL — which is stateful, which is stateless, and which one always evaluates rules in numeric order?
2. Walk through the 7-step SageMaker → S3 checklist. Where does KMS come in?
3. What does Flow Logs **not** capture, and what should you use instead?
4. Why is CloudWatch Logs the wrong destination for VPC Flow Logs at scale?
5. What's the difference between Reachability Analyzer and Network Access Analyzer?

## 10. Cross-references

- **Module 6** — VPC, subnets, endpoints (prerequisite)
- **Module 8** — multi-VPC connectivity
- **Module 41** — SageMaker VPC mode + no-internet egress (where the 7-step checklist lives in production)
- **Module 50** — Security primitives (where Flow Logs feed into Security Hub findings)

## Primary sources

- [`VPC_Connectivity_Options.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/VPC_Connectivity_Options.pdf)
- Research report: [`03_networking.md`](../../research_inputs/04_aws_for_ai_ml/03_networking.md)
