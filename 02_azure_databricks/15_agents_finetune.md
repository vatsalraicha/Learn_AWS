# Module 15 — Agent Framework, Agent Bricks, AI Functions, Fine-tuning

> **Goal of this module:** know what each Mosaic AI surface is for — Agent Framework as governance layer, Agent Bricks as auto-tuned beta, AI Functions in SQL as the underrated batch-inference unlock, and fine-tuning's reality. Plus an honest hype-vs-substance scorecard for the 2026 catalog.

---

## Mosaic AI Agent Framework — pragmatic, not magical

The Agent Framework is **deliberately not** a competitor to LangGraph or AutoGen. It's the **deployment + governance layer beneath them.** You author your agent in LangChain, LangGraph, LlamaIndex, OpenAI Agents SDK, or vanilla Python; you log it as an MLflow PyFunc; you deploy it via Mosaic Serving; and the framework adds:

- **Unity Catalog tools** — register Python functions as UC objects → callable as agent tools with RBAC, lineage, and discovery. The UC Tool Catalog is a real differentiator vs ad-hoc tool registries.
- **Lakeguard execution** — tools run remotely on serverless generic compute under user identity, not service principal. Defends against prompt-injection-as-code-execution.
- **MCP server bridging** — the framework can expose UC functions as Model Context Protocol servers and consume external MCP servers.
- **MLflow tracing automatic** — every step in the agent shows in the trace UI.
- **AI Gateway in front** — same governance applies to agent endpoints.

### What you actually do

```python
import mlflow
from mlflow.types.llm import ChatMessage, ChatCompletionResponse
from databricks.sdk.service.serving import EndpointCoreConfigInput

# 1. Author the agent however you want — LangGraph below
from langgraph.graph import StateGraph
graph = StateGraph(MyState)
graph.add_node("retrieve", retrieve_node)
graph.add_node("generate", generate_node)
agent = graph.compile()

# 2. Wrap as MLflow PyFunc
class MyAgent(mlflow.pyfunc.PythonModel):
    def predict(self, context, model_input):
        return agent.invoke(model_input)

# 3. Log with MLflow
with mlflow.start_run():
    mlflow.pyfunc.log_model(
        artifact_path="agent",
        python_model=MyAgent(),
        registered_model_name="prod_phi_clinical.models.clinical_agent_v3",
    )

# 4. Deploy via Mosaic Serving
w = WorkspaceClient()
w.serving_endpoints.create(...)
```

The framework is a thin wrapper. **You keep your orchestration framework choice (LangGraph for stateful agents); the framework gives you governance + serving + observability.**

### Honest limitations

- **Hard to enforce strict structured outputs end-to-end** through the serving wrapper.
- **Multi-step workflows are *possible* but the framework doesn't add much over LangGraph itself.**
- **Extra endpoint hop adds 50-200ms latency** vs direct model call — bad for sub-second SLAs.
- **Cost** — serverless compute + serving endpoint + tool execution stacks up.

### Architect take

**Use Agent Framework when you need governed enterprise tools** (UC functions over PHI tables) and don't want to build your own MCP server. **Author the orchestration in LangGraph** (best state management) or stay vanilla. **Skip the framework for low-latency consumer-facing agents.**

---

## Agent Bricks — auto-optimized, Beta

Announced at Data + AI Summit June 11, 2025. **What it actually is:** a higher-level abstraction *on top of* Agent Framework. You describe the task in natural language, point at your enterprise data, and Databricks:

1. Auto-generates synthetic data resembling your data
2. Auto-generates an evaluation set + LLM judges
3. Searches the optimization space (model, prompts, retrieval params, judge calibration)
4. Returns an optimized agent with cost/quality Pareto curve

### Templates

- **Structured information extraction**
- **Knowledge assistant (RAG)**
- **Custom text transformation**
- **Multi-agent supervisor**

### Reference customer claim

AstraZeneca: **400,000 clinical trial documents, structured extraction in <60 minutes, no code.**

### Hype vs real

This is the most "demo-driven" of the new offerings. The 60-minute claim is a single optimized template path. Real-world enterprise extraction tasks typically need iteration on schema, edge cases, and judge calibration that no auto-optimizer fully solves.

**Treat Agent Bricks as the new "low-code RAG" — useful for proofs of concept and second-tier internal tools, not the right place to put the regulated patient-facing pipeline.** Beta status also means probably **not in BAA scope yet** — flag for the security team.

### Architect's verdict

For Optum, **Agent Bricks is appropriate for**:
- Internal-only PoCs to demonstrate value
- Non-PHI workloads (provider directories, public health data)
- Rapid iteration before standing up an Agent Framework production pipeline

**NOT appropriate (yet) for:**
- PHI-touching production agents (Beta + BAA scope unclear)
- Customer-facing or clinician-facing tools
- Anything that requires explainable, auditable per-step behavior

---

## AI Functions in SQL — the underrated batch-inference unlock

`ai_query`, `ai_classify`, `ai_extract`, `ai_summarize`, `ai_translate`, `ai_similarity`, `ai_mask`, `vector_search`. Run from Databricks SQL, notebooks, Lakeflow Spark Declarative Pipelines, or Workflows.

**Cost rolls up under MODEL_SERVING / BATCH_INFERENCE in `system.billing.usage`** — actually attributable per warehouse / per user.

### Why this matters for AI engineers (not BI analysts)

**Batch inference.** The 2025 serverless batch inference release means you can do:

```sql
SELECT 
  claim_id,
  ai_query(
    'databricks-llama-3-3-70b',
    concat('Summarize this claim line: ', claim_text)
  ) AS summary
FROM silver.claim_line_with_text
WHERE ingestion_date = current_date();
```

over a 100M-row Delta table, and the scheduler auto-scales the underlying serving fleet. Performance claim: **up to 3× faster than alternative approaches.** In practice the win is *not* writing your own UDF + concurrency + retry logic.

### Production patterns

- **Bulk PHI de-identification:** `ai_mask` over claims notes
- **Coding/extraction:** `ai_extract` with JSON schema for ICD-10 / CPT extraction from clinical text
- **Categorization at ETL time:** `ai_classify` for triage tier on inbound case notes
- **RAG corpus refresh:** `ai_query` to regenerate summaries on Delta CDC events

```sql
-- ai_extract with JSON schema for clinical coding
SELECT 
  note_id,
  ai_extract(
    'databricks-claude-haiku-4-5',
    note_text,
    'icd10_codes ARRAY<STRING>, cpt_codes ARRAY<STRING>, diagnoses ARRAY<STRING>'
  ) AS codes
FROM silver.clinical_notes
WHERE encounter_date >= '2025-01-01';
```

### Governance note

AI Functions inherit the AI Gateway's PII redaction and rate limits **only if the underlying endpoint has them configured.** Confirm at endpoint level; don't assume.

### Architect take

**This is the single biggest "I couldn't do this on Azure ML alone" feature.** For batch-scale enrichment of healthcare data, the alternative is a Spark UDF wrapping AOAI with hand-rolled concurrency, retry, and cost tracking — and you'll spend a sprint getting it stable.

**Default-on for any large-scale text enrichment workload.**

---

## Fine-tuning on Databricks

Mosaic AI Model Training supports:

- **Instruction Fine-Tuning (IFT)** — jsonl with `prompt`/`response` columns, supervised. The 90% case.
- **Continued Pretraining (CPT)** — raw text, language adaptation / domain shift. Useful for clinical-language corpora.
- **Chat completion fine-tuning** — multi-turn `messages` format.
- **LoRA / PEFT** — parameter-efficient tuning, cheap and fast.
- Full-parameter fine-tuning for smaller models.

**Supported model families:** Llama 3 / 3.1 / 3.3, Mistral, plus continued availability of MPT checkpoints. **DBRX retired April 2025** from FMAPI fine-tuning.

Output is a **Databricks-served model on a provisioned throughput endpoint.**

### Cost claim

Databricks markets "10× lower cost" than naive multi-node training, attributed to system-level optimizations (Composer, Streaming, FSDP+TP) inherited from MosaicML.

### Honest comparison

| | Databricks Mosaic | Bedrock fine-tuning | OpenAI fine-tuning | DIY GPU + PEFT |
|---|---|---|---|---|
| Models supported | Llama, Mistral | Claude, Llama, Titan | GPT-4o, GPT-4.1 | Anything OSS |
| Data stays in lakehouse | Yes | Cross-cloud | No | Yes |
| Serving auto-deploy | Yes (PT endpoint) | Yes | Yes | Build yourself |
| LoRA/QLoRA | Yes | Limited | Hidden | Full control |
| HIPAA path | Yes (with BAA) | Yes | No (most contracts) | Yes |
| Cost/quality control | Medium | Low | Lowest | Highest |

### Architect take

**For a regulated org doing IFT on Llama-class models, Databricks is the right answer because the data never leaves UC.**

**For aggressive PEFT experimentation with novel architectures** (Qwen, DeepSeek, custom MoE), drop to GPU clusters with HuggingFace + PEFT directly — the Mosaic training service is too constrained on model menu.

### Pre-training reality check

Databricks bought MosaicML for $1.3B in 2023 partly for the pretraining narrative. **Reality in 2026:** the overwhelming majority of customer training on Databricks is *fine-tuning*. **Enterprises are not pretraining 70B+ models from scratch in 2026. Economics killed it.**

The interesting pre-training-adjacent workload is **continued pretraining (CPT) of a Llama checkpoint on a domain corpus** (clinical notes, claims data, drug ontologies) — that *is* a real pattern, supported by Mosaic CPT, and worth knowing for an EM pitching a "differentiated clinical LLM" line item to an exec. **CPT yes; full pretraining no.**

---

## Reference architecture: enterprise RAG + agent on Databricks

```
Source docs (S3/ADLS/SharePoint/SQL)
   ↓
Lakeflow Connect → Delta (raw)
   ↓
Lakeflow Declarative Pipelines (silver, chunked + metadata)
   ↓
ai_query (BGE-large embeddings via FMAPI) → Delta (vectors)
   ↓
Mosaic Vector Search index (Delta Sync, hybrid BM25+ANN)
   ↓
Agent Framework retrieval node
   ↓
LangGraph orchestration (state, retries, branching)
   ↓
Mosaic Serving endpoint behind AI Gateway (PII redaction, rate limit)
   ↓
MLflow tracing on every step
   ↓
Databricks Apps / external client
```

**Every step lives in UC.** PHI never leaves the lakehouse. MLflow traces every request. Eval set in MLflow Prompt Registry.

### Multi-agent supervisor pattern

Databricks pushed this pattern hard in 2025–2026:

```
Supervisor agent (router/planner)
  ├── Retrieval agent (Vector Search)
  ├── Structured-extraction agent (Agent Bricks template or custom)
  ├── Computation agent (UC SQL functions)
  └── Action agent (UC tool functions, external MCP servers)
```

Each sub-agent is a separate Mosaic Serving endpoint. Supervisor in LangGraph. **Useful template; do not over-engineer if a single agent solves the use case.**

---

## Hype vs Substance scorecard (the 2026 picture)

| Offering | Hype level | Substance | Healthcare-architect verdict |
|---|---|---|---|
| MLflow 3 GenAI tracing/eval | High | High | **Adopt.** Best-in-class for the price (free OSS). |
| Mosaic Vector Search | Medium | High (if on Delta) | **Adopt** when data already on lakehouse; skip otherwise. |
| FMAPI pay-per-token (HIPAA) | Medium | High | **Major unlock** — primary path for non-Anthropic LLM access under BAA. |
| Mosaic Model Serving (custom) | Medium | High | Solid; competitive with AML for opinionated LLM serving. |
| AI Gateway | Medium | Medium-High | Real value for governance; thinner than dedicated gateways like Kong/LiteLLM Proxy on features but UC-integrated. |
| Mosaic Agent Framework | High | Medium | Use as deployment+governance layer, **not as orchestrator**. |
| Agent Bricks | **Very High** | Low-Medium | PoC tool. **Don't put regulated workloads on it yet.** |
| Mosaic Model Training (FT) | Medium | High | Best when data on UC; constrained model menu otherwise. |
| Mosaic Pretraining | High (legacy) | Low (for typical enterprise) | Almost no enterprise actually pre-trains. **CPT yes.** |
| AI Functions in SQL | Medium | **High** | Underrated. Real productivity unlock for batch enrichment. |
| Genie | Very High (keynote) | Medium | BI feature; not your daily tool. |
| Databricks Connect VS Code | Low | Medium | Improved but rough. Use `.py`-first discipline. |
| Vector Search billion-scale | High (2026 announcement) | Wait-and-see | New, watch real benchmarks before committing. |

---

## TL;DR for the AI Architect interview pitch

1. **The Databricks AI value proposition for a healthcare org is data gravity + governance** — PHI is in Delta + UC anyway, so RAG, batch enrichment, fine-tuning, and serving all happen without copying data to a third-party AI vendor.
2. **The strongest pieces of the platform** are MLflow 3 (GenAI obs/eval), AI Functions in SQL (batch inference), and HIPAA-scoped FMAPI.
3. **The weakest "marketed" pieces** are Agent Bricks (Beta, demo-driven), scale-to-zero serving (don't use in prod), and pretraining (almost no enterprise actually does it).
4. **The right reference architecture** for an enterprise RAG/agent system: Delta → Vector Search (hybrid) → Agent Framework wrapping LangGraph → Mosaic Serving → AI Gateway, all governed by UC, all traced by MLflow.
5. **Skip the "Databricks does everything" pitch.** Most mature healthcare AI architectures will run Databricks for data+ML+RAG, AOAI/Anthropic for premium frontier models, and AI Gateway as the policy layer between them. **Argue the pluralist architecture; it's the credible one.**

---

## Sanity check

1. Why is Agent Framework "not a LangGraph competitor"? What's it actually for?
2. Agent Bricks claim: 400K AstraZeneca trial docs in <60 min. What's the architect's calibration on this for a regulated production use case?
3. What does `ai_query` over a 100M-row Delta table give you that hand-rolled UDF + concurrency wouldn't?
4. Continued Pretraining (CPT) vs full pretraining — which is the real enterprise pattern in 2026, and why?
5. Walk through the canonical RAG-on-Databricks reference architecture from source docs to client.
6. The hype-vs-substance scorecard: what's the most overhyped offering, and what's the most underrated?

---

## Further reading

- [Build compound AI systems faster — Mosaic AI](https://www.databricks.com/blog/build-compound-ai-systems-faster-databricks-mosaic-ai)
- [Agent Framework + Agent Evaluation announcement](https://www.databricks.com/blog/announcing-mosaic-ai-agent-framework-and-agent-evaluation)
- [Multi-agent supervisor architecture](https://www.databricks.com/blog/multi-agent-supervisor-architecture-orchestrating-enterprise-ai-scale)
- [Agent Bricks press release](https://www.databricks.com/company/newsroom/press-releases/databricks-launches-agent-bricks-new-approach-building-ai-agents)
- [Agent Bricks — The New Stack](https://thenewstack.io/databricks-launches-agent-bricks-its-new-no-code-ai-agent-builder/)
- [AI Gateway as governance layer for agentic AI](https://www.databricks.com/blog/ai-gateway-governance-layer-agentic-ai)
- [AI Functions docs](https://docs.databricks.com/aws/en/large-language-models/ai-functions)
- [`ai_query` reference](https://learn.microsoft.com/en-us/azure/databricks/sql/language-manual/functions/ai_query)
- [Introducing serverless batch inference](https://www.databricks.com/blog/introducing-serverless-batch-inference)
- [Mosaic AI Model Training](https://www.databricks.com/product/machine-learning/mosaic-ai-training)
- [Foundation Model fine-tuning data preparation](https://learn.microsoft.com/en-us/azure/databricks/large-language-models/foundation-model-training/data-preparation)
- [LLM fine-tuning blog](https://www.databricks.com/blog/llm-fine-tuning)
