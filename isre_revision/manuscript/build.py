"""Build manuscript.docx from manuscript.md in Management Science submission format.

pandoc converts the Markdown (with LaTeX math -> native Word equations); python-docx then
applies the journal layout: Times New Roman 12 pt, double spacing, 1-inch margins on
US Letter, page numbers, and yellow highlighting for [[placeholders]].
"""
import re
import subprocess
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

HERE = Path(__file__).parent
SRC, TMP, OUT = HERE / "manuscript.md", HERE / "_build.md", HERE / "manuscript.docx"

# 1. Wrap [[ ... ]] placeholders in a highlighted character style.
text = SRC.read_text()
text = re.sub(r"\[\[(.*?)\]\]", lambda m: "[\\[\\[" + m.group(1) + "\\]\\]]{custom-style=\"Placeholder\"}",
              text, flags=re.S)
TMP.write_text(text)

subprocess.run(["pandoc", str(TMP), "-f", "markdown+tex_math_dollars", "-t", "docx",
                "--resource-path", str(HERE), "-o", str(OUT)], check=True)
TMP.unlink()

doc = Document(OUT)
FONT = "Times New Roman"


def set_font(style, size=12, bold=None, italic=None, color_black=True):
    f = style.font
    f.name, f.size = FONT, Pt(size)
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(a), FONT)
    for a in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
        rfonts.attrib.pop(qn(a), None)
    if bold is not None:
        f.bold = bold
    if italic is not None:
        f.italic = italic
    if color_black:
        f.color.rgb = RGBColor(0, 0, 0)


def spacing(style, line=2.0, before=0, after=0, indent=None, align=None, keep_next=None):
    pf = style.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = line
    pf.space_before, pf.space_after = Pt(before), Pt(after)
    if indent is not None:
        pf.first_line_indent = indent
    if align is not None:
        pf.alignment = align
    if keep_next is not None:
        pf.keep_with_next = keep_next


styles = {s.name: s for s in doc.styles}
for name in ("Normal", "Body Text", "First Paragraph", "Compact", "Block Text"):
    if name in styles:
        set_font(styles[name])
        spacing(styles[name])
for name in ("Body Text", "First Paragraph"):
    if name in styles:
        spacing(styles[name], indent=Inches(0.5))
if "Compact" in styles:
    set_font(styles["Compact"], size=10)
    spacing(styles["Compact"], line=1.0)

for name, size, bold, italic, before in (("Title", 14, True, False, 0), ("Heading 1", 12, True, False, 12),
                                         ("Heading 2", 12, True, True, 6), ("Heading 3", 12, False, True, 6)):
    if name in styles:
        st = styles[name]
        set_font(st, size, bold, italic)
        spacing(st, before=before, after=0, indent=Inches(0), keep_next=True,
                align=WD_ALIGN_PARAGRAPH.CENTER if name == "Title" else WD_ALIGN_PARAGRAPH.LEFT)

for name, kw in (("Author", dict(align=WD_ALIGN_PARAGRAPH.CENTER, after=12)),
                 ("Abstract Title", dict(align=WD_ALIGN_PARAGRAPH.CENTER)),
                 ("Abstract", dict(align=WD_ALIGN_PARAGRAPH.JUSTIFY)),
                 ("Keywords", dict(before=12)),
                 ("EC Title", dict(align=WD_ALIGN_PARAGRAPH.CENTER, after=12)),
                 ("Reference", dict())):
    if name in styles:
        st = styles[name]
        set_font(st, bold=name in ("Abstract Title", "EC Title"))
        spacing(st, indent=Inches(0), **kw)
if "Reference" in styles:
    pf = styles["Reference"].paragraph_format
    pf.left_indent, pf.first_line_indent = Inches(0.5), Inches(-0.5)

for name in ("Table Caption", "Image Caption", "Caption"):
    if name in styles:
        set_font(styles[name], size=11, italic=False)
        spacing(styles[name], line=1.0, before=6, after=6, indent=Inches(0), keep_next=(name == "Table Caption"))
if "Captioned Figure" in styles:
    spacing(styles["Captioned Figure"], line=1.0, before=6, align=WD_ALIGN_PARAGRAPH.CENTER, indent=Inches(0))

if "Placeholder" in styles:
    rpr = styles["Placeholder"].element.get_or_add_rPr()
    hl = OxmlElement("w:highlight")
    hl.set(qn("w:val"), "yellow")
    rpr.append(hl)

for name in ("Hyperlink",):
    if name in styles:
        styles[name].font.color.rgb = RGBColor(0, 0, 0)

# Page setup: US Letter, 1-inch margins, centred page number in footer.
for sec in doc.sections:
    sec.page_width, sec.page_height = Inches(8.5), Inches(11)
    for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(sec, side, Inches(1))
    p = sec.footer.paragraphs[0] if sec.footer.paragraphs else sec.footer.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    for tag, txt in (("begin", None), (None, "PAGE"), ("end", None)):
        if tag:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), tag)
        else:
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = txt
        run._r.append(el)
    run.font.name, run.font.size = FONT, Pt(12)

# Tables: full width, single spaced, 10 pt, header row bold, simple top/bottom rules.
for tbl in doc.tables:
    tbl.autofit = True
    tblPr = tbl._tbl.tblPr
    w = tblPr.find(qn("w:tblW"))
    if w is None:
        w = OxmlElement("w:tblW")
        tblPr.append(w)
    w.set(qn("w:type"), "pct")
    w.set(qn("w:w"), "5000")
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "bottom"):
        b = OxmlElement(f"w:{edge}")
        b.set(qn("w:val"), "single")
        b.set(qn("w:sz"), "8")
        b.set(qn("w:color"), "000000")
        borders.append(b)
    old = tblPr.find(qn("w:tblBorders"))
    if old is not None:
        tblPr.remove(old)
    tblPr.append(borders)
    for i, row in enumerate(tbl.rows):
        for cell in row.cells:
            if i == 0:
                tcPr = cell._tc.get_or_add_tcPr()
                tcb = OxmlElement("w:tcBorders")
                b = OxmlElement("w:bottom")
                b.set(qn("w:val"), "single")
                b.set(qn("w:sz"), "4")
                b.set(qn("w:color"), "000000")
                tcb.append(b)
                tcPr.append(tcb)
            for para in cell.paragraphs:
                para.paragraph_format.line_spacing = 1.0
                para.paragraph_format.first_line_indent = Inches(0)
                for r in para.runs:
                    r.font.size = Pt(10)
                    r.font.name = FONT
                    if i == 0:
                        r.font.bold = True

# Direct yellow highlight on placeholder runs (some renderers ignore highlight set on a character style).
from docx.enum.text import WD_COLOR_INDEX
def _all_paragraphs(d):
    for para in d.paragraphs:
        yield para
    for t in d.tables:
        for row in t.rows:
            for cell in row.cells:
                yield from cell.paragraphs
for para in _all_paragraphs(doc):
    for r in para.runs:
        if r.style is not None and r.style.name == "Placeholder":
            r.font.highlight_color = WD_COLOR_INDEX.YELLOW

# Breathing room after tables: 12 pt before the paragraph that follows each table.
body = doc.element.body
for tbl in body.iter(qn("w:tbl")):
    nxt = tbl.getnext()
    if nxt is not None and nxt.tag == qn("w:p"):
        pPr = nxt.find(qn("w:pPr"))
        if pPr is None:
            pPr = OxmlElement("w:pPr"); nxt.insert(0, pPr)
        sp = pPr.find(qn("w:spacing"))
        if sp is None:
            sp = OxmlElement("w:spacing"); pPr.append(sp)
        sp.set(qn("w:before"), "240")

doc.core_properties.author = "Authors blinded for review"
doc.core_properties.title = "When Do Better AI Coding Tools Ship Fewer Defects?"
doc.save(OUT)
print("wrote", OUT)
