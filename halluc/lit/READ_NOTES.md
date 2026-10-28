# Notes on papers actually read

Only papers whose text was provided or retrieved and read are listed. For each: what was read, what it shows, and how it may be cited. Anything not listed here has **not** been read and should not be cited from this repository's notes.

## Leng & Yuan (2026), Information Systems Research

**Reference.** Leng Y, Yuan Y (2026) SUVA: A probabilistic framework for auditing LLMs with an application to social preferences. *Inform. Systems Res.* 37(3):1805–1830. https://doi.org/10.1287/isre.2024.0857 (received January 23, 2024; accepted January 2, 2026; Senior Editor Ravi Bapna, Associate Editor Pallab Sanyal; published online in advance February 23, 2026).

**What was read.** The PDF supplied by the authors (27 pages): pages 1805–1808 (abstract, introduction, contributions, start of literature review and methods, Figure 1) and 1824–1827 (applications, discussion and conclusion, start of the endnotes) were read as page images; the whole text was searched with a text extraction for the terms below. The methods and results pages in between (about 1809–1823) were **not** read in detail.

**What it does.** It introduces SUVA (state–understanding–value–action), a probabilistic framework for auditing the behavior of language models from their text: it relates the values a model states in its chain-of-thought to the action it finally takes, using prompts adapted from behavioral-economics games. It is applied to social preferences in eight LLMs, to the effect of post-training (supervised fine-tuning, direct preference optimization), and to three delegation scenarios (platform–influencer, customer-service chatbot, team bonus allocation). Its stated purpose is pre-deployment auditing of whether LLM behavior aligns with organizational values.

**Overlap with our manuscript.** None found. A full-text term search returned no occurrence of *hallucination*, *factual*, *audit budget/effort*, *human review/oversight*, *cluster*, *dispersion*, *Fano*, or *Poisson*; "verify" appears three times and refers to verifying alignment; "accuracy" refers to how well stated values predict actions and "error" to error bars. The paper audits behavioral dispositions before deployment; our paper concerns the allocation of run-time human verification of factual errors.

**How it may be cited (suggested wording, to be checked by the authors).** As an ISR precedent that auditing LLM output is an information-systems topic, and as a contrast: "Closely related work audits the behavior of language models before deployment, linking a model's stated reasoning to its final decisions (Leng and Yuan 2026). We address a complementary problem..."

**Useful for the manuscript's form.** The paper has a "Contributions" subsection in the introduction, a literature review split into two subsections, applications, and a "Discussion and Conclusion" with "Practical and Methodological Implications" and "Theoretical Implications" subsections; supplementary material is an online appendix. Its reference list shows ISR's reference style (see below).

**References it cites that look relevant to our Section 2 (not read; known only from the reference list).**
- Baird A, Maruping LM (2021) The next generation of research on IS use: A theoretical framework of delegation to and from agentic IS artifacts. *MIS Quart.* 45(1):315–341.
- Berente N, Gu B, Recker J, Santhanam R (2021) Managing artificial intelligence. *MIS Quart.* 45(3):1433–1450.
- Jussupow E, Spohrer K, Heinzl A, Gawlitza J (2021) Augmenting medical diagnosis decisions? An investigation into physicians' decision-making process with artificial intelligence. *Inform. Systems Res.* 32(3):713–735.
- Abdel-Karim BM, Pfeuffer N, Carl KV, Hinz O (2023) How AI-based systems can induce reflections: The case of AI-augmented diagnostic work. *MIS Quart.* 47(4):1395–1424.
- Adam M, Roethke K, Benlian A (2023) Human vs. automated sales agents: How and why customer responses shift across sales stages. *Inform. Systems Res.* 34(3):1148–1168.
- Fügener A, Grahl J, Gupta A, Ketter W (2022) Cognitive challenges in human–artificial intelligence collaboration: Investigating the path toward productive delegation. *Inform. Systems Res.* 33(2):678–696. (This entry **confirms the bibliographic data** of the reference used in our manuscript.)

## Bouayad, Padmanabhan & Chari (2019), Information Systems Research

**Reference.** Bouayad L, Padmanabhan B, Chari K (2019) Audit policies under the sentinel effect: Deterrence-driven algorithms. *Inform. Systems Res.* 30(2):466–485. https://doi.org/10.1287/isre.2019.0841 (received November 12, 2015; accepted December 3, 2018; Senior Editor Yong Tan, Associate Editor Ahmed Abbasi).

**What was read.** The PDF supplied by the authors (21 pages), as extracted text: the abstract, introduction, the statement of the audit problem (start of Section 2), the discussion with its limitations, and the conclusions were read; the details of the diffusion model, the survey, the algorithm and the simulation (Sections 2.2–5) were **not** read closely, and the online appendices (analytical model, game) are not part of the PDF.

**What it does.** Audit selection as an algorithm-design problem in health-care claims: given a network of practitioners, choose k practitioners to audit so as to maximize detection of fraudulent ones and the "sentinel effect", the deterrence that arises when audit information diffuses by word of mouth and other practitioners improve their billing. A greedy search selects the k nodes; an agent-based simulation, informed by interviews, a focus group and a physician survey, compares deterrence-driven selection with detection-driven selection and with broadcasting. The paper states that audit cost is not modeled in the simulation (an analytical treatment is in an online appendix).

**Statements in the text that bear on our manuscript.**
- "Much of the prior work in auditing algorithms has focused on use of scoring to detect fraudulent providers. We call these detection algorithms" (scoring algorithms compute suspicion indices used to select claims for investigation).
- The benefits of an audit are separated into the direct "audit effect" (detection) and the second-order "sentinel effect" (deterrence through diffusion).

**Overlap with our manuscript.** None on the object of audit: the audited parties are strategic practitioners who respond to audits, the setting is a social network, and the objective includes deterrence. Our problem has the scoring-and-selection structure but the verified content is produced by a model, so (absent retraining on audit outcomes) only the detection benefit remains, and the structure we study lies within a generated text, not across a network.

**How it may be cited (suggested wording, to be checked by the authors).** "Audit selection has been studied as an algorithm-design problem in information systems research: scoring models rank items by suspicion, and when audited parties respond, the objective is extended to include deterrence (Bouayad et al. 2019). Our setting has the scoring but not the deterrence."

**References it cites that look relevant (not read; bibliographic data as printed in its reference list).**
- Dionne G, Giuliano F, Picard P (2009) Optimal auditing with scoring: Theory and application to insurance fraud. *Management Sci.* 55(1):58–70. (Described in the paper as discussing scoring algorithms within an optimal auditing strategy, including the value of auditing some claims even when investigation cost exceeds the expected benefit; not read.)
- Tennyson S, Salsas-Forn P (2002) Claims auditing in automobile insurance: Fraud detection and deterrence objectives. *J. Risk Insurance* 69(3):289–308.
- D'Arcy J, Hovav A, Galletta D (2009) User awareness of security countermeasures and its impact on information systems misuse: A deterrence approach. *Inform. Systems Res.* 20(1):79–98.
- Van Vlasselaer V, Eliassi-Rad T, Akoglu L, Snoeck M, Baesens B (2017) GOTCHA! Network-based fraud detection for social security fraud. *Management Sci.* 63(9):3090–3110.

**Useful for the manuscript's form.** Contributions are enumerated in the introduction ("first to..."; we should avoid priority claims we cannot support), a mixed-method design is used for realism, and analytical results are placed in online appendices.

## Taudien, Fügener, Gupta & Ketter (2026), Information Systems Research ("Just Accepted")

**Reference.** Taudien A, Fügener A, Gupta A, Ketter W (2026) Enhancing AI use: How complementary system information drives delegation frequency and effectiveness. *Inform. Systems Res.* Published online in Just Accepted, September 4, 2026. https://doi.org/10.1287/isre.2024.1330. This is the unedited accepted manuscript; volume, issue and pages do not exist yet and the text may change in production.

**What was read.** The supplied PDF (40 pages) as extracted text: the abstract, the introduction with its contributions, and the discussion subsections "Practical Implications" and "Limitations and Future Research". The hypotheses, the experimental procedure, the measures and the results sections were **not** read in detail. A term search found no occurrence of *hallucination*, *language model*, *generative*, *LLM*, or *audit*.

**What it does.** An online experiment (n = 560, image classification, a 2×2 between-subjects design) in which people decide which tasks to delegate to an AI classifier. It manipulates ex-ante "AI certainty" (the AI's estimated probability of being correct, shown before the decision) and ex-post "AI outcome" information (whether the AI was right, shown afterwards). Reported findings (from the abstract and introduction): either signal alone has no or a negative effect on combined human–AI performance (outcome information alone lowers delegation frequency and effectiveness; certainty alone raises frequency but not effectiveness); both together raise delegation frequency and effectiveness and yield performance above that of humans or the AI alone. The authors explain this by users' mental models of the AI's capabilities, using expectation confirmation theory and situation awareness theory.

**Statements in the text that bear on our manuscript.**
- Limitations: certainty scores help "only if" they accurately reflect the AI's actual performance; effectiveness "may depend on both the level and variance" of the scores, since low variance limits the ability to distinguish tasks; providing outcome information for every decision "may not always be feasible."
- Practical implications mention content moderation, diagnostic pre-screening and fraud flagging as settings where humans decide whether to hand over individual tasks, and link the discussion to human oversight in the EU AI Act.

**Overlap with our manuscript.** None on the object of study (delegation of tasks to an image classifier versus allocation of verification to generated text), but the two share the structure of a machine signal about correctness, human reliance on it, and feedback on outcomes. Their caveats about calibration and variance correspond to our dependence on the calibration and the dispersion of predicted risk (Proposition 2).

**How it may be cited (suggested wording, to be checked by the authors).** "Experimental work on delegation to an image classifier finds that a probability-of-correctness signal shown before a decision and feedback on outcomes shown afterwards help users decide when to rely on the machine only in combination (Taudien et al. 2026)." Update the reference if the article has appeared in an issue before submission.

**References it cites that look relevant (not read; bibliographic data as printed in its reference list).**
- Bauer K, von Zahn M, Hinz O (2023) Expl(AI)ned: The impact of explainable artificial intelligence on users' information processing. *Inform. Systems Res.* 34(4):1582–1602.
- Hemmer P, Schemmer M, Kühl N, Vössing M, Satzger G (2025) Complementarity in human-AI collaboration: Concept, sources, and evidence. *Eur. J. Inform. Systems* 34(6):979–1002.
- Vaccaro M, Almaatouq A, Malone T (2024) When combinations of humans and AI are useful: A systematic review and meta-analysis. *Nature Human Behav.* 8(12):2293–2303.
- Adam M, Diebel C, Goutier M, Benlian A (2024) Navigating autonomy and control in human-AI delegation: User responses to technology- versus user-invoked task allocation. *Decision Support Systems* 180:114193.
- Dietvorst BJ, Simmons JP, Massey C (2015) Algorithm aversion: People erroneously avoid algorithms after seeing them err. *J. Experiment. Psych. General* 144(1):114–126.

## Jussupow, Bauer, Heigl, Vogt & Hinz (2026), Information Systems Research

**Reference.** Jussupow E, Bauer K, Heigl RM, Vogt B, Hinz O (2026) The indirect disclosure effect: How disclosing generative AI use impacts human creative collaboration with AI. *Inform. Systems Res.* Published online in Articles in Advance August 27, 2026 (pp. 1–21). https://doi.org/10.1287/isre.2024.0951 (received March 1, 2024; accepted June 1, 2026; Senior Editor Ulrike Schultze, Associate Editor Aron Lindberg).

**What was read.** The supplied PDF (22 pages) as extracted text: the abstract, the discussion (summary of findings, theoretical contributions, policy implications, the start of the limitations) and the relevant reference entries. The theory development, the two experiments' procedures and the results were **not** read in detail. A term search found no occurrence of *hallucination*, *factual*, *verify*, *audit*, *oversight* or *detect*.

**What it does.** Two nested mixed-methods experiments in which participants create images with a text-to-image GenAI tool under different disclosure conditions. Drawing on Goffman's impression management, it shows an "indirect disclosure effect": when creators anticipate that GenAI use will be disclosed to an audience, most withdraw from the creative process and leave image generation to the tool, driven by the fear that audiences will not recognize their creative agency; the resulting artifacts are judged more novel but less appealing. The authors read this as a tension in transparency regulation (they mention Article 50 of the EU AI Act) but stress that it does not show that transparency is undesirable.

**Statements in the text that bear on our manuscript.**
- Policy implications: binary labels may be too coarse; process-level documentation (iterative prompting, selection, revision, post-generation editing) and content-provenance standards (the Coalition for Content Provenance and Authenticity is named, with metadata-based records of content history) point to a nuanced approach that "may mitigate" creator withdrawal.
- Limitations: image creation only; modalities such as writing may differ; anonymous settings without reputational stakes; open whether the effect persists for "more technical" tasks.

**Overlap with our manuscript.** None on verification or factual errors. It bears on Section 8.2 as a boundary: our recommendation concerns provenance metadata used internally to route review, not labels shown to audiences, and whether recording provenance changes how authors use a tool is, for text generation in organizations, untested.

**How it may be cited (suggested wording, to be checked by the authors).** See Section 8.2 of the manuscript.

## Shi & Viswanathan (2023), Information Systems Research — read; not relevant; do not cite

**Reference.** Shi L, Viswanathan S (2023) Optional verification and signaling in online matching markets: Evidence from a randomized field experiment. *Inform. Systems Res.* 34(4):1603–1621. https://doi.org/10.1287/isre.2022.1194.

**What was read.** The supplied PDF (20 pages) as extracted text: the abstract, the introduction, and a term search over the whole text.

**What it is.** A randomized field experiment on an online dating platform. "Verification" means **phone verification of a user's identity**, offered as an optional, visible, credible signal; the study asks who opts in, how verified users are treated by others, and the effect on matching, comparing free and paid verification. There is no model of verification effort or cost, no detection of errors, and no treatment of generated content (no occurrence of *hallucination*, *budget*, *verification cost*, *generative*, *language model*).

**Conclusion.** The title-based guess in `CANDIDATES.md` ("modeling conventions for verification costs and signals") was **wrong**: the paper does not bear on our problem. It would be padding to cite it. It is mentioned here only so that nobody cites it on the strength of its title.

## ISR reference style (evidence from the same paper)

Entries in this ISR paper's list follow the pattern `Surname Initials, Surname Initials (Year) Title in sentence case. Journal abbreviation Volume(Issue):pages.` with abbreviated journal names, for example `Inform. Systems Res.`, `MIS Quart.`, `Proc. Natl. Acad. Sci. USA`, `Amer. Econom. Rev.`; conference papers as `Internat. Conf. Machine Learn. (PMLR, New York), 337–371`; books as `Bratman M (1987) Intention, Plans, and Practical Reason (Harvard University Press, Cambridge, MA)`. In-text citations are `Baird and Maruping (2021)` or `(Baird and Maruping 2021)`. The official INFORMS reference-style PDF itself has not been read.

## Dionne, Giuliano & Picard (2009), Management Science

**Reference.** Dionne G, Giuliano F, Picard P (2009) Optimal auditing with scoring: Theory and application to insurance fraud. *Management Sci.* 55(1):58–70. https://doi.org/10.1287/mnsc.1080.0905.

**What was read.** The supplied PDF as extracted text: abstract, introduction, model setup, Propositions 1–3, the budget-constrained corollary, the start of the signal-manipulation section and the conclusion. The calibration and the e-companion appendices were **not** read in detail.

**What it shows.** Optimal auditing combined with a fraud-scoring "suspicion index" i: the insurer's optimal strategy is a type-dependent "red flags strategy" (audit if i exceeds a threshold i*), deterministic from the insurer's viewpoint, random from the policyholder's. Audits deter, so the optimal rule can audit claims whose direct expected gain is negative (needs commitment), and the rule stays threshold-shaped under a budget constraint (Corollary 1) and some signal manipulation.

**Overlap with us.** A threshold rule on an estimated risk score is not new: it is the scoring-based audit rule. Ours is the no-deterrence counterpart (the generator does not respond to checks), where the direct benefit-cost rule is optimal. Our novelty lies in the Cox/overdispersion measurement link, the value-of-targeting identity, adaptivity result and the empirical structure, not in the threshold form.

**Suggested wording.** "In audit settings with scoring, the optimal rule refers a case when its suspicion index exceeds a threshold, and deterrence can justify audits whose direct expected gain is negative (Dionne et al. 2009)."

## Fügener, Grahl, Gupta & Ketter (2022), Information Systems Research — read

**Reference.** Fügener A, Grahl J, Gupta A, Ketter W (2022) Cognitive challenges in human–artificial intelligence collaboration: Investigating the path toward productive delegation. *Inform. Systems Res.* 33(2):678–696. https://doi.org/10.1287/isre.2021.1079.

**What was read.** The supplied PDF (20 pages) as extracted text: abstract, introduction, theory (Sections 2.1–2.3, start of 2.4), the discussion and limitations (Section 5). The experimental procedures (Studies 1–4) and tables were **not** read in detail. A term search found no occurrence of *hallucination*, *verif-*, *audit*, *language model* or *generative*.

**What it shows.** Image-classification experiments with MTurk workers (humans and an AI classify; either may delegate to the other). The AI delegating uncertain images to humans ("inversion") beats the AI alone; humans delegating to the AI do not benefit, even when taught a good delegation rule, because they lack metaknowledge (cannot judge their own capability and task difficulty). Not explained by algorithm aversion. Combined optimum reported as 89.9% against 77% (AI alone) and 71.7% (humans alone).

**Overlap with us.** No overlap on verification of generated text. It supports the argument that review should be routed by external signals, not by the reviewer's own judgment of where errors lie. Boundaries: images, lay crowd workers, classification, not factual checking.
