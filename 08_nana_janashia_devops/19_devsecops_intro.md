# 19 — Introduction to DevSecOps

## 1. The problem DevSecOps solves

Traditional security:
- Security review at the end (waterfall)
- Bottleneck: 1 security engineer for 100 devs
- "No" by default; slows releases
- Findings come back weeks after code shipped
- Fix cost: 100x what it would have been at design

The result: teams ship insecure code OR security blocks the business. Neither works.

## 2. The DevSecOps reframe

- Security is **everyone's** job — devs own remediation
- Security tools **shift left** into IDE, pre-commit, PR checks
- Security **automates** what humans did manually (scanning, policy enforcement)
- Security teams **build platforms** that scale — paved roads, not gatekeeping

## 3. DORA + DevSecOps — the data

The 2024 DORA report adds **security** as a 5th capability dimension. Findings:
- **Elite teams** integrate security into delivery; medium teams have security as a separate gate
- **Elite teams** have higher security AND higher velocity (the security/speed tradeoff is false)
- **Elite teams** automate ~80% of security checks

The DevSecOps thesis empirically holds.

## 4. The DevSecOps pipeline (the canonical view)

```
Plan        Design          Code           Build          Test            Release/Deploy    Monitor
│           │               │              │              │               │                 │
threat      secure          IDE             SAST           DAST            signing            SIEM
modeling    design          security        SCA            IAST            admission control  EDR
            review          extensions      secrets scan   compliance      runtime defense    incident response
                            pre-commit      image scan     scans
```

Each pipeline stage gets its own security gate. Findings flow to **DefectDojo** (or equivalent) for triage.

## 5. Roles & responsibilities

| Role | DevSecOps mandate |
|---|---|
| **Developer** | Write secure code; respond to scan findings; threat model their feature |
| **Security Engineer** | Build the platform; tune rules; investigate alerts; train devs |
| **DevOps / Platform Engineer** | Wire scanners into pipelines; harden infra |
| **AI/ML Engineer** | Same as developer + model-specific risks (data leakage, adversarial inputs, prompt injection) |
| **Compliance / Audit** | Map controls to frameworks; produce evidence |
| **Manager / EM** | Make security explicit in OKRs; defend remediation time |

Capital One: ~1:30 ratio (security engineers : product engineers) — they build the platform, not the reviews.

## 6. The DevSecOps maturity ladder

| Level | Posture |
|---|---|
| **0 — None** | No scans; security only via pen test at release |
| **1 — Manual** | Some scanners exist but findings not enforced |
| **2 — Automated** | CI gates on Critical findings |
| **3 — Integrated** | Scanners + DefectDojo + SLA + rotation; metrics tracked |
| **4 — Continuous** | Policy-as-code + runtime defense + auto-remediation; elite DORA |

Most regulated finance is at L3 trending L4.

## 7. The 11 capabilities (and where each maps in this curriculum)

| # | Capability | Module |
|---|---|---|
| 1 | Secret scanning | 20 |
| 2 | SAST | 22 (mentioned in 20-22) |
| 3 | SCA | 22 |
| 4 | DAST | 26 |
| 5 | Container/image scanning | 24 |
| 6 | IaC scanning | 27 |
| 7 | Cloud security (IAM, CSPM) | 25, 28 |
| 8 | K8s security (RBAC, admission) | 29-30, 34 |
| 9 | Secrets management | 35 |
| 10 | Service mesh + mTLS | 36 |
| 11 | Compliance as code | 37 |

## 8. The metrics that matter (DevSecOps KPIs)

- **MTTR for security findings** — by severity, by team
- **% of findings remediated within SLA**
- **Critical CVEs in production** (should be 0)
- **% pipelines with security scans enabled** (should be 100)
- **Mean time from scanner alert to ticket creation** (should be < 1hr; automate)
- **Security debt aging** (oldest unfixed Critical)

## 9. The shift-everywhere progression

| Stage | Where security lives |
|---|---|
| Old | Pre-release pen test |
| Shift-left | Pre-commit + IDE + CI scans |
| Shift-right | Runtime detection + EDR + admission |
| **Shift-everywhere** (2025+) | All of above + threat modeling at design |

The 2026 mindset: security is a non-functional requirement, not a phase.

## 10. The cultural unblockers

What kills DevSecOps in practice:
- **Punitive findings disposition** — devs game the tool, hide work
- **No remediation time in sprints** — "we'll get to it" never happens
- **Vendor sprawl** — 20 scanners, 0 normalization (this is what DefectDojo solves)
- **No exec backing** — security loses to feature pressure

What unblocks:
- Blameless culture
- Time explicitly budgeted for security work
- Findings normalized into one platform with SLAs
- Sec engineers embedded in dev teams, not in a separate ivory tower

## 11. Quick self-check

1. What's the "shift-everywhere" reframe over "shift-left"?
2. Why is the speed/security tradeoff considered false by DORA?
3. Name three signs of a DevSecOps maturity ladder L1 (manual) team.
4. What's the role of DefectDojo in the DevSecOps pipeline?
5. What's the most common cultural anti-pattern that kills DevSecOps in practice?

(Answers: security lives at every stage including design + runtime, not just CI; elite teams have higher velocity AND security — they automate the tradeoff away; scanners exist but findings not enforced + no SLAs + no normalized triage + no remediation budget; normalizes findings from many scanners into one trackable backlog with CWE mapping; punitive disposition that punishes devs for findings causes hiding and gaming.)
