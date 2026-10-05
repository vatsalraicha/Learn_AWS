# Topic 07 — Master Table of Contents

> All 57 modules + companion files + quizzes + code artifacts. See [`README.md`](README.md) for the narrative learning path and [`FACTS.md`](FACTS.md) for citable facts.

## Companion files

- [`README.md`](README.md) — entry point and learning path
- [`FACTS.md`](FACTS.md) — citable facts with last-verified dates
- [`CAPITAL_ONE.md`](CAPITAL_ONE.md) — Capital One DevOps dossier

## Part A — Git fundamentals

- [01 — Git history, architecture & object model](01_git_architecture_objects.md)
- [02 — Configuration, identity, signing setup (SSH + GPG)](02_config_identity_signing.md)
- [03 — Core workflows + .gitignore + .gitattributes](03_core_workflows.md)
- [04 — Branching, merging, rebasing, conflict resolution](04_branching_merging_rebasing.md)
- [05 — Remotes, fetch/pull/push, forks, upstream sync](05_remotes_forks_upstream.md)
- [06 — Undo & recovery (reset, revert, restore, reflog, blame, bisect)](06_undo_recovery.md)
- [07 — Stash, tags, hooks, submodules, worktrees](07_stash_tags_hooks_submodules_worktrees.md)

## Part B — GitHub collaboration

- [08 — Repository setup standards](08_repo_setup_standards.md)
- [09 — Issues, projects, milestones, labels](09_issues_projects_milestones.md)
- [10 — Pull requests, code review, merge strategies](10_prs_code_review_merge.md)
- [11 — Branch protection, Rulesets, CODEOWNERS](11_branch_protection_rulesets_codeowners.md) 🏦
- [12 — Auth: PAT, SSH, GPG/SSH commit signing](12_auth_pat_ssh_signing.md) 🏦
- [13 — Organizations, teams, permissions](13_orgs_teams_permissions.md)
- [14 — GitHub CLI (`gh`) fundamentals](14_gh_cli_fundamentals.md)

## Part C — Branching strategies

- [15 — Git Flow vs GitHub Flow vs Trunk-based](15_branching_strategies.md) ⭐
- [16 — Feature flags, release branching, InnerSource](16_feature_flags_innersource.md)

## Part D — Repository architecture

- [17 — Monorepo vs polyrepo](17_monorepo_vs_polyrepo.md)
- [18 — Python ML repo structure (pyproject.toml, packaging)](18_python_ml_repo_structure.md)
- [19 — Templates, ADRs, docs, conventional commits, release-please](19_templates_adr_docs_conventional_commits.md)

## Part E — GitHub Actions Core

- [20 — Workflow YAML, events, triggers](20_actions_workflow_events.md)
- [21 — Jobs, steps, runners](21_actions_jobs_steps_runners.md)
- [22 — Marketplace, expressions, contexts, conditionals](22_actions_marketplace_expressions.md)
- [23 — Variables, secrets, env scoping](23_actions_vars_secrets_env.md)
- [24 — Outputs, needs, concurrency, timeouts](24_actions_outputs_needs_concurrency.md)
- [25 — Caching, artifacts, matrix builds, debugging](25_actions_cache_artifacts_matrix.md)

## Part F — GitHub Actions Advanced

- [26 — Reusable workflows (`workflow_call`)](26_actions_reusable_workflows.md) ⭐
- [27 — Composite + custom actions (JS, Docker)](27_actions_composite_custom.md) ⭐
- [28 — Self-hosted runners + ARC + GPU runners](28_actions_self_hosted_arc_gpu.md) ⭐
- [29 — OIDC to AWS — canonical pattern](29_actions_oidc_aws.md) ⭐
- [30 — Environments + protection rules + scoped secrets](30_actions_environments_protection.md) 🏦
- [31 — GITHUB_TOKEN, cost optimization, org templates](31_actions_token_cost_templates.md) 🏦

## Part G — GHAS (GitHub Advanced Security)

- [32 — Secret scanning + push protection](32_ghas_secret_scanning.md) 🏦
- [33 — CodeQL + custom queries + Copilot Autofix](33_ghas_codeql_autofix.md) 🏦
- [34 — Dependabot + dependency review](34_ghas_dependabot.md) 🏦
- [35 — SBOM + SLSA + Artifact Attestations + Sigstore](35_ghas_sbom_slsa_attestations.md) 🏦

## Part H — Compliance & audit

- [36 — SAML SSO, SCIM, IP allow lists, audit logs](36_compliance_sso_scim_audit.md) 🏦
- [37 — SR 11-7 + immutable audit trails + separation of duties](37_compliance_sr117_audit.md) 🏦

## Part I — Git/GitHub for ML

- [38 — Notebook discipline (jupytext, nbdime, nbstripout, ReviewNB)](38_notebook_discipline.md) ⭐
- [39 — Git LFS + DVC + lakeFS + HF Hub](39_lfs_dvc_lakefs_hf.md)
- [40 — Pre-commit ecosystem + reproducibility + notebook→module](40_precommit_reproducibility_refactor.md) ⭐

## Part J — MLOps with GitHub Actions

- [41 — CI for ML: lint, test, type-check](41_mlops_ci_for_ml.md) ⭐
- [42 — Model validation gates (fairness, bias, drift)](42_mlops_validation_gates.md) ⭐🏦
- [43 — MLflow Model Registry + SageMaker Pipelines from Actions](43_mlops_mlflow_sagemaker.md) ⭐
- [44 — Champion/challenger, shadow, A/B, feature store](44_mlops_champion_challenger.md) ⭐
- [45 — Automated retraining + model rollback workflows](45_mlops_retraining_rollback.md) ⭐🏦

## Part K — AWS deployment patterns

- [46 — OIDC trust policy deep + per-env IAM scoping](46_aws_oidc_trust_policy_deep.md) ⭐
- [47 — Deploying to SageMaker, ECS/EKS, Lambda, ECR](47_aws_deploy_sagemaker_ecs_eks_lambda.md) ⭐
- [48 — CDK + CloudFormation + Terraform from Actions; cross-account](48_aws_cdk_cfn_tf_cross_account.md) ⭐

## Part L — Jenkins

- [49 — Jenkins architecture + Jenkinsfile (declarative vs scripted)](49_jenkins_architecture_jenkinsfile.md) ⭐
- [50 — Multibranch + GitHub webhooks + shared libraries](50_jenkins_multibranch_shared_libs.md) ⭐
- [51 — Credentials + GitHub→Jenkins→AWS + Capital One pattern](51_jenkins_credentials_ghaws.md) ⭐🏦

## Part M — GitHub Apps & automation

- [52 — GitHub Apps, webhooks, gh CLI, GraphQL/REST](52_apps_webhooks_ghcli_graphql.md)

## Part N — AI coding assistants

- [53 — GitHub Copilot (IDE, Chat, PR review, gh copilot)](53_ai_copilot.md) ⭐
- [54 — Claude Code in enterprise (scoping, agentic, .agent.md, MCP)](54_ai_claude_code_enterprise.md) ⭐
- [55 — Governance, privacy, code-of-conduct for AI dev tools](55_ai_governance_privacy.md) ⭐🏦

## Part O — Capital One lens + certifications

- [56 — Capital One DevOps deep dive](56_capital_one_devops_deep.md)
- [57 — Certification roadmap (GH-900, GH-200, GH-500, GH-300, CJE)](57_cert_roadmap.md)

## Quizzes

- [`quizzes/01_git_foundations.md`](quizzes/01_git_foundations.md) — Parts A–B
- [`quizzes/02_branching_actions_core.md`](quizzes/02_branching_actions_core.md) — Parts C–E
- [`quizzes/03_actions_advanced_security.md`](quizzes/03_actions_advanced_security.md) — Parts F–H
- [`quizzes/04_mlops_aws.md`](quizzes/04_mlops_aws.md) — Parts I–K
- [`quizzes/05_jenkins_ai_capital_one.md`](quizzes/05_jenkins_ai_capital_one.md) — Parts L–O

## Code artifacts

- [`code/codeowners_example`](code/codeowners_example) — CODEOWNERS exemplar with team routing
- [`code/precommit_ml.yaml`](code/precommit_ml.yaml) — pre-commit config for ML repos
- [`code/reusable_python_ci.yml`](code/reusable_python_ci.yml) — reusable workflow for Python CI
- [`code/composite_setup_python.yml`](code/composite_setup_python.yml) — composite action for Python setup
- [`code/oidc_aws_deploy.yml`](code/oidc_aws_deploy.yml) — OIDC to AWS + SageMaker deploy workflow
- [`code/oidc_aws_trust_policy.json`](code/oidc_aws_trust_policy.json) — IAM trust policy template
- [`code/jenkinsfile_declarative_ml.groovy`](code/jenkinsfile_declarative_ml.groovy) — declarative Jenkinsfile for ML
- [`code/jenkins_shared_lib_skeleton/`](code/jenkins_shared_lib_skeleton/) — shared library directory layout
- [`code/codeql_python_workflow.yml`](code/codeql_python_workflow.yml) — CodeQL advanced setup for Python ML
