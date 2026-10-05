# Quiz 03 — Actions advanced + GHAS + Compliance (Parts F–H)

Covers modules 26–37.

---

## Section 1 — Reusable workflows + composite actions + ARC (modules 26–28)

1. **What's the difference between a reusable workflow and a composite action?**
   <details><summary>Answer</summary>Reusable workflow = whole jobs (`runs-on:`, multiple steps, services, container). Used via `jobs.<id>.uses:`. Composite action = sequence of steps within a job. Used via `steps.uses:`. Reusable workflows for "whole pipelines"; composite actions for "reusable step sequences."</details>

2. **What's the nesting limit for reusable workflows?**
   <details><summary>Answer</summary>4 levels deep (A → B → C → D, no further).</details>

3. **What is `secrets: inherit` and when should you use it?**
   <details><summary>Answer</summary>Forwards all caller's secrets to a reusable workflow. Convenient but blurs trust boundaries. Per 2026 guidance, explicit per-secret passing via `secrets: { NAME: ${{ secrets.NAME }} }` is preferred for trust clarity. Use `inherit` only in same-org cases where you trust the reusable workflow.</details>

4. **What are the two Helm charts that comprise ARC?**
   <details><summary>Answer</summary>`gha-runner-scale-set-controller` (the operator) and `gha-runner-scale-set` (the runner pool). Distributed as OCI artifacts on `ghcr.io/actions/actions-runner-controller-charts`.</details>

5. **What's the difference between ARC's `dind` and `kubernetes` container modes?**
   <details><summary>Answer</summary>`dind` = Docker-in-Docker; privileged; simple but security-concerning. `kubernetes` = uses container hooks to schedule containers as sibling pods (no privileged daemon). Preferred for security. Required for some operations to work cleanly.</details>

---

## Section 2 — OIDC to AWS (modules 29, 46)

6. **What's the OIDC provider URL for GitHub?**
   <details><summary>Answer</summary>`https://token.actions.githubusercontent.com`. Audience: `sts.amazonaws.com`.</details>

7. **What's the most-important security pitfall when writing OIDC trust policies?**
   <details><summary>Answer</summary>NEVER use `ForAllValues:StringEquals` in an Allow statement. It returns true when the claim is absent or misspelled, granting unintended access. Always use `StringEquals` or `StringLike`.</details>

8. **What does the `sub` claim look like for restricting to a specific environment?**
   <details><summary>Answer</summary>`repo:capitalone/cool-ml-service:environment:prod`. Combined with the `prod` GitHub Environment requiring manual approval, this is the gold-standard pattern for prod-deploy auth.</details>

9. **What's the `job_workflow_ref` claim used for?**
   <details><summary>Answer</summary>Identifies the reusable workflow that called the current job. Restricting your trust policy to a specific `job_workflow_ref` means roles can only be assumed via your central blessed pipeline — service teams can't write inline AWS calls and grab prod roles.</details>

10. **What permission is required in the workflow for OIDC?**
    <details><summary>Answer</summary>`permissions: id-token: write` (at workflow or job level).</details>

---

## Section 3 — Environments + cost (modules 30, 31)

11. **What protection rules can a GitHub Environment have?**
    <details><summary>Answer</summary>Required reviewers (up to 6 people/teams, 1–6 approvals required), wait timer (delay N min before starting), deployment branches (which refs can deploy), custom protection rules (third-party app callbacks). Plus environment-scoped secrets + variables.</details>

12. **What's the relationship between environments and OIDC sub-claims?**
    <details><summary>Answer</summary>Job declares `environment: prod`. OIDC sub claim includes `environment:prod`. Trust policy requires this sub. Result: prod role can only be assumed from a workflow running in the prod environment, which required manual approval. Combines separation of duties (env approval) with credential scoping (OIDC).</details>

13. **What are the cost levers for Actions billing?**
    <details><summary>Answer</summary>Concurrency cancellation (cancel duplicate PR runs), path filters (skip CI on docs), matrix pruning, caching, runner sizing, avoid macOS/Windows where not needed (10×/2× multipliers), skip-CI commits for low-value changes, self-hosted at scale.</details>

---

## Section 4 — GHAS + supply chain (modules 32–35)

14. **What does GitHub Secret Protection cost?**
    <details><summary>Answer</summary>$19/active committer/month (since GHAS unbundling, April 1 2025). GitHub Code Security is the separate $30/mo product. Active committer = any contributor who pushed to a GHAS-enabled private repo in the last 90 days.</details>

15. **What detects secrets at push time and how can users bypass it?**
    <details><summary>Answer</summary>GHAS Secret Protection's push protection. Bypass requires explicit "false positive" or "fix later" declaration with reason — captured in audit log for review.</details>

16. **What's Copilot Autofix and when is it enabled?**
    <details><summary>Answer</summary>LLM-suggested fixes for CodeQL alerts. GA August 2024; enabled by default with code scanning, no separate toggle. Suggestion appears as a one-click code change in the PR.</details>

17. **What SLSA Build Level do GitHub Artifact Attestations achieve out-of-the-box?**
    <details><summary>Answer</summary>Level 2 by default. Level 3 by using reusable workflows (isolation between build process and calling workflow).</details>

18. **What's the difference between CycloneDX and SPDX SBOM formats?**
    <details><summary>Answer</summary>SPDX (Linux Foundation) is legal/license-first (richer license model). CycloneDX (OWASP) is security-first (vulnerabilities, services, attestations included). Pick CycloneDX for security use cases; SPDX for legal/license compliance.</details>

---

## Section 5 — Compliance + SR 11-7 (modules 36, 37)

19. **What's SCIM for?**
    <details><summary>Answer</summary>System for Cross-domain Identity Management. Automates GitHub org user provisioning from your IdP: employee joins → SCIM creates GitHub user; team change → SCIM updates GitHub team; employee leaves → SCIM deactivates user. Non-negotiable for compliant deprovisioning at enterprise scale.</details>

20. **What is SR 11-7 and what does it require for ML CI/CD?**
    <details><summary>Answer</summary>Federal Reserve Supervisory Letter (April 4, 2011) on model risk management. Applies to every US bank's quantitative models, including ML. Requires: three lines of defense (1L dev, 2L MRM, 3L audit), independent validation gates, immutable audit trails, separation of duties on deploys, ability to reconstruct model state at any past point in time, documented rollback capability.</details>

21. **How long is the GitHub audit log retained in the UI vs API?**
    <details><summary>Answer</summary>6 months in UI; exportable indefinitely via API. Stream to your SIEM for long-term retention required by compliance.</details>

22. **What's the separation-of-duties mechanism for prod deploys in GitHub Actions?**
    <details><summary>Answer</summary>Environment "Allow self-review = no" + Required Reviewers (different from the author). The person who merged the PR can't also be the one approving the prod deploy. Captured in deployment history.</details>
