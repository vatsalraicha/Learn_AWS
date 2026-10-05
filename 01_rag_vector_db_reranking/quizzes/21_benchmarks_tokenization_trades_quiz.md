# Quiz — Module 21 (Benchmarks, Tokenization & Trade Studies)

## Recall

1. Which benchmark do you cite for: (a) embedder quality, (b) reranker quality, (c) end-to-end RAG, (d) honest long-context?
2. Three Unicode-character categories that silently break RAG, with one example each.
3. Empirical 2025 finding on fine-tuning at scale (code completion).
4. The 2026 production consensus on RAG vs fine-tuning in one sentence.

## Apply

5. Your customer asks: "we want a chatbot that's helpful in our brand voice and answers from current product docs." RAG, FT, or both?
6. Your customer asks: "we have a stable taxonomy of 20 customer-intent categories; classify each support ticket." RAG, FT, or neither?
7. Pick a benchmark: "we want to claim our system handles legal pinpoint citations correctly."

## Diagnose

8. Your embedder scores well on MTEB but poorly on your domain queries. Two possible diagnoses.
9. The user types "401k" but your retriever returns nothing. The corpus has many 401k docs. What's likely wrong?
10. Your team fine-tuned on 50K examples and quality plateaued. Adding 100K more examples gave 0.2% improvement. What does this suggest about scaling further vs. switching to RAG?

## Defend

11. Argue against "we'll fine-tune the model on our entire knowledge base."
12. Defend why an architect should be able to pick a benchmark for any given claim, not just cite "MTEB."

---

## Answer key

<details>
<summary>Click to reveal</summary>

1. (a) **MTEB Retrieval** sub-track. (b) **BEIR** (NDCG@10 across 18 zero-shot domains). (c) **RAGBench** (TRACe metrics) and/or **FRAMES** (multi-hop). (d) **NoLiMa** (degradation 1K → 32K, requires semantic-not-literal matching).
2. **Zero-width** (ZWSP `U+200B`, soft hyphen `U+00AD`); **byte-order mark** (`U+FEFF`); **directional control** (RTL mark `U+202E`); **whitespace variants** (NBSP `U+00A0`, hair space `U+200A`).
3. Fine-tuning saturates around 300M tokens; RAG keeps improving with corpus size. Specifically: scaling FT from 90K → 120K files gave only 0.16-0.35% improvement; RAG (BM25 / CoCoSoDa) gave 2.13-2.26% at the same scale.
4. **Volatile knowledge → retrieval. Stable behavior → fine-tuning.** Most production needs both, on appropriate components.
5. **Both.** Fine-tune for brand voice (stable behavior). RAG over product docs (volatile knowledge). FT alone produces consistent voice answering stale facts; RAG alone gives correct facts in inconsistent voice.
6. **Fine-tune** (probably LoRA). 20-category classification is structured-output behavior; not knowledge that changes. RAG isn't needed if the categories are fixed. Few-shot prompting may be enough if examples per category are limited.
7. **LegalBench-RAG** — specifically tests precise retrieval of pinpoint citations on legal corpora; expert-annotated; covers retrieval (not just generation) which is exactly what citation quality requires.
8. (a) **Domain mismatch** — MTEB is generic; your domain has specialized vocabulary that MTEB models weren't trained on. Solution: domain-tuned embedder OR add BM25 hybrid. (b) **Test-data leakage** — your model was trained on benchmark-like data, inflating MTEB; production data is genuinely different.
9. **Tokenization edge case.** The user copy-pasted "401k" from somewhere with a hidden zero-width character — actually `4 0 1 ZWSP k`. Embeds differently from `401k`. **Fix:** Unicode normalization (NFKC + strip invisible chars) at query time. Add to ingestion too if not already done.
10. **Switch to RAG (or augment with RAG).** Fine-tuning has plateaued; further data adds 0.2% — diminishing returns indicate FT is approaching its capacity for this task. RAG can keep improving with corpus growth (more docs = more retrievable knowledge). Common pattern: keep fine-tuned model for behavior, add RAG for knowledge that needs to grow.
11. (a) **Knowledge changes** — the moment you re-train, your knowledge is stale. Re-training is slow and expensive. (b) **No citations** — fine-tuned answers can't be traced to sources. (c) **Hallucination remains** — FT compresses knowledge into weights lossy-ly. (d) **No selective updates** — can't retract a single fact without re-training. (e) **RAG is cheaper for the same knowledge volume** at scale. The right move is FT for behavior, RAG for facts.
12. (a) Different benchmarks measure different things; "MTEB" is multi-task and the average hides what matters. (b) Architects communicate trade-offs via specific evidence — saying "our reranker improves NDCG@10 on BEIR's MS-MARCO subset by 4 points" is concrete and falsifiable; "we did better on MTEB" isn't. (c) Auditors / interviewers / regulators ask precise questions; precise benchmark fluency is the answer. (d) Different stakeholders care about different aspects (eval ≠ ranking ≠ classification ≠ multilingual); fluency means picking the right one for the audience.

</details>
