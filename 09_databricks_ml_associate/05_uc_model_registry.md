# Module 5 — Unity Catalog Model Registry

> **Goal of this module:** Master the UC Registry's alias-based lifecycle, tag CRUD, and the mental switch away from legacy stages. Expect 3-4 questions on this directly. Combined with Module 3 (Feature Engineering), these two cover the "UC-native ML" half of Domain 1.
>
> **Maps to exam objectives:** *Register a model using the MLflow Client API in the Unity Catalog registry · Identify benefits of registering models in the Unity Catalog registry over the workspace registry · Identify scenarios where promoting code is preferred over promoting models and vice versa · Set or remove a tag for a model · Promote a challenger model to a champion model using aliases* (Domain 1).

---

## Coverage map (verbatim exam objectives → where taught here)

| Verbatim objective | Taught in section |
|---|---|
| Register a model using the MLflow Client API in the Unity Catalog registry | "Registering a model — three patterns" (Pattern C) + "Full registry API surface" |
| Identify benefits of registering models in the Unity Catalog registry over the workspace registry | "Benefits of UC registry over workspace registry" |
| Identify scenarios where promoting code is preferred over promoting models and vice versa | "Promote code vs promote model" |
| Set or remove a tag for a model | "Tags — separate from aliases" + look-alike table for `set_registered_model_tag` vs `set_model_version_tag` |
| Promote a challenger model to a champion model using aliases | "Setting and using aliases" + "Lifecycle example end-to-end" |

---

## The two registries — recognize the switch

| Registry | Naming | Lifecycle | Status |
|----------|--------|-----------|--------|
| **Unity Catalog (UC)** | `catalog.schema.model` (three-level) | **Aliases** (`@champion`, `@challenger`, `@dev`, ...) | **CURRENT** |
| **Workspace** | `model_name` (single-level, workspace-scoped) | **Stages** (`None`, `Staging`, `Production`, `Archived`) | Legacy |

The exam objectives are written explicitly around UC and aliases — "promote a challenger model to a champion model using aliases." If a question mentions `transition_model_version_stage` or "transition to Production stage," that's the **legacy** API; the answer is usually that the candidate should be using aliases instead, or the question is testing that you recognize the distinction.

### Switching MLflow to UC

```python
import mlflow
mlflow.set_registry_uri("databricks-uc")
```

Without this, registrations land in the workspace registry. This one line is your switch.

---

## Aliases — the new mental model

An **alias** is an arbitrary string label that points to a specific version of a registered model. Unlike stages, aliases are:

- **Many-to-many.** One model version can carry multiple aliases. Multiple versions can carry the same alias (rare — more often you reassign).
- **Free-form names.** `@champion`, `@challenger`, `@dev`, `@shadow`, `@a`, `@b` — whatever convention you adopt.
- **Reassignable.** You promote by reassigning the alias, not by transitioning a state machine.
- **Resolvable in URIs.** `models:/catalog.schema.model@champion` resolves to whatever version currently carries `@champion`.

### Stages vs aliases — cognitive switch

```
Legacy stages (workspace registry)
─────────────────────────────────
Version 1: stage=None
Version 2: stage=Staging       — promoted
Version 3: stage=Production    — promoted
Version 4: stage=None          — newly registered
Operation: client.transition_model_version_stage(name, version=4, stage="Production")
           (this AUTO-archives the previous Production by default)


UC aliases
──────────
Version 1: aliases=[]
Version 2: aliases=[@dev]
Version 3: aliases=[@champion]
Version 4: aliases=[@challenger]
Promotion: client.set_registered_model_alias(name, "champion", version=4)
           (this MOVES the @champion label from v3 to v4; v3 keeps no alias unless you set one)
```

> ⚠️ **Exam trap:** "Promote v4 to Production stage" is a legacy phrasing. In UC, you'd say "set alias `@champion` to v4." If the question's setup is UC-native (FeatureEngineeringClient, `models:/catalog.schema.model`, `set_registry_uri("databricks-uc")`), then the correct API is `set_registered_model_alias`, not `transition_model_version_stage`.

---

## Registering a model — three patterns

### Pattern A: at log time

The simplest path. `log_model` accepts a `registered_model_name`:

```python
mlflow.set_registry_uri("databricks-uc")

with mlflow.start_run():
    ...
    mlflow.sklearn.log_model(
        model,
        artifact_path="model",
        registered_model_name="retail.models.churn",   # three-level name
    )
```

If `retail.models.churn` doesn't exist, MLflow creates it. The just-logged model becomes the next version.

### Pattern B: from an existing run via `mlflow.register_model`

```python
result = mlflow.register_model(
    model_uri=f"runs:/{run_id}/model",
    name="retail.models.churn",
)
print(result.version)   # e.g., 5
```

Useful when you logged a model first and decided to register it later.

### Pattern C: via `MlflowClient`

```python
from mlflow import MlflowClient

client = MlflowClient()
client.create_registered_model("retail.models.churn")   # idempotent (errors if exists)

mv = client.create_model_version(
    name="retail.models.churn",
    source=f"runs:/{run_id}/model",
    run_id=run_id,
)
print(mv.version)
```

Lowest-level. Useful in CI/CD scripts or when you need fine-grained control.

---

## Setting and using aliases

```python
from mlflow import MlflowClient
client = MlflowClient()

# Promote v4 to @champion
client.set_registered_model_alias(
    name="retail.models.churn",
    alias="champion",
    version=4,
)

# Set v5 as @challenger
client.set_registered_model_alias(
    name="retail.models.churn",
    alias="challenger",
    version=5,
)

# Promote @challenger to @champion (reassign)
client.set_registered_model_alias(
    name="retail.models.churn",
    alias="champion",
    version=5,   # was 4; now @champion points to 5
)

# Remove an alias
client.delete_registered_model_alias(
    name="retail.models.churn",
    alias="challenger",
)

# Get the version currently aliased
mv = client.get_model_version_by_alias(
    name="retail.models.churn",
    alias="champion",
)
print(mv.version, mv.run_id)
```

### Loading a model by alias

```python
# In application code
model = mlflow.pyfunc.load_model("models:/retail.models.churn@champion")
```

This always resolves to whatever version currently carries `@champion`. **No code change** to swap the champion behind the scenes.

> ⚠️ **Exam trap — alias URI syntax:** Use `@` not `/`. `models:/retail.models.churn@champion` is correct; `models:/retail.models.churn/champion` is the **legacy stage** syntax and only works in workspace registry.

---

## Tags — separate from aliases

Tags are key/value metadata, **not** lifecycle markers. They live at three levels: model-level, version-level, run-level.

### Model-level tags (apply to the whole registered model)

```python
# Set
client.set_registered_model_tag(
    name="retail.models.churn",
    key="owner",
    value="ml-platform",
)

# Delete
client.delete_registered_model_tag(
    name="retail.models.churn",
    key="owner",
)
```

### Version-level tags

```python
# Set
client.set_model_version_tag(
    name="retail.models.churn",
    version=4,
    key="validated_by",
    value="qa-team",
)

# Delete
client.delete_model_version_tag(
    name="retail.models.churn",
    version=4,
    key="validated_by",
)
```

### Run-level tags (set on the MLflow Run — see Module 4)

```python
mlflow.set_tag("data_version", "2026-05-23")
client.set_tag(run_id, "data_version", "2026-05-23")
```

> ⚠️ **Exam trap — `set_tag` vs `set_registered_model_tag`:** Plain `mlflow.set_tag` writes to the **current run**. `MlflowClient.set_registered_model_tag` writes to a **registered model**. Different surfaces. Pay attention to the question's stem (Model UI vs Run UI).

---

## Benefits of UC registry over workspace registry

The exam asks you to recognize these:

1. **Three-level namespace** — `catalog.schema.model` is the same shape as `catalog.schema.table` and `catalog.schema.volume`. Unified mental model.
2. **Cross-workspace access** — one model is reachable from any workspace in the account with UC permissions.
3. **ACL inheritance from UC** — `GRANT EXECUTE ON MODEL ... TO ...` follows the standard UC grant model.
4. **Aliases > stages** — flexible, free-form, multi-version-per-alias semantics. Stages were rigid.
5. **Unified lineage** — UC tracks lineage from tables → features → runs → models in one graph.
6. **Built for Mosaic AI Model Serving** — serving endpoints natively reference UC models (`catalog.schema.model@champion` works as a served-entity URI).

> ⚠️ **Exam trap:** Don't pick "workspace registry is easier" — Databricks treats the workspace registry as legacy. Don't pick "workspace registry is faster" — there's no latency difference. The correct angle is **governance, lineage, cross-workspace, aliases**.

---

## "Promote code" vs "promote model" — exam scenarios

Section 1 explicitly asks: *"Identify scenarios where promoting code is preferred over promoting models and vice versa."* The framework:

### Promote code (default)

You reproduce training in higher environments by promoting the **training code** (notebook/script) and re-running it with environment-appropriate data. This gives you:
- Full auditability — every artifact has a code path
- Retrainability — refresh the model on new data anytime
- Consistent behavior across envs — same code, same model logic

### Promote model (sometimes)

You train once and copy the model artifact across environments. Reasons:
- **Training environment cannot be reproduced in target** — e.g., dev has GPU, prod is CPU-only and can't train
- **Target environment has no access to training data** — e.g., raw PHI is in a restricted dev catalog
- **Training is uneconomical to repeat** — e.g., LLM fine-tune that took 48 hours
- **Byte-exact reproducibility is required** — code-promotion can drift due to non-determinism

### Hybrid (common in practice)

Promote code to staging; promote *registered model versions* from staging to production (the model was trained in staging, validated, and the version is promoted). This is the de facto pattern with UC aliases.

```
dev workspace      staging workspace      prod (same UC catalog)
─────────────      ─────────────────      ─────────────────────
edit code  ──────► run training            (no training; consume)
                   register model
                   set @validated alias    set @champion alias
                                           ▲
                                           │  (cross-workspace UC grant)
                                           └── serving endpoint reads @champion
```

> ⚠️ **Exam trap — "always promote code":** Wrong. Databricks tests both directions. Read the scenario for environment constraints. "Production cluster has no access to the raw training table" → **promote model**. "Same data is available across envs, want full reproducibility" → **promote code**.

---

## Lifecycle example end-to-end (UC)

```python
import mlflow
from mlflow import MlflowClient

mlflow.set_registry_uri("databricks-uc")
client = MlflowClient()

# Train and register
with mlflow.start_run() as run:
    mlflow.log_param("max_depth", 10)
    mlflow.log_metric("auc", 0.92)
    mlflow.sklearn.log_model(
        model, "model",
        registered_model_name="retail.models.churn",
    )

run_id = run.info.run_id

# Find the version that was just created
versions = client.search_model_versions(f"name='retail.models.churn'")
latest = max(versions, key=lambda v: int(v.version))

# Tag this version
client.set_model_version_tag(
    name="retail.models.churn",
    version=latest.version,
    key="trained_on",
    value="2026-05-23",
)

# Mark it as challenger
client.set_registered_model_alias(
    name="retail.models.churn",
    alias="challenger",
    version=latest.version,
)

# Later, after evaluation passes: promote to champion
client.set_registered_model_alias(
    name="retail.models.churn",
    alias="champion",
    version=latest.version,
)

# Optionally clean up the challenger alias
client.delete_registered_model_alias(
    name="retail.models.churn",
    alias="challenger",
)

# Inference code (anywhere) — no code change to swap behind
loaded = mlflow.pyfunc.load_model("models:/retail.models.churn@champion")
```

---

## Look-alike API comparison — registry edition

| Pair | Difference | Exam tell |
|------|------------|-----------|
| `set_registered_model_alias(name, alias, version)` vs `set_registered_model_tag(name, key, value)` | alias = pointer to a version; tag = key/value metadata | "champion/challenger label" → alias. "owner=alice" → tag |
| `set_registered_model_tag(name, key, value)` vs `set_model_version_tag(name, version, key, value)` | model-level tag (all versions) vs single-version tag | "this version was validated" → version tag. "owner of the model" → model tag |
| `mlflow.register_model(model_uri, name)` vs `MlflowClient().create_registered_model(name)` + `create_model_version(...)` | one-step convenience vs explicit two-step | Either works; the client form is what CI/CD scripts use |
| `mlflow.<flavor>.log_model(..., registered_model_name=...)` vs `mlflow.register_model(...)` | log-and-register in one call vs register an already-logged run | Log-time vs after-the-fact |
| `set_registered_model_alias` vs `transition_model_version_stage` | UC (aliases) vs workspace (stages) — different registries | If question mentions UC / three-level name → alias. If "Production"/"Staging" → legacy stages |
| `get_model_version_by_alias(name, alias)` vs `get_model_version(name, version)` | resolve alias to current version vs fetch a specific version | "what's currently @champion" → by_alias |
| `delete_registered_model_alias(name, alias)` vs `delete_model_version_tag(name, version, key)` | remove an alias vs remove a tag | Symmetric to set counterparts |
| `models:/cat.sch.model@champion` vs `models:/cat.sch.model/3` vs `models:/cat.sch.model/Production` | UC alias / version number / legacy stage URI | `@` = UC alias; `/<int>` = version; `/<word>` = legacy stage (workspace only) |

---

## Full registry API surface — `MlflowClient` methods

```python
client = MlflowClient()

# === Registered Models (the named lineage) ===
client.create_registered_model(name, tags=None, description=None)
client.get_registered_model(name)
client.delete_registered_model(name)
client.rename_registered_model(name, new_name)            # workspace registry only
client.search_registered_models(filter_string=..., max_results=..., order_by=[...])
client.update_registered_model(name, description=...)

# === Model Versions ===
client.create_model_version(name, source, run_id=None, tags=None, description=None, await_creation_for=300)
client.get_model_version(name, version)
client.delete_model_version(name, version)
client.search_model_versions(filter_string="name='cat.sch.model'", max_results=..., order_by=[...])
client.update_model_version(name, version, description=...)

# === Aliases (UC only) ===
client.set_registered_model_alias(name, alias, version)
client.get_model_version_by_alias(name, alias)
client.delete_registered_model_alias(name, alias)

# === Tags ===
# Model-level (applies to all versions)
client.set_registered_model_tag(name, key, value)
client.delete_registered_model_tag(name, key)
# Version-level (applies to one version)
client.set_model_version_tag(name, version, key, value)
client.delete_model_version_tag(name, version, key)

# === Legacy stages (workspace registry — DO NOT use on UC) ===
client.transition_model_version_stage(name, version, stage="Production", archive_existing_versions=True)
client.get_latest_versions(name, stages=["Production", "Staging"])
```

> ⚠️ **Exam trap — three-level name required on UC:** When using UC, every `name` must be `catalog.schema.model_name`. A bare model name like `"churn_model"` resolves to the workspace registry even if you set `set_registry_uri("databricks-uc")`. Always write the three-level form.

### Permissions you need in UC for these calls

| Action | Required UC privileges |
|--------|------------------------|
| Create a registered model | `USE CATALOG` + `USE SCHEMA` + `CREATE MODEL` on the schema |
| Log a new version | `USE CATALOG` + `USE SCHEMA` + `CREATE MODEL VERSION` on the model |
| Load / read the model | `USE CATALOG` + `USE SCHEMA` + `EXECUTE` on the model |
| Set alias / tag | `USE CATALOG` + `USE SCHEMA` + `APPLY TAG` (for tags) or model `OWNER` (for aliases) |
| Delete the model | `OWNER` of the model (or admin) |

Exam may phrase as "a data scientist gets a permission error when promoting" — likely missing `EXECUTE`, `CREATE MODEL VERSION`, or alias-setting privilege.

---

## Worked exam-question walkthroughs

### Worked example: "Register a model from an existing run via the Client API"

**Pattern:** Four snippets to register `runs:/abc123/model` to UC name `retail.models.churn`.

**Reasoning:** "Client API" means `MlflowClient`. Use the explicit two-step form.

**Correct (Pattern C):**
```python
client.create_registered_model("retail.models.churn")    # idempotent — skip if exists
mv = client.create_model_version(
    name="retail.models.churn",
    source="runs:/abc123/model",
    run_id="abc123",
)
```

**Equivalent (Pattern B):** `mlflow.register_model(model_uri="runs:/abc123/model", name="retail.models.churn")`.

**Distractors:** missing `source=`; two-level name (UC rejects); `transition_model_version_stage` (legacy + wrong action).

### Worked example: "Promote a challenger to champion"

**Pattern:** v4 is `@challenger`. Promote to `@champion`.

**Correct:**
```python
client.set_registered_model_alias(
    name="retail.models.churn", alias="champion", version=4,
)
```

The previous `@champion` version is implicitly demoted (loses the alias).

**Common distractor:** `transition_model_version_stage(...stage="Production")` — wrong registry.

### Worked example: "Remove a tag"

**Pattern:** Model has `owner=alice`. Remove it.

**Correct (model-level):** `client.delete_registered_model_tag(name="retail.models.churn", key="owner")`.
**Correct (version-level):** `client.delete_model_version_tag(name="retail.models.churn", version=4, key="owner")`.

Wording disambiguates which scope.

### Worked example: "Promote code or promote model?"

**Decision rules:**
- "Prod cannot access training data" → promote model
- "Training requires GPUs not in prod" → promote model
- "Compliance requires byte-exact reproducibility" → promote model
- "Want full retrainability / lineage" → promote code
- "Frequent retraining on fresh data" → promote code

---

## Output prediction drills

### Drill 1
```python
client.create_registered_model("retail.models.churn")
client.create_registered_model("retail.models.churn")
```
**Q:** Second call result?
**A:** **Error** (`RESOURCE_ALREADY_EXISTS`). Not idempotent.

### Drill 2
```python
client.set_registered_model_alias("retail.models.churn", "champion", 3)
client.set_registered_model_alias("retail.models.churn", "champion", 5)
mv = client.get_model_version_by_alias("retail.models.churn", "champion")
print(mv.version)
```
**Q:** Output?
**A:** `5`. Second `set_alias` reassigns; v3 loses the alias.

### Drill 3
```python
mlflow.set_registry_uri("databricks-uc")
mlflow.sklearn.log_model(model, "model", registered_model_name="churn_model")
```
**Q:** Result?
**A:** **Error.** UC requires three-level name.

### Drill 4
```python
client.set_registered_model_tag("retail.models.churn", "owner", "alice")
client.set_model_version_tag("retail.models.churn", 4, "owner", "bob")
```
**Q:** v4 owner tag?
**A:** Both coexist in different scopes. Model-level says alice; version-level says bob. No conflict.

### Drill 5
```python
mlflow.pyfunc.load_model("models:/retail.models.churn/champion")
```
**Q:** Loads v3 currently `@champion`?
**A:** **No — error.** `/` is legacy stage syntax. UC requires `@`: `models:/retail.models.churn@champion`.

---

## End-to-end mini-scenario (registry CI/CD pattern)

```python
import mlflow
from mlflow import MlflowClient

mlflow.set_registry_uri("databricks-uc")
client = MlflowClient()
MODEL_NAME = "retail.models.churn"

with mlflow.start_run(run_name="nightly_train") as run:
    mlflow.log_param("max_depth", 10)
    mlflow.log_metric("val_auc", 0.91)
    mlflow.sklearn.log_model(
        model, artifact_path="model",
        registered_model_name=MODEL_NAME,
    )

# Newly-created version
versions = client.search_model_versions(f"name='{MODEL_NAME}'")
new_version = max(int(v.version) for v in versions)

# Tag + alias as challenger
client.set_model_version_tag(MODEL_NAME, new_version, "val_auc", "0.91")
client.set_registered_model_alias(MODEL_NAME, "challenger", new_version)

# Promote if better than current champion
champion = client.get_model_version_by_alias(MODEL_NAME, "champion")
champion_auc = float(client.get_model_version(MODEL_NAME, champion.version).tags.get("val_auc", 0))

if 0.91 > champion_auc:
    client.set_registered_model_alias(MODEL_NAME, "champion", new_version)
    client.delete_registered_model_alias(MODEL_NAME, "challenger")

# Inference URI never changes
prod_model = mlflow.pyfunc.load_model(f"models:/{MODEL_NAME}@champion")
```

This hits all five Module 5 exam objectives.

---

## Common pitfalls

### Forgetting `set_registry_uri("databricks-uc")`

Without this, your `log_model(registered_model_name=...)` call lands in the **workspace** registry, not UC. The model appears in the workspace Models sidebar but not in your catalog.

### Using legacy stage syntax against UC

```python
# This DOES NOT WORK in UC
client.transition_model_version_stage(name=..., version=4, stage="Production")
# Error or silently no-op (depending on MLflow version)
```

UC does not have stages. Use `set_registered_model_alias` instead.

### Mixing two-level and three-level names

UC requires `catalog.schema.model`. The workspace registry uses bare names. If you registered to workspace and try to address it as `catalog.schema.model`, it won't resolve.

### Confusing model-level tags with version-level tags

`set_registered_model_tag` tags the **whole registered model** (across all versions). `set_model_version_tag` tags **one version**. They show up in different UI panels.

### Forgetting that aliases are mutable

`@champion` today may point to v4; next week, v7. Code that hard-codes a version number (`models:/...catalog.schema.model/4`) won't pick up the swap. Use the alias URI to get auto-swap behavior.

---

## What the exam tests on this module

> 🎯 **Exam tests here:**
> - UC registry uses **aliases**; workspace registry uses **stages**. Recognize the cognitive switch.
> - `mlflow.set_registry_uri("databricks-uc")` is the switch line.
> - `client.set_registered_model_alias(name, alias, version)` for promotion.
> - URI syntax: `models:/catalog.schema.model@champion` (UC) vs `models:/model/Production` (legacy).
> - Tag CRUD: `set_registered_model_tag` / `delete_registered_model_tag` (model-level) vs `set_model_version_tag` (version-level).
> - Benefits of UC: three-level namespace, cross-workspace, ACL inheritance, aliases, unified lineage, Mosaic AI Model Serving integration.
> - When to promote code vs promote model.

---

## Mini quiz

1. Write the one line of Python that switches MLflow's registry to UC.
2. v4 is currently `@champion`. v5 was registered yesterday as `@challenger` and passed evaluation. Promote v5 to champion.
3. Your team is moving from workspace registry to UC. The CI/CD job still calls `client.transition_model_version_stage(name, version, "Production")`. What needs to change?
4. A teammate writes `models:/retail.models.churn/champion` and gets an error. Why?
5. You set `mlflow.set_tag("owner", "alice")` after `mlflow.start_run()`. Then in the UC Models UI you don't see "owner" on the registered model. Why?

### Answers

1. `mlflow.set_registry_uri("databricks-uc")`.
2. ```python
   client.set_registered_model_alias(
       name="retail.models.churn", alias="champion", version=5,
   )
   ```
   The previous v4 keeps no alias unless you explicitly add one (e.g., `@previous_champion`).
3. UC doesn't have stages. Replace with `client.set_registered_model_alias(name, "champion", version)`. URI usage also needs updating from `models:/<name>/Production` to `models:/<name>@champion`.
4. The `/` between model name and alias is the legacy **stage** syntax. UC aliases use `@`: `models:/retail.models.churn@champion`.
5. `mlflow.set_tag` writes to the current **run**, not the **registered model**. Use `client.set_registered_model_tag(name="retail.models.churn", key="owner", value="alice")` to set it on the model.
