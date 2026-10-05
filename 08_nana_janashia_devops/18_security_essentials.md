# 18 — Security Essentials + OWASP Top 10

## Why this module exists

DevSecOps presupposes baseline security literacy. This module is the 30-minute primer on attack categories, OWASP Top 10, and the layered-defense framing that everything in Part 2 will build on.

## 1. The cost of breaches (the business case for shift-left)

- **Average data breach cost 2024**: $4.88M (IBM Cost of a Data Breach Report 2024)
- **Capital One 2019 breach**: 100M+ records, $190M+ in fines + legal, plus reputation damage and SR 11-7 scrutiny
- **Equifax 2017 breach**: 147M records, ~$1.4B in costs over the following years
- **Stripe-grade scrutiny**: SOC 2 / PCI-DSS / FedRAMP / HIPAA — non-compliance blocks revenue, not just penalties

## 2. The CIA triad (the security north star)

- **Confidentiality** — only authorized parties see the data
- **Integrity** — data is not tampered with (signing, hashing, checksums)
- **Availability** — the system is up when needed (DDoS protection, redundancy)

Add three more (the AAA/non-rep additions):
- **Authentication** — proving who you are
- **Authorization** — what you can do
- **Non-repudiation** — proving who did what

## 3. Attack categories at a glance

| Category | Example |
|---|---|
| **Injection** | SQL injection, command injection, LDAP injection |
| **XSS** (Cross-site scripting) | Reflected, stored, DOM-based |
| **CSRF** | Forge requests using user's session |
| **SSRF** (Server-side request forgery) | Make the server fetch URLs you choose — **Capital One 2019 root cause** |
| **Authentication bypass** | Weak passwords, MFA bypass, session hijacking |
| **Privilege escalation** | Lateral movement after initial foothold |
| **DoS / DDoS** | Volumetric or app-layer flooding |
| **Supply chain** | Compromised dependencies (SolarWinds 2020, xz utils 2024) |
| **Insider threat** | Authorized user misusing access |
| **Physical** | Datacenter breach, stolen laptop |
| **Social engineering** | Phishing, vishing, business email compromise |

## 4. OWASP Top 10 (2021 — current, with 2025 update in flight)

| # | Risk | Defense |
|---|---|---|
| **A01** | **Broken Access Control** | Authorization checks server-side, deny-by-default, RBAC |
| **A02** | **Cryptographic Failures** | TLS everywhere, no weak ciphers, no plaintext secrets |
| **A03** | **Injection** | Parameterized queries, input validation, output encoding |
| **A04** | **Insecure Design** | Threat modeling, secure-by-default architecture |
| **A05** | **Security Misconfiguration** | Hardening baselines, no defaults, no debug in prod |
| **A06** | **Vulnerable + Outdated Components** | SCA, Dependabot, patch SLAs |
| **A07** | **Identification + Authentication Failures** | MFA, strong session mgmt, no credential stuffing |
| **A08** | **Software + Data Integrity Failures** | Signed artifacts (Cosign), SLSA, CI integrity |
| **A09** | **Security Logging + Monitoring Failures** | Centralized logs, SIEM, alerting |
| **A10** | **SSRF** | Allowlist outbound, no metadata-service access from app |

The 2025 draft (not yet finalized as of 2026-05) reportedly raises Insecure Design and Supply Chain Integrity higher.

## 5. CWE Top 25 (MITRE's complement)

Where OWASP Top 10 is web-focused, **CWE Top 25 Most Dangerous Software Weaknesses** is software-wide and updated annually. Cross-references between the two:
- CWE-79 (XSS) ↔ OWASP A03
- CWE-89 (SQL injection) ↔ OWASP A03
- CWE-787 (Out-of-bounds write) — not in OWASP but high in CWE
- CWE-918 (SSRF) ↔ OWASP A10

DefectDojo (Module 21) imports scanner reports and maps findings to CWE for normalized tracking.

## 6. Defense in layers (the onion model)

```
┌──────────────────────────────────────────────────────────┐
│  Network                                                 │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Perimeter                                          │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │  Host                                          │  │  │
│  │  │  ┌──────────────────────────────────────────┐  │  │  │
│  │  │  │  Application                              │  │  │  │
│  │  │  │  ┌──────────────────────────────────────┐  │  │  │  │
│  │  │  │  │  Data                                  │  │  │  │  │
│  │  │  │  └──────────────────────────────────────┘  │  │  │  │
│  │  │  └──────────────────────────────────────────┘  │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

Each layer has its own controls:
- **Network**: VPC, NACL, NetworkPolicy, segmentation
- **Perimeter**: WAF, rate limiting, IP allowlists, DDoS
- **Host**: hardened OS, EDR, FIM (file integrity monitoring)
- **Application**: input validation, output encoding, AuthN/AuthZ
- **Data**: encryption at rest + transit, tokenization (Capital One: Databolt), key rotation

Defense-in-depth: assume any one layer will fail; the next must catch it.

## 7. Threat modeling — STRIDE + PASTA + LINDDUN

Threat modeling is "think like an attacker before you ship." Frameworks:

- **STRIDE** (Microsoft, oldest): Spoofing, Tampering, Repudiation, Info disclosure, DoS, Elevation of privilege
- **PASTA** (Process for Attack Simulation and Threat Analysis) — risk-driven
- **LINDDUN** (privacy-focused)
- **OWASP Threat Dragon** — free tool

In practice: a 30-min whiteboard with engineering + security per major feature. Document the trust boundaries; enumerate threats per boundary; prioritize fixes.

## 8. Compliance frameworks that drive what you build

| Framework | Domain | Touch points |
|---|---|---|
| **SOC 2** | All SaaS | Access controls, monitoring, change mgmt, vendor mgmt |
| **PCI-DSS v4** (2024 effective) | Card data | Tokenization, network segmentation, scanning, pen test |
| **HIPAA** | US healthcare | PHI handling, BAA, audit logs (6yr retention), encryption |
| **GDPR** | EU citizens' data | Consent, data minimization, right to erasure, breach disclosure |
| **CCPA / CPRA** | California consumers | Similar to GDPR for CA |
| **SR 11-7** | US bank model risk | Model validation, audit trails, separation of duties |
| **FedRAMP** | US federal cloud | NIST 800-53 controls, continuous monitoring |
| **ISO 27001** | Global infosec | ISMS — Information Security Mgmt System |

Capital One operates under: PCI-DSS v4, SR 11-7, GLBA, SOC 1+2+3, ISO 27001, FFIEC.

## 9. The DevSecOps remit

DevSecOps shifts security:
- **Left** (earlier in lifecycle) — into design, into IDE
- **Right** (later in lifecycle) — into runtime detection/response
- **Everywhere** (the 2025 reframe) — at every stage of the pipeline

The remaining 20 modules of Part 2 map directly onto these stages.

## 10. Quick self-check

1. What's the CIA triad?
2. What was the root cause of the Capital One 2019 breach and which OWASP item is it?
3. Why is shift-left security more cost-effective than shift-right?
4. What does STRIDE stand for?
5. What's the difference between SOC 2 and PCI-DSS?

(Answers: Confidentiality, Integrity, Availability; SSRF + over-permissive IAM role + IMDSv1 — OWASP A10; finding bugs in design or IDE is ~100x cheaper than finding in prod; Spoofing/Tampering/Repudiation/Information disclosure/DoS/Elevation of privilege; SOC 2 is a SaaS-controls-attestation, PCI-DSS is a card-data-specific compliance standard.)
