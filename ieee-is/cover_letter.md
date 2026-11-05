Ook Lee
Department of Information System
Hanyang University
Seoul, 04763, South Korea
ooklee@hanyang.ac.kr

[Date]

Editor-in-Chief
*IEEE Intelligent Systems*

Dear Editor-in-Chief,

I am pleased to submit the manuscript "Filter or Prior? What LLM Synthetic Agents Are Worth in Experimentation Pipelines" for consideration as a Feature Article in *IEEE Intelligent Systems*.

Platforms are beginning to use large language model (LLM) "digital twins" to screen design alternatives, such as headlines, defaults, and price displays, before spending real user traffic on A/B tests. Most published evaluations ask whether twins reproduce known behavioral effects on average. Practitioners need answers to two more practical questions. When is a twin informative? And when is it informative enough to change what gets tested? The article answers both.

The manuscript makes three contributions:

1. **A validity map from pre-registered tests.** Across five model families, three persona formats, and 13 model versions, twins recover the direction of cue-based effects such as framing and anchoring but not their magnitude. Default effects reverse in sign depending on whether the paradigm is familiar from training text. Extra reasoning reduces factual errors while increasing bias. Errors are specific to model versions.
2. **A decision model that turns validity into value.** A single quantity, the correlation ρ between twin scores and true effects, determines whether pre-screening pays. Filtering candidates on twin scores helps only below a break-even traffic budget N\*(ρ). For ρ ≤ 0.1, filtering never pays.
3. **A field evaluation on 500 public Upworthy headline experiments.** Four current models reach ρ = 0.13–0.23. At these values, discarding candidates on twin scores doubles the expected loss in click-through rate at realistic budgets. Using the scores as a calibrated prior is safe but saves only 1–3% of traffic.

The article ends with five quantitative rules that platform teams can apply before putting synthetic agents into an experimentation pipeline. I believe it suits the magazine's readership of researchers and practitioners who build and deploy intelligent systems. It addresses a decision many teams now face, it is written for a broad technical audience, and its central message is that the way an AI signal is used matters as much as whether the signal exists. The results are deliberately sobering, which I hope will make them a useful counterweight to the many positive demonstrations in this area.

The manuscript contains about 2,000 words of main text including a sidebar (2,750 words if each figure and table is counted as 250 words), a 155-word abstract, one figure, two tables, and 14 references. It was prepared with the IEEE Computer Society magazine template.

I confirm the following:

- **Originality.** The manuscript is original, has not been published, and is not under consideration by any other journal or magazine.
- **Related submission.** I am also submitting a separate article to *IEEE Intelligent Systems*, "Same Model, Different Shortcuts: How Prompt Layout Steers LLM Operators to Skip Verification." The two papers share a broad interest in auditing LLM agents before organizations delegate to them, but they address different problems with different data. That article studies whether LLM operators skip verification steps in a maintenance task. The present article studies whether LLM-simulated users can stand in for human A/B test participants. Neither paper reuses data or results from the other.
- **Preregistration.** The confirmatory studies were pre-registered (AsPredicted #320110 and #320124). All registered predictions are reported, including those that were not supported.
- **Data and code.** No new human data were collected. The human benchmarks (Twin-2K-500 and the Upworthy Research Archive) are public. Prompts, model outputs, and analysis code will be made publicly available at [repository URL].
- **Use of AI tools.** As stated in the Acknowledgments, I used Claude (Anthropic), an AI assistant, to help draft and edit the text, to write the simulation and analysis code, and to prepare Figure 1. I reviewed, revised, and verified all content, including every reported number.
- **Competing interests.** I have no competing interests to declare.

Thank you for considering this submission. I look forward to hearing from you.

Sincerely,

Ook Lee
Professor, Department of Information System
Hanyang University
