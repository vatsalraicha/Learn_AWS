# Chapter 14 — Eigenvalues and Eigenvectors

> **Goal of this chapter:** to build a working understanding of eigenvalues and eigenvectors — not as a recipe you apply, but as a structural property of linear transformations that you can *see*. PCA (which we'll derive in Chapter 40) finds the "directions of maximum variance" in your data by computing the eigenvectors of the covariance matrix. That sentence is gibberish until you know what an eigenvector *is*. By the end of this chapter, when somebody says "we project onto the top three eigenvectors of $\Sigma$," you should be able to translate that into a picture: there are three special directions in the data, and we're describing each point by where it falls along those directions. The rest is computation.

---

## 14.1 The motivating picture — directions a matrix doesn't rotate

Back in Chapter 11 we saw that a matrix $A$ acts on the plane: it stretches, rotates, shears, or projects. Pick a vector $\mathbf{v}$, apply $A$ to it, and you get a new vector $A \mathbf{v}$. In general, $A \mathbf{v}$ has a different *direction* than $\mathbf{v}$ — that's what rotation and shear do.

But for some specific matrices and some specific vectors, the output direction matches the input direction. The matrix has stretched the vector (or shrunk it, or flipped it), but it hasn't rotated it. The vector lies along an "axis" of the transformation, a direction that the matrix only scales without turning.

These special vectors are the **eigenvectors** of $A$, and the corresponding scaling factors are the **eigenvalues**. Whenever we can find them, they tell us something deep: $A$, on those special directions, is doing nothing more interesting than multiplication by a number. Everything complicated about $A$ — the rotations, the shears — happens *off* those axes.

Let's see one in 2D before we formalise. Take the diagonal matrix

$$
A = \begin{pmatrix} 2 & 0 \\ 0 & 3 \end{pmatrix}.
$$

From Chapter 11: $A$ stretches the plane by a factor of 2 horizontally and 3 vertically. Now ask: which directions does $A$ *not* rotate?

The x-axis direction, $\mathbf{e}_1 = (1, 0)$: $A \mathbf{e}_1 = (2, 0) = 2 \mathbf{e}_1$. The output is $\mathbf{e}_1$ scaled by 2. Same direction. Eigenvector with eigenvalue $\lambda = 2$.

The y-axis direction, $\mathbf{e}_2 = (0, 1)$: $A \mathbf{e}_2 = (0, 3) = 3 \mathbf{e}_2$. Eigenvector with eigenvalue $\lambda = 3$.

Try $(1, 1)$: $A (1, 1) = (2, 3)$. This is *not* a scalar multiple of $(1, 1)$. So $(1, 1)$ is *not* an eigenvector of this $A$.

The pattern: for a diagonal matrix, the eigenvectors are the standard axes, and the eigenvalues are the diagonal entries. The whole "diagonal matrix" thing is exactly "matrix expressed in its eigenvector coordinate system" — no rotation involved, just scaling on each axis.

The story gets more interesting when the matrix is *not* diagonal. In that case, there are still special directions — but they're tilted from the standard axes, and finding them is the work of this chapter.

---

## 14.2 Formal definition

A non-zero vector $\mathbf{v}$ is an **eigenvector** of an $n \times n$ matrix $A$ if there exists a scalar $\lambda$ such that

$$
A \mathbf{v} = \lambda \mathbf{v}.
$$

The scalar $\lambda$ is the **eigenvalue** associated with $\mathbf{v}$.

Three things to notice immediately.

**Eigenvectors are non-zero by definition.** The zero vector trivially satisfies $A \mathbf{0} = \lambda \mathbf{0}$ for any $\lambda$, so we exclude it to keep the definition meaningful.

**Scaling an eigenvector gives another eigenvector with the same eigenvalue.** If $A \mathbf{v} = \lambda \mathbf{v}$, then $A(c \mathbf{v}) = c A \mathbf{v} = c \lambda \mathbf{v} = \lambda (c \mathbf{v})$. So eigenvectors come in *whole lines*, not isolated vectors. We usually pick a unit-length representative.

**Eigenvalues can be negative or zero.** A negative eigenvalue means the matrix *flips* the eigenvector (and scales by $|\lambda|$). A zero eigenvalue means the matrix *kills* the eigenvector — sends it to zero. Eigenvalues of zero are exactly the directions that the matrix projects to nothing; their existence is equivalent to the matrix being singular.

---

## 14.3 Finding eigenvalues — the characteristic equation

We have a definition. Now we need a procedure.

The equation $A \mathbf{v} = \lambda \mathbf{v}$ can be rewritten as

$$
A \mathbf{v} - \lambda \mathbf{v} = \mathbf{0} \quad\Longleftrightarrow\quad (A - \lambda I) \mathbf{v} = \mathbf{0}.
$$

We are looking for a *non-zero* $\mathbf{v}$ that satisfies this. The equation $(A - \lambda I) \mathbf{v} = \mathbf{0}$ has a non-zero solution if and only if the matrix $A - \lambda I$ is *singular* — its columns are linearly dependent, equivalently its determinant is zero.

So the eigenvalues are exactly the solutions of the **characteristic equation**:

$$
\boxed{\det(A - \lambda I) = 0.}
$$

For an $n \times n$ matrix, $\det(A - \lambda I)$ is a polynomial of degree $n$ in $\lambda$ — the **characteristic polynomial**. Its roots are the eigenvalues. By the fundamental theorem of algebra, an $n$-degree polynomial has exactly $n$ roots in the complex numbers (counted with multiplicity), so an $n \times n$ matrix has exactly $n$ eigenvalues (possibly with repeats, possibly complex).

For each eigenvalue $\lambda$, we plug it back into $(A - \lambda I) \mathbf{v} = \mathbf{0}$ and solve for $\mathbf{v}$.

### 14.3.1 A worked 2x2 example, step by step

Let's find the eigenvalues and eigenvectors of

$$
A = \begin{pmatrix} 4 & 1 \\ 2 & 3 \end{pmatrix}.
$$

**Step 1: Form $A - \lambda I$.**

$$
A - \lambda I = \begin{pmatrix} 4 - \lambda & 1 \\ 2 & 3 - \lambda \end{pmatrix}.
$$

**Step 2: Compute its determinant.**

$$
\det(A - \lambda I) = (4 - \lambda)(3 - \lambda) - (1)(2) = 12 - 4\lambda - 3\lambda + \lambda^2 - 2 = \lambda^2 - 7\lambda + 10.
$$

**Step 3: Set to zero and solve.**

$$
\lambda^2 - 7\lambda + 10 = 0.
$$

Factor: $(\lambda - 5)(\lambda - 2) = 0$. So $\lambda_1 = 5$ and $\lambda_2 = 2$.

Two eigenvalues. So far so good.

**Step 4a: Find the eigenvector for $\lambda_1 = 5$.**

Plug $\lambda = 5$ into $(A - \lambda I) \mathbf{v} = \mathbf{0}$:

$$
\begin{pmatrix} 4 - 5 & 1 \\ 2 & 3 - 5 \end{pmatrix} \mathbf{v} = \begin{pmatrix} -1 & 1 \\ 2 & -2 \end{pmatrix} \mathbf{v} = \mathbf{0}.
$$

This gives two equations: $-v_1 + v_2 = 0$ and $2 v_1 - 2 v_2 = 0$. They are the same equation: $v_2 = v_1$. So every vector of the form $(t, t)$ is an eigenvector. Pick $\mathbf{v}_1 = (1, 1)$ as a representative.

**Verify:** $A \mathbf{v}_1 = \begin{pmatrix} 4 & 1 \\ 2 & 3 \end{pmatrix} \begin{pmatrix} 1 \\ 1 \end{pmatrix} = \begin{pmatrix} 5 \\ 5 \end{pmatrix} = 5 \mathbf{v}_1$. ✓

**Step 4b: Find the eigenvector for $\lambda_2 = 2$.**

Plug $\lambda = 2$ into $(A - \lambda I) \mathbf{v} = \mathbf{0}$:

$$
\begin{pmatrix} 2 & 1 \\ 2 & 1 \end{pmatrix} \mathbf{v} = \mathbf{0}.
$$

Both rows give: $2 v_1 + v_2 = 0$, i.e., $v_2 = -2 v_1$. So $(t, -2t)$ for any $t$ is an eigenvector. Pick $\mathbf{v}_2 = (1, -2)$.

**Verify:** $A \mathbf{v}_2 = \begin{pmatrix} 4 & 1 \\ 2 & 3 \end{pmatrix} \begin{pmatrix} 1 \\ -2 \end{pmatrix} = \begin{pmatrix} 4 - 2 \\ 2 - 6 \end{pmatrix} = \begin{pmatrix} 2 \\ -4 \end{pmatrix} = 2 \mathbf{v}_2$. ✓

So $A$ has two special directions: $(1, 1)$, which it stretches by 5, and $(1, -2)$, which it stretches by 2. Every other vector in the plane is some linear combination of these two, and applying $A$ to a combination scales each piece by its own eigenvalue.

### 14.3.2 The geometric picture

Picture the plane. Draw the line through the origin along $(1, 1)$ — the first eigenvector. Draw another line through the origin along $(1, -2)$ — the second eigenvector. These are the "axes" of $A$. (They're not perpendicular here — that's a special feature of *symmetric* matrices, which we'll get to.)

Now: $A$ acts on this picture by stretching the first axis by 5 and the second by 2. Vectors along the first axis stay along that axis, only longer. Vectors along the second axis stay along that axis, slightly longer. Vectors that aren't on either axis are decomposed (in the new "eigen-basis") and stretched differently along each axis.

That's all $A$ is doing. It looks complicated in the standard $(x, y)$ basis because the eigenvectors aren't aligned with the axes. In the eigen-basis, $A$ is just diagonal: it scales by 5 along one direction and 2 along the other.

This insight — that you can find a basis in which $A$ is *diagonal* — is the punchline of this chapter and the engine of PCA.

---

## 14.4 The case of complex eigenvalues — and why we mostly don't worry

Some matrices have no real eigenvalues. The simplest example: the 90° rotation matrix

$$
R = \begin{pmatrix} 0 & -1 \\ 1 & \phantom{-}0 \end{pmatrix}.
$$

The characteristic polynomial is $\det(R - \lambda I) = \lambda^2 + 1$, which has roots $\lambda = \pm i$ — purely imaginary. No real eigenvalue exists.

Geometrically this is obvious. The rotation matrix rotates every direction by 90°. There is no direction in the real plane that $R$ leaves un-rotated (other than the trivial $\mathbf{0}$). The eigenvectors live in the complex plane, where rotation corresponds to multiplication by $e^{i\theta}$ — a complex eigenvalue of modulus 1.

For most ML, we work with **symmetric** matrices (covariance matrices, $X^T X$, etc.), and these have a beautiful property: *all their eigenvalues are real*. So we'll mostly forget complex eigenvalues. But it's worth knowing they exist, so the general theorem is "eigenvalues are real *if* the matrix is symmetric," not "eigenvalues are always real."

---

## 14.5 Symmetric matrices — the eigenstructure ML cares about

A matrix $A$ is **symmetric** if $A = A^T$. Symmetric matrices show up everywhere in ML:

- The **covariance matrix** $\Sigma$ of a dataset is symmetric. So is the sample covariance $\frac{1}{n} X^T X$ (after centering).
- The **Gram matrix** $X^T X$ is symmetric for any $X$.
- The **Hessian** of a smooth scalar function is symmetric (by equality of mixed partials).
- The **kernel matrix** in kernel methods is symmetric.

Symmetric matrices have two extraordinary properties:

**Property 1: All eigenvalues are real.** No imaginary $\lambda$'s ever show up.

**Property 2: Eigenvectors corresponding to distinct eigenvalues are orthogonal.**

Let me sketch why property 2 holds. Suppose $A \mathbf{v}_1 = \lambda_1 \mathbf{v}_1$ and $A \mathbf{v}_2 = \lambda_2 \mathbf{v}_2$ with $\lambda_1 \neq \lambda_2$.

Compute $\mathbf{v}_2^T A \mathbf{v}_1$ two ways.

First way: $\mathbf{v}_2^T (A \mathbf{v}_1) = \mathbf{v}_2^T (\lambda_1 \mathbf{v}_1) = \lambda_1 (\mathbf{v}_2^T \mathbf{v}_1)$.

Second way: since $A = A^T$, $\mathbf{v}_2^T A \mathbf{v}_1 = (A \mathbf{v}_2)^T \mathbf{v}_1 = (\lambda_2 \mathbf{v}_2)^T \mathbf{v}_1 = \lambda_2 (\mathbf{v}_2^T \mathbf{v}_1)$.

So $\lambda_1 (\mathbf{v}_2^T \mathbf{v}_1) = \lambda_2 (\mathbf{v}_2^T \mathbf{v}_1)$, which means $(\lambda_1 - \lambda_2)(\mathbf{v}_2^T \mathbf{v}_1) = 0$. Since $\lambda_1 \neq \lambda_2$, we must have $\mathbf{v}_2^T \mathbf{v}_1 = 0$ — the eigenvectors are orthogonal. ∎

If two or more eigenvalues coincide (a *repeated* eigenvalue), the corresponding eigenvectors span a higher-dimensional subspace and can be *chosen* to be orthogonal (Gram-Schmidt applied to whatever basis you find). The end result: a symmetric matrix admits a full **orthonormal basis of eigenvectors**. This is the **spectral theorem**, the most beautiful theorem in linear algebra and the foundation of PCA.

We state it but don't prove it in full generality (the proof for symmetric matrices requires a small amount of analysis). Take this away:

> **Spectral theorem (informal):** For every real symmetric $n \times n$ matrix $A$, there exists an orthonormal basis $\{\mathbf{u}_1, \ldots, \mathbf{u}_n\}$ of $\mathbb{R}^n$ consisting of eigenvectors of $A$, with corresponding real eigenvalues $\lambda_1, \ldots, \lambda_n$.

This is the reason PCA works. The covariance matrix is symmetric, so the spectral theorem applies, so the principal components are an orthonormal basis aligned with eigendirections — exactly the conditions PCA needs.

---

## 14.6 Diagonalization

If $A$ is an $n \times n$ matrix with $n$ linearly independent eigenvectors (which is *always* true for symmetric matrices, and usually true for general ones), then we can write

$$
A = Q \Lambda Q^{-1},
$$

where

- $Q$ is the matrix whose columns are the eigenvectors of $A$.
- $\Lambda$ is the diagonal matrix whose diagonal entries are the eigenvalues.

This factorisation is called the **eigendecomposition** of $A$.

For a symmetric $A$, we can choose the eigenvectors to be orthonormal, in which case $Q$ is an orthogonal matrix — meaning $Q^T Q = I$, so $Q^{-1} = Q^T$. The decomposition simplifies to

$$
A = Q \Lambda Q^T \qquad (\text{symmetric case}).
$$

This is the cleanest, most computational-friendly form. The "inverse" is just a transpose.

### 14.6.1 What diagonalization tells us

The equation $A = Q \Lambda Q^{-1}$ can be read as a coordinate change:

1. $Q^{-1}$ takes a vector $\mathbf{x}$ written in standard coordinates and re-expresses it in the eigenbasis.
2. $\Lambda$ scales each eigenbasis coordinate by the corresponding eigenvalue.
3. $Q$ rotates back to standard coordinates.

In the eigenbasis, $A$ is just a diagonal matrix — pure scalings, one per axis. The complication of $A$ in the original coordinates is *only* the rotation from the eigenbasis to standard coordinates.

This is also how you compute powers of $A$ efficiently: $A^k = Q \Lambda^k Q^{-1}$, and $\Lambda^k$ is just the diagonal matrix with entries $\lambda_i^k$. What would otherwise be $k$ separate matrix multiplications becomes a single scalar exponentiation per eigenvalue.

### 14.6.2 Eigendecomposition example

For the $A = \begin{pmatrix} 4 & 1 \\ 2 & 3 \end{pmatrix}$ from section 14.3:

Eigenvalues: $\lambda_1 = 5$, $\lambda_2 = 2$.
Eigenvectors: $\mathbf{v}_1 = (1, 1)$, $\mathbf{v}_2 = (1, -2)$.

$$
Q = \begin{pmatrix} 1 & 1 \\ 1 & -2 \end{pmatrix}, \quad \Lambda = \begin{pmatrix} 5 & 0 \\ 0 & 2 \end{pmatrix}.
$$

Compute $Q^{-1}$: $\det Q = 1 \cdot (-2) - 1 \cdot 1 = -3$. So

$$
Q^{-1} = \frac{1}{-3}\begin{pmatrix} -2 & -1 \\ -1 & \phantom{-}1 \end{pmatrix} = \begin{pmatrix} 2/3 & 1/3 \\ 1/3 & -1/3 \end{pmatrix}.
$$

Verify $A = Q \Lambda Q^{-1}$:

$$
Q \Lambda = \begin{pmatrix} 1 & 1 \\ 1 & -2 \end{pmatrix} \begin{pmatrix} 5 & 0 \\ 0 & 2 \end{pmatrix} = \begin{pmatrix} 5 & 2 \\ 5 & -4 \end{pmatrix}.
$$

$$
Q \Lambda Q^{-1} = \begin{pmatrix} 5 & 2 \\ 5 & -4 \end{pmatrix} \begin{pmatrix} 2/3 & 1/3 \\ 1/3 & -1/3 \end{pmatrix} = \begin{pmatrix} 10/3 + 2/3 & 5/3 - 2/3 \\ 10/3 - 4/3 & 5/3 + 4/3 \end{pmatrix} = \begin{pmatrix} 4 & 1 \\ 2 & 3 \end{pmatrix} = A. ✓
$$

(This $A$ is not symmetric, so the eigenvectors aren't orthogonal — you can check: $(1)(1) + (1)(-2) = -1 \neq 0$. So $Q$ is not orthogonal here. In the symmetric case we'd have $Q^{-1} = Q^T$.)

---

## 14.7 The Singular Value Decomposition (SVD)

Eigendecomposition is gorgeous but limited. It only applies to *square* matrices, and even then only when there are enough linearly independent eigenvectors. ML data matrices are usually *not* square — $X$ might be $n$ rows by $d$ columns with $n \neq d$.

The **Singular Value Decomposition** (SVD) generalises eigendecomposition to arbitrary matrices. We'll state it without proof; the proof is a non-trivial chapter of any linear algebra book.

**SVD theorem.** Every real $m \times n$ matrix $A$ can be factored as

$$
A = U \Sigma V^T,
$$

where:

- $U$ is an $m \times m$ orthogonal matrix ($U^T U = I_m$). Its columns are the **left singular vectors** of $A$.
- $\Sigma$ is an $m \times n$ "diagonal" matrix — non-negative entries $\sigma_1 \geq \sigma_2 \geq \cdots \geq \sigma_r > 0$ on the diagonal, zeros elsewhere, where $r = \text{rank}(A)$. The $\sigma_i$ are the **singular values**.
- $V$ is an $n \times n$ orthogonal matrix. Its columns are the **right singular vectors**.

The connection to eigendecomposition:

- The columns of $V$ are the eigenvectors of $A^T A$ (symmetric, $n \times n$).
- The columns of $U$ are the eigenvectors of $A A^T$ (symmetric, $m \times m$).
- The singular values $\sigma_i$ are the square roots of the eigenvalues of $A^T A$ (equivalently, of $A A^T$).

So SVD is, in effect, "eigendecomposition done on $A^T A$ and $A A^T$ in a coordinated way."

### 14.7.1 What SVD is good for in ML

Three blockbuster applications:

**1. Low-rank approximation.** The best rank-$k$ approximation of $A$ (in the L2 sense) is obtained by keeping only the top $k$ singular values: $A_k = \sum_{i=1}^{k} \sigma_i \mathbf{u}_i \mathbf{v}_i^T$. The remaining $\sigma_{k+1}, \ldots, \sigma_r$ are discarded. This is the **Eckart-Young theorem**. It's the math behind compressed image storage, collaborative-filtering recommender systems, and PCA-as-data-compression.

**2. PCA.** The principal components of a centered data matrix $X$ are exactly the right singular vectors of $X$, with the corresponding singular values telling you how much variance each component captures. PCA via SVD is the standard implementation — more numerically stable than computing eigenvectors of $X^T X$ directly. Chapter 40.

**3. The pseudo-inverse.** For a non-square or singular matrix, the **Moore-Penrose pseudo-inverse** is defined via SVD: if $A = U \Sigma V^T$, then $A^+ = V \Sigma^+ U^T$, where $\Sigma^+$ inverts the non-zero singular values and leaves zeros alone. This is what `np.linalg.pinv` computes, and it's the rigorous way to solve least-squares problems when $X^T X$ is singular or near-singular. Ridge regression with $\lambda \to 0$ is closely related.

We won't go further into SVD here; it deserves a chapter of its own. The takeaway: SVD is the universal factorisation that always exists, that generalises eigendecomposition to all matrices, and that underpins half of practical numerical linear algebra in ML.

---

## 14.8 Connection to ML — PCA preview

PCA, derived in full in Chapter 40, goes roughly like this.

You have a data matrix $X$ — $n$ rows of $d$-dimensional examples. You center it (subtract the mean of each column). The sample covariance matrix is $\Sigma = \frac{1}{n-1} X^T X$ (a $d \times d$ symmetric matrix).

By the spectral theorem, $\Sigma$ has an orthonormal basis of eigenvectors $\mathbf{u}_1, \ldots, \mathbf{u}_d$ with corresponding eigenvalues $\lambda_1 \geq \lambda_2 \geq \cdots \geq \lambda_d \geq 0$. The eigenvectors are called the **principal components**; the eigenvalues are the **variances** along each component.

The interpretation: $\mathbf{u}_1$ is the *direction in feature space along which the data varies the most*. The variance of the data projected onto $\mathbf{u}_1$ is $\lambda_1$. $\mathbf{u}_2$ is the direction (orthogonal to $\mathbf{u}_1$) of *next-greatest* variance, with variance $\lambda_2$. And so on.

Dimensionality reduction: keep the top $k$ principal components; project each data point onto them. You've gone from $d$ dimensions to $k$, retaining $\sum_{i=1}^{k} \lambda_i / \sum_{i=1}^{d} \lambda_i$ of the total variance. If the data lives "near" a $k$-dimensional subspace (which it often does, when $d$ is large and features are correlated), $k \ll d$ may suffice.

This is, in one paragraph, the entire idea of PCA. The mathematical content is the spectral theorem and a Lagrangian optimisation to show that "maximum variance" leads to the eigenvalue problem. We will do all of that carefully in Chapter 40.

---

## 14.9 Ridge regression and the pseudo-inverse — another preview

Standard OLS: $\hat{\mathbf{w}} = (X^T X)^{-1} X^T \mathbf{y}$. If $X^T X$ is singular (rank-deficient $X$ — collinear features, or $n < d$), no inverse exists, OLS is undefined.

Ridge regression: $\hat{\mathbf{w}} = (X^T X + \lambda I)^{-1} X^T \mathbf{y}$ for some $\lambda > 0$. The added $\lambda I$ shifts every eigenvalue of $X^T X$ up by $\lambda$, making the matrix invertible.

Via SVD: if $X = U \Sigma V^T$, then $X^T X = V \Sigma^T \Sigma V^T = V D V^T$ where $D$ is diagonal with entries $\sigma_i^2$. The matrix $X^T X + \lambda I = V (D + \lambda I) V^T$. Its inverse is $V (D + \lambda I)^{-1} V^T$. Ridge regression replaces $1/\sigma_i^2$ (which blows up when $\sigma_i$ is small) with $1/(\sigma_i^2 + \lambda)$ (which stays bounded).

So ridge can be read as "shrink the contribution of directions where $X$ has little signal, leave directions with strong signal alone." A beautiful interpretation that requires SVD to see clearly. We won't go further here; Chapter 20 will.

---

## 14.10 Code, last

```python
import numpy as np

# A 2x2 example — non-symmetric
A = np.array([[4.0, 1.0],
              [2.0, 3.0]])
eigvals, eigvecs = np.linalg.eig(A)
print(eigvals)          # [5., 2.]    (in some order)
print(eigvecs)
# Columns of eigvecs are the eigenvectors (normalized to unit length).
# Note: NumPy's eigenvector for lambda=5 is (1,1)/sqrt(2) ≈ (0.707, 0.707)
# and for lambda=2 is (1,-2)/sqrt(5) ≈ (0.447, -0.894)

# Verify A v = lambda v for each
for i in range(2):
    v = eigvecs[:, i]
    lam = eigvals[i]
    print(np.allclose(A @ v, lam * v))   # True

# Symmetric matrix — eigenvectors are orthogonal
S = np.array([[2.0, 1.0],
              [1.0, 2.0]])
vals, vecs = np.linalg.eigh(S)   # use eigh for symmetric — faster, real-only
print(vals)             # [1., 3.]
print(vecs)             # columns orthonormal
print(vecs.T @ vecs)    # ~ I — confirms orthonormality

# Diagonalization reconstruction
Q = vecs
Lam = np.diag(vals)
print(np.allclose(Q @ Lam @ Q.T, S))   # True — symmetric case

# SVD
X = np.array([[3.0, 1.0],
              [2.0, 4.0],
              [1.0, 2.0]])  # 3x2
U, sigma, Vt = np.linalg.svd(X, full_matrices=False)
print(U.shape, sigma.shape, Vt.shape)   # (3, 2), (2,), (2, 2)
print(sigma)            # singular values, descending
# Reconstruct
print(np.allclose(U @ np.diag(sigma) @ Vt, X))    # True

# Pseudo-inverse via SVD (or directly)
X_pinv = np.linalg.pinv(X)
print(X_pinv.shape)     # (2, 3) — pseudo-inverse of mxn matrix is nxm
print(np.allclose(X_pinv @ X, np.eye(2)))   # True — left inverse

# Connection: top eigenvalues of X^T X = squares of singular values
print(np.linalg.eigvalsh(X.T @ X))   # in ascending order
print(sigma ** 2)                     # the same values in descending order
```

A note on `eig` vs `eigh`. For symmetric matrices, always use `np.linalg.eigh` — it exploits symmetry, is faster, returns real (not complex) values, and is more numerically stable. `np.linalg.eig` is the general routine and will return complex eigenvalues when they exist. Mixing them up is a classic ML-numerics bug.

---

## 14.11 Edge cases and engineering tradeoffs

**Repeated eigenvalues.** When two eigenvalues coincide, the corresponding eigenspace is multi-dimensional, and there's no unique "direction." You can pick any orthonormal basis of that subspace. Numerically, repeated or nearly-repeated eigenvalues can cause eigenvector estimates to swap or be ill-defined; SVD is generally more stable.

**Defective matrices.** A square matrix that doesn't have $n$ linearly independent eigenvectors is called **defective** and *cannot be diagonalized*. Such matrices exist in theory (e.g., $\begin{pmatrix} 1 & 1 \\ 0 & 1 \end{pmatrix}$ has only one independent eigenvector), but in ML we almost never see them — our matrices are symmetric or close to symmetric, and SVD always exists regardless.

**Numerical precision.** Computing eigenvalues of large matrices is iterative and approximate. For matrices up to several thousand on a side, modern routines are fast and accurate. For massive matrices, *iterative* methods like Lanczos (for a few largest eigenvalues only) become essential. Spark MLlib's PCA uses iterative methods under the hood.

**Sign ambiguity of eigenvectors.** If $\mathbf{v}$ is an eigenvector, so is $-\mathbf{v}$ (same eigenvalue, just negated). NumPy's choice of sign is implementation-defined; if you compare results between libraries (or between runs), don't be surprised when an eigenvector is sign-flipped.

---

## 14.12 What this builds on / where this returns

**Builds on:** Chapter 13 (matrix multiplication, determinant, inverse — all used in the characteristic equation). Chapter 12 (orthogonality — central to the symmetric case). Chapter 11 (matrices as linear transformations — the geometric picture of eigenvectors).

**Returns:**

- **PCA** (Chapter 40): the principal components are the eigenvectors of the (symmetric) covariance matrix, and the variances are the eigenvalues.
- **Spectral clustering** (mentioned briefly in Part G): clusters are found via eigenvectors of a graph Laplacian.
- **Ridge regression** (Chapter 20): the SVD view explains exactly what ridge does to the spectrum.
- **Convergence of optimization** (Chapter 17): the eigenvalues of the Hessian of the loss determine how fast gradient descent converges and which step sizes are stable.
- **Markov chains and PageRank** (out of scope, but a famous application): the stationary distribution is the eigenvector of the transition matrix with eigenvalue 1.

---

## 14.13 Exercises

1. **Definition check.** State, in your own words, what it means for $\mathbf{v}$ to be an eigenvector of $A$ with eigenvalue $\lambda$.

2. **Eigenvalues of a diagonal matrix.** Find the eigenvalues and eigenvectors of $D = \begin{pmatrix} 7 & 0 & 0 \\ 0 & -2 & 0 \\ 0 & 0 & 5 \end{pmatrix}$.

3. **2x2 by hand.** Find the eigenvalues and eigenvectors of $A = \begin{pmatrix} 2 & 1 \\ 1 & 2 \end{pmatrix}$. Show every step.

4. **Symmetric eigenvectors are orthogonal.** For your answer to problem 3, verify that the two eigenvectors are orthogonal.

5. **A non-symmetric example.** Find the eigenvalues and eigenvectors of $B = \begin{pmatrix} 5 & 1 \\ 0 & 3 \end{pmatrix}$. Are the eigenvectors orthogonal? Should they be?

6. **Complex eigenvalues.** Compute the characteristic polynomial of the 90° rotation $R = \begin{pmatrix} 0 & -1 \\ 1 & 0 \end{pmatrix}$. What are its roots? Geometrically, why does $R$ have no real eigenvectors?

7. **The trace.** The **trace** of a matrix is the sum of its diagonal entries: $\text{tr}(A) = \sum A_{ii}$. Show, using your 2x2 example from problem 3, that $\text{tr}(A) = \lambda_1 + \lambda_2$. (This is a general fact: trace equals sum of eigenvalues.)

8. **Determinant and eigenvalues.** Similarly, show that $\det(A) = \lambda_1 \lambda_2$ for your matrix from problem 3. (This is also general: determinant equals product of eigenvalues.)

9. **Singular = zero eigenvalue.** Find the eigenvalues of $C = \begin{pmatrix} 1 & 2 \\ 2 & 4 \end{pmatrix}$. Notice one of them is zero. Identify the corresponding eigenvector. Explain why this eigenvector is also in the null space of $C$.

10. **PCA intuition.** Suppose your $2 \times 2$ data covariance matrix is $\Sigma = \begin{pmatrix} 4 & 0 \\ 0 & 1 \end{pmatrix}$. Without doing any computation, what are the principal components and the variances? In what direction does the data vary the most?

11. **A tilted PCA.** Now $\Sigma = \begin{pmatrix} 2 & 1 \\ 1 & 2 \end{pmatrix}$. Find the principal components and their variances. What does this tell you about the shape of the data cloud?

12. **SVD shape arithmetic.** $X$ is $10{,}000 \times 50$. What are the shapes of $U$, $\Sigma$, $V$ in the (compact) SVD $X = U \Sigma V^T$? How many singular values does $X$ have at most?

13. **SVD for low-rank approximation.** Your matrix $X$ has singular values $\sigma_1 = 100, \sigma_2 = 80, \sigma_3 = 5, \sigma_4 = 1, \sigma_5 = 0.2$. To approximate $X$ "well" with a low-rank factorisation, how many components would you keep, and why?

14. **A connection between PCA and SVD.** Why is computing PCA via SVD of the (centered) data matrix $X$ usually more numerically stable than computing eigenvectors of $X^T X$ directly?

<details>
<summary>Answers</summary>

1. $\mathbf{v}$ is a non-zero vector that $A$ maps to a scalar multiple of itself: $A \mathbf{v} = \lambda \mathbf{v}$. Geometrically, the direction of $\mathbf{v}$ is preserved by $A$; only its magnitude changes (by a factor of $\lambda$, possibly negative).

2. Eigenvalues are the diagonal entries: $7, -2, 5$. Eigenvectors are the standard basis vectors: $\mathbf{e}_1, \mathbf{e}_2, \mathbf{e}_3$.

3. $A - \lambda I = \begin{pmatrix} 2-\lambda & 1 \\ 1 & 2-\lambda \end{pmatrix}$. $\det = (2-\lambda)^2 - 1 = \lambda^2 - 4\lambda + 3 = (\lambda - 1)(\lambda - 3)$. Eigenvalues: $1, 3$. For $\lambda = 3$: $(A - 3I)\mathbf{v} = \begin{pmatrix} -1 & 1 \\ 1 & -1 \end{pmatrix}\mathbf{v} = \mathbf{0}$, giving $v_2 = v_1$; pick $\mathbf{v}_1 = (1, 1)$. For $\lambda = 1$: $\begin{pmatrix} 1 & 1 \\ 1 & 1 \end{pmatrix}\mathbf{v} = \mathbf{0}$, giving $v_2 = -v_1$; pick $\mathbf{v}_2 = (1, -1)$.

4. $\mathbf{v}_1 \cdot \mathbf{v}_2 = (1)(1) + (1)(-1) = 0$. Orthogonal. (As expected; $A$ is symmetric.)

5. $\det(B - \lambda I) = (5 - \lambda)(3 - \lambda) - 0 = 0$, so $\lambda = 5, 3$. For $\lambda = 5$: $\begin{pmatrix} 0 & 1 \\ 0 & -2 \end{pmatrix}\mathbf{v} = \mathbf{0}$ gives $v_2 = 0$, so $\mathbf{v}_1 = (1, 0)$. For $\lambda = 3$: $\begin{pmatrix} 2 & 1 \\ 0 & 0 \end{pmatrix}\mathbf{v} = \mathbf{0}$ gives $v_1 = -v_2/2$, so $\mathbf{v}_2 = (1, -2)$ (or $(-1, 2)$). Orthogonality check: $(1)(1) + (0)(-2) = 1 \neq 0$. Not orthogonal. Not expected to be — $B$ is not symmetric.

6. $\det(R - \lambda I) = \lambda^2 + 1$. Roots: $\pm i$. Geometrically: $R$ rotates *every* nonzero real vector by 90°, so no real vector is mapped to a scalar multiple of itself.

7. $\text{tr}(A) = 2 + 2 = 4 = 1 + 3 = \lambda_1 + \lambda_2$. ✓

8. $\det(A) = 4 - 1 = 3 = 1 \cdot 3 = \lambda_1 \lambda_2$. ✓

9. $\det(C - \lambda I) = (1-\lambda)(4-\lambda) - 4 = \lambda^2 - 5\lambda$. Eigenvalues: $0, 5$. For $\lambda = 0$: $\begin{pmatrix} 1 & 2 \\ 2 & 4 \end{pmatrix}\mathbf{v} = \mathbf{0}$ gives $v_1 = -2 v_2$, so $\mathbf{v} = (2, -1)$ (or $(-2, 1)$). The eigenvector for eigenvalue $0$ is precisely a non-zero vector that $C$ sends to $\mathbf{0}$ — i.e., a non-zero element of the null space. Existence of a zero eigenvalue is equivalent to the null space being non-trivial, equivalent to $C$ being singular.

10. Principal components are $(1, 0)$ (eigenvalue 4) and $(0, 1)$ (eigenvalue 1). The data varies most along the x-direction, with variance 4 there and variance 1 along y.

11. $\Sigma - \lambda I = \begin{pmatrix} 2-\lambda & 1 \\ 1 & 2-\lambda \end{pmatrix}$, $\det = (2-\lambda)^2 - 1 = (\lambda - 1)(\lambda - 3)$. Eigenvalues: $\lambda_1 = 3, \lambda_2 = 1$. Eigenvectors: $\mathbf{u}_1 = (1, 1)/\sqrt{2}$ (the "northeast" direction), $\mathbf{u}_2 = (1, -1)/\sqrt{2}$ ("northwest"). The data cloud is an ellipse tilted at 45°, with the long axis pointing northeast (variance 3) and the short axis pointing northwest (variance 1). PCA's first component captures three times more variance than the second.

12. Compact SVD: $U$ is $10000 \times 50$, $\Sigma$ is $50 \times 50$ diagonal (or as a vector of length 50), $V$ is $50 \times 50$. At most 50 singular values (rank can't exceed the smaller dimension).

13. Keep 2 components. The first two singular values are 100 and 80 — large. The next three drop to 5, 1, 0.2 — a sharp "elbow" in the spectrum. Discarding components 3+ loses very little of the signal and captures the dominant 2-dimensional structure.

14. Forming $X^T X$ squares the condition number — small singular values become tiny (squared), and tiny eigenvalues are computed less accurately. SVD operates on $X$ directly without that squaring step, so its numerical precision is much better, especially when $X$ is nearly rank-deficient.

</details>
