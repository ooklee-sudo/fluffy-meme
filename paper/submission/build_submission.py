"""Build a blinded, ISR-formatted manuscript (11 pt, double-spaced, 1-inch margins) and report its page count.
Usage: python3 build_submission.py   (requires pandoc, python-docx, libreoffice)"""
import re, subprocess, shutil, os
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_LINE_SPACING
SRC = "../paper_ISR.md"; FIG = "../contracts/fig_sensitivity.png"
s = open(SRC).read()
s = re.sub(r"^---\n.*?\n---\n", "", s, count=1, flags=re.S)                      # drop internal status header
s = re.sub(r"\*\*Authors:\*\*.*\n\n", "", s)                                        # double-anonymous review: remove author line
s = s.replace("\\_", "_")                                                          # markdown escapes not needed in docx build
s = re.sub(r"`paper/[^`]*`", "the replication package (anonymized for review)", s)
s = s.replace("(contracts/fig_sensitivity.png){width=70%}", f"({os.path.abspath(FIG)}){{width=5.2in}}")
open("manuscript_blinded.md", "w").write(s)
subprocess.run(["pandoc", "--print-default-data-file", "reference.docx"], stdout=open("ref.docx", "wb"), check=True)
d = Document("ref.docx")
for st in d.styles:
    if st.type == 1 and st.font is not None:
        st.font.name = "Times New Roman"
        if st.name in ("Normal", "Body Text", "First Paragraph", "Compact", "Block Text", "Table"):
            st.font.size = Pt(11)
        pf = st.paragraph_format
        if st.name in ("Body Text", "First Paragraph", "Normal"):
            pf.line_spacing_rule = WD_LINE_SPACING.DOUBLE; pf.space_after = Pt(0); pf.space_before = Pt(0)
        if st.name == "Compact":
            pf.line_spacing_rule = WD_LINE_SPACING.SINGLE; pf.space_after = Pt(2); st.font.size = Pt(10)
        if st.name.startswith("Heading"): st.font.name = "Times New Roman"; st.font.size = Pt(12); st.font.bold = True
for sec in d.sections:
    sec.left_margin = sec.right_margin = sec.top_margin = sec.bottom_margin = Inches(1)
d.save("ref.docx")
subprocess.run(["pandoc", "manuscript_blinded.md", "-o", "manuscript_blinded.docx", "--reference-doc=ref.docx"], check=True)
subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "manuscript_blinded.docx"], check=True, capture_output=True)
from pypdf import PdfReader
r = PdfReader("manuscript_blinded.pdf"); n = len(r.pages)
txt = " ".join(p.extract_text() for p in r.pages)
refs_page = next((i+1 for i, p in enumerate(r.pages) if "Agrawal, A." in p.extract_text()), None)
print(f"Total pages: {n} (limit 38 incl. references/appendices/tables/figures); reference list starts on page {refs_page}; text pages before references ~ {refs_page-1 if refs_page else '?'} (limit 32)")
