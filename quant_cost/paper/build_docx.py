"""Build the Word files for the ISR submission from the markdown sources.  python build_docx.py

  ISR_manuscript_blinded.docx   double-spaced, 11 pt, 1-inch margins, no identifying information
  ISR_online_appendix.docx      same format (separate document, as the ISR guidelines allow)
  ISR_cover_letter.docx         single-spaced; seen by the editors only
"""
import re, subprocess
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_LINE_SPACING, WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


def add_page_number(section):
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    for kind, text in (("begin", None), (None, "PAGE"), ("end", None)):
        if kind:
            el = OxmlElement("w:fldChar"); el.set(qn("w:fldCharType"), kind)
        else:
            el = OxmlElement("w:instrText"); el.set(qn("xml:space"), "preserve"); el.text = text
        run._r.append(el)


def math_markup(s):
    """Turn plain-text sub- and superscripts into pandoc markup (s_b -> s~b~, m^(-1/g) -> m^-1/g^)."""
    # superscripts written as ^( ... ) with balanced parentheses
    out, i = [], 0
    while i < len(s):
        if s.startswith("^(", i):
            depth, j = 0, i + 1
            while j < len(s):
                depth += (s[j] == "(") - (s[j] == ")")
                if depth == 0:
                    break
                j += 1
            inner = s[i + 2:j].replace(" ", "\\ ")
            out.append("^" + inner + "^")
            i = j + 1
        else:
            out.append(s[i]); i += 1
    s = "".join(out)
    for tok in ("Q*", "λ*", "WTP*"):      # literal asterisks, not emphasis
        s = s.replace(tok, tok[:-1] + "\\*")
    s = re.sub(r"\^([γ])(?![\w(])", r"^\1^", s)
    s = re.sub(r"(?<![\w`/.])(s|w|p|λ|γ|S̄|c|D)_([a-z0-9]+(?:,[A-Z])?)(?![\w])", r"\1~\2~", s)
    return s


def build(src, out, double=True, strip_reference_note=False):
    s = open(src, encoding="utf-8").read()
    s = re.sub(r"^> .*\n\n", "", s, count=1, flags=re.M)             # internal draft banner
    if strip_reference_note and "## References" in s:
        a = s.index("## References")
        s = s[:a] + re.sub(r"Reference style follows.*?before submission\.\n\n", "", s[a:], flags=re.S)
    s = math_markup(s)
    open("/tmp/_tmp.md", "w", encoding="utf-8").write(s)
    subprocess.run(["pandoc", "/tmp/_tmp.md", "-f", "markdown", "--resource-path=.", "-o", "/tmp/_raw.docx"], check=True)
    d = Document("/tmp/_raw.docx")
    for sec in d.sections:
        sec.left_margin = sec.right_margin = sec.top_margin = sec.bottom_margin = Inches(1)
        sec.page_width, sec.page_height = Inches(8.5), Inches(11)
        add_page_number(sec)
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
        pf.line_spacing_rule = WD_LINE_SPACING.DOUBLE if double else WD_LINE_SPACING.SINGLE
        pf.space_before = Pt(0); pf.space_after = Pt(0 if double else 6)
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
    cp = d.core_properties
    for attr in ("author", "last_modified_by", "title", "subject", "comments", "keywords"):
        setattr(cp, attr, "")
    d.save(out)
    print("saved", out)


if __name__ == "__main__":
    build("manuscript_study2.md", "ISR_manuscript_blinded.docx", strip_reference_note=True)
    build("appendix_study2.md", "ISR_online_appendix.docx")
    build("cover_letter_isr.md", "ISR_cover_letter.docx", double=False)
