# Module 42 — Amazon Bedrock

> **What this is:** Bedrock model catalog (Anthropic Claude, Amazon Nova, Llama, Mistral, Cohere), Knowledge Bases, Agents, Guardrails, Flows, Prompt Management, Distillation, custom models, Provisioned Throughput, Application Inference Profiles.

---

## 1. The model catalog

Bedrock is AWS's managed FM service. Models available (2026):

- **Anthropic Claude** — Claude 4.x family (Opus 4.7, Sonnet 4.6, Haiku 4.5). The largest portfolio.
- **Amazon Nova** (GA Dec 2024) — Nova Lite, Nova Pro, Nova Premier, Nova Micro. AWS-native FM family.
- **Meta Llama** — 3.x and 4.x.
- **Mistral** — Mistral, Mixtral, Mistral Large.
- **Cohere** — Command, Embed, Rerank.
- **AI21**, **Stability**, **DeepSeek** — additional.

**Model access requests** — Bedrock requires explicit per-region, per-account, per-model opt-in. Plan this in account vending.

## 2. Knowledge Bases (managed RAG)

Bedrock Knowledge Bases is a managed RAG implementation:

1. Ingest documents (S3, web crawler, Confluence, SharePoint, etc.).
2. Chunking + embedding (you pick model, e.g., Cohere Embed or Titan Embed).
3. Index into a **vector store** — Bedrock supports:
   - **OpenSearch Serverless** (default)
   - **Aurora pgvector**
   - **Pinecone**
   - **Redis Enterprise**
   - **MongoDB Atlas**
   - **Neptune Analytics** (2024)
4. Query: Bedrock retrieves, augments prompt, calls FM, returns response.

**Capital One use case** likely: regulatory document RAG with OpenSearch Serverless backend, paired with Guardrails.

## 3. Agents

Multi-step reasoning with action groups + knowledge bases.

- **Action groups** = OpenAPI specs that the agent can invoke (Lambda-backed).
- **Multi-agent collaboration** GA Dec 2024.
- **Inline agents** — define an agent in code, no console resource.
- **Return-of-control** — the agent yields control back to the application instead of calling a tool directly.

## 4. Guardrails

Six content filters:
1. **Content filters** — hate, insults, sexual, violence, misconduct, prompt injection.
2. **Denied topics** — define forbidden subjects.
3. **Word filters** — block specific words/phrases.
4. **Sensitive information filters** — PII detection (block or redact). GA includes CC numbers, SSN, etc.
5. **Contextual Grounding Check** — verify response is grounded in retrieved context.
6. **Automated Reasoning** (2024) — formal verification of claims.

**Capital One: NeMo Guardrails appears in their job postings**. They likely use Bedrock Guardrails as the first line for Bedrock-hosted models and NeMo Guardrails for self-hosted.

## 5. Flows

Visual workflow builder for chaining Bedrock prompts, FMs, code (Lambda), and Knowledge Bases. The "low-code agent" surface.

## 6. Prompt Management

Versioned prompt registry — store prompts as managed resources, deploy versions, A/B test.

## 7. Model Distillation (GA Dec 2024)

Train a smaller, cheaper model from outputs of a larger one. Use:
- Teacher: Claude Opus.
- Student: smaller Claude Haiku or Llama.
- Result: 60-80% cost reduction with 85-95% quality retention.

## 8. Custom Models

- **Continued Pre-Training (CPT)** — feed domain corpus to adapt base model.
- **Fine-Tuning (FT)** — labeled task data.
- Custom models served via Provisioned Throughput.

## 9. Provisioned Throughput

Committed capacity for production:
- **Per-MU (Model Unit) pricing** — predictable.
- Required for custom models, optional for base models.
- Commit 1 month or 6 months for discounts.
- **Break-even vs on-demand**: ~8-12M output tokens / MU / month.

## 10. Application Inference Profiles (2024)

Tag-based cost allocation for Bedrock usage:
- Profile = tags + cross-region routing rules.
- **Per-tag cost reports**.
- **Cross-region inference** — automatically route to a region with capacity.

Capital One uses this for **per-app chargeback** (per the re:Invent 2024 "Control the cost of your generative AI services" talk).

## 11. Bedrock Data Automation (2024)

Newer service for **automated document/image/video understanding**: extract structured data from invoices, IDs, contracts. The "Textract on steroids" pitched for GenAI workflows.

## 12. 2024-2026 changes

- **Amazon Nova** GA Dec 2024.
- **Model Distillation** GA Dec 2024.
- **Agents multi-agent collaboration** GA Dec 2024.
- **Guardrails Automated Reasoning + Contextual Grounding** new.
- **Application Inference Profiles** GA.
- **Cross-region inference** GA Aug 2024.
- **Bedrock Data Automation** GA.

## 13. Pitfalls

- **Throttling** — Bedrock has per-region, per-model rate limits. Use Provisioned Throughput at scale or distribute via cross-region profiles.
- **Guardrails false positives** — content filters can over-block; tune thresholds.
- **Knowledge Bases ingestion drift** — re-ingest as source docs change.
- **Forgetting model access requests** in new accounts/regions.

## 14. Pricing examples (May 2026, us-east-1)

- **Claude Haiku 4.5**: $0.25 / 1M input tokens, $1.25 / 1M output
- **Claude Sonnet 4.6**: $3 / 1M input, $15 / 1M output
- **Claude Opus 4.7**: $15 / 1M input, $75 / 1M output
- **Nova Lite**: $0.06 / 1M input, $0.24 / 1M output
- **Provisioned Throughput**: per-MU pricing; commit-based.

## 15. Capital One lens

Brent Segner's re:Invent 2024 talk *"Control the cost of your generative AI services"* signals:
- **Application Inference Profiles for chargeback.**
- **Pre-deployment cost gate** (estimate token cost before launching a new agent).
- **Dedicated FinOps-for-AI team.**
- **Guardrails first-class** in compliance posture.

Likely workloads:
- **Eno** uses Bedrock with Anthropic Claude (LLM upgrade announcement 2024).
- **Servicing Tool** uses both Bedrock and self-hosted (NVIDIA GTC 2025 EXS74442).
- **Knowledge Bases** for compliance/regulatory document retrieval.

## 16. Sanity check

1. What are Bedrock's six guardrail filters?
2. When does Provisioned Throughput pay off vs on-demand?
3. What does Model Distillation do, and what's the typical cost reduction?
4. What's the use case for Cross-Region Inference?
5. Walk through how Capital One likely uses Application Inference Profiles.

## 17. Cross-references

- **Module 27** — vector backends for Bedrock KB
- **Module 44** — self-hosted FM alternative to Bedrock
- **Module 52** — Databolt tokenization upstream of Bedrock prompts
- **Module 56** — Bedrock cost discipline

## Primary sources

- Bedrock User Guide (archived as HTML in downloads/aws_whitepapers/)
- Bedrock Pricing page (archived)
- [`c1tech_reinvent_2024.html`](../../research_inputs/04_aws_for_ai_ml/downloads/capital_one/c1tech_reinvent_2024.html) — Capital One re:Invent 2024 GenAI cost talk
- Research report: [`10_genai_on_aws.md`](../../research_inputs/04_aws_for_ai_ml/10_genai_on_aws.md)
