# Quiz — Classical Algorithms (Modules 5-7)

## Module 5 — Content-based filtering

1. Why did content-based filtering fall out of fashion ~2010 and come back ~2023?
2. A user has watched 200 movies. Ten years ago they liked horror; now they prefer documentaries. What's wrong with averaging their history into one user vector, and what's the production fix (Pinterest-style)?
3. A new documentary uploaded today has no interactions. How does a hybrid (content + collaborative) model rank it for a documentary fan?
4. List three modern content-encoder choices (text, image, audio).
5. Amazon's COSMO (2024) uses LLMs to generate "common-sense" knowledge for products. Why is this approach competitive with manually curated taxonomies?

## Module 6 — Neighborhood CF

1. Why did user-based kNN lose to item-based kNN at industrial scale?
2. Two items have 2 users who both rated them 5 stars. Raw Pearson = 1.0. Why is this misleading and what fixes it?
3. The Amazon item-item similarity matrix at 10⁷ items is **not** stored as a 10¹⁴-entry dense matrix. What does Amazon actually store?
4. Your "Frequently bought together" rail surfaces a $5 cable as similar to a $1000 laptop because of high co-occurrence. Suggest a similarity tweak.
5. For implicit feedback (plays in a music service), which similarity (cosine over binary, Jaccard, lift) would you choose, and why?

## Module 7 — Matrix factorization & FM family

1. Why is "SVD for recommenders" a misnomer?
2. In ALS-implicit, what's `c_ui` for an item the user never interacted with? What does that contribute to the objective?
3. Write the BPR loss for one triple. Explain in one sentence why it's "AUC-like."
4. FM has `O(n · k)` parameters but expresses every pairwise interaction. How is that possible?
5. The 2020 NCF reproducibility paper showed plain MF beats NCF when properly tuned. What's the lesson for evaluating new recsys ideas?
6. Your team replaces ALS with a DLRM-style ranker and AUC goes up 0.5% offline. Why might this not translate to an online win?
