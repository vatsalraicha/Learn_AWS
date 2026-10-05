# Quiz — Module 10 (Code Retrieval, Metadata & Routing)

## Recall

1. Name two code-specialized embedding models (early 2026) and one benchmark each scored well on.
2. What does "AST-based chunking" mean, and what tool is the de-facto standard for it across languages?
3. List four mechanical metadata fields and three LLM-enriched metadata fields you'd typically store.
4. What's the "single-call enrichment" pattern?

## Apply

5. You're building RAG over a corpus that's 60% code and 40% prose. What's your embedder strategy?
6. A user asks: "give me a sample of the CLAUDE.md file." Two architectures could handle this — describe both, and say which you'd pick if you control the filesystem.
7. Your RAG product gets these queries: (a) "find the `Customer.refund_amount` field", (b) "explain how refunds work", (c) "list all customers with refunds > $1000 in 2024." Map each to the right retrieval tool.

## Diagnose

8. Your code RAG retrieves the right *concepts* but wrong *files* — e.g., user asks about authentication, you return the docs/auth-overview.md but not the actual `auth.py` implementation. What's likely wrong?
9. After adding LLM-enriched metadata, retrieval got worse on "what's our cancellation policy" type queries. Hypothesis?

## Defend

10. Cursor and Claude Code primarily use grep and AST tools, not vector search, for code. Defend that choice.
11. You're going to argue for spending $200 on a one-time LLM-enrichment pass over your 100K-chunk corpus. Make the case to a skeptical manager in three bullet points.

---

## Answer key

<details>
<summary>Click to reveal</summary>

1. **`voyage-code-3`** — SOTA on CodeSearchNet, +5-8 NDCG over text-embedding-3-large on code. **Qwen3-Embedding-8B** — tops MTEB-Code. **Gemini Embedding 2** — MTEB Code ~84.0. (Any two of these.)
2. Parse the source code into an Abstract Syntax Tree, then chunk along syntactic boundaries (functions, classes, top-level blocks) instead of by character or token count. **tree-sitter** is the de-facto multi-language parser; used by GitHub, Cursor, Sourcegraph.
3. Mechanical: `chunk_id`, `doc_id`, `filename`, `file_path`, `section_path`, `page`, `language`, `last_modified` (any 4). LLM-enriched: `summary`, `entities`, `topics`, `intent_categories`, `suggested_queries`, `contains_pii` (any 3).
4. Instead of N LLM calls per chunk (one per metadata field), you make ONE LLM call that returns a structured JSON containing all fields. Combined with prompt caching, this turns enrichment from cost-prohibitive to affordable ($50-200 for a 100K-chunk corpus).
5. Either use a strong all-rounder that tops both general and code benchmarks (**Gemini Embedding 2** or **Qwen3-Embedding**), OR run two indices — code with `voyage-code-3`, prose with a generic embedder — and route at query time. Two-index gives best quality, one-embedder gives operational simplicity.
6. **Architecture A — function-calling router:** LLM sees the query and a `read_file(name)` tool; emits `read_file(name="CLAUDE.md")`; you serve the file directly. **Architecture B — self-querying retriever:** parse `filename = "CLAUDE.md"` as a metadata filter, vector-search over chunks of that file. If you control the filesystem, **A is simpler, faster, and zero-hallucination** — pick it.
7. (a) **grep / LSP** — exact symbol lookup. (b) **Vector search** with code embedder — concept query. (c) **SQL** — structured query against the orders table.
8. Likely embedder choice. Generic embedders see code only as text; they retrieve "documents about authentication" rather than implementations. Switch to `voyage-code-3` or `Qwen3-Embedding`. Also: AST-based chunking, so each chunk's "type=code/doc" is in metadata for filtering or reranking.
9. The summary embedding may be drifting the retriever toward summary matches over chunk-content matches — and your summaries are paraphrasing in a way that loses the literal phrasing in the policy. Either: (a) keep both vectors but rerank chunk-text matches above summary-only matches, or (b) tune the enrichment prompt to preserve key phrases verbatim in summaries.
10. (a) Identifiers are exact tokens — grep returns the literal answer, vector search guesses. (b) No index staleness — grep reads the working copy. (c) Refactors / renames don't invalidate grep; they break vector indexes silently. (d) Free, composable, fast. Vector search still earns its keep on conceptual queries; the smart move is hybrid routing, not picking a side.
11. (a) **Amortizes per query.** A 100K-chunk corpus serves millions of queries; $200 once becomes a fraction of a cent per query. (b) **Unlocks filtering** — without metadata you can't honor "Q4 2024," "internal-only," or "policies vs emails" — and most real user queries have implicit filters like those. (c) **Reranker signal** — even when filters don't apply, entity/topic/summary fields measurably improve reranking quality. The alternative is shipping a worse product to save coffee money.

</details>
