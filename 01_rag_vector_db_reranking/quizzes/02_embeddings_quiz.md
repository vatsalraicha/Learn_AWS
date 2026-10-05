# Quiz — Module 2 (Embeddings)

## Recall

1. Define bi-encoder and cross-encoder. Which is faster? Which is more accurate?
2. What is Matryoshka Representation Learning?
3. Name the top-of-MTEB English embedder (early 2026) and one strong open-source alternative.
4. What does cosine similarity measure, geometrically?

## Apply

5. You have a corpus of 200M chunks. Embedding model X is 3072-dim, model Y is 1024-dim. Both score similarly on MTEB. Why might Y be the better choice?
6. Your embedder has a 512-token context limit. Your chunks are 800 tokens average. What goes wrong, and what's the fix?
7. You're building RAG over a corpus heavy in error codes (TS-999, ERR-4421). Pure dense embeddings retrieve poorly. Two paths: (a) fine-tune embeddings, (b) add BM25 hybrid. Which is cheaper and almost certainly fixes most of the gap?

## Diagnose

8. Your retrieval recall@10 is 60% on a domain corpus, but the same embedder hits 80% on MTEB benchmarks. What might be wrong?
9. After upgrading from voyage-3 to voyage-4, retrieval quality *dropped*. Most likely cause?

## Defend

10. "MTEB average score is the right way to pick an embedding model." Argue against this in two sentences.
11. Why is hard-negative mining the most important variable in embedder fine-tuning, more than dataset size?

---

## Answer key

<details>
<summary>Click to reveal</summary>

1. **Bi-encoder:** encodes query and doc independently into vectors; compare with cosine. Fast (precompute doc vectors offline). **Cross-encoder:** encodes (query, doc) pair jointly through a transformer; outputs scalar relevance. Slow (must run model per pair). Cross-encoder is more accurate per pair; bi-encoder is the only feasible *retriever* over millions of docs.
2. A training technique where the first N dims of the output vector are themselves a good embedding. Lets you truncate at query/serve time without retraining. Adopted as industry standard ~2024-2026.
3. Top: Google **Gemini Embedding 001** (~68.32 avg). Open-source: **Qwen3-Embedding** (Apache 2.0, ~70.6 retrieval slice) or **BGE-M3** (multilingual, dense+sparse+multivector in one).
4. Cosine of the angle between two vectors in high-dimensional space. Scale-invariant; only direction matters.
5. 200M × 3072 × 4 bytes ≈ 2.4 TB; 200M × 1024 × 4 bytes ≈ 800 GB. Storage and search latency scale with dimension; smaller wins big at scale if quality is comparable.
6. Silent truncation — model only sees the first 512 tokens of each chunk; the second half is unembedded. Fix: smaller chunks (400 tokens), or different embedder with larger context.
7. **(b) BM25 hybrid** is far cheaper. BM25 nails literal-token matches that embeddings miss. Almost always closes most of the gap before fine-tuning is needed.
8. Domain-vocabulary mismatch (drug names, internal codes, legal jargon embed poorly), or distribution mismatch (queries phrased differently from documents). MTEB is generic, your domain is not.
9. The vectors in the index are still in voyage-3's space. You need to re-embed the corpus with voyage-4 before the new model performs.
10. (a) MTEB average mixes 8 task families; the retrieval sub-score may not match the average, and only retrieval matters for RAG. (b) Your domain isn't represented in MTEB; the model that wins on Reddit may lose on legal contracts.
11. Random negatives are obviously wrong; the model learns to push trivially separated examples apart, which doesn't transfer. Hard negatives — docs that look relevant but aren't — teach the model the boundary that actually matters in production. A small number of hard negatives outperforms a huge number of random ones.

</details>
