# Module 5 — Networking primer for ML engineers (assume zero)

> **What this is:** networking from first principles, no AWS. CIDR, subnets, routes, NAT, DNS, TCP/UDP, ports, firewalls, load balancers. The substrate everything else in Part B sits on.
>
> **Why it matters:** every "my SageMaker notebook can't reach S3", "the endpoint returns 504 only from prod", and "why is our NAT bill $14k/month?" is a networking ticket in disguise. At Capital One — where every workload runs inside a regulated VPC with no Internet Gateway egress — networking *is* the system, not an optional layer.
>
> **Pre-req:** none. This module exists for ML engineers who have never had to think about this.

---

## 1. IP addresses and CIDR

An **IPv4 address** is 32 bits, written as four 8-bit octets: `10.20.30.40`. Each octet is 0-255.

A **CIDR block** (Classless Inter-Domain Routing) is `address/prefix-length`, where the prefix is the number of leading bits fixed for the network. The remaining bits are host bits.

| CIDR | Host bits | Total addresses | AWS usable |
|---|---|---|---|
| `/16` | 16 | 65,536 | 65,531 |
| `/20` | 12 | 4,096 | 4,091 |
| `/24` | 8 | 256 | 251 |
| `/28` | 4 | 16 | 11 (smallest VPC subnet AWS allows) |

**Rule of thumb:** every step smaller in prefix length doubles the size. `/23` is 2× `/24`.

**AWS reserves 5 addresses per subnet** (a frequent gotcha):
- `.0` — network address
- `.1` — VPC router
- `.2` — DNS (Amazon-provided)
- `.3` — future use (reserved)
- `.255` — broadcast

So a `/28` subnet has 16 - 5 = **11 usable IPs**. This bites you when launching SageMaker training clusters: an 8-node distributed job + Studio app ENI + a couple of VPC endpoint ENIs and you're out.

## 2. RFC 1918 private address space

Never routable on the public internet — these are the building blocks of every private network:

| Range | Size | Common usage |
|---|---|---|
| `10.0.0.0/8` | 16.7 M | Enterprise default; large orgs subdivide |
| `172.16.0.0/12` | 1 M | Docker default; **avoid** colliding |
| `192.168.0.0/16` | 65 K | Home networks; small offices |

**RFC 6598** `100.64.0.0/10` is "carrier-grade NAT" space — AWS uses it for some service-managed ENIs (e.g., EKS pod IPs in some CNI modes).

## 3. Subnets, route tables, and gateways

A **subnet** is a slice of a VPC's CIDR, bound to exactly one Availability Zone.

A **route table** is a list of `destination CIDR → target` rules consulted **longest-prefix-match first**. Every subnet has exactly one route table (the main one if not explicitly associated).

**Gateways:**

- **Internet Gateway (IGW)** — a horizontally scaled VPC component that lets resources with public IPs reach the internet *and* receive return traffic. A subnet is "public" iff its route table has `0.0.0.0/0 → igw-...`.
- **NAT Gateway** — AWS-managed Network Address Translation. Instances in **private subnets** send egress to the NAT GW, which rewrites the source IP to its own (public) Elastic IP. Return packets come back to the NAT and are de-translated. Stateful, one-way (no inbound from internet).
- **NAT Instance** — legacy: an EC2 instance you manage doing the same thing. Useful only for tiny scale or special routing tricks.
- **Egress-Only Internet Gateway (EIGW)** — IPv6 equivalent of NAT GW. Stateful, one-way, free.

## 4. DNS basics

DNS turns names into IPs. Record types you must know:

| Record | What it does |
|---|---|
| **A** | Name → IPv4. `api.example.com → 52.1.2.3` |
| **AAAA** | Name → IPv6 |
| **CNAME** | Name → another name. Cannot exist at zone apex |
| **MX** | Mail exchanger |
| **TXT** | Arbitrary strings (SPF, DKIM, domain verification) |
| **NS** | Delegates a zone to authoritative name servers |
| **SOA** | Start-of-authority metadata |
| **PTR** | Reverse DNS (IP → name); rare in cloud-native apps |

Route 53 invented **ALIAS** records to fix the "CNAME at zone apex" problem for AWS-managed targets (ELB, CloudFront, S3 website).

**TTL** (Time-To-Live) controls caching duration. Short TTLs (60s) for failover; long TTLs (24h) for stable infra.

## 5. TCP vs UDP, ports, ephemeral ports

| | TCP | UDP |
|---|---|---|
| Connection model | Connection-oriented | Connectionless |
| Reliability | Reliable, ordered | Unreliable, no ordering |
| Overhead | Three-way handshake (SYN/SYN-ACK/ACK) | Minimal |
| Use cases | HTTP, gRPC, databases, SSH | DNS, QUIC (HTTP/3), real-time media |

A **port** is a 16-bit number (0-65535). Well-known: `22` SSH, `80` HTTP, `443` HTTPS, `53` DNS, `5432` PostgreSQL, `3306` MySQL, `6443` Kubernetes API.

**Ephemeral ports** — when a client connects out, the kernel picks a random source port from a range (Linux 32768-60999, Windows 49152-65535). **Return traffic must be allowed back on that ephemeral port.** This is *the* most common NACL-mistake source.

## 6. Firewalls: stateful vs stateless

**Stateful** firewalls remember connections. If you allow outbound, the response is automatically allowed. AWS Security Groups, modern host firewalls.

**Stateless** firewalls evaluate every packet independently. You must explicitly allow both directions, including ephemeral return ports. AWS NACLs.

This single distinction explains why "I opened port 443 outbound" doesn't work on a NACL — you also need to allow inbound on the ephemeral port range.

## 7. Load balancers: L4 vs L7

The **OSI layer** they operate on:

| | L4 (transport) | L7 (application) |
|---|---|---|
| Sees | IP + port | HTTP headers, paths, cookies, gRPC frames |
| Speed | Fast, simple | Slightly higher latency |
| Client IP preservation | Easy | Requires X-Forwarded-For or PROXY protocol |
| Examples | AWS NLB | AWS ALB |
| Capabilities | TCP/UDP passthrough | Path/host/header routing, JWT auth, WAF |

## 8. Public vs private IPs, Elastic IPs

A **public IP** is reachable from the internet (subject to firewalls). A **private IP** is RFC 1918 — only routable within your VPC or peered networks.

An **Elastic IP (EIP)** is a static public IPv4 you own and can reassign. AWS now charges **$0.005/hr (~$3.60/mo) for every public IPv4** (in use *or* idle), since Feb 2024 — a meaningful line item at fleet scale.

## 9. Common pitfalls (right now, before you touch AWS)

- **Overlapping CIDRs** between VPCs make peering and TGW attachments impossible. Centralize allocations with IPAM.
- **`/28` subnet for a training cluster**: 11 IPs is not enough for an 8-node distributed job once you count ENIs, Studio apps, and VPC endpoints.
- **Forgetting the AWS-reserved 5 addresses** when sizing subnets.
- **Confusing "no internet access" with "no AWS service access"** — S3 needs *routing*, which a VPC endpoint provides without an IGW.
- **Confusing CNAME and ALIAS** at zone apex.
- **NACL ephemeral-port mistake** — opening 443 outbound but forgetting to allow 32768-60999 inbound on the return path.

## 10. Sanity check

1. How many usable IPs does a `/24` AWS subnet have, and why?
2. Which RFC 1918 range is the Docker default, and why does that matter?
3. What's the difference between an IGW and a NAT GW?
4. Stateful vs stateless firewall — which one needs you to allow ephemeral return ports explicitly?
5. Why can't you have a CNAME at zone apex, and what does AWS use as a workaround?

## 11. Cross-references

- **Module 6** — VPC, where these primitives become AWS objects
- **Module 7** — SG and NACL in AWS detail
- **Module 8** — multi-VPC connectivity (peering, TGW, PrivateLink, DX, VPN)
- **Module 9** — DNS, load balancing, edge — Route 53, ALB/NLB/GWLB, CloudFront, WAF, Shield

## Primary sources

- [`VPC_Connectivity_Options.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/VPC_Connectivity_Options.pdf)
- Research report: [`03_networking.md`](../../research_inputs/04_aws_for_ai_ml/03_networking.md)
- RFC 1918, RFC 6598 (Internet Engineering Task Force)
