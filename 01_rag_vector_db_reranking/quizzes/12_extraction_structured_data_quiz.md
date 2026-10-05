# Quiz — Module 12 (Extraction & Structured Data RAG)

## Recall

1. Name three production document parsers (early 2026) and one differentiator each.
2. What's the difference between OCR-based extraction and VLM-based extraction?
3. What's the typical text-to-SQL RAG pattern? What gets embedded, what doesn't?
4. Name two multimodal embedding models (early 2026).

## Apply

5. Your corpus is mostly two-column scientific PDFs with embedded tables. Which parser would you start with and why?
6. A user has a CSV with 500K rows of orders. They ask: "What's the average order size for Texas customers in 2024?" Walk through the architecture that handles this well.
7. A 30-slide PowerPoint has critical content in charts on 8 slides. Outline an indexing strategy.

## Diagnose

8. RAG over PDFs returns mostly correct text but tables come out garbled into paragraphs. What's likely wrong, and what's the cheapest fix?
9. After ingesting a 1M-row Excel file as embedded JSON rows, queries about totals and averages return wrong answers. What's the architectural problem?

## Defend

10. "Just embed everything — text, tables, code, JSON. The embedder will figure it out." Argue against this in 3 specific points.
11. Defend why "the parser is more important than the embedder" for many real RAG projects.

---

## Answer key

<details>
<summary>Click to reveal</summary>

1. Any three of: **LlamaParse** (multi-column awareness, agentic mode); **Docling** (open-source, layout analysis, table recognition); **Unstructured** ("ETL for LLMs", 50+ formats, element-typing); **Mistral OCR** (VLM-based, multilingual, $0.001/page batch); **Reducto** (financial/legal accuracy); **AWS Textract / Azure DI / Google Document AI** (cloud-native, OCR + tables).
2. **OCR-based:** detect text glyphs in an image and transcribe to text. Best on plain printed text. **VLM-based:** vision-language model "reads" the page like a human, can interpret layout, tables, equations, even charts. More accurate on complex layouts; usually more expensive.
3. **Pattern:** RAG-over-schema. **Embedded:** table descriptions, column descriptions, units, example queries, glossary, business-term definitions. **NOT embedded:** the data itself. The LLM uses retrieved schema context to write SQL; SQL runs against the actual database.
4. Any two of: **Gemini Embedding 2** (text+image+video+audio+PDF, 3072-dim, MTEB 68.32), **Qwen3-VL-2B** (Apache, smaller modality gap, 0.945 cross-modal), **ColPali / ColQwen**, **CLIP / OpenCLIP**, **Voyage Multimodal 3.5**.
5. **Docling** (open-source, layout analysis + reading-order reconstruction + table structure) or **LlamaParse** (multi-column-aware, top-tier table extraction). Both handle the "two columns get interleaved" failure mode that vanilla parsers (PyMuPDF, pdfminer) blow.
6. (a) Load the CSV into a structured store (Postgres, Snowflake, DuckDB). (b) RAG-over-schema: embed table description, column descriptions, business glossary, example queries. (c) User asks the question; LLM retrieves relevant schema docs; LLM writes SQL: `SELECT AVG(amount) FROM orders WHERE state='TX' AND date BETWEEN '2024-01-01' AND '2024-12-31'`. (d) Execute, return rows + LLM's natural-language explanation. The 500K rows themselves are never embedded.
7. (a) Extract bullets, titles, speaker notes as text per slide. (b) Render each slide to an image. (c) Pass each image through a VLM to generate a caption ("This slide shows a bar chart of Q4 revenue by region, with EMEA leading at $42M..."). (d) Index both the text and the VLM caption, plus a thumbnail in metadata. (e) For chart-heavy decks, also embed slide images with a multimodal embedder or ColPali for late-interaction matching at query time.
8. The parser doesn't recognize table structure — flowing the cells into paragraphs in reading order. Cheapest fix: switch to a layout-aware parser (Docling, LlamaParse, OpenDataLoader). Treat extracted tables as their own elements, render to markdown for the LLM, and generate an LLM summary for retrieval.
9. Vector retrieval returns the closest single row, not an aggregate. Aggregations (SUM, AVG, GROUP BY) require a query engine, not nearest-neighbor search. The architectural problem: you treated structured data as documents. Fix: load to a structured store and use text-to-SQL.
10. (a) Embeddings distort numerical relationships — `amount=160.01` and `amount=159.99` aren't "similar" in vector space the way they are as numbers. (b) Aggregations are impossible — vector search returns one row at a time, not SUM/AVG. (c) Filtering on structured fields ("Texas + 2024 + > $10K") is trivial in SQL but degrades vector search performance and can return < k results.
11. (a) Garbage in, garbage out — even the best embedder can't recover meaning a parser destroyed (interleaved columns, lost tables, dropped charts). (b) The parser determines what counts as a "chunk" and what metadata it carries; both drive retrieval quality more than embedder choice. (c) Switching embedders is a one-line change; switching parsers means re-ingesting the entire corpus. The expensive thing is correct, not fancy.

</details>
