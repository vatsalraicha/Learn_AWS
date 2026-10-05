# Quiz 05 — Jenkins + Apps + AI assistants + Capital One + Certs (Parts L–O)

Covers modules 49–57.

---

## Section 1 — Jenkins (modules 49–51)

1. **What's the difference between declarative and scripted Jenkinsfile?**
   <details><summary>Answer</summary>Declarative: `pipeline { ... }` block; structured (stages, steps); lintable; covers 90% of needs; the default for new code. Scripted: Groovy script with `node { ... }`; full programming language but unstructured; legacy or edge cases requiring complex logic.</details>

2. **What's a Jenkins shared library and how is it invoked?**
   <details><summary>Answer</summary>A Git repo with `vars/` (callable steps) + `src/` (Groovy classes) + `resources/` (bundled files). Invoked from Jenkinsfile via `@Library('lib-name@ref') _` — ref can be branch, tag, or SHA.</details>

3. **What's a multibranch pipeline?**
   <details><summary>Answer</summary>A Jenkins job that auto-discovers branches AND PRs from a Git repo, creating a sub-job per. Reads `Jenkinsfile` from each branch. Triggered by webhooks or polling. The pattern for "every push/PR runs CI."</details>

4. **What's IRSA in the context of Jenkins?**
   <details><summary>Answer</summary>IAM Roles for Service Accounts on EKS. Jenkins agent pods use a K8s ServiceAccount annotated with an IAM role ARN; AWS SDK auto-assumes that role. No long-lived AWS credentials in Jenkins credentials store. The OIDC-equivalent for Jenkins → AWS.</details>

5. **In a Jenkinsfile, what's `withCredentials` for?**
   <details><summary>Answer</summary>Scopes credentials to a block; auto-injects as env vars; auto-masks values in logs; auto-cleans on block exit. Standard pattern for credential usage instead of baking into Jenkinsfile.</details>

6. **What's Capital One's "singular software delivery pipeline" pattern?**
   <details><summary>Answer</summary>One centrally-maintained pipeline pattern (Jenkins shared library; modern equivalent: GitHub Actions reusable workflows) consumed by all teams via short Jenkinsfiles (10-30 lines). All security/compliance gates baked into the library; teams can't skip them because they ARE the pipeline. Bug fix → bump library version → every consumer gets it.</details>

---

## Section 2 — GitHub Apps + automation (module 52)

7. **What's a GitHub App vs an OAuth App?**
   <details><summary>Answer</summary>GitHub App = its own identity (bot); installable per-repo or org-wide; 1-hour installation tokens; better permission scoping. OAuth App = acts as a user; long-lived tokens; legacy. Use GitHub Apps for new automation.</details>

8. **When should you prefer GraphQL over REST for the GitHub API?**
   <details><summary>Answer</summary>For complex cross-resource queries (e.g., "all PRs across all repos in an org with their reviewers"). GraphQL fetches in one request what would be N+M+K REST calls. Use REST for simple single-resource calls.</details>

9. **What's the rate limit for a GitHub App installation token?**
   <details><summary>Answer</summary>5,000 requests/hr per installation. Multiple installations = scales linearly. Much better than PAT 5,000/hr per user.</details>

---

## Section 3 — AI dev tools (modules 53–55)

10. **What changes in GitHub Copilot billing on June 1, 2026?**
    <details><summary>Answer</summary>Usage-based billing via "AI Credits." Every plan includes a monthly credit allotment; paid plans can buy more. Token consumption (input + output + cached) metered per model. Code completions + Next Edit Suggestions remain unmetered. Copilot code review starts consuming Actions minutes.</details>

11. **What's the Copilot Enterprise differentiator over Business?**
    <details><summary>Answer</summary>Codebase indexing for org-tailored suggestions, custom fine-tuned models, Copilot in github.com Chat, knowledge bases, custom org-level instructions. Both have content exclusion + IP indemnity + admin controls + audit logs.</details>

12. **What's a `CLAUDE.md` (or `AGENTS.md`) file at the root of a repo for?**
    <details><summary>Answer</summary>Context for AI coding agents — code style, testing approach, things to avoid, naming conventions. Read at session start. Reduces friction (no need to repeat in every prompt) and enforces team norms.</details>

13. **What's MCP and what does it solve?**
    <details><summary>Answer</summary>Model Context Protocol — Anthropic-pioneered standard for connecting LLMs to external tools and data. MCP servers expose capabilities (GitHub, Slack, DBs, custom) to AI agents. Replaces ad-hoc custom integrations with a standardized protocol.</details>

14. **What are the four risk dimensions for AI dev tools at a bank?**
    <details><summary>Answer</summary>Data leakage (where does our code go?), IP risk (could AI suggest IP-encumbered code?), quality (could AI introduce bugs/vulns?), compliance (does usage satisfy SR 11-7, fair lending, etc.?). Each requires specific mitigations (content exclusion, IP indemnity, mandatory review, audit log).</details>

15. **What's Capital One's "DEI" team responsible for in this context?**
    <details><summary>Answer</summary>Developer Experience & Innovation. Owns enterprise governance of AI dev tools: license procurement, SSO + audit log integration, content exclusion configuration, approved-tool list, annual responsible-AI training, ROI tracking.</details>

---

## Section 4 — Capital One synthesis (module 56)

16. **What's the published scale of Capital One's CI/CD platform?**
    <details><summary>Answer</summary>~7,000 engineers, >500,000 Jenkins pipelines, ~50,000 build/test/deploy actions per day. (Source: CloudBees + Sonatype talks.)</details>

17. **What two open-source projects has Capital One released that matter for this role?**
    <details><summary>Answer</summary>**Hygieia** (2015, OSCON) — DevOps dashboard. **Cloud Custodian** (2016, AWS Summit; now CNCF Incubating) — YAML-based AWS policy-as-code; delivered 25% AWS resource reduction at C1.</details>

18. **What's the DORA case study Capital One is cited for?**
    <details><summary>Answer</summary>Trunk-based development + feature flags adoption. Reported 20× release-frequency improvement without production incidents.</details>

19. **When was Capital One's last on-prem data center closed?**
    <details><summary>Answer</summary>November 2020. First major US bank to complete full public cloud migration.</details>

---

## Section 5 — Certifications (module 57)

20. **What's the recommended cert ladder for a Sr Lead AI/ML Engineer at Capital One?**
    <details><summary>Answer</summary>(1) AWS SA Associate (table stakes), (2) AWS ML Specialty (role fit), (3) GitHub Actions GH-200 (CI/CD), (4) GitHub Advanced Security GH-500 (bank-relevant), (5) AWS DevOps Engineer Pro, (6) CKA (if heavy EKS), (7) Jenkins CJE (Capital One specific), (8) GitHub Foundations GH-900 (easy win).</details>

21. **What's the duration and pass rate for the GitHub Actions GH-200 exam?**
    <details><summary>Answer</summary>100 minutes, pass = 70%, $99 USD. Skills updated January 2026.</details>

22. **How is GitHub Foundations (GH-900) structured?**
    <details><summary>Answer</summary>75 scored + 10-15 unscored questions in 120 minutes, 70% pass, $99 (often -50% promo). Entry-level cert covering repos, branches, PRs, Issues, Actions intro, Pages, security basics, account/billing, Markdown.</details>
