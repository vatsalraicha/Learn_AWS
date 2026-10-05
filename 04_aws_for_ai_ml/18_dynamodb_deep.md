# Module 18 — DynamoDB Deep

> **What this is:** the canonical AWS NoSQL key-value/document store — single-table design, partition keys + GSI/LSI, Streams, TTL, on-demand vs provisioned, DAX, transactions, Global Tables, PITR, hot-partition pathologies.

---

## 1. Single-table design

DynamoDB rewards denormalization. The canonical pattern: **one table holds all entity types**, distinguished by generic partition (`PK`) and sort keys (`SK`) with overloaded values:

```
PK              SK              ... attributes
USER#123        PROFILE         email="...", name="..."
USER#123        ORDER#2026-05   amount=100, status="shipped"
USER#123        SESSION#abc     last_seen=...
```

Access patterns are encoded into key prefixes; queries are `PK = X AND SK BEGINS_WITH Y`. **Trade-off:** schema lives in app code, tooling weaker, but reads are O(1) with no joins.

## 2. Keys and indexes

| | Description |
|---|---|
| **Partition key alone (HASH)** | Point lookups only |
| **PK + SK (HASH + RANGE)** | Range scans within partition |
| **GSI (Global Secondary Index)** | Different PK/SK; async-replicated; separate throughput. Up to **20 per table** (raised 2023 from 5) |
| **LSI (Local Secondary Index)** | Same PK, different SK; sync; **must be defined at table creation**; 10 GB per-partition cap inherits |

## 3. Streams and triggers

DynamoDB Streams emit ordered change records per partition for **24 hours**. Common sinks:

- **Lambda triggers** — fire on each batch; the classic CDC pattern (item updated → invalidate cache, send notification, fan to OpenSearch).
- **Kinesis Data Streams** integration (since 2020) — 1-year retention, multiple consumers, replay capability. Preferred for analytics fanout.

## 4. TTL

Per-item epoch attribute. Items are deleted **within 48 hours** of expiry — **not at the second** (common bug). TTL deletes emit Stream events with `userIdentity: dynamodb`. **Free.**

## 5. Capacity modes

- **Provisioned** — you set RCU/WCU; auto-scaling supported. Reserved Capacity 1y/3y for ~50-75% discount.
- **On-demand** — pay-per-request, scales instantly up to **2× the previous peak** (peak limit raised significantly in 2024 to 1M RCU / 1M WCU per table on request).

**Switching mode allowed once per 24h.**

**Crossover:** on-demand wins below ~14-18% sustained utilization of equivalent provisioned. Spiky traffic → on-demand; flat 24/7 traffic → provisioned + reserved.

## 6. DAX (DynamoDB Accelerator)

Write-through cache for **microsecond reads** (vs single-digit-ms direct).

- VPC-bound cluster.
- Item cache (`GetItem`) and query cache (`Query`/`Scan`).
- **Limitations:** no consistent-reads through DAX item cache; cluster failover ~30s.
- Pricing: per node-hour like ElastiCache (~$0.04/hr for `dax.t3.small` up to $4+/hr for `dax.r5.16xlarge`).

## 7. Transactions

`TransactWriteItems` / `TransactGetItems`.

- Up to **100 items** (raised 2022 from 25).
- **4 MB total** payload.
- ACID, all-or-nothing.
- **Twice the cost** of normal writes/reads.

Use for multi-item invariants (debit + credit ledger pair).

## 8. Global Tables

Multi-region active-active replication with **last-writer-wins** conflict resolution based on stream timestamp.

- Eventual consistency cross-region (~1s typical).
- Replication is free per-row; you pay RCU/WCU in each region.
- **Global Tables v2 (2019)** is the only supported version; v1 deprecated mid-2024.

## 9. Point-in-Time Recovery (PITR)

35-day continuous backup, second-granular restore to any new table. **Doubles the storage bill while enabled** — budget for it.

## 10. Import/Export with S3

- **Import from S3** (2022) — bulk-create a new table from S3 (DynamoDB JSON, ION, CSV). Free except for table writes — but writes are billed as `WCU × items`.
- **Export to S3** — point-in-time snapshot to S3, ION or JSON. Doesn't consume RCU. Use for analytics via Athena / Glue.
- **2024**: incremental export to S3 — only changed items since last export. Turns DynamoDB → S3 → Athena into a low-cost CDC pipeline.

## 11. Hot partitions and adaptive capacity

Each partition caps at **3000 RCU / 1000 WCU**.

A skewed key (e.g., `customerId` for a viral user) saturates one partition while the table is nominally fine.

**Adaptive capacity** (always-on since 2019) rebalances throughput across partitions but **cannot break the per-partition cap**.

**Fix: write sharding** — append a random suffix `customerId#0..9` to spread writes, then query 10 partitions and merge.

## 12. Expression syntax

Three expression types in queries:
- **Key Condition Expression** — what defines the range (`PK = :v AND SK BEGINS_WITH :p`).
- **Filter Expression** — post-filter applied after read (still consumes RCU on filtered-out items).
- **Projection Expression** — which attributes to return.

## 13. Consistent vs eventually consistent reads

- **Eventually consistent** (default) — half the RCU cost; possible to read stale data within ~1 sec.
- **Strongly consistent** — full RCU cost; latest write returned.

## 14. DynamoDB Local

A downloadable Java app that mimics the API for local development. Doesn't perfectly replicate Streams or some auto-scaling behaviors, but good enough for unit tests.

## 15. Pitfalls

- **Hot partition** — single key dominating. Use write sharding.
- **GSI throttling** — separate WCU; if you under-provisioned the GSI, writes propagate slowly. **Provisioned mode: pay attention to GSI capacity separately.**
- **Filter Expression illusion** — filtering doesn't reduce RCU; it just hides items after the read.
- **Scan instead of Query** — scans every item. Almost never the right answer; design access patterns to be Queries.

## 16. Capital One lens

DynamoDB is the natural fit for Capital One's serverless-first culture:
- Lambda + DynamoDB is the canonical pattern.
- Per-LOB tables with consistent naming and tagging.
- On-demand mode for new services; switch to provisioned + reserved as traffic stabilizes.
- DynamoDB Streams → Lambda → fraud-detection model is a common pattern.

## 17. Sanity check

1. What is single-table design and what's the trade-off?
2. GSI vs LSI — when does each make sense, and what's the LSI gotcha?
3. What's the per-partition throughput cap, and what's the workaround for hot keys?
4. Why does on-demand vs provisioned crossover happen around 14-18%?
5. What does PITR cost, and what does it cover?

## 18. Cross-references

- **Module 21** — ElastiCache + MemoryDB (alternative low-latency stores)
- **Module 22** — DynamoDB → Redshift zero-ETL
- **Module 32** — Lambda + DynamoDB Streams (the canonical CDC pattern)
- **Module 56** — DynamoDB cost discipline

## Primary sources

- [`DynamoDB_Best_Practices.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/DynamoDB_Best_Practices.pdf)
- Research report: [`06a_relational_dynamodb.md`](../../research_inputs/04_aws_for_ai_ml/06a_relational_dynamodb.md)
