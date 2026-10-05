# 37 — 🏦 SR 11-7 + immutable audit trails + separation of duties for ML deployments

> *"SR 11-7 is the Federal Reserve's model-risk supervisory letter. It governs every ML model in production at every US bank. The CI/CD implication: every model promotion must be approved, attested, and reconstructible years later."*

## Why this module exists

The bank-specific overlay on everything in Topic 07. The technical patterns (signed commits, attestations, environment approvals) are the *implementation* of SR 11-7 / model-risk management requirements. This module makes the regulator → code mapping explicit so you can speak fluently in interviews about "how would you make your ML pipeline SR 11-7 compliant?"

---

## 1. SR 11-7 — what it is

- **Supervisory Letter SR 11-7** — issued by the Federal Reserve Board on **April 4, 2011**.
- **Subject**: Guidance on Model Risk Management.
- **Applies to**: every US bank holding company and supervised institution.
- **Scope**: any quantitative model used in business decisions — credit scoring, fraud detection, AML, market risk, capital reserves, ALM, deposit-flow forecasting, marketing targeting, etc.
- **Modern ML scope**: explicitly includes machine learning models per subsequent OCC guidance.

The letter is short (~21 pages). It articulates three core principles:
1. **Sound model development, implementation, and use.**
2. **Effective model validation** — independent review of every material model.
3. **Robust governance** — policies, procedures, oversight, controls.

The structure: **three lines of defense** (1L = model developers/users; 2L = model risk management / independent validation; 3L = internal audit).

For your role as a Sr Lead AI/ML Engineer at Capital One:
- You're 1L (you develop + use models).
- 2L challenges your work (MRM team independently validates).
- 3L audits the process.
- The CI/CD pipeline is the evidence machine that lets 2L and 3L verify your work *years later*.

---

## 2. What SR 11-7 demands from a CI/CD pipeline

The letter doesn't say "thou shalt use GitHub Actions." It says (paraphrased):

| SR 11-7 principle | CI/CD translation |
|---|---|
| Documented model development | ADRs + model cards in repo; signed commits |
| Data lineage tracked | Lineage attestations; SBOM-equivalent for training data |
| Model code immutable + reproducible | Signed artifact attestations; deterministic builds where feasible |
| Independent validation gate | Separate environment with required reviewer (the MRM team) |
| Change-control over deployments | GitHub Environment manual approval; CloudTrail logs |
| Separation of duties | Author ≠ approver; CODEOWNERS + Required Reviewer rules; environment self-review disabled |
| Ongoing monitoring | Drift detection wired to alerts; champion/challenger metrics tracked |
| Override / kill switch | Feature flag for instant model disable; rollback workflow tested |
| Auditable history forever | Audit log streamed to SIEM; long-term retention beyond GitHub's 6 months |

---

## 3. The minimum viable SR 11-7 model pipeline (sketch)

```
1. Engineer makes a model change in a PR
   ├─ CODEOWNERS routes review to @ml-team
   ├─ Required Reviewer rule routes review to @model-validation (MRM) for `/models/**`
   ├─ Required CI checks: lint + test + model-validation (fairness, bias, drift)
   ├─ Signed commits enforced
   └─ Conventional Commits enforced

2. PR merged to main (squash)
   ├─ Audit log: merge by alice; verified signed; 2 approvals (bob, carol)
   ├─ Audit log: model-validation status check = passed
   └─ Triggers training pipeline

3. SageMaker training pipeline runs
   ├─ Reads training data from S3 (versioned + lineage-attested)
   ├─ Trains model
   ├─ Runs validation suite (offline metrics, fairness, bias)
   ├─ Registers in SageMaker Model Registry as "PendingApproval"
   └─ Generates SLSA Build Level 3 attestation for model artifact

4. MRM team independent validation
   ├─ Reads validation report
   ├─ Runs their own challenge tests
   ├─ Approves "Approved" in SageMaker Model Registry (or rejects)
   └─ Audit log captures approver identity + timestamp

5. Deploy to production (GitHub Actions workflow)
   ├─ Job has `environment: prod` (manual approval required)
   ├─ Required approver: SRE team (NOT the model author — separation of duties)
   ├─ OIDC + IAM role scoped to "prod-model-deployer" trust
   ├─ Updates SageMaker endpoint to point to approved model version
   ├─ CloudTrail logs the UpdateEndpoint call
   └─ Audit log + Deployment history captures full chain

6. Production monitoring
   ├─ Real-time drift detection on input distribution + predictions
   ├─ Fairness metrics tracked per protected group
   ├─ Alerts to model-on-call when SLO breaches
   └─ Rollback workflow tested in chaos drills, executable in <5 min

7. Years later, an audit asks "show me the model that was running on 2026-08-12 at 14:00 UTC for endpoint X"
   ├─ Query SageMaker Model Registry: which version was active at that time
   ├─ Query the registry entry: source commit SHA Y, training data ID Z
   ├─ Verify artifact attestation: provenance signed by workflow run W
   ├─ Query GitHub: PR that contained SHA Y, who reviewed, who approved deploy
   └─ Query CloudTrail: who called UpdateEndpoint, when, from which role
   → Full reconstruction. SR 11-7 satisfied.
```

---

## 4. Separation of duties — the operational meaning

Separation of duties = "no single person can move a model from development to production unilaterally."

In practice:
- **Code author** writes the change.
- **Code reviewer** (different person, from CODEOWNERS) approves the PR.
- **MRM validator** (different team) independently validates the model.
- **Deploy approver** (different from above three) approves the prod deploy.

GitHub mechanisms:
- CODEOWNERS for routing
- Required Reviewer ruleset rule with `!self-review` (newer feature)
- Environment "Allow self-review = no"
- Required reviewers on `prod` environment

Audit evidence: the chain of identities at each gate, captured in audit log + deployment history.

**Anti-pattern**: a single SRE who reviews ML PRs, approves model registry entries, AND approves prod deploys. Same person doing all three = no separation. Hire / staff so the responsibilities are split.

---

## 5. Immutable audit trail

SR 11-7 doesn't say "use Git." It says "be able to reconstruct any model state at any point in time."

Git commits are immutable (content-addressed). Signed commits are tamper-evident. The pieces:

- **Code state**: signed commit SHA at deploy time
- **Build state**: artifact attestation (provenance)
- **Data state**: snapshot ID of training data (versioned in S3 + cataloged in Glue/Unity)
- **Environment state**: CDK/CloudFormation deployed at the time (also tagged)
- **Decision metadata**: who approved, when, with what comment

Captured in:
- GitHub (commits, PRs, environments, audit log)
- SageMaker Model Registry (model version metadata)
- AWS CloudTrail (every API call, who called it)
- Your SIEM (long-term retention)

Cross-referenced via:
- The audit-log streaming setup ([module 36](36_compliance_sso_scim_audit.md))
- Tags carrying `commit_sha` + `pipeline_run_id` on every AWS resource

---

## 6. Override / kill switch

SR 11-7 expects you to have a way to instantly disable a misbehaving model. Options:
- **Feature flag** (LaunchDarkly / AWS AppConfig) — fastest, no deploy needed
- **SageMaker endpoint update** to a previous model version — minutes
- **Endpoint deletion** — last resort

The kill switch must be tested. Quarterly chaos drill: "disable production model in <2 min." Capture the timing as audit evidence.

---

## 7. Model card — the required documentation

A **model card** (Google's 2018 paper popularized the format) documents what the model does, its training data, intended use, performance metrics per slice, and known limitations.

For SR 11-7, the model card answers the documentation requirement at the model level.

Standard sections:
1. Model details (name, version, owner, date)
2. Intended use + out-of-scope use
3. Training data (source, dates, size, known biases)
4. Evaluation data (same)
5. Metrics (accuracy + fairness across protected groups)
6. Quantitative analysis (confusion matrix, ROC curves)
7. Caveats and limitations
8. Ethical considerations

Store as `MODEL_CARD.md` in the model's repo. Update on every model retraining. Link from SageMaker Model Registry's `description` field.

---

## 8. Fairness, bias, drift — as code

Embed in CI as required status checks:

```yaml
- name: Fairness check
  run: |
    python -m fairness_eval \
      --model models/checkpoint.pt \
      --eval-data data/eval.parquet \
      --protected-attrs age,gender,race \
      --metrics demographic_parity,equal_opportunity,disparate_impact \
      --threshold 0.8 \
      --output fairness-report.json

- name: Upload fairness report
  uses: actions/upload-artifact@v4
  with: { name: fairness-report, path: fairness-report.json }

- name: Fail if fairness violated
  run: python -c "import json; r=json.load(open('fairness-report.json')); exit(0 if r['passed'] else 1)"
```

Make this a required check on the model's repo. PR can't merge if fairness regresses.

In production: continuous drift + fairness monitoring (Evidently AI, Arize, SageMaker Model Monitor, custom). Alerts wired to PagerDuty.

We cover the implementation in [module 42](42_mlops_validation_gates.md).

---

## 9. Capital One signaling — what they'd want to see

In an interview, when asked "how would you make your ML pipeline SR 11-7 compliant?":

> "Each model lifecycle step maps to a control: PR review enforces 1L self-checks (CODEOWNERS + required CI). Independent validation is a separate environment in the registry-promotion flow with MRM as required approver — that's the 2L gate. Production deploys require a separate person from the model author via environment manual approval — separation of duties. Every artifact is signed via OIDC-to-Sigstore (SLSA L3 if using reusable workflows). Audit log streamed to Splunk for retention beyond GitHub's 6 months. CloudTrail captures every endpoint mutation. Kill switch via SageMaker endpoint version revert, tested quarterly. Model card in repo, updated each retraining. Years later, given a date and an endpoint, we can reconstruct: commit SHA → training data version → validation reports → MRM approver → deploy approver. That's what 3L audit asks for."

---

## 10. Cross-references

- The technical primitives this module composes:
  - Signed commits → [module 02](02_config_identity_signing.md), [module 11](11_branch_protection_rulesets_codeowners.md)
  - CODEOWNERS + Required Reviewer → [module 11](11_branch_protection_rulesets_codeowners.md)
  - Environment approval + scoped secrets → [module 30](30_actions_environments_protection.md)
  - OIDC + IAM role scoping → [module 29](29_actions_oidc_aws.md)
  - Artifact attestations + Sigstore → [module 35](35_ghas_sbom_slsa_attestations.md)
  - Audit log streaming → [module 36](36_compliance_sso_scim_audit.md)
- Fairness/bias/drift in CI → [module 42](42_mlops_validation_gates.md).
- SageMaker Model Registry promotion → [module 43](43_mlops_mlflow_sagemaker.md).
- Model rollback workflows → [module 45](45_mlops_retraining_rollback.md).
