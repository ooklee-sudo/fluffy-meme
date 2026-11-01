from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import sys
def doc():
    d=Document(); s=d.styles['Normal']; s.font.name='Times New Roman'; s.font.size=Pt(12); return d
TITLE="Does Release Timing in the LLM Software Ecosystem Respond to Accumulating Degradation? An Empirical Study of Open-Source Repositories and Public Chat Logs"

# ---------- cover letter ----------
d=doc()
for t in ["Ook Lee","Department of Information System, Hanyang University","Seoul, Republic of Korea","ooklee@hanyang.ac.kr","","[Date]","","The Editors","PLOS ONE","","Dear Editors,",""]:
    d.add_paragraph(t)
body=[
f"Please consider the enclosed manuscript, “{TITLE},” for publication in PLOS ONE as a Research Article.",
"Software built around large language models is widely expected to degrade as the world drifts away from a model’s training data, and practitioners are advised to refresh such systems on a schedule that balances renewal cost against degradation cost. We ask whether the public record matches this expectation. We state a small replacement model, derive three testable implications (errors rise with the time since the last refresh; refresh probability rises with that time; higher measured drift predicts worse outcomes), and show by simulation that the model’s parameters are recoverable. We then test the implications on weekly bug-report counts and release dates for 19 widely used open-source repositories (4,071 repository-weeks; 1,521 releases) and on 478,498 English conversations from the public WildChat corpus.",
"None of the three implications is supported. After total issue volume is controlled, bug reports do not rise with the age of a release; the probability of a release does not rise with that age; and a measure of prompt drift does not predict user corrections once repeated automated templates are removed. An uncorrected drift measure appeared to predict corrections (p = 0.009) only because a single template had come to dominate the data. A same-week contrast of model snapshots with different training cutoffs also finds no support for the prediction, although it cannot separate cutoff from model generation. We are explicit that these are negative results from convenience samples, that the correction detector has low recall, and that a null result in open-source repositories does not imply that degradation is absent in production.",
"We believe the manuscript meets the PLOS ONE publication criteria. It reports a rigorous test of a widely held belief with pre-specified eligibility rules, a simulation benchmark showing that the tests would have detected the effect had it been present, validation of the outcome measure with human and AI labels, and a full account of the limits of the data. The study does not depend on the novelty or direction of its findings. It also documents a methodological hazard that readers who work with public chat logs can use: a reasonable-looking drift measure produced a significant association that disappeared when one automated template was removed.",
"All data and code needed to reproduce the results are provided: the weekly GitHub aggregates, the collection, measurement, simulation and analysis code, and the labeling codebook and labels without conversation text. The WildChat corpus is publicly available from its publisher, and we store only aggregate counts and binary features of conversations. [Repository DOI: to be inserted before submission.]",
"This work has not been published and is not under consideration elsewhere. The author declares no competing interests. [Confirm: no preprint posted, or give the preprint link.]",
"Thank you for your consideration.",
"","Sincerely,","","Ook Lee","Department of Information System, Hanyang University","ooklee@hanyang.ac.kr","ORCID: [to be inserted]"]
for t in body: d.add_paragraph(t)
d.save('PLOS_ONE_Cover_Letter.docx')

# ---------- statements ----------
d=doc(); p=d.add_paragraph(); r=p.add_run("PLOS ONE submission statements (to paste into the online form)"); r.bold=True
def sec(h,t):
    p=d.add_paragraph(); p.add_run(h).bold=True
    for x in (t if isinstance(t,list) else [t]): d.add_paragraph(x)
sec("Title",TITLE)
sec("Article type","Research Article")
sec("Financial Disclosure","The author received no specific funding for this work. [Confirm; if any grant, university or employer support was received, name it here.]")
sec("Competing Interests","The author has declared that no competing interests exist.")
sec("Data Availability Statement",[
"All data and code are available at [Zenodo/GitHub repository, DOI to be inserted], released under [license, e.g., CC BY 4.0 for data and MIT for code]. The repository contains the weekly GitHub aggregates for the 19 repositories (bug counts, total issue counts, release indicators), the collection, measurement, simulation and analysis scripts, the per-conversation binary features derived from WildChat (no conversation text), and the labeling codebook with labels and identifiers.",
"The WildChat-1M corpus is publicly available from its publisher (Hugging Face, allenai/WildChat-1M). Raw GitHub data can be re-collected with the supplied scripts using a GitHub access token. No data are restricted."])
sec("Ethics Statement","The study uses public repository metadata and the public WildChat corpus, which is distributed with hashed identifiers. Only aggregate counts and binary features were stored, and no conversation text was stored or is published. The study involved no human participants, and institutional ethics approval was not required. [Confirm with your institution.]")
sec("Author Contributions (CRediT)","Ook Lee: Conceptualization, Methodology, Software, Formal analysis, Investigation, Data curation, Writing – original draft, Writing – review & editing, Visualization.")
sec("Generative AI disclosure","[Edit to match your actual use.] A large language model (Claude, Anthropic) was used as one of the two labelers when validating the correction detector, as described in Section 4.4 of the manuscript; its labels were compared with human labels and reported. The author also used an AI assistant to help write and run analysis code and to draft and edit text, and takes responsibility for the content.")
sec("Clinical trial number","Not applicable.")
sec("Preprint","[State whether a preprint has been posted; PLOS ONE accepts preprints.]")
sec("Suggested academic editors / reviewers (optional)","[Add 3–5 names with affiliations and emails, or leave blank.]")
sec("Pre-submission checklist",[
"1. Replace “available upon request” in the manuscript with the repository DOI.",
"2. Correct gpt-4-0613 to gpt-4-0314 in Sections 4.2 and 5.3 and re-check the “eight weeks” statement.",
"3. Insert the snapshot-design text (manuscript_insert_snapshot_design.md).",
"4. Remove the Editorial Manager (EMSE) title page; PLOS ONE needs a title page and a blinded or unblinded manuscript per its instructions.",
"5. Make figures and tables meet PLOS requirements (TIFF/EPS at 300–600 dpi; tables in the text).",
"6. Check that author affiliation, ORCID and funding fields match the online form."])
d.save('PLOS_ONE_Submission_Statements.docx')
