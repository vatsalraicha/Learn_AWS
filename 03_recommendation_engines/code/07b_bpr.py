"""Module 7 — Bayesian Personalized Ranking (BPR) for implicit feedback.

Run:  python 07b_bpr.py
"""
from __future__ import annotations
import numpy as np


def sample_triple(user_items, n_items, rng):
    while True:
        u = rng.integers(0, len(user_items))
        if not user_items[u]:
            continue
        i = rng.choice(list(user_items[u]))
        j = rng.integers(0, n_items)
        if j not in user_items[u]:
            return u, i, j


def train_bpr(user_items, n_users, n_items, k=16, lr=0.05, reg=0.01, n_steps=20000, seed=0):
    rng = np.random.default_rng(seed)
    P = rng.normal(0, 0.1, (n_users, k))
    Q = rng.normal(0, 0.1, (n_items, k))
    b_i = np.zeros(n_items)

    def sigmoid(x):
        return 1.0 / (1.0 + np.exp(-x))

    for step in range(n_steps):
        u, i, j = sample_triple(user_items, n_items, rng)
        x_uij = (P[u] @ Q[i] + b_i[i]) - (P[u] @ Q[j] + b_i[j])
        sig = sigmoid(-x_uij)  # = 1 - sigmoid(x_uij); gradient direction

        P[u]   += lr * (sig * (Q[i] - Q[j]) - reg * P[u])
        Q[i]   += lr * (sig * P[u] - reg * Q[i])
        Q[j]   += lr * (-sig * P[u] - reg * Q[j])
        b_i[i] += lr * (sig - reg * b_i[i])
        b_i[j] += lr * (-sig - reg * b_i[j])

    return P, Q, b_i


if __name__ == "__main__":
    # 6 users, 10 items; each user "likes" 2-4 items
    rng = np.random.default_rng(0)
    n_users, n_items = 6, 10
    user_items = [set(rng.choice(n_items, size=rng.integers(2, 5), replace=False).tolist())
                  for _ in range(n_users)]
    print("User → positive items:")
    for u, s in enumerate(user_items):
        print(f"  user {u}: {sorted(s)}")

    P, Q, b_i = train_bpr(user_items, n_users, n_items, n_steps=30000)

    print("\nTop-3 ranked items per user (excluding already-positive):")
    for u in range(n_users):
        scores = P[u] @ Q.T + b_i
        for pos in user_items[u]:
            scores[pos] = -np.inf
        top = np.argsort(scores)[::-1][:3]
        print(f"  user {u}: {top.tolist()}  scores={scores[top].round(2).tolist()}")
