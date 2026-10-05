#!/usr/bin/env python3
"""Generate a clean EPUB cover (1600x2560, the standard ebook cover aspect)."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("cover.png")

W, H = 1600, 2560
BG = (245, 246, 247)
ACCENT = (24, 90, 157)
DARK = (28, 38, 56)
SUBTLE = (107, 119, 140)

img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

# Accent band along the top
draw.rectangle([(0, 0), (W, 280)], fill=ACCENT)
# Thin band along the bottom
draw.rectangle([(0, H - 80), (W, H)], fill=ACCENT)


def load_font(candidates, size):
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


# macOS-friendly font fallbacks
font_title = load_font(
    [
        "/System/Library/Fonts/Supplemental/Avenir Next.ttc",
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/Library/Fonts/Arial Bold.ttf",
    ],
    140,
)
font_sub = load_font(
    [
        "/System/Library/Fonts/Supplemental/Avenir Next.ttc",
        "/System/Library/Fonts/HelveticaNeue.ttc",
    ],
    62,
)
font_small = load_font(
    [
        "/System/Library/Fonts/Supplemental/Avenir Next.ttc",
        "/System/Library/Fonts/HelveticaNeue.ttc",
    ],
    44,
)
font_tiny = load_font(
    [
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/Courier New.ttf",
    ],
    38,
)


def draw_centered(text, font, fill, y):
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    draw.text(((W - w) / 2, y), text, font=font, fill=fill)


# Header band text
draw_centered("CAREER_UPSKILL · TOPIC 01", font_small, (255, 255, 255), 110)

# Title block
draw_centered("RAG, Vector Databases", font_title, DARK, 720)
draw_centered("& Reranking", font_title, DARK, 880)

# Horizontal rule
draw.rectangle([(280, 1130), (W - 280, 1136)], fill=ACCENT)

# Subtitle
draw_centered("A practitioner's reference for", font_sub, SUBTLE, 1220)
draw_centered("AI architects in regulated industries", font_sub, SUBTLE, 1300)

# Module list (small text)
modules = [
    "Foundations · Embeddings · Vector Databases",
    "Extraction · Chunking · Retrieval Strategies",
    "Reranking · Advanced & Agentic RAG",
    "Evaluation (Methodology · Online · Observability)",
    "Production · Code Routing · Personalization",
    "Grounding & Citation · Multilingual",
    "Domain Case Studies · Security & Privacy",
    "Frontier Patterns · Web & Real-time",
    "Production Engineering · Benchmarks",
]
y0 = 1500
for i, line in enumerate(modules):
    draw_centered(line, font_small, DARK, y0 + i * 78)

# Footer
draw_centered("Compiled for Vatsal Raicha · 2026", font_tiny, (255, 255, 255), H - 60)

img.save(out, "PNG", optimize=True)
print(f"Wrote {out}")
