"""
generate_quiz_pdf.py
Reads a quiz JSON file and writes two PDFs:
  - <test_id>_quiz.pdf        — questions only (student copy, no answers)
  - <test_id>_solutions.pdf   — questions + answers + explanations (review copy)

Usage:
    python3 scripts/generate_quiz_pdf.py <test_json_path>

Example:
    python3 scripts/generate_quiz_pdf.py data/tests/generated/bella_data_test_4.json
"""

import json
import sys
import textwrap
from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus.flowables import Flowable


# ── Colour palette ────────────────────────────────────────────────────────────
BRAND_BLUE   = HexColor("#1a4f8a")
BRAND_LIGHT  = HexColor("#e8f0fb")
CODE_BG      = HexColor("#f4f4f4")
CODE_BORDER  = HexColor("#cccccc")
CORRECT_BG   = HexColor("#d4edda")
CORRECT_FG   = HexColor("#155724")
EXPLAIN_BG   = HexColor("#fff3cd")
GUIDE_BG     = HexColor("#f0f4ff")
HEADER_FG    = white
SUBHEAD_FG   = HexColor("#444444")
MUTED        = HexColor("#666666")

# ── Styles ────────────────────────────────────────────────────────────────────
def build_styles():
    base = getSampleStyleSheet()

    def s(name, parent="Normal", **kw):
        return ParagraphStyle(name, parent=base[parent], **kw)

    return {
        "title":   s("title",   "Title",
                     fontSize=20, textColor=BRAND_BLUE,
                     spaceAfter=4, alignment=TA_CENTER),
        "subtitle": s("subtitle", "Normal",
                     fontSize=10, textColor=MUTED,
                     spaceAfter=2, alignment=TA_CENTER),
        "divider":  s("divider",  "Normal",
                     fontSize=8, textColor=MUTED,
                     spaceAfter=6, alignment=TA_CENTER),

        "q_number": s("q_number", "Normal",
                     fontSize=13, fontName="Helvetica-Bold",
                     textColor=BRAND_BLUE, spaceBefore=6, spaceAfter=2),
        "topic":    s("topic",    "Normal",
                     fontSize=8,  textColor=MUTED, spaceAfter=4),
        "teach":    s("teach",    "Normal",
                     fontSize=9,  textColor=SUBHEAD_FG,
                     leftIndent=8, spaceAfter=6, leading=13),
        "prompt":   s("prompt",   "Normal",
                     fontSize=10.5, leading=15, spaceAfter=6),
        "option":   s("option",   "Normal",
                     fontSize=10, leading=14, leftIndent=12),
        "option_correct": s("option_correct", "Normal",
                     fontSize=10, leading=14, leftIndent=12,
                     textColor=CORRECT_FG, fontName="Helvetica-Bold"),
        "code":     s("code",     "Code",
                     fontSize=8.5, fontName="Courier",
                     leftIndent=8, rightIndent=8, leading=12,
                     backColor=CODE_BG, spaceAfter=6),
        "answer_label": s("answer_label", "Normal",
                     fontSize=10, fontName="Helvetica-Bold",
                     textColor=CORRECT_FG, spaceBefore=4, spaceAfter=2),
        "explain_head": s("explain_head", "Normal",
                     fontSize=10, fontName="Helvetica-Bold",
                     textColor=HexColor("#856404"), spaceAfter=2),
        "explain_body": s("explain_body", "Normal",
                     fontSize=10, leading=14, spaceAfter=4,
                     leftIndent=8),
        "guide_head": s("guide_head", "Normal",
                     fontSize=9, fontName="Helvetica-Bold",
                     textColor=BRAND_BLUE, spaceBefore=4, spaceAfter=2),
        "guide_q":   s("guide_q",  "Normal",
                     fontSize=9, leading=13, leftIndent=12,
                     textColor=SUBHEAD_FG),
        "footer":   s("footer",   "Normal",
                     fontSize=8, textColor=MUTED, alignment=TA_CENTER),
    }


# ── Helper: coloured section box ─────────────────────────────────────────────
def colour_box(content_rows, bg, border=None, padding=6):
    """Wrap a list of Paragraph/Spacer items in a shaded single-cell table."""
    tbl = Table([[content_rows]], colWidths=[6.5 * inch])
    style = [
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("TOPPADDING",    (0, 0), (-1, -1), padding),
        ("BOTTOMPADDING", (0, 0), (-1, -1), padding),
        ("LEFTPADDING",   (0, 0), (-1, -1), padding),
        ("RIGHTPADDING",  (0, 0), (-1, -1), padding),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]
    if border:
        style += [
            ("BOX", (0, 0), (-1, -1), 0.5, border),
            ("ROUNDEDCORNERS", [4]),
        ]
    tbl.setStyle(TableStyle(style))
    return tbl


# ── Code block renderer ───────────────────────────────────────────────────────
def code_block(code_text, styles):
    """Return a shaded code table with monospace text."""
    lines = code_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    cell = Paragraph(f'<font name="Courier" size="8.5">{lines.replace(chr(10), "<br/>")}</font>',
                     styles["code"])
    tbl = Table([[cell]], colWidths=[6.5 * inch])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CODE_BG),
        ("BOX",        (0, 0), (-1, -1), 0.5, CODE_BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
    ]))
    return tbl


# ── Question builder ──────────────────────────────────────────────────────────
OPTION_LETTERS = ["A", "B", "C", "D"]

def build_question_block(q, styles, show_solutions):
    """Return a list of flowables for a single question."""
    elems = []

    # Number + topic line
    tags = ", ".join(q.get("topic_tags", []))
    unit = q.get("unit", "")
    elems.append(Paragraph(
        f"Question {q['id'].lstrip('q').upper()}",
        styles["q_number"]
    ))
    elems.append(Paragraph(
        f"Unit {unit} · {tags}  |  {q.get('type','').replace('_',' ').title()}",
        styles["topic"]
    ))

    # Teaching note (solutions copy only)
    if show_solutions and q.get("teaching_note"):
        note_para = Paragraph(
            f"<i>Why this question:</i> {q['teaching_note']}",
            styles["teach"]
        )
        elems.append(colour_box([note_para], BRAND_LIGHT, BRAND_BLUE, padding=8))
        elems.append(Spacer(1, 6))

    # Prompt
    elems.append(Paragraph(q["prompt"], styles["prompt"]))

    # Code block
    if q.get("code_block"):
        elems.append(code_block(q["code_block"], styles))
        elems.append(Spacer(1, 4))

    # Options
    answer = q["answer_key"]
    opts = q.get("options", {})
    for letter in OPTION_LETTERS:
        if letter not in opts:
            continue
        text = opts[letter]
        safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if show_solutions and letter == answer:
            label = f"<b>✓ {letter}.</b> {safe}"
            p = Paragraph(label, styles["option_correct"])
        else:
            p = Paragraph(f"{letter}.  {safe}", styles["option"])
        elems.append(p)
    elems.append(Spacer(1, 6))

    # Guiding questions (always shown)
    guides = q.get("guiding_questions", [])
    if guides:
        guide_rows = [Paragraph("Guiding Questions — think through these before answering:",
                                styles["guide_head"])]
        for i, gq in enumerate(guides, 1):
            safe_g = gq["text"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            guide_rows.append(Paragraph(f"{i}. {safe_g}", styles["guide_q"]))
            guide_rows.append(Spacer(1, 3))
        elems.append(colour_box(guide_rows, GUIDE_BG, BRAND_BLUE, padding=8))
        elems.append(Spacer(1, 6))

    # Answer + explanation (solutions copy only)
    if show_solutions:
        exp_text = q.get("explanation", "")
        safe_exp = exp_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        sol_rows = [
            Paragraph(f"Correct Answer: {answer}", styles["answer_label"]),
            Paragraph(safe_exp, styles["explain_body"]),
        ]
        elems.append(colour_box(sol_rows, EXPLAIN_BG, HexColor("#ffc107"), padding=8))
        elems.append(Spacer(1, 8))

    return KeepTogether(elems)


# ── Header table ──────────────────────────────────────────────────────────────
def build_header_table(title, subtitle, copy_label):
    title_style  = ParagraphStyle("h1", fontSize=16, fontName="Helvetica-Bold",
                                  textColor=white, alignment=TA_LEFT, leading=20)
    label_style  = ParagraphStyle("h2", fontSize=10, fontName="Helvetica",
                                  textColor=HexColor("#cce0ff"), alignment=TA_LEFT)
    copy_style   = ParagraphStyle("h3", fontSize=9, fontName="Helvetica-Bold",
                                  textColor=white, alignment=TA_LEFT)
    title_para  = Paragraph(title,      title_style)
    sub_para    = Paragraph(subtitle,   label_style)
    copy_para   = Paragraph(copy_label, copy_style)
    cell = [title_para, Spacer(1, 3), sub_para, Spacer(1, 3), copy_para]
    tbl = Table([[cell]], colWidths=[7 * inch])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), BRAND_BLUE),
        ("TOPPADDING",    (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING",   (0, 0), (-1, -1), 16),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 16),
    ]))
    return tbl


# ── Score table (quiz copy) ───────────────────────────────────────────────────
def build_score_table(n_questions):
    header = ["Q", "Answer", "✓/✗"]
    data   = [header] + [[str(i), "", ""] for i in range(1, n_questions + 1)]
    tbl = Table(data, colWidths=[0.5*inch, 1.2*inch, 0.5*inch])
    style = [
        ("BACKGROUND",  (0, 0), (-1, 0),  BRAND_BLUE),
        ("TEXTCOLOR",   (0, 0), (-1, 0),  white),
        ("FONTNAME",    (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 9),
        ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
        ("GRID",        (0, 0), (-1, -1), 0.5, CODE_BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, CODE_BG]),
    ]
    tbl.setStyle(TableStyle(style))
    return tbl


# ── Main PDF builder ──────────────────────────────────────────────────────────
def build_pdf(quiz: dict, out_path: Path, show_solutions: bool):
    copy_label = "SOLUTIONS & EXPLANATIONS — Review Copy" if show_solutions else "STUDENT QUIZ — Question Copy"
    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=LETTER,
        leftMargin=0.75*inch, rightMargin=0.75*inch,
        topMargin=0.75*inch,  bottomMargin=0.75*inch,
    )

    styles = build_styles()
    story  = []

    # Header
    story.append(build_header_table(
        title    = quiz.get("title", "Quiz"),
        subtitle = f"Session · {quiz.get('created_at','')}",
        copy_label = copy_label,
    ))
    story.append(Spacer(1, 12))

    if not show_solutions:
        # Student copy: name line + answer table at top
        story.append(Paragraph("Name: ______________________________    Date: _______________", styles["prompt"]))
        story.append(Spacer(1, 6))
        n = len(quiz.get("questions", []))
        story.append(build_score_table(n))
        story.append(Spacer(1, 14))

    story.append(HRFlowable(width="100%", thickness=0.5, color=BRAND_BLUE, spaceAfter=10))

    for q in quiz.get("questions", []):
        story.append(build_question_block(q, styles, show_solutions))
        story.append(HRFlowable(width="100%", thickness=0.5, color=CODE_BORDER, spaceAfter=8, spaceBefore=4))

    doc.build(story)
    print(f"  Written: {out_path}")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/generate_quiz_pdf.py <path_to_quiz.json>")
        sys.exit(1)

    json_path = Path(sys.argv[1])
    if not json_path.exists():
        print(f"Error: file not found: {json_path}")
        sys.exit(1)

    quiz = json.loads(json_path.read_text())
    out_dir = json_path.parent

    quiz_pdf      = out_dir / f"{quiz['test_id']}_quiz.pdf"
    solutions_pdf = out_dir / f"{quiz['test_id']}_solutions.pdf"

    print("Generating quiz PDF …")
    build_pdf(quiz, quiz_pdf, show_solutions=False)

    print("Generating solutions PDF …")
    build_pdf(quiz, solutions_pdf, show_solutions=True)

    print("\nDone.")
    print(f"  Quiz:      {quiz_pdf}")
    print(f"  Solutions: {solutions_pdf}")
