# Quiz — Module 1 (Foundations)

## Recall

1. What does "RAG" stand for, and which 2020 paper introduced the term?
2. Name the four "defects of parametric knowledge in LLMs" that RAG addresses.
3. Name the three failure modes in the "RAG triad."
4. List four situations where RAG is the *wrong* tool.

## Apply

5. You're building a chatbot for a 30-page handbook. Which of {RAG, long context, fine-tuning} would you start with and why?
6. Your RAG product has a 100ms end-to-end latency budget. What does this constraint imply about your architecture?
7. Indexing is done offline; querying is done online. Why does this asymmetry matter for engineering tradeoffs?

## Diagnose

8. Users complain answers are confidently wrong. The retriever returns the right chunks. Which failure mode in the triad is this?
9. Faithfulness is high but answers are off-topic. Which failure mode?

## Defend

10. Argue why "ada-002 + cosine top-5 + stuff into prompt" is *insufficient* for production. Give three concrete failure modes a more modern pipeline addresses.

---

## Answer key

<details>
<summary>Click to reveal</summary>

1. Retrieval-Augmented Generation. Lewis et al., 2020 ("Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks", arXiv:2005.11401), Facebook AI.
2. **Frozen** (knowledge cutoff), **Lossy** (compression), **Ungrounded** (no citations), **Bounded** (can't memorize whole corpus).
3. **Context relevance** (wrong/missing chunks), **Faithfulness** (answer contradicts context), **Answer relevance** (answer doesn't address question).
4. The model already knows. The corpus fits in context. You need behavior (not knowledge) change. The query is reasoning-heavy. Sub-100ms latency target. Highly relational data needing graph traversal.
5. **Long context.** 30 pages fits in any modern model's context. RAG over it is over-engineering with no quality benefit.
6. With 100ms budget, full RAG (embed + search + rerank + LLM) is infeasible. Options: precomputed FAQ index, no reranker, very small generator, semantic cache as primary.
7. Indexing-time costs amortize over many queries — you can afford expensive operations (LLM-generated context, semantic chunking). Query-time mistakes hit every user; latency and cost compound.
8. **Faithfulness fail** — the model isn't using the context faithfully.
9. **Answer relevance fail** — the answer doesn't address the question, even though it's grounded.
10. Three concrete things that fail: (a) Naïve fixed-size chunking destroys context across boundaries; modern: structure-aware + contextual retrieval. (b) Pure dense fails on exact-match (codes, IDs, jargon); modern: hybrid + RRF. (c) Top-5 cosine returns near-duplicate or marginally-relevant chunks; modern: rerank with cross-encoder, MMR-diversify. Other valid: no eval loop, no caching, hallucination on retrieval-misses (no Self-RAG/CRAG-style refusal).

</details>
