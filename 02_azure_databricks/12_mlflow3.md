# Module 12 — MLflow 3.0 Deep

> **Goal of this module:** know what MLflow 3.0 (June 2025) brought to the GenAI side, why it's the strongest piece of the Mosaic AI stack, and how it stacks against LangSmith / Langfuse / Phoenix / Helicone for an AI architect at a healthcare org.
>
> **Assumes:** you understand the basics of experiment tracking from Topic 01's evaluation modules (13A/13B/13C). This module is about how Databricks-hosted MLflow specifically extends the OSS picture.

---

## Why MLflow 3.0 matters

Pre-3.0 MLflow was "the experiment tracker" — runs, parameters, metrics, artifacts, model registry. That mental model was sufficient for classical ML and incomplete for GenAI.

**MLflow 3.0 (released June 2025 at DAIS)** is a major rewrite focused on GenAI: **trace-first observability**, **prompts as first-class entities**, **LLM-judge evaluation** built in, and a new **`LoggedModel`** versioning concept that links a model version to its Git commit, configs, traces, and eval runs ([MLflow 3 launch blog](https://www.databricks.com/blog/mlflow-30-unified-ai-experimentation-observability-and-governance), [MLflow.org 3 release](https://mlflow.org/releases/3)).

It's **open source, Apache 2.0, Linux Foundation.** Databricks reports adoption by ~60% of the Fortune 500. For an architect on Databricks, **it's no longer "the experiment tracker" — it's the LLM observability + evaluation + prompt registry platform that competes head-on with LangSmith / Langfuse / Phoenix / Helicone.**

---

## What ships in MLflow 3 for GenAI

### Tracing with autolog for 20+ libraries

```python
import mlflow

# One-line instrumentation
mlflow.openai.autolog()
mlflow.anthropic.autolog()
mlflow.langchain.autolog()
mlflow.llama_index.autolog()
mlflow.dspy.autolog()

# Now any call through these libs produces OpenTelemetry-compatible spans
```

Autolog produces:
- **Traces** with inputs, outputs, token counts, latency, tool calls
- **Nested traces** logged automatically via the LangChain Callbacks framework
- **OTEL-compatible spans** that interoperate with broader observability (Datadog, Splunk via OTLP)

This is the **single biggest reason** to be on MLflow 3 — one line gives you GenAI observability that you'd otherwise pay LangSmith / Langfuse for.

### Prompt Registry — first-class prompts

```python
# Register a prompt as a versioned UC object
mlflow.prompts.register(
    name="claim_summary_v3",
    template="Summarize this claim line for a clinical reviewer: {claim_line}",
    version="v3",
    tags={"team": "claims", "use_case": "review"}
)

# Set an alias (champion / challenger)
mlflow.prompts.set_alias("claim_summary_v3", alias="champion")

# Use the prompt by alias
prompt = mlflow.prompts.load("claim_summary", alias="champion")
```

**Git-style versioning, aliases (`champion`, `challenger`), visual diffs in the UI, rollback.** The closest first-party competitor to PromptLayer — and it lives next to your model artifacts in UC.

### Evaluation harness

```python
import mlflow.evaluate as mle

# Built-in scorers
results = mlflow.evaluate(
    data=eval_dataset,
    model="prod_phi_claims.models.claim_summarizer",
    targets="ground_truth",
    metrics=[
        "exact_match",
        "rouge",
        mlflow.metrics.genai.faithfulness(),    # built-in LLM judge
        mlflow.metrics.genai.relevance(),
        mlflow.metrics.genai.answer_correctness(),
    ],
    judge_model="endpoints:/databricks-claude-sonnet-4-6"
)
```

- **Built-in scorers** plus integrations to RAGAS, DeepEval, Phoenix, TruLens, Guardrails AI.
- **Multi-turn evaluation** for agent flows.
- **Online evaluation** against production traffic (samples from inference tables).
- **Judge alignment** — calibrate an LLM-as-judge against a labeled human-feedback set.

### Agent eval — trajectory-level scoring

```python
# Score the full agent trajectory, not just the final answer
results = mlflow.evaluate(
    data=eval_dataset,
    model=my_agent,
    metrics=[
        mlflow.metrics.genai.tool_use_correctness(),  # right tools in right order
        mlflow.metrics.genai.groundedness(),
        mlflow.metrics.genai.relevance(),
    ]
)
```

Most agent failure modes are at **step transitions** (wrong tool selected, wrong arguments, hallucinated tool output). Trajectory-level scoring catches them.

### DSPy compile tracing

```python
import mlflow

mlflow.dspy.autolog(log_traces_from_compile=True)

# DSPy compile fires thousands of LM calls; off-by-default for trace explosion
optimized = compile_program(my_module, trainset)
```

By default off (compilation can fire thousands of module calls); opt-in via `log_traces_from_compile=True`. Critical for anyone doing prompt optimization with DSPy.

### `LoggedModel` — the full lineage

A LoggedModel ties together:
- **Model code** (Git commit hash)
- **Configs** (prompt versions, model parameters, retrieval params)
- **Traces** (every inference run logged)
- **Eval runs** (the eval results that justified deploying this version)
- **MLflow Run** (the training run if applicable)
- **UC model registry entry**

For a healthcare audit conversation, this is the **answer to "show me what model produced this output, with what prompt, against what data."**

---

## Honest comparison vs alternatives

| Need | MLflow 3 | LangSmith | Langfuse | Phoenix | Helicone |
|---|---|---|---|---|---|
| OSS + self-host | Yes (Apache 2.0) | No | Yes | Yes | Partial |
| Prompt registry depth | Strong | Strong | Medium | Weak | Weak |
| Built-in judge alignment | Yes | Yes | No | Limited | No |
| Native Databricks integration | Native | Bolt-on | Bolt-on | Bolt-on | Bolt-on |
| Multi-turn / agent eval | Yes | Yes | Basic | Yes | No |
| Multi-step trajectory analysis | Strong | Strong | Basic | **Best (50+ research-backed metrics)** | Weak |
| Cost / token analytics | Built-in | Strong | Strong | Strong | **Best (gateway-first)** |

### Architect take

**If you're on Databricks, MLflow 3 is the default** — not because it's the best at every dimension (Phoenix is still arguably better at multi-step trajectory analysis), but because the **lineage to UC tables, Vector Search indexes, and serving endpoints is automatic.**

**For a healthcare org under HIPAA, "no third-party LLM observability vendor in the data path" is a real procurement win.** Sending traces to a SaaS LangSmith means PHI may transit a third party that needs its own BAA — usually a non-starter. MLflow 3 self-hosts (or runs on Databricks-managed infra under your BAA scope) and avoids that conversation.

---

## Production patterns

### Pattern: agent inference traced end-to-end

```python
import mlflow
from langgraph.graph import StateGraph

mlflow.langchain.autolog()
mlflow.openai.autolog()  # or mlflow.anthropic.autolog()

# Build the agent graph
graph = StateGraph(MyState)
graph.add_node("retrieve", retrieve_node)
graph.add_node("generate", generate_node)
graph.add_node("validate", validate_node)
agent = graph.compile()

# Every invocation is traced
with mlflow.start_run(run_name="agent_invoke") as run:
    result = agent.invoke({"query": user_query})
    mlflow.log_param("user_id", user_id)
```

The trace UI shows every node, every retrieval call, every LLM call, every tool invocation, with token counts and latency. **Debugging an agent that "sometimes hallucinates" reduces to looking at the trace for the bad case.**

### Pattern: prompt registry as the change-control surface

```python
# Production code references prompts by alias, not literal
prompt = mlflow.prompts.load("claim_summary", alias="champion")

# A new prompt version is registered (manually or via PR)
mlflow.prompts.register(
    name="claim_summary",
    template="...",
    version="v4",
    tags={"author": "alice", "ticket": "JIRA-12345"}
)

# Promote in CI after eval gate passes
mlflow.prompts.set_alias("claim_summary", alias="challenger", version="v4")

# After A/B testing, promote
mlflow.prompts.set_alias("claim_summary", alias="champion", version="v4")
```

The architect's rule: **never hardcode prompts in production code.** Every prompt lives in the registry; production references by alias. Changes go through registry promotion + eval gate.

### Pattern: judge alignment for healthcare-specific metrics

```python
# Step 1: gather a labeled set of (prompt, response, human_judgment) examples
labeled_set = spark.table("eval.clinical_review_labels")

# Step 2: define the judge
clinical_judge = mlflow.metrics.genai.make_genai_metric(
    name="clinical_appropriateness",
    judge_model="endpoints:/databricks-claude-sonnet-4-6",
    grading_prompt="""Rate the clinical appropriateness of this summary 
for review by a registered nurse on a 1-5 scale. 
Considerations: factual accuracy, omission of relevant details, 
overstatement of clinical significance.""",
    examples=labeled_set
)

# Step 3: validate the judge against held-out human labels
validation = mlflow.evaluate(
    data=held_out_set,
    metrics=[clinical_judge]
)

# If alignment with human labels > some threshold, deploy the judge
```

**Judge alignment** is the discipline that makes LLM-as-judge defensible. Without it, you're using one LLM to grade another with no calibration to ground truth.

---

## When MLflow 3 isn't the right answer

- **You need multi-step trajectory analysis with research-grade metrics** — Phoenix has 50+ specialized metrics; MLflow 3's built-in set is smaller.
- **You're not on Databricks** — MLflow 3 is OSS, but the deep integration with UC / Vector Search / Model Serving is the value-add. Off-Databricks, LangSmith may have a smoother experience.
- **You need a gateway with cost-per-customer attribution** — Helicone is gateway-first and better at this.
- **Your team is heavily invested in LangSmith already** — switching cost may not pay back.

For Optum specifically, **MLflow 3 is the right default** — Databricks-native, BAA-eligible, no third-party data path.

---

## Pain points to know

- **Artifact bloat** — large LoRA adapters or full-tune checkpoints push artifact stores to GBs. Use `mlflow.pyfunc.log_model` with model code paths and external artifact references rather than `log_artifact` for everything.
- **Trace volume** — high-throughput agents produce huge traces; sample in production via `mlflow.set_logging_sample_rate(0.1)` or filter what's traced.
- **Cross-platform monitoring** — works for agents running outside Databricks, but the integration is rougher than for Databricks-native serving endpoints.
- **DSPy compile traces are off by default** for good reason — opting in produces a flood; only enable when you specifically need to debug optimization.

---

## Sanity check

1. What's the difference between MLflow 2.x's "run + params + metrics + artifacts" model and MLflow 3.0's GenAI surface?
2. Why is judge alignment important, and what does it mean operationally?
3. How does the Prompt Registry change the production code-vs-prompt change control story?
4. When is Phoenix better than MLflow 3 for agent trajectory analysis?
5. Why does "no third-party LLM observability vendor in the data path" matter for healthcare?
6. A team is using DSPy and complains traces are exploding. What's the lever?

---

## Further reading

- [MLflow 3 launch blog (Databricks)](https://www.databricks.com/blog/mlflow-30-unified-ai-experimentation-observability-and-governance)
- [MLflow 3 release (mlflow.org)](https://mlflow.org/releases/3)
- [MLflow GenAI tracing](https://mlflow.org/docs/latest/genai/tracing/)
- [MLflow Langfuse alternative comparison](https://mlflow.org/langfuse-alternative/)
- [MLflow top-5 agent observability tools](https://mlflow.org/top-5-agent-observability-tools/)
- [MLflow DSPy integration on Azure Databricks](https://learn.microsoft.com/en-us/azure/databricks/mlflow3/genai/tracing/integrations/dspy)
- [Perficient — MLflow 3 features](https://blogs.perficient.com/2025/06/30/mlflow-3-0-genai-features-revolutionizing-ai-development/)
- [Phoenix (Arize) — multi-step agent metrics](https://docs.arize.com/phoenix)
- [LangSmith comparison](https://www.langchain.com/langsmith)
