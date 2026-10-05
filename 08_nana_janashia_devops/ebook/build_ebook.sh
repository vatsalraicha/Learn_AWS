#!/usr/bin/env bash
# Build Topic 08 EPUB + PDF from all module files.
set -euo pipefail

TOPIC_DIR="$(cd "$(dirname "$0")/.." && pwd)"
EBOOK_DIR="$TOPIC_DIR/ebook"
OUT_MD="$EBOOK_DIR/Nana_Janashia_DevOps_complete_ebook.md"
OUT_EPUB="$EBOOK_DIR/Nana_Janashia_DevOps_complete_ebook.epub"
OUT_PDF="$EBOOK_DIR/Nana_Janashia_DevOps_complete_ebook.pdf"
COVER="$EBOOK_DIR/cover.png"
CSS="$EBOOK_DIR/ebook.css"
VENV_PY="/Users/vr/Code/Career_upskill/.venv/bin/python"

# Module order
MODULES=(
  "01_intro_devops.md"
  "02_linux_basics.md"
  "03_git_devops.md"
  "04_databases.md"
  "05_build_tools.md"
  "06_iaas_digitalocean.md"
  "07_nexus.md"
  "08_docker.md"
  "09_jenkins.md"
  "10_aws_devops.md"
  "11_k8s_overview.md"
  "12_eks.md"
  "13_terraform.md"
  "14_python_basics.md"
  "15_boto3_automation.md"
  "16_ansible.md"
  "17_prometheus.md"
  "18_security_essentials.md"
  "19_devsecops_intro.md"
  "20_gitleaks_precommit.md"
  "21_defectdojo.md"
  "22_sca.md"
  "23_cd_pipeline.md"
  "24_image_scanning.md"
  "25_aws_security.md"
  "26_dast_zap.md"
  "27_iac_gitops.md"
  "28_cloudtrail_cloudwatch.md"
  "29_k8s_security.md"
  "30_eks_access.md"
  "31_gitlab_oidc.md"
  "32_eks_blueprints.md"
  "33_argocd.md"
  "34_opa_gatekeeper.md"
  "35_secrets_management.md"
  "36_istio.md"
  "37_compliance_as_code.md"
  "38_devsecops_org_change.md"
  "39_gitlab_vs_actions_jenkins.md"
  "40_gitlab_core.md"
  "41_gitlab_runners.md"
  "42_gitlab_nodejs_pipeline.md"
  "43_gitlab_optimization.md"
  "44_gitlab_microservices.md"
  "45_gitlab_components.md"
  "46_gitlab_to_k8s.md"
  "47_ai_study_assistants.md"
  "48_agile_scrum_jira.md"
  "49_web_fundamentals.md"
  "50_frontend_frameworks.md"
  "51_vuejs.md"
  "52_nodejs.md"
  "53_mongodb_sql_nosql.md"
  "54_testing.md"
  "55_packaging.md"
  "56_linux_deploy.md"
  "57_multienv_config.md"
  "58_git_for_app_teams.md"
  "59_ai_tools_2026.md"
  "60_cka_exam_logistics.md"
  "61_k8s_core_concepts.md"
  "62_kubeadm_cluster_build.md"
  "63_deployments_services_dns.md"
  "64_external_services.md"
  "65_rbac_certificates_api.md"
  "66_troubleshooting.md"
  "67_multicontainer_pods.md"
  "68_volumes.md"
  "69_configmap_secret.md"
  "70_resources_limits.md"
  "71_scheduling.md"
  "72_probes.md"
  "73_deployment_strategies.md"
  "74_etcd_backup_restore.md"
  "75_k8s_rest_api.md"
  "76_cluster_upgrade.md"
  "77_kube_contexts.md"
  "78_certs_renewal.md"
  "79_network_policy.md"
  "80_cka_study_plan.md"
)

# Map module 78 to actual filename
ACTUAL_MODULES=()
for m in "${MODULES[@]}"; do
  if [ -f "$TOPIC_DIR/$m" ]; then
    ACTUAL_MODULES+=("$m")
  elif [ "$m" = "78_certs_renewal.md" ] && [ -f "$TOPIC_DIR/78_cert_management.md" ]; then
    ACTUAL_MODULES+=("78_cert_management.md")
  else
    echo "WARN: $m not found, skipping"
  fi
done

echo "==> Generating cover"
"$VENV_PY" "$EBOOK_DIR/make_cover.py" "$COVER"

echo "==> Building combined markdown"
cat > "$OUT_MD" <<'EOF'
---
title: "Nana Janashia DevOps Curriculum"
subtitle: "DevOps · DevSecOps · GitLab CI/CD · IT Fundamentals · CKA (Career_upskill — Topic 08)"
author: "Vatsal Raicha"
date: "May 2026"
lang: "en-US"
rights: "© 2026 Vatsal Raicha. Personal use only."
description: "80-module compendium covering Nana Janashia's five paid courses, written for a senior AI/ML engineer at Optum targeting Capital One Sr Lead AI/ML."
---

EOF

cat "$TOPIC_DIR/README.md" >> "$OUT_MD"
echo -e "\n\n\\newpage\n\n" >> "$OUT_MD"
cat "$TOPIC_DIR/00_Table_Of_Contents.md" >> "$OUT_MD"
echo -e "\n\n\\newpage\n\n" >> "$OUT_MD"
cat "$TOPIC_DIR/FACTS.md" >> "$OUT_MD"
echo -e "\n\n\\newpage\n\n" >> "$OUT_MD"

for m in "${ACTUAL_MODULES[@]}"; do
  echo "  + $m"
  echo -e "\n\n\\newpage\n\n" >> "$OUT_MD"
  cat "$TOPIC_DIR/$m" >> "$OUT_MD"
done

# Quizzes
echo -e "\n\n\\newpage\n\n# Part Quizzes\n\n" >> "$OUT_MD"
for q in part1_devops_bootcamp.md part2_devsecops.md part3_gitlab.md part4_it_fundamentals.md part5_cka.md; do
  if [ -f "$TOPIC_DIR/quizzes/$q" ]; then
    echo -e "\n\\newpage\n" >> "$OUT_MD"
    cat "$TOPIC_DIR/quizzes/$q" >> "$OUT_MD"
  fi
done

# Capital One dossier
echo -e "\n\n\\newpage\n\n" >> "$OUT_MD"
cat "$TOPIC_DIR/CAPITAL_ONE.md" >> "$OUT_MD"

echo "==> Combined markdown: $(wc -l < "$OUT_MD") lines, $(wc -c < "$OUT_MD") bytes"

echo "==> Building EPUB"
pandoc "$OUT_MD" \
  -o "$OUT_EPUB" \
  --toc --toc-depth=2 \
  --epub-cover-image="$COVER" \
  --css="$CSS" \
  --metadata title="Nana Janashia DevOps Curriculum" \
  --metadata author="Vatsal Raicha"

echo "==> EPUB: $OUT_EPUB ($(du -h "$OUT_EPUB" | cut -f1))"

if command -v xelatex &> /dev/null; then
  echo "==> Building PDF (xelatex)"
  pandoc "$OUT_MD" \
    -o "$OUT_PDF" \
    --toc --toc-depth=2 \
    --pdf-engine=xelatex \
    -V geometry:margin=1in \
    -V fontsize=11pt \
    -V mainfont="Helvetica" \
    -V monofont="Menlo" \
    --highlight-style=tango \
    || echo "PDF build failed (continuing)"
  if [ -f "$OUT_PDF" ]; then
    echo "==> PDF: $OUT_PDF ($(du -h "$OUT_PDF" | cut -f1))"
  fi
else
  echo "==> xelatex not available; skipping PDF"
fi

echo "==> Done."
ls -lh "$EBOOK_DIR/"
