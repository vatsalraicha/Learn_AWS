# %% [markdown]
# # Notebook 12 — Document Extraction (Docling vs Unstructured)
#
# **Pairs with:** [Module 12 — Extraction & Structured Data](../12_extraction_structured_data.md)
#
# **What you'll see:**
# 1. **Same source HTML** through Docling and Unstructured side-by-side.
# 2. **Same PDF** (auto-downloaded from arXiv) through both parsers.
# 3. How **element-typing** (heading vs paragraph vs table vs list) survives each parser.
# 4. The cost of NOT using a structure-aware parser.
#
# **Stack:** docling, unstructured, requests. **No OpenAI.** LlamaParse demo skipped — needs an API key
# (uncomment that block if you have `LLAMA_CLOUD_API_KEY` set).

# %% [markdown]
# ## Setup

# %%
import os
import warnings
import json
from pathlib import Path
from typing import List, Dict, Any
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")
warnings.filterwarnings("ignore", category=UserWarning)

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# %% [markdown]
# ## Sample 1 — A messy multi-section HTML
#
# Realistic-looking content: nested headers, a list, a table, embedded code, plus boilerplate
# that a naive parser would inline into the main content.

# %%
SAMPLE_HTML = """<!DOCTYPE html>
<html>
<head><title>Acme HR Handbook 2024</title></head>
<body>
<nav>Home | About | Careers | Contact</nav>
<header><h1>Acme HR Handbook 2024</h1></header>

<main>
  <section>
    <h2>2. Compensation</h2>
    <p>Acme bases compensation on four factors: role, level, location, and performance.</p>

    <h3>2.1 401(k) Retirement Plan</h3>
    <p>The company matches <strong>100%</strong> of employee contributions up to <strong>4%</strong>
    of eligible compensation.</p>
    <p>Vesting is graded over 3 years per the schedule below:</p>

    <table>
      <thead><tr><th>Year</th><th>Vested %</th></tr></thead>
      <tbody>
        <tr><td>1</td><td>33%</td></tr>
        <tr><td>2</td><td>66%</td></tr>
        <tr><td>3</td><td>100%</td></tr>
      </tbody>
    </table>

    <h3>2.2 Equity Grants</h3>
    <ul>
      <li>4-year vesting with a 1-year cliff.</li>
      <li>Refresh grants reviewed annually.</li>
      <li>Option to early-exercise at the company's discretion.</li>
    </ul>

    <pre><code>def calculate_match(salary, contribution_pct):
    return salary * min(contribution_pct, 0.04)</code></pre>
  </section>
</main>

<footer>© 2024 Acme Corp. All rights reserved. <a href="/privacy">Privacy</a></footer>
</body>
</html>
"""

html_path = DATA_DIR / "sample_handbook.html"
html_path.write_text(SAMPLE_HTML)
print(f"Sample HTML written: {html_path}")


# %% [markdown]
# ## Parser 1 — Unstructured
#
# Unstructured tags every block with an element type (Title, NarrativeText, Table, ListItem, etc).
# Useful both for RAG (filter chunks by type) and for skipping boilerplate.

# %%
print("\n=== UNSTRUCTURED on HTML ===")
from unstructured.partition.html import partition_html

elements = partition_html(filename=str(html_path))
for el in elements[:20]:
    el_type = el.category if hasattr(el, "category") else type(el).__name__
    text = str(el).replace("\n", " ")[:80]
    print(f"  [{el_type:18s}] {text}")

# Notice: nav, footer typically come through as NarrativeText with low-quality content.
# In production, filter by category or by Unstructured's "is_continuation" / metadata.

# %% [markdown]
# ## Parser 2 — Docling on HTML

# %%
print("\n=== DOCLING on HTML ===")
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert(str(html_path))
doc = result.document

# Docling returns a structured doc. Let's print as markdown (its native export format)
print(doc.export_to_markdown()[:1500])

# %% [markdown]
# Compare the two outputs:
# - **Unstructured** classifies elements into types you can filter (Table, ListItem, NarrativeText).
# - **Docling** produces clean markdown that preserves headings, list structure, and the table.
# - For RAG indexing, Unstructured is friendlier (typed elements drive metadata enrichment).
# - For LLM context (feed it markdown), Docling is friendlier.
# - **Production pattern:** use both — Unstructured for typed metadata, Docling output as the
#   clean text body of each chunk.

# %% [markdown]
# ## Sample 2 — A real PDF (auto-downloaded from arXiv)
#
# Lewis et al. 2020 "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks" — the canonical
# RAG paper. Small, public-domain, and we get to see how the parsers handle real LaTeX-rendered content.

# %%
PDF_URL = "https://arxiv.org/pdf/2005.11401"
pdf_path = DATA_DIR / "rag_paper.pdf"

if not pdf_path.exists():
    print(f"Downloading {PDF_URL}...")
    r = requests.get(PDF_URL, timeout=30)
    r.raise_for_status()
    pdf_path.write_bytes(r.content)
    print(f"Saved {len(r.content):,} bytes to {pdf_path}")
else:
    print(f"PDF already cached at {pdf_path}")

# %% [markdown]
# ### Unstructured on PDF (fast strategy)

# %%
print("\n=== UNSTRUCTURED on PDF (fast) ===")
from unstructured.partition.pdf import partition_pdf

elements_pdf = partition_pdf(filename=str(pdf_path), strategy="fast")
print(f"Total elements extracted: {len(elements_pdf)}")
print("\nFirst 12 elements:")
for el in elements_pdf[:12]:
    el_type = el.category if hasattr(el, "category") else type(el).__name__
    text = str(el).replace("\n", " ")[:80]
    print(f"  [{el_type:18s}] {text}")

# Count element types
from collections import Counter
type_counts = Counter(el.category if hasattr(el, "category") else type(el).__name__ for el in elements_pdf)
print(f"\nElement type distribution:")
for et, count in type_counts.most_common():
    print(f"  {et:20s} {count}")

# %% [markdown]
# ### Docling on PDF
#
# Docling has stronger layout analysis on PDFs — multi-column reading order, table structure
# recognition, formula detection. Slower than Unstructured-fast but consistently better
# structure preservation.

# %%
print("\n=== DOCLING on PDF ===")
print("(this takes 30-60 seconds — Docling does layout analysis per page)")

# Docling auto-downloads its layout / OCR models on first run.
result_pdf = converter.convert(str(pdf_path))
doc_pdf = result_pdf.document

md_output = doc_pdf.export_to_markdown()
print(f"\nDocling produced {len(md_output):,} chars of markdown.")
print("\nFirst 800 chars:")
print(md_output[:800])

# Save for inspection
(DATA_DIR / "rag_paper_docling.md").write_text(md_output)
print(f"\nFull Docling output saved to {DATA_DIR / 'rag_paper_docling.md'}")

# %% [markdown]
# ### Compare table extraction
#
# arXiv RAG paper has tables (model comparison, ablations). Run a quick check on whether each
# parser preserves them.

# %%
print("\n=== TABLE PRESERVATION CHECK ===")
unstructured_tables = [el for el in elements_pdf if (hasattr(el, "category") and el.category == "Table")]
print(f"Unstructured detected {len(unstructured_tables)} tables")
for i, t in enumerate(unstructured_tables[:2]):
    print(f"\n  Table {i+1}:")
    print(f"    {str(t)[:300]}...")

docling_tables = [item for item in doc_pdf.tables] if hasattr(doc_pdf, "tables") else []
print(f"\nDocling detected {len(docling_tables)} tables")
for i, t in enumerate(docling_tables[:2]):
    md = t.export_to_dataframe().to_markdown() if hasattr(t, "export_to_dataframe") else str(t)
    print(f"\n  Table {i+1} (markdown):")
    print(f"    {md[:300]}...")


# %% [markdown]
# ## Optional — LlamaParse (commented out; needs API key)
#
# Uncomment if you have a `LLAMA_CLOUD_API_KEY` in your `.env`:
#
# ```python
# from llama_cloud_services import LlamaParse
# parser = LlamaParse(
#     api_key=os.environ["LLAMA_CLOUD_API_KEY"],
#     result_type="markdown",
# )
# documents = parser.load_data(str(pdf_path))
# print(documents[0].text[:1000])
# ```

# %% [markdown]
# ## Things to try next
#
# 1. **Hi-Res PDF parsing** — `partition_pdf(strategy="hi_res")` runs layout analysis (slower, much better tables).
# 2. **Multi-column** — try a PDF with two-column layout (most academic papers); compare reading order.
# 3. **Scanned PDF** — feed Unstructured a scanned PDF; observe OCR fallback.
# 4. **Element-aware chunking** — chain Notebook 04's chunker on top of Unstructured's typed elements:
#    skip Headers/Footers, chunk per Section, attach element_type as metadata.
# 5. **Mistral OCR alternative** — for VLM-based parsing of complex layouts, try the Mistral OCR
#    API ($0.001/page batch tier).
#
# ## What this demonstrated
# - **Unstructured** = element-typed extraction (great for RAG metadata).
# - **Docling** = clean markdown output preserving structure (great for LLM context).
# - **Both miss things by themselves** — production parsers chain them or pick per-document type.
# - **Garbage in → garbage out**: most "RAG quality issues" trace back to the parser, not the embedder.
