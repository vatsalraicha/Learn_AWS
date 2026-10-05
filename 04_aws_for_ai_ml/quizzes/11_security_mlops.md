# Quiz 11 — Security, MLOps & Capital One Patterns (Modules 50-55)

> Take cold. Heaviest on regulated-finance signal.

---

## Recall

1. What does Cloud Custodian do, and where did it come from?
2. SR 11-7 — name the three pillars.
3. RCPs vs SCPs — what gap do RCPs close?
4. The 2019 Capital One breach attack chain in three steps.
5. What's the rubicon-ml differentiator vs other experiment-tracking tools?

## Apply

6. Design org-wide policy enforcement that catches an S3 bucket misconfigured for public access.
7. Map SR 11-7 to SageMaker features (Model Cards, Registry, Clarify, Lineage).
8. You're auditing a Capital One ML pipeline. Walk through what artifacts you'd ask to see.
9. Configure GitHub Actions to deploy to AWS without storing AWS keys in GitHub.

## Diagnose

10. After the 2019 breach, name three controls that would have stopped each step in the chain.
11. A KServe pod can't read its model from S3. Walk through what to check.
12. Cloud Custodian dry-run shows it would terminate 200 production EC2 instances. What's likely wrong with the policy?

## Defend

13. Defend tokenization (Databolt-style) upstream of S3 vs SSE-KMS encryption alone.
14. Defend EKS+KServe over SageMaker endpoints for Capital One's specific workloads.
15. Defend Cloud Custodian over SCPs alone.

---

## Answers

1. **Cloud Custodian**: YAML policy-as-code for cloud governance (AWS, GCP, Azure). Originally **built by Capital One**; now **CNCF Incubating** since Sep 2022. Apache 2.0.
2. **Model development** (sound theory, robust methodology), **Model validation** (independent review), **Governance** (policies, roles, documented risk appetite).
3. **SCPs bound principals** (your IAM users/roles). **RCPs bound resources** — they prevent any principal (including external/anonymous) from accessing resources outside your org. SCPs can't stop a cross-account or unauthenticated reader from hitting your S3 if the bucket policy allows it; RCPs can.
4. **(1)** SSRF in misconfigured WAF allowed attacker to call EC2 metadata. **(2)** IMDSv1 returned role credentials with no token. **(3)** Role had broad S3 permissions; attacker exfiltrated ~106M records.
5. **`auto_git_enabled=True`** binds every experiment to a specific git SHA. The lineage is automatic — the SR 11-7 audit answer for "what code trained this model?" is built into the platform.
6. **Layers**: (1) **SCP** denies `s3:PutBucketAcl` → public. (2) **RCP** on Org denies any principal outside org accessing S3. (3) **Config Rule** `s3-bucket-public-read-prohibited` detects+remediates. (4) **Cloud Custodian** runs on event mode, scans on bucket creation, alerts/locks-down. (5) **Macie** scans S3 for sensitive data and alerts on exposure.
7. (Module 52 detailed table.) Briefly: Model Cards = documentation pillar. Model Registry = approval/versioning. Clarify = bias/explainability evidence. Lineage Tracking + rubicon-ml = experiment provenance for validation. Model Monitor = ongoing model risk monitoring.
8. **Training data inventory** + Lake Formation tags. **Code commit** that trained the model (rubicon-ml git SHA). **Hyperparameters** (Model Registry). **Bias + explainability** (Clarify reports). **Evaluation results** + thresholds. **Approval record** in Model Registry. **Deployment manifests** (CDK/Terraform). **Monitoring alerts** (Model Monitor schedule). **Access logs** (CloudTrail).
9. **OIDC federation**: create an OIDC provider in IAM for `token.actions.githubusercontent.com`; create role with trust policy allowing `sts:AssumeRoleWithWebIdentity` with strict `sub` claim (`repo:org/repo:ref:refs/heads/main`); use `aws-actions/configure-aws-credentials@v4` action with `role-to-assume`.
10. **SSRF**: WAF rule scoping, IMDSv2 required (token-based). **IMDSv1**: enforce IMDSv2 via SCP. **Broad S3 role**: least-privilege role + prefix-scoped grants. **No detection**: GuardDuty Extended Threat Detection. **Public bucket**: Block Public Access at account+org (RCP). **Sensitive data unprotected**: Macie + Databolt tokenization.
11. (1) **IRSA / Pod Identity** role attached to ServiceAccount? (2) Role has `s3:GetObject` on the model bucket+prefix? (3) Bucket policy allows the role? (4) **KMS Interface endpoint** + key policy if SSE-KMS? (5) VPC endpoint for S3 (Gateway) in cluster VPC? (6) NACL allowing 443 out + ephemeral in? (7) Pod's `securityContext` allowing network?
12. **Filter too broad** — likely matched production tags or didn't exclude `Environment=prod`. **Always dry-run; always exclude prod by default and opt-in.** Also possible: the policy was meant to flag (notify), not terminate (act).
13. **SSE-KMS encrypts the data at rest in S3**. The data is still **decrypted on read** by anyone with KMS permission. **Tokenization replaces the sensitive data itself** with surrogate tokens — even if someone reads the bucket, they get tokens, not PAN. PCI scope is bounded to the tokenization service. Defense in depth.
14. **Custom runtime control** (vendored Triton + specific TensorRT-LLM). **EKS investment** already exists. **Multi-region portability** is easier. **High-volume cost** can beat SageMaker endpoints. **Pod-level canary** via Istio. **Air-gapped isolation** possible.
15. **SCPs are preventive** but don't catch existing drift, can't auto-remediate, and don't see what's actually deployed. **Custodian** is detective + responsive: scans existing resources, runs rules continuously, can auto-remediate (tag, stop, terminate, notify). They're complementary, not redundant — Custodian is the runtime governance layer.
