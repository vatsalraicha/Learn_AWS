# Quizzes — Topic 09 Databricks Certified ML Associate

> ~145 original practice questions across 5 quiz files, mapped to the four exam domains. Use these to drill recognition speed and catch weak areas before exam day.

---

## Quiz files and weights

| File | Domain | Questions | Exam weight |
|------|--------|----------:|-----------:|
| [`01_databricks_ml.md`](01_databricks_ml.md) | Domain 1 — Databricks ML | ~55 | **38%** |
| [`02_ml_workflows.md`](02_ml_workflows.md) | Domain 2 — ML Workflows / Data Processing | ~28 | **19%** |
| [`03_model_development.md`](03_model_development.md) | Domain 3 — Model Development | ~45 | **31%** |
| [`04_model_deployment.md`](04_model_deployment.md) | Domain 4 — Model Deployment | ~17 | **12%** |
| **Total** | All four | **~145** | 100% |

The total is ~3× exam length (48 questions). Use the surplus for re-takes after weak-area review.

---

## How to take a quiz

1. **Cold.** No peeking at modules, no Google, no notes. Treat it like the real exam.
2. **Timed.** Budget **1m 52s per question** (the real exam's per-question pace). For a 28-question quiz: 28 × 1m52s ≈ **52 minutes**.
3. **Don't read answers until you've completed the full quiz.** Resist the urge to check after each question.
4. **Score yourself** using the rubric below.
5. **Read every answer explanation** — even on questions you got right. The explanation often surfaces a trap or alternate phrasing you'll see on a real exam.
6. **Mark failed questions.** Re-take them 48 hours later (memory consolidation).

---

## Question style — what each section tests

Every quiz file is structured into four sections:

| Section | % of questions | Skill tested |
|---------|---------------:|--------------|
| **Recall** | ~30% | Direct fact retrieval — API names, signatures, dates, definitions |
| **Apply** | ~40% | Read a code snippet or scenario, pick the right action |
| **Diagnose** | ~20% | Given a symptom, identify the root cause |
| **Defend** | ~10% | Justify a design decision or argue against a wrong approach |

The real exam leans **Apply + Diagnose**. Don't be alarmed if Recall feels easy — it should. Apply + Diagnose is where the exam separates passers from non-passers.

---

## Scoring rubric

Each question is worth 1 point regardless of section. Compute:

```
score % = (correct / total) × 100
```

| Score | Interpretation |
|-------|----------------|
| **≥85%** | Comfortable pass. Schedule the exam. |
| **70–84%** | Likely pass with some risk. Drill weak domain(s) before scheduling. |
| **55–69%** | Not ready. Re-read modules for the lowest-scoring domain; re-take 48 hours later. |
| **<55%** | Several weak domains. Re-read all modules; re-take in 1 week. |

The official passing threshold is widely cited as 70%, but Databricks doesn't publish it. **Aim for 85%+** on practice to give yourself margin against scaled scoring and exam-day pressure.

---

## What 70% looks like (the real-exam math)

- 48 questions × 70% = **33.6 → you need 34 correct, can miss 14**.
- 14 wrong answers out of 48 = roughly **3 missed per domain** on average.
- If you find yourself routinely missing 4+ in one domain on practice, that's your weakness — drill it.

---

## Drill plan for weak areas

If you fail a quiz (<70%):

1. **Identify the section.** Were misses concentrated in Recall (fact gaps), Apply (can't operationalize), Diagnose (don't see the trap), or Defend (don't know the framework)?
2. **Re-read the relevant modules.** Don't skim — slow read with attention to "Exam trap" callouts.
3. **Cross-check `FACTS.md`.** That file is the single source of truth for citable claims and API signatures.
4. **Wait 48 hours, then re-take.** Spaced repetition is real.

For domain-specific weak areas:

| Weak domain | Modules to re-drill | Practice focus |
|-------------|---------------------|----------------|
| Domain 1 (Databricks ML) | 01, 02, 03, 04, 05 | UC FE Client vs FS Client, MLflow `search_runs`, alias promotion |
| Domain 2 (ML Workflows) | 06, 07, 08 | `summary` vs `describe`, OHE-needed-or-not, log transform |
| Domain 3 (Model Dev) | 09, 10, 11, 12 | Hyperopt `fmin` syntax, CV model-count math, metric choice |
| Domain 4 (Deployment) | 13, 14 | Batch UDF vs streaming DLT vs Model Serving distinction |

---

## Common traps that recur across quizzes

These show up multiple times. Internalize them:

1. **`FeatureEngineeringClient` (UC) vs `FeatureStoreClient` (legacy).** Always pick the UC variant for new code.
2. **UC Registry aliases, not stages.** No `transition_model_version_stage` in UC.
3. **`hp.choice` returns the INDEX**, not the value. Use `space_eval`.
4. **`order_by` direction in `search_runs`** — `DESC` to maximize, `ASC` to minimize.
5. **`SparkTrials` is for single-node models** — NOT for Spark ML estimators.
6. **`describe()` lacks percentiles**; `summary()` includes them.
7. **OHE is unnecessary for tree-based models.**
8. **Median imputation is the safer default** for skewed data.
9. **Exponentiate log-transformed predictions** before computing RMSE/MAE on original scale.
10. **`SparkTrials` does double-parallelization** when used on Spark ML — don't do it.
11. **CV trains `grid_size × k` models** (plus 1 refit).
12. **Traffic percentages on Model Serving must sum to 100.**
13. **"Tens of thousands of events/sec" → DLT, NOT Model Serving.**
14. **For imbalanced binary classification, `weightCol` is the Databricks-preferred technique** when it's an option.
15. **`F1` for imbalanced classification**, not accuracy.

---

## After you pass the quizzes

When you score 85%+ across all four quizzes:

1. **Re-take all four back-to-back in 90 minutes.** This is your dress rehearsal for the timed real exam.
2. **Sleep well before the exam.** Cognitive performance on multiple-choice is sleep-sensitive.
3. **Skim `FACTS.md` the morning of the exam.** Just the API signatures and version cutoffs. Don't try to learn anything new.
4. **Don't take new practice exams the day before** — they introduce noise.

Good luck. The exam is 48 questions in 90 minutes; you've practiced 145 questions across these quizzes plus 14 modules of conceptual depth. You're ready.
