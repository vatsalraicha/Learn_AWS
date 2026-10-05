# 23 — ML platform operators: SageMaker, Vertex AI, Azure ML, MLflow, Kubeflow Pipelines

## Why this module exists

Airflow as orchestrator of ML training/serving systems. AWS has the deepest providers; Azure ML is thinnest.

---

## 1. AWS SageMaker

Provider: `apache-airflow-providers-amazon`. The richest ML operator suite.

| Operator | Use |
|---|---|
| `SageMakerProcessingOperator` | Run a Processing Job (data prep) |
| `SageMakerTrainingOperator` | Training job |
| `SageMakerTuningOperator` | Hyperparameter tuning |
| `SageMakerModelOperator` | Register a model |
| `SageMakerEndpointConfigOperator` + `SageMakerEndpointOperator` | Deploy real-time endpoint |
| `SageMakerTransformOperator` | Batch transform |
| `SageMakerStartPipelineOperator` | Trigger an SM Pipelines pipeline (preferred for compound flows) |
| `SageMakerPipelineSensor` | Wait for SM Pipelines run |
| `SageMakerAutoMLOperator` | Autopilot job |

```python
from airflow.providers.amazon.aws.operators.sagemaker import SageMakerStartPipelineOperator

trigger_sm_pipeline = SageMakerStartPipelineOperator(
    task_id="trigger_sm",
    pipeline_name="prod-ml-pipeline",
    pipeline_params={"InputDataLocation": "s3://myorg/data/{{ ds }}/"},
    deferrable=True,
)
```

For Capital One MLE work: Airflow triggers SageMaker Pipelines; SM Pipelines runs the multi-step ML flow internally; Airflow waits.

---

## 2. GCP Vertex AI

Provider: `apache-airflow-providers-google`.

| Operator | Use |
|---|---|
| `CustomTrainingJobOperator` | Train via custom container |
| `CreatePipelineJobOperator` | Run Vertex AI Pipeline |
| `BatchPredictionJobOperator` | Batch predictions |
| `ModelDeployOperator` | Deploy to endpoint |
| `AutoMLTrainingJobOperator` | AutoML |
| `GenerativeModelGenerateContentOperator` (2024+) | Vertex AI Generative |

```python
from airflow.providers.google.cloud.operators.vertex_ai.custom_job import CreateCustomContainerTrainingJobOperator

train = CreateCustomContainerTrainingJobOperator(
    task_id="train",
    project_id="my-proj",
    region="us-central1",
    display_name="train-{{ ds_nodash }}",
    container_uri="gcr.io/my-proj/train:1.0",
    machine_type="a3-highgpu-8g",
    accelerator_type="NVIDIA_H100_80GB",
    accelerator_count=8,
    args=["--epochs=10"],
)
```

---

## 3. Azure ML

Provider: `apache-airflow-providers-microsoft-azure`. Thinner.

| Operator | Use |
|---|---|
| `AzureMachineLearningOperator` | Submit a job (limited) |

For richer integration: use `PythonOperator` calling Azure ML SDK directly. Or `KubernetesPodOperator` with an Azure ML-aware container.

---

## 4. MLflow

No first-class operators. Use `PythonOperator` + `mlflow` client:

```python
@task
def log_to_mlflow(metrics: dict):
    import mlflow
    mlflow.set_tracking_uri("databricks")          # or http://mlflow.internal
    with mlflow.start_run(run_name="airflow-{{ run_id }}"):
        mlflow.log_metrics(metrics)
```

Lineage challenge: MLflow runs aren't automatically linked to Airflow runs. Add the run_id as a tag.

---

## 5. Kubeflow Pipelines (KFP)

Provider: `apache-airflow-providers-cncf-kubernetes` includes KFP integration patterns.

The common pattern: KFP runs inside K8s; Airflow triggers via the KFP SDK in a PythonOperator. Less common than SageMaker/Vertex.

---

## 6. HuggingFace + Airflow

No first-class. Common pattern: `KubernetesPodOperator` launching a HF Transformers training container.

---

## 7. The Capital One pattern

For ML at Capital One:

```
Airflow DAG (data prep) → Step Functions → SageMaker Pipelines (train) → S3 (model) → KServe deploy via ArgoCD
```

Airflow lives in data engineering (ETL into curated layer). The ML side runs on Step Functions + SageMaker. Airflow's role is at the **data preparation boundary**, not the ML training/serving spine.

This is the architect-grade nuance: don't shoehorn Airflow into ML orchestration when Step Functions is the better fit on AWS.

---

## 8. Anti-patterns

| Anti-pattern | Fix |
|---|---|
| Training in Airflow PythonOperator | Use SageMaker / Vertex / Databricks operator |
| Long-running sync training waits | `deferrable=True` |
| Hardcoded model artifact paths | Templated paths via XCom (small path strings) |
| No model lineage | OpenLineage emit + MLflow tags |

---

## Sanity check

1. SageMaker has the deepest provider. What does `SageMakerStartPipelineOperator` wrap?
2. Vertex AI training — what's the canonical operator for custom containers?
3. Azure ML provider is thinnest. What's the pragmatic workaround?
4. MLflow integration — what lineage challenge needs explicit work?
5. Capital One: where does Airflow fit in their ML stack?

---

## Sources

- [Amazon provider — SageMaker](https://airflow.apache.org/docs/apache-airflow-providers-amazon/stable/operators/sagemaker/)
- [Google provider — Vertex AI](https://airflow.apache.org/docs/apache-airflow-providers-google/stable/operators/cloud/vertex_ai.html)
- [Microsoft Azure provider — ML](https://airflow.apache.org/docs/apache-airflow-providers-microsoft-azure/stable/)
- [MLflow Tracking](https://mlflow.org/docs/latest/tracking.html)

→ Next: [24 — Airflow + dbt (Cosmos)](24_dbt_airflow.md)
