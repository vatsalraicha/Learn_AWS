# 42 — ⭐🏦 Model validation gates: fairness, bias, drift in CI/CD

> *"For a bank model, accuracy isn't enough. Fairness across protected groups, bias against the regulated attributes, drift between training and prod — each is a required status check before deploy."*

## Why this module exists

SR 11-7 (see [module 37](37_compliance_sr117_audit.md)) requires every material model to pass independent validation before reaching production. At Capital One, fair-lending laws (ECOA, Reg B) add legal requirements around protected attributes (race, gender, age, etc.). This module covers how to encode these checks as required status checks in CI/CD.

---

## 1. The three validation dimensions

| Dimension | Question | Tooling |
|---|---|---|
| **Performance** | Does the model meet accuracy/precision/recall targets? | pytest assertions on metrics |
| **Fairness** | Does the model perform equally across protected groups? | aif360, fairlearn, evidently |
| **Drift** | Has the production data distribution shifted from training data? | evidently, NannyML, river, SageMaker Model Monitor |
| **Explainability** | Can we explain individual predictions? (SR 11-7 + ECOA adverse-action) | SHAP, LIME, integrated gradients |

For a fraud model: all four matter. For a recommendations model: fairness + drift matter most.

---

## 2. Fairness — the metrics

The big three (definitions vary by source; these are standard):

| Metric | Formula | What it means |
|---|---|---|
| **Demographic parity** | P(ŷ=1 \| A=0) = P(ŷ=1 \| A=1) | Approval rate equal across groups |
| **Equal opportunity** | P(ŷ=1 \| Y=1, A=0) = P(ŷ=1 \| Y=1, A=1) | Among true positives, approval rate equal |
| **Disparate impact** | P(ŷ=1 \| A=0) / P(ŷ=1 \| A=1) | Should be ≥0.8 (4/5ths rule) — US legal guideline |
| **Equalized odds** | Equal TPR AND equal FPR across groups | Strongest fairness criterion |

These metrics are mathematically incompatible (you can't satisfy all four simultaneously except in trivial cases) — the model owner must declare which to optimize for, with regulatory + business sign-off.

For lending models: **disparate impact ≥0.8** is the 4/5ths-rule threshold from the EEOC's Uniform Guidelines (1978). Equal opportunity is preferred when ground truth is available.

---

## 3. Fairness check in CI

```python
# scripts/validate_fairness.py
import json
import sys
import pandas as pd
from fairlearn.metrics import demographic_parity_ratio, equalized_odds_ratio, MetricFrame
from sklearn.metrics import recall_score, false_positive_rate
import joblib

def main(model_path: str, eval_path: str, protected_attrs: list, output_path: str) -> int:
    model = joblib.load(model_path)
    df = pd.read_parquet(eval_path)

    X = df.drop(columns=["is_fraud"] + protected_attrs)
    y = df["is_fraud"]
    y_pred = model.predict(X)

    results = {"passed": True, "checks": []}

    for attr in protected_attrs:
        a = df[attr]

        dpr = demographic_parity_ratio(y, y_pred, sensitive_features=a)
        eor = equalized_odds_ratio(y, y_pred, sensitive_features=a)

        results["checks"].append({
            "attribute": attr,
            "demographic_parity_ratio": dpr,
            "equalized_odds_ratio": eor,
            "threshold_dpr": 0.80,
            "threshold_eor": 0.80,
            "passed": dpr >= 0.80 and eor >= 0.80,
        })

    results["passed"] = all(c["passed"] for c in results["checks"])

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(json.dumps(results, indent=2))
    return 0 if results["passed"] else 1

if __name__ == "__main__":
    sys.exit(main(
        model_path=sys.argv[1],
        eval_path=sys.argv[2],
        protected_attrs=sys.argv[3].split(","),
        output_path=sys.argv[4],
    ))
```

In the workflow:

```yaml
- name: Fairness check
  run: |
    python scripts/validate_fairness.py \
      models/checkpoint.pkl \
      data/eval.parquet \
      age,gender,race \
      fairness-report.json

- uses: actions/upload-artifact@v4
  with: { name: fairness-report, path: fairness-report.json }
```

If `validate_fairness.py` exits non-zero, the step fails → CI fails → PR can't merge (with branch protection requiring this check).

---

## 4. Drift detection

Drift = "the data your model sees in prod is statistically different from what it was trained on." Causes model performance to degrade silently.

Two kinds:
- **Covariate drift**: input distribution changes. (e.g., transaction amounts shifted post-inflation.)
- **Concept drift**: relationship between input and output changes. (e.g., fraud patterns evolve.)

```python
# scripts/detect_drift.py
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, TargetDriftPreset
import pandas as pd

reference = pd.read_parquet("data/training_distribution.parquet")
current = pd.read_parquet("data/production_sample.parquet")

report = Report(metrics=[DataDriftPreset(), TargetDriftPreset()])
report.run(reference_data=reference, current_data=current)
report.save_html("drift-report.html")
result = report.as_dict()

# Fail if too many features drifted
drift_share = result["metrics"][0]["result"]["dataset_drift"]
n_drifted = sum(1 for f in result["metrics"][0]["result"]["drift_by_columns"].values() if f["drift_detected"])

if n_drifted > 3 or drift_share:
    print(f"DRIFT DETECTED: {n_drifted} features drifted")
    exit(1)
```

In production: continuous drift monitoring via SageMaker Model Monitor or self-hosted evidently. Alerts to model-on-call.

In CI: pre-deploy check that the training data hasn't drifted vs the previous training data (catches data-pipeline regressions).

---

## 5. The full pre-merge model gate

```yaml
jobs:
  model-validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -e ".[dev,train]"

      # Train on small validation dataset
      - name: Train baseline
        run: python -m my_pkg.training.train --config configs/validation.yaml --output /tmp/model.pkl

      # Performance gate
      - name: Performance check
        run: |
          python scripts/validate_performance.py /tmp/model.pkl data/eval.parquet performance.json
          python -c "
          import json
          d = json.load(open('performance.json'))
          assert d['auc'] >= 0.85, f\"AUC regressed: {d['auc']}\"
          assert d['precision_at_recall_50'] >= 0.7
          "

      # Fairness gate
      - name: Fairness check
        run: |
          python scripts/validate_fairness.py /tmp/model.pkl data/eval.parquet age,gender,race fairness.json
          python -c "
          import json
          d = json.load(open('fairness.json'))
          assert d['passed'], 'Fairness gate failed'
          "

      # Drift gate
      - name: Drift check
        run: python scripts/detect_drift.py

      # Explainability gate (sample sanity)
      - name: SHAP sanity
        run: |
          python scripts/sanity_shap.py /tmp/model.pkl data/eval.parquet

      # Upload reports
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: model-validation-reports
          path: |
            performance.json
            fairness.json
            drift-report.html

      # Post summary to PR
      - name: PR comment with results
        if: github.event_name == 'pull_request'
        uses: marocchino/sticky-pull-request-comment@v2
        with:
          message: |
            ## Model validation results
            - AUC: ${{ steps.perf.outputs.auc }} (threshold: 0.85)
            - Fairness DPR (age, gender, race): all passed (threshold: 0.80)
            - Drift detected: no
            - SHAP sanity: passed
            See artifacts for full reports.
```

Required status check `model-validation` on branch protection: PR can't merge if any of these gate.

---

## 6. The independent-validation gate (SR 11-7 2L)

The CI gates above are 1L self-checks. The 2L gate is independent — MRM team reviews the model BEFORE production deploy.

Pattern: SageMaker Model Registry promotion gate.

1. Training pipeline → model registered as `PendingApproval` in registry.
2. MRM team gets notified (Slack, email, ServiceNow ticket).
3. MRM runs their own validation suite (different code, different fixtures, often different team).
4. MRM approves or rejects in registry.
5. CD workflow watches for `Approved` status → deploys.

This is the **separation-of-duties** mechanism for model deployment. Implementation in [module 43](43_mlops_mlflow_sagemaker.md).

---

## 7. Adverse-action explainability (ECOA / Reg B)

For credit decisions, the lender must provide a reason for denial. The model must support generating per-decision explanations.

SHAP (SHapley Additive exPlanations) is the standard:

```python
import shap
import joblib

model = joblib.load("model.pkl")
explainer = shap.TreeExplainer(model)

# Per-decision explanation
for sample_id, sample in test_set.iterrows():
    shap_values = explainer.shap_values(sample)
    top_drivers = sorted(zip(feature_names, shap_values), key=lambda x: abs(x[1]), reverse=True)[:5]
    print(f"Decision for {sample_id}: top drivers: {top_drivers}")
```

In CI: sanity-check that SHAP values are computable on sample data. In prod: at every adverse decision, log + return top-K SHAP drivers in the structured response.

For neural network models: integrated gradients, LIME, or Anchors instead of SHAP.

---

## 8. The MLflow integration

MLflow tracks every experiment + every metric. CI can:

```yaml
- name: Log experiment to MLflow
  run: |
    mlflow run . -P config=configs/validation.yaml --env-manager=local
    # Logs metrics, params, artifacts to MLflow tracking server
  env:
    MLFLOW_TRACKING_URI: ${{ vars.MLFLOW_URI }}
    MLFLOW_EXPERIMENT_NAME: "ci-validation"
```

MLflow becomes the single source of truth for every model version's metrics — accessible by 1L, 2L, 3L. Auditors look here.

---

## 9. Model card auto-generation

After training + validation, generate a model card:

```python
from huggingface_hub import ModelCard

card = ModelCard.from_template(
    template_path="MODEL_CARD_TEMPLATE.md",
    model_id="my-fraud-detector-v3",
    auc=metrics["auc"],
    fairness_dpr=fairness["demographic_parity_ratio"],
    commit_sha=os.environ["GITHUB_SHA"],
    training_data_id=data_version_id,
    ...
)
card.save("MODEL_CARD.md")
```

Commit `MODEL_CARD.md` (or attach to model registry entry) so MRM has the documentation ready.

---

## 10. Cross-references

- SR 11-7 framing → [module 37](37_compliance_sr117_audit.md).
- MLflow + SageMaker Model Registry promotion gate → [module 43](43_mlops_mlflow_sagemaker.md).
- Champion/challenger + shadow for live testing → [module 44](44_mlops_champion_challenger.md).
- Rollback workflow when prod drift detected → [module 45](45_mlops_retraining_rollback.md).
- Environment manual approval as the 2L gate → [module 30](30_actions_environments_protection.md).
