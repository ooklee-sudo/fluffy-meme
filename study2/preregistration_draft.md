---
title: "Preregistration (Draft): Does Visual Overstatement of Listing Photographs Raise Valuation Before the Reveal and Lower It After? A Within-Subject Experiment"
---

**Format:** OSF Preregistration (pre-data-collection), drafted for submission before any Study 2 data are collected.
**Status:** DRAFT. Items in [square brackets] must be completed or confirmed before registration. No Study 2 data have been collected.
**Date drafted:** 2026-11-25

# 1. Study Information

**Title.** Does visual overstatement of listing photographs raise valuation before the reveal and lower it after? A within-subject online experiment (Study 2 of "When Photos Promise More Than Places Deliver").

**Authors.** [Names and affiliations].

**Ethics.** [IRB or ethics committee name and protocol number, approval date]. Participants give informed consent before starting. No deception beyond the stimulus manipulation described below; a debrief page explains that some photographs were digitally edited.

**Description.** Guests usually see a short-term rental only through photographs. We test the causal effect of showing an *exaggerated* (edited to look better) photograph of a room, compared with a *faithful* photograph of the same room, on (a) valuation before the true room is revealed, (b) the revision of valuation when the true room is shown, and (c) disconfirmation, hypothetical ratings, and perceived host honesty after the reveal. The study is the experimental part of a paper that defines *visual overstatement* as the gap between what a photograph conveys about an attribute and what guests experience.

## Hypotheses

All hypotheses are directional and refer to the exaggerated condition ($L_2$) relative to the faithful condition ($L_0$) of the same physical room.

- **H1(a), face-value valuation.** Before the reveal, exaggerated photographs raise perceived quality and stated willingness to pay (WTP).
- **H2(a), correction.** The fall in WTP after the real place is shown is larger for exaggerated than for faithful photographs. That is, $\Delta WTP = WTP_{post} - WTP_{pre}$ is lower (more negative) in $L_2$ than in $L_0$.
- **H3(a), penalty.** After the reveal, exaggerated photographs lead to more negative expectation disconfirmation, lower hypothetical star ratings, and lower perceived host honesty than faithful photographs of the same room.

Secondary, non-directional expectations (reported but not used to test the hypotheses above): trust and booking intention before the reveal; rebooking intention and post-reveal WTP after the reveal.

# 2. Design Plan

**Study type.** Experiment, randomized, within-subject, online.

**Blinding.** Participants are not told the hypothesis or that two versions of each room exist. Participants never see the same room in both conditions. Condition labels are not shown in the interface. Analysts are not blind to condition, but the analysis code is fixed in advance (see Section 6) and will be uploaded before data collection starts.

**Study design.**

- *Stimuli.* 24 real rooms, each photographed by the authors. For each room there are two cover photographs: a faithful version ($L_0$: standard 28 mm-equivalent lens, natural light, no staging beyond basic housekeeping) and an exaggerated version ($L_2$: ultra-wide 16 mm-equivalent perspective, brightness and contrast enhancement, and generative AI inpainting [tool and version to be recorded] that removes clutter, power cords, wall scuffs, and worn textiles while keeping the structural layout and core furniture). Edits are limited to removal and surface enhancement. No amenities are added. Each room also has three unedited reveal photographs taken from different angles under standard lighting.
- *Manipulation check (before the main study).* [N = 45] independent raters on Prolific rate all 48 cover photographs, without seeing the ground truth, on perceived spaciousness, brightness, and cleanliness (seven-point scales). Each room's exaggerated version must score higher than its faithful version on all three attributes. Rooms that fail are re-edited and re-rated. The criterion for proceeding is that the mean difference is positive for every attribute and statistically significant (p < .05) across rooms. These raters take no part in the main study.
- *Trial structure.* Each participant evaluates six rooms drawn at random from the 24, three in $L_0$ and three in $L_2$. Assignment of rooms to conditions, and presentation order, are randomized per participant. No participant sees the same room in both conditions.
- *Block 1 (before the reveal).* For each listing, one cover photograph and identical standardized listing text (location tier, number of beds, basic amenities). Participants rate how clean, spacious, bright, and well maintained the place looks (seven-point scales), how much they trust the listing, and their maximum WTP per night (open numeric box, entered before any price anchor appears). They then see a fixed reference price (\$130 per night) and answer whether they would book at that price. Block 1 makes no mention of accuracy or honesty.
- *Block 2 (the reveal).* After all six Block 1 evaluations, participants see the same six listings again, in the same order, with the initial cover photograph displayed beside the three ground-truth photographs. For each listing they report expectation disconfirmation, the hypothetical star rating they would leave after staying, perceived host honesty, post-reveal WTP, and rebooking intention.

**Randomization.** Computer-generated, per participant, within the survey platform [platform and version]. The assignment seed is recorded.

# 3. Sampling Plan

**Existing data.** Registration is prior to creation of data. No Study 2 data exist. A pilot of about [10] participants is run first to check instructions, timing, and attention-check function. Pilot data are excluded from all analyses and are described in the paper.

**Data collection procedures.** Participants are recruited on Prolific. Inclusion criteria: age 18 or older, residence in the United States or United Kingdom, fluent in English, and having booked a short-term rental in the previous two years (screened by Prolific filters and a first-page question). Compensation: [amount to be set so that the hourly rate is at or above Prolific's recommended minimum for the expected duration; expected duration about [12] minutes, to be confirmed by the pilot].

**Sample size.** The target is 120 participants after exclusions, which gives 720 room-level evaluations (360 per condition). Recruitment continues until 120 valid participants are reached. We do not look at outcome data before the target is reached, and we do not stop or extend the sample on the basis of results.

**Sample size rationale.** We simulated the design (crossed participant and room random intercepts, each explaining 25 percent of the variance; participant-level paired comparison; two-sided $\alpha = .05$; 1,000 simulated experiments per cell). With 120 participants, power is about .64 for a standardized condition effect of $d = 0.15$, .89 for $d = 0.20$, and at least .99 for $d \ge 0.30$. With 90 participants, power for $d = 0.20$ is about .77. The code is in the project repository (study2/power.py) and will be archived with the registration. The variance assumptions are checked against the pilot, but the target sample is not changed after data collection starts.

**Exclusion rules (preregistered).**

1. Participants who fail the attention check (a quality-control item embedded in Block 1 with one unambiguous correct answer [item text to be written]) are excluded and replaced.
2. Participants who do not finish both blocks are excluded and replaced.
3. Participants whose total completion time is below [one third] of the pilot median are excluded and replaced.
4. Room evaluations with WTP outside [\$10, \$1,000] per night are treated as invalid for the WTP analyses (flagged before looking at condition effects). The primary analysis is run with and without these observations, and both results are reported.

No other exclusions are made. All exclusions and replacements are counted and reported.

# 4. Variables

**Manipulated variable.** *Exaggerated*: 1 = exaggerated photograph ($L_2$), 0 = faithful photograph ($L_0$), within participant and within room.

**Measured variables.**

| Block | Variable | Scale | Role |
|:--|:--|:--|:--|
| 1 | Perceived quality index | Mean of four seven-point ratings (clean, spacious, bright, well maintained) | Primary for H1(a); internal consistency (Cronbach's $\alpha$) is reported |
| 1 | Pre-reveal WTP | Open numeric, \$ per night | **Primary** for H1(a) |
| 1 | Initial listing trust | Seven-point | Secondary |
| 1 | Booking intention at \$130 | Binary | Secondary |
| 2 | Expectation disconfirmation | Seven-point: 1 = much worse than expected, 4 = exactly as expected, 7 = much better | **Primary** for H3(a) |
| 2 | Hypothetical star rating | 1 to 5 stars | **Primary** for H3(a) |
| 2 | Perceived host honesty | Seven-point agreement with "The host presented this place honestly in the first photograph" | **Primary** for H3(a) |
| 2 | Post-reveal WTP | Open numeric, \$ per night | Secondary |
| 2 | WTP revision, $\Delta WTP$ | Post-reveal WTP minus pre-reveal WTP | **Primary** for H2(a) |
| 2 | Rebooking intention | Seven-point | Secondary |
| Both | Trial position (1 to 6), room, participant | Covariates and grouping factors | Model terms |
| Both | Demographics (age, gender, country, short-term rental experience) | Collected at the end | Descriptive only |

**Indices.** The perceived quality index is the mean of the four ratings. No other composites are formed.

# 5. Analysis Plan

**Statistical models.** Observations are cross-classified by participant and room. For continuous outcomes, we fit linear mixed-effects models with crossed random intercepts for participants ($u_i$) and rooms ($v_r$):

$$Y_{ir} = \beta_0 + \beta_1\,\text{Exaggerated}_{ir} + \gamma\,\text{Order}_{ir} + u_i + v_r + \varepsilon_{ir}$$

For the binary booking choice, we fit the corresponding logistic mixed-effects model. The coefficient $\beta_1$ is the condition effect. Models are fit by restricted maximum likelihood [software and version, for example R lme4 / lmerTest, Satterthwaite degrees of freedom]. If a model does not converge, we first simplify the random-effects structure (drop the room intercept), and we report that change.

**Confirmatory tests and inference criteria.**

| Hypothesis | Outcome | Test | Direction predicted |
|:--|:--|:--|:--|
| H1(a) | Pre-reveal WTP | $\beta_1$ in the model above | $\beta_1 > 0$ |
| H1(a) | Perceived quality index | same | $\beta_1 > 0$ |
| H2(a) | $\Delta WTP$ | same | $\beta_1 < 0$ |
| H3(a) | Expectation disconfirmation | same | $\beta_1 < 0$ |
| H3(a) | Hypothetical star rating | same | $\beta_1 < 0$ |
| H3(a) | Perceived host honesty | same | $\beta_1 < 0$ |

Two-sided tests at $\alpha = .05$. The six confirmatory tests are one family, and we apply the Holm correction across them. We report adjusted and unadjusted p values and 95 percent confidence intervals. A hypothesis is counted as supported when the corresponding test or tests are significant in the predicted direction after correction (H3(a) requires all three outcomes to be in the predicted direction; we report which of the three are significant). Standardized effects (Cohen's *d*, computed from the model estimate and the total standard deviation) are reported for all confirmatory tests.

**H2(a) additional test.** We also fit a repeated-measures model of WTP with a condition-by-stage (pre versus post reveal) interaction and a random intercept for participants and rooms. The interaction is the same quantity as the $\Delta WTP$ effect and is reported as a consistency check.

**Secondary outcomes.** Trust, booking intention, post-reveal WTP, and rebooking intention are analyzed with the same model and are labeled exploratory. They are not included in the Holm family.

**Robustness checks (preregistered).**

1. Two-way clustered standard errors by participant and room.
2. Interaction of condition with trial order, $\text{Exaggerated} \times \text{Order}$, for each primary outcome.
3. *First-trial analysis.* Restricting to the first room each participant evaluates, a pure between-subject comparison. This reduces concern about learning across trials and demand characteristics, although it does not remove it. We report the estimate and interpret it as a check on direction and size, since the sample is only about one sixth of the full number of observations.
4. Results with and without the observations flagged by exclusion rule 4.
5. Results with the exaggerated condition's manipulation check (perceived spaciousness, brightness, and cleanliness from the independent raters) as a covariate at the room level.

**Mediation and mechanisms (exploratory).** We estimate whether the post-reveal effect on star rating and on post-reveal WTP operates through disconfirmation and perceived host honesty, with bootstrap confidence intervals (5,000 resamples, resampling participants). Three accounts could produce the post-reveal penalty: (i) inference about the host's type (a host who misrepresents may also misrepresent attributes a photograph cannot show), (ii) a fairness-based reaction to broken trust, and (iii) reference-dependent loss aversion. The design cannot separate them, and it has no condition in which a photograph undersells the room. We therefore describe the pattern as consistent or inconsistent with each account and do not claim to test them.

**Missing data.** Participants with incomplete data are excluded and replaced (Section 3). Within-participant item missingness is not expected, because all items are required. We do not impute.

**Transformations.** WTP is analyzed in dollars. As a sensitivity analysis, we repeat the WTP analyses on log WTP.

**Exploratory analyses.** Any analysis not listed above is exploratory and is labeled as such in the paper. We will report all preregistered analyses whatever their direction, and any deviation from this plan with the reason.

# 6. Other

**Data and code availability.** Anonymized data, stimuli identifiers, the survey instrument, and analysis code are shared in a public repository at the time of publication. The analysis code [study2/analysis.R or .py] will be uploaded to the registration before data collection starts and will be run unchanged on the final data. Raw photographs taken by the authors are shared if image rights allow.

**Deviations.** Any deviation from this registration is documented in the paper, with the reason and with the effect of the deviation on the results where it can be assessed.

**Other.** The paper also contains an observational field study (Study 1), which is not part of this registration. The paper presents Study 2 results only after this registration is public and data collection is complete.

**Potential extensions, not part of this registration.** (1) A third condition in which a photograph *undersells* the room, to test the asymmetry that reference-dependent loss aversion predicts. (2) A delayed, memory-based reveal in which the original photograph is not shown beside the true photographs, to test how much of the penalty survives without side-by-side comparison. (3) An information manipulation about attributes that photographs cannot show (for example noise), to test the host-type account. If run, each will be registered separately.
