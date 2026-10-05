# 48 — ⭐ CDK + CloudFormation + Terraform from Actions; cross-account

> *"Capital One uses CDK heavily (per re:Invent 2024 talks). The deploy pattern is consistent across IaC tools: OIDC + role assumption + diff-on-PR + apply-on-merge."*

## Why this module exists

Infrastructure-as-code deployments need the same care as app deployments — diff visible in PRs, scoped credentials, manual approval for prod, audit trails. This module covers the CDK + CloudFormation + Terraform workflows, plus the cross-account patterns Capital One uses.

---

## 1. CDK from Actions

```yaml
name: CDK Deploy
on:
  push:
    branches: [main]
  pull_request:

permissions:
  id-token: write
  contents: read
  pull-requests: write

jobs:
  diff:
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-node@v4
        with: { node-version: "22" }
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt
      - run: npm install -g aws-cdk

      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ vars.CDK_READ_ROLE_ARN }}    # read-only for diff
          aws-region: us-east-1

      - run: cdk synth

      - name: Diff
        id: diff
        run: |
          cdk diff --app cdk.out 2>&1 | tee diff.txt
          # Capture for PR comment
          {
            echo 'OUTPUT<<EOF'
            cat diff.txt
            echo EOF
          } >> $GITHUB_OUTPUT

      - uses: marocchino/sticky-pull-request-comment@v2
        with:
          header: cdk-diff
          message: |
            ## CDK Diff
            \`\`\`
            ${{ steps.diff.outputs.OUTPUT }}
            \`\`\`

  deploy:
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    environment: prod
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-node@v4
      - uses: actions/setup-python@v5
      - run: pip install -r requirements.txt && npm install -g aws-cdk

      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ vars.CDK_DEPLOY_ROLE_ARN }}
          aws-region: us-east-1

      - run: cdk deploy --all --require-approval never
```

**Diff on PR / apply on merge** is the canonical pattern. Reviewer sees what infra changes before approving.

For Capital One: CDK is heavily used (per their re:Invent 2024 talks on IaC governance). They have internal CDK construct libraries that codify standard patterns (e.g., "compliant S3 bucket" with KMS + access logging + Cloud Custodian policy attached).

### CDK bootstrap

CDK requires bootstrapping per account+region: `cdk bootstrap aws://ACCOUNT_ID/REGION`. Creates the CDKToolkit stack (S3 bucket for assets, IAM roles for deploy). Do this once per account+region; revisit after CDK version bumps.

---

## 2. CloudFormation from Actions

For repos that prefer raw CloudFormation:

```yaml
- uses: aws-actions/configure-aws-credentials@v4
  with: { role-to-assume: ${{ vars.DEPLOY_ROLE_ARN }}, aws-region: us-east-1 }

- uses: aws-actions/aws-cloudformation-github-deploy@v1
  with:
    name: fraud-detector-stack
    template: cloudformation/template.yaml
    parameter-overrides: "Environment=prod,Version=${{ github.sha }}"
    capabilities: CAPABILITY_IAM,CAPABILITY_NAMED_IAM
    no-fail-on-empty-changeset: "1"
```

Less popular than CDK but works. For things that should NOT be exposed to a programming language (compliance-mandated templates, public reference templates).

---

## 3. Terraform from Actions

```yaml
- uses: hashicorp/setup-terraform@v3
  with:
    terraform_version: 1.9.0

- uses: aws-actions/configure-aws-credentials@v4
  with: { role-to-assume: ${{ vars.TF_DEPLOY_ROLE_ARN }}, aws-region: us-east-1 }

- run: terraform init
- run: terraform fmt -check
- run: terraform validate

- name: Plan
  id: plan
  run: terraform plan -out=tfplan -no-color | tee plan.txt

- uses: marocchino/sticky-pull-request-comment@v2
  if: github.event_name == 'pull_request'
  with:
    header: tf-plan
    message: |
      ## Terraform Plan
      \`\`\`hcl
      ${{ steps.plan.outputs.stdout }}
      \`\`\`

- name: Apply (on main only)
  if: github.event_name == 'push' && github.ref == 'refs/heads/main'
  run: terraform apply -auto-approve tfplan
```

State backend: S3 + DynamoDB lock table (the standard). The role needs read+write to the state bucket.

Tools: `tflint`, `tfsec`, `checkov` for IaC scanning. Run in CI as required checks.

---

## 4. Drift detection

IaC + manual changes drift over time. Schedule a periodic check:

```yaml
on:
  schedule:
    - cron: '0 8 * * 1'   # Monday 8am UTC

jobs:
  drift-check:
    runs-on: ubuntu-latest
    steps:
      - run: cdk diff --app cdk.out 2>&1 | tee diff.txt
      - run: |
          if [ -s diff.txt ]; then
            curl -X POST $SLACK_WEBHOOK -d "{\"text\":\"Drift detected\"}"
          fi
```

For prod: drift is a paging event. Manual changes to prod should be impossible (deploy role doesn't trust humans, only Actions).

---

## 5. Cross-account deploys

Capital One has many AWS accounts (dev / staging / prod per LOB, plus shared services). The OIDC + chained role pattern handles cross-account:

Central account (`shared-cicd`):
- Trusts GitHub OIDC.
- Hosts `github-actions-entry` role.

Target accounts (`ml-prod`, `ml-staging`, ...):
- Trust the entry role (via cross-account `sts:AssumeRole`).
- Have per-target roles with deploy permissions.

Workflow:

```yaml
- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::SHARED_ACCT:role/github-actions-entry
    aws-region: us-east-1

- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::ML_PROD_ACCT:role/cdk-deploy-role
    role-chaining: true
    role-external-id: capitalone-cdk
    aws-region: us-east-1

- run: cdk deploy MyStack --all
```

Benefits:
- One OIDC trust setup (in the central account)
- Per-target-account scoping via cross-account trust
- `ExternalId` defends against confused-deputy
- Centralized auditing of who assumed what

---

## 6. CDK Pipelines vs GitHub Actions

CDK has its own pipeline construct (CDK Pipelines, based on CodePipeline). It auto-wires:
- Source: GitHub (via CodeStar connections)
- Build: CodeBuild
- Deploy stages with auto-rollback

Pros: AWS-native, integrated with CDK
Cons: yet another CI/CD system to learn; visibility lives in CodePipeline console, not GitHub

For Capital One's GitHub Actions + Jenkins reality, CDK Pipelines is rarely the chosen path. Better: CDK code in repo, deploy via GH Actions (or Jenkins) workflow.

---

## 7. The Cloud Custodian intersection

Capital One's open-source Cloud Custodian is a runtime enforcement layer. CDK/CFN/TF declares infra; Custodian enforces compliance ongoing.

Pattern:
- IaC creates resources (with required tags, encryption, etc.)
- Custodian policies run on cron, flag/remediate non-compliant resources
- New IaC changes go through PR review + IaC scanning (tfsec, checkov)
- If Custodian remediates, audit log captures it

You should know Custodian exists; you don't need to write its policies as a Sr ML Lead. The platform team owns those.

---

## 8. Migrating between IaC tools

Often: existing CloudFormation → CDK (CDK can import CFN stacks). Or Terraform → CDK. Or just consolidating sprawl.

Tools:
- `cdk import` — import existing resources into CDK management
- `terraformer` — generate Terraform from existing resources
- `former2` — generate CFN from existing resources

Migration approach: import in stages, validate diff is empty, then iterate. Don't try a big-bang migration.

---

## 9. The IaC PR review checklist

When reviewing an IaC PR:
- ✅ Diff comment posted; reviewer reads it
- ✅ Required IaC scans passed (tfsec, checkov, cdk-nag)
- ✅ Changes are reversible (deploy + rollback both tested in staging)
- ✅ No secrets in IaC code (use Parameter Store / Secrets Manager references)
- ✅ Tags are present (`Owner`, `Env`, `CostCenter`, `Project`)
- ✅ Resource names follow naming convention
- ✅ KMS encryption enabled where appropriate
- ✅ Logging enabled where appropriate
- ✅ Cross-account permissions explicitly scoped
- ✅ ADR exists for non-trivial decisions

---

## 10. Cross-references

- The OIDC + cross-account trust → [module 46](46_aws_oidc_trust_policy_deep.md).
- The deploy targets the IaC creates → [module 47](47_aws_deploy_sagemaker_ecs_eks_lambda.md).
- ARC on EKS (CDK to provision the EKS cluster) → [module 28](28_actions_self_hosted_arc_gpu.md).
- Topic 04 module 01 (account/org/landing zone) — for the multi-account architecture context.
