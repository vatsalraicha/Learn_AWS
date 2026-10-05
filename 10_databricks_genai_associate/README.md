# Topic 10 — Databricks Certified Generative AI Engineer Associate

> **Audience:** Senior AI/ML Engineer (10+ yrs Python/PySpark), already deep on RAG, vector databases, and reranking from [Topic 01](../01_rag_vector_db_reranking/). Comfortable on Databricks (Topic 02) and with MLflow basics (Topic 09 Databricks ML Associate).
>
> **Goal:** Pass the **Databricks Certified Generative AI Engineer Associate** (March 18, 2026 version) on the first attempt, and — more importantly — leave with the design vocabulary to lead GenAI architecture reviews at Optum / Capital One / any regulated employer.
>
> **Last verified:** 2026-05-23

---

## Why this cert (and why now)

The Generative AI Engineer Associate is **the only Databricks cert that tests the full agent lifecycle** — design, data prep, build, deploy, govern, evaluate, monitor — against Databricks-native primitives (Mosaic AI Vector Search, Agent Framework, Agent Bricks, AI Gateway, MLflow 3 GenAI). Every other Databricks ML cert is either narrower (ML Associate ≈ classic ML) or unreleased (no Pro tier exists for GenAI as of May 2026).

The **March 18, 2026 refresh** materially upgraded the exam — 11 new objectives covering Agent Bricks, MCP servers, MLflow Prompt Registry, CI/CD for agents, storage-optimized Vector Search, Databricks Apps as UIs, AI Gateway, and `mlflow.genai.evaluate()` custom Scorers. **ExamTopics dumps from 2024 are partially obsolete.** This curriculum is built against the verbatim Mar 2026 objectives.

---

## Exam logistics (one-glance)

| Item | Value |
|------|-------|
| Official name | Databricks Certified Generative AI Engineer Associate |
| Current version | **March 18, 2026** |
| Scored questions | **45** (+ unscored statistical items) |
| Question format | Multiple-choice **and multiple-select** (some "select TWO" / "select THREE") |
| Time limit | **90 minutes** |
| Fee | **$200 USD** (+ local tax) |
| Delivery | Online Proctored (Kryterion / WebAssessor) |
| Prerequisite | None; 6+ months hands-on recommended |
| Validity | **2 years** — full retake required to recertify |
| Passing score | ~70% (~32 of 45). Not officially published; community consensus. |
| Languages | EN, JA, PT-BR, KO |
| Registration | [webassessor.com/databricks](https://webassessor.com/databricks) |

> ⚠️ **Action:** Re-check the exam guide URL **two weeks before** sitting — Databricks updates the guide quietly whenever the exam changes.

---

## Domain weights (Mar 2026)

| # | Section | Weight | # Objectives | Curriculum modules |
|---|---------|--------|--------------|--------------------|
| 1 | Design Applications | **14%** | 6 | [01](01_genai_use_case_design.md), [02](02_model_selection.md) |
| 2 | Data Preparation | **14%** | 8 | [03](03_chunking_strategies.md), [04](04_embeddings_indexing.md) |
| 3 | **Application Development** | **30%** | 13 | [05](05_prompt_engineering.md), [06](06_mosaic_ai_vector_search.md), [07](07_rag_chains.md), [08](08_agent_framework.md), [09](09_agent_bricks.md) |
| 4 | **Assembling and Deploying** | **22%** | 15 | [10](10_model_serving_endpoints.md), [11](11_ci_cd_for_agents.md), [12](12_databricks_apps_as_ui.md) |
| 5 | Governance | **8%** | 4 | [13](13_governance_guardrails.md) |
| 6 | Evaluation & Monitoring | **12%** | 10 | [14](14_genai_evaluation.md), [15](15_production_monitoring.md) |
| | **TOTAL** | **100%** | **56** | **15 modules** |

> **Sections 3 + 4 = 52% of the exam.** Allocate study time accordingly. If you read this corpus end-to-end but skip the agent build, you will probably fail.

---

## What's new in the Mar 2026 refresh (read this carefully)

Eleven objectives were added or materially rewritten. They cluster in Sections 1, 4, and 6:

**Section 1 — Design**
- **Agent Bricks** (Obj 6): when to pick Knowledge Assistant vs Multi-Agent Supervisor vs Information Extraction.

**Section 3 — App Development**
- **Genie Spaces / conversational API** (Obj 13): multi-agent systems that talk to Genie for structured data retrieval.

**Section 4 — Assemble & Deploy (the most-changed section, 6 new objectives)**
- **Persistent agent memory / datastores** (Obj 11): Delta, Online Tables, Lakebase as memory layers.
- **CI/CD for agents** (Obj 12): Vector Search index updates, prompt promotion across environments, component testing.
- **MCP servers** (Obj 13): managed (Databricks-hosted), external (third-party), custom (your own).
- **Prompt Registry + aliases** (Obj 14): MLflow 3 Prompt Registry, version control, `@production` / `@staging` aliases.
- **Databricks Apps as UI** (Obj 15): Streamlit / Gradio / Dash hosting for agent UIs, OAuth + service principal pattern.
- **Storage-optimized Vector Search** (Obj 10): the standard vs storage-optimized configuration trade-off.

**Section 6 — Eval & Monitor**
- **AI Gateway** (Obj 8): Inference Tables, Usage Tables, rate limiting.
- **Custom Scorers in `mlflow.genai.evaluate()`** (Obj 9): going beyond built-in judges.

If you only have 4 hours to study, prioritize Section 4. If you have 10 hours, add Section 6. If you have 40 hours, do the modules in order.

---

## Learning path — 15 modules

### Domain 1: Design (14%)
| # | Module | Why it matters |
|---|--------|---------------|
| 1 | [GenAI use-case design](01_genai_use_case_design.md) | Prompt eng vs RAG vs fine-tune vs agent. Decomposing a business ask into pipeline I/O. |
| 2 | [Model selection](02_model_selection.md) | Foundation Model Catalog, FMAPI tiers (PPT vs PT), multimodal options, retirement lifecycle. |

### Domain 2: Data Preparation (14%)
| # | Module | Why it matters |
|---|--------|---------------|
| 3 | [Chunking strategies](03_chunking_strategies.md) | Fixed / recursive / semantic chunking; size + overlap math; metadata; Spark chunking. |
| 4 | [Embeddings & indexing](04_embeddings_indexing.md) | Embedding model selection; Vector Search index lifecycle; Delta Sync vs Direct Access; storage-optimized. |

### Domain 3: Application Development (30%) — the heavy block
| # | Module | Why it matters |
|---|--------|---------------|
| 5 | [Prompt engineering](05_prompt_engineering.md) | Few-shot, CoT, ReAct, structured output, Jinja templates, prompt as artifact. |
| 6 | [Mosaic AI Vector Search](06_mosaic_ai_vector_search.md) | Index lifecycle, hybrid (BM25 + ANN with RRF), filters, reranker param. |
| 7 | [RAG chains](07_rag_chains.md) | LangChain + Databricks, retriever→LLM, citations, multi-hop, evaluation hook-points. |
| 8 | [Agent Framework](08_agent_framework.md) | UC Functions as tools, ChatAgent / ResponsesAgent, MLflow tracing. |
| 9 | [Agent Bricks](09_agent_bricks.md) | NEW 2026 — three managed variants; decision rule vs Agent Framework. |

### Domain 4: Assembling & Deploying (22%) — the second-heaviest block
| # | Module | Why it matters |
|---|--------|---------------|
| 10 | [Model Serving endpoints](10_model_serving_endpoints.md) | Scale-to-zero, served entities vs served models, traffic config, environments. |
| 11 | [CI/CD for agents](11_ci_cd_for_agents.md) | DABs, pyfunc.log_model, UC registration, environment promotion, MCP server config. |
| 12 | [Databricks Apps as agent UIs](12_databricks_apps_as_ui.md) | App service principal + user OAuth pattern; Streamlit / Gradio. |

### Domain 5: Governance (8%)
| # | Module | Why it matters |
|---|--------|---------------|
| 13 | [Governance & guardrails](13_governance_guardrails.md) | UC for prompts/models/agents; AI Gateway PII + toxicity guardrails; Lakeguard; licensing. |

### Domain 6: Evaluation & Monitoring (12%)
| # | Module | Why it matters |
|---|--------|---------------|
| 14 | [GenAI evaluation](14_genai_evaluation.md) | `mlflow.genai.evaluate`, built-in judges, custom Scorers, golden datasets, Prompt Registry. |
| 15 | [Production monitoring](15_production_monitoring.md) | Inference Tables, Usage Tables, rate limiting, embedding drift, cost + latency SLO. |

---

## Companion files

- [`FACTS.md`](FACTS.md) — atomic, citable claims (numbers, model names, GA dates, retirement lifecycle). Every line dated.
- [`quizzes/`](quizzes/) — 135+ practice questions in six files mapped 1-to-1 to the domain weights (~19/19/41/30/11/16). Recall / Apply / Diagnose / Defend. All **original** (NDA-safe).

## Cross-references to other topics

- **RAG fundamentals, retrieval evaluation, reranking math:** [Topic 01](../01_rag_vector_db_reranking/) — assumed knowledge. This curriculum will not re-derive cosine vs dot product or explain why a cross-encoder beats BM25 alone.
- **MLflow 2 → 3 transition, Unity Catalog basics, FMAPI pricing on Azure:** [Topic 02](../02_azure_databricks/) — especially modules 12 (MLflow 3), 13 (Vector Search), 14 (FMAPI + Serving + AI Gateway), 15 (Agent Framework, Bricks, AI Functions).
- **MLflow tracking, model registry semantics, Unity Catalog three-level namespace:** [Topic 09](../09_databricks_ml_associate/).

---

## How to use this corpus

1. **Read the modules in order** — they map to exam domains 1→6 in left-to-right narrative.
2. After each module, **take its share of the quiz cold** (no peeking). Score yourself.
3. **Build the end-to-end agent referenced in modules 7→12** on Databricks Free Edition. Do it once. The hands-on rep is the difference between 65% and 80% on the exam.
4. **Re-read modules where you scored < 80%** on the quiz.
5. **One week before the exam:** Take the full 135-question quiz set under timed conditions (sub-quizzes weighted to exam %). Aim for ≥ 80%. If you hit that, you're ready.

> ⚠️ **NDA reminder:** Every question in [`quizzes/`](quizzes/) is **original**, derived from the verbatim public objectives plus the 10 official sample questions. Do not memorize ExamTopics / Skillcertpro / Whizlabs dumps — they are partially wrong (pre-March 2026 refresh) and violate Databricks's NDA.

---

## Style conventions

- **Mermaid diagrams** where the relationship between components matters (agent compositions, index lifecycles, deployment flows).
- **`> ⚠️ Exam trap:` callouts** flag wrong-answer patterns from the 10 official sample questions and from community failure modes.
- **Code blocks** show realistic Databricks SDK / `mlflow.genai` / SQL `ai_query` — not toy code. PySpark fluency is assumed.
- **No OpenAI** in code samples (per project convention) — Claude, Llama, DBRX, Mixtral preferred.
- **"Last verified" dates** on every external URL — the GenAI stack moves fast.

---

## What this topic guarantees

If you study **only** these 15 modules + the quizzes in `quizzes/`, you should be genuinely prepared for the March 18, 2026 exam. Specifically, each module:

1. **Covers every verbatim Mar 2026 objective** assigned to it (see `Coverage map` header in each module — maps objective → section anchor).
2. **Teaches the full API surface** the objective implies, with parameter tables for every consequential call:
   - `mlflow.pyfunc.log_model` (`python_model`, `code_paths`, `resources`, `pip_requirements` vs `extra_pip_requirements`, `input_example`, `registered_model_name`) — Module 08
   - `VectorSearchClient.create_endpoint` / `create_delta_sync_index` / `create_direct_access_index` / `get_index` / `list_indexes` / `sync` / `delete_index` — Module 04
   - `similarity_search()` with all params (`query_text`, `query_vector`, `columns`, `num_results`, `filters` dict syntax, `query_type`, `score_threshold`, `reranker`) — Module 06
   - `mlflow.genai.evaluate()` full signature + `Scorer` interface + `Feedback` return — Module 14
   - `serving_endpoints.create()` with `served_entities`, `workload_size`, `scale_to_zero_enabled`, `traffic_config`, `route_optimized`, `auto_capture_config` / Inference Tables — Module 10
   - `databricks bundle deploy` / `run` / `validate` and `targets` semantics — Module 11
   - AI Gateway `guardrails`, `rate_limits`, `inference_table_config` shapes — Modules 13, 15
3. **Calls out look-alike APIs** the exam uses as distractors:
   - Delta Sync vs Direct Access, managed vs self-managed embeddings, STANDARD vs STORAGE_OPTIMIZED — Module 04
   - `similarity_search()` vs `query()` vs SQL `vector_search()`; `query_type` ANN vs HYBRID vs FULL_TEXT; score interpretation per metric — Module 06
   - LangChain vs LlamaIndex; `DatabricksVectorSearch` retriever vs `DatabricksEmbeddings` vs `ChatDatabricks`; Chain vs Runnable vs LCEL — Module 07
   - `ChatAgent` vs `ResponsesAgent`; UC Function tools vs Python tools; `pip_requirements` vs `extra_pip_requirements` — Module 08
   - Knowledge Assistant vs Information Extraction vs Multi-Agent Supervisor — Module 09
   - `served_entities` vs `served_models` (legacy); FMAPI task types (`llm/v1/chat` vs `completions` vs `embeddings`) — Modules 02, 10
   - AI Gateway routes vs guardrails vs rate limits vs Inference Tables — Modules 13, 15
   - built-in judges (Relevance, Groundedness, Safety, ChunkRelevance, RetrievalRelevance, Correctness) vs custom Scorers; `mlflow.genai.evaluate()` vs `mlflow.evaluate()` (legacy) — Module 14
4. **Walks through worked exam questions** anchored on the 10 official sample questions, with reasoning chains and distractor traps named.
5. **Provides output-prediction drills** ("Given this code, what does it return / fail with?") in every module.
6. **States decision rules** in the form *"If you see X → answer involves Y because Z"* as `> 🎯 How to recognize on the exam:` callouts.
7. **Closes with an end-to-end mini-scenario** — a 30–80 line code block that exercises every API in the module against a realistic problem.

**Reader test (after studying):** Open any quiz file cold; aim for ≥ 80%. If you hit that on all six quizzes + the official 10 sample questions, you have ≈ 80% confidence of passing. Hands-on building of the Module 7→12 end-to-end agent on Databricks Free Edition pushes that toward ≈ 90%.

**Honest limitation:** This curriculum is a study aid, not a substitute for Databricks Free Edition hands-on. Mike Kahn (Medium) and other passers all emphasize that docs-only studying fails on the scenario-based questions. **Build one end-to-end agent.** Once.

---

## Quick-start path (compressed 2-week plan)

Already strong on RAG + MLflow + Databricks?

| Day | Focus |
|----|-------|
| 1 | README + FACTS + Module 01 + Module 02. Quiz 01 (Design). |
| 2 | Modules 03 + 04. Quiz 02 (Data Prep). |
| 3 | Modules 05 + 06. Half of Quiz 03. |
| 4 | Modules 07 + 08. Rest of Quiz 03. |
| 5 | Module 09 (Agent Bricks — NEW, heavily tested). Re-quiz 03 missed items. |
| 6 | Modules 10 + 11. Quiz 04 (Assemble & Deploy). |
| 7 | Module 12. Re-quiz 04 missed items. |
| 8 | Module 13. Quiz 05 (Governance). |
| 9 | Module 14. Half of Quiz 06. |
| 10 | Module 15. Rest of Quiz 06. |
| 11 | Full 135-question simulation, timed. |
| 12 | Review weak spots — re-read modules where you scored < 80%. |
| 13 | Hands-on: build the Module 7→12 end-to-end agent on Free Edition. |
| 14 | Light review + sleep. Exam next day. |

Total: 50–65 focused hours.
