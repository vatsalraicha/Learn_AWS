# Chapter 44 — PR Curves: When They Tell the Truth ROC Hides

> **Goal of this chapter:** to introduce the precision–recall (PR) curve as the proper partner — and, for imbalanced problems, the proper *replacement* — for the ROC curve we built in Chapter 43. PR curves are not a different metric or a different idea; they're the same threshold sweep, plotted on different axes. But "different axes" turns out to mean "vastly different message" when one class is rare.
>
> The motivating example is sobering. Fraud is 0.1% of transactions. You build a model that predicts "not fraud" for every input. Accuracy: 99.9%. ROC-AUC: 0.5. PR-AUC: roughly 0.001. All three numbers are correct. Two of them are useless. Only one tells you the model is worthless. This chapter is about why.

---

## 44.1 The disaster of the imbalanced ROC

We saw at the end of Chapter 43 that AUC has a "feature" — it is robust to class imbalance. The probabilistic interpretation, $P(s(x_+) > s(x_-))$, doesn't care about the class ratio: it's a pairwise property. A model that ranks well on pairs has high AUC whether 1% or 50% of the data are positives.

In Chapter 43.5.3 we warned this stability is misleading. Time to make the warning precise with numbers.

Consider a fraud-detection problem. A million transactions; 1,000 are fraud (0.1% prevalence); 999,000 are legitimate. We train a model. At some threshold the confusion matrix is:

```
                 Predicted Fraud    Predicted Legit
   Actual Fraud      950                 50          ← 1,000 fraud
   Actual Legit    10,000            989,000         ← 999,000 legit
```

Let's compute the metrics:

- **Recall (TPR)** = $950 / 1{,}000 = 95.0\%$. We catch 95% of fraud.
- **FPR** = $10{,}000 / 999{,}000 = 1.0\%$. We false-alarm on only 1% of legit transactions.
- **Precision** = $950 / (950 + 10{,}000) = 950 / 10{,}950 = 8.7\%$. **Of the things we flag as fraud, 8.7% really are fraud.**

If you'd reported only the ROC numbers — TPR 95%, FPR 1% — you'd describe this as a stellar model. Two metrics within 1% of "perfect." The AUC of such a model, across all thresholds, would routinely come out at 0.97 or higher.

But the precision tells a different story: for every fraud we correctly catch, we wrongly flag 10 legit customers. In production, the fraud-ops team gets a flood of alerts, 91% of which are noise. They lose trust in the model within a week.

What happened? The ROC view used FPR, which has $TN$ in its denominator. With 999,000 legit transactions, 10,000 false positives is a tiny fraction — 1%. The negative class is so huge that big FP counts barely move the FPR. ROC looks great.

The PR view uses precision, which has $FP$ in its denominator (alongside $TP$). $FP$ and $TP$ are both small numbers — 10,000 vs. 950 — so each FP visibly hurts precision. PR shows the truth: precision is 8.7%.

This isn't a flaw in ROC; it's a feature operating outside its useful domain. For *balanced* problems, ROC and PR tell roughly the same story. For *imbalanced* problems — where positives are rare — PR is honest where ROC is misleading.

This chapter shows you how to build PR curves, how to read them, why the baseline is different, and when to use which.

---

## 44.2 Building the PR curve

The recipe is structurally identical to the ROC recipe — same threshold sweep, different axes.

Given a trained binary classifier and a labelled evaluation set:

1. Score every example.
2. Pick a threshold $\tau$.
3. Compute the confusion matrix at that $\tau$.
4. Extract two numbers:
   - **Recall** = $TP / (TP + FN)$.
   - **Precision** = $TP / (TP + FP)$.
5. Plot $(recall, precision)$.
6. Sweep $\tau$ and connect points.

By convention, recall is on the x-axis (0 to 1) and precision on the y-axis (0 to 1).

Two key differences from ROC visible in the convention:

- **Direction of the threshold sweep.** As $\tau$ decreases (we predict positive more eagerly), recall *increases* (we catch more) and precision *typically decreases* (we false-alarm more). So sweeping $\tau$ from high to low traces the PR curve from the *left* (low recall) to the *right* (high recall). The "high precision, low recall" region is on the left; the "low precision, high recall" region is on the right.
- **The curve is not monotone.** Unlike ROC (which always heads up-right), PR can wiggle. Adding a single false positive (going from $\tau$ to $\tau - \epsilon$) might increase recall (if it's a TP) or it might just hurt precision (if it's a FP). The curve can locally go up or down in precision as you sweep. The overall trend is still "left = high precision, right = high recall," but the shape is bumpier.

```
   Precision
        1.0 ┤●●                              ← high precision, low recall
            │  ●●●●                            (very high threshold)
        0.9 ┤      ●●●
            │         ●●●
        0.8 ┤            ●●●        good model — bows out toward (1, 1)
            │               ●●●
        0.7 ┤                  ●●●
            │                     ●●●
            │                        ●●●
        0.5 ┤                            ●●
            │              - - - - - - - - - prevalence baseline (random model)
            │
        0.1 ┤
            │
        0.0 ●─────────────────────────────────────────► Recall
           0.0                                     1.0
```

A "good" PR curve sits close to the top-right corner $(1, 1)$ — high precision AND high recall. A "random" classifier hovers at the *prevalence* line — the horizontal line at $y = p$, where $p$ is the fraction of positives in the dataset. Below the prevalence line is worse than random.

### 44.2.1 Where does the prevalence baseline come from?

This is one of the most underappreciated facts in classification metrics. The ROC random baseline is the diagonal $y = x$, at AUC = 0.5. The PR random baseline is *not* a fixed line — it depends on the class prevalence.

Consider a classifier that produces uniformly random scores, ignoring the input. At any threshold $\tau$, the proportion of positives above $\tau$ is, by symmetry, the same as the proportion of negatives above $\tau$. Among the "predicted positive" subset, the fraction that are actually positive is just the population prevalence — there's no signal sorting them.

Formally: if scores are independent of labels, then $P(y = 1 \mid s > \tau) = P(y = 1) = p$ for any $\tau$. The expected precision of a random classifier is $p$, the prevalence.

So:

- For a 50% prevalence (balanced) problem, the PR random baseline is the horizontal line at $y = 0.5$.
- For a 10% prevalence, it's at $y = 0.10$.
- For a 1% prevalence (fraud), it's at $y = 0.01$.
- For a 0.1% prevalence, it's at $y = 0.001$.

This means **PR baselines are not comparable across datasets** the way ROC baselines are. A PR-AUC of 0.30 looks bad in absolute terms but is excellent on a 1% prevalence problem (where the baseline is 0.01). A PR-AUC of 0.30 on a 50%-prevalence problem is dreadful. Always anchor PR-AUC to the prevalence.

---

## 44.3 Why PR exposes what ROC hides — a worked example

Let's construct a concrete numerical example so the geometric intuition lands.

A binary classification problem with $P = 5$ positives and $N = 95$ negatives, total $n = 100$. Prevalence = 5%.

Suppose at one specific threshold the classifier produces:

- TP = 5, FN = 0, FP = 10, TN = 85.

That is: it catches all 5 positives, but produces 10 false positives along the way.

**ROC numbers:**

- TPR = $5/5 = 1.00$.
- FPR = $10/95 \approx 0.105$.
- This point is at (0.105, 1.00) on the ROC curve — close to the top-left corner, looks great.

**PR numbers:**

- Recall = $5/5 = 1.00$.
- Precision = $5/(5+10) = 5/15 \approx 0.333$.
- This point is at (1.00, 0.333) on the PR curve — recall is great, but precision is only 33%.

What's the story? Of the 15 transactions flagged as positive by the model, only 5 are real positives. Two-thirds of flags are false alarms. The model is "catching everything" — but the cost is that two out of every three alerts are false.

The ROC view says "FPR is only 10%, very respectable." The PR view says "33% precision, the alert stream is mostly noise."

Now imagine the problem is *more* imbalanced. Same model behavior, but now $P = 5$, $N = 9{,}995$, $n = 10{,}000$. The model still catches all 5 positives. Say its FP rate among negatives is unchanged — about 10% — so $FP = 999$ and $TN = 8{,}996$.

**ROC numbers:**

- TPR = $5/5 = 1.00$.
- FPR = $999/9{,}995 \approx 0.10$.
- ROC point still at roughly (0.10, 1.00). Looks identical to the less-imbalanced case.

**PR numbers:**

- Recall = $5/5 = 1.00$.
- Precision = $5/(5+999) = 5/1{,}004 \approx 0.005$ = 0.5%.
- PR point at (1.00, 0.005). The model's "positive" flags are 99.5% noise.

ROC sees no change — same TPR, same FPR. PR sees a catastrophe — precision collapsed from 33% to 0.5% because the FP count scaled with the negative class size.

This is the canonical demonstration. The PR curve's denominators only involve the positive class and the predicted-positive count — both small. ROC's denominator involves the negative count — huge for imbalanced problems. As you scale up the negative class, ROC remains stable (because TN absorbs FP increases) while PR degrades visibly (because each new FP visibly hurts precision).

### 44.3.1 A larger sweep

Let's now walk a full PR curve for a 10% prevalence problem. We have $P = 100$ positives, $N = 900$ negatives in a 1000-example validation set. The classifier produces scores. We sweep $\tau$:

| $\tau$ | TP | FP | FN | TN | Recall | Precision |
|------:|---:|---:|---:|---:|------:|---------:|
| 0.95 | 30 | 1 | 70 | 899 | 0.30 | 0.97 |
| 0.85 | 55 | 5 | 45 | 895 | 0.55 | 0.92 |
| 0.75 | 75 | 20 | 25 | 880 | 0.75 | 0.79 |
| 0.65 | 85 | 50 | 15 | 850 | 0.85 | 0.63 |
| 0.50 | 92 | 120 | 8 | 780 | 0.92 | 0.43 |
| 0.30 | 98 | 300 | 2 | 600 | 0.98 | 0.25 |
| 0.10 | 100 | 700 | 0 | 200 | 1.00 | 0.125 |

Plotting (recall, precision):

```
  Precision
       1.0 ┤
           │
       0.97┤●  (0.30, 0.97)
       0.92┤   ●  (0.55, 0.92)
           │
       0.79┤      ●  (0.75, 0.79)
           │
       0.63┤          ●  (0.85, 0.63)
           │
       0.43┤              ●  (0.92, 0.43)
           │
       0.25┤                   ●  (0.98, 0.25)
       0.125┤                       ●  (1.00, 0.125)
       0.10├─ - - - - - - - - - - - - - - - prevalence baseline
       0.0 ●─────┬─────┬─────┬─────┬─────► Recall
                0.3   0.55  0.75  0.92    1.0
```

The curve starts high-left (high precision, low recall) and descends to low-right (low precision, high recall). It clearly dominates the prevalence baseline of 0.10. A "knee" sits around (0.75, 0.79) — likely where F1 is maximised. To the right of the knee, precision drops faster than recall rises, suggesting the classifier is becoming noisy at low thresholds. To the left, recall is poor — the threshold is so high we miss most positives.

This is exactly the geometric story PR curves are designed to convey.

---

## 44.4 PR-AUC and Average Precision

Just as we summarised the ROC curve with AUC, we summarise the PR curve with an area metric. Two slightly different ones, often used interchangeably but technically distinct:

### 44.4.1 PR-AUC

**PR-AUC** is the area under the precision–recall curve, computed by trapezoidal integration:

$$
\text{PR-AUC} = \int_0^1 \text{precision}(r) \, dr
$$

In practice you compute it numerically from the discrete (recall, precision) points using the trapezoid rule, just as you did for ROC.

PR-AUC ranges from 0 (no signal) to 1 (perfect). The random baseline is *not* 0.5 — it equals the positive prevalence $p$. So for a 10% prevalence problem, PR-AUC = 0.1 is the no-information baseline; PR-AUC = 0.7 is excellent.

### 44.4.2 Average Precision (AP)

**Average Precision** is a slightly different summary that's especially popular in information retrieval and object detection. It's the *weighted mean* of precision values across recall thresholds:

$$
\text{AP} = \sum_{k} (R_k - R_{k-1}) \cdot P_k
$$

where the sum is over the discrete recall levels $R_k$ as the threshold sweeps. This is a *right-rectangle* approximation of the area, where each recall increment is weighted by the precision at that point.

Trapezoidal PR-AUC and AP usually differ by at most a few percentage points, and the difference matters little in practice. sklearn's `average_precision_score` returns AP; some other libraries return trapezoidal PR-AUC. The PySpark `areaUnderPR` is the trapezoidal version. When reading a paper, check which one is being reported — but mostly, they're talking about the same thing.

### 44.4.3 Computing PR-AUC by hand on a small example

Take the seven-point PR curve from the table in 44.3.1. Trapezoidal area summed left-to-right:

```
Segment (R, P) → (R', P'):  Δ R = R' - R, average P = (P + P')/2, area = ΔR · avg P
```

- (0, 0.97) is the implicit left endpoint? Actually the curve doesn't start at (0, _) — it starts at the lowest-recall point we measured. For a cleaner calc, sklearn extrapolates.

Without getting precious, just use the table points 1 through 7:

| Segment | ΔR | (P + P')/2 | Area |
|--------|------:|-----:|-----:|
| (0.30, 0.97) → (0.55, 0.92) | 0.25 | 0.945 | 0.236 |
| (0.55, 0.92) → (0.75, 0.79) | 0.20 | 0.855 | 0.171 |
| (0.75, 0.79) → (0.85, 0.63) | 0.10 | 0.710 | 0.071 |
| (0.85, 0.63) → (0.92, 0.43) | 0.07 | 0.530 | 0.037 |
| (0.92, 0.43) → (0.98, 0.25) | 0.06 | 0.340 | 0.020 |
| (0.98, 0.25) → (1.00, 0.125) | 0.02 | 0.188 | 0.004 |

Sum (from recall 0.30 to 1.00): 0.539. If we wanted PR-AUC over $[0, 1]$, we'd need to extrapolate the curve to recall 0 (precision typically very high there). Assuming the curve at recall 0 is at precision near 1.0 (a perfect operating point at high threshold), the missing trapezoid from (0, 1.0) to (0.30, 0.97) is roughly $0.30 \cdot 0.985 = 0.296$. Total PR-AUC ≈ 0.539 + 0.296 ≈ 0.83.

Compare to baseline of 0.10 — PR-AUC of 0.83 is substantially better. The model has serious signal.

---

## 44.5 When to use which curve

To summarise the chapter's central decision rule:

**Use the ROC curve (and ROC-AUC) when:**

- The classes are balanced (say, 40-60% each way), so the negative class isn't huge enough to mask FP costs.
- You care about *ranking quality across the whole input distribution*, not specifically about the positive class.
- You're comparing across datasets with different prevalences and want a metric that doesn't shift with prevalence.

**Use the PR curve (and PR-AUC) when:**

- The classes are imbalanced — positives are rare.
- You care about the positive class specifically — about correctness *of the positive predictions*.
- The cost of a false positive depends on the count, not on the rate.

For most real-world imbalanced classification problems — fraud, churn, defect detection, disease screening, click prediction, intrusion detection — PR is the right curve. ROC is what you report alongside for completeness, but PR is what you make decisions from.

A small consolation: if you have both ROC-AUC and PR-AUC, you can roughly diagnose what's happening. ROC-AUC near 1 with PR-AUC near baseline → severe imbalance hiding precision problems. Both high → genuinely strong model. Both moderate → middling model. PR-AUC > ROC-AUC almost never happens in practice; the two are correlated but PR can be much lower.

---

## 44.6 The "above prevalence" trap

Newcomers to PR-AUC often expect 0.5 to be "decent" — by analogy with ROC-AUC where 0.5 is the no-information baseline. This is wrong for PR, and it causes real misjudgement.

A PR-AUC of 0.5 on a 1% prevalence problem is excellent — it's 50× the baseline. A PR-AUC of 0.5 on a 40% prevalence problem is mediocre — it's only 25% better than baseline. Always cite **PR-AUC together with the prevalence** so the reader can interpret.

I have personally seen ML reports state "PR-AUC = 0.42" with no further context, leaving the audience to guess whether that's good or bad. It might be brilliant (for a 0.1% prevalence) or terrible (for 50% prevalence). The number alone is uninterpretable.

The minimum honest report for an imbalanced classifier is:

> "On a test set with $X\%$ positive prevalence, the model achieves PR-AUC = $Y$, ROC-AUC = $Z$, with precision = $P$ and recall = $R$ at the chosen operating threshold."

That's five numbers (six if you include accuracy). Each one tells you something the others don't.

---

## 44.7 PR and ROC together — when both lie

Both curves have a shared blind spot: they only work on test data with *labels*. If your production traffic has a different prevalence from your test set, neither curve generalises perfectly to production.

This is a deployment subtlety. Suppose you trained and evaluated on a 10% positive set (perhaps by oversampling). Your PR-AUC = 0.7 on that test set. In production, the positive rate is 1%. The model's *score function* hasn't changed, but the precision at any operating threshold will be much lower in production — because there are 10× more negatives competing for each FP slot.

The lesson: PR and ROC are *test-set* metrics. For production-relevant precision, you need to evaluate on a test set with production-like prevalence, OR you need to do the math to map test-set precision to production precision. We cover this in Chapter 46 (resampling) and Chapter 73 (production monitoring).

---

## 44.8 The Spark and sklearn surface

### 44.8.1 sklearn

```python
from sklearn.metrics import precision_recall_curve, average_precision_score

# y_true: 0/1 labels. y_score: predicted positive-class scores.
precision, recall, thresholds = precision_recall_curve(y_true, y_score)
ap = average_precision_score(y_true, y_score)

# Plot:
import matplotlib.pyplot as plt
plt.plot(recall, precision, label=f"PR (AP={ap:.3f})")
plt.axhline(y=sum(y_true)/len(y_true), color='gray', linestyle='--',
            label=f"baseline (prevalence={sum(y_true)/len(y_true):.2f})")
plt.xlabel("Recall"); plt.ylabel("Precision")
plt.legend(); plt.show()
```

A couple of practical notes:

- `precision_recall_curve` returns *one more value* in the precision/recall arrays than in the thresholds array. The final precision is 1.0 and final recall is 0.0 by convention (the "no positives predicted" endpoint). This means you can't directly zip `(precision, recall, thresholds)` — the last point has no associated threshold.
- For multiclass, use `average_precision_score(y_true, y_score, average='macro')` or `'weighted'`. We discuss in Chapter 47.

### 44.8.2 pyspark.ml

Spark's BinaryClassificationEvaluator exposes `areaUnderPR`:

```python
from pyspark.ml.evaluation import BinaryClassificationEvaluator

evaluator = BinaryClassificationEvaluator(
    labelCol="label",
    rawPredictionCol="rawPrediction",
    metricName="areaUnderPR"
)
pr_auc = evaluator.evaluate(predictions_df)
```

To extract the actual curve points (not just the area), drop to the underlying RDD-based metrics:

```python
from pyspark.mllib.evaluation import BinaryClassificationMetrics
rdd = predictions_df.select("score", "label").rdd.map(lambda r: (float(r.score), float(r.label)))
metrics = BinaryClassificationMetrics(rdd)
metrics.areaUnderPR
metrics.pr().collect()   # list of (recall, precision) tuples
```

Both `areaUnderROC` and `areaUnderPR` are exposed from BinaryClassificationEvaluator — typically you compute both and report both. We cover this in depth in Chapter 66.

---

## 44.9 A final example — the "predict everything as negative" pathology

Let's close with the example from the chapter opening, fully worked.

Setup: 1 million transactions. 0.1% are fraud → 1,000 fraud, 999,000 legit. A "model" predicts "not fraud" for every input. Its confusion matrix at any threshold (it's a constant predictor):

```
                Predicted +    Predicted −
   Actual +          0           1,000
   Actual −          0         999,000
```

- TP = 0, FP = 0, FN = 1,000, TN = 999,000.
- Accuracy = (0 + 999,000)/1,000,000 = 99.9%.
- Recall = 0/1000 = 0%.
- Precision = 0/0 — undefined, but conventionally treated as 0 (no predicted positives, no real ones in the predicted set).
- ROC-AUC: the model's score is constant; pairs of (positive, negative) are tied at every threshold; AUC = 0.5 (random).
- PR-AUC: the curve is degenerate — precision = 0 everywhere except the trivial endpoint at recall = 0. PR-AUC ≈ 0.

Three different summaries of the same useless model:

1. Accuracy: 99.9%. Looks fantastic. Bad metric.
2. ROC-AUC: 0.5. Honestly reflects "no information." Good metric.
3. PR-AUC: 0.001. Honestly reflects "no useful positive predictions." Best metric for this problem.

A teammate who reports only accuracy gives you a misleading 99.9%. A teammate who reports ROC-AUC gives you an honest 0.5 — equivalent to random. A teammate who reports PR-AUC gives you a brutally honest 0.001, which is the right gut-level signal: "this model does not work for the rare class."

That last metric is what fraud, churn, defect-detection, disease-screening teams should be looking at. Make it part of your default reporting.

---

## 44.10 Summary

The bones:

1. The **PR curve** plots precision (y) vs. recall (x) as the threshold sweeps. Same threshold sweep as ROC; different axes.
2. PR's axes use TP and FP in their denominators — both small numbers. ROC's FPR has TN in its denominator — huge for imbalanced problems. This is why PR sees what ROC hides.
3. The **random-classifier baseline** for PR is the horizontal line at $y = p$ (the prevalence), not a fixed line. PR-AUC of 0.3 is dreadful at 50% prevalence and excellent at 1%. Always anchor to prevalence.
4. **PR-AUC** is the area under the PR curve. **Average Precision (AP)** is a closely related summary. They're slightly different numerically; both are reasonable summaries.
5. **Use PR** for imbalanced classification problems where you care about positive-class correctness. **Use ROC** for balanced problems, or when ranking across the whole distribution is what matters.
6. PR-AUC and ROC-AUC together diagnose more than either alone: high ROC-AUC with low PR-AUC = imbalance hiding precision problems.
7. Both PR and ROC are *test-set* metrics. If production prevalence differs from test prevalence, precision in production differs from precision on the test set.
8. **Spark exposes both** via `BinaryClassificationEvaluator.metricName ∈ {"areaUnderROC", "areaUnderPR"}`.

If you can take any confusion matrix at any threshold and quickly compute both the ROC point and the PR point, sketch the curves, anchor PR-AUC to prevalence, and explain *why* PR exposes what ROC hides — you have the chapter.

---

## 44.11 What this builds on / where this returns

**Builds on:** Chapter 42 (precision, recall, threshold sweep). Chapter 43 (ROC, AUC, the area-under-curve summary pattern). Chapter 9 (basic probability — the "PR baseline is prevalence" derivation).

**Returns:**

- **Imbalanced classification** — the engineering response, where PR-AUC is one of the headline metrics — *Chapter 46*.
- **Multi-class metrics** — including how to compute PR-AUC for $K > 2$ classes — *Chapter 47*.
- **Spark evaluators in depth** — exposing `areaUnderPR` and how to get curve points — *Chapter 66*.

---

## 44.12 Exercises

Cold attempt all.

1. **Build a PR curve.** A binary classifier produces scores on 10 examples (3 positives, 7 negatives):

   | rank | score | label |
   |:---:|:---:|:---:|
   | 1 | 0.90 | + |
   | 2 | 0.81 | − |
   | 3 | 0.77 | + |
   | 4 | 0.65 | − |
   | 5 | 0.52 | + |
   | 6 | 0.49 | − |
   | 7 | 0.41 | − |
   | 8 | 0.35 | − |
   | 9 | 0.22 | − |
   | 10 | 0.18 | − |

   Sweep the threshold; compute (recall, precision) at each step. Sketch the staircase. Estimate PR-AUC by trapezoidal integration. What is the prevalence baseline for this dataset?

2. **The prevalence baseline.** Why is the PR random baseline at $y = p$ and not at $y = 0.5$? Argue from the probabilistic interpretation: what is $P(y = 1 \mid \hat{y} = 1)$ when scores are independent of labels?

3. **The FP-volume problem.** A fraud-detection model has TPR = 95%, FPR = 1%. The dataset has 1% positive prevalence (out of 100,000 examples, 1,000 are fraud). Compute precision. Now suppose the prevalence is 0.01% (10 are fraud) — same TPR and FPR. Compute precision again. Discuss.

4. **Reading the curves together.** A model has ROC-AUC = 0.94 and PR-AUC = 0.08 on a test set with 0.5% prevalence. What is going on? Is this model useful?

5. **A PR-AUC interpretation question.** A team reports PR-AUC = 0.45 with no other context. Why is this number nearly uninterpretable, and what would you ask to interpret it?

6. **Direction of the threshold sweep.** On a PR curve, as the threshold *decreases* from high to low, which direction does the operating point move (left/right, up/down)? Why?

7. **Imbalanced + ROC vs. PR.** Sketch a hypothetical scenario where ROC-AUC is 0.97 but PR-AUC is 0.20. Describe the model behaviour: what is it doing well, what is it doing poorly, what would you do if this was your model?

8. **The endpoint issue.** sklearn's `precision_recall_curve` returns precision and recall arrays whose final values are $(1.0, 0.0)$ — meaning at the highest threshold, precision = 1.0 and recall = 0.0. Why does the curve include this point? What does it mean operationally?

9. **PR vs. ROC equivalence regime.** Show by example that for a *balanced* problem (50/50), PR and ROC give substantially the same picture. Construct a small numerical example.

10. **Production prevalence shift.** Your test-set PR-AUC is 0.75 at 30% prevalence (you oversampled positives). In production, the prevalence is 3%. Does your test-set PR-AUC predict production PR-AUC? Why or why not? What is the right way to report this?

11. **F1 vs. PR-AUC.** F1 is computed at one operating point; PR-AUC summarises the curve. When should you report F1 and when should you report PR-AUC?

12. **Spark trap.** A colleague computes PR-AUC in Spark with:

    ```python
    BinaryClassificationEvaluator(
        labelCol="label",
        predictionCol="prediction",
        metricName="areaUnderPR"
    )
    ```

    What is wrong? Fix it.

<details>
<summary>Answers</summary>

1. P = 3, N = 7, prevalence = 0.3. Sweep:
   - $\tau > 0.90$: TP=0, FP=0. Recall=0, Precision undefined (skip / endpoint).
   - $\tau = 0.90$ (predict ranks 1): TP=1, FP=0. R=1/3, P=1.
   - $\tau = 0.81$ (ranks 1-2): TP=1, FP=1. R=1/3, P=1/2.
   - $\tau = 0.77$ (ranks 1-3): TP=2, FP=1. R=2/3, P=2/3.
   - $\tau = 0.65$ (ranks 1-4): TP=2, FP=2. R=2/3, P=1/2.
   - $\tau = 0.52$ (ranks 1-5): TP=3, FP=2. R=1, P=3/5.
   - $\tau = 0.49$ (ranks 1-6): TP=3, FP=3. R=1, P=1/2.
   - $\tau = 0.41$ (ranks 1-7): TP=3, FP=4. R=1, P=3/7.
   - $\tau = 0.35$ (ranks 1-8): TP=3, FP=5. R=1, P=3/8.
   - $\tau = 0.22$ (ranks 1-9): TP=3, FP=6. R=1, P=3/9 = 1/3.
   - $\tau = 0.18$ (all 10): TP=3, FP=7. R=1, P=3/10.

   Plot the (R, P) points; PR-AUC by trapezoidal integration from R=0 (where we extrapolate P≈1) to R=1. Rough estimate: (0→1/3, P~1.0) contributes ≈ 0.33; (1/3→2/3) midpoint P~0.58 contributes ≈ 0.193; (2/3→1) midpoint P~0.55 contributes ≈ 0.183. Sum ≈ 0.71. Baseline = prevalence = 0.30.

2. If scores are independent of labels, then for any threshold $\tau$, the subset of examples above the threshold contains the same fraction of positives as the population (no selection bias). So $P(y = 1 \mid \hat{y} = 1) = P(y = 1) = p$. That's precision, and it equals prevalence — so the random-baseline curve sits at the horizontal line $y = p$.

3. Case 1 (1% prevalence, 100K examples, 1K positives, 99K negatives): TP = 950, FP = 990, precision = 950/1940 = 49.0%. Case 2 (0.01% prevalence, 100K examples, 10 positives, 99,990 negatives): TP = 9.5 ≈ 10, FP = 999.9 ≈ 1000, precision = 10/1010 = 0.99%. As the negative class gets larger, precision collapses while ROC numbers (TPR=95%, FPR=1%) stay rock-steady. This is the key imbalance trap.

4. The model ranks well (high ROC-AUC), but its positive predictions are mostly noise (low PR-AUC). With 0.5% prevalence, this is consistent with the model giving "right ordering on average across pairs" while still having FP greatly exceed TP at any reasonable operating threshold. Whether useful depends on the application: if downstream is pure ranking ("show me the top 100 most-likely fraud cases"), it might still help. If downstream is binary alerting, the FP volume kills usability and the model is not deployable without further work (resampling, threshold tuning, more features).

5. PR-AUC is unanchored without the prevalence. 0.45 at 1% prevalence is excellent (45× baseline); 0.45 at 50% prevalence is mediocre (≤2× baseline). Ask: "What is the prevalence of the positive class in the test set?"

6. As $\tau$ decreases, more examples are predicted positive, so recall typically rises and precision typically falls. The operating point moves *right* (higher recall) and *typically down* (lower precision), with possible local non-monotone wiggles in precision.

7. The model ranks positives ahead of negatives well — high ROC-AUC. But because negatives outnumber positives ~99 to 1, even a small FPR (say 5%) means many FPs, dwarfing TPs. The model is brilliant for *ranking* (show the top K candidates) but terrible for *binary alerting* (precision collapses). Options: tune threshold much higher (accept lower recall in exchange for usable precision); use the model output as a ranked list to a human reviewer rather than a binary decision; collect more positive labels and retrain; add features specifically targeted at distinguishing top-of-distribution borderline cases.

8. The (P=1.0, R=0.0) endpoint corresponds to a threshold above the maximum score — no examples are predicted positive. Operationally, this is the "predict nothing" endpoint: if you predict zero positives, precision is conventionally 1 (vacuously — every positive prediction is correct because there are none) and recall is 0 (you caught no positives). Including this point lets the curve extend to recall = 0, which is needed for PR-AUC integration on $[0, 1]$.

9. Example: P = 50, N = 50. Suppose at threshold $\tau_1$: TP=40, FP=10. TPR = 40/50 = 0.80. FPR = 10/50 = 0.20. Recall = 0.80. Precision = 40/50 = 0.80. At threshold $\tau_2$: TP=30, FP=5. TPR = 0.60. FPR = 0.10. Recall = 0.60. Precision = 30/35 = 0.857. The ROC points and PR points move in tandem — both improve as threshold rises. ROC-AUC and PR-AUC tell the same story (the baseline for PR-AUC at 50% prevalence is 0.5, so even moderate models look "good" by both metrics).

10. No, test-set PR-AUC does not directly predict production PR-AUC because the prevalence has shifted by 10×. In production with 3% prevalence, FP at any operating threshold will dominate TP more — precision drops, PR-AUC drops. The right way to report: also evaluate on a held-out test set with production-representative prevalence (i.e., don't oversample the production-eval set), and report that PR-AUC. Or use prevalence-corrected formulas — sklearn doesn't do this directly, but the math is straightforward.

11. F1 is for reporting a specific *operating point* — useful when you've chosen a deployment threshold and want one number to summarize that decision. PR-AUC is for reporting *classifier capability* across all operating points — useful for model comparison, leaderboards, capacity-without-commitment. In practice you report both: PR-AUC for the model selection conversation, F1 (or precision/recall) for the deployed operating point.

12. `predictionCol` should be `rawPredictionCol`. PR-AUC is computed from the *score* (continuous), not the 0/1 *prediction*. Using the 0/1 column degenerates the curve. The fix:

    ```python
    BinaryClassificationEvaluator(
        labelCol="label",
        rawPredictionCol="rawPrediction",
        metricName="areaUnderPR"
    )
    ```

</details>
