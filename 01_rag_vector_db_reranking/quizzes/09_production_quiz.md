# Quiz — Module 9 (Production)

## Recall

1. Roughly, where does the cost go in production RAG (top three buckets)?
2. Name three distinct caching layers and what each caches.
3. What is indirect prompt injection? Where does OWASP rank it on the LLM Top 10 (2025)?
4. What's "Context Rot"?

## Apply

5. You upgrade your embedding model. What's the deployment plan that avoids downtime and quality regression?
6. Your latency p95 is 3.5s, budget is 2s. Reranker is 600ms p95, LLM is 2s p95. Where do you start cutting?
7. You're crawling external webpages into your RAG corpus. What two layers of injection defense are non-negotiable?

## Diagnose

8. Semantic cache is hitting 60%, but you're seeing stale answers in production. Likely cause?
9. Your reranker's API has p99 latency spikes to 3 seconds. Mitigations?

## Defend

10. "We optimize p50 latency." Argue against, propose alternative.
11. Why is "attribution-gated answering" a stronger defense against injection than "filtering retrieved content for prompt-injection patterns"?

---

## Answer key

<details>
<summary>Click to reveal</summary>

1. Embedding generation (40-60%), Vector storage + search (20-35%), LLM inference (15-25%). Infra rounds it out.
2. (a) **Embedding cache** — content hash → vector. (b) **Semantic response cache** — query embedding → past response if similar enough. (c) **LLM provider prompt cache** — server-side cache of static prompt prefixes. Each addresses different pieces of the latency/cost stack.
3. Attacker plants malicious instructions in content the system will later retrieve (webpages, support tickets, public docs). At query time, retriever pulls the poisoned chunk into context; the LLM follows the embedded instructions. OWASP LLM Top 10 (2025): **#1**.
4. Even within rated context length, LLM answer quality degrades non-linearly with input size. The "1M token capability" overstates real-world capability for non-trivial multi-fact reasoning.
5. Blue-green: build a *new* index in parallel using the new embedder. Re-embed the corpus at off-peak. Run both indexes in shadow mode and compare quality on the eval set. When new index passes, atomically switch query traffic. Keep the old index for rollback.
6. The LLM and reranker dominate. (a) Reduce reranker work — fewer candidates (top-50 instead of top-100), or cheaper reranker model. (b) Stream the LLM (TTFT matters more than full-response latency for perceived speed). (c) Aggressively cache. (d) Self-host the reranker if API tail latency is the killer.
7. (a) Source allowlisting / provenance — only ingest from trusted, hashed sources, OR a sanitization layer that can detect adversarial structure. (b) Action screening for any agent tool calls — separate intent-vs-action check ignoring retrieved content. Without these two, indirect injection is essentially undefended.
8. TTL too long. Corpus updated; cache didn't. Set TTL aligned with corpus update cadence (often hours, not days). Or: use cache invalidation triggered by corpus updates.
9. (a) Self-host the reranker on a GPU pool — eliminates external API tail. (b) Parallel call with timeout fallback to a smaller local reranker. (c) Skip rerank for adaptive-routed easy queries. (d) Smaller candidate set (top-50 → top-30) reduces variance.
10. p50 hides tail latency. The 5% of users on the 5-second tail dominate satisfaction. Optimize **p95** or **p99** as the SLO; ensure p50 stays acceptable as a side effect.
11. Pattern-based filtering of retrieved content is a cat-and-mouse game — attackers iterate to bypass patterns. Attribution-gated answering changes the model's *contract*: "you may only state facts traceable to a retrieved source span, with citation." There's no slot for the injected "ignore previous instructions" because there's nothing it could be a citation for. Stronger because it's structural, not heuristic.

</details>
