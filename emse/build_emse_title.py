import sys; sys.path.insert(0, "/home/user/fluffy-meme/isr_submission/manuscript_build")
from docbuild import *
T = "Mutants overstate what LLM-written unit tests can find: reach on mutants and on real faults"
d = new_doc(spacing=1.5, footer=False)
P(d, "**Title page**", indent=False, align="center", size=11, after=12)
TITLE(d, T, size=15)
P(d, "Ook Lee", indent=False, align="center", size=12, after=2)
P(d, "Department of Information Systems, Hanyang University, Seoul, Republic of Korea", indent=False, align="center", size=11, after=2)
P(d, "Corresponding author: Ook Lee, ooklee@hanyang.ac.kr", indent=False, align="center", size=11, after=2)
P(d, "ORCID: [to be added]", indent=False, align="center", size=11, after=14)
P(d, "**Keywords** Test generation · Large language models · Mutation testing · Real faults · Test oracle · BugsInPy", indent=False, size=11, after=10)
P(d, "**Word count** about 2,700 (main text including tables and figure captions)", indent=False, size=11, after=14)
H2(d, "Declarations")
for k, v in [
 ("Funding", "Not applicable."),
 ("Competing interests", "The author declares no competing interests."),
 ("Ethics approval", "Not applicable. No human participants or personal data were involved."),
 ("Data availability", "Code, prompts, per-bug and per-module results and analysis scripts are available on Zenodo, version 2 of the replication package (https://doi.org/10.5281/zenodo.23674752). BugsInPy and the studied libraries are public."),
 ("Author contributions", "O.L. conceived the study, built the pipeline, ran the analyses and wrote the manuscript."),
 ("Use of generative AI", "The studied tests were written by Claude Haiku 5.5, Claude Sonnet 5.5 and DeepSeek V4.1 Flash. An AI coding assistant (Claude Code) was used to write and run the analysis code and to draft and edit the manuscript text; the author reviewed the results and takes responsibility for the content."),
]:
    P(d, f"**{k}** {v}", indent=False, size=11, after=4, align="justify")
d.save("EMSE_Title_Page.docx")
