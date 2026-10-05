# Module 53 — The Capital One MLOps Spine

> **What this is:** the synthesized view of Capital One's MLOps platform — SageMaker + Step Functions + Glue + EMR + EKS/KServe + rubicon-ml. The integrated picture across previous modules.

---

## 1. The full diagram

```
                ┌────────────────────────────────────────┐
                │ Raw data sources                       │
                │   - Card transactions (Kinesis)        │
                │   - Customer events (DDB Streams)      │
                │   - Operational systems (CDC via DMS)  │
                └─────────────────┬──────────────────────┘
                                  ↓
                ┌──────────────────────────────────────┐
                │ Databolt tokenization (upstream)     │
                │ — raw PAN/PII replaced with tokens   │
                └─────────────────┬────────────────────┘
                                  ↓
                ┌──────────────────────────────────────┐
                │ S3 raw zone                          │
                └─────────────────┬────────────────────┘
                                  ↓ (Glue / EMR / Databricks)
                ┌──────────────────────────────────────┐
                │ S3 curated zone (Iceberg)            │
                │ + Lake Formation FGAC                │
                │ + Unity Catalog (Databricks workloads)│
                └─────────────────┬────────────────────┘
                                  ↓
            ┌─────────────────────┴─────────────────────┐
            ↓                                           ↓
  ┌──────────────────────────┐         ┌─────────────────────────┐
  │ Feature Engineering      │         │ Snowflake (enterprise   │
  │   - Glue Spark           │         │  analytics + marketplace)│
  │   - EMR (Spark/Iceberg)  │         └─────────────────────────┘
  │   - Databricks (Photon)  │
  └────────────┬─────────────┘
               ↓
  ┌──────────────────────────────────┐
  │ SageMaker Feature Store          │
  │   - Online (DynamoDB / MemoryDB) │
  │   - Offline (S3 Iceberg)         │
  └────────────┬─────────────────────┘
               ↓
  ┌──────────────────────────────────────────────┐
  │ Training                                     │
  │   - SageMaker Training Jobs                  │
  │   - SageMaker HyperPod (FM scale, EKS-based) │
  │   - Databricks (distributed)                 │
  └────────────┬─────────────────────────────────┘
               ↓
  ┌──────────────────────────────────┐
  │ Experiment Tracking              │
  │   - rubicon-ml (git-SHA-linked)  │
  │   - MLflow on SageMaker          │
  └────────────┬─────────────────────┘
               ↓
  ┌──────────────────────────────────┐
  │ Model Registry (SageMaker)       │
  │   - Approval gate (SR 11-7)      │
  │   - Model Cards + Clarify        │
  └────────────┬─────────────────────┘
               ↓
       ┌───────┴───────┐
       ↓               ↓
  ┌────────────┐  ┌─────────────────┐
  │ SageMaker  │  │ EKS + KServe    │
  │ Endpoints  │  │ (self-hosted)   │
  └─────┬──────┘  └────────┬────────┘
        ↓                  ↓
  ┌─────────────────────────────────────────┐
  │ Production Inference                     │
  │   - Eno chatbot (Bedrock + Claude)       │
  │   - Servicing Tool (EKS + Triton + NeMo) │
  │   - Fraud scoring (Neptune ML + SM)      │
  └─────────────────────────────────────────┘

  Orchestration overlay:    EventBridge → Step Functions → above
  Observability overlay:    CloudWatch + Datadog + Prom/Grafana
  Governance overlay:       Lake Formation + UC + Model Cards + rubicon-ml
  Compliance overlay:       Cloud Custodian + GuardDuty + Macie + Security Hub
```

## 2. The named platform team — IFX

**Intelligent Foundations and Experiences (IFX)** is Capital One's internal ML platform team (per the Lead MLE job posting).

IFX likely owns:
- The MLOps platform (above).
- Internal SDKs (the serverless Kinesis SDK, model serving wrappers).
- Shared infrastructure (EKS clusters, SageMaker domains).
- Self-service model deployment paths.

## 3. The rubicon-ml choice

**rubicon-ml** ([github.com/capitalone/rubicon-ml](https://github.com/capitalone/rubicon-ml)) is Capital One's experiment-tracking tool.

The differentiator: **`auto_git_enabled=True`** binds every experiment to a specific git SHA. The lineage is automatic:

```python
from rubicon_ml import Rubicon

rubicon = Rubicon(persistence="filesystem", root_dir="./rubicon", auto_git_enabled=True)
project = rubicon.create_project("card-fraud-v3")
exp = project.log_experiment(name="run-12")
exp.log_metric("auc", 0.92)
exp.log_parameter("learning_rate", 0.001)
# Each experiment automatically tags the git SHA of the code that ran it
```

This is the **SR 11-7 audit answer**: *"Show me which exact code (down to the commit) trained this production model."*

## 4. Fraud-graph ML

Capital One's tech blog publishes work on:
- Graph ML for fraud detection.
- University partnerships on global graph transformers, dynamic customer embeddings.

The architecture pattern:
1. Stream transactions to Neptune (writer).
2. Periodic Neptune ML GNN training.
3. Score new transactions via SageMaker inference using GNN-derived features.

## 5. The hybrid serving decision (SageMaker vs KServe)

The single most distinctive thing about Capital One's MLOps:

| Choose **SageMaker endpoints** when | Choose **EKS + KServe** when |
|---|---|
| Low-volume model | High-volume + latency-critical |
| Standard framework (PyTorch / TF / XGBoost) | Custom runtime (Triton + custom kernels) |
| Want zero ops on serving | Existing EKS skillset and operations |
| Don't need fine-grained traffic routing | Need pod-level canary, blue/green |
| Acceptable to be on managed schedule | Need air-gapped, FedRAMP-style isolation |

## 6. Talking points for interviews

Three crisp framings:

- *"Capital One's MLOps spine is SageMaker + Step Functions + Glue + EMR + EKS/KServe with rubicon-ml binding every experiment to a git SHA — the SR 11-7 audit answer is built into the platform."*

- *"The hybrid SageMaker-endpoint and KServe-on-EKS serving decision is what makes Capital One distinctive. SageMaker for managed simplicity, KServe for latency, custom runtime, and Kubernetes-native operations."*

- *"Databolt sits upstream of S3 — raw PAN never lands in the lake, so PCI-DSS scope is bounded to the tokenization tier. This shapes every data pipeline downstream."*

## 7. Cross-references

This module synthesizes:
- **Modules 35, 38** — SageMaker MLOps
- **Module 33, 54** — EKS + KServe
- **Module 40** — HyperPod for FM training
- **Module 52** — SR 11-7 + Databolt
- **Module 25** — Neptune + fraud graphs
- **Module 51** — Cloud Custodian governance
- **CAPITAL_ONE.md** — the dossier

## 8. Sanity check

1. What does IFX stand for?
2. What does rubicon-ml's `auto_git_enabled=True` enable, audit-wise?
3. Walk through the SageMaker vs KServe decision.
4. Where does Databolt sit in the data flow, and what does it bound?
5. How does fraud-graph ML use Neptune + SageMaker together?

## Primary sources

- [`rubicon_ml_readme.md`](../../research_inputs/04_aws_for_ai_ml/downloads/oss_tooling/rubicon_ml_readme.md)
- [`c1tech_ai.html`](../../research_inputs/04_aws_for_ai_ml/downloads/capital_one/c1tech_ai.html)
- [`c1tech_reinvent_2024.html`](../../research_inputs/04_aws_for_ai_ml/downloads/capital_one/c1tech_reinvent_2024.html)
- [`CAPITAL_ONE.md`](CAPITAL_ONE.md)
- Research report: [`13_mlops_c1_patterns.md`](../../research_inputs/04_aws_for_ai_ml/13_mlops_c1_patterns.md)
