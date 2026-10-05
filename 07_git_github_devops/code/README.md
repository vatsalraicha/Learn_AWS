# Topic 07 — Code artifacts

Companion code samples to the Topic 07 modules. Each is a self-contained, copy-pasteable starting point. Adapt the `capitalone/...` placeholders to your org / repo names.

## Files

| File | Companion module(s) | What |
|---|---|---|
| [`codeowners_example`](codeowners_example) | [11](../11_branch_protection_rulesets_codeowners.md) | CODEOWNERS template with bank-grade routing patterns |
| [`precommit_ml.yaml`](precommit_ml.yaml) | [40](../40_precommit_reproducibility_refactor.md) | Full pre-commit config for Python ML repos |
| [`reusable_python_ci.yml`](reusable_python_ci.yml) | [26](../26_actions_reusable_workflows.md), [41](../41_mlops_ci_for_ml.md) | Reusable workflow for Python CI (called from any repo) |
| [`composite_setup_python.yml`](composite_setup_python.yml) | [27](../27_actions_composite_custom.md) | Composite action: setup Python + uv + cache |
| [`oidc_aws_deploy.yml`](oidc_aws_deploy.yml) | [29](../29_actions_oidc_aws.md), [47](../47_aws_deploy_sagemaker_ecs_eks_lambda.md) | Full workflow: OIDC → AWS → SageMaker endpoint update + smoke test |
| [`oidc_aws_trust_policy.json`](oidc_aws_trust_policy.json) | [29](../29_actions_oidc_aws.md), [46](../46_aws_oidc_trust_policy_deep.md) | IAM trust policy template with 5 patterns commented |
| [`jenkinsfile_declarative_ml.groovy`](jenkinsfile_declarative_ml.groovy) | [49](../49_jenkins_architecture_jenkinsfile.md), [50](../50_jenkins_multibranch_shared_libs.md) | Capital One-style declarative Jenkinsfile for ML service |
| [`jenkins_shared_lib_skeleton/vars/c1.groovy`](jenkins_shared_lib_skeleton/vars/c1.groovy) | [50](../50_jenkins_multibranch_shared_libs.md) | Jenkins shared library entry point with build/deploy steps |
| [`codeql_python_workflow.yml`](codeql_python_workflow.yml) | [33](../33_ghas_codeql_autofix.md) | CodeQL advanced setup + semgrep + trivy SARIF upload |

## How to use

1. Copy the relevant file into your repo at the path indicated in the module.
2. Replace `capitalone`, `ORG`, `REPO`, `AWS_ACCOUNT_ID`, etc. with your values.
3. Cross-reference the companion module for the conceptual explanation.

## Conventions

- Action pins are at the major-version tag (`@v4`, `@v6`) — change to specific SHAs for production.
- Placeholder org name throughout is `capitalone` — substitute your own.
- All examples assume the OIDC trust + Environment setup described in modules 29, 30, 46.
- Python examples assume `uv` + `pyproject.toml` (see [module 18](../18_python_ml_repo_structure.md)).
- Jenkins shared library examples assume the IRSA + K8s-agent pattern (see [module 51](../51_jenkins_credentials_ghaws.md)).
