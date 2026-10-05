# Quiz — Foundations (Modules 1-4)

Answer cold. The module text + FACTS.md are the answer keys.

## Module 1 — Foundations & taxonomy

1. List the seven problem framings ("ratings prediction" through "generative") and give one production example of each.
2. The "canonical pipeline" has two phases that run on different cadences. What are they, and why does mixing them cause production bugs?
3. Why does scoring all 100M items with the full ranker per request fail, and what's the funnel's mathematical justification?
4. "Don't use RAG when…" — Module 1 lists six anti-cases for recommenders. Name four.
5. Explain the feedback loop in one paragraph. List three mitigations.

## Module 2 — Math foundations

1. Prove that for L2-normalised vectors, cosine, dot product, and negative Euclidean distance rank items identically.
2. Write the ALS-implicit objective. Explain the role of `c_ui` and `p_ui`.
3. Write the BPR loss for one triple. Explain why it's "AUC-like."
4. State the FM equation. How does it generalise biased matrix factorisation?
5. Sampled softmax with in-batch negatives needs a correction. What is it, why is it called LogQ, and what happens at serving time without it?
6. Your CTR model trained with 100× negative downsampling reports `pCTR = 0.5`. Compute the calibrated `pCTR`.

## Module 3 — Data, signals, features

1. List the seven feature categories with one example each.
2. Why is "missing rating = 0" wrong for implicit feedback? Sketch three alternative treatments.
3. What is train-serve skew, and what's the "log-and-wait" pattern that fixes it?
4. Define point-in-time correctness in one sentence. Name one feature store that enforces it.
5. List three embedding-table compression tricks and one trade-off of each.
6. The watermark for conversion labels is 7 days. A team wants to train hourly to get fresh signal. How do you reconcile?

## Module 4 — Evaluation

1. What does Recall@k measure and why is it the dominant retrieval metric? Quote an industrial target.
2. Define NDCG@k. What's the difference vs MAP?
3. Why is offline AUC weakly correlated with online business metrics? Name four reasons.
4. Explain CUPED in one sentence. What's the typical variance reduction?
5. Why does interleaving give ~100× sample-efficiency vs bucket A/B for ranking comparisons?
6. Describe the doubly-robust estimator. What's the "doubly robust" guarantee?
7. Top-K off-policy correction (Chen et al. 2019). What does the correction adjust for?
