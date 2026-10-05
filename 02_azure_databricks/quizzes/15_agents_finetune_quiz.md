# Quiz — Module 15: Agent Framework, Agent Bricks, AI Functions, Fine-tuning

## Recall

**Q1.** What is the role of Mosaic AI Agent Framework — is it a LangGraph competitor?

<details><summary>Answer</summary>

**No, it's deliberately NOT a LangGraph competitor.** It's the **deployment + governance layer beneath** LangGraph / LangChain / LlamaIndex / vanilla Python.

You author the agent orchestration in LangGraph (best state management); the framework gives you:
- **UC tools** — Python functions registered as UC objects, callable as agent tools with RBAC + lineage
- **Lakeguard execution** — tools run remotely under user identity, not service principal
- **MCP server bridging** — expose UC functions as MCP servers; consume external MCP servers
- **MLflow tracing** automatic
- **AI Gateway** in front

**Architect take:** use Agent Framework when you need governed enterprise tools (UC functions over PHI). Skip the framework for low-latency consumer-facing agents (the extra endpoint hop adds 50–200ms latency).
</details>

**Q2.** What does `ai_query` give you that hand-rolled Spark UDFs + AOAI wouldn't?

<details><summary>Answer</summary>

`ai_query` (and the family — `ai_classify`, `ai_extract`, `ai_summarize`, `ai_translate`, `ai_similarity`, `ai_mask`, `vector_search`) gives you:

1. **Auto-scaling serving fleet under the hood** — serverless batch inference scales to handle 100M-row workloads.
2. **Cost attribution in `system.billing.usage`** under MODEL_SERVING / BATCH_INFERENCE — per-warehouse, per-user.
3. **AI Gateway integration** — PII redaction, rate limiting, audit (if configured at endpoint level).
4. **No concurrency / retry / error handling code** to write — the SQL function handles it.
5. **3× faster than naive Spark UDF + AOAI** per Databricks benchmarks.
6. **Inline JSON schema** for `ai_extract` — get structured output without prompt engineering ceremony.

**The architect's case:** for batch-scale enrichment of healthcare data (de-identification, ICD-10 extraction, claim summarization, classification), this is the single most underrated productivity unlock in Mosaic AI. Building the equivalent yourself takes a sprint and produces a less reliable result.
</details>

---

## Apply

**Q3.** Use AI Functions to do bulk ICD-10 extraction from clinical notes, with structured output schema and PII redaction.

<details><summary>Answer</summary>

```sql
-- Configure the endpoint with PII redaction in AI Gateway (one-time)
-- (See Module 14 for the gateway config code)

-- Run bulk ICD-10 extraction
INSERT INTO silver.clinical_codes_extracted
SELECT 
  note_id,
  encounter_id,
  member_id,
  ai_extract(
    endpoint => 'clinical-extract-haiku',  -- pre-configured endpoint with gateway
    text     => note_text,
    schema   => 'STRUCT<
                   icd10_codes: ARRAY<STRUCT<code: STRING, description: STRING>>,
                   cpt_codes:   ARRAY<STRUCT<code: STRING, description: STRING>>,
                   diagnoses:   ARRAY<STRING>,
                   medications: ARRAY<STRUCT<name: STRING, dosage: STRING>>
                 >'
  ) AS extracted,
  current_timestamp() AS extraction_ts
FROM silver.clinical_notes
WHERE encounter_date >= '2025-01-01'
  AND extraction_ts IS NULL;  -- only un-extracted

-- Audit: confirm the extraction ran with gateway redaction
SELECT 
  count(*),
  max(event_time)
FROM system.access.audit
WHERE service_name = 'serving'
  AND request_params:endpoint_name = 'clinical-extract-haiku'
  AND date(event_time) = current_date();
```

**Discipline:**
- **Endpoint pre-configured with AI Gateway PII redaction** — the prompt may inadvertently contain SSN/MRN; redact before transit.
- **Structured output schema** — `ai_extract` enforces it; no parsing JSON-from-string at the consumer.
- **Idempotent re-run** — `WHERE extraction_ts IS NULL` makes this safely re-runnable.
- **HIPAA discipline:** the endpoint must be on FMAPI pay-per-token with CSP=HIPAA workspace, OR provisioned throughput. Don't route PHI prompts through external models without verified BAA chain.
- **Cost monitoring:** check `system.billing.usage` under MODEL_SERVING SKU for the endpoint; tag with cost_center for chargeback.
</details>

---

## Diagnose

**Q4.** A team runs Agent Bricks on a clinical extraction task. The auto-generated agent gets 78% accuracy on AstraZeneca's published "60-min" benchmark replicate. They want to deploy it to production for clinical reviewer workflows. Walk through your architect-level review.

<details><summary>Answer</summary>

**My architect-level review would push back, hard, on the "deploy to production for clinical reviewers."**

**The structural objections:**

1. **Agent Bricks is Beta.** As of May 2026, Beta status means **out of BAA scope by default** for healthcare workloads. Even if the security team is willing to grant exception, the audit trail position is weaker than a fully-supported feature.

2. **78% accuracy is not "ready for clinical reviewers."** For a clinical decision-supporting workflow, the cost of false negatives (missed diagnoses) and false positives (incorrect codes) is real. 78% means 22% wrong; what's the cost of each error category?

3. **The 60-minute optimization claim is a single optimized path.** Real-world workloads need iteration on schema, edge cases, judge calibration. Treat the benchmark as "we got to 78% in an hour" not "we have a production-ready agent."

4. **No human-in-the-loop discipline.** Clinical reviewer workflows shouldn't replace the reviewer; they should *assist* the reviewer. The Agent Bricks output should be a *first-pass suggestion* with provenance, not an authoritative classification.

**The architect's path forward:**

1. **Use Agent Bricks for the PoC.** It demonstrates value quickly — useful for exec stakeholder buy-in.

2. **Migrate to Agent Framework + LangGraph for production.** Same data and prompts, but:
   - Production-grade BAA scope
   - Custom orchestration (branching, retries, human-in-the-loop checkpoints)
   - Per-step MLflow tracing for audit
   - Provisioned throughput on a HIPAA-eligible model
   - AI Gateway with rate limiting + PII redaction

3. **Define accuracy gates that match clinical risk.** For coding suggestions, 78% may be acceptable as suggestions with reviewer override; for any auto-decision, require >95% with confidence intervals.

4. **Implement explainability.** Agent Bricks gives you optimized output but limited explainability. Production needs "why did the agent suggest this code" with citations to source text.

5. **Document the limitation.** Even after migration, document that this is a clinical *suggestion* tool, not a clinical *decision* tool. Train reviewers; track override rates; iterate.

**The pitch to the team:** "Agent Bricks got us to a working prototype in an hour. That's genuinely useful. Now we treat that prototype as the *spec*, and rebuild it on Agent Framework + LangGraph for production with the governance, BAA scope, and human-in-the-loop discipline this workflow requires."

**Source:** [Agent Bricks press](https://www.databricks.com/company/newsroom/press-releases/databricks-launches-agent-bricks-new-approach-building-ai-agents).
</details>

---

## Defend

**Q5.** A peer says "we should pretrain a clinical Llama variant on Optum's claims data — it'll be a competitive moat." Defend or refute.

<details><summary>Answer</summary>

**Refute, decisively.**

Where the peer is right (limited):
- **Domain-tuned models** can outperform general models on domain-specific tasks.
- **Owning the model weights** has strategic value for some narratives.

Where the peer is wrong:
- **Full pretraining of a 70B+ model from scratch is economically unjustifiable** in 2026. Mosaic's reference customers for full pretraining are Databricks itself (DBRX), AI2 (OLMo), Krutrim, and a handful of model vendors. **Almost no enterprise pretrains.** The cost (millions of dollars in compute), the talent (PhDs in ML systems), and the time (months) don't pencil out vs starting from a Llama 3.3 base.

- **The competitive-moat argument doesn't hold.** Llama 3.3, Claude, GPT-4o are improving faster than your pretraining cycle. By the time you've pretrained a clinical model, base models will be better than yours on the same task — without the Optum tuning cost.

- **What actually works: Continued Pretraining (CPT) + IFT.** Take a Llama 3.3 70B base. Run CPT on a clinical-language corpus (de-identified claims, public clinical text, drug ontologies) for a week. Then IFT on Optum-specific tasks (claim summarization, ICD-10 coding, prior-auth review). You get domain adaptation at a fraction of the cost.

- **Mosaic AI Model Training supports CPT** specifically for this. The LoRA path makes it cheap.

**The architect's pitch to the peer:**
- "Full pretraining is the wrong altitude for our budget and team. We don't have ML systems PhDs; we have data engineers."
- "**Continued pretraining of Llama 3.3 + IFT on our task suite** delivers ~80% of the benefit at <5% of the cost."
- "Track the base-model leaderboards. When Llama 4 (or whatever) ships at significantly higher quality, we re-CPT against the new base. We don't have to be in the model-training arms race."
- "The competitive moat is **the data + the eval set + the deployment governance**, not the weights. Anyone can fine-tune from Llama; not everyone has Optum-grade de-identified claims data, clinical-reviewer feedback labels, and HIPAA-deployment infrastructure."

**The cost call-out for the CFO:** full pretraining a 70B model for 6 months on H100 cluster ≈ $5M+ raw compute, plus team. CPT + IFT on a Llama base ≈ $50K. The math doesn't justify the moat narrative.

**Sources:** [DBRX retirement from FMAPI](https://docs.databricks.com/aws/en/release-notes/product/2025/april), [Mosaic AI Model Training](https://www.databricks.com/product/machine-learning/mosaic-ai-training), [LLM fine-tuning blog](https://www.databricks.com/blog/llm-fine-tuning).
</details>
