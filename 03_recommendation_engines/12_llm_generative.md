# Module 12 — LLMs & Generative Recommenders

> The two biggest architectural shifts in recsys since deep learning: **semantic IDs / generative retrieval** (TIGER, 2023) and **generative recommenders** (HSTU, 2024). Together they suggest that the standard funnel — retrieval + ranking + reranking — may collapse into a single autoregressive model. This module is the most volatile in the curriculum; check FACTS.md before quoting numbers.

---

## 1. The three ways LLMs touch recsys

| Pattern | What | Latency | Example |
|---------|------|---------|---------|
| **LLM as feature extractor** | Encode item text/image/audio offline → embedding fed into existing ranker | None online (precomputed) | CLIP for Pinterest pins; Spotify podcast transcripts |
| **LLM as ranker** | Score candidates with an LLM prompt; expensive but rich | 200-2000 ms | Cohere Rerank; Claude rerank in B2B search |
| **LLM as recommender (generative)** | Generate the next item ID autoregressively | Variable; can be cheaper than expected | TIGER, HSTU, P5, LLaRA |

Patterns 1-2 are widely deployed today. Pattern 3 is the bleeding edge.

---

## 2. LLM as feature extractor

The cheapest and most common use. Run a foundation model offline; cache the embeddings or labels; feed into a normal ranker.

### 2.1 Text features

- Pretrained sentence encoders: BGE-large, E5, GTE, `text-embedding-3-small`, Voyage, Cohere Embed v3.
- For each item, encode (title + description + categories + reviews) → 768-1024d vector.
- Concatenated to the item tower as a content feature.

### 2.2 Multimodal features

- CLIP, SigLIP, EVA-CLIP, DINOv2 for image; MERT / OpenL3 for audio.
- Combined embeddings for video (frame + audio + caption).

### 2.3 LLM-generated tags

LLMs *generate* structured tags (mood, occasion, complexity, audience):

```
prompt: "Tag this product: Crocs Classic Clogs (orange). Categories: comfort, casual, summer, controversial, ugly-cute. Output JSON: {tags: [...], audience: ..., style: ...}"
```

Output becomes a feature. Pinterest uses this for pin labels; Amazon COSMO does it for "common sense" knowledge generation; Spotify for podcast topics.

### 2.4 Cost economics

A single LLM call costs ~$0.01-$0.1 per item. For a 10M-item catalog, that's $100k-$1M one-time cost — manageable, and refreshable monthly. The cost stays out of the request path because it's offline.

---

## 3. LLM as ranker

The "vector search + LLM rerank" pattern (Module 32 has tech-stack details).

```mermaid
flowchart LR
    Q[User query / context] --> R[Retrieval<br/>top-100 from ANN]
    R --> P[LLM ranker<br/>"score these for relevance"]
    P --> TOP[Top-10]
```

### 3.1 Pointwise vs listwise prompts

Pointwise: "Given user X and item Y, score relevance 1-5." Easier to parallelize; less context-aware.

Listwise: "Given user X, here are 50 items; output the best 10 in order." Better quality; harder to evaluate; more expensive.

### 3.2 Cohere Rerank, Voyage rerank-2, Claude/GPT as ranker

- **Cohere Rerank v3+**: dedicated reranker; ~50 candidates → top-10 in ~100ms.
- **Voyage rerank-2**: similar.
- **Claude / GPT as reranker**: prompted; ~500-1500ms; expensive but flexible.

Production B2B startup stack: vector search → Cohere Rerank → optional Claude pass for top-5 if quality matters more than latency.

### 3.3 Distillation

Run an LLM ranker on logged queries to *generate labels*; train a small cross-encoder (BGE-reranker, MiniLM) to mimic it. The cross-encoder serves in production at 5-20ms per request.

This is the dominant 2024-2026 pattern for "LLM-quality rerank at non-LLM latency." Cohere Rerank itself is built this way.

---

## 4. Generative recommenders — the conceptual shift

Classical recsys: predict P(action | user, item) for each candidate independently.

Generative recsys: **autoregressively generate** the next user action (next item, next event):

```
P(next | history) = P(item_{t+1} | item_t, action_t, item_{t-1}, action_{t-1}, ...)
```

The model is a **decoder transformer** trained with cross-entropy over the item vocabulary (or a quantized version of it).

The retrieval problem collapses: instead of scoring all candidates, you **generate** the top-K via beam search or sampling. The ranking problem collapses: the same model emits action probabilities.

### 4.1 Why this matters

- **One model replaces N siloed models.** Recommendation, search, autoplay, push notifications all become "decode from a shared LLM."
- **Scaling laws** apply. More params + more data + longer sequence → predictable improvements (Wukong scaling law paper).
- **Cold start improves** through content tokenization (semantic IDs).
- **The funnel may collapse.** Retrieval + ranking + reranking → one model.

### 4.2 Why this isn't trivial

- **Item vocabulary explosion.** A YouTube-scale model needs to emit one of 10⁹ items. Softmax over a billion classes is infeasible. → semantic IDs.
- **Inference latency.** Autoregressive decoding can be slow. → speculative decoding, parallel sampling, MTIA-class accelerators.
- **Serving infrastructure.** Different from DLRM-style; needs KV cache, attention kernels.

---

## 5. TIGER — Semantic IDs (Google, Rajput et al. NeurIPS 2023)

**"Recommender Systems with Generative Retrieval"** — the breakthrough that made generative retrieval practical.

### 5.1 The problem

A standard recommender has an embedding row per item. Adding a new item means initialising a new embedding from zero — bad for cold start. And the row count grows linearly with the catalog, making the model expensive at scale.

### 5.2 The TIGER solution

1. **Encode each item** with a multimodal content encoder → dense vector.
2. **Quantize the vector** with **RQ-VAE (Residual Quantization VAE)** into a tuple of `(c_1, c_2, c_3, c_4)` discrete codes — each from a codebook of ~256 entries.
3. **Treat the tuple as the item's "semantic ID"**, generalizing across content-similar items.
4. **Train an encoder-decoder transformer** to autoregressively predict the next item's semantic ID from the user's history (a sequence of semantic IDs).

```mermaid
flowchart LR
    I[Item content<br/>text/image/audio] --> E[Content encoder]
    E --> V[Dense vector]
    V --> RQ[RQ-VAE]
    RQ --> SID[Semantic ID<br/>tuple of codes c_1, c_2, c_3, c_4]
    SID --> SEQ[Sequence: ..., SID_{t-1}, SID_t, ?]
    SEQ --> T[Decoder transformer]
    T --> NID[Next item's SID]
    NID --> ITEM[Decoded → actual item]
```

### 5.3 Why semantic IDs

- **Cold start**: a new item gets a semantic ID from its content alone — no warm-up needed.
- **Generalization**: items with shared prefix codes are content-similar; the model can leverage that.
- **Compact vocabulary**: ~4 × 256 codes = ~1024 tokens; the model generates 4 tokens per item.

### 5.4 Production status

- Google deployed it in some surfaces (search, YouTube ads have related work).
- Pinterest's "LIGER" is a generative-retrieval analog.
- Active research area; not yet ubiquitous.

---

## 6. HSTU — Generative Recommenders at Meta (Zhai et al. ICML 2024)

**"Actions Speak Louder than Words: Trillion-Parameter Sequential Transducers for Generative Recommendations"** — the most consequential recsys paper of 2024.

### 6.1 Core thesis

Treat recommendation as **next-token prediction over an interleaved sequence of `(item, action)` tokens**:

```
sequence = [item_1, action_1, item_2, action_2, item_3, action_3, ...]
predict next item and next action jointly
```

DLRM treats each (user, item) pair as independent. HSTU treats the user as a long sequence and the model predicts what they'll do next.

### 6.2 The HSTU layer

Self-attention is O(n²); for sequences of tens of thousands, that's prohibitive. HSTU replaces it with a **pointwise gated** attention variant whose FLOPs scale **linearly** with sequence length.

The HSTU block is a **hierarchical structure** that progressively encodes longer-range dependencies.

### 6.3 Scale

- **1.5T parameters**, mostly in embedding/projection tables.
- Sequence length: tens of thousands of events.
- Trained with LLM-style checkpoint sharding (Meta's training infra).

### 6.4 Production wins at Meta

- Deployed on Ads, Reels through 2024-2025.
- Significant relative E2E engagement gains over the prior DLRM-family ranker.
- In rollout for Feed.

### 6.5 Architectural implications

- Retrieval and ranking can collapse into a single autoregressive model.
- Feature engineering shifts: instead of designing 200 hand-crafted counter features, you tokenize more event types.
- Inference is heavier than DLRM. MTIA, INT8/FP8 quantization, KV caching all become critical.

---

## 7. P5 — Pretrain, Personalized Prompt, Predict (Geng et al. RecSys 2022)

**"Recommendation as Language Processing (RLP)"** — recast recommendation as text-to-text.

```
Input  prompt: "User 1234 has interacted with items [543, 122, 9]. What item will they like next?"
Output: "789"  (item ID as a string)
```

Built on T5. Multi-task: rating prediction, sequential recommendation, explanation generation, review summarization — all framed as text.

**Why it's interesting**: a single text-to-text model can do *all* of recsys tasks. **Why it's not (yet) production**: text-token-by-token generation is too slow at scale; semantic IDs (TIGER) are the practical evolution.

---

## 8. LLaRA, TallRec, CoLLM, RecLLM — LLM fine-tuning for recsys

A family of papers fine-tuning small LLMs (Llama 7-13B) on recommendation tasks:

- **TallRec** (Bao et al. RecSys 2023) — instruction-tune Llama to do recommendation.
- **LLaRA** (Liao et al. ICME 2024) — bridge ID embeddings and text via a projection.
- **CoLLM** (Zhang et al. 2024) — collaborative embeddings integrated with LLM.
- **RecLLM** (Friedman et al. Google 2023) — conversational recommendation via LLM.

Status: research-grade. Best for:
- **Conversational recommenders** (multi-turn refinement).
- **Cold-start surfaces** where content understanding helps.
- **Long-tail / niche domains** where general-knowledge LLMs add value.

Production deployments exist but are smaller-scale (B2B, niche catalogs); the latency / cost makes them hard at consumer-internet scale.

---

## 9. HLLM — Hierarchical LLM (ByteDance, Chen et al. 2024)

A two-level LLM architecture for sequential recommendation:

1. **Item LLM** produces dense representations from item content.
2. **User LLM** processes sequences of item representations to predict the next item.

Released by ByteDance in 2024 — paralleling HSTU's direction at TikTok/Douyin.

---

## 10. Scaling laws for recsys (Wukong, Meta 2024)

**"Wukong: Towards a Scaling Law for Large-Scale Recommendation"** showed that recsys scaling looks like LLM scaling:

```
performance ~ compute^α
```

over a range of model sizes, batch sizes, and data volumes. The exponents are smaller than LLM scaling but real and consistent.

Practical implication: you can plan recsys compute investment the same way you plan LLM compute — more params + more tokens + longer context = predictable improvements.

---

## 11. Conversational and agentic recommenders

The 2024-2026 frontier:

- **Conversational recommenders**: the user refines their preference through dialogue ("show me thrillers but not horror; less violent than X"). LLM handles the dialogue; recsys backend retrieves and ranks.
- **Agentic shopping**: an LLM agent navigates marketplaces on the user's behalf (Operator, Claude Computer Use). Implication: agents may not click ads — they parse structured data. The shape of "ads" may need to change.
- **AI DJ (Spotify)** is a deployed instance: LLM commentary + recsys + TTS.
- **Bing Copilot, Perplexity, Google AI Overviews**: sponsored answers in chat. Attribution and brand safety are unsolved.

---

## 12. Production trade-offs summary

| Approach | Cost | Latency | Cold start | Production ready |
|----------|------|---------|------------|------------------|
| LLM as feature extractor | Low (offline) | None online | Excellent | Yes — default in 2024-2026 |
| LLM as ranker (Cohere, etc.) | Medium | 100-500 ms | Good | Yes — common in B2B |
| LLM rerank with distillation | Medium training | 5-20 ms | Good | Yes — consumer-scale |
| TIGER / semantic IDs | High training | Comparable to two-tower | Excellent | Early production |
| HSTU / generative recs | Very high training | Higher than DLRM; doable on MTIA | Excellent | Meta deployed; others experimenting |
| Full LLM-as-recsys (P5 style) | Very high training + serving | Too slow at scale | Excellent for cold | Research |

---

## 13. Sample code: simple generative recommender (using a tiny transformer)

(See [`code/12_generative_rec.py`](code/12_generative_rec.py) for a runnable version on MovieLens.)

```python
import torch, torch.nn as nn

class GenRec(nn.Module):
    """Tiny generative recommender: treats sequences of item IDs as a language."""
    def __init__(self, vocab_size, d_model=64, n_heads=2, n_layers=2, max_len=50):
        super().__init__()
        self.tok_emb = nn.Embedding(vocab_size, d_model)
        self.pos_emb = nn.Embedding(max_len, d_model)
        layer = nn.TransformerEncoderLayer(d_model, n_heads, batch_first=True)
        self.encoder = nn.TransformerEncoder(layer, n_layers)
        self.head = nn.Linear(d_model, vocab_size)

    def forward(self, seq):
        pos = torch.arange(seq.size(1), device=seq.device)
        x = self.tok_emb(seq) + self.pos_emb(pos)
        mask = nn.Transformer.generate_square_subsequent_mask(seq.size(1)).to(seq.device)
        h = self.encoder(x, mask=mask)
        return self.head(h)         # (B, L, V) logits over items

    @torch.no_grad()
    def generate(self, prefix, k=10):
        # Greedy/top-K from the last position
        logits = self.forward(prefix)[:, -1, :]
        return logits.topk(k=k).indices
```

That's the kernel of TIGER / HSTU — without semantic IDs and at toy scale. The path from this to production HSTU is engineering, not algorithms.

---

## 14. Sanity check

1. Why is "LLM as feature extractor" the most-deployed of the three LLM-in-recsys patterns?
2. What problem do semantic IDs (TIGER's RQ-VAE codes) solve that vanilla item ID embeddings can't?
3. HSTU's headline trick is replacing standard self-attention with a pointwise gated variant. Why?
4. P5 frames every recsys task as text-to-text. Why is this elegant for research but impractical for billion-user surfaces?
5. Generative recommenders enable retrieval-via-decoding. What infrastructure must change vs a DLRM-style stack?
6. A B2B search startup wants LLM-quality ranking at 10ms p99 latency. What architecture would you propose?
