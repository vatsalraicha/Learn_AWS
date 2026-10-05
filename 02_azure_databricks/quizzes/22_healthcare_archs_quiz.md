# Quiz — Module 22: Healthcare Reference Architectures

## Recall

**Q1.** What is the two-workspace PHI/analytics split, and why is it the load-bearing design choice?

<details><summary>Answer</summary>

**The split:**
- **PHI workspace** — CSP=HIPAA, all the network controls, bound to `phi_raw_*` catalogs only. PHI engineers + claims-ETL pipelines work here.
- **Analytics workspace** — bound to `member_deid_*` catalogs. ML training, BI, RAG, Genie, broader user access.

**Why it's load-bearing:**

It leverages **workspace-catalog binding** as the hard isolation primitive. Even if a user has account-level SELECT grants on PHI catalogs, **they cannot read from a non-bound workspace.** This is the difference between "we trust ABAC + grants" and "we have a hard isolation boundary that survives a single misconfigured policy."

Concretely: if an analyst is given the wrong group membership and ends up with SELECT on a PHI catalog, **they still can't query it from the analytics workspace** — workspace-catalog binding vetoes it. ABAC, row filters, column masks are all defense-in-depth on top.

For HIPAA audit, this is the structural answer to "how do you guarantee PHI doesn't leak to the analytics path?"
</details>

**Q2.** What's the FHIR de-identification path, and what does Microsoft explicitly NOT guarantee?

<details><summary>Answer</summary>

**The path:**
1. Source EHRs → AHDS FHIR service (PHI authoritative store, BAA-covered PaaS)
2. `$export` operation with `_anonymizationConfig=anonymizationConfig.json`
3. Uses **FHIR-Tools-for-Anonymization** engine, **HIPAA Safe Harbor sample config** as starting point
4. De-identified data lands in ADLS deid container (CMK + PE)
5. Auto Loader → Databricks Bronze → Silver shred per resourceType → Gold analytics

**What Microsoft explicitly NOT guarantees:**

> *"Microsoft is unable to evaluate de-identified export outputs or determine the acceptability for your use cases and compliance needs. The FHIR service's de-identified export is not guaranteed to meet any specific legal, regulatory, or compliance requirements."*

**Architect implication:** the Safe Harbor sample config is a **starting point**, not a finished compliance artifact. Your privacy office must:
- Review the `fhirPathRules` for completeness against your specific data shape
- Sign off on the final config
- Re-validate periodically as data evolves
- Run sample outputs through a privacy review

**Note:** Azure API for FHIR is being **retired Sept 30, 2026**; no new deployments since Apr 1, 2025. **Path forward = Azure Health Data Services FHIR service.** Organizations still on the legacy API need a migration plan.
</details>

**Q3.** What's the canonical Silver-layout choice for X12 claims, and when would you pick each?

<details><summary>Answer</summary>

**Two reasonable Silver layouts:**

1. **Wide-segment** — one Silver table per logical entity:
   - `claim_header` (one row per claim)
   - `claim_line` (one row per claim line, with claim_id FK)
   - `service_line_adjustment` (one row per adjustment, with claim_line FK)
   - `provider_info`, `member_info`, etc.
   
   **Best for analytics.** Joins are clean; clustering keys make sense. Requires a good X12 parser.
   
   **Cluster `claim_header` by `(payer_id, received_date)`; `claim_line` by `(member_id, service_date)`.**

2. **EAV-by-segment** — one row per segment, columns `(claim_id, loop_id, segment_id, element_position, value)`. 
   
   **Good for full-fidelity audit** — preserves every X12 segment with original positions. **Bad for analytics** — every query is essentially a self-join across segment positions.
   
   Use sparingly; when full-fidelity audit is the requirement and analytics needs are modest.

**X12 parser choice:**
- **`pyx12`** — OSS Python; decent quality; sufficient for most workloads at moderate scale
- **Edifecs** — commercial, mature, used heavily in payor ETL; pay-to-play but reliable
- **Custom Spark UDF** — when you need specific behavior or have unusual transaction sets; expensive engineering investment

**Production discipline:** Bronze keeps raw X12 text immutable (regulator-friendly). Silver is the wide-segment shred. Gold rolls up to member-month, claim-summary, denial-analysis grain.
</details>

---

## Apply

**Q4.** Sketch the architecture for an HCC risk-adjustment pipeline that uses clinical NLP on provider notes.

<details><summary>Answer</summary>

```
┌────────────────────────────────────────────────────────────────────┐
│ Source: Provider notes (PDFs, Word docs, EHR text exports)         │
│ HIPAA-eligible workspace: ws-phi-east-001                          │
└────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│ UC Volume: /Volumes/clinical/raw/notes/                            │
│ Managed volume; CMK; lineage-traced                                │
└────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│ Auto Loader streaming ingest                                       │
│   - File notification mode (Event Grid + Storage Queue)            │
│   - cloudFiles.maxFilesPerTrigger = 1000                           │
└────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│ Bronze: clinical.bronze.notes_raw                                  │
│   - One row per note: note_id, member_id, encounter_id,            │
│     source_doc_path, raw_text, ingestion_ts                        │
│   - Append-only, immutable, regulator-friendly                     │
└────────────────────────────────────────────────────────────────────┘
                              │
                              ▼ Lakeflow Declarative Pipeline
┌────────────────────────────────────────────────────────────────────┐
│ Silver: clinical.silver.note_chunks                                │
│   - Sentence-boundary chunking (~512 tokens)                       │
│   - Preserves member_id, encounter_id, source_doc, chunk_position  │
│   - Cluster by (member_id, encounter_id)                           │
└────────────────────────────────────────────────────────────────────┘
                              │
                              ▼ ai_query batch inference (HIPAA-eligible)
┌────────────────────────────────────────────────────────────────────┐
│ Clinical NLP via John Snow Labs Model Serving endpoint             │
│   - Provisioned throughput (NOT pay-per-token for production)      │
│   - PHI-aware; in CSP=HIPAA workspace, BAA-eligible                │
│   - AI Gateway with PII redaction defense-in-depth                 │
│   - Inference table captures every request/response                │
└────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│ Silver: clinical.silver.hcc_candidates                             │
│   - chunk_id, candidate_icd10, candidate_hcc, confidence_score,    │
│     model_version, run_ts                                          │
│   - Cluster by (member_id, run_ts)                                 │
└────────────────────────────────────────────────────────────────────┘
                              │
                              ▼ Human-in-the-loop review
┌────────────────────────────────────────────────────────────────────┐
│ Databricks App: HCC Reviewer Workflow                              │
│   - Reviewer queue ordered by confidence (review borderline first) │
│   - Review accepts/rejects/modifies candidate codes                │
│   - Logs every decision to Silver: hcc_review_decisions             │
└────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│ Gold: clinical.gold.member_hcc_codes_validated                     │
│   - One row per validated (member, hcc_code, year)                 │
│   - Drives risk-score calculation downstream                       │
└────────────────────────────────────────────────────────────────────┘
```

**Critical decisions:**
- **Provisioned Throughput, not Pay-Per-Token** — for predictable production latency and cost
- **AI Gateway PII redaction** — defense in depth, even though prompts are PHI-cleared
- **Inference tables tagged `phi_class=high`** — they contain PHI; ABAC-protect
- **Human-in-the-loop** — clinical decision support, NOT auto-decision. Reviewer accepts/rejects every candidate.
- **All compute in PHI workspace** — workspace-catalog binding to `clinical.*` (PHI catalogs)
- **MLflow trace** every inference for audit
- **Schedule**: Lakeflow pipeline triggers on new notes; daily batch for the inference run; near-real-time review queue

**Cost projection:**
- Provisioned throughput endpoint: ~$1,400/mo for Medium A10G held warm (Module 14)
- ai_query batch: scales with volume; system.billing.usage attributes to MODEL_SERVING SKU
- Database App: minimal (Apps GA pricing)

**The architect's pitch:** "This pattern combines RAG-style retrieval (chunked notes), specialized clinical NLP (John Snow Labs model), human-in-the-loop validation, and full audit lineage. The risk-adjustment use case requires the human reviewer; the model is suggesting, not deciding. HIPAA-clean throughout."
</details>

---

## Defend

**Q5.** A peer says "we should put Genie on the de-identified Member 360 Gold table — it's de-identified, so HIPAA isn't a concern." Defend or refute.

<details><summary>Answer</summary>

**Calibrate — closer to right than wrong, but with caveats.**

Where the peer is right:
- **Genie on de-identified data is the recommended pattern** (Module 21). The CSP-default disabling of AI features applies to PHI catalogs; on de-identified catalogs in the analytics workspace, Genie is fine.
- **Member 360 in Gold is a strong Genie use case** — well-modeled, dimensional, exactly the shape Genie's metric-views + verified-answers pattern needs.

Where the peer's framing needs calibration:

1. **"De-identified" is a state of confidence, not a binary.** HIPAA Safe Harbor de-identification is a specific protocol; whatever pipeline you used (FHIR-Tools-for-Anonymization, custom UDF, Privacera tokenization) has assumptions and edge cases. **Document what the de-identification standard is** for the Gold table; have it reviewed by privacy office.

2. **Re-identification risk via aggregation.** A "de-identified" dataset can be re-identified if combined with external data. Genie users asking joint queries across datasets can sometimes re-identify members. The protection: **make sure the de-identification meets Expert Determination if the data has any quasi-identifiers** (zip code + DOB + gender, etc.).

3. **Genie space history persists.** Even on de-identified catalogs, the natural-language questions are persisted. If a user asks "show me member 1234's claims history" and the de-id pipeline uses synthetic IDs, the question contains the synthetic ID — not PHI, but still useful context for an attacker who has compromised audit logs.

4. **Verify the BAA scope.** The HIPAA-allowed preview features list (Module 21) covers some Genie features; verify the specific Genie features you'll use are on the allowlist.

5. **Treat Genie like a SQL surface, not a "read whatever I want" surface.** UC row filters and column masks DO apply to the SQL Genie generates. **Build verified-answer SQL functions for the high-frequency questions; let Genie pattern-match to those.**

**The architect's pitch:**
- "Yes, Genie on the de-identified Gold catalog is fine."
- "But we don't get to skip the discipline because it's de-identified. We document the de-id standard, verify it meets Expert Determination if it has quasi-identifiers, build verified-answer SQL functions for the common questions, and audit Genie space usage."
- "The 'de-identified, no concern' framing is the trap — re-identification via aggregation is real. Treat de-id as a layer of protection, not a license."

**Production discipline:**
- Genie space tagged `phi_class=none` in UC for clarity
- Verified answers for the top-50 common questions
- Quarterly review of Genie usage logs for unusual access patterns
- Privacy office sign-off on the de-identification standard

**Sources:** [Genie Spaces docs](https://learn.microsoft.com/en-us/azure/databricks/genie/), [HIPAA Safe Harbor & Expert Determination](https://www.hhs.gov/hipaa/for-professionals/privacy/special-topics/de-identification/index.html).
</details>
