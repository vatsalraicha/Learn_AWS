# Quiz 06 — Evaluation & Monitoring (12%, 16 Qs)

> Take cold. ~2 min/Q. Maps to **Modules 14–15**.

---

## Recall

1. Which `mlflow.genai` function runs an evaluation against a dataset with scorers?
2. From: Relevance, Groundedness, Correctness, Safety, ChunkRelevance, Similarity — which require ground truth?
3. State the difference between AI Gateway Inference Tables and Usage Tables.
4. What's the API call to register a custom Scorer decorator-style?
5. Name two cost-control levers for LLM workloads on Databricks.
6. State the difference between evaluation and monitoring in one sentence.

## Apply

7. Three SMEs disagree on 30% of items. The exam asks the best action. From: average / drop disputed / rubrics + calibration + `mlflow.genai.evaluate()` / replace with LLM judge — which?
8. You need a metric "every answer must include at least one `[S\d+]` citation." Built-in or custom?
9. Mean Groundedness drops from 0.91 to 0.78 over a week in prod. What's a likely cause and a diagnostic step?
10. The agent picks a smaller LLM for a classification task. How do you justify it quantitatively?
11. Rate limiting: 1000 calls/user/minute. User X submits 10K calls/min. Result?

## Diagnose

12. The retrieval judge returns 0.0 even though the retriever appears to return relevant chunks. What's likely wrong in tracing?
13. Eval score `mean_relevance = 0.95` in dev but production responses show high refusal rate. Diagnosis?
14. The Inference Table has request rows but no `latency_ms`. Why?

## Defend

15. Justify investing in a golden eval dataset over relying on production monitoring alone.

## [Multi-select]

16. **[select TWO]** Things that AI Gateway tracks for a live agent (Sec 6 Obj 8).
    (A) Inference Tables
    (B) Usage Tables
    (C) Embedding storage size
    (D) Rate limiting metrics
    (E) Workspace billing line items

---

## Answers

1. **`mlflow.genai.evaluate(data=..., predict_fn=..., scorers=[...])`**. → Module 14
2. **Correctness** and **Similarity** (both compare against expected). The others can score without a reference. → Module 14
3. **Inference Tables** = raw per-request log (request, response, latency, tokens, status) for audit + offline eval. **Usage Tables** = aggregates (tokens, DBUs per user per endpoint per day) for FinOps. → Module 15
4. **`@mlflow.genai.scorer`** decorator (or subclass `mlflow.genai.scorers.Scorer`). → Module 14
5. From: smaller model where possible / caching frequent queries / output length cap / rate limiting per user / scale-to-zero / batch via `ai_query` / storage-optimized VS / embedding cache / Provisioned Throughput at high QPS / prompt compression. Pick any two. → Module 15
6. **Evaluation** = curated golden dataset, pre-deployment, on every change. **Monitoring** = live traffic via Inference Tables, continuous post-deployment. → Module 14
7. **Rubrics + SME calibration + `mlflow.genai.evaluate()`.** Sample Q10 answer. Averaging muddies noise; dropping loses hard examples; LLM-judge as source-of-truth is wrong. → Module 14
8. **Custom scorer** — regex-match `\[S\d+\]` in the response. Built-in judges don't cover format constraints. → Module 14
9. Likely causes: (a) source data drift (new docs added that confuse the retriever), (b) embedding model lifecycle change, (c) chunking pipeline regression. Diagnostic: re-run last week's golden eval set; if scores stable on golden but degraded on prod sample, retrieval distribution has shifted. Investigate query mix and source updates. → Modules 14, 15
10. Run `mlflow.genai.evaluate()` on the golden set with both candidates (small + large). Plot quality (composite Relevance/Correctness) vs cost per 1K requests. Pick the smallest that clears the quality bar (e.g., 0.85 mean Correctness). Document the trade-off in the run. → Module 15
11. Requests above 1000/min are **rejected with a rate-limit error**. User waits for the next minute window. Other users unaffected. → Module 15
12. **Span types missing.** ChunkRelevance / RetrievalRelevance judges look for `RETRIEVER`-typed spans. If retrieval ran but the span wasn't tagged with `span_type="RETRIEVER"` (or autolog didn't capture it), judges find no retrieval data. → Module 14
13. **Eval set lacks coverage of out-of-scope / hard-edge cases.** Dev score is high because dataset is happy-path-only; prod has real distribution including OOS questions the agent (correctly or not) refuses. Add OOS / edge / adversarial coverage to the eval set. → Module 14
14. **AI Gateway Inference Tables not enabled** on the endpoint, OR the processed (flattened) table isn't queried — raw table only has the JSON payload. Enable the inference table config explicitly. → Module 15
15. Monitoring tells you the live agent's behavior on real users, **but it does not tell you "is this new version better than the last."** You need a fixed dataset (golden set) to do head-to-head version comparison, regression testing, and pre-deployment gating. Monitoring catches regressions in production; eval prevents them from shipping. Both are required; eval is the prevention layer. → Module 14
16. **(A) Inference Tables** and **(B) Usage Tables**. Also **(D) Rate limiting metrics** — all three are Sec 6 Obj 8 features. Pick the two strongest. (C) and (E) aren't AI Gateway features. → Module 15
