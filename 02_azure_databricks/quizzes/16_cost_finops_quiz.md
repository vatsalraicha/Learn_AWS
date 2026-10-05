# Quiz — Module 16: Cost & FinOps for AI Architects

## Recall

**Q1.** What is the Two-Bill Surprise, and what's the practitioner rule of thumb for total spend?

<details><summary>Answer</summary>

**Two-Bill Surprise:** Databricks billing has two distinct line items that show up in different places in Azure Cost Management:
1. **DBU charge** (Databricks software fee)
2. **Azure VM/storage/network charge** (Microsoft)

Teams budget against the DBU rate they see on databricks.com/pricing, then get blindsided when the underlying VM, storage, and networking bill arrives separately.

**Practitioner rule of thumb:** **budget $2–$3 of total spend per $1 of DBU spend.** Forecasts that count only DBUs are systematically low.
</details>

**Q2.** What is the DBCU forfeit-not-rollover trap, and how does it shape commit sizing?

<details><summary>Answer</summary>

**DBCU = Databricks Commit Units.** Prepurchased 1- or 3-year. Discount: 10–15% (1y) up to ~37% (3y) off list price. Apply across all SKUs (cross-SKU flexible).

**The forfeit trap:**
- If you **under-commit:** you get list price on overage, no penalty.
- If you **over-commit:** DBCUs do **NOT roll over past the term — you forfeit unused units.**

**Right-size to the *p25–p50* of your forecasted spend, not p75.** Get the discount on the predictable floor; leave the rest on-demand. Forecasting from `system.billing.usage` per workload type gives you the data to commit at the lower-bound 25th percentile safely.
</details>

**Q3.** What's the single biggest cost lever on the Databricks side that requires zero engineering work?

<details><summary>Answer</summary>

**Migrate scheduled jobs from All-Purpose Compute to Jobs Compute.** That's a **3.6× cost cut** on the Databricks side ($0.55/DBU → $0.15/DBU on Azure Premium), with no code changes — only the job's `existing_cluster_id` (or job_cluster definition) changes.

In Asset Bundles: change `existing_cluster_id: <all-purpose-id>` to a `new_cluster:` definition (or `job_cluster_key:` reference) that uses Jobs Compute pricing.

For most teams that grew up on shared interactive clusters, this is the **single highest-ROI lever on the platform.** A team running 50 scheduled jobs at 20 DBU-hours/night × 250 nights/yr saves ~$100K/yr from this one change.
</details>

---

## Apply

**Q4.** Write the SQL chargeback query that joins `system.billing.usage` with `system.billing.list_prices` to get monthly cost by business unit.

<details><summary>Answer</summary>

```sql
WITH monthly_usage AS (
  SELECT
    custom_tags['business_unit']  AS bu,
    custom_tags['cost_center']    AS cc,
    custom_tags['environment']    AS env,
    sku_name,
    cloud,
    date_trunc('month', usage_date) AS usage_month,
    SUM(usage_quantity) AS dbu
  FROM system.billing.usage
  WHERE usage_date >= current_date - INTERVAL 90 DAYS
  GROUP BY 1, 2, 3, 4, 5, 6
)
SELECT 
  u.usage_month,
  u.bu,
  u.cc,
  u.env,
  u.sku_name,
  u.dbu,
  ROUND(u.dbu * p.pricing.default, 2) AS list_cost
FROM monthly_usage u
LEFT JOIN system.billing.list_prices p
  ON u.sku_name = p.sku_name 
  AND u.cloud = p.cloud
WHERE p.price_start_time <= u.usage_month 
  AND (p.price_end_time IS NULL OR p.price_end_time > u.usage_month)
ORDER BY u.usage_month DESC, list_cost DESC;
```

**Discipline:**
- Join `list_prices` for $-denominated cost (DBU is unit-of-consumption, not money).
- Filter on `price_start_time` / `price_end_time` to handle SKU rate changes over time.
- Group by tag dimensions for chargeback; without good tags this query is useless (Module 17 covers the cluster policy that enforces tags).
- Pin to a **Lakeview dashboard** so finance can self-serve.
- **For SQL warehouses,** join `system.compute.warehouses` to map warehouse_id → tags.
- **For models/serving,** the SKU shows up under MODEL_SERVING / BATCH_INFERENCE; tag at endpoint level.

**The architect's discipline:** the dashboard built from this query is what turns "Databricks is expensive" into "AI is X% of the data platform bill." Build it once; refresh weekly.
</details>

---

## Diagnose

**Q5.** A team's monthly Databricks bill grew 40% over 3 months with no obvious change. The architect digs in. Walk through the diagnosis approach.

<details><summary>Answer</summary>

**Diagnostic approach:**

1. **Pull `system.billing.usage` for the last 90 days, grouped by (week, sku_name, cluster_id).** Find the SKU that grew. Common patterns:
   - All-Purpose growth → cluster sprawl or someone using interactive for scheduled work
   - Jobs Compute growth → expected job growth or runaway autoscale
   - Serverless SQL growth → bursty BI growing into sustained load
   - Model Serving growth → new endpoint or warm-pool creep

2. **Drill into the top 5 cost concentrators.** From the Youssef playbook: "**one job was 70%+ of total job spend.**" Often a single workload is the issue.

3. **Check for anti-patterns:**
   - **Idle clusters** — look at `system.compute.clusters` for `last_terminate_time` patterns; clusters with `auto_terminate_minutes` unset
   - **Autoscale runaway** — look at `system.compute.cluster_events` for nodes scaled up but jobs that completed in seconds
   - **Photon turned on globally for UDF-heavy code** — pay 2× DBU for nothing
   - **DLT in continuous mode** when the SLA is next-business-day
   - **Forgotten Model Serving endpoint** — Medium A10G held warm = ~$1,400/mo of pure idle

4. **Check for storage-side growth:**
   - VACUUM not running → time-travel bloat
   - CDF enabled where no consumer reads
   - Predictive Optimization disabled per-table by mistake

5. **Check for upstream changes:**
   - New job deployed without policy review
   - DBR upgrade changed default behavior
   - Source data volume grew (legitimate growth, but verify)

**The architect's deliverable:** a written summary with:
- Top 3 cost growth drivers, with numbers
- Recommended fixes per driver, ROI estimate
- Policy changes to prevent recurrence (cluster policy update, monitoring alert)

**Tools to consider** if the analysis takes >2 days repeatedly: Sync Gradient or Unravel. Native is fine for the first $2M/yr; tooling pays back beyond that scale.
</details>

---

## Defend

**Q6.** A peer says "we should commit to a 3-year DBCU at our current burn rate to lock in the 37% discount." Defend or refute.

<details><summary>Answer</summary>

**Calibrate — direction is right, sizing matters.**

Where the peer is right:
- **3-year DBCU is the maximum-discount tier**, up to ~37% off list (per Microsoft published guidance).
- **Multi-year commits unlock 15–25% additional discount levers** beyond the published prepay rate.
- For an org with stable, predictable Databricks spend, this is real money.

Where the peer is wrong (the sizing question):
- **"Current burn rate"** is the wrong target. **Commit to the *p25–p50* of forecasted spend, not p75 or current.**
- DBCUs **forfeit if you over-commit.** Not partial — fully forfeit. Locking in current burn rate guarantees over-commit if growth slows or workloads optimize.
- The ~37% discount is the headline; the realized discount on over-committed DBCUs is **0%** (because forfeited DBCUs are pure waste).

**The architect's defensible commit math:**

1. Pull monthly DBU consumption per SKU for the last 12 months from `system.billing.usage`.
2. **Take the lower-bound 25th percentile** of monthly consumption per SKU.
3. **Commit that as the 3-year DBCU base.** This is your "predictable floor."
4. **Run the variable peak on PAYG.** No DBCU discount on the peak, but no forfeit risk either.

**Worked example:**
- Current burn: 1M DBU/month
- Last 12 months ranged 600K-1.1M DBU/month (high variance from new workloads, optimization, seasonality)
- p25 = ~700K DBU/month
- **Commit 700K DBU/month for 3 years** → realized 37% discount
- **Run the rest (300K-400K DBU peaks) on PAYG** → no discount but no forfeit

**Vs the peer's pitch:**
- Commit 1M DBU/month for 3 years
- If actual usage trends down to 800K (legitimate optimization): **forfeit 200K DBU/month × 36 months = 7.2M DBU forfeit.** At ~$0.20/DBU effective, that's **$1.44M in forfeited prepay.**

**The architect's pitch:** "We're 100% on the 3-year commit direction; the discount is real money. The right size is p25 of historical, not current. That captures the predictable floor while preserving optionality on the variable peak. Forfeit risk is the killer; we're going to size around it, not into it."

**Production discipline:** review the commit annually. If usage is consistently above commit + variability, increase commit at renewal. **Never lock in current burn at first commit.**

**Sources:** [Prepay Databricks reserved capacity](https://learn.microsoft.com/en-us/azure/cost-management-billing/reservations/prepay-databricks-reserved-capacity), [Reservation discount applied](https://learn.microsoft.com/en-us/azure/cost-management-billing/reservations/reservation-discount-databricks).
</details>

**Q7.** A peer says "we should standardize on Serverless for everything to simplify our cost model." Defend or refute.

<details><summary>Answer</summary>

**Refute, with calibration.**

Where the peer is right:
- **Serverless simplifies the cost model** — one bill, no VM line item, no instance-type tuning, scale-to-zero for idle workloads.
- **For bursty / unpredictable / interactive workloads, serverless wins on TCO.** No idle cost, sub-minute startup.
- **For new teams without operational maturity**, serverless removes a class of cost-tuning chores (instance selection, Spot configuration, autoscale tuning).

Where the peer is wrong:

1. **Serverless premium ($0.70/DBU SQL Serverless vs $0.55 SQL Pro) doesn't pay back at high utilization.** A warehouse running 70%+ saturated benefits from classic + Reserved VMs underneath; serverless's premium becomes pure overhead.

2. **Serverless DLT cost explosions are documented** — 3–5× more expensive than classic for some workloads (Zipher analysis: €2K burned in two days in one published case). DBU consumption inside serverless is opaque, so you can't tune it.

3. **Loss of architectural levers:**
   - No instance type choice — for memory-intensive joins or GPU-heavy ML, you can't pick the right shape
   - No Spot — for fault-tolerant batch ETL, Spot is 90% savings on the VM side; serverless doesn't have it
   - No custom Docker images — for proprietary library setups, serverless can't accommodate
   - No `.persist()` on serverless Spark — some Spark patterns don't translate
   - No per-job memory/CPU metrics via API — observability is weaker

4. **Cost-model "simplification" is partial.** You still have system.billing.usage with multiple SKUs (serverless SQL, serverless jobs, serverless model serving each have different rates); serverless doesn't make chargeback easier — just removes the VM line.

**The architect's pitch:**
- **Use Serverless for:** bursty BI, dev/staging, interactive analyst pools, embedded analytics in Apps, any workload where utilization < 30%.
- **Use Classic Jobs Compute for:** scheduled ETL with predictable utilization, large saturated warehouses, ML training, custom-library workloads.
- **Measure, don't assume.** Pull `system.billing.usage` for existing workloads; classify each by utilization shape; route accordingly.

**The "all-in on serverless" argument is procurement-shaped, not architecture-shaped.** Different workloads want different compute models; the platform supports both for a reason. **Pick the engine that fits the workload, not the simpler-billing line.**

**Sources:** [Zipher serverless analysis](https://zipher.cloud/databricks-serverless-pros-cons/), [Bauplan to serverless or not](https://www.bauplanlabs.com/post/to-serverless-or-not-to-serverless).
</details>
