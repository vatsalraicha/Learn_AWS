# Topic 04 — Ebook build

This directory builds the **AWS for AI/ML Engineers** ebook (EPUB + PDF + combined markdown) from the 57 module files in the parent directory.

## Files in this directory

| File | What it is |
|---|---|
| `build_ebook.sh` | Build script — runs the full pipeline |
| `make_cover.py` | Generates the 1600×2560 cover PNG |
| `preprocess_mermaid.py` | Pre-renders Mermaid diagrams to PNG for EPUB |
| `ebook.css` | EPUB stylesheet (Charter serif body, Avenir sans headings) |
| `SOURCES.md` | The Sources & References appendix |
| `cover.png` | Generated cover image |
| `AWS_for_AI_ML_complete_ebook.md` | Combined source markdown (~8,700 lines) |
| `AWS_for_AI_ML_complete_ebook.epub.md` | Intermediate (mermaid → PNG) |
| `AWS_for_AI_ML_complete_ebook.pdf` | PDF render via xelatex |
| `AWS_for_AI_ML_complete_ebook.epub` | EPUB3 with cover, CSS, embedded fonts |

## How to rebuild

```bash
./build_ebook.sh
```

Requires:
- `pandoc` (3.x+) — `brew install pandoc`
- `xelatex` (TeXLive / MacTeX) for PDF
- `mmdc` (Mermaid CLI) for diagram pre-rendering — `npm install -g @mermaid-js/mermaid-cli`
- Python with PIL (already in repo `.venv`) for cover generation

## Contents

The ebook is structured as:

1. **How to read this ebook** (intro)
2. **CAPITAL_ONE.md dossier** — interview-ready Capital One AWS context
3. **57 modules** (Parts A–N) in numeric order
4. **Appendix A — FACTS.md** — citable atomic facts
5. **Appendix B — Sources & References** — every URL cited, archived offline

## Output sizes (typical)

- Combined markdown: ~400 KB (~8,700 lines)
- PDF: ~750 KB
- EPUB: ~470 KB

## Caveat on regenerating

The source modules in the parent directory are the canonical version. This ebook is a *derived artifact*. If a module changes, re-run `./build_ebook.sh` to regenerate.
