# %% [markdown]
# # Notebook 15 — Multilingual Retrieval & Lost-in-the-Middle
#
# **Pairs with:** [Module 15 — Multilingual & Long-Context Failures](../15_multilingual_long_context.md)
#
# **What you'll see:**
# 1. **BGE-M3** doing **cross-lingual** retrieval — English query, Spanish/French docs.
# 2. The **"Lost in the Middle"** effect — same answer, different positions in a long context.
# 3. The **U-aware reordering trick** that exploits the U-curve instead of fighting it.
#
# **Stack:** FlagEmbedding (BGE-M3, 100+ languages), anthropic. **No OpenAI.**

# %% [markdown]
# ## Part 1 — Multilingual / cross-lingual retrieval with BGE-M3

# %%
import os
import time
from pathlib import Path
from typing import List, Tuple
import numpy as np
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")

# %%
print("Loading BGE-M3 (first run downloads ~2.2 GB into HF cache)...")
from FlagEmbedding import BGEM3FlagModel
m3 = BGEM3FlagModel("BAAI/bge-m3", use_fp16=False)
print("Loaded.")

# %%
# A multilingual mini-corpus on the same topic family
multilingual_corpus = [
    # English
    ("en_001", "Acme matches 100% of employee 401(k) contributions up to 4% of salary.", "en"),
    ("en_002", "B2B customers may request a refund within 30 days of purchase.", "en"),
    ("en_003", "Birth parents receive 16 weeks of paid parental leave.", "en"),
    # Spanish
    ("es_001", "Acme iguala el 100% de las contribuciones de los empleados al 401(k) hasta el 4% del salario.", "es"),
    ("es_002", "Los clientes B2B pueden solicitar un reembolso dentro de los 30 días posteriores a la compra.", "es"),
    ("es_003", "Los padres biológicos reciben 16 semanas de licencia parental remunerada.", "es"),
    # French
    ("fr_001", "Acme égale 100% des cotisations 401(k) des employés jusqu'à 4% du salaire.", "fr"),
    ("fr_002", "Les clients B2B peuvent demander un remboursement dans les 30 jours suivant l'achat.", "fr"),
    ("fr_003", "Les parents biologiques reçoivent 16 semaines de congé parental rémunéré.", "fr"),
    # Hindi (Devanagari)
    ("hi_001", "एक्मे कर्मचारी 401(k) योगदान का 100% तक मिलान करता है, अधिकतम 4% वेतन तक।", "hi"),
    ("hi_002", "B2B ग्राहक खरीद के 30 दिनों के भीतर रिफंड का अनुरोध कर सकते हैं।", "hi"),
]

corpus_ids = [c[0] for c in multilingual_corpus]
corpus_texts = [c[1] for c in multilingual_corpus]
corpus_langs = [c[2] for c in multilingual_corpus]

print(f"\nEmbedding {len(corpus_texts)} multilingual chunks with BGE-M3...")
embeddings = m3.encode(corpus_texts, return_dense=True)["dense_vecs"]
embeddings = np.array(embeddings)
print(f"Done. Shape: {embeddings.shape}")

# %%
def cross_lingual_search(query: str, top_k: int = 3) -> List[Tuple[str, str, float]]:
    qv = np.array(m3.encode([query], return_dense=True)["dense_vecs"][0])
    qv = qv / np.linalg.norm(qv)
    docs_n = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    scores = docs_n @ qv
    top = np.argsort(scores)[::-1][:top_k]
    return [(corpus_ids[i], corpus_langs[i], float(scores[i])) for i in top]

# %%
# Query in English; corpus has en/es/fr/hi documents on the same topic
query_en = "What is our 401k match policy?"
print(f"\n=== Query (English): {query_en}")
for cid, lang, score in cross_lingual_search(query_en):
    print(f"  [{lang}] {cid}  sim={score:.3f}  {corpus_texts[corpus_ids.index(cid)][:70]}...")

# Query in Spanish — should retrieve all 4 language variants of the same topic
query_es = "¿Cuál es la política de igualación del 401k?"
print(f"\n=== Query (Spanish): {query_es}")
for cid, lang, score in cross_lingual_search(query_es):
    print(f"  [{lang}] {cid}  sim={score:.3f}  {corpus_texts[corpus_ids.index(cid)][:70]}...")

# Query in Hindi
query_hi = "401k मिलान नीति क्या है?"
print(f"\n=== Query (Hindi): {query_hi}")
for cid, lang, score in cross_lingual_search(query_hi):
    print(f"  [{lang}] {cid}  sim={score:.3f}  {corpus_texts[corpus_ids.index(cid)][:70]}...")

# %% [markdown]
# Notice cross-lingual retrieval finds the relevant doc *regardless of source language*.
# BGE-M3 (and similar 100+ language embedders) map all languages to a shared semantic space.
#
# **Production caveat:** quality is uneven. English usually scores 10-30 points higher than
# non-English on the same task. Track per-language SLOs.

# %% [markdown]
# ## Part 2 — Lost in the Middle
#
# Show how answer accuracy depends on WHERE the relevant info sits in a long context.
# We'll plant a known fact ("the secret code is XKZ-742") at three positions and ask Claude
# to retrieve it.

# %%
from anthropic import Anthropic
client = Anthropic()

# Build a long, plausible-looking distractor context — many short paragraphs about HR / policy / tech.
DISTRACTOR_PARAGRAPHS = [
    "Acme's compensation philosophy bases pay on role, level, location, and performance benchmarked quarterly.",
    "The B2B refund policy was updated in Q4 2024 to allow 30-day refunds, superseding the prior 14-day rule.",
    "Vector databases differ in their indexing algorithms; HNSW dominates most modern benchmarks.",
    "Reciprocal Rank Fusion combines retrievers without score normalization using k=60 by default.",
    "Cross-encoders cannot serve as primary retrievers due to per-pair compute cost at scale.",
    "Parental leave at Acme is 16 weeks for birth parents and 8 weeks for adoptive parents.",
    "Self-attention computes pairwise scores across query tokens for each key token in the sequence.",
    "GraphRAG extracts entities and builds community summaries hierarchically before retrieval.",
    "BM25 remains hard to beat for keyword-heavy queries despite being a 1994-vintage algorithm.",
    "The 401(k) match is 100% up to 4% of eligible compensation with 3-year graded vesting.",
    "ColBERT employs late interaction with a multi-vector representation per document.",
    "Embedding drift can silently degrade retrieval as the same text produces different vectors over time.",
    "Self-RAG uses reflection tokens like Retrieve and IsRel to gate generation behavior.",
    "Faithfulness in Ragas is a two-step pipeline: claim decomposition then NLI verification.",
    "MMR balances relevance and diversity; lambda controls the tradeoff explicitly.",
    "Anthropic Citations API enforces parser-validated pointers so cited spans must exist.",
    "Long-context degradation is non-linear past 32K tokens even on frontier models.",
    "Chroma research dubbed this 'Context Rot' and observed it across all major LLM families.",
    "Hybrid search combines BM25 with dense embeddings, fused typically via RRF.",
    "Patronus Lynx is an open-weight Llama-3 fine-tune for hallucination detection.",
] * 8  # ~160 paragraphs total

NEEDLE = "The secret code for accessing the executive lounge is XKZ-742."


def context_with_needle_at(position_pct: float) -> str:
    """Insert needle at given fractional position (0.0=start, 1.0=end) in the distractor pile."""
    paragraphs = list(DISTRACTOR_PARAGRAPHS)
    insert_idx = int(position_pct * len(paragraphs))
    paragraphs.insert(insert_idx, NEEDLE)
    return "\n\n".join(paragraphs)


PROMPT_TEMPLATE = """The following is a collection of internal company notes. Answer the user's question
using only the information in the notes.

NOTES:
{context}

QUESTION: What is the secret code for accessing the executive lounge?

Answer:"""


def ask_claude(context: str) -> str:
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=100,
        temperature=0.0,
        messages=[{"role": "user", "content": PROMPT_TEMPLATE.format(context=context)}],
    )
    return msg.content[0].text.strip()


# %%
print("\n=== Lost-in-the-Middle test ===")
print(f"Distractor pile: {len(DISTRACTOR_PARAGRAPHS)} paragraphs ≈ ~{len(' '.join(DISTRACTOR_PARAGRAPHS))//4:,} tokens")
print(f"Needle (placed at varying positions): \"{NEEDLE}\"")

import re

results = []
for pct, label in [(0.02, "near start"), (0.5, "middle"), (0.98, "near end")]:
    context = context_with_needle_at(pct)
    answer = ask_claude(context)
    found = "XKZ-742" in answer
    print(f"\nPosition: {label} ({int(pct*100)}%)")
    print(f"  Answer: {answer[:120]}")
    print(f"  Found XKZ-742: {found}")
    results.append((pct, label, found, answer))

# %% [markdown]
# **What this typically shows:** modern frontier models (Sonnet 4.5, GPT-4o, Gemini) have
# improved on Lost-in-the-Middle and often find the needle anywhere — at this length and difficulty.
# To reliably reproduce the U-curve, push context length way up (10x more distractors) AND make
# the question more semantically distant from the needle (this is what NoLiMa does).
#
# **The lesson stands regardless:** the further the relevant info sits from start/end,
# the lower the model's *internal attention weight* on it, even when the final answer comes out right.
# In production with subtler queries, you DO see the degradation.

# %% [markdown]
# ## Part 3 — The U-aware reordering trick
#
# Given a list of chunks ranked by reranker score, **place the top-1 at position 1 and top-2
# at the LAST position** (not at position 2). Top-3 at position 2, top-4 at penultimate, etc.
# This exploits the U-curve instead of fighting it.

# %%
def u_aware_reorder(ranked_chunks: List[str]) -> List[str]:
    """Place top results at the start AND end of the list, alternating.
    The middle gets the lowest-ranked content (which the model attends to least anyway)."""
    front, back = [], []
    for i, chunk in enumerate(ranked_chunks):
        if i % 2 == 0:
            front.append(chunk)
        else:
            back.insert(0, chunk)
    return front + back


# Demo with 6 mock-ranked chunks
ranked = [f"[Rank {i+1}] Chunk content for rank {i+1}" for i in range(6)]
reordered = u_aware_reorder(ranked)

print("\n=== U-aware reordering demo ===")
print("Naive order (high to low):")
for i, c in enumerate(ranked):
    print(f"  Position {i+1}: {c}")

print("\nU-aware order (top results at extremes):")
for i, c in enumerate(reordered):
    print(f"  Position {i+1}: {c}")

print("\nObserve: rank-1 at position 1, rank-2 at LAST position (where attention is also high).")
print("Rank-3 at position 2, rank-4 at second-to-last. Worst content lands in the middle (where attention is lowest).")

# %% [markdown]
# ## Things to try next
#
# 1. **Push context length to 30K+ tokens** — make the distractor pile much bigger. The U-curve
#    becomes measurable.
# 2. **Run NoLiMa-style probes** — phrase the question to share NO words with the needle (force
#    semantic, not literal, retrieval). Modern LLMs degrade much more on that.
# 3. **Wire u_aware_reorder into Notebook 06** — apply it AFTER reranking, before sending to
#    the LLM. Compare answer quality with vs without.
# 4. **Per-language quality** — repeat the cross-lingual search with non-English queries and
#    measure recall@k separately per language. Watch the English bias appear.
# 5. **Mixed-script retrieval** — try queries with code-switching ("how is the 401k policy
#    in नई कंपनी") and watch BGE-M3 handle it gracefully.
#
# ## What this demonstrated
# - **BGE-M3** handles cross-lingual retrieval natively — no translation pipeline needed.
# - **Lost-in-the-Middle** is real but newer frontier models are more robust to it on simple probes.
# - **U-aware reordering** is a free quality win — exploit the U-curve, don't fight it.
