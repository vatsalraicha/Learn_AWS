# 56 — Capital One DevOps deep dive (companion to CAPITAL_ONE.md)

> *"Synthesizing all 55 prior modules into the Capital One reality. The end-to-end picture."*

## Why this module exists

The synthesis. We've covered Git, GitHub, Actions, GHAS, Jenkins, AWS deploy, MLOps, AI tooling. This module shows how they compose at Capital One specifically — the published facts + the inferences a Sr Lead candidate should make.

For the standalone dossier, see [`CAPITAL_ONE.md`](CAPITAL_ONE.md). This module is the "what to do with it" lens.

---

## 1. The five public anchors

These are documented facts about Capital One's tech stack (sources in [`CAPITAL_ONE.md`](CAPITAL_ONE.md)):

1. **100% AWS** — last on-prem DC closed November 2020 (first major US bank to fully migrate).
2. **Jenkins-based singular delivery pipeline** — InnerSource pattern; 7,000 engineers, 500k+ pipelines, 50k builds/day.
3. **Open-source: Hygieia + Cloud Custodian** — DevOps dashboard + AWS policy-as-code; latter delivered 25% AWS resource reduction.
4. **Trunk-based development + feature flags** — DORA case study; 20× release-frequency improvement reported.
5. **MLOps on Step Functions + SageMaker + EKS-KServe** — published architecture; Step Functions is the orchestration spine, SageMaker for managed ML, KServe for self-hosted model serving.

Everything else is inferred from public job postings, re:Invent talks, and standard regulated-finance patterns.

---

## 2. The implied stack (high confidence)

- **Source**: GitHub Enterprise Cloud
- **Identity**: SAML SSO via internal IdP; SCIM provisioning; verified domain `capitalone.com`
- **Branch governance**: Rulesets requiring signed commits + CODEOWNERS + status checks + linear history on `main`
- **CI**: Jenkins (legacy + active) + GitHub Actions (newer workloads); both on EKS-based ephemeral agents
- **CI shared logic**: central InnerSource Jenkins shared library (`c1-pipeline`-style) + GitHub Actions reusable workflows in central `workflows-org` repo
- **Self-hosted CI runners**: ARC on EKS for Actions (in-VPC builds); K8s-provisioned Jenkins agents for Jenkins
- **Cloud auth**: OIDC for GitHub Actions → AWS; IRSA for Jenkins agents on EKS
- **Container registry**: ECR (per-account)
- **Deploy targets**: ECS, EKS+KServe, Lambda, SageMaker endpoints
- **IaC**: CDK heavily (per re:Invent 2024); CloudFormation; some Terraform
- **Runtime governance**: Cloud Custodian on cron in every account; SCPs at org level
- **Security**: GHAS (Code Security + Secret Protection); CodeQL; Dependabot; Artifact Attestations
- **AI dev tools**: Copilot Business/Enterprise; Claude Code Enterprise (DEI team owns governance)
- **Observability**: Splunk for audit logs; Datadog likely for app metrics; CloudWatch for AWS
- **Model platform**: SageMaker Model Registry + MLflow Tracking + Feature Store; SR 11-7 compliance via separation of duties + immutable audit

---

## 3. The end-to-end CI/CD shape

For a new ML service "fraud-detector-v3":

```
Engineer creates branch fix/JIRA-12345
   │
   │ commits + signs
   ▼
Push to GitHub
   │
   │ webhook ──► Jenkins multibranch (or Actions reusable workflow)
   │
   ▼
CI runs:
   ├─ Lint + test + type-check (pre-commit grade)
   ├─ CodeQL + secret scan (GHAS)
   ├─ Dependency review (GHAS)
   ├─ Model validation (fairness, bias, drift) — bank-required for ML PRs
   ├─ Build + push image to ECR (with SLSA L3 attestation)
   └─ Post status to GitHub PR
   │
   ▼
PR review:
   ├─ CODEOWNERS routes to @ml-platform + @model-validation (for /models/**)
   ├─ Required Reviewer rule: @security-team for sensitive paths
   ├─ 2 approvals required + signed commits verified + conversation resolution
   └─ Merge to main (squash)
   │
   ▼
Main-branch CI:
   ├─ Trigger training pipeline (SageMaker Pipeline)
   ├─ Trained model → registered in SageMaker Model Registry as "PendingApproval"
   ├─ MRM team notified via Slack + ServiceNow CHG ticket
   └─ MRM independent validation → "Approved" in registry
   │
   ▼
CD pipeline triggers (EventBridge on registry approval → repository_dispatch):
   ├─ Deploy to staging (auto, with smoke test)
   ├─ Shadow deploy to prod (no user impact)
   ├─ Bake 24-48h, analyze metrics
   ├─ Canary (5% traffic) — environment 'prod-canary', 1 reviewer
   ├─ Bake 30 min, check SLOs
   ├─ Full rollout — environment 'prod', 2 reviewers (separation of duties)
   └─ Archive old model in registry
   │
   ▼
Post-deploy:
   ├─ Champion/challenger metrics tracked (SageMaker Model Monitor)
   ├─ Drift detection alerts to ml-on-call PagerDuty
   ├─ Auto-rollback Lambda if regression detected
   └─ Audit trail: GitHub + Jenkins + CloudTrail + SageMaker + SIEM
```

Years later, an audit asks for the full chain — every step is traceable from any starting point.

---

## 4. The InnerSource culture

Capital One's "Open Source Office" (founded 2015) governs internal open-source and InnerSource. Principles:

- **All internal repos searchable** across the org (with read access defaulting to all engineers)
- **Open contribution** via PR; ownership via CODEOWNERS
- **Curated reuse** — central shared libraries are InnerSource'd, contributed to by any team
- **Open source where appropriate** — Hygieia + Cloud Custodian as examples

For you as a Sr Lead: your team's shared utilities should be InnerSource'd. Your team should also be active consumers + contributors to other teams' shared libraries. The "I'll just rebuild it" instinct is anti-pattern.

---

## 5. The Jenkins → Actions migration arc

Capital One isn't abandoning Jenkins. But for greenfield work, Actions is increasingly viable.

| Workload | Likely path |
|---|---|
| Legacy services with complex Jenkinsfiles | Stay on Jenkins |
| New microservices | GitHub Actions with reusable workflows |
| ML training pipelines | SageMaker Pipelines + Step Functions; orchestration via either |
| InfraOps (CDK/CFN deploys) | GitHub Actions (cleaner GitOps story) |
| Long-running training | Jenkins (better long-job UX) |
| GPU-heavy work | ARC on EKS (new) or Jenkins K8s agents (existing) |

Your role as Sr Lead: pick the right tool per workload. Don't be religious. Migration is opportunistic; don't move things just to move them.

---

## 6. The DEI team for AI tooling

Capital One reportedly has a Developer Experience & Innovation team responsible for evaluating + governing enterprise AI dev tools. They:
- Procure licenses (Copilot Enterprise, Claude Code Enterprise, others)
- Configure org-level governance (content exclusion, SSO, audit log streaming)
- Maintain approved-tool list + restricted-tool list
- Run annual responsible-AI training
- Field requests for new tool evaluations
- Publish usage metrics + ROI

You partner with DEI for any AI-tool needs your team has. Don't go rogue with personal accounts of unapproved tools. See [module 55](55_ai_governance_privacy.md).

---

## 7. The hiring signal — what they're testing

When they interview you for Sr Lead AI/ML Engineer, the GitHub/DevOps questions probably cover:

1. **"Walk me through your team's CI/CD."**
   - Right answer: trunk-based + small PRs + required CI + signed commits + CODEOWNERS + OIDC + separation of duties for prod. Doesn't matter if Actions or Jenkins — the discipline matters.

2. **"How do you handle secrets in your pipeline?"**
   - Right answer: OIDC + IRSA — no long-lived AWS credentials. Per-environment role scoping. Secrets Manager for things not IAM-able.

3. **"How would you deploy a new model to prod?"**
   - Right answer: registry-promotion flow with MRM approval gate; shadow → canary → ramp → full; auto-rollback on regression; full audit trail.

4. **"What's your view on AI coding assistants in a regulated environment?"**
   - Right answer: useful with governance; human review non-negotiable; partner with DEI; SOC 2 Type II + content exclusion + audit logs as table stakes.

5. **"How do you keep your team's CI consistent with the org's standards?"**
   - Right answer: reference reusable workflows / shared libraries from the central org repo; InnerSource any improvements upstream; org-level Rulesets enforce policy.

6. **"What's SR 11-7 and how does it affect your ML pipeline?"**
   - Right answer: per [module 37](37_compliance_sr117_audit.md). Specifics on three lines of defense, separation of duties, immutable audit, rollback capability.

7. **"You're the new lead of a team using Git Flow + long-lived branches. How do you transition to trunk-based?"**
   - Right answer: fast CI first; feature flags infrastructure; cultural change (small PRs, daily integration); enforce via branch protection + Rulesets; ~3-6 months.

---

## 8. The cross-references

This entire module is a synthesis. Specific references:

- Branch governance → [module 11](11_branch_protection_rulesets_codeowners.md)
- OIDC + AWS → [module 29](29_actions_oidc_aws.md), [module 46](46_aws_oidc_trust_policy_deep.md)
- Self-hosted CI on K8s → [module 28](28_actions_self_hosted_arc_gpu.md)
- Reusable workflows + composite actions → [module 26](26_actions_reusable_workflows.md), [module 27](27_actions_composite_custom.md)
- Jenkins shared libraries → [module 50](50_jenkins_multibranch_shared_libs.md)
- The Jenkins → Actions handoff → [module 51](51_jenkins_credentials_ghaws.md)
- GHAS (secret scanning, CodeQL, Dependabot, SBOM/SLSA) → [modules 32–35](32_ghas_secret_scanning.md)
- Audit + compliance → [module 36](36_compliance_sso_scim_audit.md), [module 37](37_compliance_sr117_audit.md)
- ML pipeline + SR 11-7 → [modules 41–45](41_mlops_ci_for_ml.md)
- AWS deploy patterns → [modules 46–48](46_aws_oidc_trust_policy_deep.md)
- AI dev tools governance → [module 55](55_ai_governance_privacy.md)
- Dossier → [`CAPITAL_ONE.md`](CAPITAL_ONE.md)

---

## 9. The companion file

[`CAPITAL_ONE.md`](CAPITAL_ONE.md) — read it before any interview. The standalone dossier covers:
- Strategic posture + history
- Public scale numbers
- The Singular Software Delivery Pipeline pattern
- Hygieia + Cloud Custodian
- Trunk-based + feature flags
- The implied GitHub posture
- The Jenkins → GitHub → AWS handoff
- Interview-question preparation

---

## 10. The Sr Lead's mindset

Capital One has lived the cloud-native journey at scale longer than any other regulated US bank. They expect Sr Leads to have internalized:

- Discipline that comes from running cloud-native at scale through a 2019 breach
- The InnerSource ethos — many teams contribute, ownership is curated
- Pragmatism over religion — Jenkins AND Actions; SageMaker AND EKS; AWS-only without apology
- Compliance-as-code — controls embedded in pipelines, not on top
- "Boring" reliability — sophisticated patterns rendered routine via automation

If you internalize these five threads, you'll speak their language naturally in interviews. The technical specifics in Topic 07 are the vocabulary. This ethos is the grammar.
