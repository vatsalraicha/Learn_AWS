#!/usr/bin/env bash
# Build Topic 03 EPUB from all 34 Recommendation Engines module files.
set -euo pipefail

TOPIC_DIR="$(cd "$(dirname "$0")/.." && pwd)"
EBOOK_DIR="$TOPIC_DIR/ebook"
OUT_MD="$EBOOK_DIR/Recommendation_Engines_complete_ebook.md"
OUT_EPUB="$EBOOK_DIR/Recommendation_Engines_complete_ebook.epub"
COVER="$EBOOK_DIR/cover.png"
CSS="$EBOOK_DIR/ebook.css"
VENV_PY="/Users/vr/Code/Career_upskill/.venv/bin/python"

echo "==> Generating cover"
"$VENV_PY" "$EBOOK_DIR/make_cover.py" "$COVER"

echo "==> Building combined markdown"
cat > "$OUT_MD" <<'EOF'
---
title: "Recommendation Engines & Ads"
subtitle: "Classical to LLM recsys, ads ecosystem, A/B testing (Career_upskill — Topic 03)"
author: "Vatsal Raicha"
date: "May 2026"
lang: "en-US"
rights: "© 2026 Vatsal Raicha. Personal use only."
description: "34-module curriculum on recommendation engines and ads — foundations through industry deep dives (Netflix, Meta, TikTok, Google) and full ads ecosystem."
---

EOF

# README + TOC + FACTS
for header in README.md 00_Table_Of_Contents.md FACTS.md; do
  if [ -f "$TOPIC_DIR/$header" ]; then
    cat "$TOPIC_DIR/$header" >> "$OUT_MD"
    echo -e "\n\n\\newpage\n\n" >> "$OUT_MD"
  fi
done

# Modules 01-34
for m in $(ls "$TOPIC_DIR"/[0-9][0-9]_*.md | grep -v "00_Table_Of_Contents" | sort); do
  echo "  + $(basename "$m")"
  echo -e "\n\n\\newpage\n\n" >> "$OUT_MD"
  cat "$m" >> "$OUT_MD"
done

# Quizzes
echo -e "\n\n\\newpage\n\n# Grouped Quizzes\n\n" >> "$OUT_MD"
if [ -d "$TOPIC_DIR/quizzes" ]; then
  for q in $(ls "$TOPIC_DIR/quizzes"/*.md 2>/dev/null | sort); do
    echo "  + quiz: $(basename "$q")"
    echo -e "\n\\newpage\n" >> "$OUT_MD"
    cat "$q" >> "$OUT_MD"
  done
fi

echo "==> Combined markdown: $(wc -l < "$OUT_MD") lines, $(wc -c < "$OUT_MD") bytes"

echo "==> Building EPUB"
pandoc "$OUT_MD" \
  -o "$OUT_EPUB" \
  --toc --toc-depth=2 \
  --epub-cover-image="$COVER" \
  --css="$CSS" \
  --metadata title="Recommendation Engines & Ads" \
  --metadata author="Vatsal Raicha"

echo "==> EPUB: $OUT_EPUB ($(du -h "$OUT_EPUB" | cut -f1))"
echo "==> Done."
