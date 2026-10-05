# Ebook — RAG, Vector Databases & Reranking

A proper reflowable **EPUB3** ebook, plus a print-style PDF and the combined source markdown.
Built from the modules in `topics/01_rag_vector_db_reranking/` — source files are not modified.

## Files

| File | Size | Format | Best for |
|------|------|--------|----------|
| **`RAG_complete_ebook.epub`** | ~4.7 MB | **EPUB3 with cover, CSS, rendered diagrams** | **Apple Books, Kindle (via Calibre), Calibre Viewer, mobile** |
| `RAG_complete_ebook.pdf` | ~660 KB, 209 pages | PDF | Print, archival, desktop reading |
| `RAG_complete_ebook.md` | ~340 KB | Combined markdown | GitHub / Obsidian / VS Code (mermaid renders natively) |
| `cover.png` | ~180 KB | PNG, 1600×2560 | EPUB cover (auto-generated) |
| `ebook.css` | — | CSS | Typography for EPUB |
| `build_ebook.sh` | — | bash | Regenerate everything |
| `preprocess_mermaid.py` | — | python | Pre-render mermaid blocks to PNG |
| `make_cover.py` | — | python | Generate the cover image |
| `mermaid_images/` | — | dir | Rendered diagram PNGs |

## What makes this a real ebook (not just a PDF)

The EPUB is properly authored:

- **Reflowable text** — adjusts to your e-reader's font size, screen size, orientation.
- **30 chapters** with hard page breaks at each `# Module N` heading.
- **Embedded TOC + navigation document** (EPUB3 `nav.xhtml`) — works in every reader.
- **Cover image** auto-generated from the module list.
- **Custom CSS** for readable typography:
  - Serif for body (Charter / Georgia / Iowan Old Style fallback chain).
  - Sans-serif for headings (Avenir Next / Helvetica Neue / Arial).
  - Mono for code (Menlo / Consolas).
  - Hyphenation enabled; widows/orphans controlled; tables and code blocks marked `page-break-inside: avoid`.
- **119 of 122 mermaid diagrams pre-rendered to PNG** (via `mmdc` CLI) and embedded. The other 3 have source syntax that mmdc rejects; they fall back to code blocks in the ebook (kept readable).
- **Full metadata** (title, subtitle, author, publisher, date, language, ISBN-like identifier, subject tags, description, rights) — drives the ebook's library entry on Apple Books / Calibre / Kindle.

## Order (per `00_Table_Of_Contents.md`)

Extraction (file `12_extraction_structured_data.md`) appears as Module 04a, before chunking (file `04_chunking_indexing.md`) as Module 04b — because parsing source documents logically precedes deciding how to split them.

Full reading order:

```
01 Foundations
02 Embeddings
03 Vector Databases
04a Extraction & Structured Data       (file 12)
04b Chunking & Indexing                (file 04)
05 Retrieval Strategies
06 Reranking
07 Advanced & Agentic RAG
08 Evaluation (high level)
09 Production
10 Code Retrieval, Metadata & Routing
11 Personalization & Conversational
13a Eval Methodology & Statistics
13b Eval Online & Human
13c Eval Observability & Operations
14 Grounding, Citation & Hallucination
15 Multilingual & Long-Context
16 Domain Case Studies
17 Security, Privacy & Auditing
18 Frontier Retrieval Patterns
19 Web, Real-time & Multimodal
20 Production Engineering
21 Benchmarks, Tokenization & Trade Studies

Appendix: FACTS.md
```

## What's NOT in the ebook

- Quizzes (`quizzes/*.md`) — answer keys are collapsible `<details>` blocks; not ideal in print.
- Code companion notebooks (`code/*.py`) — meant to run, not read.
- Top-level README.

These remain in their source directories. If you want them included, edit `build_ebook.sh`.

## How to open

**Apple Books** (macOS / iPad / iPhone): double-click the `.epub` or drag into Books.
**Calibre**: open Calibre → Add Books → select the `.epub`. Calibre also previews / converts to Kindle (AZW3, MOBI).
**Kindle**: send the `.epub` to your Kindle email address (Amazon converts), or convert to AZW3 via Calibre first.
**Mobile**: AirDrop / email the `.epub` to your phone, open in Apple Books or any EPUB reader.

## Rebuilding

```bash
cd /Users/vr/Code/Career_upskill
bash topics/01_rag_vector_db_reranking/ebook/build_ebook.sh
```

Takes ~2-3 minutes (mermaid rendering takes most of it; subsequent runs are faster because diagrams are content-hashed and cached).

## Toolchain used

- **pandoc** 3.9 — markdown → EPUB3 / PDF
- **mmdc** (`@mermaid-js/mermaid-cli`) — render mermaid → PNG
- **xelatex** (MacTeX) — PDF engine
- **Pillow** (in `.venv`) — cover image generation

## Mermaid render coverage

- Found: **122** diagrams across the modules
- Rendered to PNG and embedded: **122** ✅ (full coverage)

To achieve full coverage, three source files received small syntax fixes (semantic no-ops — the rendered diagrams look the same):

| File | Change | Reason |
|------|--------|--------|
| `07_advanced_agentic_rag.md` | `{Need to retrieve?<br/>"Retrieve" token}` → `{"Need to retrieve?<br/>'Retrieve' token"}` (and similar for `IsRel`, `IsSup`) | Mermaid rhombus nodes containing `<br/>` AND nested double-quotes need the whole label wrapped in quotes |
| `13b_eval_online_human.md` | `"Tell me about [made-up entity]"` → `Tell me about a made-up entity` | In mindmap syntax, `[...]` triggers shape parsing; quotes don't escape it |
| `18_frontier_retrieval_patterns.md` | `T1[Call retrieve(q1)]` → `T1["Call retrieve(q1)"]` | Square-bracket node labels with unescaped parens need quoting |

These same fixes would be required for any mermaid renderer (`mermaid-cli` / `mmdc`, `mermaid-filter`, mermaid.live, etc.) — they all share one parser.

## Alternative renderer: mermaid-filter

`mermaid-filter` is installed globally (`npm install -g mermaid-filter`) as a pandoc-filter approach if you prefer that workflow. It wraps `mermaid-cli` under the hood — slower than the current pre-render approach (because it runs Chromium via Puppeteer per call) but it's the standard pandoc convention.

To switch the build to it: in `build_ebook.sh`, replace the `preprocess_mermaid.py` step with `--filter=mermaid-filter` on the pandoc invocation. Current default is the faster pre-render approach.
