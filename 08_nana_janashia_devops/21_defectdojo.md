# 21 — Vulnerability Management — DefectDojo + CWE

## Why this module exists

You have 6+ scanners (GitLeaks, Trivy, Snyk, ZAP, SonarQube, Checkov, Dependabot). Each outputs findings in its own format. Without normalization you can't:
- Dedupe (same CVE flagged by 3 tools = 3 tickets if not normalized)
- SLA-track (fix Critical in 7 days, High in 30 days)
- Report ("how many open Criticals on team X?")
- Prove compliance ("we triage every finding")

**DefectDojo** is the OSS aggregator. The commercial alternatives: **Snyk** (vendor's own platform), **Mend (WhiteSource)**, **Veracode**, **Checkmarx**, **GitLab Vulnerability Report** (built into Ultimate).

## 1. DefectDojo at a glance

- OSS (originally OWASP DefectDojo, now under SecurityCompass + community)
- Python + Django + Postgres
- Supports **200+ scanner formats** (parses JSON, SARIF, XML, etc.)
- Free; commercial **DefectDojo Pro** for SaaS deployment
- Self-hosted in Docker / K8s; many ASPM (Application Security Posture Mgmt) vendors built ON DefectDojo

## 2. Concepts

```
Product Type
  └─ Product (an application or service)
      └─ Engagement (a security activity: pen test, code scan campaign, etc.)
          └─ Test (one scanner run)
              └─ Finding (one vulnerability)
```

**Finding** properties:
- Severity (Critical / High / Medium / Low / Info)
- CWE
- CVE (if applicable)
- Status: Active / Verified / Mitigated / False-Positive / Out-of-Scope
- SLA dates
- Mitigation steps
- Notes

## 3. Install (Docker Compose for learning)

```bash
git clone https://github.com/DefectDojo/django-DefectDojo
cd django-DefectDojo
./dc-up.sh
# Wait, then:
./dc-up.sh --build-pull
# Get admin password:
docker compose -f docker-compose.yml logs initializer | grep "Admin password"
```

Browse http://localhost:8080. Login as `admin` + the password.

For production: K8s Helm chart from `https://github.com/DefectDojo/django-DefectDojo` charts dir.

## 4. Importing scanner results

Each scanner has its own DefectDojo "parser." Examples:

| Scanner | DefectDojo parser |
|---|---|
| Trivy | "Trivy Scan" |
| Bandit | "Bandit Scan" |
| GitLeaks | "Gitleaks Scan" |
| ZAP | "ZAP Scan" |
| Semgrep | "Semgrep JSON Report" |
| Checkov | "Checkov Scan" |
| Snyk | "Snyk Scan" |
| SARIF (universal) | "SARIF" |

Upload via UI or API:

```bash
curl -X POST "$DD_URL/api/v2/import-scan/" \
  -H "Authorization: Token $DD_API_TOKEN" \
  -F "scan_date=2026-05-22" \
  -F "minimum_severity=Low" \
  -F "active=true" \
  -F "verified=false" \
  -F "scan_type=Trivy Scan" \
  -F "file=@trivy-report.json" \
  -F "engagement=42" \
  -F "test_title=Trivy scan of api:1.2.3"
```

**reimport-scan** vs **import-scan**: reimport dedupes against existing findings → ticket already exists, no new one created. Use reimport in CI for repeated scans.

## 5. CI integration (the production pattern)

```yaml
# GitHub Actions snippet
- name: Trivy scan
  run: trivy image --format json -o trivy.json ghcr.io/me/app:${{ github.sha }}

- name: Upload to DefectDojo
  env:
    DD_URL: ${{ secrets.DD_URL }}
    DD_TOKEN: ${{ secrets.DD_TOKEN }}
  run: |
    curl -fsSL -X POST "$DD_URL/api/v2/reimport-scan/" \
      -H "Authorization: Token $DD_TOKEN" \
      -F "scan_date=$(date +%F)" \
      -F "scan_type=Trivy Scan" \
      -F "active=true" -F "verified=false" \
      -F "engagement=${{ vars.DD_ENGAGEMENT_ID }}" \
      -F "file=@trivy.json"
```

## 6. CWE — the taxonomy DefectDojo speaks

CWE = Common Weakness Enumeration. Maintained by MITRE. Hierarchical:
- **CWE-1000** view (research view, full tree)
- **CWE-1003** view (mapping into SDLC weaknesses)
- **CWE Top 25** annual list of most-dangerous

Examples:
- CWE-79 → XSS
- CWE-89 → SQL Injection
- CWE-22 → Path Traversal
- CWE-918 → SSRF
- CWE-787 → Out-of-bounds Write (most-dangerous in 2024)

DefectDojo uses CWE as the canonical taxonomy across scanners. CVE-XXXX (specific instance) maps to CWE-NNN (weakness category).

## 7. SLA + automation

Configure SLA per severity in DefectDojo:
- Critical: 7 days
- High: 30 days
- Medium: 60 days
- Low: 90 days

Findings past SLA show in the SLA dashboard. Integration with Jira/GitLab/GitHub Issues auto-creates tickets.

Other automation:
- **JIRA integration** — sync findings → tickets bidirectionally
- **Slack notifications** — on new Critical findings
- **API webhooks** — on finding-state changes

## 8. Risk acceptance + false-positive triage

Most scanners produce false positives. DefectDojo workflow:
1. **New finding** appears (Active, Unverified)
2. Triage: developer + security review
3. Set status: **Verified** (real) or **False-Positive** (incorrect)
4. Set **Mitigation** if accepted risk with compensating control
5. **Risk Acceptance** for findings that aren't false-positive but can't be fixed (compensating control + expiry date)

Risk Acceptance is reviewed quarterly. SR 11-7-style audit asks: "show me all accepted risks, their justifications, and their compensating controls."

## 9. Reporting + dashboards

DefectDojo dashboards:
- Open findings by severity + age
- Product risk scores
- Trends (findings/week, MTTR)
- SLA compliance

Export reports as PDF/CSV for auditors. SOC 2 / PCI-DSS auditors love this artifact.

## 10. Alternatives at a glance

| Tool | Comparison |
|---|---|
| **GitLab Vulnerability Report** | Built into GitLab Ultimate; tight CI integration; auto-dedupe; vendor-locked |
| **Snyk** | Best UX; commercial scanner + tracker; per-developer pricing |
| **GitHub Code Scanning** (CodeQL) | GitHub-native; SARIF-based; less rich tracking |
| **Checkmarx One** | Enterprise SAST/SCA/DAST + tracker |
| **Veracode** | Long-standing, enterprise; binary-analysis SAST |
| **OX Security / Apiiro / Cycode** | ASPM challengers — full lifecycle |

For Capital One scale: enterprise ASPM tool (Apiiro, Cycode, or similar) + GHAS Code Security + internal triage workflows.

## 11. Quick self-check

1. What problem does DefectDojo solve that running scanners individually doesn't?
2. What's the difference between import-scan and reimport-scan?
3. What's CWE vs CVE?
4. What's a "Risk Acceptance" in DefectDojo and why is it audited?
5. Name three commercial alternatives to DefectDojo.

(Answers: normalizes findings from many scanners into one trackable backlog with dedup + SLA + reporting; reimport dedupes findings vs existing ones, import creates fresh — use reimport in CI; CWE is a category of weakness, CVE is a specific instance/identifier; finding kept open with compensating control and expiry instead of fixed — auditors check justification + control + expiry; Snyk, Mend, Veracode, Checkmarx, GitLab Vulnerability Report, GitHub Code Scanning.)
