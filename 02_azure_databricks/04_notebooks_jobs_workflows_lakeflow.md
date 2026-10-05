# Module 4 — Notebooks vs Jobs vs Workflows vs Lakeflow Declarative Pipelines

> **Goal of this module:** be able to pick the right orchestration surface for any workload, navigate the 2024–2025 rebrand from DLT to Lakeflow without confusion, and avoid the common traps (notebook code review hell, DLT-target-vs-schema confusion, silent breaking schema changes in declarative pipelines).

---

## Why this exists

Databricks ships **four overlapping orchestration surfaces**, each with its own DSL and operational shape:

1. **Notebooks** — interactive prototyping; can be run on a schedule but shouldn't be the production deployment artifact.
2. **Jobs / Workflows** — imperative, multi-task DAG of notebooks/wheels/scripts/SQL with retries, alerts, parameterization. The general-purpose orchestrator.
3. **Lakeflow Declarative Pipelines** (formerly Delta Live Tables, "DLT") — declarative, decorator-based, automatic dependency graph, automatic streaming/CDC handling, automatic data quality. The Spark-shaped ETL specialist.
4. **Lakeflow Designer** — no-code drag-and-drop with GenAI assistance, generates real Lakeflow pipelines under the hood. Public Preview from June 2025.

These are not interchangeable. The architect's job is to know when each fits, when teams reach for the wrong one (very common), and when to *combine* them (the canonical 2026 pattern is Workflows orchestrating a mix of Lakeflow pipelines and ad-hoc notebook tasks).

The 2024–2025 rebrand of DLT → "Lakeflow Declarative Pipelines (SDP — Spark Declarative Pipelines)" added taxonomy churn on top — backward compatible, but you'll see "DLT" in event log schemas, billing SKUs, and older docs while seeing "Lakeflow" in newer surfaces. Don't get confused; the underlying engine is the same.

---

## Notebooks — interactive, not production

### What they are

A Databricks notebook is either:
- **`.ipynb`** — Jupyter format, JSON, with embedded outputs; the format Databricks displays in the UI by default.
- **`.py` (or `.sql`, `.scala`)** — "Databricks-format" source notebooks that use `# Databricks notebook source` headers and `# COMMAND ----------` separators. Git-friendly. The recommended format for any notebook that lives in version control.

Both formats run identically in Databricks; the format choice is about source-control mechanics. **`.py` format is the right default for anything destined for review.**

### The code review problem

Notebooks were designed for solo iteration, not collaborative engineering. Every team that grew past ~5 engineers hits the same problems:

- **`.ipynb` JSON diffs are unreadable** in GitHub / Azure DevOps. A single cell edit produces noise across line numbers, output cells, and execution counts.
- **Embedded outputs blow up repo size.** A notebook that ran `display(df)` on a 1000-row DataFrame carries 100 KB of HTML in the JSON. Multiply across notebooks and PRs and you hit Git's size limits.
- **`.gitignore` after the fact doesn't shrink history** — once you committed outputs, you have to rewrite history (BFG, `git filter-repo`) to reclaim space.
- **Autosave fights "save when I commit"** — Databricks autosaves notebook source on every cell run, producing dirty trees.
- **Repos limits** — Databricks Git folders explicitly recommend against monorepo-backed clones; "cloning a monorepo can exceed Git folder memory and disk limits and slow Git operations" ([Repos limits](https://learn.microsoft.com/en-us/azure/databricks/repos/limits)). Notebook UI render limit is 10 MB.

**The pattern that survives PR review:**

1. **Use `.py` format** for any notebook that lives in Git. Convert from `.ipynb` to `.py` with the Databricks CLI: `databricks workspace export-dir … --format SOURCE`.
2. **Strip outputs before commit** with `nbstripout` (for `.ipynb`) or by configuring the `.py` save mode.
3. **Move reusable logic into Python modules** in the same Repo (`src/` directory). The notebook becomes a thin orchestrator that calls module functions. This makes the logic testable with `pytest` + `chispa` (Module 5 covers this pattern).
4. **Use `blackbricks`** ([repo](https://github.com/inspera/blackbricks)) as a pre-commit hook to apply `black` to Python cells and `sqlparse` to SQL cells — vanilla `black` doesn't parse Databricks notebook headers.
5. **Use `databricks-pylint-plugin`** ([Databricks Labs](https://github.com/databrickslabs)) to catch Databricks-specific anti-patterns (dbutils misuse, hardcoded cluster IDs).

### When notebooks are still the right answer

- **Interactive data exploration** — the cell-by-cell loop is genuinely better than a `.py` REPL for analytical work.
- **Throwaway one-off analyses** — "what does this distribution look like?" doesn't need to be a wheel.
- **Demo / educational content** — the rich output is the point.

For everything else (production ETL, ML training pipelines, infrastructure code), **`.py` modules + Asset Bundles + CI** is the path. Module 19 covers DABs.

---

## Jobs / Workflows — the general-purpose orchestrator

### Mental model

A **Workflow** (formerly "Job," renamed around 2023–2024) is a DAG of **tasks**. Each task is one of:
- Notebook
- Python wheel (a `.whl` with an entry point)
- Python script
- SQL (warehouse query, dashboard refresh, or alert)
- DLT / Lakeflow Pipeline
- Spark JAR
- Spark Submit
- dbt task
- "If/Else" condition

Tasks declare dependencies (`depends_on`) and form a DAG. The scheduler handles ordering, retries, alerting.

### What Workflows give you

- **Retries** — at the task level (max retries, retry interval, retry on timeout).
- **Alerting** — email / webhook / Microsoft Teams / Slack / PagerDuty on success / failure / start / duration warning.
- **Parameterization** — task parameters with templating (`{{job.start_time}}`, `{{job.run_id}}`, `{{tasks.upstream.values.x}}`).
- **Multi-cluster** — different tasks can use different clusters; Job Compute is the default.
- **Concurrency limits** — `max_concurrent_runs` on the workflow level.
- **For-each loops** — iterate a task over a list of parameter values; runs concurrently up to the limit.
- **Continuous / triggered / scheduled** — cron, file-arrival trigger, REST trigger.
- **Repair runs** — when a task fails, fix the code and "repair-run" only the failed branch instead of re-running the whole DAG.

### Anti-patterns

1. **One giant notebook task that does everything** — defeats the point of the DAG. Split by logical step.
2. **All tasks on a single shared All-Purpose cluster** — pays $0.55/DBU instead of $0.15. Use Job Compute (cluster definition embedded in the workflow).
3. **No alerting on failure** — silently broken pipelines are how data gets stale.
4. **Tasks calling tasks via REST API instead of declared dependencies** — bypasses the DAG; the scheduler doesn't know about the dependency.
5. **Hardcoded cluster IDs** — pin to a cluster ID, the cluster gets deleted, the job dies forever. Use Job clusters or instance pools by tag.

### Multi-task patterns worth knowing

```yaml
# Example Asset Bundle workflow definition (databricks.yml)
resources:
  jobs:
    silver_refresh:
      name: silver_refresh
      tasks:
        - task_key: ingest_claims
          existing_cluster_id: ${var.silver_cluster_id}
          notebook_task: { notebook_path: ./src/ingest/claims.py }
        - task_key: ingest_eligibility
          existing_cluster_id: ${var.silver_cluster_id}
          notebook_task: { notebook_path: ./src/ingest/eligibility.py }
        - task_key: build_member_month
          depends_on:
            - { task_key: ingest_claims }
            - { task_key: ingest_eligibility }
          notebook_task: { notebook_path: ./src/silver/member_month.py }
        - task_key: data_quality
          depends_on:
            - { task_key: build_member_month }
          notebook_task: { notebook_path: ./src/checks/run.py }
      schedule: { quartz_cron_expression: "0 0 6 * * ?" }
      email_notifications:
        on_failure: [data-platform-oncall@optum.com]
        no_alert_for_skipped_runs: true
      max_concurrent_runs: 1
```

The `max_concurrent_runs: 1` is important — it prevents a slow nightly run from starting a second run on top of itself.

---

## Lakeflow Declarative Pipelines (the rebrand of DLT)

### What it is

Lakeflow Declarative Pipelines (SDP) is the **declarative ETL framework** built into Databricks. You write Python or SQL with decorators / SQL keywords describing **what each table/view should be** (input + transformation), and the framework figures out:

- Dependency graph from the table references
- Streaming vs batch (from the source)
- Incremental processing (CDC handling)
- Data quality (`EXPECT … ON VIOLATION DROP/FAIL`)
- Backfill and schema migration
- Observability (event log, lineage)

The DLT → Lakeflow rebrand happened progressively in 2024–2025; at DAIS 2025 Databricks **open-sourced** the core declarative pipeline tech to the Apache Spark project (lands fully in **Apache Spark 4.1** as Spark Declarative Pipelines). Existing DLT pipelines run unchanged — fully backward compatible. Python code can migrate from `import dlt` to `from pyspark import pipelines as dp`, with `@dp.table` for streaming tables and `@materialized_view` for materialized views ([Lakeflow July 2025 update](https://www.databricks.com/blog/whats-new-lakeflow-declarative-pipelines-july-2025)).

**SKU codes still begin with "DLT"**, event log schemas still say `dlt`. The term lingers in admin/billing surfaces; that's why "DLT" won't die fully.

### When Lakeflow wins

- **Streaming + CDC ingestion** with `APPLY CHANGES INTO` — handles late-arriving deletes, schema evolution, idempotency. Implementing this manually with `MERGE` is error-prone.
- **Data quality at the pipeline level** — `EXPECT (paid_amount >= 0) ON VIOLATION DROP ROW` runs in-line, not after the fact.
- **Multi-table dependency graphs** that change frequently — you don't have to re-author the DAG; the framework derives it from `dlt.read("table_name")` references.
- **Materialized views** with incremental refresh.
- **Backfill** — a single command rebuilds a table from sources.

### When Lakeflow loses

- **Imperative logic** — branching, looping, calling external APIs, complex state machines. Workflows + notebook tasks fit better.
- **Complex Python that doesn't fit the table-as-function model** — anything that needs to do non-tabular work mid-pipeline.
- **CI/CD against ephemeral environments** — DLT pipelines have "target" and "schema" config that can be confusing in DABs deployments ([Community 127147](https://community.databricks.com/t5/data-engineering/problems-and-questions-with-deploying-lakeflow-declarative/td-p/127147)).
- **Debugging** — declarative errors propagate through generated Spark code; stack traces are harder to read than imperative Spark.

### The DLT → Lakeflow code surface

```python
# 2024-style DLT
import dlt
from pyspark.sql.functions import *

@dlt.table(
  comment="Bronze claims, raw landing zone",
  table_properties={"quality": "bronze"}
)
def claims_bronze():
    return (
      spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .load("/Volumes/raw/edi/claims/")
    )

@dlt.table(comment="Silver claims, deduped, schema-enforced")
@dlt.expect_or_drop("valid_claim", "claim_id IS NOT NULL")
@dlt.expect_or_drop("positive_paid", "paid_amount >= 0")
def claims_silver():
    return (
      dlt.read_stream("claims_bronze")
        .dropDuplicates(["claim_id"])
        # ... transformations ...
    )
```

```python
# 2025-style Lakeflow / Spark Declarative Pipelines
from pyspark import pipelines as dp
from pyspark.sql.functions import *

@dp.table(
  comment="Bronze claims, raw landing zone",
  table_properties={"quality": "bronze"}
)
def claims_bronze():
    # same body
    ...

@dp.materialized_view(comment="Member-month aggregates")
def member_month():
    return (
      dp.read("claims_silver")
        .groupBy("member_id", date_trunc("month", "service_date").alias("year_month"))
        .agg(sum("paid_amount").alias("paid"))
    )
```

The decorators changed (`@dlt` → `@dp`), `@materialized_view` is new, `dlt.read` becomes `dp.read`. Pipelines can mix old and new in transition.

### `target` vs `schema` (the gotcha)

DLT/Lakeflow pipelines deploy to a **target schema** in the metastore. The pipeline configuration has a `target` field (legacy) and a `schema` field (newer). They serve overlapping purposes; mixing them (or not setting one consistently) causes deployment confusion. **Use `schema` in modern pipelines; treat `target` as deprecated** unless you have a specific reason.

When deploying via DABs (Module 19), the pattern is:

```yaml
resources:
  pipelines:
    silver_pipeline:
      name: silver_${bundle.target}
      schema: silver_${bundle.target}     # not target
      libraries:
        - notebook: { path: ./src/silver/main.py }
      configuration:
        env: ${bundle.target}             # parameter your code can read
```

### Breaking schema changes

A breaking schema change in a source table (e.g., a column type change without `delta.enableTypeWidening`) leaves a Lakeflow pipeline unable to recover **without manually resetting the CDC checkpoint and recreating the bundle deployment.** This is documented pain ([Community 127147](https://community.databricks.com/t5/data-engineering/problems-and-questions-with-deploying-lakeflow-declarative/td-p/127147)). Plan for it: discipline schema changes upstream, use type widening where possible, and have a runbook for "Lakeflow pipeline stuck on schema change."

### The new IDE (DAIS 2025)

Databricks shipped a **new IDE for data engineering** built around Lakeflow pipelines, with code-DAG pairing (you see the dependency graph next to the code you're editing), contextual previews, and AI-assisted authoring ([July 2025 update](https://www.databricks.com/blog/whats-new-lakeflow-declarative-pipelines-july-2025)). Worth trying for greenfield Lakeflow work; the workspace UI is the older path.

---

## Lakeflow Designer — no-code with a real artifact

Public Preview June 2025. Drag-and-drop ETL canvas + GenAI assistant; **generates real Lakeflow Declarative Pipelines code under the hood that's git-versionable.** Pay-for-compute, no per-user license.

The architect-relevant point: **the output is the same Lakeflow Python/SQL that an engineer would write**, so you can use Designer for non-engineer prototypes and then take ownership of the generated code in source control. Doesn't paint you into a no-code corner the way some legacy ETL tools did.

For Optum-scale healthcare, Designer's likely use is **business analyst self-service** for non-PHI workloads (provider lookups, network adequacy reports). Don't use it on PHI catalogs without the same governance discipline as engineer-written pipelines.

---

## The decision tree

When a workload arrives, ask in this order:

```
Q1. Is it a one-off exploration or demo?
    → Notebook (interactive)

Q2. Is it a streaming / CDC ingestion or a multi-table DAG of tabular transformations?
    → Lakeflow Declarative Pipelines

Q3. Is it imperative — branching, calling APIs, ML training, generic Python?
    → Workflows with Job Compute

Q4. Does the workload mix Lakeflow ETL + ML training + a final SQL refresh?
    → Workflows orchestrating a Lakeflow pipeline task + Python wheel task + SQL task
    (the canonical 2026 pattern)

Q5. Is the author a non-engineer who needs an ETL prototype?
    → Lakeflow Designer (then promote the generated code to source control)
```

The "Workflows orchestrating other things" is the answer for most production architectures — Workflows is the orchestrator, Lakeflow is the ETL specialist, notebooks are for tasks that don't fit either.

---

## Production reality

### The DABs YAML sprawl

DABs is the recommended CI/CD path for both Workflows and Lakeflow pipelines (Module 19), but the community sentiment is captured by Daniel Beach: *"I don't want to be a YAML engineer any more than you do. It's one thing to have IaC (Infrastructure as Code), and another thing to have Pipelines as Code"* ([Data Engineering Central](https://dataengineeringcentral.substack.com/p/simplifying-cicd-with-databricks)). Reuse / abstraction of `job_clusters` blocks across bundles is awkward; teams resort to YAML anchors, Jinja, or cookiecutter templating. **Brickflow** (Nike OSS, ~220 stars) is the third-party Python DSL that compiles to DABs YAML — worth knowing if your bundles get unwieldy ([Nike-Inc/brickflow](https://github.com/Nike-Inc/brickflow)).

### Notebook code-review mitigation in practice

Most teams that survive notebook-driven PR fatigue end up with this discipline:
- **`.py` format** for all version-controlled notebooks
- **Reusable logic in `src/` Python modules**, imported into thin notebooks
- **`pytest` + `chispa`** for unit tests on the modules (Module 5)
- **`blackbricks`** as a pre-commit hook
- **DABs** for deployment to dev/stage/prod targets
- **Notebooks-only-in-Repos**, never in `/Workspace/Users/<name>/...` for any production code

### The "Workflow stuck because of an upstream cluster failure" pattern

A common operational pain: a Workflow has 12 tasks; the upstream cluster fails to start; the workflow times out; you "repair run" but the cluster is still misbehaving and re-fails. This is where **Serverless Jobs Compute** earns its keep — startup is sub-minute and the cluster failure mode largely disappears.

For non-serverless Job Compute, instance pools (Module 2) reduce startup variance.

---

## When NOT to use each surface

- **Notebooks for production code paths** — pay the upfront cost of `.py` modules + tests; you'll save it back many times in code review and debugging.
- **Lakeflow for imperative logic** — the framework is for declarative tabular pipelines; imperative work fights it.
- **Workflows for sub-second triggered work** — Workflows have minimum scheduling overhead (~seconds). If you need millisecond response, you're in Model Serving or Apps territory.
- **Lakeflow Designer for production PHI workloads** — until governance discipline matures, treat Designer as prototype-grade.

---

## Sanity check

1. A team has 20 production "jobs" all running on a single shared All-Purpose cluster. Walk through the migration path and the cost impact.
2. What's the difference between `target` and `schema` in a DLT/Lakeflow pipeline configuration, and why does it matter for DABs deployments?
3. Why is `.py` notebook format strictly preferable to `.ipynb` for any version-controlled work, and how do you migrate?
4. A 12-task Workflow has been failing intermittently because a cluster takes 10 min to start and the first task times out at 8 min. Three options to fix?
5. When does Lakeflow Declarative Pipelines win over Workflows + notebook tasks, and when does it lose?
6. What is `Lakeflow Designer` and what's the architect's policy on its output?

---

## Further reading

- [Workflows / Jobs — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/jobs/)
- [Lakeflow Declarative Pipelines — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/ldp/)
- [What happened to DLT? — Azure docs](https://learn.microsoft.com/en-us/azure/databricks/ldp/where-is-dlt)
- [What's new in Lakeflow Declarative Pipelines (July 2025)](https://www.databricks.com/blog/whats-new-lakeflow-declarative-pipelines-july-2025)
- [Lakeflow Designer Public Preview blog](https://www.databricks.com/blog/announcing-public-preview-lakeflow-designer)
- [Repos limits — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/repos/limits)
- [blackbricks — formatting for Databricks notebooks](https://github.com/inspera/blackbricks)
- [Daniel Beach — Simplifying CI/CD with Databricks](https://dataengineeringcentral.substack.com/p/simplifying-cicd-with-databricks)
- [Nike-Inc/brickflow — Pythonic DSL on top of DABs](https://github.com/Nike-Inc/brickflow)
