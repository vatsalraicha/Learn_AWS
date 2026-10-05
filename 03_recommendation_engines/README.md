# Topic 03 — Recommendation Engines (and Ads)

> Comprehensive curriculum on how recommendation systems and ad-ranking systems are designed, built, trained, and operated in production — covering math foundations, classical ML, deep learning, generative recommenders, and the engineering reality at Netflix, Spotify, YouTube, Meta, TikTok, Apple, Amazon, Pinterest, LinkedIn, Airbnb, and the B2B/outreach long tail. The Ads section is treated as a first-class peer to Recommendations, not a footnote.

## Why this matters

Recommendations and ads are **the two ML applications that pay for most of consumer internet**. They are also the most architecturally honest: latency budgets are measured in milliseconds, label distributions are biased by the system's own past decisions, and a 1% offline accuracy gain may be invisible online while a 1% ranking change can move millions in revenue. If you can hold the whole stack — auction theory, feature engineering, embedding tables, two-tower retrieval, multi-task ranking, exploration, calibration, attribution, privacy APIs — you are credible as an AI architect for *most* consumer or marketplace products on earth.

## Learning path

### Part A — Foundations
| # | Module | Why it matters |
|---|--------|----------------|
| 1 | [Foundations & taxonomy](01_foundations.md) | What "a recommender" actually is; problem framings (rating prediction, top-N, slate, session); business metrics vs ML metrics; the retrieval→ranking→reranking funnel as the universal architecture |
| 2 | [Mathematical foundations](02_math_foundations.md) | Similarity (cosine, dot, Mahalanobis); matrix factorization math (SVD, ALS, BPR, WARP); learning-to-rank loss families (pointwise/pairwise/listwise); softmax sampling math; the calibration math behind CTR models |
| 3 | [Data, signals & features](03_data_features.md) | Implicit vs explicit feedback; logging discipline; positive/negative sampling; impression logging; counterfactual data; feature engineering taxonomy; embedding tables and hash collisions; feature freshness budgets |
| 4 | [Evaluation: offline → online](04_evaluation.md) | Recall@k, NDCG, HR, MAP, MRR; per-user vs per-impression; offline–online correlation gap; A/B testing, interleaving, MAB; CUPED; counterfactual off-policy estimators (IPS, DR, DM); guardrails |

### Part B — Classical algorithms
| # | Module | Why it matters |
|---|--------|----------------|
| 5 | [Content-based filtering](05_content_based.md) | TF-IDF + cosine; the "no cold-start for items" property; modern revival via embeddings; when content-based beats CF |
| 6 | [Collaborative filtering — neighborhood](06_collaborative_filtering.md) | User-based and item-based kNN; Amazon's classic 2003 item-to-item paper; similarity metrics (Pearson, adjusted cosine); shrinkage |
| 7 | [Matrix factorization & FM family](07_matrix_factorization.md) | SVD/FunkSVD/SVD++; ALS for implicit feedback (Hu, Koren, Volinsky); BPR (Bayesian Personalized Ranking); Factorization Machines (Rendle 2010); FFM |

### Part C — Deep learning era
| # | Module | Why it matters |
|---|--------|----------------|
| 8 | [Neural recommenders & CTR models](08_neural_ctr.md) | NCF (and why it was overrated), Wide & Deep, DeepFM, xDeepFM, DCN/DCN-V2, AutoInt, FiBiNet, MaskNet, DLRM, FinalMLP |
| 9 | [Sequential & session models](09_sequential.md) | GRU4Rec, SASRec, BERT4Rec, S3-Rec, CL4SRec, gSASRec; long-history models (SIM, ETA, TWIN); DIN/DIEN/BST (Alibaba) |
| 10 | [Two-tower retrieval at scale](10_two_tower.md) | The dominant production retrieval architecture; in-batch negatives; mixed negative sampling; sampled softmax; YouTube's two-tower; LogQ correction; serving topology |
| 11 | [Graph neural networks for recs](11_gnn.md) | LightGCN, NGCF; PinSage (Pinterest); PinnerSage multi-embedding users; heterogeneous GNNs; subgraph sampling at scale |
| 12 | [LLMs & generative recommenders](12_llm_generative.md) | TIGER, semantic IDs (RQ-VAE), HSTU (Meta's generative recommender), P5, LLaRA, RecLLM, CoLLM; LLM-as-feature-extractor vs LLM-as-ranker vs generative recsys; Wukong scaling laws |

### Part D — Production architecture
| # | Module | Why it matters |
|---|--------|----------------|
| 13 | [The funnel: retrieval → ranking → re-ranking](13_funnel.md) | Why every large-scale recommender is a funnel; latency budgets at each stage; candidate union; ranking model topology; reranking layer |
| 14 | [Candidate generation systems](14_candidate_generation.md) | Multiple parallel retrievers (content, collaborative, social, popularity, freshness, exploration); per-source dedup; quotas and caps |
| 15 | [Ranking & multi-task learning](15_ranking_mtl.md) | MMoE, PLE, STAR, PEPNet; multi-objective optimization; value modeling; calibration; reward shaping for long-term value |
| 16 | [Cold start, exploration, debiasing, fairness, freshness](16_coldstart_exploration_bias.md) | Cold-start patterns; ε-greedy, Thompson sampling, LinUCB, contextual bandits; position bias models; selection/exposure bias; diversity (MMR, DPP); calibration; fairness |

### Part E — Industry deep dives
| # | Module | Why it matters |
|---|--------|----------------|
| 17 | [Netflix](17_netflix.md) | The Prize → matrix factorization → deep learning → unified Foundation Model; row personalization; artwork bandits; XP experimentation; Metaflow/Maestro |
| 18 | [Spotify](18_spotify.md) | Echo Nest heritage; Discover Weekly; BaRT bandits; audio embeddings (musicnn, OpenL3); podcasts; AI DJ; Annoy → Voyager |
| 19 | [YouTube + Google](19_youtube_google.md) | Covington 2016; MMoE multi-task; Top-K off-policy RL; TIGER generative retrieval; Google Discover; ScaNN; TFRS |
| 20 | [Apple](20_apple.md) | Differential privacy + on-device personalization; Apple Music/News/App Store; Apple Intelligence; PCC; CoreML |
| 21 | [Meta — Feed, Reels, Generative Recommender](21_meta.md) | DLRM; Reels; HSTU generative recommender; FBGEMM; MTIA; TorchRec; trillion-parameter embeddings |
| 22 | [TikTok / ByteDance](22_tiktok.md) | Monolith real-time training; collisionless embedding hashing; FYP exploration; Volcano Engine |
| 23 | [Amazon, Pinterest, LinkedIn, Airbnb, Uber, DoorDash, Etsy](23_marketplace_zoo.md) | Marketplace recommenders, search ranking, two-sided fairness, geo, ETA-aware ranking |
| 24 | [B2B & outreach startups](24_b2b_outreach.md) | Lead scoring, intent data, ABM, Salesforce Einstein, Clay/Apollo/Outreach/Salesloft, generative cold email, sales enablement search |

### Part F — Ads (first-class section)
| # | Module | Why it matters |
|---|--------|----------------|
| 25 | [Ads foundations: auctions & economics](25_ads_auctions.md) | GSP, VCG, first-price; eCPM, pCTR×bid; quality score; reserve prices; programmatic ecosystem (DSP/SSP/DMP/Exchange); RTB & OpenRTB |
| 26 | [CTR & CVR prediction at depth](26_ctr_cvr_models.md) | FTRL → Wide&Deep → DeepFM → DCN-V2 → DIN/DIEN/BST → SIM/ETA → DLRM → Wukong → HSTU; ESMM for delayed conversions; calibration math |
| 27 | [Bidding, pacing & budget control](27_bidding_pacing.md) | Bid shading for first-price; PID controllers for pacing; smart bidding (tCPA, tROAS, value-based); auto-bidding evolution |
| 28 | [Attribution & measurement](28_attribution_measurement.md) | Last-click, MTA, DDA; lift studies; geo experiments; MMM resurgence (Meridian, Robyn, LightweightMMM); incrementality; uplift modeling |
| 29 | [Privacy & post-cookie advertising](29_privacy_ads.md) | ATT/IDFA; SKAdNetwork/AdAttributionKit; Privacy Sandbox (Topics, Protected Audience, Attribution Reporting); CHIPS; clean rooms; differential privacy in ads |
| 30 | [Ads at Google, Meta, Amazon, TikTok, Apple, Microsoft](30_ad_platforms.md) | Performance Max, Advantage+, Sponsored Products, Symphony AI, Apple Search Ads, retail media networks |
| 31 | [Creatives, fraud, brand safety](31_creative_fraud_safety.md) | Generative creative (Performance Max + Advantage+ + Symphony), Dynamic Creative Optimization, brand-safety classification, IVT/SIVT, IAS/DV/MOAT |

### Part G — Tech stack & MLOps
| # | Module | Why it matters |
|---|--------|----------------|
| 32 | [The recsys tech stack](32_tech_stack.md) | Kafka/Flink, feature stores (Feast/Tecton/Vertex/Databricks), TorchRec/TFRS/Merlin, FAISS/HNSW/ScaNN/Vespa, Triton/Ray Serve, experiment platforms, observability |
| 33 | [Reference architectures by company size](33_reference_architectures.md) | Startup (~$5M ARR), mid-stage (~$50M ARR), hyperscaler ($1B+). Build vs buy decisions, vendor (Amazon Personalize / Vertex AI / Recombee / Algolia) vs in-house |

### Part H — Experimentation deep dive
| # | Module | Why it matters |
|---|--------|----------------|
| 34 | [A/B testing & experimentation methods by business type](34_ab_testing_methods.md) | The 10 experimentation methods (bucket A/B, interleaving, switchback, cluster, geo / synthetic control, CUPED, sequential testing, long-term holdouts, lift studies, bandits); how Netflix, Uber, Meta, Salesforce do it differently; SRM + the 15 things that go wrong; experimentation platforms (XP, ERF, Curie, Statsig, Eppo); the maturity ladder |

## Companion files

- [`FACTS.md`](FACTS.md) — atomic, citable facts (numbers, model names, paper IDs, benchmark scores, dates). Single source of truth; every volatile claim in modules points here.
- [`quizzes/`](quizzes/) — per-module questions for cold recall practice.
- [`code/`](code/) — runnable Python: MF/ALS/BPR from scratch, two-tower in PyTorch, SASRec, LightGBM ranker, contextual bandit, simple ad auction simulator.
- [`references/`](references/) — downloaded/archived papers and engineering blog posts (where licensing allows).

## How to use this

1. Read **Part A** in order — foundations are the substrate everything else assumes.
2. Skim Parts B and C, then jump to whichever depth matters for your role:
   - **Architect interview prep** → Parts A, C, D, E, G
   - **Ads-side role** → Parts A, B, then jump to F
   - **ML engineer fundamentals** → Parts A, B, C, with the code/
3. Use FACTS.md as your quick-reference index.
4. The industry deep dives (Part E) cite specific papers — read at least one per company you care about.

## Scope notes

- **Cutoff:** content reflects 2025-early-2026 state of practice. Generative recommenders (HSTU/TIGER) shifted from research to production between 2023 and 2025; CTR architectures evolve more slowly.
- **Math density:** modules 2, 7, 8, 10, 26 are math-heavy on purpose. The rest is architecture and engineering.
- **Code intent:** demonstrate algorithm mechanics on toy datasets. None of it is production-grade.
- **Bias:** strong English-language internet / US-centric (Netflix/YouTube/Spotify/Meta/Amazon) plus ByteDance and Alibaba where their published work dominates. Indian/European marketplaces (Flipkart, Zalando, Bol.com) get cameo coverage only.
