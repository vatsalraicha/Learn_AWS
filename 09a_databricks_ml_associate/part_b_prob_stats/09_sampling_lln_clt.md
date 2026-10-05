# Chapter 9 — Sampling, the Law of Large Numbers, and the Central Limit Theorem

> **Goal of this chapter:** to bridge the gap between *the world's true distributions* (which we cannot see) and *the samples we draw from them* (which we work with). We never see the true mean of click-through rates; we see the empirical mean across yesterday's traffic. We never see the true distribution of returns on a model variant; we see a finite holdout of measurements. Two foundational theorems govern this gap. The Law of Large Numbers says that sample averages converge to true means as the sample grows. The Central Limit Theorem says *more* — that the sampling distribution of those averages takes a specific shape (normal) with a specific spread ($\sigma / \sqrt{n}$). These two theorems are why statistics works at all, and they underpin every confidence interval, every cross-validation estimate, every "we tested on 10,000 examples and got an AUC of 0.873 ± 0.004" statement you will ever read.

---

## 9.1 We can never see the truth

The setup is humble and important. Somewhere "out there" — in the world's data-generating process — is a probability distribution that we'd like to know about. The true click-through rate of a recommendation. The true error rate of a classifier on all future emails. The true median household income of a country. We do not have access to it. What we have is a *sample* — finitely many independent observations.

Three honest questions:

1. **Convergence.** As the sample grows, do statistics computed on it (mean, variance, quantiles) approach the corresponding true population quantities? If yes, in what sense?
2. **Sampling distribution.** For a finite sample, those statistics are themselves random — different samples give different estimates. What is the distribution of, say, the sample mean across many samples?
3. **Quantification of uncertainty.** Given a single sample, can we say something like "the true mean is between A and B with 95% confidence"? On what basis?

Question 1 is answered by the **Law of Large Numbers**. Question 2 is answered by the **Central Limit Theorem**. Question 3 — confidence intervals — is the subject of Chapter 10 and is built directly on top of CLT.

These three are the heart of statistical inference. They are also, in the typical applied curriculum, often skipped past in favor of computational recipes. We will go through them carefully.

---

## 9.2 iid samples

Throughout this chapter we will assume our observations are **iid** — independent and identically distributed. The two pieces:

- **Identically distributed:** each observation is drawn from the same distribution.
- **Independent:** the value of any observation gives you no information about the others.

If you are estimating the average height of US adults and you randomly sample 1,000 people from across the country, those are iid (each one's height is drawn from the population distribution; one person's height tells you nothing extra about another's). If you sample 1,000 people from the same household, they are *not* iid — within a household, heights are correlated (genetics, shared nutrition).

The iid assumption is the foundation of almost all statistical estimation theory. It can be relaxed, but every relaxation costs you. For ML, iid is the working assumption for tabular data (the rows of your training set, supposedly drawn iid from some population). For time-series and graph data it doesn't hold and you need different machinery. For the rest of this chapter, iid.

---

## 9.3 The sample mean and sample variance

Given $n$ iid observations $X_1, X_2, \ldots, X_n$, two natural summaries:

**Sample mean:**

$$
\bar{X}_n = \frac{1}{n} \sum_{i=1}^{n} X_i.
$$

**Sample variance:** (we'll explain the $n-1$ choice carefully in a moment)

$$
S^2_n = \frac{1}{n - 1} \sum_{i=1}^{n} (X_i - \bar{X}_n)^2.
$$

These are *random variables* — they're functions of the observed sample, which is itself random. Each is an *estimator* of the corresponding population quantity:

- $\bar{X}_n$ estimates $\mu = \mathbb{E}[X]$.
- $S^2_n$ estimates $\sigma^2 = \text{Var}[X]$.

The estimators have their own distributions, called **sampling distributions**, that describe how the estimates would vary if we re-ran the sampling procedure many times.

### 9.3.1 The expectation of the sample mean

A reassuring fact: $\mathbb{E}[\bar{X}_n] = \mu$. This is one line of algebra:

$$
\mathbb{E}[\bar{X}_n] = \mathbb{E}\left[\frac{1}{n} \sum_{i=1}^n X_i\right] = \frac{1}{n} \sum_{i=1}^n \mathbb{E}[X_i] = \frac{1}{n} \cdot n \mu = \mu. \quad \blacksquare
$$

Each $X_i$ has expectation $\mu$ (identically distributed); by linearity, the expectation of the sum is $n\mu$; divide by $n$. The sample mean is an **unbiased** estimator of the population mean — its expectation is exactly the parameter it estimates.

### 9.3.2 The variance of the sample mean

A more interesting fact:

$$
\text{Var}[\bar{X}_n] = \frac{\sigma^2}{n}.
$$

Let's derive it. By independence of the $X_i$, the variance of their sum is the sum of their variances:

$$
\text{Var}\left[\sum_{i=1}^n X_i\right] = \sum_{i=1}^n \text{Var}[X_i] = n \sigma^2.
$$

(Independence is crucial — without it, covariance terms would appear.) Then:

$$
\text{Var}[\bar{X}_n] = \text{Var}\left[\frac{1}{n} \sum_{i=1}^n X_i\right] = \frac{1}{n^2} \cdot n \sigma^2 = \frac{\sigma^2}{n}.
$$

(We used $\text{Var}[cX] = c^2 \text{Var}[X]$ from Chapter 5.)

So the sample mean has variance $\sigma^2 / n$ and standard deviation $\sigma / \sqrt{n}$. This $\sigma / \sqrt{n}$ is called the **standard error of the mean**. It is the most-used quantity in all of applied statistics.

Pause on that. Doubling your sample size does not halve the standard error — it reduces it by a factor of $\sqrt{2} \approx 1.41$. To halve the standard error, you need to *quadruple* the sample. To get 10× precision, you need 100× the data. This is the "$\sqrt{n}$ law" that governs how much data you need, and it is brutal news for engineers who hoped that adding a few more samples would dramatically tighten their estimates.

### 9.3.3 The $n-1$ in the sample variance — Bessel's correction

Why divide by $n - 1$ rather than $n$ when computing the sample variance? This is a famous subtlety worth understanding rather than memorising.

Define two candidate variance estimators:

$$
\tilde{S}^2 = \frac{1}{n} \sum_{i=1}^n (X_i - \bar{X}_n)^2 \quad \text{(uses } n \text{)},
$$

$$
S^2 = \frac{1}{n - 1} \sum_{i=1}^n (X_i - \bar{X}_n)^2 \quad \text{(uses } n-1 \text{)}.
$$

**Claim:** $\mathbb{E}[\tilde{S}^2] = \frac{n-1}{n} \sigma^2$ (biased), while $\mathbb{E}[S^2] = \sigma^2$ (unbiased).

The bias of $\tilde{S}^2$ comes from using $\bar{X}_n$ (the sample mean) instead of $\mu$ (the true mean) when measuring deviations. The sum of squared deviations *from the sample mean* is systematically smaller than it would be from any other reference point — that's a property of $\bar{X}_n$ being the value that minimises the sum of squared deviations. So we're underestimating, and dividing by $n - 1$ instead of $n$ inflates the estimate just enough to fix it.

**Derivation sketch.** Start with the algebraic identity

$$
\sum_{i=1}^n (X_i - \bar{X}_n)^2 = \sum_{i=1}^n (X_i - \mu)^2 - n (\bar{X}_n - \mu)^2.
$$

(This is one of those identities that falls out of expanding and rearranging; you should be able to verify it by direct expansion if you sit with it.) Take expectations:

$$
\mathbb{E}\left[\sum_{i=1}^n (X_i - \bar{X}_n)^2\right] = \sum_{i=1}^n \mathbb{E}[(X_i - \mu)^2] - n \mathbb{E}[(\bar{X}_n - \mu)^2].
$$

The first sum: each term is $\sigma^2$ (definition of variance), giving $n \sigma^2$.

The second term: $\mathbb{E}[(\bar{X}_n - \mu)^2] = \text{Var}[\bar{X}_n] = \sigma^2 / n$, so the whole second term is $n \cdot \sigma^2/n = \sigma^2$.

So:

$$
\mathbb{E}\left[\sum_{i=1}^n (X_i - \bar{X}_n)^2\right] = n \sigma^2 - \sigma^2 = (n - 1) \sigma^2.
$$

Divide by $n - 1$:

$$
\mathbb{E}[S^2] = \frac{(n - 1) \sigma^2}{n - 1} = \sigma^2. \quad \blacksquare
$$

So $S^2$ (with $n-1$ in the denominator) is unbiased; $\tilde{S}^2$ (with $n$) is biased low by a factor of $(n-1)/n$.

For large $n$ the difference is negligible. For small $n$ it matters. NumPy's `np.var` defaults to dividing by $n$ (`ddof=0`); to get the unbiased version, use `np.var(x, ddof=1)`. Pandas defaults to $n-1$ in `.var()`. The discrepancy is a source of unnecessary confusion; remember which convention your tool uses.

A subtle conceptual point: people sometimes describe Bessel's correction as "because we used one degree of freedom to estimate the mean." This is a useful intuition. The sum of squared deviations involves the sample mean $\bar{X}_n$, which is itself estimated from the data. The information used to estimate $\bar{X}_n$ — one number's worth, one "degree of freedom" — is no longer available to estimate variance. We have $n - 1$ effective degrees of freedom for variance estimation. This intuition becomes more rigorous in the theory of linear models, where degrees-of-freedom corrections proliferate.

---

## 9.4 The Law of Large Numbers

We are now ready to state the first theorem.

### 9.4.1 The statement

**Law of Large Numbers (LLN):** Let $X_1, X_2, \ldots$ be iid random variables with $\mathbb{E}[X_i] = \mu$ and $\text{Var}[X_i] = \sigma^2 < \infty$. Let $\bar{X}_n = (X_1 + \ldots + X_n) / n$. Then as $n \to \infty$:

$$
\bar{X}_n \to \mu \quad \text{(in an appropriate sense).}
$$

The "appropriate sense" comes in two flavors:

- **Weak LLN (WLLN):** $\bar{X}_n$ converges to $\mu$ *in probability*. For any $\epsilon > 0$, $P(|\bar{X}_n - \mu| > \epsilon) \to 0$ as $n \to \infty$.
- **Strong LLN (SLLN):** $\bar{X}_n$ converges to $\mu$ *almost surely*. $P(\lim_{n \to \infty} \bar{X}_n = \mu) = 1$.

The strong version is, well, stronger — it talks about the limit of a single sequence, not about probabilities of "bad" outcomes shrinking. For our purposes the two are interchangeable; the takeaway is the same: large samples produce estimates close to the truth.

The proofs are not difficult — Chebyshev's inequality gives the weak LLN in three lines; the strong LLN requires a bit more machinery — but they are not on the curriculum and we will not pause for them.

### 9.4.2 What LLN does *and does not* say

It does say: as $n$ grows, the sample mean converges to the true mean.

It does **not** say: any particular sample mean is "close" to the true mean. For finite $n$, $\bar{X}_n$ is still random; the LLN guarantees the limit but not the speed.

It does **not** say: extremely unlikely deviations don't happen. They do, just rarely. The LLN is a statement about the asymptotic behaviour.

It does **not** say: the gambler's fallacy is rational. If a fair coin has come up heads ten times in a row, the LLN does *not* say "the next flip is more likely to be tails to balance things out." Each flip is iid; what the LLN guarantees is that after many *more* flips, the proportion will approach 0.5, but it does so by *dilution*, not by *correction*. The first ten heads remain — they're just outweighed by future flips.

### 9.4.3 LLN in code: the coin flip

Let's see the LLN in action with the simplest possible simulation.

```python
import numpy as np

# Simulate flipping a fair coin many times, tracking the running mean
rng = np.random.default_rng(seed=42)
n_max = 10_000
flips = rng.binomial(1, 0.5, size=n_max)   # 1 = heads, 0 = tails

# Cumulative mean: at each step n, the average of the first n flips
running_mean = np.cumsum(flips) / np.arange(1, n_max + 1)

# Look at the running mean at various sample sizes
checkpoints = [10, 100, 1000, 10000]
for n in checkpoints:
    print(f"n={n:>5}  mean={running_mean[n-1]:.4f}  deviation from 0.5: {abs(running_mean[n-1] - 0.5):.4f}")
```

Running this (or similar) produces output like:

```
n=   10  mean=0.4000  deviation from 0.5: 0.1000
n=  100  mean=0.5300  deviation from 0.5: 0.0300
n= 1000  mean=0.4950  deviation from 0.5: 0.0050
n=10000  mean=0.5021  deviation from 0.5: 0.0021
```

The pattern is exactly what LLN predicts. Early samples are noisy (after 10 flips the mean can easily be off by 0.1 or more); later samples settle close to 0.5. The convergence is *slow* — note that 1000 flips still gave a deviation of 0.005, and to halve that you'd need 4000 flips. The $\sqrt{n}$ rate at work.

If you plotted the running mean vs. sample size, you'd see a curve that wanders early and settles toward 0.5 with shrinking oscillations. That picture *is* the LLN.

### 9.4.4 Why LLN matters for ML

Every time you evaluate a model on a finite test set and compute a metric — accuracy, AUC, RMSE — you are computing the average of some loss across the test examples. By LLN, that average converges to the population expectation as the test set grows. Without LLN you would have no reason to believe that an accuracy of 0.873 on a 30,000-example test set told you anything about the model's behaviour on the next email.

The LLN is the *reason* sample-based estimation works at all. The CLT is the reason you can *quantify the uncertainty* in those estimates.

---

## 9.5 The Central Limit Theorem

The headline act. The most consequential theorem in applied statistics.

### 9.5.1 The statement

**Central Limit Theorem (CLT):** Let $X_1, X_2, \ldots$ be iid random variables with $\mathbb{E}[X_i] = \mu$ and $\text{Var}[X_i] = \sigma^2 < \infty$. Let $\bar{X}_n = (X_1 + \ldots + X_n)/n$. Then as $n \to \infty$:

$$
\frac{\bar{X}_n - \mu}{\sigma / \sqrt{n}} \to N(0, 1) \quad \text{(in distribution).}
$$

Equivalently:

$$
\bar{X}_n \to N\left(\mu, \frac{\sigma^2}{n}\right) \quad \text{(in distribution)},
$$

where the right-hand side is a normal distribution with mean $\mu$ and variance $\sigma^2 / n$.

**Read this carefully.** The theorem says that the sample mean — *regardless of the underlying distribution of the $X_i$* — has a sampling distribution that approaches normal as $n$ grows. The shape of the original distribution can be uniform, exponential, log-normal, anything (with finite variance); the sample mean's distribution still ends up normal.

This is astonishing. It is the deep reason the normal distribution shows up everywhere in nature and in statistics. Anything that can be conceptualised as a "sum or average of many small independent effects" tends toward normal, regardless of the effects' individual shapes. Heights are sums of many small genetic and environmental effects → normal. Test scores are sums of many small effects on each question's outcome → normal. Average sales per customer over a quarter → normal (approximately).

### 9.5.2 What "converges in distribution" means

The convergence is not pointwise — we are not claiming $\bar{X}_n$'s actual values approach a normal random variable's values. We are claiming the *distribution* of $\bar{X}_n$ approaches the normal distribution. Concretely:

$$
\lim_{n \to \infty} P\left(\frac{\bar{X}_n - \mu}{\sigma / \sqrt{n}} \leq z\right) = \Phi(z) \quad \text{for all } z,
$$

where $\Phi$ is the standard normal CDF. The CDF of the standardised sample mean approaches the standard normal CDF.

### 9.5.3 The proof, in spirit

We will not give the full proof — it uses characteristic functions and Taylor expansions — but here is the rough idea.

Each $X_i$ has its own distribution with mean $\mu$ and variance $\sigma^2$. Consider its **characteristic function** $\varphi_X(t) = \mathbb{E}[e^{itX}]$, a complex-valued function that uniquely determines the distribution. By Taylor expansion around $t = 0$, $\varphi_X(t) \approx 1 + i\mu t - \frac{\sigma^2 + \mu^2}{2} t^2 + O(t^3)$.

The standardised sample mean $Z_n = (\bar{X}_n - \mu) / (\sigma/\sqrt{n})$ has characteristic function

$$
\varphi_{Z_n}(t) = \left(\varphi_X\left(\frac{t}{\sigma \sqrt{n}}\right)\right)^n \cdot e^{-it \mu \sqrt{n}/\sigma}
$$

(after simplifying). Substituting the Taylor expansion and taking the limit as $n \to \infty$ gives $\varphi_{Z_n}(t) \to e^{-t^2/2}$, which is the characteristic function of the standard normal. By the uniqueness of characteristic functions, $Z_n$ converges in distribution to $N(0, 1)$.

That is the structural skeleton. The detail-work is in justifying the limit interchange, which requires more careful analysis. The proof is a routine graduate-level exercise; we mention it so you know it exists and rests on solid ground, not on hope.

### 9.5.4 Caveats and when CLT fails

CLT requires:

1. **Finite variance.** Without it, the theorem fails — sample means of Cauchy-distributed variables, for example, don't converge to anything (the Cauchy has infinite variance, and the sample mean of Cauchys is itself Cauchy, regardless of $n$).
2. **Independence.** With heavy positive correlation, the effective sample size is much smaller than $n$, and convergence to normality is slower or fails outright.
3. **Identical distribution** — though there are generalised CLTs (Lindeberg-Feller, etc.) that relax this.
4. **Large enough $n$.** "Large enough" depends on the underlying distribution's shape. For roughly symmetric distributions, $n = 30$ is often "good enough." For very skewed distributions (e.g., income data), you may need hundreds or thousands.

When CLT is approximately valid is a judgement call. For most ML problems — model evaluation on thousands of test examples, A/B testing on millions of impressions — CLT is in force and we use it freely.

---

## 9.6 Empirical demonstration of CLT

Now the most viscerally satisfying experiment in this chapter. Let's take a wildly non-normal distribution, sample from it, take sample means, and watch the distribution of those sample means become normal.

Start with the uniform distribution on $[0, 1]$. Its mean is $0.5$ and variance $1/12 \approx 0.0833$. The shape is *flat* — nothing about it looks normal.

```python
import numpy as np

rng = np.random.default_rng(seed=42)

# Step 1: draw 10,000 samples of size n=1 from Uniform(0,1)
# These are just the underlying values; their distribution is flat
n = 1
many_samples = rng.uniform(0, 1, size=(10_000, n))
sample_means = many_samples.mean(axis=1)  # n=1 case: this is just the original values

# Mean and std of this collection
print(f"n={n}: mean(means) = {sample_means.mean():.4f},  std(means) = {sample_means.std():.4f}")
# Expected: mean ≈ 0.5, std ≈ 1/sqrt(12) ≈ 0.289
```

The histogram of the "sample means" with $n=1$ is just the histogram of the uniform — a flat box from 0 to 1.

Now repeat with $n = 30$:

```python
n = 30
many_samples = rng.uniform(0, 1, size=(10_000, n))
sample_means = many_samples.mean(axis=1)

print(f"n={n}: mean(means) = {sample_means.mean():.4f},  std(means) = {sample_means.std():.4f}")
# Expected mean ≈ 0.5
# Expected std = sigma / sqrt(n) = (1/sqrt(12)) / sqrt(30) ≈ 0.0527
```

Compare:

- Sample-of-1 from uniform: distribution is flat. Mean 0.5, std 0.289.
- Sample-of-30 mean: distribution is *normal-looking*, peaked at 0.5, std ≈ 0.053.

Histogram of the 10,000 sample means (for $n=30$) would show a clean bell curve centered at 0.5 with the predicted standard deviation. The flatness is gone; what's left is a Gaussian.

The lesson: even though we drew from a uniform — about as non-normal as it gets — averaging just 30 samples produced means whose distribution is essentially normal. This is the CLT in action.

A larger experiment, sweeping $n$:

```python
from scipy import stats

rng = np.random.default_rng(seed=42)

for n in [1, 2, 5, 10, 30, 100]:
    samples = rng.uniform(0, 1, size=(10_000, n))
    means = samples.mean(axis=1)
    
    # Standardize: how close are these to N(0, 1) after centering and scaling?
    standardised = (means - 0.5) / ((1/np.sqrt(12)) / np.sqrt(n))
    
    # Kolmogorov-Smirnov test against N(0,1) — close to 0 means closer to normal
    ks_stat, _ = stats.kstest(standardised, "norm")
    print(f"n={n:>3}:  KS stat vs N(0,1) = {ks_stat:.4f}")
```

You should see KS statistics that decrease as $n$ grows. By $n = 30$, the KS statistic is small; by $n = 100$, it's smaller still. The empirical convergence to normality is fast and visible.

A useful exercise: replace the uniform with an exponential distribution (`rng.exponential(scale=1.0, ...)`), which is even more skewed. The CLT still works — but you'll need a larger $n$ to see it.

---

## 9.7 Why $\sqrt{n}$ — and the precision-doubles-cost-quadruples story

We have seen the $\sqrt{n}$ already, in section 9.3.2: the standard error of the sample mean is $\sigma/\sqrt{n}$. CLT gives us more — it says the entire sampling distribution shrinks at this rate.

The practical implications.

**To halve your uncertainty, quadruple your data.** If a sample of 1,000 gave you standard error 0.03, you need a sample of 4,000 to get standard error 0.015. To halve again, you need 16,000. To halve again, 64,000. This is the cost of precision — and it's why dataset size is so often the binding constraint in applied work.

**Diminishing returns.** Going from 10,000 to 100,000 samples reduces standard error by a factor of $\sqrt{10} \approx 3.16$ — useful, but not transformative. Going from 100,000 to 1,000,000 only buys you another $\sqrt{10}$. This is why the question "do I need more data or more careful features" doesn't have an obvious answer — sometimes feature engineering buys you more than scaling up data.

**Comparing two means.** If you have two groups of size $n$ each and want to compare their means, the standard error of the *difference* is $\sqrt{\sigma_1^2/n + \sigma_2^2/n}$ — still scaling as $1/\sqrt{n}$. Detecting an effect of size $\delta$ requires roughly $n \propto (\sigma/\delta)^2$ samples per group. Detecting a 0.5%-relative-improvement in click-through rate, when CTR is around 5% with the variance $0.05 \cdot 0.95 = 0.0475$, requires *millions* of impressions. This is the math of every A/B test you'll ever run.

---

## 9.8 The bootstrap — a quick preview

The CLT tells us the *theoretical* sampling distribution of the sample mean. What if we want the sampling distribution of something more complex — a median, a quantile, a model's AUC — for which we have no closed-form theory?

The **bootstrap**, invented by Bradley Efron in 1979, provides an answer that is both computationally simple and statistically sound. The idea: simulate the sampling process by *resampling from the sample itself*, with replacement.

Concretely. Suppose you have a sample of $n$ observations, and you want the sampling distribution of some statistic $T$ computed from it. The bootstrap procedure:

1. Draw a "bootstrap sample" of size $n$ from your original sample, *with replacement*. (Some observations appear multiple times; some are omitted.)
2. Compute $T$ on this bootstrap sample.
3. Repeat steps 1-2, say, 10,000 times. You now have 10,000 bootstrap replicates of $T$.
4. The empirical distribution of these replicates approximates the sampling distribution of $T$.

In code:

```python
def bootstrap_mean_distribution(data, n_boot=10_000, rng=None):
    """Return n_boot bootstrap-resampled means of the input data."""
    if rng is None:
        rng = np.random.default_rng()
    n = len(data)
    boot_means = np.empty(n_boot)
    for b in range(n_boot):
        sample = rng.choice(data, size=n, replace=True)
        boot_means[b] = sample.mean()
    return boot_means

# Example
data = np.random.default_rng(0).normal(loc=10, scale=2, size=200)
boot_means = bootstrap_mean_distribution(data, n_boot=10_000)
print(f"Bootstrap mean of means: {boot_means.mean():.4f}")
print(f"Bootstrap std of means: {boot_means.std():.4f}")
print(f"Theoretical std: {2 / np.sqrt(200):.4f}")  # σ/sqrt(n)
```

The bootstrap standard deviation of the means closely matches the theoretical $\sigma / \sqrt{n}$ — which it should, because the bootstrap is itself a kind of empirical CLT.

The bootstrap is general-purpose. You can use it to compute confidence intervals for any statistic, even when no closed-form theory exists — the median, a quantile, the AUC of a classifier on a test set, the gain in F1 from one model to another. Bootstrap confidence intervals for model metrics are a routine and powerful tool. We will see them again in Chapter 22 (cross-validation) and Chapter 44 (confidence on AUC).

Two cautions:

- The bootstrap assumes iid data. With time-series or hierarchical data, you need variations (block bootstrap, etc.).
- The bootstrap requires enough data — typically dozens to hundreds of observations — to characterise the underlying distribution well. With 5 observations, bootstrap CIs are unreliable.

---

## 9.9 What this looks like in ML evaluation

Take a moment to connect the theory to the practice.

When you compute the accuracy of a classifier on a 30,000-example test set:

- The accuracy is a sample mean of indicator variables (1 if correct, 0 if wrong).
- By LLN, this sample mean converges to the true accuracy as test set size grows.
- By CLT, the sampling distribution of the accuracy is approximately normal with mean = true accuracy and standard error $\sqrt{p(1-p)/n}$ where $p$ is the accuracy. (We're applying CLT to the Bernoulli case, which is exactly the normal approximation to the binomial.)
- For $p \approx 0.95$ and $n = 30{,}000$: standard error = $\sqrt{0.95 \cdot 0.05 / 30000} \approx 0.00126$. So accuracy = 0.95 ± 0.0025 (95% CI, applying the 2-sigma rule from Chapter 6).

This is how "accuracy 0.95 ± 0.0025" claims are derived. They are statements about CLT-justified normal approximations to sampling distributions. In Chapter 10 we'll make the confidence-interval construction explicit; here it is, working from first principles.

The same machinery gives you uncertainty on:
- ROC AUC (Chapter 43).
- Precision and recall (with appropriate adjustments for the rare-positive case).
- The improvement between two models (Chapter 46).
- Cross-validation estimates of generalisation error (Chapter 22).

Every "we evaluated and got X with confidence ±Y" claim is a CLT claim underneath.

---

## 9.10 Code: putting it all together

A consolidated example. Let's simulate evaluating a classifier with true accuracy 0.85 on test sets of growing size, and confirm that the sample-accuracy estimates have approximately normal sampling distributions with the predicted standard error.

```python
import numpy as np

rng = np.random.default_rng(seed=42)

true_accuracy = 0.85
n_repeats = 5_000   # we'll "rerun the test set creation" this many times

for n_test in [100, 1_000, 10_000, 100_000]:
    # Simulate the test process n_repeats times
    correctness = rng.binomial(1, true_accuracy, size=(n_repeats, n_test))
    sample_accuracies = correctness.mean(axis=1)
    
    empirical_mean = sample_accuracies.mean()
    empirical_std = sample_accuracies.std()
    theoretical_std = np.sqrt(true_accuracy * (1 - true_accuracy) / n_test)
    
    print(f"n_test={n_test:>6}: empirical mean={empirical_mean:.4f}, "
          f"empirical std={empirical_std:.5f}, theoretical std={theoretical_std:.5f}")
```

Sample output:

```
n_test=   100: empirical mean=0.8500, empirical std=0.03581, theoretical std=0.03571
n_test=  1000: empirical mean=0.8500, empirical std=0.01133, theoretical std=0.01129
n_test= 10000: empirical mean=0.8500, empirical std=0.00357, theoretical std=0.00357
n_test=100000: empirical mean=0.8500, empirical std=0.00113, theoretical std=0.00113
```

Three things to notice. First, the empirical mean is essentially the true 0.85 — that's the LLN. Second, the empirical std matches the theoretical $\sqrt{p(1-p)/n}$ to four decimal places — that's the CLT. Third, the std scales as $1/\sqrt{n}$: going from 100 to 10,000 (100× the data) reduced std by a factor of 10 ($\sqrt{100}$). This is the $\sqrt{n}$ law made tactile.

For each test-set size, the histogram of `sample_accuracies` would be approximately normal — by CLT. The normal approximation lets us state confidence intervals (Chapter 10) and run hypothesis tests (also Chapter 10).

---

## 9.11 What we glossed over

A few honest omissions.

1. **Modes of convergence.** We listed "in probability" and "almost surely" as the two LLN flavors but did not formally distinguish. There are also "in distribution" (CLT) and "in $L^p$" (a different convergence concept). The exact relationships among these are graduate-level material and beyond what we need.

2. **Non-iid data.** Time-series, spatial data, hierarchical/clustered data all violate iid. There are extensions (mixing conditions, dependent CLTs) but they are technical. For the ML Associate exam and most applied work, iid is the working assumption and we flag departures when they matter.

3. **Higher-order corrections to CLT.** The Edgeworth expansion gives finer asymptotic corrections to CLT — useful in small-sample inference, but rarely in ML.

4. **The Berry-Esseen bound.** Quantifies how close the sample mean's distribution is to the normal for finite $n$. The bound says the KS distance is at most $C \cdot \rho / (\sigma^3 \sqrt{n})$ where $\rho$ is the third absolute central moment. For practical purposes, this is the formal justification for "CLT is good enough by $n = 30$ for symmetric distributions, larger for skewed."

5. **Multivariate CLT.** When you average vectors instead of scalars, the limit is a multivariate normal with the natural covariance structure. Used implicitly in many places.

We have the working core.

---

## 9.12 Summary

1. We never see population truths. We see iid samples, and we estimate population parameters from them. The estimators (sample mean $\bar{X}_n$, sample variance $S^2$) are themselves random variables with their own sampling distributions.
2. The **sample mean** $\bar{X}_n$ has $\mathbb{E}[\bar{X}_n] = \mu$ (unbiased) and $\text{Var}[\bar{X}_n] = \sigma^2 / n$ (the standard-error formula). Standard error scales as $1/\sqrt{n}$ — to halve uncertainty, quadruple the sample.
3. The **sample variance** $S^2$ is computed with $n - 1$ in the denominator (Bessel's correction), giving an unbiased estimator of $\sigma^2$. The intuition: we used one degree of freedom to estimate $\bar{X}_n$, so we have $n - 1$ degrees of freedom left for variance.
4. The **Law of Large Numbers** says $\bar{X}_n \to \mu$ as $n \to \infty$. Sample averages converge to true means. This is *why* sample-based estimation works at all.
5. The **Central Limit Theorem** says $\bar{X}_n$'s distribution approaches $N(\mu, \sigma^2/n)$ as $n$ grows — regardless of the shape of the underlying distribution. This is *why* the normal distribution dominates applied statistics.
6. CLT requires finite variance, independence, and $n$ "large enough." For most ML evaluation problems, $n$ is plenty large and CLT is in force.
7. The **bootstrap** is a computational technique that simulates the sampling distribution by resampling. It generalises CLT-based uncertainty quantification to statistics that have no closed-form distribution theory.
8. Every "metric ± standard error" claim in ML evaluation is, underneath, a CLT claim. Confidence intervals (Chapter 10) build on this directly.

---

## 9.13 What this builds on / where this returns

**Builds on:** Chapter 5 (random variables, mean, variance), Chapter 6 (the normal distribution and its 68-95-99.7 properties), Chapter 7 (independence, variance of sums).

**Returns:**

- **Confidence intervals** in *Chapter 10* are direct applications of CLT.
- **Cross-validation theory** in *Chapter 22* uses LLN to argue why CV estimates converge to the true generalisation error, and CLT to put error bars on the estimate.
- **A/B test power analyses** ("how many users do I need?") are CLT computations.
- **Bootstrap confidence intervals on AUC** in *Chapter 44* implement the bootstrap procedure sketched in section 9.8.
- **Drift detection** in Part L uses CLT-derived test statistics to flag when an incoming distribution looks different from the training distribution.
- **Optimisation theory** for stochastic gradient descent (Chapter 17) leans on CLT to argue that minibatch gradient estimates are unbiased with manageable variance.

---

## 9.14 Exercises

1. **Standard error.** A test set of 5,000 examples gives an accuracy of 0.90 for a classifier. Using the Bernoulli variance formula and CLT, compute the standard error and a 95% confidence interval for the true accuracy. (Use the 2σ rule.)

2. **Sample-size scaling.** A first experiment with $n = 1{,}000$ gave standard error 0.03 on some quantity. You want standard error 0.005. How large does $n$ need to be?

3. **Sample mean vs. true mean.** A coin has unknown bias $p$. You flip it 100 times and get 60 heads. (a) What is your point estimate of $p$? (b) What is the standard error of that estimate? (c) Roughly what interval do you have 95% confidence the true $p$ lies in?

4. **Bessel's correction by hand.** Compute the sample variance of the data set $\{2, 4, 4, 4, 5, 5, 7, 9\}$ both ways: dividing by $n$ and dividing by $n - 1$. By how much does Bessel's correction shift the result?

5. **LLN intuition.** A gambler insists that after observing 10 consecutive heads, the next flip is "due" to be tails. Use the LLN to explain why this is wrong. What *is* the LLN saying about the long-run proportion of heads?

6. **CLT condition: finite variance.** Suppose $X_i$ are iid Cauchy-distributed. The Cauchy has infinite variance. What does CLT say about $\bar{X}_n$ here? (Hint: the sample mean of $n$ iid Cauchys is itself Cauchy, no matter how large $n$ is.)

7. **CLT-based normal approximation.** For a Binomial$(100, 0.3)$ random variable, use CLT to approximate $P(X \leq 25)$. Compare with the exact value using `scipy.stats.binom`.

8. **Bootstrap by hand.** Given the sample $\{1, 2, 3, 4, 5\}$, list two different bootstrap samples of size 5 (drawn with replacement). Compute the means of each. Now describe in words what would happen if you repeated this 10,000 times.

9. **What sample size do I need.** You're A/B testing two recommendation algorithms. The current CTR is 5%. You want to detect a true improvement to 5.1% (a relative 2% lift) with high power. The standard error of the difference in proportions is roughly $\sqrt{2 \cdot 0.05 \cdot 0.95 / n}$. About how many impressions per arm do you need so the standard error is small enough that 0.1 percentage point is detectable (say, 2 standard errors)?

10. **Why √n is brutal.** A team claims that doubling their data from 1M to 2M users will halve their uncertainty. Explain why this is wrong, and what doubling the data actually buys.

11. **Sampling distribution of the variance.** Without doing the computation, predict whether $S^2$ — the sample variance — also has a sampling distribution that becomes approximately normal as $n$ grows. Why or why not?

12. **Code task.** Modify the code in section 9.6 to use samples from $\text{Exponential}(1)$ (which has heavy right skew) instead of Uniform(0, 1). Plot histograms of the sample means for $n = 1, 5, 30, 100$. At what $n$ does the distribution start to look normal? Why is the threshold higher than for the uniform?

<details>
<summary>Answers</summary>

1. Standard error = $\sqrt{0.9 \cdot 0.1 / 5000} = \sqrt{0.000018} \approx 0.00424$. 95% CI ≈ $0.90 \pm 2 \cdot 0.00424 = 0.90 \pm 0.0085$, so roughly $[0.892, 0.908]$.

2. SE scales as $1/\sqrt{n}$. To shrink from 0.03 to 0.005 — a factor of 6 — we need $n$ to grow by a factor of $36$. So $n \approx 36{,}000$.

3. (a) $\hat{p} = 60/100 = 0.6$. (b) SE = $\sqrt{0.6 \cdot 0.4 / 100} \approx 0.049$. (c) 95% CI ≈ $0.6 \pm 0.098$, i.e., roughly $[0.50, 0.70]$. Wide — small sample.

4. Mean = $(2+4+4+4+5+5+7+9)/8 = 40/8 = 5$. Squared deviations: 9, 1, 1, 1, 0, 0, 4, 16. Sum = 32. Divided by 8: 4. Divided by 7: 32/7 ≈ 4.571. Bessel's correction shifts by $32/7 - 32/8 = 32 \cdot (1/7 - 1/8) = 32/56 ≈ 0.571$.

5. The LLN does not say "the next flip is more likely to be tails." It says the long-run proportion of heads approaches 0.5. This is by *dilution* (more flips averaging out), not by *correction*. The 10 heads are already in the record; they get drowned out by future flips, not cancelled.

6. CLT does not apply (its finite-variance assumption fails). In fact, the sample mean of $n$ iid Cauchys is itself a Cauchy with the same scale — $\bar{X}_n$ does not concentrate around any value, regardless of $n$. The LLN also fails. This is a famous pathological case.

7. Mean = $np = 30$, variance = $np(1-p) = 21$, std = $\sqrt{21} \approx 4.583$. Z = $(25 - 30)/4.583 \approx -1.091$. $P(Z \leq -1.091) \approx 0.138$. Exact via `binom.cdf(25, 100, 0.3) \approx 0.163`. CLT approximation is off by about 0.025 in this case — modest $n=100$, asymmetric. Continuity correction would help.

8. Bootstrap sample 1: maybe $\{1, 3, 3, 4, 5\}$, mean = 3.2. Bootstrap sample 2: maybe $\{2, 2, 2, 4, 5\}$, mean = 3.0. Repeating 10,000 times produces 10,000 means; their distribution is the bootstrap estimate of the sampling distribution of $\bar{X}$. The original sample's mean is 3.0; the bootstrap means should center on 3.0 with some spread.

9. Standard error of difference: $\sqrt{2 \cdot 0.05 \cdot 0.95 / n}$. Want $2 \cdot \text{SE} = 0.001$ (0.1pp). So $\text{SE} = 0.0005$, $\text{SE}^2 = 2.5 \times 10^{-7}$. Solve: $n = 2 \cdot 0.05 \cdot 0.95 / 2.5 \times 10^{-7} = 0.095/2.5 \times 10^{-7} = 380{,}000$ per arm. Detecting tiny lifts requires very large samples — the reality of running CTR A/B tests.

10. Doubling $n$ shrinks SE by factor $\sqrt{2} \approx 1.41$. Not by 2. So uncertainty drops by about 30%, not 50%. To halve the uncertainty you need 4× the data.

11. Yes — $S^2$ is itself an average (of squared deviations), and for large $n$ its sampling distribution is approximately normal by CLT. (Technically the $\chi^2$ distribution comes in for the exact distribution under normality of the underlying, but asymptotically it's normal.)

12. For the exponential (mean 1, skewed right), the sample mean for $n = 1$ is just exponential-shaped. By $n = 5$ it's still visibly skewed. By $n = 30$ it's nearly normal. By $n = 100$ it's indistinguishable from normal. The threshold is higher than for the uniform because the exponential is more skewed; CLT's convergence rate depends on the underlying distribution's higher moments (the third moment / Berry-Esseen bound).

</details>
