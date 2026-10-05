# Chapter 10 — Hypothesis Testing, p-values, and Confidence Intervals

> **Goal of this chapter:** to give the right framework for the question every ML engineer faces sooner or later: "Is this improvement real, or is it just noise?" We will build the machinery — null and alternative hypotheses, test statistics, p-values, confidence intervals — from the ground up. We will work through one fully detailed example (the t-test for the difference of two means, which is also the workhorse of model A/B comparison) and identify the precise things p-values and confidence intervals *do not* mean. By the end you should be able to read or write the sentence "the difference was statistically significant ($p = 0.03$)" and know exactly what is being claimed, what isn't, and where the framework can mislead.

---

## 10.1 The motivating question

You are evaluating two models. Model A scored AUC 0.872 on a held-out test set. Model B, the new candidate you've been working on for two weeks, scored AUC 0.881. The improvement is 0.009.

Should you ship B?

The shape of an honest answer:

1. **Yes, if** the difference is bigger than what you'd expect from noise alone — the natural variability of AUC estimates on finite test sets. A 0.009 improvement on a tiny test set could be noise; on a million-example test set the same 0.009 improvement is almost certainly real.
2. **Yes, if** the cost of being wrong (shipping B when B is actually no better than A) is acceptable given the operational risk.
3. **No, if** the difference might be a fluke and the cost of shipping a regression is high.

Question 1 is the *statistical* question. Hypothesis testing is the machinery for answering it. We will spend the chapter on that machinery.

Question 2 is the *business* question, separate from but adjacent to the statistical one. We will return to it when we discuss significance vs. effect size.

---

## 10.2 The pipeline of a hypothesis test

The general shape of any hypothesis test:

1. **State two hypotheses.** A null hypothesis $H_0$ (the "boring" hypothesis — usually "no effect," "no difference," "model A and model B are equally good") and an alternative hypothesis $H_1$ (the "interesting" hypothesis — usually "there is an effect," "B is better than A").
2. **Choose a test statistic.** Some function of the data that we expect to be small if $H_0$ is true and large if $H_1$ is true. The choice depends on what we're testing.
3. **Determine the test statistic's distribution under $H_0$.** This is the *null distribution* — the distribution we'd expect to see if there were no real effect, just sampling noise.
4. **Compute the observed test statistic from the data.**
5. **Compute the p-value.** The probability of seeing a test statistic at least as extreme as the observed one, *if $H_0$ were true*.
6. **Compare to a significance level $\alpha$.** Conventionally $\alpha = 0.05$. If $p \leq \alpha$, "reject" $H_0$ — declare that the data is incompatible enough with $H_0$ that we don't believe it. If $p > \alpha$, "fail to reject" $H_0$ — the data is consistent with $H_0$; we don't have evidence against it.

The pipeline looks clean on paper. The conceptual subtleties hide in step 5 — what exactly is a p-value? — and in step 6 — what does "reject" or "fail to reject" really mean?

We will work the pipeline through a concrete example, and then dissect the subtleties.

---

## 10.3 The worked example: comparing two model AUCs

Set up our scenario. Models A and B were each evaluated on the *same* test set of 10,000 examples. Each model produces a score for each example; from these we computed an AUC for A and an AUC for B.

A complication right at the start: because A and B were evaluated on the same test set, their AUC estimates are *not* independent — they share the random sample of test examples. A proper test for the difference of correlated AUCs is the DeLong test, which we won't develop here. For pedagogical simplicity we'll instead use a setup where the two AUC estimates *are* independent — say, A's AUC was measured on an old test set of 10,000 examples and B's on a new, independent test set of 10,000 examples — and treat the two AUC estimates as iid normal random variables (which they are, approximately, by CLT applied to the underlying paired comparisons).

So we have:
- $\hat{\theta}_A = 0.872$ with estimated standard error $\hat{\sigma}_A = 0.005$.
- $\hat{\theta}_B = 0.881$ with estimated standard error $\hat{\sigma}_B = 0.005$.

(The standard error of AUC depends on the test-set size and the data — we computed these via bootstrap or DeLong on our test set; for this example, accept them.)

### 10.3.1 The hypotheses

$$
H_0: \theta_A = \theta_B, \quad H_1: \theta_A \neq \theta_B.
$$

The null hypothesis: the two models have the same true AUC. Any difference we observe is sampling noise. The alternative: the AUCs differ.

We've chosen a *two-sided* alternative — we're testing for "B's AUC differs from A's," without committing to which direction. If we had strong prior reason to expect B to be better, we could choose a one-sided alternative $H_1: \theta_B > \theta_A$; the p-values would be halved. Two-sided is the more conservative default and is what we'll use.

### 10.3.2 The test statistic

A natural quantity to look at is the difference of the two estimates:

$$
\hat{\delta} = \hat{\theta}_B - \hat{\theta}_A = 0.881 - 0.872 = 0.009.
$$

The standard error of this difference, by independence, is

$$
\hat{\sigma}_\delta = \sqrt{\hat{\sigma}_A^2 + \hat{\sigma}_B^2} = \sqrt{0.005^2 + 0.005^2} = \sqrt{0.00005} \approx 0.00707.
$$

(We're using the formula $\text{Var}[X - Y] = \text{Var}[X] + \text{Var}[Y]$ for independent variables, derived in Chapter 7.)

The standardised test statistic — the difference divided by its standard error:

$$
Z = \frac{\hat{\delta}}{\hat{\sigma}_\delta} = \frac{0.009}{0.00707} \approx 1.273.
$$

This is, conceptually, a Z-score: it measures how many standard errors the observed difference is from zero (the null-hypothesis value).

### 10.3.3 The null distribution

Under $H_0$, the true difference is zero, and by CLT (Chapter 9) the estimate $\hat{\delta}$ is approximately normal with mean 0 and standard error $\sigma_\delta$. The standardised statistic $Z$ is approximately standard normal:

$$
Z \sim N(0, 1) \quad \text{under } H_0.
$$

(Technically, since we're estimating $\sigma_\delta$ from data rather than knowing it, the statistic follows a *Student's t* distribution with degrees of freedom depending on the sample sizes. For our large test sets, t and standard normal are essentially identical. For smaller samples the distinction matters.)

### 10.3.4 The p-value

The p-value is the probability, *under $H_0$*, of observing a $Z$ as extreme as 1.273 or more. Since we're using a two-sided test, "as extreme" means $|Z| \geq 1.273$:

$$
p = P(|Z| \geq 1.273 \mid H_0) = 2 \cdot P(Z \geq 1.273) = 2 \cdot (1 - \Phi(1.273)).
$$

From the standard normal CDF, $\Phi(1.273) \approx 0.898$. So $1 - \Phi(1.273) \approx 0.102$, and $p \approx 0.204$.

### 10.3.5 The decision

With $\alpha = 0.05$, $p = 0.204 > 0.05$: we **fail to reject** $H_0$. The observed difference of 0.009 is *not* implausible under the hypothesis that the two models are equally good — it could easily arise from sampling noise.

This does *not* mean B is no better than A. It means our data is insufficient to conclude that B is better. If you had a larger test set with smaller standard errors — say, $\hat{\sigma}_A = \hat{\sigma}_B = 0.002$ — the same observed difference of 0.009 would correspond to $Z = 0.009 / \sqrt{2 \cdot 0.002^2} = 3.18$, $p \approx 0.0015$, and we would reject $H_0$. Same effect size, smaller standard errors, much smaller p-value.

This is the essential lesson: **statistical significance depends on both the effect size and the sample size**. Failing to reject is *not* evidence that the null is true; it is the absence of evidence against it.

---

## 10.4 The t-test, formally

The example we just walked through is, in spirit, a **two-sample t-test for the difference of two means**. Let's name the parts.

### 10.4.1 Setup

You have two independent samples:

- Sample A: $X_1^A, X_2^A, \ldots, X_{n_A}^A$ iid with mean $\mu_A$ and variance $\sigma_A^2$.
- Sample B: $X_1^B, X_2^B, \ldots, X_{n_B}^B$ iid with mean $\mu_B$ and variance $\sigma_B^2$.

You want to test $H_0: \mu_A = \mu_B$ vs. $H_1: \mu_A \neq \mu_B$.

### 10.4.2 The test statistic

Compute sample means $\bar{X}_A, \bar{X}_B$ and sample variances $S_A^2, S_B^2$. The test statistic is:

$$
t = \frac{\bar{X}_B - \bar{X}_A}{\sqrt{S_A^2 / n_A + S_B^2 / n_B}}.
$$

The numerator is the observed difference; the denominator is the standard error of that difference. Under $H_0$, $t$ follows (approximately) a Student's t distribution.

### 10.4.3 Why t and not standard normal?

If we knew the true variances $\sigma_A^2, \sigma_B^2$, the test statistic would follow a standard normal. Because we are estimating $\sigma$ from $S$ — using sample variances — we incur additional uncertainty, and the relevant distribution is the **Student's t**.

The Student's t distribution looks like a normal but with heavier tails — a t with degrees of freedom $\nu$ has more probability mass far from zero than $N(0, 1)$ does. As $\nu \to \infty$, the t converges to the standard normal. For our purposes:

- $\nu < 30$: meaningfully different from normal. Use t-tables or `scipy.stats.t`.
- $\nu \geq 30$: essentially normal. The two give p-values that agree to three decimal places.
- $\nu = $ moderate to large: software handles the t calculation; use it.

For our model-AUC example with thousands of test examples, the degrees of freedom are large enough that we can use the standard normal — which we implicitly did.

### 10.4.4 Code: a complete t-test

```python
import numpy as np
from scipy import stats

rng = np.random.default_rng(seed=42)

# Simulate two samples with a small true effect
n = 100
sample_A = rng.normal(loc=10.0, scale=2.0, size=n)
sample_B = rng.normal(loc=10.3, scale=2.0, size=n)   # true effect 0.3

# Run a two-sample t-test (Welch's t-test allows unequal variances)
t_stat, p_value = stats.ttest_ind(sample_A, sample_B, equal_var=False)
print(f"t = {t_stat:.4f}, p = {p_value:.4f}")

# Manually
diff = sample_B.mean() - sample_A.mean()
se = np.sqrt(sample_A.var(ddof=1)/n + sample_B.var(ddof=1)/n)
t_manual = diff / se
print(f"Manual t = {t_manual:.4f}, diff = {diff:.4f}, se = {se:.4f}")
```

Run this with different sample sizes (n=10, n=100, n=1000). With $n = 100$ and a true effect of 0.3, you'll often get p ≈ 0.3 — failing to detect a real effect. With $n = 1000$, p will drop into the small range. The same true effect can be "not significant" with small samples and "highly significant" with large samples. Always.

---

## 10.5 Type I and Type II errors

The hypothesis-testing framework can make two distinct mistakes.

**Type I error** (false positive): rejecting $H_0$ when $H_0$ is actually true. We declared a real effect when there wasn't one. The probability of a Type I error is $\alpha$ (the significance level we chose). With $\alpha = 0.05$, we accept a 5% chance of falsely claiming an effect.

**Type II error** (false negative): failing to reject $H_0$ when $H_0$ is actually false. There was a real effect, but we didn't detect it. The probability of a Type II error is denoted $\beta$, and $1 - \beta$ is called the **statistical power** of the test. Higher power = lower chance of missing real effects.

A 2x2 table makes the relationships clear:

|                     | $H_0$ is true       | $H_0$ is false      |
|---------------------|---------------------|---------------------|
| **Reject $H_0$**    | Type I error ($\alpha$) | Correct (power $1 - \beta$) |
| **Fail to reject**  | Correct ($1 - \alpha$) | Type II error ($\beta$)     |

Setting $\alpha$ low (e.g., 0.01) reduces false positives but raises the bar for declaring an effect — increasing $\beta$ (false negatives). There is no free lunch; the two errors trade off, and the only way to reduce *both* is to *get more data*.

### 10.5.1 Power analysis

Before running an experiment, sensible engineers do a **power analysis**: given the effect size they want to detect, the variance of the data, and the $\alpha$ they'll use, what sample size do they need to detect the effect with, say, 80% probability?

The formula for the simplest case (two-sample t-test, equal variances, equal sample sizes) is roughly:

$$
n \approx \left(\frac{z_{1 - \alpha/2} + z_{1 - \beta}}{\delta / \sigma}\right)^2,
$$

where $\delta$ is the effect size to detect, $\sigma$ the standard deviation per sample, $z_{1 - \alpha/2}$ and $z_{1 - \beta}$ are standard normal quantiles. For $\alpha = 0.05$ (two-sided), $z_{1 - \alpha/2} \approx 1.96$; for power 80%, $z_{1 - \beta} \approx 0.84$.

The formula has a clear shape: detecting a *small* effect (relative to $\sigma$) requires *large* $n$. The CTR A/B test of Chapter 9.7 made this concrete — detecting 0.1pp lifts at 5% baseline CTR requires hundreds of thousands of impressions per arm.

In ML, you can do power analyses for model comparison: given the standard error of your AUC estimate (which you can compute from a single AUC computation by bootstrap), what sample size do you need to reliably detect a 0.01 improvement? Often the answer is "more test data than you have," at which point the right response is to be honest: "the improvement is real in our test set but our test set is too small to be confident."

---

## 10.6 What a p-value *is* and *is not*

This section is the single most important in the chapter. Misinterpretations of p-values are responsible for an enormous fraction of the misleading statistical claims in science and business.

**A p-value is:** the probability, under $H_0$, of observing a test statistic at least as extreme as the one we observed.

**A p-value is *not*:**

1. **The probability that $H_0$ is true.** This is the most common misinterpretation. The p-value is $P(\text{data} \mid H_0)$, not $P(H_0 \mid \text{data})$. Confusing these is the same error as Chapter 8's prosecutor's fallacy. To get $P(H_0 \mid \text{data})$ you would need a Bayesian framework with a prior on $H_0$, and the answer would depend on that prior.

2. **The probability that the result will replicate.** A p-value of 0.03 does not mean "97% chance the same finding will hold in a replication." Replication probability is a separate question that depends on, among other things, the true effect size, the power of the replication study, and statistical noise.

3. **The effect size.** A p-value tells you how unlikely the observed data is under the null — not how large the effect is. With huge sample sizes, *any* effect, no matter how tiny and practically irrelevant, can produce a tiny p-value. With small sample sizes, even huge effects can produce non-significant p-values. **Significance is not effect size**, and reporting one without the other is misleading.

4. **A statement about whether your specific result is "real."** The p-value is a property of the procedure (over many hypothetical experiments). It is not a probability statement about your particular dataset.

5. **An invitation to keep testing until you find significance.** This is "p-hacking" — running many tests until one comes out below 0.05, then reporting only that one. The 0.05 threshold is calibrated assuming a single, pre-specified test. Multiple testing destroys the calibration. We address this in section 10.8.

These distinctions matter. The American Statistical Association issued a formal statement in 2016 trying to rein in misuse; the misuses continue regardless. Build the habit of pairing every p-value with the effect size and the sample size.

A useful slogan: **a p-value is a measure of evidence against the null, calibrated for a single test, that says nothing about effect size or practical significance.**

---

## 10.7 Confidence intervals

Hypothesis tests answer a yes/no question ("is the effect zero?"). Often more useful is a range: "we estimate the true effect is between such-and-such with 95% confidence." This is a **confidence interval**.

### 10.7.1 Construction

For a sample mean $\bar{X}$ with standard error $\text{SE}$, a 95% confidence interval is approximately

$$
\bar{X} \pm 1.96 \cdot \text{SE}.
$$

The 1.96 is the 97.5th percentile of the standard normal (since 2.5% lies above 1.96 in each tail, leaving 95% in the middle). Equivalently, for a t-distributed statistic with $\nu$ degrees of freedom, use the t-distribution's 97.5th percentile.

The construction generalises: a 95% CI for any estimate is roughly $\hat{\theta} \pm 1.96 \cdot \text{SE}(\hat{\theta})$, when $\hat{\theta}$ is approximately normal (which it is, by CLT, for most well-behaved estimators).

For the model-AUC example:

$$
\hat{\delta} = 0.009, \quad \hat{\sigma}_\delta = 0.00707.
$$

95% CI for the true difference $\delta = \theta_B - \theta_A$:

$$
0.009 \pm 1.96 \cdot 0.00707 = 0.009 \pm 0.0139 = [-0.005, 0.023].
$$

The interval *contains zero*. This is equivalent to "the test does not reject $H_0$ at $\alpha = 0.05$." If the 95% CI for the difference contains zero, the corresponding two-sided hypothesis test at $\alpha = 0.05$ fails to reject the null. This is the formal duality between confidence intervals and hypothesis tests: they encode the same information.

### 10.7.2 Interpretation — and the most common misinterpretation

A 95% confidence interval is *correctly* interpreted as: "the procedure that produced this interval produces intervals that contain the true value 95% of the time, across repeated applications."

It is *incorrectly* interpreted as: "there's a 95% probability the true value is in this specific interval."

The distinction is subtle but real. In the frequentist framework (which is where confidence intervals live), the parameter is a fixed unknown number, not a random variable; it either is or isn't in this interval — the probability is 0 or 1, but you don't know which. The 95% refers to the *long-run frequency* of the interval-construction procedure, not to this particular interval.

For practical purposes the misinterpretation is usually harmless — most people who think "95% chance the truth is in [-0.005, 0.023]" make the right downstream decisions. But for precise communication, the correct phrasing matters: "I'm 95% confident *in the procedure*; this is the interval it gave me on this dataset."

The Bayesian analog of a confidence interval — called a **credible interval** — *does* permit the "95% chance the truth is in the interval" interpretation, because in the Bayesian framework, the parameter has a posterior distribution. The two intervals often look similar numerically; they differ in their conceptual content.

### 10.7.3 Why CIs are usually more informative than p-values

A p-value reports a single number against a binary decision. A confidence interval reports both the estimate and its uncertainty.

- **Significant, big CI excluding zero**: clearly something is there.
- **Significant, narrow CI just barely excluding zero**: something is there, but the effect is small.
- **Not significant, narrow CI containing zero**: we have strong evidence the effect is essentially zero (small).
- **Not significant, wide CI**: insufficient data; we can't tell whether the effect is zero, small, or large.

The p-value distinguishes only the first two from the last two. The confidence interval makes all four cases visible. For any practical decision-making, CIs are usually the better summary.

A useful habit: when reporting an A/B test result or a model comparison, always include the point estimate, the 95% CI, *and* the p-value. Each captures different information.

---

## 10.8 The multiple-testing problem

Suppose you run a single hypothesis test at $\alpha = 0.05$. The chance of a false positive is 5%.

Suppose now you run 20 *independent* hypothesis tests, all at $\alpha = 0.05$, with all 20 nulls true. The chance that *none* of them produces a false positive is $0.95^{20} \approx 0.358$, so the chance that *at least one* does is about 64%. Almost certain.

This is the **multiple-testing problem**, and it is one of the leading causes of irreproducible "discoveries" in science and in industrial ML.

### 10.8.1 Where it shows up

- **Feature selection**: testing whether each of 100 features is associated with the target, at $\alpha = 0.05$. Even if no feature is truly associated, you expect about 5 to look significant by chance.
- **Subgroup analysis**: an A/B test produces no overall effect, so you slice by gender, age, geo, device, browser, day of week — eventually some slice shows a significant effect. The significance is likely spurious.
- **Hyperparameter selection without proper CV**: running 50 hyperparameter configurations on the same validation set and shipping the best. The best is partly genuine, partly noise.
- **Sequential testing**: running an A/B test and checking results daily, stopping the moment p < 0.05. You will eventually cross the threshold even if there is no effect, just by random walk.

### 10.8.2 Bonferroni correction

The simplest fix is to lower the per-test $\alpha$. If you plan to run $m$ tests and want the overall false-positive rate (the "family-wise error rate") to be at most $\alpha_{\text{family}}$, use $\alpha_{\text{per-test}} = \alpha_{\text{family}} / m$. With 20 tests and a target family-wise $\alpha = 0.05$, each individual test uses $\alpha = 0.0025$.

This is the **Bonferroni correction**. It's conservative — it controls the family-wise error rate but at the cost of reducing power. A more nuanced approach is the **false discovery rate** (FDR), introduced by Benjamini and Hochberg in 1995, which controls the *expected fraction* of false discoveries among the rejected nulls rather than the probability of *any* false discovery. FDR-controlled tests have higher power than Bonferroni-corrected tests when many true effects exist, and are now standard in many scientific fields.

For most ML practice, the Bonferroni intuition — "the more tests you run, the smaller each individual p-value needs to be" — is enough to keep you out of trouble. If you find yourself slicing data to look for any kind of significant effect, you are in p-hacking territory and should adjust thresholds accordingly or, better, pre-register a single analysis plan.

---

## 10.9 Significance is not effect size — a parable

I'll close the substantive content of the chapter with a story that captures the most important meta-lesson.

You're running an A/B test of a model change. The test ran for a month, accumulating 10 million observations per arm. The result: a difference in conversion rate of 0.02 percentage points (from 4.50% to 4.52%), with a p-value of 0.001.

The p-value is tiny. The result is "highly statistically significant." Headlines write themselves.

But pause. The effect size is 0.02 percentage points. Is that *practically* significant? Are you confident the engineering cost of shipping the change, the new code paths to maintain, the increased complexity, the risks of unexpected interactions — are these all worth a 0.02 pp lift? Probably not. The result is statistically significant because the sample is enormous; it tells you "the lift is not zero" but says nothing about whether the lift is worth caring about.

The opposite parable also bites. A small early-stage experiment with 200 observations per arm shows a 5pp lift in conversion, but the p-value is 0.12 — not statistically significant. The lift is enormous, but the sample is too small to rule out chance. The right response is "promising but inconclusive; run a larger experiment" — not "no effect detected, abandon the idea."

The meta-lesson: **statistical significance and practical significance are different things**. A complete report includes the point estimate (effect size), the confidence interval (uncertainty), and the p-value (evidence against null) — all three. Stripping any of them away invites bad decisions.

---

## 10.10 Where hypothesis testing matters for ML

A short tour.

**Model comparison.** The natural application — and the example we used. Comparing AUCs, accuracies, or any metric between two models requires accounting for the uncertainty in each estimate. The DeLong test (for paired AUCs), McNemar's test (for paired classifiers on the same examples), and the bootstrap-comparison method are the standard tools. We'll see these in Chapter 46.

**Feature significance.** Logistic regression coefficients and OLS coefficients each come with a standard error and a p-value testing whether the coefficient is zero. This is useful for interpretation — though prone to all the multiple-testing pitfalls when you have many features. Chapter 31-32 will quote these statistics.

**A/B testing.** All A/B test analysis is hypothesis testing under the hood. Get this right or your business decisions will be based on noise.

**Drift detection.** Production ML systems use hypothesis tests to detect when the incoming feature distribution has shifted from the training distribution. A common approach: split the recent production data and compare to training via a Kolmogorov-Smirnov test or a t-test on key statistics. Significant shifts trigger retraining alerts. Part L returns to this.

**Calibration assessment.** Testing whether a classifier's output probabilities match observed frequencies is a statistical test against the null "the classifier is calibrated."

---

## 10.11 What we glossed over

A few honest omissions.

1. **Non-parametric tests.** We described the t-test (which assumes approximate normality). For non-normal data with small samples, Wilcoxon rank-sum and similar tests don't require this assumption. Useful but not on the curriculum.

2. **The DeLong test specifically.** The right way to compare two AUCs on the same test set. We skipped its derivation. If you need to compare classifier AUCs in production, look it up.

3. **Bayesian hypothesis testing.** Replaces the binary reject/fail-to-reject decision with a Bayes factor — the ratio of the data's marginal likelihood under each hypothesis. Cleaner in some ways, but rarely used in routine ML.

4. **Sequential analysis.** Methods that let you check results as the data accumulates, with proper adjustment to maintain valid type-I-error control. These are increasingly used in modern A/B testing platforms but are beyond our scope.

5. **Confidence regions for multivariate parameters.** Confidence intervals generalise to confidence ellipsoids for multiple parameters. We won't construct them, but be aware they exist.

The single-test, frequentist machinery we've built is more than enough for ML Associate-level work and 80% of practical model-comparison tasks.

---

## 10.12 Summary

1. **A hypothesis test** asks "is the data compatible with the null hypothesis?" The pipeline: state $H_0$ and $H_1$, choose a test statistic, find its distribution under $H_0$, compute the statistic, compute the p-value, compare to $\alpha$.
2. **A p-value** is the probability of observing a test statistic at least as extreme as the one we got, *under the null*. It is *not* the probability the null is true, the probability of replication, or the effect size.
3. **Type I error** = false positive (reject $H_0$ when true), controlled by $\alpha$. **Type II error** = false negative (fail to reject $H_0$ when false), controlled by the power $1 - \beta$ of the test, which depends on sample size and effect size.
4. **The t-test** for the difference of two means is the workhorse for comparing model metrics. The test statistic is the observed difference divided by its standard error; the null distribution is Student's t (or normal for large samples).
5. **Confidence intervals** report the range of plausible parameter values; they encode the same information as a hypothesis test but more informatively. A 95% CI containing zero is equivalent to "fail to reject $H_0$" at $\alpha = 0.05$.
6. **Multiple testing** inflates false-positive rates. Bonferroni correction (divide $\alpha$ by the number of tests) is the simplest fix; FDR control is more nuanced.
7. **Statistical significance is not practical significance.** With large samples, any non-zero effect produces a tiny p-value. Always report effect size and CI alongside p-values.
8. **In ML**, hypothesis testing shows up in model comparison, feature significance, A/B testing, drift detection, and calibration assessment.

---

## 10.13 What this builds on / where this returns

**Builds on:** Chapter 9 — sampling distributions, CLT, standard errors. The entire chapter is an application of CLT to "is this difference real or noise?"

**Returns:**

- **Model comparison** in *Chapter 46* (imbalanced classification, threshold tuning) uses hypothesis tests to decide whether a new threshold or strategy is meaningfully better.
- **Statistical tests for drift detection** appear in *Part L* (Databricks platform).
- **Coefficient significance in regression** appears in *Chapter 31* (OLS) and *Chapter 32* (logistic regression).
- **A/B testing for shipped models** is a discipline we touched on in Part A; the formal machinery is here.
- The **multiple testing** problem returns implicitly in *Chapter 29* (feature selection) and *Chapter 22* (hyperparameter selection, where "trying many configurations" is multiple testing).

---

## 10.14 Exercises

1. **A simple t-test.** Two samples have means 10.2 and 11.5, sample standard deviations 2.0 and 2.5, sizes 30 and 40. Compute the t statistic for the two-sample test of equal means. (Don't compute the exact p-value; just write down the formula and the number.)

2. **From t to p.** Suppose your t statistic from question 1 came out around 2.4. The degrees of freedom are large enough that you can use the standard normal approximation. Estimate the two-sided p-value.

3. **Confidence interval from a sample mean.** A sample of $n = 100$ has mean 50 and standard deviation 8. Compute the standard error of the mean, then the 95% confidence interval.

4. **CI and hypothesis test are dual.** The 95% confidence interval for some parameter is $[-0.02, 0.18]$. Without further computation, what would you predict for the result of a two-sided hypothesis test of $H_0: \text{parameter} = 0$? What about $H_0: \text{parameter} = 0.05$?

5. **What does p = 0.03 mean.** Suppose you read in a paper "the new method outperformed the baseline (mean improvement 1.2%, p = 0.03)." For each of the following interpretations, mark Right or Wrong:
   1. There's a 3% chance the new method is no better than the baseline.
   2. There's a 3% chance of getting an improvement this large (or larger) if the methods were truly equivalent.
   3. There's a 97% chance the same improvement will replicate next time.
   4. The new method is 97% likely to be better than the baseline.
   5. We have moderate evidence against the null hypothesis.

6. **Sample-size and significance.** A true effect of 0.001 standard deviations between two groups is essentially nonexistent for practical purposes. With $n = 10^9$ samples per group, will it likely be statistically significant? Discuss what this means.

7. **Power and Type II error.** You want to detect a true difference of 0.02 percentage points in conversion rate between two arms of an A/B test. Baseline rate is 5%. Using the rough formula in section 10.5.1, estimate how many observations per arm you need for 80% power at $\alpha = 0.05$. (You'll need to compute $\sigma^2 \approx p(1-p) \approx 0.0475$, then $\delta/\sigma$, etc.)

8. **Multiple testing trap.** A researcher tests 50 hypotheses, each at $\alpha = 0.05$, with no real effects in any of them. What's the expected number of false positives? Probability of at least one false positive?

9. **Bonferroni in action.** Your team has 10 candidate features and wants to test whether each one is associated with the target. You'd like a family-wise type-I error of 0.05. What individual $\alpha$ should each test use? If 3 features have p-values 0.001, 0.004, and 0.03, which ones survive Bonferroni?

10. **CI interpretation.** A confidence interval for a model's improvement over a baseline is $[1.5\%, 2.8\%]$ at 95% confidence. Which of the following is the *correct* interpretation?
    1. There's a 95% chance the true improvement is between 1.5% and 2.8%.
    2. If we repeated the experiment many times, 95% of the constructed intervals would contain the true improvement.
    3. The true improvement is definitely between 1.5% and 2.8%.
    4. The probability of observing this much improvement is 95%.

11. **Effect size vs. significance.** Two A/B tests produced these results:
    - Test A: $n = 100$, observed improvement 5pp, $p = 0.06$ (just over threshold).
    - Test B: $n = 1{,}000{,}000$, observed improvement 0.02pp, $p < 0.001$.
    
    Which test would you act on, and why?

12. **Code task.** Run two-sample t-tests on simulated data with sample sizes 30, 100, 1000 and a true effect size of 0.1 standard deviations. For each, run the test 1000 times and record how often you reject at $\alpha = 0.05$. Connect the result to "power."

<details>
<summary>Answers</summary>

1. $t = (11.5 - 10.2) / \sqrt{2.0^2/30 + 2.5^2/40} = 1.3 / \sqrt{4/30 + 6.25/40} = 1.3 / \sqrt{0.1333 + 0.1563} = 1.3 / \sqrt{0.2896} = 1.3 / 0.5381 \approx 2.416$.

2. For $z = 2.4$, $P(Z > 2.4) \approx 0.0082$. Two-sided: $p \approx 0.016$.

3. SE = $8/\sqrt{100} = 0.8$. 95% CI = $50 \pm 1.96 \cdot 0.8 = 50 \pm 1.568 = [48.43, 51.57]$.

4. $H_0: \theta = 0$: zero is inside [-0.02, 0.18], so fail to reject at $\alpha = 0.05$. $H_0: \theta = 0.05$: 0.05 is also inside the interval, so fail to reject. Any null value inside the CI corresponds to "fail to reject."

5. (a) Wrong (confuses $P(\text{data} \mid H_0)$ with $P(H_0 \mid \text{data})$). (b) Right — this is the definition. (c) Wrong (p-value is not replication probability). (d) Wrong (same as a, in different language). (e) Right (this is the legitimate framing of moderate evidence against null).

6. Yes — with $n = 10^9$, the standard error is microscopic, and any non-zero effect will be highly significant. This is a vivid example of statistical significance not implying practical significance. With huge samples, you can statistically "detect" essentially zero effects.

7. $\sigma \approx \sqrt{0.0475} \approx 0.218$ (using p(1-p) as a binomial variance approximation). $\delta/\sigma = 0.0002 / 0.218 \approx 0.000917$. Then $n \approx ((1.96 + 0.84)/0.000917)^2 \approx (3053)^2 \approx 9{,}300{,}000$ per arm. Detecting 2bps lifts requires ~10M users per arm.

8. Expected false positives: $50 \cdot 0.05 = 2.5$. Probability of at least one: $1 - 0.95^{50} \approx 1 - 0.077 = 0.923$, about 92%.

9. Per-test α = 0.05/10 = 0.005. The features with p = 0.001 and p = 0.004 survive; the one with p = 0.03 does not (it's above 0.005).

10. (b) — the formal frequentist interpretation. (a) is the common but technically incorrect "Bayesian-flavored" reading. (c) is wrong (no certainty). (d) is nonsensical.

11. Test A has a larger effect (5pp vs 0.02pp) but borderline significance — promising but inconclusive; recommend running a larger experiment. Test B has high significance but trivial effect — significant noise, not worth shipping. Acting on Test B would optimise the wrong thing. Either way, before deciding, consider business context: even a 5pp lift in conversion might not be worth $X engineering cost.

12. Output will show rejection rates around 4% (effectively the type-I error, when true effect is small relative to noise) for n=30, climbing to maybe 17% for n=100, and 80%+ for n=1000. The connection to "power": power is the probability of rejecting H0 when H0 is false. As n grows, power grows. The plot of "rejection rate vs. n" is the power curve.

</details>
