# %% [markdown]
# # Notebook 05 — Hybrid Retrieval (BM25 + Dense + RRF)
#
# **Pairs with:** [Module 5 — Retrieval Strategies](../05_retrieval_strategies.md)
#
# **What you'll see:**
# 1. A query that pure dense retrieval gets wrong (exact-match miss).
# 2. A query that pure BM25 gets wrong (paraphrase miss).
# 3. How **hybrid + RRF** fixes both.
# 4. The actual line-by-line of Reciprocal Rank Fusion.
#
# **Stack:** LanceDB (embedded vector store), `rank_bm25` (sparse), Voyage `voyage-3-large` (embeddings).
# **No OpenAI.**
#
# Run: `python 05_hybrid_retrieval.py`  or open in VS Code and Run Cell.

# %% [markdown]
# ## Setup

# %%
import os
from pathlib import Path
from typing import List, Tuple, Dict
from collections import defaultdict

import numpy as np
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")  # main repo .env

# Local seed corpus
import sys
sys.path.insert(0, str(Path(__file__).parent / "data"))
from seed_corpus import get_corpus, get_eval_queries  # noqa: E402

corpus = get_corpus()
print(f"Corpus loaded: {len(corpus)} chunks")

# %% [markdown]
# ## Build the dense (vector) index with LanceDB + Voyage embeddings
#
# Why these choices:
# - **Voyage `voyage-3-large`** — strong English embedder; not OpenAI.
# - **LanceDB** — embedded, no server, fast on Mac. Stores in `./lancedb_storage/`.

# %%
import voyageai
import lancedb
import pyarrow as pa

vo_client = voyageai.Client(api_key=os.environ["VOYAGE_API_KEY"])

def embed_texts(texts: List[str], input_type: str) -> List[List[float]]:
    """Embed a batch with Voyage. input_type='document' for indexing, 'query' at retrieve time."""
    result = vo_client.embed(texts, model="voyage-3-large", input_type=input_type)
    return result.embeddings

# Build LanceDB table
db = lancedb.connect("./lancedb_storage")
if "rag_chunks" in db.table_names():
    db.drop_table("rag_chunks")

print("Embedding corpus chunks...")
chunk_ids = [c[0] for c in corpus]
chunk_texts = [c[1] for c in corpus]
chunk_metas = [c[2] for c in corpus]
embeddings = embed_texts(chunk_texts, input_type="document")

records = [
    {
        "chunk_id": cid,
        "text": text,
        "vector": vec,
        "doc_type": meta.get("doc_type", ""),
        "topic": meta.get("topic", ""),
        "year": meta.get("year", 0),
    }
    for cid, text, meta, vec in zip(chunk_ids, chunk_texts, chunk_metas, embeddings)
]
table = db.create_table("rag_chunks", data=records)
print(f"LanceDB table built: {len(records)} chunks indexed.")

# %% [markdown]
# ## Build the sparse (BM25) index

# %%
from rank_bm25 import BM25Okapi
import re

def simple_tokenize(text: str) -> List[str]:
    return re.findall(r"\w+", text.lower())

tokenized_corpus = [simple_tokenize(t) for t in chunk_texts]
bm25 = BM25Okapi(tokenized_corpus)
print("BM25 index built.")

# %% [markdown]
# ## Define retrievers

# %%
def dense_retrieve(query: str, top_k: int = 5) -> List[Tuple[str, float]]:
    qvec = embed_texts([query], input_type="query")[0]
    results = table.search(qvec).limit(top_k).to_list()
    return [(r["chunk_id"], 1.0 - r["_distance"]) for r in results]  # convert distance to similarity

def bm25_retrieve(query: str, top_k: int = 5) -> List[Tuple[str, float]]:
    scores = bm25.get_scores(simple_tokenize(query))
    ranked = np.argsort(scores)[::-1][:top_k]
    return [(chunk_ids[i], float(scores[i])) for i in ranked if scores[i] > 0]


# %% [markdown]
# ## Reciprocal Rank Fusion — the actual algorithm
#
# `RRF(d) = Σ_i 1 / (k + rank_i(d))` with k=60 default. Note we never use the raw scores —
# only the ranks from each retriever. This is what makes RRF immune to score-scale mismatch.

# %%
def rrf_fuse(rankings: List[List[Tuple[str, float]]], k: int = 60) -> List[Tuple[str, float]]:
    """Fuse multiple ranked lists. Each list: [(chunk_id, score), ...]."""
    fused: Dict[str, float] = defaultdict(float)
    for ranking in rankings:
        for rank, (chunk_id, _score) in enumerate(ranking):
            fused[chunk_id] += 1.0 / (k + rank + 1)  # rank+1 because rank starts at 0
    return sorted(fused.items(), key=lambda x: x[1], reverse=True)


def hybrid_retrieve(query: str, top_k: int = 5) -> List[Tuple[str, float]]:
    dense = dense_retrieve(query, top_k=10)
    sparse = bm25_retrieve(query, top_k=10)
    fused = rrf_fuse([dense, sparse])
    return fused[:top_k]


# %% [markdown]
# ## See the failure modes
#
# ### Failure 1 — exact-match query that dense embedding fumbles
# A query asking about a specific filename or term. BM25 nails it; dense gets close but
# can be distracted by topical similarity.

# %%
query_1 = "401k_plan_2024.pdf vesting schedule"  # exact filename + jargon

print(f"\nQUERY: {query_1}")
print("-" * 80)
print("Dense (vector):")
for cid, score in dense_retrieve(query_1, top_k=3):
    print(f"  {cid:8s}  sim={score:.3f}  {next(c[1] for c in corpus if c[0]==cid)[:80]}...")
print("BM25 (sparse):")
for cid, score in bm25_retrieve(query_1, top_k=3):
    print(f"  {cid:8s}  bm25={score:.2f}  {next(c[1] for c in corpus if c[0]==cid)[:80]}...")
print("HYBRID (RRF):")
for cid, score in hybrid_retrieve(query_1, top_k=3):
    print(f"  {cid:8s}  rrf={score:.4f}  {next(c[1] for c in corpus if c[0]==cid)[:80]}...")

# %% [markdown]
# ### Failure 2 — paraphrase that BM25 misses but dense gets

# %%
query_2 = "how long until I'm fully invested in my retirement contributions"  # no token overlap with "401k vesting"

print(f"\nQUERY: {query_2}")
print("-" * 80)
print("Dense (vector):")
for cid, score in dense_retrieve(query_2, top_k=3):
    print(f"  {cid:8s}  sim={score:.3f}  {next(c[1] for c in corpus if c[0]==cid)[:80]}...")
print("BM25 (sparse):")
for cid, score in bm25_retrieve(query_2, top_k=3):
    print(f"  {cid:8s}  bm25={score:.2f}  {next(c[1] for c in corpus if c[0]==cid)[:80]}...")
print("HYBRID (RRF):")
for cid, score in hybrid_retrieve(query_2, top_k=3):
    print(f"  {cid:8s}  rrf={score:.4f}  {next(c[1] for c in corpus if c[0]==cid)[:80]}...")

# %% [markdown]
# ## Quick eval — how does each retriever do across the eval set?
#
# Recall@3 = does the gold chunk land in top-3?

# %%
queries = get_eval_queries()

def recall_at_k(retriever_fn, queries, k: int = 3) -> float:
    hits = 0
    for q, _topic, gold in queries:
        retrieved = [cid for cid, _ in retriever_fn(q, top_k=k)]
        if any(g in retrieved for g in gold):
            hits += 1
    return hits / len(queries)

print(f"\nRecall@3 over {len(queries)} eval queries:")
print(f"  Dense only:  {recall_at_k(dense_retrieve, queries):.2f}")
print(f"  BM25 only:   {recall_at_k(bm25_retrieve, queries):.2f}")
print(f"  Hybrid RRF:  {recall_at_k(hybrid_retrieve, queries):.2f}")

# %% [markdown]
# ## Things to try next
#
# 1. **Weighted RRF** — change `rrf_fuse` to take per-retriever weights. Tune empirically.
# 2. **Different k for RRF** — try k=10, 30, 60, 100. The standard 60 was empirical from the original paper.
# 3. **Swap embedder** — try BGE-M3 (open-source, multilingual) and compare:
#    ```python
#    from FlagEmbedding import BGEM3FlagModel
#    model = BGEM3FlagModel('BAAI/bge-m3')
#    embeddings = model.encode(texts)['dense_vecs']
#    ```
# 4. **Add metadata filtering** — LanceDB supports `.where("year = 2024")` chained off `.search()`.
# 5. **Inspect the BM25 / dense disagreement** — log queries where the top-1 from each retriever differs.
#    Those are the queries that hybrid is "earning its keep" on.
#
# ## What this demonstrated
# - Pure dense fails on jargon / filenames / IDs.
# - Pure BM25 fails on paraphrase.
# - **RRF fuses without needing score normalization** — that's the trick.
# - Hybrid recall consistently ≥ either component alone.

if __name__ == "__main__":
    pass
