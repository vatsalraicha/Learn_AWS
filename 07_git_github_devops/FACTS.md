# Topic 07 — FACTS.md (Git, GitHub & DevOps)

> Atomic, citable facts. One fact per line, citation in square brackets, last-verified date.
>
> **Last updated:** 2026-05-21

---

## Git core

- **Git** initially released **April 7, 2005** by Linus Torvalds for Linux kernel development. [Source: git-scm.com history] [Verified 2026-05-21]
- **Git 2.54.0** released **April 20, 2026** — most recent stable as of this writing. [Source: github.blog/open-source/git] [Verified 2026-05-21]
- **Git 3.0** targeted for **late 2026**. Headline change: **default hash algorithm switches from SHA-1 to SHA-256**. SHA-256 support has been opt-in since 2.29 (Oct 2020); blocker is GitHub still not supporting SHA-256 repos. [Source: deployhq.com/blog/git-3-0; lwn.net coverage] [Verified 2026-05-21]
- **SHA-1 weakness**: Shattered (CWI/Google, 2017) demonstrated practical collision; Shambles (2020) extended to chosen-prefix collisions. Git mitigates with `SHA-1DC` (collision-detecting). [Source: shattered.io] [Verified 2026-05-21]
- **Reftable** — compressed ref storage format replacing packed-refs / loose-refs. Shipped in 2.48 (Jan 2025); production-ready 2.51. Speeds up repos with millions of refs. [Source: lwn.net 2025; git release notes] [Verified 2026-05-21]
- **Default branch name** for new repos changed from `master` to `main` in Git 2.28 (Jul 2020) via `init.defaultBranch` config. [Source: git release notes 2.28] [Verified 2026-05-21]
- **Sparse checkout v2 (cone mode)** GA in 2.27 (Jun 2020); supports massive monorepos by checking out only specified subtrees. [Source: git release notes] [Verified 2026-05-21]

## Git object model

- Git stores 4 object types: **blob** (file content), **tree** (directory listing), **commit** (snapshot pointer + metadata), **tag** (annotated tag). Each object identified by SHA-1 hash of its content. [Source: git-scm.com/book/en/v2/Git-Internals-Git-Objects] [Verified 2026-05-21]
- **Refs** are pointers to commits, stored as text files under `.git/refs/` (or in the reftable). `HEAD`, `refs/heads/<branch>`, `refs/remotes/<remote>/<branch>`, `refs/tags/<tag>`. [Source: git-scm.com Pro Git ch10] [Verified 2026-05-21]
- **Reflog** records every change to `HEAD` and branch refs for **90 days** by default (configurable `gc.reflogExpire`). Recovery tool of last resort. [Source: git-scm.com docs] [Verified 2026-05-21]
- **Pack files** consolidate loose objects via delta compression — triggered by `git gc`; key for repo size on large histories. [Source: git-scm.com Pro Git ch10] [Verified 2026-05-21]

## GitHub platform — 2025–2026 timeline

- **GitHub Advanced Security (GHAS) unbundled** on **April 1, 2025** into two standalone SKUs: **GitHub Secret Protection** ($19/active committer/mo) + **GitHub Code Security** ($30/active committer/mo). Both now purchasable on Team plan (previously Enterprise-only). [Source: sdtimes.com; github.com/security/plans] [Verified 2026-05-21]
- **Artifact Attestations** GA late 2024 (after public beta). Sigstore-signed; achieve **SLSA v1.0 Build Level 2** out-of-the-box; Level 3 via reusable workflows. [Source: github.com/orgs/community/discussions/129761; github.blog/security] [Verified 2026-05-21]
- **Copilot Autofix for CodeQL** GA **August 14, 2024**. On by default with CodeQL — no separate toggle. [Source: github.blog/changelog/2024-08-14] [Verified 2026-05-21]
- **Required Reviewer rule for Repository Rulesets** GA **February 17, 2026**. Supports `!` negation patterns. [Source: github.blog/changelog/2026-02-17] [Verified 2026-05-21]
- **GitHub Copilot pricing (2026)**: Free (limited), Pro $10/mo, Pro+ $39/mo, Business $19/user/mo, Enterprise $39/user/mo. [Source: github.com/features/copilot/plans] [Verified 2026-05-21]
- **Copilot usage-based billing** rolls out **June 1, 2026** — AI Credits replace request-based metering. Code completions + Next Edit Suggestions remain free of credits. Copilot Code Review will consume Actions minutes on GitHub-hosted runners from this date. [Source: github.blog/news-insights/company-news; docs.github.com/enterprise-cloud/copilot/reference/copilot-billing] [Verified 2026-05-21]
- **GitHub Actions Security Roadmap 2026** ships: read-only `GITHUB_TOKEN` default in new repos, mandatory action review for first-time contributors, platform-wide attestation support. [Source: github.blog/news-insights/product-news/whats-coming-to-our-github-actions-2026-security-roadmap] [Verified 2026-05-21]

## GitHub Actions limits & defaults

- **GitHub-hosted runner OS images**: ubuntu-22.04, ubuntu-24.04, ubuntu-latest (=24.04 since Jan 2025), windows-2022, windows-2025, macos-13, macos-14, macos-15 (Apple Silicon). [Source: docs.github.com/actions/using-github-hosted-runners] [Verified 2026-05-21]
- **GitHub-hosted runner specs (standard)**: 4 vCPU / 16 GB RAM / 14 GB SSD for Linux & Windows. Larger runners (org-level): 4/8/16/32/64 vCPU options + ARM64 + GPU. [Source: docs.github.com/actions] [Verified 2026-05-21]
- **GPU runners** (private preview turning GA): NVIDIA T4 (Linux) — billed per minute, more than standard. [Source: github.blog Actions roadmap] [Verified 2026-05-21]
- **Free tier minutes (private repos)**: Free 2,000 min/mo, Pro 3,000, Team 3,000, Enterprise 50,000. Public repos always free. macOS = 10× multiplier; Windows = 2× multiplier on minute consumption. [Source: docs.github.com/billing/concepts/product-billing/github-actions] [Verified 2026-05-21]
- **Workflow job timeout** default = **6 hours** (max 35 days on self-hosted). Step has no default timeout. [Source: docs.github.com/actions] [Verified 2026-05-21]
- **Concurrent jobs** (GitHub-hosted): Free 20 (5 macOS), Pro 40 (5 macOS), Team 60 (5 macOS), Enterprise 180 (50 macOS). [Source: docs.github.com/actions/learn-github-actions/usage-limits-billing-and-administration] [Verified 2026-05-21]
- **Artifact retention** default = **90 days** (configurable 1–400 days for org/repo). [Source: docs.github.com/actions/using-workflows/storing-workflow-data-as-artifacts] [Verified 2026-05-21]
- **Reusable workflow nesting**: max **4 levels** deep. [Source: docs.github.com/actions/sharing-automations/reusing-workflows] [Verified 2026-05-21]
- **Composite action steps**: no hard limit, but each step counts toward the 1000-step-per-job cap. [Source: docs.github.com/actions] [Verified 2026-05-21]
- **Workflow file size**: max 1 MB. [Source: docs.github.com/actions usage limits] [Verified 2026-05-21]
- **Matrix max combinations**: 256 jobs per workflow run. [Source: docs.github.com/actions/using-jobs/using-a-matrix-for-your-jobs] [Verified 2026-05-21]
- **GITHUB_TOKEN expires** at end of workflow run; max permissions configurable per workflow/job. New default = read-only (per 2026 roadmap). [Source: docs.github.com/actions/security-guides/automatic-token-authentication] [Verified 2026-05-21]

## OIDC to AWS (Capital One pattern)

- **OIDC provider URL**: `https://token.actions.githubusercontent.com`. **Audience**: `sts.amazonaws.com`. [Source: docs.github.com/actions/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services] [Verified 2026-05-21]
- **Required workflow permission**: `permissions: id-token: write`. [Source: GitHub Docs] [Verified 2026-05-21]
- **Action**: `aws-actions/configure-aws-credentials@v4` is the official action; supports `role-to-assume`, `role-session-name`, `aws-region`, `mask-aws-account-id`. [Source: github.com/aws-actions/configure-aws-credentials] [Verified 2026-05-21]
- **Trust policy condition keys**: `token.actions.githubusercontent.com:sub` (most important — restricts which repo/branch/env can assume) and `token.actions.githubusercontent.com:aud`. **Use `StringEquals` or `StringLike`; never `ForAllValues:*`** (returns true on missing claim → unintended access). [Source: AWS IAM docs; AWS security blog] [Verified 2026-05-21]
- **Sub claim formats**:
  - Branch: `repo:ORG/REPO:ref:refs/heads/main`
  - Tag: `repo:ORG/REPO:ref:refs/tags/v1.2.3`
  - PR: `repo:ORG/REPO:pull_request`
  - Environment: `repo:ORG/REPO:environment:prod`
  - Reusable workflow caller: `repo:ORG/REPO:ref:refs/heads/main:job_workflow_ref:ORG/REUSABLE-REPO/.github/workflows/x.yml@refs/heads/main` [Source: GitHub OIDC docs] [Verified 2026-05-21]
- **Session duration default**: 1 hour; configurable up to role's `MaxSessionDuration` (default 1h, max 12h). [Source: AWS IAM docs] [Verified 2026-05-21]

## Actions Runner Controller (ARC)

- **Current ARC** lives at **`actions/actions-runner-controller`** (GitHub-owned, replaced the community `summerwind/actions-runner-controller`). [Source: github.com/actions/actions-runner-controller] [Verified 2026-05-21]
- **Two Helm charts** (released as OCI artifacts, not tarballs):
  - `oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set-controller`
  - `oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set` [Source: github.com/actions/actions-runner-controller/blob/master/charts/README.md] [Verified 2026-05-21]
- **Architecture**: Listener pod long-polls GitHub Actions Service via HTTPS → patches `EphemeralRunnerSet` CR → JIT runner pods spawned → execute one job → pod deleted. [Source: docs.github.com/actions/concepts/runners/actions-runner-controller] [Verified 2026-05-21]
- **Container modes**: `dind` (Docker-in-Docker, requires privileged) or `kubernetes` (uses container hooks, schedules containers as sibling pods — preferred for security). [Source: ARC docs] [Verified 2026-05-21]
- **JIT runner tokens** retry up to **5 times** on creation failure; jobs unassigned after **24 hours** if no runner claims them. [Source: ARC docs] [Verified 2026-05-21]

## CODEOWNERS & branch protection

- **CODEOWNERS file** lives in `.github/CODEOWNERS`, `CODEOWNERS`, or `docs/CODEOWNERS` (in that search order). [Source: docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners] [Verified 2026-05-21]
- **Syntax**: glob path → `@user` `@org/team` `email@domain.com`. Last matching rule wins. Order matters. [Source: GitHub CODEOWNERS docs] [Verified 2026-05-21]
- **Branch protection rules**: legacy; still supported. **Rulesets**: newer (GA 2023); evaluated additively (multiple rulesets stack), visible to non-admins, support layered policies (org → repo). [Source: docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets] [Verified 2026-05-21]
- **Required signed commits**: a branch protection / ruleset option. Enforces GPG-, S/MIME-, or SSH-signed commits. [Source: GitHub docs] [Verified 2026-05-21]
- **`merge_group` event** for merge queues GA 2023; lets workflows test the queue's tentative commit before merging. [Source: github.blog/changelog merge queue] [Verified 2026-05-21]

## GHAS — Code Security & Secret Protection

- **GitHub Code Security ($30/active-committer/mo)** includes: CodeQL (default + advanced setup), code scanning with third-party SARIF, Copilot Autofix, dependency review, security campaigns. [Source: github.com/security/plans] [Verified 2026-05-21]
- **GitHub Secret Protection ($19/active-committer/mo)** includes: secret scanning (200+ partner patterns), push protection (blocks at push time), AI-powered detection, custom patterns, security insights. [Source: github.com/security/plans] [Verified 2026-05-21]
- **Billing basis**: any contributor who committed to a GHAS-enabled private repo in the last **90 days** counts as an active committer. [Source: docs.github.com/en/billing/concepts/product-billing/github-advanced-security] [Verified 2026-05-21]
- **CodeQL languages supported (2026)**: C/C++, C#, Go, Java/Kotlin, JavaScript/TypeScript, Python, Ruby, Swift, GitHub Actions workflows. [Source: docs.github.com/en/code-security/code-scanning/creating-an-advanced-setup-for-code-scanning/codeql-code-scanning-for-compiled-languages] [Verified 2026-05-21]
- **Default setup vs advanced setup**: default = autodetect languages, run on push/PR; advanced = custom workflow file with full control over queries/triggers. [Source: docs.github.com/code-security] [Verified 2026-05-21]
- **Dependabot tiers**: Alerts (free for public + private with GHAS), Security updates (free), Version updates (free; configured via `.github/dependabot.yml`). [Source: docs.github.com/en/code-security/dependabot] [Verified 2026-05-21]

## Supply chain / SBOM / SLSA

- **SLSA v1.0** specification — 4 build levels: L1 (provenance exists), L2 (signed provenance + hosted build), L3 (hardened build + isolation), L4 (deprecated post-1.0, two-party review). [Source: slsa.dev] [Verified 2026-05-21]
- **GitHub Artifact Attestations** achieve **SLSA L2 by default**; **L3 by using reusable workflows** (isolation between build process and calling workflow). [Source: docs.github.com/actions/security-for-github-actions/using-artifact-attestations] [Verified 2026-05-21]
- **Actions**: `actions/attest@v3`, `actions/attest-build-provenance@v3`, `actions/attest-sbom@v3`. Verify with `gh attestation verify`. [Source: github.com/actions/attest] [Verified 2026-05-21]
- **SBOM formats**: **CycloneDX** (OWASP, security-first) vs **SPDX** (Linux Foundation, legal/license-first). GitHub generates SPDX SBOMs natively via `Dependency Graph → SBOM`. [Source: docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/export-sbom-for-your-repository] [Verified 2026-05-21]
- **EU Cyber Resilience Act** enforcement begins **December 11, 2027** — effectively mandates SBOMs for software sold in the EU. [Source: European Commission CRA timeline] [Verified 2026-05-21]
- **Sigstore** components: `cosign` (signing tool), `Fulcio` (CA), `Rekor` (transparency log). GitHub uses Sigstore Public Good for public repos; dedicated instance (no transparency log) for private. [Source: sigstore.dev; GitHub artifact attestation docs] [Verified 2026-05-21]

## Jenkins

- **Jenkins LTS** release line — new LTS every ~12 weeks; example: 2.452.x (2024), 2.479.x (2025), 2.504.x (early 2026). [Source: jenkins.io/changelog-stable] [Verified 2026-05-21]
- **Declarative Pipeline** released in **pipeline-model-definition 1.0, September 2017**. The recommended modern syntax. [Source: jenkins.io/doc/book/pipeline] [Verified 2026-05-21]
- **Shared Libraries**: defined as Git repos; standard layout: `vars/*.groovy` (callable as global steps), `src/<package>/*.groovy` (Groovy classes), `resources/` (binary files). Referenced via `@Library('name')` or `@Library('name@version')`. [Source: jenkins.io/doc/book/pipeline/shared-libraries] [Verified 2026-05-21]
- **Multibranch Pipeline plugin** + **GitHub Branch Source** plugin auto-discover branches and PRs from a GitHub repo or org. [Source: plugins.jenkins.io/github-branch-source] [Verified 2026-05-21]
- **Credentials Plugin** with scopes: System (whole controller), Global (controller + agents), per-Folder. Best practice: use Folder-scoped + `withCredentials` block (never bake into Jenkinsfile). [Source: plugins.jenkins.io/credentials] [Verified 2026-05-21]

## Capital One — public engineering posture

- **Engineers**: ~7,000 on the Jenkins-based pipeline platform. [Source: CloudBees video "Scaling Jenkins Agents at Capital One"] [Verified 2026-05-21]
- **Jenkins pipelines**: >500,000 automation pipelines. [Source: CloudBees / Sonatype talks] [Verified 2026-05-21]
- **Daily activity**: ~50,000 build/test/deploy executions per day. [Source: CloudBees / Sonatype] [Verified 2026-05-21]
- **AWS resource reduction from Cloud Custodian**: ~25%. [Source: TechCrunch 2016; AWS Summit 2016 talk] [Verified 2026-05-21]
- **Open-source projects**: Hygieia (DevOps dashboard, 2015 OSCON), Cloud Custodian (AWS policy-as-code, 2016 AWS Summit; now CNCF Incubating). [Source: developer.capitalone.com/opensource; CNCF projects list] [Verified 2026-05-21]
- **Cloud posture**: 100% AWS; last on-prem DC closed November 2020 (cross-reference Topic 04 CAPITAL_ONE.md). [Source: C1 press releases] [Verified 2026-05-21]
- **Published CI/CD pattern**: "singular software delivery pipeline" using InnerSource. Jenkins shared libraries are the unit of reuse. [Source: capitalone.com/tech/open-source/innersource-singular-software-delivery-pipeline] [Verified 2026-05-21]
- **Published DORA pattern**: trunk-based development + feature flags; reported 20× release-frequency improvement. [Source: DORA capabilities page; LaunchDarkly case study] [Verified 2026-05-21]

## Certifications

- **GitHub Foundations (GH-900)**: 75 scored questions (+10–15 unscored), 120 min, 70% pass, $99 USD. Updated Jan 2026. [Source: learn.microsoft.com/credentials/certifications/github-foundations] [Verified 2026-05-21]
- **GitHub Actions (GH-200)**: 100 min, $99, skills updated Jan 2026. [Source: Microsoft Learn] [Verified 2026-05-21]
- **GitHub Advanced Security (GH-500)**: 100 min, $99. CodeQL + secret scanning + Dependabot. [Source: Microsoft Learn] [Verified 2026-05-21]
- **GitHub Administration (GH-300)**: enterprise admin focus. $99. [Source: Microsoft Learn] [Verified 2026-05-21]
- **CloudBees Certified Jenkins Engineer (CJE)**: $300 USD; multiple-choice, 90 min; covers pipeline syntax, plugins, security. [Source: cloudbees.com/cje] [Verified 2026-05-21]

## SR 11-7 (model risk) — regulated finance lens

- **SR 11-7** — Federal Reserve Supervisory Letter, **April 4, 2011**. Replaces OCC 2000-16; codifies "model risk management" guidance for US banks. [Source: federalreserve.gov/supervisionreg/srletters/sr1107.htm] [Verified 2026-05-21]
- **Three lines of defense**: 1L = model developers/users; 2L = independent model validation (MRM); 3L = internal audit. [Source: SR 11-7 text; ValidMind blog] [Verified 2026-05-21]
- **Material requirements for AI/ML**: immutable audit trails of training data + code + hyperparameters; reproducible builds; signed artifacts; independent validation report; ongoing performance monitoring; documented assumptions and limitations. [Source: SR 11-7; ModelOp; Abacus] [Verified 2026-05-21]

## AI coding assistants in enterprise

- **GitHub Copilot Business** ($19/user/mo): IDE completions + Chat + content exclusion + IP indemnity + admin controls + audit logs. [Source: docs.github.com/copilot] [Verified 2026-05-21]
- **GitHub Copilot Enterprise** ($39/user/mo): adds codebase indexing for org-tailored suggestions, custom fine-tuned models, Copilot in github.com, knowledge bases, custom instructions at org level. [Source: docs.github.com/copilot] [Verified 2026-05-21]
- **Claude Code Enterprise**: SOC 2 Type II, SSO, role-based permissions, configurable retention, customer prompts not used to train by default, TLS 1.3 / AES-256, BYOK option, HIPAA available. Released as enterprise tier early 2026. [Source: claude.com/product/claude-code/enterprise; anthropic.com/product/enterprise] [Verified 2026-05-21]
- **Cursor for Business**: SOC 2 Type II, Privacy Mode (code not stored on Cursor servers). [Source: cursor.com pricing] [Verified 2026-05-21]
