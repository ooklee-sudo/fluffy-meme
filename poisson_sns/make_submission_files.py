"""Build the submission package: cover letter, title page, highlights, checklist, anonymized code zip."""
import os, shutil, zipfile
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_COLOR_INDEX

OUT = "../dss_revision/submission/"
os.makedirs(OUT, exist_ok=True)
TITLE = ("Pre-testing social media campaigns with LLM-agent simulation: event-driven agent timing and the "
         "scale-versus-speed trade-off in seeding decisions")
HL = ["Agent timing in LLM simulators is set by a point process, not the simulation clock",
      "An LLM rates the urge to act; an inhomogeneous Poisson process decides when",
      "At equal exposure budget, influencer seeding gave about 78% more adopters",
      "Distributed seeding reached half its adopters sooner and varied far less",
      "Conclusions are unchanged when a rule-based oracle is replaced by LLM ratings"]


def newdoc():
    d = Document()
    d.styles["Normal"].font.name = "Times New Roman"
    d.styles["Normal"].font.size = Pt(11)
    return d


def fill(p, t):  # highlight bracketed fields to be completed by the authors
    import re
    for part in re.split(r"(\[[^\]]+\])", t):
        r = p.add_run(part)


# 1. title page
d = newdoc()
d.add_heading("Title page", 1)
d.add_paragraph("(Upload as a separate file; it is not sent to reviewers.)")
d.add_heading("Title", 2); d.add_paragraph(TITLE)
d.add_heading("Authors and affiliations", 2)
d.add_paragraph("Ook Lee\nDepartment of Information Systems, Hanyang University, Seoul, Korea")
d.add_heading("Corresponding author", 2)
fill(d.add_paragraph(), "Ook Lee, Department of Information Systems, Hanyang University, Seoul, Korea. E-mail: ooklee@hanyang.ac.kr.")
d.add_heading("CRediT author statement", 2)
fill(d.add_paragraph(), "Ook Lee: Conceptualization, Methodology, Software, Formal analysis, Writing – original draft, Writing – review and editing.")
d.add_heading("Acknowledgements and funding", 2)
fill(d.add_paragraph(), "This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors.")
d.add_heading("Declaration of competing interest", 2)
fill(d.add_paragraph(), "The author declares that he or she has no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.")
d.add_heading("Declaration of generative AI use", 2)
fill(d.add_paragraph(),
     "Large language models are part of the method of this study: ten independent instances of an LLM (Claude Sonnet) acted as "
     "raters of the intensity oracle in Study 3 (Section 4.4 and Appendix B). In addition, an AI assistant (Claude, Anthropic) was used to implement the "
     "simulation code from the written specification, to run the analyses, and to draft and edit the manuscript. The author reviewed and edited all content and takes full "
     "responsibility for the published work.")
d.save(OUT + "1_title_page.docx")

# 2. highlights
d = newdoc()
d.add_heading("Highlights", 1)
for h in HL:
    d.add_paragraph(h, style="List Bullet")
d.save(OUT + "2_highlights.docx")

# 3. cover letter
d = newdoc()
d.add_heading("Cover letter", 1)
d.add_paragraph("October 8, 2026")
d.add_paragraph("To the Editors of Decision Support Systems,")
d.add_paragraph(
    "We submit the manuscript entitled “" + TITLE + "” for consideration as a research article in Decision Support Systems.")
d.add_paragraph(
    "Managers who choose how to seed a social media campaign cannot test the options in the field without cost, and simulation "
    "with large language model (LLM) agents is an attractive pre-test. Most LLM-agent simulators, however, decide when agents act "
    "with a fixed-interval clock, so temporal outcomes such as the speed of diffusion are partly an artifact of the simulation loop. "
    "We present Poisson-SNS, a simulator in which an LLM rates how strongly a situation moves an agent to act and an inhomogeneous "
    "Poisson process determines when it acts, and we use it to examine a concrete decision: concentrating a campaign on a few "
    "influencers versus spreading it across many ordinary users at equal exposure budget.")
d.add_paragraph(
    "The main findings are that the scheduler reproduces the daily activity cycle far better than homogeneous Poisson and polling "
    "baselines against an assumed reference; that concentration yields more adopters in expectation while distribution is faster "
    "and far more predictable, so no strategy dominates; and that these conclusions are robust to replacing the rule-based "
    "intensity oracle with LLM ratings and to most parameter variations, but not to a network without a heavy-tailed follower "
    "distribution. We state the limits of the evidence explicitly: without platform trace data the behavioral validation relies on "
    "assumed references, and the results are offered as hypotheses for field testing.")
d.add_paragraph(
    "We believe the paper fits the journal because it addresses simulation-based support for a managerial decision on social "
    "media, connects to work published in Decision Support Systems on word-of-mouth marketing, diffusion models, and LLM-based "
    "decision support, and contributes a reusable specification together with an evaluation protocol.")
fill(d.add_paragraph(),
     "The manuscript is original, has not been published, and is not under consideration elsewhere. The sole author has approved the submission. "
     "The code, results, and the LLM rating table are provided as an anonymized supplementary archive. A statement on the use of generative AI is included "
     "on the title page and in the manuscript.")
d.add_paragraph("Sincerely,")
d.add_paragraph("Ook Lee\nDepartment of Information Systems, Hanyang University, Seoul, Korea\nooklee@hanyang.ac.kr")
d.save(OUT + "3_cover_letter.docx")

# 4. checklist
d = newdoc()
d.add_heading("Submission checklist", 1)
d.add_heading("Done in this package", 2)
for t in ["Anonymized manuscript (editable .docx), with abstract, keywords, highlights, tables, figures, appendices",
          "Separate title page, highlights file, cover letter (fields to complete are highlighted)",
          "Figures as 300 dpi PNG in dss_revision/figures (also embedded in the manuscript)",
          "Anonymized code and data archive (code_anonymous.zip), checked for author names and affiliations",
          "DSS literature positioning: references verified against Crossref (journal ISSN 0167-9236)"]:
    d.add_paragraph(t, style="List Bullet")
d.add_heading("Only the authors can do these", 2)
for t in ["Check the filled-in statements, which are based on standard wording and were not confirmed by you: no funding, no competing interests, sole-author approval and originality (title page, cover letter), and the CRediT role list. Add ORCID, postal address, telephone, and suggested reviewers if the system asks for them",
          "Confirm the generative-AI declaration wording and the originality statement",
          "Upload code_anonymous.zip as a supplementary file in the submission system (the manuscript says it is provided as an anonymized supplementary archive). Do not link the current public GitHub repository, which shows your account name",
          "Read each cited Decision Support Systems paper and adjust the one-line descriptions in Section 2.1 (written from titles and bibliographic records); repeat the literature search in the journal for better-fitting papers",
          "Create an account in the journal's submission system and upload the files"]:
    d.add_paragraph(t, style="List Bullet")
d.add_heading("Could not be verified (the Guide for Authors was not readable from the working environment)", 2)
for t in ["Number of Highlights bullets and characters per bullet (a third-party page says 3–5 bullets, up to 85 characters; unverified)",
          "Abstract length limit (third-party page says 150–300 words; unverified). The current abstract has about 300 words, so shorten it if the limit is lower",
          "Reference style (the manuscript uses an Elsevier-like author-year style and the author-year list was not checked against the journal; a third-party page says numbered style; unverified)",
          "Page or word limits, figure and table placement rules, and any required template",
          "Exact anonymization rules (the journal uses double-anonymized review; check what must be removed from the file properties and the text)"]:
    d.add_paragraph(t, style="List Bullet")
d.add_heading("Known limitations to keep in mind before submitting", 2)
for t in ["The simulator was re-implemented from the manuscript specification, so some settings are assumptions (Appendix A); they are disclosed in the paper",
          "Validation uses assumed reference profiles, not real platform data. This is the paper's main weakness and is stated as such",
          "LLM ratings come from one rater per batch with no repeat ratings, so repeatability is not measured. Running the API script (build_llm_table.py, --repeats 3) would fix this"]:
    d.add_paragraph(t, style="List Bullet")
d.save(OUT + "0_checklist.docx")

# 5. anonymized code zip
src = "."
skip = {"__pycache__", "make_paper.py", "make_submission_files.py"}
with zipfile.ZipFile(OUT + "code_anonymous.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(os.listdir(src)):
        if f in skip or f.startswith("."):
            continue
        z.write(os.path.join(src, f), "poisson_sns/" + f)
print(sorted(os.listdir(OUT)))
