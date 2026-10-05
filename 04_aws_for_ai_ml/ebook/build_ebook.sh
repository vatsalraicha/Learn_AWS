#!/usr/bin/env bash
# Build the combined ebook from Topic 04 markdown files.
# Source files are NOT modified.
#
# Output: ebook/AWS_for_AI_ML_complete_ebook.md (combined source),
#         ebook/AWS_for_AI_ML_complete_ebook.pdf,
#         ebook/AWS_for_AI_ML_complete_ebook.epub

set -euo pipefail

TOPIC_DIR="$(cd "$(dirname "$0")/.." && pwd)"
EBOOK_DIR="$TOPIC_DIR/ebook"
OUT_MD="$EBOOK_DIR/AWS_for_AI_ML_complete_ebook.md"
OUT_MD_EPUB="$EBOOK_DIR/AWS_for_AI_ML_complete_ebook.epub.md"
OUT_PDF="$EBOOK_DIR/AWS_for_AI_ML_complete_ebook.pdf"
OUT_EPUB="$EBOOK_DIR/AWS_for_AI_ML_complete_ebook.epub"
COVER="$EBOOK_DIR/cover.png"
CSS="$EBOOK_DIR/ebook.css"
VENV_PY="/Users/vr/Code/Career_upskill/.venv/bin/python"

# Module order — natural numeric sort 01..57
MODULES=(
  "01_account_org_landing_zone.md"
  "02_iam_deep.md"
  "03_regions_azs_edge.md"
  "04_billing_pricing_tagging.md"
  "05_networking_primer.md"
  "06_vpc_deep.md"
  "07_sg_nacl_flow_logs.md"
  "08_multi_vpc_hybrid.md"
  "09_dns_lb_edge.md"
  "10_s3_deep.md"
  "11_efs_fsx_ebs.md"
  "12_lake_governance.md"
  "13_glue_fundamentals.md"
  "14_glue_spark_deep.md"
  "15_etl_orchestration.md"
  "16_rds_relational.md"
  "17_aurora_deep.md"
  "18_dynamodb_deep.md"
  "19_documentdb_deep.md"
  "20_keyspaces_cassandra.md"
  "21_elasticache_memorydb.md"
  "22_redshift_deep.md"
  "23_snowflake_on_aws.md"
  "24_athena_federation.md"
  "25_neptune_graph.md"
  "26_opensearch.md"
  "27_vector_decision_framework.md"
  "28_msk_deep.md"
  "29_kinesis_flink.md"
  "30_ec2_accelerators.md"
  "31_ecs_fargate_batch.md"
  "32_lambda_deep.md"
  "33_eks_foundations.md"
  "34_sagemaker_platform.md"
  "35_sagemaker_data.md"
  "36_sagemaker_training.md"
  "37_sagemaker_inference.md"
  "38_sagemaker_mlops.md"
  "39_jumpstart_canvas_autopilot.md"
  "40_hyperpod.md"
  "41_sagemaker_networking_security.md"
  "42_bedrock.md"
  "43_amazon_q.md"
  "44_self_hosted_fm.md"
  "45_databricks_aws_architecture.md"
  "46_unity_catalog_aws.md"
  "47_databricks_networking.md"
  "48_emr_vs_databricks.md"
  "49_databricks_aws_admin.md"
  "50_security_primitives.md"
  "51_governance_policy_as_code.md"
  "52_financial_services_compliance.md"
  "53_c1_mlops_spine.md"
  "54_kserve_deep.md"
  "55_cicd_for_ml.md"
  "56_observability_cost.md"
  "57_cert_roadmap.md"
)

# ── Step 1 — Build combined markdown ─────────────────────────────────────────
echo "Building combined markdown..."

cat > "$OUT_MD" <<'EOF'
---
title: "AWS for AI/ML Engineers"
subtitle: "A practitioner's reference for Senior Lead engineers (Career_upskill — Topic 04, Capital One lens)"
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

This is the consolidated reading copy of **Topic 04 — AWS for AI/ML Engineers**, from the **Career_upskill** project. The source markdown files live at `topics/04_aws_for_ai_ml/` and remain the canonical version; this ebook is a derived artifact.

**Audience:** a Senior/Lead AI/ML engineer preparing for the AWS-native, regulated-finance environment at Capital One. Networking is taught from first principles. Database depth is maximized (12 dedicated modules). SageMaker gets 8 modules. Databricks-on-AWS gets a full 5-module Part since the user already has Azure Databricks (Topic 02) fluency.

**Ordering** is the natural numeric sequence — Modules 1 through 57, organized into 14 Parts (A–N).

**What's included:**
- All 57 conceptual modules
- The Capital One dossier (interview/role-prep)
- The FACTS.md appendix (citable facts, dates, costs)
- A full Sources & References appendix

**What's NOT included:**
- Code artifacts (Terraform, KServe YAML, Custodian policies, Python pipelines — they run, they don't read)
- Quizzes in their original collapsible form
- The Table of Contents file (this ebook's auto-generated TOC supersedes it)

**Diagrams** are Mermaid where present. The EPUB build pre-renders them to PNG via the `mmdc` CLI. In the PDF they appear as code blocks unless mmdc is installed.

**Cross-references** in the source modules use relative paths like `[Module 42](42_bedrock.md)`. In this single-file ebook they appear as in-document links.

\newpage

EOF

# Capital One dossier first — interview-ready content
echo "  + CAPITAL_ONE.md (dossier)"
echo "" >> "$OUT_MD"
echo "\\newpage" >> "$OUT_MD"
echo "" >> "$OUT_MD"
cat "$TOPIC_DIR/CAPITAL_ONE.md" >> "$OUT_MD"
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
echo "# Appendix A — FACTS.md" >> "$OUT_MD"
echo "" >> "$OUT_MD"
echo "_Atomic, citable facts. Single source of truth for dates, costs, GA, retirements, and exam metadata._" >> "$OUT_MD"
echo "" >> "$OUT_MD"
# Skip the FACTS.md heading (it's already inside the file) — print the body
cat "$TOPIC_DIR/FACTS.md" >> "$OUT_MD"

# Appendix B: Sources & References
echo "  + SOURCES.md (appendix)"
echo "" >> "$OUT_MD"
echo "\\newpage" >> "$OUT_MD"
echo "" >> "$OUT_MD"
cat "$EBOOK_DIR/SOURCES.md" >> "$OUT_MD"

echo "Combined markdown: $OUT_MD ($(wc -l < "$OUT_MD") lines)"

# ── Step 2 — Convert to PDF ──────────────────────────────────────────────────
echo ""
echo "Building PDF (this takes ~60-120s for 57 modules)..."

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

# ── Step 3 — Build EPUB ──────────────────────────────────────────────────────
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
title: "AWS for AI/ML Engineers"
subtitle: "A practitioner's reference — Capital One lens"
creator:
  - role: author
    text: "Compiled for Vatsal Raicha"
publisher: "Career_upskill"
date: "2026"
lang: "en-US"
identifier: "career_upskill_topic_04_2026"
description: "Complete practitioner's reference for AWS at the Senior Lead AI/ML Engineer level — networking from zero, 12 database modules, 8 SageMaker modules, Bedrock + self-hosted GenAI, Databricks-on-AWS, regulated-finance security & compliance, Capital One MLOps patterns including EKS+KServe, and the full AWS AI/ML certification roadmap (SAA → MLA → DEA → SCS → SAP → AIP)."
subject:
  - "Amazon Web Services"
  - "Machine Learning"
  - "AI/ML Engineering"
  - "Cloud Architecture"
  - "Financial Services"
  - "MLOps"
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
