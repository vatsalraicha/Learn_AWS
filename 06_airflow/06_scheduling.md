# 06 — Scheduling deep: logical date, data interval, timetables, catchup, backfill, Datasets/Assets

## Why this module exists

Scheduling is the most-misunderstood part of Airflow. Get it right or wake up at 3am.

---

## 1. Logical date vs data interval

Critical distinction. For `schedule="@daily"` starting 2026-01-01:

| Field | Value for first run |
|---|---|
| `logical_date` | `2026-01-01T00:00:00` |
| `data_interval_start` | `2026-01-01T00:00:00` |
| `data_interval_end` | `2026-01-02T00:00:00` |
| Actual wall-clock execution | **`2026-01-02T00:00:00`** (after interval ends) |

A daily DAG "for 2026-01-01" runs **at the end** of 2026-01-01 — when that day's data is complete. Templates use `data_interval_start` (the logical "what day is this run about?").

This is why backfills work consistently: re-running logical_date=2026-01-01 processes the same data interval regardless of when it runs.

---

## 2. Schedule formats

- **Cron**: `"0 3 * * *"` — at 03:00 daily.
- **Preset**: `"@daily"`, `"@hourly"`, `"@weekly"`, `"@monthly"`, `"@yearly"`, `"@once"`.
- **Timedelta**: `timedelta(hours=4)` — every 4 hours from start_date.
- **List of Datasets**: `[dataset_A, dataset_B]` — run when ANY dataset updates.
- **Custom Timetable** (2.2+): for unusual schedules (business days, specific times).
- **None**: trigger-only DAGs.

---

## 3. Catchup — the source of "365 runs at once"

`catchup=True` (the historical default): on first deploy, Airflow runs every interval between `start_date` and now.

- DAG with `start_date=2025-01-01` + `schedule="@daily"` + `catchup=True` deployed today → ~500 runs queued.
- Recipe for disaster on a real warehouse.

**Always set `catchup=False` for new DAGs.** Use explicit backfills when needed (`airflow dags backfill`).

---

## 4. Backfill

```bash
airflow dags backfill -s 2026-01-01 -e 2026-01-31 sales_etl
```

Runs the DAG for each logical date in the range. Use for:
- Filling gaps from outages.
- Reprocessing data with corrected logic.
- Loading historical data on a new pipeline.

For large backfills: use `--reset-dagruns` carefully (deletes prior runs first); throttle with pools to avoid warehouse overload.

---

## 5. Custom Timetables (AIP-39)

For schedules cron can't express:

```python
from airflow.timetables.trigger import CronTriggerTimetable
from pendulum import timezone

@dag(
    timetable=CronTriggerTimetable("0 9 * * 1-5", timezone=timezone("America/New_York")),
    start_date=datetime(2026, 1, 1),
    catchup=False,
)
def weekday_morning_etl():
    ...
```

Business-day-only, NY timezone, 9am. CronTriggerTimetable handles DST.

For more complex schedules (e.g., "last business day of month"): write a custom Timetable subclass.

---

## 6. Dataset-driven scheduling (the modern way)

```python
ds_sales = Dataset("snowflake://prod.staging.sales")
ds_inventory = Dataset("snowflake://prod.staging.inventory")

# Producer
@dag(schedule="0 2 * * *", catchup=False)
def load_sales():
    @task(outlets=[ds_sales])
    def load(): ...

# Consumer — runs when BOTH datasets update
@dag(schedule=[ds_sales, ds_inventory], catchup=False)
def aggregate():
    @task
    def agg(): ...
```

The consumer DAG triggers when both datasets have been updated since the last run. Replaces cron-coordinated dependencies between DAGs.

Limitation: requires producer DAGs to declare `outlets=` on their final tasks. No automatic detection.

In Airflow 3.0: Datasets renamed to **Assets** with richer metadata (`@asset` decorator, more conditions).

---

## 7. `max_active_runs` + `max_active_tasks`

```python
@dag(
    max_active_runs=1,                  # only one run at a time per DAG
    max_active_tasks=10,                # max tasks running per run
    ...
)
```

For DAGs that touch a shared resource (e.g., Snowflake staging table) — `max_active_runs=1` prevents data races on backfills.

`max_active_tasks` (formerly `concurrency`) protects against fan-out blowing up the worker pool.

---

## 8. Schedule + DAG-run states

| State | Meaning |
|---|---|
| `queued` | Scheduled but no tasks yet started |
| `running` | At least one task is in progress |
| `success` | All tasks succeeded |
| `failed` | A task failed |
| `up_for_retry` | Task failed but will retry |
| `upstream_failed` | A predecessor failed |
| `skipped` | Branched away |

Failure propagation: a task failure marks downstream as `upstream_failed` unless `trigger_rule="all_done"` etc.

`trigger_rule` options: `all_success` (default), `all_failed`, `all_done`, `one_success`, `one_failed`, `none_failed`, `none_skipped`, `always`.

---

## 9. Time zones

Airflow stores all timestamps in UTC. Schedules can be specified in local zones via Timetables. Templates render in UTC by default.

Best practice: write all SQL/code in UTC; convert at the boundary (UI display, business reports).

---

## 10. The scheduling decision tree

```
Need to run when external data lands?
   → Dataset-driven schedule

Need to run on a fixed clock?
   → Cron string (UTC) or CronTriggerTimetable (with tz)

Need to run after another DAG?
   → Dataset (preferred) or ExternalTaskSensor

Need to run irregularly?
   → schedule=None + TriggerDagRunOperator from a controlling DAG / API

Need to run once for a one-shot migration?
   → schedule="@once", catchup=False
```

---

## Sanity check

1. For `schedule="@daily"` with `logical_date=2026-05-20`, when does the run actually start (wall-clock)?
2. Why is `catchup=False` the safe default for new DAGs?
3. Dataset-driven scheduling replaces what older pattern?
4. `max_active_runs=1` — when is this important?
5. CronTriggerTimetable handles what that a raw cron string doesn't?
6. The default `trigger_rule` is what, and what does it imply for branching?

---

## Sources

- [Scheduling and Timetables](https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/timetable.html)
- [Datasets and Data-aware scheduling](https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/datasets.html)
- [Backfill](https://airflow.apache.org/docs/apache-airflow/stable/dag-run.html#backfill)
- [AIP-39 Custom Timetables](https://cwiki.apache.org/confluence/display/AIRFLOW/AIP-39+Richer+scheduler_interval)

→ Next: [07 — Sensors & triggers](07_sensors_triggers.md)
