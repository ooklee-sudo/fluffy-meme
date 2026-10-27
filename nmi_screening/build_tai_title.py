import sys; sys.path.insert(0, "/home/user/fluffy-meme/isr_submission/manuscript_build")
from docbuild import *
T = "Combining Detectors That Fail Differently Defends Screens for Machine-Written Scholarly Text Against Adaptive Authors"
d = new_doc(spacing=1.5, footer=False)
P(d, "**Title Page**", indent=False, align="center", size=11, after=10)
TITLE(d, T, size=15)
P(d, "Ook Lee", indent=False, align="center", size=12, after=2)
P(d, "Department of Information Systems, Hanyang University, Seoul, Republic of Korea", indent=False, align="center", size=11, after=2)
P(d, "Corresponding author: Ook Lee (e-mail: ooklee@hanyang.ac.kr)", indent=False, align="center", size=11, after=2)
P(d, "ORCID: [to be added]", indent=False, align="center", size=11, after=12)
P(d, "**Manuscript type** Regular paper", indent=False, size=11, after=4)
P(d, "**Index Terms** Adversarial robustness, AI-generated text detection, ensemble methods, large language models, research integrity, zero-shot detection.", indent=False, size=11, after=4, align="justify")
P(d, "**Length** 6 pages in the IEEE two-column format; 5 tables, 2 figures, 37 references; supplementary material (6 pages).", indent=False, size=11, after=12)
H2(d, "Declarations")
for k, v in [
 ("Funding", "This research received no specific grant."),
 ("Conflict of interest", "The author declares no competing interests."),
 ("Ethics", "Not applicable. No human participants or personal data were involved; all human texts are published papers."),
 ("Data and code availability", "Code, machine-generated corpora, per-document scores and result tables are available on Zenodo (https://doi.org/10.5281/zenodo.23664508, version 2)."),
 ("Prior submission", "An earlier version was submitted to Nature Machine Intelligence and declined without review on grounds of fit."),
 ("Use of generative AI", "The machine-written papers studied were produced by GPT-4o, Claude Sonnet 5.5, Llama 3.3 70B Instruct and DeepSeek V4.1 Flash, and Gemini 2.5 Pro served as a judge. An AI coding assistant (Claude Code) was used to write and run the analysis code and to draft and edit the manuscript text; the author reviewed the results and takes responsibility for the content."),
]:
    P(d, f"**{k}** {v}", indent=False, size=11, after=4, align="justify")
d.save("tai_submission/TAI_Title_Page.docx"); print("ok")
