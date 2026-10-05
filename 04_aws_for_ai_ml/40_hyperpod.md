# Module 40 — SageMaker HyperPod

> **What this is:** purpose-built clusters for foundation-model training — Slurm-based vs EKS-based HyperPod, Recipes, Task Governance, FSx Lustre integration.

---

## 1. The problem HyperPod solves

FM training runs span **days to weeks** on **thousands of GPUs**. At that scale:

- Node failures are inevitable (~1-5% per day on H100).
- Restart-from-scratch wastes compute.
- Manual recovery is a full-time job.

**HyperPod** is AWS's purpose-built cluster for this scale: long-running, fault-tolerant, multi-thousand-GPU jobs.

## 2. Two flavors

### Slurm-based HyperPod (original GA 2023)

Cluster orchestrated by **Slurm** — the HPC standard. Familiar to research teams.

### EKS-based HyperPod (GA 2024)

Cluster orchestrated by **Kubernetes / EKS** — familiar to cloud-native teams. **Aligns with Capital One's KServe + EKS choice.**

## 3. Resilience features

- **Auto-restart on node failure** — replaces a failed node, restores from checkpoint, resumes.
- **Health checks** — proactive detection of degraded GPUs.
- **Lifecycle scripts** — customize node setup (install drivers, mount storage).
- **Cluster controller** monitors the whole cluster.

## 4. HyperPod Recipes

Curated training scripts for popular FM architectures:
- Llama family fine-tuning.
- Falcon fine-tuning.
- Mistral.
- Custom architectures (BYO).

Recipes are a **starting point** — you adapt to your data and config. Faster than building from scratch.

## 5. Task Governance (2024)

Workload management across multi-team clusters:
- Quota allocation per team.
- Priority preemption.
- Fair-share scheduling.

## 6. FSx Lustre storage

HyperPod clusters use **FSx Lustre** for shared training data — terabits/s throughput. Data Repository Association (DRA) syncs to S3 (lazy-load on first access).

## 7. Instance group definitions

A HyperPod cluster is a set of **instance groups** with different roles:
- **Compute group** — training instances (P5/P5e/P5en).
- **Controller group** — Slurm controller (Slurm flavor only).
- **Login group** — SSH access nodes (Slurm flavor).

## 8. Picking Slurm vs EKS-based HyperPod

| | Slurm | EKS |
|---|---|---|
| Familiar to | HPC researchers | Cloud-native engineers |
| Job specification | sbatch / srun | K8s Job / PyTorchJob CRD |
| Operator ecosystem | Slurm modules | Helm + operators |
| Integration with KServe / Karpenter | Limited | Native |
| **Capital One lens** | Possible for research teams | **Strong fit given existing EKS investment** |

## 9. 2024-2026 changes

- **EKS-based HyperPod** GA 2024 — the major addition.
- **Task Governance** GA.
- **Recipes** expanded.

## 10. Pitfalls

- **Underused cluster** — HyperPod costs a lot when idle. Plan capacity.
- **Wrong instance group sizing** — controller too small breaks Slurm flavor.
- **No checkpointing** in your training script — defeats HyperPod's recovery.
- **FSx Lustre cold-start** — first epoch slow without preload.

## 11. Capital One lens

Given Capital One's heavy EKS/KServe investment for inference, **EKS-based HyperPod is the natural fit for FM training**:
- Same EKS skillset.
- Karpenter integration possible for non-HyperPod ancillary workloads.
- Aligns with Sr Lead MLE / Lead MLE JD's "build Kubernetes clusters, PyTorch, TensorFlow on AWS" language.

## 12. Sanity check

1. What problem does HyperPod solve that ordinary Training Jobs don't?
2. Slurm vs EKS HyperPod — what's the audience for each?
3. What are HyperPod Recipes?
4. What's Task Governance, and why does it matter for multi-team clusters?
5. Why does FSx Lustre matter here?

## 13. Cross-references

- **Module 11** — FSx Lustre
- **Module 33** — EKS foundations (the EKS-based HyperPod data plane)
- **Module 36** — SageMaker Training (the non-HyperPod alternative)
- **Module 44** — self-hosted FM (where you'd use HyperPod)

## Primary sources

- SageMaker HyperPod docs (archived)
- Research report: [`09_sagemaker.md`](../../research_inputs/04_aws_for_ai_ml/09_sagemaker.md)
