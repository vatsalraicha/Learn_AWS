# %% [markdown]
# # Notebook 04 — Chunking Strategies Compared
#
# **Pairs with:** [Module 4 — Chunking & Indexing](../04_chunking_indexing.md)
#
# **What you'll see, on the same source document:**
# 1. **Fixed-size chunking** (the dumb baseline).
# 2. **Recursive character splitting** (LangChain's de-facto default).
# 3. **Semantic chunking** (split where embedding distance jumps).
# 4. **Anthropic Contextual Retrieval** (LLM prepends a chunk-specific context summary before embedding).
# 5. Retrieval recall with each strategy on the same query — concrete numbers.
#
# **Stack:** anthropic, voyageai, langchain text splitters. **No OpenAI.**

# %% [markdown]
# ## Setup — a longer document to actually chunk

# %%
import os
import re
from pathlib import Path
from typing import List, Tuple
import numpy as np
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")

# A multi-section document where context across sections matters
DOCUMENT = """\
# Acme Corp Employee Handbook 2024

## 1. Company Overview
Acme Corp was founded in 2009 and operates in 18 countries. Our mission is to make
enterprise software people actually want to use.

## 2. Compensation Philosophy
Acme bases compensation on four factors: role, level, location, and performance.
We benchmark against industry data quarterly. The combined target compensation includes
base salary, annual bonus, and equity.

### 2.1 401(k) Retirement Plan
The company matches 100% of employee contributions up to 4% of eligible compensation.
Vesting is graded over 3 years: 33% after year 1, 66% after year 2, 100% after year 3.
Match contributions are made each pay period. Employees are auto-enrolled at 3%; you
can change this at any time via the benefits portal.

### 2.2 Equity
New hires receive an equity grant that vests over 4 years with a 1-year cliff.
Refresh grants are reviewed annually as part of the performance cycle.

## 3. Time Off
Acme provides unlimited PTO. The expectation is that employees take at least 15 days
per year. Holidays are observed per the country-specific calendar.

### 3.1 Parental Leave
Birth parents receive 16 weeks of paid leave. Non-birth parents and adoptive parents
receive 8 weeks. Leave must be taken within 12 months of the qualifying event.

### 3.2 Medical Leave
Up to 12 weeks of paid medical leave is available, subject to employer-provided
disability insurance terms. Coordinate with HR before scheduling.

## 4. Refund and Customer Policies (External)
This section is for customer-facing reference only.

### 4.1 B2B Refund Policy (Q4 2024)
B2B customers may request a refund within 30 days of purchase. Refunds for annual
contracts are pro-rated. Promotional discount codes are non-refundable except where
required by law. This supersedes the Q1 2023 policy.

### 4.2 Trial Conversions
Free trial users who convert to paid in the first 7 days receive a 10% lifetime
discount. This stacks with annual prepayment discounts.

## 5. Code of Conduct
Treat colleagues, customers, and partners with respect. Report concerns to People Ops
or via the anonymous ethics line. Retaliation is prohibited.
"""

print(f"Document length: {len(DOCUMENT)} chars / ~{len(DOCUMENT)//4} tokens (rough)")

# %% [markdown]
# ## Strategy 1 — Fixed-size chunking
#
# 500-char chunks, 50-char overlap. The dumb baseline.

# %%
def fixed_size_chunks(text: str, size: int = 500, overlap: int = 50) -> List[str]:
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + size])
        start += size - overlap
    return chunks

fixed_chunks = fixed_size_chunks(DOCUMENT)
print(f"\nFixed-size: {len(fixed_chunks)} chunks")
print("First chunk preview:")
print(fixed_chunks[0][:200], "...")

# %% [markdown]
# ## Strategy 2 — Recursive character splitting (LangChain default)

# %%
from langchain_text_splitters import RecursiveCharacterTextSplitter

recursive_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " ", ""],
)
recursive_chunks = recursive_splitter.split_text(DOCUMENT)
print(f"\nRecursive: {len(recursive_chunks)} chunks")
print("Chunks aligned to section boundaries:")
for i, c in enumerate(recursive_chunks):
    first_line = c.strip().split("\n")[0]
    print(f"  [{i}] {first_line[:80]}")

# %% [markdown]
# ## Strategy 3 — Semantic chunking (split at embedding-distance jumps)

# %%
import voyageai

vo = voyageai.Client(api_key=os.environ["VOYAGE_API_KEY"])

def split_into_sentences(text: str) -> List[str]:
    # Naive but works — for production use a real sentencizer (spaCy, nltk).
    sents = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sents if s.strip()]

def cosine(a, b):
    a, b = np.array(a), np.array(b)
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))

def semantic_chunks(text: str, percentile: float = 95, min_chunk_len: int = 200) -> List[str]:
    """Split at sentence boundaries where adjacent embeddings differ above the percentile threshold."""
    sentences = split_into_sentences(text)
    if len(sentences) < 2:
        return [text]
    embs = vo.embed(sentences, model="voyage-3-large", input_type="document").embeddings
    distances = [1 - cosine(embs[i], embs[i + 1]) for i in range(len(sentences) - 1)]
    threshold = np.percentile(distances, percentile)
    breakpoints = [i + 1 for i, d in enumerate(distances) if d > threshold]
    chunks, start = [], 0
    for bp in breakpoints:
        chunk = " ".join(sentences[start:bp]).strip()
        if len(chunk) >= min_chunk_len:
            chunks.append(chunk)
            start = bp
    last = " ".join(sentences[start:]).strip()
    if last:
        chunks.append(last)
    return chunks

print("\nSemantic chunking (Voyage embeddings)...")
sem_chunks = semantic_chunks(DOCUMENT)
print(f"Semantic: {len(sem_chunks)} chunks")
for i, c in enumerate(sem_chunks):
    print(f"  [{i}] {c[:80]}...")

# %% [markdown]
# ## Strategy 4 — Anthropic Contextual Retrieval
#
# Each chunk gets a 50-100 token LLM-generated context prefix that situates it within
# the document. Then we embed the contextualized chunk.
#
# Implementation note: in production you'd use **prompt caching** to cache the document
# while varying the chunk — turns this from expensive to nearly free. We skip caching here
# for simplicity but note where it would go.

# %%
from anthropic import Anthropic

client = Anthropic()

CONTEXT_PROMPT = """<document>
{doc}
</document>

Here is a chunk we want to situate within the whole document:
<chunk>
{chunk}
</chunk>

Please give a short (50-100 token) context that situates this chunk within the overall
document for the purposes of improving search retrieval. Answer only with the succinct
context and nothing else."""

def contextualize_chunks(doc: str, chunks: List[str]) -> List[str]:
    """Prepend an LLM-generated context to each chunk. Production: use prompt caching."""
    contextualized = []
    for chunk in chunks:
        msg = client.messages.create(
            model="claude-haiku-4-5",   # cheap; quality differential is small
            max_tokens=200,
            messages=[{
                "role": "user",
                "content": CONTEXT_PROMPT.format(doc=doc, chunk=chunk),
            }],
            # In production:
            # system=[{"type": "text", "text": "...", "cache_control": {"type": "ephemeral"}}]
        )
        context = msg.content[0].text.strip()
        contextualized.append(f"{context}\n\n{chunk}")
    return contextualized

print("\nContextualizing recursive chunks (Claude Haiku 4.5)...")
ctx_chunks = contextualize_chunks(DOCUMENT, recursive_chunks)
print(f"Contextualized: {len(ctx_chunks)} chunks (one prefix per chunk)")
print("\nExample chunk vs contextualized chunk:")
print("RAW    :", recursive_chunks[3][:120], "...")
print("CONTEXT:", ctx_chunks[3][:200], "...")

# %% [markdown]
# ## Compare retrieval recall on a tricky query
#
# Query: "How long until I'm fully vested in retirement contributions?"
#
# This query phrases things differently from the doc ("invested" → "vested" / "401k") AND
# requires the right *section* to be retrieved. Watch how each strategy fares.

# %%
def embed_chunks(chunks: List[str]) -> np.ndarray:
    embs = vo.embed(chunks, model="voyage-3-large", input_type="document").embeddings
    return np.array(embs)

def embed_query(q: str) -> np.ndarray:
    return np.array(vo.embed([q], model="voyage-3-large", input_type="query").embeddings[0])

def top_k(query_vec: np.ndarray, chunk_vecs: np.ndarray, k: int = 1) -> List[int]:
    # Normalize for cosine
    chunk_vecs_n = chunk_vecs / np.linalg.norm(chunk_vecs, axis=1, keepdims=True)
    q_n = query_vec / np.linalg.norm(query_vec)
    scores = chunk_vecs_n @ q_n
    return list(np.argsort(scores)[::-1][:k])


tricky_query = "How long until I'm fully vested in retirement contributions?"
qv = embed_query(tricky_query)

strategies = {
    "Fixed-size":            fixed_chunks,
    "Recursive":             recursive_chunks,
    "Semantic":              sem_chunks,
    "Contextual Retrieval":  ctx_chunks,
}

print(f"\nQUERY: {tricky_query}\n")
for name, chunks in strategies.items():
    vecs = embed_chunks(chunks)
    top_idx = top_k(qv, vecs, k=1)[0]
    snippet = chunks[top_idx][:120].replace("\n", " ")
    contains_answer = ("3 years" in chunks[top_idx]) or ("vesting" in chunks[top_idx].lower())
    flag = "✓" if contains_answer else "✗"
    print(f"  {name:25s} top-1 idx={top_idx} {flag} → {snippet}...")

# %% [markdown]
# ## Things to try next
#
# 1. **Tune semantic chunking percentile** — try 80, 90, 95, 99. Lower = more chunks, smaller; higher = fewer, larger.
# 2. **Add prompt caching** to the contextualize_chunks function — cache the document on the first call. Production version is ~10× cheaper.
# 3. **BM25 + Contextual** — Module 4 notes Anthropic also indexes the contextualized chunk into BM25. Combine with the hybrid retriever from Notebook 05.
# 4. **Late chunking** — load `jina-embeddings-v3` and try late chunking (embed full doc → mean-pool over span boundaries). Compare to Contextual Retrieval on cross-section queries.
# 5. **Multiple queries** — run 5-10 queries against each strategy. Watch which strategy wins on which query type.
#
# ## What this demonstrated
# - Fixed-size chunking is structurally bad — section boundaries get cut mid-content.
# - Recursive splitter respects structure for free.
# - Semantic chunking is more expensive (one embedding per sentence) but adapts to the doc.
# - **Contextual Retrieval** is the production winner when the LLM-call cost is amortizable
#   (prompt caching makes this real). Per Anthropic's published numbers: 35% retrieval-failure
#   reduction; 49% with BM25; 67% with reranker.
