# Topic 13 — Databricks Certified Associate Developer for Apache Spark

> **Audience:** Senior AI/ML Engineer (Optum), 10+ years of PySpark in production. You write `groupBy().agg()` in your sleep — but the new (April 2025 relaunch) version of this exam tests **Spark Connect**, **Pandas API on Spark**, **Structured Streaming**, and **AQE internals** that even strong PySpark engineers stumble on. This corpus is calibrated for someone who needs a *refresh on Spark internals* and a *cold introduction to the new domains*, not a tutorial on `df.select()`.
>
> **Goal:** Pass the exam (45 questions / 90 minutes / ~70% threshold / $200 / 2-yr validity) on the first attempt, with confidence in every domain — including the ones a senior practitioner has never had to touch (Spark Connect deployment model, `pyspark.pandas` semantics).
>
> **Last updated:** 2026-05-23

---

## What this topic guarantees

If you study these 14 modules + 5 quiz files thoroughly:

- **Every verbatim objective** from the Oct 2025 exam guide is covered, with a `## Coverage map` header at the top of every module mapping objectives → section anchors.
- **Full PySpark 3.5 API surface** for: DataFrame methods (select, filter, withColumn, drop, distinct, sample, limit, sort, union/unionByName, join variants, groupBy/agg, window functions, na.drop/fill, sorting), Spark SQL functions (`F.col`, `F.lit`, `F.when/otherwise`, `F.coalesce`, date/time, string, array, struct, JSON, aggregation, ranking, lag/lead), I/O (Parquet, CSV, JSON, ORC, Delta-as-file, JDBC), tuning configs (AQE, broadcast threshold, shuffle partitions, file partition bytes), streaming (readStream/writeStream, output modes, triggers, watermarks, foreachBatch), Spark Connect (`sc://`, gRPC, restrictions), and Pandas-on-Spark (`pyspark.pandas`) plus the four Pandas UDF types.
- **All 10 official sample questions** walked through with distractor analysis (Module 14).
- **Look-alike comparison tables** for the canonical traps: `F.coalesce` function vs `df.coalesce(n)` method; `union` (position) vs `unionByName` (name); `repartition` vs `coalesce`; `distinct` vs `dropDuplicates`; `na.drop("any")` vs `na.drop("all")`; `sc.broadcast(value)` vs `F.broadcast(df)`; `row_number` vs `rank` vs `dense_rank`; `pyspark.pandas` vs `pandas_udf`; storage levels; AQE config keys vs distractors.
- **Output-prediction drills** (heavy emphasis on Modules 02, 05, 07, 08, 09, 10) — predict-then-verify exercises mirroring the exam's code-completion + output-prediction question patterns.
- **Decision-rule callouts** (`> 🎯 How to recognize this on the exam:`) in every module — exam-day decision logic to recognize question patterns.
- **End-to-end mini-scenarios** showing realistic small pipelines that exercise multiple objectives together.

Calibrated for someone who reads only these modules + takes the quizzes — no external resources required to pass.

---

## What's new — exam relaunched April 2025

This is **not** the old "Apache Spark 3.0 (Python)" exam. That one was retired. The new exam:

- **Spark 3.5** content (NOT Spark 4.0 — no ANSI-default, no Variant type, no collations, no Arbitrary Stateful Processing V2).
- **Python only.** The Scala track was removed — there is currently no Databricks-administered Scala Spark cert.
- **NOT Databricks-platform-specific.** Pure open-source Spark. No Unity Catalog, no Delta Lake-specific tooling (time travel, OPTIMIZE, ZORDER), no Databricks Workflows, no DBFS, no Photon. Delta is mentioned only as a *readable file format* via `delta.`path``.
- **45 questions in 90 minutes** (was 60Q / 120 min in the legacy 3.0 exam). About 2 min/question.
- **7 domains** (was ~3 in the legacy version). Three brand-new domains: Structured Streaming, Spark Connect, Pandas API on Spark.

If you took the 3.0 version years ago, treat this as a different exam. The 50% you already know will be muscle memory; the other 50% requires deliberate study.

---

## Exam logistics

| Attribute | Value |
|---|---|
| **Official name** | Databricks Certified Associate Developer for Apache Spark |
| **Question count** | 45 scored (plus a few unscored statistical items, time-adjusted) |
| **Duration** | 90 minutes |
| **Passing score** | Not publicly disclosed; community-reported **~70%** (treat as floor; aim for 85%+) |
| **Cost** | **$200 USD** + local taxes |
| **Language (exam UI)** | English |
| **Language (code)** | **Python only** — every snippet is PySpark |
| **Spark version** | **3.5.x** (with Spark Connect features from 3.4) |
| **Delivery** | Online proctored OR test-center |
| **Prerequisites** | None; Databricks suggests 6+ months hands-on |
| **Validity** | **2 years** — recertify by retaking the current exam |
| **Test aides** | None — no API docs, no scratch paper, no calculator |
| **Registration** | Webassessor (webassessor.com/databricks) |
| **Results** | Immediate pass/fail + per-section percentage breakdown |

---

## Domain weights — the map

| # | Domain | Weight | ~Qs (of 45) | Module(s) |
|---|--------|--------|-------------|-----------|
| 1 | **Apache Spark Architecture & Components** | **20%** | ~9 | [01](01_spark_architecture.md), [02](02_lazy_evaluation_dag.md), [03](03_execution_model.md) |
| 2 | **Using Spark SQL** | **20%** | ~9 | [04](04_spark_sql_basics.md), [05](05_spark_sql_functions.md) |
| 3 | **Developing DataFrame/Dataset API Applications** | **30%** ← largest | ~14 | [06](06_dataframe_basics.md), [07](07_dataframe_transformations.md), [08](08_aggregations_window.md), [09](09_joins_unions.md) |
| 4 | **Troubleshooting & Tuning** | **10%** | ~5 | [10](10_performance_tuning.md) |
| 5 | **Structured Streaming** | **10%** (new) | ~5 | [11](11_structured_streaming.md) |
| 6 | **Spark Connect — Deploy Applications** | **5%** (new) | ~2 | [12](12_spark_connect.md) |
| 7 | **Pandas API on Spark** | **5%** (new) | ~2 | [13](13_pandas_api_on_spark.md) |
| | **Synthesis & official sample walk-through** | | | [14](14_official_sample_questions_walkthrough.md) |
| | **TOTAL** | 100% | 45 | |

**Senior-engineer ROI ranking** — where 2-3 weeks of study buys the most points:
1. **AQE internals & config keys** (Module 10) — almost every senior I've trained gets the AQE config-key trap wrong.
2. **Structured Streaming** (Module 11) — if you haven't built a streaming job in the last 2 years, this is your weak spot.
3. **Spark Connect** (Module 12) — totally new surface; 2 questions but easy to get both right with 1 hour of focused study.
4. **Pandas API on Spark vs Pandas UDFs** (Module 13) — these are *different things* and the exam will trick you.
5. **Narrow vs wide transformations edge cases** (Module 02) — `union` is narrow; people get this wrong.

---

## Learning path — 14 modules

### Domain 1 — Architecture (20%)
1. [`01_spark_architecture.md`](01_spark_architecture.md) — Driver, executor, cluster manager (standalone/YARN/K8s), JVM processes, tasks-per-core, SparkContext vs SparkSession.
2. [`02_lazy_evaluation_dag.md`](02_lazy_evaluation_dag.md) — Transformations vs actions, lineage, Catalyst, DAG scheduler, narrow vs wide (the full list), shuffle boundaries.
3. [`03_execution_model.md`](03_execution_model.md) — Application → Job → Stage → Task; shuffle write/read; spill to disk; speculative execution; dynamic allocation.

### Domain 2 — Spark SQL (20%)
4. [`04_spark_sql_basics.md`](04_spark_sql_basics.md) — SQL queries, `createTempView` vs `createOrReplaceTempView` vs global temp view, catalog, `spark.sql()` returning a DataFrame, pivot/unpivot, querying files directly.
5. [`05_spark_sql_functions.md`](05_spark_sql_functions.md) — `cast`, `lit`, `when().otherwise()`, the *function* `coalesce` vs the *DataFrame method* `.coalesce()`, `expr`, `broadcast`, date functions, regex, arrays, structs, JSON, `withColumn` vs `withColumnRenamed`.

### Domain 3 — DataFrame / Dataset API (30%) — largest section
6. [`06_dataframe_basics.md`](06_dataframe_basics.md) — Reading (CSV, JSON, Parquet, Delta, ORC, Text), writing, save modes, schemas (`inferSchema` vs explicit StructType vs DDL string), `partitionBy` vs `bucketBy`.
7. [`07_dataframe_transformations.md`](07_dataframe_transformations.md) — `select`, `selectExpr`, `filter`/`where`, `withColumn`/`withColumnRenamed`, `drop`, `distinct` vs `dropDuplicates`, `sample`, `limit`, `sort`/`orderBy`, chaining discipline.
8. [`08_aggregations_window.md`](08_aggregations_window.md) — `groupBy().agg()`, `pivot`, `approx_count_distinct`, Window functions (`partitionBy`/`orderBy`/`rowsBetween`/`rangeBetween`), `row_number`/`rank`/`dense_rank`/`percent_rank`/`cume_dist`/`lag`/`lead`.
9. [`09_joins_unions.md`](09_joins_unions.md) — Join types (inner/left/right/full outer/semi/anti/cross), broadcast joins and their *outer-join restrictions*, `union` (narrow!) vs `unionByName` (by name), multi-key joins.

### Domain 4 — Tuning (10%)
10. [`10_performance_tuning.md`](10_performance_tuning.md) — AQE three pillars + the **config-key naming trap**, broadcast thresholds (planner vs runtime), partition tuning (`repartition` vs `coalesce` vs `sortWithinPartitions`), cache vs persist & storage levels, predicate pushdown, partition pruning, file-format choice, bucketing, skew (salting, AQE skew join).

### Domain 5 — Structured Streaming (10%)
11. [`11_structured_streaming.md`](11_structured_streaming.md) — `readStream`/`writeStream`, triggers (default, `processingTime`, `availableNow`, `once` deprecated), output modes (append, complete, update) decision tree, `checkpointLocation`, watermarks + `dropDuplicates`, `foreachBatch`, exactly-once semantics.

### Domain 6 — Spark Connect (5%)
12. [`12_spark_connect.md`](12_spark_connect.md) — Client-server architecture, gRPC protocol, `SparkSession.builder.remote("sc://...")`, deployment modes (client/cluster/local — *local-mode = single worker node* is on the exam), restrictions (no RDD API, no SparkContext, no client-side broadcast variables).

### Domain 7 — Pandas API on Spark (5%)
13. [`13_pandas_api_on_spark.md`](13_pandas_api_on_spark.md) — `import pyspark.pandas as ps`, semantics vs real pandas (no in-place ops by default, index handling), conversion (`to_pandas`/`from_pandas`/`to_spark`), `pandas_udf` (4 types — scalar, scalar-iter, grouped-map, grouped-agg), when to choose which.

### Synthesis
14. [`14_official_sample_questions_walkthrough.md`](14_official_sample_questions_walkthrough.md) — Walk through the 10 official sample questions (paraphrased per NDA) with full reasoning, including back-references to source modules. **Do this last.**

---

## Companion files

- [`FACTS.md`](FACTS.md) — atomic citable claims (exam logistics, version dates, config keys, defaults, storage levels). Single source of truth, updated whenever a fact gets re-verified.
- [`quizzes/`](quizzes/) — 5 quiz files, ~135 questions total (45 × 3 — three full mock-exam volumes' worth, distributed by domain weight):
  - [`01_architecture.md`](quizzes/01_architecture.md) — 27 questions (20%)
  - [`02_spark_sql.md`](quizzes/02_spark_sql.md) — 27 questions (20%)
  - [`03_dataframe_api.md`](quizzes/03_dataframe_api.md) — 40 questions (30%)
  - [`04_tuning.md`](quizzes/04_tuning.md) — 14 questions (10%)
  - [`05_streaming_connect_pandas.md`](quizzes/05_streaming_connect_pandas.md) — 27 questions (10+5+5%)
  - [`README.md`](quizzes/README.md) — usage, scoring, recommended cadence.

---

## How to use this

1. **First pass (read-through):** Modules 01 → 13 in order. ~6–8 hours for a senior practitioner. Skip nothing — the "obvious" sections often hide the exam-trap details.
2. **Module quizzes:** After each module, take the corresponding quiz **cold** (no peeking). Track your score per domain.
3. **AQE & Streaming deep dive:** Re-read Modules 10 and 11. These are the points-per-hour goldmines.
4. **Walk-through:** Module 14 — work through the 10 official samples without looking at answers first.
5. **Mock exam:** Combine 45 questions across the quizzes (proportional by weight) and take it under timed conditions. Score yourself. Anything below 80% in a domain → revisit that module.
6. **Re-take quizzes** at 70%+ before scheduling. Aim for 85%+ on full-set practice before booking.

---

## Estimated time investment (senior PySpark engineer)

| Phase | Hours |
|---|---|
| Read-through Modules 01–14 | 8–10 |
| Take all quizzes cold, review wrong answers | 6–8 |
| AQE + Streaming + Spark Connect deep dive (Modules 10, 11, 12) | 4–6 |
| Pandas-on-Spark hands-on (Module 13) | 2 |
| Mock exam(s) under timed conditions | 3–4 |
| Final review of FACTS.md + official guide PDF | 2 |
| **Total** | **25–32 hours over 2–3 weeks** |

If you've shipped PySpark code in the last 6 months, you'll lean toward the low end. If your last Spark touch was 2 years ago, lean toward the high end and add 5–10 hours for hands-on warm-up.

---

## Source-of-truth ordering

When two sources disagree, trust in this order:

1. **The official Oct 2025 exam guide PDF** (`research_inputs/13_databricks_spark_dev_associate/databricks_spark_dev_associate_exam_guide.pdf`).
2. **Apache Spark 3.5.0 documentation** (`spark.apache.org/docs/3.5.0/`).
3. **Databricks certification page** (`databricks.com/learn/certification/apache-spark-developer-associate`).
4. **Community write-ups** (Medium, Reddit) — useful for exam-day flavor but never for technical truth.
5. **Practice-dump sites** (ExamTopics etc.) — assume they're showing the OLD 3.0 exam questions mislabeled as 3.5. Use ONLY if you can cross-verify against the official guide.

---

## Scope notes

- **No NDA violations.** All sample-question content in Module 14 and the quizzes is paraphrased from the official guide's *publicly published* 10 sample questions, or original questions derived from the verbatim exam objectives.
- **Spark 3.5 only.** No Spark 4.0 features (ANSI default, Variant, collations) are tested or covered.
- **No Databricks-platform UI.** This is a pure-Spark exam. Module references to Databricks-specific features (e.g., Liquid Clustering, Photon) appear only as *exclusions* — "this is NOT tested."
- **Python-only code.** All examples in PySpark. Spark SQL examples are SQL strings passed to `spark.sql()`, never Scala.

---

## What I'm not covering (and why)

- **Spark Streaming (DStreams)** — legacy API, not on the exam; Structured Streaming replaces it.
- **MLlib** — mentioned by the exam guide as one of "the modules of Spark," but no MLlib code or concepts are tested beyond the existence of the module.
- **GraphX** — not tested.
- **Spark 4.0 features** — exam predates broad 4.0 adoption.
- **Databricks-platform features** — Unity Catalog, Delta Lake-specific operations, Photon, Workflows, DBSQL warehouses. See Topic 02 (Azure Databricks) for those.
