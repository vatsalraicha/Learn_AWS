# Chapter 13 — Matrix Multiplication, Inverse, Determinant

> **Goal of this chapter:** to build matrix multiplication, the inverse, and the determinant from the ground up — not as formulas to memorise, but as operations with concrete geometric meaning. When you call `model.fit(X, y)` on a linear regression in Spark or scikit-learn, the math underneath computes $(X^T X)^{-1} X^T \mathbf{y}$. Every piece of that expression is in this chapter: the matrix product $X^T X$, the inverse $(\cdot)^{-1}$, and the matrix-vector multiplication $X^T \mathbf{y}$. By the end of this chapter, the **normal equation** (which we'll derive in full in Chapter 31) will be readable. Until then, it would be hieroglyphic. We're going to fix that now.

---

## 13.1 Why we cannot skip matrix multiplication

It is tempting to treat matrix multiplication as the kind of thing the numerical library handles. You write `A @ B` in NumPy; a number comes out; what's the difficulty?

The difficulty is that when training fails or when the math goes sideways, you need to know what $A \mathbf{x}$ *means* to diagnose it. The most common bugs in linear-algebraic ML code are shape mismatches and silently transposed matrices — and the only fix is to understand what each axis of each matrix represents and what the product is computing semantically. Matrix multiplication is not the kind of operation you can use without understanding; it punishes you immediately if you try.

We will derive the rule from two starting points — the row-times-column formula and the composition-of-linear-maps view — and show why they agree. Both views are useful in different contexts; both will return repeatedly throughout the rest of this book.

---

## 13.2 Matrix times vector — the warm-up

Before matrix-times-matrix, we need matrix-times-vector. We sketched this in Chapter 11 — let's pin it down.

An $m \times n$ matrix $A$ defines a linear function $\mathbb{R}^n \to \mathbb{R}^m$. Given $\mathbf{x} \in \mathbb{R}^n$, the product $A \mathbf{x}$ is an element of $\mathbb{R}^m$, computed as follows.

**The row-times-column rule.** Each entry of $A\mathbf{x}$ is the dot product of the corresponding row of $A$ with $\mathbf{x}$. Specifically,

$$
(A\mathbf{x})_i \;=\; \sum_{j=1}^{n} A_{ij}\, x_j \;=\; (\text{row } i \text{ of } A) \cdot \mathbf{x}.
$$

You produce $m$ numbers (one per row of $A$), each one a dot product. Each requires $n$ multiplications and additions, so the total cost is $O(mn)$.

**The linear-combination-of-columns rule.** Equivalently, $A\mathbf{x}$ is a *linear combination of the columns of $A$*, with coefficients given by the entries of $\mathbf{x}$:

$$
A \mathbf{x} \;=\; x_1 \mathbf{a}_1 + x_2 \mathbf{a}_2 + \cdots + x_n \mathbf{a}_n,
$$

where $\mathbf{a}_j$ is the $j$-th column of $A$.

These two views are *the same thing computed in different orders*. The row view: pull a row, dot it with $\mathbf{x}$. The column view: scale each column by the matching entry of $\mathbf{x}$ and sum them. Both produce the same result. You should switch between them based on which one's intuition is clearer for a given problem.

### 13.2.1 Worked example

Let

$$
A = \begin{pmatrix} 1 & 2 & 3 \\ 4 & 5 & 6 \end{pmatrix}, \qquad \mathbf{x} = (1, 0, 2).
$$

**Row view.** First row dotted with $\mathbf{x}$: $1 \cdot 1 + 2 \cdot 0 + 3 \cdot 2 = 1 + 0 + 6 = 7$. Second row dotted with $\mathbf{x}$: $4 \cdot 1 + 5 \cdot 0 + 6 \cdot 2 = 4 + 0 + 12 = 16$. So $A\mathbf{x} = (7, 16)$.

**Column view.** $1 \cdot (1, 4) + 0 \cdot (2, 5) + 2 \cdot (3, 6) = (1, 4) + (0, 0) + (6, 12) = (7, 16)$.

Same answer, both ways. The column view makes especially clear what $A\mathbf{x}$ *can be* — it lives in the span of the columns of $A$. This set is called the **column space** of $A$. We'll come back to it.

---

## 13.3 Matrix times matrix — composition of linear maps

Now to the main event. Why does matrix multiplication have its (initially mysterious) row-times-column shape?

Here is the clean derivation. Let $A$ be an $m \times k$ matrix (so $A$ is a linear map $\mathbb{R}^k \to \mathbb{R}^m$). Let $B$ be a $k \times n$ matrix ($\mathbb{R}^n \to \mathbb{R}^k$). The **composition** $A \circ B$ is the function $\mathbb{R}^n \to \mathbb{R}^m$ defined by

$$
(A \circ B)(\mathbf{x}) = A(B \mathbf{x}).
$$

First apply $B$, then apply $A$. Composition of linear maps is itself a linear map (easy to verify from linearity properties). So by the theorem from Chapter 11 (every linear map $\mathbb{R}^n \to \mathbb{R}^m$ is given by an $m \times n$ matrix), there exists *some* $m \times n$ matrix $C$ such that $C \mathbf{x} = A(B \mathbf{x})$ for every $\mathbf{x}$. We *define* the matrix product $AB$ to be exactly this $C$.

So matrix multiplication is, definitionally, the matrix whose action is "first do $B$, then do $A$." We now need to work out what its entries are.

The trick: apply both sides to each standard basis vector $\mathbf{e}_j$ (the vector with $1$ in position $j$ and $0$ elsewhere). The product $C \mathbf{e}_j$ is, by the column view, just the $j$-th column of $C$. And $A(B \mathbf{e}_j)$ is $A$ applied to the $j$-th column of $B$. So:

$$
\text{column } j \text{ of } C \;=\; A \cdot (\text{column } j \text{ of } B).
$$

Each column of $C$ is $A$ times the corresponding column of $B$. To compute entry $(i, j)$ of $C$: take the $i$-th row of $A$, dotted with the $j$-th column of $B$:

$$
\boxed{(AB)_{ij} \;=\; \sum_{\ell=1}^{k} A_{i\ell}\, B_{\ell j}.}
$$

That is the row-times-column formula, derived from the composition view. Note the indexing: the *inner* dimension of $A$ (its column count, $k$) must equal the *outer* dimension of $B$ on the left (its row count, $k$). The result is shaped by the *outer* dimensions: $m$ rows and $n$ columns.

Shape arithmetic: $(m \times k)(k \times n) = (m \times n)$. If the inner $k$'s don't match, the product is undefined.

### 13.3.1 Worked numerical example

Multiply a $2 \times 3$ matrix by a $3 \times 2$ matrix:

$$
A = \begin{pmatrix} 1 & 2 & 3 \\ 4 & 5 & 6 \end{pmatrix}, \qquad B = \begin{pmatrix} 7 & 8 \\ 9 & 10 \\ 11 & 12 \end{pmatrix}.
$$

The result will be $2 \times 2$. Compute each entry by row-of-$A$ dot column-of-$B$.

$(AB)_{11}$ = row 1 of $A$ $\cdot$ column 1 of $B$ = $1 \cdot 7 + 2 \cdot 9 + 3 \cdot 11 = 7 + 18 + 33 = 58$.

$(AB)_{12}$ = row 1 of $A$ $\cdot$ column 2 of $B$ = $1 \cdot 8 + 2 \cdot 10 + 3 \cdot 12 = 8 + 20 + 36 = 64$.

$(AB)_{21}$ = row 2 of $A$ $\cdot$ column 1 of $B$ = $4 \cdot 7 + 5 \cdot 9 + 6 \cdot 11 = 28 + 45 + 66 = 139$.

$(AB)_{22}$ = row 2 of $A$ $\cdot$ column 2 of $B$ = $4 \cdot 8 + 5 \cdot 10 + 6 \cdot 12 = 32 + 50 + 72 = 154$.

$$
AB = \begin{pmatrix} 58 & 64 \\ 139 & 154 \end{pmatrix}.
$$

Twelve multiplications, eight additions. For square $n \times n$ matrices the cost is $O(n^3)$ in the straightforward algorithm; the asymptotically best known algorithm is around $O(n^{2.37})$, but for any matrix you will encounter outside of theoretical computer science papers, $O(n^3)$ is the operational reality.

### 13.3.2 Three properties to nail down

**Associative:** $(AB)C = A(BC)$. Matrix multiplication is associative; you can parenthesise however you like. (This is what makes "compose three linear maps in either order of pairing" come out the same.)

**Distributive:** $A(B + C) = AB + AC$ and $(A + B)C = AC + BC$.

**Not commutative:** in general, $AB \neq BA$. This is the property that surprises students. Even for two $2 \times 2$ matrices, the order matters. Geometrically, this is obvious: rotating then stretching is not the same as stretching then rotating. (Try it with the rotation and scaling matrices from Chapter 11.) Algebraically, it is the single biggest pitfall when manipulating matrix expressions — you cannot just shuffle factors around as if you were doing regular numbers.

There is a special case where commutativity does hold: when both matrices are *diagonal*, or when one of them is the identity, or when they happen to share an eigenbasis. The last condition is deep and will return in Chapter 14.

---

## 13.4 The transpose

The **transpose** $A^T$ of an $m \times n$ matrix $A$ is the $n \times m$ matrix obtained by swapping rows and columns:

$$
(A^T)_{ij} = A_{ji}.
$$

For

$$
A = \begin{pmatrix} 1 & 2 & 3 \\ 4 & 5 & 6 \end{pmatrix}, \qquad A^T = \begin{pmatrix} 1 & 4 \\ 2 & 5 \\ 3 & 6 \end{pmatrix}.
$$

Two key identities:

- $(A^T)^T = A$ — transposing twice gets you back.
- $(AB)^T = B^T A^T$ — the transpose of a product is the product of the transposes, *in reverse order*. This is the identity that appears everywhere in linear-regression derivations.

The reversal in $(AB)^T = B^T A^T$ is a common bug source. The intuition: if $AB$ is "first do $B$, then $A$," then the transpose has to undo both in the right order. Algebraically it's a direct computation: $((AB)^T)_{ij} = (AB)_{ji} = \sum_\ell A_{j\ell} B_{\ell i} = \sum_\ell (A^T)_{\ell j} (B^T)_{i \ell} = \sum_\ell (B^T)_{i\ell} (A^T)_{\ell j} = (B^T A^T)_{ij}$.

A matrix is **symmetric** if $A = A^T$. Symmetric matrices have to be square. They show up everywhere in ML: covariance matrices, Gram matrices $X^T X$, the Hessian of a smooth scalar function. Symmetric matrices have very pleasant properties — real eigenvalues, orthogonal eigenvectors — which we'll exploit in Chapter 14.

---

## 13.5 The identity matrix and matrix inverse

The $n \times n$ identity matrix $I$ has 1's on the diagonal and 0's elsewhere. It satisfies $I A = A I = A$ for any compatible $A$. It is the multiplicative identity.

The **inverse** $A^{-1}$ of a square matrix $A$, when it exists, is the unique matrix such that

$$
A A^{-1} = A^{-1} A = I.
$$

Geometrically: if $A$ is a linear transformation, $A^{-1}$ is the linear transformation that *undoes* it. Apply $A$, then $A^{-1}$, and you're back where you started. Rotate 90° clockwise; rotate 90° counterclockwise; you've done nothing.

### 13.5.1 When does the inverse exist?

Not every matrix has an inverse. Three equivalent conditions for invertibility of a square $n \times n$ matrix $A$:

1. $A \mathbf{x} = \mathbf{0}$ implies $\mathbf{x} = \mathbf{0}$ — i.e., the only vector mapped to zero is zero itself.
2. The columns (equivalently, rows) of $A$ are **linearly independent** — no column can be written as a linear combination of the others.
3. $\det A \neq 0$.

A matrix that fails any of these is **singular** (non-invertible). We'll see in section 13.7 what the determinant detects.

If $A$ is invertible, the inverse is unique. The proof is short: suppose $B$ and $C$ both satisfy $AB = BA = I$ and $AC = CA = I$. Then $B = BI = B(AC) = (BA)C = IC = C$. Uniqueness follows from associativity.

### 13.5.2 Computing the inverse of a 2x2 matrix

There is a closed-form formula for the inverse of a $2 \times 2$ matrix:

$$
A = \begin{pmatrix} a & b \\ c & d \end{pmatrix}, \qquad A^{-1} = \frac{1}{ad - bc} \begin{pmatrix} d & -b \\ -c & a \end{pmatrix}.
$$

The quantity $ad - bc$ in the denominator is the **determinant** of $A$. If it's zero, the formula blows up — the matrix has no inverse.

**Why does this work?** Multiply it out:

$$
A \cdot \frac{1}{ad - bc} \begin{pmatrix} d & -b \\ -c & a \end{pmatrix} = \frac{1}{ad - bc} \begin{pmatrix} ad - bc & -ab + ab \\ cd - cd & -bc + ad \end{pmatrix} = \frac{1}{ad - bc} \begin{pmatrix} ad - bc & 0 \\ 0 & ad - bc \end{pmatrix} = I.
$$

Works on both sides. So the formula is correct.

For larger matrices the closed-form gets messy fast. The practical algorithm is **Gauss-Jordan elimination** or, in numerical libraries, **LU decomposition** — factor $A = LU$ where $L$ is lower triangular and $U$ is upper triangular, then solve $A \mathbf{x} = \mathbf{b}$ as two triangular systems. We won't derive these here; we mention them because that's what `numpy.linalg.solve` is doing under the hood.

### 13.5.3 An important warning about computing inverses in practice

In numerical ML code, you almost never *explicitly* compute $A^{-1}$. If you want to solve $A \mathbf{x} = \mathbf{b}$, you don't compute $\mathbf{x} = A^{-1} \mathbf{b}$. You call `np.linalg.solve(A, b)`, which does Gaussian elimination directly — faster and more numerically stable than forming the inverse and then multiplying.

Similarly, the normal equation $\hat{\mathbf{w}} = (X^T X)^{-1} X^T \mathbf{y}$ is taught as if you literally invert $X^T X$ and then multiply. In production, you solve the linear system $(X^T X) \hat{\mathbf{w}} = X^T \mathbf{y}$ via a numerically stable method (Cholesky, QR, or SVD). The notation pretends to invert; the implementation does something cleverer. We will revisit this in Chapter 31.

For now: $A^{-1}$ exists as a mathematical object; you reason about it abstractly. Whether you ever materialise it as numbers is a numerical engineering choice.

---

## 13.6 The determinant

We've already brushed against the determinant — it appears in the 2x2 inverse formula, and "$\det A \neq 0$" is the invertibility test. Let's now develop what it actually *is*.

### 13.6.1 The 2x2 determinant: signed area

For a $2 \times 2$ matrix $A = \begin{pmatrix} a & b \\ c & d \end{pmatrix}$, the determinant is

$$
\det A = ad - bc.
$$

Here is the geometric meaning. Recall from Chapter 11 that $A$ transforms the unit square (corners at $(0,0), (1,0), (1,1), (0,1)$) into a parallelogram with corners at $(0,0)$, $(a, c)$, $(a+b, c+d)$, $(b, d)$. The *area* of that parallelogram is $|\det A| = |ad - bc|$.

The *sign* of $\det A$ tells you whether the transformation preserves orientation (positive — the unit square is mapped to a parallelogram traversed in the same counterclockwise order) or flips it (negative — like a mirror reflection).

Test it: for the identity $\begin{pmatrix} 1 & 0 \\ 0 & 1 \end{pmatrix}$, $\det = 1$ — area unchanged, orientation preserved. For the reflection $\begin{pmatrix} 1 & 0 \\ 0 & -1 \end{pmatrix}$, $\det = -1$ — area unchanged, orientation flipped. For the doubling $\begin{pmatrix} 2 & 0 \\ 0 & 2 \end{pmatrix}$, $\det = 4$ — area scales by 4 (which makes sense: each side doubles, so area quadruples). For a 90° rotation $\begin{pmatrix} 0 & -1 \\ 1 & 0 \end{pmatrix}$, $\det = 0 \cdot 0 - (-1)(1) = 1$ — rotations preserve area.

What about a *singular* matrix like the projection $\begin{pmatrix} 1 & 0 \\ 0 & 0 \end{pmatrix}$? $\det = 0$. And indeed, this matrix squashes the unit square onto the x-axis — a line, which has zero area. The connection between "zero determinant" and "non-invertible" suddenly makes sense: if the transformation collapses 2D into 1D (or 3D into 2D, or any-D into lower), it has destroyed information that no inverse can recover, and the "area scaling factor" is zero.

### 13.6.2 The 3x3 determinant: signed volume

For 3x3 matrices, the determinant equals the signed volume of the parallelepiped formed by the three column vectors. Zero determinant means the columns are coplanar — they span only a 2D subspace of $\mathbb{R}^3$ — and the transformation collapses 3D space onto a plane.

The formula is more involved. One way to compute it is **cofactor expansion along the first row**:

$$
\det \begin{pmatrix} a & b & c \\ d & e & f \\ g & h & i \end{pmatrix} = a (ei - fh) - b (di - fg) + c (dh - eg).
$$

Each term is one of the diagonal entries times the determinant of the $2 \times 2$ submatrix you get by crossing out that entry's row and column, with alternating signs. The result is the volume.

This pattern — cofactor expansion — works for any $n \times n$ matrix, recursively: an $n \times n$ determinant is a sum of $n$ terms, each of which is an entry times an $(n-1) \times (n-1)$ determinant. For large $n$, this is impossibly slow ($n!$ operations); in practice numerical libraries compute determinants via the LU decomposition.

### 13.6.3 Properties of the determinant

A few that will come up:

- $\det(I) = 1$.
- $\det(AB) = \det(A) \det(B)$. (Areas/volumes scale multiplicatively under composition.)
- $\det(A^T) = \det(A)$.
- $\det(A^{-1}) = 1 / \det(A)$ (when $A$ is invertible). Consistent with the above: $\det(A) \det(A^{-1}) = \det(I) = 1$.
- $\det(cA) = c^n \det(A)$ for an $n \times n$ matrix and scalar $c$.

The most important fact, and the one we will use without further mention:

$$
A \text{ is invertible} \;\Longleftrightarrow\; \det A \neq 0.
$$

We will state but not prove this. The proof goes through cofactor expansion and a fair amount of careful algebra; it is in any standard linear algebra textbook. The geometric intuition is the clincher: if the transformation has zero area/volume scaling, it has flattened the space and is non-invertible.

---

## 13.7 Rank, column space, row space — a light touch

These concepts are essential for understanding linear regression, regularization, and PCA at a deep level. We won't go all-in here, but we need the vocabulary.

The **column space** of an $m \times n$ matrix $A$ is the set of all vectors of the form $A \mathbf{x}$ as $\mathbf{x}$ ranges over $\mathbb{R}^n$. By the linear-combination-of-columns view of $A \mathbf{x}$, this is exactly the **span of the columns of $A$**. It is a subspace of $\mathbb{R}^m$.

The **row space** is the span of the rows of $A$, a subspace of $\mathbb{R}^n$.

The **rank** of $A$ is the dimension of the column space (equivalently, the dimension of the row space — a non-obvious theorem). For an $m \times n$ matrix, $\text{rank}(A) \leq \min(m, n)$.

A matrix has **full rank** if its rank equals $\min(m, n)$. For a square matrix, full rank means $\text{rank} = n$ means invertible means $\det \neq 0$.

Why does this matter for ML?

- In linear regression, the matrix $X^T X$ is invertible if and only if $X$ has full column rank — meaning, no feature is a linear combination of the others. If two columns of $X$ are perfectly correlated (the same column twice, for instance), $X$ is rank-deficient, $X^T X$ is singular, and the normal equation has no unique solution. (Ridge regression — Chapter 20 — sidesteps this by adding a small multiple of $I$, which makes $X^T X + \lambda I$ always invertible.)

- In PCA, the rank of the covariance matrix bounds the number of non-trivial principal components.

- In recommender systems, the trick of *low-rank matrix factorization* is to approximate a large user-item matrix by the product of two skinny matrices — implicitly assuming that the underlying structure has low rank.

Rank is, in a sense, the dimensionality of the *real* information in a matrix. A matrix with 5,000 columns but rank 50 is "really" a 50-dimensional object dressed up in 5,000-dimensional clothing. PCA recovers the 50 dimensions; SVD (Chapter 14) does the same job more generally.

---

## 13.8 Worked example — solving a 2x2 linear system two ways

Suppose we want to solve

$$
\begin{cases} 2 x + 3 y = 8 \\ x + 4 y = 9 \end{cases}
$$

This is the matrix equation $A \mathbf{v} = \mathbf{b}$ with

$$
A = \begin{pmatrix} 2 & 3 \\ 1 & 4 \end{pmatrix}, \qquad \mathbf{v} = \begin{pmatrix} x \\ y \end{pmatrix}, \qquad \mathbf{b} = \begin{pmatrix} 8 \\ 9 \end{pmatrix}.
$$

### 13.8.1 Method 1: Gaussian elimination

Form the augmented matrix and row-reduce:

$$
\begin{pmatrix} 2 & 3 & | & 8 \\ 1 & 4 & | & 9 \end{pmatrix}.
$$

Swap rows to get a 1 in the top-left (cleaner):

$$
\begin{pmatrix} 1 & 4 & | & 9 \\ 2 & 3 & | & 8 \end{pmatrix}.
$$

Subtract 2 times row 1 from row 2:

$$
\begin{pmatrix} 1 & 4 & | & 9 \\ 0 & -5 & | & -10 \end{pmatrix}.
$$

From the second row: $-5 y = -10$, so $y = 2$. Back-substitute into the first row: $x + 4(2) = 9$, so $x = 1$.

Solution: $\mathbf{v} = (1, 2)$.

### 13.8.2 Method 2: Compute the inverse

Determinant: $\det A = 2 \cdot 4 - 3 \cdot 1 = 8 - 3 = 5$. Non-zero, so invertible.

$$
A^{-1} = \frac{1}{5} \begin{pmatrix} 4 & -3 \\ -1 & 2 \end{pmatrix} = \begin{pmatrix} 4/5 & -3/5 \\ -1/5 & 2/5 \end{pmatrix}.
$$

Then $\mathbf{v} = A^{-1} \mathbf{b}$:

$$
\mathbf{v} = \begin{pmatrix} 4/5 & -3/5 \\ -1/5 & 2/5 \end{pmatrix} \begin{pmatrix} 8 \\ 9 \end{pmatrix} = \begin{pmatrix} 32/5 - 27/5 \\ -8/5 + 18/5 \end{pmatrix} = \begin{pmatrix} 5/5 \\ 10/5 \end{pmatrix} = \begin{pmatrix} 1 \\ 2 \end{pmatrix}.
$$

Same answer, $(1, 2)$. Both methods work. Method 1 (elimination) is what `np.linalg.solve` does under the hood — it's faster, especially for larger systems, because it never forms the inverse. Method 2 is conceptually clean and what you write in math derivations, but you don't actually run it that way.

---

## 13.9 Code, last

```python
import numpy as np

# Matrix-vector product
A = np.array([[1.0, 2.0, 3.0],
              [4.0, 5.0, 6.0]])
x = np.array([1.0, 0.0, 2.0])
print(A @ x)            # [ 7. 16.]

# Matrix-matrix product
B = np.array([[7.0,  8.0],
              [9.0, 10.0],
              [11.0, 12.0]])
C = A @ B
print(C)                # [[ 58.  64.] [139. 154.]]

# Shape check that bites every newcomer
# A @ A.T works (2x3 times 3x2 -> 2x2)
print((A @ A.T).shape)  # (2, 2)
# A @ A does NOT work (2x3 times 2x3 — mismatched inner dims)
# A @ A would raise ValueError

# Transpose
print(A.T)
print(A.T.shape)        # (3, 2)
# (AB)^T = B^T A^T
print(np.allclose((A @ B).T, B.T @ A.T))   # True

# Identity
I3 = np.eye(3)
print(I3)
print(np.allclose(A @ I3, A))   # True

# Inverse — small example
M = np.array([[2.0, 3.0],
              [1.0, 4.0]])
M_inv = np.linalg.inv(M)
print(M_inv)
print(np.allclose(M @ M_inv, np.eye(2)))   # True

# Solving A v = b — preferred over computing M_inv @ b
b = np.array([8.0, 9.0])
v = np.linalg.solve(M, b)
print(v)                 # [1. 2.]

# Determinant
print(np.linalg.det(M))  # 5.0  (with tiny FP noise)

# Singular matrix detection
S = np.array([[1.0, 2.0],
              [2.0, 4.0]])     # row 2 = 2 * row 1
print(np.linalg.det(S))         # ~0.0
# np.linalg.inv(S) would raise LinAlgError: Singular matrix

# Rank
print(np.linalg.matrix_rank(M))  # 2 — full rank
print(np.linalg.matrix_rank(S))  # 1 — rank deficient
```

Two practical points. First, `@` is matrix multiplication; `*` is elementwise. Mixing them up is the single most common bug for beginners. Second, `np.linalg.solve(A, b)` is what you reach for to compute $A^{-1} \mathbf{b}$, not `np.linalg.inv(A) @ b` — solve is faster and more accurate. The explicit `inv` exists, but it is for when you genuinely need the inverse matrix as an object, not just its action on a vector.

---

## 13.10 Edge cases and engineering tradeoffs

**Ill-conditioned matrices.** A matrix can be technically invertible (non-zero determinant) but *nearly* singular — the determinant is tiny, columns are almost linearly dependent. Inverting such a matrix amplifies floating-point error catastrophically. The diagnostic is the **condition number**: the ratio of the largest to smallest singular value (Chapter 14). High condition number $\Rightarrow$ tread carefully. Ridge regression's main practical purpose is to fix this.

**Matrix multiplication cost.** Naïve algorithm is $O(n^3)$ for square matrices. BLAS implementations exploit cache hierarchies and SIMD to make this fast — fast enough that for matrices up to a few thousand on a side, you can multiply them in seconds on a laptop. For larger matrices, distributed compute (Spark) or specialised hardware (GPU) becomes necessary. Part J revisits.

**Storage.** A dense $n \times n$ matrix at 8 bytes per entry is $8n^2$ bytes. At $n = 10^4$ that's 800 MB — uncomfortable but tolerable. At $n = 10^5$, that's 80 GB — out of the question for a single machine. Sparse representations and low-rank factorizations are how production systems handle scale.

**Numerical inverses on near-singular matrices.** When `np.linalg.inv` is given a near-singular matrix, the result can have wildly wrong entries even though `inv @ M` returns something close to $I$. The pseudo-inverse (`np.linalg.pinv`, based on SVD) is the safer fallback. We will see why in Chapter 14.

---

## 13.11 What this builds on / where this returns

**Builds on:** Chapter 11 (vectors, matrices as linear maps). Chapter 12 (dot products, which are the building blocks of row-times-column).

**Returns:**

- **Linear regression** (Chapter 31): the normal equation $\hat{\mathbf{w}} = (X^T X)^{-1} X^T \mathbf{y}$ is just $X^T X$, its inverse, and a matrix-vector product. We derive it from first principles in Chapter 31.
- **Logistic regression** (Chapter 32): no closed-form inverse, but the Hessian (which determines the curvature of the loss surface) is a matrix whose properties drive optimisation.
- **Regularization** (Chapter 20): ridge regression replaces $(X^T X)^{-1}$ with $(X^T X + \lambda I)^{-1}$, which is always invertible — fixing the rank-deficiency problem.
- **Eigendecomposition and PCA** (Chapters 14, 40): they extract structure from a symmetric matrix $X^T X$ (or the covariance matrix).
- **Spark MLlib** (Part J, K): every distributed linear algebra primitive — `RowMatrix`, `BlockMatrix`, distributed `gemm` — is the same operations performed across cluster nodes.

---

## 13.12 Exercises

1. **Matrix-vector by row view.** Compute $A \mathbf{x}$ for $A = \begin{pmatrix} 1 & 0 & 2 \\ -1 & 3 & 1 \end{pmatrix}$ and $\mathbf{x} = (2, 1, -1)$.

2. **Same product by column view.** Redo problem 1 using the column-view formula and verify you get the same answer.

3. **Matrix-matrix product.** Compute $AB$ for $A = \begin{pmatrix} 1 & 2 \\ 3 & 4 \end{pmatrix}$ and $B = \begin{pmatrix} 5 & 6 \\ 7 & 8 \end{pmatrix}$. Then compute $BA$. They should be different.

4. **Shape inference.** What is the shape of $X^T X$ if $X$ is $n \times d$? What is the shape of $X X^T$? When $n = 10{,}000$ and $d = 5{,}000$, which one would you rather store?

5. **Transpose identity.** Verify $(AB)^T = B^T A^T$ by computing both sides for the matrices in problem 3.

6. **Compute a 2x2 inverse by hand.** Let $A = \begin{pmatrix} 3 & 1 \\ 2 & 4 \end{pmatrix}$. Compute $\det A$, then $A^{-1}$. Then verify $A A^{-1} = I$.

7. **A singular matrix.** Show that $S = \begin{pmatrix} 1 & 2 \\ 2 & 4 \end{pmatrix}$ has $\det = 0$. Without computing further, what does this tell you about (a) the rank of $S$, (b) whether $S$ is invertible, (c) the relationship between the columns?

8. **Solve a 2x2 system by elimination.** Solve $3x + 2y = 7$, $x - y = 1$. Show every step.

9. **Solve the same system via the inverse.** Same as problem 8, now using $\mathbf{v} = A^{-1} \mathbf{b}$. Confirm you get the same answer.

10. **Determinant of a special matrix.** Compute the determinant of the rotation matrix $R = \begin{pmatrix} \cos\theta & -\sin\theta \\ \sin\theta & \cos\theta \end{pmatrix}$. What does the answer tell you geometrically?

11. **A 3x3 determinant.** Compute $\det \begin{pmatrix} 1 & 2 & 3 \\ 0 & 1 & 4 \\ 5 & 6 & 0 \end{pmatrix}$ by cofactor expansion along the first row. Show each step.

12. **Rank from inspection.** What is the rank of $M = \begin{pmatrix} 1 & 2 & 3 \\ 2 & 4 & 6 \\ 1 & 1 & 1 \end{pmatrix}$? Justify by spotting a linear dependence.

13. **Engineering practice.** Suppose you need to compute $A^{-1} \mathbf{b}$ in production code. Why is `np.linalg.solve(A, b)` preferred over `np.linalg.inv(A) @ b`? Give two reasons.

14. **Connection to ML.** In the normal equation $\hat{\mathbf{w}} = (X^T X)^{-1} X^T \mathbf{y}$, what is the shape of $X^T X$ if $X$ is $n \times d$? What does it mean for $X^T X$ to be singular? Name two things in your data that could cause this.

<details>
<summary>Answers</summary>

1. Row 1 dotted with $\mathbf{x}$: $1 \cdot 2 + 0 \cdot 1 + 2 \cdot (-1) = 2 + 0 - 2 = 0$. Row 2: $-1 \cdot 2 + 3 \cdot 1 + 1 \cdot (-1) = -2 + 3 - 1 = 0$. So $A \mathbf{x} = (0, 0)$.

2. Columns of $A$: $(1, -1)$, $(0, 3)$, $(2, 1)$. Compute $2(1, -1) + 1(0, 3) + (-1)(2, 1) = (2, -2) + (0, 3) + (-2, -1) = (0, 0)$. Same answer.

3. $AB = \begin{pmatrix} 19 & 22 \\ 43 & 50 \end{pmatrix}$. $BA = \begin{pmatrix} 23 & 34 \\ 31 & 46 \end{pmatrix}$. Different.

4. $X^T X$ is $d \times d$ ($5{,}000 \times 5{,}000$, 200 MB at 8 bytes/entry). $X X^T$ is $n \times n$ ($10{,}000 \times 10{,}000$, 800 MB). Prefer storing $X^T X$ — it's smaller and is what shows up in the normal equation anyway.

5. $AB = \begin{pmatrix} 19 & 22 \\ 43 & 50 \end{pmatrix}$. $(AB)^T = \begin{pmatrix} 19 & 43 \\ 22 & 50 \end{pmatrix}$. $B^T = \begin{pmatrix} 5 & 7 \\ 6 & 8 \end{pmatrix}$, $A^T = \begin{pmatrix} 1 & 3 \\ 2 & 4 \end{pmatrix}$. $B^T A^T = \begin{pmatrix} 5 \cdot 1 + 7 \cdot 2 & 5 \cdot 3 + 7 \cdot 4 \\ 6 \cdot 1 + 8 \cdot 2 & 6 \cdot 3 + 8 \cdot 4 \end{pmatrix} = \begin{pmatrix} 19 & 43 \\ 22 & 50 \end{pmatrix}$. Match.

6. $\det A = 3 \cdot 4 - 1 \cdot 2 = 10$. $A^{-1} = \frac{1}{10}\begin{pmatrix} 4 & -1 \\ -2 & 3 \end{pmatrix} = \begin{pmatrix} 0.4 & -0.1 \\ -0.2 & 0.3 \end{pmatrix}$. Check: $A A^{-1} = \begin{pmatrix} 3(0.4) + 1(-0.2) & 3(-0.1) + 1(0.3) \\ 2(0.4) + 4(-0.2) & 2(-0.1) + 4(0.3) \end{pmatrix} = \begin{pmatrix} 1.0 & 0.0 \\ 0.0 & 1.0 \end{pmatrix} = I$.

7. $\det S = 1 \cdot 4 - 2 \cdot 2 = 0$. (a) Rank is at most 1 (one column is twice the other, so they span only a 1D subspace). Rank is exactly 1 because $S$ is non-zero. (b) Not invertible. (c) Column 2 = 2 × column 1.

8. From $x - y = 1$, $x = y + 1$. Substitute: $3(y + 1) + 2y = 7 \Rightarrow 5y + 3 = 7 \Rightarrow y = 4/5$. Then $x = 4/5 + 1 = 9/5$. Solution $(9/5, 4/5)$.

9. $A = \begin{pmatrix} 3 & 2 \\ 1 & -1 \end{pmatrix}$, $\det A = -3 - 2 = -5$. $A^{-1} = \frac{1}{-5}\begin{pmatrix} -1 & -2 \\ -1 & 3 \end{pmatrix} = \begin{pmatrix} 1/5 & 2/5 \\ 1/5 & -3/5 \end{pmatrix}$. $A^{-1} \mathbf{b} = \begin{pmatrix} 1/5 & 2/5 \\ 1/5 & -3/5 \end{pmatrix} \begin{pmatrix} 7 \\ 1 \end{pmatrix} = \begin{pmatrix} 7/5 + 2/5 \\ 7/5 - 3/5 \end{pmatrix} = (9/5, 4/5)$. Matches.

10. $\det R = \cos^2 \theta - (-\sin\theta)(\sin\theta) = \cos^2 \theta + \sin^2 \theta = 1$. The rotation preserves area and orientation. (Makes sense — rotations don't stretch.)

11. Expanding along row 1: $1 \cdot \det \begin{pmatrix} 1 & 4 \\ 6 & 0 \end{pmatrix} - 2 \cdot \det \begin{pmatrix} 0 & 4 \\ 5 & 0 \end{pmatrix} + 3 \cdot \det \begin{pmatrix} 0 & 1 \\ 5 & 6 \end{pmatrix} = 1(0 - 24) - 2(0 - 20) + 3(0 - 5) = -24 + 40 - 15 = 1$.

12. Rank 2. Row 2 = 2 × row 1, so the first two rows are linearly dependent; they span a 1D space. Row 3 is not in that span (1 ≠ 2 × something consistent with rows 1-2). So total rank is 2.

13. (1) `solve` is faster — it doesn't compute the full inverse, only the part needed to find $\mathbf{x}$. (2) `solve` is more numerically stable — computing an inverse and then multiplying amplifies floating-point error more than direct elimination does. For nearly-singular matrices the difference is dramatic.

14. $X^T X$ is $d \times d$. Singular means rank $< d$, meaning some linear combination of the columns of $X$ is the zero vector. Two practical causes: (a) two features are perfectly correlated (one is a linear function of another) — the most common case, often from accidentally including both a feature and a one-hot encoding of it; (b) you have fewer training examples than features ($n < d$), in which case $X$ has more columns than rows and $X^T X$ is rank-deficient by counting. Ridge regression's $\lambda I$ term fixes both.

</details>
