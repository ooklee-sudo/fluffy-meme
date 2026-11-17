[Date]

The Editors
*Political Analysis*

Dear Editors,

We are pleased to submit our manuscript, "Consistent but Not Valid: How LLM Labels Bias Class-Specific Estimates," for consideration as a Letter in *Political Analysis*.

Political scientists increasingly use large language models (LLMs) to label text, and the agreement between repeated model runs is often reported as evidence that the labels are reliable. Our Letter shows why that evidence is not enough once the labels enter downstream inference. We study 191 posts by the U.S. president during the 2026 closure of the Strait of Hormuz, labelled by five LLM runs and by human coders whose disagreements were resolved by an independent third coder, and we link them to tick-level oil prices.

The Letter makes three contributions:

1. **Consistency is not validity.** The model runs agree with one another at κ = 0.69–0.84 but with the human coders at only κ = 0.44–0.49. They over-label escalation even when given the human coders' own codebook, and this holds even for the model that produced the original labels.
2. **Where the bias comes from.** We write the model-label estimate as an exact mixture of human-class means. This decomposition shows that the model labels understate the response to escalation because they add posts that humans read as de-escalation, not because correctly labelled posts respond less. It also shows that two label sets with similar κ and precision can bias an estimate by different amounts.
3. **The cost of correction.** A simulation on our fully labelled data shows that design-based corrections remove the bias but, with few events, need human labels for a third to a half of the corpus before they are more accurate than the biased estimate.

We believe the Letter fits *Political Analysis* because it extends a line of work published in the journal on validating automated text classification and on using machine-generated variables in regression (Grimmer and Stewart 2013; Fong and Tyler 2021). It ends with four reporting practices that apply to any study that carries LLM labels into downstream estimates. We are transparent about the evidence's limits. The escalation result rests on ten events, the human–model difference is not statistically significant on its own, and we make no causal claim about posts and prices.

The main text contains 1,982 words, excluding the title, abstract, and references (2,465 including tables and figure notes), with one figure and two tables. Supplementary Information accompanies the submission. On acceptance, we will deposit replication code, prompts, model outputs, coder sheets, and analysis plans in the *Political Analysis* Dataverse.

[This manuscript is original and is not under review elsewhere. A longer, earlier version with a different framing was submitted to *Information Systems Research* (manuscript ISRE-2026-4587); it has been [withdrawn / rejected] as of [date].]

Large language models were used as classification instruments in the study, as described in the manuscript. [State any use of generative AI in drafting, editing, or coding, consistent with the journal's policy.] [Funding statement.] [The authors declare no conflicts of interest.]

Thank you for considering our submission.

Sincerely,

[Corresponding author name]
[Affiliation]
[Email]
