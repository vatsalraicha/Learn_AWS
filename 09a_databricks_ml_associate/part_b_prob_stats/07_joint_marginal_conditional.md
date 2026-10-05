# Chapter 7 — Joint, Marginal, Conditional Probability and Independence

> **Goal of this chapter:** to move from one random variable at a time to several random variables interacting. The spam classifier wants $P(\text{spam} \mid \text{contents})$ — a conditional probability. The notation $P(A \mid B)$ looks simple; the structure underneath it (joint distributions, marginalisation, the chain rule) deserves a careful unpacking. By the end of this chapter you will be able to compute conditional probabilities from joint tables, marginalise out unwanted variables, recognise independence when it holds, and understand covariance and correlation as the natural numerical summary of "how two variables move together."

---

## 7.1 Why we need more than one variable

In Chapter 3, the spam classifier produced $\hat{p}(\text{spam} \mid x)$. The bar is doing work. The model is not predicting "is this email spam" in the abstract; it is predicting *given the email's contents*. The contents condition the prediction. Different content vectors $x$ get different predicted probabilities — that is the whole point.

The probability framework so far doesn't quite handle this. Chapter 5 talked about a single random variable $X$ at a time. To talk about probabilities of one thing given another, we need to talk about *two* random variables — the label $Y$ and the contents $X$ — and the way their distributions interact. That interaction is captured by the **joint distribution**.

A second motivation: many estimators we will encounter (variance of a sum, covariance, correlation, the bias-variance decomposition, PCA) are statements about how multiple random variables relate. None of them can even be stated, much less proved, without joint distributions in hand.

So we level up.

---

## 7.2 Joint distributions

### 7.2.1 Discrete joint distributions

For two discrete random variables $X$ and $Y$, the **joint probability mass function** is

$$
p_{X,Y}(x, y) = P(X = x, Y = y).
$$

This is the probability that $X$ takes the value $x$ *and* $Y$ takes the value $y$ — both simultaneously. The comma in $P(X = x, Y = y)$ is read "and." For the rest of this chapter, we will use lowercase $p$ for joint PMFs (and lowercase $f$ for joint PDFs) and uppercase $P$ for probabilities of events.

The joint PMF satisfies the obvious generalisation of the single-variable conditions:

1. $p_{X,Y}(x, y) \geq 0$ for all $(x, y)$.
2. $\sum_x \sum_y p_{X,Y}(x, y) = 1$ (summing over all possible value pairs).

### 7.2.2 A worked example: disease and test

Time for a concrete example you can hold in your head.

Suppose we screen a population for a disease using a diagnostic test. There are two random variables:

- $D \in \{0, 1\}$: does the person actually have the disease? ($D = 1$ if yes.)
- $T \in \{0, 1\}$: did the test come back positive? ($T = 1$ if yes.)

A joint distribution over $(D, T)$ might look like this 2x2 table:

```
                    T = 0 (test neg)    T = 1 (test pos)    P(D)
D = 0 (no disease)       0.94                0.05            0.99
D = 1 (disease)          0.001               0.009           0.01
                    -----------------------------------
                         0.941               0.059
P(T)
```

Each cell is the joint probability of that combination. We have made up numbers consistent with a disease that affects 1% of the population (so $P(D=1) = 0.01$) and a test that is right *most of the time* but not perfect.

Let's verify: $0.94 + 0.05 + 0.001 + 0.009 = 1.0$. ✓

A few quick reads from this table:

- The most common outcome is "no disease, negative test" — that's 94% of people.
- "Disease, positive test" (a true positive) is 0.9% of people.
- "No disease, positive test" (a false positive) is 5% of people — *bigger than the entire disease prevalence*. This is going to matter when we ask the famous Bayes question in Chapter 8.

### 7.2.3 Continuous joint distributions

For continuous $X, Y$, replace the PMF with a **joint probability density function** $f_{X,Y}(x, y)$ satisfying:

1. $f_{X,Y}(x, y) \geq 0$ for all $(x, y)$.
2. $\int \int f_{X,Y}(x, y) \, dx \, dy = 1$.
3. For any region $R \subset \mathbb{R}^2$: $P((X, Y) \in R) = \int \int_R f_{X,Y}(x, y) \, dx \, dy$.

Geometrically: $f_{X,Y}$ is a surface in 3D over the $(x, y)$ plane, integrating to 1. Probability of a region equals the volume under the surface above that region.

For the rest of the chapter we will mostly work in the discrete case — the math is the same with sums replaced by integrals.

---

## 7.3 Marginal distributions

If you have a joint distribution over $(X, Y)$ and you want to recover the distribution over $X$ alone — ignoring $Y$, or "marginalising it out" — you sum (or integrate) the joint over all values of $Y$.

### 7.3.1 The marginalisation formula

**Discrete case:**

$$
p_X(x) = \sum_y p_{X,Y}(x, y).
$$

**Continuous case:**

$$
f_X(x) = \int_{-\infty}^{\infty} f_{X,Y}(x, y) \, dy.
$$

The $p_X(x)$ on the left is the **marginal PMF** of $X$ — just the single-variable PMF you'd get if you ignored $Y$.

### 7.3.2 Why is this legal?

It's worth a careful look at why summing the joint gives you the marginal.

The event $\{X = x\}$ — "$X$ takes the value $x$, $Y$ is whatever" — is the union over all values of $y$ of the disjoint events $\{X = x, Y = y\}$:

$$
\{X = x\} = \bigcup_y \{X = x, Y = y\}.
$$

These sub-events are disjoint (you can't have $Y = y_1$ and $Y = y_2$ at the same time for different $y_1, y_2$). By Kolmogorov's third axiom (countable additivity):

$$
P(X = x) = \sum_y P(X = x, Y = y) = \sum_y p_{X, Y}(x, y).
$$

Hence the formula. The licence is the additivity axiom, applied to a partition of the event $\{X = x\}$.

### 7.3.3 Marginals from the disease-test table

The marginal $P(D = d)$ comes from summing rows:

$$
P(D = 0) = 0.94 + 0.05 = 0.99. \quad P(D = 1) = 0.001 + 0.009 = 0.01.
$$

So the disease prevalence is 1%, as we set up.

The marginal $P(T = t)$ comes from summing columns:

$$
P(T = 0) = 0.94 + 0.001 = 0.941. \quad P(T = 1) = 0.05 + 0.009 = 0.059.
$$

About 5.9% of tested people test positive. Note this is much larger than the 1% disease rate — most of the positives are false positives. We'll quantify this exactly in Chapter 8.

These marginals are exactly what showed up in the right-hand column and bottom row of the table — they were the row and column sums.

### 7.3.4 An important warning: marginals do *not* determine the joint

Two different joint distributions can have the same marginals. The marginals tell you about each variable in isolation; the joint additionally tells you how they relate. Throwing away the joint and keeping only the marginals is throwing away information.

A toy example. Consider two binary variables with marginals $P(X = 1) = P(Y = 1) = 0.5$. Joint distribution 1 ("independent"):

| | Y=0 | Y=1 |
|---|---|---|
| X=0 | 0.25 | 0.25 |
| X=1 | 0.25 | 0.25 |

Joint distribution 2 ("perfectly correlated"):

| | Y=0 | Y=1 |
|---|---|---|
| X=0 | 0.5 | 0 |
| X=1 | 0 | 0.5 |

Both have marginal $P(X = 1) = 0.5$ and marginal $P(Y = 1) = 0.5$. But in the first, $X$ and $Y$ are independent; in the second, $X$ always equals $Y$. The marginals are blind to this difference.

This is one of those facts that sounds trivial when stated but bites a surprising number of practitioners. If you see two ML papers reporting "the same input distribution and the same label distribution," they might still be doing very different things.

---

## 7.4 Conditional probability

### 7.4.1 Definition

The **conditional probability** of event $A$ given event $B$ is defined as

$$
P(A \mid B) = \frac{P(A \cap B)}{P(B)}, \quad \text{provided } P(B) > 0.
$$

In words: of all the outcomes in which $B$ happens, what fraction also have $A$? The denominator is "all the ways $B$ can happen"; the numerator is "all the ways $A$ and $B$ can both happen." The ratio is the conditional.

For random variables: $P(X = x \mid Y = y) = \frac{P(X = x, Y = y)}{P(Y = y)} = \frac{p_{X,Y}(x, y)}{p_Y(y)}$.

### 7.4.2 Geometric interpretation

Picture the sample space as a region of area 1. The event $B$ is some sub-region of area $P(B)$.

When we condition on $B$, we are *restricting attention* to that sub-region. We're saying "given that we landed somewhere in $B$, where are we?" The conditional probability rescales probabilities so that the area of $B$ becomes the new "total" — we divide by $P(B)$. Everything outside $B$ is irrelevant; everything inside $B$ gets its probability rescaled by the factor $1 / P(B)$.

```
Whole sample space (area 1)
+--------------------------------+
|                                |
|       +-----------+            |
|       |     A     |            |
|       |   _____   |            |
|       |  |  A∩B|  |            |
|       |  |     |  |            |
|       |  |_____|__|________    |
|       +--|        B          | |
|          |                   | |
|          |                   | |
|          |___________________| |
|                                |
+--------------------------------+

P(A | B) is the fraction of region B that is also in A.
After conditioning on B, B becomes the new universe;
A ∩ B becomes A's "share" of that new universe.
```

The mental shift: conditioning is "restrict and renormalise."

### 7.4.3 Conditional probabilities from the disease-test table

Recall the table:

```
                    T = 0       T = 1     Row total (P(D))
D = 0               0.94        0.05       0.99
D = 1               0.001       0.009      0.01
Col total (P(T))    0.941       0.059      1.0
```

Various conditional probabilities we might want.

**$P(T = 1 \mid D = 1)$** — the test's *sensitivity* (also called recall, or true positive rate). Of people who have the disease, what fraction test positive?

$$
P(T = 1 \mid D = 1) = \frac{P(T = 1, D = 1)}{P(D = 1)} = \frac{0.009}{0.01} = 0.9.
$$

90% of diseased people test positive. The test has 90% sensitivity.

**$P(T = 0 \mid D = 0)$** — the test's *specificity*. Of healthy people, what fraction test negative?

$$
P(T = 0 \mid D = 0) = \frac{0.94}{0.99} = 0.9495 \approx 0.95.
$$

About 95% of healthy people test negative. Specificity is 95%; equivalently the false positive rate is 5%.

**$P(D = 1 \mid T = 1)$** — what most people *want* to know: given a positive test, what's the probability of disease?

$$
P(D = 1 \mid T = 1) = \frac{P(D = 1, T = 1)}{P(T = 1)} = \frac{0.009}{0.059} \approx 0.153.
$$

About 15% of people who test positive actually have the disease. Most positives are false. This is the *Bayes-rule shock* — the same numerical fact we'll re-derive from scratch in Chapter 8, but it's already implicit in the joint table.

The huge gap between "the test is 90% sensitive and 95% specific" (which sounds great) and "15% of positive tests are real" (which sounds terrible) is one of the most important lessons in applied probability, and the reason this chapter has to come before Chapter 8.

### 7.4.4 The "conditional distribution" is a full distribution

For each value $y$ of $Y$, the conditional PMF $p_{X \mid Y}(x \mid y) = p_{X,Y}(x, y) / p_Y(y)$ is a complete probability distribution over $x$ — it satisfies the PMF conditions (non-negative, sums to 1 over $x$). The "sums to 1" claim is worth verifying:

$$
\sum_x p_{X \mid Y}(x \mid y) = \sum_x \frac{p_{X,Y}(x, y)}{p_Y(y)} = \frac{1}{p_Y(y)} \sum_x p_{X,Y}(x, y) = \frac{p_Y(y)}{p_Y(y)} = 1.
$$

The third equality used the marginalisation formula: $\sum_x p_{X,Y}(x, y) = p_Y(y)$.

So *for each value of the conditioning variable*, you get a fresh probability distribution over the conditioned variable. You can compute its mean (the **conditional expectation** $\mathbb{E}[X \mid Y = y]$), its variance, all the usual things.

---

## 7.5 The chain rule

A small but central piece of algebra. From the conditional probability definition $P(A \mid B) = P(A \cap B) / P(B)$, we can solve for the numerator:

$$
P(A \cap B) = P(A \mid B) \cdot P(B).
$$

For random variables:

$$
p_{X, Y}(x, y) = p_{X \mid Y}(x \mid y) \cdot p_Y(y).
$$

This is the **chain rule**. It is just the definition of conditional probability rearranged, but the rearrangement is so useful that it gets its own name.

You can also chain the other way: $P(A \cap B) = P(B \mid A) \cdot P(A)$. Both factorisations of $P(A \cap B)$ are valid. Equating them gives us Bayes' theorem — which is the subject of Chapter 8.

The chain rule generalises to more variables:

$$
P(A_1 \cap A_2 \cap A_3) = P(A_1) \cdot P(A_2 \mid A_1) \cdot P(A_3 \mid A_1 \cap A_2),
$$

and so on for any number. This generalisation is what licenses sequential reasoning — "first I observe $A_1$, then given that I observe $A_2$, then given both..." The chain rule lets you build up the joint probability of a sequence from the conditional probabilities of each step given the previous ones. Hidden Markov models, recurrent networks, autoregressive models all rest on this scaffolding.

---

## 7.6 Independence

If knowing $Y$ tells you nothing new about $X$, we say $X$ and $Y$ are **independent**. Formally:

$$
X \text{ and } Y \text{ are independent} \iff P(X = x, Y = y) = P(X = x) \cdot P(Y = y) \text{ for all } x, y.
$$

Equivalently (using the chain rule): $P(X = x \mid Y = y) = P(X = x)$ for all $y$ with $P(Y = y) > 0$. Knowing $Y$ doesn't change the distribution of $X$.

### 7.6.1 In the disease-test example, is $D$ independent of $T$?

Check: is $P(D = 1, T = 1) = P(D = 1) \cdot P(T = 1)$?

$P(D = 1, T = 1) = 0.009$.
$P(D = 1) \cdot P(T = 1) = 0.01 \cdot 0.059 = 0.00059$.

These are not equal. $D$ and $T$ are *not* independent — which is exactly what we'd hope. If the test were independent of the disease status, the test would be useless. The test's diagnostic value is precisely the *amount* of non-independence between $D$ and $T$.

### 7.6.2 Independent example: two fair coin flips

$X$ = first flip, $Y$ = second flip, each Bernoulli(0.5). The joint PMF is

| | $Y = 0$ | $Y = 1$ |
|---|---|---|
| $X = 0$ | 0.25 | 0.25 |
| $X = 1$ | 0.25 | 0.25 |

Marginals: $P(X = 0) = P(X = 1) = 0.5$, same for $Y$.

Check: $P(X = 0, Y = 0) = 0.25 = 0.5 \cdot 0.5 = P(X = 0) P(Y = 0)$. ✓ The two flips are independent.

### 7.6.3 What independence buys you

When $X$ and $Y$ are independent:

- $\mathbb{E}[XY] = \mathbb{E}[X] \mathbb{E}[Y]$. (Expectations of products factor for independent variables.)
- $\text{Var}[X + Y] = \text{Var}[X] + \text{Var}[Y]$. (Variances add.)
- Joint PMF/PDF factors: $p_{X, Y}(x, y) = p_X(x) p_Y(y)$. The whole joint distribution is determined by the two marginals.

These simplifications are why independence is such an important hypothesis. Whole methods (naive Bayes, the chi-squared independence test) rest on assuming or testing for it.

But independence is a *strong* assumption. Real-world variables are usually slightly correlated, and the question is how much.

---

## 7.7 Covariance

The natural number measuring "how $X$ and $Y$ move together" is the **covariance**:

$$
\text{Cov}[X, Y] = \mathbb{E}\left[(X - \mu_X)(Y - \mu_Y)\right],
$$

where $\mu_X = \mathbb{E}[X]$ and $\mu_Y = \mathbb{E}[Y]$.

Read it carefully. We take each variable's deviation from its mean, multiply them, and take the expectation of the product. If $X$ tends to be above its mean when $Y$ is above its mean (and below when below), the products $(X - \mu_X)(Y - \mu_Y)$ are mostly positive, so the expectation is positive — *positive covariance*. If $X$ is above its mean when $Y$ is below (and vice versa), the products are mostly negative — *negative covariance*. If $X$ and $Y$'s deviations are unrelated, the positives and negatives cancel — *zero covariance*.

### 7.7.1 Shortcut formula for covariance

By the same algebra as Chapter 5's variance shortcut:

$$
\text{Cov}[X, Y] = \mathbb{E}[XY] - \mathbb{E}[X]\mathbb{E}[Y].
$$

**Derivation.** Expand the product:

$$
\text{Cov}[X, Y] = \mathbb{E}[(X - \mu_X)(Y - \mu_Y)] = \mathbb{E}[XY - \mu_X Y - X \mu_Y + \mu_X \mu_Y].
$$

Use linearity:

$$
= \mathbb{E}[XY] - \mu_X \mathbb{E}[Y] - \mathbb{E}[X] \mu_Y + \mu_X \mu_Y.
$$

Since $\mathbb{E}[X] = \mu_X$ and $\mathbb{E}[Y] = \mu_Y$:

$$
= \mathbb{E}[XY] - \mu_X \mu_Y - \mu_X \mu_Y + \mu_X \mu_Y = \mathbb{E}[XY] - \mu_X \mu_Y. \quad \blacksquare
$$

So computing covariance reduces to computing $\mathbb{E}[XY]$ and subtracting $\mathbb{E}[X] \mathbb{E}[Y]$.

### 7.7.2 Special case: $X = Y$

What's $\text{Cov}[X, X]$? Plug in:

$$
\text{Cov}[X, X] = \mathbb{E}[(X - \mu_X)(X - \mu_X)] = \mathbb{E}[(X - \mu_X)^2] = \text{Var}[X].
$$

The variance is just the covariance of a variable with itself. This is one of those small unifying facts that makes a lot of subsequent derivations cleaner.

### 7.7.3 Variance of a sum, properly

We can now state the general formula for the variance of a sum, which we previewed in Chapter 5:

$$
\text{Var}[X + Y] = \text{Var}[X] + \text{Var}[Y] + 2 \text{Cov}[X, Y].
$$

**Derivation.** Let $\mu_X + \mu_Y = \mathbb{E}[X + Y]$ (linearity). Then

$$
\text{Var}[X + Y] = \mathbb{E}[((X + Y) - (\mu_X + \mu_Y))^2] = \mathbb{E}[((X - \mu_X) + (Y - \mu_Y))^2].
$$

Expand the square inside:

$$
= \mathbb{E}[(X - \mu_X)^2 + 2(X - \mu_X)(Y - \mu_Y) + (Y - \mu_Y)^2].
$$

Use linearity to split into three expectations:

$$
= \mathbb{E}[(X - \mu_X)^2] + 2 \mathbb{E}[(X - \mu_X)(Y - \mu_Y)] + \mathbb{E}[(Y - \mu_Y)^2].
$$

The three terms are, respectively, $\text{Var}[X]$, $2 \text{Cov}[X, Y]$, and $\text{Var}[Y]$:

$$
\text{Var}[X + Y] = \text{Var}[X] + \text{Var}[Y] + 2 \text{Cov}[X, Y]. \quad \blacksquare
$$

When $X$ and $Y$ are independent, $\text{Cov}[X, Y] = 0$ and variances add cleanly. When they aren't, the covariance is the correction term.

### 7.7.4 Independence implies zero covariance, but not the reverse

If $X$ and $Y$ are independent, then $\mathbb{E}[XY] = \mathbb{E}[X] \mathbb{E}[Y]$, so

$$
\text{Cov}[X, Y] = \mathbb{E}[XY] - \mathbb{E}[X]\mathbb{E}[Y] = 0.
$$

So independence ⇒ zero covariance. The converse, however, is *not* true in general. Two variables can have zero covariance and still be wildly dependent.

A classic example. Let $X$ be uniform on $\{-1, 0, 1\}$ and $Y = X^2$. Then $Y$ is a deterministic function of $X$ — they are about as dependent as variables can be. But:

$$
\mathbb{E}[X] = 0, \quad \mathbb{E}[Y] = \mathbb{E}[X^2] = (1 + 0 + 1)/3 = 2/3,
$$

$$
\mathbb{E}[XY] = \mathbb{E}[X^3] = (-1 + 0 + 1)/3 = 0,
$$

$$
\text{Cov}[X, Y] = 0 - 0 \cdot 2/3 = 0.
$$

Zero covariance, but $Y$ is entirely determined by $X$. The covariance only measures *linear* association. If the relationship between $X$ and $Y$ is nonlinear and symmetric (here, $Y$ grows on both sides of zero), the linear measure misses it entirely.

This is the second time we're meeting the rule: independent ⇒ uncorrelated, but uncorrelated does not imply independent. For jointly *normal* random variables it happens to be an iff (zero covariance does imply independence for joint normals), but in general it does not. Worth holding firmly.

---

## 7.8 Correlation

The covariance has a problem: it depends on the units of $X$ and $Y$. If $X$ is in dollars and $Y$ is in years, $\text{Cov}[X, Y]$ is in dollar-years, which is uninterpretable. Worse, multiplying $X$ by 1000 (changing units from dollars to thousandths-of-a-cent) multiplies the covariance by 1000 — the number changes although the *strength* of the relationship hasn't.

The fix: rescale. Divide by the standard deviations of $X$ and $Y$ to get a dimensionless number:

$$
\rho_{X, Y} = \frac{\text{Cov}[X, Y]}{\sigma_X \sigma_Y}.
$$

This is the **(Pearson) correlation coefficient**. It is unitless, scale-invariant, and — as we'll see — always between $-1$ and $1$.

### 7.8.1 Properties

- $\rho = 1$: $X$ and $Y$ are perfectly positively linearly related. $Y = aX + b$ for some $a > 0$.
- $\rho = -1$: perfectly negatively linearly related. $Y = aX + b$ for some $a < 0$.
- $\rho = 0$: zero linear association. (Not zero association — see the $X, X^2$ example above.)
- Intermediate values measure the strength of *linear* association.

### 7.8.2 Why $|\rho| \leq 1$ — sketch of the Cauchy-Schwarz argument

The boundedness of $\rho$ is one of the more elegant facts in elementary probability. It follows from a general inequality called the **Cauchy-Schwarz inequality**:

$$
|\mathbb{E}[UV]| \leq \sqrt{\mathbb{E}[U^2] \mathbb{E}[V^2]}
$$

for any random variables $U, V$ with finite second moments. The proof goes by considering $\mathbb{E}[(U - \lambda V)^2] \geq 0$ for any $\lambda$, which is a quadratic in $\lambda$ that must have a non-positive discriminant, which gives Cauchy-Schwarz.

Apply Cauchy-Schwarz to the centered variables $U = X - \mu_X$ and $V = Y - \mu_Y$:

$$
|\mathbb{E}[(X - \mu_X)(Y - \mu_Y)]| \leq \sqrt{\mathbb{E}[(X - \mu_X)^2] \mathbb{E}[(Y - \mu_Y)^2]}.
$$

The left-hand side is $|\text{Cov}[X, Y]|$. The right is $\sqrt{\text{Var}[X] \cdot \text{Var}[Y]} = \sigma_X \sigma_Y$. So:

$$
|\text{Cov}[X, Y]| \leq \sigma_X \sigma_Y \implies |\rho_{X, Y}| = \frac{|\text{Cov}[X, Y]|}{\sigma_X \sigma_Y} \leq 1.
$$

Equality holds in Cauchy-Schwarz iff $U$ and $V$ are proportional (one is a scalar multiple of the other), which translates to $Y$ being an affine function of $X$. So $|\rho| = 1$ ⇔ $Y = aX + b$ for some constants.

This is the cleanest way I know to see why correlation is bounded — and to see that "perfect correlation" is *exactly* "perfect linear relationship." For nonlinear relationships, the correlation falls below 1 even when the underlying dependence is perfect.

### 7.8.3 Correlation is not causation

A statement that is repeated so often it is in danger of becoming a slogan, but it deserves the airtime.

If $X$ and $Y$ are correlated, one of several possibilities holds:
- $X$ causes $Y$.
- $Y$ causes $X$.
- A third variable $Z$ causes both — they are correlated through $Z$, with no direct causal link between them.
- The correlation is a statistical fluke that will not survive new data.

Correlation does not, on its own, distinguish among these. Causal inference is a separate and substantial subfield — beyond the scope of this book — that builds on top of probability theory with additional structure (graphs, interventions, counterfactuals). When a stakeholder asks you "what causes the conversion rate to drop?" they are asking a causal question; a correlation-only ML model cannot, in general, answer it.

For ML evaluation purposes, correlation is fine — we want our model's predictions to correlate with the truth. For ML-driven decision-making in the real world ("do this intervention and the outcome will change in such-and-such way"), causality matters and you need to be more careful.

---

## 7.9 Joint, marginal, conditional in code

Time to make this tactile. We'll use NumPy to:

1. Generate samples from a known joint distribution (uncorrelated, positively correlated, negatively correlated).
2. Compute empirical covariance and correlation and compare with the theoretical values.
3. Visualise the joint and the marginals.

```python
import numpy as np

# Random number generator with fixed seed
rng = np.random.default_rng(seed=42)

# --- Two independent standard normals ---
n = 10_000
X = rng.normal(0, 1, size=n)
Y = rng.normal(0, 1, size=n)

# Empirical covariance and correlation
cov_XY = np.mean((X - X.mean()) * (Y - Y.mean()))
corr_XY = cov_XY / (X.std() * Y.std())
print(f"Independent: cov = {cov_XY:.4f}, corr = {corr_XY:.4f}")
# Expect cov ≈ 0, corr ≈ 0
```

This computes covariance from first principles. For more variables, NumPy has `np.cov` and `np.corrcoef`:

```python
# Built-in cov matrix
C = np.cov(np.stack([X, Y]))
print("Covariance matrix:\n", C)
# Diagonal entries are Var(X), Var(Y); off-diagonal is Cov(X, Y)
```

Now let's generate *correlated* normals. The standard trick: start with two independent normals, then form a linear combination.

```python
# Generate Y as a linear function of X plus independent noise
Z = rng.normal(0, 1, size=n)
Y_corr = 0.8 * X + np.sqrt(1 - 0.8**2) * Z   # designed to have corr(X, Y_corr) = 0.8

cov = np.cov(np.stack([X, Y_corr]))
corr = np.corrcoef(np.stack([X, Y_corr]))
print("Designed corr 0.8: empirical corr matrix =\n", corr)
```

Why does the construction `Y = 0.8 X + sqrt(1 - 0.8^2) Z` give correlation 0.8?

Quick derivation. Both $X$ and $Z$ are standard normal and independent, so $\text{Var}[X] = \text{Var}[Z] = 1$ and $\text{Cov}[X, Z] = 0$.

$$
\text{Var}[Y] = 0.8^2 \text{Var}[X] + (1 - 0.8^2) \text{Var}[Z] = 0.64 + 0.36 = 1.
$$

$$
\text{Cov}[X, Y] = \text{Cov}[X, 0.8 X + \sqrt{1 - 0.64} Z] = 0.8 \text{Var}[X] + 0 = 0.8.
$$

$$
\rho_{X, Y} = \frac{0.8}{1 \cdot 1} = 0.8.
$$

So we constructed it directly. Empirically, you should see a correlation very close to 0.8 (and as $n$ grows, closer and closer — LLN, see Chapter 9).

For more elaborate constructions — many variables with a specified covariance matrix — the standard technique is the **Cholesky decomposition**: factor $\Sigma = L L^T$ and form $Y = \mu + L Z$ where $Z$ is a standard multivariate normal. We'll meet this in Chapter 13 alongside matrix algebra.

For a visualisation, a scatter plot of $(X, Y_\text{corr})$ would show points clustered around a line with positive slope, with some spread perpendicular to it. The tighter the cluster, the higher the correlation.

---

## 7.10 Why this chapter matters for ML

A quick tour of the role these concepts will play in subsequent chapters.

- **Bayes' theorem** (Chapter 8) is the chain rule rearranged. You can't do Bayes without conditional probabilities being clear, and you can't do conditional probabilities without joint distributions being clear.
- **Logistic regression and Naive Bayes** (Chapters 32, 37) model the joint distribution $p(X, Y)$ — Naive Bayes explicitly, with strong independence assumptions; logistic regression implicitly, by directly modelling the conditional $p(Y \mid X)$.
- **The covariance matrix** of a multivariate distribution (Chapter 14) is the natural generalisation of variance to multiple variables. PCA is the eigendecomposition of the covariance matrix (Chapter 40).
- **Linear regression's normal-equations derivation** rests on covariances between features and the target.
- **Independence assumptions** in feature engineering — for example, "are these two features measuring different things?" — are quietly statements about covariance/correlation.
- **Drift detection** in production ML is about whether the joint distribution of inputs has shifted from training time to inference time.
- **Causal inference**, which we did not develop here but will reference, builds atop joints and conditionals.

Joint, marginal, conditional, independence — these are the four pillars of multivariate probability, and you will lean on each of them many times.

---

## 7.11 Summary

1. The **joint distribution** $p_{X, Y}(x, y)$ describes how two random variables interact. The **marginal** is recovered by summing (or integrating) the joint over the other variable. **Conditional** distributions come from the formula $P(A \mid B) = P(A \cap B) / P(B)$ — restrict to $B$ and renormalise.
2. The **chain rule** $p_{X, Y}(x, y) = p_{X \mid Y}(x \mid y) p_Y(y)$ is the conditional definition rearranged. It is the basis of Bayes' theorem and of sequential probabilistic models.
3. **Independence** of $X$ and $Y$ means the joint factors as the product of marginals: $p_{X, Y}(x, y) = p_X(x) p_Y(y)$. Equivalently, $P(X = x \mid Y = y) = P(X = x)$ — conditioning doesn't change anything.
4. **Covariance** $\text{Cov}[X, Y] = \mathbb{E}[(X - \mu_X)(Y - \mu_Y)] = \mathbb{E}[XY] - \mathbb{E}[X]\mathbb{E}[Y]$ measures linear co-movement. Variance is covariance with itself.
5. The general variance of a sum: $\text{Var}[X + Y] = \text{Var}[X] + \text{Var}[Y] + 2 \text{Cov}[X, Y]$. Independence reduces this to additive.
6. **Correlation** $\rho = \text{Cov}[X, Y] / (\sigma_X \sigma_Y)$ is the dimensionless, scale-free version. By Cauchy-Schwarz, $|\rho| \leq 1$, with equality iff $Y = aX + b$.
7. **Independence implies zero correlation; the reverse is not true.** Correlation captures linear association only; non-linear dependencies can give zero correlation despite total functional determinism.
8. **Correlation is not causation.** A statement easily made, harder to internalise. Building a model on correlations and acting on it causally is a recipe for nasty surprises.

---

## 7.12 What this builds on / where this returns

**Builds on:** Chapter 5 (single random variables, expectation, variance) and Chapter 6 (specific distributions — Bernoulli is the alphabet of the joint examples here).

**Returns:**

- **Conditional probability** is the engine of *Chapter 8* (Bayes' theorem) and of *Chapter 37* (Naive Bayes).
- **Covariance** and the **covariance matrix** return in *Chapter 14* (eigenvalues of the covariance matrix) and *Chapter 40* (PCA derivation as eigendecomposition of covariance).
- **Variance of a sum with covariance** is used in *Chapter 9* (the variance of a sample mean — and the appearance of the $\sqrt{n}$ in the standard error).
- **Independence assumptions** show up in *Chapter 37* (Naive Bayes assumes class-conditional independence of features), *Chapter 22* (CV folds assumed independent), and throughout Part L (drift detection).
- **Correlation as scale-free dependence** measure is used as a feature-feature similarity check in *Chapter 23* (EDA) and *Chapter 29* (feature selection).
- **Correlation vs. causation** is referenced in the broader discussion of fairness and feature engineering in *Part E*.

---

## 7.13 Exercises

1. **Marginal from joint.** The joint PMF of $(X, Y)$ is given by the table:

   | | Y=0 | Y=1 | Y=2 |
   |---|---|---|---|
   | X=0 | 0.1 | 0.2 | 0.1 |
   | X=1 | 0.15 | 0.25 | 0.2 |

   Compute the marginal distributions of $X$ and $Y$.

2. **Conditional from joint.** Using the table from question 1, compute $P(Y = 1 \mid X = 1)$ and $P(X = 0 \mid Y = 2)$.

3. **Independence check.** Are $X$ and $Y$ in question 1 independent? Justify by checking a single cell against the product of the marginals.

4. **The disease test re-examined.** Using the joint table from section 7.2.2, compute (a) the sensitivity, (b) the specificity, (c) the positive predictive value $P(D = 1 \mid T = 1)$, and (d) the negative predictive value $P(D = 0 \mid T = 0)$. Comment on which two of these are usually quoted by test manufacturers and which two patients actually want to know.

5. **Variance addition.** Two iid random variables $X$ and $Y$ each have variance 5. What is $\text{Var}[X + Y]$? What is $\text{Var}[X - Y]$? Justify using the variance-of-a-sum formula.

6. **Covariance from a joint table.** Compute $\text{Cov}[X, Y]$ and $\rho_{X, Y}$ for the joint distribution in question 1.

7. **Zero covariance, full dependence.** Verify by direct computation that if $X$ takes values $\{-1, 0, 1\}$ each with probability $1/3$ and $Y = X^2$, then $\text{Cov}[X, Y] = 0$ even though $Y$ is a deterministic function of $X$. Discuss why this happens.

8. **Linear relationship gives $\rho = 1$.** Show that if $Y = 3X + 5$, then $\rho_{X, Y} = 1$, regardless of the distribution of $X$. (Compute $\text{Cov}[X, Y]$ and $\text{Var}[Y]$ in terms of $\text{Var}[X]$.)

9. **A correlation of $-1$.** Construct an explicit example with $\rho_{X, Y} = -1$, using a simple discrete random variable for $X$.

10. **Chain rule application.** A user visits a website. With probability 0.7, the home page loads (event $A$). Given that the home page loads, with probability 0.3, the user clicks a particular ad (event $B$). Given that both happen, with probability 0.1, the user makes a purchase (event $C$). What is $P(A \cap B \cap C)$?

11. **Code computation.** Using NumPy, generate 10,000 samples of $(X, Y)$ where $X \sim N(0, 1)$ and $Y = 0.5 X + \text{noise}$, with noise iid standard normal. Compute the empirical covariance and correlation. Predict their theoretical values, then compare.

12. **What can correlation miss?** Give two real-world examples (different from the $Y = X^2$ one in the text) of pairs of variables that you would intuitively call "strongly dependent" but which would have low Pearson correlation.

<details>
<summary>Answers</summary>

1. Marginal $P(X)$: $P(X = 0) = 0.1 + 0.2 + 0.1 = 0.4$, $P(X = 1) = 0.15 + 0.25 + 0.2 = 0.6$. Marginal $P(Y)$: $P(Y=0) = 0.25$, $P(Y=1) = 0.45$, $P(Y=2) = 0.3$.

2. $P(Y = 1 \mid X = 1) = P(Y = 1, X = 1) / P(X = 1) = 0.25 / 0.6 \approx 0.417$. $P(X = 0 \mid Y = 2) = P(X = 0, Y = 2) / P(Y = 2) = 0.1 / 0.3 \approx 0.333$.

3. Not independent. For independence we need $P(X = x, Y = y) = P(X = x) P(Y = y)$ for all cells. Check the cell $(0, 0)$: joint is 0.1, product of marginals is $0.4 \cdot 0.25 = 0.10$. That cell happens to match! But cell $(0, 1)$: joint is 0.2, product is $0.4 \cdot 0.45 = 0.18$ — doesn't match. So not independent (a single mismatched cell suffices to break independence).

4. (a) Sensitivity = $P(T=1 \mid D=1) = 0.009 / 0.01 = 0.9$. (b) Specificity = $P(T=0 \mid D=0) = 0.94 / 0.99 \approx 0.949$. (c) PPV = $P(D=1 \mid T=1) = 0.009 / 0.059 \approx 0.153$. (d) NPV = $P(D=0 \mid T=0) = 0.94 / 0.941 \approx 0.999$. Manufacturers quote sensitivity and specificity (intrinsic to the test, not the population). Patients want PPV and NPV (which depend on prevalence). The mismatch between "the test is 90/95% accurate" and "only 15% of positives are real" is the gist of the Bayesian-disease intuition.

5. For independent (and hence uncorrelated) iid variables: $\text{Var}[X + Y] = 5 + 5 + 2 \cdot 0 = 10$. $\text{Var}[X - Y] = \text{Var}[X] + \text{Var}[-Y] + 2 \text{Cov}[X, -Y] = 5 + 5 + 0 = 10$. (Note $\text{Var}[-Y] = \text{Var}[Y] = 5$; the negative cancels in the variance.) Subtracting independent variables increases variance just as much as adding does.

6. $\mathbb{E}[X] = 0 \cdot 0.4 + 1 \cdot 0.6 = 0.6$. $\mathbb{E}[Y] = 0 \cdot 0.25 + 1 \cdot 0.45 + 2 \cdot 0.3 = 1.05$. $\mathbb{E}[XY] = (0)(0)(0.1) + (0)(1)(0.2) + (0)(2)(0.1) + (1)(0)(0.15) + (1)(1)(0.25) + (1)(2)(0.2) = 0.25 + 0.4 = 0.65$. $\text{Cov} = 0.65 - 0.6 \cdot 1.05 = 0.65 - 0.63 = 0.02$. For $\rho$, compute $\text{Var}[X] = 0.6 \cdot 0.4 = 0.24$ and $\text{Var}[Y] = \mathbb{E}[Y^2] - (\mathbb{E}[Y])^2 = (0 \cdot 0.25 + 1 \cdot 0.45 + 4 \cdot 0.3) - 1.05^2 = 1.65 - 1.1025 = 0.5475$. $\rho = 0.02 / \sqrt{0.24 \cdot 0.5475} \approx 0.02 / 0.362 \approx 0.055$. Small positive correlation.

7. $\mathbb{E}[X] = 0$. $\mathbb{E}[Y] = \mathbb{E}[X^2] = 2/3$. $\mathbb{E}[XY] = \mathbb{E}[X^3] = ((-1)^3 + 0^3 + 1^3)/3 = 0$. $\text{Cov} = 0 - 0 \cdot 2/3 = 0$. Despite $Y$ being a function of $X$, the correlation is zero. The reason is symmetry — positive deviations in $X$ and negative deviations in $X$ both give the same $Y$, so the linear measure can't see the relationship.

8. $\mathbb{E}[Y] = 3 \mathbb{E}[X] + 5$. $\text{Cov}[X, Y] = \mathbb{E}[(X - \mu_X)(Y - 3\mu_X - 5)] = \mathbb{E}[(X - \mu_X)(3(X - \mu_X))] = 3 \text{Var}[X]$. $\text{Var}[Y] = 9 \text{Var}[X]$. So $\rho = 3\text{Var}[X] / \sqrt{\text{Var}[X] \cdot 9 \text{Var}[X]} = 3 \text{Var}[X] / (3 \text{Var}[X]) = 1$.

9. Let $X$ be uniform on $\{-1, 1\}$ and $Y = -X$. Then $Y = aX + b$ with $a = -1$, so $\rho = -1$.

10. By the chain rule: $P(A \cap B \cap C) = P(A) \cdot P(B \mid A) \cdot P(C \mid A \cap B) = 0.7 \cdot 0.3 \cdot 0.1 = 0.021$. About 2.1%.

11. Theoretically: $\text{Var}[X] = 1$, $\text{Var}[Y] = 0.25 \cdot 1 + 1 = 1.25$, $\text{Cov}[X, Y] = 0.5 \cdot \text{Var}[X] = 0.5$, $\rho = 0.5 / \sqrt{1 \cdot 1.25} \approx 0.447$. Empirical values from 10,000 samples should be very close, within ±0.01 of the theoretical.

12. Examples: (a) Height of a person and the day of year they were born — no relationship, but a periodic dependence (slightly more births in some months) wouldn't show up linearly. (b) The relationship between a stock's return today and its return three months from now (could be nonlinear, threshold-driven). (c) "Number of bedrooms in a house" and "house price per square foot" — these can be related but nonmonotonically (1-bedrooms are higher PSF than 4-bedrooms because of small-unit premium; 5-bedrooms are higher PSF than 4-bedrooms because of luxury). Many real-world relationships are non-monotonic; Pearson misses them.

</details>
