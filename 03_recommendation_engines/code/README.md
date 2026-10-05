# Topic 03 — Code

Runnable Python examples for recommendation engine algorithms. Each file is self-contained — runs on a laptop in seconds-to-minutes — and intentionally minimal. The purpose is to illustrate mechanics, not to be production-grade.

## Setup

The project's `.venv` at `/Users/vr/Code/Career_upskill/.venv` already has Python 3.11. Install requirements:

```bash
/Users/vr/Code/Career_upskill/.venv/bin/pip install -r requirements.txt
```

## Files

| File | Module | What it shows |
|------|--------|---------------|
| `05_content_based.py` | 5 | TF-IDF + cosine; modern dense-embedding variant |
| `06_neighborhood_cf.py` | 6 | Item-based kNN on a small ratings matrix |
| `07_matrix_factorization.py` | 7 | SGD-trained MF with biases + ALS sketch |
| `07b_bpr.py` | 7 | BPR loss with negative sampling |
| `08_dlrm_lite.py` | 8 | Tiny DLRM-style ranker in PyTorch |
| `09_sasrec.py` | 9 | Toy SASRec sequential recommender |
| `10_two_tower.py` | 10 | Two-tower retrieval with in-batch negatives + LogQ |
| `11_lightgcn.py` | 11 | Minimal LightGCN with sparse adjacency propagation |
| `12_generative_rec.py` | 12 | Tiny generative recommender (transformer next-item) |
| `25_auction_sim.py` | 25 | GSP vs VCG vs first-price auction simulator |
| `27_pacing_pid.py` | 27 | PID budget pacing controller demo |
| `28_mmm_demo.py` | 28 | Marketing-mix-modeling demo with adstock and saturation |
| `bandit_thompson.py` | 16 | Thompson sampling contextual bandit |

## Notes

- All code uses common libraries: NumPy, scikit-learn, PyTorch, SciPy.
- No GPU required for any example.
- Real industrial code is 100-1000× the complexity. These are mental-model demonstrators.
