# 29 — ⭐ OIDC to AWS — the canonical pattern

> *"If you take only one thing from Topic 07, take this: GitHub Actions → AWS via OIDC. No long-lived AWS keys in GitHub secrets, ever."*

## Why this module exists

OIDC (OpenID Connect) lets GitHub Actions assume AWS IAM roles using short-lived (1-hour) tokens, without any long-lived AWS access keys stored anywhere. This is **the** authentication pattern for Capital One (and every modern AWS-native shop). It's also the most security-critical configuration to get right.

If you understand only one Sr-Lead-level GitHub Actions concept, make it this.

---

## 1. The big picture

**Without OIDC** (the old, bad way):

```
1. Generate AWS access key + secret for an IAM user
2. Store as GitHub Actions secrets (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
3. Workflow reads secrets, configures AWS SDK
4. The key sits in GitHub forever, can be exfiltrated, has no expiry
```

**With OIDC**:

```
1. AWS IAM trusts GitHub's OIDC identity provider
2. Workflow requests a workflow-scoped JWT (signed by GitHub)
3. Workflow exchanges JWT for AWS STS temporary credentials (1-hour expiry)
4. No long-lived secret anywhere
```

The trust policy on the IAM role uses **claims in the JWT** to restrict which repo/branch/environment can assume it.

---

## 2. The setup — 3 components

### A. Add GitHub as an OIDC identity provider in AWS IAM

Once per AWS account. (Capital One: once per AWS account; they likely have a CDK construct for this.)

```bash
# Console: IAM → Identity providers → Add provider → OpenID Connect
# Provider URL: https://token.actions.githubusercontent.com
# Audience: sts.amazonaws.com
```

CDK:

```python
from aws_cdk import aws_iam as iam

provider = iam.OpenIdConnectProvider(
    self, "GitHubOIDCProvider",
    url="https://token.actions.githubusercontent.com",
    client_ids=["sts.amazonaws.com"],
)
```

Terraform:

```hcl
resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}
```

(GitHub's thumbprint changes occasionally — AWS now auto-verifies, so the thumbprint is informational. Keep it as belt-and-braces.)

### B. Create an IAM role with a trust policy

Role trust policy = "who can assume this role?" For OIDC, it's GitHub Actions with specific JWT claims:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:capitalone/cool-ml-service:ref:refs/heads/main"
        }
      }
    }
  ]
}
```

Attach permissions policies — `AmazonSageMakerFullAccess`, your custom deploy policy, etc.

### C. Workflow uses the role

```yaml
name: Deploy
on:
  push:
    branches: [main]

permissions:
  id-token: write          # REQUIRED — lets the workflow request an OIDC JWT
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/github-actions-deployer
          role-session-name: gh-actions-${{ github.run_id }}
          aws-region: us-east-1
          # Optional:
          # role-duration-seconds: 3600    # default
          # mask-aws-account-id: false

      - run: aws sts get-caller-identity      # verify
      - run: aws s3 cp ./artifact.zip s3://my-bucket/
```

No `AWS_ACCESS_KEY_ID`. No `AWS_SECRET_ACCESS_KEY`. The runner's IAM identity is the assumed role.

---

## 3. The `sub` claim — the security backbone

The trust policy condition restricts which workflows can assume the role. The most important claim:

| Pattern | Matches |
|---|---|
| `repo:capitalone/cool-ml-service:*` | Any workflow in `capitalone/cool-ml-service` (any branch, any event) |
| `repo:capitalone/cool-ml-service:ref:refs/heads/main` | Only when running on `main` branch |
| `repo:capitalone/cool-ml-service:ref:refs/tags/v*.*.*` | Only on SemVer-style tag pushes |
| `repo:capitalone/cool-ml-service:pull_request` | Only on `pull_request` events |
| `repo:capitalone/cool-ml-service:environment:prod` | Only when running in the `prod` GitHub Environment |

The environment-bound pattern is the **gold standard** for prod deploys: combine GitHub Environment protection rules (manual approval, see [module 30](30_actions_environments_protection.md)) with sub-claim scoping. A workflow can only assume the prod role if it (a) runs in the `prod` environment, which (b) required manual approval.

Example trust policy for prod-only access:

```json
{
  "Condition": {
    "StringEquals": {
      "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
      "token.actions.githubusercontent.com:sub": "repo:capitalone/cool-ml-service:environment:prod"
    }
  }
}
```

---

## 4. The critical security pitfall

❌ **NEVER use `ForAllValues:StringEquals` in Allow statements**:

```json
"Condition": {
  "ForAllValues:StringEquals": {
    "token.actions.githubusercontent.com:sub": "repo:capitalone/cool:..."
  }
}
```

Reason: `ForAllValues` returns **true** if the claim is **absent** or doesn't match the claim name (e.g., misspelling). An attacker doesn't need to satisfy your condition; they just need a JWT without that claim, and Allow → true.

✅ **Always use `StringEquals` or `StringLike`** — these require the claim to be present AND match.

This is a real CVE pattern. AWS published guidance after multiple customer incidents.

---

## 5. The other claims in the JWT

```json
{
  "jti": "...",
  "sub": "repo:capitalone/cool-ml-service:ref:refs/heads/main",
  "aud": "sts.amazonaws.com",
  "ref": "refs/heads/main",
  "sha": "abc123...",
  "repository": "capitalone/cool-ml-service",
  "repository_owner": "capitalone",
  "repository_id": "12345678",
  "repository_owner_id": "67890",
  "run_id": "1234567890",
  "run_number": "42",
  "run_attempt": "1",
  "actor": "vraicha",
  "actor_id": "98765",
  "workflow": "Deploy",
  "head_ref": "",
  "base_ref": "",
  "event_name": "push",
  "ref_type": "branch",
  "environment": "prod",
  "job_workflow_ref": "capitalone/cool-ml-service/.github/workflows/deploy.yml@refs/heads/main",
  "iss": "https://token.actions.githubusercontent.com",
  "iat": 1716315600,
  "exp": 1716316800
}
```

You can condition on any of these. Common patterns:

- `token.actions.githubusercontent.com:repository_owner` — restrict to a specific org
- `token.actions.githubusercontent.com:job_workflow_ref` — restrict to a specific reusable workflow (so the role can only be assumed via your central pipeline)
- `token.actions.githubusercontent.com:environment` — restrict to a specific environment

### The `job_workflow_ref` claim (the InnerSource superpower)

When a job calls a reusable workflow, `job_workflow_ref` contains the reusable workflow's path. This lets you restrict role assumption to "must be called via our central pipeline":

```json
"StringLike": {
  "token.actions.githubusercontent.com:job_workflow_ref": "capitalone/workflows-org/.github/workflows/sagemaker-deploy.yml@refs/heads/main"
}
```

Now no consumer can write their own deploy step that grabs the prod role — they have to call the central reusable workflow.

This is THE pattern at Capital One scale: deploy roles trust only the central pipeline. Service repos can only deploy through the blessed workflow.

---

## 6. Per-environment IAM role scoping

Standard pattern: one role per (repo × environment) combination, or one role per (team × environment).

```
Account: capital-one-ml-dev
  Role: github-actions-deployer-dev
    Trust: repo:capitalone/cool-ml-service:environment:dev
    Permissions: deploy to dev SageMaker, write to dev S3

Account: capital-one-ml-staging
  Role: github-actions-deployer-staging
    Trust: repo:capitalone/cool-ml-service:environment:staging
    Permissions: deploy to staging SageMaker

Account: capital-one-ml-prod
  Role: github-actions-deployer-prod
    Trust: repo:capitalone/cool-ml-service:environment:prod
    Permissions: deploy to prod SageMaker (minimum)
```

Multi-account = blast radius isolation. The prod role lives in the prod account; the dev role lives in the dev account. A compromised dev workflow can't touch prod resources.

Workflow:

```yaml
jobs:
  deploy:
    environment: ${{ inputs.env }}                              # dev / staging / prod
    runs-on: ubuntu-latest
    steps:
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::${{ vars.AWS_ACCOUNT_ID }}:role/github-actions-deployer-${{ inputs.env }}
          aws-region: us-east-1
```

`vars.AWS_ACCOUNT_ID` is set per-environment in repo Settings → Environments → variables. Different value per env.

---

## 7. Role-chaining (cross-account)

For organizations with many accounts, you can chain role assumption:

```yaml
- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::ROOT_ACCOUNT:role/github-actions-entry
    aws-region: us-east-1

- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::TARGET_ACCOUNT:role/cross-account-deployer
    role-chaining: true
    aws-region: us-east-1
```

Step 1: assume entry role in central account via OIDC.
Step 2: from there, assume a cross-account role in the target.

Use when:
- Many target accounts but you want one OIDC trust setup.
- Existing cross-account architecture (entry account → spoke accounts).

---

## 8. Verifying the setup

After setting up, prove it works:

```yaml
- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::...
    aws-region: us-east-1
- run: aws sts get-caller-identity
# Expected:
# {
#   "UserId": "AROA...:gh-actions-1234567890",
#   "Account": "123456789012",
#   "Arn": "arn:aws:sts::123456789012:assumed-role/github-actions-deployer/gh-actions-1234567890"
# }
```

`UserId` ending in your `role-session-name` confirms the OIDC path. The session expires when the workflow ends (or after `role-duration-seconds`, default 1h).

CloudTrail logs every assume-role call with the session name. Pair with your audit log review.

---

## 9. Common errors and fixes

| Error | Fix |
|---|---|
| `Error: Could not assume role` + no specific reason | Trust policy doesn't match your claims. Use `aws iam simulate-principal-policy` to debug. |
| `User: ... is not authorized to perform: sts:TagSession` | The `aws-actions/configure-aws-credentials` action adds session tags by default; either grant `sts:TagSession` in the trust policy or set `role-skip-session-tagging: true`. |
| `id-token: write` missing → `Error: Failed to retrieve identity token` | Add `permissions: id-token: write` at workflow or job level. |
| Conditions in trust policy use `ForAllValues:` → security incident | Replace with `StringEquals` or `StringLike`. |
| Works on push, fails on PR | Sub claim doesn't match `pull_request` event format. Either add a PR-specific condition or scope to push only. |
| Works in one repo, fails when you reuse the workflow | The reusable workflow's `job_workflow_ref` doesn't match. Add it to trust conditions. |

---

## 10. Cross-references

- Deeper trust policy patterns + IAM role design → [module 46](46_aws_oidc_trust_policy_deep.md).
- Environments + manual approvals + scoped secrets → [module 30](30_actions_environments_protection.md).
- Self-hosted runners (different identity story — IRSA, not OIDC-to-AWS-role) → [module 28](28_actions_self_hosted_arc_gpu.md).
- Cross-account deploys, CDK + IAM roles → [module 48](48_aws_cdk_cfn_tf_cross_account.md).
- Reusable workflows + `job_workflow_ref` scoping → [module 26](26_actions_reusable_workflows.md).
- Topic 04 (AWS) IAM deep — for the underlying AWS identity model.
