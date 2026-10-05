# Quiz 01 — Databricks Intelligence Platform (10%)

> Take cold. ~14 questions. Spend ~2 min per question.

---

## Recall

1. Where in the Databricks architecture does customer Delta data physically live: control plane, compute plane, or storage in the customer cloud?
2. Name the three core compute types available for running workloads on Databricks.
3. What does "DBR LTS" stand for, and approximately how long is its support window?
4. What does Photon do to a Spark cluster?

## Apply

5. A scheduled hourly ETL job runs in production. The team wants to minimize DBU cost. Which cluster type should they pick?
6. The team prompt says "we want hands-off, auto-optimized compute with no cluster tuning." Which compute do you pick?
7. Two BI users complain about 5-minute startup delays on the SQL warehouse. They want sub-30-second startups. What's the fix?
8. A regulated workload mandates that all compute run inside the customer's cloud account. Can the team use serverless?
9. A DE team wants OPTIMIZE and VACUUM to happen automatically on their UC-managed tables. Which feature?

## Diagnose

10. A team's job has been running fine for months on an all-purpose cluster. The cost reports show $20k/month for this job alone. The same logic on a job cluster costs $9k. What's going on?
11. A SQL Warehouse hangs at "starting" for 8 minutes before serving queries. The team needs sub-minute startup. What two changes are reasonable?

## Defend

12. The team is debating Photon vs no Photon. Photon costs ~2× the DBU rate. Argue when Photon wins on $/query.
13. A pre-2025 study guide describes "Workflows" as the orchestration product. A post-2025 doc calls it "Lakeflow Jobs." Are they the same thing? What changed?
14. The boss asks whether to put the DR / failover compute in the same cloud as the primary. Answer briefly.

---

## Answers

1. **Storage in the customer cloud** (S3/ADLS/GCS). Control plane never holds customer data. Classic compute is also in the customer cloud; serverless compute is in Databricks' cloud but reads customer data via short-lived credentials.
2. **All-purpose clusters, job clusters, serverless** (plus SQL Warehouses as a specialized variant).
3. **Long-Term Support** Databricks Runtime — about **24 months** of patches. Non-LTS gets ~6 months.
4. **Vectorized C++ execution engine** that replaces JVM row-at-a-time execution for many operators. 2-10× speedup on SQL/DataFrame workloads, at ~2× the DBU rate.
5. **Job cluster** — ephemeral, ~half the DBU of all-purpose, terminated at job end. If the prompt mentions "hands-off" specifically, serverless. Pure "minimize DBU" → job cluster.
6. **Serverless** — "hands-off / auto-optimized" maps to serverless.
7. **Switch to a serverless SQL warehouse.** Sub-30-second startup vs minutes for classic. Alternatively, an instance pool can pre-warm classic compute, but serverless is the canonical fix.
8. **No** (typically) — serverless runs in Databricks' cloud account, not the customer's. Regulated workloads requiring data residency on the customer's compute must use classic.
9. **Predictive Optimization** — auto OPTIMIZE/VACUUM on UC-managed tables. Default on for newer DBR/UC.
10. **All-purpose clusters cost ~2× the DBU of job clusters.** The job has been paying interactive-priced compute for scheduled work. Switch to a job cluster (or serverless) → roughly halves cost.
11. (1) **Switch to serverless SQL warehouse**, or (2) **enable an instance pool** to pre-warm classic compute. Either reduces startup latency dramatically.
12. **Photon wins when:** (a) query is SQL- or DataFrame-heavy (CPU-bound, not I/O-bound); (b) Photon's 2-10× speedup more than offsets the 2× DBU rate. **Photon loses when:** (a) workload is I/O-bound (no CPU advantage to capture); (b) heavy use of unsupported UDFs; (c) tiny datasets where startup dominates.
13. **Same product, renamed.** "Workflows" / "Jobs" / "Lakeflow Jobs" are the same orchestrator. The engine is unchanged. New exams prefer the "Lakeflow Jobs" terminology; older study guides use "Workflows."
14. **No (typically).** DR / failover compute should be in a **different region** (and ideally a different cloud's region) to survive a regional outage. Same-cloud is fine; same-region defeats the purpose.
