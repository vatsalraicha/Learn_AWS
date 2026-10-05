# Chapter 19 — The Bias-Variance Decomposition

> **Goal of this chapter:** to derive, from scratch, with every step visible, one of the most beautiful equations in machine learning. The claim is this: for regression with squared loss, the expected test error at any input $x$ decomposes *exactly* into three terms — squared bias, variance, and irreducible noise. The decomposition is an identity; it falls out of algebra; once you see it, you cannot un-see why models overfit, why regularization helps, why more data reduces some kinds of error but not others, and why no model can ever achieve zero test error on noisy data.
>
> Chapter 18 told us that test loss is U-shaped in capacity. This chapter tells us *why*. The U-shape is the sum of two terms that move in opposite directions: bias² (down with capacity) and variance (up with capacity). The sweet spot is where their sum is minimized.
>
> We will set up notation carefully, derive the identity slowly, give the dartboard analogy that builds intuition, and then *demonstrate it numerically* on the polynomial-regression example from Chapter 18. By the end you should be able to (a) write the decomposition down from memory, (b) explain what each term measures and how to manipulate it, and (c) recognize bias-dominated and variance-dominated behavior in your own training runs.

---

## 19.1 What we're decomposing, and why

Recall the setup from Chapter 16. There's a true function $f^*: \mathcal{X} \to \mathbb{R}$ (regression). Observations are noisy:

$$
y = f^*(x) + \varepsilon
$$

where $\varepsilon$ is a zero-mean random variable with variance $\sigma^2$. The noise $\varepsilon$ is independent of $x$ — it's the part of the world that's inherently unpredictable, the *irreducible* part.

We're given a random training set $D = \{(x_1, y_1), \ldots, (x_n, y_n)\}$ drawn i.i.d. from the joint distribution of $(x, y)$. We use $D$ to fit a model $\hat{f}_D$ — the notation reminds us that the fitted model depends on which training set we got.

Now: fix a specific test point $x_0$. The true output is $y_0 = f^*(x_0) + \varepsilon_0$. The model's prediction is $\hat{f}_D(x_0)$. The squared error at this test point is

$$
(y_0 - \hat{f}_D(x_0))^2
$$

Two things are random in this expression:

1. The *training set* $D$ used to fit the model. Different $D$ → different $\hat{f}_D$ → different prediction at $x_0$.
2. The *test noise* $\varepsilon_0$. Even at a fixed $x_0$ with a fixed model, $y_0$ varies because of the random $\varepsilon_0$.

We want the **expected squared error** at $x_0$, averaging over both sources of randomness:

$$
\mathbb{E}_{D, \varepsilon_0}\!\left[(y_0 - \hat{f}_D(x_0))^2\right]
$$

This is the quantity we're going to decompose. The decomposition will tell us what *kinds* of error contribute to it.

A small notation note before we proceed: when the subscript on $\mathbb{E}$ is unambiguous from context, we'll drop it. When we write $\mathbb{E}_D$ we mean "average over training sets"; when we write $\mathbb{E}_\varepsilon$ we mean "average over the noise on $y_0$." All other quantities ($f^*$, $x_0$, $\sigma^2$) are non-random in this analysis.

---

## 19.2 The three quantities we're going to identify

Before the derivation, let me name what we expect to find, so you know what we're aiming for.

**Bias of the model at $x_0$:**

$$
\text{Bias}(\hat{f}, x_0) = \mathbb{E}_D[\hat{f}_D(x_0)] - f^*(x_0)
$$

Read: "averaged over all training sets, how far is the model's prediction at $x_0$ from the true value?" If you trained on infinitely many training sets and averaged their predictions, you'd get $\mathbb{E}_D[\hat{f}_D(x_0)]$ — call it the model's *expected prediction* at $x_0$. The bias is the gap between that expected prediction and the truth. Bias measures **systematic** error — error that doesn't go away by averaging.

**Variance of the model at $x_0$:**

$$
\text{Var}(\hat{f}, x_0) = \mathbb{E}_D\!\left[\left(\hat{f}_D(x_0) - \mathbb{E}_D[\hat{f}_D(x_0)]\right)^2\right]
$$

Read: "how much does the prediction at $x_0$ jiggle around its expected value as we re-draw training sets?" Variance measures **sensitivity to training data** — how much the same point's prediction would change if you had a different training set.

**Irreducible noise:**

$$
\sigma^2 = \mathbb{E}_\varepsilon[\varepsilon_0^2] = \text{Var}(\varepsilon_0)
$$

Read: "how much does the *truth* itself jiggle even at a fixed $x_0$?" This isn't a property of the model — it's a property of the data-generating process. Even a perfect oracle that knew $f^*$ exactly would have squared error $\sigma^2$ on $y_0$, because $y_0$ has random noise on top of $f^*(x_0)$.

The decomposition we're about to derive says:

$$
\boxed{\mathbb{E}[(y_0 - \hat{f}_D(x_0))^2] = \text{Bias}^2(\hat{f}, x_0) + \text{Var}(\hat{f}, x_0) + \sigma^2}
$$

Three terms. Two depend on the model. One doesn't. They don't interact — they just add. Let's prove it.

---

## 19.3 The derivation — every step visible

We will derive the identity for a *fixed* test point $x_0$. Once you have it pointwise, you get it averaged over all $x_0$ by taking an outer expectation.

To make the algebra readable, let me abbreviate. Drop the $x_0$ argument (everything is evaluated at $x_0$ throughout). Define:

- $f \equiv f^*(x_0)$ — the true target value (a constant, not random).
- $y \equiv y_0 = f + \varepsilon$, where $\varepsilon$ is random with $\mathbb{E}[\varepsilon] = 0$ and $\text{Var}(\varepsilon) = \sigma^2$.
- $\hat{f} \equiv \hat{f}_D(x_0)$ — the model's prediction (random because $D$ is random).
- $\bar{f} \equiv \mathbb{E}_D[\hat{f}_D(x_0)]$ — the expected prediction over training sets (a constant).

The quantity we want is:

$$
\mathbb{E}[(y - \hat{f})^2]
$$

where the expectation is over both $\varepsilon$ (noise on $y$) and $D$ (training set choice).

### Step 1: Substitute $y = f + \varepsilon$

$$
\mathbb{E}[(y - \hat{f})^2] = \mathbb{E}\!\left[(f + \varepsilon - \hat{f})^2\right]
$$

### Step 2: Add and subtract $\bar{f}$ inside the parentheses

This is the crucial algebraic move. We rearrange $(f + \varepsilon - \hat{f})$ as $(\varepsilon) + (f - \bar{f}) + (\bar{f} - \hat{f})$:

$$
f + \varepsilon - \hat{f} = \varepsilon + (f - \bar{f}) + (\bar{f} - \hat{f})
$$

Verify: $\varepsilon + (f - \bar{f}) + (\bar{f} - \hat{f}) = \varepsilon + f - \bar{f} + \bar{f} - \hat{f} = \varepsilon + f - \hat{f}$. ✓

So we have three groupings:

- $\varepsilon$: pure noise.
- $f - \bar{f}$: the bias (true value minus expected prediction). A constant.
- $\bar{f} - \hat{f}$: the deviation of the model's prediction from its own expected prediction. Random, zero-mean.

### Step 3: Expand the square of three terms

We use $(a + b + c)^2 = a^2 + b^2 + c^2 + 2ab + 2ac + 2bc$:

With $a = \varepsilon$, $b = (f - \bar{f})$, $c = (\bar{f} - \hat{f})$:

$$
(\varepsilon + (f-\bar{f}) + (\bar{f}-\hat{f}))^2 = \varepsilon^2 + (f-\bar{f})^2 + (\bar{f}-\hat{f})^2 + 2\varepsilon(f-\bar{f}) + 2\varepsilon(\bar{f}-\hat{f}) + 2(f-\bar{f})(\bar{f}-\hat{f})
$$

### Step 4: Take the expectation, using linearity

$$
\mathbb{E}[(y - \hat{f})^2] = \mathbb{E}[\varepsilon^2] + \mathbb{E}[(f-\bar{f})^2] + \mathbb{E}[(\bar{f}-\hat{f})^2] + 2\mathbb{E}[\varepsilon(f-\bar{f})] + 2\mathbb{E}[\varepsilon(\bar{f}-\hat{f})] + 2\mathbb{E}[(f-\bar{f})(\bar{f}-\hat{f})]
$$

Now we evaluate the six terms one by one.

### Step 5: First three terms — the keepers

**Term 1:** $\mathbb{E}[\varepsilon^2]$.

$\varepsilon$ has mean zero and variance $\sigma^2$, so $\mathbb{E}[\varepsilon^2] = \text{Var}(\varepsilon) + (\mathbb{E}[\varepsilon])^2 = \sigma^2 + 0 = \sigma^2$. 

So Term 1 $= \sigma^2$. This is the **irreducible noise**.

**Term 2:** $\mathbb{E}[(f-\bar{f})^2]$.

$f$ is a constant ($f^*(x_0)$) and $\bar{f}$ is a constant ($\mathbb{E}_D[\hat{f}_D(x_0)]$). So $(f - \bar{f})^2$ is itself a constant — no expectation needed:

$$
\mathbb{E}[(f-\bar{f})^2] = (f - \bar{f})^2 = (\text{Bias})^2
$$

This is **bias squared**.

**Term 3:** $\mathbb{E}[(\bar{f}-\hat{f})^2]$.

$\bar{f}$ is constant (with respect to $D$); $\hat{f}$ is random in $D$. By the definition of variance:

$$
\mathbb{E}[(\bar{f}-\hat{f})^2] = \mathbb{E}[(\hat{f} - \bar{f})^2] = \mathbb{E}[(\hat{f} - \mathbb{E}[\hat{f}])^2] = \text{Var}(\hat{f})
$$

This is **variance**.

So if the last three "cross terms" all vanish, we're done. Let's check them.

### Step 6: The cross terms vanish (carefully)

**Term 4:** $2\mathbb{E}[\varepsilon(f-\bar{f})]$.

$(f-\bar{f})$ is a constant. $\varepsilon$ is independent of everything else and has $\mathbb{E}[\varepsilon] = 0$:

$$
\mathbb{E}[\varepsilon(f-\bar{f})] = (f - \bar{f}) \cdot \mathbb{E}[\varepsilon] = (f-\bar{f}) \cdot 0 = 0
$$

So Term 4 = 0. ✓

**Term 5:** $2\mathbb{E}[\varepsilon(\bar{f}-\hat{f})]$.

Here $\varepsilon$ is the test noise and $\hat{f}$ depends on the training set $D$. *Crucially*, the test noise $\varepsilon$ on $y_0$ is independent of the training set $D$ — they're separate draws. So $\varepsilon$ and $(\bar{f} - \hat{f})$ are independent random variables, and the expectation of a product of independent random variables is the product of expectations:

$$
\mathbb{E}[\varepsilon(\bar{f}-\hat{f})] = \mathbb{E}[\varepsilon] \cdot \mathbb{E}[\bar{f}-\hat{f}] = 0 \cdot \mathbb{E}[\bar{f}-\hat{f}] = 0
$$

So Term 5 = 0. ✓

(Without independence — which would be the case if test noise leaked into training, e.g., via data leakage — this cross-term would *not* vanish and the decomposition wouldn't hold. The whole derivation depends on the train/test independence assumption that Chapter 21 will rigorously enforce.)

**Term 6:** $2\mathbb{E}[(f-\bar{f})(\bar{f}-\hat{f})]$.

$(f - \bar{f})$ is a constant. Pull it out:

$$
\mathbb{E}[(f-\bar{f})(\bar{f}-\hat{f})] = (f-\bar{f}) \cdot \mathbb{E}[\bar{f}-\hat{f}]
$$

Now $\mathbb{E}[\bar{f} - \hat{f}] = \bar{f} - \mathbb{E}[\hat{f}] = \bar{f} - \bar{f} = 0$ (by definition of $\bar{f}$).

So Term 6 = 0. ✓

### Step 7: Assemble

Terms 4-6 vanish. We're left with:

$$
\mathbb{E}[(y_0 - \hat{f}_D(x_0))^2] = \underbrace{\sigma^2}_{\text{irreducible}} + \underbrace{(\text{Bias})^2}_{\text{bias squared}} + \underbrace{\text{Var}(\hat{f})}_{\text{variance}}
$$

That's the identity. It's exact — not an approximation, not an inequality, an algebraic identity that holds for any model $\hat{f}$, any test point $x_0$, any data-generating function $f^*$, as long as the assumptions hold (squared loss, additive noise, train/test independence).

Read it aloud one more time: *the expected squared error at a test point is the sum of three sources — squared bias from a too-simple model, variance from over-sensitivity to training data, and irreducible noise inherent in the world.*

---

## 19.4 The dartboard analogy

For intuition, picture a dartboard. You're throwing $K$ darts (each dart is a model fit on a different training set $D$). The bullseye is the true value $f^*(x_0)$.

**Low bias, low variance.** The darts cluster tightly around the bullseye. Each individual dart is close to the truth, and the darts agree with each other. This is the goal.

```
                       •
                     • • •
                       •
                   ◯  ← bullseye
```

**Low bias, high variance.** The darts are scattered widely *around* the bullseye. On average, they're on the bullseye — but any individual dart is far away. Lots of model jitter; no systematic offset.

```
              •
                  •
       •     ◯       •
                    •
                  •
              •
```

**High bias, low variance.** The darts cluster tightly *off* to one side. They all agree with each other — but they all agree about the wrong answer. The model is systematically biased.

```
              ◯ ← bullseye
              
              
              
                    • • •
                      • •
                       •
```

**High bias, high variance.** Both: scattered, *and* the cluster is off-center. The worst of both worlds.

```
              ◯ ← bullseye
              
              
                       •
                  •  •
              •            •
                    •
                       •
```

The pictures explain the names:

- *Bias* measures **systematic** displacement from the truth — the center of the dart cloud minus the bullseye.
- *Variance* measures **scatter** within the dart cloud — how much the predictions disagree with each other across training sets.
- The total squared error at the test point is, by the decomposition, "distance from center to bullseye, squared" + "average squared distance from individual dart to center" + "noise floor."

The Pythagoras-of-error-sources picture is exact.

---

## 19.5 How capacity affects each term

Now we connect the decomposition to Chapter 18's U-curve.

**Low-capacity models.** The hypothesis class $\mathcal{H}$ is small — say, only straight lines. The expected prediction $\bar{f} = \mathbb{E}_D[\hat{f}_D(x_0)]$ is roughly the best linear approximation to $f^*$ at $x_0$. If $f^*$ is genuinely non-linear, this is far from $f^*(x_0)$ — *high bias*. But because the class is so constrained, two different training sets give very similar fits — *low variance*.

**High-capacity models.** The hypothesis class is huge — say, polynomials up to degree 100 on a dataset of size 20. The expected prediction $\bar{f}$ is close to $f^*$ (high enough capacity to express any reasonable target) — *low bias*. But individual fits depend wildly on the training data: each different $D$ produces a wildly-different polynomial — *high variance*.

So as capacity increases:

- Bias² decreases (model can express more shapes; closer to truth on average).
- Variance increases (model's specific fit jiggles more with the training data).

The total error is bias² + variance + irreducible. The irreducible term is constant. The other two move in opposite directions. Their sum is U-shaped:

```
   error
    │
    │\                          ___
    │ \\        variance      ___/
    │  \\                  ___/
    │   \\               _/        
    │    \\           __/          ←  total
    │     \\        _/                error 
    │      \\     _/                 (U-shape)
    │       \\__/                  
    │       /  \              
    │     _/    \\___                ← bias²
    │   _/         \\___              (decreasing)
    │ _/              \\____
    │__________________________ ← irreducible σ²
    │
    └────────────────────────────► capacity
                  ↑
              sweet spot
       (gradient of bias² = -gradient of variance)
```

The sweet spot is exactly where increasing capacity costs more variance than it saves bias. At that point, the marginal gradients of bias² and variance balance — adding capacity past it makes total error rise.

This is the U-curve, derived from algebra rather than asserted.

---

## 19.6 What each term tells you to do

The decomposition is more than poetry; it's a *prescription*.

**High bias → fix:**
- Use a more flexible model class (more capacity).
- Add more features.
- Engineer non-linear features (polynomial, interaction terms).
- Reduce regularization if it's currently aggressive.

**High variance → fix:**
- Use a less flexible model class (less capacity).
- Add regularization (L1, L2, ElasticNet — Ch 20).
- Get more training data.
- Use ensemble methods that average noisy models (bagging — Ch 34).

**Irreducible noise → can't fix.** This is the noise floor. The best you can do is recognize when you're near it and stop trying to push down further. Sometimes you can reduce irreducible noise by collecting *better* features that capture more of $y$'s variation — but that's relabeling the term, not eliminating it.

How do you *diagnose* whether your error is bias-heavy or variance-heavy? Two practical heuristics:

1. **Training loss high, validation loss similar** → bias-dominated (Chapter 18's underfitting). The model can't capture the signal.

2. **Training loss low, validation loss much higher** → variance-dominated (Chapter 18's overfitting). The model fits training-specific noise.

This is the diagnostic from Chapter 18, re-explained: the *gap* between training and validation loss is essentially a measurement of variance.

Why? Training loss measures how the model fits the data it saw — basically, "how close is $\hat{f}_D$ to *those specific* $y_i$'s?" Variance affects this less because $\hat{f}_D$ was fit *to* those $y_i$'s. Validation loss measures how the model fits *new* data — and the variance term hits this hard, because variance is exactly "how much does $\hat{f}_D$ jiggle away from the average prediction?" New data on the same $f^*$ will be at the average prediction; a high-variance fit will be off from there.

---

## 19.7 Effect of more data

A useful consequence: *more data reduces variance but not bias.*

Why variance shrinks: as $n \to \infty$, the training set becomes more representative of the true distribution. Two large training sets are similar to each other, so two fitted models are similar, so $\text{Var}(\hat{f}) \to 0$. (For consistent estimators in nice classes — and most things we care about — the rate is something like $\text{Var} \sim 1/n$.)

Why bias does *not* shrink with $n$: bias is determined by the *expressiveness* of $\mathcal{H}$. If you fit linear functions to a sinusoidal pattern, the best linear approximation is the same regardless of whether you have 100 training points or 100 million. More data refines your estimate of *the best linear approximation*, but the best linear approximation is itself non-zero distance from $f^*$ — and that distance is the bias.

The picture: as $n$ grows, the variance term in the decomposition shrinks toward zero, while the bias term stays roughly fixed. Total error converges to $\text{Bias}^2 + \sigma^2$ — the **asymptotic error floor** for that model class.

This explains a phenomenon every working ML engineer eventually meets: "I doubled my training data and my model didn't improve." If your error is bias-dominated, doubling data doesn't help. The fix is more capacity, not more data.

It also explains the converse: high-capacity models *need* lots of data. A deep neural net's variance is enormous on a small training set (the U-curve says: at high capacity with small $n$, you're way to the right on the curve, in the overfit zone). Add more data and the variance term shrinks; the U-curve "shifts right" — the sweet-spot capacity moves higher. This is why deep learning's empirical successes scale with data: the high-capacity models are useless on small data but become best-in-class on big data.

---

## 19.8 A worked numerical example: polynomial regression on $\sin$

Let's actually compute bias², variance, and total error for the running example. We'll fit polynomials of degrees 1, 3, 5, 9 to noisy $\sin$ data, repeatedly with different training sets, and measure each term.

### 19.8.1 The setup

True function: $f^*(x) = \sin(\pi x)$ on $x \in [0, 1]$.

Noise: $\varepsilon \sim \mathcal{N}(0, 0.2^2)$, so $\sigma^2 = 0.04$.

We'll evaluate the decomposition at $K = 20$ uniformly-spaced test points and average. For each model class (degrees 1, 3, 5, 9), we'll:

1. Draw $T = 200$ independent training sets, each of size $n = 8$.
2. Fit a polynomial of the given degree to each training set.
3. For each test point $x_0$:
   - Collect the $T$ predictions $\hat{f}_1(x_0), \ldots, \hat{f}_T(x_0)$.
   - Compute the empirical $\bar{f}(x_0) = \frac{1}{T}\sum_t \hat{f}_t(x_0)$.
   - Compute Bias² $= (\bar{f}(x_0) - f^*(x_0))^2$.
   - Compute Variance $= \frac{1}{T}\sum_t (\hat{f}_t(x_0) - \bar{f}(x_0))^2$.
4. Average bias² and variance over the test points.
5. Total expected error = bias² + variance + $\sigma^2$.

### 19.8.2 The code

```python
import numpy as np
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline

rng = np.random.default_rng(0)

def true_f(x):
    return np.sin(np.pi * x)

sigma = 0.2
n_train = 8
T = 200  # training sets
K = 20   # test points
x_test = np.linspace(0.05, 0.95, K)
y_test_true = true_f(x_test)

for degree in [1, 3, 5, 9]:
    predictions = np.zeros((T, K))     # one row per training set, one col per test point
    for t in range(T):
        x_tr = rng.uniform(0, 1, size=n_train)
        y_tr = true_f(x_tr) + rng.normal(0, sigma, size=n_train)
        model = make_pipeline(
            PolynomialFeatures(degree=degree, include_bias=False),
            LinearRegression()
        )
        model.fit(x_tr.reshape(-1, 1), y_tr)
        predictions[t] = model.predict(x_test.reshape(-1, 1))
    
    mean_pred = predictions.mean(axis=0)              # E_D[ f_hat(x0) ]  per test point
    bias_sq_per_x = (mean_pred - y_test_true) ** 2    # bias^2 per test point
    var_per_x = predictions.var(axis=0)               # variance per test point
    
    bias_sq = bias_sq_per_x.mean()
    var     = var_per_x.mean()
    total   = bias_sq + var + sigma**2
    
    print(f"Degree {degree}: bias² = {bias_sq:.4f}, var = {var:.4f}, "
          f"σ² = {sigma**2:.4f}, total = {total:.4f}")
```

### 19.8.3 What the table looks like (typical run)

```
Degree 1: bias² = 0.182,  var = 0.013,  σ² = 0.040,  total = 0.235
Degree 3: bias² = 0.014,  var = 0.034,  σ² = 0.040,  total = 0.088
Degree 5: bias² = 0.006,  var = 0.121,  σ² = 0.040,  total = 0.167
Degree 9: bias² = 0.011,  var = 8.420,  σ² = 0.040,  total = 8.471
```

(Exact numbers vary with the random seed; the qualitative pattern is robust.)

Read this carefully. It's the decomposition speaking.

**Degree 1.** Bias² is large (0.182): a straight line cannot capture the sinusoid; its expected fit is systematically off. Variance is tiny (0.013): different training sets produce similar lines. Total error is dominated by bias.

**Degree 3.** Bias² has dropped massively (0.014): a cubic can approximate $\sin$ quite well on $[0, 1]$. Variance has risen a little (0.034). Total error (0.088) is the minimum across these four — the sweet spot.

**Degree 5.** Bias² is even lower (0.006). But variance has jumped to 0.121. The bias improvement is buried by the variance increase. Total error rises.

**Degree 9.** Bias² is about where it was at degree 5 (0.011) — the polynomial is expressive enough; you can't get much further. But variance is *catastrophic* (8.420). Different training sets produce wildly different degree-9 polynomials, each wiggling violently between their training points. Total error explodes.

You're watching, in numbers, the U-curve unfold from the decomposition.

```
   error
       8 │                                       *  ← degree 9 (variance explosion)
       6 │
       4 │
       2 │
     0.2 │  *   ← degree 1 (bias-dominated)
   0.15 │              *  ← degree 5 (rising variance)
    0.1 │
   0.05 │       *   ← degree 3 (sweet spot)
       0 │_____________________________________________
         deg 1  deg 3   deg 5    deg 7     deg 9
```

### 19.8.4 The bias-variance picture as you vary $n$

Re-run the experiment with $n_{\text{train}} = 8$, $n_{\text{train}} = 80$, $n_{\text{train}} = 800$. What you see (qualitatively):

- For *degree 9*: variance shrinks dramatically with $n$. At $n=800$, variance is small, bias² is tiny, total error is near $\sigma^2$. *More data rescued the high-capacity model*.
- For *degree 1*: bias² stays roughly the same regardless of $n$. Variance shrinks but it was already small. *More data didn't help the bias-dominated model.*

This is the asymptotic floor story from §19.7, in numbers. High-capacity models *need* data; bias-limited models cannot be saved by data.

---

## 19.9 Regularization, previewed

Chapter 20 will introduce regularization formally. The bias-variance lens explains why it works.

Regularization adds a penalty to the loss that discourages large weights. The effect is to *constrain* $\mathcal{H}$ — to push the model toward simpler functions even within a high-capacity class.

Through the decomposition lens: regularization *increases* bias (the constrained model is further from $f^*$ on average) but *decreases* variance (the constrained model jiggles less with training data). If you do this carefully — choosing the regularization strength via cross-validation — you can find a point where the variance reduction outweighs the bias increase, and total error goes down.

Regularization is a *deliberate bias-variance trade*: you spend some bias to buy variance reduction. The next chapter will make this trade explicit and show how to tune it.

---

## 19.10 Three subtleties worth naming

**Subtlety 1: bias-variance is for squared loss.** The clean three-term identity holds specifically for $L_2$ loss. For 0/1 classification loss, cross-entropy, and other losses, you can write down analogous decompositions but they're messier (Domingos 2000 gives a unified framework). The intuition — bias from inflexibility, variance from over-sensitivity, irreducible from the world — carries over even though the algebra is uglier.

**Subtlety 2: bias and variance are point-wise.** The derivation in §19.3 was for a fixed test point $x_0$. The total expected loss over the input distribution is the *integral* over all $x$ of the pointwise decomposition. A model might be biased at some $x$ values and variance-heavy at others. When practitioners say "this model has high bias," they usually mean "averaged over the test distribution."

**Subtlety 3: estimating the terms is itself hard.** In real ML you don't know $f^*$, so you can't directly measure bias. The numerical demonstration in §19.8 worked because we knew $f^* = \sin(\pi x)$. In practice, the diagnostic is via *symptoms* — the train/validation gap — not direct measurement. The decomposition is a *conceptual* tool that explains the symptoms, not a numerical tool you compute on a real dataset.

---

## 19.11 A short tour of how the decomposition shows up in algorithms

The decomposition isn't an abstract artifact — it lives in the design of every algorithm in Part F.

**Linear regression and ridge regression.** Linear regression is low-variance, possibly-high-bias. Ridge (Ch 20) adds an L2 penalty that lowers variance further at the cost of bias.

**Decision trees.** Deep trees are low-bias, high-variance — they can memorize anything but are wildly sensitive to the data. Shallow trees are high-bias, low-variance.

**Random forests (bagging).** Bagging averages many high-variance trees. The bias is roughly that of one tree (averaging biased predictors gives a biased average), but the variance drops by a factor of $\sim 1/T$ where $T$ is the number of trees (almost; correlation between trees prevents full $1/T$ reduction — Ch 34). Random forests are *variance-reduction machines*. They're a beautiful application of the decomposition.

**Boosting.** Boosting (Ch 35-36) sequentially fits weak learners to the residuals of the current ensemble. It's a *bias-reduction* algorithm: it iteratively lowers bias by fitting what the previous learners got wrong. Over-boosting can increase variance (and is one of the failure modes), which is why early stopping and shrinkage are essential to boosting in practice.

These three patterns — single high-bias model, averaged low-bias high-variance models, sequenced bias-reducers — exhaust the design space of supervised learning. Each is best understood through the lens of the bias-variance decomposition.

---

## 19.12 Summary

The chapter in one statement:

For squared loss and additive noise, the expected test error at any input decomposes exactly as

$$
\mathbb{E}[(y - \hat{f}(x))^2] = \underbrace{(\mathbb{E}[\hat{f}(x)] - f^*(x))^2}_{\text{Bias}^2} + \underbrace{\mathbb{E}[(\hat{f}(x) - \mathbb{E}[\hat{f}(x)])^2]}_{\text{Variance}} + \underbrace{\sigma^2}_{\text{Irreducible}}
$$

Bias is systematic underfitting; variance is over-sensitivity to training data; the noise floor is what the world itself adds. They sum, exactly, to total expected error.

Consequences you should be able to draw:

1. The U-curve of test loss vs. capacity is the sum of decreasing bias² and increasing variance.
2. More data shrinks variance but not bias.
3. Regularization spends bias to reduce variance.
4. Diagnose bias-dominated error by "both train and validation high"; diagnose variance-dominated by "train low, validation high."
5. Different algorithms attack the decomposition differently: bagging reduces variance; boosting reduces bias.

If you walk away with one image, make it the dartboard. If you walk away with one equation, make it the boxed identity above.

---

## 19.13 What this builds on / where this returns

**Builds on:**
- Chapter 5 (expectation and variance of random variables — the basic algebra used in §19.3 is at this level).
- Chapter 7 (independence — used in Step 6 of the derivation, when we said test noise is independent of training data).
- Chapter 16 (loss functions; squared loss specifically).
- Chapter 18 (the capacity / U-curve picture this chapter formalizes).

**Returns:**
- *Chapter 20* (regularization) deliberately trades bias for variance reduction.
- *Chapter 22* (cross-validation) is the procedure for choosing where on the U-curve to operate.
- *Chapter 31* (linear regression) — low-variance, possibly-biased.
- *Chapter 32* (logistic regression) — same story.
- *Chapters 33-34* (trees, random forests) — bagging reduces variance.
- *Chapters 35-36* (boosting) — gradient boosting reduces bias by iteratively fitting residuals.
- *Part H* — when we measure precision/recall/AUC, the same decomposition applies *qualitatively* to those metrics even though the clean three-term identity is loss-specific.

---

## 19.14 Exercises

1. **Write it from memory.** State the bias-variance decomposition without looking. Define each of the three terms in plain English.

2. **A constant predictor.** Suppose $\hat{f}(x) = c$ for all $x$, where $c$ is a fixed constant (not trained). At a test point $x_0$ with true $f^*(x_0) = 5$ and noise $\sigma^2 = 1$, compute the bias, the variance, and the total expected error for $c = 3$. Then for $c = 5$. Then for $c = 7$.

3. **A mean-of-data predictor.** Suppose $\hat{f}(x) = \bar{y}_D$ — the mean of the training labels — independent of $x$. Argue (without full algebra) why this predictor has *low* variance (relative to a complex model) and *high* bias (relative to a good fit). 

4. **The cross-term in Step 5.** Re-derive why $\mathbb{E}[\varepsilon (\bar{f} - \hat{f})] = 0$. State precisely which independence assumption you used.

5. **Where the dartboard analogy breaks down.** The analogy implicitly assumes a 2D plane; bias-variance lives in 1D (each $\hat{f}(x_0)$ is a scalar). Is the analogy still useful? Why?

6. **U-curve sketching.** Sketch a U-curve of total error vs. capacity. Decompose it into the bias² and variance components on the same axes. Mark the sweet spot.

7. **A high-capacity floor.** What's the asymptotic test error (as $n \to \infty$) for a model class that contains $f^*$? Hint: think about each term separately.

8. **Bias under varying $n$.** Re-explain in 1-2 sentences why adding more data doesn't reduce bias.

9. **Decomposing a worked example.** From the §19.8 table at degree 3: bias² = 0.014, var = 0.034, $\sigma^2 = 0.040$. (a) What's the total expected error? (b) What fraction of the error is irreducible? (c) Suppose you could reduce variance to zero (say, by infinite training data) — what would the total error become? (d) What does that tell you about how much room is left for improvement?

10. **Bagging and the decomposition.** Suppose you have a high-variance model class — each individually-fit model has Var = $V$. You bag $T$ uncorrelated models. What is the bias of the average? What is the variance? Why is this useful?

11. **A regularization trade.** A model has bias² = 0.05 and variance = 0.20. You apply regularization that doubles the bias and halves the variance. Was that a good trade?

12. **A diagnostic.** Your model has training loss 0.05 and validation loss 0.45. Estimate (qualitatively) the breakdown: bias² big or small? Variance big or small? Irreducible noise — can you tell?

<details>
<summary>Answers</summary>

1. $\mathbb{E}[(y - \hat{f}(x))^2] = \text{Bias}^2 + \text{Var} + \sigma^2$. **Bias²**: how far the average prediction (over training sets) is from the true value — systematic error from a too-simple model. **Variance**: how much predictions jiggle across different training sets — sensitivity to the specific training data. **Irreducible noise**: variance of the test noise itself; the floor that no model can beat.

2. For all three: $\hat{f}$ is non-random (no training set), so Variance $= 0$. Irreducible $\sigma^2 = 1$ in all cases. Bias = $c - f^* = c - 5$. So:
   - $c = 3$: Bias $= -2$, Bias² = 4, total = $4 + 0 + 1 = 5$.
   - $c = 5$: Bias $= 0$, Bias² = 0, total = $0 + 0 + 1 = 1$.
   - $c = 7$: Bias $= 2$, Bias² = 4, total = 5.

3. *Low variance*: $\bar{y}_D$ is the mean of $n$ noisy labels. By the law of large numbers (Ch 9), $\bar{y}_D$ converges to the true population mean of $y$, so different training sets give similar $\bar{y}_D$ values — variance is small (scales as $\sim \sigma^2 / n$). *High bias*: the predictor ignores $x$ entirely — it predicts the same value everywhere. Whenever the true $f^*$ varies in $x$, this is wrong at most points, with the wrongness equal to $\mathbb{E}[y] - f^*(x_0)$ at point $x_0$. So bias varies pointwise and averages to a non-trivial value.

4. We showed: $\mathbb{E}[\varepsilon(\bar{f} - \hat{f})] = \mathbb{E}[\varepsilon] \cdot \mathbb{E}[\bar{f} - \hat{f}] = 0 \cdot 0 = 0$. We used the independence of the *test noise* $\varepsilon$ (which sits on the test label $y_0$) from the *training set* $D$ (which determines $\hat{f}$). They're independent because $y_0$ is a separate draw from $D$. Independence lets us factor the expectation of the product.

5. Still useful. The dartboard is a 2D *cartoon* of a 1D scenario — but it correctly conveys: bias = displacement of dart cloud center, variance = spread of dart cloud. The picture aids intuition even though predictions live on a line.

6. Sketch: bias² is a monotonically *decreasing* curve from upper-left. Variance is a monotonically *increasing* curve from lower-left. Their sum is U-shaped with minimum where the slopes balance ($d(\text{Bias}^2)/d(\text{cap}) = -d(\text{Var})/d(\text{cap})$). Add the constant horizontal line $\sigma^2$ for irreducible; the total U is shifted up by $\sigma^2$.

7. Bias² → 0 (the class contains $f^*$). Variance → 0 (with infinite data, $\hat{f}_D = f^*$ deterministically). Irreducible $\sigma^2$ remains. So the asymptotic floor is $\sigma^2$ — the noise floor.

8. Bias is determined by how well the *expected* model in the model class approximates $f^*$ — it's a property of the model class, not the sample size. More data lets you estimate the best-in-class function more reliably, but the best-in-class function is unchanged.

9. (a) Total = $0.014 + 0.034 + 0.040 = 0.088$. (b) $0.040 / 0.088 = 45\%$ of the error is irreducible. (c) With variance → 0, total $\to 0.014 + 0 + 0.040 = 0.054$. (d) The room left is the variance term (0.034) plus the small bias² gap (0.014 above the noise floor of 0.040). Reducing variance via more data or regularization could bring you close to 0.054; you can't get below 0.040 with this noise level.

10. Bias of the average = bias of one model (averaging biased estimators of the same target gives the same bias). Variance of the average of $T$ uncorrelated models with variance $V$ each = $V/T$. The bias is unchanged, but variance is cut by a factor of $T$. This is why bagging (random forests, Ch 34) reduces variance dramatically when the base learners are diverse enough to be approximately uncorrelated.

11. New bias² = $0.10$, new variance = $0.10$. Old total = $0.05 + 0.20 + \sigma^2 = 0.25 + \sigma^2$. New total = $0.10 + 0.10 + \sigma^2 = 0.20 + \sigma^2$. Total dropped by 0.05 — yes, good trade.

12. Training low and validation high → large generalization gap → variance is the dominant problem. Bias² is small (the model fits training fine). About the irreducible noise: from these two numbers alone you can't tell. To estimate it, you'd want to know what the *best possible* model in the relevant universe could achieve — or compare to a low-capacity baseline that bounds the bias and noise from above.

</details>
