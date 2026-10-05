# Module 36 — SageMaker Training

> **What this is:** Training Jobs, distributed training (SMDDP, FSDP), Spot training, warm pools, Trainium training, Heterogeneous Clusters, MLflow integration.

---

## 1. Training Jobs — the core

A SageMaker Training Job:

1. Provisions instance(s) of your chosen type.
2. Pulls a Docker image (built-in or BYOC).
3. Mounts S3 input data (or FSx Lustre, or EFS).
4. Runs your training script.
5. Writes output (model artifacts) to S3.
6. Tears down.

Pricing: **per-second** instance-hours. Single-instance or multi-instance.

## 2. Distributed training libraries

### SMDDP (SageMaker Distributed Data Parallel)

AWS-optimized DDP library. Drop-in replacement for PyTorch DDP, optimized for AWS network topology (EFA, NCCL tuning).

### SageMaker Model Parallel (SMP)

Tensor + pipeline parallelism for models too large for one GPU. **SMP v2** integrates with PyTorch **FSDP** (Fully Sharded Data Parallel).

### Native PyTorch FSDP / DeepSpeed

You can also use vanilla PyTorch FSDP or DeepSpeed in a Training Job; SageMaker is the wrapper.

## 3. Spot training (SageMaker Managed Spot Training)

Up to **90% off On-Demand**. SageMaker handles:
- Spot interruption → checkpoint restore.
- Job restart on new instances.
- Max wait time + max run time settings.

Your code must implement **periodic checkpointing** (every 10-30 min for large training).

## 4. Warm pools

A pool of pre-provisioned instances. Subsequent training jobs skip provisioning (~5-10 min savings).

Use for: iterative experimentation where you launch many short jobs back-to-back.

## 5. Trainium training

**Trn1, Trn2** instances for cost-optimized training via AWS Neuron SDK.

- PyTorch and TensorFlow via Neuron compiler.
- Up to ~40% cost reduction vs equivalent NVIDIA.
- Trade-off: not all architectures supported equally well.

**Trainium2 UltraServer** (Dec 2024 GA) — 64-chip super-node, comparable to NVIDIA HGX H100.

## 6. Heterogeneous Clusters

Mix CPU and GPU instances in one job:
- **Data loading workers** on CPU instances.
- **Training workers** on GPU instances.

Decouples data pipeline scaling from model compute. Useful when data preprocessing is the bottleneck.

## 7. Training Compiler (deprecated)

SageMaker Training Compiler (XLA/Inductor-based) is being deprecated in 2025. Use native PyTorch 2.x + `torch.compile()` instead.

## 8. MLflow integration

SageMaker hosts MLflow Tracking Server (2024+). Use as the experiment tracker alongside Training Jobs:

```python
import mlflow
mlflow.set_tracking_uri("arn:aws:sagemaker:...:mlflow-tracking-server/...")
with mlflow.start_run():
    # train...
    mlflow.log_metric("loss", loss)
    mlflow.log_model(model, "model")
```

## 9. Entrypoint patterns

For distributed training:

```python
from sagemaker.pytorch import PyTorch

estimator = PyTorch(
    entry_point="train.py",
    role=role,
    instance_count=8,
    instance_type="ml.p5.48xlarge",
    distribution={
        "torch_distributed": {"enabled": True},  # uses torchrun
        # or "smdistributed": {"dataparallel": {"enabled": True}}
    },
    framework_version="2.4.0",
    py_version="py311",
    hyperparameters={...}
)
estimator.fit({"train": "s3://.../train/", "val": "s3://.../val/"})
```

## 10. 2024-2026 changes

- **SMP v2 + FSDP integration**.
- **Trainium2 UltraServer** GA.
- **Heterogeneous Clusters** matured.
- **MLflow integration** as alternative to SageMaker Experiments (deprecating).
- **Training Compiler deprecation**.

## 11. Pitfalls

- **No checkpointing on Spot** → training restart loses progress.
- **Data loader bottleneck** → GPUs underutilized; check `nvidia-smi` and add CPU workers.
- **Wrong distribution config** → distributed-data-parallel mistakenly runs single-GPU.
- **NCCL timeouts** on slow networks → tune `NCCL_TIMEOUT` higher.
- **Cross-AZ training without EFA** → 10x slower than intra-AZ.

## 12. Capital One lens

For FM training:
- **HyperPod** (Module 40) for multi-day, multi-thousand-GPU jobs.
- **Spot + Capacity Blocks** mix — Capacity Blocks for SLA-bound runs, Spot for resumable experiments.
- **MLflow on SageMaker** for experiment tracking, paired with **rubicon-ml** for git-linked audit trails.

For non-FM training:
- **SageMaker Training Jobs** with Spot.
- **Trainium2** evaluated where compatible.

## 13. Sanity check

1. SMDDP vs FSDP — when does each matter?
2. What's the workflow for Spot training with checkpointing?
3. What problem do Heterogeneous Clusters solve?
4. When is Trainium worth picking over NVIDIA?
5. Why is MLflow integration replacing SageMaker Experiments?

## 14. Cross-references

- **Module 30** — EC2 instance types (the underlying hardware)
- **Module 40** — HyperPod (the FM-scale training cluster)
- **Module 11** — FSx Lustre (training I/O storage)
- **Module 38** — MLOps (Pipelines orchestrating Training Jobs)

## Primary sources

- SageMaker Developer Guide (archived)
- Research report: [`09_sagemaker.md`](../../research_inputs/04_aws_for_ai_ml/09_sagemaker.md)
