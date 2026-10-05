# %% [markdown]
# # Notebook 10 — Function-Call Routing (RAG vs grep vs SQL vs read_file)
#
# **Pairs with:** [Module 10 — Code, Metadata & Routing](../10_code_metadata_routing.md)
#
# **What you'll see:**
# 1. The mistake of routing every query to vector search.
# 2. A **function-calling LLM** that picks among `read_file`, `grep_code`, `vector_search`,
#    and `run_sql` per query.
# 3. Side-by-side: vector-search-only vs router on a mixed query batch.
#
# **Stack:** anthropic tool use, lancedb, sqlite, regex grep. **No OpenAI.**

# %% [markdown]
# ## Setup — a tiny fake "workspace" with three data sources

# %%
import os
import re
import sqlite3
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")

WORKSPACE = Path("./fake_workspace")
WORKSPACE.mkdir(exist_ok=True)

# 1) Some files for read_file / grep
(WORKSPACE / "CLAUDE.md").write_text(
    "# CLAUDE.md\n\nThis file describes how to use Claude in our project.\n\n"
    "## Setup\nInstall the SDK: `pip install anthropic`\n\n"
    "## Notes\nUse Sonnet 4.5 for production work.\n"
)
(WORKSPACE / "auth.py").write_text(
    "from typing import Optional\n\n"
    "def getUserSession(user_id: str) -> Optional[dict]:\n"
    "    \"\"\"Fetch session by user id from the cache.\"\"\"\n"
    "    return cache.get(f'session:{user_id}')\n\n"
    "def invalidateSession(session_id: str) -> bool:\n"
    "    return cache.delete(f'session:{session_id}')\n"
)
(WORKSPACE / "billing.py").write_text(
    "def calculateRefund(amount: float, days_since: int) -> float:\n"
    "    if days_since > 30:\n"
    "        return 0.0\n"
    "    return amount * (1 - days_since / 30)\n"
)

# 2) A SQLite DB for run_sql
DB_PATH = WORKSPACE / "orders.db"
if DB_PATH.exists():
    DB_PATH.unlink()
conn = sqlite3.connect(DB_PATH)
conn.executescript("""
CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT, state TEXT);
CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER, amount REAL, date TEXT);
INSERT INTO customers VALUES (1, 'Acme Inc', 'TX'), (2, 'Beta LLC', 'CA'), (3, 'Gamma Corp', 'TX');
INSERT INTO orders VALUES (1, 1, 1500.00, '2024-11-15'), (2, 1, 800.00, '2024-12-02'),
                         (3, 2, 2500.00, '2024-10-20'), (4, 3, 12000.00, '2024-11-30');
""")
conn.commit()

# 3) The seed corpus from earlier notebooks (for vector_search on prose)
import sys
sys.path.insert(0, str(Path(__file__).parent / "data"))
from seed_corpus import get_corpus  # noqa: E402

corpus = get_corpus()
chunk_ids = [c[0] for c in corpus]
chunk_texts = [c[1] for c in corpus]
text_by_id = {c[0]: c[1] for c in corpus}

import voyageai, lancedb
vo = voyageai.Client(api_key=os.environ["VOYAGE_API_KEY"])
db = lancedb.connect("./lancedb_storage")
if "rag_chunks" not in db.table_names():
    embs = vo.embed(chunk_texts, model="voyage-3-large", input_type="document").embeddings
    db.create_table("rag_chunks", data=[
        {"chunk_id": cid, "text": t, "vector": v}
        for cid, t, v in zip(chunk_ids, chunk_texts, embs)
    ])
table = db.open_table("rag_chunks")

# %% [markdown]
# ## Define the four tools the agent can call

# %%
TOOLS = [
    {
        "name": "read_file",
        "description": "Fetch the contents of a specific file by exact name or path. "
                       "Use when the user names a file directly (e.g. 'show me CLAUDE.md').",
        "input_schema": {
            "type": "object",
            "properties": {"name": {"type": "string", "description": "File name or path"}},
            "required": ["name"],
        },
    },
    {
        "name": "grep_code",
        "description": "Search source code for an exact pattern. Use when the user asks about "
                       "a specific symbol, function name, identifier, or literal string in code.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Regex pattern to search for"},
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "vector_search",
        "description": "Semantic search over the documentation knowledge base. Use for "
                       "concept questions, paraphrased queries, or 'where is X explained?' "
                       "type questions where exact tokens won't match.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}, "top_k": {"type": "integer", "default": 3}},
            "required": ["query"],
        },
    },
    {
        "name": "run_sql",
        "description": "Execute a SQL query against the orders database. Tables: "
                       "customers(id, name, state), orders(id, customer_id, amount, date). "
                       "Use for aggregations, filtering on structured fields, joins.",
        "input_schema": {
            "type": "object",
            "properties": {"sql": {"type": "string", "description": "SQL query"}},
            "required": ["sql"],
        },
    },
]


def tool_read_file(name: str) -> str:
    p = WORKSPACE / name
    if not p.exists():
        return f"ERROR: {name} not found"
    return p.read_text()

def tool_grep_code(pattern: str) -> str:
    matches = []
    for f in WORKSPACE.glob("*.py"):
        for i, line in enumerate(f.read_text().splitlines(), 1):
            if re.search(pattern, line):
                matches.append(f"{f.name}:{i}: {line}")
    return "\n".join(matches) if matches else f"No matches for /{pattern}/"

def tool_vector_search(query: str, top_k: int = 3) -> str:
    qv = vo.embed([query], model="voyage-3-large", input_type="query").embeddings[0]
    results = table.search(qv).limit(top_k).to_list()
    return "\n---\n".join(f"[{r['chunk_id']}] {r['text']}" for r in results)

def tool_run_sql(sql: str) -> str:
    try:
        rows = conn.execute(sql).fetchall()
        return "\n".join(str(row) for row in rows) or "(no rows)"
    except Exception as e:
        return f"SQL ERROR: {e}"

TOOL_FUNCS = {
    "read_file": tool_read_file,
    "grep_code": tool_grep_code,
    "vector_search": tool_vector_search,
    "run_sql": tool_run_sql,
}

# %% [markdown]
# ## The router agent — let Claude pick the tool

# %%
from anthropic import Anthropic
client = Anthropic()

def route_and_answer(query: str) -> Dict[str, Any]:
    """Single-turn router: send the query + tools to Claude, execute the tool it chose,
    pass the result back, get the final answer."""
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=500,
        tools=TOOLS,
        messages=[{"role": "user", "content": query}],
    )
    # If Claude chose a tool, execute it
    if msg.stop_reason == "tool_use":
        tool_use_block = next(b for b in msg.content if b.type == "tool_use")
        tool_name = tool_use_block.name
        tool_input = tool_use_block.input
        tool_result = TOOL_FUNCS[tool_name](**tool_input)

        # Pass result back for the final answer
        followup = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=500,
            tools=TOOLS,
            messages=[
                {"role": "user", "content": query},
                {"role": "assistant", "content": msg.content},
                {
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": tool_use_block.id,
                        "content": tool_result,
                    }],
                },
            ],
        )
        final_text = next(b.text for b in followup.content if b.type == "text")
        return {
            "tool_chosen": tool_name,
            "tool_input": tool_input,
            "tool_result_preview": tool_result[:200],
            "answer": final_text,
        }
    else:
        # No tool — direct answer
        text = next((b.text for b in msg.content if b.type == "text"), "")
        return {"tool_chosen": None, "answer": text}


# %% [markdown]
# ## Run the router on a mix of query types

# %%
queries = [
    "Give me the contents of CLAUDE.md.",                       # → read_file
    "Find all uses of getUserSession in the codebase.",         # → grep_code
    "Why is Reciprocal Rank Fusion useful in hybrid retrieval?",# → vector_search
    "How much did Texas customers spend in 2024 in total?",     # → run_sql
    "Show me the calculateRefund function.",                    # → grep_code or read_file
]

for q in queries:
    print(f"\n{'='*80}")
    print(f"QUERY: {q}")
    result = route_and_answer(q)
    print(f"Tool chosen: {result['tool_chosen']}")
    if result.get("tool_input"):
        print(f"Tool input : {result['tool_input']}")
    print(f"Answer:\n{result['answer']}")

# %% [markdown]
# ## Compare: vector-search-only on the same queries
#
# This is the "every query is a vector query" anti-pattern. Watch what fails.

# %%
print(f"\n\n{'='*80}\nVECTOR-SEARCH-ONLY (anti-pattern)\n{'='*80}")
for q in queries:
    print(f"\nQ: {q}")
    res = tool_vector_search(q, top_k=2)
    print(f"  → {res[:200]}...")

# %% [markdown]
# Notice the failure modes:
# - "Give me CLAUDE.md" → vector search returns whatever chunk is closest to that phrasing,
#   never the actual file.
# - "Find getUserSession usages" → vector search retrieves vague "function" mentions, not
#   the literal occurrences.
# - "Texas customer total" → vector search returns nothing relevant; SQL would compute it instantly.
#
# The routing pattern fixes all three.

# %% [markdown]
# ## Things to try next
#
# 1. **Multi-step routing** — wrap this in a loop so the agent can call multiple tools per
#    query (e.g., "find getUserSession usages and explain how to invalidate them" needs
#    grep + read_file + vector_search).
# 2. **Add a `web_search` tool** for queries about external/breaking content.
# 3. **Track which tool gets picked** over a real query log. The distribution tells you
#    whether vector search is over- or under-used in your product.
# 4. **Failure mode**: send a query the LLM should refuse instead of routing (e.g., "delete
#    all files"). Add an `abstain` tool or a safety check before tool execution.
# 5. **Combine with Notebook 14's abstention policy** — if vector_search returns weak
#    results AND the tool is correct, abstain rather than hallucinate.
#
# ## What this demonstrated
# - Production "AI assistants" don't run vector search on every query — they **route**.
# - **Function-calling LLMs** are the right router; they understand intent better than
#   classifier-based routing for new query patterns.
# - Vector search is **one tool**, not the answer. The answer is in routing.
