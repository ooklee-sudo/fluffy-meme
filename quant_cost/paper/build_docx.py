"""Build the ISR review copy (double-spaced, 11 pt, 1-inch margins) from manuscript_study2.md.  python build_docx.py"""
import re, subprocess
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_LINE_SPACING
s = open("manuscript_study2.md", encoding="utf-8").read()
s = re.sub(r"^> .*\n\n", "", s, count=1, flags=re.M)            # internal draft banner
a = s.index("## References")
s = s[:a] + re.sub(r"Reference style follows.*?before submission\.\n\n", "", s[a:], flags=re.S)
open("/tmp/ms_review.md", "w", encoding="utf-8").write(s)
subprocess.run(["pandoc", "/tmp/ms_review.md", "-f", "markdown", "-o", "/tmp/ms_raw.docx"], check=True)
d = Document("/tmp/ms_raw.docx")
for sec in d.sections:
    sec.left_margin = sec.right_margin = sec.top_margin = sec.bottom_margin = Inches(1)
    sec.page_width, sec.page_height = Inches(8.5), Inches(11)
for st in d.styles:
    if st.type == 1:
        try:
            st.font.name = "Times New Roman"; st.font.size = Pt(11)
            if st.name.startswith("Heading") or st.name in ("Title", "Subtitle"):
                st.font.color.rgb = RGBColor(0, 0, 0); st.font.bold = True
        except Exception:
            pass
for para in d.paragraphs:
    pf = para.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.DOUBLE; pf.space_after = Pt(0); pf.space_before = Pt(0)
    for r in para.runs:
        r.font.name = "Times New Roman"; r.font.size = Pt(11)
        if para.style.name.startswith("Heading") or para.style.name == "Title":
            r.font.color.rgb = RGBColor(0, 0, 0); r.font.bold = True
        else:
            r.font.color.rgb = None
for t in d.tables:
    for row in t.rows:
        for c in row.cells:
            for para in c.paragraphs:
                para.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
                for r in para.runs:
                    r.font.name = "Times New Roman"; r.font.size = Pt(10)
d.save("manuscript_study2_isr_review_copy.docx")
print("saved")
