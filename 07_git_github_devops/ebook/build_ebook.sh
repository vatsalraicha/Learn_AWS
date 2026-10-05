#!/usr/bin/env bash
# Build Topic 07 EPUB from Git, GitHub & DevOps modules.
# Source files are NOT modified.
set -euo pipefail

TOPIC_DIR="$(cd "$(dirname "$0")/.." && pwd)"
EBOOK_DIR="$TOPIC_DIR/ebook"
OUT_MD="$EBOOK_DIR/Git_GitHub_DevOps_complete_ebook.md"
OUT_EPUB="$EBOOK_DIR/Git_GitHub_DevOps_complete_ebook.epub"
OUT_PDF="$EBOOK_DIR/Git_GitHub_DevOps_complete_ebook.pdf"
COVER="$EBOOK_DIR/cover.png"
CSS="$EBOOK_DIR/ebook.css"
VENV_PY="/Users/vr/Code/Career_upskill/.venv/bin/python"

MODULES=(
  "01_git_architecture_objects.md"
  "02_config_identity_signing.md"
  "03_core_workflows.md"
  "04_branching_merging_rebasing.md"
  "05_remotes_forks_upstream.md"
  "06_undo_recovery.md"
  "07_stash_tags_hooks_submodules_worktrees.md"
  "08_repo_setup_standards.md"
  "09_issues_projects_milestones.md"
  "10_prs_code_review_merge.md"
  "11_branch_protection_rulesets_codeowners.md"
  "12_auth_pat_ssh_signing.md"
  "13_orgs_teams_permissions.md"
  "14_gh_cli_fundamentals.md"
  "15_branching_strategies.md"
  "16_feature_flags_innersource.md"
  "17_monorepo_vs_polyrepo.md"
  "18_python_ml_repo_structure.md"
  "19_templates_adr_docs_conventional_commits.md"
  "20_actions_workflow_events.md"
  "21_actions_jobs_steps_runners.md"
  "22_actions_marketplace_expressions.md"
  "23_actions_vars_secrets_env.md"
  "24_actions_outputs_needs_concurrency.md"
  "25_actions_cache_artifacts_matrix.md"
  "26_actions_reusable_workflows.md"
  "27_actions_composite_custom.md"
  "28_actions_self_hosted_arc_gpu.md"
  "29_actions_oidc_aws.md"
  "30_actions_environments_protection.md"
  "31_actions_token_cost_templates.md"
  "32_ghas_secret_scanning.md"
  "33_ghas_codeql_autofix.md"
  "34_ghas_dependabot.md"
  "35_ghas_sbom_slsa_attestations.md"
  "36_compliance_sso_scim_audit.md"
  "37_compliance_sr117_audit.md"
  "38_notebook_discipline.md"
  "39_lfs_dvc_lakefs_hf.md"
  "40_precommit_reproducibility_refactor.md"
  "41_mlops_ci_for_ml.md"
  "42_mlops_validation_gates.md"
  "43_mlops_mlflow_sagemaker.md"
  "44_mlops_champion_challenger.md"
  "45_mlops_retraining_rollback.md"
  "46_aws_oidc_trust_policy_deep.md"
  "47_aws_deploy_sagemaker_ecs_eks_lambda.md"
  "48_aws_cdk_cfn_tf_cross_account.md"
  "49_jenkins_architecture_jenkinsfile.md"
  "50_jenkins_multibranch_shared_libs.md"
  "51_jenkins_credentials_ghaws.md"
  "52_apps_webhooks_ghcli_graphql.md"
  "53_ai_copilot.md"
  "54_ai_claude_code_enterprise.md"
  "55_ai_governance_privacy.md"
  "56_capital_one_devops_deep.md"
  "57_cert_roadmap.md"
)

echo "Building combined markdown..."

cat > "$OUT_MD" <<'EOF'
---
title: "Git, GitHub & DevOps for AI/ML Engineers"
subtitle: "Capital One — Sr Lead AI/ML lens (Career_upskill — Topic 07)"
author: "Compiled for Vatsal Raicha"
date: "2026"
lang: "en-US"
documentclass: book
papersize: letter
monofont: "Menlo"
---

# How to read this ebook

This is the consolidated reading copy of **Topic 07 — Git, GitHub & DevOps for AI/ML Engineers**, from the **Career_upskill** project. Source markdown files live at `topics/07_git_github_devops/` and remain canonical.

**Audience:** A Senior AI/ML engineer preparing for the Sr Lead AI/ML Engineer role at Capital One — AWS-native, regulated finance, Snowflake + Databricks + EKS-KServe spine, Jenkins + GitHub Enterprise + GitHub Actions hybrid CI/CD.

**Unifying thread:** *How does a regulated bank ship AI/ML code from a developer's laptop to a SageMaker endpoint, with every step audit-trailed, every artifact signed, every credential ephemeral, and nothing manual on the prod path?*

**Ordering:** natural numeric sequence — Modules 1 through 57, organized into 15 Parts (A–O).

**Included:** all 57 modules + CAPITAL_ONE.md companion + FACTS.md as appendices.

**Not included:** code artifacts (in `code/`), quizzes (in `quizzes/`).

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

echo "  + CAPITAL_ONE.md (appendix A)"
echo "" >> "$OUT_MD"
echo "\\newpage" >> "$OUT_MD"
echo "" >> "$OUT_MD"
echo "# Appendix A — Capital One DevOps Dossier" >> "$OUT_MD"
echo "" >> "$OUT_MD"
echo "_The standalone Capital One dossier — read before any interview._" >> "$OUT_MD"
echo "" >> "$OUT_MD"
cat "$TOPIC_DIR/CAPITAL_ONE.md" >> "$OUT_MD"

echo "  + FACTS.md (appendix B)"
echo "" >> "$OUT_MD"
echo "\\newpage" >> "$OUT_MD"
echo "" >> "$OUT_MD"
echo "# Appendix B — FACTS.md" >> "$OUT_MD"
echo "" >> "$OUT_MD"
echo "_Atomic, citable facts with last-verified dates. Git versions, Actions limits, GHAS pricing, Jenkins LTS, Copilot tiers, SR 11-7 reference, cert metadata._" >> "$OUT_MD"
echo "" >> "$OUT_MD"
cat "$TOPIC_DIR/FACTS.md" >> "$OUT_MD"

echo "Combined markdown: $OUT_MD ($(wc -l < "$OUT_MD") lines)"

if [[ ! -f "$COVER" ]] || [[ "$EBOOK_DIR/make_cover.py" -nt "$COVER" ]]; then
  echo "Generating cover..."
  "$VENV_PY" "$EBOOK_DIR/make_cover.py" "$COVER"
fi

# ── Build PDF (xelatex) ─────────────────────────────────────────────
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

META_FILE="$EBOOK_DIR/.epub_metadata.yaml"
cat > "$META_FILE" <<'META'
---
title: "Git, GitHub & DevOps for AI/ML Engineers"
subtitle: "Capital One — Sr Lead AI/ML lens"
creator:
  - role: author
    text: "Compiled for Vatsal Raicha"
publisher: "Career_upskill"
date: "2026"
lang: "en-US"
identifier: "career_upskill_topic_07_2026"
description: "57-module practitioner's reference for Git, GitHub, and DevOps tooling — calibrated to the Sr Lead AI/ML Engineer role at Capital One. Covers Git architecture and object model, the full branching/merging/rebasing/recovery toolkit, GitHub collaboration (PRs, Rulesets, CODEOWNERS, signed commits, SAML SSO), trunk-based development with feature flags (Capital One's published DORA pattern), Python ML repo structure with pyproject.toml + uv + src layout, GitHub Actions deep (YAML, events, runners, matrix, caching, reusable workflows, composite actions, ARC on EKS, GPU runners), the canonical OIDC-to-AWS pattern with per-environment IAM role scoping and the InnerSource job_workflow_ref claim, GHAS (Secret Protection $19/mo + Code Security $30/mo unbundled April 2025), CodeQL + Copilot Autofix, Dependabot, SBOM + SLSA Build Level 2/3 + Artifact Attestations + Sigstore, SAML/SCIM/audit-log streaming, SR 11-7 model risk management for ML CI/CD, notebook discipline (jupytext/nbdime/nbstripout), DVC + Git LFS + Hugging Face Hub, pre-commit + reproducibility + notebook-to-module refactoring, CI for ML (lint, test, type, notebook test, model smoke), model validation gates (fairness/bias/drift), MLflow + SageMaker Model Registry promotion flow, champion/challenger + shadow + canary + A/B safe-rollout, automated retraining triggers + sub-5-minute rollback workflows, AWS deploy targets (SageMaker, ECS, EKS+KServe, Lambda, ECR), CDK + CloudFormation + Terraform from Actions + cross-account chaining, Jenkins (architecture, declarative Jenkinsfile, multibranch + GitHub webhooks, shared libraries, credentials + IRSA, the GitHub→Jenkins→AWS handoff), GitHub Apps + webhooks + gh CLI + GraphQL, GitHub Copilot (Business/Enterprise + usage-based billing June 2026), Claude Code Enterprise (agentic workflows, CLAUDE.md, MCP), AI dev tool governance for regulated environments, Capital One DevOps deep dive (Singular Software Delivery Pipeline, Hygieia, Cloud Custodian, 7000 engineers / 500k Jenkins pipelines / 50k builds/day), and certification roadmap (GH-900, GH-200, GH-500, GH-300, Jenkins CJE). Includes a Capital One companion dossier and a FACTS.md appendix with last-verified citable facts."
subject:
  - "Git"
  - "GitHub"
  - "GitHub Actions"
  - "GitHub Advanced Security"
  - "Jenkins"
  - "CI/CD"
  - "MLOps"
  - "DevOps"
  - "AWS"
  - "SageMaker"
  - "InnerSource"
  - "SR 11-7"
  - "Trunk-based Development"
  - "Capital One"
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
