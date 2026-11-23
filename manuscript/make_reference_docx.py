"""Build submission_reference.docx: the Word style template pandoc uses for the manuscript (Times New Roman 12 pt,
double-spaced body, single-spaced tables, black headings, page numbers and continuous line numbers).

Usage:  python make_reference_docx.py  (needs pandoc and python-docx)
"""
import os
import subprocess
import tempfile

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor, Inches

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = "Times New Roman"


def set_font(style, size=None, bold=None, italic=None):
    f = style.font
    f.name, f.color.rgb = FONT, RGBColor(0, 0, 0)
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts"); rpr.append(rfonts)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(a), FONT)
    for a in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
        rfonts.attrib.pop(qn(a), None)
    if size: f.size = Pt(size)
    if bold is not None: f.bold = bold
    if italic is not None: f.italic = italic


def main():
    with tempfile.TemporaryDirectory() as td:
        base = os.path.join(td, "ref.docx")
        with open(base, "wb") as fh:
            fh.write(subprocess.run(["pandoc", "--print-default-data-file", "reference.docx"], capture_output=True, check=True).stdout)
        doc = Document(base)
    st = {s.name: s for s in doc.styles}
    for name in ("Normal", "Body Text", "First Paragraph", "Abstract", "Block Text", "Bibliography"):
        if name in st:
            s = st[name]; set_font(s, 12)
            pf = s.paragraph_format
            pf.line_spacing_rule = WD_LINE_SPACING.DOUBLE
            pf.space_before, pf.space_after = Pt(0), Pt(0)
            if name in ("Body Text",):
                pf.first_line_indent = Inches(0.3)
    for name in ("Compact",):
        s = st[name]; set_font(s, 10); s.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    for name, size in (("Title", 16), ("Heading 1", 13), ("Heading 2", 12), ("Heading 3", 12)):
        s = st[name]; set_font(s, size, bold=True, italic=False)
        pf = s.paragraph_format; pf.space_before, pf.space_after = Pt(18 if name != "Title" else 0), Pt(6); pf.keep_with_next = True
        pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
    st["Title"].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for name in ("Table Caption", "Image Caption", "Caption"):
        if name in st:
            s = st[name]; set_font(s, 11, italic=False); s.paragraph_format.space_before = Pt(12)
            s.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE; s.paragraph_format.keep_with_next = True
    for name in ("Hyperlink",):
        if name in st:
            set_font(st[name])
    # table style: top and bottom rules, rule under the header row
    tbl = st["Table"].element
    tblPr = tbl.find(qn("w:tblPr"))
    borders = OxmlElement("w:tblBorders")
    for edge, sz in (("top", 8), ("bottom", 8)):
        b = OxmlElement(f"w:{edge}"); b.set(qn("w:val"), "single"); b.set(qn("w:sz"), str(sz)); b.set(qn("w:color"), "000000"); borders.append(b)
    old = tblPr.find(qn("w:tblBorders"))
    if old is not None: tblPr.remove(old)
    tblPr.append(borders)
    # page setup: Letter-agnostic margins, page number footer, continuous line numbers
    sec = doc.sections[0]
    sec.left_margin = sec.right_margin = sec.top_margin = sec.bottom_margin = Inches(1)
    p = sec.footer.paragraphs[0] if sec.footer.paragraphs else sec.footer.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    for tag, txt in (("begin", None), (None, "PAGE"), ("end", None)):
        if tag:
            fc = OxmlElement("w:fldChar"); fc.set(qn("w:fldCharType"), tag); run._r.append(fc)
        else:
            it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = txt; run._r.append(it)
    ln = OxmlElement("w:lnNumType"); ln.set(qn("w:countBy"), "1"); ln.set(qn("w:restart"), "continuous")
    sec._sectPr.append(ln)
    out = os.path.join(HERE, "submission_reference.docx")
    doc.save(out)
    print("saved", out)


if __name__ == "__main__":
    main()
