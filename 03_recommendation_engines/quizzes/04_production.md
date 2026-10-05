# Quiz — Production Architecture (Modules 13-16)

## Module 13 — The funnel

1. Why can't a single model just rank all 10⁹ items per request, even on GPU?
2. Your retrieval stage has Recall@100 = 0.3. What does this tell you about the cap on your ranker's possible improvement?
3. The L2 ranker outputs pCTR ≈ 0.6 for every candidate. What's gone wrong?
4. Three creators have produced 80% of recent home-feed items. Which stage of the funnel should fix this and how?
5. Your retrieval timeouts spike under load. Describe a sensible degradation path.

## Module 14 — Candidate generation

1. Why not just one two-tower retriever?
2. Your "trending" retriever pushes the same 50 items to every user. Trade-off, and mitigation?
3. Merging candidates from 5 retrievers with different score scales. How do you decide which item ranks higher?
4. A user's last 10 clicks are all on creator A. Without explicit anti-monopoly logic, what happens to the next slate?
5. Why do production teams reserve 1-5% of slots for random/exploration items?
6. Cold-start behaviour of a pure ANN retriever for a brand-new item, and the fix?

## Module 15 — Ranking & MTL

1. Why does single-objective CTR optimization eventually break a recsys?
2. MMoE replaces a shared bottom with experts and per-task gates. Why does this reduce negative transfer?
3. Value model combines task probabilities with weights `w_i`. Why must each `p_i` be calibrated?
4. ESMM avoids training CVR directly. What bias does this avoid?
5. A 1% AUC improvement vs a 5% weight change in the value model — which is likely to produce more business impact?
6. Ranker maximises short-term watch time and CTR. Retention is flat. What's missing from the loss?

## Module 16 — Cold start, exploration, debiasing

1. A user signs up today with no profile. 2-stage fix for a usable first session?
2. A new item gets 0 impressions because its ID embedding is random. What feature should the item tower use?
3. The shallow position tower (PAL) absorbs position bias. Why does setting position to "neutral" at inference work?
4. ε-greedy and Thompson sampling. Which is better for a 10-arm choice with sparse rewards?
5. "Popular items dominate" complaint reaches the ranker but isn't fixed. Where else can you intervene?
6. Define provider-side fairness in two sentences. Give one mitigation that fits in re-ranking.
