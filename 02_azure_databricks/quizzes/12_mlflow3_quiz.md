# Quiz — Module 12: MLflow 3.0 Deep

## Recall

**Q1.** What's the most important addition in MLflow 3.0 (June 2025) for GenAI workloads?

<details><summary>Answer</summary>

**Trace-first observability with autolog for 20+ libraries.** One line — e.g., `mlflow.langchain.autolog()` or `mlflow.anthropic.autolog()` — produces OpenTelemetry-compatible spans capturing inputs, outputs, token counts, latency, tool calls. Nested traces log automatically via callback frameworks.

This is what makes MLflow 3 a competitor to LangSmith / Langfuse / Phoenix / Helicone — pre-3.0, MLflow was "experiment tracker" with manual tracing. Now it's a real LLM observability platform.

**Other major additions:**
- **Prompt Registry** — Git-style versioning, aliases, visual diffs
- **Evaluation harness** with built-in LLM judges + judge-alignment to labeled human data
- **Agent eval** — trajectory-level scoring
- **`LoggedModel`** — links model version to Git commit, configs, traces, eval runs
</details>

**Q2.** What's "judge alignment" and why does it matter?

<details><summary>Answer</summary>

**Judge alignment** = calibrating an LLM-as-judge against a labeled human-feedback set. You collect a set of (prompt, response, human_judgment) examples, configure the LLM judge with a grading prompt, and validate that the judge's outputs correlate with the human labels above some threshold.

**Why it matters:** without alignment, you're using one LLM to grade another with no calibration to ground truth. The judge might consistently rate things as "good" that humans disagree with, or systematically penalize things humans like.

**Operationally:** before deploying an LLM judge to production evaluation, run it against a held-out human-labeled set and verify alignment (correlation, agreement rate, bias direction). If it's misaligned, either retune the grading prompt or pick a different judge model. Don't ship un-aligned judges to evaluate production GenAI.

For healthcare specifically: clinical metrics (clinical appropriateness, omission of relevant details, factual accuracy) are *exactly* the cases where a generic judge fails — domain-specific alignment is mandatory.
</details>

---

## Apply

**Q3.** Write a code snippet that registers a clinical-summary prompt with versioning + aliasing, then references it from production code.

<details><summary>Answer</summary>

```python
import mlflow

# Register prompt v3
mlflow.prompts.register(
    name="claim_summary",
    template="""You are a clinical reviewer assistant. Summarize this claim line 
for review by a registered nurse. Be concise. Flag missing information explicitly.

Claim line:
{claim_line}

Member context:
{member_context}

Summary:""",
    version="v3",
    tags={
        "team": "claims-review",
        "ticket": "JIRA-CLNCREV-12345",
        "author": "data-eng@optum.com",
        "phi_class": "high",  # operational tagging
    }
)

# Promote to challenger after CI eval gate passes
mlflow.prompts.set_alias("claim_summary", alias="challenger", version="v3")

# After A/B testing, promote to champion
mlflow.prompts.set_alias("claim_summary", alias="champion", version="v3")

# --- Production code (in agent_runner.py) ---

prompt_template = mlflow.prompts.load("claim_summary", alias="champion")

# Use the template (substitute via str.format or langchain's PromptTemplate)
filled = prompt_template.template.format(
    claim_line=claim_data,
    member_context=member_data
)

# Send to LLM via Foundation Model APIs
response = client.predict(
    endpoint="databricks-claude-sonnet-4-6",
    inputs={"messages": [{"role": "user", "content": filled}]}
)
```

**Production discipline:**
- **Never hardcode prompts in code.** Production references prompts by alias.
- **Promotion via CI** — a PR that registers a new prompt version triggers an eval gate; if the eval passes, CI promotes alias to `challenger`; A/B testing promotes to `champion`.
- **Tag with PHI class** — important for HIPAA audit (does this prompt template ever see PHI?).
- **Visual diffs in the MLflow UI** make prompt changes reviewable.
</details>

---

## Diagnose

**Q4.** A team's agent observability is fragmented — some traces in MLflow, some in LangSmith (a previous-team decision), some not traced at all. They want to consolidate. Walk through the migration to MLflow 3 as the single source.

<details><summary>Answer</summary>

**Migration plan:**

1. **Inventory current trace destinations.** Find every `langsmith.trace` decorator, every `LangChainTracer` callback, every custom `print()`-based logging. Document.

2. **Pick MLflow 3 as the destination** with explicit rationale:
   - Native Databricks integration (UC lineage, Vector Search, Model Serving connect automatically)
   - HIPAA-eligible without third-party data-path BAA conversation
   - OSS + self-host vs LangSmith's vendor lock-in
   - Cross-library autolog covers 20+ libraries

3. **Replace LangSmith setup with MLflow autolog:**
   ```python
   # Old
   from langchain.callbacks.tracers.langchain import LangChainTracer
   tracer = LangChainTracer(project_name="claims-agent")
   
   # New
   import mlflow
   mlflow.langchain.autolog()
   mlflow.set_experiment("/Shared/claims-agent")
   ```
   Same one-line setup; existing LangChain callbacks work transparently.

4. **For the "not traced at all" cases**, add the appropriate autolog: `mlflow.openai.autolog()`, `mlflow.anthropic.autolog()`, etc.

5. **Migrate existing trace data?** Probably not worth it — LangSmith traces are a different schema. Cut the changeover cleanly: from date X, all new traces in MLflow; LangSmith stays read-only for historical lookup until retention expires.

6. **Update dashboards / alerting** that reference LangSmith metrics. Build equivalent Lakeview dashboards from MLflow trace data.

7. **Communicate to engineers** — the muscle memory shift from "open LangSmith for trace debugging" to "open MLflow Trace UI" takes a few weeks.

**Anticipate friction:**
- **DSPy compile tracing** — off by default in MLflow; engineers may complain "I can't see compile traces." Document the `log_traces_from_compile=True` opt-in.
- **High-throughput agents** — sample in production via `mlflow.set_logging_sample_rate(0.1)` to keep trace volume manageable.
- **Cost-attribution dashboards** — MLflow 3 has token/cost data in traces; build a dashboard from `system.serving.usage` joined with MLflow trace metadata.

**The architect's pitch:** "We're consolidating to MLflow 3 because it gives us BAA-clean tracing, native UC integration, and we drop a third-party SaaS bill. The migration is a one-line autolog change in code."
</details>

---

## Defend

**Q5.** A peer says "we should use Phoenix instead of MLflow 3 — its agent metrics are better." Defend or refute for an Optum healthcare context.

<details><summary>Answer</summary>

**Calibrate — partially right, but MLflow 3 wins on the integration argument.**

Where the peer is right:
- **Phoenix has 50+ research-backed metrics** for multi-step agent trajectory analysis. For deep agent debugging and metric variety, Phoenix is genuinely strong.
- **Phoenix is OSS** and self-hostable; not a vendor lock-in.
- **For pure model evaluation work** (testing different agent architectures, comparing trajectory metrics), Phoenix can give you better signals.

Where the peer is wrong for Optum:
- **MLflow 3 has the native Databricks integration** — automatic lineage to UC tables, Vector Search indexes, Model Serving endpoints, prompt registry. With Phoenix, you bolt-on; with MLflow 3, it's built in.
- **HIPAA / BAA scope** — Phoenix self-hosted under your BAA is fine, but the operational cost of running it is non-trivial. MLflow 3 hosted on Databricks is BAA-covered automatically.
- **Prompt registry** — Phoenix doesn't have one (or the equivalent is much weaker). For production change control, prompt registry is load-bearing; you'd end up running both Phoenix + something else for prompts.
- **Single source of truth** — splitting tracing between Phoenix and MLflow doubles the operational surface. Engineers context-switch between two UIs.

**The honest synthesis:**
- **Use MLflow 3 as the production tracing + prompt registry + evaluation source of truth.**
- **Use Phoenix selectively for deep agent metric analysis** during development — pull traces from MLflow into Phoenix for the cases where the 50+ metrics matter, then ship the configuration that won.
- **Don't try to replace MLflow 3 with Phoenix.** The operational cost of two systems exceeds the metric-variety benefit for most production work.

**The architect's pitch:** "MLflow 3 is the platform tracing source. Phoenix is a power tool for deep dives during eval research. We don't run them in production parallel; we use Phoenix when MLflow's metrics aren't sufficient for a specific question."

**Sources:** [MLflow top-5 agent observability tools comparison](https://mlflow.org/top-5-agent-observability-tools/), [MLflow Langfuse alternative](https://mlflow.org/langfuse-alternative/).
</details>
