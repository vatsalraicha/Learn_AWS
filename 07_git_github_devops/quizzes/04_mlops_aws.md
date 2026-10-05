# Quiz 04 — Git/GitHub for ML + MLOps + AWS deployment (Parts I–K)

Covers modules 38–48.

---

## Section 1 — Notebook + data discipline (modules 38, 39)

1. **What three tools combine for ML notebook discipline in 2026?**
   <details><summary>Answer</summary>**nbstripout** (strip outputs at commit), **nbdime** (semantic notebook diffs), **jupytext** (pair `.ipynb` with `.py` text representation). Pre-commit framework wires them up.</details>

2. **When should you use Git LFS vs DVC?**
   <details><summary>Answer</summary>Git LFS for small-medium binary fixtures rarely changing (<50 MB, committed once). DVC for ML data + models with lineage, pipelines, experiments. LFS lacks lineage and gets expensive fast for ML workloads.</details>

3. **What's the killer guarantee of a feature store?**
   <details><summary>Answer</summary>Point-in-time consistency. At training time, features for a given event are the values that EXISTED at that event's timestamp — not the latest values (which would leak future data). Critical for time-series ML.</details>

4. **What's `.git-blame-ignore-revs` useful for in ML repos?**
   <details><summary>Answer</summary>List of commit SHAs to skip when `git blame` runs (and in GitHub's Blame UI). After a big `black`/`ruff format` PR, add its SHA so blame shows the real author of each line, not the formatter.</details>

---

## Section 2 — CI for ML + validation (modules 41, 42)

5. **What four CI layers are standard for an ML repo?**
   <details><summary>Answer</summary>Static (lint, format, type-check, secrets, deps), Unit (pure function + data shape tests), Integration (DB roundtrips, API calls), Model smoke (train 1 epoch on sample data, verify artifacts). Plus nightly full training.</details>

6. **Why is "overfit to a tiny batch" a useful model test?**
   <details><summary>Answer</summary>If a model can't overfit 4 samples in 20 steps, the architecture is broken or there's a dead gradient. Catches structural model bugs in seconds.</details>

7. **What's the "4/5ths rule" for fairness in lending models?**
   <details><summary>Answer</summary>EEOC guideline: disparate impact ratio (approval rate for protected group / approval rate for non-protected group) must be ≥ 0.8. Operationalized as a CI gate.</details>

8. **What's the difference between covariate drift and concept drift?**
   <details><summary>Answer</summary>Covariate drift = input distribution changes (e.g., transaction amounts shifted post-inflation). Concept drift = relationship between input and output changes (e.g., fraud patterns evolve). Both degrade model performance; different remediation.</details>

9. **What library is the standard for fairness metrics in Python?**
   <details><summary>Answer</summary>`fairlearn` (most common) and `aif360` (IBM, broader). Both compute demographic parity, equalized odds, etc.</details>

---

## Section 3 — Registry + champion/challenger + rollback (modules 43–45)

10. **What metadata should every model version in the registry have?**
    <details><summary>Answer</summary>commit_sha, training_data_id, framework_version, python_version, training_run_id (MLflow), evaluation_metrics (incl. fairness), model_card_url, attestation_url, created_by (workflow URL), approved_by (MRM identity + timestamp).</details>

11. **What's the canonical safe-rollout sequence for a new model?**
    <details><summary>Answer</summary>Shadow (parallel, no user impact) → Canary (5% traffic) → Ramp (50%) → Full (100%). Each stage with its own bake time + monitoring + manual approval. Auto-rollback on regression.</details>

12. **What's a SageMaker production variant?**
    <details><summary>Answer</summary>A model variant within an endpoint, with a routing weight. Multiple variants = traffic splitting. Update weights via `update_endpoint_weights_and_capacities` to shift traffic. Native champion/challenger support.</details>

13. **What's the target MTTR for an emergency model rollback?**
    <details><summary>Answer</summary>< 5 minutes. Workflow triggered by `workflow_dispatch` with reason input; environment with single approver (faster than normal prod gate); smoke-tests post-rollback; Slack + audit log.</details>

14. **What triggers retraining (the five canonical sources)?**
    <details><summary>Answer</summary>(1) Scheduled (cron), (2) Drift-detected (monitor → workflow_dispatch), (3) Manual, (4) Data-change (hook on upstream data refresh), (5) Performance regression (live metric drop).</details>

---

## Section 4 — OIDC + AWS deploy (modules 46–48)

15. **In a trust policy, why use `StringEquals` instead of `ForAllValues:StringEquals`?**
    <details><summary>Answer</summary>`ForAllValues:` returns true when the claim is absent or misspelled, granting unintended access. `StringEquals` requires the claim be present AND match. Real CVE pattern across multiple customers.</details>

16. **What does `role-chaining: true` do in `aws-actions/configure-aws-credentials@v4`?**
    <details><summary>Answer</summary>Tells the action to assume the next role from already-active credentials (instead of via OIDC). Used for the multi-account pattern: assume entry role via OIDC, then chain to target account roles via cross-account trust.</details>

17. **What's IRSA?**
    <details><summary>Answer</summary>IAM Roles for Service Accounts. EKS feature where a K8s ServiceAccount is annotated with an IAM role ARN; pods using that SA get the role's identity via STS auto-discovery. The Jenkins/Kubernetes equivalent of GitHub Actions OIDC.</details>

18. **What's the pattern for deploying a SageMaker endpoint with zero downtime from Actions?**
    <details><summary>Answer</summary>Create a new endpoint config (with new model + variant config); `update_endpoint` to point at new config; `wait endpoint-in-service`. SageMaker handles the rolling cutover. Smoke-test before reporting success.</details>

19. **Why do CDK PRs typically include a "diff" comment on the PR?**
    <details><summary>Answer</summary>So reviewers can see what infra changes the merge will produce before approving. Pattern: PR triggers `cdk diff` (with read-only role); output posted as PR comment via marocchino/sticky-pull-request-comment; merge triggers `cdk deploy`.</details>

20. **What's the standard cross-account deploy pattern at Capital One scale?**
    <details><summary>Answer</summary>Central entry account has the OIDC provider + entry role. Target accounts (per env, per LOB) have roles that trust the entry role with `sts:ExternalId` requirement. Workflow chains: OIDC → entry role → target role. Centralizes OIDC trust setup; per-target scoping; ExternalId defends against confused-deputy.</details>
