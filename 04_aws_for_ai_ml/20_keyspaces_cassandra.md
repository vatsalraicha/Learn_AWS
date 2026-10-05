# Module 20 — Amazon Keyspaces (for Apache Cassandra)

> **What this is:** managed Cassandra-API-compatible service. When to pick it over DynamoDB. The "Cassandra without operating Cassandra."

---

## 1. The pitch

Amazon Keyspaces is a managed Cassandra-API service. It exposes the **CQL (Cassandra Query Language)** wire protocol and most CQL surface, but **the underlying storage is not Apache Cassandra**. AWS implements the Cassandra protocol on a proprietary backend that looks more like DynamoDB.

This matters: behaviors that come from Cassandra's gossip / vnodes / hinted handoff don't apply.

## 2. Capacity modes

- **On-demand** — pay-per-request, no provisioning.
- **Provisioned** — RCU/WCU like DynamoDB.

Switch mode once per 24h. Same model as DynamoDB.

## 3. Multi-region replication

**Active-active across up to 6 regions.** Conflict resolution is last-writer-wins (similar to DynamoDB Global Tables).

## 4. Partition design

Same principles as Cassandra:
- Choose partition keys that distribute writes evenly.
- Clustering keys define order within partition.
- Bounded partitions (under ~100MB).

## 5. CQL surface — what's supported vs gaps

**Supported:**
- Most basic CQL — SELECT, INSERT, UPDATE, DELETE, CREATE TABLE.
- Indexes (limited).
- Time-To-Live.
- Lightweight transactions (LWT) within a single partition.

**Not supported:**
- **Materialized views** — not implemented.
- **User-defined functions (UDFs)**.
- **Triggers**.
- **Cross-partition LWT**.
- Some CQL functions (e.g., `toTimestamp`).
- **Tunable consistency** — only ONE and LOCAL_QUORUM are supported.

## 6. Other constraints

- **Max row size: 1 MB** (Cassandra OSS allows larger). Common trap when porting.
- **No tunable replication factor** — managed by AWS.

## 7. Keyspaces vs DynamoDB

| | Keyspaces | DynamoDB |
|---|---|---|
| API | CQL (Cassandra) | DynamoDB API |
| Use it for | Existing Cassandra apps | New AWS-native designs |
| Max row | 1 MB | 400 KB |
| Cross-partition transactions | No | Yes (TransactWriteItems) |
| Streams | No (different mechanism) | Yes |
| Multi-region | Up to 6 regions | Global Tables |
| Vector search | No | No |

**Rule:** if you don't have an existing Cassandra investment, default to DynamoDB.

## 8. Use cases

- **Time-series data** — events with high write throughput, queried by partition + time range.
- **Existing Cassandra apps** migrating to AWS without rewriting CQL.
- **High-throughput KV** with large rows up to 1MB.

## 9. Pitfalls

- **Porting from open-source Cassandra** — many features absent. Test first.
- **CQL gotchas** — materialized views, UDFs, triggers won't work; rewrite using app-layer logic.
- **Row size limit** — 1 MB cap surprises ports from Cassandra clusters with multi-MB rows.

## 10. Capital One lens

Probably used selectively for time-series workloads where the team has Cassandra expertise. DynamoDB is the broader default per their public patterns.

## 11. Sanity check

1. What's the Keyspaces vs Cassandra OSS difference under the hood?
2. What's the max row size, and how does that constrain Cassandra ports?
3. What CQL features are NOT supported?
4. When does Keyspaces win over DynamoDB?
5. What's the multi-region active-active limit?

## 12. Cross-references

- **Module 18** — DynamoDB (the AWS-native alternative)
- **Module 21** — ElastiCache + MemoryDB (other low-latency options)

## Primary sources

- [`Keyspaces_Developer_Guide.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/Keyspaces_Developer_Guide.html)
- [`Keyspaces_Best_Practices.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/Keyspaces_Best_Practices.html)
- Research report: [`06b_nosql_siblings.md`](../../research_inputs/04_aws_for_ai_ml/06b_nosql_siblings.md)
