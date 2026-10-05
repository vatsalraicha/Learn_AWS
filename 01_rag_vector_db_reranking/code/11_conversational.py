# %% [markdown]
# # Notebook 11 — Conversational Query Rewriting
#
# **Pairs with:** [Module 11 — Personalization & Conversational](../11_personalization_conversational.md)
#
# **What you'll see:**
# 1. The **multi-turn coreference problem** — naive retrieval fails on follow-up questions.
# 2. A **fast LLM rewriter** that turns the latest message + history into a standalone query.
# 3. Side-by-side: retrieval recall WITHOUT vs WITH the rewriter.
# 4. **Multi-strategy rewriting** — generate 3 complementary rewrites, fuse via RRF.
#
# **Stack:** anthropic (Haiku for fast rewrites), voyageai, lancedb. **No OpenAI.**

# %% [markdown]
# ## Setup

# %%
import os
import re
from pathlib import Path
from typing import List, Tuple, Dict
from collections import defaultdict
import numpy as np
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")

import sys
sys.path.insert(0, str(Path(__file__).parent / "data"))
from seed_corpus import get_corpus  # noqa: E402

corpus = get_corpus()
chunk_ids = [c[0] for c in corpus]
chunk_texts = [c[1] for c in corpus]
text_by_id = {c[0]: c[1] for c in corpus}

# %%
import voyageai
import lancedb

vo = voyageai.Client(api_key=os.environ["VOYAGE_API_KEY"])

def embed(texts: List[str], input_type: str) -> List[List[float]]:
    return vo.embed(texts, model="voyage-3-large", input_type=input_type).embeddings

db = lancedb.connect("./lancedb_storage")
if "rag_chunks" not in db.table_names():
    embs = embed(chunk_texts, input_type="document")
    db.create_table("rag_chunks", data=[
        {"chunk_id": cid, "text": t, "vector": v}
        for cid, t, v in zip(chunk_ids, chunk_texts, embs)
    ])
table = db.open_table("rag_chunks")

def dense_retrieve(query: str, top_k: int = 3) -> List[str]:
    qv = embed([query], "query")[0]
    return [r["chunk_id"] for r in table.search(qv).limit(top_k).to_list()]

# %% [markdown]
# ## A multi-turn conversation that exposes the problem

# %%
conversation = [
    {"role": "user", "content": "Tell me about the 401k plan."},
    {"role": "assistant", "content": "Acme matches 100% up to 4% with 3-year graded vesting."},
    {"role": "user", "content": "How does that compare to the parental leave benefit?"},  # 'that' is ambiguous
]

latest_message = conversation[-1]["content"]

# %% [markdown]
# ## Without rewriting — naive retrieval on the literal latest message

# %%
print(f"\nLATEST MESSAGE (literal): {latest_message}\n")
naive_hits = dense_retrieve(latest_message, top_k=3)
print("Naive retrieval results:")
for cid in naive_hits:
    print(f"  {cid}: {text_by_id[cid][:80]}...")

# %% [markdown]
# Notice the problem: the retriever doesn't know "that" refers to the 401k plan.
# Likely it returns parental leave docs (which the user did mention) but misses the 401k
# context the user is implicitly comparing against.

# %% [markdown]
# ## With rewriter — turn the dialogue into a standalone query

# %%
from anthropic import Anthropic

client = Anthropic()

REWRITE_PROMPT = """Given this conversation, rewrite the latest user message as a single
self-contained question that can be understood without the prior turns. Resolve all
pronouns ("that", "it", "they") and carry forward implied subjects. If the latest message
is unrelated to prior turns, return it unchanged.

Output only the rewritten question, no preamble.

Conversation:
{conv}

Latest message: {latest}

Rewritten question:"""


def format_conversation(conv: List[Dict]) -> str:
    return "\n".join(f"{t['role']}: {t['content']}" for t in conv[:-1])


def rewrite_query(conversation: List[Dict]) -> str:
    msg = client.messages.create(
        model="claude-haiku-4-5",  # fast & cheap; ideal for rewriting
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": REWRITE_PROMPT.format(
                conv=format_conversation(conversation),
                latest=conversation[-1]["content"],
            ),
        }],
    )
    return msg.content[0].text.strip()


standalone = rewrite_query(conversation)
print(f"\nREWRITTEN: {standalone}\n")

rewritten_hits = dense_retrieve(standalone, top_k=3)
print("Retrieval after rewriting:")
for cid in rewritten_hits:
    print(f"  {cid}: {text_by_id[cid][:80]}...")

# %% [markdown]
# Now the retriever sees both topics ("401k plan" AND "parental leave") and can pull
# both relevant policies. Without rewriting, it would only chase one of them.

# %% [markdown]
# ## Multi-strategy rewriting (frontier 2026 pattern)
#
# Generate 3 complementary rewrites, retrieve for each, fuse with RRF. Each rewrite
# targets a different failure mode.

# %%
MULTI_STRATEGY_PROMPT = """Given this conversation, produce 3 complementary rewrites of
the latest user message, each targeting a different retrieval failure mode:

1. **Minimal**: a coreference-resolved standalone question (just fix pronouns).
2. **Decomposed**: split into the underlying sub-questions (one per topic).
3. **HyDE-style**: a one-paragraph hypothetical answer that captures what a relevant
   document would say.

Output JSON: {{"minimal": "...", "decomposed": ["...", "..."], "hyde": "..."}}

Conversation:
{conv}

Latest message: {latest}

JSON only:"""

import json

def multi_strategy_rewrite(conversation: List[Dict]) -> Dict:
    msg = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": MULTI_STRATEGY_PROMPT.format(
                conv=format_conversation(conversation),
                latest=conversation[-1]["content"],
            ),
        }],
    )
    text = msg.content[0].text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    return json.loads(text)


rewrites = multi_strategy_rewrite(conversation)
print("\n=== Multi-strategy rewrites ===")
print(f"Minimal   : {rewrites['minimal']}")
print(f"Decomposed: {rewrites['decomposed']}")
print(f"HyDE      : {rewrites['hyde'][:120]}...")

# %% [markdown]
# ## RRF-fuse retrieval across all rewrites

# %%
def rrf_fuse(rankings: List[List[str]], k: int = 60) -> List[Tuple[str, float]]:
    fused: Dict[str, float] = defaultdict(float)
    for ranking in rankings:
        for r, cid in enumerate(ranking):
            fused[cid] += 1.0 / (k + r + 1)
    return sorted(fused.items(), key=lambda x: -x[1])


# Build the list of queries to retrieve for
queries = [rewrites["minimal"], rewrites["hyde"]] + rewrites["decomposed"]
all_rankings = [dense_retrieve(q, top_k=5) for q in queries]
fused = rrf_fuse(all_rankings)

print("\n=== Multi-strategy + RRF top-5 ===")
for cid, score in fused[:5]:
    print(f"  {cid}  rrf={score:.4f}  {text_by_id[cid][:80]}...")

# %% [markdown]
# Notice this typically retrieves **more diverse** chunks across the 401k AND parental leave
# AND any other implied topics — exactly what the user's comparison question needs.

# %% [markdown]
# ## Things to try next
#
# 1. **Topic-shift detection** — add a check that returns the original message unchanged
#    when the topic clearly shifts. Critical for long conversations that go many directions.
# 2. **Use the bot's last answer in the rewriter context** — for queries like "tell me more
#    about that policy" the antecedent is in the bot's last reply, not the user's prior turn.
# 3. **Conversation summarization** — for 20+ turn conversations, summarize older turns into
#    a single block + keep last 3-4 verbatim. Cuts cost without losing rewriter quality.
# 4. **Latency profiling** — time the rewriter step. Haiku 4.5 should be ~150-300ms; if
#    higher, you've blown your latency budget.
# 5. **A/B against no-rewriter on a real eval set** — measure recall@5 lift; expect
#    ~30-40 point improvement on later-turn queries (per MTRAG benchmark).
#
# ## What this demonstrated
# - Naive retrieval on the literal latest message **breaks on follow-up turns** — it has
#   no idea what "that" refers to.
# - A **fast rewriter** in front of retrieval is the standard fix; the cost is ~200ms latency.
# - **Multi-strategy rewriting** with RRF fusion handles complex compare-and-contrast
#   queries that single rewrites can't.
