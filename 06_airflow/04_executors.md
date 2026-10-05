# 04 — Executors deep: Sequential, Local, Celery, Kubernetes, CeleryKubernetes, Edge

## Why this module exists

The executor is the architectural decision with the biggest cost and security implications. Pick wrong and you'll fight Airflow for a year.

---

## 1. The executors

| Executor | Concurrency | Where tasks run | Use case |
|---|---|---|---|
| **SequentialExecutor** | 1 task | Same process as scheduler | Smoke tests, SQLite only |
| **LocalExecutor** | N parallel processes | On the scheduler host | Single-machine dev / small prod |
| **CeleryExecutor** | Distributed | Celery workers + Redis/RabbitMQ | The most-deployed production executor |
| **KubernetesExecutor** | One Pod per task | Each task is a K8s Pod | Cloud-native, elastic scale |
| **CeleryKubernetesExecutor** | Hybrid | Celery for short, K8s for long | Best of both worlds |
| **EdgeExecutor** (2.10+) | Remote agents | Hosts outside the cluster | On-prem agents talking to a cloud scheduler |

For new prod deployments in 2025-2026: **KubernetesExecutor** is the dominant pick. CeleryExecutor remains for low-resource shops + workloads with very short tasks (overhead of pod-per-task hurts).

---

## 2. SequentialExecutor

Single-threaded. SQLite as metadata DB. **Test only.** Mentioned for completeness.

---

## 3. LocalExecutor

Multi-process on the scheduler host:

```ini
[core]
executor = LocalExecutor
parallelism = 32
max_active_runs_per_dag = 16
```

Pros: simple; no extra infra; up to ~32 concurrent tasks.

Cons: all tasks run on the scheduler box; one runaway task crashes others; no isolation; can't scale horizontally.

When OK: small teams, < 100 DAGs, < 32 concurrent tasks at peak.

---

## 4. CeleryExecutor — the workhorse

```ini
[core]
executor = CeleryExecutor
[celery]
broker_url = redis://redis:6379/0
result_backend = db+postgresql://airflow:...@postgres:5432/airflow
```

Architecture:
- **Celery workers** (separate Deployment/Pod-set) pull from Redis/RabbitMQ.
- Scheduler enqueues tasks.
- Workers pick up and execute.

Pros:
- Mature; widely understood.
- Workers can scale horizontally.
- Short task overhead is low (worker stays warm).

Cons:
- Workers are long-lived processes — Python package conflicts across tasks.
- Workers idle between tasks consume resources.
- Need Redis + result backend infra.
- No per-task isolation (one bad pickle can crash a worker).

For ETL with 1000+ short tasks/hour: Celery wins.

### 4.1 Celery scaling — Flower + KEDA

[Flower](https://flower.readthedocs.io/) is the Celery monitoring UI. Shows worker count, queue length, task state.

For autoscaling: **KEDA** with Celery queue length metric scales worker pods up/down. Standard pattern on K8s self-host.

---

## 5. KubernetesExecutor — one Pod per task

```ini
[core]
executor = KubernetesExecutor
[kubernetes]
namespace = airflow
worker_container_repository = myorg/airflow
worker_container_tag = 2.10.3
```

Each task runs in a **freshly-spawned K8s Pod**. The Pod uses the image specified by the operator or DAG (via `executor_config={"pod_override": ...}`).

Pros:
- Per-task isolation — each task gets its own Pod with own Python deps.
- Elastic scale — pods are created on demand, terminated when done.
- Right-size resources per task — heavy tasks get big pods, light tasks tiny pods.
- Composes with Karpenter for autoscaling.

Cons:
- Pod startup overhead (~5-15s per task) — bad for many short tasks.
- Image management overhead — each task's image must be available.
- More moving parts to debug.

For ML pipelines, heavy ETL, GPU jobs: K8sExecutor is the right answer.

### 5.1 Pod override pattern

```python
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from kubernetes.client.models import V1Pod, V1Container, V1ResourceRequirements

@task(executor_config={
    "pod_override": V1Pod(
        spec=V1PodSpec(
            containers=[V1Container(
                name="base",
                resources=V1ResourceRequirements(
                    requests={"cpu": "2", "memory": "8Gi"},
                    limits={"cpu": "4", "memory": "16Gi", "nvidia.com/gpu": "1"},
                ),
            )],
            service_account_name="ml-tasks-sa",            # IRSA / WIF
            tolerations=[V1Toleration(key="nvidia.com/gpu", operator="Exists")],
            node_selector={"workload": "gpu-training"},
        ),
    ),
})
def train_model():
    ...
```

Each task can be a different "shape" of pod. Combined with Karpenter, you get cost-efficient per-task scaling.

---

## 6. CeleryKubernetesExecutor — the hybrid

```ini
[core]
executor = CeleryKubernetesExecutor
```

Tasks declared with `queue="kubernetes"` run on K8sExecutor; everything else on Celery. Lets you reserve K8sExecutor for heavy / GPU / long tasks while keeping Celery for high-throughput short tasks.

The pragmatic production pattern when you have both kinds of workloads.

---

## 7. EdgeExecutor (2.10+, experimental)

Long-running edge agents pull tasks from the scheduler over HTTPS. Tasks run on-prem or in restricted networks. Useful for:

- On-prem agents pulling work from MWAA / Astro.
- Air-gapped tasks triggered by central scheduler.
- IoT / edge data collection.

Still maturing as of 2026.

---

## 8. The executor choice matrix

| | LocalExecutor | CeleryExecutor | KubernetesExecutor |
|---|---|---|---|
| Low ops overhead | ✅ | ⚠️ Redis + Flower | ⚠️ K8s cluster |
| Per-task isolation | ❌ | ❌ | ✅ |
| Cost-efficient at scale | ❌ | ⚠️ idle workers | ✅ (with autoscale) |
| Short tasks (<10s) | ✅ | ✅ | ❌ pod overhead |
| Long tasks (>30min) | ❌ resource sharing | ⚠️ ties up worker | ✅ |
| Custom dep per task | ❌ | ❌ same image | ✅ pod_override |
| GPU per task | ❌ | ❌ | ✅ |
| Regulated environment | ⚠️ | ⚠️ | ✅ best audit trail |

---

## 9. Executor and the security boundary

- **LocalExecutor**: task code runs as the scheduler user. Compromised task = compromised scheduler. Don't use for untrusted DAGs.
- **CeleryExecutor**: task runs as the worker user. Compromised task = compromised worker (and the Celery worker's entire deps). Still wide blast radius.
- **KubernetesExecutor**: task runs in its own Pod with its own SA, image, network policy. The strongest isolation. **The right choice for multi-tenant Airflow.**

For Capital One–style: K8sExecutor + per-task IRSA SA + per-task PSA-restricted enforcement is the path.

---

## 10. Managed offerings and executors

| Service | Executor | Choice? |
|---|---|---|
| MWAA | **Celery only** | No choice |
| Cloud Composer 2/3 | **CeleryKubernetes** (Composer 2), **Celery + K8sPodOperator** (Composer 3) | Limited |
| Azure Managed Airflow | KubernetesExecutor | Yes |
| Astronomer Astro | KubernetesExecutor (default) | Yes |
| Self-host Helm chart | Any | Yes |

For Capital One AWS context: **MWAA is Celery-only**. If you need K8sExecutor, you self-host on EKS or use Astro on AWS Hybrid.

---

## Sanity check

1. Pod startup overhead is ~5-15s on K8sExecutor. When does that matter?
2. Why is K8sExecutor the strongest isolation choice for multi-tenant Airflow?
3. What does CeleryKubernetesExecutor give you that pure K8s doesn't?
4. Celery + KEDA — what does KEDA scale on?
5. What's the executor option in MWAA, and why does that constrain architectural choices?
6. `pod_override` lets you customize what per task?

---

## Sources

- [Airflow Executors](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/executor/index.html)
- [Celery Executor](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/executor/celery.html)
- [Kubernetes Executor](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/executor/kubernetes.html)
- [Edge Executor (2.10+)](https://airflow.apache.org/docs/apache-airflow-providers-edge/)
- [Flower](https://flower.readthedocs.io/)
- [KEDA](https://keda.sh/)

→ Next: [05 — DAG authoring](05_dag_authoring.md)
