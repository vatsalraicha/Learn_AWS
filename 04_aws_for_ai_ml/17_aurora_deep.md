# Module 17 — Aurora Deep

> **What this is:** Aurora architecture (6-way replicated storage), Aurora Postgres vs MySQL, Aurora Serverless v2, **Aurora Limitless** (sharded, GA Dec 2024), and **Aurora DSQL** (distributed multi-region active-active Postgres, GA May 2025 — the 2025 headline service). Plus Global Database, Babelfish, I/O-Optimized.

---

## 1. The architecture innovation

Aurora's key idea: **separate compute from storage**.

- Compute nodes (writer + readers) are stateless DB engines.
- Storage is a distributed, log-structured fleet replicating each **10 GB segment 6 ways across 3 AZs** (2 copies per AZ).
- Write quorum: **4 of 6**. Read quorum: **3 of 6**. Aurora can lose an entire AZ plus one more copy and stay available for both reads and writes.

Replication is via **redo-log shipping to storage**, not buffer-page replication. Readers tail the same log; replica lag is typically **10-20 ms** vs RDS's seconds.

## 2. Aurora Postgres vs Aurora MySQL

| | Aurora PG | Aurora MySQL |
|---|---|---|
| Compatibility | PG 11–16 | MySQL 5.7, 8.0 |
| **Babelfish** | Yes (SQL Server wire compat) | No |
| ML integration | Yes (Bedrock, SageMaker, Comprehend) | Yes |
| **Limitless** | Yes (GA Dec 2024) | Preview only |
| Parallel Query | Limited | Broader |

## 3. Aurora Serverless v2

v2 fixes v1's biggest sin: cold starts. v2 maintains a warmer pool of pre-provisioned ACUs and scales in **0.5 ACU increments within seconds**, not minutes.

- v1 is deprecated as of late 2024 — migrate.
- v2 supports Global Database, read replicas, Data API.
- Pricing: 1 ACU ≈ 2GB RAM + proportional CPU at ~$0.12/ACU-hour.
- **Crossover vs provisioned** `r6g.large` (~$0.29/hr): ~50% sustained utilization. Below that, serverless v2 wins.

## 4. Aurora Limitless Database (GA Dec 2024)

Horizontally-sharded Postgres-compatible database.

- Define **sharded tables** (partitioned by a column like `customer_id`).
- Define **reference tables** (replicated to every shard).
- A **routing layer** (DB shard group endpoint) parses SQL and routes to the right shard.
- **Cross-shard transactions** use distributed 2PC.
- Claimed throughput at re:Invent 2024: **2M+ writes/sec**.

Use when you've outgrown single-writer Aurora (typically 200K+ writes/sec sustained) and don't need DSQL's multi-region active-active.

## 5. Aurora DSQL (GA May 2025) — the headline

**Aurora DSQL** (Distributed SQL) is a serverless, **multi-region active-active Postgres-compatible** database. AWS's answer to Spanner and CockroachDB.

Key properties:
- **Multi-region active-active strongly consistent writes** with single-digit-ms commit latency in-region.
- Writes use a distributed time-ordered commit protocol on **Time Sync Service** (microsecond-precise hardware clocks).
- **Postgres-compatible** wire protocol and SQL surface — subset at GA (no foreign keys, no triggers, no sequences with strict ordering).
- **No instance management** — fully serverless.
- **Optimistic concurrency control** — transactions can abort with serialization errors; app must retry.
- Pricing: **per DPU** (Distributed Processing Unit), per-byte-stored, per-region.

**Use cases:**
- Globally distributed financial transactions.
- Multi-region SaaS where every region needs read+write.
- Regulatory data sovereignty with availability.

**Capital One implication:** DSQL maps directly onto multi-region active-active aspirations for **card auth and fraud-decision systems**. This is strategically the most important new database service AWS has shipped since DynamoDB Global Tables. Watch closely.

## 6. Aurora Global Database

Storage-level replication to **up to 5 secondary regions** with <1s lag typical. Secondary is read-only until promoted.

- Managed planned failover: ≤2 min RPO.
- Unplanned failover: RPO seconds, RTO ~1 min.

**Different from DSQL:** GD is asynchronous primary/secondary; DSQL is sync active-active.

## 7. Babelfish

Postgres extension that speaks the **Microsoft SQL Server TDS wire protocol** and T-SQL dialect.

Migrate SQL Server apps to Aurora PG **without rewriting client code**. Compatibility is partial — not all T-SQL constructs supported. Use the **Babelfish Compass** tool to assess.

## 8. Aurora I/O-Optimized

Pricing tier where you pay ~30% more on instance hours and storage, but **I/O is free**.

Standard Aurora bills per I/O at $0.20 per million requests.

**Breakeven:** workloads where I/O > ~25% of total Aurora bill. **High-write, high-scan OLTP almost always wins on I/O-Optimized; sleepy report DBs stay on Standard.**

## 9. Aurora ML integration

`aws_ml.invoke_endpoint` calls SageMaker; `aws_bedrock.invoke_model` calls Bedrock; `aws_ml.detect_sentiment` calls Comprehend — all from SQL.

Useful for inline embedding generation and feature serving — **but careful**: a hot SELECT against Bedrock will rack up cost fast. Cache results.

## 10. Pitfalls

- **Reader endpoint stickiness** — Aurora's reader endpoint round-robins on DNS resolution, but JDBC pools cache one IP. Use **AWS JDBC Wrapper Driver** for proper reader load balancing.
- **Storage cost surprises** — Aurora bills storage on high-water-mark; deletes don't shrink. Use `VACUUM FULL` (carefully) or dump/restore.
- **Failover read-after-write** — after failover, old writer becomes a reader briefly; stale reads possible. Application must handle.

## 11. Capital One lens

- **Aurora Postgres** for transactional services at scale (likely the platform's default for new builds).
- **Aurora Serverless v2** for non-prod environments and bursty workloads.
- **Aurora DSQL** is the architecturally interesting service for multi-region card auth and fraud decisioning — expect Capital One to be a public reference customer at some re:Invent in 2025-26.
- **I/O-Optimized** for write-heavy fraud / fraud-feature tables.

## 12. Sanity check

1. How does Aurora's 6-way replicated storage tolerate failure?
2. When does Aurora Serverless v2 win economically over provisioned?
3. Limitless vs DSQL — what's the difference in consistency model?
4. What does Babelfish solve, and what's its compatibility tool?
5. When is I/O-Optimized worth the 30% instance premium?

## 13. Cross-references

- **Module 16** — RDS family (Aurora is built on the RDS control plane)
- **Module 27** — pgvector in Aurora for RAG
- **Module 18** — DynamoDB Global Tables (Aurora DSQL alternative for K-V)
- **Module 41** — SageMaker integration with Aurora ML extensions

## Primary sources

- [`Aurora_User_Guide.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/Aurora_User_Guide.pdf)
- [`Aurora_DSQL_Whitepaper.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/Aurora_DSQL_Whitepaper.pdf)
- Research report: [`06a_relational_dynamodb.md`](../../research_inputs/04_aws_for_ai_ml/06a_relational_dynamodb.md)
