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

## ISR reference style (evidence from the same paper)

Entries in this ISR paper's list follow the pattern `Surname Initials, Surname Initials (Year) Title in sentence case. Journal abbreviation Volume(Issue):pages.` with abbreviated journal names, for example `Inform. Systems Res.`, `MIS Quart.`, `Proc. Natl. Acad. Sci. USA`, `Amer. Econom. Rev.`; conference papers as `Internat. Conf. Machine Learn. (PMLR, New York), 337–371`; books as `Bratman M (1987) Intention, Plans, and Practical Reason (Harvard University Press, Cambridge, MA)`. In-text citations are `Baird and Maruping (2021)` or `(Baird and Maruping 2021)`. The official INFORMS reference-style PDF itself has not been read.
