# Module 33 — Reference Architectures by Company Size

> Three blueprints: startup (~$5-50M ARR), mid-stage (~$50-500M ARR), hyperscaler ($1B+). Each one is *complete* — a team could implement it. Each one is *appropriate* for its scale — building the hyperscaler stack at a Series B startup is the most common failure mode in this curriculum.

---

## 1. The startup stack ($5-50M ARR)

100-person SaaS / consumer / B2B startup. 100k-10M MAU.

```
┌────────────────────────────────────────────────────────────────────┐
│                        DATA / WAREHOUSE                           │
│  App Postgres ──► Fivetran / Airbyte ──► Snowflake or BigQuery   │
│  Segment / Rudderstack ──► same warehouse                         │
│  dbt for transformations                                          │
└──────────────────────────────┬─────────────────────────────────────┘
                               │
                  ┌────────────┴────────────┐
                  ▼                         ▼
        ┌──────────────────┐      ┌──────────────────┐
        │  Feast online    │      │  Training jobs   │
        │  (Redis backend) │      │  (Modal / GH     │
        │                  │      │   Actions / Ray) │
        └────────┬─────────┘      │  LightGBM        │
                 │                │  sentence-       │
                 │                │  transformers    │
                 │                └────────┬─────────┘
                 │                         │
                 │             ┌───────────┴────────────┐
                 │             ▼                        ▼
                 │     ┌──────────────┐         ┌──────────────┐
                 │     │  MLflow      │         │ Pinecone /   │
                 │     │  registry    │         │ pgvector     │
                 │     └──────┬───────┘         └──────┬───────┘
                 │            │                        │
                 ▼            ▼                        ▼
        ┌────────────────────────────────────────────────────┐
        │           FastAPI service (Python 3.11)            │
        │  /recommend → retrieve(Pinecone) → rank(LightGBM)  │
        │             → rules → response                      │
        └─────────────────────────┬──────────────────────────┘
                                  │
                       ┌──────────┴──────────┐
                       ▼                     ▼
                ┌────────────┐        ┌──────────────┐
                │ Cloudflare │        │  Datadog +   │
                │ / Vercel   │        │  Evidently   │
                │ edge       │        │  self-host   │
                └────────────┘        └──────────────┘

   Experimentation: Statsig free tier or GrowthBook self-host
```

### 1.1 Choices

- **LightGBM ranker** (not deep learning) — fits the data scale, fast inference, SHAP for explainability.
- **Sentence-transformers** for content embeddings — pretrained, free, runs anywhere.
- **Pinecone or pgvector** depending on scale and existing Postgres.
- **Feast + Redis** for online features.
- **Statsig free tier** for A/B.
- **Modal / GitHub Actions** for periodic training (no dedicated GPU cluster).

### 1.2 Cost ballpark

| Item | Cost / month |
|---|---|
| Snowflake/BigQuery | $2K-$8K |
| Pinecone (Starter/Standard) | $70-$700 |
| Redis Cloud | $100-$1K |
| Modal/Runpod GPU jobs | $200-$1K |
| Cloud compute (FastAPI on Fargate/Cloud Run) | $200-$1K |
| Observability (Datadog + Evidently OSS) | $500-$3K |
| Experimentation (Statsig paid) | $0-$3K |
| **Total** | **$3K-$20K/mo** |

Well under one MLE's loaded cost.

### 1.3 When to upgrade

- > 10M MAU.
- > 50ms p99 latency consistently breached.
- Multiple models needing shared features.
- Multiple teams sharing the platform.

---

## 2. The mid-stage stack ($50-500M ARR)

10-100M MAU. Multiple product surfaces. Multiple ML teams.

```
                 ┌─────────────────────────────────────────┐
                 │   Kafka + schema registry              │
                 └────────────┬────────────────────────────┘
       ┌──────────────────────┼──────────────────────┐
       ▼                      ▼                      ▼
┌──────────────┐    ┌────────────────┐    ┌────────────────┐
│ Flink for    │    │ Spark on EMR / │    │ Snowflake /    │
│ streaming    │    │ Databricks for │    │ BigQuery for   │
│ features +   │    │ batch ML +     │    │ analytics +    │
│ aggregations │    │ training       │    │ BI             │
└──────┬───────┘    └────────┬───────┘    └────────────────┘
       │                     │
       │                     ▼
       │           ┌──────────────────┐
       │           │  Iceberg / Delta │
       │           │  on S3 / GCS     │
       │           └──────────────────┘
       │                     │
       └────────┬────────────┘
                ▼
       ┌──────────────────┐
       │ Tecton or        │
       │ Chronon / Feathr │
       │ feature platform │
       └────────┬─────────┘
                │
       ┌────────┼─────────────────────────────┐
       ▼                                      ▼
┌─────────────────┐                  ┌──────────────────┐
│  Training:      │                  │  Online store:   │
│  PyTorch +      │                  │  ScyllaDB or     │
│  TorchRec on    │                  │  DynamoDB        │
│  4-32 GPUs      │                  └────────┬─────────┘
│  TFRS / Merlin  │                           │
└────────┬────────┘                           │
         │                                    │
         ▼                                    ▼
┌─────────────────┐                  ┌──────────────────┐
│  MLflow         │                  │  Two-stage       │
│  registry       │                  │  serving:        │
└────────┬────────┘                  │  Triton ranker + │
         │                           │  FAISS/HNSW      │
         └──────────────────────────►│  retriever       │
                                     └────────┬─────────┘
                                              │
                                              ▼
                                     ┌──────────────────┐
                                     │  Arize / Evidently│
                                     │  monitoring +    │
                                     │  Statsig/Eppo for │
                                     │  experimentation │
                                     └──────────────────┘
```

### 2.1 Choices

- **Deep ranker** (DLRM-style with TorchRec or DCN-V2 with TFRS) is feasible.
- **Tecton** or open-source Chronon/Feathr for the feature platform.
- **NVIDIA Triton** for GPU serving with dynamic batching.
- **FAISS or HNSW** for retrieval.
- **Arize** for ML observability.
- **CUPED-aware experimentation** (Statsig paid tier or Eppo).

### 2.2 Cost ballpark

| Item | Cost / month |
|---|---|
| Data infra (Kafka + Flink + Spark + S3) | $30K-$150K |
| Snowflake/BigQuery + Iceberg | $20K-$100K |
| GPU training cluster (4-32 GPUs) | $50K-$300K |
| Online serving (Triton + ScyllaDB) | $30K-$200K |
| Observability + experimentation vendor | $20K-$100K |
| **Total** | **$150K-$850K/mo** |

10-30 MLEs supported.

---

## 3. The hyperscaler stack ($1B+ revenue)

100M+ MAU. Trillion-parameter models. 50-500 MLEs on recsys alone.

```
              ┌──────────────────────────────────┐
              │ Kafka / Pulsar bus (own infra)  │
              └────────────┬─────────────────────┘
            ┌──────────────┼─────────────────────┐
            ▼              ▼                     ▼
┌───────────────┐  ┌────────────────┐  ┌──────────────────┐
│ Flink stream  │  │ Spark / Trino  │  │ ClickHouse for   │
│ feature jobs  │  │ on Iceberg     │  │ near-real-time   │
│               │  │ lake (S3/GCS)  │  │ analytics        │
└──────┬────────┘  └────────┬───────┘  └──────────────────┘
       │                    │
       ▼                    ▼
┌─────────────────────────────────────────┐
│ In-house Feature Platform               │
│ (Tecton++, Feast++, Chronon-like)       │
│ Online: ScyllaDB / Cassandra / Bigtable │
│ Offline: Iceberg/Delta on S3            │
└─────────┬───────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────┐
│ Training:                                │
│  - TorchRec on 8x-128x H100 / MTIA      │
│  - Hundreds of experiments/week         │
│  - Internal HP scheduler (Ray-like)     │
│  - LLM pipeline for content embeddings  │
└─────────┬───────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────┐
│ Two-stage serving on Triton / custom    │
│  Retrieval: Vespa or in-house HNSW/ScaNN│
│  Ranking: DLRM/HSTU/sequence model      │
│  Embedding cache: ScyllaDB / Cassandra  │
│  Hot-feature cache: in-memory           │
│  p99 < 80ms end-to-end                  │
└─────────┬───────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────┐
│ Internal Experimentation Platform        │
│ (Netflix XP / Airbnb ERF clone)          │
│ - CUPED, sequential testing              │
│ - Interleaving for ranking comparisons   │
│ - Long-term holdouts                     │
│ - Counterfactual / off-policy eval        │
└─────────────────────────────────────────┘
```

### 3.1 What's different at this scale

- **Custom feature platform** — vendor pricing doesn't scale linearly past ~1B feature reads/day.
- **Self-managed ANN** — Vespa or custom HNSW with embedding-cache locality optimisations.
- **Two-stage models with shared embedding tables**, sharded via TorchRec or custom parameter servers.
- **100% in-house experimentation** — vendor stats engines aren't trustworthy at FAANG-scale traffic.
- **Generative recommenders** (HSTU at Meta, TIGER variants at Google) in production by 2025-2026.

### 3.2 Cost ballpark

- **Training compute**: $10M-$100M/yr.
- **Serving compute**: $10M-$100M/yr.
- **Storage + data infra**: $5M-$30M/yr.
- **ML talent**: $50M-$300M/yr.
- **All-in**: **$100M-$500M/yr**.

---

## 4. Build vs buy decision

When to build a custom feature platform / ANN / experimentation:

| Signal | Build |
|---|---|
| Feature reads > 1B/day | Yes |
| > 50 MLEs blocked by vendor | Yes |
| Latency SLA < 50ms p99 consistently breached | Maybe |
| Specific privacy / compliance need vendor can't meet | Yes |
| Internal political pressure to "not depend on a vendor" | No (bad reason) |
| Team has the staffing | Yes |
| Team thinks they can do it in 6 months | No (will take 2 years) |

The classical mistake: a 50-person company tries to build the hyperscaler stack. Recipe for an unshipped product.

---

## 5. The recsys engineering org chart

At each scale, the team structure changes.

### 5.1 Startup

- 1-3 ML engineers reporting to head of engineering.
- Shared platform with data engineering.
- Quarterly OKRs tied to a single metric (CTR, conversion, retention).

### 5.2 Mid-stage

- 10-30 MLEs across 2-5 surface teams.
- Dedicated ML platform team (3-5 engineers).
- Quarterly OKRs per surface; platform team metrics on developer productivity (model deploys/week).

### 5.3 Hyperscaler

- 100-500 MLEs.
- ML platform team (50+).
- Per-surface teams (Feed ranking, Ads ranking, Retrieval, Re-ranking, etc).
- Specialised teams: experimentation platform, embedding infra, content understanding (LLM features).
- Half-yearly OKRs; complex value-model trade-offs handled by product leadership.

---

## 6. Common failure modes at each stage

### 6.1 Startup

- Over-engineering: building Kafka before having a recsys.
- Premature deep learning: training a transformer with 100k events.
- No A/B testing: shipping by intuition; can't tell what works.

### 6.2 Mid-stage

- Train-serve skew: built fast, didn't enforce point-in-time correctness.
- Feedback loops without exploration: model gets weirder over months.
- Cost explosion: 5 teams each running their own GPU cluster.

### 6.3 Hyperscaler

- Org friction > tech friction: building anything takes 3 quarters because of platform reviews.
- Long-term reward divergence: short-term metrics keep rising; retention quietly drops.
- Talent burnout: ranking systems become so complex new hires take 9 months to ship.

---

## 7. Sanity check

1. A 100-person B2B SaaS company wants to build a "Netflix-style recommender." What stack do you actually propose for their first iteration?
2. The classic build-vs-buy mistake is building before scale demands it. Give two signals that say "you should still use the vendor."
3. Mid-stage companies often try to centralise everything in one feature store. What's the trade-off and when does it become net-positive?
4. The hyperscaler ML org chart has a 50-person platform team. What does that team produce that no individual surface team would?
5. Your CEO says "we want to build our own DLRM in 6 months." You're at $30M ARR. How do you push back constructively?
