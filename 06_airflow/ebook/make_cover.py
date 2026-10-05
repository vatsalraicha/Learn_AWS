#!/usr/bin/env python3
"""Generate the Topic 06 EPUB cover (1600x2560)."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("cover.png")

W, H = 1600, 2560
BG = (245, 246, 247)
ACCENT = (17, 122, 139)  # Airflow teal
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


draw_centered("CAREER_UPSKILL · TOPIC 06", font_small, (255, 255, 255), 110)

draw_centered("Apache", font_title, DARK, 680)
draw_centered("Airflow", font_title, DARK, 850)

draw.rectangle([(280, 1100), (W - 280, 1106)], fill=ACCENT)

draw_centered("32 modules — for AI/ML Engineers", font_sub, SUBTLE, 1190)
draw_centered("Multi-cloud safe data exposure", font_sub, SUBTLE, 1270)

modules = [
    "History · core concepts · architecture · executors",
    "TaskFlow · dynamic mapping · deferrable · datasets",
    "Sensors · Triggerer · Connections · Secrets backends",
    "Securing Airflow · RBAC · OIDC · audit · networking",
    "XCom · custom backends · OpenLineage · observability",
    "Airflow on K8s · KubernetesPodOperator · KEDA",
    "MWAA on AWS (PRIVATE_ONLY · IAM · Secrets Mgr)",
    "Cloud Composer on GCP (WIF · PSC · CMEK)",
    "Azure Managed Airflow (Fabric · git-sync · Key Vault)",
    "Astronomer Astro · Helm on-prem · air-gap",
    "Snowflake · Databricks · Spark · SageMaker · dbt",
    "Alternatives: Step Functions · Prefect · Dagster · Argo",
    "Airflow 3.0 · Task SDK · Assets · DAG versioning",
    "Certs: AWS DEA-C01 · Astronomer DAG Authoring",
]
y0 = 1410
for i, line in enumerate(modules):
    draw_centered(line, font_small, DARK, y0 + i * 70)

draw_centered("Compiled for Vatsal Raicha · 2026", font_tiny, (255, 255, 255), H - 60)

img.save(out, "PNG", optimize=True)
print(f"Wrote {out}")
