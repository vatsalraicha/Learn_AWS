# Module 30 — EC2 & Accelerators

> **What this is:** EC2 instance families for ML workloads — G5/G6/P4/P5/P5e (NVIDIA), Trainium / Inferentia (AWS chips), EC2 Capacity Blocks, UltraClusters, EFA, Spot economics.

---

## 1. The taxonomy

| Family | Use |
|---|---|
| **M** | General-purpose (CPU+RAM balanced) |
| **C** | Compute-optimized |
| **R** | Memory-optimized |
| **X** | Extra memory |
| **I**, **D** | Storage-optimized |
| **G** | Graphics + general GPU (G5/G6) |
| **P** | Training-grade GPU (P4d/P5/P5e/P5en) |
| **Inf** | Inference accelerators (Inferentia2) |
| **Trn** | Training accelerators (Trainium, Trainium2) |

## 2. NVIDIA GPU instances

| Instance | GPU | VRAM/GPU | Best for |
|---|---|---|---|
| **G5** | A10G (24 GB) | small inference, single-GPU training |
| **G6 / G6e** | L4 / L40S (24/48 GB) | mid-range inference, fine-tuning |
| **P4d / P4de** | A100 (40/80 GB) | distributed training |
| **P5** | H100 (80 GB) | FM-scale training |
| **P5e** | H200 (141 GB) | larger FM training, 2024+ |
| **P5en** | H200 + EFAv3 | tightly-coupled GPU clusters |

## 3. AWS-designed accelerators

- **Trainium (Trn1)** — first-gen training chip. Cheaper per FLOP than NVIDIA.
- **Trainium2 (Trn2)** — 2024 launch; closer to H100 perf at much lower cost. **UltraServer** form factor.
- **Inferentia (Inf1, Inf2)** — inference chips. Inf2 supports larger models.

Trade-off: lower price/perf, but PyTorch / TensorFlow integration via **AWS Neuron SDK** is the long pole. Not all model architectures are well-optimized.

## 4. EC2 Capacity Blocks for ML

**Reserve GPU capacity windows** — guaranteed availability of P4/P5/P5e for 1-182 days.

- Announced 2023; expanded for H100/H200 in 2024.
- Use case: planned multi-day FM training runs where on-demand might not have capacity.
- **Pay for the window** whether you use the GPUs or not — accurate forecasting matters.

## 5. UltraClusters and EFA

**UltraCluster** — thousands of interconnected GPU instances with **Elastic Fabric Adapter (EFA)** networking.

- **EFA** — OS-bypass network adapter; ~100 Gbps with sub-microsecond latency.
- Required for tightly-coupled distributed training (NCCL all-reduce).
- Not all instance types support EFA; the high-end P5/P5e/P5en do.

**EFAv3** (2024) — expanded throughput, lower latency.

## 6. Nitro System

AWS's hypervisor and security boundary. Most modern instances are Nitro-based:
- Hardware-virtualized networking and storage (no hypervisor overhead).
- Security: customer can't access the hypervisor / management plane.
- Underpins all the GPU instance types.

## 7. AMIs (Amazon Machine Images)

For ML workloads:
- **DLAMI (Deep Learning AMI)** — pre-installed with CUDA, cuDNN, NCCL, PyTorch, TensorFlow.
- **Bottlerocket** — minimal container-optimized OS; good for EKS GPU nodes.
- **Custom AMI** — your own image with org-specific tooling.

## 8. Auto Scaling Groups (ASG)

Scale EC2 by launch template + ASG. For GPU workloads, ASG with **mixed instances policy** + **Spot** is common.

## 9. Spot economics for ML

**Up to 90% off On-Demand.** Spot interruption rates by instance family:

| Family | Typical interruption rate |
|---|---|
| `c5`, `c6i` | low (~5%) |
| `m5`, `m6i` | low |
| `p4d` | medium (10-20% in busy regions) |
| `p5`, `p5e` | high — variable; subject to capacity demand |

**For GPU training:** combine Spot + checkpointing every 10-30 minutes. SageMaker Managed Spot Training handles this automatically.

## 10. Placement Groups

Hint to EC2 to place instances physically close (or far):

- **Cluster** — same low-latency network segment. For HPC, NCCL all-reduce.
- **Spread** — different racks. For HA.
- **Partition** — groups of cluster + spread. For Hadoop/Cassandra.

## 11. Pricing examples (us-east-1, May 2026)

- `p5.48xlarge` (8× H100) — ~$98/hr on-demand
- `p5e.48xlarge` (8× H200) — ~$110/hr on-demand
- `g5.xlarge` (1× A10G) — ~$1.00/hr on-demand
- `trn2.48xlarge` — ~$25/hr on-demand (vs ~$98/hr for p5.48xlarge equivalent)

Spot can drop these by 60-90% with availability tradeoffs.

## 12. Capital One lens

For training:
- **P5/P5e** for FM-scale training jobs.
- **EC2 Capacity Blocks** to reserve GPU windows for planned training runs.
- **Trainium2** if cost-driven and model fits AWS Neuron SDK support.

For inference:
- **G6/G6e** for medium-sized inference workloads (KServe pods on EKS).
- **Inf2** where the workload fits Neuron SDK.

## 13. Sanity check

1. P5 vs P5e vs P5en — what's different?
2. When is Trainium2 the right call vs P5?
3. What does EFA enable for distributed training?
4. When does Spot make sense for ML, and what's the operational requirement?
5. EC2 Capacity Blocks — what problem do they solve?

## 14. Cross-references

- **Module 36** — SageMaker training (uses these instance types)
- **Module 40** — HyperPod (clusters of these)
- **Module 44** — self-hosted FM serving on EC2/EKS

## Primary sources

- [`EC2_Capacity_Blocks_ML.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/EC2_Capacity_Blocks_ML.html)
- [`Spot_Best_Practices.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/Spot_Best_Practices.html)
- Research report: [`08_compute_for_ml.md`](../../research_inputs/04_aws_for_ai_ml/08_compute_for_ml.md)
