# Quiz 01 — Design Applications (14%, 19 Qs)

> Take cold (no peeking). ~2 min per question. Maps to **Modules 01–02**.

---

## Recall

1. The Databricks Foundation Model APIs (FMAPI) offer two billing modes. Name them and one defining property of each.
2. Which Mar 2026 exam section newly introduces **Agent Bricks**?
3. List the three Agent Bricks variants.
4. A fine-tuned model can be deployed via which FMAPI billing mode — Pay-per-token, Provisioned Throughput, or both?
5. Name the multimodal Foundation Model available in the Databricks catalog as of May 2026.

## Apply

6. Business ask: "Generate a one-line marketing tagline from a SKU's specs." Which GenAI pattern do you pick? (Prompt eng / RAG / single-agent / multi-agent / fine-tune)
7. Business ask: "Tell the customer their last shipment's delivery date for transaction X." RAG, fine-tune, or feature lookup via an agent tool?
8. Business ask: "Auto-extract `vendor_name`, `invoice_date`, `total_amount` from 1M PDF invoices, minimal team to maintain." Information Extraction Brick vs custom prompt + `ai_extract` SQL — which fits the prompt better?
9. The prompt says: "Customer query may need a SQL aggregate over claims OR retrieval over policy docs." Which Agent Bricks variant?
10. Workload: 50 concurrent users, ~800 input tokens / ~200 output tokens, < 2s p95, HIPAA. PPT or PT, and roughly how many PT units (order of magnitude)?

## Diagnose

11. Agent demo locally hits SLA but fails in production with `MODEL_NOT_AVAILABLE`. What's the likely lifecycle issue?
12. The base LLM produces good answers but in plain prose; downstream parser expects strict JSON. The team adds "respond in JSON" to the system prompt; reliability is only 70%. What's the next step?
13. The agent uses a fine-tuned model + the configured endpoint is PPT. Result: deployment fails. Why?
14. The retrieval step returns the top-5 by ANN only. Quality is poor. Diagnosis?

## Defend

15. Argue why "fine-tune the LLM with the member database" is wrong for a use case that needs the current per-member delivery date.
16. The team wants to use Agent Bricks Knowledge Assistant for a patient-facing PHI Q&A bot in production. Argue against.
17. Justify picking Llama 3.1 8B over Llama 3.3 70B for an internal classification task with strict cost constraints.

## [Multi-select]

18. **[select TWO]** Which patterns are appropriate when the business says *"minimize maintenance / no team to maintain the agent / auto-optimize cost/quality"*?
   (A) Agent Framework with custom LangGraph
   (B) Agent Bricks Knowledge Assistant
   (C) Agent Bricks Information Extraction
   (D) Hand-rolled pyfunc with LangChain
   (E) Direct OpenAI SDK call

19. **[select TWO]** Which model attributes are relevant when selecting an LLM for a long-context QA over 80-page contracts?
   (A) Context window
   (B) Multimodal capability
   (C) Tool-calling reliability
   (D) Latency under streaming
   (E) Model retirement date

---

## Answers (don't peek until done)

1. **Pay-per-token (PPT)** — per-token billing, dev/spiky traffic, AI Playground; **Provisioned Throughput (PT)** — hourly per PT unit, production guarantees, HIPAA, hosts fine-tuned models. → Module 02
2. **Section 1: Design Applications** (Obj 6). → Module 09
3. Knowledge Assistant, Multi-Agent Supervisor, Information Extraction. → Module 09
4. **PT only.** Fine-tuned models cannot be served via PPT. → Module 02
5. **Llama 4 Maverick** (and Scout). → Module 02
6. **Prompt engineering.** No enterprise data needed; one LLM call with templated prompt. → Module 01
7. **Feature lookup via agent tool.** Per-record dynamic data lives in a feature store / Online Table. NOT fine-tuning (sample Q2 trap). → Module 01
8. **Information Extraction Brick.** "Minimal team to maintain" + "auto-optimize" is the Bricks signal phrase. → Module 09
9. **Multi-Agent Supervisor.** Routes across Genie (SQL aggregates) and Knowledge Assistant (RAG). → Module 09
10. **PT** (HIPAA + sustained QPS). At ~50,000 tokens/sec total and ~1.5K tokens/sec per PT unit, **~30–40 PT units**. Exact number from GenAI Calculator. → Module 02
11. The base model was **retired** on its scheduled retirement date. The endpoint configured a model whose PPT or PT lifecycle ended. Re-pin to a current model + version. → Module 02
12. **Use structured output API or Pydantic + retry**. Or use `ai_extract` if the task is field extraction. Vague prompt instructions plateau around 70%; the platform-level structured-output enforcement is the next reliability rung. → Module 05
13. **Fine-tuned models deploy only as PT, not PPT.** Switch to a PT endpoint. → Module 02
14. **No reranker.** Top-5 ANN misses borderline-relevant chunks. Over-retrieve (top-50) and apply a cross-encoder rerank step. → Module 01, 04
15. Fine-tuning bakes data into weights; per-member dynamic data drifts daily. Result: stale answers + leaked PHI across members + 7-figure cost to retrain monthly. Correct pattern: feature store / Online Table lookup as a tool. → Module 01
16. Bricks is **Beta** for the regulated PHI category; BAA scope unclear; abstracts prompt and retrieval config that compliance must review; no fine-grained per-step audit. Pick **Agent Framework** for regulated production. → Module 09
17. Llama 8B is 10–50× cheaper per token; classification is well within 8B capability; quality bar for label assignment is typically clearable; eval on golden set will confirm. Use the smaller model that clears the bar, not the bigger one "to be safe." → Module 02, 15
18. **(B) and (C)** — both Bricks variants. (A) custom LangGraph and (D) hand-rolled pyfunc require maintenance. (E) sidesteps Databricks governance entirely. → Module 09
19. **(A) Context window** and **(E) Model retirement date**. (B) multimodal not needed for text contracts. (C) tool-calling not the binding constraint. (D) streaming nice-to-have but not core for QA. → Module 02
