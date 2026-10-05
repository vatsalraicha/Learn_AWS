# Code companion — RAG, Vector DBs & Reranking

Hands-on notebooks paired with the conceptual modules. Each script is **runnable as both a Python script and a Jupyter notebook** via the `# %%` cell-marker convention (VS Code recognizes these natively; `jupytext` can convert).

## Setup

### One-time: create venv and install

```bash
# From /Users/vr/Code/Career_upskill (the main repo, NOT the worktree)
python3.11 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r .claude/worktrees/confident-banzai-454694/topics/01_rag_vector_db_reranking/code/requirements.txt
```

Or with conda:

```bash
conda create -n career_upskill python=3.11 -y
conda activate career_upskill
pip install -r requirements.txt
```

### API keys you'll need

Create a `.env` in the **main repo root** (gitignored — already in your `.gitignore`):

```bash
# Required for most notebooks
ANTHROPIC_API_KEY=sk-ant-...

# Optional — if you want to compare embedders / rerankers
VOYAGE_API_KEY=...
COHERE_API_KEY=...

# Optional — for parsing
LLAMA_CLOUD_API_KEY=...     # LlamaParse
MISTRAL_API_KEY=...         # Mistral OCR

# Optional — observability
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_SECRET_KEY=...
LANGFUSE_HOST=https://cloud.langfuse.com
```

The scripts use `python-dotenv` to load these.

### Key design choices

- **No OpenAI.** Anthropic Claude is the default LLM; Voyage/Cohere/BGE for embeddings.
- **LanceDB** is the embedded vector store of choice (single-process, no server, on-disk Parquet+Lance format). `pgvector` and `qdrant` are demonstrated alongside in module 03 only.
- **Ragas / DeepEval configured with Claude as judge.** Both libraries default to OpenAI; we override.
- **All notebooks use a small, public, embeddable corpus** (the `data/` folder seed) so you can run end-to-end without proprietary data.

## Notebooks

| # | Notebook | Pairs with module |
|---|----------|-------------------|
| 1 | [`03_vector_db_hnsw.py`](03_vector_db_hnsw.py) | Module 3 — HNSW tuning, recall vs latency |
| 2 | [`04_chunking.py`](04_chunking.py) | Module 4 — fixed/recursive/semantic/Anthropic Contextual |
| 3 | [`05_hybrid_retrieval.py`](05_hybrid_retrieval.py) | Module 5 — BM25 + dense + RRF |
| 4 | [`06_reranking.py`](06_reranking.py) | Module 6 — Cohere/BGE/MMR |
| 5 | [`10_routing.py`](10_routing.py) | Module 10 — function-call routing (read_file/grep/sql/vector) |
| 6 | [`11_conversational.py`](11_conversational.py) | Module 11 — multi-turn query rewriter |
| 7 | [`12_extraction.py`](12_extraction.py) | Module 12 — Docling vs Unstructured (HTML + arXiv PDF) |
| 8 | [`13a_evaluation.py`](13a_evaluation.py) | Module 8/13A — Ragas with Claude judge, bootstrap CIs |
| 9 | [`14_grounding_hallucination.py`](14_grounding_hallucination.py) | Module 14 — Anthropic Citations + HHEM + NLI |
| 10 | [`15_multilingual_lostmid.py`](15_multilingual_lostmid.py) | Module 15 — BGE-M3 cross-lingual + lost-in-the-middle |

## Running a notebook

**As a script:**
```bash
python 05_hybrid_retrieval.py
```

**As a Jupyter notebook in VS Code:**
1. Open the `.py` file.
2. VS Code shows "Run Cell" buttons above each `# %%` marker.
3. Click "Run Cell" or `Shift+Enter`.

**Convert to .ipynb with jupytext:**
```bash
pip install jupytext
jupytext --to ipynb 05_hybrid_retrieval.py
```

## Stack notes

- LanceDB requires no server — files in `./lancedb_storage/`.
- BGE-M3 first run downloads ~2.2 GB of weights into HuggingFace cache. Subsequent runs are fast.
- Ragas calls multiple LLM judge invocations per question — expect ~$0.05–0.20 per evaluated question on a Sonnet-class judge. Use the small example sets first.

## Troubleshooting

- **`AttributeError: module 'numpy' has no attribute ...`** — pin `numpy<2.0` if you hit this with older sentence-transformers.
- **LanceDB `ImportError`** on Mac M-series — make sure you're on Python 3.11+, not the system 3.9.
- **Ragas judge errors** — confirm your `ANTHROPIC_API_KEY` is loaded; print `os.environ.get('ANTHROPIC_API_KEY')[:8]` to verify.
