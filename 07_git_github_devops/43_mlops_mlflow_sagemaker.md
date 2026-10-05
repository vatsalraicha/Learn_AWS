# 43 — ⭐ MLflow Model Registry + SageMaker Pipelines from Actions

> *"The registry is the model-version source of truth. Promotion-by-API replaces 'someone in slack approved it.' "*

## Why this module exists

A model registry is to ML what a container registry is to apps — a versioned, queryable store of artifacts with metadata, stage labels (Dev/Staging/Prod), and promotion gates. The two standards: **MLflow Model Registry** (open source) and **SageMaker Model Registry** (AWS native). Capital One uses both (or one — see context). This module covers the integration patterns from GitHub Actions.

---

## 1. The registry's role

For each trained model version, the registry stores:
- The artifact (or pointer to S3 / OCI registry)
- Metadata: training params, training data ID, source commit SHA, metrics, tags
- Lineage: which dataset, which code, which framework version
- Stage: `Dev` / `Staging` / `Production` / `Archived` (or custom)
- Approval status: who approved, when, with what comment
- The serving image / endpoint config

The registry is THE handoff between training and serving. Training pipelines register; serving pipelines fetch.

---

## 2. SageMaker Model Registry (the AWS-native choice)

```python
import boto3
from sagemaker import Session
from sagemaker.model_metrics import ModelMetrics, MetricsSource

sm = Session()

# Step 1: register a model
model_package = sm.sagemaker_client.create_model_package(
    ModelPackageGroupName="fraud-detector",
    ModelPackageDescription="Trained on Q2 data; commit a1b2c3",
    InferenceSpecification={
        "Containers": [{
            "Image": "763104351884.dkr.ecr.us-east-1.amazonaws.com/pytorch-inference:2.2-cpu-py311",
            "ModelDataUrl": "s3://my-bucket/models/fraud-detector/v3/model.tar.gz",
        }],
        "SupportedContentTypes": ["application/json"],
        "SupportedResponseMIMETypes": ["application/json"],
    },
    ModelApprovalStatus="PendingManualApproval",
    ModelMetrics=ModelMetrics(
        model_statistics=MetricsSource(
            s3_uri="s3://my-bucket/reports/v3-metrics.json",
            content_type="application/json",
        ),
    ).to_dict(),
    CustomerMetadataProperties={
        "commit_sha": "a1b2c3",
        "training_data_version": "ds-2026-04-15",
        "trained_by": "ml-platform/training-pipeline-v2",
        "fairness_status": "passed",
    },
)
print(model_package["ModelPackageArn"])
```

Stages in SageMaker Registry:
- `PendingManualApproval` — newly registered, awaiting MRM review
- `Approved` — MRM signed off, CD can deploy
- `Rejected` — MRM said no

---

## 3. The promotion workflow (CI/CD)

```yaml
# .github/workflows/train-and-register.yml
name: Train + Register
on:
  workflow_dispatch:
  push:
    branches: [main]
    paths: ['src/models/**', 'configs/training.yaml']

permissions:
  id-token: write
  contents: read

jobs:
  train:
    environment: train       # OIDC role for training
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ vars.TRAIN_ROLE_ARN }}
          aws-region: us-east-1

      - name: Trigger SageMaker training job
        id: trigger
        run: |
          # Use boto3 or AWS CLI to start a training job
          JOB_NAME="train-$(date +%s)-${{ github.sha }}"
          aws sagemaker create-training-job ...
          echo "job_name=$JOB_NAME" >> $GITHUB_OUTPUT

      - name: Wait for training
        run: aws sagemaker wait training-job-completed-or-stopped --training-job-name ${{ steps.trigger.outputs.job_name }}

      - name: Get model S3 URI
        id: model
        run: |
          URI=$(aws sagemaker describe-training-job --training-job-name ${{ steps.trigger.outputs.job_name }} \
            --query 'ModelArtifacts.S3ModelArtifacts' --output text)
          echo "uri=$URI" >> $GITHUB_OUTPUT

      - name: Register in SageMaker Model Registry as PendingManualApproval
        run: |
          python scripts/register_model.py \
            --model-uri ${{ steps.model.outputs.uri }} \
            --commit-sha ${{ github.sha }} \
            --data-version "ds-2026-04-15"

      - name: Notify MRM team
        run: |
          curl -X POST $SLACK_WEBHOOK -d '{
            "text": "New model version pending approval: fraud-detector v_${{ github.run_number }}"
          }'
        env:
          SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK }}
```

MRM team approves via the SageMaker UI or via a script that calls `update_model_package` setting `ModelApprovalStatus=Approved`.

Then deploy:

```yaml
# .github/workflows/deploy.yml
on:
  # Triggered by EventBridge rule when a model package's status changes to Approved
  repository_dispatch:
    types: [model-approved]

permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    environment: prod         # manual approval gate + scoped OIDC
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ vars.PROD_DEPLOY_ROLE_ARN }}
          aws-region: us-east-1

      - name: Update SageMaker endpoint to approved model
        run: |
          python scripts/deploy_endpoint.py \
            --endpoint fraud-detector-prod \
            --model-package-arn ${{ github.event.client_payload.model_package_arn }}

      - name: Smoke test endpoint
        run: python scripts/smoke_test.py --endpoint fraud-detector-prod
```

EventBridge → Lambda → GitHub repository_dispatch wires the registry approval → CD workflow.

---

## 4. The MLflow alternative

MLflow has its own Model Registry (open source; self-hostable). Stages: `None`, `Staging`, `Production`, `Archived`.

```python
import mlflow

mlflow.set_tracking_uri("https://mlflow.capital-one-internal.io")

# Register from a logged run
with mlflow.start_run() as run:
    # ... train ...
    mlflow.sklearn.log_model(model, "model", registered_model_name="fraud-detector")
    run_id = run.info.run_id

# Promote
client = mlflow.MlflowClient()
client.transition_model_version_stage(
    name="fraud-detector",
    version="3",
    stage="Production",
    archive_existing_versions=True,
)
```

MLflow Tags + Descriptions hold metadata. Aliases (`@champion`, `@challenger`) are the newer recommended way to mark "the deployed one" (replacing stages).

MLflow integrates with SageMaker via the `mlflow-deployments` plugin — you can register in MLflow + deploy to SageMaker endpoints from one tool.

For Capital One: probably MLflow as the experiment-tracking + cross-cloud registry; SageMaker Model Registry as the AWS-deploy-gate registry. Different layers; both used.

---

## 5. The metadata you should capture per model version

Make these mandatory at registration:
- `commit_sha` — exact source code
- `training_data_id` — exact dataset (DVC hash, lakeFS commit, or S3 versioned URI)
- `framework_version` — torch/tensorflow/sklearn version
- `python_version` — Python interpreter
- `training_run_id` — pointer to the experiment-tracking run (MLflow/W&B)
- `evaluation_metrics` — performance, fairness, calibration
- `model_card_url` — link to the model card markdown
- `attestation_url` — SLSA attestation (see [module 35](35_ghas_sbom_slsa_attestations.md))
- `created_by` — workflow run URL
- `approved_by` — MRM identity + timestamp (set on promotion)

This is the metadata you'll be asked for in an SR 11-7 audit.

---

## 6. Lineage queries

Given a deployed endpoint, you should be able to answer:
- "What model version is running right now?" → `aws sagemaker describe-endpoint`
- "What's the commit SHA for that model?" → registry metadata
- "Show me the validation report for that commit." → registry tag → S3 URI
- "Who approved its deploy?" → SageMaker registry approval history + GitHub deployment history
- "When did we last train?" → MLflow run timestamp
- "What data did it train on?" → registry tag → DVC/lakeFS pointer

If any of these are "uhh let me dig…", your audit story isn't tight.

---

## 7. The cross-account pattern

Capital One has many AWS accounts (per Topic 04 CAPITAL_ONE.md). Pattern:

- **ML Dev account**: training runs, models registered in dev registry
- **ML Staging account**: models replicated from dev (cross-account); staged endpoint
- **ML Prod account**: only approved models from staging, replicated again

Model package replication:
```python
# Replicate to staging
boto3.client("sagemaker").create_model_package(
    SourceModelPackageArn="arn:aws:sagemaker:us-east-1:DEV_ACCT:model-package/...",
    ...
)
```

Or use SageMaker's cross-account model sharing via the registry. Either way, the prod endpoint only ever pulls from the prod-account registry — no direct dev→prod jumps.

---

## 8. Model serving — the runtime

Once deployed:
- SageMaker endpoint, ECS/EKS via KServe (Capital One's stack), Lambda for low-traffic.
- Endpoint config references the model package.
- Updates are zero-downtime via `update_endpoint` with a new endpoint config + waiting for `InService`.

Auto-scaling: SageMaker auto-scaling policy on `InvocationsPerInstance` or custom CloudWatch metrics.

Monitoring: SageMaker Model Monitor for data quality + drift detection, integrated with CloudWatch alarms.

We cover deploy patterns in [module 47](47_aws_deploy_sagemaker_ecs_eks_lambda.md).

---

## 9. SageMaker Pipelines (the orchestration layer)

For complex training flows (data prep → train → eval → register), SageMaker Pipelines is the AWS-native orchestrator.

```python
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import ProcessingStep, TrainingStep
from sagemaker.workflow.step_collections import RegisterModel

prep_step = ProcessingStep(name="Prep", processor=..., inputs=..., outputs=...)
train_step = TrainingStep(name="Train", estimator=..., inputs=...)
register_step = RegisterModel(name="Register", model_package_group_name="fraud-detector", ...)

pipeline = Pipeline(name="fraud-detector-train", steps=[prep_step, train_step, register_step])
pipeline.upsert(role_arn="arn:aws:iam::...:role/sagemaker-execution")
pipeline.start(parameters={"input_data": "s3://..."})
```

Trigger from GitHub Actions:

```yaml
- name: Start SageMaker pipeline
  run: |
    python scripts/start_pipeline.py --pipeline fraud-detector-train --data ${{ inputs.data }}
- name: Wait for completion
  run: aws sagemaker wait pipeline-execution-completed --pipeline-execution-arn $ARN
```

Pipelines auto-track lineage (Step Functions style); the lineage is queryable per execution.

---

## 10. Cross-references

- Model validation gates (CI side) → [module 42](42_mlops_validation_gates.md).
- SR 11-7 compliance posture → [module 37](37_compliance_sr117_audit.md).
- AWS deploy targets (where the model ends up) → [module 47](47_aws_deploy_sagemaker_ecs_eks_lambda.md).
- OIDC role for training vs deploy (per env) → [module 29](29_actions_oidc_aws.md), [module 46](46_aws_oidc_trust_policy_deep.md).
- Rollback workflows (when prod model misbehaves) → [module 45](45_mlops_retraining_rollback.md).
- Topic 04 module 38 (SageMaker MLOps) — for the AWS-side foundations.
