# Quiz — Module 11 (Personalization & Conversational RAG)

## Recall

1. What's the standard technique to handle "follow-up question" turns in conversational RAG?
2. Per MTRAG-style benchmarks, what's the rough drop in Recall@5 from first to later turns?
3. Name three things you'd put in a user profile.
4. What's the difference between **personalization** and **memory** in a chatbot?

## Apply

5. Conversation: User asks about Contextual Retrieval, then asks "How does it compare to late chunking?" Trace what naïve retrieval would do vs. what a query-rewriter-equipped system would do.
6. You have a backend that picks an LLM model size for the rewriter. Why is a fast/cheap model the right choice?
7. List the three architectural levels of personalization, ordered by cost.

## Diagnose

8. Your chatbot's first-turn retrieval looks great; by turn 4, users complain about wrong answers. What's the most likely cause and the cheapest fix?
9. You added a static user profile but personalization quality plateaued after a week. What did you forget?

## Defend

10. "Personalization is just metadata filtering." Argue against this in 2-3 sentences.
11. Your team wants to feed the entire 30-turn conversation into the rewriter "for completeness." Defend the alternative.

---

## Answer key

<details>
<summary>Click to reveal</summary>

1. **Query rewriting** — use an LLM (cheap/fast) to rewrite the latest message into a standalone, decontextualized query that resolves coreferences and carries forward prior context. THEN embed and retrieve.
2. From ~0.89 first turn to ~0.47 on later turns. The dominant cause is unresolved coreferences (~60% of follow-up messages).
3. Any three of: explicit preferences (role, expertise, language), implicit signals (clicks, dwell time, thumbs), behavioral history (past queries, engaged chunks), constraints (tenant, role, region), aggregated preference embedding.
4. **Personalization** = stable user attributes that shape *retrieval ranking* ("backend engineer in healthcare"). **Memory** = specific facts the assistant learned about the user that shape *what the model knows* ("user's wife's name is Priya"). Different stores, different roles.
5. Naïve: embeds the literal "How does it compare to late chunking?" → retrieves docs about late chunking only, misses Contextual Retrieval. Rewriter: combines history + message → emits "How does Anthropic's Contextual Retrieval compare to late chunking?" → retrieval now lands in both topic regions and finds comparison-relevant chunks.
6. Latency. Rewriter sits in the critical path before retrieval. Adding 800ms of GPT-4-class rewriter blows the budget. Haiku/Flash/4o-mini at < 200ms preserves the budget while doing 95% of the rewriting job.
7. (1) **Filter-based scoping** (tenant/role/region as metadata filters) — cheapest. (2) **Reranker-conditioned** — pass user profile as context to the reranker. (3) **Profile-as-vector** — aggregate engagement embedding combined with query embedding at retrieval time — most expensive.
8. Multi-turn retrieval failure due to unresolved coreferences. Cheapest fix: add a query-rewriter step before retrieval using a fast LLM. Empirically lifts later-turn recall from ~0.47 back toward first-turn 0.89.
9. The feedback loop. Profile is static; signals collected from interactions weren't fed back to update it. Even simple loops ("boost up-voted sources") beat fancier static profiles. Track explicit (thumbs) and implicit (dwell, copy) signals; recompute profile on a cadence.
10. Filter-based scoping is access control disguised as personalization — it limits the *candidate set* but doesn't change *how the candidates are ranked* for a given user. Two backend engineers in healthcare with different prior interests get the same ranking under filter-only; real personalization differentiates between them via behavior signals or profile vectors.
11. Performance saturates after 4-6 user turns; bot turns barely contribute. 30-turn input is mostly tokens that don't move the rewriter's quality, but they do raise cost and latency. Use a rolling summary of older turns + last 3-4 verbatim. Same quality, ~10× cheaper.

</details>
