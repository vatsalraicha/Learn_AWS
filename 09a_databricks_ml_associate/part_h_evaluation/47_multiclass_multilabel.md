# Chapter 47 — Multi-Class and Multi-Label

> **Goal of this chapter:** to generalise the binary-classification evaluation machinery of Chapters 42–44 to two harder problems: **multi-class** classification, where each example belongs to exactly one of $K > 2$ classes, and **multi-label** classification, where each example can belong to several classes at once. The binary case turned out to require six metrics to characterise honestly; the multi-class case requires those same metrics *per class*, with three different ways of averaging them across classes — and the choice of averaging is the central decision. Multi-label is even subtler: it's not just "$K$ classes" — it's "any subset of $K$ classes per example", which breaks several of our binary intuitions.
>
> Two classes is the easy case. The exam, and reality, also live in $K > 2$. This chapter walks the generalisation carefully, including which Spark and sklearn calls correspond to which mathematical choice, so you don't end up reporting "F1 = 0.78" without being able to specify *which F1* you computed.

---

## 47.1 Multi-class classification — the setup

In binary classification we had labels $y \in \{0, 1\}$. In **multi-class classification** we have labels $y \in \{0, 1, 2, \ldots, K-1\}$, with $K > 2$. Examples:

- **Image classification with 10 classes** — CIFAR-10's airplane, automobile, bird, cat, deer, dog, frog, horse, ship, truck.
- **Document categorization** — classify a news article as one of {politics, sports, business, technology, entertainment}.
- **Multi-class credit risk** — {approve, deny, manual review} = a 3-class problem.
- **Medical triage** — patient routed to one of {ER, urgent care, outpatient, home discharge}.

The defining property: **exactly one label per example**. The classes are mutually exclusive — an article in our news categorization isn't both "sports" and "business"; it's one or the other. (If an article could legitimately be both, that's **multi-label** classification, which we cover in 47.7.)

Multi-class is a natural extension of binary, and most of the machinery generalises smoothly. But the generalisation has choices, and the choices matter.

---

## 47.2 Algorithms — native vs. binary decomposition

Some classifiers are **natively multi-class** — they handle $K > 2$ directly without modification. Others are **fundamentally binary** and need a decomposition strategy to handle multi-class.

### 47.2.1 Native multi-class algorithms

- **Softmax / multinomial logistic regression** (Chapter 32). Generalises binary logistic regression by replacing the sigmoid with the softmax function. Produces a probability vector $\hat{p}(x) \in [0,1]^K$ summing to 1 across classes.

- **Decision trees** (Chapter 33). At each leaf, the prediction is the majority class among training examples falling into that leaf. Works for any $K$ without modification.

- **Random forests and gradient-boosted trees** (Chapters 34–36). Inherit multi-class capability from their tree base learners. (GBT for multi-class is more subtle — one common implementation trains $K$ independent boosted ensembles, one per class, and softmaxes the outputs.)

- **k-nearest neighbors** (Chapter 37). The predicted class is the mode of the $k$ nearest neighbors' labels. Works for any $K$.

- **Naive Bayes** (Chapter 37). Computes $P(y = k \mid x)$ for each class via Bayes' rule; picks the argmax.

### 47.2.2 Binary classifiers needing decomposition

Some classifiers are inherently binary — the math only makes sense for a single decision boundary. **Support Vector Machines** (in their classical formulation) and certain specialised classifiers fall here. For these, two standard decomposition strategies exist:

**One-vs-Rest (OvR), also called One-vs-All (OvA).** For each class $k \in \{0, \ldots, K-1\}$, train a binary classifier:

> "Class $k$ vs. everything else."

That's $K$ binary classifiers. At prediction time, each classifier produces a score for "is this example class $k$ or not?" The predicted class is the one whose classifier gave the highest score.

For our 5-class news problem, OvR trains 5 classifiers:

- Politics vs. (sports, business, tech, entertainment)
- Sports vs. (politics, business, tech, entertainment)
- Business vs. (politics, sports, tech, entertainment)
- Tech vs. (politics, sports, business, entertainment)
- Entertainment vs. (politics, sports, business, tech)

Pros: simple, parallelizable (train classifiers independently), $K$ classifiers total — linear in $K$.

Cons: each binary classifier sees imbalanced data (one class as positive, $K - 1$ classes as negative — naturally $\frac{K-1}{K}$ negatives), which can hurt training. Scores from different OvR classifiers are not directly comparable on the same scale.

**One-vs-One (OvO).** For each *pair* of classes, train a binary classifier distinguishing only those two. That's $\binom{K}{2} = K(K-1)/2$ classifiers.

For 5 classes: $5 \cdot 4 / 2 = 10$ pairwise classifiers. At prediction time, each classifier votes for one of its two classes; the class with the most votes wins.

Pros: each pairwise classifier sees balanced data (assuming roughly equal class prevalences). Often more accurate than OvR.

Cons: quadratic in $K$ — for 100 classes, you train 4,950 classifiers. Expensive at scale.

In practice, OvR is more common because it scales linearly. The Databricks ML Associate exam world includes pyspark.ml's `OneVsRest` meta-classifier, which wraps any binary estimator into a multi-class one:

```python
from pyspark.ml.classification import LogisticRegression, OneVsRest

binary_lr = LogisticRegression(maxIter=100)
ovr = OneVsRest(classifier=binary_lr, labelCol="label", featuresCol="features")
ovr_model = ovr.fit(train_df)
```

`OneVsRest` is itself a meta-Estimator — it produces $K$ independent binary models internally and aggregates their predictions.

(Spark does NOT have a built-in `OneVsOne`. If you need OvO in Spark, you'd implement it manually or use scikit-learn.)

---

## 47.3 The multi-class confusion matrix

For binary, the confusion matrix was 2×2. For multi-class with $K$ classes, it's $K \times K$:

$$
C_{ij} = \text{number of examples with true class } i \text{ and predicted class } j
$$

The diagonal entries are correct predictions. Off-diagonal entries are *which* class an example was confused with — useful diagnostic information binary doesn't have.

For example, on a 3-class news problem (politics, sports, business — abbreviate P, S, B), suppose we evaluate on 500 examples:

```
                Predicted
              P    S    B
        ┌────┬────┬────┐
   P    │ 90 │  5 │ 10 │  → 105 actual politics
        ├────┼────┼────┤
A  S    │  3 │190 │  7 │  → 200 actual sports
        ├────┼────┼────┤
   B    │ 15 │ 12 │168 │  → 195 actual business
        └────┴────┴────┘
        108  207  185      → 500 total
```

We can read the diagnostic structure straight off:

- **Politics accuracy:** 90/105 = 85.7% — 90 correctly classified out of 105.
- **Sports accuracy:** 190/200 = 95.0%.
- **Business accuracy:** 168/195 = 86.2%.

We can also see the *confusions*:
- 10 political articles were misclassified as business, but only 5 as sports — politics is more often confused with business than sports.
- 12 business articles were misclassified as sports; 15 as politics.
- The model is fairly cleanly separating sports from the other two, which makes intuitive sense.

This kind of insight is lost in binary classification (where there's only one possible kind of mistake per direction). For multi-class, the confusion matrix is a *diagnostic tool*, not just a metric source.

### 47.3.1 Overall accuracy

Accuracy generalises directly:

$$
\text{accuracy} = \frac{\sum_k C_{kk}}{\sum_{i,j} C_{ij}} = \frac{\text{trace}(C)}{n}
$$

For our example: (90 + 190 + 168) / 500 = 448/500 = 89.6%.

The trivial baseline accuracy is the prevalence of the *largest* class — sports, at 200/500 = 40%. So we're substantially above baseline.

For balanced multi-class problems, accuracy is more honest than for binary imbalanced problems. But for imbalanced multi-class (one class is far more common than others), the same caveat applies — accuracy can be dominated by the majority class. We need per-class metrics.

---

## 47.4 Per-class precision, recall, F1

Every binary metric extends to multi-class by computing it **per class**, treating that class as "positive" and all others as "negative" — i.e., a temporary OvR view.

For class $k$:

- $TP_k$ = $C_{kk}$ (correctly classified as $k$).
- $FP_k$ = $\sum_{i \neq k} C_{ik}$ (other classes wrongly classified as $k$ — the column of class $k$ minus the diagonal).
- $FN_k$ = $\sum_{j \neq k} C_{kj}$ (class $k$ wrongly classified as something else — the row of class $k$ minus the diagonal).
- $TN_k$ = everything else.

Then:

$$
P_k = \frac{TP_k}{TP_k + FP_k}, \quad R_k = \frac{TP_k}{TP_k + FN_k}, \quad F_{1,k} = \frac{2 P_k R_k}{P_k + R_k}
$$

For our 3-class example:

**Politics (k=P):**
- $TP_P = 90$. $FP_P = 3 + 15 = 18$ (other classes predicted as politics — bottom of P column). $FN_P = 5 + 10 = 15$ (politics predicted as other — right of P row).
- $P_P = 90/108 = 83.3\%$. $R_P = 90/105 = 85.7\%$. $F_{1,P} = 2(0.833)(0.857)/(0.833+0.857) = 1.428/1.690 = 0.845$.

**Sports (k=S):**
- $TP_S = 190$. $FP_S = 5 + 12 = 17$. $FN_S = 3 + 7 = 10$.
- $P_S = 190/207 = 91.8\%$. $R_S = 190/200 = 95.0\%$. $F_{1,S} = 0.934$.

**Business (k=B):**
- $TP_B = 168$. $FP_B = 10 + 7 = 17$. $FN_B = 15 + 12 = 27$.
- $P_B = 168/185 = 90.8\%$. $R_B = 168/195 = 86.2\%$. $F_{1,B} = 0.884$.

Tabulating:

| Class | Precision | Recall | F1 | Support |
|-------|----------:|-------:|---:|--------:|
| Politics | 0.833 | 0.857 | 0.845 | 105 |
| Sports   | 0.918 | 0.950 | 0.934 | 200 |
| Business | 0.908 | 0.862 | 0.884 | 195 |

This is the per-class report. Per-class numbers tell you exactly where the model is strong (sports) and weak (politics) — useful information for the next iteration of feature engineering.

But for a single headline number, you need to *average* the per-class metrics. And there are three different ways to do that.

---

## 47.5 Macro, micro, and weighted averaging

When you summarise multi-class precision (or recall, or F1) with one number, you have three choices. Each treats the classes differently, and the choice matters.

### 47.5.1 Macro average

**Macro average** is the unweighted mean of per-class metrics:

$$
P_{\text{macro}} = \frac{1}{K} \sum_{k=1}^{K} P_k
$$

For our example: $P_{\text{macro}} = (0.833 + 0.918 + 0.908) / 3 = 0.886$.

Macro treats *every class equally*, regardless of how many examples it has. Sports (200 examples) and politics (105 examples) count the same in the average. This is the right choice when **classes are equally important** — for instance, in a medical triage system where every category matters regardless of frequency.

For *imbalanced* multi-class problems, macro is *honest* in the sense that it doesn't let the rare classes get drowned out. A model that aces the majority class and bombs on the minorities will have a *macro* F1 that reflects the bad minorities. This is usually the desired behaviour.

### 47.5.2 Weighted average

**Weighted average** weights each per-class metric by the support (number of examples) of that class:

$$
P_{\text{weighted}} = \sum_{k=1}^{K} \frac{n_k}{n} \cdot P_k
$$

For our example: $P_{\text{weighted}} = (105/500)(0.833) + (200/500)(0.918) + (195/500)(0.908) = 0.175 + 0.367 + 0.354 = 0.896$.

Weighted treats *every example equally*, so larger classes contribute more to the average. This is closer to overall correctness — if you ace the majority class and bomb the minorities, weighted F1 is still high.

This is sometimes what you want (when the larger classes really are more important — high-volume customer segments deserve more weight) and sometimes what you don't (when fairness across classes matters).

### 47.5.3 Micro average

**Micro average** is computed by aggregating TP, FP, FN globally across all classes, then computing the metric:

$$
P_{\text{micro}} = \frac{\sum_k TP_k}{\sum_k TP_k + \sum_k FP_k}
$$

For our example:
- $\sum TP = 90 + 190 + 168 = 448$.
- $\sum FP = 18 + 17 + 17 = 52$.

$P_{\text{micro}} = 448/(448+52) = 448/500 = 0.896$.

Hmm — same as weighted. Coincidence?

Not coincidence — **for multi-class classification (single-label) with the same support definitions, micro-precision = micro-recall = micro-F1 = accuracy.** This is because in single-label multi-class, every example is in exactly one class — so any FP for class $k$ is also an FN for some other class $j$. The sums $\sum FP_k$ and $\sum FN_k$ are equal (both equal the total number of misclassifications). So:

$$
P_{\text{micro}} = R_{\text{micro}} = \frac{\sum TP_k}{\sum TP_k + \sum FP_k} = \frac{\text{correct}}{n} = \text{accuracy}
$$

Micro averaging is *only different* from accuracy in **multi-label** settings (where examples can be in multiple classes, breaking the equivalence). For single-label multi-class, micro = accuracy; reporting both adds no information.

### 47.5.4 The choice tree

Summarising:

| Average | What it equals | When to use |
|---|---|---|
| **Macro** | unweighted mean of per-class metrics | classes equally important; concerned about minority classes |
| **Weighted** | mean weighted by support | overall correctness; larger classes more important |
| **Micro** | global aggregation; in single-label, equals accuracy | only meaningful for multi-label; otherwise just report accuracy |

A practical heuristic: **report macro AND weighted together** for multi-class problems. Their gap tells you about class-balance fairness. Identical macro and weighted = balanced data or uniformly good model. Weighted much higher than macro = good on the big classes, bad on the small ones.

For our example: macro F1 = (0.845 + 0.934 + 0.884)/3 = 0.888. Weighted F1 = (0.845·105 + 0.934·200 + 0.884·195)/500 = (88.7 + 186.8 + 172.4)/500 = 447.9/500 = 0.896. They're very close, indicating fairly balanced performance.

---

## 47.6 Multi-class ROC and AUC

ROC and PR curves are intrinsically binary — they need a "positive" and "negative" class. For multi-class, you can extend by:

**OvR ROC/AUC:** for each class $k$, treat it as positive and the rest as negative; compute the binary ROC curve. You get $K$ curves and $K$ AUC values. Macro-average them, or report individually.

**OvO ROC/AUC:** for each pair of classes, compute binary AUC. Average over pairs (with various weighting schemes).

The reported "multi-class AUC" in libraries is usually OvR macro-averaged AUC:

$$
\text{AUC}_{\text{macro, OvR}} = \frac{1}{K} \sum_k \text{AUC}_k
$$

sklearn:

```python
from sklearn.metrics import roc_auc_score
auc = roc_auc_score(y_true, y_score, multi_class='ovr', average='macro')
# or:
auc = roc_auc_score(y_true, y_score, multi_class='ovo', average='weighted')
```

`y_score` here must be a $(n, K)$ probability matrix (one score per example per class), not a single column. Most natively multi-class models (softmax LR, random forest with `predict_proba`) produce this directly.

---

## 47.7 Multi-label classification

Now the harder case. **Multi-label** classification: each example can have **multiple labels simultaneously**. The label is a *set*, not a single value.

Examples:

- **News tagging.** An article might be tagged with multiple topics: {politics, business, technology}.
- **Image multi-tagging.** A photo might contain {cat, dog, person, outdoor}.
- **Document categorization** in a topic taxonomy. A research paper might be in {machine learning, computer vision, fairness}.

The label is a *subset* of $K$ possible labels. The "label space" is $\{0, 1\}^K$ — every example is a $K$-dimensional binary vector indicating which labels are active. With $K$ labels, there are $2^K$ possible label sets.

### 47.7.1 The Binary Relevance approach

The simplest approach: treat each label as an independent binary classification problem. Train $K$ binary classifiers, each predicting one label.

For news tagging: train one classifier "is this politics?", one "is this business?", etc. At inference, predict each label independently; the predicted label set is the union of those marked positive.

This is the most common multi-label approach. Pros: simple, scales linearly in $K$, any binary classifier works. Cons: ignores label correlations — if "politics" and "business" frequently co-occur, Binary Relevance won't capture that.

More sophisticated approaches (Classifier Chains, label powerset, label-aware methods) are out of scope here.

### 47.7.2 Multi-label metrics

For multi-label, our binary metrics need adaptation:

**Hamming loss.** The fraction of (example, label) pairs that are incorrect. For $n$ examples and $K$ labels:

$$
\text{Hamming loss} = \frac{1}{nK} \sum_{i=1}^n \sum_{k=1}^K \mathbb{1}[y_{ik} \neq \hat{y}_{ik}]
$$

This is "what fraction of all label-decisions did the model get wrong?" Lower is better; 0 means perfect.

**Subset accuracy** (also called **exact match ratio**). The fraction of examples where the predicted label set *exactly matches* the true label set:

$$
\text{subset accuracy} = \frac{1}{n} \sum_{i=1}^n \mathbb{1}[\hat{y}_i = y_i]
$$

Strict — even one wrong label flips a whole example to "wrong." For high-$K$ problems with rich label sets, subset accuracy is usually very low.

**Per-label F1, averaged.** Compute F1 for each label (treating as binary), then average (macro, micro, or weighted). This is the most common reported metric for multi-label.

**Micro F1 in multi-label** is now different from accuracy (because sums of FP and FN are no longer equal). It's a global aggregation that treats each (example, label) decision as one prediction.

### 47.7.3 The softmax vs. sigmoid distinction

A subtle but important modeling point. For multi-class (single-label), the output layer uses **softmax** — outputs sum to 1, representing a probability distribution over classes.

For multi-label, you use **sigmoid per label** — each label has an independent probability in $[0, 1]$, and they don't sum to 1. A multi-label example might have predicted probabilities (politics=0.8, business=0.7, sports=0.1, tech=0.6, entertainment=0.05) — they sum to 2.25, which is fine because the model is asserting multiple labels.

Confusing softmax for sigmoid (or vice versa) is a common bug. Sigmoid + cross-entropy on a multi-label problem trains $K$ independent binary classifiers (Binary Relevance). Softmax + cross-entropy on a multi-label problem forces the labels to compete — only one label per example is allowed to have high probability, which is *wrong* for multi-label.

If you're using a deep-learning framework and outputting multi-label predictions: **use sigmoid activation + binary cross-entropy loss**, not softmax + categorical cross-entropy.

### 47.7.4 Multi-label is not heavily on the exam

Multi-label classification is briefly mentioned in the Databricks ML Associate scope but not deeply tested. The Spark MLlib API doesn't have first-class multi-label support — you'd implement Binary Relevance manually (train $K$ separate LR models, one per label). Most exam-relevant multi-class material lives in Section 47.5 (macro vs. micro vs. weighted).

---

## 47.8 The Spark and sklearn surface

### 47.8.1 sklearn

```python
from sklearn.metrics import (
    classification_report, confusion_matrix,
    precision_score, recall_score, f1_score
)

# Multi-class report
print(classification_report(y_true, y_pred, target_names=['A', 'B', 'C']))
# Outputs per-class precision, recall, F1, support;
# plus 'accuracy', 'macro avg', 'weighted avg' lines.

# Specific averages
f1_macro    = f1_score(y_true, y_pred, average='macro')
f1_weighted = f1_score(y_true, y_pred, average='weighted')
f1_micro    = f1_score(y_true, y_pred, average='micro')  # = accuracy for single-label
```

For multi-label, you pass `y_true` and `y_pred` as $(n, K)$ binary indicator matrices and specify `average='macro'` etc.

### 47.8.2 pyspark.ml — MulticlassClassificationEvaluator

Spark's `MulticlassClassificationEvaluator` is the workhorse:

```python
from pyspark.ml.evaluation import MulticlassClassificationEvaluator

evaluator = MulticlassClassificationEvaluator(
    labelCol="label",
    predictionCol="prediction",
    metricName="f1"   # default is "f1"
)
score = evaluator.evaluate(predictions_df)
```

Available `metricName` values:

| metricName | What it is |
|---|---|
| `accuracy` | overall accuracy |
| `f1` | weighted F1 (despite the name — confirm in the Spark docs for your version) |
| `weightedPrecision` | weighted-average precision |
| `weightedRecall` | weighted-average recall |
| `weightedFMeasure` | weighted F1 (synonymous with `f1` in current Spark) |
| `weightedTruePositiveRate` | weighted recall, same as weightedRecall |
| `weightedFalsePositiveRate` | weighted FPR |
| `truePositiveRateByLabel` | per-class recall; requires `metricLabel=k` to specify class |
| `precisionByLabel` | per-class precision; requires `metricLabel=k` |
| `fMeasureByLabel` | per-class F1; requires `metricLabel=k` |
| `hammingLoss` | for multi-label (Spark 3.x+) |
| `logLoss` | multi-class log loss |

A nuance worth flagging: the **default `metricName="f1"`** in Spark's MulticlassClassificationEvaluator computes **weighted F1** in current versions, NOT macro F1. This catches people coming from sklearn (where `f1_score` with default `average='binary'` for binary, or where you must explicitly pick an average for multi-class). Always confirm by reading the Spark API docs for your specific version. To get macro F1 in Spark, you'd have to compute per-class F1 manually (`fMeasureByLabel` with each label) and average yourself.

For multi-label problems, Spark's support is limited; usually you'd build $K$ independent binary models with `BinaryClassificationEvaluator` and aggregate metrics manually.

We treat all this in depth in Chapter 66.

---

## 47.9 A worked end-to-end multi-class example

Putting it together. We have a 4-class image-classification problem: {cat, dog, bird, fish}. Test set has 1,000 examples evenly split (250 each — balanced). The trained model produces this confusion matrix:

```
                  Predicted
              C    D    Bi   F
        ┌────┬────┬────┬────┐
   C    │220 │ 15 │  5 │ 10 │  → 250 actual cat
        ├────┼────┼────┼────┤
A  D    │ 20 │200 │ 10 │ 20 │  → 250 actual dog
        ├────┼────┼────┼────┤
   Bi   │  5 │  5 │225 │ 15 │  → 250 actual bird
        ├────┼────┼────┼────┤
   F    │  3 │ 12 │ 20 │215 │  → 250 actual fish
        └────┴────┴────┴────┘
        248  232  260  260
```

**Accuracy:** (220+200+225+215)/1000 = 860/1000 = 86%.

**Per-class metrics:**

| Class | TP | FP | FN | Precision | Recall | F1 |
|---|----:|---:|---:|---------:|-------:|---:|
| Cat   | 220 | 28 | 30 | 0.887 | 0.880 | 0.884 |
| Dog   | 200 | 32 | 50 | 0.862 | 0.800 | 0.830 |
| Bird  | 225 | 35 | 25 | 0.865 | 0.900 | 0.882 |
| Fish  | 215 | 45 | 35 | 0.827 | 0.860 | 0.843 |

(Computing FP for Cat: 20 + 5 + 3 = 28 — other classes predicted as cat. FN for Cat: 15 + 5 + 10 = 30 — cat predicted as other.)

**Macro F1:** (0.884 + 0.830 + 0.882 + 0.843) / 4 = 3.439/4 = 0.860.

**Weighted F1:** Each class has 250 support out of 1000, so the weights are 0.25 each. Weighted F1 = 0.25 · (0.884 + 0.830 + 0.882 + 0.843) = 0.860.

(For balanced data, macro and weighted coincide.)

**Micro F1 = accuracy = 0.86.**

The model is fairly uniformly good across classes — F1 ranges from 0.83 (dog, with the most off-diagonal mass) to 0.88 (cat, bird). Dogs are confused with cats more than the reverse (20 D→C vs. 15 C→D). Fish are sometimes confused with birds (20 F→Bi vs. 15 Bi→F). These are the kinds of insights you mine from the confusion matrix when iterating.

**If the class distribution were imbalanced** — say, 700 cats, 100 dogs, 100 birds, 100 fish — macro and weighted would diverge:

- Weighted F1 would be dragged up by cat's contribution (with weight 0.7).
- Macro F1 would treat all classes equally, exposing weak minority-class F1s.

For an imbalanced 4-class problem, **always look at macro F1 alongside weighted F1**. The gap is the diagnostic.

---

## 47.10 Common pitfalls

A consolidated list:

1. **Confusing softmax (single-label) and sigmoid (multi-label) output activations.** Train your model with the right loss for the right problem.

2. **Reporting "F1 = X" without specifying the average.** Macro? Weighted? Micro? Without saying which, the number is ambiguous.

3. **Using accuracy as the headline metric for imbalanced multi-class.** A 90/5/3/2-prevalence dataset with a "predict majority always" model scores 90% accuracy. Misleading.

4. **Forgetting that micro F1 = accuracy in single-label multi-class.** If you're reporting both, you're double-counting; pick one.

5. **Spark's default `metricName="f1"`** is weighted F1, not macro F1. Easy to misread.

6. **One-vs-Rest training without checking class imbalance.** Each binary classifier in OvR sees imbalanced data (one class as positive, all others as negative). Apply Chapter 46's techniques (class weights, threshold tuning) per binary classifier as needed.

7. **OvO without considering training cost.** For $K = 100$, OvO trains nearly 5,000 classifiers. OvR scales much better.

8. **Multi-label with `precision_score(y_true, y_pred)`** — sklearn's default averages might not be what you want. Specify `average='macro'` or `'micro'` explicitly.

---

## 47.11 Summary

The bones:

1. **Multi-class** classification: each example belongs to exactly one of $K > 2$ classes.
2. Algorithms: some native (softmax LR, trees, forests, kNN); some need binary decomposition. **OvR** (one-vs-rest): $K$ binary classifiers; linear in $K$. **OvO** (one-vs-one): $K(K-1)/2$ pairwise classifiers; quadratic in $K$. pyspark.ml has `OneVsRest`.
3. The **multi-class confusion matrix** is $K \times K$. Diagonal = correct; off-diagonal = confusions (diagnostically useful).
4. **Per-class metrics:** precision, recall, F1 for each class via the OvR view ($TP_k$, $FP_k$, $FN_k$).
5. **Three averaging schemes:**
   - **Macro**: unweighted mean of per-class metrics. Treats classes equally.
   - **Weighted**: mean weighted by support. Treats examples equally.
   - **Micro**: global aggregation. For single-label multi-class, micro = accuracy.
6. Report **macro AND weighted F1** together. Their gap diagnoses class-balance fairness.
7. **Multi-class AUC** typically means OvR macro-averaged AUC.
8. **Multi-label** classification: each example has a *set* of labels. Different from multi-class. Use **sigmoid per label** activation, not softmax. **Hamming loss**, **subset accuracy**, per-label F1 are the metrics. Binary Relevance is the simplest approach.
9. **Spark surface:** `MulticlassClassificationEvaluator` with `metricName ∈ {accuracy, f1 (weighted), weightedPrecision, weightedRecall, precisionByLabel, fMeasureByLabel, ...}`. The default `f1` is weighted; for macro you compute manually.

If you can build a multi-class confusion matrix, compute per-class precision/recall/F1, average them by macro/weighted/micro and explain the difference — you have the chapter.

---

## 47.12 What this builds on / where this returns

**Builds on:** Chapter 32 (softmax / multinomial LR — the native multi-class generalisation of logistic regression). Chapter 42 (binary precision, recall, F1). Chapter 43 (binary ROC/AUC). Chapter 46 (imbalanced classification — applies per-class).

**Returns:**

- **Spark MulticlassClassificationEvaluator and BinaryClassificationEvaluator** in detail — *Chapter 66*.
- **End-to-end multi-class projects** — none directly in the capstone (Lending Club is binary), but the patterns generalise.

---

## 47.13 Exercises

Cold attempt.

1. **Build a multi-class confusion matrix.** A model on 3-class problem {A, B, C} is evaluated on 100 examples. Predictions break down:
   - 30 actual A: 25 predicted A, 3 predicted B, 2 predicted C.
   - 40 actual B: 5 predicted A, 32 predicted B, 3 predicted C.
   - 30 actual C: 2 predicted A, 4 predicted B, 24 predicted C.

   Build the 3×3 confusion matrix. Compute per-class precision, recall, F1. Compute macro F1 and weighted F1.

2. **Micro = accuracy proof.** Argue informally why, in single-label multi-class classification, micro F1 = accuracy. Where does the equivalence break for multi-label?

3. **Macro vs. weighted divergence.** A 3-class problem has 100 examples with prevalences 80/15/5. The model has F1 = 0.95 on the majority class, 0.50 on the second class, 0.20 on the third. Compute macro F1 and weighted F1. Discuss which is more honest.

4. **OvR vs. OvO trade-off.** For a 50-class problem, how many binary classifiers does OvR train? How many does OvO train? Which would you choose, and why?

5. **The Spark `metricName` confusion.** A colleague reports "F1 = 0.78" computed using Spark's MulticlassClassificationEvaluator with default settings. Their reviewer reports "F1 = 0.62" computed using `f1_score(y_true, y_pred, average='macro')` in sklearn. Why might the two disagree on the same data? Whose number is "correct"?

6. **Softmax vs. sigmoid.** A team is building a multi-label tagging model with $K = 10$ possible tags per news article. They use a final softmax layer + categorical cross-entropy loss. What's wrong with this choice?

7. **Multi-label Hamming loss.** A 3-label problem (labels A, B, C) has 4 test examples. True labels and predictions:

   | i | True | Predicted |
   |--:|---|---|
   | 1 | {A, B}    | {A, C}    |
   | 2 | {B}       | {B}       |
   | 3 | {A, C}    | {A, C}    |
   | 4 | {A, B, C} | {B, C}    |

   Compute Hamming loss. Compute subset accuracy.

8. **Class-by-class diagnostic.** A multi-class confusion matrix shows that class A is correctly predicted 90% of the time, but 9% of class B examples are predicted as class A. What does this asymmetry suggest? What feature engineering or modeling fix would you investigate?

9. **OneVsRest in Spark.** Write the PySpark code to train a OneVsRest model wrapping a LogisticRegression base learner on a multi-class problem with `featuresCol="features"` and `labelCol="label"`.

10. **Macro AUC vs. weighted AUC.** When would you prefer macro AUC and when weighted AUC for a multi-class problem? Give one scenario for each.

11. **Multi-label class weights.** In a multi-label problem with very rare labels (some labels apply to only 1% of examples), can you still use class weights to balance the loss? How would you set them up?

12. **Adversarial confusion matrix.** A team reports macro F1 = 0.92 on a 5-class problem. You ask to see the confusion matrix; it shows that one class (5% prevalence) has F1 = 0.45 and the other four (each 23.75% prevalence) have F1 in the range 0.93–0.97. How is the macro F1 still 0.92? Show the calculation.

<details>
<summary>Answers</summary>

1. Confusion matrix:
   ```
            A   B   C
       A   25   3   2
       B    5  32   3
       C    2   4  24
   ```
   For class A: TP=25, FP=5+2=7, FN=3+2=5. P=25/32=0.781, R=25/30=0.833, F1=0.806.
   For class B: TP=32, FP=3+4=7, FN=5+3=8. P=32/39=0.821, R=32/40=0.800, F1=0.810.
   For class C: TP=24, FP=2+3=5, FN=2+4=6. P=24/29=0.828, R=24/30=0.800, F1=0.814.
   Macro F1: (0.806 + 0.810 + 0.814)/3 = 0.810.
   Weighted F1: (30/100)(0.806) + (40/100)(0.810) + (30/100)(0.814) = 0.242 + 0.324 + 0.244 = 0.810. (Same, by coincidence of nearly-equal per-class F1.)

2. In single-label multi-class, each FP for class k corresponds to an FN for some other class j (the example that was wrongly predicted as k actually belongs to j, so j has an FN). So $\sum FP_k = \sum FN_k$ = total misclassifications. Micro precision = $\frac{\sum TP}{\sum TP + \sum FP}$ = $\frac{\text{correct}}{n}$ = accuracy. Same for micro recall and F1. In multi-label, each (example, label) can independently be FP or FN — they're no longer paired — so the sums diverge and micro F1 ≠ accuracy.

3. Macro F1 = (0.95 + 0.50 + 0.20)/3 = 0.55. Weighted F1 = (80/100)(0.95) + (15/100)(0.50) + (5/100)(0.20) = 0.76 + 0.075 + 0.01 = 0.845. Weighted is higher (0.845) because the majority class is doing well and dominates. Macro (0.55) honestly reflects that two of three classes are poor. If you care about minority classes (often you should), macro is the honest metric; if overall correctness is what matters, weighted is fine. Reporting both shows the truth.

4. OvR: 50 binary classifiers. OvO: 50·49/2 = 1,225 classifiers. OvR is the practical choice — 24× fewer classifiers, linear in K, easier to train and serve. OvO might give slightly better accuracy on small-K problems but at heavy cost for K=50.

5. Spark's default is weighted F1; sklearn was computing macro F1. They're measuring different things, neither "incorrect" — but they're not comparable. Always specify which F1. To reconcile: have the colleague pass `metricName="f1"` (already default) AND verify they're seeing weighted; have the reviewer compute weighted in sklearn (`average='weighted'`) for the same comparison. Best practice: report both macro and weighted for any multi-class problem.

6. Softmax forces the output probabilities to sum to 1 — i.e., the model is saying "this article belongs to exactly one tag." But it's a multi-label problem — articles can have multiple tags simultaneously. The correct choice is sigmoid per label + binary cross-entropy per label, treating each label independently (Binary Relevance). Softmax + categorical cross-entropy will train a multi-class single-label classifier, which is the wrong problem.

7. Hamming loss: example 1 (true {A,B}, pred {A,C}) — A correct, B is FN, C is FP → 2 wrong labels out of 3. Example 2 (true {B}, pred {B}) — 0 wrong. Example 3 — 0 wrong. Example 4 (true {A,B,C}, pred {B,C}) — A is FN, B correct, C correct → 1 wrong. Total wrong: 2+0+0+1 = 3 out of 4×3 = 12 label-decisions. Hamming loss = 3/12 = 0.25. Subset accuracy: example 2 and 3 are exact matches (2/4 = 0.50).

8. The asymmetry suggests features "look like" class A when the true label is B more often than the reverse. Possible causes: B has more variability and the model defaults to A; the features overlap heavily in some region with A's distribution dominating. Fixes: examine which examples of B are misclassified (are they border cases?); add features that specifically distinguish B from A; engineer interactions; consider per-class threshold tuning (raise the bar to predict A so borderline cases go to B).

9. ```python
   from pyspark.ml.classification import LogisticRegression, OneVsRest
   base = LogisticRegression(maxIter=100, featuresCol="features", labelCol="label")
   ovr = OneVsRest(classifier=base, labelCol="label", featuresCol="features",
                    predictionCol="prediction")
   ovr_model = ovr.fit(train_df)
   predictions = ovr_model.transform(test_df)
   ```

10. Macro AUC: when class importance is equal regardless of prevalence — e.g., a multi-class medical diagnosis where every disease matters equally. Weighted AUC: when downstream cost is proportional to class prevalence — e.g., a recommendation system where the dominant class drives the most revenue.

11. Yes — you'd compute per-label weights inversely proportional to label prevalence. In Spark with Binary Relevance, train K independent binary classifiers, each with its own weightCol computed from that label's prevalence. In sklearn with a multi-output classifier, you can pass `class_weight='balanced'` per label, or use sample_weight that accounts for which labels are present in each example (more complex).

12. Macro F1 = (0.45 + 0.93 + 0.94 + 0.95 + 0.97)/5 = 4.24/5 = 0.848 ≈ 0.85. Hmm, not 0.92. Let me re-read — the question says macro is 0.92. So with one class at 0.45 and others 0.93-0.97, you can't get macro = 0.92. The question is checking whether you notice this is impossible. If F1=0.45 on one class out of 5 with the others averaging ~0.95, macro is at most (0.45+4·0.97)/5 = 0.864. The team's report of macro = 0.92 is inconsistent with these per-class F1s, meaning either they reported the wrong number, computed weighted (which would be (0.45·5 + 0.93·23.75 + 0.94·23.75 + 0.95·23.75 + 0.97·23.75)/100 = (2.25 + 22.09 + 22.32 + 22.56 + 23.04)/100 = 92.27/100 = 0.923 — that matches!), or there's a math error. The "0.92" is almost certainly weighted F1, misreported as macro. Always recompute from per-class numbers; never trust a single summary statistic without context.

</details>
