# Chapter 12 — Dot Products, Projections, Orthogonality

> **Goal of this chapter:** to build, from scratch, the geometric and algebraic machinery of the dot product — and then to use it for the two things that show up in every ML model: measuring how similar two vectors are, and projecting one vector onto another. Back in Chapter 3 we said "the model computes $\mathbf{w} \cdot \mathbf{x} + b$ for each email." That dot product is doing the work of comparing the email's word counts to the learned weights — a similarity computation, dressed up as arithmetic. Every linear model in this book reduces, at prediction time, to a dot product. You should understand what that dot product is *measuring*.

---

## 12.1 The motivating question — how similar are two emails?

Take two emails. Each one is a 5,000-dimensional bag-of-words vector. Their "subject matter" is, in some intuitive sense, captured by which words are in them and how often.

You want a number — a single scalar — that says whether they're talking about the same thing. Large when they're about the same thing, small when they're not.

A few candidates suggest themselves immediately. You could:

- Count the number of shared words. (Crude. Doesn't account for frequency.)
- Compute the Euclidean distance between them. (Better, but the absolute magnitudes interfere. A long spam email and a short spam email are far apart in L2 distance even if they're about the same thing, because one has way more total counts.)
- Compute the *angle* between the two vectors. (This is, it will turn out, what we want.)

The angle has a nice property: it doesn't care about how long the vectors are, only about which direction they point. Two emails about basketball, one short and one long, are pointing in roughly the same direction even though they have very different L2 norms. We want a similarity metric that returns "1" for "same direction" and "0" for "orthogonal" (totally unrelated), regardless of magnitudes.

The tool that gives us the angle — and a thousand other useful things — is the dot product. It is going to occupy this entire chapter.

---

## 12.2 The dot product, algebraically

Given two vectors $\mathbf{a}, \mathbf{b} \in \mathbb{R}^n$, their **dot product** is defined to be

$$
\mathbf{a} \cdot \mathbf{b} \;=\; \sum_{i=1}^{n} a_i b_i \;=\; a_1 b_1 + a_2 b_2 + \cdots + a_n b_n.
$$

A scalar — a single real number. Note that the dot product takes two vectors and returns a number, not another vector. It "contracts" two vectors down to one number.

For example, in $\mathbb{R}^3$, the dot product of $\mathbf{a} = (1, 2, 3)$ and $\mathbf{b} = (4, -1, 2)$ is

$$
\mathbf{a} \cdot \mathbf{b} = 1 \cdot 4 + 2 \cdot (-1) + 3 \cdot 2 = 4 - 2 + 6 = 8.
$$

Some authors and codebases write the same thing as $\mathbf{a}^T \mathbf{b}$ (row times column, a $1 \times n$ times $n \times 1$ matrix product). The two notations mean the same thing; we'll use $\cdot$ when we want the dot-product intuition and $\mathbf{a}^T \mathbf{b}$ when matrix algebra is the context.

Three algebraic properties to write down (they are easy to prove by unfolding the sums, and we'll need each):

1. **Symmetric.** $\mathbf{a} \cdot \mathbf{b} = \mathbf{b} \cdot \mathbf{a}$. Obvious from the definition.
2. **Linear in each argument.** $(\mathbf{a} + \mathbf{b}) \cdot \mathbf{c} = \mathbf{a} \cdot \mathbf{c} + \mathbf{b} \cdot \mathbf{c}$, and $(c\mathbf{a}) \cdot \mathbf{b} = c (\mathbf{a} \cdot \mathbf{b})$.
3. **Positive definite.** $\mathbf{a} \cdot \mathbf{a} = \sum a_i^2 \geq 0$, with equality only when $\mathbf{a} = \mathbf{0}$. In particular, $\mathbf{a} \cdot \mathbf{a} = \|\mathbf{a}\|_2^2$ — the dot product of a vector with itself is the *square* of its Euclidean length.

That last identity, $\mathbf{a} \cdot \mathbf{a} = \|\mathbf{a}\|^2$, is the bridge between the algebraic and geometric views. Norm and dot product are not independent — the dot product *defines* the L2 norm.

---

## 12.3 The dot product, geometrically

The algebra is direct. But where is the *angle*?

Here is the geometric formula:

$$
\mathbf{a} \cdot \mathbf{b} \;=\; \|\mathbf{a}\|\, \|\mathbf{b}\| \cos\theta,
$$

where $\theta$ is the angle between the two vectors when their tails are placed at the origin.

This is one of the most consequential equations in all of linear algebra. The dot product is the product of the magnitudes times the *cosine* of the angle between them. From this single equation you can derive almost everything else in this chapter — projections, orthogonality, cosine similarity.

Let's prove it.

### 12.3.1 Deriving the equivalence

Start with the law of cosines from high school trigonometry. In a triangle with sides of length $|\mathbf{a}|$, $|\mathbf{b}|$, and $|\mathbf{c}|$ (where $\mathbf{c} = \mathbf{a} - \mathbf{b}$, the third side of the triangle from the head of $\mathbf{b}$ to the head of $\mathbf{a}$), with the angle $\theta$ between $\mathbf{a}$ and $\mathbf{b}$:

$$
\|\mathbf{c}\|^2 = \|\mathbf{a}\|^2 + \|\mathbf{b}\|^2 - 2 \|\mathbf{a}\| \|\mathbf{b}\| \cos \theta.
$$

(Just the standard law-of-cosines from a high-school trig class. If $\theta = 90°$, $\cos \theta = 0$ and this reduces to the Pythagorean theorem.)

Now expand $\|\mathbf{c}\|^2 = \|\mathbf{a} - \mathbf{b}\|^2$ using the algebraic definition of the dot product:

$$
\|\mathbf{a} - \mathbf{b}\|^2 = (\mathbf{a} - \mathbf{b}) \cdot (\mathbf{a} - \mathbf{b}) = \mathbf{a} \cdot \mathbf{a} - 2 \mathbf{a} \cdot \mathbf{b} + \mathbf{b} \cdot \mathbf{b} = \|\mathbf{a}\|^2 - 2 \mathbf{a} \cdot \mathbf{b} + \|\mathbf{b}\|^2.
$$

(Used the linearity and symmetry of the dot product, and the fact that $\mathbf{v} \cdot \mathbf{v} = \|\mathbf{v}\|^2$.)

So we have two expressions for $\|\mathbf{c}\|^2$:

$$
\|\mathbf{a}\|^2 + \|\mathbf{b}\|^2 - 2 \|\mathbf{a}\| \|\mathbf{b}\| \cos \theta \;=\; \|\mathbf{a}\|^2 - 2 \mathbf{a} \cdot \mathbf{b} + \|\mathbf{b}\|^2.
$$

Cancel the $\|\mathbf{a}\|^2 + \|\mathbf{b}\|^2$ from both sides and divide by $-2$:

$$
\|\mathbf{a}\| \|\mathbf{b}\| \cos \theta \;=\; \mathbf{a} \cdot \mathbf{b}. \qquad \blacksquare
$$

The algebraic dot product and the geometric "magnitudes times cosine" are *the same thing*. Two definitions, one quantity.

### 12.3.2 What this tells us

A few immediate consequences.

**Sign of the cosine $=$ sign of the dot product.** $\cos \theta > 0$ for acute angles ($\theta < 90°$); $\cos \theta = 0$ at $\theta = 90°$; $\cos \theta < 0$ for obtuse angles. So:

- Positive dot product $\Leftrightarrow$ vectors point in *roughly the same direction*.
- Zero dot product $\Leftrightarrow$ vectors are **perpendicular** (orthogonal).
- Negative dot product $\Leftrightarrow$ vectors point in *roughly opposite directions*.

This is the cleanest one-sentence summary of the dot product you will get. A positive number means the two vectors agree, more or less. A negative number means they disagree. Zero means they have nothing to say to each other.

**Extremes.** If $\theta = 0$ (same direction), $\cos \theta = 1$ and $\mathbf{a} \cdot \mathbf{b} = \|\mathbf{a}\| \|\mathbf{b}\|$ — the *maximum* possible value given the lengths. If $\theta = 180°$ (opposite directions), $\cos \theta = -1$ and $\mathbf{a} \cdot \mathbf{b} = -\|\mathbf{a}\| \|\mathbf{b}\|$ — the *minimum*. So for fixed lengths, the dot product is maximised when the vectors align and minimised when they point opposite.

```
                   ↗
                  ↗ b
   ̂a · b > 0:   ↗      ← acute angle between a and b
                ↗
       ────────► a

                   ↑
                   │ b
   a · b = 0:      │      ← right angle
                   │
       ────────► a

       ◄────
   a · b < 0:   ← b      ← obtuse angle
                ◄────────► a
```

---

## 12.4 Cosine similarity — measuring direction, ignoring magnitude

Going back to the motivating problem in section 12.1: we wanted a similarity metric that doesn't care about magnitude. From the geometric formula:

$$
\cos \theta \;=\; \frac{\mathbf{a} \cdot \mathbf{b}}{\|\mathbf{a}\| \|\mathbf{b}\|}.
$$

This quantity — the cosine of the angle between $\mathbf{a}$ and $\mathbf{b}$ — is called the **cosine similarity** between them. It is the dot product, normalised by the product of the norms. It always lies in $[-1, 1]$. It equals $1$ for vectors in the same direction, $0$ for perpendicular, $-1$ for opposite.

Cosine similarity is the workhorse similarity metric for high-dimensional data. NLP, recommender systems, image retrieval — wherever you have vectors that live in a high-dimensional space and you want to compare them, you'll see cosine similarity. It's used because:

- It is invariant to magnitude. A long document and a short document on the same topic have the same cosine similarity to a query, regardless of length.
- It has a clean range $[-1, 1]$ with intuitive endpoints.
- It is fast to compute — just a dot product and two norms.

For positive-valued data (like word counts, which are non-negative), cosine similarity actually lives in $[0, 1]$, because the dot product of two non-negative vectors cannot be negative. That makes it especially friendly for bag-of-words.

### 12.4.1 Worked numerical example

Consider two emails encoded over a 5-word vocabulary (this is small enough to work by hand):

$$
\mathbf{a} = (1, 0, 1, 0, 1), \qquad \mathbf{b} = (1, 1, 0, 0, 1).
$$

Dot product:

$$
\mathbf{a} \cdot \mathbf{b} = 1 \cdot 1 + 0 \cdot 1 + 1 \cdot 0 + 0 \cdot 0 + 1 \cdot 1 = 1 + 0 + 0 + 0 + 1 = 2.
$$

Norms:

$$
\|\mathbf{a}\| = \sqrt{1 + 0 + 1 + 0 + 1} = \sqrt{3} \approx 1.732.
$$

$$
\|\mathbf{b}\| = \sqrt{1 + 1 + 0 + 0 + 1} = \sqrt{3} \approx 1.732.
$$

Cosine similarity:

$$
\cos \theta = \frac{2}{\sqrt{3} \cdot \sqrt{3}} = \frac{2}{3} \approx 0.667.
$$

The angle itself is $\theta = \arccos(2/3) \approx 48.2°$. Intuitively: the two emails share two words out of three nonzero positions in each, so they overlap "two-thirds" in a loose sense — and the cosine confirms it numerically.

A second example for contrast: $\mathbf{a} = (1, 0, 1, 0, 1)$ and $\mathbf{c} = (0, 1, 0, 1, 0)$. Dot product is zero — the two vectors have non-zero entries in completely disjoint positions. They are **orthogonal**. Cosine similarity is $0$. The emails share no words; no similarity.

---

## 12.5 Orthogonality — the workhorse concept

Two vectors are **orthogonal** if their dot product is zero:

$$
\mathbf{a} \perp \mathbf{b} \quad\Longleftrightarrow\quad \mathbf{a} \cdot \mathbf{b} = 0.
$$

Geometrically, orthogonality means perpendicular: the angle is $90°$. In 2D and 3D this matches the everyday "at right angles" notion. In higher dimensions it generalises perfectly: two 5000-dimensional vectors are orthogonal iff $\sum a_i b_i = 0$. We can't draw it but the algebra is the same.

### 12.5.1 Why orthogonality matters in ML

Two of the deepest threads in this book hang on orthogonality.

**Orthogonal features carry no redundant information.** If features $X_1$ and $X_2$ are orthogonal across your dataset (their column vectors have dot product zero), then knowing $X_1$'s value tells you nothing about $X_2$'s value, *on average*. Models can learn weights for the two features independently — there's no cross-talk. When features are highly *non-*orthogonal (correlated), the optimisation problem becomes nasty, the weights become unstable, and you get the kind of pathology I described at the start of Chapter 11.

**PCA finds an orthonormal basis.** Principal Components Analysis (Chapter 40) rotates the data into a new coordinate system in which the new features (the principal components) are orthogonal *and* aligned with the directions of maximum variance. The "orthogonal" part is what makes the principal components independent; the "aligned with variance" part is what makes the first few of them contain most of the information.

We aren't ready to derive these claims rigorously yet. But the *concept* of orthogonality is going to come up over and over, and you should keep it cognitively cheap.

### 12.5.2 Orthonormal — orthogonal *and* unit length

A set of vectors is **orthonormal** if every vector has length $1$ and every pair is orthogonal. The standard basis $\{\mathbf{e}_1, \mathbf{e}_2, \ldots, \mathbf{e}_n\}$ of $\mathbb{R}^n$ — where $\mathbf{e}_i$ has a $1$ in position $i$ and $0$ elsewhere — is orthonormal: each $\|\mathbf{e}_i\| = 1$, and $\mathbf{e}_i \cdot \mathbf{e}_j = 0$ for $i \neq j$.

Orthonormal bases are the cleanest possible coordinate system. Once you have an orthonormal basis $\{\mathbf{u}_1, \ldots, \mathbf{u}_n\}$, any vector $\mathbf{v}$ in the space can be written as $\mathbf{v} = \sum_i (\mathbf{v} \cdot \mathbf{u}_i) \mathbf{u}_i$. The coordinates are just dot products. This decomposition is a major reason orthonormal bases are coveted; PCA gives you exactly one, custom-fit to your data.

---

## 12.6 Projection — the rest of the dot product's job

Given two non-zero vectors $\mathbf{a}$ and $\mathbf{b}$, we often want to know: how much of $\mathbf{a}$ "points along" $\mathbf{b}$? Imagine $\mathbf{b}$ as a fixed direction; we want to decompose $\mathbf{a}$ into a piece *along* $\mathbf{b}$ and a piece *perpendicular* to $\mathbf{b}$.

The piece along $\mathbf{b}$ is the **projection** of $\mathbf{a}$ onto $\mathbf{b}$, written $\text{proj}_{\mathbf{b}}(\mathbf{a})$.

```
            ╱ a
           ╱
          ╱│ 
         ╱ │← (a - proj_b a), perpendicular to b
        ╱  │
       ╱   │
      ────●─────────► b
         proj_b a
```

The projection is the "shadow" of $\mathbf{a}$ on the line spanned by $\mathbf{b}$, when light shines perpendicular to that line. The leftover, $\mathbf{a} - \text{proj}_{\mathbf{b}}(\mathbf{a})$, is exactly the part of $\mathbf{a}$ perpendicular to $\mathbf{b}$.

### 12.6.1 Deriving the formula

We want $\text{proj}_{\mathbf{b}}(\mathbf{a})$ to be a vector along $\mathbf{b}$. So it has the form $c \mathbf{b}$ for some scalar $c$ — we just need to find $c$.

The defining condition: $\mathbf{a} - c \mathbf{b}$ must be perpendicular to $\mathbf{b}$. That is,

$$
(\mathbf{a} - c \mathbf{b}) \cdot \mathbf{b} = 0.
$$

Expanding using linearity:

$$
\mathbf{a} \cdot \mathbf{b} - c (\mathbf{b} \cdot \mathbf{b}) = 0.
$$

Solving for $c$:

$$
c = \frac{\mathbf{a} \cdot \mathbf{b}}{\mathbf{b} \cdot \mathbf{b}}.
$$

So the projection is

$$
\boxed{\text{proj}_{\mathbf{b}}(\mathbf{a}) \;=\; \frac{\mathbf{a} \cdot \mathbf{b}}{\mathbf{b} \cdot \mathbf{b}} \, \mathbf{b}.}
$$

That is the standard formula. Notice that it depends on both the *dot product* (in the numerator) and the *squared length of $\mathbf{b}$* (in the denominator). If $\mathbf{b}$ happens to be a unit vector ($\mathbf{b} \cdot \mathbf{b} = 1$), the formula simplifies beautifully:

$$
\text{proj}_{\hat{\mathbf{b}}}(\mathbf{a}) \;=\; (\mathbf{a} \cdot \hat{\mathbf{b}}) \, \hat{\mathbf{b}}.
$$

For unit vectors, the projection of $\mathbf{a}$ onto $\hat{\mathbf{b}}$ is just "the dot product, times the direction." This is why orthonormal bases are so convenient: the coordinates of $\mathbf{v}$ in such a basis are exactly the dot products with the basis vectors. Same formula, no division.

### 12.6.2 The scalar projection vs. the vector projection

A useful distinction: $c = \mathbf{a} \cdot \hat{\mathbf{b}}$ (when $\hat{\mathbf{b}}$ is a unit vector) is the **scalar projection** — just the signed length of the shadow. $c \hat{\mathbf{b}}$ is the **vector projection** — the actual vector pointing along $\mathbf{b}$.

We use both. When we want to *measure* how much $\mathbf{a}$ points along $\mathbf{b}$, the scalar projection is the right quantity. When we want to *reconstruct* the component of $\mathbf{a}$ along $\mathbf{b}$ (e.g., for decomposition), the vector projection is what we need.

### 12.6.3 Worked numerical example

Project $\mathbf{a} = (3, 4)$ onto $\mathbf{b} = (1, 0)$ — the x-axis direction.

$$
\mathbf{a} \cdot \mathbf{b} = 3 \cdot 1 + 4 \cdot 0 = 3.
$$

$$
\mathbf{b} \cdot \mathbf{b} = 1 + 0 = 1.
$$

$$
\text{proj}_{\mathbf{b}}(\mathbf{a}) = \frac{3}{1} (1, 0) = (3, 0).
$$

And the answer is reassuringly obvious from the picture: $\mathbf{a}$'s shadow on the x-axis is just $(3, 0)$, its x-component. The math confirms what the geometry already shouted.

A less trivial example. Project $\mathbf{a} = (4, 3)$ onto $\mathbf{b} = (2, 2)$.

$$
\mathbf{a} \cdot \mathbf{b} = 4 \cdot 2 + 3 \cdot 2 = 8 + 6 = 14.
$$

$$
\mathbf{b} \cdot \mathbf{b} = 4 + 4 = 8.
$$

$$
\text{proj}_{\mathbf{b}}(\mathbf{a}) = \frac{14}{8} (2, 2) = \left( \frac{14}{4}, \frac{14}{4} \right) = (3.5, 3.5).
$$

Sanity check: the result lies on the line $y = x$ (the direction of $\mathbf{b}$). Good. And the difference $\mathbf{a} - \text{proj}_{\mathbf{b}}(\mathbf{a}) = (4, 3) - (3.5, 3.5) = (0.5, -0.5)$ should be perpendicular to $\mathbf{b}$. Verify: $(0.5, -0.5) \cdot (2, 2) = 1 - 1 = 0$. Confirmed.

### 12.6.4 Decomposing $\mathbf{a}$ into "along $\mathbf{b}$" and "perpendicular to $\mathbf{b}$"

You can always write

$$
\mathbf{a} = \underbrace{\text{proj}_{\mathbf{b}}(\mathbf{a})}_{\text{along } \mathbf{b}} + \underbrace{\left( \mathbf{a} - \text{proj}_{\mathbf{b}}(\mathbf{a}) \right)}_{\perp \mathbf{b}}.
$$

This is the *orthogonal decomposition* of $\mathbf{a}$ relative to $\mathbf{b}$. The two pieces are orthogonal to each other (we just verified this in the example), and they sum to $\mathbf{a}$.

This decomposition is the core engine behind:

- **Gram-Schmidt orthogonalisation** — the procedure for turning any basis into an orthonormal one.
- **Least squares** — projecting the observed data onto the column space of $X$ to find the best linear fit. We will see this in Chapter 31.
- **PCA** — projecting data onto the leading eigenvectors of the covariance matrix. Chapter 40.

Every one of these is "decompose $\mathbf{a}$ into along-and-perpendicular pieces" applied repeatedly. Worth holding onto.

---

## 12.7 Linear models = dot products

Let's connect the chapter back to ML, explicitly.

In Chapter 3 we said: a logistic regression's prediction is

$$
\hat{p}(\text{spam} \mid \mathbf{x}) = \sigma(\mathbf{w} \cdot \mathbf{x} + b).
$$

We can now read that formula geometrically. The model has learned a weight vector $\mathbf{w} \in \mathbb{R}^d$ — one weight per feature. For an input $\mathbf{x}$:

- $\mathbf{w} \cdot \mathbf{x}$ is a dot product. By the geometric formula, $\mathbf{w} \cdot \mathbf{x} = \|\mathbf{w}\| \|\mathbf{x}\| \cos \theta$.
- The sign of $\mathbf{w} \cdot \mathbf{x}$ tells you whether $\mathbf{x}$ points in roughly the same direction as $\mathbf{w}$ (positive — vote for spam) or in roughly the opposite direction (negative — vote for ham).
- The magnitude tells you how confident the vote is.

The model has, in effect, learned a *direction* in feature space (the direction of $\mathbf{w}$). Inputs that align with that direction get high spam scores; inputs that anti-align get low scores. The bias $b$ shifts the decision boundary off the origin.

The **decision boundary** — the set of inputs with $\mathbf{w} \cdot \mathbf{x} + b = 0$ — is, geometrically, a *hyperplane* in $\mathbb{R}^d$ perpendicular to $\mathbf{w}$. (A line in 2D, a plane in 3D, a hyperplane otherwise.) On one side of the hyperplane, $\mathbf{w} \cdot \mathbf{x} + b > 0$; on the other, $< 0$. The model labels accordingly.

```
                  ↑ w   (the weight direction)
                  │
       spam     ────────  decision boundary (w·x + b = 0)
       side          ←── x's projected here are exactly on the line
                  │
       ham        ────────
       side
```

Everything that linear models do — including logistic regression, linear regression, linear SVM, and the linear layer of a neural network — is geometrically a dot product (compute a score along a learned direction) followed by an optional nonlinearity. Once you see this, you've understood the geometric heart of a whole class of algorithms.

---

## 12.8 Code, last

```python
import numpy as np

# Dot product
a = np.array([1.0, 2.0, 3.0])
b = np.array([4.0, -1.0, 2.0])
print(a @ b)              # 8.0
print(np.dot(a, b))       # 8.0   (same thing)

# Cosine similarity
def cosine_sim(a, b):
    return (a @ b) / (np.linalg.norm(a) * np.linalg.norm(b))

a = np.array([1, 0, 1, 0, 1], dtype=float)
b = np.array([1, 1, 0, 0, 1], dtype=float)
print(cosine_sim(a, b))   # 0.6666666666666667

# Orthogonality check
c = np.array([0, 1, 0, 1, 0], dtype=float)
print(a @ c)              # 0.0   — orthogonal
print(cosine_sim(a, c))   # 0.0

# Projection
def proj(a, b):
    return (a @ b) / (b @ b) * b

a = np.array([4.0, 3.0])
b = np.array([2.0, 2.0])
p = proj(a, b)
print(p)                   # [3.5, 3.5]

# Decomposition into "along b" and "perpendicular to b"
perp = a - p
print(perp)                # [ 0.5, -0.5]
print(p @ perp)            # 0.0 — they really are orthogonal
print(np.allclose(p + perp, a))  # True — they sum to a

# Linear model prediction is just a dot product
w = np.array([0.5, -1.2, 0.3, 2.0, -0.8])
x = np.array([1.0,  3.0, 0.5, 0.0,  2.0])
b = 0.1
z = w @ x + b
print(z)                   # -4.85
sigmoid = 1.0 / (1.0 + np.exp(-z))
print(sigmoid)             # 0.0078...  (close to 0 — strong "ham" vote)
```

Two practical observations. First, in production code you almost never write `cosine_sim` by hand — `sklearn.metrics.pairwise.cosine_similarity` does the batched version efficiently, including for sparse matrices. Second, for very high-dimensional sparse data (the bag-of-words case), `scipy.sparse` matrices store only the non-zero entries and compute dot products in time proportional to the number of non-zeros, not the dimension. Doing dense dot products on $10^6$-dimensional vectors would melt the laptop; sparse dot products run in microseconds.

---

## 12.9 Edge cases and engineering tradeoffs

**Zero vectors.** Cosine similarity is undefined when either vector is zero ($0/0$). In ML this happens when a document contains *only* stopwords (which were removed from the vocabulary) — its feature vector is identically zero. Handle this defensively: define $\cos(\mathbf{0}, \mathbf{b}) := 0$ by convention, or filter zero vectors out upstream.

**Numerical precision.** For very high-dimensional sparse vectors the dot product is fine, but for very-large-magnitude dense vectors you can get catastrophic cancellation in the sum. Use `numpy.dot` rather than rolling your own loop — BLAS handles this with care.

**Cosine vs. Euclidean.** Cosine similarity ignores magnitudes; Euclidean distance respects them. They induce different geometries on the data. For text classification, cosine is more common because length is uninformative; for image embeddings, you sometimes care about magnitude too, and Euclidean (or its squared form) is the default. Always know which one your library uses by default.

**Negative cosine in non-negative data.** When all feature values are non-negative (counts, frequencies), cosine similarity is bounded in $[0, 1]$, never negative. If you see a negative cosine on what should be count data, you have a bug.

---

## 12.10 What this builds on / where this returns

**Builds on:** Chapter 11 — vectors, addition, scaling, and the L2 norm. Especially the identity $\mathbf{v} \cdot \mathbf{v} = \|\mathbf{v}\|^2$, which is the bridge between norm and dot product.

**Returns:**

- **Linear regression** (Chapter 31) is built entirely on projection: $\hat{\mathbf{y}}$ is the projection of $\mathbf{y}$ onto the column space of $X$.
- **Logistic regression** (Chapter 32) is the dot product $\mathbf{w} \cdot \mathbf{x}$ followed by a sigmoid; the decision boundary is a hyperplane perpendicular to $\mathbf{w}$.
- **K-means and other clustering** (Chapter 38) use Euclidean distance (a norm-of-difference), which is built on dot products.
- **PCA** (Chapter 40) finds an orthonormal basis of principal directions — orthogonality is the whole point.
- **Cosine similarity** appears anywhere we measure similarity in high dimensions — embedding lookup, retrieval, NLP downstream tasks.

---

## 12.11 Exercises

1. **Dot product by hand.** Compute $\mathbf{a} \cdot \mathbf{b}$ for $\mathbf{a} = (2, -1, 3)$ and $\mathbf{b} = (1, 4, -2)$.

2. **From dot product to angle.** For $\mathbf{a} = (1, 0)$ and $\mathbf{b} = (1, 1)$, compute the dot product, the two norms, $\cos \theta$, and $\theta$ itself.

3. **Cosine similarity.** Compute $\cos \theta$ for $\mathbf{a} = (3, 0, 4, 0)$ and $\mathbf{b} = (0, 5, 0, 12)$. What does the result tell you about how similar the vectors are?

4. **Cosine similarity in NLP.** Two emails encoded as $\mathbf{a} = (0, 2, 1, 0, 3)$ and $\mathbf{b} = (4, 0, 2, 1, 0)$. Compute the cosine similarity. They share one word (position 3). Does that match your intuition?

5. **Orthogonality test.** Verify that $(1, 2, -1)$ and $(3, -1, 1)$ are orthogonal.

6. **Construct an orthogonal vector.** Find a non-zero vector orthogonal to $(2, 3)$ in $\mathbb{R}^2$. How many such vectors are there, up to scalar multiples?

7. **Projection by hand.** Project $\mathbf{a} = (5, 2)$ onto $\mathbf{b} = (1, 0)$. Then project the same $\mathbf{a}$ onto $\mathbf{b} = (0, 1)$. Then add the two projections. What do you get?

8. **Projection onto a unit vector.** Let $\hat{\mathbf{u}} = (1/\sqrt{2}, 1/\sqrt{2})$. Project $\mathbf{a} = (3, 1)$ onto $\hat{\mathbf{u}}$. Then compute the perpendicular piece $\mathbf{a} - \text{proj}_{\hat{\mathbf{u}}}(\mathbf{a})$ and verify it's orthogonal to $\hat{\mathbf{u}}$.

9. **The linear model's decision boundary.** A logistic regression has weights $\mathbf{w} = (1, -1)$ and bias $b = 0$. Describe the decision boundary geometrically. Which inputs $\mathbf{x}$ are predicted as spam (score $> 0$)?

10. **Decomposition.** Decompose $\mathbf{a} = (3, 4)$ into a sum of a vector along $(1, 1)$ and a vector perpendicular to $(1, 1)$. Show both pieces.

11. **An ML interpretation.** Suppose the weight vector for a spam classifier is $\mathbf{w}$ and you see, after training, that $\mathbf{w}$ has large positive weights on the words `viagra, prize, free` (positions $i_1, i_2, i_3$) and large negative weights on `meeting, regards, attached` (positions $i_4, i_5, i_6$), with all other weights near zero. For two emails — email A about a team meeting and email B about a prize draw — describe geometrically how their feature vectors relate to $\mathbf{w}$ and why the model produces different scores.

12. **Cosine vs. Euclidean.** Two emails $\mathbf{a} = (1, 1, 1)$ and $\mathbf{b} = (10, 10, 10)$. Compute the L2 distance between them, and the cosine similarity. What does each one say about the relationship between the emails?

<details>
<summary>Answers</summary>

1. $2 \cdot 1 + (-1) \cdot 4 + 3 \cdot (-2) = 2 - 4 - 6 = -8$.

2. $\mathbf{a} \cdot \mathbf{b} = 1$. $\|\mathbf{a}\| = 1$. $\|\mathbf{b}\| = \sqrt{2}$. $\cos \theta = 1 / \sqrt{2} \approx 0.707$. $\theta = 45°$.

3. $\mathbf{a} \cdot \mathbf{b} = 0 + 0 + 0 + 0 = 0$. $\cos \theta = 0$. The vectors are *orthogonal*. They have nothing in common — every nonzero position of one is a zero position of the other.

4. $\mathbf{a} \cdot \mathbf{b} = 0 + 0 + 2 + 0 + 0 = 2$. $\|\mathbf{a}\| = \sqrt{0 + 4 + 1 + 0 + 9} = \sqrt{14} \approx 3.742$. $\|\mathbf{b}\| = \sqrt{16 + 0 + 4 + 1 + 0} = \sqrt{21} \approx 4.583$. $\cos \theta = 2 / (\sqrt{14} \sqrt{21}) = 2 / \sqrt{294} \approx 0.117$. Very small. Matches intuition — they share only one word out of many, and even that word is a small contribution.

5. $(1)(3) + (2)(-1) + (-1)(1) = 3 - 2 - 1 = 0$. Yes, orthogonal.

6. Any vector $(a, b)$ with $2a + 3b = 0$ — e.g., $(3, -2)$ or $(-3, 2)$ or $(6, -4)$. All are scalar multiples of $(3, -2)$. So there's exactly one direction's worth, up to sign and scaling.

7. Onto $(1, 0)$: $\text{proj} = (5, 0)$. Onto $(0, 1)$: $\text{proj} = (0, 2)$. Sum: $(5, 2) = \mathbf{a}$. Projections onto orthogonal axes reconstruct the original — this is exactly how coordinates in an orthonormal basis work.

8. $\mathbf{a} \cdot \hat{\mathbf{u}} = 3/\sqrt{2} + 1/\sqrt{2} = 4/\sqrt{2} = 2\sqrt{2}$. $\text{proj} = 2\sqrt{2} \cdot (1/\sqrt{2}, 1/\sqrt{2}) = (2, 2)$. Perpendicular piece: $(3, 1) - (2, 2) = (1, -1)$. Dot product with $\hat{\mathbf{u}}$: $1/\sqrt{2} - 1/\sqrt{2} = 0$. Verified orthogonal.

9. Decision boundary: $x_1 - x_2 = 0$, i.e., the line $x_1 = x_2$. Inputs with $x_1 > x_2$ have positive score (predicted spam); inputs with $x_1 < x_2$ have negative score (predicted ham).

10. Project $\mathbf{a} = (3, 4)$ onto $\mathbf{b} = (1, 1)$: $\mathbf{a} \cdot \mathbf{b} = 7$. $\mathbf{b} \cdot \mathbf{b} = 2$. $\text{proj} = (7/2)(1,1) = (3.5, 3.5)$. Perpendicular: $(3, 4) - (3.5, 3.5) = (-0.5, 0.5)$. Check: $(-0.5)(1) + (0.5)(1) = 0$. Yes. $(3, 4) = (3.5, 3.5) + (-0.5, 0.5)$. Verified.

11. Email A (meeting): has large positive components at positions $i_4, i_5, i_6$ (negative-weight words) and near-zero elsewhere. Geometrically, A points in the *opposite* direction from $\mathbf{w}$ in the dimensions that matter. So $\mathbf{w} \cdot \mathbf{x}_A < 0$ — predicted ham. Email B (prize): has large positive components at $i_1, i_2, i_3$ (positive-weight words). It points in the *same* direction as $\mathbf{w}$ in the dimensions that matter. $\mathbf{w} \cdot \mathbf{x}_B > 0$ — predicted spam. The dot product is, literally, summing the votes.

12. L2 distance: $\sqrt{81 + 81 + 81} = 9\sqrt{3} \approx 15.6$ — large. Cosine similarity: $(10 + 10 + 10) / (\sqrt{3} \cdot \sqrt{300}) = 30 / 30 = 1$. The two vectors point in *exactly* the same direction, but $\mathbf{b}$ is 10 times longer. L2 says "very far apart"; cosine says "same direction." For text, cosine's verdict is usually the one we want — these two might be a short and long document on the same topic.

</details>
