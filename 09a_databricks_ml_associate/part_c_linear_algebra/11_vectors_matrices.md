# Chapter 11 — Vectors and Matrices: Geometric Intuition First

> **Goal of this chapter:** to give you a working mental model of what a vector and a matrix *are* — not as syntactic Python objects, but as the geometric and functional things they actually represent. Back in Chapter 3 we casually said "represent an email as a 5,000-dimensional vector of word counts." That sentence hides every difficulty in linear algebra. What does "5,000-dimensional vector" actually mean? You cannot picture it. You cannot draw it on a napkin. And yet, by the end of this chapter, you should be confident that the intuitions you build for two-dimensional vectors transfer — almost unchanged — to five thousand dimensions. That confidence is what allows the rest of the math in this book to feel grounded rather than mystical.

---

## 11.1 Why we cannot skip this chapter

There is a culture among working data scientists of treating linear algebra as plumbing: "I call `numpy.dot` and a number comes out; what else is there to know?" This attitude survives until your first serious debugging session. You will train a logistic regression on 5,000 features and notice that the weights for two highly correlated features have flipped signs, in opposite directions, both with large magnitude. Why? Because the two columns are nearly *collinear*, which makes the matrix $X^T X$ nearly singular, which makes the inverse blow up, which the optimizer expresses as wild, cancelling weights. If you only know `numpy.dot`, you have no language to even diagnose this. If you know what a near-singular matrix is and why it ruins least-squares, the bug names itself.

The same thing happens with PCA. The same thing happens with the covariance matrix in any multivariate normal computation. The same thing happens with collaborative-filtering matrix factorizations, with attention layers in transformers, with embedding spaces in NLP. Every one of these is linear algebra under a thin wrapper, and the wrapper leaks the moment something goes sideways.

So we will spend this chapter — and the four after it — building the *intuition*. Not memorising formulas, not even doing very much computation. We are after the mental picture that you can pull up when the formula on the screen looks foreign. When you have that picture, the formulas become readable; when you don't, they remain hieroglyphs.

---

## 11.2 What a vector is, geometrically

Start with the easiest case: a point on a flat sheet of paper. Draw a horizontal axis and a vertical axis crossing at the origin $O$. Now mark a point at horizontal distance $3$ from the origin and vertical distance $2$. This point has two coordinates, $(3, 2)$.

We can do two different things with that pair of numbers and *both views are correct, simultaneously*. They are the two faces of every vector.

**The "point" view.** $(3, 2)$ is a location. It is a place in the plane. If your plane represents heights and weights of cats, then $(3\text{ kg}, 2\text{ m tall})$ is a specific (alarming) cat.

**The "arrow" view.** $(3, 2)$ is a displacement. It is an arrow that starts at the origin and ends at the point $(3, 2)$. It has a direction (up and to the right, a bit shallow) and a length (about $\sqrt{13} \approx 3.6$). If your plane represents a force diagram, then $(3, 2)$ is a force of magnitude $3.6$ pulling at an angle.

```
            y
            │
          3 ┤        
          2 ┤         •  ← the point (3, 2)
            │       ↗     also: the arrow from O to (3,2)
          1 ┤     ↗
            │   ↗
          0 ┼─↗─────────── x
            O 1 2 3
```

Most of the time in machine learning we tacitly use the arrow view, because we end up adding and scaling vectors, and adding arrows is more intuitive than adding points. But the point view is what gets the data scientist started: "each row of my dataset is a point in feature space." Both views are right; they are reconciled by noting that you can take any arrow and slide it so its tail is at the origin, and what's left of it is a unique point.

### 11.2.1 Three dimensions and beyond

Add a third axis pointing out of the page. Now the point $(3, 2, 1)$ is a location in space, and the arrow from origin to that point has a definite length and direction. You can still draw it, though perspective drawings of three-dimensional axes are awkward.

What about four dimensions? You cannot draw it. There is no fourth direction perpendicular to the three you already have, in physical space. The right move is to stop trying to draw, and to *trust the algebra*. A four-dimensional vector is just an ordered list of four numbers, $(3, 2, 1, 7)$. The geometric operations — adding, scaling, computing lengths, computing angles — are all defined algebraically and continue to make sense.

When we say "an email is a 5,000-dimensional vector," we mean: it is an ordered list of 5,000 numbers, one per word in the vocabulary. We can no longer visualize it. We can absolutely still compute with it, and the *geometric language* — "the angle between two emails", "the length of an email vector", "the projection of one email onto another" — continues to apply unchanged. That is the gift of linear algebra: the 2D pictures we drew above survive into arbitrary dimensions.

### 11.2.2 Vectors as ordered lists, formally

So algebraically, a vector in $n$ dimensions is

$$
\mathbf{v} = (v_1, v_2, \ldots, v_n) \quad \text{or, as a column,} \quad \mathbf{v} = \begin{pmatrix} v_1 \\ v_2 \\ \vdots \\ v_n \end{pmatrix}.
$$

Whether we write it as a row or as a column will matter once we start multiplying by matrices. The default in mathematics, and the default in this book, is the *column* form. A row vector is the transpose of a column vector, written $\mathbf{v}^T$.

The set of all $n$-dimensional vectors with real-number entries is called $\mathbb{R}^n$. So $\mathbb{R}^2$ is the plane, $\mathbb{R}^3$ is everyday three-dimensional space, $\mathbb{R}^{5000}$ is the bag-of-words feature space from Chapter 3.

---

## 11.3 Adding and scaling — the two fundamental operations

A vector space is essentially a collection of vectors closed under two operations: adding two vectors and scaling a vector by a number. Everything else — angles, projections, decompositions — is built on top of these.

### 11.3.1 Vector addition

Given $\mathbf{a} = (a_1, \ldots, a_n)$ and $\mathbf{b} = (b_1, \ldots, b_n)$, their sum is

$$
\mathbf{a} + \mathbf{b} = (a_1 + b_1,\ a_2 + b_2,\ \ldots,\ a_n + b_n).
$$

Componentwise. That is the algebra. What does it look like?

In 2D, the geometric picture is the **parallelogram rule**. Draw $\mathbf{a}$ as an arrow from the origin. Draw $\mathbf{b}$ as an arrow from the origin. Now slide a copy of $\mathbf{b}$ so its tail sits at the head of $\mathbf{a}$. The arrow from the origin to the head of that slid-copy is $\mathbf{a} + \mathbf{b}$.

```
            y
          5 ┤             . →
            │           .   →
          4 ┤         .       →  a + b = (4, 5)
            │       .          ●
          3 ┤    b .         /↑
            │    .         /  │ slid-b
          2 ┤  ●        /     │
            │ /│      /
          1 ┤/ │   a/
            │  │ /
          0 ┼──●─────────── x
            O      a=(3,1)
```

Here $\mathbf{a} = (3, 1)$, $\mathbf{b} = (1, 2)$, and $\mathbf{a} + \mathbf{b} = (4, 3)$. (The diagram is approximate.) The diagonal of the parallelogram you've drawn is the sum. Equivalently, by the algebra: $3 + 1 = 4$, $1 + 2 = 3$. Same answer two ways.

This parallelogram picture transfers, *unchanged*, to higher dimensions. In 5,000-dimensional bag-of-words space, the sum of an email with vocabulary $\{$"meeting": 2, "tomorrow": 1$\}$ and an email with vocabulary $\{$"meeting": 1, "agenda": 3$\}$ is a new "vector" with $\{$"meeting": 3, "tomorrow": 1, "agenda": 3$\}$ — added componentwise. You cannot draw the parallelogram in 5,000 dimensions, but the *rule* still applies.

### 11.3.2 Scalar multiplication (scaling)

Given a vector $\mathbf{v}$ and a scalar (a single real number) $c$, the scaled vector is

$$
c \mathbf{v} = (c v_1,\ c v_2,\ \ldots,\ c v_n).
$$

Multiply every component by $c$. Geometrically in 2D: if $c > 1$, the vector gets longer in the same direction. If $0 < c < 1$, shorter. If $c = 0$, you get the zero vector. If $c < 0$, the vector flips direction *and* scales by $|c|$.

```
        c=2: ───────► (longer same direction)
        c=1: ───►
        c=0.5: ─►
        c=0:  (just the origin)
        c=-1: ◄───
        c=-2: ◄─────── (longer opposite direction)
```

Note that scaling never *rotates* the vector — it only stretches, shrinks, or flips. To rotate, you need a matrix; we will get there in section 11.6.

### 11.3.3 Combining the two — linear combinations

If you can add vectors and scale them, you can build any **linear combination**: pick scalars $c_1, c_2, \ldots, c_k$ and vectors $\mathbf{v}_1, \mathbf{v}_2, \ldots, \mathbf{v}_k$, and form

$$
c_1 \mathbf{v}_1 + c_2 \mathbf{v}_2 + \cdots + c_k \mathbf{v}_k.
$$

The set of all linear combinations of a fixed set of vectors is called their **span**. The span of one nonzero vector in $\mathbb{R}^2$ is the line through the origin in the vector's direction. The span of two non-parallel vectors in $\mathbb{R}^2$ is all of $\mathbb{R}^2$. The span of three vectors in $\mathbb{R}^3$ is either a plane (if they're coplanar) or all of $\mathbb{R}^3$ (if they're not).

This concept of "span" is going to return when we discuss feature dependence, rank of a matrix, and PCA. Hold onto it.

---

## 11.4 Norms — measuring length

The **length** of a vector — also called its **norm** or **magnitude** — is a single non-negative number that summarises "how big" the vector is. There are several different norms in common use, and which one you pick depends on what you're doing.

### 11.4.1 The Euclidean norm (L2)

The default norm, the one that matches everyday intuition about distance, is the **Euclidean norm**, also called the **L2 norm**:

$$
\|\mathbf{v}\|_2 = \sqrt{v_1^2 + v_2^2 + \cdots + v_n^2}.
$$

For $\mathbf{v} = (3, 4)$ in 2D, $\|\mathbf{v}\|_2 = \sqrt{9 + 16} = \sqrt{25} = 5$. This is exactly the Pythagorean theorem applied to the right triangle with legs 3 and 4 and hypotenuse 5.

In 3D, $\|\mathbf{v}\|_2 = \sqrt{v_1^2 + v_2^2 + v_3^2}$ — Pythagoras applied twice. In $n$ dimensions, the formula extends by analogy. It is still "length" in every geometric sense we care about: if you took a tape measure and stretched it from the origin to the point $\mathbf{v}$, the tape would read $\|\mathbf{v}\|_2$.

### 11.4.2 The Manhattan norm (L1)

The **Manhattan norm**, or **L1 norm**, sums absolute values instead of squaring:

$$
\|\mathbf{v}\|_1 = |v_1| + |v_2| + \cdots + |v_n|.
$$

For $\mathbf{v} = (3, 4)$, $\|\mathbf{v}\|_1 = 3 + 4 = 7$. The name comes from a stylised Manhattan, where you cannot walk diagonally through buildings — you walk along the grid. To go from $(0,0)$ to $(3,4)$ you walk 3 blocks east and then 4 blocks north, total 7 blocks. The L2 norm asks "as the crow flies"; L1 asks "as the taxi drives."

L1 is going to show up again, decisively, when we discuss **lasso regularization** in Chapter 20. The L1 penalty has the remarkable property of driving some coefficients to *exactly* zero, performing implicit feature selection. That geometric story rests on the unit ball of L1 (a diamond, sharp at the axes) versus the unit ball of L2 (a circle, smooth everywhere). We will draw that picture when we need it.

### 11.4.3 The supremum norm (L∞)

The **L∞ norm** (also called the **max norm**, **Chebyshev norm**, or **supremum norm**) is

$$
\|\mathbf{v}\|_\infty = \max_i |v_i|.
$$

The largest component, in absolute value. For $\mathbf{v} = (3, 4)$, $\|\mathbf{v}\|_\infty = 4$. It is the "worst-case" norm — the biggest single deviation matters, the others don't.

These three — L1, L2, L∞ — are the three most common members of a family called the **p-norms**, $\|\mathbf{v}\|_p = (\sum |v_i|^p)^{1/p}$. As $p \to \infty$, the formula tends to the max. As $p \to 1$ from above, we get L1. At $p = 2$ we get Euclidean.

### 11.4.4 What "distance" means between vectors

Given two vectors $\mathbf{a}$ and $\mathbf{b}$, the **distance** between them is the norm of their difference:

$$
d(\mathbf{a}, \mathbf{b}) = \|\mathbf{a} - \mathbf{b}\|.
$$

(Whichever norm you've chosen.) The point is: distance between two points is just a length applied to the connecting arrow. Two emails are "close" if the vector pointing from one to the other is short.

This will return in Chapter 38 when we discuss k-means clustering — k-means assigns each point to the *nearest* cluster center, and "nearest" is virtually always L2 distance. But you should know that L1 (Manhattan distance) and other norms produce different clusterings, sometimes with very different operational properties.

### 11.4.5 Unit vectors

A vector with length $1$ is a **unit vector**. Any nonzero vector $\mathbf{v}$ can be *normalized* to a unit vector by dividing by its length:

$$
\hat{\mathbf{v}} = \frac{\mathbf{v}}{\|\mathbf{v}\|_2}.
$$

The result has length $1$ and points in the same direction as $\mathbf{v}$. Unit vectors are how we strip a vector down to "pure direction" with the magnitude removed. They show up everywhere — in defining angles, in expressing rotations, in machine learning whenever we care about direction more than magnitude (cosine similarity, normalized embeddings).

---

## 11.5 What a matrix is — four views, all useful

So far we have only had vectors. A **matrix** is, on its face, a rectangular grid of numbers:

$$
A = \begin{pmatrix} 1 & 2 & 3 \\ 4 & 5 & 6 \end{pmatrix}.
$$

This $A$ has $2$ rows and $3$ columns; we call it a $2 \times 3$ matrix. In general an $m \times n$ matrix has $m$ rows and $n$ columns. The entry in row $i$, column $j$ is written $A_{ij}$ or $a_{ij}$. Indexing in math is usually 1-based; in NumPy it's 0-based; we will gently adjust between the two without making a fuss.

A grid of numbers is a perfectly correct *first* view of a matrix. But it is also the least useful view for understanding what matrices *do*. There are at least four views, and you should mentally toggle between them depending on what you're doing.

### 11.5.1 View 1: a 2D array of numbers

This is the obvious view. A matrix is data, in a table. The entry $A_{ij}$ is the number stored at row $i$, column $j$. Spreadsheets are matrices. A pixel image (height by width, grayscale) is a matrix. A bag-of-words feature matrix — one row per email, one column per vocabulary word — is a matrix.

This view is the right one when you're *manipulating* the matrix as data: indexing it, slicing it, filtering rows, computing summary statistics column by column.

### 11.5.2 View 2: a linear function from $\mathbb{R}^n$ to $\mathbb{R}^m$

Here is the view that unlocks everything else in linear algebra. An $m \times n$ matrix $A$ defines a function

$$
T_A : \mathbb{R}^n \to \mathbb{R}^m, \qquad T_A(\mathbf{x}) = A\mathbf{x}.
$$

It takes in an $n$-dimensional vector and produces an $m$-dimensional vector. The function it represents has a very specific property: it is **linear**, which means

$$
T_A(\mathbf{x} + \mathbf{y}) = T_A(\mathbf{x}) + T_A(\mathbf{y}) \qquad \text{and} \qquad T_A(c\mathbf{x}) = c\, T_A(\mathbf{x}).
$$

Linear functions preserve vector addition and scalar multiplication. Equivalently: linear functions take straight lines through the origin to straight lines through the origin (possibly squashed to a single point), and they take the origin to the origin.

It turns out — this is a non-obvious theorem of linear algebra — that *every* linear function from $\mathbb{R}^n$ to $\mathbb{R}^m$ is given by multiplication by some $m \times n$ matrix. So matrices and linear functions are in one-to-one correspondence. The grid of numbers is just a compact way to write down a linear function.

This is the view that makes matrix multiplication mean something. We will get to it in Chapter 13.

### 11.5.3 View 3: a collection of column vectors

You can read an $m \times n$ matrix as a *list of $n$ column vectors*, each of length $m$. The matrix

$$
A = \begin{pmatrix} 1 & 2 & 3 \\ 4 & 5 & 6 \end{pmatrix}
$$

is "really" three columns: $\mathbf{a}_1 = (1, 4)$, $\mathbf{a}_2 = (2, 5)$, $\mathbf{a}_3 = (3, 6)$, stacked side by side.

This view is the right one when you're thinking about the matrix as the *output* of a linear function. The product $A\mathbf{x}$ turns out (we'll show this in Chapter 13) to be exactly $x_1 \mathbf{a}_1 + x_2 \mathbf{a}_2 + x_3 \mathbf{a}_3$ — a linear combination of the columns, with coefficients given by $\mathbf{x}$. The set of all things you can produce by varying $\mathbf{x}$ is exactly the span of the columns — the **column space** of $A$.

### 11.5.4 View 4: a collection of row vectors

You can also read $A$ as a list of $m$ row vectors. For our $A$ above, that's two rows: $\mathbf{r}_1 = (1, 2, 3)$ and $\mathbf{r}_2 = (4, 5, 6)$.

This view is useful when each row represents one *data example* and each column represents one *feature*. In Chapter 3 our spam email feature matrix had one row per email. When you do `X.mean(axis=0)` in NumPy to get the mean feature vector, you're collapsing rows by column — taking advantage of the row view. When you do `X.mean(axis=1)` to get one mean per row, you're taking advantage of the column view.

The reason there are four views and not one is that all four are *correct simultaneously* and each one's intuition is sharpest for different problems. A working ML practitioner toggles between them constantly.

---

## 11.6 A 2x2 matrix as a function of the plane

Let's make View 2 concrete. Consider the simplest non-trivial example:

$$
A = \begin{pmatrix} 2 & 0 \\ 0 & 3 \end{pmatrix}.
$$

This is a $2 \times 2$ matrix. It is the matrix of a linear function $\mathbb{R}^2 \to \mathbb{R}^2$. What does that function *do*?

Multiplying by $A$: take any $\mathbf{x} = (x_1, x_2)$ and produce

$$
A\mathbf{x} = \begin{pmatrix} 2 & 0 \\ 0 & 3 \end{pmatrix} \begin{pmatrix} x_1 \\ x_2 \end{pmatrix} = \begin{pmatrix} 2 x_1 \\ 3 x_2 \end{pmatrix}.
$$

(We'll formalise matrix-times-vector in Chapter 13; for now take this on faith, it's the "row times column" rule applied twice.) The function scales the first coordinate by $2$ and the second by $3$. Geometrically: it stretches the plane horizontally by a factor of $2$ and vertically by a factor of $3$.

A vivid way to see this: take the **unit square** with corners at $(0,0)$, $(1,0)$, $(1,1)$, $(0,1)$, and ask "where does $A$ send these corners?"

- $(0, 0) \mapsto (0, 0)$. The origin stays put — always true for linear functions.
- $(1, 0) \mapsto (2, 0)$. The east corner stretches twice as far east.
- $(1, 1) \mapsto (2, 3)$. The northeast corner stretches both ways.
- $(0, 1) \mapsto (0, 3)$. The north corner stretches three times as far north.

```
Before A:                After A:

       y                       y
     1 ┼───┐                3 ┼───────┐
       │   │                  │       │
       │   │                  │       │
       │   │                2 ┤       │
       │   │                  │       │
       │   │                  │       │
     0 ┴───┴── x            1 ┤       │
       0   1                  │       │
                              │       │
                            0 ┴───────┴── x
                              0       2
```

Same shape (rectangle), different dimensions. $A$ takes the unit square to a $2 \times 3$ rectangle.

Now try a different matrix:

$$
A = \begin{pmatrix} 0 & -1 \\ 1 & \phantom{-}0 \end{pmatrix}.
$$

Apply to the corners:

- $(0, 0) \mapsto (0, 0)$.
- $(1, 0) \mapsto (0, 1)$. The east corner goes to the north.
- $(1, 1) \mapsto (-1, 1)$. The northeast corner goes to the northwest.
- $(0, 1) \mapsto (-1, 0)$. The north corner goes to the west.

This is a **90-degree rotation counterclockwise**. The unit square is rotated, not stretched. Same shape, same area, different orientation.

A third example, the **shear**:

$$
A = \begin{pmatrix} 1 & 1 \\ 0 & 1 \end{pmatrix}.
$$

- $(0, 0) \mapsto (0, 0)$.
- $(1, 0) \mapsto (1, 0)$. East corner unmoved.
- $(1, 1) \mapsto (2, 1)$. Northeast corner pushed right.
- $(0, 1) \mapsto (1, 1)$. North corner pushed right.

```
Before:           After (shear):

   1 ┼───┐         1 ┤   ┌───┐
     │   │           │  /   /
     │   │           │ /   /
   0 ┴───┴── x     0 ┴/───/── x
     0   1           0    2
```

The square has become a parallelogram, slanted to the right. This is exactly what happens when you shove the top of a stack of paper sideways — pages stay parallel, but the stack leans.

The last basic example, **projection** onto the x-axis:

$$
A = \begin{pmatrix} 1 & 0 \\ 0 & 0 \end{pmatrix}.
$$

- $(0, 0) \mapsto (0, 0)$.
- $(1, 0) \mapsto (1, 0)$.
- $(1, 1) \mapsto (1, 0)$.
- $(0, 1) \mapsto (0, 0)$.

The whole plane gets *collapsed* onto the x-axis. This is a projection — it loses information. Two different inputs $(1, 1)$ and $(1, 0)$ map to the same output $(1, 0)$. The function is no longer invertible. We will see in Chapter 13 that this collapse is exactly what the determinant detects.

### 11.6.1 Why this matters

These four examples — scale, rotate, shear, project — are the building blocks of *every* linear transformation. Every $2 \times 2$ matrix can be decomposed, via the singular value decomposition (Chapter 14), into a rotation, a scaling along axes, and another rotation. So in some sense, "matrix = rotate, then stretch, then rotate" is the complete story for what any linear function does.

When we get to Chapter 14 and discuss eigenvectors — vectors that a matrix only *stretches* without rotating — you will see exactly which directions in the plane "feel" the matrix as a pure scaling rather than as a rotation plus a scaling. That picture is what makes PCA work.

---

## 11.7 Special matrices to recognise

Three special matrices will appear so often it pays to name them now.

### 11.7.1 The zero matrix

All entries are zero. The function it represents collapses everything to the origin: $\mathbf{0} \cdot \mathbf{x} = \mathbf{0}$ for any $\mathbf{x}$. Geometrically it crushes the entire input space to a single point. Algebraically it is the "additive identity" — adding it to any matrix leaves the matrix unchanged.

### 11.7.2 The identity matrix

The $n \times n$ identity matrix, written $I_n$ or just $I$, has 1's on the diagonal and 0's everywhere else. For $n = 3$:

$$
I_3 = \begin{pmatrix} 1 & 0 & 0 \\ 0 & 1 & 0 \\ 0 & 0 & 1 \end{pmatrix}.
$$

It represents the *identity function*: $I \mathbf{x} = \mathbf{x}$ for every $\mathbf{x}$. It is the "multiplicative identity" for matrices — $IA = AI = A$ for any matrix $A$ of compatible size.

The identity will show up the moment we discuss matrix inverses (Chapter 13). $A^{-1}$ is the matrix that, multiplied by $A$, gives $I$ — the inverse "undoes" what $A$ does.

### 11.7.3 The diagonal matrix

A matrix with zeros everywhere except possibly on the diagonal:

$$
D = \begin{pmatrix} d_1 & 0 & 0 \\ 0 & d_2 & 0 \\ 0 & 0 & d_3 \end{pmatrix}.
$$

The function it represents scales coordinate $i$ by $d_i$. Easy to think about, easy to compute with, and the goal of *diagonalization* (Chapter 14) is to find a coordinate system in which a given matrix *becomes* diagonal — once you've done that, you've reduced the matrix to a set of independent one-dimensional scalings.

---

## 11.8 Code, last

Now that we know what we mean, the NumPy is easy.

```python
import numpy as np

# A vector in R^5 — note: 1D arrays in NumPy represent column vectors
# implicitly; transpose is a no-op on 1D arrays.
v = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
print(v.shape)          # (5,)

# A matrix — 2x3, exactly the A from section 11.5.
A = np.array([[1.0, 2.0, 3.0],
              [4.0, 5.0, 6.0]])
print(A.shape)          # (2, 3)

# Vector addition and scaling
a = np.array([3.0, 1.0])
b = np.array([1.0, 2.0])
print(a + b)            # [4. 3.]
print(2 * a)            # [6. 2.]

# Norms — L2, L1, L-infinity
v = np.array([3.0, 4.0])
print(np.linalg.norm(v))          # 5.0   (L2 — the default)
print(np.linalg.norm(v, ord=1))   # 7.0   (L1)
print(np.linalg.norm(v, ord=np.inf))  # 4.0  (L-infinity)

# Distance between two points
a = np.array([1.0, 2.0])
b = np.array([4.0, 6.0])
print(np.linalg.norm(a - b))      # 5.0

# Normalize a vector to unit length
v = np.array([3.0, 4.0])
v_hat = v / np.linalg.norm(v)
print(v_hat)                       # [0.6, 0.8]
print(np.linalg.norm(v_hat))       # 1.0

# Matrix-vector product (preview of Chapter 13)
A_scale = np.array([[2.0, 0.0],
                    [0.0, 3.0]])
x = np.array([1.0, 1.0])
print(A_scale @ x)                # [2., 3.]  — corners of the stretched square
```

Three things to internalise from this snippet. First, NumPy's `@` operator (or equivalently `np.dot`, or `np.matmul`) is the matrix product. It is *not* `*` — `*` is *elementwise* multiplication, which is something different and a frequent bug source. Second, NumPy distinguishes between 1D arrays (shape `(n,)`) and 2D arrays (shape `(n, 1)` for column vectors, `(1, n)` for row vectors). They mostly interoperate but occasionally bite. Third, `np.linalg.norm` defaults to L2 — when you want anything else, pass `ord=`.

We are deliberately not using fancier NumPy in this chapter. The code is here to make the math executable, not to be impressive.

---

## 11.9 Edge cases and engineering tradeoffs

A few practical notes that will save you debugging time:

**The zero vector has no direction.** When you normalize, dividing by the norm, you must guard against `v / 0`. In code this gives a NaN; in math we just exclude the zero vector from any normalized statement.

**Numerical precision.** $\|\mathbf{v}\|_2 = \sqrt{\sum v_i^2}$ involves squaring. For very large $v_i$, squaring can overflow; for very small $v_i$, squaring can underflow. Production libraries use numerically careful implementations that scale before squaring. You won't notice the difference for the vectors in this book, but you should know it exists.

**Sparse vectors.** A "5000-dimensional vector" full of zeros except for a few entries is a sparse vector. Storing it as a dense array wastes memory and CPU. Production ML code uses sparse representations (`scipy.sparse`, Spark `SparseVector`) for the high-dimensional, mostly-zero feature vectors that arise in NLP and recommender systems. The math is identical; only the storage and the multiplication routines differ.

**The "vector in 5000 dimensions" mental model.** Resist the urge to picture this. You will fail. Instead, picture the 2D or 3D case and *trust* that the same operations apply. The algebra is the algebra. The 2D drawing is a crutch, not a definition.

---

## 11.10 What this builds on / where this returns

**Builds on:** Just basic algebra and the Cartesian coordinate system. This is the foundational chapter for all of Part C.

**Returns:**

- **Norms** return in Chapter 20 (regularization geometry — L1 ball vs L2 ball) and in Chapter 38 (k-means uses L2 distance).
- **The four views of a matrix** return in *every chapter from here on*. Chapter 12 leans on the column view to derive the dot product. Chapter 13 leans on the linear-function view to derive matrix multiplication. Chapter 14 leans on the column view to derive eigendecomposition.
- **Linear combinations** and **span** return in Chapter 13 (column space, rank) and Chapter 14 (eigenvectors as the directions of "pure scaling").
- **The unit-square transformation picture** returns in Chapter 13 (determinant = signed area scaling) and Chapter 14 (eigenvectors are the directions whose square gets stretched but not rotated).

---

## 11.11 Exercises

Do these cold. The answers are folded below.

1. **The two views of a vector.** Sketch the vector $(2, 3)$ as (a) a point and (b) an arrow. In your own words, write a one-sentence description of when each view is the more useful one.

2. **Componentwise arithmetic.** Compute $\mathbf{a} + \mathbf{b}$ and $3\mathbf{a} - 2\mathbf{b}$ for $\mathbf{a} = (1, 2, 3)$, $\mathbf{b} = (4, 0, -1)$.

3. **Norms by hand.** Compute the L1, L2, and L∞ norms of $\mathbf{v} = (1, -2, 3, -4)$.

4. **Distance.** Compute the L2 distance between $(1, 2, 3)$ and $(4, 6, 3)$. Then compute their L1 distance. Why are they different?

5. **Normalize.** Normalize $(6, 8)$ to a unit vector under the L2 norm. Verify its length is $1$.

6. **Linear combination as span.** Is $(5, 7)$ in the span of $(1, 1)$ and $(1, 2)$? Find the coefficients $c_1, c_2$ such that $c_1 (1,1) + c_2 (1, 2) = (5, 7)$.

7. **Span dimension.** What is the span of the single vector $(1, 2, 3)$? What is the span of the two vectors $(1, 0, 0)$ and $(0, 1, 0)$? What is the span of $(1, 0, 0)$ and $(2, 0, 0)$? Be precise about what *geometric object* each span is.

8. **2x2 matrix as function.** For $A = \begin{pmatrix} 1 & 0 \\ 0 & -1 \end{pmatrix}$, compute the images of the four unit-square corners. What geometric operation does $A$ represent?

9. **A bigger stretch.** For $A = \begin{pmatrix} 3 & 0 \\ 0 & 0.5 \end{pmatrix}$, what does $A$ do to the unit square? Sketch the result.

10. **A combined transformation.** Consider $A = \begin{pmatrix} 0 & 1 \\ -1 & 0 \end{pmatrix}$. Apply it to $(1, 0)$, $(0, 1)$, $(1, 1)$. What geometric operation is this?

11. **The identity in action.** Multiply $I_3 \mathbf{v}$ where $\mathbf{v} = (5, -2, 7)$. Show every step.

12. **A high-dimensional intuition check.** Two emails $\mathbf{e}_1$ and $\mathbf{e}_2$ in $\mathbb{R}^{5000}$ each have non-zero entries only at positions corresponding to words that appear in them. $\mathbf{e}_1$ has 30 non-zero entries; $\mathbf{e}_2$ has 50 non-zero entries; they share 10 words in common. Without writing out 5000 numbers, what is the maximum possible number of non-zero entries in $\mathbf{e}_1 + \mathbf{e}_2$? In $\mathbf{e}_1 - \mathbf{e}_2$?

<details>
<summary>Answers</summary>

1. Point view: useful when each vector is a "data point" and you're examining their locations relative to each other. Arrow view: useful when adding or scaling vectors, where the geometric picture (parallelogram, stretching) is informative.

2. $\mathbf{a} + \mathbf{b} = (5, 2, 2)$. $3\mathbf{a} - 2\mathbf{b} = (3 - 8, 6 - 0, 9 - (-2)) = (-5, 6, 11)$.

3. L1: $1 + 2 + 3 + 4 = 10$. L2: $\sqrt{1 + 4 + 9 + 16} = \sqrt{30} \approx 5.477$. L∞: $\max(1, 2, 3, 4) = 4$.

4. L2: difference $= (-3, -4, 0)$; norm $= \sqrt{9 + 16 + 0} = 5$. L1: $3 + 4 + 0 = 7$. Different because L2 measures "as the crow flies" via the Pythagorean theorem, while L1 sums absolute component-wise distances.

5. $\|(6, 8)\|_2 = \sqrt{36 + 64} = \sqrt{100} = 10$. So $\hat{\mathbf{v}} = (0.6, 0.8)$. Verification: $\sqrt{0.36 + 0.64} = \sqrt{1} = 1$.

6. Set up $c_1 + c_2 = 5$ and $c_1 + 2 c_2 = 7$. Subtract: $c_2 = 2$. Then $c_1 = 3$. So $(5, 7) = 3(1, 1) + 2(1, 2)$. Yes, it is in the span.

7. Span of $(1, 2, 3)$: a *line* through the origin in $\mathbb{R}^3$, in the direction of that vector. Span of $(1, 0, 0)$ and $(0, 1, 0)$: a *plane* through the origin in $\mathbb{R}^3$ — specifically, the xy-plane. Span of $(1, 0, 0)$ and $(2, 0, 0)$: a *line* (the x-axis), because $(2, 0, 0)$ is just a scaled copy of $(1, 0, 0)$ — they are linearly dependent and only span what one of them spans.

8. $(0, 0) \mapsto (0, 0)$. $(1, 0) \mapsto (1, 0)$. $(1, 1) \mapsto (1, -1)$. $(0, 1) \mapsto (0, -1)$. The matrix flips the plane vertically — reflection across the x-axis.

9. The unit square becomes a rectangle $3$ wide and $0.5$ tall. Stretched horizontally by 3, squashed vertically to half.

10. $(1, 0) \mapsto (0, -1)$. $(0, 1) \mapsto (1, 0)$. $(1, 1) \mapsto (1, -1)$. This is a 90-degree rotation *clockwise* (compare to the counterclockwise version in section 11.6).

11. $I_3 \mathbf{v} = (1 \cdot 5 + 0 \cdot (-2) + 0 \cdot 7,\ 0 \cdot 5 + 1 \cdot (-2) + 0 \cdot 7,\ 0 \cdot 5 + 0 \cdot (-2) + 1 \cdot 7) = (5, -2, 7) = \mathbf{v}$.

12. $\mathbf{e}_1$ has support of size 30, $\mathbf{e}_2$ size 50, overlap 10. The union of the supports has size $30 + 50 - 10 = 70$. Both $\mathbf{e}_1 + \mathbf{e}_2$ and $\mathbf{e}_1 - \mathbf{e}_2$ have non-zero entries at most on the union — so at most $70$. (For the sum, the entries in the overlap could in principle cancel only if components had opposite signs — for word counts, they don't, so the sum has exactly 70 non-zeros. For the difference, the overlap entries could cancel exactly if equal, dropping the count below 70.)

</details>
