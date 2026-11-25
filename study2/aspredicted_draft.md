---
title: "AsPredicted Preregistration (Draft)"
---

**Status:** DRAFT for submission at AsPredicted before any data are collected. Items in [square brackets] must be completed before submission. AsPredicted asks for short answers, so details (stimulus production, full survey text, analysis code) go in the attached files listed under question 8.

# 1) Have any data been collected for this study already?

No, no data have been collected for this study. A pilot of about [10] participants will be run first to check instructions and timing; pilot data will be excluded from all analyses.

# 2) What's the main question being asked or hypothesis to be tested?

Main question: does showing an *exaggerated* (edited to look better) photograph of a short-term rental room, instead of a *faithful* photograph of the same room, change how the room is valued before the truth is shown, and how it is judged after the true room is revealed?

Hypotheses, all comparing the exaggerated condition (L2) with the faithful condition (L0) of the same physical room:

- **H1(a).** Before the reveal, exaggerated photographs raise perceived quality and willingness to pay (WTP).
- **H2(a).** The change in WTP after the reveal (post-reveal WTP minus pre-reveal WTP) is more negative for exaggerated than for faithful photographs.
- **H3(a).** After the reveal, exaggerated photographs lead to more negative expectation disconfirmation, lower hypothetical star ratings, and lower perceived host honesty.

# 3) Describe the key dependent variable(s) specifying how they will be measured.

Confirmatory (six outcomes):

1. *Pre-reveal WTP* (H1(a)): maximum price per night, open numeric box, in US dollars, entered before any price anchor is shown.
2. *Perceived quality index* (H1(a)): mean of four seven-point ratings of how clean, spacious, bright, and well maintained the place looks.
3. *WTP revision* (H2(a)): post-reveal WTP minus pre-reveal WTP for the same listing.
4. *Expectation disconfirmation* (H3(a)): "Compared to what you expected from the first photograph, how is the actual place?" 1 = much worse than expected, 4 = exactly as expected, 7 = much better than expected.
5. *Hypothetical star rating* (H3(a)): the rating (1 to 5 stars) the participant would leave after staying.
6. *Perceived host honesty* (H3(a)): seven-point agreement with "The host presented this place honestly in the first photograph."

Exploratory (not used to test the hypotheses): initial listing trust (seven-point), booking intention at a fixed price of \$130 per night (yes or no), post-reveal WTP, and rebooking intention (seven-point).

# 4) How many and which conditions will participants be assigned to?

Two conditions, manipulated within participants and within rooms:

- **L0 Faithful:** standard 28 mm-equivalent lens, natural light, no staging beyond basic housekeeping.
- **L2 Exaggerated:** ultra-wide 16 mm-equivalent perspective, brightness and contrast enhancement, and generative AI inpainting [tool and version] that removes clutter, cords, wall scuffs, and worn textiles. Edits are limited to removal and surface enhancement. No amenities are added.

Each participant evaluates six rooms drawn at random from a pool of 24 real rooms photographed by the authors: three in L0 and three in L2. The assignment of rooms to conditions and the presentation order are randomized for each participant, and no participant sees the same room in both conditions. In Block 1, participants rate each listing from one cover photograph. In Block 2, after all six listings are rated, they see the same listings again with the original cover photograph beside three unedited photographs of the real room, and they answer the Block 2 questions. Before the main study, an independent sample of [45] raters will check that, for each room, the exaggerated version scores higher than the faithful version on perceived spaciousness, brightness, and cleanliness; rooms that fail are re-edited.

# 5) Specify exactly which analyses you will conduct to examine the main question/hypothesis.

For each of the six confirmatory outcomes, we will fit a linear mixed-effects model with crossed random intercepts for participants and rooms:

Outcome = b0 + b1 × Exaggerated + g × TrialPosition + participant intercept + room intercept + error.

The test is b1 (two-sided, alpha = .05), with the predicted sign: b1 > 0 for pre-reveal WTP and the quality index (H1(a)); b1 < 0 for WTP revision (H2(a)); b1 < 0 for disconfirmation, star rating, and host honesty (H3(a)). The six tests form one family, and p values are adjusted with the Holm procedure. We report adjusted and unadjusted p values, 95 percent confidence intervals, and standardized effect sizes. H3(a) is counted as supported only if all three of its outcomes have the predicted sign, and we report which of them are significant. If a model does not converge, we drop the room intercept and report this. Exploratory outcomes use the same model and are labeled exploratory.

Robustness checks: (a) standard errors clustered two-way by participant and room; (b) the interaction of condition with trial position; (c) the analysis restricted to the first room each participant evaluates (a pure between-subject comparison, interpreted as a check on direction and size); (d) WTP analyses on log WTP, and with and without observations flagged under question 6; (e) a repeated-measures model of WTP with a condition-by-stage (pre versus post reveal) interaction.

Exploratory mediation: bootstrap confidence intervals (5,000 resamples of participants) for whether disconfirmation and perceived host honesty carry the post-reveal effect on star rating and post-reveal WTP. We will describe results as consistent or inconsistent with three accounts (inference about the host's type, a fairness-based reaction to broken trust, and reference-dependent loss aversion), and we will not claim to separate them.

# 6) Describe exactly how outliers will be defined and handled, and your precise rule(s) for excluding observations.

Participants are excluded, and replaced to reach the target, if they (a) fail the embedded attention check [item text to be written], (b) do not finish both blocks, or (c) complete the survey in less than [one third] of the pilot median time. Participants are never excluded on the basis of their answers to the outcome questions.

Outliers: any WTP response below \$10 or above \$1,000 per night is flagged as invalid for the WTP analyses (the flag is set before looking at condition effects). The WTP analyses are run with and without the flagged observations, and both results are reported. No other observations are removed, and all exclusions are counted and reported.

# 7) How many observations will be collected or what will determine sample size?

The target is 120 participants after exclusions, which gives 720 room-level observations (360 per condition). Recruitment on Prolific (age 18 or older, resident in the United States or United Kingdom, fluent in English, booked a short-term rental in the previous two years) continues until 120 valid participants are reached. We will not look at outcome data before the target is reached, and we will not stop or extend data collection on the basis of the results.

Rationale: in a simulation of the design (crossed participant and room random intercepts, each 25 percent of the variance, alpha = .05), 120 participants give a power of about .64 for a standardized condition effect of 0.15, about .89 for 0.20, and at least .99 for 0.30 or more (code: study2/power.py).

# 8) Anything else you would like to pre-register?

- *Ethics and data:* [IRB or ethics approval number]. Anonymized data, the survey instrument, stimulus identifiers, and analysis code will be shared at publication. The analysis code [file name] will be attached to this registration before data collection starts and run unchanged on the final data.
- *Deviations:* any deviation from this registration will be documented in the paper with the reason.
- *Not part of this registration:* the paper also contains an observational field study (Study 1). Possible follow-up experiments (a condition in which the photograph undersells the room, a delayed memory-based reveal, and a manipulation of information about attributes a photograph cannot show) will be registered separately if run.

# 9) Give a title for this AsPredicted pre-registration

[Visual overstatement of listing photographs: effects on valuation before and after the reveal (within-subject experiment)]

*Type of study (if asked): experiment or survey.*
