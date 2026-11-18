"""Build manuscript/manuscript_draft.docx from manuscript_draft.md with journal-style formatting.

pandoc converts the markdown (equations become native Word equations); python-docx then sets
  Times New Roman 12 pt, double spacing, 1-inch margins, page numbers in the footer,
  black bold headings, three-rule tables in 9 pt, single-spaced captions, hanging indents in the reference list.
Usage: python3 -I sim/make_docx.py
"""
import re, subprocess, sys
from pathlib import Path
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
M = ROOT / "manuscript"
FONT = "Times New Roman"


def set_font(style, size=None, bold=None, italic=None, color=True):
    style.font.name = FONT
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts"); rpr.append(rfonts)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"): rfonts.set(qn(a), FONT)
    for a in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
        if rfonts.get(qn(a)) is not None: del rfonts.attrib[qn(a)]
    if size: style.font.size = Pt(size)
    if bold is not None: style.font.bold = bold
    if italic is not None: style.font.italic = italic
    if color: style.font.color.rgb = RGBColor(0, 0, 0)


def make_reference(path):
    base = M / "_reference_default.docx"
    subprocess.run(["pandoc", "-o", str(base), "--print-default-data-file", "reference.docx"], check=True)
    d = Document(str(base))
    st = d.styles
    byname = {x.name: x for x in st}          # pandoc's reference uses capitalised built-in names that python-docx does not map
    for name in ("Normal", "Body Text", "First Paragraph", "Compact", "Block Text"):
        if name in byname:
            s = byname[name]; set_font(s, 12)
            pf = s.paragraph_format
            pf.line_spacing_rule = WD_LINE_SPACING.DOUBLE
            pf.space_before = Pt(0); pf.space_after = Pt(0)
            if name in ("Body Text", "First Paragraph"): pf.first_line_indent = Inches(0.5)
            if name == "Compact": pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
    for name, size, it in (("Title", 16, False), ("Heading 1", 14, False), ("Heading 2", 13, False), ("Heading 3", 12, False), ("Heading 4", 12, True)):
        if name in byname:
            s = byname[name]; set_font(s, size, bold=True, italic=it)
            s.paragraph_format.space_before = Pt(12); s.paragraph_format.space_after = Pt(6)
            s.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
            s.paragraph_format.keep_with_next = True
    if "Title" in byname: byname["Title"].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for name in ("Author", "Date", "Abstract", "Image Caption", "Table Caption", "Figure", "Captioned Figure"):
        if name in byname: set_font(byname[name], 11)
    sec = d.sections[0]
    sec.page_width, sec.page_height = Inches(8.5), Inches(11)
    for a in ("left_margin", "right_margin", "top_margin", "bottom_margin"): setattr(sec, a, Inches(1))
    d.save(str(path))
    base.unlink()


def add_page_number(section):
    p = section.footer.paragraphs[0] if section.footer.paragraphs else section.footer.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for t, txt in (("begin", None), (None, " PAGE "), ("end", None)):
        r = p.add_run(); r.font.name = FONT; r.font.size = Pt(11)
        if t:
            fc = OxmlElement("w:fldChar"); fc.set(qn("w:fldCharType"), t); r._r.append(fc)
        else:
            it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = txt; r._r.append(it)


def border(cell, **kw):
    tcPr = cell._tc.get_or_add_tcPr()
    b = tcPr.find(qn("w:tcBorders"))
    if b is None:
        b = OxmlElement("w:tcBorders"); tcPr.append(b)
    for edge, val in kw.items():
        e = b.find(qn(f"w:{edge}"))
        if e is None:
            e = OxmlElement(f"w:{edge}"); b.append(e)
        e.set(qn("w:val"), val["val"]); e.set(qn("w:sz"), str(val["sz"])); e.set(qn("w:color"), "000000"); e.set(qn("w:space"), "0")


def style_tables(doc):
    for t in doc.tables:
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = True
        tblPr = t._tbl.tblPr
        # remove pandoc's table style borders, set width to 100%
        w = tblPr.find(qn("w:tblW"))
        if w is None:
            w = OxmlElement("w:tblW"); tblPr.append(w)
        w.set(qn("w:type"), "pct"); w.set(qn("w:w"), "5000")
        rows = t.rows
        for ri, row in enumerate(rows):
            trPr = row._tr.get_or_add_trPr()
            cs = OxmlElement("w:cantSplit"); trPr.append(cs)          # keep a row on one page
            if ri == 0:
                th = OxmlElement("w:tblHeader"); trPr.append(th)      # repeat the header row on each page
            for c in row.cells:
                for p in c.paragraphs:
                    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
                    p.paragraph_format.first_line_indent = Inches(0)
                    p.paragraph_format.space_before = Pt(1); p.paragraph_format.space_after = Pt(1)
                    for r in p.runs:
                        r.font.name = FONT; r.font.size = Pt(8.5)
                        if ri == 0: r.font.bold = True
                if ri == 0: border(c, top={"val": "single", "sz": 12}, bottom={"val": "single", "sz": 6})
                if ri == len(rows) - 1: border(c, bottom={"val": "single", "sz": 12})


CAP = re.compile(r"^(Table|Figure) [A-Z]?\d+\.")


def style_paragraphs(doc):
    in_refs = False
    for p in doc.paragraphs:
        txt = p.text.strip()
        if p.style.name.startswith("Heading"):
            in_refs = txt == "References"
            continue
        if CAP.match(txt):                                   # captions: single spaced, no indent, smaller
            pf = p.paragraph_format
            pf.line_spacing_rule = WD_LINE_SPACING.SINGLE; pf.first_line_indent = Inches(0)
            pf.space_before = Pt(3); pf.space_after = Pt(12)
            for r in p.runs: r.font.size = Pt(10); r.font.name = FONT
            continue
        if in_refs and txt:                                  # references: hanging indent, single spaced
            pf = p.paragraph_format
            pf.left_indent = Inches(0.5); pf.first_line_indent = Inches(-0.5)
            pf.line_spacing_rule = WD_LINE_SPACING.SINGLE; pf.space_after = Pt(6)
        if txt.startswith("Keywords:") or txt.startswith("Proposition ") or txt.startswith("Lemma "):
            p.paragraph_format.first_line_indent = Inches(0)
        if p.paragraph_format.alignment is None and p.style.name in ("Body Text", "First Paragraph"):
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        # center paragraphs that hold only a picture
        if p._p.xpath(".//w:drawing") and not txt:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.first_line_indent = Inches(0)
            p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE


def build(md=None, out=None):
    md = md or M / "manuscript_draft.md"; out = out or M / "manuscript_draft.docx"
    ref = M / "_reference.docx"
    make_reference(ref)
    r = subprocess.run(["pandoc", str(md), "-o", str(out), "--from", "markdown+tex_math_dollars+pipe_tables+implicit_figures",
                        "--reference-doc", str(ref), "--resource-path", str(M)], capture_output=True, text=True)
    ref.unlink(missing_ok=True)
    if r.returncode != 0: raise RuntimeError(r.stderr[:500])
    d = Document(str(out))
    add_page_number(d.sections[0])
    style_tables(d); style_paragraphs(d)
    d.save(str(out))
    return out


if __name__ == "__main__":
    p = build(); d = Document(str(p))
    print("wrote", p, "| paragraphs", len(d.paragraphs), "| tables", len(d.tables), "| images", len(d.inline_shapes))
