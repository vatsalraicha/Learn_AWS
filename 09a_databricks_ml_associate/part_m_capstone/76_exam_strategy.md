# Chapter 76 — Exam-Day Strategy and Self-Assessment

> **Goal of this chapter:** to translate knowledge into a pass. A curriculum that does not help you actually pass the exam fails its first-order purpose, and knowledge is necessary but not sufficient — exam mechanics matter. The 90-minute window has its own rhythm, the question patterns reward fluency more than depth, and there are systematic time-wasters that even prepared candidates fall into. This chapter covers what to do in the two weeks before the exam, on the morning of, and during the 90 minutes — plus a self-assessment checklist of 35 questions you should be able to answer cold, with the curriculum chapter mapped against each one so that any gap points you back to the right page.

---

## 76.1 The shape of the exam

From the RESEARCH.md synthesis: **48 scored questions, 90 minutes, ~$200, passing score ~70%**. Multi-choice and a small number of multi-select. Online proctored via **Kryterion WebAssessor** with a webcam. No test aides allowed. The calculator is built into the WebAssessor interface — you do not need a physical one. Code that appears in questions is in **Python**; SQL appears only for non-ML data manipulation. The certification is valid for **two years**.

Time per question: **48 questions in 90 minutes is 1 minute 52 seconds per question** on average. Some questions are 4-6 line scenarios that you can read in 20 seconds and answer in another 20; some are code-completion questions that demand a careful look. The pace is not crushing but it is not generous either — a single 5-minute rabbit hole on one question costs you the time you needed for three other ones.

If you fail, there is a **mandatory 14-day waiting period** before you can retake, and a full **$200 retake fee** every time. No free vouchers. Plan as if you only get one attempt; the retake is your safety net, not your plan.

---

## 76.2 Domain weights — where to overweight your last-week review

| Domain | Section name (PDF) | Weight | Approx. questions |
|---|---|---:|---:|
| 1 | Databricks Machine Learning | **38%** | ~18 |
| 2 | Data Processing / ML Workflows | **19%** | ~9 |
| 3 | Model Development | **31%** | ~15 |
| 4 | Model Deployment | **12%** | ~6 |

Two practical implications. First, **the Databricks-specific domain (1) is the single largest** — UC Feature Engineering, MLflow tracking, UC Model Registry with aliases, AutoML. If you only have one day left and you have not nailed these APIs cold, drill them. The curriculum chapters that bear on this domain are Part L (Chapters 68-74) and the capstone (Chapter 75). Second, **deployment is the smallest at 12%** — about six questions. You cannot afford to skip it (those six questions can be the difference between 68% and 80%) but you also do not want to over-invest at the expense of domains 1 and 3.

Within Domain 3 (Model Development, 31%), the most heavily-tested sub-topics — based on the published sample questions and the recurring patterns in the question banks — are:

- Hyperopt `fmin` mechanics and `hp.choice` index trap.
- The G × F + 1 model-count math for grid search with cross-validation.
- Choosing the right metric for an imbalanced or log-transformed problem.
- Identifying estimator-versus-transformer correctly in a pyspark.ml Pipeline.
- Class imbalance mitigation (class weights, threshold tuning).

Drill those. They are high-yield.

---

## 76.3 Two weeks out

Read all 76 chapters end-to-end. Do not skip. The first time through this curriculum was learning; this second pass is *consolidation* — you are looking for connections you missed the first time, and you are noticing which chapters' material has gone fuzzy.

Do every exercise. Where you cannot answer an exercise cold, re-read the chapter the exercise was attached to. Exercises are calibration: they tell you whether the chapter actually landed. A chapter you read and felt you understood, but whose exercises you fluffed, has not actually landed — go back.

Two-week budget: roughly 30-40 hours of focused study time, which is 2-3 hours a day over two weeks of weekdays plus a longer weekend session. If you have less time, this curriculum's later chapters (Parts L and M) are higher-yield than the early ones — Part B's probability primer is foundational but few questions test it directly; Part L's MLflow and UC mechanics are tested in nearly every domain.

---

## 76.4 One week out

Pick the five or six chapters where you struggled most on the two-week pass. Re-read them deeply — not skim, *re-read*. Re-do the exercises cold. Make hand-written notes if it helps you; the kinetic act of writing tends to seat material that won't seat from reading alone.

If you have specific weak domains, this is the time to drill them with targeted practice. Recommended resources from RESEARCH.md:

- **Databricks Academy's free self-paced courses** — particularly "ML Model Development" and "ML Ops". Each is 3-5 hours and includes hands-on labs.
- **Udemy practice exams** — there are several question banks at $15-30. Time yourself. The questions are not the real exam, but the patterns are similar and the timing pressure is good practice. *Caveat:* some practice banks still reflect the obsolete 2023 scope with Spark ML as a 33% domain. Anything that mentions "Spark ML 33% weight" or "Staging → Production stage transitions" is referencing the old exam.

A specific drill worth doing this week: **open a Databricks workspace and re-walk the Chapter 75 capstone end-to-end**. Type the code yourself, do not copy-paste. The act of running each cell — and seeing the MLflow UI, the UC catalog, the registered model with aliases — locks in knowledge in a way that reading does not.

---

## 76.5 Three days out

Do all chapter exercises again, cold, timed. The drill is **90 seconds per exercise** to mimic the exam pace. If you are consistently slow on a particular topic — say, the G × F + 1 model-count math takes you 3 minutes — that is a sign you do not yet have it as fluent recall. Drill those specifically with flashcard-style repetition until you can answer without hesitating.

If you have not yet taken a full timed practice exam, take one now. Score yourself honestly. A score below 75% means you need the extra few days; consider postponing if your exam date is movable. A score in 75-85% means you are on track; spend the next two days polishing weak areas. A score above 85% means you are very likely to pass — at this point you are optimising for margin, not for survival.

---

## 76.6 One day out

Light review only. Skim the citable facts below — the kind of detail that is too granular to derive but shows up verbatim in code-completion questions. A single-page review the night before catches the ones you might have let drift.

**API names that have changed and the wrong one is a trap.**

- `FeatureEngineeringClient` (Unity Catalog) — *not* `FeatureStoreClient` (the legacy Hive-metastore client; deprecated).
- `mlflow.set_registry_uri("databricks-uc")` — the line that points MLflow at the Unity-Catalog-backed registry. Without it, registrations land in the legacy workspace registry.
- DLT (Delta Live Tables) was renamed to **Lakeflow Declarative Pipelines** in 2025. The old DLT syntax still works (backward-compatible), but the marketing-current name is Lakeflow.
- Workflows was renamed to **Lakeflow Jobs** in the same wave.

**Exact metric names (capitalisation matters).**

- `BinaryClassificationEvaluator.metricName` ∈ {`"areaUnderROC"`, `"areaUnderPR"`} — *not* `"AUC"` or `"PR-AUC"`.
- `MulticlassClassificationEvaluator.metricName` ∈ {`"f1"`, `"accuracy"`, `"weightedPrecision"`, `"weightedRecall"`, `"weightedFMeasure"`, `"logLoss"`}.
- `RegressionEvaluator.metricName` ∈ {`"rmse"`, `"mse"`, `"r2"`, `"mae"`, `"var"`}. Default is `"rmse"`.
- pyspark's default `f1` is **macro F1** (unweighted mean across classes), not weighted F1.

**Signatures and conventions for MLflow search.**

- `MlflowClient().search_runs(experiment_ids=[id], filter_string="...", order_by=[...], max_results=N)`.
- Filter-string column prefixes: `params.X`, `metrics.X`, `tags.X`, `attributes.X` (where `attributes` covers `start_time`, `status`, `user_id`, …).
- Order-by direction: `"metrics.val_auc DESC"` — direction goes after a space. Omitting it defaults to ascending (so leaving it out and expecting the *best* run returns the *worst*).

**UC Model Registry — aliases, not stages.**

- The Unity-Catalog registry uses **aliases** (`@champion`, `@challenger`, `@archived`) — string labels you set on a version with `MlflowClient().set_registered_model_alias(name, alias, version)`.
- Legacy stages (`None`, `Staging`, `Production`, `Archived`) belong to the old workspace registry; `transition_model_version_stage` does *not* apply to UC-registered models.

**Hyperopt `hp.choice` returns the index, not the value.**

- `hp.choice('max_depth', [3, 5, 7, 10])` followed by `best = fmin(...)` returns `best['max_depth']` as an integer in `{0, 1, 2, 3}`. To recover the actual value: `from hyperopt import space_eval; space_eval(space, best)`.

**The `G × F + 1` model-count formula.**

- A `CrossValidator` with a `ParamGridBuilder` of `G` combinations and `numFolds=F` trains `G × F` models for evaluation plus **one** final refit on the full training set with the best params — total `G × F + 1`. The classic exam pattern: `G=6, F=3` ⇒ 19.

**AQE config-key prefix.**

- `spark.sql.adaptive.enabled` (not `spark.adaptive.enabled` or `spark.aqe.enabled`). Sub-knobs: `spark.sql.adaptive.coalescePartitions.enabled`, `spark.sql.adaptive.skewJoin.enabled`.

**`GBTClassifier` is binary-only in pyspark.ml.**

- For multi-class boosted trees you must wrap in `OneVsRest` or reach for an external library (XGBoost on Spark via `xgboost-spark`).

**Then stop.** Cramming the night before a 90-minute exam at 70%-pass is not productive. Sleep is more productive. Set up your testing environment ahead of time so the morning is not a panic.

---

## 76.7 Morning of

Eat. Hydrate. Do not cram. If you have a coffee habit, have your usual amount; if you do not, do not start today.

Set up your testing environment **30 minutes before the exam start time**. The Kryterion WebAssessor proctoring software requires you to install a small client, take a webcam photo, hold up your ID, and pan the camera around your testing room to confirm there are no notes or extra devices. If anything goes wrong with the setup — a webcam permission issue, a router restart — you do not want it eating your exam time.

Use the restroom before the start. Once the exam begins, you can leave only by ending the exam early.

---

## 76.8 During the 90 minutes — three passes

A practical structure that almost all successful candidates use:

**First pass (40-50 minutes).** Answer every question you can confidently in under 90 seconds. The Kryterion interface has a "flag for review" button — use it. Flag every question where you hesitated, where two answers seemed plausible, where you ran out of time. Do not dwell. Do not second-guess. The goal of the first pass is to lock in your easy points; you may be looking at 30-35 of the 48 questions that fall into "I know this, click, next".

**Second pass (30-40 minutes).** Return to the flagged questions. Now you have more time per question — averaging 2-3 minutes per flagged one. Re-read carefully. For multi-select questions, count the answers you have selected; if the question says "select two" and you have selected one, that is a clue you are missing one. For code-completion questions, mentally type out what each option would do and see which one matches the stated goal.

**Final pass (last 5 minutes).** Scroll back to the top and verify that **every question has an answer**. There is no penalty for guessing, and the exam is scored on correct answers, not on net-of-wrong. Leaving a question blank is strictly worse than guessing. If you have absolutely no idea, eliminate any answers you can rule out and pick from the remaining; even a 1-in-2 guess on a flagged question is +0.5 expected questions correct on average.

A pitfall I want to flag explicitly: **do not re-read every question on the final pass**. By minute 85 you are tired, your judgment is worse, and second-guessing a question you confidently answered in minute 12 is a way to lose a point you had already earned. Trust the first pass. Use the final five minutes to fill blanks, not to revisit certainties.

---

## 76.9 Question-pattern recognition

The exam has predictable question patterns. Recognising them quickly saves time.

**Pattern A — "Which API does this?"** A short scenario plus four candidate code snippets, only one of which uses the correct Databricks-specific class or method. The traps are usually:
- `FeatureEngineeringClient.create_table()` (correct, current, UC) vs `FeatureStoreClient.register_table()` (legacy workspace store, deprecated).
- `mlflow.set_registered_model_alias()` (correct for UC) vs `mlflow.transition_model_version_stage()` (legacy workspace registry).
- `BinaryClassificationEvaluator(metricName="areaUnderROC")` (correct) vs `BinaryClassificationEvaluator(metricName="AUC")` (wrong — the metric name string is `areaUnderROC`, exactly).
- `MlflowClient.search_runs(order_by=["metrics.auc DESC"])` (correct) vs `MlflowClient.list_runs(sort="auc")` (wrong API name).

The defence is *literal* familiarity with the API names. If you have written each of these calls in a real notebook at least once, the wrong options will jump out.

**Pattern B — Code completion.** A code stub with one blank, four candidate fills. Most often tests `MlflowClient` method names, `hp.*` primitives in a Hyperopt space, or pyspark.ml estimator vs transformer distinctions.

**Pattern C — Scenario → architecture choice.** Four to six lines of business context, pick the right deployment pattern. The recurring distinction: **batch vs streaming vs real-time serving**.
- "Score 10M records overnight" → **batch** with `pyspark.sql` or pandas UDF over a Delta table.
- "Tens of thousands of events per second with elastic scaling" → **streaming inference with DLT (now Lakeflow Declarative Pipelines)** or Structured Streaming with `foreachBatch` calling a model.
- "Synchronous request-response, <100ms latency, low-to-moderate QPS" → **Mosaic AI Model Serving endpoint**.

**Pattern D — Compute math.** "How many models will be trained?" Always the G × F + 1 formula (with F=1 if it is a `TrainValidationSplit` rather than `CrossValidator`). RESEARCH.md's pitfall #3 covers the most common error: forgetting to multiply by k.

**Pattern E — "Which is true about X?" (concept recall).** Four statements about a concept; one is true, three are subtly wrong. Targets include online vs offline feature tables, UC vs workspace registry, mean vs median imputation, OHE for trees vs linear models, Hyperopt `hp.choice` return semantics.

**Pattern F — Mitigation / diagnostic.** A described problem (imbalanced data; overfitting; skewed target; high val/test gap), pick the right technique. The right answer is usually the *cheapest* technique that addresses the problem — Databricks tends to favor `weightCol` for imbalance over SMOTE because `weightCol` is native to Spark ML, threshold tuning over expensive resampling, log-transform over rank transforms.

---

## 76.10 Common time-wasters

Even prepared candidates lose points to specific avoidable behaviors. Watch for these:

- **Doing math by hand when the calculator is faster.** The interface has a calculator. If a question asks "5 × 4 × 3 × 5 = ?", use it. You will be wrong on at least one arithmetic question if you do all of them in your head under pressure.
- **Re-reading the same question three times.** Read carefully once. Answer. Move on. If you find yourself reading a question a third time, it is a flag-and-move-on candidate, not a sit-and-stare candidate.
- **Second-guessing your gut on a fully understood question.** Your first instinct on a question you confidently know is almost always right. Switching answers under fatigue is one of the most common ways well-prepared candidates lose points.
- **Falling into a single-question rabbit hole.** No single question is worth 5 minutes. If you cannot crack it in 2 minutes, flag and move on. You can come back. You will think more clearly after answering ten other questions in the meantime.
- **Reading questions in panic mode.** If your heart is racing, take three slow breaths. The exam time stops for nothing but it also does not punish you for a 15-second pause that lets you read the next question clearly.

---

## 76.11 Self-assessment checklist

The following 35 questions are the **floor of mastery**. If you can answer each cold, in your own words, in under 90 seconds, you are exam-ready. If you cannot, the chapter mapping tells you which chapter to revisit. Use this as a final calibration in the last few days before the exam.

### Foundations

1. **What is the bias-variance decomposition of expected prediction error?** *(Ch 19)*
2. **Why does k-fold cross-validation give more stable estimates than a single train-validation split, and when would you choose train-validation instead?** *(Ch 22)*
3. **What is data leakage, and name three forms of it that arise in feature engineering?** *(Ch 21)*
4. **Define point-in-time correctness and explain why it is needed for time-stamped feature joins.** *(Ch 71)*

### Feature engineering

5. **When should you use median imputation instead of mean?** *(Ch 24)*
6. **Why is one-hot encoding appropriate for linear models but often wasteful for tree-based models?** *(Ch 25)*
7. **Name two situations where a log-transform of a numeric feature is appropriate, and one situation where it is not.** *(Ch 26)*
8. **What is winsorisation, and how does it differ from clipping or trimming outliers?** *(Ch 27)*

### Algorithms

9. **What is the loss function logistic regression minimises, and how does it differ from squared error?** *(Ch 32)*
10. **Explain, in two sentences, the difference between bagging (random forest) and boosting (gradient-boosted trees).** *(Ch 34, Ch 35, Ch 36)*
11. **What does `featureImportances` measure in a fitted `GBTClassifier`, and why is "impurity-based" importance subject to a known bias?** *(Ch 36)*

### Evaluation

12. **Define precision, recall, F1, and explain when F1 is misleading.** *(Ch 42)*
13. **What does AUC measure geometrically, and why is it threshold-invariant?** *(Ch 43)*
14. **When does the PR curve tell you something AUC hides?** *(Ch 44)*
15. **For a regression problem with a log-transformed target, why must you `np.exp()` predictions before computing RMSE on the original scale?** *(Ch 45, RESEARCH common pitfall #6)*
16. **Name three techniques for handling imbalanced classification, with one situation each where the technique is preferred.** *(Ch 46)*

### Hyperparameter optimization

17. **Compute, by hand: how many models will a CrossValidator with `numFolds=4` and a `ParamGridBuilder` of size 5 fit, including the final refit?** *(Ch 65)*
18. **Explain Bayesian optimization in one paragraph — what is the surrogate model and what is the acquisition function?** *(Ch 51)*
19. **What does `hp.choice("x", [10, 20, 30])` return when read from the `best` dict, and how do you recover the actual value?** *(Ch 53, RESEARCH common pitfall — `space_eval`)*
20. **What is `SparkTrials` and when do you use it vs the default `Trials`?** *(Ch 53)*

### Spark and pyspark.ml

21. **Distinguish a Transformer from an Estimator in pyspark.ml. Give one example of each.** *(Ch 62)*
22. **Why does `StandardScaler(withMean=True)` cause a problem when applied to a sparse vector from `OneHotEncoder`?** *(Ch 63)*
23. **What does `handleInvalid="keep"` do on `StringIndexer`, and why is it the safer choice for production pipelines?** *(Ch 63)*
24. **In a pipeline `[indexer, encoder, assembler, classifier]`, which stages are estimators and which are transformers?** *(Ch 62, Ch 63)*

### Databricks platform

25. **Name three benefits of creating feature store tables at the UC level versus the workspace level.** *(Ch 70, Ch 71)*
26. **What is the difference between `FeatureEngineeringClient` and `FeatureStoreClient`?** *(Ch 71)*
27. **What does `online_table = fe.publish_table(...)` do, and when do you need it?** *(Ch 71)*
28. **Explain how to find the best run by AUC across an MLflow experiment using `MlflowClient`.** *(Ch 72)*
29. **What is the magic line that makes `mlflow.register_model()` target the UC registry instead of the workspace registry?** *(Ch 73)*
30. **In UC Model Registry, how do you promote a challenger version to champion?** *(Ch 73)*

### AutoML and deployment

31. **Name three things AutoML on Databricks produces beyond the trained model itself.** *(Ch 74)*
32. **For a workload requiring tens of thousands of events per second with elastic scaling, which Databricks deployment pattern do you choose and why?** *(Ch 75 reflection + RESEARCH common pitfall #4)*
33. **Mosaic AI Model Serving: how do you configure traffic-split A/B testing between two model versions on a single endpoint?** *(RESEARCH research summary)*

### Capstone

34. **Without re-reading Chapter 75, sketch the 12-stage end-to-end Lending Club project from memory.** *(Ch 75)*
35. **In the Lending Club project, why was the random-split AUC 3 points higher than the temporal-split AUC, and what does this teach about the role of split discipline?** *(Ch 21 + Ch 75)*

If you can answer all 35 cold, you are calibrated for the exam. If you stumble on five or more, the chapter mapping tells you where to spend your last few hours.

---

## 76.12 What if you fail

Failure is annoying but it is not the end. The mandatory 14-day waiting period (per the November 2023 retake policy) gives you a structured window to recalibrate.

What the exam tells you when you fail: **per-domain pass/fail**. Kryterion reports your performance by domain — you can see whether you got, say, "Pass" on Databricks ML and Model Development but "Fail" on Data Processing and Model Deployment. That is your roadmap. Spend the 14 days re-reading the chapters that map to your weak domains.

A practical retake plan:
- Day 1-3 after fail: take a day off. Look at the exam transcript. Identify the 1-2 weakest domains.
- Day 4-10: re-read the relevant chapters from this curriculum, redo the exercises, take a fresh practice test.
- Day 11-13: targeted drill on the highest-yield weak spots.
- Day 14: retake.

Pass rates on retake are substantially higher than on first attempt — the exam patterns are familiar, the timing pressure is no longer novel, and the targeted study has closed specific gaps. Anecdotally, candidates who fail the first attempt by under 5 points typically pass the second attempt by 10+ points.

If you fail a second time, that is a signal — not that you are incapable, but that something about your study approach is not working. Consider switching tactics: instead of more chapters, do more hands-on. Build three or four small end-to-end projects on a real workspace, not just read about them. The exam is, ultimately, testing whether you have *used* these APIs, not whether you have *read about* them, and there is no substitute for the muscle memory of having actually called `fe.create_table` or `client.set_registered_model_alias` yourself.

---

## 76.13 After passing

Update your LinkedIn within 24 hours — the certification badge is automatic from Credly once your pass is processed. Add the badge to your email signature if your company allows it. Many of us have observed that "Databricks Certified" in a profile generates inbound recruiter contact at a notably higher rate than "Spark/Databricks experience" alone, even though the underlying capability is the same. The credential is a discovery filter, not just a credential.

Schedule your next exam. The natural next step is the **Databricks Certified Machine Learning Professional**, which builds directly on the Associate scope and adds deeper MLOps content: Lakehouse Monitoring, more sophisticated deployment patterns, MLflow Recipes, distributed training with TorchDistributor and Horovod, and advanced feature engineering with point-in-time joins at scale. Topic 11 of this repository (`/topics/11_databricks_ml_professional/` when built) covers it. Schedule the Professional for roughly three to six months after the Associate, giving yourself time to consolidate the Associate material on real work before stacking the next layer.

The Associate is a valid credential for two years. Two years from now, recertification means retaking the (then-current) full exam. Calendar the renewal date so it does not lapse.

---

## 76.14 This curriculum's contract — closed

A reader who completed all 76 chapters of this curriculum, attempted every exercise, and walked through the capstone has been exposed to every concept and every API on the Mar 1, 2025 exam guide. The exposure is not surface-level — Parts B through D give the probability and optimization foundations that most other curricula skip, Part E goes deeper on feature engineering than the exam tests, Part I on hyperparameter optimization derives the algorithms from first principles rather than just naming the APIs, and Part L covers the Databricks-specific platform layer where most of the points live.

A reasonable pass-rate prediction, for a learner with Vatsal's profile (10+ years PySpark and ML, comfortable with the Optum production environment, light on Databricks-specific UC and MLflow before starting this curriculum): **85% on a first attempt** if all exercises were done seriously. Higher if the capstone was run hands-on on a real workspace. Lower if the curriculum was read passively without exercises — passive reading on this exam reliably underperforms its expected score by 5-10 points because the exam tests *fluency*, not just exposure.

The exam, fundamentally, is the side effect. The point of the curriculum was the mastery underneath. If the exam is the only thing this curriculum gave you, it failed. If the exam is the most superficial thing this curriculum gave you, it succeeded — the deeper things being the ability to debug a Spark pipeline, diagnose temporal leakage in a credit model, choose the right metric for a regulatory ML system, and explain to a stakeholder why their proposed approach has a hidden flaw. Those skills outlast the certification by decades. The certification just opens the doors that let you exercise them.

Good luck on the exam. You are ready.

---

## 76.15 Builds on

**Builds on:** essentially the entire curriculum, but particularly Chapter 75 (the capstone — the self-assessment in 76.11 assumes you have walked the project) and the RESEARCH.md exam-scope document.

There is no "where this returns" section for this chapter. This is the last chapter of the curriculum. The work returns, after this, to your career.
