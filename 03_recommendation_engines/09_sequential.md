# Module 9 — Sequential & Session Models

> If Module 8 is "the user is a static profile that interacts with items," this module is "the user is a sequence of events, and what they do next depends most on what they just did." The dominant pattern for short-video, music, e-commerce, and ads since 2018.

---

## 1. Why sequential

Static recommenders mix together a user's history into a single vector. That works when long-term taste is stable. It fails when:

- The user has multiple interest "moods" (Netflix kids vs adult).
- Recent context dominates (just searched for running shoes → next session should rank running gear).
- Sequence patterns matter (people who watch episode 1 of a series want episode 2).
- Sessions have arcs (workout playlist starts slow, ramps up).

Sequential models capture these by *processing the history as a sequence* and predicting the next event.

```mermaid
flowchart LR
    H[Last N events:<br/>e_1, e_2, ..., e_n] --> ENC[Sequence encoder<br/>RNN / Transformer]
    ENC --> R[Representation of current state]
    R --> S[score(state, candidate item)]
    C[Candidate item j] --> S
    S --> P[P(next = j | history)]
```

---

## 2. GRU4Rec (Hidasi et al. ICLR 2016) — session-based RNNs

The first widely deployed sequential recommender. Treats a user session as a sequence; uses a **GRU** to encode it.

```
h_t = GRU(emb(i_t), h_{t-1})
ŷ_t = softmax(W · h_t)
```

At inference, `h_t` is the user state; `argmax` over `softmax` is the next-item prediction.

**Why GRU not LSTM**: empirically similar but cheaper. **Why softmax not regression**: top-N matters more than scores.

Limitations: hard to parallelize at training (sequential RNN); long sequences need truncated backprop; doesn't handle items the user hasn't seen.

---

## 3. SASRec — Self-Attentive Sequential Recommendation (Kang & McAuley ICDM 2018)

Replace the RNN with a **transformer decoder**.

```
masked self-attention over history → next-item prediction
```

- Causal mask: position `t` only attends to positions `< t`.
- Loss: cross-entropy over `next_item` for each position.
- Inference: take the final-position output, top-K via dot product against item embeddings.

SASRec is the **canonical sequential recsys baseline**. Still hard to beat without significantly more compute. Most "new" sequential papers compare against it.

```python
class SASRec(nn.Module):
    def __init__(self, n_items, d_model=64, n_layers=2, n_heads=2, max_len=50):
        super().__init__()
        self.item_emb = nn.Embedding(n_items + 1, d_model, padding_idx=0)
        self.pos_emb  = nn.Embedding(max_len, d_model)
        layer = nn.TransformerEncoderLayer(d_model, n_heads, batch_first=True)
        self.encoder = nn.TransformerEncoder(layer, n_layers)
        self.max_len = max_len

    def forward(self, seq):           # seq: (B, L) item ids
        pos = torch.arange(seq.size(1), device=seq.device)
        x = self.item_emb(seq) + self.pos_emb(pos)
        mask = nn.Transformer.generate_square_subsequent_mask(seq.size(1)).to(seq.device)
        h = self.encoder(x, mask=mask)
        # score against all items
        logits = h @ self.item_emb.weight.T
        return logits   # (B, L, n_items+1)
```

---

## 4. BERT4Rec — Bidirectional Encoder (Sun et al. CIKM 2019)

Instead of causal next-item prediction, **masked-item prediction**. Pre-train by randomly masking items in the sequence and predicting them from the *bidirectional* context.

- Same architecture as BERT.
- Inference: mask the last position and predict.
- Slightly better than SASRec on many benchmarks; harder to fine-tune.

**Caveat** (Petrov & Macdonald 2022): the original BERT4Rec evaluation was non-standard; with a fair comparison the gap to SASRec is small.

---

## 5. Contrastive sequential models

A self-supervised twist: augment the sequence (mask, crop, reorder), then contrastively train so different augmentations of the same sequence are nearby.

- **CL4SRec** (Xie et al. ICDE 2022) — three augmentations: item crop, mask, reorder.
- **DuoRec** (Qiu et al. 2022) — model-augmented positive pairs.
- **S3-Rec** (Zhou et al. CIKM 2020) — self-supervised pretraining with multiple objectives.

Helps especially in **cold-start sequences** and when the action space is huge.

---

## 6. Long-sequence modeling — the SIM/ETA/TWIN line

Standard sequence models truncate to the last 50-200 events. But a Tmall user has thousands of past purchases; clipping to 50 loses signal. The Alibaba/Kuaishou lineage tackles this.

### 6.1 SIM — Search-based Interest Model (Pi et al. CIKM 2020, Alibaba)

Two-stage attention:

1. **General Search Unit (GSU)** — retrieve top-K items from the user's lifelong history that are relevant to the target ad. Two flavors:
   - **Hard search**: same-category items via inverted index.
   - **Soft search**: embedding-based ANN.
2. **Exact Search Unit (ESU)** — DIN-style target-aware attention over the retrieved subset.

Allows lifelong history (10k+) with manageable cost. Production at Alibaba.

### 6.2 ETA — End-to-end User Behavior Retrieval (Chen et al. 2021)

Replaces hard search with **SimHash LSH** that's **jointly trained** with the ranker. The retrieval step is differentiable end-to-end.

### 6.3 TWIN — Two-stage Interest Network (Chang et al. KDD 2023, Kuaishou)

Unifies target-aware attention across both retrieval and ranking — closes the representation gap. The two stages share the same attention parameters, so the retrieval picks "things the ranker would care about."

### 6.4 TWIN-V2 (2024)

Hierarchical clustering of the lifetime history; cluster-aware target attention. Scales to truly lifelong sequences.

---

## 7. HSTU — Hierarchical Sequential Transducer Unit (Meta, Zhai et al. ICML 2024)

The most consequential sequential recsys paper of 2024. Module 12 details. In brief:

- Cast both **retrieval and ranking** as next-action prediction over an interleaved sequence of `(item, action)` tokens.
- HSTU layer = pointwise feedforward + gated linear attention variant. FLOPs scale roughly linearly with sequence length.
- Scales to **1.5T parameters**, sequences of tens of thousands of events.
- **Clean scaling laws** (Wukong, Zhai et al. follow-on): performance is power-law in compute, like LLMs.

Replaces DLRM at Meta production scale for Reels and ads through 2024-2025.

---

## 8. Sequence-aware ranking vs sequence-aware retrieval

Two different uses of sequence models:

| Use | Architecture | Output |
|-----|--------------|--------|
| **Retrieval** | Encoder of user sequence → user vector; ANN over item vectors | Top-K candidates |
| **Ranking** | Encoder of sequence + features → score per candidate | Fine-grained scores |

Most production systems use **both**:
- A sequence-encoder user vector for two-tower retrieval.
- A heavier sequence-aware ranker (DIN-style) for fine ranking.

---

## 9. Negative sampling in sequential models

Sequential models almost always train with **sampled softmax** over the item vocabulary:

```
L = − Σ_t  log [ exp(s(h_t, i_{t+1})) / Σ_{j ∈ S} exp(s(h_t, j)) ]
```

where `S = {i_{t+1}} ∪ negatives`.

- **Random uniform negatives**: simplest.
- **Popularity-proportional**: standard.
- **In-batch**: cheap, biased toward popular items.
- **Hard negatives via current-model retrieval**: most expensive, fastest convergence.

The LogQ correction (Module 2 §4) applies here too.

---

## 10. Industry use cases

| Company | Sequential model | Surface |
|---------|------------------|---------|
| TikTok / ByteDance | Two-tower + Monolith + HLLM | For You Page |
| Meta | DLRM with sequence features → HSTU (2024+) | Reels, Feed |
| YouTube | Two-tower + ranking + RL with off-policy correction | Watch Next |
| Spotify | Session transformers, AI DJ | Discover, DJ, Autoplay |
| Netflix | Foundation Model over multi-year sequences | Home ranking, "Play Something" |
| Alibaba | DIN → DIEN → BST → SIM → ETA → TWIN | Taobao display ads, Tmall search |
| Kuaishou | TWIN / TWIN-V2 + PEPNet | Short-video |
| Amazon | Personalize uses HRNN-Metadata for sequences | Various |

The pattern: sequence models everywhere by 2024.

---

## 11. Sample code: SASRec training loop sketch

(See [`code/09_sasrec.py`](code/09_sasrec.py) for a runnable version.)

```python
import torch
from torch.utils.data import DataLoader

model = SASRec(n_items=10000, d_model=64, n_layers=2, n_heads=2, max_len=50)
opt = torch.optim.Adam(model.parameters(), lr=1e-3)

# Training loop sketch — each batch is (sequences, labels) where label[t] = next item
for epoch in range(10):
    for seq, label, mask in loader:           # seq: (B, L), label: (B, L), mask: (B, L) for padding
        logits = model(seq)                   # (B, L, V)
        loss = torch.nn.functional.cross_entropy(
            logits.reshape(-1, logits.size(-1)),
            label.reshape(-1),
            ignore_index=0,                   # pad token
        )
        opt.zero_grad(); loss.backward(); opt.step()

# Inference: take final-position output, top-K
with torch.no_grad():
    h = model.encoder(model.item_emb(seq) + model.pos_emb(torch.arange(seq.size(1))))
    last = h[:, -1, :]                        # (B, d_model)
    scores = last @ model.item_emb.weight.T   # (B, n_items+1)
    top_k = scores.topk(k=10).indices
```

---

## 12. Sanity check

1. Why does a static "user profile" representation underfit users with multiple distinct interests, and how does a sequence model address this?
2. SASRec uses causal masking; BERT4Rec uses bidirectional masking. Which is the better fit for "predict next item" and why?
3. Your user has 10,000 lifetime events. Why can't you run vanilla DIN-style attention with all 10,000 as keys, and what did SIM / ETA / TWIN do about it?
4. In a sequential model, what's the danger of training only on positives without sampled-softmax negatives?
5. Why does Meta's HSTU treat *both* items and actions as tokens in the sequence?
