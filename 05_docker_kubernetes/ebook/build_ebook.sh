#!/usr/bin/env bash
# Build Topic 05 EPUB from Docker/Kubernetes modules.
# Source files are NOT modified.
set -euo pipefail

TOPIC_DIR="$(cd "$(dirname "$0")/.." && pwd)"
EBOOK_DIR="$TOPIC_DIR/ebook"
OUT_MD="$EBOOK_DIR/Docker_K8s_complete_ebook.md"
OUT_EPUB="$EBOOK_DIR/Docker_K8s_complete_ebook.epub"
COVER="$EBOOK_DIR/cover.png"
CSS="$EBOOK_DIR/ebook.css"
VENV_PY="/Users/vr/Code/Career_upskill/.venv/bin/python"

MODULES=(
  "01_linux_primitives.md"
  "02_docker_architecture.md"
  "03_dockerfile_images.md"
  "04_image_security.md"
  "05_registries.md"
  "06_docker_networking.md"
  "07_docker_storage.md"
  "08_docker_secrets.md"
  "09_docker_compose.md"
  "10_hardening_checklist.md"
  "11_cis_cves.md"
  "12_data_exposure_onprem.md"
  "13_data_exposure_aws.md"
  "14_data_exposure_gcp.md"
  "15_data_exposure_azure.md"
  "16_k8s_architecture.md"
  "17_workload_objects.md"
  "18_k8s_networking.md"
  "19_k8s_storage.md"
  "20_configmap_secrets.md"
  "21_rbac_serviceaccounts.md"
  "22_pod_security.md"
  "23_admission_control.md"
  "24_k8s_supply_chain.md"
  "25_observability_runtime.md"
  "26_eks_data_exposure.md"
  "27_gke_data_exposure.md"
  "28_aks_data_exposure.md"
  "29_onprem_k8s_data.md"
  "30_model_serving_k8s.md"
  "31_training_k8s.md"
  "32_service_mesh.md"
  "33_cert_roadmap.md"
)

echo "Building combined markdown..."

cat > "$OUT_MD" <<'EOF'
---
title: "Docker & Kubernetes for AI/ML Engineers"
subtitle: "Multi-cloud data-exposure security lens (Career_upskill — Topic 05)"
author: "Compiled for Vatsal Raicha"
date: "2026"
lang: "en-US"
---

# How to read this ebook

This is the consolidated reading copy of **Topic 05 — Docker & Kubernetes for AI/ML Engineers**, from the **Career_upskill** project. Source markdown files live at `topics/05_docker_kubernetes/` and remain canonical.

**Audience:** A Senior/Lead AI/ML engineer preparing for the EKS+KServe stack at Capital One (and analogous regulated-finance environments). Linux primitives are taught from first principles so the security controls in later modules make sense at the system-call level. The unifying thread is **how to expose data to and from containers safely** across **on-premise, AWS, GCP, and Azure** — modules 12–15 and 26–29 carry the cloud-specific deep dives.

**Ordering:** natural numeric sequence — Modules 1 through 33, organized into 9 Parts (A–I).

**Included:** all 33 modules + FACTS.md as an appendix.

**Not included:** code artifacts (Dockerfiles, K8s manifests, Helm fragments, Terraform — they ship in `code/`); quizzes (in `quizzes/`); table-of-contents file (this ebook's auto-generated TOC supersedes it).

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
echo "_Atomic, citable facts. Single source of truth for CVE numbers, CSI driver GA dates, K8s version cutoffs, certification metadata, cloud-specific identity-binding mechanisms._" >> "$OUT_MD"
echo "" >> "$OUT_MD"
cat "$TOPIC_DIR/FACTS.md" >> "$OUT_MD"

echo "Combined markdown: $OUT_MD ($(wc -l < "$OUT_MD") lines)"

# Generate cover
if [[ ! -f "$COVER" ]] || [[ "$EBOOK_DIR/make_cover.py" -nt "$COVER" ]]; then
  echo "Generating cover..."
  "$VENV_PY" "$EBOOK_DIR/make_cover.py" "$COVER"
fi

# Metadata
META_FILE="$EBOOK_DIR/.epub_metadata.yaml"
cat > "$META_FILE" <<'META'
---
title: "Docker & Kubernetes for AI/ML Engineers"
subtitle: "Multi-cloud data-exposure security lens"
creator:
  - role: author
    text: "Compiled for Vatsal Raicha"
publisher: "Career_upskill"
date: "2026"
lang: "en-US"
identifier: "career_upskill_topic_05_2026"
description: "33-module practitioner's reference covering Linux kernel primitives, Docker runtime architecture, image security and supply chain (Cosign, SBOM, SLSA), the four cloud-specific data-exposure deep dives (on-prem NFS/Ceph/MinIO/Vault; AWS ECS/EFS/FSx/Mountpoint-S3/IMDSv2; GCP Workload Identity Federation/gcsfuse/VPC-SC; Azure Managed Identity/Files/Disk/Blob/Key Vault), Kubernetes fundamentals + security, the EKS/GKE/AKS/on-prem K8s deep dives (IRSA, EKS Pod Identity, WIF, Entra Workload ID, Rook-Ceph, Velero), AI/ML on K8s (KServe + Triton + vLLM, Kubeflow Training Operator + GPU Operator + Karpenter), service mesh (Istio ambient, Linkerd, Cilium, SPIFFE/SPIRE), and the KCNA → CKAD → CKA → CKS certification roadmap."
subject:
  - "Docker"
  - "Kubernetes"
  - "Container Security"
  - "AI/ML Engineering"
  - "Cloud Architecture"
  - "DevSecOps"
  - "MLOps"
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
