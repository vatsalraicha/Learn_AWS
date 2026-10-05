# Module 55 — CI/CD for ML on AWS

> **What this is:** CodePipeline / CodeBuild / CodeArtifact, GitHub Actions with **OIDC federation to AWS IAM** (the modern pattern), SageMaker Pipelines vs Step Functions for ML CI/CD, model registry promotion strategies, IaC with CDK + Terraform.

---

## 1. The CI/CD chains

| Stack | Use |
|---|---|
| **CodePipeline + CodeBuild + CodeArtifact** | AWS-native CI/CD |
| **GitHub Actions + OIDC** | Most common in 2026 |
| **GitLab CI + OIDC** | Where GitLab is the source |
| **Jenkins on EC2** | Legacy; many shops migrating |

### GitHub Actions + OIDC pattern (the modern default)

**Don't store AWS keys in GitHub.** Instead, configure OIDC trust:

1. In AWS, create an **OIDC provider** for `https://token.actions.githubusercontent.com`.
2. Create an IAM role with trust policy allowing `sts:AssumeRoleWithWebIdentity` from that OIDC provider, conditioned on the GitHub `sub` claim.
3. In GitHub Actions, use the `aws-actions/configure-aws-credentials@v4` action with `role-to-assume`.

```yaml
permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole
          aws-region: us-east-1
      - run: terraform apply -auto-approve
```

**The trust policy `sub` claim must be scoped tightly:**
```
"Condition": {
  "StringEquals": {
    "token.actions.githubusercontent.com:sub": "repo:capitalone/card-ml:ref:refs/heads/main"
  }
}
```

A too-broad `sub` (`repo:capitalone/card-ml:*`) lets feature branches assume the same role — a real attack vector.

## 2. CodeCommit deprecation note

**CodeCommit closed to new customers mid-2024.** Existing customers retained; new shops use GitHub Enterprise, GitLab, or Bitbucket Cloud.

## 3. SageMaker Pipelines vs Step Functions for ML CI/CD

(Module 15.)

- **SageMaker Pipelines** — best for the ML-specific DAG (Processing → Training → Evaluation → Register).
- **Step Functions** — best for the outer orchestration (event → SM Pipeline → Model Registry → deploy gate → deploy).

**Pattern:** GitHub Actions kicks off Terraform/CDK; Terraform/CDK provisions resources; SageMaker Pipeline runs; Step Functions orchestrates the deployment after Model Registry approval.

## 4. Model registry promotion strategies

Three approaches:

### Manual approval
PR merges to main → training → Model Registry as `Pending` → human approver flips to `Approved` → deployment.

### Automated approval gates
Same flow, but a CI job runs evaluation checks (accuracy threshold, bias threshold, latency benchmark) and auto-approves if passed.

### Progressive rollout
Approved model → deploy to staging → canary on prod (5%) → full prod after N hours of green metrics.

**Capital One pattern:** all three, depending on workload sensitivity. Manual for high-risk models (credit decisioning); automated + progressive for low-risk.

## 5. Packaging models

- **Model Registry** (SageMaker) — the metadata + S3 artifact reference.
- **Container image** in ECR — for KServe/Triton serving.
- **S3 artifact** — the raw weights for SageMaker endpoints.

**Most regulated shops use Model Registry as the gate**, regardless of where the artifact ends up.

## 6. IaC patterns — CDK + Terraform

A common pattern:

- **Terraform** for foundational/networking — VPC, TGW, IAM roles, KMS.
- **AWS CDK** for application-layer constructs — SageMaker domains, Lambda, Step Functions.
- **Separation rationale**: Terraform's state model and provider ecosystem suit networking; CDK's L2/L3 constructs are richer for app-level patterns.

### cdk-nag + cfn-guard in CI

(Module 51.) Run cdk-nag at `cdk synth` time; run cfn-guard against the synthesized CloudFormation template. Both must pass before deploy.

## 7. Container security scanning

- **Inspector v2** scans ECR images for vulnerabilities.
- **Trivy** / **Snyk** in CI for early detection.

Common Capital One pattern: block deploys if container has CRITICAL or HIGH CVEs.

## 8. Secrets and config management

- **Secrets Manager** for rotated secrets (DB passwords, API keys).
- **Parameter Store** for non-rotated config.
- **IAM Identity Center** for human workforce access.
- **Doppler / HashiCorp Vault** for cross-platform secrets management.

## 9. Automated rollback

Patterns:
- **CodeDeploy traffic shifting** (Lambda, ECS) — automatically rolls back if CloudWatch alarms trigger during deploy.
- **Istio canary + Flagger** for K8s — auto-rollback on metric regression.
- **SageMaker endpoint blue/green** — rollback variant on health-check failure.

## 10. 2024-2026 changes

- **GitHub Actions OIDC** widespread.
- **SageMaker Pipelines @step decorator** + MLflow integration.
- **CodeCatalyst** exists but adoption limited in regulated finance.
- **EKS Pod Identity** widely adopted (vs IRSA).
- **cdk-nag** matured.

## 11. Pitfalls

- **OIDC `sub` claim too broad** — high-privilege role assumable from any branch.
- **No IaC drift detection** — manual console changes diverge from code.
- **Model Registry approval bottleneck** — gate it on a SLA.
- **Container scanning at deploy** instead of build → late detection.

## 12. Capital One lens

Likely CI/CD:
- **GitHub Actions + OIDC** to AWS.
- **Terraform for VPC/IAM, CDK for app stacks**.
- **cdk-nag + cfn-guard + Cloud Custodian** as the policy layers.
- **SageMaker Pipelines + Step Functions** for ML orchestration.
- **Model Registry + rubicon-ml + Model Cards** for the approval audit trail.
- **Inspector** for container vulnerability scanning.

## 13. Sanity check

1. Why OIDC federation instead of GitHub-stored AWS keys?
2. What's the trust policy `sub` claim pitfall?
3. SageMaker Pipelines vs Step Functions for ML CI/CD — when does each fit?
4. Why use both CDK and Terraform in the same org?
5. What did CodeCommit do in 2024?

## 14. Cross-references

- **Module 38** — SageMaker MLOps (Pipelines + Registry)
- **Module 15** — orchestration (Step Functions)
- **Module 51** — cdk-nag + cfn-guard + Cloud Custodian
- **Module 2** — IAM trust policies

## Primary sources

- Research report: [`13_mlops_c1_patterns.md`](../../research_inputs/04_aws_for_ai_ml/13_mlops_c1_patterns.md)
