# Quiz — Industry Deep Dives (Modules 17-24)

## Module 17 — Netflix

1. Why did Netflix never deploy the winning Netflix Prize solution?
2. The 2024-2025 Foundation Model unified many bespoke models. What did *not* get unified, and why?
3. Why does Netflix run a bandit for artwork instead of the same DLRM-style ranker?
4. Interleaving gives ~100× sample efficiency vs bucket A/B. Why?
5. A Netflix engineer says "model is great offline but long-term retention isn't moving." What's missing?

## Module 18 — Spotify

1. Spotify's cold-start problem is severe (120k uploads/day). What's the architectural answer?
2. BaRT picks both items and explanations. Why is the explanation framed as part of the treatment?
3. Why did Spotify replace Annoy with Voyager?
4. AI DJ is a three-subsystem product. What are they, and how do user skips feed back?
5. Spotify reserves slots for under-represented artists. What fairness metric is this?

## Module 19 — YouTube + Google

1. Why does YouTube's ranking network predict watch time via weighted logistic regression instead of regression?
2. The shallow position tower at YouTube lets the ranker learn relevance. What gets set to "neutral" at inference, and why?
3. MMoE's gates learn soft routing over experts. Why does this beat shared-bottom multi-task?
4. The Top-K off-policy correction is needed because RL retraining sees logged data. What does the correction adjust for?
5. TIGER's RQ-VAE produces a tuple of discrete codes per item. Why is this better for cold start than an ID embedding table?

## Module 20 — Apple

1. Why does Apple keep "you downloaded X" on-device rather than logging it server-side?
2. Local DP applies noise on the device before any data leaves. What does Apple recover at the server, and what does it sacrifice?
3. Private Cloud Compute does heavier inference than on-device. What's the privacy guarantee that vanilla cloud doesn't have?
4. Why is editorial curation more important at Apple Music than at Spotify, all else equal?
5. Why does Apple invest in the Create ML "Recommender" template for third-party devs when it doesn't sell ads?

## Module 21 — Meta

1. DLRM's bottleneck is bandwidth on embedding lookups, not FLOPs. Why does this drive Meta's hardware (MTIA) and software (FBGEMM, TorchRec) investments?
2. HSTU treats both items and actions as tokens in the sequence. What's the benefit over a sequence of just items?
3. Wukong demonstrated power-law scaling for recsys. What's the planning implication?
4. Andromeda enables ~10kx candidate-pool expansion. Where in the funnel does this matter?
5. Reels cold-start for new content uses CLIP-style content embeddings. Why is this more critical for Reels than for the main Feed?

## Module 22 — TikTok / ByteDance

1. Why does TikTok benefit more from real-time training than Netflix does?
2. Monolith's collisionless hash inserts a new ID only when its count crosses a threshold. Trade-off vs always-inserting?
3. The FYP reserves explicit exploration slots for new creators. What metric does this defend against?
4. Douyin and TikTok share architecture but are separate code paths. Engineering reason beyond regulation?
5. HLLM bears strong resemblance to HSTU and TIGER. What's the common direction of 2024-2026?

## Module 23 — Amazon, Pinterest, LinkedIn, Airbnb, Uber, DoorDash, Etsy

1. Amazon's 2003 item-item paper is still in production 20 years later. What property of item-item CF makes it durable?
2. Why are GNNs more valuable at Pinterest than at YouTube?
3. LinkedIn's LiRank trains a calibration layer jointly with the main model. Why better than post-hoc calibration?
4. Airbnb's "booked listing as global context" — what training-time trick does this represent and why is it important?
5. DoorDash uses DoubleML to estimate ranking treatment effects. Why is observational click rate insufficient for ranking decisions?
6. Etsy's cold start relies on image embeddings. Why does image dominate over text for handmade goods?

## Module 24 — B2B & outreach

1. Why does a B2B recsys typically use LightGBM rather than DLRM?
2. The Clay-style "personalisation at scale" pattern adds a quality classifier after the LLM call. What does this defend against?
3. Intent data from Bombora, 6sense, G2 is usually aggregated via weighted sum or LightGBM. What's the alternative in 2026 given the data scale?
4. A B2B startup wants to add an "AI cold email" feature without burning customer reputation. Name two ML components that gate sending.
5. Highspot ranks decks by "win-rate-of-content-when-used." What's the causal-inference problem hiding in this signal?
