# 04 — Databases in the Development Process

> Nana's curriculum places this as a "bonus" inside Phase 1. For an AI/ML engineer who already runs Snowflake/Databricks/RDS/DynamoDB regularly, this is review — but the **DevOps angle** (where databases fit in the pipeline, schema migrations, backups, secrets) is worth a quick pass.

## 1. Why databases matter to DevOps

A DevOps pipeline touches the database every deploy:
- Schema migrations must run safely (forward AND reversibly)
- Backups must verify (untested backups are not backups)
- Credentials must rotate (secrets manager → app config)
- Test environments need realistic data (anonymized prod or synthetic)
- Production data must never leak into non-prod

## 2. The database landscape in 2026

| Category | Examples | Use case |
|---|---|---|
| **Relational (SQL)** | Postgres, MySQL, SQL Server, Oracle | Default choice; transactional, ACID, joins |
| **Cloud-managed relational** | RDS, Aurora, Cloud SQL, Azure SQL, Supabase, Neon, PlanetScale | Same as above but managed |
| **NoSQL document** | MongoDB, DynamoDB, CosmosDB, Firestore | Flexible schema, sharding by default |
| **NoSQL key-value** | Redis, DynamoDB, Memcached, ElastiCache | Cache, session store, rate limit |
| **NoSQL wide-column** | Cassandra, ScyllaDB, BigTable, Keyspaces | Massive write scale, time-series, sensor |
| **Graph** | Neo4j, Neptune, ArangoDB, TigerGraph | Relationships are the access pattern |
| **Time-series** | InfluxDB, TimescaleDB, Prometheus (internal), VictoriaMetrics | Metrics, IoT, financial ticks |
| **Vector** | Pinecone, Weaviate, Qdrant, Milvus, pgvector, OpenSearch, Atlas Vector Search | RAG, semantic search |
| **Search** | OpenSearch, Elasticsearch, Algolia, Typesense | Full-text + faceting |
| **OLAP / Data Warehouse** | Snowflake, BigQuery, Redshift, Databricks SQL | Analytical queries on TBs+ |
| **Lakehouse** | Databricks (Delta), Iceberg + Trino, S3 Tables | Warehouse-lake hybrid |
| **NewSQL** | CockroachDB, Spanner, Aurora DSQL (May 2025 GA), YugabyteDB | Distributed SQL with strong consistency |

The 2026 vibe: **Postgres has won** the "default OLTP" tier (with all its extensions: pgvector, PostGIS, TimescaleDB, Citus). Anything else needs a justification.

## 3. Schema migrations — the DevOps blocker

Tools:
- **Flyway** (Java, SQL-first, paid + OSS) — banking standard
- **Liquibase** (Java, XML/YAML/JSON/SQL) — banking alternative
- **Alembic** (Python, SQLAlchemy ecosystem) — Python apps
- **golang-migrate** — Go apps
- **Rails Active Record migrations** — Ruby
- **Prisma Migrate** — Node/TS apps
- **DBmate** — language-agnostic, simple

Migration discipline:
1. **Forward-only with backfill, not destructive.** Add column nullable → backfill → mark NOT NULL in next migration → remove old column in third migration. Three deploys, never one.
2. **Migration runs before app deploy.** Pipeline: migrate → deploy → smoke test.
3. **Migrations are tested in CI** against a fresh DB.
4. **Rollback plan documented per migration** (most teams forward-fix; the more disciplined have explicit DOWN migrations tested).

## 4. Database connection patterns in the pipeline

- **Local dev**: `.env` file with DATABASE_URL, gitignored.
- **CI**: ephemeral DB container (Postgres in docker-compose), seeded with fixtures.
- **Staging**: managed instance, anonymized prod snapshot or synthetic data.
- **Production**: managed instance with secrets in Secrets Manager, IAM auth where supported.

```yaml
# docker-compose snippet for CI
services:
  postgres:
    image: postgres:17-alpine
    environment:
      POSTGRES_PASSWORD: ci_password
      POSTGRES_DB: app_test
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 2s
```

## 5. Backups — the production reality

Cloud-managed DBs handle backups for you:
- **RDS / Aurora**: automated backups (1-35 day retention), continuous backup for PITR, manual snapshots
- **DynamoDB**: PITR (35 days), on-demand backups
- **Atlas (MongoDB)**: continuous + scheduled snapshots, queryable backups

Self-managed: `pg_dump`, `pg_basebackup`, `mongodump` on cron + offsite copy.

**The test that matters**: can you actually restore in < your RTO? Run a quarterly restore drill. Capital One does this for every critical system.

## 6. Quick self-check

1. Why is "destructive migration on prod" a DevOps anti-pattern?
2. What's the 3-deploy column-rename pattern?
3. How does DynamoDB PITR differ from on-demand backups?
4. Why is Postgres the 2026 default for OLTP?
5. Where do you store the database password in a Jenkins pipeline?

(Answers: irreversible breakage, no rollback path; add new nullable → backfill → enforce NOT NULL → drop old; PITR = continuous to any second in last 35 days, snapshots = point-in-time copies; battle-tested + ecosystem + extensions; in Jenkins Credentials store referenced by ID, never inline in Jenkinsfile.)
