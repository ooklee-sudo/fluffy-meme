import sys; sys.path.insert(0, "/home/user/fluffy-meme/isr_submission/manuscript_build")
from docbuild import *
T = "Which screens for machine-written scholarly text survive an adaptive author?"
d = new_doc(spacing=1.15, footer=False)
P(d, "Ook Lee", indent=False); P(d, "Hanyang University, Seoul, Republic of Korea", indent=False); P(d, "ooklee@hanyang.ac.kr", indent=False, after=10)
P(d, "[Date]", indent=False, after=10)
P(d, "The Editors", indent=False); P(d, "*Nature Machine Intelligence*", indent=False, after=10)
P(d, "**Manuscript: “" + T + "”**", indent=False, after=10)
P(d, "Dear Editors,", indent=False, after=8)
P(d, "I submit the manuscript above as an Article. It has not been published and is not under consideration elsewhere.", indent=False, spacing=1.3, after=8, align="justify")
H2(d, "The question and the findings")
P(d, "Publishers and research-integrity offices screen manuscripts for machine authorship, yet detectors are usually evaluated on text that no author has tried to disguise. I audit nine screens (two transparent count-based screens, six published detectors and a zero-shot language-model judge) on 474 human papers and machine papers from GPT-4o, Claude Sonnet 5.5 and Llama 3.3 70B, under six attacks, including attacks aimed at probability-based detectors. The main findings are:", indent=False, spacing=1.3, after=4, align="justify")
BUL(d, [
 "No detector is robust to every attack. Replacing half of a paper's sentences with human sentences lowers Fast-DetectGPT and a fine-tuned RoBERTa classifier from AUC 0.94 and 0.96 to 0.61 and 0.60 on Claude papers, while both stay above 0.83 on Llama papers.",
 "Probability-based scores invert under perturbation: disguised text is less probable than genuine human text, so log-likelihood drops to AUC 0.05, and a two-sided deviation score restores it to 0.90.",
 "A strong supervised baseline (TF-IDF) depends partly on structural artifacts: on an unseen generator its AUC falls from 0.85 to 0.66 when artifacts are removed and only function words are kept.",
 "The transparent count screen is less accurate than the best published detectors, so its case rests on explanation and cost, not accuracy. A zero-shot judge is robust to the attacks, partly because it notices damaged text.",
], size=None)
H2(d, "Relevance to the journal")
P(d, "The paper is a robustness audit of machine-text detection, an evaluation question of consequence for research integrity. It provides a common protocol, a cross-generator and adaptive-attack comparison of methods that are usually reported separately, a control for artifacts in supervised baselines, and a released code and data package.", indent=False, spacing=1.3, after=8, align="justify")
H2(d, "Limitations")
BUL(d, [
 "Three generators, one genre (English-language scientific papers), 100 attacked papers per generator and cell, and a judge run on a subset of one attack because of a spending cap.",
 "The study is an independent re-implementation: the original data and code of an earlier version of this work were not available, so all corpora, screens and attacks were rebuilt.",
 "Attackers are simple and none optimizes against a detector's gradient; zero-shot detectors used one open model pair.",
], size=None)
H2(d, "Compliance")
P(d, "No human participants or personal data are involved. Code and derived data are at https://doi.org/10.5281/zenodo.23664508 (MIT licence). I declare no competing interests. Generative AI was used as disclosed in the manuscript (coding assistant for analysis code and drafting; the studied texts and the judge are themselves AI outputs). Suggested reviewers: [to be completed]. I have no reviewers to exclude [to be confirmed].", indent=False, spacing=1.3, after=8, align="justify")
P(d, "Sincerely,", indent=False, after=24)
P(d, "Ook Lee", indent=False)
d.save("NMI_Audit_Cover_Letter.docx")
