# Quiz — Module 13: Mosaic AI Vector Search & RAG on Databricks

## Recall

**Q1.** What's the difference between a Standard and Storage-optimized Vector Search endpoint?

<details><summary>Answer</summary>

- **Standard** — in-memory, full precision, **tens-of-ms latency**. Caps around **320M vectors**.
- **Storage-optimized** — compressed, **~250ms latency**, billion-scale (~1B vectors at 768-dim), **~7× cheaper per vector.**

**Pick Standard when** — latency sensitivity is high (chat apps), corpus fits under ~320M vectors, cost isn't the dominant constraint.

**Pick Storage-optimized when** — corpus is 100M+ vectors, latency tolerance is hundreds of ms, cost matters (e.g., 50M+ chunk healthcare corpora).
</details>

**Q2.** What's the difference between Delta Sync and Direct Access indexes, and what are the two pipeline types for Delta Sync?

<details><summary>Answer</summary>

- **Delta Sync indexes** — source Delta table → vector index, automatic incremental sync via Change Data Feed. **The killer feature.** You manage your data in Delta; the index follows.
- **Direct Access indexes** — caller-managed; you upsert vectors via API. For when you need full control of the indexing pipeline (e.g., custom embedding pipelines that don't flow through Delta).

Pipeline types for Delta Sync:
- **`TRIGGERED`** — manual sync (e.g., nightly). Cheaper. Recommended for stable corpora.
- **`CONTINUOUS`** — Delta CDF tails the source; ~minutes lag. More expensive. Recommended for active-add corpora.
</details>

---

## Apply

**Q3.** Set up a Delta Sync index for clinical notes with hybrid search support and member-level filter capability.

<details><summary>Answer</summary>

```python
from databricks.vector_search.client import VectorSearchClient

vsc = VectorSearchClient()

# 1. Create the source Silver table with embeddings
spark.sql("""
CREATE TABLE clinical.silver.note_chunks_with_embeddings (
  chunk_id        STRING NOT NULL,
  member_id       STRING,
  encounter_id    STRING,
  source_doc      STRING,
  text            STRING,
  embedding       ARRAY<FLOAT>,        -- 1024-dim BGE-large
  ingestion_ts    TIMESTAMP,
  PRIMARY KEY (chunk_id)
)
USING DELTA
CLUSTER BY (member_id)                  -- for filter speed
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true' -- needed for Delta Sync
)
""")

# 2. Compute embeddings (one-time backfill via ai_query)
spark.sql("""
INSERT INTO clinical.silver.note_chunks_with_embeddings
SELECT 
  chunk_id, member_id, encounter_id, source_doc, text,
  ai_query('databricks-bge-large-en', concat(text)) AS embedding,
  current_timestamp() AS ingestion_ts
FROM clinical.silver.note_chunks
""")

# 3. Create the Delta Sync index
vsc.create_delta_sync_index(
    endpoint_name="prod_clinical_vs",
    source_table_name="clinical.silver.note_chunks_with_embeddings",
    index_name="clinical.indexes.notes_v1",
    pipeline_type="TRIGGERED",  # nightly sync
    primary_key="chunk_id",
    embedding_dimension=1024,
    embedding_vector_column="embedding",
    columns_to_sync=[
        "chunk_id", "text", "member_id", "encounter_id", "source_doc"
    ]
)

# 4. Hybrid query at retrieval time
results = vsc.get_index("prod_clinical_vs", "clinical.indexes.notes_v1").similarity_search(
    query_text="shortness of breath chest pain",
    columns=["chunk_id", "text", "member_id", "encounter_id"],
    num_results=10,
    query_type="HYBRID",   # BM25 + ANN with RRF
    filters={"member_id": ["MBR-12345"]}  # member-level filter
)
```

**Discipline notes:**
- **CDF on the source** is required for Delta Sync.
- **Cluster by `member_id`** for filter performance.
- **`columns_to_sync`** — explicitly list what the agent will need; reduces index size and lookup time.
- **TRIGGERED + nightly** — cheaper; if real-time freshness matters, switch to CONTINUOUS but accept the cost.
- **HIPAA discipline:** the index lives in UC managed encrypted storage (managed-services CMK applies). Members must have explicit grants on the source table for the agent (running as their identity) to retrieve their data.
</details>

---

## Diagnose

**Q4.** A team's RAG agent latency is 8 seconds per query at 95th percentile. The Vector Search lookup is supposedly 200ms. Where's the time going, and what would you check?

<details><summary>Answer</summary>

8 seconds total when Vector Search is 200ms means **>96% of the latency is elsewhere.** Common contributors:

1. **LLM generation** — the dominant cost in most RAG systems. A Llama 3.3 70B generation of 500 output tokens at ~30 tok/s is ~15 seconds. Even Claude Sonnet at 50 tok/s is 10 seconds for 500 tokens.
   - **Fix:** check what model is being used; switch to a smaller model (Haiku, Llama 3.1 8B); reduce output length; use streaming UI to mask the wait.

2. **Cold start on Model Serving** — if the endpoint scales to zero, the first query after idle takes 10–20s+ (Module 14 covers).
   - **Fix:** keep min concurrency > 0 for prod paths; accept warmup cost.

3. **Multiple LLM calls in the agent** — if the agent does retrieve → rerank (LLM) → generate, that's 2–3 LLM calls in series.
   - **Fix:** look at the MLflow trace; if rerank is unnecessary, drop it; if rerank is needed, use a smaller model for rerank than for generation.

4. **Tool calls / external API calls** — if the agent calls an external service (FHIR API, claim status lookup), that latency adds up.
   - **Fix:** parallelize tool calls where possible; cache repeated lookups.

5. **Embedding the query** — if the agent embeds the query at runtime via FMAPI, that's ~100-300ms typically.
   - **Fix:** usually negligible compared to generation; not the lever.

6. **Prompt construction overhead** — large context (10K+ retrieved chunks) costs both compute and prompt-processing time.
   - **Fix:** retrieve fewer chunks; rerank to top-N; truncate context.

**The diagnostic loop:**
1. Open the MLflow trace UI for a slow request.
2. Look at the trace tree — which span is slowest?
3. Drill into the slowest span; verify it matches your hypothesis.
4. Fix the slowest contributor first.

**MLflow 3 makes this trivial** — autolog captures spans for every nested call. Without MLflow tracing, this debug loop would take hours of `print()` debugging.
</details>

---

## Defend

**Q5.** A peer says "we should use Pinecone for our healthcare RAG — it's the industry standard and faster than Mosaic." Defend or refute for an Optum context.

<details><summary>Answer</summary>

**Refute, with calibration.**

Where the peer is right:
- **Pinecone is faster on raw query latency** at billion-scale and very high QPS. For consumer-grade chat apps with sub-100ms latency budgets, Pinecone is competitive.
- **Pinecone has multi-cloud availability** — useful for shops not committed to one cloud.

Where the peer is wrong for Optum healthcare:
- **PHI data movement is the architecture-blocker.** Pinecone hosts your vectors on Pinecone infrastructure (Enterprise tier offers self-host but at high cost and operational overhead). Sending PHI embeddings (which can be reverse-engineered toward source content with the right adversary — Vec2Text and similar attacks) to a third-party SaaS requires a Pinecone BAA on top of Databricks BAA on top of Azure BAA. Three-way BAA stacks make procurement reluctant.

- **No automatic Delta Sync.** With Pinecone, you build and maintain a re-embedding pipeline; with Mosaic, the source Delta updates and the index follows automatically. For an Optum-scale platform team, this is non-trivial operational savings.

- **No UC ACL enforcement.** Mosaic's filters can use UC group memberships at retrieval time; Pinecone has its own access control that doesn't integrate with UC. You'd duplicate the access model.

- **Mosaic's hybrid search BM25 + ANN with RRF is purpose-built for medical codes** (ICD-10, CPT, SNOMED, NDC) — keyword index trained on your data. Pinecone's hybrid is sparse + dense but the sparse side requires you to provide sparse vectors, not raw text.

- **Latency isn't the bottleneck for healthcare RAG anyway.** As Q4 showed, LLM generation dominates the 8-second p95. Saving 100ms on retrieval is invisible to the user.

**The architect's pitch:**
- **For healthcare RAG on Databricks: Mosaic Vector Search is the right default.** Data gravity (PHI in Delta) + UC governance + Delta Sync + hybrid search for medical codes + BAA simplicity.
- **Use Pinecone selectively** for non-PHI workloads where Pinecone's specific features matter (very high QPS, multi-cloud requirement).
- **Don't fight the data gravity.** Optum's data is going to be in the lakehouse anyway; using a vector DB that lives next to that data is operationally cheaper.

**The "industry standard" framing is the tell** — Pinecone is the most-named vector DB by AI startups, but enterprise healthcare doesn't share that distribution. The right answer is shaped by your data location and governance posture, not by social proof.

**Sources:** [Mosaic Vector Search docs](https://learn.microsoft.com/en-us/azure/databricks/vector-search/vector-search), [Vec2Text attack](https://arxiv.org/abs/2310.06816) (relevant to the BAA argument).
</details>
