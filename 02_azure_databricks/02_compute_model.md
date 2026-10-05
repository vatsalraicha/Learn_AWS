# Module 2 — Compute Model Deep Dive

> **Goal of this module:** be able to pick the right compute shape for any Databricks workload, write a production-grade cluster policy, understand exactly what Photon and serverless cost vs deliver, and not get surprised by the hidden gotchas (cold starts, init-script deprecations, Spot fallbacks, autoscaling thrashing).

---

## Why this exists

Databricks' compute story is not "Spark on managed VMs." It's a five-dimensional product: **{cluster mode (single user / shared / no isolation), tier (classic / serverless), runtime (DBR version), engine (JVM Spark / Photon), instance shape (CPU / memory / GPU / Spot)}** — every combination has different price, latency, security, and feature trade-offs. The architect's job is to know which combination fits which workload, codify that as a cluster policy, and audit drift.

The pitfall most teams fall into: **everything runs on All-Purpose Compute with autoscaling enabled, Photon turned on globally, default cluster policies.** That configuration is ~3.6× more expensive than Jobs Compute, has 37% higher cost than tuned fixed clusters with worse runtime ([Sync Computing benchmark](https://medium.com/sync-computing/is-databrickss-autoscaling-cost-efficient-610e6ece4831)), and pays Photon's 2× DBU multiplier on workloads that don't benefit. Module 16 tells you to find this and fix it; this module tells you how to design around it.

---

## How it works — the cluster taxonomy

### Five compute SKUs that matter in 2026

| SKU | Use | $/DBU-hr (Azure, Premium, US) | VM in price? | Typical startup |
|---|---|---:|---|---|
| **Jobs Compute** (classic) | Scheduled, ephemeral runs | **$0.15** | No (separate Azure VM bill) | 3–7 min |
| **All-Purpose Compute** | Interactive notebooks, dev | **$0.55** | No | 3–10 min |
| **Serverless Jobs** | Scheduled, fast startup | ~$0.35 | **Yes** | seconds |
| **SQL Serverless** | DBSQL warehouses | **$0.70** | **Yes** | 5–10 sec |
| **Model Serving** | Online inference | varies, GPU 10–628 DBU/hr | **Yes** | 10s–min cold |

_Sources: [Azure Databricks pricing](https://azure.microsoft.com/en-us/pricing/details/databricks/), [databrickspricing.com rate tables](https://www.databrickspricing.com/dbu-pricing-explained). All numbers May 2026._

The first decision is **Jobs Compute vs All-Purpose Compute** — and the answer is "Jobs Compute, always, for anything scheduled." All-Purpose is for *interactive* work where humans are typing in notebooks. Migrating scheduled workloads from All-Purpose to Jobs is a **3.6× cost cut on the Databricks side**, no engineering work other than changing where the job runs ([Youssef cost playbook](https://medium.com/@ahmed.youssef12377/databricks-cost-optimization-playbook-lessons-from-cutting-production-costs-by-over-80-0e81d8b7a374)). It is the single highest-ROI lever on the platform.

### Cluster modes (access mode)

Three modes since 2024 ([UC compute docs](https://learn.microsoft.com/en-us/azure/databricks/compute/configure)):

- **Single User** — one user owns the cluster; runs as that user's identity. Works with all UC features. The 2026 default for ML / individual dev work.
- **Standard / Shared** — multiple users, isolated Python environments per user, runs queries as the *querying* user (so UC permissions enforce per-user). Required for analyst clusters where you want one warm pool serving the team.
- **No Isolation Shared** — legacy, multiple users, shared identity. **Cannot use Unity Catalog for tables with row/column filters.** Avoid for new work; deprecate where you find it.

For UC + ABAC + row filters + column masks, **Standard or Single User mode is mandatory** ([UC requirements](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/get-started)). The legacy "passthrough" mode many shops grew up on is gone.

### Photon — the 2× DBU question

Photon is Databricks' vectorized C++ execution engine, originally announced at Data + AI Summit 2020 and now the default for SQL and DLT. It charges a **2× DBU multiplier** on the cluster ([Photon docs](https://learn.microsoft.com/en-us/azure/databricks/compute/photon)).

The breakeven test: Photon must produce **~20% more speedup than the bare instance** to be net-positive on cost — because the speedup also reduces VM hours and DBU-hours, the math is not pure 2×/2× ([Sync Computing benchmark on TPC-DS 1TB](https://medium.com/sync-computing/are-databricks-clusters-with-photon-and-graviton-instances-worth-it-845641d464f2)).

**Photon-friendly workloads (turn it on):**
- SQL warehouses, Spark SQL queries, DataFrame native operations
- Joins, aggregations, window functions, sorts
- Native Parquet read/write, Delta MERGE/UPDATE/DELETE (Photon got a native Parquet writer in 2024 that accelerates DML)

**Photon-hostile workloads (don't pay the 2×):**
- **Python UDFs** — execution falls back to Python; Photon does nothing
- **Pandas UDFs** — partial benefit, but generally below the 20% margin
- **RDD code** — Photon doesn't run RDDs at all
- **Spark MLlib / pyspark.ml training loops** — iterative; Photon barely helps
- **Tiny data jobs** — Photon's setup overhead amortizes poorly under ~10 GB
- **Append-mostly streaming with simple transformations** — already cheap; Photon adds DBU

**Miles Cole's TPC-style benchmark** ([Is Databricks Photon a no-brainer?](https://milescole.dev/data-engineering/2024/04/30/Is-Databricks-Photon-A-NoBrainer.html)) found ~2.7× average speedup but **Query 6 cost 72% MORE with Photon** ($0.054 → $0.093). The takeaway: **"Photon everywhere by default" is an anti-pattern**. Benchmark per workload type, then enforce via cluster policy.

### Serverless compute — the 2024–2025 wave

Serverless is now GA across the board: SQL warehouses (longstanding), jobs/notebooks (2024), model serving (2024), DLT/Lakeflow (2025), and serverless GPU compute beta on Azure (A10 only as of late 2025).

**What serverless gives you:**
- Sub-minute startup — vs 3–10 min on classic
- Scale to zero in seconds — no idle bill
- VM cost included in the DBU rate (one bill instead of two)
- No cluster config to manage — no Spot/On-Demand decisions, no instance type tuning

**What serverless takes away:**
- **You cannot pick instance type, use Spot, or run a custom Docker image.**
- **You cannot `.persist()` DataFrames** — caching API is restricted on serverless ([HN 43899252](https://news.ycombinator.com/item?id=43899252)).
- **No per-job memory/CPU metrics via API.**
- **Cold-start re-installs your full dependency tree** every time. The startup cost reproduces in seconds rather than minutes, but it reproduces ([Bauplan analysis](https://www.bauplanlabs.com/post/to-serverless-or-not-to-serverless)).
- **Higher per-DBU rate** ($0.70 SQL Serverless vs $0.55 SQL Pro). Pays back when utilization is jagged; loses on flat-line saturated warehouses.

**Real production reports of serverless cost explosions** for DLT specifically: 3–5× cost increases moving DLT to serverless; one user reported €2,000 burned in two days across four pipelines ([Zipher analysis](https://zipher.cloud/databricks-serverless-pros-cons/)). Databricks markets 98% lower cost for materialized view refreshes — the discrepancy is workload-shape-dependent and the buyer can't see DBU consumption inside serverless to validate. **Default to classic Jobs Compute for predictable production workloads; default to serverless for spiky / interactive / unknown-utilization paths.**

### GPU compute on Azure Databricks

The 2026 SKU lineup ([Azure Databricks GPU docs](https://learn.microsoft.com/en-us/azure/databricks/compute/gpu)):

| Family | GPU | Memory | Use |
|---|---|---|---|
| NCadsA10_v4 | A10g | 24 GB | Cheap inference, light fine-tuning |
| NCads_A100_v4 | A100 40 GB | 40 GB | 7B–13B fine-tunes |
| NDasrA100_v4 | A100 80 GB | 80 GB | Larger models, larger batches |
| ND_H100_v5 (8× H100) | H100 | 8× 80 GB NVLink | 70B fine-tunes, distributed training |
| NV_v5 | various | — | Visualization (rare in DBX) |
| NC v3 (V100) | V100 | 16 GB | **Being deprecated — don't start here** |

ND_H100_v5 lists ~$98/hr Azure on-demand (~$12.30/GPU-hr); spot ~$70-75/hr. Reserved 1y/3y up to 60% off ([Vantage instance pricing](https://instances.vantage.sh/azure/vm/nd96isrh100-v5)).

**Azure capacity reality:** H100 capacity in HIPAA-eligible regions (East US, Central US) is tightest. East US 2, South Central, West US 3 are most reliable but may not satisfy data residency. **Check capacity availability before committing roadmap.**

### Cluster mode meets DBR

Each cluster picks a Databricks Runtime (DBR) version. The 2026 picture:

| DBR | Spark | Status | Use for |
|---|---|---|---|
| 14.3 LTS | 3.5 | EoS approaching | Avoid for new work |
| 15.4 LTS | 3.5 | Supported | If hard dep on Spark 3.5 |
| 16.4 LTS | 3.5 | Supported (May 2025) | Liquid Clustering GA, UC managed Iceberg Public Preview |
| **17.3 LTS** | **4.0** | **Recommended** (Oct 2025) | **2026 greenfield default** |
| 18.x | 4.0 | Non-LTS, latest features | Edge cases |

DBR upgrade is the single most disruptive recurring admin event — Spark 4 / Scala 2.13 / `input_file_name` removal in 17.x are real breaking changes for code that depended on legacy APIs. Module 17 covers the upgrade runbook.

### Init scripts — the lifecycle that won't sit still

Init scripts run on every cluster node at startup. Used for: corp CA cert install, library install for offline workspaces, monitoring agent install, custom `LD_LIBRARY_PATH` for proprietary libs.

**The deprecation history (3 migrations in ~3 years):**
1. **Pre-2023:** DBFS-stored cluster-scoped init scripts.
2. **May 2023:** DBFS deprecated; migrate to **workspace files**.
3. **Dec 1, 2023:** cluster-named DBFS scripts disabled outright.
4. **2024+:** workspace files OK, but **UC Volumes is the recommended pattern** for governance and versioning.

The pattern that sticks ([Databricks KB migration](https://kb.databricks.com/clusters/migration-guidance-for-init-scripts-on-dbfs)):

```bash
# Store at: /Volumes/_admin/init/scripts/install_corp_ca_v3.sh
# Reference in cluster policy as init_scripts: [{ "volumes": { "destination": "..." } }]
```

Use a **`_v<n>` suffix** in the path to enable rollforward without overwriting in place — every cluster restart re-pulls; if the new version is bad, you flip the policy to `_v(n-1)` and bounce. **Never edit init scripts in place** — the wave of cluster restarts touching the bad version is hard to undo.

---

## Cluster policies — the central admin lever

A cluster policy is JSON that constrains what users can configure when they create a cluster. Policies enforce tags (for chargeback), instance types (for cost), DBR versions (for stability), auto-termination (against forgotten clusters), and security mode (for UC compatibility). They are the single highest-ROI admin artifact.

The pattern: **one policy per persona**, not per team. Personas are stable; teams come and go.

### The four canonical personas

```json
// 1. Analyst — interactive, smallish, hard auto-term
{
  "spark_version": {"type": "regex", "pattern": "^17\\.[0-9]+\\.x-scala2\\.13$"},
  "node_type_id": {"type": "allowlist", "values": [
    "Standard_DS4_v5", "Standard_DS5_v5", "Standard_E8ds_v5"
  ]},
  "data_security_mode": {"type": "fixed", "value": "USER_ISOLATION"},
  "autotermination_minutes": {"type": "range", "minValue": 10, "maxValue": 60, "defaultValue": 30},
  "num_workers": {"type": "range", "maxValue": 8},
  "custom_tags.cost_center": {"type": "regex", "pattern": "^cc-[0-9]{6}$"},
  "custom_tags.business_unit": {"type": "allowlist", "values": ["claims", "member", "provider", "rx", "stars", "actuarial"]},
  "custom_tags.data_classification": {"type": "allowlist", "values": ["non-phi", "deid"]},
  "spark_conf.spark.databricks.cluster.profile": {"type": "fixed", "value": "singleNode", "hidden": true},
  "init_scripts.0.volumes.destination": {"type": "fixed", "value": "/Volumes/_admin/init/analyst_v3.sh"}
}
```

```json
// 2. ML Engineer — GPU allowed, longer runtime, Spot for cost
{
  "spark_version": {"type": "regex", "pattern": "^17\\.[0-9]+\\.x-(gpu-)?ml-scala2\\.13$"},
  "node_type_id": {"type": "allowlist", "values": [
    "Standard_DS5_v5", "Standard_E8ds_v5",
    "Standard_NC24ads_A100_v4", "Standard_ND96isr_H100_v5"
  ]},
  "data_security_mode": {"type": "allowlist", "values": ["SINGLE_USER", "USER_ISOLATION"]},
  "autotermination_minutes": {"type": "range", "minValue": 30, "maxValue": 240, "defaultValue": 120},
  "num_workers": {"type": "range", "maxValue": 32},
  "azure_attributes.availability": {"type": "fixed", "value": "SPOT_WITH_FALLBACK_AZURE"},
  "azure_attributes.first_on_demand": {"type": "fixed", "value": 1},
  "azure_attributes.spot_bid_max_price": {"type": "fixed", "value": -1},
  "custom_tags.cost_center": {"type": "regex", "pattern": "^cc-[0-9]{6}$"},
  "custom_tags.workload": {"type": "fixed", "value": "ml"},
  "custom_tags.data_classification": {"type": "allowlist", "values": ["non-phi", "deid", "phi"]}
}
```

```json
// 3. Job (production, no humans) — narrow, Photon-default, Jobs Compute
{
  "cluster_type": {"type": "fixed", "value": "job"},
  "spark_version": {"type": "regex", "pattern": "^17\\.[0-9]+\\.x-scala2\\.13$"},
  "node_type_id": {"type": "allowlist", "values": [
    "Standard_DS4_v5", "Standard_DS5_v5", "Standard_E8ds_v5", "Standard_E16ds_v5"
  ]},
  "data_security_mode": {"type": "fixed", "value": "SINGLE_USER"},
  "runtime_engine": {"type": "fixed", "value": "PHOTON"},
  "azure_attributes.availability": {"type": "fixed", "value": "SPOT_WITH_FALLBACK_AZURE"},
  "azure_attributes.first_on_demand": {"type": "fixed", "value": 1},
  "num_workers": {"type": "range", "maxValue": 50},
  "custom_tags.cost_center": {"type": "regex", "pattern": "^cc-[0-9]{6}$"},
  "custom_tags.workload": {"type": "fixed", "value": "etl"},
  "custom_tags.data_classification": {"type": "allowlist", "values": ["non-phi", "deid", "phi"]}
}
```

```json
// 4. Platform Admin / Break-Glass — broad, audited, time-limited
{
  "spark_version": {"type": "unlimited", "isOptional": false},
  "node_type_id": {"type": "unlimited"},
  "data_security_mode": {"type": "allowlist", "values": ["SINGLE_USER", "USER_ISOLATION"]},
  "autotermination_minutes": {"type": "range", "minValue": 5, "maxValue": 120, "defaultValue": 60},
  "num_workers": {"type": "range", "maxValue": 100},
  "custom_tags.cost_center": {"type": "fixed", "value": "cc-platform-admin"},
  "custom_tags.purpose": {"type": "regex", "pattern": "^break-glass-(incident|investigation|maintenance)-[A-Z]+-[0-9]{4}-[0-9]{2}-[0-9]{2}$"}
}
```

The break-glass policy's `purpose` regex forces every cluster created under it to carry an incident ticket reference, which lands in `system.access.audit` for compliance review. Permission to *use* this policy is granted to the on-call SRE group only and audited monthly.

### The hidden tax: tag enforcement

Tag enforcement at policy level is the single thing that makes chargeback work. Without it, you get free-text tags that don't normalize (`cost-center` vs `cost_center` vs `costcenter`), and the chargeback report explodes. The pattern: enforce a regex on `custom_tags.cost_center`, allowlist on `custom_tags.business_unit`, and require `custom_tags.data_classification` for any HIPAA workspace ([MS Learn — usage detail tags](https://learn.microsoft.com/en-us/azure/databricks/admin/account-settings/usage-detail-tags)).

For serverless workloads, cluster policies don't apply — you need **Serverless Budget Policies** ([Revefi guide](https://www.revefi.com/blog/databricks-serverless-budget-policies-2026)) to enforce the same tags. Module 17 covers this.

---

## Instance pools — the latency-vs-cost trade

**Instance pools** are pre-warmed VM pools; clusters claim from the pool instead of waiting on Azure VM provisioning. Reduces classic-cluster startup from 3–7 min to ~30 sec for the cluster scheduler portion (the DBR install still happens). Tags on pools propagate to clusters that use them.

**When pools save money:** teams with frequent ephemeral cluster creation (CI integration jobs, ad-hoc analyst sessions). The idle-VM cost of the pool is offset by faster startup × frequency.

**When pools waste money:** low-frequency clusters. A pool with 4 idle VMs at $0.40/hr each that gets one cluster spin-up per day burns $35/day for ~5 minutes saved. Don't run pools at min_idle > 0 for low-traffic environments.

**Tag inheritance gotcha:** **cluster tags override pool tags on billing rows.** If a cluster forgets a `cost_center` tag, the pool's tag does *not* automatically backfill. Enforce both at policy level.

---

## Autoscaling — when it helps, when it actively hurts

Autoscaling adjusts worker count based on pending tasks. Sounds great. The Sync Computing TPC-DS 100GB benchmark found **default autoscaling 37% more expensive AND 14% slower** than a tuned fixed cluster ([Sync benchmark](https://medium.com/sync-computing/is-databrickss-autoscaling-cost-efficient-610e6ece4831)). Two reasons:
1. **Upscale events burn minutes** in `RESIZING → UPSIZE_COMPLETED`, plus init-script reinitialization on new nodes.
2. **The autoscaler bounces 1↔2 nodes** mid-job for short bursts that don't justify the up/down cost.

**When autoscaling actually wins:**
- **Ad-hoc / interactive** workloads where load is unpredictable.
- **Long-running clusters** where the savings on idle minutes outweigh the upscale cost.

**When fixed clusters win:**
- **Predictable batch jobs** — size once with empirical data, run forever. This is most production ETL.
- **Photon-heavy SQL** where startup-on-demand is short anyway.

**The Spot interaction trap:** autoscaling sees pending tasks and asks for more workers. If Spot capacity is unavailable in the region, Databricks falls back to On-Demand silently. You signed up for 90% savings and ended up paying list price during a regional Spot crunch. Mitigation:
- `azure_attributes.first_on_demand` = 1 — the driver is always On-Demand (avoids preemption killing the cluster mid-run)
- `azure_attributes.availability` = `SPOT_WITH_FALLBACK_AZURE` — workers are Spot, fall back to On-Demand if needed
- Set explicit Spot ceilings in cluster policy so the fallback is bounded.

---

## When NOT to use Databricks compute

For completeness, cases where some other compute fits better:

1. **Pure SQL BI under 1 TB** — DuckDB on a beefy VM beats spinning a Spark cluster, no DBU, no shuffle.
2. **Sub-100ms streaming feature serving** — Lakebase or a dedicated Redis / DynamoDB beats round-tripping through Spark.
3. **Sub-second model inference at extreme cost-per-token** — vLLM-on-AKS will outprice Mosaic Serving for a mature MLE team.
4. **Custom CUDA / Triton / FlashAttention research** — DBR pins CUDA versions; raw AKS with GPU operator gives full control.
5. **Notebook with ten users, one shared dataset, hourly load** — Snowflake at warehouse-suspended-when-idle is operationally simpler.

For Optum scale none of these are blockers; they exist to know when *not* to over-fit Databricks to a problem.

---

## Production reality

### The "default cluster" tax

Most workspaces run with default cluster policies (or none) for the first 6–12 months. The cost shape that emerges:
- Devs make per-person All-Purpose clusters (~$400/mo idle each × 30 devs = **$144K/yr of nothing**).
- One forgotten cluster left running over a month: **$1,000+** ([Youssef cost playbook](https://medium.com/@ahmed.youssef12377/databricks-cost-optimization-playbook-lessons-from-cutting-production-costs-by-over-80-0e81d8b7a374)).
- A "scheduled" workload accidentally on All-Purpose: 3.6× the real cost.
- Photon turned on globally: 2× DBU on every UDF-heavy ETL job for nothing.

The fix is mostly admin, not engineering — see Module 17.

### Cluster startup pain

Classic cluster startup is 3–7 min typical, sometimes 10 min ([Community thread 78172](https://community.databricks.com/t5/data-engineering/databricks-cluster-random-slow-start-times/td-p/78172)). For a job that runs in 90 seconds the math doesn't work — you spend 4 minutes warming the cluster to do 1.5 minutes of work. Three workarounds, in order of preference:
1. **Move to Serverless Jobs Compute.** Sub-minute startup. The right answer when latency matters and the workload isn't streaming-cheap.
2. **Use Instance Pools.** Cluster scheduler runs in ~30 sec; DBR install still happens. Helps if you're not on serverless.
3. **Co-locate small jobs into one larger job.** If you're running 50 jobs of 90 sec each on independent clusters, batch them into one DAG.

### Library install conflicts

Databricks "cannot guarantee the order in which specific libraries are installed on the cluster" ([library docs](https://docs.databricks.com/aws/en/libraries/)). Built-in DBR libs silently override user-installed libs. One community report: a wheel installed as a JAR by Python Wheel Task ([Community 33146](https://community.databricks.com/t5/data-engineering/bug-databricks-install-whl-as-jar-in-python-wheel-task/td-p/33146)). The recommended fix — "use one wheel containing all deps" — collides with corporate artifact-repo policies that forbid bundling third-party code.

The pragmatic discipline: **pin all your dep versions in a `pyproject.toml`-driven wheel; build it in CI; install it as the only library on the cluster; let DBR provide everything else.** Use a private PyPI mirror (Azure Artifacts, JFrog) for the regulated case where you can't pull from public PyPI.

### `databricks-connect` version drift

The local `databricks-connect` package's major.minor must match the cluster's DBR version, but the VS Code extension defaulted to the wrong version for over a year ([GitHub #1391](https://github.com/databricks/databricks-vscode/issues/1391)). Worse: installing `databricks-connect` removes local `pyspark` (mutually exclusive). Every DBR upgrade triggers a coordinated team-wide local-env upgrade, or CI breaks silently. Plan for it.

---

## Sanity check

1. A scheduled job currently runs on **All-Purpose Compute** at $0.55/DBU. What's the dollar cut from migrating it to Jobs Compute, and what — if anything — has to change in the job code?
2. You're benchmarking Photon on a Spark job that's 70% Python UDF. The job runs 8% faster with Photon on. Should you keep it on?
3. Your team has 30 dev ML clusters, one per person. You suspect $100K+/yr in idle waste. What three policy levers would you pull?
4. A user reports their cluster won't accept a `databricks-connect` connection from VS Code. The cluster is on DBR 17.3 LTS. What's the most likely root cause and how do you fix it?
5. The platform team wants to enforce that **every cluster carries a `cost_center` tag and uses an approved DBR LTS**. What's the JSON snippet inside a cluster policy that does this?
6. A streaming Bronze job is auto-scaling between 1 and 2 nodes for short bursts and the bill is high. What would you do, and why is autoscaling sometimes the wrong default?

---

## Further reading

- [Compute configuration reference — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/compute/configure)
- [GPU-enabled compute — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/compute/gpu)
- [Photon — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/compute/photon)
- [Cluster policies reference — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/admin/clusters/policies)
- [Init scripts migration guidance — Databricks KB](https://kb.databricks.com/clusters/migration-guidance-for-init-scripts-on-dbfs)
- [Sync Computing — Photon TPC-DS benchmark](https://medium.com/sync-computing/are-databricks-clusters-with-photon-and-graviton-instances-worth-it-845641d464f2)
- [Sync Computing — Is autoscaling cost-efficient?](https://medium.com/sync-computing/is-databrickss-autoscaling-cost-efficient-610e6ece4831)
- [Miles Cole — Is Databricks Photon a no-brainer?](https://milescole.dev/data-engineering/2024/04/30/Is-Databricks-Photon-A-NoBrainer.html)
- [Spot instance best practices — MS Tech Community](https://techcommunity.microsoft.com/blog/microsoftmissioncriticalblog/azure-databricks---best-practices-for-using-spot-instances-in-cluster-scaling/4402018)
- [Bauplan — To serverless or not](https://www.bauplanlabs.com/post/to-serverless-or-not-to-serverless)
- [Zipher — When is Photon worth it?](https://zipher.cloud/when-is-databricks-photon-worth-it/)
