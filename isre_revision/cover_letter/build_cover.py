"""Build cover_letter.docx from cover_letter.md (Times 12 pt, 1.15 spacing, yellow [[placeholders]])."""
import os, re, subprocess
from docx import Document
from docx.enum.text import WD_COLOR_INDEX
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, "cover_letter.md")).read()
src = re.sub(r"(?m)^(Professor .*|Department Editor.*|\[\[Corresponding author name\]\]|\[\[Affiliation\]\])$", r"\1\\", src)
src = re.sub(r"\[\[(.*?)\]\]", lambda m: "[\\[\\[" + m.group(1) + "\\]\\]]{custom-style=\"Placeholder\"}", src, flags=re.S)
tmp, out = os.path.join(here, "_cl.md"), os.path.join(here, "cover_letter.docx")
open(tmp, "w").write(src)
subprocess.run(["pandoc", tmp, "-o", out], check=True)
os.remove(tmp)
d = Document(out)
for st in d.styles:
    try:
        st.font.name = "Times New Roman"
        rf = st.element.get_or_add_rPr().find(qn("w:rFonts"))
        if rf is not None:
            for a in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
                rf.attrib.pop(qn(a), None)
            for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
                rf.set(qn(a), "Times New Roman")
    except Exception:
        pass
names = [s.name for s in d.styles]
for name in ("Normal", "Body Text", "First Paragraph"):
    if name in names:
        st = d.styles[name]
        st.font.size, st.font.color.rgb = Pt(12), RGBColor(0, 0, 0)
        pf = st.paragraph_format
        pf.line_spacing, pf.space_before, pf.space_after, pf.first_line_indent = 1.15, Pt(0), Pt(10), Inches(0)
for p in d.paragraphs:
    for r in p.runs:
        if r.style is not None and r.style.name == "Placeholder":
            r.font.highlight_color = WD_COLOR_INDEX.YELLOW
for s in d.sections:
    s.page_width, s.page_height = Inches(8.5), Inches(11)
    for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(s, side, Inches(1))
d.core_properties.title = "Cover letter"
d.save(out)
print("wrote", out)
