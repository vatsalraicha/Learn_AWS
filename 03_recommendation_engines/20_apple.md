# Module 20 — Apple

> The outlier. Apple does not centralise behavioural data the way Meta or Google do. The entire stack flows from that constraint: heavy on-device modeling, differential privacy for telemetry, attested-no-retention cloud for heavy inference, and editorial curation as the quality floor. Worth studying because every privacy-conscious company in 2026 wants to imitate part of this.

---

## 1. The strategic stance

Apple monetises **the device** (hardware margin) and **services** (App Store cut, Apple Music/News/TV+ subscriptions, Apple Search Ads). It does **not** monetise behavioural data the way ad-funded platforms do.

Architecture flows from monetisation:
- On-device personalisation by default.
- Differential privacy for any telemetry leaving the device.
- Private Cloud Compute (PCC) for heavier inference without retention.
- Editorial curation as quality floor where personalisation is shallow.

---

## 2. App Store recommendations

Three primary surfaces:

- **Today tab** — editorially curated daily feed; ML personalises ordering and which stories surface for which users.
- **Apps / Games tabs** — Charts (Top Free, Top Paid, Top Grossing) plus algorithmic shelves: "Apps We Love," "Editor's Choice," "Because You Downloaded X."
- **Search** — exact-name match (high precedence) + keyword relevance from app metadata + ML re-ranker (install rate, post-install engagement, retention, ratings, freshness, personalisation).

Architectural notes:
- **On-device personalisation** for personalised shelves. The signal "you downloaded X" lives on-device; candidate generation runs server-side (population-level), personalised re-ranking happens on-device.
- Ranker weights **post-install engagement and retention**, not just install rate — one of the strongest disincentives against clickbait creatives in any app store.
- Apple Search Ads bid into the same slate at the top (Module 30).

---

## 3. Apple Music

Personalisation combines:

- **Collaborative filtering** over listening events.
- **Audio content embeddings**. Apple acquired Shazam in 2018; spectrogram-derived track embeddings allow cold-start.
- **Editorial curation**. Apple Music maintains a large editorial staff producing playlists; ML decides which to surface but the playlist itself is human-curated. Different from Spotify's heavier algorithmic-playlist tilt.
- **Personalised stations**. "Discovery Station" is a sequence model over listen history.

See [machinelearning.apple.com](https://machinelearning.apple.com) for relevant papers on music embeddings, multimodal content understanding, and on-device personalisation.

---

## 4. Apple News

Top Stories on the Today tab are picked by a newsroom. Below the fold ML personalises story ordering based on:
- Topic interests inferred on-device from reading history.
- Source preferences (publishers followed, blocked).
- Time-of-day and reading-context patterns.

Personalisation happens **on-device**. Differentially-private-aggregated telemetry about which stories perform in which interest segments flows back to Apple; the per-user reading log does not.

---

## 5. Differential privacy and on-device ML

Apple's foundational public work: **"Learning with Privacy at Scale"** (Apple ML Journal, 2017). Local DP for telemetry across emoji and word suggestions, Safari crash reports, Health typing data.

### 5.1 Local DP

Apply noise **on the device** before any data leaves. The server only ever sees noisy reports; aggregation across millions of devices recovers useful population statistics (counts, top-k) while bounding per-user leakage by an epsilon budget.

Mechanisms:
- **Count-Mean-Sketch (CMS)** and **Hadamard-Count-Mean-Sketch (HCMS)** for LDP frequency estimation.
- **Private Set Union / Sequence Fragment Puzzle** for novel-vocabulary discovery.

### 5.2 Consequence for recsys

Apple cannot run the same per-user gradient-based personalisation Meta or Google do on server-side training data. Instead:
- Train **population-level models** server-side using DP-aggregated signal.
- **Personalise on-device** — fine-tuning small heads, ranking candidate sets locally, or running k-NN against a user's local embedding cache.

---

## 6. Private Cloud Compute (PCC) and Apple Intelligence

Apple Intelligence (WWDC 2024, shipped iOS 18, expanded through 2025-2026) introduces a tiered architecture:

1. **On-device foundation models** (~3B parameters) handle the majority of requests on Neural Engine.
2. **Private Cloud Compute** — Apple-trained models on Apple-controlled servers. Data encrypted in transit, processed in attested enclaves, not retained, with publicly verifiable binaries for auditing. **No SRE shell access**.
3. **ChatGPT / partner fallback** is opt-in per request.

PCC matters for recsys because it lets Apple run heavier-than-on-device personalised inference (a larger ranker for Siri Suggestions, more capable LLM for query understanding in News/Spotlight) **without compromising the privacy guarantee** that user data isn't retained server-side.

The 2025-2026 expansion brings PCC-tier ranking into Siri Suggestions, Mail prioritisation, Spotlight.

---

## 7. CoreML, Create ML, MLX — the on-device ML pipeline

- **CoreML** — on-device inference runtime with INT8 quantisation, palettisation, stateful KV-cache support (added 2024 for transformer decoders), tight Neural Engine integration.
- **Create ML** — Apple's no-code training tool. Includes a "Recommender" template that trains an ALS/MF-style CF model so third-party developers can ship per-app on-device personalisation.
- **MLX** (released 2023) — Apple Silicon's NumPy-like array framework with autodiff and unified-memory awareness.

---

## 8. Strategic implications for an AI architect

The Apple stack is worth understanding precisely because it is the **counter-example** to centralised-data orthodoxy:

- **Model size budget** dictated by Neural Engine memory and battery.
- **Retrieval candidates** may need to be sent to the device rather than scored server-side.
- **Telemetry budget** is finite (DP epsilon is consumed across all endpoints).
- **Editorial curation** is a quality floor when per-user signal is weak.
- **PCC** opens a middle tier between on-device and full cloud.

Recommendation-system architecture is **downstream of the privacy / data-collection posture the company has chosen**. Apple, Meta, TikTok have different postures → different stacks.

---

## 9. Sanity check

1. Why does Apple keep "you downloaded X" on-device rather than logging it server-side?
2. Local DP applies noise on the device before any data leaves. What does Apple recover at the server, and what does it sacrifice?
3. Private Cloud Compute does heavier inference than on-device. What's the privacy guarantee that PCC offers that vanilla cloud doesn't?
4. Why is editorial curation more important at Apple Music than at Spotify, all else equal?
5. The Create ML "Recommender" template ships with iOS. Why does Apple invest in third-party developer recsys when it doesn't sell ads?
