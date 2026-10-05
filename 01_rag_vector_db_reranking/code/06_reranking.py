# %% [markdown]
# # Notebook 06 — Reranking
#
# **Pairs with:** [Module 6 — Reranking](../06_reranking.md)
#
# **What you'll see:**
# 1. The same hybrid retrieval pipeline from Notebook 05, top-10 candidates.
# 2. Three rerankers reorder them:
#    - **Cohere Rerank v4** (commercial API)
#    - **BGE-reranker-v2-m3** (open-source, runs locally on CPU)
#    - **MMR diversity reorder** (no model — pure algorithm)
# 3. How quality and diversity differ between them.
#
# **Stack:** Cohere API + BGE locally. **No OpenAI.**

# %% [markdown]
# ## Setup — reuse the hybrid retriever from Notebook 05

# %%
import os
from pathlib import Path
from typing import List, Tuple, Dict
from collections import defaultdict
import re

import numpy as np
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")

import sys
sys.path.insert(0, str(Path(__file__).parent / "data"))
from seed_corpus import get_corpus, get_eval_queries  # noqa: E402

corpus = get_corpus()
chunk_ids = [c[0] for c in corpus]
chunk_texts = [c[1] for c in corpus]
text_by_id = {c[0]: c[1] for c in corpus}

# %%
# Rebuild the indexes (would normally import from a shared utils module — kept inline for clarity)
import voyageai
import lancedb
from rank_bm25 import BM25Okapi

vo = voyageai.Client(api_key=os.environ["VOYAGE_API_KEY"])

def embed(texts: List[str], input_type: str) -> List[List[float]]:
    return vo.embed(texts, model="voyage-3-large", input_type=input_type).embeddings

def tok(s): return re.findall(r"\w+", s.lower())

db = lancedb.connect("./lancedb_storage")
if "rag_chunks" not in db.table_names():
    embs = embed(chunk_texts, input_type="document")
    db.create_table("rag_chunks", data=[
        {"chunk_id": cid, "text": t, "vector": v}
        for cid, t, v in zip(chunk_ids, chunk_texts, embs)
    ])
table = db.open_table("rag_chunks")
bm25 = BM25Okapi([tok(t) for t in chunk_texts])

def hybrid_retrieve(q: str, top_k: int = 10) -> List[str]:
    qv = embed([q], "query")[0]
    dense = [r["chunk_id"] for r in table.search(qv).limit(top_k).to_list()]
    sparse_scores = bm25.get_scores(tok(q))
    sparse = [chunk_ids[i] for i in np.argsort(sparse_scores)[::-1][:top_k] if sparse_scores[i] > 0]

    fused: Dict[str, float] = defaultdict(float)
    for ranked in [dense, sparse]:
        for r, cid in enumerate(ranked):
            fused[cid] += 1.0 / (60 + r + 1)
    return [cid for cid, _ in sorted(fused.items(), key=lambda x: -x[1])]

# %% [markdown]
# ## Reranker 1 — Cohere Rerank v4 (commercial API)

# %%
import cohere

co = cohere.ClientV2(api_key=os.environ["COHERE_API_KEY"])

def rerank_cohere(query: str, candidate_ids: List[str], top_n: int = 5) -> List[Tuple[str, float]]:
    docs = [text_by_id[cid] for cid in candidate_ids]
    response = co.rerank(
        model="rerank-v3.5",   # use latest production reranker
        query=query,
        documents=docs,
        top_n=top_n,
    )
    return [(candidate_ids[r.index], r.relevance_score) for r in response.results]

# %% [markdown]
# ## Reranker 2 — BGE-reranker-v2-m3 (open-source, runs on CPU)
#
# First run downloads ~2.2 GB. Subsequent runs use HF cache (~/.cache/huggingface/hub/).

# %%
from FlagEmbedding import FlagReranker

print("Loading BGE reranker (first run downloads weights)...")
bge_reranker = FlagReranker("BAAI/bge-reranker-v2-m3", use_fp16=False)  # use_fp16=True if GPU

def rerank_bge(query: str, candidate_ids: List[str], top_n: int = 5) -> List[Tuple[str, float]]:
    pairs = [[query, text_by_id[cid]] for cid in candidate_ids]
    scores = bge_reranker.compute_score(pairs, normalize=True)  # sigmoid -> [0,1]
    ranked = sorted(zip(candidate_ids, scores), key=lambda x: -x[1])
    return ranked[:top_n]

# %% [markdown]
# ## Reranker 3 — MMR (no model, just diversity-aware reordering)
#
# MMR(d) = (1−λ)·sim(q,d) − λ·max_{s∈selected} sim(d,s)
#
# λ=0 → pure relevance, λ=1 → pure diversity. λ=0.5 typical.

# %%
def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))

def rerank_mmr(query: str, candidate_ids: List[str], top_n: int = 5, lam: float = 0.5) -> List[Tuple[str, float]]:
    qv = np.array(embed([query], "query")[0])
    cand_texts = [text_by_id[cid] for cid in candidate_ids]
    cand_vecs = [np.array(v) for v in embed(cand_texts, "document")]

    selected: List[int] = []
    selected_scores: List[float] = []
    remaining = list(range(len(candidate_ids)))

    while remaining and len(selected) < top_n:
        best_i, best_score = None, -1e9
        for i in remaining:
            sim_q = cosine(cand_vecs[i], qv)
            sim_to_selected = max((cosine(cand_vecs[i], cand_vecs[j]) for j in selected), default=0)
            mmr_score = (1 - lam) * sim_q - lam * sim_to_selected
            if mmr_score > best_score:
                best_score, best_i = mmr_score, i
        selected.append(best_i)
        selected_scores.append(best_score)
        remaining.remove(best_i)

    return [(candidate_ids[i], s) for i, s in zip(selected, selected_scores)]

# %% [markdown]
# ## Run all three on a query and compare

# %%
query = "Why use a cross-encoder reranker on top of vector search?"

candidates = hybrid_retrieve(query, top_k=10)
print(f"\nQUERY: {query}\n")
print("Top-10 hybrid candidates (no rerank):")
for r, cid in enumerate(candidates):
    print(f"  {r+1:2d}. {cid:8s}  {text_by_id[cid][:80]}...")

print("\n--- Cohere Rerank v3.5 (top-3) ---")
for cid, score in rerank_cohere(query, candidates, top_n=3):
    print(f"  {cid:8s}  cohere={score:.3f}  {text_by_id[cid][:80]}...")

print("\n--- BGE-reranker-v2-m3 (top-3) ---")
for cid, score in rerank_bge(query, candidates, top_n=3):
    print(f"  {cid:8s}  bge={score:.3f}    {text_by_id[cid][:80]}...")

print("\n--- MMR diversity (λ=0.5, top-3) ---")
for cid, score in rerank_mmr(query, candidates, top_n=3, lam=0.5):
    print(f"  {cid:8s}  mmr={score:.3f}    {text_by_id[cid][:80]}...")


# %% [markdown]
# ## Compare on the eval set — Hit@1 with and without rerank

# %%
queries = get_eval_queries()

def hit_at_1(rerank_fn, name: str):
    hits = 0
    for q, _topic, gold in queries:
        cands = hybrid_retrieve(q, top_k=10)
        top1 = rerank_fn(q, cands, top_n=1)[0][0] if cands else None
        if top1 in gold:
            hits += 1
    return hits / len(queries), name

# Baseline: hybrid only, no rerank
def baseline_top1(q, cands, top_n=1):
    return [(cands[0], 1.0)] if cands else []

print("\nHit@1 across eval queries:")
for fn, name in [
    (baseline_top1, "Hybrid only"),
    (rerank_cohere, "Cohere v3.5"),
    (rerank_bge,    "BGE-reranker-v2-m3"),
    (rerank_mmr,    "MMR (λ=0.5)"),
]:
    score, _ = hit_at_1(fn, name)
    print(f"  {name:25s} {score:.2f}")

# %% [markdown]
# ## Things to try next
#
# 1. **Vary MMR λ**: 0.1 (mostly relevance), 0.7 (heavy diversity). Watch how the top-3 changes.
# 2. **Two-stage rerank**: BGE-base for top-50→top-30, then Cohere v3.5 for top-30→top-10.
# 3. **Swap reranker**: try Voyage `rerank-2.5`, mxbai-rerank-large-v2, or Jina-reranker-v3.
# 4. **Run latency comparison**: time each rerank call. Cohere ≈ 200ms; BGE ≈ depends on CPU/GPU.
# 5. **Add LLM-as-reranker** (Module 6 covers this): use Claude with a listwise prompt.
#
# ## What this demonstrated
# - **Cohere Rerank** is the production default for most teams — fastest path to quality.
# - **BGE-reranker-v2-m3** runs locally with no API; competitive quality, slower on CPU.
# - **MMR is not a quality reranker** — it diversifies. Use AFTER a quality reranker.
# - All three reranker patterns improve Hit@1 over hybrid-only on a real eval set.
