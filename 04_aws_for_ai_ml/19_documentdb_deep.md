# Module 19 — DocumentDB Deep

> **What this is:** Amazon DocumentDB — MongoDB-compatible document database with Aurora-style architecture, Elastic Clusters for sharding, vector search for RAG, change streams.

---

## 1. Architecture

DocumentDB borrows Aurora's separation of compute and storage. Each cluster has:

- **Primary** (writer)
- **Replicas** (readers, up to 15)
- **6-way replicated storage across 3 AZs**, like Aurora.

You pay per-instance, like RDS. **Instance-based pricing** is the biggest cost differentiator from MongoDB Atlas's cluster-tier pricing.

## 2. MongoDB compatibility

- Compatible with **MongoDB 5.0 API**. Older docs say 4.0; this was upgraded to 5.0 in 2023.
- Some MongoDB API gaps: change streams structure differs slightly; certain operators not implemented; no `$lookup` across collections (added in 4.0+); aggregation pipeline supported.
- Use the official `mongo` shell or Compass; clients work as long as they target compatible API version.

## 3. Sharding via Elastic Clusters

DocumentDB **Elastic Clusters** (GA 2023) allow horizontal sharding for large workloads:

- Up to **32 shards** per cluster.
- Up to **64 instances per shard**.
- Multi-billion-document collections supported.
- Shard keys define partitioning.
- Capital One use case: large document workloads (e.g., per-customer JSON profiles).

## 4. Indexes

- **Compound** indexes — multi-field, ordered.
- **Multikey** indexes — on array fields.
- **Geospatial** — 2dsphere for lat/lon queries.
- **Text** — full-text on string fields.
- **Hashed** indexes — even-distribution sharding.
- **TTL indexes** — auto-expire docs.

## 5. Vector search

**DocumentDB vector search** (GA 2024) — vector indexes for RAG and similarity search:

- **HNSW** and **IVFFlat** index types.
- Up to **2,000 dimensions**.
- Inner product, cosine, Euclidean distance metrics.
- Capital One use case: **in-VPC RAG** — embeddings of compliance docs / customer FAQs stored in DocumentDB without leaving the VPC.

## 6. Aggregation pipeline

Standard MongoDB-style aggregation: `$match`, `$group`, `$project`, `$lookup`, `$unwind`, `$facet`, etc. Used for analytics inside DocumentDB without separate ETL.

## 7. Change streams

Like MongoDB. Tail the change stream from a Lambda or Glue job to react to inserts/updates/deletes. Used for CDC, cache invalidation, downstream sync.

## 8. IAM authentication

GA 2023. Replaces password auth with IAM SigV4 tokens. Pairs with IRSA / Pod Identity for EKS workloads.

## 9. Migration patterns

- **AWS DMS (Database Migration Service)** can migrate from self-managed MongoDB to DocumentDB.
- Some operators may need rewriting due to API gaps.
- Capital One pattern: lift acquired companies' MongoDB workloads onto DocumentDB via DMS.

## 10. DocumentDB vs MongoDB Atlas on AWS

| | DocumentDB | MongoDB Atlas on AWS |
|---|---|---|
| Native AWS integration | Yes (IAM, KMS, VPC) | Limited (BYO IAM) |
| Latest MongoDB version | 5.0 API | Latest (7.x+ at 2026) |
| Aggregation pipeline | Most | All |
| Atlas-specific features | No | Atlas Search, Charts, Triggers |
| Pricing | Instance-based | Cluster-tier |
| FedRAMP / regulated | Yes (AWS-native) | Limited |

For regulated finance, **DocumentDB wins** on AWS-native security integration. For pure feature parity with MongoDB, Atlas wins.

## 11. 2024-2026 changes

- **DocumentDB vector search** GA 2024.
- **Elastic Clusters** (sharding) GA 2023, refined 2024.
- **IAM auth** GA 2023.
- **MongoDB 5.0 API parity** improvements.

## 12. Pitfalls

- **API gaps vs MongoDB** — some operators absent. Test before migration.
- **Index size limits** — like MongoDB, indexes count against memory.
- **Cluster failover** — primary failover ~30s, not seconds like Aurora.
- **Connection pooling** — DocumentDB has lower default max connections than self-managed MongoDB. Use a connection pool (mongoose connection pooling, MongoEngine, etc.).

## 13. Capital One lens

DocumentDB is the natural store for:
- Member-profile JSON documents.
- Compliance / regulatory document libraries (paired with vector search for RAG).
- Acquired-company MongoDB migrations.

## 14. Sanity check

1. What's DocumentDB's architecture, and what AWS service is it modeled on?
2. What MongoDB API version does DocumentDB target as of 2026?
3. When would you use Elastic Clusters?
4. What's the vector search story, and what use case fits at Capital One?
5. DocumentDB vs Atlas — when does each win?

## 15. Cross-references

- **Module 27** — vector capabilities decision framework (DocumentDB vs alternatives)
- **Module 42** — Bedrock Knowledge Bases (can DocumentDB be a backend?)
- **Module 17** — Aurora (the architectural parent)

## Primary sources

- [`DocumentDB_Best_Practices.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/DocumentDB_Best_Practices.html)
- [`DocumentDB_Vector_Search.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/DocumentDB_Vector_Search.html)
- Research report: [`06b_nosql_siblings.md`](../../research_inputs/04_aws_for_ai_ml/06b_nosql_siblings.md)
