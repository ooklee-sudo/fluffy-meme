"""Word versions of dss_highlights.txt and dss_cover_letter.txt (Times New Roman 12 pt).

Usage:  python make_dss_extras_docx.py
"""
import os

from docx import Document
from docx.shared import Pt, Inches

HERE = os.path.dirname(os.path.abspath(__file__))


def new_doc():
    d = Document()
    st = d.styles["Normal"]
    st.font.name, st.font.size = "Times New Roman", Pt(12)
    st.element.rPr.rFonts.set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}eastAsia", "Times New Roman")
    for s in d.sections:
        s.left_margin = s.right_margin = s.top_margin = s.bottom_margin = Inches(1)
    return d


def highlights():
    d = new_doc()
    h = d.add_paragraph(); r = h.add_run("Highlights"); r.bold = True
    for line in open(os.path.join(HERE, "dss_highlights.txt"), encoding="utf-8").read().splitlines():
        if line.strip():
            d.add_paragraph(line.strip(), style="List Bullet")
    d.save(os.path.join(HERE, "dss_highlights.docx"))


def cover_letter():
    d = new_doc()
    text = open(os.path.join(HERE, "dss_cover_letter.txt"), encoding="utf-8").read()
    for block in text.split("\n\n"):
        p = d.add_paragraph()
        lines = block.strip("\n").split("\n")
        for i, line in enumerate(lines):
            run = p.add_run(line)
            if i < len(lines) - 1:
                run.add_break()
        p.paragraph_format.space_after = Pt(10)
    d.save(os.path.join(HERE, "dss_cover_letter.docx"))


if __name__ == "__main__":
    highlights()
    cover_letter()
    print("saved dss_highlights.docx and dss_cover_letter.docx")
