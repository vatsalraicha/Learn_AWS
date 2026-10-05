# Module 22 — TikTok / ByteDance

> The recommender system most users have direct emotional opinions about. Most of its "magic" is engineering — particularly the **real-time training** loop (Monolith) and **aggressive exploration** for new content. The For You Page is a contextual bandit + sequence model + multi-source retriever wrapped in a re-ranker.

---

## 1. What's actually public

Less than for Netflix or Meta. The clearest signals come from:
- The **Monolith** paper (2022, ByteDance Research).
- ByteDance's [Volcano Engine](https://www.volcengine.com) enterprise documentation (English limited).
- Academic publications from ByteDance Research on long-sequence modelling, multi-task, off-policy correction.

Public reality: TikTok uses a two-tower retriever, a multi-task DLRM-style ranker, and a re-ranker. The differentiators are **training infrastructure** (Monolith) and **content half-life handling** (aggressive exploration for fresh content).

---

## 2. Monolith — real-time training (2022)

[Liu et al. DLRS@RecSys 2022 / arXiv 2209.07663](https://arxiv.org/abs/2209.07663). [OSS at github.com/bytedance/monolith](https://github.com/bytedance/monolith).

### 2.1 Collisionless hashing

Standard pipelines hash high-cardinality IDs into a fixed-size table, causing collisions and quality loss. Monolith uses a **dynamic, expirable hash table** keyed by raw IDs:

- New IDs inserted on the fly only when occurrence count crosses a threshold (filters one-off junk IDs).
- IDs not touched for a window are evicted to bound memory.
- Frequency-based filter prevents memorising one-time tokens.

### 2.2 Online training

**Parameter server** architecture where:
- A streaming joiner labels events as soon as they happen.
- Workers consume labels and push gradients to the PS within seconds.
- Every few minutes a serving snapshot is published — sparse params incrementally, dense params in larger snapshots.
- A/B tests pin the serving snapshot version because the model never stops moving (train-serve skew is the central engineering challenge).

### 2.3 Why this matters

TikTok's content half-life is short (often hours), new creators upload constantly. A daily-batch recommender would systematically under-explore freshness. Monolith's near-online loop is the engineering reason TikTok can promote a brand-new video to global virality within hours.

---

## 3. The For You Page (FYP) and exploration

- **Retrieval**: union of multiple sources — two-tower (user history), trending, creator-follow, similar-to-just-watched, fresh-content, interest-tag. Each produces a few hundred items.
- **Coarse ranking**: a lightweight model trims thousands to a few hundred.
- **Fine ranking**: deep multi-task model produces per-objective probabilities (finish, like, share, comment, follow, dwell-time bucket).
- **Value model**: linear (or low-degree polynomial) combination; uncertainty-aware variants published.
- **Reranker**: creator diversity, topic diversity, integrity, and explicit **exploration** slots reserved for fresh content / new creators / under-explored interests.

### 3.1 What makes TikTok "feel like TikTok"

Exploration:
- New videos from new creators get an initial small-audience test; engagement above a threshold escalates them to larger pools (multi-stage Thompson-sampling-like bandit).
- A user's "interest" is broadened by injecting items outside their dense cluster; conversion of these into long watches reshapes their embedding quickly.

---

## 4. HLLM — Hierarchical LLM for sequential recommendation (2024)

[Chen et al. 2024 / arXiv 2409.12740](https://arxiv.org/abs/2409.12740). ByteDance's published next-gen direction.

- **Item LLM** produces dense item representations from content.
- **User LLM** processes sequences of item representations to predict the next item.

Paralleling Google's TIGER and Meta's HSTU. Not yet confirmed in production at the scale of those.

---

## 5. Douyin, Lemon8, CapCut

- **Douyin** (Chinese app) and TikTok share algorithmic DNA but are **separate code paths** and separate models trained on separate data (regulatory boundary). Douyin's e-commerce integration drives heavier investment in **search + recommendation unification** and in **multi-modal item embeddings** bridging product catalog and short video.
- **Lemon8** (lifestyle / Pinterest-like) reuses the Monolith stack and feature platform; ranker is tuned for image+text rather than video.
- **CapCut** is a creation tool; it produces structured creative metadata (scenes, music, effects) usable as features when those clips are uploaded to TikTok.

---

## 6. ByteDance infra stack — Volcano Engine

- **Volcano Engine** (Huoshan Yinqing) — enterprise face of ByteDance's internal cloud, including managed versions of recsys building blocks:
  - ByteHouse (ClickHouse fork).
  - Real-time data services.
  - Monolith-derivative offerings.
- **BMF / BMTrain / DeepSpeed-style** distributed training internally.
- Heavy use of GPUs (NVIDIA H100/H200 in 2024-2025) plus an in-house accelerator effort.
- Storage: **HDFS-derivative** for batch, **Kafka** for streaming, **ClickHouse / ByteHouse** for analytics.
- Feature platform: internal; architectural diagrams have appeared in talks.

---

## 7. Privacy posture

- **Project Texas / Project Clover** — data localisation for US and EU users into Oracle / European data centres, with restricted access by ByteDance personnel.
- On-device personalisation and limited federated learning experiments, less publicly documented than Apple's.
- ATT compliance similar to Meta's — TikTok also lost cross-app conversion fidelity on iOS.

---

## 8. What an architect should take away

1. **Real-time training is a differentiator** only where content half-life is short. Otherwise daily batch is fine.
2. **Collisionless hashing** beats fixed-size hashing for high-cardinality IDs with one-time-token noise.
3. **The exploration mechanism is part of the product**, not a quality afterthought. TikTok's bandit-driven new-content exploration is what makes FYP feel discovery-oriented.
4. ByteDance's stack diverges from FAANG mainly on real-time training infra and content half-life optimisation.

---

## 9. Sanity check

1. Why does TikTok benefit more from real-time training (minutes from event to model) than Netflix does?
2. Monolith's collisionless hash inserts a new ID only when its count crosses a threshold. What's the trade-off vs always-inserting?
3. The FYP reserves explicit exploration slots for new creators. What metric does this defend against?
4. Douyin and TikTok share architecture but are separate code paths. What is the *engineering* reason, beyond regulation?
5. ByteDance's HLLM paper bears strong resemblance to HSTU and TIGER. What's the common direction of travel for 2024-2026?
