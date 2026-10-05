# 28 — Cost & scaling: KEDA, deferrable, right-sizing, multi-tenant

## Why this module exists

A typical mid-sized Airflow runs $5-50K/mo. Half of that is usually waste — idle workers, oversized envs, poke-mode sensors. This module is the cost lever set.

---

## 1. The cost levers

| Lever | Saving | Effort |
|---|---|---|
| Switch sensors to `deferrable=True` | 30-70% worker hours | Low |
| KEDA autoscale workers (Celery) | 40-60% baseline | Medium |
| Right-size MWAA env class | 30% | Low |
| `MinWorkers = 1` (vs default higher) | 20% | Low |
| Move heavy work to EMR Serverless / Glue / SageMaker | 50%+ | Medium-high |
| Aggressive log retention | 10-30% CloudWatch cost | Low |
| Disable DEBUG logs | 50% CloudWatch | Low |
| Cosmos with `dbt_manifest` (not file scan) | Lower scheduler load | Low |

---

## 2. Deferrable everywhere = the biggest win

A typical ETL has 10-50 sensors waiting for data. With `mode="poke"` each holds a worker slot for hours. With `deferrable=True` they cost a tiny fraction in the Triggerer.

Real numbers: a shop with 30 hourly sensors-each-waiting-1-hour-with-`poke`-mode = 30 worker slots permanently occupied. Switching to deferrable: 30 sensors managed by a single Triggerer pod.

---

## 3. KEDA on Celery workers

Already covered (module 15). Scale to zero off-hours; scale up on queue depth.

```yaml
# excerpt
minReplicaCount: 0
maxReplicaCount: 20
triggers:
  - type: postgresql
    metadata:
      query: SELECT count(*) FROM task_instance WHERE state='queued'
      targetQueryValue: '4'
```

Saves the night/weekend cost of idle workers.

---

## 4. K8sExecutor right-sizing

Per-task `pod_override`. Don't request 4 CPU + 8GB for tasks that need 0.5 CPU + 512 MB.

For LARGE task envelopes: separate Karpenter pool (cheap CPU vs expensive GPU). Scale on demand.

---

## 5. MWAA cost optimization

- `MinWorkers = 1`.
- `MaxWorkers` tuned to peak DAG concurrency.
- Smallest env class that meets scheduler need.
- Webserver in `PRIVATE_ONLY` doesn't reduce cost but saves NAT egress.
- CloudWatch log retention: 30 days (or whatever compliance allows); export to S3 Glacier for longer.
- Set `WARN` level on `airflow-DAGProcessing` log group (the chattiest).

---

## 6. Composer cost optimization

- Composer 3 with smallest baseline.
- Scale-to-near-zero off-hours.
- CMEK adds cost but is non-negotiable for regulated; ack it.
- Use the cluster outside the customer project mode (reduces customer K8s cost).

---

## 7. Astro cost optimization

- Right-size AU per deployment.
- Pause dev/staging envs when not in use.
- Image-bake DAGs (no git-sync overhead).
- Use Astro's "smart caching" features.

---

## 8. Compute placement

The biggest waste is doing transforms in Airflow:

```python
# COST: pulls 100M rows into worker RAM
df = pd.read_sql("SELECT * FROM huge_table", conn)
df = df.groupby(...).agg(...)
df.to_sql("agg_table", conn)
```

```python
# RIGHT: warehouse does the work
SnowflakeOperator(sql="""
  INSERT INTO agg_table
  SELECT ... FROM huge_table GROUP BY ...
""")
```

Snowflake's compute is way cheaper than your Airflow worker for tabular transforms.

---

## 9. Multi-tenancy patterns

Three approaches:

### 9.1 One Airflow per team

Each team has its own env (MWAA / Astro deployment / K8s namespace).

Pros: complete isolation; per-team cost; per-team upgrade cadence.
Cons: N×ops; idle envs.

### 9.2 One shared Airflow

Single env; namespaces / pools / per-DAG access control / per-task K8s SA.

Pros: cost-efficient; ops once.
Cons: noisy neighbors; harder upgrades; one DAG can stall scheduler for all.

### 9.3 Hybrid

Critical / regulated DAGs on dedicated env; "the rest" on shared.

For Capital One: hybrid is plausible — finance team has dedicated, generic data eng shares.

---

## 10. The architect-grade cost dashboard

- $ per DAG (with cost-allocation tags / labels).
- $ per team.
- Worker utilization (% of slots used).
- Triggerer load (triggers per second).
- Compute placement breakdown — Airflow worker / EMR / Snowflake / Databricks.

For Capital One–style FinOps: Cloud Custodian rule "DAGs without `team` and `cost-center` tags fail policy."

---

## Sanity check

1. Deferrable-everywhere — what's the saving on a typical sensor-heavy DAG?
2. KEDA + Celery — what does scale-to-zero off-hours actually save?
3. The "transform in Python" anti-pattern's cost lever — push transforms to where?
4. One Airflow per team vs one shared — describe trade-offs.
5. Cloud Custodian rule for DAG cost-allocation tagging — what's the policy?

---

## Sources

- [KEDA](https://keda.sh/docs/2.13/scalers/postgresql/)
- [Airflow Helm chart KEDA support](https://airflow.apache.org/docs/helm-chart/stable/keda.html)
- [MWAA pricing optimization](https://docs.aws.amazon.com/mwaa/latest/userguide/mwaa-environment-pricing.html)

→ Next: [29 — Multi-tenancy patterns](29_multi_tenancy.md)
