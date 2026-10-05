# Module 21 — ElastiCache & MemoryDB

> **What this is:** AWS's in-memory data stores — ElastiCache (Redis / Valkey / Memcached cache), MemoryDB (durable Redis-compatible primary DB), the Valkey fork story, vector search at sub-millisecond latency.

---

## 1. The Valkey story (2024)

In March 2024, Redis Inc. relicensed Redis from BSD to a **dual SSPL/RSALv2 license** — effectively non-open-source.

The Linux Foundation forked Redis as **Valkey** (March 28, 2024, fork point Redis 7.2.4), under BSD. AWS, Google Cloud, Oracle, Ericsson, and SnapChat became founding sponsors.

**AWS dropped ~33% off ElastiCache Valkey pricing** vs ElastiCache Redis. ElastiCache Serverless and MemoryDB now support Valkey as the modern default for new builds.

## 2. ElastiCache — the cache tier

**Three engine options:**
- **Valkey** — the open-source fork. Default in 2026 for new builds.
- **Redis OSS** — versions through 7.4 still supported.
- **Memcached** — simpler key-value cache; no persistence, no replication, no clustering coordination. Niche.

**Deployment modes:**
- **Cluster mode disabled** — single primary + replicas, single shard.
- **Cluster mode enabled (CME)** — multi-shard cluster, 500 shards max, 16,384 hash slots. **Migration from CMD → CME is painful** — application must handle hash-slot routing.

**ElastiCache Serverless** (GA Nov 2023) — pay per data + per ECPU (ElastiCache Processing Unit). No node sizing. Great default for unpredictable workloads.

## 3. MemoryDB — durable Redis-compatible primary DB

**MemoryDB** is positioned as a **system-of-record**, not a cache. Same Redis API, but:

- **Multi-AZ durability** via transactional log to S3-like layer.
- **Strong consistency** within primary; eventual consistency across replicas.
- Used as **primary DB** for ultra-low-latency workloads — session state, real-time leaderboards, feature stores.

**MemoryDB vector search** (GA 2024) — HNSW indexes for sub-millisecond similarity search. The use case: **real-time agent/RAG context retrieval** where the user-facing latency budget is < 50ms.

## 4. ElastiCache vs MemoryDB

| | ElastiCache | MemoryDB |
|---|---|---|
| **Durability** | Cache (data can be lost) | Durable primary DB |
| **Replication** | Async to replicas | Sync via transactional log |
| **Use case** | Cache, ephemeral state | System of record, feature store |
| **Cost** | Lower per GB | ~2-3× ElastiCache |
| **Vector search** | (via Redis 7.x ANN) | Yes (HNSW, 2024) |

## 5. Cache patterns (ElastiCache)

| Pattern | Description |
|---|---|
| **Cache-aside (lazy loading)** | App reads cache; on miss, queries DB, writes to cache. Most common. |
| **Write-through** | App writes both to DB and cache atomically. Lower miss rate, higher write latency. |
| **Write-behind (write-back)** | App writes only to cache; async background writes DB. Risky if cache fails. |
| **TTL-based expiration** | Set TTL on every key; cache evicts on expiry. Simple staleness control. |

## 6. Hot key mitigation

Hot key = single key getting disproportionate traffic.

Fixes:
- **Read from replicas** for read-heavy hot keys.
- **Client-side caching** (Redis 6+ tracking) — clients cache responses, server invalidates on change.
- **Sharding by key suffix** — split one logical key across N physical keys, client picks one.

## 7. Pricing snapshot

- **ElastiCache Valkey** `cache.r7g.large` ~$0.227/hr (33% cheaper than Redis on same hardware after AWS pricing change).
- **ElastiCache Serverless** — per ECPU + per GB-hr; ~$0.0035 per ECPU.
- **MemoryDB Valkey** `db.r7g.large` ~$0.515/hr — about 2.3× ElastiCache.

## 8. 2024-2026 changes

- **Valkey fork** March 2024; AWS GA on ElastiCache + MemoryDB.
- **AWS ~33% Valkey price drop** vs Redis on equivalent hardware.
- **ElastiCache Serverless** GA Nov 2023.
- **MemoryDB Vector Search** GA 2024.
- **Redis 7.4** still supported but Valkey is the recommended forward-looking choice.

## 9. Pitfalls

- **Cluster mode migration** (CMD → CME) is a non-trivial app rewrite.
- **MemoryDB cost overshoot** when used as a cache instead of system-of-record.
- **Memcached's lack of persistence** means cache restart = full miss.
- **Vector search on small datasets** — adds operational complexity for marginal benefit vs Aurora pgvector.

## 10. Capital One lens

Likely patterns:
- **ElastiCache Valkey Serverless** for service-tier caching.
- **MemoryDB** for the online feature store where sub-millisecond is required.
- **MemoryDB Vector** for agent context retrieval (Eno, Servicing Tool) where latency budget is tight.

## 11. Sanity check

1. What's the Valkey story and why does it matter to AWS pricing?
2. When does MemoryDB make sense vs ElastiCache?
3. Cache-aside vs write-through vs write-behind — which is most common and why?
4. How do you mitigate a hot key in Redis?
5. What's the MemoryDB vector search use case at Capital One scale?

## 12. Cross-references

- **Module 18** — DynamoDB (the durable KV alternative)
- **Module 27** — vector capabilities decision framework
- **Module 35** — SageMaker Feature Store (offline-online split; MemoryDB as the online tier)

## Primary sources

- [`ElastiCache_Best_Practices.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/ElastiCache_Best_Practices.html)
- [`Valkey_Announcement.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/Valkey_Announcement.html)
- [`MemoryDB_Vector_Search.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/MemoryDB_Vector_Search.html)
- Research report: [`06b_nosql_siblings.md`](../../research_inputs/04_aws_for_ai_ml/06b_nosql_siblings.md)
