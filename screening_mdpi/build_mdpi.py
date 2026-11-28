"""Convert the IEEE TAI version of "Combining Detectors That Fail Differently..." to the MDPI Electronics layout.

Usage: python build_mdpi.py SOURCE_TAI.docx MDPI_BASE.docx OUT.docx "AFFILIATION LINE" [CORR_EMAIL COAUTHOR]
With a co-author, the corresponding author (first author) is starred, a Correspondence line is added, the back matter
uses plural wording, and an Author Contributions statement is added (with a highlighted part to complete).
Contact details are passed in at run time so that none are stored in the repository.
SOURCE is nmi_screening/TAI_Manuscript.docx (branch claude/ecstatic-fermi-i6ec13); BASE is any Word file built on the
MDPI Electronics template (its MDPI_* styles, header and footer are reused; its body is replaced).
"""
import copy
import io
import re
import sys

import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm

SRC, BASE, OUT = sys.argv[1:4]
AFFILIATION = sys.argv[4] if len(sys.argv) > 4 else "Department, University, City, Country; e-mail"
CORR_EMAIL = sys.argv[5] if len(sys.argv) > 5 else ""
COAUTHOR = sys.argv[6] if len(sys.argv) > 6 else ""
PLURAL = bool(COAUTHOR)
src, out = docx.Document(SRC), docx.Document(BASE)

TITLE = "Combining Detectors That Fail Differently Defends Screens for Machine-Written Scholarly Text Against Adaptive Authors"
KEYWORDS = ("adversarial robustness; AI-generated text detection; ensemble methods; large language models; "
            "research integrity; zero-shot detection")

HEAD1 = {"I": "1. Introduction", "II": "2. Related Work", "III": "3. Threat Model and Problem",
         "IV": "4. Proposed Defence", "V": "5. Experimental Setup", "VI": "6. Results",
         "VII": "7. Discussion and Limitations", "VIII": "8. Conclusions"}
ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8}
HEAD2 = {"Data artifacts": "Data Artifacts", "Detection without attack": "Detection without Attack",
         "Attacks and guided attacks": "Attacks and Guided Attacks",
         "Inversion and the two-sided score": "Inversion and the Two-Sided Score",
         "Operating point": "Operating Point", "A new field and the artifact control": "A New Field and the Artifact Control"}
TABLES = [  # caption, footer
    ("AUC without attack (186 evaluation humans, 100 machine papers per generator).", "* Proposed components."),
    ("Worst case under attack: AUC without attack → lowest AUC over eight attacks (attack).", None),
    ("Share flagged at the calibrated 5% threshold (mean over generators) and false-positive rate (FPR) on evaluation humans.", None),
    ("Economics papers: AUC without attack/with 50% human sentences.", None),
    ("Artifact control for the TF-IDF classifier.", None),
]
FIGS = [
    "AUC of every method under every attack, by generator. Rows below the white line are the proposed components and the judge. Blank: not run.",
    "(a) Lowest AUC over four generators and eight attacks per method; proposed components in blue. (b) AUC on Claude papers by attack for Fast-DetectGPT, the two-sided score and the mean ensemble.",
]
# MDPI reference style; *italic* and **bold** are rendered as such.
REFS = [
    "Liang, W.; et al. Quantifying large language model usage in scientific papers. *Nat. Hum. Behav.* **2025**. https://doi.org/10.1038/s41562-025-02273-8.",
    "Kobak, D.; Gonzalez-Marquez, R.; Horvát, E.-A.; Lause, J. Delving into LLM-assisted writing in biomedical publications through excess vocabulary. *Sci. Adv.* **2025**, *11*.",
    "Gehrmann, S.; Strobelt, H.; Rush, A. GLTR: Statistical detection and visualization of generated text. In Proceedings of the 57th Annual Meeting of the Association for Computational Linguistics: System Demonstrations, Florence, Italy, 2019; pp. 111–116.",
    "Mitchell, E.; Lee, Y.; Khazatsky, A.; Manning, C.D.; Finn, C. DetectGPT: Zero-shot machine-generated text detection using probability curvature. In Proceedings of the 40th International Conference on Machine Learning (ICML), Honolulu, HI, USA, 2023.",
    "Bao, G.; Zhao, Y.; Teng, Z.; Yang, L.; Zhang, Y. Fast-DetectGPT: Efficient zero-shot detection of machine-generated text via conditional probability curvature. In Proceedings of the International Conference on Learning Representations (ICLR), Vienna, Austria, 2024.",
    "Hans, A.; et al. Spotting LLMs with Binoculars: Zero-shot detection of machine-generated text. In Proceedings of the 41st International Conference on Machine Learning (ICML), Vienna, Austria, 2024.",
    "Solaiman, I.; et al. Release strategies and the social impacts of language models. *arXiv* **2019**, arXiv:1908.09203.",
    "Verma, V.; Fleisig, E.; Tomlin, N.; Klein, D. Ghostbuster: Detecting text ghostwritten by large language models. In Proceedings of the 2024 Conference of the North American Chapter of the Association for Computational Linguistics (NAACL), Mexico City, Mexico, 2024.",
    "Krishna, K.; Song, Y.; Karpinska, M.; Wieting, J.; Iyyer, M. Paraphrasing evades detectors of AI-generated text, but retrieval is an effective defense. In Advances in Neural Information Processing Systems 36 (NeurIPS 2023), New Orleans, LA, USA, 2023.",
    "Sadasivan, V.S.; Kumar, A.; Balasubramanian, S.; Wang, W.; Feizi, S. Can AI-generated text be reliably detected? *Trans. Mach. Learn. Res.* **2025**.",
    "Wang, Y.; et al. Stumbling blocks: Stress testing the robustness of machine-generated text detectors under attacks. In Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (ACL), Bangkok, Thailand, 2024; pp. 2894–2925.",
    "Huang, G.; et al. Are AI-generated text detectors robust to adversarial perturbations? In Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (ACL), Bangkok, Thailand, 2024; pp. 6005–6024.",
    "Cheng, Y.; Sadasivan, V.S.; Saberi, M.; Saha, S.; Feizi, S. Adversarial paraphrasing: A universal attack for humanizing AI-generated text. In Advances in Neural Information Processing Systems 38 (NeurIPS 2025), 2025.",
    "Li, Y.; et al. MAGE: Machine-generated text detection in the wild. In Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (ACL), Bangkok, Thailand, 2024; pp. 36–53.",
    "Dugan, L.; et al. RAID: A shared benchmark for robust evaluation of machine-generated text detectors. In Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (ACL), Bangkok, Thailand, 2024; pp. 12463–12492.",
    "Wang, Y.; et al. M4: Multi-generator, multi-domain, and multi-lingual black-box machine-generated text detection. In Proceedings of the 18th Conference of the European Chapter of the Association for Computational Linguistics (EACL), St. Julian’s, Malta, 2024; pp. 1369–1407.",
    "Dingfelder, P.; Riess, C. Contamination in generated text detection benchmarks. *arXiv* **2025**, arXiv:2511.09200.",
    "Pudasaini, S.; Miralles-Pechuán, L.; Lillis, D.; Llorens Salvador, M. Why AI-generated text detection fails: Evidence from explainable AI beyond benchmark accuracy. *arXiv* **2026**, arXiv:2603.23146.",
    "Desaire, H.; Chua, A.E.; Isom, M.; Jarosova, R.; Hua, D. Distinguishing academic science writing from humans or ChatGPT with over 99% accuracy using off-the-shelf machine learning tools. *Cell Rep. Phys. Sci.* **2023**, *4*, 101426.",
    "Mosca, E.; Abdalla, M.H.I.; Basso, P.; Musumeci, M.; Groh, G. Distinguishing fact from fiction: A benchmark dataset for identifying machine-generated scientific papers in the LLM era. In Proceedings of the 3rd Workshop on Trustworthy Natural Language Processing (TrustNLP), Toronto, ON, Canada, 2023; pp. 190–207.",
    "Yu, S.; Luo, M.; Madasu, A.; Lal, V.; Howard, P. Is your paper being reviewed by an LLM? Benchmarking AI text detection in peer review. In Proceedings of the International Conference on Learning Representations (ICLR), 2026.",
    "Pu, X.; Zhang, J.; Han, X.; Tsvetkov, Y.; He, T. On the zero-shot generalization of machine-generated text detectors. In Findings of the Association for Computational Linguistics: EMNLP 2023, Singapore, 2023; pp. 4799–4808.",
    "Zheng, L.; et al. Judging LLM-as-a-judge with MT-Bench and Chatbot Arena. In Advances in Neural Information Processing Systems 36 (NeurIPS 2023), New Orleans, LA, USA, 2023.",
    "Panickssery, A.; Bowman, S.R.; Feng, S. LLM evaluators recognize and favor their own generations. In Advances in Neural Information Processing Systems 37 (NeurIPS 2024), Vancouver, BC, Canada, 2024.",
    "Kirchenbauer, J.; Geiping, J.; Wen, Y.; Katz, J.; Miers, I.; Goldstein, T. A watermark for large language models. In Proceedings of the 40th International Conference on Machine Learning (ICML), Honolulu, HI, USA, 2023; pp. 17061–17084.",
    "Zhang, H.; et al. Watermarks in the sand: Impossibility of strong watermarking for generative models. In Proceedings of the 41st International Conference on Machine Learning (ICML), Vienna, Austria, 2024.",
    "Liang, W.; Yuksekgonul, M.; Mao, Y.; Wu, E.; Zou, J. GPT detectors are biased against non-native English writers. *Patterns* **2023**, *4*, 100779.",
    "Wu, J.; Yang, S.; Zhan, R.; Yuan, Y.; Chao, L.S.; Wong, D.F. A survey on LLM-generated text detection: Necessity, methods, and future directions. *Comput. Linguist.* **2025**, *51*, 275–338.",
    "Zhou, Y.; He, B.; Sun, L. Navigating the shadows: Unveiling effective disturbances for modern AI content detectors. In Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (ACL), Bangkok, Thailand, 2024; pp. 10847–10861.",
    "Creo, A.; Pudasaini, S. SilverSpeak: Evading AI-generated text detectors using homoglyphs. In Proceedings of the 1st Workshop on GenAI Content Detection (GenAIDetect), Abu Dhabi, United Arab Emirates, 2025; pp. 1–46.",
    "Shi, Z.; Wang, Y.; Yin, F.; Chen, X.; Chang, K.-W.; Hsieh, C.-J. Red teaming language model detectors with language models. *Trans. Assoc. Comput. Linguist.* **2024**, *12*, 174–189.",
    "Koike, R.; Kaneko, M.; Okazaki, N. OUTFOX: LLM-generated essay detection through in-context learning with adversarially generated examples. In Proceedings of the AAAI Conference on Artificial Intelligence, Vancouver, BC, Canada, 2024; Volume 38, pp. 21258–21266.",
    "David, I.; Gervais, A. AuthorMist: Evading AI text detectors with reinforcement learning. *arXiv* **2025**, arXiv:2503.08716.",
    "Ranganath, S.; Ramesh, A. StealthRL: Reinforcement learning paraphrase attacks for multi-detector evasion of AI-text detectors. *arXiv* **2026**, arXiv:2602.08934.",
    "Wu, J.; et al. DetectRL: Benchmarking LLM-generated text detection in real-world scenarios. In Advances in Neural Information Processing Systems 37 (NeurIPS 2024), Datasets and Benchmarks Track, Vancouver, BC, Canada, 2024.",
    "Gritsai, G.; Voznyuk, A.; Grabovoy, A.; Chekhovich, Y. Are AI detectors good enough? A survey on quality of datasets with machine-generated texts. *arXiv* **2024**, arXiv:2410.14677.",
    "Cameron, A.C.; Trivedi, P.K. *Regression Analysis of Count Data*, 2nd ed.; Cambridge University Press: Cambridge, UK, 2013.",
]
BACK = ([("Author Contributions: ", "Conceptualization, O.L.; methodology, O.L.; software, O.L.; formal analysis, O.L.; "
          "writing—original draft preparation, O.L.; writing—review and editing, O.L. and Y.N.; "
          "[[add Y.N.'s other roles, e.g., data curation, validation, investigation]]. "
          "All authors have read and agreed to the published version of the manuscript.")] if PLURAL else []) + [
    ("Funding: ", "This research received no external funding."),
    ("Institutional Review Board Statement: ", "Not applicable."),
    ("Informed Consent Statement: ", "Not applicable."),
    ("Data Availability Statement: ", "The code, machine-generated corpora, per-document scores and result tables are openly "
     "available on Zenodo at https://doi.org/10.5281/zenodo.23664508 (version 2). The human papers are public and can be "
     "re-collected from the identifier lists provided."),
    ("Acknowledgments: ", "The machine-written papers studied here were produced by GPT-4o, Claude Sonnet 5.5, Llama 3.3 70B "
     "Instruct and DeepSeek V4.1 Flash, and Gemini 2.5 Pro served as a judge. During the preparation of this manuscript, the "
     + ("authors" if PLURAL else "author") + " used an AI coding assistant (Claude Code) to write and run the analysis code "
     "and to draft and edit the manuscript text. The " + ("authors have" if PLURAL else "author has") + " reviewed and "
     "edited the output and " + ("take" if PLURAL else "takes") + " full responsibility for the content of this publication."),
    ("Conflicts of Interest: ", "The " + ("authors declare" if PLURAL else "author declares") + " no conflicts of interest."),
]
ABBREV = [("AUC", "area under the receiver operating characteristic curve"), ("FPR", "false-positive rate"),
          ("LLM", "large language model"), ("MAD", "median absolute deviation"),
          ("TF-IDF", "term frequency–inverse document frequency")]


# ---------------------------------------------------------------- helpers
def compress_citations(text: str) -> str:
    """'[9], [10], [11]' -> '[9–11]'; '[1], [2]' -> '[1,2]'."""
    def repl(m):
        nums = sorted({int(n) for n in re.findall(r"\d+", m.group(0))})
        parts, i = [], 0
        while i < len(nums):
            j = i
            while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
                j += 1
            parts.append(f"{nums[i]}–{nums[j]}" if j - i >= 2 else ",".join(map(str, nums[i:j + 1])))
            i = j + 1
        return "[" + ",".join(parts) + "]"
    return re.sub(r"\[\d+\](?:,\s*\[\d+\])*", repl, text)


def fix_refs(text: str) -> str:
    text = compress_citations(text)
    text = re.sub(r"\bTables? (VIII|VII|VI|IV|V|III|II|I)\b(?: and (VIII|VII|VI|IV|V|III|II|I)\b)?",
                  lambda m: ("Tables " if m.group(2) else "Table ") + str(ROMAN[m.group(1)])
                  + (f" and {ROMAN[m.group(2)]}" if m.group(2) else ""), text)
    text = re.sub(r"\bFig\. (\d)", r"Figure \1", text)
    text = re.sub(r"\bSection (VIII|VII|VI|IV|V|III|II|I)\b", lambda m: f"Section {ROMAN[m.group(1)]}", text)
    return text


def add_par(style: str, runs=None, text: str = None):
    p = out.add_paragraph(style=style)
    if text is not None:
        p.add_run(text)
    for r in runs or []:
        nr = p.add_run(fix_refs(r.text))
        nr.bold, nr.italic = r.bold, r.italic
        if r.font.subscript:
            nr.font.subscript = True
        if r.font.superscript:
            nr.font.superscript = True
    return p


def add_marked(style: str, text: str):
    """Paragraph with *italic* and **bold** markup."""
    p = out.add_paragraph(style=style)
    for tok in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*)", text):
        if not tok:
            continue
        if tok.startswith("**"):
            p.add_run(tok[2:-2]).bold = True
        elif tok.startswith("*"):
            p.add_run(tok[1:-1]).italic = True
        else:
            p.add_run(tok)
    return p


def set_runs(p, *pieces):
    """Replace a paragraph's text, keeping its first runs' formatting: pieces = [(text, bold), ...]."""
    for r in p.runs[len(pieces):]:
        r._r.getparent().remove(r._r)
    for k, (t, b) in enumerate(pieces):
        if k < len(p.runs):
            p.runs[k].text = t
            p.runs[k].bold = b
            p.runs[k].font.superscript = None
        else:
            p.add_run(t).bold = b


def add_table(tbl_el, caption: str, footer):
    add_marked("MDPI_4.1_table_caption", f"**Table {add_table.n}.** {caption}")
    add_table.n += 1
    el = copy.deepcopy(tbl_el)
    tblPr = el.find(qn("w:tblPr"))
    for tag in ("w:tblBorders", "w:tblStyle", "w:tblW", "w:tblInd", "w:jc", "w:tblLayout"):
        for x in tblPr.findall(qn(tag)):
            tblPr.remove(x)
    style = OxmlElement("w:tblStyle"); style.set(qn("w:val"), out.styles["MDPI_4.1_three_line_table"].style_id)
    tblPr.insert(0, style)
    w = OxmlElement("w:tblW"); w.set(qn("w:w"), "5000"); w.set(qn("w:type"), "pct"); tblPr.append(w)
    jc = OxmlElement("w:jc"); jc.set(qn("w:val"), "center"); tblPr.append(jc)
    for tag in ("w:tcBorders", "w:tcW", "w:shd"):
        for x in el.iter(qn(tag)):
            x.getparent().remove(x)
    body_style = out.styles["MDPI_4.2_table_body"].style_id
    for p in el.iter(qn("w:p")):
        pPr = p.find(qn("w:pPr"))
        if pPr is None:
            pPr = OxmlElement("w:pPr"); p.insert(0, pPr)
        for x in pPr.findall(qn("w:pStyle")):
            pPr.remove(x)
        ps = OxmlElement("w:pStyle"); ps.set(qn("w:val"), body_style); pPr.insert(0, ps)
        for x in pPr.findall(qn("w:jc")):
            pPr.remove(x)
        for sz in p.iter(qn("w:sz")):
            sz.getparent().remove(sz)
        for sz in p.iter(qn("w:szCs")):
            sz.getparent().remove(sz)
    # three-line rule: top and bottom of the table, line under the header row
    borders = OxmlElement("w:tblBorders")
    for side, val in (("top", "single"), ("bottom", "single"), ("left", "nil"), ("right", "nil"),
                      ("insideH", "nil"), ("insideV", "nil")):
        b = OxmlElement(f"w:{side}"); b.set(qn("w:val"), val)
        if val == "single":
            b.set(qn("w:sz"), "8"); b.set(qn("w:space"), "0"); b.set(qn("w:color"), "auto")
        borders.append(b)
    tblPr.append(borders)
    first = el.find(qn("w:tr"))
    for tc in first.findall(qn("w:tc")):
        tcPr = tc.find(qn("w:tcPr"))
        if tcPr is None:
            tcPr = OxmlElement("w:tcPr"); tc.insert(0, tcPr)
        tb = OxmlElement("w:tcBorders"); bt = OxmlElement("w:bottom")
        bt.set(qn("w:val"), "single"); bt.set(qn("w:sz"), "4"); bt.set(qn("w:space"), "0"); bt.set(qn("w:color"), "auto")
        tb.append(bt); tcPr.append(tb)
    out.element.body.insert(len(out.element.body) - 1, el)
    if footer:
        add_par("MDPI_4.3_table_footer", text=footer)


add_table.n = 1


def add_figure(blob: bytes, caption: str):
    p = out.add_paragraph(style="MDPI_5.2_figure")
    p.add_run().add_picture(io.BytesIO(blob), width=Cm(13.0))
    add_marked("MDPI_5.1_figure_caption", f"**Figure {add_figure.n}.** {caption}")
    add_figure.n += 1


add_figure.n = 1

# ---------------------------------------------------------------- front matter (edit the base's own paragraphs)
body = out.element.body
kids = list(body.iterchildren())
keep = 8  # article type, title, authors, affiliation, correspondence, abstract, keywords, line
for el in kids[keep:]:
    if not el.tag.endswith("sectPr"):
        body.remove(el)
P = out.paragraphs
set_runs(P[1], (TITLE, None))
if PLURAL:
    set_runs(P[2], ("Ook Lee", None), ("*", None), (" and ", None), (COAUTHOR, None))
    P[2].runs[1].font.superscript = True
else:
    set_runs(P[2], ("Ook Lee", None))
# The affiliation line (with e-mail) is passed in so that no contact details live in the repository.
set_runs(P[3], (AFFILIATION, None))
if PLURAL:
    set_runs(P[4], ("*", True), (f"\tCorrespondence: {CORR_EMAIL}", None))
else:
    P[4]._p.getparent().remove(P[4]._p)  # single author: no separate correspondence line
src_par = src.paragraphs
abstract = src_par[2].text.split("—", 1)[1].strip()
P = out.paragraphs
k = 5 if PLURAL else 4
set_runs(P[k], ("Abstract: ", True), (abstract, None))
set_runs(P[k + 1], ("Keywords: ", True), (KEYWORDS, None))
out.add_paragraph(style="MDPI_1.9_line")

# ---------------------------------------------------------------- body
table_i = fig_i = 0
after_equation = False
started = False
for el in src.element.body.iterchildren():
    tag = el.tag.split("}")[1]
    if tag == "tbl":
        cap, foot = TABLES[table_i]
        add_table(el, cap, foot)
        table_i += 1
        continue
    if tag != "p":
        continue
    p = docx.text.paragraph.Paragraph(el, src)
    t = p.text.strip()
    if el.findall(".//" + qn("w:drawing")):
        rid = el.find(".//" + qn("a:blip")).get(qn("r:embed"))
        add_figure(src.part.related_parts[rid].blob, FIGS[fig_i])
        fig_i += 1
        continue
    if not t:
        continue
    m1 = re.match(r"^(VIII|VII|VI|IV|V|III|II|I)\. [A-Z ]+$", t)
    if m1:
        started = True
        add_par("MDPI_2.1_heading1", text=HEAD1[m1.group(1)])
        sec_no, sub_no = ROMAN[m1.group(1)], 0
        continue
    if not started:
        continue
    if t in ("DATA AVAILABILITY", "ACKNOWLEDGMENT", "REFERENCES"):
        break
    m2 = re.match(r"^([A-F])\. (.+)$", t)
    if m2 and len(t) < 60 and not t.endswith("."):
        sub_no += 1
        add_par("MDPI_2.2_heading2", text=f"{sec_no}.{sub_no}. {HEAD2.get(m2.group(2), m2.group(2))}")
        continue
    if t.startswith(("Fig. ", "TABLE ")):
        continue  # captions are rebuilt
    if t.startswith("•"):
        runs = list(p.runs)
        q = add_par("MDPI_3.7_itemize", runs)
        if q.runs and q.runs[0].text.startswith("•"):
            q.runs[0].text = q.runs[0].text.lstrip("• ").lstrip()
        continue
    if re.search(r"\t\(\d\)$", t):
        add_par("MDPI_3.9_equation", list(p.runs))
        after_equation = True
        continue
    style = "MDPI_3.1_text"
    if t.endswith(":"):
        style = "MDPI_3.5_text_before_list"
    elif after_equation and t[:1].islower():
        style = "MDPI_3.2_text_no_indent"
    after_equation = False
    add_par(style, list(p.runs))

# ---------------------------------------------------------------- back matter
from docx.enum.text import WD_COLOR_INDEX
for label, text in BACK:
    q = out.add_paragraph(style="MDPI_6.2_back_matter")
    q.add_run(label).bold = True
    for tok in re.split(r"(\[\[[^\]]+\]\])", text):
        if tok.startswith("[["):
            q.add_run(tok[2:-2]).font.highlight_color = WD_COLOR_INDEX.YELLOW  # to be completed by the authors
        elif tok:
            q.add_run(tok)
q = out.add_paragraph(style="MDPI_6.2_back_matter"); q.add_run("Abbreviations").bold = True
add_par("MDPI_6.2_back_matter", text="The following abbreviations are used in this manuscript:")
for a, b in ABBREV:
    add_par("MDPI_6.2_back_matter", text=f"{a}\t{b}")
add_par("MDPI_2.1_heading1", text="References")
for k, r in enumerate(REFS, 1):
    add_marked("MDPI_8.1_references", r)

assert table_i == len(TABLES) and fig_i == len(FIGS), (table_i, fig_i)
out.save(OUT)
print(f"wrote {OUT}: {table_i} tables, {fig_i} figures, {len(REFS)} references")
