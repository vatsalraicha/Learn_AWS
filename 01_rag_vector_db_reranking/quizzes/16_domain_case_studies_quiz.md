# Quiz — Module 16 (Domain Case Studies)

## Recall

1. Name the four PHI exposure surfaces in a clinical RAG system.
2. What's the canonical legal-RAG benchmark, and what makes it different from LegalBench?
3. Three numerical-precision safeguards specific to financial RAG.
4. What does industry data say about ticket deflection rates achievable with mature customer-support RAG?

## Apply

5. You're building a clinical decision-support tool for cardiologists. Map the architecture: authority tier filter, refusal threshold, citation level, latency budget.
6. A customer-support bot's deflection rate is 70% (above target). What's the signal that you're over-deflecting?
7. Pick the right architecture for: "produce a quarterly earnings summary citing specific numbers from a 10-K filing."

## Diagnose

8. A legal AI tool consistently confuses California and Texas case law on property disputes. Specific architectural fix?
9. A healthcare RAG bot answers eligibly but the chunk it cited is from 2018 (current is 2024). Two failures must be fixed — name them.

## Defend

10. Argue why "knowledge base quality determines 80% of customer-support agent performance" — what's load-bearing.
11. Defend running a dedicated structural-number-validator AFTER faithfulness in a financial RAG.

---

## Answer key

<details>
<summary>Click to reveal</summary>

1. Query text, retrieved chunks, generated response, audit log.
2. **LegalBench-RAG** — successor designed specifically for retrieval evaluation. 6,858 expert-annotated query-answer pairs over 79M characters. LegalBench tested generation; LegalBench-RAG isolates and tests retrieval precision specifically (does the system find the right *clauses*, not just the right docs).
3. (a) Structural number-match validation against source (regex/exact comparison). (b) Time-aware retrieval with `as_of_date` metadata to avoid prior-period docs. (c) Text-to-SQL routing for quantitative queries (don't embed tabular data). Bonus: per-claim faithfulness with the chunk's exact figure.
4. 40-60% deflection rate is achievable with mature RAG + well-maintained KB. ~30% operational cost reduction. CSAT lift ~25%. KB quality determines ~80% of agent performance.
5. **Authority tier filter:** peer-reviewed > major guideline > internal protocol > older notes. **Refusal threshold:** very high — refuse when no peer-reviewed source supports answer. **Citation level:** claim-level grounding required, with source authority displayed. **Latency budget:** 2-5s acceptable; clinicians will wait for accuracy.
6. (a) Re-query rate within 24h going up (users coming back). (b) CSAT dropping. (c) Escalations that DO happen are taking longer (because users tried bot first, got bad answer, then escalated frustrated). Optimal target is "high deflection + low re-query + stable CSAT," not just deflection.
7. **Hybrid: text-to-SQL on the 10-K's tables + RAG on its narrative.** Numbers come from SQL with structural validation; analysis comes from RAG with citation. Pure RAG over a 10-K wastes tokens on tables that should be queried as data.
8. Self-querying retriever extracts jurisdiction at query time AND filters retrieval by `jurisdiction = 'TX'`. Plus reranker boosting same-state cases. Plus a status-validator step that rejects if retrieved cases are out-of-jurisdiction.
9. (a) Retrieval failure: stale chunk surfaced because the time/recency metadata wasn't filtered. **Add date-aware retrieval.** (b) Citation validation failure: even if 2018 chunk surfaced, the answer should have flagged "this guidance was superseded in 2024." **Add as-of-date display + supersession metadata to chunks.**
10. RAG can only retrieve what's in the corpus. If the KB has stale, contradictory, or missing articles, no architecture can fix it. Better embedder → still retrieves stale docs. Better reranker → ranks stale docs higher. Better generator → produces fluent stale answers. The KB is the floor; the pipeline is multipliers on that floor.
11. Faithfulness checks "answer is consistent with retrieved context" — but it's an LLM-judge, prone to numerical fuzziness. A claim like "$1,400" supported by source "$1.4M" might pass faithfulness (both reference money) but is materially wrong. A structural validator that extracts every number from the answer and verifies it appears verbatim (or within tolerance) in the source catches this class of error that no LLM-judge reliably does.

</details>
