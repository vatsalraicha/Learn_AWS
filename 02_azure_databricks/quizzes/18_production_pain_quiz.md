# Quiz — Module 18: Production Pain, Anti-Patterns, War Stories

## Recall

**Q1.** Name five of the top production pain points and link each to the relevant fix or mitigation module.

<details><summary>Answer</summary>

Any five from:
1. **Two-Bill Surprise** (DBU + Azure VM separately) — fix in Module 16 (forecast in $2-3 total per $1 DBU).
2. **Cluster startup 3–10 min** — fix in Module 2 (instance pools, serverless).
3. **Photon's 2× DBU not always net-positive** — fix in Module 6 (benchmark per workload).
4. **Autoscaling 37% worse than tuned fixed clusters** — fix in Module 2 (use fixed for predictable batch).
5. **UC migration breaking dashboards** — fix in Module 10 (HMS Federation as bridge).
6. **Three-permission collision (workspace ACL ↔ UC ↔ workspace binding)** — fix in Module 9 (debug order).
7. **`databricks-connect` version drift** — fix in Module 5 (pin version, coordinate DBR upgrades).
8. **Notebook code review hell** — fix in Module 4 (`.py` format + src/ modules).
9. **Init script deprecation churn** — fix in Module 17 (UC volumes + `_v<n>` versioning).
10. **Library install non-deterministic order** — fix in Module 5 (one wheel, all deps pinned).
</details>

**Q2.** Why is "the Databricks Reddit channel" not a reliable honest pain report source?

<details><summary>Answer</summary>

**Because it's an engineered marketing channel.** Foundation Inc. publicly documented turning r/databricks into "a powerful community engine" ([Foundation case study](https://foundationinc.co/lab/databricks-reddit-strategy)). r/databricks moderation is closer to vendor-managed community than independent practitioner space.

**For honest pain reports:**
- **r/dataengineering** — where Daniel Beach's Standard-Tier critique blew up
- **Hacker News** — top thread on Databricks Serverless captured the "endless progression of unpleasant surprises" sentiment
- **Practitioner Substacks** — Daniel Beach (Confessions of a Data Guy), Benn Stancil (category collapse), Joe Reis (data modeling critique)

**Architect-level teaching point:** vendor critique on public forums can carry account-team consequences (Beach reported being "hunted down at work" after public critique). For an architect/EM at Optum, this is a real consideration when sharing platform feedback publicly — the right channel is your Databricks account team's solutions architect, not LinkedIn.
</details>

---

## Apply

**Q3.** A new architect joining Optum asks "what are the top 3 things I should NOT do on Databricks?" Give them your three.

<details><summary>Answer</summary>

**1. Don't enable Photon globally.**
Photon's 2× DBU multiplier needs ~20% speedup margin to break even. For SQL warehouses and DLT silver/gold, default-on. For Python UDF-heavy ETL, ML training, RDD code, or small-data jobs: Photon is net-negative. Benchmark per workload; encode the decision in cluster policy. (Miles Cole found Photon made one TPC query 72% MORE expensive.)

**2. Don't put scheduled jobs on All-Purpose Compute.**
3.6× cost cut moving them to Jobs Compute, no engineering work. The single highest-ROI lever on the platform. A team running 50 jobs at 20 DBU-hours/night × 250 nights/yr saves ~$100K/yr from this one change.

**3. Don't use scale-to-zero on production Model Serving endpoints.**
Databricks' own docs say not to. Cold start is "10–20 sec usually but can stretch to minutes" with no SLA. For prod chat or RAG agents, set min concurrency > 0; accept ~$1,400/mo idle cost on a Medium A10G to avoid p99 cold-start surprises. Module 14.

**Bonus #4:** Don't trust UC migration timelines that say "weeks." Plan for 6–12 months at Optum scale. HMS Federation makes it incremental; without exec sponsorship of "no new HMS tables after [date]," migration drags indefinitely. Module 10.

**The architect's pitch:** "These three avoid the most common production-cost surprises and the most common HIPAA-relevant operational mistake. Get the policy enforcement and the cost discipline in place from day one; you'll save us six figures a year and prevent a 3am cold-start incident."
</details>

---

## Diagnose

**Q4.** A team is 4 months into a UC migration. They're behind schedule, the on-call team is reporting "broken things" weekly, and engineers are talking about "rolling back to HMS." Walk through the architect-level intervention.

<details><summary>Answer</summary>

**This is a known pattern** — 7-Eleven's DAIS 2025 talk title was literally "Reorienting a Complex UC Migration." Mid-course corrections are normal; the question is how to land the migration without giving up.

**Step 1: Diagnose what's actually broken.**

Pull data from `system.access.audit` and incident tickets:
- **What's the most common breakage?** (dashboards, dbt models, iterative jobs, secrets, group memberships)
- **Is it migration-caused or pre-existing?** Some "UC broke this" reports are actually "UC exposed a pre-existing fragility."
- **Are the same teams reporting the same problems?** Or is it scattered?

**Step 2: Stabilize via HMS Federation.**

If the team did big-bang migration without HMS Federation, that's the architectural error. **Roll back to HMS Federation as the bridge:**
- Federate `hive_metastore` as `legacy_hms_catalog` in UC (Module 10)
- Re-point any code that's broken to read from `legacy_hms_catalog` while UC migration of those tables is fixed
- This **doesn't roll back the migration** — it provides the incremental bridge that should have been there from the start

**Step 3: Triage the broken work.**

Categorize each broken thing:
- **Quick fix (hours)** — wrong path reference, group permission missing
- **Medium (days)** — dbt model rewrite, dashboard repoint
- **Hard (weeks)** — iterative pipeline performance regression requiring code refactor

Triage by business impact, not engineering effort.

**Step 4: Have the forcing-function conversation.**

If the team doesn't have exec sponsorship for "no new HMS tables after [date]," the migration drags. **Get that sponsorship now.** Without it, every team adds new HMS tables faster than you migrate, and the project never ends.

**Step 5: Reset the timeline expectations.**

Communicate to leadership: "We're 4 months in. Our original plan was X months; based on what we've learned, the realistic completion is X months from now, not X-4 months from now." This is the conversation the team is afraid to have but must have.

**Step 6: Document the learnings.**

Write the post-mortem now — what worked, what didn't, what would you do differently. This becomes the runbook for any future workspace's migration.

**The architect's framing:** "Migrations like this are common to fail this way. The fix isn't to give up; it's to reorient. HMS Federation is the architectural tool we should have used from the start. Let's stabilize, retriage, get exec sponsorship for the forcing function, and ship the migration in 6 more months — slower than planned, but successfully."

**The "rolling back to HMS" framing is the wrong impulse.** UC is the right destination; the journey just needs better engineering. Resist the rollback narrative; champion the reorientation.

**Sources:** [DAIS 2025 7-Eleven talk](https://www.databricks.com/dataaisummit/session/story-unity-catalog-uc-migration-using-ucx-7-eleven-reorient-complex-uc), [Karlo Kotarac UC lessons](https://medium.com/valcon-consulting/unity-catalog-migration-best-practices-lessons-learned-from-two-implementations-part-1-f692811643a6).
</details>

---

## Defend

**Q5.** A peer says "the Medallion Architecture (Bronze/Silver/Gold) is the data model — every table goes through three layers." Defend or refute.

<details><summary>Answer</summary>

**Refute, with calibration.** (This was also covered in Module 3's quiz; the production-pain frame here is slightly different.)

Daniel Beach's framing: *"the false gospel of the Medallion Architecture wreaked havoc on a generation of Data Engineers"* ([Confessions of a Data Guy](https://www.confessionsofadataguy.com/the-medallion-architecture-farce/)). His charge: pushing three layers for every dataset increases storage and compute consumption that flows directly to Databricks revenue.

The peer's interpretation — "every table goes through three layers" — is the version that produces the waste:
- **Triples storage** (Bronze + Silver + Gold for each dataset, even trivial lookup tables)
- **Triples compute** (read + transform + write at each layer, even when no transformation adds value)
- **Lets engineers skip real modeling** because "we have layers"

**The honest framing:**
- **Medallion is a *staging pattern*, not a data model.** Bronze (raw landing), Silver (conformed, grain-stable), Gold (analytics-ready). Real data modeling — star vs OBT, surrogate keys, conformed dimensions, SCD types — happens *inside* one of these layers (typically Gold), not by virtue of having layers.
- **For streaming ingestion with quality concerns**, Bronze/Silver/Gold is genuinely useful — Bronze captures the immutable original, Silver enforces schemas and dedupes, Gold serves analytics.
- **For simple lookup tables** (a 100-row vocabulary table), one layer is fine. **Don't force three.**
- **For pre-modeled feeds** (a partner sends you a clean star), Silver may be redundant — land directly to Gold.

**The architect's discipline:** apply medallion as a **guideline**, not a rule. Healthcare organizations that bought into "every dataset goes through three layers" have spent millions on storage and compute layers that produce no analytical value. **The `system.billing.usage` data tells the story** — find the Silver tables that no Gold table reads from, and delete them.

**For Optum-scale healthcare:**
- HL7v2 / X12 / FHIR Bundles → Bronze (raw, immutable, regulator-friendly)
- Silver shred per resource type / claim line / segment
- Gold for HEDIS, member-month, risk-adjustment use cases
- Reference data (ICD-10 vocab, CMS code lists) → one layer; don't force three.

**The pitch to the peer:** "Medallion is staging discipline, not modeling. The 'every table through three layers' rule is what Daniel Beach calls the false gospel. We use it where it adds value (streaming Bronze, regulated raw retention) and skip it where it doesn't (lookup tables, pre-modeled feeds). Module 3 has the practitioner pattern."

**Sources:** [Joe Reis on Medallion not being a data model](https://practicaldatamodeling.substack.com/p/medallion-architecture-is-not-a-data), [Daniel Beach Medallion Farce](https://www.confessionsofadataguy.com/the-medallion-architecture-farce/).
</details>
