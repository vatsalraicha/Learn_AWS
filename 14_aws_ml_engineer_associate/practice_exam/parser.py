"""Parse questions.md into a list of question dicts."""
from __future__ import annotations

import re
from pathlib import Path
from typing import TypedDict


class Question(TypedDict):
    number: int
    section: str
    section_num: int
    objective: str
    stem: str
    options: dict[str, str]
    answer: list[str]
    multi_select: bool
    explanation: str


# Accept both `Section N:` and `Domain N:` headers — Topic 14 uses `Domain N:`.
_HEADER_RE = re.compile(
    r"^Q(?P<num>\d+)\s+[—-]\s+(?:Section|Domain)\s+(?P<sec_num>\d+):\s+(?P<sec_name>.+?)\s*$"
)
_OBJ_RE = re.compile(r"^\*\*Objective:\*\*\s*(?P<obj>.+?)\s*$")
_OPTION_RE = re.compile(r"^-\s+(?P<letter>[A-D])\.\s+(?P<text>.*)$")
_ANSWER_RE = re.compile(r"^\*\*Answer:\*\*\s*(?P<ans>.+?)\s*$")
_EXPLANATION_RE = re.compile(r"^\*\*Explanation:\*\*\s*(?P<exp>.+?)\s*$")


def _split_blocks(text: str) -> list[str]:
    parts = re.split(r"\n## Q", "\n" + text)
    return [f"Q{p}" for p in parts[1:]]


def _parse_block(block: str) -> Question:
    lines = block.splitlines()
    header_match = _HEADER_RE.match(lines[0])
    if not header_match:
        raise ValueError(f"Could not parse header: {lines[0]!r}")
    num = int(header_match["num"])
    sec_num = int(header_match["sec_num"])
    section = header_match["sec_name"]

    # Find structural lines.
    objective = ""
    answer_line_idx = -1
    explanation_line_idx = -1
    option_start_idx = -1
    for i, line in enumerate(lines):
        if not objective:
            m = _OBJ_RE.match(line)
            if m:
                objective = m["obj"]
                continue
        if option_start_idx < 0 and _OPTION_RE.match(line):
            option_start_idx = i
        if answer_line_idx < 0:
            m = _ANSWER_RE.match(line)
            if m:
                answer_line_idx = i
        if explanation_line_idx < 0:
            m = _EXPLANATION_RE.match(line)
            if m:
                explanation_line_idx = i

    if option_start_idx < 0 or answer_line_idx < 0 or explanation_line_idx < 0:
        raise ValueError(f"Missing structural element in Q{num}")

    # Stem = everything between objective line and first option, trimmed of blanks.
    obj_idx = next(i for i, l in enumerate(lines) if _OBJ_RE.match(l))
    stem_lines = lines[obj_idx + 1 : option_start_idx]
    stem = "\n".join(stem_lines).strip()

    # Parse options. Each option starts at a `- A.` line and extends until the next
    # option, the answer line, or a blank-line-followed-by-non-indented marker.
    options: dict[str, str] = {}
    option_indices: list[tuple[int, str]] = []
    for i in range(option_start_idx, answer_line_idx):
        m = _OPTION_RE.match(lines[i])
        if m:
            option_indices.append((i, m["letter"]))
    option_indices.append((answer_line_idx, "_END_"))

    for j in range(len(option_indices) - 1):
        start, letter = option_indices[j]
        end, _ = option_indices[j + 1]
        first_line = _OPTION_RE.match(lines[start])["text"]
        rest = "\n".join(lines[start + 1 : end])
        body = first_line if not rest.strip() else f"{first_line}\n{rest}"
        # Strip trailing blank lines.
        options[letter] = body.rstrip()

    # Parse answer.
    answer_raw = _ANSWER_RE.match(lines[answer_line_idx])["ans"]
    answer_letters = [a.strip() for a in answer_raw.split(",")]
    answer_letters = [a for a in answer_letters if re.match(r"^[A-D]$", a)]
    multi_select = len(answer_letters) > 1

    # Parse explanation (may span multiple lines until end of block).
    exp_first = _EXPLANATION_RE.match(lines[explanation_line_idx])["exp"]
    exp_rest = "\n".join(lines[explanation_line_idx + 1 :]).strip()
    explanation = exp_first if not exp_rest else f"{exp_first}\n{exp_rest}"
    # Strip any trailing `---` horizontal rules.
    explanation = re.sub(r"\n?-{3,}\s*$", "", explanation).strip()

    return Question(
        number=num,
        section=section,
        section_num=sec_num,
        objective=objective,
        stem=stem,
        options=options,
        answer=answer_letters,
        multi_select=multi_select,
        explanation=explanation,
    )


def load_questions(path: str | Path) -> list[Question]:
    text = Path(path).read_text(encoding="utf-8")
    blocks = _split_blocks(text)
    questions = [_parse_block(b) for b in blocks]
    return questions


if __name__ == "__main__":
    qs = load_questions(Path(__file__).parent / "questions.md")
    print(f"Parsed {len(qs)} questions.")
    by_section: dict[int, int] = {}
    for q in qs:
        by_section[q["section_num"]] = by_section.get(q["section_num"], 0) + 1
    for s in sorted(by_section):
        print(f"  Domain {s}: {by_section[s]} questions")
    multi = sum(1 for q in qs if q["multi_select"])
    print(f"  Multi-select: {multi}")
    if qs:
        print(f"\nSample Q{qs[0]['number']}: {qs[0]['stem'][:80]}...")
        print(f"  Options: {list(qs[0]['options'].keys())}")
        print(f"  Answer: {qs[0]['answer']}")
