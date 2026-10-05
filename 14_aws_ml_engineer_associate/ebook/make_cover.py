#!/usr/bin/env python3
"""Generate the Topic 14 EPUB cover (1600x2560).

AWS-orange-on-dark-navy for the MLA-C01 Practice Guide.
Title page line: "AWS Certified Machine Learning Engineer – Associate Practice Guide"
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("cover.png")

W, H = 1600, 2560
# AWS-themed palette
BG = (35, 47, 62)           # AWS dark navy
ACCENT = (255, 153, 0)      # AWS orange
DARK = (245, 246, 247)
SUBTLE = (180, 195, 215)
PANEL = (50, 65, 85)

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

SAFE_W = W - 240


def fit_title_font(text, max_size=120, min_size=40, max_width=SAFE_W):
    """Pick the largest font size at which `text` fits within max_width."""
    size = max_size
    while size > min_size:
        font = load_font(TITLE_FONT_PATHS, size)
        bbox = draw.textbbox((0, 0), text, font=font)
        if (bbox[2] - bbox[0]) <= max_width:
            return font
        size -= 4
    return load_font(TITLE_FONT_PATHS, min_size)


# Title is long — split across 3 lines to keep each line readable
font_t1 = fit_title_font("AWS Certified", max_size=140)
font_t2 = fit_title_font("Machine Learning Engineer", max_size=110)
font_t3 = fit_title_font("— Associate —", max_size=90)
font_practice = fit_title_font("Practice Guide", max_size=130)

font_sub = load_font(
    [
        "/System/Library/Fonts/Supplemental/Avenir Next.ttc",
        "/System/Library/Fonts/HelveticaNeue.ttc",
    ],
    52,
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
    36,
)


def draw_centered(text, font, fill, y):
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    draw.text(((W - w) / 2, y), text, font=font, fill=fill)


# Header band text
draw_centered("CAREER_UPSKILL · TOPIC 14 · MLA-C01", font_small, (255, 255, 255), 110)

# Title block — three certification lines + "Practice Guide" highlight
draw_centered("AWS Certified", font_t1, DARK, 540)
draw_centered("Machine Learning Engineer", font_t2, DARK, 700)
draw_centered("— Associate —", font_t3, SUBTLE, 840)

# Horizontal rule
draw.rectangle([(280, 980), (W - 280, 986)], fill=ACCENT)

# "Practice Guide" emphasized in orange
draw_centered("Practice Guide", font_practice, ACCENT, 1050)

# Subtitle stats
draw_centered("64 chapters · 11 parts · ~54,000 lines", font_sub, SUBTLE, 1280)
draw_centered("From first principles to exam day", font_sub, SUBTLE, 1360)

# Part list (small text)
parts = [
    "A · The MLE landscape on AWS",
    "B · AWS foundations (IAM, S3, VPC, KMS, compute)",
    "C · Data ingestion & storage",
    "D · Data preparation & features",
    "E · Model development on SageMaker",
    "F · HPO & distributed training",
    "G · Deployment & inference",
    "H · Orchestration & CI/CD",
    "I · Monitoring, drift & governance",
    "J · Security, networking & cost",
    "K · AI services + GenAI + Capstone + Exam day",
]
y0 = 1520
for i, line in enumerate(parts):
    draw_centered(line, font_small, DARK, y0 + i * 75)

# Footer
draw_centered("Compiled for Vatsal Raicha · 2026", font_tiny, (255, 255, 255), H - 55)

img.save(out, "PNG", optimize=True)
print(f"Wrote {out}")
