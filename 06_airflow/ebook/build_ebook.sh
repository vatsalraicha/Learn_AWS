#!/usr/bin/env bash
# Build Topic 06 EPUB from Airflow modules.
# Source files are NOT modified.
set -euo pipefail

TOPIC_DIR="$(cd "$(dirname "$0")/.." && pwd)"
EBOOK_DIR="$TOPIC_DIR/ebook"
OUT_MD="$EBOOK_DIR/Airflow_complete_ebook.md"
OUT_EPUB="$EBOOK_DIR/Airflow_complete_ebook.epub"
COVER="$EBOOK_DIR/cover.png"
CSS="$EBOOK_DIR/ebook.css"
VENV_PY="/Users/vr/Code/Career_upskill/.venv/bin/python"

MODULES=(
  "01_history_landscape.md"
  "02_core_concepts.md"
  "03_architecture.md"
  "04_executors.md"
  "05_dag_authoring.md"
  "06_scheduling.md"
  "07_sensors_triggers.md"
  "08_secrets_backends.md"
  "09_securing_airflow.md"
  "10_networking.md"
  "11_xcom_data_passing.md"
  "12_data_flow_design.md"
  "13_lineage_openlineage.md"
  "14_observability.md"
  "15_airflow_on_k8s.md"
  "16_mwaa_aws.md"
  "17_composer_gcp.md"
  "18_azure_managed_airflow.md"
  "19_astro_and_onprem.md"
  "20_dwh_integrations.md"
  "21_databricks_integration.md"
  "22_spark_emr_dataproc_glue.md"
  "23_ml_platforms.md"
  "24_dbt_airflow.md"
  "25_alternatives.md"
  "26_cicd_dags.md"
  "27_sre_failure_modes.md"
  "28_cost_scaling.md"
  "29_multi_tenancy.md"
  "30_airflow_3.md"
  "31_migration.md"
  "32_certifications.md"
)

echo "Building combined markdown..."

cat > "$OUT_MD" <<'EOF'
---
title: "Apache Airflow for AI/ML Engineers"
subtitle: "Multi-cloud + security + data-exposure lens (Career_upskill — Topic 06)"
author: "Compiled for Vatsal Raicha"
date: "2026"
lang: "en-US"
---

# How to read this ebook

This is the consolidated reading copy of **Topic 06 — Apache Airflow for AI/ML Engineers**, from the **Career_upskill** project. Source markdown files live at `topics/06_airflow/` and remain canonical.

**Audience:** A Senior/Lead AI/ML engineer preparing to credibly operate, secure, and architect Airflow at the Lead/Architect level — across MWAA, Cloud Composer, Azure Managed Airflow, Astronomer, and self-hosted on-prem. The unifying thread is **how Airflow safely exposes data and credentials** — to workers, downstream systems (Snowflake/Databricks/SageMaker/Vertex), operators (humans), and across cloud boundaries.

**Ordering:** natural numeric sequence — Modules 1 through 32, organized into 6 Parts (A–F).

**Included:** all 32 modules + FACTS.md as an appendix.

**Not included:** example DAGs and Terraform (in `code/`), quizzes (in `quizzes/`).

\newpage

EOF

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

echo "  + FACTS.md (appendix)"
echo "" >> "$OUT_MD"
echo "\\newpage" >> "$OUT_MD"
echo "" >> "$OUT_MD"
echo "# Appendix A — FACTS.md" >> "$OUT_MD"
echo "" >> "$OUT_MD"
echo "_Atomic, citable facts. Provider package versions, MWAA env classes, Composer GA/EOL dates, Airflow 3.0 release, exam metadata._" >> "$OUT_MD"
echo "" >> "$OUT_MD"
cat "$TOPIC_DIR/FACTS.md" >> "$OUT_MD"

echo "Combined markdown: $OUT_MD ($(wc -l < "$OUT_MD") lines)"

if [[ ! -f "$COVER" ]] || [[ "$EBOOK_DIR/make_cover.py" -nt "$COVER" ]]; then
  echo "Generating cover..."
  "$VENV_PY" "$EBOOK_DIR/make_cover.py" "$COVER"
fi

META_FILE="$EBOOK_DIR/.epub_metadata.yaml"
cat > "$META_FILE" <<'META'
---
title: "Apache Airflow for AI/ML Engineers"
subtitle: "Multi-cloud + security + data-exposure lens"
creator:
  - role: author
    text: "Compiled for Vatsal Raicha"
publisher: "Career_upskill"
date: "2026"
lang: "en-US"
identifier: "career_upskill_topic_06_2026"
description: "32-module practitioner's reference for Apache Airflow at the Lead/Architect level. Covers core concepts, architecture, executors (Sequential/Local/Celery/K8s/CeleryK8s/Edge), DAG authoring (TaskFlow, dynamic mapping, deferrable, setup/teardown), scheduling deep, securing Airflow (RBAC, FAB Auth Manager, OIDC, audit), networking, XCom + custom backends, OpenLineage + Marquez + DataHub + Unity Catalog interop, observability, and the four managed-Airflow deep dives (MWAA + PRIVATE_ONLY + Secrets Manager + KMS; Cloud Composer 2 vs 3 + Workload Identity Federation + PSC; Azure Managed Airflow + Fabric; Astronomer Astro Hosted/Hybrid/Software + self-hosted Helm on-prem + air-gap). Integrations with Snowflake/Redshift/BigQuery/Synapse, Databricks, EMR/Dataproc/Glue, SageMaker/Vertex/Azure ML, dbt + Cosmos. Honest comparison with Prefect, Dagster, Argo, Step Functions, Databricks Workflows. CI/CD, SRE failure modes, cost & scaling, multi-tenancy. Airflow 3.0 deep dive (Task SDK, Deadlines, multi-cluster scheduler, Assets, UI rewrite, DAG versioning) and migration. AWS DEA-C01 + Astronomer DAG Authoring certification roadmap."
subject:
  - "Apache Airflow"
  - "Data Engineering"
  - "Workflow Orchestration"
  - "MLOps"
  - "Cloud Architecture"
  - "MWAA"
  - "Cloud Composer"
  - "Astronomer"
rights: "© 2026 Vatsal Raicha. For personal use."
---
META

echo "Building EPUB..."
pandoc "$OUT_MD" \
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
