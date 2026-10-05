# 44 — ⭐ Champion/challenger, shadow, A/B, feature store

> *"Deploying a model to prod is the easy part. Knowing it's better than what's there, with statistical confidence, before flipping traffic — that's the senior pattern."*

## Why this module exists

A new model passing all CI gates is necessary but not sufficient. Production behavior can surprise you (drift, novel input distributions, latency outliers, downstream system interactions). The safe rollout patterns — **shadow → champion/challenger → A/B → full** — are the discipline that catches issues with low blast radius.

---

## 1. The four canonical patterns

| Pattern | What | When | Blast radius |
|---|---|---|---|
| **Shadow** | New model runs in parallel; predictions logged, not returned | Always-on for first 24-72 hours | Zero (no user impact) |
| **Champion/challenger** | Champion = current prod; challenger = new model; small % of traffic to challenger | After shadow signals are clean | Low — controlled % |
| **A/B test** | Split traffic for statistical significance test on business metric | When business metric matters (revenue, click-through) | Medium |
| **Full** | 100% of traffic to new model | After all above clean | High but monitored |

Sequence: every prod model goes through 1→4. Each gate requires explicit approval.

---

## 2. Shadow deployment

Run the new model in parallel with current; log its predictions; don't act on them.

```python
# In your inference service
def predict(request):
    response_v1 = champion_model.predict(request)
    response_v2 = challenger_model.predict(request)   # SHADOW

    # Log for analysis
    log_shadow(
        request=request,
        champion_pred=response_v1,
        challenger_pred=response_v2,
    )

    return response_v1   # User sees champion's response
```

Analyze logs after 24-72h:
- Latency distribution (is challenger slower?)
- Prediction distribution (does challenger hit edge cases the same way?)
- Error rates (does challenger crash on certain inputs?)
- Disagreement rate (when do they differ? on what kinds of inputs?)

Shadow catches: novel input shapes, broken serialization edge cases, dependency issues, latency regression. Zero user impact.

---

## 3. Champion/challenger (and canary)

```python
def predict(request, traffic_split: dict):
    if random.random() < traffic_split["challenger"]:
        response = challenger_model.predict(request)
        log_serving(model="challenger", request=request, response=response)
    else:
        response = champion_model.predict(request)
        log_serving(model="champion", request=request, response=response)
    return response
```

`traffic_split` starts at e.g. 1% challenger; monitor; ramp to 5%, 25%, 50%, then 100%.

For AWS:
- **SageMaker production variants** native support: one endpoint, multiple model variants, each with a weight. Update weights to shift traffic.
- **Lambda** weighted aliases work the same way.
- **EKS / Kong / Envoy / Istio** can do weighted routing.

```python
# SageMaker production variants update
sm.update_endpoint_weights_and_capacities(
    EndpointName="fraud-detector-prod",
    DesiredWeightsAndCapacities=[
        {"VariantName": "champion", "DesiredWeight": 95},
        {"VariantName": "challenger", "DesiredWeight": 5},
    ],
)
```

GitHub Actions workflow:

```yaml
jobs:
  promote-to-canary:
    environment: prod-canary
    steps:
      - run: python scripts/set_weights.py --champion 95 --challenger 5

  observe:
    needs: promote-to-canary
    steps:
      - run: sleep 1800        # bake for 30 min
      - run: python scripts/check_metrics.py --variant challenger --slo-precision 0.85

  ramp:
    needs: observe
    environment: prod
    steps:
      - run: python scripts/set_weights.py --champion 50 --challenger 50

  full:
    needs: ramp
    environment: prod
    steps:
      - run: python scripts/set_weights.py --champion 0 --challenger 100
      # Then: archive champion, rename challenger to champion in next deploy
```

Each environment has its own manual approval (`prod-canary` → 1 approver; `prod` → 2 approvers from different team).

---

## 4. A/B testing (proper experiment)

When the business cares about a downstream metric (revenue, conversion, latency-per-customer-satisfaction-point), do a proper experiment:

- Random 50/50 split, persistent assignment per user
- Sufficient sample size for statistical significance (run sample-size calculator)
- Multi-week duration for novelty effects + weekday seasonality
- Pre-registered hypothesis + metric (no fishing for significance)
- External statistical reviewer (so you don't p-hack)

Tools:
- **GrowthBook** / **Optimizely** / **LaunchDarkly** for experiment platforms
- **Statsig** / **Eppo** for stats-heavy ones
- Custom — use feature flags + analytics

The experiment platform handles the split + sample-size + statistical-significance test. Your job: instrument the metric correctly.

---

## 5. Auto-rollback on regression

Combine champion/challenger with automated alerts → revert:

```python
# Lambda triggered by CloudWatch alarm on challenger metric regression
def lambda_handler(event, context):
    # Alarm fired: challenger p99 latency >100ms (champion: 50ms)
    sm.update_endpoint_weights_and_capacities(
        EndpointName="fraud-detector-prod",
        DesiredWeightsAndCapacities=[
            {"VariantName": "champion", "DesiredWeight": 100},
            {"VariantName": "challenger", "DesiredWeight": 0},
        ],
    )
    notify_slack("Auto-rolled back challenger due to latency regression")
```

For Capital One: this is the prod-grade pattern. Automated rollback within seconds, plus human-driven postmortem. Reduces mean-time-to-recovery dramatically.

---

## 6. Feature store

A **feature store** is a centralized service for ML features:
- Authoritative source for feature definitions
- Online serving (low-latency reads at inference)
- Offline serving (batch retrieval for training)
- Time-travel queries (get feature values as of timestamp T — critical for training)
- Lineage from raw data → features

The point-in-time consistency guarantee is the killer feature: at inference time T, the model gets the feature values that EXISTED at T (not the latest values which might leak future data).

Options:
- **SageMaker Feature Store** (AWS native; integrates with SageMaker Pipelines)
- **Feast** (open source, multi-cloud)
- **Tecton** (commercial, leader in space)
- **Hopsworks** (open source + commercial)

GitHub Actions integration: feature definitions live in repo (`features/fraud.yaml`); CI validates definitions + materializes batch features to S3 / online store.

```yaml
- name: Validate feature definitions
  run: feast validate

- name: Materialize features
  run: |
    feast materialize-incremental $(date -u +%Y-%m-%dT00:00:00)
    feast push-source
```

For Capital One: SageMaker Feature Store likely (AWS native). Feast occasionally for cross-cloud.

---

## 7. The promotion-gate sequence

End-to-end:

```
Train + register (PendingApproval)
   ↓
MRM independent validation
   ↓
Approved in registry
   ↓
Deploy to staging endpoint (auto via env gate)
   ↓
Smoke + load test
   ↓
Deploy as SHADOW to prod (auto)
   ↓
Bake 48 hours; analyze shadow logs
   ↓
Manual approval to CANARY (5%)
   ↓
Bake 24 hours; check SLOs
   ↓
Manual approval to RAMP (50%)
   ↓
Bake 4 hours; check business metric
   ↓
Manual approval to FULL (100%)
   ↓
Archive old champion in registry
```

Each transition is a GitHub Actions workflow job with `environment: <stage>` and required reviewers. Each stage has automated rollback if metrics regress.

---

## 8. Champion/challenger for non-ML services

Same pattern applies to non-ML services (feature flags + traffic routing). The discipline is identical: shadow → canary → ramp → full.

For Capital One pipelines: every prod deploy uses this pattern, ML or not. The published `singular software delivery pipeline` includes canary as a built-in stage.

---

## 9. Common pitfalls

❌ **No shadow phase** — first time the new code/model sees real prod traffic is when 5% of users hit it. Many bugs reveal themselves only in shadow.

❌ **Canary not statistically meaningful** — 5% traffic for 5 minutes gets you noise. Bake long enough for confident comparison.

❌ **No rollback automation** — if rollback requires a human, MTTR > 30 min. With auto-rollback, < 30s.

❌ **Champion forgotten** — after promoting challenger to champion, the old "champion" needs to be archived in registry; otherwise registry fills up with stale versions.

❌ **Feature drift between shadow and prod** — shadow may not see all prod inputs (e.g., rate-limited customers). Validate shadow coverage matches production input distribution.

---

## 10. Cross-references

- The model registry stages → [module 43](43_mlops_mlflow_sagemaker.md).
- Rollback workflows in detail → [module 45](45_mlops_retraining_rollback.md).
- Environment-based deploys (the gating mechanism) → [module 30](30_actions_environments_protection.md).
- Validation gates per model → [module 42](42_mlops_validation_gates.md).
- Topic 04 module 37 (SageMaker Inference) — for the AWS-side details on production variants.
