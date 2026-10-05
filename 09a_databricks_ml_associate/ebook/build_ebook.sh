#!/usr/bin/env bash
# Build the combined ebook for Topic 09a — Databricks ML Associate (Mastery Track).
# Source files are NOT modified.
#
# Output: ebook/Databricks_ML_Associate_Mastery_complete_ebook.md (combined source),
#         ebook/Databricks_ML_Associate_Mastery_complete_ebook.epub.md (mermaid-preprocessed),
#         ebook/Databricks_ML_Associate_Mastery_complete_ebook.epub
#
# Strategy:
#   - README.md goes in first as preface (level-1 # heading already).
#   - For each chapter, we synthesize a `# Part X — Theme` heading before its
#     part's first chapter, then shift every chapter's headings down by 1
#     (so the chapter's existing `# Chapter N — Title` becomes `## Chapter N — Title`).
#   - Heading shifting is done with a tiny sed pipeline that only touches the
#     copy we're building (source files untouched).

set -euo pipefail

START_TS=$(date +%s)

TOPIC_DIR="$(cd "$(dirname "$0")/.." && pwd)"
EBOOK_DIR="$TOPIC_DIR/ebook"
OUT_MD="$EBOOK_DIR/Databricks_ML_Associate_Mastery_complete_ebook.md"
OUT_MD_EPUB="$EBOOK_DIR/Databricks_ML_Associate_Mastery_complete_ebook.epub.md"
OUT_EPUB="$EBOOK_DIR/Databricks_ML_Associate_Mastery_complete_ebook.epub"
COVER="$EBOOK_DIR/cover.png"
CSS="$EBOOK_DIR/ebook.css"
VENV_PY="/Users/vr/Code/Career_upskill/.venv/bin/python"

# Part folder → Part header (level-1 in combined md)
declare -a PART_DIRS=(
  "part_a_why_ml"
  "part_b_prob_stats"
  "part_c_linear_algebra"
  "part_d_fundamental_problem"
  "part_e_feature_engineering"
  "part_f_supervised"
  "part_g_unsupervised"
  "part_h_evaluation"
  "part_i_hpo"
  "part_j_spark"
  "part_k_pyspark_ml"
  "part_l_databricks_mlflow"
  "part_m_capstone"
)

declare -a PART_TITLES=(
  "Part A — Why ML Exists"
  "Part B — Probability & Statistics Primer"
  "Part C — Linear Algebra & Calculus Essentials"
  "Part D — The Fundamental ML Problem"
  "Part E — Feature Engineering as a Discipline"
  "Part F — Supervised Algorithms — From the Math"
  "Part G — Unsupervised Algorithms"
  "Part H — Model Evaluation Theory"
  "Part I — Hyperparameter Optimization"
  "Part J — Spark from Zero"
  "Part K — pyspark.ml in Depth"
  "Part L — Databricks Platform & MLflow"
  "Part M — Capstone"
)

# ── Step 1 — Build combined markdown ─────────────────────────────────────────
echo "Building combined markdown..."

cat > "$OUT_MD" <<'EOF'
---
title: "Databricks ML Associate — Mastery Track"
subtitle: "Teaching ML from first principles — 76 chapters, 13 parts, ~41,000 lines"
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

EOF

# README first as preface — keep its headings as-is (level-1 is fine for the
# top-level "Topic 09a — ..." preface heading)
echo "  + README.md (preface)"
cat "$TOPIC_DIR/README.md" >> "$OUT_MD"
echo "" >> "$OUT_MD"

# Helper: shift markdown ATX headings down by one level.
# Only touches lines that START with one-or-more '#' followed by a space.
# Code fences are preserved by toggling state.
shift_headings() {
  # shellcheck disable=SC2016
  awk '
    BEGIN { in_fence = 0 }
    {
      # Toggle code-fence state on lines that start with ``` (any language tag)
      if ($0 ~ /^[ \t]*```/) {
        in_fence = !in_fence
        print
        next
      }
      if (in_fence == 0 && $0 ~ /^#{1,6}[ \t]/) {
        # Prepend one extra '#'
        print "#" $0
      } else {
        print
      }
    }
  '
}

# Iterate parts → chapters
for i in "${!PART_DIRS[@]}"; do
  part_dir="${PART_DIRS[$i]}"
  part_title="${PART_TITLES[$i]}"
  full_part_dir="$TOPIC_DIR/$part_dir"

  if [[ ! -d "$full_part_dir" ]]; then
    echo "WARN: missing part dir $part_dir" >&2
    continue
  fi

  # Emit a level-1 Part header (new chapter break in EPUB)
  echo "" >> "$OUT_MD"
  echo "# $part_title" >> "$OUT_MD"
  echo "" >> "$OUT_MD"

  # Find all chapters in this part, sort by leading two-digit prefix
  while IFS= read -r chapter; do
    [[ -z "$chapter" ]] && continue
    chapter_name="$(basename "$chapter")"
    echo "  + $part_dir/$chapter_name"
    echo "" >> "$OUT_MD"
    # Shift this chapter's headings down by one level so the existing
    # `# Chapter N — Title` becomes `## Chapter N — Title`, nesting it under
    # the Part header we just emitted.
    shift_headings < "$chapter" >> "$OUT_MD"
    echo "" >> "$OUT_MD"
  done < <(find "$full_part_dir" -maxdepth 1 -name "*.md" | sort)
done

echo "Combined markdown: $OUT_MD ($(wc -l < "$OUT_MD") lines)"

# ── Step 2 — Build EPUB ──────────────────────────────────────────────────────
echo ""
echo "Building EPUB..."

# (a) Pre-render mermaid blocks → PNG, replace with image references
if command -v mmdc >/dev/null 2>&1; then
  echo "  • Pre-rendering mermaid diagrams via mmdc..."
  "$VENV_PY" "$EBOOK_DIR/preprocess_mermaid.py" "$OUT_MD" "$OUT_MD_EPUB" || cp "$OUT_MD" "$OUT_MD_EPUB"
else
  echo "  • mmdc not found; mermaid blocks will appear as code blocks." >&2
  cp "$OUT_MD" "$OUT_MD_EPUB"
fi

# (b) Generate cover image
if [[ ! -f "$COVER" ]] || [[ "$EBOOK_DIR/make_cover.py" -nt "$COVER" ]]; then
  echo "  • Generating cover image..."
  "$VENV_PY" "$EBOOK_DIR/make_cover.py" "$COVER"
fi

# (c) Metadata for EPUB
META_FILE="$EBOOK_DIR/.epub_metadata.yaml"
cat > "$META_FILE" <<'META'
---
title: "Databricks ML Associate — Mastery Track"
subtitle: "Teaching ML from first principles"
creator:
  - role: author
    text: "Compiled for Vatsal Raicha"
publisher: "Career_upskill"
date: "2026"
lang: "en-US"
identifier: "career_upskill_topic_09a_2026"
description: "A 76-chapter, 13-part mastery-track curriculum for the Databricks Certified Machine Learning Associate exam. Teaches ML from first principles — probability and statistics, linear algebra and calculus, the fundamental ML problem (loss, bias-variance, cross-validation), feature engineering, supervised and unsupervised algorithms from the math, model evaluation theory, hyperparameter optimization, Spark from zero, pyspark.ml in depth, Databricks platform and MLflow, ending in a capstone project and exam strategy. ~41,000 lines of textbook-grade content."
subject:
  - "Databricks"
  - "Machine Learning"
  - "Apache Spark"
  - "PySpark"
  - "MLflow"
  - "Certification Prep"
  - "AI/ML Engineering"
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
END_TS=$(date +%s)
ELAPSED=$((END_TS - START_TS))
echo ""
echo "─── Built in ${ELAPSED}s ───"
ls -la "$OUT_MD" "$OUT_MD_EPUB" "$OUT_EPUB" 2>&1 | grep -v "No such" || true
