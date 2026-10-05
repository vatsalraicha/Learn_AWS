# Chapter 16 — Loss Functions and the Optimization Framing of ML

> **Goal of this chapter:** to convert the slightly vague picture of "ML is function approximation" from Chapter 1 into a concrete, mathematical job. By the end of the chapter you should be able to write down what it formally means to "train a model"; explain why squared error is the natural loss for regression with Gaussian noise (and *derive* it from maximum likelihood); explain why cross-entropy is the natural loss for classification (and derive it from Bernoulli MLE); explain the relationship between the 0/1 loss (what we *actually* care about) and the cross-entropy loss (what we *actually* optimize); and articulate the **empirical risk minimization** principle, including the leap of faith it asks you to make.
>
> This chapter is the centerpiece of the entire curriculum's spine. Everything that comes after — gradient descent (Ch 17), overfitting (Ch 18), the bias-variance decomposition (Ch 19), regularization (Ch 20), cross-validation (Ch 22), every specific algorithm in Part F — is either (a) a method for solving the optimization problem we set up here, or (b) a method for choosing among the *several* possible optimization problems we could have set up here. Read this carefully.

---

## 16.1 The question every algorithm answers

Chapter 1 said ML's job is to take examples $\{(x_i, y_i)\}_{i=1}^n$ and produce a function $\hat{f}: \mathcal{X} \to \mathcal{Y}$ that approximates the unknown true function $f$. That left two enormous questions unanswered:

1. *Out of the infinite space of possible functions $\hat{f}$, which one do we pick?*
2. *On what grounds do we call one $\hat{f}$ "better" than another?*

The two questions are tangled. You can't pick the best one without a notion of what "best" means. You can't define "best" without committing to a measure. So the first move in setting up any ML problem is to write down a **loss function** — a number-valued function that tells you, for any candidate $\hat{f}$, *how badly it does* on the data you have.

Once you have a loss function, "train a model" turns into:

$$
\hat{f} = \arg\min_{f \in \mathcal{H}} \;\; L(f; \text{training data})
$$

Read aloud: "the model we ship is the one, drawn from the hypothesis class $\mathcal{H}$, that minimizes our loss on the training data." Every supervised ML algorithm in this book — linear regression, logistic regression, decision trees, random forests, gradient-boosted trees, neural networks — is a specific instantiation of this template. The hypothesis class $\mathcal{H}$ changes (linear functions, decision trees of depth $\leq d$, neural nets of a given architecture), the loss $L$ changes (squared error, cross-entropy, hinge), and the optimization procedure changes (closed-form, gradient descent, greedy splitting). The *shape* of the problem does not.

The rest of this chapter unpacks that template.

---

## 16.2 What is a loss function, formally?

A **loss function** is any function

$$
\ell : \mathcal{Y} \times \mathcal{Y} \to \mathbb{R}_{\geq 0}
$$

that takes a prediction $\hat{y}$ and a true label $y$, and returns a non-negative real number measuring how wrong the prediction was. Conventions:

- $\ell(\hat{y}, y) = 0$ means the prediction is perfect.
- $\ell(\hat{y}, y) > 0$ means the prediction is wrong; larger means more wrong.

That's it. That's the contract. Any function satisfying it is a candidate loss. The choice of *which* loss is what shapes the problem.

A small but crucial subtlety: $\hat{y}$ doesn't have to live in the same set as $y$. For classification, $y \in \{0, 1\}$, but the model often outputs $\hat{y} \in [0, 1]$ — a probability rather than a hard label. The loss has to accept both. We'll see this pattern repeatedly: the *score* the model produces and the *label* the world has are not in the same format, and the loss is the bridge.

For an entire dataset of $n$ examples, the **empirical risk** (or empirical loss, or training loss — the names all mean the same thing) is just the average:

$$
L(f) = \frac{1}{n} \sum_{i=1}^n \ell(f(x_i), y_i)
$$

"Empirical" because it's computed on the empirical data, not on the underlying population. We'll come back, harshly, to the difference in §16.9.

---

## 16.3 Squared loss for regression — and why it's everywhere

For regression problems — $\mathcal{Y} = \mathbb{R}$ — by far the most common loss is **squared error**:

$$
\ell_{\text{sq}}(\hat{y}, y) = (y - \hat{y})^2
$$

The empirical risk is the **mean squared error**:

$$
\text{MSE}(f) = \frac{1}{n} \sum_{i=1}^n (y_i - f(x_i))^2
$$

Three observations before we ask *why* this loss specifically:

First, it's symmetric: predicting 10 when the truth is 8 costs the same as predicting 6 when the truth is 8. Both are off by 2; both incur a loss of 4.

Second, it's strictly convex in $\hat{y}$ — the parabola opens upward, has a unique minimum, and gets steep fast as you move away from it. A prediction off by 4 costs *four times* as much as a prediction off by 2, not twice as much. Large errors are punished disproportionately.

Third, it's smooth — differentiable everywhere with respect to $\hat{y}$. We'll exploit this in Chapter 17 when we talk about gradient descent.

But the deeper question is: why squared error rather than, say, $(y - \hat{y})^4$ or $|y - \hat{y}|^3$? It's not arbitrary. There's a beautiful probabilistic story underneath, and it's worth telling now because the same shape of argument explains every loss function in this chapter.

### 16.3.1 Deriving MSE from Gaussian noise + MLE

Here's the setup. Suppose the true relationship between $x$ and $y$ in the world is some function $f^*$ plus *additive Gaussian noise*:

$$
y = f^*(x) + \varepsilon, \qquad \varepsilon \sim \mathcal{N}(0, \sigma^2)
$$

That is, the world produces $y$ by computing $f^*(x)$ and then adding a normally-distributed random kick with mean 0 and variance $\sigma^2$. This is a *modeling assumption* — and in many regression problems it's a reasonable one, because measurement error, omitted variables, and the central limit theorem all push real-world noise toward normality.

Given this assumption, the probability density of observing a specific $y$ at a specific $x$, *if our model $f$ is correct*, is the Gaussian density:

$$
p(y \mid x; f) = \frac{1}{\sqrt{2\pi\sigma^2}} \exp\left(-\frac{(y - f(x))^2}{2\sigma^2}\right)
$$

Now suppose we have $n$ independent training examples $(x_1, y_1), \ldots, (x_n, y_n)$. The probability density of observing *all* of them, given a candidate $f$, is the product (independence):

$$
p(y_1, \ldots, y_n \mid x_1, \ldots, x_n; f) = \prod_{i=1}^n \frac{1}{\sqrt{2\pi\sigma^2}} \exp\left(-\frac{(y_i - f(x_i))^2}{2\sigma^2}\right)
$$

This expression — viewed as a function of $f$ — is called the **likelihood** of the data under the model. The maximum likelihood estimate (MLE) is the $f$ that makes this expression as large as possible. The picture: "out of all candidate functions, pick the one that makes the actual observed data the *least surprising*."

Maximizing a product of small numbers is numerically nasty, so we take logs. Logarithms turn products into sums, and the log is monotonic so the maximizer is the same. The **log-likelihood** is:

$$
\log p(\cdot \mid \cdot; f) = \sum_{i=1}^n \left[-\frac{1}{2}\log(2\pi\sigma^2) - \frac{(y_i - f(x_i))^2}{2\sigma^2}\right]
$$

Let me simplify, step by step. Pull the constants out of the sum:

$$
= -\frac{n}{2}\log(2\pi\sigma^2) - \frac{1}{2\sigma^2} \sum_{i=1}^n (y_i - f(x_i))^2
$$

Now maximize this over $f$. The first term doesn't depend on $f$ at all — it's a constant we can drop for the purposes of optimization. The second term has a negative sign and a positive $1/(2\sigma^2)$ factor; maximizing a negative quantity is the same as minimizing its absolute value. So maximizing the log-likelihood is equivalent to:

$$
\arg\min_f \sum_{i=1}^n (y_i - f(x_i))^2
$$

And that, after dividing by $n$ (which doesn't change the minimizer), is **exactly the MSE**.

Read this slowly: *under the assumption that the noise around the true function is Gaussian, minimizing squared error is the same thing as picking the most probable explanation for the data.* MSE isn't arbitrary. It's the maximum-likelihood loss for one of the most natural noise models in the world. That's why it shows up everywhere — and also why, when the noise *isn't* Gaussian (heavy tails, asymmetric distributions, outliers), squared error becomes a worse choice and other losses become better.

### 16.3.2 A small numerical worked example

Suppose we have four predictions and four truths:

| $i$ | $y_i$ | $\hat{y}_i$ | residual $y_i - \hat{y}_i$ | squared |
|---:|----:|-----:|---:|---:|
| 1 | 10.0 | 9.0  | $+1.0$ | 1.00 |
| 2 |  5.0 | 6.0  | $-1.0$ | 1.00 |
| 3 |  8.0 | 8.5  | $-0.5$ | 0.25 |
| 4 |  2.0 | 5.0  | $-3.0$ | 9.00 |

The MSE is $(1.00 + 1.00 + 0.25 + 9.00) / 4 = 11.25 / 4 = 2.8125$.

Notice how the fourth example, with a residual of $-3$, contributes 9 — more than the other three examples combined. That's the disproportionate-punishment property at work. If you care a lot about this property, MSE is great. If a single outlier is poisoning your fit, MSE is dangerous, and the next section's alternative may serve you better.

---

## 16.4 Absolute loss (MAE) — when MSE is too sensitive

The **absolute loss** is just what it sounds like:

$$
\ell_{\text{abs}}(\hat{y}, y) = |y - \hat{y}|
$$

and the empirical risk is the **mean absolute error**:

$$
\text{MAE}(f) = \frac{1}{n} \sum_{i=1}^n |y_i - f(x_i)|
$$

For the four-point example above:

| $i$ | $y_i$ | $\hat{y}_i$ | $|y_i - \hat{y}_i|$ |
|---:|----:|-----:|---:|
| 1 | 10.0 | 9.0  | 1.00 |
| 2 |  5.0 | 6.0  | 1.00 |
| 3 |  8.0 | 8.5  | 0.50 |
| 4 |  2.0 | 5.0  | 3.00 |

MAE $= (1.00 + 1.00 + 0.50 + 3.00) / 4 = 5.50 / 4 = 1.375$.

Compare to the MSE we got above (2.8125). Two qualitative differences:

**MAE is more robust to outliers.** The fourth example contributes $3.0$ to MAE — three times as much as a residual-$1$ example — instead of contributing 9 — nine times as much. The penalty grows *linearly* with the error rather than *quadratically*. A single 100-dollar misprediction in a $\$10k$ regression will dominate MSE but will be only one data point's worth of grief in MAE.

There's a probabilistic story here too. If you assume the noise is Laplace-distributed ($p(\varepsilon) \propto e^{-|\varepsilon|/b}$) rather than Gaussian, then MAE pops out of MLE in exactly the same way MSE did for Gaussian noise. The Laplace distribution has fatter tails than the Gaussian — it expects occasional large deviations as a feature, not a bug — so the loss it produces under-weights extreme residuals.

**MAE is not differentiable at zero.** The absolute-value function has a kink at the origin; the derivative is $+1$ for positive residuals, $-1$ for negative residuals, and undefined exactly at zero. This isn't a deal-breaker — you can use *subgradients*, which we touch on in Chapter 17, and modern optimizers handle it fine — but it complicates the derivation. For linear regression with MSE, there is a beautiful closed-form solution (Chapter 31); for linear regression with MAE (called *quantile regression* in its general form), there is not.

### 16.4.1 The median-vs-mean connection

Here's a slick fact that helps you remember the MSE/MAE difference. Suppose we have a single feature-free prediction problem: pick a constant $c$ that best predicts $\{y_1, \ldots, y_n\}$. What value of $c$ minimizes the loss?

For **MSE**: $\arg\min_c \sum (y_i - c)^2$. Take the derivative with respect to $c$ and set to zero: $-2 \sum (y_i - c) = 0$, i.e., $\sum y_i = nc$, i.e., $c = \bar{y}$, the **mean**.

For **MAE**: $\arg\min_c \sum |y_i - c|$. This is harder to differentiate but a classical result: the minimizer is the **median**.

So MSE wants the mean; MAE wants the median. And we know from descriptive statistics that the mean is sensitive to outliers and the median is not. The connection is exact, and it's a clean way to remember the qualitative difference.

---

## 16.5 The hinge loss — a brief mention for SVMs

Used by support vector machines (SVMs), which are out of the core ML Associate scope but worth knowing about. For binary classification with $y \in \{-1, +1\}$ and a real-valued score $\hat{y}$:

$$
\ell_{\text{hinge}}(\hat{y}, y) = \max(0, 1 - y\hat{y})
$$

The shape: if $y$ and $\hat{y}$ have the same sign and $|\hat{y}| \geq 1$ (the prediction is correct and confident), the loss is zero. Otherwise, the loss grows linearly with the "shortfall" from a confident-correct margin. The SVM training objective is to minimize hinge loss plus a regularization term.

We won't derive it; we mention it so the name doesn't surprise you. Cross-entropy (next section) is what dominates classical classification in this curriculum.

---

## 16.6 Cross-entropy loss for classification

Now we turn to classification, where $\mathcal{Y}$ is a discrete set. The 0/1 loss — discussed in §16.7 — is the loss we *actually care about*: did the prediction match the label or not? But it's terrible to optimize directly. So we use a **surrogate loss** that's friendlier to optimization but still aligned with what we care about. For binary and multiclass classification with probabilistic outputs, that surrogate is **cross-entropy** (also called **log loss**, **logistic loss**, or **negative log-likelihood**).

Let's derive it from scratch, the same way we derived MSE — from a probabilistic assumption + MLE.

### 16.6.1 Binary cross-entropy from Bernoulli MLE

Setup. Binary classification, so $y \in \{0, 1\}$. The model outputs a probability $\hat{p} \in [0, 1]$ for the positive class — e.g., logistic regression's $\hat{p} = \sigma(\mathbf{w} \cdot \mathbf{x} + b)$ from Chapter 3. The assumption: given the features, the label is a Bernoulli draw with parameter $\hat{p}$:

$$
p(y \mid x; \hat{p}) = \hat{p}^y (1 - \hat{p})^{1-y}
$$

Check: if $y = 1$, this is $\hat{p}^1(1-\hat{p})^0 = \hat{p}$. If $y = 0$, this is $\hat{p}^0(1-\hat{p})^1 = 1 - \hat{p}$. Both reduce to the obvious answer.

For $n$ i.i.d. examples, the likelihood is the product:

$$
\prod_{i=1}^n \hat{p}_i^{y_i} (1 - \hat{p}_i)^{1-y_i}
$$

where $\hat{p}_i$ is the model's predicted probability for example $i$. Take the log:

$$
\sum_{i=1}^n \left[y_i \log \hat{p}_i + (1 - y_i) \log(1 - \hat{p}_i)\right]
$$

We want to maximize this. Equivalently, minimize the *negative* log-likelihood:

$$
L(f) = -\sum_{i=1}^n \left[y_i \log \hat{p}_i + (1 - y_i) \log(1 - \hat{p}_i)\right]
$$

Divide by $n$ (doesn't change the minimizer) and you have the **binary cross-entropy** loss:

$$
\text{BCE}(f) = -\frac{1}{n} \sum_{i=1}^n \left[y_i \log \hat{p}_i + (1 - y_i) \log(1 - \hat{p}_i)\right]
$$

Look at the per-example loss $-[y \log \hat{p} + (1-y)\log(1-\hat{p})]$. Only one of the two terms is active per example — the $y_i = 1$ term when $y_i = 1$, the $y_i = 0$ term when $y_i = 0$. The loss for a positive example $(y=1)$ is $-\log \hat{p}$ — *zero* when $\hat{p} = 1$ (perfect confidence in the right answer), *infinite* when $\hat{p} \to 0$ (perfect confidence in the *wrong* answer). The penalty for being confidently wrong is unbounded. This is a critical property: it pushes the model to make calibrated, sensible probability outputs, not just to get the binary answer right.

### 16.6.2 A numerical worked example

Four binary classification examples. Compute the BCE.

| $i$ | $y_i$ | $\hat{p}_i$ | term: $-[y_i \log \hat{p}_i + (1-y_i)\log(1-\hat{p}_i)]$ |
|---:|---:|---:|---:|
| 1 | 1 | 0.9 | $-\log(0.9) = 0.1054$ |
| 2 | 0 | 0.1 | $-\log(0.9) = 0.1054$ |
| 3 | 1 | 0.6 | $-\log(0.6) = 0.5108$ |
| 4 | 0 | 0.8 | $-\log(0.2) = 1.6094$ |

(All logs are natural logarithms.)

BCE = $(0.1054 + 0.1054 + 0.5108 + 1.6094) / 4 = 2.331 / 4 = 0.5828$.

Notice example 4: the model said positive class with probability $0.8$, but the true label was negative. The model was confident and wrong, and the loss reflects that — $1.6094$ is more than ten times the loss of example 1 (also a correct-ish prediction, $\hat{p} = 0.9$ for a positive). Confidently wrong is what cross-entropy punishes hardest.

A useful sanity check: a model that always predicts $\hat{p} = 0.5$ regardless of input gets a per-example loss of $-\log(0.5) \approx 0.693$ on *every* example. That's the BCE of a model that knows nothing. Any trained model worth shipping should beat 0.693 substantially on its training data.

### 16.6.3 Multiclass cross-entropy

For multiclass classification with $K$ classes — $y \in \{1, 2, \ldots, K\}$, model outputs a probability vector $\hat{p} = (\hat{p}_1, \ldots, \hat{p}_K)$ with $\sum_k \hat{p}_k = 1$ — the analogous derivation starts from the **categorical** (one-hot multinomial-with-$n=1$) distribution:

$$
p(y \mid x; \hat{p}) = \prod_{k=1}^K \hat{p}_k^{\mathbb{1}[y = k]}
$$

where $\mathbb{1}[y=k]$ is 1 if the true class is $k$ and 0 otherwise. The negative log-likelihood, averaged over $n$ examples, is:

$$
\text{CE}(f) = -\frac{1}{n} \sum_{i=1}^n \sum_{k=1}^K \mathbb{1}[y_i = k] \log \hat{p}_{i,k} = -\frac{1}{n}\sum_{i=1}^n \log \hat{p}_{i, y_i}
$$

The right-hand simplification is the useful form: for each example, just look at the model's predicted probability for the *true* class, take the log, negate. Sum, average.

Special case check: with $K=2$, this reduces to binary cross-entropy. (Exercise.)

In code, this is what `nn.CrossEntropyLoss` in PyTorch and `sparse_categorical_crossentropy` in Keras compute. In Spark ML, it's the loss inside `LogisticRegression`'s multinomial mode.

---

## 16.7 The 0/1 loss — the one we actually care about

For classification, the loss we *truly* care about is whether the predicted class matches the true class:

$$
\ell_{0/1}(\hat{y}, y) = \mathbb{1}[\hat{y} \neq y]
$$

— 0 if we got it right, 1 if we got it wrong. The empirical risk is then the **error rate** (one minus accuracy):

$$
\text{Error}(f) = \frac{1}{n}\sum_{i=1}^n \mathbb{1}[\hat{y}_i \neq y_i]
$$

This is what the business cares about. So why don't we just optimize it directly?

Two reasons, and they're devastating:

**It's non-differentiable.** Every classification model produces, at some intermediate layer, a continuous score (logits, probabilities). The 0/1 loss is a *step* — it jumps from 0 to 1 at the threshold. Gradient-based optimization can't navigate steps; the gradient is zero everywhere the loss is constant, and undefined at the cliff. SGD slides off it; no learning happens.

**It's non-convex in the parameters.** Even if you could differentiate it, the resulting optimization problem is NP-hard in general. There's no efficient algorithm.

So we use cross-entropy as a **surrogate**. Cross-entropy is differentiable, convex (for linear models — Ch 32 will show), and *upper-bounds* 0/1 loss for sensible thresholds. Minimizing cross-entropy tends to minimize 0/1 loss too, with the bonus that the model also produces calibrated probability outputs that we can use to compute precision, recall, ROC, PR curves, threshold tuning — everything in Chapter 3's spam example.

The relationship is best summarized as: **0/1 loss is the goal; cross-entropy is the lever.** We pull the lever; the goal gets closer; we measure the goal separately to see how we're doing.

```
                cross-entropy loss
   loss            ___________________
     |          __/
     |       __/
     |     _/
     |    /
     |    |  0/1 loss
     | 1__|________________________
     |    |
     |    |
     | 0__|________________________
          ↑
        decision boundary
```

(Schematically: 0/1 loss is the dashed step; cross-entropy is a smooth upper-bounding curve. Optimizing the smooth one drags down the step.)

---

## 16.8 Empirical risk minimization — and the hope

We can now write down the formal ML setup with full precision. Given:

- A hypothesis class $\mathcal{H}$ (e.g., all linear functions, all decision trees of depth $\leq d$, all neural nets of a given architecture).
- A loss function $\ell$ (e.g., squared error, cross-entropy).
- A training set $D = \{(x_i, y_i)\}_{i=1}^n$ drawn i.i.d. from some unknown distribution $P(x, y)$.

We define the **empirical risk** (training loss):

$$
\hat{L}(f) = \frac{1}{n}\sum_{i=1}^n \ell(f(x_i), y_i)
$$

And the **empirical risk minimizer**:

$$
\hat{f} = \arg\min_{f \in \mathcal{H}} \hat{L}(f)
$$

This is **empirical risk minimization** (ERM). It is the unifying framework for almost all of classical supervised ML. Each algorithm is just ERM with a specific $(\mathcal{H}, \ell)$ pair and a specific algorithm for solving the $\arg\min$:

| Algorithm | $\mathcal{H}$ | $\ell$ | Solver |
|---|---|---|---|
| Linear regression (OLS) | linear functions | squared error | closed-form |
| Ridge regression | linear functions | squared + L2 | closed-form |
| Lasso | linear functions | squared + L1 | coordinate descent |
| Logistic regression | linear-then-sigmoid | binary cross-entropy | gradient descent |
| Multinomial LR | linear-then-softmax | multiclass cross-entropy | gradient descent |
| Decision tree | trees of depth $\leq d$ | Gini / entropy (a proxy for 0/1) | greedy splitting |
| Random forest | average of $T$ trees | as above per tree | bagging + greedy |
| GBT | sum of $T$ shallow trees | any differentiable | functional gradient descent |

(I'm using `solver` loosely — the "closed-form" for OLS is itself solved by Cholesky or QR factorization in practice. The point is the conceptual move.)

### 16.8.1 The leap of faith

Here is the deeply uncomfortable part. We minimize the empirical risk. But the empirical risk is the loss on the training data — data we've already seen. What we *actually* want is low loss on data we *haven't* seen — the **true (or population) risk**:

$$
L^*(f) = \mathbb{E}_{(x, y) \sim P}[\ell(f(x), y)]
$$

This is the expected loss over the entire underlying distribution $P$, which we don't have access to. We have access only to the empirical distribution — a finite, noisy sample.

The leap of faith in ERM is: *empirical risk on the training set is a good estimate of true risk on the population, so minimizing the empirical risk should approximately minimize the true risk.*

This is true *sometimes* — and the next four chapters (18, 19, 20, 22) are about exactly when it fails and what to do about it. Spoiler: it fails most spectacularly when $\mathcal{H}$ is very large (high capacity), so that the empirical risk can be driven near zero while the true risk balloons. That's overfitting, and it's why ERM alone is not enough.

For now, internalize:

- ERM is the framework.
- The training loss it minimizes is *not* the true loss we care about.
- The discrepancy between them is the central technical problem of supervised ML, and Chapters 18-22 are the response.

---

## 16.9 Why "minimize training loss" is naive — preview

Consider an extreme case. Suppose $\mathcal{H}$ contains a function that just memorizes the training data:

$$
f_{\text{memorize}}(x) = \begin{cases} y_i & \text{if } x = x_i \text{ for some } i \\ 0 & \text{otherwise} \end{cases}
$$

The empirical risk of $f_{\text{memorize}}$ is *zero*. It is the empirical risk minimizer. ERM picks it. It is also catastrophically bad at predicting anything new — it returns $0$ for every input it hasn't seen.

This is the reductio. Pure ERM, with a sufficiently rich hypothesis class, will pick a memorizer. To get useful generalization, we have to *constrain* $\mathcal{H}$ — explicitly (smaller model class), implicitly (regularization, Ch 20), or via the optimization procedure itself (early stopping, dropout). The constraint is *not* in the loss function; it's in the choice of $\mathcal{H}$ and the discipline around training.

This insight is why Ch 18 (capacity, overfitting), Ch 19 (bias-variance), Ch 20 (regularization), and Ch 22 (cross-validation) all exist. The loss function is the framing; the rest of Part D is the *honest* answer to "now how do we actually do this without the model cheating?"

---

## 16.10 Worked computation: comparing MSE and MAE in code

Let's compute MSE and MAE on a small synthetic example in NumPy. Save the script as `losses_demo.py`.

```python
import numpy as np

# Ground truth and predictions for 6 examples.
y_true = np.array([10.0, 5.0, 8.0, 2.0, 7.5, 12.0])
y_pred = np.array([ 9.0, 6.0, 8.5, 5.0, 7.0, 11.5])

residuals = y_true - y_pred

mse = np.mean(residuals ** 2)
mae = np.mean(np.abs(residuals))

print(f"Residuals: {residuals}")
print(f"MSE: {mse:.4f}")
print(f"MAE: {mae:.4f}")
print(f"sqrt(MSE) = RMSE: {np.sqrt(mse):.4f}")

# Now imagine one of the predictions is dramatically wrong (outlier).
y_pred_bad = y_pred.copy()
y_pred_bad[3] = -20.0     # was 5.0, now wildly off
res_bad = y_true - y_pred_bad

print("\nWith one outlier prediction:")
print(f"MSE: {np.mean(res_bad ** 2):.4f}")
print(f"MAE: {np.mean(np.abs(res_bad)):.4f}")
```

Run it and you'll see the MSE explodes (the outlier residual is now $22$, contributing $484$ to the sum) while the MAE rises much more modestly (the outlier contributes $22$ vs. typical values around $1$). This is the robustness-to-outliers difference in living color.

### 16.10.1 Cross-entropy in code

```python
import numpy as np

def binary_cross_entropy(y_true, p_pred, eps=1e-12):
    """Binary cross-entropy.
    
    y_true: array of 0/1 labels.
    p_pred: array of predicted probabilities in (0, 1).
    eps: floor to avoid log(0).
    """
    p = np.clip(p_pred, eps, 1 - eps)   # numerical safety
    return -np.mean(y_true * np.log(p) + (1 - y_true) * np.log(1 - p))

y = np.array([1, 0, 1, 0])
p_good = np.array([0.9, 0.1, 0.8, 0.2])   # confident and right
p_meh  = np.array([0.6, 0.4, 0.6, 0.4])   # right direction, low confidence
p_bad  = np.array([0.4, 0.6, 0.3, 0.7])   # right direction inverted

print(f"BCE (good): {binary_cross_entropy(y, p_good):.4f}")
print(f"BCE (meh):  {binary_cross_entropy(y, p_meh):.4f}")
print(f"BCE (bad):  {binary_cross_entropy(y, p_bad):.4f}")
print(f"BCE (50/50 baseline): {binary_cross_entropy(y, np.full(4, 0.5)):.4f}")
```

You'll see:
- Confident-and-right: BCE around 0.16.
- Meh: BCE around 0.51.
- Confidently-wrong: BCE around 0.92.
- Coin-flip: BCE $\approx \log 2 \approx 0.693$ (the "knowing nothing" baseline).

The clip-to-`eps` trick is essential in real implementations: `log(0)` is $-\infty$, and even a single such term overflows the mean. Production loss functions always clip.

---

## 16.11 Putting it together: the optimization framing of ML

We can now state, with full precision, what the rest of Part D is about. Given the ERM setup:

$$
\hat{f} = \arg\min_{f \in \mathcal{H}} \hat{L}(f)
$$

we ask three questions:

1. **How do we actually solve the $\arg\min$?** Even with $\mathcal{H}$ specified and $\ell$ fixed, finding the minimum is an algorithmic problem. For some $(\mathcal{H}, \ell)$ pairs (OLS) there's a closed-form solution. For most modern problems (logistic regression, neural nets), we use **gradient descent**. That's Chapter 17.

2. **How do we keep $\hat{L}(\hat{f})$ from being misleading?** As §16.9 hinted, ERM with rich $\mathcal{H}$ overfits — empirical risk gets driven to zero while true risk explodes. Chapter 18 makes this precise, Chapter 19 decomposes it (bias-variance), Chapter 20 introduces regularization to fight it, and Chapters 21-22 introduce held-out data and cross-validation to *measure* it honestly.

3. **How do we choose $\mathcal{H}$?** A linear function is a very different beast from a 1000-leaf tree. The choice of $\mathcal{H}$ — model class — is the topic of Parts F (supervised algorithms) and G (unsupervised). Each algorithm fixes a specific $\mathcal{H}$ and a specific solver.

These three threads run through the rest of the book. The optimization framing we built in this chapter is the spine connecting them.

---

## 16.12 Summary

The whole chapter, stripped to bones:

1. **Loss function** $\ell(\hat{y}, y) \geq 0$ is a scalar measure of how wrong a prediction is. The empirical risk is the average over the training set.
2. **Squared error** (MSE) is the standard regression loss. It pops out of MLE under the assumption of Gaussian noise. Strictly convex, smooth, sensitive to outliers.
3. **Absolute error** (MAE) is the robust alternative. Pops out of MLE under Laplace noise. Linear penalty; more robust to outliers; non-differentiable at zero. Predicts the median where MSE predicts the mean.
4. **Cross-entropy** is the standard classification loss. Pops out of MLE under Bernoulli (binary) or categorical (multiclass) likelihoods. Unbounded penalty for confidently-wrong predictions; calibrates probabilities.
5. **0/1 loss** is what classification really cares about, but it's not differentiable and not convex. Cross-entropy is the standard differentiable surrogate.
6. **Empirical risk minimization** (ERM) is the unifying framework: pick the $f$ in $\mathcal{H}$ that minimizes the training loss. Every supervised ML algorithm is ERM with specific $(\mathcal{H}, \ell, \text{solver})$.
7. **The leap of faith** in ERM is that training loss approximates true (population) loss. This is true some of the time and false a lot of the time. The rest of Part D is the response.

If you can write down the ERM template — $\arg\min_{f \in \mathcal{H}} \frac{1}{n} \sum \ell(f(x_i), y_i)$ — and explain what each symbol means, including the leap of faith, you have the spine.

---

## 16.13 What this builds on / where this returns

**Builds on:**
- Chapter 1 (function approximation $f, \hat{f}$).
- Chapter 5 (expectation of a random variable — needed to write true risk $\mathbb{E}[\ell]$).
- Chapter 6 (the Gaussian and Bernoulli distributions — the MLE derivations depend on their densities).
- Chapter 9 (sampling and i.i.d. — the assumption underlying the leap of faith).

**Returns:** in basically every later chapter.
- *Chapter 17* solves the $\arg\min$ via gradient descent.
- *Chapter 18* shows why pure ERM overfits.
- *Chapter 19* gives the bias-variance decomposition of the *true* risk we wish we could minimize.
- *Chapter 20* adds a regularization term to the empirical risk to control overfitting.
- *Chapters 21-22* set up validation/CV to estimate true risk honestly.
- *Chapter 31* solves OLS (MSE on linear functions) in closed form.
- *Chapter 32* derives logistic regression's training objective from binary cross-entropy.
- *Chapter 36* uses functional-gradient descent on arbitrary differentiable losses for gradient boosting.

---

## 16.14 Exercises

1. **The mean as MSE-minimizer.** Without re-reading §16.4.1, derive: given a fixed set of numbers $\{y_1, \ldots, y_n\}$, what constant $c$ minimizes $\sum (y_i - c)^2$? Show the steps.

2. **Median vs mean.** Compute MSE and MAE for the constant predictions $c = 5$ and $c = 6$ on the data $\{1, 4, 5, 6, 100\}$. Which $c$ wins for each loss? What's the actual mean and median?

3. **Why log?** In the MLE derivation of MSE we took the log of the likelihood before maximizing. Name two reasons.

4. **A Laplace check.** The Laplace density is $p(\varepsilon) = \frac{1}{2b}\exp(-|\varepsilon|/b)$. Carry through the MLE derivation analogous to §16.3.1 and show that the resulting empirical loss is MAE.

5. **Confidently wrong.** Under binary cross-entropy, compute the loss for a prediction of $\hat{p} = 0.01$ when $y = 1$. Compute it for $\hat{p} = 0.5$ when $y = 1$. By what factor is the first worse?

6. **Cross-entropy as a baseline.** What's the BCE of a "knows nothing" model that predicts $\hat{p} = 0.5$ for every example, on a balanced binary dataset? Show your work.

7. **Multiclass reduces to binary.** For $K = 2$, show algebraically that multiclass cross-entropy ($-\sum_k \mathbb{1}[y=k]\log \hat{p}_k$) reduces to binary cross-entropy.

8. **0/1 vs. cross-entropy.** Give an example of a model on 4 examples where 0/1 loss is the same as a competing model, but cross-entropy distinguishes them. Why is this distinction often valuable?

9. **The memorization model.** Why doesn't ERM with the memorization function from §16.9 give a useful model in practice? What's the empirical risk? What's the true risk?

10. **Outliers and loss choice.** You're predicting transaction amounts in a fraud-investigation pipeline. The vast majority are between \$10 and \$500, but occasionally a legitimate \$50,000 wire transfer shows up. Which loss would you pick — MSE or MAE — and why?

11. **Numerical safety.** Why does the BCE implementation clip predictions to $[\epsilon, 1 - \epsilon]$ before taking the log? What goes wrong without it?

12. **ERM in one sentence.** Write the ERM problem in symbols, then explain in English what each piece of notation means, in under 100 words.

<details>
<summary>Answers</summary>

1. $\frac{d}{dc}\sum(y_i - c)^2 = -2\sum(y_i - c) = 0 \Rightarrow \sum y_i = nc \Rightarrow c = \bar{y}$.

2. For $\{1, 4, 5, 6, 100\}$: mean is $23.2$, median is $5$. At $c=5$: MSE $= (16+1+0+1+9025)/5 = 1808.6$; MAE $= (4+1+0+1+95)/5 = 20.2$. At $c=6$: MSE $= (25+4+1+0+8836)/5 = 1773.2$; MAE $= (5+2+1+0+94)/5 = 20.4$. MSE prefers $c=6$ (closer to mean of $23.2$); MAE prefers $c=5$ (the median).

3. (a) Products of many small probabilities underflow numerically; the log turns them into sums of negative numbers that stay representable. (b) The log is monotonic, so maximizing the log of the likelihood gives the same maximizer as the likelihood itself. (Bonus: derivatives of products via the product rule are nightmarish; derivatives of sums are easy.)

4. Likelihood is $\prod \frac{1}{2b}\exp(-|y_i - f(x_i)|/b)$. Log-likelihood is $-n\log(2b) - \frac{1}{b}\sum |y_i - f(x_i)|$. Maximizing over $f$ drops the constant, equivalent to minimizing $\sum |y_i - f(x_i)|$, which is MAE up to division by $n$.

5. $-\log(0.01) \approx 4.605$. $-\log(0.5) \approx 0.693$. Factor: $4.605 / 0.693 \approx 6.65$. Being confidently wrong (1% probability assigned to the correct class) is roughly 6.65× worse than being uncertain.

6. On any example, $-[y \log 0.5 + (1-y)\log 0.5] = -\log 0.5 = \log 2 \approx 0.693$. So BCE $= 0.693$ regardless of the labels. This is the floor a useful model must beat.

7. With $K=2$ and using $p_1 = \hat{p}, p_2 = 1 - \hat{p}$, and treating the labels as $y \in \{1, 2\}$ with one-hot: $-\sum_k \mathbb{1}[y=k]\log p_k$ becomes $-\log \hat{p}$ when $y$ is class 1, and $-\log(1 - \hat{p})$ when $y$ is class 2. Relabel class 1 → 1, class 2 → 0, and that's exactly $-[y\log \hat{p} + (1-y)\log(1-\hat{p})]$.

8. Suppose model A predicts $\hat{p} = (0.51, 0.49, 0.51, 0.49)$ on labels $(1, 0, 1, 0)$ — gets them all right barely. Model B predicts $\hat{p} = (0.99, 0.01, 0.99, 0.01)$ — gets them all right confidently. Both have 0/1 loss 0 (using threshold 0.5). But B's cross-entropy is much lower. Distinguishing is valuable because B's outputs are *calibrated probabilities* you can use for thresholding, ranking, and downstream cost-sensitive decisions; A's outputs aren't trustworthy at any threshold but 0.5.

9. Empirical risk: zero (perfect on training data). True risk: catastrophic (returns 0 on every novel input, with cross-entropy that goes to infinity when the true label is 1). It demonstrates that minimizing empirical risk alone, with sufficient hypothesis-class capacity, doesn't produce a useful model. The fix lies in constraining $\mathcal{H}$ — the entire content of Ch 18-20.

10. MAE. The occasional \$50k wire is a legitimate outlier — it isn't noise we want the model to fit; it's a real data point we don't want to *dominate* the loss. Under MSE, that single example's residual could be 10⁴+ times bigger than typical residuals and would essentially be the only thing the model fits. MAE keeps the influence proportional. The exception: if those big transfers are exactly what you want to predict accurately, MSE's emphasis is what you want — depends on the cost structure.

11. `log(0)` is $-\infty$, and any term where $\hat{p}=0$ paired with $y=1$ (or $\hat{p}=1$ with $y=0$) would make the loss infinite — and crucially the *gradient* explodes too. Clipping caps the worst-case contribution and keeps optimization numerically stable. Real implementations clip at $\epsilon \approx 10^{-12}$.

12. $\hat{f} = \arg\min_{f \in \mathcal{H}} \frac{1}{n}\sum_{i=1}^n \ell(f(x_i), y_i)$. In words: among all functions $f$ in our hypothesis class $\mathcal{H}$, we pick the one that minimizes the average loss $\ell$ on our $n$ training examples. The $f(x_i)$ is the prediction, $y_i$ is the true label, $\ell$ measures wrongness. We *hope* this empirical-best $f$ is also good on data we haven't seen — the leap of faith ERM rests on.

</details>
