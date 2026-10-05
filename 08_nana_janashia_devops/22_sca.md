# 22 — SCA — Software Composition Analysis

## Why this module exists

Your app is 5% your code and 95% open-source dependencies. SCA scans your dependency tree for known CVEs, license issues, and dangerous transitive deps. **xz utils backdoor (CVE-2024-3094, March 2024)** was a wake-up call — supply chain risk is real.

## 1. The SCA scope

What SCA covers:
1. **Known CVEs in dependencies** — match dep → NVD / GHSA / OSV databases
2. **License compliance** — GPL in proprietary code, license incompatibilities
3. **End-of-life packages** — unmaintained deps
4. **Transitive deps** — your direct dep brings 50 transitive deps; SCA scans them all
5. **Container base images** — image deps are also dependencies

## 2. The vuln-data sources

| Source | What |
|---|---|
| **NVD** (NIST National Vulnerability Database) | Authoritative CVE feed |
| **GHSA** (GitHub Advisory Database) | GitHub's curated DB; often faster than NVD |
| **OSV.dev** (Google) | Multi-ecosystem; structured |
| **PyPA Advisory DB** | Python-specific |
| **rustsec advisory DB** | Rust |
| **npm Advisory** | JS |
| **CVE.org / MITRE** | The numbering authority |

CVSS = Common Vulnerability Scoring System (0-10 severity). EPSS = Exploit Prediction Scoring System (probability of exploitation in next 30 days — newer + more actionable than CVSS).

## 3. SCA tool landscape

| Tool | Lang/Ecosystem | License |
|---|---|---|
| **Dependabot** (GitHub) | All | Free with GitHub |
| **Renovate** | All | OSS |
| **Snyk Open Source** | All | Commercial |
| **OWASP Dependency-Check** | Java + others | OSS |
| **Trivy fs** | All | OSS |
| **Grype** | All | OSS |
| **GitHub Dependency Graph** | All | Free with GitHub |
| **GitLab Dependency Scanning** | All | GitLab Ultimate |
| **JFrog Xray** | All | Commercial |
| **Sonatype Nexus IQ** | All | Commercial |
| **Mend (formerly WhiteSource)** | All | Commercial |
| **OSV-Scanner** (Google) | All | OSS |

## 4. Dependabot — the GitHub default

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule: { interval: "weekly" }
    open-pull-requests-limit: 10
    groups:
      python-deps:
        patterns: ["*"]
        update-types: ["minor", "patch"]
    ignore:
      - dependency-name: "numpy"
        update-types: ["version-update:semver-major"]

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule: { interval: "weekly" }

  - package-ecosystem: "docker"
    directory: "/"
    schedule: { interval: "weekly" }
```

Dependabot:
- Opens PRs for vulnerable + outdated deps
- Free; included with GitHub
- "Dependabot security updates" auto-open PRs for known CVEs even without schedule
- Use **groups** to bundle related deps (avoid 50 PRs)

## 5. Renovate — the more powerful alternative

Renovate (originally GitLab; now Mend-owned, still OSS) supersedes Dependabot for serious shops:
- Customizable group rules (e.g., "all minor TS deps in one PR weekly")
- Auto-merge when CI passes
- Dependency dashboard issue with all pending updates
- Better monorepo support (per-workspace updates)
- Supports more ecosystems
- Available as GitHub App, GitLab integration, or self-hosted

`renovate.json`:
```json
{
  "extends": ["config:recommended"],
  "schedule": ["before 6am on monday"],
  "packageRules": [
    {
      "matchUpdateTypes": ["minor", "patch"],
      "automerge": true,
      "automergeType": "branch"
    },
    {
      "matchPackageNames": ["torch", "transformers"],
      "schedule": ["before 6am on the first day of the month"]
    }
  ],
  "vulnerabilityAlerts": { "labels": ["security"], "automerge": false }
}
```

## 6. Trivy fs — SCA for any repo, CLI-friendly

```bash
# Scan a project directory
trivy fs --severity HIGH,CRITICAL --exit-code 1 .

# JSON output for DefectDojo
trivy fs -f json -o trivy-fs.json .

# Specific dep file
trivy fs --scanners vuln,secret,misconfig requirements.txt
```

Trivy combines: dep scanning + secret scanning + misconfig (IaC) scanning in one tool. The OSS Swiss Army knife.

## 7. License compliance

A few cases where SCA flags licenses:
- **GPL in proprietary code** — copyleft viral license; can force open-sourcing
- **AGPL** — even network use triggers source disclosure
- **No license** — defaults to "All rights reserved"; legally can't use
- **License mismatch with corporate policy** — many shops forbid AGPL, GPL > v2

Tools:
- **FOSSology** — OSS license scanner
- **ScanCode** — OSS license + provenance
- **Snyk License Compliance / Mend Licenses** — commercial
- **Software Bill of Materials (SBOM)** — see Module 24

## 8. Pinning + lockfiles (the supply-chain discipline)

The 2026 best practice:
- **Pin direct deps to exact versions** in your dependency file (e.g., `pandas==2.2.3` not `pandas>=2.0`)
- **Commit the lockfile** (poetry.lock, uv.lock, package-lock.json, go.sum)
- **For lockfile in cryptographic-hash form** (npm has integrity hashes, Go has go.sum hashes, uv has hash-verified lock)
- **For pip:** `pip-tools` or `uv` + hash-checking mode
- **Renovate / Dependabot** to bump deliberately

The xz utils backdoor exploited *new versions* — pinning doesn't fully protect (you'd update eventually) but **dependency review before merge** does.

## 9. SCA in CI

```yaml
# GitLab Ultimate has built-in
sast: { stage: test }
dependency_scanning: { stage: test }
include:
  - template: Jobs/Dependency-Scanning.gitlab-ci.yml
  - template: Jobs/SAST.gitlab-ci.yml
```

```yaml
# GitHub Actions with Trivy
- name: SCA
  run: trivy fs --severity HIGH,CRITICAL --exit-code 1 --format sarif -o trivy.sarif .

- uses: github/codeql-action/upload-sarif@v3
  with: { sarif_file: trivy.sarif }
```

```yaml
# GitHub Actions with Snyk
- uses: snyk/actions/python-3.10@master
  env: { SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }} }
  with: { command: monitor }
```

## 10. EPSS — the prioritization tool

EPSS (Exploit Prediction Scoring System) gives each CVE a probability of being exploited in the next 30 days. Far more actionable than CVSS.

- CVSS 10.0 + EPSS 0.0001 → critical but no known exploit; lower urgency
- CVSS 6.0 + EPSS 0.85 → medium but actively exploited; **fix now**

Modern SCA tools (Snyk, Mend) surface EPSS alongside CVSS. CISA's Known Exploited Vulnerabilities (KEV) catalog is the binary version: it's on the list or not.

## 11. The remediation playbook

For each SCA finding:
1. **Is it reachable?** If your code doesn't call the vulnerable function, severity may be lower (Snyk Reachability / Phylum / Endor Labs sell this analysis).
2. **Is there a fix?** Upgrade to patched version.
3. **No fix yet?** Workaround? Compensating control? Risk-accept with expiry?
4. **Mark in DefectDojo** with status.
5. **Track SLA** — Critical: 7 days; High: 30; Medium: 60.

## 12. Quick self-check

1. What's the difference between Dependabot and Renovate?
2. What's EPSS and why is it more actionable than CVSS alone?
3. Why does pinning direct deps not fully protect against supply-chain attacks?
4. What's the OSV.dev project?
5. What does "reachability analysis" do for SCA findings?

(Answers: Dependabot is GitHub-built, simple; Renovate is more configurable, OSS, group rules, automerge, monorepo-friendly; EPSS predicts exploit probability in next 30d — CVSS only measures theoretical severity; eventually you upgrade and pick up the malicious version (xz pattern); Google's multi-ecosystem structured vuln DB; tells you whether your code actually calls the vulnerable function — lowers severity for unreachable findings.)
