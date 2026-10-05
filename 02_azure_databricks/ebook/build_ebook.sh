#!/usr/bin/env bash
# Build Topic 02 EPUB from all 25 Azure Databricks module files.
set -euo pipefail

TOPIC_DIR="$(cd "$(dirname "$0")/.." && pwd)"
EBOOK_DIR="$TOPIC_DIR/ebook"
OUT_MD="$EBOOK_DIR/Azure_Databricks_complete_ebook.md"
OUT_EPUB="$EBOOK_DIR/Azure_Databricks_complete_ebook.epub"
COVER="$EBOOK_DIR/cover.png"
CSS="$EBOOK_DIR/ebook.css"
VENV_PY="/Users/vr/Code/Career_upskill/.venv/bin/python"

echo "==> Generating cover"
"$VENV_PY" "$EBOOK_DIR/make_cover.py" "$COVER"

echo "==> Building combined markdown"
cat > "$OUT_MD" <<'EOF'
---
title: "Azure Databricks for AI/ML Engineers"
subtitle: "Lakehouse, Unity Catalog, MLflow 3, Mosaic AI, HIPAA (Career_upskill — Topic 02)"
author: "Vatsal Raicha"
date: "May 2026"
lang: "en-US"
rights: "© 2026 Vatsal Raicha. Personal use only."
description: "25-module curriculum on Azure Databricks for a senior AI/ML engineer — Optum/healthcare lens with HIPAA + production hardening."
---

EOF

# README first
if [ -f "$TOPIC_DIR/README.md" ]; then
  cat "$TOPIC_DIR/README.md" >> "$OUT_MD"
  echo -e "\n\n\\newpage\n\n" >> "$OUT_MD"
fi

# FACTS
if [ -f "$TOPIC_DIR/FACTS.md" ]; then
  cat "$TOPIC_DIR/FACTS.md" >> "$OUT_MD"
  echo -e "\n\n\\newpage\n\n" >> "$OUT_MD"
fi

# Modules 01-25 in numeric order
for m in $(ls "$TOPIC_DIR"/[0-9][0-9]_*.md | sort); do
  echo "  + $(basename "$m")"
  echo -e "\n\n\\newpage\n\n" >> "$OUT_MD"
  cat "$m" >> "$OUT_MD"
done

# Quizzes section
echo -e "\n\n\\newpage\n\n# Module Quizzes\n\n" >> "$OUT_MD"
if [ -d "$TOPIC_DIR/quizzes" ]; then
  for q in $(ls "$TOPIC_DIR/quizzes"/*.md 2>/dev/null | sort); do
    echo "  + quiz: $(basename "$q")"
    echo -e "\n\\newpage\n" >> "$OUT_MD"
    cat "$q" >> "$OUT_MD"
  done
fi

# REVIEW.md (adversarial self-review)
if [ -f "$TOPIC_DIR/REVIEW.md" ]; then
  echo -e "\n\n\\newpage\n\n" >> "$OUT_MD"
  cat "$TOPIC_DIR/REVIEW.md" >> "$OUT_MD"
fi

echo "==> Combined markdown: $(wc -l < "$OUT_MD") lines, $(wc -c < "$OUT_MD") bytes"

echo "==> Building EPUB"
pandoc "$OUT_MD" \
  -o "$OUT_EPUB" \
  --toc --toc-depth=2 \
  --epub-cover-image="$COVER" \
  --css="$CSS" \
  --metadata title="Azure Databricks for AI/ML Engineers" \
  --metadata author="Vatsal Raicha"

echo "==> EPUB: $OUT_EPUB ($(du -h "$OUT_EPUB" | cut -f1))"
echo "==> Done."
