# FACTS — RAG, Vector DBs & Reranking

> Atomic, citable facts. Numbers, model names, benchmark scores. If a fact is here, it should be specific enough to use in a job interview without hand-waving.
>
> **Last verified:** 2026-05-10. Reranker and embedding leaderboards shift fast — re-verify before quoting in writing.

---

## 1. Foundations

- **RAG = Retrieval-Augmented Generation.** Term originates from the Lewis et al. 2020 Facebook AI paper ("Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks").
- **Why it exists:** parametric knowledge in an LLM is (a) frozen at training time, (b) lossy, (c) ungrounded (no citations), (d) fixed in size. RAG adds a non-parametric memory the model can consult at inference time.
- **Canonical pipeline (vanilla / "Naïve RAG"):** chunk → embed → store → retrieve top-k → stuff in prompt → generate.
- **When RAG is NOT the right tool:** when the answer is in parametric memory already (general knowledge), when the corpus is small enough to fit in context (long-context wins), when you need *behavior* changes (fine-tune), when latency budget is sub-100ms end-to-end (consider keyword search + cache).

---

## 2. Embeddings

- **MTEB** (Massive Text Embedding Benchmark) is the reference benchmark. Hosted on Hugging Face: `huggingface.co/spaces/mteb/leaderboard`. Covers 8 task families incl. retrieval, reranking, clustering, classification.
- **Top of MTEB English (early 2026):** Google **Gemini Embedding 001** (~68.32 avg), Alibaba **Qwen3-Embedding-8B** (~70.6 on retrieval-heavy slice), NVIDIA **NV-Embed-v2** (72.31 avg on certain configs).
- **Top commercial APIs:** Voyage AI **voyage-3-large** (leads retrieval-focused metrics; +10.58% over OpenAI text-embedding-3-large at matched dimensions), Cohere **embed-v4**, OpenAI **text-embedding-3-large** (3072 dim, $0.13/1M tokens) and **text-embedding-3-small** ($0.02/1M tokens).
- **Top open-source:** **BGE-M3** (BAAI; supports dense + sparse + multi-vector in one model, 100+ languages), **Qwen3-Embedding** (Apache 2.0), **Nomic Embed v2**, **Jina-embeddings-v3** (8K context, late chunking native).
- **Matryoshka Representation Learning (MRL):** training trick — first N dims of the vector form a usable lower-dim embedding on their own. Lets you truncate at query time. Adopted by Gemini Embedding, Voyage, Cohere v4, OpenAI text-3-*, Jina v5, Nomic v1.5. Industry standard as of 2026.
- **Bi-encoder vs cross-encoder (key distinction):**
  - Bi-encoder: encodes query and doc independently into vectors. Fast (millisecond search via ANN). Less accurate per-pair.
  - Cross-encoder: encodes (query, doc) pair jointly through a transformer. Slow (must run model per pair). Much more accurate.
  - Implication: bi-encoder retrieves, cross-encoder reranks the top candidates.

---

## 3. Vector Databases

### Index algorithms

| Algorithm | RAM-resident? | Filtered search | Update friendliness | Best for |
|-----------|---------------|-----------------|---------------------|----------|
| **HNSW** | Yes (full graph) | OK (post-filter or pre-filter w/ ACORN) | Good (incremental insert/delete) | Quality-first, mid-scale |
| **IVF / IVF-PQ** | Centroids in RAM, vectors compressible | **Strong** (centroid pre-filter) | Needs periodic rebuild | Filter-heavy, billion-scale |
| **DiskANN** | Compressed in RAM, full vectors on SSD | OK | Good (designed for dynamic data) | Disk-resident, very large corpora |
| **ScaNN** | Yes | OK | Moderate | Google-scale; specialized |

- **HNSW** = Hierarchical Navigable Small World. Multi-layer graph. Tunable: `M` (neighbors), `ef_construction`, `ef_search`. Pareto-optimal on most ANN benchmarks.
- **IVF-PQ** combines inverted file (clustering) with Product Quantization (compression). Memory-cheap; quality cost is small with right tuning.
- **DiskANN** keeps compressed vectors in RAM, full-precision on SSD. Microsoft research → used by Cosmos DB, SQL Server vector index. 7× faster than vanilla on GPU benchmarks.

### Distance metrics

- **Cosine**: scale-invariant; standard for normalized text embeddings.
- **Dot product**: equivalent to cosine *if* vectors are unit-normalized. Cheaper to compute.
- **L2 (Euclidean)**: less common for text; default for some image embeddings.
- **Rule:** use whatever metric the embedding model was trained for. OpenAI / Cohere / Voyage models are trained for cosine.

### Vendor landscape (2026)

| DB | Type | Notes |
|----|------|-------|
| **pgvector** | Postgres extension | Default if you already run Postgres. v0.9 added IVF_RaBitQ. Often within 10% of dedicated DBs. |
| **Qdrant** | Standalone (Rust) | Lowest p50 (~4ms), strong filtered search, hybrid native, payload-based multi-tenancy. |
| **Pinecone** | Managed only | Default if you want zero ops. Added hybrid in 2024. Serverless tier billed per-query. |
| **Weaviate** | Standalone (Go) | Hybrid + GraphQL native, strong multi-tenancy, modules for embeddings/rerankers. |
| **Milvus** | Standalone (Go/C++) | Best for very large scale (1B+); Zilliz is the managed version. |
| **Vespa** | Standalone (Java/C++) | Yahoo-built; production-grade hybrid; learning-to-rank built-in. |
| **OpenSearch / Elasticsearch** | Search engine + vector | Hybrid native; good if you already run it. k-NN plugin / `dense_vector` field. |
| **LanceDB** | Embedded / standalone | Lance columnar format; good for embedded / serverless. |
| **Chroma** | Embedded / serverless | DX-focused; popular for prototypes. |

### Latency benchmarks (10M-vector scale, public benchmarks)

- Qdrant: p50 ~4ms, p99 ~12-25ms
- Weaviate: p99 ~16ms
- Milvus: p99 ~18ms
- pgvector HNSW: within ~10% of Qdrant on equivalent compute (Supabase benchmark)

---

## 4. Chunking & Indexing

- **Recommended starting point:** RecursiveCharacterTextSplitter, 400-512 tokens, 10-20% overlap. NVIDIA found 15% optimal on FinanceBench at 1024-token chunks.
- **Semantic chunking:** split where sentence-embedding distance crosses a threshold. Up to ~70% lift over naive baselines, but pays embedding cost at indexing time. Marginal benefit fades above ~5000-token docs.
- **Agentic chunking:** LLM picks chunking strategy per document. Experimental; cost-prohibitive for most.
- **Anthropic's Contextual Retrieval (Sept 2024):** prepend each chunk with a 50-100 token LLM-generated *contextual summary* that says where the chunk sits in the doc. Then embed AND BM25-index the contextualized chunk.
  - **Numbers (Anthropic's own benchmark):** Contextual Embeddings reduce top-20 retrieval failure by **35%**. Combined with BM25: **49%**. With reranker on top: **67%**.
  - Cost: one-time LLM call per chunk at indexing — amortizable with prompt caching (Anthropic's own caching makes this near-free).
- **Late chunking (Jina, Sept 2024 paper, arXiv 2409.04701):** reverse the order — embed the *whole document* with a long-context embedding model, then mean-pool token spans into chunk vectors. Preserves cross-chunk context. Available in `jina-embeddings-v3`.
  - Reported lift: similarity scores rise from 70-75% to 82-84% on cross-chunk reference queries.
- **"Context cliff" finding (Jan 2026 systematic study):** response quality drops sharply around 2500-token chunks. Sentence chunking matched semantic chunking up to ~5000 tokens at far lower cost.
- **Multi-representation indexing:** index summaries for retrieval, but feed the full chunk to the LLM. Common in production.

---

## 5. Retrieval Strategies

- **Hybrid search:** combine sparse (BM25 / SPLADE) + dense (embeddings). Sparse handles exact-match (codes, IDs, jargon); dense handles semantic.
- **BM25** is a 1994-vintage probabilistic ranking function. Still hard to beat for keyword queries. SPLADE is a learned sparse retrieval model (neural, but produces sparse vectors).
- **Reciprocal Rank Fusion (RRF):** the standard fusion algorithm. Score = Σ 1/(k + rank_i). Default k=60 (works well empirically). Sidesteps score-normalization problem because it ignores absolute scores.
- **Weighted RRF:** assign per-source weight (e.g., dense 1.0, BM25 0.7) — useful when one source is known stronger.
- **Hybrid + RRF achieves ~91% recall@10 in published benchmarks** without score normalization.
- **HyDE (Hypothetical Document Embeddings, Gao et al. 2022):** prompt LLM to *write* a hypothetical answer to the query, embed THAT, then retrieve docs similar to the hypothetical. Usually generate 5 hypothetical docs and average embeddings. Fixes question-vs-document distribution mismatch.
- **Multi-query / RAG-Fusion (Adrian Raudaschl, 2023):** use LLM to generate N query rewrites, retrieve for each, fuse with RRF. Increases recall at cost of latency × N.
- **Step-back prompting:** generate a more abstract version of the query, retrieve for both, combine.
- **Self-querying retriever:** LLM extracts metadata filters from natural-language query (e.g., "papers from 2023 about LLMs" → filter year=2023, vector search "LLMs").

---

## 6. Reranking

### Reranker landscape (early 2026)

| Model | Type | Notes |
|-------|------|-------|
| **Zerank-2** | Closed (ZeroEntropy) | Top of leaderboard at 1638 ELO |
| **Cohere Rerank v4.0 Pro** | Closed API | 1629 ELO; production default; multilingual (100+) |
| **Voyage Rerank-2.5** | Closed API | ~Cohere quality at ~2× lower latency |
| **Jina Reranker v3** | Open-weight | 61.94 nDCG@10 on BEIR; **listwise**; 64 docs in 131K context |
| **Mixedbread mxbai-rerank-large-v2** | Open (Qwen-2.5 base, 1.5B) | 57.49 BEIR; trained with three-stage RL |
| **mxbai-rerank-base-v2** | Open (0.5B) | 55.57 BEIR; lightweight |
| **BGE-reranker-v2-m3** | Open (BAAI) | Lightweight, multilingual baseline |
| **gte-reranker-modernbert-base** | Open (149M) | Matches 1B+ models on Hit@1 — size ≠ quality |
| **nemotron-rerank-1b** | Open (NVIDIA) | Top accuracy when latency unconstrained |
| **rank-zephyr-7b**, **RankLlama** | Open LLM-rerankers | Listwise, open alternatives to RankGPT |

### Architectural categories

1. **Cross-encoder rerankers** — single transformer over `[query; doc]`, outputs scalar relevance. Most production rerankers (Cohere, Voyage, mxbai, BGE).
2. **Late-interaction (ColBERT family)** — multi-vector per doc; MaxSim aggregation. **Third path** between bi- and cross-encoder.
   - **PLAID** (CIKM '22): centroid-pruned engine; up to 7× faster on GPU, 45× on CPU vs vanilla ColBERTv2 with same quality.
   - **ColPali / ColQwen** — late interaction over *image patches* (treat PDFs as images). Each page → ~1030 patches × 128-dim.
3. **LLM-as-reranker** — frame ranking as generation. RankGPT (uses GPT-4), RankZephyr (open Mistral-7B), RankLlama. Pointwise / pairwise / **listwise** modes. RankLLM toolkit (Castorini, SIGIR 2025) is the reference implementation.
4. **MMR (Maximal Marginal Relevance)** — diversity-aware, not quality-aware. Score = (1−λ)·rel − λ·max_sim_to_already_picked. λ=0.7 is a common starting point. Use AFTER cross-encoder to deduplicate, not as primary reranker.

### Listwise vs pairwise vs pointwise (LLM rerankers)

- **Pointwise:** score each doc independently. Cheapest, weakest.
- **Pairwise:** score doc pairs (A vs B). Quadratic-ish.
- **Listwise:** model sees the whole candidate list and emits a permutation. Best quality. Used by RankGPT, Jina-rerank-v3.

### Cost / latency reality

- Rerankers are typically 50-300ms per query on candidate set of 50-100.
- Cohere/Voyage hosted: ~$1-2 per 1K rerank queries depending on doc count.
- Self-hosted rerankers (BGE, mxbai) eliminate per-query cost but need GPU; commodity for batch, more thought for low-latency online.

---

## 7. Advanced & Agentic RAG

- **Self-RAG (Asai et al. 2023):** model emits *reflection tokens* — `[Retrieve]`, `[IsRel]`, `[IsSup]`, `[IsUse]` — to decide when to retrieve and to grade what came back. Self-trained.
- **CRAG (Corrective RAG, Yan et al. 2024):** lightweight retrieval evaluator scores retrieved docs as Correct / Incorrect / Ambiguous, triggers refinement (rewrite + web search) when not Correct.
- **Adaptive RAG (Jeong et al. 2024):** small classifier (T5-large) predicts query difficulty (no-retrieve / single-step / multi-step) and routes accordingly. Saves cost on easy queries.
- **GraphRAG (Microsoft, 2024):** extract entity-relationship graph → cluster into communities → summarize each community level → query against community summaries (global) or local subgraphs (specific).
  - **Numbers:** 86% accuracy vs 32% baseline RAG on enterprise multi-hop benchmarks. 80% correct (90% with acceptable) vs 50.83% (67.5%) for vector RAG.
  - **Cost:** indexing 100-1000× more expensive than vector RAG. **LazyGraphRAG** reduces indexing to 0.1% of full GraphRAG.
  - **Caveats:** -13.4% on Natural Questions vs vanilla RAG; -16.6% on time-sensitive queries; +2.3× latency on average. Wins on multi-hop, loses on simple lookup.
- **HippoRAG, PathRAG, OG-RAG:** graph-RAG variants with different traversal/summarization strategies.
- **Long-context vs RAG (NVIDIA "ChatQA-2" + Qwen2-72B + GPT-4-Turbo benchmarks):**
  - Below 32K context: long-context can match or beat default RAG (top-5).
  - Above 200K: RAG over focused chunks usually wins on non-Gemini models.
  - Above 400K: RAG almost always wins on non-Gemini.
  - Gemini 1.5 Pro achieves >99.7% recall on single-needle up to 1M tokens; **Gemini 3** holds quality 200K-1M; multi-needle scores trail single-needle by 15-40 points across the field — single-needle NIAH overstates real capability.
- **Context Rot (Chroma research, 2024):** model performance degrades non-linearly as input tokens grow even within rated context length. Implication: just because the model accepts 1M tokens doesn't mean it uses them well.

---

## 8. Evaluation

### Retrieval-only metrics

- **Recall@k** — fraction of relevant docs found in top-k.
- **Precision@k** — fraction of top-k that are relevant.
- **MRR** (Mean Reciprocal Rank) — 1/rank of the first relevant doc, averaged.
- **NDCG@k** (Normalized Discounted Cumulative Gain) — graded relevance, position-discounted. Standard in IR. nDCG@10 is the default reranker benchmark metric.
- **MAP** (Mean Average Precision).
- **Hit@k** — binary: was any relevant doc in top-k?

### End-to-end RAG metrics (LLM-as-judge based)

- **Faithfulness** (Ragas) — does the answer follow from the retrieved context? 0-1.
- **Answer Relevancy** — does the answer address the question?
- **Context Precision** — were relevant chunks ranked at the top?
- **Context Recall** — did retrieved context cover the ground truth?
- **Context Relevancy** — fraction of retrieved context that's actually relevant.

### Frameworks

| Framework | Strength | Weakness |
|-----------|----------|----------|
| **Ragas** | Strict logical entailment for faithfulness; widely cited | Stricter scoring; can over-penalize valid paraphrases |
| **DeepEval** | Pytest-style; CI/CD native; pragmatic-interpretation faithfulness | Less strict than Ragas |
| **TruLens** | Dashboards, experiment tracking | Heavier UI; less suited for headless CI |
| **Phoenix (Arize)** | Tracing + eval combined | Eval set narrower than Ragas |
| **LangSmith** | Vendor-tied; great DX with LangChain/LangGraph | Less neutral |

- **Production-ready threshold (rule of thumb):** Ragas faithfulness ≥ 0.8 AND context precision ≥ 0.8.
- **Synthetic eval set generation:** Ragas, RAGAS-T, and DeepEval can generate (question, ground-truth answer, golden context) tuples from your own corpus. Always sanity-check by hand — generated questions skew easy.

---

## 9. Production

### Cost breakdown (typical production RAG)

- Embedding generation: 40-60% of cost
- Vector storage: 20-35%
- LLM inference: 15-25%
- Infra (compute, networking): 10-20%

### Latency budget (typical user-facing RAG, end-to-end ≤ 2-3s)

| Stage | Budget |
|-------|--------|
| Query embed | 20-50ms |
| Vector search (top-100) | 5-30ms |
| BM25 / hybrid fusion | 5-20ms |
| Reranker (cross-encoder, top-100→top-10) | 50-300ms |
| LLM generation (streaming first token) | 200-800ms |
| LLM full response | 1-3s |

### Caching

- **Embedding cache** (deterministic per content hash) — eliminate re-embedding for repeated content.
- **Semantic cache** (cache responses keyed by query embedding similarity) — hit on near-duplicate queries. Can cut p95 latency 2-5× and cost up to 80%.
- **Prompt cache** (Anthropic, OpenAI, Gemini) — caches the static portion of the LLM prompt server-side. Massive win when context is large and stable.
- **Matryoshka two-stage** — search 256-dim first for top 200-300, rerank with 1536-dim. Free quality-preserving cost cut on MRL-trained models.

### Drift & freshness

- **Embedding drift** — when you upgrade the embedding model, all your vectors are now in a different space. Re-embed the entire corpus. Plan for this.
- **Corpus freshness** — define ingestion latency SLO. Most production RAG re-indexes incrementally on doc change events.
- **Eval drift** — your golden eval set ages too. Refresh quarterly.

### Security

- **Indirect prompt injection (IPI):** attacker plants instructions in retrievable content (e.g., a webpage, support ticket). At query time, retriever pulls poisoned chunk into context. OWASP LLM Top 10 (2025) ranks this #1.
- **Mitigations (defense in depth):**
  1. Content provenance / source allowlists.
  2. Sanitization (HTML/Markdown stripping, Unicode normalization).
  3. Classifier-based input/output screening on retrieved content.
  4. Action screening: separate "intent" model checks tool calls against original user intent, ignoring retrieved context.
  5. Least-privilege tools.
  6. Attribution-gated answering (answer only what's traceable to source).
- **PII:** strip/redact at ingestion if corpus contains it; OR enforce row-level access control at query time. Choice depends on threat model.

---

---

## 10. Code retrieval, metadata enrichment & query routing

### Code-specialized embedders (early 2026)

| Model | Notes |
|-------|-------|
| **Voyage `voyage-code-3`** | SOTA on CodeSearchNet. **+5-8 NDCG over OpenAI text-embedding-3-large** on code retrieval. |
| **Qwen3-Embedding-8B** | Apache 2.0; tops **MTEB-Code** benchmark; strong multilingual + code combo. |
| **Gemini Embedding 2** | MTEB-Code ~84.0; best all-rounder when you want one embedder for everything. |
| **Jina Code Embeddings v2** | Specialized open-weight option. |

**Rule of thumb:** if > 30% of corpus is code, switching from a generic embedder to a code-specialized one reliably gains 5-10 retrieval points.

### Code-aware chunking
- **AST-based chunking** beats character/token splitting for code. Tools: tree-sitter (multi-language), LangChain `LanguageParser`, Sourcegraph SCIP.
- Chunks should align to functions, classes, methods, top-level blocks.

### The "grep beats vectors" finding
- Production code agents — **Cursor, Claude Code, Devin** — primarily use grep / ripgrep / filesystem tools, not vector search, for code work.
- Reasons: identifiers are exact; no staleness; no rename drift; free; composable.
- Vectors still win for concept-search ("where do we handle rate limiting") and onboarding queries.
- **Mature pattern:** hybrid router — agent picks grep / AST / vector / SQL / read_file per query.

### Metadata schema (typical fields)

**Mechanical (cheap, ingest-time):** `chunk_id`, `doc_id`, `doc_type`, `source`, `filename`, `file_path`, `section_path`, `page`, `chunk_index`, `language`, `last_modified`.

**LLM-enriched (per-chunk LLM call at ingest):** `summary`, `entities`, `topics`, `intent_categories`, `suggested_queries`, `content_type`, `contains_pii`.

### LLM enrichment patterns
- **MetaRAG / Dynamic Metadata RAG** — research framework (arXiv:2512.05411, late 2025). Uses LLM-generated metadata to enhance retrieval.
- **Single-call enrichment** — extract all metadata fields per chunk in ONE LLM call returning structured JSON, not one call per field.
- **Cost math:** 100K chunks × ~200 tokens → ~20M input tokens. With prompt caching, $50-200 one-time on Sonnet-class models.
- Metadata used at query time for: **filtering** (self-querying extracts filter expressions) AND **reranking signal** (entity overlap, summary similarity, topic match).

### Query-routing tool taxonomy

| Query class | Right tool |
|-------------|-----------|
| Specific file by name | `read_file` |
| Symbol lookup in code | `grep` / LSP references |
| Structured DB query | SQL execution |
| Concept / semantic | Vector search |
| Multi-hop reasoning | GraphRAG / agent loop |
| Real-time / external | API / web search |
| Math / computation | Code interpreter |

- Routers can be **classifier-based** (Adaptive RAG style) or **function-calling LLM-based** (modern default for agentic systems).
- Most production "RAG quality issues" are routing problems mistaken for retrieval problems.

---

## 11. Personalization & conversational / multi-turn retrieval

### Conversational RAG

- **Recall@5 drops from ~0.89 (first turn) to ~0.47 (later turns)** on MTRAG-style benchmarks. ~60% of follow-up messages have unresolved coreferences.
- **Standard fix:** query rewriter — fast LLM (Haiku/Flash class) rewrites the latest message into a self-contained query before retrieval. Adds <200ms in the critical path.
- **History-window finding:** performance saturates after **4-6 user turns**. Including bot turns adds little. For longer convos, summarize older turns into one block + keep last 3-4 verbatim.
- **Multi-strategy rewriting (frontier 2026):** generate 5 complementary rewrites — Minimal (coref-resolved), Corpus-Specific (domain terms), HyDE-style, Chain-of-Thought (decomposed), Anchor-Keyword (entities for sparse). Retrieve for each, fuse with RRF.
- **Failure modes:** topic shifts (rewriter hallucinates linkage); coreference to bot's prior answer (rewriter must see bot's last reply); latency stack-up.

### Personalization

- Three architectural levels (cost-ordered):
  1. **Filter-based scoping** (tenant, role, region as metadata filters). Most enterprise "personalization" is just this.
  2. **Reranker-conditioned** — pass user profile to reranker as context (cross-encoder fine-tune or LLM-as-reranker zero-shot).
  3. **Profile-as-vector** — aggregated engagement embedding combined with query embedding (typical α=0.7 on query, 0.3 on profile).
- **Feedback loop is the product.** Static profiles staleness-decay fast. Track explicit (thumbs, ratings) AND implicit (dwell, copy-text, re-query, abandonment) signals; recompute profile on a cadence.
- **Personalization ≠ memory.** Personalization = stable user attributes shaping ranking. Memory = specific facts the assistant has learned about the user shaping its parametric/contextual knowledge.

### Memory product landscape (2026)

| Tool | Philosophy |
|------|-----------|
| **Mem0** | CRUD memory layer; bolt onto any agent. Passive extraction via `add()`. |
| **Letta (formerly MemGPT)** | Full agent runtime with explicit memory blocks; OS-inspired hierarchy. |
| **Provider-managed** | ChatGPT memory, Claude Projects, Gemini Workspace. |
| **Custom vector RAG per user** | DIY when schema needs are specific. |

Clean separation: RAG retrieves from corpus; Memory retrieves from user-specific facts; Personalization shapes both.

---

## 12. Document extraction & structured data RAG

### Document parsers (2026)

| Tool | Notes |
|------|-------|
| **Unstructured** | "ETL for LLMs"; 50+ formats; element-typing; open + SaaS |
| **LlamaParse** | Multi-column aware; agentic mode for complex docs; ~$0.003-$0.09/page |
| **Docling** (IBM) | Open; layout + reading-order + table structure recognition |
| **Mistral OCR** | VLM-based; multilingual; tables/equations/LaTeX; **$0.001/page (batch)** |
| **Reducto** | Premium parsing; finance/legal accuracy |
| **AWS Textract / Azure Document Intelligence / Google Document AI** | Cloud-native OCR + forms + tables |
| **PyMuPDF / PyMuPDF4LLM** | Open libs; free, fast, simple PDFs |
| **OpenDataLoader** | Open; XY-Cut++ multi-column handling; **0.928 table accuracy** on 200 real PDFs |
| **Firecrawl Fire-PDF** | <400ms/page average; up to 25s on complex tables |

**Key principle:** "garbage in, garbage out." Most RAG quality issues trace to the parser, not the embedder.

### PDF-specific failure modes
- **Multi-column interleaved as gibberish** → layout-aware parser (Docling, LlamaParse, OpenDataLoader XY-Cut++).
- **Tables flow into paragraphs** → table-aware extractor (Camelot/Tabula for vector PDFs; VLM for visual).
- **Scanned PDFs return empty** → OCR (Tesseract / Textract / Mistral OCR).
- **Headers/footers pollute chunks** → element-aware parser tags `Header`/`Footer`.
- **Math / LaTeX garbled** → math-aware extractor (Mistral OCR, Marker).

### Structured data — the principle
- **Don't embed rows of Excel/CSV/SQL data.** Embeddings distort numbers, prevent aggregation, kill filtering perf, and explode cost.
- **Right pattern: text-to-SQL with RAG-over-schema.** Embed: table descriptions, column descriptions/units, glossary, example queries. Don't embed: data itself.
- **Tools:** Vanna AI (RAG-for-SQL, agent-based 2.0), LangChain SQL agent, LlamaIndex `NLSQLTableQueryEngine`, DSPy text-to-SQL, vendor-native (Snowflake Cortex, BigQuery Gemini, Databricks Genie).
- **Tables-in-PDFs (hybrid case):** index per-table — markdown rendering + LLM summary + column-header embedding. Route aggregation queries to code-interpreter or SQL on the table.

### Multimodal RAG (early 2026)

| Model | Notes |
|-------|-------|
| **Gemini Embedding 2** (March 2026) | First natively multimodal embedding. Text+image+video+audio+PDF in one 3072-dim space. MTEB English 68.32; video retrieval 68.8. |
| **Qwen3-VL-2B** | Apache 2.0; smaller modality gap (0.25 vs Gemini's 0.73); 0.945 cross-modal retrieval. |
| **ColPali / ColQwen** | Late interaction over image patches; SOTA for visually-rich docs. |
| **CLIP / OpenCLIP** | Foundation; still useful for image-only tasks. |
| **Voyage Multimodal 3.5** | Alternative API. |

Three patterns: caption-then-text (simple), native multimodal embedding (flexible), hybrid (caption + multimodal embed, RRF fuse).

---

## 13. Evaluation deep dive (Modules 13A/B/C)

### LLM-as-judge mechanics
- **Ragas faithfulness algorithm:** two-step LLM pipeline. (1) Decompose answer into atomic, pronoun-resolved claims. (2) NLI-judge each claim against retrieved context, return 0/1. Score = supported/total.
- **DeepEval faithfulness:** different — checks for contradictions, not strict entailment. Same answer/context can score Ragas 0.95 / DeepEval 0.71. Both valid, measure different things.
- **A score without "framework + judge model + version" is not a number.**

### Judge biases (Zheng et al., NeurIPS '23, arXiv:2306.05685)
- **Position bias** — judges favor first option. GPT-4: ~60% consistent on order swap.
- **Verbosity bias** — judges over-prefer longer responses; all LLMs susceptible.
- **Self-preference bias** — LLMs prefer outputs from their own family; linked to self-recognition.
- **Style bias** — over-rewards confident tone, formatting.
- **Mitigation stack:** position-swap + cross-family judge + calibrated rubric + multi-judge ensemble. 2025 study (arXiv:2604.23178) found 18/20 strategies improve overall.

### Statistical rigor
- **Sample sizes:** hackathon 20-50; internal 100-200; customer-facing 500+; high-stakes 1000+.
- **CLT breaks below ~200 samples** ([2025 paper](https://arxiv.org/abs/2503.01747)). Use bootstrap, not t-test.
- **Bootstrap with B=1000 iterations.** Non-overlapping 95% CIs = strong evidence A ≠ B.
- **Independence violations are silent killers:** same passage / same user → cluster-aware bootstrap.
- **IAA metrics:** Cohen's κ (2 raters), Fleiss' κ (3+ raters categorical), **Krippendorff's α** (any data type, missing values OK — Google standard), Gwet's AC (skewed prevalence — Meta).
- **IAA targets:** > 0.8 high; 0.67-0.8 substantial; < 0.4 task is under-defined.

### The benchmark zoo

**Pure retrieval:**
- **MS-MARCO** (2018, MRR@10) — Bing query in-distribution.
- **TREC-DL** (annual) — IR field gold standard, expert labels.
- **BEIR** (2021) — 18 domains zero-shot generalization, NDCG@10.
- **MTEB Retrieval** — 15 datasets, default embedder leaderboard.

**End-to-end RAG:**
- **KILT** (2021) — 11 knowledge-intensive tasks.
- **NQ (Natural Questions)** — Google queries + Wikipedia.
- **RAGBench** (2024) — 100K examples, industry corpora, TRACe metric framework.
- **RAGTruth** (2024) — 18K LLM responses with **word-level hallucination** annotation.
- **MTRAG** — multi-turn RAG; Recall@5 0.89→0.47 across turns.
- **FRAMES** (Google, Sept 2024) — 824 hard multi-hop questions, 2-15 articles each. Single-step 0.40 → multi-step 0.66 → oracle 0.73.

**Long-context:**
- **NIAH single-needle** — saturated.
- **NoLiMa** (Feb 2025) — minimal lexical overlap; GPT-4o drops 99.3% (1K) → 69.7% (32K). The honest long-context test.
- **BABILong** — long-context reasoning.

**Domain:** MedQA, MIMIC-CDR (medical); LegalBench, CaseHOLD (legal); FinQA (finance); HumanEval, SWE-Bench (code); BIRD (text-to-SQL).

### Online / production eval
- **Shadow traffic before A/B** — log only, no user impact, ≥ 1-2 weeks.
- **A/B sample size formula (binary metric):** N per arm ≈ 16·p·(1-p) / Δ². Detecting 3pp lift on 30% baseline ≈ 3,700 / arm.
- **Interleaving** — 10× more sample-efficient than user-bucket A/B for search-style results.
- **Sequential testing** (mSPRT, group sequential, always-valid p-values) lets you stop early without inflating false positives.
- **Multi-armed bandits / Thompson sampling** — for maximize-reward scenarios; risks premature convergence under non-stationarity.

### Human eval
- **SxS beats pointwise.** "Is A better than B" more reliable than "rate A 1-5."
- **Likert: 3-5 levels with anchors beats 7-10.** Central tendency bias collapses signal on wide scales.
- **Anchor examples + calibration round + per-rater bias tracking** — minimum viable rater pipeline.

### Red team
- **ASR (Attack Success Rate)** + **FRR (False Refusal Rate)** — both matter.
- **Tools:** Promptfoo (50+ attack plugins), DeepTeam, Lakera Gandalf, Garak (NVIDIA), HarmBench, RedBench.
- **Refusal-aware red-teaming (EMNLP 2025):** models refuse one phrasing of a probe and answer a near-paraphrase; need external classifier guardrail.

### Hallucination detectors
- **Patronus Lynx (8B / 70B)** — open-weight Llama-3 fine-tune; outperforms GPT-4o, Claude-3-Sonnet on hallucination detection. Released 2024.
- **Vectara HHEM-2.1-Open** — lightweight cross-encoder; runs on consumer GPU; ~1.5s on CPU for 2K tokens.
- **Vectara HHEM-2.3** — commercial, higher quality.
- **Galileo Hallucination Index** — combined detection + observability + leaderboard.

### Observability tools (early 2026)
- **Langfuse** (OSS, MIT, 19K+ stars) — default open-source full-stack.
- **Arize Phoenix** (OSS, 7.8K+ stars) — OpenTelemetry-native.
- **Comet Opik** — agent-trace focus.
- **LangSmith** — best DX with LangChain.
- **Galileo, Helicone, Traceloop** — specialized.
- **OpenTelemetry GenAI semantic conventions** — vendor-neutral standard.

### Drift detection
- **Fingerprint set** of 1000 representative texts, embed weekly, compare cosine.
- Healthy: 85-95% nearest neighbors persist week-over-week. Drifting: 25-40% drop off.
- **Three drift types:** model drift (provider silent updates), corpus drift (KB changes), query drift (users ask new things, new vocab).

### Eval-as-CI cost
- Naive Ragas-on-every-PR: $30-100/run. Killers: tiered judges, judge-call cache (>80% hit on stable evals), sampling, deterministic structural assertions, dedicated 7B judges (Lynx-8B).

---

## 14. Grounding, citation & hallucination

### Vocabulary
- **Grounding:** output anchored in retrieved evidence.
- **Faithfulness:** claims don't contradict retrieved context (Module 13A).
- **Citation:** each claim linked to specific supporting span.
- **Factuality:** output consistent with reality (regardless of context).
- **A faithful answer over a wrong corpus is unfactual but not hallucinating.**

### Hallucination taxonomy (2025)
- **Intrinsic:** contradicts the input/context. Checkable; detect with NLI/Lynx/HHEM.
- **Extrinsic:** can't be verified from context. Harder; needs external source-of-truth or model-internal signals.
- **Citation hallucinations:** ~3-15% of long-form RAG citations are hallucinated even when underlying facts are correct (FACTUM, arXiv:2601.05866).

### Citation strategies (trust order)
1. Document-level — weakest, often un-auditable.
2. Inline span — Perplexity/Bing/Claude pattern.
3. **Claim-level grounding** — gold standard, required for regulated domains.

### Architectural patterns
- **GTR** (generate-then-retrieve, post-hoc citation) — structurally unsuitable for regulated work.
- **RTG** (retrieve-then-generate) — standard RAG; better but model can still drift.
- **Inline citation generation** with parser-validated pointers (Anthropic Citations API) — only architecture consistent by construction.

### Citation benchmarks
- **ALCE** (EMNLP 2023) — canonical; 3 datasets (ASQA, QAMPARI, ELI5). Line-level citations beat document-level by **>14 points** in precision.
- **GaRAGe** (June 2025, arXiv:2506.07671) — 2,366 questions, 35K+ annotated passages. ALCE successor.
- **AttributedQA** — earlier, narrower.

### Hallucination detection categories
- **NLI-based:** DeBERTa-NLI, AlignScore, SummaC, Vectara HHEM-2.1-Open. Cheap (~40ms/pair); narrower.
- **LLM-judge:** Ragas, DeepEval, Patronus Lynx-8B/70B (open Llama-3 SOTA), GPT-4 with rubric.
- **Self-consistency:** SelfCheckGPT — sample N, check agreement.
- **Internal-state / mechanistic:** FACTUM, attention/logit analysis.

### "RAG paradoxically increases hallucinations"
- Distractor chunks invite confabulated connections.
- Conflicting chunks force confident pick.
- "Use only context" prompt forces fabricated support over refusal.
- Mitigation: refusal-aware generation (CRAG, Self-RAG, abstention triggers).

### Abstention signals (combine for refusal policy)
1. Top retrieved cosine < threshold (~0.55).
2. Reranker top score < threshold (~0.4).
3. Faithfulness mid-stream < threshold (~0.7).
4. NLI: claims unsupported fraction > threshold (~0.3).
5. Self-consistency disagreement.
6. Hallucination detector score > threshold.

---

## 15. Multilingual & long-context failures

### Multilingual architectural patterns
1. Translation-as-bridge — translate query to corpus language, retrieve, translate back. Cost: compounding errors.
2. **Native cross-lingual embedding** — one model, shared space. 2026 default for top languages.
3. Per-language indexes — best per-language quality, ops overhead.

### Multilingual embedders (early 2026)
| Model | Notes |
|-------|-------|
| **BGE-M3** | Open, 100+ langs, dense+sparse+multi-vector in one. **MIRACL ~70.0 nDCG@10** avg across 18 languages. De-facto open default. |
| **multilingual-E5 (small/large)** | Open, smaller. Strong on Arabic / Indic languages. |
| **Cohere embed-multilingual-v3** | Commercial API, 100+ langs. |
| **Qwen3-Embedding (0.6B/4B/8B)** | Apache 2.0; **tops MMTEB**; 0.6B competitive with Gemini Embedding. |
| **Gemini Embedding 2** | Native multilingual + multimodal in one. |

### Multilingual benchmarks
- **MIRACL** — 18 languages, monolingual per language. nDCG@10 standard.
- **mMARCO** — multilingual MS-MARCO, cross-lingual.
- **XOR-TyDi** — cross-lingual open-domain QA.
- **MMTEB** — multilingual MTEB.

### English bias
- Multilingual embedders score **10-30 points higher on English** than non-English on the same task. Always run **per-language SLOs**, never just a global one.

### Lost in the Middle (Liu et al. 2023, TACL 2024, arXiv:2307.03172)
- U-shaped accuracy curve across context positions: ~75% at extremes, ~50% in middle.
- Called **serial-position effect** in psychology (Ebbinghaus 1913).
- Holds across all frontier models.

### Mitigations
- **Reorder by reranker score with U-aware placement** (top-1 at start, top-2 at end, top-3 at position 2, ...). Free; +5-10% answer quality routinely.
- **Top-k smaller is better** past a point. 5-10 well-chosen beats 20-50.
- **Iterative retrieve-read** (CRAG, Self-RAG) sidesteps via small focused contexts.
- **Position encoding extensions:** PI, YaRN, LongRoPE, CLEX, Self-Extend (consumed via models).
- **Attention modifications:** StreamingLLM, H2O, TOVA, Activation Beacon (architectural).

### NoLiMa headline numbers
- GPT-4o: **99.3% at 1K → 69.7% at 32K tokens.**
- 11 of tested models drop **below 50% of short-context baseline** at 32K.
- Multi-needle trails single-needle by 15-40 points.
- "Supports 1M tokens" overstates real capability for non-trivial multi-fact reasoning.

### Compound failure
- Lost-in-the-middle is **worse** in non-English long contexts. Tokenization is less efficient (more tokens per word, pushing info further in); position encoding is English-tuned. Per-language top-k tuning helps.

---

## 14. Domain case studies (Module 16)

- **Healthcare:** HIPAA mandates BAA per vendor, PHI encryption at-rest + in-transit, audit log per query. Four PHI exposure surfaces: query, retrieved chunks, response, audit log. Citation: claim-level required. Refusal calibrated liberal. Eval: MedQA, MIMIC-CDR, PubMedQA, MedRAG.
- **Legal:** LegalBench-RAG (6,858 expert-annotated query-answer pairs over 79M chars) is the reference benchmark — tests precise retrieval of pinpoint citations. 2025 VLAIR study: CoCounsel/Vincent AI/Harvey/Oliver all struggle on multi-jurisdictional questions. Architectural fix: jurisdiction extractor LLM + filter + status validator.
- **Financial:** Number-precision is everything. Faithfulness alone misses dollar/percentage swaps. Add structural number-match validator. Time-aware retrieval mandatory. Tabular data goes to text-to-SQL, not RAG. Compliance: SR 11-7, SOX. Benchmarks: FinQA, TAT-QA, ConvFinQA, FinanceBench.
- **Customer support:** 40-60% deflection achievable with mature RAG. ~30% op-cost reduction. CSAT lift ~25%. **KB quality determines ~80% of agent performance.** Patterns: intent classifier in front, semantic cache (30-50% hit), confidence-gated escalation.

## 15. Security, privacy & auditing (Module 17)

- **Vec2Text** (Morris et al. 2023, arXiv:2310.06816): **92% exact recovery of 32-token text from embeddings.** Treat embedding storage like source-text storage.
- **ALGEN, ZSinvert, BeamClean** (2024-2025): cross-embedder, zero-shot, noise-adaptive inversion.
- **Defenses:** don't expose raw vectors; encrypt at rest; Gaussian noise (mild); concept-aware obfuscation; differential privacy (formal).
- **Federated RAG:** FedE4RAG, FRAG, HyFedRAG. Use single-key homomorphic encryption (SK-MHE) for ciphertext vector ops. Use case: multi-org collaboration.
- **DP-RAG** (arXiv:2412.04697): formal `(ε, δ)` privacy. Useful at ε≈5 if facts appear in ≥100 docs.
- **TEE / Confidential Compute** (RemoteRAG, ACL 2025): hardware-attested isolation; faster than HE.
- **Counterfactual RAG** (CF-RAG, Causal-CF-RAG 2025): identifies causally relevant chunks via systematic perturbation. Audit-grade explainability.

## 16. Frontier retrieval patterns (Module 18)

- **SPLADE** (SIGIR '21/'22): learned-sparse retrieval. Outputs sparse vector over BERT vocab; runs on standard inverted indexes (Lucene/Elasticsearch). Term weighting + term expansion. Latency similar to BM25; quality between BM25 and dense.
- **TILDE / TILDEv2:** alternative learned-sparse; faster query-time inference than SPLADE.
- **Reasoning-model RAG patterns:** (a) reasoning model as generator; (b) Search-during-thinking (Search-o1, Search-R1) — model interleaves retrieval with thought; (c) self-consistency over N RAG attempts.
- **Test-time-compute caveat (arXiv:2502.12215, ACL 2025):** longer CoTs don't reliably improve answers; correct solutions often shorter than incorrect ones.
- **LightRAG** (EMNLP 2025): 10× token reduction vs Microsoft GraphRAG; 65-80% cost savings at 1500+ docs/month. Dual-level retrieval. Production-ready.
- **AutoSchemaKG** (May 2025): autonomous schema induction from web-scale corpora.
- **LLM-driven KG construction:** Precision ~98.8%, Recall ~93.2%, F1 ~95.9% on entity extraction; ~75% precision on relations.

## 17. Web, real-time & multimodal (Module 19)

- **Web search APIs (2025-2026):**
  - **Tavily** — RAG-quality, factual, SOC 2 (acquired by Nebius Feb 2026).
  - **Exa** — semantic / research; 94.9% on SimpleQA Research API.
  - **Perplexity** — fastest median ~358ms; returns finished answers.
  - **Linkup** — citation grounding; entity coverage.
  - **Serper / Brave** — volume / cost.
- **15× latency spread** across the field (358ms – 5.49s).
- **CDC for RAG:** Striim, Confluent Flink+embeddings, Streamkap, Debezium-based pipelines. Chunk-level CDC achieves 10-15% re-processing (vs 85-95% for standard upsert). 40-60% accuracy lift on time-sensitive queries.
- **LiveVectorLake** (2026): bitemporal versioned RAG; "as-of-time-T" queries.
- **Long-context as cache:** corpus < 200K tokens AND stable, with 5-min cache TTL (Anthropic, Gemini). 70-90% cost reduction on cached prefix. Beats RAG for narrow stable corpora.

## 18. Production engineering (Module 20)

- **vLLM** is the production default for self-hosted LLM serving (Apache 2.0, OpenAI-compatible API, PagedAttention, broad model support).
- **TGI, SGLang, TensorRT-LLM** are alternatives; TGI is simpler but lacks chunked prefill.
- **Self-host threshold:** typically >$10K/month managed spend OR >10B embedding tokens/month.
- **K8s patterns:** GPU node taints + tolerations; KEDA autoscaling on queue depth (NOT CPU); Pod disruption budgets; topology spread.
- **NVIDIA reference architecture:** NIM microservices + cuVS GPU vector search. Available 2025-2026.
- **FinOps tooling:** Portkey, Helicone, Langfuse, Traceloop, Datadog LLM Obs, Finout, Vantage.
- **Cost levers ranked:** trim context (30-60% reduction), model routing (Sonnet→Haiku 80% reduction), prompt caching (70-90% reduction on prefix), semantic cache (30-50% hit), small embedder (6× cheaper), batch tier.
- **Average AI spend 2025:** $85,521/org/month, +36% YoY.
- **Native RAG wastes 70-80% of input tokens** without proper reranking.
- **Cache invalidation:** dependency tracking (cached response → supporting chunks → invalidate on change) > naive TTL for correctness.

## 19. Benchmarks, tokenization & trade studies (Module 21)

- **Benchmark by use case:** MTEB Retrieval (embedder), BEIR (reranker), RAGBench/FRAMES (end-to-end RAG), NoLiMa (long-context honest), MIRACL (multilingual), LegalBench-RAG, MedQA/MIRAGE, FinQA/TAT-QA, BIRD/Spider (text-to-SQL), CodeSearchNet/MTEB-Code.
- **Tokenization edge cases:** invisible Unicode chars (ZWSP `U+200B`, soft hyphen `U+00AD`, BOM `U+FEFF`, RTL `U+202E`); pre-tokenization quirks (NBSP vs space); non-English tokenizes 2-3× more tokens; chunk boundaries should be token-aware not char-aware.
- **NFKC normalization + invisible-char stripping** at ingestion AND query time is the production fix.
- **RAG vs FT empirical findings (2025):** FT in code completion saturates ~300M tokens; RAG keeps improving. Medical hybrid (FT+RAG) consistently beats either alone for safety-critical QA. Snorkel: fine-tuned smaller model can match GPT-3 at 1,400× smaller for narrow tasks.
- **2026 production consensus:** **volatile knowledge → retrieval, stable behavior → fine-tuning.**
- **Default order to try:** prompt-only → RAG → LoRA → full FT.

---

## 20. GraphRAG deep dive (Module 22)

### Microsoft GraphRAG pipeline (arXiv:2404.16130)
- Per-chunk LLM call extracts **entities** (name, type, description), **relationships** (source, target, description, strength 1-10), and optional **covariates / claims** (subject, object, status ∈ {TRUE, FALSE, SUSPECTED}, time-bounds).
- Default entity types: `person | organization | geo | event`; customizable.
- **Covariates are off by default** — they roughly double indexing cost.
- Entity de-duplication: same entity mentioned in many chunks → one consolidated node with LLM-merged description.
- **Leiden algorithm** (not Louvain — Leiden guarantees connected communities) runs hierarchically: L0 (small dense), L1 (medium), L2 (large), L3 (root).
- Each community gets an LLM-generated **community report** — primary retrieval target for global search.

### Three query strategies
- **Local search**: extract entities from query → match graph nodes → walk N hops → assemble chunks + relationships + community reports.
- **Global search**: map-reduce over all community reports at the chosen level.
- **DRIFT** (Dynamic Reasoning and Inference with Flexible Traversal): hybrid — match query against top-K community reports → generate broad initial answer + follow-up questions → run each follow-up as local search → synthesize.

### Cost reality (100K-doc corpus, Sonnet-class extractor)
- Microsoft GraphRAG full features: **~$40K-$60K** indexing.
- LazyGraphRAG: **~$300-$1,000** (0.1% to 2%).
- LightRAG: **~$4K-$8K** (~10%).
- Vector RAG baseline (embeddings only): **~$65**.
- Microsoft GraphRAG shipped a `--estimate-cost` CLI flag (May 2025) to forecast cost before kicking off indexing.

### HippoRAG (NeurIPS 2024, arXiv:2405.14831)
- Inspired by hippocampal indexing theory.
- Workflow: LLM extracts query concepts → seed entity nodes in schemaless KG → **Personalized PageRank** distributes mass through graph → highest-PPR passages are retrieved context.
- **+20% multi-hop QA over SOTA.** Single-step beats iterative retrieval (IRCoT) at **10-20× cheaper, 6-13× faster.**

### HippoRAG 2 (Feb 2025, arXiv:2502.14802)
- **Dual-node KG** — passage AND phrase nodes coexist; PPR over both.
- **LLM-based triple filtering** post-PPR removes noise.
- **Continual learning** — incremental updates without full re-index.
- Evaluated on: factual memory (NQ, PopQA), sense-making (NarrativeQA), associativity (MuSiQue, 2Wiki, HotpotQA, LV-Eval).
- **+7 F1 over NV-Embed-v2** on associative benchmarks.

### PathRAG (Feb 2025, arXiv:2502.14902)
- Retrieves **only the relational paths between query-relevant nodes** (not whole communities, not immediate neighbors).
- Flow-based pruning with distance-aware reliability scoring.
- Paths ordered ascending-reliability in prompt to combat lost-in-the-middle.
- **59.93% win rate vs Microsoft GraphRAG**, **57.09% vs LightRAG**, **13.69% token reduction vs LightRAG**.

### OG-RAG (Dec 2024 / EMNLP 2025, arXiv:2412.15235)
- Ontology-grounded **hypergraph** (hyperedges connect multiple entities per fact).
- Requires upfront ontology (SNOMED CT for medical, FIBO for finance, etc.).
- **+55% recall**, **+40% response correctness** across 4 LLMs, **+27% fact-based reasoning**.

### HyKGE (ACL 2025, arXiv:2312.15883)
- HyDE applied to graph retrieval. Pipeline:
  1. Hypothesis Output Module (LLM generates plausible answer first).
  2. NER (W2NER extracts entities from hypothesis).
  3. Retrieve from medical KG using those entities.
  4. Rerank with fragment-granularity-aware reranker.
- Validated on Chinese medical QA. Strong on accuracy + explainability.

### GraphReader (EMNLP 2024, arXiv:2406.14550)
- Graph as navigation aid for **long single documents**.
- Agent plans, walks, and reflects using predefined node-read functions.
- **4K-context GraphReader beats GPT-4-128K** across 16K-256K context lengths.

### MedGraphRAG (ACL 2025, arXiv:2408.04187)
- **Triple-graph**: Tier 1 user docs → Tier 2 credible sources (PubMed, FDA, guidelines) → Tier 3 general medical KG (UMLS, SNOMED).
- **U-Retrieval** — top-down precise retrieval + bottom-up response refinement.
- Validated on 9 medical QA benchmarks + 2 health fact-checking + long-form generation. Boosts GPT-4 and LLaMA-3-70B above human-expert accuracy on certain tasks.

### Multi-hop benchmark scores (approximate)
- Vector RAG: 2WikiMultiHopQA F1 ~0.45, HotpotQA ~0.50, MuSiQue ~0.20.
- Microsoft GraphRAG: 2Wiki F1 ~0.63, HotpotQA ~0.65, MuSiQue ~0.33.
- HippoRAG: 2Wiki ~0.65-0.70, HotpotQA ~0.67, MuSiQue ~0.35.
- HippoRAG 2: +7 F1 over NV-Embed-v2 on associative slice.

### Hybrid Vector+Graph routing
- **~80% queries** simple semantic → vector RAG.
- **~15% queries** multi-hop / aggregative → graph RAG.
- **~5% queries** multi-step planning → agent.
- Patterns: **Vector-first** (vector → expand via graph), **Graph-first** (graph → enrich via vector), **Dynamic routing** (classifier picks).
- "Routing is the product" — classifier quality drives user-facing quality more than any individual retriever.

### Healthcare case study architecture
- Triple-graph (MedGraphRAG) + ontology grounding (OG-RAG) + path retrieval (PathRAG) + PPR (HippoRAG) + vector fallback.
- Authority-tier reranking: peer-reviewed > FDA label > internal guideline > clinician note.
- Strict abstention if no peer-reviewed support.
- Audit log per query, 6+ year retention (HIPAA).
- No PHI in third-party APIs without BAA.

### Tooling landscape
- **Microsoft GraphRAG** — reference implementation (Python).
- **LazyGraphRAG** — Microsoft follow-up (lazy extraction).
- **LightRAG** — HKU dual-level retrieval (EMNLP 2025).
- **HippoRAG / HippoRAG 2** — OSU NLP Group.
- **Neo4j LLM Knowledge Graph Builder** — UI + LangChain integration.
- **neo4j-graphrag-python** — official Neo4j GraphRAG library.
- **Memgraph, NebulaGraph, FalkorDB, Apache AGE** — graph DB alternatives.

### When NOT to use graph-RAG
- 80%+ queries are simple semantic lookup.
- Corpus is flat prose with little relational structure.
- Indexing budget < $5K/month for the corpus size.
- Corpus updates faster than indexing pipeline runs.
- < 15-20% of real queries require multi-hop or aggregation.

---

## Sources & references

- Anthropic — [Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval)
- Lewis et al. 2020 — [RAG paper (arXiv:2005.11401)](https://arxiv.org/abs/2005.11401)
- Khattab & Zaharia 2020 — [ColBERT (arXiv:2004.12832)](https://arxiv.org/abs/2004.12832)
- Santhanam et al. 2022 — PLAID (CIKM '22)
- Jina — [Late Chunking paper (arXiv:2409.04701)](https://arxiv.org/abs/2409.04701)
- Asai et al. 2023 — Self-RAG (arXiv:2310.11511)
- Yan et al. 2024 — CRAG (arXiv:2401.15884)
- Jeong et al. 2024 — Adaptive RAG (arXiv:2403.14403)
- Microsoft — [GraphRAG](https://github.com/microsoft/graphrag) and Microsoft Research blog
- Chroma — [Context Rot research](https://research.trychroma.com/context-rot)
- MTEB Leaderboard — `huggingface.co/spaces/mteb/leaderboard`
- BEIR Benchmark — Thakur et al. 2021
- OWASP — [LLM Top 10 (2025)](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)
- Castorini RankLLM — [github.com/castorini/rank_llm](https://github.com/castorini/rank_llm)
- Ragas — [docs.ragas.io](https://docs.ragas.io)
- DeepEval — [deepeval.com](https://deepeval.com)
