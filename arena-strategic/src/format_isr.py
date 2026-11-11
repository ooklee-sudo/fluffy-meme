"""Format a manuscript .docx for ISR review: anonymized, double-spaced, 12-pt Times New Roman, 1-inch margins, page numbers."""
import sys, re
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
src, out = sys.argv[1], sys.argv[2]
d = Document(src)
# 1. remove the byline (date · @mention) and any other paragraph carrying an @handle
for p in list(d.paragraphs):
    if re.search(r'·\s*@\S+', p.text) or re.fullmatch(r'\s*\S+\s*·\s*@\S+\s*', p.text):
        p._element.getparent().remove(p._element)
# 2. clear document metadata
cp = d.core_properties
for attr in ('author', 'last_modified_by', 'comments', 'keywords', 'subject', 'category'): setattr(cp, attr, '')
# 3. page setup
for s in d.sections:
    s.top_margin = s.bottom_margin = s.left_margin = s.right_margin = Inches(1)
    s.page_width, s.page_height = Inches(8.5), Inches(11)
    fp = s.footer.paragraphs[0] if s.footer.paragraphs else s.footer.add_paragraph()
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = fp.add_run()
    for tag, text in (('begin', None), (None, 'PAGE'), ('end', None)):
        if tag:
            el = OxmlElement('w:fldChar'); el.set(qn('w:fldCharType'), tag); run._r.append(el)
        else:
            it = OxmlElement('w:instrText'); it.set(qn('xml:space'), 'preserve'); it.text = text; run._r.append(it)
# 4. fonts and spacing: body double-spaced, tables single-spaced; all text Times New Roman 12 (tables 10)
def style_runs(par, size):
    for r in par.runs:
        if r.font.name != 'Cambria Math': r.font.name = 'Times New Roman'
        r._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman') if r._element.rPr is not None and r._element.rPr.rFonts is not None else None
        r.font.size = Pt(size)
for st in d.styles:
    try:
        if st.type == 1: st.font.name = 'Times New Roman'
    except Exception: pass
for p in d.paragraphs:
    pf = p.paragraph_format; pf.line_spacing = 2.0; pf.space_before = Pt(0); pf.space_after = Pt(0)
    style_runs(p, 12)
for t in d.tables:
    for row in t.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.line_spacing = 1.0; style_runs(p, 10)
d.save(out); print('saved', out)
