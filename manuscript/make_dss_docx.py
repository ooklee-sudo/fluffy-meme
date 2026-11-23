"""Word version of dss_manuscript.tex (elsarticle) for reading and editing, via the converter in make_ijds_docx.py.

Usage:  python make_dss_docx.py      (needs pandoc; writes dss_manuscript.docx)
"""
import os
import re
import subprocess
import tempfile

import make_ijds_docx as M

HERE = os.path.dirname(os.path.abspath(__file__))


def to_informs_macros(src):
    """Rewrite the elsarticle front matter and appendix markup into the macros make_ijds_docx understands."""
    fm = src[src.index("\\begin{frontmatter}"):src.index("\\end{frontmatter}")]
    title = M.macro_arg(fm, "title")
    author = re.sub(r"\\corref\{[^}]*\}", "", fm[fm.index("\\author[") :].split("]", 1)[1].split("\n")[0]).strip()[1:-1]
    c = fm.index("{", fm.index("\\cortext["))
    email = fm[c + 1:M.find_close(fm, c)].replace("Corresponding author. ", "")
    email = re.sub(r"\\todo\{([^}]*)\}", r"[\1]", email)
    aff = fm[fm.index("\\address["):].split("]", 1)[1].split("\n")[0].strip()[1:-1]
    abstract = fm[fm.index("\\begin{abstract}") + 16:fm.index("\\end{abstract}")].strip()
    kw = fm[fm.index("\\begin{keyword}") + 15:fm.index("\\end{keyword}")].strip().replace(" \\sep ", "; ")
    body = src[src.index("\\end{frontmatter}") + len("\\end{frontmatter}"):]
    body = body.replace("\\appendix", "\\begin{APPENDICES}").replace("\\bibliographystyle", "\\end{APPENDICES}\n\\bibliographystyle")
    body = re.sub(r"\\begin\{adjustbox\}\{[^}]*\}\n?|\n?\\end\{adjustbox\}", "", body)
    body = body.replace("\\todo{", "\\pending{")
    # in Word, signed numbers and footnote marks read better as plain text than as equations
    body = re.sub(r"\$([+-])(\d[\d.]*)\$", lambda m: ("\u2212" if m.group(1) == "-" else "+") + m.group(2), body)
    for mark, ch in (("\\dagger", "\u2020"), ("\\ddagger", "\u2021"), ("\\ast", "*")):
        body = body.replace("$^" + mark + "$", "\\textsuperscript{" + ch + "}")
    body = body.replace("$<0$", "<0")
    body = body.replace("\\ref{app:", "Appendix~\\ref{app:")  # elsarticle's \ref already prints "Appendix X"
    return (f"\\TITLE{{{title}}}\n\\AUTHOR{{{author}}}\n\\AFF{{{aff}, {email}}}\n\\ABSTRACT{{{abstract}}}\n"
            f"\\KEYWORDS{{{kw}}}\n\\maketitle\n{body}")


def main():
    src = open(os.path.join(HERE, "dss_manuscript.tex"), encoding="utf-8").read()
    bib = M.parse_bib(os.path.join(HERE, "dss_refs.bib"))
    body, refs = M.convert(to_informs_macros(src), bib)
    refs_tex = re.sub(r"\*([^*]+)\*", r"\\emph{\1}", refs).replace("&", "\\&")
    out = os.path.join(HERE, "dss_manuscript.docx")
    with tempfile.TemporaryDirectory() as td:
        bt = os.path.join(td, "body.tex")
        open(bt, "w", encoding="utf-8").write("\\documentclass{article}\\begin{document}\n" + body
                                              + "\n\\section*{References}\n\n" + refs_tex + "\n\\end{document}\n")
        subprocess.run(["pandoc", bt, "-f", "latex", "--reference-doc", os.path.join(HERE, "submission_reference.docx"), "-o", out], check=True)
    polish(out)
    print("saved", out)


def polish(path):
    """Centre the title block, unindent abstract and keywords, and size table columns to their content."""
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Inches, Emu
    doc = Document(path)
    ps = doc.paragraphs
    for p in ps:  # title, author, affiliation: everything before the abstract
        if p.text.startswith("Abstract."):
            break
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Inches(0)
    for p in ps[:8]:
        if p.text.startswith(("Abstract.", "Key words:")):
            p.paragraph_format.first_line_indent = Inches(0)
            p.paragraph_format.space_before = Inches(0.15)
    from docx.enum.text import WD_LINE_SPACING
    from docx.shared import Pt
    for t in doc.tables:  # table cells: no first-line indent, single spacing, 10 pt
        for p in t._tbl.iter(qn("w:p")):
            from docx.text.paragraph import Paragraph
            par = Paragraph(p, None)
            pf = par.paragraph_format
            pf.first_line_indent = Inches(0); pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
            pf.space_before = Pt(1); pf.space_after = Pt(1)
            for r in par.runs:
                r.font.size = Pt(10)
    total = Inches(6.5)
    for t in doc.tables:
        ncol = len(t.columns)
        need = [0.5] * ncol  # inches needed to keep each column's data cells on one line (headers may wrap)
        for ri, tr in enumerate(t._tbl.tr_lst):
            if ri == 0:
                continue
            tcs = tr.tc_lst
            if len(tcs) != ncol:  # merged section-label row
                continue
            for jj, tc in enumerate(tcs):
                L = len(" ".join("".join(tc.itertext()).split()))
                inch = 0.18 + 0.068 * L * (1.3 if tc.find(".//" + qn("m:oMath")) is not None else 1.0)
                need[jj] = max(need[jj], inch)
        if sum(need) > 6.5:
            need = [x * 6.5 / sum(need) for x in need]
        else:  # spread the spare width in proportion to need
            spare = 6.5 - sum(need)
            need = [x + spare * x / sum(need) for x in need]
        widths = [Inches(x) for x in need]
        tblPr = t._tbl.tblPr
        for el in tblPr.findall(qn("w:tblW")):
            tblPr.remove(el)
        for tag in ("w:tblLayout", "w:tblW"):
            for el in tblPr.findall(qn(tag)):
                tblPr.remove(el)
        tw = OxmlElement("w:tblW"); tw.set(qn("w:w"), str(int(Emu(total).inches * 1440))); tw.set(qn("w:type"), "dxa")
        lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed")
        style = tblPr.find(qn("w:tblStyle"))  # schema order: tblStyle, tblW, ..., tblLayout, ..., tblLook, tblCaption
        (style.addnext(tw) if style is not None else tblPr.insert(0, tw))
        look = tblPr.find(qn("w:tblLook"))
        (look.addprevious(lay) if look is not None else tblPr.append(lay))
        grid = t._tbl.tblGrid
        for gc, w in zip(grid.findall(qn("w:gridCol")), widths):
            gc.set(qn("w:w"), str(int(Emu(w).inches * 1440)))
        for tr in t._tbl.tr_lst:
            j = 0
            for tc in tr.tc_lst:
                span = tc.tcPr.find(qn("w:gridSpan")) if tc.tcPr is not None else None
                n = int(span.get(qn("w:val"))) if span is not None else 1
                tcw = tc.get_or_add_tcPr().get_or_add_tcW()
                tcw.set(qn("w:type"), "dxa"); tcw.set(qn("w:w"), str(int(Emu(sum(widths[j:j + n])).inches * 1440)))
                j += n
    doc.save(path)


if __name__ == "__main__":
    main()
