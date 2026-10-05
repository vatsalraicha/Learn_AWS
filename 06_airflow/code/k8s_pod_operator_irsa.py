"""
KubernetesPodOperator with IRSA — Capital One–compatible MWAA + EKS pattern.

The MWAA worker (running in MWAA's Fargate) uses its execution role to
authenticate to the EKS cluster. The spawned pod uses its own ServiceAccount
(IRSA-rolled) to access AWS APIs (S3, KMS, Secrets Manager).

References: Topic 05 modules 26 (EKS), 30 (model serving); Topic 06 modules 04,
15 (Airflow on K8s), 16 (MWAA), 23 (ML platforms).
"""
from datetime import datetime, timedelta

from airflow.decorators import dag
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from kubernetes.client import V1ResourceRequirements, V1EnvVar, V1Toleration


@dag(
    dag_id="train_model_on_eks",
    start_date=datetime(2026, 1, 1),
    schedule=None,                      # trigger-only
    catchup=False,
    default_args={
        "owner": "ml-platform",
        "retries": 0,                   # ML training: don't auto-retry
        "execution_timeout": timedelta(hours=24),
    },
    tags=["ml", "eks", "training"],
)
def train_model_on_eks():
    train = KubernetesPodOperator(
        task_id="train",
        # The K8s connection — MWAA Connection of type "kubernetes" pre-configured
        kubernetes_conn_id="eks_prod",
        in_cluster=False,
        namespace="ml-training",
        name="train-{{ ds_nodash }}-{{ ti.try_number }}",
        image="123456789012.dkr.ecr.us-east-1.amazonaws.com/myorg/train:1.4.0@sha256:abc...",

        # IRSA: this SA is bound to an IAM role with S3 read on the data bucket
        service_account_name="train-sa",
        labels={
            "app": "train",
            "team": "ml-platform",
            "cost-center": "ml-training",
        },

        cmds=["torchrun"],
        arguments=[
            "--nproc-per-node=8",
            "--nnodes=1",
            "/workspace/train.py",
            "--data-uri=s3://myorg-ml-data/2026/{{ ds }}/",
            "--checkpoint-uri=s3://myorg-ml-checkpoints/{{ run_id }}/",
            "--epochs=10",
        ],
        env_vars=[
            V1EnvVar(name="TORCH_NCCL_DEBUG", value="WARN"),
            V1EnvVar(name="AWS_DEFAULT_REGION", value="us-east-1"),
        ],

        container_resources=V1ResourceRequirements(
            requests={"cpu": "8",  "memory": "64Gi",  "nvidia.com/gpu": "8"},
            limits  ={"cpu": "16", "memory": "128Gi", "nvidia.com/gpu": "8"},
        ),
        tolerations=[
            V1Toleration(key="nvidia.com/gpu", value="training", operator="Equal", effect="NoSchedule"),
        ],
        node_selector={"workload": "ml-training"},

        # Security context — PSA-restricted compatible
        security_context={
            "runAsNonRoot": True,
            "runAsUser": 10001,
            "fsGroup": 10001,
        },
        container_security_context={
            "allowPrivilegeEscalation": False,
            "readOnlyRootFilesystem": False,  # PyTorch writes checkpoints
            "capabilities": {"drop": ["ALL"]},
        },

        get_logs=True,
        is_delete_operator_pod=True,    # cleanup
        deferrable=True,                # offload wait to Triggerer
        startup_timeout_seconds=300,
    )

    train


train_model_on_eks()
