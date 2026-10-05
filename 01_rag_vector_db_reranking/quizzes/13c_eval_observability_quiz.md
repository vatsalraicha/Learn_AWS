# Quiz — Module 13C (Production Observability & Ops)

## Recall

1. Name 5 fields you'd minimum-log per RAG query for debuggability.
2. What is OpenTelemetry's role in LLM observability?
3. Define the three drift types affecting RAG.
4. Name two open-weight hallucination detection models.
5. What does "eval-as-CI" mean operationally?

## Apply

6. You're picking an LLM observability tool for a team that already uses Datadog for everything else. What's the simplest approach?
7. Outline a tiered approach to running RAG evals in CI without spending $100/PR.
8. You're starting drift monitoring from scratch. What's the minimum viable instrumentation?

## Diagnose

9. Your held-out eval recall@10 has been stable for 6 months at 0.88. Last week it dropped to 0.79 and stayed there. Three diagnostic steps in priority order.
10. p95 latency is up 30% with no code changes. Walk through the trace fields you'd inspect.

## Defend

11. Argue why "every span instrumented" isn't optional, even for a small team.
12. Defend versioning your eval set the same way you version code.

---

## Answer key

<details>
<summary>Click to reveal</summary>

1. Any 5: trace_id, query text (PII-aware), embedder version, retrieved doc_ids + scores, reranker version + ms, prompt token count, generated tokens + finish reason, total cost, total ms, user feedback (when received), hallucination score (when computed).
2. Vendor-neutral standard for tracing; defines GenAI semantic conventions (model, tokens, cost). Most modern observability platforms (Phoenix, Langfuse, Comet Opik) accept OTLP traces. Instrument once, port across vendors.
3. **Model drift** — same text produces different embeddings over time (provider silent updates or upgrade). **Corpus drift** — KB content changes (added, deleted, updated). **Query drift** — users ask about new things, use new vocabulary.
4. **Patronus Lynx (8B / 70B)** — Llama-3 fine-tune. **Vectara HHEM-2.1-Open** — cross-encoder, runs on consumer GPU.
5. Evals run automatically in CI on every PR; failed evals block merges; eval set is versioned alongside code; production failures get added to the eval set.
6. Datadog has LLM Observability that bolts onto existing APM dashboards/alerts. Minimal new tooling. If you want OSS / vendor neutrality later, instrument with OpenTelemetry GenAI semconv so you can add a tool like Phoenix/Langfuse alongside without re-instrumenting.
7. **Static checks + smoke evals** ($0.50 / PR, 30 examples). **Cache judge calls** keyed on (claim_text, context_hash, judge_version) — typically >80% hit rate on stable evals. **Tiered judges**: cheap (Lynx-8B, GPT-4o-mini) on hot path, expensive (Opus, GPT-4) nightly. **Sampling:** 50/500 per PR, full 500 nightly. **Deterministic structural checks** for free (regex, "must contain X").
8. (a) Held-out eval set: 200 (query, golden_doc_id) pairs; run weekly; track recall@k. (b) Fingerprint set: 1000 representative texts; embed weekly; track cosine drift vs. prior week and nearest-neighbor stability. (c) Production telemetry: distribution of top-1 retrieved cosine similarity; refusal rate; per-stage latency.
9. (a) Did the corpus change? Check ingestion logs for that week — large delete? mass update? (b) Did the embedder change? Compare a fingerprint set's vectors week-over-week. (c) Did query distribution shift? Cluster the week's queries; flag emergent topics. The most likely culprit in stable systems is a corpus event; in churning ones, embedder.
10. (a) Per-stage `ms` in trace: which stage shifted? (b) For the slow stage, check `model` and `version` fields — was a model auto-updated? (c) Check input sizes — did prompt tokens grow? (d) Check error/retry counts — provider rate-limiting? (e) Compare same trace fields on faster traces from prior week to localize.
11. Without instrumented spans, you can't answer "why did this query produce this answer." Every customer escalation becomes archaeology. The cost of instrumentation is hours; the cost of one un-debuggable production incident is days plus credibility. Particularly cheap with OpenTelemetry — auto-instrumentation libraries cover most stacks.
12. (a) An unversioned eval set means "Ragas 0.85" today and "Ragas 0.85" next month aren't comparable — the set may have changed. (b) Rollbacks need both code and eval at the right version. (c) Audit / compliance trails require reproducibility. (d) Splitting eval improvements from pipeline improvements requires versioned baselines. The discipline is identical to versioning code: tags, immutable references, CI integration.

</details>
