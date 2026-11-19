Ook Lee
Department of Information Systems
Hanyang University
Seoul, 04763, Republic of Korea
ooklee@hanyang.ac.kr

[Date]

The Editor-in-Chief
*IEEE Software*

Dear Editor-in-Chief,

Please consider the enclosed manuscript, "Your LLM Judge Measures Your Protocol: Lessons from Trying to Explain Stack Overflow's Decline," for publication as a feature article in *IEEE Software*.

Many engineering teams now compare coding assistants by letting one large language model (LLM) grade another's answers. They use the resulting scores to choose which assistant to license, to detect regressions after a vendor update, and to judge which teams or languages benefit from a tool. Our article shows, through a concrete case, how fragile such scores can be.

We set out to test whether Stack Overflow lost the most questions in the topics where LLMs answer best. We built tag-level accuracy measures for 50 tags from nearly 2,000 Stack Overflow questions, using answers from four models graded by an LLM, and stress-tested the measures before using them. The results carry a lesson that reaches well beyond Stack Overflow:

- On the same questions, the grading rubric moved measured accuracy by up to 52 percentage points, and moving one sentence of instruction from the user message to the system message moved it by 11 points. Either change was enough to reverse the ranking of models.
- Accuracy levels per topic were moderately stable, but per-topic improvements between two model versions did not replicate across prompt formats.
- An apparently significant link between model capability and the loss of questions disappeared once placebo windows and a second capability measure were added. Without those checks, we would have reported several spurious effects.

The article closes with seven practices, presented as a sidebar, that teams and researchers can apply whenever LLM-graded accuracy informs a decision. We believe the article fits *IEEE Software*'s practitioner audience. It requires no specialized statistical background, and its message is directly actionable for anyone who evaluates or procures AI coding tools.

The manuscript is prepared in the Computer Society magazine template. It contains about 3,200 words, including references, table text, and the author biography, plus one figure and two tables. It has 13 references. All data, prompts, model outputs, and scripts are openly available on Zenodo (doi: 10.5281/zenodo.23829331).

A longer research version of this work was submitted to *Empirical Software Engineering* (EMSE-D-26-01502) and was returned without review because of that journal's reviewing capacity. The present article has been substantially rewritten for a practitioner audience. It has not been published previously and is not under consideration elsewhere. The use of AI tools in the study and in preparing the manuscript is disclosed in the Acknowledgments. The author declares no competing interests.

Thank you for your time and consideration.

Sincerely,

Ook Lee
Department of Information Systems, Hanyang University
