# Quiz 02 — MLOps (Section 2, ~43%)

> Covers modules **07-13**: UC model registry lifecycle, DABs, CI/CD with DABs + GitHub Actions, Lakehouse Monitoring, drift detection, model governance, inference tables.
>
> **76 questions** — Recall (23) / Apply (30) / Diagnose (15) / Defend (8). Largest section of the exam — slow read. ~30% of this quiz is monitoring/drift (the biggest single objective cluster).
>
> All questions are **ORIGINAL** — written from the verbatim Sept 30 2025 exam objectives. No NDA content.

---

## Recall (Qs 1-23)

1. Name the three Lakehouse Monitoring profile types.
2. Which Lakehouse Monitoring profile is automatically suited for tables produced by Model Serving inference tables?
3. Which two Delta tables does Lakehouse Monitoring write as outputs of a monitor?
4. Name the four canonical UC model aliases used by the deploy-code lifecycle.
5. Which MLflow client method sets an alias on a registered model version?
6. Which legacy-registry method is the deprecated counterpart to setting a UC alias?
7. Which statistical test does Lakehouse Monitoring use for numerical drift by default?
8. Which statistical test does Lakehouse Monitoring use for categorical drift?
9. Which statistical test, bounded in `[0, log 2]`, is symmetric and works on binned numerical or categorical distributions?
10. Which DAB CLI command validates a `databricks.yml` file before deployment?
11. Which DAB CLI command deploys a bundle to a named target (e.g., prod)?
12. Which DAB CLI command runs a named job within a deployed bundle?
13. Name the four kinds of resources commonly declared inside `resources:` of a `databricks.yml` for an ML project.
14. What is the canonical promotion pattern: a model version with a `@challenger` alias is promoted to which alias upon passing tests?
15. Which Databricks construct auto-logs every request and response on a Model Serving endpoint into a Delta table?
16. Which drift type **cannot be detected from features alone** and requires labels?
17. Which drift type changes `P(Y)` over time (e.g., fraud rate rising 2× during holidays)?
18. Which drift type changes `P(X)` while `P(Y|X)` is unchanged (e.g., new customer demographics)?
19. Which drift type changes `P(Ŷ)` (model output distribution) — useful as an early-warning signal that doesn't require labels?
20. Which Lakehouse Monitoring concept lets you compute drift metrics per slice (e.g., per region, per device class)?
21. What is the "baseline" of a monitor and where is it usually sourced from?
22. Which Databricks SQL construct fires alerting (email / Slack) when a `_drift_metrics` row exceeds a threshold?
23. Which file in a DAB project declares per-environment config (catalog, host, mode)?

## Apply (Qs 24-53)

24. You're configuring a `TimeSeries` monitor on a table that has a `prediction_ts` timestamp column. List the three mandatory configuration fields.

25. You want to roll back from version 47 (currently `@champion`) to version 45 (the previous champion). Provide the **exact** two `MlflowClient` calls in order.

26. You're writing a DAB `databricks.yml` to register an MLflow experiment + a UC registered model + a job that runs `train.py` on a job cluster. Sketch the `resources:` block.

27. You need to detect drift on a continuous feature `transaction_amount` and a categorical feature `merchant_category`. Which two statistical tests does Lakehouse Monitoring run, and what triggers an alert?

28. You want a monitor to detect drift between this week's inference logs and a fixed baseline (last quarter's golden traffic). Which profile type, and how is the baseline registered?

29. Your serving endpoint logs requests/responses to an inference table `prod.ml.churn_inference`. Ground-truth labels arrive 7 days later. Sketch the join SQL that produces `(prediction_ts, prediction, label)` rows for model-performance monitoring.

30. You want a CI workflow on PR merge to `main` to: validate bundle, run unit tests, deploy bundle to staging, run integration tests. Sketch the YAML structure (high-level steps, 5-6 bullets) of the GitHub Actions job.

31. You want to ensure ONLY a service principal can promote a model from `@challenger` to `@champion`. Which UC permission do you grant the SP on the registered model, and which permission do you withhold from data scientists?

32. You're deploying a model serving endpoint via DAB. Sketch the YAML resource block for `model_serving_endpoints` with one served entity at 100% traffic.

33. You want to compute a **custom metric** (e.g., `prediction_business_value = (prediction * 0.85) - 0.10`) inside a Lakehouse Monitoring snapshot monitor. Which monitor configuration argument and what does it produce?

34. The data table has a `prediction` and a `label` column. You want the monitor to compute precision, recall, F1, and AUROC. Which Lakehouse Monitoring profile type computes these automatically, and what argument specifies them?

35. You're alerting on JS divergence > 0.1 for any feature. Sketch the Databricks SQL query against the `_drift_metrics` table that returns features in breach for the last 24h.

36. You want automated retraining triggered when feature drift JS > 0.15 over a 7-day window. Outline the orchestration: which Databricks construct watches the metric, what triggers what, what consumes the new model?

37. You promoted model version 47 to `@champion`. Inference Tables show p95 latency jumped from 80ms to 220ms. What is the rollback procedure that **does not restart** the serving endpoint?

38. You want every model version in `prod.ml.churn` to be tagged with the git commit SHA. Which two MLflow client calls accomplish this?

39. You want to enforce: any model registered under `prod.ml.*` must have a `signature`. Which platform feature already enforces this, and what does the registration call look like if signature is missing?

40. Sketch the YAML target block for `dev`, `staging`, `prod` in a `databricks.yml`, with each target overriding `default_catalog` and `host`.

41. You're designing integration tests for an ML pipeline (feature eng → train → eval → deploy → infer). Which artifact lives where (which environment): unit tests in dev? Integration tests in staging? Smoke tests in prod? Outline the matrix.

42. A `pytest` test in a Databricks notebook imports a helper from `src/features.py`. The notebook can't find the module on the cluster. Which Databricks Repos / Workspace Files mechanism fixes the import path?

43. You want to monitor an endpoint's request rate, error rate, and p99 latency. Which Lakehouse Monitoring objective covers this versus what should be configured at the Model Serving endpoint level?

44. You want to back up the inference table for a regulated workflow. Which UC feature provides the audit trail of when each inference table row was written?

45. Sketch the `InferenceLog` monitor `metrics:` config for model-performance tracking with `label_col="label"`, `prediction_col="pred"`, `problem_type="classification"`.

46. You want to compare current inference distribution to last week's, every day. Which Lakehouse Monitoring profile, and which two arguments configure the comparison window?

47. Your `databricks.yml` references `${var.catalog}`. Where is this variable defined, and how does CI override it for the prod deploy?

48. Which Databricks Asset Bundle target option ensures only specific service principals can deploy / undeploy resources for that target?

49. Sketch the `mlflow.MlflowClient().search_model_versions(...)` call to find all versions of `prod.ml.churn` with the tag `commit_sha` set to a specific value.

50. You want a single Databricks Job to run unit tests + integration tests + deploy bundle. Should this live as one notebook task or three? Justify.

51. Which `databricks.yml` resource type would you use to declare a registered model with a target catalog and schema (and what happens if the catalog doesn't exist)?

52. Inference table size grows 50 GB/day. You want to retain 90 days. What UC / Delta feature manages retention?

53. Outline the three steps of the **deploy-code strategy** (vs deploy-model strategy).

## Diagnose (Qs 54-68)

54. A snapshot monitor on a 100M-row table is taking 3 hours per refresh and incurring large DBU cost. Diagnose the likely causes and three optimizations.

55. A `TimeSeries` monitor reports drift on every refresh, but the team knows nothing has changed. The baseline window is set to "last 30 days" and the comparison window is "last 7 days." What's wrong?

56. A model version was promoted to `@champion` programmatically. The serving endpoint still serves the old version. Diagnose two probable causes.

57. A drift alert fires every hour because the JS divergence on `state_code` hits 0.05 (above threshold 0.04). On manual inspection, the production data is identical to baseline. What might be wrong with the monitor config?

58. A team registers a model via `mlflow.sklearn.log_model(..., registered_model_name="ml.churn")`. UC rejects the registration. Why, and what's the fix?

59. A DAB deploy succeeds but the model serving endpoint is unhealthy. The endpoint logs show `MlflowException: Model version not found`. Diagnose: what's likely missing from the bundle deployment order?

60. The `_drift_metrics` table grew to 800 GB. The monitor has been running daily for 6 months on a wide schema (200 columns). What's the storage culprit and the mitigation?

61. A monitor is configured with `slicing_exprs=["region", "device_type"]` and reports 50× more rows in metrics tables than expected. What is the slicing semantics that the engineer misunderstood?

62. Concept drift is suspected. The team configures a Lakehouse Monitoring InferenceLog monitor with `problem_type="classification"` but leaves `label_col` unset. Why won't this detect concept drift?

63. The CI/CD pipeline deploys a DAB to prod successfully but the registered model version in prod points to dev's MLflow tracking server URI. Diagnose.

64. A monitor's `baseline_table_name` is set to `prod.ml.baseline_v1`. Six months later the team rotates the baseline to `prod.ml.baseline_v2` but old drift metrics still appear in dashboards. Why, and what's the proper rotation process?

65. The team uses `MODEL_VERSION_TRANSITIONED_STAGE` webhooks to trigger CI. In UC-mode workspaces, this webhook event **does not fire**. What's the modern replacement event(s)?

66. An integration test passes in staging but fails in prod with `PermissionError`. The service principal has `USE_CATALOG` and `USE_SCHEMA` but not `EXECUTE` on the registered model. Which UC permissions are missing for *which* operation?

67. A monitor uses an `InferenceLog` profile and the `prediction_col` is auto-logged from Model Serving. The team adds a new model version with a *different* output schema (regression scalar vs prior classification). The monitor breaks. Diagnose the schema-evolution gotcha.

68. The team configures a Databricks SQL alert on a `_drift_metrics` query. The alert never fires despite drift. Diagnose two configuration failure modes.

## Defend (Qs 69-76)

69. Defend the choice of UC **aliases** over legacy registry **stages** for production promotion.

70. Argue against "use GitHub Actions alone to manage ML deployment on Databricks" — defend DABs as the canonical answer.

71. Defend the use of an `InferenceLog` monitor over a `TimeSeries` monitor on the inference table.

72. Argue against trying to detect concept drift from features alone using KS / chi-sq.

73. Defend running drift checks on **prediction outputs** (P(Ŷ)) in addition to features (P(X)).

74. Defend the use of separate `dev`, `staging`, `prod` UC catalogs over a single catalog with `_dev` / `_prod` schemas.

75. Argue for / against using **webhooks** to promote `@challenger` → `@champion` automatically without a human gate.

76. Defend the choice of a **job cluster** (vs all-purpose) for CI-triggered training and validation runs.

---

## Answers (don't peek until done)

1. **Snapshot, TimeSeries, InferenceLog.**
2. **InferenceLog** — designed for the request/response schema with optional `label` join.
3. **`<table>_profile_metrics`** (distribution stats per column) and **`<table>_drift_metrics`** (drift test results per column vs baseline).
4. `@champion`, `@challenger`, `@archived` (and `@baseline` is sometimes used; the first three are canonical).
5. `client.set_registered_model_alias(name, alias, version)`.
6. `client.transition_model_version_stage(name, version, stage)`. > ⚠️ **Exam trap:** This is the **legacy** API. UC = aliases.
7. **Kolmogorov-Smirnov (KS)** test.
8. **Chi-squared** test.
9. **Jensen-Shannon divergence (JS)**.
10. `databricks bundle validate`.
11. `databricks bundle deploy -t prod`.
12. `databricks bundle run -t prod <job_name>`.
13. `experiments`, `registered_models`, `model_serving_endpoints`, `jobs` (and `pipelines` for DLT).
14. `@champion`.
15. **Inference Tables** (enabled on the Model Serving endpoint config — `auto_capture_config`).
16. **Concept drift** — `P(Y|X)` change requires labels.
17. **Label drift** (prior shift).
18. **Feature drift** (covariate shift).
19. **Prediction drift** — observable in inference tables without labels.
20. **Slicing** (`slicing_exprs`).
21. The **baseline table** — usually a fixed historical reference (e.g., the training set used to train the deployed model).
22. **Databricks SQL Alerts** on a saved query against the `_drift_metrics` table.
23. `databricks.yml` itself, with `targets:` overrides; per-target var files can also be referenced.

24. `profile_type=TimeSeries`, `timestamp_col=<ts column>`, `granularities=["1 day", ...]`.
25.
```python
client = MlflowClient()
client.delete_registered_model_alias(name="prod.ml.churn", alias="champion")
client.set_registered_model_alias(name="prod.ml.churn", alias="champion", version=45)
```
(or just call `set_registered_model_alias` — it overwrites — but explicit delete + set is the recommended audit-friendly pattern).

26.
```yaml
resources:
  experiments:
    churn_exp:
      name: /Shared/ml/churn
  registered_models:
    churn_model:
      name: prod.ml.churn
      catalog_name: prod
      schema_name: ml
  jobs:
    train_job:
      name: train-churn
      tasks:
        - task_key: train
          notebook_task: { notebook_path: ./train.py }
          new_cluster: { spark_version: "15.4.x-scala2.12", node_type_id: "i3.xlarge", num_workers: 4 }
```

27. **KS** for `transaction_amount` (continuous), **Chi-squared** for `merchant_category` (categorical). Alert when the test's drift metric (KS statistic or chi-sq stat) exceeds the configured threshold and the p-value falls below alpha.

28. `Snapshot` profile with `baseline_table_name="prod.ml.golden_baseline"`. Snapshot compares the full current table to that baseline each refresh.

29.
```sql
SELECT inf.request_id, inf.prediction_ts, inf.prediction, lbl.label
FROM prod.ml.churn_inference AS inf
LEFT JOIN prod.ml.labels AS lbl
  ON inf.request_id = lbl.request_id
WHERE inf.prediction_ts >= current_date() - INTERVAL 14 DAYS
```
Then compute precision/recall etc on the joined view — and configure the InferenceLog monitor's `label_col` to point at the label.

30. (1) Checkout, (2) install `databricks-cli`, (3) `databricks bundle validate`, (4) `pytest tests/unit/`, (5) `databricks bundle deploy -t staging`, (6) `databricks bundle run -t staging integration_test_job` and gate on exit code.

31. Grant the SP `MANAGE` on the registered model (lets it set aliases). Withhold `MANAGE` from data scientists; grant them only `EXECUTE` (read + use) and `APPLY_TAG` if they need to tag.

32.
```yaml
model_serving_endpoints:
  churn_endpoint:
    name: churn-endpoint
    config:
      served_entities:
        - name: champion
          entity_name: prod.ml.churn
          entity_version: 47
          workload_size: Small
          scale_to_zero_enabled: true
      traffic_config:
        routes:
          - served_model_name: champion
            traffic_percentage: 100
```

33. `custom_metrics=[Metric(type="aggregate", name=..., input_columns=["prediction"], definition="(prediction * 0.85) - 0.10", output_data_type="DOUBLE")]`. Produces an extra column in the `_profile_metrics` table.

34. **InferenceLog** profile. Specify via `problem_type=("classification"|"regression")`, `label_col=<col>`, `prediction_col=<col>`; standard model-performance metrics are computed automatically.

35.
```sql
SELECT column_name, MAX(js_distance) AS max_js
FROM prod.ml.churn_inference_drift_metrics
WHERE window.start >= current_timestamp() - INTERVAL 24 HOURS
GROUP BY column_name
HAVING max_js > 0.1
```

36. A **Databricks Job** scheduled hourly runs a SQL query against `_drift_metrics`. If breach, the same job triggers a downstream training Job (or sets a flag in a table the training Job watches). The training Job retrains, logs new version, sets `@challenger`. A separate gate (test job) promotes `@challenger` → `@champion`. Serving endpoint pinned to `@champion` picks up the new version automatically.

37. `client.set_registered_model_alias("prod.ml.churn", "champion", previous_good_version)`. The endpoint is pinned to `@champion`, so reassigning the alias swaps the served model without an endpoint restart (assumes `entity_version` is left dynamic via alias-pinning; if pinned to a literal version, you need to update the endpoint config).

38.
```python
client.set_model_version_tag("prod.ml.churn", version=47, key="commit_sha", value="abc123")
client.set_registered_model_tag("prod.ml.churn", key="last_promoted_commit", value="abc123")
```

39. UC enforces signature on `log_model` when `registered_model_name=` is a three-level UC name. Without `signature=` (or `input_example=` to infer), the registration raises `MlflowException: Model signature is required for models in Unity Catalog`.

40.
```yaml
targets:
  dev:
    default: true
    workspace: { host: https://dev.databricks.com }
    variables: { catalog: dev }
  staging:
    workspace: { host: https://staging.databricks.com }
    variables: { catalog: staging }
  prod:
    workspace: { host: https://prod.databricks.com }
    variables: { catalog: prod }
    run_as: { service_principal_name: prod-deploy-sp }
```

41. Dev: unit tests + smoke tests (small data). Staging: full integration tests on staging-catalog data, deploy to staging endpoint, run end-to-end. Prod: deployment smoke test (endpoint health, sample inference) only; no test-write to prod tables.

42. Add the repo to the workspace via **Databricks Repos** or **Workspace Files**; then `sys.path.append(...)` to the repo root, or use Repos' automatic path resolution. Notebooks in the same repo can import sibling modules.

43. **Lakehouse Monitoring** monitors the *data and predictions* (drift, performance). **Endpoint-level metrics** (request rate, error rate, p99 latency, CPU, memory) come from Model Serving's built-in monitoring UI / endpoint observability — not Lakehouse Monitoring.

44. The inference table itself is a **Delta table with versioning** — `DESCRIBE HISTORY` shows every write, who wrote, when. Combined with UC audit logs (`system.access.audit`), every write is auditable.

45.
```python
metrics = {
    "prediction_col": "pred",
    "label_col": "label",
    "problem_type": "classification",
}
```
(in the `InferenceLog` profile spec; the monitor auto-computes accuracy, precision, recall, F1, AUROC).

46. **TimeSeries** profile with `granularities=["1 day"]` and a comparison via the baseline rolling window: configure `baseline_table_name=None` (no fixed baseline) and rely on the monitor's automatic window-over-window comparison; or set a separate `baseline_table_name` if a fixed week-ago snapshot is preferred.

47. Defined in `variables:` at the bundle top level (`variables: { catalog: { default: dev } }`) or per-target. CI overrides with `--var "catalog=prod"` on `databricks bundle deploy`, or sets `BUNDLE_VAR_CATALOG=prod` env var.

48. `run_as:` with `service_principal_name:` — only that SP can deploy/run resources in that target. Combine with workspace ACLs on the SP token.

49.
```python
client.search_model_versions(
    filter_string="name = 'prod.ml.churn' and tag.commit_sha = 'abc123'"
)
```

50. **Three tasks** (or three jobs). Separation gives independent retry, independent logs, independent failure isolation. Unit-test failure should not waste integration-test cluster spin-up time; integration failure should NOT auto-deploy. One notebook makes status opaque.

51. `registered_models:` with `catalog_name: prod`, `schema_name: ml`. If the catalog doesn't exist, the bundle deploy fails — DABs do not create catalogs/schemas; provision them via Terraform or out-of-band.

52. **Delta Lake retention** via `VACUUM` (file cleanup) + the inference table's auto-capture config has a retention setting (or use a Lakeflow Job to `DELETE WHERE prediction_ts < current_date() - INTERVAL 90 DAYS` followed by `VACUUM RETAIN 0 HOURS`).

53. (1) Train + register the model in dev. (2) Promote the **code** (DAB) through dev → staging → prod; each env retrains its own model on its own data, registering to its own catalog. (3) Production model is what the prod training job produces — not what dev trained. Contrast: deploy-model strategy ships the dev-trained model object across envs.

54. Wide schema (drift on every column is O(columns)) + full-table snapshot recomputed each run + no slicing budget. Optimizations: limit `slicing_exprs` to ≤ 3, exclude unused columns via the monitor schema, use `TimeSeries` with windowing instead of full snapshot, increase the refresh interval.

55. Baseline window overlaps comparison window. With baseline = "last 30 days" and comparison = "last 7 days," the last 7 days are in BOTH — the test still detects drift in a non-overlapping subset. Fix: baseline should be a fixed reference (e.g., a snapshot of training data) or a non-overlapping window.

56. (a) The endpoint's `entity_version` is pinned to a literal version, not `@champion` alias; you have to update the endpoint config to point at `@champion` or the new version. (b) The endpoint config has a small built-in cache TTL; you must re-deploy / `PATCH` the endpoint to force a refresh. Default behavior: aliases ARE picked up by Model Serving when the endpoint references `@champion`, but if `entity_version` is set explicitly, alias changes are ignored.

57. `state_code` has many low-frequency categories. **Chi-squared is sensitive** to small expected counts; spurious drift shows up. Fix: use **JS divergence** for high-cardinality categorical, or bucket rare states into `OTHER`, or raise the alert threshold.

58. **Two-level name** — UC requires `catalog.schema.model`. Fix: use `dev.ml.churn` (or whatever target catalog).

59. The bundle deployed the model serving endpoint *before* the registered model resource was created / a model version was logged. Fix: deploy order should be `registered_models` → train job (run + log version) → `model_serving_endpoints`. Or split into two bundle deploys.

60. Wide schema (200 cols) × daily drift metrics × 180 days = huge row count. Mitigation: (a) exclude rarely-used columns from the monitor, (b) reduce granularity (weekly instead of daily), (c) `VACUUM` + drop old partitions on the metrics tables, (d) configure metric table retention via Delta `tblproperties`.

61. `slicing_exprs=["region", "device_type"]` produces **the cross product**: each combination (region, device_type) is its own slice — not "drift per region OR per device_type." For 10 regions × 5 devices = 50 slices per metric. Fix: only slice on dimensions that matter for the business decision.

62. `InferenceLog` with `label_col` unset only computes *prediction-distribution drift* (P(Ŷ)), not model performance. Concept drift = P(Y|X) change = requires labels. Without labels, no concept drift signal.

63. The `databricks.yml` target hard-coded `experiment` or `tracking_uri` to the dev workspace. The CI workflow should run `databricks bundle deploy -t prod` *inside the prod workspace context* (CI's `DATABRICKS_HOST` env var must be prod). Check token + host in CI secret store.

64. The `_drift_metrics` table is append-only; old rows from the v1 baseline still exist alongside new rows. Dashboards likely filter by `baseline_version` if available, but if not, old rows appear. Rotation process: (1) name baselines with versioned table names; (2) rebuild the monitor pointing at v2 (`databricks lakehouse-monitoring update`); (3) optionally clear old `_drift_metrics` rows; (4) update dashboard filters.

65. UC does not emit `MODEL_VERSION_TRANSITIONED_STAGE` (no stages in UC). Modern events: `MODEL_VERSION_ALIAS_CREATED`, `MODEL_VERSION_TAG_SET`, `MODEL_VERSION_CREATED` — and/or use the **Jobs as gate** pattern triggered by alias-change rather than webhook.

66. To **load and serve** a model: needs `EXECUTE` on the registered model + `USE_CATALOG`/`USE_SCHEMA` on the containing catalog/schema. To **register a new version**: needs `EXECUTE`+`CREATE_MODEL_VERSION` or `MANAGE`. To **set alias**: needs `MANAGE`. The error suggests serving — grant `EXECUTE`.

67. Monitor schemas are inferred at creation. New version with a different output schema mismatches the inferred schema → monitor fails. Fix: either keep schemas consistent across versions (recommended), or recreate the monitor when schema changes (and accept the loss of historical comparison).

68. (a) The alert query returns 0 rows when drift IS present, because the query's `WHERE` filter is wrong (e.g., filters by `window.start` in a way that misses the latest window). (b) Alert is configured with a too-high threshold (e.g., JS > 1, which never happens since JS is bounded). Or notification channel (Slack webhook, email) is misconfigured.

69. (a) Aliases support **multiple champions** (e.g., regional champions) — stages don't. (b) Aliases are **atomic moves** — no stale "Production" version. (c) Aliases work across UC catalogs uniformly. (d) Audit trail is cleaner: alias-change events are first-class. (e) Stages tie to legacy workspace registry which is sunset in UC-mode workspaces.

70. GitHub Actions alone can't atomically express Databricks resources (endpoints, registered models, jobs, experiments) — you'd need ad-hoc REST calls per resource. DABs declare all ML infra as code + state, support targets, support `validate` before `deploy`, integrate with the Databricks CLI's auth — and the exam explicitly endorses DABs (sample Q8) as the env-promotion answer.

71. `InferenceLog` knows the request/response schema, can join labels, computes model-performance metrics out of the box. `TimeSeries` is a generic timestamp-aware monitor — you'd lose the model-aware metrics (precision, recall, AUROC).

72. Concept drift = `P(Y|X)` change. Without `Y`, no test can distinguish "input distribution changed but Y|X same" (feature drift) from "input distribution same but Y|X changed" (concept drift). Features alone are necessary but not sufficient.

73. Prediction drift is a **leading indicator** — labels arrive late or never; if `P(Ŷ)` shifts, something upstream is changing even if you can't yet measure performance. It also catches data-pipeline bugs (suddenly all predictions are 0.5).

74. Catalog-level separation provides: (a) UC permissions are catalog-scoped — easy to grant prod-only SP access; (b) accidental cross-env writes are impossible; (c) audit + lineage queries naturally segment by env; (d) catalog quotas / storage policies can be set differently. Schema-suffix patterns leak across boundaries.

75. **Against** in regulated industries: HIPAA / SOX / model-risk-management require documented human approval for prod model changes. Webhook auto-promote can be appropriate for: low-risk, observable rollback, well-tested challenger criteria. The standard pattern: webhook triggers tests, tests set `@candidate`, *human gate* promotes `@candidate` → `@champion`.

76. Job clusters are: (a) **cheaper** (lower DBU rate than all-purpose); (b) **ephemeral** — no state leaks between CI runs; (c) **isolated** — each CI run gets a fresh cluster; (d) **audit-friendly** — every run is uniquely identifiable. All-purpose clusters are shared, mutable, and bill at higher rates.
