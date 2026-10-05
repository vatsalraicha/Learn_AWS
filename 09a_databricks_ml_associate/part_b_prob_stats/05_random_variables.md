# Chapter 5 — Random Variables, Distributions, Expectation, Variance

> **Goal of this chapter:** to put a careful, mathematical foundation under everything that was hand-waved in Part A. In Chapter 3 we said logistic regression "outputs a probability between 0 and 1." We used the word "probability" as if its meaning were obvious. It is not. By the end of this chapter you will be able to say, with precision, what a probability *is*, what a random variable *is*, how expectations and variances are computed, and why the linearity of expectation is one of the most useful facts in all of probability. The math here is not optional. Every loss function in Part D is an expectation in disguise; every confidence interval in Chapter 10 is a statement about a variance; every Bayesian computation in Chapter 8 lives on top of this scaffolding.
>
> If you have never sat down and worked through this material before, take your time. The Part-A vocabulary you absorbed informally — "the model's probability of spam is 0.73" — is about to be rebuilt from below.

---

## 5.1 The motivating question: what *is* a probability?

In Chapter 3 we trained a logistic regression model and said it outputs a number $\hat{p}(\text{spam} \mid x) \in [0, 1]$ which we interpreted as "the probability that this email is spam." We then set a threshold at $\tau = 0.7$, picked an operating point on the precision-recall curve, and shipped a service.

At no point did we ask: when the model says "0.73", what does that number *mean*? It is not the count of anything we directly observed. It is not a measurement, like the email's length in tokens. The email either is spam (label 1) or it isn't (label 0); there is no "0.73-spamness" hiding inside it. Yet the number is real, and it carries real predictive content — when we group all the emails the model scored at exactly 0.73 and check, we find that roughly 73% of them really were spam. Some kind of statement is being made; we owe ourselves a careful account of what kind.

The account exists. It was given its modern form by Andrey Kolmogorov in 1933, and it is the foundation of every applied probability calculation done since. We start there, not because the Databricks exam tests measure theory (it doesn't), but because every shortcut in applied probability is licensed by something at the foundation, and confusion about probabilities in ML is almost always confusion about which licence the practitioner is using.

So: what is a probability?

---

## 5.2 Sample spaces, events, and the axioms

### 5.2.1 The sample space

Every probability statement starts with a **sample space** $\Omega$ — the set of all possible outcomes of whatever random procedure you have in mind.

For a single coin flip: $\Omega = \{H, T\}$. Two outcomes, both physical.

For a single die roll: $\Omega = \{1, 2, 3, 4, 5, 6\}$.

For two coin flips: $\Omega = \{HH, HT, TH, TT\}$.

For the height of a randomly chosen adult: $\Omega = (0, \infty)$ — every positive real number, in principle. (No adult is exactly 0 or exactly infinite; the open interval is a slight idealisation.)

For an email arriving at our spam classifier: $\Omega$ is the set of every possible email — every combination of subject text, body text, sender, attachments, timestamp. Astronomically large; uncountably infinite if we allow free-form text. We rarely write $\Omega$ down explicitly for problems this messy, but it exists conceptually.

### 5.2.2 Events

An **event** is a subset of the sample space. For the die roll, the event "rolled an even number" is the set $\{2, 4, 6\} \subset \Omega$. The event "rolled at least 5" is $\{5, 6\}$. The event "rolled a 7" is the empty set $\emptyset$ — possible to write down, impossible to occur.

For our spam classifier, the event "this email is spam" is the subset of all possible emails for which the spam label is 1.

### 5.2.3 The axioms

A **probability** is a function $P$ that takes an event and returns a number, subject to three rules that Kolmogorov laid down:

1. **Non-negativity:** $P(A) \geq 0$ for any event $A$. Probabilities are never negative.
2. **Normalisation:** $P(\Omega) = 1$. The probability that *something* happens is 1.
3. **Countable additivity:** if $A_1, A_2, A_3, \ldots$ are pairwise disjoint events (no two share any outcome), then $P(A_1 \cup A_2 \cup \ldots) = P(A_1) + P(A_2) + \ldots$.

That's it. Three rules. Everything else in probability — Bayes' theorem, expectations, variances, the central limit theorem — is derived from these three. Worth pausing on, because most of the time when a probability calculation feels confusing, the way out is to step back to these three rules and check what they license.

For the fair die: $P(\{i\}) = 1/6$ for each $i \in \{1, \ldots, 6\}$. By rule 3, $P(\{2, 4, 6\}) = P(\{2\}) + P(\{4\}) + P(\{6\}) = 1/6 + 1/6 + 1/6 = 1/2$. Even-number-rolling has probability 1/2. The arithmetic is trivial; the licensing principle isn't.

### 5.2.4 Frequentist and Bayesian readings — a brief detour

The axioms don't tell you what a probability *means* in the world. There are two main interpretations, and serious people have written long books arguing about them.

The **frequentist** reading: $P(A)$ is the long-run fraction of times $A$ occurs if you repeat the experiment many times. $P(\text{heads}) = 0.5$ for a fair coin means that in a million flips, about half a million will be heads. This is the dominant reading in classical statistics and in most ML evaluation.

The **Bayesian** reading: $P(A)$ is a *degree of belief* that $A$ will occur, updateable as evidence arrives. $P(\text{this email is spam} \mid \text{contents}) = 0.73$ is your rational confidence, given what you know. This reading is closer to how the spam classifier's output is used in practice.

Both readings satisfy Kolmogorov's axioms, and most of this book will not depend on which one you adopt. We will, however, take the Bayesian reading seriously when we get to Bayes' theorem in Chapter 8.

---

## 5.3 Random variables, formally

Now we can define a random variable properly. The informal version: a random variable is "a number whose value depends on the outcome of some random procedure." The formal version is slightly more careful.

A **random variable** $X$ is a function from the sample space to the real numbers:

$$
X: \Omega \to \mathbb{R}.
$$

For each outcome $\omega \in \Omega$, $X(\omega)$ is the number we associate with that outcome.

This sounds abstract; in practice it is so natural that you've been doing it for years without noticing. Examples:

- **Die roll.** $\Omega = \{1, 2, 3, 4, 5, 6\}$ and we let $X(\omega) = \omega$. The random variable is just the number on the die. Could it have been something else? Sure — we could define $Y(\omega) = 1$ if $\omega$ is even, $Y(\omega) = 0$ if $\omega$ is odd. Same sample space, different random variable.

- **Two coin flips.** $\Omega = \{HH, HT, TH, TT\}$. Define $X$ = "number of heads." Then $X(HH) = 2$, $X(HT) = 1$, $X(TH) = 1$, $X(TT) = 0$. The random variable has collapsed the four outcomes into three numerical values.

- **Spam classifier.** The sample space is all emails. Define $Y(\omega) = 1$ if email $\omega$ is spam, $0$ otherwise. This is the *label* — and yes, the label is a random variable, because which email you'll see next is, from the model's point of view, random.

The mental shift to make: in probability theory, "a random variable" is not a value, and it is not a number. It is a *function*. The value it takes on any particular outcome is a number, but the random variable itself is the rule that assigns numbers to outcomes.

A useful piece of notation: $P(X = x)$ is shorthand for $P(\{\omega \in \Omega : X(\omega) = x\})$ — the probability of the event consisting of all outcomes that $X$ maps to the value $x$. We will use this shorthand constantly.

### 5.3.1 Discrete vs. continuous random variables

The dichotomy that matters for everything that follows: is the random variable's range *discrete* (a finite or countably infinite set, like $\{0, 1, 2, \ldots\}$) or *continuous* (an interval of real numbers, like $[0, 1]$ or all of $\mathbb{R}$)?

Discrete examples: number of heads in two flips; outcome of a die; number of customers arriving in an hour; the binary label "is this email spam?"; the count of times the word "viagra" appears in an email.

Continuous examples: height of a randomly chosen adult; tomorrow's high temperature; the exact time a customer arrived; the score $z = \mathbf{w} \cdot \mathbf{x} + b$ produced by a logistic regression *before* the sigmoid (this can be any real number); the output of the sigmoid (a number in $(0, 1)$).

The mathematical machinery for the two cases is *almost* parallel — same intuitions, same definitions — but differs in one important way that beginners regularly get wrong. We handle each separately.

---

## 5.4 Discrete random variables: the PMF

For a discrete random variable $X$, we describe its behaviour with a **probability mass function** (PMF):

$$
p_X(x) = P(X = x).
$$

The PMF is just a list, one entry per possible value, telling you the probability that $X$ equals that value. For a fair die, the PMF is:

$$
p_X(1) = p_X(2) = p_X(3) = p_X(4) = p_X(5) = p_X(6) = \frac{1}{6}.
$$

For the "number of heads in two flips" random variable from earlier, the PMF is:

$$
p_X(0) = \frac{1}{4}, \quad p_X(1) = \frac{2}{4} = \frac{1}{2}, \quad p_X(2) = \frac{1}{4}.
$$

(The 1/2 comes from there being two outcomes — $HT$ and $TH$ — that produce the value 1.)

A PMF must satisfy two conditions, which fall out of Kolmogorov's axioms:

1. $p_X(x) \geq 0$ for every $x$.
2. $\sum_x p_X(x) = 1$, where the sum is over all values $X$ can take.

If you ever write down a "probability distribution" whose values are negative, or that doesn't sum to 1, you have made a mistake. Sanity-check by summing.

### 5.4.1 Reading the PMF as a histogram

A useful mental picture: the PMF is a bar chart. The $x$-axis lists possible values; the $y$-axis is the probability of each. Total area = 1.

```
   p_X(x)
    │
1/2 ┤            █
    │            █
1/4 ┤    █       █       █
    │    █       █       █
    └────┴───────┴───────┴────► x
         0       1       2
       "no       "one    "two
       heads"   head"   heads"
```

The height of each bar is *the actual probability*. Two heads happens 25% of the time. You can read it directly off the chart.

This will not be true for continuous random variables, which is one of the most common sources of confusion. Hold on to it.

---

## 5.5 Continuous random variables: the PDF

For a continuous random variable $X$, there is a subtlety. If $X$ is, say, the height of a randomly chosen adult — taking values in $(0, \infty)$ — then for any *specific* value $h$, we have $P(X = h) = 0$.

This sounds wrong at first. Surely the probability that a randomly chosen adult is exactly 1.75 metres tall is not zero?

It is. *Exactly* 1.75 metres means 1.75000000... metres, an infinitely precise measurement. Among the uncountably many possible heights, the probability of landing on any single one is zero — there are "too many" alternatives. What is non-zero is the probability that the height lies in an *interval*: $P(1.74 < X < 1.76)$ might be 5%, and $P(1.7499 < X < 1.7501)$ might be 0.05%, and so on, shrinking continuously as the interval shrinks.

The object that captures this is the **probability density function** (PDF), conventionally written $f_X(x)$.

The defining property of the PDF: for any interval $[a, b]$,

$$
P(a \leq X \leq b) = \int_a^b f_X(x) \, dx.
$$

The PDF is a *density*, not a probability. To get a probability, you integrate it over an interval. The PDF itself can take values greater than 1 — that's fine, because it's a density, and you only get probabilities by accumulating area.

The PDF satisfies:

1. $f_X(x) \geq 0$ for every $x$.
2. $\int_{-\infty}^{\infty} f_X(x) \, dx = 1$.

Compare with the PMF conditions: same structure, with summation replaced by integration. The mathematics is the same idea applied to a continuous range.

### 5.5.1 The PMF-vs-PDF confusion, named explicitly

Here is the trap to avoid: **$f_X(x)$ is not a probability**. It is a density. If you read a normal-distribution textbook plot and see $f_X(0) = 0.4$ for a standard normal, that does *not* mean "the probability of $X = 0$ is 0.4." That probability is zero. What it means is that the density at 0 is 0.4, so the probability of falling in a tiny window around 0 of width $\Delta x$ is approximately $0.4 \cdot \Delta x$.

This is exactly the kind of distinction that gets glossed over in applied work and that bites you when you start trying to do things like compute likelihoods. A likelihood under a continuous distribution is a *density* evaluated at the observation, not a probability — which is why "the likelihood is 17" is a perfectly sensible thing for software to print and why it confuses people who expect probabilities.

```
PMF                              PDF
(discrete X)                     (continuous X)

  height = probability             height = density (not probability!)
  sum = 1                          area under curve = 1
  P(X=x) is the bar height         P(X=x) = 0 for any single x
                                   P(a ≤ X ≤ b) = area between a and b
```

Get this distinction firmly in hand. It will come up in every subsequent chapter.

---

## 5.6 The cumulative distribution function

A unifying object that works for both discrete and continuous cases is the **cumulative distribution function** (CDF):

$$
F_X(x) = P(X \leq x).
$$

The CDF tells you the probability that $X$ takes a value less than or equal to $x$. It is defined for every real $x$, regardless of whether $X$ is discrete or continuous. It is:

- monotonically non-decreasing (as $x$ grows, $F_X(x)$ never decreases — you're adding probability to the running total);
- bounded below by 0 (as $x \to -\infty$) and above by 1 (as $x \to \infty$);
- step-like for discrete RVs (jumps of size $p_X(x)$ at each value $X$ can take);
- continuous for continuous RVs (no jumps).

For our die-roll random variable:

| $x$  | $F_X(x) = P(X \leq x)$ |
|-----:|----:|
| 0.5  | 0   |
| 1    | 1/6 |
| 2    | 2/6 |
| 3    | 3/6 |
| 4    | 4/6 |
| 5    | 5/6 |
| 6    | 1   |
| 7    | 1   |

The CDF jumps up by 1/6 at each integer 1 through 6 and is flat in between.

For a continuous $X$ with PDF $f_X$, the CDF is the running integral:

$$
F_X(x) = \int_{-\infty}^{x} f_X(t) \, dt.
$$

Differentiating recovers the PDF: $f_X(x) = F_X'(x)$. The CDF and the PDF carry exactly the same information; you can convert between them at will.

The CDF is enormously useful in practice because:
- Probabilities of intervals come from CDF differences: $P(a < X \leq b) = F_X(b) - F_X(a)$. No integration needed if you have the CDF.
- Many test statistics and quantile computations are expressed in CDF terms.
- The CDF is what lets you simulate samples from a distribution given uniform random numbers (the "inverse-CDF method").

---

## 5.7 Expectation

We arrive at the most useful single concept in this chapter.

### 5.7.1 Discrete expectation

The **expectation** (or **expected value**, or **mean**) of a discrete random variable $X$ is

$$
\mathbb{E}[X] = \sum_x x \cdot p_X(x).
$$

In words: multiply each possible value by its probability, sum the lot. It is a *weighted average*, where the weights are probabilities.

For our die: $\mathbb{E}[X] = 1 \cdot \frac{1}{6} + 2 \cdot \frac{1}{6} + 3 \cdot \frac{1}{6} + 4 \cdot \frac{1}{6} + 5 \cdot \frac{1}{6} + 6 \cdot \frac{1}{6} = \frac{21}{6} = 3.5$.

The expectation is $3.5$ — a value the die *cannot actually take*. This is one of the routine surprises about expectations: the expected value need not be a value the random variable can attain. It's the long-run average of many rolls, not a prediction of any single roll. If you rolled 1 million dice and averaged, you'd get something very close to 3.5.

For our two-coin random variable (number of heads):

$$
\mathbb{E}[X] = 0 \cdot \frac{1}{4} + 1 \cdot \frac{1}{2} + 2 \cdot \frac{1}{4} = 0 + 0.5 + 0.5 = 1.
$$

In two flips, you expect (on average) one head. Matches intuition.

### 5.7.2 Continuous expectation

For continuous $X$ with PDF $f_X$:

$$
\mathbb{E}[X] = \int_{-\infty}^{\infty} x \cdot f_X(x) \, dx.
$$

Same idea — value times probability density, accumulated over the range. The sum becomes an integral; everything else is parallel.

### 5.7.3 Expectation as a "center of mass"

A geometric reading: if you imagine the PMF (or PDF) as a mass distribution along the real line, the expectation is the point where that distribution balances. Put a unit weight at each value of $X$ proportional to its probability; the expectation is the fulcrum that makes the seesaw level.

This intuition explains why $\mathbb{E}[X] = 3.5$ for the die — symmetric distribution, balance point in the middle. It also explains why for a highly skewed distribution (say, household incomes, with a long right tail), the mean is to the right of the median; the rare-but-extreme right tail pulls the balance point.

---

## 5.8 Linearity of expectation — the most useful theorem of the chapter

Here is a fact whose usefulness is hard to overstate. For *any* random variables $X$ and $Y$ and any real constants $a$ and $b$:

$$
\mathbb{E}[aX + b] = a \mathbb{E}[X] + b
$$

and more generally,

$$
\mathbb{E}[X + Y] = \mathbb{E}[X] + \mathbb{E}[Y].
$$

These two facts together — scalar multiplication and addition both pass through the expectation — are called the **linearity of expectation**. Crucially, the additivity holds *whether or not $X$ and $Y$ are independent*. This is going to be useful repeatedly.

### 5.8.1 Proof of $\mathbb{E}[aX + b] = a\mathbb{E}[X] + b$

Let's do the discrete case carefully and you can take the continuous case on faith (it's the same argument with integrals).

Start from the definition:

$$
\mathbb{E}[aX + b] = \sum_x (ax + b) \cdot p_X(x).
$$

Why is this the right expression? Because $aX + b$ is itself a random variable: when $X$ takes the value $x$, $aX + b$ takes the value $ax + b$, with the same probability $p_X(x)$. So the expectation of $aX + b$ sums each value-it-can-take times its probability, which is exactly what we wrote.

Now distribute the sum:

$$
\sum_x (ax + b) \cdot p_X(x) = \sum_x ax \cdot p_X(x) + \sum_x b \cdot p_X(x).
$$

Pull constants out of the sums:

$$
= a \sum_x x \cdot p_X(x) + b \sum_x p_X(x).
$$

The first sum is the definition of $\mathbb{E}[X]$. The second sum is $\sum_x p_X(x) = 1$ (the PMF sums to 1). So:

$$
\mathbb{E}[aX + b] = a \mathbb{E}[X] + b \cdot 1 = a \mathbb{E}[X] + b. \quad \blacksquare
$$

That's the whole proof. Three lines of algebra, one application of the PMF axiom. Worth holding onto: every "step" was either a definition or pulling a constant out of a sum.

### 5.8.2 Proof of $\mathbb{E}[X + Y] = \mathbb{E}[X] + \mathbb{E}[Y]$

This one requires joint distributions, which we treat carefully in Chapter 7, but here is the sketch.

If $X$ and $Y$ are both defined on the same sample space $\Omega$, then $X + Y$ is also a random variable on $\Omega$, with $(X+Y)(\omega) = X(\omega) + Y(\omega)$. The expectation of $X + Y$ is, by definition,

$$
\mathbb{E}[X + Y] = \sum_\omega (X(\omega) + Y(\omega)) \cdot P(\{\omega\}).
$$

(For now think of $\Omega$ as discrete; the continuous version uses integrals.) Distribute the sum:

$$
= \sum_\omega X(\omega) \cdot P(\{\omega\}) + \sum_\omega Y(\omega) \cdot P(\{\omega\}) = \mathbb{E}[X] + \mathbb{E}[Y].
$$

Done. Note that we *never used independence* — the joint behaviour of $X$ and $Y$ doesn't show up. Even if they are highly correlated, the expectation of their sum is the sum of their expectations.

By induction, $\mathbb{E}[X_1 + X_2 + \ldots + X_n] = \mathbb{E}[X_1] + \mathbb{E}[X_2] + \ldots + \mathbb{E}[X_n]$ for any collection. This generalisation is what makes linearity of expectation so much more useful than it first appears: hard sums of correlated things become easy.

### 5.8.3 Why this matters in ML

In Part D, we will define a **loss function** as the expected error of a model:

$$
\text{risk}(f) = \mathbb{E}[L(f(X), Y)].
$$

The training procedure approximates this expectation with the average loss on the training set. The whole gradient-descent enterprise — taking derivatives of the loss, updating parameters — relies on the fact that derivatives and expectations commute (the linearity argument again, applied to expectations of derivatives). Without linearity of expectation, modern ML's mathematical scaffolding doesn't hold together.

---

## 5.9 Variance and standard deviation

Expectation tells you the center. It does not tell you the *spread*. Two random variables can have the same mean but very different distributions:

- $X$: always equal to 5. Mean: 5. Spread: zero.
- $Y$: equal to 0 with probability 1/2 and 10 with probability 1/2. Mean: 5. Spread: large.

We need a way to quantify spread. The standard tool is the **variance**.

### 5.9.1 Definition

$$
\text{Var}[X] = \mathbb{E}\left[(X - \mu)^2\right], \quad \text{where } \mu = \mathbb{E}[X].
$$

In words: the variance is the expected squared deviation of $X$ from its mean. Larger when $X$ tends to be far from its mean; zero when $X$ is constant.

Why squared? Three reasons. First, $(X - \mu)$ can be positive or negative; squaring makes everything positive so they don't cancel. Second, squaring penalises large deviations more than small ones, which is often what we want. Third — and this is the deep reason — squaring leads to clean algebra. Many of probability's nicest identities (CLT, the bias-variance decomposition, OLS) depend on the squared-deviation form. Using absolute deviation $|X - \mu|$ would also measure spread, but the math is harder.

### 5.9.2 The standard deviation

The variance has units of "$X$-squared." If $X$ is in dollars, $\text{Var}[X]$ is in dollars-squared, which is not a unit you can read off a chart. The **standard deviation** brings it back to the original units:

$$
\sigma_X = \sqrt{\text{Var}[X]}.
$$

Standard deviation is the more interpretable cousin: roughly, "a typical distance of $X$ from its mean." When we report "the average IQ is 100 with a standard deviation of 15," we mean that most people are within 15 IQ points of 100.

### 5.9.3 The computational shortcut

A formula you will use constantly:

$$
\text{Var}[X] = \mathbb{E}[X^2] - (\mathbb{E}[X])^2.
$$

This is the **variance shortcut formula**. It is often easier than computing $\mathbb{E}[(X - \mu)^2]$ directly because computing $\mathbb{E}[X^2]$ requires only the original distribution, not the centered one.

Derivation (this is one to actually do step by step):

$$
\text{Var}[X] = \mathbb{E}[(X - \mu)^2]
$$

Expand the square:

$$
= \mathbb{E}[X^2 - 2\mu X + \mu^2].
$$

Use linearity of expectation to split the sum into three pieces:

$$
= \mathbb{E}[X^2] - \mathbb{E}[2\mu X] + \mathbb{E}[\mu^2].
$$

The middle term: $2\mu$ is a constant (it's just the number $\mu$ times 2), so $\mathbb{E}[2\mu X] = 2\mu \mathbb{E}[X] = 2\mu \cdot \mu = 2\mu^2$.

The last term: $\mu^2$ is a constant. The expectation of a constant is itself: $\mathbb{E}[\mu^2] = \mu^2$.

Substituting:

$$
\text{Var}[X] = \mathbb{E}[X^2] - 2\mu^2 + \mu^2 = \mathbb{E}[X^2] - \mu^2.
$$

Since $\mu = \mathbb{E}[X]$:

$$
\text{Var}[X] = \mathbb{E}[X^2] - (\mathbb{E}[X])^2. \quad \blacksquare
$$

Every line was either a definition, an algebraic expansion, or a use of linearity of expectation. No magic.

### 5.9.4 Variance is *not* linear

Here is where variance differs sharply from expectation. We have:

$$
\text{Var}[aX + b] = a^2 \text{Var}[X].
$$

Notice three things. First, the constant $b$ disappears — adding a constant doesn't change the spread. Second, the scalar $a$ comes out *squared* — scaling $X$ by 2 makes the variance 4 times larger (the spread doubles, and we measure spread squared). Third, this rule is *not* additive in the way expectation is.

Let's prove it. Let $Y = aX + b$ with $\mu_Y = \mathbb{E}[Y] = a\mu_X + b$ (by linearity of expectation). Then

$$
\text{Var}[Y] = \mathbb{E}[(Y - \mu_Y)^2] = \mathbb{E}[(aX + b - a\mu_X - b)^2] = \mathbb{E}[(a(X - \mu_X))^2]
$$

$$
= \mathbb{E}[a^2 (X - \mu_X)^2] = a^2 \mathbb{E}[(X - \mu_X)^2] = a^2 \text{Var}[X]. \quad \blacksquare
$$

What about the sum? $\text{Var}[X + Y] = \text{Var}[X] + \text{Var}[Y]$ — but **only if $X$ and $Y$ are uncorrelated**. The general identity is

$$
\text{Var}[X + Y] = \text{Var}[X] + \text{Var}[Y] + 2 \text{Cov}[X, Y],
$$

where the covariance $\text{Cov}[X, Y]$ measures how $X$ and $Y$ move together. We're previewing this; the full treatment is in Chapter 7. The takeaway for now: expectation passes cleanly through sums even when variables are correlated; variance does not.

---

## 5.10 Worked example 1: the die roll

Let's compute the variance of a fair die roll by both routes, and verify they agree.

### Route 1: directly from $\mathbb{E}[(X - \mu)^2]$

$\mu = 3.5$. We need $\mathbb{E}[(X - 3.5)^2]$. The PMF puts $1/6$ on each of $\{1, 2, 3, 4, 5, 6\}$:

| $x$ | $x - 3.5$ | $(x - 3.5)^2$ | $(x - 3.5)^2 \cdot \frac{1}{6}$ |
|---:|----:|----:|----:|
| 1 | $-2.5$ | 6.25 | $1.0417$ |
| 2 | $-1.5$ | 2.25 | $0.3750$ |
| 3 | $-0.5$ | 0.25 | $0.0417$ |
| 4 | $+0.5$ | 0.25 | $0.0417$ |
| 5 | $+1.5$ | 2.25 | $0.3750$ |
| 6 | $+2.5$ | 6.25 | $1.0417$ |

Sum the right column:

$$
\text{Var}[X] = 1.0417 + 0.375 + 0.0417 + 0.0417 + 0.375 + 1.0417 = 2.9167.
$$

In fraction form, $1/6 (6.25 + 2.25 + 0.25 + 0.25 + 2.25 + 6.25) = 1/6 \cdot 17.5 = 17.5/6 = 35/12 \approx 2.9167$.

### Route 2: via the shortcut

$\mathbb{E}[X^2] = \frac{1}{6}(1 + 4 + 9 + 16 + 25 + 36) = \frac{91}{6} \approx 15.1667$.

$\mathbb{E}[X]^2 = 3.5^2 = 12.25$.

$\text{Var}[X] = 15.1667 - 12.25 = 2.9167$. Same answer. The shortcut was easier (no centering), and the two methods agree as they must.

Standard deviation: $\sigma_X = \sqrt{35/12} \approx 1.708$. A "typical" roll deviates from the mean of 3.5 by about 1.7. Reasonable — the values range from 1 to 6, so deviations of 1-2 are typical, and 2.5 is the maximum.

---

## 5.11 Worked example 2: the Bernoulli random variable

This example will return many times. A **Bernoulli random variable** $X$ with parameter $p$ takes the value 1 with probability $p$ and the value 0 with probability $1 - p$:

$$
p_X(1) = p, \quad p_X(0) = 1 - p.
$$

The classic example is a single coin flip: 1 if heads, 0 if tails, with $p = 0.5$ for a fair coin. The classic ML example: the binary label "is this email spam?" — a Bernoulli with $p$ being whatever the true spam probability is for this email's features.

### 5.11.1 Computing the mean

$$
\mathbb{E}[X] = 1 \cdot p + 0 \cdot (1 - p) = p.
$$

The mean of a Bernoulli is just its parameter. Intuitive: if heads happens with probability $p$, the long-run average of (1s and 0s) is $p$.

### 5.11.2 Computing the variance

Use the shortcut. First, $\mathbb{E}[X^2]$:

$$
\mathbb{E}[X^2] = 1^2 \cdot p + 0^2 \cdot (1 - p) = p.
$$

(Note that for Bernoulli, $X^2 = X$ — squaring 0 gives 0 and squaring 1 gives 1 — so $\mathbb{E}[X^2] = \mathbb{E}[X] = p$. A small but useful observation.)

Then $(\mathbb{E}[X])^2 = p^2$. So:

$$
\text{Var}[X] = p - p^2 = p(1 - p).
$$

The variance is $p(1 - p)$. A few sanity checks:

- If $p = 0$ or $p = 1$, the variable is deterministic (always 0 or always 1), and the variance is 0. Plug in: $0(1-0) = 0$ and $1(1-1) = 0$. Checks out.
- If $p = 0.5$, the variance is $0.5 \cdot 0.5 = 0.25$, the maximum. This is the most "uncertain" Bernoulli — a fair coin maximises variance.
- Plotting $p(1-p)$ as a function of $p$, it's a downward parabola peaking at $p = 0.5$.

This $p(1-p)$ pops up *everywhere*. In Chapter 6 it determines the variance of the binomial. In Chapter 32 it appears in the second derivative of the cross-entropy loss, which is why logistic regression's optimization landscape is so well-behaved. In A/B testing, the variance of the sample proportion comes from it. Memorise it.

### 5.11.3 Connection back to logistic regression

Here, finally, is the formal statement of what Chapter 3 hand-waved.

When logistic regression produces $\hat{p}(\text{spam} \mid x) = 0.73$ for an email, it is saying: "I am modelling the label $Y$ for this email as a Bernoulli random variable with parameter $p = 0.73$." The output of the model is the *parameter of a distribution over the label*, not a label itself. The label is then drawn from that distribution.

This framing — "the model outputs a parameter, the observation is sampled from the parameterised distribution" — is the same framing that underlies every probabilistic model in ML. Linear regression: model outputs the mean of a Gaussian. Logistic regression: model outputs the $p$ of a Bernoulli. Naive Bayes: each feature is modelled as drawn from some class-conditional distribution. Once you see this pattern, you see it everywhere; it is the spine of "probabilistic ML" as a whole.

---

## 5.12 Code: random variables and their moments in Python

After all the math, code. We'll use NumPy and SciPy to compute the things we just derived by hand.

```python
import numpy as np
from scipy import stats

# --- Die roll ---
# Use scipy's discrete uniform: integers 1..6
die = stats.randint(low=1, high=7)   # high is exclusive
print("Die mean:", die.mean())        # 3.5
print("Die var:",  die.var())         # 35/12 ≈ 2.9167
print("Die std:",  die.std())         # ≈ 1.7078

# Verify by simulation
np.random.seed(0)
rolls = np.random.randint(1, 7, size=1_000_000)
print("Simulated mean:", rolls.mean())   # ~3.500
print("Simulated var:",  rolls.var())    # ~2.917
```

Two things worth noticing in this snippet.

First, the analytical computation (via `stats.randint`) and the empirical computation (a million simulated rolls) agree to two or three decimal places. This is the **law of large numbers** in action — sample averages converge to expectations. We'll prove it in Chapter 9.

Second, `np.random.seed(0)` makes the simulation reproducible. Always seed your random calls when you want reproducible results.

```python
# --- Bernoulli ---
p = 0.3
bern = stats.bernoulli(p=p)
print("Bernoulli mean:", bern.mean())         # p = 0.3
print("Bernoulli var:",  bern.var())          # p(1-p) = 0.21
print("Bernoulli std:",  bern.std())          # sqrt(0.21) ≈ 0.458

# PMF values
print("P(X=0):", bern.pmf(0))   # 0.7
print("P(X=1):", bern.pmf(1))   # 0.3

# Computational shortcut, by hand
samples = bern.rvs(size=100_000, random_state=0)
empirical_mean = samples.mean()
empirical_E_Xsq = (samples ** 2).mean()
empirical_var_shortcut = empirical_E_Xsq - empirical_mean ** 2
print("Empirical var via shortcut:", empirical_var_shortcut)  # ~0.21
```

The shortcut formula works empirically just as we'd hope.

```python
# --- A continuous example: the standard normal ---
norm = stats.norm(loc=0, scale=1)    # mean 0, std 1
print("PDF at 0:", norm.pdf(0))      # ≈ 0.3989  (NOT a probability!)
print("PDF at 1:", norm.pdf(1))      # ≈ 0.2420
print("P(X ≤ 0):", norm.cdf(0))      # 0.5
print("P(X ≤ 1):", norm.cdf(1))      # ≈ 0.8413

# The probability that X is between -1 and 1
p_within_one_sigma = norm.cdf(1) - norm.cdf(-1)
print("P(-1 ≤ X ≤ 1):", p_within_one_sigma)  # ≈ 0.6827 (the "68%" of 68-95-99.7)
```

The PDF at 0 is 0.3989. Reading that as "the probability of $X = 0$ is 0.3989" is **wrong**. The probability of any single value is zero. What 0.3989 *means* is: the density at 0 is 0.3989; the probability of falling in a tiny interval $[0, \Delta x]$ is approximately $0.3989 \cdot \Delta x$.

The CDF, by contrast, *does* give probabilities directly. $P(X \leq 1) = 0.8413$ is the actual probability that a standard normal random variable comes out at most 1. The difference $\text{CDF}(1) - \text{CDF}(-1) = 0.6827$ is the well-known "68% within one standard deviation" property of the normal — we'll meet it again in Chapter 6.

---

## 5.13 A note on what we glossed over

This chapter built the basic machinery. A few things we did *not* do, and where they show up:

1. **Measure theory.** Kolmogorov's axioms are stated for "events," which in the full theory are members of a $\sigma$-algebra (not all subsets of $\Omega$ are events — pathological subsets exist for continuous sample spaces). For applied ML this never matters. If you ever see a paper mention "measurability," you are reading something deeper than this book.

2. **Joint distributions.** We mostly worked with one random variable at a time. Multiple random variables, their joint behaviour, and conditional probabilities are the subject of Chapter 7.

3. **Conditional expectation.** $\mathbb{E}[Y \mid X = x]$ is the expectation of $Y$ given that $X$ took the value $x$. It is itself a function of $x$ (different conditional means for different conditioning values). We touch on it lightly in Chapter 7 and use it extensively from Chapter 19 onward.

4. **Higher moments.** Beyond the mean (first moment) and the variance (second central moment), there are skewness (third moment) and kurtosis (fourth moment). These come up in some applied contexts; for the exam they don't.

5. **Moment-generating functions.** A clean way to derive the moments of many distributions in one go. Useful in theory; not used in the exam.

The omissions are intentional — we have enough to climb the ladder we're going to use.

---

## 5.14 Summary

Strip this chapter down to its essentials:

1. **A probability** is a function $P$ on events (subsets of a sample space $\Omega$) satisfying non-negativity, normalisation, and countable additivity. Three rules. Everything else follows.
2. **A random variable** $X$ is a function $\Omega \to \mathbb{R}$. It's a rule for assigning numbers to outcomes, not a number itself.
3. **Discrete** random variables are described by a PMF $p_X(x) = P(X = x)$. The PMF gives probabilities directly; it sums to 1.
4. **Continuous** random variables are described by a PDF $f_X(x)$. The PDF is a *density*, not a probability; probabilities come from integrating it over an interval. $P(X = x) = 0$ for any single point.
5. The **CDF** $F_X(x) = P(X \leq x)$ works for both discrete and continuous cases and is monotonically non-decreasing from 0 to 1.
6. **Expectation** $\mathbb{E}[X]$ is a weighted average of $X$'s values, weighted by probability (sum or integral). It is the "center of mass" of the distribution.
7. **Linearity of expectation:** $\mathbb{E}[aX + b] = a \mathbb{E}[X] + b$ and $\mathbb{E}[X + Y] = \mathbb{E}[X] + \mathbb{E}[Y]$, the latter holding without any independence assumption. Most useful theorem in probability.
8. **Variance** $\text{Var}[X] = \mathbb{E}[(X - \mu)^2] = \mathbb{E}[X^2] - \mu^2$ measures spread. Variance is *not* linear in the same way; $\text{Var}[aX + b] = a^2 \text{Var}[X]$, and variances of sums require covariance to handle correlated terms.
9. **Bernoulli random variable**: $\mathbb{E}[X] = p$, $\text{Var}[X] = p(1-p)$. The model for binary labels; the foundation of logistic regression's probabilistic reading.

If you can compute the mean and variance of a discrete random variable from its PMF, and explain why $\mathbb{E}[X + Y] = \mathbb{E}[X] + \mathbb{E}[Y]$ holds even when $X$ and $Y$ are correlated, you have the working competence for the rest of Part B.

---

## 5.15 What this builds on / where this returns

**Builds on:** Chapter 3's informal use of "probability" in the spam classifier's output. Chapter 3 said the model outputs a probability; this chapter said *what that means*.

**Returns:**

- **Linearity of expectation** is used to derive the **loss-function framing of ML** in *Chapter 16* — empirical risk is the average over training data, which estimates the expected loss.
- **Variance and the shortcut formula** return in *Chapter 19*'s **bias-variance decomposition** — the proof relies on the same algebra we did in section 5.9.3.
- **Bernoulli random variables** are the label model in *Chapter 32*'s derivation of **logistic regression** from maximum likelihood. The connection sketched in 5.11.3 becomes formal.
- **Discrete and continuous distinction** matters in *Chapter 6* (specific distributions) and *Chapter 10* (the difference between continuous test statistics like the t and discrete ones like the chi-squared).
- **The PDF-is-not-a-probability** trap returns in *Chapter 6* when we work with the normal distribution and in *Chapter 8* when we compute Bayes' theorem with continuous likelihoods.

---

## 5.16 Exercises

Attempt all of them cold. Answers in the fold.

1. **A weighted coin.** A coin lands heads with probability $0.7$. Let $X$ be the random variable that is 1 on heads and 0 on tails. Compute $\mathbb{E}[X]$, $\mathbb{E}[X^2]$, and $\text{Var}[X]$ by hand. Verify that $\text{Var}[X] = p(1 - p)$.

2. **Two dice.** Let $X$ be the sum of two fair dice. Without computing the full PMF, find $\mathbb{E}[X]$. (Hint: linearity of expectation — write $X$ as a sum of two simpler random variables.)

3. **Variance of two dice.** Continue from question 2. Find $\text{Var}[X]$, assuming the two dice are independent. (Hint: variances add for independent random variables.)

4. **PMF or not?** Which of the following is a valid PMF for a discrete random variable taking values in $\{0, 1, 2, 3\}$? For invalid ones, say why.
   1. $p_X(0) = 0.2$, $p_X(1) = 0.3$, $p_X(2) = 0.4$, $p_X(3) = 0.1$.
   2. $p_X(0) = 0.5$, $p_X(1) = 0.5$, $p_X(2) = 0.0$, $p_X(3) = 0.0$.
   3. $p_X(0) = 0.3$, $p_X(1) = 0.3$, $p_X(2) = 0.3$, $p_X(3) = 0.3$.
   4. $p_X(0) = -0.1$, $p_X(1) = 0.6$, $p_X(2) = 0.3$, $p_X(3) = 0.2$.

5. **In your own words.** Explain why $P(X = x) = 0$ for any single value $x$ when $X$ is continuous. Why doesn't this mean $X$ can never take any specific value?

6. **PDF vs. PMF.** A friend says, "If the standard normal PDF at 0 is 0.3989, the probability of getting 0 is 39.89%." Correct them precisely. What *is* the meaning of 0.3989?

7. **Expectation of a transformed variable.** Let $X$ be a fair die roll. Define $Y = 2X - 3$. Compute $\mathbb{E}[Y]$ and $\text{Var}[Y]$ two ways: (a) by computing the PMF of $Y$ and using the definitions, and (b) by using the linearity rules. They should agree.

8. **A non-linear transformation.** Let $X$ be a fair die. Compute $\mathbb{E}[X^2]$ directly. Does $\mathbb{E}[X^2] = (\mathbb{E}[X])^2$? If not, what's the difference, and what does it represent?

9. **Probability of an event from a CDF.** A continuous random variable $X$ has CDF $F_X$ with $F_X(2) = 0.3$ and $F_X(5) = 0.8$. What is $P(2 < X \leq 5)$?

10. **Bernoulli variance reasoning.** Without computing, argue that a Bernoulli with $p = 0.99$ has smaller variance than one with $p = 0.5$. Why does it make intuitive sense that the variance peaks at $p = 0.5$?

11. **The model's "probability."** Recall the spam classifier outputs $\hat{p}(\text{spam} \mid x)$. If you took 10,000 emails that the model scored at exactly $\hat{p} = 0.7$, what fraction would you expect to actually be spam — assuming the model is *well-calibrated*? What does that tell you about the meaning of the output, in Bernoulli-parameter terms?

12. **Linearity even for dependent variables.** Let $X$ be a fair die roll, and let $Y = -X$. Compute $\mathbb{E}[X + Y]$ directly. Compare with $\mathbb{E}[X] + \mathbb{E}[Y]$. Now compute $\text{Var}[X + Y]$ directly and compare with $\text{Var}[X] + \text{Var}[Y]$. Explain what you observe.

<details>
<summary>Answers</summary>

1. $\mathbb{E}[X] = 1 \cdot 0.7 + 0 \cdot 0.3 = 0.7$. $\mathbb{E}[X^2] = 1^2 \cdot 0.7 + 0^2 \cdot 0.3 = 0.7$. $\text{Var}[X] = 0.7 - 0.7^2 = 0.7 - 0.49 = 0.21$. And indeed $p(1-p) = 0.7 \cdot 0.3 = 0.21$.

2. Let $X_1, X_2$ be the values of the two dice; $X = X_1 + X_2$. Each die has $\mathbb{E}[X_i] = 3.5$. By linearity, $\mathbb{E}[X] = 3.5 + 3.5 = 7$.

3. Each die has variance $35/12$. For independent variables, variances add: $\text{Var}[X] = 35/12 + 35/12 = 70/12 = 35/6 \approx 5.833$.

4. (a) Valid: non-negative, sums to 1. (b) Valid: non-negative, sums to 1. (c) Invalid: sums to 1.2, not 1. (d) Invalid: $p_X(0) = -0.1 < 0$.

5. Continuous random variables take values in a range with uncountably many points. The total probability is 1, and "uncountably many" outcomes can't each carry positive probability without the total exceeding 1. So each point gets probability 0. This doesn't mean $X$ never takes a specific value — it means the language of "probability of a single point" is the wrong language for continuous variables; you should ask for the probability of falling in *intervals* instead.

6. The 0.3989 is the *density* at 0, not a probability. It tells you that the probability of falling in a small interval $[0, \Delta x]$ is approximately $0.3989 \cdot \Delta x$ — the height of the curve times the width of the interval. To get an actual probability you must integrate the PDF over a range; the probability that $X = 0$ exactly is zero.

7. (a) $Y$ takes values $2 \cdot 1 - 3 = -1, 1, 3, 5, 7, 9$, each with probability $1/6$. $\mathbb{E}[Y] = (-1 + 1 + 3 + 5 + 7 + 9)/6 = 24/6 = 4$. $\mathbb{E}[Y^2] = (1 + 1 + 9 + 25 + 49 + 81)/6 = 166/6 \approx 27.667$. $\text{Var}[Y] = 27.667 - 16 = 11.667$. (b) By rules: $\mathbb{E}[Y] = 2 \cdot 3.5 - 3 = 4$. $\text{Var}[Y] = 2^2 \cdot 35/12 = 140/12 = 35/3 \approx 11.667$. Agree.

8. $\mathbb{E}[X^2] = (1 + 4 + 9 + 16 + 25 + 36)/6 = 91/6 \approx 15.167$. $(\mathbb{E}[X])^2 = 3.5^2 = 12.25$. They differ by $91/6 - 12.25 = 2.917 = 35/12$ — exactly the variance. This is the computational shortcut formula in disguise: $\mathbb{E}[X^2] - (\mathbb{E}[X])^2 = \text{Var}[X]$.

9. $P(2 < X \leq 5) = F_X(5) - F_X(2) = 0.8 - 0.3 = 0.5$.

10. For $p = 0.99$, the outcome is almost always 1; little uncertainty, little variance — specifically $0.99 \cdot 0.01 = 0.0099$. For $p = 0.5$, you're maximally unsure which outcome will appear; variance is maximal at $0.5 \cdot 0.5 = 0.25$. Intuitively: variance measures spread, and a near-deterministic distribution has almost no spread.

11. Expect about 7,000 to actually be spam. The model's output 0.7 is the *parameter $p$ of the Bernoulli distribution* it's putting on the label $Y$ given this email's features. If well-calibrated, the long-run fraction of spam among emails scored 0.7 matches that $p$.

12. $X + Y = X - X = 0$ always. $\mathbb{E}[X + Y] = 0$. By linearity, $\mathbb{E}[X] + \mathbb{E}[Y] = 3.5 + (-3.5) = 0$. They agree — linearity of expectation didn't care about the dependence. Now $\text{Var}[X + Y] = \text{Var}[0] = 0$ (a constant has zero variance). But $\text{Var}[X] + \text{Var}[Y] = 35/12 + 35/12 = 70/12$. They disagree dramatically. The "missing piece" is $2 \text{Cov}[X, Y] = 2 \text{Cov}[X, -X] = -2 \text{Var}[X] = -70/12$, which exactly cancels the sum to give 0. Variance is not linear; covariance accounts for the difference.

</details>
