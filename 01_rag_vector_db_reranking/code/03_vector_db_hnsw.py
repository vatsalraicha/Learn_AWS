# %% [markdown]
# # Notebook 03 — Vector DB Internals: HNSW Tuning Experiments
#
# **Pairs with:** [Module 3 — Vector Databases](../03_vector_databases.md)
#
# **What you'll see:**
# 1. Build a corpus of ~5000 vectors using a small local embedder (no API cost).
# 2. Compare **flat (brute force)** vs **HNSW** indices on:
#    - Recall@10 (vs ground truth)
#    - Query latency (p50, p95)
# 3. **Tune HNSW** (`M`, `ef_construction`, `ef_search`) — see the recall/latency Pareto frontier.
# 4. Show why "approximate nearest neighbor" is a tradeoff, not a free lunch.
#
# **Stack:** sentence-transformers (BGE-small for cheap local embeddings), lancedb, numpy. **No OpenAI.**

# %% [markdown]
# ## Setup — generate a corpus and embed locally

# %%
import os
import time
import warnings
from pathlib import Path
from typing import List, Tuple, Dict
import random
import numpy as np
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")
warnings.filterwarnings("ignore", category=UserWarning)
random.seed(42)
np.random.seed(42)

# We'll synthesize a corpus by taking a small "topic" per chunk and varying it. Realistic enough
# to produce non-trivial nearest-neighbor structure; cheap enough to embed locally.
TOPICS = [
    "401(k) retirement plan match policy",
    "parental leave benefits for adoptive parents",
    "B2B refund policy for annual contracts",
    "vector database HNSW index tuning",
    "BM25 sparse retrieval algorithm",
    "Reciprocal Rank Fusion for hybrid search",
    "cross-encoder reranker model architecture",
    "ColBERT late interaction multi-vector",
    "self-attention mechanism in transformers",
    "GraphRAG community summarization",
]
ADJECTIVES = ["modern", "deprecated", "experimental", "production-ready", "internal", "external", "Q4 2024", "legacy"]
SUBJECTS = ["overview", "implementation notes", "best practices", "common pitfalls", "tuning guide",
            "performance comparison", "cost analysis", "case study"]

def synthesize_corpus(n: int = 5000) -> List[str]:
    """Make N short texts by combining topic + adjective + subject + filler."""
    chunks = []
    for i in range(n):
        topic = TOPICS[i % len(TOPICS)]
        adj = ADJECTIVES[i % len(ADJECTIVES)]
        subj = SUBJECTS[i % len(SUBJECTS)]
        chunks.append(
            f"This {adj} document covers {subj} for {topic}. "
            f"It includes details on configuration, expected outcomes, and common edge cases. "
            f"Reference id: {i}."
        )
    random.shuffle(chunks)
    return chunks

corpus = synthesize_corpus(5000)
print(f"Synthesized corpus: {len(corpus)} chunks")

# %% [markdown]
# ## Embed locally with BGE-small (cheap, fast, no API)

# %%
from sentence_transformers import SentenceTransformer

print("Loading BGE-small-en-v1.5 (first run downloads ~130MB)...")
model = SentenceTransformer("BAAI/bge-small-en-v1.5")
print(f"Embedding {len(corpus)} chunks...")
t0 = time.time()
vectors = model.encode(corpus, batch_size=64, show_progress_bar=False, normalize_embeddings=True)
print(f"Done. Shape: {vectors.shape}, took {time.time()-t0:.1f}s")

# %% [markdown]
# ## Build a flat index (ground truth — exact nearest neighbor by brute force)
#
# We need this as the baseline to measure recall against.

# %%
def flat_search(query_vec: np.ndarray, vectors: np.ndarray, top_k: int = 10) -> List[int]:
    """Exact brute-force nearest neighbor by cosine (vectors are normalized)."""
    scores = vectors @ query_vec
    return list(np.argsort(scores)[::-1][:top_k])

# %% [markdown]
# ## Build a flat-only LanceDB table for baseline timing

# %%
import lancedb
import pyarrow as pa

db = lancedb.connect("./lancedb_storage")
for tname in ["vectors_flat", "vectors_hnsw"]:
    if tname in db.table_names():
        db.drop_table(tname)

print("Building flat (no index)...")
records = [{"id": i, "text": t, "vector": vec.tolist()} for i, (t, vec) in enumerate(zip(corpus, vectors))]
flat_table = db.create_table("vectors_flat", data=records)
print(f"Flat table: {len(records)} rows")

# %% [markdown]
# ## Build HNSW with default tuning

# %%
print("Building HNSW index (M=16, ef_construction=100)...")
t0 = time.time()
hnsw_table = db.create_table("vectors_hnsw", data=records)
hnsw_table.create_index(
    metric="cosine",
    index_type="IVF_HNSW_SQ",   # LanceDB's HNSW variant; SQ = scalar quantization
    num_partitions=1,           # single-partition for small corpus
    num_sub_vectors=16,
    m=16,
    ef_construction=100,
)
print(f"Index built in {time.time()-t0:.1f}s")

# %% [markdown]
# ## Generate query set and compute ground truth

# %%
def make_queries(n: int = 50) -> List[str]:
    return [
        f"How do I configure {random.choice(TOPICS)} for {random.choice(SUBJECTS)}?"
        for _ in range(n)
    ]

queries = make_queries(50)
print(f"Embedding {len(queries)} queries...")
query_vecs = model.encode(queries, normalize_embeddings=True)

# Ground truth: exact top-10 from brute force
print("Computing ground-truth nearest neighbors (brute force)...")
ground_truth = []
for q in query_vecs:
    ground_truth.append(set(flat_search(q, vectors, top_k=10)))

# %% [markdown]
# ## Benchmark: flat search vs HNSW
#
# Measure (1) recall@10 against ground truth and (2) query latency p50/p95.

# %%
def benchmark(table, query_vecs: np.ndarray, ground_truth: List[set]) -> Dict:
    latencies = []
    recalls = []
    for q, gt in zip(query_vecs, ground_truth):
        t0 = time.perf_counter()
        results = table.search(q).limit(10).to_list()
        latencies.append((time.perf_counter() - t0) * 1000)
        retrieved = set(r["id"] for r in results)
        recalls.append(len(retrieved & gt) / len(gt))
    return {
        "p50_ms": float(np.percentile(latencies, 50)),
        "p95_ms": float(np.percentile(latencies, 95)),
        "p99_ms": float(np.percentile(latencies, 99)),
        "recall@10": float(np.mean(recalls)),
    }

print("\n=== Benchmarks ===")
flat_metrics = benchmark(flat_table, query_vecs, ground_truth)
print(f"Flat (brute force):  p50={flat_metrics['p50_ms']:6.2f}ms  p95={flat_metrics['p95_ms']:6.2f}ms  recall@10={flat_metrics['recall@10']:.3f}")

hnsw_metrics = benchmark(hnsw_table, query_vecs, ground_truth)
print(f"HNSW (default M=16): p50={hnsw_metrics['p50_ms']:6.2f}ms  p95={hnsw_metrics['p95_ms']:6.2f}ms  recall@10={hnsw_metrics['recall@10']:.3f}")

# %% [markdown]
# At 5000 vectors, flat is fast and HNSW barely helps. **The interesting region is 100K - 100M
# vectors** where flat search is infeasible and HNSW shines.
#
# Try this at home: bump `synthesize_corpus(50000)` and re-run. Flat will slow significantly while
# HNSW stays roughly constant — the whole point of ANN.

# %% [markdown]
# ## Tuning sweep — vary `ef_search` (query-time beam width)
#
# `ef_search` is the only HNSW parameter you can adjust **after** the index is built.
# Higher = more recall, more latency.

# %%
print("\n=== HNSW ef_search sweep ===")
print(f"{'ef_search':<12} {'p50_ms':<10} {'p95_ms':<10} {'recall@10':<10}")
print("-" * 50)

for ef in [10, 20, 50, 100, 200]:
    # LanceDB allows passing nprobes per query; ef_search is set via the search builder
    latencies = []
    recalls = []
    for q, gt in zip(query_vecs, ground_truth):
        t0 = time.perf_counter()
        results = hnsw_table.search(q).nprobes(ef).limit(10).to_list()
        latencies.append((time.perf_counter() - t0) * 1000)
        retrieved = set(r["id"] for r in results)
        recalls.append(len(retrieved & gt) / len(gt))
    p50 = float(np.percentile(latencies, 50))
    p95 = float(np.percentile(latencies, 95))
    rec = float(np.mean(recalls))
    print(f"{ef:<12} {p50:<10.2f} {p95:<10.2f} {rec:<10.3f}")

# %% [markdown]
# **The classic ANN tradeoff:** as `ef_search` (beam width) grows, recall climbs toward 1.0
# but latency grows roughly proportionally. Pick a point on the Pareto frontier that satisfies
# your SLO.
#
# In production: tune `ef_search` against a representative eval set. The default is rarely optimal.

# %% [markdown]
# ## Things to try next
#
# 1. **Scale the corpus to 50K or 100K** — see flat search start to suffer while HNSW holds steady.
# 2. **Vary M and ef_construction** — these affect index BUILD quality. Bigger = slower index, better recall.
# 3. **Compare against IVF_PQ** — same LanceDB, different `index_type`. Memory cheaper, slightly worse recall.
# 4. **Add metadata filtering** — `.where("category = 'foo'")` chained off `.search()`. Watch what
#    happens to HNSW recall when filter selectivity is high (Module 3 covers this).
# 5. **Plot the Pareto curve** — collect (recall, latency) for many `ef_search` values, plot it.
#    The shape tells you where you're "wasting" recall or latency.
#
# ## What this demonstrated
# - **Flat search** has perfect recall but doesn't scale.
# - **HNSW** trades a small recall hit for big speed gains at scale.
# - **`ef_search` is the production tuning knob** — adjust without rebuilding the index.
# - **5K vectors is too small** to see the win. Try 50K to feel the difference.
