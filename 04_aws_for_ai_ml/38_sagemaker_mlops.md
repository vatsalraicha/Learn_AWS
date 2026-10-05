# Module 38 — SageMaker MLOps

> **What this is:** SageMaker Pipelines, Projects, Model Registry, Model Monitor, Lineage Tracking. The orchestration + governance layer.

---

## 1. SageMaker Pipelines

DAG of ML steps. Two definition styles:

### Python DSL

```python
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import ProcessingStep, TrainingStep
from sagemaker.workflow.model_step import ModelStep

pipeline = Pipeline(name="card-fraud-pipeline", steps=[
    ProcessingStep("preprocess", ...),
    TrainingStep("train", ...),
    ModelStep("register", ...),
])
pipeline.upsert(role_arn=role)
pipeline.start()
```

### @step decorator (2024)

```python
from sagemaker.workflow.function_step import step

@step(instance_type="ml.m5.xlarge")
def preprocess(input_path: str) -> str:
    # ...
    return output_path

@step
def train(data_path: str) -> str:
    # ...
    return model_artifact
```

The decorator pattern compiles to a Pipeline. Easier for Python-first teams.

## 2. Step types

- **ProcessingStep** — preprocessing/postprocessing.
- **TrainingStep** — model training.
- **TuningStep** — hyperparameter tuning.
- **ModelStep / RegisterModelStep** — register to Model Registry.
- **ConditionStep** — branching.
- **ClarifyCheckStep, QualityCheckStep** — bias / quality gates.
- **LambdaStep, CallbackStep** — escape hatches.

## 3. Projects (templated CI/CD)

SageMaker Projects = Service Catalog templates that provision:
- A Git repo.
- CodePipeline for CI/CD.
- A SageMaker Pipeline.
- Model Registry deployment hooks.

Use when: you want a starter MLOps template per use case (regression, classification, NLP, vision).

## 4. Model Registry

Versioned model package store:

- **Model Package Groups** — collections of versions for a single model.
- **Approval status**: PendingManualApproval, Approved, Rejected.
- **Cross-account sharing** — share a registry across the AWS org via RAM.
- **Deploy from registry** to endpoints (real-time, serverless, async, batch).

**Capital One pattern**: Model Registry as the **approval gate**. PR merges to main trigger training; trained model lands in Registry as Pending; manual or automated reviewer approves; downstream deployment triggers.

## 5. Model Monitor

Continuous monitoring of deployed models. Four monitor types:

| | What it detects |
|---|---|
| **Data Quality** | Input data drift (schema, stats) |
| **Model Quality** | Prediction quality (requires ground truth) |
| **Bias Drift** | Bias metrics shifting over time |
| **Feature Attribution Drift** | SHAP attributions shifting (via Clarify) |

Schedules: hourly cron-like. Output: CloudWatch metrics + S3 reports.

## 6. Lineage Tracking

Artifacts, contexts, associations — the audit trail.

- **Artifacts** — model files, data sets, container images.
- **Contexts** — projects, pipelines, environments.
- **Associations** — "this model was trained on this data with this pipeline."

The data structure that backs SR 11-7 audit responses: "show me what data trained this production model and who approved it." Pairs with **rubicon-ml** for git-SHA-linked detail.

## 7. Edge Manager (deprecated)

SageMaker Edge Manager is being deprecated in favor of IoT Greengrass. Move existing edge-ML workloads.

## 8. The MLOps lifecycle (full picture)

```
Code commit
  ↓
CodePipeline / GitHub Actions OIDC
  ↓
Build container, run unit tests
  ↓
SageMaker Pipeline (Processing → Training → Evaluation → Register)
  ↓
Model Registry (Pending)
  ↓
Manual or automated approval
  ↓
Deploy to staging endpoint
  ↓
Shadow test or Inference Recommender
  ↓
Deploy to prod (Inference Components, MME, or KServe)
  ↓
Model Monitor + Lineage Tracking ongoing
  ↓
Drift detected → trigger retraining
```

## 9. 2024-2026 changes

- **@step decorator** for Pipelines.
- **MLflow integration** complements Model Registry.
- **Pipelines + Step Functions interop** improved.
- **Edge Manager deprecated**.

## 10. Pitfalls

- **Step max input/output size** — pass S3 references, not large blobs.
- **Manual approval bottleneck** — gate it on a SLA, fall back to automated approval.
- **Model Monitor without ground truth** — can detect drift but not quality directly.
- **Pipeline failures without retry policy** — single transient failure kills the run.

## 11. Capital One lens

- **SageMaker Pipelines** for training DAG.
- **Step Functions** for outer-loop orchestration (Module 15).
- **Model Registry** as the audit gate.
- **rubicon-ml** for git-SHA-linked experiment tracking (SR 11-7).
- **Model Cards + Clarify** for regulator-facing documentation.

## 12. Sanity check

1. Pipeline Python DSL vs @step decorator — when does each fit?
2. What four monitor types does Model Monitor support?
3. How does Lineage Tracking serve SR 11-7 audit?
4. Why is the Model Registry approval gate critical for regulated finance?
5. Edge Manager — what's it deprecating to?

## 13. Cross-references

- **Module 15** — Step Functions as outer orchestrator
- **Module 35** — Model Cards (in Registry)
- **Module 52** — SR 11-7 + Lineage
- **Module 53** — rubicon-ml integration

## Primary sources

- SageMaker MLOps Whitepaper (archived)
- Research report: [`09_sagemaker.md`](../../research_inputs/04_aws_for_ai_ml/09_sagemaker.md)
