# Quiz 04 — Model Deployment (Domain 4, 12%)

> ~17 questions covering batch / streaming / real-time inference patterns, `mlflow.pyfunc.spark_udf`, `fe.score_batch`, DLT streaming inference, Model Serving endpoints, traffic splits.
>
> Take cold. Budget ~32 minutes (17 × 1m 52s).

---

## Recall

1. The three model-serving patterns the exam contrasts: **batch**, **____**, and **real-time**.
2. The MLflow function that turns any registered model into a Spark UDF for batch inference: `mlflow.pyfunc.____(spark, model_uri)`.
3. The Feature Engineering Client's batch-scoring helper that automatically performs feature lookups: `fe.____(model_uri, df)`.
4. The streaming inference framework Databricks recommends for elastic event-stream throughput: **____** (formerly DLT, now branded Lakeflow Declarative Pipelines).
5. The HTTP path to query a Model Serving endpoint: `POST /serving-endpoints/{name}/____`.
6. Traffic percentages across served entities in one endpoint must sum to **____**.

## Apply

7. You have a Spark ML `PipelineModel` registered in UC. What's the most efficient way to apply it to a Spark DataFrame for batch scoring?
8. Same model, but it's a sklearn pipeline (not Spark ML). What's the most efficient call now?
9. The model was logged via `fe.log_model(... training_set=ts ...)`. To batch-score new rows given only the primary keys, which method?
10. Construct the request body to query a churn endpoint with three records: `{age: 35, income: 50000}`, `{age: 42, income: 75000}`, `{age: 28, income: 32000}`.
11. The product team wants 95% of traffic on model v3 and 5% on v4 for a canary. Sketch the `traffic_config`.
12. You need to deploy a model where the cluster's Python version doesn't match the training environment. What `env_manager` should `spark_udf` use?

## Diagnose

13. The scenario: "20,000 sensor events per second, predictions needed within seconds of arrival." A teammate proposes Model Serving. Argue against.
14. Your endpoint's first request after 2 hours of idle takes 50 seconds; subsequent requests are 80ms. Diagnose and propose a fix.
15. The endpoint config validation rejects `routes=[{v3: 60}, {v4: 50}]` with "invalid traffic percentages." Diagnose.

## Defend

16. Defend the choice of `fe.score_batch` over `mlflow.pyfunc.spark_udf` for a model that consumes UC feature tables.
17. Argue why Model Serving endpoints are NOT appropriate for batch scoring 10M rows nightly.

---

## Answers

1. **Streaming**.
2. `mlflow.pyfunc.spark_udf(spark, model_uri, env_manager="virtualenv")`.
3. `fe.score_batch(model_uri, df)`.
4. **DLT** (Delta Live Tables / Lakeflow Declarative Pipelines).
5. `/invocations`.
6. **100** (exactly).
7. **`mlflow.spark.load_model(uri).transform(df)`** — native Spark ML transform. No UDF overhead, no Python boundary, no model load per worker.
8. **`mlflow.pyfunc.spark_udf(spark, model_uri).withColumn(...)`** over the DataFrame. sklearn models can't natively transform Spark DataFrames; the UDF wraps them.
9. **`fe.score_batch(model_uri="models:/...@champion", df=lookup_df)`** — auto feature lookups from the UC feature tables.
10. ```json
    {
      "dataframe_records": [
        {"age": 35, "income": 50000},
        {"age": 42, "income": 75000},
        {"age": 28, "income": 32000}
      ]
    }
    ```
11. ```python
    TrafficConfig(routes=[
        Route(served_model_name="churn-v3", traffic_percentage=95),
        Route(served_model_name="churn-v4", traffic_percentage=5),
    ])
    ```
12. **`env_manager="virtualenv"`** (or `"conda"`). This creates an isolated environment on each worker that matches the dependencies logged with the model. `"local"` would use the cluster's Python and likely produce wrong predictions or errors.
13. Model Serving is per-request HTTP. 20,000 events/sec = 20,000 HTTP calls/sec — wasteful, expensive, and architecturally wrong. The right answer is **DLT (or Structured Streaming) with the model wrapped in a Spark UDF**, processing events in micro-batches. DLT elastically scales the cluster; Model Serving doesn't elastic-scale to streams.
14. **Cold start.** `scale_to_zero_enabled=True` shut down workers during idle. The first request had to spin up a worker, load the model, and warm caches (~30-60s). Fixes: (a) Disable scale-to-zero for production. (b) Reduce the idle-timeout window. (c) Keep a periodic synthetic request firing to keep the endpoint warm.
15. Traffic percentages must **sum to exactly 100**. 60+50=110. Adjust to `[{v3: 95}, {v4: 5}]` or similar that sums to 100.
16. (a) **Automatic feature lookups** — scoring code only needs primary keys, not the full feature schema. (b) **Schema drift safety** — when feature tables evolve, `fe.score_batch` uses the model's logged lookup spec, ensuring training-scoring parity. (c) **No manual joining code** — fewer lines, fewer bugs, easier to maintain. (d) **Lineage** — UC tracks the lookups in lineage graphs automatically.
17. Model Serving is sized for per-request workloads, not bulk. (a) Throwing 10M HTTP requests would exceed any sensible rate limit. (b) Per-request cost is much higher than batch compute. (c) Latency overhead per request (~50-100ms) × 10M rows = days of wall-clock time. (d) Batch UDFs process in parallel on Spark, finishing in minutes. The right tool for batch is `mlflow.pyfunc.spark_udf` or `fe.score_batch` writing to a Delta table.
