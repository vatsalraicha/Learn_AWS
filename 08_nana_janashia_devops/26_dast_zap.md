# 26 — Secure CD + DAST with OWASP ZAP

## Why this module exists

SAST scans your source code; SCA scans your deps; image scans look at the built artifact. **DAST (Dynamic Application Security Testing) scans the running app** — finds runtime vulns SAST can't (auth flaws, business logic, configuration issues).

## 1. DAST vs SAST vs IAST

| | SAST | DAST | IAST |
|---|---|---|---|
| **When** | Code-time | Runtime | Runtime, instrumented |
| **Needs** | Source code | Running app | Agent in the app |
| **Finds** | Pattern matches, taint flows | Real exploit attempts | Both |
| **False positives** | High | Lower | Lowest |
| **Speed** | Fast | Slow (full scan: hours) | Real-time |
| **Tooling** | Semgrep, CodeQL, SonarQube, Bandit | OWASP ZAP, Burp Suite, StackHawk | Contrast, Seeker (HCL) |

You want all three (or at least SAST + DAST). Capital One does.

## 2. OWASP ZAP — the OSS DAST leader

ZAP (Zed Attack Proxy) — originally OWASP flagship; since 2023 hosted by **The Software Security Project** (separate non-profit, after OWASP governance changes); still OSS Apache-2.0.

Modes:
- **Baseline scan** — passive, ~2 min; finds low-hanging fruit
- **Full scan** — active, can run hours; sends actual attack payloads
- **API scan** — given an OpenAPI/GraphQL/SOAP spec, tests endpoints

## 3. ZAP baseline scan in CI

```yaml
# GitLab CI
dast-baseline:
  stage: dast
  image: ghcr.io/zaproxy/zaproxy:stable
  script:
    - zap-baseline.py -t https://staging.example.com -r dast-report.html -J dast.json -m 10
  artifacts:
    paths:
      - dast-report.html
      - dast.json
    expire_in: 30 days
  allow_failure: true
```

```yaml
# GitHub Actions
- name: ZAP Baseline Scan
  uses: zaproxy/action-baseline@v0.13.0
  with:
    target: https://staging.example.com
    rules_file_name: '.zap/rules.tsv'
    cmd_options: '-J zap.json'
```

Baseline scan does:
- Spider the site
- Identify forms, headers, cookies
- Check for missing security headers (CSP, HSTS, X-Frame-Options)
- Check cookie attributes (HttpOnly, Secure, SameSite)
- TLS configuration check
- Default credential checks
- **Does NOT send malicious payloads** — safe to run nightly

## 4. ZAP full scan

```bash
docker run -v $(pwd):/zap/wrk -t ghcr.io/zaproxy/zaproxy:stable \
  zap-full-scan.py -t https://staging.example.com -r full-report.html
```

Full scan **does** send active payloads (SQL injection attempts, XSS payloads, command injection). Only run against test environments — never production. Coordinate with WAF teams (will trigger alerts).

## 5. ZAP API scan (for REST/GraphQL APIs)

```bash
zap-api-scan.py -t https://api.example.com/openapi.json \
  -f openapi -r api-report.html
```

ZAP parses the OpenAPI spec; tests every endpoint with auth + edge cases.

## 6. Custom rules + authentication

DAST against authenticated apps requires teaching ZAP to log in:

```yaml
# Authentication config (ZAP automation framework)
env:
  contexts:
    - name: app
      urls: [https://staging.example.com/]
      authentication:
        method: json
        parameters:
          loginUrl: https://staging.example.com/api/login
          loginRequestBody: '{"username":"qa","password":"qa"}'
        verification:
          method: poll
          loggedInRegex: "\\Q\"loggedIn\":true\\E"
      sessionManagement:
        method: cookie
      users:
        - name: qa
          credentials: { username: qa, password: qa }
```

Then `zap-baseline.py -t ... --hook /zap/auth-hook.py`.

## 7. WAF interaction

Your WAF (AWS WAF, Cloudflare, Akamai) will block DAST scans. Options:
- **Whitelist scanner IPs** in WAF for the staging environment
- **Disable WAF on staging** entirely
- **Tag traffic** so WAF logs but doesn't block

Coordinate with security team; don't surprise the SOC with attack traffic at 3am.

## 8. Beyond ZAP — the DAST landscape

| Tool | Note |
|---|---|
| **Burp Suite Community / Pro** | Manual pen-tester favorite; Pro adds scanner ($499/yr/user) |
| **StackHawk** | Commercial; ZAP-engine-based; CI-friendly; per-app pricing |
| **Invicti** / **Acunetix** | Enterprise web app + API |
| **Wallarm** / **42Crunch** | API-specific |
| **Schemathesis** | OSS property-based API testing |

For CI integration: ZAP or StackHawk are the realistic choices. Burp Pro is for manual review.

## 9. API-specific DAST

REST/GraphQL APIs need different testing than full web apps. Tools:
- **Schemathesis** — OSS; property-based from OpenAPI/GraphQL schema
- **42Crunch** — API security platform
- **Wallarm** — API security
- **Postman + Newman** — collection-based functional tests (not security but useful baseline)

```bash
# Schemathesis
schemathesis run https://api.example.com/openapi.json --checks all
```

## 10. Mobile app DAST

For mobile (iOS/Android), DAST means:
- **MobSF** (Mobile Security Framework) — OSS, static + dynamic for mobile binaries
- **NowSecure** — commercial
- **Quark Engine** — Android malware analysis

Less common for back-end engineers; relevant if you ship a mobile app.

## 11. The complete DevSecOps pipeline (where DAST fits)

```
SAST (CI on PR)
  ↓
SCA (CI on PR)
  ↓
Image scan (CI after build)
  ↓
Deploy to staging
  ↓
DAST baseline (post-deploy, on every release)
  ↓
DAST full (nightly, scheduled)
  ↓
DAST API (on schema change)
  ↓
Manual pen test (quarterly)
```

## 12. Quick self-check

1. What's the difference between SAST and DAST?
2. What's the difference between ZAP baseline scan and ZAP full scan?
3. Why can't you run DAST full-scan against production?
4. Why is authenticated DAST significantly harder than unauthenticated?
5. What is Schemathesis and what makes it different from ZAP?

(Answers: SAST scans source code, DAST scans the running app; baseline is passive + safe ~2min, full sends active attack payloads + can run hours; DAST sends real attack payloads that could damage data, trip WAFs, or affect real users; ZAP has to learn login flow + maintain session + re-auth as session expires; OSS property-based API testing from OpenAPI/GraphQL schema — generates test inputs from contract, complementary to ZAP.)
