# Module 37 — SageMaker Inference

> **What this is:** the inference endpoint variants — Real-time, Serverless, Async, Batch Transform, Multi-Model Endpoints (MME), Multi-Container, Inference Components, Inference Recommender, Shadow testing.

---

## 1. The four inference modes

| Mode | Latency | Cost model | Use |
|---|---|---|---|
| **Real-time endpoint** | ms | Per instance-hour 24/7 | Production low-latency |
| **Serverless inference** | ms-s (cold start) | Per request + per duration | Bursty, low-volume |
| **Async endpoint** | seconds-minutes | Per instance-hour while processing | Large input/output, long-running |
| **Batch Transform** | minutes-hours | Per instance-hour for batch | Offline scoring of large datasets |

## 2. Real-time endpoints

Standard pattern:

```python
predictor = model.deploy(
    instance_type="ml.g5.xlarge",
    initial_instance_count=2,
    endpoint_name="card-fraud-model"
)
```

- Multi-AZ behind a load balancer.
- Auto-scaling on `InvocationsPerInstance` or custom CloudWatch metrics.
- Configurable concurrency.

**Pricing trap**: even at 0 RPS, you pay per instance-hour. **The biggest SageMaker cost gotcha.**

## 3. Serverless inference

Pay per request:

```python
serverless_config = ServerlessInferenceConfig(memory_size_in_mb=2048, max_concurrency=20)
predictor = model.deploy(serverless_inference_config=serverless_config)
```

- Up to 6 GB memory.
- Cold-start latency on first request.
- Max concurrency configurable.

Use when: bursty workload, <1k requests/hr, latency budget allows cold start.

## 4. Async inference

For **long-running inputs/outputs** (e.g., document AI processing a 50-page PDF):

- Input from S3, output to S3.
- SNS notification on completion.
- Scales to 0 when no requests.
- Up to 1 GB input, 1 hour processing time.

## 5. Batch Transform

Offline scoring:

```python
transformer = model.transformer(
    instance_type="ml.m5.xlarge",
    instance_count=10,
    output_path="s3://.../predictions/"
)
transformer.transform(data="s3://.../inputs/", content_type="text/csv", split_type="Line")
```

Cheaper than spinning up a real-time endpoint just to score a static dataset.

## 6. Multi-Model Endpoints (MME)

Host **thousands of models on one endpoint**. Models load on-demand from S3 into instance memory.

- **CPU MMEs** — many small models per instance.
- **GPU MMEs** — fewer, larger models.

Use when: many models with similar runtime, modest QPS per model. **Memory pressure** is the failure mode — too many concurrent unique models triggers thrashing.

## 7. Multi-Container Endpoints

Different containers + routing logic on one endpoint. Each request routed to one container.

Useful for: A/B testing model versions, ensemble where each model is a different framework.

## 8. Inference Components (the 2024 cost story)

**Inference Components** (GA 2024) decouple model from endpoint compute:

- One endpoint hosts a pool of compute.
- Multiple "components" (models) packed onto the pool.
- Pack ratio: small models share a GPU.

The big cost win: **fractional GPU allocation per model**. Where MME was about hot-loading from S3, Inference Components is about static co-location with proper resource accounting.

## 9. Inference Recommender

Load-tests your model on multiple instance types and produces a Pareto cost/latency report. Use before going to production to pick the right instance.

## 10. Shadow testing

Mirror production traffic to a new model variant without affecting production. Compare metrics (latency, error rate, prediction distribution) before flipping traffic.

## 11. Auto-scaling

Configure on:
- **InvocationsPerInstance** (most common).
- **GPU/CPU utilization**.
- **Custom CloudWatch metric**.

**Cold-start under scale-up:** scaling-out adds new instances which need ~3-5 min to load model and warm up. Plan accordingly.

## 12. Latency tuning

- **Right-size instance** — Inference Recommender.
- **Model compression** — quantization (INT8, FP8), pruning.
- **Compile with TensorRT** for NVIDIA, or **AWS Neuron** for Inferentia.
- **Batch on the server** when SLA allows.
- **SageMaker LMI (Large Model Inference)** container for FM serving.

## 13. SageMaker LMI

**Large Model Inference** container — purpose-built for FM serving with:
- **DJL Serving** (Deep Java Library) under the hood.
- **vLLM**, **TensorRT-LLM**, **TGI** backends.
- **Tensor parallel inference** across multiple GPUs.

The AWS-native path for serving large open-source FMs without rolling your own KServe.

## 14. 2024-2026 changes

- **Inference Components** GA (the cost story).
- **DJL/LMI v12** with vLLM 0.6+, TensorRT-LLM updates.
- **Shadow testing matured**.
- **Serverless inference** memory raised to 6 GB.

## 15. Pitfalls

- **Idle real-time endpoint** — biggest SageMaker cost gotcha. Use serverless or scheduled shutdown.
- **MME memory pressure** — too many concurrent models.
- **Cold-start on serverless** for latency-critical workloads — use provisioned concurrency or real-time.
- **Auto-scale lag** on traffic spike — pre-warm or use Inference Components.

## 16. Capital One lens

Capital One **self-hosts on EKS + KServe** for many models (Module 54). But SageMaker endpoints likely still used for:
- Lower-volume models where SageMaker simplicity beats EKS overhead.
- **Inference Components** for cost-efficient packing of similar models.
- **Shadow testing** before promoting to KServe production.

## 17. Sanity check

1. Real-time vs Serverless vs Async vs Batch — when does each win?
2. What's the MME failure mode?
3. What does Inference Components solve that MME doesn't?
4. When would you reach for SageMaker LMI?
5. What's the idle-endpoint cost gotcha?

## 18. Cross-references

- **Module 54** — KServe (the self-hosted alternative)
- **Module 56** — cost discipline (the idle-endpoint trap)
- **Module 30** — instance type pricing
- **Module 38** — model registry → deploy pattern

## Primary sources

- SageMaker Inference Best Practices (archived)
- Research report: [`09_sagemaker.md`](../../research_inputs/04_aws_for_ai_ml/09_sagemaker.md)
