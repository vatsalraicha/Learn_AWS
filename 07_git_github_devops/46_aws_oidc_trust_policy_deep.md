# 46 — ⭐ OIDC trust policy deep + per-env IAM role scoping

> *"You already saw the basics in module 29. This is the IAM-detailed version: every claim, every gotcha, every Capital One pattern."*

## Why this module exists

OIDC + AWS is the most-leveraged Sr-Lead pattern in Topic 07. Module 29 covers the basics; this module covers the production-grade trust policy patterns: per-environment role design, multi-account chaining, the `job_workflow_ref` claim for InnerSource pipelines, the security review checklist.

---

## 1. The full claim catalog (cheat sheet)

| Claim | Example value | Best for restricting |
|---|---|---|
| `sub` | `repo:capitalone/repo:ref:refs/heads/main` | Specific repo + branch/tag/env |
| `aud` | `sts.amazonaws.com` | Should always equal this |
| `repository_owner` | `capitalone` | Restrict to specific org |
| `repository` | `capitalone/cool-ml-service` | Specific repo |
| `repository_id` | `12345678` | Specific repo (immutable; survives renames) |
| `environment` | `prod` | Specific GitHub Environment |
| `event_name` | `push` / `pull_request` / `workflow_dispatch` | Restrict by event |
| `ref` | `refs/heads/main` | Branch |
| `ref_type` | `branch` / `tag` | Branch vs tag |
| `actor` | `vraicha` | Specific user (rarely useful — bot identities cover this) |
| `job_workflow_ref` | `capitalone/workflows-org/.github/workflows/deploy.yml@refs/heads/main` | Must call via specific reusable workflow |
| `workflow_ref` | `capitalone/cool/.github/workflows/ci.yml@refs/heads/main` | Specific workflow file |
| `head_ref` | `feature/x` (set only on PR events) | PR source branch |
| `base_ref` | `main` (set only on PR events) | PR target branch |
| `run_attempt` | `1` / `2` / ... | Restrict re-runs |

Combine multiple in your trust policy for defense in depth.

---

## 2. Pattern 1 — branch-restricted role (basic)

```json
{
  "Version": "2012-10-17",
  "Statement": [{
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
  }]
}
```

Use for: a CI role that only main-branch workflows can assume (deploy to dev / staging).

---

## 3. Pattern 2 — environment-bound prod role

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

Combined with the `prod` GitHub Environment having required reviewers + manual approval + main-only deployment-branch — this is the pattern for prod.

Workflow:

```yaml
jobs:
  deploy:
    environment: prod
    permissions: { id-token: write, contents: read }
    steps:
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::PROD_ACCT:role/deployer-prod
```

The role can be assumed ONLY when the workflow runs in `prod` environment (which required manual approval).

---

## 4. Pattern 3 — reusable-workflow-only access (the InnerSource pattern)

```json
{
  "Condition": {
    "StringEquals": {
      "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
      "token.actions.githubusercontent.com:sub": "repo:capitalone/cool-ml-service:environment:prod"
    },
    "StringLike": {
      "token.actions.githubusercontent.com:job_workflow_ref": "capitalone/workflows-org/.github/workflows/sagemaker-deploy.yml@refs/heads/main"
    }
  }
}
```

This is THE Capital One pattern. The prod role can only be assumed:
- From `capitalone/cool-ml-service`
- In `prod` environment
- AND when the calling job uses the central reusable deploy workflow

A service team can't write `aws sagemaker update-endpoint` inline in their workflow and grab the prod role. They have to call the central blessed workflow — which has the org's audit + safety baked in.

---

## 5. Pattern 4 — multi-repo same role

Sometimes one role serves multiple repos (e.g., all ML repos can write to a shared model registry):

```json
{
  "Condition": {
    "StringEquals": {
      "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
      "token.actions.githubusercontent.com:repository_owner": "capitalone"
    },
    "StringLike": {
      "token.actions.githubusercontent.com:sub": [
        "repo:capitalone/ml-service-*:ref:refs/heads/main",
        "repo:capitalone/ml-service-*:environment:prod"
      ]
    }
  }
}
```

Note: `StringLike` accepts list. `repo:capitalone/ml-service-*:*` would also work but is more permissive.

---

## 6. Pattern 5 — tag-based release deploy

```json
{
  "Condition": {
    "StringEquals": {
      "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
      "token.actions.githubusercontent.com:ref_type": "tag"
    },
    "StringLike": {
      "token.actions.githubusercontent.com:sub": "repo:capitalone/cool:ref:refs/tags/v*.*.*",
      "token.actions.githubusercontent.com:ref": "refs/tags/v*.*.*"
    }
  }
}
```

Only push-tag events with semver-style tags can assume. Use for "release deploys come from tags only" pattern.

---

## 7. Pattern 6 — PR-only role (for ephemeral env deploys)

For PR-preview environments (deploy a stack per PR for testing):

```json
{
  "Condition": {
    "StringEquals": {
      "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
      "token.actions.githubusercontent.com:event_name": "pull_request"
    },
    "StringLike": {
      "token.actions.githubusercontent.com:sub": "repo:capitalone/cool:pull_request"
    }
  }
}
```

Scope role permissions tightly — PR-preview should NOT have any prod-data access. Per-PR ephemeral environments in `dev` AWS account only.

---

## 8. The cardinal sin (worth repeating)

❌ **`ForAllValues:StringEquals`** in an Allow:

```json
"Condition": {
  "ForAllValues:StringEquals": {
    "token.actions.githubusercontent.com:sub": "repo:capitalone/cool:..."
  }
}
```

Returns true when the claim is **absent** or differs from your key. An attacker crafting a JWT without that claim gets approved.

✅ **Always use `StringEquals`, `StringLike`, or `StringEqualsIfExists` for Allow.** Use `ForAnyValue` patterns only in Deny statements (where "any one matches" is the desired semantic).

Reference: AWS IAM blog post on the issue, plus multiple customer incidents in 2022–2024.

---

## 9. Multi-account chaining

Capital One has many AWS accounts. Pattern:

**Entry account** (centralized OIDC trust):
```json
{
  "Statement": [{
    "Principal": { "Federated": "arn:aws:iam::ENTRY_ACCT:oidc-provider/token.actions.githubusercontent.com" },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": { ... sub claim restrictions ... }
  }]
}
```

**Target account** (allows chaining from entry):
```json
{
  "Statement": [{
    "Principal": { "AWS": "arn:aws:iam::ENTRY_ACCT:role/github-actions-entry" },
    "Action": "sts:AssumeRole",
    "Condition": {
      "StringEquals": {
        "sts:ExternalId": "capitalone-ml-deployer"
      }
    }
  }]
}
```

Workflow:

```yaml
- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::ENTRY_ACCT:role/github-actions-entry
    aws-region: us-east-1

- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::TARGET_ACCT:role/cross-account-deployer
    role-chaining: true
    aws-region: us-east-1
    role-external-id: capitalone-ml-deployer
```

Benefits:
- One OIDC trust setup (entry account); all target accounts trust the entry role.
- `ExternalId` adds defense against confused-deputy attacks.
- Easier to rotate / audit centrally.

---

## 10. The IAM design checklist

When a Sr Lead designs a deploy role, the checklist:

- ✅ Trust policy uses `StringEquals` / `StringLike`, never `ForAllValues:`
- ✅ `sub` claim restricts to specific repo + environment (or workflow ref)
- ✅ Role has least-privilege permissions for the actual deploy (not `*:*`)
- ✅ Role can only be assumed for `role-duration-seconds` ≤ 1 hour (don't extend unless needed)
- ✅ Role has resource-level conditions where possible (`Resource: "arn:aws:s3:::specific-bucket/*"`)
- ✅ Role's permissions are tagged (`{"Project": "fraud-detector", "Env": "prod"}`)
- ✅ CloudTrail logging is enabled for the role's AWS account
- ✅ A test workflow has verified the role assumes correctly + the operation succeeds
- ✅ The role is documented (which repo/workflow uses it, what it does, who owns it)
- ✅ Quarterly review: is the role still needed? still scoped correctly?

---

## 11. Cross-references

- The basic OIDC setup → [module 29](29_actions_oidc_aws.md).
- Environment-bound deploys → [module 30](30_actions_environments_protection.md).
- Reusable workflows (the `job_workflow_ref` pattern) → [module 26](26_actions_reusable_workflows.md).
- AWS deploy targets where these roles act → [module 47](47_aws_deploy_sagemaker_ecs_eks_lambda.md), [module 48](48_aws_cdk_cfn_tf_cross_account.md).
- Topic 04 IAM modules (foundations).
