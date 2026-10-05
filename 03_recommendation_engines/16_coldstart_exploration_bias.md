# Module 16 — Cold Start, Exploration, Debiasing, Fairness, Freshness

> The "five hard problems" from Module 1, in detail. Each one has multiple mitigations; this module is the toolkit.

---

## 1. Cold start

### 1.1 New user

A user with < 10 lifetime events has no useful ID embedding.

Mitigations:
1. **Onboarding flow**: ask for 3-10 explicit interests; map to seed items.
2. **Context-only ranker branch**: a separate tower trained on (no user_id, demographic + device + geo + time) → user vector. Switched in for users with `tenure_days < 7`.
3. **Heavy exploration**: first session shows higher diversity; learn fast.
4. **Demographic priors**: shrink toward the mean for the user's age band / country / device.
5. **Cohort propagation**: if a new user invited by an existing user (referral), use the inviter's profile as a prior.

### 1.2 New item

A new item with 0 interactions has a random ID embedding.

Mitigations:
1. **Content embeddings**: the item tower consumes (text, image, audio) embeddings from pretrained encoders. Available on day 1.
2. **Creator / seller priors**: a new pin from an established creator inherits the creator's average performance.
3. **Exploration boost**: reserve 1-5% of impressions for new items.
4. **Throttled experimentation**: small initial audience; if engagement passes threshold, scale up.
5. **Editorial bootstrap**: new artists get a slot in "Fresh Finds"; new movies feature in "New Releases."
6. **Semantic IDs (TIGER)**: a new item gets a code based on content; the model generalises from shared prefix codes (Module 12).

### 1.3 New surface

A brand-new product surface has no logged data.

Mitigations:
- Transfer from similar surfaces (Spotify Podcasts borrowed from Music).
- Heavy editorial seeding (curators provide initial value).
- Faster exploration regime.
- Aggressive A/B testing for the first quarter.

### 1.4 New domain (geographic expansion)

Entering a new country has different content, language, behaviour patterns.

Mitigations:
- Demographic features (country, language as one-hot).
- Transfer learning from related domains.
- Editorial bootstrap heavy.
- Avoid US-trained models being directly applied; per-region fine-tuning.

---

## 2. The exploration vs exploitation problem

A pure exploiter (always picks the current top-ranked item) starves the long tail and locks in the feedback loop. A pure explorer (random) gives users a bad experience.

The trade-off is a fundamental problem. The toolkit:

### 2.1 ε-greedy

With probability ε, pick a random item from the candidate set. With probability 1-ε, pick the top-ranked.

Simple, terrible. Random items annoy users; ε must be small (1-5%).

### 2.2 Thompson sampling

For each item, maintain a posterior over its reward. Sample from each posterior; pick the item with the highest sample.

- Naturally trades exploration vs exploitation: high-variance items are sampled more often, but only when they could plausibly win.
- Works for Bernoulli rewards (click / no click) with Beta posteriors.

```python
# pseudocode
for item in candidates:
    alpha[item] = 1 + clicks[item]
    beta[item]  = 1 + impressions[item] - clicks[item]
    sample[item] = beta_distribution(alpha[item], beta[item]).sample()
chosen = argmax(sample)
```

### 2.3 LinUCB and contextual bandits

When you have **features** about items/contexts, model the reward as a linear function of features:

```
r = θᵀ · x + noise
```

UCB scores combine the predicted mean and a "confidence width":

```
score(x) = θ̂ᵀ · x + α · sqrt(xᵀ A⁻¹ x)
```

Higher score either because predicted mean is high *or* because the confidence interval is wide → uncertain items get explored.

Used by Netflix (artwork), Spotify (BaRT), Yahoo News (the original LinUCB paper, Li et al. WWW 2010).

### 2.4 Neural contextual bandits

Replace the linear `θᵀ x` with a deep network; estimate uncertainty via dropout-Bayesian, ensembles, or last-layer Bayesian methods. Production examples: Spotify BaRT 2022+, Netflix neural artwork bandit.

### 2.5 ε vs Thompson vs UCB

- ε-greedy: simplest, works as backstop.
- Thompson: best for many-arm Bernoulli settings.
- UCB / LinUCB: best when contextual features matter.

In production, you often use multiple — Thompson for arm selection, ε for ad-hoc exploration, model retraining handles long-term learning.

---

## 3. Selection bias and exposure bias

The system only logs data on items it chose to show. The unseen items are missing-not-at-random.

### 3.1 Inverse Propensity Scoring (IPS)

Weight each observation by `1 / P(item was shown | u)`:

```
L_IPS = Σ_observed  (1/p_shown) · loss(item)
```

Requires:
- Knowing the propensities (the past system's policy must be logged or estimable).
- Exploration noise (otherwise propensities are 0 or 1 → singular weights).

The 2019 Joachims, Swaminathan, de Rijke paper "Deep Learning with Logged Bandit Feedback" is the production-grade reference.

### 3.2 Doubly Robust (DR)

Combine IPS with a model-based reward estimator. Module 4 §4.4. Consistent if either model is correct.

### 3.3 Direct unbiased data

A small fraction of traffic uses a known stochastic policy (uniform random or softmax over scores) to generate truly unbiased data. The "random arm" of a contextual bandit. Yahoo R3 dataset is famous for releasing such data.

### 3.4 Counterfactual augmentation

Train with the loss on observed items + an IPS-weighted regularizer that encourages the model to predict reasonable scores for unseen items.

---

## 4. Position bias

Items higher up the slate are clicked more often *regardless of relevance*. If you naively train on click data, the model learns "position 1 is great."

### 4.1 Click models

The classical click-modeling literature (Chuklin et al. 2015):
- **Position-Based Model (PBM)**: `P(click | u, i, pos) = P(examine | pos) · P(relevant | u, i)`.
- **Cascade Model**: user examines items top-down, stops at the first relevant.
- **Dynamic Bayesian Network (DBN)**: full sequential model with persistence.
- **User Browsing Model (UBM)**: distance-from-last-click affects examine.

Each gives a different `θ(pos)` factor. With the factorisation, you can recover relevance from click data.

### 4.2 Shallow position tower (PAL — Guo et al. KDD 2019)

The cleanest production trick. Add a **shallow tower** consuming only position-related features (slot, page number, surface). Its output is **added** (in logit space) to the main network's output.

- At training: position is real.
- At inference: set position to a *neutral* value (e.g., position = 1). The main network learns relevance; the position tower absorbs bias.

Used at Google, YouTube, Netflix, LinkedIn LiRank (which trains a calibrated position adjustment jointly).

### 4.3 IPS reweighting

Treat position as part of the propensity:

```
P(item i is shown to u at position pos) = P(retrieved) · P(ranked at pos | retrieved)
```

Reweight by `1 / θ(pos)`. Estimating `θ(pos)` requires randomized position swaps in a small fraction of traffic.

### 4.4 Randomization (position swaps)

To estimate `θ(pos)`, randomly swap adjacent positions in some impressions. The difference in CTR across swap pairs reveals `θ`. A small but principled cost in user experience.

---

## 5. Popularity bias

Popular items get more impressions → more clicks → look more popular → get more recommended. Long tail starves.

### 5.1 Down-weight popular items in negatives

Standard popularity-based negative sampling: `q(j) ∝ count(j)^α` with `α < 1`. Lower `α` (e.g., 0.5) gives more weight to rare items.

### 5.2 Inverse-frequency reweighting

Multiply training loss by `1 / popularity` (or its smoothed version). Forces the model to learn rare items as well as popular.

### 5.3 Per-source quotas

In candidate generation (Module 14), cap the contribution of "popularity" retrievers. Force tail retrievers to contribute too.

### 5.4 Fairness constraints

Hard caps: no item appears more than X% of slots in a daily window.

---

## 6. Diversity

Three flavours:

### 6.1 Intra-list diversity

Within one slate, items shouldn't be too similar. **MMR** (Module 13) and **DPP** are the standard mitigations.

### 6.2 Inter-list diversity / personalization

Two users with similar profiles shouldn't get identical slates. Captured via per-user noise or per-context exploration.

### 6.3 Temporal diversity

The same user shouldn't get the same items day after day. Mitigated by:
- Recency penalty (items shown in last 7 days get score -ε).
- Round-robin across content types.

---

## 7. Calibration

For multi-task and ads ranking, predictions must be probabilities. Module 2 §5 has the math (Platt, isotonic, beta calibration, slice-level multi-calibration).

### 7.1 Post-hoc calibration

Train a calibration layer (isotonic regression or a small MLP) on held-out data after the main model trains. The simplest fix.

### 7.2 Jointly-learned calibration

LinkedIn's LiRank trains an **isotonic calibration head** jointly with the main model. Cleaner; one-step training.

### 7.3 Slice-level

Calibrate per (advertiser × placement × geo × time-of-day) slice. Ads systems do this hourly.

---

## 8. Fairness

The third "hard problem" of multi-stakeholder ranking. Modern definitions:

### 8.1 Provider-side fairness

Are creators / sellers / advertisers getting fair exposure?

- Gini coefficient of exposure across creators.
- Minimum-impression-floor for new creators.
- Top-K creators capped at X% of total impressions.

### 8.2 Consumer-side fairness

Are demographic groups getting comparable quality?

- Per-group AUC / NDCG.
- Per-group recommendation diversity.
- Per-group click-through-rate.

### 8.3 Two-sided marketplace fairness

Airbnb, Etsy, Uber face this directly. Implementations:
- Re-ranking constraints: each seller / host appears in top-K with proportional probability.
- Exposure regularisers in training loss.
- Position-aware fairness metrics.

### 8.4 Algorithmic fairness research

- **Demographic parity**: outcomes are independent of protected attributes.
- **Equalized odds**: TPR and FPR are equal across groups.
- **Calibration parity**: predicted probabilities mean the same thing across groups.

These often conflict; choose based on use case and regulation.

---

## 9. Freshness

### 9.1 Why freshness matters

A 6-month-old top-recommended item is uninteresting once seen. News, short video, social need fresh content within hours.

### 9.2 Freshness as a feature

- `log(1 + age_hours)` as a feature in the ranker.
- Decay factors: `boost(i) = exp(-λ · age)`.

### 9.3 Dedicated freshness retrievers

Separate candidate-gen for fresh content (Module 14 §2.5).

### 9.4 Recency caps

Don't show the same item twice within X hours.

### 9.5 Freshness vs accuracy trade-off

A fresh-content recommender has lower offline accuracy by definition (less behavioral signal per item). Live A/B is the only fair evaluation.

---

## 10. Filter bubbles and ideological diversity

A long-running concern: recsys feedback loops produce echo chambers.

Recent research (Anderson et al. WWW 2020 at Spotify; Bakshy, Messing, Adamic 2015 at Facebook) suggests the bubble effect is often smaller than predicted — but not zero.

Mitigations:
- Explicit diversity injection (varied perspectives in news, varied genres in music).
- Per-user "broadening" interventions.
- Editorial overrides for high-stakes topics.

---

## 11. Sanity check

1. A user signs up today with no profile. What's your 2-stage fix to give them a usable first session?
2. Your new item gets 0 impressions because its ID embedding is random. What feature should the item tower use to bootstrap retrieval?
3. The shallow position tower trick (PAL) absorbs position bias. Why does setting position to "neutral" at inference work?
4. ε-greedy and Thompson sampling are both exploration. Which is better for a 10-arm choice with sparse rewards, and why?
5. Your "popular items dominate" complaint reaches the ranker but isn't fixed. Where else in the funnel can you intervene?
6. Define provider-side fairness in two sentences. Give one mitigation that fits in re-ranking.
