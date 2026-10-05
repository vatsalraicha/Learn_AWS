# Module 18 — Spotify

> A massive catalog (~100M+ tracks, ~6M podcasts), low-stakes-but-high-frequency sessions, severe cold-start pressure (~120k uploads/day). Spotify invested heavily in audio content embeddings, sequence models, and bandit-driven shelf assembly. The 2023 AI DJ is the most visible generative-recsys product launch to date.

---

## 1. The origin story: Echo Nest + Discover Weekly

Spotify acquired The Echo Nest (2014, ~$100M). Discover Weekly launched July 2015 — a personalised 30-track playlist every Monday. Original build:

- **CF** over user-playlist and user-track matrices via logistic matrix factorisation ([Johnson NIPS 2014](https://stanford.edu/~rezab/nips2014workshop/submits/logmat.pdf)).
- **NLP over playlist titles/descriptions** — playlists as documents, tracks as words → word2vec-style track embeddings.
- **Audio analysis** — Echo Nest fingerprinting + deep audio embeddings for cold-start tracks.

Combined via weighted retrieval + ranking with editorial filters (explicit tracks, already-played-recently, taste profile).

---

## 2. BaRT — Bandits for Recommendations as Treatments

Spotify Home is a stack of shelves (Made For You, Jump back in, Discover, New Releases for You). **BaRT** is the contextual-bandit framework that assembles Home.

Canonical paper: [McInerney et al. RecSys 2018](https://dl.acm.org/doi/10.1145/3240323.3240354). "Explore, Exploit, and Explain: Personalising Explainable Recommendations with Bandits."

- Each impression of (shelf, position, card) is a contextual-bandit decision.
- Multi-objective reward: stream rate, save rate, satisfaction, downstream session quality.
- Context: user state, time of day, device, recent activity, learned user embedding.
- Integrates **explanations** — the shelf title itself is a treatment ("Because you like X" vs "Recommended for you" vs "Trending"); bandit picks both items and framing.

By 2022-2024, BaRT moved to **neural contextual bandits** with longer-horizon counterfactual reward modeling.

---

## 3. Audio content embeddings — the cold-start solution

100M+ tracks, ~120k uploads/day. Pure CF can't reach new uploads. Audio embeddings are how Spotify gives a new track a useful vector on day 1.

Lineage:
- **Echo Nest audio analysis** — DSP features (tempo, key, loudness, sections, beats).
- **musicnn** (Pons & Serra 2019) — CNN on Million Song Dataset / MagnaTagATune for tag prediction.
- **OpenL3** (Cramer et al. ICASSP 2019) — self-supervised audio-visual embeddings.
- **CLMR / MULE / MERT** (2021-2024) — contrastive/masked self-supervised learning on raw audio at scale. Spotify-internal variants in talks by Won, Ferraro, Bogdanov.

Used for:
- Cold-start retrieval (acoustic neighbours propagate CF signal).
- Mood/genre attribute prediction.
- Sequence-model conditioning (track ID embedding + audio embedding fed jointly).

---

## 4. Podcast recommendation — a separate problem

Sessions are longer (30 min - 2 hr), catalog ~6M shows, discovery slower, audio is spoken language not music.

Pipeline:
- Separate retrieval keyed on (show, episode).
- Heavy use of **transcripts** — every podcast auto-transcribed, text embeddings (multilingual sentence-BERT-style).
- Topical/taste taxonomy learned over transcripts + editorial overlay.
- Separate ranker for podcast shelves; a top-level routing model balances music vs podcast inventory on the unified Home.

---

## 5. Sequential modeling and the AI DJ (2023)

Music is sequential — "what plays next" is the dominant question.

Stack:
- **Track2Vec / song2vec** — item embeddings via skip-gram on listening sessions.
- **Sequence transformers** — BERT4Rec-style and decoder-only over (user, session, track) sequences to predict next track.
- Conditioned on the anchor (playlist/autoplay context), user embedding, recent session.

### 5.1 AI DJ (Feb 2023)

Three subsystems:

1. **Track sequencing** — session-aware ranker conditioned on listening history, DJ "show" context, inferred mood. Bandit-driven explore/exploit.
2. **Narrative / commentary generation** — LLM generates per-segment scripts from a structured prompt with track metadata, artist context, user history ("first time you've heard this artist," "played this 5× last week"). Guardrails for factuality.
3. **Voice synthesis** — Sonantic (acquired June 2022, ~$50M); SSML-like markup controls pacing/emphasis.

User skip → telemetry feeds back into the session ranker.

[Spotify newsroom announcement](https://newsroom.spotify.com/2023-02-22/spotify-debuts-a-new-ai-dj-right-in-your-pocket/).

---

## 6. Two-tower retrieval at 100M+ track scale

- **User tower**: long-range user history (transformer encoder), context (time, device, prior session) → ~256d vector.
- **Item tower**: track ID + artist + album + audio embedding + metadata → same space.
- Item vectors precomputed and ANN-indexed; user vector computed at request.

Powers Discover Weekly, Daily Mixes, Home shelves, Autoplay/Radio. Multiple variants per surface (different reward heads, different negative sampling).

---

## 7. ANN: Annoy → Voyager

**Annoy** (Bernhardsson, 2013) — random projection trees, Spotify's workhorse for the 2010s. By early 2020s HNSW dominated ANN-benchmarks.

**Voyager** ([open-sourced Oct 2023](https://engineering.atspotify.com/2023/10/introducing-voyager-spotifys-new-nearest-neighbor-search-library/)) is Spotify's HNSW replacement:
- Typed indexes.
- Lower memory.
- Faster recall at same QPS.
- Ergonomic Python/Java API.

---

## 8. Cold start

- **New tracks**: audio embedding → immediate placement in joint space → acoustic neighbours propagate CF. Artist embedding transfers prior listening.
- **New artists**: audio + artist metadata (label, country, genre tags). "Fresh Finds" and Discover Weekly reserve slots for under-represented artists.
- **New users**: onboarding asks for artists/genres; first-week editorial + popularity heavy; rapid personalisation after a few sessions.

---

## 9. Tech stack

| Layer | Tool |
|---|---|
| Cloud | GCP (migrated from on-prem in 2016) |
| Warehouse | BigQuery |
| Streaming | Pub/Sub + Dataflow / Beam |
| Workflow | Luigi (originally; Spotify OSS 2012) + Dataflow + Flyte/Kubeflow |
| ML framework | TensorFlow primary, growing PyTorch |
| ML orchestration | Kubeflow Pipelines on GKE |
| Internal dev portal | Backstage (Spotify OSS, 2020) |
| ANN | Voyager (HNSW) — replaced Annoy 2023 |
| Feature store | Internal (Hendrix → Jukebox) |
| Experimentation | Internal A/B platform |

---

## 10. Multi-objective fairness

Spotify publicly discusses **artist fairness** — preventing winner-takes-all distribution:

- Discover Weekly reserves slots for under-represented artists.
- "Fresh Finds" surface dedicated to new artists.
- Editorial overlays for genre / regional diversity.

Anderson et al. WWW 2020 ([algorithmic effects on consumption diversity](https://research.atspotify.com/algorithmic-effects-on-the-diversity-of-consumption-on-spotify/)) is a useful reference on the trade-offs.

---

## 11. Important papers / posts

- McInerney et al. RecSys 2018 — BaRT.
- Anderson et al. WWW 2020 — algorithmic diversity.
- McInerney et al. KDD 2020 — counterfactual slate eval ([arXiv 2007.12986](https://arxiv.org/abs/2007.12986)).
- Spotify Engineering blog 2023 — Voyager release.
- Newsroom 2023 — AI DJ launch.

---

## 12. Sanity check

1. Spotify's cold-start problem is severe (120k uploads/day). What's the architectural answer that "give every new track a useful vector on day 1"?
2. BaRT picks both *items and explanations*. Why is the explanation framed as part of the treatment?
3. Why did Spotify replace Annoy with Voyager, and what's the underlying ANN algorithm?
4. The AI DJ is a three-subsystem product. What are they, and how do user skips feed back?
5. Spotify reserves slots for under-represented artists. What metric in Module 16's fairness toolkit does this map to?
