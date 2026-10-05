# Module 13 — Mosaic AI Vector Search & RAG on Databricks

> **Goal of this module:** know how Vector Search differs from Pinecone / Azure AI Search / Qdrant for healthcare RAG, when its scale limits hurt, the canonical RAG-on-Databricks reference architecture, and the healthcare-specific use cases (ICD-10 / CPT / SNOMED) where hybrid search wins.
>
> **Assumes:** you understand RAG fundamentals, embeddings, hybrid retrieval, reranking from Topic 01. This module is about how Databricks-native Vector Search specifically supports those patterns.

---

## What Mosaic AI Vector Search is

A **Databricks-native vector database** built on **HNSW with L2 distance** (cosine via normalized vectors). Two endpoint flavors:

- **Standard endpoint** — in-memory, full precision, tens-of-ms latency. Caps around **320M vectors**.
- **Storage-optimized endpoint** — compressed, ~250ms latency, billion-scale, **~7× cheaper per vector.** Up to ~1B vectors at 768-dim ([Decoupled design blog](https://www.databricks.com/blog/decoupled-design-billion-scale-vector-search)).

Two index types:
- **Delta Sync indexes** — source Delta table → vector index, automatic incremental sync via Change Data Feed. **The killer feature.**
- **Direct Access indexes** — caller-managed; you upsert vectors directly. For when you need full control of the indexing pipeline.

Hybrid search GA 2025: **BM25 + ANN** with Reciprocal Rank Fusion (`rrf_param=60` default). The keyword index is **trained on your data**, which matters for healthcare codes (ICD-10, CPT, SNOMED, NDC) — pure dense retrieval is bad at these.

---

## When Vector Search wins

### vs Azure AI Search

| Feature | Mosaic Vector Search | Azure AI Search |
|---|---|---|
| Auto-sync from source | **Delta only (great if on lakehouse)** | Manual / indexer |
| Hybrid search | Yes (RRF) | Yes (semantic ranker) |
| Multi-tenant filters | Yes | Yes |
| Latency at scale | 10–250ms | 10–50ms |
| HIPAA BAA | Yes (with CSP workspace) | Yes |
| Lock-in | Hard (Delta) | Medium |

### vs Pinecone

- **Pinecone** wins on extreme-scale serverless query latency and multi-cloud availability
- **Mosaic** wins on no extra vendor, UC ACLs, automatic Delta sync, no extra data movement (PHI stays in lakehouse)

### vs Qdrant on Databricks

- **Qdrant** is OSS, self-host, lower lock-in, full control
- **Mosaic** is managed; you don't run the index infrastructure

### Architect take

**If your golden source is already in Delta + UC, Mosaic Vector Search is the lowest-friction option.** The Delta Sync semantics alone justify it — every other vector DB requires a re-embedding pipeline you have to maintain.

**If you have data in SQL Server / Cosmos / S3 not yet on the lakehouse, Azure AI Search is more pragmatic** — it has connectors to those sources you'd otherwise rebuild.

**Don't fight the data gravity.** For Optum-scale, where most data is heading toward the lakehouse anyway, Mosaic is the right default for new RAG deployments.

---

## Performance honest numbers

- **Beyond 2M (standard) or 64M (storage-opt) vectors per unit**, latency rises and QPS plateaus around **30 QPS**.
- **Index creation is famously slow** — community thread complaints from 2024 still relevant. Plan for **hours, not minutes**, on first build of 10M+ corpora.
- **Cost** — pricing per "vector search unit," roughly 2M vectors of 768-dim per unit. For a healthcare org with ~50M PHI-bearing chunks, you're in storage-optimized territory unless you can shard by tenant or therapy area.

---

## Healthcare-specific use cases

### Clinical notes RAG

```
Provider notes (PDF / Word / EHR exports)
    ↓
UC Volume: /Volumes/clinical/raw/notes/
    ↓ Auto Loader streaming ingest
    ↓
Bronze: clinical.bronze.notes_raw (full text + metadata)
    ↓ Chunking pipeline (sentence-boundary, ~512 token chunks)
    ↓
Silver: clinical.silver.note_chunks (chunk_id, text, member_id, encounter_id, source_doc)
    ↓ Embedding via FMAPI BGE-large
    ↓
Silver: clinical.silver.note_chunks_with_embeddings
    ↓ Delta Sync → Vector Search
    ↓
Mosaic AI Vector Search index: clinical.indexes.notes_v1
    ↓
Agent retrieval node (Module 15)
```

**Discipline:**
- **Chunk on sentence boundaries**, not arbitrary tokens — clinical text has structure that arbitrary chunking destroys.
- **Preserve metadata** — `member_id`, `encounter_id`, `source_doc`, `created_at` for filtering and citation.
- **De-identify before indexing** if the consumer is a non-clinical audience (Module 22 has the FHIR de-id pipeline).
- **Hybrid BM25 + dense** because clinical notes mix prose with codes (ICD-10, CPT) — dense retrieval misses exact-code matches.

### Code-aware retrieval

```sql
-- Search ICD-10-coded claims with both keyword and semantic
SELECT 
  claim_id,
  diagnosis_code,
  diagnosis_description,
  -- Hybrid search: BM25 on the code + dense on the description
  vector_search(
    'clinical.indexes.icd10_v1',
    query_text => 'shortness of breath',
    columns => ['diagnosis_code', 'diagnosis_description'],
    num_results => 20
  ) AS results
FROM silver.claim_diagnosis;
```

**The hybrid scoring** (BM25 + ANN with RRF) is essential here — pure dense retrieval would miss exact code matches like "I50.9" (heart failure unspecified); pure BM25 would miss semantic relatives.

### Member-level filtering

```python
results = vsc.get_index("clinical.indexes.notes_v1").similarity_search(
    query_text="recent admission for chest pain",
    columns=["chunk_id", "text", "member_id", "encounter_id"],
    filters={"member_id": ["MBR-12345"]},  # filter at retrieval time
    num_results=10
)
```

Metadata filtering at query time is essential for **per-member RAG** — the agent retrieves only chunks from this member's record.

---

## The canonical RAG-on-Databricks reference architecture

```
Source docs (S3/ADLS/SharePoint/SQL)
   ↓
Lakeflow ingestion → Delta (raw)
   ↓
DLT/SDP cleansing → Delta (silver, chunked + metadata)
   ↓
ai_query (embeddings via FMAPI BGE/GTE) → Delta (vectors)
   ↓
Mosaic Vector Search index (Delta Sync, hybrid BM25+ANN)
   ↓
Agent Framework retrieval node → MLflow PyFunc agent
   ↓
Mosaic Serving endpoint behind AI Gateway
   ↓
Databricks Apps / external client
```

**UC governs every step. MLflow traces every request. Eval set in MLflow Prompt Registry.**

This is the **"RAG on Databricks" architecture diagram for any healthcare proposal.** Every component lives in UC; PHI stays in lakehouse; lineage is end-to-end.

---

## Production patterns

### Pattern: Delta Sync index for incremental updates

```python
from databricks.vector_search.client import VectorSearchClient

vsc = VectorSearchClient()

vsc.create_delta_sync_index(
    endpoint_name="prod_vs_endpoint",
    source_table_name="clinical.silver.note_chunks_with_embeddings",
    index_name="clinical.indexes.notes_v1",
    pipeline_type="TRIGGERED",  # or "CONTINUOUS"
    primary_key="chunk_id",
    embedding_dimension=1024,  # for BGE-large
    embedding_vector_column="embedding",
    columns_to_sync=["chunk_id", "text", "member_id", "encounter_id", "source_doc"]
)
```

- `TRIGGERED` — manual sync; cheaper, run nightly.
- `CONTINUOUS` — Delta CDF tails the source; ~minutes lag; more expensive.

### Pattern: hybrid search query

```python
results = vsc.get_index("clinical.indexes.notes_v1").similarity_search(
    query_text="shortness of breath chest pain emergency",
    columns=["chunk_id", "text", "member_id", "encounter_id"],
    num_results=10,
    query_type="HYBRID",  # BM25 + ANN
    filters={"encounter_date": ">= '2025-01-01'"},
)
```

The hybrid mode is the default-on switch for healthcare retrieval.

### Pattern: index rebuild for embedding model changes

Embedding model upgrades (BGE-large → BGE-large-v2) require **full re-embedding of the corpus.** Plan for it:
1. Build the new index in parallel (`notes_v2`).
2. Backfill: `ai_query` over the source Delta to compute new embeddings; write to a new Delta table; trigger Delta Sync.
3. Plan for hours of compute on ~10M+ corpora.
4. Switch the agent's index reference; deprecate the old index.

**Don't try to swap embedding models on the same index.** The vector space is incompatible.

---

## Pain points

- **Index rebuild time** — first build of 10M+ vectors can take hours; "incremental" via Delta Sync is the only sane path. Plan re-embedding strategy for model upgrades carefully — full rebuild blocks query traffic on the same endpoint at scale.
- **QPS plateau around 30 QPS per endpoint** at large scale — for high-throughput scenarios, you may need multiple endpoints or storage-optimized variant.
- **Storage-optimized endpoint cold start** — first query after idle takes seconds.
- **Filter cardinality** — high-cardinality filters (`member_id` for a 10M-member plan) work but add latency. Consider sharding by tenant or therapy area for very high-cardinality cases.
- **No native cross-region replication** — for DR, you replicate the source Delta + rebuild the index in the secondary region (Module 23).

---

## When NOT to use Vector Search

- **Source data is not in Delta / UC** — the Delta Sync magic doesn't apply; you'd build a re-embedding pipeline anyway. Azure AI Search may be more pragmatic.
- **Sub-10ms latency requirement** at high QPS — Pinecone or self-hosted Qdrant on a tuned cluster are faster.
- **You need real-time updates** with sub-second freshness — Delta Sync is incremental but has minutes of lag.
- **Billion-scale at single-digit-ms latency** — neither Mosaic nor most managed vector DBs hit this; you're in custom-infrastructure territory.

---

## Sanity check

1. What's the difference between Standard and Storage-optimized Vector Search endpoints, and when do you pick each?
2. Why is hybrid search (BM25 + ANN with RRF) essential for healthcare retrieval specifically?
3. Delta Sync indexes have two pipeline types. What are they and when do you pick each?
4. A team needs to upgrade embedding models. What's the migration path?
5. When does Azure AI Search beat Mosaic Vector Search architecturally?
6. What's the expected latency profile at 100M vectors on a Standard endpoint?

---

## Further reading

- [Mosaic AI Vector Search GA blog](https://www.databricks.com/blog/announcing-mosaic-ai-vector-search-general-availability-databricks)
- [Hybrid search GA blog](https://www.databricks.com/blog/announcing-hybrid-search-general-availability-mosaic-ai-vector-search)
- [Vector Search docs — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/vector-search/vector-search)
- [Vector Search best practices — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/vector-search/vector-search-best-practices)
- [Vector Search cost management](https://learn.microsoft.com/en-us/azure/databricks/vector-search/vector-search-cost-management)
- [Decoupled design — billion-scale Vector Search](https://www.databricks.com/blog/decoupled-design-billion-scale-vector-search)
- [Build compound AI systems faster — Mosaic AI](https://www.databricks.com/blog/build-compound-ai-systems-faster-databricks-mosaic-ai)
- [Retrieval-augmented generation on Databricks](https://docs.databricks.com/aws/en/generative-ai/retrieval-augmented-generation)
