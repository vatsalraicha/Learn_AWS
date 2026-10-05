# Topic 03 — Recommendation Engines & Ads — Table of Contents

> Master index. Open this first.

## Top-level

- [`README.md`](README.md) — Overview, learning path, scope notes
- [`FACTS.md`](FACTS.md) — Atomic, citable facts (numbers, model names, paper IDs, benchmark scores, dates)

---

## Modules

### Part A — Foundations
- [Module 1 — Foundations & taxonomy](01_foundations.md)
- [Module 2 — Mathematical foundations](02_math_foundations.md)
- [Module 3 — Data, signals & features](03_data_features.md)
- [Module 4 — Evaluation: offline → online](04_evaluation.md)

### Part B — Classical algorithms
- [Module 5 — Content-based filtering](05_content_based.md)
- [Module 6 — Collaborative filtering: neighborhood methods](06_collaborative_filtering.md)
- [Module 7 — Matrix factorization & FM family](07_matrix_factorization.md)

### Part C — Deep learning era
- [Module 8 — Neural recommenders & CTR models](08_neural_ctr.md)
- [Module 9 — Sequential & session models](09_sequential.md)
- [Module 10 — Two-tower retrieval at scale](10_two_tower.md)
- [Module 11 — Graph neural networks for recsys](11_gnn.md)
- [Module 12 — LLMs & generative recommenders](12_llm_generative.md)

### Part D — Production architecture
- [Module 13 — The funnel: retrieval → ranking → re-ranking](13_funnel.md)
- [Module 14 — Candidate generation systems](14_candidate_generation.md)
- [Module 15 — Ranking & multi-task learning](15_ranking_mtl.md)
- [Module 16 — Cold start, exploration, debiasing, fairness, freshness](16_coldstart_exploration_bias.md)

### Part E — Industry deep dives
- [Module 17 — Netflix](17_netflix.md)
- [Module 18 — Spotify](18_spotify.md)
- [Module 19 — YouTube + Google](19_youtube_google.md)
- [Module 20 — Apple](20_apple.md)
- [Module 21 — Meta: Feed, Reels, generative recommender](21_meta.md)
- [Module 22 — TikTok / ByteDance](22_tiktok.md)
- [Module 23 — Amazon, Pinterest, LinkedIn, Airbnb, Uber, DoorDash, Etsy](23_marketplace_zoo.md)
- [Module 24 — B2B & outreach startups](24_b2b_outreach.md)

### Part F — Ads (first-class section)
- [Module 25 — Ads foundations: auctions & economics](25_ads_auctions.md)
- [Module 26 — CTR & CVR prediction at depth](26_ctr_cvr_models.md)
- [Module 27 — Bidding, pacing & budget control](27_bidding_pacing.md)
- [Module 28 — Attribution & measurement](28_attribution_measurement.md)
- [Module 29 — Privacy & post-cookie advertising](29_privacy_ads.md)
- [Module 30 — Ads at Google, Meta, Amazon, TikTok, Apple, Microsoft](30_ad_platforms.md)
- [Module 31 — Creatives, fraud, brand safety](31_creative_fraud_safety.md)

### Part G — Tech stack & MLOps
- [Module 32 — The recsys tech stack](32_tech_stack.md)
- [Module 33 — Reference architectures by company size](33_reference_architectures.md)

### Part H — Experimentation deep dive
- [Module 34 — A/B testing & experimentation methods by business type](34_ab_testing_methods.md)

---

## Quizzes

- [`quizzes/README.md`](quizzes/README.md) — Quiz index
- [Quiz 01 — Foundations (Modules 1-4)](quizzes/01_foundations.md)
- [Quiz 02 — Classical algorithms (Modules 5-7)](quizzes/02_classical.md)
- [Quiz 03 — Deep learning (Modules 8-12)](quizzes/03_deep_learning.md)
- [Quiz 04 — Production architecture (Modules 13-16)](quizzes/04_production.md)
- [Quiz 05 — Industry deep dives (Modules 17-24)](quizzes/05_industry.md)
- [Quiz 06 — Ads (Modules 25-31)](quizzes/06_ads.md)
- [Quiz 07 — Tech stack (Modules 32-33)](quizzes/07_tech_stack.md)
- [Quiz 08 — A/B testing & experimentation (Module 34)](quizzes/08_ab_testing.md)

---

## Code

- [`code/README.md`](code/README.md) — Code overview + setup
- [`code/requirements.txt`](code/requirements.txt) — Python dependencies

| File | Module | Demonstrates |
|------|--------|--------------|
| [`05_content_based.py`](code/05_content_based.py) | 5 | TF-IDF + cosine; dense-embedding variant |
| [`06_neighborhood_cf.py`](code/06_neighborhood_cf.py) | 6 | Item-based kNN on a ratings matrix |
| [`07_matrix_factorization.py`](code/07_matrix_factorization.py) | 7 | SGD-trained MF with biases |
| [`07b_bpr.py`](code/07b_bpr.py) | 7 | Bayesian Personalized Ranking with negative sampling |
| [`08_dlrm_lite.py`](code/08_dlrm_lite.py) | 8 | DLRM-style ranker in PyTorch |
| [`09_sasrec.py`](code/09_sasrec.py) | 9 | Toy SASRec sequential recommender |
| [`10_two_tower.py`](code/10_two_tower.py) | 10 | Two-tower retrieval + in-batch negatives + LogQ |
| [`11_lightgcn.py`](code/11_lightgcn.py) | 11 | Minimal LightGCN with sparse propagation |
| [`12_generative_rec.py`](code/12_generative_rec.py) | 12 | Generative next-item transformer (TIGER kernel) |
| [`25_auction_sim.py`](code/25_auction_sim.py) | 25 | GSP vs VCG vs first-price auction simulator |
| [`27_pacing_pid.py`](code/27_pacing_pid.py) | 27 | PID budget pacing controller |
| [`28_mmm_demo.py`](code/28_mmm_demo.py) | 28 | MMM with adstock + Hill saturation |
| [`bandit_thompson.py`](code/bandit_thompson.py) | 16 | Thompson sampling vs ε-greedy vs greedy |

---

## Research inputs

Deep-research reports built during the topic 03 session (in `research_inputs/03_recommendation_engines/` at repo root):

- [`01_netflix_spotify.md`](../../research_inputs/03_recommendation_engines/01_netflix_spotify.md) — Netflix + Spotify production architectures
- [`02_youtube_meta_tiktok.md`](../../research_inputs/03_recommendation_engines/02_youtube_meta_tiktok.md) — YouTube, Meta, TikTok deep dive
- [`03_apple_amazon_pinterest_linkedin_airbnb_uber.md`](../../research_inputs/03_recommendation_engines/03_apple_amazon_pinterest_linkedin_airbnb_uber.md) — Apple, Amazon, Pinterest, LinkedIn, Airbnb, Uber, DoorDash, Etsy
- [`04_ads_deep_dive.md`](../../research_inputs/03_recommendation_engines/04_ads_deep_dive.md) — Full ads ecosystem deep dive (9 parts)
- [`05_latest_research_2023_2026.md`](../../research_inputs/03_recommendation_engines/05_latest_research_2023_2026.md) — Cutting-edge recsys research 2023-2026
- [`06_b2b_outreach_techstack.md`](../../research_inputs/03_recommendation_engines/06_b2b_outreach_techstack.md) — B2B/outreach + production tech stack

---

## Suggested reading orders

**Architect interview prep (4-6 weeks):**
A1-A4 → C8 → C10 → C12 → D13-D16 → E17 → E19 → E21 → F25-F26 → G32-G33 → H34

**Ads-side / monetization-leaning role:**
A1-A4 → C8 → C10 → C12 → F25 → F26 → F27 → F28 → F29 → F30 → F31 → H34

**ML engineer fundamentals (with hands-on code):**
A1-A4 → B5-B7 → C8-C10 → D13-D16 → run `code/05_content_based.py`, `06_neighborhood_cf.py`, `07_matrix_factorization.py`, `10_two_tower.py`, `09_sasrec.py`

**Marketplace / two-sided platform:**
A1-A4 → C10 → D13-D16 → E23 (Airbnb, Uber, DoorDash) → H34 (switchback, geo experiments)

**B2B / startup founder:**
A1-A4 → B5-B7 → C10 → D13-D16 → E24 → G32-G33 → H34
