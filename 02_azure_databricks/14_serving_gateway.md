# Module 14 — Foundation Model APIs + Model Serving + AI Gateway

> **Goal of this module:** know what each Mosaic AI Model Serving endpoint type is for, the FMAPI HIPAA breakthrough, the scale-to-zero reality, what AI Gateway gives you that raw Azure ML doesn't, and the GPU economics for healthcare AI on Azure.

---

## The four endpoint types

Mosaic AI Model Serving covers four distinct endpoint kinds. Knowing which is which is the architect's first decision:

1. **Foundation Model APIs (FMAPI), pay-per-token** — Databricks-hosted Llama 3.3 70B, Llama 4 Maverick, GTE-large, BGE-large embeddings. Pre-provisioned by Databricks; you pay per token only.
2. **Foundation Model APIs, provisioned throughput** — same models, but you reserve throughput in tokens/sec. **HIPAA-compliant in GA.** Concurrency guarantees, predictable cost.
3. **External models** — Azure OpenAI, Anthropic on Bedrock, **Anthropic native via the Databricks Anthropic Messages API** (Claude Haiku 4.5, Sonnet 4.6, Opus 4.7 with 1M context). Routed through Databricks AI Gateway.
4. **Custom models** — your own fine-tune, your own HuggingFace model, MLflow-logged PyFunc. Deploy to CPU or GPU endpoints.

---

## FMAPI — what's actually available (May 2026)

### Pay-per-token Databricks-hosted models

- **Llama 3.3 70B Instruct** (128k ctx)
- **Llama 4 Maverick** (MoE, multimodal)
- **GTE-large embeddings** (1024-dim, 8192 ctx window)
- **BGE-large embeddings** (1024-dim, 512 ctx window)
- **Anthropic Claude Haiku 4.5 / Sonnet 4.6 / Opus 4.7** (1M ctx) — via the Anthropic Messages API on Databricks; only available as pay-per-token external models
- Tool use / function calling supported on Llama-class and Anthropic
- Structured output via JSON schema response format
- Batch inference via `ai_query` (Module 15)

### Retirements worth tracking

- **Claude 3.7 Sonnet** retiring April 12, 2026
- **Mistral 8x7B** already retired
- **DBRX** retired April 2025 from FMAPI pay-per-token + fine-tuning

### Pricing

[FACTS.md](FACTS.md) has the May 2026 DBU per million tokens table. Quick reference:

| Model | Input DBU/M | Output DBU/M |
|---|---:|---:|
| Llama 4 Maverick | 7.143 | 21.429 |
| Llama 3.3 70B | 7.143 | 21.429 |
| Qwen 3 Next 80B | 2.143 | 17.143 |
| Llama 3.1 8B | 2.143 | 6.429 |

Embeddings: BGE-large 1.429 DBU/M, GTE 1.857 DBU/M.

---

## The HIPAA breakthrough

**Pay-per-token FMAPI is now BAA-eligible** with Compliance Security Profile (CSP) workspace + HIPAA-supported region. **For years, FMAPI was non-HIPAA**, forcing healthcare orgs to use only Azure OpenAI Service or self-hosted models for any LLM that touched PHI. ([FMAPI compliance docs](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/compliance))

**Specifically eligible (with CSP):**
- Llama 3.3 70B at pay-per-token
- BGE-large / GTE-large embeddings
- `LLM batch inference with ai_query` (HIPAA-only preview list as of May 2026)

**Provisioned throughput FMAPI** — HIPAA-compliant in GA across regions.

**Anthropic Claude via Databricks** — needs careful review. Being a third-party external model, you must validate that **Anthropic's BAA + Databricks' BAA + Azure's BAA all stack.** Many healthcare orgs prefer Claude via Bedrock for documented BAA chain. **Default position for PHI-prompts: use FMAPI Llama or AOAI; use Anthropic for non-PHI-prompts.**

**BAAs typically exclude Beta and Preview features.** Agent Bricks was Beta as of summit; flag for the security team.

### Architect take

**Llama 3.3 70B at pay-per-token under HIPAA is the most underrated 2025 unlock for healthcare.** For ~80% of enterprise RAG / extraction / classification workloads it's "good enough" and avoids the AOAI quota dance. **Reserve provisioned throughput for the latency-critical chat-completion path.**

---

## Mosaic AI Model Serving — the "everything endpoint"

### GPU options on Azure

| Family | GPU | Memory | Use |
|---|---|---|---|
| `NCadsA10_v4` | A10g | 24 GB | Cheap inference, light fine-tuning |
| `NCads_A100_v4` | A100 40 GB | 40 GB | 7B–13B fine-tunes |
| `NDasrA100_v4` | A100 80 GB | 80 GB | Larger models, larger batches |
| `ND_H100_v5` (8× H100) | H100 | 8× 80 GB NVLink | 70B fine-tunes |
| `NV_v5` | various | — | Visualization (rare) |
| NC v3 (V100) | V100 | 16 GB | **Being deprecated** |

ND H100 v5 lists ~$98/hr on-demand on Azure (~$12.30/GPU-hr); spot ~$70-75/hr.

### GPU model serving cost (May 2026)

| Endpoint Size | GPU | DBU/hr |
|---|---|---:|
| Small | T4 or eq. | 10.48 |
| Medium | A10G ×1 | 20.00 |
| Medium 4× | A10G ×4 | 112.00 |
| Medium 8× | A10G ×8 | 290.80 |
| Large 8× 40GB | A100 40GB ×8 | 538.40 |
| Large 8× 80GB | A100 80GB ×8 | 628.00 |

At ~$0.07/DBU base, a Medium A10G is **~$1.40/hr** = ~$1,000/mo if held warm. A Large 8X A100 80GB is **~$44/hr** = **~$32K/mo per endpoint held warm**. The most underestimated GenAI cost line in healthcare AI proposals.

---

## Scale-to-zero reality

**30-min idle window**, **10–20 sec cold start "usually" but can stretch to minutes**, **no SLA on cold start**. For GPU endpoints, the first request is "extra high latency."

Databricks' own docs explicitly say **don't use scale-to-zero for production with consistent uptime needs** ([production optimization docs](https://docs.databricks.com/aws/en/machine-learning/model-serving/production-optimization)).

**Translation:** scale-to-zero is a **dev/staging feature**, not a prod cost-saving lever. For production:
- **Min concurrency > 0** (typically 1) — accept ~$1,400/mo idle cost for an A10G endpoint to avoid p99 cold-start surprises
- **Auto-scale up** to the configured max for traffic spikes
- **Document the cost** so the FinOps team isn't surprised

### Azure GPU capacity reality

**H100 capacity in HIPAA-eligible regions (East US, Central US) is tightest.** East US 2, South Central, West US 3 are most reliable but may not satisfy data residency. **Check capacity availability before committing roadmap.**

---

## AI Gateway — the governance layer

**Renamed from "Mosaic AI Gateway" to "Unity AI Gateway"** in 2025. Sits in front of Model Serving endpoints providing:

- **Per-endpoint, per-user, per-group rate limits** (QPM and TPM)
- **Provider fallback chains** (e.g., GPT-4 → Claude on 429/5XX) without client-side changes
- **PII detection & redaction** (emails, SSN, phone) before prompt leaves the workspace
- **Custom guardrails** (March 2025 release)
- **Audit logging** to `system.access.audit`
- **Usage tracking** attributed to UC principals
- **Payload logging to inference tables**

**AI Gateway features were free in Beta through 2025** ([Unity AI Gateway product page](https://www.databricks.com/product/artificial-intelligence/ai-gateway), [Configure AI Gateway docs](https://learn.microsoft.com/en-us/azure/databricks/ai-gateway/configure-ai-gateway-endpoints)).

### Why AI Gateway matters for healthcare

- **PII redaction at the gateway layer** — prompts containing PHI are detected and redacted before they hit a non-BAA-covered LLM
- **Per-group rate limits** — prevent runaway agent loops from burning budget
- **Audit log unification** — all LLM access lands in `system.access.audit` regardless of which model was called
- **Provider fallback** — when AOAI is throttled, fall back to FMAPI Llama; when both are down, fail closed gracefully

**AI Gateway is what differentiates Mosaic Serving from raw Azure ML endpoints.** For an architect at Optum, this is a real value-add over rolling your own gateway.

---

## Architect take vs alternatives

### vs Azure ML online endpoints

- **AML** — more flexible (any container, any framework), no opinion on prompts/tokens
- **Mosaic Serving** — opinionated specifically for LLMs; integrates token accounting, AI Gateway, MLflow tracing, UC governance natively

**If you're on Databricks anyway, AML endpoints become an integration tax.** Use Mosaic.

### vs vLLM-on-AKS

- **vLLM-on-AKS** gives the absolute best $/token economics if you have an MLE comfortable with Kubernetes, GPU operator, autoscaling, operational overhead
- **Mosaic Serving** gives you ~80% of the throughput at 30%+ price premium with zero ops

**For a healthcare org without a deep platform team: Mosaic.** For a mature AI platform team with K8s muscle: vLLM-on-AKS.

### vs Azure OpenAI

- **AOAI** — Azure-native quota, regional pinning, BAA in-scope
- **Mosaic FMAPI** — Llama and open weights; different model menu

**Most enterprise architectures will end up using both, with AI Gateway as the reverse proxy.** Don't try to standardize on one; the model catalogs are complements.

---

## Production patterns

### Pattern: HIPAA-compliant LLM serving for clinical RAG

```
Clinical PDFs in UC Volume
   ↓
Vector Search (Module 13)
   ↓
Agent retrieves top-5 chunks
   ↓ (PHI in retrieved chunks)
Pay-per-token FMAPI (Llama 3.3 70B) — HIPAA-eligible with CSP
   ↓ Routed via AI Gateway
   ↓
Response with PII redacted (gateway-side)
   ↓
Inference table logs (request + response, encrypted with DBFS-root CMK)
   ↓
Audit trail in system.access.audit
```

**Discipline:**
- **CSP=HIPAA workspace** with all the network controls (Module 21)
- **AI Gateway with PII redaction enabled** as a defense in depth — even if the prompt accidentally contains member SSN, gateway redacts before transit
- **Inference tables tagged with `phi_class=high`** in UC; ABAC policies prevent unauthorized reads
- **Per-group rate limits** on the agent endpoint to prevent budget runaway

### Pattern: provisioned throughput for chat SLO

For a clinical chat app with sub-3-second p99 latency requirement:

```python
# Provisioned throughput endpoint
endpoint_config = {
    "name": "clinical-chat-pt",
    "config": {
        "served_models": [{
            "name": "claude-sonnet-46-pt",
            "external_model": {
                "name": "claude-sonnet-4-6",
                "provider": "databricks-anthropic",
                "task": "llm/v1/chat",
            },
            "min_provisioned_throughput": 100,   # tokens/sec
            "max_provisioned_throughput": 500,
            "scale_to_zero_enabled": False,       # DON'T for prod
        }],
        "auto_capture_config": {
            "catalog_name": "prod_phi_clinical",
            "schema_name": "ai_observability",
            "enabled": True,
            "table_name_prefix": "clinical_chat"
        }
    }
}

w = WorkspaceClient()
w.serving_endpoints.create(**endpoint_config)
```

**Provisioned throughput pays back when:**
- Traffic is predictable (you know the floor)
- p99 latency matters (no scale-up jitter)
- Cost-per-token at scale beats per-token rates

**Pay-per-token wins when:**
- Traffic is bursty and unpredictable
- Cold-start latency is acceptable
- Volume is small enough that PT min commitment exceeds actual usage

### Pattern: AI Gateway with fallback for resilience

```python
# Gateway routes requests to a primary endpoint with fallback
gateway_route = {
    "name": "clinical-chat-route",
    "primary_endpoint": "clinical-chat-pt",
    "fallback_endpoints": [
        "clinical-chat-fmapi-llama-3-3",  # if PT throttles or fails
        "clinical-chat-aoai-gpt-4o"        # second-tier fallback
    ],
    "rate_limits": [
        {"calls": 1000, "renewal_period": "minute", "key": "user"},
        {"calls": 10000, "renewal_period": "hour", "key": "endpoint"}
    ],
    "guardrails": {
        "pii_detection": {"enabled": True, "action": "REDACT"},
        "input_max_tokens": 8000,
        "output_max_tokens": 2000
    }
}
```

The fallback chain handles AOAI throttling, region issues, model deprecations transparently.

---

## Pain points

- **Model artifact size** — large LoRA adapters or full-tune checkpoints push artifact stores to GBs.
- **Cold start** — 10s–minutes, no SLA. **Always have a warm pool for prod.**
- **Region availability for GPUs** — H100 capacity on Azure is fluid. Plan capacity with the Azure account team before committing roadmap.
- **BAA scope on previews** — every "Beta" or "Preview" feature is **out of BAA by default**. Maintain a canonical list of BAA-covered features per workspace.
- **NCCL multi-node debugging** — real grunt work even on managed Databricks; budget 15-25% extra for first multi-node fine-tune.
- **Cost attribution** — token spend across FMAPI, external models, agent endpoints requires `system.serving` table queries; not visible in default cost dashboards. Build the FinOps dashboard yourself in Lakeview.

---

## When NOT to use Mosaic Serving

- **Sub-100ms inference latency at extreme cost-per-token discipline** — vLLM-on-AKS or self-hosted will beat Mosaic if you have the ops team
- **Custom containers / unusual frameworks** — AML's flexibility wins
- **Pure batch inference without real-time** — `ai_query` (Module 15) is cheaper than spinning a serving endpoint
- **Models you can't get on FMAPI and don't want to manage** — use Bedrock directly via the Anthropic Messages API or AOAI

---

## Sanity check

1. What are the four Model Serving endpoint types, and when do you use each?
2. The pay-per-token FMAPI HIPAA breakthrough — what specifically changed and what's the architect implication?
3. Why does Databricks tell you NOT to use scale-to-zero in production?
4. What does AI Gateway give you that raw Azure ML endpoints don't?
5. A Large 8X A100 80GB endpoint held warm costs how much per month, roughly? Why does this matter for your cost projection?
6. Anthropic Claude via Databricks — what's the BAA conversation you need to have for PHI prompts?

---

## Further reading

- [Mosaic AI Model Serving — Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/machine-learning/model-serving/)
- [Foundation Model APIs supported models](https://learn.microsoft.com/en-us/azure/databricks/machine-learning/foundation-model-apis/supported-models)
- [FMAPI compliance / HIPAA](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/compliance)
- [Anthropic Messages API on Databricks](https://docs.databricks.com/aws/en/machine-learning/model-serving/query-anthropic-messages)
- [Unity AI Gateway product page](https://www.databricks.com/product/artificial-intelligence/ai-gateway)
- [Configure AI Gateway endpoints](https://learn.microsoft.com/en-us/azure/databricks/ai-gateway/configure-ai-gateway-endpoints)
- [GPU-enabled compute](https://learn.microsoft.com/en-us/azure/databricks/compute/gpu)
- [Production optimization for Model Serving](https://docs.databricks.com/aws/en/machine-learning/model-serving/production-optimization)
- [Vantage instance pricing — Azure ND H100 v5](https://instances.vantage.sh/azure/vm/nd96isrh100-v5)
