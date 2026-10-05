# Module 16 — Relational Basics — RDS Family

> **What this is:** Amazon RDS managed relational databases (Postgres, MySQL, MariaDB, Oracle, SQL Server, Db2), with the production essentials — Multi-AZ, read replicas, RDS Proxy, Blue/Green deployments, IAM auth, encryption.

---

## 1. Supported engines (as of 2026-05)

- **PostgreSQL** — default for greenfield in regulated enterprises. Versions through 17.x. **pgvector** ships in 0.7+ for embedding-similarity search in OLTP.
- **MySQL** — 5.7 (extended support), 8.0, 8.4 LTS.
- **MariaDB** — drop-in MySQL alternative; less common in regulated estates.
- **Oracle** — BYOL or License Included; CDB architecture required as of 21c.
- **SQL Server** — Express, Web, Standard, Enterprise editions; Always On not exposed (use Multi-AZ).
- **Db2** — added Dec 2023 (LUW, BYOL). Capital One historically ran Db2 on z/OS; managed RDS-Db2 is the off-ramp.

## 2. High availability — Multi-AZ Instance vs Cluster

| Feature | **Multi-AZ Instance** | **Multi-AZ Cluster** |
|---|---|---|
| Standby count | 1 (sync) | 2 (semi-sync) |
| Standbys readable? | No | Yes (read-after-write caveats) |
| Failover time | 60-120s | <35s typical |
| Engines supported | All | Postgres, MySQL only |
| Storage | Single EBS per node | Per-node local storage |

**Read replicas** are async-replicated copies for read scale-out. Intra-region uses engine-native replication; cross-region adds encryption-key replication and ~seconds-to-minutes lag. Promotion breaks the replication relationship.

## 3. RDS Proxy

**Fully managed connection pool**. Mandatory for **Lambda → RDS** at any scale: Lambda's per-invocation connection burst kills Postgres `max_connections`.

- Supports IAM auth pass-through.
- Secrets Manager rotation — no app restart on credential rotation.
- Adds ~5ms latency.
- Costs ~$0.015 / vCPU-hour of the underlying instance.

## 4. Blue/Green Deployments

Clone the production cluster, apply schema / engine changes on the green stack, then switch over with replication ensuring data parity. **Switchover typically ~1 minute** of write downtime.

2024 milestones: GA for SQL Server, cross-region promotion for Aurora.

Use for: major-version upgrades, schema changes, instance class moves.

## 5. Other operational essentials

- **Parameter groups** (engine config: `work_mem`, `max_connections`) vs **option groups** (engine features: Oracle OEM, SQL Server Audit). DB-level vs cluster-level scope matters for Aurora.
- **Automated backups** — 1-35 day retention, PITR to a second. Manual snapshots persist until deleted; encrypted snapshots can be copied cross-region/cross-account.
- **IAM authentication** — 15-min token replaces password. Cap: 200 new connections/sec per instance; use RDS Proxy to amortize.
- **Encryption at-rest** — via KMS (customer or AWS-managed CMK). Cannot toggle on a live instance — must snapshot, copy with encryption, restore.
- **TLS** — `rds-ca-rsa2048-g1` is the current bundle as of 2026. The 2024 CA rotation forced fleet-wide client updates — plan for the next rotation.
- **Performance Insights** — 7 days free retention, paid up to 2 years. **AAS (Average Active Sessions)** is the headline metric — anything above vCPU count means saturation.

## 6. 2024-2026 changes

- **RDS for Db2** GA Dec 2023.
- **Postgres 17** support early 2025.
- **MySQL 8.4 LTS** late 2024.
- **Extended Support pricing** kicked in for MySQL 5.7 and Postgres 11 at $0.10/vCPU-hr after community EOL — budget this for legacy.
- **Blue/Green for SQL Server** GA 2024.
- **pgvector 0.7** with HNSW filtered search.
- **RDS storage autoscaling now supports gp3 from gp2 in-place** (no rebuild).

## 7. Pitfalls

- **Storage autoscaling traps** — max storage threshold is a hard ceiling, not advisory. Once hit, writes fail. Set with 50% headroom and alarm at 70% used.
- **gp2 burst exhaustion** — under 1TB you live on burst credits. Move to gp3 for predictable performance below the 1TB threshold.
- **Free storage = log files + temp** — long-running Postgres transactions bloat WAL and `pg_temp`. Alert on `FreeStorageSpace` not just CPU.
- **Connection storm during failover** — Multi-AZ failover invalidates DNS; clients with cached connections must reconnect. RDS Proxy hides this from app pods.

## 8. Capital One lens

Capital One is Postgres-heavy for transactional services (per public re:Invent talks), with Aurora for the largest workloads. RDS-on-Postgres is the default for medium services where Aurora's premium isn't justified. Db2 RDS is a likely candidate for mainframe-modernization tracks. **RDS Proxy is mandatory for any Lambda fronting Postgres.**

## 9. Pricing nuance

- A `db.r6g.large` Multi-AZ instance is roughly 2x single-AZ price (you pay for the standby).
- gp3 storage is ~20% cheaper than gp2 and decouples IOPS from size.
- Reserved Instances yield 30-60% discount over 1y/3y terms; aligns poorly with cloud-native autoscaling but well with steady-state OLTP.

## 10. Sanity check

1. Multi-AZ Instance vs Cluster — when does Cluster pay off?
2. When is RDS Proxy mandatory?
3. What does Blue/Green deployment buy you, and what's the typical downtime?
4. Why does IAM auth need RDS Proxy at any scale?
5. What's the AAS metric in Performance Insights?

## 11. Cross-references

- **Module 17** — Aurora (RDS's higher-performance sibling)
- **Module 19** — DocumentDB (Aurora-style architecture, NoSQL)
- **Module 22, 24** — Redshift/Athena query federation reading from RDS
- **Module 32** — Lambda + RDS Proxy pattern

## Primary sources

- [`RDS_Best_Practices.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/RDS_Best_Practices.pdf)
- Research report: [`06a_relational_dynamodb.md`](../../research_inputs/04_aws_for_ai_ml/06a_relational_dynamodb.md)
