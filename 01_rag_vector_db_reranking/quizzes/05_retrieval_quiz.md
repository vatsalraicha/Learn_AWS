# Quiz — Module 5 (Retrieval Strategies)

## Recall

1. Write the RRF score formula. What's the typical value of `k`?
2. What does HyDE stand for, and what's the core idea in one sentence?
3. Name three query-transformation techniques besides HyDE.
4. What does BM25 reward, and what does it penalize?

## Apply

5. Your retriever fails on queries containing rare error codes (TS-999, ERR-4421). What's the cheapest fix?
6. You're building RAG with a 1.5s end-to-end latency budget. You're considering multi-query (4 rewrites) plus HyDE. Which fits the budget, and what's the math?
7. A query is "Show me Python papers from 2023 about LLMs." Describe the self-querying transformation.

## Diagnose

8. RRF is producing strange rankings — short BM25 list dominates the fusion. What's likely wrong?
9. After adding HyDE to a domain-tuned RAG system, recall *dropped*. Hypothesis?

## Defend

10. "Just use a stronger embedder; you don't need hybrid." Argue against this in 2-3 sentences.
11. Multi-query and HyDE both diversify retrieval. Why are they NOT redundant?

---

## Answer key

<details>
<summary>Click to reveal</summary>

1. `RRF_score(d) = Σ_i 1 / (k + rank_i(d))`. Default k = 60.
2. **H**ypothetical **D**ocument **E**mbeddings. Have an LLM write a hypothetical answer to the query, embed THAT, and retrieve real documents similar to the hypothetical — converts query-to-doc retrieval into doc-to-doc retrieval.
3. Multi-query / RAG-Fusion (generate query rewrites, fuse with RRF). Step-back prompting (generate a more abstract query, retrieve for both). Self-querying (extract metadata filters from natural language). Sub-question decomposition.
4. BM25 rewards term frequency in the document and inverse document frequency (rare terms count more). Penalizes very long docs via length normalization.
5. **Hybrid: add BM25 alongside dense, fuse with RRF.** Sparse retrieval handles literal-token matching; embeddings often whiff on novel codes the model has never seen.
6. Multi-query 4 rewrites: rewrite generation ~300ms, then 4 parallel hybrid retrievals ~30ms. Reranker ~200ms, LLM ~800ms. Total ~1.3s — fits. Adding HyDE would add another ~500ms (LLM call to generate hypothetical doc), pushing total to ~1.8s — over budget.
7. LLM extracts: `filters: {language: "Python", year: 2023}`, `semantic_query: "papers about LLMs"`. Run filtered semantic search.
8. RRF treats every retriever as equal; if BM25 returns 5 results and dense returns 50, the BM25 ones get high "rank advantage" because they're at low rank numbers and dense's tail at high rank gets `1/(60+50)` ≈ low contribution. Use **weighted RRF**, or normalize the lists' lengths.
9. Domain-tuned embedder + general-purpose LLM = the LLM's hypothetical doc is *less* similar to your domain corpus than the user's actual query. HyDE helps when query/doc style mismatch is large; it can hurt when retrieval is already strong.
10. (a) No embedder yet handles exact-match (codes, jargon, OOV terms) as well as BM25. (b) Hybrid is nearly free with RRF — no normalization complexity. (c) Empirically hybrid pulls recall@10 from ~70s to ~91% on standard benchmarks.
11. Multi-query generates *paraphrases of the question*. HyDE generates *hypothetical answers*. Different surface forms — paraphrases ≈ question-shaped, hypotheses ≈ answer-shaped. They retrieve different chunks because they sit on different sides of the query/doc distribution gap.

</details>
