"""
AWS Certified Machine Learning Engineer - Associate (MLA-C01) Practice Guide deck.

Teaching companion to the textbook at topics/14_aws_ml_engineer_associate/.
Visual style mirrors topics/09a_databricks_ml_associate/pptx/build_deck.py.
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree

# ---------- color palette (verbatim from Topic 09a) ----------
BG       = RGBColor(0x12, 0x18, 0x26)   # dark navy
PANEL    = RGBColor(0x1B, 0x23, 0x36)
ACCENT   = RGBColor(0xFF, 0x3E, 0x00)   # orange
ACCENT_D = RGBColor(0xC8, 0x31, 0x00)
WHITE    = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT    = RGBColor(0xF5, 0xF6, 0xF7)
MUTED    = RGBColor(0xAA, 0xB4, 0xC8)
GREY     = RGBColor(0x6C, 0x77, 0x8C)
GREEN    = RGBColor(0x4C, 0xC0, 0x70)
BLUE     = RGBColor(0x3D, 0x8B, 0xFD)
YELLOW   = RGBColor(0xF5, 0xC0, 0x42)
RED      = RGBColor(0xE0, 0x4B, 0x4B)
PURPLE   = RGBColor(0xA0, 0x6C, 0xD5)

prs = Presentation()
prs.slide_width  = Inches(13.333)
prs.slide_height = Inches(7.5)
SW, SH = prs.slide_width, prs.slide_height
BLANK = prs.slide_layouts[6]


# ---------- helpers ----------
def add_slide():
    s = prs.slides.add_slide(BLANK)
    bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SW, SH)
    bg.line.fill.background()
    bg.fill.solid()
    bg.fill.fore_color.rgb = BG
    bg.shadow.inherit = False
    return s

def textbox(slide, x, y, w, h, text, *, size=18, bold=False, color=LIGHT,
            align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, font="Calibri"):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Emu(0)
    tf.margin_top = tf.margin_bottom = Emu(0)
    tf.vertical_anchor = anchor
    lines = text.split("\n") if isinstance(text, str) else text
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        r = p.add_run()
        r.text = line
        r.font.name = font
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.color.rgb = color
    return tb

def rich_textbox(slide, x, y, w, h, runs, *, align=PP_ALIGN.LEFT,
                 anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Emu(0)
    tf.margin_top = tf.margin_bottom = Emu(0)
    tf.vertical_anchor = anchor
    for i, para in enumerate(runs):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        for txt, props in para:
            r = p.add_run()
            r.text = txt
            r.font.name = props.get("font", "Calibri")
            r.font.size = Pt(props.get("size", 16))
            r.font.bold = props.get("bold", False)
            r.font.italic = props.get("italic", False)
            r.font.color.rgb = props.get("color", LIGHT)
    return tb

def rect(slide, x, y, w, h, fill=PANEL, line=None, line_w=0.75):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(line_w)
    s.shadow.inherit = False
    return s

def rrect(slide, x, y, w, h, fill=PANEL, line=None, line_w=0.75):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(line_w)
    s.shadow.inherit = False
    return s

def ellipse(slide, x, y, w, h, fill=PANEL, line=None):
    s = slide.shapes.add_shape(MSO_SHAPE.OVAL, x, y, w, h)
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(0.75)
    s.shadow.inherit = False
    return s

def arrow(slide, x1, y1, x2, y2, color=ACCENT, weight=2.0):
    c = slide.shapes.add_connector(2, x1, y1, x2, y2)
    c.line.color.rgb = color
    c.line.width = Pt(weight)
    ln = c.line._get_or_add_ln()
    tail = etree.SubElement(ln, qn('a:tailEnd'))
    tail.set('type', 'triangle')
    tail.set('w', 'med')
    tail.set('h', 'med')
    return c

def line(slide, x1, y1, x2, y2, color=MUTED, weight=1.0, dash=False):
    c = slide.shapes.add_connector(1, x1, y1, x2, y2)
    c.line.color.rgb = color
    c.line.width = Pt(weight)
    if dash:
        ln = c.line._get_or_add_ln()
        ln.set('cap', 'flat')
        prstDash = etree.SubElement(ln, qn('a:prstDash'))
        prstDash.set('val', 'dash')
    return c

def boxlabel(slide, x, y, w, h, text, *, fill=PANEL, color=LIGHT, size=14,
             bold=False, line=None):
    rect(slide, x, y, w, h, fill=fill, line=line)
    textbox(slide, x, y, w, h, text, size=size, color=color, bold=bold,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

def rboxlabel(slide, x, y, w, h, text, *, fill=PANEL, color=LIGHT, size=14,
              bold=False, line=None):
    rrect(slide, x, y, w, h, fill=fill, line=line)
    textbox(slide, x, y, w, h, text, size=size, color=color, bold=bold,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

def slide_title(slide, title, *, color=WHITE):
    rect(slide, Inches(0.5), Inches(0.45), Inches(0.12), Inches(0.55),
         fill=ACCENT)
    textbox(slide, Inches(0.75), Inches(0.4), Inches(12), Inches(0.7),
            title, size=28, bold=True, color=color)

def slide_subtitle(slide, sub):
    textbox(slide, Inches(0.75), Inches(1.0), Inches(12), Inches(0.4),
            sub, size=14, color=MUTED, bold=False)

def footer(slide, ref):
    textbox(slide, Inches(0.5), Inches(7.1), Inches(8), Inches(0.3),
            "AWS MLA-C01 · Practice Guide", size=10, color=GREY)
    textbox(slide, Inches(9), Inches(7.1), Inches(3.83), Inches(0.3),
            ref, size=10, color=ACCENT, align=PP_ALIGN.RIGHT, bold=True)


def add_table(slide, x, y, w, h, headers, rows, *,
              header_fill=ACCENT, header_color=WHITE, body_fill=PANEL,
              alt_fill=None, body_color=LIGHT, font_size=12,
              header_size=13, col_widths=None):
    if alt_fill is None:
        alt_fill = RGBColor(0x22, 0x2C, 0x40)
    nrows = len(rows) + 1
    ncols = len(headers)
    tbl_shape = slide.shapes.add_table(nrows, ncols, x, y, w, h)
    tbl = tbl_shape.table
    if col_widths:
        total = sum(col_widths)
        for i, cw in enumerate(col_widths):
            tbl.columns[i].width = int(w * cw / total)
    for j, hd in enumerate(headers):
        cell = tbl.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = header_fill
        cell.text = ""
        tf = cell.text_frame
        tf.margin_left = tf.margin_right = Inches(0.08)
        tf.margin_top = tf.margin_bottom = Inches(0.04)
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT
        r = p.add_run()
        r.text = hd
        r.font.name = "Calibri"
        r.font.size = Pt(header_size)
        r.font.bold = True
        r.font.color.rgb = header_color
    for i, row in enumerate(rows):
        fill = body_fill if i % 2 == 0 else alt_fill
        for j, val in enumerate(row):
            cell = tbl.cell(i + 1, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = fill
            cell.text = ""
            tf = cell.text_frame
            tf.margin_left = tf.margin_right = Inches(0.08)
            tf.margin_top = tf.margin_bottom = Inches(0.04)
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT
            r = p.add_run()
            r.text = str(val)
            r.font.name = "Calibri"
            r.font.size = Pt(font_size)
            r.font.color.rgb = body_color
    return tbl


# ---------- section divider ----------
def section_divider(letter, theme, chapters):
    s = add_slide()
    rect(s, 0, 0, SW, SH, fill=ACCENT)
    rect(s, 0, Inches(6.6), SW, Inches(0.9), fill=BG)
    textbox(s, Inches(0.75), Inches(2.2), Inches(12), Inches(0.7),
            f"Part {letter}", size=44, bold=True, color=WHITE)
    textbox(s, Inches(0.75), Inches(3.1), Inches(12), Inches(1.6),
            theme, size=44, bold=True, color=WHITE)
    textbox(s, Inches(0.75), Inches(4.9), Inches(12), Inches(0.5),
            chapters, size=20, color=WHITE)
    textbox(s, Inches(0.75), Inches(6.75), Inches(12), Inches(0.5),
            "AWS MLA-C01 · Practice Guide",
            size=12, color=MUTED)
    return s


def chapter_slide(title, ref, bullets):
    """Standard chapter slide: title + 4-6 bullets in a panel."""
    s = add_slide()
    slide_title(s, title)
    # body panel
    rrect(s, Inches(0.5), Inches(1.5), Inches(12.33), Inches(5.3),
          fill=PANEL, line=ACCENT)
    # bullets
    y0 = Inches(1.75)
    h_total = Inches(4.9)
    n = len(bullets)
    step = h_total / max(n, 1)
    for i, b in enumerate(bullets):
        bx = Inches(0.85)
        by = y0 + step * i
        # accent dot
        ellipse(s, bx, by + Inches(0.13), Inches(0.16), Inches(0.16), fill=ACCENT)
        textbox(s, Inches(1.15), by, Inches(11.6), step,
                b, size=14, color=LIGHT)
    footer(s, ref)
    return s


# =======================================================================
# FRONT MATTER
# =======================================================================

def front_title():
    s = add_slide()
    rect(s, 0, 0, Inches(0.6), SH, fill=ACCENT)
    textbox(s, Inches(1.0), Inches(2.0), Inches(11), Inches(1.6),
            "AWS Certified Machine Learning Engineer", size=44,
            color=WHITE, bold=True)
    textbox(s, Inches(1.0), Inches(2.95), Inches(11), Inches(1.0),
            "– Associate", size=44, color=WHITE, bold=True)
    rect(s, Inches(1.0), Inches(4.2), Inches(2.5), Inches(0.06), fill=ACCENT)
    textbox(s, Inches(1.0), Inches(4.4), Inches(11), Inches(0.8),
            "Practice Guide", size=36, color=ACCENT, bold=True)
    textbox(s, Inches(1.0), Inches(6.75), Inches(11), Inches(0.4),
            "Career upskill · Topic 14", size=11, color=GREY)


def front_audience():
    s = add_slide()
    slide_title(s, "Who this deck is for · How to use it")
    rrect(s, Inches(0.75), Inches(1.6), Inches(5.9), Inches(4.8),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(1.0), Inches(1.8), Inches(5.4), Inches(0.5),
            "AUDIENCE", size=14, color=ACCENT, bold=True)
    textbox(s, Inches(1.0), Inches(2.3), Inches(5.4), Inches(4),
            ("• Strong Python; ML fundamentals assumed (Topic 9a "
             "covers the math from first principles).\n\n"
             "• AWS taught at a working-engineer level — IAM, S3, "
             "VPC reviewed but not from zero.\n\n"
             "• You’re sitting MLA-C01, but more importantly you "
             "want to ship production ML on AWS without surprises."),
            size=14, color=LIGHT)
    rrect(s, Inches(6.85), Inches(1.6), Inches(5.9), Inches(4.8),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(7.1), Inches(1.8), Inches(5.4), Inches(0.5),
            "HOW TO USE", size=14, color=ACCENT, bold=True)
    textbox(s, Inches(7.1), Inches(2.3), Inches(5.4), Inches(4),
            ("• Each chapter slide is a self-contained concept lens, "
             "sourced from the textbook’s Goal + Exam alerts.\n\n"
             "• Footer references the chapter where the depth lives. "
             "Always go to the book for derivations and IaC.\n\n"
             "• The deck is text-dense by design — every bullet "
             "is an exam-grade fact, not a generic summary."),
            size=14, color=LIGHT)
    footer(s, "Preface")


def front_contents():
    s = add_slide()
    slide_title(s, "Contents")
    slide_subtitle(s, "Eleven parts · 64 chapters · four exam domains")
    headers = ["#", "Theme", "What it covers", "Chs"]
    rows = [
        ["A", "Landscape",                "Role + exam + AWS ML stack map",       "1 – 4"],
        ["B", "AWS foundations",          "IAM, S3, VPC, KMS, compute",           "5 – 9"],
        ["C", "Data ingestion & storage", "Formats, FSx, Kinesis, Glue, EMR",     "10 – 15"],
        ["D", "Data prep & features",     "Glue jobs, DataBrew, Wrangler, FS",    "16 – 21"],
        ["E", "Model development",        "Studio, built-ins, BYOC, MLflow",      "22 – 30"],
        ["F", "HPO & distributed",        "AMT, FSDP/SMDDP, Spot, cost",          "31 – 34"],
        ["G", "Deployment & inference",   "Endpoint types, MME, autoscale, edge", "35 – 42"],
        ["H", "Orchestration & CI/CD",    "Pipelines, Step Fns, EventBridge, IaC","43 – 47"],
        ["I", "Monitoring & governance",  "Model Monitor, drift, Registry, A/B",  "48 – 52"],
        ["J", "Security & cost",          "PassRole, VPC, KMS, GDPR, FinOps",     "53 – 58"],
        ["K", "AI services + GenAI + capstone", "Bedrock, RAG, fraud capstone, exam", "59 – 64"],
    ]
    add_table(s, Inches(0.75), Inches(1.55), Inches(11.83), Inches(5.4),
              headers, rows, col_widths=[1, 4, 8, 2], font_size=12,
              header_size=13)
    footer(s, "Contents")


def front_exam_mechanics():
    s = add_slide()
    slide_title(s, "MLA-C01 exam mechanics")
    slide_subtitle(s, "What you sit on exam day — the numbers to memorise")
    # 4 stat tiles top row
    tiles = [
        ("65", "questions\n50 scored + 15 unscored", BLUE),
        ("130 min", "no scheduled breaks\nthe clock runs continuously", ACCENT),
        ("720 / 1000", "passing scaled score\nnot 700, not 750", GREEN),
        ("compensatory", "no per-domain minimum\nstrong areas carry weak", PURPLE),
    ]
    x = Inches(0.5); y = Inches(1.7); w = Inches(3.05); h = Inches(2.5)
    for big, sub, c in tiles:
        rrect(s, x, y, w, h, fill=PANEL, line=c)
        textbox(s, x, y + Inches(0.35), w, Inches(0.9), big, size=32,
                bold=True, color=c, align=PP_ALIGN.CENTER)
        textbox(s, x + Inches(0.2), y + Inches(1.35), w - Inches(0.4),
                Inches(1.0), sub, size=12, color=LIGHT, align=PP_ALIGN.CENTER)
        x += w + Inches(0.2)
    # bottom rules
    rrect(s, Inches(0.5), Inches(4.4), Inches(12.33), Inches(2.4),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(0.75), Inches(4.5), Inches(12), Inches(0.5),
            "Five question formats", size=14, bold=True, color=ACCENT)
    textbox(s, Inches(0.75), Inches(4.95), Inches(12), Inches(1.8),
            ("• Multiple choice (1 of 4) · Multiple response "
             "(2–3 of 5–6, all-or-nothing scoring) · Ordering "
             "(3–6 items) · Matching (3–6 prompts) · "
             "Case study (multi-question scenario)\n\n"
             "• No penalty for guessing — never leave a blank. A "
             "1-in-2 guess on a flagged question is +0.5 expected.\n\n"
             "• Pace: ~1m 56s per scored question; fatigue hits "
             "around Q60 — plan a mental reset at the 100-minute mark."),
            size=13, color=LIGHT)
    footer(s, "Ch 2")


def front_domains():
    s = add_slide()
    slide_title(s, "The four exam domains")
    slide_subtitle(s, "Where the 50 scored questions actually come from")
    domains = [
        ("Domain 1", "Data Preparation for ML", "28%",
         "Ingest · transform · validate · feature engineer\n"
         "Glue · EMR · Kinesis · DataBrew · Wrangler\n"
         "Feature Store · Ground Truth · Clarify pre-train bias",
         BLUE),
        ("Domain 2", "ML Model Development", "26%",
         "Choose modelling approach · train · tune · analyse\n"
         "Built-ins · script mode · BYOC · JumpStart · AMT\n"
         "Distributed training · Clarify · Debugger · MLflow",
         GREEN),
        ("Domain 3", "Deployment & Orchestration", "22%",
         "Pick endpoint shape · deploy · autoscale · CI/CD\n"
         "Real-time · serverless · async · batch · MME/IC\n"
         "Pipelines · Step Functions · EventBridge · IaC",
         YELLOW),
        ("Domain 4", "Monitoring + Security + Cost", "24%",
         "Monitor · secure · govern · optimise cost\n"
         "Model Monitor · drift · Registry · Model Cards\n"
         "IAM · KMS · VPC · Spot · SageMaker SP",
         ACCENT),
    ]
    x = Inches(0.5); y = Inches(1.6); w = Inches(3.05); h = Inches(5.3)
    for name, theme, pct, body, c in domains:
        rrect(s, x, y, w, h, fill=PANEL, line=c)
        rect(s, x, y, w, Inches(0.55), fill=c)
        textbox(s, x, y, w, Inches(0.55), name, size=15, bold=True,
                color=BG if c == YELLOW else WHITE,
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        textbox(s, x + Inches(0.15), y + Inches(0.7), w - Inches(0.3),
                Inches(0.5), theme, size=13, bold=True, color=LIGHT,
                align=PP_ALIGN.CENTER)
        textbox(s, x + Inches(0.15), y + Inches(1.2), w - Inches(0.3),
                Inches(0.8), pct, size=36, bold=True, color=c,
                align=PP_ALIGN.CENTER)
        textbox(s, x + Inches(0.2), y + Inches(2.4), w - Inches(0.4),
                Inches(2.7), body, size=11, color=LIGHT)
        x += w + Inches(0.2)
    footer(s, "Ch 2")


# =======================================================================
# CHAPTER CONTENT
# =======================================================================

# Each entry: (chapter title, ref-label, [bullet strings])
PART_A = [
    ("What an ML Engineer actually does on AWS", "Ch 1", [
        "AWS defines the role with four verbs: build, operationalize, deploy, maintain — expanded into six task families (ingest+transform, train+tune, deploy+autoscale, CI/CD, monitor, secure).",
        "The role is NOT research / novel architecture / new optimizers — that’s Applied Scientist or ML Researcher work, not MLE.",
        "Domain 4 (Security + Monitoring) is 24% of the exam and IAM/KMS/VPC questions are a meaningful slice — read an IAM policy fluently or lose easy points.",
        "Failure modes map to task statements: training-serving skew → Task 1.2 + 4.1; data drift → Task 4.1 Model Monitor + 2.3 perf analysis.",
        "Feature Store exists specifically to kill training-serving skew — one computation path, two stores, byte-identical reads.",
    ]),
    ("The MLA-C01 exam dissected", "Ch 2", [
        "65 questions / 130 min / 720-to-pass / scaled 100–1000 / compensatory — no per-domain minimum.",
        "Five formats: MCQ, MRQ (all-or-nothing), Ordering (3–6 items), Matching (3–6 prompts), Case study — official AWS source numbers.",
        "Never leave a blank — there’s no penalty for guessing; a 1-in-2 guess is +0.5 expected questions correct.",
        "Bound your study with the out-of-scope list: if a topic isn’t in the 12 task statements, it isn’t on the exam.",
        "Fatigue hits around Q60 — plan a 10-second mental reset at the 100-minute mark; flag liberally on Pass 1.",
        "Online proctoring (OnVUE): closed eyes are the only legitimate thinking pose; eye-movement, second people, second devices all flag.",
    ]),
    ("The AWS ML stack — a 30,000 ft map", "Ch 3", [
        "Four layers: Foundations (EC2/S3/VPC/IAM) → Data (Glue/Athena/EMR/Kinesis) → ML platform (SageMaker, Bedrock) → AI services.",
        "Bedrock vs JumpStart: do you need to pick the GPU? Yes → JumpStart; no → Bedrock. Claude is Bedrock-exclusive; Qwen/Gemma are JumpStart-only.",
        "Private subnet can’t reach S3 → Gateway VPC endpoint for S3 (free, route-table entry). Only S3 and DynamoDB use gateway endpoints.",
        "Glue vs EMR vs Athena: serverless ETL/Catalog → Glue; custom JARs/long-lived cluster → EMR; ad-hoc SQL on S3 → Athena.",
        "Amazon Forecast retired July 2024 → SageMaker DeepAR or Canvas. Lookout for Equipment/Metrics/Vision discontinued Oct 2025.",
        "“Least operational overhead” tells: Secrets Manager (not Parameter Store), NAT Gateway (not NAT instance), EMR Serverless, Bedrock.",
    ]),
    ("SageMaker as the spine — anatomy", "Ch 4", [
        "SageMaker is an umbrella over ~50 capabilities — group by lifecycle: Studio, Training (jobs, AMT, HyperPod), Inference (4 endpoint types, IC, MME), MLOps (Pipelines, Registry, Monitor).",
        "Notebook Instance LCC timeout = 5 min; Studio LCC timeout = 15 min. Notebook LCC has OnCreate+OnStart; Studio LCC has OnStart only.",
        "Domain AuthMode (IAM vs IdC), VpcId, SubnetIds, AppNetworkAccessType, KmsKeyId — all IMMUTABLE after CreateDomain. Fix = new domain.",
        "Processing Jobs are the second-most-tested compute primitive after training jobs — they sit under Pipelines data-prep / eval / Clarify steps.",
        "SMP v2 (Dec 2023) is PyTorch-only; SMP v1 (MXNet/TF) is gone. If a question pairs SMP with TensorFlow, it’s a distractor.",
        "Most-tested number in Domain 3: real-time/serverless 6 MB payload / 60 s timeout. Larger → Async (1 GB / 1 hr) or Batch Transform.",
    ]),
]

PART_B = [
    ("IAM for ML — roles, policies, the PassRole trap", "Ch 5", [
        "Policy evaluation: explicit deny > explicit allow > implicit deny. Grants are inclusive, caps are intersective, explicit deny is final.",
        "PassRole error → fix is on the CALLER’s identity policy: add iam:PassRole on the role ARN with iam:PassedToService=sagemaker.amazonaws.com.",
        "AmazonSageMakerFullAccess is a starting point, not a destination — the substring-naming trap (role must contain “SageMaker”) bites in production.",
        "Role Manager builds new persona-based roles; Access Analyzer policy generation right-sizes an existing role from observed CloudTrail.",
        "Cross-account deploy = chain: sts:AssumeRole → local PassRole → SageMaker CreateModel. Single resource-based policy is insufficient.",
        "Never tag-scope iam:PassRole (TOCTOU race — AWS docs say “does not have reliable results”) — use ARN patterns like arn:aws:iam::*:role/ml/exec/*.",
    ]),
    ("S3 deep dive for ML workloads", "Ch 6", [
        "Express One Zone: SSE-KMS for general use, but SageMaker output to directory buckets supports SSE-S3 only — you cannot have both.",
        "S3 Vectors is cheap at-rest storage for embeddings; OpenSearch wins sub-50ms vector recall. Don’t pick Vectors for high-QPS RAG latency.",
        "Object Lock: Compliance > Governance (Compliance can’t be overridden, even by root). Picking Governance for “regulatory immutability” is wrong.",
        "FastFile supports S3Prefix only; no ManifestFile. Pipe is FIFO and doesn’t support random access — use File or FastFile for f.seek().",
        "Bucket Keys reduce SSE-KMS API cost ~99% — always enable for SageMaker batch transform / FastFile training on KMS-encrypted data.",
        "aws/s3 (AWS-managed key) cannot be used for cross-account S3 access — a customer-managed CMK is mandatory for partner-account training data.",
    ]),
    ("VPC, subnets, security groups, endpoints", "Ch 7", [
        "Security groups are stateful; NACLs are stateless — NACL ephemeral-port inbound is the most-missed NAT-Gateway rule.",
        "Distributed training nodes can’t talk to each other → the security group must reference ITSELF as a source (never 0.0.0.0/0).",
        "EnableNetworkIsolation + VpcConfig together = no internet egress AND no IAM creds in container. Single-knob answers are wrong.",
        "On-prem callers reaching S3 over Direct Connect → INTERFACE endpoint for S3 (gateway endpoints are not reachable from outside the VPC).",
        "Two VPCs sharing = peering; 3+ VPCs = Transit Gateway. The exam penalises mesh peering when TGW is the AWS-recommended answer.",
        "AppNetworkAccessType (Studio domain network mode) is immutable — cannot convert PublicInternetOnly to VpcOnly without recreating the domain.",
    ]),
    ("KMS, Secrets Manager & encryption-in-depth", "Ch 8", [
        "Three key ownership tiers: AWS-owned, AWS-managed (aws/*), customer-managed CMK. Only CMKs cross accounts and only CMKs give you key-policy control.",
        "KMSThrottlingException on SSE-KMS S3 reads → enable S3 Bucket Keys (free, one toggle, ~99% reduction). Never “switch to SSE-S3” (kills audit).",
        "Every S3 bucket has SSE-S3 on by default since Jan 2023 — that’s NOT the same as “encrypted with a CMK” for regulated workloads.",
        "Forgetting OutputDataConfig.KmsKeyId on CreateTrainingJob silently writes the model artifact under aws/s3 — no audit trail for decrypt events.",
        "AWS Config rules to enforce: sagemaker-endpoint-configuration-kms-key-configured, sagemaker-notebook-instance-kms-key-configured.",
        "Secrets Manager (rotation, cross-account, JSON) vs SSM Parameter Store (free, no rotation) — the exam picks Secrets Manager for any rotation/PII story.",
    ]),
    ("Compute primitives — EC2 families, containers, Lambda", "Ch 9", [
        "g5 (A10G 24GB) is the default GPU inference answer; g6 (L4); g6e (L40S 48GB) for ~13B LLMs on one GPU. Memorise the GPU memory ladder.",
        "p5 = H100 80GB; p5e/p5en = H200 141GB. Pick p5en when stem stresses CPU↔GPU bandwidth (Sapphire Rapids + Gen5 PCIe + 100 Gbps EBS).",
        "Inf2 is the generative-AI inference answer on Inferentia; inf1 predates LLMs and lacks accelerator memory — always a distractor on 2025+ stems.",
        "Trainium powers Anthropic’s Claude (Project Rainier, 1M Trn2 chips). Any “Anthropic on AWS” stem points to Trainium, not GPUs.",
        "Graviton + MME = NO. Multi-Model Endpoints don’t support Graviton. “MME, cheapest CPU” → c6i/m5, never m7g/c7g.",
        "Container contract is exact: /opt/ml/code/inference.py, port 8080, GET /ping (2s) + POST /invocations (60s), 8-min readiness window.",
    ]),
]

PART_C = [
    ("Data formats for ML", "Ch 10", [
        "Factorization Machines = RecordIO-protobuf only (sparse variant); XGBoost = CSV/libsvm, never RecordIO. Format mismatch is a silent killer.",
        "CSV with a header row fed to a SageMaker built-in: the first “data point” becomes the header string — strip headers or use RecordIO-protobuf.",
        "Iceberg / Hudi / Delta are TABLE formats; Parquet / Avro / ORC are FILE formats. “Iceberg uses what file format?” → Parquet + Avro manifests.",
        "Athena reads Parquet fastest; for ACID inserts to a training table queried by Athena AND Spark, the answer is Iceberg on S3 (or S3 Tables).",
        "TFRecord is TensorFlow-native; SageMaker built-ins prefer RecordIO-protobuf; XGBoost prefers CSV; DeepAR wants JSON Lines or Parquet.",
        "Convert raw JSON to a format that minimises Athena scan cost → CTAS to Snappy-compressed Parquet, partitioned on the most common filter column.",
    ]),
    ("Storage for training — S3, EFS, FSx Lustre, ONTAP", "Ch 11", [
        "Pick FastFile for “large dataset, sequential reads, no upfront download, no VPC setup”. Pick FSx Lustre for “many small files + distributed GPUs”.",
        "FSx Lustre is single-AZ — training cluster must match the AZ exactly. Multi-AZ resilience = recreate from S3 DRA or replicate.",
        "FSx ONTAP: SageMaker FileSystemConfig API does NOT accept it. Stage ONTAP → S3 (DataSync / AutoTiering), then train via FastFile/Pipe/File.",
        "Pipe vs FastFile: RecordIO-Protobuf or built-in algorithm by name → Pipe. Custom training scripts / generic loaders → FastFile.",
        "EBS billed per-instance, NOT per-cluster: 4 nodes × 2 TB VolumeSizeInGB = 8 TB provisioned, not 2 TB — cost surprise in HPO fan-out.",
        "FSx Lustre cost = storage + provisioned throughput; both bill while idle. Cheapest-fix hierarchy: delete > smaller throughput tier > IT > hsm_release.",
    ]),
    ("Streaming ingestion — KDS, Firehose, MSAF, MSK", "Ch 12", [
        "Firehose floor is 60 seconds — NEVER the answer for “sub-second” or “real-time fraud decision”, despite the marketing copy.",
        "KDS On-Demand with EFO is the modern answer for “many independent consumers, low latency, spiky workload” (Nov 2025 pricing change).",
        "Shared fan-out = pull (GetRecords, ~200 ms); EFO = push (SubscribeToShard HTTP/2, ~70 ms). If a stem reverses these, eliminate.",
        "KCL consumer checkpoints live in DynamoDB — not S3 (Flink), not the stream itself (Kafka __consumer_offsets).",
        "Use Pipes-with-filter for high-volume Kinesis/DynamoDB streams when target needs only a small percentage — Lambda ESM filtering costs more.",
        "MSAF (Managed Service for Apache Flink) is the AWS-native stream processor; MSK is managed Kafka for teams that need Kafka semantics.",
    ]),
    ("Glue Catalog, Athena, Lake Formation", "Ch 13", [
        "Column / row / cell-level security on a shared table = Lake Formation, never an IAM bucket policy (columns live INSIDE Parquet files).",
        "Crawler UpdateBehavior=LOG records new columns to logs but doesn’t update the Catalog — the classic “new column not in Athena” cause.",
        "Iceberg / Delta tables self-register through engine writes — running a Glue Crawler over them is a documented anti-pattern.",
        "Lake Formation column grant fails “because the analyst can still see the column” → revoke IAMAllowedPrincipals first.",
        "Lake Formation does NOT mask Parquet bytes — it only enforces access through engines that respect it. Revoke direct S3 IAM perms too.",
        "Glue Data Quality runs DQDL rules in the ingest job and routes failures to quarantine — Model Monitor is for inference traffic, not training inputs.",
    ]),
    ("Amazon EMR for ML data processing", "Ch 14", [
        "Stem keywords for EMR: PB scale, Spark + custom JAR, GPU Spark, Trino JDBC, Iceberg/Hudi/Delta with version pinning. Glue is otherwise the default.",
        "Three deployment models: EMR on EC2 (long-lived cluster), EMR Serverless (auto-scaled workers, ~60–120s cold start), EMR on EKS.",
        "Durable storage for cluster feature outputs = EMRFS (S3), never HDFS. HDFS vanishes when the cluster terminates.",
        "EMR Serverless is NOT Lambda — it runs Spark inside managed workers; the cold-start gap is 60–120s, not Lambda’s sub-second.",
        "Pre-initialized capacity (initialCapacity on the EMR Serverless Application) is the warm-pool knob — trades cost for instant starts.",
        "EMRStep in SageMaker Pipelines requires an existing cluster ID; for transient “no infra to maintain”, use EMRServerlessStep instead.",
    ]),
    ("Operational stores — DynamoDB, RDS, Redshift, OpenSearch", "Ch 15", [
        "DynamoDB hot partition: ProvisionedThroughputExceededException on one key → redesign partition key for higher cardinality, NOT raise total RCU.",
        "Per-partition limits are HARD: 3000 RCU / 1000 WCU / 10 GB — no amount of total-table capacity overcomes a single hot partition.",
        "Redshift ML BYOM batches 50K–220K rows per SageMaker call and times out at 370s — lower MAX_BATCH_ROWS, don’t blame the endpoint alone.",
        "OpenSearch knn_vector caps at 10,000 floats per vector. Titan 1024/1536, Cohere 1024, OpenAI 3072 — all fit; 16,384-d does not.",
        "Three engines for OpenSearch vectors — FAISS (default, fast), NMSLIB (legacy), Lucene (Java-native, broader compatibility).",
        "ElastiCache for online features when sub-ms is mandatory and you tolerate the cache-management burden; otherwise use Feature Store In-Memory.",
    ]),
]

PART_D = [
    ("AWS Glue jobs — Spark, Python shell, Ray", "Ch 16", [
        "Default to Glue when stem says “data engineer without Spark experience”, “visual ETL”, or “serverless ETL with a Catalog”.",
        "EMR Serverless wins only when the stem also mentions custom JARs, specific Spark/Iceberg/Hudi versions, or PB-scale tuning.",
        "Glue 5.0 default timeout = 8 hours (down from Glue 4.0’s 48). Migration job dying at 8 hrs → set Timeout=2880, not “switch to EMR”.",
        "Flex tier is incompatible with Glue Auto Scaling AND with G.4X+ workers. “Flex + G.4X for cost savings” fails validation.",
        "JDBC bookmark key MUST be monotonic — UUIDs and hash PKs silently miss/duplicate rows. Fix: add updated_at TIMESTAMP or auto-increment id.",
        "Four Glue runtimes: Spark, Spark Streaming, Python shell (small ETL), Ray (distributed Python). Match runtime to data shape, not preference.",
    ]),
    ("AWS Glue DataBrew", "Ch 17", [
        "Persona is the discriminator: “business analyst / non-developer / no Spark / no code” → DataBrew. “Data scientist + Feature Store” → Data Wrangler.",
        "Billing floor: $0.48 × 5 nodes = $2.40/hr minimum — terrible per-event economics for small files; Lambda wins those cases.",
        "Five primitives: Dataset, Project, Recipe, Recipe Job, Profile Job. 250+ built-in transforms; recipes are version-controlled, shareable artifacts.",
        "DataBrew + Macie + Comprehend: Macie = bucket discovery (no transform), DataBrew = column-level mask/hash, Comprehend = freeform-text PII API.",
        "Modern Data Wrangler lives inside SageMaker Canvas — Studio Classic Data Wrangler is deprecated. Don’t pick “the Data Wrangler tab in new Studio”.",
        "Canonical pairings: DataBrew + Glue Data Quality for Task 1.3 validation; DataBrew recipes embedded in Glue Studio Spark jobs for scale.",
    ]),
    ("SageMaker Data Wrangler", "Ch 18", [
        "Named in two Exam Guide task statements (1.1 and 1.2) — the only data-prep tool double-named. Its niche: ML-aware visual feature engineering.",
        "Custom-transform 80M-row pandas limit: large dataset + custom pandas → rewrite as PySpark/PySpark SQL, don’t just scale up the instance.",
        "Pre-training bias → Clarify embedded in Data Wrangler. Post-training bias → standalone Clarify Processing job or Model Monitor (Ch 48).",
        "Quick Model is NOT Autopilot — it’s a single XGBoost fit-and-score for fast feedback inside the flow, not an AutoML ensemble.",
        "Export targets: Feature Store, Pipelines, Python notebook, Spark/Glue, S3 — the multi-export surface is the moat over DataBrew.",
        "SMOTE for class imbalance is built into Data Wrangler; for boosting models, scale_pos_weight is usually a better answer than SMOTE.",
    ]),
    ("SageMaker Feature Store — online + offline", "Ch 19", [
        "In-Memory store kill-switches: 50 GiB cap, on-demand only, no offline replication, no customer-managed KMS — wrong for “training” / “CMK” / “capacity planning”.",
        "Pick In-Memory for sub-ms RTB / click-time / card-present fraud only; DAX in front of Standard is a distractor (no API integration).",
        "Throughput mode switch is rate-limited to ONE transition per 24 hours per feature group — plan for the expected workload, not instantaneous spike.",
        "PutRecord writes to BOTH online and offline stores from a single code path — the structural property that kills training-serving skew.",
        "BatchGetRecord caps at 100 records per call across all groups — shard into parallel calls for higher fan-out, never claim it does 1000.",
        "RecordIdentifier + EventTime are mandatory schema for point-in-time-correct training joins. Offline store moved to Iceberg in 2024.",
    ]),
    ("Data labeling — Ground Truth, GT Plus, A2I, MTurk", "Ch 20", [
        "HIPAA / PHI / confidential / regulated: NEVER MTurk. Valid answers are private workforce, or Ground Truth self-service — NOT Ground Truth Plus.",
        "Active learning minimum is 1,250 objects (API constraint), recommended 5,000 (cost-positive). Below 1,250, active learning isn’t available.",
        "Augmented manifest is JSON LINES (each line a separate JSON object), not JSON. json.load() on the whole file fails on line 2.",
        "Ground Truth Plus is NOT HIPAA-eligible as of early 2026 — the managed workforce sits outside the BAA boundary.",
        "Five-word mnemonic: “Ground Truth makes labels; A2I checks labels.” Before-training → GT; after-training (human review of predictions) → A2I.",
        "AugmentedManifestFile is the only output that flows directly into a SageMaker training job without a reshape step.",
    ]),
    ("Bias detection & data integrity — Clarify, Glue DQ, Macie", "Ch 21", [
        "Clarify works on tabular, text, image, multi-modal since 2023 — old material limiting it to tabular is stale.",
        "AWS-native synthetic generation: SDV on SageMaker Processing, or Bedrock LLM paraphrase. No “Amazon Synthetic Data Service” — it’s a distractor.",
        "Composite DQDL rule scope defaults to COLUMN-level; for per-row OR-style validation, switch composite evaluation to ROW.",
        "Glue Data Quality is the managed product; Deequ is the open-source library under it. Custom Spark job is not the right answer.",
        "Macie is S3-ONLY. PII in RDS/DynamoDB/Redshift → Comprehend DetectPiiEntities in Lambda/Glue, or DataBrew PII transforms.",
        "Macie does NOT publish to SNS directly — path is Macie → EventBridge → SNS/Lambda/Step Functions/Security Hub.",
    ]),
]

PART_E = [
    ("SageMaker Studio anatomy & training-job lifecycle", "Ch 22", [
        "LCC timeout: Notebook Instance = 5 min, Studio = 15 min — long pip-install failing under 15 min is a Studio LCC question.",
        "Domain immutability: AuthMode, VpcId, SubnetIds, AppNetworkAccessType, KmsKeyId — all immutable. UpdateDomain CANNOT fix them.",
        "VpcOnly Studio + “scientists still need pip install” → CodeArtifact as a private PyPI proxy reached via PrivateLink (NAT-GW violates “no internet”).",
        "model.tar.gz (/opt/ml/model/) is for the next pipeline step; output.tar.gz (/opt/ml/output/data/) is the side-channel — don’t confuse them.",
        "Spot invariant: MaxWaitTimeInSeconds ≥ MaxRuntimeInSeconds. Sane default = MaxRuntime + 3600. “Half of MaxRuntime” fails validation.",
        "Studio Classic vs Studio (new): “SageMaker Studio” in MLA-C01 means Studio inside SageMaker AI, NOT Unified Studio.",
    ]),
    ("SageMaker built-in algorithms", "Ch 23", [
        "When 3 of 4 algorithm names are real built-ins and one is famous-but-not-AWS (DBSCAN, t-SNE, isolation forest, Prophet) — famous-but-not-AWS is wrong.",
        "XGBoost CSV: label is column 0, NO header row. Forgetting the header is the single most-tested data-format detail in built-ins.",
        "For imbalanced classification with XGBoost, prefer scale_pos_weight over SMOTE — boosting reweights loss natively.",
        "Linear Learner / k-means / PCA / FM / NTM / Object2Vec accept RecordIO-protobuf (often via Pipe). Object Detection is GPU single-instance.",
        "DeepAR consumes JSON Lines or Parquet with start, target, cat, dynamic_feat fields. It replaced retired Amazon Forecast for the exam.",
        "early_stopping_rounds requires a validation channel — omit the channel and you silently never early-stop.",
    ]),
    ("Script mode — TensorFlow, PyTorch, HuggingFace, Sklearn", "Ch 24", [
        "HuggingFace Estimator wraps PyTorch OR TensorFlow DLC — pass one version arg, not both; always include transformers_version.",
        "/opt/ml/model/ is for the model artifact (→ model.tar.gz); /opt/ml/output/data/ is for side artifacts (→ output.tar.gz). Wrong path = empty tarball.",
        "SM_MODEL_DIR → /opt/ml/model; SM_OUTPUT_DATA_DIR → /opt/ml/output/data. Distractors: /tmp/model, ~/model, /var/sagemaker/model.",
        "requirements.txt cold-start cost: 14-min installs → build a custom Docker image extending the DLC, push to ECR, reference via image_uri.",
        "distribution= MUST be set when instance_count > 1 — without it, 4 nodes silently run as single-process on node 0, billing 4x for 1x work.",
        "Local mode (instance_type=“local”) lets you iterate without paying for SageMaker compute — always test locally before the cloud bill.",
    ]),
    ("BYOC — bring your own container", "Ch 25", [
        "Training argv is exactly the literal “train”; inference argv is “serve”. “python train.py” or a tini wrapper are wrong by construction.",
        "Inference contract: port 8080, GET /ping (2s, HTTP 200, empty body), POST /invocations (60s), 8-min startup readiness window.",
        "/opt/ml/model/ at inference time is read-only — SageMaker extracts model.tar.gz before serve runs; never write back at request time.",
        "Production ECR repos MUST be tagMutability=IMMUTABLE. Never reference :latest in EndpointConfig — you destroy audit trail and break reproducibility.",
        "GPU MME requires NVIDIA Triton (or TorchServe) — the MMS-based CPU BYOC contract does NOT work on GPU. “Custom GPU MME handler” → Triton.",
        "Extend a DLC for 95% of cases; only build a fresh Dockerfile when the framework / CUDA version / OS userspace genuinely requires it.",
    ]),
    ("SageMaker JumpStart", "Ch 26", [
        "Bedrock is the default for FM workloads; JumpStart wins only when a specific constraint bites: open weights, model not in Bedrock, deep fine-tune control.",
        "accept_eula=True is mandatory at .deploy() AND .fit() for licensed models, and it is PER-ACCOUNT (not per-org). Bake into IaC.",
        "Marketplace subscription (AI21, Cohere) is per-account AND per-region — subscribing in us-east-1 doesn’t entitle deploy in us-west-2.",
        "Marketplace fees stack ON TOP of compute hours — build a three-column cost spreadsheet (instance + storage + Marketplace), never two.",
        "merge_lora_weights=False is the architectural gate for multi-tenant LoRA hosting on shared base + LMI/vLLM + Inference Components.",
        "Two SDK entrypoints: JumpStartModel for deploy, JumpStartEstimator for fine-tune. Sustained throughput past per-token break-even tips toward JumpStart.",
    ]),
    ("SageMaker Autopilot — AutoML done right", "Ch 27", [
        "Three modes: Ensembling (default for small data, AutoGluon under the hood), HPO (Linear Learner et al.), Auto (mode picker, fragile).",
        "Auto-mode falls back to HPO when bucket is locked-down, S3DataType=ManifestFile, or S3Uri has >1000 objects — always set Mode explicitly.",
        "Algorithm pool by mode: LightGBM → Ensembling only; SageMaker Linear Learner → HPO only. “Linear Models” in Ensembling = sklearn, not Linear Learner.",
        "AutoMLStep in SageMaker Pipelines is ENSEMBLING-only — HPO mode is not supported inside pipelines.",
        "Best-in-class teams use Autopilot ONCE: harvest the candidate notebook, then iterate by hand. It’s a starting point, not a production loop.",
        "15 supported objective metrics (Accuracy, F1, AUC, MSE, MAE, R², BalancedAccuracy, etc.) — pick the metric the BUSINESS cares about.",
    ]),
    ("Experiments + MLflow on SageMaker", "Ch 28", [
        "Native SageMaker Experiments isn’t deprecated but isn’t marketed either — “Experiments vs MLflow” on the exam → MLflow unless explicitly constrained.",
        "Managed MLflow tracking server bills per hour even when idle. Stop ≠ Delete: Stop preserves data; Delete removes metadata but keeps S3 artifacts.",
        "Serverless MLflow (Dec 2025) has NO compute charge for the tracking layer — only S3 artifact store cost. New “least cost / least ops” answer.",
        "MLflow Pipelines integration auto-creates a default MLflow App if none exists when a Pipeline runs — zero-config tracking.",
        "Same train.py body can log to either system; managed MLflow supports MLflow Model Registry → wire into SageMaker Model Registry for approval gates.",
        "Three reproducibility failure modes tracking does NOT fix: non-deterministic CUDA kernels, mutable upstream data, missing seed.",
    ]),
    ("SageMaker Clarify — post-training bias + explainability", "Ch 29", [
        "Online Explainability is configured on EndpointConfig, NOT the endpoint — create new config, then UpdateEndpoint. No live toggle exists.",
        "Disparate Impact (DI) no-bias value is 1.0 (a ratio), not 0. Four-fifths rule: acceptable band is [0.80, 1.25] — EEOC + NYC Local Law 144.",
        "Four label-free post-training metrics (DPPL, DI, FT, CDDPL) are exactly what Bias Drift Monitor runs without ground truth. Mnemonic: DDFC.",
        "Missing ShapBaseline silently synthesizes a single-row median/mode baseline — attributions look plausible but are misleading. Always supply representative samples.",
        "Online ExplainerConfig adds NumberOfSamples+1 model invocations per request — 5ms model + 200ms SLO + SHAP-on-every → must go offline batch.",
        "FMEval dataset-to-dimension map: TREX/TriviaQA (factual), CrowS-Pairs (stereotyping), RealToxicityPrompts (toxicity), BoolQ (QA accuracy).",
    ]),
    ("SageMaker Debugger & Profiler", "Ch 30", [
        "Tensor save cost exploding — raise save_interval, use reductions (mean/std/min/max), apply S3 lifecycle, or set s3_output_path=None. Not bigger instances.",
        "Fail-fast on diverging loss: ExplodingTensor rule with StopTraining() action — cheaper than manual CloudWatch dashboards every time.",
        "Debugger system monitoring still works on PyTorch 2.x; Debugger FRAMEWORK profiling is deprecated — use SageMaker Profiler (smprof) instead.",
        "Built-in rules: VanishingGradient, ExplodingTensor, Overfit, Underfit, LossNotDecreasing, PoorWeightInitialization, SaturatedActivation.",
        "Profiler reports surface low GPU utilization, CPU bottlenecks, dataloader stalls, slow IO — the actionable signal for cost-down work.",
        "Hooks attach at training-script time and stream tensors to S3; rules run in a side-car container and emit CloudWatch + StopTraining on violations.",
    ]),
]

PART_F = [
    ("SageMaker Automatic Model Tuning (AMT)", "Ch 31", [
        "Hyperband with early_stopping_type=Auto is a CONFIGURATION ERROR — always Hyperband with TrainingJobEarlyStoppingType=OFF.",
        "max_parallel_jobs=50 with Bayesian defeats the surrogate — 3 to 5 is the production sweet spot. Strategy isn’t the problem; parallelism is.",
        "Warm-start cap: 500 total trials INCLUDING parent jobs. Two 250-trial parents + 100-trial child = 600 = fails. Trim parents or child.",
        "ScalingType=Logarithmic for learning rate, L1/L2, weight decay, dropout when range spans decades — forgetting it is a top exam trap.",
        "Four strategies: Bayesian (default, GP surrogate), Random (parallel-friendly), Grid (small categorical), Hyperband (successive-halving + early stop).",
        "Two warm-start modes: IDENTICAL_DATA_AND_ALGORITHM (resume search) vs TRANSFER_LEARNING (related task on different data).",
    ]),
    ("Distributed training — FSDP, SMDDP, SMP", "Ch 32", [
        "FSDP NO_SHARD ≡ DDP — a trap. Memory-pressure answers: SHARD_GRAD_OP, FULL_SHARD, or HYBRID_SHARD (full inside-node, replicate across).",
        "SMDDP on a single p4d gives ZERO benefit — it optimises inter-node EFA collectives, NVLink does intra-node fine via NCCL.",
        "Training Compiler is deprecated; modern answer is torch.compile() for GPU, Neuron SDK for Trainium. Recognise vintage cues in the stem.",
        "HyperPod choice rule: research team wants sbatch → Slurm. K8s shop → EKS. Share GPUs between training and inference → EKS.",
        "HyperPod vs Training Jobs: long pretrains with node-failure risk → HyperPod. Short fine-tunes / dozens per day → Training Jobs.",
        "EFA is required for multi-node GPU distributed training. g5.48xlarge has no EFA — “AllReduce slow on 16 g5” → move to p4d/p5.",
    ]),
    ("Spot, Warm Pools, Checkpointing", "Ch 33", [
        "MaxWaitTimeInSeconds ≥ MaxRuntimeInSeconds, with MaxWait capped at 3600s for non-checkpointing built-ins. Get this wrong and Spot fails.",
        "Spot + Warm Pools is mutually exclusive (EnableManagedSpotTraining=True with KeepAlivePeriodInSeconds>0 = ValidationException).",
        "Atomic checkpointing required: write to temp path, then os.replace(). Saving model.state_dict() only — you lose optimizer momentum on resume.",
        "SageMaker has NO Reserved Instances. The only committed-use discount is a SageMaker AI Savings Plan — RIs apply to EC2, not SageMaker.",
        "Combine SageMaker SP (baseline coverage ~70%) + Managed Spot (long jobs) for mature production cost — SP gives floor, Spot covers spikes.",
        "Warm Pool 3600s KeepAlivePeriod per job; 28-day chain cap; HPO uses warm pools automatically since 2022 for child trial cold-start savings.",
    ]),
    ("Training-cost optimization patterns", "Ch 34", [
        "Training Compiler is in MAINTENANCE — no new releases. Modern speedups: torch.compile, Neuron SDK, right-sizing, better data pipeline.",
        "AMT MaxParallelTrainingJobs trades wall-clock for peak burn rate; it does NOT reduce total cost. 1000 trials × 5 parallel = same $ as serial.",
        "Compute Savings Plans do NOT cover SageMaker. The only SageMaker discount is a SageMaker AI Savings Plan. Ceiling 64% (3-yr all-upfront).",
        "There are NO Reserved Instances for SageMaker. Capacity-reservation analogue for HyperPod = Capacity Reservation / flexible training plan.",
        "Right-size with Inference Recommender (endpoints) and CloudWatch training metrics (no managed right-sizing for training); avoid Compute Optimizer.",
        "Pipe + FastFile modes cut training-side IO cost; pre-resize datasets before training; mix Spot + On-Demand by runtime sensitivity.",
    ]),
]

PART_G = [
    ("The four SageMaker endpoint types", "Ch 35", [
        "Four payload ceilings: real-time 6 MB, serverless 6 MB, async 1 GB, batch-transform mini-batch 100 MB. Memorise as a unit.",
        "Serverless has NO GPU, period — any LLM / transformer / vision / >6 GB model rules it out on sight.",
        "Async caps at 60 min processing and 1 GB payload — longer → Batch Transform; larger → split or Batch.",
        "“Scale to zero” + 200 MB payload → ASYNC, not serverless — payload trumps the scale-to-zero phrase.",
        "Never scale real-time on CPUUtilization — use SageMakerVariantInvocationsPerInstance. CPU isn’t monotonic in load for ML.",
        "Classic real-time can’t truly scale to zero (min=1). Use Inference Components with MinCopies=0, or serverless, or async.",
    ]),
    ("Real-time endpoints — variants, A/B, shadow", "Ch 36", [
        "Shadow ≠ A/B: shadow variant doesn’t return a response to the client — latency/throughput/output-distribution validation, not business KPIs.",
        "Rolling Updates are Inference-Component-only — doesn’t exist on standard production-variant endpoints. Variant path = BlueGreen.",
        "Auto-rollback triggers from CloudWatch ALARMS during a baking period, not from raw metrics or log lines. Alarm must be OK at deploy start.",
        "InvocationsPerInstance is the right autoscaling metric for variants/MME; InvocationsPerCopy for Inference Components. Match metric to shape.",
        "InitialVariantWeight=0.1 routes ~9% traffic — NOT zero customer impact. “Zero impact validation” → shadow variant only.",
        "Model → EndpointConfig → Endpoint triangle. EndpointConfig is immutable post-create; you Update by swapping EndpointConfig.",
    ]),
    ("Serverless inference & provisioned concurrency", "Ch 37", [
        "Provisioned Concurrency bills idle capacity continuously — add scheduled autoscaling for bursty workloads to avoid “worst of both worlds”.",
        "Serverless = CPU-only. YOLOv8, Stable Diffusion, large transformers, “wants ml.g5.xlarge” — all disqualify serverless on sight.",
        "Convert real-time to serverless is NOT in-place — you must create a new serverless endpoint and route traffic. UpdateEndpoint can’t flip shape.",
        "6 MB payload trap: 30 MB PDF / video clip = serverless wrong even though traffic shape fits. Async is the right answer.",
        "Memory tiers (1–6 GB) + MaxConcurrency. Pricing: memory × duration; PC adds per-hour idle cost.",
        "Cold starts: ~0.5–6 s typical; mitigations are PC, smaller artifacts, lower memory tiers, regional warmth, or scheduled scaling.",
    ]),
    ("Async inference & batch transform", "Ch 38", [
        "Async ceilings: 1 GB payload, 3600 s processing. Between 6 MB and 1 GB → async is the default; over 1 GB → Batch Transform or chunking.",
        "Real-time / serverless 6 MB load-balancer limit is a HARD WALL, not a guideline — it cannot be raised.",
        "After async completes, SNS success topic → subscriber Lambda → DynamoDB / next workflow step. Polling S3 is wasteful and not the documented pattern.",
        "Step Functions integrates with async via .waitForTaskToken + EventBridge rule on SageMaker async-completion event — not via endpoint polling.",
        "Batch Transform IS Spot-eligible at the standard ~70% discount (the parameter is per-account/region, not a per-job flag). Old blogs say otherwise; updated.",
        "Batch Transform mini-batch: MaxConcurrentTransforms × MaxPayloadInMB ≤ 100 MB. Manifest file allowed; S3 in / S3 out.",
    ]),
    ("Multi-Model & Multi-Container endpoints", "Ch 39", [
        "MME stem signals: many similar tenant models, skewed traffic, same framework, cost-sensitive. “First-invocation latency” → cold-load + ModelCacheHit metric.",
        "MME is NOT LLM hosting. Many LLMs / per-LLM autoscaling / scale-to-zero → Inference Components, not MME.",
        "AWS Graviton is NOT supported for MME. Cheapest CPU MME = c6i / m5. m7g / c7g are wrong by construction on MME stems.",
        "GPU MME requires Triton or TorchServe — the MMS CPU BYOC contract does not work on GPU.",
        "MME autoscaling: InvocationsPerInstance, NOT CPUUtilization — cold loads spike CPU and cause flapping.",
        "MME is NOT deprecated. IC is the right answer for per-model control / framework heterogeneity / scale-to-zero; MME is right for cheap multi-tenant.",
    ]),
    ("Endpoint auto-scaling, deployment, rollback", "Ch 40", [
        "Predictive scaling does not exist for SageMaker variants — “predictive” on a SageMaker endpoint = scheduled scaling.",
        "Default scale metric is SageMakerVariantInvocationsPerInstance — not CPU/GPU/Memory (those are EC2 ASG metrics).",
        "Cooldown direction is asymmetric and fixed: ScaleInCooldown > ScaleOutCooldown (e.g., 300 out / 600 in).",
        "Scalable-dimension MUST match endpoint type: sagemaker:variant:DesiredInstanceCount for variants; sagemaker:inference-component:DesiredCopyCount for IC.",
        "Blue/green doubles capacity for the bake — fleet of 10 p4d at $33/hr = +$330/hr. Use Rolling Updates (IC-only) when cost-sensitive.",
        "AutoRollback reacts only to CloudWatch alarms you wired — it can’t catch silent quality regressions; pair with Model Monitor.",
    ]),
    ("Inference Recommender, Neo, edge", "Ch 41", [
        "Compute Optimizer does NOT cover SageMaker — use Inference Recommender for endpoints. Top-frequency exam trap.",
        "SageMaker Neo compiles per target — a model compiled for ml_c5 will NOT run on ml_g4dn or jetson_nano. Not portable.",
        "Edge Manager is DEPRECATED — use Greengrass v2 for edge ML on the 2026 exam. Highest-frequency edge ML trap.",
        "Triton is NOT the default LLM serving answer in 2025–26 — LMI / vLLM containers have displaced it for transformer inference.",
        "Two Recommender modes: Default (built-in candidate set, fastest) vs Advanced (custom load profile, traffic patterns). Pick by realism vs speed.",
        "Right-sizing is where ~50% of inference savings come from — BEFORE quantization, compilation, or architectural changes.",
    ]),
    ("Inference outside SageMaker — Lambda, ECS, EKS", "Ch 42", [
        "Lambda has NO GPU and a 10 GB container image limit — LLM / diffusion / GPU-CV / sub-50ms transformer = Lambda is wrong.",
        "SnapStart since Nov 2024 supports Java, Python 3.12+, .NET 8 only — modern cold-start fix for Python ML Lambda.",
        "SageMaker Operator for Kubernetes is ACK-based now — the legacy HostingDeployment CRD operator is deprecated. Pick ACK on the exam.",
        "HyperPod Inference Operator went GA as a managed EKS add-on April 2026 — amazon-sagemaker-hyperpod-inference, JumpStartModel CRD.",
        "Break-even for leaving SageMaker is roughly $30K–$50K/mo inference spend — below that, the ops cost of EKS exceeds the SageMaker premium.",
        "ECS Fargate has NO GPU — “serverless GPU inference” is never Fargate. SageMaker async/real-time on GPU or EKS GPU pods only.",
    ]),
]

PART_H = [
    ("SageMaker Pipelines — steps, params, conditions", "Ch 43", [
        "PipelineSession is mandatory when constructing Estimator/Processor that feeds into TrainingStep/ProcessingStep — default Session causes double-runs.",
        "AutoMLStep is ENSEMBLING-only inside pipelines — mode=HYPERPARAMETER_TUNING is rejected when used inside a pipeline.",
        "ModelStep is the modern replacement for CreateModelStep + RegisterModel — prefer it over the legacy classes since SDK 2.90.",
        "ConditionStep cannot nest — collapse multiple checks into one ConditionStep with conditions=[...], or chain two ConditionSteps at top level.",
        "Lineage is auto-enabled on every SageMaker Pipelines run — “end-to-end lineage with no custom code” → SageMaker Pipelines, not Step Functions or MWAA.",
        "LocalPipelineSession runs the whole pipeline inside local Docker containers — use for sanity-check before upsert to the real service.",
    ]),
    ("Step Functions vs Pipelines vs MWAA", "Ch 44", [
        "Distributed Map is Standard-only — Express workflows cannot host it. “Process 10K S3 objects in parallel” + Express = wrong.",
        "Express cannot use .sync — 5-min max duration and in-memory state make long-poll integrations physically impossible.",
        "CreateEndpoint does NOT support .sync — use Lambda polling DescribeEndpoint, or .waitForTaskToken + EventBridge endpoint-state event.",
        "MWAA charges 24/7 hourly even when idle — a mw1.small runs ~$350/mo with zero DAGs. “Minimize cost for once-per-week DAG” → not MWAA.",
        "Decision tree: ML-only → SageMaker Pipelines (lineage free). Cross-service → Step Functions Standard. Existing Airflow shop → MWAA.",
        "CreateTransformJob doesn’t auto-generate IAM policy (unlike CreateTrainingJob.sync) — attach sagemaker:*Transform* + EventBridge inline.",
    ]),
    ("EventBridge — Rules, Scheduler, Pipes", "Ch 45", [
        "Default move for “trigger X when Y happens” is EventBridge — Lambda polling and CloudWatch Events rule are usually distractors.",
        "Rules are UTC-only; for DST-aware cron, use EventBridge Scheduler with ScheduleExpressionTimezone (e.g., America/New_York).",
        "Pipes filtering reduces invocation cost for high-volume Kinesis/DynamoDB → small-percentage target — cheaper than Lambda ESM with Lambda-level filter.",
        "Cross-account routing: local → central → local works (one hop). No transitive routing through multiple central buses or cross-region chains.",
        "S3-to-EventBridge is a per-bucket toggle — OFF by default. Rule firing nothing → enable EventBridge notifications in bucket Properties.",
        "Canonical drift→retrain loop: Model Monitor alarm → EventBridge rule → Lambda dispatcher → StartPipelineExecution with extracted context.",
    ]),
    ("CI/CD — CodePipeline, Build, Deploy, Artifact", "Ch 46", [
        "Two pipelines, not one: model-build (code+data → Approved model package) and model-deploy (Approved → live endpoint with guardrails).",
        "CodePipeline V2 = per-action-minute billing ($0.002/min, 100 free). High-frequency long-build workloads may favour V1’s flat fee.",
        "CodeCommit was closed to new customers July 2024 — modern AWS-native git is CodeStar Connections to GitHub / GitLab / Bitbucket.",
        "CodeDeploy is for Lambda / ECS / EC2 — NOT SageMaker endpoints. SageMaker has native BlueGreenUpdatePolicy / RollingUpdatePolicy in UpdateEndpoint.",
        "CodeArtifact upstream chain caps at 10 + one external connection — deeper promotion chains need flattening or multi-domain split.",
        "GitHub OIDC: lock token.actions.githubusercontent.com:sub to repo+branch (StringLike), not wildcards — #1 OIDC misconfiguration on AWS Security blog.",
    ]),
    ("Infrastructure as code — CFN, CDK, Projects", "Ch 47", [
        "Change set = dry-run preview of YOUR next update. Drift detection = scan current live state vs last deployed template. Don’t conflate them.",
        "CloudFormation stack hard limit: 500 resources. “MaximumNumberOfResources” error → nested stacks or CDK Stages, not bigger templates.",
        "CDK Pipelines is self-mutating — “pipeline updates itself when its definition changes” points to CDK Pipelines, not raw CodePipeline.",
        "SageMaker Projects = CloudFormation + CodePipeline + SageMaker Pipelines — scaffolding around Pipelines, NOT a replacement for them.",
        "Pipelines are standalone entities per AWS docs — you can create/update/run pipelines from a notebook without a SageMaker Project.",
        "Use CloudFormation Hooks/Guard for policy-as-code on templates; Registry+Modules for sharing reusable resource patterns.",
    ]),
]

PART_I = [
    ("SageMaker Model Monitor — the four monitors", "Ch 48", [
        "Model Quality is the only monitor that requires ground-truth labels. “Labels arrive 90 days late” → use Data Quality, Bias Drift, or Feature Attribution Drift.",
        "EventBridge → Pipeline direct invoke with CloudWatch alarm payload is INCOMPLETE — you need a Lambda dispatcher to extract context and call StartPipelineExecution.",
        "Data Quality WILL NOT catch concept drift — inputs unchanged + accuracy dropped = Model Quality, not Data Quality.",
        "EEOC 4/5ths rule sets DI band at [0.80, 1.25] — codified in NYC Local Law 144 for automated hiring tools.",
        "Feature Attribution Drift is a LEADING indicator of concept drift — fires before Model Quality when labels are delayed. Pair with Data Quality.",
        "Six-step workflow: baseline → schedule → capture → process → compare → alarm. Same skeleton across all four monitor types.",
    ]),
    ("Drift fundamentals — covariate, label, concept", "Ch 49", [
        "“Detect feature distribution changes WITHOUT ground truth” = Data Quality monitor → covariate shift. Model Quality is a distractor here.",
        "Model Quality requires ground truth — if labels are unavailable or 30+ days late, Model Quality cannot help.",
        "PSI thresholds: 0.10 / 0.25 / 0.50 — small / significant / major. Industry-standard “declare drift” is 0.25 (credit-risk / fraud default).",
        "PSI binning: 10 equally populated deciles for continuous; categories for categorical. Zero-baseline bins need Laplace smoothing or exclusion.",
        "KS is the non-parametric two-sample default for CONTINUOUS features; Chi-squared is the analogue for CATEGORICAL.",
        "Three flavours: covariate shift P(X) changes, label shift P(Y) changes, concept drift P(Y|X) changes — only the last needs labels to detect.",
    ]),
    ("CloudWatch, X-Ray, CloudTrail for ML", "Ch 50", [
        "There is NO TrainingJobStatus CloudWatch metric — SageMaker emits state changes via EventBridge as “SageMaker Training Job State Change” events.",
        "Legacy aws-xray-sdk + X-Ray daemon entered maintenance Feb 2026; EOS Feb 2027. New work uses ADOT (OpenTelemetry + X-Ray exporter).",
        "sagemaker:InvokeEndpoint is a CloudTrail DATA event, off by default — HIPAA / model-risk audit → explicitly enable, budget for ~$0.10/100K invokes.",
        "CloudTrail Lake closes to new customers May 2026 — greenfield ML audit-log answer is one of the migration paths, not Lake.",
        "Endpoint metrics auto-published: Invocations, ModelLatency, OverheadLatency, Invocation4XXErrors, Invocation5XXErrors. CPU/GPU/Memory under /aws/sagemaker/Endpoints.",
        "CloudWatch Logs ML log groups must be CMK-encrypted in regulated workloads — default service key leaves invocation prompts unprotected.",
    ]),
    ("Registry, Model Cards, Lineage", "Ch 51", [
        "ModelApprovalStatus transitions emit “SageMaker Model Package State Change” events — the seam between human approval and automated deploy.",
        "Nov 2024 staging construct is ADDITIVE to legacy ModelApprovalStatus, not breaking — “rewrite everything” is the wrong answer.",
        "Staging construct is NOT enforced by the service — anyone with sagemaker:UpdateModelPackage can skip stages. Enforce via SCP / IAM / EventBridge.",
        "Model Card link to Model Package is at the version level and tamper-evident — you cannot rewrite the card a package was approved against.",
        "Lineage Tracking is AUTO-ENABLED on every TrainingJob, ProcessingJob, TransformJob, ModelPackage, Endpoint — no opt-in, no flag.",
        "Three-level hierarchy: Model Package Group → Model Package → Model Version. Use RAM for hub-and-spoke cross-account registry sharing.",
    ]),
    ("A/B testing & shadow variants in production", "Ch 52", [
        "InitialVariantWeight=0.1 is NOT zero customer impact — routes ~9% of traffic. “Zero impact validation” → always shadow variant.",
        "Shadow ≠ A/B: shadow never returns to the client. “Measure user-side outcome” → production variants. “Zero customer impact” → shadow.",
        "Peeking inflates Type I error to ~25% — daily p-value checks with stop-at-0.05 is a ~25% false-positive test, not 5%. Use sequential / always-valid p-values.",
        "SUTVA violation invalidates A/B — marketplaces, social feeds, shared inventory need cluster-randomisation or switchback designs, not 50/50 user split.",
        "Sample size formula: n ≈ 16·σ²/MDE² — memorise. Power 0.8 + alpha 0.05 + two-sided test — these are the implicit constants.",
        "Production variants for revenue/conversion experiments; shadow variants for latency/error/output-distribution validation. Two primitives, complementary.",
    ]),
]

PART_J = [
    ("The least-privilege ML execution role", "Ch 53", [
        "AccessDenied + iam:PassRole error → fix is on the CALLER’s role: explicit iam:PassRole scoped to target ARN + iam:PassedToService=sagemaker.amazonaws.com.",
        "Role-naming substring trap: “MLEngineeringTrainingRole” (no “SageMaker”) + AmazonSageMakerFullAccess → PassRole denied. Fix = customer-managed policy, not rename.",
        "Don’t grant sagemaker:* on the execution role — grant the specific action with tag-scoped condition, or orchestrate via Pipelines.",
        "Never tag-scope iam:PassRole (TOCTOU race) — AWS docs explicitly warn. Use ARN patterns like arn:aws:iam::*:role/ml/exec/*.",
        "Boundary intersection: identity ∩ boundary = effective. Either denying = deny. Fix is whichever side of the intersection makes sense for least privilege.",
        "Two-role pattern: developer caller role (sees console, calls APIs) vs SageMaker execution role (used BY SageMaker to read S3 / write outputs). Don’t mix.",
    ]),
    ("Network isolation for ML", "Ch 54", [
        "Studio VpcOnly + pip install 403 today (worked yesterday) → 12-hour CodeArtifact token TTL expired. Fix: aws codeartifact login or lifecycle-config cron.",
        "FIPS endpoint + endpoint policy: doesn’t work — FIPS runtime endpoints don’t honour endpoint policies. Use identity-based (SCP + boundary + role) instead.",
        "On-prem reading S3 over Direct Connect = INTERFACE endpoint for S3 (the gateway endpoint isn’t reachable from outside the VPC).",
        "Corollary trap: NEVER replace the in-VPC gateway endpoint with the interface endpoint to “simplify” — interface is $0.01/GB, gateway is free.",
        "Minimum endpoint set for VpcOnly Studio: SageMaker API, runtime, Studio, S3 (gateway), KMS, ECR, STS, Logs, plus the workload-specific ones.",
        "EnableNetworkIsolation + VpcConfig together = no internet egress AND no IAM creds in container. Pick BOTH for regulated training/inference.",
    ]),
    ("Encryption end-to-end — KMS across the lifecycle", "Ch 55", [
        "KmsKeyId parameter lives on every SageMaker output surface: training OutputDataConfig, EBS Volume, EFS/FSx, Feature Group online/offline, endpoint config.",
        "Bucket Keys reduce SSE-KMS API costs ~99% — always the answer over “switch to SSE-S3” (kills audit), aws/s3 (no cross-account), or quota increase (treats symptom).",
        "VolumeKmsKeyId is silently IGNORED on Nitro instance-store-heavy families (some ml.p4d, ml.trn1, ml.g5) — NVMe uses ephemeral encryption, not EBS.",
        "Multi-Region Keys do NOT eliminate S3 Cross-Region Replication re-encryption — AWS docs treat MRKs as single-region for service-integrated CRR.",
        "KMS pending-deletion window is 7–30 days (default 30). For instant lockout, call DisableKey first; deletion completes the cycle.",
        "EnableInterContainerTrafficEncryption=True encrypts distributed-training traffic between containers in the same job — mandatory for FedRAMP/HIPAA workloads.",
    ]),
    ("Compliance — PII, PHI, GDPR, HIPAA", "Ch 56", [
        "Macie is S3-ONLY — PII outside S3 (Redshift, DynamoDB, EFS, OpenSearch) is NEVER Macie.",
        "Guardrails sensitive-info filter does NOT redact CloudWatch Logs invocation logs — use CloudWatch Logs data protection (separate feature) for log-time masking.",
        "Iceberg snapshot trap: GDPR delete + 5-day default snapshot retention — yesterday’s snapshot still has the row. Run expire_snapshots + remove_orphan_files.",
        "Ground Truth Plus is NOT HIPAA-eligible (managed workforce sits outside BAA). PHI labeling → GT self-service + private workforce in VPC.",
        "PHI encryption: SSE-S3 is WRONG (no key-use audit). SSE-KMS with customer-managed CMK + CloudTrail kms:Decrypt + restrictive key policy is the answer.",
        "Bedrock Global CRIS may route prompts to ANY commercial region — GDPR/BDSG/PHI workloads must use Geographic CRIS, not Global.",
    ]),
    ("Cost optimization — Spot, SP, right-sizing, silicon", "Ch 57", [
        "Spot is NOT supported for real-time endpoints, serverless inference, async endpoints, or Studio apps — only training and Batch Transform.",
        "Managed Spot is incompatible with Warm Pools — EnableManagedSpotTraining=True + KeepAlivePeriodInSeconds>0 = ValidationException.",
        "Compute SP does NOT cover SageMaker — SageMaker SP is the only SP that does. Mixed estate = both SPs, one cannot cover both.",
        "SageMaker SP does NOT stack with Managed Spot — Spot already discounts; SP applies only to on-demand billing.",
        "NO Reserved Instances for SageMaker — “buy an RI for the endpoint” is wrong by construction. SageMaker SP is the only committed-use discount.",
        "Compute Optimizer does NOT cover SageMaker — use Inference Recommender (endpoints) and CloudWatch metrics (training); Compute Optimizer covers EC2/Lambda/RDS/EBS.",
    ]),
    ("Cost observability — Cost Explorer, Budgets, anomaly", "Ch 58", [
        "Budget Actions do NOT natively stop SageMaker training jobs or endpoints — Budget → SNS → Lambda → StopTrainingJob / DeleteEndpoint is the correct path.",
        "Budgets refreshes up to 3x/day — Budget Actions inherit several-hour lag. “Real-time stop on threshold” → EventBridge + CloudWatch alarms, not Budgets.",
        "Cost Anomaly Detection is ML-based; Budgets is static-threshold — “alert me when SageMaker spend spikes unexpectedly” = CAD; “exceeds $5K/mo” = Budgets.",
        "Cost allocation tags must be ACTIVATED and activation is not retroactive — un-activated months are forever unallocated.",
        "Compute Optimizer does NOT cover SageMaker — the single most-tested cost-tool trap. Inference Recommender (endpoints) + CloudWatch (training) + JL idle-shutdown LCC (notebooks).",
        "Weekend HPO defense: Budget at 80% → SNS → Lambda lists running training jobs, filters by tag, calls StopTrainingJob on the runaways.",
    ]),
]

PART_K = [
    ("The “which AI service?” decision tree", "Ch 59", [
        "Amazon Forecast is CLOSED to new customers — demand forecasting in 2026 = SageMaker DeepAR (built-in) or SageMaker Canvas (no-code).",
        "All three Lookout services (Equipment, Metrics, Vision) were DISCONTINUED Oct 10, 2025 — never the right answer on a 2026 exam, even if listed.",
        "Three services that LOOK HIPAA-friendly but are NOT eligible: Ground Truth Plus, Fraud Detector, all Lookouts. Mechanical Turk is never PHI-eligible.",
        "Rekognition Custom Labels (vision) ≠ Comprehend Custom (text) — modality from the noun, task type (classify / extract) from the verb.",
        "Verb + noun + qualifier triple: sentiment / entities / PII → Comprehend; OCR → Textract; recs → Personalize; fraud → Fraud Detector; vision → Rekognition; voice → Polly / Transcribe; translation → Translate.",
        "Canonical chains the exam loves: Transcribe → Comprehend → Bedrock (voice analytics); Textract → Comprehend → A2I (doc processing with human review).",
    ]),
    ("Amazon Bedrock — the FM platform", "Ch 60", [
        "Four Bedrock pillars: Model Gateway (Converse, on-demand), Lifecycle (fine-tune, distill, RFT, App Inference Profiles), Agents+KB, Safety (Guardrails).",
        "RFT launched on Nova 2 Lite at re:Invent 2025 — “reward function / optimise for math+code accuracy” → RFT on Nova 2 Lite, not SFT.",
        "Standalone ApplyGuardrail polices outputs of NON-Bedrock models (self-hosted Llama, external API) — don’t reach for Converse + guardrailConfig.",
        "Any model produced INSIDE Bedrock (SFT, CPT, distillation, RFT) is servable only via Provisioned Throughput — ~$15K/mo floor for one MU.",
        "Global CRIS may route to ANY region worldwide — GDPR/BDSG/Australian APP/PHI → Geographic CRIS only, never Global. Use SCP to deny aws:RequestedRegion=unspecified.",
        "Multi-agent collaboration (“returns / shipping / account” sub-agents under a supervisor) beats one bloated agent past ~20 tools — tool-choice accuracy collapses otherwise.",
    ]),
    ("GenAI patterns on AWS — RAG, fine-tune, agents", "Ch 61", [
        "Customization cost order: prompt engineering → RAG → fine-tune (SFT/LoRA) → distillation → CPT → RFT — start cheap, escalate on signal.",
        "“Citations / sources / freshness” → RAG. “Unlabeled / large corpus / vocabulary gap” → CPT. Both apply → production = CPT-then-RAG; single-answer exam = RAG.",
        "S3 Vectors is the cheapest vector store for infrequent / very-large corpora; Redis Enterprise for sub-ms; Aurora pgvector for SQL+ACID; Neptune Analytics for GraphRAG.",
        "Bedrock Knowledge Bases is the DEFAULT managed RAG answer — custom OpenSearch + Lambda + Step Functions only when KB lacks a needed feature.",
        "Hybrid search (BM25 + vector with RRF fusion) gives +5–15% NDCG on exact-code/SKU stems — reranking (cross-encoder) adds another +5–10%.",
        "AgentCore = production runtime for non-trivial agents (8-hour sessions, BYO framework, MCP/A2A). Bedrock Agents = fast prototype, 15-min cap.",
    ]),
    ("Bedrock vs JumpStart — when each wins", "Ch 62", [
        "Bedrock = managed token-priced API. JumpStart = SageMaker endpoint billed by instance-hour. Two completely different cost shapes for the same model family.",
        "Bedrock customization (SFT/CPT/distill/RFT) is narrow; JumpStart is open-ended. “Sensible defaults, no MLOps team” → Bedrock; “DeepSpeed Zero-3 on 16 GPUs” → JumpStart.",
        "Bedrock PT has ~$15K/month floor (one Llama MU × 730 hr × ~$21/hr) — buying PT for unproven low-volume workload is a top exam anti-pattern.",
        "JumpStart real-time endpoint bills 24×7 even when idle — idle-shutdown LCC exists for notebooks, NOT for real-time endpoints.",
        "Hybrid is the 2026 default for serious production: Bedrock for generation (Claude-quality), JumpStart for cheap high-volume small models (rerank, embed, PII).",
        "Six decision axes the exam buries: control of GPU, model in Bedrock catalog, customization depth, sustained throughput, latency floor, data residency.",
    ]),
    ("Capstone — fraud-detection pipeline end-to-end", "Ch 63", [
        "Architecture: Kinesis → Lambda/Flink → Feature Store dual-write → SageMaker XGBoost + AMT Hyperband + Spot → real-time endpoint behind API Gateway → Model Monitor.",
        "Feature Store dual-write (OnlineStoreConfig + OfflineStoreConfig + TargetStores=[both]) is the byte-identical contract that kills training-serving skew.",
        "Spot training needs atomic checkpointing + MaxWaitTime > MaxRuntime — non-atomic writes silently produce broken models on Spot resume.",
        "Hyperband REQUIRES EarlyStoppingType=Off — setting it to Auto makes the two stopping mechanisms race; trials terminate prematurely and nondeterministically.",
        "Auto-rollback should be wired to a CloudWatch CUSTOM metric on a BUSINESS KPI (approval rate, fraud capture) — not CPU/latency, which miss silent model regressions.",
        "Iceberg snapshot retention can violate GDPR erasure — set retention to ≤30 days OR run expire_snapshots + remove_orphan_files on every erasure request.",
    ]),
    ("Exam-day strategy + self-assessment", "Ch 64", [
        "Passing score is 720 (NOT 700) on the 100–1000 scale — every cohort has candidates who get 712 and walk out thinking they passed.",
        "The SageMaker Trap: operationalisation knowledge beats model-training depth on MLA-C01 (vs the older MLS-C01). Rebalance away from hyperparameter math.",
        "MRQ scoring is ALL-OR-NOTHING — two right + one wrong on a Select-THREE = ZERO credit. Count your highlighted options before clicking Next.",
        "There are NO scheduled breaks — the clock runs continuously. Plan hydration and bathroom timing accordingly.",
        "OnVUE: closed eyes is the only legitimate thinking pose. Eye movement off-screen, second people, second devices all flag. First-sit candidates should prefer Pearson VUE in-centre.",
        "Pace = ~1m 56s per scored question; fatigue hits ~Q60. Plan a 10-second mental reset at minute 100. Flag liberally on Pass 1; never leave a blank.",
    ]),
]


# Final capstone closing slide
def closing_slide():
    s = add_slide()
    slide_title(s, "What’s next — the AWS cert ladder")
    slide_subtitle(s, "You built the textbook. Now sit the exam.")
    # 3 next-cert tiles
    tiles = [
        ("AWS ML Specialty",
         "MLS-C01 retiring; legacy material still useful for theory depth. "
         "Strong companion to MLA-C01 — same model-math vocabulary, "
         "different operational lens. Optional, not strategic.",
         BLUE),
        ("Solutions Architect Pro",
         "SAP-C02. The architecture-breadth credential. Tests the same "
         "multi-account / networking / cost discipline you exercised in "
         "Part J, but across the whole AWS surface. Highest-ROI follow-up.",
         GREEN),
        ("Security Specialty",
         "SCS-C02. Deepens Domain 4 (IAM, KMS, VPC, CloudTrail) to a "
         "regulated-industry bar. Pair with MLA-C01 for FS / health / gov "
         "ML platform roles.",
         PURPLE),
    ]
    x = Inches(0.5); y = Inches(1.7); w = Inches(4.1); h = Inches(4.3)
    for name, body, c in tiles:
        rrect(s, x, y, w, h, fill=PANEL, line=c)
        rect(s, x, y, w, Inches(0.55), fill=c)
        textbox(s, x, y, w, Inches(0.55), name, size=17, bold=True,
                color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        textbox(s, x + Inches(0.25), y + Inches(0.75),
                w - Inches(0.5), h - Inches(0.9), body, size=13, color=LIGHT)
        x += w + Inches(0.2)
    # closing line
    rrect(s, Inches(0.5), Inches(6.15), Inches(12.33), Inches(0.7),
          fill=ACCENT)
    textbox(s, Inches(0.5), Inches(6.15), Inches(12.33), Inches(0.7),
            "Sixty-four chapters bought you the knowledge. Now 130 minutes prove you read the book.",
            size=15, bold=True, color=WHITE,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    footer(s, "Finis")


# =======================================================================
# DECK ASSEMBLY
# =======================================================================

def build():
    # Front matter
    front_title()
    front_audience()
    front_contents()
    front_exam_mechanics()
    front_domains()

    parts = [
        ("A", "Landscape",                "Chapters 1–4",   PART_A),
        ("B", "AWS foundations",          "Chapters 5–9",   PART_B),
        ("C", "Data ingestion & storage", "Chapters 10–15", PART_C),
        ("D", "Data prep & features",     "Chapters 16–21", PART_D),
        ("E", "Model development",        "Chapters 22–30", PART_E),
        ("F", "HPO & distributed training","Chapters 31–34", PART_F),
        ("G", "Deployment & inference",   "Chapters 35–42", PART_G),
        ("H", "Orchestration & CI/CD",    "Chapters 43–47", PART_H),
        ("I", "Monitoring & governance",  "Chapters 48–52", PART_I),
        ("J", "Security & cost",          "Chapters 53–58", PART_J),
        ("K", "AI services, GenAI & capstone", "Chapters 59–64", PART_K),
    ]
    for letter, theme, range_, chapters in parts:
        section_divider(letter, theme, range_)
        for title, ref, bullets in chapters:
            chapter_slide(title, ref, bullets)

    closing_slide()

    out = ("/Users/vr/Code/Career_upskill/topics/"
           "14_aws_ml_engineer_associate/pptx/"
           "AWS_MLA_C01_Practice_Guide.pptx")
    prs.save(out)
    print(f"Saved: {out}")
    print(f"Slides: {len(prs.slides)}")


if __name__ == "__main__":
    build()
