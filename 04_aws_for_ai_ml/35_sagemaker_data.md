# Module 35 — SageMaker Data

> **What this is:** Data Wrangler, Feature Store (online + offline), Processing Jobs, Ground Truth, Clarify (bias + explainability), Model Cards.

---

## 1. Data Wrangler

**Visual data prep tool** — 300+ built-in transformations: type conversions, joins, custom transforms (Pandas/Spark), text/datetime parsing, outlier detection.

- Recipes compile to **Processing Jobs** (PySpark/Pandas).
- Output to S3, Feature Store, or directly to Training Job.

## 2. Feature Store

The managed feature platform. **Two tiers:**

| | **Online Store** | **Offline Store** |
|---|---|---|
| Backing | DynamoDB | S3 + Iceberg (since 2023) |
| Latency | single-digit ms | seconds-minutes |
| Use case | Inference-time feature lookup | Training/batch scoring |

Features are organized into **Feature Groups** — like tables. Ingest via boto3 / SageMaker SDK; query via Athena (offline) or `get_record` (online).

**Capital One use case**: per-customer behavioral features ingested from Glue → Feature Store → SageMaker training (offline) + KServe inference (online via DynamoDB or MemoryDB tier).

## 3. Processing Jobs

Run preprocessing / postprocessing code on managed containers. Three backends:

- **Built-in containers** — Spark, Scikit-Learn, Hugging Face.
- **Custom containers** — BYOC for your toolchain.
- **Bring Your Own Algorithm** for legacy patterns.

Output to S3. Pricing: per-instance-hour.

## 4. Ground Truth & Ground Truth Plus

**Ground Truth** — managed data labeling.
- Workforce options: Mechanical Turk, vendor-managed, private (your own workforce).
- Active learning to reduce labeling cost.

**Ground Truth Plus** — fully-managed labeling service (AWS handles the workforce).

## 5. Clarify

Bias and explainability:

- **Bias detection** — pre-training (data) and post-training (model). Statistical metrics like Class Imbalance, Difference in Positive Proportions in Labels, Demographic Disparity, etc.
- **SHAP-based explainability** — global and per-prediction feature importance.

**Capital One relevance**: SR 11-7 model risk management requires documented bias and explainability evidence. Clarify outputs feed Model Cards.

## 6. Model Cards (the SR 11-7 anchor)

Standardized model documentation:

- Intended use, training data, evaluation metrics, ethical considerations, decisions.
- Versioned with the model in Model Registry.
- Exportable as PDF for regulator submissions.

The **regulator-facing artifact**. Model Cards + Clarify + rubicon-ml (Capital One's OSS) form the audit trail for SR 11-7 / Fed model risk reviews.

## 7. A2I (Augmented AI)

Human-in-the-loop workflows: route low-confidence predictions to humans for review. Integrates with Textract, Comprehend, or custom workflows.

## 8. 2024-2026 changes

- **Feature Store offline-store on Iceberg** (2023+).
- **Data Wrangler in Unified Studio**.
- **Clarify Foundation Model evaluation** (for LLMs).
- **Model Cards integrated with Bedrock** for foundation models.

## 9. Pitfalls

- **Feature Store online cost** — DynamoDB writes for high-throughput features can dominate.
- **Data Wrangler recipes that don't scale** — built-in transforms work on samples; full data may OOM.
- **Forgetting Clarify in regulated workflows** — no SR 11-7 evidence trail.

## 10. Capital One lens

- **Feature Store** likely paired with MemoryDB vector for sub-ms online inference.
- **Clarify + Model Cards + rubicon-ml** for SR 11-7 model governance.
- **Ground Truth Plus** for high-quality labeling (financial transactions, fraud signals).

## 11. Sanity check

1. Online vs offline Feature Store — what's the backing store and latency?
2. What's the SR 11-7 chain: Clarify + Model Cards + ?
3. Ground Truth vs Ground Truth Plus — what's the difference?
4. When would you use a Processing Job vs Glue?
5. What does Data Wrangler compile its recipes to?

## 12. Cross-references

- **Module 21** — MemoryDB (online feature serving)
- **Module 38** — Model Registry, MLflow
- **Module 52** — SR 11-7 in regulatory context
- **Module 53** — rubicon-ml in Capital One MLOps spine

## Primary sources

- SageMaker Feature Store docs (archived)
- Research report: [`09_sagemaker.md`](../../research_inputs/04_aws_for_ai_ml/09_sagemaker.md)
