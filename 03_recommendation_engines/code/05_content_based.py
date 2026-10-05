"""Module 5 — Content-based filtering.

TF-IDF + cosine, plus a dense-embedding variant using sentence-transformers.
Run:  python 05_content_based.py
"""
from __future__ import annotations
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def tfidf_content_recommender(items: list[tuple[str, str]], liked_ids: set[str], top_n: int = 5):
    item_ids = [i[0] for i in items]
    texts = [i[1] for i in items]
    vec = TfidfVectorizer(stop_words="english", min_df=1)
    X = vec.fit_transform(texts)
    liked_idx = [item_ids.index(i) for i in liked_ids]
    user_vec = X[liked_idx].mean(axis=0)
    sims = cosine_similarity(np.asarray(user_vec), X).ravel()
    ranked = sorted(zip(item_ids, sims), key=lambda x: -x[1])
    return [r for r in ranked if r[0] not in liked_ids][:top_n]


def dense_content_recommender(items, liked_ids, top_n=5, model_name="all-MiniLM-L6-v2"):
    """Same idea with a pretrained sentence encoder. Falls back gracefully if sentence-transformers isn't installed."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("(sentence-transformers not installed; skipping dense variant)")
        return None
    enc = SentenceTransformer(model_name)
    embs = enc.encode([t for _, t in items], normalize_embeddings=True)
    ids = [i for i, _ in items]
    liked_idx = [ids.index(i) for i in liked_ids]
    user_vec = embs[liked_idx].mean(axis=0, keepdims=True)
    sims = (embs @ user_vec.T).ravel()
    ranked = sorted(zip(ids, sims), key=lambda x: -x[1])
    return [r for r in ranked if r[0] not in liked_ids][:top_n]


if __name__ == "__main__":
    items = [
        ("m1", "action thriller with car chases and explosions"),
        ("m2", "romantic comedy in paris"),
        ("m3", "espionage spy thriller in cold war europe"),
        ("m4", "slapstick comedy with talking animals"),
        ("m5", "intense action movie with martial arts"),
        ("m6", "documentary about world war two espionage"),
        ("m7", "feel-good romantic story in tuscany"),
    ]
    liked = {"m1", "m5"}  # action / thriller fan

    print("=== TF-IDF top-5 ===")
    for item, score in tfidf_content_recommender(items, liked):
        print(f"  {item}  {score:.3f}")

    print("\n=== Dense embeddings (sentence-transformers) top-5 ===")
    dense_res = dense_content_recommender(items, liked)
    if dense_res:
        for item, score in dense_res:
            print(f"  {item}  {score:.3f}")
