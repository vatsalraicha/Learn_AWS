# Quiz — Part 2 (DevSecOps Bootcamp: Modules 18-38)

## Section A — Security Fundamentals + Scanning

**Q1.** What was the root cause of the Capital One 2019 breach and which OWASP item is it?

<details><summary>Answer</summary>

SSRF + over-permissive IAM role + IMDSv1 — OWASP A10. IMDSv2 hop-limit=1 mitigates the specific attack vector.
</details>

**Q2.** What problem does the pre-commit framework solve?

<details><summary>Answer</summary>

Orchestrates many hooks (gitleaks, lint, format, secret detect) from a single declarative `.pre-commit-config.yaml` + version-pins each.
</details>

**Q3.** Why must CI also scan for secrets if pre-commit catches them?

<details><summary>Answer</summary>

Developers can bypass pre-commit with `git commit --no-verify`. CI is the enforcement layer that can't be bypassed.
</details>

**Q4.** What's the difference between SAST, DAST, and IAST?

<details><summary>Answer</summary>

SAST scans source code, DAST scans the running app, IAST instruments the running app (agent inside). False positives: SAST high → IAST low.
</details>

**Q5.** What problem does DefectDojo solve that running scanners individually doesn't?

<details><summary>Answer</summary>

Normalizes findings from many scanners into one trackable backlog with dedup + SLA + CWE mapping + risk-accept workflow + reporting.
</details>

**Q6.** What's EPSS and why is it more actionable than CVSS alone?

<details><summary>Answer</summary>

Exploit Prediction Scoring System — probability of exploitation in next 30 days. CVSS only measures theoretical severity; EPSS measures actual risk.
</details>

## Section B — Container Security + GitOps

**Q7.** What is "keyless signing" with Cosign and what 3 Sigstore components make it work?

<details><summary>Answer</summary>

OIDC-based ephemeral keys with no long-term key management. Components: Fulcio (CA for short-lived certs), Rekor (transparency log), Cosign (CLI).
</details>

**Q8.** What's SLSA L3 in one sentence?

<details><summary>Answer</summary>

Build runs in isolated environment producing non-falsifiable provenance signed by the build platform.
</details>

**Q9.** What's the security advantage of GitOps's pull model over CI-push?

<details><summary>Answer</summary>

Pipeline doesn't need cluster credentials; cluster pulls from Git. Fewer credentials to leak. Plus Git-history audit, drift detection.
</details>

**Q10.** Why is Kyverno winning over OPA Gatekeeper for K8s-only shops in 2026?

<details><summary>Answer</summary>

YAML policies (simpler than Rego), native mutation + generation, image signature verify built-in. K8s-focused — no need for Rego's cross-tool flexibility.
</details>

## Section C — AWS + K8s Security

**Q11.** What's the IAM permission evaluation precedence order?

<details><summary>Answer</summary>

Explicit Deny → SCP/RCP → Permission Boundary → Identity Policy ∩ Resource Policy → implicit Deny.
</details>

**Q12.** Why does the legacy aws-auth ConfigMap pose risks compared to EKS Access Entries?

<details><summary>Answer</summary>

Bad edit can lock you out of cluster. No IAM controls on its modification. Only K8s-audit (no CloudTrail). Access Entries fix all three.
</details>

**Q13.** What replaced PodSecurityPolicy in K8s 1.25+ and what are the three profiles?

<details><summary>Answer</summary>

Pod Security Admission (PSA) enforcing Pod Security Standards. Profiles: Privileged, Baseline, Restricted.
</details>

**Q14.** Why is automounting the ServiceAccount token to a pod that doesn't need K8s API a risk?

<details><summary>Answer</summary>

The token is a credential. Compromised pod → attacker has K8s API access scoped to that SA. Set `automountServiceAccountToken: false` for pods that don't need the API.
</details>

## Section D — Secrets, Mesh, Compliance

**Q15.** Why are K8s Secrets not actually secret?

<details><summary>Answer</summary>

Base64-encoded only — not encrypted. Anyone with API access can decode them. Use envelope encryption with KMS + External Secrets Operator + cloud secret manager.
</details>

**Q16.** What does Istio's PeerAuthentication object do?

<details><summary>Answer</summary>

Configures mTLS mode (STRICT / PERMISSIVE / DISABLE) for pods in scope. STRICT = only mTLS allowed; PERMISSIVE = accepts both during migration.
</details>

**Q17.** What's the difference between NetworkPolicy and Istio AuthorizationPolicy?

<details><summary>Answer</summary>

NetworkPolicy is L3/L4 + IP/label-based + cheap. Istio AuthZ is L7 + SPIFFE-identity-based + mTLS-required. Use both layered.
</details>

**Q18.** What's Cloud Custodian and who built it?

<details><summary>Answer</summary>

Declarative Python policy-as-code framework for AWS resources — detection + filters + actions in one YAML. Capital One built it, CNCF Sandbox since 2018.
</details>

**Q19.** Why is auto-remediation valuable beyond just detection?

<details><summary>Answer</summary>

Closes the window between detection and human response — many findings should be auto-fixed in seconds, not days. Defense-in-depth at machine speed.
</details>

**Q20.** Why does "buy tools and drop them on devs" fail as a DevSecOps strategy?

<details><summary>Answer</summary>

No training, no support, no triage capacity → backlog grows → tools get ignored. Humans + process + paved-road > tools alone.
</details>

---

**Scoring**: 18+ → DevSecOps-ready conversation. 14-17 → solid working knowledge. < 14 → revisit critical modules.
