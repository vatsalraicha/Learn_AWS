# Quiz — Module 13A (Eval Methodology & Statistics)

## Recall

1. Walk through the two-step LLM pipeline that Ragas uses to compute faithfulness.
2. Name three documented LLM-judge biases and one mitigation each.
3. What's the standard mitigation for self-preference bias?
4. What does Krippendorff's α measure, and what's an acceptable production target?
5. Name three RAG-specific benchmarks (released 2024+) and what each is best for.

## Apply

6. You ran your eval and got Ragas 0.81 → 0.84 on a 100-question set. Should you ship the change? What's the right test?
7. Pick a benchmark for: (a) choosing an embedder, (b) testing if the reranker upgrade is real, (c) testing if your long-context decision is sound, (d) end-to-end RAG quality with multi-hop hard questions.
8. You're designing eval for a customer-facing healthcare RAG product. Roughly what eval set size and bootstrap iteration count would you choose?

## Diagnose

9. Pipeline A and Pipeline B both show 0.83 faithfulness with 95% CI [0.78, 0.88] each. A senior engineer wants to ship A because "it scored 0.83 in two consecutive runs." What's wrong with their reasoning?
10. Your eval pipeline runs 5 questions per Wikipedia passage (3 passages, 15 questions). Bootstrap CIs look great. What's the silent assumption being violated and how does it bias your conclusions?

## Defend

11. Defend "you can't compare Ragas 0.85 across teams unless you specify the judge model and version."
12. Your team only runs end-to-end accuracy as the eval. Argue why per-stage component evals are not optional.

---

## Answer key

<details>
<summary>Click to reveal</summary>

1. **Step 1 — claim decomposition:** an LLM prompt breaks the answer into atomic, pronoun-resolved statements (output as JSON list). **Step 2 — NLI verification:** for each statement, an LLM judge labels 0 or 1 based on whether it's entailed by the retrieved context. Score = supported / total claims.
2. Any three of: **Position bias** (mit: A↔B swap, take agreement); **Verbosity bias** (mit: rubric anchoring, length-normalized scoring); **Self-preference bias** (mit: cross-family judge); **Style bias** (mit: rubric on factual content); **Limited reasoning** (mit: executable check fallback).
3. Use a judge from a **different model family** than the generator. Linked to self-recognition; same-family judges score same-family generations higher.
4. Inter-annotator/inter-rater agreement on categorical or ordinal labels; works with any data type, multiple raters, missing values. Production target: > 0.8 high; 0.67-0.8 substantial; < 0.67 rubric needs work.
5. Any three of: **RAGBench** (industry-aligned end-to-end, 100K examples, TRACe metrics); **RAGTruth** (word-level hallucination annotation, 18K responses); **FRAMES** (Google, multi-hop hard, 824 questions); **MTRAG** (multi-turn); **NoLiMa** (long-context with minimal lexical overlap).
6. **Probably not.** Run bootstrap on 100 samples → expect a 95% CI of roughly ±0.05-0.07. The 0.03 difference is within noise. Either expand sample to 400-500, or use a paired test (same questions on both pipelines, measure per-question delta), which is much more powerful at the same N.
7. (a) MTEB Retrieval. (b) BEIR NDCG@10. (c) NoLiMa. (d) FRAMES.
8. Customer-facing healthcare = high-stakes. Eval set 1000+ examples, bootstrap 1000+ iterations. Plus per-domain anchors and human SxS for safety-critical cases.
9. (a) 0.83 in two consecutive runs is a sample size of 2; says nothing. (b) The CI [0.78, 0.88] tells you the *single-run* uncertainty is ±0.05; far larger than any difference you could be claiming. (c) Without a paired test or larger N, you cannot claim A is better than baseline (or B). The correct response is more data or a paired comparison.
10. The 5 questions per passage are not independent — they share the same context, the same retrieval target. Standard bootstrap that resamples *questions* underestimates the true variance. Use **cluster-aware bootstrap** (resample passages first, then questions within them). True CIs are wider; "significant" results may not be.
11. (a) Different judges (GPT-4 vs Claude vs open-source) score the same answer/context differently due to bias profiles and knowledge. (b) Within the same judge family, version updates change scoring (silently — providers update behind stable names). (c) Without provenance the number is just a string; comparing it across teams is comparing apples to oranges. The discipline is: framework_name + judge_model + judge_version + eval_set_version, every time.
12. End-to-end accuracy tells you when something broke; not what broke. With per-stage metrics (Recall@k, NDCG, faithfulness, answer relevance), a regression localizes — "Recall@10 dropped means retrieval"; "Recall is fine but faithfulness fell means generation drifted." Without per-stage you spend days chasing the wrong fix. Both run together; per-stage on every PR (cheap), end-to-end nightly (expensive).

</details>
