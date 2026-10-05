# 31 — Training on K8s: Kubeflow Training Operator, Volcano, NVIDIA GPU Operator, Karpenter

## Why this module exists

Distributed training has different K8s semantics than serving: gang scheduling (all pods or none), rendezvous (rank assignment), GPU topology, and aggressive autoscale-down post-completion. This module covers the four primitives.

---

## 1. Kubeflow Training Operator

CRDs for distributed training: `PyTorchJob`, `TFJob`, `MPIJob`, `PaddleJob`, `XGBoostJob`, `JAXJob`. Each handles framework-specific rendezvous and lifecycle.

```yaml
apiVersion: kubeflow.org/v1
kind: PyTorchJob
metadata: { name: train-bert-2026q2, namespace: ml-training }
spec:
  pytorchReplicaSpecs:
    Master:
      replicas: 1
      restartPolicy: OnFailure
      template:
        spec:
          serviceAccountName: train-sa
          containers:
            - name: pytorch
              image: nvcr.io/nvidia/pytorch:24.06-py3
              command: ["torchrun", "--standalone", "--nnodes=1", "--nproc-per-node=8", "train.py"]
              resources: { limits: { nvidia.com/gpu: 8 } }
    Worker:
      replicas: 7
      restartPolicy: OnFailure
      template: { ... }
```

The operator sets `MASTER_ADDR`, `MASTER_PORT`, `WORLD_SIZE`, `RANK` env vars per pod. `torchrun` consumes them; PyTorch initializes the process group automatically.

For 64 GPUs across 8 nodes: 1 Master + 7 Workers, each with `nvidia.com/gpu: 8`.

---

## 2. Volcano — gang scheduling

Default K8s scheduler picks pods one at a time. For training with 64 GPUs, you don't want 7 pods running while pod 8 waits for capacity — that wastes GPU hours. **Gang scheduling** says: schedule all-or-nothing.

[Volcano](https://volcano.sh/) is the CNCF Incubating batch scheduler:

```yaml
apiVersion: scheduling.volcano.sh/v1beta1
kind: PodGroup
metadata: { name: train-bert, namespace: ml-training }
spec:
  minMember: 8                        # 8 pods minimum to start
  queue: ml-default
---
# Pod template includes:
metadata:
  annotations:
    scheduling.k8s.io/group-name: train-bert
spec:
  schedulerName: volcano
```

Volcano + Training Operator is the standard production combo for large training.

---

## 3. NVIDIA GPU Operator

Helm-installable. Manages:

- **NVIDIA driver** (matching kernel).
- **Container Toolkit** (for nvidia-container-runtime).
- **Device Plugin** (advertises `nvidia.com/gpu` resource to K8s).
- **GPU Feature Discovery** (labels nodes with `nvidia.com/gpu.product=H100` etc).
- **DCGM Exporter** (Prometheus metrics).
- **MIG Manager** (for MIG-capable GPUs).
- **PSA-restricted** compatibility.

```bash
helm install gpu-operator nvidia/gpu-operator -n gpu-operator --create-namespace \
  --set toolkit.version=v1.16.0 \
  --set driver.version=550.90.07 \
  --set migManager.enabled=true
```

For Capital One–style stack: GPU Operator is non-negotiable on any GPU node pool.

---

## 4. MIG, time-slicing, MPS — capacity strategies

| Strategy | Hardware | Use case |
|---|---|---|
| **MIG** | A100/H100/H200 | Multi-model serving with isolation; up to 7 instances per A100-80GB |
| **Time-slicing** | Any | Multi-tenant training without isolation (don't recommend) |
| **MPS** | Any | Multiple processes share one GPU; CUDA-native; co-located inference |

For training: full GPU per pod. For serving small models: MIG.

---

## 5. Distributed-comm primitives

NCCL is the GPU-to-GPU comm library. Optimal NCCL needs:

- **NVLink** between GPUs in same node (P5/P5e instances on AWS).
- **InfiniBand** or **EFA** (AWS) between nodes for multi-node.
- **NCCL_TOPO_FILE** for topology hints.

For multi-node on EKS:

```yaml
# Pod annotations for EFA
metadata:
  annotations:
    k8s.amazonaws.com/efa-resource: "true"
spec:
  containers:
    - resources:
        limits:
          nvidia.com/gpu: 8
          vpc.amazonaws.com/efa: 4                   # 4 EFA interfaces
```

EFA gives ~3.2 Tbps inter-node on `p5.48xlarge`. Without it, multi-node training is bottlenecked at GPU 1's pace.

---

## 6. Karpenter for GPU autoscaling

```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata: { name: gpu-h100-training }
spec:
  template:
    metadata:
      labels: { workload: training }
    spec:
      taints:
        - { key: nvidia.com/gpu, value: "h100", effect: NoSchedule }
      requirements:
        - { key: kubernetes.io/arch, operator: In, values: [amd64] }
        - { key: node.kubernetes.io/instance-type, operator: In,
            values: [p5.48xlarge, p5e.48xlarge, p5en.48xlarge] }
        - { key: karpenter.sh/capacity-type, operator: In, values: [on-demand, spot] }
      nodeClassRef: { name: gpu-default-ec2 }
  disruption:
    consolidationPolicy: WhenEmpty
    consolidateAfter: 30s              # training is fail-fast; can churn nodes
    expireAfter: 168h
```

For training: `consolidateAfter: 30s` is OK (jobs are batched). For serving: 5m+ as in module 26.

For multi-node training: **EC2 Capacity Blocks for ML** is the AWS primitive to reserve capacity for fixed time windows (1-8 weeks). Karpenter can target capacity blocks. Required when chasing scarce P5 capacity.

---

## 7. Spot instances for training — checkpointing

Spot is 70-80% cheaper but interruptible. For training:

- Checkpoint every 30 min or per-epoch.
- Use **Karpenter Spot** capacity type.
- On interruption (2-min warning), kubelet evicts; PyTorchJob's `OnFailure` policy reschedules.
- **The job resumes from last checkpoint** — write a resume-from-checkpoint code path in training scripts.

This is the cost lever that turns $1M training into $200K. Capital One's published FinOps culture would care.

---

## 8. Topology-aware scheduling

For 64-GPU training where same-rack matters: **Topology Aware Scheduling** (TAS) hints to scheduler "place these 8 pods on nodes in the same rack."

The K8s primitive: `topologySpreadConstraints` + node labels for rack/AZ:

```yaml
topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: topology.kubernetes.io/zone
    whenUnsatisfiable: DoNotSchedule
    labelSelector: { matchLabels: { job-name: train-bert } }
```

For training: prefer same-AZ (minimize inter-AZ cost + latency).

---

## 9. The Training Operator alternatives

- **Ray on K8s** (KubeRay) — Ray cluster as RayCluster CRD; flexible Python parallelism.
- **DeepSpeed / FSDP / Megatron** — frameworks for >7B-param training; called from PyTorchJob.
- **NVIDIA NeMo Curator + NeMo Megatron** — LLM-specific.
- **Argo Workflows** — for DAGs of training steps (compose with PyTorchJob inside).

For ML platforms: Training Operator is the standard; Ray is the alternative for HPC-flexible workloads.

---

## 10. The training pipeline on K8s

```
S3 bucket (raw data) → Glue/EMR transform → S3 bucket (features) → KubeFlow PyTorchJob → S3 (checkpoints) → KServe InferenceService
                                                       ↑
                                                  Argo / Step Functions orchestration
                                                       ↑
                                                  Triggered by data freshness / schedule
```

For Capital One: Step Functions orchestrates (not Airflow); PyTorchJob runs on EKS; checkpoints go to S3 with KMS; model artifact promoted to KServe via GitOps.

---

## Sanity check

1. PyTorchJob auto-sets which four env vars per pod, and what do they mean?
2. Why does multi-node distributed training need gang scheduling?
3. EFA on EKS — what does it accelerate, and on which instance types?
4. Spot for training: what's the one code change you need to make in training scripts?
5. MIG vs time-slicing — pick one for "model serving with strict isolation."
6. Step Functions vs Argo Workflows for training orchestration — what's the Capital One choice?

---

## Sources

- [Kubeflow Training Operator](https://www.kubeflow.org/docs/components/training/overview/)
- [Volcano](https://volcano.sh/en/docs/)
- [NVIDIA GPU Operator](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/)
- [NVIDIA MIG](https://docs.nvidia.com/datacenter/tesla/mig-user-guide/)
- [AWS EFA on EKS](https://docs.aws.amazon.com/eks/latest/userguide/node-efa.html)
- [Karpenter](https://karpenter.sh/)
- [EC2 Capacity Blocks for ML](https://aws.amazon.com/ec2/capacityblocks/)
- [KubeRay](https://docs.ray.io/en/latest/cluster/kubernetes/index.html)

→ Next: [32 — Service mesh & zero-trust — Istio, Linkerd, Cilium, SPIFFE/SPIRE](32_service_mesh.md)
