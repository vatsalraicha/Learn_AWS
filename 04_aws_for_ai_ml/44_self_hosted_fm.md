# Module 44 — Self-Hosted FM Training & Serving

> **What this is:** when to self-host on EC2/EKS vs use Bedrock. NVIDIA NIM, Triton Inference Server, EC2 Capacity Blocks, NVIDIA AI Enterprise, Nemo Guardrails. Capital One's self-hosted path.

---

## 1. When to self-host vs Bedrock

| Reason | Self-host | Bedrock |
|---|---|---|
| **Control over runtime / container** | ✓ | |
| **Custom CUDA kernels, vendored libs** | ✓ | |
| **FedRAMP / air-gapped / strict isolation** | ✓ | |
| **Very high token volume (>$1M/mo Bedrock)** | breakeven check | |
| **Latency below Bedrock SLA** | ✓ (in-VPC) | |
| **Operational simplicity** | | ✓ |
| **Model selection breadth (Claude, Llama, etc.)** | | ✓ |
| **No GPU procurement burden** | | ✓ |

**Capital One's split** (inferred from Eno + Servicing Tool architectures):
- **Bedrock for Eno** — natural-language interface with guardrails fitting compliance posture.
- **Self-hosted EKS + Triton + NeMo Guardrails for Servicing Tool** — performance-critical, NVIDIA-stack alignment (per GTC 2025).

## 2. NVIDIA NIM (Inference Microservices)

**NIM** = optimized container images for serving specific FMs (Llama, Mistral, custom). GA on AWS Marketplace 2024.

- Wraps **TensorRT-LLM**, **vLLM**, **Triton** — picks the best for the model.
- Standardized REST API.
- Auto-tunes batch size, KV cache for the GPU.

## 3. NVIDIA Triton Inference Server

Generic inference server supporting multiple frameworks (PyTorch, TensorFlow, ONNX, TensorRT, OpenVINO, Python).

- **Dynamic batching** for throughput.
- **Model ensembles** (chain models).
- **Concurrent model execution** on GPU.

Triton on EC2 GPU + behind ALB is a common self-hosted pattern.

## 4. EC2 Capacity Blocks for ML

(See Module 30 for the EC2 side.)

For self-hosted training:
- **Reserve P5/P5e windows for planned FM training**.
- 1-182 day windows.
- Pay for the window regardless of use.

## 5. NVIDIA AI Enterprise on AWS

Enterprise-supported NVIDIA software stack (GPU drivers, NeMo, Triton, RAPIDS, etc.). Capital One specifically mentions this stack at re:Invent 2024 and NVIDIA GTC 2025.

## 6. Nemo Guardrails

**Open-source** LLM safety framework from NVIDIA. Defines guardrails as YAML/Colang programs:
- Topic restrictions.
- Conversation flow control.
- PII detection.
- Fact-checking against retrieved context.

**Appears in Capital One Sr Distinguished MLE job posting** as a preferred qualification. Their self-hosted ML path uses NeMo Guardrails as the equivalent of Bedrock Guardrails.

## 7. Self-hosted vector DBs (preview)

For self-hosted RAG (covered in Module 27):
- **OpenSearch** (Service or Serverless).
- **Aurora pgvector** for tight integration with OLTP.
- **MemoryDB vector** for sub-ms agent context.

## 8. SageMaker HyperPod (the AWS-managed alternative)

If self-hosting feels like too much ops burden but you need foundation-model-scale training, **SageMaker HyperPod** (Module 40) is the middle ground — AWS-managed Slurm or EKS clusters for FM training.

## 9. EKS + KServe pattern (the Capital One way)

(Full treatment in Module 54.)

The serving stack:
- **EKS** with Karpenter for GPU node provisioning.
- **KServe InferenceService** CRDs to define models.
- **Triton or NIM** as the runtime per model.
- **Istio** for traffic management (canary, blue/green).
- **NeMo Guardrails** as the safety layer.
- **CloudWatch + Prometheus/Grafana** observability.

## 10. Cost math: self-hosted vs Bedrock

**Rough rule of thumb**:
- For < 1M tokens/day, Bedrock wins (no infra to manage).
- For 1-10M tokens/day, comparable.
- For > 10M tokens/day, self-hosted breaks even, depending on model.
- For > 100M tokens/day at low latency, self-hosted typically wins.

**Capital One scale** likely puts them in the "self-host the latency-critical and high-volume workloads, Bedrock everything else" zone.

## 11. 2024-2026 changes

- **NIM GA on AWS Marketplace** 2024.
- **Triton matured**.
- **NVIDIA AI Enterprise on AWS** standard offering.
- **EC2 Capacity Blocks H100/H200 expansion**.

## 12. Pitfalls

- **Self-hosting "because we want control"** without doing the cost math.
- **GPU provisioning blind spots** — Capacity Blocks unused = wasted spend.
- **Model serving without proper batching** — order-of-magnitude waste.
- **Forgetting NeMo Guardrails** — self-hosted models without safety = compliance risk.

## 13. Capital One lens

- **Eno** likely on Bedrock with Claude (managed).
- **Servicing Tool** likely self-hosted EKS + Triton + NeMo (per GTC 2025).
- **Custom adapters / fine-tunes** for fraud-specific models on self-hosted P5/P5e via Capacity Blocks.

**Talking point:** *"I'd expect the self-host vs Bedrock split at Capital One to be based on three things: latency budget (sub-100ms favors self-host in VPC), token volume (>10M/day economics), and compliance fit (custom adapters/RLHF favor self-host)."*

## 14. Sanity check

1. What does NIM wrap, and what's the value?
2. When does self-hosting beat Bedrock economically?
3. What does NeMo Guardrails do, and why does it appear in Capital One job postings?
4. Walk through the EKS + KServe + Triton + NeMo stack.
5. What's SageMaker HyperPod's role in the self-host vs managed decision?

## 15. Cross-references

- **Module 30** — EC2 + Capacity Blocks (the hardware)
- **Module 33** — EKS foundations
- **Module 40** — SageMaker HyperPod (managed alternative)
- **Module 42** — Bedrock (the contrast)
- **Module 54** — KServe deep (the serving layer)

## Primary sources

- NIM on AWS Marketplace docs (archived)
- NeMo Guardrails GitHub (archived)
- Research report: [`10_genai_on_aws.md`](../../research_inputs/04_aws_for_ai_ml/10_genai_on_aws.md)
