# Quiz — Module 14: FMAPI + Model Serving + AI Gateway

## Recall

**Q1.** What are the four Model Serving endpoint types?

<details><summary>Answer</summary>

1. **Foundation Model APIs (FMAPI), pay-per-token** — Databricks-hosted Llama 3.3 70B, Llama 4 Maverick, GTE-large, BGE-large embeddings. Pre-provisioned; pay per token.
2. **Foundation Model APIs, provisioned throughput** — same models, you reserve throughput in tokens/sec. HIPAA-compliant in GA.
3. **External models** — AOAI, Anthropic on Bedrock, Anthropic native via Databricks Anthropic Messages API (Claude Haiku 4.5 / Sonnet 4.6 / Opus 4.7 with 1M context). Routed via AI Gateway.
4. **Custom models** — your own fine-tune, your own HF model, MLflow PyFunc. Deploy to CPU or GPU endpoints.
</details>

**Q2.** What is the FMAPI HIPAA breakthrough, and what's the practical implication?

<details><summary>Answer</summary>

**Pay-per-token FMAPI is now BAA-eligible** with Compliance Security Profile (CSP) workspace in a HIPAA-supported region. **For years, FMAPI was non-HIPAA**, forcing healthcare orgs to use only Azure OpenAI Service or self-hosted models for any LLM touching PHI.

**Practical implication:** **Llama 3.3 70B at pay-per-token under HIPAA is the most underrated 2025 unlock for healthcare.** For ~80% of enterprise RAG / extraction / classification workloads it's "good enough" and avoids the AOAI quota dance. Reserve provisioned throughput for the latency-critical chat-completion path.

**Caveat:** Anthropic Claude via Databricks needs careful BAA review — being a third-party external model, you must validate that Anthropic's BAA + Databricks' BAA + Azure's BAA all stack. Many healthcare orgs prefer Claude via Bedrock for documented BAA chain.
</details>

---

## Apply

**Q3.** Configure a HIPAA-compliant pay-per-token FMAPI endpoint for clinical RAG with PII redaction at the gateway, per-user rate limits, and inference logging.

<details><summary>Answer</summary>

```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# 1. Create the FMAPI endpoint (pay-per-token)
w.serving_endpoints.create(
    name="clinical-rag-llama-3-3",
    config={
        "served_models": [{
            "name": "llama-3-3-70b",
            "model_name": "system.ai.llama-3-3-70b-instruct",
            "model_version": "1",
            "scale_to_zero_enabled": False,        # production = no scale-to-zero
            "workload_size": "Small",              # min concurrency
            "min_provisioned_throughput": 0,
            "max_provisioned_throughput": 0,       # pay-per-token, not PT
        }],
        "auto_capture_config": {
            "catalog_name": "prod_phi_clinical",
            "schema_name": "ai_observability",
            "enabled": True,
            "table_name_prefix": "clinical_rag"
        }
    }
)

# 2. Configure AI Gateway features on the endpoint
w.serving_endpoints.put_ai_gateway(
    name="clinical-rag-llama-3-3",
    rate_limits=[
        {"calls": 100, "renewal_period": "minute", "key": "user"},
        {"calls": 10000, "renewal_period": "hour", "key": "endpoint"}
    ],
    guardrails={
        "input": {
            "pii": {"behavior": "MASK"},
            "valid_topics": ["clinical_review", "claim_summary"],
            "invalid_keywords": ["ignore previous instructions", "system prompt"]
        },
        "output": {
            "pii": {"behavior": "MASK"}
        }
    },
    inference_table_config={
        "enabled": True,
        "catalog_name": "prod_phi_clinical",
        "schema_name": "ai_observability",
        "table_name_prefix": "clinical_rag_inference"
    },
    usage_tracking_config={"enabled": True}
)

# 3. Tag the inference table for ABAC governance
spark.sql("""
ALTER TABLE prod_phi_clinical.ai_observability.clinical_rag_inference_payload
  SET TBLPROPERTIES ('phi_class' = 'high', 'data_classification' = 'phi')
""")
```

**Discipline notes:**
- **CSP=HIPAA workspace** is a prerequisite (Module 21).
- **`scale_to_zero_enabled = False`** in production (Databricks' own docs).
- **PII gateway redaction** — defense in depth even if a prompt accidentally contains an SSN.
- **Inference table** captures every request/response — audit-friendly, but **the table contains PHI**, so tag and ABAC-protect.
- **Rate limits per user + per endpoint** — prevents agent loops or runaway batch jobs from consuming budget.
</details>

---

## Diagnose

**Q4.** A team's Model Serving endpoint has scale-to-zero enabled in production. Users complain that the first chat each morning takes 45 seconds. Walk through the diagnosis and fix.

<details><summary>Answer</summary>

**Diagnosis is essentially the symptom — scale-to-zero is the problem.**

Databricks' own docs explicitly say **don't use scale-to-zero for production with consistent uptime needs**. Cold starts are documented at **10–20 sec "usually" but can stretch to minutes**; for GPU endpoints, "extra high latency for first request." The 45-second p99 the team is seeing is consistent with this.

**Fix in priority order:**

1. **Disable scale-to-zero**: set `scale_to_zero_enabled = False` and `min_provisioned_throughput` (or `workload_size`) to a non-zero value. Accept ~$1,400/mo idle cost for an A10G endpoint to avoid the cold-start surprise.

2. **Audit which other endpoints have scale-to-zero in prod** — almost certainly a misconfigured Asset Bundle template that propagated to other deployments. Fix the template; redeploy.

3. **Document the policy**: scale-to-zero is for dev/staging only. Add a CI check that fails the bundle deployment if `scale_to_zero_enabled = true` and the target is `prod`.

4. **Cost budget conversation** with finance: warm GPU endpoints are not free. The pattern "we'll save money with scale-to-zero" doesn't hold for production; document the warm-cost line item upfront.

5. **For low-traffic prod endpoints** where idle warmth is genuinely wasteful: consider routing through pay-per-token FMAPI instead, which doesn't have idle cost (Databricks bears it). Architect tradeoff: lose latency control + custom-model support; gain no idle cost.

**The systemic point:** scale-to-zero in production is a recurring anti-pattern. Module 17 (admin playbook) should include a CI check for this; Module 16 (cost & FinOps) should include the idle-cost line item in any GenAI cost projection.

**Source:** [Production optimization for Model Serving](https://docs.databricks.com/aws/en/machine-learning/model-serving/production-optimization).
</details>

---

## Defend

**Q5.** A peer says "we should use Azure OpenAI for everything — it's the proven HIPAA-compliant LLM path." Defend or refute given the 2025/2026 FMAPI HIPAA changes.

<details><summary>Answer</summary>

**Calibrate — partially right historically, increasingly wrong in 2026.**

Where the peer is right:
- **AOAI is BAA-covered, mature, regional**, and predictable for prod.
- **GPT-4o family** is genuinely strong for general reasoning and tool use.
- **Azure quota system** is well-understood by Optum's cloud team.
- **For external-facing chat with strict latency SLOs**, AOAI's regional deployments are battle-tested.

Where the peer is wrong (and getting more wrong):
- **FMAPI pay-per-token is now HIPAA-eligible** with CSP. The historical reason to default to AOAI for PHI is gone for many use cases.
- **Llama 3.3 70B is "good enough" for ~80% of enterprise RAG / extraction / classification workloads** at meaningfully lower per-token cost than GPT-4-class models.
- **Data residency** — FMAPI inference happens inside your Databricks workspace's network plane; PHI never crosses to AOAI's service. For some regulators, this is a stronger position.
- **No quota dance** — AOAI deployments require capacity planning per region; FMAPI is on-demand.
- **Single billing surface** — FMAPI usage shows up in your Databricks bill, not split across AOAI invoices.
- **Unified observability** — FMAPI inference flows through MLflow, AI Gateway, and `system.access.audit`. AOAI requires custom plumbing.

**The architect's pragmatic position for 2026:**
- **Use FMAPI Llama 3.3 70B** as the default for HIPAA-eligible RAG / extraction / classification workloads.
- **Use AOAI** when you need GPT-4-specific capabilities (function calling polish, vision-on-image-PDFs in a workflow that depends on it, customer's procurement preference).
- **Use Anthropic via Databricks** for non-PHI-prompts where Claude's quality justifies (tool-use heavy agents, long-context reasoning).
- **AI Gateway in front of all of them** — uniform rate limiting, fallback, audit, PII redaction.

**The honest pitch:** "AOAI is fine, but we're paying both AOAI's premium AND missing the FMAPI HIPAA unlock. Let's route most workloads to FMAPI and keep AOAI for the cases it's actually best at. Same compliance posture, lower cost, simpler ops."

**Sources:** [FMAPI HIPAA compliance docs](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/compliance), [HIPAA on Azure Databricks](https://learn.microsoft.com/en-us/azure/databricks/security/privacy/hipaa).
</details>
