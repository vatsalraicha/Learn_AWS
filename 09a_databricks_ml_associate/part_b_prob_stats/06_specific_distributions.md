# Chapter 6 — The Distributions You'll Actually Meet

> **Goal of this chapter:** to introduce, derive, and ground in worked examples the small set of distributions you will see again and again throughout the rest of this book and the rest of your ML career. There are infinitely many possible probability distributions; in practice, perhaps a dozen show up in 90% of applied work. We will cover five core ones — Bernoulli, binomial, multinomial, Poisson, and the normal — and touch on geometric and exponential. For each: the PMF or PDF, the mean and variance (derived, not asserted), a concrete example of where it shows up, and a tactile sense of "what this distribution actually looks like."
>
> This chapter is denser with formulas than Chapter 5 was. That is a feature, not a bug. The formulas are the working tools; the goal is for them to stop feeling like memorisation and start feeling like a set of trusted tools whose shape you remember because you've used them.

---

## 6.1 Why these five distributions and not others?

Statistics has invented hundreds of distributions. Wikipedia lists more than 90 with their own articles. Why focus on five?

Because of one observation: nearly every problem in classical ML can be modelled adequately using a small set of distributions that recur because of *structural* reasons. The Bernoulli appears whenever a binary outcome is involved — yes/no, spam/ham, click/no-click. The binomial appears as the natural distribution of a count of binary outcomes — "how many of these 100 trials succeeded?" The multinomial is its multi-class cousin — "which of $k$ categories did we land in, and how many times each?" The Poisson appears whenever we count arrivals of independent events in a fixed window — customer arrivals, server errors, fraud attempts per day. The normal appears as the limit of many small independent influences added together — heights, test scores, measurement errors, and the sampling distribution of almost any well-behaved estimator (this is the central limit theorem, which we will prove in spirit in Chapter 9).

The exponential and geometric distributions describe "waiting times" — how long until the next event, or how many trials until the first success. They show up in survival analysis and in the analysis of randomised algorithms. We give them a brief treatment.

Five core, two supporting. That is the right working repertoire.

A pattern to watch for as you read: many of these distributions are built from the Bernoulli by composition. The binomial is a *sum of* Bernoullis. The multinomial is a *vector of* multinomial counts (the multi-class Bernoulli generalised). The Poisson is the *limit of* many small-probability Bernoullis. The geometric is the *waiting time of* iid Bernoullis. The Bernoulli is the seed; the others are crops.

---

## 6.2 The Bernoulli distribution

We met this in Chapter 5. Let us put it down formally as the foundation we'll build on.

### 6.2.1 Definition

A random variable $X$ is **Bernoulli** with parameter $p \in [0, 1]$ — written $X \sim \text{Bernoulli}(p)$ — if it takes the value 1 with probability $p$ and the value 0 with probability $1 - p$.

PMF, written compactly:

$$
p_X(x) = p^x (1 - p)^{1 - x} \quad \text{for } x \in \{0, 1\}.
$$

The compact form looks slightly tricky; let's verify it. When $x = 1$: $p^1 (1-p)^0 = p \cdot 1 = p$. When $x = 0$: $p^0 (1-p)^1 = 1 \cdot (1-p) = 1-p$. Good.

### 6.2.2 Mean and variance, recapped

From Chapter 5: $\mathbb{E}[X] = p$, $\text{Var}[X] = p(1-p)$. Both derived from the PMF in section 5.11; we won't re-derive here.

### 6.2.3 Where it shows up

Every binary classification label is a Bernoulli. Every coin flip. Every "did the user click the ad?" event. Every "did this loan default?" event. Every "did the patient survive 30 days?" event. The Bernoulli is the alphabet of binary decisions.

When you train logistic regression, you are estimating the parameter $p$ of a Bernoulli distribution — conditional on the input features. The model says "given $x$, the label $Y$ follows $\text{Bernoulli}(\sigma(\mathbf{w} \cdot \mathbf{x} + b))$." We derive this formally in Chapter 32.

---

## 6.3 The binomial distribution

Now we add the natural next question. If you flip a biased coin (parameter $p$) ten times, how many heads do you get? The answer is a *count*, a non-negative integer between 0 and 10. The distribution of that count is the **binomial distribution**.

### 6.3.1 Construction from Bernoullis

Let $X_1, X_2, \ldots, X_n$ be iid Bernoulli with parameter $p$. Then their sum

$$
S = X_1 + X_2 + \ldots + X_n
$$

is a binomial random variable with parameters $n$ and $p$, written $S \sim \text{Binomial}(n, p)$.

The construction is the key. The binomial is *literally* a sum of iid Bernoullis. This is the source of all of its properties.

### 6.3.2 The PMF — and where the binomial coefficient comes from

What is $P(S = k)$, the probability of exactly $k$ successes in $n$ trials?

Pick one specific sequence of $n$ outcomes that has exactly $k$ ones (successes) and $n-k$ zeros (failures). Each one happens with probability $p$, each zero with probability $1-p$, and the trials are independent. So the probability of this specific sequence is

$$
p^k (1-p)^{n-k}.
$$

But many different sequences contain exactly $k$ ones. They are all equally likely (each is $p^k (1-p)^{n-k}$), and we want the total probability of "any of these sequences occurs." So we count them and multiply.

How many sequences of length $n$ contain exactly $k$ ones? This is the number of ways to choose which $k$ of the $n$ positions get a 1. From combinatorics, that count is the **binomial coefficient**:

$$
\binom{n}{k} = \frac{n!}{k! \, (n - k)!}.
$$

(Read "$n$ choose $k$.") So the binomial PMF is:

$$
P(S = k) = \binom{n}{k} p^k (1-p)^{n-k} \quad \text{for } k \in \{0, 1, 2, \ldots, n\}.
$$

Sanity check: for $n = 1$, $\binom{1}{0} = 1$ and $\binom{1}{1} = 1$, so $P(S = 0) = 1 - p$ and $P(S = 1) = p$ — which is the Bernoulli we started from. The binomial with $n = 1$ is the Bernoulli.

### 6.3.3 Mean and variance, derived from the construction

Because $S = X_1 + \ldots + X_n$ is a sum of iid Bernoullis, linearity of expectation gives the mean for free:

$$
\mathbb{E}[S] = \mathbb{E}[X_1] + \ldots + \mathbb{E}[X_n] = n \cdot p.
$$

Three lines, no integration, no combinatorial sums. This is the payoff of having Chapter 5 firmly under us.

For variance, we use the fact that the $X_i$ are *independent*, which means variances add:

$$
\text{Var}[S] = \text{Var}[X_1] + \ldots + \text{Var}[X_n] = n \cdot p(1-p).
$$

(If the $X_i$ were correlated, this would not hold — covariance terms would appear. But independence is part of the definition of "iid".)

So: $S \sim \text{Binomial}(n, p)$ has mean $np$ and variance $np(1-p)$. Memorise this; it is one of the workhorses.

### 6.3.4 Worked example: spam in a sample of 100 emails

Suppose the true spam rate is $p = 0.24$ and you sample 100 emails at random. Let $S$ be the number of spam emails in your sample. Then $S \sim \text{Binomial}(100, 0.24)$.

- Expected number of spam: $\mathbb{E}[S] = 100 \cdot 0.24 = 24$.
- Variance: $\text{Var}[S] = 100 \cdot 0.24 \cdot 0.76 = 18.24$.
- Standard deviation: $\sqrt{18.24} \approx 4.27$.

So a typical sample contains 24 spams give-or-take 4 or 5. A sample with 35 spam would be unusually high; a sample with 10 spam would be unusually low.

The probability of *exactly* 30 spam:

$$
P(S = 30) = \binom{100}{30} (0.24)^{30} (0.76)^{70}.
$$

The binomial coefficient $\binom{100}{30}$ is astronomical (about $2.94 \times 10^{25}$), and the powers of 0.24 and 0.76 are vanishingly small, but their product comes out to a sensible probability, about 0.029. We will compute it in code below.

### 6.3.5 Shape of the binomial

For small $n$, the binomial looks discrete and asymmetric:

```
n=10, p=0.3:

   P(S=k)
    │
 0.27┤      █
    │     ██
 0.2 ┤   ███
    │   ████
 0.13┤  ████
    │  █████
 0.07┤  █████
    │  ██████
 0   ┤  ██████___
    └──┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─► k
       0 1 2 3 4 5 6 7 8 9 10
```

Skewed when $p \neq 0.5$, with the mode near $np$.

For *large* $n$ — say $n = 100$ — the shape becomes smooth and almost symmetric, approaching a normal distribution. This is the central limit theorem peeking in: a sum of many iid random variables looks normal. We will make this precise in Chapter 9. For now, hold the picture: binomial-with-large-$n$-and-moderate-$p$ ≈ normal.

### 6.3.6 Where it shows up

Counts of binary outcomes in a fixed-size batch. Number of clicks among 1000 ad impressions. Number of defaults in a portfolio of 500 loans. Number of misclassified examples in a batch of 200 test examples (with the classifier's error rate as $p$). The binomial is the natural model whenever you have $n$ independent trials and you're counting the successes.

---

## 6.4 The multinomial distribution

Now lift from binary to multi-class. Suppose each trial has $k$ possible outcomes, not just two — like rolling a 6-sided die, or routing each email to one of `{inbox, promotions, junk}`, or classifying each image as one of `{cat, dog, bird, fish}`. Track the counts of each outcome over $n$ trials. The resulting joint distribution of counts is the **multinomial distribution**.

### 6.4.1 Setup

Each trial lands in one of $k$ categories, with probabilities $p_1, p_2, \ldots, p_k$ where $\sum_{i=1}^k p_i = 1$. Run $n$ independent trials. Let $X_i$ be the count in category $i$. Then $(X_1, X_2, \ldots, X_k)$ is jointly multinomial with parameters $n$ and $(p_1, \ldots, p_k)$.

The counts must satisfy $\sum_{i=1}^k X_i = n$ — every trial lands in exactly one category — so the $X_i$ are not independent of each other.

### 6.4.2 The PMF

By a multinomial-coefficient argument that generalises the binomial:

$$
P(X_1 = n_1, X_2 = n_2, \ldots, X_k = n_k) = \frac{n!}{n_1! \, n_2! \, \cdots \, n_k!} \prod_{i=1}^{k} p_i^{n_i}
$$

with $\sum n_i = n$. The fraction is the multinomial coefficient — the number of ways to assign $n$ trials to $k$ categories with counts $n_1, \ldots, n_k$. When $k = 2$ this collapses back to the binomial (because $\binom{n}{n_1, n_2} = \binom{n}{n_1}$ when $n_2 = n - n_1$).

### 6.4.3 Marginals are binomial

A useful fact for intuition. If you focus on a single category — say category 1 — and ask "how many trials land in category 1?", the marginal distribution of $X_1$ is just $\text{Binomial}(n, p_1)$. From category 1's point of view, each trial is "category 1 (success)" with probability $p_1$ or "anything else (failure)" with probability $1 - p_1$.

So $\mathbb{E}[X_i] = n p_i$ and $\text{Var}[X_i] = n p_i (1 - p_i)$.

The categories are *not independent* of each other (because they have to sum to $n$), but each marginally is a binomial.

### 6.4.4 Where it shows up: softmax outputs

When a neural network or any multi-class classifier outputs class probabilities — `[0.7, 0.2, 0.1]` for `[cat, dog, bird]` on a given image — those probabilities are parameterising a multinomial distribution over the label of that single image. With $n = 1$, the multinomial reduces to a "categorical distribution" (one trial, one outcome), and the loss function we use to train is the *negative log-likelihood* under that categorical model — also known as **cross-entropy**.

This is why cross-entropy is the standard loss for multi-class classification: it is the log-likelihood under a multinomial assumption. We derive this fully in Chapter 32 (binary cross-entropy ↔ Bernoulli) and revisit it for multi-class in Chapter 47.

---

## 6.5 The Poisson distribution

Now a different shape of problem. You don't have a fixed number of trials; you have a continuous window of time (or space), and *events arrive in it at some rate*. How many events do you see in the window?

### 6.5.1 Setup and PMF

A random variable $X$ is **Poisson** with parameter $\lambda > 0$ — written $X \sim \text{Poisson}(\lambda)$ — if its PMF is

$$
P(X = k) = \frac{\lambda^k e^{-\lambda}}{k!} \quad \text{for } k \in \{0, 1, 2, \ldots\}.
$$

Note the domain: $X$ takes non-negative integer values, possibly unbounded — could be 0, could be 100, could be 1,000,000 with vanishingly small probability. There is no fixed $n$ here.

Sanity check that the PMF sums to 1:

$$
\sum_{k=0}^{\infty} \frac{\lambda^k e^{-\lambda}}{k!} = e^{-\lambda} \sum_{k=0}^{\infty} \frac{\lambda^k}{k!} = e^{-\lambda} \cdot e^{\lambda} = 1
$$

using the Taylor series $e^x = \sum_{k=0}^{\infty} x^k / k!$. Good.

### 6.5.2 Mean and variance

A clean result: $\mathbb{E}[X] = \lambda$ and $\text{Var}[X] = \lambda$. The mean equals the variance. This is a *distinctive* feature of the Poisson — most distributions have separate mean and variance parameters, but the Poisson collapses them. If you ever see real-world count data where the sample variance is much bigger than the sample mean ("over-dispersion") or much smaller ("under-dispersion"), the Poisson is probably the wrong model.

Let's derive the mean. By definition:

$$
\mathbb{E}[X] = \sum_{k=0}^{\infty} k \cdot \frac{\lambda^k e^{-\lambda}}{k!}.
$$

The $k = 0$ term is zero, so:

$$
= \sum_{k=1}^{\infty} k \cdot \frac{\lambda^k e^{-\lambda}}{k!} = \sum_{k=1}^{\infty} \frac{\lambda^k e^{-\lambda}}{(k-1)!}
$$

(cancelling the $k$ in the numerator with one factor of $k!$ in the denominator). Pull $\lambda$ out and substitute $j = k - 1$:

$$
= \lambda e^{-\lambda} \sum_{k=1}^{\infty} \frac{\lambda^{k-1}}{(k-1)!} = \lambda e^{-\lambda} \sum_{j=0}^{\infty} \frac{\lambda^j}{j!} = \lambda e^{-\lambda} \cdot e^\lambda = \lambda. \quad \blacksquare
$$

The variance computation is similar in spirit but involves $\mathbb{E}[X(X-1)] = \lambda^2$ as an intermediate step; we'll spare the details (it's an exercise).

### 6.5.3 Poisson as the limit of binomial

Here's a deep fact that explains why the Poisson is the right model for "rare events in a window."

Suppose you have a binomial with $n$ very large and $p$ very small, such that $np = \lambda$ is fixed and moderate. In other words: many trials, each with low probability of success, with the *expected number of successes* held constant.

**Claim:** as $n \to \infty$ and $p \to 0$ with $np = \lambda$, the binomial PMF converges to the Poisson PMF with parameter $\lambda$.

**Derivation sketch.** Start from the binomial PMF:

$$
\binom{n}{k} p^k (1-p)^{n-k} = \frac{n!}{k! (n-k)!} \left(\frac{\lambda}{n}\right)^k \left(1 - \frac{\lambda}{n}\right)^{n-k}.
$$

Split it apart:

$$
= \frac{1}{k!} \cdot \frac{n!}{(n-k)!} \cdot \frac{\lambda^k}{n^k} \cdot \left(1 - \frac{\lambda}{n}\right)^n \cdot \left(1 - \frac{\lambda}{n}\right)^{-k}.
$$

Look at each piece as $n \to \infty$:

- $\frac{n!}{(n-k)! \, n^k} = \frac{n(n-1)(n-2)\cdots(n-k+1)}{n^k} \to 1$ — for fixed $k$, the ratio of $k$ consecutive integers near $n$ to $n^k$ approaches 1.
- $(1 - \lambda/n)^n \to e^{-\lambda}$ — the famous limit.
- $(1 - \lambda/n)^{-k} \to 1$ — exponent $k$ is fixed; the base goes to 1.

So:

$$
\binom{n}{k} p^k (1-p)^{n-k} \to \frac{\lambda^k e^{-\lambda}}{k!} = \text{Poisson}(\lambda) \text{ PMF}. \quad \blacksquare
$$

Geometrically: many small Bernoullis added up, with their total mean held fixed, become a Poisson. This is the rationale for using the Poisson in any situation where "many things could happen, each rarely."

### 6.5.4 Worked example: customer arrivals

Suppose a small online store gets an average of 3 customers per hour. Assume customer arrivals are independent (one customer doesn't influence another). Then the number of customers arriving in one hour, call it $X$, is approximately $\text{Poisson}(3)$.

- $P(X = 0)$ (no customers): $\frac{3^0 e^{-3}}{0!} = e^{-3} \approx 0.0498$, about 5%.
- $P(X = 3)$ (exactly average): $\frac{3^3 e^{-3}}{6} = \frac{27 e^{-3}}{6} \approx 0.224$, about 22%.
- $P(X = 6)$ (twice average): $\frac{3^6 e^{-3}}{720} = \frac{729 e^{-3}}{720} \approx 0.050$, about 5%.
- $P(X = 10)$ (huge spike): $\frac{3^{10} e^{-3}}{10!} \approx 0.0008$, less than one in a thousand.

Mean = variance = 3. Standard deviation = $\sqrt{3} \approx 1.73$. A typical hour sees 3 ± 2 customers; a slow hour might be 1, a busy hour 5 or 6, a remarkable hour 8+.

### 6.5.5 Where it shows up

Anywhere events arrive in a fixed window, independently, at some rate:

- Customer arrivals at a service.
- Server errors per hour.
- Mutations per generation in a small organism.
- Goals scored in a soccer match (famously well-modelled by Poisson).
- Phishing attempts per day against a corporate email gateway.
- Number of clicks on an ad in a fixed budget window.

The "independence" assumption is the main place reality bites — if arrivals are bursty (one customer brings five friends), the variance can be much larger than the mean, and you need a richer model (negative binomial, often).

---

## 6.6 The normal (Gaussian) distribution

Now we cross from the discrete world to the continuous one, with the most important distribution in all of statistics.

### 6.6.1 The PDF

A random variable $X$ is **normal** (or **Gaussian**) with mean $\mu$ and variance $\sigma^2$ — written $X \sim N(\mu, \sigma^2)$ — if its PDF is

$$
f_X(x) = \frac{1}{\sigma \sqrt{2\pi}} \exp\left(-\frac{(x - \mu)^2}{2 \sigma^2}\right), \quad x \in \mathbb{R}.
$$

The formula looks intimidating; let's read it piece by piece.

- The shape is an exponential of a *negative quadratic* in $(x - \mu)$. So the PDF peaks at $x = \mu$ (the exponent is zero there) and decays in both directions, faster for larger $(x - \mu)$.
- The "$\sigma^2$ in the denominator of the exponent" controls how fast the decay is — large $\sigma$, slow decay (wide bell); small $\sigma$, fast decay (narrow bell).
- The "$1/(\sigma \sqrt{2\pi})$" out front is a normalising constant. It is whatever it needs to be so that the PDF integrates to 1. The $\sqrt{2\pi}$ comes from a famous Gaussian integral; you can take it on faith.
- The shape is the symmetric "bell curve" everyone has seen.

```
  f_X(x), N(0, 1)
    │
 0.4┤        .--.
    │       /    \
 0.3┤      /      \
    │     /        \
 0.2┤    /          \
    │   /            \
 0.1┤  /              \
    │ /                \
 0  ┤_/__________________\_____► x
   -3 -2  -1  0  1  2  3
```

### 6.6.2 The standard normal and the Z transform

The **standard normal** is the special case $\mu = 0$, $\sigma = 1$. It is conventionally denoted $Z$:

$$
f_Z(z) = \frac{1}{\sqrt{2\pi}} \exp\left(-\frac{z^2}{2}\right).
$$

Why standard? Because any normal random variable can be converted to a standard normal by a linear transformation:

$$
Z = \frac{X - \mu}{\sigma} \implies Z \sim N(0, 1).
$$

You subtract the mean (centers it on 0) and divide by the standard deviation (scales the spread to 1). This **Z-score** is one of the most useful constructions in applied stats — it lets you tabulate properties of the standard normal once and apply them to any normal by transformation.

### 6.6.3 The 68-95-99.7 rule

For a standard normal:

- $P(-1 \leq Z \leq 1) \approx 0.6827$.
- $P(-2 \leq Z \leq 2) \approx 0.9545$.
- $P(-3 \leq Z \leq 3) \approx 0.9973$.

In words: about 68% of values are within one standard deviation of the mean, about 95% within two, and 99.7% within three. By the Z-transform, this holds for *any* normal — about 68% of values lie within $\mu \pm \sigma$, 95% within $\mu \pm 2\sigma$, etc.

This is the famous "68-95-99.7" rule (sometimes called the "empirical rule"). It is the single most-used heuristic in applied statistics for sanity-checking whether an observation is "unusual." A z-score of 3 is rare; a z-score of 5 is *very* rare (about 1 in 3.5 million); a z-score of 10 is essentially impossible under the normal model and suggests either a data error or that the data isn't really normal.

### 6.6.4 Why so common — the central limit theorem in preview

Why does the normal show up in so many real-world phenomena? The deep answer is the **central limit theorem** (CLT), which we'll prove in spirit in Chapter 9. The rough statement:

*If you sum a large number of independent random variables, each with finite variance, the sum's distribution approaches normal — regardless of the shape of the individual distributions.*

So any quantity that can be thought of as a sum of many small independent influences tends toward normal. Examples:

- Heights of adults: many small genetic and environmental factors add up. Roughly normal.
- Errors in a physical measurement: many tiny sources of noise summing. Roughly normal.
- The number of heads in 1000 coin flips: a sum of 1000 Bernoullis. Approximately normal by the CLT (and we already noted in section 6.3 that the binomial approaches a normal shape for large $n$).
- The average of any large random sample: a sum of iid variables divided by $n$. Approximately normal — this is the form of CLT we'll use most often.

The CLT is also why the normal is the "default" model for residuals and errors in classical statistics: residuals in a well-fit linear model are themselves sums of many small ignored effects, so are approximately normal in many cases.

### 6.6.5 Mean and variance — by definition

By construction, $X \sim N(\mu, \sigma^2)$ has $\mathbb{E}[X] = \mu$ and $\text{Var}[X] = \sigma^2$. Deriving these from the PDF requires evaluating Gaussian integrals; the symmetry of the PDF around $\mu$ pins down the mean, and the variance falls out of integrating $x^2 f_X(x)$ via a substitution trick. We'll spare the calculus; the parameter names are descriptive.

### 6.6.6 Worked example: test scores

The SAT total score for a year is roughly $N(\mu = 1050, \sigma^2 = 200^2)$.

What fraction of students score above 1450?

Compute the z-score: $Z = (1450 - 1050)/200 = 2.0$. So we want $P(Z > 2)$ for a standard normal. By symmetry and the 95% rule, $P(|Z| > 2) \approx 0.0455$, so $P(Z > 2) \approx 0.02275$, about 2.3% of students.

What fraction score below 850? $Z = (850 - 1050)/200 = -1.0$. $P(Z < -1) = 1 - P(Z < 1) = 1 - 0.8413 = 0.1587$, about 16%.

These computations — Z-score, look up in a table or compute via `scipy.stats.norm.cdf`, interpret — are the bread and butter of applied stats.

### 6.6.7 Where it shows up in ML

The normal distribution is everywhere:

- **Linear regression** assumes residuals are normal with mean 0 and constant variance (the Gauss-Markov assumptions). The maximum likelihood estimate under this assumption is the ordinary least squares estimate.
- **Confidence intervals** for sample means use the normal because of the CLT (Chapter 10).
- **The Gaussian kernel** (an exponential of a negative quadratic, just like the normal PDF) shows up in kernel methods and in similarity measures.
- **Initialisation** of neural network weights is typically from a small-variance normal — He init, Xavier init, etc.
- **Feature normalisation** (subtract mean, divide by standard deviation) is the Z-transform applied feature-by-feature; many algorithms (logistic regression with regularisation, SVMs, k-means) are sensitive to scaling and standardising helps.
- **Gaussian Mixture Models** as a clustering tool.

If you remember one continuous distribution, remember the normal.

---

## 6.7 The geometric and exponential distributions — light touch

We close with two distributions of "waiting times." We will not lean on them as heavily as the previous five, but they appear in survival analysis, in the analysis of randomised algorithms, and occasionally in time-to-event prediction tasks.

### 6.7.1 The geometric distribution

You flip a biased coin (parameter $p$) until you get the first head. Let $X$ be the number of flips needed. Then $X$ is **geometric**.

Two conventions exist. One counts the total number of trials including the success ($X \in \{1, 2, 3, \ldots\}$); the other counts the number of failures before the first success ($X \in \{0, 1, 2, \ldots\}$). Software packages differ. We use the "total trials" version.

PMF: $P(X = k) = (1 - p)^{k-1} p$. To get the first head on trial $k$, you need $k - 1$ tails followed by a head.

Mean: $\mathbb{E}[X] = 1/p$. If a fair coin, you expect to wait 2 flips on average for a head. If $p = 0.01$, you expect 100 flips. The "expected waiting time" is the reciprocal of the success probability.

Variance: $\text{Var}[X] = (1-p)/p^2$. Skips the derivation.

The geometric is the discrete analog of "how long until the first event." It has a **memoryless** property: given that the first $k$ flips were all tails, the distribution of *additional* flips needed is the same as the original distribution. The coin has no memory of past failures. This is, in fact, a defining property of the geometric — it is the only memoryless discrete distribution.

### 6.7.2 The exponential distribution

The continuous analog. If events arrive as a Poisson process with rate $\lambda$, the waiting time until the next event is **exponentially distributed**.

PDF: $f_X(x) = \lambda e^{-\lambda x}$ for $x \geq 0$.

CDF: $F_X(x) = 1 - e^{-\lambda x}$. The probability that the next event arrives within time $x$.

Mean: $\mathbb{E}[X] = 1/\lambda$. If events arrive at rate 3 per hour, the expected waiting time is $1/3$ hours = 20 minutes.

Variance: $\text{Var}[X] = 1/\lambda^2$.

Like the geometric, the exponential is memoryless: conditional on no event having occurred yet, the distribution of remaining waiting time is the same exponential. It is the only continuous distribution with this property.

Where it shows up: server response times (sometimes — many real systems have heavier tails), inter-arrival times in queueing theory, time-to-failure in some reliability problems. In ML it shows up in survival analysis and in the Laplace prior used in some Bayesian models.

---

## 6.8 Code: working with these distributions in SciPy

The `scipy.stats` module provides each of these as a "frozen" distribution object that you parameterise and then call methods on.

```python
import numpy as np
from scipy import stats

# --- Bernoulli ---
bern = stats.bernoulli(p=0.3)
print("Bernoulli mean:", bern.mean())   # 0.3
print("Bernoulli var:", bern.var())     # 0.21
print("PMF at 1:", bern.pmf(1))         # 0.3

# --- Binomial ---
binom = stats.binom(n=100, p=0.24)
print("Binomial mean:", binom.mean())   # 24
print("Binomial var:", binom.var())     # 18.24

# Probability of exactly 30 spam in 100 emails when true rate is 24%
print("P(S=30):", binom.pmf(30))        # ~0.029

# Probability of 30 or more
print("P(S>=30):", binom.sf(29))        # ~0.10
# (sf = "survival function" = 1 - CDF)

# --- Poisson ---
pois = stats.poisson(mu=3)               # mu here = lambda
print("Poisson mean:", pois.mean())     # 3
print("Poisson var:", pois.var())       # 3
print("P(X=0):", pois.pmf(0))           # ~0.0498
print("P(X<=5):", pois.cdf(5))          # ~0.916

# --- Normal ---
norm = stats.norm(loc=1050, scale=200)
print("Normal mean:", norm.mean())      # 1050
print("Normal var:", norm.var())        # 40000

# Fraction of students scoring above 1450
print("P(X>1450):", 1 - norm.cdf(1450)) # ~0.0228 (≈ 2.3%)

# Fraction within ±1 std
print("Within ±1σ:", norm.cdf(1250) - norm.cdf(850))  # ~0.6827

# --- Multinomial ---
# Probabilities over 3 categories, n=10 trials
multi = stats.multinomial(n=10, p=[0.5, 0.3, 0.2])
# Probability of specific count vector [5, 3, 2]
print("P([5,3,2]):", multi.pmf([5, 3, 2]))  # ~0.0851

# --- Exponential ---
expo = stats.expon(scale=1/3)            # scale = 1/lambda
print("Expo mean:", expo.mean())         # 0.333
# P(wait < 0.5)
print("P(X<0.5):", expo.cdf(0.5))        # ~0.777
```

A short demonstration of the normal-as-limit-of-binomial idea:

```python
import numpy as np
from scipy import stats

# Simulate: sum of 1000 Bernoulli(0.5)s
n_trials = 10_000
n_per_trial = 1000
p = 0.5

# Each row is one "experiment" of n_per_trial flips; sum across columns
results = np.random.binomial(1, p, size=(n_trials, n_per_trial)).sum(axis=1)

# Empirical mean and std
print("Empirical mean:", results.mean())   # ~500
print("Empirical std:", results.std())     # ~15.8 (= sqrt(1000*0.25))

# Compare to normal with same mean and variance
mu = n_per_trial * p
sigma = np.sqrt(n_per_trial * p * (1 - p))
print("Theoretical mean (np):", mu)
print("Theoretical std (sqrt(np(1-p))):", sigma)

# Z-score of a value
z = (results[0] - mu) / sigma
print("First experiment z-score:", z)
```

You should see the empirical mean and std come very close to the binomial's mean and std (500 and $\sqrt{250} \approx 15.81$). The histogram of `results` would, if plotted, look indistinguishable from a normal with the same mean and standard deviation. This is the CLT and the normal approximation to the binomial in action.

---

## 6.9 A reference table

It is occasionally useful to have all of these in one place. The table below summarises what we've derived; you should be able to reconstruct each row from memory after a re-read.

| Distribution | Range | Parameters | PMF or PDF | Mean | Variance |
|---|---|---|---|---|---|
| Bernoulli | $\{0, 1\}$ | $p$ | $p^x(1-p)^{1-x}$ | $p$ | $p(1-p)$ |
| Binomial | $\{0, 1, \ldots, n\}$ | $n, p$ | $\binom{n}{k} p^k (1-p)^{n-k}$ | $np$ | $np(1-p)$ |
| Multinomial | $\{n_1 + \ldots + n_k = n\}$ | $n, p_1, \ldots, p_k$ | $\frac{n!}{n_1! \cdots n_k!} \prod p_i^{n_i}$ | $np_i$ | $np_i(1-p_i)$ |
| Poisson | $\{0, 1, 2, \ldots\}$ | $\lambda$ | $\frac{\lambda^k e^{-\lambda}}{k!}$ | $\lambda$ | $\lambda$ |
| Geometric (total trials) | $\{1, 2, \ldots\}$ | $p$ | $(1-p)^{k-1} p$ | $1/p$ | $(1-p)/p^2$ |
| Normal | $\mathbb{R}$ | $\mu, \sigma^2$ | $\frac{1}{\sigma\sqrt{2\pi}} e^{-(x-\mu)^2/(2\sigma^2)}$ | $\mu$ | $\sigma^2$ |
| Exponential | $[0, \infty)$ | $\lambda$ | $\lambda e^{-\lambda x}$ | $1/\lambda$ | $1/\lambda^2$ |

The table is *not* the lesson. The derivations are the lesson; the table is a quick-reference once you know how the entries got there.

---

## 6.10 Summary

1. **Bernoulli**: one coin flip. Parameter $p$. Mean $p$, variance $p(1-p)$. The atom of binary classification.
2. **Binomial**: sum of $n$ iid Bernoullis. Counts of successes in $n$ trials. Mean $np$, variance $np(1-p)$. The binomial coefficient comes from "how many ways to arrange $k$ successes in $n$ slots."
3. **Multinomial**: $n$ trials, each landing in one of $k$ categories. Joint distribution of category counts. Each marginal is binomial. The distribution underlying softmax outputs in multi-class classification.
4. **Poisson**: counts of independent events in a fixed window at rate $\lambda$. Mean = variance = $\lambda$. The limit of binomial when $n \to \infty$, $p \to 0$, $np = \lambda$.
5. **Normal**: continuous, symmetric, bell-shaped. Parameters $\mu, \sigma^2$. The 68-95-99.7 rule. The Z-transform standardises any normal to $N(0, 1)$. Appears everywhere as a result of the CLT.
6. **Geometric/exponential**: discrete and continuous "waiting time" distributions. Memoryless. Useful in survival analysis and queueing.

If you can recognise each distribution from a verbal description of the situation ("counts in a fixed window," "binary trials repeated $n$ times," "waiting until first event") and quote its mean and variance from memory, you have what you need for the rest of the book.

---

## 6.11 What this builds on / where this returns

**Builds on:** Chapter 5 — random variables, PMF/PDF, expectation, variance, linearity of expectation. We used all of it here.

**Returns:**

- **Bernoulli** is the label model in *Chapter 32*'s derivation of logistic regression from maximum likelihood. The binary cross-entropy loss is the negative log-likelihood under a Bernoulli.
- **Binomial and Poisson** are the test statistics for **rare-event detection** in *Chapter 10* and **drift detection** in Part L.
- **Multinomial** is the label model for multi-class softmax in *Chapter 37* (Naive Bayes uses it for word counts) and again in *Chapter 47* (multi-class evaluation).
- **Normal** is the residual model in *Chapter 31* (linear regression / OLS), the basis for confidence intervals in *Chapter 10*, the asymptotic distribution of estimators in *Chapter 9*, and the foundation of many evaluation-metric distributions.
- **The CLT-flavored "sum of independent things looks normal"** intuition is the engine of *Chapter 9*.
- **Exponential** appears in survival-analysis flavored treatments of churn and time-to-event later in your career; not deeply in this book.

---

## 6.12 Exercises

1. **Bernoulli from PMF.** Write the Bernoulli PMF using the compact form $p^x (1-p)^{1-x}$. Verify it gives the right value for $x = 0$ and $x = 1$. Then verify by direct sum that it sums to 1.

2. **Binomial PMF computation.** A coin has $p = 0.4$. Flip it 5 times. Compute $P(\text{exactly 2 heads})$ by hand using the binomial PMF. Then compute $\mathbb{E}[\text{number of heads}]$ and $\text{Var}[\text{number of heads}]$.

3. **Binomial mean by linearity.** Show that for $S \sim \text{Binomial}(n, p)$, $\mathbb{E}[S] = np$ using linearity of expectation. (Two lines of argument.)

4. **Poisson by hand.** A call center receives an average of 5 calls per minute. Assuming Poisson, compute (a) the probability of zero calls in a minute, (b) the probability of exactly 5 calls in a minute, (c) the probability of 10 or more calls in a minute (use software for the tail).

5. **Binomial-to-Poisson limit.** A web service handles 1,000,000 requests per day, and the per-request probability of a crash is $10^{-6}$. Approximate the distribution of daily crashes. What's its expected number? What's the probability of zero crashes in a given day?

6. **Normal Z-scores.** A normal distribution has $\mu = 50$, $\sigma = 5$. What is the Z-score of an observation of 62? Of 38? What does the 68-95-99.7 rule tell you about how unusual each is?

7. **Normal area, by hand.** Using only the 68-95-99.7 rule and symmetry, estimate $P(X > \mu + \sigma)$ for any normal $X$. (No tables.)

8. **Multinomial reasoning.** A 3-class classifier outputs probabilities `[0.7, 0.2, 0.1]` for `[cat, dog, bird]` on a given image. Each image's label is drawn from this categorical (multinomial with $n=1$) distribution. If you had 100 images, all with this same probability vector, how many would you expect to be cats? With what standard deviation?

9. **Recognise the distribution.** For each scenario, name the right distribution and its parameters:
   1. The number of typos in a 10-page document, given that typos appear at rate 0.2 per page.
   2. Whether a particular email is spam.
   3. The number of red balls drawn in 20 draws with replacement from an urn that is 30% red.
   4. The waiting time (in seconds) until the next visitor arrives at a website that gets 100 visitors per minute.
   5. The number of flips until the first heads on a fair coin.

10. **Mean vs. variance for Poisson.** Suppose you observe counts of customer arrivals per hour over 30 days. The empirical mean is 8 per hour; the empirical variance is 22 per hour. Is the Poisson a good model? Why or why not?

11. **Variance addition gone wrong.** Let $X_1, X_2$ be the values from two rolls of a die. Without computing, predict whether $\text{Var}[X_1 + X_2]$ equals $\text{Var}[X_1] + \text{Var}[X_2]$. Now let $Y_1 = X_1$ and $Y_2 = X_1$ (the same die value, copied). Is $\text{Var}[Y_1 + Y_2] = \text{Var}[Y_1] + \text{Var}[Y_2]$? Explain.

12. **Code computation.** Using `scipy.stats`, compute the probability that a $\text{Binomial}(100, 0.05)$ random variable is at most 3. Compute the same probability under a Poisson approximation. Are they close? Should they be?

<details>
<summary>Answers</summary>

1. At $x = 1$: $p^1 (1-p)^0 = p$. At $x = 0$: $p^0 (1-p)^1 = 1-p$. Sum: $p + (1-p) = 1$. ✓

2. $P(\text{2 heads}) = \binom{5}{2} (0.4)^2 (0.6)^3 = 10 \cdot 0.16 \cdot 0.216 = 0.3456$. Mean = $5 \cdot 0.4 = 2$. Variance = $5 \cdot 0.4 \cdot 0.6 = 1.2$.

3. $S = X_1 + X_2 + \ldots + X_n$, each $X_i$ Bernoulli$(p)$ with $\mathbb{E}[X_i] = p$. By linearity, $\mathbb{E}[S] = \sum \mathbb{E}[X_i] = np$.

4. (a) $P(X = 0) = e^{-5} \approx 0.00674$, about 0.7%. (b) $P(X = 5) = 5^5 e^{-5}/120 = 3125 \cdot 0.00674 / 120 \approx 0.175$, about 17.5%. (c) From `scipy.stats.poisson(5).sf(9)`, about 0.032, 3.2%.

5. $np = 10^6 \cdot 10^{-6} = 1$. Poisson$(\lambda = 1)$. $P(0 \text{ crashes}) = e^{-1} \approx 0.368$, about 37%.

6. $Z(62) = (62 - 50)/5 = 2.4$. $Z(38) = (38 - 50)/5 = -2.4$. A z-score of 2.4 is just outside ±2σ (where 95% of values lie), so each is at roughly the 99th-percentile-tail-ish — about 0.8% chance of being more extreme on either side, or roughly 1.6% combined.

7. The 68% rule says $P(|Z| < 1) \approx 0.68$, so $P(|Z| > 1) \approx 0.32$. By symmetry $P(Z > 1) \approx 0.16$.

8. Expected number of cats = $100 \cdot 0.7 = 70$ (the marginal of the multinomial in the cat dimension is Binomial(100, 0.7)). Variance = $100 \cdot 0.7 \cdot 0.3 = 21$. Standard deviation = $\sqrt{21} \approx 4.58$. Typical sample has 70 cats give-or-take 5.

9. (a) Poisson$(\lambda = 2)$ — 10 pages × 0.2 per page. (b) Bernoulli$(p)$ where $p$ is the spam probability. (c) Binomial$(20, 0.3)$. (d) Exponential with rate $\lambda = 100$/min = $5/3$ per second, so mean wait $= 0.6$ s. (e) Geometric$(0.5)$.

10. Probably not. The Poisson would predict variance ≈ mean = 8. Observed variance of 22 is much larger — "over-dispersion." Suggests arrivals are clustered or the rate varies (rush hour vs. quiet hour). Consider negative binomial or a mixture model.

11. For independent $X_1, X_2$: yes, variances add. For $Y_1 = Y_2 = X_1$: $\text{Var}[Y_1 + Y_2] = \text{Var}[2X_1] = 4\text{Var}[X_1]$. But $\text{Var}[Y_1] + \text{Var}[Y_2] = 2\text{Var}[X_1]$. They disagree by a factor of 2 because $Y_1, Y_2$ are perfectly correlated; the missing term is $2 \text{Cov}[Y_1, Y_2] = 2\text{Var}[X_1]$.

12. `stats.binom(100, 0.05).cdf(3)` ≈ 0.258. `stats.poisson(5).cdf(3)` ≈ 0.265. Very close — about 0.7 percentage points apart. They *should* be close, because with $n = 100$ large and $p = 0.05$ small, $np = 5$ is moderate; this is exactly the regime where the binomial-to-Poisson limit applies.

</details>
