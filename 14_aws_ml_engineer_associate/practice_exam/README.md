# AWS MLA-C01 — Practice Exam

A local Flask web app that serves a 500-question practice bank for the
**AWS Certified Machine Learning Engineer – Associate (MLA-C01)** exam
(live version: April 2024+).

## What's in here

| File | Purpose |
|---|---|
| `questions.md` | 500 exam-realistic questions in a parseable markdown format. Weighted to match the real exam: 140 / 130 / 110 / 120 across Domains 1–4 (28% / 26% / 22% / 24%). |
| `parser.py` | Parses `questions.md` into Python dicts. Run standalone for a sanity check. |
| `app.py` | Flask app — landing page → quiz form → results with scoring + explanations. |
| `templates/` | Jinja templates (`base.html`, `index.html`, `quiz.html`, `results.html`). |
| `static/style.css` | Stylesheet. AWS-orange accent (#FF9900). |
| `Dockerfile` | Container image (python:3.11-slim + waitress prod WSGI). |
| `requirements.txt` | Pinned dependencies (flask 3.1.3, waitress 3.0.2, markdown 3.10.2). |
| `.dockerignore` | Keeps `__pycache__`, venvs, IDE files, etc. out of the image. |

## Quick start — Docker (recommended for sharing)

```bash
# From this directory:
docker build -t aws-mle-associate .
docker run --rm -p 5151:5151 aws-mle-associate
```

Then open **http://localhost:5151**.

The container:
- Runs `waitress` (production WSGI) on port `5151` as a non-root `app` user.
- Includes a `HEALTHCHECK` against `/`.
- Final image size: ~222 MB (47 MB compressed).

### Sharing the image

```bash
# Save to a tarball you can scp / share / send:
docker save aws-mle-associate | gzip > aws-mle-associate.tar.gz

# On the other machine:
docker load < aws-mle-associate.tar.gz
docker run --rm -p 5151:5151 aws-mle-associate
```

### Run on a different host port

```bash
docker run --rm -p 8080:5151 aws-mle-associate   # browse to http://localhost:8080
```

### Run detached (background)

```bash
docker run -d --name mla-c01 -p 5151:5151 --restart unless-stopped aws-mle-associate
docker logs -f mla-c01     # tail the logs
docker stop mla-c01        # stop it later
```

## Run it (native, without Docker)

From the project root:

```bash
.venv/bin/python topics/14_aws_ml_engineer_associate/practice_exam/app.py
```

Or from this directory:

```bash
cd topics/14_aws_ml_engineer_associate/practice_exam
../../../.venv/bin/python app.py
```

Then open **http://127.0.0.1:5151**.

### Options

```bash
python app.py --host 0.0.0.0 --port 5151 --debug
```

## How it works

1. **Landing page** — pick domains (defaults to all), question count (10 / 25 / 65 / 100 / 250 / all), and shuffle on/off.
2. **Quiz** — all selected questions on one page. Radio buttons for single-answer, checkboxes for `(Select TWO)` style. Sticky submit footer with a live "X of Y answered" progress bar.
3. **Results** — overall score (with 72% pass threshold, ~720/1000 scaled), per-domain breakdown, and a question-by-question review showing your answer, the correct answer, and the explanation. Filter to wrong-only / right-only / all.

## Real exam mechanics

- **Length:** 65 questions in 130 minutes (≈2 min/question).
- **Pass:** 720/1000 scaled (~72%). Aim ≥80% on this bank for margin.
- **Format:** Single-answer (A–D) and a small number of multi-response (Select TWO/THREE), plus a handful of ordering/matching/case-study items on the real exam. This bank focuses on the single-answer + Select TWO formats — the most heavily weighted.

## Question format

Each question in `questions.md` follows this format (used by the parser):

```
## Q42 — Domain 1: Data Preparation for Machine Learning
**Objective:** {one-line objective from the official MLA-C01 exam guide}

{question stem — can be multiple lines, markdown}

- A. {option}
- B. {option}
- C. {option}
- D. {option}

**Answer:** C
(or "A, C" for multi-select questions)

**Explanation:** {why correct, why distractors fail}
```

To add or edit questions, edit `questions.md` and re-run the app — the parser is invoked at startup.

## Sanity-check the parser

```bash
.venv/bin/python topics/14_aws_ml_engineer_associate/practice_exam/parser.py
```

Should print (when the full bank is in place):

```
Parsed 500 questions.
  Domain 1: 140 questions
  Domain 2: 130 questions
  Domain 3: 110 questions
  Domain 4: 120 questions
  Multi-select: {N}
```

## Notes on exam alignment

- Question difficulty and patterns mirror the AWS MLA-C01 official exam guide (Apr 2024+).
- Coverage maps to every task statement in the four official domains:
  - **Domain 1 — Data Preparation for Machine Learning (28%)** → ingestion, transformation, integrity, feature stores.
  - **Domain 2 — ML Model Development (26%)** → algorithm choice, SageMaker training, hyperparameter tuning, evaluation.
  - **Domain 3 — Deployment and Orchestration of ML Workflows (22%)** → endpoint deployment patterns, CI/CD, infra/scaling.
  - **Domain 4 — ML Solution Monitoring, Maintenance, and Security (24%)** → Model Monitor, Clarify, IAM/KMS/VPC, cost optimization.
- See the per-chapter materials under `topics/14_aws_ml_engineer_associate/part_*/` for the topic-to-domain map and deeper teaching content.
- All questions are 4-option (A–D); multi-select questions are marked `(Select TWO)` in the stem.
