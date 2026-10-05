# Chapter 35 — Boosting from First Principles — AdaBoost

> **Goal of this chapter:** to introduce **boosting**, the sequential alternative to bagging — and to do so with the algorithm that started it all, AdaBoost. Boosting sounds at first like a competitor to bagging (Chapter 34), but it's actually a fundamentally different idea: instead of training many trees in parallel on independent bootstrap samples, boosting trains trees *sequentially*, with each new tree focused on what the previous trees got wrong. AdaBoost is the original — the algorithm that, in 1996, convinced the ML community that this idea worked. Understanding AdaBoost is how you understand what XGBoost (Chapter 36) is doing. We'll go slow.

---

## 35.1 A different intuition: focus on the hard examples

Random forests build many trees in parallel. Each tree sees a random subset of rows and features; they're trained independently; we average them.

Boosting takes a different starting point. What if, instead of treating all training examples equally, we made the model **focus on the examples it currently gets wrong?**

The intuition. Train a weak classifier on the data. It will get some examples right, some wrong. Increase the weight on the wrong ones — re-train the next classifier on this re-weighted distribution. The new classifier will be incentivized to fix what the previous one missed. Combine the predictions weighted by each classifier's accuracy. Repeat.

This is a fundamentally sequential idea. The $t$-th classifier depends on what classifiers $1, \ldots, t-1$ got wrong. You cannot parallelize across the boosting iterations the way you can across trees in a forest.

The miracle is that this works — and it works *so well* that boosted decision trees, in their modern form (Chapter 36), dominate tabular ML benchmarks. AdaBoost showed that the miracle was real. Gradient boosting generalized it. XGBoost and LightGBM made it production-ready.

We'll walk AdaBoost step by step.

---

## 35.2 The AdaBoost algorithm

We have $n$ training examples for binary classification with labels $y_i \in \{-1, +1\}$ (note the $\pm 1$ encoding — not $\{0, 1\}$. AdaBoost is most cleanly stated this way, for reasons that will become apparent.) The algorithm:

```
Initialize weights w_i^(1) = 1/n for all i = 1, ..., n
For t = 1, 2, ..., T:
    1. Train a weak learner h_t on the training set,
       using the current weights w^(t) to weigh examples.
       (h_t outputs values in {-1, +1}.)
    2. Compute the weighted error of h_t:
           ε_t = Σ_i w_i^(t) · I[h_t(x_i) ≠ y_i]
       (Sum of weights of misclassified examples.)
    3. If ε_t >= 0.5, stop — the learner is worse than random.
    4. Compute the learner's "voting weight":
           α_t = (1/2) · log((1 - ε_t) / ε_t)
       (Larger when ε_t is smaller; positive when ε_t < 0.5.)
    5. Update example weights:
           w_i^(t+1) = w_i^(t) · exp(-α_t · y_i · h_t(x_i)) / Z_t
       where Z_t is a normalization constant making weights sum to 1.

Final predictor: H(x) = sign(Σ_t α_t · h_t(x))
```

Let's unpack each step.

### 35.2.1 The weak learner

A **weak learner** is any classifier that does *slightly* better than random — error < 0.5. AdaBoost requires nothing more. In the original AdaBoost paper, the weak learners are usually **decision stumps**: one-level decision trees (single split). Stumps are about as weak as it gets and still useful — they capture "if feature $j$ is above threshold $t$, predict +1; otherwise -1" and nothing more.

Why stumps? Because the boosting process will combine many of them. A single stump is weak; an ensemble of 100 stumps, each focused on a different aspect of the data, can be powerful.

### 35.2.2 The voting weight α

Step 4 derives the voting weight as

$$
\alpha_t = \frac{1}{2} \log \frac{1 - \varepsilon_t}{\varepsilon_t}
$$

This is the log-odds of being correct. If $\varepsilon_t = 0.5$ (no better than random), $\alpha_t = 0$ — the learner is given zero voting weight. If $\varepsilon_t \to 0$ (perfect classifier), $\alpha_t \to \infty$ — infinite confidence. If $\varepsilon_t = 0.1$, $\alpha_t = 0.5 \log(0.9/0.1) = 0.5 \log 9 \approx 1.10$.

Why is this the right voting weight? Because it's *exactly* the weight that minimizes the exponential loss after this step. We'll prove this in §35.4.

### 35.2.3 The weight update

Step 5 is the heart of AdaBoost:

$$
w_i^{(t+1)} \propto w_i^{(t)} \cdot \exp(-\alpha_t \cdot y_i \cdot h_t(x_i))
$$

The exponent's sign: $y_i \cdot h_t(x_i) = +1$ if the prediction matches the label, $-1$ otherwise. So:

- **Correctly classified** ($y_i h_t = +1$): weight multiplied by $\exp(-\alpha_t)$. Since $\alpha_t > 0$, this is $< 1$ — weights *decrease*.
- **Misclassified** ($y_i h_t = -1$): weight multiplied by $\exp(+\alpha_t) > 1$ — weights *increase*.

The misclassified examples become more important in the next iteration. The correctly classified ones become less important. The next weak learner is trained on this re-weighted distribution and is forced to focus on what the current ensemble is getting wrong.

The magnitude of the up-weighting depends on $\alpha_t$. If the current learner is very accurate ($\alpha_t$ large), the few examples it misses get *strongly* up-weighted. If the current learner is only marginally better than random ($\alpha_t$ small), weight updates are mild.

### 35.2.4 The final predictor

$$
H(x) = \text{sign}\left( \sum_{t=1}^T \alpha_t h_t(x) \right)
$$

Each weak learner's vote $h_t(x) \in \{-1, +1\}$ is multiplied by its weight $\alpha_t$ and summed. The sign of the sum is the final prediction. The *magnitude* of the sum is a confidence score — a kind of "margin" that we'll discuss in §35.5.

---

## 35.3 Why these specific formulas?

The exact formulas for $\alpha_t$ and the weight update aren't arbitrary. They drop out of a single principle: **AdaBoost is gradient descent on the exponential loss in function space.** We'll derive this in §35.4 and then everything will click.

### 35.3.1 The exponential loss

Define the exponential loss:

$$
L_{\text{exp}}(y, \hat{f}(x)) = \exp(-y \cdot \hat{f}(x))
$$

where $\hat{f}(x) = \sum_t \alpha_t h_t(x)$ is the unsignthed combined prediction (before taking the sign). For binary $y \in \{-1, +1\}$:

- When $y \hat{f}(x) > 0$ (correct sign), $L_{\text{exp}}$ is between 0 and 1 — small loss.
- When $y \hat{f}(x) < 0$ (wrong sign), $L_{\text{exp}} > 1$ and grows exponentially as the margin becomes more negative.

Sum across examples to get the training loss:

$$
\mathcal{L}(\hat{f}) = \sum_i \exp(-y_i \hat{f}(x_i))
$$

Compare to:
- 0-1 loss: $I[y_i \neq \hat{f}(x_i)]$ — what we actually care about, but discontinuous.
- Cross-entropy: $\log(1 + \exp(-y_i \hat{f}(x_i)))$ — the logistic loss, smoother penalty for wrong predictions.

The exponential loss penalizes wrong predictions *more aggressively* than cross-entropy. This is both a feature (forces focus on hard examples) and a bug (vulnerable to label noise — a single mislabeled example accumulates exponential penalty).

### 35.3.2 AdaBoost as forward stagewise gradient descent

Now the punchline. Suppose we've already built $\hat{f}_{t-1}(x) = \sum_{s=1}^{t-1} \alpha_s h_s(x)$. We want to add a single new term $\alpha_t h_t(x)$ to minimize the new training loss

$$
\mathcal{L}(\hat{f}_t) = \sum_i \exp(-y_i (\hat{f}_{t-1}(x_i) + \alpha_t h_t(x_i)))
$$

$$
= \sum_i \exp(-y_i \hat{f}_{t-1}(x_i)) \cdot \exp(-y_i \alpha_t h_t(x_i))
$$

Let $w_i^{(t)} = \exp(-y_i \hat{f}_{t-1}(x_i))$ (the "weight" of example $i$ at iteration $t$). Then

$$
\mathcal{L} = \sum_i w_i^{(t)} \cdot \exp(-\alpha_t y_i h_t(x_i))
$$

Now: for fixed $\alpha_t > 0$, the loss is minimized when $h_t$ is the classifier that minimizes the weighted error $\sum_i w_i^{(t)} I[h_t(x_i) \neq y_i]$. That's exactly step 1 of AdaBoost — train the weak learner with the current weights.

Given $h_t$, find the optimal $\alpha_t$. Split the sum into correctly and incorrectly classified examples:

$$
\mathcal{L} = e^{-\alpha_t} \sum_{i: y_i = h_t(x_i)} w_i^{(t)} + e^{+\alpha_t} \sum_{i: y_i \neq h_t(x_i)} w_i^{(t)}
$$

Let $\varepsilon_t = \sum_{i: \text{wrong}} w_i^{(t)} / \sum_i w_i^{(t)}$ be the weighted error rate. Assuming weights sum to 1 (after normalization):

$$
\mathcal{L} = (1 - \varepsilon_t) e^{-\alpha_t} + \varepsilon_t e^{+\alpha_t}
$$

Differentiate w.r.t. $\alpha_t$ and set to zero:

$$
-(1 - \varepsilon_t) e^{-\alpha_t} + \varepsilon_t e^{+\alpha_t} = 0
$$

$$
e^{2\alpha_t} = \frac{1 - \varepsilon_t}{\varepsilon_t}
$$

$$
\alpha_t = \frac{1}{2} \log \frac{1 - \varepsilon_t}{\varepsilon_t}
$$

That's *exactly* the AdaBoost formula for $\alpha_t$. We derived it, not by accident.

The weight update follows the same way: after committing to $\alpha_t$ and $h_t$, the next iteration's weight $w_i^{(t+1)} = \exp(-y_i \hat{f}_t(x_i)) = \exp(-y_i \hat{f}_{t-1}(x_i)) \cdot \exp(-\alpha_t y_i h_t(x_i)) = w_i^{(t)} \cdot \exp(-\alpha_t y_i h_t(x_i))$. Exactly the update rule.

**The upshot:** AdaBoost is doing greedy stage-wise minimization of the exponential loss. Every formula is a consequence of that single principle. This view — algorithms as gradient descent in function space — is what generalizes AdaBoost to gradient boosting (Chapter 36) for arbitrary loss functions.

---

## 35.4 Bagging vs. boosting — the tradeoff

Now we can compare bagging and boosting cleanly.

| Aspect | Bagging (Chapter 34) | Boosting (Chapter 35) |
|---|---|---|
| Trees built | In parallel, independently | Sequentially, each on residuals/reweighted |
| Each tree sees | A bootstrap sample | The full training set, reweighted |
| Combination | Equal-weight vote/mean | Weighted vote, weights tied to accuracy |
| What it reduces | Variance | Variance AND bias |
| Overfitting risk | Low (more trees never hurts) | Real (more trees can overfit) |
| Sensitive to label noise | Moderate | High (exponentially upweights mistakes) |
| Parallelizable | Trivially (independent trees) | Not across iterations |
| Hyperparameter sensitivity | Low | Moderate-to-high |

Bagging is a *variance reduction* technique. Boosting can reduce variance AND bias — because each new learner is correcting the previous ensemble's errors, the bias of the ensemble *decreases* as more learners are added. But boosting can also overfit if you boost too long.

This bias-variance distinction is the heart of when each approach wins. If your individual model is already low-bias but high-variance (deep, unconstrained trees), bagging is the right tool. If you can use a very weak base learner (decision stump) and want to incrementally build up a complex predictor, boosting is the right tool.

In practice, gradient boosting with shallow trees (depth 3-8) hits the sweet spot — moderate variance per tree, sequential bias-reduction, careful early stopping. We'll dig into this in Chapter 36.

---

## 35.5 The margin theory of AdaBoost

A surprising fact about AdaBoost: even after the training error reaches zero, additional boosting rounds *continue to improve test error*. This puzzled researchers in the 1990s — surely once you classify the training set perfectly, more learning is overfitting?

Schapire et al. (1998) explained this with **margin theory**. Define the margin of training example $i$ at iteration $T$ as

$$
\text{margin}_T(i) = \frac{y_i \cdot \sum_t \alpha_t h_t(x_i)}{\sum_t |\alpha_t|}
$$

— the normalized signed prediction. Margins in $[-1, +1]$. Negative margin = misclassified; positive = correctly classified; closer to ±1 = more confident.

Even after training error is zero (all margins positive), additional boosting rounds continue to *push margins toward +1*. Larger margins lead to better generalization (the connection to SVMs is obvious; the math is similar). So AdaBoost keeps improving even when zero-one training error has saturated.

This is also why early stopping in AdaBoost is more subtle than in gradient boosting — it's hard to know when continuing to boost is "useful" vs. "overfitting" because the training error metric stops changing once it hits zero.

In gradient boosting on real loss functions (cross-entropy, MSE), early stopping on a validation set is the right tool because the validation loss DOES start increasing once you overfit.

---

## 35.6 A worked numerical example

A 4-row dataset for binary classification:

| $i$ | $x_{i,1}$ | $x_{i,2}$ | $y_i$ |
|----:|----------:|----------:|------:|
| 1 | 1 | 2 | +1 |
| 2 | 2 | 3 | +1 |
| 3 | 3 | 1 | -1 |
| 4 | 4 | 2 | -1 |

Initialize $w_i^{(1)} = 1/4$ for all $i$.

**Round 1.** Train a decision stump. Consider all candidate splits. The split "$x_1 \leq 2.5$" puts {1, 2} on the left (both +1) and {3, 4} on the right (both -1). This is a perfect classifier — error 0. So $h_1(x) = +1$ if $x_1 \leq 2.5$, else $-1$. $\varepsilon_1 = 0$, $\alpha_1 = \frac{1}{2}\log(1/0) = \infty$.

Hmm — perfect first classifier gives infinite alpha, which means we're done in one round. Let's use a less perfectly-separable dataset to actually see boosting in action.

**Revised dataset:**

| $i$ | $x_{i,1}$ | $y_i$ |
|----:|----------:|------:|
| 1 | 1 | +1 |
| 2 | 2 | +1 |
| 3 | 3 | -1 |
| 4 | 4 | +1 |
| 5 | 5 | -1 |

Now no stump can perfectly classify (example 4 with $x = 4, y = +1$ sits between two negatives). Run AdaBoost.

Initialize: $w = (0.2, 0.2, 0.2, 0.2, 0.2)$.

**Round 1.** Candidate stumps:
- "$x \leq 1.5$": predict +1 left, -1 right. Errors: rows 2 (pred -1, true +1), 4 (pred -1, true +1). $\varepsilon = 0.4$.
- "$x \leq 2.5$": +1 left, -1 right. Errors: row 4 (pred -1, true +1). $\varepsilon = 0.2$.
- "$x \leq 3.5$": +1 left, -1 right. Errors: row 3 (pred +1, true -1), row 4 (pred -1, true +1). $\varepsilon = 0.4$.
- "$x \leq 4.5$": +1 left, -1 right. Errors: row 3 (pred +1, true -1), row 5 OK. $\varepsilon = 0.2$. Wait — also need rows 1, 2, 4 to be predicted +1 (they are) and row 5 to be -1 (it is). Only row 3 is wrong. $\varepsilon = 0.2$.

Tie between "$\leq 2.5$" and "$\leq 4.5$" at $\varepsilon = 0.2$. Pick "$\leq 2.5$" (arbitrary).

$h_1(x) = +1$ if $x \leq 2.5$, else $-1$. $\alpha_1 = 0.5 \log(0.8/0.2) = 0.5 \log 4 = 0.693$.

Weight update: $w_i^{(2)} \propto w_i^{(1)} \exp(-\alpha_1 y_i h_1(x_i))$.

For correctly classified (rows 1, 2, 3, 5): factor $\exp(-0.693) = 0.5$. New unnormalized: $0.1$ each.

For row 4 (misclassified): factor $\exp(+0.693) = 2$. New unnormalized: $0.4$.

Sum: $4 \cdot 0.1 + 0.4 = 0.8$. Normalized: rows 1,2,3,5 get $0.1/0.8 = 0.125$; row 4 gets $0.4/0.8 = 0.5$.

So $w^{(2)} = (0.125, 0.125, 0.125, 0.5, 0.125)$. Row 4 now dominates with 50% of the weight.

**Round 2.** Re-evaluate stumps under the new weights.

- "$x \leq 3.5$": +1 left, -1 right. Errors: row 3 (pred +1, true -1), weight 0.125; row 4 (pred +1, true +1, *correct*). Re-check: $x_4 = 4 > 3.5$, predicted -1. Row 4's true label is +1. *Misclassified.* Weight 0.5. Total error: $0.125 + 0.5 = 0.625 > 0.5$. Bad — this stump in this direction is now WORSE than random because of the weight on row 4.

Try the reversed stump: "$x \leq 3.5$": -1 left, +1 right. Errors: rows 1, 2 (predicted -1, true +1), weights $0.125 + 0.125 = 0.25$; row 4 (predicted +1, true +1, correct); row 5 (predicted +1, true -1), weight 0.125. Total: $0.25 + 0.125 = 0.375$.

Let's also try "$x \leq 4.5$" (originally tied with our round-1 choice): +1 left, -1 right. Errors: row 3 (pred +1, true -1, weight 0.125). Total: 0.125. Much better!

So pick "$x \leq 4.5$" with $\varepsilon_2 = 0.125$. $\alpha_2 = 0.5 \log(0.875/0.125) = 0.5 \log 7 \approx 0.973$.

Weight update: rows correctly classified by $h_2$ have weight multiplied by $\exp(-0.973) \approx 0.378$. Misclassified (row 3) has weight multiplied by $\exp(+0.973) \approx 2.646$.

Rows 1, 2, 4, 5: new unnormalized: $0.125 \cdot 0.378 = 0.0472$ for rows 1, 2, 5; $0.5 \cdot 0.378 = 0.189$ for row 4.

Row 3: $0.125 \cdot 2.646 = 0.331$.

Sum: $3 \cdot 0.0472 + 0.189 + 0.331 = 0.142 + 0.189 + 0.331 = 0.662$.

Normalized: rows 1,2,5: $0.0472/0.662 = 0.0712$; row 4: $0.189/0.662 = 0.285$; row 3: $0.331/0.662 = 0.500$.

$w^{(3)} = (0.071, 0.071, 0.500, 0.285, 0.071)$.

Row 3 is now the heaviest. Row 4 is still significant. The boost is iterating on the hard examples.

**Round 3.** Skip the detailed arithmetic — we'd train another stump under these new weights, likely picking a split that classifies row 3 correctly.

**The ensemble after 2 rounds.** $H(x) = \text{sign}(0.693 \cdot h_1(x) + 0.973 \cdot h_2(x))$.

For $x = 1$: $h_1 = +1$ (since $1 \leq 2.5$), $h_2 = +1$ (since $1 \leq 4.5$). Sum: $0.693 + 0.973 = 1.666 > 0$. Predict +1. ✓
For $x = 4$: $h_1 = -1$ (since $4 > 2.5$), $h_2 = +1$ (since $4 \leq 4.5$). Sum: $-0.693 + 0.973 = 0.280 > 0$. Predict +1. ✓ (Note: $h_1$ alone got this wrong; the ensemble corrects.)
For $x = 5$: $h_1 = -1$, $h_2 = -1$. Sum: $-0.693 - 0.973 = -1.666 < 0$. Predict -1. ✓

After just 2 rounds, the ensemble classifies all 5 training examples correctly. The 2-round combination of two weak stumps achieves what no single stump could.

This is the magic of boosting in miniature.

---

## 35.7 Limitations of AdaBoost

### 35.7.1 Sensitivity to label noise

AdaBoost upweights misclassified examples *exponentially*. A mislabeled training example will be misclassified at every round (because no classifier can correctly predict the wrong label), and its weight will keep growing. Eventually it dominates the weights, and the algorithm wastes its energy trying to fit the noise.

This is the classic critique of AdaBoost. On noisy data, it overfits hard.

Modifications: **LogitBoost** (Friedman et al. 2000) replaces the exponential loss with the logistic loss, which grows much slower for misclassified examples — robust to noise. Gradient boosting (Chapter 36) generalizes this insight to arbitrary loss functions.

### 35.7.2 Sensitivity to outliers

Same problem, different framing. Outliers — points that don't fit the underlying pattern — get exponentially up-weighted just like mislabels. AdaBoost will try hard to fit them, distorting the ensemble.

### 35.7.3 Bound to binary classification (in its original form)

The classic AdaBoost is binary $\{-1, +1\}$. Multiclass extensions exist (AdaBoost.MH, SAMME) but they're awkward. By the time you need multiclass, you're usually reaching for gradient boosting anyway.

### 35.7.4 No native missing value handling

AdaBoost expects clean numerical inputs. Gradient boosting libraries (XGBoost, LightGBM) handle missing values natively, which is a huge engineering convenience.

---

## 35.8 Why AdaBoost still matters

AdaBoost is rarely used in production today. Gradient boosting beats it on essentially every metric — robustness, accuracy, library quality, support for arbitrary losses. So why teach AdaBoost?

**Pedagogy.** AdaBoost is the clearest introduction to the sequential ensemble idea. Every concept that powers XGBoost — weak learners, sequential refinement, weighted losses, the gradient-descent-in-function-space view — is present in AdaBoost in its simplest form.

**History.** AdaBoost was the algorithm that convinced the ML community that ensembling weak learners could outperform single strong learners. Before AdaBoost, this was theoretical; after, it was inevitable. Understanding the field's path matters.

**Theoretical foundation.** The PAC-learning theorem (Freund and Schapire, 1997) proves AdaBoost achieves arbitrarily low training error with enough rounds, under mild conditions. This was a major theoretical result, and the proof techniques are still used to analyze other ensemble methods.

**Connection to gradient boosting.** AdaBoost is a special case of gradient boosting with the exponential loss. Understanding AdaBoost makes the gradient-boosting generalization obvious — "swap the loss function, work out the gradients, away you go."

---

## 35.9 Code

scikit-learn has `AdaBoostClassifier` and `AdaBoostRegressor` (AdaBoost.R2). The default base estimator is a decision stump (1-level tree); you can use deeper trees if you want.

```python
from sklearn.ensemble import AdaBoostClassifier
from sklearn.tree import DecisionTreeClassifier

ada = AdaBoostClassifier(
    estimator=DecisionTreeClassifier(max_depth=1),  # stump
    n_estimators=200,
    learning_rate=1.0,           # shrinkage applied to alpha
    algorithm="SAMME",            # multiclass variant; SAMME.R is for probabilistic learners
    random_state=0,
)
ada.fit(X_train, y_train)

# Per-stage error monitoring
for i, score in enumerate(ada.staged_score(X_test, y_test)):
    if i % 10 == 0:
        print(f"Iter {i}: test accuracy {score:.4f}")
```

The `staged_score` method lets you see how performance evolves as more rounds are added — invaluable for diagnosing whether you're still benefiting from more rounds.

`learning_rate < 1.0` applies "shrinkage" — multiplying each $\alpha_t$ by the learning rate. Smaller learning rate + more rounds gives better generalization (the same wisdom as in gradient boosting).

scikit-learn does NOT have AdaBoost in `pyspark.ml`. Spark MLlib chose to invest in `GBTClassifier` (Chapter 36) instead — gradient boosting subsumes AdaBoost. If you specifically need boosted ensembles on Spark, use `GBTClassifier`.

---

## 35.10 What this builds on / where this returns

**Builds on:**
- Chapter 19 — bias-variance (boosting reduces both, but adds overfitting risk).
- Chapter 33 — decision trees as the canonical weak learner.
- Chapter 16-17 — loss functions and gradient descent (boosting is gradient descent in function space).

**Returns:**
- Chapter 36 — gradient boosting generalizes this to arbitrary differentiable loss functions, replacing the exponential loss with cross-entropy, MSE, etc. XGBoost, LightGBM, CatBoost.

---

## 35.11 Exercises

1. **Why $\pm 1$ encoding?** Why does AdaBoost use $y \in \{-1, +1\}$ instead of $\{0, 1\}$? (Hint: think about the exponent in the weight update and the loss function.)

2. **Compute α.** A weak learner achieves weighted error $\varepsilon = 0.3$. What is its voting weight $\alpha$? What if $\varepsilon = 0.45$? What if $\varepsilon = 0.05$?

3. **Sanity-check the weight update.** Show that if $\varepsilon_t < 0.5$ (the learner is better than random), the misclassified examples have their weights increased (factor > 1) and correctly classified examples have their weights decreased (factor < 1).

4. **One round by hand.** A 4-example training set with initial weights $(0.25, 0.25, 0.25, 0.25)$. A weak learner classifies examples 1 and 2 correctly, 3 and 4 incorrectly. Compute $\varepsilon$, $\alpha$, and the new weight vector.

5. **The exponential loss derivation.** Re-derive the AdaBoost update for $\alpha_t$ starting from the principle "minimize the exponential loss after adding the new term."

6. **Margin intuition.** A 3-round AdaBoost ensemble has $\alpha = (0.5, 0.7, 0.3)$ and an example $x$ where $h_1(x) = +1, h_2(x) = -1, h_3(x) = +1$. The true label is $y = +1$. Compute the margin. Is this example correctly classified?

7. **Why noise hurts AdaBoost.** Suppose 5% of your training labels are wrong (random flips). After many rounds of AdaBoost, what happens to the weights on the mislabeled examples? Why is this bad?

8. **AdaBoost vs. RF on noise.** Why is random forest *more* robust to label noise than AdaBoost? (Hint: think about how each algorithm responds to a single mislabeled example.)

9. **The "weak learner" requirement.** What's the minimum requirement for a base learner to be useful in AdaBoost? What happens if you pass a learner with $\varepsilon = 0.5$? With $\varepsilon = 0.6$?

10. **Shrinkage.** If you set `learning_rate=0.5` in sklearn's AdaBoost, what changes mathematically? Why might this help generalization?

11. **Boosting vs. bagging at margin saturation.** AdaBoost can keep improving test error after training error hits zero. Why? Random forest can't do this — adding more trees just plateaus. Why the difference?

12. **Stump vs. deep tree as weak learner.** If you use a depth-10 decision tree as the base learner in AdaBoost, what's likely to happen? Why is the standard advice to use stumps or shallow trees?

<details>
<summary>Answers</summary>

1. With $y \in \{-1, +1\}$ and $h \in \{-1, +1\}$, the product $y h$ is $+1$ if correct, $-1$ if wrong. The exponential loss $\exp(-y \hat{f})$ and the weight update $\exp(-\alpha y h)$ both flip sign cleanly. With $\{0, 1\}$ encoding the math is uglier. Same model, just notational convention — but the $\pm 1$ choice makes the algebra clean.

2. $\varepsilon = 0.3$: $\alpha = 0.5 \log(0.7/0.3) = 0.5 \log 2.33 \approx 0.424$. $\varepsilon = 0.45$: $\alpha = 0.5 \log(0.55/0.45) = 0.5 \log 1.22 \approx 0.100$. $\varepsilon = 0.05$: $\alpha = 0.5 \log(0.95/0.05) = 0.5 \log 19 \approx 1.472$.

3. The factor is $\exp(-\alpha y h)$. For correct ($yh = 1$): $\exp(-\alpha)$. Since $\varepsilon < 0.5$ implies $\alpha > 0$, $\exp(-\alpha) < 1$. For wrong ($yh = -1$): $\exp(+\alpha) > 1$.

4. $\varepsilon = 0.25 + 0.25 = 0.5$. Uh-oh — the algorithm terminates because $\varepsilon \geq 0.5$. This learner is no better than random under the current weights. (In practice if $\varepsilon = 0.5$ exactly, $\alpha = 0$, nothing happens; if greater than 0.5, you'd flip the learner's outputs and use $1 - \varepsilon$.)

5. See §35.3.2. Steps: write $\mathcal{L} = (1-\varepsilon)e^{-\alpha} + \varepsilon e^{+\alpha}$, differentiate, set to zero, solve.

6. Sum of weighted votes: $0.5 \cdot 1 - 0.7 \cdot 1 + 0.3 \cdot 1 = 0.5 - 0.7 + 0.3 = 0.1$. Sum of $|\alpha|$: $1.5$. Margin: $y \cdot 0.1 / 1.5 = 0.067$. Positive but small. Correctly classified (sign is +1) but with low confidence.

7. The mislabeled examples are misclassified every round (no learner predicts the wrong label correctly). Their weights grow exponentially. Eventually they dominate the weighted distribution, and the algorithm spends all its energy fitting noise. Test error increases.

8. RF averages many trees, each on a random subset of data. A mislabeled example only appears in ~63% of the bootstrap samples, and even when it's in the bag, it's one of $n$ examples with equal weight. Its influence is bounded. AdaBoost focuses *increasingly* on hard-to-classify examples, and mislabeled examples are hardest of all.

9. The learner must achieve $\varepsilon < 0.5$ under the current weights. If $\varepsilon = 0.5$, no progress. If $\varepsilon = 0.6$, the learner is worse than random — you'd negate its outputs to use it (effectively, flip it). AdaBoost terminates if no learner can do better than 0.5.

10. Multiplies each $\alpha_t$ by 0.5 — every learner's "vote" is half as strong. To achieve the same total fit, you need ~2x as many rounds. Slower convergence, but the resulting ensemble is "smoother" — less likely to overfit. Same intuition as small step sizes in gradient descent.

11. AdaBoost continues to push margins toward +1 even after zero-one error hits zero (Schapire's margin theory). RF's predictions are votes from independent trees; once each tree gets its prediction "right" on average, adding more identical-ish trees doesn't change much. RF saturates because it doesn't have a margin-pushing mechanism.

12. A depth-10 tree is already a strong classifier — often achieves $\varepsilon = 0$ on a small training set. Then $\alpha = \infty$ in a single round and AdaBoost terminates. Or, even if $\varepsilon$ is small but nonzero, the rounds quickly start fitting noise because deep trees overfit individually. Stumps are weak enough that no single round overfits and the sequential refinement has room to operate.

</details>
