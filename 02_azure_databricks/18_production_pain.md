# Module 18 — Production Pain, Anti-Patterns, War Stories

> **Goal of this module:** the production reality that vendor marketing won't surface — the 25 pain points practitioners cite repeatedly, the teams who left Databricks (and why), the anti-patterns experienced engineers warn newcomers about, and the gaps between the happy path and what actually ships.

---

## Why this module exists

A teaching corpus that only covers "how things work in the brochure" produces architects who can't troubleshoot. This module captures the **failure modes** — the things that go wrong on real Databricks deployments — so that an architect at Optum recognizes them before they ship to production rather than after.

The frame: **Databricks is a serious platform with serious tradeoffs.** Marketing pretends the platform is the answer to everything; r/dataengineering and HN tell a different story. Both are right. The architect's job is to use the strong parts well and avoid the weak parts.

---

## The top 25 production pain points

### 1. The Two-Bill Surprise

DBU sticker shock + cloud infra invoice. Practitioners now warn newcomers to **budget $2–3 of total spend per $1 of DBU spend** ([Flexera](https://www.flexera.com/blog/finops/snowflake-vs-databricks/), [Confessions of a Data Guy](https://www.confessionsofadataguy.com/databricks-doubles-cost-reddit-explodes-im-in-trouble/)). Module 16.

### 2. Classic compute cluster startup latency (3–10 min)

Classic job clusters routinely take 3–7 minutes to spin up; community thread documented "random slow start times" up to 10 minutes ([Community 78172](https://community.databricks.com/t5/data-engineering/databricks-cluster-random-slow-start-times/td-p/78172)). For short jobs this dwarfs actual compute. Workarounds: shared all-purpose clusters with pool warmup, serverless, or instance pools.

### 3. Serverless cold start + dependency reinstall

Serverless was supposed to fix #2, but every cold start re-downloads and installs the full dependency tree onto fresh nodes ([Bauplan analysis](https://www.bauplanlabs.com/post/to-serverless-or-not-to-serverless), [HN 43899252](https://news.ycombinator.com/item?id=43899252)). Top HN comment: an *"endless progression of unpleasant surprises and being told 'oh no you can't do it that way.'"*

### 4. Serverless DLT cost explosions (3–5× classic)

Multiple production reports of 3–5× cost increases moving DLT to serverless. One user reported €2,000 burned in two days; Zipher analysis: Serverless 3× more expensive than cheapest on-demand worker, 4.5× vs spot ([Zipher](https://zipher.cloud/databricks-serverless-pros-cons/)).

### 5. Photon's actual ROI is workload-dependent, not "always on"

Photon imposes a flat 2× DBU multiplier; must produce >2× speedup to be net-positive. Miles Cole's TPC-style benchmark showed roughly 2.7× average speedup but **Query 6 cost 72% more with Photon** ([Miles Cole](https://milescole.dev/data-engineering/2024/04/30/Is-Databricks-Photon-A-NoBrainer.html)). "Photon everywhere by default" is an anti-pattern.

### 6. Autoscaling thrashing — slower AND more expensive

Sync Computing benchmarked default autoscaling against fixed clusters on TPC-DS 100GB: **37% more expensive AND 14% slower** than a tuned fixed cluster ([Sync Computing](https://medium.com/sync-computing/is-databrickss-autoscaling-cost-efficient-610e6ece4831)).

### 7. Unity Catalog migration is an organizational project, not a tool run

Real migrations break dashboards, dbt refs, IAM-backed external locations, and incremental model self-references. Reliable Data Engineering's 500-model dbt migration documented the breakage extensively ([Medium](https://medium.com/@reliabledataengineering/i-migrated-500-dbt-models-to-databricks-unity-catalog-heres-what-broke-and-what-got-10x-2a2dc93f548b)). Module 10.

### 8. UCX is "explore only" — not officially supported

The official UCX migration toolkit is a Databricks Labs project explicitly marked "not formally supported with SLAs" ([UCX docs](https://databrickslabs.github.io/ucx/)). Multiple community-reported failures.

### 9. Workspace ACL ↔ Unity Catalog permission collision

Three permission systems coexist; mid-migration produces broken dashboards and lost access. Module 9.

### 10. databricks-connect version drift vs cluster DBR

Local package's major.minor must match cluster DBR; VS Code extension defaulted to wrong version for over a year ([GitHub #1391](https://github.com/databricks/databricks-vscode/issues/1391)). Module 5.

### 11. Notebook code review hell

JSON `.ipynb` diffs unreadable; autosave fights "save when I commit"; outputs blow repo size; reviewers can't read JSON deltas with embedded outputs ([Repos limits](https://learn.microsoft.com/en-us/azure/databricks/repos/limits)). Module 4 covered the mitigation pattern.

### 12. Repos size limits and monorepo penalties

Databricks Git folders explicitly recommend against monorepo-backed clones — "cloning a monorepo can exceed Git folder memory and disk limits and slow Git operations." For healthcare orgs that want one shared monorepo for compliance traceability, this is a real architectural tax.

### 13. Init-script deprecation churn

DBFS-stored cluster-scoped init scripts deprecated May 2023; cluster-named scripts disabled Dec 1, 2023; UC volumes is the current pattern. **Multiple migration steps within ~3 years** has eroded trust that today's "right way" will still work in two years.

### 14. Library install conflicts and non-deterministic order

Databricks "cannot guarantee the order in which specific libraries are installed on the cluster" ([library docs](https://docs.databricks.com/aws/en/libraries/)); precedence rules between built-in DBR libs and user-installed libs cause silent version overrides; one community post reported a wheel installed as JAR by Python Wheel Task ([Community 33146](https://community.databricks.com/t5/data-engineering/bug-databricks-install-whl-as-jar-in-python-wheel-task/td-p/33146)).

### 15. Secrets handling friction (especially Azure Key Vault + RBAC)

Secret scope creation has no UI link — append `#secrets/createScope` to URL. Key-Vault-backed scopes don't natively work with RBAC-only Key Vaults — you must give the AzureDatabricks enterprise app the "Key Vault Secrets User" role at the vault level, which means **every Databricks workspace in your tenant can theoretically access that vault** ([Community 86836](https://community.databricks.com/t5/administration-architecture/secret-scope-with-azure-rbac/td-p/86836)).

### 16. Model Serving cold start with no SLA on scale-from-zero

Documented as "10–20 seconds, but can sometimes take minutes" with **no SLA** ([Databricks docs](https://docs.databricks.com/aws/en/machine-learning/model-serving/production-optimization)). Module 14.

### 17. DLT / Lakeflow Declarative Pipelines debugging opacity

`target` vs `schema` confusion; breaking schema changes leave pipelines unable to recover without manually resetting CDC and recreating bundles ([Community 127147](https://community.databricks.com/t5/data-engineering/problems-and-questions-with-deploying-lakeflow-declarative/td-p/127147)). Module 4.

### 18. Cost attribution / chargeback requires policy-enforced tagging

Tags don't propagate unless enforced via cluster policy and serverless budget policies; without policy, users create untagged clusters and DBUs become unattributable. **Months-long FinOps cleanup** before chargeback is credible.

### 19. Asset Bundles ("DABs") YAML sprawl

Daniel Beach: *"I don't want to be a YAML engineer any more than you do. It's one thing to have IAC (Infrastructure as Code), and another thing to have Pipelines as Code"* ([Substack](https://dataengineeringcentral.substack.com/p/simplifying-cicd-with-databricks)). Module 19.

### 20. Multi-region DR is customer-driven, not platform-provided

"Azure Databricks requires a customer-driven approach to disaster recovery" — you replicate workspaces, infra, security configs, and Delta tables yourself ([DR docs](https://learn.microsoft.com/en-us/azure/databricks/admin/disaster-recovery)). Module 23.

### 21. Delta Sharing — gotchas behind the marketing

Documented limits: cannot share liquid-clustered tables with partition filtering, cannot share row-filtered or column-masked tables, cannot share SHALLOW CLONE tables. Cross-environment (commercial → GovCloud, AWS GovCloud → Azure China) is unsupported. Module 11.

### 22. Caching and memory behavior is "unknowable" to users

A widely-shared Medium critique: *"You clear the cache; things remain mysteriously cached. You cache explicitly; your data evaporates like morning dew"* ([Medium / Uncle Charlie](https://medium.com/@charles_67574/a-critique-of-databricks-the-tyranny-of-false-intelligence-70d007ff64e1)). Module 6 covered the four caching layers; the practitioner experience is that they conflict in surprising ways.

### 23. UC migration causing performance regressions on iterative jobs

Jobs that ran in minutes on Hive take hours on UC because of per-call permission lookups in iterative workloads ([Tredence](https://www.tredence.com/blog/migrating-to-unity-catalog), [Aditya Goyal](https://www.adityagoyalportfolio.com/story-uc-migration)). Module 10.

### 24. The "Medallion Architecture" tax

Daniel Beach: *"the false gospel of the Medallion Architecture wreaked havoc on a generation of Data Engineers"* — three layers per dataset increases storage and compute that flows directly to Databricks revenue ([Confessions](https://www.confessionsofadataguy.com/the-medallion-architecture-farce/)). Module 3.

### 25. UI search and observability gaps

G2/Gartner reviewers complain workspace search "never finds results from a month ago," UI lags behind typing, table drawers auto-close. Per-job memory/CPU metrics aren't exposed via API ([HN 43899252](https://news.ycombinator.com/item?id=43899252)) — observability for a healthcare audit is mostly "build it yourself with system tables."

---

## Teams who left Databricks (or considered it)

### Snowflake migrations from Databricks

Snowflake publicly markets "savings of 50–70% on average when migrating from Databricks" ([Snowflake comparison page](https://www.snowflake.com/en/snowflake-vs-databricks/)). The driver in honest comparisons: **predictability of the bill**, not raw speed. Snowflake's 60-second minimum warehouse resume penalizes spiky workloads, but the tradeoff is fewer FinOps surprises.

### GetYourGuide migrated FROM Snowflake TO Databricks

At -20% cost ([GetYourGuide blog](https://www.getyourguide.careers/posts/from-snowflake-to-databricks-our-cost-effective-journey-to-a-unified-data-warehouse)). The honest reading: it depends on workload mix. **Heavy ML/streaming → Databricks usually wins on TCO. BI/SQL-only → Snowflake usually wins on simplicity.**

### The hybrid pattern — multi-platform is the new "left"

*"Successful enterprises in 2025 aren't choosing one platform — they're orchestrating two or three"* — Snowflake for governed BI, Databricks for ML/AI, Fabric as the integration layer for Microsoft-native shops ([Polestar](https://medium.com/@polestaranalytics/comparing-databricks-snowflake-and-fabric-why-all-three-are-the-best-approach-b04e814caa86)).

### Microsoft Fabric pull on Azure-native shops

Fabric is positioned as "the integration layer for Microsoft-native teams." Power BI shops that previously used Databricks SQL Warehouses now have a credible same-vendor path to leave the Databricks SQL plane.

### OSS Spark + Iceberg (the threat Databricks is most defensive about)

Iceberg interop is the major 2024–2026 concession (Databricks acquired Tabular for ~$1B in 2024). Practitioners considering "leaving" usually mean **replacing Databricks compute with EMR/Glue + Iceberg, or DuckDB + Iceberg for medium-data analytics**, while keeping the data in object storage they already own.

---

## Anti-patterns vendor marketing won't surface

10 anti-patterns to know:

1. **"Just enable Photon everywhere."** Wrong default. Photon costs 2× and is net-negative for VACUUM, OPTIMIZE, RDDs, UDF-heavy code, append-mode writes, dev clusters, short queries.
2. **"Just turn on autoscaling."** Default autoscaling can be 37% more expensive AND slower than a sized fixed cluster for predictable batch.
3. **"Bronze/Silver/Gold for every dataset."** Medallion is a guideline, not a law; applying it indiscriminately triples storage and compute for trivial datasets.
4. **"Use the workspace UI for secrets."** There is no UI for secret-scope creation — append `#secrets/createScope`. If your runbook says "go to the secrets page," you don't have a runbook.
5. **"Migrate tables first, fix permissions when people complain."** The dominant UC migration anti-pattern; produces broad over-grants you'll spend a year clawing back.
6. **"Scale-to-zero in production model serving."** Databricks' own docs say not to.
7. **"Commit notebooks with output."** Repo size explodes; `.gitignore` after-the-fact doesn't help; reviewers can't read JSON diffs.
8. **"DABs as the single source of truth for everything."** Pipelines-as-YAML-as-code becomes its own maintenance burden; abstract aggressively or you become a YAML engineer.
9. **"Key Vault RBAC works fine."** The AzureDatabricks enterprise app gets vault-level access for the whole tenant — review with security before signing off.
10. **"Run UCX, you'll be migrated by Friday."** UCX is unsupported labs code; assessment dashboards stale on re-run; code rewrites are still manual.

---

## Happy path vs reality gaps

### Unity Catalog migration

- **Happy path:** Run UCX → migrate-tables → grant catalog/schema permissions → done.
- **Reality:** Iterative jobs slow due to per-call permission lookups; 500-model dbt rewrites for three-level namespacing; workspace-level SCIM groups must be re-created at the account level; external locations need new IAM/storage credentials. **Plan for 2× the estimated duration.** Module 10.

### DLT / Lakeflow in CI/CD

- **Happy path:** Define pipeline in YAML bundle, deploy via DAB.
- **Reality:** `target` vs `schema` config confusion; breaking schema changes that require manual CDC reset and bundle recreation; opaque debugging through generated Spark code. Local unit testing of DLT logic is hard because DLT's decorator semantics don't replay outside a pipeline runtime.

### Cross-workspace governance

- **Happy path:** Single account, account-level groups, UC catalogs shared across workspaces.
- **Reality:** Workspace-catalog bindings can deny access even when UC grants exist. Mid-migration you have BOTH legacy workspace ACLs and UC grants live; reasoning about effective permissions requires reading three permission models simultaneously.

### Multi-region DR

- **Happy path:** Enable DR; Databricks handles it.
- **Reality:** Customer-driven; Terraform replication of workspace + IAM + UC + secret scopes; Delta deep-clones replicated cross-region; jobs and DAB definitions re-deployed. **For a healthcare payor with paired-region RTO of <4h, this is a multi-quarter platform-engineering project.** Module 23.

### Local development / databricks-connect

- **Happy path:** `databricks-connect configure`, run code locally as if on a cluster.
- **Reality:** Version must match cluster DBR; installation breaks local PySpark; VS Code extension defaulted to the wrong version for over a year. Each DBR upgrade is a coordinated team-wide local-env upgrade.

---

## Other surprises worth surfacing

### Lakebase: OLTP-on-the-lakehouse is brand new and unproven at scale

Databricks acquired Neon (serverless Postgres) and is pitching "Lakebase" as fused OLTP+lakehouse — Daniel Beach's analysis is appropriately skeptical about whether transactional workloads belong on a lakehouse foundation at all ([Confessions on Lakebase](https://www.confessionsofadataguy.com/lakebase-databricks-bold-play-to-fuse-oltp-and-the-lakehouse/)). For a healthcare team this is "wait for v2" territory.

### DBR major-version upgrades are opt-in with real breaking changes

Each new DBR ships Spark + library + behavioral changes that can break tested pipelines. Combined with #10 (databricks-connect lockstep) and #13 (init script churn), DBR upgrades are major undertakings, not patch-Tuesday events. Many shops run on 13.x or 14.x LTS for years, deferring 15.x/16.x adoption.

### Databricks-Reddit relationship is engineered

Foundation Inc. publicly documented how Databricks turned a private subreddit (r/databricks) "into a powerful community engine" ([Foundation case study](https://foundationinc.co/lab/databricks-reddit-strategy)). r/databricks moderation is closer to vendor-managed community than independent practitioner space — for honest pain reports, **r/dataengineering** (where Daniel Beach's posts blew up) and HN are richer.

### Databricks reaches out to public critics

Daniel Beach's account: posting Standard-Tier criticism on LinkedIn/Reddit got "the Databricks folk to hunt me down at work and tell me I'm naughty" ([Confessions](https://www.confessionsofadataguy.com/databricks-doubles-cost-reddit-explodes-im-in-trouble/)). **This is itself a teaching point about vendor relationships at the architect/EM level — public critique can carry account-team consequences.**

### "Databricks won the battle" — Mir Report 2025

A non-marketing recap of DAIS 2025 captured the strategic state: Databricks consolidated category leadership for ML/AI on the lakehouse, but the win was about **ecosystem gravity** (Iceberg interop, Mosaic AI, Lakebase) more than core platform improvements ([Mir Report](https://mir.report/p/how-databricks-won-the-battle-for)). Translation for an architect: **betting on Databricks today is a bet on ecosystem lock-in, not on irreplaceable engineering** — keep your data in Delta + Iceberg-readable form so you have an exit option.

---

## Bottom-line synthesis (for an AI Architect / EM in healthcare)

1. **Cost predictability is Databricks' weakest point.** Build a FinOps function before the platform expands, not after. Enforce tags via cluster policy from day one.
2. **Photon, autoscaling, and serverless are workload-specific tools, not defaults.** Benchmark per workload; Sync Computing-style empirical analysis pays for itself.
3. **Unity Catalog migration is a 6–18 month organizational project.** Treat it as one. UCX accelerates but does not replace governance design.
4. **Secrets, DR, and cross-workspace governance are mostly customer-built on Azure Databricks.** For HIPAA you'll own all three.
5. **Keep an exit door open.** Delta + Iceberg interop, dbt as transformation layer, and storage in the customer's own ADLS keep optionality. Resist Databricks-only constructs (Lakebase, fully proprietary Mosaic features) for production-critical paths until they have multi-year track records.
6. **Read r/dataengineering and HN, not r/databricks.** The first two surface honest pain; the third is a managed channel.

---

## Sanity check

1. The Two-Bill Surprise — what's the practitioner rule of thumb for total spend?
2. Why is "Photon everywhere by default" an anti-pattern?
3. Default autoscaling vs tuned fixed cluster — what's the Sync Computing benchmark result?
4. UC migration is "a 6–18 month organizational project, not a tool run." What's the discipline implication?
5. Why is r/dataengineering a more honest source than r/databricks for production pain reports?
6. What's the architect's exit-door discipline, and why does it matter for a 5-year roadmap?

---

## Further reading

- [Confessions of a Data Guy — Daniel Beach](https://www.confessionsofadataguy.com/) — practitioner-grade honest essays on Databricks
- [Mir Report — How Databricks Won the Battle](https://mir.report/p/how-databricks-won-the-battle-for) — strategic state-of-play
- [Benn Stancil — Category collapse](https://benn.substack.com/p/category-collapse) — contrarian read on lakehouse marketing
- [Sync Computing — Photon TPC-DS benchmark](https://medium.com/sync-computing/are-databricks-clusters-with-photon-and-graviton-instances-worth-it-845641d464f2)
- [Sync Computing — Autoscaling cost-efficient?](https://medium.com/sync-computing/is-databrickss-autoscaling-cost-efficient-610e6ece4831)
- [Miles Cole — Photon TCO analysis](https://milescole.dev/data-engineering/2024/04/30/Is-Databricks-Photon-A-NoBrainer.html)
- [Zipher — Serverless pros and cons](https://zipher.cloud/databricks-serverless-pros-cons/)
- [HN 43899252 — Databricks Serverless critique thread](https://news.ycombinator.com/item?id=43899252)
- [Foundation Inc — Databricks Reddit strategy case study](https://foundationinc.co/lab/databricks-reddit-strategy)
- [Polestar — Databricks + Snowflake + Fabric all three](https://medium.com/@polestaranalytics/comparing-databricks-snowflake-and-fabric-why-all-three-are-the-best-approach-b04e814caa86)
- [Reliable Data Engineering — 500 dbt models migration](https://medium.com/@reliabledataengineering/i-migrated-500-dbt-models-to-databricks-unity-catalog-heres-what-broke-and-what-got-10x-2a2dc93f548b)
- [Karlo Kotarac — UC migration lessons](https://medium.com/valcon-consulting/unity-catalog-migration-best-practices-lessons-learned-from-two-implementations-part-1-f692811643a6)
