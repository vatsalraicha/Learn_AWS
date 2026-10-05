#!/usr/bin/env bash
# Build the combined ebook for Databricks Certified Generative AI Engineer Associate.
# Source files are NOT modified.
set -euo pipefail

TOPIC_DIR="$(cd "$(dirname "$0")/.." && pwd)"
EBOOK_DIR="$TOPIC_DIR/ebook"
OUT_MD="$EBOOK_DIR/Databricks_GenAI_Associate_complete_ebook.md"
OUT_MD_EPUB="$EBOOK_DIR/Databricks_GenAI_Associate_complete_ebook.epub.md"
OUT_PDF="$EBOOK_DIR/Databricks_GenAI_Associate_complete_ebook.pdf"
OUT_EPUB="$EBOOK_DIR/Databricks_GenAI_Associate_complete_ebook.epub"
COVER="$EBOOK_DIR/cover.png"
CSS="$EBOOK_DIR/ebook.css"
VENV_PY="/Users/vr/Code/Career_upskill/.venv/bin/python"

MODULES=(
  "01_genai_use_case_design.md"
  "02_model_selection.md"
  "03_chunking_strategies.md"
  "04_embeddings_indexing.md"
  "05_prompt_engineering.md"
  "06_mosaic_ai_vector_search.md"
  "07_rag_chains.md"
  "08_agent_framework.md"
  "09_agent_bricks.md"
  "10_model_serving_endpoints.md"
  "11_ci_cd_for_agents.md"
  "12_databricks_apps_as_ui.md"
  "13_governance_guardrails.md"
  "14_genai_evaluation.md"
  "15_production_monitoring.md"
)

QUIZZES=(
  "01_design.md"
  "02_data_prep.md"
  "03_app_development.md"
  "04_assemble_deploy.md"
  "05_governance.md"
  "06_evaluation_monitoring.md"
)

# ── Step 1 — Build combined markdown ─────────────────────────────────────────
echo "Building combined markdown..."

cat > "$OUT_MD" <<'EOF'
---
title: "Databricks Certified Generative AI Engineer Associate"
subtitle: "Build production GenAI on Databricks (Career_upskill — Topic 10)"
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

This is the consolidated reading copy of **Topic 10 — Databricks Certified Generative AI Engineer Associate**, from the **Career_upskill** project. The source markdown files live at `topics/10_databricks_genai_associate/` and remain the canonical version; this ebook is a derived artifact.

**Ordering** is the natural numeric sequence — README, then numbered modules, then FACTS, then quizzes.

**What's included:**
- README (study plan, scope, exam logistics)
- All numbered modules
- The FACTS.md appendix (citable facts, version cutoffs, exam metadata)
- Quizzes (~3× exam length, with answer explanations)

**Diagrams** are Mermaid where present. The EPUB build pre-renders them to PNG via the `mmdc` CLI; if unavailable they appear as code blocks.

\newpage

EOF

# README first
echo "  + README.md"
echo "" >> "$OUT_MD"
echo "\\newpage" >> "$OUT_MD"
echo "" >> "$OUT_MD"
cat "$TOPIC_DIR/README.md" >> "$OUT_MD"
echo "" >> "$OUT_MD"

# Then each module in order
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

# Appendix A: FACTS.md
echo "  + FACTS.md (appendix)"
echo "" >> "$OUT_MD"
echo "\\newpage" >> "$OUT_MD"
echo "" >> "$OUT_MD"
echo "# Appendix A — FACTS" >> "$OUT_MD"
echo "" >> "$OUT_MD"
echo "_Atomic, citable facts. Single source of truth for dates, versions, deprecations, exam metadata._" >> "$OUT_MD"
echo "" >> "$OUT_MD"
cat "$TOPIC_DIR/FACTS.md" >> "$OUT_MD"

# Appendix B: quizzes
echo "" >> "$OUT_MD"
echo "\\newpage" >> "$OUT_MD"
echo "" >> "$OUT_MD"
echo "# Appendix B — Quizzes" >> "$OUT_MD"
echo "" >> "$OUT_MD"

for quiz in "${QUIZZES[@]}"; do
  if [[ ! -f "$TOPIC_DIR/quizzes/$quiz" ]]; then
    echo "WARN: missing quiz $quiz" >&2
    continue
  fi
  echo "  + quizzes/$quiz"
  echo "" >> "$OUT_MD"
  echo "\\newpage" >> "$OUT_MD"
  echo "" >> "$OUT_MD"
  cat "$TOPIC_DIR/quizzes/$quiz" >> "$OUT_MD"
  echo "" >> "$OUT_MD"
done

echo "Combined markdown: $OUT_MD ($(wc -l < "$OUT_MD") lines)"

# ── Step 2 — Convert to PDF (optional) ───────────────────────────────────────
echo ""
echo "Attempting PDF (optional — skipped if no LaTeX engine)..."
if false; then  # PDF disabled - LaTeX deps incomplete on this system
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
      echo "WARN: PDF build failed — continuing without PDF." >&2
  }
else
  echo "  • xelatex not found — skipping PDF (EPUB still produced)."
fi

# ── Step 3 — Build EPUB ──────────────────────────────────────────────────────
echo ""
echo "Building EPUB..."

if command -v mmdc >/dev/null 2>&1; then
  echo "  • Pre-rendering mermaid diagrams via mmdc..."
  "$VENV_PY" "$EBOOK_DIR/preprocess_mermaid.py" "$OUT_MD" "$OUT_MD_EPUB" || cp "$OUT_MD" "$OUT_MD_EPUB"
else
  echo "  • mmdc not found; mermaid blocks will appear as code blocks." >&2
  cp "$OUT_MD" "$OUT_MD_EPUB"
fi

if [[ ! -f "$COVER" ]] || [[ "$EBOOK_DIR/make_cover.py" -nt "$COVER" ]]; then
  echo "  • Generating cover image..."
  "$VENV_PY" "$EBOOK_DIR/make_cover.py" "$COVER"
fi

META_FILE="$EBOOK_DIR/.epub_metadata.yaml"
cat > "$META_FILE" <<'META'
---
title: "Databricks Certified Generative AI Engineer Associate"
subtitle: "Build production GenAI on Databricks"
creator:
  - role: author
    text: "Compiled for Vatsal Raicha"
publisher: "Career_upskill"
date: "2026"
lang: "en-US"
identifier: "career_upskill_topic_10_2026"
description: "Complete study reference for the Databricks Certified Generative AI Engineer Associate exam — modules, FACTS appendix, and quizzes (~3x exam length), with answer explanations and look-alike API traps. Career_upskill Topic 10."
subject:
  - "Databricks"
  - "Certification"
  - "Machine Learning"
  - "Data Engineering"
  - "Apache Spark"
rights: "© 2026 Vatsal Raicha. For personal use."
---
META

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

echo ""
echo "─── Built ───"
ls -la "$OUT_MD" "$OUT_EPUB" 2>&1 | grep -v "No such" || true
[[ -f "$OUT_PDF" ]] && ls -la "$OUT_PDF"
