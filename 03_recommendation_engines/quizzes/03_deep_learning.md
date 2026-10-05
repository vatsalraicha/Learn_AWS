# Quiz — Deep Learning (Modules 8-12)

## Module 8 — Neural CTR

1. Why did Wide & Deep need hand-crafted feature crosses, and how did DeepFM remove that?
2. DCN-V2's cross layer computes `x_{l+1} = x_0 ⊙ (W_l x_l + b_l) + x_l`. What does this compute that a plain MLP can't?
3. DLRM's pairwise dot products produce N·(N+1)/2 interaction features. Why is this affordable but a full N×N MLP isn't?
4. A user's history is 10,000 items. Standard DIN attention would have 10k keys per candidate. What did SIM / ETA / TWIN do?
5. Wukong demonstrated power-law scaling. What's the practical implication for an architect choosing model size?

## Module 9 — Sequential models

1. Why does a "user profile = mean of history" approach underfit multi-mood users? How does a sequence model address this?
2. SASRec uses causal masking; BERT4Rec uses bidirectional masking. Which is the better fit for "predict next item" and why?
3. Why can't you run vanilla DIN-style attention over 10,000 historical items per candidate? What did SIM/ETA/TWIN do?
4. In a sequential model, what's the danger of training only on positives without sampled-softmax negatives?
5. Meta's HSTU treats items AND actions as tokens. Why?

## Module 10 — Two-tower retrieval

1. Two-tower's dot-product factorization is the entire reason it scales. What's the alternative architecture and why can't it scale?
2. In-batch negatives give B-1 negatives per positive for free. What's the bias and what's the correction?
3. You launch a two-tower retriever and popular items are missing from top-K. Most likely cause?
4. Item catalog grows 10×; model architecture stays the same. What part of the serving stack must scale, and how?
5. New items added daily need to appear in retrieval the same day. How do you ensure that without retraining the whole model?
6. A teammate proposes cosine instead of dot product. What conditions make these equivalent?

## Module 11 — GNNs for recsys

1. Why is the GNN message-passing path "user → item → user → item" equivalent to multi-hop collaborative filtering?
2. PinSage's biggest engineering innovation wasn't the model. What was it?
3. LightGCN removed feature transformations and nonlinearity from NGCF and got better results. What does this suggest?
4. PinnerSage represents each user with ~3 medoids instead of one centroid. What's the trade-off?
5. Why are GNNs more valuable at Pinterest/LinkedIn than at Netflix/YouTube?
6. Production GNNs typically precompute embeddings and serve via lookup. Why don't they run message passing at request time?

## Module 12 — LLMs & generative recommenders

1. Why is "LLM as feature extractor" the most-deployed of the three LLM-in-recsys patterns?
2. What problem do semantic IDs (TIGER's RQ-VAE codes) solve that vanilla item ID embeddings can't?
3. HSTU's headline trick is replacing standard self-attention with a pointwise gated variant. Why?
4. P5 frames every recsys task as text-to-text. Why is this elegant for research but impractical for billion-user surfaces?
5. Generative recommenders enable retrieval-via-decoding. What infrastructure must change vs a DLRM-style stack?
6. A B2B search startup wants LLM-quality ranking at 10ms p99 latency. What architecture would you propose?
