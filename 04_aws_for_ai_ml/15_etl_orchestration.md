# Module 15 — ETL Orchestration Choices

> **What this is:** the decision framework for AWS orchestration — Step Functions vs MWAA vs EventBridge Pipes vs SageMaker Pipelines vs Glue Workflows. Plus a walk-through of the **Capital One MLOps orchestration spine**.

---

## 1. The options

| Tool | Strengths | Weaknesses |
|---|---|---|
| **Step Functions** | Native AWS service integrations (200+), JSON/JSONata definition, error handling, parallel & map states, two flavors (Standard, Express) | State payload size limits, JSON DSL learning curve |
| **MWAA** (Managed Airflow) | Python DAGs, huge ecosystem of operators, familiar to data engineers | Environment management overhead, version upgrades painful, $$$ at scale |
| **EventBridge Pipes** | Source→filter→enrich→target serverless pattern, no Lambda glue needed | Limited per-pipe transformations |
| **EventBridge Rules + Schedules** | Cron + event matching, scheduler GA 2022 | Not a full DAG engine |
| **SageMaker Pipelines** | ML-native (steps for training/processing/registry), integrated with SM Studio, supports @step decorator | SageMaker-only; less flexible for non-ML steps |
| **Glue Workflows** | Native to Glue jobs/crawlers/triggers | Limited; outgrown quickly |

## 2. Step Functions deep

**Standard vs Express:**

| | Standard | Express |
|---|---|---|
| Max duration | 1 year | 5 min |
| Pricing model | Per state transition ($0.025 / 1k) | Per request + execution time |
| Use case | Long-running ML pipelines | High-volume event handling |
| Execution history | Visible | CloudWatch Logs only |

**Variables and JSONata** (2024) — Step Functions added inline variables and JSONata expressions, dramatically reducing the boilerplate. Now you can do `$states.input.txnId` and not need a Lambda just to extract a field.

## 3. MWAA versions and sizing

- MWAA 2.7.x (current stable as of 2026-05).
- Environment classes: `mw1.small` ($0.49/hr), `mw1.medium` ($0.78/hr), `mw1.large` ($1.55/hr), `mw1.xlarge` ($3.10/hr) — plus workers + scheduler + DB. A medium env with 5 workers runs ~$1,500/mo before DAG run cost.
- Upgrade pain: in-place upgrades are non-trivial; many shops spin a new env and migrate DAGs.

## 4. EventBridge Pipes

A serverless source→filter→enrich→target pattern:

```
[Source: SQS]    → [Filter: only orders > $100]
                 → [Enrich: Lambda fetches customer profile]
                 → [Target: SageMaker async endpoint for fraud scoring]
```

No Lambda glue needed for the filter; no SQS-to-Lambda-to-something boilerplate. Patterns once expressed as "Lambda fetches from SQS, applies filter, transforms, calls API" collapse to a 30-line Pipe definition.

## 5. SageMaker Pipelines

ML-native DAG. Steps:
- ProcessingStep, TrainingStep, TuningStep
- ModelStep, RegisterModelStep
- ConditionStep, ClarifyCheckStep, QualityCheckStep
- LambdaStep, CallbackStep (escape hatches)
- **2024**: `@step` decorator — Python function-as-step pattern.
- **MLflow integration**: SageMaker hosts MLflow tracking server.

## 6. Glue Workflows

Limited. Use for DAGs that are 100% Glue. Anything with Lambda, ECS, SageMaker — graduate to Step Functions.

## 7. The Capital One MLOps orchestration spine

Based on their re:Invent 2024 talks and Sr Lead MLE job posting:

```
EventBridge (data-ready event)
    ↓
Step Functions (orchestrator)
    ↓
  ├── Glue (feature engineering)
  ├── SageMaker Processing (preprocessing)
  ├── SageMaker Pipeline (training, evaluation, registration)
  ├── EMR / Databricks (if heavy distributed compute needed)
  ↓
SageMaker Model Registry (approval gate)
    ↓
Deploy Step (SageMaker endpoint or EKS+KServe)
    ↓
SageMaker Model Monitor (closes the loop with drift detection)
```

## 8. Pitfalls

- **Step Functions state payload size limits** — 256 KB. Pass S3 references, not blobs.
- **MWAA env upgrades** — often easier to rebuild than upgrade in place.
- **EventBridge Pipes payload size** — 256 KB before/after enrichment.
- **SageMaker Pipelines step max size** — practical limit on the number of steps and the size of step inputs/outputs.
- **Glue Workflows complexity** — outgrow quickly; bite the Step Functions migration early.

## 9. Capital One lens (talking point)

In an architecture review: *"For new ML pipelines I'd default to Step Functions for orchestration with SageMaker Pipelines for the training sub-DAG, EventBridge Pipes for source-side fan-in, and MWAA only for legacy DAGs the team already has."*

## 10. Sanity check

1. Step Functions Standard vs Express — when does Express pay off?
2. What was the 2024 Step Functions feature that reduced the need for "Lambda just to extract a field"?
3. EventBridge Pipes — what's the source→filter→enrich→target shape useful for?
4. When does Glue Workflows stop scaling, and what do you graduate to?
5. Walk through the Capital One MLOps orchestration spine end-to-end.

## 11. Cross-references

- **Module 13, 14** — Glue (the data layer Step Functions orchestrates)
- **Module 28, 29** — Kinesis / MSK / EventBridge (the streaming sources)
- **Module 38** — SageMaker MLOps (Pipelines deep)
- **Module 53** — Capital One MLOps spine (the integrated view)

## Primary sources

- [`Step_Functions_DeveloperGuide.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/Step_Functions_DeveloperGuide.pdf)
- [`SageMaker_Pipelines_DG.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/SageMaker_Pipelines_DG.pdf)
- Research report: [`05_glue_etl.md`](../../research_inputs/04_aws_for_ai_ml/05_glue_etl.md)
