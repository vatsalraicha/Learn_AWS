# Quiz 05 — Databases (Modules 16-27)

> Take cold. 12-module Part E. Aim for 80%.

---

## Recall

1. Aurora's 6-way replicated storage — write quorum? Read quorum?
2. DynamoDB single-table design — what's the core idea?
3. What's the difference between MemoryDB and ElastiCache?
4. Aurora DSQL's headline property — what is it?
5. Which database engines support `pgvector`?
6. Bedrock Knowledge Bases — what are the native vector backends?

## Apply

7. Design a feature store with sub-millisecond online lookups for fraud-scoring and offline analytics for training. Which AWS services back the online and offline tiers?
8. You need horizontally-sharded Postgres with 2M+ writes/sec. Which AWS service GA'd in 2024 does this?
9. Capital One uses both Redshift and Snowflake. What workload would you put on each?
10. Design RAG for 10M policy documents with hybrid lexical + semantic search. Which vector backend, and why?

## Diagnose

11. A DynamoDB table is hot — one partition is throttling at 1000 WCU while the table is provisioned at 10,000 WCU. Why, and how do you fix it?
12. Aurora I/O-Optimized — when does the 30% instance premium pay back?
13. Your DocumentDB query that worked on MongoDB 6.x is failing. What's the likely cause?

## Defend

14. Argue for picking Amazon Keyspaces over DynamoDB.
15. Argue against using MemoryDB as a system-of-record vs DynamoDB.

---

## Answers

1. **Write quorum 4/6. Read quorum 3/6.** Aurora tolerates losing 1 entire AZ + 1 more copy.
2. **One table holds many entity types**, distinguished by generic PK/SK overloaded values (`USER#123` / `ORDER#456`). Reads are O(1), no joins; trade-off is schema lives in app code.
3. **MemoryDB is durable** (multi-AZ transactional log) — system-of-record. **ElastiCache is a cache** — data can be lost. Both Redis-compatible (and now Valkey).
4. **Multi-region active-active strongly consistent writes** (Postgres-compatible). AWS's answer to Spanner / Cockroach.
5. **Aurora Postgres** and **RDS Postgres** support pgvector (versions 15+).
6. **OpenSearch Serverless** (default), **Aurora pgvector**, **Pinecone**, **Redis Enterprise**, **MongoDB Atlas**, **Neptune Analytics** (2024).
7. **Online**: SageMaker Feature Store (DynamoDB-backed) for ms latency, or MemoryDB for sub-ms. **Offline**: SageMaker Feature Store offline (S3 + Iceberg).
8. **Aurora Limitless Database** (GA Dec 2024).
9. **Redshift** for service-team marts + Zero-ETL from Aurora (AWS-native, predictable cost). **Snowflake** for enterprise-shared analytics (cross-team concurrency via multi-cluster warehouses, data marketplace pattern).
10. **OpenSearch Service (or Serverless)** with FAISS HNSW + hybrid BM25+vector. BM25 catches exact-term matches; vector catches semantic similarity; combined dramatically improves recall.
11. **Hot partition**: per-partition cap is 3000 RCU / 1000 WCU regardless of table provisioning. Adaptive capacity rebalances throughput but can't break the per-partition cap. **Fix: write sharding** — append random suffix `customerId#0..9` to spread writes.
12. When **I/O cost exceeds ~25% of total Aurora bill**. High-write or high-scan OLTP typically wins on I/O-Optimized; sleepy report DBs stay on Standard.
13. DocumentDB targets **MongoDB 5.0 API** — operations introduced in 6.x or 7.x may not be supported. Check the DocumentDB compatibility matrix.
14. **Existing Cassandra app** with CQL queries — Keyspaces lets you migrate without rewriting code. Time-series workloads with Cassandra patterns. **But** if no Cassandra investment, DynamoDB is the AWS-native default.
15. **MemoryDB is ~2-3× ElastiCache cost** because it's durable. For a system-of-record use case, **DynamoDB** is cheaper at scale, has Streams/Global Tables/PITR, and uses on-demand. MemoryDB shines for **ultra-low-latency** SoR (sub-ms) where DynamoDB single-digit-ms is too slow.
