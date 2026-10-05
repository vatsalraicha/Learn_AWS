# Chapter 43 — ROC Curves and AUC: The Geometric Meaning

> **Goal of this chapter:** to make the ROC curve and its area-under-the-curve (AUC) into something more than vocabulary you've seen on dashboards. Almost every binary classifier in industry is described, in passing, by its AUC — "the model is at 0.87 AUC, ship it" — and the speaker is usually unable to say, exactly, what that means. By the end of this chapter you will be able to. You'll know what the curve is, where the points come from, why the diagonal is the random classifier, why the area has a *probabilistic* interpretation that's far more interesting than "area under a curve", and when AUC is the right metric to quote versus when it lies.
>
> The substance is mostly geometric. The math is light but precise. The takeaway is one short sentence that, once it lands, never leaves you.

---

## 43.1 Why a curve at all?

We ended Chapter 42 on a single picture: a trained classifier is not one model, it's a *family* of classifiers indexed by the threshold $\tau$. Each $\tau$ produces one confusion matrix, one set of (precision, recall) numbers, one operating point.

If you only ever report metrics at the default $\tau = 0.5$, you are summarising the family by one of its members. Different members behave differently. To talk about the *family as a whole* — i.e., the classifier's intrinsic capability, decoupled from any specific operating-point choice — you need to summarise the whole sweep of thresholds.

There are two standard ways to do this. The ROC curve and the PR curve. We do ROC in this chapter and PR in Chapter 44. They are visualising the same underlying threshold sweep on different axes, and they tell you different things.

A working analogy: think of a high-jumper. At each height of the bar (the threshold), they either clear or don't. The "performance curve" — height vs. probability of clearing — describes the jumper's full ability, not their behaviour at one particular height. The ROC curve is the analogous "ability curve" for a binary classifier.

---

## 43.2 Building the ROC curve from a threshold sweep

The recipe for the ROC curve is mechanical. Given a trained classifier and a labelled evaluation set:

1. Score every example. You now have a list $(s_i, y_i)$ — scores and labels.
2. Pick a candidate threshold $\tau$.
3. Compute the confusion matrix at that $\tau$.
4. Extract two numbers from the confusion matrix:
   - **True Positive Rate** (TPR), a.k.a. recall = $TP/(TP+FN)$.
   - **False Positive Rate** (FPR) = $FP/(FP+TN)$.
5. Plot the point $(FPR, TPR)$.
6. Sweep $\tau$ through all interesting values and connect the points.

That gives you the ROC curve. By convention, FPR is on the x-axis and TPR on the y-axis. Both are between 0 and 1. The curve always starts at $(0, 0)$ — at $\tau = \infty$ (or just very high), we predict positive for nothing, so $FP = 0$ and $TP = 0$, hence both rates are 0 — and ends at $(1, 1)$ — at $\tau = -\infty$ (very low), we predict positive for everything, so $FP = $ all negatives and $TP = $ all positives, hence both rates are 1.

```
     TPR (recall)
       1.0 ┤                            (1, 1)
           │                       ●●●●●●
           │              ●●●●●●●●●
           │         ●●●●●            ← good model — bows up and to the left
           │      ●●●
           │    ●●           - - - - - - random classifier (y = x)
       0.5 ┤  ●●        - - -
           │ ●●     - - -
           │●  - - -
           │ - -        ← bad model — below the diagonal (flip predictions!)
           │-
       0.0 ●─────────────────────────►  FPR
          0.0                       1.0
```

Three regions on this picture matter:

1. **The diagonal $y = x$.** A classifier that produces random scores — say, uniform random numbers, ignoring the input entirely — has, at every threshold, FPR roughly equal to TPR. Why? Because if scores are independent of labels, then the fraction of positives above the threshold equals the fraction of negatives above the threshold, in expectation. So a random classifier traces the diagonal. **The diagonal is the no-information baseline.**

2. **Above the diagonal.** A model that has learned something — TPR > FPR at every threshold — bows upward and to the left. The closer to the top-left corner $(0, 1)$, the better. A perfect classifier — one that separates positives from negatives entirely — passes through $(0, 1)$: zero false positives, all true positives caught.

3. **Below the diagonal.** A classifier that scores positives lower than negatives — perfectly anti-correlated — traces below the diagonal. The right response is to *flip its predictions* (or its scores). Below-the-diagonal classifiers, after flipping, become above-the-diagonal.

The curve is monotonically non-decreasing in both x and y as $\tau$ sweeps from high to low: lowering the threshold can only add positives (never remove them), so TP and FP both monotonically grow, meaning TPR and FPR both monotonically grow. The curve never goes "left" or "down" as you trace it from $(0,0)$ to $(1,1)$.

### 43.2.1 Worked example — six data points

Let's actually do this by hand. We have a tiny evaluation set of 6 examples. The classifier produces scores; labels are known. We sort by descending score:

| rank | score $s$ | label $y$ |
|----:|:---------:|:--------:|
| 1 | 0.95 | + |
| 2 | 0.83 | + |
| 3 | 0.72 | − |
| 4 | 0.55 | + |
| 5 | 0.40 | − |
| 6 | 0.21 | − |

Three positives (rank 1, 2, 4), three negatives (rank 3, 5, 6). Total $P = 3$, $N = 3$.

We sweep the threshold through every distinct score value. At each threshold, examples with score $\geq \tau$ are predicted positive; the rest negative. Let's tabulate.

**Threshold above 0.95** (predict positive for nothing): TP = 0, FP = 0, FN = 3, TN = 3. TPR = 0/3 = 0. FPR = 0/3 = 0. Point: $(0, 0)$.

**Threshold = 0.95** (predict positive for rank 1 only — a real positive): TP = 1, FP = 0. TPR = 1/3. FPR = 0/3 = 0. Point: $(0, 1/3)$.

**Threshold = 0.83** (predict positive for ranks 1-2 — both real positives): TP = 2, FP = 0. TPR = 2/3. FPR = 0. Point: $(0, 2/3)$.

**Threshold = 0.72** (predict positive for ranks 1-3 — two real positives, one false positive): TP = 2, FP = 1. TPR = 2/3. FPR = 1/3. Point: $(1/3, 2/3)$.

**Threshold = 0.55** (predict positive for ranks 1-4): TP = 3, FP = 1. TPR = 3/3 = 1. FPR = 1/3. Point: $(1/3, 1)$.

**Threshold = 0.40** (predict positive for ranks 1-5): TP = 3, FP = 2. TPR = 1. FPR = 2/3. Point: $(2/3, 1)$.

**Threshold = 0.21** (predict positive for everything): TP = 3, FP = 3. TPR = 1. FPR = 1. Point: $(1, 1)$.

The curve goes through these points in order:

```
       TPR
        1 ┤        ●─────●─────●  (1/3, 1) (2/3, 1) (1, 1)
          │        │
        2/3┤  ●────●            (0, 2/3) → (1/3, 2/3)
          │  │
        1/3┤  ●                 (0, 1/3)
          │  │
          │  │
         0 ●                   (0, 0)
          └──┬─────┬─────┬────► FPR
            0    1/3   2/3    1
```

A staircase curve. It steps up (in TPR) when we cross a threshold that exposes a real positive, and steps right (in FPR) when we cross a threshold that exposes a negative. The corner at $(1/3, 1)$ is where we've caught all three positives but only one false positive — the model is reasonably good.

### 43.2.2 A pause to register what just happened

In that staircase walk, every time the threshold "exposed" a positive (a true positive moved from below the threshold to above), the curve stepped *up*. Every time it exposed a negative (a false positive moved above the threshold), it stepped *right*.

A good model exposes positives first (because it scores them higher than negatives). A bad model exposes them in random order. A perfect model exposes all positives before any negatives — the curve climbs straight up to $(0, 1)$, then traverses straight right to $(1, 1)$.

This is the right way to *see* the ROC curve. Forget the formula; visualise the threshold descending through sorted scores, and the curve stepping up on a positive, right on a negative.

---

## 43.3 AUC — the area under the curve

The ROC curve is a curve. To rank models, we summarise it with a single number — the area under the ROC curve, **AUC** (sometimes ROC-AUC to disambiguate from PR-AUC).

The area lies between 0 and 1:

- **AUC = 1.0:** perfect classifier. The curve goes straight up to $(0, 1)$ then across to $(1, 1)$; area = 1.
- **AUC = 0.5:** random classifier. The curve is the diagonal; area = $\frac{1}{2} \cdot 1 \cdot 1 = 0.5$.
- **AUC < 0.5:** the classifier is worse than random. Flip its predictions; new AUC will be $1 - \text{old AUC} > 0.5$.
- **AUC = 0.0:** a perfect classifier with the labels swapped. (Equally informative as AUC = 1.0, just flipped.)

For our six-point example, what is the AUC? You can compute it as a sum of trapezoid areas under the staircase. Walking from $(0, 0)$ to $(0, 1/3)$ to $(0, 2/3)$ to $(1/3, 2/3)$ to $(1/3, 1)$ to $(2/3, 1)$ to $(1, 1)$:

```
Step 1: (0, 0) → (0, 1/3).      Δx = 0,    no area.
Step 2: (0, 1/3) → (0, 2/3).    Δx = 0,    no area.
Step 3: (0, 2/3) → (1/3, 2/3).  Δx = 1/3,  height = 2/3,  area = 2/9.
Step 4: (1/3, 2/3) → (1/3, 1).  Δx = 0,    no area.
Step 5: (1/3, 1) → (2/3, 1).    Δx = 1/3,  height = 1,    area = 1/3.
Step 6: (2/3, 1) → (1, 1).      Δx = 1/3,  height = 1,    area = 1/3.
```

Total AUC = $0 + 0 + 2/9 + 0 + 1/3 + 1/3 = 2/9 + 2/3 = 2/9 + 6/9 = 8/9 \approx 0.889$.

So this classifier has AUC = 8/9. The maximum is 1, the random baseline is 0.5; 0.889 is well above the baseline.

(For a staircase ROC, the trapezoidal area computation is exact, not an approximation. The trapezoids degenerate into rectangles because the curve is piecewise-axis-aligned.)

---

## 43.4 The probabilistic interpretation — the punchline of this chapter

We've defined AUC as the area under the ROC curve. That's the *operational* definition. There is also a *probabilistic* interpretation that is far more useful, and it is the thing that, once internalised, makes AUC a genuinely meaningful number rather than just "area under something."

> **Theorem.** AUC equals the probability that, for a uniformly randomly chosen positive example $x_+$ and a uniformly randomly chosen negative example $x_-$, the classifier scores them in the correct order — i.e., $s(x_+) > s(x_-)$. Formally:
>
> $$
> \text{AUC} = P\!\left(s(x_+) > s(x_-)\right)
> $$
>
> (With ties broken by convention — typically a tied pair contributes 1/2 to the count.)

This is sometimes called the **Mann-Whitney-Wilcoxon interpretation** of AUC, after a classical statistic that turns out to compute exactly this probability.

### 43.4.1 Why this is the right way to think about AUC

The probabilistic interpretation says: pick any positive example, pick any negative example. AUC is the probability your model gets the ranking right.

This has consequences:

- **AUC is threshold-independent.** It doesn't depend on where you draw the line; it's a property of the score function on positive-negative pairs.
- **AUC is class-imbalance invariant (sort of).** Doubling the number of negatives doesn't change the probability of a random pair being in the right order — it just changes the *number* of pairs. We'll qualify this in Chapter 44.
- **AUC is interpretable as a ranking metric, not a classification metric.** It's measuring "given any positive and any negative, does my score function order them correctly?" That's a ranking question, and AUC is the right answer to it.

If your downstream use of the model is *ranking* — "give me the top 100 leads sorted by likelihood-to-convert", "show me the most likely fraudsters first", "rank applicants by default risk" — AUC is directly meaningful. The ranking quality is what AUC measures.

### 43.4.2 Verifying the interpretation on the six-point example

Let's verify the theorem on our six-point example. We had three positives (scores 0.95, 0.83, 0.55) and three negatives (scores 0.72, 0.40, 0.21). There are $3 \times 3 = 9$ positive–negative pairs. For each pair, did the model score the positive higher than the negative?

```
pos\neg    0.72    0.40    0.21
0.95       ✓ +     ✓ +     ✓ +
0.83       ✓ +     ✓ +     ✓ +
0.55      ✗ −     ✓ +     ✓ +
```

Eight pairs out of nine are correctly ordered. The one exception is the positive at 0.55 vs. the negative at 0.72 — the model scored that negative higher than that positive. So the empirical probability of correct ordering is $8/9 \approx 0.889$.

That's exactly the AUC we computed by integrating the staircase. Not a coincidence — the theorem says they have to match.

### 43.4.3 A sketch of why the theorem holds

We won't do a fully formal proof, but here's the geometric intuition.

At each threshold $\tau$, the classifier sorts examples into "above" and "below". A positive example with score $s_+$ contributes to the TPR for all $\tau \leq s_+$. A negative example with score $s_-$ contributes to the FPR for all $\tau \leq s_-$.

Now imagine walking along the ROC curve as $\tau$ decreases. Each step in the staircase corresponds to one example crossing the threshold. If a positive crosses first (i.e., has a higher score than the next-highest negative), the curve steps *up*. If a negative crosses first, it steps *right*.

The area under the staircase is, by elementary geometry, the count of pairs where the positive was reached before the negative — i.e., where the positive scored higher. Normalised by the total number of pairs ($P \cdot N$), this gives the probability $P(s_+ > s_-)$.

A reader who wants the formal derivation can find it in Hanley & McNeil's classic 1982 paper, or in any modern textbook on ROC analysis. For our purposes the geometric picture suffices.

### 43.4.4 The "did you flip a coin?" sanity check

A random classifier produces scores independent of labels. The probability that a random score is higher than another random score is exactly 1/2 (by symmetry — no preference either way). Hence AUC = 1/2 for a random classifier. That matches our intuition and the geometric picture: a random classifier traces the diagonal, and the area below the diagonal is 1/2.

A perfect classifier gives all positives a score higher than all negatives. Probability of correct ordering = 1. Hence AUC = 1.

Both boundary cases work out. Good.

---

## 43.5 What AUC is *not*

The interpretation we just nailed down is powerful, but it has limits. Naming the limits now will save you from misusing AUC later.

### 43.5.1 AUC doesn't tell you the operating point

Two models with identical AUC can have *very different* behaviour at the threshold you actually deploy. AUC averages over the entire ROC curve. If you only care about the top 1% of scores (e.g., "the 1% of customers most likely to churn"), the area at the far-left of the curve is what matters — but a model that's brilliant in the top 1% and mediocre everywhere else can have the same AUC as a model that's solid throughout. AUC will not distinguish them.

If your downstream use is "rank the top K" or "operate at a fixed FPR", look at the **partial AUC** (area under the curve restricted to the relevant FPR range), or just look at the curve.

### 43.5.2 AUC doesn't tell you about calibration

If you want to *interpret the model's score as a probability* — "this customer has a 23% chance of defaulting" — AUC doesn't help. AUC depends only on the rank ordering of scores, not their values. A model that outputs 0.9 for every positive and 0.1 for every negative has AUC 1.0; so does a model that outputs 0.501 for every positive and 0.499 for every negative. The first might be calibrated; the second is not. AUC ignores the difference.

Calibration is its own subject (we touched on it briefly in Chapter 32 for logistic regression, and we return to it in Chapter 73 for production-monitoring discussions). For now: if you need calibrated probabilities, evaluate calibration separately — reliability diagrams, Brier score, calibration error.

### 43.5.3 AUC is misleadingly stable under class imbalance

The interpretation $P(s_+ > s_-)$ doesn't depend on the class ratio — pick a random positive, pick a random negative, score them. So a fraud model that's 0.95 AUC at a 1% fraud rate has the same AUC if you re-balance the test set to 50% fraud (same model, same scores, different evaluation set). This is sometimes praised as a feature of AUC: it's "robust" to class imbalance.

But the praise is misleading. In a 1%-positive problem, **the negatives vastly outnumber the positives**. The FPR denominator (number of true negatives) is huge — say, 99% of your dataset. A model can have hundreds of false positives without barely moving the FPR. So the ROC curve looks good — the FPR stays low — while precision is dismal because the FPs outnumber TPs by 10:1.

This is the central reason we'll prefer PR curves over ROC for imbalanced problems in Chapter 44. AUC says "the ranking is good"; PR-AUC says "the *positive predictions* are good." The first can be high while the second is terrible.

### 43.5.4 AUC doesn't transfer across populations

If you train on one population and evaluate on another, AUC is sensitive to the score distribution in the new population, not just the ranking. A subtle point worth flagging: AUC on a balanced eval set may not predict AUC on production traffic, particularly if the score distribution drifts.

---

## 43.6 ROC vs. PR — a preview

In Chapter 44 we will derive the PR curve as a sibling of ROC, then argue at length that for severely imbalanced problems PR is the more honest visualisation. The teaser:

- ROC curve: x = FPR = $FP/(FP+TN)$, y = TPR = $TP/(TP+FN)$.
- PR curve: x = recall = $TP/(TP+FN)$, y = precision = $TP/(TP+FP)$.

The critical difference: ROC's denominator on the x-axis includes TN, which is *huge* when negatives are common. PR uses only TP and FP — both are small numbers, so each FP is "loud" on the precision axis.

For a balanced problem (say, classes 50–50), ROC and PR tell roughly the same story. For an imbalanced problem (1% positive, 99% negative), they tell very different stories. Pick your visualisation accordingly.

---

## 43.7 When to report AUC

Despite the caveats, AUC remains the standard single-number summary for binary classifiers, and it earns its place. A reasonable rule:

- **Report AUC** when you want to summarise classifier *capability* independent of operating point — when comparing many models in a leaderboard, or when the downstream use is ranking-based.
- **Don't rely on AUC alone** for cost-sensitive deployment decisions. Tune the threshold using F-beta or expected cost (Ch 42), and report both AUC (for "how good is the model overall?") and the operating-point metrics (for "what does it actually do in production?").
- **Pair with PR-AUC** for imbalanced problems. The two together give you a complete picture: ROC-AUC for ranking quality on the whole input distribution, PR-AUC for ranking quality specifically among positive predictions.

In my experience, the single sentence "we have AUC 0.92 and PR-AUC 0.74" tells me more about a model than any single number could.

---

## 43.8 The Spark and sklearn surface

### 43.8.1 sklearn

```python
from sklearn.metrics import roc_curve, roc_auc_score

# y_true is array of 0/1 labels; y_score is the array of predicted positive-class scores.
# The score can be a probability (from predict_proba) or the raw decision function output.
fpr, tpr, thresholds = roc_curve(y_true, y_score)
auc = roc_auc_score(y_true, y_score)

# Plot — by hand or with matplotlib.
import matplotlib.pyplot as plt
plt.plot(fpr, tpr, label=f"ROC (AUC={auc:.3f})")
plt.plot([0, 1], [0, 1], '--', color='gray', label="random")
plt.xlabel("FPR"); plt.ylabel("TPR")
plt.legend(); plt.show()
```

A few practical notes:

- `roc_curve` returns three arrays: FPR values, TPR values, and the threshold corresponding to each point. The threshold array is sorted in decreasing order — high thresholds first, low thresholds last.
- `roc_auc_score` accepts either probability scores or any score function. It doesn't require a probability — only that higher scores indicate "more positive."
- For multi-class, `roc_auc_score` supports `multi_class='ovr'` (one-vs-rest) or `'ovo'` (one-vs-one), with `average='macro'` or `'weighted'`. We'll discuss in Chapter 47.

### 43.8.2 pyspark.ml

Spark's BinaryClassificationEvaluator exposes AUC directly:

```python
from pyspark.ml.evaluation import BinaryClassificationEvaluator

evaluator = BinaryClassificationEvaluator(
    labelCol="label",
    rawPredictionCol="rawPrediction",   # the score column (NOT the 0/1 prediction)
    metricName="areaUnderROC"
)
auc = evaluator.evaluate(predictions_df)
```

Two quirks:

- The `rawPrediction` column for many Spark classifiers is a **DenseVector** of length $K$ (the number of classes), where element $k$ is the score for class $k$. BinaryClassificationEvaluator knows to extract the positive-class score automatically.
- Spark does **not** expose `roc_curve`-style (FPR, TPR, threshold) lists from the evaluator directly. To get the curve points (e.g., for plotting), use the underlying `BinaryClassificationMetrics` (Spark's RDD-based MLlib API):

  ```python
  from pyspark.mllib.evaluation import BinaryClassificationMetrics
  rdd = predictions_df.select("score", "label").rdd.map(lambda r: (float(r.score), float(r.label)))
  metrics = BinaryClassificationMetrics(rdd)
  metrics.areaUnderROC  # equivalent to the evaluator
  metrics.roc().collect()  # list of (FPR, TPR) tuples
  ```

We'll cover this in Chapter 66.

---

## 43.9 Worked summary: reading a real ROC curve

Here is a typical ROC curve as you might see it in a presentation:

```
   TPR
    1.0 ┤                          ────────────●  AUC = 0.92
        │                    ─────/
        │              ─────/
        │         ────/
    0.8 ┤      ──/
        │    ─/
        │  ─/
    0.6 ┤ /
        │/                  - - - - - - random (AUC = 0.5)
    0.4 ┤              - - -
        │         - - -
    0.2 ┤   - - -
        │- -
    0.0 ●─────────────────────────────────────► FPR
       0.0  0.1  0.2  0.4  0.6  0.8  1.0
```

What does this tell you?

- The curve sits well above the diagonal — the model has substantial signal.
- AUC = 0.92 — high ranking quality. For a random positive–negative pair, the model orders them correctly 92% of the time.
- The "knee" of the curve is roughly at $(0.1, 0.85)$. If you operate at FPR = 0.1, you catch 85% of positives. If you operate at FPR = 0.05 (further left), you'd catch maybe 75% — there's a steep tradeoff in the high-precision region.
- The curve is steepest at the bottom-left, which is the region you typically care about (low FPR). This is the desirable shape.

Three operating points might be marked on this curve:

- **High precision** ($\tau$ high, point near top-left): low FPR, high precision, moderate recall.
- **F1-optimal** ($\tau$ moderate, somewhere on the knee): balanced precision and recall.
- **High recall** ($\tau$ low, point near top-right): high TPR, high FPR, lower precision.

Picking among them is the threshold-tuning decision from Chapter 42. AUC tells you the *family* is good; the operating-point choice is separate.

---

## 43.10 Summary

The bones:

1. The **ROC curve** plots TPR (= recall) on the y-axis vs. FPR on the x-axis as the threshold sweeps from high to low. Every threshold = one point. Curve runs from $(0, 0)$ to $(1, 1)$, monotonically non-decreasing.
2. The **diagonal** $y = x$ is the random classifier. Above the diagonal = better than random; below = worse than random (flip predictions).
3. **AUC** = area under the ROC curve. Between 0 and 1; random = 0.5; perfect = 1.
4. **Probabilistic interpretation** of AUC: $P(s(x_+) > s(x_-))$ — the probability that a random positive is scored higher than a random negative. This makes AUC a *ranking quality* metric, not a classification metric.
5. AUC is **threshold-independent** — it summarises the whole curve, not one operating point. Two models with the same AUC can deploy very differently.
6. AUC is **mostly class-imbalance invariant** — same ranking quality for the same scores regardless of class ratio. But because FPR has the (huge) TN count in its denominator for imbalanced problems, AUC can look good while precision is poor. PR curves (Ch 44) fix this.
7. AUC tells you nothing about **calibration** — whether the model's probability outputs are believable as probabilities.
8. Use AUC to summarise classifier capability; pair with PR-AUC for imbalanced problems; tune thresholds separately with F-beta or expected cost.

If you can sketch an ROC curve, identify the no-information baseline, compute AUC from the staircase (or from the rank-ordering of scores), and state the probabilistic interpretation in one sentence — you have the chapter.

---

## 43.11 What this builds on / where this returns

**Builds on:** Chapter 42 (TPR/recall, FPR, the threshold dial). Chapter 9 (basic probability — the AUC interpretation uses the probability of a random pair being correctly ordered, which is a Mann-Whitney-Wilcoxon statistic). Part F's classifiers — all produce scores that can be ROC-evaluated.

**Returns:**

- **PR curves** — the partner visualisation that's more honest for imbalanced problems — *Chapter 44*.
- **Imbalanced classification** — the broader engineering response, where AUC's stability and its blind spot both matter — *Chapter 46*.
- **Multi-class AUC** (OvR and OvO averaging) — *Chapter 47*.
- **Spark evaluators in depth**, including `BinaryClassificationMetrics` for curve points — *Chapter 66*.

---

## 43.12 Exercises

Cold attempt all of them.

1. **From scratch on five points.** A classifier produces these scores on 5 examples:

   | rank | score | label |
   |:---:|:---:|:---:|
   | 1 | 0.91 | + |
   | 2 | 0.74 | − |
   | 3 | 0.68 | + |
   | 4 | 0.42 | + |
   | 5 | 0.19 | − |

   Sweep the threshold through all distinct values. At each threshold, compute (FPR, TPR) and plot the staircase. Compute AUC by trapezoidal area. Verify by counting pairs $(x_+, x_-)$ with $s(x_+) > s(x_-)$ out of $P \cdot N$.

2. **Why the diagonal?** Argue informally — three sentences — why a classifier that produces scores statistically independent of the label has expected ROC = the diagonal line $y = x$.

3. **The flipped-classifier exercise.** A classifier has AUC = 0.18 on a binary task. What does this mean? What should you do? What is the AUC of the resulting model?

4. **AUC = 1.0 vs. high accuracy.** Construct a tiny example (5 examples, 2 of each class as needed) where the classifier has AUC = 1.0 but accuracy at $\tau = 0.5$ is only 60%. Hint: think about what AUC requires vs. what accuracy at a specific threshold requires.

5. **AUC is rank-only.** Two classifiers, A and B, produce scores on the same data. Classifier A's scores are exactly $0.01 \times$ classifier B's scores. Their AUCs are equal. Explain why in one sentence, and explain what this means about AUC's ability to compare scores across different models.

6. **AUC under class-balance change.** A model's AUC is 0.85 on a test set with 50% positives. The same model is evaluated on a new test set with the same examples but only the negatives reweighted (10% positives, 90% negatives). What is the new AUC, and why? What might *change* between the two evaluations even though AUC doesn't?

7. **The probabilistic interpretation in words.** A teammate asks: "what does AUC = 0.78 actually mean?" Answer in one sentence using the probabilistic interpretation, no jargon.

8. **A trap.** A fraud-detection model has AUC = 0.96 on a test set with 0.1% fraud. The team is delighted and ships. Two weeks later they discover that at the operating threshold, precision is 4%. How can both be true at once? What did AUC fail to communicate?

9. **Partial AUC.** You only care about the model's behavior at very low FPR (say FPR < 0.05) because false positives are extremely expensive. Why is full AUC potentially misleading for your use case? What would you compute instead?

10. **AUC ≠ calibration.** Construct two classifiers on the same data with identical AUC but where one outputs probability-like scores in $[0, 1]$ near the truth and the other outputs scores in $[0.49, 0.51]$. What does AUC say about them? What does calibration say?

11. **Reading sklearn output.** `roc_curve(y_true, y_score)` returns three arrays: FPR values, TPR values, and thresholds. Why might the threshold array contain values outside $[0, 1]$ — say, a value of `1.95` — when the inputs were probabilities?

12. **Spark prediction column.** A new colleague writes:

    ```python
    BinaryClassificationEvaluator(
        labelCol="label",
        predictionCol="prediction",   # the 0/1 column
        metricName="areaUnderROC"
    )
    ```

    What is wrong? What should `predictionCol` be replaced with, and why does it matter?

<details>
<summary>Answers</summary>

1. P = 3, N = 2. Sweep thresholds:
   - $\tau > 0.91$: TP=0, FP=0. Point (0, 0).
   - $\tau = 0.91$: TP=1, FP=0. (0, 1/3).
   - $\tau = 0.74$: TP=1, FP=1. (1/2, 1/3).
   - $\tau = 0.68$: TP=2, FP=1. (1/2, 2/3).
   - $\tau = 0.42$: TP=3, FP=1. (1/2, 1).
   - $\tau = 0.19$: TP=3, FP=2. (1, 1).

   Areas: (0,0)→(0,1/3) Δx=0; (0,1/3)→(1/2,1/3) Δx=1/2, h=1/3, area=1/6; (1/2,1/3)→(1/2,2/3) Δx=0; (1/2,2/3)→(1/2,1) Δx=0; (1/2,1)→(1,1) Δx=1/2, h=1, area=1/2. Total = 1/6 + 1/2 = 2/3 ≈ 0.667.

   Pair check: 3·2 = 6 pairs. Pairs (pos_score, neg_score) and whether pos > neg:
   - (0.91, 0.74): ✓, (0.91, 0.19): ✓
   - (0.68, 0.74): ✗, (0.68, 0.19): ✓
   - (0.42, 0.74): ✗, (0.42, 0.19): ✓

   4 out of 6 ordered correctly = 4/6 = 2/3. Matches AUC = 0.667. ✓

2. If scores are independent of labels, then conditional on a threshold, the fraction of positives above equals the fraction of negatives above (in expectation, by independence). So TPR = FPR in expectation at every threshold, meaning the ROC curve lies on the diagonal.

3. AUC = 0.18 < 0.5 means the model's score function is anti-correlated with the truth — positives are scored *lower* than negatives. The right response is to flip the predictions (or negate the score). The new AUC is $1 - 0.18 = 0.82$.

4. Example: scores (0.6, 0.55, 0.51) on positives and (0.4, 0.45) on negatives. All three positives outscore both negatives, so AUC = 1.0. At $\tau = 0.5$, predictions: + + + − − vs. labels + + + − −. Accuracy = 5/5 = 100%. Hmm, that gives high accuracy too — bad example.

   Better: positives have scores (0.6, 0.55, 0.51, 0.50), negatives (0.4, 0.45). All positives outscore both negatives. AUC = 1.0. At $\tau = 0.5$, the positive at 0.50 is on the boundary; with $\tau \geq 0.5$ rule it's predicted positive (counts as correct) — try $\tau = 0.52$: 3 correctly predicted positive, 1 wrongly predicted negative, 2 correctly negative. Accuracy = 5/6 = 83%. Still high.

   Actually it's hard to get AUC = 1.0 with low accuracy because perfect ranking implies there exists a threshold that perfectly separates classes — any threshold between the lowest positive and highest negative score gives 100% accuracy. So this exercise is trickier than it sounds; the lesson is that AUC = 1.0 implies *some* threshold achieves 100% accuracy, but the default $\tau = 0.5$ may not be it. If the highest negative score is 0.45 and lowest positive is 0.51, then $\tau = 0.5$ is fine; but if the lowest positive is 0.20 and the highest negative is 0.15, all scores might be on the wrong side of $\tau = 0.5$. So: positives at 0.18, 0.15, 0.12; negatives at 0.10, 0.08. AUC = 1.0 (all positives outscore all negatives). At $\tau = 0.5$: all five predicted negative; accuracy = 2/5 = 40%. There you go.

5. AUC depends only on the rank ordering of scores, not their values. Scaling all scores by 0.01 preserves rank order, so AUC is unchanged. This means AUC cannot distinguish a well-calibrated model from a model with scores compressed into a narrow range — you can't compare absolute confidence levels using AUC alone.

6. AUC is roughly unchanged because it's a property of the score function applied to pairs, and reweighting negatives (without changing their scores) doesn't change pairwise orderings. What does change: the FPR computed at any specific threshold (because the denominator $FP + TN$ changes) and precision (because the FP-to-TP ratio at any operating point changes). Specifically, precision will drop dramatically when negatives are upweighted, even though AUC is constant. This is the lurking trap of Chapter 44.

7. "Pick any one positive and any one negative example. AUC = 0.78 means the model gives the positive a higher score than the negative 78% of the time."

8. AUC is high because the model ranks well *on average* across the distribution of pairs, but most pairs involve plentiful negatives. The model can rank positives in roughly the right region of the score distribution and still have negatives interleaving heavily with positives in the high-score region — leading to abysmal precision at any practical threshold (the FPs vastly outnumber TPs because there are 999× as many negatives). AUC failed to communicate the precision problem because FPR has TN in its denominator and TN is huge. PR-AUC would have shown the issue clearly.

9. Full AUC averages across the entire FPR range, including the high-FPR region you don't care about. A model that's mediocre in low-FPR and brilliant in high-FPR can have the same full AUC as a model with the opposite profile. You should compute partial AUC restricted to FPR ∈ [0, 0.05], or report TPR at FPR = 0.05 as a single number ("TPR@FPR=5%").

10. AUC is identical for both — both have the same rank ordering. Calibration says: the first model's probabilities are believable (you can use them as risk estimates); the second model's probabilities are meaningless (everything is near 0.5 regardless of the underlying truth). For ranking applications, either is fine. For probability-based downstream decisions (cost-sensitive thresholds, Bayesian decisions), only the first is usable.

11. sklearn's roc_curve adds a synthetic threshold at the beginning that is slightly higher than the maximum score (often `max(scores) + 1`) to guarantee the curve starts at FPR=0, TPR=0. So if scores are probabilities maxing at 0.95, the first threshold returned might be 1.95. It's a sentinel value, not a true probability. (More recent sklearn versions just use `max(score) + 1` or `np.inf`; the exact value isn't standardized.)

12. The `predictionCol` should be `rawPredictionCol` (or sometimes `probabilityCol`, depending on Spark version). BinaryClassificationEvaluator computes AUC, which is a **ranking** metric — it needs the continuous *score*, not the discrete 0/1 *prediction*. Using the 0/1 prediction column gives a degenerate ROC curve with only two points (the threshold sweep degenerates), and the AUC is essentially meaningless. Always confirm Spark evaluators are pointed at the right column type.

</details>
