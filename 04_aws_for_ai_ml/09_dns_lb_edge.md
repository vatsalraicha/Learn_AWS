# Module 9 — DNS, Load Balancing, and Edge

> **What this is:** Route 53 (hosted zones + 7 routing policies + Resolver), ALB/NLB/GWLB, CloudFront, Global Accelerator, WAF, Shield. The DNS + L7/L4 + CDN layer.
>
> **Why it matters:** every public-facing AI/ML surface (LLM API gateway, model inference endpoint, RAG-backed chatbot) sits behind some combination of Route 53 + ALB + WAF + Shield + CloudFront. Designing for DDoS resilience and global low-latency inference is part of the Sr Lead role.

---

## 1. Route 53

**Public hosted zones** — authoritative DNS for an internet domain.

**Private hosted zones** — DNS visible only inside associated VPCs. Critical for **PrivateLink override patterns** — you create a private hosted zone for `sagemaker.us-east-1.amazonaws.com` and override the AWS public DNS with your endpoint IPs.

### 7 routing policies

| Policy | When to use |
|---|---|
| **Simple** | One record set, no logic |
| **Weighted** | Traffic split by weights (canary deploys, A/B) |
| **Latency-based** | Route to the lowest-latency AWS region for the resolver |
| **Failover** | Primary/secondary with health-check-driven cutover |
| **Geolocation** | By user country/continent (sovereignty) |
| **Geoproximity** | By physical distance, with a "bias" knob (Traffic Flow only) |
| **Multi-value answer** | Up to 8 healthy records returned, basic DNS-level load distribution |

### Health checks

HTTP/HTTPS/TCP, can **chain** (calculated health checks combining sub-checks) and integrate with CloudWatch alarms.

### Route 53 Resolver

The DNS server every VPC gets at `VPC-base+2`. **Resolver endpoints** (inbound/outbound) let on-prem resolvers query VPC names and vice versa — essential for hybrid PrivateLink architectures.

**Resolver query logs** to S3/CWL/Firehose — fills the DNS blind spot in Flow Logs.

## 2. Application Load Balancer (ALB) — L7

- HTTP/HTTPS/gRPC/HTTP-2/WebSocket.
- Path-based, host-based, header-based, query-string-based routing.
- Targets: EC2, IP, Lambda, containers (via target groups).
- Native integration with **WAF**, **Cognito** (auth offload), **OIDC**.
- Sticky sessions via cookies.
- **Slow start mode** for new targets — gentle ramp.
- Pricing: hourly + **LCU** (Load Balancer Capacity Units, mix of new connections, active connections, processed bytes, rule evaluations).

## 3. Network Load Balancer (NLB) — L4

- TCP/UDP/TLS passthrough or termination.
- **Static IPs per AZ** (and Elastic IP support). Critical when partners need to allowlist your IPs.
- Ultra-low latency (~100 µs), tens of millions of concurrent flows.
- Preserves client source IP by default (instance mode).
- **The L4 layer underneath PrivateLink services.**

## 4. Gateway Load Balancer (GWLB)

- L3, uses **GENEVE encapsulation** (UDP port 6081).
- Inserts third-party network/security appliances (Palo Alto, Fortinet, Check Point, Aviatrix, Suricata) transparently into the traffic path.
- The "service-chain" primitive: route VPC egress → GWLB endpoint → appliance fleet → out.

## 5. CloudFront

- Global CDN, 600+ POPs.
- Origins: S3, ALB, EC2, MediaStore, custom HTTP.
- **Lambda@Edge** and **CloudFront Functions** for compute at the edge.
- **Origin Access Control (OAC)** locks S3 origins so the bucket is only reachable via CloudFront — table stakes for serving static SageMaker docs or generated assets.
- TLS termination, **HTTP/3**, Brotli, signed URLs/cookies.

**AI/ML angles:**
- Serve **Bedrock-generated assets** with edge caching.
- Host **LLM-app static frontends** (React/Next.js) close to users.
- Cache **embeddings or model artifacts** close to inference clients.

## 6. AWS Global Accelerator (GA)

**Anycast static IPs** in front of regional ALB/NLB/EC2 endpoints. Traffic enters the AWS backbone at the nearest edge POP and rides AWS's network the rest of the way — typically **30-60% faster** than public-internet routing for cross-region traffic.

Useful for a globally distributed inference API (e.g., a latency-critical fraud-decision model serving customer requests worldwide).

## 7. AWS WAF

Rule engine in front of ALB, CloudFront, API Gateway, AppSync, App Runner.

| Rule type | Use case |
|---|---|
| **Managed rule groups** | AWS, Marketplace (OWASP Top 10, account-takeover, bot control) |
| **Custom rules** | String match, regex, geo, IP set, size, SQLi/XSS |
| **Rate-based rules** | Count requests per 5-min sliding window per IP (or per header/cookie/JA3); essential against scrapers hitting your LLM endpoint |
| **Bot Control** | Paid managed rule group, behavioral bot detection |
| **CAPTCHA / Challenge** | Interactive challenges as an action |

**Pricing:** $5 / web ACL / mo + $1 / rule / mo + $0.60 per million requests + managed-rule subscriptions.

**Connection to the 2019 Capital One breach:** the attack started via an SSRF in a misconfigured WAF (ModSecurity, third-party at the time). Today's AWS WAF doesn't have that specific vulnerability, but the lesson is "WAF rules are a security boundary; treat them like code."

## 8. AWS Shield

- **Standard** — free, auto-enabled, defends against common L3/L4 DDoS.
- **Advanced** — $3,000/mo per organization (12-month commit) + data-transfer protection. Adds:
  - **DRT (DDoS Response Team)** 24/7
  - **Cost protection** for scaling during attacks
  - **L7 mitigation** when paired with WAF
  - **Attack analytics**
  - Shield Advanced metrics in CloudWatch

For regulated finance, Shield Advanced is table-stakes on any public-facing surface.

## 9. Pitfalls and anti-patterns

- **ALB sticky sessions** break stateless container scaling assumptions.
- **NLB source-IP preservation** requires `client_ip = on` in nginx / `proxy_protocol_v2` for some apps.
- **CloudFront and S3** default bucket policy collisions — always use OAC, never bucket-level "public" toggles.
- **WAF rate-based rules with too-broad keys** (IP only) miss authenticated abuse; use composite keys (IP + session token or IP + JA3 fingerprint).
- **Route 53 ALIAS vs CNAME confusion at zone apex** — use ALIAS for AWS-managed targets.
- **No CloudFront in front of S3 static assets** — CORS pain and no edge cache.

## 10. Capital One lens

- **ALBs internal-only inside VPC**, fronted by API Gateway (private) or by an on-prem F5/edge stack via DX.
- All **public-facing surfaces behind CloudFront + WAF + Shield Advanced**.
- **Route 53 private hosted zones** (resolver rules + endpoints) used to centralize PrivateLink DNS overrides across the org.
- **Global Accelerator** considered for multi-region active-active inference APIs (e.g., latency-critical fraud-decision models).
- Public-facing surfaces have **AWS Shield Advanced** + DRT engagement runbook.

## 11. Sanity check

1. Name the 7 Route 53 routing policies and one production use case for each.
2. ALB vs NLB — which preserves client IP by default, and which one underpins PrivateLink?
3. What is GENEVE encapsulation and what does GWLB use it for?
4. What does OAC do, and why is it critical for S3+CloudFront patterns?
5. When does Global Accelerator pay off vs just using CloudFront?

## 12. Cross-references

- **Module 8** — multi-VPC connectivity (PrivateLink is built on NLB)
- **Module 33** — EKS Ingress (often ALB Ingress Controller or ALBv2)
- **Module 42, 44** — Bedrock + self-hosted LLM endpoints (CDN + WAF patterns)
- **Module 50** — security primitives (WAF + Shield + Network Firewall combo)

## Primary sources

- [`Route53_Routing_Policies.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/Route53_Routing_Policies.html)
- [`ELB_Types_Comparison.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/ELB_Types_Comparison.html)
- Research report: [`03_networking.md`](../../research_inputs/04_aws_for_ai_ml/03_networking.md)
