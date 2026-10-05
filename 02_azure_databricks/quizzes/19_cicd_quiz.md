# Quiz — Module 19: CI/CD with Asset Bundles + Terraform

## Recall

**Q1.** When do you use Terraform vs DABs in the canonical 2026 Databricks deployment pattern?

<details><summary>Answer</summary>

**Terraform for the platform:**
- Account-level resources (metastore, UC catalogs at structure level, account SPs, NCCs, network configurations)
- Cross-workspace topology (catalog bindings, NCC management)
- Workspaces themselves
- Treating Databricks as part of the broader Azure landing zone

**DABs for the application:**
- Workspace-internal artifacts that ship with the application repo: jobs, Lakeflow pipelines, notebooks, dashboards, ML experiments
- Application lifecycle that matches release cadence

**Don't manage both layers from one tool.** Terraform's strength is account/cloud topology; DABs' strength is application lifecycle following the git repo. The canonical pattern is **separate repos**: `optum-databricks-platform` (Terraform) + `claims-platform-bundle`, `member-platform-bundle`, etc. (DABs).
</details>

**Q2.** What is OIDC federation for Databricks CI/CD, and why is it the recommended pattern over PATs in 2026?

<details><summary>Answer</summary>

**OIDC federation** = the CI runner authenticates to Databricks via the Entra ID identity layer, without storing a long-lived PAT.

The flow:
1. GitHub Actions / Azure DevOps runner has an OIDC identity (issued by GitHub or ADO).
2. Entra Service Principal is configured to trust that issuer.
3. Pipeline authenticates as the SP via `azure-oidc` auth method on the Databricks CLI.

**Why it's better than PATs:**
- **No long-lived secret** — no PAT to rotate, no PAT to leak in logs.
- **Token rotation handled by Entra** — automatic and short-lived.
- **Audit trail in Entra + Databricks** — both sides know what authed.
- **Per-environment SPs** — each target (dev/stage/prod) can have a distinct SP with appropriate scope.
- **Procurement / security teams strongly prefer it** — PATs are a finding waiting to happen.

**Setup:** the Entra SP federation config is one-time; the GHA workflow uses `permissions: id-token: write` and `DATABRICKS_AUTH_TYPE: azure-oidc`. Module 19 has the YAML.
</details>

---

## Apply

**Q3.** Write the GitHub Actions workflow for a 4-stage deployment: lint → unit test → deploy-stage (auto on main) → deploy-prod (manual approval gate). Use OIDC federation.

<details><summary>Answer</summary>

```yaml
# .github/workflows/deploy.yml
name: Claims Platform Deploy

on:
  push:
    branches: [main]
  workflow_dispatch:  # for manual prod promotions

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install ruff black sqlfluff
      - run: ruff check src/ tests/
      - run: black --check src/ tests/
      - run: sqlfluff lint sql/

  unit-test:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - uses: actions/setup-java@v4
        with: { java-version: '17', distribution: 'temurin' }
      - run: pip install -r requirements-test.txt
      - run: pytest tests/unit/ --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v4

  deploy-stage:
    runs-on: ubuntu-latest
    needs: unit-test
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v4
      - name: Login to Azure via OIDC
        uses: azure/login@v2
        with:
          client-id:       ${{ secrets.AZURE_CLIENT_ID_STAGE }}
          tenant-id:       ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID_STAGE }}
      - uses: databricks/setup-cli@main
      - run: databricks bundle validate --target stage
        env:
          DATABRICKS_HOST: ${{ vars.DATABRICKS_STAGE_HOST }}
          DATABRICKS_AUTH_TYPE: azure-oidc
      - run: databricks bundle deploy --target stage
        env:
          DATABRICKS_HOST: ${{ vars.DATABRICKS_STAGE_HOST }}
          DATABRICKS_AUTH_TYPE: azure-oidc
      - name: Smoke test
        run: databricks bundle run claims_silver_refresh --target stage
        env:
          DATABRICKS_HOST: ${{ vars.DATABRICKS_STAGE_HOST }}
          DATABRICKS_AUTH_TYPE: azure-oidc

  deploy-prod:
    runs-on: ubuntu-latest
    needs: deploy-stage
    if: github.event_name == 'workflow_dispatch'
    environment:
      name: production    # GitHub Environment with required reviewers
      url: https://adb-99999.azuredatabricks.net
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v4
      - name: Login to Azure via OIDC
        uses: azure/login@v2
        with:
          client-id:       ${{ secrets.AZURE_CLIENT_ID_PROD }}
          tenant-id:       ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID_PROD }}
      - uses: databricks/setup-cli@main
      - run: databricks bundle deploy --target prod
        env:
          DATABRICKS_HOST: ${{ vars.DATABRICKS_PROD_HOST }}
          DATABRICKS_AUTH_TYPE: azure-oidc
```

**Key choices:**
- **Separate Azure SPs per environment** (`AZURE_CLIENT_ID_STAGE`, `AZURE_CLIENT_ID_PROD`) — each scoped to its workspace
- **Separate subscriptions per env** matches the recommended Optum-prod pattern
- **GitHub Environment "production"** triggers the approval gate (configure required reviewers in repo settings)
- **`workflow_dispatch`** for manual prod trigger; auto-deploys to stage on main merge
- **Smoke test on stage** validates the deploy worked before opening the prod gate
- **No PATs anywhere** — OIDC federation throughout
</details>

---

## Diagnose

**Q4.** A team's DABs deploy is intermittently failing with HTTP 429 errors during the file upload phase. The bundle has 200+ notebooks. What's happening, and what would you do?

<details><summary>Answer</summary>

**Root cause:** Databricks API rate limits. DABs uploads files individually via REST; for 200+ files, the bursts hit per-account or per-workspace rate limits. Documented in the [Rabobank tech blog](https://rabobank.jobs/en/techblog/3-die-hard-lessons-we-ve-learned-when-using-databricks-asset-bundles/) as one of the "3 die-hard lessons."

**Diagnosis:**
1. **Check the failing pipeline log** for HTTP 429 (rate limited) errors.
2. **Count the bundle's file count** via `find src/ notebooks/ resources/ -type f | wc -l`. Above ~150-200 files, rate limiting becomes likely.

**Fixes (in priority order):**

1. **Reduce file count via bundling** — package related notebooks as a single Python wheel. The bundle uploads 1 wheel + a few entry-point notebooks instead of 200 individual notebooks.

2. **Split the bundle** — if logical separation makes sense, split into per-domain bundles (claims, member, provider). Each is smaller; deploys parallel.

3. **Retry with backoff** — wrap `databricks bundle deploy` in a retry loop for the CI step:
   ```bash
   for i in {1..3}; do
     databricks bundle deploy --target stage && break
     echo "Retry $i in 60s..."
     sleep 60
   done
   ```
   This is a band-aid, not a fix.

4. **Distribute deployment time** — schedule the deploy off-peak. Other teams hitting the same workspace may be saturating the rate limit.

5. **Engage Databricks support** — if the workspace is operating at scale that systematically hits rate limits, the account team can sometimes raise the limits.

**The systemic pattern:** DABs' single-file-upload model has a scale ceiling. **For very large bundles, package as wheels + minimal entrypoint notebooks.** This is also the recommended pattern for testability — the wheel is pip-installable and pytest-able locally; the notebook is a thin orchestrator.

**Architect-level conversation:** "We're hitting DABs' rate limits because we have 200 notebooks. The fix isn't to reduce features — it's to refactor toward fewer, larger artifacts. Module 4 covers the `.py`-modules-in-`src/`-with-thin-notebook-orchestrator pattern; this is exactly the case it's designed for."

**Source:** [Rabobank — 3 die-hard DABs lessons](https://rabobank.jobs/en/techblog/3-die-hard-lessons-we-ve-learned-when-using-databricks-asset-bundles/).
</details>

---

## Defend

**Q5.** A peer says "we should manage everything (workspaces, jobs, notebooks, all of it) in one big Terraform monorepo for consistency." Defend or refute.

<details><summary>Answer</summary>

**Refute, with calibration.**

Where the peer is right:
- **Consistency has value** — one tool, one workflow, one mental model.
- **Avoiding the "Terraform AND DABs" complexity** is appealing.
- **Terraform CAN deploy notebooks and jobs** via the databricks Terraform provider.

Where the peer is wrong:
- **Lifecycle mismatch.** Workspaces change at infrastructure cadence (months); jobs change at application cadence (days). Forcing them into one repo couples the lifecycles wrong — every notebook change triggers Terraform plan against the entire infrastructure.
- **Application-team independence.** A claims-team change to their bundle shouldn't require platform-team review. Separate repos (DABs per app + Terraform for platform) give application teams autonomy.
- **DABs is Databricks-blessed for notebook/job/pipeline/dashboard lifecycle.** Using Terraform for those works but is the worse-fit tool — DABs has features (target promotion, validation, run command, smoke test) Terraform doesn't.
- **State-file blast radius.** A single Terraform monorepo has one state file. Corruption or accidental destroy affects everything. Splitting reduces blast radius.
- **Rate limits.** Terraform applies the entire plan; for 100+ jobs across 50 workspaces, this is slow and rate-limit-prone.

**The architect's pitch:**
- **Two-tool, two-repo model is the canonical 2026 pattern:**
  - `optum-databricks-platform` (Terraform) — workspaces, account topology, identity, network
  - `claims-platform-bundle` (DABs) — claims app jobs and pipelines
  - `member-platform-bundle` (DABs) — member app jobs and pipelines
  - … etc.
- **Within each, use IaC discipline** — PR review, plan output for review, automated apply.
- **Terraform for the things that change rarely; DABs for the things that change daily.**

**The "consistency" argument is the wrong frame.** Consistency at the cost of lifecycle mismatch is worse than slight tool diversity matched to actual change cadence.

**Production discipline:**
- **Document the ownership boundary** — platform team owns Terraform; application teams own DABs.
- **Document the integration points** — DABs references workspace + UC catalogs created by Terraform; Terraform doesn't deploy DABs artifacts.
- **Use `module` patterns in Terraform** to standardize workspace + cluster-policy creation across repos so application teams get a predictable platform.

**Source:** [DABs vs Terraform deployment guide](https://newmathdata.com/blog/databricks-asset-bundles-dabs-vs-terraform-deployment-guide/).
</details>
