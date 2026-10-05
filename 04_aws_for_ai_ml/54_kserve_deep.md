# Module 54 — EKS for ML Serving — KServe Deep

> **What this is:** KServe — the Kubernetes-native model serving project. CRDs (InferenceService, ServingRuntime), KServe ModelMesh, KEDA, Karpenter for GPU, Istio, IRSA/Pod Identity, NVIDIA GPU Operator. The differentiator that Capital One explicitly mentions in its Lead MLE job posting.

---

## 1. The KServe story

KServe (formerly KFServing, part of Kubeflow until it became independent) is the standard Kubernetes-native ML serving framework. Capital One's Lead MLE posting is titled **"Lead Machine Learning Engineer (MLOps, KServe — building Kubernetes Clusters, PyTorch, TensorFlow on AWS)"** — explicit signal.

## 2. InferenceService CRD

The core abstraction:

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: card-fraud
  namespace: ml-prod
spec:
  predictor:
    serviceAccountName: kserve-sa  # IRSA / Pod Identity
    minReplicas: 2
    maxReplicas: 50
    model:
      modelFormat:
        name: pytorch
      storageUri: s3://co-card-prd-models/fraud/v3/
      resources:
        requests:
          nvidia.com/gpu: 1
          memory: 16Gi
        limits:
          nvidia.com/gpu: 1
          memory: 16Gi
  transformer:
    containers:
      - image: 123.dkr.ecr.us-east-1.amazonaws.com/transformer:v1
  explainer:
    alibi:
      type: AnchorTabular
      storageUri: s3://co-card-prd-models/fraud/v3/explainer
```

Components:
- **Predictor** — the model server.
- **Transformer** — optional pre/post-processing.
- **Explainer** — optional explainability sidecar (Alibi / SHAP).

## 3. Runtimes

KServe ships ServingRuntime definitions for:
- **TensorFlow Serving**
- **TorchServe**
- **Triton Inference Server** (NVIDIA)
- **ONNX Runtime**
- **MLServer**
- **vLLM** (LLM serving)
- **Custom** — your own Docker image

## 4. ModelMesh — multi-model serving

For shops with many small models, **ModelMesh** packs multiple models into shared inference pods:
- Models load on-demand from S3.
- LRU eviction when memory full.
- Routing transparent to clients.

Analogous to SageMaker MME but Kubernetes-native.

## 5. Deployment modes

- **Knative Serving** (the original) — serverless, scale-to-zero.
- **Raw Deployment** (GA, increasingly preferred at scale) — vanilla K8s Deployment + HPA + Service, avoiding Knative's revision proliferation.

**Capital One scale likely uses Raw Deployment** — Knative's revision history grows fast and adds operational complexity.

## 6. KEDA — event-driven autoscaling

Standard HPA scales on CPU/memory. **KEDA** scales on **external signals**:
- SQS queue depth.
- Kafka consumer lag.
- Custom CloudWatch metrics.
- Prometheus metrics.

For ML serving: scale on **incoming request rate from the messaging layer**, not just CPU.

## 7. Karpenter for GPU

(Module 33 introduces Karpenter.) For ML serving:

```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: gpu-inference
spec:
  template:
    spec:
      requirements:
        - key: "node.kubernetes.io/instance-type"
          operator: In
          values: ["g5.xlarge", "g5.2xlarge", "g6e.xlarge", "g6e.2xlarge"]
        - key: "karpenter.sh/capacity-type"
          operator: In
          values: ["spot", "on-demand"]
      nodeClassRef:
        name: default
```

When a KServe pod is `Pending` due to no GPU node, Karpenter provisions one in 30 seconds. Idle GPU nodes terminate via consolidation.

## 8. Istio service mesh

For traffic management:
- **VirtualService** — request routing rules.
- **DestinationRule** — load balancing policy, circuit breaker.
- **Canary deployments**: shift 5% of traffic to v2, monitor metrics, shift more.
- **Blue/green**: maintain v1 + v2 pods simultaneously, flip traffic atomically.

KServe integrates with Istio for these patterns.

## 9. Gateway API (newer)

The Kubernetes Gateway API (more powerful than Ingress) is replacing some Istio patterns in 2025-26. Worth tracking.

## 10. IRSA / Pod Identity

(Module 33.) The KServe pod's ServiceAccount → IAM role → access to S3 model bucket, KMS decrypt, CloudWatch metrics, etc. **No static AWS keys** in the pod.

## 11. NVIDIA GPU Operator

Manages on GPU nodes:
- **NVIDIA drivers**.
- **CUDA toolkit**.
- **Device plugin** (advertises `nvidia.com/gpu` to scheduler).
- **MIG (Multi-Instance GPU)** — partition an A100/H100 into smaller logical GPUs.

EKS Auto Mode handles this automatically; otherwise you install it via Helm.

## 12. Observability

KServe + Istio + Prometheus + Grafana:
- Per-model latency, throughput, error rate.
- GPU utilization, memory, KV cache.
- Request/response distributions.

## 13. Why Capital One picks KServe over SageMaker endpoints

Inferred reasons:
- **Custom runtime control** — vendored Triton with specific TensorRT-LLM versions.
- **Tight integration with their EKS investment** — same skillset and operations as the rest of their services.
- **Multi-region portability** — easier to run identical KServe deployments across regions.
- **Cost at high scale** — per-pod GPU sharing via ModelMesh and Karpenter consolidation can beat SageMaker endpoint pricing at very high volume.
- **Pod-level traffic control** for canary / blue/green (Istio).
- **Air-gapped, FedRAMP-style isolation** when needed.

## 14. KServe + Triton + NeMo Guardrails (the C1 Servicing Tool stack)

A plausible architecture for Capital One's Generative AI Agent Servicing Tool (presented at NVIDIA GTC 2025):

```
External request → Istio Gateway →
  KServe InferenceService (transformer pod: input sanitization) →
  Predictor pod (Triton + LLM model) →
  NeMo Guardrails sidecar (safety filter) →
  Response transformer →
  Out
```

All running on EKS with Karpenter-provisioned GPU nodes.

## 15. 2024-2026 changes

- **Karpenter v1.x** stable (Module 33).
- **Istio Ambient Mode** GA — sidecar-less mesh.
- **Gateway API** replacing Ingress in many shops.
- **KServe Raw Deployment** mode dominant for scale.
- **EKS Pod Identity Agent** replacing IRSA for new clusters.

## 16. Pitfalls

- **KServe revision proliferation** (Knative mode) — clean up old revisions or use Raw Deployment.
- **OIDC trust-policy `sub` claim scoping** — too broad allows lateral movement across namespaces.
- **No PodDisruptionBudget** → cluster upgrades evict all model pods at once.
- **GPU operator misconfig** → pods stuck `Pending` with cryptic errors.
- **Karpenter without consolidation** → idle GPU nodes burn.

## 17. Sanity check

1. What's the InferenceService CRD anatomy (predictor, transformer, explainer)?
2. ModelMesh — what problem does it solve, and what's the SageMaker analog?
3. Knative vs Raw Deployment mode in KServe — when does each win?
4. What is KEDA, and why does it matter for ML serving?
5. Walk through the Karpenter + GPU node + KServe pod lifecycle.

## 18. Cross-references

- **Module 33** — EKS foundations (the underlying cluster)
- **Module 30** — EC2 GPU instances (the nodes)
- **Module 37** — SageMaker inference (the managed alternative)
- **Module 53** — Capital One MLOps spine (the integrated view)
- **Module 44** — self-hosted FM (the related concept)

## Primary sources

- [`kserve_main.html`](../../research_inputs/04_aws_for_ai_ml/downloads/oss_tooling/kserve_main.html)
- [`kserve_quickstart.html`](../../research_inputs/04_aws_for_ai_ml/downloads/oss_tooling/kserve_quickstart.html)
- [`karpenter_main.html`](../../research_inputs/04_aws_for_ai_ml/downloads/oss_tooling/karpenter_main.html)
- [`aws_ml_eks_best_practices.html`](../../research_inputs/04_aws_for_ai_ml/downloads/oss_tooling/aws_ml_eks_best_practices.html)
- Research report: [`13_mlops_c1_patterns.md`](../../research_inputs/04_aws_for_ai_ml/13_mlops_c1_patterns.md)
