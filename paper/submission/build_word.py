"""Build the Word deliverables for the ISR submission package:
  01_Title_Page.docx, 02_Manuscript_Blinded.docx, 03_Cover_Letter.docx, 04_Online_Appendix.docx, 05_Replication_Code.docx
Run from paper/submission:  python3 build_word.py   (requires pandoc, python-docx, libreoffice for the PDF check)."""
import os, re, subprocess, glob, copy
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_LINE_SPACING, WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
OUT = os.path.join(HERE, "word"); os.makedirs(OUT, exist_ok=True)
SHORT_TITLE = "Who Pays for the Next Attempt?"
PAGEBREAK = '\n\n```{=openxml}\n<w:p><w:r><w:br w:type="page"/></w:r></w:p>\n```\n\n'

# ----------------------------------------------------------------------------- text helpers
def sub_sup(md):
    """Convert the source's escaped subscripts/superscripts to pandoc markdown sub/superscripts."""
    md = md.replace("e^{S^FB/σ}", "exp(S^FB^/σ)")
    md = re.sub(r"\\_\{([^}]*)\}", lambda m: "~" + m.group(1).replace(" ", "\\ ") + "~", md)
    md = re.sub(r"\\_([A-Za-z0-9]+)", r"~\1~", md)
    md = re.sub(r"\^(FB|e)(?![A-Za-z])", r"^\1^", md)
    md = re.sub(r"(?<=\))\^([nj])(?![A-Za-z])", r"^\1^", md)
    md = md.replace("\\_", "_")
    return md

def strip_front(md):
    md = re.sub(r"^---\n.*?\n---\n", "", md, count=1, flags=re.S)
    return md

def figure_paths(md):
    for name, w in [("fig_sensitivity", "5.2in"), ("fig_intuition", "5.8in")]:
        md = re.sub(rf"\(contracts/{name}\.png\)\{{width=\d+%\}}",
                    lambda m, n=name, w=w: f"({os.path.join(ROOT, 'contracts', n + '.png')}){{width={w}}}", md)
    return md

def words(md):
    return len(re.sub(r"[#*|`>\-]", " ", md).split())

# ----------------------------------------------------------------------------- reference documents
def make_reference(path, body_spacing):
    subprocess.run(["pandoc", "--print-default-data-file", "reference.docx"], stdout=open(path, "wb"), check=True)
    d = Document(path)
    for st in d.styles:
        if st.type != 1: continue
        try:
            st.font.name = "Times New Roman"
            rpr = st.element.get_or_add_rPr(); rf = rpr.find(qn("w:rFonts"))
            if rf is None: rf = OxmlElement("w:rFonts"); rpr.append(rf)
            for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"): rf.set(qn(a), "Times New Roman")
        except Exception: pass
        if st.name in ("Normal", "Body Text", "First Paragraph", "Block Text"):
            st.font.size = Pt(11); pf = st.paragraph_format
            pf.space_before = Pt(0); pf.space_after = Pt(0 if body_spacing == "double" else 6)
            pf.line_spacing_rule = WD_LINE_SPACING.DOUBLE if body_spacing == "double" else WD_LINE_SPACING.ONE_POINT_FIVE if body_spacing == "onehalf" else WD_LINE_SPACING.SINGLE
        if st.name == "Compact":
            st.font.size = Pt(10); st.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE; st.paragraph_format.space_after = Pt(2)
        if st.name.startswith("Heading") or st.name in ("Title", "Subtitle"):
            st.font.color.rgb = RGBColor(0, 0, 0); st.font.bold = True
            st.font.size = Pt({"Title": 16, "Heading 1": 13, "Heading 2": 12, "Heading 3": 11}.get(st.name, 11))
            st.paragraph_format.space_before = Pt(12); st.paragraph_format.space_after = Pt(6)
        if st.name in ("Source Code", "Verbatim Char"):
            st.font.name = "Courier New"; st.font.size = Pt(8)
            try:
                rf = st.element.get_or_add_rPr().find(qn("w:rFonts"))
                for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"): rf.set(qn(a), "Courier New")
            except Exception: pass
            if st.name == "Source Code":
                st.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE; st.paragraph_format.space_after = Pt(0)
        if st.name in ("Image Caption", "Table Caption", "Caption"):
            st.font.size = Pt(10); st.font.italic = False
    for sec in d.sections:
        sec.left_margin = sec.right_margin = sec.top_margin = sec.bottom_margin = Inches(1)
        sec.page_width = Inches(8.5); sec.page_height = Inches(11)
    d.save(path)

def add_field(run, instr):
    for t, txt in (("begin", None), (None, instr), ("end", None)):
        if t:
            e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), t); run._r.append(e)
        else:
            e = OxmlElement("w:instrText"); e.set(qn("xml:space"), "preserve"); e.text = txt; run._r.append(e)

def borders(table):
    tbl = table._tbl; pr = tbl.tblPr
    b = OxmlElement("w:tblBorders")
    for side, sz in (("top", 8), ("bottom", 8), ("insideH", 2)):
        e = OxmlElement(f"w:{side}"); e.set(qn("w:val"), "single"); e.set(qn("w:sz"), str(sz)); e.set(qn("w:space"), "0"); e.set(qn("w:color"), "000000"); b.append(e)
    for old in pr.findall(qn("w:tblBorders")): pr.remove(old)
    pr.append(b)

def postprocess(path, header=None, footer_numbers=True, landscape=False):
    d = Document(path)
    for t in d.tables:
        borders(t)
        for row in t.rows:
            for c in row.cells:
                for p in c.paragraphs:
                    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
                    for r in p.runs: r.font.size = Pt(9 if len(t.columns) > 6 else 10)
    for p in d.paragraphs:
        if p.style is not None and (p.style.name.startswith("Heading") or p.style.name == "Title"):
            for r in p.runs: r.font.color.rgb = RGBColor(0, 0, 0); r.font.name = "Times New Roman"
    sec = d.sections[0]
    if header:
        hp = sec.header.paragraphs[0]; hp.text = header; hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        for r in hp.runs: r.font.size = Pt(9); r.font.name = "Times New Roman"
    if footer_numbers:
        fp = sec.footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = fp.add_run(); r.font.size = Pt(10); add_field(r, "PAGE")
    d.core_properties.author = ""; d.core_properties.last_modified_by = ""; d.core_properties.title = ""; d.core_properties.comments = ""
    d.save(path)

def to_docx(md_text, out_name, spacing, header=None, title_meta=None):
    md_path = os.path.join(HERE, "_tmp_" + out_name.replace(".docx", ".md")); ref = os.path.join(HERE, f"_ref_{spacing}.docx")
    if not os.path.exists(ref): make_reference(ref, spacing)
    open(md_path, "w").write(md_text)
    out = os.path.join(OUT, out_name)
    subprocess.run(["pandoc", md_path, "-f", "markdown+pipe_tables+fenced_code_blocks+raw_attribute", "-o", out, "--reference-doc=" + ref], check=True)
    postprocess(out, header=header); os.remove(md_path)
    return out

# ----------------------------------------------------------------------------- source material
src = strip_front(open(os.path.join(ROOT, "paper_ISR.md")).read())
cut = src.index("## Appendix A.")
main_part, appendix_part = src[:cut], src[cut:]
main_part = re.sub(r"\*\*Authors:\*\*.*\n\n", "", main_part)
main_part = re.sub(r"\*\(Bibliographic details.*?\)\*\n\n", "", main_part, flags=re.S)
main_part = main_part.rstrip().rstrip("-").rstrip()
main_part = re.sub(r"(?<!Online )Appendix ([A-E])", r"Online Appendix \1", main_part)
main_part = re.sub(r"`[^`]*`", "the replication package", main_part)
main_text_words = words(main_part.split("## References")[0])
abstract_words = words(main_part.split("## Abstract")[1].split("---")[0])

# ----------------------------------------------------------------------------- 02 manuscript
man_md = figure_paths(sub_sup(main_part))
man_md = man_md.replace("---\n\n", "\n")                                   # horizontal rules are not needed in Word
to_docx(man_md, "02_Manuscript_Blinded.docx", "double", header=SHORT_TITLE)

# ----------------------------------------------------------------------------- 01 title page
title_md = f"""# Title Page

*(This page is not part of the blinded manuscript. Upload it separately, as required for double-anonymous review.)*

**Title.** Who Pays for the Next Attempt? Contract Design and Escalation Rules for AI-Assisted Software Maintenance

**Running header.** {SHORT_TITLE}

**Manuscript type.** Research Article

**Authors and affiliations.** [Author 1 name, title, department, institution, city, country]; [Author 2 name, …]

**Corresponding author.** [Name, postal address, e-mail address, telephone]

**ORCID of the submitting author.** [https://orcid.org/xxxx-xxxx-xxxx-xxxx]

**Keywords.** AI–human task allocation; escalation; outcome-based pricing; IT service contracts; software maintenance; large language models; double marginalization; optimal stopping *(map these to the ScholarOne keyword list at submission)*

**Length.** Abstract: {abstract_words} words. Main text before the references: about {main_text_words:,} words (the manuscript is formatted in 11-point type, double-spaced, with one-inch margins). An online appendix accompanies the paper.

**Funding.** [Funding sources and grant numbers, or "This research received no external funding."]

**Acknowledgments.** [To be completed after review; omitted from the blinded manuscript.]

**Conflicts of interest.** [Declare any perceived conflicts of interest.]

**Disclosure of AI assistance.** [Describe the use of generative AI tools in preparing the text, the analysis code, and the data, in line with the INFORMS policy on AI use; see the cover letter.]
"""
to_docx(title_md, "01_Title_Page.docx", "onehalf")

# ----------------------------------------------------------------------------- 03 cover letter
contrib = open(os.path.join(HERE, "contribution_statement.md")).read().split("\n", 2)[2].strip()
cover_md = f"""[Date]

Editor-in-Chief, Senior Editor, and Associate Editor
*Information Systems Research*

**Re: Submission of a Research Article, "Who Pays for the Next Attempt? Contract Design and Escalation Rules for AI-Assisted Software Maintenance"**

Dear Editors,

We submit the enclosed manuscript for consideration as a Research Article in *Information Systems Research*. The paper is a theory article that applies and extends search theory and vertical-contracting theory to a new information systems phenomenon, pay-per-use AI services, and illustrates the model with open repair data. It addresses a question that is becoming material for IT organizations: when a vendor of AI-based software repair charges per attempt or per verified fix, how many failed attempts should the buyer tolerate before escalating a defect to an engineer, and how does the vendor's price structure shape that decision? We derive the buyer's optimal escalation rule, characterize the vendor's optimal contract and the rent that deep sampling requires the vendor to leave the buyer, and examine private vendor quality and competition. We test the premises of the model on open data and calibrate its cost parameters to public wage statistics, task-time annotations, and API price lists.

The intended audience is both academic (researchers on the economics of information systems, IT sourcing and governance, and human–AI work design) and practical (chief information officers, engineering and procurement managers, and AI vendors).

## Contribution statement

{contrib}

## Paper provenance

[Authors to confirm each item before submission.] The manuscript has not been published and is not under review elsewhere. It has not previously been submitted to *Information Systems Research*. [State whether any version has been submitted to another journal and, if so, the reasons for rejection and the changes made.] [State whether the paper is posted on a working-paper website other than the authors' own, and whether any part has been copyrighted for pre-publication.] [List any related work by the authors that overlaps with this submission.]

## Data provenance

The manuscript uses only public data and public information. We list the sources and the status of the permissions below.

- *RepairBench results* (public GitHub repository of the RepairBench project, retrieved at the commit of 26 October 2025). We use counts of test-passing samples and token usage; no patches are redistributed. The repository carries no license file, so we have asked or will ask the maintainers for written permission. [Status of permission: pending; attach documentation if required.]
- *SWE-bench submissions* (public GitHub repository of the SWE-bench experiments). We use resolved lists and statements of pass@k and cost in submission READMEs. The checkout we used had no license file at its root. [Status of permission: pending.]
- *HumanEvalPack* (HumanEvalFix, Python; Hugging Face dataset, MIT license). We use the 164 tasks and their tests. We generated 19,680 model samples with three open-weight models through a public API and store only pass/fail outcomes and token counts, not generated code. [Authors to confirm that the terms of the API and of the three model licenses permit this use.]
- *Price list and statistics.* Public model prices from the OpenRouter model list (accessed 25 October 2026); wage and compensation statistics from the US Bureau of Labor Statistics; task-time annotations for SWE-bench Verified as summarized by Epoch AI. No human-subject data are collected or used.

## Use of generative AI

[Authors to complete in accordance with the INFORMS policy on generative AI. The manuscript's empirical component itself uses language models as an object of study: three open-weight models were sampled to produce the repair outcomes analyzed in Section 6. Describe any use of AI tools in drafting text, writing code, or checking proofs, and confirm that the authors reviewed and take responsibility for all content.]

## Preferred editors and reviewers

[Two preferred Senior Editors; two preferred Associate Editors; five preferred reviewers, at least two of them members of the Editorial Review Board; none with a conflict of interest as defined in the submission guidelines.]

## Funding and conflicts of interest

[Funding statement.] [Conflict-of-interest statement.]

Thank you for considering our work. We would be glad to provide any additional information.

Sincerely,

[Corresponding author name]
[Affiliation and e-mail]
"""
to_docx(cover_md, "03_Cover_Letter.docx", "onehalf")

# ----------------------------------------------------------------------------- 04 online appendix
def sensitivity_table():
    rows = ["| Regime | Heterogeneity profile | Grid points | AI repair worth using | Welfare: success fee > per-attempt | Vendor profit: success fee ≥ per-attempt | Firm saving: success fee > per-attempt | Median welfare / first best (per-attempt, success fee) | Median N^FB, vendor's depth | Vendor's depth below N^FB | Rent share of W(N^FB): median [min–max] |",
            "|---|---|---|---|---|---|---|---|---|---|---|"]
    regime = ""
    for line in open(os.path.join(ROOT, "contracts", "results_sensitivity.txt")):
        line = line.rstrip("\n")
        if line.startswith("==="): regime = line.split(":")[0].replace("=== ", "").strip()
        elif "|" in line and not line.startswith("profile"):
            cells = [c.strip() for c in line.split("|")]
            if len(cells) >= 10: rows.append("| " + regime + " | " + " | ".join(cells[:10]) + " |")
    return "\n".join(rows)

def verbatim(title, filename, base):
    p = os.path.join(ROOT, base, filename)
    return f"### {title}\n\nOutput of `{filename}`.\n\n```\n{open(p).read().rstrip()}\n```\n\n"

extra = f"""
## Appendix E. Detailed Sensitivity Results

The table reports, for each regime and heterogeneity profile in Section 5.4, the share of grid points at which AI repair is worth using and the comparison of the two contract forms. Monopoly equilibria are computed exactly from the budget steps.

{sensitivity_table()}

## Appendix F. Calibration of the Cost Parameters

{verbatim("F.1 Calibration script output", "results_calibration.txt", "contracts")}
{verbatim("F.2 Running example (Table 1 and Figure 1)", "results_running_example.txt", "contracts")}
{verbatim("F.3 Incentive rent (Table 2)", "results_incentive_rent.txt", "contracts")}

## Appendix G. Additional Numerical Results

{verbatim("G.1 Monopoly equilibria and random sweep (Table 3 and Section 5.1)", "results_contracts.txt", "contracts")}
{verbatim("G.2 Robustness over random parameter draws", "results_robustness.txt", "contracts")}
{verbatim("G.3 Private vendor quality: representative case", "results_asymmetric.txt", "contracts")}
{verbatim("G.4 Private vendor quality: sweep", "results_asym_sweep.txt", "contracts")}
{verbatim("G.5 Differentiated-Bertrand equilibria", "results_diff_bertrand.txt", "contracts")}
{verbatim("G.6 Differentiated-Bertrand sweep", "results_diff_sweep.txt", "contracts")}
{verbatim("G.7 Numerical checks of the proofs", "results_verify_proofs.txt", "contracts")}
{verbatim("G.8 Distribution-free checks (Propositions 1, 5, 6)", "results_general_theory.txt", "contracts")}

## Appendix H. Empirical Analyses of Repair Data

{verbatim("H.1 RepairBench (Section 6)", "results_empirical.txt", "empirical")}
{verbatim("H.2 SWE-bench logs and published coverage points", "results_swebench.txt", "empirical")}
{verbatim("H.3 HumanEvalFix with 40 samples per bug", "results_hef.txt", "empirical/sampling")}
"""
app_head = f"""# Online Appendix (E-Companion) to "Who Pays for the Next Attempt? Contract Design and Escalation Rules for AI-Assisted Software Maintenance"

This online appendix contains the survival function and estimation details (Appendices A and B), reproducibility notes (Appendix C), the proofs (Appendix D), and additional numerical and empirical results (Appendices E to H). Section numbers refer to the manuscript.

"""
app_md = app_head + re.sub(r"`[^`]*`(?=[,.;)])", lambda m: m.group(0), appendix_part) + extra
app_md = app_md.replace("The replication package contains", "The replication code file accompanying the submission contains")
app_md = figure_paths(sub_sup(app_md)).replace("---\n\n", "\n")
to_docx(app_md, "04_Online_Appendix.docx", "single", header=SHORT_TITLE + " — Online Appendix")

# ----------------------------------------------------------------------------- 05 replication code
CODE = [
 ("contracts/contracts.py", "Core model: market, contracts, first best and Stackelberg equilibria"),
 ("contracts/running_example.py", "Table 1 and Figure 1 (running example)"),
 ("contracts/incentive_rent_table.py", "Table 2 (incentive rent)"),
 ("contracts/robustness.py", "Random-draw comparison of the contracts (Section 5.1)"),
 ("contracts/asymmetric.py", "Private vendor quality: profit order and equilibria (Section 5.2)"),
 ("contracts/asym_sweep.py", "Private vendor quality: sweep (Section 5.2)"),
 ("contracts/diff_bertrand.py", "Differentiated-Bertrand competition (Section 5.3, Table 4)"),
 ("contracts/diff_sweep.py", "Differentiated-Bertrand sweep (Section 5.3)"),
 ("contracts/calibration.py", "Cost calibration from public sources (Section 5.4)"),
 ("contracts/sensitivity.py", "Sensitivity across calibrated ranges (Table 5)"),
 ("contracts/fig_sensitivity.py", "Figure 2"),
 ("contracts/verify_proofs.py", "Numerical checks of Propositions 4 and 8(b)"),
 ("contracts/general_theory.py", "Distribution-free checks of Propositions 1, 5, 6"),
 ("empirical/load_repairbench.py", "RepairBench: extract per-bug success counts"),
 ("empirical/analyze.py", "RepairBench: model fits and out-of-sample policy comparison (Section 6)"),
 ("empirical/swebench_repo_level.py", "SWE-bench: calibration from published coverage points (Section 6)"),
 ("empirical/sampling/sample_humanevalfix.py", "HumanEvalFix: sampling and test execution (Section 6)"),
 ("empirical/sampling/analyze_hef.py", "HumanEvalFix: analysis of 40 samples per bug (Section 6)"),
]
def sanitize(code):
    code = code.replace("/home/user/assert-kth/repairbench/results", "<REPAIRBENCH_CLONE>/results")
    code = code.replace("/home/user/swe-bench/experiments/evaluation", "<SWE_BENCH_EXPERIMENTS_CLONE>/evaluation")
    return code
map_rows = "\n".join([
 "| Table 1, Figure 1 | `running_example.py` |", "| Table 2 | `incentive_rent_table.py` |", "| Table 3 and the 296-draw comparison (Section 5.1) | `contracts.py`, `robustness.py` |",
 "| Section 5.2 | `asymmetric.py`, `asym_sweep.py` |", "| Table 4 and the 240-cell sweep (Section 5.3) | `diff_bertrand.py`, `diff_sweep.py` |",
 "| Section 5.4 calibration, Table 5, Figure 2 | `calibration.py`, `sensitivity.py`, `fig_sensitivity.py` |", "| Section 6, RepairBench | `load_repairbench.py`, `analyze.py` |",
 "| Section 6, SWE-bench | `swebench_repo_level.py` |", "| Section 6, HumanEvalFix | `sample_humanevalfix.py`, `analyze_hef.py` |",
 "| Online Appendix D numerical checks | `verify_proofs.py`, `general_theory.py` |"])
readme = f"""# Replication Code File

This file accompanies "Who Pays for the Next Attempt? Contract Design and Escalation Rules for AI-Assisted Software Maintenance." It lists the code that produces every number, table, and figure in the manuscript. Identifying information has been removed for review.

## Environment

Python 3.13 with numpy 2.5.3, scipy 1.18.1, pandas 3.0.5, pyarrow 26.0.0, and matplotlib 3.11.2. The scripts under `contracts/` import each other (`contracts.py` is imported by most), so place them in a single folder and run them from there. Random seeds are fixed inside each script.

## Data and how to obtain it

- *RepairBench results.* Clone the public RepairBench repository and pass its `results` folder as the first argument of `load_repairbench.py`. We used the commit of 26 October 2025. The loader writes `bug_counts.json`, which `analyze.py` reads from the current directory.
- *SWE-bench submissions.* Clone the public SWE-bench experiments repository and pass its `evaluation` folder to `swebench_repo_level.py`. The script reads the resolved lists in each `results/results.json`.
- *HumanEvalFix.* Download the Python split of the HumanEvalPack dataset (Hugging Face, `bigcode/humanevalpack`, file `python/test-00000-of-00001.parquet`) and save it as `hep_python.parquet` next to `sample_humanevalfix.py`. Sampling calls the OpenRouter chat-completions API; set the environment variable `OPENROUTER_API_KEY` to your own key. Run `python3 sample_humanevalfix.py <model> 40` for each model (we used `meta-llama/llama-3.2-3b-instruct`, `mistralai/ministral-8b-2512`, and `google/gemma-3-4b-it`), then `python3 analyze_hef.py`. Generated code is not stored; only pass/fail outcomes and token counts are written. The sampling cost was $0.56.
- *Prices and statistics.* The calibration in `calibration.py` uses the figures cited in Section 5.4 (BLS wage, benefits share, SWE-bench Verified time buckets, OpenRouter prices, and published per-task agent costs) as constants, with the sources named in comments and in the manuscript.

## Run order

1. `contracts.py` (equilibria for the three heterogeneity profiles), `robustness.py`, `running_example.py`, `incentive_rent_table.py`.
2. `asymmetric.py`, `asym_sweep.py`, `diff_bertrand.py`, `diff_sweep.py`.
3. `calibration.py`, `sensitivity.py`, `fig_sensitivity.py`.
4. `verify_proofs.py`, `general_theory.py`.
5. Empirical: `load_repairbench.py`, `analyze.py`, `swebench_repo_level.py`, `sample_humanevalfix.py`, `analyze_hef.py`.

Each script writes its output to a `results_*.txt` file, reproduced in Online Appendices E to H.

## Where each result comes from

| Manuscript item | Script |
|---|---|
{map_rows}

## Code listings
"""
parts = [readme]
for path, desc in CODE:
    code = sanitize(open(os.path.join(ROOT, path)).read())
    parts.append(PAGEBREAK + f"### `{os.path.basename(path)}`\n\n*{desc}.*\n\n```python\n{code.rstrip()}\n```\n")
repl_md = "\n".join(parts)
to_docx(repl_md, "05_Replication_Code.docx", "single", header=SHORT_TITLE + " — Replication code")

# ----------------------------------------------------------------------------- PDF check and report
subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", os.path.join(OUT, "_pdf")] + sorted(glob.glob(os.path.join(OUT, "*.docx"))), check=True, capture_output=True)
from pypdf import PdfReader
for f in sorted(glob.glob(os.path.join(OUT, "_pdf", "*.pdf"))):
    print(f"{os.path.basename(f)}: {len(PdfReader(f).pages)} pages")
print("main text words before references:", main_text_words, "| abstract words:", abstract_words)
for ref in glob.glob(os.path.join(HERE, "_ref_*.docx")): os.remove(ref)
