# Quiz — Ads (Modules 25-31)

## Module 25 — Ads auctions

1. Why isn't GSP truthful for ≥2 slots, and what equilibrium describes how rational bidders play it?
2. Meta switched from GSP to VCG in 2018. What advertiser behavior does VCG enable that GSP makes hard?
3. When the display industry moved to first-price, what new ML problem did DSPs have to solve?
4. eCPM is `1000 × bid × pCTR`. What does "improve pCTR" mean for revenue?
5. OpenRTB latency budget is ~100ms for the DSP. Three architectural choices forced by this.
6. A teammate proposes improving pCTR AUC by 1% offline. Why might this not improve revenue?

## Module 26 — CTR / CVR models

1. Why is FTRL-LR with billions of hashed features still relevant in 2026?
2. ESMM trains both pCTR and pCTCVR but never pCVR directly. What bias does this avoid?
3. DCN-V2 cross layer: `x_{l+1} = x_0 ⊙ (W_l x_l + b_l) + x_l`. How does this differ from a plain MLP, and what does it capture?
4. Your CTR model has 0.85 AUC offline; calibration is 30% off in some slices. What does this break in production?
5. The Alibaba SIM/ETA/TWIN line solves lifelong sequence modeling. Why is "lifelong" valuable for ads CTR?
6. HSTU replaces DLRM-style point-wise CTR with autoregressive sequence prediction. What's the architectural casualty?

## Module 27 — Bidding, pacing, budget

1. In tCPA, the platform bids `tCPA × pCVR`. What happens if pCVR is poorly calibrated?
2. Bid shading became necessary when the industry switched to first-price. Why doesn't second-price need shading?
3. A PID pacing controller's integral term overshoots when budget is briefly capped. Standard fix?
4. RL for pacing models the problem as an MDP. What's the reward signal, and why is offline RL relevant?
5. Performance Max and Advantage+ abstract bidding for advertisers. What ML problems are hidden, and how does an advertiser regain insight?

## Module 28 — Attribution & measurement

1. Last-click attribution gives 100% credit to the last touch. Why fundamentally biased toward search/retargeting?
2. DDA at Google retired rule-based models in 2023. What replaced them, and what limitation remains?
3. Ghost ads run the auction for control users but don't serve. What does this measure that a "show PSA" control doesn't?
4. MMM works at aggregate level. Why has it resurged post-ATT?
5. Clean rooms allow joint analysis without raw data exchange. Two use cases?
6. Causal Forests / DoubleML estimate per-user treatment effect from observational data. Why attractive for ads?

## Module 29 — Privacy & post-cookie

1. ATT opt-in is ~25%. What happened to advertisers who relied on IDFA-keyed retargeting?
2. SKAN 4.0 introduced hierarchical conversion values. What does "crowd anonymity" prevent that prior SKAN versions allowed?
3. Topics API gives the advertiser ~3 topics per call. Compare information content vs a third-party cookie.
4. Protected Audience API runs the auction on-device. What does this prevent for the DSP, and what new constraints does it create for bidding logic?
5. Production DP is mostly at the measurement layer, not at model training. Why?
6. Clean rooms preserve "data never moves" but allow joint analysis. Three production use cases.

## Module 30 — Ad platforms

1. Performance Max consolidates many surfaces under one campaign type. Advertiser gained vs lost vs the SKAG era?
2. Meta's Advantage+ Audience eliminates manual targeting in 2024. Why does the platform prefer to make these decisions?
3. Apple Search Ads grew from $300M to $5B+ post-ATT. What's the structural advantage Apple had?
4. Walmart acquired Vizio in 2024. Connect this to the retail-media-network thesis.
5. Microsoft's "Copilot ads" are sponsored answers in chat. Three unsolved problems.

## Module 31 — Creative, fraud, brand safety

1. DCO traditionally picks among advertiser-uploaded variants. What does generative creative change?
2. The hardest problem in generative ads isn't generation — it's quality gating. Three failure modes a quality classifier must catch.
3. GARM dissolved in 2024 but its taxonomy persists. Why does the taxonomy survive?
4. Bot traffic is ~30% of web. Most filtered for free as GIVT. Why is SIVT harder?
5. The 2024 wind-down of MOAT pushed customers to IAS and DV. What does that consolidation mean for the verification market?
