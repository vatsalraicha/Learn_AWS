# Chapter 20 — Regularization: L1, L2, ElasticNet

> **Goal of this chapter:** to introduce the most-used weapon in the practitioner's arsenal against overfitting, *regularization*, and to derive it carefully enough that you can pick the right flavor for a given problem and understand what each is doing geometrically. Chapter 19 told us, formally, that high-capacity models have low bias but high variance. Reducing capacity is one fix; *regularizing* a high-capacity model is another. The trick of regularization is that you don't change the model class — you change the *loss* the optimizer sees, adding a penalty that discourages "complex" parameter vectors. The optimization still happens in the same parameter space, but the trough of the loss landscape is shifted toward simpler solutions.
>
> We will derive the two principal regularizers, **L2 (ridge)** and **L1 (lasso)**, and the convex combination **ElasticNet**. We'll see L2's beautiful closed-form solution for ridge regression. We'll see *why* L1 produces sparse solutions where L2 only shrinks weights toward zero — this is the famous "diamond vs. sphere" geometry that's worth absorbing in detail. We'll see how the regularization parameter $\lambda$ slides you along the bias-variance trade. And we'll write a small piece of code that demonstrates the difference in practice.

---

## 20.1 The problem in one sentence

Chapter 19 said: high-capacity models have high variance. They wiggle wildly to fit the noise in any specific training set. The fitted parameters can be enormous in magnitude — even when the underlying signal is gentle, an unconstrained high-capacity fit can produce a 9th-degree polynomial whose coefficients alternate $+10^4, -10^5, +10^6, \ldots$ to thread through the training points exactly.

Regularization's idea: *add a term to the loss that punishes the model for having large weights*. Now the optimizer faces a tension. On one hand it wants to fit the data (drive the squared/cross-entropy loss down). On the other hand it wants to keep weights small (drive the penalty down). The optimum balances both.

The general form:

$$
\boxed{L_{\text{reg}}(\mathbf{w}) = \underbrace{L(\mathbf{w})}_{\text{empirical loss}} + \lambda \cdot \underbrace{R(\mathbf{w})}_{\text{regularizer}}}
$$

where $\lambda > 0$ is the **regularization strength** (a hyperparameter we tune) and $R(\mathbf{w})$ is the **regularizer** — a function that quantifies how "complex" the parameter vector is.

Different choices of $R$ give different regularizers:

- $R(\mathbf{w}) = \|\mathbf{w}\|_2^2 = \sum w_j^2$ → **L2** (ridge).
- $R(\mathbf{w}) = \|\mathbf{w}\|_1 = \sum |w_j|$ → **L1** (lasso).
- $R(\mathbf{w}) = \alpha \|\mathbf{w}\|_1 + (1-\alpha)\|\mathbf{w}\|_2^2$ → **ElasticNet**.

By convention, we *do not* regularize the intercept $b$ — the intercept just sets the overall vertical level of the predictions and there's no good reason to push it toward zero. (scikit-learn, Spark ML, etc., all follow this convention by default; you can override but usually shouldn't.)

In practice, you also see $R$ with $\frac{1}{2}$ coefficients or other small algebraic conveniences. The convention varies by library — but the *shape* of the regularizer is what matters; the constants are just scaling.

---

## 20.2 L2 regularization (ridge regression)

The simplest regularizer is L2: penalize the sum of squared weights. For regression with squared loss, the L2-regularized objective is:

$$
L_{\text{ridge}}(\mathbf{w}, b) = \frac{1}{n}\sum_{i=1}^n (y_i - \mathbf{w} \cdot \mathbf{x}_i - b)^2 + \lambda \|\mathbf{w}\|_2^2
$$

This is called **ridge regression** in classical statistics. Let's understand what it does.

### 20.2.1 What L2 punishes

L2 punishes large weights *proportionally to their squared magnitude*. A weight of 10 contributes $100\lambda$ to the penalty; a weight of 100 contributes $10{,}000\lambda$ — a hundred times more. This means L2 is *especially* aggressive against extreme weights and *relatively* tolerant of small weights.

Geometrically: L2 pushes the optimizer toward parameter vectors that are *close to the origin* in the standard Euclidean sense. Among all solutions with similar empirical loss, L2 prefers the one with the smallest sum of squared coefficients.

The crucial property: **L2 shrinks weights toward zero, but never to exactly zero.** A weight that's contributing even a tiny bit to reducing the empirical loss will be kept at some small positive value. The optimizer trades off "marginal benefit to empirical loss" against "marginal cost from the penalty," and unless the marginal benefit is exactly zero (which happens only for completely useless features), the equilibrium is some non-zero weight.

### 20.2.2 The closed-form solution for ridge regression

One of L2's pleasant properties is that, for linear regression with squared loss, it has a *closed-form* solution. Let me derive it carefully.

Set up. Stack the $n$ training inputs into a matrix $X \in \mathbb{R}^{n \times d}$ — row $i$ is $\mathbf{x}_i^T$. Stack the targets into a vector $\mathbf{y} \in \mathbb{R}^n$. Assume for derivation purposes that we've absorbed the intercept by adding a column of ones to $X$ (so $b$ becomes a component of $\mathbf{w}$) — but with the understanding that the regularizer doesn't penalize that intercept entry. For clean notation in this derivation, let's drop the intercept entirely; you can add it back as an unregularized parameter at the end.

The regularized loss in matrix form:

$$
L_{\text{ridge}}(\mathbf{w}) = \frac{1}{n}(\mathbf{y} - X\mathbf{w})^T(\mathbf{y} - X\mathbf{w}) + \lambda \mathbf{w}^T \mathbf{w}
$$

Expand the first term:

$$
(\mathbf{y} - X\mathbf{w})^T(\mathbf{y} - X\mathbf{w}) = \mathbf{y}^T\mathbf{y} - 2\mathbf{w}^T X^T \mathbf{y} + \mathbf{w}^T X^T X \mathbf{w}
$$

So (dropping the $\frac{1}{n}$ which doesn't change the minimizer, and being explicit):

$$
n \cdot L_{\text{ridge}}(\mathbf{w}) = \mathbf{y}^T\mathbf{y} - 2\mathbf{w}^T X^T \mathbf{y} + \mathbf{w}^T X^T X \mathbf{w} + n\lambda \mathbf{w}^T\mathbf{w}
$$

Take the gradient with respect to $\mathbf{w}$ (Chapter 15: matrix calculus):

$$
\nabla_\mathbf{w} (n L_{\text{ridge}}) = -2 X^T \mathbf{y} + 2 X^T X \mathbf{w} + 2 n\lambda \mathbf{w}
$$

Set this to zero:

$$
X^T X \mathbf{w} + n\lambda \mathbf{w} = X^T \mathbf{y}
$$

$$
(X^T X + n\lambda I) \mathbf{w} = X^T \mathbf{y}
$$

So the ridge estimator is:

$$
\boxed{\hat{\mathbf{w}}_{\text{ridge}} = (X^T X + n\lambda I)^{-1} X^T \mathbf{y}}
$$

(With $n$ absorbed into $\lambda$ in some conventions, you'll see $(X^TX + \lambda I)^{-1} X^T \mathbf{y}$ — the variable naming differs across libraries; the structure is the same.)

Compare this to the OLS solution (Chapter 31 will derive it):

$$
\hat{\mathbf{w}}_{\text{OLS}} = (X^T X)^{-1} X^T \mathbf{y}
$$

The only difference is the $n\lambda I$ term added to $X^TX$. That tiny addition has two consequences worth noticing:

**Numerical:** When $X^TX$ is *singular* (e.g., because two features are perfectly correlated, or because $d > n$), the OLS solution doesn't exist — you can't invert the matrix. Adding $n\lambda I$ makes the matrix invertible. This is the "ridge" in the name — a positive ridge added along the diagonal stabilizes the inverse.

**Shrinkage:** For invertible $X^TX$, adding $n\lambda I$ pulls the estimator toward zero. As $\lambda \to 0$, $\hat{\mathbf{w}}_{\text{ridge}} \to \hat{\mathbf{w}}_{\text{OLS}}$. As $\lambda \to \infty$, $\hat{\mathbf{w}}_{\text{ridge}} \to \mathbf{0}$. So $\lambda$ slides you smoothly from "no regularization" to "all weights zero."

### 20.2.3 Worked numerical example

Tiny problem. Three training points, one feature:

| $x_i$ | $y_i$ |
|---:|---:|
| 1 | 2 |
| 2 | 5 |
| 3 | 7 |

(For simplicity ignore the intercept — just fit $\hat{y} = wx$. We'll have a single weight $w$.)

$X = [1, 2, 3]^T$. $\mathbf{y} = [2, 5, 7]^T$.

$X^TX = 1 + 4 + 9 = 14$.
$X^T\mathbf{y} = 1 \cdot 2 + 2 \cdot 5 + 3 \cdot 7 = 2 + 10 + 21 = 33$.

**OLS:** $w_{\text{OLS}} = 33 / 14 \approx 2.357$.

**Ridge with $\lambda = 1$:** $(X^TX + n\lambda) = 14 + 3 \cdot 1 = 17$. $w_{\text{ridge}} = 33/17 \approx 1.941$.

**Ridge with $\lambda = 10$:** $14 + 30 = 44$. $w_{\text{ridge}} = 33/44 \approx 0.750$.

**Ridge with $\lambda = 100$:** $14 + 300 = 314$. $w_{\text{ridge}} = 33/314 \approx 0.105$.

**Ridge with $\lambda \to \infty$:** denominator → ∞, $w \to 0$.

You can see the shrinkage in action: the OLS estimate of $w \approx 2.36$ gets pulled toward zero as $\lambda$ grows. The shrinkage is smooth — no abrupt jumps.

What's happening to the predictions? At the OLS estimate $w = 2.357$, residuals are $(2 - 2.357, 5 - 4.714, 7 - 7.071) = (-0.357, 0.286, -0.071)$, MSE $\approx 0.071$. At $\lambda = 10$ with $w \approx 0.75$, residuals are $(1.25, 3.5, 4.75)$ — predictions are now way too small. MSE on training $\approx 13.8$ — much worse. The model has been *over-regularized* — bias is now so high that empirical loss has exploded. The right $\lambda$ is somewhere in between, and we'd choose it via cross-validation (Ch 22).

### 20.2.4 L2 from the bias-variance perspective

The ridge estimator's bias-variance properties are well-studied. The estimator is **biased** (it's not equal to $\mathbf{w}^*$ in expectation — the shrinkage toward zero introduces a systematic downward bias). But it has *lower variance* than OLS. For an appropriately chosen $\lambda$, the *total* expected error — bias² + variance — is lower than OLS.

This is the regularization trade in numbers: spend some bias, save more variance.

When does this trade pay off? When OLS's variance is the binding constraint — which is exactly when:

- $n$ is small relative to $d$ (not much data per parameter).
- Features are highly correlated (multicollinearity, which inflates OLS variance).
- $d > n$ (high-dimensional regression, where OLS doesn't have a unique solution at all).

In modern ML — high-dimensional feature spaces from one-hot encoding, text features, embeddings — these conditions are the *norm*. Some flavor of regularization is almost always on.

---

## 20.3 L1 regularization (lasso)

The L1 regularizer is the absolute-value version:

$$
R(\mathbf{w}) = \|\mathbf{w}\|_1 = \sum_j |w_j|
$$

The L1-regularized loss for linear regression is:

$$
L_{\text{lasso}}(\mathbf{w}, b) = \frac{1}{n}\sum_{i=1}^n (y_i - \mathbf{w} \cdot \mathbf{x}_i - b)^2 + \lambda \|\mathbf{w}\|_1
$$

This is called **lasso regression** ("least absolute shrinkage and selection operator" — Robert Tibshirani, 1996). Two things change relative to L2:

**No closed form.** Because $|w|$ is not differentiable at $w = 0$, the optimization is harder. There's no $(X^TX + n\lambda I)^{-1}$ analog. Solvers use **coordinate descent** (cycle through coordinates, updating one at a time with a closed-form per-coordinate update) or **LARS** (a path algorithm that traces $\hat{\mathbf{w}}$ as $\lambda$ varies). These are out of scope for this curriculum to derive, but they're efficient and standard.

**Sparse solutions.** This is the famous property and the reason L1 is everywhere. The lasso *drives some weights to exactly zero*. Those features are effectively *dropped* from the model. This is **feature selection built into the regularizer**. With L1, you don't decide which features to keep — the regularizer decides.

The next section gives the geometric intuition for *why* L1 induces sparsity while L2 doesn't. This is one of the most worthwhile pictures to internalize in classical ML.

---

## 20.4 The diamond vs. sphere — why L1 induces sparsity

Here is the heart of L1's magic. To get the intuition, look at the optimization problem in a *constrained* form:

$$
\text{Minimize} \quad L(\mathbf{w}) \quad \text{subject to} \quad R(\mathbf{w}) \leq t
$$

This is equivalent to the penalized form $L + \lambda R$ by Lagrangian duality (for every $\lambda \geq 0$ there's a corresponding $t$, and vice versa). The constraint set is the **feasible region** for $\mathbf{w}$.

For **L2**: $R(\mathbf{w}) = \|\mathbf{w}\|_2^2 \leq t$. The feasible region is a *disk* in 2D (a *ball* in higher D). Smooth, round, no corners.

For **L1**: $R(\mathbf{w}) = \|\mathbf{w}\|_1 \leq t$. The feasible region is a *diamond* in 2D — the rotated square with vertices on the axes (an *L1 ball*, with corners pointing along each axis).

The optimization picks the point in the feasible region that minimizes the empirical loss $L(\mathbf{w})$. For linear regression with squared loss, the level curves of $L$ are concentric *ellipses* centered at the OLS optimum $\hat{\mathbf{w}}_{\text{OLS}}$. As the constraint shrinks (smaller $t$, more aggressive regularization), the feasible region shrinks toward the origin. The optimal point is where the smallest ellipse intersects the feasible region — i.e., the *outermost level curve of $L$ that still touches the feasible region*.

```
   L2: smooth circular constraint                L1: corner-y diamond constraint
   ────────────────────────────────              ────────────────────────────────
                                                              w2
              ellipses of L           ↑              ellipses of L         ↑
                                       │                                    │
                                       │                                    │
            ╱─────────╲           ╱│ │              ╱──╲    ◆               │
          ╱     ⊙       ╲       ╱ │ │            ╱     OLS                  │
          │     OLS       │   ╱   │ │           ◇      ⊙ ◆ ─────  ← optimum at corner
          │              │ ╱     │ │             ◇       ◆
            ╲─────────╱           │ │            ◇      ◆
                                  │ │              ◇  ◆
              ↑                   │ │                ◆
        optimum is a point        │ │              
        on the circle             │ │              
        (generally not on axis)   │ │              
                                  ─────────────────── w1     
```

In the L2 picture, the ellipses of $L$ and the round constraint touch at some generic point. There's no reason for that point to lie on either axis. So all weights are typically nonzero — they get shrunk but not eliminated.

In the L1 picture, the ellipses touch the diamond. *The diamond's vertices are on the axes.* When the ellipse touches the diamond at a vertex — and unless the ellipse happens to be perfectly aligned, the corners are the most likely place — the optimum has all-but-one coordinates equal to zero. *Sparsity emerges geometrically.*

In higher dimensions, the picture generalizes: L2's constraint set is a smooth sphere, and the optimum is generically off all coordinate axes (all weights nonzero). L1's constraint set is a polyhedron with corners on coordinate axes, edges between pairs of axes, faces between triples of axes — and ellipses generically touch on these low-dimensional features, producing optima where many weights are exactly zero.

The takeaway:

| Regularizer | Constraint shape | Optimum location | Effect on weights |
|---|---|---|---|
| L2 | Smooth ball | Generic point | All shrunk, none zero |
| L1 | Polyhedron with axis-aligned corners | Often at corner/edge | Many exactly zero (sparsity) |

This is the "diamond vs. sphere" picture and is one of the cleanest visual arguments in ML. If you remember nothing else from this chapter, remember this picture.

---

## 20.5 ElasticNet — the convex combination

L1 and L2 each have strengths and weaknesses:

- L2: dense solutions, smooth optimization, good when many features are weakly informative.
- L1: sparse solutions, automatic feature selection, but can be unstable when features are correlated (it picks one of two correlated features arbitrarily and zeros out the other).

A natural idea: combine them. **ElasticNet** does exactly this:

$$
R_{\text{EN}}(\mathbf{w}) = \alpha \|\mathbf{w}\|_1 + (1-\alpha) \|\mathbf{w}\|_2^2
$$

with $\alpha \in [0, 1]$. The full objective:

$$
L_{\text{EN}}(\mathbf{w}) = L(\mathbf{w}) + \lambda \left[\alpha \|\mathbf{w}\|_1 + (1-\alpha) \|\mathbf{w}\|_2^2\right]
$$

Set $\alpha = 1$: pure L1 (lasso). Set $\alpha = 0$: pure L2 (ridge). Anywhere in between blends.

The benefits of mixing:

- ElasticNet still produces sparse solutions (the L1 component drives weights to zero) but with the L2 component, correlated features tend to be selected *together* rather than arbitrarily one-out, one-in. This is more stable.
- Mathematically, the L2 component smooths the constraint set — the diamond's corners become slightly rounded, the optimization is better-behaved.

scikit-learn's `ElasticNet` and Spark ML's `LinearRegression` with `elasticNetParam` and `regParam` (where `elasticNetParam` is $\alpha$ and `regParam` is $\lambda$) implement this. The standard practical recipe is to fix $\alpha$ to something like 0.5 (or to tune it via CV alongside $\lambda$) and tune $\lambda$ aggressively.

---

## 20.6 The regularization parameter $\lambda$ — sliding the bias-variance trade

$\lambda$ is the dial. Let's understand precisely how it shifts the bias-variance balance.

**$\lambda = 0$:** No regularization. The objective is just empirical loss. We're at OLS / unconstrained MLE. Bias is whatever the model class allows; variance is whatever the data allows. For high-capacity classes, variance is large.

**$\lambda$ small:** Tiny shrinkage. Bias rises slightly (we're now slightly biased toward zero), variance falls slightly. Total error often falls — small $\lambda$ is almost always better than $\lambda = 0$ in practice for high-capacity classes.

**$\lambda$ moderate:** The sweet spot. Variance has dropped substantially, bias has risen but less. Total error is minimized somewhere in this range.

**$\lambda$ large:** All weights heavily shrunk. Variance is small (we're constraining tightly), but bias is now huge — the model is unable to fit the signal because the weights can't grow large enough. Total error rises.

**$\lambda \to \infty$:** All weights forced to zero. Model predicts the (unregularized) intercept everywhere. Bias is at the "predict the mean" baseline; variance is zero. Total error equals the residual sum of squares around the mean.

So as $\lambda$ goes from 0 to $\infty$, you trace a curve in (bias, variance) space:

```
   bias²                                
     │       λ → ∞ (high bias, zero variance)
   high│                                  *
     │                              *  *
     │                          *  *
     │                       * *
     │                     * *
   low│                  * *
     │            * *  *     ← λ small (low bias, high variance)
     └──────────────────────────────────────► variance
              low              high
                       ↑
                     sweet spot at intermediate λ
                  (where total error is minimized)
```

The picture is the *Pareto frontier* of regularized models: each point on the curve is the best bias-variance trade you can achieve at some particular $\lambda$. The minimum of the total-error curve is somewhere on this frontier; CV (Ch 22) is how we find it.

A few practical realities:

- **The right $\lambda$ depends on the data, the features, and the model.** There's no universal good value. You must tune.
- **Log-scale matters.** Sweep $\lambda \in \{10^{-4}, 10^{-3}, 10^{-2}, 10^{-1}, 1, 10, 100\}$ — geometric spacing. Linear spacing is wrong because the *effect* of $\lambda$ is multiplicative.
- **Feature scaling matters.** L1 and L2 penalize $|w|$ and $w^2$ respectively. If feature $j$ ranges over $[0, 1]$ and feature $k$ ranges over $[0, 1000]$, the same $w$ has a thousand-times-bigger effect on the prediction from feature $k$. The regularizer treats them the same — punishing $w$ identically. This means features on different scales get differently regularized. *Always scale features before regularizing* (Ch 26 covers scaling formally).

---

## 20.7 Worked code: ridge and lasso in scikit-learn

```python
import numpy as np
from sklearn.linear_model import Ridge, Lasso, ElasticNet, LinearRegression
from sklearn.preprocessing import StandardScaler

# Synthetic data: y depends on the first 5 features; the next 15 are noise.
rng = np.random.default_rng(0)
n, d = 100, 20
X = rng.normal(size=(n, d))
true_w = np.array([2.0, -1.5, 1.0, 0.5, -0.5] + [0.0] * 15)
y = X @ true_w + rng.normal(scale=0.5, size=n)

# Always scale features before regularizing.
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Baseline: ordinary least squares.
ols = LinearRegression().fit(X_scaled, y)
print(f"OLS coefficients: {np.round(ols.coef_, 3)}")

# Ridge with various lambda. Note sklearn calls it `alpha`, not lambda.
for alpha in [0.01, 1.0, 100.0]:
    ridge = Ridge(alpha=alpha).fit(X_scaled, y)
    print(f"Ridge α={alpha:7.2f}: {np.round(ridge.coef_, 3)}")

print()

# Lasso with various lambda.
for alpha in [0.01, 0.1, 1.0]:
    lasso = Lasso(alpha=alpha).fit(X_scaled, y)
    nonzero = (np.abs(lasso.coef_) > 1e-6).sum()
    print(f"Lasso α={alpha:5.2f}: {nonzero}/20 nonzero coeffs, "
          f"coefs={np.round(lasso.coef_, 3)}")

# ElasticNet
en = ElasticNet(alpha=0.1, l1_ratio=0.5).fit(X_scaled, y)
nonzero = (np.abs(en.coef_) > 1e-6).sum()
print(f"ElasticNet α=0.1 l1_ratio=0.5: {nonzero}/20 nonzero")
```

A typical run prints something like:

```
OLS coefficients: [ 2.030 -1.531  0.997  0.498 -0.523  0.041 -0.063 ... ]
Ridge α=   0.01: [ 2.029 -1.530  0.996  0.498 -0.523  0.041 -0.063 ... ]
Ridge α=   1.00: [ 1.946 -1.475  0.962  0.470 -0.504  0.038 -0.060 ... ]
Ridge α= 100.00: [ 0.572 -0.422  0.295  0.137 -0.149  0.011 -0.018 ... ]

Lasso α= 0.01: 19/20 nonzero coeffs ...
Lasso α= 0.10: 7/20 nonzero coeffs ...
Lasso α= 1.00: 0/20 nonzero coeffs ...

ElasticNet α=0.1 l1_ratio=0.5: 8/20 nonzero
```

Observations:

- **Ridge with small $\alpha$** is essentially OLS — the regularization barely bites.
- **Ridge with $\alpha = 100$** has shrunk everything substantially — the true-signal weights are still proportionally the largest, but everything's smaller.
- **Lasso with $\alpha = 0.01$** is barely sparser than OLS.
- **Lasso with $\alpha = 0.1$** drives 13 of 20 coefficients to exactly zero — and ideally those zeros correspond to the noise features (last 15). In practice, with finite data, lasso often selects the right features but isn't perfect.
- **Lasso with $\alpha = 1.0$** has zeroed every coefficient — over-regularized.
- **ElasticNet** combines: 12 of 20 zero, with stable selection of correlated features.

The crucial *qualitative* difference: even at heavy ridge regularization, *every* coefficient is non-zero. At even modest lasso regularization, *most* coefficients are zero. That's the L1 sparsity property in action.

### 20.7.1 Cross-validation to pick $\lambda$

```python
from sklearn.linear_model import RidgeCV, LassoCV

# RidgeCV with built-in leave-one-out
rcv = RidgeCV(alphas=np.logspace(-3, 3, 20)).fit(X_scaled, y)
print(f"Best ridge α: {rcv.alpha_:.4f}")

# LassoCV with 5-fold
lcv = LassoCV(alphas=np.logspace(-3, 1, 20), cv=5).fit(X_scaled, y)
print(f"Best lasso α: {lcv.alpha_:.4f}")
```

The `*CV` variants do the search automatically. Always specify a logarithmically-spaced grid (via `np.logspace`). Chapter 22 is the deep dive on cross-validation; this is a teaser.

---

## 20.8 Regularization in classification

The same machinery applies to logistic regression with cross-entropy. The objective becomes:

$$
L_{\text{LR}}(\mathbf{w}, b) = -\frac{1}{n}\sum_i [y_i \log \hat{p}_i + (1-y_i)\log(1-\hat{p}_i)] + \lambda R(\mathbf{w})
$$

with $\hat{p}_i = \sigma(\mathbf{w} \cdot \mathbf{x}_i + b)$. The regularizer $R$ can be L1, L2, or ElasticNet. Same geometric picture, same trade-offs.

In scikit-learn, `LogisticRegression(penalty='l2', C=1.0)` — note the parameter is `C` which is the *inverse* of $\lambda$ (so small `C` means strong regularization, opposite of `alpha`). In Spark ML, `LogisticRegression(regParam=0.1, elasticNetParam=0.5)` — same conventions as the linear regression case.

The bias-variance story is the same. L1 selects features. L2 shrinks all weights. ElasticNet blends.

---

## 20.9 Where things go wrong — debugging regularization

A few common pitfalls:

**Forgetting to scale features.** If you regularize unscaled features, the regularizer applies an unequal penalty to features at different scales. Coefficients on small-magnitude features get effectively heavier penalties. The result is unfair feature selection. *Always scale* before regularizing.

**Regularizing the intercept.** Default in most libraries is "no" — verify this. Regularizing the intercept means you're pushing predictions toward zero in absolute terms, which is rarely what you want.

**Choosing $\lambda$ by eyeballing.** Don't. Use cross-validation. The right $\lambda$ for one dataset is wrong for another by orders of magnitude.

**Confusing $\lambda$ direction across libraries.** scikit-learn's `Ridge(alpha=...)` uses $\lambda$ directly (larger = more regularization). scikit-learn's `LogisticRegression(C=...)` uses $1/\lambda$ (larger C = *less* regularization). Spark ML's `regParam` is direct. Read the docs.

**Over-regularizing.** Symptom: training and validation losses are both high *and* close. You've pushed the bias up too far. Decrease $\lambda$.

**Under-regularizing.** Symptom: training loss low, validation high, large gap. Standard overfitting. Increase $\lambda$.

These are the diagnostic tools from Chapter 18 applied to the regularization knob specifically. The U-curve of validation loss vs. $\lambda$ is the *same shape* as the U-curve of validation loss vs. capacity — and indeed, $\lambda$ is *effectively* a capacity dial: high $\lambda$ = low effective capacity, low $\lambda$ = high effective capacity.

---

## 20.10 Summary

The chapter, condensed:

1. **Regularization** = adding a penalty term $\lambda R(\mathbf{w})$ to the empirical loss to discourage complex parameter vectors.
2. **L2 (ridge):** $R(\mathbf{w}) = \|\mathbf{w}\|_2^2$. Penalizes squared magnitude. *Shrinks* weights but doesn't zero them. Has a closed-form solution: $\hat{\mathbf{w}}_{\text{ridge}} = (X^TX + n\lambda I)^{-1}X^T\mathbf{y}$. Stable; works well with correlated features.
3. **L1 (lasso):** $R(\mathbf{w}) = \|\mathbf{w}\|_1$. Penalizes absolute magnitude. Produces *sparse* solutions — many weights exactly zero. Effective feature selection. No closed form; uses coordinate descent.
4. **ElasticNet:** convex combination of L1 and L2. Sparsity from L1 + stability from L2. Most robust default.
5. **Geometric intuition:** L1's constraint set has corners on the axes (sparsity); L2's is smooth (no sparsity).
6. **$\lambda$ slides bias-variance:** small $\lambda$ = low bias, high variance (close to OLS); large $\lambda$ = high bias, low variance. Find sweet spot via CV.
7. **Pre-scale features** before regularizing. Sweep $\lambda$ on a log scale.

The big-picture role of regularization: it lets you use a high-capacity model class *while controlling its variance*. Without regularization, you'd be forced to use low-capacity models in many situations. With regularization, you can use, say, all 10,000 features of a TF-IDF vector for spam classification, and the regularizer will figure out which ~50 of them are actually useful and zero the rest.

---

## 20.11 What this builds on / where this returns

**Builds on:**
- Chapter 16 (loss functions — we just modified the loss).
- Chapter 17 (gradient descent — the optimization machinery).
- Chapter 18 (overfitting — the disease regularization treats).
- Chapter 19 (bias-variance — the framework that explains *why* regularization helps).

**Returns:**
- *Chapter 22* (cross-validation): the mechanism for choosing $\lambda$.
- *Chapter 31* (linear regression): ridge as a numerical and statistical refinement.
- *Chapter 32* (logistic regression): L1/L2-regularized logistic regression is the standard.
- *Chapter 36* (gradient boosting): the *shrinkage* parameter in GBT is conceptually similar — a per-iteration regularizer.
- *Part I* (HPO): tuning $\lambda$ is the canonical example of hyperparameter optimization.
- *Part K* (`pyspark.ml`): the `regParam` and `elasticNetParam` parameters expose exactly what we derived here.

---

## 20.12 Exercises

1. **The general form.** Write the L2-regularized loss for linear regression in symbols. Identify which terms are empirical loss and which are the regularizer.

2. **Derive ridge.** Re-derive the ridge regression closed-form solution from scratch. Verify the steps from §20.2.2.

3. **L1 vs. L2 weights.** Suppose OLS gives $\mathbf{w}_{\text{OLS}} = (2.5, -0.1, 0.05, 1.8, -3.0)$. Qualitatively, what do you expect ridge regression and lasso to do to these weights, respectively, for moderate $\lambda$?

4. **The geometric picture.** Sketch the L1 and L2 constraint sets in 2D. Sketch an ellipse of constant empirical loss. Mark where the optimum lies for each.

5. **A scaling problem.** You have two features, $x_1 \in [0, 1]$ and $x_2 \in [0, 1000]$, both equally informative about $y$. You apply L2 regularization without scaling. What happens to $w_1$ relative to $w_2$? Why is this bad?

6. **Sparsity counting.** A 100-feature lasso fit with $\lambda$ chosen by CV produces 15 nonzero coefficients. Why is this often a desirable outcome?

7. **Numerical illustration.** Use the §20.2.3 example: data $(1, 2), (2, 5), (3, 7)$. Compute ridge $w$ with $\lambda = 5$. Compute training MSE at this $w$. Compare to OLS.

8. **Why L2 has a closed form but L1 doesn't.** Explain in one paragraph.

9. **The C-vs-$\lambda$ convention.** Why does `LogisticRegression(C=10)` use *less* regularization than `LogisticRegression(C=0.1)`? What's the relation between `C` and $\lambda$?

10. **Diagnosing $\lambda$.** Training loss is 0.40, validation loss is 0.41. The model is regularized at $\lambda = 100$. Should you increase or decrease $\lambda$? What's the diagnosis?

11. **An asymmetric correlation case.** You have features $x_1$ and $x_2$ where $x_2 = x_1 + \text{tiny noise}$ (highly correlated, nearly identical). OLS will be unstable. What will pure L1 do? Pure L2? ElasticNet?

12. **A research-level question.** In what regime do you expect L1 to outperform L2? L2 to outperform L1? When are they roughly equivalent?

<details>
<summary>Answers</summary>

1. $L = \frac{1}{n}\sum_{i=1}^n (y_i - \mathbf{w} \cdot \mathbf{x}_i - b)^2 + \lambda \|\mathbf{w}\|_2^2$. Empirical loss: the squared-error sum. Regularizer: $\lambda \|\mathbf{w}\|_2^2$.

2. As in §20.2.2: write the MSE in matrix form, expand, take gradient, set to zero, solve. Result: $(X^TX + n\lambda I)\mathbf{w} = X^T\mathbf{y}$.

3. Ridge: every coefficient shrunk toward zero proportionally. So roughly $(2.0, -0.08, 0.04, 1.4, -2.4)$ for moderate $\lambda$. Lasso: the smallest coefficients in magnitude (the $-0.1$ and $0.05$) are likely driven to zero; the larger ones shrunk but kept. Result: something like $(2.0, 0.0, 0.0, 1.4, -2.4)$.

4. L2: a circle. L1: a diamond. Ellipse: concentric around OLS optimum. Optimum is at the tangency point. For L2 this is a generic point on the circle. For L1 the tangency typically occurs at a corner of the diamond, on an axis.

5. The OLS solution has $w_1$ roughly 1000× larger than $w_2$ (because $w_2 \cdot x_2 = w_1 \cdot x_1$ requires $w_2 = w_1 / 1000$). Now the L2 penalty $w_1^2 + w_2^2$ is dominated by $w_1^2$. The regularizer aggressively shrinks $w_1$, hardly touches $w_2$ — unequal treatment of equally-informative features. Scaling first puts them on equal footing.

6. Sparsity is interpretable (you can tell which features matter), faster at inference (fewer multiplications), more robust to noisy/irrelevant features, easier to maintain in production (fewer features to monitor). Often the true generating process is sparse and L1 recovers the true support.

7. $X^TX = 14$, $X^T\mathbf{y} = 33$, $n\lambda = 15$. $w_{\text{ridge}} = 33/(14+15) = 33/29 \approx 1.138$. OLS: $w \approx 2.357$. Predictions at $\lambda = 5$: $(1.14, 2.28, 3.41)$. Residuals: $(0.86, 2.72, 3.59)$. MSE = $(0.74 + 7.40 + 12.88)/3 \approx 7.0$. Much higher than OLS's $\approx 0.07$. Over-regularized at $\lambda = 5$ for this tiny dataset.

8. L2's regularizer is differentiable everywhere (it's a smooth quadratic). Adding it to the squared-error loss keeps the total quadratic, which has a unique zero-gradient point — solvable by linear algebra. L1's regularizer $|w|$ is non-differentiable at zero. The total loss is convex but not smooth — the gradient doesn't exist at points where any $w_j = 0$. You can't solve "set gradient to zero" because the gradient isn't defined there. So you use iterative methods (coordinate descent, LARS) that handle the kink correctly.

9. scikit-learn's convention is $C = 1/\lambda$. Large $C$ = small $\lambda$ = weak regularization. Small $C$ = large $\lambda$ = strong regularization. The convention comes from the SVM literature where $C$ controls the "softness" of the margin.

10. Training and validation are both high and close — underfit, or over-regularized. *Decrease* $\lambda$.

11. L1: arbitrary — picks one of $x_1, x_2$ and zeros the other. Across runs or slight data changes, which one it picks can flip. Unstable selection. L2: keeps both, splits the credit between them (each gets about half the weight a single feature would have). Stable. ElasticNet: keeps both together (the L2 component prevents the flip) but still drives nearby weak features to zero (the L1 component). Often the right default for correlated-feature settings.

12. L1 wins when the true generating function is sparse (few features actually matter). L2 wins when many features each contribute a small amount. Equivalent in non-sparse, low-correlation regimes. In practice, when in doubt, ElasticNet (which can lean either way).

</details>
