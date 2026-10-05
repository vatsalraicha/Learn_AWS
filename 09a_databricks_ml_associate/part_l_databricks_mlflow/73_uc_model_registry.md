# Chapter 73 — UC Model Registry, Aliases, and the Legacy-Stages Migration

> **Goal of this chapter:** to teach you the Unity Catalog Model Registry — what a registered model is, how versions and aliases work, how promotion happens, and what the legacy "stages" world looked like and why it's gone. By the end you should be able to register a trained model, tag a version, set a champion alias, load by alias, swap the champion atomically, and describe the differences between the legacy workspace registry and the UC registry as the exam tests them. You should also know enough about Mosaic AI Model Serving to recognize it as the production-serving layer that sits on top of the registry, even though the deep serving APIs are out of scope for the Associate exam.

In Ch 72 we built the discipline of tracking runs. A run is the *training* artifact. The registry is the *promotion* artifact — the layer above the run, where a model gets a stable name, gets versions, gets governance, and ultimately serves traffic. The two layers are independent on purpose: every registered model points to a tracked run, but most tracked runs never become registered models. Only the ones you want to use go through the registry.

---

## 73.1 The motivating story — three models named churn_final.pkl

The data science team has trained 87 churn-prediction models over six months. The current production endpoint loads a pickle from `/dbfs/models/churn_final.pkl`. The on-call engineer pages the team at 2am: "the model returns garbage on a particular input shape." The team starts investigating.

What version of the model is in production? Whatever was written to `churn_final.pkl` "the last time we deployed." When? Nobody is sure. Which notebook produced it? They check git. Two notebooks were modified that week.

What happens if they roll back? They'd need to re-train the previous model from the previous data, because no one saved a copy. They could try yesterday's pickle backup — but the schema changed three weeks ago and yesterday's model has different feature columns. The rollback is a multi-day project.

This is the situation the **Model Registry** exists to prevent. A registered model has:

1. **A stable name** (`prod.churn.rf_model`) that doesn't change as new versions arrive.
2. **Versioned, immutable model artifacts** (`v1`, `v2`, `v3` — you never overwrite a version, only add new ones).
3. **Aliases** (`@champion`, `@challenger`) that point to a specific version; aliases move, versions don't.
4. **Lineage** back to the run that trained each version, the data it used, the user who registered it.
5. **Permissions** in UC: who can deploy, who can roll back, who can even see the model exists.

Loading by alias (`models:/prod.churn.rf_model@champion`) means the serving code never changes when you promote a new version. The endpoint always loads "whatever is champion right now." Promotion is one alias reassignment. Rollback is the same alias reassignment in reverse.

This chapter is the Registry mechanics, the UC-specific aliases-vs-stages story, and the loading pattern for inference.

---

## 73.2 What a registered model is

In UC, a **registered model** is a securable with a 3-level UC name:

```
prod.churn.rf_model
```

Where:

- `prod` — catalog.
- `churn` — schema.
- `rf_model` — the model name.

A registered model has:

- Zero or more **versions** (numbered 1, 2, 3, …). Each version is immutable — once created, its artifact and metadata don't change.
- Zero or more **aliases**, each pointing to exactly one version.
- Tags (per-model and per-version).
- An owner.
- Permissions (via UC grants).
- An MLflow lineage pointer per version — the run_id that produced the artifact.

The registered model itself does not contain the model artifact directly. Versions contain artifacts. The registered model is the *name* and the *governance shell*.

---

## 73.3 Registering a model

Two common paths.

### 73.3.1 Path A — direct `mlflow.register_model`

After a training run has logged a model artifact, you register it:

```python
import mlflow

# Make sure the registry URI points at UC, not the legacy workspace registry
mlflow.set_registry_uri("databricks-uc")

# Register
result = mlflow.register_model(
    model_uri=f"runs:/{run_id}/model",         # path to the artifact within a run
    name="prod.churn.rf_model",                # 3-level UC name
)
print(f"Registered as version {result.version}")
```

The first time you call this for `prod.churn.rf_model`, it creates v1. Subsequent calls create v2, v3, … — every registration adds a new version.

### 73.3.2 Path B — register at log time

You can register in one step when logging the model:

```python
with mlflow.start_run() as run:
    model.fit(X_train, y_train)
    mlflow.sklearn.log_model(
        model,
        artifact_path="model",
        registered_model_name="prod.churn.rf_model",  # registers automatically
    )
```

Or via `fe.log_model` (Ch 71) when you want to also bake in feature lineage:

```python
fe.log_model(
    model=model,
    artifact_path="model",
    flavor=mlflow.sklearn,
    training_set=training_set,
    registered_model_name="prod.churn.rf_model",
)
```

Both Path A and Path B produce the same result: a new version under the registered model.

### 73.3.3 The signature requirement

UC refuses to register a model whose logged artifact has no signature. So when you log the model, include the signature:

```python
from mlflow.models.signature import infer_signature

sig = infer_signature(X_train, model.predict(X_train))
mlflow.sklearn.log_model(model, "model", signature=sig, input_example=X_train.head(5))
```

If you forget, the `register_model` call fails with `INVALID_PARAMETER_VALUE: Model signature is required`. The fix is to re-log with a signature.

---

## 73.4 Versions are immutable

This is worth saying explicitly because it's a common confusion for people coming from "deploy `model.pkl`, overwrite to update".

Once `prod.churn.rf_model/v3` exists, it points to a specific artifact. You cannot modify v3. You cannot re-train v3 in place. You can:

- Create v4 (a new artifact).
- Tag v3 (tags ARE mutable, separately from the artifact).
- Set an alias to point at v3 or v4 (aliases ARE mutable).
- Delete v3 (administratively — but this is rare and discouraged; better to mark it archived via alias or tag).

The discipline: **versions are immutable, aliases are mutable.** The whole governance model rests on this.

---

## 73.5 Aliases — the modern promotion mechanism

An **alias** is a string label attached to one specific version of a registered model. Common aliases:

- `@champion` — the current production version. By convention.
- `@challenger` — a candidate being evaluated against champion.
- `@dev` — current development version.
- `@archived` — previously-champion versions kept for reference.
- Arbitrary other names — `@regulatory_approved`, `@us_only`, `@experimental` — UC lets you define any string.

A registered model can have many aliases. An alias points to exactly one version. A version can be referenced by many aliases.

### 73.5.1 Setting an alias

```python
from mlflow import MlflowClient
client = MlflowClient()

# Promote v3 to champion
client.set_registered_model_alias(
    name="prod.churn.rf_model",
    alias="champion",
    version=3,
)
```

### 73.5.2 Querying by alias

```python
# Find which version is currently champion
mv = client.get_model_version_by_alias(
    name="prod.churn.rf_model",
    alias="champion",
)
print(f"Champion is version {mv.version}, trained from run {mv.run_id}")
```

### 73.5.3 Deleting / reassigning an alias

To "move" an alias from one version to another, just set it again — it overwrites:

```python
# Promote v4 to champion (was v3 before)
client.set_registered_model_alias(
    name="prod.churn.rf_model",
    alias="champion",
    version=4,
)
```

To delete an alias:

```python
client.delete_registered_model_alias(
    name="prod.churn.rf_model",
    alias="challenger",
)
```

### 73.5.4 The atomic-swap property

Reassigning an alias is atomic. Any caller doing `models:/prod.churn.rf_model@champion` immediately starts seeing the new version on the next load. There's no in-between state where the alias points to nothing.

This is the basis of zero-downtime promotion: the serving endpoint loads `@champion` once per inference (or once per refresh interval); after the alias swap, new lookups see the new version; old in-flight requests using the old version finish naturally.

---

## 73.6 Tags — finer-grained metadata

Tags are key-value strings, separate from aliases. Two kinds:

### 73.6.1 Registered-model tags (per model, not per version)

```python
client.set_registered_model_tag(
    name="prod.churn.rf_model",
    key="owner",
    value="ml-platform-team",
)
client.delete_registered_model_tag(
    name="prod.churn.rf_model",
    key="owner",
)
```

Use for: ownership, business domain, regulatory classifications that apply to the model regardless of version.

### 73.6.2 Model-version tags (per version)

```python
client.set_model_version_tag(
    name="prod.churn.rf_model",
    version=3,
    key="passed_bias_audit",
    value="true",
)
```

Use for: per-version certifications, evaluation results, deployment notes.

Tags are searchable: `client.search_model_versions(filter_string="tags.passed_bias_audit = 'true'")`.

### 73.6.3 Tags vs aliases — when to use which

- **Alias** = "the current X" — a *pointer* that moves over time. There is exactly one current champion at any moment.
- **Tag** = persistent metadata about a specific version or the model. Tags don't move (they can be deleted/re-added but their semantics is "this fact about this object").

A version tagged `passed_bias_audit=true` keeps that tag forever (or until you remove it). An alias `champion` reassigns as the model evolves.

---

## 73.7 The legacy stages story — what you might still encounter

Before UC, MLflow's model registry had **stages**:

- `None` — newly-registered, not yet promoted.
- `Staging` — under evaluation.
- `Production` — currently in production.
- `Archived` — retired.

Transitions:

```python
# LEGACY — workspace registry only
client.transition_model_version_stage(
    name="churn_model",
    version=3,
    stage="Production",
    archive_existing_versions=True,  # auto-archives the previous Production version
)
```

This API still exists for the legacy workspace registry (`mlflow.set_registry_uri("databricks")`). For UC (`databricks-uc`), it does NOT exist — UC raises an error if you try to transition a stage on a UC-registered model.

### 73.7.1 Why stages were retired

Stages were a fixed, opinionated lifecycle: every model had to fit into None / Staging / Production / Archived. Real ML workflows often want more:

- Multiple production versions for different regions or customer tiers.
- A "regulatory_approved" state separate from "production".
- A "shadow" version receiving traffic but not authoritative.
- Per-version certifications without forcing a global state transition.

Aliases generalize stages. You can recreate the stages workflow with aliases (`@champion` = Production, `@candidate` = Staging, `@archived` = Archived) — but you can also have `@us_champion`, `@eu_champion`, `@regulatory_approved`, etc., without inventing new lifecycle states.

### 73.7.2 The exam trap

The exam tests this distinction. A typical question:

*"You have a model registered in UC as `cat.sch.churn_model`. You want to move version 3 to Production. What do you call?"*

The wrong answers — the distractors — include:
- `client.transition_model_version_stage(..., stage="Production")` — this is the legacy API; doesn't work on UC.
- Re-registering the model — unnecessary, doesn't promote.

The right answer:
- `client.set_registered_model_alias(..., alias="champion", version=3)`.

If a question mentions a 3-level model name AND `stage="Production"`, it's almost certainly testing the legacy-vs-UC trap.

### 73.7.3 What happens if you have legacy stages and migrate to UC?

UC doesn't import stages from the workspace registry. When you migrate (or just re-register a model into UC), you start fresh with aliases. The convention most teams adopt:

- Whatever was `Production` in legacy → becomes `@champion` in UC.
- Whatever was `Staging` → becomes `@challenger`.
- `Archived` → either deleted or tagged `archived=true`.

There is no automated migration tool; it's a deliberate cutover.

---

## 73.8 Loading models from the registry

The whole point of the registry is that consumer code references models by their *stable* name, not by run_id or file path.

### 73.8.1 Load by alias (the recommended pattern)

```python
import mlflow.pyfunc

model = mlflow.pyfunc.load_model("models:/prod.churn.rf_model@champion")
predictions = model.predict(input_df)
```

The URI scheme: `models:/<catalog>.<schema>.<name>@<alias>` or `models:/<catalog>.<schema>.<name>/<version>` (specific version) or `models:/<catalog>.<schema>.<name>/latest` (latest version — rarely useful in production).

When you load by alias, you get whichever version is currently aliased. After an alias swap, the next `load_model` returns the new version. No code change.

### 73.8.2 Load with the flavor-specific API

If you want the native model object (not the pyfunc-wrapped version):

```python
import mlflow.sklearn
sklearn_model = mlflow.sklearn.load_model("models:/prod.churn.rf_model@champion")
# Now sklearn_model is the original RandomForestClassifier instance,
# with .predict_proba, .feature_importances_, etc.
```

For Spark models:

```python
import mlflow.spark
spark_model = mlflow.spark.load_model("models:/prod.churn.rf_model@champion")
predictions_df = spark_model.transform(input_spark_df)
```

### 73.8.3 The `score_batch` shortcut for feature-store-aware models

If the model was logged with `fe.log_model` (Ch 71), there's a single-call batch inference:

```python
from databricks.feature_engineering import FeatureEngineeringClient
fe = FeatureEngineeringClient()

predictions = fe.score_batch(
    model_uri="models:/prod.churn.rf_model@champion",
    df=ids_df,
)
```

This does the model load + feature lookup + prediction in one shot, using the feature lineage baked into the model.

---

## 73.9 Permissions on registered models

A registered model is a UC securable. The privilege list (Ch 70):

| Privilege | What it allows |
|---|---|
| `EXECUTE` | Load the model, call predict (the consumer's grant). |
| `MODIFY` | Add versions, set/delete aliases, set tags. |
| `OWNERSHIP` | Full control; transfer ownership. |
| `ALL PRIVILEGES` | Everything above. |
| `APPLY TAG` | Add tags only. |

Plus the chain: `USE CATALOG` on `prod`, `USE SCHEMA` on `prod.churn`.

A production-serving service principal needs `USE CATALOG`, `USE SCHEMA`, `EXECUTE` on the model. The ML team needs `MODIFY` or `OWNERSHIP`. Read-only stakeholders get `BROWSE` to see the model exists without loading it.

This is the second time in this Part where UC's governance has done meaningful work for free — feature tables in Ch 71, models here. Both ride on the same permission model.

---

## 73.10 The full promotion workflow

Putting it together — the realistic promotion of a new model version:

```python
# === Day 0 — Champion v3 in production ===
# Endpoint loads models:/prod.churn.rf_model@champion → v3

# === Day 1 — Train candidate v4 ===
with mlflow.start_run(run_name="churn_v4_more_features") as run:
    # ... train, evaluate ...
    mlflow.sklearn.log_model(
        model, "model",
        signature=sig, input_example=X_train.head(5),
        registered_model_name="prod.churn.rf_model",   # creates v4
    )
    candidate_version = 4    # or extract from result

# === Day 1+ — Mark v4 as challenger ===
client.set_registered_model_alias(
    name="prod.churn.rf_model",
    alias="challenger",
    version=candidate_version,
)
client.set_model_version_tag(
    name="prod.churn.rf_model",
    version=candidate_version,
    key="trained_on",
    value="2026-05-data",
)

# === Day 2-5 — Offline validation ===
# Run validation queries, A/B simulation, business KPI checks.
# Tag the version as validated.
client.set_model_version_tag(
    name="prod.churn.rf_model",
    version=candidate_version,
    key="offline_validated",
    value="true",
)

# === Day 6 — Promote: atomic alias swap ===
# Move @champion from v3 to v4.
client.set_registered_model_alias(
    name="prod.churn.rf_model",
    alias="champion",
    version=candidate_version,        # was 3, now 4
)

# Optionally: keep v3 around with an archived alias for fast rollback.
client.set_registered_model_alias(
    name="prod.churn.rf_model",
    alias="archived",
    version=3,
)

# === Production endpoint now serves v4 transparently ===

# === If something goes wrong (Day 6 + 1 hour) — instant rollback ===
client.set_registered_model_alias(
    name="prod.churn.rf_model",
    alias="champion",
    version=3,        # rollback
)
# Endpoint serves v3 again on next load. Total downtime: zero.
```

The pattern is general:
1. Train and register the new version.
2. Tag and alias as challenger.
3. Validate offline.
4. Tag validation results.
5. Atomic alias swap.
6. (Optional) keep old champion accessible for rollback.

---

## 73.11 The "promote code vs promote model" debate

The exam Section 1 explicitly tests: "Identify scenarios where promoting code is preferred over promoting models and vice versa."

The two paradigms:

- **Promote model.** Train once in dev, register, alias-promote across environments. Same artifact in dev / staging / prod.
- **Promote code.** Promote the *training code* across environments, then re-train in each environment against that environment's data. The dev environment's "model" is whatever the dev-data-trained version produces; prod is what prod-data produces.

When to promote model:
- Data is identical in dev and prod (or dev is a clean subset).
- Training is expensive — you don't want to retrain in each environment.
- You want the *exact same* model artifact in prod as you tested in staging.
- Regulatory environments where the certified artifact must be the deployed artifact.

When to promote code:
- Dev data and prod data differ meaningfully — you want each environment trained on its own data.
- Training is cheap.
- You're worried about subtle data leakage from dev into prod (the registered model could carry dev-specific information).
- Each environment must be isolated for compliance.

Most healthcare and fintech ML deployments promote-model (regulatory tractability — the certified artifact moves through environments). Most consumer-data ML promotes-code (data shape changes per environment).

There's no universal right answer. The exam expects you to recognize both paradigms and articulate when each fits.

---

## 73.12 Webhooks → Lakeflow Jobs (the modern hook story)

Pre-UC, you could attach **webhooks** to model-stage-transition events — get a Slack notification when a model entered Staging, kick off a CI job when it entered Production, etc.

UC doesn't have webhooks the same way. The modern pattern is **Lakeflow Jobs** (formerly "Workflows") that fire on alias changes or schedule. A simple example:

- A scheduled job runs hourly, queries the UC Model Registry for any model where `@challenger` is newer than 24 hours and has `tags.offline_validated=true`, and triggers downstream validation.
- A job watching a Delta change feed on the registry's audit log can react to any registry event.

For the Associate exam, knowing that webhooks are legacy and that Lakeflow Jobs / event-driven mechanisms replace them is enough. You won't be tested on webhook syntax.

---

## 73.13 Mosaic AI Model Serving — the forward pointer

The Associate exam tests Model Serving lightly (it's a Section 4 topic at 12% of the exam). What you need:

**Mosaic AI Model Serving** is a managed serving endpoint that hosts UC-registered models behind an HTTP REST API.

You configure an endpoint with one or more *served entities*, each pointing to a registered model + alias or version:

```json
{
  "name": "churn-predictor",
  "config": {
    "served_entities": [
      {
        "entity_name": "prod.churn.rf_model",
        "entity_version": null,
        "alias": "champion",
        "workload_size": "Small",
        "scale_to_zero_enabled": true
      }
    ]
  }
}
```

Critical facts for the exam:

- **Endpoints serve UC-registered models** (referenced by alias or version).
- **Endpoints support multiple served entities** with `traffic_percentage` summing to 100 — this is the "split data between endpoints" exam objective. Used for A/B testing two versions.
- **Endpoints auto-scale** based on traffic, including scale-to-zero (no requests → no cost).
- **Endpoints accept JSON input** at `POST /serving-endpoints/{name}/invocations` with payloads like `{"dataframe_records": [{"feature1": 1.2, ...}]}`.
- **For feature-store-aware models** (logged with `fe.log_model`), the endpoint looks up online features automatically from the configured UC online tables.
- **When you reassign the alias** that an endpoint targets, the endpoint picks up the new version on its next refresh (within seconds). No endpoint redeployment needed.

The last point is the payoff of the entire alias mechanism: zero-downtime promotion. Promote `@champion` in UC → endpoint serves new model. Done.

Endpoints are billed separately from cluster compute (their own DBU stream). They live on a different compute fabric — you don't size them as Spark clusters; you pick a "workload size" (Small, Medium, Large) and Databricks manages scaling.

For the Associate exam, you should be able to:
- Describe the three serving paradigms — **batch** (`fe.score_batch` against a UC table), **real-time** (Mosaic AI Model Serving HTTP endpoint), **streaming** (Spark Structured Streaming with a `pandas_udf` calling the model, or DLT with a model UDF).
- Recognize when each fits: batch for daily scoring of millions; real-time for per-request inference; streaming for high-throughput event processing.
- Recognize that DLT is *not* the same as Model Serving — DLT is high-throughput streaming inference; Model Serving is low-latency request/response.

---

## 73.14 Worked example — end-to-end registration + promotion

```python
import mlflow
from mlflow import MlflowClient
from mlflow.models.signature import infer_signature
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

mlflow.set_registry_uri("databricks-uc")
mlflow.set_experiment("/Shared/churn-experiment")
client = MlflowClient()

# === Train + register v1 ===
with mlflow.start_run(run_name="churn_v1") as run1:
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=100, max_depth=6).fit(X_train, y_train)
    sig = infer_signature(X_train, model.predict(X_train))
    mlflow.sklearn.log_model(
        model, "model",
        signature=sig, input_example=X_train.head(3),
        registered_model_name="prod.churn.rf_model",
    )
    v1_run_id = run1.info.run_id

# Make v1 champion
client.set_registered_model_alias("prod.churn.rf_model", "champion", version=1)

# === Train + register v2 (improvement attempt) ===
with mlflow.start_run(run_name="churn_v2_more_trees") as run2:
    model = RandomForestClassifier(n_estimators=300, max_depth=8).fit(X_train, y_train)
    sig = infer_signature(X_train, model.predict(X_train))
    mlflow.sklearn.log_model(
        model, "model",
        signature=sig, input_example=X_train.head(3),
        registered_model_name="prod.churn.rf_model",
    )

# Mark v2 as challenger
client.set_registered_model_alias("prod.churn.rf_model", "challenger", version=2)

# Tag v2 with its validation result
client.set_model_version_tag(
    "prod.churn.rf_model", version=2, key="val_auc", value="0.864",
)

# === Inspect ===
print("Champion:", client.get_model_version_by_alias("prod.churn.rf_model", "champion").version)
print("Challenger:", client.get_model_version_by_alias("prod.churn.rf_model", "challenger").version)

# === Promote v2 to champion ===
client.set_registered_model_alias("prod.churn.rf_model", "champion", version=2)
# v1 still has no alias (or you could set @archived)
client.set_registered_model_alias("prod.churn.rf_model", "archived", version=1)

# === Load by alias (this is what production code does) ===
champion_model = mlflow.pyfunc.load_model("models:/prod.churn.rf_model@champion")
# champion_model now refers to v2 — no code change needed in the consumer

# === Rollback if needed ===
# client.set_registered_model_alias("prod.churn.rf_model", "champion", version=1)
```

---

## 73.15 Common errors and traps

### 73.15.1 "Stages don't exist in UC"

If you call `transition_model_version_stage(name="prod.churn.rf_model", ...)` on a UC-registered model, you get an error like:

```
RESOURCE_DOES_NOT_EXIST: Stages are not supported in Unity Catalog.
Use aliases instead.
```

The fix: `set_registered_model_alias(...)`.

### 73.15.2 "Signature required"

```
INVALID_PARAMETER_VALUE: Model signature is required for registering models
in Unity Catalog.
```

Fix: re-log the model with `signature=infer_signature(...)`.

### 73.15.3 Forgetting `set_registry_uri("databricks-uc")`

If you've been using the legacy workspace registry (or if the notebook inherits an old default), calls to register might silently land in the wrong registry — model appears in the legacy workspace UI but not in UC. Always set the registry URI explicitly.

### 73.15.4 Permission chain on registered models

Same as tables (Ch 70's USE/USE/SELECT chain): to load a model, the consumer needs `USE CATALOG`, `USE SCHEMA`, and `EXECUTE ON MODEL`. Missing the chain → permission denied. The first-debugging-step for "I can't load this model" is to check the chain.

### 73.15.5 Alias on a non-existent version

```python
client.set_registered_model_alias("prod.churn.rf_model", "champion", version=99)
# RESOURCE_DOES_NOT_EXIST: Model version 99 does not exist
```

UC validates the version exists before setting the alias. You can't "promote into the future."

---

## 73.16 What this builds on / where this returns

**Builds on:** Ch 70 (UC namespace, securables, permissions); Ch 72 (MLflow tracking — runs are the source of model artifacts).

**Returns:** Nothing in subsequent chapters of this Part (Part L ends here). The capstone (*Ch 74*) reuses everything: feature engineering in UC, MLflow tracking, UC Model Registry with alias-based promotion, and Mosaic AI Model Serving for the deployed endpoint.

---

## 73.17 Exercises

1. **3-level name.** Write the fully-qualified UC name for a registered fraud model in the `prod` catalog under the `risk` schema, named `xgb_fraud_v2`.

2. **Immutability.** You've registered `prod.churn.rf_model/v3` and realize the model was trained on the wrong data. You want to "fix" v3. What can you actually do? What should you do?

3. **Aliases vs stages.** A teammate writes:
   ```python
   client.transition_model_version_stage(
       name="prod.churn.rf_model", version=3, stage="Production"
   )
   ```
   This fails. Why, and what's the correct call?

4. **Atomic swap reasoning.** Walk through what happens at the serving endpoint when you reassign `@champion` from v3 to v4. Why is there no downtime?

5. **Tag vs alias.** For each, decide whether to use a tag or an alias:
   (a) Mark v3 as the version currently used by the US team's endpoint.
   (b) Record that v3 passed the bias audit in March.
   (c) Mark v3 as the canonical "production" version.
   (d) Record that v3 was trained on the 2026-Q1 data snapshot.
   (e) Indicate v3 is the candidate being evaluated against the current production model.

6. **The legacy migration.** Your team is moving from the legacy workspace registry to UC. Currently you have a model `churn_model` with v3 in `Production` stage, v4 in `Staging`, v1 and v2 in `Archived`. Describe how you'd recreate this state in UC.

7. **Promotion workflow.** Sketch (in code or pseudocode) the steps to promote a new model version v5 to production using UC aliases, with the previous champion v4 kept available for rollback.

8. **Load by alias vs load by version.** Why is loading `models:/cat.sch.m@champion` better than loading `models:/cat.sch.m/3` in production code?

9. **Permission chain.** A service principal can't load `prod.churn.rf_model`. The error says "PERMISSION_DENIED". List the three privileges the SP needs and the chain order.

10. **Signature error.** A teammate runs `mlflow.register_model(...)` and gets `INVALID_PARAMETER_VALUE: Model signature is required`. What did they forget, and how do they fix it?

11. **Promote code vs promote model.** Give two scenarios where promote-code is the right answer, and two where promote-model is.

12. **Mosaic AI Model Serving recognition.** Of these, which is best served by Mosaic AI Model Serving vs batch inference vs DLT streaming?
    (a) Score 50 million members daily.
    (b) Return a fraud-risk score in <50ms for each card transaction.
    (c) Process a Kafka topic of 100k events/sec, applying a classifier to each.
    (d) Compute monthly retention scores per customer.

13. **The traffic split.** Describe what the following served-entity config does:
    ```
    served_entities: [
      {entity_name: "prod.churn.rf_model", alias: "champion", traffic_percentage: 90},
      {entity_name: "prod.churn.rf_model", alias: "challenger", traffic_percentage: 10}
    ]
    ```

14. **End-to-end story.** Walk through the lifecycle of a single model from training notebook to live endpoint, naming every API call (training, logging, registering, aliasing, loading, promoting, rolling back).

15. **The Hyperopt → register pipeline.** You did a Hyperopt sweep with autolog. You want to register the best model into UC. Outline the steps.

<details>
<summary>Answers</summary>

1. `prod.risk.xgb_fraud_v2`.

2. You cannot modify v3 — it's immutable. The correct action is to train a new model (v4) with the correct data, register it, and promote (alias-swap) `@champion` to v4. Optionally delete v3 from the registry to prevent accidental use, though more commonly you'd leave it and rely on the alias to control which version serves traffic.

3. Stages don't exist for UC-registered models. The correct call: `client.set_registered_model_alias(name="prod.churn.rf_model", alias="champion", version=3)`.

4. The endpoint loads the model from `models:/...@champion` either on every request or on a refresh cycle. When the alias is reassigned, the next load picks up the new version. Atomic in UC's metastore — there's no moment where the alias points to nothing. In-flight requests with the old version finish normally; new requests get the new version. Zero downtime.

5. (a) alias (e.g., `@us_team`); (b) tag (`passed_bias_audit_march=true`); (c) alias (`@champion`); (d) tag (`trained_on=2026-Q1`); (e) alias (`@challenger`).

6. (i) Register the existing v3, v4 into UC (or re-register the underlying runs) — UC gives them new sequential version numbers, say v1 and v2 in UC. (ii) Set alias `@champion` on UC-v1 (the old Production). (iii) Set alias `@challenger` on UC-v2 (the old Staging). (iv) Optionally don't migrate the Archived versions, or migrate and tag them `archived=true`. There's no automated tool — it's a deliberate cutover.

7. ```python
    # New v5 — registered via mlflow.sklearn.log_model with registered_model_name
    client.set_registered_model_alias("prod.churn.rf_model", "challenger", version=5)
    # ... validate v5 ...
    client.set_model_version_tag("prod.churn.rf_model", 5, "validated", "true")
    # Atomic promotion
    client.set_registered_model_alias("prod.churn.rf_model", "champion", version=5)
    # Old champion v4 kept available
    client.set_registered_model_alias("prod.churn.rf_model", "archived", version=4)
    # If rollback needed:
    # client.set_registered_model_alias("prod.churn.rf_model", "champion", version=4)
    ```

8. Because the alias-based load is *stable across promotions*. The serving code never changes — alias swaps in UC immediately route the endpoint to the new version. Loading by explicit version requires editing the code (or redeploying) to change versions.

9. `USE CATALOG prod`, `USE SCHEMA prod.churn`, `EXECUTE ON MODEL prod.churn.rf_model`. All three required; missing any one → permission denied.

10. They forgot to log the model with `signature=...`. Fix: re-train (or just re-log if the model object is still in memory) using `mlflow.sklearn.log_model(model, "model", signature=infer_signature(X_train, model.predict(X_train)), input_example=...)`, then re-register.

11. *Promote code:* (a) dev and prod data shapes differ; (b) training is cheap and you want each environment trained on its own data. *Promote model:* (a) you want the exact same certified artifact in prod that staging tested; (b) training is expensive and you don't want to retrain across environments.

12. (a) batch — daily, millions, latency tolerant. (b) Model Serving — request/response, <50ms. (c) DLT streaming — high throughput, continuous. (d) batch — monthly cadence, large volume.

13. The endpoint accepts requests and routes 90% of them to the `@champion` version of `prod.churn.rf_model`, and 10% to the `@challenger` version. This is the A/B testing pattern — both versions run in parallel; you collect logs and compare metrics offline before promoting challenger to champion.

14. Train in a notebook → `mlflow.start_run` and `mlflow.sklearn.log_model(... registered_model_name=...)` (or call `mlflow.register_model` afterward) → `client.set_registered_model_alias(..., alias="challenger", version=N)` → validate offline → tag with results → `client.set_registered_model_alias(..., alias="champion", version=N)` → Mosaic AI endpoint configured with `entity_name=..., alias="champion"` auto-picks up the new version. If problems: `client.set_registered_model_alias(..., alias="champion", version=N-1)` rolls back.

15. (i) Use `client.search_runs(experiment_ids=..., order_by=["metrics.val_auc DESC"], max_results=1)` to find the best child run. (ii) Either re-train at parent-run level with the best hyperparams and log the model there, OR call `mlflow.register_model(model_uri=f"runs:/{best_run_id}/model", name="prod.cat.model")`. (iii) Set `@challenger` alias on the new version. (iv) Validate, set `@champion`, etc., per the standard promotion workflow.

</details>
