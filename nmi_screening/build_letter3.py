import sys; sys.path.insert(0, "/home/user/fluffy-meme/isr_submission/manuscript_build")
from docbuild import *
import pandas as pd
R = pd.read_csv("replication/data/defence_results.csv"); M = R[R.target != "econ"]
c = lambda m, g, k: float(M[(M.method == m) & (M.generator == g) & (M.cond == k)].auc.iloc[0])
w = lambda m: M[(M.method == m) & (M.cond != "orig") & (~M.cond.isin(["mix30", "noise3", "edit0.25", "edit0.5", "edit0.75", "hybrid0.5"]))].auc.min()
T = "Combining detectors that fail differently protects screens for machine-written scholarly text against adaptive authors"
d = new_doc(spacing=1.15, footer=False)
P(d, "Ook Lee", indent=False); P(d, "Hanyang University, Seoul, Republic of Korea", indent=False); P(d, "ooklee@hanyang.ac.kr", indent=False, after=10)
P(d, "[Date]", indent=False, after=10)
P(d, "The Editors", indent=False); P(d, "*Nature Machine Intelligence*", indent=False, after=10)
P(d, "**Manuscript: “" + T + "”**", indent=False, after=10)
P(d, "Dear Editors,", indent=False, after=8)
P(d, "I submit the manuscript above as an Article. It has not been published and is not under consideration elsewhere.", indent=False, spacing=1.3, after=8, align="justify")
H2(d, "The question and the findings")
P(d, "Publishers and research-integrity offices screen manuscripts for machine authorship, but detectors are usually tested on text no author has tried to disguise. The manuscript tests nine screens on 474 human papers and papers from four generators, including DeepSeek V4.1 Flash, under eight attacks, two of which query a detector's own score, and proposes a defence that does not require knowing the attack. The main findings are:", indent=False, spacing=1.3, after=4, align="justify")
BUL(d, [
 f"Every single detector has a failure. Keeping the most human-looking of four sentence-mixed candidates, as judged by Fast-DetectGPT, drives its AUC on Claude papers from {c('fd','claude','orig'):.2f} to {c('fd','claude','bok_mix'):.2f}, below chance; guided rewriting does not work.",
 f"Probability-based scores invert under perturbation because spliced text is less probable than genuine human text; a two-sided score calibrated on separate human papers turns this into a signal ({c('dl','claude','bok_mix'):.2f} under the same attack).",
 f"Combining standardized scores of detectors that fail differently, with no learned weights and no attacked training data, raises the worst-case AUC over four generators and eight attacks from {w('fd'):.2f} for the best single detector to {w('mean4'):.2f}–{w('top2'):.2f}.",
 "A control shows that supervised accuracy rests partly on structural artifacts of how human papers were extracted, which limits what high numbers on a new field mean.",
], size=None)
H2(d, "Relevance to the journal")
P(d, "The paper combines a method (a parameter-free defence) with an adversarial evaluation that includes attacks aimed at the detector's own score, on scientific text, a setting of growing consequence for research integrity. Code and derived data are public.", indent=False, spacing=1.3, after=8, align="justify")
H2(d, "Limitations stated in the manuscript")
BUL(d, [
 "The defence raises the worst case in AUC more than at a strict 5% false-positive operating point, and it is not tested against attackers who optimize against the combination itself.",
 "Each cell compares 100 attacked papers with 186 human papers; three fields, English only; one open model pair for zero-shot scores; the judge on a subset of attacks.",
 "The study is an independent re-implementation: the original data and code of an earlier version of this work were not available, so all corpora, screens and attacks were rebuilt.",
], size=None)
H2(d, "Declarations")
P(d, "No human participants or personal data are involved. Code and derived data: Zenodo, https://doi.org/10.5281/zenodo.23664508 (version 2). I declare no competing interests. Generative AI use is disclosed in the manuscript. Suggested reviewers: [optional].", indent=False, spacing=1.3, after=8, align="justify")
P(d, "Sincerely,", indent=False, after=20); P(d, "Ook Lee", indent=False)
d.save("NMI_Defence_Cover_Letter.docx"); print("ok")
