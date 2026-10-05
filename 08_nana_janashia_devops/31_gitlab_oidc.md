# 31 — Secure IaC Pipeline — GitLab OIDC to AWS

## Why this module exists

Securing the IaC pipeline means securing the credentials it uses. OIDC is the modern way to give CI short-lived AWS credentials without storing long-lived secrets anywhere. This module covers the GitLab-specific OIDC integration with AWS.

## 1. The OIDC pattern (in one paragraph)

GitLab Runners issue a signed OIDC token per job. AWS IAM trusts GitLab's OIDC provider URL + verifies a signed JWT. The trust policy on a role limits assumption to specific (project, branch, environment) tuples. The runner exchanges its token for short-lived AWS credentials via `sts:AssumeRoleWithWebIdentity`.

Result: no AWS access keys in GitLab CI variables. No long-lived secrets to rotate or leak.

## 2. Register GitLab as OIDC provider in AWS

For GitLab SaaS (gitlab.com):
```bash
aws iam create-open-id-connect-provider \
  --url https://gitlab.com \
  --client-id-list https://gitlab.com \
  --thumbprint-list <gitlab-cert-thumbprint>
```

Or in Terraform:
```hcl
data "tls_certificate" "gitlab" {
  url = "https://gitlab.com"
}

resource "aws_iam_openid_connect_provider" "gitlab" {
  url             = "https://gitlab.com"
  client_id_list  = ["https://gitlab.com"]
  thumbprint_list = [data.tls_certificate.gitlab.certificates[0].sha1_fingerprint]
}
```

For self-hosted GitLab, use your own URL.

## 3. Create an IAM Role with GitLab trust policy

```hcl
resource "aws_iam_role" "gitlab_ci" {
  name = "gitlab-ci-deploy"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = aws_iam_openid_connect_provider.gitlab.arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "gitlab.com:aud" = "https://gitlab.com"
        }
        StringLike = {
          # Allow only main branch of myorg/myproject
          "gitlab.com:sub" = "project_path:myorg/myproject:ref_type:branch:ref:main"
        }
      }
    }]
  })
}
```

The `sub` claim is the powerful constraint. Examples:
- `project_path:myorg/myrepo:ref_type:branch:ref:main` — only main branch
- `project_path:myorg/myrepo:ref_type:tag:ref:v*` — only version tags
- `project_path:myorg/myrepo:ref_type:branch:ref:*` — any branch (less safe)
- `project_path:myorg/myrepo:environment:production` — only when GitLab env=production

## 4. GitLab CI consumes the OIDC token

```yaml
# .gitlab-ci.yml
deploy:
  stage: deploy
  image: amazon/aws-cli:latest
  id_tokens:
    GITLAB_OIDC_TOKEN:
      aud: https://gitlab.com
  script:
    - >
      export $(printf "AWS_ACCESS_KEY_ID=%s AWS_SECRET_ACCESS_KEY=%s AWS_SESSION_TOKEN=%s"
      $(aws sts assume-role-with-web-identity
      --role-arn arn:aws:iam::1234:role/gitlab-ci-deploy
      --role-session-name "gitlab-${CI_PIPELINE_ID}"
      --web-identity-token "$GITLAB_OIDC_TOKEN"
      --duration-seconds 3600
      --query 'Credentials.[AccessKeyId,SecretAccessKey,SessionToken]'
      --output text))
    - aws s3 ls
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

The `id_tokens` block tells GitLab to issue an OIDC JWT with the given audience; it's injected as the `GITLAB_OIDC_TOKEN` env var for that job.

## 5. The Terraform IaC pipeline using GitLab OIDC

```yaml
# .gitlab-ci.yml
stages: [validate, plan, apply]

variables:
  AWS_DEFAULT_REGION: us-east-1
  TF_ROOT: terraform/
  TF_STATE_NAME: prod

.assume_role: &assume_role
  before_script:
    - >
      export $(aws sts assume-role-with-web-identity
      --role-arn $AWS_ROLE_ARN
      --role-session-name "tf-${CI_PIPELINE_ID}"
      --web-identity-token "$GITLAB_OIDC_TOKEN"
      --duration-seconds 3600
      --query 'Credentials.[AccessKeyId,SecretAccessKey,SessionToken]'
      --output text | awk '{print "AWS_ACCESS_KEY_ID="$1, "AWS_SECRET_ACCESS_KEY="$2, "AWS_SESSION_TOKEN="$3}')

validate:
  stage: validate
  image: hashicorp/terraform:1.10
  id_tokens: { GITLAB_OIDC_TOKEN: { aud: https://gitlab.com } }
  variables: { AWS_ROLE_ARN: arn:aws:iam::1234:role/tf-plan }
  <<: *assume_role
  script:
    - cd $TF_ROOT
    - terraform init
    - terraform fmt -check -recursive
    - terraform validate

plan:
  stage: plan
  image: hashicorp/terraform:1.10
  id_tokens: { GITLAB_OIDC_TOKEN: { aud: https://gitlab.com } }
  variables: { AWS_ROLE_ARN: arn:aws:iam::1234:role/tf-plan }
  <<: *assume_role
  script:
    - cd $TF_ROOT
    - terraform init
    - terraform plan -out=tfplan
  artifacts:
    paths: [$TF_ROOT/tfplan]

apply:
  stage: apply
  image: hashicorp/terraform:1.10
  id_tokens: { GITLAB_OIDC_TOKEN: { aud: https://gitlab.com } }
  variables: { AWS_ROLE_ARN: arn:aws:iam::1234:role/tf-apply }
  <<: *assume_role
  script:
    - cd $TF_ROOT
    - terraform init
    - terraform apply -auto-approve tfplan
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      when: manual
```

Two roles:
- **tf-plan** — read-only + plan (assumable from any branch)
- **tf-apply** — full apply (trust policy constrains to `ref:main` only)

The two-role split is the **principle of least privilege** at pipeline level.

## 6. Compare to GitHub Actions OIDC

GitHub Actions has equivalent OIDC support. See [Topic 07 Module 29](../07_git_github_devops/29_actions_oidc_aws.md) and [Topic 07 Module 46](../07_git_github_devops/46_aws_oidc_trust_policy_deep.md).

Differences:
- GitHub uses `token.actions.githubusercontent.com` as OIDC provider URL
- `aud` defaults to `sts.amazonaws.com` (or `aws-actions/configure-aws-credentials`)
- `sub` claim format: `repo:owner/repo:ref:refs/heads/main`
- `aws-actions/configure-aws-credentials@v4` action does the assume-role automatically

## 7. Cross-account deploys

Common pattern: GitLab → CI account → cross-account assume → target account.

```hcl
# Target account role (in prod account)
resource "aws_iam_role" "prod_deployer" {
  name = "prod-deployer"
  assume_role_policy = jsonencode({
    Statement = [{
      Effect = "Allow"
      Principal = { AWS = "arn:aws:iam::CI_ACCOUNT_ID:role/gitlab-ci-bridge" }
      Action = "sts:AssumeRole"
      Condition = {
        StringEquals = { "sts:ExternalId" = "shared-external-id-for-mfa" }
      }
    }]
  })
}
```

Pipeline first assumes the CI-account role via OIDC, then chains to target account via cross-account AssumeRole.

## 8. The 12-point secure-pipeline checklist

1. **OIDC + IAM Role** — never long-lived AWS keys in CI vars
2. **Trust policy constrains to specific (project, branch, env)** — `sub` claim wildcards = bad
3. **Two-role split** — plan role read-only, apply role write
4. **Apply only on main + manual approval**
5. **Pipeline runner identity in **CloudTrail** — every API call attributable
6. **Pipeline can't read its own state file** — separate role for state-bucket admin
7. **No `sudo` / no `--privileged` in CI containers**
8. **GitLab Runner on private subnet** — outbound only, no inbound 22
9. **Secrets in GitLab CI Variables only when OIDC isn't possible** — masked + protected
10. **Project Runners over Group Runners** for sensitive projects (avoid noisy-neighbor risk)
11. **`CI_JOB_TOKEN`** for GitLab API access (not personal access tokens)
12. **Scan IaC code with Checkov + tfsec** before plan

## 9. Quick self-check

1. What does the `sub` claim in the GitLab OIDC token contain?
2. Why is splitting "plan role" and "apply role" a security best practice?
3. What's the security benefit of OIDC over AWS access keys in GitLab CI?
4. How does cross-account deploy work with OIDC?
5. Why is `id_tokens` block needed in `.gitlab-ci.yml`?

(Answers: project path + ref type + ref name (e.g., `project_path:myorg/myrepo:ref_type:branch:ref:main`) + optionally environment; least privilege — plan never needs write, so a plan-job compromise can't apply destructive changes; no long-lived secrets to leak/rotate, audited per-job in CloudTrail, scoped to specific (project, branch); first assume CI-account role via OIDC, then chain AssumeRole to target account; tells GitLab to issue an OIDC JWT for that job with the specified audience — required for AWS to verify.)
