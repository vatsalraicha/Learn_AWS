# 30 — 🏦 Environments: protection rules, required reviewers, deployment branches, scoped secrets

> *"GitHub Environments are the prod-gate primitive. Combine with OIDC sub-claim scoping and you have audit-grade deploy controls."*

## Why this module exists

A **GitHub Environment** is a named deployment target (`dev`, `staging`, `prod`) with its own protection rules, secrets, variables, and deployment branch restrictions. For a bank, this is THE mechanism that satisfies "separation of duties" + "manual approval for prod" + "scoped credentials" — without writing custom infrastructure.

---

## 1. The shape

An Environment has:
- **Name** (`dev`, `staging`, `prod`, `prod-canary`, ...)
- **Protection rules** (gates before a job using this env can start):
  - Required reviewers (people or teams who must approve)
  - Wait timer (delay N minutes before starting)
  - Custom protection rules (third-party check, GitHub Apps)
- **Deployment branches** restriction (which refs can deploy to this env)
- **Environment secrets** (only available when running in this env)
- **Environment variables** (same)
- **Deployment history** (who deployed what, when)

Configure: Settings → Environments → New environment.

---

## 2. A typical bank-grade prod environment

```
Environment: prod
├── Required reviewers: @capitalone/ml-ops-leads (2 of 4 approvers)
├── Wait timer: 5 minutes
├── Deployment branches: main only (no tags, no manual override)
├── Secrets:
│   ├── DATABASE_PASSWORD (different value than dev/staging)
│   └── EXTERNAL_API_KEY
├── Variables:
│   ├── AWS_ACCOUNT_ID = "111111111111"
│   ├── SAGEMAKER_ENDPOINT = "fraud-detector-prod"
│   └── ROLE_ARN = "arn:aws:iam::111111111111:role/gh-deployer-prod"
└── Custom protection rule: model-validation-check passed in last 24h
```

A workflow targeting `prod`:

```yaml
jobs:
  deploy-prod:
    environment: prod          # binds environment; triggers all protection rules
    runs-on: ubuntu-latest
    steps:
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ vars.ROLE_ARN }}                # env variable
          aws-region: us-east-1
      - run: aws sagemaker update-endpoint --endpoint-name ${{ vars.SAGEMAKER_ENDPOINT }} ...
        env:
          API_KEY: ${{ secrets.EXTERNAL_API_KEY }}             # env secret
```

When this workflow tries to start:
1. **Deployment branch check**: workflow must be on `main`. If on a feature branch, fails immediately.
2. **Wait timer**: workflow pauses 5 minutes (anti-fat-finger).
3. **Required reviewers**: GitHub notifies reviewers; the job waits for 2 of 4 to approve via the UI.
4. **Custom rules**: GitHub App / external service must pass.
5. Once approved: the job runs with env secrets + variables available.

The deployment shows up in repo Deployments tab with full history.

---

## 3. Required reviewers — the manual gate

Up to **6 individuals or teams** can be listed. The configuration sets:
- **Required reviewers**: who can approve
- **Number of approvals required** (1–6)
- **Allow self-review**: yes/no (usually NO for prod)
- **Prevent self-review** (newer): the actor who triggered the workflow can't approve their own deploy

```yaml
# In Environment settings UI:
Required reviewers:
  - @capitalone/ml-ops-leads (team)
  - @vraicha (specific user)
Number of approvers needed: 2
Allow self-review: No
```

When the job hits the gate, GitHub:
- Sends notification to all eligible reviewers.
- Shows an "Approve and deploy" / "Reject" button in the workflow run UI.
- Records who approved + their comment in the deployment history.

This is the **separation of duties** mechanism for SR 11-7 (see [module 37](37_compliance_sr117_audit.md)) — the person merging the PR can't also be the one approving the prod deploy.

---

## 4. Wait timer

```
Wait timer: 5 minutes
```

After all other gates pass, GitHub waits this long before starting the job. Use cases:
- Window to abort a deploy you regret triggering.
- Spread deploys to avoid overlapping load.
- Time for monitoring/alerting baseline to settle.

Max wait: 43,200 minutes (30 days). Usually 5–15 minutes is plenty.

---

## 5. Deployment branches

```
Deployment branches:
  - Only allow `main`
  # or: All branches
  # or: Selected branches: ['main', 'release/*']
  # or: Custom pattern: 'release/v*.*.*'
  # or: Selected tags: 'v*.*.*'
```

Prevents a workflow on `feature-x` from deploying to prod. If the workflow is on the wrong branch, the job is auto-rejected.

For `prod`: usually `main` only.
For `staging`: usually `main` + `release/*`.
For `dev`: any branch.

---

## 6. Environment-scoped secrets and variables

```bash
# Set via gh CLI
gh secret set DB_PASSWORD --env prod --body "$VALUE"
gh variable set AWS_ACCOUNT_ID --env prod --body "111111111111"

gh secret list --env prod
gh variable list --env prod
```

Resolution: when a job has `environment: prod`, it sees:
1. Env-scoped secrets/variables (highest priority)
2. Repo secrets/variables
3. Org secrets/variables
4. (Workflow `env:` block at YAML level)

Common per-env values:
- `AWS_ACCOUNT_ID` — different account per env
- `DEPLOY_ROLE_ARN` — different role per env (scoped to that env's `sub` claim)
- `SLACK_WEBHOOK` — different channel
- `KUBE_CONTEXT` — different cluster
- Anything that varies by env

---

## 7. Combining with OIDC — the gold-standard pattern

The reason environments + OIDC together = audit-grade:

1. OIDC trust policy on prod IAM role: `sub` must equal `repo:capitalone/cool-ml-service:environment:prod`.
2. Workflow job targets `environment: prod`.
3. Environment requires 2 reviewers + main branch only.

Result:
- Code can ONLY reach prod role from a workflow running in the prod environment.
- The prod environment requires manual approval + main branch.
- A compromised dev workflow can't request the prod role (its JWT doesn't have `environment: prod` in sub).
- The deployment history shows who approved + the commit SHA + the workflow run.

This satisfies **separation of duties** (commit author ≠ deploy approver), **immutable audit trail** (deployment history), and **least privilege** (no long-lived prod credential exists).

---

## 8. Custom deployment protection rules

GitHub Apps can register as **deployment protection rules**. When a workflow job hits an environment gate, GitHub calls your App's webhook; your App returns approve/reject (or queues a pending decision for human).

Common use cases:
- ServiceNow CHG ticket must be open and approved
- PagerDuty must show no active P1 incidents
- Datadog SLO is green
- Model validation score from MLflow must exceed threshold (SR 11-7)
- Internal CMDB cross-check

Once the App approves (or rejects), the workflow proceeds (or fails).

Setting: Environment → "Deployment protection rules" → add Apps from your org's installed Apps.

---

## 9. The deployment history

Every environment has a deployment history (Repo → Deployments tab + Settings → Environments → [env] → Deployments).

Each deployment record:
- Timestamp
- Triggered by (actor)
- Approved by (if reviewers required)
- Workflow + run ID + SHA
- Status (success, failure, in_progress)
- Active/inactive (the latest is "active")

API access:

```bash
gh api repos/capitalone/cool-ml-service/deployments --paginate
gh api repos/capitalone/cool-ml-service/deployments/12345/statuses
```

For SR 11-7 audit: the deployment history is your contemporaneous evidence that every prod change was approved by an authorized person and tied to a specific commit. Export to your audit system; retain per policy.

---

## 10. Strategies

### Promote-through-envs

```yaml
on:
  push:
    branches: [main]

jobs:
  deploy-dev:
    environment: dev
    # ... deploys to dev

  deploy-staging:
    needs: deploy-dev
    environment: staging
    # ... deploys to staging
    # (staging env has 0 reviewers — auto-promote on dev success)

  deploy-prod:
    needs: deploy-staging
    environment: prod
    # ... deploys to prod
    # (prod env has 2 required reviewers — manual approval)
```

One commit → automatic dev + staging → human-approved prod. Standard SaaS pattern, also fits Capital One.

### Canary + full

```yaml
jobs:
  deploy-canary:
    environment: prod-canary
    # ... deploys to 5% of prod
    # (prod-canary env: 1 reviewer, auto-rollback if metrics regress)

  deploy-full:
    needs: deploy-canary
    environment: prod
    # ... deploys to remaining 95%
    # (prod env: 1 reviewer, after canary baked for 30 min)
```

### Per-region

```yaml
strategy:
  matrix:
    region: [us-east-1, us-west-2, eu-west-1]
jobs:
  deploy:
    environment: prod-${{ matrix.region }}
    # ... each region has its own env, gates, secrets
```

Different regions can have different approval requirements (e.g., EU region requires GDPR-trained reviewer).

---

## 11. The pitfalls

❌ **Forgetting `environment: <name>`** in the job — secrets/variables won't be scoped; protection rules won't apply.

❌ **Granting all repo write to a service account** that can bypass environment rules — keep bypass list tiny.

❌ **No deployment branch restriction** — a workflow on a feature branch can deploy to prod.

❌ **Self-review enabled** on prod env — author of code can also approve deploy. SR 11-7 anti-pattern.

❌ **Same secret name at repo level and env level with different values** — confusion when debugging. Use distinct names if scopes differ; or only at env level if env-specific.

❌ **Long wait timer + no escape** — sometimes you need to deploy NOW (urgent prod fix). Have a documented break-glass path with audit logging.

---

## 12. Cross-references

- OIDC sub-claim scoping by environment → [module 29](29_actions_oidc_aws.md).
- The deeper IAM role design per environment → [module 46](46_aws_oidc_trust_policy_deep.md).
- SR 11-7 + deployment audit trail → [module 37](37_compliance_sr117_audit.md).
- Model validation as a custom deployment protection rule → [module 42](42_mlops_validation_gates.md).
- Champion/challenger + canary patterns for ML → [module 44](44_mlops_champion_challenger.md).
