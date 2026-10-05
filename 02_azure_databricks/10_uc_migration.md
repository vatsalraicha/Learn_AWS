# Module 10 — Hive Metastore → Unity Catalog Migration Reality

> **Goal of this module:** internalize what a real `hive_metastore` → UC migration looks like, what UCX gives you and where it falls short, why HMS Federation (GA March 2025) is the single most important escape hatch, and the war stories you'll encounter at Optum-scale.

---

## Why this is its own module

The marketing version says "use UCX, you'll be migrated by Friday." The reality is **6–12 months for a non-trivial estate.** Databricks' own internal migration took 10 months with a 4-person team ([Databricks blog: kicking off UC governance journey](https://www.databricks.com/blog/databricks-databricks-kicking-journey-governance-unity-catalog)). Ensemble (a healthcare RCM company) did a single-night cutover after several months of prep covering ~10,000 tables ([Ensemble UC case study](https://www.databricks.com/customers/ensemble/unity-catalog)).

For an architect at Optum, this is a **multi-quarter platform-engineering project**, not a tool run.

---

## What you're actually migrating

UC migration touches four largely-independent layers:

1. **Tables and storage** — registering existing tables with UC, sometimes converting external→managed or relocating storage
2. **Permissions** — workspace-local groups become account-level; HMS GRANTs become UC GRANTs; storage-side IAM becomes UC storage credentials
3. **Code references** — every `spark.sql("USE hive_metastore.default...")` becomes `prod_catalog.silver...`; dbt `{{ ref('x') }}` becomes `{{ ref('catalog.schema.x') }}`; notebook hardcodes get rewritten
4. **Compute** — UC-enabled clusters require Standard or Single User mode; legacy "passthrough" / "no isolation shared" clusters can't see UC tables with row/column filters

Each layer has its own pain. Migrating one without the others breaks production.

---

## UCX (Databricks Labs) — what it is and isn't

[`databrickslabs/ucx`](https://github.com/databrickslabs/ucx) is the **unsupported** Labs project (no SLA — "provided as-is") that automates most of the heavy lifting.

### The four headline workflows

1. **Assessment** — inventories tables, mounts, jobs, clusters, init scripts, permissions; produces a dashboard.
2. **Group migration** — promotes workspace-local groups to account-level groups (UC requires account-level identities).
3. **Table migration** — converts managed/external HMS tables to UC, handling ADLS Gen1 → Gen2 path translation.
4. **Code migration** — lints notebooks/jobs/queries for `hive_metastore.*` references and DBFS mounts.

The [common-challenges page](https://databrickslabs.github.io/ucx/docs/reference/common_challenges/) is brutally honest about the rough edges.

### Real gotchas from GitHub issues and community

- **Mounts are second-class.** [Issue #2498](https://github.com/databrickslabs/ucx/issues/2498) — table migration fails on shared clusters with `DBUtilsCore.mounts() is not whitelisted` on DBR 15.4. Workaround: rely on the `ucx.mounts` table, not `dbutils.fs.mounts()`.
- **Spark SQL migration is partial.** [Issue #2551](https://github.com/databrickslabs/ucx/issues/2551) — `spark.sql("…")` queries get table-migration linting but not full code rewrite. Anything dynamically constructed escapes the linter.
- **429 throttling.** Bulk `migrate-tables` jobs hit Databricks API rate limits in large estates ([Community 90825](https://community.databricks.com/t5/get-started-discussions/error-in-migration-with-ucx-tool/td-p/90825)).
- **Time travel is lost on CLONE.** Cloned tables are new tables; no pre-migration history.
- **Azure-specific:** `wasb://` and `adl://` (gen1) paths must be moved to `abfss://` (gen2) before UC will register them.
- **Hive partition commands** (`ALTER TABLE … PARTITION`) don't translate to UC managed tables.
- **Performance regressions.** [One retail case study](https://www.adityagoyalportfolio.com/story-uc-migration) reports jobs that took minutes on HMS taking hours on UC after migration — usually because legacy code relied on direct DBFS path access (now blocked under UC shared-access mode) and fell back to slower paths.
- **Network-restricted enterprises** (read: healthcare, finance) hit additional pain because UCX needs egress to GitHub during install ([Rearc on UCX in restricted networks](https://www.rearc.io/blog/network-restricted-databricks-ucx-installation)).

### The UCX maturity reality

7-Eleven's 2025 DAIS talk was titled **"Story of a UC Migration: Reorienting a Complex UC Migration"** ([DAIS 2025 session](https://www.databricks.com/dataaisummit/session/story-unity-catalog-uc-migration-using-ucx-7-eleven-reorient-complex-uc)) — the framing alone signals how often the first attempt doesn't land.

UCX is a **starting point**, not a finish line. Plan for at least one "we're going to redo the assessment because the first one missed N% of our jobs."

---

## HMS Federation — the single most important escape hatch

[GA'd March 2025](https://www.databricks.com/blog/announcing-public-preview-hive-metastore-and-aws-glue-federation-unity-catalog), [HMS Federation](https://learn.microsoft.com/en-us/azure/databricks/query-federation/hms-federation-concepts) lets you **mount the entire HMS as a *foreign catalog* in UC.** You get UC permissions, lineage, and audit over HMS tables **without moving data.**

```sql
-- Federate the workspace's HMS into UC
CREATE FOREIGN CATALOG legacy_hms_catalog
  USING CONNECTION my_hms_connection
  COMMENT 'Foreign catalog wrapping the legacy HMS';
```

Now `hive_metastore` becomes `legacy_hms_catalog` (or whatever you name the foreign catalog), code keeps working, and you migrate at your own pace.

- **Read/write to internal HMS** (the workspace's own HMS)
- **Read-only to external HMS and Glue**

This is the single best change for incremental migration — it was missing for the first ~2 years of UC and forced big-bang cutovers. Now you can:
1. Federate HMS so existing code keeps working
2. Migrate hot tables to UC managed at your own pace
3. Update code references gradually (over months, not all at once)
4. Decommission HMS when migration is complete

For Optum-scale, this is the difference between a 3-month coordinated cutover and a 12+ month gradual migration without a hard deadline.

---

## Migration patterns — what actually works

### Pattern 1: assessment → federation → gradual migration (recommended)

```
Week 1-2: Run UCX assessment, build inventory
Week 3-4: Set up account-level identity federation; deploy AIM if available
Week 5-6: Set up storage credentials, external locations, target catalogs
Week 7-8: Federate HMS → UC (HMS Federation)
Week 9+:  Gradually migrate hot tables; update code references
Month 6+: Migrate remaining tables; decommission HMS
```

This is the multi-quarter version that doesn't break production.

### Pattern 2: big-bang cutover (high-risk, only with a clear forcing function)

```
Month 1-3: Heavy prep — UCX runs, code rewrites, group migrations, dashboard re-points
Month 4: Single-night cutover — all jobs paused, tables migrated, code redeployed
Month 5: Stabilization — fix edge cases, performance regressions
```

Ensemble did this with ~10K tables. Most healthcare orgs shouldn't.

### Pattern 3: greenfield UC, freeze HMS (the "hard policy" approach)

Databricks itself used this internally: **no new HMS tables allowed past a quarter in.** This forces HMS counts to zero by attrition rather than active migration.

Works if your team has the political muscle to enforce the policy. Less useful at Optum-scale where dozens of teams have HMS-shaped pipelines.

---

## Specific migration challenges to plan for

### 1. dbt model rewrites

Reliable Data Engineering's 500-model dbt migration documented:
- Every `{{ ref('x') }}` had to become `{{ ref('catalog.schema.x') }}`
- ~60 incremental models broke on `{{ this }}`
- 40+ S3 external tables failed because workspace-IAM didn't transfer to metastore-level credentials
- `spark.databricks.delta.schema.autoMerge.enabled` had to be set explicitly to keep schema evolution working

([Reliable Data Engineering / Medium](https://medium.com/@reliabledataengineering/i-migrated-500-dbt-models-to-databricks-unity-catalog-heres-what-broke-and-what-got-10x-2a2dc93f548b))

### 2. Iterative jobs slowing down

A repeated horror-story pattern: "jobs that ran perfectly fine on Hive suddenly took hours on UC — especially parts of the pipeline that involved loops or iterative processing" ([Tredence](https://www.tredence.com/blog/migrating-to-unity-catalog), [Aditya Goyal portfolio](https://www.adityagoyalportfolio.com/story-uc-migration)).

The UC permission lookup path adds overhead per call; iterative workloads that did 10K+ small queries amplified it. **Workarounds involve refactoring loops into bulk operations** — i.e., a code rewrite, not a config flip.

### 3. The three-permission collision (mid-migration is the worst)

Mid-migration you have BOTH legacy workspace ACLs and UC grants live. **Reasoning about effective permissions requires reading three permission models simultaneously** ([UC access control](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/access-control)). The field anti-pattern is "migrate tables first, then grant broadly when people complain" — which produces over-grants you spend a year clawing back.

The discipline: **finish the group migration before migrating tables.** Account-level groups must exist and be assigned before tables move; otherwise grants fall through.

### 4. Storage credentials and external locations

External tables on HMS used direct IAM (workspace cluster identity → ADLS). On UC, this has to become a storage credential + external location. Without it, the migrated table is registered but unreadable.

The discipline: **set up storage credentials before migrating any external table.** The UCX assessment dashboard shows you the storage paths in use; pre-create credentials and locations covering all of them.

### 5. SCIM workspace → account migration

Workspace-local SCIM groups don't appear in UC GRANTs. **Move SCIM provisioning from workspace level to account level** ([Marczak.IO Lessons Learned](https://marczak.io/posts/2025/12/migrating-to-unity-catalog-the-big-picture/)). Many teams discover this only after groups go missing in UC.

The 2026 fix: **Automatic Identity Management for Entra ID** (Public Preview) replaces the SCIM-connector dance entirely.

### 6. Cluster mode upgrades

Legacy "no-isolation shared" clusters can't see UC tables with row filters or column masks. The migration includes:
- Upgrade clusters to **Standard (Shared)** or **Single User** mode
- Update notebooks that depended on now-blocked patterns (direct DBFS path access, `dbutils.fs.mounts()`, etc.)

### 7. Dashboards re-pointing

Power BI semantic models, Tableau workbooks, Lakeview dashboards — all reference tables by their three-part name. Migration involves a coordinated dashboard refresh: republish each dashboard against the new UC catalog name.

For healthcare: dashboards referencing PHI tables also need to move to PHI-bound workspaces. Don't migrate the catalog without re-binding the dashboards.

---

## Production reality

### Plan for 2× the estimated duration

Whatever the plan says, multiply by 2. Migration discovers things UCX assessment missed: legacy `dbutils` calls in obscure notebooks, custom Spark configs, SQL queries with dynamic table names that escape the linter.

### "It won't take that long" is the leading indicator of pain

The 7-Eleven DAIS 2025 talk title — **"Reorienting a Complex UC Migration"** — is the universal experience. Plan for at least one mid-course correction.

### The forcing function that helps

For Databricks itself, the forcing function was a **hard policy: no new HMS tables.** That policy is what drove HMS counts to zero. Without a forcing function, attrition is slow and HMS lingers for years.

For an Optum-scale org, get an exec to sign the policy *before* you start. Migration without a forcing function meanders.

### The success criterion

You're done when:
- All hot tables are in UC managed
- Code references are updated
- HMS is read-only / decommissioned
- Workspace-level groups are gone
- Audit is flowing through `system.access.audit`
- Lineage works end-to-end on at least the priority pipelines

This is a **6–12 month project**, not a sprint goal.

---

## When NOT to migrate (yet)

- **You don't have account-level identity** — fix that first.
- **You haven't decided your catalog naming convention** — once you pick names, they're sticky.
- **You don't have a UCX assessment dashboard with a credible inventory** — flying blind into a complex migration produces the "we didn't know that was there" failures.
- **You don't have a forcing function** — without one, the migration drags.

---

## Sanity check

1. What does HMS Federation give you that didn't exist in UC's first 2 years, and why is it the most important migration unlock?
2. What's the realistic timeline for a 1000-table migration at Optum scale, and what's the riskiest dependency to plan for?
3. Why did Databricks' own UC migration take 10 months, and what was their forcing function?
4. UCX is "no SLA, Labs project." What does that mean for your migration plan?
5. A team migrated their tables to UC and now their iterative pipeline is 10× slower. What's the likely cause?
6. The three-permission collision is worst mid-migration. What discipline minimizes the pain?

---

## Further reading

- [databrickslabs/ucx](https://github.com/databrickslabs/ucx)
- [UCX common challenges](https://databrickslabs.github.io/ucx/docs/reference/common_challenges/)
- [HMS Federation — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/query-federation/hms-federation-concepts)
- [HMS+Glue Federation announcement](https://www.databricks.com/blog/announcing-public-preview-hive-metastore-and-aws-glue-federation-unity-catalog)
- [Migrate tables to UC](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/migrate)
- [Databricks-on-Databricks UC journey](https://www.databricks.com/blog/databricks-databricks-kicking-journey-governance-unity-catalog)
- [Ensemble UC case study](https://www.databricks.com/customers/ensemble/unity-catalog)
- [Reliable Data Engineering — 500 dbt models migration](https://medium.com/@reliabledataengineering/i-migrated-500-dbt-models-to-databricks-unity-catalog-heres-what-broke-and-what-got-10x-2a2dc93f548b)
- [Karlo Kotarac — UC migration lessons (Valcon)](https://medium.com/valcon-consulting/unity-catalog-migration-best-practices-lessons-learned-from-two-implementations-part-1-f692811643a6)
- [Marczak.IO — Migrating to UC the big picture](https://marczak.io/posts/2025/12/migrating-to-unity-catalog-the-big-picture/)
- [Daniel Beach — Migrating to Databricks](https://www.confessionsofadataguy.com/migrating-to-databricks-a-guide/)
