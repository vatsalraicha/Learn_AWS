# Module 23 — Amazon, Pinterest, LinkedIn, Airbnb, Uber, DoorDash, Etsy

> Marketplace recommenders — where the recommendation is also a purchase, a booking, or a job application. The math is the same as Modules 8-12; the constraints (two-sided fairness, ETA, geo, perishable supply) are different and more interesting.

---

## 1. Amazon

### 1.1 The 2003 item-to-item paper

Linden, Smith, York 2003 — the most-cited industrial recsys paper of the 2000s. Module 6 §3 has the details.

The architecture: precompute item-item similarity offline; at request time, for user history `H`, score candidate `j` by `Σ_{i ∈ H} sim(i, j)`. Latency independent of user count.

Powers "Customers Who Bought This Also Bought." Twenty years old, still in production.

### 1.2 Modern Amazon stack

| Surface | Dominant signal |
|---|---|
| Homepage carousels ("Recommended for you") | Long-term taste; recency-weighted browse |
| PDP item-item | Co-purchase / co-view item similarity |
| "Frequently bought together" | Co-purchase within same order |
| Cart upsell | Order-affinity, small-ticket items |
| "Buy it Again" | Poisson / hazard-rate replenishment model |
| Search ranking | A9 → A10 → A11/Cosmo |
| Sponsored Products | Auction × predicted CTR × predicted CVR |

- **PRP (Personalized Re-Ranking Platform)** — internal re-ranker over candidates from upstream retrievers.
- **Buy it Again** — Poisson model for consumables ([Bhagat et al. 2019](https://www.amazon.science/publications/buy-it-again-modeling-repeat-purchase-recommendations)).
- **COSMO (2024)** ([Amazon Science](https://www.amazon.science/publications/cosmo-a-large-scale-e-commerce-common-sense-knowledge-generation-and-serving-system)) — LLM-distilled knowledge graph enriching query understanding ("running shoes → outdoor cardio → complementary: hydration belt").

### 1.3 Search ranking — A9, A10, A11/Cosmo

- **A9** (~2003-2017): keyword relevance + sales velocity + conversion rate, feature-engineered linear model.
- **A10** (~2018-2020): heavier weighting on external traffic, organic vs paid conversion, seller authority.
- **A11 / Cosmo** (2023-2024): LLM-augmented knowledge graph + deep multi-task ranker.

Multi-objective deep ranker: click probability, purchase probability, contribution profit, quality signals (return rate, review sentiment, defect rate).

### 1.4 Amazon Personalize — externalised

The AWS-managed service. Recipes:
- User-Personalization (HRNN-Metadata).
- Personalized-Ranking — re-rank caller-provided candidates.
- Similar-Items — item-item CF.
- Trending-Now, Popularity-Count, Item-Affinity.
- Next-Best-Action (2022) for sequential decisions.

Built on similar primitives to Amazon.com internal but multi-tenant and recipe-bounded.

### 1.5 Infrastructure

- **DynamoDB** — sessions, cart, recommendation cache. Sub-10ms p99.
- **Neptune** — graph DB for product-knowledge-graph traversal.
- **SageMaker** — training/serving substrate.
- **OpenSearch** — BM25-flavoured sparse retrieval.

---

## 2. Pinterest

### 2.1 PinSage (2018)

Ying et al. KDD 2018. The first widely-deployed production GNN. Module 11 §4 has the details.

- 3B pins, 18B edges.
- GraphSAGE with random-walk neighbourhood sampling.
- Producer-consumer training.
- Hard-negative curriculum.
- MapReduce-style inference.

Powers Related Pins, Home Feed candidate generation.

### 2.2 PinnerSage (2020) — multi-embedding user

Pal et al. KDD 2020. Cluster the user's history into Ward-medoid groups; user is represented by ~3 medoids. At serve time, retrieve top-K per medoid and merge.

### 2.3 ItemSAGE — multimodal content embedding

Multimodal content understanding folded into a single pin embedding. Inputs: pin image (ViT), title, description, board context, OCR'd image text.

### 2.4 Two-tower + HNSW

Pinterest is among the heaviest production HNSW users — lower latency at high recall, better tail latency.

### 2.5 LLM-based labeling (2024-2026)

Pinterest publicly describes LLMs used to:
- Label pins with rich taste / intent tags.
- Generate query expansions for search.
- Generate synthetic training labels.
- Caption images.

---

## 3. LinkedIn

### 3.1 People You May Know (PYMK)

Signal mix:
- Graph proximity (FoF strongest).
- Shared affiliations (employer, school, skills).
- Address book imports (with consent).
- Co-occurrence (same meeting, email thread, group).
- Engagement signals.

Eras: Linear → GBDT → GNN/two-tower → LiGNN (2024).

### 3.2 LiRank (2024)

[Borisyuk et al. KDD 2024](https://arxiv.org/abs/2402.06859) "LiRank: Industrial Large Scale Ranking Models at LinkedIn."

Consolidated ranker family used across Feed, Jobs, Ads, PYMK:
- **Residual DCN** for feature interactions.
- **Dense Gating** to control feature contribution dynamically.
- **Isotonic calibration layer** trained jointly.
- **INT8 quantisation** for serving at scale.
- Transformer layers for sequence features.

### 3.3 LiGNN (2024)

[arXiv 2402.11139](https://arxiv.org/abs/2402.11139). Graph neural network framework at LinkedIn scale.
- Adaptive neighborhood sampling.
- Training infrastructure for 100+ billion edges.
- Powers PYMK, job recommendations, content.

### 3.4 JYMBII — Jobs You Might Be Interested In

- Retrieval by skills match, title similarity, geo, seniority, learned embeddings.
- Ranking by predicted apply rate, predicted **qualified-apply** rate, predicted dismissal.
- Two-sided constraints: impression caps per posting, fairness constraints.

### 3.5 Recruiter Search — EBR

Embedding-based retrieval over 1B+ members. Query tower × member tower → ANN + lexical filters + cross-encoder rerank.

### 3.6 Open-source

- **Photon ML** — Spark-based ML library with GAME (generalised additive mixed effects).
- **Feathr** — open-source feature store, donated to LF AI 2022 ([github.com/feathr-ai/feathr](https://github.com/feathr-ai/feathr)).

---

## 4. Airbnb

### 4.1 The 2018 embeddings paper

[Grbovic & Cheng KDD 2018](https://www.kdd.org/kdd2018/accepted-papers/view/real-time-personalization-using-embeddings-for-search-ranking-at-airbnb) — best paper.

Two embedding spaces:

1. **Listing embeddings** from click sessions. Skip-gram with negative sampling; **booked listing as global context** anchors training; **negative sampling from the same market** ensures within-market similarity.
2. **User-type and listing-type embeddings** for **long-term** personalisation. Bucket users/listings into types since per-user embeddings would be too sparse.

### 4.2 Two-sided marketplace constraints

Airbnb ranks for:
- Guest preference + click/book likelihood.
- Host quality (response rate, cancellation rate, rating, Superhost).
- Marketplace health — avoid concentrating bookings on a small set.
- Geographic diversity.
- Calendar availability and price competitiveness.

### 4.3 Smart Pricing

Recommends nightly prices to hosts. Counterfactual estimation challenge: we only observe one realised price per night.

### 4.4 ML platform — Bighead and Chronon

- **Bighead** — Airbnb's end-to-end ML platform.
- **Chronon** ([open-sourced 2023](https://chronon.ai)) — feature platform with point-in-time correctness, declarative DSL for windowed aggregations evaluated identically in batch and streaming.

---

## 5. Uber Eats / Uber

### 5.1 Restaurant recommendations

Multi-objective ranking blends:
- Conversion (P(order | impression)).
- Quality (rating, repeat rate, photo quality).
- Distance / ETA — a 45-minute ETA destroys conversion.
- Diversity (cuisine, price band).
- Marketplace economics (delivery fee, commission, partner status).

### 5.2 Michelangelo — ML platform

Internal ML platform, publicly documented since 2017. Feature store / Palette, training on Spark and Ray, GPU clusters, model registry, real-time prediction service.

One of the first widely-cited "internal ML platforms"; inspired much of the industry's feature-store push.

### 5.3 DeepETA

ETA prediction is foundational. Transformer encoder consuming origin/destination geo features, time, traffic, recent realised ETAs from nearby rides. Sub-50ms p99. Consumed by Uber Eats ranking, driver-rider matching, surge pricing.

---

## 6. DoorDash

### 6.1 Store and item ranking

Two-tower retrieval (consumer × store) + deep multi-task ranker. Factors: predicted conversion, ETA and fee, quality, diversity, marketplace constraints.

### 6.2 DoubleML and causal inference

DoorDash has been most public on:
- **DoubleML / Doubly-Robust estimation** for unbiased treatment-effect estimates from observational data.
- **CATE** — predict **by how much** showing a store as top result increases order probability vs showing it lower.
- Applied to: promotion targeting, store ordering, pricing, dispatch.

[doordash.engineering](https://doordash.engineering/) has the blog series.

### 6.3 Sibyl

Feature/prediction service: sub-10ms p99 for hundreds of models, feature transformation inside the prediction service, tight integration with experimentation.

---

## 7. Etsy

### 7.1 Marketplace structure

- ~100M+ listings, ~9M active sellers.
- Listings mostly unique / near-unique; lifetime weeks; small quantity.
- Buyer intent often aesthetic/exploratory.
- Pure CF is weak; content-based methods central.

### 7.2 Embedding-based retrieval

- Listing embeddings from title + description + image + taxonomy + shop signals.
- Query embeddings, tower trained against engagement.
- ANN over listings via FAISS / HNSW.
- **Hybrid retrieval** fusing dense embedding scores with BM25 — exact-token matching catches what dense vectors miss in long-tail text.

### 7.3 Multi-stakeholder ranking

Two stakeholders: buyers (relevance, quality, conversion) and sellers (fair impression distribution; new-shop bootstrap).

Mechanisms:
- Fairness re-rankers capping exposure per shop.
- Exploration boosts for new listings.
- Quality scores penalising policy-violating / low-effort listings.

### 7.4 Cold start for handmade / long-tail

- **Image embeddings** carry most of the cold-start signal — in handmade, the photograph is much of the product.
- **Taxonomy / attribute extraction** (color, material, occasion, style) gives structured cold-start features.
- **Shop-level priors** bootstrap new listings.

---

## 8. Cross-cutting patterns

| Pattern | Where |
|---------|-------|
| Two-tower retrieval | All eight |
| Multi-objective ranking | All eight |
| GNN in production | Pinterest, LinkedIn |
| Content embeddings central | All — increasingly LLM-derived |
| Open-sourced feature store | LinkedIn (Feathr), Airbnb (Chronon) |
| Causal inference / uplift | DoorDash, Uber, Airbnb |
| Multi-stakeholder fairness | Airbnb, Etsy, LinkedIn jobs |

---

## 9. Sanity check

1. Amazon's 2003 item-item paper is still in production 20 years later. What property of item-item CF makes it so durable at scale?
2. Pinterest deploys PinSage end-to-end. Why are GNNs more valuable at Pinterest than at YouTube?
3. LinkedIn's LiRank trains a calibration layer jointly with the main model. Why is this better than post-hoc calibration?
4. Airbnb's "booked listing as global context" — what training-time trick does this represent and why is it important?
5. DoorDash uses DoubleML to estimate ranking treatment effects. Why is observational click rate insufficient for ranking improvement decisions?
6. Etsy's cold start relies on image embeddings. Why does image dominate over text for handmade goods?
