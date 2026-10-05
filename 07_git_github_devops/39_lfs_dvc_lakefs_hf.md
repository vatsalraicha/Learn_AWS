# 39 — Git LFS + DVC + lakeFS + Hugging Face Hub

> *"Don't put large files in git. Pick the right tool: LFS for small/medium binaries, DVC for ML data + models with lineage, lakeFS for data-lake-scale, HF Hub for model distribution."*

## Why this module exists

ML repos hit git's "everything is small text" assumption hard. Datasets, model weights, checkpoints — all binary, large, and changing. Git LFS, DVC, lakeFS, and Hugging Face Hub each solve overlapping pieces. This module clarifies which to pick when.

---

## 1. The "don't put it in git" decision tree

```
Is the file <100 KB and text?
  → Yes: commit to git.

Is the file <50 MB and binary?
  → Yes if rarely changing: commit to git (with `.gitattributes` `binary`).
  → No if frequently changing: use LFS or DVC.

Is the file 50 MB – 5 GB?
  → Use Git LFS (simple) or DVC (lineage).

Is the file >5 GB OR you have terabytes of data?
  → DVC with S3/GCS backend, lakeFS, or just S3 + manifest.

Is it a trained model you want to share/distribute?
  → Hugging Face Hub (or SageMaker Model Registry / MLflow for internal).
```

The default at every shop: **production code in git; data + large models OUT of git**, with a pointer/manifest in git.

---

## 2. Git LFS — simple large-file storage

Git Large File Storage replaces the file in your repo with a small **pointer file** (text, ~130 bytes). The actual content lives in LFS storage (GitHub's, GitLab's, or self-hosted).

```bash
brew install git-lfs
cd my-repo
git lfs install
git lfs track "*.pt"
git lfs track "*.h5"
git lfs track "*.parquet"
git add .gitattributes
git add models/checkpoint.pt
git commit -m "add checkpoint"
git push
```

`.gitattributes` gets entries like:

```
*.pt    filter=lfs diff=lfs merge=lfs -text
*.h5    filter=lfs diff=lfs merge=lfs -text
```

When someone clones, they get pointer files. To get the actual data:

```bash
git lfs pull          # download all LFS files for current commit
git lfs fetch         # download to LFS cache without checkout
```

**Pros**: Simple, native git workflow, GitHub-supported.
**Cons**:
- **Cost**: GitHub LFS storage = $5/mo per 50 GB; bandwidth = $5/mo per 50 GB. Quickly very expensive for ML datasets.
- **No lineage**: which data was used for which training run?
- **No partial fetch**: getting one file requires fetching the pointer first, then the blob.
- **History bloat**: every change to a 1GB file adds 1GB to LFS storage. Forever.
- **Performance**: slow on huge files compared to direct object storage.

**When to use LFS**: small-to-medium binary fixtures (test images, fonts, base model weights you commit once). NOT for actively-iterating ML datasets.

---

## 3. DVC — Data Version Control

Designed specifically for ML. Tracks data + models OUTSIDE git, with a small pointer file IN git. Adds pipelines, experiments, metrics.

```bash
pip install dvc[s3]      # or [gcs], [azure], [gdrive], etc.
cd my-ml-repo
dvc init
git add .dvc .dvcignore && git commit -m "init dvc"

# Configure remote storage (S3 in this example)
dvc remote add -d storage s3://my-bucket/dvc-store
git add .dvc/config && git commit -m "configure dvc remote"

# Track a dataset
dvc add data/train.parquet
# This creates data/train.parquet.dvc (a text pointer file) and adds the original to .gitignore
git add data/train.parquet.dvc data/.gitignore && git commit -m "add training data"

# Push data to remote
dvc push

# Someone else clones the repo
git clone ... && cd repo
dvc pull          # downloads data/train.parquet from S3
```

The pointer file `data/train.parquet.dvc`:

```yaml
outs:
  - md5: 5e8b3f...
    size: 1048576000
    path: train.parquet
```

### DVC pipelines

DVC also models your training pipeline as a DAG:

```yaml
# dvc.yaml
stages:
  prepare:
    cmd: python src/prepare.py
    deps:
      - data/raw.csv
      - src/prepare.py
    outs:
      - data/processed.parquet

  train:
    cmd: python src/train.py
    deps:
      - data/processed.parquet
      - src/train.py
    params:
      - learning_rate
      - epochs
    outs:
      - models/checkpoint.pt
    metrics:
      - metrics.json:
          cache: false
```

```bash
dvc repro          # runs only the stages whose inputs changed
dvc metrics show
dvc exp run        # create an experiment branch
```

DVC tracks:
- Data versions (pointer files in git)
- Model versions (same)
- Pipeline stages and their inputs/outputs
- Experiments (parametrized runs with metrics)

**Pros**: ML-native, lineage-tracked, multi-backend, free (open source).
**Cons**: Learning curve; ecosystem smaller than MLflow; doesn't replace experiment-tracking UI (Studio is paid).

**When to use DVC**: when you want git-native data + model versioning with pipeline tracking, and don't mind the .dvc pointer files.

---

## 4. lakeFS — git-like for data lakes

[lakeFS](https://lakefs.io/) puts a git-like layer over S3 / GCS / Azure Blob. Branches, commits, merges — but for petabytes of data, not for code.

```bash
lakectl repo create lakefs://ml-data s3://my-lake-bucket/
lakectl branch create lakefs://ml-data/experiment-x --source main
# ... mutate data in experiment-x branch ...
lakectl commit lakefs://ml-data/experiment-x -m "add Q3 data"
lakectl merge lakefs://ml-data/experiment-x lakefs://ml-data/main
```

Apps read/write to lakeFS as if it were S3 (`s3a://repo/branch/key`), with git-like isolation.

**Pros**: petabyte-scale; zero-copy branches (just metadata); strong consistency guarantees; integrates with Spark, Trino, Athena.
**Cons**: deploy a service; smaller community than DVC; ML-pipeline tooling lighter.

**When to use**: data-lake-scale data (multi-TB+) where you need isolated dev/test/prod views. Often pairs with DVC (lakeFS for data; DVC for pipelines).

---

## 5. Hugging Face Hub

The default for **model distribution** in the ML community. Repos on huggingface.co with git + LFS under the hood, plus a model card, dataset cards, and the Inference API.

```bash
pip install huggingface_hub
huggingface-cli login

# Clone a model repo (uses git + LFS automatically)
git lfs install
git clone https://huggingface.co/meta-llama/Llama-3-8B-Instruct

# Or via Python
from huggingface_hub import snapshot_download
path = snapshot_download(repo_id="meta-llama/Llama-3-8B-Instruct")

# Upload your own model
from huggingface_hub import HfApi
api = HfApi()
api.create_repo(repo_id="capitalone/my-finetuned-model", private=True)
api.upload_folder(folder_path="models/checkpoint/", repo_id="capitalone/my-finetuned-model")
```

For Capital One: **private** HF Hub repos are the standard way to distribute models internally OR to consume open-source base models. With Enterprise Hub, you get SSO + SCIM + IP allowlist + audit log + dedicated infra.

**When to use**: model distribution. Not for raw training data.

---

## 6. The combined ML repo stack (typical)

```
Repo on GitHub:
├── src/                           ← code in git (small, text)
├── notebooks/                     ← .py pairs in git; .ipynb gitignored
├── data/
│   ├── sample/                    ← tiny test fixtures in git
│   └── train.parquet.dvc          ← pointer file in git; data in S3 via DVC
├── models/
│   └── checkpoint.pt.dvc          ← pointer file; weights in S3
├── dvc.yaml                       ← pipeline definition
├── pyproject.toml
└── .gitattributes                 ← LFS rules for small binaries
```

Plus:
- **S3** holds the actual large data + models (DVC-managed)
- **Hugging Face Hub** (or SageMaker Model Registry) holds versioned model releases for distribution
- **MLflow Tracking Server** records experiment metadata (params, metrics, artifacts pointers)

---

## 7. The 2026 alternatives — XetHub

[XetHub](https://xethub.com/) (acquired by Hugging Face in 2024) is content-defined chunking for huge files. Replaces LFS with much better diffing for large binaries (delta-encoded, partial fetch). HF Hub has been migrating to Xet-backed storage.

For new projects, Xet-backed HF Hub repos handle multi-GB model weights with git-like ergonomics at a fraction of LFS bandwidth cost.

---

## 8. Decision matrix

| You have | Best tool |
|---|---|
| <10 binary fixtures, <50 MB each | Git LFS |
| ML datasets with iteration, lineage matters | DVC + S3 |
| Petabyte data lakes with branch-and-merge semantics | lakeFS |
| Distributing a trained model | Hugging Face Hub (or SageMaker Model Registry) |
| Internal model registry with promotion gates | SageMaker Model Registry / MLflow |
| Versioned training data with strong consistency | DVC + S3 (small/med) or lakeFS (large) |
| ML-experiments tracking + visualization | MLflow / W&B / Neptune |

The boundary is fuzzy. Common stack at modern shops: DVC + S3 for data; MLflow for experiments; SageMaker Model Registry for deployment; Hugging Face Hub for sharing open models.

---

## 9. The Capital One reality

Inference: AWS-native. Most likely:
- **Data**: S3 + Glue/Lake Formation catalogs; possibly LakeFS in some teams.
- **Data versioning**: DVC for repos with active data iteration; SageMaker Feature Store for serving features.
- **Models**: SageMaker Model Registry as the primary model store + promotion gate (see [module 43](43_mlops_mlflow_sagemaker.md)).
- **External base models**: pulled from HF Hub via internal mirror (so the pull happens in their VPC, not over public internet).
- **Git LFS**: minimally — fixture data, base model weights pinned in repo.

---

## 10. Cross-references

- Repo `pyproject.toml` + .gitignore for ML → [module 18](18_python_ml_repo_structure.md).
- Notebook discipline (notebook side of the same coin) → [module 38](38_notebook_discipline.md).
- MLflow + SageMaker Model Registry → [module 43](43_mlops_mlflow_sagemaker.md).
- Topic 04 module 10 — S3 deep — for the storage layer DVC/lakeFS sit on.
