# Capital One DevOps — Dossier for Sr Lead AI/ML Engineer

> **Audience:** You — preparing for the Sr Lead AI/ML Engineer role at Capital One.
> **Purpose:** A single document to read before an interview / recruiter call / architecture discussion, grounding you in Capital One's GitHub + Jenkins + AWS reality.
> **Companion to:** [Topic 07 modules](README.md) and [Topic 04 CAPITAL_ONE.md](../04_aws_for_ai_ml/CAPITAL_ONE.md).
> **Last updated:** 2026-05-21

---

## Strategic posture in one paragraph

Capital One was the **first major US bank to fully migrate to public cloud** (last on-prem data center closed November 2020). They are AWS-only for production. Their DevOps backbone is **GitHub Enterprise + Jenkins + AWS**, scaled to ~**7,000 engineers**, **500,000+ Jenkins pipelines**, and **~50,000 build/test/deploy executions per day**. Their published delivery model is **the Singular Software Delivery Pipeline** — InnerSource Jenkins shared libraries that every team consumes, with deviation handled via configuration not forking. Their published branching pattern is **trunk-based development with feature flags** (DORA-cited case study with 20× release-frequency improvement). They are heavy users of **CDK** (per re:Invent 2024) and run **KServe on EKS** for self-hosted ML serving alongside SageMaker.

---

## 1. The numbers (publicly cited)

| Metric | Value | Source |
|---|---|---|
| Engineers on the platform | ~7,000 | CloudBees "Scaling Jenkins Agents at Capital One" video |
| Jenkins pipelines | >500,000 | CloudBees / Sonatype talks |
| Build/test/deploy actions/day | ~50,000 | CloudBees / Sonatype |
| AWS resource reduction (Cloud Custodian) | 25% | TechCrunch / AWS Summit 2016 |
| Release frequency improvement (TBD adoption) | 20× | LaunchDarkly / DORA case study |
| Cloud-migration completion | November 2020 (last DC closed) | C1 press releases |

---

## 2. The Singular Software Delivery Pipeline

From their published [Building a Singular Software Delivery Pipeline](https://www.capitalone.com/tech/open-source/innersource-singular-software-delivery-pipeline/):

**Idea**: instead of every team building their own CI/CD, one centrally-maintained pipeline pattern is consumed by all teams.

**Why it works in regulated finance**:
- All security + compliance gates (SAST, SCA, secret scan, license scan, container scan, IaC scan) baked into the central pipeline; teams can't skip the gate because the gate IS the pipeline
- Approved deployment patterns (canary, blue/green, ECS/EKS/Lambda/SageMaker) as library steps; teams configure, don't reinvent
- Audit is easy — same pipeline → same logs schema → same artifact attestation format → same approver chain
- MTTR for security patches drops dramatically (bump one library version → every team picks it up)

**How it's implemented**:
- **Jenkins shared libraries** (Groovy `vars/` + `src/`) referenced via `@Library('c1-pipeline@stable')` in per-team Jenkinsfile
- Each team's `Jenkinsfile` is ~10–30 lines; the library does the heavy lifting
- New steps added via PR to the central library; CODEOWNERS routes review to the platform team
- (Modern equivalent: GitHub Actions reusable workflows in a central `workflows-org` repo)

**Reference module**: [50 — Multibranch + shared libraries](50_jenkins_multibranch_shared_libs.md), [56 — Capital One DevOps deep](56_capital_one_devops_deep.md).

---

## 3. Open-source projects from Capital One

### Hygieia (2015, OSCON release)
- DevOps dashboard — single pane of glass for the SDLC across hundreds of teams
- Captures: source commits, build runs (Jenkins), code quality (SonarQube), security scans, deployments, feature toggles, dependency scans (Nexus IQ)
- Pluggable collector architecture — write a collector once, every team's dashboard benefits
- Repo: [Hygieia/Hygieia](https://github.com/Hygieia/Hygieia)
- **Signal to you**: Capital One's appetite for in-house tooling for cross-team observability — they prefer "one dashboard of dashboards" over per-team rollouts

### Cloud Custodian (2016, AWS Summit release)
- YAML-based **policy-as-code** rules engine for AWS (now multi-cloud)
- Use cases: enforce tagging, kill unused EC2s, encrypt S3 buckets, quarantine non-compliant IAM, schedule dev/test shutdowns
- Now a **CNCF Incubating project** (donated 2023)
- 25% AWS resource reduction at C1 attributed to Custodian
- Repo: [cloud-custodian/cloud-custodian](https://github.com/cloud-custodian/cloud-custodian)
- **Signal to you**: Capital One enforces compliance continuously + automatically — not point-in-time audits

### Capital One Software products (commercial, not OSS)
- **Slingshot** — Snowflake cost governance (launched 2021)
- **Databolt** — vaultless tokenization for Redshift, Aurora, RDS; expanded to **unstructured GenAI data in March 2026**
- **Signal to you**: Capital One Software arm productizes their internal tools — strong indicator of the AWS + Snowflake + Databricks + GenAI stack they actually use

---

## 4. Trunk-based development + feature flags

Capital One is the canonical DORA case study for trunk-based development at scale in regulated finance. Key elements:

- **One main branch.** Feature branches live <24h and are rebased frequently
- **Feature flags decouple deploy from release.** Unfinished features ship to prod behind off-by-default flags
- **Continuous integration** — every PR runs lint + test + security + build
- **Pair on big changes** instead of long-lived feature branches; many small PRs

Reported result: **20× release-frequency improvement, no incidents.**

Reference module: [15 — Branching strategies](15_branching_strategies.md), [16 — Feature flags + InnerSource](16_feature_flags_innersource.md).

---

## 5. The implied GitHub posture (inferred + sourced)

What's publicly confirmed:
- **GitHub Enterprise** is the source-control plane
- **Jenkins** integrated with GitHub via webhooks (multibranch pipelines)
- **InnerSource fork model** internally
- **Configuration as Code** (Chef + Ansible, version-controlled, InnerSource changes)

What you should assume but verify in onboarding:
- **SAML SSO + SCIM** via internal IdP (standard for any enterprise)
- **Rulesets** (or branch protection) requiring signed commits + CODEOWNERS + status checks + linear history on `main`
- **CODEOWNERS** at scale, routing reviews to SMEs
- **GHAS (Code Security + Secret Protection)** licensed — virtually certain at this scale
- **GitHub Copilot Business or Enterprise** — Capital One's DEI team owns governance
- **Self-hosted runners** likely ARC on EKS for VPC-only / GPU workloads
- **Audit log streaming** to Splunk / SIEM

Reference modules: [11](11_branch_protection_rulesets_codeowners.md), [12](12_auth_pat_ssh_signing.md), [28](28_actions_self_hosted_arc_gpu.md), [32–35](32_ghas_secret_scanning.md), [36](36_compliance_sso_scim_audit.md).

---

## 6. The Jenkins → GitHub → AWS handoff

```
GitHub PR
   │
   ├─ Status checks (CodeQL, Dependabot, secret scan) ──► PR can't merge until green
   │
   ├─ Webhook ──► Jenkins Multibranch pipeline
   │                  │
   │                  ├─ Shared library: cls.lint() / cls.test() / cls.scan() / cls.build()
   │                  ├─ Artifact published to Artifactory / ECR
   │                  └─ Notify back to PR with status check
   │
   ▼
Merge to main (signed, squash)
   │
   ├─ Jenkins ──► deploy via library: cls.deployToEcs() / cls.deployToLambda() / cls.deploySagemaker()
   │                  │
   │                  └─ Uses IRSA (Jenkins-on-EKS) or OIDC (Actions) → per-env AWS role assumption
   │
   └─ Cloud Custodian runs in target account on cron, enforcing policy continuously
```

For ML specifically:
- Notebook in repo → CI strips outputs (nbstripout) + tests via nbmake/jupytext
- Trained model artifact registered in **SageMaker Model Registry** (PendingApproval)
- MRM team independent validation → Approved
- Promotion gate (manual approval + bias/drift/fairness check) → Step Functions deploys to SageMaker endpoint
- Shadow → champion/challenger → full cutover (per [module 44](44_mlops_champion_challenger.md))

Reference modules: [49–51](49_jenkins_architecture_jenkinsfile.md), [29](29_actions_oidc_aws.md), [42–45](42_mlops_validation_gates.md).

---

## 7. The compliance overlay (SR 11-7)

For every ML model deployed:
- Signed commits
- CODEOWNERS-routed PR review (1L)
- MRM independent validation in SageMaker Model Registry (2L)
- Separation of duties on prod deploy (author ≠ approver)
- Immutable audit trail (GitHub audit log + Jenkins logs + CloudTrail + Registry + SIEM)
- SLSA Build Level 3 attestation on artifacts (signed via OIDC/Sigstore)
- Kill switch / rollback workflow tested quarterly

Reference module: [37 — SR 11-7](37_compliance_sr117_audit.md).

---

## 8. What this means for your interview

Likely questions + good answers:

### "Walk me through how you'd add a new ML service to the pipeline."

> "I wouldn't reinvent CI/CD — I'd extend the existing shared library (or reusable workflow) with the new deployment target. New service repo from the InnerSource template; pyproject.toml + Dockerfile; Jenkinsfile that calls cls.standardCI() + cls.deploySagemaker(). PR review routes via CODEOWNERS. CI runs gates including model validation. Trained model registers in SageMaker Model Registry as PendingApproval. MRM independent validation. On approval, Step Functions promotes through staging → shadow → canary → full. Audit trail captured at every step."

### "How do you handle secrets for a SageMaker training job triggered from CI?"

> "OIDC for GitHub Actions or IRSA for Jenkins agents — no long-lived AWS keys. Role scoped per environment via OIDC sub-claim (`repo:capitalone/cool:environment:prod`). For things not IAM-able (Snowflake key-pair, third-party API tokens), AWS Secrets Manager with the role having `secretsmanager:GetSecretValue` on specific secret ARNs only. Pre-commit hook + GHAS Secret Protection catch any accidental commits of credentials."

### "How do you keep trunk green?"

> "Pre-merge: required status checks (lint, test, security, build, model validation). Required PR review with CODEOWNERS. Required signed commits. Feature flags for unfinished features. Concurrency cancellation in CI saves duplicate-run waste. Short-lived branches (<24h) with daily rebase. Pair-program on architectural changes instead of long feature branches. Merge queues for high-traffic repos to prevent semantic conflicts."

### "Explain the SR 11-7 implications of your model deployment pipeline."

> "Three lines of defense at the CI/CD level: 1L is the engineer's CODEOWNERS-approved PR with passing validation gates. 2L is MRM independent validation as a registry-promotion gate. 3L is internal audit, served by the immutable trail in GitHub + CloudTrail + SIEM. Separation of duties: PR author can't approve their own prod deploy via Environment 'self-review = no'. Every artifact has a signed SLSA L3 attestation. Rollback workflow tested quarterly. Model card updated each retraining."

### "What would you change about Capital One's stack?"

> "Respect the constraints — 500k Jenkins pipelines aren't moving to Actions overnight, nor should they. But for greenfield ML services, GitHub Actions with OIDC + ARC on EKS gives faster developer feedback than spinning up new Jenkins pipelines. I'd treat it as opportunistic migration: new work goes to Actions; existing Jenkins stays. The shared-library pattern is identical in spirit (Jenkins library vs reusable workflows) so the InnerSource culture transfers."

---

## 9. The "boring" reliability frame

Capital One has been doing cloud-native at scale longer than nearly any regulated US bank. They expect Sr Leads to have internalized:

- Discipline that comes from running production cloud at scale + going through a 2019 breach
- InnerSource ethos — many teams contribute, ownership is curated
- Pragmatism over religion — Jenkins AND Actions; SageMaker AND EKS; AWS-only without apology
- Compliance-as-code — controls embedded in pipelines, not on top
- "Boring" reliability — sophisticated patterns rendered routine via automation

Speak in this frame and you sound like one of them.

---

## 10. Sources

The factual claims trace to public material:

- [Capital One — Building a Singular Software Delivery Pipeline](https://www.capitalone.com/tech/open-source/innersource-singular-software-delivery-pipeline/)
- [Capital One — Centrally Orchestrated Software Pipelines](https://www.capitalone.com/tech/software-engineering/benefits-of-a-centrally-orchestrated-software-delivery-pipeline/)
- [Capital One — InnerSourcing for Enterprise Applications](https://www.capitalone.com/tech/open-source/innersourcing-enterprise-applications/)
- [CloudBees — Scaling Jenkins Agents at Capital One](https://www.cloudbees.com/videos/jenkins-agent-capital-one)
- [Sonatype — How Capital One Automates Automation Tools](https://www.sonatype.com/blog/how-capital-one-automates-automation-tools)
- [TechCrunch — Capital One open sources Cloud Custodian](https://techcrunch.com/2016/04/19/capital-one-open-sources-cloud-custodian-aws-resource-management-tool/)
- [DevExchange — Hygieia](https://developer.capitalone.com/opensource-projects/hygieia/)
- [DORA — Trunk-based development](https://dora.dev/capabilities/trunk-based-development/)
- [LaunchDarkly — Elite Performance with Trunk-based Development](https://launchdarkly.com/blog/elite-performance-with-trunk-based-development/)
- [Cross-reference: Topic 04 CAPITAL_ONE.md](../04_aws_for_ai_ml/CAPITAL_ONE.md) — AWS-side dossier
