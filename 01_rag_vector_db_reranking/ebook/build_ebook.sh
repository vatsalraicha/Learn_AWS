#!/usr/bin/env bash
# Build the combined ebook from the topic markdown files.
# Source files are NOT modified.
#
# Output: ebook/RAG_complete_ebook.md (combined source),
#         ebook/RAG_complete_ebook.pdf,
#         ebook/RAG_complete_ebook.epub
#
# Order respects topics/01_rag_vector_db_reranking/00_Table_Of_Contents.md
# (extraction module 12 placed before chunking module 04).

set -euo pipefail

TOPIC_DIR="$(cd "$(dirname "$0")/.." && pwd)"
EBOOK_DIR="$TOPIC_DIR/ebook"
OUT_MD="$EBOOK_DIR/RAG_complete_ebook.md"
OUT_MD_EPUB="$EBOOK_DIR/RAG_complete_ebook.epub.md"     # version with mermaid → png
OUT_PDF="$EBOOK_DIR/RAG_complete_ebook.pdf"
OUT_EPUB="$EBOOK_DIR/RAG_complete_ebook.epub"
COVER="$EBOOK_DIR/cover.png"
CSS="$EBOOK_DIR/ebook.css"
VENV_PY="/Users/vr/Code/Career_upskill/.venv/bin/python"

# Module order per 00_Table_Of_Contents.md
MODULES=(
  "01_foundations.md"
  "02_embeddings.md"
  "03_vector_databases.md"
  "12_extraction_structured_data.md"        # 04a — moved up per TOC
  "04_chunking_indexing.md"                 # 04b
  "05_retrieval_strategies.md"
  "06_reranking.md"
  "07_advanced_agentic_rag.md"
  "08_evaluation.md"
  "09_production.md"
  "10_code_metadata_routing.md"
  "11_personalization_conversational.md"
  "13a_eval_methodology_statistics.md"
  "13b_eval_online_human.md"
  "13c_eval_observability_ops.md"
  "14_grounding_citation_hallucination.md"
  "15_multilingual_long_context.md"
  "16_domain_case_studies.md"
  "17_security_privacy_auditing.md"
  "18_frontier_retrieval_patterns.md"
  "19_web_realtime_multimodal.md"
  "20_production_engineering.md"
  "21_benchmarks_tokenization_trades.md"
  "22_graphrag_deep_dive.md"
)

# ── Step 1 — Build combined markdown ─────────────────────────────────────────
echo "Building combined markdown..."

# YAML metadata block — pandoc reads this for title/author/date on cover.
cat > "$OUT_MD" <<'EOF'
---
title: "RAG, Vector Databases & Reranking"
subtitle: "A practitioner's reference for AI architects (Career_upskill — Topic 01)"
author: "Compiled for Vatsal Raicha"
date: "2026"
documentclass: report
geometry: margin=0.9in
fontsize: 11pt
linkcolor: blue
urlcolor: blue
toccolor: blue
toc: true
toc-depth: 2
numbersections: false
papersize: letter
monofont: "Menlo"
---

\newpage

# How to read this ebook

This is the consolidated reading copy of Topic 01 — RAG, Vector Databases & Reranking — from the **Career_upskill** project. The source markdown files live at `topics/01_rag_vector_db_reranking/` and remain the canonical version; this ebook is a derived artifact.

**Ordering** follows `00_Table_Of_Contents.md` — note that the extraction module (Module 12 in filename order) appears as Module 04a, before chunking (04b), because parsing source documents logically precedes deciding how to split them.

**What's included:** all 23 conceptual modules plus the `FACTS.md` appendix.
**What's NOT included:** quizzes (their collapsible answer keys don't print cleanly), code companion notebooks (those run, they don't read), the README.

**Diagrams** are written in Mermaid syntax. They render natively in GitHub, Obsidian, VS Code Markdown Preview, and Typora. In this PDF/EPUB they appear as code blocks — install a Mermaid pandoc filter if you want them rendered to images (see `build_ebook.sh`).

\newpage

EOF

# Append each module with a page break between them
for mod in "${MODULES[@]}"; do
  if [[ ! -f "$TOPIC_DIR/$mod" ]]; then
    echo "WARN: missing $mod" >&2
    continue
  fi
  echo "  + $mod"
  echo "" >> "$OUT_MD"
  echo "\\newpage" >> "$OUT_MD"
  echo "" >> "$OUT_MD"
  cat "$TOPIC_DIR/$mod" >> "$OUT_MD"
  echo "" >> "$OUT_MD"
done

# Appendix: FACTS.md
echo "" >> "$OUT_MD"
echo "\\newpage" >> "$OUT_MD"
echo "" >> "$OUT_MD"
echo "# Appendix — FACTS.md" >> "$OUT_MD"
echo "" >> "$OUT_MD"
echo "_Atomic, citable facts. Numbers, model names, benchmark scores. Source of truth for every claim in the chapters above._" >> "$OUT_MD"
echo "" >> "$OUT_MD"
cat "$TOPIC_DIR/FACTS.md" >> "$OUT_MD"

echo "Combined markdown: $OUT_MD ($(wc -l < "$OUT_MD") lines)"

# ── Step 2 — Convert to PDF ──────────────────────────────────────────────────
echo ""
echo "Building PDF (this takes ~30-60s)..."

# Mermaid blocks → code blocks (pandoc default behavior, no filter).
# Use xelatex so we get Unicode + nicer fonts.
pandoc "$OUT_MD" \
  -o "$OUT_PDF" \
  --pdf-engine=xelatex \
  --toc \
  --toc-depth=2 \
  --no-highlight \
  -V colorlinks=true \
  -V linestretch=1.15 \
  -V geometry:margin=0.85in \
  2>&1 | grep -vE "Missing character|font Helvetica" | tail -10 || {
    echo "WARN: PDF build failed. Combined markdown is still at $OUT_MD" >&2
}

# ── Step 3 — Build a proper EPUB ─────────────────────────────────────────────
# Steps: (a) pre-render mermaid → PNG, (b) generate cover, (c) pandoc with CSS + cover.
echo ""
echo "Building EPUB (the real reflowable ebook)..."

# (a) Pre-render mermaid blocks → PNG, replace with image references
if command -v mmdc >/dev/null 2>&1; then
  echo "  • Pre-rendering mermaid diagrams via mmdc..."
  "$VENV_PY" "$EBOOK_DIR/preprocess_mermaid.py" "$OUT_MD" "$OUT_MD_EPUB"
else
  echo "  • mmdc not found; mermaid blocks will appear as code blocks. Install with: npm install -g @mermaid-js/mermaid-cli" >&2
  cp "$OUT_MD" "$OUT_MD_EPUB"
fi

# (b) Generate cover image
if [[ ! -f "$COVER" ]] || [[ "$EBOOK_DIR/make_cover.py" -nt "$COVER" ]]; then
  echo "  • Generating cover image..."
  "$VENV_PY" "$EBOOK_DIR/make_cover.py" "$COVER"
fi

# (c) Write metadata to a temp file (cleaner than process substitution + line continuation)
META_FILE="$EBOOK_DIR/.epub_metadata.yaml"
cat > "$META_FILE" <<'META'
---
title: "RAG, Vector Databases & Reranking"
subtitle: "A practitioner's reference for AI architects"
creator:
  - role: author
    text: "Compiled for Vatsal Raicha"
publisher: "Career_upskill"
date: "2026"
lang: "en-US"
identifier: "career_upskill_topic_01_2026"
description: "Complete practitioner's guide covering RAG foundations through frontier patterns — embeddings, vector databases, hybrid retrieval, reranking, agentic RAG, evaluation methodology, production engineering, and domain case studies."
subject:
  - "Information Retrieval"
  - "Machine Learning"
  - "Large Language Models"
  - "Retrieval-Augmented Generation"
rights: "© 2026 Vatsal Raicha. For personal use."
---
META

# (d) Build the EPUB3 with cover + CSS + metadata
echo "  • Building EPUB3 with cover + CSS..."
pandoc "$OUT_MD_EPUB" \
  -o "$OUT_EPUB" \
  --toc \
  --toc-depth=2 \
  --split-level=1 \
  --css="$CSS" \
  --epub-cover-image="$COVER" \
  --metadata-file="$META_FILE" \
  --resource-path="$EBOOK_DIR" \
  2>&1 | tail -10

rm -f "$META_FILE"

# ── Summary ──────────────────────────────────────────────────────────────────
echo ""
echo "─── Built ───"
ls -la "$OUT_MD" "$OUT_PDF" "$OUT_EPUB" 2>&1 | grep -v "No such" || true
