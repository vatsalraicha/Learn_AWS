# Topic 01 — RAG, Vector Databases & Reranking

> Test topic for the Career_upskill format. If this works, we replicate the structure for other topics (project management, cloud certs, etc.).

## Learning path

| # | Module | Why it matters |
|---|--------|----------------|
| 1 | [Foundations](01_foundations.md) | Why RAG exists, the canonical pipeline, when NOT to use RAG |
| 2 | [Embeddings](02_embeddings.md) | The vector layer — bi-encoders, MTEB, Matryoshka, multi-vector |
| 3 | [Vector Databases](03_vector_databases.md) | HNSW/IVF/PQ/DiskANN internals; the 2026 vendor landscape |
| 4 | [Chunking & Indexing](04_chunking_indexing.md) | Recursive, semantic, agentic, contextual retrieval, late chunking |
| 5 | [Retrieval Strategies](05_retrieval_strategies.md) | Hybrid (BM25+dense), RRF, HyDE, multi-query, RAG-Fusion, self-querying |
| 6 | [Reranking](06_reranking.md) | **Deepest module.** Cross-encoders, ColBERT, LLM-as-reranker, MMR, listwise |
| 7 | [Advanced & Agentic RAG](07_advanced_agentic_rag.md) | Self-RAG, CRAG, Adaptive, GraphRAG; long-context vs RAG |
| 8 | [Evaluation](08_evaluation.md) | Recall@k, MRR, NDCG, faithfulness; Ragas, TruLens, DeepEval |
| 9 | [Production](09_production.md) | Latency budgets, cost math, caching, drift, prompt injection, PII |
| 10 | [Code Retrieval, Metadata & Routing](10_code_metadata_routing.md) | Code embedders, AST chunking, grep-vs-vector, LLM-enriched metadata, function-calling routers |
| 11 | [Personalization & Conversational RAG](11_personalization_conversational.md) | Multi-turn query rewriting, user profiles, feedback loops, memory (Mem0/Letta) vs personalization |
| 12 | [Extraction & Structured Data](12_extraction_structured_data.md) | PDF/PPTX/HTML/Excel parsing, OCR vs VLM, text-to-SQL, multimodal RAG |
| 13A | [Eval Methodology & Statistics](13a_eval_methodology_statistics.md) | LLM-judge mechanics, biases, bootstrap CIs, the benchmark zoo, calibration |
| 13B | [Eval — Online & Human](13b_eval_online_human.md) | Shadow traffic, A/B, interleaving, MAB, SxS rubrics, IAA, red-team |
| 13C | [Eval — Production Observability](13c_eval_observability_ops.md) | OTel-LLM tracing, drift monitoring, hallucination detectors, eval-as-CI |
| 14 | [Grounding, Citation & Hallucination](14_grounding_citation_hallucination.md) | Citation mechanics, hallucination taxonomy, ALCE/GaRAGe, abstention triggers |
| 15 | [Multilingual & Long-Context Failures](15_multilingual_long_context.md) | Cross-lingual embedders, MIRACL, Lost in the Middle, NoLiMa, position encoding |
| 16 | [Domain Case Studies](16_domain_case_studies.md) | Medical (HIPAA/citation/refusal), legal (pinpoint/jurisdiction), financial (numbers/SQL), customer-support (deflection/cache) |
| 17 | [Security, Privacy & Auditing](17_security_privacy_auditing.md) | Embedding inversion (Vec2Text), federated/DP/TEE RAG, counterfactual auditing, audit logs |
| 18 | [Frontier Retrieval Patterns](18_frontier_retrieval_patterns.md) | SPLADE deeper, reasoning-model RAG, agentic iteration, KG construction (LightRAG) |
| 19 | [Web, Real-time & Multimodal](19_web_realtime_multimodal.md) | Web search APIs (Tavily/Exa/Perplexity), CDC ingestion, multimodal conversational, long-context-as-cache |
| 20 | [Production Engineering](20_production_engineering.md) | Self-hosted infra (vLLM, K8s), FinOps for RAG, advanced caching, ops maturity ladder |
| 21 | [Benchmarks, Tokenization & Trade Studies](21_benchmarks_tokenization_trades.md) | Benchmark zoo by use case, Unicode pitfalls, RAG vs fine-tuning decision framework |
| 22 | [GraphRAG Deep Dive](22_graphrag_deep_dive.md) | Microsoft GraphRAG full pipeline + worked example, HippoRAG/2, PathRAG, OG-RAG, HyKGE, GraphReader, MedGraphRAG, hybrid Vector+Graph routing, cost calculator, healthcare case study |

## Companion files

- [`FACTS.md`](FACTS.md) — atomic, citable facts (numbers, model names, benchmark scores). Single source of truth, updated whenever something stale gets caught.
- [`quizzes/`](quizzes/) — per-module questions. Use to test recall after reading; we'll also do a live oral quiz separately.
- [`references/`](references/) — downloaded papers and archived blog posts where licensing allows.

## How to use this

1. Read modules in order **1 → 9**, or jump to module 6 if you want the deepest reranking material first.
2. Each module ends with a "Sanity check" — 3-5 questions you should be able to answer in your head before moving on.
3. After finishing a module, take its quiz cold (no peeking).
4. Cross-reference FACTS.md anytime you want a number or citation.

## Scope notes

- **Cutoff:** content reflects 2025–early 2026 state of the art. Reranker leaderboards in particular shift quarterly — check FACTS.md → "Last verified" dates.
- **Bias toward RAG-for-LLMs:** classical IR (TREC, learning-to-rank for web search) is referenced but not the focus.
- **Code:** intentionally minimal. The teaching goal is mental models, not copy-paste recipes.
