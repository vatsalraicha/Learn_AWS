# Quiz — Module 2: Compute Model Deep Dive

## Recall

**Q1.** Name the five Databricks compute SKUs an architect should know, with their May 2026 Azure Premium $/DBU-hr.

<details><summary>Answer</summary>

- **Jobs Compute (classic):** $0.15/DBU-hr
- **All-Purpose Compute:** $0.55/DBU-hr
- **Serverless Jobs:** ~$0.35/DBU-hr (VM included)
- **SQL Serverless:** $0.70/DBU-hr (VM included)
- **Model Serving:** varies; CPU base $0.07/DBU; GPU 10–628 DBU/hr depending on size
</details>

**Q2.** What is Photon's DBU multiplier, and what's the breakeven speedup needed for it to be net-positive on cost?

<details><summary>Answer</summary>

**2× DBU multiplier.** Breakeven is **~20% speedup** above the bare-instance baseline — the speedup also reduces VM hours and DBU-hours, so the math is not pure 2×/2×. Below 20% speedup, you pay more than you save; above ~30%, Photon clearly wins.
</details>

**Q3.** What three cluster access modes exist as of 2026, and which one is being phased out?

<details><summary>Answer</summary>

- **Single User** — one user, all UC features supported (default for ML)
- **Standard / Shared** — multiple users, isolated Python environments per user, runs queries as the querying user (required for analyst clusters with UC ABAC)
- **No Isolation Shared** — legacy, multiple users, shared identity. **Cannot use UC tables with row/column filters.** Avoid for new work; deprecate where you find it.
</details>

**Q4.** What is the recommended pattern for storing init scripts in 2026, and what was wrong with the previous patterns?

<details><summary>Answer</summary>

**UC Volumes** — store at e.g. `/Volumes/_admin/init/analyst_v3.sh`. Provides governance (UC ACLs), versioning (`_v<n>` suffix in path for rollforward), and audit (every read shows in `system.access.audit`).

The previous patterns:
1. **DBFS-stored cluster-scoped init scripts** — deprecated May 2023.
2. **Cluster-named DBFS init scripts** — disabled outright Dec 1, 2023.
3. **Workspace files** — works but lacks governance/audit primitives Volumes provide.

The "3 migrations in ~3 years" history is itself a teaching point — the platform's right answer churns; design for change.
</details>

---

## Apply

**Q5.** A team has 50 scheduled jobs running on All-Purpose clusters at an average of 20 DBU-hours each per night. They run 250 nights a year. What's the annual savings from migrating these jobs to Jobs Compute, and is there any code change required?

<details><summary>Answer</summary>

Per-job savings: 20 DBU-hr × ($0.55 - $0.15) = **$8/job/night**.
Annual savings: 50 jobs × $8 × 250 nights = **$100,000/yr** on the Databricks side. Azure VM cost is unchanged (same instance types).

**Code change:** none. The job code is identical; only the *where it runs* changes. In a Databricks Asset Bundle, you change `existing_cluster_id` to a `job_cluster` definition (or to a serverless job). For ad-hoc one-off jobs, configure the job-level cluster instead of attaching to an interactive cluster.

This is the **single highest-ROI lever on the platform** for any team that grew up doing scheduled work on shared interactive clusters.
</details>

**Q6.** Write a cluster policy snippet that enforces:
- DBR 17.3 LTS only
- `cost_center` tag matching `cc-` followed by 6 digits
- `business_unit` from a fixed list of {`claims`, `member`, `provider`}
- USER_ISOLATION mode
- Auto-termination between 15 and 120 minutes

<details><summary>Answer</summary>

```json
{
  "spark_version": {"type": "fixed", "value": "17.3.x-scala2.13"},
  "data_security_mode": {"type": "fixed", "value": "USER_ISOLATION"},
  "autotermination_minutes": {"type": "range", "minValue": 15, "maxValue": 120, "defaultValue": 30},
  "custom_tags.cost_center": {"type": "regex", "pattern": "^cc-[0-9]{6}$"},
  "custom_tags.business_unit": {"type": "allowlist", "values": ["claims", "member", "provider"]}
}
```

In production you'd also constrain `node_type_id`, `num_workers`, and `init_scripts` — see the Module 2 examples.
</details>

---

## Diagnose

**Q7.** A team complains their classic cluster takes 8 minutes to start up "randomly" — sometimes 3 minutes, sometimes 10. What are the likely contributing factors, and what would you propose?

<details><summary>Answer</summary>

Contributing factors (in rough likelihood order):
1. **Azure VM provisioning latency** — 1–4 min, varies by region, instance type, and current capacity pressure. H100 capacity is especially fluid in HIPAA-eligible regions.
2. **DBR install on each node** — 30–90 sec per node; hits *every node* even when an instance pool warms the VM.
3. **Init script execution** — every node runs init scripts at boot. A slow corp-CA install or a `pip install` of a heavy library can add minutes. Library install conflicts can extend further.
4. **Spot capacity unavailability** — if the cluster requested Spot and Azure says no, the autoscaler falls back silently to On-Demand, which adds time.
5. **NSG / Private Link DNS resolution** — for VNet-injected workspaces, DNS resolution to control-plane FQDNs can stall.

Proposals:
- Move to **Serverless Jobs** for any latency-sensitive scheduled workload (sub-minute startup).
- Use **Instance Pools** with min_idle > 0 if the workload pattern justifies it.
- **Profile the init scripts** — replace heavy `pip install` with a pre-built wheel; cache corp CAs in the DBR custom container if possible.
- For VNet-injected workspaces, audit the DNS path — Module 20 covers this.
</details>

**Q8.** A platform admin sees that the same job sometimes takes 12 minutes and sometimes takes 25 minutes on the same All-Purpose cluster. Spot is enabled. What's the most likely cause, and how would you make the runtime predictable?

<details><summary>Answer</summary>

**Most likely:** Spot preemption mid-run. When Azure reclaims a Spot node, Spark loses an executor and re-runs the lost tasks on a new node. For a job with broad shuffle dependencies, this cascades — the re-run can take longer than the original run.

The autoscaler also can mask this — when a Spot is preempted, the autoscaler asks for a replacement; if Spot is unavailable, it falls back to On-Demand silently, restoring runtime but with a billing surprise.

**To make runtime predictable:**
1. Move scheduled work off All-Purpose to **Jobs Compute** (cost cut + isolation).
2. Set **`first_on_demand` = 1** so the driver is always On-Demand (driver preemption kills the cluster mid-run, much worse than worker preemption).
3. For SLA-sensitive workloads, **disable Spot entirely** and accept the higher VM cost. Spot is for fault-tolerant batch ETL with retries enabled, not for streaming or near-real-time.
4. Right-size the cluster from `system.billing.usage` data — fixed beats autoscaling for predictable batch.
5. Consider **Serverless Jobs** if the workload isn't huge — Spot risk is the platform's, not yours.
</details>

---

## Defend

**Q9.** A peer engineer argues "Photon should be on by default everywhere — Databricks recommends it." Defend or refute.

<details><summary>Answer</summary>

**Refute, with calibration.**

Where the peer is right:
- For **SQL warehouses, Spark SQL, and DataFrame native operations** (joins, aggregations, sorts, window functions, native Parquet read/write, MERGE/UPDATE/DELETE), Photon delivers ~2–3× speedup that comfortably clears the 20% breakeven. Default-on for those is correct.
- DLT/Lakeflow defaults to Photon; that's correct because the typical declarative pipeline is SQL/DataFrame-shaped.

Where the peer is wrong:
- For **Python UDF-heavy code**, Photon doesn't help — UDFs run in Python, the C++ kernel doesn't apply. You pay 2× DBU for nothing.
- For **Pandas UDFs**, partial benefit but generally below the 20% margin.
- For **RDD code, Spark MLlib training loops, and append-mostly streaming with simple transformations**, Photon either doesn't run or doesn't help enough.
- **Tiny data jobs** (< 10 GB) don't amortize Photon's setup overhead.
- Miles Cole's TPC-style benchmark documented **Query 6 cost 72% MORE with Photon** — this isn't theoretical, it's a measured outcome.

**Production discipline:** benchmark per workload type, then encode the decision in cluster policy. Job clusters for SQL/ETL → Photon on. Job clusters for ML training or UDF-heavy ETL → Photon off, benchmark per case. The 2× DBU multiplier is a real tax; pay it where it pays back.
</details>

**Q10.** A FinOps lead argues the team should "go all-in on Serverless Jobs Compute — it's the future, and we'll save money on idle." Defend or refute.

<details><summary>Answer</summary>

**Calibrate — partially right, partially wrong.**

Where they're right:
- **Spiky / interactive / unknown-utilization workloads** absolutely save on serverless because there's no idle bill.
- **Sub-minute startup** is a real productivity win for development.
- **One billing line** (DBU includes VM) is simpler than two.

Where they're wrong:
- **DLT/Lakeflow on serverless has been known to cost 3–5× classic** — €2,000 burned in two days reported in production ([Zipher](https://zipher.cloud/databricks-serverless-pros-cons/)). Workload-shape dependent.
- **Predictable, large, long-running batch jobs** at high utilization are cheaper on classic Jobs Compute with Spot workers. Serverless's $0.35/DBU + included VM doesn't always beat $0.15/DBU + Spot VM at $0.05/hr.
- **No instance type, no Spot, no custom Docker image** — you lose the levers that classic gives you.
- **Cold-start re-installs your dependencies every time** — heavy deps (transformers, torch) make this painful.
- **No `.persist()` on serverless** — caching API restricted; some Spark patterns don't translate.

**The right framing for the FinOps lead:** serverless wins on flexibility and idle-cost; classic wins on predictable saturated workloads. Pull `system.billing.usage` for the team's existing workloads, classify each by utilization shape, route accordingly. **"All-in on serverless" is a bumper sticker, not a strategy.** Module 16 has the math.
</details>
