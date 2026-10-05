# 15 — Airflow on Kubernetes: KubernetesExecutor, KubernetesPodOperator, KEDA scaling

## Why this module exists

Every managed Airflow offering is K8s under the hood. Self-hosted production almost always means Helm on K8s. This module is the K8s-specific Airflow knowledge.

---

## 1. The two K8s patterns

### 1.1 KubernetesExecutor (every task = pod)

```ini
[core]
executor = KubernetesExecutor
```

Already covered in module 04. Recap: each task is a pod. Pros: isolation, per-task resources, per-task SA. Cons: 5-15s pod startup overhead.

### 1.2 KubernetesPodOperator (one task = one pod)

Used with **any** executor (Celery, K8s, etc.). Spawns a one-off pod for THIS task:

```python
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator

train_step = KubernetesPodOperator(
    task_id="train_step",
    namespace="ml-training",
    name="train",
    image="myorg/train:1.0",
    cmds=["python", "train.py"],
    arguments=["--epochs=10"],
    service_account_name="train-sa",                   # IRSA / WIF / Entra MI
    resources={"requests": {"cpu": "4", "memory": "16Gi", "nvidia.com/gpu": "1"},
               "limits":   {"cpu": "8", "memory": "32Gi", "nvidia.com/gpu": "1"}},
    tolerations=[{"key": "nvidia.com/gpu", "operator": "Exists"}],
    node_selector={"workload": "gpu-training"},
    is_delete_operator_pod=True,
    in_cluster=True,
    config_file=None,
    deferrable=True,
    get_logs=True,
)
```

Used with Celery executor: scheduler runs lightweight orchestration in Celery; heavy/specialized work goes to pods.

This is the **Capital One–compatible** pattern: MWAA's Celery + K8sPodOperator hitting an EKS cluster for the actual ML work.

---

## 2. IRSA / WIF / Entra Workload ID for tasks

Each task pod has its own SA. The SA is bound to a cloud IAM principal:

- AWS: IRSA annotation on the SA → IAM role.
- GCP: Workload Identity annotation → GSA.
- Azure: Workload ID annotation → Managed Identity.

The task gets cloud credentials without static keys. Modules 26-28 in Topic 05 cover the binding.

For MWAA + K8sPodOperator on EKS:

```python
KubernetesPodOperator(
    ...
    service_account_name="train-sa",
    in_cluster=False,
    config_file=None,
    kubernetes_conn_id="eks_cluster",        # Airflow Connection with eks config
)
```

MWAA worker uses its execution role to assume into the EKS cluster's IAM; spawns pod with `train-sa`.

---

## 3. The DAG-on-K8s pattern (K8sExecutor + Helm)

For self-host: deploy via the official Apache Airflow Helm chart (or Astronomer's):

```bash
helm install airflow apache-airflow/airflow -n airflow --create-namespace \
  -f values.yaml
```

`values.yaml` highlights:

```yaml
executor: KubernetesExecutor

webserver:
  replicas: 2
  service: { type: ClusterIP }

scheduler:
  replicas: 2

triggerer:
  enabled: true
  replicas: 1

postgresql:
  enabled: false              # use external managed Postgres
data:
  metadataConnection:
    user: airflow
    pass: ""                   # from k8s secret
    host: postgres.internal
    port: 5432
    db: airflow

dags:
  gitSync:
    enabled: true
    repo: git@github.com:myorg/airflow-dags.git
    branch: main
    subPath: dags
    sshKeySecret: airflow-dags-deploy-key
    period: 60s

workers:
  enabled: false              # K8sExecutor — no Celery workers

logs:
  persistence:
    enabled: false
  remote:
    enabled: true
    classRef: airflow.providers.amazon.aws.log.s3_task_handler.S3TaskHandler
    config:
      remote_log_conn_id: aws_default
      remote_base_log_folder: s3://myorg-airflow-logs/

secrets:
  - airflow-fernet-key
  - airflow-secret-key
  - airflow-db-password

extraEnv: |
  - name: AIRFLOW__SECRETS__BACKEND
    value: airflow.providers.amazon.aws.secrets.secrets_manager.SecretsManagerBackend
  - name: AIRFLOW__SECRETS__BACKEND_KWARGS
    value: '{"connections_prefix": "airflow/connections", "variables_prefix": "airflow/variables"}'
```

---

## 4. KEDA autoscaling for Celery workers

If you stick with Celery for short tasks:

```yaml
# KEDA ScaledObject
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata: { name: airflow-worker, namespace: airflow }
spec:
  scaleTargetRef: { name: airflow-worker }
  minReplicaCount: 0          # scale to zero off-hours
  maxReplicaCount: 20
  triggers:
    - type: postgresql
      metadata:
        connectionFromEnv: KEDA_DB_CONNECTION
        query: |
          SELECT count(*) FROM task_instance
          WHERE state = 'queued' AND queue = 'default'
        targetQueryValue: '4'
```

KEDA scales workers based on queue depth in metadata DB. Saves money when idle.

`persistence: false` on workers — they're ephemeral; logs to S3 directly.

---

## 5. Pod templates

For K8sExecutor, define a default pod template:

```yaml
podTemplate: |
  apiVersion: v1
  kind: Pod
  metadata:
    labels: { airflow-worker: "true" }
  spec:
    serviceAccountName: airflow-task
    securityContext:
      runAsNonRoot: true
      runAsUser: 50000
      fsGroup: 50000
    containers:
      - name: base
        image: myorg/airflow-tasks:2.10.3
        resources:
          requests: { cpu: "100m", memory: "256Mi" }
          limits:   { cpu: "500m", memory: "1Gi" }
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: false   # Airflow writes to /opt/airflow
          capabilities: { drop: [ALL] }
```

Each task pod inherits this. Override per task via `executor_config={"pod_override": ...}`.

---

## 6. The DAG sync patterns on K8s

| Pattern | Notes |
|---|---|
| **git-sync sidecar** | Sidecar in scheduler + worker pods that pulls latest from git. Most common. |
| **Image-baked** | DAGs included in custom Docker image; deploy by image tag. Astronomer / regulated shops. |
| **PVC-shared** | Single PVC mounted into all pods; CI writes DAGs there. Now uncommon. |
| **S3/GCS/Blob sync** | MWAA / Composer pattern; not standard for self-host but possible. |

Image-baked is the most secure (DAGs are immutable, signed); git-sync is the most agile.

---

## 7. Networking

Airflow on K8s lives in its own namespace with:

- **NetworkPolicy default-deny** + explicit allows.
- **PSA restricted** (with exception for scheduler/worker pods that need PVC writes — use baseline).
- **Service mesh sidecar** (Istio/Linkerd) for mTLS to internal services.
- **Webserver Ingress** behind oauth2-proxy / API gateway.

---

## 8. The Capital One angle

For C1's AWS-native shop: **MWAA + K8sPodOperator hitting EKS** is the cleanest pattern. MWAA's Celery handles short scheduling work; heavy ML tasks fan out as pods on EKS with their own IRSA SAs.

Alternative: **Astro Hybrid on EKS** — Astronomer manages the control plane; data plane runs in your VPC. More flexibility but pricier.

Module 16 covers MWAA specifically.

---

## Sanity check

1. KubernetesExecutor vs KubernetesPodOperator — when does each fit?
2. KEDA scales Celery workers based on what?
3. Pod template via Helm — what defaults does it set, and how do you override per task?
4. DAG sync via git-sync vs image-baked — trade-offs.
5. MWAA + K8sPodOperator pattern — what does the MWAA worker contribute vs what does the EKS pod contribute?

---

## Sources

- [Apache Airflow Helm Chart](https://airflow.apache.org/docs/helm-chart/stable/index.html)
- [KubernetesPodOperator](https://airflow.apache.org/docs/apache-airflow-providers-cncf-kubernetes/stable/operators.html)
- [KEDA](https://keda.sh/)
- [Astronomer Helm Chart](https://github.com/astronomer/airflow-chart)

→ Next: [16 — **MWAA — AWS Managed Workflows for Apache Airflow**](16_mwaa_aws.md)
