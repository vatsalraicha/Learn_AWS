# Topic 07 — Git, GitHub & DevOps for AI/ML Engineers (Capital One lens)

> **Audience:** Senior AI/ML Engineer (Optum, Azure shop) preparing for **Sr Lead AI/ML Engineer at Capital One** (AWS-native, regulated finance, Snowflake + Databricks + EKS-KServe spine, Jenkins + GitHub Enterprise + GitHub Actions hybrid CI/CD).
>
> **Goal:** A teaching corpus where every module is research-backed and oriented to the actual stack a Sr Lead operates in a top-tier US bank: trunk-based development, signed commits, CODEOWNERS-routed reviews, GHAS-gated PRs, Jenkins shared libraries, GitHub Actions reusable workflows, OIDC into AWS, SR 11-7-grade audit trails for model deployments.
>
> **Branch:** `topic-07-git-github-devops`
>
> **Last updated:** 2026-05-21

---

## Promise

Same standard as Topic 04, 05, 06. Research-before-writing. Citable facts in [`FACTS.md`](FACTS.md) with last-verified dates. Primary sources (GitHub Docs, AWS blogs, Capital One tech blog, Jenkins docs, DORA, SLSA, SR 11-7) summarized under [`../../research_inputs/07_git_github_devops/`](../../research_inputs/07_git_github_devops/).

The **unifying thread** for this topic is:

> *How does a regulated bank ship AI/ML code from a developer's laptop to a SageMaker endpoint, with every step audit-trailed, every artifact signed, every credential ephemeral, and nothing manual on the prod path?*

That thread runs through every module. Modules tagged 🏦 are bank-specific or compliance-driven. Modules tagged ⭐ are the highest-leverage ones for the Sr Lead role.

---

## Learning path (57 modules in 15 parts)

| # | Module | Why it matters |
|---|--------|----------------|
| **Part A — Git fundamentals (1–7)** | | |
| 1 | [Git history, architecture & object model](01_git_architecture_objects.md) | The mental model: blobs/trees/commits/refs is what every higher-level concept resolves to |
| 2 | [Configuration, identity & signing setup (SSH + GPG)](02_config_identity_signing.md) | 🏦 Required signed commits start here |
| 3 | [Core workflows: init/clone/add/commit/status/log/diff + .gitignore/.gitattributes](03_core_workflows.md) | The 80% of git you do daily |
| 4 | [Branching, merging, rebasing, conflict resolution](04_branching_merging_rebasing.md) | The most-misunderstood Git topic. Rebase vs merge — pick deliberately |
| 5 | [Remote operations: fetch/pull/push, forks, upstream sync](05_remotes_forks_upstream.md) | InnerSource depends on this being reflexive |
| 6 | [Undo & recovery: reset/revert/restore, reflog, blame, bisect](06_undo_recovery.md) | When prod is on fire, you reach for reflog. Know it cold |
| 7 | [Stash, tags, hooks, submodules, worktrees](07_stash_tags_hooks_submodules_worktrees.md) | The "rest of git": when each is the right tool |
| **Part B — GitHub collaboration (8–14)** | | |
| 8 | [Repository setup standards (README, LICENSE, CONTRIBUTING, CoC, templates)](08_repo_setup_standards.md) | What every new repo gets on day 1; bank repos have extras |
| 9 | [Issues, projects, milestones, labels](09_issues_projects_milestones.md) | The work-management layer; integrates with Jira at most banks |
| 10 | [Pull requests, code review, merge strategies (merge/squash/rebase)](10_prs_code_review_merge.md) | The change unit. Suggestions, approvals, requested changes |
| 11 | [🏦 Branch protection, Rulesets, CODEOWNERS](11_branch_protection_rulesets_codeowners.md) | The governance backbone — what stops a junior from merging straight to main |
| 12 | [Authentication: PAT (classic vs fine-grained), SSH, GPG/SSH commit signing](12_auth_pat_ssh_signing.md) | 🏦 The credential surface you have to get right |
| 13 | [Organizations, teams, permissions, repo roles](13_orgs_teams_permissions.md) | Enterprise GitHub is org-shaped; understanding the model |
| 14 | [GitHub CLI (`gh`) fundamentals](14_gh_cli_fundamentals.md) | The CLI is faster than the UI for 90% of operations |
| **Part C — Branching strategies (15–16)** | | |
| 15 | [⭐ Git Flow vs GitHub Flow vs Trunk-based development](15_branching_strategies.md) | Capital One = trunk-based + feature flags; you must know why |
| 16 | [Feature flags, release branching, InnerSource](16_feature_flags_innersource.md) | How to ship unfinished features safely |
| **Part D — Repository architecture (17–19)** | | |
| 17 | [Monorepo vs polyrepo trade-offs](17_monorepo_vs_polyrepo.md) | A first-principles call most teams get wrong |
| 18 | [Python ML repo structure (pyproject.toml, src layout, packaging)](18_python_ml_repo_structure.md) | The 2026 standard layout for production Python |
| 19 | [Repo templates, ADRs, docs, conventional commits, release-please](19_templates_adr_docs_conventional_commits.md) | InnerSource standardization at scale |
| **Part E — GitHub Actions Core (20–25)** | | |
| 20 | [Workflow YAML, events, triggers](20_actions_workflow_events.md) | The grammar of every workflow |
| 21 | [Jobs, steps, runners (GitHub-hosted vs self-hosted)](21_actions_jobs_steps_runners.md) | The execution model |
| 22 | [Marketplace actions, expressions, contexts, conditionals](22_actions_marketplace_expressions.md) | Where the leverage comes from; how to be safe |
| 23 | [Variables, secrets, env scoping](23_actions_vars_secrets_env.md) | The credential surface inside a workflow |
| 24 | [Outputs, needs, concurrency, timeouts, continue-on-error](24_actions_outputs_needs_concurrency.md) | Job orchestration primitives |
| 25 | [Caching, artifacts, matrix builds, debugging](25_actions_cache_artifacts_matrix.md) | Speed + breadth + observability |
| **Part F — GitHub Actions Advanced (26–31)** | | |
| 26 | [⭐ Reusable workflows (`workflow_call`)](26_actions_reusable_workflows.md) | The Sr Lead pattern. Org-wide standardization |
| 27 | [⭐ Composite + custom actions (JS, Docker)](27_actions_composite_custom.md) | Build the things you reuse across repos |
| 28 | [⭐ Self-hosted runners + ARC + GPU runners](28_actions_self_hosted_arc_gpu.md) | Capital One has in-house K8s ML; ARC is the path |
| 29 | [⭐ OIDC to AWS — the canonical pattern](29_actions_oidc_aws.md) | THE pattern. No long-lived keys. Per-env role scoping |
| 30 | [🏦 Environments: protection rules, required reviewers, deployment branches, scoped secrets](30_actions_environments_protection.md) | The prod-gate primitive |
| 31 | [🏦 GITHUB_TOKEN scoping, cost optimization, org workflow templates](31_actions_token_cost_templates.md) | The platform-engineer lens |
| **Part G — GitHub Advanced Security (32–35)** | | |
| 32 | [🏦 Secret scanning + push protection](32_ghas_secret_scanning.md) | Stop leaks at the door |
| 33 | [🏦 CodeQL + custom queries + SARIF + Copilot Autofix](33_ghas_codeql_autofix.md) | The deepest SAST in the ecosystem |
| 34 | [🏦 Dependabot + dependency review action](34_ghas_dependabot.md) | Supply-chain hygiene at the dependency level |
| 35 | [🏦 SBOM + SLSA + Artifact Attestations + Sigstore](35_ghas_sbom_slsa_attestations.md) | Supply-chain attestation; required for EU CRA from 2027 |
| **Part H — Compliance & audit (36–37)** | | |
| 36 | [🏦 SAML SSO, SCIM, IP allow lists, audit logs](36_compliance_sso_scim_audit.md) | Enterprise identity + immutable history |
| 37 | [🏦 SR 11-7 + immutable audit trails + separation of duties for ML deployments](37_compliance_sr117_audit.md) | The regulator-grade lens — model risk management |
| **Part I — Git/GitHub for ML projects (38–40)** | | |
| 38 | [⭐ Notebook discipline (jupytext, nbdime, nbstripout, ReviewNB)](38_notebook_discipline.md) | The single biggest delta between research ML and production ML repos |
| 39 | [Git LFS + DVC + lakeFS + Hugging Face Hub](39_lfs_dvc_lakefs_hf.md) | Where data and models live when they're too big for git |
| 40 | [⭐ Pre-commit ecosystem + reproducibility + notebook→module refactoring](40_precommit_reproducibility_refactor.md) | Production code lives in modules, not notebooks |
| **Part J — MLOps with GitHub Actions (41–45)** | | |
| 41 | [⭐ CI for ML: lint, test, type-check, notebook test](41_mlops_ci_for_ml.md) | What "green CI" means when your code trains models |
| 42 | [⭐🏦 Model validation gates (fairness, bias, drift) in CI/CD](42_mlops_validation_gates.md) | SR 11-7 + fair-lending compliance as code |
| 43 | [⭐ MLflow Model Registry + SageMaker Pipelines from Actions](43_mlops_mlflow_sagemaker.md) | The registry-promotion pattern |
| 44 | [⭐ Champion/challenger, shadow, A/B, feature store integration](44_mlops_champion_challenger.md) | Safe rollout patterns |
| 45 | [⭐🏦 Automated retraining triggers + model rollback workflows](45_mlops_retraining_rollback.md) | Compliance-grade rollback in <5 min |
| **Part K — AWS deployment patterns (46–48)** | | |
| 46 | [⭐ OIDC trust policy + configure-aws-credentials@v4 + per-env IAM role scoping](46_aws_oidc_trust_policy_deep.md) | The trust-policy patterns Capital One actually uses |
| 47 | [⭐ Deploying to SageMaker (endpoints, batch, pipelines), ECS/EKS, Lambda, ECR](47_aws_deploy_sagemaker_ecs_eks_lambda.md) | The deploy targets you'll touch |
| 48 | [⭐ CDK + CloudFormation + Terraform from Actions, cross-account](48_aws_cdk_cfn_tf_cross_account.md) | Capital One uses CDK heavily; cross-account is mandatory |
| **Part L — Jenkins (49–51)** | | |
| 49 | [⭐ Jenkins architecture + Jenkinsfile (declarative vs scripted)](49_jenkins_architecture_jenkinsfile.md) | The other half of Capital One's CI/CD reality |
| 50 | [⭐ Multibranch + GitHub webhooks + shared libraries](50_jenkins_multibranch_shared_libs.md) | The Capital One shared-library pattern |
| 51 | [⭐🏦 Credentials, GitHub→Jenkins→AWS handoffs, the Capital One pattern](51_jenkins_credentials_ghaws.md) | The end-to-end CI/CD picture |
| **Part M — GitHub Apps & automation (52)** | | |
| 52 | [GitHub Apps, webhooks, gh CLI scripting, GraphQL vs REST](52_apps_webhooks_ghcli_graphql.md) | When the platform team needs more than Actions |
| **Part N — AI coding assistants in enterprise (53–55)** | | |
| 53 | [⭐ GitHub Copilot (IDE, Chat, PR review, `gh copilot`)](53_ai_copilot.md) | The most-used AI dev tool in industry |
| 54 | [⭐ Claude Code in enterprise (scoping, agentic workflows, `.agent.md`, MCP)](54_ai_claude_code_enterprise.md) | The agentic-coding tool C1 is rolling out |
| 55 | [⭐🏦 Governance, privacy, code-of-conduct for AI dev tools](55_ai_governance_privacy.md) | What you must internalize before touching prompts |
| **Part O — Capital One lens + certifications (56–57)** | | |
| 56 | [Capital One DevOps deep — the public stack (see also CAPITAL_ONE.md)](56_capital_one_devops_deep.md) | The companion to [`CAPITAL_ONE.md`](CAPITAL_ONE.md) |
| 57 | [Certification roadmap (GH-900, GH-200, GH-500, GH-300, CJE)](57_cert_roadmap.md) | The credentials that map to this role |

## Companion files

- [`FACTS.md`](FACTS.md) — atomic citable facts (Git versions, Actions limits, GHAS pricing, runner specs, Jenkins LTS, Copilot tiers, SR 11-7 reference, cert metadata)
- [`CAPITAL_ONE.md`](CAPITAL_ONE.md) — Capital One DevOps dossier (Jenkins scale, singular pipeline, Hygieia, Cloud Custodian, trunk-based)
- [`00_Table_Of_Contents.md`](00_Table_Of_Contents.md) — master index of all modules + companion files + quizzes + code
- [`quizzes/`](quizzes/) — 5 quizzes grouped per part-block
- [`code/`](code/) — example workflows, composite action, reusable workflow, Jenkinsfile + shared library skeleton, CODEOWNERS exemplar, pre-commit config, OIDC trust policy JSON, SageMaker deploy workflow
- [`../../research_inputs/07_git_github_devops/`](../../research_inputs/07_git_github_devops/) — research summary + Capital One dossier

## How to use this

1. **Modules 1–7** are the Git mental model. Skim if you're already fluent, but at least read module 1 (object model) and module 6 (recovery) — those are where senior engineers earn their stripes.
2. **Modules 8–14** are GitHub collaboration. Module 11 (branch protection / Rulesets / CODEOWNERS) is the single most-tested topic in real interviews.
3. **Modules 15–19** are the workflow / architecture block. Skim 15 if you've done trunk-based; read 17 (mono vs poly) carefully — most interview teams expect a strong opinion.
4. **Modules 20–31** are the GitHub Actions backbone. **Modules 26 (reusable workflows) and 29 (OIDC to AWS) are the two highest-ROI modules in the entire topic for Capital One.**
5. **Modules 32–37** are the security + compliance block. All 🏦. Read all of them.
6. **Modules 38–40** are notebook + ML repo hygiene. Module 40 is what separates a researcher from a Lead.
7. **Modules 41–48** are MLOps + AWS deployment. The core of the role.
8. **Modules 49–51** are Jenkins. Don't skip them — Capital One runs ~500k Jenkins pipelines.
9. **Module 52** is the power-user / platform-engineer module.
10. **Modules 53–55** are AI assistants. Capital One has a dedicated team governing these tools — module 55 is the one you cannot skip.
11. **Modules 56–57** wrap with the Capital One lens and certs.

## Scope notes

- **Cutoff**: 2025 → May 2026. Git 2.54.0, GHAS unbundled (Apr 2025), Actions Security Roadmap 2026, Copilot usage-based billing (Jun 2026), Required Reviewer Rule for Rulesets (Feb 2026), Claude Code Enterprise (early 2026). [`FACTS.md`](FACTS.md) carries last-verified dates per fact.
- **Cross-references**: Modules link heavily to **Topic 04** (AWS — for SageMaker, IAM, networking) and **Topic 05** (Docker/K8s — for ARC, containerized actions, KServe). When a concept is fully covered there, we link instead of re-deriving.
- **Stack convention**: GitHub Enterprise Cloud + GitHub Actions + Jenkins LTS 2.504.x + ARC on EKS + AWS-only deploy targets. Cross-cloud examples (GCP, Azure) appear only where relevant for comparison.
- **Cert mapping**: in module 57.

## Stack baseline (additions to the project `.venv`)

```
pre-commit                # multi-language git hook framework
nbstripout                # strip notebook outputs at commit
nbdime                    # semantic notebook diffs
jupytext                  # notebook ↔ .py / .md pairing
dvc[s3]                   # data version control (S3 remote)
mlflow                    # model registry + tracking (Topic 04 cross-ref)
boto3                     # AWS SDK (used in GH-Actions Lambda/SageMaker examples)
aws-cdk-lib               # CDK constructs (used in module 48 examples)
gh                        # GitHub CLI (install via brew, not pip)
act                       # run GH Actions locally (install via brew)
gitleaks                  # secret scanner you can run locally
trivy                     # SCA + container scanner
detect-secrets            # Yelp's secret scanner (pre-commit hook)
ruff                      # Rust-based linter + formatter
mypy                      # static typing
bandit                    # Python security linter
```

System tools (install via brew):

```
brew install git gh act pre-commit gitleaks trivy
```

## Research provenance

Built from research notes under [`../../research_inputs/07_git_github_devops/`](../../research_inputs/07_git_github_devops/) plus primary sources (GitHub Docs, AWS blog posts, Capital One tech blog, Jenkins docs, DORA, SLSA, Sigstore, NIST SP 800-218, SR 11-7).
