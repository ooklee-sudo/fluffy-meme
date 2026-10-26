import sys; sys.path.insert(0, "/home/user/fluffy-meme/isr_submission/manuscript_build")
from docbuild import *
T = "Detecting machine-written scholarly text depends on the generator and on what authors know"
d = new_doc(spacing=1.15, footer=False)
P(d, "[Date]", indent=False, after=10)
P(d, "The Editors", indent=False); P(d, "*Nature Machine Intelligence*", indent=False, after=10)
P(d, "**Manuscript: “" + T + "”**", indent=False, after=10)
P(d, "Dear Editors,", indent=False, after=8)
P(d, "We submit the manuscript above as an Article. It has not been published and is not under consideration elsewhere.", indent=False, spacing=1.3, after=8, align="justify")
H2(d, "The question and the finding")
P(d, "Organizations that screen documents for machine authorship must decide how much to spend, yet detection research reports accuracy for one generator at a time, without base rates, costs or adaptive authors. We study cascaded screening, in which a free screen built from counts of small linguistic events decides which documents reach a costly language-model judge, using 474 human papers and papers from GPT-4o, Claude and Llama. Our main findings are:", indent=False, spacing=1.3, after=4, align="justify")
BUL(d, [
 "Screens detect machine papers well only within a generator (AUC 0.99 within GPT-4o, 0.73 when trained on GPT-4o and tested on Claude, and near chance with human-only training).",
 "A strong judge (Gemini 2.5 Pro, AUC 0.97 on two generators) almost completely misses a third generator (AUC 0.66; 1% of Claude papers flagged).",
 "A cascade keeps most of the judge's detection at lower cost when machine papers are rare (savings up to 71% in illustrative cost settings), but depends on the screen.",
 "A crude feature-aware edit cuts the screen's detection from 53% to 8% and weakens the cascade, whereas a generic LLM rewrite does not evade the screen, and neither attack fools the judge.",
], size=None)
H2(d, "Why this is relevant to the journal's readers")
P(d, "The paper is about how to evaluate and deploy machine-text detectors, a question of growing consequence for research integrity. It shows that headline accuracy, reported for one generator without adversaries, can mislead decisions about deployment, and it offers a simple decision model that links detector performance to base rates, costs and author behaviour. We recognize that the paper combines empirical results with a decision model drawn from economics and that its empirical base is modest; we would welcome the editors' view on fit and are happy to send a pre-submission inquiry if that is more appropriate.", indent=False, spacing=1.3, after=8, align="justify")
H2(d, "Limitations")
BUL(d, [
 "Three generators, one genre (English-language scientific papers) and two judges; samples are modest and the judged subset is 500 documents.",
 "We did not compare against other published detectors, embedding-based methods, or human reviewers, and the attacks are not the strongest conceivable.",
 "Costs of review and of a missed paper, and the base rate, are assumed; cost results are structural illustrations.",
 "The clustering model was designed after baseline results were seen; its confirmatory test uses one held-out generator.",
], size=None)
H2(d, "Compliance")
P(d, "No human participants or personal data are involved. The prompts, generated papers and analysis code will be deposited in a public repository [DOI to be added]. The authors declare no competing interests [to be confirmed]. [State how generative AI tools were used in preparing the manuscript, code and analysis, as the journal's policy requires.] Suggested reviewers: [to be completed].", indent=False, spacing=1.3, after=8, align="justify")
P(d, "Sincerely,", indent=False, after=24)
P(d, "[Corresponding author]", indent=False)
d.save("NMI_Screening_Cover_Letter.docx")
