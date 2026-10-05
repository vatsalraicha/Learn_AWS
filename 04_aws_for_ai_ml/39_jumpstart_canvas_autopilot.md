# Module 39 — SageMaker JumpStart, Canvas, Autopilot

> **What this is:** the pre-trained / no-code / AutoML surfaces in SageMaker — JumpStart's FM hub, Canvas's visual AutoML, and Autopilot's programmatic AutoML.

---

## 1. JumpStart

**Foundation model hub**:
- **LLMs**: Llama 3, Mistral, Falcon, Mixtral, Code Llama.
- **Image models**: Stable Diffusion XL, FLUX.
- **Embedding models**: Cohere, BGE, Sentence-Transformers.
- **Domain-specific**: Hugging Face fine-tunes.

For each model: **deploy with one click** to a SageMaker endpoint, or **fine-tune** with sample notebooks.

## 2. JumpStart vs Bedrock

| | JumpStart | Bedrock |
|---|---|---|
| Hosting | Your endpoint (SageMaker) | AWS-managed API |
| Customization | Full (fine-tune, modify) | Limited (Continued Pre-Training + FT via Bedrock Custom Models) |
| Cost model | Per-instance-hour | Per-token |
| Best for | Self-hosted + tunable | Quick start, multi-model, managed |

**Rule:** JumpStart when you want control over the deployment artifact and operations.

## 3. Canvas

**No-code ML** for business analysts:
- Tabular AutoML.
- Image classification / object detection (via JumpStart models).
- Text (sentiment, classification, summarization).
- Time-series forecasting.
- **Generative AI** (chat with Bedrock-hosted models, document Q&A).

Pricing: per-session-hour. Designed for non-engineers.

## 4. Autopilot (programmatic AutoML)

Programmatic API for tabular + time-series AutoML:

```python
from sagemaker.automl.automl import AutoML

automl = AutoML(
    role=role,
    target_attribute_name="fraud",
    sagemaker_session=session,
    max_candidates=50,
    max_runtime_per_training_job_in_seconds=3600,
)
automl.fit(inputs="s3://.../train/")
best_candidate = automl.best_candidate()
```

- Tries N (default 250) algorithms × hyperparams.
- Auto-feature-engineers.
- Outputs explainability via Clarify.
- Best candidate deployable to endpoint.

## 5. Decision matrix

| Need | Pick |
|---|---|
| Foundation model deploy / fine-tune | **JumpStart** |
| No-code tabular / time-series ML | **Canvas** |
| Programmatic tabular AutoML | **Autopilot** |
| Multi-FM API with managed serving | **Bedrock** |
| Custom training script | **Module 36 Training Jobs** |

## 6. Bedrock integration

Canvas can use Bedrock-hosted FMs for chat / document Q&A — the unified UX.

## 7. Pitfalls

- **JumpStart instance type** mismatch — many FMs require GPU; you'll get OOM on CPU defaults.
- **Canvas pricing surprise** — per-session-hour adds up for analysts.
- **Autopilot run time** — large datasets blow past default time limits.

## 8. Capital One lens

- **JumpStart** for self-hosting open-source FMs (Llama, Mistral) when Bedrock model selection doesn't fit.
- **Canvas** for business-analyst self-service (likely with Databolt-tokenized data).
- **Autopilot** for quick tabular baselines (fraud, credit, churn).

## 9. Sanity check

1. JumpStart vs Bedrock — when does each win?
2. What's Canvas, and who's the user?
3. Autopilot programmatic flow — what do you give it, what do you get back?
4. Why is Canvas pricing per-session-hour?
5. Can Canvas talk to Bedrock?

## 10. Cross-references

- **Module 34** — SageMaker platform (Canvas lives in Studio)
- **Module 42** — Bedrock (alternative to JumpStart for managed FM)
- **Module 44** — self-hosted FM (JumpStart is one path here)

## Primary sources

- SageMaker JumpStart docs (archived)
- Research report: [`09_sagemaker.md`](../../research_inputs/04_aws_for_ai_ml/09_sagemaker.md)
