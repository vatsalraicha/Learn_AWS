# Quiz 04 — Productionizing Data Pipelines (18%)

> Take cold. ~24 questions. ~2 min per question. Covers Lakeflow Jobs, Databricks Asset Bundles (DAB), monitoring/Spark UI, repair runs, serverless.

---

## Recall

1. What was "Workflows / multi-task jobs" renamed to in 2025?
2. What's the root config file of a Databricks Asset Bundle?
3. Which top-level YAML block in `databricks.yml` defines environment-specific overrides (dev/staging/prod)?
4. Which top-level YAML block defines the jobs and pipelines being deployed?
5. Which Lakeflow Jobs feature lets you re-run only the failed tasks of a partially-failed job without rerunning the successful ones?
6. Name the three compute choices for a task in Lakeflow Jobs.
7. Which API does one task use to pass a value to a downstream task in the same job?

## Apply

8. You need to run a daily ETL job that depends on three upstream notebooks. After the notebooks succeed, an LDP pipeline runs, and on success a notification is sent. Sketch the Lakeflow Jobs task DAG.
9. The team wants the job triggered automatically when a new file lands in `/Volumes/main/landing/orders/`. Which trigger type?
10. The team needs to promote the same job definition across dev → staging → prod with environment-specific parameter values. Which Databricks feature?
11. Write the `databricks.yml` skeleton showing a single job `orders_daily` running an LDP pipeline `orders_pipeline`, with `dev` and `prod` targets and a `catalog` variable.
12. The team needs to pass the value `last_run_id` from a Notebook task to a downstream Python task. Sketch both sides.
13. You want a job to run on serverless compute instead of a job cluster. What changes in the task config?
14. CLI command to validate a bundle locally before deploying.
15. CLI command to deploy a bundle to the `prod` target.
16. CLI command to run a job named `orders_daily` from a deployed bundle.
17. The team wants retries with a 5-minute backoff and a max of 3 attempts for a flaky task. Where do they configure this?

## Diagnose

18. A team's job runs on an all-purpose cluster and costs $20k/month. The same workload on a job cluster costs ~$9k. What changed and why?
19. A repair run reruns a task that succeeded last time. The team expected it to skip succeeded tasks. What's wrong?
20. The team's bundle deploys but the pipeline has stale code. They edited the SQL files locally but didn't bump anything. Why isn't the new code running?
21. A task fails because a variable substitution `${var.catalog}` is empty in prod. The dev target works fine. Where to look?
22. The Spark UI shows one stage with `max task time = 45s`, `median = 800ms`. What problem does this indicate?

## Defend

23. Defend job clusters over all-purpose clusters for scheduled Workflows tasks.
24. Defend DABs over the "click around the Jobs UI then export the JSON" approach for cross-environment promotion.

---

## Answers

1. **Lakeflow Jobs** — same product, renamed. Engine and feature set unchanged. ⚠️ **Exam trap:** Pre-2025 study material calls it "Workflows" or "multi-task jobs."
2. **`databricks.yml`** at the bundle root.
3. **`targets:`** — defines dev / staging / prod (or arbitrary names) with per-target workspace, variables, and resource overrides.
4. **`resources:`** — contains `jobs:`, `pipelines:`, `schemas:`, `models:`, `experiments:`, etc.
5. **Repair run** — re-execute failed tasks only, preserving the success state of completed tasks. ⚠️ **Exam trap:** Repair reuses partial state — taskValues from successful tasks are still available; the repair starts where the failure occurred.
6. **All-purpose cluster** (interactive, expensive), **job cluster** (ephemeral, cheaper), **serverless** (managed by Databricks).
7. **`dbutils.jobs.taskValues.set("key", value)`** in the producing task; **`dbutils.jobs.taskValues.get(taskKey="upstream_task", key="key")`** in the consuming task.
8. Three notebook tasks `n1`, `n2`, `n3` run in parallel; one pipeline task `ldp_run` lists all three in `depends_on`; one notification task `notify_ok` lists `ldp_run` in `depends_on`. Example outline:
   ```yaml
   tasks:
     - task_key: n1
       notebook_task: {notebook_path: ./n1.py}
     - task_key: n2
       notebook_task: {notebook_path: ./n2.py}
     - task_key: n3
       notebook_task: {notebook_path: ./n3.py}
     - task_key: ldp_run
       depends_on: [{task_key: n1}, {task_key: n2}, {task_key: n3}]
       pipeline_task: {pipeline_id: ${resources.pipelines.orders_pipeline.id}}
     - task_key: notify_ok
       depends_on: [{task_key: ldp_run}]
       notebook_task: {notebook_path: ./notify.py}
   ```
9. **File arrival trigger** — Lakeflow Jobs has a native file-arrival trigger that watches a UC Volume / external location path and fires when new files appear.
10. **Databricks Asset Bundles (DAB)** with `targets:` providing per-environment overrides + `variables:` for per-target values. ⚠️ **Exam trap:** Any "promote across envs" scenario answer is DAB.
11. ```yaml
    bundle:
      name: orders

    variables:
      catalog:
        default: dev_main

    targets:
      dev:
        mode: development
        workspace: {host: https://adb-dev.cloud.databricks.com}
        variables: {catalog: dev_main}
      prod:
        mode: production
        workspace: {host: https://adb-prod.cloud.databricks.com}
        variables: {catalog: main}

    resources:
      pipelines:
        orders_pipeline:
          name: orders-${bundle.target}
          catalog: ${var.catalog}
          target: sales
          libraries:
            - notebook: {path: ./pipelines/orders.sql}
      jobs:
        orders_daily:
          name: orders-daily-${bundle.target}
          tasks:
            - task_key: run_pipeline
              pipeline_task: {pipeline_id: ${resources.pipelines.orders_pipeline.id}}
    ```
12. Producer notebook:
    ```python
    dbutils.jobs.taskValues.set(key="last_run_id", value="run_12345")
    ```
    Downstream task receives it as a parameter using `{{tasks.<producer_task_key>.values.last_run_id}}`, or reads via:
    ```python
    rid = dbutils.jobs.taskValues.get(taskKey="producer_task", key="last_run_id")
    ```
13. Replace the `job_cluster_key` (and the associated `job_clusters:` block) with a `compute` reference to a serverless config — or simply omit the cluster spec on a workspace where serverless tasks are enabled. The task then runs on Databricks-managed serverless compute.
14. **`databricks bundle validate`** — schema-checks the bundle without deploying.
15. **`databricks bundle deploy -t prod`** (or `--target prod`).
16. **`databricks bundle run orders_daily -t <target>`**.
17. In the task definition: `max_retries`, `min_retry_interval_millis`, and `retry_on_timeout` fields on the task. In `databricks.yml` under `resources.jobs.<job>.tasks[*].max_retries` etc.
18. **All-purpose clusters are roughly 3.6× the DBU price of job clusters** (some sources cite 2× — the spread depends on tier and DBR). Either way, all-purpose is intended for interactive notebook use, not scheduled production. Switching scheduled tasks to job clusters (or serverless) typically cuts cost by ~50% or more. ⚠️ **Exam trap:** For any "minimize cost of scheduled job" scenario, the answer is job cluster (or serverless if "hands-off" is in the prompt).
19. **Repair runs DO skip successful tasks by default** — repair reruns the failed task(s) and their downstream dependents only. If a successful task is being re-run, something else is happening: the user clicked "Run now" instead of "Repair run," or the failed task has `depends_on` pointing back to that successful task with a clear-state config. ⚠️ **Exam trap:** "Repair run" preserves partial state — that's the whole point.
20. **They didn't redeploy the bundle.** Editing local files doesn't push to the workspace until `databricks bundle deploy -t <target>` is run. The deployed artifact references the workspace copy. Fix: redeploy.
21. **`targets.prod.variables.catalog`** is missing or null, while `targets.dev.variables.catalog` is set. Either set it at the target level, or set a `default:` on the variable so all targets inherit it unless overridden.
22. **Data skew on that stage.** One task processed ~56× more data than the median, suggesting one partition (or join key) is far larger than the others. Diagnose: check the SQL/DataFrame tab for the operator, then look for a skewed join key. Fixes: AQE skew join, salting the key, or repartitioning by a more uniform column.
23. **Job clusters are 2–3.6× cheaper per DBU** than all-purpose, terminate at job end (no idle pay), and isolate workloads (no contention with interactive users). All-purpose is intended for interactive notebook use, not production. For any scheduled task, job cluster is the default-correct answer (serverless if "hands-off" is in the prompt).
24. **DABs:** declarative, version-controlled, idempotent across envs, supports variable substitution for environment-specific values, integrates with CI/CD, and rolls back cleanly with `databricks bundle destroy`. **Manual UI export:** non-reproducible, drift-prone, no version history, no parameterization, no rollback. The exam expects DAB as the answer in any "promote / CI/CD / multi-env" scenario.
