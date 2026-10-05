#!/usr/bin/env bash
# Build the combined ebook for Topic 14 — AWS Certified ML Engineer Associate.
# Source files are NOT modified.
#
# Output: ebook/AWS_MLA_C01_Practice_Guide.md (combined source),
#         ebook/AWS_MLA_C01_Practice_Guide.epub.md (mermaid-preprocessed),
#         ebook/AWS_MLA_C01_Practice_Guide.epub

set -euo pipefail

START_TS=$(date +%s)

TOPIC_DIR="$(cd "$(dirname "$0")/.." && pwd)"
EBOOK_DIR="$TOPIC_DIR/ebook"
OUT_MD="$EBOOK_DIR/AWS_MLA_C01_Practice_Guide.md"
OUT_MD_EPUB="$EBOOK_DIR/AWS_MLA_C01_Practice_Guide.epub.md"
OUT_EPUB="$EBOOK_DIR/AWS_MLA_C01_Practice_Guide.epub"
COVER="$EBOOK_DIR/cover.png"
CSS="$EBOOK_DIR/ebook.css"
VENV_PY="/Users/vr/Code/Career_upskill/.venv/bin/python"

# Part folder → Part header (level-1 in combined md)
declare -a PART_DIRS=(
  "part_a_landscape"
  "part_b_aws_foundations"
  "part_c_data_ingestion_storage"
  "part_d_data_prep_features"
  "part_e_model_development"
  "part_f_hpo_distributed_training"
  "part_g_deployment_orchestration"
  "part_h_monitoring_governance"
  "part_i_security_iam_networking"
  "part_j_ai_services_genai"
  "part_k_capstone"
)

declare -a PART_TITLES=(
  "Part A — Landscape"
  "Part B — AWS Foundations for ML Engineers"
  "Part C — Data Ingestion & Storage"
  "Part D — Data Preparation & Features"
  "Part E — Model Development on SageMaker"
  "Part F — HPO & Distributed Training"
  "Part G — Deployment & Inference"
  "Part H — Orchestration & CI/CD"
  "Part I — Monitoring, Drift & Governance"
  "Part J — Security, IAM, Networking & Cost"
  "Part K — AI Services, GenAI, Capstone & Exam Day"
)

# ── Step 1 — Build combined markdown ─────────────────────────────────────────
echo "Building combined markdown..."

cat > "$OUT_MD" <<'EOF'
---
title: "AWS Certified Machine Learning Engineer – Associate Practice Guide"
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

# README first as preface — keep its headings as-is
echo "  + README.md (preface)"
cat "$TOPIC_DIR/README.md" >> "$OUT_MD"
echo "" >> "$OUT_MD"

# Helper: shift markdown ATX headings down by one level.
shift_headings() {
  awk '
    BEGIN { in_fence = 0 }
    {
      if ($0 ~ /^[ \t]*```/) {
        in_fence = !in_fence
        print
        next
      }
      if (in_fence == 0 && $0 ~ /^#{1,6}[ \t]/) {
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

  echo "" >> "$OUT_MD"
  echo "# $part_title" >> "$OUT_MD"
  echo "" >> "$OUT_MD"

  while IFS= read -r chapter; do
    [[ -z "$chapter" ]] && continue
    chapter_name="$(basename "$chapter")"
    echo "  + $part_dir/$chapter_name"
    echo "" >> "$OUT_MD"
    shift_headings < "$chapter" >> "$OUT_MD"
    echo "" >> "$OUT_MD"
  done < <(find "$full_part_dir" -maxdepth 1 -name "*.md" | sort)
done

echo "Combined markdown: $OUT_MD ($(wc -l < "$OUT_MD") lines)"

# ── Step 2 — Build EPUB ──────────────────────────────────────────────────────
echo ""
echo "Building EPUB..."

# (a) Pre-render mermaid blocks → PNG
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
title: "AWS Certified Machine Learning Engineer – Associate Practice Guide"
creator:
  - role: author
    text: "Compiled for Vatsal Raicha"
publisher: "Career_upskill"
date: "2026"
lang: "en-US"
identifier: "career_upskill_topic_14_mla_c01_2026"
description: "A 64-chapter, 11-part practice guide for the AWS Certified Machine Learning Engineer – Associate (MLA-C01) exam. Teaches the production ML engineering skills the exam tests, with deep dives across data ingestion, feature engineering, SageMaker training and deployment, MLOps orchestration, monitoring and drift, security and cost, plus Bedrock and generative AI patterns. ~54,000 lines of textbook-grade content."
subject:
  - "AWS"
  - "Amazon SageMaker"
  - "Amazon Bedrock"
  - "Machine Learning"
  - "MLOps"
  - "Certification Prep"
  - "AI/ML Engineering"
  - "MLA-C01"
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
