# Quiz — Module 10: HMS → Unity Catalog Migration Reality

## Recall

**Q1.** What is HMS Federation, and why is it the most important migration unlock?

<details><summary>Answer</summary>

**HMS Federation** (GA March 2025) lets you mount the entire `hive_metastore` as a **foreign catalog** in UC. You get UC permissions, lineage, and audit over HMS tables **without moving data.**

**Why it's the most important unlock:** for the first ~2 years of UC, migration was effectively a big-bang cutover — you couldn't progressively move tables because UC-enabled clusters couldn't read HMS tables cleanly. With HMS Federation, you can:
1. Federate HMS so existing code keeps working
2. Migrate hot tables to UC managed at your own pace
3. Update code references gradually
4. Decommission HMS when migration is complete

**Read/write to internal HMS** (workspace's own HMS); **read-only to external HMS and Glue.**
</details>

**Q2.** What are the four headline UCX workflows, and what's the biggest caveat about UCX itself?

<details><summary>Answer</summary>

UCX is a Databricks Labs project ([databrickslabs/ucx](https://github.com/databrickslabs/ucx)). The four workflows:

1. **Assessment** — inventories tables, mounts, jobs, clusters, init scripts, permissions; produces a dashboard.
2. **Group migration** — promotes workspace-local groups to account-level groups.
3. **Table migration** — converts managed/external HMS tables to UC, handling ADLS path translation.
4. **Code migration** — lints notebooks/jobs/queries for `hive_metastore.*` references and DBFS mounts.

**The biggest caveat: UCX is "no SLA, provided as-is."** It's a Labs project, not a supported product. Common community-reported failures:
- Spark SQL migration is partial — dynamic SQL escapes the linter
- 429 throttling on bulk migrations
- Network-restricted enterprises hit egress issues installing UCX
- Mounts are second-class on shared clusters

**Plan accordingly:** UCX is a starting point, not a finish line. Expect at least one "we're going to redo the assessment" mid-course correction.
</details>

---

## Apply

**Q3.** Outline a 6-month UC migration plan for an Optum-scale organization with ~5000 tables and 50+ engineers across multiple business units, using HMS Federation as the incremental escape hatch.

<details><summary>Answer</summary>

**Phase 0: Pre-work (Month -2 to 0) — political and architectural**
- Get exec sponsorship for a forcing function: "no new HMS tables after [date]." Without it, migration drags.
- Decide catalog naming convention: e.g., `<env>_<phi-class>_<domain>` → `prod_phi_claims`, `prod_deid_member`.
- Identify the small set of metastore admins; provision the tier-0 governance workspace.
- Set up Automatic Identity Management for Entra ID (Public Preview) so account-level identity flows automatically.

**Month 1-2: Assessment + foundation**
- Run UCX assessment in every workspace; consolidate inventory in a `_admin` UC catalog.
- Identify the top-50 hot tables (those touched by >10 jobs or >5 dashboards).
- Set up storage credentials and external locations covering all ADLS paths in use.
- Migrate workspace-local SCIM groups to account-level (or rely on AIM).

**Month 3: HMS Federation**
- Deploy HMS Federation across all production workspaces. `hive_metastore` becomes `legacy_hms_catalog` (a foreign UC catalog).
- Verify all existing pipelines continue to work via the federated path.
- Begin code-reference inventory using UCX linter.

**Month 4: Hot-table migration**
- Migrate the top-50 hot tables to UC managed Delta. Each migration is its own change-control event.
- Update dbt projects, dashboards, and notebooks to point at the new UC catalog names.
- Bind PHI catalogs to PHI workspaces only.

**Month 5: Long-tail migration**
- Migrate remaining hot+warm tables. Cold tables can stay on HMS Federation indefinitely or be migrated opportunistically.
- Update all CI/CD pipelines (DABs targets) to reference UC catalogs.
- Decommission workspace-level SCIM where AIM has replaced it.

**Month 6: Stabilization + decommission**
- Audit residual HMS usage via `system.access.audit`.
- Decommission workspaces that no longer need HMS access.
- Document the new UC patterns in the platform runbook.
- Plan the eventual HMS sunset (likely Year 2).

**Risks to flag for leadership:**
- **2× rule** — plan estimates often double in execution.
- **Iterative-pipeline performance regressions** are common after migration; budget time for code refactors.
- **Mid-course correction** is normal — the 7-Eleven DAIS 2025 talk title was "Reorienting a Complex UC Migration."
- **Audit log retention** for HIPAA must be in place before the migration starts (Module 17).
</details>

---

## Diagnose

**Q4.** A team migrated a 100M-row Bronze table from HMS to UC managed Delta. The nightly Lakeflow pipeline that processes it now takes 4× longer than before. The team complains UC "made it slower." Walk through the diagnosis.

<details><summary>Answer</summary>

**Most likely root cause:** UC permission lookup overhead amplified by an iterative or loop-heavy pipeline. The pattern documented at retail and healthcare orgs: jobs that ran in minutes on HMS take hours on UC because legacy code did 10K+ small queries, each of which now incurs UC permission lookup ([Tredence](https://www.tredence.com/blog/migrating-to-unity-catalog)).

**Diagnosis approach:**
1. **Spark UI SQL plan** — count the number of distinct query executions in the slow stage. If it's 10K+, the pipeline is iterative; UC overhead per call adds up.
2. **Check for `dbutils.fs.mounts()` calls** — these now hit a permission boundary on UC clusters and may be redirected through a slower path.
3. **Check for direct DBFS path access** — UC shared-access mode blocks `/dbfs/...` paths; the code may have fallen back to a slower path.
4. **Check for workspace-mounted vs UC volume paths** — old `/mnt/...` mounts vs new `/Volumes/...` paths have different I/O characteristics.

**Fixes:**
1. **Refactor loops into bulk operations** — most healthcare ETL has loops that can be replaced with single Spark queries. This is the highest-ROI change.
2. **Replace `dbutils.fs.mounts()` with the `ucx.mounts` table** or hardcode paths.
3. **Migrate from DBFS mounts to UC Volumes** — `/Volumes/<catalog>/<schema>/<volume>/...` is the modern path.
4. **Use UC managed tables for the hot path** — full UC managed gets the latest optimizations (Predictive Optimization, deletion vectors); external tables get less.
5. **Profile in Spark UI** — if Photon was on for HMS but not for UC (cluster mode change), turn it back on.

**Production discipline:** **migration is the time to refactor, not preserve.** Code that's "10K small queries that worked fine on HMS" is technical debt that UC is now charging you for. Treat it as a planned engineering investment.
</details>

---

## Defend

**Q5.** A peer says "we should do a big-bang cutover next month — drag out the migration any longer and people will resist." Defend or refute for an Optum-scale environment.

<details><summary>Answer</summary>

**Refute, with calibration.**

Where the peer is right:
- **Migration drag is real.** Without a forcing function, HMS lingers for years.
- **Some teams do big-bang successfully** — Ensemble did ~10K tables in a single-night cutover after months of prep.

Where the peer is wrong for Optum-scale:
- **5000+ tables, 50+ engineers, multiple business units** is fundamentally different from a focused 10K-table organization. The blast radius of a single-night cutover failure is too high.
- **Healthcare adds compliance pressure** — a botched cutover that breaks PHI access during business hours is a HIPAA-impacting incident, not just an engineering one.
- **HMS Federation (GA March 2025) is exactly the tool** for incremental migration. Skipping it is leaving the most important architectural unlock unused.
- **Big-bang assumes the prep is complete.** Databricks's own internal migration took 10 months with a 4-person team — and they had complete control over the platform. An Optum BU has variable platform discipline; not every team will be ready on the cutover date.
- **The "people will resist" argument is the wrong forcing function.** The right forcing function is exec sponsorship of "no new HMS tables after [date]" + a clear migration path that doesn't break production. Resistance comes from disruption, not from duration.

**The architect's defensible position:**
- **6-month gradual migration with HMS Federation as the bridge.**
- **Forcing function: exec policy that no new HMS tables are allowed after Month 2.** This caps HMS growth and gives existing tables a clear migration target.
- **Hot-table migration in Month 4** — the top-50 tables that get hit by most pipelines and dashboards. Get the visible wins.
- **Long tail** can stay on HMS Federation indefinitely or be migrated opportunistically. Not every cold table needs to be UC managed.
- **Decommission HMS in Year 2**, not in Month 6.

**The honest counter to the peer:** "We agree migration drag is real. The fix is the forcing function (exec policy on no-new-HMS), not a higher-risk cutover. HMS Federation is the architectural tool exactly for this case — let's use it."

**Source:** [HMS Federation announcement](https://www.databricks.com/blog/announcing-public-preview-hive-metastore-and-aws-glue-federation-unity-catalog), [Databricks own UC journey](https://www.databricks.com/blog/databricks-databricks-kicking-journey-governance-unity-catalog).
</details>
