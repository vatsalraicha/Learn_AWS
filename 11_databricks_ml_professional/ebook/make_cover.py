#!/usr/bin/env python3
"""Generate EPUB cover (1600x2560) for Databricks Certified Machine Learning Professional."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("cover.png")
W, H = 1600, 2560
BG = (245, 246, 247)
ACCENT = (255,54,33)  # Databricks orange-red
DARK = (28, 38, 56)
SUBTLE = (107, 119, 140)

img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)
draw.rectangle([(0, 0), (W, 280)], fill=ACCENT)
draw.rectangle([(0, H - 80), (W, H)], fill=ACCENT)


def load_font(candidates, size):
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


font_title = load_font(
    [
        "/System/Library/Fonts/Supplemental/Avenir Next.ttc",
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/Library/Fonts/Arial Bold.ttf",
    ],
    120,
)
font_sub = load_font(
    [
        "/System/Library/Fonts/Supplemental/Avenir Next.ttc",
        "/System/Library/Fonts/HelveticaNeue.ttc",
    ],
    56,
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


def wrap_centered(text, font, fill, y_start, max_width, line_height):
    words = text.split()
    lines = []
    cur = []
    for w in words:
        trial = " ".join(cur + [w])
        bbox = draw.textbbox((0, 0), trial, font=font)
        if (bbox[2] - bbox[0]) > max_width and cur:
            lines.append(" ".join(cur))
            cur = [w]
        else:
            cur.append(w)
    if cur:
        lines.append(" ".join(cur))
    for i, ln in enumerate(lines):
        draw_centered(ln, font, fill, y_start + i * line_height)
    return y_start + len(lines) * line_height


draw_centered("CAREER_UPSKILL · DATABRICKS CERTIFICATIONS", font_small, (255, 255, 255), 110)

y_after = wrap_centered("Databricks Certified Machine Learning Professional", font_title, DARK, 600, W - 240, 150)

draw.rectangle([(280, y_after + 80), (W - 280, y_after + 86)], fill=ACCENT)

draw_centered("Production ML on Databricks", font_sub, SUBTLE, y_after + 180)

# Tagline lines
draw_centered("16 modules · 4 domains", font_small, DARK, y_after + 360)
draw_centered("MLflow advanced · DABs · Inference Tables · Monitoring", font_small, DARK, y_after + 420)

# Footer
draw_centered("Compiled for Vatsal Raicha · 2026", font_tiny, (255, 255, 255), H - 60)

img.save(out, "PNG", optimize=True)
print(f"Wrote {out}")
