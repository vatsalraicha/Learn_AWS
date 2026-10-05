# Quiz 02 — Data Preparation (14%, 19 Qs)

> Take cold. ~2 min per question. Maps to **Modules 03–04**.

---

## Recall

1. Name four document-extraction Python libraries and a format each is best for (PDF text, scanned image, HTML, web crawl).
2. What Delta table property must be enabled for a Vector Search Delta Sync index to incrementally update?
3. Mosaic AI Vector Search uses which fusion algorithm to combine BM25 + ANN scores in hybrid search?
4. State the **vector cap** for a standard Vector Search endpoint and roughly the maximum supported on storage-optimized.
5. List four chunking strategies and one document type each is well-suited for.

## Apply

6. Source corpus: 50 PDFs, mostly text but some embedded tables and figures. Best extraction step on Databricks?
7. Chunks are 512 tokens. You need an embedding model optimized for cost/latency over quality. From these options, pick: (A) ctx 512, dim 384 (B) ctx 8192, dim 1024 (C) ctx 4096, dim 1536 (D) ctx 1024, dim 768.
8. You add chunks to `cat.silver.chunks` but the Delta Sync index does not show the new rows. Three things to check?
9. Sample Q1 scenario: too many chunks; reduce chunk count while keeping quality. Which two levers?
10. Corpus mixes prose with ICD-10 codes. Which `query_type` setting do you use, and why?

## Diagnose

11. The recall@K is high but precision@K is low. Best fix without changing chunking?
12. After switching the embedding model from BGE Large (dim 1024) to GTE Small (dim 384), the existing index reports schema mismatch. Why?
13. Your filter `{"member_state": "NY"}` returns zero candidates even though there are matching docs. The agent's endpoint SP has `USE_INDEX`. What's the likely cause?
14. Boilerplate footers ("Page X of Y") dominate top-K retrievals across queries. Diagnosis and fix?

## Defend

15. Argue why you'd build a BM25-only index over a hybrid one for a compliance-audit search use case.
16. Justify picking storage-optimized over standard for a 250M-vector index with nightly updates.
17. Defend keeping CDF enabled on the chunk Delta table even though storage is more expensive.

## [Multi-select]

18. **[select TWO]** Required to feed a Vector Search Delta Sync index from a Delta table.
   (A) `delta.enableChangeDataFeed = true`
   (B) Primary key column declared and unique
   (C) Embedding column populated at write time
   (D) Vector dimension matches the embedding endpoint's output
   (E) Source table partitioned by date

19. **[select THREE]** When does hybrid search outperform pure ANN?
   (A) Corpus contains medical / legal codes
   (B) Pure prose with paraphrased queries
   (C) Brand names and SKUs in queries
   (D) Rare jargon the embedding model didn't see
   (E) High-volume similarity for embedding clusters

---

## Answers

1. `pypdf` / `pdfplumber` (text PDF), `pytesseract` (scanned image), `BeautifulSoup` (HTML), `Scrapy` (web crawl at scale). → Module 03
2. **`delta.enableChangeDataFeed = true`**. → Module 03, 04
3. **Reciprocal Rank Fusion (RRF)** with default `k=60`. → Module 04, 06
4. Standard: **~100M vectors**. Storage-optimized: **1B+ at dim 768**. → Modules 04, 06
5. Fixed-window (uniform docs), Recursive (default prose), Semantic (high-quality RAG), Structure-aware (Markdown wikis / FAQs). → Module 03
6. **`ai_parse_document()`** — preserves table/figure spatial metadata. Then chunk the resulting text. → Module 03
7. **(A) ctx 512, dim 384.** Match context length to chunk size; smaller dim = cheaper. Sample Q4's answer. → Module 02, 04
8. (a) Change Data Feed enabled? (b) Primary key unique? (c) Embedding endpoint healthy + dim matches? Also: index sync state via `idx.describe()`, ACLs. → Module 04
9. **Increase chunk size** and **decrease overlap.** Chunk count ≈ tokens / (size − overlap). Sample Q1. → Module 03
10. **`query_type="HYBRID"`** — BM25 finds exact code matches (I50.9); ANN finds semantic relatives ("heart failure"). RRF fuses. → Module 04, 06
11. **Add a cross-encoder reranker** that over-retrieves (top-50) and reranks to top-5. → Module 04
12. Embedding dimension changed; existing index's embedding column is dim 1024. You **cannot hot-swap embedding model on an existing index** — must build a new index (blue/green). → Module 04, 06
13. **Filter cardinality issue** or the filter syntax. Vector Search applies filters **before** ANN; if zero rows match the filter, ANN has nothing to search. Check the source table for matching rows and the filter syntax (e.g., string casing). → Module 06
14. **Pre-chunk filtering not applied.** Strip boilerplate via regex/`BeautifulSoup` before chunking. Boilerplate dominates because it's semantically generic but lexically dense across many queries. → Module 03
15. Compliance audits need **exact-token matching** at huge scale (every doc that mentions term X). BM25-only on storage-opt provides this at the lowest cost per vector — no embedding compute or storage. Semantic similarity isn't the right metric for "find every mention." → Module 04, 06
16. > 100M rules out standard. Nightly updates are fine with Triggered sync. Cost is ~7× lower per vector at this scale. Hybrid + reranker still available. → Module 04
17. CDF is **required** for Delta Sync incremental updates. Without it, you'd full-refresh the index nightly — much higher compute. The storage delta is small relative to the cost of full refreshes. → Module 03, 04
18. **(A) and (B).** CDF + unique PK. (C) is optional — VS can embed for you. (D) is required only if you precompute embeddings. (E) partitioning unrelated to index requirement. → Module 03, 04
19. **(A), (C), (D).** Codes, brand names, rare jargon all benefit from BM25's exact-token matching. (B) ANN alone handles paraphrase. (E) embedding clusters are an ANN strength, not hybrid's. → Module 06
