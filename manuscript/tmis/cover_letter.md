Ook Lee
Hanyang University
Seoul, Republic of Korea
ooklee@hanyang.ac.kr
ORCID: 0000-0003-4361-7927

[Date]

Editor-in-Chief
*ACM Transactions on Management Information Systems*

Dear Editor-in-Chief,

I am pleased to submit the manuscript "**Switching the Ruler: Measurement-System Risk and Real Options in Generative AI Maintenance**" for consideration as a Research Article in *ACM Transactions on Management Information Systems*.

**The problem.** Organizations increasingly maintain generative AI systems with other AI systems. A judge model scores outputs, an optimizer searches for prompts that raise the score, and a release review promotes the policy that scores best. This practice rests on a measure that is cheap, that the organization itself optimizes against, and that vendors can change without notice behind a stable model name. Real options research on IT investment, which has guided how IS scholars and managers think about staging and abandoning IT commitments, assumes that the measure used to update beliefs stays attached to the asset it measures. The manuscript asks what happens to the logic of IT commitment when that assumption fails.

**Contributions.** The manuscript makes two theoretical contributions and two supporting ones.

1. It introduces *measurement-system risk*, the risk that the instrument used to observe the value of an IT asset is biased, collapsing, or jumping. It defines the construct through an explicit observation equation, distinguishes its three forms, and shows why it cannot be absorbed into the technical, organizational, market, and competitive risk classes of option-based IT risk management.
2. It defines the *switch-the-ruler option*, an option written on the measurement instrument rather than on the project: the right to pin a judge version, to refuse comparisons across a suspected change, and to recalibrate the judge against independent inspection. The manuscript shows that the classical IT option menu depends on this option and proves that its value vanishes when the judge becomes uninformative, so organizations should pin informative judges and replace uninformative ones.
3. A formal option model yields six propositions on when promoting on judge scores commits too early. An extension shows that inspection both detects and deters gaming and determines how strongly pay can safely be tied to judge scores.
4. Computational experiments with open-weight models on 200 verifiable math problems show that the problem depends on the judge. Search against a strong judge raised accuracy by 14.5 points over a control arm (t(199) = 4.90, p < .001), and the gain was significantly smaller under a weak judge (difference 10.5 points, t(199) = 2.33, p = .021). Under the weak judge, correctness peaked early while the judge score kept rising, which is the pattern of proxy overoptimization.

**Fit with ACM TMIS.** The manuscript addresses the journal's evaluation criteria directly.

- *MIS relevance:* it extends two established IS literatures, real options in IT investment and organizational control, to the governance of generative AI systems.
- *Scientific rigor:* the constructs are formally defined, the propositions and model results are proved in the appendices, and the experiments report exact tests on per-question data.
- *Innovation:* measurement-system risk and the switch-the-ruler option have no counterparts in the existing option-based IT risk literature.
- *Societal relevance and design:* the analysis translates into a concrete design for release governance, an options ledger that versions the judge, separates development, holdout, and canary evaluation items, and gates promotion on independent inspection. These are decisions that organizations deploying generative AI now make every week, often on the strength of a single dashboard number.

The manuscript is not a purely theoretical paper: its theory is paired with a formal model and with experiments whose code and complete per-question raw data are provided as supplementary material for replication.

**Declarations.** The manuscript is original, has not been published elsewhere, and is not under consideration by any other journal. No paper by the author overlaps substantially with this submission. The main text is approximately 5,800 words, within the journal's guideline for Research Articles; proofs, derivations, and model details are in the appendices. The research involved no human participants. [Optional, per ACM policy on generative AI: describe any use of generative AI tools in preparing the manuscript, consistent with the disclosure in the Acknowledgments.]

**Suggested Associate Editors.** [Optional: name one or two Associate Editors without conflicts of interest whose expertise covers IT investment, real options, or AI governance.]

Thank you for considering this submission. I look forward to hearing from you.

Sincerely,

Ook Lee
Hanyang University
