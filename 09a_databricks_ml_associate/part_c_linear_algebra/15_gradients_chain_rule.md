# Chapter 15 — Gradients and the Chain Rule

> **Goal of this chapter:** to give you a working, geometric understanding of the gradient — what it is, where it points, why it matters — and the chain rule that makes it computable on real ML models. "Training a model" is, at its core, "minimising a loss function," and the only way we minimise functions of millions of parameters is by following the gradient downhill. Until you know what a gradient *is*, the sentence "the model trains" is a black box, and the difference between SGD, momentum, Adam, and L-BFGS is unintelligible. This is the last preparatory chapter before Part D, where we'll write loss functions and actually run gradient descent. Everything Part D does rests on what this chapter builds.

---

## 15.1 The motivating picture — finding the bottom of a valley

Imagine you're standing on a hillside in fog, and you want to walk to the lowest point in the valley. You can't see far, but you can feel the slope under your feet. The strategy is obvious: feel which way is downhill, take a small step in that direction, feel again, step again. Repeat until you can't go down any more.

That algorithm — "take a step in the steepest-descent direction" — is **gradient descent**. The "feel which way is downhill" part is computing the **gradient**. Everything in the training of every linear model, every neural network, every modern deep learning system at any scale is some variation on this loop.

The intuition is solid. The math is what makes it rigorous and what tells us how big a step to take and when to stop. We're going to build it up, from one variable to many, then layer the chain rule on top so we can compute gradients through arbitrarily complicated function compositions.

---

## 15.2 The derivative in one variable — a quick refresher

For a function $f : \mathbb{R} \to \mathbb{R}$, the **derivative** at the point $x_0$ is

$$
f'(x_0) \;=\; \lim_{h \to 0} \frac{f(x_0 + h) - f(x_0)}{h}.
$$

Geometrically: $f'(x_0)$ is the *slope* of the tangent line to the graph of $f$ at $x = x_0$. If $f'(x_0) > 0$, the function is locally increasing — go right and $f$ goes up. If $f'(x_0) < 0$, locally decreasing — go right and $f$ goes down. If $f'(x_0) = 0$, the tangent is flat — possibly a minimum, possibly a maximum, possibly a saddle.

```
        f(x)
         │     ___
         │    /
         │   /  slope = f'(x_0)
         │  /
         │ /●  ← (x_0, f(x_0))
         │/
         │
         └─────────── x
            x_0
```

The connection to "downhill": $-f'(x_0)$ tells you which direction makes $f$ smaller. If $f'(x_0) > 0$ (uphill to the right), you want to move *left* to decrease $f$. If $f'(x_0) < 0$ (downhill to the right), you want to move right. Either way, the direction of decrease is $-\text{sign}(f'(x_0))$, and the *size* of $f'(x_0)$ tells you how steep the slope is.

This is going to generalise to many variables. The gradient is the multi-dimensional sibling of the derivative; gradient descent is the multi-dimensional sibling of "move opposite to the derivative."

### 15.2.1 Worked example

$f(x) = x^2$ has $f'(x) = 2x$. At $x = 3$: $f'(3) = 6 > 0$, so the function is locally increasing — moving right makes $f$ bigger. To decrease $f$, move left. At $x = 0$: $f'(0) = 0$, flat. This is the minimum of $f$ — and indeed $f(0) = 0$ is the smallest value of $x^2$.

A gradient descent iteration would look like: start somewhere, say $x = 3$. Step in the direction of $-f'(x)$ with some small step size $\eta$ (the **learning rate**): $x_{\text{new}} = x - \eta f'(x) = 3 - \eta \cdot 6$. With $\eta = 0.1$, $x_{\text{new}} = 2.4$. Next iteration: $f'(2.4) = 4.8$, $x_{\text{new}} = 2.4 - 0.48 = 1.92$. Then $1.536$. Then $1.229$. Then $0.983$. Convergent — heading to zero.

If the step size is too large ($\eta = 1$, say): $x_{\text{new}} = 3 - 1 \cdot 6 = -3$. We overshot the minimum entirely and bounced to the other side. Next step: $f'(-3) = -6$, so $x_{\text{new}} = -3 - 1 \cdot (-6) = 3$. We're back where we started, bouncing forever. The learning rate matters enormously, and this is precisely the kind of thing we will dissect in Chapter 17.

---

## 15.3 Partial derivatives — derivatives in many variables

What happens when $f$ depends on more than one variable? Suppose $f : \mathbb{R}^n \to \mathbb{R}$, so $f(x_1, x_2, \ldots, x_n)$ is a scalar function of $n$ scalar inputs. Examples:

- $f(x, y) = x^2 + y^2$ — a paraboloid bowl in 3D.
- $f(\mathbf{w}) = \frac{1}{n} \sum_i (\mathbf{w} \cdot \mathbf{x}_i - y_i)^2$ — the linear regression loss as a function of weights.

There is no single "derivative" of a multi-variable function. There's a derivative *with respect to each input variable*, holding the others fixed. That's a **partial derivative**:

$$
\frac{\partial f}{\partial x_i}(x_1, \ldots, x_n) \;=\; \lim_{h \to 0} \frac{f(x_1, \ldots, x_i + h, \ldots, x_n) - f(x_1, \ldots, x_n)}{h}.
$$

The notation $\partial f / \partial x_i$ — "partial $f$ partial $x_i$" — emphasises that we're varying only one input. The rule for computing partial derivatives in practice: pretend all the other variables are constants, then take the ordinary one-variable derivative.

### 15.3.1 Worked example

$f(x, y) = x^2 + 3 y^2$.

$\frac{\partial f}{\partial x}$: treat $y$ as constant. The derivative of $x^2$ is $2x$; the derivative of $3y^2$ (constant w.r.t. $x$) is $0$. So $\frac{\partial f}{\partial x} = 2x$.

$\frac{\partial f}{\partial y}$: treat $x$ as constant. Derivative of $x^2$ (constant w.r.t. $y$) is $0$; derivative of $3y^2$ is $6y$. So $\frac{\partial f}{\partial y} = 6y$.

At the point $(1, 2)$: $\partial f / \partial x = 2$, $\partial f / \partial y = 12$. The function is "more sensitive" to changes in $y$ than to $x$ at that point — wiggling $y$ by a small amount changes $f$ six times more than wiggling $x$ by the same amount.

---

## 15.4 The gradient — partial derivatives, assembled

The **gradient** of $f$, written $\nabla f$ (read "nabla $f$" or "grad $f$"), is the vector of all partial derivatives:

$$
\nabla f(\mathbf{x}) \;=\; \left( \frac{\partial f}{\partial x_1},\; \frac{\partial f}{\partial x_2},\; \ldots,\; \frac{\partial f}{\partial x_n} \right).
$$

It is a function from $\mathbb{R}^n$ to $\mathbb{R}^n$ — at each point in the input space, it returns an $n$-dimensional vector.

For our example $f(x, y) = x^2 + 3y^2$:

$$
\nabla f(x, y) = (2x, 6y).
$$

At $(1, 2)$: $\nabla f = (2, 12)$. At the origin: $\nabla f(0, 0) = (0, 0)$. The gradient vanishes at the origin, suggesting (correctly) that this is the minimum.

### 15.4.1 The geometric meaning — direction of steepest ascent

Here is the geometric fact that makes the gradient useful, and you should write this on the inside of your skull:

> The gradient $\nabla f(\mathbf{x}_0)$ points in the direction of *steepest ascent* of $f$ at $\mathbf{x}_0$. Its magnitude $\|\nabla f(\mathbf{x}_0)\|$ is the rate of increase per unit distance in that direction.

The proof: at $\mathbf{x}_0$, for a small displacement $\mathbf{u}$ (unit vector), the change in $f$ is approximately

$$
f(\mathbf{x}_0 + h \mathbf{u}) - f(\mathbf{x}_0) \;\approx\; h \, \nabla f(\mathbf{x}_0) \cdot \mathbf{u}.
$$

(This is the multivariate Taylor expansion to first order.) The rate of change in direction $\mathbf{u}$ is the dot product $\nabla f \cdot \mathbf{u}$, which by Chapter 12's geometric formula is $\|\nabla f\| \|\mathbf{u}\| \cos \theta = \|\nabla f\| \cos \theta$. This is maximised when $\cos \theta = 1$, i.e., when $\mathbf{u}$ points in the *same direction* as $\nabla f$.

So $\nabla f$ tells you the direction that makes $f$ increase the fastest. And $-\nabla f$ is the direction that makes $f$ *decrease* the fastest — the **steepest descent direction**. That is the direction gradient descent moves in.

### 15.4.2 Visualising the gradient on a contour plot

Picture the function $f(x, y) = x^2 + 3y^2$ as a surface — a bowl. Draw its **contour lines** in the $(x, y)$ plane: curves where $f$ is constant. For $f = c$, the contour is the ellipse $x^2 + 3 y^2 = c$.

At any point on a contour line, the gradient $\nabla f$ is *perpendicular* to the contour. The gradient points away from the centre of the ellipse, outward — in the direction of *increase* (going to a contour with a higher $f$ value). The opposite direction, $-\nabla f$, points inward, toward the centre — the minimum.

```
            y
              \         /
               \       /
                \  ↑  /        ← contours of f, ellipses
                 \ │ /
                  \│/
       ────────────●────────── x
                  /│\
                 / │ \
                /  ↓  \
               /       \
              /         \

The gradient (vector at the centre, pointing up here) is
perpendicular to the contour through that point; -grad
points toward the minimum at the origin.
```

This perpendicular relationship between gradient and contour is a key visual. It's what makes gradient descent look like "rolling down a bowl": at each point, you move perpendicular to the local contour, in the direction of decreasing $f$, until you reach the bottom.

### 15.4.3 Worked numerical example with the gradient

Take $f(x, y) = x^2 + 3 y^2$, starting at $(2, 1)$.

$f(2, 1) = 4 + 3 = 7$. $\nabla f(2, 1) = (4, 6)$. The steepest-descent direction is $-(4, 6) = (-4, -6)$. Normalising: length is $\sqrt{16 + 36} = \sqrt{52} \approx 7.21$. Unit steepest-descent: $(-4/\sqrt{52}, -6/\sqrt{52}) \approx (-0.555, -0.832)$.

If we take a step of size $\eta = 0.1$ in the direction $-\nabla f$ (not normalised — just $-\nabla f$ itself), the new point is $(2, 1) - 0.1(4, 6) = (1.6, 0.4)$. $f(1.6, 0.4) = 2.56 + 0.48 = 3.04$ — substantially lower than $7$. Good.

Step again: $\nabla f(1.6, 0.4) = (3.2, 2.4)$. $(1.6, 0.4) - 0.1(3.2, 2.4) = (1.28, 0.16)$. $f = 1.638 + 0.0768 = 1.715$. Lower again.

Each step shrinks $f$. With enough steps, we'll converge to $(0, 0)$ where $f = 0$. The trajectory zig-zags somewhat because the bowl is elongated (a 3x stretch on the $y$-axis), and gradient descent doesn't take perfectly direct paths in such cases — a topic we'll revisit in Chapter 17 when we discuss the role of preconditioning, momentum, and Adam.

---

## 15.5 The chain rule — single variable

Now to the most consequential idea in all of optimisation: the **chain rule**. It is the engine of backpropagation, of every gradient computation in PyTorch and JAX, of training every neural network ever built. Without it, ML at any non-trivial scale is impossible.

The chain rule answers: if $f$ depends on $u$, and $u$ depends on $x$, how does $f$ depend on $x$?

In one variable: suppose $y = f(u(x))$ — that is, $u$ is a function of $x$, and $f$ is a function of $u$. Then

$$
\frac{dy}{dx} = \frac{dy}{du} \cdot \frac{du}{dx}.
$$

The derivative of the composition is the product of the derivatives. The notation $dy/du$ here means "differentiate $f$ as a function of $u$"; $du/dx$ means "differentiate $u$ as a function of $x$." Both evaluated at the right point.

### 15.5.1 Worked example

$y = (3x + 1)^2$. Let $u = 3x + 1$, so $y = u^2$.

$dy/du = 2u$. $du/dx = 3$. Chain rule: $dy/dx = 2u \cdot 3 = 6u = 6(3x + 1) = 18 x + 6$.

Verify by expanding: $y = (3x + 1)^2 = 9 x^2 + 6 x + 1$. $dy/dx = 18 x + 6$. ✓

The chain rule is what lets us differentiate complicated functions by composing simpler steps. We never have to expand and simplify the full algebraic expression — we just track the chain of dependencies.

---

## 15.6 The multivariate chain rule

Now the version that we actually need. Suppose $f$ is a function of several intermediate variables, each of which is itself a function of the inputs.

Concrete case to keep in mind: $f$ depends on $u$ and $v$, and $u$ and $v$ each depend on $x$ and $y$. So $f = f(u(x, y),\ v(x, y))$.

How does $f$ depend on $x$? By the **multivariate chain rule**:

$$
\frac{\partial f}{\partial x} \;=\; \frac{\partial f}{\partial u} \cdot \frac{\partial u}{\partial x} \;+\; \frac{\partial f}{\partial v} \cdot \frac{\partial v}{\partial x}.
$$

Similarly for $y$:

$$
\frac{\partial f}{\partial y} \;=\; \frac{\partial f}{\partial u} \cdot \frac{\partial u}{\partial y} \;+\; \frac{\partial f}{\partial v} \cdot \frac{\partial v}{\partial y}.
$$

The pattern: sum over all paths from the input ($x$ or $y$) to the output ($f$), multiplying derivatives along each path.

### 15.6.1 Worked example with a tiny "neural network"

This is the worked example that anchors everything. We're going to compute the gradient of a tiny one-hidden-unit "neural network" by the chain rule. The exact same logic, applied to billion-parameter networks, is **backpropagation**.

Setup. We have:
- An input $x$ (scalar for simplicity).
- A weight $w_1$ from input to hidden unit.
- A hidden unit value $u = w_1 \cdot x$ (linear; no activation, to keep this small).
- A weight $w_2$ from hidden unit to output.
- An output $y = w_2 \cdot u = w_2 \cdot w_1 \cdot x$.
- A label $t$ (the target).
- A loss $L = (y - t)^2$ (squared error).

So $L$ is, at the bottom, a function of $w_1$, $w_2$ (and the data $x, t$, but those are fixed during training). We want to know:

$$
\frac{\partial L}{\partial w_1}, \quad \frac{\partial L}{\partial w_2}.
$$

These tell us how to update $w_1$ and $w_2$ via gradient descent.

**Compute $\partial L / \partial w_2$.** We can write the chain $L \to y \to w_2$. So

$$
\frac{\partial L}{\partial w_2} = \frac{\partial L}{\partial y} \cdot \frac{\partial y}{\partial w_2}.
$$

- $L = (y - t)^2$, so $\partial L / \partial y = 2 (y - t)$.
- $y = w_2 \cdot u$, so $\partial y / \partial w_2 = u$.

Therefore: $\partial L / \partial w_2 = 2 (y - t) \cdot u$.

**Compute $\partial L / \partial w_1$.** Chain $L \to y \to u \to w_1$:

$$
\frac{\partial L}{\partial w_1} = \frac{\partial L}{\partial y} \cdot \frac{\partial y}{\partial u} \cdot \frac{\partial u}{\partial w_1}.
$$

- $\partial L / \partial y = 2(y - t)$, as before.
- $\partial y / \partial u = w_2$.
- $\partial u / \partial w_1 = x$.

Therefore: $\partial L / \partial w_1 = 2(y - t) \cdot w_2 \cdot x$.

**Numerical check.** Say $x = 1$, $w_1 = 2$, $w_2 = 3$, $t = 7$. Then $u = 2$, $y = 6$, $L = (6 - 7)^2 = 1$.

$\partial L / \partial w_2 = 2(6 - 7) \cdot 2 = -4$. So increasing $w_2$ would *decrease* $L$ (since the partial is negative). Step in direction $-\partial L / \partial w_2 = +4$. With learning rate $\eta = 0.01$, new $w_2 = 3 + 0.04 = 3.04$.

$\partial L / \partial w_1 = 2(6 - 7) \cdot 3 \cdot 1 = -6$. New $w_1 = 2 + 0.06 = 2.06$.

Check whether the loss improved: with the new weights, $y_{\text{new}} = 2.06 \cdot 3.04 \cdot 1 = 6.2624$, $L_{\text{new}} = (6.2624 - 7)^2 = 0.5434$. Loss went from $1.0$ to $0.54$. Down by half in one step.

That's backpropagation. The math is exactly the chain rule applied to a function composition; for deeper networks, you just keep chaining more $\partial / \partial$ factors. The bookkeeping is enormous in practice — billions of parameters, layers of compositions — but the principle is what we just did.

### 15.6.2 The "computation graph" picture

A useful mental aid: draw the computation as a directed graph, with inputs at the top, intermediate variables in the middle, and the output at the bottom. The chain rule is then "for every path from an input to the output, multiply derivatives along the path; sum over all paths."

```
        w1    x         w2
          \  /           |
           u             |
            \           /
              y = w2 * u
                  |
                  L = (y - t)^2
```

Paths from $w_1$ to $L$: $w_1 \to u \to y \to L$, one path. Derivative is the product $\partial u / \partial w_1 \cdot \partial y / \partial u \cdot \partial L / \partial y = x \cdot w_2 \cdot 2(y - t)$. Matches.

Paths from $w_2$ to $L$: $w_2 \to y \to L$, one path. Derivative is $\partial y / \partial w_2 \cdot \partial L / \partial y = u \cdot 2(y - t)$. Matches.

For more complex networks with branches and merges, you sum over all paths. This is the universal backpropagation algorithm.

---

## 15.7 The Hessian — second derivatives in many variables

Just as the derivative has a second derivative ($f''$) telling you about curvature, a multi-variable function has a **Hessian matrix** of second partial derivatives:

$$
H_{ij} = \frac{\partial^2 f}{\partial x_i \partial x_j}.
$$

For our $f(x, y) = x^2 + 3 y^2$:

$$
H = \begin{pmatrix} \partial^2 f / \partial x^2 & \partial^2 f / \partial x \partial y \\ \partial^2 f / \partial y \partial x & \partial^2 f / \partial y^2 \end{pmatrix} = \begin{pmatrix} 2 & 0 \\ 0 & 6 \end{pmatrix}.
$$

The Hessian is symmetric (by Clairaut's theorem, equality of mixed partials, for any smooth $f$).

What does the Hessian *tell* you?

- **Convexity.** If $H$ is **positive semi-definite** everywhere (all eigenvalues non-negative), $f$ is **convex** — there is a unique global minimum (no local optima to get trapped in). If $H$ is positive definite (strictly positive eigenvalues), $f$ is *strictly* convex with a unique minimum. Our $H$ above has eigenvalues $2, 6$, both positive — $f$ is strictly convex. Good.

- **Curvature.** The eigenvalues of $H$ tell you how curved $f$ is in each principal direction. Large eigenvalue $=$ steeply curved (narrow valley); small eigenvalue $=$ gently curved (broad valley). The ratio of largest to smallest eigenvalue is the **condition number** of $H$, and high condition numbers make gradient descent zigzag — see Chapter 17.

- **Newton's method.** Second-order optimisation methods use the Hessian explicitly: $\mathbf{x}_{\text{new}} = \mathbf{x} - H^{-1} \nabla f$. Newton's method converges much faster than gradient descent when it applies, but inverting a million-by-million Hessian is impractical, so in deep learning we settle for first-order methods.

We won't go deep on the Hessian here; the role it plays in Part D is mostly diagnostic. But you should know it exists, what its eigenvalues mean for convergence, and why convexity guarantees nice behaviour.

---

## 15.8 Convexity — what makes a loss function tame

A function $f : \mathbb{R}^n \to \mathbb{R}$ is **convex** if, for any two points $\mathbf{x}, \mathbf{y}$ in its domain and any $\alpha \in [0, 1]$,

$$
f(\alpha \mathbf{x} + (1 - \alpha) \mathbf{y}) \leq \alpha f(\mathbf{x}) + (1 - \alpha) f(\mathbf{y}).
$$

Geometrically: the function lies below the chord between any two of its points. The classic 1D picture is a bowl: any chord drawn on top of the function is above the function itself.

Convex functions have *no local minima that aren't global*. Every local minimum is the global minimum. This is the deepest reason ML practitioners love convex losses: gradient descent on a convex loss is guaranteed to find the global optimum (eventually, with a small enough step size). No initialisation tricks, no warm restarts, no fear of bad local minima.

Linear regression's loss (mean squared error) is convex. Logistic regression's loss (cross-entropy) is convex. SVMs' loss is convex. This is not an accident — classical statistical learning carefully chose loss functions that are convex precisely so that optimisation is well-behaved. The 1950s-1990s of ML was, in large part, the era of convex losses.

Neural networks are a striking exception. Their losses are *not* convex in the network weights — there are many local minima, saddle points, plateaus, and the optimisation landscape is studied for its own sake. The fact that gradient descent works *well enough* on these non-convex losses is one of the surprises of deep learning. But that story is for another book.

For Part D, you should keep in mind: when the loss is convex, gradient descent is theoretically clean and works reliably. When it's not, all bets are off, and you rely on empirical tricks (good initialisation, learning-rate schedules, adaptive optimisers).

---

## 15.9 Code, last

We'll compute gradients by hand in NumPy. No autograd yet — that's the magic of PyTorch / JAX, but understanding what they're doing under the hood requires having done it manually at least once.

```python
import numpy as np

# A 2D convex function — a paraboloid
def f(x, y):
    return x**2 + 3 * y**2

# Its gradient, derived analytically
def grad_f(x, y):
    return np.array([2 * x, 6 * y])

# Gradient descent loop
x, y = 2.0, 1.0
lr = 0.1
trajectory = [(x, y, f(x, y))]
for step in range(30):
    gx, gy = grad_f(x, y)
    x -= lr * gx
    y -= lr * gy
    trajectory.append((x, y, f(x, y)))

for i, (xi, yi, fi) in enumerate(trajectory[::5]):
    print(f"step {i*5:3d}: x={xi:+.4f}  y={yi:+.4f}  f={fi:.6f}")
# step   0: x=+2.0000  y=+1.0000  f=7.000000
# step   5: x=+0.6554  y=+0.0102  f=0.430...
# step  10: x=+0.2147  y=+0.0001  f=0.046...
# step  15: x=+0.0703  y=+0.0000  f=0.005...
# ... converges to (0, 0)

# The little neural network from section 15.6.1
def forward(w1, w2, x):
    u = w1 * x
    y_pred = w2 * u
    return u, y_pred

def loss(y_pred, t):
    return (y_pred - t) ** 2

def grads(w1, w2, x, t):
    # Forward
    u = w1 * x
    y_pred = w2 * u
    # Backward (chain rule, by hand)
    dL_dy = 2 * (y_pred - t)
    dL_dw2 = dL_dy * u
    dL_du = dL_dy * w2
    dL_dw1 = dL_du * x
    return dL_dw1, dL_dw2

x_data, t_data = 1.0, 7.0
w1, w2 = 2.0, 3.0
lr = 0.01

for step in range(200):
    u, y_pred = forward(w1, w2, x_data)
    L = loss(y_pred, t_data)
    dL_dw1, dL_dw2 = grads(w1, w2, x_data, t_data)
    w1 -= lr * dL_dw1
    w2 -= lr * dL_dw2
    if step % 25 == 0:
        print(f"step {step:3d}: w1={w1:.4f}  w2={w2:.4f}  L={L:.6f}")
# step   0: w1=2.0600  w2=3.0400  L=1.000000
# step  25: w1=2.4...  w2=3.5...  L=...
# ... L drives toward 0 as the product w1*w2 approaches 7

# Verify a partial derivative numerically (finite-difference sanity check)
def num_partial(f, args, i, h=1e-6):
    args_plus = list(args); args_plus[i] += h
    args_minus = list(args); args_minus[i] -= h
    return (f(*args_plus) - f(*args_minus)) / (2 * h)

# Recompute partial of L wrt w1 numerically at the starting point
def L_full(w1, w2, x, t):
    return (w2 * w1 * x - t) ** 2

print(num_partial(L_full, (2.0, 3.0, 1.0, 7.0), 0))   # ~ -6.0  (matches analytic)
print(num_partial(L_full, (2.0, 3.0, 1.0, 7.0), 1))   # ~ -4.0  (matches analytic)
```

Two practical notes. First: **always sanity-check analytic gradients with finite differences** when implementing a new model. Compute the gradient both ways and verify they agree to a few decimal places. This catches the vast majority of math errors. Second: deep learning frameworks (PyTorch, JAX, TensorFlow) automate the chain-rule computation via **automatic differentiation** — you specify the forward computation, the framework constructs the computation graph and computes gradients automatically. But the framework is just doing what we did by hand above, at scale. If you understand the manual derivation, the framework's behaviour stops being magic.

---

## 15.10 Edge cases and engineering tradeoffs

**Non-differentiable points.** The L1 norm $\|\mathbf{x}\|_1 = \sum |x_i|$ is not differentiable at points where some $x_i = 0$. The function has a "kink" there. For such losses, we use **subgradients** — generalisations of gradients that work at non-smooth points. Lasso regularisation (L1 penalty) requires this machinery and is the reason lasso has "sparse" solutions (coefficients exactly zero); we'll meet it again in Chapter 20.

**Gradient explosion and vanishing.** In deep networks, the chain rule multiplies many factors together. If each factor is $> 1$, the product can grow enormous (exploding gradient); if each is $< 1$, the product can shrink to zero (vanishing gradient). This is a major topic in deep learning, addressed by initialisation schemes, batch normalisation, residual connections, and care with activation functions. Out of scope for this book.

**Numerical precision of finite differences.** The finite-difference approximation $(f(x + h) - f(x))/h$ requires careful choice of $h$. Too large: inaccurate due to truncation. Too small: catastrophic cancellation from subtracting nearly-equal floats. The "centred" version $(f(x+h) - f(x-h))/(2h)$ has lower truncation error, and $h \sim 10^{-6}$ is a reasonable default for double-precision. Use finite differences only for sanity checks, never for production gradient computation.

**The learning rate.** This single hyperparameter swings between "gradient descent converges in 50 steps" and "gradient descent diverges to infinity." Too small: slow. Too large: oscillates or diverges. Modern optimisers (Adam, RMSprop) try to adapt the learning rate per parameter; we'll see them in Chapter 17.

---

## 15.11 What this builds on / where this returns

**Builds on:** single-variable calculus (high school / early university). The dot product from Chapter 12 (because gradient times direction is a dot product). The matrix derivative formalism implicitly draws on the matrix algebra of Chapter 13.

**Returns:**

- **Loss functions** (Chapter 16): we'll define the canonical losses (MSE, cross-entropy) and compute their gradients explicitly.
- **Gradient descent** (Chapter 17): the algorithm we sketched here will be made rigorous, with convergence analysis, SGD, mini-batch, momentum, and Adam.
- **Bias-variance** (Chapter 19): the decomposition relies on expectation and variance algebra, which we set up in Part B but also rests on the existence of optimal weights minimising expected loss — a calculus statement.
- **Linear regression** (Chapter 31): the closed-form solution $\hat{\mathbf{w}} = (X^T X)^{-1} X^T \mathbf{y}$ comes from setting the gradient of MSE to zero.
- **Logistic regression** (Chapter 32): no closed form, but a convex loss whose gradient we'll compute via the chain rule, then optimise via gradient descent.
- **Backpropagation** (mentioned but not derived in this book): the chain rule applied to the computation graph of a neural network. Once you've done the tiny example in section 15.6.1, you've done backprop in miniature.

---

## 15.12 Exercises

1. **One-variable derivatives.** Compute $f'(x)$ for: (a) $f(x) = 3 x^4 - 2x^2 + 5$; (b) $f(x) = \sin(x) + e^x$; (c) $f(x) = 1/x$ for $x \neq 0$.

2. **Partial derivatives.** For $f(x, y) = x^2 y + 3 x y^3$, compute $\partial f / \partial x$ and $\partial f / \partial y$.

3. **Gradient at a point.** For $f(x, y) = x^2 + 3 y^2$, what is $\nabla f$ at $(3, -1)$? Which direction is steepest descent? With learning rate $\eta = 0.05$, where does one gradient-descent step take you?

4. **Gradient and contour.** For $f(x, y) = x^2 + y^2$, the contours are circles around the origin. The gradient at $(1, 1)$ is $(2, 2)$. Verify (geometrically or algebraically) that this is perpendicular to the contour at that point.

5. **Steepest descent vs random direction.** At the point $(3, -1)$ for $f = x^2 + 3y^2$, the gradient is $(6, -6)$. Compute the directional derivative of $f$ in the directions (a) of $\nabla f$, (b) of $-\nabla f$, (c) of the unit vector $(1, 0)$. Which gives the largest decrease, which gives the largest increase?

6. **Chain rule single-variable.** Compute $dy/dx$ for $y = \cos(3 x^2 + 1)$.

7. **Chain rule with two intermediate variables.** $f(u, v) = u^2 + v^2$, $u(x) = x + 1$, $v(x) = 2x$. Compute $df/dx$ two ways: (a) substitute and differentiate; (b) use the chain rule with two paths. Verify they agree.

8. **The tiny network.** Repeat the gradient calculation in section 15.6.1 but for $x = 2$, $w_1 = 1$, $w_2 = 2$, $t = 5$. Compute $u$, $y$, $L$, $\partial L / \partial w_1$, $\partial L / \partial w_2$. Take one gradient-descent step with $\eta = 0.05$ and compute the new loss.

9. **Hessian.** Compute the Hessian of $f(x, y) = x^2 + 3 y^2$. What are its eigenvalues? Is $f$ convex?

10. **Non-convex example.** Sketch $f(x) = x^4 - 2 x^2$. (Hint: it's a "double well" with two local minima.) Where are the local minima and the local maximum? At each, what is $f'$? At each, what is $f''$? Is $f$ convex?

11. **Convexity definition.** Use the definition (15.8) to verify that $f(x) = x^2$ is convex on $\mathbb{R}$. (Show $f(\alpha a + (1-\alpha) b) \leq \alpha f(a) + (1-\alpha) f(b)$ for all $a, b, \alpha \in [0, 1]$.)

12. **Gradient descent step size.** For $f(x) = x^2$ starting at $x_0 = 1$, what step size $\eta$ makes gradient descent (a) converge geometrically, (b) bounce back to $-1$ exactly, (c) diverge? Express the new $x$ in terms of $x_0$ and $\eta$ after one step.

13. **Connection to ML.** Logistic regression's loss for a single example is $L(\mathbf{w}) = -[y \log \sigma(\mathbf{w} \cdot \mathbf{x}) + (1 - y) \log(1 - \sigma(\mathbf{w} \cdot \mathbf{x}))]$, where $\sigma$ is the sigmoid. Without computing yet (we'll do it formally in Chapter 32), describe what tools from this chapter you'd use to derive $\partial L / \partial w_j$.

14. **Finite-difference check.** For $f(x, y) = x^2 + 3 y^2$, write the finite-difference approximation to $\partial f / \partial x$ at $(2, 1)$ with $h = 0.001$. Compute both that and the analytic value. How close do they agree?

<details>
<summary>Answers</summary>

1. (a) $f'(x) = 12 x^3 - 4 x$. (b) $f'(x) = \cos(x) + e^x$. (c) $f'(x) = -1/x^2$.

2. $\partial f / \partial x = 2 x y + 3 y^3$. $\partial f / \partial y = x^2 + 9 x y^2$.

3. $\nabla f(3, -1) = (6, -6)$. Steepest descent direction: $-(6, -6) = (-6, 6)$. One step: $(3, -1) - 0.05 (6, -6) = (3 - 0.3, -1 + 0.3) = (2.7, -0.7)$.

4. Tangent to circle $x^2 + y^2 = 2$ at $(1, 1)$ has direction $(-1, 1)$ (perpendicular to the radial direction $(1, 1)$). Dot product with the gradient: $(2)(- 1) + (2)(1) = 0$. Perpendicular.

5. Directional derivative of $f$ in unit direction $\mathbf{u}$ is $\nabla f \cdot \mathbf{u}$. (a) $\mathbf{u} = (6, -6)/\sqrt{72}$. Directional: $(6, -6) \cdot (6, -6)/\sqrt{72} = 72/\sqrt{72} = \sqrt{72} \approx 8.49$. Largest *positive* — direction of steepest increase. (b) Opposite — $-\sqrt{72} \approx -8.49$. Largest *negative* — steepest decrease. (c) $\mathbf{u} = (1, 0)$, directional derivative $= 6$. Intermediate.

6. Let $u = 3 x^2 + 1$, $y = \cos(u)$. $dy/du = -\sin(u)$. $du/dx = 6x$. So $dy/dx = -6x \sin(3x^2 + 1)$.

7. (a) Substitute: $f(x) = (x+1)^2 + (2x)^2 = x^2 + 2x + 1 + 4x^2 = 5 x^2 + 2 x + 1$. $df/dx = 10 x + 2$. (b) Chain rule: $\partial f / \partial u = 2u$, $\partial f / \partial v = 2v$. $du/dx = 1$, $dv/dx = 2$. $df/dx = 2u \cdot 1 + 2v \cdot 2 = 2(x+1) + 4(2x) = 2x + 2 + 8x = 10 x + 2$. Agree.

8. $u = 1 \cdot 2 = 2$. $y = 2 \cdot 2 = 4$. $L = (4 - 5)^2 = 1$. $\partial L / \partial w_2 = 2(4 - 5) \cdot u = -2 \cdot 2 = -4$. $\partial L / \partial w_1 = 2(4 - 5) \cdot w_2 \cdot x = -2 \cdot 2 \cdot 2 = -8$. New $w_1 = 1 - 0.05(-8) = 1.4$. New $w_2 = 2 - 0.05(-4) = 2.2$. New $y = 1.4 \cdot 2.2 \cdot 2 = 6.16$, new $L = (6.16 - 5)^2 = 1.346$. Loss got *worse*! The step size was too large. (With $\eta = 0.01$ instead, loss would decrease as expected. This is exactly the "learning rate too large" symptom.)

9. $H = \begin{pmatrix} 2 & 0 \\ 0 & 6 \end{pmatrix}$. Eigenvalues: $2, 6$. Both positive, so $H$ is positive definite at every point, so $f$ is strictly convex. (Indeed, $(0, 0)$ is the unique global minimum.)

10. $f'(x) = 4 x^3 - 4 x = 4 x (x^2 - 1)$. Zeros at $x = -1, 0, 1$. $f''(x) = 12 x^2 - 4$. At $x = -1$: $f'' = 8 > 0$ — local minimum. At $x = 0$: $f'' = -4 < 0$ — local maximum. At $x = 1$: $f'' = 8 > 0$ — local minimum. Two local (and global) minima at $\pm 1$, one local max at $0$. *Not* convex; $f''$ changes sign.

11. $f(\alpha a + (1-\alpha) b) = (\alpha a + (1-\alpha) b)^2 = \alpha^2 a^2 + 2\alpha(1-\alpha) ab + (1-\alpha)^2 b^2$. We want this $\leq \alpha a^2 + (1-\alpha) b^2$. The difference is $\alpha a^2 + (1-\alpha) b^2 - [\alpha^2 a^2 + 2\alpha(1-\alpha) ab + (1-\alpha)^2 b^2] = \alpha(1-\alpha) a^2 - 2\alpha(1-\alpha) ab + \alpha(1-\alpha) b^2 = \alpha(1-\alpha)(a - b)^2 \geq 0$ since $\alpha(1-\alpha) \geq 0$ on $[0, 1]$. So $f$ is convex.

12. $f'(x) = 2x$. $x_{\text{new}} = x - \eta \cdot 2 x = (1 - 2\eta) x$. (a) Geometric convergence if $|1 - 2\eta| < 1$, i.e., $0 < \eta < 1$. (b) Bounces back to $-1$ exactly if $1 - 2\eta = -1$, i.e., $\eta = 1$. (c) Diverges if $|1 - 2\eta| > 1$, i.e., $\eta > 1$ (or $\eta < 0$).

13. The chain rule on the composition $L \circ \sigma \circ (\mathbf{w} \cdot \mathbf{x})$. Specifically: $\partial L / \partial w_j = (\partial L / \partial \sigma) \cdot (\partial \sigma / \partial z) \cdot (\partial z / \partial w_j)$ where $z = \mathbf{w} \cdot \mathbf{x}$. The last factor is $x_j$. The middle factor uses $d\sigma/dz = \sigma(z)(1 - \sigma(z))$ — a special identity for the sigmoid. The first factor is from differentiating the cross-entropy. A nice algebra collapse happens that leaves $\partial L / \partial w_j = (\sigma(z) - y) x_j$ — extremely clean. We do all this in Chapter 32.

14. Analytic: $\partial f / \partial x \big|_{(2,1)} = 2(2) = 4$. Finite difference: $(f(2.001, 1) - f(1.999, 1)) / 0.002 = ((2.001^2 + 3) - (1.999^2 + 3)) / 0.002 = (4.004001 - 3.996001) / 0.002 = 0.008 / 0.002 = 4$. Agreement is essentially exact for this polynomial (to floating-point precision). For more complex functions, agreement to ~6 decimal places is typical.

</details>
