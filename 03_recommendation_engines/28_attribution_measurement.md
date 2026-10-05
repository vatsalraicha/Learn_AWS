# Module 28 — Attribution & Measurement

> "Half the money I spend on advertising is wasted; the trouble is I don't know which half." — John Wanamaker. This module is the modern toolkit for answering Wanamaker.

---

## 1. The three measurement paradigms

| Paradigm | Question answered | Limitation |
|---|---|---|
| **Last-click / rule-based MTA** | What touchpoint did the user click last? | Observational; obscures upper-funnel impact |
| **Data-driven attribution (DDA)** | What "credit" should each touchpoint get? | Statistical, but still observational |
| **Incrementality / lift** | Would the conversion have happened *without* the ad? | Truly causal but expensive |

All three are needed in modern ads measurement. The 2024-2026 industry consensus: **MMM + lift studies + experiments** at the strategic level; DDA and MTA for tactical optimisation.

---

## 2. Last-click and rule-based MTA

The legacy default. Google Analytics Universal had six built-ins:

- **Last click** — all credit to last touchpoint.
- **First click** — all credit to first touchpoint.
- **Linear** — equal credit across all touchpoints.
- **Time-decay** — credit decays exponentially with time-to-conversion.
- **Position-based (40-20-20-20)** — front-loaded.
- **U-shaped** — first and last get more credit.

All are arbitrary. None are causal. Useful only for "compared to last quarter under the same model" trend tracking.

---

## 3. Data-driven attribution (DDA)

### 3.1 Markov chain attribution

Model the journey as a Markov chain over channel states. **Removal effect**: the change in conversion probability when channel X is removed from the chain. Attribute credit by removal effect.

[Anderl et al. 2016](https://doi.org/10.1016/j.ijresearchmar.2016.04.005) — "Mapping the customer journey: Lessons learned from graph-based attribution modeling."

### 3.2 Shapley value attribution

Cooperative game-theoretic credit: a channel's credit is its average marginal contribution to conversion across all possible orderings of channels. O(N!) exact; approximated in practice.

### 3.3 DDA at Google Ads

The default since March 2023 — Google retired all rule-based models for Google Ads. Counterfactual model trained on conversion paths.

### 3.4 The fundamental limitation

DDA is **observational**. It can tell you "channel X frequently appears before conversion" but not "channel X *caused* the conversion." A user who would have converted anyway clicked your ad — DDA gives credit. The fix is incrementality (§5).

---

## 4. CTR vs CVR vs CTCVR — the auction-side metrics

Module 26 covered. Important because **bidding** uses these:

| Quantity | Meaning |
|---|---|
| CTR = P(click \| impression) | clickability |
| CVR = P(convert \| click) | post-click conversion |
| CTCVR = P(click & convert \| impression) | downstream value |
| pVCM = E[value \| convert] | dollars |
| Expected value = pCTCVR × value | actual bid in tROAS |

ESMM (Module 26 §12) is the canonical solution for the CVR sample-selection bias.

---

## 5. Incrementality and lift studies

The honest measurement. **Run experiments**:

| Method | Description |
|---|---|
| **Conversion lift studies** | Randomised holdout. Control gets PSA. Meta Lift, Google Brand Lift, TikTok Lift Studies |
| **Ghost ads** ([Johnson, Lewis, Nubbemeyer 2017, eBay](https://www.aeaweb.org/articles?id=10.1257/aer.20151070)) | Run the auction for control but don't serve; log would-have-won impressions |
| **PSA tests** | Substitute a PSA in control |
| **Geo experiments** | Split DMAs. Synthetic control ([CausalImpact, Brodersen et al. Google 2015](https://research.google/pubs/inferring-causal-impact-using-bayesian-structural-time-series-models/)) |
| **Switchback** | Time-based randomisation |
| **Audience holdouts** | Randomised 1-10% holdout for campaign duration |

Cost: 1-10% of budget goes to control; results take days to weeks.

Reward: the only honest answer to "did this ad work?"

---

## 6. Marketing Mix Modeling (MMM) — the post-cookie resurgence

The classic econometric formulation:

```
sales_t = β_0 + Σ_c β_c · saturate(adstock(spend_{c,t})) + Σ controls + ε
```

- `adstock` — exponential decay over time capturing carry-over.
- `saturate` — Hill / S-shape saturation capturing diminishing returns.
- `controls` — seasonality, macro factors, prices, distribution.

### 6.1 The modern OSS tooling

| Tool | Owner | Notes |
|---|---|---|
| **Meridian** | Google, OSS Jan 2024 | Bayesian hierarchical MMM (Stan/TF Probability); geo + national; reach & frequency. [github.com/google/meridian](https://github.com/google/meridian) |
| **LightweightMMM** | Google, 2021 | JAX/NumPyro. Replaced by Meridian. |
| **Robyn** | Meta, OSS since 2021 | R + Python; Nevergrad hyperparameter optimisation. [github.com/facebookexperimental/Robyn](https://github.com/facebookexperimental/Robyn) |
| **PyMC-Marketing** | PyMC Labs | Bayesian MMM + CLV |
| **Orbit** | Uber | Bayesian time series |

### 6.2 Why MMM is back

Post-ATT and post-cookie, deterministic per-user attribution broke. MMM works at **aggregate** level — no per-user identifiers needed. The 2024-2026 wave is calibrating MMM with experiment data:

> **Unified Marketing Measurement (UMM)** = MMM + lift studies + clean-room data.

Vendors: Nielsen, Analytic Partners, IPSOS MMA, Marketing Evolution.

---

## 7. Causal inference for ads

### 7.1 Uplift / Heterogeneous Treatment Effects

Predict **per-user lift** from a treatment (showing an ad):

```
τ(x) = E[Y | treatment=1, X=x] − E[Y | treatment=0, X=x]
```

Approaches:
- **Two-model** (S-learner, T-learner): fit one model per arm.
- **X-learner** (Künzel et al. 2019): cross-fitted meta-algorithm.
- **R-learner** (Nie & Wager 2021): residualised regression.
- **Causal Forests** ([Athey & Wager 2019](https://www.jstor.org/stable/26611818)).

Libraries: `econml` (Microsoft), `causalml` (Uber), `pylift` (Wayfair), `grf` (R).

### 7.2 Double / Debiased ML (Chernozhukov et al. 2018)

Two orthogonal nuisance models (treatment assignment, outcome given features) → unbiased treatment-effect estimates from observational data. The DoorDash blog series is the production reference.

### 7.3 Synthetic control

[Abadie, Diamond, Hainmueller 2010](https://economics.mit.edu/files/11859); [CausalImpact Bayesian variant 2015]. Used heavily for geo-experiment-style ad measurements.

---

## 8. The clean-room layer (2024-2026)

When data can't move between parties, **clean rooms** allow joint analysis without raw data exchange:

| Clean room | Owner | Notes |
|---|---|---|
| Google Ads Data Hub (ADH) | Google | First-party + Google ad logs in BigQuery |
| Amazon Marketing Cloud (AMC) | Amazon | Same for Amazon Ads |
| Meta Advanced Analytics | Meta | Clean-room for large advertisers |
| AWS Clean Rooms | AWS | Multi-party clean room over S3 |
| Snowflake Data Clean Rooms | Snowflake | Native data sharing + row-level access; DP via Habu (acquired 2024) |
| Databricks Clean Rooms | Databricks | Delta Sharing |
| LiveRamp Safe Haven | LiveRamp | Identity-resolved |
| InfoSum | InfoSum | Federated query — data never moves |

Use cases:
- Match advertiser CRM to platform impressions.
- Compute lift across platforms without sharing raw data.
- Build look-alikes without exposing seed sets.

---

## 9. Sanity check

1. Last-click attribution gives 100% credit to the last touch. Why is this fundamentally biased toward search and retargeting?
2. DDA at Google retired rule-based models in 2023. What did it replace them with, and what limitation remains?
3. Ghost ads run the auction for control users but don't serve. What does this measure that a "show PSA" control doesn't?
4. MMM works at aggregate level. Why has it resurged post-ATT?
5. Clean rooms allow joint analysis without raw data exchange. Name two use cases and the privacy property they preserve.
6. Causal Forests / DoubleML let you estimate per-user treatment effect from observational data. Why is this attractive for ads when randomised experiments are expensive?
