# 25 — AWS Cloud Security Essentials (IAM Deep)

> Cross-link: [Topic 04 Part A (Modules 2-4)](../04_aws_for_ai_ml/) covers IAM, accounts, billing exhaustively. This module is the **DevSecOps subset** — IAM as a security primitive.

## 1. The AWS security model

- **Shared Responsibility**: AWS secures the cloud (hypervisor, datacenters, networking fabric). You secure what's *in* the cloud (your data, your apps, your IAM).
- **Identity is the new perimeter.** In 2026 there is no "trust the VPC"; assume any pod, any function, any user could be compromised. IAM + per-resource policies decide everything.

## 2. Securing the root user

Root user = god mode on the account. Steps you take **once**:
1. Set strong unique password
2. MFA on hardware key (YubiKey/Titan) — not SMS, not authenticator app for root
3. Delete root access keys if any
4. Use root account only for: account-level changes, billing, account closure
5. Set up account contacts (security + billing + operations)
6. Enable **MFA delete** on critical S3 buckets

Lock it in a virtual safe and walk away.

## 3. IAM core concepts

### Principals
- **Users** — long-lived identities (humans); use Identity Center SSO instead
- **Roles** — temporary creds; assumed by services (EC2 role), federated users (SSO), other accounts (cross-account)
- **Groups** — collections of users (not principals themselves)
- **Federated identities** — external (SAML, OIDC) mapped to roles

### Policies
- **Identity-based** — attached to user/role/group; what *they* can do
- **Resource-based** — attached to resource (S3 bucket, KMS key); who can do what to *it*
- **Permission boundaries** — max-permissions cap on a role; useful for delegated admin
- **SCPs (Service Control Policies)** — Organization-level guardrails (deny-by-default at OU)
- **RCPs (Resource Control Policies)** — Org-level on resources (2024 GA)
- **Session policies** — narrow permissions at AssumeRole time

### Permissions evaluation (the precedence)
```
Explicit DENY → wins, always
Else if SCP/RCP doesn't allow → DENY
Else if permission boundary doesn't allow → DENY
Else if identity policy + resource policy don't allow → DENY (implicit)
Else → ALLOW
```

Master this; it answers 80% of "why is X denied?" questions.

## 4. Policy anatomy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowReadS3",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::my-bucket",
        "arn:aws:s3:::my-bucket/*"
      ],
      "Condition": {
        "Bool": { "aws:MultiFactorAuthPresent": "true" },
        "IpAddress": { "aws:SourceIp": "10.0.0.0/8" }
      }
    }
  ]
}
```

`Action` = what (read, write, delete, list). `Resource` = on what. `Condition` = under what circumstances. `Effect` = Allow or Deny.

## 5. The IAM patterns you'll use

### Principle of least privilege
Start narrow; grant only what's needed; expand on demand. Use **IAM Access Analyzer** to detect over-privileged policies and generate policies from CloudTrail history.

### MFA required for sensitive actions
```json
{
  "Effect": "Deny",
  "Action": "*",
  "Resource": "*",
  "Condition": {
    "BoolIfExists": { "aws:MultiFactorAuthPresent": "false" }
  }
}
```
Apply via SCP or to specific roles.

### IP allowlist for human users
```json
"Condition": {
  "NotIpAddress": { "aws:SourceIp": ["10.0.0.0/8", "1.2.3.4/32"] }
}
```

### Service-linked roles
AWS creates these per service (e.g., AWSServiceRoleForRDS); don't modify, don't delete unless removing the service.

## 6. IAM Identity Center (formerly AWS SSO)

The 2026 recommended way to give humans access:
- SCIM-sync from your IdP (Okta, Entra ID, JumpCloud)
- Permission sets defined centrally; assigned per account
- Short-lived credentials (no long-lived access keys for humans!)
- One sign-in across all member accounts

```
Identity Center → Permission Set "Developer" → applied to account 111111 and 222222
                → Permission Set "Admin" → applied only to admin account
                → Permission Set "ReadOnly" → applied across all accounts for auditors
```

## 7. CI/CD authentication — OIDC + IAM Role

The **2026 standard** (covered Module 29 + Topic 07 Module 46):
- GitHub Actions / GitLab CI / CircleCI publish OIDC tokens
- IAM trust policy on a role: "this role can be assumed by tokens from `https://token.actions.githubusercontent.com` matching org `myorg` and repo `myrepo`"
- No long-lived access keys = nothing to leak or rotate

Trust policy example:
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "Federated": "arn:aws:iam::1234:oidc-provider/token.actions.githubusercontent.com" },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": { "token.actions.githubusercontent.com:aud": "sts.amazonaws.com" },
      "StringLike": { "token.actions.githubusercontent.com:sub": "repo:myorg/myrepo:ref:refs/heads/main" }
    }
  }]
}
```

## 8. KMS — encryption keys

- **AWS-managed keys** — created automatically by service (aws/s3, aws/ebs); free
- **Customer-managed keys (CMK)** — you own; ~$1/mo per key + API calls; can rotate, can restrict
- **CloudHSM** — dedicated FIPS-140-2 L3 hardware; expensive; required for some compliance

CMK best practices:
- One CMK per service per account per environment (don't share)
- **Key policy + IAM policy** must both allow (defense in depth)
- **Automatic annual rotation** on
- Use **multi-region keys** for replicated data
- **Key grants** for temporary delegations

## 9. Secrets Manager + Parameter Store

| Feature | Secrets Manager | SSM Parameter Store |
|---|---|---|
| **Cost** | $0.40/secret/mo + $0.05/10k reads | Free standard tier (4KB max), $0.05/10k reads for advanced |
| **Automatic rotation** | Yes (RDS native) | No |
| **Cross-region replication** | Yes | No |
| **Max size** | 64KB | 4KB (std) / 8KB (advanced) |
| **Use case** | DB creds, API keys | Config, env-specific values |

Use SSM Parameter Store for config + free-tier secrets; Secrets Manager when you need rotation or > 4KB.

Both integrate with **External Secrets Operator** for K8s (Module 35).

## 10. Audit baseline (the must-haves)

- **CloudTrail** — every API call; multi-region trail; S3 + CloudWatch destinations
- **Config** — resource configuration history + compliance rules (Module 37)
- **GuardDuty** — threat detection from VPC Flow Logs + DNS logs + CloudTrail
- **Security Hub** — aggregates findings from GuardDuty, Inspector, Macie, Config, IAM Access Analyzer
- **Inspector v2** — vulnerability scanning for EC2, Lambda, ECR
- **Macie** — sensitive-data discovery in S3

Capital One: all of the above, plus **Cloud Custodian** for policy enforcement.

## 11. The IAM mistakes that cause breaches

1. **Wildcard `Resource: *` on `Action: *`** — admin access where dev should have view
2. **Long-lived access keys for humans** — Capital One 2019 root cause adjacent
3. **No MFA on critical roles** — anyone with the access key wins
4. **Trust policy with `Principal: *`** — anyone in the world can assume
5. **IAM role with NetworkPolicy = none** — pod can hit metadata service
6. **Resource policies allowing cross-account without conditions** — supply-chain risk
7. **Sharing keys via Slack/email** — guarantees breach

## 12. Quick self-check

1. What's the precedence order for IAM permission evaluation?
2. What's the difference between SCP and IAM policy?
3. Why use OIDC instead of access keys for CI/CD?
4. When use SSM Parameter Store vs Secrets Manager?
5. What does IAM Access Analyzer do?

(Answers: explicit Deny → SCP → permission boundary → identity policy ∩ resource policy → implicit Deny; SCP is Org-level guardrail (can't grant, only deny), IAM policy is account-level grant; short-lived creds, nothing to leak/rotate, audited; Parameter Store for config + small free secrets, Secrets Manager for rotation + large/cross-region; finds over-privileged policies and generates least-privilege policies from CloudTrail history.)
