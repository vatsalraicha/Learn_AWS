# 30 — Model serving on K8s: KServe, Seldon, BentoML, Triton, vLLM, Ray Serve

> *"KServe + KEDA + Karpenter on EKS is the Capital One stack. Master the `InferenceService` CRD and you've made yourself credible for the Lead role."*

## Why this module exists

Model serving on K8s is the area Capital One's Lead MLE job posting explicitly names. This module compares the leading frameworks, focuses on KServe (the C1 choice), and shows the `InferenceService` patterns for classical ML, transformer, and LLM serving.

---

## 1. The framework landscape

| Framework | License | What it adds over a plain Deployment |
|---|---|---|
| **KServe** | Apache 2.0 (CNCF Incubating) | `InferenceService` CRD; pre/post-processor + predictor + explainer chain; ModelMesh for many small models; autoscaling (Knative or RawDeployment); standard `/v1/models/X:predict` API |
| **Seldon Core v2** | Source-available (Seldon Inc.) | Multi-model serving, experiments (canary, A/B), Seldon Inference Graph |
| **BentoML + Yatai** | Apache 2.0 | Python-first framework; bundles deps + model into a "Bento"; Yatai for K8s deploy |
| **NVIDIA Triton** | Apache 2.0 | High-perf C++ inference server; backends for ONNX, TensorRT, PyTorch, TensorFlow, Python, FIL (forest); concurrent model exec |
| **vLLM** | Apache 2.0 | LLM-specialized; continuous batching, PagedAttention; the de facto for LLM inference 2024-2026 |
| **Text Generation Inference (TGI)** | Apache 2.0 | HuggingFace; similar to vLLM; quantization-friendly |
| **Ray Serve** | Apache 2.0 | Ray-based; flexible Python deployment graphs; HPC parallelism |

For Capital One context: **KServe + RawDeployment mode + a Triton or vLLM predictor underneath**. KServe is the orchestration layer; Triton/vLLM is the actual model runtime.

---

## 2. KServe — the `InferenceService` CRD

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata: { name: sentiment, namespace: ml-serving }
spec:
  predictor:
    serviceAccountName: sentiment-sa            # IRSA / Pod Identity / WIF role
    minReplicas: 1
    maxReplicas: 5
    containerConcurrency: 4
    timeout: 60
    pytorch:
      storageUri: s3://myorg-ml-models/sentiment/v1.4/
      resources:
        requests: { cpu: 1, memory: 4Gi, nvidia.com/gpu: 1 }
        limits:   { cpu: 2, memory: 8Gi, nvidia.com/gpu: 1 }
```

What's happening:
- KServe controller creates a Deployment (or Knative service in default mode), Service, and (if Knative) revision.
- The `pytorch` predictor pulls weights from `s3://...` via the SA (IRSA permissions).
- Endpoint: `http://sentiment.ml-serving.svc.cluster.local/v1/models/sentiment:predict` (the OpenAI-style API).

### 2.1 Deployment modes

- **Serverless** (Knative-backed, default before v0.11) — scale to zero, request-based autoscaling.
- **RawDeployment** — vanilla Deployment + HPA. No Knative dependency. **Capital One's likely mode** for predictable workloads.

```yaml
metadata:
  annotations:
    serving.kserve.io/deploymentMode: RawDeployment
```

### 2.2 ModelMesh — many small models on one pod

For RAG retrievers, embedding services, traditional ML with thousands of models: ModelMesh loads models on-demand into pre-warmed serving pods. One pod serves many models; LRU eviction.

### 2.3 The transformer + predictor chain

```yaml
spec:
  transformer:
    containers:
      - name: tokenize
        image: myorg/tokenizer:1.0
        env: [{ name: MODEL_NAME, value: sentiment }]
  predictor:
    triton:
      storageUri: s3://myorg-models/sentiment-onnx/
```

Request flows: client → KServe transformer → predictor → response. Useful for tokenization, image preprocessing, etc.

---

## 3. KServe + Triton

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata: { name: bert-base }
spec:
  predictor:
    triton:
      runtimeVersion: 24.06-py3
      storageUri: s3://myorg-models/bert-base/
      resources: { requests: { nvidia.com/gpu: 1 } }
```

Triton's model repository format (`models/<name>/<version>/model.plan` for TensorRT, etc.) defined in `s3://...`. KServe pulls and starts Triton.

For multi-model serving with hot model swapping: this is the canonical pattern.

---

## 4. KServe + vLLM for LLM serving

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata: { name: llama3-8b }
spec:
  predictor:
    containers:
      - name: vllm
        image: vllm/vllm-openai:v0.6.2
        args:
          - --model=meta-llama/Llama-3.1-8B-Instruct
          - --dtype=bfloat16
          - --max-num-seqs=64
          - --gpu-memory-utilization=0.92
          - --enable-prefix-caching
        env:
          - { name: HF_TOKEN, valueFrom: { secretKeyRef: { name: hf-token, key: token } } }
        resources:
          requests: { nvidia.com/gpu: 1, memory: 32Gi }
          limits:   { nvidia.com/gpu: 1, memory: 32Gi }
        ports: [{ containerPort: 8000 }]
```

vLLM exposes the OpenAI-compatible API at `/v1/chat/completions`. Drop-in for LangChain / OpenAI SDK clients. PagedAttention + continuous batching extracts ~2-5x throughput over naïve serving.

For LLM-scale serving (Llama 70B, Mixtral 8x7B): tensor-parallel across multiple GPUs:

```yaml
args:
  - --tensor-parallel-size=4
  - --pipeline-parallel-size=2
resources:
  limits: { nvidia.com/gpu: 4 }
```

The pod gets 4 GPUs; vLLM shards the model.

---

## 5. Autoscaling

### 5.1 HPA (CPU/memory + custom metrics)

Standard HPA works for serving:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata: { name: sentiment-hpa }
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: sentiment-predictor-default
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Pods
      pods:
        metric: { name: requests_per_second }
        target: { type: AverageValue, averageValue: "50" }
```

For ML serving, latency or queue depth metrics work better than CPU. Expose them via Prometheus + `prometheus-adapter`.

### 5.2 KEDA — event-driven autoscaling

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata: { name: vllm-scaler, namespace: ml-serving }
spec:
  scaleTargetRef: { name: llama3-8b-predictor-default }
  minReplicaCount: 1
  maxReplicaCount: 8
  triggers:
    - type: prometheus
      metadata:
        serverAddress: http://prometheus.monitoring.svc:9090
        metricName: vllm_pending_requests
        threshold: '10'
        query: sum(rate(vllm_pending_requests[1m])) by (model)
```

KEDA scales based on prom metrics. Works with any queue (Kafka, SQS, Redis lists, RabbitMQ).

### 5.3 Knative scale-to-zero

Default KServe mode. Pod scales to 0 when no requests; cold start on first request (~10s for small models, 30-90s for large).

For LLM serving: **NEVER use scale-to-zero** — cold start of a 70B model is minutes. Use `minReplicas: 1+`.

---

## 6. GPU sharing

Three patterns:

- **NVIDIA MIG** (A100, H100, H200, H200 NVL) — hardware partition. e.g., A100-80GB split into 7×10GB MIG slices. Each pod gets a slice as a "fractional GPU."
- **NVIDIA time-slicing** — software multiplexing; multiple pods share one GPU. No isolation; throughput share.
- **MPS** (Multi-Process Service) — multiple processes share GPU concurrently. CUDA-native.

For ML serving with small models: MIG is the right call. For training: full GPU per pod.

The **NVIDIA GPU Operator** installs and manages the device plugin, MIG, DCGM, GPU Feature Discovery, MIG-parted config.

---

## 7. Karpenter for GPU pools

Already covered in module 26. The GPU NodePool with `consolidateAfter: 5m` prevents thrash on expensive instances.

For multi-tier serving: separate NodePools for inference (low-latency, smaller GPUs like L4/L40S) vs training (multi-GPU nodes).

---

## 8. Capital One signal — putting it together

The job posting language: "Lead Machine Learning Engineer (MLOps, KServe — building Kubernetes Clusters, PyTorch, TensorFlow on AWS)". Decode:

- **KServe** — the orchestration layer.
- **Building Kubernetes Clusters** — the candidate is expected to operate the cluster, not just consume a managed one. Karpenter, VPC CNI, IRSA, etc.
- **PyTorch + TensorFlow** — frameworks, both. Triton supports both as backends; KServe predictor handles both.
- **on AWS** — EKS specifically.

What this implies for talking-points in an interview:

- "I'd use KServe RawDeployment mode with KEDA for autoscaling on Prometheus metrics — Knative-Serverless adds latency that hurts at p99."
- "For LLM serving I'd reach for vLLM with PagedAttention; for traditional models, Triton."
- "GPU pools managed by Karpenter with `consolidateAfter: 5m` to prevent expensive node thrash."
- "IRSA-rolled model S3 bucket; model artifacts versioned by `storageUri` with digest in the InferenceService."
- "Falco runtime rules for shell-spawn / IMDS / SA-token-theft signals."

This is the credibility multiplier vs candidates who only know SageMaker endpoints.

---

## 9. Observability for serving

Per-model metrics:

- **request_count, request_latency** (histograms).
- **gpu_utilization** (DCGM).
- **vllm_pending_requests, vllm_running_requests, vllm_tokens_generated_per_second** (LLM-specific).
- **model_load_seconds** (cold start).

Combined with OpenTelemetry traces for per-request latency breakdown.

---

## 10. Security hardening for serving

Inherits modules 22 + 23:

- PSA `restricted` namespace label.
- ServiceAccount with IRSA / Pod Identity → S3 read-only on the model bucket only.
- NetworkPolicy: ingress only from API gateway; egress to S3 + KMS + Secrets Manager + DCGM + logging.
- Cosign-verified image at admission (Kyverno).
- Read-only root FS + tmpfs for `/tmp` + `/dev/shm` of appropriate size.
- Resource requests = limits for GPU pods (Guaranteed QoS).

---

## Sanity check

1. Why does Capital One likely use KServe RawDeployment instead of Knative Serverless?
2. vLLM vs Triton — when does each fit?
3. NVIDIA MIG vs time-slicing — which gives isolation, which gives more density?
4. Why is scale-to-zero a bad idea for LLM serving?
5. KEDA scales based on what kinds of metrics, and what does it give over HPA-with-CPU?
6. Name three security controls a KServe `InferenceService` pod should have.

---

## Sources

- [KServe docs](https://kserve.github.io/website/)
- [KServe InferenceService API](https://kserve.github.io/website/latest/reference/api/)
- [NVIDIA Triton Inference Server](https://github.com/triton-inference-server/server)
- [vLLM](https://docs.vllm.ai/)
- [HuggingFace TGI](https://huggingface.co/docs/text-generation-inference/)
- [Ray Serve](https://docs.ray.io/en/latest/serve/index.html)
- [KEDA](https://keda.sh/)
- [NVIDIA GPU Operator](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/)
- [Karpenter](https://karpenter.sh/)

→ Next: [31 — Training on K8s — Training Operator, Volcano, GPU Operator, Karpenter](31_training_k8s.md)
