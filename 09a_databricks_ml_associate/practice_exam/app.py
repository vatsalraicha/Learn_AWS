"""Flask quiz app for Databricks ML Associate practice exam."""
from __future__ import annotations

import random
import uuid
from pathlib import Path

import markdown as md
from flask import Flask, abort, redirect, render_template, request, session, url_for

from parser import Question, load_questions

ROOT = Path(__file__).parent
QUESTIONS = load_questions(ROOT / "questions.md")
QUESTIONS_BY_NUMBER = {q["number"]: q for q in QUESTIONS}

app = Flask(__name__)
app.secret_key = "databricks-ml-associate-practice-exam-local-only"

# Active quiz sessions held in-process (single-user local app).
_QUIZ_STATE: dict[str, dict] = {}

MD_EXTENSIONS = ["fenced_code", "tables", "sane_lists"]


def render_md(text: str) -> str:
    return md.markdown(text, extensions=MD_EXTENSIONS)


@app.template_filter("md")
def md_filter(text: str) -> str:
    return render_md(text)


SECTION_NAMES = {
    1: "Databricks Machine Learning (38%)",
    2: "Data Processing / ML Workflows (19%)",
    3: "Model Development (31%)",
    4: "Model Deployment (12%)",
}


def section_counts() -> dict[int, int]:
    counts: dict[int, int] = {1: 0, 2: 0, 3: 0, 4: 0}
    for q in QUESTIONS:
        counts[q["section_num"]] += 1
    return counts


def build_quiz(num_questions: int, sections: list[int], shuffle: bool) -> list[int]:
    """Return a list of selected question numbers."""
    pool = [q for q in QUESTIONS if q["section_num"] in sections]
    if shuffle:
        random.shuffle(pool)
    if num_questions == 0 or num_questions > len(pool):
        chosen = pool
    elif shuffle:
        chosen = pool[:num_questions]
    else:
        # Sample proportionally across selected sections in deterministic order.
        per_section: dict[int, list[Question]] = {s: [] for s in sections}
        for q in pool:
            per_section[q["section_num"]].append(q)
        # Compute proportional count per section.
        total = sum(len(v) for v in per_section.values())
        targets = {s: max(1, round(num_questions * len(per_section[s]) / total)) for s in sections}
        # Adjust rounding so the totals match num_questions.
        delta = num_questions - sum(targets.values())
        for s in sorted(sections, key=lambda x: -len(per_section[x])):
            if delta == 0:
                break
            step = 1 if delta > 0 else -1
            if targets[s] + step >= 1 and targets[s] + step <= len(per_section[s]):
                targets[s] += step
                delta -= step
        chosen = []
        for s in sections:
            chosen.extend(per_section[s][: targets[s]])
        chosen.sort(key=lambda q: q["number"])
    return [q["number"] for q in chosen]


@app.route("/")
def index():
    return render_template(
        "index.html",
        section_names=SECTION_NAMES,
        section_counts=section_counts(),
        total=len(QUESTIONS),
    )


@app.route("/start", methods=["POST"])
def start():
    sections = [int(s) for s in request.form.getlist("sections") or []]
    if not sections:
        sections = [1, 2, 3, 4]
    num_q_raw = request.form.get("num_questions", "48").strip()
    try:
        num_q = int(num_q_raw)
    except ValueError:
        num_q = 48
    if num_q < 0:
        num_q = 0
    shuffle = request.form.get("shuffle") == "on"

    question_numbers = build_quiz(num_q, sections, shuffle)
    if not question_numbers:
        abort(400, "No questions match the selected sections.")

    quiz_id = uuid.uuid4().hex
    _QUIZ_STATE[quiz_id] = {
        "question_numbers": question_numbers,
        "sections": sections,
        "shuffle": shuffle,
    }
    session["quiz_id"] = quiz_id
    return redirect(url_for("quiz", quiz_id=quiz_id))


@app.route("/quiz/<quiz_id>")
def quiz(quiz_id: str):
    state = _QUIZ_STATE.get(quiz_id)
    if not state:
        return redirect(url_for("index"))
    questions = [QUESTIONS_BY_NUMBER[n] for n in state["question_numbers"]]
    return render_template(
        "quiz.html",
        quiz_id=quiz_id,
        questions=questions,
        section_names=SECTION_NAMES,
    )


@app.route("/submit/<quiz_id>", methods=["POST"])
def submit(quiz_id: str):
    state = _QUIZ_STATE.get(quiz_id)
    if not state:
        return redirect(url_for("index"))

    question_numbers = state["question_numbers"]
    user_answers: dict[int, list[str]] = {}
    results = []
    correct_count = 0
    section_breakdown: dict[int, dict[str, int]] = {}

    for n in question_numbers:
        q = QUESTIONS_BY_NUMBER[n]
        field = f"q{n}"
        if q["multi_select"]:
            selected = sorted(request.form.getlist(field))
        else:
            val = request.form.get(field)
            selected = [val] if val else []
        user_answers[n] = selected

        correct_set = sorted(q["answer"])
        is_correct = selected == correct_set
        if is_correct:
            correct_count += 1
        sec = q["section_num"]
        if sec not in section_breakdown:
            section_breakdown[sec] = {"correct": 0, "total": 0}
        section_breakdown[sec]["total"] += 1
        if is_correct:
            section_breakdown[sec]["correct"] += 1

        results.append(
            {
                "question": q,
                "selected": selected,
                "correct_set": correct_set,
                "is_correct": is_correct,
            }
        )

    total = len(question_numbers)
    score_pct = round(100 * correct_count / total, 1) if total else 0.0
    passed = score_pct >= 70.0

    return render_template(
        "results.html",
        results=results,
        correct=correct_count,
        total=total,
        score_pct=score_pct,
        passed=passed,
        section_breakdown=section_breakdown,
        section_names=SECTION_NAMES,
    )


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", default=5050, type=int)
    ap.add_argument("--debug", action="store_true", help="Flask dev server with debug")
    ap.add_argument("--prod", action="store_true", help="Use waitress (production WSGI)")
    ap.add_argument("--threads", default=8, type=int, help="Waitress thread count")
    args = ap.parse_args()
    print(f"\n  Databricks ML Associate practice exam — http://{args.host}:{args.port}\n")
    if args.prod:
        from waitress import serve

        print(f"  [waitress] serving with {args.threads} threads\n")
        serve(app, host=args.host, port=args.port, threads=args.threads)
    else:
        app.run(host=args.host, port=args.port, debug=args.debug)
