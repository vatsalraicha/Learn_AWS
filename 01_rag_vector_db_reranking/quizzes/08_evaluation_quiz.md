# Quiz — Module 8 (Evaluation)

## Recall

1. Name the three metrics in the "RAG triad."
2. What's the difference between Context Precision and Context Recall?
3. NDCG@k — what does it measure, and why is it used over plain Recall@k for reranker leaderboards?
4. Name three RAG eval frameworks and their primary use cases.

## Apply

5. You have Recall@10 = 0.95 but Faithfulness = 0.55. Which stage is broken, and what would you investigate first?
6. Faithfulness is 0.95 but users complain answers are wrong. What's the diagnosis?
7. You're starting a fresh RAG project — no labeled eval set. How would you bootstrap one in a day?

## Diagnose

8. Ragas reports faithfulness 0.92; DeepEval reports 0.71. Which is "right"?
9. Recall@10 = 100%, Precision@10 = 30%. The LLM downstream is hallucinating. Connect the dots.

## Defend

10. "We use thumbs-up rate as our only metric." Argue why this is dangerous.
11. Why is per-stage measurement essential? What goes wrong with "end-to-end accuracy" as the only metric?

---

## Answer key

<details>
<summary>Click to reveal</summary>

1. **Context Relevance**, **Faithfulness**, **Answer Relevance**.
2. **Context Precision:** of the retrieved chunks, how many are actually relevant? **Context Recall:** of all the truly relevant chunks in the corpus, how many made it into the retrieved set? Precision is "how clean is what we got"; recall is "did we get enough."
3. **Normalized Discounted Cumulative Gain at k.** Graded relevance with position discount — relevant docs at rank 1 count more than at rank 10. Reranker leaderboards (BEIR) use it because reranking is fundamentally about *ordering*, not just inclusion. Recall@10 doesn't penalize a relevant doc at rank 10 vs rank 1; NDCG does.
4. **Ragas** — metric exploration, paper-style eval, strict logical entailment. **DeepEval** — pytest-style, CI/CD gates. **TruLens** — dashboards, experiment tracking. (Phoenix, LangSmith also valid.)
5. **Generation stage is broken.** Retrieval is fine (right chunks landed in top-10), but the LLM isn't using them faithfully. Investigate: prompt structure (is context cleanly separated?), context noise (too many irrelevant chunks crowding signal?), model choice (small models are more prone to drift).
6. The retrieved context itself is wrong. Faithfulness = 0.95 means "the answer follows from the context"; it doesn't say the context is *correct*. The corpus may be stale or contradictory. Investigate corpus accuracy and recency.
7. Use Ragas' or DeepEval's `TestsetGenerator` against your corpus to generate 100-200 (question, ground-truth, golden context) tuples. Hand-review 30-50 for sanity. Mix in the 10-20 real user queries you have. Day 1 done; you can iterate from there.
8. Neither is "right." They measure differently — Ragas is strict logical entailment, DeepEval is pragmatic-interpretation. Use both: a query that fails on Ragas but passes DeepEval is "valid paraphrase"; a query that passes Ragas but fails DeepEval is "technically supported but misleading." Both are useful.
9. Recall = 100% (relevant docs in top-10), Precision = 30% (7 of 10 are noise). The LLM is fed mostly irrelevant context — it gets confused and hallucinates from the noise or mixes facts across contexts. Add a reranker (cuts top-10 to top-5 by quality), or shrink the chunk count passed to the LLM.
10. (a) Survivorship bias — only motivated users vote. (b) Doesn't localize failures (was it retrieval or generation?). (c) Lags by minutes-to-hours; you can ship a regression and not see signal until tomorrow. (d) Doesn't catch silent quality drift on rare query types. Need it as a *signal*, not the only one.
11. With only end-to-end accuracy, a regression tells you "something broke" but not where. Was retrieval bad, was the prompt bad, was the model bad? You waste days chasing the wrong fix. Per-stage metrics localize: low context recall → fix retrieval; high context recall + low faithfulness → fix generation; high faithfulness + low answer relevance → fix the prompt's instruction.

</details>
