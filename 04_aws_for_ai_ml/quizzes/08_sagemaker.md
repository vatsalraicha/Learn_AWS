# Quiz 08 — SageMaker Deep (Modules 34-41)

> Take cold. 8 SageMaker modules. The most heavily-tested part on MLA-C01.

---

## Recall

1. Studio Domain vs Space — what's the relationship?
2. Online vs Offline Feature Store — what backs each?
3. What are the four Model Monitor types?
4. What's the difference between Inference Components and Multi-Model Endpoints (MME)?
5. HyperPod has two flavors — name them.

## Apply

6. Design a SageMaker training pipeline for a fraud-detection model that must hit a $50k budget. Which SageMaker features lower cost?
7. Map SR 11-7 model risk management to specific SageMaker features (Module 52 hint).
8. Design an inference endpoint that scales to 0 at night. Which inference mode?
9. You have 10,000 small XGBoost models, one per customer segment. How do you host them?

## Diagnose

10. A SageMaker training job in VPC mode hangs at start. List the most likely causes.
11. A real-time endpoint has 99th-percentile latency 10× higher than 50th. What's likely going on, and what do you check?
12. Model Monitor reports drift but model performance looks fine in offline tests. What's the discrepancy explanation?

## Defend

13. Defend SageMaker endpoints over EKS+KServe for a specific workload type.
14. Defend EKS+KServe over SageMaker endpoints for Capital One's serving needs.
15. Defend using JumpStart over Bedrock for hosting Llama 3.

---

## Answers

1. **Domain = multi-user workspace** (VPC, KMS, IAM scope). **Space = single workspace** inside a Domain (private or shared). Each Space runs on a specific instance type.
2. **Online**: DynamoDB (ms latency). **Offline**: S3 + Iceberg (since 2023). Both backed by Feature Group definitions.
3. **Data Quality**, **Model Quality** (requires ground truth), **Bias Drift**, **Feature Attribution Drift** (Clarify-based).
4. **MME**: many models share an endpoint; load on-demand from S3 into instance memory (LRU). Pressure point: memory thrashing. **Inference Components** (2024): decouple model from endpoint compute; pack ratio = small models share a GPU; static co-location with proper resource accounting. Better cost model at scale.
5. **Slurm-based** (HPC standard) and **EKS-based** (Kubernetes, GA 2024 — aligns with Capital One's KServe choice).
6. **Spot training** (up to 90% off), **warm pools** (skip provisioning), **Trainium2** if model fits Neuron SDK, **SageMaker Savings Plans** for steady-state, **Heterogeneous Clusters** for CPU data loading + GPU training split, **MLflow** to avoid running duplicate experiments.
7. **Model Cards** → development docs. **Model Registry** → versioning + approval. **Clarify** → bias + SHAP explainability. **Lineage Tracking + rubicon-ml** → experiment provenance. **Model Monitor** → ongoing validation. **CloudTrail** → audit trail.
8. **Serverless inference** scales to 0 between requests. Trade-off: cold start on first invocation (300-1000ms). Or **schedule shutdown** of a provisioned endpoint via Lambda (for predictable off-hours).
9. **MME (Multi-Model Endpoint)** on a single CPU instance with 10k models in S3, loaded on-demand. Or **Inference Components** with packed allocation. **Per-customer-segment routing**: header-based, set by inference request handler.
10. (1) VPC endpoints missing (S3, ECR, STS, etc.). (2) SG outbound blocking. (3) KMS key policy not granting SageMaker. (4) Subnet too small for cluster. (5) Cross-AZ data transfer too slow without EFA. (6) Wrong IAM role permissions. (7) NACL ephemeral-port mistake.
11. **Cold start on auto-scale-out** — new instances loading model. Or **GIL contention** (if Python). Or **memory pressure causing GC pauses**. Check: CloudWatch `ModelLatency` per-instance, `InstanceCount` correlated with p99.
12. **Data drift without quality drift** — input distribution changed, but model is still right on the new distribution (rare). More likely: drift is detected but the model is being saved by **out-of-distribution graceful degradation**, or the offline test set doesn't reflect production.
13. **Low-volume models, standard frameworks, want zero ops.** SageMaker auto-managed scaling, multi-AZ, integrated monitoring. Small team without K8s expertise.
14. **High-volume + latency-critical + custom runtime + existing EKS investment.** Capital One's stack already runs Kubernetes; KServe gives pod-level traffic control (canary, blue/green); Karpenter + GPU consolidation can beat SageMaker endpoint pricing at very high scale; air-gapped FedRAMP-style isolation easier.
15. **JumpStart**: you control the deployment artifact, can fine-tune freely, host with custom config, choose instance type/MIG/etc. **Bedrock**: managed API, per-token pricing, no infra to manage. **Pick JumpStart** when you need control over the runtime, want to fine-tune iteratively, or have compliance reasons to keep the model in your account.
