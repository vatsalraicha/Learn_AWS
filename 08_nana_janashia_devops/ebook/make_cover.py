#!/usr/bin/env python3
"""Generate the Topic 08 EPUB cover (1600x2560)."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("cover.png")

W, H = 1600, 2560
BG = (15, 23, 42)                # slate-900
ACCENT = (96, 165, 250)          # blue-400
ACCENT2 = (34, 197, 94)          # green-500 (k8s-ish)
TITLE = (248, 250, 252)          # slate-50
SUBTLE = (148, 163, 184)         # slate-400

img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

# Diagonal accent stripes (DevOps vibe)
for i, y in enumerate(range(0, H, 200)):
    color = ACCENT if i % 2 == 0 else ACCENT2
    draw.polygon([(0, y), (W, y - 100), (W, y - 80), (0, y + 20)], fill=color)

# Solid header band
draw.rectangle([(0, 0), (W, 380)], fill=BG)
draw.rectangle([(0, H - 200), (W, H)], fill=BG)


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

font_title = load_font(FONT_CANDIDATES, 140)
font_subtitle = load_font(FONT_CANDIDATES, 58)
font_small = load_font(FONT_CANDIDATES, 46)
font_tiny = load_font(FONT_CANDIDATES, 36)


def center(text, font, y, color):
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    draw.text(((W - w) // 2, y), text, font=font, fill=color)


# Title
center("Nana Janashia", font_title, 700, TITLE)
center("DevOps Curriculum", font_title, 870, TITLE)

# Divider line
draw.line([(W // 4, 1080), (3 * W // 4, 1080)], fill=ACCENT, width=4)

# Subtitle
center("DevOps · DevSecOps · GitLab CI/CD", font_subtitle, 1150, SUBTLE)
center("IT Fundamentals · CKA", font_subtitle, 1230, SUBTLE)

# Module count
center("80 modules · 5 courses", font_small, 1450, ACCENT2)

# Footer
center("Career_upskill — Topic 08", font_tiny, H - 320, SUBTLE)
center("2026 · Vatsal Raicha", font_tiny, H - 260, SUBTLE)

img.save(out, "PNG", optimize=True)
print(f"Cover written to {out}")
