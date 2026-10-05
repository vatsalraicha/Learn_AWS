# Module 8 — Multi-VPC and Hybrid Connectivity

> **What this is:** VPC Peering, Transit Gateway, PrivateLink (for your own services), Direct Connect, VPN, Cloud WAN. The connectivity layer that links VPCs to each other and to on-prem.
>
> **Why it matters:** Capital One operates 600+ accounts under a hub-and-spoke TGW topology with DX into multiple colos. Every architecture review asks how a new workload integrates — you need to fluently distinguish "TGW route" from "PrivateLink service" from "VPC peering."

---

## 1. VPC Peering

- 1:1 connection between two VPCs.
- Region-local or inter-region.
- **Non-transitive** — A↔B and B↔C does *not* give A↔C.
- Cheap (only data-transfer charges); CIDRs must not overlap.
- Doesn't scale past ~10 VPCs — mesh becomes O(n²) and the route-table maintenance becomes painful.

**Use case:** two VPCs that need to talk to each other and that's it. Beyond two, switch to Transit Gateway.

## 2. Transit Gateway (TGW)

The hub-and-spoke replacement for peering meshes.

- Attaches **VPCs, VPNs, Direct Connect Gateways, peer TGWs (cross-region), Connect attachments** (SD-WAN/GRE).
- **Route tables** on the TGW segment traffic. Pattern: one RT per environment — "prod can talk to prod-shared-services, not to dev."
- Quotas: ~5,000 attachments per TGW; 10,000 routes per RT.
- **Pricing: $0.05/hr per attachment** (~$36/mo each) + **$0.02/GB processed**. A 100-VPC TGW: ~$3,600/mo before traffic.

**TGW route table pattern (typical):**

```
prod-rt:
  attached: prod-card-ml, prod-card-app, prod-shared-services
  prod-card-ml ↔ prod-shared-services  ✓
  prod-card-ml ↔ prod-card-app          ✓
  prod-card-ml ↔ dev-*                  ✗ (no route)
```

## 3. AWS PrivateLink (for your own services)

Built on the same plumbing as Interface endpoints, but for **your own services**:

1. You publish a service backed by an **NLB** or **GWLB**.
2. Consumers create an **Interface endpoint** into your service from their own VPCs.
3. One-directional (consumer → provider only).
4. **No CIDR overlap concerns** since the consumer sees only an ENI IP in their own VPC.

**Capital One pattern:** every shared internal service (model registry, feature store, internal LLM gateway, central tokenization service like Databolt) is exposed via PrivateLink rather than via TGW reachability. **Least-privilege at the L4 level** — each consumer is an explicit endpoint resource, easy to audit, easy to revoke.

This is the architect-grade insight: **TGW gives broad reachability between networks; PrivateLink gives narrow access to one specific service.** Use TGW for tiers that share resources broadly (e.g., shared monitoring); use PrivateLink for everything else.

## 4. Direct Connect (DX)

A **physical fiber circuit** from your DC/colo into an AWS DX location.

| Type | Description |
|---|---|
| **Dedicated connection** | Full 1/10/100 Gbps port; you own it |
| **Hosted connection** | Sub-port slice from an APN partner (50 Mbps to 25 Gbps) |

**Virtual Interfaces (VIFs):**
- **Private VIF** — one VPC (via VGW) or many (via DX Gateway → TGW).
- **Public VIF** — AWS public service endpoints (S3, etc.) without using the internet.
- **Transit VIF** — DX Gateway → Transit Gateway.

**Pricing:** port-hour + data-transfer-out (cheaper than internet egress, much cheaper at scale).

**Always pair with VPN backup.** A DX circuit is a single physical path and can fail.

## 5. Site-to-Site VPN and Client VPN

**Site-to-Site VPN:**
- IPsec tunnels (always two for redundancy) between an AWS VGW/TGW and a customer gateway (your firewall).
- Up to ~1.25 Gbps per tunnel.
- Often used as DX backup or for low-traffic remote sites.

**Client VPN:**
- Managed OpenVPN-based service for human users to reach VPCs.
- Mutual TLS + optionally federated auth.
- $0.10/hr per associated subnet + $0.05/hr per connected client.
- Used for engineers' workstation access to private VPCs.

## 6. Cloud WAN

AWS's "global network as a service": you define **network segments** (e.g., prod, dev, shared) in **policy JSON**; Cloud WAN provisions the underlying TGWs, peerings, and DX gateways across regions.

**The replacement for the hand-rolled "global TGW mesh."** Use when you have 4+ regions or want declarative segmentation across them.

## 7. TGW Network Manager

A monitoring/observability console for TGWs, Cloud WAN, DX, VPN. Topology view, CloudWatch metrics, events.

## 8. Asymmetric routing — the silent killer

A common failure mode in inspection architectures (Network Firewall, third-party appliances):

1. Packet enters via TGW route table A → reaches firewall → traffic returns.
2. Return packet hits a different TGW route table B → routed via a different path.
3. Stateful firewall in the path drops the asymmetric return.

**Fix:** TGW **appliance mode** for stateful inspection appliances. Forces symmetric routing through the same appliance.

## 9. Pricing pitfalls

- **TGW data charges count both directions** in many cross-account patterns.
- **VPC Peering is "free" within an AZ** but cross-AZ traffic still incurs $0.01/GB.
- **Adding a secondary CIDR** that overlaps with a peered VPC or on-prem → invisible blackhole.
- **Direct Connect without a VPN backup** → an outage waiting to happen.
- **Interface endpoint cost** scales with AZ count × endpoint count × hours.

## 10. Capital One lens

- **Hub-and-spoke TGW per region**, peered across regions, ideally evolving to **Cloud WAN**.
- **DX from multiple Capital One colos to AWS**, redundant per region, with S2S VPN backup.
- **Inter-account service access via PrivateLink** rather than open TGW routes — every service consumption is auditable as an endpoint resource.
- **Egress to internet** (where unavoidable, e.g., partner APIs) goes via a centralized egress VPC with **AWS Network Firewall + Squid proxy + domain allowlisting**.
- **Network Access Analyzer scopes** encode regulatory invariants ("PCI workloads cannot reach non-PCI workloads").

## 11. Sanity check

1. VPC Peering is non-transitive. What does that mean operationally, and when does it bite?
2. When would you pick PrivateLink for one of your own services over a TGW route?
3. What's the difference between a Private VIF and a Transit VIF on Direct Connect?
4. What is "TGW appliance mode" and what problem does it solve?
5. When does Cloud WAN start to make sense vs hand-rolled multi-region TGW?

## 12. Cross-references

- **Module 6** — VPC + Interface endpoints (PrivateLink for AWS services)
- **Module 7** — SGs/NACLs for traffic that crosses the connectivity layer
- **Module 47** — Databricks on AWS PrivateLink / Secure Cluster Connectivity
- **Module 50, 51** — Network Firewall as part of the security primitives

## Primary sources

- [`Hybrid_Connectivity.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/Hybrid_Connectivity.pdf)
- [`Building_Scalable_Secure_Multi_VPC_Network_Infrastructure.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/Building_Scalable_Secure_Multi_VPC_Network_Infrastructure.pdf)
- [`AWS_Transit_Gateway_Best_Practices.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/AWS_Transit_Gateway_Best_Practices.html)
- Research report: [`03_networking.md`](../../research_inputs/04_aws_for_ai_ml/03_networking.md)
