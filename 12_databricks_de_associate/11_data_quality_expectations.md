# Module 11 — Data Quality with Expectations

> **Domain 3 (31%) — Data Processing & Transformations**
> **Domain 5 (11%) — Data Governance & Quality**
>
> **What you must walk away with:** All three expectation actions and their decorators. Multi-expectation grouping with `expect_all`. The quarantine pattern. How to query expectation violations from the event log. When to use a row filter / column mask vs an expectation.

---

## Coverage map (verbatim July 25, 2025 objectives → where taught here)

| Verbatim objective | Taught in section |
|---|---|
| Implement data pipelines using LDP (data-quality layer) | §1 what expectations are; §2 the three actions; §3 Python decorator forms + `expect_all*` group decorators; §4 quarantine pattern |
| Identify DDL features (CONSTRAINT … EXPECT … ON VIOLATION DROP ROW / FAIL UPDATE) | §2 SQL forms + §3 decorator ↔ SQL mapping |
| Use lineage / debug tools to query violations | §5 "Inspecting violations via the event log" (`event_log('<pipeline_id>')`) |
| Distinguish expectations from UC row filters / column masks | §6 "Expectations are NOT row filters / column masks" |
| Identify DDL features (Delta CHECK constraint vs LDP expectation) | §7 "Constraints vs expectations" |

Cross-references: Module 10 for the LDP framework that owns expectations; Module 15 for UC row filters / column masks / dynamic views (the access-control side); Module 14 for the event-log monitoring layer.

---

## 1. What expectations are

Expectations are **declarative data-quality constraints** attached to LDP tables. Each expectation is:

- A **name** (used in the event log to identify which rule failed).
- A **boolean SQL expression** evaluated per row.
- An **action** on violation.

```sql
CREATE OR REFRESH STREAMING TABLE main.silver.orders (
  CONSTRAINT valid_id        EXPECT (order_id IS NOT NULL)        ON VIOLATION DROP ROW,
  CONSTRAINT positive_amount EXPECT (amount > 0)                  ON VIOLATION FAIL UPDATE,
  CONSTRAINT recent_date     EXPECT (order_ts >= '2020-01-01')
)
AS SELECT * FROM STREAM(LIVE.bronze_orders);
```

Three rules attached to one table. Each handles violations differently.

---

## 2. The three actions

### 2.1 Default — warn (no `ON VIOLATION` clause)

```sql
CONSTRAINT recent_date EXPECT (order_ts >= '2020-01-01')
```

- Row is **kept** in the output.
- Violation count is **logged** in the pipeline event log.
- No effect on pipeline success.

Use when: you want visibility into quality issues without changing the data flow.

### 2.2 DROP ROW

```sql
CONSTRAINT valid_id EXPECT (order_id IS NOT NULL) ON VIOLATION DROP ROW
```

- Violating rows are **dropped** from the output.
- Violation count is logged.
- Pipeline continues.

Use when: bad rows are unfixable and shouldn't pollute downstream tables.

### 2.3 FAIL UPDATE

```sql
CONSTRAINT positive_amount EXPECT (amount > 0) ON VIOLATION FAIL UPDATE
```

- If any row violates, the **entire pipeline update fails** — no rows written.
- The pipeline can be repaired and re-run.

Use when: a violation indicates a systemic issue that requires human intervention.

### Decision table

| Severity of violation | Action |
|----------------------|--------|
| "Nice to know, doesn't block" | default (warn) |
| "Bad row, exclude from analytics" | DROP ROW |
| "Pipeline is broken if this fires; humans must look" | FAIL UPDATE |

---

## 3. Python decorator form

```python
from pyspark import pipelines as dp

@dp.table
@dp.expect("valid_id", "order_id IS NOT NULL")                       # warn
@dp.expect_or_drop("positive_amount", "amount > 0")                  # drop
@dp.expect_or_fail("recent_date", "order_ts >= '2020-01-01'")        # fail
def silver_orders():
    return (dp.read_stream("bronze_orders")
              .select("order_id", "customer_id", "amount", "order_ts"))
```

| Decorator | Equivalent SQL |
|-----------|---------------|
| `@dp.expect(name, cond)` | `CONSTRAINT name EXPECT (cond)` |
| `@dp.expect_or_drop(name, cond)` | `… ON VIOLATION DROP ROW` |
| `@dp.expect_or_fail(name, cond)` | `… ON VIOLATION FAIL UPDATE` |

### Multi-expectation forms

```python
@dp.table
@dp.expect_all({
    "valid_id": "order_id IS NOT NULL",
    "positive_amount": "amount > 0",
    "recent_date": "order_ts >= '2020-01-01'"
})
def silver_orders():
    return dp.read_stream("bronze_orders")

# Or with DROP semantics on all:
@dp.expect_all_or_drop({...})

# Or with FAIL semantics on all:
@dp.expect_all_or_fail({...})
```

Compactly express many rules at once.

---

## 4. Quarantine pattern — capture bad rows separately

```sql
-- Main table drops bad rows
CREATE OR REFRESH STREAMING TABLE main.silver.orders
  (CONSTRAINT valid_id EXPECT (order_id IS NOT NULL) ON VIOLATION DROP ROW)
AS SELECT * FROM STREAM(LIVE.bronze_orders);

-- Quarantine table collects the bad rows
CREATE OR REFRESH STREAMING TABLE main.quarantine.orders_invalid
AS SELECT * FROM STREAM(LIVE.bronze_orders)
   WHERE order_id IS NULL;
```

Why split: the main table stays clean for downstream consumers; the quarantine table is reviewable by humans / sent to a remediation queue.

Variant — single source table, two outputs via a "tag" column:

```sql
CREATE OR REFRESH STREAMING TABLE main.silver.orders_tagged
AS SELECT
    *,
    CASE
      WHEN order_id IS NULL THEN 'invalid_missing_id'
      WHEN amount <= 0      THEN 'invalid_amount'
      ELSE 'valid'
    END AS validity
   FROM STREAM(LIVE.bronze_orders);

CREATE OR REFRESH MATERIALIZED VIEW main.silver.orders
AS SELECT * EXCEPT(validity) FROM LIVE.orders_tagged WHERE validity = 'valid';

CREATE OR REFRESH MATERIALIZED VIEW main.quarantine.orders
AS SELECT * FROM LIVE.orders_tagged WHERE validity != 'valid';
```

---

## 5. Inspecting violations via the event log

```sql
SELECT
  timestamp,
  details:flow_progress.metrics.num_output_rows AS output_rows,
  details:flow_progress.data_quality.expectations
FROM event_log('<pipeline_id>')
WHERE event_type = 'flow_progress'
ORDER BY timestamp DESC
LIMIT 20;
```

The `expectations` field is a list with per-rule:
- `name` — the CONSTRAINT name.
- `dataset` — which table the expectation is on.
- `passed_records` — how many rows passed.
- `failed_records` — how many violated.

You can build a dashboard on the event log to monitor quality trends.

### ⚠️ Exam trap — silent drops aren't actually silent

A common misconception: "DROP ROW silently loses data, so I can't tell what was dropped." False — every drop increments the failed_records counter in the event log. You don't see the **rows themselves**, but you see the **count** and can correlate with the quarantine pattern if needed.

---

## 6. Expectations are NOT row filters / column masks

Three different mechanisms, often confused:

| Feature | What | When applied | Domain |
|---------|------|--------------|--------|
| **Expectation** | Quality check on incoming rows in LDP | At LDP table compute time | Data quality (DE) |
| **Row filter** (UC) | Restrict which rows a user sees | At query time, per user | Access control (Governance) |
| **Column mask** (UC) | Replace a column's value for some users | At query time, per user | Access control (Governance) |
| **Dynamic view** | View that conditionally exposes columns | At query time, per user | Access control (Governance) |

The exam tests recognition of which mechanism applies:
- "Validate `order_id` is not null at ingestion" → **Expectation**.
- "Hide `ssn` from non-HR users" → **Column mask** or dynamic view (Module 15).
- "Restrict EU users to EU rows" → **Row filter** or dynamic view (Module 15).

### ⚠️ Exam trap — expectation vs row filter

Expectations operate on the **write** side (during LDP table compute). Row filters operate on the **read** side (per-user query). Don't pick "expectation" for an access-control question.

---

## 7. Constraints vs expectations

Delta has SQL CHECK constraints:

```sql
ALTER TABLE main.silver.orders
ADD CONSTRAINT positive_amount CHECK (amount > 0);
```

- A Delta CHECK constraint causes the **write to fail** if any row violates.
- Applies in any write (not just LDP).
- Cannot be conditional (drop vs fail).

vs. LDP expectations:
- LDP expectations can drop, warn, or fail.
- LDP expectations are queryable in the event log with counts.
- LDP expectations are declarative inside LDP DDL.

For the DE Associate exam, **expectations** is the answer for LDP data-quality questions. CHECK constraints are a Delta feature that complements but doesn't replace expectations.

---

## 8. Putting it together — Bronze → quality-checked Silver

```sql
-- Bronze: keep everything, including bad rows
CREATE OR REFRESH STREAMING TABLE main.bronze.orders
AS SELECT *,
          _metadata.file_path AS source_file,
          current_timestamp() AS ingest_ts
   FROM STREAM read_files('/Volumes/main/landing/orders/', format => 'json');

-- Silver: drop NULL IDs, drop non-positive amounts, fail on stale dates
CREATE OR REFRESH STREAMING TABLE main.silver.orders (
  CONSTRAINT valid_id        EXPECT (order_id IS NOT NULL)        ON VIOLATION DROP ROW,
  CONSTRAINT positive_amount EXPECT (amount > 0)                  ON VIOLATION DROP ROW,
  CONSTRAINT recent          EXPECT (order_ts >= '2020-01-01')    ON VIOLATION FAIL UPDATE,
  CONSTRAINT valid_customer  EXPECT (customer_id RLIKE '^[A-Z0-9]+$')  -- warn only
)
AS SELECT
     order_id,
     customer_id,
     CAST(amount AS DECIMAL(18,2)) AS amount,
     TO_TIMESTAMP(order_ts)       AS order_ts,
     ingest_ts
   FROM STREAM(LIVE.bronze_orders);

-- Quarantine: capture the dropped rows for review
CREATE OR REFRESH STREAMING TABLE main.quarantine.orders
AS SELECT * FROM STREAM(LIVE.bronze_orders)
   WHERE order_id IS NULL OR CAST(amount AS DECIMAL(18,2)) <= 0;
```

---

## 9. Mini quiz (cold)

1. Which expectation action drops violating rows but keeps the pipeline running?
2. Which expectation action fails the entire pipeline?
3. Which action keeps the row and just logs the violation?
4. The Python decorator for "drop violating rows" is `@dp.expect_or_???`. Fill in.
5. Where do you query expectation violation counts after a pipeline run?
6. You want to hide `ssn` from non-HR users at query time. Is this an expectation or a column mask?
7. You want to ensure `customer_id` is never null at ingestion. Is this an expectation or a column mask?
8. Difference between Delta CHECK constraint and LDP expectation?

### Answers

1. **`ON VIOLATION DROP ROW`** (decorator: `@dp.expect_or_drop`).
2. **`ON VIOLATION FAIL UPDATE`** (decorator: `@dp.expect_or_fail`).
3. **Default** — no `ON VIOLATION` clause (decorator: `@dp.expect`).
4. **`@dp.expect_or_drop`**.
5. **The pipeline event log**: `SELECT * FROM event_log('<pipeline_id>') WHERE event_type = 'flow_progress'` and look at the `expectations` field.
6. **Column mask** (or dynamic view) — applies at query time per user. Not an expectation.
7. **Expectation** — quality check at ingestion / LDP compute.
8. **CHECK constraint** fails the write (always); applies to any Delta write. **Expectation** can drop / warn / fail, only applies inside LDP DDL, and is queryable in the event log.

---

## 10. Sanity check before moving on

You should be able to:
- Recite the three expectation actions and decorators.
- Pick expectation for quality-at-ingestion questions and column mask / row filter for access-control questions.
- Describe the quarantine pattern.
- Know that violations are visible in `event_log(<pipeline_id>)`.

If any of those are fuzzy, re-read Sections 2, 4, and 6.
