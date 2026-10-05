#!/usr/bin/env python3
"""Generate the Topic 07 EPUB cover (1600x2560)."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("cover.png")

W, H = 1600, 2560
BG = (246, 248, 250)               # GitHub bg-subtle
ACCENT = (9, 105, 218)             # GitHub blue
DARK = (31, 35, 40)
SUBTLE = (87, 96, 106)
GREEN = (35, 134, 54)              # GitHub green (signed-commit verified)

img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

# Top + bottom bands
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


draw_centered("CAREER_UPSKILL · TOPIC 07", font_small, (255, 255, 255), 110)

draw_centered("Git, GitHub", font_title, DARK, 600)
draw_centered("& DevOps", font_title, DARK, 770)

draw.rectangle([(280, 1020), (W - 280, 1026)], fill=ACCENT)

draw_centered("57 modules — for AI/ML Engineers", font_sub, SUBTLE, 1110)
draw_centered("Capital One — Sr Lead AI/ML lens", font_sub, GREEN, 1190)

modules = [
    "Git object model · branching · rebase · recovery · reflog",
    "GitHub PRs · CODEOWNERS · Rulesets · signed commits",
    "Trunk-based · feature flags · InnerSource",
    "Repo architecture · pyproject.toml · ADRs · release-please",
    "Actions: YAML · events · matrix · cache · artifacts",
    "Reusable workflows · composite actions · ARC · GPU runners",
    "OIDC to AWS · environments · GITHUB_TOKEN scoping",
    "GHAS: secret scanning · CodeQL · Dependabot · SBOM · SLSA",
    "Compliance: SAML/SCIM · audit logs · SR 11-7",
    "Notebook discipline · DVC · pre-commit · reproducibility",
    "MLOps: CI · validation gates · MLflow · SageMaker · rollback",
    "AWS deploy: SageMaker · ECS/EKS · Lambda · CDK · cross-account",
    "Jenkins: declarative · multibranch · shared libraries · IRSA",
    "Copilot · Claude Code · governance · certifications",
]
y0 = 1340
for i, line in enumerate(modules):
    draw_centered(line, font_small, DARK, y0 + i * 70)

draw_centered("Compiled for Vatsal Raicha · 2026", font_tiny, (255, 255, 255), H - 60)

img.save(out, "PNG", optimize=True)
print(f"Wrote {out}")
