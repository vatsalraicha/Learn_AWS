# Quiz — Module 22 (GraphRAG Deep Dive)

## Recall

1. Name the three query strategies in Microsoft GraphRAG and one use case for each.
2. What does Microsoft GraphRAG mean by a "covariate," and why is it off by default?
3. Why does Microsoft GraphRAG use **Leiden** rather than Louvain for community detection?
4. What's the core innovation of HippoRAG — what algorithm does it use to enable multi-hop retrieval without iterative LLM calls?
5. HippoRAG 2 vs HippoRAG: name two architectural changes.
6. PathRAG retrieves something different from GraphRAG and LightRAG. What, and why?
7. OG-RAG uses **hyperedges**. What problem do hyperedges solve that regular edges don't?
8. HyKGE is essentially "HyDE applied to graph retrieval." Walk through its pipeline.
9. GraphReader uses a graph for what purpose — and what's the surprising long-context result?
10. MedGraphRAG's "triple-graph." What are the three tiers?

## Apply

11. You're routing queries in a hybrid system. Where do these go: (a) "What is Dr. Lee's primary specialty?" (b) "What patterns emerge across our last 100 patient notes?" (c) "Tell me about the new refund policy."
12. You have a 100K-document corpus, $20K budget for indexing, and want graph-RAG. Pick the framework and justify.
13. A team wants to deploy Microsoft GraphRAG. What's the single highest-leverage cost optimization they can apply at indexing time?
14. Healthcare case study: a doctor asks "Is sorafenib safe for this patient with severe portal hypertension and concurrent warfarin?" Which retrieval modes activate in a well-designed MedGraphRAG-style system, and in what order?

## Diagnose

15. Your graph-RAG system performs well on multi-hop questions (HotpotQA F1 = 0.68) but worse than vector RAG on simple factual lookups (NaturalQuestions accuracy = 0.61 vs 0.74). What's the diagnosis and the fix?
16. After deploying GraphRAG, you observe that indexing cost spiked 600× but answer quality only improved 4% on user-facing metrics. Three diagnostic questions to ask.
17. Your community reports look generic ("This community concerns business and people") rather than informative. Two likely causes.

## Defend

18. Argue against "we'll use Microsoft GraphRAG for everything." Make the case with specific costs and query-distribution facts.
19. PathRAG claims a 60% win rate over Microsoft GraphRAG via LLM-judge. Why might that number not transfer to your production setting?
20. Defend why a healthcare graph-RAG system should refuse 5% of legitimate questions rather than answer all of them.

---

## Answer key

<details>
<summary>Click to reveal</summary>

1. **Local search** — entity-anchored ("What did Dr. Lee say about X?"). **Global search** — map-reduce over community reports for aggregative queries ("What themes recur?"). **DRIFT** — hybrid: starts global with vector match on community reports, generates follow-up sub-questions, runs each as a local search.

2. **Covariates** are positive factual statements about entities — `(subject, object, type, status ∈ {TRUE, FALSE, SUSPECTED}, time-bounds, description)`. Example: "Celia murdered her husband and child (suspected)." They're off by default because they roughly double indexing cost and most teams don't have a use case ready — only enable when you'll actually query them.

3. Louvain can produce **disconnected communities** (nodes the algorithm says are in one community but aren't actually connected through the community's own edges). Leiden adds a refinement phase that guarantees connected, well-separated communities. Run hierarchically: each level groups the previous level's communities.

4. **Personalized PageRank (PPR).** At query time: LLM extracts query concepts → seed nodes in the KG → run PPR seeded at those nodes → highest-PPR passages are the retrieved context. PPR spreads probability mass through the graph, naturally visiting multi-hop neighbors of the seeds without an explicit iterative LLM loop. Result: comparable quality to iterative retrieval (IRCoT) at 10-20× lower cost and 6-13× faster.

5. (a) **Dual-node KG** — both passage nodes AND phrase nodes coexist; PPR seeds and spreads over both. (b) **LLM-based triple filtering** at query time removes noise from PPR's broad spread. (c) **Unification of dense + sparse retrieval** for seeding. (d) **Continual learning** — incremental doc updates without full re-indexing. (Any two.)

6. PathRAG retrieves only **the relational paths between query-relevant nodes**, not whole communities (GraphRAG) and not immediate neighbors (LightRAG). Uses flow-based pruning with distance-aware reliability scoring. Reasons: less noise; better citation (the path IS the explanation); helps with lost-in-the-middle by ordering paths inside the prompt.

7. Regular edges are pairwise — only connect two entities. Many facts are inherently multi-way: *"In 2024, Acme launched Product X in Region Y under Compliance Framework Z"* involves 5 entities in one constraint. Hyperedges connect all 5 nodes in a single edge, preserving the joint constraint. Pairwise decomposition loses that ("Acme launched in 2024" AND "Product X in Region Y" doesn't imply the original joint relationship).

8. (1) **HOM (Hypothesis Output Module)** — LLM generates a plausible answer to the query first. (2) **NER (Named Entity Recognition)** — extract entities from the *hypothesis*. (3) **Retrieve** from the medical KG using those entities. (4) **Rerank** with fragment-granularity-aware reranker that filters noise while balancing diversity and relevance. (5) Generate final answer with grounded context. Core insight: short user queries are under-specified; let the LLM imagine the answer's shape first, then retrieve real evidence for that shape.

9. **As a navigation aid** for long single documents. The agent chunks the long doc, builds a graph linking chunks via shared entities, then plans and walks the graph using predefined functions (read node content, read neighbors). Surprising result: **with a 4K context window, GraphReader beats GPT-4 with 128K context** across context lengths from 16K to 256K. The trick: more selective attention to relevant content beats brute-force long-context.

10. (a) **Tier 1 — user documents** (clinical notes, internal protocols). (b) **Tier 2 — credible medical sources** (PubMed abstracts, FDA labels, clinical guidelines). (c) **Tier 3 — general medical knowledge graph** (UMLS, SNOMED CT). Every response must trace from user doc → credible source → general KG. Three tiers exist to enforce traceability and authority hierarchy.

11. (a) **Local graph search** — entity-anchored query about a specific person. (b) **Global graph search** — aggregative theme query across many documents. (c) **Vector RAG** — simple semantic lookup, single-doc answer likely.

12. **LightRAG** or **LazyGraphRAG**. Microsoft's full GraphRAG indexing on 100K docs is ~$40K-$60K (above budget). LightRAG runs at ~10% of that cost (~$4K-8K) for comparable retrieval quality. LazyGraphRAG defers extraction to query time → only ~0.1% of indexing cost, with quality close enough for most use cases.

13. **Switch from Sonnet-class to Haiku-class for the entity extraction LLM call** (the per-chunk cost driver). Often saves 70% of the extraction budget. Reserve Sonnet for community report generation, where the quality difference matters more. Closely behind: enable LazyGraphRAG / sample-and-extrapolate; skip covariates unless you'll use them; smaller chunks reduce per-chunk extraction tokens.

14. Likely order: (a) **PathRAG-style local** — find the path from `sorafenib → contraindicated_in → severe portal hypertension`. (b) **PathRAG-style** for drug-interaction path: `sorafenib → interacts_with → warfarin`. (c) **Tier escalation** through the MedGraphRAG triple-graph: user doc (this patient's chart) → credible source (sorafenib FDA label) → general KG (drug-drug interaction in RxNorm/UMLS). (d) **Authority-tier reranker** ensures peer-reviewed/FDA sources outrank internal notes. (e) **Abstention check** — if any link is missing or any contraindication ambiguous, the system refuses with "consult clinician." All of these compose in a well-designed system; a single retriever isn't enough.

15. The system is **over-routing to graph-RAG**. Simple factual queries don't need graph traversal; the extra graph context adds noise. Fix: improve the **routing classifier** so simple lookups route to vector RAG, and only multi-hop / aggregative queries go to graph. Track per-mode quality.

16. (a) **What fraction of production queries are actually multi-hop or aggregative?** If <15%, graph-RAG isn't earning its keep. (b) **Did the queries that DID benefit show meaningful quality lift?** If you exclude the queries that didn't need graph, what's the lift? (c) **Could a simpler alternative (HyDE, multi-query, better reranker, contextual retrieval) have closed the gap at a fraction of the cost?**

17. (a) The **community is too coarse** — Leiden produced a huge top-level community covering most of the graph; the LLM summarizer can't say anything specific. Fix: use a finer level (L0 or L1, not L2/L3). (b) The **summarization prompt is too generic** — doesn't ask for entity-specific or relationship-specific findings. Fix: prompt template tailored to your domain (medical: "what conditions, drugs, and treatments are discussed; who are the key clinicians"; legal: "what doctrine, jurisdiction, and parties").

18. Most production query distributions are ~80% simple lookups (vector RAG handles), ~15% multi-hop (graph wins), ~5% multi-step (agent needed). Microsoft GraphRAG indexing is 100-1000× vector RAG indexing cost — that's $40K-$60K for a 100K-doc corpus. Spending that to improve 15% of queries by ~20% gives a break-even of 10+ months on cost-sensitive workloads (e.g., 100K customer-support queries/month at $1 per better answer). The right answer is **adaptive routing**: vector RAG default, graph RAG only when query distribution warrants. Start with LightRAG or LazyGraphRAG to reduce indexing cost 10-100×. Most teams don't need full Microsoft GraphRAG.

19. (a) **LLM-judge bias** — the judge model has preferences that may not match your users' preferences. (b) **Eval-set composition** — the 60% win rate is on benchmark queries (likely multi-hop, paper-friendly); your production distribution may look different. (c) **Cost wasn't measured** — PathRAG's path extraction may add latency that the win-rate eval ignored. (d) Your **own corpus and domain** may favor different retrieval shapes (e.g., flat policy docs vs. relational entity-heavy corpora). The right move: A/B PathRAG and current system on YOUR queries with YOUR judges/users.

20. (a) **Clinical harm asymmetry** — wrong answer can hurt patients; over-refusal frustrates users but is recoverable. The asymmetric cost demands liberal refusal. (b) **Regulatory** — FDA SaMD classification, HIPAA, malpractice exposure all penalize confidently-wrong answers far more than refusals. (c) **Trust** — once a clinical AI is caught being confidently wrong, it loses trust permanently. Refusing maintains long-term usability. (d) **Architecture support** — refusal is feasible because graph-RAG's authority tiers + provenance trace let you measure when no peer-reviewed source supports an answer, then refuse cleanly. Better to be a useful tool 95% of the time and silent the other 5% than to be a confidently-wrong tool 100% of the time.

</details>
