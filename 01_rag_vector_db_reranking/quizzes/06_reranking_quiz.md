# Quiz — Module 6 (Reranking)

> Deepest module — most questions.

## Recall

1. Why does RAG use a retriever-then-reranker architecture instead of one or the other?
2. Name the five families of reranker.
3. What is MaxSim in the context of ColBERT?
4. What does "listwise" reranking mean?
5. Name three production-grade cross-encoder rerankers (early 2026).
6. What's the typical λ value when starting MMR?

## Apply

7. You have a 200ms end-to-end latency budget for retrieval + rerank. Which reranker family fits?
8. Your top-10 results are full of near-duplicate chunks (same fact appearing in different documents). Which technique fixes this — and where in the pipeline does it sit?
9. You're building RAG over a corpus of scanned PDFs (slides, financial filings, screenshots). OCR is unreliable. What reranker family would you investigate?
10. You want to fine-tune a reranker on 5000 query/doc pairs from your logs. What's the most important data-quality variable, and why?

## Diagnose

11. After enabling Cohere Rerank v4 on a strong existing pipeline, quality dropped on some queries. What's a plausible cause?
12. Your team set top-k=5 from the retriever and reranks the 5. The reranker isn't moving the needle. Why?

## Defend

13. "Parameter count = quality" — argue against this for rerankers. Cite a specific 2026 example.
14. Multi-stage rerank (cheap → expensive) seems like over-engineering. Defend it on cost-quality grounds.
15. LLM-as-reranker (RankGPT-style) is more accurate than cross-encoder rerankers. Why is it not the production default?

---

## Answer key

<details>
<summary>Click to reveal</summary>

1. Bi-encoder retrieval is fast but lossy; cross-encoder rerank is accurate but slow. The two-stage architecture exploits both — bi-encoder finds candidates over millions; cross-encoder picks the best from a few hundred. Neither alone meets both quality and latency.
2. **Cross-encoder**, **late interaction (ColBERT family)**, **LLM-as-reranker**, **MMR (diversity)**, **classical learning-to-rank (LTR/GBDT)**.
3. For each query token, compute its similarity to every doc token; take the maximum (MaxSim). Sum over query tokens to get the document score. The "late interaction" mechanism.
4. The reranker sees the entire candidate list at once and emits a ranked permutation, rather than scoring docs in isolation (pointwise) or in pairs (pairwise).
5. Any three of: Cohere Rerank v4 Pro, Voyage Rerank-2.5, Jina Reranker v3, mxbai-rerank-large-v2, BGE-reranker-v2-m3, gte-reranker-modernbert-base, nemotron-rerank-1b. (Zerank-2 also acceptable.)
6. λ = 0.5-0.7 typically (relevance-leaning). λ=0 = pure relevance, λ=1 = pure diversity.
7. **Cross-encoder family** (Cohere/Voyage/Jina/mxbai) — typical 50-300ms. LLM-as-reranker won't fit; MMR alone isn't a quality reranker.
8. **MMR (Maximal Marginal Relevance)**. Sits AFTER the cross-encoder reranker — re-orders the top-N for diversity, λ around 0.7. The cross-encoder picks quality; MMR removes redundancy.
9. **Late interaction over image patches — ColPali / ColQwen.** Treat pages as images, skip OCR entirely, embed patches with late interaction.
10. **Hard negatives.** A reranker fine-tuned on (query, relevant_doc, *hard negative that the current retriever surfaces but is wrong*) learns the boundary that actually matters in production. Random or easy negatives barely move the needle.
11. The hosted reranker may be prompt-tuned for general English; if your domain has heavy jargon or your existing reranker was domain-tuned, the swap regresses on those niches. Fix: A/B on representative queries, or fine-tune the new model.
12. Reranker only helps when there's signal to extract. With only 5 candidates from the retriever, there isn't much to reorder. Pull top-50 from the retriever, then reranker has space to discriminate.
13. `gte-reranker-modernbert-base` is 149M parameters and matches the 1.2B `nemotron-rerank-1b` on Hit@1. Bottleneck is data and training recipe, not parameter count.
14. Cheap reranker on top-200→top-30 (cost low even at high candidate count). Expensive reranker (Cohere v4 Pro listwise / RankGPT) only on the 30 that survived. You pay the expensive cost on the candidates that matter, get the quality, avoid the bill of running expensive reranker on full top-200.
15. (a) Latency — RankGPT runs 1.5-3s per query. (b) Cost — $30-100 per 1K queries vs $1-2 for Cohere/Voyage. (c) Inconsistency — generation isn't deterministic; ranking can shift. Cross-encoders are 90% of the quality at <10% of the cost and latency.

</details>
