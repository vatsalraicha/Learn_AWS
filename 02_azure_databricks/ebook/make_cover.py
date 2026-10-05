#!/usr/bin/env python3
"""Generate the Topic 02 EPUB cover (1600x2560) — Azure Databricks."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("cover.png")

W, H = 1600, 2560
BG = (10, 20, 35)                # deep azure
DBX_RED = (255, 56, 33)          # Databricks coral/red
AZURE_BLUE = (0, 120, 212)       # Azure blue
TITLE = (248, 250, 252)
SUBTLE = (148, 163, 184)

img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

# Diagonal bands suggesting lakehouse layers
for i, y in enumerate(range(0, H, 240)):
    color = AZURE_BLUE if i % 2 == 0 else DBX_RED
    draw.polygon([(0, y), (W, y - 130), (W, y - 110), (0, y + 20)], fill=color)

# Solid header/footer bands
draw.rectangle([(0, 0), (W, 380)], fill=BG)
draw.rectangle([(0, H - 220), (W, H)], fill=BG)


def load_font(candidates, size):
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Avenir Next.ttc",
    "/System/Library/Fonts/HelveticaNeue.ttc",
    "/System/Library/Fonts/Helvetica.ttc",
]

font_title = load_font(FONT_CANDIDATES, 150)
font_subtitle = load_font(FONT_CANDIDATES, 62)
font_small = load_font(FONT_CANDIDATES, 46)
font_tiny = load_font(FONT_CANDIDATES, 36)


def center(text, font, y, color):
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    draw.text(((W - w) // 2, y), text, font=font, fill=color)


center("Azure", font_title, 680, TITLE)
center("Databricks", font_title, 850, TITLE)

draw.line([(W // 4, 1070), (3 * W // 4, 1070)], fill=DBX_RED, width=4)

center("Lakehouse · Delta · Unity Catalog", font_subtitle, 1140, SUBTLE)
center("MLflow 3 · Mosaic AI · HIPAA", font_subtitle, 1230, SUBTLE)

center("25 modules · 11 research dossiers", font_small, 1450, AZURE_BLUE)

center("Career_upskill — Topic 02", font_tiny, H - 320, SUBTLE)
center("2026 · Vatsal Raicha", font_tiny, H - 260, SUBTLE)

img.save(out, "PNG", optimize=True)
print(f"Cover written to {out}")
