# Module 19 — CI/CD with Asset Bundles + Terraform

> **Goal of this module:** know when to use Databricks Asset Bundles vs Terraform, what each is for, the canonical pipeline shape with OIDC federation (no PATs), environment promotion patterns, and the YAML-sprawl problem and how teams escape it.

---

## The two-tool answer

The right pattern in 2026:

- **Terraform for the platform** — workspaces, account-level resources (metastore, UC catalogs, account SPs, NCCs), networking, identity bindings.
- **Databricks Asset Bundles (DABs) for the application** — workspace-internal artifacts that ship with code: jobs, Lakeflow pipelines, notebooks, dashboards, ML experiments.

**Don't try to manage both layers from one tool.** Terraform's strength is account/cloud topology; DABs' strength is application lifecycle that follows the git repo.

---

## Databricks Asset Bundles (DABs)

### What it is

The **Databricks-blessed deployment artifact.** Replaces `dbx` (deprecated late 2023). Defined in `databricks.yml`, deploys notebooks, jobs, pipelines, ML experiments, dashboards as a **versioned bundle.**

GA April 2024 ([GA blog](https://www.databricks.com/blog/announcing-general-availability-databricks-asset-bundles)). Renamed to "Declarative Automation Bundles" in 2025 ([docs](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/)) — but the term "DABs" remains in common use.

### Project structure

```
my-bundle/
  databricks.yml          # bundle config: name, targets (dev/stage/prod), variables
  resources/
    jobs.yml              # Workflow definitions
    pipelines.yml         # Lakeflow Declarative Pipelines
    models.yml            # MLflow models
  src/
    silver/
      __init__.py
      member_month.py     # pure-Python module
    bronze/
      claims_loader.py
  notebooks/
    silver/
      member_month_runner.py  # thin notebook orchestrator
  tests/
    test_member_month.py
  pyproject.toml
  .github/workflows/
    deploy.yml
```

### Lifecycle

```
databricks bundle validate
databricks bundle deploy --target dev
databricks bundle run silver_refresh --target dev
databricks bundle deploy --target stage  (auto on main merge)
databricks bundle deploy --target prod   (manual approval)
```

CI promotes by retargeting; same bundle artifact moves through environments.

### The honest pain points

The Rabobank tech blog ([3 die-hard lessons](https://rabobank.jobs/en/techblog/3-die-hard-lessons-we-ve-learned-when-using-databricks-asset-bundles/)) and Hiflylabs ([on isolated networks](https://hiflylabs.com/blog/2025/11/20/databricks-asset-bundles-isolated-networks)) document:
- **API rate limits (HTTP 429)** on file uploads at scale
- **Basic validation feedback** — bundle validate doesn't catch all the things prod will
- **No visibility into the underlying REST calls** — when something fails you guess
- **YAML cannot loop or branch** like Terraform — you write boilerplate

**Multi-tenant gotcha:** DABs assume a workspace is pre-existing — every client/tenant requires a duplicated bundle ([Prabhakaran Kanniappan / Medium](https://medium.com/@prabhakarankanniappan/databricks-asset-bundles-why-they-break-and-how-smart-engineers-fix-them-47f94f669547)).

Thoughtworks Tech Radar placed DABs in **"Trial"** — useful but with caveats ([Thoughtworks Radar](https://www.thoughtworks.com/en-us/radar/languages-and-frameworks/databricks-asset-bundles)).

### When YAML sprawl bites

Daniel Beach: *"I don't want to be a YAML engineer any more than you do. It's one thing to have IaC (Infrastructure as Code), and another thing to have Pipelines as Code"* ([Substack](https://dataengineeringcentral.substack.com/p/simplifying-cicd-with-databricks)).

Reuse / abstraction of `job_clusters` blocks across bundles is awkward. Teams resort to:
- **YAML anchors** (basic reuse, breaks at scale)
- **Jinja templating** (treats YAML as text)
- **Cookiecutter templates** (one-time scaffolding)
- **Brickflow** (Python DSL on top of DABs — see below)

---

## Brickflow — when DABs YAML gets unwieldy

[Nike-Inc/brickflow](https://github.com/Nike-Inc/brickflow) — Pythonic DAG framework that **deploys via DABs under the hood.** ~220 stars, active 2024–2025 release cadence. Engineering page: [engineering.nike.com/brickflow](https://engineering.nike.com/brickflow/).

**Why teams pick it over plain DABs:**
- **Python > YAML for any nontrivial fan-out** — looping over 50 similar jobs in YAML is awkward; trivial in Python
- **Native testing seams** — pytest the DAG construction
- **Opinionated project structure** — less time deciding, more time shipping

**When to use:**
- Bundles getting >500 lines of YAML
- Many similar jobs that differ only in parameters (per-tenant, per-source)
- Teams that prefer Python over YAML for "logic-shaped" deployment config

**When DABs alone is fine:**
- Small bundles (a few jobs, one pipeline)
- Teams without dedicated platform engineering capacity

---

## Terraform — `databricks/databricks` provider

### When to use Terraform

- **Account-level resources** — metastore, workspaces, UC catalogs, account SPs, network configurations
- **Cross-workspace topology** — bind catalogs to multiple workspaces, manage NCCs
- **Treating Databricks as part of the broader Azure landing zone** — same Terraform stack as your Azure infra

### When to use DABs alongside Terraform

- **Workspace-internal artifacts** — jobs, DLT pipelines, notebooks, dashboards that ship with the application repo
- **Application lifecycle that matches release cadence** — DAB versions track app versions

### Common pattern at Optum scale

**Terraform for the platform:** `optum-databricks-platform` repo
- Workspace provisioning (per region, per business unit)
- UC metastore + initial catalog structure
- Network configuration (VNet, NSG, NCC, private endpoints)
- Service principals, OIDC federation
- Cluster policies (Module 17)

**DABs for each application:** `claims-platform-bundle`, `member-platform-bundle`, etc.
- Jobs and Lakeflow pipelines for that app
- Notebooks and dashboards
- ML experiments

This separation is the canonical 2026 pattern. **Don't try to put everything in one Terraform monorepo** — application teams need lifecycle independence from the platform team.

### Terraform provider docs and modules

- [databricks/databricks Terraform provider](https://registry.terraform.io/providers/databricks/databricks/latest/docs)
- [databricks/terraform-databricks-modules](https://github.com/databricks/terraform-databricks-modules) — reference modules for UC bootstrap, workspace deployment, mounts, jobs

---

## CI/CD pipeline shape

The canonical pipeline shape on GitHub Actions or Azure DevOps:

```
1. lint        → ruff, black, sqlfluff
2. unit        → pytest with chispa or local PySpark; runs on runner, no cluster
3. validate    → databricks bundle validate
4. integration → bundle deploy --target ci → bundle run; teardown
5. deploy-stage → bundle deploy --target stage (auto on main)
6. smoke       → run a synthetic job, check outputs
7. deploy-prod → bundle deploy --target prod (manual approval)
```

### Auth: OIDC federation (no PATs)

Databricks supports OIDC federation. **GitHub Actions / Azure DevOps pipelines authenticate to Databricks without long-lived PATs.** The 2025+ recommended CI/CD auth pattern.

GitHub Actions example:

```yaml
# .github/workflows/deploy.yml
name: Deploy claims bundle
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write   # needed for OIDC
      contents: read
    steps:
      - uses: actions/checkout@v4
      
      - name: Login to Azure via OIDC
        uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
      
      - uses: databricks/setup-cli@main
      
      - name: Validate bundle
        run: databricks bundle validate --target stage
        env:
          DATABRICKS_HOST: ${{ vars.DATABRICKS_STAGE_HOST }}
          DATABRICKS_AUTH_TYPE: azure-oidc
      
      - name: Deploy bundle to stage
        run: databricks bundle deploy --target stage
        env:
          DATABRICKS_HOST: ${{ vars.DATABRICKS_STAGE_HOST }}
          DATABRICKS_AUTH_TYPE: azure-oidc
      
      - name: Smoke test
        run: databricks bundle run claims_silver_refresh --target stage
        env:
          DATABRICKS_HOST: ${{ vars.DATABRICKS_STAGE_HOST }}
          DATABRICKS_AUTH_TYPE: azure-oidc
```

The Entra Service Principal is configured to trust the GHA OIDC issuer; no client secret needed. Token rotation is handled by Entra.

For self-hosted runners inside the regulated VNet (healthcare standard), the runner has direct network access to the workspace; the OIDC flow is the same.

---

## Environment promotion patterns

| Pattern | Isolation | Cost | Best for |
|---|---|---|---|
| **Same workspace, different UC catalogs** (`dev_catalog`, `prod_catalog`) | Weak — shared compute, shared cluster policies | Low | Small teams, early lifecycle |
| **Different workspaces, same subscription** | Medium — separate quota, separate UC schemas under one metastore | Medium | Most enterprises |
| **Different workspaces, different subscriptions** | Strong — separate billing, separate Entra app regs, separate networks | High | Regulated (Optum-grade healthcare) |

### Optum recommendation

**Separate-subscription pattern for prod.** Dev and stage can share a subscription. UC metastore can still be one per region — catalogs are the isolation boundary.

Pattern:
```
Subscription:  optum-databricks-nonprod (dev + stage workspaces)
Subscription:  optum-databricks-prod (prod-general workspace, prod-phi workspace)
Subscription:  optum-databricks-prod-dr (DR region workspaces)
```

The separate-subscription split for prod gives:
- **Separate billing** — prod cost rolls up cleanly
- **Separate Entra app registrations** — different SPs, easier to lock down
- **Separate network blast radius** — a bad change in nonprod can't reach prod
- **Compliance isolation** — auditor sees prod as its own envelope

---

## Testing in CI

### Unit tests — fast, no cluster

```python
# tests/silver/test_member_month.py
import pytest
from chispa.dataframe_comparer import assert_df_equality
from src.silver.member_month import build_member_month

@pytest.fixture(scope="session")
def spark():
    from pyspark.sql import SparkSession
    return (SparkSession.builder
              .master("local[2]")
              .appName("test")
              .config("spark.sql.warehouse.dir", "/tmp/spark-warehouse")
              .getOrCreate())

def test_basic_member_month(spark, tmp_path):
    # Build small fixture DataFrames
    # Call build_member_month
    # Assert with chispa
    pass
```

`pytest` + `chispa` for DataFrame equality. **PySpark in local mode on the runner.** Fast (<2 min). **Required.**

### Integration tests — ephemeral target on serverless

```yaml
# CI step
- name: Integration tests
  run: |
    databricks bundle deploy --target ci
    databricks bundle run silver_refresh --target ci
    pytest tests/integration/  # validates the result table
    databricks bundle destroy --target ci  # teardown
```

Run on **serverless job compute** (cheaper than spinning a classic cluster). 5–15 min.

### Data quality tests

- **`dbt test`** for SQL-shaped transformations
- **DLT/Lakeflow expectations** (`@dp.expect_or_drop`) inline in pipelines
- **Lakehouse Monitoring** in a downstream job for drift detection

### Contract tests

- **Schema contracts via `pydantic`** for explicit input shapes
- **Delta `CHECK` constraints** for value-range invariants
- **Column-level lineage assertions** via `system.access.column_lineage` queries

### What teams skip and why

- **Integration tests against real Delta tables** — too slow, devs hate the wait. Skipped → caught in stage. Acceptable if stage has good monitoring.
- **DR-failover drills** — quarterly, often skipped after the first one. **Optum-grade orgs cannot skip these for HIPAA audit reasons.**
- **Cross-region read tests** — assumed to "just work" because of GRS. Often broken at Private DNS layer.

---

## Multi-target bundle config

Real-world `databricks.yml` for a multi-target bundle:

```yaml
bundle:
  name: claims_platform

include:
  - resources/*.yml

variables:
  catalog:
    description: UC catalog for the bundle's data
    default: dev_claims
  env:
    description: Environment label
    default: dev

targets:
  dev:
    mode: development
    workspace:
      host: https://adb-12345.azuredatabricks.net
    variables:
      catalog: dev_claims
      env: dev
  
  stage:
    mode: production
    workspace:
      host: https://adb-67890.azuredatabricks.net
    variables:
      catalog: stage_claims
      env: stage
    permissions:
      - level: CAN_MANAGE
        group_name: dataeng-claims
  
  prod:
    mode: production
    workspace:
      host: https://adb-99999.azuredatabricks.net
    variables:
      catalog: prod_phi_claims
      env: prod
    permissions:
      - level: CAN_MANAGE
        group_name: dataeng-claims-prod
      - level: CAN_RUN
        group_name: oncall-platform-admins
```

The same bundle artifact deploys to all three; only variables and workspace targets differ.

---

## Production patterns

### Pattern: change-controlled prod deploy with manual approval

```yaml
# .github/workflows/deploy-prod.yml
name: Deploy to prod
on:
  workflow_dispatch:  # manual trigger only
  
jobs:
  approval:
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://adb-99999.azuredatabricks.net
    # the 'environment: production' triggers the approval gate
    steps:
      - uses: actions/checkout@v4
      - uses: databricks/setup-cli@main
      - run: databricks bundle deploy --target prod
        env:
          DATABRICKS_AUTH_TYPE: azure-oidc
```

GitHub Environments give you the manual-approval gate. For Optum-grade prod, the approver is an on-call platform admin or a designated change-management engineer.

### Pattern: hotfix without breaking the promotion train

When a prod bug needs an immediate fix bypassing the normal stage gate:

1. Branch from the prod tag, not from main
2. Apply the minimum fix
3. Deploy to prod via emergency channel (still requires approval)
4. Cherry-pick the fix back into main
5. Re-deploy main to stage to re-establish the promotion train

This avoids the anti-pattern of "merge a bunch of WIP into main to ship a hotfix."

---

## When NOT to use these patterns

- **DABs for non-Databricks workloads** — they're Databricks-specific. Don't shoehorn other infra into them.
- **Terraform for application code** — Terraform's strength is infrastructure topology, not "this notebook runs on Tuesday."
- **Single-environment "we'll just deploy to prod"** — works for solo experiments; fails the moment a second person joins.
- **PAT-based auth in 2026** — OIDC federation is the standard; PATs are a tech-debt artifact.

---

## Sanity check

1. When do you use Terraform vs DABs?
2. Why does Brickflow exist, and when would a team adopt it over plain DABs?
3. What does OIDC federation give you that PAT-based auth doesn't?
4. Walk through the canonical CI/CD pipeline shape — 7 steps.
5. Why is the separate-subscription environment-promotion pattern the right answer for Optum's prod?
6. What testing layers belong in CI, and which do teams skip (rightly or wrongly)?

---

## Further reading

- [Databricks Asset Bundles GA blog](https://www.databricks.com/blog/announcing-general-availability-databricks-asset-bundles)
- [DABs / Declarative Automation Bundles docs](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/)
- [Bundle examples — Databricks GitHub](https://github.com/databricks/bundle-examples)
- [databricks/databricks Terraform provider](https://registry.terraform.io/providers/databricks/databricks/latest/docs)
- [Terraform databricks modules](https://github.com/databricks/terraform-databricks-modules)
- [Nike-Inc/brickflow](https://github.com/Nike-Inc/brickflow)
- [databricks/cli (Databricks CLI)](https://github.com/databricks/cli)
- [Workload Identity Federation for CI/CD](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/auth/oauth-m2m)
- [Daniel Beach — Simplifying CI/CD with Databricks](https://dataengineeringcentral.substack.com/p/simplifying-cicd-with-databricks)
- [Rabobank — 3 die-hard DABs lessons](https://rabobank.jobs/en/techblog/3-die-hard-lessons-we-ve-learned-when-using-databricks-asset-bundles/)
- [newmathdata — DABs vs Terraform deployment guide](https://newmathdata.com/blog/databricks-asset-bundles-dabs-vs-terraform-deployment-guide/)
