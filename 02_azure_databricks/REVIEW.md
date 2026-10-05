# Adversarial Review — Topic 02

> The user's prompt asked: *"Pretend you're a Databricks Solutions Architect with 8 years at the company, reading these modules. What's wrong, oversimplified, outdated, or missing? Where would I push back?"*
>
> This is the self-review pass. Items that surfaced as substantive criticism, with assessment of severity and whether the corpus needs revision.

---

## Substantive criticisms (in priority order)

### 1. Volatile claims marked as facts (HIGH)

**Issue:** Many specific claims about GA/Preview status, Anthropic Claude model versions, FMAPI BAA scope, and DBR support lifecycle are written as if they're stable facts as of May 2026. In reality, several are inferred from training-data cutoff (Jan 2026) plus directional research, and may have shifted.

**Examples in the corpus:**
- "Pay-per-token FMAPI is now BAA-eligible with CSP" — directionally correct as of late 2025, but specific Anthropic model availability (Haiku 4.5, Sonnet 4.6, Opus 4.7) on Databricks may differ from current catalog
- "Lakebase status: still Public Preview as of May 2026" — flagged as uncertain in the research (research file 05); could be GA by now
- "Agent Bricks Beta status as of May 2026" — could have moved to GA
- "DBR 17.3 LTS as the recommended 2026 default" — verifiable but specific support windows shift
- "Mosaic (geospatial) EOL Aug 2026" — verifiable but specific date worth re-checking

**The corpus does flag this** — `FACTS.md` carries "Last verified" dates and Module 1's "Stable vs volatile surfaces" section explicitly distinguishes claim categories. **But individual modules don't always re-flag the volatility** in the prose.

**Mitigation:** every volatile claim in a module should defer to FACTS.md and explicitly say "verify before betting a roadmap on this." The corpus does this inconsistently.

**Severity:** HIGH for a teaching-corpus user who quotes a number in an architecture review without re-verifying.

---

### 2. The Optum-specific framing may be too tight (MEDIUM)

**Issue:** The corpus is written for "Vatsal at Optum, healthcare, Azure shop." Most modules pivot the discussion through that lens. **A reader switching contexts (e.g., to a financial-services architect role) would find sections that don't translate cleanly.**

**Examples:**
- The HIPAA-heavy framing in Modules 4, 21, 22 doesn't apply outside healthcare
- "Optum is Azure-heavy" assumption shapes Module 25's cert recommendation — may not apply to AWS or GCP shops
- The two-workspace PHI/analytics split (Module 9, 22) is healthcare-specific; financial services has different segregation patterns (PCI scope, GLBA, etc.)

**The corpus addresses this** — README scope notes say "Bias: Azure Databricks (Optum is an Azure shop). AWS-specific differences are flagged where they matter." But individual modules don't always re-state the bias.

**Mitigation:** explicit "for non-healthcare readers" callouts where the healthcare framing dominates. Especially Modules 21, 22.

**Severity:** MEDIUM. A senior architect reader can mentally substitute "PCI" for "HIPAA"; a junior architect may not.

---

### 3. Missing module on streaming + real-time architecture (MEDIUM)

**Issue:** The corpus covers Auto Loader (Module 5, 8), Structured Streaming watermarks (Modules 5, 6), and stream-static / stream-stream joins (Module 6) — but **doesn't have a single module that pulls together the real-time architecture story** (event hub → streaming silver → real-time aggregations → online feature stores → model serving for sub-second decisions).

**Why it matters for healthcare:**
- Real-time fraud / clinical alerting workloads exist
- Lakebase (online feature store) and Streaming Tables don't get integrated treatment
- Real-time RAG / agent serving has latency considerations the corpus discusses piecemeal

**The corpus covers the pieces** in Modules 4, 5, 6, 8, 13, 14 but doesn't integrate them.

**Mitigation:** a Module 26 ("Real-time architecture and streaming") could pull these together. Or augment Module 8 (Ingestion) with a "real-time architectures" section.

**Severity:** MEDIUM. The pieces are present; integration is missing.

---

### 4. The "what about Snowflake/Fabric" treatment is vendor-comparison heavy and could over-rotate (MEDIUM)

**Issue:** The corpus repeatedly compares Databricks to Snowflake (Modules 1, 7, 16, 18) and Fabric (Modules 1, 16, 18). The comparisons are honest but may be heavier than the use case warrants. **A practitioner reading 25 modules expecting Databricks-on-Databricks content gets a fair amount of competitive positioning.**

**Where it lands:**
- Module 1 — "lakehouse vision and competitive positioning" — fair
- Module 7 — "Snowflake-vs-Databricks SQL benchmark" — fair but extensive
- Module 16 — "honest comparison" section — fair given budget-ownership ask
- Module 18 — "teams who left" — fair given the production-pain frame

**This is partly the prompt's fault** — the user explicitly asked for "Where do teams hit a wall and consider leaving Databricks for Snowflake / BigQuery / pure-Spark / etc., and why?" So vendor comparison was a deliberate ask.

**Mitigation:** none needed if the user reads it as intended. **A Solutions Architect at Databricks would push back** on the volume of comparison; a healthcare CFO or AI architect at Optum may appreciate it.

**Severity:** MEDIUM. Self-aware tradeoff.

---

### 5. The "production pain" framing may discourage adoption (MEDIUM)

**Issue:** Module 18 enumerates 25 production pain points; Modules 5, 11, 17, 21 also flag specific gotchas. **A reader without production Databricks experience could come away thinking "Databricks is broken."**

**The corpus's saving grace:** Modules 1, 6, 9, 12, 14, 15, 16, 22 all have "where Databricks is genuinely strong" sections that balance the criticisms.

**A Solutions Architect at Databricks would push back hard** on Module 18's framing — characterizing the platform as a "minefield of production pain" doesn't match their experience that most customers are productive after the first 6-12 months of platform engineering.

**Counterargument that's already in the corpus:** every pain point has a workaround or mitigation. The corpus isn't saying "don't use Databricks"; it's saying "know the operational discipline required." That framing is defensible.

**Mitigation:** Module 18 could open with a stronger "this is the minefield map; Modules 16-17 cover the discipline that lets you walk through it without stepping on mines" framing. Currently the framing is implicit.

**Severity:** MEDIUM. Reader-state-dependent.

---

### 6. The Lakeflow rebrand coverage is correct but incomplete (LOW)

**Issue:** Modules 4, 8 cover the DLT → Lakeflow Spark Declarative Pipelines rebrand. Module 4 has the migration mapping (`@dlt.table` → `@dp.table`). **What's missing:** a clear "if I'm reading Databricks docs that say 'DLT', here's what's still relevant vs what's renamed" mapping.

**The taxonomy churn is real:**
- "DLT" still appears in event log schemas, billing SKUs, some doc paths
- "Lakeflow Declarative Pipelines" in newer docs
- "Spark Declarative Pipelines" in OSS Apache Spark 4.1 context

**Mitigation:** a Module 4 sub-section ("Reading older docs: a translation guide") could help. Currently it's implicit.

**Severity:** LOW. Practitioners working through the docs will figure it out.

---

### 7. The audit log pipeline (Module 17, 21) glosses over the SIEM tokenization detail (MEDIUM)

**Issue:** The corpus correctly identifies that `request_params` can contain PHI and that audit logs are themselves PHI. It mentions "tokenizing forwarder" or "separate locked-down SIEM index" as options — but **doesn't show a concrete example or recommend a specific approach.**

**Why it matters:** the choice of tokenizer (Splunk Stream + REGEX, Splunk SmartStore with field anonymization, Sentinel logic apps with Logic-App-based redaction, etc.) is an architecture decision with real implications. The corpus punts.

**Mitigation:** Module 17's audit pipeline section could include 2-3 concrete tokenizer architecture options with tradeoffs. Currently it's a one-paragraph mention.

**Severity:** MEDIUM. Architects implementing this will need to figure it out anyway, but the corpus could give them a head start.

---

### 8. The cert decision framework (Module 25) doesn't address PMP fully (LOW)

**Issue:** Module 25 mentions PMP in passing but doesn't really decide it. The user-profile memory flags "persuasion/PM/budget" as the gap; PMP is the obvious candidate cert. **The module hedges instead of recommending.**

**Why it hedges:** the architect-vs-EM choice is itself open in the user's profile. The module is right to not over-decide.

**Mitigation:** Module 25 could have a more explicit "if EM-track, here's the PMP recommendation; if architect-track, skip PMP" decision tree. Currently it presents both as open.

**Severity:** LOW. Self-aware hedge given user-profile uncertainty.

---

### 9. No module on the developer experience workflow end-to-end (LOW)

**Issue:** The corpus has Module 4 (notebooks/jobs/Lakeflow), Module 5 (Spark practitioner), Module 19 (CI/CD), Module 17 (admin). **Missing:** a "day in the life of a Databricks developer" module that ties the workflow together end-to-end.

**Why it might help:** a junior architect reading the 25 modules has all the pieces but may not know how they compose into a working developer workflow. (`databricks-connect` setup → write code → unit test → bundle deploy to dev → integration test → PR → CI deploys to stage → manual approval → prod.)

**Counterargument:** the workflow is implicit across Modules 4-5-19, and a senior architect reader can compose it themselves. **Adding a 26th module risks bloat.**

**Mitigation:** maybe a workflow diagram in the README. Currently the README is module-list-shaped, not workflow-shaped.

**Severity:** LOW. A nice-to-have, not a gap.

---

### 10. Module 6 (Performance) is dense and could benefit from worked examples (LOW)

**Issue:** Module 6 covers join strategies, AQE, skew, caching, file layout, Photon-aware code, configs, window functions, streaming — all in one ~1200-line module. **It's the densest module in the corpus.**

**A Solutions Architect at Databricks would say:** "This is a great cookbook, but it's overwhelming for a first read. Could use 2-3 worked examples (e.g., 'here's a slow merge — walk through the diagnosis and fix') to anchor the patterns."

**Counterargument:** Module 5's "diagnostic loop" provides one such walkthrough. The quizzes in Modules 5, 6 also include worked diagnostic problems.

**Mitigation:** consider splitting Module 6 into 6A (joins/skew/AQE) and 6B (caching/file layout/Photon). Currently it's one module.

**Severity:** LOW. Aesthetic; the content is correct.

---

## Items that DON'T need revision

These came up during review but I judged they're already handled correctly:

- **The healthcare bias** is the user's explicit ask; the corpus correctly serves it
- **The "exit door discipline"** (Modules 1, 11, 18, 24) is repeated across modules; that's intentional anchoring, not redundancy
- **The cost framing in Modules 16 + 18** is heavier than the average corpus would have, but the user's "budget ownership gap" memory makes it appropriate
- **The MLflow 3 vs LangSmith comparison in Module 12** is fair to both sides; not partisan
- **The Solutions-Architect-pushback voice in the quizzes** is a deliberate teaching device

---

## Items the corpus could ADD in a v2

(Not for this version; flagged for future iterations)

1. **Real production architecture diagram** for Optum-grade healthcare, with all components labeled (Module 22 has a sketch but could be more comprehensive)
2. **Cost projection spreadsheet** — given a workload shape, here's the monthly DBU + Azure VM + storage projection (Module 16 covers the inputs; doesn't hand the user the spreadsheet)
3. **Interview prep guide** — given Modules 1-25, here are the 30 questions an AI Architect interview will ask, mapped to module references
4. **Comparative reference architectures** — Optum vs Snowflake-shop vs Fabric-shop. The Modules show one path well; alternatives are implied.
5. **More healthcare-specific code examples** — the code/ folder leans generic; specific X12 parser, FHIR shred, or HEDIS measure patterns would help

---

## Net assessment

**The corpus is comprehensive, opinionated, and matches Topic 01's depth.** The pain-points framing is honest; the healthcare bias is appropriate to the user; the cert framework gives a defensible recommendation. The 25 modules + 25 quizzes + 20 code artifacts cover the architect-track ground at the right altitude.

**The most important architect-level revision** would be tightening the volatile-claims discipline (Item 1) and making the audit-log tokenization more concrete (Item 7). Both are addressable with module-level edits, not structural changes.

**A Databricks Solutions Architect with 8 years at the company would mostly nod along**, push back on Item 4 (vendor comparison volume) and Item 5 (production pain framing tone), and grudgingly acknowledge that everything else is at least defensible.

**I judge the corpus ready for the user.** They asked for the version that prepares them for an architect-track interview at a regulated healthcare org; they got it. The volatile claims are cited and dated; the FACTS.md is the single source of truth for "is this still current"; the modules give them the mental model and the operational discipline to be credible in the actual conversation.

---

## Self-review meta-note

This review is honest but limited. A real second-pair-of-eyes review by a senior practitioner would surface things this self-review can't: lived-experience nuances, war stories from specific incidents, the "hmm, that's not quite how it works in production" feedback that comes from operating Databricks at scale.

**Recommendation:** when the user has time, pair the corpus with at least one external review:
- A Databricks Solutions Architect (vendor-side; biased toward "platform is great" but knows the internal product roadmap)
- A practitioner Substack author (e.g., Daniel Beach) — paid review or community feedback
- A healthcare AI architect at a peer org (Humana, CVS, Anthem) for the regulated-industry lens

The corpus is a starting point that gets the user 80% of the way; the last 20% benefits from external validation.
