#!/usr/bin/env python3
"""Generate the Topic 09a EPUB cover (1600x2560).

Databricks-orange-on-dark style for the Mastery Track curriculum.
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("cover.png")

W, H = 1600, 2560
# Dark background, Databricks-orange accent
BG = (18, 24, 38)
ACCENT = (255, 62, 0)  # Databricks orange/red
DARK = (245, 246, 247)
SUBTLE = (170, 180, 200)
PANEL = (28, 36, 54)

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


TITLE_FONT_PATHS = [
    "/System/Library/Fonts/Supplemental/Avenir Next.ttc",
    "/System/Library/Fonts/HelveticaNeue.ttc",
    "/Library/Fonts/Arial Bold.ttf",
]

# Safe drawable width — leave margin on each side so the title never clips.
SAFE_W = W - 240


def fit_title_font(text, max_size=140, min_size=60, max_width=SAFE_W):
    """Pick the largest font size at which `text` fits within max_width."""
    size = max_size
    while size > min_size:
        font = load_font(TITLE_FONT_PATHS, size)
        bbox = draw.textbbox((0, 0), text, font=font)
        if (bbox[2] - bbox[0]) <= max_width:
            return font
        size -= 4
    return load_font(TITLE_FONT_PATHS, min_size)


# Auto-fit both title lines so a long string like "Databricks ML Associate"
# does not clip on the 1600-px canvas.
font_title_a = fit_title_font("Databricks ML Associate")
font_title_b = fit_title_font("Mastery Track")
font_sub = load_font(
    [
        "/System/Library/Fonts/Supplemental/Avenir Next.ttc",
        "/System/Library/Fonts/HelveticaNeue.ttc",
    ],
    58,
)
font_small = load_font(
    [
        "/System/Library/Fonts/Supplemental/Avenir Next.ttc",
        "/System/Library/Fonts/HelveticaNeue.ttc",
    ],
    42,
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
draw_centered("CAREER_UPSKILL · TOPIC 09a", font_small, (255, 255, 255), 110)

# Title block
draw_centered("Databricks ML Associate", font_title_a, DARK, 660)
draw_centered("Mastery Track", font_title_b, ACCENT, 830)

# Horizontal rule
draw.rectangle([(280, 1080), (W - 280, 1086)], fill=ACCENT)

# Subtitle
draw_centered("Teaching ML from first principles", font_sub, SUBTLE, 1170)
draw_centered("76 chapters · 13 parts · ~41,000 lines", font_sub, SUBTLE, 1250)

# Part list (small text)
parts = [
    "A · Why ML exists — framing the problem",
    "B · Probability & statistics primer",
    "C · Linear algebra & calculus essentials",
    "D · The fundamental ML problem",
    "E · Feature engineering as a discipline",
    "F · Supervised algorithms — from the math",
    "G · Unsupervised algorithms",
    "H · Model evaluation theory",
    "I · Hyperparameter optimization",
    "J · Spark from zero",
    "K · pyspark.ml in depth",
    "L · Databricks platform & MLflow",
    "M · Capstone — project + exam strategy",
]
y0 = 1410
for i, line in enumerate(parts):
    draw_centered(line, font_small, DARK, y0 + i * 70)

# Footer
draw_centered("Compiled for Vatsal Raicha · 2026", font_tiny, (255, 255, 255), H - 60)

img.save(out, "PNG", optimize=True)
print(f"Wrote {out}")
