# Module 21 — Meta: Feed, Reels, Generative Recommender

> Meta runs **trillion-parameter** recommenders across Feed, Reels, Instagram Explore, ads. The 2024 HSTU paper marks a paradigm shift — DLRM-style point-wise CTR is being replaced by autoregressive sequence prediction. This module is the most architecturally consequential of the company deep dives.

---

## 1. The DLRM era (2019-2023)

[Naumov et al. 2019](https://arxiv.org/abs/1906.00091) "Deep Learning Recommendation Model" — Meta's open-sourced reference.

Architecture:
- **Sparse features** (user ID, ad ID, page ID) → embedding tables. Single tables of **tens of TBs**, aggregate embeddings in the **multi-trillion-parameter** range.
- **Dense features** → bottom MLP producing a vector at embedding dim.
- **Feature interaction layer**: pairwise dot products of embeddings + dense vector, producing N(N+1)/2 interaction features.
- **Top MLP** → sigmoid → click/conversion probability.

DLRM is **bandwidth-bound on embedding lookups**, which is why Meta's hardware roadmap and the parameter-server / TorchRec investments matter so much.

### 1.1 Embedding tables at trillion scale

- **FBGEMM** — low-precision, embedding-bag-optimised CPU/GPU kernels.
- **TorchRec** — distributed embedding sharding (row, column, table-wise), planner that picks layout, fused communication.
- **PARAM** — benchmark suite that drove MTIA spec.
- **MTIA v1/v2** — Meta's in-house inference (increasingly training) accelerator for embedding-heavy workloads.
- **Zion/ZionEX** ([Mudigere et al. ISCA 2022](https://arxiv.org/abs/2104.05158)) — large-scale training platform.

---

## 2. The 2024 paradigm shift: HSTU

[Zhai et al. ICML 2024](https://arxiv.org/abs/2402.17152) "Actions Speak Louder than Words: Trillion-Parameter Sequential Transducers for Generative Recommendations." The most consequential recsys paper from Meta in years.

### 2.1 Core thesis

DLRM treats recommendation as point-wise binary classification. HSTU reframes it as **next-action prediction over an interleaved sequence of (item, action) tokens** — like a language model.

```
sequence = [item_1, action_1, item_2, action_2, ...]
predict: next item AND next action
```

### 2.2 The HSTU layer

Self-attention is O(n²); for sequences of tens of thousands, that's prohibitive. HSTU uses a **pointwise gated** attention variant whose FLOPs scale **linearly** with sequence length.

### 2.3 Scale and wins

- Up to **1.5T parameters**, mostly in embedding/projection tables.
- Sequence length: tens of thousands of events.
- Trained with LLM-style checkpoint sharding.
- Significant relative E2E engagement gains over the prior DLRM-family ranker.

Status as of 2026-05:
- Deployed on Ads, Reels.
- In rollout for Feed.

### 2.4 Architectural implications

- Retrieval and ranking can collapse into a single autoregressive model.
- Feature engineering shifts from "design 200 hand-crafted counters" to "tokenise more event types correctly."
- Inference latency is heavier per request than DLRM → MTIA, INT8/FP8 quantisation, KV caching become critical.

---

## 3. Wukong — scaling laws for recsys

[Zhang et al. ICML 2024](https://arxiv.org/abs/2403.02545) "Wukong: Towards a Scaling Law for Large-Scale Recommendation."

- Stack of FM-like blocks scaling predictably with parameters and compute.
- **Clean power-law scaling** to ~100B parameters.
- The recsys analogue of LLM scaling laws.

Implication: more params + more data + longer sequence → predictable improvements. You can plan recsys compute investment the same way you plan LLM compute.

---

## 4. Reels and Instagram Explore

### 4.1 Architecture

- **Cold-start for new users.** Content-based embeddings (vision + audio LLM features) serve reasonable Reels from session 1. Aggressive exploration in the first ~10 minutes bootstraps a user embedding from a small number of completed/skipped watches.
- **Cold-start for new content.** Ranker leans on **content embeddings** (CLIP-style vision + audio + caption) and **creator priors** until interaction signal accumulates.
- **Multi-stage funnel.** Two-tower retrieval pulls thousands of candidates; an early-stage lightweight ranker trims to hundreds; a heavyweight DHEN / HSTU scores the final set; a re-ranker enforces diversity and integrity constraints.

[Meta Engineering 2023](https://engineering.fb.com/2023/08/09/ml-applications/scaling-instagram-explore-recommendations-system/) describes consolidating Reels and Explore on a shared modeling and feature-store stack.

### 4.2 DHEN — Deep & Hierarchical Ensemble Network

Ensemble of interaction modules (DCN-v2, AutoInt, Transformer) on shared embeddings. Pre-HSTU production ranker family for many surfaces.

### 4.3 Andromeda

Revealed in 2024 — next-gen retrieval using HSTU-derived generative retrieval, GPU feature processing on NVIDIA Grace Hopper. ~10kx candidate-pool expansion vs prior systems.

---

## 5. Ad ranking

- **Predicted action rate models** (pCTR, pCVR, p_view-15s, p_purchase, etc.).
- **Value model**: advertiser bid × predicted action probability × quality / user-value adjustments. VCG-like auction with reserves.
- **Ad delivery system** (pacing) spreads budget over time using control theory.
- **Aggregated Event Measurement (AEM)** — post-ATT measurement protocol for iOS.
- **Advantage+ campaigns** (2022→) — LLM/automation layer picking audiences and creatives.
- **Lookalike audiences** — embedding-based: centroid of seed audience, cosine similarity, eligibility filter.

[He et al. KDD 2014](https://research.facebook.com/file/273183074306353/practical-lessons-from-predicting-clicks-on-ads-at-facebook.pdf) "Practical Lessons from Predicting Clicks on Ads at Facebook" is still the canonical reference on calibration math (Module 26 details).

---

## 6. LLMs for content understanding

Meta uses LLM/foundation models heavily as **feature extractors**:
- Vision: **DINOv2**, **SAM/SAM 2**, internal image-understanding stack.
- Multimodal: **Llama 3 / 4** + vision encoders caption, classify, embed content; embeddings feed integrity, search, the ranker.
- Generative ads: Llama-driven creative-variant generation in Advantage+; ranker chooses among generated variants.

---

## 7. Re-ranking, diversity, integrity

Final stage on each feed is a **re-ranker** operating on the candidate set as a whole:
- Creator diversity, content-type diversity (Reel vs photo vs text), ad load.
- Integrity classifiers flag borderline content; ranker demotes ("borderline content demotion").
- Constrained optimisation: maximise sum of value-model scores subject to constraints via **Lagrangian relaxation** with online dual updates.

---

## 8. Open-source contributions

- **PyTorch** itself.
- [**TorchRec**](https://github.com/pytorch/torchrec) — distributed sharded embeddings.
- [**FBGEMM**](https://github.com/pytorch/FBGEMM) — embedding kernels.
- [**DLRM reference**](https://github.com/facebookresearch/dlrm).
- [**Velox**](https://github.com/facebookincubator/velox) — C++ vectorised SQL/Dataframe engine used in Spark and Presto.
- **PyTorch 2 + torch.compile** — graph capture + Inductor; modern replacement for Glow.

---

## 9. Sanity check

1. DLRM's bottleneck is bandwidth on embedding lookups, not FLOPs. Why does this drive Meta's hardware (MTIA) and software (FBGEMM, TorchRec) investments?
2. HSTU treats both items and actions as tokens in the sequence. What's the benefit over a sequence of just items?
3. Wukong demonstrated power-law scaling for recsys. What's the practical planning implication for an architect deciding model size?
4. Andromeda enables ~10kx candidate-pool expansion. Where in the funnel does this matter, and how does generative retrieval help?
5. Reels cold-start for new content uses CLIP-style content embeddings. Why is this a more critical investment for Reels than for the Feed feed?
