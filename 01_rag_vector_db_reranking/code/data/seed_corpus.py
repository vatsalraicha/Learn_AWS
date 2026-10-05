"""Tiny synthetic corpus for the notebooks. Public, embeddable, no licensing concerns.

Returns a list of (chunk_id, text, metadata) tuples covering a few different domains
so retrieval results are visibly differentiable.
"""

from typing import List, Tuple, Dict

CORPUS: List[Tuple[str, str, Dict]] = [
    # --- HR policy chunks (the "refund / leave / 401k" style we keep using as examples) ---
    (
        "hr_001",
        "Acme Corp 401(k) Plan: The company matches 100% of employee contributions up to 4% of "
        "eligible compensation. Vesting is graded over 3 years: 33% after year 1, 66% after year 2, "
        "100% after year 3. Match contributions are made each pay period.",
        {"doc_type": "policy", "topic": "401k", "year": 2024, "filename": "401k_plan_2024.pdf"},
    ),
    (
        "hr_002",
        "Acme Corp Refund Policy for Q4 2024: B2B customers may request a refund within 30 days of "
        "purchase. Refunds for annual contracts are pro-rated. Promotional discount codes are "
        "non-refundable except where required by law.",
        {"doc_type": "policy", "topic": "refund", "year": 2024, "filename": "refund_policy_q4_2024.pdf"},
    ),
    (
        "hr_003",
        "Acme Corp Refund Policy for Q1 2023: All sales are final after 14 days. Promotional "
        "discounts cannot be combined with refund requests. This policy was superseded by the "
        "Q4 2024 update.",
        {"doc_type": "policy", "topic": "refund", "year": 2023, "filename": "refund_policy_q1_2023.pdf"},
    ),
    (
        "hr_004",
        "Parental leave at Acme: Birth parents receive 16 weeks of paid leave. Non-birth parents "
        "and adoptive parents receive 8 weeks. Leave must be taken within 12 months of the qualifying event.",
        {"doc_type": "policy", "topic": "leave", "year": 2024, "filename": "parental_leave_2024.pdf"},
    ),
    # --- Technical chunks (RAG-related, useful for self-referential tests) ---
    (
        "tech_001",
        "BM25 is a probabilistic ranking function used in information retrieval. It rewards term "
        "frequency in a document while down-weighting common terms via inverse document frequency. "
        "It is a 1994-vintage algorithm but remains hard to beat for keyword-heavy queries.",
        {"doc_type": "technical", "topic": "retrieval", "filename": "bm25_overview.md"},
    ),
    (
        "tech_002",
        "HNSW (Hierarchical Navigable Small World) is a graph-based approximate nearest neighbor "
        "index. It builds a multi-layer graph where higher layers have sparser connections for "
        "long-range hops. Tuning parameters include M (graph degree), ef_construction, and ef_search.",
        {"doc_type": "technical", "topic": "vector_db", "filename": "hnsw_explained.md"},
    ),
    (
        "tech_003",
        "Reciprocal Rank Fusion (RRF) combines rankings from multiple retrievers without requiring "
        "score normalization. The score for a document is the sum of 1/(k + rank_i) across all "
        "retrievers, with k typically set to 60.",
        {"doc_type": "technical", "topic": "retrieval", "filename": "rrf_algorithm.md"},
    ),
    (
        "tech_004",
        "A cross-encoder reranker takes a (query, document) pair as joint input and produces a "
        "single relevance score. Unlike bi-encoders, cross-encoders cannot be precomputed but offer "
        "much higher accuracy. They are typically used as a second stage on top of a fast bi-encoder retriever.",
        {"doc_type": "technical", "topic": "reranking", "filename": "cross_encoder.md"},
    ),
    # --- Distractors / negatives ---
    (
        "dist_001",
        "Quarterly revenue growth in Q4 was driven by enterprise renewals and a successful EMEA "
        "expansion. Operating margin improved by 280 basis points year-over-year.",
        {"doc_type": "financial", "topic": "earnings", "year": 2024, "filename": "q4_2024_earnings.pdf"},
    ),
    (
        "dist_002",
        "The new espresso machine in the office kitchen requires the bean hopper to be refilled "
        "weekly. Descaling should be performed monthly. The maintenance log is on the kitchen counter.",
        {"doc_type": "ops", "topic": "facilities", "filename": "kitchen_notes.txt"},
    ),
    (
        "dist_003",
        "Self-attention is a mechanism in transformer architectures where each token computes "
        "attention weights against all other tokens in the sequence. Multi-head attention runs "
        "this in parallel across multiple subspaces. Introduced in 'Attention Is All You Need' (2017).",
        {"doc_type": "technical", "topic": "ml_theory", "filename": "self_attention.md"},
    ),
]


def get_corpus() -> List[Tuple[str, str, Dict]]:
    """Return the corpus as (id, text, metadata) tuples."""
    return CORPUS


def get_eval_queries() -> List[Tuple[str, str, List[str]]]:
    """Eval queries for the notebooks: (query, expected_topic, gold_chunk_ids)."""
    return [
        (
            "What is our 401k match policy?",
            "401k",
            ["hr_001"],
        ),
        (
            "Can a B2B customer get a refund after 30 days for a Q4 2024 purchase?",
            "refund",
            ["hr_002"],
        ),
        (
            "How does HNSW work?",
            "vector_db",
            ["tech_002"],
        ),
        (
            "Why use a cross-encoder reranker on top of vector search?",
            "reranking",
            ["tech_004", "tech_003"],
        ),
        (
            "How many weeks of parental leave for adoptive parents?",
            "leave",
            ["hr_004"],
        ),
        (
            "What does RRF do?",
            "retrieval",
            ["tech_003"],
        ),
    ]


if __name__ == "__main__":
    corpus = get_corpus()
    queries = get_eval_queries()
    print(f"Corpus: {len(corpus)} chunks across {len(set(c[2]['doc_type'] for c in corpus))} doc types")
    print(f"Eval queries: {len(queries)}")
