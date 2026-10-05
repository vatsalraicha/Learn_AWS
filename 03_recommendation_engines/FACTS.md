# FACTS — Recommendation Engines & Ads

> Atomic, citable claims. When a module needs a date, number, or paper name, it points here. If a fact below is wrong or stale, fix it *here first*, then the modules. Last full audit: **2026-05-11**.

---

## 1. Canonical papers — recommenders

| Year | Paper | Authors | Why it matters | Source |
|------|-------|---------|----------------|--------|
| 2003 | Amazon.com Recommendations: Item-to-Item Collaborative Filtering | Linden, Smith, York | First widely cited industrial recsys; the "people who bought X also bought Y" architecture | IEEE Internet Computing |
| 2008 | Collaborative Filtering for Implicit Feedback Datasets | Hu, Koren, Volinsky | The ALS-for-implicit-feedback paper; the math behind every "weighted matrix factorization" library | ICDM 2008 |
| 2009 | Matrix Factorization Techniques for Recommender Systems | Koren, Bell, Volinsky | The summary of the Netflix Prize era; SVD/SVD++/timeSVD++ | IEEE Computer 42(8) |
| 2009 | BPR: Bayesian Personalized Ranking from Implicit Feedback | Rendle et al. | The pairwise-ranking loss that made implicit-feedback MF actually work | UAI 2009 |
| 2010 | Factorization Machines | Rendle | Generalizes MF to handle arbitrary feature interactions | ICDM 2010 |
| 2015 | Field-aware Factorization Machines for CTR Prediction | Juan, Zhuang, Chin, Lin | Won several Kaggle CTR competitions; introduced field embeddings | RecSys 2016 |
| 2016 | Wide & Deep Learning for Recommender Systems | Cheng et al. (Google Play) | The first widely deployed deep + linear architecture; established the pattern | DLRS 2016 |
| 2016 | Deep Neural Networks for YouTube Recommendations | Covington, Adams, Sargin | The canonical two-stage (candidate gen + ranking) deep recsys; everyone copies its diagram | RecSys 2016 |
| 2017 | DeepFM: A Factorization-Machine based Neural Network for CTR | Guo et al. (Huawei) | Replaced Wide's manual feature crosses with an FM | IJCAI 2017 |
| 2017 | Neural Collaborative Filtering | He et al. | Cited 7000+ times. **Rendle's 2020 reproducibility study showed plain dot-product MF beats NCF** when properly tuned — historically important caution | WWW 2017 / counter: RecSys 2020 |
| 2018 | Deep Interest Network for Click-Through Rate Prediction | Zhou et al. (Alibaba) | Attention over user history; production at Alibaba | KDD 2018 |
| 2018 | Real-time Personalization using Embeddings for Search Ranking at Airbnb | Grbovic, Cheng | Listing embeddings via skip-gram on session sequences | KDD 2018 |
| 2018 | PinSage: Graph Convolutional Neural Networks for Web-Scale Recommender Systems | Ying et al. (Pinterest) | First production-scale GNN recsys; 3B+ nodes | KDD 2018 |
| 2018 | Sampling-Bias-Corrected Neural Modeling for Large Corpus Item Recommendations | Yi et al. (Google) | The two-tower with LogQ correction paper | RecSys 2019 |
| 2018 | SASRec: Self-Attentive Sequential Recommendation | Kang, McAuley | The transformer-for-sequences baseline; still tough to beat | ICDM 2018 |
| 2019 | BERT4Rec: Sequential Recommendation with Bidirectional Encoder | Sun et al. (Alibaba) | Masked-LM-style sequential recsys | CIKM 2019 |
| 2019 | DLRM: Deep Learning Recommendation Model | Naumov et al. (Meta) | Open-sourced reference for sparse-embedding-heavy CTR | arXiv 1906.00091 |
| 2019 | Recommending What Video to Watch Next: A Multitask Ranking System | Zhao et al. (YouTube) | MMoE for multi-task ranking; the production reference | RecSys 2019 |
| 2019 | Top-K Off-Policy Correction for a REINFORCE Recommender | Chen et al. (YouTube) | RL for long-term user value; the off-policy correction recipe | WSDM 2019 |
| 2020 | LightGCN: Simplifying and Powering Graph Convolution Network | He et al. | Strips NGCF down — still a strong baseline | SIGIR 2020 |
| 2020 | PinnerSage: Multi-Modal User Embedding Framework | Pal et al. (Pinterest) | Cluster users into multiple interest embeddings | KDD 2020 |
| 2022 | DCN-V2: Improved Deep & Cross Network and Practical Lessons | Wang et al. (Google) | The current Deep & Cross production form | WWW 2021 |
| 2022 | Monolith: Real-Time Recommendation System with Collisionless Embedding Table | Liu et al. (ByteDance) | Real-time online training; collisionless cuckoo hash for embeddings | arXiv 2209.07663 / DLRS 2022 |
| 2023 | Recommender Systems with Generative Retrieval (TIGER) | Rajput et al. (Google) | Semantic IDs via RQ-VAE + autoregressive generation; the start of generative retrieval | NeurIPS 2023 |
| 2023 | P5: Pretrain, Personalized Prompt, and Predict Paradigm | Geng et al. | Multi-task recommendations as text-to-text via T5 | RecSys 2022 / extended 2023 |
| 2024 | Actions Speak Louder than Words: Trillion-Parameter Sequential Transducers for Generative Recommendations | Zhai et al. (Meta) | HSTU — Meta's generative recommender replacing DLRM in production; new scaling laws | ICML 2024 (arXiv 2402.17152) |
| 2024 | Wukong: Towards a Scaling Law for Large-Scale Recommendation | Zhang et al. (Meta) | Scaling-law paper for recsys — shows power-law improvements up to ~100B params | ICML 2024 (arXiv 2403.02545) |
| 2024 | LiRank: Industrial Large Scale Ranking Models at LinkedIn | Borisyuk et al. | LinkedIn's production ranking framework | KDD 2024 |
| 2024 | Foundation Model for Personalized Recommendation | Netflix Tech Blog | Netflix's unified-model approach (March 2025 publication) | netflixtechblog.com |

---

## 2. Canonical papers — Ads / CTR

| Year | Paper | Authors | Why | Source |
|------|-------|---------|-----|--------|
| 2013 | Ad Click Prediction: a View from the Trenches | McMahan et al. (Google) | FTRL-Proximal; the operational reality of logistic-regression ads ranking | KDD 2013 |
| 2014 | Practical Lessons from Predicting Clicks on Ads at Facebook | He et al. (Meta) | GBDT + LR hybrid; feature transforms at scale | ADKDD 2014 |
| 2018 | xDeepFM: Combining Explicit and Implicit Feature Interactions | Lian et al. (Microsoft) | Compressed Interaction Network (CIN) | KDD 2018 |
| 2019 | AutoInt: Automatic Feature Interaction Learning via Self-Attentive | Song et al. | Multi-head self-attention over feature embeddings | CIKM 2019 |
| 2019 | ESMM: Entire Space Multi-Task Model | Ma et al. (Alibaba) | The fix for sample selection bias in CVR modeling | SIGIR 2018 |
| 2020 | DCN-V2 | Wang et al. (Google) | Practical replacement for DCN-V1 | WWW 2021 |
| 2020 | FiBiNET: Combining Feature Importance and Bilinear feature Interaction | Huang et al. (Sina Weibo) | SENet attention over fields | RecSys 2019 |
| 2021 | MaskNet: Introducing Feature-wise Multiplication to CTR | Wang, Zhang, Sun (Weibo) | Mask-block multiplicative interactions | DLP-KDD 2021 |
| 2022 | FinalMLP: An Enhanced Two-Stream MLP Model for CTR | Mao et al. | Shows tuned MLPs match complex architectures | AAAI 2023 |
| 2022 | DIN/DIEN/BST extensions, SIM | Alibaba | Long-history attention (search-based interest model) | KDD 2020 (SIM) |
| 2023 | TWIN: TWo-stage Interest Network for Lifelong User Behavior Modeling | Kuaishou | Long-sequence CTR with sub-linear attention | KDD 2023 |
| 2023 | PEPNet: Parameter and Embedding Personalized Network for Infusing with Personalized Prior Information | Chang et al. (Kuaishou) | Multi-domain CTR with gating | KDD 2023 |

---

## 3. Key benchmarks & datasets

| Dataset | Domain | Use | Notes |
|---------|--------|-----|-------|
| MovieLens (100k / 1M / 10M / 20M / 25M / latest) | Movies | Explicit-feedback CF | Still the most-cited research benchmark; small enough for laptops |
| Netflix Prize (deprecated) | Movies | MF history | Withdrawn 2010 after re-identification concerns |
| Amazon Reviews (Ni et al. 2019; updated 2023) | E-commerce | Implicit + reviews | 233M reviews; the standard real-world test |
| Yelp | Local | Implicit + reviews | Open dataset |
| LastFM-1K / LastFM-1B | Music | Sequential, session | Plays-as-implicit |
| RetailRocket | E-commerce | Sessions, conversions | Smaller |
| Criteo 1TB | Display CTR | The CTR benchmark | Hashed sparse features |
| Avazu | Mobile CTR | CTR | Smaller cousin of Criteo |
| Taobao Display Ad / Taobao User Behavior | Sequence | DIN/DIEN papers used these | Open from Alibaba |
| KuaiRand / KuaiRec | Short video | Less biased eval | Has random-recommendation logs for unbiased eval |
| MIND (Microsoft News) | News | News rec | Cold start heavy |
| H&M Personalized Fashion (Kaggle 2022) | Fashion | Multimodal | Image + text |
| Yahoo! R3 | Music | Unbiased eval | Includes random exposure |

---

## 4. Latency & scale benchmarks (industry-published)

| Metric | Number | Source / Date |
|--------|--------|---------------|
| YouTube candidate pool | ~Billions of videos → ~hundreds retrieved | Covington et al. 2016 (still cited 2024) |
| Pinterest PinSage graph | 3B+ nodes, 18B+ edges | PinSage 2018 |
| Meta DLRM embedding table size in 2022 | 12 TB | Meta engineering posts |
| TikTok Monolith real-time update freshness | minutes | Monolith paper 2022 |
| Typical ranking-stage p99 latency budget | <100 ms | Industry consensus |
| Typical retrieval p99 latency budget | 20-50 ms | Industry consensus |
| Reranking p99 budget | 10-30 ms | Industry consensus |
| Total feed assembly budget for mobile | 200-500 ms | Industry consensus |
| Real-time bidding (RTB) per-bid budget | 100 ms (OpenRTB spec) | IAB Tech Lab |

---

## 5. Auction & ad-tech facts

- **GSP vs VCG**: Google ran GSP for AdWords/Search since 2002. Facebook switched its ads system from GSP to VCG in **2018**.
- **First-price auctions in display**: Industry shift began ~2017-2018 driven by header bidding. Google AdX moved to first-price in **September 2019** for display.
- **OpenRTB**: IAB-maintained protocol. Current 2.x; 3.0 specified but not widely adopted as of 2026.
- **iOS ATT** (App Tracking Transparency) launched with **iOS 14.5 in April 2021**; opt-in rate stabilized at roughly 25-30% globally.
- **SKAdNetwork 4.0** released alongside iOS 16.1 (Oct 2022) — added hierarchical conversion values (coarse + fine + lock).
- **AdAttributionKit** introduced at WWDC24 (iOS 17.4+, June 2024); supersedes SKAdNetwork for new integrations.
- **Privacy Sandbox (Web)**: Google **abandoned plans to deprecate third-party cookies in Chrome** (July 2024) but Privacy Sandbox APIs (Topics, Protected Audience, Attribution Reporting) shipped anyway.
- **Topics API**: ~470 ad-relevant topics (taxonomy v2, 2024 update).
- **Protected Audience API** (formerly FLEDGE): on-device auction for retargeting use cases.

---

## 6. Frameworks & libraries (with versions / notes as of 2026-05)

| Library | Version (approx, 2026-05) | What it is |
|---------|---------------------------|------------|
| TorchRec | 1.0+ stable | PyTorch primitives for sharded embedding tables, distributed recsys |
| TensorFlow Recommenders (TFRS) | 0.7+ | High-level Keras recsys API, two-tower idiom |
| TF-Ranking | 0.5+ | Learning-to-rank in TF |
| NVIDIA Merlin (HugeCTR, NVTabular, Models) | Merlin 23.x | GPU-accelerated CTR training |
| RecBole | 1.2+ | Research benchmark suite (78+ algorithms) |
| Microsoft Recommenders | 1.2+ | Open-source recipes (Jupyter notebooks) |
| implicit | 0.7+ | Fast ALS / BPR / LMF on CPU + GPU |
| LightFM | 1.17+ | Hybrid CF + content; CPU-friendly |
| Spotlight | dormant | PyTorch sequence/MF; not actively maintained |
| Cornac | 2.x | Research multi-modal recsys |
| Faiss | 1.8+ | Meta's similarity search; HNSW + IVF-PQ + flat |
| ScaNN | 1.3+ | Google's anisotropic vector quantization; SOTA recall/QPS |
| Annoy | 1.17 | Spotify's original ANN; mostly legacy now |
| Voyager | 2024 release | Spotify's replacement for Annoy |
| Vespa | 8.x | Yahoo/Verizon Media's open-source serving engine (search + recs) |
| Feast | 0.40+ | Open-source feature store (the de-facto OSS choice) |
| Meridian | 1.0 (2024) | Google's open-source MMM |
| Robyn | 3.x (2024) | Meta's R-based MMM |

---

## 7. Industry tech-stack snapshots (publicly disclosed)

| Company | Training | Feature store | Serving | Notable |
|---------|----------|---------------|---------|---------|
| Netflix | Metaflow + Keystone (Flink) | Axion / in-house | Mantis / Eureka | Iceberg + Spark for data; Maestro orchestration |
| Spotify | TensorFlow + Kubeflow on GCP | Internal "Feature Platform" | gRPC service mesh; Annoy → Voyager | BigQuery heavy; Backstage for tooling |
| YouTube/Google | TF + TFX + TFRS | Vertex AI feature store internally derived | Borg + TF Serving + ScaNN | Two-stage canonical |
| Meta | PyTorch + TorchRec + FBGEMM | Tectonic (internal) | Predictor / DLRM serving | MTIA chips, AI hardware vertical |
| TikTok / ByteDance | Internal TF fork + Monolith | Internal | Internal | Real-time training is the differentiator |
| Apple | Internal (Bolt) + CoreML | On-device + private cloud compute (PCC) | On-device | Differential privacy + federated stats |
| Amazon | SageMaker + internal | SageMaker Feature Store + DynamoDB | SageMaker / NEMO | Personalize as productized version |
| Pinterest | PyTorch | Galaxy (internal) | KSP + HNSW | PinSage open-sourced ideas |
| LinkedIn | Spark + TensorFlow + Pro-ML | Frame (internal) | Quantum (serving) | Photon ML open source |
| Airbnb | TensorFlow + Bighead | Zipline | In-house | Listing embeddings via skip-gram |
| Uber | Michelangelo | Palette | In-house | "Real-time predictions for ride pricing" |
| DoorDash | PyTorch + LGBM | Sibyl | In-house | DoubleML for causal ranking |
| Etsy | Spark + PyTorch | Internal | In-house | Multimodal listings |

---

## 8. Calibration & evaluation reference

- **Position bias**: roughly **e^{-α·position}** decay in CTR; reranking models that correct for position use either click models (Cascade, DBN, PBM, UBM) or a position-bias tower.
- **CUPED variance reduction**: typical 30-50% reduction in A/B test required sample size when there's a good pre-period covariate.
- **Offline-online correlation**: known to be weak; a 1% NDCG@10 lift offline may be 0% online. Always run shadow + A/B.
- **NDCG vs MAP vs MRR**: MAP for binary relevance, NDCG for graded relevance, MRR for "find the one good answer" (search-like).
- **Recall@k for retrieval**: industrial targets are usually **Recall@100 ≥ 0.7** or **Recall@1000 ≥ 0.9** for the candidate set fed into ranking.

---

## 9. Volatile / verify-before-citing

The following claims move fast — verify currency before quoting in interviews or docs.

- HSTU has fully replaced DLRM at Meta production scale → verified by Zhai et al. (2024) ICML paper and follow-on Meta engineering blog. Status as of 2026-05: deployed on Ads + Reels; in rollout for Feed.
- Performance Max share of Google Ads spend.
- Advantage+ share of Meta Ads spend.
- Whether Google has fully deprecated third-party cookies — **as of 2026-05, cookies still supported in Chrome; Privacy Sandbox APIs ship in parallel**.
- Any "X has joined / left / been acquired" claim about ad-tech vendors.

---

## 10. Experimentation methods quick reference

| Method | Best for | Source |
|--------|----------|--------|
| Bucket A/B | Default for independent users | — |
| Interleaving (team-draft) | Ranking comparisons; ~100× sample-efficient | Radlinski et al. 2008 |
| Switchback | Marketplaces (Uber, DoorDash, Airbnb) | Uber Eng 2018+ |
| Cluster randomisation | Social / marketplace SUTVA violations | Meta, LinkedIn |
| Geo experiments + synthetic control | Country-level rollouts, ads | Abadie 2010; CausalImpact 2015 |
| CUPED variance reduction | Squeeze sample-size by 30-50% | Deng/Xu/Kohavi/Walker, Microsoft 2013 |
| Sequential testing (mSPRT) | Peeking without alpha inflation | Howard, Ramdas et al. 2021 |
| Permanent holdouts | Long-horizon retention/LTV | Netflix, Airbnb, Booking |
| Surrogate index | Estimate long-term from short-term proxies | Athey, Chetty, Imbens NBER 2019 |
| Lift studies / Ghost ads | Ads incrementality | Johnson, Lewis, Nubbemeyer eBay 2017 |
| Contextual bandits | Continuous experimentation, tactical | Li et al. LinUCB 2010; Thompson 1933 |

Canonical book: Kohavi, Tang, Xu — *"Trustworthy Online Controlled Experiments"* (2020).

## 11. Internal experimentation platforms (publicly known)

| Company | Platform | Distinctive feature |
|---------|----------|---------------------|
| Microsoft / LinkedIn | ExP | CUPED's birthplace; "Trustworthy Online Controlled Experiments" book material |
| Netflix | XP | Heavy interleaving; thousands concurrent |
| Airbnb | ERF | ~700 concurrent; published architecture |
| Booking.com | ETF | >1000 simultaneous A/B; test-driven culture |
| Uber | XP / Morpheus | Switchback + synthetic control + classical |
| DoorDash | Curie | Specialised for switchback + causal |
| Meta | Deltoid / PlanOut | PlanOut OSS but stale; Deltoid internal |
| Google | Overlapping experiments | Tang et al. KDD 2010; tens of thousands layered |

## 12. Math one-liners (cross-reference for modules)

| Concept | One-line form |
|---------|---------------|
| Cosine similarity | `cos(u,v) = u·v / (‖u‖‖v‖)` |
| Predicted rating in MF | `r̂_ui = μ + b_u + b_i + p_u · q_i` |
| ALS with implicit feedback (Hu/Koren/Volinsky) | Minimise `Σ c_ui (p_ui − x_u·y_i)² + λ(‖X‖² + ‖Y‖²)` where `p_ui = 1{r_ui>0}`, `c_ui = 1 + α r_ui` |
| BPR loss | `−log σ(x̂_ui − x̂_uj)` for positive `i`, negative `j` |
| FM equation | `ŷ = w_0 + Σ w_i x_i + Σ_{i<j} ⟨v_i, v_j⟩ x_i x_j` |
| Sampled softmax (two-tower) | `p(i|u) ∝ exp(s(u,i) − log q(i))` (LogQ correction) |
| MMR | `argmax_{i ∈ R\S} [λ sim(i,q) − (1−λ) max_{j∈S} sim(i,j)]` |
| GSP price for slot k | second-highest pCTR×bid below slot k, scaled by quality |
| VCG payment for slot k | the externality the bidder imposes on others |
