# Module 26 — OpenSearch — Search & Vector

> **What this is:** Amazon OpenSearch Service (managed) vs OpenSearch Serverless. k-NN plugin engines (Lucene, FAISS, nmslib). HNSW vs IVF indexes. Hybrid BM25 + vector search. The post-Elasticsearch-fork story.

---

## 1. Service vs Serverless

| | **OpenSearch Service** | **OpenSearch Serverless** |
|---|---|---|
| Form | Provisioned cluster (you size nodes) | Per-capacity (OCU) auto-scaling |
| Use case | Steady-state log analytics, large indices | Vector workloads, time-series, unpredictable load |
| Capacity unit | Instance types (r6g.large, etc.) | **OCU = 6 GB RAM + 2 vCPU + 120 GB storage** |
| Dev-mode minimum | Tiny clusters | **2 OCU floor** (the cheapest viable Serverless deployment) |

## 2. The 2021 Elasticsearch fork

Elastic relicensed Elasticsearch in 2021 to a non-OSS license; AWS forked it as **OpenSearch** (Apache 2.0). Since then OpenSearch has diverged: own roadmap, different feature set in some areas (e.g., k-NN engines, alerting), strong AWS integration.

## 3. k-NN engine choices

OpenSearch's k-NN plugin supports three engines:

- **Lucene** — pure Java, in-process. Easier to manage, lower throughput.
- **FAISS** — Facebook's library; high throughput, more memory.
- **nmslib** — older; less commonly chosen for new builds.

**Index types** (for FAISS / nmslib):

- **HNSW** (Hierarchical Navigable Small World) — graph-based; high recall, ANN search.
- **IVF** (Inverted File Index) — clustering-based; better for very large datasets where memory matters.

Default choice: **HNSW on FAISS** for production.

## 4. Hybrid search (BM25 + vector)

OpenSearch supports combining **BM25** (lexical relevance) with **vector** (semantic) search results via **Reciprocal Rank Fusion (RRF)** or weighted score combination.

- BM25 catches exact-term matches that embedding similarity misses.
- Vector search catches semantic similarity that exact-term misses.
- Combined: substantially higher relevance for RAG and search workloads.

## 5. Ingestion pipelines

- **OpenSearch Ingestion** (formerly Data Prepper, managed in 2024) — managed pipelines for log, trace, metric ingestion.
- **Bulk API** for batch indexing.
- **Index templates** for schema-on-read patterns.

## 6. Security plugin

Fine-grained access control:
- Document-level security.
- Field-level security.
- Tenants (isolated workspaces).
- Integration with Cognito, SAML, IAM Identity Center.

## 7. Neural search

ML-based query rewriting: an embedding model translates a query to better matches. Reduces the "I searched for X but meant Y" problem.

## 8. OpenSearch as RAG backend

The big use case in 2024-2026:

- **Bedrock Knowledge Bases** uses OpenSearch Serverless as the default vector store.
- **Hybrid search** improves recall for noisy queries.
- **Native integration** with Bedrock for embedding generation.

## 9. OpenSearch Service vs Elastic Cloud on AWS

| | OpenSearch Service | Elastic Cloud on AWS |
|---|---|---|
| Latest features | OpenSearch roadmap (k-NN improvements, neural search, AWS integration) | Latest Elastic features (Lens, security, ML jobs) |
| AWS-native auth/encryption | Deep | Limited |
| Cost | Generally lower at scale | Premium for Elastic features |

For Capital One: OpenSearch Service is the AWS-native choice.

## 10. 2024-2026 changes

- **Serverless GA** for vector and time-series workloads (refined 2024).
- **Neural search** matured.
- **Bedrock KB integration** as the default vector backend.
- **OpenSearch 2.x** versions advanced.

## 11. Pitfalls

- **Serverless 2 OCU minimum** — ~$700/month floor for dev environments.
- **HNSW memory footprint** — vector indexes can dominate RAM; size accordingly.
- **Index rotation** in Service — managed by Index State Management policies; complex to design.
- **Hybrid search tuning** — relevance scoring needs experimentation per workload.

## 12. Capital One lens

OpenSearch is likely used for:
- **Log analytics** at scale.
- **Hybrid BM25 + vector RAG** for policy/compliance document retrieval.
- **Eno's answer retrieval** layer (combined with Bedrock for generation).

## 13. Sanity check

1. Service vs Serverless — when does each win?
2. Three k-NN engines — what's the default pick?
3. HNSW vs IVF — when does IVF matter?
4. Why does hybrid BM25+vector beat either alone?
5. What is the 2 OCU minimum cost implication for OpenSearch Serverless?

## 14. Cross-references

- **Module 27** — vector capabilities decision framework
- **Module 42** — Bedrock Knowledge Bases
- **Module 56** — log analytics as observability backend

## Primary sources

- [`OpenSearch_Vector_Search.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/OpenSearch_Vector_Search.html)
- [`OpenSearch_Serverless.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/OpenSearch_Serverless.html)
- [`OpenSearch_kNN.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/OpenSearch_kNN.html)
- Research report: [`06c_analytical_vector_graph.md`](../../research_inputs/04_aws_for_ai_ml/06c_analytical_vector_graph.md)
