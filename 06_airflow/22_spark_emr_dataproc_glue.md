# 22 — Spark family: EMR, EMR Serverless, EMR-on-EKS, Dataproc, HDInsight, AWS Glue

## Why this module exists

Pushing compute to Spark (vs running it in Airflow workers) is the canonical "don't transform in Python" pattern for big jobs.

---

## 1. AWS EMR

Operators in `apache-airflow-providers-amazon`:

| Operator | Use |
|---|---|
| `EmrCreateJobFlowOperator` | Spin up an EMR cluster |
| `EmrAddStepsOperator` | Add Spark steps to cluster |
| `EmrStepSensor` | Wait for step completion |
| `EmrTerminateJobFlowOperator` | Kill cluster |
| `EmrServerlessStartJobOperator` | EMR Serverless — preferred for ad-hoc |
| `EmrContainerOperator` | EMR on EKS — submit jobs to managed K8s |

The "create cluster → add steps → terminate" pattern is the classic EMR-on-EC2 flow. For setup/teardown semantics (module 05), wrap in setup/teardown.

For modern AWS Spark: **EMR Serverless** or **EMR on EKS** beats EC2.

```python
from airflow.providers.amazon.aws.operators.emr import EmrServerlessStartJobOperator

spark_job = EmrServerlessStartJobOperator(
    task_id="run_etl",
    application_id="00abcd...",                  # pre-created EMR Serverless app
    execution_role_arn="arn:aws:iam::...:role/emr-serverless-job",
    job_driver={
        "sparkSubmit": {
            "entryPoint": "s3://myorg-jobs/etl.py",
            "sparkSubmitParameters": "--conf spark.executor.cores=4",
        },
    },
    configuration_overrides={
        "monitoringConfiguration": {
            "s3MonitoringConfiguration": {"logUri": "s3://myorg-emr-logs/"},
        },
    },
    deferrable=True,
)
```

---

## 2. EMR on EKS

For shops already on EKS: run Spark via EMR on EKS — get EKS's elasticity + IAM model.

```python
from airflow.providers.amazon.aws.operators.emr import EmrContainerOperator

spark_step = EmrContainerOperator(
    task_id="run_etl",
    virtual_cluster_id="virt-cluster-id",
    execution_role_arn="arn:aws:iam::...:role/emr-on-eks-job",
    release_label="emr-7.0.0-latest",
    job_driver={"sparkSubmitJobDriver": {"entryPoint": "s3://..."}},
    deferrable=True,
)
```

Alternative: **SparkKubernetesOperator** (via Spark-on-K8s operator) for non-EMR. Less managed.

---

## 3. GCP Dataproc

Provider: `apache-airflow-providers-google`.

| Operator | Use |
|---|---|
| `DataprocSubmitJobOperator` | Submit job to existing Dataproc cluster (Jobs v1 API) |
| `DataprocCreateBatchOperator` | **Dataproc Serverless** — preferred path |
| `DataprocCreateClusterOperator` | Spin up cluster |
| `DataprocDeleteClusterOperator` | Kill cluster |

```python
from airflow.providers.google.cloud.operators.dataproc import DataprocCreateBatchOperator

spark_batch = DataprocCreateBatchOperator(
    task_id="spark_batch",
    project_id="my-proj",
    region="us-central1",
    batch_id="etl-{{ ds_nodash }}",
    batch={
        "pyspark_batch": {
            "main_python_file_uri": "gs://myorg-jobs/etl.py",
        },
        "runtime_config": {"version": "2.2"},
        "environment_config": {
            "execution_config": {
                "service_account": "dataproc-job@my-proj.iam.gserviceaccount.com",
                "subnetwork_uri": "projects/.../subnetworks/dataproc-subnet",
            },
        },
    },
    deferrable=True,
)
```

Dataproc Serverless = no cluster management. The right default.

---

## 4. Azure HDInsight / HDInsight on AKS

Legacy HDInsight is fading; **HDInsight on AKS** (GA 2024) is the newer path. Provider: `apache-airflow-providers-microsoft-azure`.

For most Azure Spark: people use Databricks. HDInsight is for shops that picked it pre-Databricks-Azure-launch.

---

## 5. AWS Glue

| Operator | Use |
|---|---|
| `GlueJobOperator` | Run a Glue Spark/Python job |
| `GlueJobSensor` | Wait for completion |
| `GlueCrawlerOperator` | Run a crawler |
| `GlueDataBrewStartJobOperator` | Run DataBrew |
| `GlueDataQualityRulesetEvaluationRunOperator` | Run a Glue Data Quality ruleset |

Glue ETL jobs are Spark + AWS-managed. Airflow's role: trigger + monitor.

```python
from airflow.providers.amazon.aws.operators.glue import GlueJobOperator

glue_etl = GlueJobOperator(
    task_id="glue_etl",
    job_name="my_etl_job",
    script_location="s3://myorg-glue/scripts/etl.py",
    iam_role_name="GlueETLRole",
    create_job_kwargs={"GlueVersion": "4.0", "NumberOfWorkers": 10},
    deferrable=True,
)
```

---

## 6. SparkKubernetesOperator (generic)

For Spark on K8s without EMR/Dataproc:

```python
from airflow.providers.cncf.kubernetes.operators.spark_kubernetes import SparkKubernetesOperator

spark = SparkKubernetesOperator(
    task_id="spark",
    application_file="spark-app.yaml",                # SparkApplication CRD manifest
    namespace="spark-jobs",
    kubernetes_conn_id="kubernetes_default",
)
```

Requires the [Spark Operator](https://github.com/GoogleCloudPlatform/spark-on-k8s-operator) installed. For shops self-managing Spark on K8s.

---

## 7. Decision tree

```
Need Spark on AWS?
  → Modest scale, intermittent: EMR Serverless
  → Already on EKS: EMR on EKS
  → Long-lived ETL: EMR on EC2
  → Lake-house centric: Databricks (module 21)

Need Spark on GCP?
  → Dataproc Serverless (Batch)
  → Or Databricks on GCP

Need Spark on Azure?
  → Databricks on Azure (most common)
  → HDInsight on AKS (rarely greenfield)

Need pure K8s Spark?
  → SparkKubernetesOperator with Spark Operator
```

---

## 8. The Capital One context

Capital One uses EMR (their Topic 04 references include EMR jobs orchestrating data into Snowflake), Databricks, and Glue. Airflow as the orchestrator above all of them.

The decision criterion Cap One favors: **serverless > managed > cluster**. EMR Serverless and Glue over EMR-on-EC2 where workloads fit.

---

## Sanity check

1. EMR Serverless vs EMR on EKS vs EMR on EC2 — when does each fit?
2. Dataproc Serverless replaces what older Dataproc pattern?
3. `SparkKubernetesOperator` requires what to be installed in the cluster?
4. AWS Glue + Airflow — Airflow's role is what?
5. Capital One favors what compute model for Spark?

---

## Sources

- [Amazon provider — EMR operators](https://airflow.apache.org/docs/apache-airflow-providers-amazon/stable/operators/emr/)
- [Amazon provider — EMR Serverless](https://airflow.apache.org/docs/apache-airflow-providers-amazon/stable/operators/emr/emr_serverless.html)
- [Google provider — Dataproc](https://airflow.apache.org/docs/apache-airflow-providers-google/stable/operators/cloud/dataproc.html)
- [Amazon provider — Glue](https://airflow.apache.org/docs/apache-airflow-providers-amazon/stable/operators/glue.html)
- [Spark Operator for K8s](https://github.com/GoogleCloudPlatform/spark-on-k8s-operator)

→ Next: [23 — ML platform operators](23_ml_platforms.md)
