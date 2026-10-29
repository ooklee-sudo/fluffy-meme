---
title: ""
---

[Date: 29 October 2026]

Editor-in-Chief, *Information Systems Research*\
INFORMS\
[Name of the handling editor, if known]

**Re: Submission of "When the Platform Moves Underneath: Maintaining Complementary IT Assets under Endogenous Release Cadence"**

Dear Editor,

We are pleased to submit the enclosed manuscript, "When the Platform Moves Underneath: Maintaining Complementary IT Assets under Endogenous Release Cadence," for consideration as a research article in *Information Systems Research*.

**What the paper does.** Firms increasingly build complementary IT assets, such as fine-tuned adapters, on foundation-model platforms that they do not control, and every platform upgrade destroys some or all of that value. We ask how a firm should maintain such an asset after adoption and how the platform owner's choices of release cadence and compatibility support interact with that decision. We model the firm's choice among copying the asset, transferring it with a costly compatibility tool, and retraining it as a real option, and we let the platform owner, first as a monopolist and then in a logit duopoly with a release race, choose how often to release. We discipline the model with release histories of six open-weight model families and with recovery rates measured on open model pairs of 160M to 3B parameters on three tasks (math reasoning, summarization, and text-to-SQL).

## Statement of contribution

We see three contributions to the information systems literature.

1. **From adoption to post-adoption maintenance.** The real-options view of IT platforms (Fichman 2004; Benaroch and Kauffman 1999; Taudes et al. 2000) has focused on the timing of adoption. We move it to the maintenance of an asset that is already deployed on a platform that is replaced at a rate the asset owner does not choose. We show that the retraining threshold rises with the recovery rate as 1/(1 − *R*) and with upgrade intensity and volatility, that a free copy weakly dominates immediate retraining, and that a costly compatibility tool can be optimal only for assets of intermediate value and only when its cost is below a bound Γ. These regions do not depend on any named algorithm.

2. **The platform owner as the agent that sets the life of the option.** We treat release cadence as the owner's choice rather than a fact of nature. Compatibility tools and release speed are strategic complements for any distribution of asset values: better tools invite faster release and can leave the firms that retrain anyway worse off. A revenue-sharing owner over-releases if and only if the average customer is harmed at the margin by a faster clock. This connects boundary resources (Ghazawneh and Henfridsson 2013) to platform evolution (Tiwana et al. 2010), because resource provision and the pace of change turn out to be jointly determined.

3. **Platform competition and a practical rule.** Under logit duopoly each owner internalizes exactly one-third of the marginal change in customer surplus, and numerical analysis shows that an intermediate race separates owners into a fast, compatible frontier platform and a slow, stable one. For managers the results imply a simple default: copy by default, buy a transfer tool only when its measured cost is below Γ, and read owner-provided compatibility tooling as a signal of faster release. In the 24 pair-task combinations we tested, a costly transfer method had room to pay in only two, and we say explicitly where copy fails and retraining is the right choice.

**Fit with the journal.** The paper addresses platform governance, the value and maintenance of IT assets, and the economics of information systems, in the setting of foundation models that are becoming core infrastructure for firms. It extends two streams that *Information Systems Research* has published (real options in IT investment and platform evolution) and gives them an explicit maintenance channel.

## Declarations

- **Originality.** The manuscript is original, is not under consideration elsewhere, and has not been published in any form. [Optional, delete if you prefer not to state it: An earlier version was submitted to another journal and was not accepted. The present version has been substantially revised and extended, including new empirical evidence on additional tasks and model scales.]
- **Anonymity.** The manuscript has been prepared for double-blind review. The title page, author information, and acknowledgments are provided in a separate file.
- **Conflicts of interest.** [None to declare. Please confirm.]
- **Funding.** [State funding sources or "None."]
- **Data and code.** All numerical results can be reproduced with the replication package (scripts, per-seed results, and release-history data). An anonymized copy is available to reviewers on request. No proprietary or subscription data are used.
- **Use of generative AI.** [Disclose per the journal's policy. For example: "Generative AI tools were used to assist with code, numerical checks, and language editing. The authors designed the study, verified all results, and take full responsibility for the content."]

Thank you for considering our work. We would be glad to provide any further information.

Sincerely,

[Corresponding author name]\
[Affiliation]\
[Email]\
[On behalf of all authors]
