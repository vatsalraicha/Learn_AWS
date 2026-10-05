# Quiz — Module 3 (Vector Databases)

## Recall

1. What does ANN stand for, and why don't we just use exact nearest neighbor?
2. Name the four main ANN algorithm families.
3. What are the three HNSW tuning parameters?
4. What does Product Quantization (PQ) buy you?

## Apply

5. You have 1B vectors and 64GB of RAM. Why is HNSW alone risky? What two alternatives would you evaluate?
6. Your queries are heavily filter-driven (per-tenant, narrow time ranges). Which index family typically handles this well, and why?
7. You're already running Postgres for application data and you have 30M chunks. Defend choosing pgvector over Qdrant.

## Diagnose

8. After enabling tight metadata filters, your HNSW p99 latency went from 15ms to 800ms. What's the likely cause?
9. Your embedder is cosine-trained but the vector DB is configured for L2. What's the failure mode? (Not "broken" — subtler.)

## Defend

10. Argue why "Pinecone vs Qdrant vs Weaviate" is the wrong framing for choosing a vector DB.
11. When does a separate vector DB stop being worth it, and you should just stay on pgvector?

---

## Answer key

<details>
<summary>Click to reveal</summary>

1. Approximate Nearest Neighbor. Exact NN is O(N) per query — at 100M vectors × 1024 dim, that's 100B float multiplications per query, infeasible at production latency.
2. **Graph-based** (HNSW), **Inverted-file** (IVF / IVF-PQ), **Disk-based** (DiskANN), **Tree/hashing** (ScaNN, Annoy).
3. `M` (graph degree per node), `ef_construction` (build-time beam), `ef_search` (query-time beam).
4. Memory compression — split each vector into M sub-vectors and quantize each to 1 of 256 codebook entries. Typical 32× compression. Loses some accuracy.
5. HNSW needs the whole graph in RAM; 1B × 1024-dim float32 ≈ 4TB just for vectors. Alternatives: **DiskANN** (compressed in RAM, full on SSD) or **IVF-PQ** (centroid index + PQ-compressed vectors, much smaller RAM footprint).
6. **IVF / IVF-PQ.** The centroid pre-filter cooperates with metadata filters — narrow to relevant clusters, apply filter, search. Graph-based indexes (HNSW) often degrade under heavy filtering because the graph assumes intact connectivity.
7. (a) One fewer system to operate. (b) Transactions across application data and vectors. (c) pgvector v0.9 + IVF_RaBitQ within ~10% of dedicated DBs at 30M scale. (d) Saves the cost of a separate managed service. (e) Backups, replication, monitoring already solved.
8. Pre-filter killed the HNSW graph's connectivity assumption — pruned subgraph forces near-brute-force traversal in the surviving subset. Fix: filter-aware HNSW (Qdrant, Weaviate ACORN), or use IVF.
9. The DB still returns *some* answer — the rankings will be similar but not optimal. Quality silently regresses; metrics drift but don't error. The bug hides because it doesn't crash.
10. The vendor is rarely the bottleneck for quality. Index algorithm, embedder choice, chunking strategy, hybrid + reranker drive 90% of quality. Vendor choice is mostly an operational decision (managed vs self-host, ops cost, ecosystem fit). Don't let benchmark differences of 2ms drive you when your reranker takes 200ms.
11. Roughly: when you're at < 50M vectors, English-only, no extreme filter selectivity, and your team already runs Postgres. Above ~100M or when you need very high concurrency / very low p99 / native hybrid features pgvector hasn't caught up on, dedicated DBs start earning their keep.

</details>
