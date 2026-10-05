#!/usr/bin/env python3
"""Generate the Topic 04 EPUB cover (1600x2560)."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("cover.png")

W, H = 1600, 2560
BG = (245, 246, 247)
ACCENT = (232, 119, 34)  # AWS orange
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
    150,
)
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
draw_centered("CAREER_UPSKILL · TOPIC 04", font_small, (255, 255, 255), 110)

# Title block
draw_centered("AWS for AI/ML", font_title, DARK, 680)
draw_centered("Engineers", font_title, DARK, 850)

# Horizontal rule
draw.rectangle([(280, 1100), (W - 280, 1106)], fill=ACCENT)

# Subtitle
draw_centered("57 modules — Senior Lead practitioner", font_sub, SUBTLE, 1190)
draw_centered("Capital One regulated-finance lens", font_sub, SUBTLE, 1270)

# Module list (small text)
modules = [
    "Foundations · IAM · Regions · Billing",
    "Networking from zero · VPC · PrivateLink · TGW",
    "S3 · EFS/FSx · Lake Formation · Iceberg",
    "Glue · Step Functions · MWAA",
    "12 Database modules: RDS, Aurora DSQL, DynamoDB,",
    "DocumentDB, MemoryDB, Redshift, Snowflake, Athena,",
    "Neptune, OpenSearch, Vector decision framework",
    "MSK · Kinesis · EKS · Lambda · SageMaker (×8)",
    "Bedrock · Q · Self-hosted FM · Databricks on AWS",
    "Security · Cloud Custodian · SR 11-7 · KServe",
    "Cert path: SAA → MLA → DEA → SCS → SAP → AIP",
]
y0 = 1430
for i, line in enumerate(modules):
    draw_centered(line, font_small, DARK, y0 + i * 78)

# Footer
draw_centered("Compiled for Vatsal Raicha · 2026", font_tiny, (255, 255, 255), H - 60)

img.save(out, "PNG", optimize=True)
print(f"Wrote {out}")
