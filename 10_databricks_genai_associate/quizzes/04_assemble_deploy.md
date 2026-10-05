# Quiz 04 — Assembling & Deploying (22%, 30 Qs)

> Take cold. ~2 min/Q. Maps to **Modules 07, 10, 11, 12**.

---

## Recall

1. What's the **most-tested** missing argument in `mlflow.pyfunc.log_model` for an agent that calls a VS index?
2. State the registry URI string that points MLflow at Unity Catalog.
3. Name the three MCP server integration types.
4. Two patterns for persistent agent memory inside UC — name them and their typical latency.
5. Which SQL function batch-scores rows from a Delta table through a Model Serving endpoint?
6. Name the MLflow API for atomic alias-based prompt promotion across environments.
7. What permission does an app's service principal need to call a Model Serving endpoint?
8. State the security pattern from sample Q8 in one sentence.

## Apply

9. You need to deploy an agent that reads from `cat.indexes.policy_v1` and calls `databricks-llama-3-3-70b-instruct`. Show the minimal `resources=[...]` argument for `log_model`.
10. Scenario: 50M rows in `bronze.claims` need a summary column once. Endpoint via Python loop or `ai_query`?
11. You want to canary 10% of traffic to a new agent version. Sketch the `traffic_config`.
12. Sample Q9 scenario: one source has managed MCP, one needs API key. Which two actions?
13. Persistent agent memory for a HIPAA-regulated chat agent — which storage layers?
14. Promote prompt v8 from staging to production atomically without redeploying the model. Which call?
15. Build a DAB target for staging that points at a separate UC catalog `staging_cat`. Show the YAML stanza.
16. A user types in the form: `member_id = "12345"`. Your Streamlit app passes that to the agent. What's the vulnerability and the fix?
17. The agent calls UC function `cat.tools.get_member_history`. The endpoint deploys but tool calls fail. Likely cause if `resources` includes the function?
18. The endpoint with `scale_to_zero_enabled=True` shows 45s latency on first request after 5 minutes idle. Options to remove the cold start without scaling-up wastefully?

## Diagnose

19. Symptom: agent endpoint serves locally; in prod, gets 403 when querying a VS index. `resources` declared at log time. Three further causes?
20. The Streamlit app on Databricks Apps returns 401 to the user. SSO is configured. Diagnosis path?
21. The model is registered in UC; `mlflow.set_registry_uri("databricks-uc")` was called; but `log_model` still fails with "model name must be in three-level form." Why?
22. Two served entities `v3` (90%) and `v4_canary` (10%). Traffic percentages sum to 95. Result?
23. Inference Tables aren't populating on a new endpoint. The endpoint serves traffic correctly. What's missing?

## Defend

24. Argue for Databricks Apps over Vercel for a PHI agent UI.
25. Defend pinning explicit model version in the endpoint config while using aliases for promotion tracking — vs reading alias at endpoint resolution time.
26. Justify rolling traffic via canary (10% → 50% → 100%) even when staging eval passes.

## [Multi-select]

27. **[select TWO]** Required `log_model` arguments for a deployable Databricks RAG chain.
   (A) `registered_model_name` in three-level UC form
   (B) `resources` listing endpoints + indexes + functions used
   (C) `input_example` for schema inference
   (D) `pip_requirements` always empty
   (E) `artifact_path` set to "model"

28. **[select TWO]** Persistent agent memory patterns Databricks tests as exam-correct.
   (A) Delta tables in UC
   (B) Online Tables (low-latency lookup)
   (C) Redis on the app's machine
   (D) Lakebase (Postgres on Databricks)
   (E) The agent's local file system

29. **[select THREE]** Steps for promoting a prompt from dev to production with rollback ability.
   (A) Register prompt to MLflow Prompt Registry under UC name
   (B) Hardcode prompt in chain.py and commit to main
   (C) Set alias `@staging` to the new version
   (D) After eval passes, set `@production` to the same version
   (E) Store the prompt in a Delta table with a timestamp

30. **[select TWO]** Behaviors of `ai_query()` that distinguish it from a Python loop hitting the endpoint.
   (A) Spark parallelizes calls across the cluster
   (B) Per-row error handling via `failOnError => false`
   (C) Lower latency on a single row
   (D) Better real-time streaming support
   (E) Built-in retries against transient endpoint errors

---

## Answers

1. **`resources=[...]`** — declaring each Databricks resource the chain uses. Without it, the served endpoint can't authenticate to VS index / LLM / functions. → Module 07
2. **`"databricks-uc"`** (not `"databricks"`). → Module 07
3. Managed, External, Custom. → Module 11
4. **Delta tables** (durable, seconds latency), **Online Tables** (< 50 ms key lookup). Also Lakebase (< 10 ms transactional) and VS index (semantic memory). → Module 11
5. **`ai_query`**. → Module 10
6. **`mlflow.genai.set_prompt_alias(name=..., alias="production", version=N)`**. → Modules 05, 11
7. **`CAN_QUERY`** on the endpoint. → Module 12
8. App backend calls the agent endpoint with the **app's service principal**; user identity flows via workspace OAuth from browser to app; per-user data filtering happens in the agent based on forwarded user context — never PAT in browser. → Module 12
9. ```python
   resources=[
       mlflow.models.resources.DatabricksServingEndpoint(
           endpoint_name="databricks-llama-3-3-70b-instruct"),
       mlflow.models.resources.DatabricksVectorSearchIndex(
           index_name="cat.indexes.policy_v1"),
   ]
   ``` → Module 07
10. **`ai_query`**. Batch + Spark parallelism + lower cost per scored row. Python loop forfeits parallelism. → Module 10
11. ```python
    traffic_config=TrafficConfig(routes=[
        Route(served_model_name="v3", traffic_percentage=90),
        Route(served_model_name="v4_canary", traffic_percentage=10),
    ])
    ``` → Module 10
12. **(1)** Use managed MCP for the Databricks source. **(2)** Deploy the external MCP and reference its API key via `{{secrets/scope/key}}` in Databricks Secrets. Sample Q9 = D + E. → Module 11
13. **Delta tables in UC** (audit log) and **Online Tables** (live state lookup). PHI must stay in UC-governed HIPAA-scope catalogs. NOT external Redis. → Module 11
14. **`mlflow.genai.set_prompt_alias(name="cat.prompts.x", alias="production", version=8)`**. Agent loads `@production` at every request, so alias swap is immediate. → Modules 05, 11
15. ```yaml
    targets:
      staging:
        workspace:
          host: https://staging.cloud.databricks.com
        variables:
          catalog: staging_cat
    ``` → Module 11
16. **User-spoofing.** Malicious user changes the form value to access someone else's data. Fix: derive identity from **verified workspace OAuth/Forwarded-Email header**, not user-controlled input. → Module 12
17. The endpoint's **service principal** lacks `EXECUTE` on the function in UC, OR workspace lacks serverless generic compute enabled (the Lakeguard execution layer). → Modules 08, 10
18. Options: (a) Set `min_provisioned_concurrent_units` > 0 to keep one warm; (b) Schedule a keep-alive ping every N minutes during business hours; (c) Use Provisioned Throughput with always-on capacity. Trade cost for warmth. → Module 10
19. (a) Endpoint SP doesn't have `USE_INDEX` grant (resources declaration sets it up for the **deploy via agents helper** path, but custom deploys may need explicit grants). (b) Index was rebuilt with a new name; resources list references the old. (c) Cross-workspace identity boundary mismatch. → Module 10
20. The app's service principal isn't authorized in the workspace, or the user's group isn't allowed to view the app, or the app's OAuth callback URL isn't registered. Check app permissions in workspace UI. → Module 12
21. The **registered_model_name** was passed in two-level form (`schema.model`) or unqualified. UC requires three-level (`catalog.schema.model`). → Module 07
22. **Validation failure** — traffic_percentage must sum to exactly 100 across all routes. The config update will reject. → Module 10
23. **AI Gateway Inference Tables not enabled** on the endpoint. Configure via `serving_endpoints.update_ai_gateway(inference_table_config=...)`. → Module 15
24. PHI requires staying inside BAA scope. Databricks Apps runs in the workspace with UC-governed credentials, full audit logs, no PHI leaving the BAA boundary. Vercel is generally not BAA-covered for healthcare unless contracted explicitly; even then, propagating identity + UC ACLs is harder. → Module 12
25. Pinning version in config gives **deterministic deployments** — the endpoint always serves what you expect. Alias tracks promotion state (which version is "currently production"). Reading alias at endpoint resolution time introduces a moving target — config drift, hard to reproduce. Better: alias signals promotion; config pin executes. → Modules 10, 11
26. Staging eval can't catch every production edge case — distribution differences, scale-dependent bugs, cold-cache effects. Canary at 10% gives a real-world signal before exposing all users. With auto-rollback on SLO breach, max blast radius is 10% of users for the canary window. → Modules 10, 11, 15
27. **(A) + (B).** Three-level UC name + `resources` declaration. (C) recommended but not strictly required. (D) optional. (E) not required by Databricks. → Module 07
28. **(A), (B), (D).** UC-native memory layers. Redis on the app machine and local filesystem bypass UC governance. → Module 11
29. **(A), (C), (D).** Registry + staging alias + production alias. Hardcoding (B) and Delta-as-store (E) lose the alias semantics. → Modules 05, 11
30. **(A) + (B).** Spark parallelism and per-row error handling. (C) ai_query has higher per-row latency than a single direct call. (D) `ai_query` isn't streaming. (E) retries exist but aren't the distinguishing feature. → Module 10
