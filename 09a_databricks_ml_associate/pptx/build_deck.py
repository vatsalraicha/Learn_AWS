"""
Databricks ML Associate — Mastery Track study deck builder.

Teaching companion to the textbook at topics/09a_databricks_ml_associate/.
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree

# ---------- color palette ----------
BG       = RGBColor(0x12, 0x18, 0x26)   # dark navy
PANEL    = RGBColor(0x1B, 0x23, 0x36)
ACCENT   = RGBColor(0xFF, 0x3E, 0x00)   # databricks orange
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
    """runs = list of paragraphs, each = list of (text, dict_of_props)."""
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
    c = slide.shapes.add_connector(2, x1, y1, x2, y2)  # straight
    c.line.color.rgb = color
    c.line.width = Pt(weight)
    # add arrowhead
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
    # accent rule
    rect(slide, Inches(0.5), Inches(0.45), Inches(0.12), Inches(0.55),
         fill=ACCENT)
    textbox(slide, Inches(0.75), Inches(0.4), Inches(12), Inches(0.7),
            title, size=30, bold=True, color=color)

def slide_subtitle(slide, sub):
    textbox(slide, Inches(0.75), Inches(1.05), Inches(12), Inches(0.4),
            sub, size=15, color=MUTED, bold=False)

def footer(slide, ref):
    textbox(slide, Inches(0.5), Inches(7.1), Inches(8), Inches(0.3),
            "Databricks ML Associate · Mastery Track", size=10, color=GREY)
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
    # header
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
    # body
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
    # overlay accent rectangle
    rect(s, 0, 0, SW, SH, fill=ACCENT)
    # small dark stripe at the bottom
    rect(s, 0, Inches(6.6), SW, Inches(0.9), fill=BG)
    textbox(s, Inches(0.75), Inches(2.2), Inches(12), Inches(0.7),
            f"Part {letter}", size=44, bold=True, color=WHITE)
    textbox(s, Inches(0.75), Inches(3.1), Inches(12), Inches(1.2),
            theme, size=54, bold=True, color=WHITE)
    textbox(s, Inches(0.75), Inches(4.4), Inches(12), Inches(0.5),
            chapters, size=20, color=WHITE)
    textbox(s, Inches(0.75), Inches(6.75), Inches(12), Inches(0.5),
            "Databricks ML Associate · Mastery Track",
            size=12, color=MUTED)
    return s


# =======================================================================
# FRONT MATTER
# =======================================================================

def front_title():
    s = add_slide()
    # left orange stripe
    rect(s, 0, 0, Inches(0.6), SH, fill=ACCENT)
    textbox(s, Inches(1.0), Inches(1.6), Inches(11), Inches(0.6),
            "Databricks ML Associate", size=28, color=ACCENT, bold=True)
    textbox(s, Inches(1.0), Inches(2.2), Inches(11), Inches(1.6),
            "Mastery Track", size=72, color=WHITE, bold=True)
    # accent rule
    rect(s, Inches(1.0), Inches(3.85), Inches(2.5), Inches(0.06), fill=ACCENT)
    textbox(s, Inches(1.0), Inches(4.05), Inches(11), Inches(0.6),
            "A visual companion to the textbook",
            size=24, color=LIGHT)
    textbox(s, Inches(1.0), Inches(4.85), Inches(11), Inches(0.5),
            "Diagrams · derivations · comparison tables · worked examples",
            size=16, color=MUTED)
    textbox(s, Inches(1.0), Inches(6.75), Inches(11), Inches(0.4),
            "Career upskill · Topic 09a", size=11, color=GREY)


def front_audience():
    s = add_slide()
    slide_title(s, "Who this deck is for · How to use it")
    # two panels
    rrect(s, Inches(0.75), Inches(1.6), Inches(5.9), Inches(4.8),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(1.0), Inches(1.8), Inches(5.4), Inches(0.5),
            "AUDIENCE", size=14, color=ACCENT, bold=True)
    textbox(s, Inches(1.0), Inches(2.3), Inches(5.4), Inches(4),
            ("• Strong Python; PySpark and ML are taught from zero in the "
             "textbook.\n\n"
             "• You're sitting the Databricks ML Associate exam, but more "
             "importantly you want to be genuinely good at the job.\n\n"
             "• You'd rather understand the math than memorize an answer key."),
            size=15, color=LIGHT)
    rrect(s, Inches(6.85), Inches(1.6), Inches(5.9), Inches(4.8),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(7.1), Inches(1.8), Inches(5.4), Inches(0.5),
            "HOW TO USE", size=14, color=ACCENT, bold=True)
    textbox(s, Inches(7.1), Inches(2.3), Inches(5.4), Inches(4),
            ("• Each content slide is a self-contained concept lens — read "
             "it on a flight, in a 1:1, or as a refresher.\n\n"
             "• Footer references the chapter(s) where the depth lives. "
             "Always go to the book for derivations.\n\n"
             "• Slides are diagrams first, prose second. If a slide is just "
             "bullets, it's a comparison table — and that's the point."),
            size=15, color=LIGHT)
    footer(s, "Preface")


def front_contents():
    s = add_slide()
    slide_title(s, "Contents")
    slide_subtitle(s, "Thirteen parts · 76 textbook chapters")
    headers = ["", "Part", "Theme", "Chapters"]
    rows = [
        ["A", "Why ML exists",                       "Framing the problem",                   "1 – 4"],
        ["B", "Probability & statistics primer",     "RVs, distributions, Bayes, CLT, tests", "5 – 10"],
        ["C", "Linear algebra & calculus",           "Vectors, matrices, eigen, gradients",   "11 – 15"],
        ["D", "The fundamental ML problem",          "Loss, GD, bias-variance, CV",           "16 – 22"],
        ["E", "Feature engineering",                 "EDA → encoding → selection",            "23 – 30"],
        ["F", "Supervised algorithms",               "Linear → trees → boosting",             "31 – 37"],
        ["G", "Unsupervised algorithms",             "K-means, hierarchical, PCA, UMAP",      "38 – 41"],
        ["H", "Model evaluation theory",             "Confusion, ROC, regression metrics",    "42 – 47"],
        ["I", "Hyperparameter optimization",         "Grid, random, Bayesian, Hyperopt",      "48 – 54"],
        ["J", "Spark from zero",                     "Architecture, Catalyst, shuffle, AQE",  "55 – 61"],
        ["K", "pyspark.ml in depth",                 "Pipelines, CV, persistence",            "62 – 67"],
        ["L", "Databricks platform & MLflow",        "UC, Feature Store, MLflow, AutoML",     "68 – 74"],
        ["M", "Capstone & exam strategy",            "Lending Club end-to-end",               "75 – 76"],
    ]
    # use 4-col table — first col is just the letter
    headers2 = ["#", "Theme", "What it covers", "Chs"]
    rows2 = [[r[0], r[1], r[2], r[3]] for r in rows]
    add_table(s, Inches(0.75), Inches(1.6), Inches(11.83), Inches(5.3),
              headers2, rows2, col_widths=[1, 4, 7, 2], font_size=12,
              header_size=13)
    footer(s, "Contents")


# =======================================================================
# PART A — WHY ML EXISTS
# =======================================================================

def partA_function_approximation():
    s = add_slide()
    slide_title(s, "ML as function approximation")
    slide_subtitle(s, "Learn an unknown f: X → Y from a sample of (x, y) pairs")
    # input cloud
    ellipse(s, Inches(0.9), Inches(2.5), Inches(2.6), Inches(2.6),
            fill=PANEL, line=BLUE)
    textbox(s, Inches(0.9), Inches(2.5), Inches(2.6), Inches(2.6),
            "INPUT  X\n\nemail text\npixels\nuser features",
            size=14, color=LIGHT, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    # output cloud
    ellipse(s, Inches(9.85), Inches(2.5), Inches(2.6), Inches(2.6),
            fill=PANEL, line=GREEN)
    textbox(s, Inches(9.85), Inches(2.5), Inches(2.6), Inches(2.6),
            "OUTPUT  Y\n\nspam / not\ndigit class\nrevenue",
            size=14, color=LIGHT, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    # f arrow
    rrect(s, Inches(4.2), Inches(3.3), Inches(4.9), Inches(1.0),
          fill=ACCENT)
    textbox(s, Inches(4.2), Inches(3.3), Inches(4.9), Inches(1.0),
            "f̂  ≈  f", size=32, color=WHITE, bold=True,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    arrow(s, Inches(3.5), Inches(3.8), Inches(4.2), Inches(3.8))
    arrow(s, Inches(9.1), Inches(3.8), Inches(9.85), Inches(3.8))
    # bottom note
    textbox(s, Inches(0.75), Inches(5.6), Inches(11.83), Inches(1.2),
            ("We have many (xᵢ, yᵢ).  We don't know f.  We pick a hypothesis "
             "class H and search for the h ∈ H that minimises loss on the "
             "data — gambling that low train loss generalises to new x."),
            size=15, color=MUTED, align=PP_ALIGN.CENTER)
    footer(s, "Ch 1")


def partA_three_paradigms():
    s = add_slide()
    slide_title(s, "The three paradigms")
    slide_subtitle(s, "What the learner is given dictates what it can learn")
    y0 = Inches(1.7); h = Inches(4.7); w = Inches(4.0); gap = Inches(0.2)
    cols = [
        ("SUPERVISED",  "Labeled (x, y) pairs",
         "Goal: predict y for new x.\n\nClassification: y ∈ {classes}\nRegression: y ∈ ℝ\n\nExamples:\n• spam / not\n• credit default risk\n• house price",
         BLUE),
        ("UNSUPERVISED", "Only x, no labels",
         "Goal: find structure.\n\nClustering, dim. reduction,\ndensity estimation\n\nExamples:\n• customer segments\n• PCA for compression\n• anomaly detection",
         PURPLE),
        ("REINFORCEMENT", "State + reward signal",
         "Goal: learn a policy π that\nmaximises expected reward.\n\nNot on the Associate exam,\nbut shapes how you read\nproduction ML systems.\n\nExamples:\n• AlphaGo\n• ad bidding\n• robotics",
         YELLOW),
    ]
    x = Inches(0.6)
    for title, sub, body, c in cols:
        rrect(s, x, y0, w, h, fill=PANEL, line=c)
        rect(s, x, y0, w, Inches(0.55), fill=c)
        textbox(s, x, y0, w, Inches(0.55), title, size=18, bold=True,
                color=BG if c == YELLOW else WHITE,
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        textbox(s, x + Inches(0.2), y0 + Inches(0.7), w - Inches(0.4),
                Inches(0.6), sub, size=14, color=ACCENT, bold=True)
        textbox(s, x + Inches(0.2), y0 + Inches(1.3), w - Inches(0.4),
                h - Inches(1.4), body, size=13, color=LIGHT)
        x += w + gap
    footer(s, "Ch 2")


def partA_spam_pipeline():
    s = add_slide()
    slide_title(s, "Spam detection end-to-end")
    slide_subtitle(s, "Every step appears in every supervised project")
    y = Inches(2.0); h = Inches(1.0); w = Inches(1.55)
    steps = [
        ("Raw\nemails", PANEL),
        ("Label", BLUE),
        ("Features\n(BoW, TF-IDF)", PANEL),
        ("Split\ntrain/test", PANEL),
        ("Train\nlogreg", ACCENT),
        ("Evaluate\nP / R / F1", GREEN),
        ("Deploy +\nmonitor", YELLOW),
    ]
    x = Inches(0.5)
    for label, c in steps:
        textcolor = BG if c == YELLOW else WHITE
        rrect(s, x, y, w, h, fill=c)
        textbox(s, x, y, w, h, label, size=12, bold=True, color=textcolor,
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        x += w + Inches(0.2)
    # arrows between
    x = Inches(0.5) + w
    for i in range(6):
        arrow(s, x + Inches(0.02), y + Inches(0.5),
              x + Inches(0.18), y + Inches(0.5))
        x += w + Inches(0.2)
    # threshold callout
    rrect(s, Inches(0.6), Inches(4.3), Inches(5.8), Inches(2.5),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(0.8), Inches(4.4), Inches(5.5), Inches(0.4),
            "THE THRESHOLD KNOB", size=13, color=ACCENT, bold=True)
    textbox(s, Inches(0.8), Inches(4.85), Inches(5.5), Inches(1.9),
            ("The model outputs P(spam | x). The threshold τ converts that "
             "score into a decision.\n\nMove τ up → fewer flagged emails, "
             "higher precision, lower recall.\n\nThe model didn't change. "
             "The operating point did."),
            size=13, color=LIGHT)
    # vocab callout
    rrect(s, Inches(6.7), Inches(4.3), Inches(6.0), Inches(2.5),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(6.9), Inches(4.4), Inches(5.7), Inches(0.4),
            "VOCABULARY YOU OWN NOW", size=13, color=ACCENT, bold=True)
    textbox(s, Inches(6.9), Inches(4.85), Inches(5.7), Inches(1.9),
            ("feature · label · training · inference · accuracy · "
             "precision · recall · F1 · threshold · overfitting · "
             "class imbalance · operating point"),
            size=13, color=LIGHT)
    footer(s, "Ch 3")


def partA_lifecycle():
    s = add_slide()
    slide_title(s, "The seven-stage ML lifecycle")
    slide_subtitle(s, "Every later chapter slots into one of these stages")
    stages = [
        ("1", "Problem\nframing",    "Loss, metric, success"),
        ("2", "Data\nacquisition",   "Source, schema, drift"),
        ("3", "EDA &\nfeature eng.", "Clean, encode, scale"),
        ("4", "Modeling",            "Algo + hparams + CV"),
        ("5", "Evaluation",          "Holdout, cohorts, fairness"),
        ("6", "Deployment",          "Batch · streaming · real-time"),
        ("7", "Monitoring",          "Drift, retrain triggers"),
    ]
    y = Inches(1.9); h = Inches(1.5); w = Inches(1.7)
    x = Inches(0.45)
    for n, t, sub in stages:
        rrect(s, x, y, w, h, fill=PANEL, line=ACCENT)
        ellipse(s, x + Inches(0.55), y + Inches(0.15), Inches(0.6),
                Inches(0.6), fill=ACCENT)
        textbox(s, x + Inches(0.55), y + Inches(0.15), Inches(0.6),
                Inches(0.6), n, size=16, bold=True, color=WHITE,
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        textbox(s, x, y + Inches(0.75), w, Inches(0.5), t, size=12,
                bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        textbox(s, x, y + Inches(1.15), w, Inches(0.35), sub, size=10,
                color=MUTED, align=PP_ALIGN.CENTER)
        x += w + Inches(0.1)
    # feedback loop
    arrow(s, Inches(12.3), Inches(2.65), Inches(12.6), Inches(2.65))
    line(s, Inches(12.6), Inches(2.65), Inches(12.6), Inches(5.3), color=ACCENT)
    line(s, Inches(12.6), Inches(5.3), Inches(0.65), Inches(5.3), color=ACCENT)
    line(s, Inches(0.65), Inches(5.3), Inches(0.65), Inches(3.4), color=ACCENT)
    arrow(s, Inches(0.65), Inches(3.4), Inches(1.15), Inches(3.4), color=ACCENT)
    textbox(s, Inches(0.75), Inches(5.4), Inches(12), Inches(0.4),
            "Monitoring drives retraining — the lifecycle is a loop, not a line.",
            size=13, color=ACCENT, bold=True, align=PP_ALIGN.CENTER)
    # under-text
    textbox(s, Inches(0.75), Inches(6.0), Inches(11.83), Inches(0.9),
            ("On Databricks: stages 2-3 → DLT / Spark; stage 4 → "
             "pyspark.ml + MLflow; stage 6 → Model Serving; stage 7 → "
             "Lakehouse Monitoring + scheduled jobs."),
            size=13, color=MUTED, align=PP_ALIGN.CENTER)
    footer(s, "Ch 4")


def partA_ml_vs_rules():
    s = add_slide()
    slide_title(s, "ML vs rule-based programming")
    slide_subtitle(s, "When you'd choose one over the other")
    headers = ["Aspect", "Rule-based", "Machine learning"]
    rows = [
        ["Input",            "Rules + data → output",                "Data + output → rules (learned)"],
        ["Maintainability",  "Rules grow without bound",             "Retrain when data shifts"],
        ["Edge cases",       "Need explicit rule per case",          "Generalises from examples"],
        ["Explainability",   "Trivially auditable",                  "Depends on model class"],
        ["Data hunger",      "Minimal",                              "Hungry — and quality > quantity"],
        ["When it wins",     "Stable, well-specified domains",       "Pattern-rich, noisy, evolving inputs"],
        ["Failure mode",     "Brittleness as rules pile up",         "Silent drift; concept change"],
    ]
    add_table(s, Inches(0.5), Inches(1.7), Inches(12.33), Inches(4.8),
              headers, rows, col_widths=[3, 6, 6], font_size=13,
              header_size=14)
    textbox(s, Inches(0.5), Inches(6.6), Inches(12.33), Inches(0.5),
            "Use ML when the rules are hidden inside the data — not when you can just write them.",
            size=14, color=ACCENT, bold=True, align=PP_ALIGN.CENTER)
    footer(s, "Ch 1")


def partA_data_split_preview():
    s = add_slide()
    slide_title(s, "What data is for — a preview of Part D")
    slide_subtitle(s, "Three roles, three different jobs")
    y = Inches(2.0); h = Inches(3.2)
    # train block
    rrect(s, Inches(0.6), y, Inches(6.0), h, fill=PANEL, line=BLUE)
    rect(s, Inches(0.6), y, Inches(6.0), Inches(0.55), fill=BLUE)
    textbox(s, Inches(0.6), y, Inches(6.0), Inches(0.55),
            "TRAIN  ~60-80%", size=18, bold=True, color=WHITE,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    textbox(s, Inches(0.8), y + Inches(0.75), Inches(5.6), Inches(2.4),
            ("Used to fit the model parameters.\n\n"
             "The optimiser SEES every example here.\n\n"
             "Loss on this set goes down as you train — by design.\n"
             "Don't trust it as a quality signal."),
            size=14, color=LIGHT)
    # val
    rrect(s, Inches(6.8), y, Inches(2.9), h, fill=PANEL, line=YELLOW)
    rect(s, Inches(6.8), y, Inches(2.9), Inches(0.55), fill=YELLOW)
    textbox(s, Inches(6.8), y, Inches(2.9), Inches(0.55),
            "VAL  ~10-20%", size=18, bold=True, color=BG,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    textbox(s, Inches(6.95), y + Inches(0.75), Inches(2.6), Inches(2.4),
            ("Pick hyperparameters.\n\nSelect models.\n\n"
             "Model SEES this indirectly.\n\nNo unbiased estimate "
             "of true performance lives here."),
            size=13, color=LIGHT)
    # test
    rrect(s, Inches(9.9), y, Inches(2.85), h, fill=PANEL, line=GREEN)
    rect(s, Inches(9.9), y, Inches(2.85), Inches(0.55), fill=GREEN)
    textbox(s, Inches(9.9), y, Inches(2.85), Inches(0.55),
            "TEST  ~10-20%", size=18, bold=True, color=WHITE,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    textbox(s, Inches(10.05), y + Inches(0.75), Inches(2.55), Inches(2.4),
            ("Touched ONCE, at the end.\n\n"
             "Unbiased estimate of generalisation.\n\n"
             "Touching twice = silently overfitting to it."),
            size=13, color=LIGHT)
    textbox(s, Inches(0.75), Inches(5.5), Inches(11.83), Inches(1.4),
            ("The deeper story (cross-validation, stratified splits, "
             "time-series CV, leakage) lives in Chapters 21–22. "
             "For now: holdouts are not interchangeable — each "
             "answers a different question."),
            size=14, color=MUTED, align=PP_ALIGN.CENTER)
    footer(s, "Ch 4 → Chs 21-22")



# =======================================================================
# PART B — PROBABILITY & STATISTICS
# =======================================================================

def partB_rv_pmf_pdf():
    s = add_slide()
    slide_title(s, "Random variables · PMF vs PDF")
    slide_subtitle(s, "Discrete spikes vs continuous densities — same idea, different math")
    # left: PMF
    rrect(s, Inches(0.5), Inches(1.7), Inches(6.0), Inches(5.0),
          fill=PANEL, line=BLUE)
    textbox(s, Inches(0.7), Inches(1.85), Inches(5.6), Inches(0.4),
            "DISCRETE   P(X = x)  —  the PMF", size=15, bold=True,
            color=BLUE)
    # axes
    ox, oy = Inches(0.9), Inches(5.7)
    arrow(s, ox, oy, ox, Inches(2.6), color=MUTED, weight=1.0)
    arrow(s, ox, oy, Inches(6.2), oy, color=MUTED, weight=1.0)
    textbox(s, Inches(6.0), oy + Inches(0.05), Inches(0.6), Inches(0.3),
            "x", size=11, color=MUTED)
    textbox(s, ox - Inches(0.3), Inches(2.5), Inches(0.6), Inches(0.3),
            "P", size=11, color=MUTED)
    heights = [0.6, 1.2, 1.8, 2.2, 1.5, 0.9, 0.4]
    bx = ox + Inches(0.3)
    for hh in heights:
        rect(s, bx, oy - Inches(hh), Inches(0.5), Inches(hh), fill=BLUE)
        bx += Inches(0.7)
    textbox(s, Inches(0.7), Inches(6.1), Inches(5.6), Inches(0.6),
            "Sum of bar heights = 1.   Example: dice, # spam emails, # clicks.",
            size=12, color=LIGHT)
    # right: PDF
    rrect(s, Inches(6.85), Inches(1.7), Inches(6.0), Inches(5.0),
          fill=PANEL, line=GREEN)
    textbox(s, Inches(7.05), Inches(1.85), Inches(5.6), Inches(0.4),
            "CONTINUOUS   f(x)  —  the PDF", size=15, bold=True,
            color=GREEN)
    ox2, oy2 = Inches(7.25), Inches(5.7)
    arrow(s, ox2, oy2, ox2, Inches(2.6), color=MUTED, weight=1.0)
    arrow(s, ox2, oy2, Inches(12.55), oy2, color=MUTED, weight=1.0)
    # bell curve approximation using freeform
    from pptx.util import Emu
    # draw freeform polygon as polyline
    pts = []
    import math
    for i in range(60):
        t = -3 + 6 * i / 59
        y = math.exp(-t * t / 2)
        px = ox2 + Inches(0.2 + (i / 59) * 5.0)
        py = oy2 - Inches(y * 2.6)
        pts.append((px, py))
    # connect dots with lines (already imported `line`)
    for i in range(len(pts) - 1):
        line(s, pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
             color=GREEN, weight=2.5)
    textbox(s, Inches(7.05), Inches(6.1), Inches(5.6), Inches(0.6),
            "Area under curve = 1.   P(a ≤ X ≤ b) = ∫ₐᵇ f(x) dx.   "
            "Height ≠ probability.", size=12, color=LIGHT)
    footer(s, "Ch 5")


def partB_distributions():
    s = add_slide()
    slide_title(s, "Four distributions you must own")
    slide_subtitle(s, "PMF/PDF · mean · variance · when it shows up")
    headers = ["Distribution", "PMF / PDF", "E[X]", "Var[X]", "Where you meet it"]
    rows = [
        ["Bernoulli(p)",
         "P(1)=p, P(0)=1-p",
         "p", "p(1-p)",
         "One coin flip; one binary label"],
        ["Binomial(n, p)",
         "C(n,k) pᵏ (1-p)ⁿ⁻ᵏ",
         "np", "np(1-p)",
         "# clicks in n impressions"],
        ["Poisson(λ)",
         "e⁻ᵠ λᵏ / k!",
         "λ", "λ",
         "Rare events per interval"],
        ["Normal(μ, σ²)",
         "(1/√(2πσ²))·e^(-(x-μ)²/2σ²)",
         "μ", "σ²",
         "Sample means (via CLT)"],
    ]
    add_table(s, Inches(0.5), Inches(1.7), Inches(12.33), Inches(4.4),
              headers, rows, col_widths=[3, 5, 1.2, 1.4, 4.5],
              font_size=13, header_size=14)
    textbox(s, Inches(0.5), Inches(6.4), Inches(12.33), Inches(0.6),
            ("Memorise the moments — they appear in everything from class-"
             "imbalance reasoning to confidence-interval width."),
            size=13, color=MUTED, align=PP_ALIGN.CENTER)
    footer(s, "Ch 6")


def partB_bayes_disease():
    s = add_slide()
    slide_title(s, "Bayes' theorem · the rare-disease worked example")
    slide_subtitle(s, "Why a 99%-accurate test isn't 99% reliable")
    # formula
    rrect(s, Inches(0.5), Inches(1.6), Inches(12.33), Inches(1.0),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(0.5), Inches(1.6), Inches(12.33), Inches(1.0),
            "P(disease | +)  =  [ P(+ | disease) · P(disease) ]  /  P(+)",
            size=22, bold=True, color=WHITE, align=PP_ALIGN.CENTER,
            anchor=MSO_ANCHOR.MIDDLE)
    # set-up
    rrect(s, Inches(0.5), Inches(2.85), Inches(6.0), Inches(2.4),
          fill=PANEL, line=BLUE)
    textbox(s, Inches(0.7), Inches(2.95), Inches(5.6), Inches(0.4),
            "SETUP", size=14, bold=True, color=BLUE)
    textbox(s, Inches(0.7), Inches(3.35), Inches(5.6), Inches(2.0),
            ("Prevalence:           P(D)  = 0.001\n"
             "Sensitivity:           P(+|D)  = 0.99\n"
             "False positive rate: P(+|¬D) = 0.05\n\n"
             "Population: 100,000 people."),
            size=14, color=LIGHT, font="Consolas")
    # arithmetic
    rrect(s, Inches(6.85), Inches(2.85), Inches(6.0), Inches(2.4),
          fill=PANEL, line=GREEN)
    textbox(s, Inches(7.05), Inches(2.95), Inches(5.6), Inches(0.4),
            "ARITHMETIC", size=14, bold=True, color=GREEN)
    textbox(s, Inches(7.05), Inches(3.35), Inches(5.6), Inches(2.0),
            ("True positives:   0.001 · 0.99 · 100k =     99\n"
             "False positives:  0.999 · 0.05 · 100k =  4,995\n"
             "Total positives:                            5,094\n\n"
             "P(D | +) = 99 / 5,094  ≈  1.9%"),
            size=14, color=LIGHT, font="Consolas")
    # punchline
    rrect(s, Inches(0.5), Inches(5.5), Inches(12.33), Inches(1.4),
          fill=ACCENT)
    textbox(s, Inches(0.5), Inches(5.5), Inches(12.33), Inches(1.4),
            ("Test is \"99% accurate\".  A positive result still means only "
             "1.9% chance of disease.\n"
             "Posterior = (likelihood × prior) / evidence — and the prior "
             "matters as much as the likelihood."),
            size=15, bold=True, color=WHITE, align=PP_ALIGN.CENTER,
            anchor=MSO_ANCHOR.MIDDLE)
    footer(s, "Ch 8")


def partB_lln_clt():
    s = add_slide()
    slide_title(s, "LLN and CLT · why averages behave")
    slide_subtitle(s, "The two theorems that make statistics possible")
    # LLN box
    rrect(s, Inches(0.5), Inches(1.7), Inches(6.0), Inches(5.0),
          fill=PANEL, line=BLUE)
    rect(s, Inches(0.5), Inches(1.7), Inches(6.0), Inches(0.55), fill=BLUE)
    textbox(s, Inches(0.5), Inches(1.7), Inches(6.0), Inches(0.55),
            "Law of Large Numbers", size=18, bold=True, color=WHITE,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    textbox(s, Inches(0.7), Inches(2.4), Inches(5.6), Inches(0.6),
            "X̄ₙ  →  μ   as n → ∞",
            size=22, color=WHITE, bold=True, font="Consolas",
            align=PP_ALIGN.CENTER)
    # diagram: noisy line settling
    import math
    ox, oy = Inches(0.8), Inches(5.8)
    arrow(s, ox, oy, ox, Inches(3.4), color=MUTED)
    arrow(s, ox, oy, Inches(6.3), oy, color=MUTED)
    # horizontal mean line
    line(s, ox, Inches(4.6), Inches(6.3), Inches(4.6), color=GREEN,
         weight=1.5, dash=True)
    # noisy curve converging
    pts = []
    import random; random.seed(7)
    for i in range(60):
        x = ox + Inches(0.1 + i * 0.09)
        noise = (random.random() - 0.5) * (1.0 / (1 + i * 0.15))
        y = Inches(4.6) - Inches(noise * 1.2)
        pts.append((x, y))
    for i in range(len(pts) - 1):
        line(s, pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
             color=BLUE, weight=1.2)
    textbox(s, Inches(0.7), Inches(6.0), Inches(5.6), Inches(0.5),
            "Sample mean converges to true mean.", size=12, color=MUTED,
            align=PP_ALIGN.CENTER)
    # CLT box
    rrect(s, Inches(6.85), Inches(1.7), Inches(6.0), Inches(5.0),
          fill=PANEL, line=GREEN)
    rect(s, Inches(6.85), Inches(1.7), Inches(6.0), Inches(0.55),
         fill=GREEN)
    textbox(s, Inches(6.85), Inches(1.7), Inches(6.0), Inches(0.55),
            "Central Limit Theorem", size=18, bold=True, color=WHITE,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    textbox(s, Inches(7.05), Inches(2.4), Inches(5.6), Inches(0.6),
            "X̄ₙ  ~  Normal(μ, σ²/n)",
            size=22, color=WHITE, bold=True, font="Consolas",
            align=PP_ALIGN.CENTER)
    # two distribution sketches
    # source — skewed
    textbox(s, Inches(7.05), Inches(3.2), Inches(2.6), Inches(0.4),
            "Source dist (any)", size=11, color=MUTED, align=PP_ALIGN.CENTER)
    ox2, oy2 = Inches(7.2), Inches(5.6)
    arrow(s, ox2, oy2, ox2, Inches(3.7), color=MUTED)
    arrow(s, ox2, oy2, Inches(9.6), oy2, color=MUTED)
    # skewed bars
    sk = [0.3, 0.9, 1.6, 1.4, 0.9, 0.6, 0.4, 0.3]
    bx = ox2 + Inches(0.1)
    for hh in sk:
        rect(s, bx, oy2 - Inches(hh), Inches(0.25), Inches(hh), fill=PURPLE)
        bx += Inches(0.28)
    # arrow to →
    arrow(s, Inches(9.7), Inches(4.5), Inches(10.05), Inches(4.5),
          color=ACCENT, weight=2.5)
    # sample-mean dist — bell
    textbox(s, Inches(10.0), Inches(3.2), Inches(2.6), Inches(0.4),
            "Dist of X̄ₙ", size=11, color=MUTED, align=PP_ALIGN.CENTER)
    ox3, oy3 = Inches(10.1), Inches(5.6)
    arrow(s, ox3, oy3, ox3, Inches(3.7), color=MUTED)
    arrow(s, ox3, oy3, Inches(12.7), oy3, color=MUTED)
    pts = []
    for i in range(40):
        t = -2.5 + 5 * i / 39
        yv = math.exp(-t * t / 2)
        px = ox3 + Inches(0.1 + (i / 39) * 2.4)
        py = oy3 - Inches(yv * 1.7)
        pts.append((px, py))
    for i in range(len(pts) - 1):
        line(s, pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
             color=GREEN, weight=2.0)
    textbox(s, Inches(7.05), Inches(6.0), Inches(5.6), Inches(0.5),
            "Mean of n samples becomes Normal, whatever the source.",
            size=12, color=MUTED, align=PP_ALIGN.CENTER)
    footer(s, "Ch 9")


def partB_hypothesis_pipeline():
    s = add_slide()
    slide_title(s, "The hypothesis-testing pipeline")
    slide_subtitle(s, "Five boxes — every test in classical stats slots in")
    steps = [
        ("State H₀ and H₁",
         "Null: no effect.\nAlternative: the effect you suspect."),
        ("Pick test\nstatistic",
         "Choose based on data:\nt-test, χ², z, F, KS…"),
        ("Pick α\n(significance)",
         "Type-I error budget.\nUsually 0.05 or 0.01."),
        ("Compute\np-value",
         "P(seeing data this extreme | H₀ true)."),
        ("Decide",
         "p < α  →  reject H₀.\nElse: fail to reject (NOT \"accept\")."),
    ]
    y = Inches(2.2); h = Inches(2.4); w = Inches(2.3)
    x = Inches(0.55)
    for i, (t, body) in enumerate(steps):
        rrect(s, x, y, w, h, fill=PANEL, line=ACCENT)
        ellipse(s, x + Inches(0.95), y - Inches(0.25), Inches(0.5),
                Inches(0.5), fill=ACCENT)
        textbox(s, x + Inches(0.95), y - Inches(0.25), Inches(0.5),
                Inches(0.5), str(i + 1), size=14, bold=True, color=WHITE,
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        textbox(s, x + Inches(0.1), y + Inches(0.3), w - Inches(0.2),
                Inches(0.7), t, size=14, bold=True, color=WHITE,
                align=PP_ALIGN.CENTER)
        textbox(s, x + Inches(0.15), y + Inches(1.1), w - Inches(0.3),
                Inches(1.2), body, size=11, color=LIGHT, align=PP_ALIGN.CENTER)
        if i < 4:
            arrow(s, x + w, y + Inches(1.2), x + w + Inches(0.1),
                  y + Inches(1.2))
        x += w + Inches(0.1)
    textbox(s, Inches(0.5), Inches(5.4), Inches(12.33), Inches(1.6),
            ("A small p-value is evidence against H₀ — it is NOT the "
             "probability that H₀ is true, and it is NOT the probability "
             "you'd get the same effect again. See next slide."),
            size=14, color=MUTED, align=PP_ALIGN.CENTER)
    footer(s, "Ch 10")


def partB_pvalue_truth():
    s = add_slide()
    slide_title(s, "The p-value · what it IS vs what it ISN'T")
    slide_subtitle(s, "More misinterpreted than understood")
    headers = ["The p-value IS", "The p-value is NOT"]
    rows = [
        ["P(data this extreme | H₀ true)",
         "P(H₀ true | data)"],
        ["A statement about long-run behaviour under H₀",
         "The probability the result will replicate"],
        ["Sensitive to sample size — large n shrinks p",
         "A measure of effect size or practical importance"],
        ["A decision tool when paired with α and effect size",
         "Proof that the alternative hypothesis is correct"],
        ["Conditional on a specific model + assumptions",
         "Robust to multiple comparisons (Bonferroni etc.)"],
    ]
    add_table(s, Inches(0.5), Inches(1.7), Inches(12.33), Inches(4.4),
              headers, rows, col_widths=[1, 1], font_size=14,
              header_size=15)
    rrect(s, Inches(0.5), Inches(6.35), Inches(12.33), Inches(0.6),
          fill=ACCENT)
    textbox(s, Inches(0.5), Inches(6.35), Inches(12.33), Inches(0.6),
            "p ≠ probability the null is true.   p = probability of THIS DATA, given the null.",
            size=14, bold=True, color=WHITE, align=PP_ALIGN.CENTER,
            anchor=MSO_ANCHOR.MIDDLE)
    footer(s, "Ch 10")


def partB_confidence_intervals():
    s = add_slide()
    slide_title(s, "Confidence intervals · the misunderstood cousin")
    slide_subtitle(s, "Long-run coverage — not a probability about the parameter")
    # diagram: many intervals, some miss the true value
    line(s, Inches(7.0), Inches(1.9), Inches(7.0), Inches(6.5),
         color=ACCENT, weight=2.5, dash=True)
    textbox(s, Inches(7.05), Inches(1.65), Inches(2), Inches(0.3),
            "true μ", size=12, color=ACCENT, bold=True)
    import random; random.seed(3)
    y = Inches(2.0)
    for i in range(18):
        center = 7.0 + (random.random() - 0.5) * 1.2
        half = 0.6 + random.random() * 0.3
        lo = Inches(center - half)
        hi = Inches(center + half)
        miss = not (center - half <= 7.0 <= center + half)
        c = RED if miss else GREEN
        line(s, lo, y, hi, y, color=c, weight=2.5)
        # caps
        line(s, lo, y - Inches(0.06), lo, y + Inches(0.06), color=c, weight=2.5)
        line(s, hi, y - Inches(0.06), hi, y + Inches(0.06), color=c, weight=2.5)
        y += Inches(0.25)
    # left panel
    rrect(s, Inches(0.5), Inches(1.7), Inches(5.7), Inches(5.0),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(0.7), Inches(1.85), Inches(5.3), Inches(0.4),
            "WHAT A 95% CI ACTUALLY MEANS", size=14, bold=True, color=ACCENT)
    textbox(s, Inches(0.7), Inches(2.4), Inches(5.3), Inches(4.2),
            ("If you repeated the experiment many times and built a CI "
             "each time using the same procedure, about 95% of those "
             "intervals would contain the true parameter.\n\n"
             "It does NOT mean:\n"
             "• 95% chance THIS interval contains μ.\n"
             "• 95% of data points are in it.\n"
             "• Future estimates land here 95% of the time.\n\n"
             "Right →  18 intervals from 18 simulated samples.\n"
             "Green covered μ; red missed."),
            size=13, color=LIGHT)
    footer(s, "Ch 10")



# =======================================================================
# PART C — LINEAR ALGEBRA & CALCULUS
# =======================================================================

def partC_vectors_dot():
    s = add_slide()
    slide_title(s, "Vectors as arrows · dot product as similarity")
    slide_subtitle(s, "Geometry first, indices later")
    # left: vectors
    rrect(s, Inches(0.5), Inches(1.7), Inches(6.0), Inches(5.0),
          fill=PANEL, line=BLUE)
    textbox(s, Inches(0.7), Inches(1.85), Inches(5.6), Inches(0.4),
            "TWO VECTORS IN ℝ²", size=14, bold=True, color=BLUE)
    # axes
    ox, oy = Inches(3.5), Inches(5.6)
    arrow(s, ox, oy, ox, Inches(2.5), color=MUTED, weight=1.0)
    arrow(s, ox, oy, Inches(6.3), oy, color=MUTED, weight=1.0)
    # vec a: (2, 1.5) scaled
    arrow(s, ox, oy, ox + Inches(1.8), oy - Inches(1.2),
          color=ACCENT, weight=3.0)
    textbox(s, ox + Inches(1.85), oy - Inches(1.45), Inches(0.8),
            Inches(0.4), "a", size=18, bold=True, color=ACCENT)
    # vec b: (1, 2)
    arrow(s, ox, oy, ox + Inches(0.9), oy - Inches(2.0),
          color=BLUE, weight=3.0)
    textbox(s, ox + Inches(0.6), oy - Inches(2.4), Inches(0.8),
            Inches(0.4), "b", size=18, bold=True, color=BLUE)
    # angle marker
    textbox(s, ox + Inches(0.3), oy - Inches(0.55), Inches(0.6),
            Inches(0.3), "θ", size=14, color=WHITE)
    # right: formulas
    rrect(s, Inches(6.85), Inches(1.7), Inches(6.0), Inches(5.0),
          fill=PANEL, line=GREEN)
    textbox(s, Inches(7.05), Inches(1.85), Inches(5.6), Inches(0.4),
            "DOT PRODUCT", size=14, bold=True, color=GREEN)
    textbox(s, Inches(7.05), Inches(2.4), Inches(5.6), Inches(3.6),
            ("Algebraic:   a · b  =  Σᵢ aᵢ bᵢ\n\n"
             "Geometric:  a · b  =  ‖a‖ ‖b‖ cos θ\n\n"
             "Therefore:   cos θ  =  (a · b) / (‖a‖ ‖b‖)\n\n"
             "This is COSINE SIMILARITY — used in TF-IDF,\n"
             "embeddings, recommenders.\n\n"
             "Special cases:\n"
             "  · perpendicular  →  a · b = 0\n"
             "  · same direction →  a · b = ‖a‖ ‖b‖"),
            size=14, color=LIGHT, font="Consolas")
    footer(s, "Chs 11-12")


def partC_projection():
    s = add_slide()
    slide_title(s, "Projection · the workhorse of regression and PCA")
    slide_subtitle(s, "The shadow of a on b's direction")
    # diagram
    ox, oy = Inches(2.0), Inches(5.8)
    line(s, Inches(0.6), oy, Inches(8.0), oy, color=MUTED)
    # a direction
    arrow(s, ox, oy, Inches(6.5), Inches(3.2),
          color=ACCENT, weight=3.0)
    textbox(s, Inches(6.6), Inches(3.0), Inches(0.6), Inches(0.4),
            "a", size=18, bold=True, color=ACCENT)
    # b direction along axis
    arrow(s, ox, oy, Inches(7.5), oy, color=BLUE, weight=3.0)
    textbox(s, Inches(7.55), oy - Inches(0.05), Inches(0.6), Inches(0.4),
            "b", size=18, bold=True, color=BLUE)
    # projection drop
    line(s, Inches(6.5), Inches(3.2), Inches(6.5), oy, color=GREEN,
         weight=2.0, dash=True)
    # projection vector
    arrow(s, ox, oy + Inches(0.05), Inches(6.5), oy + Inches(0.05),
          color=GREEN, weight=3.0)
    textbox(s, Inches(3.5), oy + Inches(0.1), Inches(3), Inches(0.4),
            "proj_b(a)", size=14, bold=True, color=GREEN)
    # formula panel
    rrect(s, Inches(8.5), Inches(1.7), Inches(4.4), Inches(5.0),
          fill=PANEL, line=GREEN)
    textbox(s, Inches(8.7), Inches(1.85), Inches(4.0), Inches(0.4),
            "FORMULA", size=14, bold=True, color=GREEN)
    textbox(s, Inches(8.7), Inches(2.5), Inches(4.0), Inches(4.0),
            ("proj_b(a)  =  ((a · b) / (b · b)) · b\n\n"
             "Used in:\n"
             "• OLS regression — projecting y onto col(X)\n"
             "• Gram-Schmidt orthogonalisation\n"
             "• PCA — projecting data onto principal axes\n"
             "• Residual = a − proj_b(a)"),
            size=12, color=LIGHT, font="Consolas")
    footer(s, "Ch 12")


def partC_matrix_linear_map():
    s = add_slide()
    slide_title(s, "Matrix as a linear map")
    slide_subtitle(s, "A matrix is what it DOES to space — not the table of numbers")
    # left unit square
    rrect(s, Inches(0.5), Inches(1.7), Inches(6.0), Inches(5.0),
          fill=PANEL, line=BLUE)
    textbox(s, Inches(0.7), Inches(1.85), Inches(5.6), Inches(0.4),
            "BEFORE   (unit square, basis e₁ e₂)",
            size=14, bold=True, color=BLUE)
    ox, oy = Inches(2.0), Inches(5.8)
    arrow(s, ox, oy, ox, Inches(2.7), color=MUTED)
    arrow(s, ox, oy, Inches(6.2), oy, color=MUTED)
    rect(s, ox, oy - Inches(1.6), Inches(1.6), Inches(1.6),
         fill=BLUE)
    arrow(s, ox, oy, ox + Inches(1.6), oy, color=WHITE, weight=2.5)
    arrow(s, ox, oy, ox, oy - Inches(1.6), color=WHITE, weight=2.5)
    # right transformed
    rrect(s, Inches(6.85), Inches(1.7), Inches(6.0), Inches(5.0),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(7.05), Inches(1.85), Inches(5.6), Inches(0.4),
            "AFTER  A = [[2, 1], [0, 1.5]]",
            size=14, bold=True, color=ACCENT)
    ox2, oy2 = Inches(8.3), Inches(5.8)
    arrow(s, ox2, oy2, ox2, Inches(2.7), color=MUTED)
    arrow(s, ox2, oy2, Inches(12.6), oy2, color=MUTED)
    # parallelogram: e1 -> (2,0), e2 -> (1, 1.5)
    p1 = (ox2, oy2)
    p2 = (ox2 + Inches(2.0), oy2)
    p3 = (ox2 + Inches(2.0) + Inches(1.0), oy2 - Inches(1.8))
    p4 = (ox2 + Inches(1.0), oy2 - Inches(1.8))
    # draw parallelogram as freeform shape using ROUNDED edges via lines
    from pptx.util import Emu
    sh = s.shapes.add_shape(MSO_SHAPE.PARALLELOGRAM, p4[0], p3[1],
                            Inches(3.0), Inches(1.8))
    sh.fill.solid(); sh.fill.fore_color.rgb = ACCENT
    sh.line.fill.background(); sh.shadow.inherit = False
    # transformed basis arrows
    arrow(s, ox2, oy2, ox2 + Inches(2.0), oy2, color=WHITE, weight=2.5)
    arrow(s, ox2, oy2, ox2 + Inches(1.0), oy2 - Inches(1.8),
          color=WHITE, weight=2.5)
    textbox(s, Inches(0.5), Inches(6.6), Inches(12.33), Inches(0.5),
            "Columns of A are where e₁ and e₂ land.   det(A) = the area-scaling factor.",
            size=14, color=ACCENT, bold=True, align=PP_ALIGN.CENTER)
    footer(s, "Ch 13")


def partC_eigen():
    s = add_slide()
    slide_title(s, "Eigenvectors · directions A leaves alone")
    slide_subtitle(s, "Av = λv  —  the equation that unlocks PCA, PageRank, stability")
    rrect(s, Inches(0.5), Inches(1.6), Inches(12.33), Inches(1.0),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(0.5), Inches(1.6), Inches(12.33), Inches(1.0),
            "A v  =  λ v",
            size=40, bold=True, color=WHITE, font="Consolas",
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    # diagram
    rrect(s, Inches(0.5), Inches(2.85), Inches(6.0), Inches(4.0),
          fill=PANEL, line=BLUE)
    textbox(s, Inches(0.7), Inches(2.95), Inches(5.6), Inches(0.4),
            "Most vectors rotate when you apply A",
            size=13, color=BLUE, bold=True)
    ox, oy = Inches(3.3), Inches(6.0)
    arrow(s, ox, oy, ox, Inches(3.5), color=MUTED)
    arrow(s, ox, oy, Inches(6.3), oy, color=MUTED)
    arrow(s, ox, oy, ox + Inches(1.4), oy - Inches(1.0), color=MUTED, weight=2)
    arrow(s, ox, oy, ox + Inches(2.0), oy - Inches(0.6),
          color=BLUE, weight=2.5)
    textbox(s, ox + Inches(1.4), oy - Inches(1.3), Inches(0.6), Inches(0.3),
            "v", size=14, color=MUTED, bold=True)
    textbox(s, ox + Inches(2.0), oy - Inches(0.95), Inches(0.6), Inches(0.3),
            "Av", size=14, color=BLUE, bold=True)
    # eigen panel
    rrect(s, Inches(6.85), Inches(2.85), Inches(6.0), Inches(4.0),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(7.05), Inches(2.95), Inches(5.6), Inches(0.4),
            "Eigenvectors only stretch (or flip)", size=13,
            color=ACCENT, bold=True)
    ox, oy = Inches(9.6), Inches(6.0)
    arrow(s, ox, oy, ox, Inches(3.5), color=MUTED)
    arrow(s, ox, oy, Inches(12.6), oy, color=MUTED)
    arrow(s, ox, oy, ox + Inches(1.2), oy - Inches(1.2),
          color=ACCENT, weight=2.5)
    arrow(s, ox, oy, ox + Inches(2.2), oy - Inches(2.2),
          color=ACCENT_D, weight=3.5)
    textbox(s, ox + Inches(1.2), oy - Inches(1.55), Inches(0.6), Inches(0.3),
            "v", size=14, color=ACCENT, bold=True)
    textbox(s, ox + Inches(2.2), oy - Inches(2.55), Inches(0.6), Inches(0.3),
            "λv", size=14, color=ACCENT_D, bold=True)
    textbox(s, Inches(0.5), Inches(7.0), Inches(12.33), Inches(0.3),
            "PCA  =  eigendecomposition of the covariance matrix Σ", size=12,
            color=MUTED, align=PP_ALIGN.CENTER, bold=True)
    footer(s, "Ch 14")


def partC_gradients():
    s = add_slide()
    slide_title(s, "Gradients · the direction of steepest ascent")
    slide_subtitle(s, "∇f points uphill — gradient descent goes the other way")
    # contour plot
    rrect(s, Inches(0.5), Inches(1.7), Inches(7.0), Inches(5.0),
          fill=PANEL, line=BLUE)
    textbox(s, Inches(0.7), Inches(1.85), Inches(6.6), Inches(0.4),
            "Contours of f(x, y) = x² + 3y²", size=14, bold=True, color=BLUE)
    # nested ellipses
    cx, cy = Inches(4.0), Inches(4.4)
    for r in [0.4, 0.9, 1.4, 1.9, 2.4]:
        e = s.shapes.add_shape(MSO_SHAPE.OVAL,
                               cx - Inches(r), cy - Inches(r * 0.6),
                               Inches(2 * r), Inches(2 * r * 0.6))
        e.fill.background()
        e.line.color.rgb = MUTED
        e.line.width = Pt(1.0)
        e.shadow.inherit = False
    # gradient arrow at a point
    px, py = Inches(4.0) + Inches(1.6), Inches(4.4) - Inches(0.5)
    arrow(s, px, py, px + Inches(0.9), py - Inches(0.5),
          color=ACCENT, weight=3.0)
    textbox(s, px + Inches(0.9), py - Inches(0.85), Inches(0.8),
            Inches(0.3), "∇f", size=14, bold=True, color=ACCENT)
    # descent direction
    arrow(s, px, py, px - Inches(0.9), py + Inches(0.5),
          color=GREEN, weight=3.0)
    textbox(s, px - Inches(1.6), py + Inches(0.55), Inches(1.5),
            Inches(0.3), "−∇f  (descent)", size=12, bold=True, color=GREEN)
    # math panel
    rrect(s, Inches(7.85), Inches(1.7), Inches(5.0), Inches(5.0),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(8.05), Inches(1.85), Inches(4.6), Inches(0.4),
            "KEY IDENTITIES", size=14, bold=True, color=ACCENT)
    textbox(s, Inches(8.05), Inches(2.45), Inches(4.6), Inches(4.0),
            ("∇f  =  [ ∂f/∂x₁ , ∂f/∂x₂ , … ]ᵀ\n\n"
             "Steepest-ascent direction.\n\n"
             "Update rule (GD):\n"
             "θ ← θ − η ∇L(θ)\n\n"
             "η too small → crawl.\n"
             "η too big   → divergence.\n"
             "η just right → glide."),
            size=14, color=LIGHT, font="Consolas")
    footer(s, "Ch 15")


def partC_chain_rule():
    s = add_slide()
    slide_title(s, "Chain rule · how backprop sees the world")
    slide_subtitle(s, "Compose functions, multiply derivatives")
    # diagram: x -> u -> v -> L
    y = Inches(3.0); h = Inches(1.3); w = Inches(2.0)
    nodes = [("x", BLUE), ("u = g(x)", PANEL), ("v = h(u)", PANEL),
             ("L = ℓ(v)", ACCENT)]
    x = Inches(0.7)
    centers = []
    for label, c in nodes:
        rrect(s, x, y, w, h, fill=c, line=ACCENT if c == PANEL else None)
        textbox(s, x, y, w, h, label, size=18, bold=True,
                color=BG if c == ACCENT else WHITE,
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE,
                font="Consolas")
        centers.append((x + w, y + h / 2))
        x += w + Inches(0.85)
    for i in range(3):
        cx_from = centers[i]
        cx_to = (centers[i][0] + Inches(0.85), centers[i][1])
        arrow(s, cx_from[0], cx_from[1], cx_to[0], cx_to[1])
    # chain rule formula
    rrect(s, Inches(0.5), Inches(5.0), Inches(12.33), Inches(1.6),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(0.5), Inches(5.0), Inches(12.33), Inches(1.6),
            "dL/dx  =  dL/dv · dv/du · du/dx",
            size=28, bold=True, color=WHITE, font="Consolas",
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    textbox(s, Inches(0.5), Inches(6.75), Inches(12.33), Inches(0.4),
            "Backprop = repeated chain rule across every layer of a network.",
            size=13, color=MUTED, align=PP_ALIGN.CENTER, bold=True)
    footer(s, "Ch 15")



# =======================================================================
# PART D — FUNDAMENTAL ML PROBLEM
# =======================================================================

def partD_loss_table():
    s = add_slide()
    slide_title(s, "Loss functions · what \"good\" means to the optimiser")
    slide_subtitle(s, "Change the loss → change what the model learns")
    headers = ["Loss", "Formula", "Used for", "Property to know"]
    rows = [
        ["MSE",   "(1/n) Σ (yᵢ − ŷᵢ)²",
         "Regression",       "Penalises large errors quadratically; sensitive to outliers"],
        ["MAE",   "(1/n) Σ |yᵢ − ŷᵢ|",
         "Regression",       "Median-seeking; robust to outliers; non-smooth at 0"],
        ["Huber", "Quadratic near 0, linear far",
         "Regression w/ outliers", "Hybrid — differentiable, robust"],
        ["Binary cross-entropy", "−[ y log p + (1−y) log(1−p) ]",
         "Binary classification", "MLE under Bernoulli model"],
        ["Categorical CE", "−Σ yₖ log pₖ",
         "Multi-class classification", "MLE under multinomial; softmax pairs naturally"],
        ["Hinge",  "max(0, 1 − y · f(x))",
         "SVMs",             "Margin-based; ignores correctly-classified points"],
    ]
    add_table(s, Inches(0.5), Inches(1.7), Inches(12.33), Inches(4.8),
              headers, rows, col_widths=[2, 4.5, 3, 5.5], font_size=13,
              header_size=14)
    textbox(s, Inches(0.5), Inches(6.55), Inches(12.33), Inches(0.5),
            "The choice of loss IS a modelling decision — not just an implementation detail.",
            size=14, color=ACCENT, bold=True, align=PP_ALIGN.CENTER)
    footer(s, "Ch 16")


def partD_gradient_descent():
    s = add_slide()
    slide_title(s, "Gradient descent · the engine under almost every model")
    slide_subtitle(s, "1-D parabola — three learning rates, three fates")
    # parabola
    import math
    ox, oy = Inches(1.0), Inches(6.4)
    arrow(s, ox, oy, ox, Inches(1.8), color=MUTED)
    arrow(s, ox, oy, Inches(12.5), oy, color=MUTED)
    # vertex
    cx = Inches(6.7)
    pts = []
    for i in range(81):
        t = -2.0 + 4.0 * i / 80
        y = t * t
        px = cx + Inches(t * 1.4)
        py = oy - Inches(y * 1.0)
        pts.append((px, py))
    for i in range(len(pts) - 1):
        line(s, pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
             color=WHITE, weight=2.0)
    # three starting points / step traces
    def stepdown(x0, lr, color, n=6, dy_label_offset=0):
        x = x0
        for k in range(n):
            grad = 2 * x
            x_new = x - lr * grad
            px1 = cx + Inches(x * 1.4); py1 = oy - Inches((x * x) * 1.0)
            px2 = cx + Inches(x_new * 1.4); py2 = oy - Inches((x_new * x_new) * 1.0)
            ellipse(s, px1 - Inches(0.06), py1 - Inches(0.06),
                    Inches(0.12), Inches(0.12), fill=color)
            arrow(s, px1, py1 - Inches(0.05), px2, py2 - Inches(0.05),
                  color=color, weight=1.5)
            x = x_new
    stepdown(-1.8, 0.1,  GREEN)   # too small
    stepdown(-1.5, 0.5,  YELLOW)  # just right
    stepdown(-1.2, 1.05, RED, n=4)  # too big — oscillates / diverges
    # legend
    rrect(s, Inches(0.5), Inches(1.6), Inches(12.33), Inches(0.6),
          fill=PANEL)
    textbox(s, Inches(0.7), Inches(1.6), Inches(4), Inches(0.6),
            "η small → crawl", size=13, bold=True, color=GREEN,
            anchor=MSO_ANCHOR.MIDDLE)
    textbox(s, Inches(5.0), Inches(1.6), Inches(4), Inches(0.6),
            "η right → glide", size=13, bold=True, color=YELLOW,
            anchor=MSO_ANCHOR.MIDDLE)
    textbox(s, Inches(9.4), Inches(1.6), Inches(4), Inches(0.6),
            "η big → diverge", size=13, bold=True, color=RED,
            anchor=MSO_ANCHOR.MIDDLE)
    textbox(s, Inches(0.5), Inches(6.85), Inches(12.33), Inches(0.4),
            "θ ← θ − η · ∇L(θ)     SGD = one example/batch.   Mini-batch = compromise.",
            size=14, color=MUTED, align=PP_ALIGN.CENTER, font="Consolas")
    footer(s, "Ch 17")


def partD_capacity_ucurve():
    s = add_slide()
    slide_title(s, "Capacity · the U-shape that every modeller lives with")
    slide_subtitle(s, "Train error keeps dropping. Test error doesn't.")
    # axes
    ox, oy = Inches(1.5), Inches(6.4)
    arrow(s, ox, oy, ox, Inches(2.0), color=MUTED)
    arrow(s, ox, oy, Inches(12.3), oy, color=MUTED)
    textbox(s, Inches(12.0), oy + Inches(0.1), Inches(2), Inches(0.3),
            "capacity →", size=12, color=MUTED)
    textbox(s, ox - Inches(0.9), Inches(1.9), Inches(2), Inches(0.3),
            "error", size=12, color=MUTED)
    # train curve (monotone decreasing)
    import math
    pts_train = []
    for i in range(40):
        t = i / 39
        y = 1.0 - 0.95 * (1 - math.exp(-3 * t))
        px = ox + Inches(0.3 + t * 10.0)
        py = oy - Inches(y * 3.5)
        pts_train.append((px, py))
    for i in range(len(pts_train) - 1):
        line(s, pts_train[i][0], pts_train[i][1],
             pts_train[i + 1][0], pts_train[i + 1][1],
             color=GREEN, weight=2.5)
    # test curve — U-shape
    pts_test = []
    for i in range(40):
        t = i / 39
        # U around t=0.45
        y = 0.4 + 1.5 * (t - 0.45) ** 2 + 0.6 * math.exp(-5 * t)
        px = ox + Inches(0.3 + t * 10.0)
        py = oy - Inches(y * 1.8)
        pts_test.append((px, py))
    for i in range(len(pts_test) - 1):
        line(s, pts_test[i][0], pts_test[i][1],
             pts_test[i + 1][0], pts_test[i + 1][1],
             color=ACCENT, weight=2.5)
    # underfit / sweet / overfit zones
    line(s, ox + Inches(3.5), Inches(2.2), ox + Inches(3.5), oy,
         color=MUTED, weight=1.0, dash=True)
    line(s, ox + Inches(7.5), Inches(2.2), ox + Inches(7.5), oy,
         color=MUTED, weight=1.0, dash=True)
    textbox(s, ox + Inches(0.5), Inches(2.05), Inches(3), Inches(0.4),
            "underfit", size=14, bold=True, color=BLUE)
    textbox(s, ox + Inches(4.5), Inches(2.05), Inches(3), Inches(0.4),
            "sweet spot", size=14, bold=True, color=GREEN)
    textbox(s, ox + Inches(8.5), Inches(2.05), Inches(3), Inches(0.4),
            "overfit", size=14, bold=True, color=RED)
    # legend
    rect(s, Inches(10.5), Inches(2.6), Inches(0.4), Inches(0.1), fill=GREEN)
    textbox(s, Inches(11.0), Inches(2.5), Inches(2), Inches(0.3),
            "train error", size=12, color=GREEN)
    rect(s, Inches(10.5), Inches(2.95), Inches(0.4), Inches(0.1), fill=ACCENT)
    textbox(s, Inches(11.0), Inches(2.85), Inches(2), Inches(0.3),
            "test error", size=12, color=ACCENT)
    footer(s, "Ch 18")


def partD_bias_variance():
    s = add_slide()
    slide_title(s, "Bias-variance decomposition · the centerpiece")
    slide_subtitle(s, "Total expected error breaks into three pieces")
    # equation
    rrect(s, Inches(0.5), Inches(1.6), Inches(12.33), Inches(1.4),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(0.5), Inches(1.6), Inches(12.33), Inches(1.4),
            "E[(y − f̂(x))²]   =   Bias(f̂)²   +   Var(f̂)   +   σ²",
            size=28, bold=True, color=WHITE, font="Consolas",
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    textbox(s, Inches(0.5), Inches(2.95), Inches(12.33), Inches(0.4),
            "(systematic miss)         (instability)        (irreducible noise)",
            size=13, color=MUTED, align=PP_ALIGN.CENTER)
    # dartboards (four quadrants)
    quads = [
        ("Low bias · Low variance",   "Goal",            GREEN,  Inches(0.7), Inches(3.4)),
        ("Low bias · High variance",  "Overfit",         YELLOW, Inches(3.85), Inches(3.4)),
        ("High bias · Low variance",  "Underfit",        BLUE,   Inches(7.0),  Inches(3.4)),
        ("High bias · High variance", "Worst of both",   RED,    Inches(10.15), Inches(3.4)),
    ]
    import random; random.seed(11)
    for title, sub, c, x, y in quads:
        rrect(s, x, y, Inches(3.0), Inches(3.5), fill=PANEL, line=c)
        textbox(s, x, y + Inches(0.05), Inches(3.0), Inches(0.4),
                title, size=11, color=c, bold=True, align=PP_ALIGN.CENTER)
        textbox(s, x, y + Inches(0.4), Inches(3.0), Inches(0.4),
                sub, size=14, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
        # dartboard
        cx = x + Inches(1.5); cy = y + Inches(2.0)
        for r, fc in [(0.9, RED), (0.65, YELLOW), (0.4, WHITE), (0.18, BG)]:
            ellipse(s, cx - Inches(r), cy - Inches(r),
                    Inches(2 * r), Inches(2 * r),
                    fill=fc, line=GREY)
        # darts
        # determine bias offset and variance scatter
        bx_off = 0.0 if "Low bias" in title else 0.45
        var = 0.08 if "Low variance" in title else 0.4
        for _ in range(8):
            dx = bx_off + (random.random() - 0.5) * 2 * var
            dy = (random.random() - 0.5) * 2 * var
            ellipse(s, cx + Inches(dx) - Inches(0.06),
                    cy + Inches(dy) - Inches(0.06),
                    Inches(0.12), Inches(0.12), fill=BLUE)
    footer(s, "Ch 19")


def partD_regularisation_geometry():
    s = add_slide()
    slide_title(s, "L1 vs L2 · the geometry of \"don't get too big\"")
    slide_subtitle(s, "Why L1 zeroes coefficients and L2 just shrinks them")
    # left: L1 diamond
    rrect(s, Inches(0.5), Inches(1.7), Inches(6.0), Inches(5.0),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(0.7), Inches(1.85), Inches(5.6), Inches(0.4),
            "L1 (Lasso) — ‖β‖₁ ≤ t  → diamond",
            size=14, bold=True, color=ACCENT)
    cx, cy = Inches(3.5), Inches(4.4)
    # diamond
    dh = Inches(1.4)
    diamond = s.shapes.add_shape(MSO_SHAPE.DIAMOND, cx - dh, cy - dh,
                                 Inches(2.8), Inches(2.8))
    diamond.fill.solid(); diamond.fill.fore_color.rgb = ACCENT_D
    diamond.line.color.rgb = ACCENT; diamond.line.width = Pt(2.0)
    diamond.shadow.inherit = False
    # OLS contours (ellipses) offset
    ocx = cx + Inches(1.0); ocy = cy - Inches(0.6)
    for r in [0.5, 0.9, 1.3]:
        e = s.shapes.add_shape(MSO_SHAPE.OVAL,
                               ocx - Inches(r * 1.2), ocy - Inches(r * 0.8),
                               Inches(r * 2.4), Inches(r * 1.6))
        e.fill.background(); e.line.color.rgb = LIGHT
        e.line.width = Pt(1.2); e.shadow.inherit = False
    # touch point on a vertex
    ellipse(s, cx + dh - Inches(0.1), cy - Inches(0.1),
            Inches(0.2), Inches(0.2), fill=YELLOW)
    textbox(s, Inches(0.7), Inches(6.0), Inches(5.6), Inches(0.7),
            "Optimum touches a CORNER → some coefficient = 0 → sparsity.",
            size=13, color=LIGHT, align=PP_ALIGN.CENTER)
    # right: L2 circle
    rrect(s, Inches(6.85), Inches(1.7), Inches(6.0), Inches(5.0),
          fill=PANEL, line=BLUE)
    textbox(s, Inches(7.05), Inches(1.85), Inches(5.6), Inches(0.4),
            "L2 (Ridge) — ‖β‖₂ ≤ t  → circle",
            size=14, bold=True, color=BLUE)
    cx2, cy2 = Inches(9.85), Inches(4.4)
    ellipse(s, cx2 - Inches(1.4), cy2 - Inches(1.4),
            Inches(2.8), Inches(2.8),
            fill=RGBColor(0x1E, 0x4A, 0x8C), line=BLUE)
    ocx2 = cx2 + Inches(1.0); ocy2 = cy2 - Inches(0.6)
    for r in [0.5, 0.9, 1.3]:
        e = s.shapes.add_shape(MSO_SHAPE.OVAL,
                               ocx2 - Inches(r * 1.2), ocy2 - Inches(r * 0.8),
                               Inches(r * 2.4), Inches(r * 1.6))
        e.fill.background(); e.line.color.rgb = LIGHT
        e.line.width = Pt(1.2); e.shadow.inherit = False
    # smooth touch — no corner
    ellipse(s, cx2 + Inches(1.0), cy2 - Inches(0.5),
            Inches(0.2), Inches(0.2), fill=YELLOW)
    textbox(s, Inches(7.05), Inches(6.0), Inches(5.6), Inches(0.7),
            "Optimum touches a SMOOTH boundary → coefficients shrink but stay nonzero.",
            size=13, color=LIGHT, align=PP_ALIGN.CENTER)
    footer(s, "Ch 20")


def partD_kfold_cv():
    s = add_slide()
    slide_title(s, "k-fold cross-validation")
    slide_subtitle(s, "Every example is val once, train (k-1) times — k=5 below")
    rows = 5
    cols = 5
    cell_w = Inches(2.2); cell_h = Inches(0.7)
    grid_x = Inches(1.5); grid_y = Inches(2.0)
    for i in range(rows):
        # row label
        textbox(s, Inches(0.5), grid_y + cell_h * i, Inches(1.0), cell_h,
                f"Fold {i + 1}", size=13, color=LIGHT, bold=True,
                anchor=MSO_ANCHOR.MIDDLE)
        for j in range(cols):
            is_val = (j == i)
            c = ACCENT if is_val else PANEL
            rect(s, grid_x + cell_w * j, grid_y + cell_h * i,
                 cell_w - Inches(0.05), cell_h - Inches(0.05),
                 fill=c, line=GREY)
            label = "VAL" if is_val else "train"
            textbox(s, grid_x + cell_w * j, grid_y + cell_h * i,
                    cell_w - Inches(0.05), cell_h - Inches(0.05),
                    label, size=12, bold=True,
                    color=WHITE if is_val else MUTED,
                    align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    textbox(s, Inches(0.5), Inches(5.8), Inches(12.33), Inches(0.5),
            "CV-score  =  mean of the k val-fold scores   (and the SD tells you stability)",
            size=14, color=ACCENT, bold=True, align=PP_ALIGN.CENTER)
    textbox(s, Inches(0.5), Inches(6.4), Inches(12.33), Inches(0.6),
            ("Stratified: preserves class ratios per fold (use for classification).\n"
             "Time-series: rolling windows, no future-into-past leakage."),
            size=13, color=MUTED, align=PP_ALIGN.CENTER)
    footer(s, "Ch 22")


def partD_leakage():
    s = add_slide()
    slide_title(s, "Data leakage · the silent killer of holdouts")
    slide_subtitle(s, "Test info leaking into train → optimistic, unreproducible scores")
    headers = ["Source of leakage", "How it happens", "Mitigation"]
    rows = [
        ["Target leakage",
         "Feature is computed using future / label-derived info",
         "Audit every feature for time-of-knowledge"],
        ["Train-test contamination",
         "Imputation / scaling fit on full data, then split",
         "Fit transformers on train only; reuse on test"],
        ["Group leakage",
         "Same user / patient / device in both train and val",
         "GroupKFold; split by entity, not by row"],
        ["Time leakage",
         "Random split when data is temporal",
         "TimeSeriesSplit; train past → predict future"],
        ["Duplicate rows",
         "Same record appears in train and test",
         "Dedupe before split; track join keys"],
        ["Tuning leakage",
         "Test set touched during HPO",
         "Three-way split or nested CV"],
    ]
    add_table(s, Inches(0.5), Inches(1.7), Inches(12.33), Inches(5.0),
              headers, rows, col_widths=[3, 6, 5], font_size=13,
              header_size=14)
    footer(s, "Ch 22")



# =======================================================================
# PART E — FEATURE ENGINEERING
# =======================================================================

def partE_missing_taxonomy():
    s = add_slide()
    slide_title(s, "Missing data taxonomy · MCAR / MAR / MNAR")
    slide_subtitle(s, "The mechanism dictates the legal imputation")
    cards = [
        ("MCAR",
         "Missing Completely At Random",
         "Missingness is independent of all data.",
         "Sensor power blip drops 1% of rows.",
         "Drop rows OR simple impute — both unbiased.",
         GREEN),
        ("MAR",
         "Missing At Random",
         "Missingness depends on OBSERVED variables only.",
         "Older respondents skip the income question.",
         "Impute using observed features (KNN / MICE).",
         YELLOW),
        ("MNAR",
         "Missing Not At Random",
         "Missingness depends on the UNOBSERVED value itself.",
         "High earners refuse to disclose income.",
         "Hard — model the missingness or accept bias.",
         RED),
    ]
    x = Inches(0.5); y = Inches(1.7); w = Inches(4.1); h = Inches(5.2)
    for title, full, mech, ex, fix, c in cards:
        rrect(s, x, y, w, h, fill=PANEL, line=c)
        rect(s, x, y, w, Inches(0.6), fill=c)
        textcol = BG if c == YELLOW else WHITE
        textbox(s, x, y, w, Inches(0.6), title, size=22, bold=True,
                color=textcol, align=PP_ALIGN.CENTER,
                anchor=MSO_ANCHOR.MIDDLE)
        textbox(s, x + Inches(0.2), y + Inches(0.7), w - Inches(0.4),
                Inches(0.4), full, size=12, color=c, bold=True)
        textbox(s, x + Inches(0.2), y + Inches(1.2), w - Inches(0.4),
                Inches(1.4), "MECHANISM", size=11, color=ACCENT, bold=True)
        textbox(s, x + Inches(0.2), y + Inches(1.5), w - Inches(0.4),
                Inches(1.0), mech, size=13, color=LIGHT)
        textbox(s, x + Inches(0.2), y + Inches(2.6), w - Inches(0.4),
                Inches(0.4), "EXAMPLE", size=11, color=ACCENT, bold=True)
        textbox(s, x + Inches(0.2), y + Inches(2.9), w - Inches(0.4),
                Inches(1.0), ex, size=13, color=LIGHT)
        textbox(s, x + Inches(0.2), y + Inches(4.0), w - Inches(0.4),
                Inches(0.4), "WHAT TO DO", size=11, color=ACCENT, bold=True)
        textbox(s, x + Inches(0.2), y + Inches(4.3), w - Inches(0.4),
                Inches(1.0), fix, size=13, color=LIGHT)
        x += w + Inches(0.1)
    footer(s, "Ch 24")


def partE_categorical_decision():
    s = add_slide()
    slide_title(s, "Categorical encoding · a decision tree")
    slide_subtitle(s, "Cardinality drives the choice — not personal preference")
    # root
    rrect(s, Inches(5.0), Inches(1.7), Inches(3.5), Inches(0.8),
          fill=ACCENT)
    textbox(s, Inches(5.0), Inches(1.7), Inches(3.5), Inches(0.8),
            "Categorical feature", size=16, bold=True, color=WHITE,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    # ordered?
    rrect(s, Inches(5.0), Inches(2.9), Inches(3.5), Inches(0.7),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(5.0), Inches(2.9), Inches(3.5), Inches(0.7),
            "Is the order meaningful?", size=13, color=LIGHT,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    arrow(s, Inches(6.75), Inches(2.5), Inches(6.75), Inches(2.9))
    # yes branch
    rrect(s, Inches(0.6), Inches(4.0), Inches(3.5), Inches(2.7),
          fill=PANEL, line=GREEN)
    rect(s, Inches(0.6), Inches(4.0), Inches(3.5), Inches(0.5), fill=GREEN)
    textbox(s, Inches(0.6), Inches(4.0), Inches(3.5), Inches(0.5),
            "ORDINAL", size=14, bold=True, color=WHITE,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    textbox(s, Inches(0.8), Inches(4.65), Inches(3.1), Inches(2.0),
            ("size = {S, M, L, XL}\n→ {0, 1, 2, 3}\n\n"
             "Map to integers in their natural order. The model can "
             "exploit monotonicity."),
            size=12, color=LIGHT)
    arrow(s, Inches(5.0), Inches(3.25), Inches(2.5), Inches(4.0),
          color=GREEN)
    # no branch — cardinality
    rrect(s, Inches(9.4), Inches(4.0), Inches(3.5), Inches(0.7),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(9.4), Inches(4.0), Inches(3.5), Inches(0.7),
            "How many levels?", size=13, color=LIGHT,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    arrow(s, Inches(8.5), Inches(3.25), Inches(11.0), Inches(4.0))
    # 3 leaves
    leaves = [
        ("Low  (≤ 10)", "One-Hot",
         "Adds k or k−1 columns.\nClean, no false ordering."),
        ("Mid  (~50)",  "Target / Frequency",
         "Replace category with mean(y|cat).\nGuard against leakage with CV."),
        ("High (>100)", "Hashing / Embedding",
         "Hashing → fixed-width, lossy.\nEmbedding → learn dense rep."),
    ]
    x = Inches(0.6); y = Inches(5.1)
    for card, technique, body in leaves:
        rrect(s, x, y, Inches(4.1), Inches(1.7), fill=PANEL, line=BLUE)
        textbox(s, x + Inches(0.15), y + Inches(0.1), Inches(3.8),
                Inches(0.3), card, size=11, color=BLUE, bold=True)
        textbox(s, x + Inches(0.15), y + Inches(0.4), Inches(3.8),
                Inches(0.4), technique, size=14, color=WHITE, bold=True)
        textbox(s, x + Inches(0.15), y + Inches(0.85), Inches(3.8),
                Inches(0.85), body, size=11, color=LIGHT)
        x += Inches(4.2)
    arrow(s, Inches(10.0), Inches(4.7), Inches(2.6), Inches(5.1), color=BLUE)
    arrow(s, Inches(11.0), Inches(4.7), Inches(6.8), Inches(5.1), color=BLUE)
    arrow(s, Inches(12.0), Inches(4.7), Inches(11.0), Inches(5.1), color=BLUE)
    footer(s, "Ch 25")


def partE_numerical_transforms():
    s = add_slide()
    slide_title(s, "Numerical transforms · when to use which scaler")
    slide_subtitle(s, "Algorithm + distribution + outliers → choice")
    headers = ["Transform", "Formula", "Good when", "Bad when"]
    rows = [
        ["StandardScaler",
         "(x − μ) / σ",
         "~Normal, distance-based models (KNN, SVM, k-means, NN)",
         "Heavy outliers (μ, σ blown out)"],
        ["MinMaxScaler",
         "(x − min) / (max − min)",
         "Bounded inputs needed (e.g. images, NN sigmoid)",
         "Outliers compress the rest"],
        ["RobustScaler",
         "(x − median) / IQR",
         "Outliers present; want centred features",
         "When you want strict [0,1] bounds"],
        ["Log / log1p",
         "log(1 + x)",
         "Right-skewed, positive, multiplicative effects",
         "Negative or zero-heavy data"],
        ["Box-Cox",
         "(xλ − 1) / λ",
         "Want optimal power transform to normal",
         "x must be strictly positive"],
        ["Yeo-Johnson",
         "Generalised Box-Cox",
         "Box-Cox but with negatives allowed",
         "When simpler scaler suffices"],
        ["No scaling",
         "—",
         "Trees, GBDT — split rule is scale-invariant",
         "Distance/coefficient-based models"],
    ]
    add_table(s, Inches(0.5), Inches(1.7), Inches(12.33), Inches(5.0),
              headers, rows, col_widths=[2.2, 3.0, 4.5, 3.5],
              font_size=12, header_size=13)
    footer(s, "Ch 26")


def partE_outliers():
    s = add_slide()
    slide_title(s, "Outlier detection · four lenses, four tradeoffs")
    slide_subtitle(s, "No single method is right — combine them, then investigate")
    headers = ["Method", "What it checks", "Assumes", "Watch out for"]
    rows = [
        ["z-score (|z| > 3)",
         "Standard deviations from mean",
         "Approximate normality",
         "Skewed data; μ, σ contaminated"],
        ["IQR rule (Tukey)",
         "Below Q1 − 1.5·IQR or above Q3 + 1.5·IQR",
         "Robust quartiles available",
         "Multimodal distributions"],
        ["Mahalanobis distance",
         "Distance accounting for covariance",
         "Multivariate normal-ish",
         "Singular covariance with correlated features"],
        ["Isolation Forest",
         "Few splits to isolate → anomaly",
         "Anomalies are rare and different",
         "Needs tuning of contamination rate"],
        ["DBSCAN noise points",
         "Points outside any dense cluster",
         "Density structure exists",
         "Hyperparameter (ε, minPts) sensitivity"],
    ]
    add_table(s, Inches(0.5), Inches(1.7), Inches(12.33), Inches(5.0),
              headers, rows, col_widths=[2.5, 4, 3.5, 3.5],
              font_size=12, header_size=13)
    textbox(s, Inches(0.5), Inches(6.85), Inches(12.33), Inches(0.4),
            "An outlier is a question, not an answer — investigate before deleting.",
            size=13, color=ACCENT, bold=True, align=PP_ALIGN.CENTER)
    footer(s, "Ch 27")


def partE_cyclical_encoding():
    s = add_slide()
    slide_title(s, "Cyclical features · the sin/cos trick")
    slide_subtitle(s, "Hour 23 and hour 0 are close. Integers say they're not.")
    # circle
    rrect(s, Inches(0.5), Inches(1.7), Inches(6.0), Inches(5.0),
          fill=PANEL, line=BLUE)
    textbox(s, Inches(0.7), Inches(1.85), Inches(5.6), Inches(0.4),
            "Hours-of-day mapped to the unit circle",
            size=13, bold=True, color=BLUE)
    cx, cy = Inches(3.5), Inches(4.5)
    ellipse(s, cx - Inches(1.6), cy - Inches(1.6),
            Inches(3.2), Inches(3.2), fill=BG, line=BLUE)
    # 24 hour ticks
    import math
    for h in range(24):
        a = (h / 24) * 2 * math.pi - math.pi / 2
        x = cx + Inches(math.cos(a) * 1.6)
        y = cy + Inches(math.sin(a) * 1.6)
        ellipse(s, x - Inches(0.05), y - Inches(0.05),
                Inches(0.1), Inches(0.1),
                fill=ACCENT if h in (0, 6, 12, 18) else WHITE)
        if h in (0, 6, 12, 18):
            tx = cx + Inches(math.cos(a) * 1.9)
            ty = cy + Inches(math.sin(a) * 1.9)
            textbox(s, tx - Inches(0.25), ty - Inches(0.15),
                    Inches(0.5), Inches(0.3),
                    str(h), size=11, color=ACCENT, bold=True,
                    align=PP_ALIGN.CENTER)
    # right: formula
    rrect(s, Inches(6.85), Inches(1.7), Inches(6.0), Inches(5.0),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(7.05), Inches(1.85), Inches(5.6), Inches(0.4),
            "ENCODING", size=14, bold=True, color=ACCENT)
    textbox(s, Inches(7.05), Inches(2.4), Inches(5.6), Inches(4.3),
            ("sin_h  =  sin(2π · h / 24)\n"
             "cos_h  =  cos(2π · h / 24)\n\n"
             "Why two columns?\n"
             "Either one alone is two-to-one\n"
             "(e.g. sin(π/4) = sin(3π/4)).\n\n"
             "Use also for:\n"
             "• day of week  (period 7)\n"
             "• month        (period 12)\n"
             "• day of year  (period 365)"),
            size=14, color=LIGHT, font="Consolas")
    footer(s, "Ch 28")


def partE_feature_selection():
    s = add_slide()
    slide_title(s, "Feature selection · three families")
    slide_subtitle(s, "Filter / Wrapper / Embedded — different cost, different fidelity")
    cards = [
        ("FILTER",
         "Score features independently of any model",
         ["Correlation w/ target",
          "Mutual information",
          "χ² for categorical",
          "Variance threshold"],
         "Fast, model-agnostic",
         "Ignores interactions",
         BLUE),
        ("WRAPPER",
         "Train a model on subsets, optimise score",
         ["Recursive feat. elim. (RFE)",
          "Forward / backward selection",
          "Sequential feat. selection"],
         "Accurate, model-aware",
         "Expensive; risk of overfitting",
         YELLOW),
        ("EMBEDDED",
         "Selection happens inside model training",
         ["L1-penalised regression",
          "Tree feature importances",
          "Boosting gain / weight"],
         "Good cost / quality balance",
         "Selection ties to one model class",
         GREEN),
    ]
    x = Inches(0.5); y = Inches(1.7); w = Inches(4.1); h = Inches(5.2)
    for title, sub, items, pro, con, c in cards:
        rrect(s, x, y, w, h, fill=PANEL, line=c)
        rect(s, x, y, w, Inches(0.55), fill=c)
        textcol = BG if c == YELLOW else WHITE
        textbox(s, x, y, w, Inches(0.55), title, size=18, bold=True,
                color=textcol, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        textbox(s, x + Inches(0.2), y + Inches(0.7), w - Inches(0.4),
                Inches(1.0), sub, size=12, color=ACCENT, bold=True)
        item_text = "\n".join("• " + i for i in items)
        textbox(s, x + Inches(0.2), y + Inches(1.5), w - Inches(0.4),
                Inches(2.0), item_text, size=13, color=LIGHT)
        textbox(s, x + Inches(0.2), y + Inches(3.7), w - Inches(0.4),
                Inches(0.3), "PRO", size=11, color=GREEN, bold=True)
        textbox(s, x + Inches(0.2), y + Inches(4.0), w - Inches(0.4),
                Inches(0.5), pro, size=12, color=LIGHT)
        textbox(s, x + Inches(0.2), y + Inches(4.5), w - Inches(0.4),
                Inches(0.3), "CON", size=11, color=RED, bold=True)
        textbox(s, x + Inches(0.2), y + Inches(4.8), w - Inches(0.4),
                Inches(0.5), con, size=12, color=LIGHT)
        x += w + Inches(0.1)
    footer(s, "Ch 29")


def partE_feature_store_skew():
    s = add_slide()
    slide_title(s, "Training-serving skew · why feature stores exist")
    slide_subtitle(s, "Same logic, two places — drift apart and predictions break")
    # two paths
    # Training path
    rrect(s, Inches(0.5), Inches(1.8), Inches(6.0), Inches(2.2),
          fill=PANEL, line=BLUE)
    rect(s, Inches(0.5), Inches(1.8), Inches(6.0), Inches(0.5), fill=BLUE)
    textbox(s, Inches(0.5), Inches(1.8), Inches(6.0), Inches(0.5),
            "TRAINING (batch, Spark)", size=14, bold=True, color=WHITE,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    boxlabel(s, Inches(0.7), Inches(2.5), Inches(1.5), Inches(0.6),
             "Raw data", fill=BG, color=LIGHT, size=11, line=BLUE)
    arrow(s, Inches(2.25), Inches(2.8), Inches(2.55), Inches(2.8), color=BLUE)
    boxlabel(s, Inches(2.6), Inches(2.5), Inches(2.0), Inches(0.6),
             "transform_v1", fill=BG, color=LIGHT, size=11, line=BLUE)
    arrow(s, Inches(4.65), Inches(2.8), Inches(4.95), Inches(2.8), color=BLUE)
    boxlabel(s, Inches(5.0), Inches(2.5), Inches(1.4), Inches(0.6),
             "features", fill=BG, color=LIGHT, size=11, line=BLUE)
    textbox(s, Inches(0.7), Inches(3.3), Inches(5.8), Inches(0.5),
            "Heavy windows, joins, aggregates over 90 days.",
            size=11, color=MUTED)
    # Serving path
    rrect(s, Inches(0.5), Inches(4.2), Inches(6.0), Inches(2.2),
          fill=PANEL, line=YELLOW)
    rect(s, Inches(0.5), Inches(4.2), Inches(6.0), Inches(0.5), fill=YELLOW)
    textbox(s, Inches(0.5), Inches(4.2), Inches(6.0), Inches(0.5),
            "SERVING (real-time, pandas / API)", size=14, bold=True,
            color=BG, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    boxlabel(s, Inches(0.7), Inches(4.9), Inches(1.5), Inches(0.6),
             "Live event", fill=BG, color=LIGHT, size=11, line=YELLOW)
    arrow(s, Inches(2.25), Inches(5.2), Inches(2.55), Inches(5.2),
          color=YELLOW)
    boxlabel(s, Inches(2.6), Inches(4.9), Inches(2.0), Inches(0.6),
             "transform_v1.1?", fill=BG, color=LIGHT, size=11, line=YELLOW)
    arrow(s, Inches(4.65), Inches(5.2), Inches(4.95), Inches(5.2),
          color=YELLOW)
    boxlabel(s, Inches(5.0), Inches(4.9), Inches(1.4), Inches(0.6),
             "features?", fill=BG, color=LIGHT, size=11, line=YELLOW)
    textbox(s, Inches(0.7), Inches(5.7), Inches(5.8), Inches(0.5),
            "Re-implemented by another team, in another language.",
            size=11, color=MUTED)
    # skew callout
    rrect(s, Inches(6.85), Inches(1.8), Inches(6.0), Inches(4.6),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(7.05), Inches(1.95), Inches(5.6), Inches(0.4),
            "THE SKEW PROBLEM", size=14, bold=True, color=ACCENT)
    textbox(s, Inches(7.05), Inches(2.5), Inches(5.6), Inches(3.7),
            ("Same feature, two implementations.\n"
             "Training uses 90-day average; serving rolls 30 days.\n"
             "Training imputes nulls with mean; serving drops them.\n\n"
             "Result: model sees a different distribution at predict\n"
             "time than at fit time — accuracy collapses silently.\n\n"
             "FEATURE STORE FIX\n"
             "• one definition of each feature, versioned\n"
             "• offline (Delta) and online (low-latency) views\n"
             "• point-in-time joins for training\n"
             "• same logic served from the same code path"),
            size=13, color=LIGHT)
    footer(s, "Ch 30 → Part L")



# =======================================================================
# PART F — SUPERVISED ALGORITHMS
# =======================================================================

def partF_linear_regression():
    s = add_slide()
    slide_title(s, "Linear regression · the OLS normal equation")
    slide_subtitle(s, "A closed-form solution that every later model imitates")
    rrect(s, Inches(0.5), Inches(1.7), Inches(12.33), Inches(1.6),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(0.5), Inches(1.7), Inches(12.33), Inches(1.6),
            "β̂  =  (XᵀX)⁻¹ Xᵀ y",
            size=42, bold=True, color=WHITE, font="Consolas",
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    # derivation flow
    boxes = [
        ("Loss",        "L(β) = ‖y − Xβ‖²"),
        ("Gradient",    "∇L  =  −2 Xᵀ (y − Xβ)"),
        ("Set to 0",    "Xᵀ X β  =  Xᵀ y"),
        ("Solve",       "β̂  =  (XᵀX)⁻¹ Xᵀ y"),
    ]
    x = Inches(0.5); y = Inches(3.6); w = Inches(2.95); h = Inches(1.6)
    for label, eq in boxes:
        rrect(s, x, y, w, h, fill=PANEL, line=BLUE)
        textbox(s, x, y + Inches(0.1), w, Inches(0.4),
                label, size=12, color=BLUE, bold=True,
                align=PP_ALIGN.CENTER)
        textbox(s, x, y + Inches(0.55), w, Inches(0.9), eq,
                size=14, color=WHITE, bold=True, font="Consolas",
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        x += w + Inches(0.1)
    # callouts
    textbox(s, Inches(0.5), Inches(5.4), Inches(12.33), Inches(1.6),
            ("ASSUMPTIONS:  linearity · independent errors · homoscedasticity · "
             "normal residuals · no perfect multicollinearity.\n\n"
             "WHEN IT BREAKS:  XᵀX singular  →  use ridge ( + λI )  or SVD-based "
             "pseudoinverse.   For large n, prefer iterative solvers (SGD)."),
            size=14, color=LIGHT, align=PP_ALIGN.LEFT)
    footer(s, "Ch 31")


def partF_logistic_sigmoid():
    s = add_slide()
    slide_title(s, "Logistic regression · log-odds and the sigmoid")
    slide_subtitle(s, "A linear model on the log-odds scale")
    # left: log-odds equation
    rrect(s, Inches(0.5), Inches(1.7), Inches(6.0), Inches(2.4),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(0.7), Inches(1.8), Inches(5.6), Inches(0.4),
            "MODEL", size=14, bold=True, color=ACCENT)
    textbox(s, Inches(0.7), Inches(2.3), Inches(5.6), Inches(1.8),
            ("logit(p)  =  log( p / (1 − p) )  =  βᵀx\n\n"
             "p  =  σ(βᵀx)  =  1 / (1 + e^(−βᵀx))"),
            size=15, color=WHITE, font="Consolas")
    # decision boundary
    rrect(s, Inches(0.5), Inches(4.25), Inches(6.0), Inches(2.65),
          fill=PANEL, line=BLUE)
    textbox(s, Inches(0.7), Inches(4.35), Inches(5.6), Inches(0.4),
            "DECISION BOUNDARY", size=14, bold=True, color=BLUE)
    textbox(s, Inches(0.7), Inches(4.85), Inches(5.6), Inches(2.0),
            ("p = 0.5   ⇔   βᵀx = 0\n"
             "That is the equation of a HYPERPLANE.\n\n"
             "Logistic regression is a linear classifier —\n"
             "non-linear behaviour only via features."),
            size=13, color=LIGHT, font="Consolas")
    # right: sigmoid plot
    rrect(s, Inches(6.85), Inches(1.7), Inches(6.0), Inches(5.2),
          fill=PANEL, line=GREEN)
    textbox(s, Inches(7.05), Inches(1.85), Inches(5.6), Inches(0.4),
            "σ(z) = 1 / (1 + e^(−z))",
            size=14, bold=True, color=GREEN, font="Consolas")
    import math
    ox, oy = Inches(7.5), Inches(6.5)
    arrow(s, ox, oy, ox, Inches(2.5), color=MUTED)
    arrow(s, ox - Inches(0.05), oy - Inches(1.6),
          Inches(12.5), oy - Inches(1.6), color=MUTED)
    # y axis labels
    textbox(s, ox - Inches(0.55), oy - Inches(3.4), Inches(0.5), Inches(0.3),
            "1", size=11, color=MUTED)
    textbox(s, ox - Inches(0.55), oy - Inches(1.7), Inches(0.5), Inches(0.3),
            "0.5", size=11, color=MUTED)
    textbox(s, ox - Inches(0.55), oy - Inches(0.1), Inches(0.5), Inches(0.3),
            "0", size=11, color=MUTED)
    # sigmoid
    pts = []
    for i in range(80):
        z = -6 + 12 * i / 79
        y = 1 / (1 + math.exp(-z))
        px = ox + Inches(0.1 + (i / 79) * 4.7)
        py = oy - Inches(y * 3.3)
        pts.append((px, py))
    for i in range(len(pts) - 1):
        line(s, pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
             color=GREEN, weight=2.5)
    # threshold line
    line(s, ox, oy - Inches(1.6), Inches(12.4), oy - Inches(1.6),
         color=ACCENT, weight=1.5, dash=True)
    footer(s, "Ch 32")


def partF_decision_tree():
    s = add_slide()
    slide_title(s, "Decision tree · split impurity-greedy, recurse")
    slide_subtitle(s, "Gini and entropy disagree on tails but agree on direction")
    # tree diagram
    rrect(s, Inches(0.5), Inches(1.7), Inches(7.5), Inches(5.0),
          fill=PANEL, line=BLUE)
    textbox(s, Inches(0.7), Inches(1.85), Inches(7.0), Inches(0.4),
            "Recursive binary splits", size=13, bold=True, color=BLUE)
    # root
    rrect(s, Inches(3.5), Inches(2.5), Inches(2.0), Inches(0.7),
          fill=ACCENT)
    textbox(s, Inches(3.5), Inches(2.5), Inches(2.0), Inches(0.7),
            "income ≤ 50k?", size=12, bold=True, color=WHITE,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    # left child
    rrect(s, Inches(1.0), Inches(3.8), Inches(2.0), Inches(0.7),
          fill=PANEL, line=BLUE)
    textbox(s, Inches(1.0), Inches(3.8), Inches(2.0), Inches(0.7),
            "age ≤ 30?", size=12, color=LIGHT,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    # right child
    rrect(s, Inches(5.5), Inches(3.8), Inches(2.0), Inches(0.7),
          fill=PANEL, line=BLUE)
    textbox(s, Inches(5.5), Inches(3.8), Inches(2.0), Inches(0.7),
            "balance ≤ 5k?", size=12, color=LIGHT,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    # leaves
    leaves = [(0.3, "default"), (2.0, "ok"), (4.5, "ok"), (6.2, "default")]
    for lx, lab in leaves:
        c = RED if lab == "default" else GREEN
        rrect(s, Inches(lx), Inches(5.2), Inches(1.3), Inches(0.6),
              fill=c)
        textbox(s, Inches(lx), Inches(5.2), Inches(1.3), Inches(0.6),
                lab, size=11, bold=True, color=WHITE,
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    # connectors
    arrow(s, Inches(4.5), Inches(3.2), Inches(2.0), Inches(3.8), color=MUTED)
    arrow(s, Inches(4.5), Inches(3.2), Inches(6.5), Inches(3.8), color=MUTED)
    arrow(s, Inches(2.0), Inches(4.5), Inches(0.9), Inches(5.2), color=MUTED)
    arrow(s, Inches(2.0), Inches(4.5), Inches(2.7), Inches(5.2), color=MUTED)
    arrow(s, Inches(6.5), Inches(4.5), Inches(5.2), Inches(5.2), color=MUTED)
    arrow(s, Inches(6.5), Inches(4.5), Inches(6.9), Inches(5.2), color=MUTED)
    # right: impurity panel
    rrect(s, Inches(8.3), Inches(1.7), Inches(4.6), Inches(5.0),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(8.5), Inches(1.85), Inches(4.2), Inches(0.4),
            "IMPURITY MEASURES", size=14, bold=True, color=ACCENT)
    textbox(s, Inches(8.5), Inches(2.4), Inches(4.2), Inches(4.2),
            ("Gini:    1 − Σ pₖ²\n"
             "Entropy: −Σ pₖ log pₖ\n\n"
             "Both are maximised at uniform\n"
             "and zero at pure nodes.\n\n"
             "Choose the split that maximises\n"
             "    parent_impurity − Σwc · child_impurity\n"
             "(information gain).\n\n"
             "Practical:\n"
             "• control depth / min_samples\n"
             "• prune or use min_impurity_decrease\n"
             "• categorical splits = 2^(k-1) − 1 options"),
            size=12, color=LIGHT, font="Consolas")
    footer(s, "Ch 33")


def partF_random_forest():
    s = add_slide()
    slide_title(s, "Random forest · bagging + feature randomness")
    slide_subtitle(s, "Average many decorrelated trees → variance falls, bias stays")
    # data
    rrect(s, Inches(0.5), Inches(1.9), Inches(2.2), Inches(0.8),
          fill=BLUE)
    textbox(s, Inches(0.5), Inches(1.9), Inches(2.2), Inches(0.8),
            "Training data", size=14, bold=True, color=WHITE,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    # bootstraps
    bsts = [
        (3.4, "Bootstrap 1\n(rows sampled\nwith replacement)"),
        (3.4 + 2.5, "Bootstrap 2"),
        (3.4 + 5.0, "Bootstrap B"),
    ]
    for bx, label in bsts:
        rrect(s, Inches(bx), Inches(1.7), Inches(2.3), Inches(1.3),
              fill=PANEL, line=BLUE)
        textbox(s, Inches(bx), Inches(1.7), Inches(2.3), Inches(1.3),
                label, size=11, color=LIGHT, align=PP_ALIGN.CENTER,
                anchor=MSO_ANCHOR.MIDDLE)
        arrow(s, Inches(2.7), Inches(2.35), Inches(bx), Inches(2.35),
              color=MUTED)
    # trees
    trees = [3.4, 3.4 + 2.5, 3.4 + 5.0]
    for bx in trees:
        # mini tree
        cx = Inches(bx) + Inches(1.15); cy = Inches(3.6)
        ellipse(s, cx - Inches(0.13), cy - Inches(0.13),
                Inches(0.26), Inches(0.26), fill=ACCENT)
        ellipse(s, cx - Inches(0.6), cy + Inches(0.3),
                Inches(0.2), Inches(0.2), fill=GREEN)
        ellipse(s, cx + Inches(0.4), cy + Inches(0.3),
                Inches(0.2), Inches(0.2), fill=GREEN)
        ellipse(s, cx - Inches(0.9), cy + Inches(0.8),
                Inches(0.15), Inches(0.15), fill=YELLOW)
        ellipse(s, cx - Inches(0.3), cy + Inches(0.8),
                Inches(0.15), Inches(0.15), fill=YELLOW)
        ellipse(s, cx + Inches(0.1), cy + Inches(0.8),
                Inches(0.15), Inches(0.15), fill=YELLOW)
        ellipse(s, cx + Inches(0.7), cy + Inches(0.8),
                Inches(0.15), Inches(0.15), fill=YELLOW)
        line(s, cx, cy + Inches(0.13), cx - Inches(0.5), cy + Inches(0.3),
             color=MUTED)
        line(s, cx, cy + Inches(0.13), cx + Inches(0.5), cy + Inches(0.3),
             color=MUTED)
        arrow(s, Inches(bx) + Inches(1.15), Inches(3.0),
              Inches(bx) + Inches(1.15), Inches(3.45), color=MUTED)
    # aggregation
    rrect(s, Inches(3.4), Inches(5.0), Inches(7.4), Inches(0.9),
          fill=ACCENT)
    textbox(s, Inches(3.4), Inches(5.0), Inches(7.4), Inches(0.9),
            "Aggregate:  classification → vote;  regression → mean",
            size=15, bold=True, color=WHITE,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    for bx in trees:
        arrow(s, Inches(bx) + Inches(1.15), Inches(4.6),
              Inches(bx) + Inches(1.15), Inches(5.0))
    # key idea callout
    rrect(s, Inches(0.5), Inches(6.05), Inches(12.33), Inches(1.0),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(0.5), Inches(6.05), Inches(12.33), Inches(1.0),
            ("Two sources of randomness:  (1) bootstrap rows  (2) sample √p "
             "features at each split.  Out-of-bag rows give a free CV estimate."),
            size=13, color=LIGHT, align=PP_ALIGN.CENTER,
            anchor=MSO_ANCHOR.MIDDLE)
    footer(s, "Ch 34")


def partF_adaboost():
    s = add_slide()
    slide_title(s, "AdaBoost · reweight what the last learner missed")
    slide_subtitle(s, "Three iterations — the data didn't change, the weights did")
    iters = [
        ("Iteration 1", [(0.8, 0.3, BLUE), (1.6, 0.4, BLUE),
                         (0.7, 1.0, BLUE), (2.2, 1.4, RED),
                         (2.6, 0.6, RED), (3.2, 1.5, RED)]),
        ("Iteration 2", [(0.8, 0.3, BLUE), (1.6, 0.4, BLUE),
                         (0.7, 1.0, BLUE), (2.2, 1.4, RED),
                         (2.6, 0.6, RED), (3.2, 1.5, RED)]),
        ("Iteration 3", [(0.8, 0.3, BLUE), (1.6, 0.4, BLUE),
                         (0.7, 1.0, BLUE), (2.2, 1.4, RED),
                         (2.6, 0.6, RED), (3.2, 1.5, RED)]),
    ]
    # different misclassified points get bigger
    bigger = [
        [],
        [0, 4],     # in iter 2, two of the points are emphasised
        [2, 5],     # in iter 3, different ones
    ]
    boundary_x = [2.0, 1.5, 2.5]  # vertical decision line shifts
    for i, (title, pts) in enumerate(iters):
        ox = Inches(0.5 + i * 4.3)
        rrect(s, ox, Inches(1.7), Inches(4.2), Inches(5.0),
              fill=PANEL, line=BLUE)
        textbox(s, ox, Inches(1.8), Inches(4.2), Inches(0.4),
                title, size=14, bold=True, color=BLUE, align=PP_ALIGN.CENTER)
        # axes / region
        ax_x = ox + Inches(0.3); ax_y = Inches(6.4)
        arrow(s, ax_x, ax_y, ax_x, Inches(2.4), color=MUTED)
        arrow(s, ax_x, ax_y, ox + Inches(3.9), ax_y, color=MUTED)
        # decision boundary (vertical)
        bx = ax_x + Inches(boundary_x[i] * 0.9)
        line(s, bx, Inches(2.4), bx, ax_y, color=ACCENT, weight=2.0,
             dash=True)
        # points
        for j, (px, py, col) in enumerate(pts):
            r = 0.18 if j in bigger[i] else 0.1
            ellipse(s, ax_x + Inches(px * 0.9) - Inches(r),
                    ax_y - Inches(py * 1.3) - Inches(r),
                    Inches(2 * r), Inches(2 * r), fill=col)
    textbox(s, Inches(0.5), Inches(6.85), Inches(12.83), Inches(0.4),
            "After each round, increase weights on misclassified points; train next weak learner; combine with α weights.",
            size=12, color=MUTED, align=PP_ALIGN.CENTER)
    footer(s, "Ch 35")


def partF_gbm_residuals():
    s = add_slide()
    slide_title(s, "Gradient boosting · fit pseudo-residuals")
    slide_subtitle(s, "Each tree learns what the previous ensemble got wrong")
    # flow
    boxes = [
        ("F₀(x)",       "init prediction\n(e.g. mean ȳ)"),
        ("r₁ = y − F₀", "compute\nresiduals"),
        ("h₁(x)",       "fit tree to\nresiduals"),
        ("F₁ = F₀ + η h₁", "update\nensemble"),
        ("…repeat",    "stop when val\nstops improving"),
    ]
    x = Inches(0.4); y = Inches(2.4); w = Inches(2.45); h = Inches(2.0)
    for label, body in boxes:
        rrect(s, x, y, w, h, fill=PANEL, line=ACCENT)
        textbox(s, x, y + Inches(0.2), w, Inches(0.5), label,
                size=14, bold=True, color=ACCENT,
                align=PP_ALIGN.CENTER, font="Consolas")
        textbox(s, x, y + Inches(0.85), w, Inches(1.1), body,
                size=12, color=LIGHT, align=PP_ALIGN.CENTER)
        x += w + Inches(0.1)
    # arrows under boxes
    x = Inches(0.4) + w
    for _ in range(4):
        arrow(s, x, y + Inches(1.0), x + Inches(0.1), y + Inches(1.0))
        x += w + Inches(0.1)
    # loop arrow
    line(s, Inches(12.0), Inches(4.5), Inches(12.0), Inches(5.4), color=ACCENT)
    line(s, Inches(12.0), Inches(5.4), Inches(2.6), Inches(5.4), color=ACCENT)
    line(s, Inches(2.6), Inches(5.4), Inches(2.6), Inches(4.5), color=ACCENT)
    arrow(s, Inches(2.6), Inches(4.5), Inches(2.6), Inches(4.45),
          color=ACCENT)
    # KEY IDEA
    rrect(s, Inches(0.4), Inches(5.7), Inches(12.4), Inches(1.3),
          fill=PANEL, line=GREEN)
    textbox(s, Inches(0.6), Inches(5.8), Inches(12.0), Inches(0.4),
            "WHY \"GRADIENT\"?", size=13, bold=True, color=GREEN)
    textbox(s, Inches(0.6), Inches(6.15), Inches(12.0), Inches(0.85),
            ("For squared loss, residual (y − F) IS the negative gradient. "
             "For other losses, swap residual for −∂L/∂F.  The next tree "
             "is a discrete step in the steepest-descent direction over function space."),
            size=13, color=LIGHT)
    footer(s, "Ch 36")


def partF_xgb_lgbm_cat():
    s = add_slide()
    slide_title(s, "XGBoost · LightGBM · CatBoost")
    slide_subtitle(s, "Same idea, three engineering philosophies")
    headers = ["", "XGBoost", "LightGBM", "CatBoost"]
    rows = [
        ["Tree growth",
         "Level-wise (balanced)",
         "Leaf-wise (best-gain)",
         "Symmetric / oblivious"],
        ["Speed lever",
         "Histogram + GPU",
         "Histogram + GOSS + EFB",
         "Histogram + ordered boosting"],
        ["Categorical",
         "Manual (OHE / target)",
         "Native int-encoded",
         "Native — ordered TS, best for high card."],
        ["Default regularisation",
         "γ, λ in objective",
         "min_data, leaves",
         "L2 + ordered TS prevents target leak"],
        ["Wins when",
         "Need rock-solid baselines",
         "Very wide datasets, fast iter",
         "Heavy categorical, small-to-mid data"],
        ["Watch out for",
         "Slower than LGBM on wide data",
         "Overfit on small data; tune carefully",
         "Slower train; smaller community"],
    ]
    add_table(s, Inches(0.5), Inches(1.7), Inches(12.33), Inches(5.0),
              headers, rows, col_widths=[2.5, 3.5, 3.5, 3.5],
              font_size=12, header_size=13)
    textbox(s, Inches(0.5), Inches(6.8), Inches(12.33), Inches(0.4),
            "Default to LightGBM for wide tabular; XGBoost when you need predictability; CatBoost when categoricals dominate.",
            size=12, color=ACCENT, bold=True, align=PP_ALIGN.CENTER)
    footer(s, "Ch 36")


def partF_nb_knn():
    s = add_slide()
    slide_title(s, "Naive Bayes & KNN · when each shines")
    slide_subtitle(s, "Different inductive biases — pick the one that matches your data")
    headers = ["Aspect", "Naive Bayes", "k-NN"]
    rows = [
        ["Assumption",
         "Features independent given the class",
         "Similar inputs have similar labels"],
        ["Training cost",
         "O(n p) — just count / sum",
         "O(1) — store the data"],
        ["Prediction cost",
         "O(p) per example",
         "O(n p) per example (without indexing)"],
        ["Calibration",
         "Often over-confident (independence violated)",
         "Vote-based, naturally well-calibrated"],
        ["Loves",
         "Text, high-dim sparse data",
         "Low-dim, dense, well-separated"],
        ["Hates",
         "Strongly correlated features",
         "Curse of dimensionality; needs scaling"],
        ["Common pitfall",
         "Zero counts → smoothing (Laplace)",
         "Skewed classes → distance-weighted k"],
    ]
    add_table(s, Inches(0.5), Inches(1.7), Inches(12.33), Inches(5.2),
              headers, rows, col_widths=[2.5, 5, 5], font_size=13,
              header_size=14)
    footer(s, "Ch 37")



# =======================================================================
# PART G — UNSUPERVISED
# =======================================================================

def partG_kmeans_progression():
    s = add_slide()
    slide_title(s, "k-means · four iterations of Lloyd's algorithm")
    slide_subtitle(s, "Assign → update → assign → … until centroids stop moving")
    import random; random.seed(2)
    # generate three blobs
    blobs = [
        (0.6, 0.6, BLUE),
        (2.0, 1.6, GREEN),
        (1.0, 2.2, YELLOW),
    ]
    points = []
    for (cx, cy, c) in blobs:
        for _ in range(8):
            x = cx + (random.random() - 0.5) * 0.7
            y = cy + (random.random() - 0.5) * 0.7
            points.append((x, y, c))
    # init centroids (bad on purpose)
    init = [(0.3, 0.4), (1.0, 1.0), (2.0, 1.0)]
    centroids_iters = [init,
                       [(0.7, 0.7), (1.2, 1.7), (2.1, 1.5)],
                       [(0.6, 0.6), (1.0, 2.2), (2.0, 1.6)],
                       [(0.6, 0.6), (1.0, 2.2), (2.0, 1.6)]]
    titles = ["Iter 0 — init", "Iter 1", "Iter 2", "Iter 3 — converged"]
    panel_w = Inches(3.0); panel_h = Inches(4.4)
    for i, (title, centroids) in enumerate(zip(titles, centroids_iters)):
        px = Inches(0.5 + i * 3.2)
        py = Inches(1.8)
        rrect(s, px, py, panel_w, panel_h, fill=PANEL, line=ACCENT)
        textbox(s, px, py + Inches(0.1), panel_w, Inches(0.4),
                title, size=13, bold=True, color=ACCENT, align=PP_ALIGN.CENTER)
        # axes
        ax_x = px + Inches(0.3); ax_y = py + Inches(4.1)
        arrow(s, ax_x, ax_y, ax_x, py + Inches(0.7), color=MUTED)
        arrow(s, ax_x, ax_y, px + Inches(2.8), ax_y, color=MUTED)
        # points — colored by nearest centroid in this iter
        for x, y, true_c in points:
            # assign to nearest centroid
            d = [((x - c[0]) ** 2 + (y - c[1]) ** 2) for c in centroids]
            ci = d.index(min(d))
            col = [BLUE, GREEN, YELLOW][ci]
            pxv = ax_x + Inches(x * 0.7)
            pyv = ax_y - Inches(y * 1.3)
            ellipse(s, pxv - Inches(0.07), pyv - Inches(0.07),
                    Inches(0.14), Inches(0.14), fill=col)
        # centroids — big X
        for ci, c in enumerate(centroids):
            col = [BLUE, GREEN, YELLOW][ci]
            cx = ax_x + Inches(c[0] * 0.7); cy = ax_y - Inches(c[1] * 1.3)
            # plus sign
            line(s, cx - Inches(0.2), cy, cx + Inches(0.2), cy,
                 color=col, weight=3.5)
            line(s, cx, cy - Inches(0.2), cx, cy + Inches(0.2),
                 color=col, weight=3.5)
    textbox(s, Inches(0.5), Inches(6.4), Inches(12.83), Inches(0.7),
            ("Inertia = Σ min‖xᵢ − μₖ‖² monotonically decreases.  Init matters — use k-means++ to avoid bad locals."),
            size=13, color=MUTED, align=PP_ALIGN.CENTER)
    footer(s, "Ch 38")


def partG_choose_k():
    s = add_slide()
    slide_title(s, "Choosing k · elbow + silhouette")
    slide_subtitle(s, "Two diagnostics, two questions — agree before you commit")
    import math
    # elbow plot
    rrect(s, Inches(0.5), Inches(1.7), Inches(6.0), Inches(5.2),
          fill=PANEL, line=BLUE)
    textbox(s, Inches(0.7), Inches(1.85), Inches(5.6), Inches(0.4),
            "ELBOW (inertia vs k)", size=14, bold=True, color=BLUE)
    ox, oy = Inches(1.2), Inches(6.6)
    arrow(s, ox, oy, ox, Inches(2.4), color=MUTED)
    arrow(s, ox, oy, Inches(6.2), oy, color=MUTED)
    textbox(s, Inches(5.7), oy + Inches(0.05), Inches(1), Inches(0.3),
            "k", size=12, color=MUTED)
    pts = []
    for k in range(1, 11):
        val = 10 / k + 0.5
        px = ox + Inches(k * 0.45)
        py = oy - Inches(val * 0.3)
        pts.append((px, py))
        ellipse(s, px - Inches(0.06), py - Inches(0.06),
                Inches(0.12), Inches(0.12), fill=BLUE)
    for i in range(len(pts) - 1):
        line(s, pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
             color=BLUE, weight=2.0)
    # elbow at k=3
    ellipse(s, pts[2][0] - Inches(0.18), pts[2][1] - Inches(0.18),
            Inches(0.36), Inches(0.36), fill=BG, line=ACCENT)
    textbox(s, pts[2][0] + Inches(0.2), pts[2][1] - Inches(0.4),
            Inches(2.5), Inches(0.4), "elbow at k=3", size=12, color=ACCENT,
            bold=True)
    # silhouette
    rrect(s, Inches(6.85), Inches(1.7), Inches(6.0), Inches(5.2),
          fill=PANEL, line=GREEN)
    textbox(s, Inches(7.05), Inches(1.85), Inches(5.6), Inches(0.4),
            "SILHOUETTE (score vs k)", size=14, bold=True, color=GREEN)
    ox2, oy2 = Inches(7.5), Inches(6.6)
    arrow(s, ox2, oy2, ox2, Inches(2.4), color=MUTED)
    arrow(s, ox2, oy2, Inches(12.6), oy2, color=MUTED)
    sil = [0.0, 0.32, 0.62, 0.55, 0.42, 0.35, 0.28, 0.22, 0.18]
    sp = []
    for k, v in zip(range(2, 11), sil):
        px = ox2 + Inches((k - 1) * 0.5)
        py = oy2 - Inches(v * 5.0)
        sp.append((px, py))
        ellipse(s, px - Inches(0.06), py - Inches(0.06),
                Inches(0.12), Inches(0.12), fill=GREEN)
    for i in range(len(sp) - 1):
        line(s, sp[i][0], sp[i][1], sp[i + 1][0], sp[i + 1][1],
             color=GREEN, weight=2.0)
    ellipse(s, sp[1][0] - Inches(0.18), sp[1][1] - Inches(0.18),
            Inches(0.36), Inches(0.36), fill=BG, line=ACCENT)
    textbox(s, sp[1][0] + Inches(0.2), sp[1][1] - Inches(0.4),
            Inches(2.5), Inches(0.4), "peak at k=3", size=12, color=ACCENT,
            bold=True)
    textbox(s, Inches(0.5), Inches(7.0), Inches(12.33), Inches(0.3),
            "Silhouette ranges from −1 (wrong cluster) to +1 (well placed).",
            size=11, color=MUTED, align=PP_ALIGN.CENTER)
    footer(s, "Ch 38")


def partG_hierarchical():
    s = add_slide()
    slide_title(s, "Hierarchical clustering · the dendrogram")
    slide_subtitle(s, "Build a tree of merges — cut it horizontally to choose k")
    # dendrogram
    rrect(s, Inches(0.5), Inches(1.8), Inches(12.33), Inches(4.0),
          fill=PANEL, line=BLUE)
    # leaves at bottom
    base_y = Inches(5.4)
    leaf_xs = [Inches(1.0 + i * 1.3) for i in range(8)]
    labels = ["A", "B", "C", "D", "E", "F", "G", "H"]
    for x, lab in zip(leaf_xs, labels):
        textbox(s, x - Inches(0.15), base_y + Inches(0.05), Inches(0.3),
                Inches(0.3), lab, size=12, color=LIGHT, bold=True,
                align=PP_ALIGN.CENTER)
    # merges define vertical levels
    merges = [
        ([0, 1], 4.9),
        ([2, 3], 4.9),
        ([4, 5], 4.8),
        ([6, 7], 4.8),
        ([0.5, 2.5], 4.3),  # AB-CD
        ([4.5, 6.5], 4.3),  # EF-GH
        ([1.5, 5.5], 3.2),  # everything
    ]
    # store merged x of each cluster id
    cluster_x = {i: leaf_xs[i] for i in range(8)}
    cluster_y = {i: base_y for i in range(8)}
    for kids, yv in merges:
        yE = Inches(yv)
        # for first 4 merges, kids are indices
        if all(isinstance(k, int) for k in kids):
            x1 = cluster_x[kids[0]]; y1 = cluster_y[kids[0]]
            x2 = cluster_x[kids[1]]; y2 = cluster_y[kids[1]]
        else:
            # use the kids as x-positions directly
            x1 = Inches(kids[0] + 1.0); x2 = Inches(kids[1] + 1.0)
            # find their last-known y
            y1 = Inches(4.9 if kids[0] in (0.5, 2.5) else 4.8)
            y2 = Inches(4.9 if kids[1] in (0.5, 2.5) else 4.8)
        # vertical lines down to children
        line(s, x1, y1, x1, yE, color=ACCENT, weight=2.0)
        line(s, x2, y2, x2, yE, color=ACCENT, weight=2.0)
        # horizontal merge
        line(s, x1, yE, x2, yE, color=ACCENT, weight=2.0)
        # parent x = midpoint
        if all(isinstance(k, int) for k in kids):
            mid = (x1 + x2) // 2
            for k in kids:
                cluster_x[k] = mid; cluster_y[k] = yE
    # cut line
    line(s, Inches(0.7), Inches(3.7), Inches(11.5), Inches(3.7),
         color=GREEN, weight=2.0, dash=True)
    textbox(s, Inches(11.6), Inches(3.55), Inches(1.6), Inches(0.3),
            "cut → k=2", size=12, color=GREEN, bold=True)
    # right linkage panel
    rrect(s, Inches(0.5), Inches(5.95), Inches(12.33), Inches(1.0),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(0.7), Inches(6.0), Inches(11.9), Inches(0.4),
            "LINKAGE CHOICES", size=12, color=ACCENT, bold=True)
    textbox(s, Inches(0.7), Inches(6.35), Inches(11.9), Inches(0.6),
            ("single = min pairwise (chains).   complete = max (compact).   "
             "average = mean.   Ward = minimise variance increase (most common with Euclidean)."),
            size=12, color=LIGHT)
    footer(s, "Ch 39")


def partG_pca_eigen():
    s = add_slide()
    slide_title(s, "PCA · eigendecomposition of the covariance matrix")
    slide_subtitle(s, "Rotate axes so the first direction captures the most variance")
    # equations
    rrect(s, Inches(0.5), Inches(1.7), Inches(6.0), Inches(5.2),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(0.7), Inches(1.85), Inches(5.6), Inches(0.4),
            "DERIVATION", size=14, bold=True, color=ACCENT)
    textbox(s, Inches(0.7), Inches(2.35), Inches(5.6), Inches(4.5),
            ("1.  Centre X:    Xc = X − μ\n\n"
             "2.  Covariance:  Σ  =  (1/n) Xcᵀ Xc\n\n"
             "3.  Eigen:       Σ vₖ  =  λₖ vₖ\n\n"
             "4.  Sort λ₁ ≥ λ₂ ≥ … ≥ λp\n\n"
             "5.  Top k eigenvectors → projection matrix W\n\n"
             "6.  Reduced data:  Z = Xc W\n\n"
             "Variance explained:  λₖ / Σⱼ λⱼ"),
            size=13, color=LIGHT, font="Consolas")
    # scree plot
    rrect(s, Inches(6.85), Inches(1.7), Inches(6.0), Inches(5.2),
          fill=PANEL, line=GREEN)
    textbox(s, Inches(7.05), Inches(1.85), Inches(5.6), Inches(0.4),
            "SCREE  (cumulative variance explained)",
            size=14, bold=True, color=GREEN)
    ox, oy = Inches(7.5), Inches(6.6)
    arrow(s, ox, oy, ox, Inches(2.4), color=MUTED)
    arrow(s, ox, oy, Inches(12.6), oy, color=MUTED)
    # bars + cumulative line
    vals = [0.42, 0.21, 0.13, 0.08, 0.06, 0.04, 0.03, 0.02, 0.01]
    cum = 0
    cum_pts = []
    for k, v in enumerate(vals):
        bx = ox + Inches(0.2 + k * 0.55)
        bh = Inches(v * 7.0)
        rect(s, bx, oy - bh, Inches(0.45), bh, fill=GREEN)
        cum += v
        cum_pts.append((bx + Inches(0.225), oy - Inches(cum * 3.8)))
    for i in range(len(cum_pts) - 1):
        line(s, cum_pts[i][0], cum_pts[i][1],
             cum_pts[i + 1][0], cum_pts[i + 1][1],
             color=ACCENT, weight=2.5)
    # 95% threshold
    line(s, ox, oy - Inches(0.95 * 3.8), Inches(12.6), oy - Inches(0.95 * 3.8),
         color=YELLOW, weight=1.5, dash=True)
    textbox(s, Inches(11.6), oy - Inches(0.95 * 3.8) - Inches(0.2),
            Inches(1.0), Inches(0.3), "95%", size=11, color=YELLOW, bold=True)
    footer(s, "Ch 40")


def partG_tsne_umap_caveats():
    s = add_slide()
    slide_title(s, "t-SNE & UMAP · what these plots do NOT tell you")
    slide_subtitle(s, "Beautiful maps, treacherous interpretations")
    headers = ["The plot shows", "It does NOT show"]
    rows = [
        ["Local neighbourhood structure",
         "Global distances — far apart ≠ very different"],
        ["Whether clusters exist (probably)",
         "Cluster SIZES — areas are not preserved"],
        ["Coarse separation patterns",
         "Cluster DENSITIES — apparent gaps may be artifact"],
        ["A useful exploratory view",
         "A reliable feature space for downstream classifiers"],
        ["Reproducibility within a run",
         "Reproducibility across perplexity / n_neighbors / seed"],
    ]
    add_table(s, Inches(0.5), Inches(1.7), Inches(12.33), Inches(4.4),
              headers, rows, col_widths=[1, 1], font_size=14,
              header_size=15)
    rrect(s, Inches(0.5), Inches(6.3), Inches(12.33), Inches(0.7),
          fill=ACCENT)
    textbox(s, Inches(0.5), Inches(6.3), Inches(12.33), Inches(0.7),
            "Use t-SNE / UMAP to see structure — never to measure it.",
            size=15, bold=True, color=WHITE, align=PP_ALIGN.CENTER,
            anchor=MSO_ANCHOR.MIDDLE)
    footer(s, "Ch 41")



# =======================================================================
# PART H — EVALUATION
# =======================================================================

def partH_confusion_matrix():
    s = add_slide()
    slide_title(s, "The confusion matrix · 2×2 with real numbers")
    slide_subtitle(s, "A loan-default classifier on 1,000 customers")
    # 2x2 matrix
    cx = Inches(2.0); cy = Inches(2.4); cell = Inches(2.2)
    # headers
    textbox(s, cx + cell, cy - Inches(0.6), cell * 2, Inches(0.4),
            "Actual",
            size=14, color=ACCENT, bold=True, align=PP_ALIGN.CENTER)
    textbox(s, cx + cell, cy - Inches(0.25), cell, Inches(0.3),
            "Default (1)", size=12, color=LIGHT, bold=True,
            align=PP_ALIGN.CENTER)
    textbox(s, cx + cell * 2, cy - Inches(0.25), cell, Inches(0.3),
            "OK (0)", size=12, color=LIGHT, bold=True,
            align=PP_ALIGN.CENTER)
    # left side labels
    textbox(s, cx - Inches(0.6), cy + cell * 0.5 - Inches(0.5),
            Inches(0.6), Inches(1.0), "P\nr\ne\nd",
            size=14, color=ACCENT, bold=True, align=PP_ALIGN.CENTER)
    textbox(s, cx, cy, cell, cell, "Pos (1)", size=12, color=LIGHT,
            bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    textbox(s, cx, cy + cell, cell, cell, "Neg (0)", size=12,
            color=LIGHT, bold=True, align=PP_ALIGN.CENTER,
            anchor=MSO_ANCHOR.MIDDLE)
    # cells
    cells = [
        (1, 0, "TP", 80, GREEN, "True\npositive"),
        (2, 0, "FP", 60, RED, "False\npositive"),
        (1, 1, "FN", 20, RED, "False\nnegative"),
        (2, 1, "TN", 840, GREEN, "True\nnegative"),
    ]
    for col, row, lab, val, c, sub in cells:
        rect(s, cx + cell * col, cy + cell * row, cell, cell,
             fill=PANEL, line=c)
        textbox(s, cx + cell * col, cy + cell * row + Inches(0.1),
                cell, Inches(0.5), lab, size=18, bold=True, color=c,
                align=PP_ALIGN.CENTER)
        textbox(s, cx + cell * col, cy + cell * row + Inches(0.65),
                cell, Inches(0.7),
                str(val), size=36, bold=True, color=WHITE,
                align=PP_ALIGN.CENTER)
        textbox(s, cx + cell * col, cy + cell * row + Inches(1.55),
                cell, Inches(0.5), sub, size=10, color=MUTED,
                align=PP_ALIGN.CENTER)
    # metrics panel
    rrect(s, Inches(7.5), Inches(1.9), Inches(5.4), Inches(5.0),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(7.7), Inches(2.05), Inches(5.0), Inches(0.4),
            "DERIVED METRICS", size=14, bold=True, color=ACCENT)
    textbox(s, Inches(7.7), Inches(2.55), Inches(5.0), Inches(4.3),
            ("Accuracy  =  (TP + TN) / N   =  92.0%\n\n"
             "Precision = TP / (TP + FP) =  80 / 140  = 57.1%\n\n"
             "Recall    = TP / (TP + FN) =  80 / 100  = 80.0%\n\n"
             "F1        = 2·P·R / (P + R)            = 66.7%\n\n"
             "Specificity = TN / (TN + FP)           = 93.3%\n\n"
             "Prevalence =  100 / 1000               = 10%"),
            size=12, color=LIGHT, font="Consolas")
    footer(s, "Ch 42")


def partH_precision_recall_f1():
    s = add_slide()
    slide_title(s, "Precision · Recall · F1 — and when you care about which")
    slide_subtitle(s, "Asymmetric costs → asymmetric metrics")
    headers = ["Metric", "Formula", "Optimise when…", "Example"]
    rows = [
        ["Precision",
         "TP / (TP + FP)",
         "False positives are expensive",
         "Spam filter — don't quarantine real mail"],
        ["Recall",
         "TP / (TP + FN)",
         "False negatives are expensive",
         "Cancer screen — don't miss a real case"],
        ["F1",
         "2 P R / (P + R)",
         "Balanced concerns; class imbalance",
         "Single-number sanity check"],
        ["F-β  (β=2)",
         "(1+β²) P R / (β² P + R)",
         "Recall matters β times more",
         "Fraud — recall heavier, but not infinite"],
        ["Specificity",
         "TN / (TN + FP)",
         "Negatives need to be screened well",
         "Disease-free certification"],
    ]
    add_table(s, Inches(0.5), Inches(1.7), Inches(12.33), Inches(4.5),
              headers, rows, col_widths=[2, 3, 4, 5], font_size=13,
              header_size=14)
    rrect(s, Inches(0.5), Inches(6.4), Inches(12.33), Inches(0.6),
          fill=ACCENT)
    textbox(s, Inches(0.5), Inches(6.4), Inches(12.33), Inches(0.6),
            "There is no \"best\" metric. There is a cost matrix — and the metric that mirrors it.",
            size=14, bold=True, color=WHITE, align=PP_ALIGN.CENTER,
            anchor=MSO_ANCHOR.MIDDLE)
    footer(s, "Ch 42")


def partH_roc_curve():
    s = add_slide()
    slide_title(s, "ROC curve · sweep the threshold, plot TPR vs FPR")
    slide_subtitle(s, "AUC = area under this staircase")
    # axes
    rrect(s, Inches(0.5), Inches(1.7), Inches(8.5), Inches(5.2),
          fill=PANEL, line=BLUE)
    ox, oy = Inches(1.8), Inches(6.5)
    arrow(s, ox, oy, ox, Inches(2.1), color=MUTED)
    arrow(s, ox, oy, Inches(8.7), oy, color=MUTED)
    textbox(s, Inches(8.5), oy + Inches(0.05), Inches(1.5), Inches(0.3),
            "FPR", size=12, color=MUTED, bold=True)
    textbox(s, ox - Inches(1.0), Inches(2.0), Inches(1.5), Inches(0.3),
            "TPR", size=12, color=MUTED, bold=True)
    # diagonal random
    line(s, ox, oy, Inches(8.5), Inches(2.2), color=GREY, weight=1.5, dash=True)
    textbox(s, Inches(7.0), Inches(4.2), Inches(2), Inches(0.3),
            "random", size=11, color=GREY)
    # ROC curve — concave
    import math
    pts = []
    for i in range(60):
        f = i / 59
        t = 1 - (1 - f) ** 3
        px = ox + Inches(f * 6.6)
        py = oy - Inches(t * 4.3)
        pts.append((px, py))
    for i in range(len(pts) - 1):
        line(s, pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
             color=ACCENT, weight=2.5)
    # mark a few thresholds
    for i, lab in [(15, "τ=0.7"), (30, "τ=0.5"), (50, "τ=0.2")]:
        ellipse(s, pts[i][0] - Inches(0.08), pts[i][1] - Inches(0.08),
                Inches(0.16), Inches(0.16), fill=YELLOW)
        textbox(s, pts[i][0] + Inches(0.1), pts[i][1] - Inches(0.05),
                Inches(1.5), Inches(0.3), lab, size=11, color=YELLOW)
    # right: interpretation
    rrect(s, Inches(9.3), Inches(1.7), Inches(3.6), Inches(5.2),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(9.5), Inches(1.85), Inches(3.2), Inches(0.4),
            "AUC INTERPRETATION", size=12, bold=True, color=ACCENT)
    textbox(s, Inches(9.5), Inches(2.35), Inches(3.2), Inches(4.5),
            ("AUC  =  P(score₊ > score₋)\n\n"
             "Probability that a random\n"
             "positive scores higher than\n"
             "a random negative.\n\n"
             "0.5  →  random\n"
             "1.0  →  perfect ranking\n\n"
             "Threshold-free metric —\n"
             "compares rankings, not\n"
             "specific operating points."),
            size=12, color=LIGHT, font="Consolas")
    footer(s, "Ch 43")


def partH_roc_vs_pr():
    s = add_slide()
    slide_title(s, "ROC vs PR · imbalanced classes change the picture")
    slide_subtitle(s, "Same model, two curves — only one is honest under skew")
    # left ROC
    rrect(s, Inches(0.5), Inches(1.7), Inches(6.0), Inches(5.2),
          fill=PANEL, line=BLUE)
    textbox(s, Inches(0.7), Inches(1.85), Inches(5.6), Inches(0.4),
            "ROC — looks great", size=14, bold=True, color=BLUE)
    ox, oy = Inches(1.3), Inches(6.5)
    arrow(s, ox, oy, ox, Inches(2.4), color=MUTED)
    arrow(s, ox, oy, Inches(6.2), oy, color=MUTED)
    line(s, ox, oy, Inches(6.2), Inches(2.5), color=GREY, dash=True)
    import math
    pts = []
    for i in range(60):
        f = i / 59
        t = 1 - (1 - f) ** 4
        px = ox + Inches(f * 4.6); py = oy - Inches(t * 3.7)
        pts.append((px, py))
    for i in range(len(pts) - 1):
        line(s, pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
             color=ACCENT, weight=2.5)
    textbox(s, Inches(2.5), Inches(3.0), Inches(3), Inches(0.3),
            "AUC = 0.94", size=14, color=GREEN, bold=True)
    # right PR
    rrect(s, Inches(6.85), Inches(1.7), Inches(6.0), Inches(5.2),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(7.05), Inches(1.85), Inches(5.6), Inches(0.4),
            "PR — same model, much sadder", size=14, bold=True, color=ACCENT)
    ox2, oy2 = Inches(7.65), Inches(6.5)
    arrow(s, ox2, oy2, ox2, Inches(2.4), color=MUTED)
    arrow(s, ox2, oy2, Inches(12.6), oy2, color=MUTED)
    # PR curve — bows downward sharply
    pts2 = []
    for i in range(60):
        r = i / 59
        p = max(0.05, 1.0 - 0.95 * r ** 0.7)
        px = ox2 + Inches(r * 4.6); py = oy2 - Inches(p * 3.7)
        pts2.append((px, py))
    for i in range(len(pts2) - 1):
        line(s, pts2[i][0], pts2[i][1], pts2[i + 1][0], pts2[i + 1][1],
             color=ACCENT, weight=2.5)
    textbox(s, Inches(8.5), Inches(3.0), Inches(3.5), Inches(0.3),
            "AP = 0.42", size=14, color=ACCENT, bold=True)
    textbox(s, Inches(0.5), Inches(7.0), Inches(12.33), Inches(0.3),
            "When positives are < 1% of data, ROC AUC flatters the model.   PR (and Average Precision) tell the truth.",
            size=11, color=MUTED, align=PP_ALIGN.CENTER)
    footer(s, "Ch 43")


def partH_regression_metrics():
    s = add_slide()
    slide_title(s, "Regression metrics · what each penalises")
    slide_subtitle(s, "Same residuals — different metrics tell different stories")
    headers = ["Metric", "Formula", "Penalty shape", "Use when"]
    rows = [
        ["MSE",
         "(1/n) Σ (y − ŷ)²",
         "Quadratic — big errors dominate",
         "Outliers matter; you fit by OLS"],
        ["RMSE",
         "√MSE",
         "Same units as y",
         "Reporting; comparing across datasets"],
        ["MAE",
         "(1/n) Σ |y − ŷ|",
         "Linear — robust",
         "Outliers should not dominate"],
        ["MAPE",
         "(100/n) Σ |y − ŷ| / |y|",
         "Relative",
         "Errors should scale with magnitude (sales)"],
        ["R²",
         "1 − SS_res / SS_tot",
         "Variance fraction explained",
         "Comparing model vs mean baseline"],
        ["Adjusted R²",
         "1 − (1 − R²)(n−1)/(n−p−1)",
         "Penalises extra features",
         "Comparing models with different p"],
    ]
    add_table(s, Inches(0.5), Inches(1.7), Inches(12.33), Inches(5.0),
              headers, rows, col_widths=[2, 3, 4, 5], font_size=12,
              header_size=13)
    textbox(s, Inches(0.5), Inches(6.85), Inches(12.33), Inches(0.4),
            "MAPE explodes when y ≈ 0 — use SMAPE or absolute-error variants if your target straddles zero.",
            size=12, color=ACCENT, bold=True, align=PP_ALIGN.CENTER)
    footer(s, "Ch 44")


def partH_imbalanced_techniques():
    s = add_slide()
    slide_title(s, "Imbalanced classification · four lines of defence")
    slide_subtitle(s, "Pick the technique by where it intervenes")
    headers = ["Lever", "Technique", "Where it acts", "Watch out for"]
    rows = [
        ["Splitting",
         "Stratified k-fold",
         "Train/val/test composition",
         "Doesn't help the model — only honest scoring"],
        ["Loss",
         "Class weights / focal loss",
         "Inside the optimiser",
         "Don't combine with resampling blindly"],
        ["Threshold",
         "Move τ away from 0.5",
         "After training",
         "Set on val, not test"],
        ["Data",
         "Over- (SMOTE) / undersample",
         "Training data only",
         "Leakage if applied before CV split"],
        ["Algorithm",
         "Choose calibrated learners",
         "Model selection",
         "Calibrate (Platt / isotonic) if needed"],
        ["Metric",
         "Use PR / AP, not accuracy / ROC AUC",
         "Reporting",
         "Beware of \"accuracy\" with 1% positives"],
    ]
    add_table(s, Inches(0.5), Inches(1.7), Inches(12.33), Inches(5.2),
              headers, rows, col_widths=[2, 4, 4, 4], font_size=12,
              header_size=13)
    footer(s, "Ch 46")


def partH_multiclass_macros():
    s = add_slide()
    slide_title(s, "Multi-class evaluation · micro vs macro vs weighted")
    slide_subtitle(s, "Three ways to roll per-class scores into one number — they disagree")
    headers = ["Average", "Formula", "Treats classes…", "Use when"]
    rows = [
        ["Micro-F1",
         "F1 computed from total TP, FP, FN",
         "By their size (frequent classes dominate)",
         "Accuracy-like; balanced data"],
        ["Macro-F1",
         "Mean of per-class F1",
         "Equally, regardless of size",
         "All classes matter equally"],
        ["Weighted-F1",
         "Σ wₖ Fₖ, weight by class support",
         "By their size, like micro — but per-class",
         "Imbalanced + want per-class interpretability"],
        ["Per-class",
         "F1 for each class shown separately",
         "Individually",
         "Diagnose which classes the model fails on"],
    ]
    add_table(s, Inches(0.5), Inches(1.7), Inches(12.33), Inches(4.4),
              headers, rows, col_widths=[2, 4.5, 4.5, 3.5],
              font_size=13, header_size=14)
    rrect(s, Inches(0.5), Inches(6.3), Inches(12.33), Inches(0.65),
          fill=ACCENT)
    textbox(s, Inches(0.5), Inches(6.3), Inches(12.33), Inches(0.65),
            "Multi-label ≠ multi-class — multi-label uses Hamming loss, subset accuracy, sample-averaged F1.",
            size=13, bold=True, color=WHITE, align=PP_ALIGN.CENTER,
            anchor=MSO_ANCHOR.MIDDLE)
    footer(s, "Ch 47")



# =======================================================================
# PART I — HYPERPARAMETER OPTIMIZATION
# =======================================================================

def partI_hpo_problem():
    s = add_slide()
    slide_title(s, "The HPO problem · objective + search space + budget")
    slide_subtitle(s, "Minimise val-loss over θ, subject to a compute budget")
    rrect(s, Inches(0.5), Inches(1.7), Inches(12.33), Inches(1.4),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(0.5), Inches(1.7), Inches(12.33), Inches(1.4),
            "θ*  =  argmin_{θ ∈ Θ}   E[ L( model(θ), val ) ]",
            size=26, bold=True, color=WHITE, font="Consolas",
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    # three components
    cards = [
        ("OBJECTIVE",
         "What you actually evaluate.\n\nVal loss / CV mean / business KPI.\n\nMust be cheap-ish (you'll call it many times) but representative.",
         BLUE),
        ("SEARCH SPACE Θ",
         "Continuous (lr, λ), discrete (n_estimators), categorical (solver).\n\nLog-scale where natural (lr, λ).\nMixed spaces are the hard case.",
         GREEN),
        ("BUDGET",
         "Wall-clock, trials, dollars.\n\nDrives algorithm choice:\n• small budget  →  random / Bayesian\n• big budget   →  grid (rarely worth it)\n• parallel     →  ASHA / Hyperband",
         YELLOW),
    ]
    x = Inches(0.5); y = Inches(3.4); w = Inches(4.1); h = Inches(3.6)
    for title, body, c in cards:
        rrect(s, x, y, w, h, fill=PANEL, line=c)
        rect(s, x, y, w, Inches(0.55), fill=c)
        textbox(s, x, y, w, Inches(0.55), title,
                size=15, bold=True, color=BG if c == YELLOW else WHITE,
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        textbox(s, x + Inches(0.2), y + Inches(0.7), w - Inches(0.4),
                h - Inches(0.85), body, size=13, color=LIGHT)
        x += w + Inches(0.1)
    footer(s, "Ch 48")


def partI_grid_vs_random():
    s = add_slide()
    slide_title(s, "Grid vs random · same budget, very different coverage")
    slide_subtitle(s, "Bergstra & Bengio (2012): random wins on most landscapes")
    # left grid
    rrect(s, Inches(0.5), Inches(1.7), Inches(6.0), Inches(5.2),
          fill=PANEL, line=BLUE)
    textbox(s, Inches(0.7), Inches(1.85), Inches(5.6), Inches(0.4),
            "GRID  (9 trials, 3 × 3)", size=14, bold=True, color=BLUE)
    ox, oy = Inches(1.5), Inches(6.4)
    arrow(s, ox, oy, ox, Inches(2.4), color=MUTED)
    arrow(s, ox, oy, Inches(6.2), oy, color=MUTED)
    textbox(s, Inches(5.7), oy + Inches(0.05), Inches(1), Inches(0.3),
            "hp 1", size=11, color=MUTED)
    textbox(s, ox - Inches(0.7), Inches(2.3), Inches(1), Inches(0.3),
            "hp 2", size=11, color=MUTED)
    # grid points
    for i in range(3):
        for j in range(3):
            px = ox + Inches(1.0 + i * 1.4)
            py = oy - Inches(0.8 + j * 1.0)
            ellipse(s, px - Inches(0.1), py - Inches(0.1),
                    Inches(0.2), Inches(0.2), fill=BLUE)
    textbox(s, Inches(0.7), Inches(6.6), Inches(5.6), Inches(0.3),
            "Only 3 unique values per axis", size=11, color=MUTED,
            align=PP_ALIGN.CENTER)
    # right random
    rrect(s, Inches(6.85), Inches(1.7), Inches(6.0), Inches(5.2),
          fill=PANEL, line=GREEN)
    textbox(s, Inches(7.05), Inches(1.85), Inches(5.6), Inches(0.4),
            "RANDOM  (9 trials)", size=14, bold=True, color=GREEN)
    ox2, oy2 = Inches(7.85), Inches(6.4)
    arrow(s, ox2, oy2, ox2, Inches(2.4), color=MUTED)
    arrow(s, ox2, oy2, Inches(12.6), oy2, color=MUTED)
    textbox(s, Inches(12.1), oy2 + Inches(0.05), Inches(1), Inches(0.3),
            "hp 1", size=11, color=MUTED)
    textbox(s, ox2 - Inches(0.7), Inches(2.3), Inches(1), Inches(0.3),
            "hp 2", size=11, color=MUTED)
    import random; random.seed(7)
    for _ in range(9):
        px = ox2 + Inches(0.4 + random.random() * 4.2)
        py = oy2 - Inches(0.4 + random.random() * 3.4)
        ellipse(s, px - Inches(0.1), py - Inches(0.1),
                Inches(0.2), Inches(0.2), fill=GREEN)
    textbox(s, Inches(7.05), Inches(6.6), Inches(5.6), Inches(0.3),
            "9 unique values per axis", size=11, color=MUTED,
            align=PP_ALIGN.CENTER)
    footer(s, "Ch 49")


def partI_bo_loop():
    s = add_slide()
    slide_title(s, "Bayesian optimisation · five-step loop")
    slide_subtitle(s, "Use trial history to predict where to evaluate next")
    steps = [
        ("History",
         "All (θ, val_loss)\nseen so far"),
        ("Surrogate",
         "Fit a cheap model\n(GP / TPE) of loss\nover Θ"),
        ("Acquisition",
         "EI / UCB / TPE ratio\nbalances explore vs\nexploit"),
        ("Next θ",
         "argmax of\nacquisition\n(cheap)"),
        ("Evaluate",
         "Run expensive\ntraining, observe\nloss"),
    ]
    y = Inches(2.5); h = Inches(2.2); w = Inches(2.3)
    x = Inches(0.55)
    for i, (t, body) in enumerate(steps):
        rrect(s, x, y, w, h, fill=PANEL, line=ACCENT)
        ellipse(s, x + w/2 - Inches(0.25), y - Inches(0.25),
                Inches(0.5), Inches(0.5), fill=ACCENT)
        textbox(s, x + w/2 - Inches(0.25), y - Inches(0.25),
                Inches(0.5), Inches(0.5), str(i + 1),
                size=14, bold=True, color=WHITE,
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        textbox(s, x, y + Inches(0.25), w, Inches(0.5),
                t, size=14, bold=True, color=WHITE,
                align=PP_ALIGN.CENTER)
        textbox(s, x + Inches(0.15), y + Inches(0.95), w - Inches(0.3),
                Inches(1.2), body, size=11, color=LIGHT,
                align=PP_ALIGN.CENTER)
        if i < 4:
            arrow(s, x + w, y + Inches(1.1),
                  x + w + Inches(0.1), y + Inches(1.1))
        x += w + Inches(0.1)
    # loop back arrow
    line(s, Inches(12.0), Inches(4.7), Inches(12.0), Inches(5.6),
         color=ACCENT)
    line(s, Inches(12.0), Inches(5.6), Inches(2.7), Inches(5.6),
         color=ACCENT)
    line(s, Inches(2.7), Inches(5.6), Inches(2.7), Inches(4.7),
         color=ACCENT)
    arrow(s, Inches(2.7), Inches(4.7), Inches(2.7), Inches(4.65),
          color=ACCENT)
    textbox(s, Inches(0.5), Inches(6.0), Inches(12.33), Inches(0.5),
            "Append → re-fit surrogate → repeat. Each evaluation makes the surrogate smarter.",
            size=13, color=ACCENT, bold=True, align=PP_ALIGN.CENTER)
    textbox(s, Inches(0.5), Inches(6.6), Inches(12.33), Inches(0.5),
            "BO shines when each evaluation is expensive (training a deep net) and the search space is moderate-dim.",
            size=12, color=MUTED, align=PP_ALIGN.CENTER)
    footer(s, "Ch 51")


def partI_tpe():
    s = add_slide()
    slide_title(s, "TPE · model the good and bad regions separately")
    slide_subtitle(s, "Tree-structured Parzen Estimator — what Hyperopt uses by default")
    rrect(s, Inches(0.5), Inches(1.7), Inches(7.0), Inches(5.2),
          fill=PANEL, line=BLUE)
    textbox(s, Inches(0.7), Inches(1.85), Inches(6.6), Inches(0.4),
            "Split trials by score: top γ% (good)  vs  rest (bad)",
            size=13, bold=True, color=BLUE)
    # two density sketches on shared axis
    import math
    ox, oy = Inches(1.0), Inches(6.6)
    arrow(s, ox, oy, ox, Inches(2.4), color=MUTED)
    arrow(s, ox, oy, Inches(7.4), oy, color=MUTED)
    textbox(s, Inches(7.1), oy + Inches(0.05), Inches(1), Inches(0.3),
            "θ", size=12, color=MUTED, bold=True)
    # good density g(θ) — narrow peak around θ=0.6
    pts_g = []
    for i in range(80):
        t = i / 79
        g = math.exp(-((t - 0.6) ** 2) / 0.02) * 0.9
        px = ox + Inches(t * 6.0); py = oy - Inches(g * 3.5)
        pts_g.append((px, py))
    for i in range(len(pts_g) - 1):
        line(s, pts_g[i][0], pts_g[i][1],
             pts_g[i + 1][0], pts_g[i + 1][1], color=GREEN, weight=2.5)
    # bad density ℓ(θ) — broader
    pts_b = []
    for i in range(80):
        t = i / 79
        b = (math.exp(-((t - 0.25) ** 2) / 0.1)
             + 0.5 * math.exp(-((t - 0.9) ** 2) / 0.06)) * 0.65
        px = ox + Inches(t * 6.0); py = oy - Inches(b * 3.5)
        pts_b.append((px, py))
    for i in range(len(pts_b) - 1):
        line(s, pts_b[i][0], pts_b[i][1],
             pts_b[i + 1][0], pts_b[i + 1][1], color=RED, weight=2.5)
    # legend
    rect(s, Inches(1.0), Inches(2.2), Inches(0.4), Inches(0.1), fill=GREEN)
    textbox(s, Inches(1.5), Inches(2.1), Inches(2), Inches(0.3),
            "ℓ(θ) — good", size=11, color=GREEN)
    rect(s, Inches(3.5), Inches(2.2), Inches(0.4), Inches(0.1), fill=RED)
    textbox(s, Inches(4.0), Inches(2.1), Inches(2), Inches(0.3),
            "g(θ) — bad", size=11, color=RED)
    # right: maths panel
    rrect(s, Inches(7.85), Inches(1.7), Inches(5.0), Inches(5.2),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(8.05), Inches(1.85), Inches(4.6), Inches(0.4),
            "ACQUISITION", size=14, bold=True, color=ACCENT)
    textbox(s, Inches(8.05), Inches(2.4), Inches(4.6), Inches(4.5),
            ("EI(θ)  ∝  ℓ(θ) / g(θ)\n\n"
             "Pick θ that is:\n"
             "  • likely under \"good\" (ℓ high)\n"
             "  • unlikely under \"bad\" (g low)\n\n"
             "TPE is robust to mixed spaces\n"
             "(continuous + categorical),\n"
             "which is why Hyperopt uses it.\n\n"
             "Tradeoffs:\n"
             "• simple, scalable\n"
             "• less accurate uncertainty\n"
             "  than a GP"),
            size=12, color=LIGHT, font="Consolas")
    footer(s, "Ch 52")


def partI_hyperopt():
    s = add_slide()
    slide_title(s, "Hyperopt · fmin, hp.choice, SparkTrials")
    slide_subtitle(s, "Three things to know that hurt people who don't")
    cards = [
        ("hp.choice ≠ index",
         "fmin returns the chosen INDEX, not the value.\n\n"
         "best['solver'] = 2 — not 'lbfgs'.\n\n"
         "Use  space_eval(space, best)  to recover the value.",
         RED),
        ("SparkTrials parallelism",
         "Hyperopt runs trials sequentially by default.\n\n"
         "SparkTrials(parallelism=p)  runs p trials at once\n"
         "across the cluster — but more parallel = LESS\n"
         "history to inform the next trial.\n\n"
         "Rule of thumb: parallelism ≈ √max_evals.",
         YELLOW),
        ("MLflow autologging",
         "Each trial = one MLflow run.\n\n"
         "Pass an MLflow `mlflow.start_run()` parent run\n"
         "and Hyperopt nests children under it.\n\n"
         "Great for retro-analysis of the search.",
         GREEN),
    ]
    x = Inches(0.5); y = Inches(1.7); w = Inches(4.1); h = Inches(5.2)
    for title, body, c in cards:
        rrect(s, x, y, w, h, fill=PANEL, line=c)
        rect(s, x, y, w, Inches(0.55), fill=c)
        textbox(s, x, y, w, Inches(0.55), title, size=15, bold=True,
                color=BG if c == YELLOW else WHITE,
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        textbox(s, x + Inches(0.2), y + Inches(0.7), w - Inches(0.4),
                h - Inches(0.85), body, size=12, color=LIGHT)
        x += w + Inches(0.1)
    footer(s, "Ch 53")


def partI_optuna():
    s = add_slide()
    slide_title(s, "Optuna · samplers + pruners + multi-objective")
    slide_subtitle(s, "Newer than Hyperopt, with first-class pruning")
    headers = ["Capability", "Hyperopt", "Optuna"]
    rows = [
        ["Default sampler",
         "TPE",
         "TPE; also CMA-ES, NSGA-II"],
        ["Define-by-run search space",
         "No — declare upfront",
         "Yes — define inside the objective"],
        ["Pruners (early-stop bad trials)",
         "Limited",
         "Median, ASHA, Hyperband, Percentile"],
        ["Multi-objective",
         "No",
         "Yes — Pareto front out of the box"],
        ["Distributed",
         "SparkTrials",
         "RDB storage; Joblib / Dask integrations"],
        ["Visualisation",
         "Custom",
         "Built-in plotly dashboards"],
        ["Databricks integration",
         "First-class (mature)",
         "Works; MLflow callback available"],
    ]
    add_table(s, Inches(0.5), Inches(1.7), Inches(12.33), Inches(5.0),
              headers, rows, col_widths=[3, 5, 5], font_size=12,
              header_size=14)
    textbox(s, Inches(0.5), Inches(6.85), Inches(12.33), Inches(0.4),
            "Both ship working TPE. Optuna's pruners are the differentiator for expensive training loops.",
            size=12, color=ACCENT, bold=True, align=PP_ALIGN.CENTER)
    footer(s, "Ch 54")



# =======================================================================
# PART J — SPARK FROM ZERO
# =======================================================================

def partJ_why_distributed():
    s = add_slide()
    slide_title(s, "Why distributed compute?")
    slide_subtitle(s, "When a dataset doesn't fit one machine, you scale OUT")
    # left: vertical scaling
    rrect(s, Inches(0.5), Inches(1.7), Inches(6.0), Inches(5.2),
          fill=PANEL, line=BLUE)
    textbox(s, Inches(0.7), Inches(1.85), Inches(5.6), Inches(0.4),
            "SCALE UP  (bigger box)", size=14, bold=True, color=BLUE)
    cy = Inches(4.4)
    # single growing server
    for i, (w, h, lab) in enumerate([(1.0, 1.2, "16 GB"),
                                     (1.4, 1.6, "64 GB"),
                                     (1.9, 2.2, "256 GB")]):
        rect(s, Inches(0.9 + i * 1.7), cy - Inches(h), Inches(w),
             Inches(h), fill=BLUE)
        textbox(s, Inches(0.9 + i * 1.7), cy - Inches(h) + Inches(0.1),
                Inches(w), Inches(0.3),
                lab, size=11, color=WHITE, bold=True,
                align=PP_ALIGN.CENTER)
    textbox(s, Inches(0.7), Inches(5.3), Inches(5.6), Inches(1.5),
            ("• Hardware ceiling exists\n"
             "• Cost grows super-linearly\n"
             "• Single point of failure\n"
             "• Doesn't help if I/O bound"),
            size=13, color=LIGHT)
    # right: horizontal scaling
    rrect(s, Inches(6.85), Inches(1.7), Inches(6.0), Inches(5.2),
          fill=PANEL, line=GREEN)
    textbox(s, Inches(7.05), Inches(1.85), Inches(5.6), Inches(0.4),
            "SCALE OUT  (more boxes)", size=14, bold=True, color=GREEN)
    # cluster of machines
    for r in range(2):
        for c in range(5):
            x = Inches(7.2 + c * 1.05); y = Inches(3.0 + r * 1.4)
            rect(s, x, y, Inches(0.9), Inches(1.0), fill=GREEN)
            ellipse(s, x + Inches(0.15), y + Inches(0.2),
                    Inches(0.6), Inches(0.6), fill=BG)
            textbox(s, x + Inches(0.15), y + Inches(0.2),
                    Inches(0.6), Inches(0.6),
                    "CPU", size=8, color=GREEN, bold=True,
                    align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    textbox(s, Inches(7.05), Inches(5.85), Inches(5.6), Inches(1.0),
            ("• Linear capacity in nodes\n"
             "• Commodity hardware\n"
             "• Need a programming model\n"
             "  → Spark / MapReduce / etc."),
            size=13, color=LIGHT)
    footer(s, "Ch 55")


def partJ_mr_vs_spark():
    s = add_slide()
    slide_title(s, "MapReduce vs Spark · disk vs memory")
    slide_subtitle(s, "Same shuffle dance — but one stays in RAM between stages")
    # MR top row
    y = Inches(2.0); h = Inches(1.0)
    rrect(s, Inches(0.5), y, Inches(12.33), h, fill=PANEL, line=YELLOW)
    textbox(s, Inches(0.7), y + Inches(0.05), Inches(2), Inches(0.3),
            "MAPREDUCE", size=12, bold=True, color=YELLOW)
    # boxes: HDFS — MAP — HDFS — REDUCE — HDFS — MAP — HDFS …
    nodes = ["HDFS", "MAP", "HDFS", "REDUCE", "HDFS", "MAP", "HDFS"]
    bx = Inches(1.7); bw = Inches(1.45)
    for n in nodes:
        rect(s, bx, y + Inches(0.4), bw, Inches(0.45),
             fill=YELLOW if n == "HDFS" else PANEL,
             line=YELLOW if n != "HDFS" else None)
        textbox(s, bx, y + Inches(0.4), bw, Inches(0.45), n,
                size=11, bold=True,
                color=BG if n == "HDFS" else LIGHT,
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        bx += bw + Inches(0.05)
    textbox(s, Inches(0.5), Inches(3.15), Inches(12.33), Inches(0.4),
            "Each intermediate result hits disk → I/O dominates.",
            size=12, color=MUTED)
    # Spark
    y2 = Inches(4.0)
    rrect(s, Inches(0.5), y2, Inches(12.33), h, fill=PANEL, line=GREEN)
    textbox(s, Inches(0.7), y2 + Inches(0.05), Inches(2), Inches(0.3),
            "SPARK", size=12, bold=True, color=GREEN)
    nodes2 = ["HDFS", "RDD", "RDD", "RDD", "RDD", "RDD", "HDFS"]
    bx = Inches(1.7); bw = Inches(1.45)
    for n in nodes2:
        rect(s, bx, y2 + Inches(0.4), bw, Inches(0.45),
             fill=GREEN if n == "HDFS" else PANEL,
             line=GREEN if n != "HDFS" else None)
        textbox(s, bx, y2 + Inches(0.4), bw, Inches(0.45), n,
                size=11, bold=True,
                color=BG if n == "HDFS" else LIGHT,
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        bx += bw + Inches(0.05)
    textbox(s, Inches(0.5), Inches(5.15), Inches(12.33), Inches(0.4),
            "Intermediate state in memory → 10-100× faster for iterative ML / graph workloads.",
            size=12, color=MUTED)
    # caveat
    rrect(s, Inches(0.5), Inches(5.8), Inches(12.33), Inches(1.2),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(0.5), Inches(5.8), Inches(12.33), Inches(1.2),
            ("Spark IS slower than MR if every dataset is read once and never reused.\n"
             "It wins when intermediate state would otherwise re-touch disk."),
            size=13, color=LIGHT, align=PP_ALIGN.CENTER,
            anchor=MSO_ANCHOR.MIDDLE)
    footer(s, "Ch 55")


def partJ_architecture():
    s = add_slide()
    slide_title(s, "Spark architecture · driver, executors, cluster manager")
    slide_subtitle(s, "Who decides what, who does the work, and who books the rooms")
    # driver
    rrect(s, Inches(0.5), Inches(2.0), Inches(3.5), Inches(2.5),
          fill=ACCENT)
    textbox(s, Inches(0.5), Inches(2.05), Inches(3.5), Inches(0.5),
            "DRIVER", size=18, bold=True, color=WHITE,
            align=PP_ALIGN.CENTER)
    textbox(s, Inches(0.7), Inches(2.6), Inches(3.1), Inches(1.8),
            ("• Holds SparkContext\n"
             "• Builds DAG, plans stages\n"
             "• Schedules tasks\n"
             "• Collects results"),
            size=12, color=WHITE)
    # cluster manager
    rrect(s, Inches(4.8), Inches(2.0), Inches(3.5), Inches(2.5),
          fill=YELLOW)
    textbox(s, Inches(4.8), Inches(2.05), Inches(3.5), Inches(0.5),
            "CLUSTER MANAGER", size=18, bold=True, color=BG,
            align=PP_ALIGN.CENTER)
    textbox(s, Inches(5.0), Inches(2.6), Inches(3.1), Inches(1.8),
            ("• YARN / k8s / standalone\n"
             "• Allocates executors\n"
             "• Tracks resources\n"
             "• Restarts failed nodes"),
            size=12, color=BG)
    # executors
    rrect(s, Inches(9.1), Inches(2.0), Inches(3.7), Inches(2.5),
          fill=GREEN)
    textbox(s, Inches(9.1), Inches(2.05), Inches(3.7), Inches(0.5),
            "EXECUTORS  (N)", size=18, bold=True, color=WHITE,
            align=PP_ALIGN.CENTER)
    textbox(s, Inches(9.3), Inches(2.6), Inches(3.3), Inches(1.8),
            ("• Run tasks (CPU cores)\n"
             "• Hold partitions in memory\n"
             "• Cache RDD / DF data\n"
             "• Report status to driver"),
            size=12, color=WHITE)
    # arrows
    arrow(s, Inches(4.0), Inches(3.0), Inches(4.8), Inches(3.0), color=WHITE)
    arrow(s, Inches(4.8), Inches(3.5), Inches(4.0), Inches(3.5), color=WHITE)
    arrow(s, Inches(8.3), Inches(3.0), Inches(9.1), Inches(3.0), color=WHITE)
    arrow(s, Inches(9.1), Inches(3.5), Inches(8.3), Inches(3.5), color=WHITE)
    textbox(s, Inches(4.0), Inches(2.6), Inches(0.8), Inches(0.3),
            "ask", size=10, color=WHITE)
    textbox(s, Inches(4.0), Inches(3.6), Inches(0.8), Inches(0.3),
            "grant", size=10, color=WHITE)
    textbox(s, Inches(8.3), Inches(2.6), Inches(0.8), Inches(0.3),
            "tasks", size=10, color=WHITE)
    textbox(s, Inches(8.3), Inches(3.6), Inches(0.8), Inches(0.3),
            "status", size=10, color=WHITE)
    # bottom callout
    rrect(s, Inches(0.5), Inches(5.0), Inches(12.33), Inches(1.5),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(0.7), Inches(5.1), Inches(11.9), Inches(1.4),
            ("On Databricks the cluster manager is hidden behind the cluster "
             "UI; you choose driver size + worker count + Photon, and the "
             "platform talks to the underlying VM service for you.\n\n"
             "Two cluster modes worth knowing: shared-access (UC-secured, "
             "multi-user) and single-user (full Spark surface, your own pipeline)."),
            size=13, color=LIGHT)
    footer(s, "Ch 56")


def partJ_rdd_df_dataset():
    s = add_slide()
    slide_title(s, "RDD → DataFrame → Dataset · evolution of abstractions")
    slide_subtitle(s, "Each generation traded freedom for performance")
    headers = ["", "RDD", "DataFrame", "Dataset"]
    rows = [
        ["Available since",
         "Spark 0.x",
         "Spark 1.3",
         "Spark 1.6 (Scala/Java only)"],
        ["Schema",
         "None — opaque objects",
         "Yes — named columns",
         "Yes + compile-time types"],
        ["Catalyst optimisation",
         "No",
         "Yes",
         "Yes"],
        ["Tungsten encoding",
         "No",
         "Yes",
         "Yes"],
        ["Type safety",
         "Compile-time",
         "Runtime",
         "Compile-time"],
        ["Best for",
         "Unstructured, custom ops",
         "SQL / DataFrame ops (default)",
         "Typed Scala / Java"],
        ["PySpark default",
         "Available (legacy)",
         "Yes — what you'll use",
         "N/A (no Python types)"],
    ]
    add_table(s, Inches(0.5), Inches(1.7), Inches(12.33), Inches(5.0),
              headers, rows, col_widths=[2.8, 3.2, 3.2, 3.2],
              font_size=12, header_size=13)
    textbox(s, Inches(0.5), Inches(6.8), Inches(12.33), Inches(0.4),
            "Rule of thumb: use DataFrames. Drop to RDD only when you must (custom partitioning, opaque blobs).",
            size=12, color=ACCENT, bold=True, align=PP_ALIGN.CENTER)
    footer(s, "Ch 57")


def partJ_catalyst():
    s = add_slide()
    slide_title(s, "Catalyst optimiser · four phases")
    slide_subtitle(s, "How a `df.filter().groupBy().agg()` call becomes JVM bytecode")
    phases = [
        ("Analysis",
         "Parse SQL / DF ops.\nResolve column names against schema.\nProduce logical plan."),
        ("Logical opt.",
         "Rewrite plan with rules:\npredicate pushdown,\nconstant folding,\nprojection pruning."),
        ("Physical plan",
         "Pick concrete operators:\nSortMergeJoin vs BroadcastHashJoin.\nCost-based choices."),
        ("Code gen",
         "Tungsten WSCG bytecode.\nCompiles whole stages into\nsingle inlined loops."),
    ]
    y = Inches(2.5); h = Inches(3.0); w = Inches(2.95)
    x = Inches(0.5)
    for i, (t, body) in enumerate(phases):
        rrect(s, x, y, w, h, fill=PANEL, line=ACCENT)
        ellipse(s, x + w/2 - Inches(0.25), y - Inches(0.25),
                Inches(0.5), Inches(0.5), fill=ACCENT)
        textbox(s, x + w/2 - Inches(0.25), y - Inches(0.25),
                Inches(0.5), Inches(0.5), str(i + 1),
                size=14, bold=True, color=WHITE,
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        textbox(s, x, y + Inches(0.25), w, Inches(0.5), t,
                size=15, bold=True, color=WHITE,
                align=PP_ALIGN.CENTER)
        textbox(s, x + Inches(0.2), y + Inches(0.9), w - Inches(0.4),
                Inches(2.0), body, size=12, color=LIGHT)
        if i < 3:
            arrow(s, x + w, y + Inches(1.5),
                  x + w + Inches(0.1), y + Inches(1.5))
        x += w + Inches(0.1)
    textbox(s, Inches(0.5), Inches(5.8), Inches(12.33), Inches(0.5),
            "df.explain(True)  shows you all four plans.   The physical plan is what actually runs.",
            size=13, color=ACCENT, bold=True, align=PP_ALIGN.CENTER,
            font="Consolas")
    footer(s, "Ch 58")


def partJ_narrow_wide():
    s = add_slide()
    slide_title(s, "Narrow vs wide transformations")
    slide_subtitle(s, "Wide ⇒ shuffle ⇒ stage boundary ⇒ network I/O")
    headers = ["Type", "Examples", "Partition mapping", "Shuffle?"]
    rows = [
        ["Narrow",
         "select, filter, map, withColumn, union",
         "1 parent partition → 1 child partition",
         "No"],
        ["Narrow",
         "coalesce(n)  (when reducing only)",
         "Merges adjacent partitions in place",
         "No"],
        ["Wide",
         "groupBy, agg, distinct, dropDuplicates",
         "Many → many; hash-shuffle by key",
         "Yes"],
        ["Wide",
         "join (sort-merge)",
         "Co-locate keys on both sides",
         "Yes"],
        ["Wide",
         "join (broadcast)",
         "Small side replicated; large side stays",
         "Broadcast only"],
        ["Wide",
         "repartition(n) / repartition('col')",
         "Reshuffle to n partitions",
         "Yes"],
        ["Wide",
         "orderBy / sortByKey",
         "Range partition then local sort",
         "Yes"],
    ]
    add_table(s, Inches(0.5), Inches(1.7), Inches(12.33), Inches(5.2),
              headers, rows, col_widths=[1.5, 4.5, 4.5, 1.5],
              font_size=12, header_size=13)
    textbox(s, Inches(0.5), Inches(6.95), Inches(12.33), Inches(0.4),
            "Stages = chains of narrow ops; wide ops are the boundaries.",
            size=12, color=ACCENT, bold=True, align=PP_ALIGN.CENTER)
    footer(s, "Ch 59")


def partJ_shuffle_anatomy():
    s = add_slide()
    slide_title(s, "Shuffle anatomy · three phases")
    slide_subtitle(s, "Map-side write → network transfer → reduce-side read")
    # diagram
    # mappers
    for i in range(4):
        rrect(s, Inches(0.5), Inches(1.9 + i * 0.9), Inches(2.0), Inches(0.7),
              fill=BLUE)
        textbox(s, Inches(0.5), Inches(1.9 + i * 0.9), Inches(2.0),
                Inches(0.7), f"Mapper {i + 1}", size=12, bold=True, color=WHITE,
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    # reducers
    for i in range(3):
        rrect(s, Inches(10.8), Inches(2.3 + i * 1.1), Inches(2.0), Inches(0.8),
              fill=GREEN)
        textbox(s, Inches(10.8), Inches(2.3 + i * 1.1), Inches(2.0),
                Inches(0.8), f"Reducer {i + 1}", size=12, bold=True,
                color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    # middle: shuffle box
    rrect(s, Inches(3.2), Inches(2.5), Inches(7.0), Inches(2.8),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(3.3), Inches(2.55), Inches(6.8), Inches(0.4),
            "SHUFFLE",
            size=14, bold=True, color=ACCENT, align=PP_ALIGN.CENTER)
    # arrows from each mapper to each reducer
    for i in range(4):
        for j in range(3):
            line(s, Inches(2.5), Inches(2.25 + i * 0.9),
                 Inches(10.8), Inches(2.7 + j * 1.1),
                 color=GREY, weight=0.6)
    # phase labels
    textbox(s, Inches(3.3), Inches(3.2), Inches(6.8), Inches(0.4),
            "1.  WRITE — partition by key, spill to disk", size=12,
            color=LIGHT, bold=True)
    textbox(s, Inches(3.3), Inches(3.7), Inches(6.8), Inches(0.4),
            "2.  TRANSFER — network fetch from all mappers", size=12,
            color=LIGHT, bold=True)
    textbox(s, Inches(3.3), Inches(4.2), Inches(6.8), Inches(0.4),
            "3.  READ — merge, sort, build new partition", size=12,
            color=LIGHT, bold=True)
    # cost callout
    rrect(s, Inches(0.5), Inches(5.7), Inches(12.33), Inches(1.3),
          fill=PANEL, line=RED)
    textbox(s, Inches(0.7), Inches(5.8), Inches(11.9), Inches(0.4),
            "WHY YOU CARE", size=12, color=RED, bold=True)
    textbox(s, Inches(0.7), Inches(6.15), Inches(11.9), Inches(0.8),
            ("Shuffles burn CPU, disk, and network — they are the single "
             "biggest cause of slow Spark jobs.\n"
             "Mitigate: broadcast-join small tables; pre-partition by join "
             "key; tune shuffle partitions; use AQE."),
            size=13, color=LIGHT)
    footer(s, "Ch 60")


def partJ_aqe():
    s = add_slide()
    slide_title(s, "AQE · adaptive query execution")
    slide_subtitle(s, "Replan stages at runtime using observed statistics")
    # before
    rrect(s, Inches(0.5), Inches(1.7), Inches(6.0), Inches(5.2),
          fill=PANEL, line=BLUE)
    textbox(s, Inches(0.7), Inches(1.85), Inches(5.6), Inches(0.4),
            "WITHOUT AQE", size=14, bold=True, color=BLUE)
    textbox(s, Inches(0.7), Inches(2.3), Inches(5.6), Inches(4.5),
            ("Planner picks operators using estimated\n"
             "row counts and stats at compile time.\n\n"
             "If a join key has skew, one task gets\n"
             "all the data → the whole stage hangs.\n\n"
             "If a small table grows past a threshold,\n"
             "BroadcastHashJoin still tries — OOM.\n\n"
             "200 shuffle partitions on a 5MB result\n"
             "= 199 wasted tasks."),
            size=13, color=LIGHT)
    # with AQE
    rrect(s, Inches(6.85), Inches(1.7), Inches(6.0), Inches(5.2),
          fill=PANEL, line=GREEN)
    textbox(s, Inches(7.05), Inches(1.85), Inches(5.6), Inches(0.4),
            "WITH AQE  (default since DBR 7.3)",
            size=14, bold=True, color=GREEN)
    textbox(s, Inches(7.05), Inches(2.3), Inches(5.6), Inches(4.5),
            ("After each stage, real stats flow back\n"
             "to the planner. Three rewrites:\n\n"
             "• Dynamically COALESCE small shuffle\n"
             "  partitions → fewer wasted tasks.\n\n"
             "• Switch SortMergeJoin → Broadcast if\n"
             "  one side ends up small enough.\n\n"
             "• Detect and split SKEWED partitions\n"
             "  into smaller balanced ones.\n\n"
             "spark.sql.adaptive.enabled = true"),
            size=13, color=LIGHT)
    footer(s, "Ch 61")



# =======================================================================
# PART K — PYSPARK.ML
# =======================================================================

def partK_pipeline_pattern():
    s = add_slide()
    slide_title(s, "Pipeline pattern · Transformer + Estimator")
    slide_subtitle(s, "Two interfaces. Everything in pyspark.ml is one or the other.")
    # left: definitions
    rrect(s, Inches(0.5), Inches(1.7), Inches(6.0), Inches(2.4),
          fill=PANEL, line=BLUE)
    textbox(s, Inches(0.7), Inches(1.85), Inches(5.6), Inches(0.4),
            "TRANSFORMER", size=14, bold=True, color=BLUE)
    textbox(s, Inches(0.7), Inches(2.3), Inches(5.6), Inches(1.8),
            ("DataFrame → DataFrame\n\n"
             ".transform(df) is the only method.\n\n"
             "Examples:  VectorAssembler, Bucketizer,\n"
             "Tokenizer, StringIndexerModel, a fitted\n"
             "LogisticRegressionModel."),
            size=12, color=LIGHT, font="Consolas")
    rrect(s, Inches(0.5), Inches(4.25), Inches(6.0), Inches(2.65),
          fill=PANEL, line=GREEN)
    textbox(s, Inches(0.7), Inches(4.4), Inches(5.6), Inches(0.4),
            "ESTIMATOR", size=14, bold=True, color=GREEN)
    textbox(s, Inches(0.7), Inches(4.8), Inches(5.6), Inches(2.0),
            ("DataFrame → Transformer\n\n"
             ".fit(df) returns a fitted Model\n"
             "(which IS a Transformer).\n\n"
             "Examples:  StringIndexer, StandardScaler\n"
             "before fit, LogisticRegression, RandomForest,\n"
             "any *.fit() call."),
            size=12, color=LIGHT, font="Consolas")
    # right: pipeline diagram
    rrect(s, Inches(6.85), Inches(1.7), Inches(6.0), Inches(5.2),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(7.05), Inches(1.85), Inches(5.6), Inches(0.4),
            "PIPELINE = chained stages", size=14, bold=True, color=ACCENT)
    # mini pipeline boxes
    stages = ["Indexer", "Encoder", "Assembler", "Scaler", "LR"]
    y = Inches(2.6); x = Inches(7.05); h = Inches(0.5); w = Inches(5.6)
    for stg in stages:
        rrect(s, x, y, w, h, fill=PANEL, line=GREEN)
        textbox(s, x + Inches(0.2), y, Inches(2.5), h,
                stg, size=12, color=LIGHT, bold=True, anchor=MSO_ANCHOR.MIDDLE)
        textbox(s, x + Inches(3.5), y, Inches(1.8), h,
                "Estimator", size=10, color=GREEN,
                anchor=MSO_ANCHOR.MIDDLE)
        y += Inches(0.6)
    textbox(s, Inches(7.05), Inches(5.8), Inches(5.6), Inches(1.2),
            ("Pipeline.fit(train) walks the stages:\n"
             "fit each estimator on the data so far, transform\n"
             "before passing on.   Output = PipelineModel."),
            size=12, color=LIGHT, font="Consolas")
    footer(s, "Ch 62")


def partK_transformers_table():
    s = add_slide()
    slide_title(s, "Common transformers · what each computes")
    slide_subtitle(s, "The ones the exam tests, the ones you'll use every day")
    headers = ["Transformer", "Type", "What it does", "Where it shows up"]
    rows = [
        ["VectorAssembler",
         "Transformer",
         "Combine columns → single 'features' vector",
         "Always — Spark ML needs vectors"],
        ["StringIndexer",
         "Estimator",
         "Categorical strings → 0…k-1 indices",
         "Pre-OHE or as labels"],
        ["OneHotEncoder",
         "Estimator",
         "Indices → sparse one-hot vectors",
         "Categorical features"],
        ["StandardScaler",
         "Estimator",
         "Centre & scale columns to unit variance",
         "Distance/coef models"],
        ["MinMaxScaler",
         "Estimator",
         "Rescale to [min, max]",
         "Bounded inputs"],
        ["Bucketizer",
         "Transformer",
         "Continuous → bins via splits",
         "Discretise before tree / OHE"],
        ["QuantileDiscretizer",
         "Estimator",
         "Bins by quantiles (learned)",
         "Robust binning"],
        ["Imputer",
         "Estimator",
         "Fill nulls with mean / median",
         "Tabular pipelines"],
        ["Tokenizer / RegexTokenizer",
         "Transformer",
         "String → array of tokens",
         "Text features"],
    ]
    add_table(s, Inches(0.5), Inches(1.7), Inches(12.33), Inches(5.3),
              headers, rows, col_widths=[3.5, 2, 5, 4],
              font_size=12, header_size=13)
    footer(s, "Ch 63")


def partK_cv_model_count():
    s = add_slide()
    slide_title(s, "CrossValidator · the G × F + 1 model count")
    slide_subtitle(s, "Why a 'small' grid blows up your training time")
    rrect(s, Inches(0.5), Inches(1.7), Inches(12.33), Inches(1.5),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(0.5), Inches(1.7), Inches(12.33), Inches(1.5),
            "Models fit  =  G × F  +  1",
            size=30, bold=True, color=WHITE, font="Consolas",
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    # worked example
    rrect(s, Inches(0.5), Inches(3.4), Inches(6.0), Inches(3.6),
          fill=PANEL, line=BLUE)
    textbox(s, Inches(0.7), Inches(3.5), Inches(5.6), Inches(0.4),
            "WORKED EXAMPLE", size=13, color=BLUE, bold=True)
    textbox(s, Inches(0.7), Inches(3.95), Inches(5.6), Inches(3.0),
            ("ParamGrid:\n"
             "  regParam ∈ {0.01, 0.1, 1.0}    (3)\n"
             "  elasticNetParam ∈ {0.0, 0.5}    (2)\n"
             "  maxIter ∈ {50, 100, 200}        (3)\n\n"
             "G = 3 × 2 × 3 = 18 combinations\n"
             "F = 5  (5-fold CV)\n\n"
             "Models fit = 18 × 5 + 1 = 91"),
            size=13, color=LIGHT, font="Consolas")
    # right: what the +1 is
    rrect(s, Inches(6.85), Inches(3.4), Inches(6.0), Inches(3.6),
          fill=PANEL, line=GREEN)
    textbox(s, Inches(7.05), Inches(3.5), Inches(5.6), Inches(0.4),
            "WHY THE \"+ 1\"", size=13, color=GREEN, bold=True)
    textbox(s, Inches(7.05), Inches(3.95), Inches(5.6), Inches(3.0),
            ("• G × F fits compute the CV score for\n"
             "  every grid combination.\n\n"
             "• The best combination is then refit\n"
             "  ONCE on the FULL training set.\n\n"
             "• That final model is what\n"
             "  cvModel.bestModel returns.\n\n"
             "Set collectSubModels=True to keep all\n"
             "fold-level fits (memory cost!)."),
            size=13, color=LIGHT)
    footer(s, "Ch 64")


def partK_evaluators():
    s = add_slide()
    slide_title(s, "Evaluators · pick the metric, hand it to CV / TVS")
    slide_subtitle(s, "One evaluator class per task type")
    headers = ["Evaluator", "Use for", "metricName options"]
    rows = [
        ["BinaryClassificationEvaluator",
         "2-class classification",
         "areaUnderROC (default), areaUnderPR"],
        ["MulticlassClassificationEvaluator",
         ">2 class classification",
         "f1 (default), accuracy, weightedPrecision, weightedRecall, logLoss"],
        ["MultilabelClassificationEvaluator",
         "Multi-label problems",
         "hammingLoss, precision, recall, f1Measure"],
        ["RegressionEvaluator",
         "Regression",
         "rmse (default), mse, mae, r2, var"],
        ["RankingEvaluator",
         "Recommendation ranking",
         "meanAveragePrecision, ndcgAtK, precisionAtK"],
        ["ClusteringEvaluator",
         "Unsupervised clustering",
         "silhouette (default), squared Euclidean / cosine variants"],
    ]
    add_table(s, Inches(0.5), Inches(1.7), Inches(12.33), Inches(5.0),
              headers, rows, col_widths=[4, 3.5, 7],
              font_size=12, header_size=13)
    textbox(s, Inches(0.5), Inches(6.8), Inches(12.33), Inches(0.4),
            "CV / TVS minimise loss by maximising the evaluator score — sign handled internally.",
            size=12, color=ACCENT, bold=True, align=PP_ALIGN.CENTER)
    footer(s, "Ch 65")


def partK_persistence():
    s = add_slide()
    slide_title(s, "Pipeline persistence · save once, load anywhere")
    slide_subtitle(s, "The whole pipeline (every stage) round-trips")
    # save flow
    boxes_top = [
        ("PipelineModel\n(fitted)", ACCENT),
        (".write().overwrite()\n.save(path)", PANEL),
        ("metadata + parquet\nstages/*", BLUE),
    ]
    x = Inches(0.5); y = Inches(2.3); w = Inches(3.8); h = Inches(1.4)
    for label, c in boxes_top:
        rrect(s, x, y, w, h, fill=c if c == ACCENT else PANEL,
              line=None if c == ACCENT else c if c == BLUE else BLUE)
        textbox(s, x, y, w, h, label,
                size=14, bold=True, color=WHITE,
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE,
                font="Consolas")
        x += w + Inches(0.2)
    arrow(s, Inches(4.3), Inches(3.0), Inches(4.5), Inches(3.0))
    arrow(s, Inches(8.3), Inches(3.0), Inches(8.5), Inches(3.0))
    # load flow
    boxes_bot = [
        ("Path on DBFS / UC\nVolume", BLUE),
        ("PipelineModel.load(path)", PANEL),
        (".transform(new_df)", GREEN),
    ]
    x = Inches(0.5); y = Inches(4.5)
    for label, c in boxes_bot:
        rrect(s, x, y, w, h, fill=c if c in (GREEN,) else PANEL,
              line=None if c == GREEN else c)
        textbox(s, x, y, w, h, label,
                size=14, bold=True, color=WHITE,
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE,
                font="Consolas")
        x += w + Inches(0.2)
    arrow(s, Inches(4.3), Inches(5.2), Inches(4.5), Inches(5.2))
    arrow(s, Inches(8.3), Inches(5.2), Inches(8.5), Inches(5.2))
    # callout
    rrect(s, Inches(0.5), Inches(6.2), Inches(12.33), Inches(0.85),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(0.5), Inches(6.2), Inches(12.33), Inches(0.85),
            ("Always overwrite() in re-runnable jobs.  Custom Python stages must subclass DefaultParamsWritable to round-trip."),
            size=13, color=LIGHT, align=PP_ALIGN.CENTER,
            anchor=MSO_ANCHOR.MIDDLE)
    footer(s, "Ch 67")


def partK_pandas_udf():
    s = add_slide()
    slide_title(s, "When pyspark.ml isn't enough · pandas UDFs")
    slide_subtitle(s, "Bring scikit-learn / XGBoost into Spark with Arrow")
    headers = ["Pattern", "Decorator", "Input / Output", "Use for"]
    rows = [
        ["Series → Series",
         "@pandas_udf(returnType)",
         "pd.Series → pd.Series",
         "Row-wise scalar transforms (vectorised)"],
        ["Iterator of Series",
         "@pandas_udf(returnType)\nIterator[pd.Series] → Iterator[pd.Series]",
         "Stream of batches",
         "Heavy init once per executor (load model once)"],
        ["GroupedMap",
         "df.groupBy(k).applyInPandas(fn, schema)",
         "pd.DataFrame → pd.DataFrame",
         "Train a model PER GROUP (per store, per SKU)"],
        ["mapInPandas",
         "df.mapInPandas(fn, schema)",
         "Iterator[pd.DataFrame] → Iterator[pd.DataFrame]",
         "Batched inference with sklearn / XGB / TF"],
    ]
    add_table(s, Inches(0.5), Inches(1.7), Inches(12.33), Inches(4.6),
              headers, rows, col_widths=[2.5, 4.5, 4.5, 3.5],
              font_size=11, header_size=13)
    textbox(s, Inches(0.5), Inches(6.5), Inches(12.33), Inches(0.5),
            "Arrow handles the JVM ↔ Python serialisation; you operate on familiar pandas inside the UDF.",
            size=13, color=ACCENT, bold=True, align=PP_ALIGN.CENTER)
    footer(s, "Ch 66-67")



# =======================================================================
# PART L — DATABRICKS PLATFORM & MLFLOW
# =======================================================================

def partL_workspace_anatomy():
    s = add_slide()
    slide_title(s, "Workspace anatomy · the objects you'll touch every day")
    slide_subtitle(s, "Notebook, cluster, job, model, catalog — each has its own home")
    objs = [
        ("Notebook",
         "Code + markdown + results.\nMulti-language (PY/SQL/R/SCALA).",
         BLUE),
        ("Cluster",
         "Driver + workers + DBR.\nAll-purpose vs job vs SQL warehouse.",
         GREEN),
        ("Job",
         "Scheduled / triggered runs.\nTasks form a DAG with retries.",
         YELLOW),
        ("Repo",
         "Git-synced notebook folder.\nCommit, pull, branch in-place.",
         PURPLE),
        ("Model",
         "MLflow registered model under UC\n(catalog.schema.model_name).",
         ACCENT),
        ("Catalog",
         "Top of UC namespace —\ncatalog.schema.table | volume | function.",
         RED),
    ]
    cols = 3; rows = 2
    w = Inches(4.1); h = Inches(2.4)
    for idx, (title, body, c) in enumerate(objs):
        r = idx // cols; col = idx % cols
        x = Inches(0.5 + col * (4.1 + 0.1))
        y = Inches(1.8 + r * (2.4 + 0.2))
        rrect(s, x, y, w, h, fill=PANEL, line=c)
        rect(s, x, y, w, Inches(0.5), fill=c)
        textbox(s, x, y, w, Inches(0.5), title,
                size=15, bold=True, color=BG if c in (YELLOW,) else WHITE,
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        textbox(s, x + Inches(0.2), y + Inches(0.65), w - Inches(0.4),
                h - Inches(0.8), body, size=12, color=LIGHT)
    footer(s, "Ch 68")


def partL_dbr_ml_runtime():
    s = add_slide()
    slide_title(s, "DBR ML runtime · what comes pre-installed")
    slide_subtitle(s, "Pick the runtime → libraries + drivers + Photon are picked for you")
    headers = ["Category", "Pre-installed (ML runtime)", "Notes"]
    rows = [
        ["Core Spark",
         "Apache Spark + Photon (vectorised engine)",
         "Photon enabled per cluster"],
        ["ML libs",
         "scikit-learn, XGBoost, LightGBM, statsmodels, MLflow",
         "Version pinned per DBR ML"],
        ["DL libs",
         "PyTorch, TensorFlow, Keras, transformers (DBR ML)",
         "GPU variant has CUDA + cuDNN matched"],
        ["HPO",
         "Hyperopt with SparkTrials, Optuna",
         "MLflow autolog integration"],
        ["Feature store",
         "databricks-feature-engineering",
         "UC-native point-in-time joins"],
        ["AutoML",
         "databricks.automl",
         "Glass-box notebooks generated per trial"],
        ["GPU drivers",
         "CUDA, cuDNN, NCCL bundled in GPU variant",
         "No manual setup needed"],
    ]
    add_table(s, Inches(0.5), Inches(1.7), Inches(12.33), Inches(5.0),
              headers, rows, col_widths=[2.5, 6, 4.5],
              font_size=12, header_size=13)
    textbox(s, Inches(0.5), Inches(6.8), Inches(12.33), Inches(0.4),
            "Avoid pip-installing things the runtime already provides — version drift is the #1 \"works on my notebook\" cause.",
            size=12, color=ACCENT, bold=True, align=PP_ALIGN.CENTER)
    footer(s, "Ch 68")


def partL_unity_catalog():
    s = add_slide()
    slide_title(s, "Unity Catalog · three-level namespace + permission chain")
    slide_subtitle(s, "catalog.schema.object  — replaces hive_metastore for new work")
    rrect(s, Inches(0.5), Inches(1.7), Inches(12.33), Inches(1.0),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(0.5), Inches(1.7), Inches(12.33), Inches(1.0),
            "catalog  .  schema  .  object",
            size=32, bold=True, color=WHITE, font="Consolas",
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    # tree levels
    levels = [
        ("METASTORE",
         "One per region\n(account-level)",
         ACCENT),
        ("CATALOG",
         "Top-level grouping\n(e.g. prod, dev, ml)",
         BLUE),
        ("SCHEMA / DB",
         "Logical grouping\n(e.g. lending, telemetry)",
         GREEN),
        ("OBJECT",
         "Table · View · Volume\n· Function · Model",
         YELLOW),
    ]
    y = Inches(3.1); w = Inches(2.95); h = Inches(2.5); x = Inches(0.5)
    for title, body, c in levels:
        rrect(s, x, y, w, h, fill=PANEL, line=c)
        rect(s, x, y, w, Inches(0.5), fill=c)
        textbox(s, x, y, w, Inches(0.5), title,
                size=14, bold=True,
                color=BG if c == YELLOW else WHITE,
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        textbox(s, x, y + Inches(0.65), w, Inches(1.7),
                body, size=12, color=LIGHT, align=PP_ALIGN.CENTER)
        x += w + Inches(0.1)
    rrect(s, Inches(0.5), Inches(5.8), Inches(12.33), Inches(1.2),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(0.7), Inches(5.9), Inches(11.9), Inches(0.4),
            "PERMISSION CHAIN  (you need each link)", size=12,
            color=ACCENT, bold=True)
    textbox(s, Inches(0.7), Inches(6.25), Inches(11.9), Inches(0.7),
            ("USE CATALOG  →  USE SCHEMA  →  SELECT (or other privilege) on the object."
             "  Grants inherit downwards but READ on a table requires SELECT, not just USE."),
            size=13, color=LIGHT, font="Consolas")
    footer(s, "Ch 70")


def partL_feature_store_pit():
    s = add_slide()
    slide_title(s, "Feature Engineering in UC · point-in-time joins")
    slide_subtitle(s, "Avoid future leakage when stitching features to labels")
    # left: bad
    rrect(s, Inches(0.5), Inches(1.7), Inches(6.0), Inches(5.2),
          fill=PANEL, line=RED)
    textbox(s, Inches(0.7), Inches(1.85), Inches(5.6), Inches(0.4),
            "NAIVE  (leaky)", size=14, bold=True, color=RED)
    textbox(s, Inches(0.7), Inches(2.3), Inches(5.6), Inches(2.5),
            ("Label rows:  user=42, label_time=Jan-15\n\n"
             "Feature table has:\n"
             "  Jan-10  → balance=100\n"
             "  Jan-20  → balance=200\n\n"
             "Join on user only  → could pull Jan-20\n"
             "(value FROM THE FUTURE) into the training\n"
             "row dated Jan-15.   Train accuracy: great.\n"
             "Production accuracy: collapses."),
            size=12, color=LIGHT, font="Consolas")
    # right: good
    rrect(s, Inches(6.85), Inches(1.7), Inches(6.0), Inches(5.2),
          fill=PANEL, line=GREEN)
    textbox(s, Inches(7.05), Inches(1.85), Inches(5.6), Inches(0.4),
            "POINT-IN-TIME  (correct)", size=14, bold=True, color=GREEN)
    textbox(s, Inches(7.05), Inches(2.3), Inches(5.6), Inches(4.2),
            ("FeatureLookup(\n"
             "  table_name='lending.user_features',\n"
             "  lookup_key='user_id',\n"
             "  timestamp_lookup_key='event_time')\n\n"
             "Join logic:  pick the LATEST feature row\n"
             "with feature_ts ≤ label_ts.\n\n"
             "Now Jan-15 label sees only Jan-10 balance.\n\n"
             "Same lookup logic is used at SERVING time\n"
             "via the online store — no training-serving\n"
             "skew."),
            size=12, color=LIGHT, font="Consolas")
    footer(s, "Ch 71")


def partL_mlflow_anatomy():
    s = add_slide()
    slide_title(s, "MLflow · experiment → run → params / metrics / artifacts")
    slide_subtitle(s, "Four primitives, the rest is convenience")
    # tree
    rrect(s, Inches(0.5), Inches(2.0), Inches(2.8), Inches(0.7),
          fill=ACCENT)
    textbox(s, Inches(0.5), Inches(2.0), Inches(2.8), Inches(0.7),
            "EXPERIMENT", size=15, bold=True, color=WHITE,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    arrow(s, Inches(1.9), Inches(2.7), Inches(1.9), Inches(3.1))
    rrect(s, Inches(0.5), Inches(3.1), Inches(2.8), Inches(0.7),
          fill=BLUE)
    textbox(s, Inches(0.5), Inches(3.1), Inches(2.8), Inches(0.7),
            "RUN", size=15, bold=True, color=WHITE,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    # children
    arrow(s, Inches(3.3), Inches(3.45), Inches(4.0), Inches(2.4))
    arrow(s, Inches(3.3), Inches(3.45), Inches(4.0), Inches(3.45))
    arrow(s, Inches(3.3), Inches(3.45), Inches(4.0), Inches(4.5))
    arrow(s, Inches(3.3), Inches(3.45), Inches(4.0), Inches(5.55))
    children = [
        ("PARAMS",  "log_param('lr', 0.01)\nimmutable keys → strings"),
        ("METRICS", "log_metric('rmse', 0.12, step=10)\nappend-only, time series"),
        ("TAGS",    "set_tag('git_sha', '...')\nmutable key/value"),
        ("ARTIFACTS","log_artifact, log_model\nfiles in run's blob store"),
    ]
    y = Inches(2.1)
    for label, body in children:
        rrect(s, Inches(4.1), y, Inches(8.7), Inches(1.0),
              fill=PANEL, line=ACCENT)
        textbox(s, Inches(4.3), y + Inches(0.1), Inches(2.0),
                Inches(0.4), label, size=13, bold=True, color=ACCENT)
        textbox(s, Inches(4.3), y + Inches(0.45), Inches(8.4),
                Inches(0.5), body, size=12, color=LIGHT, font="Consolas")
        y += Inches(1.1)
    textbox(s, Inches(0.5), Inches(6.8), Inches(12.33), Inches(0.4),
            "mlflow.autolog() captures most of this for sklearn / XGBoost / Keras / PyTorch automatically.",
            size=12, color=ACCENT, bold=True, align=PP_ALIGN.CENTER)
    footer(s, "Ch 72")


def partL_model_registry():
    s = add_slide()
    slide_title(s, "UC Model Registry · aliases replace stages")
    slide_subtitle(s, "Champion / Challenger is a moving label, not a folder")
    # left: legacy stages (deprecated)
    rrect(s, Inches(0.5), Inches(1.7), Inches(6.0), Inches(2.6),
          fill=PANEL, line=RED)
    textbox(s, Inches(0.7), Inches(1.85), Inches(5.6), Inches(0.4),
            "LEGACY (workspace registry — deprecated)",
            size=13, bold=True, color=RED)
    textbox(s, Inches(0.7), Inches(2.3), Inches(5.6), Inches(1.9),
            ("Stages: None / Staging / Production / Archived.\n\n"
             "Moving a version between stages meant transitioning\n"
             "the version — a fragile mutable concept.\n\n"
             "Not available in Unity Catalog."),
            size=13, color=LIGHT)
    # right: UC aliases
    rrect(s, Inches(6.85), Inches(1.7), Inches(6.0), Inches(2.6),
          fill=PANEL, line=GREEN)
    textbox(s, Inches(7.05), Inches(1.85), Inches(5.6), Inches(0.4),
            "UC ALIASES  (current)", size=13, bold=True, color=GREEN)
    textbox(s, Inches(7.05), Inches(2.3), Inches(5.6), Inches(1.9),
            ("Each registered model has VERSIONS (1, 2, 3, …).\n\n"
             "Aliases are NAMED POINTERS to versions:\n"
             "  @champion  →  version 4\n"
             "  @challenger →  version 7\n\n"
             "Re-point an alias to ship.  Versions never move."),
            size=13, color=LIGHT, font="Consolas")
    # diagram
    rrect(s, Inches(0.5), Inches(4.5), Inches(12.33), Inches(2.5),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(0.7), Inches(4.6), Inches(11.9), Inches(0.4),
            "Promotion flow", size=13, color=ACCENT, bold=True)
    # versions
    for i, v in enumerate([1, 2, 3, 4, 5, 6, 7]):
        rrect(s, Inches(0.9 + i * 1.6), Inches(5.4), Inches(1.4), Inches(0.7),
              fill=BLUE)
        textbox(s, Inches(0.9 + i * 1.6), Inches(5.4), Inches(1.4),
                Inches(0.7), f"v{v}", size=13, bold=True, color=WHITE,
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    # champion arrow → v4
    arrow(s, Inches(0.7), Inches(6.5), Inches(4.0 + 0.6), Inches(6.1),
          color=GREEN, weight=2.5)
    textbox(s, Inches(0.7), Inches(6.55), Inches(2.5), Inches(0.3),
            "@champion", size=12, color=GREEN, bold=True)
    # challenger arrow → v7
    arrow(s, Inches(9.0), Inches(6.7), Inches(11.4), Inches(6.1),
          color=YELLOW, weight=2.5)
    textbox(s, Inches(9.0), Inches(6.75), Inches(3), Inches(0.3),
            "@challenger",
            size=12, color=YELLOW, bold=True)
    footer(s, "Ch 73")


def partL_automl_glass_box():
    s = add_slide()
    slide_title(s, "AutoML · glass-box, not black-box")
    slide_subtitle(s, "Auto-explore  →  ranked leaderboard  →  EDA + trial notebooks")
    boxes = [
        ("INPUT",
         "table + target\n+ task type\n(classification\n/ regression /\nforecasting)",
         BLUE),
        ("AUTOML JOB",
         "  • EDA notebook\n"
         "  • feature\n   handling\n"
         "  • trial sweeps\n"
         "  (logreg, RF,\n"
         "   XGB, LGBM)",
         ACCENT),
        ("MLFLOW EXPERIMENT",
         "every trial\nlogged with\nparams +\nmetrics +\nautogenerated\nnotebook",
         GREEN),
        ("BEST MODEL",
         "promoted to UC\nregistry; you\nedit its\nnotebook to\nproductionise",
         YELLOW),
    ]
    y = Inches(2.4); h = Inches(3.2); w = Inches(2.95)
    x = Inches(0.5)
    for title, body, c in boxes:
        rrect(s, x, y, w, h, fill=PANEL, line=c)
        rect(s, x, y, w, Inches(0.5), fill=c)
        textbox(s, x, y, w, Inches(0.5), title, size=14, bold=True,
                color=BG if c == YELLOW else WHITE,
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        textbox(s, x + Inches(0.2), y + Inches(0.6), w - Inches(0.4),
                h - Inches(0.7), body, size=12, color=LIGHT)
        if x < Inches(10.0):
            arrow(s, x + w, y + h/2, x + w + Inches(0.1), y + h/2)
        x += w + Inches(0.1)
    textbox(s, Inches(0.5), Inches(5.9), Inches(12.33), Inches(1.0),
            ("Why \"glass-box\":  every trial generates a runnable notebook "
             "you can read, modify, and own.\n"
             "Use AutoML as a strong baseline + EDA accelerant — not as a\n"
             "way to skip understanding the model."),
            size=13, color=ACCENT, bold=True, align=PP_ALIGN.CENTER)
    footer(s, "Ch 74")



# =======================================================================
# PART M — CAPSTONE
# =======================================================================

def partM_lending_club():
    s = add_slide()
    slide_title(s, "Capstone · Lending Club loan-default end-to-end")
    slide_subtitle(s, "Twelve stages — every earlier part of the book shows up")
    stages = [
        ("1", "Read raw CSV", "Ch 57"),
        ("2", "Schema + cleaning", "Ch 23"),
        ("3", "EDA + class balance", "Ch 23, 46"),
        ("4", "Feature engineering", "Ch 24-28"),
        ("5", "Train/test split", "Ch 21-22"),
        ("6", "Pipeline (stages)", "Ch 62-63"),
        ("7", "Baseline model", "Ch 31-32"),
        ("8", "HPO (CV + grid / Hyperopt)", "Ch 48-53, 64"),
        ("9", "Evaluate (ROC / PR)", "Ch 42-43, 46"),
        ("10", "Log to MLflow", "Ch 72"),
        ("11", "Register in UC", "Ch 73"),
        ("12", "Batch inference + monitor", "Ch 30, 74"),
    ]
    cols = 4; rows = 3
    cw = Inches(3.05); ch = Inches(1.45)
    for i, (n, t, ref) in enumerate(stages):
        r = i // cols; col = i % cols
        x = Inches(0.5 + col * (3.05 + 0.1))
        y = Inches(1.8 + r * (1.45 + 0.15))
        rrect(s, x, y, cw, ch, fill=PANEL, line=ACCENT)
        ellipse(s, x + Inches(0.15), y + Inches(0.2),
                Inches(0.65), Inches(0.65), fill=ACCENT)
        textbox(s, x + Inches(0.15), y + Inches(0.2),
                Inches(0.65), Inches(0.65), n, size=16, bold=True,
                color=WHITE, align=PP_ALIGN.CENTER,
                anchor=MSO_ANCHOR.MIDDLE)
        textbox(s, x + Inches(0.9), y + Inches(0.2),
                cw - Inches(1.0), Inches(0.5), t,
                size=13, bold=True, color=WHITE)
        textbox(s, x + Inches(0.9), y + Inches(0.75),
                cw - Inches(1.0), Inches(0.5), ref,
                size=11, color=ACCENT, bold=True)
    footer(s, "Ch 75")


def partM_synthesis_matrix():
    s = add_slide()
    slide_title(s, "Synthesis · how the parts compose in one project")
    slide_subtitle(s, "Every part of the book contributes — and depends on the ones before it")
    parts = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"]
    # circular layout
    import math
    cx, cy = Inches(6.6), Inches(4.6)
    r = Inches(2.4)
    coords = {}
    for i, p in enumerate(parts):
        a = (i / len(parts)) * 2 * math.pi - math.pi / 2
        x = cx + Inches(math.cos(a) * 2.4); y = cy + Inches(math.sin(a) * 2.0)
        coords[p] = (x, y)
    # draw connections — only ones that actually compose
    pairs = [("A", "D"), ("B", "D"), ("C", "D"),
             ("D", "F"), ("D", "G"), ("D", "H"),
             ("E", "F"), ("E", "K"),
             ("F", "I"), ("G", "I"), ("H", "I"),
             ("J", "K"), ("K", "L"), ("F", "L"), ("I", "L"),
             ("D", "L"), ("E", "L")]
    for a, b in pairs:
        line(s, coords[a][0], coords[a][1],
             coords[b][0], coords[b][1], color=GREY, weight=0.8)
    # nodes on top
    for p in parts:
        x, y = coords[p]
        ellipse(s, x - Inches(0.35), y - Inches(0.35),
                Inches(0.7), Inches(0.7), fill=ACCENT)
        textbox(s, x - Inches(0.35), y - Inches(0.35),
                Inches(0.7), Inches(0.7), p, size=18, bold=True,
                color=WHITE, align=PP_ALIGN.CENTER,
                anchor=MSO_ANCHOR.MIDDLE)
    # caption
    textbox(s, Inches(0.5), Inches(6.9), Inches(12.33), Inches(0.4),
            "Edges = \"this part uses concepts from that one.\"   M (capstone) sits at the centre conceptually — it touches every node.",
            size=12, color=MUTED, align=PP_ALIGN.CENTER)
    footer(s, "Ch 75")


def closing_go_read():
    s = add_slide()
    # accent stripe
    rect(s, 0, 0, Inches(0.6), SH, fill=ACCENT)
    textbox(s, Inches(1.0), Inches(1.6), Inches(11), Inches(0.6),
            "Now go read the book.", size=44, color=WHITE, bold=True)
    textbox(s, Inches(1.0), Inches(2.6), Inches(11), Inches(0.5),
            "Slides are signposts. The depth lives in the chapters.",
            size=20, color=MUTED)
    rrect(s, Inches(1.0), Inches(3.6), Inches(11.3), Inches(2.6),
          fill=PANEL, line=ACCENT)
    textbox(s, Inches(1.3), Inches(3.8), Inches(10.7), Inches(0.4),
            "TEXTBOOK ROOT", size=14, bold=True, color=ACCENT)
    textbox(s, Inches(1.3), Inches(4.2), Inches(10.7), Inches(0.5),
            "topics/09a_databricks_ml_associate/README.md",
            size=18, color=WHITE, font="Consolas")
    textbox(s, Inches(1.3), Inches(4.95), Inches(10.7), Inches(1.2),
            ("76 chapters across 13 parts.\n"
             "Each chapter is self-contained but the parts build linearly.\n"
             "When a slide here felt thin, the chapter is where the math, "
             "the examples, and the Spark code live."),
            size=14, color=LIGHT)
    textbox(s, Inches(1.0), Inches(6.8), Inches(11), Inches(0.3),
            "Career upskill · Topic 09a", size=11, color=GREY)


# =======================================================================
# BUILD
# =======================================================================

def build_all():
    # Front
    front_title()
    front_audience()
    front_contents()

    # Part A
    section_divider("A", "Why ML Exists", "Chapters 1 – 4")
    partA_function_approximation()
    partA_three_paradigms()
    partA_spam_pipeline()
    partA_lifecycle()
    partA_ml_vs_rules()
    partA_data_split_preview()

    # Part B
    section_divider("B", "Probability & Statistics", "Chapters 5 – 10")
    partB_rv_pmf_pdf()
    partB_distributions()
    partB_bayes_disease()
    partB_lln_clt()
    partB_hypothesis_pipeline()
    partB_pvalue_truth()
    partB_confidence_intervals()

    # Part C
    section_divider("C", "Linear Algebra & Calculus", "Chapters 11 – 15")
    partC_vectors_dot()
    partC_projection()
    partC_matrix_linear_map()
    partC_eigen()
    partC_gradients()
    partC_chain_rule()

    # Part D
    section_divider("D", "The Fundamental ML Problem", "Chapters 16 – 22")
    partD_loss_table()
    partD_gradient_descent()
    partD_capacity_ucurve()
    partD_bias_variance()
    partD_regularisation_geometry()
    partD_kfold_cv()
    partD_leakage()

    # Part E
    section_divider("E", "Feature Engineering", "Chapters 23 – 30")
    partE_missing_taxonomy()
    partE_categorical_decision()
    partE_numerical_transforms()
    partE_outliers()
    partE_cyclical_encoding()
    partE_feature_selection()
    partE_feature_store_skew()

    # Part F
    section_divider("F", "Supervised Algorithms", "Chapters 31 – 37")
    partF_linear_regression()
    partF_logistic_sigmoid()
    partF_decision_tree()
    partF_random_forest()
    partF_adaboost()
    partF_gbm_residuals()
    partF_xgb_lgbm_cat()
    partF_nb_knn()

    # Part G
    section_divider("G", "Unsupervised Algorithms", "Chapters 38 – 41")
    partG_kmeans_progression()
    partG_choose_k()
    partG_hierarchical()
    partG_pca_eigen()
    partG_tsne_umap_caveats()

    # Part H
    section_divider("H", "Model Evaluation Theory", "Chapters 42 – 47")
    partH_confusion_matrix()
    partH_precision_recall_f1()
    partH_roc_curve()
    partH_roc_vs_pr()
    partH_regression_metrics()
    partH_imbalanced_techniques()
    partH_multiclass_macros()

    # Part I
    section_divider("I", "Hyperparameter Optimisation", "Chapters 48 – 54")
    partI_hpo_problem()
    partI_grid_vs_random()
    partI_bo_loop()
    partI_tpe()
    partI_hyperopt()
    partI_optuna()

    # Part J
    section_divider("J", "Spark from Zero", "Chapters 55 – 61")
    partJ_why_distributed()
    partJ_mr_vs_spark()
    partJ_architecture()
    partJ_rdd_df_dataset()
    partJ_catalyst()
    partJ_narrow_wide()
    partJ_shuffle_anatomy()
    partJ_aqe()

    # Part K
    section_divider("K", "pyspark.ml in Depth", "Chapters 62 – 67")
    partK_pipeline_pattern()
    partK_transformers_table()
    partK_cv_model_count()
    partK_evaluators()
    partK_persistence()
    partK_pandas_udf()

    # Part L
    section_divider("L", "Databricks Platform & MLflow", "Chapters 68 – 74")
    partL_workspace_anatomy()
    partL_dbr_ml_runtime()
    partL_unity_catalog()
    partL_feature_store_pit()
    partL_mlflow_anatomy()
    partL_model_registry()
    partL_automl_glass_box()

    # Part M + closing
    section_divider("M", "Capstone & Synthesis", "Chapters 75 – 76")
    partM_lending_club()
    partM_synthesis_matrix()
    closing_go_read()

    out = "/Users/vr/Code/Career_upskill/topics/09a_databricks_ml_associate/pptx/Databricks_ML_Associate_Mastery_study_deck.pptx"
    prs.save(out)
    return out, len(prs.slides)


if __name__ == "__main__":
    out, n = build_all()
    print(f"Saved {n} slides to {out}")
