# Module 27 — Vector Capabilities Decision Framework

> **What this is:** the decision matrix for "which AWS service stores my vectors for RAG?" Aurora pgvector, RDS pgvector, DocumentDB vector, MemoryDB vector, OpenSearch k-NN, Neptune Analytics. Plus Bedrock Knowledge Bases backends.

---

## 1. The options

| Service | Index types | Max dims | Latency | Throughput | Bedrock KB native? |
|---|---|---|---|---|---|
| **Aurora pgvector** | HNSW, IVFFlat | 16,000 | ms | Mid | Yes |
| **RDS Postgres pgvector** | HNSW, IVFFlat | 16,000 | ms | Mid | Yes |
| **DocumentDB vector** | HNSW, IVFFlat | 2,000 | ms | Mid | Yes |
| **MemoryDB vector** | HNSW | 1,000 | **sub-ms** | High | No (use OpenSearch) |
| **OpenSearch k-NN (FAISS HNSW)** | HNSW, IVF | 16,000 | ms | High | **Yes (default)** |
| **OpenSearch Serverless** | HNSW | 16,000 | ms | Auto-scale | Yes |
| **Neptune Analytics vectors** | Graph-aware | 16,000 | ms | Mid | Yes |
| **S3 Vectors** (new 2024) | HNSW | varies | varies | low cost | Some |

## 2. The decision tree

```
Need sub-millisecond latency for real-time agent context?
    → MemoryDB vector

Already running OpenSearch for hybrid BM25+vector search?
    → OpenSearch k-NN (FAISS HNSW)

Already running Aurora Postgres for OLTP, and dataset < 100M vectors?
    → Aurora pgvector (same DB, no new service)

Bedrock Knowledge Bases user wanting the simplest path?
    → OpenSearch Serverless (Bedrock KB's default)

Need graph-aware vector retrieval (GraphRAG)?
    → Neptune Analytics

MongoDB-API-compatible document store with vectors?
    → DocumentDB vector

Massive scale (billions of vectors), willing to trade latency for cost?
    → S3 Vectors (or OpenSearch Service with IVF)
```

## 3. Bedrock Knowledge Bases native backends

Bedrock KB natively connects to:
- **OpenSearch Serverless** (default)
- **Aurora pgvector**
- **Pinecone** (third-party)
- **Redis Enterprise** (third-party)
- **MongoDB Atlas** (third-party)
- **Neptune Analytics** (2024)

For Capital One: **OpenSearch Serverless + Aurora pgvector** are the two AWS-native paths Bedrock KB integrates with cleanly.

## 4. Cost shapes

- **Aurora pgvector** — already paying for Aurora; vectors add storage + IOPS.
- **RDS pgvector** — same as Aurora but smaller scale.
- **DocumentDB vector** — instance-based; vector index lives in cluster.
- **MemoryDB vector** — premium ($/hr × instance count); justified for sub-ms latency only.
- **OpenSearch Service** — per-instance; sized by RAM (HNSW memory-heavy).
- **OpenSearch Serverless** — OCU floor of 2 (~$700/mo for dev).
- **Neptune Analytics** — per-NCU; in-memory analytical workloads.

## 5. Multi-tenant patterns

For SaaS use cases with vector data per tenant:

- **Namespace** in OpenSearch (one index per tenant or shared index with `tenant_id` filter).
- **Schema-per-tenant** in Aurora pgvector.
- **Cluster-per-tenant** in DocumentDB/MemoryDB (heavyweight).

## 6. The "two-tier" pattern (Capital One likely)

```
OpenSearch Serverless     —— hybrid BM25 + vector for policy/regulatory RAG
    ↓ (slower, recall-focused)

MemoryDB vector           —— sub-millisecond agent context retrieval
    ↑ (fast, latency-focused)
```

Tier 1 (OpenSearch) returns top candidates from a large corpus; tier 2 (MemoryDB) caches hot tenant context for in-flight agent calls.

## 7. When to pick which (cheat sheet)

| Workload | Pick |
|---|---|
| New RAG with Bedrock | **OpenSearch Serverless** (Bedrock default) |
| Existing Aurora OLTP + vectors | **Aurora pgvector** |
| Sub-millisecond agent context | **MemoryDB vector** |
| MongoDB-compatible + vector | **DocumentDB vector** |
| Graph + vector (GraphRAG) | **Neptune Analytics** |
| Massive cold vector store | **S3 Vectors** |
| Hybrid lexical + semantic search | **OpenSearch k-NN with hybrid query** |

## 8. Pitfalls

- **Adding a new DB just for vectors** when your existing OLTP could handle it (pgvector).
- **MemoryDB for cold vectors** — way overpriced.
- **HNSW without enough RAM** — index spills, performance collapses.
- **Forgetting Bedrock KB ingestion costs** — embedding generation per chunk.

## 9. Capital One lens

Two-tier likely:
- **OpenSearch Serverless** for policy/regulatory document RAG (hybrid search) — paired with Bedrock KB.
- **MemoryDB vector** for Eno / Servicing Tool agent context (sub-millisecond requirement).
- **Aurora pgvector** for workloads that already live in Aurora.

## 10. Sanity check

1. When do you pick MemoryDB vector over OpenSearch?
2. What are Bedrock Knowledge Bases' native vector backends?
3. What's the two-tier vector pattern, and why does Capital One likely use it?
4. Why is HNSW memory-heavy, and what's the failure mode?
5. When does Aurora pgvector beat a dedicated vector DB?

## 11. Cross-references

- **Topic 01 Module 22** — GraphRAG deep dive
- **Modules 17, 19, 21, 25, 26** — the individual database modules
- **Module 42** — Bedrock Knowledge Bases

## Primary sources

- [`Bedrock_Knowledge_Bases.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/Bedrock_Knowledge_Bases.html)
- [`MemoryDB_Vector.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/MemoryDB_Vector.html)
- [`Aurora_pgvector.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/Aurora_pgvector.html)
- Research report: [`06c_analytical_vector_graph.md`](../../research_inputs/04_aws_for_ai_ml/06c_analytical_vector_graph.md)
