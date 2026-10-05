# 45 — ⭐🏦 Automated retraining triggers + model rollback workflows

> *"Two prod scenarios: (a) the model is silently getting worse over time and needs retraining; (b) the model just broke and you need to roll back NOW. Both are workflows you wire up in advance."*

## Why this module exists

The "deployed and forgotten" model is the most common failure mode in production ML. Drift creeps in, performance degrades, and nobody notices for months. The two prevention mechanisms: **scheduled retraining** (proactive) + **drift-triggered retraining** (reactive). Plus the always-needed **rollback** workflow.

For SR 11-7: the ability to roll back AND the documented frequency of retraining are both expected.

---

## 1. The retraining triggers

| Trigger | Mechanism | When |
|---|---|---|
| **Scheduled** | Cron on a workflow | Monthly / quarterly / per business cycle |
| **Drift-detected** | Monitor + alert → workflow_dispatch / repository_dispatch | When drift metric crosses threshold |
| **Manual** | `gh workflow run train.yml` | One-off (new data, hypothesis) |
| **Data-change** | Hook on data pipeline completion | When upstream data refreshes |
| **Performance regression** | Monitor + alert on live precision/recall | When prod metric drops |

A mature pipeline supports all five.

---

## 2. Scheduled retraining

```yaml
# .github/workflows/scheduled-retrain.yml
name: Scheduled retrain
on:
  schedule:
    - cron: '0 6 1 * *'    # 6am UTC, first of each month
  workflow_dispatch:        # also allow manual

jobs:
  retrain:
    uses: capitalone/workflows-org/.github/workflows/train-and-register.yml@v3
    with:
      schedule-source: monthly
    secrets: inherit
```

Notify on completion: "Monthly retrain completed, new model `fraud-detector v_42` pending MRM approval."

For Capital One: at least monthly for fraud / credit-scoring models. Quarterly for slower-moving domains. Document the cadence in the model card.

---

## 3. Drift-triggered retraining

In your model monitoring stack:

```python
# Lambda watching SageMaker Model Monitor drift report
def lambda_handler(event, context):
    drift_score = event["detail"]["drift_score"]
    if drift_score > 0.3:
        # Trigger retrain via GitHub repository_dispatch
        requests.post(
            "https://api.github.com/repos/capitalone/fraud-detector/dispatches",
            headers={"Authorization": f"token {github_token}"},
            json={
                "event_type": "drift-detected",
                "client_payload": {
                    "drift_score": drift_score,
                    "model_endpoint": "fraud-detector-prod",
                    "detected_at": event["time"],
                },
            },
        )
```

In the workflow:

```yaml
on:
  repository_dispatch:
    types: [drift-detected]

jobs:
  retrain:
    uses: capitalone/workflows-org/.github/workflows/train-and-register.yml@v3
    with:
      trigger: drift
      drift-score: ${{ github.event.client_payload.drift_score }}
    secrets: inherit
```

For Capital One scale, the Lambda → repository_dispatch pattern is the standard for "external system needs to trigger CI."

---

## 4. The rollback workflow

The most-important workflow you might never use. Or use at 2am.

```yaml
# .github/workflows/rollback.yml
name: Emergency rollback
on:
  workflow_dispatch:
    inputs:
      endpoint:
        description: "Endpoint to roll back"
        required: true
        type: string
      target-version:
        description: "Model version to roll back to (or 'previous' for last-deployed)"
        required: true
        type: string
        default: "previous"
      reason:
        description: "Reason (required for audit log)"
        required: true
        type: string

permissions:
  id-token: write
  contents: read

jobs:
  rollback:
    environment: prod-emergency        # 1 approver only (faster than normal prod gate)
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v6

      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ vars.PROD_DEPLOY_ROLE_ARN }}
          aws-region: us-east-1

      - name: Determine target version
        id: target
        run: |
          if [ "${{ inputs.target-version }}" == "previous" ]; then
            VERSION=$(python scripts/last_deployed.py --endpoint ${{ inputs.endpoint }})
          else
            VERSION="${{ inputs.target-version }}"
          fi
          echo "version=$VERSION" >> $GITHUB_OUTPUT

      - name: Rollback endpoint
        run: |
          python scripts/deploy_endpoint.py \
            --endpoint ${{ inputs.endpoint }} \
            --model-version ${{ steps.target.outputs.version }}

      - name: Wait for endpoint InService
        run: |
          aws sagemaker wait endpoint-in-service --endpoint-name ${{ inputs.endpoint }}

      - name: Smoke test
        run: python scripts/smoke_test.py --endpoint ${{ inputs.endpoint }}

      - name: Notify + log
        run: |
          curl -X POST $SLACK_WEBHOOK -d '{
            "text": "🚨 ROLLBACK executed: ${{ inputs.endpoint }} → ${{ steps.target.outputs.version }}",
            "blocks": [
              {"type":"section","text":{"type":"mrkdwn","text":"*Reason:* ${{ inputs.reason }}\n*Triggered by:* ${{ github.actor }}\n*Run:* ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"}}
            ]
          }'
        env:
          SLACK_WEBHOOK: ${{ secrets.SLACK_ALERTS_WEBHOOK }}
```

Properties:
- Triggered only by `workflow_dispatch` (not on push) — explicit human action.
- Requires `reason` input — captured in audit log.
- Environment `prod-emergency` has 1 approver (vs prod's 2) — faster.
- Smoke test confirms rollback worked before declaring success.
- Slack notification + audit log.

Goal: from "we need to roll back" to "rolled back + verified" in <5 minutes.

---

## 5. Test the rollback drill

Untested rollback = no rollback. Run a chaos drill quarterly:

1. Pick a non-critical staging endpoint.
2. Simulate failure (deploy a bad model deliberately).
3. Execute rollback workflow.
4. Measure: how long until back to good state? Did anything break?
5. Document; fix any issues; rerun.

For SR 11-7: the drill is required evidence. Auditors want to see the runbook + the drill log.

---

## 6. Pinned-previous-version pattern

To make rollback fast, keep the previous endpoint config readily restorable.

**SageMaker pattern**: every deploy creates a new endpoint configuration (versioned). Rollback = `update_endpoint` to a previous config name.

```python
# Get previous configs
configs = sm.list_endpoint_configs(
    NameContains="fraud-detector-prod-",
    SortBy="CreationTime",
    SortOrder="Descending",
    MaxResults=10,
)
previous_config = configs["EndpointConfigs"][1]["EndpointConfigName"]   # [0] is current

sm.update_endpoint(
    EndpointName="fraud-detector-prod",
    EndpointConfigName=previous_config,
)
```

Don't delete endpoint configs immediately after upgrades — keep the last N for rollback.

---

## 7. The "model is bad, what now?" runbook

When prod metrics start regressing:

1. **Identify the bad model.** Compare metrics now vs last week — `gh release view` + SageMaker Model Registry to find when the current model deployed.
2. **Decide rollback or hot-fix.** If a clear regression caused by the new model: rollback. If the world changed and the model needs retraining: hot-fix means urgent retrain + canary.
3. **Execute rollback** (workflow above) — <5 min back to last-known-good.
4. **Stop new deploys** during investigation.
5. **Triage**: drift? upstream data issue? code bug?
6. **Fix**: retrain or revert code commit.
7. **Re-deploy** through normal promote-with-approval flow once confirmed fix.
8. **Postmortem** (required for SR 11-7-grade incidents).

---

## 8. Automated retraining freshness checks

```yaml
# .github/workflows/check-staleness.yml
on:
  schedule:
    - cron: '0 8 * * 1'   # Monday 8am UTC

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - run: |
          # Find model age
          LAST_TRAIN=$(python scripts/last_model_age.py --endpoint fraud-detector-prod)
          if [ "$LAST_TRAIN" -gt 60 ]; then
            echo "::warning::Model is $LAST_TRAIN days old; consider retrain"
            curl -X POST $SLACK_WEBHOOK -d "{\"text\":\"Model fraud-detector-prod is $LAST_TRAIN days old\"}"
          fi
        env:
          SLACK_WEBHOOK: ${{ secrets.SLACK_ML_TEAM }}
```

Weekly nag if model is >60 days old. Pairs with monthly retrain schedule as a backstop.

---

## 9. Retraining triggers from MLflow / SageMaker Model Monitor

SageMaker Model Monitor publishes drift reports to CloudWatch + S3. EventBridge rule:

```python
# Terraform / CDK
from aws_cdk import aws_events as events, aws_events_targets as targets

rule = events.Rule(
    self, "DriftRule",
    event_pattern={
        "source": ["aws.sagemaker"],
        "detail_type": ["SageMaker Model Monitor Status Change"],
        "detail": {"status": ["CompletedWithViolations"]},
    },
)
rule.add_target(targets.LambdaFunction(drift_handler_lambda))
```

The Lambda then triggers the GitHub Actions workflow via `repository_dispatch`.

---

## 10. Cross-references

- The model registry (where rollback finds "previous" versions) → [module 43](43_mlops_mlflow_sagemaker.md).
- Champion/challenger (the prod-monitoring layer that detects when rollback's needed) → [module 44](44_mlops_champion_challenger.md).
- Validation gates → [module 42](42_mlops_validation_gates.md).
- SR 11-7 audit requirements (rollback evidence) → [module 37](37_compliance_sr117_audit.md).
- AWS deploy to SageMaker endpoints → [module 47](47_aws_deploy_sagemaker_ecs_eks_lambda.md).
