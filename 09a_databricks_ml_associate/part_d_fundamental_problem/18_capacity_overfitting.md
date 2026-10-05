# Chapter 18 — Capacity, Overfitting, Underfitting

> **Goal of this chapter:** to name and dissect the central failure mode of supervised ML. Chapter 16 introduced *empirical risk minimization* and warned that the empirical risk on the training data is not the same as the true risk on the population. Chapter 17 gave us an algorithm — gradient descent — that drives empirical risk relentlessly downward. Put the two together and you have a story arc: the smarter the optimizer, the more aggressively it minimizes training loss, the more likely it is to *memorize* the training set rather than *learn* the underlying pattern. The model can ace the training data and fail catastrophically on the real world.
>
> That phenomenon is **overfitting**, and recognizing it — diagnosing it from symptoms, treating it with the right intervention — is *the* skill that separates a working ML practitioner from a person who can call `model.fit()`. We'll meet its mirror image, **underfitting**, too. We'll define the concept of model **capacity** that controls them both. We'll see the U-shaped curve of test error as capacity varies, internalize the diagnostic question "what is the gap between training and validation loss?", and set up the formal decomposition that Chapter 19 will give us.

---

## 18.1 A motivating story — the spam classifier that worked too well

Imagine you finish Chapter 3's spam classifier. You're proud. The training accuracy is 99.8%. You ship it. The next week, the support team is buried in customer complaints — legitimate emails are getting routed to junk and customers are missing important mail. Production accuracy is around 70%. You're confused. The model worked great in training; what happened?

What happened is overfitting. The model didn't *learn the difference between spam and ham* in the abstract sense. It learned the specific peculiarities of the 200,000 emails it saw during training — including all their idiosyncratic noise. On the next 200,000 emails (production), the noise is different, the model's confident predictions on those specific patterns no longer apply, and accuracy collapses.

This is not a contrived scenario. It is the most common failure mode of ML in practice. Every veteran ML engineer has been the protagonist in some version of this story. Reading the symptoms early — and knowing what to do about them — is what this chapter teaches.

---

## 18.2 Capacity, in plain language

The first vocabulary we need is **capacity**. Informally, *capacity is how complex a function the model can express*. High-capacity models can express many shapes; low-capacity models can express only a few. Capacity is a property of the model class $\mathcal{H}$, not of any particular trained model.

Three concrete examples to anchor it:

**Linear regression with one feature** — $\hat{y} = wx + b$. The hypothesis class is "all straight lines." Two free parameters, and they specify a line. This is low capacity: only straight-line shapes can be expressed. A curve in the data is, fundamentally, beyond this model's reach.

**Polynomial regression with degree $k$** — $\hat{y} = w_0 + w_1 x + w_2 x^2 + \ldots + w_k x^k$. $k+1$ free parameters. As $k$ grows, the class of functions grows: degree 1 = lines; degree 2 = parabolas; degree 9 = curves that can wiggle through any 10 specific points exactly. As $k$ increases, capacity increases.

**A decision tree of depth $d$.** Capacity grows roughly as $2^d$ (the number of leaves). A depth-2 tree can express piecewise-constant functions with at most 4 regions; a depth-20 tree can express functions with up to ~$10^6$ regions. Decision trees are notorious for being able to dial capacity from very low to very high by tweaking a single hyperparameter — `max_depth`.

**A neural network with $L$ layers and $w$ width per layer.** Very high capacity for modest $(L, w)$. A network with $L = 10$ and $w = 1000$ has on the order of $10^7$ parameters. The function class is "essentially anything," subject to fitting in memory.

Capacity is not a number you can usually compute exactly, but you can rank model classes by it:

```
       low capacity                                   high capacity
   ────────────────────────────────────────────────────────────────►
   constant   line   shallow tree   degree-10 poly   deep tree   deep NN
```

The choice of capacity is the most consequential modelling decision you'll make. Too little, and you can't fit anything useful. Too much, and you fit noise. The interesting territory is in the middle — and the search for that interesting territory is the bulk of practical ML.

### 18.2.1 Why "capacity" rather than "parameter count"

A common shortcut is to use the *number of parameters* as a proxy for capacity. This is roughly right for many model classes (a polynomial of degree $k$ has $k+1$ parameters; doubling the width of a neural network roughly doubles the parameters). But it can mislead:

- A linear model and a deep neural network with the same parameter count have vastly different capacity, because the neural network's non-linearities let parameters interact multiplicatively.
- Constraining a model class — e.g., requiring all weights to be non-negative — can drastically reduce effective capacity without changing the parameter count.
- A model with $L_2$ regularization has *some* nominal capacity but its *effective* capacity is dialed down by the penalty.

The cleanest formal notion is **VC dimension** for classifiers and **Rademacher complexity** for general loss settings — both quantify "how many arbitrary labelings can this model class fit?" — but they're rarely computable for practical models. For this curriculum, treat "capacity" as a working intuition: "how flexible is the function class?" That intuition will carry you everywhere it matters.

---

## 18.3 Underfitting and overfitting — the two failure modes

With capacity defined, we can name the two pathologies.

**Underfitting.** Capacity is too low. The model can't capture the pattern even on the training data. Training loss is much higher than it should be — and validation loss is also high, often roughly the same as training loss. Symptom: *bad everywhere*.

```
                       bad                bad
                     training           validation
                       loss               loss
                        ▼                  ▼
   true pattern   ╭───────────╮       ╭───────────╮
   in the data    │ data wiggles │     │ data wiggles │
                  │   like this  │     │   like this  │
   model fit  ────│──────────────│─────│──────────────│
   (a straight    a straight line     a straight line
    line)
```

**Overfitting.** Capacity is too high. The model can drive training loss very low — by fitting the noise as well as the signal. But on new data, the noise patterns don't repeat, so the model's confident predictions on the memorized patterns don't apply. Symptom: *training loss tiny, validation loss large*. The *gap* between them is the giveaway.

```
                           wiggly line passing through every point
                           ┌──────────────────────────────────────┐
                           │  *──*                                │
                           │     \\                               │
                           │      *──*                            │
   training data:         │           \\                          │
   the model nails it      │           *                          │
                           │            \\__*                     │
                           │                 \\___*               │
                           └──────────────────────────────────────┘
                           
                           same wiggly model on new data:
                           ┌──────────────────────────────────────┐
                           │  ?       ?                           │
                           │     \\                               │
                           │      \\                              │
   model predicts          │       \\         the true pattern    │
   wildly because the      │        \\____    looks nothing       │
   wiggles were fit to     │             \\___ like the wiggles   │
   noise, not signal       │                 \\__                 │
                           └──────────────────────────────────────┘
```

The mirror-image symptom check is *the* diagnostic tool of working ML:

| Symptom | Diagnosis |
|---|---|
| Both train and validation loss are high | Underfitting |
| Train loss is low, validation loss is high (big gap) | Overfitting |
| Train loss is low, validation loss is low (small gap) | Healthy fit |
| Train loss is very low, validation loss is moderate | Mild overfitting; might still be the best you can do |

This four-cell decision table is half of being a practical ML engineer.

### 18.3.1 What overfitting *looks* like in a tiny example

To anchor the picture, take a one-dimensional regression problem. The true relationship is $y = \sin(\pi x) + \varepsilon$ where $\varepsilon \sim \mathcal{N}(0, 0.2^2)$. We observe 8 training points uniformly from $x \in [0, 1]$.

Fit three polynomial regressions:

- **Degree 1** (linear). Two parameters. Can only fit a line.
- **Degree 3**. Four parameters. Can fit a gentle curve.
- **Degree 9** (number of parameters equals number of training points). Can pass through every training point exactly.

What you see, qualitatively:

```
   degree 1: a flat-ish line                        degree 3: smooth curve following sin
   ─────────────────                                 ─.─.─.─.─.─.─.─.─.
              .                                              .   ──         .
        ●                                              ●          .──        .
              .  ●                                          .  ●     ──    .
   ─────────────────                                                ──        ●
                  ●                                                   .─ ──   .
        misses curvature                                  fits the signal sensibly
       (underfit)                                              (good fit)
   
   degree 9: passes through every training point
   wiggling violently between training points (especially near the boundary)
                  ●
            ╱─╲   ╱─╲
   ───────●   ●─●   ● ──────●         predictions between observed
                            ╲              points are nonsense
                             ╲___●
                                  ╲╱      (overfit)
```

Quantify:

| Model | Training MSE | Test MSE |
|---|---:|---:|
| Degree 1 | 0.18 | 0.20 |
| Degree 3 | 0.04 | 0.05 |
| Degree 9 | $\sim 10^{-15}$ (essentially zero) | 0.85 |

Degree 1 underfits — both train and test are bad. Degree 3 is healthy — both are low and close. Degree 9 *catastrophically* overfits — training error is machine-epsilon-level zero (it interpolates the 8 points exactly), but test error is *worse than degree 1*.

This is the canonical demonstration. We'll re-do it in code in §18.7. Internalize the picture: the wiggly degree-9 curve nails the training points and then makes wild excursions between them — exactly the behavior of a model that memorized noise.

---

## 18.4 The U-shaped curve of test error

Plot test (or validation) error vs. capacity. What you see is a U.

```
  loss
    │
    │  *                                    *
    │   *                                   *
    │    *                                 *
    │     *                              *
    │      *      ←  test loss      ←   *
    │       *                          *
    │        *                       *
    │          *.                  *
    │             *...        ...*
    │                 *.....*               ← training loss
    │                                ....   (monotonically
    │                                    .. decreasing)
    │                                       
    └──────────────────────────────────────────► capacity
       low                  sweet                    high
       capacity            spot                    capacity
    (underfitting)                              (overfitting)
```

Read the picture carefully — it's the central diagram of classical ML:

- **Training loss** decreases monotonically as capacity increases. More flexibility → easier to fit the training data → lower training loss. At extreme capacity, training loss goes to zero (every point fit exactly).

- **Test (or validation) loss** has a **U-shape**:
  - At low capacity, the model is too inflexible to capture the signal — both training and test loss are high. *Underfit.*
  - As capacity rises, the model fits the signal better — test loss drops toward training loss.
  - At the **sweet spot**, test loss is as low as it gets. Training and test loss are close to each other.
  - Beyond the sweet spot, the model starts fitting noise in addition to signal. Training loss continues to drop; test loss starts to rise. *Overfit.*

The vertical *gap* between training and test loss is sometimes called the **generalization gap**. It's near zero at low capacity (the model is too dumb to memorize anything) and grows large at high capacity (the model memorizes everything).

The sweet spot is what we're hunting for. It exists for every problem; finding it is the practical art. Cross-validation (Ch 22) is the procedure by which we estimate where it is.

### 18.4.1 The double-descent surprise (an aside)

A famous recent observation in deep learning: if you keep increasing capacity past the point where the model can perfectly interpolate the training set, test loss sometimes drops *again* — the curve "double-descends." For deep nets with vastly more parameters than data points, increasing capacity can *help* even after interpolation. This is a beautiful and active research area but is *not* the rule for classical ML — for ridge regression, decision trees, random forests, and most of what's on the Databricks ML Associate exam, the classical U-shape is the right picture. We mention double descent for completeness; ignore it for the exam.

---

## 18.5 Diagnosing overfitting in practice

You have a model. You want to know: am I overfit? underfit? right?

The procedure is mechanical:

1. **Hold out a validation set.** (Ch 21 makes this formal.)
2. **Train on the training set.** Compute training loss.
3. **Predict on validation set without retraining.** Compute validation loss.
4. **Compare.**

Specifically, look at the *gap*:

$$
\text{gap} = L_{\text{val}} - L_{\text{train}}
$$

- Small gap, both low: healthy.
- Small gap, both high: underfit.
- Large gap, train low: overfit.

Two practical extensions:

**Per-metric, not just loss.** Often you compare metrics relevant to the business: accuracy, F1, AUC. The same logic applies: a 99% training F1 with a 75% validation F1 is overfit, period.

**Learning curves.** Train on increasing fractions of your training set — 10%, 25%, 50%, 100% — and at each, record both training and validation loss. Plot:

```
   loss
     │
     │ training       ___________________     ← high-capacity model: 
     │ loss         _/                            train low, val high
     │ (val)      _/
     │          _/         validation
     │         /
     │  ......./..............................
     │ /                          training
     │/        
     │
     └──────────────────────────────► training set size
```

Two diagnoses you can read from learning curves:

- *Curves converge to a high plateau* → underfitting. Adding more data won't help; the model class is too weak.
- *Curves converge to a low plateau, with a small gap* → healthy. Possibly add more data to nudge a bit lower.
- *Curves don't converge; large gap that closes slowly as data grows* → overfitting. More data would help; more regularization would too.

Learning curves are the single most informative diagnostic plot you can make on a training run. Many engineers skip them; the ones who don't, debug faster.

---

## 18.6 Treating overfitting

You've diagnosed overfitting. The options, in roughly increasing intrusiveness:

**1. Get more data.** Often the best fix and often the most expensive. More training data means more constraint on the model; the noise patterns that previously drove the model into bad regions get statistically washed out. With infinite training data and a bounded-capacity model class, you'd hit the irreducible-error floor (Ch 19) and stop. With realistic data quantities, you trade between expense and benefit.

**2. Reduce model capacity.** Switch to a less expressive model class. Use a shallower tree, a lower-degree polynomial, a logistic regression instead of a deep neural net. This trades some bias (you might no longer be able to capture the signal as well) against the variance reduction.

**3. Regularize.** Add a penalty term to the loss that discourages "complex" model parameters. L1, L2, and ElasticNet are the standards for linear models; we cover them in Ch 20. For trees, regularization takes the form of `max_depth`, `min_samples_split`, `min_samples_leaf` — constraints on how flexibly the tree can grow.

**4. Reduce features.** Fewer features → smaller effective capacity, even with the same nominal model class. Drop features that are correlated, irrelevant, or noisy. Feature selection (Ch 29) is its own discipline.

**5. Early stopping.** Stop training before the model fully converges. The intuition: training loss decreases monotonically but validation loss eventually starts increasing. Monitor validation loss during training, and stop at the dip. This is, in effect, an implicit regularizer — you're limiting the optimization's ability to drive training loss to zero.

**6. Dropout / data augmentation.** Deep-learning-specific tools. Out of scope here.

**7. Ensemble methods** (averaging multiple noisy models). Bagging (random forests) effectively reduces variance by averaging. Boosting reduces bias and variance together by adding weak learners sequentially. Parts F covers these formally.

You can — and often should — combine these. A well-regularized model on a good amount of data with appropriate capacity is the *default* recipe. Each lever has a hyperparameter, and tuning those hyperparameters is what HPO (Part I) is about.

### 18.6.1 Treating underfitting

The diagnoses for underfitting are easier:

**1. More capacity.** Switch to a more expressive model class. Add polynomial features. Use a deeper tree. Use a bigger neural net.

**2. More features.** Often the model is starving for relevant input. Engineering richer features almost always helps.

**3. Less regularization.** If you set $\lambda$ (the regularization coefficient) too high, the regularizer is dominating and pushing all weights toward zero. Lower it.

**4. Train longer.** If the optimizer hasn't converged, you might be reading premature loss values. Continue training and check.

**5. Fix bugs.** Some "underfitting" is actually a bug — data leakage in the wrong direction, mislabeled features, wrong loss function. If your model performs at "always-predict-the-majority-class" levels, the first hypothesis is "something is broken."

Note that "more data" *doesn't* fix underfitting. If the model class is too weak to express the pattern, no amount of data fixes that — the model will perfectly capture the limit of its expressiveness and stop there. This is one of the most useful diagnostic facts: if you double your training data and validation performance doesn't move, you're underfitting (or your data isn't carrying the signal).

---

## 18.7 A code demonstration

Let's reproduce the polynomial-regression overfitting story in code. We'll use scikit-learn, since we're not yet in PySpark territory.

```python
import numpy as np
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import make_pipeline

# Generate synthetic data: y = sin(pi x) + noise
rng = np.random.default_rng(42)

def true_f(x):
    return np.sin(np.pi * x)

n_train, n_test = 8, 200
x_train = rng.uniform(0, 1, size=n_train)
y_train = true_f(x_train) + rng.normal(0, 0.2, size=n_train)

x_test = np.linspace(0, 1, n_test)
y_test = true_f(x_test) + rng.normal(0, 0.2, size=n_test)

# Try a range of polynomial degrees
degrees = [1, 2, 3, 5, 7, 9]

print(f"{'Degree':>6}  {'Train MSE':>10}  {'Test MSE':>10}  {'Gap':>10}")
print("-" * 50)

for d in degrees:
    model = make_pipeline(
        PolynomialFeatures(degree=d, include_bias=False),
        LinearRegression()
    )
    model.fit(x_train.reshape(-1, 1), y_train)
    
    train_pred = model.predict(x_train.reshape(-1, 1))
    test_pred  = model.predict(x_test.reshape(-1, 1))
    
    train_mse = mean_squared_error(y_train, train_pred)
    test_mse  = mean_squared_error(y_test, test_pred)
    
    print(f"{d:>6}  {train_mse:>10.4f}  {test_mse:>10.4f}  {test_mse - train_mse:>10.4f}")
```

A typical run produces something like:

```
Degree   Train MSE   Test MSE        Gap
--------------------------------------------------
     1     0.1786      0.1900     0.0114
     2     0.1601      0.1751     0.0150
     3     0.0421      0.0497     0.0076
     5     0.0186      0.0517     0.0331
     7     0.0079      0.1188     0.1109
     9     0.0000      0.8492     0.8492
```

Read the table. Degree 1: both high (underfit). Degree 3: both low (sweet spot). Degree 9: training is essentially zero, test is huge — textbook overfit.

The gap is the diagnostic. It's tiny at low capacity (the model is too dumb to be wrong differently on train and test), tiny at the sweet spot (the model has learned signal that generalizes), and large at high capacity (the model memorized).

If you change `n_train` from 8 to 80 and rerun, you'll see the U-curve shift right — with more data, you can support higher capacity before overfitting kicks in. This is the data/capacity tradeoff in code.

---

## 18.8 Why the test set is sacred (preview)

We've casually been using "validation" and "test" interchangeably. Chapter 21 will pull them apart properly. The short version: the validation set is where you do iteration (try this model, try that one, tune this hyperparameter). The test set is touched once, at the very end, to produce the number you report.

The reason it matters here: every time you decide "model A beats model B" based on the validation set, you've subtly used validation information to make a choice. Repeat that 50 times across hyperparameters and architectures and you've, in effect, "trained on" the validation set. Your validation score becomes optimistic. The test set is the antidote — never looked at during iteration, looked at once at the end. The number you get on the test set is the honest one.

This becomes critical when you're tuning hyperparameters (Part I) — the temptation to "just check the test set quickly" is the most common discipline failure in ML, and it produces models that look great on paper and disappoint in production.

---

## 18.9 Connection to Chapter 19's bias-variance decomposition

We've talked all chapter about why overfitting happens. We haven't given a *formal* answer. The intuition — "the model fit noise instead of signal" — is right but vague.

Chapter 19 will make it precise. It'll show that for regression with squared loss, the expected test error decomposes exactly into three pieces:

$$
\mathbb{E}[(y - \hat{f}(x))^2] = \underbrace{\text{Bias}^2(\hat{f})}_{\text{from a too-simple model}} + \underbrace{\text{Variance}(\hat{f})}_{\text{from fitting noise}} + \underbrace{\sigma^2}_{\text{irreducible}}
$$

The three terms are the three knobs:

- **Bias²** is how systematically wrong the model is, averaged across training sets. Reducing bias = increasing capacity = fitting the signal more flexibly.

- **Variance** is how much the fitted model jiggles around when you re-draw the training set. Reducing variance = decreasing capacity, or regularizing, or averaging.

- **Irreducible noise** is the part of $y$ that's inherently unpredictable from $x$. No model can do better than this; it's the floor.

Increasing capacity decreases bias *and* increases variance. The total error is the sum. The U-shape we drew in §18.4 is exactly this sum: bias² dominates at low capacity, variance dominates at high capacity, total error is minimized in between.

Chapter 19 derives this from scratch. The U-curve will *fall out of the algebra*, not the other way around.

---

## 18.10 Engineering practices that limit overfitting

Beyond the formal levers (regularization, more data), several engineering practices reduce the risk of overfitting:

**Never look at the test set during iteration.** It's the most boring rule and the most violated. Set up your pipeline so the test set is loaded *once*, at the end. Some teams hash the test set IDs and refuse to evaluate on it more than three times across the entire project.

**Stratify your splits by relevant variables.** If your dataset has a temporal structure, split by time, not randomly (Ch 21). If your dataset has groups (multiple records per patient, customer, document), put all records for a group on the same side of the split. Random splitting in these settings leaks information and produces optimistic validation numbers.

**Use cross-validation when data is limited.** A single train/validation split is noisy when the validation set is small. k-fold CV (Ch 22) averages multiple splits for a more stable estimate.

**Track training and validation loss in tandem.** Every training run, log both. MLflow autologging (Part L) does this by default for the major frameworks. The first thing a senior ML engineer looks at on a new training run is the loss curve pair.

**Use simpler models as baselines.** Always train a low-capacity baseline (logistic regression, a depth-3 tree) alongside your fancier model. If the simple model gets 87% and the fancy model gets 88%, the fancy model is probably overfit and the additional complexity isn't earning its keep. If the fancy model gets 95%, the capacity is paying off. The baseline is your reality check.

**Beware the "great test score" surprise.** If your test score is dramatically better than your validation score, you have a leak or a bug. The test score is *not supposed to* be lower than validation in a healthy pipeline (they're both estimates of generalization error and should be similar). A big gap in either direction is a flag.

---

## 18.11 Summary

The core picture, distilled:

1. **Capacity** measures how complex a function the model can express. It's a property of the model class.
2. **Underfitting** = too little capacity. Training and validation loss both high. Model can't capture the signal.
3. **Overfitting** = too much capacity. Training loss low, validation loss high. Model has fit noise.
4. **The diagnostic** is the *gap* between training and validation loss. Small gap, low losses = healthy. Big gap = overfit. Both high = underfit.
5. **The U-curve.** Training loss decreases monotonically with capacity; validation loss is U-shaped. The sweet spot — bottom of the U — is what you're hunting for.
6. **Treatments for overfitting.** More data, less capacity, regularization, fewer features, early stopping, ensembling. Combine as needed.
7. **Treatments for underfitting.** More capacity, more features, less regularization, train longer, fix bugs.
8. **The next chapter** (19) gives the formal three-term decomposition (bias² + variance + irreducible) that the U-curve is a consequence of.

The diagnostic test — *look at the training-vs-validation gap* — is the most important practical skill in this chapter. Develop it as a reflex. Every training run, look at both numbers, decide the diagnosis, choose the intervention.

---

## 18.12 What this builds on / where this returns

**Builds on:**
- Chapter 1 (the function-approximation framing — ML approximates an unknown $f$).
- Chapter 3 (overfitting was previewed informally in the spam classifier).
- Chapter 16 (the empirical-vs-true-risk distinction; ERM and its "leap of faith").
- Chapter 17 (gradient descent drives training loss down — and that is exactly what enables overfitting).

**Returns:**
- *Chapter 19* derives the bias-variance decomposition that explains the U-shape mathematically.
- *Chapter 20* introduces regularization as the principal weapon against overfitting.
- *Chapter 21* formalizes train/validation/test splits.
- *Chapter 22* introduces cross-validation as a more reliable way to estimate validation error.
- Every algorithm chapter in Part F refers back to overfitting: which hyperparameters control capacity, what the typical sweet spot looks like.
- *Part H* (evaluation) returns to this when measuring overfitting per-metric, not just per-loss.
- *Part I* (HPO) is, in some sense, an automated search across this U-curve for the sweet spot.

---

## 18.13 Exercises

1. **Diagnosing from numbers.** For each of the following (train loss, validation loss) pairs, identify whether the model is underfit, overfit, or healthy.
   - (0.05, 0.06)
   - (0.30, 0.32)
   - (0.01, 0.50)
   - (0.10, 0.50)
   - (0.50, 0.51)

2. **Capacity ranking.** Rank the following from lowest to highest capacity: a depth-2 decision tree; ordinary least squares with 5 features; a polynomial regression of degree 8 on one feature; a random forest with 1,000 trees of depth 30 each.

3. **Why the U?** In one paragraph, explain in your own words why test loss is U-shaped in capacity but training loss is monotonically decreasing.

4. **The wedding photographer revisited.** Refer back to Chapter 3's spam example. The model's training accuracy was 97.1% and validation accuracy was 96.3%. Is this overfit? How do you know?

5. **Compute the gap.** From the table in §18.7, what's the generalization gap at degree 9? At degree 1? Which is overfit and which is underfit?

6. **Treatment selection.** A team's model has training MSE = 0.01 and validation MSE = 0.40. Name three interventions, in priority order, that you would suggest, with justification.

7. **Treatment selection — the other way.** A team's model has training MSE = 0.40 and validation MSE = 0.42. Name three interventions.

8. **Learning curves.** Sketch (or describe in words) what learning curves look like for a healthy model and for an overfit model.

9. **Why more data doesn't fix underfitting.** Explain in 2-3 sentences.

10. **Why "more capacity" isn't always the answer to high error.** If validation loss is high, why might increasing capacity make things *worse* rather than better? Use the U-curve to justify.

11. **Polynomial regression with $k = n - 1$.** If you fit a polynomial of degree $k$ to $n$ data points where $k = n - 1$, what is the training MSE? Why is this almost always a bad idea?

12. **A subtle leak.** A team's model has 99% test accuracy but only 75% production accuracy. There's been no concept drift. What is the most likely explanation? (Hint: think about the test set protocol.)

<details>
<summary>Answers</summary>

1. (a) Healthy — small gap, both low. (b) Healthy but possibly underfit if the achievable loss is much lower; small gap, both moderately high. (c) Overfit — train is much lower than val. (d) Overfit — moderate train, big val gap. (e) Possibly underfit if a better model could achieve much lower; both high, no gap.

2. From low to high: OLS with 5 features → depth-2 decision tree → degree-8 polynomial in 1D → random forest with 1000 deep trees.

3. Training loss measures how well the model fits the data it was given. With more capacity, the model can fit those specific points better, so training loss falls monotonically — and at high enough capacity, it falls to zero (memorization). Validation loss measures how well the model fits *unseen* data. At low capacity, both training and validation loss are high because the model can't capture the signal. As capacity rises into the right range, the model captures the genuine pattern and validation loss falls along with training loss. Beyond the sweet spot, the model starts fitting noise that doesn't generalize — training loss keeps falling but validation loss rises again. The total effect: a U-shape.

4. No, healthy. The gap (97.1% − 96.3% = 0.8 percentage points) is small relative to either number. The model is generalizing.

5. At degree 9: train MSE ≈ 0, test MSE ≈ 0.85, gap ≈ 0.85. Massively overfit. At degree 1: train MSE ≈ 0.18, test MSE ≈ 0.19, gap ≈ 0.01. Tiny gap but both losses are high — underfit (the linear class is too weak).

6. The model is overfit. Priority interventions: (a) add regularization (L2 with reasonable strength, or for trees, lower `max_depth`); (b) get more training data if feasible — almost always reduces variance; (c) reduce model capacity (smaller depth, fewer features). Honorable mentions: feature selection; early stopping; cross-validation to systematically tune the regularizer.

7. The model is underfit. (a) Increase model capacity — deeper trees, more polynomial features, more layers. (b) Engineer richer features — domain-aware interactions, transformations. (c) Lower regularization if it's currently aggressive; check the loss function and training procedure for bugs.

8. Healthy: training loss starts somewhat high (one data point isn't informative), drops as data is added, plateaus at some low level. Validation loss starts high (model trained on a tiny sample can't predict), drops as data is added, plateaus at roughly the same low level. The two curves *converge* with little gap. Overfit: training loss starts low (you can memorize a small set) and stays low. Validation loss starts very high, drops as data is added, but stays well above training loss even at full data size. The gap doesn't close.

9. More data constrains the model class — but only insofar as the class can express the underlying pattern. An underfit model is, by definition, unable to express the pattern at all (e.g., a straight line fitting a sinusoidal pattern). Adding more data lets the model fit its limited shape *more confidently*, but the limit is the model's expressiveness, not its data. To fix underfitting, you change the model class, not the data size.

10. The U-curve says total error is the *sum* of bias² and variance (plus irreducible noise). Adding capacity reduces bias but increases variance. If you're already past the sweet spot, adding more capacity will increase variance more than it decreases bias — total error goes up.

11. With $n$ training points and a polynomial of degree $k = n - 1$, the polynomial has $n$ coefficients and can be uniquely determined to pass through *all* $n$ points exactly. Training MSE is zero (modulo numerical error). This is bad because the polynomial is wiggling violently between training points to interpolate them exactly — extreme overfitting, terrible generalization. Classical demonstration of the danger of matching parameter count to sample count.

12. The team probably evaluated on the test set repeatedly during development — choosing models, hyperparameters, features based on test performance. Each such choice is a small leak of test-set information into the training process. After enough choices, test accuracy is essentially "training accuracy on the test set" — wildly optimistic compared to true production performance. The discipline is: test set is touched once, at the very end.

</details>
