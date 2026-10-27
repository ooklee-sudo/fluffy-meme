import sys; sys.path.insert(0, "/home/user/fluffy-meme/isr_submission/manuscript_build")
from docbuild import *
import pandas as pd
R = pd.read_csv("replication/data/defence_results.csv"); M = R[R.target != "econ"]
c = lambda m, g, k: float(M[(M.method == m) & (M.generator == g) & (M.cond == k)].auc.iloc[0])
w = lambda m: M[(M.method == m) & (M.cond != "orig") & (~M.cond.isin(["mix30", "noise3", "edit0.25", "edit0.5", "edit0.75", "hybrid0.5"]))].auc.min()
T = "Combining Detectors That Fail Differently Defends Screens for Machine-Written Scholarly Text Against Adaptive Authors"
d = new_doc(spacing=1.15, footer=False)
P(d, "Ook Lee", indent=False); P(d, "Department of Information Systems, Hanyang University, Seoul, Republic of Korea", indent=False); P(d, "ooklee@hanyang.ac.kr", indent=False, after=10)
P(d, "[Date]", indent=False, after=10)
P(d, "The Editor-in-Chief", indent=False); P(d, "*IEEE Transactions on Artificial Intelligence*", indent=False, after=10)
P(d, "**Submission of a regular paper: “" + T + "”**", indent=False, after=10)
P(d, "Dear Editor-in-Chief,", indent=False, after=8)
P(d, "I submit the manuscript above as a regular paper. It has not been published and is not under consideration elsewhere. An earlier version was submitted to *Nature Machine Intelligence* and was declined without review on grounds of fit with that journal.", indent=False, spacing=1.3, after=8, align="justify")
H2(d, "Contribution")
BUL(d, [
 f"An adversarial evaluation of nine detectors of machine-written scientific papers under eight attacks and four generators, including detector-guided attacks; guided sentence mixing lowers Fast-DetectGPT's AUC on Claude papers from {c('fd','claude','orig'):.2f} to {c('fd','claude','bok_mix'):.2f}.",
 "An explanation of why probability-based scores invert under perturbation, and a two-sided score calibrated on held-out humans.",
 f"A parameter-free ensemble of robustly standardized scores of detectors that fail differently, which raises the worst-case AUC from {w('fd'):.2f} to {w('mean4'):.2f}–{w('top2'):.2f} without attacked training data.",
 "An artifact control showing that supervised accuracy partly rests on how corpora were assembled.",
], size=None)
H2(d, "Fit")
P(d, "The paper proposes and evaluates a robustness method for an AI system in an adversarial deployment setting, reports its limits (operating point, ensemble-aware attackers), and releases code and data. It addresses detection of AI-generated content, a topic within the journal's scope.", indent=False, spacing=1.3, after=8, align="justify")
H2(d, "Declarations")
P(d, "Code and data: https://doi.org/10.5281/zenodo.23664508 (version 2). No human participants were involved. I declare no competing interests. Generative AI use is disclosed in the manuscript. Suggested reviewers: [optional].", indent=False, spacing=1.3, after=8, align="justify")
P(d, "Sincerely,", indent=False, after=20); P(d, "Ook Lee", indent=False)
d.save("TAI_Cover_Letter.docx"); print("ok")
