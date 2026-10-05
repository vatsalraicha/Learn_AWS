# 47 — AI Study Assistants for Engineers

> Nana's "Ultimate IT Fundamentals" course opens with a chapter on using AI to learn faster. For Vatsal (already using Claude Code daily) this is brief — but the curriculum + Socratic patterns + risks are worth surfacing.

## 1. The 2026 landscape

| Tool | Use case |
|---|---|
| **Claude Code (CLI)** | Code-aware tutoring + project building (Vatsal's daily tool) |
| **Claude.ai (chat + projects)** | Long-form reasoning, document analysis |
| **ChatGPT** | Mainstream — broadest knowledge cutoff, native search |
| **Gemini** | Google-integrated; Workspace + Vertex |
| **Perplexity** | Citation-first search |
| **NotebookLM** | "Talk to your sources" — upload PDFs/URLs, ask questions |
| **Cursor / Windsurf** | IDE-integrated coding |
| **Anki + AI** | Spaced repetition + AI-generated cards |
| **Khanmigo** | Math/science tutoring (mostly K-12) |

## 2. The "study assistant" prompting patterns

### Socratic mode
"Don't give me the answer. Ask me questions to help me get there. Stop after each question."

### Feynman technique
"Teach me X like I'm 15. Then teach me X like I'm a senior engineer. Highlight where the two diverge."

### Custom study plan
"I have 8 hours/week, 6 months, and need to learn AWS Sr Lead AI/ML skills. Build me a week-by-week plan with concrete exercises."

### Quiz me
"Ask me 5 questions about Kubernetes scheduling. After my answer, grade (0-10) + explain gaps."

### Exam prep
"You are the CKA exam. Generate a question. Then grade my response. Continue until I pass 10 in a row."

## 3. The do's and don'ts

| Do | Don't |
|---|---|
| Verify factual claims (especially version numbers, pricing) | Trust without checking |
| Use as Socratic tutor | Use as final-answer oracle |
| Combine with primary sources (docs, papers, RFCs) | Replace primary sources |
| Use to generate practice quizzes | Use to grade actual exams |
| Use for first-draft explanations | Use as the only explanation |

## 4. The hallucination problem (still real in 2026)

Even GPT-5 / Claude 4.x hallucinate:
- **Version numbers** — often confidently wrong
- **API signatures** — invented methods
- **CVE numbers / CVSS scores** — wrong details
- **Pricing** — out of date or made up
- **Recent changes** — knowledge cutoff issues

Verify everything that matters. Use docs as ground truth.

## 5. Keeping momentum

Nana's bootcamps last 4-6 months. Maintaining momentum:
- **20-minute daily** beats 4 hours weekly
- **Track in a simple tool** (Notion, Anki, even a text file)
- **Public commitment** — tell your manager or peer; commit to demo
- **Project-based learning** — not just tutorials; build something real
- **Teach what you learn** — blog, brown-bag, Slack thread

## 6. Quick self-check

1. What's the Socratic-mode prompting pattern?
2. Why verify AI-generated version numbers?
3. What does NotebookLM do differently from ChatGPT?
4. Why is 20 min/day better than 4 hr/week?
5. What's a sign you're using AI as oracle instead of tutor?

(Answers: tell it to ask questions back, not give answers; LLMs hallucinate specifics confidently; lets you upload sources and constrains answers to those sources — fewer hallucinations; consistency builds neural pathways, weekend cramming doesn't retain; you can't reproduce the answer from primary sources or explain it without re-asking.)
