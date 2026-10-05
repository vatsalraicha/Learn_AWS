# Chapter 17 — Gradient Descent and Its Variants

> **Goal of this chapter:** to take the optimization problem set up in Chapter 16 — "minimize a loss function over a hypothesis class" — and explain, end to end, the algorithm we use to actually solve it. We'll start with plain (batch) gradient descent on a one-parameter toy, build intuition for the learning rate by watching the optimizer succeed and fail, do five iterations of gradient descent on a linear regression *by hand*, then climb up to stochastic gradient descent, mini-batches, and momentum. By the end of the chapter you will understand why gradient descent is the default training procedure for almost everything except a handful of closed-form-friendly problems, and why a careful learning-rate choice is the single most consequential hyperparameter in classical ML.
>
> This chapter does not derive Adam. We sketch what adaptive optimizers do at a qualitative level — for the Databricks ML Associate, that's sufficient. Adam, RMSprop, and friends are valuable to know about, but the *vocabulary* — learning rate, gradient, batch size, momentum — is what carries through the entire rest of the curriculum, so we spend our pages there.

---

## 17.1 The optimization problem, restated

Chapter 16 ended with the ERM template:

$$
\hat{f} = \arg\min_{f \in \mathcal{H}} \frac{1}{n} \sum_{i=1}^n \ell(f(x_i), y_i)
$$

Almost always, $\mathcal{H}$ is parameterized — we don't search over abstract functions, we search over the *parameter vector* $\mathbf{w} \in \mathbb{R}^d$ that defines the function. For linear regression, $f(x) = \mathbf{w} \cdot \mathbf{x} + b$, so the parameters are $(\mathbf{w}, b)$. For logistic regression, same shape. For a neural net, the parameters are the weight matrices and biases of every layer. For a decision tree, the "parameters" are the splits and leaf values, but trees are not gradient-trained, so they get a different chapter (33).

Restated for the gradient case:

$$
\hat{\mathbf{w}} = \arg\min_{\mathbf{w} \in \mathbb{R}^d} L(\mathbf{w})
$$

where $L(\mathbf{w}) = \frac{1}{n}\sum_i \ell(f_\mathbf{w}(x_i), y_i)$ is the training loss as a function of parameters. We want the parameter vector that minimizes the loss.

For some special cases (ordinary least squares, ridge regression), this minimum can be written down in closed form — it's the solution of a linear system. For *almost every other case*, we need an iterative numerical algorithm. The workhorse is **gradient descent**.

---

## 17.2 The picture: walking downhill

Imagine the loss $L(\mathbf{w})$ as a surface in $(d+1)$-dimensional space. The $d$ horizontal directions are the parameters; the vertical direction is the loss. You're a hiker standing on this surface and you want to find the lowest point.

In one dimension ($d = 1$), it looks like:

```
   L(w)
     │
     │       ___
     │      /   \              ___
     │     /     \           __/  \
     │    /       \         /      \
     │   /         \_______/        \____
     │  /                                 \____
     │_/                                       \____
     └────────────────────────────────────────────────► w
                                 ↑
                          global minimum
```

In two dimensions, the surface is a landscape with hills and valleys. In $d$ dimensions you can't visualize it, but the idea generalizes.

Gradient descent says: at your current location, look around, figure out which direction is *steepest downhill*, and take a small step that way. Repeat until you can't go any lower.

The direction of steepest *ascent* is the gradient $\nabla L(\mathbf{w})$ — the vector of partial derivatives, which Chapter 15 introduced. The direction of steepest *descent* is its negative. So one step of gradient descent is:

$$
\boxed{\mathbf{w}_{t+1} = \mathbf{w}_t - \eta \cdot \nabla L(\mathbf{w}_t)}
$$

where $\eta > 0$ is the **learning rate** — how big a step you take. Larger $\eta$ moves you faster; smaller $\eta$ moves you more carefully.

That update rule is *the* equation of modern ML training. Every algorithm we'll train in this curriculum — logistic regression, gradient-boosted trees (with a clever twist), every neural net — uses some version of it.

---

## 17.3 Why subtract the gradient?

This is worth a moment because, said without justification, it's just a rule. Said *with* justification, it becomes obvious.

The gradient $\nabla L(\mathbf{w})$ is, by definition, the vector of partial derivatives:

$$
\nabla L(\mathbf{w}) = \left(\frac{\partial L}{\partial w_1}, \frac{\partial L}{\partial w_2}, \ldots, \frac{\partial L}{\partial w_d}\right)
$$

Geometrically, it points in the direction along which $L$ is *increasing fastest* at the current point. (Chapter 15 derived this: the directional derivative in any unit direction $\mathbf{u}$ is $\nabla L \cdot \mathbf{u}$, which is maximized when $\mathbf{u}$ aligns with $\nabla L$.)

So $+\nabla L$ is uphill. $-\nabla L$ is downhill. We want to go down. So we subtract. End of mystery.

The learning rate $\eta$ controls how far along that downhill direction we step. Small enough $\eta$, you genuinely go downhill — first-order Taylor expansion says $L(\mathbf{w}_t - \eta \nabla L) \approx L(\mathbf{w}_t) - \eta \|\nabla L\|^2 \leq L(\mathbf{w}_t)$, with equality only if $\nabla L = 0$ (a stationary point). For *too* large $\eta$, the linear approximation breaks down — you overshoot and may land at a *higher* loss. The next section gives you that picture.

---

## 17.4 The learning rate — a 1D demonstration

Consider the world's simplest example: minimize

$$
L(w) = w^2
$$

This is a parabola with minimum at $w = 0$ and $L(0) = 0$. The gradient is $\nabla L = 2w$. The update rule is:

$$
w_{t+1} = w_t - \eta \cdot 2w_t = (1 - 2\eta) w_t
$$

Starting at $w_0 = 10$ and varying $\eta$:

**Case 1: $\eta = 0.1$.** Then $1 - 2\eta = 0.8$. Each step multiplies $w$ by $0.8$:

| $t$ | $w_t$ | $L(w_t)$ |
|---:|---:|---:|
| 0 | 10.00 | 100.00 |
| 1 |  8.00 |  64.00 |
| 2 |  6.40 |  40.96 |
| 3 |  5.12 |  26.21 |
| 4 |  4.10 |  16.78 |
| 5 |  3.28 |  10.74 |
| 10 | 1.07 | 1.15 |
| 20 | 0.115 | 0.013 |

Geometric convergence to zero. Good.

**Case 2: $\eta = 0.5$.** Then $1 - 2\eta = 0$. One step:

| $t$ | $w_t$ | $L(w_t)$ |
|---:|---:|---:|
| 0 | 10.00 | 100.00 |
| 1 |  0.00 |   0.00 |

We landed exactly at the minimum. (This works only because $L(w) = w^2$ is special — for a general quadratic with this curvature, you need exactly this learning rate to one-shot it. We'll see this idea again as Newton's method.)

**Case 3: $\eta = 0.9$.** Then $1 - 2\eta = -0.8$. Each step multiplies by $-0.8$ — alternating signs:

| $t$ | $w_t$ | $L(w_t)$ |
|---:|---:|---:|
| 0 | 10.00 | 100.00 |
| 1 | $-8.00$ | 64.00 |
| 2 |  6.40 | 40.96 |
| 3 | $-5.12$ | 26.21 |
| 4 |  4.10 | 16.78 |
| 5 | $-3.28$ | 10.74 |

Still converging — slower in magnitude than Case 1, and oscillating across the minimum — but converging.

**Case 4: $\eta = 1.1$.** Then $1 - 2\eta = -1.2$. Each step multiplies by $-1.2$ — growing in magnitude:

| $t$ | $w_t$ | $L(w_t)$ |
|---:|---:|---:|
| 0 |  10.00 |  100.00 |
| 1 | $-12.00$ |  144.00 |
| 2 |  14.40 |  207.36 |
| 3 | $-17.28$ | 298.60 |
| 4 |  20.74 |  430.18 |
| 5 | $-24.88$ | 619.46 |

This is **divergence**. The learning rate is too large; we overshoot the minimum more than we corrected, the next step overshoots even more, and we spiral off to infinity. The loss explodes. Anyone who has ever trained a neural network has seen this pattern at 2 a.m. and felt the panic.

```
   w_t
     │  η = 1.1 (divergent)
   30│             *
     │
   20│      *
     │   *
   10│●__                                ← w₀
     │   `--*___      η = 0.1 (smooth descent)
     │          \\_*___
   0 ┼------------------●────────────────┼  t
     │        η = 0.9 (oscillating decay)
     │      *
  -10│
     │
  -20│   *
     │
```

The takeaways are critical:

- Learning rate too small → slow convergence; many iterations wasted.
- Learning rate "right" → geometric (or better) convergence.
- Learning rate too large → oscillation or divergence; possibly loss → ∞.

There's a precise theoretical statement: for a strongly convex loss with **Lipschitz-continuous gradient** (smoothness constant $L_{\text{smooth}}$), GD converges iff $\eta < 2/L_{\text{smooth}}$, and the optimal step size is $\eta = 1/L_{\text{smooth}}$. We won't derive this in full; the point is that there *is* a right answer and you have to find it (or use an adaptive optimizer — §17.10 — that finds it for you).

For the simple $L = w^2$ case, $L_{\text{smooth}} = 2$, so $\eta < 1$ is required and $\eta = 0.5$ is optimal. Cases 1-3 satisfy the condition, Case 4 does not, and the table tells the story.

---

## 17.5 Convergence criteria — when to stop

Plain gradient descent doesn't terminate on its own. You either:

- Run a fixed number of iterations (e.g., 1,000).
- Stop when the gradient is small ($\|\nabla L(\mathbf{w}_t)\| < \varepsilon$ — you're near a stationary point).
- Stop when the loss is no longer decreasing meaningfully ($|L(\mathbf{w}_t) - L(\mathbf{w}_{t-1})| < \varepsilon$).
- Stop when *validation* loss starts increasing (**early stopping** — Ch 18, 20).

The last is the most important in practice: training loss can keep decreasing while validation loss has bottomed out and started rising. The model is overfitting from that point on; you should have stopped at the dip.

---

## 17.6 Gradient descent for linear regression — five iterations by hand

Time to do this on a real problem. Linear regression on three data points. The model is $\hat{y} = w x + b$. Loss is MSE. We'll do five iterations of gradient descent by hand and watch the loss come down.

**Data:**

| $i$ | $x_i$ | $y_i$ |
|---:|----:|----:|
| 1 | 1.0 | 2.0 |
| 2 | 2.0 | 3.0 |
| 3 | 3.0 | 5.0 |

(Roughly linear with slope around 1.5; intercept around 0.5.)

**Loss:**

$$
L(w, b) = \frac{1}{n}\sum_{i=1}^n (y_i - wx_i - b)^2 = \frac{1}{3}\sum_{i=1}^3 (y_i - wx_i - b)^2
$$

**Gradients** (using the chain rule):

$$
\frac{\partial L}{\partial w} = -\frac{2}{n}\sum_i x_i (y_i - wx_i - b)
$$
$$
\frac{\partial L}{\partial b} = -\frac{2}{n}\sum_i (y_i - wx_i - b)
$$

Initialize: $w_0 = 0$, $b_0 = 0$. Learning rate $\eta = 0.1$.

### Iteration 0 (compute initial loss + gradients)

Residuals $r_i = y_i - 0 \cdot x_i - 0 = y_i$: $(2, 3, 5)$.

$L = (4 + 9 + 25)/3 = 38/3 \approx 12.667$.

$\partial L / \partial w = -\frac{2}{3}(1 \cdot 2 + 2 \cdot 3 + 3 \cdot 5) = -\frac{2}{3}(2 + 6 + 15) = -\frac{2}{3} \cdot 23 = -15.333$.

$\partial L / \partial b = -\frac{2}{3}(2 + 3 + 5) = -\frac{2}{3} \cdot 10 = -6.667$.

Update:

$w_1 = 0 - 0.1 \cdot (-15.333) = 1.533$
$b_1 = 0 - 0.1 \cdot (-6.667) = 0.667$

### Iteration 1

Predictions: $\hat{y}_i = 1.533 x_i + 0.667$:

| $i$ | $\hat{y}_i$ | $r_i$ |
|---:|---:|---:|
| 1 | 2.200 | $-0.200$ |
| 2 | 3.733 | $-0.733$ |
| 3 | 5.267 | $-0.267$ |

$L = (0.04 + 0.537 + 0.071)/3 = 0.648 / 3 = 0.216$.

Loss dropped from 12.667 to 0.216 in one step. Good.

$\partial L / \partial w = -\frac{2}{3}(1 \cdot (-0.2) + 2 \cdot (-0.733) + 3 \cdot (-0.267)) = -\frac{2}{3}(-0.2 - 1.467 - 0.800) = -\frac{2}{3}(-2.467) = 1.644$

$\partial L / \partial b = -\frac{2}{3}(-0.2 - 0.733 - 0.267) = -\frac{2}{3}(-1.2) = 0.800$

Update:

$w_2 = 1.533 - 0.1 \cdot 1.644 = 1.369$
$b_2 = 0.667 - 0.1 \cdot 0.800 = 0.587$

### Iteration 2

Predictions: $\hat{y}_i = 1.369 x_i + 0.587$:

| $i$ | $\hat{y}_i$ | $r_i$ |
|---:|---:|---:|
| 1 | 1.956 | $+0.044$ |
| 2 | 3.325 | $-0.325$ |
| 3 | 4.694 | $+0.306$ |

$L = (0.002 + 0.106 + 0.094) / 3 = 0.202 / 3 = 0.067$.

$\partial L/\partial w = -\frac{2}{3}(1 \cdot 0.044 + 2 \cdot (-0.325) + 3 \cdot 0.306) = -\frac{2}{3}(0.044 - 0.650 + 0.918) = -\frac{2}{3}(0.312) = -0.208$

$\partial L/\partial b = -\frac{2}{3}(0.044 - 0.325 + 0.306) = -\frac{2}{3}(0.025) = -0.017$

Update:

$w_3 = 1.369 - 0.1 \cdot (-0.208) = 1.390$
$b_3 = 0.587 - 0.1 \cdot (-0.017) = 0.589$

### Iteration 3

Predictions: $\hat{y}_i = 1.390 \cdot x_i + 0.589$:

| $i$ | $\hat{y}_i$ | $r_i$ |
|---:|---:|---:|
| 1 | 1.979 | $+0.021$ |
| 2 | 3.369 | $-0.369$ |
| 3 | 4.759 | $+0.241$ |

$L = (0.0004 + 0.136 + 0.058) / 3 = 0.194 / 3 = 0.065$.

(Small *increase* — we may be slightly oscillating around the optimum. Continue.)

$\partial L/\partial w = -\frac{2}{3}(0.021 - 0.738 + 0.723) = -\frac{2}{3}(0.006) \approx -0.004$

$\partial L/\partial b = -\frac{2}{3}(0.021 - 0.369 + 0.241) = -\frac{2}{3}(-0.107) \approx 0.071$

Update:

$w_4 = 1.390 - 0.1 \cdot (-0.004) = 1.390$
$b_4 = 0.589 - 0.1 \cdot 0.071 = 0.582$

### Iteration 4

Predictions $\hat{y}_i = 1.390 x_i + 0.582$:

| $i$ | $\hat{y}_i$ | $r_i$ |
|---:|---:|---:|
| 1 | 1.972 | $+0.028$ |
| 2 | 3.362 | $-0.362$ |
| 3 | 4.752 | $+0.248$ |

$L = (0.0008 + 0.131 + 0.062) / 3 = 0.194 / 3 = 0.065$.

We're hovering around 0.065. The closed-form OLS solution (Ch 31) for this dataset is approximately $w = 1.5, b = 1/3 \approx 0.333$, with minimum MSE $= 1/6 \approx 0.167$ — wait, let me recompute the OLS solution because my hand-rolled GD has converged to a lower loss than that, which would be a contradiction.

Recompute OLS by the normal equations. $\bar{x} = 2$, $\bar{y} = 10/3 \approx 3.333$. $\sum (x_i - \bar{x})(y_i - \bar{y}) = (-1)(-4/3) + 0 \cdot (-1/3) + 1 \cdot (5/3) = 4/3 + 5/3 = 9/3 = 3$. $\sum (x_i - \bar{x})^2 = 1 + 0 + 1 = 2$. So $w^* = 3/2 = 1.5$. $b^* = \bar{y} - w^* \bar{x} = 10/3 - 3 = 1/3$.

Residuals at OLS: $(2 - 1.5 - 0.333, 3 - 3 - 0.333, 5 - 4.5 - 0.333) = (0.167, -0.333, 0.167)$. MSE $= (0.028 + 0.111 + 0.028)/3 = 0.167/3 = 0.056$. So the true OLS minimum is $\approx 0.056$.

Our GD converged to $\approx 0.065$, close but not quite. With more iterations and possibly a slightly smaller learning rate we'd reach $0.056$.

**Summary of five iterations:**

| Iter | $w$ | $b$ | $L$ |
|---:|---:|---:|---:|
| 0 | 0.000 | 0.000 | 12.667 |
| 1 | 1.533 | 0.667 | 0.216 |
| 2 | 1.369 | 0.587 | 0.067 |
| 3 | 1.390 | 0.589 | 0.065 |
| 4 | 1.390 | 0.582 | 0.065 |
| OLS | 1.500 | 0.333 | 0.056 |

The model is essentially converged after a handful of iterations on this trivial problem. For real problems with thousands of parameters and millions of examples, the same picture holds — the first few iterations drop the loss dramatically; later iterations refine slowly.

---

## 17.7 The cost of "batch" — and the stochastic alternative

Notice something about the gradient computation in §17.6: every iteration required us to sweep through *all three* data points. For a dataset of size $n$, each step costs $O(n)$ work. We did 5 iterations; total cost $5n$.

For $n = 3$, no problem. For $n = 10^7$, computing $\partial L / \partial w$ requires summing 10 million terms *per step* — and you might want 1,000 steps. That's $10^{10}$ inner-loop operations. Plain GD ("batch GD") becomes impractical fast.

There's a clever observation: when our data is i.i.d., the *true* gradient of the population loss is an expectation:

$$
\nabla L^*(\mathbf{w}) = \mathbb{E}_{(x,y) \sim P}[\nabla \ell(f_\mathbf{w}(x), y)]
$$

The empirical gradient $\frac{1}{n}\sum_i \nabla \ell_i$ is the sample-average estimator of this expectation. But there's no reason we need the *full*-sample estimate every step. A *single* example $\nabla \ell_i$ is, in expectation, equal to the true gradient — it's just a noisier estimate of it.

**Stochastic gradient descent (SGD)** uses this fact. Each iteration:

1. Pick one training example $i$ at random.
2. Compute $\nabla \ell_i(\mathbf{w}_t)$ — the gradient using only that example.
3. Update: $\mathbf{w}_{t+1} = \mathbf{w}_t - \eta \cdot \nabla \ell_i(\mathbf{w}_t)$.

Cost per iteration: $O(1)$ instead of $O(n)$. But the step is *noisy* — each individual gradient is correct *on average* but can point in nearly any direction for any single example.

The trade is:

| Algorithm | Steps to converge | Cost per step | Total cost |
|---|---|---|---|
| Batch GD | few (e.g., 100) | $O(n)$ | $O(100n)$ |
| SGD | many (e.g., $10n$) | $O(1)$ | $O(10n)$ |

Despite needing more steps, SGD wins on total cost for large $n$. And — counterintuitively — for non-convex problems (neural nets), the *noise* in SGD's gradient is sometimes a *feature*, not a bug: it helps the optimizer escape shallow local minima and saddle points that batch GD would get trapped in.

### 17.7.1 Mini-batch SGD — the practical default

Pure SGD is too noisy in practice. The standard compromise is **mini-batch SGD**: at each step, pick a small random batch $B$ of examples (typical size 32, 64, 128, 256, 512, 1024), compute the gradient on that batch:

$$
\nabla_B L = \frac{1}{|B|}\sum_{i \in B} \nabla \ell_i(\mathbf{w}_t)
$$

and update. This is a less-noisy estimate of the true gradient than a single example, but vastly cheaper than the full batch. Mini-batches also map naturally onto GPU/SIMD hardware — a batch of 64 examples can be processed in parallel.

In modern usage, "SGD" almost always means mini-batch SGD. Pure single-example SGD is rare outside textbooks.

A typical training run on a dataset of $n = 10^6$ examples with batch size $128$:

- One **epoch** = one pass through the entire training set = $10^6 / 128 \approx 7,800$ mini-batch updates.
- A full training run might be 10-100 epochs.
- So $\sim 10^5$ updates total. Each update is $O(\text{batch size})$.

For comparison, batch GD on this setup would do, say, 1,000 updates at cost $O(10^6)$ each = $10^9$ work total. Mini-batch is several times cheaper in wall clock and gives better final solutions on non-convex problems.

---

## 17.8 Momentum — the ball rolling downhill

SGD with a fixed learning rate has two practical problems:

1. In *ravines* — long, narrow valleys in the loss surface where the gradient is steep in one direction and shallow in another — plain SGD zigzags. Each step is mostly in the steep direction and barely makes progress in the shallow direction.

2. In *plateaus* — regions where the gradient is very small — SGD takes tiny steps and progress crawls.

**Momentum** fixes both. The idea: keep a running average of recent gradients, and use *that* as the direction to step in, rather than just the current gradient.

Formally, with momentum parameter $\beta \in [0, 1)$:

$$
\mathbf{v}_{t+1} = \beta \mathbf{v}_t + \nabla L(\mathbf{w}_t)
$$
$$
\mathbf{w}_{t+1} = \mathbf{w}_t - \eta \mathbf{v}_{t+1}
$$

The "velocity" $\mathbf{v}_t$ is the running average — at time $t$ it's a weighted sum of all past gradients, with the most recent weighted most heavily. Typical $\beta = 0.9$, meaning each step's velocity has a "decay half-life" of about $\log(2)/\log(1/\beta) \approx 7$ steps.

The physical analogy: a ball rolling down the loss landscape. Plain GD takes the direction of the current slope; momentum-GD takes the direction the ball would *roll*, integrating slope information from many previous steps. In a ravine, the gradient component along the steep wall averages out to roughly zero (it points opposite ways from the two walls); the component along the floor accumulates. Net effect: the ball accelerates down the floor and doesn't oscillate.

```
                            Without momentum
                            ▲ ▼ ▲ ▼ ▲ ▼ ▲ ▼ ▲ ▼
   ravine ───────────────► ──────────────────────►
                              tiny progress along floor
   
                            With momentum
                            
   ravine ───────────────► ━━━━━━━━━━━━━━━━━━━━━━►
                              accelerates along floor
```

Momentum is the workhorse modification to SGD. Adding it costs essentially nothing (one extra vector to store, one extra add per update) and improves convergence substantially on real problems. Spark ML's logistic regression uses L-BFGS by default, which is a *second-order* method that does even better than momentum on convex problems — we mention it for completeness; the math is out of scope for this curriculum.

---

## 17.9 RMSprop and Adam — adaptive learning rates (qualitative)

Different parameters often benefit from *different* learning rates. If one feature has values around 1 and another has values around 1000, the gradient with respect to the second weight is roughly 1000× larger, and a learning rate that's right for one is wrong for the other. The standard fix (feature scaling — Ch 26) eliminates a lot of this, but in deep learning it's pervasive.

**RMSprop** and **Adam** are *adaptive learning rate* methods. They maintain, *per parameter*, a running estimate of the magnitude of past gradients, and they divide each parameter's step size by that magnitude. The effect: parameters that have seen large gradients get smaller effective steps; parameters that have seen small gradients get larger ones.

In symbols (Adam, simplified):

- Maintain $\mathbf{m}_t$ = momentum-style average of gradients.
- Maintain $\mathbf{v}_t$ = momentum-style average of *squared* gradients.
- Update: $\mathbf{w}_{t+1} = \mathbf{w}_t - \eta \cdot \mathbf{m}_t / (\sqrt{\mathbf{v}_t} + \epsilon)$.

We won't unpack this further. The qualitative picture is enough for this course: Adam is "SGD with momentum plus per-parameter learning rate adaptation, plus a bias correction." It's the default optimizer for neural networks and is sometimes better than plain SGD even on classical problems. For the Databricks ML Associate exam — where the optimizer is usually hidden inside `LogisticRegression.fit()` and chosen by the library — the relevant fact is just that *something* iterative is happening underneath, and it's some descendent of the gradient-descent family.

---

## 17.10 Convex vs. non-convex losses

Here's a critical distinction that explains why classical ML often "just works" while neural network training is famously fiddly.

A loss function $L(\mathbf{w})$ is **convex** if its graph is bowl-shaped: any line segment between two points on the graph lies *above* the graph between them. Formally: for any $\mathbf{w}_1, \mathbf{w}_2$ and any $\alpha \in [0, 1]$,

$$
L(\alpha \mathbf{w}_1 + (1-\alpha) \mathbf{w}_2) \leq \alpha L(\mathbf{w}_1) + (1-\alpha) L(\mathbf{w}_2)
$$

Convex losses have a single global minimum (or possibly a connected set of minima at the same loss value), and gradient descent with appropriate $\eta$ provably converges to it.

**Classical ML's blessing:** most of the algorithms we'll meet in Part F have convex losses.

- Linear regression with MSE — convex (quadratic in $\mathbf{w}$).
- Ridge regression — convex (quadratic + convex regularizer).
- Lasso — convex (quadratic + convex regularizer).
- Logistic regression with cross-entropy — convex (you should verify this in Ch 32).
- SVM with hinge loss — convex.

If your loss is convex, GD finds the global optimum from any starting point. No local minima to get stuck in. The optimization just *works*.

**Non-convex problems:**

- Neural networks — non-convex (the composition of linear and non-linear layers).
- Clustering (k-means) — non-convex (and we'll see in Ch 38 that the algorithm only finds local minima).
- Gaussian mixture models trained by EM — non-convex.

For non-convex problems, GD can converge to a local minimum that's much worse than the global minimum. In neural networks this turns out to be less of a problem than feared — for large enough networks, most local minima have similar loss values — but it's still why the same model trained twice from different random initializations gives different final weights and slightly different predictions.

For the Databricks ML Associate, the algorithms in scope are almost all convex (linear regression, logistic regression). You can trust the optimizer. For the broader picture: classical ML's convex-friendly losses are why those algorithms are *trustworthy* and *reproducible* in a way neural networks aren't.

---

## 17.11 Implementing plain GD for linear regression in NumPy

Concrete code. We'll do what we did by hand in §17.6, but for an arbitrary dataset.

```python
import numpy as np

def linear_regression_gd(X, y, eta=0.01, n_iters=1000, tol=1e-8):
    """Train linear regression by plain gradient descent.
    
    X: (n, d) feature matrix (without intercept column).
    y: (n,) target vector.
    eta: learning rate.
    n_iters: max iterations.
    tol: stop if gradient norm < tol.
    
    Returns: (w, b, loss_history).
    """
    n, d = X.shape
    w = np.zeros(d)
    b = 0.0
    loss_history = []
    
    for t in range(n_iters):
        # Forward pass: predictions and residuals
        y_pred = X @ w + b
        residuals = y - y_pred             # shape (n,)
        loss = np.mean(residuals ** 2)
        loss_history.append(loss)
        
        # Gradients of MSE w.r.t. (w, b)
        grad_w = -(2.0 / n) * (X.T @ residuals)    # shape (d,)
        grad_b = -(2.0 / n) * residuals.sum()       # scalar
        
        # Step
        w = w - eta * grad_w
        b = b - eta * grad_b
        
        # Convergence check
        grad_norm = np.sqrt((grad_w ** 2).sum() + grad_b ** 2)
        if grad_norm < tol:
            break
    
    return w, b, loss_history


# Demonstrate on synthetic data: y = 1.5 x_1 - 2.0 x_2 + 3 + noise
rng = np.random.default_rng(0)
n, d = 200, 2
X = rng.normal(size=(n, d))
y_true_w = np.array([1.5, -2.0])
y_true_b = 3.0
y = X @ y_true_w + y_true_b + rng.normal(scale=0.1, size=n)

w, b, history = linear_regression_gd(X, y, eta=0.05, n_iters=500)

print(f"Learned w: {w}")           # should be ~ [1.5, -2.0]
print(f"Learned b: {b:.4f}")        # should be ~ 3.0
print(f"Initial loss: {history[0]:.4f}")
print(f"Final loss: {history[-1]:.4f}")
print(f"Iterations: {len(history)}")
```

Run that and you'll see the learned $\mathbf{w}$ approach $(1.5, -2.0)$ and $b$ approach $3.0$ within a few hundred iterations. The loss history will start large, drop fast, and asymptote.

Three good experiments to run after this:

1. Set $\eta = 1.0$ (way too large). Watch the loss explode.
2. Set $\eta = 0.0001$ (way too small). Watch convergence crawl.
3. Set $\eta = 0.1$ vs. $\eta = 0.05$. Compare convergence speed.

These exercises build the *feel* for the learning rate that no amount of reading replaces.

### 17.11.1 The same in mini-batch SGD

```python
def linear_regression_minibatch_sgd(X, y, eta=0.01, batch_size=32,
                                     n_epochs=50, seed=0):
    n, d = X.shape
    rng = np.random.default_rng(seed)
    w = np.zeros(d)
    b = 0.0
    loss_history = []
    
    for epoch in range(n_epochs):
        # Shuffle indices once per epoch
        perm = rng.permutation(n)
        
        for start in range(0, n, batch_size):
            idx = perm[start:start + batch_size]
            Xb, yb = X[idx], y[idx]
            
            yb_pred = Xb @ w + b
            res = yb - yb_pred
            
            grad_w = -(2.0 / len(idx)) * (Xb.T @ res)
            grad_b = -(2.0 / len(idx)) * res.sum()
            
            w = w - eta * grad_w
            b = b - eta * grad_b
        
        # Record epoch-end full-batch loss
        loss_history.append(np.mean((y - X @ w - b) ** 2))
    
    return w, b, loss_history
```

The structure is the same; we just iterate batch-by-batch within each epoch.

---

## 17.12 What can go wrong — a debugging checklist

Gradient descent failure modes you'll see in practice:

1. **Loss explodes (NaN, Inf).** Learning rate too large. Shrink it by 10×, try again. Also check for un-scaled features (Ch 26).

2. **Loss decreases then plateaus way above zero.** Either you've hit a local minimum (non-convex problem) or the model class is just incapable of fitting the data better (underfitting — Ch 18).

3. **Loss decreases very slowly.** Learning rate too small, or features are on wildly different scales. Scale features; try a larger learning rate.

4. **Loss oscillates without converging.** Learning rate marginally too large. Halve it.

5. **Training loss drops but validation loss rises.** Overfitting (Ch 18). Stop training (early stopping), add regularization, or reduce model capacity.

6. **Loss is `nan` from step 1.** You probably have NaN's in your data, or you're taking $\log(0)$ somewhere in the loss. Check the inputs and the loss implementation.

Most of "training is hard" boils down to one of these six. The instinct to develop: when training goes wrong, *look at the loss trajectory*. It tells you which failure mode you're in.

---

## 17.13 Summary

The takeaway picture:

1. Training a model is, almost always, **solving an optimization problem**: $\min_\mathbf{w} L(\mathbf{w})$.
2. **Plain gradient descent** is the workhorse algorithm: $\mathbf{w} \leftarrow \mathbf{w} - \eta \nabla L$. Cost per step is $O(n)$ — sweep the whole dataset.
3. The **learning rate** $\eta$ is the most consequential hyperparameter: too small wastes iterations, too large diverges. There's a "right zone" for any given loss surface.
4. **SGD** uses one example at a time. **Mini-batch SGD** uses small batches. Both are cheap-per-step but noisy. They're the default for large datasets.
5. **Momentum** accumulates a running average of gradients, helping in ravines and on plateaus. Standard add-on to SGD.
6. **Adam / RMSprop** are adaptive — per-parameter learning rate scaling. Dominant in neural networks; less critical in classical convex ML.
7. **Convex losses** (linear/logistic/ridge/lasso) → GD finds the global optimum. **Non-convex** (neural nets, clustering) → GD finds *a* local optimum.
8. Failure modes are diagnosable from the loss trajectory.

Internalize the update rule $\mathbf{w} \leftarrow \mathbf{w} - \eta \nabla L$. Internalize the picture of the loss surface as a landscape you're walking downhill on. The rest is mechanics.

---

## 17.14 What this builds on / where this returns

**Builds on:**
- Chapter 15 (gradients, the chain rule).
- Chapter 16 (loss functions — the things we minimize).

**Returns:**
- *Chapter 31* (linear regression): we'll also derive the closed-form via the normal equations, but GD is the alternative.
- *Chapter 32* (logistic regression): GD on cross-entropy is the training algorithm; we'll derive the gradient.
- *Chapter 36* (gradient boosting): "functional" gradient descent — descend in *function space*, fitting a new weak learner per step.
- *Chapter 50* (random search vs. grid search for HPO): we'll discuss why gradient-based HPO is unusual; the relevant fact is that hyperparameters don't have computable gradients in the way model parameters do.
- *Part L* (MLflow): tracking the loss trajectory per run is a built-in capability.

---

## 17.15 Exercises

1. **The update rule.** Write down plain gradient descent's update in three forms: for one scalar parameter $w$, for a vector $\mathbf{w} \in \mathbb{R}^d$, and for a batch loss $L_{\text{batch}}$ on $|B|$ examples.

2. **Why the negative gradient?** In one sentence, explain why we subtract the gradient rather than add it.

3. **Divergence by hand.** Repeat the $L(w) = w^2$ example from §17.4 with $\eta = 1.5$ and $w_0 = 2$, computing $w_1, w_2, w_3$. What happens?

4. **Step-size sweet spot.** For $L(w) = aw^2$ with $a > 0$, what learning rate exactly one-shots the minimum from any starting point? Show the algebra.

5. **GD on a small problem.** Data: $(1, 1), (2, 2), (3, 4)$. Model: $\hat{y} = wx$ (no intercept). Loss: MSE. Compute $\partial L / \partial w$ symbolically, then do 3 iterations of GD starting from $w_0 = 0$ with $\eta = 0.05$.

6. **Batch vs SGD cost.** Dataset has $n = 10^6$ examples and $d = 100$ features. Compute the per-step work for batch GD vs. SGD vs. mini-batch SGD (batch size 128). Assuming both run for 1 epoch, total work compared.

7. **Why mini-batch?** Give two reasons mini-batch SGD is preferred over pure single-example SGD in practice.

8. **Momentum intuition.** In your own words: how does momentum help in a "ravine" loss surface where one direction is much steeper than another?

9. **Convex vs non-convex.** Which of the following losses are convex in the model parameters? (a) Linear regression with MSE. (b) Logistic regression with cross-entropy. (c) A two-layer ReLU neural network with cross-entropy. (d) K-means.

10. **Diagnosing a failure.** Your training loss starts at 5, drops to 2 after the first batch, and then jumps to $10^{12}$ on the second batch. What's the most likely cause? What's the first thing to try?

11. **The closed form for OLS.** We'll derive in Ch 31 that $\mathbf{w}^* = (X^TX)^{-1}X^Ty$ minimizes MSE. Given that the closed form exists, why do many implementations *still* use gradient descent?

12. **Diminishing learning rate.** Some real training schedules decay $\eta$ over time — start with $\eta = 0.1$, drop to $\eta = 0.01$ after 50 epochs, $\eta = 0.001$ after 100 epochs. Why is this useful? Sketch a one-paragraph rationale.

<details>
<summary>Answers</summary>

1. Scalar: $w \leftarrow w - \eta \frac{dL}{dw}$. Vector: $\mathbf{w} \leftarrow \mathbf{w} - \eta \nabla L(\mathbf{w})$. Mini-batch: $\mathbf{w} \leftarrow \mathbf{w} - \eta \cdot \frac{1}{|B|}\sum_{i \in B} \nabla \ell_i(\mathbf{w})$.

2. The gradient $\nabla L$ points in the direction of steepest *ascent*. We want to go down. Subtracting moves us in the steepest-descent direction.

3. $w_1 = 2 - 1.5 \cdot 4 = -4$. $w_2 = -4 - 1.5 \cdot (-8) = 8$. $w_3 = 8 - 1.5 \cdot 16 = -16$. Magnitudes growing by factor 2 each step — divergence.

4. $L = aw^2 \Rightarrow L'(w) = 2aw$. Update: $w_1 = w_0 - \eta \cdot 2aw_0 = (1 - 2a\eta)w_0$. One-shot to zero iff $1 - 2a\eta = 0 \Rightarrow \eta = 1/(2a)$.

5. $L = \frac{1}{3}\sum (y_i - wx_i)^2$. $\partial L/\partial w = -\frac{2}{3}\sum x_i(y_i - wx_i)$. 
   - At $w_0 = 0$: gradient $= -\frac{2}{3}(1 \cdot 1 + 2 \cdot 2 + 3 \cdot 4) = -\frac{2}{3} \cdot 17 = -11.333$. $w_1 = 0 - 0.05(-11.333) = 0.567$.
   - At $w_1 = 0.567$: residuals $(1 - 0.567, 2 - 1.133, 4 - 1.7) = (0.433, 0.867, 2.300)$. Gradient $= -\frac{2}{3}(1 \cdot 0.433 + 2 \cdot 0.867 + 3 \cdot 2.300) = -\frac{2}{3}(0.433 + 1.733 + 6.900) = -\frac{2}{3}(9.067) = -6.044$. $w_2 = 0.567 - 0.05(-6.044) = 0.869$.
   - At $w_2 = 0.869$: residuals $(0.131, 0.262, 1.393)$. Gradient $= -\frac{2}{3}(0.131 + 0.524 + 4.179) = -\frac{2}{3}(4.834) = -3.223$. $w_3 = 0.869 - 0.05(-3.223) = 1.030$. (True optimum $w^* = \sum x_i y_i / \sum x_i^2 = 17/14 \approx 1.214$. We're approaching it.)

6. Each example involves $O(d)$ work to compute gradient. Batch GD per step: $O(nd) = 10^8$. SGD per step: $O(d) = 100$. Mini-batch (128): $O(128 d) = 12{,}800$. One epoch (whole dataset processed): batch GD does 1 step ($10^8$); SGD does $10^6$ steps ($10^6 \cdot 100 = 10^8$); mini-batch does $\approx 7{,}812$ steps ($7812 \cdot 12{,}800 = 10^8$). Same total work per epoch — but mini-batch makes far more parameter updates per epoch.

7. (a) Less noisy than single-example SGD — better gradient estimates → smoother convergence. (b) Maps onto SIMD/GPU hardware that processes batches in parallel, so wall-clock cost of a batch of 64 is far less than 64× the cost of one example.

8. In a ravine, the gradient at each step has a large component perpendicular to the floor (pointing uphill) and a small component along the floor (the direction toward the minimum). Without momentum, the optimizer oscillates back and forth across the ravine — the perpendicular component dominates each step. With momentum, those perpendicular components average to nearly zero across consecutive steps (they point opposite ways), while the small along-floor component accumulates. Net result: the optimizer "rolls" down the floor instead of bouncing off the walls.

9. (a) Convex (quadratic). (b) Convex (Ch 32 will show — composition of convex-ish pieces). (c) Non-convex (the ReLU + composition makes it non-convex). (d) Non-convex (the objective is the sum of squared distances to nearest cluster center, and the assignment step is combinatorial).

10. Learning rate too large; the loss exploded after one big step. First fix: divide $\eta$ by 10 and retry. (Other likely cause: a NaN in the data corrupted a gradient. Inspect.)

11. The closed form requires inverting $X^TX$, a $d \times d$ matrix. For $d = 10^4$, that's $10^{12}$ multiplications — slow. For $d = 10^5$, it doesn't fit in RAM. Also: when $X^TX$ is singular (collinear features), the inverse doesn't exist and a small ridge term is needed. Gradient descent sidesteps both — it scales linearly in $d$ per step and handles singular settings gracefully.

12. Early in training, large steps make rapid progress when far from the optimum. Late in training, large steps cause oscillation around the optimum; small steps refine the solution precisely. Decay schedules combine the speed of large $\eta$ early with the precision of small $\eta$ late.

</details>
