# 27 — IaC + GitOps for DevSecOps

## Why this module exists

IaC + GitOps is the structural foundation of DevSecOps. If your infrastructure is in Git: every change is reviewable, every artifact is auditable, every drift is detectable. This module connects Terraform (Module 13) and GitOps practices to the security posture.

## 1. The "Cattle vs Pets" concept

- **Pets** — named, hand-tended, irreplaceable (the legacy server `db01.prod`)
- **Cattle** — numbered, interchangeable, disposable (`autoscaling-group-prod-abc123`)

For DevSecOps: pets are the enemy. They accumulate manual changes, drift from the original config, are impossible to rebuild from source. Cattle are *defined* in code; any instance can be destroyed and rebuilt identically.

## 2. IaC security wins

| Without IaC | With IaC |
|---|---|
| Manual click-ops; un-auditable | Every change in Git history |
| Config drift = compliance gap | Drift detected by `terraform plan` |
| Lost-credential disasters | Reproducible from source |
| "I think it's encrypted" | Encrypted-at-rest enforced by policy |
| Inconsistent tagging | Required tags enforced by policy |
| Open security groups go unnoticed | Policy scan catches `0.0.0.0/0` |

## 3. The IaC security scanner stack

| Tool | Lang | Focus |
|---|---|---|
| **Checkov** (Bridgecrew/Prisma) | Python | Most comprehensive; Terraform + CFN + K8s + Helm + Dockerfile |
| **tfsec** (now part of Trivy) | Go | Terraform-only; merged into Trivy |
| **KICS** (Checkmarx) | Go | Multi-IaC |
| **Terrascan** (Tenable) | Go | Terraform + others |
| **Snyk IaC** | Commercial | Across-the-board |
| **cdk-nag** | TypeScript | AWS CDK specifically |
| **cfn-guard** (AWS) | Rust | CloudFormation |
| **Trivy config** | Go | Multi-IaC |
| **Cloud Custodian** | Python | Runtime AWS policy (Capital One's tool) |

**Recommendation 2026:** Checkov for breadth, plus Trivy config in CI (free + fast), plus Cloud Custodian or AWS Config for runtime drift.

## 4. Checkov in CI

```bash
pip install checkov

# Scan Terraform
checkov -d terraform/ --framework terraform --output cli --output json

# Scan with severity threshold
checkov -d . --check CKV_AWS_*  --hard-fail-on HIGH

# Skip specific checks (with justification)
checkov -d . --skip-check CKV_AWS_18,CKV_AWS_53
```

```yaml
# GitHub Actions
- uses: bridgecrewio/checkov-action@master
  with:
    directory: terraform/
    framework: terraform
    output_format: sarif
    output_file_path: checkov.sarif
- uses: github/codeql-action/upload-sarif@v3
  with: { sarif_file: checkov.sarif }
```

Common Checkov findings:
- `CKV_AWS_18`: S3 bucket without access logging
- `CKV_AWS_21`: S3 bucket versioning disabled
- `CKV_AWS_24`: SG with ingress from 0.0.0.0/0
- `CKV_AWS_53`: S3 bucket public-access-block missing

## 5. Terraform Remote State for DevSecOps

Local state = no audit. Remote state with versioning + locking:

```hcl
terraform {
  backend "s3" {
    bucket         = "tf-state-prod"
    key            = "platform/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    kms_key_id     = "alias/terraform-state"
    dynamodb_table = "tf-state-lock"
  }
}
```

Why this matters:
- **Encrypted at rest** with KMS
- **Versioning** on the S3 bucket → previous state recoverable
- **DynamoDB lock** prevents concurrent applies
- **CloudTrail logs every read/write** of the state file

## 6. CI/CD for IaC (the GitOps pattern)

```yaml
# .github/workflows/terraform.yml
on:
  pull_request: { paths: ['terraform/**'] }
  push:        { branches: [main], paths: ['terraform/**'] }

jobs:
  plan:
    runs-on: ubuntu-latest
    permissions: { id-token: write, contents: read, pull-requests: write }
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with: { role-to-assume: ${{ secrets.AWS_PLAN_ROLE }}, aws-region: us-east-1 }
      - uses: hashicorp/setup-terraform@v3
      - run: terraform init
      - run: terraform fmt -check -recursive
      - run: terraform validate
      - uses: bridgecrewio/checkov-action@master
      - run: terraform plan -out=tfplan
      - name: Post plan to PR
        # ... comment with plan output

  apply:
    needs: plan
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production    # requires manual approval per env protection
    permissions: { id-token: write, contents: read }
    steps:
      - uses: aws-actions/configure-aws-credentials@v4
        with: { role-to-assume: ${{ secrets.AWS_APPLY_ROLE }}, aws-region: us-east-1 }
      - run: terraform apply -auto-approve tfplan
```

The discipline:
- **Plan role** has read + plan permissions only
- **Apply role** has apply permissions; only assumable from `main` branch
- **PR plan visible** as comment for review
- **Apply gated** by GitHub Environment protection (requires approver)

## 7. GitOps for application deploys (preview Module 33)

```
Developer pushes code
  ↓
CI builds + tests + scans + signs image
  ↓
CI pushes image to ECR
  ↓
CI commits "image: app:1.2.3" change to GitOps repo
  ↓
ArgoCD watching GitOps repo notices change
  ↓
ArgoCD pulls + applies to cluster
  ↓
ArgoCD reports sync status
```

Key DevSecOps wins:
- **Pipeline has no cluster credentials** — cluster pulls, doesn't get pushed to
- **Every change is a Git commit** — full audit
- **Drift detection** — ArgoCD compares cluster state to Git, alerts on drift
- **Easy rollback** — revert Git commit, ArgoCD syncs

See Module 33 for the ArgoCD deep dive.

## 8. Policy-as-Code for IaC

**Open Policy Agent (Rego)** can enforce custom Terraform policies pre-apply:

```rego
# policy/terraform.rego
package terraform.s3

deny[msg] {
  resource := input.resource_changes[_]
  resource.type == "aws_s3_bucket"
  not resource.change.after.server_side_encryption_configuration
  msg := sprintf("S3 bucket '%s' must have encryption enabled", [resource.address])
}
```

```bash
terraform plan -out=tfplan
terraform show -json tfplan > plan.json
opa eval --data policy/ --input plan.json "data.terraform.s3.deny"
```

Or use **Conftest** (wrapper for OPA on Terraform/K8s manifests):
```bash
conftest test --policy policy/ plan.json
```

## 9. Drift detection

Even with IaC, manual changes happen (incident response, vendor support, accidents). Drift detection catches them.

Options:
- **`terraform plan`** on a schedule against prod state; alert if non-zero plan
- **AWS Config** — resource configuration history; compliance rules
- **Driftctl** (OSS, archived 2023) — successors emerging
- **Snyk Cloud / Wiz CSPM** — commercial
- **Cloud Custodian** — Capital One's open-source tool; broader than drift but covers it

## 10. SBOM for infrastructure?

Yes — there's a movement toward **infra SBOM**:
- What modules + providers + versions are in use across your TF estate
- Drift between TF source and applied state
- Vulnerable modules in use

Tools: **Hashicorp Terraform Cloud's Module Registry insights**, **Stacklet** (commercial Custodian), early-stage offerings from Wiz / Snyk.

## 11. The 12-point IaC security checklist

1. Remote state with encryption + locking
2. IaC scanner (Checkov + Trivy config) in CI
3. Plan on PR; apply only on main + manual approval
4. OIDC + IAM roles; no long-lived keys
5. Provider + module versions pinned (`~> 5.80`)
6. Modules from trusted sources only (private registry preferred)
7. All resources tagged (Environment, Owner, CostCenter, ManagedBy=terraform)
8. Policy-as-Code gates (OPA/Conftest/Sentinel)
9. Scheduled drift detection
10. GitOps for K8s manifests (ArgoCD/Flux)
11. Signing + verification of artifacts at admission (Cosign + Kyverno)
12. Regular IaC code review like any other code

## 12. Quick self-check

1. What's the "cattle vs pets" metaphor and why does it matter for DevSecOps?
2. What does Checkov scan and when in the pipeline do you run it?
3. How does GitOps reduce the attack surface compared to CI-pushes-to-cluster?
4. What's drift detection and what tools enable it?
5. What's the difference between "policy as code" and "compliance as code"?

(Answers: pets are unique manual-tended servers, cattle are interchangeable IaC-defined — cattle are auditable, reproducible, drift-free; Terraform/CFN/K8s/Helm/Dockerfile for security misconfigs, in CI on PR; cluster pulls from Git, pipeline doesn't need cluster credentials, every change is a commit; comparing actual cloud state to IaC source; tools: Cloud Custodian, AWS Config, scheduled terraform plan, Snyk Cloud; PaC enforces design rules pre-apply, CaC enforces continuous compliance against frameworks like CIS/SOC 2 post-deploy.)
