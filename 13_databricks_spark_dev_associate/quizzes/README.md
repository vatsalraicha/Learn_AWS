# Quizzes — Databricks Certified Associate Developer for Apache Spark

> 135 questions across 5 files, weighted to match exam domain proportions.
>
> **All questions are ORIGINAL** — derived from the verbatim exam objectives and the 10 publicly-published sample questions. No NDA-violating content.

---

## Files and weights

| File | Topics | Q count | Domain weight |
|---|---|---|---|
| [`01_architecture.md`](01_architecture.md) | Spark architecture, DAG, execution model | 27 | 20% |
| [`02_spark_sql.md`](02_spark_sql.md) | Spark SQL basics + SQL functions | 27 | 20% |
| [`03_dataframe_api.md`](03_dataframe_api.md) | DataFrame transformations, aggregations, joins | 40 | 30% |
| [`04_tuning.md`](04_tuning.md) | AQE, partitioning, caching, skew, Spark UI | 14 | 10% |
| [`05_streaming_connect_pandas.md`](05_streaming_connect_pandas.md) | Streaming, Spark Connect, Pandas API | 27 | 20% (10+5+5) |
| **Total** | | **135** | **100%** |

Three full mock-exam volumes' worth (45 × 3 = 135).

---

## Format

Each file is organized into four cognitive levels:

- **Recall** — fact lookup (e.g., "What's the default `spark.sql.shuffle.partitions`?").
- **Apply** — code identification, expected output (e.g., "Which code block accomplishes X?").
- **Diagnose** — given a symptom, identify the cause (e.g., "Why is task #5 taking 10× longer than others?").
- **Defend** — best-practice reasoning (e.g., "When would you use `coalesce` over `repartition`?").

The actual exam mixes these patterns; train across all four.

---

## How to use

1. **Cold first pass.** Take each quiz without referring to modules or FACTS.md. Time yourself: ~2 min/question (matches exam pace).
2. **Score yourself.** Compute % correct. Below 70% → revisit the corresponding module.
3. **Review wrong answers.** For each, find the underlying concept and cross-reference the module.
4. **Second pass 1 week later.** Should be 85%+ to be ready.
5. **Final mock**: pick 45 questions random from across the 5 files (proportional to weight) and take under timed conditions.

---

## Scoring guidance

| Score across all 135 | Readiness |
|---|---|
| 90%+ | Confident pass; book within 1-2 weeks |
| 80-89% | Pass likely; targeted review of weak domains |
| 70-79% | Risk zone — revisit modules where you scored < 75% |
| < 70% | Not ready; 1+ more week of study |

The actual exam pass mark is ~70% (community-reported, unconfirmed). Aim for 85%+ on practice to have margin for exam-day nerves.

---

## Honest disclaimers

- These questions are **not the real exam** and not equivalent to "exam dumps."
- They test the **same concepts at the same depth** as the official sample Qs.
- The actual exam may use slightly different phrasings or distractors.
- If you can answer 135 of these cleanly with explanations, you understand the material — that's the real goal.
- No memorization shortcuts: the exam is conceptual, not trivia-based.

Good luck.
