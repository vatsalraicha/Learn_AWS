# Module 7 — Matrix Factorization & FM Family

> The dominant recsys approach from ~2009 to ~2017. Still ships in production for the small-data parts of every company; still the strongest baseline against new deep models; still the conceptual building block of two-tower retrieval. Three names define the era: Koren, Rendle, Hu/Koren/Volinsky.

---

## 1. The factorization hypothesis

The sparse user-item interaction matrix `R ∈ R^{|U|×|I|}` is approximately low-rank: there exist `P ∈ R^{|U|×k}` and `Q ∈ R^{|I|×k}` (`k ≪ |U|, |I|`) such that

```
R̂_ui  =  μ + b_u + b_i + p_u · q_i  ≈  R_ui
```

This is *not* the same as truncated SVD: standard SVD requires a complete matrix and `R` is mostly missing. The "MF for recommenders" approach learns `P, Q` from the observed entries only, treating missing values as missing (not zero).

`μ` is the global mean rating; `b_u, b_i` are user/item biases (Module 2 §2.2).

---

## 2. The history in one paragraph

- **2006**: Simon Funk publishes his Netflix Prize blog post — SGD on the bias + factor model. The "SVD" name sticks even though it isn't really SVD.
- **2007-2008**: Koren extends with **SVD++** (incorporating implicit signal via the set of items the user has interacted with) and **timeSVD++** (bias terms that drift over time). These remain the strongest single MF models on rating prediction.
- **2008**: Hu, Koren, Volinsky publish the ALS-implicit paper. Implicit feedback CF becomes practical.
- **2009**: Rendle introduces **BPR** — Bayesian Personalized Ranking. Top-N implicit becomes a pairwise ranking problem.
- **2010**: Rendle introduces **Factorization Machines** — generalize MF to handle arbitrary feature interactions.
- **2016**: Juan et al. introduce **Field-aware FM** for ads CTR; wins multiple Kaggle competitions.
- **2017-onward**: Deep models gradually displace MF for top-N. But MF survives as a baseline that's tough to beat with proper tuning (see Rendle 2020 "Neural Collaborative Filtering vs. Matrix Factorization").

---

## 3. SGD-trained MF (the Netflix Prize version)

```
min  Σ_{(u,i) ∈ Ω}  (R_ui − μ − b_u − b_i − p_u · q_i)²  +  λ (‖P‖² + ‖Q‖² + b²)
```

Gradient updates (one example at a time):

```
e_ui = R_ui − R̂_ui
b_u  ← b_u  + η (e_ui − λ b_u)
b_i  ← b_i  + η (e_ui − λ b_i)
p_u  ← p_u  + η (e_ui · q_i − λ p_u)
q_i  ← q_i  + η (e_ui · p_u − λ q_i)
```

Typical config: `k = 50-200`, `η = 0.005`, `λ = 0.02`, 20-50 epochs.

### 3.1 SVD++

Adds an implicit factor: each user has an additional vector `y_j` for each item they implicitly interacted with (browsed, watched the trailer):

```
R̂_ui = μ + b_u + b_i + (p_u + |N(u)|^{-1/2} Σ_{j ∈ N(u)} y_j) · q_i
```

Strong on Netflix Prize. Inspired the "user representation = aggregate of item embeddings" pattern that two-tower retrieval still uses.

### 3.2 timeSVD++

User biases, item biases, and user factors are all functions of time. Models user drift ("user u used to be a horror fan; in 2024 they're documentary-heavy").

Used to be the SOTA on Netflix data. Replaced by sequential models (Module 9) that model time more directly.

---

## 4. ALS — Alternating Least Squares

For implicit feedback the standard solver. Hu, Koren, Volinsky 2008.

The objective:

```
p_ui = 1 if R_ui > 0 else 0
c_ui = 1 + α · R_ui                      # confidence

L = Σ_{u,i} c_ui (p_ui − x_u · y_i)²  + λ (‖X‖² + ‖Y‖²)
```

### 4.1 The trick

Sum is over **all** `(u, i)` — even unobserved ones (where `c_ui = 1`). A naïve implementation is O(|U|·|I|·k) per epoch. The Hu et al. trick reduces it to O((Σ |I_u|) · k² + |U| · k³) by precomputing `YᵀY` (an `k × k` matrix that summarizes the "no-signal" mass).

For each user `u`, the optimal `x_u` given fixed `Y` is closed-form:

```
x_u = (YᵀCᵘY + λI)⁻¹ YᵀCᵘp(u)
```

where `Cᵘ` is the diagonal matrix of confidences for user `u`. Crucially, `YᵀCᵘY = YᵀY + Yᵀ(Cᵘ - I)Y`, and only `|I_u|` rows of `Cᵘ - I` are non-zero. So we cache `YᵀY` once per iteration and update only the small correction.

Alternate between fixing `Y` and solving for `X`, and vice versa. Converges in 10-30 iterations.

### 4.2 The `implicit` library

Production-quality Python implementation of ALS-implicit, BPR, LMF, and similar. Supports both CPU and GPU. Used in many startups. Reference baseline for music, e-commerce, B2B recsys.

```python
import implicit
import scipy.sparse as sp

# user_item: csr_matrix, rows = users, cols = items, values = play counts
model = implicit.als.AlternatingLeastSquares(
    factors=64, regularization=0.01, alpha=15, iterations=20
)
model.fit(user_item)

# top-10 for user 42
ids, scores = model.recommend(42, user_item[42], N=10)
```

### 4.3 Where ALS-implicit still wins

- **Sparse implicit data, no rich features**: small e-commerce, small media catalogs.
- **Offline batch recommendation**: nightly nature; no online updating.
- **Strong baseline for benchmarking**: harder to beat than papers claim.

---

## 5. BPR — Bayesian Personalized Ranking

Rendle et al. 2009. The "give up on rating prediction, optimize a ranking criterion" move.

### 5.1 The loss

For each user `u`, sample a positive item `i ∈ I_u⁺` and a negative item `j ∉ I_u⁺`:

```
L_BPR = − Σ_{(u, i, j)}  ln σ(x̂_ui − x̂_uj)  +  λ Θ²
```

The model `x̂_ui` can be MF, FM, deep — BPR is just the loss.

Gradient (one triple):

```
∂L/∂Θ = − σ(−(x̂_ui − x̂_uj)) · ∂(x̂_ui − x̂_uj)/∂Θ
```

For MF, `∂(x̂_ui − x̂_uj)/∂q_i = p_u`, `∂(.)/∂q_j = -p_u`, `∂(.)/∂p_u = (q_i − q_j)`.

### 5.2 Why BPR works

The loss is approximately AUC. Pairs where the model is most wrong contribute the largest gradient; pairs that are already correct contribute near-zero. The model focuses learning on the ranking margin.

### 5.3 Negative sampling matters

The whole gradient depends on which `j` you sample.

- **Uniform**: weak signal; most negatives are easy.
- **Popularity-proportional** (Mikolov 2013, `q(j) ∝ count(j)^0.75`): standard recipe.
- **Hard negatives** (item with highest current score that isn't in positives): faster convergence, occasional overfitting.

LightFM implements BPR with a related pairwise loss (WARP — Weighted Approximate Rank Pairwise, Weston et al. 2011) that adapts negative weights based on how many negatives must be tried before finding a violator.

---

## 6. Factorization Machines (Rendle 2010)

The big idea: stop hard-coding "user × item" interaction. Model **every pairwise interaction** among arbitrary features.

```
ŷ(x) = w_0  +  Σ_i w_i x_i  +  Σ_{i<j} ⟨v_i, v_j⟩ x_i x_j
```

Each of the `n` features (e.g., user_id, item_id, time-of-day, device, country, last_genre, ...) has a `k`-dim latent vector `v_i`. The pairwise interaction is the dot product of latent vectors.

### 6.1 The fast-evaluation identity

The naive sum has `O(n²)` terms. The clever identity (Module 2 §2.5):

```
Σ_{i<j} ⟨v_i, v_j⟩ x_i x_j  =  (1/2) Σ_f [(Σ_i v_{i,f} x_i)² − Σ_i v_{i,f}² x_i²]
```

This is `O(n · k)` — linear. Critical for the algorithm's practicality.

### 6.2 Why FM generalizes MF

- If features are one-hot user-id and one-hot item-id, FM reduces to biased MF.
- Add a time-of-day feature → FM learns time-conditional taste interactions.
- Add a content feature (genre) → FM gets a content-aware MF for free.

### 6.3 Field-aware FM (FFM)

Each feature `i` has *one embedding per field of its interaction partner*. So `user_id` has separate latent vectors when interacting with `item_id` vs `time_of_day` vs `device`:

```
ŷ_FFM(x) = w_0 + Σ w_i x_i + Σ_{i<j} ⟨v_{i,f(j)}, v_{j,f(i)}⟩ x_i x_j
```

Where `f(j)` is the field of feature `j`.

Won the Criteo Display Advertising Challenge (2014, Avazu (2015), Criteo (2017)). The Kaggle CTR-champion technique for years.

Cost: `O(n · k · |fields|)` parameters vs FM's `O(n · k)`. Heavier but more expressive.

### 6.4 Production status of FM/FFM

- **2014-2019**: dominant ads CTR baselines.
- **2017+**: subsumed by deep models (DeepFM, xDeepFM — Module 8).
- **Today**: pure FM still in production at smaller ads companies; FFM mostly retired.
- The deep-FM hybrid (FM + DNN with shared embeddings) is the canonical 2017-2022 industrial pattern.

---

## 7. The 2020 reproducibility shock

Rendle, Krichene, Zhang, Anderson 2020: "Neural Collaborative Filtering vs. Matrix Factorization Revisited" (RecSys 2020). The key finding:

> **NCF** (Neural Collaborative Filtering, He et al. 2017, 7000+ citations) was supposed to beat plain dot-product MF. **It doesn't, when MF is tuned properly.**

This was the loudest signal in a broader 2019-2020 reproducibility wave (Ferrari Dacrema et al. 2019, Sun et al. 2020) showing many deep recsys claims didn't replicate when classical baselines were tuned.

Practical take-aways:
- Always tune MF / ALS / BPR carefully before claiming a deep model wins.
- The performance gap between classical and deep is small on sparse data; it widens with more features (where deep models shine).
- Architecture innovations matter less than data quality, negative sampling strategy, regularization, and feature engineering.

---

## 8. Sample code: matrix factorization with SGD from scratch

(See [`code/07_matrix_factorization.py`](code/07_matrix_factorization.py) for a runnable version with biases and explicit ALS.)

```python
import numpy as np

n_users, n_items, k = 4, 5, 8
np.random.seed(0)
P = np.random.normal(0, 0.1, (n_users, k))
Q = np.random.normal(0, 0.1, (n_items, k))
b_u = np.zeros(n_users)
b_i = np.zeros(n_items)
mu  = 3.5

# (user, item, rating) tuples
ratings = [
    (0, 0, 5), (0, 1, 3), (0, 3, 1), (0, 4, 4),
    (1, 0, 4), (1, 3, 1), (1, 4, 5),
    (2, 0, 1), (2, 1, 1), (2, 3, 5),
    (3, 2, 5), (3, 3, 4), (3, 4, 1),
]

lr, reg, epochs = 0.01, 0.02, 200
for epoch in range(epochs):
    np.random.shuffle(ratings)
    sse = 0
    for u, i, r in ratings:
        pred = mu + b_u[u] + b_i[i] + P[u] @ Q[i]
        err  = r - pred
        sse += err ** 2

        # Update
        b_u[u] += lr * (err - reg * b_u[u])
        b_i[i] += lr * (err - reg * b_i[i])
        P[u]   += lr * (err * Q[i] - reg * P[u])
        Q[i]   += lr * (err * P[u] - reg * Q[i])

    if epoch % 50 == 0:
        rmse = (sse / len(ratings)) ** 0.5
        print(f"Epoch {epoch:3d}  RMSE={rmse:.4f}")

# Predict user 0's rating for item 2 (which they haven't rated)
pred = mu + b_u[0] + b_i[2] + P[0] @ Q[2]
print(f"Predicted rating user 0 → item 2: {pred:.2f}")
```

---

## 9. Sanity check

1. Why is "SVD for recommenders" technically a misnomer?
2. In the Hu-Koren-Volinsky ALS-implicit formulation, what is `c_ui` for an item the user never interacted with, and what does that contribute to the objective?
3. Explain in one sentence why BPR's loss is sometimes called "AUC-like".
4. FM has `O(n · k)` parameters but expresses every pairwise interaction. How is that possible?
5. The 2020 NCF reproducibility paper claimed plain MF beats NCF when properly tuned. What's the broader lesson for evaluating new recsys ideas?
6. Your team replaces ALS with a DLRM-style ranker and AUC goes up 0.5% offline. Why might this not translate to an online win?
