# Chapter 42 — Classification Metrics: Confusion Matrix and Friends

> **Goal of this chapter:** to take every classification metric we used informally in Chapter 3 — accuracy, precision, recall, F1 — and make it mathematically precise. Every one of them is *derived* from a single, smaller object: the confusion matrix. Once you see the confusion matrix as the source, every other metric stops being a mysterious Python function and becomes an arithmetic identity that you could rebuild from scratch on a whiteboard.
>
> Picking the wrong metric is the most common practitioner mistake in classical ML. A team optimises for accuracy on an imbalanced dataset; six months later they discover their churn model never predicts churn. Another team optimises for F1 on a fraud problem where false positives cost a hundred times more than false negatives; the model is technically excellent and operationally useless. This chapter is the inoculation against that. We will treat each metric not as a number but as a *concept with its own geometry* — a specific question about the confusion matrix you are choosing to ask.

---

## 42.1 Where we are, and why we are doing this again

In Chapter 3 — the spam end-to-end tour — we ran into accuracy, met its dishonesty on imbalanced data, and introduced precision and recall through a worked confusion matrix. We then promised that Chapter 42 would do the formal version. This is that chapter.

You have already seen Parts B through G. You know what it means to fit a classifier (Ch 32 for logistic regression, Ch 33–34 for trees and forests, Ch 36 for gradient boosting). The output of every binary classifier is, fundamentally, the *same thing*: for each input $x$, the model produces a score $s(x) \in \mathbb{R}$ (or a probability $\hat{p}(x) \in [0, 1]$, which is just a re-scaled score). To turn that score into a *decision* — class 1 or class 0 — you compare it to a threshold $\tau$. That single thresholding act is what creates the confusion matrix.

So before we look at any metric: hold in your head the picture that there's a score, there's a threshold, and the confusion matrix is what you get when you collapse the continuous score into a discrete prediction. Every metric in this chapter is *one specific summary* of that collapse.

---

## 42.2 The confusion matrix — the source of everything

Suppose we have $n$ labelled validation examples. For each example we have a true label $y_i \in \{0, 1\}$ and a model prediction $\hat{y}_i \in \{0, 1\}$. The **confusion matrix** is a 2×2 table that counts how many examples fall into each combination of (true, predicted).

By convention — and we will stick with this convention for the rest of the chapter — the **rows are actual labels** and the **columns are predicted labels**. The class we care about (the "interesting" class, the rare one, the one we want to catch) is class 1, the **positive** class. The other is class 0, the **negative** class.

```
                       Predicted
                   ┌──────────┬──────────┐
                   │  ŷ = 1   │  ŷ = 0   │
                   │ (predict │ (predict │
                   │ positive)│ negative)│
       ┌───────────┼──────────┼──────────┤
       │  y = 1    │    TP    │    FN    │   ← row sum = # actual positives
Actual │ (positive)│          │          │
       ├───────────┼──────────┼──────────┤
       │  y = 0    │    FP    │    TN    │   ← row sum = # actual negatives
       │ (negative)│          │          │
       └───────────┴──────────┴──────────┘
                       ↑          ↑
                  column sum  column sum
                = # predicted = # predicted
                  positives     negatives
```

The four cell names are the universal language of binary classification, and you will see them in every paper, every documentation page, every interview question:

- **TP (true positive):** $y = 1$, $\hat{y} = 1$. The model correctly identifies a positive example.
- **FP (false positive):** $y = 0$, $\hat{y} = 1$. The model wrongly flags a negative as positive. (Also called a **Type I error** in classical statistics.)
- **FN (false negative):** $y = 1$, $\hat{y} = 0$. The model misses a positive. (Also called a **Type II error**.)
- **TN (true negative):** $y = 0$, $\hat{y} = 0$. The model correctly leaves a negative alone.

Four numbers. That is it. Every metric in this chapter is a fixed arithmetic combination of these four numbers. If you internalise the table — including which is row and which is column — you will never get confused about precision vs. recall again. (And yes, the literature is split on row-vs-column convention; sklearn uses rows=actual, columns=predicted, and that's what we use. Some statistics textbooks flip it. Always check.)

### 42.2.1 A running numerical example

Let's manufacture a confusion matrix we will refer to for the rest of the chapter. We have $n = 1{,}000$ validation examples. Of these, $100$ are truly positive (10% prevalence — a moderately imbalanced problem; think disease screening, churn, defect detection) and $900$ are truly negative.

We trained a classifier; here is its confusion matrix at threshold $\tau = 0.5$:

```
                Predicted positive    Predicted negative
   Actual +          80 (TP)               20 (FN)         → 100 actual +
   Actual −          20 (FP)              880 (TN)         → 900 actual −
                    100                   900              → 1000 total
                  predicted +           predicted −
```

So $TP = 80$, $FN = 20$, $FP = 20$, $TN = 880$. Out of 100 actual positives, the model caught 80 and missed 20. Out of 100 predicted positives, 80 were really positive and 20 were false alarms. Out of 900 actual negatives, 880 were correctly left alone and 20 were wrongly flagged.

Carry these numbers in your head — we're about to feed them into every metric in the chapter.

---

## 42.3 Accuracy — the seductive trap

The most obvious classification metric is **accuracy**: the fraction of predictions the model got right.

$$
\text{accuracy} = \frac{TP + TN}{TP + FP + FN + TN} = \frac{TP + TN}{n}
$$

For our running example:

$$
\text{accuracy} = \frac{80 + 880}{1000} = \frac{960}{1000} = 0.96 = 96\%
$$

Ninety-six percent. Sounds great. Sounds like a model worth shipping.

Now imagine a "model" that learned nothing, did nothing, and simply predicts class 0 (negative) for every input. Its confusion matrix would be:

```
                Predicted positive    Predicted negative
   Actual +           0  (TP)              100 (FN)
   Actual −           0  (FP)              900 (TN)
```

Accuracy:

$$
\frac{0 + 900}{1000} = 0.90 = 90\%
$$

A no-information baseline scores **90%** accuracy. Our trained model's "96%" looks dramatically less impressive once we anchor it against that baseline — we only beat the trivial classifier by 6 percentage points, and we did so by catching just 80 out of the 100 positives.

This is the canonical lesson of accuracy: **it averages over the dominant class and hides what's happening on the rare class.** Whenever the classes are imbalanced — which is most real classification problems — accuracy is a misleading headline metric. Quoting accuracy on imbalanced data is, in my experience, the single most common mistake in real-world classification reports. Catch yourself doing it. Catch others.

### 42.3.1 When *is* accuracy fine?

Three conditions, roughly:

1. **Classes are balanced** (say, 40–60% each). In that case a trivial classifier scores ~50%, and lifting to 90% is genuinely meaningful.
2. **Both error types are equally costly.** A false positive and a false negative cost the same. (Rare in practice, but possible — say, distinguishing two equally-common bird species in an academic study.)
3. **The downstream use cares about overall correctness, not per-class behaviour.** A spell-checker correctly classifying typed words; you really do just want the fraction right.

If any of these conditions fails, you need a more nuanced metric. The rest of the chapter is the nuance.

---

## 42.4 Precision — "of what we predicted positive, how much really was?"

Precision answers a specific question: of all the examples the model flagged as positive, what fraction *actually* belonged to the positive class?

$$
\text{precision} = \frac{TP}{TP + FP}
$$

Note the denominator: it is the **column sum** of the "predicted positive" column. We are restricting attention to the model's positive predictions and asking, of those, how many were right.

For our running example:

$$
\text{precision} = \frac{80}{80 + 20} = \frac{80}{100} = 0.80 = 80\%
$$

Eighty percent. Of the 100 emails (or transactions, or X-rays) the model flagged as positive, 80 were genuinely positive and 20 were false alarms.

### 42.4.1 What precision is sensitive to

Precision answers the question that matters when **false positives are the painful error**. Think of it as the rate at which the model "cries wolf":

- A spam filter wrongly junking a legitimate email is painful — the user might miss something important.
- A fraud-detection system wrongly blocking a customer's transaction is painful — the customer is angry and on the phone with support.
- A radiology screening tool wrongly flagging a tumor when none exists is painful — the patient undergoes unnecessary follow-up tests.

In each case, the cost of being wrong about a positive prediction (FP) is significant. So you optimise for precision: when the model says positive, you want it to be right.

Crucially, precision does **not** care about how many positives you missed (FN). Suppose we built a model that predicts positive for *only one* example — and that example is a true positive. Then $TP = 1$, $FP = 0$, $FN = 99$, $TN = 900$. Precision is $1/(1+0) = 100\%$. By precision alone, this is the best model ever. But it caught 1 positive out of 100 — it missed 99. Precision alone is a dangerously incomplete picture.

This is why precision is almost never reported alone. It is paired with recall.

### 42.4.2 The geometry of precision

Geometrically, precision is the rate of "true positives among predicted positives" — the fraction of the right-hand column of the confusion matrix that is in the top row.

```
                Predicted positive    Predicted negative
   Actual +    ┌──────────────┐
               │   TP = 80    │       FN = 20
               │              │
   Actual −    │   FP = 20    │       TN = 880
               └──────────────┘
                       ↑
              Precision = TP / (TP + FP)
              = fraction of THIS column
                that is in the top row
              = 80 / 100 = 80%
```

That's the visual: precision is "how much of the predicted-positive column is in the actual-positive row."

---

## 42.5 Recall — "of what really was positive, how much did we catch?"

Recall (also called **sensitivity**, **true positive rate**, **hit rate**) asks the complementary question: of all the examples that were *actually* positive, what fraction did the model catch?

$$
\text{recall} = \frac{TP}{TP + FN}
$$

Note this denominator: it is the **row sum** of the "actual positive" row. We are restricting attention to the real positives and asking, of those, how many we caught.

For our running example:

$$
\text{recall} = \frac{80}{80 + 20} = \frac{80}{100} = 0.80 = 80\%
$$

(Coincidentally the same as precision here — that's because $FP = FN$ in our example. In general they will differ.) Eighty percent of actual positives were caught; 20% slipped through.

### 42.5.1 What recall is sensitive to

Recall answers the question that matters when **false negatives are the painful error**:

- A cancer-screening tool missing an actual tumor is catastrophic — the patient goes untreated until much later.
- A fraud-detection system missing a fraudulent transaction is costly — the bank eats the chargeback.
- A search engine missing a relevant document is annoying — the user can't find what they need.

In each case, the cost of failing to flag a real positive (FN) is significant. So you optimise for recall: when something is positive, you want to catch it.

Recall does **not** care about how many false positives you raise. Suppose we built a model that predicts positive for *every* example. Then $TP = 100$, $FP = 900$, $FN = 0$, $TN = 0$. Recall is $100/(100+0) = 100\%$. Perfect recall. We caught every positive. But precision is $100/(100+900) = 10\%$ — 90% of our positive predictions were wrong. Recall alone is also dangerously incomplete.

### 42.5.2 The geometry of recall

```
                Predicted positive    Predicted negative
              ┌──────────────────────────────────────┐
   Actual +   │   TP = 80                FN = 20     │
              └──────────────────────────────────────┘
                       ↑
              Recall = TP / (TP + FN)
              = fraction of THIS row
                that is in the left column
              = 80 / 100 = 80%
   Actual −       FP = 20               TN = 880
```

Precision is "fraction of the predicted-positive column that's in the actual-positive row." Recall is "fraction of the actual-positive row that's in the predicted-positive column." These are not the same question, and that is the whole point.

### 42.5.3 Specificity — recall's mirror

There is one more single-row metric you should know. **Specificity** (also called **true negative rate**, TNR) is the analogue of recall on the *negative* class:

$$
\text{specificity} = \frac{TN}{TN + FP}
$$

It is the fraction of actual negatives we correctly left alone. For our example: $880/(880 + 20) = 880/900 = 97.8\%$.

The complement of specificity is the **false positive rate (FPR)**:

$$
\text{FPR} = 1 - \text{specificity} = \frac{FP}{TN + FP}
$$

For our example: $20/900 = 2.2\%$. FPR is the rate at which we false-alarm on the negative class. We will see this again — extensively — in Chapter 43 when we build the ROC curve.

So we have a family:

- Recall = TPR = sensitivity = $TP/(TP+FN)$ — caught-positive rate.
- Specificity = TNR = $TN/(TN+FP)$ — correctly-ignored-negative rate.
- FPR = $1 -$ TNR = $FP/(TN+FP)$ — false-alarm rate.
- Precision = $TP/(TP+FP)$ — when-we-said-positive-we-were-right rate.

Of these four, precision and recall are the two most often paired together — they answer the two halves of "how is the model doing on the positive class." Specificity is more common in medicine (where it pairs naturally with sensitivity). All of them live inside the same 2×2 confusion matrix.

---

## 42.6 F1 — collapsing two numbers into one

When you have two numbers (precision and recall) and you need to report *one* — for ranking models against each other, for a leaderboard, for a brief CEO meeting — you need a way to combine them.

The naive approach is to average them: $(P + R) / 2$. This is the **arithmetic mean**. It is a bad choice. Consider:

- Model A: precision 1.0, recall 0.0. Arithmetic mean: 0.5.
- Model B: precision 0.5, recall 0.5. Arithmetic mean: 0.5.

Both score the same under arithmetic mean. But Model A is a "predicts almost nothing" model — recall 0 means it never catches anything — while Model B is a balanced operating point. We want the combined metric to *prefer* Model B and *penalise* Model A.

The standard solution is the **F1 score**, defined as the **harmonic mean** of precision and recall:

$$
F_1 = \frac{2}{\frac{1}{P} + \frac{1}{R}} = \frac{2 P R}{P + R}
$$

The harmonic mean has a property the arithmetic mean lacks: it is dominated by the smaller of its two inputs. If either $P$ or $R$ is near zero, $F_1$ is near zero, regardless of how high the other one is.

Let's check on Model A and Model B:

- Model A: $F_1 = 2 \cdot 1.0 \cdot 0.0 / (1.0 + 0.0) = 0 / 1.0 = 0$. Correctly penalised.
- Model B: $F_1 = 2 \cdot 0.5 \cdot 0.5 / (0.5 + 0.5) = 0.5 / 1.0 = 0.5$.

Model B wins, as it should.

For our running example:

$$
F_1 = \frac{2 \cdot 0.80 \cdot 0.80}{0.80 + 0.80} = \frac{1.28}{1.60} = 0.80
$$

### 42.6.1 Why "harmonic" and not "geometric" or anything else?

You could equally use the **geometric mean** $\sqrt{P R}$ — it also goes to zero when either input does. Why the harmonic mean specifically? Two reasons.

First, the harmonic mean has a natural interpretation in this context. Precision = $TP/(TP+FP)$ and recall = $TP/(TP+FN)$ both have $TP$ in the numerator. The reciprocals are $1/P = 1 + FP/TP$ and $1/R = 1 + FN/TP$. Adding them: $1/P + 1/R = 2 + (FP + FN)/TP$. So

$$
F_1 = \frac{2}{1/P + 1/R} = \frac{2 TP}{2 TP + FP + FN}
$$

This form is suggestive: F1 is "twice the true positives" divided by "twice the true positives plus all the errors." It treats FP and FN symmetrically and equally.

Second, harmonic mean is the convention. The field standardised on it decades ago; you'll see it everywhere; deviating is more confusing than it's worth.

### 42.6.2 F-beta — when precision and recall aren't equally important

F1 weights precision and recall equally. But often they aren't equal. In a cancer screening tool, missing a tumor (FN) is much worse than a false alarm (FP), so we want a metric that weights recall more. In a spam filter, junking a legitimate email (FP) is worse than letting some spam through (FN), so we want a metric that weights precision more.

The generalisation is **F-beta**:

$$
F_\beta = (1 + \beta^2) \cdot \frac{P \cdot R}{\beta^2 \cdot P + R}
$$

The parameter $\beta$ controls the relative weight:

- $\beta = 1$ recovers F1 — equal weight.
- $\beta > 1$ weights **recall** higher. $F_2$ weights recall about 4× more than precision. Use when false negatives are expensive.
- $\beta < 1$ weights **precision** higher. $F_{0.5}$ weights precision about 4× more than recall. Use when false positives are expensive.

The exact meaning of "weights recall $\beta^2$ times more" comes from the derivation: $F_\beta$ is the harmonic mean of $P$ and $R$ where $R$ is given weight $\beta^2$ and $P$ is given weight $1$.

A quick sanity check on our running example with $\beta = 2$:

$$
F_2 = (1 + 4) \cdot \frac{0.80 \cdot 0.80}{4 \cdot 0.80 + 0.80} = \frac{5 \cdot 0.64}{4.0} = \frac{3.20}{4.0} = 0.80
$$

Same number, because precision equals recall in our example. The interesting cases are when they differ — then $F_2$ pulls toward recall and $F_{0.5}$ pulls toward precision.

In practice: pick $\beta$ based on the operational cost of FN vs. FP. If you can write the costs down explicitly (e.g., FN costs $50, FP costs $200), the F-score is a rough proxy and the cost matrix (Section 42.8) is more honest.

---

## 42.7 The precision–recall tradeoff and the threshold dial

Every classifier we have studied — logistic regression, random forest, GBT — produces not just a label but an underlying *score* $s(x) \in \mathbb{R}$ (or probability $\hat{p}(x) \in [0, 1]$). The label is just $s(x)$ thresholded:

$$
\hat{y}(x) = \begin{cases} 1 & \text{if } s(x) \geq \tau \\ 0 & \text{otherwise} \end{cases}
$$

The threshold $\tau$ is a knob, not a fixed property of the model. Most libraries default to $\tau = 0.5$ for probability outputs, but that default is **arbitrary**. You can — and should — tune $\tau$ to fit the business problem.

Moving $\tau$ shifts the confusion matrix in a specific, predictable way:

- **Raise $\tau$** → fewer predicted positives → fewer TPs (you miss some real positives) and fewer FPs (you false-alarm less). Precision typically rises (when you say positive, you're more confident), recall falls (you miss more positives).
- **Lower $\tau$** → more predicted positives → more TPs (you catch more real positives) and more FPs (you false-alarm more). Precision typically falls, recall rises.

This is the **precision–recall tradeoff**. It is not a deficiency of any one classifier — it is a structural feature of any score-based decision rule. Geometrically, as $\tau$ sweeps from $1$ down to $0$, the operating point traces out a curve in $(R, P)$ space — the precision–recall curve, which we will look at carefully in Chapter 44.

### 42.7.1 A worked example with three thresholds

Imagine a logistic regression with the same 1,000-example validation set as before. We sweep the threshold to three values and tally each confusion matrix:

**At $\tau = 0.3$** (more eager to predict positive):

```
                Predicted +    Predicted −
   Actual +        95              5
   Actual −        80            820
```

- $TP = 95$, $FP = 80$, $FN = 5$, $TN = 820$.
- Precision = $95/(95+80) = 95/175 = 54.3\%$
- Recall = $95/(95+5) = 95/100 = 95.0\%$
- F1 = $2 \cdot 0.543 \cdot 0.95 / (0.543 + 0.95) = 1.032 / 1.493 = 0.691$

**At $\tau = 0.5$** (our default):

- $TP = 80$, $FP = 20$, $FN = 20$, $TN = 880$.
- Precision = $80/100 = 80.0\%$
- Recall = $80/100 = 80.0\%$
- F1 = $2 \cdot 0.80 \cdot 0.80 / 1.60 = 0.80$

**At $\tau = 0.8$** (more conservative — only predict positive when very confident):

```
                Predicted +    Predicted −
   Actual +        55             45
   Actual −         3            897
```

- $TP = 55$, $FP = 3$, $FN = 45$, $TN = 897$.
- Precision = $55/(55+3) = 55/58 = 94.8\%$
- Recall = $55/(55+45) = 55/100 = 55.0\%$
- F1 = $2 \cdot 0.948 \cdot 0.55 / (0.948 + 0.55) = 1.043 / 1.498 = 0.696$

Three thresholds, three confusion matrices, three different (precision, recall, F1) triples. The model has not changed; the threshold has. Tabulated:

| $\tau$ | Precision | Recall | F1 |
|------:|----------:|-------:|---:|
| 0.3 | 0.543 | 0.950 | 0.691 |
| 0.5 | 0.800 | 0.800 | 0.800 |
| 0.8 | 0.948 | 0.550 | 0.696 |

The F1-optimal threshold among these three is $\tau = 0.5$ — but if we had been screening for cancer ($\beta = 2$, recall-weighted), we'd compute $F_2$ and find $\tau = 0.3$ better. If we had been screening for spam ($\beta = 0.5$, precision-weighted), $\tau = 0.8$ would win.

```
   Precision
      1.0 ┤                          ●  τ=0.8
          │
      0.95┤
          │
      0.80┤            ●  τ=0.5
          │
          │
      0.55┤   ●  τ=0.3
          │
          └──┬──────────┬──────────┬────► Recall
            0.5        0.8       0.95
```

Three operating points, one curve. The same model, repositioned three ways.

### 42.7.2 The lesson

A trained model is a *family* of classifiers indexed by the threshold. The training procedure picked the family; the threshold picks the member. Most practitioners who say "my model has precision X and recall Y" are reporting *one operating point* — usually the default $\tau = 0.5$ — without realising it's a choice. Knowing that the threshold can move, and being intentional about where you set it, is one of the cleanest separators between junior and senior ML practice.

We return to the full PR curve in Chapter 44, and to its ROC sibling in Chapter 43.

---

## 42.8 Cost-sensitive thresholding — beyond F-beta

F-beta lets you say "recall is $\beta^2$ times more important than precision." But in many real problems, the relative importance is not abstract — it is *literally* in dollars. A loan-default model: missing a defaulter costs the bank, say, $50{,}000$ on average (the unrecovered loan principal); wrongly flagging a creditworthy applicant costs $200$ (the opportunity cost of declining a profitable customer). The ratio is 250:1 toward recall, but that's an abstraction — the cost is *exactly* known.

For problems like this, the right metric isn't F1 or F-beta but **expected cost**:

$$
\text{cost}(\tau) = c_{FN} \cdot FN(\tau) + c_{FP} \cdot FP(\tau)
$$

where $c_{FN}$ and $c_{FP}$ are the per-error costs in dollars (or whatever business unit makes sense). You sweep $\tau$, compute the cost at each threshold, and pick the threshold that minimises expected cost.

(You can also include $c_{TP}$ and $c_{TN}$ — the cost or benefit of being correct — but typically these are zero or absorbed into the FN/FP costs.)

### 42.8.1 A worked example — the loan defaulter

Suppose at three thresholds we have:

| $\tau$ | FN | FP | $c_{FN} \cdot FN = \$50{,}000 \cdot FN$ | $c_{FP} \cdot FP = \$200 \cdot FP$ | Total cost |
|------:|---:|---:|----:|----:|------:|
| 0.3 | 5 | 80 | \$250,000 | \$16,000 | \$266,000 |
| 0.5 | 20 | 20 | \$1,000,000 | \$4,000 | \$1,004,000 |
| 0.8 | 45 | 3 | \$2,250,000 | \$600 | \$2,250,600 |

With these numbers, the cost-minimising threshold is $\tau = 0.3$ — the most aggressive, recall-favoring setting — because the cost of FN absolutely dominates. The default threshold $\tau = 0.5$ would cost the bank four times as much per validation set. The conservative threshold $\tau = 0.8$ would be a disaster.

If the cost ratio had been the other way — say $c_{FN} = \$200$, $c_{FP} = \$50{,}000$ — the optimal threshold would have flipped to $\tau = 0.8$.

This is the cost matrix in action. It is, in my experience, the most useful threshold-tuning lens for any real business problem where you can put dollar values on errors. Many teams stop at F1 because it requires no business conversation; the better teams have the business conversation and end up at expected cost.

### 42.8.2 What if you can't put dollar values on the errors?

Sometimes you genuinely can't. Medical, legal, ethical contexts often resist monetisation. In those cases, F-beta with a thoughtfully-chosen $\beta$ is the next-best thing. You'd pick $\beta$ in consultation with domain experts ("how many false alarms would you tolerate to catch one extra real case?"). The implicit cost ratio in F-beta is roughly $\beta^2$, so $\beta = 2$ encodes "recall is 4× more important than precision."

A third option, when you can't monetise but you can articulate constraints ("I need at least 95% recall"), is **operating-point pinning**: find the threshold that achieves the required recall, then accept whatever precision falls out. We will see this pattern in Chapter 44.

---

## 42.9 Multi-class confusion matrices — preview

We have spent this chapter on the binary case. For $K$-class problems, the confusion matrix is a $K \times K$ table:

$$
C_{ij} = \text{number of examples with true class } i \text{ and predicted class } j
$$

The diagonal is the correctly-classified count per class. Off-diagonal cells tell you which classes get confused with which.

Most binary metrics generalise — but the generalisation has choices (macro vs. micro vs. weighted averaging), and we leave the full treatment to Chapter 47. For now: know that the framework scales, but you'll have decisions to make about how to summarise.

---

## 42.10 The Spark and sklearn surface

We've spent the chapter on concepts. The code is, mercifully, short — but worth seeing once.

### 42.10.1 sklearn

The canonical sklearn pattern:

```python
from sklearn.metrics import (
    confusion_matrix, accuracy_score,
    precision_score, recall_score, f1_score, fbeta_score,
    classification_report
)

# y_true, y_pred are arrays of 0/1 labels.
cm = confusion_matrix(y_true, y_pred)
# Returns a 2D numpy array:
#   [[TN, FP],
#    [FN, TP]]
# Note sklearn's order: rows=actual, columns=predicted,
# and class 0 comes first. So TP is at [1, 1], not [0, 0].

print(f"Accuracy:  {accuracy_score(y_true, y_pred):.3f}")
print(f"Precision: {precision_score(y_true, y_pred):.3f}")  # for class 1
print(f"Recall:    {recall_score(y_true, y_pred):.3f}")
print(f"F1:        {f1_score(y_true, y_pred):.3f}")
print(f"F2:        {fbeta_score(y_true, y_pred, beta=2):.3f}")

# All-in-one summary:
print(classification_report(y_true, y_pred, target_names=['neg', 'pos']))
```

The `classification_report` is the workhorse — one call, all the per-class metrics, plus macro and weighted averages (Chapter 47).

A note on convention: sklearn's `confusion_matrix` returns the matrix with class 0 as the first row and column. So the layout is

```
            pred 0    pred 1
actual 0     TN         FP
actual 1     FN         TP
```

which is the *transpose-ish* of what most textbooks (and this chapter) draw with the positive class first. Always print and inspect the matrix before reading off values.

### 42.10.2 pyspark.ml — BinaryClassificationEvaluator and MulticlassClassificationEvaluator

Spark ML has two evaluators relevant here. **BinaryClassificationEvaluator** is restricted — it only exposes two metrics, both of which we'll cover next chapter:

```python
from pyspark.ml.evaluation import BinaryClassificationEvaluator

evaluator = BinaryClassificationEvaluator(
    labelCol="label",
    rawPredictionCol="rawPrediction",   # the score column
    metricName="areaUnderROC"           # or "areaUnderPR"
)
auc = evaluator.evaluate(predictions_df)
```

Note: BinaryClassificationEvaluator does **not** expose precision, recall, F1, or accuracy. For those, you use the multiclass evaluator (even on binary problems — binary is just $K=2$):

```python
from pyspark.ml.evaluation import MulticlassClassificationEvaluator

evaluator = MulticlassClassificationEvaluator(
    labelCol="label",
    predictionCol="prediction",   # the 0/1 prediction column, not the score
    metricName="f1"               # also: "accuracy", "weightedPrecision",
                                  # "weightedRecall", "weightedFMeasure",
                                  # "truePositiveRateByLabel", and more
)
f1 = evaluator.evaluate(predictions_df)
```

A few quirks of Spark's MulticlassClassificationEvaluator that catch people off-guard:

- It needs the **prediction** column (0/1 labels), not the **rawPrediction** column (scores). Don't confuse them.
- The default `f1` metric is the **macro-F1** averaged across classes (Chapter 47), not the binary F1 we computed by hand above. For our binary example, the two coincide only if you're careful about which class is "positive."
- For label-by-label metrics (e.g., "what is precision for class 1?"), use metric names like `precisionByLabel` with `metricLabel=1`.

We will return to all of this in Chapter 66, where we treat Spark evaluators systematically. For now: the conceptual base — confusion matrix, precision, recall, F1, F-beta — is exactly the same. Spark is just one specific calling convention.

---

## 42.11 Common pitfalls — a checklist

Things this chapter has implicitly warned you against; collect them once:

1. **Reporting accuracy on imbalanced data without anchoring to the trivial baseline.** Always compute "always predict majority class" accuracy as a baseline. If your model isn't beating it by a meaningful margin, your model is doing nothing.
2. **Reporting precision without recall, or recall without precision.** They are complementary. Quoting either alone is incomplete.
3. **Forgetting which class is "positive."** Precision and recall depend on which class you call positive. In sklearn, `pos_label=1` is the default; if your positive class is something else, override it. If two collaborators report "precision 90%" but disagree on the positive class, they are talking past each other.
4. **Treating $\tau = 0.5$ as fixed.** It is a default, not a law. Tune it.
5. **Optimising for F1 when the cost ratio is far from 1:1.** F1 implicitly assumes FP and FN cost the same. For asymmetric problems, use F-beta or expected cost.
6. **Cross-validating with non-stratified splits.** If a CV fold ends up with zero positives, precision is undefined (0/0) and recall is undefined. Use stratified CV (Chapter 22) for imbalanced classification.
7. **Computing precision/recall on the test set during model selection.** Use the validation set to tune the threshold; the test set is touched once at the end.

---

## 42.12 Summary

The bones:

1. The **confusion matrix** is the 2×2 table of (actual, predicted) counts. Rows = actual, columns = predicted (our convention). Four cells: TP, FP, FN, TN.
2. **Accuracy** = $(TP + TN)/n$. Misleading on imbalanced data.
3. **Precision** = $TP/(TP + FP)$. "Of what we predicted positive, what fraction really was?" Sensitive to false positives.
4. **Recall** (= TPR = sensitivity) = $TP/(TP + FN)$. "Of what really was positive, what fraction did we catch?" Sensitive to false negatives.
5. **Specificity** = $TN/(TN + FP)$. The negative-class analogue of recall.
6. **F1** = harmonic mean of P and R. Penalises imbalance between them. **F-beta** weights recall $\beta^2$ times more than precision.
7. Every classifier produces a score; thresholding the score produces the confusion matrix. **Moving the threshold trades off precision and recall** along a curve.
8. **Cost-sensitive thresholding** minimises $c_{FN} \cdot FN + c_{FP} \cdot FP$ — the right metric when error costs are known in dollars.
9. The pyspark.ml surface: BinaryClassificationEvaluator for AUC metrics; MulticlassClassificationEvaluator for accuracy / F1 / weighted P, R. sklearn's `classification_report` is the all-in-one summary.

If you can compute every metric in this chapter from a confusion matrix by hand, on a whiteboard, in under thirty seconds — you have the chapter.

---

## 42.13 What this builds on / where this returns

**Builds on:** Chapter 3 (informal confusion matrix, P/R, threshold for spam). Chapter 9 (sampling — relevant for the trivial-baseline argument and stratified evaluation). All of Part F (the supervised classifiers whose outputs we are evaluating). Part D's train/val/test discipline (Ch 21) — we evaluate metrics on val, report on test.

**Returns:**

- **ROC and AUC** (the threshold-sweep visualisation for FPR–TPR) — *Chapter 43*.
- **PR curves and PR-AUC** (the threshold-sweep for the precision–recall pair, and why this is the right curve for imbalanced problems) — *Chapter 44*.
- **Regression metrics** (the regression-side analogues of this chapter) — *Chapter 45*.
- **Imbalanced classification** (the broader engineering response — class weights, resampling, threshold tuning revisited) — *Chapter 46*.
- **Multi-class and multi-label** (the $K > 2$ generalisation; macro vs. micro vs. weighted averaging) — *Chapter 47*.
- **Spark evaluators in depth** — *Chapter 66*.

---

## 42.14 Exercises

Attempt all of these cold. Answers in the fold.

1. **Read the confusion matrix.** A model is evaluated on 500 examples. The confusion matrix is:

   ```
                 Pred +   Pred −
       Actual +    45      30
       Actual −    25     400
   ```

   Compute TP, FP, FN, TN. Then compute accuracy, precision, recall, specificity, FPR, and F1.

2. **The always-predict-majority baseline.** A dataset is 95% negative and 5% positive. A model that always predicts negative is evaluated. Compute the confusion matrix in terms of $n$ (the dataset size). Compute accuracy, precision (carefully — note the denominator), and recall on the positive class. What is this exercise demonstrating?

3. **Threshold direction.** A logistic regression's threshold is moved from $\tau = 0.5$ to $\tau = 0.7$. State, with one-sentence reasoning, what happens to: (a) the number of predicted positives, (b) precision, (c) recall, (d) specificity, (e) FPR. Assume the score is well-calibrated and the dataset is large.

4. **F-beta selection.** For each of the following problems, state which $\beta$ you would use ($\beta < 1$, $\beta = 1$, or $\beta > 1$) and why in one sentence. (a) Email spam detection. (b) Medical screening for an aggressive cancer. (c) Resume screening for a hiring funnel (positive = "shortlist this candidate"). (d) Industrial defect detection where defective products are recalled at significant cost.

5. **The wedding-photographer revisited.** Recall the spam example from Chapter 3 where the threshold was raised from 0.5 to 0.7 to stop wrongly junking the photographer's invoices. In terms of the confusion-matrix cells, what changed? Which metrics improved, and which got worse?

6. **F1 vs. arithmetic mean.** Compute F1 and the arithmetic mean of precision and recall for the following models:

   | Model | P | R |
   |:-----:|:-:|:-:|
   | A | 0.99 | 0.10 |
   | B | 0.70 | 0.70 |
   | C | 0.50 | 0.99 |

   Rank them by F1 and by arithmetic mean. Discuss any disagreement.

7. **Cost-sensitive thresholding.** A fraud-detection model has FN cost $1{,}000$ and FP cost $20$. At three thresholds, you observe:

   | $\tau$ | FN | FP |
   |:-----:|:-:|:-:|
   | 0.2 | 5 | 200 |
   | 0.5 | 30 | 40 |
   | 0.8 | 80 | 5 |

   Compute total cost at each threshold. Which threshold is optimal?

8. **From scratch.** Without looking back, write the formulas for precision, recall, F1, and accuracy in terms of TP, FP, FN, TN. Then write F-beta. (Self-check, no answer needed — verify against the chapter.)

9. **Diagnostic.** A team reports: "Our churn model has 92% accuracy." You know the data is 85% non-churners, 15% churners. What is the *one* follow-up question you should ask, and why? What is the *most* you can infer from 92% accuracy alone?

10. **A trap with sklearn's confusion_matrix output.** sklearn returns the confusion matrix with class 0 first: `[[TN, FP], [FN, TP]]`. A colleague writes `tn, fp, fn, tp = cm.ravel()` and reports a recall of `tn/(tn+fp) = 0.95`. What did they actually compute, and what is it called?

11. **Precision degeneracy.** Under what edge case is precision undefined (i.e., the formula gives 0/0)? Under what edge case is recall undefined? What does each tell you about the model?

12. **Specifying the positive class.** A library accepts a `pos_label` argument that defaults to 1. You have a dataset where "fraud" is encoded as `"F"` and "legit" as `"L"`. You call `precision_score(y_true, y_pred)` without specifying `pos_label` and get an error. Why? What is the right call?

<details>
<summary>Answers</summary>

1. TP=45, FP=25, FN=30, TN=400. Accuracy = (45+400)/500 = 89.0%. Precision = 45/70 = 64.3%. Recall = 45/75 = 60.0%. Specificity = 400/425 = 94.1%. FPR = 25/425 = 5.9%. F1 = 2·(0.643·0.600)/(0.643+0.600) = 0.7716/1.243 = 62.1%.

2. With $n$ examples: TP = 0, FP = 0, FN = 0.05n, TN = 0.95n. Accuracy = 0.95n/n = 95%. Precision = 0/(0+0) — undefined (division by zero); some libraries return 0 with a warning, treating "no predicted positives" as zero precision. Recall = 0/(0.05n) = 0. The exercise demonstrates that accuracy is dominated by the majority class on imbalanced data — a model that does nothing scores 95% — while precision and recall on the minority class expose that nothing is being caught.

3. (a) Predicted positives decrease — the bar to flag positive is higher. (b) Precision increases — the model only flags when very confident. (c) Recall decreases — fewer true positives caught. (d) Specificity increases — more true negatives correctly left alone. (e) FPR decreases — fewer false alarms. The model is "more conservative" — fewer alarms, but the ones raised are more reliable.

4. (a) Spam: $\beta < 1$ (say $\beta = 0.5$). Junking a real email is worse than letting some spam through. (b) Cancer: $\beta > 1$ (say $\beta = 2$ or higher). Missing a cancer is far worse than a false alarm that leads to follow-up tests. (c) Hiring: $\beta < 1$. The cost of wrongly recommending a weak candidate downstream (interview time, bad hire) is typically higher than missing a strong candidate (some loss but recoverable from other channels). Plausibly $\beta = 1$ in some firms. (d) Defects: $\beta > 1$ if shipping a defect causes a recall; $\beta < 1$ if false-positive recalls cost more than occasional defects. Likely $\beta > 1$.

5. Raising the threshold reduces predicted positives. TP decreases (we miss some real spam — FN rises). FP decreases more dramatically (the photographer's emails, scoring around 0.55-0.65, are no longer flagged — so the FPs that mattered to her disappear). Precision rises. Recall falls. Specificity rises (we wrongly junk fewer hams). FPR falls. F1 may rise or fall depending on the slope of the PR curve at that threshold.

6. Model A: F1 = 2(0.99)(0.10)/(0.99+0.10) = 0.198/1.09 = 0.182. AM = 0.545. Model B: F1 = 0.70. AM = 0.70. Model C: F1 = 2(0.50)(0.99)/(1.49) = 0.99/1.49 = 0.664. AM = 0.745. Rank by F1: B > C > A. Rank by AM: C > B > A. Disagreement on top spot: AM prefers C (which has very high recall but only moderate precision); F1 prefers B (balanced). F1 punishes Model A heavily because its recall is very low; AM lets the strong precision drag the average up to 0.545. This is exactly why F1 (harmonic mean) is preferred — it doesn't let one strong number paper over a near-zero number.

7. Cost(0.2) = 1000·5 + 20·200 = 5000 + 4000 = $9{,}000. Cost(0.5) = 1000·30 + 20·40 = 30,000 + 800 = $30{,}800. Cost(0.8) = 1000·80 + 20·5 = 80,000 + 100 = $80{,}100. Optimal threshold is $\tau = 0.2$ — aggressive, recall-favoring — because the FN cost dominates by 50×.

8. (Self-check.) Precision = TP/(TP+FP). Recall = TP/(TP+FN). F1 = 2·P·R/(P+R) = 2·TP/(2·TP + FP + FN). Accuracy = (TP+TN)/(TP+FP+FN+TN). F-beta = (1+β²)·P·R/(β²·P + R).

9. The follow-up question: "What is the precision and recall on the churn class?" The 92% accuracy could be obtained by a model that predicts "non-churner" for everyone — recall on churn = 0. Or it could be obtained by a model that catches 60% of churners with reasonable precision. From 92% alone, you cannot tell which. You CAN infer that the model is at least slightly better than the trivial baseline of 85% accuracy.

10. They computed TN/(TN+FP) = specificity, not recall. This is the negative-class analogue and is sometimes called "true negative rate." The bug is the ordering: sklearn returns `[[TN, FP], [FN, TP]]`, so `cm.ravel()` gives `(TN, FP, FN, TP)` in that order, not `(TP, FP, FN, TN)` as the variable names suggest. Standard fix: be explicit — `tn, fp, fn, tp = cm.ravel()` (using sklearn's actual order) or index the cells directly.

11. Precision is undefined when TP + FP = 0 — i.e., the model never predicts positive. Recall is undefined when TP + FN = 0 — i.e., there are no actual positives in the evaluation set (the evaluation set has no examples of the class you're measuring on). The first is a model issue (nothing is being flagged), the second is a data issue (the eval set is the wrong shape).

12. The error is because `pos_label=1` is the default but the labels are `"F"` and `"L"`, not integers. The right call is `precision_score(y_true, y_pred, pos_label="F")` to explicitly say fraud is the positive class.

</details>
