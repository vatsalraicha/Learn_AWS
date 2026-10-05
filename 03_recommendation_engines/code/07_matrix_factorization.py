"""Module 7 — Matrix factorization with SGD + biases (Funk SVD style).

Run:  python 07_matrix_factorization.py
"""
from __future__ import annotations
import numpy as np


def train_mf_sgd(ratings, n_users, n_items, k=8, lr=0.01, reg=0.02, epochs=200, seed=0):
    rng = np.random.default_rng(seed)
    P = rng.normal(0, 0.1, (n_users, k))
    Q = rng.normal(0, 0.1, (n_items, k))
    b_u = np.zeros(n_users)
    b_i = np.zeros(n_items)
    mu = float(np.mean([r for _, _, r in ratings]))

    for epoch in range(epochs):
        rng.shuffle(ratings)
        sse = 0.0
        for u, i, r in ratings:
            pred = mu + b_u[u] + b_i[i] + P[u] @ Q[i]
            err = r - pred
            sse += err ** 2
            b_u[u] += lr * (err - reg * b_u[u])
            b_i[i] += lr * (err - reg * b_i[i])
            P_u_old = P[u].copy()
            P[u] += lr * (err * Q[i] - reg * P[u])
            Q[i] += lr * (err * P_u_old - reg * Q[i])

        if epoch % 50 == 0 or epoch == epochs - 1:
            rmse = (sse / len(ratings)) ** 0.5
            print(f"Epoch {epoch:3d}  RMSE={rmse:.4f}")

    return mu, b_u, b_i, P, Q


def predict(mu, b_u, b_i, P, Q, u, i):
    return mu + b_u[u] + b_i[i] + P[u] @ Q[i]


if __name__ == "__main__":
    # 4 users, 5 items
    ratings = [
        (0, 0, 5), (0, 1, 3), (0, 3, 1), (0, 4, 4),
        (1, 0, 4), (1, 3, 1), (1, 4, 5),
        (2, 0, 1), (2, 1, 1), (2, 3, 5),
        (3, 2, 5), (3, 3, 4), (3, 4, 1),
    ]
    mu, b_u, b_i, P, Q = train_mf_sgd(list(ratings), n_users=4, n_items=5)

    print("\nPredictions for unrated cells:")
    rated = {(u, i) for u, i, _ in ratings}
    for u in range(4):
        for i in range(5):
            if (u, i) not in rated:
                p = predict(mu, b_u, b_i, P, Q, u, i)
                print(f"  user {u} → item {i}: {p:.2f}")
