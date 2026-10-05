# Quiz — Module 19 (Web, Real-time & Multimodal)

## Recall

1. Three web-search APIs and their primary differentiation.
2. CDC vs nightly batch — at what latency target does CDC become essential?
3. LiveVectorLake's chunk-level CDC reduces re-embed work to roughly what %?
4. The "long context as cache" pattern — what corpus size cutoff and TTL constraint?

## Apply

5. You need a web-search API for a product where every query must complete in 800ms. Pick one and justify.
6. Your corpus updates every 15 minutes. Outline an architecture that doesn't fall back to nightly batch.
7. A user uploads a screenshot mid-conversation and asks "what does this mean?" Outline the multimodal-RAG handling.

## Diagnose

8. After enabling Tavily web search, your bills tripled. Three optimizations.
9. A real-time CDC pipeline keeps falling behind during peak hours. Two architectural fixes.

## Defend

10. Argue why "long context as cache" beats RAG for some real workloads.
11. Defend why most production RAG systems should still build CDC-style ingestion even if their corpus doesn't update minute-by-minute today.

---

## Answer key

<details>
<summary>Click to reveal</summary>

1. **Tavily** — RAG-quality, factual verification; **Exa** — semantic / research queries; **Perplexity** — fastest median latency (~358ms), returns finished answers; **Linkup** — citation grounding + entity coverage; **Serper** — volume / cost; **You.com** — multi-step reasoning.
2. Sub-hour. Below ~30 minutes, batch starts feeling stale to users. Sub-minute requirements (live tickets, market data, alerts) make CDC essential.
3. **10-15%** (vs 85-95% for standard upsert which re-embeds the entire document on any change).
4. Corpus < ~200K tokens AND 5-minute provider TTL. Anthropic's prompt caching expires after 5 minutes; Gemini context caching is similar. Frequent hits within window are needed to amortize the first-call cost.
5. **Perplexity Search API** — ~358ms median is the only published number that fits the 800ms budget after generation. (Even faster: pre-computed answers via cache for common queries; web search only on cache miss.)
6. CDC connector (Debezium / Striim) on the source DB → chunk-level diff → in-flight embedding via Striim or Confluent Flink → vector DB. SLO: chunks searchable within 60s of source write. Plus a nightly batch for catch-up / consistency check.
7. (a) VLM caption + entity extraction on the screenshot. (b) Conversation rewriter combines prior turns + image content into a self-contained query. (c) Hybrid retrieval: text index AND multimodal embedder (Gemini Embedding 2 / ColPali) on relevant doc chunks; RRF-fuse. (d) Generator gets retrieved text + image reference for grounded answer.
8. (a) Cache web-search results aggressively (semantic + exact); 30-50% hit rate cuts proportionally. (b) Function-call routing (Module 10) — only call web search when query truly needs external content; route internal-corpus queries to internal RAG. (c) Per-query budget cap on web-search calls.
9. (a) Backpressure handling: persistent queue (Kafka) so producers don't get blocked when embedder lags; scale embedder workers horizontally. (b) Chunk-level CDC instead of doc-level — drastically reduces work per change.
10. For corpora that fit in 200K tokens AND get many queries within the cache TTL window: (a) zero retrieval failure — model attends over everything. (b) Better citation quality than RAG — model can point at any span. (c) Simpler architecture — no vector DB, no reranker, no retrieval ops. (d) Cache discount makes per-query cost competitive with RAG. Common case: bot over a single product manual. RAG wins for big / changing / multi-tenant corpora.
11. (a) Future-proof — turning batch into CDC retroactively is harder than starting with CDC. (b) Operational visibility — CDC gives per-event audit trail; batch obscures what changed when. (c) Quality — even if you don't strictly need 1-minute freshness, eliminating stale answers improves user trust; "I just updated this and the bot still says the old version" is a UX killer. (d) Cost — chunk-level CDC re-processes 10-15%; nightly batch re-processes 100% — wastes embedding compute at scale. The complexity is real but pays back over the system's lifetime.

</details>
