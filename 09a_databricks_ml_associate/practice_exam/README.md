# Databricks ML Associate — Practice Exam

A local Flask web app that serves a 200-question practice bank for the
**Databricks Certified Machine Learning Associate** exam (live version: March 1, 2025).

## What's in here

| File | Purpose |
|---|---|
| `questions.md` | 200 exam-realistic questions in a parseable markdown format. Weighted to match the real exam: 76 / 38 / 62 / 24 across Sections 1–4 (38% / 19% / 31% / 12%). |
| `parser.py` | Parses `questions.md` into Python dicts. Run standalone for a sanity check. |
| `app.py` | Flask app — landing page → quiz form → results with scoring + explanations. |
| `templates/` | Jinja templates (`base.html`, `index.html`, `quiz.html`, `results.html`). |
| `static/style.css` | Stylesheet. Databricks-style accent color. |
| `Dockerfile` | Container image (python:3.11-slim + waitress prod WSGI). |
| `requirements.txt` | Pinned dependencies (flask 3.1.3, waitress 3.0.2, markdown 3.10.2). |
| `.dockerignore` | Keeps `__pycache__`, venvs, IDE files, etc. out of the image. |

## Quick start — Docker (recommended for sharing)

```bash
# From this directory:
docker build -t databricks-ml-associate .
docker run --rm -p 5052:5052 databricks-ml-associate
```

Then open **http://localhost:5052**.

The container:
- Runs `waitress` (production WSGI) on port `5052` as a non-root `app` user.
- Includes a `HEALTHCHECK` against `/`.
- Final image size: **222 MB**.

### Sharing the image

```bash
# Save to a tarball you can scp / share / send:
docker save databricks-ml-associate | gzip > databricks-ml-associate.tar.gz

# On the other machine:
docker load < databricks-ml-associate.tar.gz
docker run --rm -p 5052:5052 databricks-ml-associate
```

### Run on a different host port

```bash
docker run --rm -p 8080:5052 databricks-ml-associate   # browse to http://localhost:8080
```

### Run detached (background)

```bash
docker run -d --name db9a -p 5052:5052 --restart unless-stopped databricks-ml-associate
docker logs -f db9a     # tail the logs
docker stop db9a        # stop it later
```

## Run it (native, without Docker)

From the project root:

```bash
.venv/bin/python topics/09a_databricks_ml_associate/practice_exam/app.py
```

Or from this directory:

```bash
cd topics/09a_databricks_ml_associate/practice_exam
../../../.venv/bin/python app.py
```

Then open **http://127.0.0.1:5050**.

### Options

```bash
python app.py --host 0.0.0.0 --port 5050 --debug
```

## How it works

1. **Landing page** — pick sections (defaults to all), question count (10 / 25 / 48 / 100 / all), and shuffle on/off.
2. **Quiz** — all selected questions on one page. Radio buttons for single-answer, checkboxes for `(Select TWO)` style. Sticky submit footer with a live "X of Y answered" progress bar.
3. **Results** — overall score (with 70% pass threshold), per-section breakdown, and a question-by-question review showing your answer, the correct answer, and the explanation. Filter to wrong-only / right-only / all.

## Question format

Each question in `questions.md` follows this format (used by the parser):

```
## Q42 — Section 1: Databricks Machine Learning
**Objective:** {one-line objective from the official exam guide}

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
.venv/bin/python topics/09a_databricks_ml_associate/practice_exam/parser.py
```

Should print:

```
Parsed 200 questions.
  Section 1: 76 questions
  Section 2: 38 questions
  Section 3: 62 questions
  Section 4: 24 questions
  Multi-select: 6
```

## Notes on exam alignment

- Question difficulty and patterns mirror the official sample questions in `research_inputs/09_databricks_ml_associate/exam_guide_excerpt.md`.
- Coverage maps to every Section bullet in the official Mar 2025 exam guide. See `research_inputs/09_databricks_ml_associate/domain_breakdown.md` for the topic-to-section map.
- The exam still tests **Hyperopt** despite Databricks deprecating it post DBR ML 16.4 LTS — this bank reflects that.
- All questions are 4-option (A–D); 6 are multi-select (marked `(Select TWO)` in the stem).
