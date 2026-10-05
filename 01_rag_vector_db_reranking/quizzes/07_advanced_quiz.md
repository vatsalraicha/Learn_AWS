# Quiz — Module 7 (Advanced & Agentic RAG)

## Recall

1. What are the four reflection tokens in Self-RAG?
2. What three labels does CRAG's retrieval evaluator emit?
3. What does Adaptive RAG's classifier predict?
4. Name the indexing pipeline of GraphRAG in three steps.
5. What is LazyGraphRAG's contribution over full GraphRAG?

## Apply

6. You're shipping an enterprise multi-hop QA product over 10K+ documents about regulatory filings. RAG or GraphRAG?
7. You have 200K-token corpus and Gemini 3. Long context or RAG?
8. Your team picked an off-the-shelf model that doesn't have Self-RAG-style training. How would you replicate the *behavior* of Self-RAG without the trained model?

## Diagnose

9. After enabling GraphRAG, simple factual queries got slower and slightly *less* accurate. What's the typical pattern, and which adaptation would help?
10. Your agentic RAG system loops until cost runs out on certain queries. What's missing?

## Defend

11. Single-needle NIAH benchmarks "overstate production capability." Defend that statement with a specific number.
12. Long context will eventually replace RAG. Defend or refute.
13. Adaptive RAG's classifier looks like overhead. Defend its inclusion.

---

## Answer key

<details>
<summary>Click to reveal</summary>

1. `[Retrieve]`, `[IsRel]`, `[IsSup]`, `[IsUse]`.
2. **Correct**, **Incorrect**, **Ambiguous**.
3. Query difficulty / complexity — typically: no-retrieval-needed, single-step, multi-step. Routes to the matching pipeline.
4. (1) Extract entities + relationships from each chunk into a knowledge graph. (2) Cluster the graph hierarchically (Leiden algorithm) into communities. (3) LLM-summarize each community at multiple levels.
5. Skips exhaustive entity extraction at indexing; does it on-the-fly during queries. **Reduces indexing cost to ~0.1% of full GraphRAG**, retains most quality.
6. **GraphRAG** (or LazyGraphRAG to control cost). 86% accuracy on multi-hop benchmarks vs 32% for vector RAG. Multi-hop is exactly where graph-based shines.
7. Likely RAG. Even Gemini 3 has Context Rot at higher inputs; multi-needle scores trail single-needle. RAG over a focused chunk-set commonly beats long-context for the same total budget at 200K+ on non-Gemini, and even on Gemini it's often a wash. Test both — but start with RAG.
8. Add CRAG-style: external classifier (small LLM or rule) judges retrieved chunks; bad chunks trigger query rewrite or skip retrieval. Behavior achieved via pipeline orchestration rather than model-internal tokens.
9. Pattern: GraphRAG adds latency (~2.3× on average) and on simple lookups underperforms vector RAG by ~13.4% on Natural Questions. Adaptation: **Adaptive routing** — classify query, route simple lookups to vector RAG and multi-hop to GraphRAG.
10. Explicit stop conditions: max iterations (5-7), token budget cap, no-progress detection ("we're not learning anything new"). Without these, agents loop indefinitely.
11. Multi-needle scores trail single-needle by 15-40 points across all frontier models. Production queries are usually multi-needle; single-needle "1M token capability" overstates real capability by that 15-40 point gap.
12. **Refute (with nuance):** in some narrow regimes (small corpora, Gemini-class models, infrequent updates) long context will replace RAG. But for most enterprise deployments — large corpora, frequent updates, cost sensitivity, multi-hop — RAG wins on cost, freshness, and actual accuracy. The frontier is **hybrid**: retrieve focused chunks, then long-context-reason over them.
13. Most queries are easy. Running the full agent loop, multi-query, GraphRAG on every query wastes 90% of the cost. A small T5 or even prompt-based classifier costs ~10ms; saves seconds and dollars on the easy 80% of traffic. Pays for itself 1000×.

</details>
