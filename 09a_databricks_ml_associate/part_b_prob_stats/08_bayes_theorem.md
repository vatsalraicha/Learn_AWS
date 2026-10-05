# Chapter 8 — Bayes' Theorem

> **Goal of this chapter:** to derive Bayes' theorem from the chain rule, name each of its four components, and work through the canonical examples where naive intuition fails badly and Bayes saves us. By the end of the chapter you should be able to take any "test for a rare condition" scenario and produce the right posterior probability without confusion. You should also be able to identify, when you read ML papers and tutorials, where Bayes' theorem is hiding — because it is hiding in many places.

---

## 8.1 A puzzle that fools nearly everyone

Let me start with the puzzle, before the math.

A test for a particular disease has been developed. The disease is rare — only 1 in 1000 people have it. The test is described as **99% accurate**, meaning:

- If you have the disease, the test comes back positive 99% of the time. (99% sensitivity.)
- If you don't have the disease, the test comes back negative 99% of the time. (99% specificity, equivalently 1% false-positive rate.)

You take the test. It comes back **positive**.

What is the probability that you actually have the disease?

Take a moment before reading on. Write down your answer.

Most people answer somewhere in the range 90-99%. "The test is 99% accurate, so if it says I'm positive, there's a 99% chance I have the disease." This is wrong. The actual answer is about **9%**, an order of magnitude below the intuitive answer.

Where did the intuition go wrong? It missed the *prior* — the base rate at which the disease occurs. The test is good, but the disease is rare, and "rare disease + good but imperfect test" produces a counterintuitive arithmetic that Bayes' theorem makes visible. We will compute the 9% from scratch in section 8.4.

The puzzle is famous not because it's a curiosity but because it captures a *systematic* error in everyday probabilistic reasoning. Doctors get it wrong. Lawyers get it wrong. Statistics students get it wrong on the first try. It's an error worth understanding, because once you internalise it you'll see it everywhere — in medical testing, in fraud detection, in spam filtering, in security alerting, anywhere we use evidence to update beliefs.

Bayes' theorem is the cure.

---

## 8.2 Deriving Bayes' theorem

Bayes' theorem is one of those results whose proof is almost embarrassingly short — three lines of algebra applied to definitions you already know. Let's see it.

Start with the chain rule from Chapter 7, expressed two ways. For any two events $A$ and $B$ with $P(A) > 0$ and $P(B) > 0$:

$$
P(A \cap B) = P(A \mid B) \cdot P(B)
$$

and

$$
P(A \cap B) = P(B \mid A) \cdot P(A).
$$

These are the same quantity ($P(A \cap B)$) expressed two ways. Set them equal:

$$
P(A \mid B) \cdot P(B) = P(B \mid A) \cdot P(A).
$$

Solve for $P(A \mid B)$ by dividing both sides by $P(B)$:

$$
\boxed{P(A \mid B) = \frac{P(B \mid A) \cdot P(A)}{P(B)}.}
$$

That's it. Bayes' theorem.

Re-read it. Take a moment to convince yourself that all we did was rearrange the chain rule. There is no new content here; Bayes' theorem is the chain rule, factored to put $P(A \mid B)$ on the left-hand side.

But this rearrangement is enormously useful in practice. Here's why.

You often have $P(B \mid A)$ and want $P(A \mid B)$. In the disease example, you have $P(\text{positive test} \mid \text{disease})$ — that's the test's sensitivity, a property of the test. You want $P(\text{disease} \mid \text{positive test})$ — what the patient cares about, which depends on the population. Bayes' theorem is the bridge.

---

## 8.3 The four named pieces

Bayes' theorem has four parts. Each has a name. The names are not just labels — they tell you how to interpret each piece in an evidence-updating workflow.

Let $H$ denote a *hypothesis* (e.g., "patient has the disease") and $E$ denote the *evidence* (e.g., "test came back positive"). Bayes' theorem in this notation:

$$
P(H \mid E) = \frac{P(E \mid H) \cdot P(H)}{P(E)}.
$$

The four pieces:

- $P(H)$ is the **prior**. What you believed about $H$ *before* you saw the evidence. The base rate.
- $P(E \mid H)$ is the **likelihood**. How probable the evidence is *if the hypothesis were true*. (Note: the likelihood is the conditional probability of evidence given hypothesis, not the other way around — this conflation is the heart of the puzzle in 8.1.)
- $P(E)$ is the **evidence** (or "marginal likelihood"). The overall probability of seeing this evidence at all, integrating over all hypotheses. It serves as a normalising constant.
- $P(H \mid E)$ is the **posterior**. What you believe about $H$ *after* observing $E$. The updated probability.

The framing is: *prior + likelihood ⇒ posterior, with the evidence as normaliser*. You start with a belief; the data arrives; you update.

### 8.3.1 Computing the evidence

The denominator $P(E)$ is often the trickiest piece. By the law of total probability — which is just marginalisation in Chapter 7's sense:

$$
P(E) = P(E \mid H) \cdot P(H) + P(E \mid \neg H) \cdot P(\neg H).
$$

In words: the evidence can happen in two ways — either the hypothesis is true and the evidence happens, or the hypothesis is false and the evidence happens anyway. Sum over both. The expression generalises if there are more than two competing hypotheses:

$$
P(E) = \sum_i P(E \mid H_i) \cdot P(H_i).
$$

This sum is over a partition of the hypothesis space — every possible truth, with their priors, with the likelihood of $E$ under each.

---

## 8.4 The rare disease, computed

Let's apply Bayes' theorem to the puzzle from section 8.1.

**Setup:**
- $H$ = "patient has the disease."
- $\neg H$ = "patient does not have the disease."
- $E$ = "test comes back positive."

**Given:**
- Prior: $P(H) = 0.001$ (1 in 1,000). Therefore $P(\neg H) = 0.999$.
- Sensitivity: $P(E \mid H) = 0.99$ (test catches 99% of positives).
- Specificity: $P(\neg E \mid \neg H) = 0.99$, which means the false-positive rate $P(E \mid \neg H) = 0.01$.

**Bayes' theorem:**

$$
P(H \mid E) = \frac{P(E \mid H) \cdot P(H)}{P(E)} = \frac{P(E \mid H) \cdot P(H)}{P(E \mid H) \cdot P(H) + P(E \mid \neg H) \cdot P(\neg H)}.
$$

Plug in:

$$
P(H \mid E) = \frac{0.99 \cdot 0.001}{0.99 \cdot 0.001 + 0.01 \cdot 0.999}.
$$

Numerator: $0.99 \cdot 0.001 = 0.00099$.

Denominator: $0.99 \cdot 0.001 + 0.01 \cdot 0.999 = 0.00099 + 0.00999 = 0.01098$.

$$
P(H \mid E) = \frac{0.00099}{0.01098} \approx 0.0902.
$$

About **9%**. The right answer to the puzzle.

### 8.4.1 Why so low? Frequencies make it tangible

The arithmetic is correct but unintuitive. Let's reframe it in terms of frequencies — a way of presenting Bayesian problems that consistently helps people get them right.

Imagine 1 million people. Apply the prior:

- 1,000 actually have the disease (the 0.1%).
- 999,000 are healthy.

Now apply the test to all of them. Sensitivity 99% on the disease group:

- Of the 1,000 with disease, 990 test positive. 10 test negative (the misses).

Specificity 99% on the healthy group:

- Of the 999,000 healthy, 989,010 test negative. **9,990 test positive** (false positives).

The total positives: 990 (true positives) + 9,990 (false positives) = 10,980.

If you are among the positives, your probability of being a true positive:

$$
\frac{990}{10{,}980} \approx 0.0902.
$$

About 9%. Same answer.

The reframing makes the intuition vivid: the **true positives** (990) are *outnumbered* by the **false positives** (9,990). Even though the test correctly catches almost everyone who is sick, the disease is so rare that the small false-positive rate, applied to a huge healthy population, generates more false positives than there are sick people in the world.

This is the key insight. When the disease is rare, the prior wins. The test has to be *much* more specific than 99% before the positive predictive value catches up.

### 8.4.2 The role of the prior

Notice that we never used the test result alone to compute $P(H \mid E)$. The prior $P(H) = 0.001$ is half of the calculation. If the prior were different, the answer would be different.

Suppose we test the same person, with the same test, but in a clinical context where the prior is higher — say the patient came in with symptoms that suggest the disease, raising the pre-test probability to $P(H) = 0.1$ (10%, not 0.1%). Redo Bayes:

$$
P(H \mid E) = \frac{0.99 \cdot 0.1}{0.99 \cdot 0.1 + 0.01 \cdot 0.9} = \frac{0.099}{0.099 + 0.009} = \frac{0.099}{0.108} \approx 0.917.
$$

About **92%**. The same test, on the same person, gives a posterior of 9% or 92% depending entirely on whether you're screening the general population or testing a symptomatic patient. The test result is the same; the *context* — encoded in the prior — changes everything.

This is the right and ethically important reading of medical testing. A positive test in a screening context is not equivalent to a positive test in a diagnostic context. Mass screening for rare conditions can produce huge numbers of false alarms even with very good tests. We will return to this in Chapter 46 when we discuss imbalanced classification, which is the ML version of the same phenomenon.

---

## 8.5 Sequential evidence: chaining Bayes

What if we have *two* tests, both positive? Or three? Bayes handles this naturally, by chaining.

Start with the posterior from the first test as the *prior* for the second test:

$$
P(H \mid E_1, E_2) = \frac{P(E_2 \mid H, E_1) \cdot P(H \mid E_1)}{P(E_2 \mid E_1)}.
$$

If the two tests are **conditionally independent given $H$** — that is, given the patient's true disease status, the two test results don't influence each other — then $P(E_2 \mid H, E_1) = P(E_2 \mid H)$, and the second update uses just the test's sensitivity again. (Conditional independence is the same idea we touched on in Chapter 7 — joint factorisation, but conditional on $H$.)

Let's compute. After the first positive test, the posterior was 0.0902. Take this as the new prior. Run a second test (with the same sensitivity 0.99 and false-positive rate 0.01):

$$
P(H \mid E_1, E_2) = \frac{0.99 \cdot 0.0902}{0.99 \cdot 0.0902 + 0.01 \cdot (1 - 0.0902)} = \frac{0.0893}{0.0893 + 0.0091} \approx 0.908.
$$

After *two* positive tests, the posterior is now about **91%**. Two independent positives, each from a 99%-accurate test, were enough to flip from "9%, probably not" to "91%, probably." This is why follow-up testing matters so much in real medical practice — a positive screening test followed by a confirmatory test produces very different posterior odds than the screening test alone.

A nicer way to chain Bayes is in **log-odds** form, but we will save that until you've spent more time with the linear case. The intuition: each piece of evidence shifts the log-posterior-odds by a fixed amount called the "log Bayes factor," and chained evidence corresponds to summing log Bayes factors. The arithmetic of belief updating is additive in log-odds.

---

## 8.6 A second worked example: an A/B test, Bayesianly

Bayes isn't only for diagnostic tests. Here is the same machinery applied to a routine ML engineering question — an A/B test.

You're running an A/B test comparing two versions of a model. Version A has been live for a while; version B is the new candidate. You ship B to 5% of traffic for a week and observe the click-through rate.

Suppose:
- Version A's click-through rate is well-established at 5.0%.
- Version B's click-through rate, in the 5% holdout, is observed to be 6.0% over 10,000 impressions (so 600 clicks).

**Question:** Is B genuinely better, or could this be noise?

A frequentist hypothesis test (which we'll meet in Chapter 10) computes a p-value: the probability of seeing this much improvement *if B were actually no different from A*. If the p-value is small, reject the null.

A Bayesian re-framing: we have a *prior* over how different B's true rate might be from A's, and we *update* with the observed data. The posterior tells us how confident we are that B is better.

**Setup:**
- Let $\theta_B$ be B's true (unknown) click-through rate.
- Prior: based on past launches, we believe new model variants are usually within ±10% of the incumbent, so we might model $\theta_B \sim \text{Beta}(50, 950)$ — a distribution centered around 0.05 with modest spread. (The Beta distribution is the natural prior for a Bernoulli parameter; we'll meet it formally in Bayesian-ML chapters in your future studies, but the key feature is that it's a flexible distribution on $[0, 1]$ and "conjugate" with the Bernoulli likelihood — meaning the posterior is also a Beta.)
- Likelihood: each impression is a Bernoulli($\theta_B$) trial. The 600 successes in 10,000 trials give a likelihood proportional to $\theta_B^{600} (1 - \theta_B)^{9400}$.

**Posterior** (after Bayes-rule update with conjugate Beta-Bernoulli, which we'll spare the derivation of):

$$
\theta_B \mid \text{data} \sim \text{Beta}(50 + 600, 950 + 9400) = \text{Beta}(650, 10350).
$$

The posterior mean is $650 / (650 + 10350) = 0.0591$. The posterior is much tighter than the prior because we have a lot of data; the prior with 1000 "pseudo-counts" is dwarfed by the 10,000 actual observations.

What we want is $P(\theta_B > 0.05 \mid \text{data})$ — the probability that B's true rate exceeds A's. From the Beta posterior, this comes out to be very close to 1: with this much data, we're highly confident B is genuinely better than A, not just noisily lucky.

The Bayesian framing has advantages: it expresses uncertainty as a posterior distribution we can compute over, not as a binary "reject / don't reject," and the prior lets us encode reasonable beliefs about expected effect sizes (large jumps from a/b tests are *suspicious*; small jumps are par for the course). For ML engineers running many A/B tests, this is the natural workflow.

We will not get deeper into Bayesian inference in this book — it's a substantial subfield — but you should know it exists, that it's a clean alternative to frequentist hypothesis testing, and that the engine under the hood is Bayes' theorem applied iteratively to incoming data.

---

## 8.7 Frequentist and Bayesian — the philosophical contrast, briefly

A small detour into the philosophy of statistics. You can skip this section without losing the thread of the book, but it pays back the time spent on it.

The **frequentist** stance: probabilities describe the long-run frequencies of events under repeated random trials. A parameter (like $\theta_B$, the true click-through rate of model B) is a fixed unknown number. The data is random; the parameter is not. Confidence intervals, p-values, and hypothesis tests are statements about the procedure's long-run behaviour — "this procedure produces intervals that contain the truth 95% of the time" — not about the specific dataset in front of you.

The **Bayesian** stance: probabilities describe degrees of belief, including beliefs about parameters. The parameter $\theta_B$ has a probability distribution — the prior, updated by evidence to the posterior. We can talk about $P(\theta_B > 0.05 \mid \text{data}) = 0.997$, a statement about the parameter itself.

Both formalisms are internally consistent. Both can answer practical questions. They disagree about *what kind of object a probability is*.

Most of classical ML — including everything on the Databricks ML Associate exam — is implicitly frequentist. We minimise empirical risk; we construct confidence intervals around metrics; we run hypothesis tests to compare models. Bayes appears explicitly in Naive Bayes (Chapter 37) and in Bayesian hyperparameter optimisation (Chapter 51), and implicitly in the use of regularisation as a "MAP estimate under a prior" — but the dominant flavor of the course is frequentist.

Practical advice: don't get religious. Use whichever framework makes the problem cleaner. Use frequentist machinery for routine reporting and hypothesis testing because that's what colleagues expect. Use Bayesian framing when you have a strong prior, want to chain updates, or need to talk about parameter distributions directly. The two perspectives are complementary, not adversarial.

---

## 8.8 Where Bayes appears in ML

A short tour, so you know where to look for Bayes in the rest of this book.

### 8.8.1 Naive Bayes classifier

The most direct application. Given features $x = (x_1, x_2, \ldots, x_d)$ and a class $y$, Bayes tells us

$$
P(y \mid x) = \frac{P(x \mid y) \cdot P(y)}{P(x)} \propto P(x \mid y) \cdot P(y).
$$

(The $\propto$ symbol means "proportional to" — we drop the $P(x)$ since it's the same for all classes; to classify, we just compare the numerators.)

Naive Bayes makes the strong assumption that the features are *conditionally independent given the class*: $P(x \mid y) = \prod_j P(x_j \mid y)$. With this assumption, the algorithm is trivial to train (just count). The "naive" in the name is the conditional-independence assumption, which is rarely literally true but often good enough. We derive the full algorithm in Chapter 37.

### 8.8.2 MAP estimation and regularisation

Many ML training objectives can be reinterpreted as "find the parameters $\theta$ that maximise $P(\theta \mid \text{data})$" — the **maximum a posteriori** (MAP) estimate. By Bayes:

$$
P(\theta \mid \text{data}) \propto P(\text{data} \mid \theta) \cdot P(\theta).
$$

Maximising this is equivalent to maximising

$$
\log P(\text{data} \mid \theta) + \log P(\theta).
$$

The first term is the log-likelihood (which we maximise during ordinary training). The second term — the log of the prior — appears as a *regularisation term*. L2 regularisation corresponds to a Gaussian prior on the weights; L1 regularisation corresponds to a Laplace prior. We'll see this connection explicitly in Chapter 20.

### 8.8.3 Bayesian hyperparameter optimisation

In Chapter 51 we'll meet Bayesian optimisation as a sophisticated hyperparameter search method. The "Bayesian" in the name is real: we maintain a *posterior* over the unknown hyperparameter-to-validation-loss function, update it as we evaluate new configurations, and use the posterior to choose the next configuration. Bayes' theorem is the update mechanism inside the algorithm.

### 8.8.4 Calibration of classifiers

When we say a probabilistic classifier is *well-calibrated*, we mean its output probabilities match observed frequencies — emails the classifier scores at 0.7 actually turn out to be spam 70% of the time. This is, implicitly, a statement about the classifier's outputs being the correct Bayesian posterior. Logistic regression's nice calibration properties are not a coincidence; they fall out of the maximum-likelihood derivation under a Bernoulli model, which is itself Bayesian-flavored. Chapter 42 returns to this.

---

## 8.9 Common pitfalls

A short list of where people go wrong with Bayes.

**Confusing $P(A \mid B)$ with $P(B \mid A)$.** The puzzle in section 8.1 is exactly this conflation. The test's accuracy is $P(\text{positive} \mid \text{disease}) = 0.99$, but what the patient wants is $P(\text{disease} \mid \text{positive})$. These are different conditional probabilities, related by Bayes' theorem and the prior.

This conflation is so common it has a name: the "prosecutor's fallacy" — confusing $P(\text{innocent} \mid \text{evidence})$ with $P(\text{evidence} \mid \text{innocent})$ in courtroom arguments. Has led to wrongful convictions.

**Ignoring the prior.** Easy to do when the prior is fuzzy ("I have no idea what the base rate is"). The cure is to make the prior explicit and reason about how sensitive the posterior is to it.

**Confusing "likelihood" and "probability."** $P(E \mid H)$ is a likelihood of the hypothesis given the data, but for continuous data this is a density, not a probability. The "likelihood is high" and "data is probable" are not the same statement when probabilities of single observations are zero.

**Assuming independent evidence when it isn't.** Two test results from the same lab are not independent — they share calibration biases. Chaining Bayes with conditionally-correlated evidence underestimates uncertainty.

**Overconfident priors.** A prior of "I'm sure $\theta = 0.5$ to four decimal places" (a delta-function prior) will not move regardless of the data, because Bayes' rule multiplies by it. Sensible priors leave room for data to dominate.

---

## 8.10 Code: Bayes' theorem in numbers

A short script to make the calculations concrete.

```python
def bayes_simple(prior, likelihood_pos_given_H, likelihood_pos_given_notH):
    """
    Compute posterior P(H | positive test).
    
    Parameters
    ----------
    prior : float
        P(H) — base rate of the hypothesis being true.
    likelihood_pos_given_H : float
        P(positive | H) — sensitivity of the test.
    likelihood_pos_given_notH : float
        P(positive | not H) — false-positive rate.
    """
    p_H = prior
    p_notH = 1 - prior
    
    # Numerator: P(positive | H) * P(H)
    numerator = likelihood_pos_given_H * p_H
    
    # Denominator (total probability of positive):
    # = P(positive | H) * P(H) + P(positive | not H) * P(not H)
    denominator = numerator + likelihood_pos_given_notH * p_notH
    
    return numerator / denominator


# The rare-disease puzzle
posterior = bayes_simple(
    prior=0.001,
    likelihood_pos_given_H=0.99,
    likelihood_pos_given_notH=0.01,
)
print(f"P(disease | one positive test) = {posterior:.4f}")  # ~0.0902

# Two positive tests, in sequence:
# the posterior of the first becomes the prior of the second
posterior_2 = bayes_simple(
    prior=posterior,
    likelihood_pos_given_H=0.99,
    likelihood_pos_given_notH=0.01,
)
print(f"P(disease | two positive tests) = {posterior_2:.4f}")  # ~0.908

# Now: what if the patient was symptomatic (prior 10%)?
posterior_symptomatic = bayes_simple(
    prior=0.10,
    likelihood_pos_given_H=0.99,
    likelihood_pos_given_notH=0.01,
)
print(f"P(disease | positive, prior 10%) = {posterior_symptomatic:.4f}")  # ~0.917
```

You can experiment with this — vary the prior, vary the sensitivity, vary the specificity — and watch how the posterior moves. A few things you should notice as you play:

- The posterior is extremely sensitive to the prior when the prior is small.
- For a given prior, increasing the specificity (decreasing false positives) makes the posterior climb dramatically. If the false-positive rate were 0.1% instead of 1%, the posterior on the original puzzle would be about 50% instead of 9%.
- Chaining positive tests is a fast path to a high posterior — but only if the tests are *conditionally independent*. In practice they often aren't, and the gains from chaining are slower than the math implies.

---

## 8.11 Bayesian model averaging — a quick mention

One last application worth naming, even briefly. When you have *multiple candidate models* for a problem and you're not sure which is right, the Bayesian framework lets you weight predictions from each model by their posterior probabilities, producing an ensemble:

$$
P(y \mid x, \text{data}) = \sum_i P(y \mid x, M_i) \cdot P(M_i \mid \text{data}).
$$

You don't pick one model; you blend them, weighted by how well each fits the data. This is called **Bayesian model averaging** (BMA).

In practice, BMA is rarely used in classical ML — the priors over model space are hard to specify, and the integrals are intractable. But the *spirit* of BMA — that you should hedge across multiple models rather than commit to one — is the conceptual root of ensemble methods (bagging, random forests, gradient boosting), which we'll meet in Chapters 34-36. Those algorithms use heuristic averaging rather than principled Bayesian averaging, but the intuition is the same: "I don't trust any one model, so I'll let many vote."

---

## 8.12 Summary

1. **Bayes' theorem**: $P(H \mid E) = \frac{P(E \mid H) \cdot P(H)}{P(E)}$, derived in three lines from the chain rule.
2. The four pieces have names: **prior** $P(H)$, **likelihood** $P(E \mid H)$, **evidence** $P(E)$, **posterior** $P(H \mid E)$. The evidence is computed by marginalising over all hypotheses.
3. The classic mistake — confusing "test is 99% accurate" with "if I tested positive, I'm 99% likely to have the disease" — comes from ignoring the prior. For rare conditions, the prior dominates, and a positive test from a screening can leave you at single-digit posterior probability.
4. **Sequential evidence** chains naturally — the posterior from one observation becomes the prior for the next, assuming conditional independence given $H$.
5. **Frequentist and Bayesian** are two consistent ways to talk about probability. Frequentist dominates classical ML; Bayesian appears in Naive Bayes, regularisation (MAP estimates), Bayesian hyperparameter optimisation, and ensemble averaging.
6. **Naive Bayes**, MAP estimation, and Bayesian optimisation are three ways Bayes lurks inside ML algorithms you'll meet later.
7. Pitfalls: confusing $P(A \mid B)$ with $P(B \mid A)$; ignoring the prior; treating likelihoods as probabilities; assuming independence that isn't there.

---

## 8.13 What this builds on / where this returns

**Builds on:** Chapter 7 — joint, marginal, conditional probability, the chain rule. Bayes is the chain rule rearranged; everything in this chapter is downstream of the conditional probability machinery in Chapter 7.

**Returns:**

- **Naive Bayes** in *Chapter 37* uses Bayes' theorem directly to classify, plus a conditional-independence assumption to make the likelihood tractable.
- **MAP estimation and regularisation** in *Chapter 20* — L1 and L2 regularisation are reinterpreted as Bayesian priors on the weights.
- **Bayesian hyperparameter optimisation** in *Chapter 51* uses Bayes' rule inside its acquisition-function machinery.
- **Calibration of classifiers** in *Chapters 42-44* — the question "are the model's output probabilities actual probabilities?" is implicitly Bayesian.
- The **prior-dominates-when-the-event-is-rare** phenomenon is the conceptual ancestor of the imbalanced-classification difficulties in *Chapter 46*.
- The contrast between **likelihood and probability** for continuous variables matters in *Chapter 32* (logistic regression's MLE derivation).

---

## 8.14 Exercises

1. **Recite Bayes.** Without referring to the chapter, write down Bayes' theorem with each piece named (prior, likelihood, evidence, posterior).

2. **Derivation from the chain rule.** Starting from $P(A \cap B) = P(A \mid B) P(B) = P(B \mid A) P(A)$, derive Bayes' theorem. Show each step.

3. **A medium-rare disease.** A disease has prevalence 5%. A test has sensitivity 95% and specificity 90%. Compute the posterior $P(\text{disease} \mid \text{positive test})$. Does this surprise you, given the test's numbers?

4. **A very accurate test on a rare disease.** Same prevalence as section 8.4 (0.1%), but now the test has sensitivity 99.9% and specificity 99.9%. Recompute the posterior. By how much did increasing specificity from 99% to 99.9% move the posterior?

5. **Confirmatory testing.** From the result in section 8.4, you get a positive on a single test (posterior 9%). You then take a *different* independent test with sensitivity 90% and specificity 99%, which also comes back positive. What's your posterior now?

6. **The prior matters.** A patient tests positive for a disease (sensitivity 0.95, specificity 0.95) in two contexts: (a) random screening, prior $P(\text{disease}) = 0.001$; (b) the patient came in with classic symptoms, prior $P(\text{disease}) = 0.5$. Compute both posteriors and explain in plain English why they differ.

7. **The prosecutor's fallacy.** A blood-type match in a criminal case has a 1-in-1000 random-match probability. The prosecutor says "the probability of innocence is 1 in 1000." Identify the conditional-probability error. With a prior probability of guilt of, say, 1 in 100,000 (you're a randomly selected suspect from a city of 100,000), what's the actual posterior probability of guilt given the blood-type match?

8. **Bayes with continuous likelihood.** A continuous observation $X \sim N(\mu, 1)$ has unknown mean $\mu$. Your prior is $\mu \sim N(0, 1)$. After one observation $X = 2$, the posterior over $\mu$ is also normal. Without deriving it formally, argue qualitatively whether the posterior mean should be (a) exactly 2, (b) exactly 0, (c) somewhere between 0 and 2. Justify.

9. **Why $P(E)$ is just a normalising constant.** If you're comparing posteriors for two competing hypotheses ($H$ and $\neg H$, or $H_1$ and $H_2$), why is $P(E)$ often not needed? In what setting *is* it needed?

10. **Connection to Naive Bayes.** Suppose features $x_1$ and $x_2$ are conditionally independent given the class. Write $P(y \mid x_1, x_2)$ using Bayes' theorem and the conditional independence assumption. What price has the assumption paid for tractability?

11. **Calibrated classifier.** A classifier outputs $\hat{p}(y = 1 \mid x) = 0.3$ on a particular example. If the classifier is well-calibrated and you've seen 10,000 examples scoring exactly 0.3, how many would you expect to actually have $y = 1$? Relate this to the Bayesian "posterior over the label" framing.

12. **Code experimentation.** Modify the `bayes_simple` function in section 8.10. For a fixed prior of 0.001 and sensitivity of 0.99, what specificity would you need to make the posterior on a positive test exceed 0.5? Solve algebraically *and* verify numerically.

<details>
<summary>Answers</summary>

1. $P(H \mid E) = P(E \mid H) P(H) / P(E)$. Prior $P(H)$, likelihood $P(E \mid H)$, evidence $P(E)$, posterior $P(H \mid E)$.

2. Set $P(A \mid B) P(B) = P(B \mid A) P(A)$, both equal to $P(A \cap B)$. Divide both sides by $P(B)$: $P(A \mid B) = P(B \mid A) P(A) / P(B)$. Done.

3. $P(\text{pos} \mid \text{dis}) P(\text{dis}) = 0.95 \cdot 0.05 = 0.0475$. $P(\text{pos} \mid \text{no dis}) P(\text{no dis}) = 0.10 \cdot 0.95 = 0.095$. Posterior: $0.0475 / (0.0475 + 0.095) = 0.0475 / 0.1425 \approx 0.333$. About 33%. Better than the 9% in the rarer case, but still surprisingly low for a "95-90" test.

4. Numerator: $0.999 \cdot 0.001 = 0.000999$. Denominator: $0.000999 + 0.001 \cdot 0.999 = 0.000999 + 0.000999 = 0.001998$. Posterior $\approx 0.5$. Going from 99% to 99.9% specificity moved the posterior from ~9% to ~50%. Specificity is the dominant lever when the disease is rare.

5. Take posterior 0.0902 as new prior. Apply Bayes with sensitivity 0.90 and false-positive rate 0.01: $0.90 \cdot 0.0902 / (0.90 \cdot 0.0902 + 0.01 \cdot 0.9098) = 0.0812 / (0.0812 + 0.0091) = 0.0812 / 0.0903 \approx 0.899$. Nearly 90%.

6. (a) Posterior = $0.95 \cdot 0.001 / (0.95 \cdot 0.001 + 0.05 \cdot 0.999) = 0.00095 / 0.05090 \approx 0.0187$, about 1.9%. (b) Posterior = $0.95 \cdot 0.5 / (0.95 \cdot 0.5 + 0.05 \cdot 0.5) = 0.475 / 0.500 = 0.95$, 95%. The same test means very different things in different contexts because the prior is different.

7. Confusing $P(\text{match} \mid \text{innocent}) = 1/1000$ with $P(\text{innocent} \mid \text{match})$. Apply Bayes with prior $P(\text{guilty}) = 10^{-5}$, sensitivity (P(match | guilty)) = 1, and false-positive rate $1/1000$. Posterior = $1 \cdot 10^{-5} / (1 \cdot 10^{-5} + 10^{-3} \cdot (1 - 10^{-5}))$ ≈ $10^{-5} / 10^{-3} = 0.01$. Only 1% probability of guilt, not 99.9%.

8. The posterior mean is between 0 and 2. Both the prior (centered at 0 with finite variance) and the data ($X = 2$, with variance 1) contribute to the estimate. The posterior weights them inversely by their precisions. For this symmetric setup it turns out the posterior is $N(1, 0.5)$ — mean exactly 1. The intuition: equal-strength prior and data each pull half the way.

9. When you compare $P(H_1 \mid E)$ to $P(H_2 \mid E)$, the denominator $P(E)$ is the same in both, so it cancels in the comparison. Useful when you're classifying (pick the hypothesis with the larger numerator) but not when you need the actual posterior probability — e.g., for cost-sensitive decisions, calibration, or thresholding.

10. $P(y \mid x_1, x_2) = P(x_1, x_2 \mid y) P(y) / P(x_1, x_2) = P(x_1 \mid y) P(x_2 \mid y) P(y) / P(x_1, x_2)$. The conditional-independence assumption let us factor the joint likelihood into products of single-feature likelihoods, which is enormously cheaper to estimate from data. The price: the assumption is rarely literally true, so the model can misjudge dependent features.

11. About 3,000 would have $y = 1$. The output 0.3 is the model's posterior probability of $y = 1$ given $x$ — by Bayes' framing, the model is computing $P(y = 1 \mid x)$ from some implicit prior and likelihood. A well-calibrated classifier's output frequency matches its asserted probability.

12. Setting posterior = 0.5: $0.99 \cdot 0.001 = 0.5 \cdot (0.99 \cdot 0.001 + (1 - \text{spec}) \cdot 0.999)$. Solving: $0.00099 = 0.000495 + 0.4995 \cdot (1 - \text{spec})$. $0.000495 = 0.4995 \cdot (1 - \text{spec})$. $1 - \text{spec} = 0.000991$. $\text{spec} = 0.999$. So you need specificity 99.9% to get the posterior to 50% under a 0.1% prior. The "99% accurate" test is two orders of magnitude away from useful for population screening on a 1-in-1000 condition.

</details>
