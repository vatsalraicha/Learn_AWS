# Chapter 31 — Linear Regression — From OLS Derivation

> **Goal of this chapter:** to build linear regression from the ground up — every formula, every assumption, every failure mode. Linear regression is the simplest possible ML model that isn't a constant. Understanding it deeply lets you understand a huge fraction of what's actually deployed in industry. The decision tree of "which model do I use?" still, in 2026, very often terminates at "a linear model with the right features." When somebody on your team reaches for XGBoost on a problem that wanted ridge regression, you should be able to feel it.

---

## 31.1 Why this is the right place to start

In Chapter 1 we fit a line by eye to five house prices. In Chapter 16 we wrote down the squared-error loss as a function of $(w, b)$ and gestured at "find the minimum". In Chapter 17 we derived gradient descent for arbitrary differentiable losses. In Chapter 20 we put L2 regularization onto a generic loss without committing to a specific model.

All four of those chapters were leading here. Linear regression is the single problem where every piece of that machinery — the loss function, the optimization, the regularization, the bias-variance tradeoff — admits a closed-form solution. You can solve it on the back of a napkin. The closed form lets you *check* what the algorithm is doing; the open-ended iterative versions of the same math are how almost every other model in this book is fit.

It is also, in many real industries — actuarial pricing, econometrics, clinical trials, ad-bid pricing — *still the dominant model in production*. Not because nobody knows about random forests, but because the interpretability of linear regression (every coefficient is a real number with a meaning, and the model's behaviour is easy to audit) is worth more than two points of held-out accuracy. The Capital One model risk management group, for instance, has a strong default toward generalized linear models for exactly this reason.

So we start here, and we go slowly.

---

## 31.2 The setup, with the bias absorbed

We have $n$ training examples. Each example is a pair $(x_i, y_i)$ where $x_i \in \mathbb{R}^d$ is a $d$-dimensional feature vector and $y_i \in \mathbb{R}$ is a continuous target. Stack the examples into a matrix and a vector:

$$
X = \begin{bmatrix} x_1^\top \\ x_2^\top \\ \vdots \\ x_n^\top \end{bmatrix} \in \mathbb{R}^{n \times d},
\quad
y = \begin{bmatrix} y_1 \\ y_2 \\ \vdots \\ y_n \end{bmatrix} \in \mathbb{R}^n
$$

$X$ is the **design matrix**. Each row is one training example; each column is one feature.

The model class is **linear functions of $x$**:

$$
\hat{y}(x) = w_1 x_{(1)} + w_2 x_{(2)} + \cdots + w_d x_{(d)} + b = w^\top x + b
$$

Notation note: $x_{(j)}$ is the $j$-th coordinate of a single example $x$. I'll drop the parenthesised subscript when it's unambiguous.

Carrying the intercept $b$ around as a separate variable is annoying. The standard trick is to *absorb* $b$ into $w$ by appending a constant 1 to every $x$. Define an augmented feature vector $\tilde{x}_i = (1, x_{i,1}, \ldots, x_{i,d}) \in \mathbb{R}^{d+1}$ and an augmented weight vector $\tilde{w} = (b, w_1, \ldots, w_d)$. Then

$$
\tilde{w}^\top \tilde{x}_i = b \cdot 1 + w_1 x_{i,1} + \cdots + w_d x_{i,d} = w^\top x_i + b
$$

— exactly what we wanted. From here on I'll drop the tildes and just say $w \in \mathbb{R}^{d+1}$ and $X \in \mathbb{R}^{n \times (d+1)}$ where the first column of $X$ is all ones. The bias is now just the first coordinate of $w$.

With this convention, predicting all $n$ examples at once is a single matrix-vector product:

$$
\hat{y} = X w \in \mathbb{R}^n
$$

That's the whole forward pass of linear regression: one matrix multiplication.

---

## 31.3 The loss function — why squared error

We need to measure how badly $\hat{y}$ differs from $y$. The standard choice is the **sum of squared errors**:

$$
L(w) = \sum_{i=1}^n (y_i - w^\top x_i)^2 = \| y - Xw \|^2
$$

(The two expressions are identical — the second is the vector norm.)

Why squared error? Three answers, of increasing depth.

**Answer 1 (geometric).** $Xw$ is a vector in $\mathbb{R}^n$, and so is $y$. Squared error is the squared Euclidean distance between them. Minimising it finds the prediction vector closest to the target vector in the standard geometry. This is the answer most people remember.

**Answer 2 (statistical).** If we assume $y_i = w^\top x_i + \epsilon_i$ where each $\epsilon_i$ is independent and normally distributed with mean 0 and variance $\sigma^2$, then the likelihood of the training data given $w$ is

$$
\prod_{i=1}^n \frac{1}{\sqrt{2\pi\sigma^2}} \exp\!\left( -\frac{(y_i - w^\top x_i)^2}{2\sigma^2} \right)
$$

Taking the log and dropping constants, maximising the log-likelihood is equivalent to *minimising* $\sum (y_i - w^\top x_i)^2$. So squared error is the **maximum likelihood estimator** under Gaussian noise. We met this idea in Chapter 16; we will meet it again, in a different form, in Chapter 32 for logistic regression.

**Answer 3 (computational).** $L(w)$ is a **quadratic** function of $w$. Quadratics in many variables have a unique global minimum (if the underlying matrix is positive definite) and the minimum is found by setting the gradient to zero — a *linear* system. So we can solve linear regression in closed form. No other model in this book has this property.

All three answers point at the same choice. We're using squared error.

There are other reasonable losses. **Mean absolute error** $\sum |y_i - w^\top x_i|$ is the MLE under *Laplace* noise, is robust to outliers, but has no closed-form solution and isn't differentiable at zero. **Huber loss** interpolates — squared error near zero, absolute error far from zero — robust to outliers, smooth, but iterative. Squared error is the default for reasons that have at this point been baked into half a century of statistics curricula.

---

## 31.4 The normal equations — full derivation

We want to minimise $L(w) = \| y - Xw \|^2$ as a function of $w \in \mathbb{R}^{d+1}$. The standard route: compute $\nabla_w L$, set it to zero, solve for $w$. Every step visible.

**Step 1: expand the norm.**

$$
L(w) = (y - Xw)^\top (y - Xw)
$$

Use the distributive property of the transpose: $(A - B)^\top = A^\top - B^\top$.

$$
= (y^\top - w^\top X^\top)(y - Xw)
$$

Multiply out the four terms:

$$
= y^\top y - y^\top X w - w^\top X^\top y + w^\top X^\top X w
$$

**Step 2: combine the middle two terms.** Both $y^\top X w$ and $w^\top X^\top y$ are scalars (1×1 matrices), and a scalar equals its own transpose. Notice $(y^\top X w)^\top = w^\top X^\top y$. So $y^\top X w = w^\top X^\top y$, and the middle becomes $-2 w^\top X^\top y$:

$$
L(w) = y^\top y - 2 w^\top X^\top y + w^\top X^\top X w
$$

**Step 3: differentiate with respect to $w$.** Three vector-calculus identities, all derivable in 5 lines but I'll just state them (we covered them in Chapter 15):

- $\nabla_w (y^\top y) = 0$ (no $w$).
- $\nabla_w (w^\top a) = a$ for a constant vector $a$.
- $\nabla_w (w^\top A w) = 2 A w$ when $A$ is symmetric.

Note that $X^\top X$ is symmetric: $(X^\top X)^\top = X^\top X$. So:

$$
\nabla_w L = 0 - 2 X^\top y + 2 X^\top X w
$$

**Step 4: set to zero.** A minimum (or saddle, or max — we'll check second-order conditions in a moment) must satisfy

$$
-2 X^\top y + 2 X^\top X w = 0
$$

Dividing by 2 and moving the $y$ term:

$$
\boxed{X^\top X \, w = X^\top y}
$$

These are the **normal equations**. They are $d+1$ linear equations in $d+1$ unknowns. They are the heart of linear regression.

**Step 5: solve.** If $X^\top X$ is invertible (we'll discuss when in a moment), multiply both sides by $(X^\top X)^{-1}$:

$$
\boxed{\hat{w} = (X^\top X)^{-1} X^\top y}
$$

That is the **ordinary least squares (OLS)** estimator. One line. No iteration. The optimal weight vector for the training set is, exactly, this matrix expression.

**Step 6: confirm it's a minimum.** The Hessian of $L$ is $\nabla^2_w L = 2 X^\top X$. For any nonzero vector $v$, $v^\top X^\top X v = \|Xv\|^2 \geq 0$, so the Hessian is positive semi-definite — $L$ is convex. If $X^\top X$ is *strictly* positive definite (full rank), $L$ is strictly convex and the critical point is the unique global minimum. Otherwise the minimum is a flat subspace and any point in it is equally optimal.

---

## 31.5 When can we actually solve the normal equations?

The closed form $\hat{w} = (X^\top X)^{-1} X^\top y$ assumes $X^\top X$ is invertible. When isn't it?

$X^\top X$ is a $(d+1) \times (d+1)$ matrix. It is invertible iff it has **full rank**, which happens iff $X$ has full column rank — iff its columns (the features, including the constant column for the bias) are linearly independent.

Linear dependence among columns is called **multicollinearity**. Concretely it happens when:

- Two features are exact duplicates (e.g., "height_in_inches" and "height_in_inches_copy").
- One feature is a linear combination of others (e.g., you one-hot-encoded a categorical and didn't drop the redundant level — the "dummy variable trap").
- You have more features than examples ($d \geq n$). Then $X$ is "wide" and $X^\top X$ is automatically rank-deficient.

In all these cases the normal equations have *infinitely many* solutions — any direction in the null space of $X$ can be added to a valid $w$ without changing $Xw$.

### 31.5.1 The pseudo-inverse fix

When $X^\top X$ is singular, you can still get *a* solution by using the **Moore-Penrose pseudo-inverse**:

$$
\hat{w} = X^+ y
$$

where $X^+$ is computed from the singular value decomposition (SVD) of $X$. We covered SVD lightly in Chapter 13; here the relevant fact is that $X^+$ exists for any matrix, and the resulting $\hat{w}$ is the *minimum-norm* solution among all least-squares solutions. `numpy.linalg.lstsq` and `scipy.linalg.lstsq` use SVD under the hood and return $\hat{w} = X^+ y$ regardless of rank.

### 31.5.2 The regularization fix

Add a small ridge penalty (more on this in §31.10):

$$
\hat{w} = (X^\top X + \lambda I)^{-1} X^\top y
$$

For any $\lambda > 0$, $X^\top X + \lambda I$ is *guaranteed* invertible, because adding a positive multiple of the identity shifts all eigenvalues up by $\lambda$ (and the eigenvalues of $X^\top X$ are already non-negative). This is one reason ridge regression is so beloved by practitioners: it kills the singularity problem dead, no questions asked.

### 31.5.3 The "drop a feature" fix

If two columns are exactly proportional, drop one. If you one-hot-encoded a $k$-level categorical and have $k$ dummies, drop one. This is the same trick the `drop_first=True` flag does in `pandas.get_dummies`. It restores full rank by hand.

---

## 31.6 When the closed form is impractical

The normal equations require computing $X^\top X$ ($O(n d^2)$) and inverting it ($O(d^3)$). For $d = 100$ this is nothing. For $d = 10{,}000$ — TF-IDF on a moderate vocabulary, say — $d^3 = 10^{12}$ operations, which is at the edge of comfortable.

For very wide problems ($d$ in the hundreds of thousands or more — image features, text embeddings, genomics), people use **gradient descent** or its many cousins. We derived gradient descent generally in Chapter 17; for linear regression specifically, the update is

$$
w \leftarrow w - \eta \nabla_w L(w) = w - \eta \cdot 2 X^\top (Xw - y)
$$

Per iteration: one matrix-vector product to get $Xw$ ($O(nd)$), one subtraction, one matrix-vector product against $X^\top$ ($O(nd)$). Total $O(nd)$ per iteration, vs. $O(nd^2 + d^3)$ once for the closed form. For wide $d$, iterative wins.

For *very large* $n$ (billions of rows), even one pass over the data is expensive. **Stochastic gradient descent** processes one example (or a mini-batch) at a time. Spark MLlib's `LinearRegression` uses an iterative solver (L-BFGS or OWLQN) for exactly this reason — it can't materialize $X^\top X$ when $X$ is distributed across hundreds of executors.

The right cognitive model: the closed form is the *definition* of what linear regression is fitting; iterative algorithms are how you actually compute it at scale. They converge to the same answer (in the well-conditioned case).

---

## 31.7 The Gauss-Markov assumptions

Linear regression is a *statistical* model, not just an optimization problem. To say anything about how good $\hat{w}$ is — its bias, its variance, its sampling distribution — we have to make assumptions about how the data was generated. The classical assumptions, due to Gauss and Markov, are:

**A1. Linearity.** $y_i = w^{*\top} x_i + \epsilon_i$ for some true $w^*$. The relationship between $x$ and $y$ is linear in $w$. ("Linear in $w$", not "linear in $x$" — you can do polynomial regression and it's still linear regression on the polynomial features.)

**A2. Errors have zero mean.** $\mathbb{E}[\epsilon_i] = 0$ for all $i$. Equivalently, the model isn't systematically over- or under-predicting.

**A3. Homoscedasticity.** $\text{Var}(\epsilon_i) = \sigma^2$ for all $i$ — every example has the same noise variance. The "skedastic" part comes from Greek $\sigma\kappa\epsilon\delta\acute{\alpha}\nu\nu\upsilon\mu\iota$, "to scatter." Homo-skedastic = same scatter.

**A4. Uncorrelated errors.** $\text{Cov}(\epsilon_i, \epsilon_j) = 0$ for $i \neq j$. Errors on different examples are independent.

**A5. No perfect multicollinearity.** $X$ has full column rank. (We discussed this in §31.5.)

If these hold, the **Gauss-Markov theorem** says the OLS estimator $\hat{w}$ is **BLUE** — the Best Linear Unbiased Estimator. "Best" means lowest variance among linear unbiased estimators of $w^*$. This is a remarkable result: of all the ways you could imagine combining the data into an estimator of $w^*$, OLS gives the smallest sampling variance, provided you stick to linear and unbiased.

If we *additionally* assume:

**A6. Normality.** $\epsilon_i \sim \mathcal{N}(0, \sigma^2)$, independently.

Then OLS is also the **maximum likelihood estimator** (we derived this in §31.3) and the sampling distribution of $\hat{w}$ is *exactly* Normal. This is what underlies all the standard errors, confidence intervals, and p-values you see in `statsmodels`' linear regression output.

---

## 31.8 What if the assumptions fail?

This is where the working knowledge lives. Each failure has a well-known fix.

**Linearity fails (A1)**: residuals plotted against predicted values show a curve (a U-shape, an inverted U, an S-curve). The relationship isn't linear in the features. Fixes: add polynomial features (Chapter 28), add interaction terms, log-transform $x$ or $y$, switch to a non-linear model (trees, GBT — Chapters 33, 36).

**Heteroscedasticity (A3 fails)**: residuals plotted against predicted values show a funnel — error variance grows with predicted value. Common when $y$ has natural multiplicative structure (income, prices, durations). Fixes: log-transform $y$ to stabilize variance; use **weighted least squares** with weights $w_i = 1/\sigma_i^2$ if you can estimate per-example variances; use a **generalized linear model** with the appropriate variance function (Gamma for positive continuous, Poisson for counts).

**Autocorrelated errors (A4 fails)**: typically a time-series sign. The Durbin-Watson statistic catches first-order autocorrelation. Fixes: explicitly model the time structure (AR, ARIMA), include lagged variables as features, use cluster-robust standard errors if it's panel data.

**Non-normal errors (A6 fails)**: residual histogram has heavy tails or skew. OLS is still BLUE under A1-A5, but confidence intervals computed assuming normality are off. Fixes: **robust regression** (Huber, RANSAC) to downweight outliers; bootstrap confidence intervals; quantile regression if you care about specific quantiles.

**Multicollinearity (A5 fails)**: $X^\top X$ near-singular, coefficient estimates have huge variance, signs flip across samples. Fixes: drop redundant features, use **ridge regression** (§31.10), use **PCA** (Chapter 40) to project onto orthogonal directions.

These diagnostics — residual plots, Q-Q plots, leverage, Cook's distance — are the bread and butter of applied linear regression in industries where the model has to be defended in a regulatory submission. They are also the reason `statsmodels.OLS` exists as a separate library from scikit-learn: scikit-learn is built for prediction; statsmodels is built for inference, and it gives you all of these diagnostics by default.

---

## 31.9 A worked numerical example — 5 points, by hand

Let's actually compute $\hat{w} = (X^\top X)^{-1} X^\top y$ for the 5-point house example from Chapter 1.

| $i$ | $x_i$ (sq ft) | $y_i$ (price, $k) |
|----:|--------------:|------------------:|
| 1 |   800 | 200 |
| 2 | 1,200 | 280 |
| 3 | 1,500 | 340 |
| 4 | 1,800 | 410 |
| 5 | 2,300 | 510 |

With bias absorbed, $X$ is $5 \times 2$ (one column of 1s, one column of sq ft):

$$
X = \begin{bmatrix} 1 & 800 \\ 1 & 1200 \\ 1 & 1500 \\ 1 & 1800 \\ 1 & 2300 \end{bmatrix},
\quad
y = \begin{bmatrix} 200 \\ 280 \\ 340 \\ 410 \\ 510 \end{bmatrix}
$$

**Compute $X^\top X$:**

$$
X^\top X = \begin{bmatrix} 1 & 1 & 1 & 1 & 1 \\ 800 & 1200 & 1500 & 1800 & 2300 \end{bmatrix}
\begin{bmatrix} 1 & 800 \\ 1 & 1200 \\ 1 & 1500 \\ 1 & 1800 \\ 1 & 2300 \end{bmatrix}
$$

Top-left: $1+1+1+1+1 = 5$.
Top-right: $800 + 1200 + 1500 + 1800 + 2300 = 7600$.
Bottom-left: same as top-right by symmetry, $7600$.
Bottom-right: $800^2 + 1200^2 + 1500^2 + 1800^2 + 2300^2 = 640{,}000 + 1{,}440{,}000 + 2{,}250{,}000 + 3{,}240{,}000 + 5{,}290{,}000 = 12{,}860{,}000$.

$$
X^\top X = \begin{bmatrix} 5 & 7600 \\ 7600 & 12{,}860{,}000 \end{bmatrix}
$$

**Compute $X^\top y$:**

Top: $200 + 280 + 340 + 410 + 510 = 1740$.
Bottom: $800 \cdot 200 + 1200 \cdot 280 + 1500 \cdot 340 + 1800 \cdot 410 + 2300 \cdot 510$
$= 160{,}000 + 336{,}000 + 510{,}000 + 738{,}000 + 1{,}173{,}000 = 2{,}917{,}000$.

$$
X^\top y = \begin{bmatrix} 1740 \\ 2{,}917{,}000 \end{bmatrix}
$$

**Invert $X^\top X$:** for a $2 \times 2$ matrix $\begin{pmatrix} a & b \\ c & d \end{pmatrix}$, the inverse is $\frac{1}{ad-bc} \begin{pmatrix} d & -b \\ -c & a \end{pmatrix}$.

Determinant: $5 \cdot 12{,}860{,}000 - 7600 \cdot 7600 = 64{,}300{,}000 - 57{,}760{,}000 = 6{,}540{,}000$.

$$
(X^\top X)^{-1} = \frac{1}{6{,}540{,}000} \begin{bmatrix} 12{,}860{,}000 & -7600 \\ -7600 & 5 \end{bmatrix}
$$

**Multiply:** $\hat{w} = (X^\top X)^{-1} X^\top y$. The bias coordinate is:

$$
\hat{b} = \frac{1}{6{,}540{,}000} (12{,}860{,}000 \cdot 1740 - 7600 \cdot 2{,}917{,}000)
$$

Compute: $12{,}860{,}000 \cdot 1740 = 22{,}376{,}400{,}000$. And $7600 \cdot 2{,}917{,}000 = 22{,}169{,}200{,}000$. Difference: $207{,}200{,}000$. Divide by $6{,}540{,}000$: $\hat{b} \approx 31.68$.

Slope:

$$
\hat{w}_1 = \frac{1}{6{,}540{,}000} (-7600 \cdot 1740 + 5 \cdot 2{,}917{,}000)
$$

$-7600 \cdot 1740 = -13{,}224{,}000$. $5 \cdot 2{,}917{,}000 = 14{,}585{,}000$. Sum: $1{,}361{,}000$. Divide by $6{,}540{,}000$: $\hat{w}_1 \approx 0.2081$.

So $\hat{y} = 0.2081 \cdot x + 31.68$. Compare to our Chapter 1 eyeball line $0.207 x + 34.4$ — the OLS solution is *very* close to what we drew by eye. That's encouraging: for a clean nearly-linear dataset, intuition and the formal procedure agree.

Predicting at 1,650 sq ft: $0.2081 \cdot 1650 + 31.68 = 343.4 + 31.68 = 375.1$ thousand. Almost identical to the Chapter 1 prediction of $375.95.

The point of doing this by hand is not to enjoy arithmetic. It is to internalize that nothing magical is happening — the OLS formula is exactly the operation we just did, and it scales identically to $d = 50$ features with $n = 100{,}000$ rows, just with bigger matrices.

---

## 31.10 Ridge regression — regularization in closed form

We met ridge regression in Chapter 20 in the abstract. Let's see what it does to linear regression specifically. The ridge objective is

$$
L_{\text{ridge}}(w) = \| y - Xw \|^2 + \lambda \| w \|^2
$$

The penalty $\lambda \|w\|^2 = \lambda \sum w_j^2$ discourages large weights. $\lambda \geq 0$ is the regularization strength.

Derive the closed form. Same approach: gradient to zero.

$$
\nabla_w L_{\text{ridge}} = -2 X^\top y + 2 X^\top X w + 2 \lambda w = 0
$$

$$
(X^\top X + \lambda I) w = X^\top y
$$

$$
\boxed{\hat{w}_{\text{ridge}} = (X^\top X + \lambda I)^{-1} X^\top y}
$$

The *only* change from OLS is the $\lambda I$ added inside the inverse.

What does $\lambda$ do? Three angles.

**Eigenvalue angle.** Suppose $X^\top X$ has eigenvalues $\sigma_1^2 \geq \sigma_2^2 \geq \cdots \geq \sigma_{d+1}^2 \geq 0$. Then $X^\top X + \lambda I$ has eigenvalues $\sigma_j^2 + \lambda$. The small eigenvalues — the directions in which $X^\top X$ is nearly singular — get shifted up the most, *in relative terms*. This is exactly the directions where unregularized OLS would have huge variance. Ridge tames them.

**Shrinkage angle.** Decompose along the eigendirections: ridge shrinks each component of $\hat{w}$ by a factor $\frac{\sigma_j^2}{\sigma_j^2 + \lambda}$. Components with large $\sigma_j^2$ (well-supported directions) are barely shrunk; components with small $\sigma_j^2$ (poorly-supported directions) are shrunk a lot. The "blob in feature space" picture from Chapter 20 made this geometric.

**Bayesian angle.** Ridge is the maximum a posteriori (MAP) estimate under a Gaussian prior $w \sim \mathcal{N}(0, \tau^2 I)$. Specifically, $\lambda = \sigma^2 / \tau^2$. Larger prior variance $\tau^2$ → smaller $\lambda$ → weaker regularization. We won't lean on this view, but it's worth knowing.

### 31.10.1 Choosing $\lambda$

$\lambda$ is a hyperparameter. The principled way to set it is by cross-validation (Chapter 22): try a grid of values (often $\lambda = 10^{-4}, 10^{-3}, \ldots, 10^{3}$ on a log scale), fit ridge for each, evaluate on held-out folds, pick the $\lambda$ with lowest CV error. `sklearn.linear_model.RidgeCV` does this automatically with efficient leave-one-out.

### 31.10.2 Scaling matters

Ridge penalizes $\sum w_j^2$. If feature 1 is "square footage" (range 800-2300) and feature 2 is "number of bedrooms" (range 1-5), the weight on bedrooms will naturally be much larger in magnitude to compensate for the smaller range. The ridge penalty will then disproportionately shrink the bedroom weight. The fix: **standardize features before applying ridge** (Chapter 26). This is so important that `Ridge` and `RidgeCV` in sklearn have `normalize` parameters (deprecated; use a `StandardScaler` in a pipeline).

OLS, by contrast, is invariant to feature scaling — you can multiply any feature's column by a constant and the predictions are identical, the weight just absorbs the inverse. Ridge is *not* scale-invariant because the penalty is not scale-invariant.

### 31.10.3 Lasso and ElasticNet

L1 regularization (lasso) replaces $\lambda \|w\|^2$ with $\lambda \|w\|_1 = \lambda \sum |w_j|$. The penalty term is *not differentiable* at $w_j = 0$, so there's no clean closed form. The fit is iterative (coordinate descent, LARS). The reward: lasso drives some coefficients to *exactly* zero, performing implicit feature selection. We covered this geometrically in Chapter 20 (the $\ell_1$-ball has corners; the optimal point sits on a corner where some coordinates are zero).

ElasticNet mixes both: $\lambda_1 \|w\|_1 + \lambda_2 \|w\|^2$. Useful when you have many correlated features — lasso alone tends to arbitrarily pick one and zero the others; the ridge component spreads weight across correlated groups.

---

## 31.11 Residual analysis — the diagnostic step

We've fit the model. How do we know it's any good — beyond the headline R² number?

The single most informative diagnostic in linear regression is the **residual plot**: plot residuals $r_i = y_i - \hat{y}_i$ against fitted values $\hat{y}_i$ (or against each feature, or against time, or against any structural variable).

What you want to see: a featureless cloud of points, evenly scattered around zero, with no visible pattern. That's the picture of "the model has captured the signal and what's left is noise."

What you might see instead, and what each pattern means:

**A trend (line) in the residuals.** The residuals systematically increase or decrease with $\hat{y}$. Diagnosis: you have an unfitted linear pattern — usually a feature you forgot or a coding bug.

**A U-shape or arc.** Diagnosis: the true relationship is non-linear. Add polynomial features, log-transform, or switch model class.

**A funnel — variance grows with $\hat{y}$.** Diagnosis: heteroscedasticity. Log-transform $y$ or use weighted least squares.

**Bands at the top and bottom — most residuals near zero, a few large positives and large negatives.** Diagnosis: heavy-tailed noise. Robust regression.

**Clusters or stripes.** Diagnosis: a categorical structure you didn't encode. Add the missing feature.

**A few extreme points far from the rest.** Outliers or high-leverage points. Investigate them — sometimes they're errors, sometimes they're the most important observations in the data.

The Q-Q plot (quantiles of residuals against theoretical Normal quantiles) catches non-normality. The scale-location plot catches heteroscedasticity. Cook's distance and leverage measure individual observations' influence. These are the four panels you get from R's `plot(lm.fit)` and from `statsmodels` post-fit diagnostics. Memorize their patterns.

---

## 31.12 Code: NumPy from scratch, then scikit-learn

The pedagogical point of this chapter is the math. The code is a victory lap.

### 31.12.1 NumPy normal equations from scratch

```python
import numpy as np

# Synthetic data: y = 2x + 1 + small noise
rng = np.random.default_rng(0)
n = 100
x = rng.uniform(0, 10, n)
y = 2 * x + 1 + rng.normal(0, 0.5, n)

# Build design matrix with bias column
X = np.column_stack([np.ones(n), x])  # shape (n, 2)

# Normal equations: w_hat = (X.T @ X)^-1 @ X.T @ y
w_hat = np.linalg.solve(X.T @ X, X.T @ y)
# Note: use linalg.solve (Cholesky/LU) rather than explicit inverse.
# It's numerically more stable and faster.

print(f"intercept (b): {w_hat[0]:.3f}")
print(f"slope (w):     {w_hat[1]:.3f}")
# intercept (b): 1.012, slope (w): 1.998 — close to truth
```

The `np.linalg.solve` call is the right way to compute $(X^\top X)^{-1} X^\top y$ in practice. Forming the explicit inverse with `np.linalg.inv` is slower and less numerically stable. For rank-deficient $X$, use `np.linalg.lstsq`, which goes through SVD.

### 31.12.2 Ridge from scratch

```python
def fit_ridge(X, y, lam):
    d = X.shape[1]
    return np.linalg.solve(X.T @ X + lam * np.eye(d), X.T @ y)

w_ridge = fit_ridge(X, y, lam=1.0)
```

One added line.

### 31.12.3 scikit-learn

```python
from sklearn.linear_model import LinearRegression, Ridge, RidgeCV

# OLS
ols = LinearRegression().fit(x.reshape(-1, 1), y)
print(ols.intercept_, ols.coef_)  # (1.012, [1.998])

# Ridge with explicit lambda
ridge = Ridge(alpha=1.0).fit(x.reshape(-1, 1), y)

# Ridge with CV-chosen lambda
ridge_cv = RidgeCV(alphas=np.logspace(-3, 3, 7)).fit(x.reshape(-1, 1), y)
print(f"chosen alpha: {ridge_cv.alpha_}")
```

`LinearRegression` uses SVD internally and handles rank-deficiency. `Ridge` solves the regularized normal equations. `RidgeCV` does leave-one-out CV efficiently using a closed-form trick (the *hat matrix* trace identity — beautiful linear algebra, beyond scope here).

### 31.12.4 PySpark MLlib preview

Spark's `LinearRegression` in `pyspark.ml.regression` uses iterative L-BFGS or normal equations under the hood, controlled by a `solver` parameter. For small enough $d$ (Spark's threshold is around 4096 features) it uses normal equations; otherwise L-BFGS. We will dig into the Spark API in Chapter 65; for now, the API shape is:

```python
from pyspark.ml.regression import LinearRegression as SparkLR

lr = SparkLR(featuresCol="features", labelCol="price",
             regParam=0.1, elasticNetParam=0.0)  # regParam = lambda
model = lr.fit(train_df)
predictions = model.transform(test_df)
```

`elasticNetParam=0.0` means pure L2 (ridge); `=1.0` means pure L1 (lasso); intermediate values mix. This is the ElasticNet parameterization.

---

## 31.13 What this builds on / where this returns

**Builds on:**

- Chapter 13 — matrix inverse and the algebra of $X^\top X$.
- Chapter 15 — gradients of quadratic forms.
- Chapter 16 — the squared-error loss.
- Chapter 17 — gradient descent (as the iterative alternative).
- Chapter 19 — the bias-variance picture of why regularization helps.
- Chapter 20 — L2 / L1 / ElasticNet regularization in general form.

**Returns:**

- Chapter 32 — logistic regression reuses the design-matrix machinery and the regularization story.
- Chapter 65 — `pyspark.ml.regression.LinearRegression` is the Spark version of what we just derived.
- Part L — when we get to MLflow tracking and model registry, linear models are the canonical "well-behaved baseline" we register first.

---

## 31.14 Exercises

1. **The normal equations from scratch.** Without looking back, derive $\hat{w} = (X^\top X)^{-1} X^\top y$ starting from $L(w) = \|y - Xw\|^2$. Show every step.

2. **A 2-point fit.** You have data $(x_1, y_1) = (1, 3)$ and $(x_2, y_2) = (3, 7)$. Build $X$ with a bias column. Compute $X^\top X$, $X^\top y$, $(X^\top X)^{-1}$, and $\hat{w}$. Verify the line passes through both points.

3. **The 3-point overdetermined case.** Data: $(1, 2), (2, 5), (3, 7)$. There is no line through all three. Compute the OLS line. What is the residual at each point? Are the residuals symmetric (do they sum to zero)? Why?

4. **Bias absorption in code.** Given a matrix `X` of shape $(n, d)$ and a vector `y`, write 3 lines of NumPy that produce $\hat{w}$ with the bias as the first entry of $\hat{w}$.

5. **What makes $X^\top X$ singular?** Give three concrete reasons. For each, propose a fix.

6. **The lstsq function.** What does `numpy.linalg.lstsq(X, y)` return when $X$ has more columns than rows? Why is that the *right* answer?

7. **Ridge eigenvalues.** $X^\top X$ has eigenvalues 100, 4, and 0.01. Compute the shrinkage factor $\sigma_j^2 / (\sigma_j^2 + \lambda)$ for each, at $\lambda = 1$. Which direction is shrunk the most? Why is that desirable?

8. **Residual diagnostics.** A colleague shows you a scatter plot of residuals vs. fitted values that has a clear U-shape. What does this mean? What are two things you might try?

9. **Why standardize before ridge.** Feature A has standard deviation 100; feature B has standard deviation 1. Without standardization, which feature does ridge regularization affect more? Why? What changes after standardization?

10. **Closed form vs. gradient descent.** For what dataset shape (large $n$ vs. large $d$) would you reach for gradient descent over the closed form? Give a rough rule of thumb in terms of $n$ and $d$.

11. **MLE under Laplace noise.** Suppose $\epsilon_i \sim \text{Laplace}(0, b)$ (heavy-tailed compared to Normal). Derive the MLE estimator. (Hint: the Laplace PDF involves $|x|$.) What is its closed form?

12. **R² from first principles.** R² is defined as $1 - \text{SS}_{\text{res}} / \text{SS}_{\text{tot}}$ where $\text{SS}_{\text{res}} = \sum (y_i - \hat{y}_i)^2$ and $\text{SS}_{\text{tot}} = \sum (y_i - \bar{y})^2$. What does $R^2 = 0$ mean? What does $R^2 = 1$ mean? Can $R^2$ be negative? When?

<details>
<summary>Answers</summary>

1. See §31.4.

2. $X = \begin{pmatrix} 1 & 1 \\ 1 & 3 \end{pmatrix}$, $y = \begin{pmatrix} 3 \\ 7 \end{pmatrix}$. $X^\top X = \begin{pmatrix} 2 & 4 \\ 4 & 10 \end{pmatrix}$, det = 20 - 16 = 4. $(X^\top X)^{-1} = \frac{1}{4} \begin{pmatrix} 10 & -4 \\ -4 & 2 \end{pmatrix}$. $X^\top y = \begin{pmatrix} 10 \\ 24 \end{pmatrix}$. $\hat{w} = \frac{1}{4}(100 - 96, -40 + 48) = (1, 2)$. Line: $\hat{y} = 1 + 2x$. Check: at $x=1$, $\hat{y}=3$ ✓; at $x=3$, $\hat{y}=7$ ✓.

3. $X = \begin{pmatrix} 1 & 1 \\ 1 & 2 \\ 1 & 3 \end{pmatrix}$, $y = (2,5,7)^\top$. $X^\top X = \begin{pmatrix} 3 & 6 \\ 6 & 14 \end{pmatrix}$, det = 6. $X^\top y = (14, 32)^\top$. $\hat{w} = \frac{1}{6}(14 \cdot 14 - 6 \cdot 32, -6 \cdot 14 + 3 \cdot 32) = \frac{1}{6}(196-192, -84+96) = \frac{1}{6}(4, 12) = (2/3, 2)$. Line: $\hat{y} = 2/3 + 2x$. Predictions: 2.67, 4.67, 6.67. Residuals: $-0.67, 0.33, 0.33$. Sum = $-0.01 \approx 0$ (rounding). Residuals always sum to zero with an intercept term — that's a consequence of the first normal equation $\sum r_i = 0$.

4. ```python
   X_aug = np.column_stack([np.ones(len(X)), X])
   w_hat = np.linalg.solve(X_aug.T @ X_aug, X_aug.T @ y)
   ```

5. (a) Duplicate columns — drop one. (b) One column is a sum of others (dummy variable trap with all $k$ levels of a categorical) — drop one level. (c) $d \geq n$ — use ridge regression or the pseudo-inverse (`np.linalg.lstsq`).

6. The minimum-norm least-squares solution: among all $w$ that minimize $\|y - Xw\|^2$, return the one with smallest $\|w\|$. It uses SVD. It's "right" because it's the unique answer in a well-defined sense; arbitrarily picking from infinite solutions wouldn't be.

7. Factors: 100/101 ≈ 0.990, 4/5 = 0.800, 0.01/1.01 ≈ 0.010. The 0.01 direction is shrunk drastically (by 99%). This is desirable because that direction's coefficient was the most poorly-estimated — its variance is huge under OLS. Ridge correctly shrinks the noisy-but-unhelpful direction.

8. The relationship is non-linear in the current features. Try: (a) add polynomial or interaction terms; (b) log-transform $y$ or some $x$; (c) switch to a non-linear model class (trees, GBT).

9. Without standardization, feature A has range 100× feature B. To represent the same effect, the weight on B has to be 100× larger than the weight on A. Ridge penalizes squared weights, so it would *unfairly* shrink the weight on B by far more. After standardization both features have unit standard deviation, so the penalty is comparable across them.

10. Closed form requires $O(d^3)$ for the inverse plus $O(nd^2)$ to form $X^\top X$. Gradient descent is $O(nd)$ per iteration. Closed form wins for small $d$; gradient descent wins for large $d$. Rule of thumb: closed form for $d < 10{,}000$; iterative beyond. (Spark MLlib uses normal equations up to about $d = 4096$.)

11. Laplace PDF: $\frac{1}{2b} \exp(-|x|/b)$. Log-likelihood: $-\sum |y_i - w^\top x_i| / b + \text{const}$. Maximizing → minimizing $\sum |y_i - w^\top x_i|$, which is **least absolute deviations (LAD)** regression. No closed form because $|\cdot|$ isn't differentiable at zero — solved iteratively. LAD is robust to outliers, unlike OLS.

12. $R^2 = 0$: the model is no better than predicting the mean. $R^2 = 1$: perfect fit, residuals are all zero. $R^2$ can be negative *on test data* when the model is worse than predicting the train mean — typical for severely overfit models. On training data $R^2 \geq 0$ always with an intercept (the OLS solution is at least as good as $\bar{y}$).

</details>
