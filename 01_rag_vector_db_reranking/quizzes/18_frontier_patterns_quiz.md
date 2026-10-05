# Quiz — Module 18 (Frontier Retrieval Patterns)

## Recall

1. SPLADE outputs what kind of vector, and what's the storage advantage over dense embeddings?
2. Three integration patterns for reasoning-model RAG.
3. The 2025 surprising finding about chain-of-thought length and answer quality.
4. LightRAG vs Microsoft GraphRAG — what's LightRAG's headline efficiency win?

## Apply

5. You have a strong dense embedder + reranker stack. Should you add SPLADE? What query-pattern tells you yes/no?
6. Pick a use case for each: o1-style reasoning model in RAG vs Search-during-thinking pattern vs self-consistency.
7. KG construction: schema-based vs schema-free — which would you pick for healthcare and which for a research-paper corpus?

## Diagnose

8. Your agentic RAG loop runs 5-15× the cost of single-shot RAG. Three guardrails to install.
9. You added a reasoning model to your pipeline; quality didn't lift on simple lookup queries (and got slightly worse). Why?

## Defend

10. Argue "schema-based KG construction is the right default for enterprise RAG."
11. Defend why SPLADE deserves consideration even when you already have dense + BM25 hybrid.

---

## Answer key

<details>
<summary>Click to reveal</summary>

1. **Sparse vector** over the BERT vocabulary (~30K dim, mostly zero, non-zero with learned weights including term-expansion entries). Stored in **standard inverted indexes** — same infrastructure as BM25 (Lucene, Elasticsearch). Adoption-cheap because no new vector store needed.
2. (a) **Reasoning model as generator** — drop in over standard RAG; better synthesis at higher cost/latency. (b) **Search-during-thinking (Search-o1, Search-R1)** — model interleaves retrieval calls with thought; trained to know when to search. (c) **Self-consistency** — sample N RAG runs, vote.
3. Longer CoTs do NOT consistently produce better answers. For o1-style models, **correct solutions are often shorter than incorrect ones for the same question.** Don't blindly crank up reasoning compute; measure.
4. **10× token reduction** for comparable accuracy. **65-80% cost savings** at 1500+ docs/month. Achieved through dual-level retrieval and single-pass entity-relation extraction (vs Microsoft GraphRAG's multi-pass community detection).
5. SPLADE earns its keep when queries have **rare-vocabulary patterns** (jargon, codes, OOV terms) where dense fails AND BM25 misses semantic relationships. If your query patterns are uniform / well-covered by dense, SPLADE adds latency for marginal gain.
6. **Reasoning model as generator:** multi-hop synthesis with bounded latency (financial analysis, legal reasoning). **Search-during-thinking:** open-ended research where the model needs to autonomously decide what to look up. **Self-consistency:** high-stakes short answers where vote-aggregation reduces variance (medical diagnosis ranking).
7. **Healthcare:** schema-based — strong existing ontologies (SNOMED, ICD, MeSH); regulatory traceability requires consistent vocabulary. **Research papers:** schema-free / EDC — cross-domain heterogeneity, schema would be too restrictive; canonicalization happens post-hoc.
8. (a) Cap iterations at 5-7. (b) Token budget per query (50K input max). (c) Cost-per-query alarm in observability. (d) Fall back to single-shot if iteration budget exhausted. (e) A/B against single-shot to confirm iterative actually wins on user metrics.
9. Reasoning models add overhead — extra "thinking tokens" — that doesn't help simple queries (where the answer is in one chunk). On simple lookups, the reasoning model spends compute reasoning over an obvious answer, and may second-guess itself into wrong territory. Solution: adaptive routing (Module 7) — only route hard / multi-hop queries to the reasoning model.
10. (a) Enterprises have well-defined entity types (customers, products, contracts, employees). (b) Schema-based extraction stays consistent across docs and across time (ontology versioned). (c) Easier to integrate with existing data models / data warehouses. (d) Better audit story: "did the LLM extract this triple correctly per our schema" is a cleaner question than "is this freeform triple structurally valid." (e) Schema-free output requires significant canonicalization work that schema-based gets up-front for free.
11. (a) SPLADE bridges BM25 and dense — beats BM25 on complex queries due to learned term weights AND beats dense on rare-vocab queries due to literal-token matching. (b) Hybrid (BM25 + dense + SPLADE, all RRF-fused) gains another 5-10 points over (BM25 + dense) on hard query sets. (c) Same inverted-index infra as BM25 — no new system to operate. (d) Better audit story than dense — the sparse weights are interpretable per-token. The cost is real (build pipeline, additional index) but for mature search infra it's straightforward to add.

</details>
