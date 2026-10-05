# %% [markdown]
# # Notebook 22 — GraphRAG: end-to-end on a tiny corpus
#
# **Pairs with:** [Module 22 — GraphRAG Deep Dive](../22_graphrag_deep_dive.md)
#
# **What you'll see:**
# 1. Build a knowledge graph from a small healthcare-themed corpus via LLM-driven entity-relationship
#    extraction (the Microsoft GraphRAG / LightRAG style).
# 2. Run **community detection** with Leiden over the resulting graph.
# 3. Implement **three retrieval modes** end-to-end:
#    - **Vector** baseline (Module 5 hybrid retriever, repeated for comparison).
#    - **Local graph search** — entity-anchored, walk neighbors.
#    - **Global graph search** — map-reduce over community summaries.
# 4. Implement a **routing classifier** that picks which retriever to use per query.
# 5. Implement **HippoRAG-style Personalized PageRank** retrieval as an alternative.
# 6. Compare results on the same queries — see where each retriever wins.
#
# **Stack:** anthropic (Claude as extractor + judge + answerer), networkx, voyageai (embeddings),
# `python-louvain` and `cdlib` for community detection. **No OpenAI.**
#
# **No Neo4j required.** We build the graph in-memory with NetworkX so you can run this
# notebook without provisioning a graph database. The principles transfer 1:1 to Neo4j.

# %% [markdown]
# ## Setup

# %%
import os
import json
import re
import textwrap
from pathlib import Path
from typing import List, Dict, Tuple, Set, Optional
from collections import defaultdict, Counter

import numpy as np
import networkx as nx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")

assert os.environ.get("ANTHROPIC_API_KEY"), "ANTHROPIC_API_KEY required"

from anthropic import Anthropic
import voyageai

client = Anthropic()
vo = voyageai.Client(api_key=os.environ["VOYAGE_API_KEY"])

EXTRACT_MODEL = "claude-haiku-4-5"        # cheap extractor (per Module 22 cost guidance)
ANSWER_MODEL  = "claude-sonnet-4-5"        # quality-first generator

# %% [markdown]
# ## A small healthcare-themed corpus
#
# 8 short documents about Acme Health Network. Mix of policies, clinical guidance, and
# operational notes — enough variety to produce a non-trivial graph.

# %%
CORPUS = [
    {
        "id": "doc_001",
        "title": "Refund Policy Q4 2024",
        "text": (
            "Acme Health Network updated its B2B refund policy in Q4 2024. "
            "Refunds may be requested within 30 days of purchase. Prior to this, "
            "the Q1 2023 policy required claims within 14 days. The Q4 2024 policy "
            "was authored by Compliance Director Dr. Maria Chen and approved by CFO James Park."
        ),
    },
    {
        "id": "doc_002",
        "title": "401k Plan 2024",
        "text": (
            "Acme matches 100% of employee 401k contributions up to 4% of salary. "
            "Vesting is graded over three years: 33% after year 1, 66% after year 2, "
            "100% after year 3. The plan is administered by Fidelity. HR Director "
            "Lisa Wong is the plan's primary contact for employee questions."
        ),
    },
    {
        "id": "doc_003",
        "title": "Parental Leave Policy",
        "text": (
            "Birth parents at Acme Health Network receive 16 weeks of paid parental leave. "
            "Non-birth parents and adoptive parents receive 8 weeks. The policy is administered "
            "by HR Director Lisa Wong. It was last updated in March 2024 to align with state law."
        ),
    },
    {
        "id": "doc_004",
        "title": "Hepatocellular Carcinoma Treatment Guideline",
        "text": (
            "For stage 3 hepatocellular carcinoma (HCC) in patients with concurrent portal "
            "hypertension, the recommended first-line treatment is transarterial chemoembolization "
            "(TACE). Sorafenib is contraindicated when portal hypertension is severe. "
            "Recommendations are based on the 2024 AASLD guidelines, reviewed by Hepatology "
            "Department Chair Dr. Robert Singh."
        ),
    },
    {
        "id": "doc_005",
        "title": "Sorafenib Prescribing Information",
        "text": (
            "Sorafenib is an oral kinase inhibitor used in advanced hepatocellular carcinoma. "
            "Contraindications include severe portal hypertension, decompensated cirrhosis, "
            "and known hypersensitivity. The drug interacts with warfarin and CYP3A4 inducers "
            "such as rifampin. Standard dose is 400mg twice daily."
        ),
    },
    {
        "id": "doc_006",
        "title": "Q1 2025 Compliance Training Requirements",
        "text": (
            "All managers at Acme Health Network must complete refund policy compliance "
            "training within 30 days of any role transition. The Q1 2025 update added "
            "cross-border revenue compliance modules. Training is mandated by Compliance "
            "Director Dr. Maria Chen and tracked by HR Director Lisa Wong."
        ),
    },
    {
        "id": "doc_007",
        "title": "Hepatology Department Board Minutes",
        "text": (
            "The hepatology department's October 2024 board meeting, chaired by Dr. Robert Singh, "
            "discussed updates to the HCC treatment protocols. Dr. Singh emphasized that sorafenib "
            "should not be prescribed to patients with severe portal hypertension, citing the "
            "2024 AASLD guidelines. Dr. Maria Chen attended as the compliance representative."
        ),
    },
    {
        "id": "doc_008",
        "title": "Operational Notes Q1 2025",
        "text": (
            "Q1 2025 saw a 12% increase in inquiries about Acme's refund policy. Most inquiries "
            "concerned B2B customers seeking refunds outside the 30-day window. The Compliance "
            "Director's office processed 47 such requests, of which 12 were granted under "
            "extenuating circumstances. CFO James Park reviewed the quarterly compliance report."
        ),
    },
]

print(f"Corpus: {len(CORPUS)} documents.")

# %% [markdown]
# ## Step 1 — LLM-driven entity & relationship extraction
#
# This is the per-chunk LLM call. Microsoft GraphRAG, LightRAG, HippoRAG all share this step
# with minor prompt variations.

# %%
EXTRACTION_PROMPT = """You are an information-extraction system. From the text below, extract:

1. ENTITIES — named persons, organizations, conditions, drugs, policies, dates, roles.
   Format: {{"name": "<canonical name>", "type": "<one of: person|organization|condition|drug|policy|date|role|other>", "description": "<one-sentence description>"}}

2. RELATIONSHIPS between entities mentioned in the text.
   Format: {{"source": "<entity name>", "target": "<entity name>", "relation": "<short verb phrase like 'works for', 'treats', 'supersedes'>", "description": "<one-sentence justification>"}}

Output a JSON object: {{"entities": [...], "relationships": [...]}}.
Output JSON only, no preamble.

TEXT:
\"\"\"
{text}
\"\"\"
"""


def extract_entities_relationships(text: str) -> Dict:
    msg = client.messages.create(
        model=EXTRACT_MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": EXTRACTION_PROMPT.format(text=text)}],
    )
    raw = msg.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"  Parse error: {e}; raw output: {raw[:300]}")
        return {"entities": [], "relationships": []}


# Process every doc
extracted = {}
print("Extracting entities/relationships from each doc...")
for doc in CORPUS:
    print(f"  • {doc['id']} '{doc['title']}'")
    extracted[doc["id"]] = extract_entities_relationships(doc["text"])

# Show what was extracted for one doc
print("\nExample extraction for doc_004 (HCC treatment guideline):")
print(json.dumps(extracted["doc_004"], indent=2)[:600])

# %% [markdown]
# ## Step 2 — Build the knowledge graph
#
# Consolidate per-doc extractions into a single NetworkX graph. Entity names are
# canonicalized (lowercase, stripped); relationships become edges with descriptions.

# %%
def canonical(name: str) -> str:
    return name.strip().lower()


G = nx.MultiDiGraph()

# Add entities (with merged descriptions across docs)
entity_descriptions: Dict[str, List[str]] = defaultdict(list)
entity_types: Dict[str, str] = {}
entity_sources: Dict[str, Set[str]] = defaultdict(set)

for doc_id, ext in extracted.items():
    for e in ext.get("entities", []):
        cname = canonical(e["name"])
        entity_descriptions[cname].append(e["description"])
        entity_types[cname] = e.get("type", "other")
        entity_sources[cname].add(doc_id)

for ent, descs in entity_descriptions.items():
    # Merge multiple descriptions into one
    merged_desc = " | ".join(dict.fromkeys(descs))  # dedup while preserving order
    G.add_node(
        ent,
        type=entity_types[ent],
        description=merged_desc,
        sources=list(entity_sources[ent]),
    )

# Add relationships
for doc_id, ext in extracted.items():
    for r in ext.get("relationships", []):
        s, t = canonical(r["source"]), canonical(r["target"])
        if s in G and t in G:
            G.add_edge(
                s, t,
                relation=r["relation"],
                description=r["description"],
                source_doc=doc_id,
            )

print(f"\nKnowledge graph built: {G.number_of_nodes()} entities, {G.number_of_edges()} relationships")
print(f"\nEntity types: {Counter(entity_types.values())}")

# Quick peek at most-connected entities
deg_centrality = sorted(G.degree(), key=lambda x: -x[1])[:10]
print(f"\nMost-connected entities:")
for ent, deg in deg_centrality:
    print(f"  {ent:50s} (degree {deg}, sources: {entity_sources[ent]})")


# %% [markdown]
# ## Step 3 — Community detection with Leiden
#
# Leiden over the graph produces communities at multiple hierarchical levels.
# Each community gets an LLM-generated "community report" — the summary that drives
# global search.

# %%
try:
    from cdlib import algorithms
    HAVE_LEIDEN = True
except ImportError:
    print("WARN: cdlib not installed. Run `pip install cdlib python-louvain` for Leiden.")
    print("       Falling back to NetworkX's `community.greedy_modularity_communities`.")
    HAVE_LEIDEN = False

# NetworkX needs an undirected graph for community detection
G_undirected = nx.Graph()
for u, v, data in G.edges(data=True):
    G_undirected.add_edge(u, v, weight=1)

if HAVE_LEIDEN:
    coms = algorithms.leiden(G_undirected)
    communities = coms.communities
else:
    communities = list(nx.community.greedy_modularity_communities(G_undirected))

print(f"\nDetected {len(communities)} communities.")
for i, comm in enumerate(communities):
    members_sample = list(comm)[:5]
    print(f"  Community {i}: {len(comm)} nodes — e.g. {members_sample}")


# %% [markdown]
# ## Step 4 — LLM-generated community reports
#
# For each community, prompt the LLM to produce a structured report. These reports become
# the primary retrieval targets for global / aggregative queries.

# %%
COMMUNITY_REPORT_PROMPT = """You are summarizing a community of related entities from a knowledge graph.
Produce a structured report with:

- TITLE: a 5-10 word title for this community
- SUMMARY: a 2-3 sentence summary of what this community is about
- KEY_FINDINGS: a list of 2-4 specific findings about the community

Entities and their descriptions:
{entities}

Relationships within the community:
{relationships}

Output as JSON: {{"title": "...", "summary": "...", "key_findings": ["...", "..."]}}.
Output JSON only.
"""


def summarize_community(community_nodes: Set[str], G: nx.MultiDiGraph) -> Dict:
    ent_block = "\n".join(
        f"- {n} ({G.nodes[n].get('type', 'other')}): {G.nodes[n].get('description', '')[:200]}"
        for n in community_nodes
    )
    rel_block = "\n".join(
        f"- {u} → {v}: {data.get('relation', '')} ({data.get('description', '')[:100]})"
        for u, v, data in G.edges(data=True)
        if u in community_nodes and v in community_nodes
    )
    msg = client.messages.create(
        model=ANSWER_MODEL,
        max_tokens=600,
        messages=[{
            "role": "user",
            "content": COMMUNITY_REPORT_PROMPT.format(
                entities=ent_block[:3000],
                relationships=rel_block[:2000] or "(none within this community)",
            ),
        }],
    )
    raw = msg.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"title": "(parse error)", "summary": raw[:300], "key_findings": []}


print("\nGenerating community reports...")
community_reports = []
for i, comm in enumerate(communities):
    report = summarize_community(comm, G)
    report["community_id"] = i
    report["members"] = list(comm)
    community_reports.append(report)
    print(f"  Community {i}: {report['title']}")
    print(f"    Summary: {report['summary'][:150]}...")


# %% [markdown]
# ## Step 5 — Embed everything for hybrid retrieval

# %%
def embed_texts(texts: List[str], input_type: str) -> List[List[float]]:
    return vo.embed(texts, model="voyage-3-large", input_type=input_type).embeddings


print("\nEmbedding document chunks for vector baseline...")
chunk_embeddings = np.array(embed_texts([d["text"] for d in CORPUS], "document"))

print("Embedding community reports for global graph search...")
report_texts = [f"{r['title']}\n{r['summary']}\nFindings: {'; '.join(r['key_findings'])}" for r in community_reports]
report_embeddings = np.array(embed_texts(report_texts, "document"))

print("Embedding entity descriptions for local graph anchor matching...")
entity_list = list(G.nodes())
entity_text = [f"{n}: {G.nodes[n].get('description', '')}" for n in entity_list]
entity_embeddings = np.array(embed_texts(entity_text, "document"))


def cosine_sim(q: np.ndarray, candidates: np.ndarray) -> np.ndarray:
    q_norm = q / np.linalg.norm(q)
    c_norm = candidates / np.linalg.norm(candidates, axis=1, keepdims=True)
    return c_norm @ q_norm


# %% [markdown]
# ## Step 6 — Three retrievers
#
# ### Vector baseline

# %%
def retrieve_vector(query: str, top_k: int = 3) -> List[Dict]:
    qv = np.array(embed_texts([query], "query")[0])
    scores = cosine_sim(qv, chunk_embeddings)
    top = np.argsort(scores)[::-1][:top_k]
    return [
        {"doc": CORPUS[i], "score": float(scores[i])}
        for i in top
    ]


# %% [markdown]
# ### Local graph search — entity-anchored

# %%
def retrieve_graph_local(query: str, hops: int = 2, top_k_chunks: int = 3) -> Dict:
    """Match query → entities → walk N hops → assemble chunks + relationships."""
    qv = np.array(embed_texts([query], "query")[0])
    ent_scores = cosine_sim(qv, entity_embeddings)
    # Top-3 seed entities
    seeds = [entity_list[i] for i in np.argsort(ent_scores)[::-1][:3]]
    # Walk N hops
    neighborhood = set(seeds)
    frontier = set(seeds)
    for _ in range(hops):
        next_frontier = set()
        for n in frontier:
            for neighbor in G.successors(n):
                next_frontier.add(neighbor)
            for predecessor in G.predecessors(n):
                next_frontier.add(predecessor)
        frontier = next_frontier - neighborhood
        neighborhood |= next_frontier
    # Gather chunks where any entity in neighborhood appeared
    relevant_docs: Set[str] = set()
    for ent in neighborhood:
        relevant_docs |= entity_sources[ent]
    # Score relevant chunks by vector similarity within this filtered set
    relevant_indices = [i for i, d in enumerate(CORPUS) if d["id"] in relevant_docs]
    if not relevant_indices:
        return {"seeds": seeds, "neighborhood": list(neighborhood), "chunks": []}
    chunk_scores = cosine_sim(qv, chunk_embeddings[relevant_indices])
    top_local = np.argsort(chunk_scores)[::-1][:top_k_chunks]
    return {
        "seeds": seeds,
        "neighborhood": list(neighborhood),
        "chunks": [
            {"doc": CORPUS[relevant_indices[i]], "score": float(chunk_scores[i])}
            for i in top_local
        ],
    }


# %% [markdown]
# ### Global graph search — over community reports

# %%
def retrieve_graph_global(query: str, top_k_communities: int = 2) -> Dict:
    """Find the most relevant community reports and aggregate their members."""
    qv = np.array(embed_texts([query], "query")[0])
    report_scores = cosine_sim(qv, report_embeddings)
    top = np.argsort(report_scores)[::-1][:top_k_communities]
    return {
        "matched_communities": [
            {"report": community_reports[i], "score": float(report_scores[i])}
            for i in top
        ],
    }


# %% [markdown]
# ### HippoRAG-style PPR (bonus, alternative)

# %%
def retrieve_pp_pagerank(query: str, top_k: int = 3, alpha: float = 0.15) -> Dict:
    """Personalized PageRank seeded by query-matched entities."""
    qv = np.array(embed_texts([query], "query")[0])
    ent_scores = cosine_sim(qv, entity_embeddings)
    seeds = {entity_list[i]: float(ent_scores[i]) for i in np.argsort(ent_scores)[::-1][:5]}

    # NetworkX PPR
    ppr_scores = nx.pagerank(G_undirected, alpha=1 - alpha, personalization=seeds)
    top_nodes = sorted(ppr_scores.items(), key=lambda kv: -kv[1])[:10]

    # Walk back: top-PPR entities → source docs → top-k docs by union frequency
    doc_scores: Dict[str, float] = defaultdict(float)
    for node, score in top_nodes:
        for d in entity_sources[node]:
            doc_scores[d] += score
    top_docs = sorted(doc_scores.items(), key=lambda kv: -kv[1])[:top_k]

    return {
        "seeds": list(seeds.keys()),
        "top_ppr_entities": [(n, round(s, 4)) for n, s in top_nodes[:5]],
        "chunks": [
            {"doc": next(d for d in CORPUS if d["id"] == doc_id), "score": score}
            for doc_id, score in top_docs
        ],
    }


# %% [markdown]
# ## Step 7 — Routing classifier
#
# Picks vector / local-graph / global-graph / ppr per query. Cheap LLM call.

# %%
ROUTER_PROMPT = """Classify the user query into ONE of these retrieval modes:

- "vector" — simple semantic lookup, single-document answer likely.
- "local_graph" — query names specific entities and needs their relationships or neighborhood.
- "global_graph" — query asks about themes/patterns/trends across multiple documents.
- "ppr" — multi-hop reasoning connecting entities through the graph.

Reply with JSON: {"mode": "...", "reasoning": "..."}.

Query: {query}

Output JSON only.
"""


def route_query(query: str) -> str:
    msg = client.messages.create(
        model=EXTRACT_MODEL,
        max_tokens=200,
        messages=[{"role": "user", "content": ROUTER_PROMPT.format(query=query)}],
    )
    raw = msg.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()
    try:
        return json.loads(raw)["mode"]
    except Exception:
        return "vector"  # safe default


# %% [markdown]
# ## Step 8 — End-to-end answering with routing

# %%
ANSWER_PROMPT = """Answer the question using only the context provided. Cite source document IDs in [brackets].

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""


def answer_with_routing(query: str) -> Dict:
    mode = route_query(query)
    if mode == "vector":
        ret = retrieve_vector(query, top_k=3)
        context = "\n\n".join(f"[{r['doc']['id']}] {r['doc']['text']}" for r in ret)
    elif mode == "local_graph":
        ret = retrieve_graph_local(query, hops=2)
        context = "\n\n".join(f"[{r['doc']['id']}] {r['doc']['text']}" for r in ret["chunks"])
        context += f"\n\n[graph context] Entities involved: {', '.join(ret['neighborhood'][:10])}"
    elif mode == "global_graph":
        ret = retrieve_graph_global(query)
        context = "\n\n".join(
            f"[Community {c['report']['community_id']}: {c['report']['title']}] "
            f"{c['report']['summary']} Findings: {'; '.join(c['report']['key_findings'])}"
            for c in ret["matched_communities"]
        )
    else:  # ppr
        ret = retrieve_pp_pagerank(query, top_k=3)
        context = "\n\n".join(f"[{r['doc']['id']}] {r['doc']['text']}" for r in ret["chunks"])
        context += f"\n\n[graph context] PPR top entities: {ret['top_ppr_entities']}"
    msg = client.messages.create(
        model=ANSWER_MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": ANSWER_PROMPT.format(context=context, question=query)}],
    )
    return {"mode": mode, "answer": msg.content[0].text.strip(), "retrieval": ret}


# %% [markdown]
# ## Step 9 — Run a battery of queries that exercise each retriever

# %%
queries = [
    # Vector: simple, single-doc
    ("What is the 401k match policy?", "expected: vector"),
    # Local graph: entity-anchored
    ("What is Dr. Maria Chen responsible for, and what does she oversee?", "expected: local_graph"),
    # Global graph: theme across docs
    ("What recurring compliance themes appear across our 2024-2025 policies?", "expected: global_graph"),
    # PPR / multi-hop: connects entities through the graph
    ("For a stage-3 HCC patient with portal hypertension, who should review the case at Acme?", "expected: ppr or local_graph"),
    # Aggregative
    ("Who are the senior administrators mentioned across our policy documents?", "expected: global_graph or local_graph"),
]

for q, expected in queries:
    print(f"\n{'=' * 70}\nQ: {q}\n  ({expected})\n{'=' * 70}")
    result = answer_with_routing(q)
    print(f"Mode chosen: {result['mode']}")
    print(f"Answer:\n{textwrap.fill(result['answer'], width=80)}")


# %% [markdown]
# ## Things to try next
#
# 1. **Swap NetworkX for Neo4j.** Replace the in-memory graph with `py2neo` / `neo4j-graphrag-python`.
#    Same logic; the graph becomes persistent and you get Cypher queries.
# 2. **Implement PathRAG.** Instead of returning whole neighborhoods, find the **shortest paths**
#    between the query-matched seeds and return only the paths.
# 3. **Implement hierarchical Leiden.** Run community detection at multiple resolutions and generate
#    reports at each level. Then route global queries to the appropriate level.
# 4. **Add ontology grounding (OG-RAG style).** Map every extracted entity to a SNOMED CT or
#    similar ontology ID; use ID matching instead of string matching.
# 5. **Add cost tracking.** Count tokens at each LLM call; project to 100K-doc indexing cost.
# 6. **Build the evaluation harness.** For each query, hand-label the gold entities and gold answer;
#    measure entity recall, path correctness, and answer faithfulness (Module 13A patterns).
# 7. **Try HippoRAG 2-style continual learning.** Add a new doc; verify the graph updates incrementally
#    without re-extracting everything.
#
# ## What this demonstrated
# - Entity-relationship extraction is the cost driver, and Haiku-class models are cheap enough.
# - Communities + LLM-generated reports turn graph-RAG global search into map-reduce over summaries.
# - **The routing classifier is what makes hybrid Vector+Graph viable** in production — each query
#   takes the cheapest retriever that produces a correct answer.
# - HippoRAG-style Personalized PageRank gives you multi-hop reasoning without iterative LLM calls,
#   at the cost of a one-time KG build.
