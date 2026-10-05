# Quiz — Module 15 (Multilingual & Long-Context Failures)

## Recall

1. Three architectural patterns for multilingual retrieval — name and one cost each.
2. Name the open-source embedder that supports 100+ languages with dense + sparse + multi-vector in one model. What's its MIRACL average?
3. What is the U-shaped curve from "Lost in the Middle"?
4. Cite the NoLiMa finding for GPT-4o at 1K vs 32K tokens.
5. What's the serial-position effect in psychology and why is it relevant to LLMs?

## Apply

6. You retrieve 20 chunks ordered by reranker score for a long-context model. What's the cheap reordering trick that often lifts quality 5-10%?
7. You're starting a RAG product for US healthcare with English + Spanish + Mandarin + Vietnamese as user-facing requirements. What's your embedder strategy?
8. You have a 200K-token corpus in mixed English + French. Long-context model with 200K window vs RAG — which would you start with and what would you measure?

## Diagnose

9. Your multilingual RAG benchmarks at recall@10 = 0.85 globally but Spanish queries average 0.72. Most likely cause and fix?
10. Top-1 reranked chunk is provably correct, but the answer ignores it. Position in prompt: 10th of 20. Diagnose.

## Defend

11. Argue why "supports 1M tokens" overstates real-world capability. Cite a specific number.
12. Defend running per-language SLOs over a single global retrieval SLO.

---

## Answer key

<details>
<summary>Click to reveal</summary>

1. **Translation-as-bridge:** translate query to corpus language. Cost: translation errors compound, slower. **Native cross-lingual embeddings:** one model, shared space. Cost: quality varies by language pair. **Per-language indexes:** one embedder per language, route at query time. Cost: operational overhead.
2. **BGE-M3.** MIRACL average ~70.0 nDCG@10 across 18 languages.
3. Performance is highest when relevant info is at the **start or end** of the context, lowest in the **middle.** Discovered in Liu et al. 2023.
4. GPT-4o achieves **99.3% accuracy at 1K tokens** and drops to **69.7% at 32K tokens** on NoLiMa (which forces semantic rather than literal matching).
5. Humans best recall items at the start and end of a list (free-recall task). Discovered Ebbinghaus 1913 / Murdock 1962. LLMs show the same pattern — likely inherited from training-data structure and architectural priors. Lost-in-the-middle is the LLM analog.
6. Reorder so top-1 is at position 1, top-2 at last, top-3 at position 2, top-4 at penultimate, etc. Exploit the U-curve instead of fighting it. Costs zero compute; routinely lifts answer quality 5-10%.
7. Single multilingual embedder for the four core languages — **BGE-M3 (open) or Cohere multilingual-v3 (API).** Test per-language quality on representative eval sets. For long-tail languages where quality lags, add per-language tuning or fall back to translation-as-bridge. Track per-language SLOs separately.
8. Start with RAG. Reasoning: even Gemini-class long-context degrades non-linearly past 32K (Context Rot); non-English compounds the degradation. RAG focuses ~30K relevant tokens which the model uses well. Measure: end-to-end faithfulness + recall@k per language; compare to long-context-only baseline as A/B.
9. Likely the embedder's English bias — multilingual embedders consistently score 10-30 points higher on English than non-English. Fixes: (a) per-language fine-tuning of the embedder on Spanish data; (b) hybrid Spanish-BM25 + dense; (c) per-language top-k tuning (more chunks for Spanish to compensate for lower precision).
10. Lost-in-the-middle. Position 10 of 20 is in the middle of the U-curve, where attention is weakest. Fix: reorder to put top-1 at position 1 (or at the end), AND/OR shrink top-k to 5-7 chunks where the U-curve is shallower.
11. Single-needle NIAH at 1M tokens hits >99% on Gemini, suggesting "supports 1M." But NoLiMa's harder semantic-matching test shows GPT-4o drops 99.3% → 69.7% at just 32K. Multi-needle scores trail single-needle by 15-40 points across all frontier models. Production queries are usually multi-needle and semantic, not single-needle and literal. The advertised number reflects the easiest possible test.
12. Multilingual embedders score 10-30 points higher on English than non-English. A global "recall@10 > 0.85" SLO is met by being great on English while non-English silently underperforms. Per-language SLOs surface this gap, drive targeted improvements (per-language fine-tune, per-language top-k tuning, language-specific reranker), and prevent the global metric from masking real user-facing quality gaps.

</details>
