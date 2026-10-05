# Quiz — Module 20 (Production Engineering)

## Recall

1. Above what monthly spend does self-hosting typically beat managed services?
2. Why is **vLLM** the production default for self-hosted LLM serving?
3. The biggest cost lever in a typical RAG product, ordered by typical impact.
4. What invariant must the semantic response cache maintain to avoid stale answers?

## Apply

5. Outline a Kubernetes deployment for a 10B-token-month workload (cost-driven, not compliance-driven).
6. Your team's monthly LLM bill went from $5K to $80K with no quality changes. Three diagnostics.
7. Pick the right LLM serving stack: simple deployment / Apache 2.0 license / OpenAI-compatible API.

## Diagnose

8. Your self-hosted vLLM pods crash under load. CPU is fine, GPU memory is at 60%. What's likely wrong?
9. Cache hit rate is 5% on a customer-support workload that should have 30%+. What's likely wrong?

## Defend

10. Argue why "queue depth" is the right autoscaling signal for LLM workloads.
11. Defend the operational complexity of dependency-aware cache invalidation over simple TTL.

---

## Answer key

<details>
<summary>Click to reveal</summary>

1. **>$10K/month** on managed APIs OR **>10B embedding tokens/month** OR strict compliance requiring on-prem. Below that, ops cost eats the savings.
2. (a) OpenAI-compatible API out of the box. (b) Apache 2.0 license — no commercial restrictions. (c) PagedAttention / chunked prefill — production-grade throughput. (d) Continuous batching. (e) Broad model compatibility. (f) Active community + enterprise support options. TGI is viable but losing share; SGLang is newer / smaller community.
3. (a) **Right-size LLM** (Sonnet → Haiku saves ~80%). (b) **Prompt caching** (provider-side, 70-90% reduction). (c) **Trim context** — kill irrelevant retrieved chunks (30-60% reduction). (d) **Semantic response cache** (30-50% hit rate cuts proportionally). (e) **Right-size embedder** (small variant 6× cheaper). (f) **Batch where possible**.
4. The cache must track **which retrieved chunks supported the cached answer** AND their versions. When any of those chunks change, the cached entry must be invalidated. TTL-only is insufficient for correctness in stale-sensitive domains.
5. (a) GPU node pool with `nvidia.com/gpu` taint + tolerations. (b) vLLM serving the LLM (1-2 replicas of L40s/A100/H100). (c) Smaller embedder serving via vLLM on commodity GPUs. (d) Qdrant or Milvus for vector store on CPU nodes. (e) KEDA-based autoscaling on queue depth (Prometheus). (f) Pod disruption budgets, topology spread. (g) OTel collector → Langfuse for observability. (h) Per-tenant rate limits at the API gateway.
6. (a) **Token usage by feature/user/prompt-version** — find the new cost driver. (b) **Cache hit rate** — did caching break? (c) **Average context length** — did retrieved-chunk count grow? (d) **Model distribution** — is everything routed to expensive models? (e) **Recent code changes** — what shipped in the cost-spike window?
7. **vLLM.** Apache 2.0 license. OpenAI-compatible API. Easy K8s deployment. Production-proven. Default 2026 choice.
8. **OOM via input length spikes.** A long prompt (e.g., 100K context due to oversized retrieval) blows past safe memory. GPU memory at 60% on average masks tail-spikes. Fix: cap input tokens per request; KV cache pressure-test; lower max-batch-size to leave headroom.
9. (a) Threshold for semantic cache hit too strict (e.g., 0.99 cosine — cache rarely hits). (b) Cache TTL too short — entries expire before reuse. (c) Personalization tokens injected into queries break cache identity. (d) Each session generates uniquely formatted queries that don't cluster.
10. CPU isn't busy during LLM inference (GPU is). What matters is "how many requests are waiting to start?" That's queue depth. Autoscaling on CPU is uncorrelated; on GPU utilization, it lags (already saturated when you scale). Queue depth is the leading signal — autoscale before queueing impacts latency.
11. (a) Healthcare/financial: stale answers are unacceptable risk. (b) TTL-based invalidation accepts staleness up to TTL — operationally simple but gives wrong answers within window. (c) Dependency-aware tracking (cache → supporting chunks → invalidate on chunk change) is correctness-preserving. (d) The complexity is one-time engineering vs ongoing risk. (e) Compliance audit: "show me you served the latest information" is much easier with dependency tracking. The TTL approach saves a few weeks of engineering for years of "is the bot serving stale data?" investigations.

</details>
