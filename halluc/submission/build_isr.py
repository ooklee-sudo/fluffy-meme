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


INFORMS_REFS = [
    "Border KC, Sobel J (1987) Samurai accountant: A theory of auditing and plunder. *Rev. Econom. Stud.* 54(4):525–540.",
    "Bouayad L, Padmanabhan B, Chari K (2019) Audit policies under the sentinel effect: Deterrence-driven algorithms. *Inform. Systems Res.* 30(2):466–485.",
    "Buçinca Z, Malaya MB, Gajos KZ (2021) To trust or to think: Cognitive forcing functions can reduce overreliance on AI in AI-assisted decision-making. *Proc. ACM Human-Comput. Interaction* 5(CSCW1):Article 188.",
    "Catalini C, Hui X, Wu J (2026) Some simple economics of AGI. Preprint, arXiv:2602.20946. [AUTHORS: verify authors and status.]",
    "Cox DR (1955) Some statistical methods connected with series of events. *J. Roy. Statist. Soc. Ser. B* 17(2):129–164.",
    "Dell'Acqua F, McFowland E III, Mollick ER, Lifshitz-Assaf H, Kellogg K, Rajendran S, Krayer L, Candelon F, Lakhani KR (2023) Navigating the jagged technological frontier: Field experimental evidence of the effects of AI on knowledge worker productivity and quality. Working paper 24-013, Harvard Business School, Boston.",
    "Fügener A, Grahl J, Gupta A, Ketter W (2021) Will humans-in-the-loop become borgs? Merits and pitfalls of working with AI. *MIS Quart.* 45(3):1527–1556.",
    "Fügener A, Grahl J, Gupta A, Ketter W (2022) Cognitive challenges in human–artificial intelligence collaboration: Investigating the path toward productive delegation. *Inform. Systems Res.* 33(2):678–696.",
    "Gale D, Hellwig M (1985) Incentive-compatible debt contracts: The one-period problem. *Rev. Econom. Stud.* 52(4):647–663.",
    "Goel AL, Okumoto K (1979) Time-dependent error-detection rate model for software reliability and other performance measures. *IEEE Trans. Reliability* R-28(3):206–211.",
    "Goodhue DL, Thompson RL (1995) Task-technology fit and individual performance. *MIS Quart.* 19(2):213–236.",
    "Hawkes AG (1971) Spectra of some self-exciting and mutually exciting point processes. *Biometrika* 58(1):83–90.",
    "Ji Z, Lee N, Frieske R, Yu T, Su D, Xu Y, Ishii E, Bang YJ, Madotto A, Fung P (2023) Survey of hallucination in natural language generation. *ACM Comput. Surveys* 55(12):Article 248.",
    "Leng Y, Yuan Y (2026) SUVA: A probabilistic framework for auditing LLMs with an application to social preferences. *Inform. Systems Res.* 37(3):1805–1830.",
    "Manakul P, Liusie A, Gales MJF (2023) SelfCheckGPT: Zero-resource black-box hallucination detection for generative large language models. *Proc. 2023 Conf. Empirical Methods Natural Language Processing* (Association for Computational Linguistics).",
    "Marshall AW, Olkin I, Arnold BC (2011) *Inequalities: Theory of Majorization and Its Applications*, 2nd ed. (Springer, New York).",
    "Min S, Krishna K, Lyu X, Lewis M, Yih W, Koh PW, Iyyer M, Zettlemoyer L, Hajishirzi H (2023) FActScore: Fine-grained atomic evaluation of factual precision in long form text generation. *Proc. 2023 Conf. Empirical Methods Natural Language Processing* (Association for Computational Linguistics).",
    "Mitchell M, Wu S, Zaldivar A, Barnes P, Vasserman L, Hutchinson B, Spitzer E, Raji ID, Gebru T (2019) Model cards for model reporting. *Proc. Conf. Fairness, Accountability, Transparency* (ACM, New York), 220–229.",
    "Niu C, Wu Y, Zhu J, Xu S, Shum K, Zhong R, Song J, Zhang T (2024) RAGTruth: A hallucination corpus for developing trustworthy retrieval-augmented language models. *Proc. 62nd Annual Meeting Assoc. Comput. Linguistics* (Association for Computational Linguistics).",
    "Parasuraman R, Manzey DH (2010) Complacency and bias in human use of automation: An attentional integration. *Human Factors* 52(3):381–410.",
    "Si C, et al. (2024) Large language models help humans verify truthfulness—except when they are convincingly wrong. *Proc. 2024 Conf. North Amer. Chapter Assoc. Comput. Linguistics* (Association for Computational Linguistics). arXiv:2310.12558. [AUTHORS: complete author list and venue.]",
    "Taudien A, Fügener A, Gupta A, Ketter W (2026) Enhancing AI use: How complementary system information drives delegation frequency and effectiveness. *Inform. Systems Res.* Published online ahead of print September 4, https://doi.org/10.1287/isre.2024.1330. [AUTHORS: update volume and pages if the article has appeared in an issue.]",
    "Townsend RM (1979) Optimal contracts and competitive markets with costly state verification. *J. Econom. Theory* 21(2):265–293.",
    "Tu, et al. (2025) Investigating factuality in long-form text generation: The roles of self-known and self-unknown. *Proc. 2025 Conf. Empirical Methods Natural Language Processing*. arXiv:2411.15993. [AUTHORS: complete author list.]",
    "Vasconcelos H, Jörke M, Grunde-McLaughlin M, Gerstenberg T, Bernstein MS, Krishna R (2023) Explanations can reduce overreliance on AI systems during decision-making. *Proc. ACM Human-Comput. Interaction* 7(CSCW1):Article 129.",
    "Wei J, et al. (2024) Long-form factuality in large language models. *Adv. Neural Inform. Processing Systems*, vol. 37. arXiv:2403.18802. [AUTHORS: complete author list.]",
    "Yang, et al. (2025) Hallucinate at the last in long response generation: A case study on long document summarization. Preprint, arXiv:2505.15291. [AUTHORS: complete author list and venue.]",
    "Zhang M, Press O, Merrill W, Liu A, Smith NA (2024) How language model hallucinations can snowball. *Proc. 41st Internat. Conf. Machine Learn.* (PMLR).",
]


def sort_references(block):
    def key(e):  # first-author surname and initials, then year (same authors in chronological order)
        authors = e.split(" (")[0].lower().replace("ç", "c").replace("ü", "u")
        year = re.search(r"\((\d{4})\)", e)
        return re.sub(r"[^a-z]", "", authors) + (year.group(1) if year else "0000")
    head = "## References\n\n[AUTHORS: every entry must be verified against the original source. Format follows the pattern of reference lists in published ISR articles (surname and initials, year in parentheses, abbreviated journal names); the official INFORMS reference-style guide has not been read, so abbreviations may need adjustment.]"
    return head + "\n\n" + "\n\n".join(sorted(INFORMS_REFS, key=key)) + "\n"


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
