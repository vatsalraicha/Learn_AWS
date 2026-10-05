# Module 31 — ECS + Fargate + AWS Batch

> **What this is:** the container orchestration alternatives to EKS — ECS (AWS-native), Fargate (serverless containers), AWS Batch (managed batch with EC2 or Fargate or EKS backend).

---

## 1. ECS

**Elastic Container Service** — AWS-native container orchestrator. Simpler than EKS but less portable.

- **Task definition** — JSON spec of containers, CPU, memory, networking, IAM.
- **Service** — desired count of tasks, load balancer integration.
- **Cluster** — logical grouping; can run on EC2 (you manage) or Fargate (AWS manages).
- **Capacity providers** — EC2 ASG (you choose instance types) or Fargate.

## 2. Fargate

**Serverless container runtime**. You give it a task definition; AWS runs it. No EC2 management.

- Platform versions (1.3, 1.4) define feature set. Currently 1.4 is the default.
- **Task networking modes** — `awsvpc` is default; each task gets its own ENI.
- **Up to 200 GB ephemeral storage** (raised from 20 GB).
- Pricing per vCPU + memory + duration.
- **No GPU support on Fargate** — for GPU tasks, use ECS-on-EC2 or EKS.

## 3. ECS vs EKS

| | ECS | EKS |
|---|---|---|
| Control plane | AWS-managed (free for ECS itself) | AWS-managed ($0.10/hr per cluster) |
| Portability | AWS-only | Kubernetes (portable) |
| Operator ecosystem | Limited | Huge (Helm, KServe, Karpenter, Istio, etc.) |
| Best for | Simple workloads, AWS-only commitment | Complex platforms, hybrid/multi-cloud, K8s-native ML tooling |

**Capital One pattern:** EKS for ML model serving (per Lead MLE job posting confirming KServe + Kubernetes). ECS likely for simpler service-tier deployments where K8s overhead isn't justified.

## 4. AWS Batch

Managed batch job runner. **Capacity environment** can use:
- EC2 (you can use Spot, Auto Scaling).
- Fargate.
- **EKS** (the EKS backend lets you run Batch on your existing EKS cluster — great for ML training and batch processing).

**Multi-Node Parallel (MNP) jobs** — for tightly-coupled distributed training (MPI / NCCL).

**Array jobs** — parameterized N-task fan-out.

**Job queues** — priority-ordered queues; fair-share scheduling across users.

## 5. ECS Anywhere

Run ECS tasks on **on-prem hardware** (or third-party cloud). AWS-managed control plane; data plane is your iron. Used for hybrid scenarios.

## 6. Pricing comparison (~)

- **ECS on EC2** — pay only for EC2 instances.
- **ECS on Fargate** — ~40-60% more expensive than equivalent EC2 (but no ops overhead).
- **Fargate Spot** — interruptible, ~70% cheaper than Fargate on-demand.
- **AWS Batch on EC2 Spot** — cheapest path for non-urgent batch.

**Rule of thumb:** Fargate makes sense when EC2 utilization < ~40%. Above that, EC2 wins.

## 7. Capital One lens

- **EKS + KServe** for ML model serving (the differentiator).
- **ECS / Fargate** for simpler service-tier deployments.
- **AWS Batch on EKS** for ML batch training jobs.
- **AWS Batch with EC2 Spot** for cost-sensitive non-urgent batch.

## 8. Pitfalls

- **Fargate without GPUs** for ML training that needs them — pick ECS-on-EC2 or EKS instead.
- **ECS service auto-scaling on CPU only** — usually need a custom metric (queue depth, latency).
- **AWS Batch job queue without retries** — silent failure.
- **Mixing ECS and EKS** in the same team often creates split expertise debt.

## 9. Sanity check

1. ECS vs EKS — when does ECS win?
2. What does Fargate not support that EC2 does (relevant to ML)?
3. AWS Batch with EKS backend — when does that matter?
4. What's a Multi-Node Parallel job?
5. ECS Anywhere — niche use case?

## 10. Cross-references

- **Module 33** — EKS foundations
- **Module 36** — SageMaker training (alternative to AWS Batch for ML)
- **Module 54** — KServe on EKS (Capital One's ML serving pattern)

## Primary sources

- Research report: [`08_compute_for_ml.md`](../../research_inputs/04_aws_for_ai_ml/08_compute_for_ml.md)
