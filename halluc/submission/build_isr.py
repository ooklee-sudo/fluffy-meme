"""Build the ISR-formatted review files from manuscript/MANUSCRIPT.md.

Applies the requirements of the ISR submission guidelines as pasted by the authors (2026-10-28):
  * in-text citations as (Author Year) / Author (Year), no comma between name and year
  * references alphabetical by first author
  * double-spaced, >= 11-pt font, one-inch margins on all four sides (abstract, references and footnotes included)
  * analytical proofs and supplementary evidence moved to a separate online appendix
  * no author information in the review files
Outputs (in this folder): ISR_manuscript.md/.docx/.pdf, ISR_online_appendix.md/.docx/.pdf
"""
import re
import subprocess
import sys

from docx import Document
from docx.enum.text import WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

SRC = "../manuscript/MANUSCRIPT.md"
FONT, SIZE = "Times New Roman", 12
AUDIENCE = (
    "The paper is written for two audiences: researchers who study human–AI collaboration, information technology "
    "governance, and the management of machine-generated content, and managers who decide how the review of such content "
    "is staffed and prioritized. In the terminology of the journal's article types it is a paper that develops an analytical "
    "model and tests its implications out of sample on human annotations released by others.\n\n"
)

CITE = re.compile(r"([A-Z][A-Za-zçÇüÜéÉ'’\-]+(?: et al\.| and [A-Z][A-Za-zçÇüÜéÉ'’\-]+)?|Dell'Acqua et al\.),? ((?:19|20)\d\d[a-z]?)")


def fix_subscripts(text):
    """Markdown 'x_dt' / 'S_{a b}' -> pandoc subscripts (the manuscript has no snake_case other than math)."""
    text = re.sub(r"(?<=\S)_\{([^}]+)\}", lambda m: "~" + m.group(1).replace(" ", "\\ ") + "~", text)
    return re.sub(r"(?<=\S)_([A-Za-z0-9]+)", r"~\1~", text)


def fix_citations(text):
    return CITE.sub(lambda m: f"{m.group(1)} {m.group(2)}", text)


def sort_references(block):
    head, *entries = [e for e in re.split(r"\n\s*\n", block.strip()) if e.strip()]
    keep = [e for e in entries if e.startswith("[AUTHORS")]
    refs = [e for e in entries if not e.startswith("[AUTHORS")]
    key = lambda e: re.sub(r"[^a-z]", "", e.lower().replace("ç", "c").replace("ü", "u"))
    return "\n\n".join([head] + keep + sorted(refs, key=key)) + "\n"


def build_markdown():
    s = open(SRC).read()
    s = re.sub(r"\*Working draft\..*?\*\n\n---\n\n", "", s, flags=re.S)
    s = s.replace("\n---\n", "\n")
    a = s.index("## Appendix A. Proofs")
    r = s.index("## References")
    appendix, refs = s[a:r], s[r:]
    main = s[:a]
    main = main.replace("We make four contributions.", AUDIENCE + "We make four contributions.", 1)
    main = main.replace("| Collection | Documents | Sentences | Error rate | Lead / later | Fano (observed vs null) | *p* | τ |",
                        "| Collection | Docs | Sents. | Rate | Lead / later | Fano obs. / null | *p* | τ |")
    main = main.replace("Appendix A", "Online Appendix A").replace("Appendix B", "Online Appendix B")
    main = fix_subscripts(fix_citations(main))
    refs = sort_references(refs)
    appendix = fix_subscripts(fix_citations(appendix.replace("## Appendix A.", "## Online Appendix A.").replace("## Appendix B.", "## Online Appendix B.")))
    appendix = ("# Online Appendix to \"Where to Look First: Heterogeneity, Position, and the Value of Targeted Verification of "
                "Language-Model Output\"\n\n" + appendix)
    open("ISR_manuscript.md", "w").write(main + refs)
    open("ISR_online_appendix.md", "w").write(appendix)
    print("main words:", len((main + refs).split()), "| online appendix words:", len(appendix.split()))


def style_docx(path):
    d = Document(path)
    for sec in d.sections:
        sec.left_margin = sec.right_margin = sec.top_margin = sec.bottom_margin = Inches(1)
    by_name = {st.name.lower(): st for st in d.styles}

    def setup(st, size, bold=None, double=True):
        st.font.name, st.font.size = FONT, Pt(size)
        st.font.color.rgb = None
        if bold is not None:
            st.font.bold = bold
        rpr = st.element.get_or_add_rPr()
        rf = rpr.find(qn("w:rFonts"))
        if rf is None:
            rf = OxmlElement("w:rFonts")
            rpr.append(rf)
        for att in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
            if rf.get(qn(att)) is not None:
                del rf.attrib[qn(att)]
        for att in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
            rf.set(qn(att), FONT)
        pf = st.paragraph_format
        pf.line_spacing_rule = WD_LINE_SPACING.DOUBLE if double else WD_LINE_SPACING.SINGLE
        pf.space_after = Pt(0)
        pf.space_before = Pt(0)

    for n in ("normal", "body text", "first paragraph", "compact", "block text"):
        if n in by_name:
            setup(by_name[n], SIZE)
    for n, size in (("title", 14), ("heading 1", 12), ("heading 2", 12), ("heading 3", 12)):
        if n in by_name:
            setup(by_name[n], size, bold=True)
    for t in d.tables:
        ncol = len(t.columns)
        first = 0.34 if ncol > 2 else 0.5
        widths = [Inches(6.5 * first)] + [Inches(6.5 * (1 - first) / (ncol - 1))] * (ncol - 1)
        t.autofit = False
        tblPr = t._tbl.tblPr
        tw = tblPr.find(qn("w:tblW"))
        if tw is None:
            tw = OxmlElement("w:tblW")
            tblPr.append(tw)
        tw.set(qn("w:type"), "dxa")
        tw.set(qn("w:w"), str(int(6.5 * 1440)))
        borders = OxmlElement("w:tblBorders")
        for edge in ("top", "bottom", "insideH"):
            el = OxmlElement(f"w:{edge}")
            el.set(qn("w:val"), "single")
            el.set(qn("w:sz"), "4")
            el.set(qn("w:color"), "808080")
            borders.append(el)
        tblPr.append(borders)
        for col, w in zip(t.columns, widths):
            col.width = w
        for row in t.rows:
            for cell, w in zip(row.cells, widths):
                cell.width = w
        for row in t.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
                    for run in p.runs:
                        run.font.size, run.font.name = Pt(11), FONT
    for sec in d.sections:
        p = sec.footer.paragraphs[0] if sec.footer.paragraphs else sec.footer.add_paragraph()
        p.alignment = 1
        run = p.add_run()
        for kind, txt in (("begin", None), (None, "PAGE"), ("end", None)):
            if kind:
                el = OxmlElement("w:fldChar")
                el.set(qn("w:fldCharType"), kind)
            else:
                el = OxmlElement("w:instrText")
                el.set(qn("xml:space"), "preserve")
                el.text = txt
            run._r.append(el)
    cp = d.core_properties
    cp.author = cp.last_modified_by = cp.title = cp.subject = cp.comments = cp.keywords = ""
    body = d.element.body
    kids = list(body)
    for i, el in enumerate(kids[:-1]):
        if el.tag == qn("w:tbl") and kids[i + 1].tag == qn("w:p"):
            ppr = kids[i + 1].get_or_add_pPr()
            sp = OxmlElement("w:spacing")
            sp.set(qn("w:before"), "240")
            ppr.append(sp)
    d.save(path)


def pages(pdf):
    out = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
    m = re.search(r"Pages:\s+(\d+)", out)
    return int(m.group(1)) if m else None


if __name__ == "__main__":
    build_markdown()
    for base in ("ISR_manuscript", "ISR_online_appendix"):
        subprocess.run(["pandoc", f"{base}.md", "-o", f"{base}.docx", "--from", "markdown+pipe_tables"], check=True)
        style_docx(f"{base}.docx")
        subprocess.run(["soffice", "--headless", "--convert-to", "pdf", f"{base}.docx"], check=True, capture_output=True)
        print(base, "PDF pages:", pages(f"{base}.pdf"))
