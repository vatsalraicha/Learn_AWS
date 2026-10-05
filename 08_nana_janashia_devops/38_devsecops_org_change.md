# 38 — Introducing DevSecOps in Organizations

## Why this module exists

Tools are 20% of DevSecOps; org change is 80%. This module is the people + process layer.

## 1. Why DevSecOps fails to take root

The pattern when DevSecOps fails:
- **Sec team buys tools** → drops them on dev teams → no training, no support → tools ignored
- **Findings flood** → no triage capacity → backlog grows → devs disengage
- **Security team is gate, not partner** → adversarial dynamic → workarounds + shadow IT
- **No exec backing** → feature pressure wins every conflict → security debt accumulates
- **Vendor sprawl** → 20 tools, no normalization → review fatigue

## 2. Cultural change drivers (what actually works)

### Make security visible
Dashboards everyone sees: open findings by team, SLA compliance, time-to-fix. **Public scoreboards drive behavior** (positively or negatively — calibrate carefully).

### Reward fixing, not punish finding
A team that ships features and has zero findings might be hiding them or not scanning. A team with many findings + fast fixes is healthy. The metric should be **MTTR**, not finding count.

### Embed security engineers in product teams
Stop the ivory-tower model. Embed: pair on threat models, write policies together, attend standups. Capital One does this at ~1:30 ratio.

### Run blameless postmortems
When an incident happens, the culture must be "what process gap?" not "who screwed up?" Otherwise people hide problems. (Same SRE principle, applied to security.)

### Champions program
Volunteer "security champions" in each product team — 10% time on security work, regular training. They become the bridge.

## 3. The real-world examples

### Netflix — Paved Road
Security team builds golden paths (Spinnaker, Lemur, BLESS, etc.) that are easier than rolling your own. Teams use the paved road because it's the path of least resistance — not because they're forced.

### Capital One — Cloud Custodian + InnerSource
- Built **Cloud Custodian** in-house; open-sourced 2018; used internally by every team.
- **InnerSource** model: security tools are internal OSS projects; product teams can contribute.
- **Security as a Service** internal — security team operates platforms, product teams consume.
- After 2019 breach: doubled down on least-privilege automation, multi-account architecture, IMDSv2 enforcement.

### Shopify — Security Engineering as Product
- Security tools have product managers + designers + UX research.
- "Security is a product" — measured by developer adoption + NPS, not just findings.

### Stripe — Risk-tiered Security
- Tiered controls by impact (PII service vs marketing site)
- Avoid "every service gets every control" — wasted effort
- High-tier services get more rigor (SAST + DAST + SCA + manual review); low-tier less

## 4. The DevSecOps transformation roadmap (12-month)

### Months 1-2: Baseline
- Inventory: what tools, what scans, what coverage today
- Surveys: how do devs feel about security right now
- Pick 2-3 frameworks to standardize on (SOC 2 + CIS AWS + CIS K8s, e.g.)

### Months 3-4: Foundation
- Stand up DefectDojo (or equivalent)
- Pre-commit hooks rolled out: gitleaks + linters
- SCA + SAST in CI on PRs
- OIDC for CI/CD (kill long-lived keys)

### Months 5-6: Container security
- Trivy in CI; fail Critical
- ECR + Cosign signing
- Pod Security Admission (restricted) on new namespaces

### Months 7-8: Cloud security
- AWS Config + Security Hub
- Cloud Custodian or equivalent
- IAM Access Analyzer
- CloudTrail + alarms

### Months 9-10: K8s + GitOps
- Kyverno admission policies
- ArgoCD/Flux migration
- External Secrets Operator
- Istio mTLS (or simpler — cert-manager + NetworkPolicy)

### Months 11-12: Monitoring + Maturity
- Compliance dashboards
- Auto-remediation for low-risk findings
- Quarterly DR + IR drills
- Re-survey team morale

## 5. DORA-style measurement for DevSecOps

The metrics to track quarterly:
- **% of pipelines with security scans enabled** (target: 100%)
- **Critical CVEs in production** (target: 0)
- **MTTR for security findings, by severity** (target: Critical < 7d, High < 30d)
- **Auto-remediation rate** (target: 50%+ of low-risk findings)
- **Time from alert to ticket** (target: < 5 min — automate)
- **Developer NPS on security tools** (target: positive)

## 6. The Build vs Buy decision

| | Build | Buy |
|---|---|---|
| **Best for** | Unique workflows; org > 5000 engineers | Standard workflows; small team |
| **Time to value** | 6-12 months | Weeks |
| **Customization** | Total | Limited |
| **Ongoing cost** | Engineering + ops | Subscription |
| **Risk** | Internal expertise dependency | Vendor lock-in + supply chain |

Capital One: builds (Cloud Custodian, internal tooling) but also buys (Wiz/Lacework-tier CSPM, Splunk SIEM).

Most teams: buy for everything; build only when scale demands.

## 7. Vendor selection criteria (the boring but essential list)

When evaluating a DevSecOps tool:
- **API-first** — can it integrate with everything you have
- **SAML / SSO + SCIM** — proper enterprise auth
- **CI/CD integration** — GitHub Actions, GitLab CI, Jenkins
- **DefectDojo / Jira ticketing integration**
- **Per-developer vs per-resource pricing** — model your trajectory
- **On-prem option** for regulated shops
- **Support quality** — talk to references
- **Roadmap alignment** — where they're investing
- **Acquisition risk** — vendor stability

## 8. Compliance vs Security (the meta-point)

**Compliance** = passing audits.
**Security** = not getting breached.

They overlap but aren't the same. A team can be compliant and unsecure (security theater). Or secure but non-compliant (mature controls not mapped to a framework).

DevSecOps should aim for **security** with compliance as a side effect. Audit-pass is the floor, not the ceiling.

## 9. The exec sponsor lever

DevSecOps needs:
- **Board / CISO sponsor** — gets time + budget approved
- **Engineering VP sponsor** — gets team buy-in
- **Public commitment** — "we will not ship with Critical CVEs" — credible commitment makes prioritization decisions automatic

Without exec backing, security loses every conflict with feature pressure.

## 10. Quick self-check

1. Why does "buy tools and drop them on devs" fail as a DevSecOps strategy?
2. What's the difference between security and compliance?
3. What's a "security champion" program?
4. Name three DevSecOps maturity metrics you'd track quarterly.
5. Why is "paved road" better than "mandatory policy" for adoption?

(Answers: no training/support/triage → backlog grows → tools get ignored — humans matter more than tools; compliance = pass audit, security = don't get breached — overlap but not the same; volunteer engineers in product teams who allocate 10% to security work + are the bridge to security team; % of pipelines scanned, Critical CVEs in prod, MTTR by severity, auto-remediation rate, developer NPS; humans take the path of least resistance — make secure path easier than insecure path and people use it without being told.)
