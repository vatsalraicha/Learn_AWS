# Quiz — Module 4 (Chunking & Indexing)

## Recall

1. What's the typical "default" chunk size and overlap?
2. Define "semantic chunking" in one sentence.
3. What two sub-techniques compose Anthropic's Contextual Retrieval?
4. How does late chunking differ from naïve chunking? (Order of operations.)
5. What is the "context cliff," and at what input size does it typically appear?

## Apply

6. You're building RAG over Markdown documentation with `#` headers. What's a free win that many teams miss?
7. You have an 8K-context embedder and a corpus of long, dense legal documents. Late chunking is available. Defend or refuse the choice.
8. Anthropic Contextual Retrieval costs an LLM call per chunk at indexing time. What makes this affordable in practice?

## Diagnose

9. Your retrieval is fine for explicit-keyword queries but fails on cross-paragraph references ("the policy mentioned earlier"). Which chunking technique most directly addresses this?
10. After switching from fixed-size to semantic chunking, retrieval quality on a 4000-token-doc corpus barely changed but cost rose. Why?

## Defend

11. "Bigger chunks = more context = better retrieval." Argue against this.
12. Multi-representation indexing seems redundant — you're storing summaries AND full chunks. Defend the design.

---

## Answer key

<details>
<summary>Click to reveal</summary>

1. 400-512 tokens with 10-20% overlap. NVIDIA found 15% optimal at 1024 tokens on FinanceBench.
2. Split text where the embedding-distance between adjacent sentences crosses a threshold — cut at semantic shifts, not fixed offsets.
3. **Contextual Embeddings** (prepend an LLM-generated context summary to each chunk before embedding) and **Contextual BM25** (also index the contextualized text into BM25). Combined: 49% retrieval-failure reduction; with reranker, 67%.
4. Naïve: chunk first, then embed each chunk independently. Late: embed the *whole document* with a long-context encoder, then mean-pool token-level vectors over chunk spans. Late chunking preserves cross-chunk context in each chunk's vector.
5. The point at which LLM answer quality degrades non-linearly with input size. Roughly ~2500 tokens; steepens above 32K.
6. Include the header path in the chunk text before embedding (e.g., `[Refund Policy > Cancellation] ...`). Free recall lift.
7. Defend: long docs benefit most from late chunking — cross-chunk context is exactly what's lost in naïve chunking, and the long-context embedder lets you recover it without LLM cost. Solid choice.
8. Prompt caching: cache the document tokens once, vary only the chunk in the prompt. The LLM provider charges full price the first time and cached-rate (10x cheaper) thereafter. Anthropic's own caching makes this near-free in practice.
9. **Contextual Retrieval** (or late chunking). The chunk needs to carry context that disambiguates "the policy mentioned earlier."
10. The "context cliff" study found that for docs < 5000 tokens, sentence chunking matched semantic chunking. The lift from semantic chunking is small there, the cost is real (200-300 embedding calls per doc just for chunking).
11. Larger chunks dilute the embedding — the per-token semantic signal gets averaged out. The phrase you care about may be 1% of the vector. Smaller chunks have sharper embeddings and higher precision; the loss is *context*, which is what Contextual Retrieval / late chunking are designed to reintroduce.
12. Indexing summaries gives you sharp, keyword-rich vectors that retrieve precisely. Returning the full chunk to the LLM gives the model the actual evidence to ground answers in. The two roles want different things — the embedder wants the gist; the LLM wants the detail.

</details>
