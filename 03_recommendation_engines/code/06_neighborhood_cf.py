"""Module 6 — Item-based kNN collaborative filtering.

Item-item cosine similarity over a small ratings matrix.
Run:  python 06_neighborhood_cf.py
"""
from __future__ import annotations
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


def item_based_knn_predict(R: np.ndarray, target_user: int, target_item: int, k: int = 3) -> float:
    """Predict R[target_user, target_item] from k most similar items the user has rated."""
    item_sim = cosine_similarity(R.T)
    np.fill_diagonal(item_sim, 0.0)

    user_ratings = R[target_user]
    rated_mask = user_ratings > 0
    sims_to_target = item_sim[target_item] * rated_mask  # only items user has rated
    top_k = np.argsort(sims_to_target)[::-1][:k]
    weights = item_sim[target_item, top_k]
    ratings = user_ratings[top_k]
    if np.abs(weights).sum() == 0:
        return float(np.mean(user_ratings[rated_mask])) if rated_mask.any() else 0.0
    return float((weights * ratings).sum() / np.abs(weights).sum())


if __name__ == "__main__":
    # users (rows) × items (cols); 0 = unrated
    R = np.array([
        [5, 3, 0, 1, 4, 0],
        [4, 0, 0, 1, 5, 2],
        [1, 1, 0, 5, 0, 4],
        [0, 0, 5, 4, 1, 5],
        [4, 4, 2, 0, 5, 3],
    ])
    users = ["alice", "bob", "carol", "dave", "eve"]
    items = [f"m{i+1}" for i in range(R.shape[1])]

    print("Item-item cosine similarities:")
    sim = cosine_similarity(R.T)
    np.fill_diagonal(sim, 0.0)
    print("    " + "   ".join(items))
    for i, row in enumerate(sim):
        print(f"{items[i]}  " + "  ".join(f"{v:5.2f}" for v in row))

    print("\nPredictions for unrated cells (top-K=3):")
    for u, user in enumerate(users):
        for it in range(R.shape[1]):
            if R[u, it] == 0:
                pred = item_based_knn_predict(R, u, it, k=3)
                print(f"  {user} → {items[it]}: {pred:.2f}")
