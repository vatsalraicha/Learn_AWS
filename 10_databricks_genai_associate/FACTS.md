# FACTS — Topic 10: Databricks Certified Generative AI Engineer Associate

> **Last verified:** 2026-05-23. Every claim cites the official Mar 18, 2026 exam guide or docs.databricks.com. Lines tagged `[COMMUNITY]` are consensus-only and not officially published.

---

## Exam logistics

| Fact | Value |
|------|-------|
| Official name | Databricks Certified Generative AI Engineer Associate |
| Current version | **March 18, 2026** |
| Scored questions | **45** |
| Unscored items | Statistical pretest items may appear; not flagged on the form; extra time factored in |
| Time limit | **90 minutes** |
| Question format | Multiple-choice **and** multiple-selection ("select TWO" / "select THREE") |
| Fee | **$200 USD** + local tax |
| Delivery | Online Proctored via Kryterion Webassessor |
| Prerequisite | None; 6+ months hands-on recommended |
| Validity | **2 years** — full retake required for recertification |
| Passing score | **~70%** (≈ 32 of 45). Not officially published; Databricks uses psychometric equating, so cut score may vary per form. [COMMUNITY] |
| Retake | Pay again and reschedule. Some community reports cite a ~14-day wait between attempts. [COMMUNITY] |
| Languages | English, Japanese, Brazilian Portuguese, Korean |
| Registration | webassessor.com/databricks |

---

## Domain weights (Mar 2026)

| § | Domain | % | # Objectives |
|---|--------|---|--------------|
| 1 | Design Applications | 14 | 6 |
| 2 | Data Preparation | 14 | 8 |
| 3 | Application Development | **30** | 13 |
| 4 | Assembling & Deploying | **22** | 15 |
| 5 | Governance | 8 | 4 |
| 6 | Evaluation & Monitoring | 12 | 10 |
| | **TOTAL** | 100 | **56** |

---

## What's new in Mar 2026 (vs 2024 launch)

11 new or materially-rewritten objectives:

1. **Agent Bricks** (Sec 1 Obj 6) — Knowledge Assistant, Multi-Agent Supervisor, Information Extraction.
2. **Genie Spaces / conversational API** (Sec 3 Obj 13) — multi-agent retrieval of structured data.
3. **Persistent agent memory** (Sec 4 Obj 11) — Delta, Online Tables, Lakebase.
4. **CI/CD for agents** (Sec 4 Obj 12) — Vector Search index updates, prompt promotion, component testing.
5. **MCP servers** (Sec 4 Obj 13) — managed / external / custom.
6. **Prompt Registry + aliases** (Sec 4 Obj 14) — MLflow 3, UC-governed, `@production` / `@staging`.
7. **Databricks Apps as UI** (Sec 4 Obj 15) — Streamlit / Gradio / Dash with service principal + user OAuth.
8. **Storage-optimized Vector Search** (Sec 4 Obj 10) — 1B+ vector scale, Triggered sync only.
9. **AI Gateway** (Sec 6 Obj 8) — Inference Tables, Usage Tables, rate limiting.
10. **Custom Scorers** (Sec 6 Obj 9) — `mlflow.genai.evaluate()` with user-defined metrics.
11. Total objectives grew from ~45 → **56**.

---

## Mosaic AI Vector Search — testable facts

| Fact | Value |
|------|-------|
| Indexing algorithm | **HNSW** (Hierarchical Navigable Small World) |
| Distance metric | L2 internally; cosine via normalized vectors; dot product available |
| Hybrid search fusion | **Reciprocal Rank Fusion (RRF)**, default `rrf_param=60` |
| Endpoint types | **Standard** (≤ 100M vectors) \| **Storage-optimized** (1B+ at dim 768) |
| Storage-optimized: indexing speed | **10–20× faster** than standard |
| Storage-optimized: sync modes | **Triggered only** (no Continuous) |
| Standard: sync modes | Delta Sync **Continuous** + Delta Sync **Triggered** + Direct Vector Access |
| Direct Vector Access | SDK push of vectors; no source Delta table required |
| BM25-only indexes | Supported on storage-optimized via Delta Sync **with no embedding column** |
| Reranker | Available as a query parameter (`reranker=`) on `similarity_search()` |
| Latency (standard) | 10–50 ms typical |
| Latency (storage-optimized) | ~250 ms typical |
| Cost ratio (storage-opt vs standard) | ~7× cheaper per vector at scale |
| Plateau QPS | ~30 QPS per VS unit beyond ~2M (standard) / ~64M (storage-opt) vectors |

### Decision table (Obj 4.10)

| Constraint | Choice |
|-----------|--------|
| < 100M vectors, frequent updates | Standard endpoint + Delta Sync **Continuous** |
| > 100M vectors, latency-tolerant | Storage-optimized endpoint + **Triggered** sync |
| Highest retrieval accuracy | Hybrid search **ON** + reranker **ON** |
| Lowest cost / dev only | Pay-per-token embeddings + smaller dim model (e.g., GTE Small dim 384) |
| 100M items, latency-critical, 80 QPS | Storage-optimized + hybrid + rerank (per official sample Q6) |

---

## Foundation Model APIs (FMAPI)

| Mode | When to use | Pricing | Compliance |
|------|-------------|---------|------------|
| **Pay-per-token (PPT)** | Prototyping, low/spiky traffic, AI Playground exploration | Per token; cheapest at low volume | Standard |
| **Provisioned Throughput (PT)** | Production workloads, performance guarantees, fine-tuned models | **Hourly per PT unit** (per-minute billing) | **HIPAA** + other compliance certs available |

- Both modes are governed by **Unity Catalog** and exposed via **Model Serving** endpoints.
- **AI Playground** is the no-code UI for PPT exploration.
- **GenAI Calculator** estimates PT units needed; input/output token mix matters.
- Per Databricks docs, some pay-per-token models retire Feb 15, 2026 and some PT models retire May 15, 2026 — the **retirement lifecycle exists**, even if specific model names are not exam-tested.
- Fine-tuned models deploy as **PT only**, not PPT.

---

## Foundation Models on Databricks (as of May 2026)

| Family | Available | Tier |
|--------|-----------|------|
| **Llama 4** (Maverick / Scout) | Yes | PPT + PT |
| **Llama 3.3** (70B Instruct) | Yes | PPT + PT (`databricks-llama-3-3-70b-instruct`) |
| **Anthropic Claude** (Sonnet / Opus / Haiku) | Yes (via partner) | PPT, region-limited |
| **GPT OSS** (gpt-oss-120b) | Yes | PPT |
| **DBRX Instruct** | Legacy, being deprecated | PPT |
| **Mixtral 8x7B Instruct** | Yes | PPT |
| **BGE Large EN v1.5** (embedding) | Yes | PPT |
| **GTE Large EN v1.5** (embedding) | Yes | PPT |

Exact catalog drifts month-to-month — always re-check `databricks-instruct` family list in AI Playground before exam day. Model **names** are unlikely to be tested; **selection criteria** definitely are.

---

## MLflow 3 GenAI features

| Feature | API surface | Section testing it |
|---------|-------------|--------------------|
| **Tracing** | `mlflow.start_span()`, `mlflow.langchain.autolog()`, `mlflow.openai.autolog()`, `@mlflow.trace` decorator | Sec 3, Sec 6 |
| **Scoring / Eval** | `mlflow.genai.evaluate(data=..., scorers=[...])` | Sec 6 |
| **Built-in Judges** | `mlflow.genai.judges` — `relevance`, `groundedness`, `safety`, `correctness`, `chunk_relevance`, `retrieval_relevance` | Sec 6 Obj 7 |
| **Custom Scorers** | `@mlflow.genai.scorer` decorator or subclass `mlflow.genai.scorers.Scorer` | Sec 6 Obj 9 |
| **Prompt Registry** | `mlflow.genai.register_prompt()`, `set_prompt_alias()`, `load_prompt(name@alias)` | Sec 4 Obj 14 |
| **Agent Framework** | `mlflow.pyfunc.ChatAgent`, `mlflow.pyfunc.ResponsesAgent` | Sec 3 Obj 11 |
| **Autotrace** | Automatic on `mlflow.<lib>.autolog()` for LangChain, LlamaIndex, OpenAI, Anthropic, DSPy, AutoGen, CrewAI, LangGraph, Pydantic-AI | Sec 3 |

### Built-in judges — ground-truth requirement

| Judge | Needs ground truth? |
|-------|--------------------|
| `relevance` (answer to question) | No |
| `groundedness` (answer supported by context) | No |
| `safety` | No |
| `chunk_relevance` | No |
| `retrieval_relevance` | No |
| `correctness` | **Yes** |
| `similarity` (semantic) | **Yes** |

> ⚠️ Sec 6 Obj 7 explicitly tests "evaluation judges that require ground truth." Memorize the column above.

---

## AI Functions in SQL

| Function | Purpose | Compute |
|----------|---------|---------|
| `ai_query(endpoint, prompt, ...)` | Generic — call any served model from SQL; full param control. **Used for batch inference at scale.** | DBSQL warehouse or notebook |
| `ai_classify(text, labels)` | Task-specific classifier | DBSQL |
| `ai_extract(text, schema)` | Pull structured fields | DBSQL |
| `ai_summarize(text)` | Summarization | DBSQL |
| `ai_translate(text, lang)` | Translation | DBSQL |
| `ai_parse_document(path)` | OCR + layout, captures tables/figures with spatial metadata | DBSQL or notebook |
| `ai_mask(text, entities)` | Mask PII / configured entities | DBSQL |
| `ai_similarity(a, b)` | Embedding similarity | DBSQL |
| `vector_search(index, query_text, ...)` | Query a Vector Search index from SQL | DBSQL |

All AI Functions respect **Unity Catalog permissions** and produce **audit logs** for compliance.

**Exam pattern:** "Score 10M rows in a Delta table once" → `ai_query()` (batch). "Real-time per-request" → Model Serving endpoint.

---

## Agent Bricks (NEW Mar 2026)

| Variant | Purpose | When to choose |
|---------|---------|----------------|
| **Knowledge Assistant** | Grounded Q&A over enterprise data (RAG-as-a-service) | Internal support assistant, FAQ bot; replaces custom RAG when you don't need fine control |
| **Information Extraction** | Pull structured fields from unstructured docs (PDFs, emails) | Replaces hand-rolled prompt-extract pipelines; produces typed output |
| **Multi-Agent Supervisor** | Orchestrate multiple agents + Genie Spaces + tools + MCP servers | Query may need both structured Genie SQL AND unstructured RAG |

**Decision rule for the exam:**
- "Minimize maintenance / auto-optimize / domain-specific quality without manual tuning" → **Agent Bricks**.
- "Fine control over chain / custom tools / specific LangChain / pyfunc with pre/post processing" → **Agent Framework**.

Agent Bricks uses auto-generated synthetic data + task benchmarks to auto-tune cost/quality Pareto.

---

## MCP servers (Model Context Protocol)

| Type | What | How to integrate |
|------|------|------------------|
| **Managed** | Databricks-hosted (UC tools, Vector Search, web browser, etc.) | Set type=`managed` + server identifier in agent's MCP config |
| **External** | Third-party MCP servers needing API key | Store API key in **Databricks Secrets**; reference in MCP config |
| **Custom** | Your own MCP server (Python) | Deploy on Databricks Apps or external host; register endpoint |

> ⚠️ Sample Q9 confirms: prefer **managed** when available; for external, **store keys in Databricks Secrets**, never inline.

---

## Mosaic AI Agent Framework

- Build the agent however you want (LangChain, LangGraph, vanilla Python, OpenAI Agents SDK, AutoGen, CrewAI, Pydantic-AI).
- Wrap as `mlflow.pyfunc.ChatAgent` (chat-style) or `mlflow.pyfunc.ResponsesAgent` (OpenAI Responses-API-style).
- Log via `mlflow.pyfunc.log_model(python_model=..., artifact_path="agent")` or `mlflow.langchain.log_model(...)`.
- Register to Unity Catalog: `mlflow.register_model(model_uri, "catalog.schema.agent_name")`.
- Deploy via Model Serving: `databricks.agents.deploy()` or `WorkspaceClient.serving_endpoints.create()`.
- Tools: register Python or SQL functions in Unity Catalog (`CREATE FUNCTION catalog.schema.fn ...`); attach to agent.
- Tracing: automatic via `mlflow.langchain.autolog()` (or equivalent per lib) — captures retriever calls, tool calls, LLM calls.
- Security: tool execution runs under **Lakeguard** on serverless generic compute.

---

## AI Gateway

| Feature | What |
|---------|------|
| **Inference Tables** | Every request/response logged to a Delta table for audit + offline eval |
| **Usage Tables** | Per-user / per-endpoint cost and token consumption |
| **Rate limiting** | Per-user or per-endpoint QPS / token caps |
| **PII detection** | Built-in guardrail (input + output) |
| **Toxicity guardrail** | Built-in; configurable threshold |
| **Topic moderation** | Block or warn on user-defined disallowed topics |
| **Routing / fallback** | Call multiple providers; route on failure or cost |

Sec 6 Obj 8 explicitly names **Inference Tables, Usage Tables, and rate limiting** as the AI Gateway features to know.

---

## Lakeguard — agent tool security boundary

When UC Python/SQL functions are used as agent tools, **Lakeguard** sandboxes them on **serverless generic compute** (Spark Connect serverless), applying:
- CPU time limits
- Memory caps
- Wall-clock timeouts
- No arbitrary local code execution
- User-identity-scoped credentials (not service principal)

> ⚠️ **Gotcha:** UC functions as agent tools require **serverless generic compute**, not serverless SQL warehouses. Wrong compute → `PERMISSION_DENIED: Cannot access Spark Connect`.

---

## Unity Catalog governance for GenAI

Single governance layer covers:

- **Models** — `catalog.schema.model_name` MLflow models.
- **Prompts** — Prompt Registry: versions + aliases.
- **Functions / Tools** — Python or SQL UDFs used as agent tools.
- **Vector Search indexes** — live in UC as table-like assets.
- **Data tables** — RAG source documents + chunked Delta tables.
- **Volumes** — PDFs, images, raw source files.

**Promotion across dev → staging → prod** uses:
- **Prompt aliases** for prompts (`@dev`, `@staging`, `@production`).
- **Model aliases / versions** for models.
- **Vector Search index aliases** for index swaps.

---

## Online Tables / Feature Serving

- **Online Table** = low-latency, key-indexed copy of a Delta table served from a Feature Serving endpoint.
- Latency: **< 50 ms** for agent lookups (user profile, recent transactions, member features).
- Created via `CREATE ONLINE TABLE ...` SQL or SDK.
- Use case: dynamic per-record state that agent needs at request time (sample Q2: customer needs delivery date per transaction → feature store keyed on `transaction_id`, **NOT** fine-tuning).

---

## Persistent agent memory layers (Sec 4 Obj 11)

| Layer | Use case | Latency |
|-------|----------|---------|
| **Delta tables in UC** | Durable conversation logs, append-only | seconds |
| **Online Tables** | Low-latency recent-state lookup, key-indexed | < 50 ms |
| **Lakebase** (Postgres-on-Databricks, GA 2025) | Relational agent state with transactions | < 10 ms |
| **Vector Search index** | Semantic memory (find similar past sessions) | 10–250 ms |

---

## Fine-tuning (Mosaic AI Model Training)

| Technique | Data format | Use case |
|-----------|-------------|----------|
| **Continued Pretraining (CPT)** | `.txt` files in UC Volume | Extend base model knowledge to new domain/language/recent docs |
| **Instruction Fine-Tuning (IFT)** | `.jsonl` with `prompt` + `response` columns | Teach task/style/format following |
| **LoRA** | Same as IFT/CPT | Parameter-efficient; smaller artifacts; preserves base model |

**Recommended order:** **CPT first** (inject domain knowledge) → **IFT second** (align to task). LoRA is the default efficiency wrapper.

Fine-tuned models deploy only as **Provisioned Throughput** endpoints.

> ⚠️ **Exam trap:** Do NOT pick fine-tuning when the requirement is "current per-record data." Dynamic data → feature store / RAG. Sample Q2.

---

## Databricks Apps as agent UIs (NEW Sec 4 Obj 15)

- Managed serverless app hosting: **FastAPI / Streamlit / Dash / Gradio / Node** inside the workspace.
- **Security pattern** (sample Q8 answer = A):
  - App backend calls Agent Serving endpoint with **app's service principal**, not user PAT.
  - User identity flows via OAuth → app context → per-user permission enforcement.
  - **Never** put PAT in browser JS, public endpoints, or API keys in frontend.

---

## Document extraction libraries (Sec 2 Obj 3)

| Format | Recommended Python lib |
|--------|------------------------|
| PDFs (text-based) | `pypdf`, `pdfplumber`, `unstructured` |
| **Scanned PDFs / images (.jpeg, .png)** | **`pytesseract`** (OCR) |
| HTML pages | `BeautifulSoup`, `lxml` |
| Web scraping at scale | `Scrapy` |
| .docx | `python-docx` |
| .pptx | `python-pptx` |
| Spreadsheets | `openpyxl`, `pandas` |
| Databricks-native PDF + tables | `ai_parse_document()` |

> ⚠️ Sample Q3: scanned images → **`pytesseract`**, NOT BeautifulSoup (HTML) / Scrapy (crawler) / pyquery.

---

## Embedding model selection (Sec 3 Obj 8, sample Q4)

When cost/latency dominate quality:
- Smaller context length (e.g., 512 tokens) for 512-token chunks — no waste.
- Smaller dim (e.g., 384) for cheaper storage + faster search.
- Sample Q4 answer = A: context length 512, 0.13 GB, dim 384.

When quality dominates:
- Larger context (1024–8192) for big chunks.
- Higher dim (768–1024) for richer semantics.
- E.g., BGE Large or GTE Large.

**Match embedding context length to your max chunk size.** Mismatch wastes parameters or truncates content.

---

## Chunking quick reference (Sec 2 Obj 1, sample Q1)

| Knob | Lever | Sample Q1 hint |
|------|-------|----------------|
| Chunk size ↑ | More context per chunk; fewer chunks; cheaper index; risk: dilution | "Increase" was correct |
| Overlap ↓ | Less duplication; fewer chunks; risk: boundary loss | "Decrease overlap" was correct |
| Recursive splitter | Respects natural boundaries (paragraph → sentence → word) | Default for prose |
| Semantic chunker | Embedding-based boundary detection | Higher quality, slower |
| Fixed-window | Simple, no boundaries | Last resort |
| Metadata | `source_doc`, `chunk_id`, `page_no`, `member_id`, `created_at` | Filtering + citation |

---

## Sample-question answer keys (official Mar 2026 sample Qs)

| Q | Answer | Lesson |
|---|--------|--------|
| 1 | A, B | Reduce # of chunks → ↑ chunk size and ↓ overlap |
| 2 | B | Per-record dynamic data → feature store keyed on transaction_id, NOT fine-tuning |
| 3 | C | Scanned images → pytesseract (OCR) |
| 4 | A | Cost/latency priority → smallest model (ctx 512, 0.13 GB, dim 384) |
| 5 | D | NLP task category for "TL;DR of a document" = Summarization |
| 6 | C | 100M items + latency-critical + 80 QPS → storage-optimized + hybrid + rerank |
| 7 | B | Gated promotion + version history + rollback → MLflow Prompt Registry + aliases |
| 8 | A | App + corporate identity + no long-lived tokens → app backend with auth context |
| 9 | D, E | Managed MCP for Databricks source + external MCP with Secrets for API key |
| 10 | B | SME disagreement → rubrics + calibration + `mlflow.genai.evaluate()` |

---

## Sources

### Primary (HIGH confidence — official, accessed 2026-05-23)
- Databricks Certified Generative AI Engineer Associate Exam Guide (March 18, 2026), local PDF.
- https://www.databricks.com/learn/certification/genai-engineer-associate
- https://docs.databricks.com/aws/en/mlflow3/genai
- https://docs.databricks.com/aws/en/vector-search/vector-search
- https://docs.databricks.com/aws/en/vector-search/vector-search-best-practices
- https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis
- https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_query
- https://docs.databricks.com/aws/en/large-language-models/ai-functions
- https://www.databricks.com/blog/unity-catalog-lakeguard-industry-first-and-only-data-governance-multi-user-apachetm-spark
- https://docs.databricks.com/aws/en/generative-ai/agent-framework/create-custom-tool
- https://www.databricks.com/product/artificial-intelligence/agent-bricks
- https://docs.databricks.com/aws/en/generative-ai/agent-bricks/multi-agent-supervisor
- https://www.databricks.com/blog/mlflow-30-unified-ai-experimentation-observability-and-governance
- https://docs.databricks.com/aws/en/mlflow3/genai/prompt-version-mgmt/prompt-registry/track-prompts-app-versions

### Secondary (MEDIUM confidence)
- Alex Cole 2026 study guide.
- Mike Kahn Medium pass writeup.
- Santosh Joshi Medium overview.
- FlashGenius 2025 guide.

### Tertiary (LOW confidence — format only)
- ExamTopics / Skillcertpro / Whizlabs practice dumps. Treat answers as hypotheses; verify against docs.
