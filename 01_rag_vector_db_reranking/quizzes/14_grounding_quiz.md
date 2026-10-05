# Quiz — Module 14 (Grounding, Citation & Hallucination)

## Recall

1. Distinguish: grounding, faithfulness, citation, factuality.
2. What's the difference between intrinsic and extrinsic hallucinations?
3. Name three citation strategies, ranked by trust level.
4. What's a "citation hallucination" and what % rate is reported in long-form RAG?
5. Name the canonical citation benchmark and its successor.

## Apply

6. You're shipping a medical RAG product. What grounding level do you require, and why?
7. Outline a 4-signal abstention/refusal policy.
8. Pick a hallucination detection approach for: (a) low-stakes chatbot at scale, (b) high-stakes financial advice with 500ms latency budget.

## Diagnose

9. Faithfulness is 0.95 but ALCE-style citation precision is 0.55. What's likely happening?
10. After enabling RAG on a corpus you previously skipped, hallucination rate went UP. Plausible cause?

## Defend

11. Argue why GTR (generate-then-retrieve) citation is structurally unsuitable for regulated domains.
12. Defend "claim-level grounding > document-level citation" with an ALCE finding.

---

## Answer key

<details>
<summary>Click to reveal</summary>

1. **Grounding** — output anchored in retrieved evidence. **Faithfulness** — output's claims don't contradict retrieved context. **Citation** — each claim linked to specific supporting span. **Factuality** — output consistent with reality (regardless of context).
2. **Intrinsic** contradicts the input/context (checkable against retrieved chunks). **Extrinsic** is unverifiable from input/context (model invented it; harder to detect).
3. (1) Document-level — weakest. (2) Inline span — Perplexity/Bing/Claude pattern. (3) Claim-level grounding — gold standard for regulated domains.
4. The model emits a citation that looks valid but points at the wrong span (or doesn't exist). FACTUM (2026) found ~3-15% of citations in long-form RAG are hallucinated even when underlying facts are correct. Mitigation: server-side validation — extract cited span, run NLI on (claim, span), reject if not entailed.
5. **ALCE** (EMNLP 2023). Successor: **GaRAGe** (June 2025) — 2,366 questions, 35K+ annotated grounding passages, more rigorous.
6. **Claim-level grounding plus authority-source check.** Reasons: (a) FDA / HIPAA traceability, (b) liability exposure, (c) some claims need authoritative source (peer-reviewed, internal policy) — random forum post citations are unacceptable. Combine claim-level citation + retrieval restricted to authority-tier sources.
7. (a) max retrieved cosine < threshold; (b) reranker top score < threshold; (c) faithfulness mid-stream check < threshold; (d) hallucination detector (Lynx/HHEM) score > threshold. Combine into "any signal trips" → refuse with closest chunks as fallback.
8. (a) Low-stakes, high-volume: NLI (HHEM-2.1-Open or DeBERTa-NLI) async, ~40ms/pair, ~free. (b) Financial high-stakes 500ms: NLI sync gate (~100ms) + Patronus Lynx-8B sync gate (~200ms) + citation validation (~50ms). Reject if any flag. Self-consistency stays out due to latency.
9. The model is generating answers that don't contradict the context (faithfulness OK) but cites the wrong span for them. Likely GTR-style post-hoc citation, OR inline citation drift during generation. Validate every citation against an NLI check on (claim, cited span).
10. The "RAG paradoxically increases hallucinations" finding. Causes: (a) distractor chunks invite confabulated connections; (b) conflicting chunks force a confident pick; (c) "answer using only the provided context" prompt forces fabricated support rather than refusal. Mitigation: refusal-aware generation (CRAG, Self-RAG, abstention triggers).
11. GTR generates the answer first, then tries to find supporting spans. Structural issues: (a) the model isn't constrained to retrieved content during generation, so it can drift; (b) post-hoc support is cherry-picked rather than guiding generation; (c) misattribution rate is high — span content may not actually entail the claim. For regulated domains where attribution is the audit trail, this is unacceptable. Inline citation generation, validated by a parser that guarantees pointer validity (Anthropic-style), is the only architecture safe for that bar.
12. ALCE follow-up showed fine-tuning Llama-2-7B to emit **line-level citations rather than document-level** boosted precision by **>14 percentage points**. Reasoning: granularity matters. Document-level lets the model "cite somewhere in this 50-page doc" — un-checkable. Line-level forces specificity — auditable, debugger-friendly, less room to fabricate.

</details>
