#!/usr/bin/env python3
"""Generate the Topic 03 EPUB cover (1600x2560) — Recommendation Engines."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("cover.png")

W, H = 1600, 2560
BG = (24, 16, 40)                # deep purple-black
NETFLIX_RED = (229, 9, 20)
SPOTIFY_GREEN = (30, 215, 96)
META_BLUE = (24, 119, 242)
TITLE = (250, 250, 250)
SUBTLE = (180, 175, 195)

img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

# Connected-graph motif: dots + thin lines suggesting collaborative filtering / GNN
import random
random.seed(42)
nodes = [(random.randint(40, W - 40), random.randint(40, H - 40)) for _ in range(60)]
for n in nodes:
    color = random.choice([NETFLIX_RED, SPOTIFY_GREEN, META_BLUE])
    draw.ellipse([n[0] - 8, n[1] - 8, n[0] + 8, n[1] + 8], fill=color)
# Sparse edges
for i in range(80):
    a, b = random.sample(nodes, 2)
    draw.line([a, b], fill=(60, 50, 80), width=1)

# Solid header/footer
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

font_title = load_font(FONT_CANDIDATES, 130)
font_subtitle = load_font(FONT_CANDIDATES, 58)
font_small = load_font(FONT_CANDIDATES, 46)
font_tiny = load_font(FONT_CANDIDATES, 36)


def center(text, font, y, color):
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    draw.text(((W - w) // 2, y), text, font=font, fill=color)


center("Recommendation", font_title, 680, TITLE)
center("Engines & Ads", font_title, 830, TITLE)

draw.line([(W // 4, 1040), (3 * W // 4, 1040)], fill=SPOTIFY_GREEN, width=4)

center("Two-tower · GNN · LLM · CTR · Auctions", font_subtitle, 1110, SUBTLE)
center("Netflix · Meta · TikTok · Google", font_subtitle, 1200, SUBTLE)

center("34 modules · 12 code artifacts", font_small, 1420, NETFLIX_RED)

center("Career_upskill — Topic 03", font_tiny, H - 320, SUBTLE)
center("2026 · Vatsal Raicha", font_tiny, H - 260, SUBTLE)

img.save(out, "PNG", optimize=True)
print(f"Cover written to {out}")
