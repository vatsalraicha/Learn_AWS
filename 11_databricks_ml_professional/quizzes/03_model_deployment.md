# Quiz 03 — Model Deployment (Section 3, ~12%)

> Covers modules **14-16**: Mosaic AI Model Serving (blue-green, canary, served entities, traffic config, scale-to-zero), batch + streaming inference, serving observability.
>
> **21 questions** — Recall (6) / Apply (9) / Diagnose (4) / Defend (2). Smallest section by weight but deep scenarios.
>
> All questions are **ORIGINAL** — written from the verbatim Sept 30 2025 exam objectives. No NDA content.

---

## Recall (Qs 1-6)

1. What is a **served entity** in Mosaic AI Model Serving?
2. Which Model Serving endpoint feature scales replicas down to zero when idle, saving cost?
3. Which deployment strategy uses two endpoints (or two served entities at 0%/100% then a flip) for instant rollback?
4. Which deployment strategy incrementally shifts a small percentage (e.g., 5% → 25% → 50% → 100%) to a new version on **one** endpoint with two served entities?
5. Which MLflow function turns a registered model into a Spark UDF for batch scoring on a Delta table?
6. What three percentiles are most commonly tracked on a serving endpoint for latency SLOs?

## Apply (Qs 7-15)

7. Sketch the `served_entities` + `traffic_config` block for a **canary 90/10** rollout: 90% to the current champion (version 47), 10% to a new challenger (version 48).

8. You need to shift the canary above to 50/50, then 0/100. Outline the two endpoint config updates (what fields change).

9. You want to score a registered model on a 200M-row Delta table with no real-time SLA. Provide the one-line `spark_udf` setup and the `withColumn` invocation.

10. You want to score a streaming source (Kafka → Delta) with model predictions appended per record. Sketch the Structured Streaming pipeline (read → transform with model UDF → write to Delta).

11. You want **blue-green** rollout for a high-risk model change. Outline the two-endpoint setup vs the single-endpoint canary alternative. Which gives faster rollback?

12. Your endpoint is hit at ~500 QPS during business hours and ~5 QPS overnight. Which Model Serving features minimize cost while keeping latency low?

13. You want every endpoint request and response logged for audit. Which Model Serving endpoint config enables this, and where do logs land?

14. The exam's deployment-strategy question presents a high-traffic critical app. Which named strategy is the textbook correct answer, and what's the second-best alternative?

15. Sketch the REST payload (JSON) that updates a serving endpoint to add a new served entity for `prod.ml.churn` version 48 with 10% traffic.

## Diagnose (Qs 16-19)

16. A canary at 10% traffic shows p99 latency 2× the champion's. Diagnose: what should you check before promoting the canary, and what kills a canary?

17. A scale-to-zero endpoint takes 30s to respond after idle. The product team complains. Diagnose: is this a Model Serving bug or expected, and what are two mitigation options?

18. Batch scoring with `mlflow.pyfunc.spark_udf` returns null predictions for 5% of rows. The model registry is healthy. Diagnose two probable causes.

19. The endpoint dashboard shows error rate spiking from 0.1% to 8% after a deploy. The model itself is fine in offline tests. Diagnose: what likely changed in the endpoint config, and what's the rollback step?

## Defend (Qs 20-21)

20. Defend the choice of **canary** over **blue-green** for a critical, high-traffic recommendation endpoint.

21. Argue against "just deploy to 100% — we tested in staging, it's fine" for a model serving change in a regulated workflow.

---

## Answers (don't peek until done)

1. A **served entity** is a specific model version (or other entity, like a foundation model) running on the endpoint. An endpoint can host one or more served entities; `traffic_config` routes requests across them by percentage.

2. **Scale-to-zero** (`scale_to_zero_enabled: true` on the served entity / workload). Cold start cost is paid on the next request.

3. **Blue-green** — two parallel environments; switch all traffic atomically. Rollback = re-point traffic. Cost: 2× during cutover.

4. **Canary** — single endpoint, multiple served entities, gradual traffic shift. Cheaper than blue-green, finer-grained observability, requires a longer observation window. > ⚠️ **Exam trap:** The sample-question textbook answer for "high-traffic critical app" is canary; blue-green is a strong second.

5. `mlflow.pyfunc.spark_udf(spark, model_uri)`.

6. **p50, p95, p99** (median, 95th, 99th).

7.
```yaml
served_entities:
  - name: champion
    entity_name: prod.ml.churn
    entity_version: "47"
    workload_size: Medium
    scale_to_zero_enabled: false
  - name: challenger
    entity_name: prod.ml.churn
    entity_version: "48"
    workload_size: Medium
    scale_to_zero_enabled: false
traffic_config:
  routes:
    - served_model_name: champion
      traffic_percentage: 90
    - served_model_name: challenger
      traffic_percentage: 10
```

8. Step 1 (50/50): update `traffic_config.routes[*].traffic_percentage` to `50` and `50`. Step 2 (0/100): set champion to `0`, challenger to `100`. The `served_entities` block stays unchanged in both steps; only `traffic_config` mutates. After completing, optionally remove the old served entity and rename `challenger` → `champion`.

9.
```python
udf = mlflow.pyfunc.spark_udf(spark, "models:/prod.ml.churn@champion")
spark.read.table("prod.silver.events").withColumn("pred", udf("f1", "f2", "f3")) \
    .write.mode("overwrite").saveAsTable("prod.gold.predictions")
```

10.
```python
udf = mlflow.pyfunc.spark_udf(spark, "models:/prod.ml.churn@champion")
(spark.readStream.format("delta").table("prod.silver.events_stream")
    .withColumn("pred", udf("f1", "f2", "f3"))
    .writeStream.format("delta")
    .option("checkpointLocation", "/tmp/chk_pred")
    .table("prod.gold.predictions_stream"))
```

11. **Blue-green** = two endpoints (`churn-endpoint-blue` + `churn-endpoint-green`) each at 100% traffic on its version. Cut over by re-pointing the application's endpoint URL (or via a router). Rollback = re-point the URL. **Canary** = one endpoint, traffic split. Blue-green has **faster, atomic rollback** (just flip the URL); canary requires re-adjusting traffic percentages but is cheaper and offers finer rollout granularity.

12. **Scale-to-zero** during off-hours + **autoscaling** during business hours (min/max replicas configured). Adds cold-start risk overnight — mitigate by setting `min_provisioned_concurrency` ≥ 1 on the daytime served entity, OR keep one replica warm. **Route Optimization** also reduces per-request latency on high-QPS endpoints.

13. **Auto-capture config** (Inference Tables) on the endpoint: `auto_capture_config={catalog_name, schema_name, table_name_prefix, enabled: true}`. Logs land in a UC Delta table (`<catalog>.<schema>.<prefix>_payload`).

14. **Canary** is the textbook answer for high-traffic critical apps (sample Q7 answer = A). **Blue-green** is the second-best (instant rollback but 2× cost). **Shadow** is best when you want to evaluate against a moving production target without affecting users.

15.
```json
{
  "config": {
    "served_entities": [
      {"name": "champion", "entity_name": "prod.ml.churn", "entity_version": "47", "workload_size": "Medium"},
      {"name": "challenger", "entity_name": "prod.ml.churn", "entity_version": "48", "workload_size": "Medium"}
    ],
    "traffic_config": {"routes": [
      {"served_model_name": "champion", "traffic_percentage": 90},
      {"served_model_name": "challenger", "traffic_percentage": 10}
    ]}
  }
}
```
Sent as `PUT /api/2.0/serving-endpoints/<name>/config`.

16. Check: p50/p95/p99 latency per served entity, error rate per entity, business-metric difference (e.g., CTR delta) if measurable, sample request payloads. A canary should be **killed** if: p99 latency degrades > agreed SLO, error rate exceeds threshold, business metric regresses, or memory/CPU on the canary replicas pegs. Rollback = set traffic_percentage back to 100/0.

17. **Expected** — scale-to-zero by definition means the first request after idle hits a cold replica that must spin up. Mitigations: (a) set `min_provisioned_concurrency: 1` so one replica is always warm; (b) keep `scale_to_zero_enabled: false` for latency-critical endpoints and accept the higher cost; (c) use a synthetic keep-warm ping every 5 min.

18. (a) The features passed to the UDF include nulls and the model's PyFunc `predict` returns null for null inputs without raising. (b) The UDF was created from a model URI pinned to a specific version, but rows are getting served by a different schema (column order mismatch, type coercion failure silently producing nulls). Inspect `df.where("pred IS NULL")` and check input column types vs the model's signature.

19. The deploy likely added a new served entity at 100% traffic without adequate warmup (cold replicas + thundering herd) OR changed `workload_size` and the new size doesn't fit the model in memory (OOM errors). Rollback: revert `traffic_config` to the previous routes (champion at 100%, challenger at 0%) and inspect the challenger's logs. Per CLAUDE.md best practice, this is exactly what canary 10% would have caught before 100% rollout.

20. Canary advantages on a high-traffic recommender: (a) **observability** — you have real production traffic on the new version while champion still serves 90%; (b) **cost** — one endpoint, not two; (c) **finer rollback** — you can hold at 10% indefinitely if metrics are mixed; (d) **business-metric measurement** — A/B comparable at the request level. Blue-green's atomic-flip property matters when you have an emergency rollback need, but at 90/10 traffic the canary is already a partial rollback — you have the lever continuously, not just at flip moments.

21. (a) Staging never has prod's traffic shape — concurrent users, payload diversity, peak QPS, real client retry patterns; (b) Staging usually doesn't have prod's data drift profile; (c) Cold-start behavior differs at scale; (d) Regulated workflows require **demonstrable, gradual exposure** documented for audit — "we tested in staging" is not an audit trail under model-risk-management frameworks. Canary 10% for 24h + automated SLO gates + signed-off promotion is the defensible pattern.
