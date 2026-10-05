# Chapter 32 — Logistic Regression — Log-Odds, MLE, Decision Boundary

> **Goal of this chapter:** to build logistic regression from the ground up — the sigmoid, the log-odds parameterization, the maximum-likelihood derivation, the decision boundary, and why gradient descent is the only way to fit it. In Chapter 3 we used logistic regression as a black box for spam classification; here we open the box and see every gear. By the end you will be able to explain, on a whiteboard, why logistic regression makes the predictions it does and what would change if you altered any piece of its setup.

---

## 32.1 Why the name is misleading, and why it matters

The name "logistic regression" is one of the more confusing artifacts of statistics' history. The word **regression** suggests we're predicting a continuous quantity. The word **logistic** suggests something to do with logistics. Both impressions are wrong.

Logistic regression is a **classification** algorithm — its output is a probability over discrete classes. It is called "regression" because what's being modeled in the linear-form-with-coefficients sense is the **log-odds** of the positive class (we'll define this carefully in §32.4). The model regresses the log-odds onto the features; the classification falls out of that.

The name has stuck for over a century. We are not going to fix it. But internalizing what it *means* — a linear model in log-odds space — is the right place to start.

Why this matters: students who think "logistic regression is for classification" memorize a fact. Students who think "logistic regression is linear regression on the logit of the probability" can derive everything that follows. The first group panics when you ask them why the coefficients are interpreted as log-odds multipliers. The second group already knew.

---

## 32.2 Why we don't just use linear regression for {0, 1} labels

Suppose you have a binary classification problem — spam (1) or ham (0). The obvious-but-wrong instinct is to encode the label as $\{0, 1\}$ and just fit a linear regression. Plug in $X$ and $y$, compute $\hat{w} = (X^\top X)^{-1} X^\top y$, and use $w^\top x$ as your "spam score."

This kind of works, in the sense that producing a number is better than producing nothing. But it is wrong on two counts.

**Problem 1: predictions go outside $[0, 1]$.** $w^\top x$ is an unbounded linear function. For any data, some prediction $w^\top x$ will be negative; for other data, some will exceed 1. What does it mean to say an email has spam probability $-0.3$ or 1.7? It means we have used the wrong model class.

**Problem 2: squared-error loss is suboptimal for {0, 1} targets.** Squared error was derived (Chapter 31) as the MLE under Normal noise. Bernoulli targets have variance $p(1-p)$ — *non-constant in $p$*. Squared error gives equal penalty to a wrong prediction near 0.5 as to a wrong prediction near 0 or 1, but probabilistically these are very different errors. The right loss function falls out of treating the labels as Bernoulli.

The fix to both problems is the same: pass the linear prediction $w^\top x$ through a function that squashes it into $(0, 1)$ — and choose that function so the resulting model has a clean probabilistic interpretation. That function is the **sigmoid**, also called the **logistic function**.

---

## 32.3 The logistic function and its geometry

Define

$$
\sigma(z) = \frac{1}{1 + e^{-z}}
$$

This is the **logistic** or **sigmoid** function. The name "sigmoid" comes from its S-shape; "logistic" is older, from Verhulst's 1840s work on population growth.

Key properties to memorize:

- **Range.** $\sigma(z) \in (0, 1)$ for all real $z$. As $z \to -\infty$, $\sigma(z) \to 0$; as $z \to +\infty$, $\sigma(z) \to 1$. Never exactly 0 or 1, but arbitrarily close.
- **Midpoint.** $\sigma(0) = \frac{1}{1+1} = 0.5$. The function is symmetric around $(0, 0.5)$.
- **Symmetry.** $\sigma(-z) = 1 - \sigma(z)$. Cross-check: $\sigma(-z) = \frac{1}{1+e^z} = \frac{e^{-z}}{e^{-z}+1}$ and $1 - \sigma(z) = 1 - \frac{1}{1+e^{-z}} = \frac{e^{-z}}{1+e^{-z}}$. Same.
- **Derivative.** This will matter for gradient descent. $\sigma'(z) = \sigma(z)(1 - \sigma(z))$. Derive it: $\sigma(z) = (1 + e^{-z})^{-1}$, so $\sigma'(z) = -(1 + e^{-z})^{-2} \cdot (-e^{-z}) = \frac{e^{-z}}{(1+e^{-z})^2}$. Multiply top and bottom by $\frac{1}{1+e^{-z}}$: $\frac{1}{1+e^{-z}} \cdot \frac{e^{-z}}{1+e^{-z}} = \sigma(z) \cdot (1 - \sigma(z))$. Done.

The derivative is largest at $z = 0$ (value $0.25$) and shrinks toward zero as $|z|$ grows. This is the "vanishing gradient" of saturation — when $w^\top x$ is large in magnitude, $\sigma'$ is tiny and learning slows. We'll see this affect optimization.

```
  σ(z) = 1/(1 + e^(-z))

   1 ┤                       _____________
     │                  ____/
     │              ___/
   0.75┤           _/
     │          _/
   0.5┤        /                ← σ(0) = 0.5
     │      _/
   0.25┤  _/
     │_/
   0 ┤___________
     └──────────┼──────────────────────►
              z=0
```

---

## 32.4 The model — and the log-odds parameterization

The logistic regression model is

$$
\hat{p}(y = 1 \mid x) = \sigma(w^\top x)
$$

(With bias absorbed into $w$, as in Chapter 31.)

That's the predictive form. But the deeper structure becomes visible when we invert the sigmoid. Set $p = \sigma(z)$, so $z = \sigma^{-1}(p)$. Solve:

$$
p = \frac{1}{1 + e^{-z}} \iff 1 + e^{-z} = \frac{1}{p} \iff e^{-z} = \frac{1-p}{p} \iff z = \log\frac{p}{1-p}
$$

The quantity $\log\frac{p}{1-p}$ is called the **log-odds** or **logit** of $p$. The model says

$$
\boxed{\log\frac{\hat{p}}{1 - \hat{p}} = w^\top x}
$$

This is the form that justifies the name "regression": **we are doing linear regression on the log-odds**. The model is linear in the log-odds, *not* in the probability.

### 32.4.1 Interpreting the coefficients

Suppose feature $x_j$ is "number of past spam reports" with weight $w_j = 0.4$. What does $w_j = 0.4$ mean?

Increasing $x_j$ by 1 increases the log-odds by 0.4. Exponentiating, the **odds** of spam are multiplied by $e^{0.4} \approx 1.49$. So each additional past spam report makes the email 1.49× *more odds* of being spam (not 1.49× more probability — odds, which is $p/(1-p)$).

This is the canonical interpretation of logistic regression coefficients, and it is *the* reason logistic regression dominates in regulated industries: every coefficient has a real, defensible meaning. In a Capital One credit-risk submission to the OCC, you can point at "this feature increases the odds of default by 12% per unit, with 95% confidence interval [8%, 16%]" and have a regulator understand exactly what the model is doing.

By contrast, "node 47 of tree 213 in the gradient boosting ensemble splits on this feature at threshold 0.3" is true but useless for an auditor.

### 32.4.2 What "linear in log-odds" lets us do and doesn't

Because the log-odds is linear in $x$, logistic regression captures **monotone, smooth, additive** effects of features on the probability. It does NOT capture:

- **Non-monotone effects** (where, say, low and high values of $x$ both predict $y=1$ but middle values predict $y=0$). You'd need polynomial features or a different model.
- **Feature interactions**. If the effect of $x_1$ depends on the value of $x_2$, you need an explicit interaction term $x_1 \cdot x_2$ as a feature.
- **Threshold effects**. A sudden jump at $x = 5$ requires either binning the feature or a non-linear model.

Adding these features by hand is exactly the feature engineering of Chapter 28. The flexibility of more complex models (trees, GBT) is that they find these patterns automatically. The discipline of logistic regression is that *you* find them, you understand them, and the model behaves predictably.

---

## 32.5 Maximum Likelihood Estimation — the loss derivation

We now need to fit the weights. The principle: maximize the likelihood of the observed labels given the features.

Assume each $y_i \mid x_i \sim \text{Bernoulli}(p_i)$ where $p_i = \sigma(w^\top x_i)$. The Bernoulli PMF is $P(y = 1) = p$, $P(y = 0) = 1 - p$, which we can write as a single formula:

$$
P(y_i \mid x_i, w) = p_i^{y_i} (1 - p_i)^{1 - y_i}
$$

(Check: $y_i = 1$ gives $p_i$; $y_i = 0$ gives $1 - p_i$.) Assuming examples are independent, the likelihood of the entire training set is:

$$
\mathcal{L}(w) = \prod_{i=1}^n p_i^{y_i} (1 - p_i)^{1 - y_i}
$$

Take logs (maximizing $\mathcal{L}$ ≡ maximizing $\log \mathcal{L}$):

$$
\log \mathcal{L}(w) = \sum_{i=1}^n \left[ y_i \log p_i + (1 - y_i) \log(1 - p_i) \right]
$$

That is exactly the negative of the **binary cross-entropy** loss. Define

$$
\boxed{L(w) = -\sum_{i=1}^n \left[ y_i \log p_i + (1 - y_i) \log(1 - p_i) \right]}
$$

where $p_i = \sigma(w^\top x_i)$. **Maximizing log-likelihood = minimizing cross-entropy.** They are the same optimization problem, off by a sign.

We've now justified, from first principles, why classification training is done with cross-entropy and not squared error: because cross-entropy is the MLE under the Bernoulli model, the way squared error was the MLE under the Normal model.

### 32.5.1 No closed form

Compute $\nabla_w L$ and see what happens. Apply the chain rule. For a single example:

$$
\frac{\partial L_i}{\partial w} = -\left[ y_i \cdot \frac{1}{p_i} - (1 - y_i) \cdot \frac{1}{1 - p_i} \right] \cdot \frac{\partial p_i}{\partial w}
$$

And $\frac{\partial p_i}{\partial w} = \sigma'(w^\top x_i) \cdot x_i = p_i(1 - p_i) \cdot x_i$. Plug in:

$$
\frac{\partial L_i}{\partial w} = -\left[ y_i (1 - p_i) - (1 - y_i) p_i \right] x_i = -(y_i - p_i) x_i = (p_i - y_i) x_i
$$

A beautiful simplification — the per-example gradient is the prediction error times the input. Summed over examples:

$$
\boxed{\nabla_w L = \sum_{i=1}^n (p_i - y_i) x_i = X^\top (p - y)}
$$

where $p = (\sigma(w^\top x_1), \ldots, \sigma(w^\top x_n))^\top$ is the prediction vector.

Notice the *structure*: this gradient has the same shape as linear regression's $X^\top(Xw - y)$, with the linear predictor $Xw$ replaced by the sigmoid prediction $p = \sigma(Xw)$.

Setting the gradient to zero: $X^\top (p - y) = 0$, where $p$ depends on $w$ through the *nonlinear* sigmoid. There is no closed-form solution. We solve iteratively.

---

## 32.6 Gradient descent and Newton's method

### 32.6.1 Vanilla gradient descent

The update rule (Chapter 17):

$$
w \leftarrow w - \eta \cdot \nabla_w L = w - \eta \cdot X^\top (p(w) - y)
$$

Pick a learning rate $\eta$. Compute $p$ given the current $w$. Update. Repeat until convergence.

L is **convex** in $w$ — this is a key fact. Convexity means there's a unique global minimum (or, when $X^\top X$ is singular, a flat optimal subspace), no local minima to worry about, and any reasonable optimizer converges to the global optimum.

To see convexity directly: the Hessian is

$$
\nabla^2_w L = X^\top D X
$$

where $D$ is a diagonal matrix with $D_{ii} = p_i(1 - p_i) \geq 0$. For any vector $v$, $v^\top X^\top D X v = (Xv)^\top D (Xv) = \sum_i D_{ii} (Xv)_i^2 \geq 0$. Positive semi-definite. $L$ is convex.

### 32.6.2 Newton's method (a.k.a. IRLS)

For convex problems, Newton's method converges *quadratically* (faster than gradient descent's linear rate) at the cost of computing the Hessian. The Newton update is

$$
w \leftarrow w - (\nabla^2_w L)^{-1} \nabla_w L = w - (X^\top D X)^{-1} X^\top (p - y)
$$

This is also called **iteratively reweighted least squares** (IRLS) because each Newton step looks like solving a weighted least-squares problem with weights $D$. IRLS is what `statsmodels.Logit` uses by default and what most pre-2010 logistic regression implementations used.

For modern large-scale problems, gradient descent (or L-BFGS, a quasi-Newton method that approximates the Hessian without ever materializing it) is preferred — Newton's $O(d^3)$ per step is prohibitive for $d > 10{,}000$.

---

## 32.7 The decision boundary

The model predicts probability $\hat{p}(x) = \sigma(w^\top x)$. To convert to a class label, we threshold (Chapter 3):

$$
\hat{y}(x) = \begin{cases} 1 & \text{if } \hat{p}(x) \geq \tau \\ 0 & \text{otherwise} \end{cases}
$$

The set of $x$ where $\hat{p}(x) = \tau$ is the **decision boundary**. At the default $\tau = 0.5$, the boundary is where $\sigma(w^\top x) = 0.5$, which means $w^\top x = 0$ (since $\sigma(0) = 0.5$). That is a **hyperplane** in feature space — a line in 2D, a plane in 3D, a $(d-1)$-dimensional flat in $d$D.

```
  Two features, decision boundary at w·x + b = 0

     x2
      ▲
      │   ●     ●
      │      ●          ●  ← class 0
      │ ●        ●
      │─────────────────────  decision boundary
      │       ▽    ▽
      │  ▽          ▽
      │   ▽   ▽          ▽  ← class 1
      │
      └────────────────────► x1
```

This is the key geometric fact about logistic regression: **the decision boundary is linear**. Even though the model output is a non-linear function of $x$ (because of the sigmoid), the *boundary between predicted classes* is a hyperplane. Inputs on one side of the hyperplane get class 1; inputs on the other get class 0.

This is also exactly the same boundary you'd get from many other linear classifiers — perceptron, linear SVM, linear discriminant analysis. They differ in how the boundary is *chosen* (the loss function), not in its geometric form. If your true class-separating surface is non-linear (say, circular or curved), no logistic regression with raw features can capture it. You'd need polynomial features, kernel methods, or trees.

### 32.7.1 Moving the threshold moves the boundary

At $\tau \neq 0.5$, the boundary is $\sigma(w^\top x) = \tau$, which gives $w^\top x = \sigma^{-1}(\tau) = \log\frac{\tau}{1 - \tau}$. So the boundary stays parallel to the $\tau = 0.5$ boundary but is shifted by the log-odds of $\tau$. This is exactly the same threshold dial from Chapter 3, viewed geometrically.

---

## 32.8 A worked numerical example: 3 iterations of gradient descent

Let's actually run gradient descent on a tiny dataset to see the machinery.

Four points in 2D:

| $i$ | $x_{i,1}$ | $x_{i,2}$ | $y_i$ |
|----:|----------:|----------:|------:|
| 1 | 1 | 1 | 0 |
| 2 | 1 | 2 | 0 |
| 3 | 2 | 3 | 1 |
| 4 | 3 | 2 | 1 |

We absorb the bias by prepending a 1. So each $x_i = (1, x_{i,1}, x_{i,2})$ and we have $w = (b, w_1, w_2)$ to learn. Initialize $w = (0, 0, 0)$ and use learning rate $\eta = 0.1$.

**Iteration 1.**

At $w = (0, 0, 0)$, every $w^\top x_i = 0$, so $p_i = \sigma(0) = 0.5$ for all $i$.

Errors $p_i - y_i$: $0.5 - 0, 0.5 - 0, 0.5 - 1, 0.5 - 1 = 0.5, 0.5, -0.5, -0.5$.

Gradient: $\sum (p_i - y_i) x_i$, summed component-wise.

- Bias component: $0.5 + 0.5 - 0.5 - 0.5 = 0$.
- $w_1$ component: $0.5 \cdot 1 + 0.5 \cdot 1 - 0.5 \cdot 2 - 0.5 \cdot 3 = 0.5 + 0.5 - 1 - 1.5 = -1.5$.
- $w_2$ component: $0.5 \cdot 1 + 0.5 \cdot 2 - 0.5 \cdot 3 - 0.5 \cdot 2 = 0.5 + 1 - 1.5 - 1 = -1$.

So $\nabla L = (0, -1.5, -1)$.

Update: $w \leftarrow w - 0.1 \cdot (0, -1.5, -1) = (0, 0.15, 0.10)$.

**Iteration 2.**

Compute $w^\top x_i$ for each $i$:

- $i=1$: $0 + 0.15 \cdot 1 + 0.10 \cdot 1 = 0.25$. $p_1 = \sigma(0.25) \approx 0.562$.
- $i=2$: $0 + 0.15 + 0.20 = 0.35$. $p_2 = \sigma(0.35) \approx 0.587$.
- $i=3$: $0 + 0.30 + 0.30 = 0.60$. $p_3 = \sigma(0.60) \approx 0.646$.
- $i=4$: $0 + 0.45 + 0.20 = 0.65$. $p_4 = \sigma(0.65) \approx 0.657$.

Errors: $0.562, 0.587, -0.354, -0.343$.

Gradient (component-wise):
- Bias: $0.562 + 0.587 - 0.354 - 0.343 = 0.452$.
- $w_1$: $0.562 + 0.587 - 0.354 \cdot 2 - 0.343 \cdot 3 = 1.149 - 0.708 - 1.029 = -0.588$.
- $w_2$: $0.562 + 0.587 \cdot 2 - 0.354 \cdot 3 - 0.343 \cdot 2 = 0.562 + 1.174 - 1.062 - 0.686 = -0.012$.

Update: $w \leftarrow (0, 0.15, 0.10) - 0.1 \cdot (0.452, -0.588, -0.012) = (-0.045, 0.209, 0.101)$.

**Iteration 3.**

Compute predictions again. I'll just give the final answer to keep the arithmetic readable:

- $i=1$: $-0.045 + 0.209 + 0.101 = 0.265$. $p_1 \approx 0.566$.
- $i=2$: $-0.045 + 0.209 + 0.202 = 0.366$. $p_2 \approx 0.590$.
- $i=3$: $-0.045 + 0.418 + 0.303 = 0.676$. $p_3 \approx 0.663$.
- $i=4$: $-0.045 + 0.627 + 0.202 = 0.784$. $p_4 \approx 0.687$.

Errors: $0.566, 0.590, -0.337, -0.313$.

After 3 iterations, the predictions for the spam-class examples ($y=1$, indices 3 and 4) have moved from 0.5 to about 0.67-0.69. The ham examples ($y=0$, indices 1 and 2) have moved from 0.5 to about 0.57-0.59. The decision boundary is slowly rotating to separate the classes. After ~50 iterations the model converges and the four points are correctly classified.

The point of doing this by hand: gradient descent is *not magic*. Each step is a gradient evaluation and a subtraction. The "training" of logistic regression is exactly this process, iterated until convergence.

---

## 32.9 Regularization

Logistic regression overfits when the model can perfectly separate the classes — the weight vector can grow arbitrarily large and the loss can drop arbitrarily low. The pathological case: linearly separable data with no regularization → the optimizer pushes weights to infinity, sigmoid outputs saturate at 0 or 1, and the model "memorizes" the training set with infinitely confident predictions on it. We discussed this geometrically in Chapter 20.

The fix is the same as in linear regression: add a penalty.

**L2-regularized logistic regression:**

$$
L_{\text{ridge}}(w) = -\sum_i [y_i \log p_i + (1-y_i)\log(1-p_i)] + \frac{\lambda}{2} \|w\|^2
$$

The gradient becomes $X^\top(p - y) + \lambda w$. Still convex. Still no closed form. Solved iteratively.

**L1-regularized logistic regression** (the "lasso logistic"): replace $\|w\|^2$ with $\|w\|_1$. As in linear regression, this drives some weights to exactly zero — implicit feature selection. Useful when you have thousands of features and expect most are irrelevant.

**ElasticNet**: a mix of L1 and L2.

scikit-learn's `LogisticRegression` parameterizes by `C = 1/λ` (inverse regularization strength) — smaller `C` means more regularization. This is a confusing convention that comes from SVM literature. Spark MLlib uses `regParam = λ` directly with `elasticNetParam` blending L1 and L2.

---

## 32.10 Multi-class extension: softmax regression

Logistic regression natively handles two classes. For $K$ classes, the generalization is **softmax regression**, also called **multinomial logistic regression**.

Maintain $K$ weight vectors $w_1, \ldots, w_K$, one per class. Predict the probability of class $c$ for input $x$ as:

$$
\hat{p}(y = c \mid x) = \frac{\exp(w_c^\top x)}{\sum_{c'=1}^K \exp(w_{c'}^\top x)}
$$

This is the **softmax function**: a generalization of the sigmoid to $K$ classes. The exponentials make every numerator positive; the denominator (sum over all classes) normalizes so probabilities sum to 1.

For $K = 2$, softmax reduces to sigmoid (with some redundancy that's usually absorbed by setting one of the $w_c = 0$).

The loss is the **categorical cross-entropy**:

$$
L(W) = -\sum_i \sum_{c=1}^K \mathbb{1}[y_i = c] \log \hat{p}(y_i = c \mid x_i) = -\sum_i \log \hat{p}(y_i \mid x_i)
$$

The second form is more compact: for each example, take the log of the predicted probability of the true class, sum, negate.

Gradient: $\nabla_{w_c} L = \sum_i (\hat{p}_{ic} - \mathbb{1}[y_i = c]) x_i$. Same structure as binary — error times input.

scikit-learn's `LogisticRegression` does softmax by default for multi-class problems (when `multi_class='multinomial'`). The alternative `multi_class='ovr'` trains $K$ binary classifiers in one-vs-rest fashion; usually multinomial is preferred. Spark MLlib's `LogisticRegression` supports both binary (default) and multinomial (set `family="multinomial"`).

---

## 32.11 The scaling pitfall

A trap that catches every new logistic-regression user at least once: **logistic regression with gradient descent needs scaled features**.

Why? The per-feature gradient is $\sum_i (p_i - y_i) x_{ij}$. If feature $j$ has values in the millions, this gradient is huge. If feature $j'$ has values near 1, that gradient is small. A single learning rate $\eta$ can't suit both — too large for $j$, too small for $j'$, or vice versa. The optimizer thrashes.

Fix: standardize features (Chapter 26) to mean 0, std 1 before fitting. The gradients are then comparable across features and a single $\eta$ works.

If you use a more sophisticated optimizer (L-BFGS, Newton, IRLS) that uses second-order information (the Hessian), scaling matters less — the Hessian re-scales the gradient appropriately. But it's still good practice. `sklearn.preprocessing.StandardScaler` followed by `LogisticRegression` in a `Pipeline` is the canonical idiom.

OLS, by contrast, is scale-invariant (Chapter 31.10.2). Logistic regression with gradient descent is not. With L2 regularization, neither is — for the same reason.

---

## 32.12 Why logistic regression remains a workhorse

Compared to a random forest or a gradient-boosted tree, logistic regression is "boring." So why is it still everywhere?

**Interpretability.** Each coefficient is a real number with a defensible meaning. Regulators, executives, and on-call engineers can read the model directly. The coefficient on "credit_utilization_ratio" is positive — that's something you can explain.

**Calibrated probabilities.** Out of the box, logistic regression outputs probabilities that are *close to calibrated* — when it says 70%, about 70% of those cases really are positive. Random forests and SVMs do not have this property without post-hoc calibration (Platt scaling, isotonic regression). For cost-sensitive thresholding (Chapter 3) you really do need calibrated probabilities; logistic regression is the cheapest way to get them.

**Fast at scale.** A logistic-regression inference is one dot product. For billions of predictions per day at low latency — ad bidding, fraud scoring — this matters. Random forests are slower (you have to walk every tree); deep nets are slower still.

**Few hyperparameters.** Just $\lambda$ (or $C$) and maybe the choice of L1/L2/elastic. Easy to tune. Easy to retrain. Easy to monitor.

**Strong baseline.** On text classification with TF-IDF features (Chapter 3), on tabular data with well-engineered features, logistic regression is often within 1-2 points of XGBoost. The question becomes: are those 1-2 points worth the loss in interpretability, training complexity, and inference latency? Often the answer is no.

**Generalizable framework.** Logistic regression is the simplest **generalized linear model**. The framework extends to Poisson regression (count targets), Gamma regression (positive continuous), and many others. Once you understand logistic, you understand the whole GLM family.

The reason logistic regression is on a Databricks ML Associate exam, and on every other ML certification, is not nostalgia. It is because it is genuinely useful and a foundational concept that many other techniques generalize from.

---

## 32.13 Code

### 32.13.1 NumPy from scratch

```python
import numpy as np

def sigmoid(z):
    # Numerically stable: split positive/negative cases
    return np.where(z >= 0, 1 / (1 + np.exp(-z)), np.exp(z) / (1 + np.exp(z)))

def logistic_regression(X, y, lr=0.1, n_iter=1000, lam=0.0):
    """Returns fitted weights w, with bias as w[0]."""
    n, d = X.shape
    X_aug = np.column_stack([np.ones(n), X])
    w = np.zeros(d + 1)
    for _ in range(n_iter):
        p = sigmoid(X_aug @ w)
        grad = X_aug.T @ (p - y) + lam * w
        # Don't regularize the bias
        grad[0] -= lam * w[0]
        w -= lr * grad
    return w

# Toy data
X = np.array([[1,1],[1,2],[2,3],[3,2]])
y = np.array([0, 0, 1, 1])
w_hat = logistic_regression(X, y, lr=0.5, n_iter=2000)
print(w_hat)  # something like [-6.5, 1.5, 1.5]
```

The sigmoid implementation needs the conditional to avoid `exp(-z)` overflow for very negative `z`. This is a real numerical concern at scale; every production logistic-regression implementation does this trick.

### 32.13.2 scikit-learn

```python
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("lr", LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000))
])
pipe.fit(X, y)
print(pipe.named_steps["lr"].coef_)
print(pipe.named_steps["lr"].intercept_)

# Probability and class predictions
probs = pipe.predict_proba(X_new)  # shape (n, 2)
classes = pipe.predict(X_new)
```

`solver="lbfgs"` is the default and a good choice for moderate $d$. `solver="liblinear"` is faster for small datasets with L1. `solver="saga"` handles L1, L2, ElasticNet, and large $n$.

### 32.13.3 PySpark MLlib preview

```python
from pyspark.ml.classification import LogisticRegression as SparkLR

lr = SparkLR(featuresCol="features", labelCol="label",
             regParam=0.01, elasticNetParam=0.0,
             family="binomial")  # or "multinomial"
model = lr.fit(train_df)
predictions = model.transform(test_df)  # has rawPrediction, probability, prediction
```

Spark's logistic regression uses L-BFGS (with a switch to OWLQN for L1). It handles binary by default and multinomial when `family="multinomial"` — important for the exam. Output columns: `rawPrediction` (the log-odds $w^\top x$), `probability` (after sigmoid/softmax), `prediction` (the argmax class).

---

## 32.14 What this builds on / where this returns

**Builds on:**
- Chapter 6 — the Bernoulli distribution.
- Chapter 7 — joint probability for the likelihood.
- Chapter 8 — Bayes' theorem (logistic regression can be derived as the posterior class probability under a Gaussian class-conditional with shared covariance, but we won't lean on this).
- Chapter 16 — cross-entropy as the canonical classification loss.
- Chapter 17 — gradient descent.
- Chapter 20 — regularization.
- Chapter 31 — the design matrix, the bias-absorption trick, the closed form for OLS that's *almost* the same structure as the gradient here.

**Returns:**
- Chapter 65 — `pyspark.ml.classification.LogisticRegression` in depth.
- Chapter 67 — pipeline persistence with logistic regression as the canonical example.
- Chapter 42 — when we formalize precision/recall/F1, logistic regression's calibrated probabilities are the right input for cost-sensitive thresholding.

---

## 32.15 Exercises

1. **Derive the sigmoid derivative.** Show that $\sigma'(z) = \sigma(z)(1 - \sigma(z))$, starting from $\sigma(z) = 1/(1 + e^{-z})$.

2. **Log-odds interpretation.** A logistic regression has weight $w_j = -0.5$ on feature "years_at_current_job" for predicting loan default. Interpret this in words. By what factor does each additional year change the odds of default?

3. **Why not squared error.** Suppose you used squared error $\sum (y_i - \sigma(w^\top x_i))^2$ as the logistic-regression loss. Compute the gradient. What undesirable property does it have when $p_i$ is near 0 or 1? (Hint: the sigmoid derivative.)

4. **Cross-entropy from MLE.** Write out the Bernoulli likelihood for a 3-example training set $(y_1, y_2, y_3) = (1, 0, 1)$ with predicted probabilities $(0.8, 0.3, 0.6)$. Take the log and sum to get the log-likelihood. Then negate for the cross-entropy.

5. **Decision boundary equation.** A logistic regression has been fit with $b = -1$, $w_1 = 2$, $w_2 = -3$. Write the equation of the decision boundary at the default threshold. Sketch it on a 2D plot.

6. **Threshold and boundary shift.** Continuing the previous exercise, what is the decision boundary at threshold $\tau = 0.7$?

7. **One iteration of gradient descent.** With training data $(x_1, x_2, y) = (1, 0, 1), (0, 1, 0), (1, 1, 1)$ and initial weights $w = (b, w_1, w_2) = (0, 0, 0)$ and learning rate 0.1, compute one gradient-descent update. Show the gradient and the new $w$.

8. **Linearly separable trap.** Why does logistic regression with no regularization "blow up" (weights go to infinity) on linearly separable data? Give two ways to prevent this.

9. **Softmax sanity check.** A 3-class softmax classifier produces logits $(z_1, z_2, z_3) = (2, 0, -1)$ for some example. Compute the softmax probabilities. What class is predicted?

10. **Why scaling matters.** Two features: $x_1$ has values around $10^6$, $x_2$ around $1$. You fit logistic regression with gradient descent and learning rate $0.01$. The loss oscillates wildly. Diagnose. Fix.

11. **Newton's method update.** Write out the IRLS Newton update for logistic regression in matrix form. What is the diagonal matrix $D$?

12. **Calibration check.** A logistic regression predicts probability 0.8 for 1000 emails. Of those 1000, 750 turn out to be spam. Is the model calibrated at this probability level? What does well-calibrated mean here?

<details>
<summary>Answers</summary>

1. $\sigma(z) = (1+e^{-z})^{-1}$. By the chain rule, $\sigma'(z) = -1 \cdot (1+e^{-z})^{-2} \cdot (-e^{-z}) = e^{-z}/(1+e^{-z})^2$. Factor as $\frac{1}{1+e^{-z}} \cdot \frac{e^{-z}}{1+e^{-z}} = \sigma(z) \cdot (1 - \sigma(z))$.

2. Negative weight: more years at current job *decreases* the log-odds of default. Each additional year multiplies the odds by $e^{-0.5} \approx 0.607$, i.e., reduces odds by about 39%.

3. The gradient of squared error w.r.t. $w$ involves a factor of $\sigma'(z) = p(1-p)$ that the cross-entropy gradient doesn't. When $p$ is near 0 or 1, $p(1-p) \approx 0$, so the gradient *vanishes* even when the prediction is very wrong. Optimization stalls. Cross-entropy doesn't have this — its gradient is $(p - y) x$, which is large precisely when the prediction is wrong.

4. Likelihood: $0.8 \cdot (1 - 0.3) \cdot 0.6 = 0.8 \cdot 0.7 \cdot 0.6 = 0.336$. Log-likelihood: $\log 0.8 + \log 0.7 + \log 0.6 \approx -0.223 - 0.357 - 0.511 = -1.091$. Cross-entropy: $+1.091$.

5. Boundary: $2 x_1 - 3 x_2 - 1 = 0$, i.e., $x_2 = (2x_1 - 1)/3$. A line with slope 2/3 and intercept $-1/3$.

6. At $\tau = 0.7$, $\log(\tau/(1-\tau)) = \log(0.7/0.3) = \log(7/3) \approx 0.847$. Boundary: $2x_1 - 3x_2 - 1 = 0.847$, i.e., $x_2 = (2x_1 - 1.847)/3$. Same slope, shifted parallel.

7. With $w = 0$, all $p_i = 0.5$. Errors: $-0.5, 0.5, -0.5$. Gradient (components for bias, $w_1$, $w_2$): bias = $-0.5 + 0.5 - 0.5 = -0.5$; $w_1 = -0.5 \cdot 1 + 0.5 \cdot 0 - 0.5 \cdot 1 = -1$; $w_2 = -0.5 \cdot 0 + 0.5 \cdot 1 - 0.5 \cdot 1 = 0$. Update: $w \leftarrow (0,0,0) - 0.1 \cdot (-0.5, -1, 0) = (0.05, 0.1, 0)$.

8. With perfect separation, any $w$ that achieves zero error can be scaled by 10× and the cross-entropy loss decreases (because predictions get more confident). The optimizer keeps scaling up. Prevention: (a) add L2 (or L1) regularization, which penalizes large $\|w\|$; (b) early stopping at a max iteration count.

9. Numerators: $e^2 = 7.389$, $e^0 = 1$, $e^{-1} = 0.368$. Sum: $8.757$. Probabilities: $(7.389/8.757, 1/8.757, 0.368/8.757) = (0.844, 0.114, 0.042)$. Predicted class: 1 (the first, with probability 0.844).

10. The gradient for $x_1$ is roughly $10^6$ times bigger than for $x_2$. With $\eta = 0.01$, the $w_1$ update overshoots wildly while $w_2$ barely moves. Fix: standardize features with `StandardScaler` before fitting.

11. $w \leftarrow w - (X^\top D X)^{-1} X^\top (p - y)$ where $D$ is diagonal with $D_{ii} = p_i (1 - p_i)$. Each iteration is a weighted-least-squares problem.

12. Yes — out of 1000 predictions at 0.8, you'd *expect* about $1000 \cdot 0.8 = 800$ to be positive. Observed: 750. That's reasonably close (within sampling noise). Well-calibrated means: among examples with predicted probability $p$, the fraction that are actually positive is also $p$. For a deeper test, you'd plot a reliability diagram across multiple probability buckets.

</details>
