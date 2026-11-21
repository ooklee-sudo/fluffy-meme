# Study 2: results section (draft)

> Draft for the authors. All numbers come from the single preregistered run of `webapp/analysis_study2.py` on the final data (commit 3f9c6c0). Wording follows the preregistered status of each test (confirmatory, planned, exploratory). Figures: `webapp/make_figures_study2.py`. Check every number against `analysis_report.txt` before submission.

## Sample

We opened the survey to 279 Prolific participants (preregistered cap: 300 recruited). All consented; 193 (69%) met the eligibility rules, 86 were screened out, and 188 eligible participants completed the survey (median completion time about 21 minutes). Applying the preregistered exclusion rules left 152 analysable participants (77 incident, 75 neutral). Rules removed participants as follows (a participant can meet more than one rule): failed an attention check, 10; answered at least two of four comprehension checks incorrectly, 11; differing job-function group or level between screening and the end, 17; finished in under one third of the median time, 3; identical willingness to pay (WTP) and choices in all four scenarios, 1; 36 participants in total. The sample is 48 participants short of the 200 planned (we analysed all that were available at the cap, as preregistered), so power was about .69 for d = 0.40 and .57 for d = 0.35 in the primary test. Twenty-four analysable participants reported that their organization prohibits sending such data to external AI services entirely (S8 = 1); they are retained in all analyses.

## Primary test (H2c)

The incident report was predicted to reduce sensitivity of WTP to the stated exposure probability. The within-person difference S (mean ln(WTP/L) at 6% minus at 2%) was 0.50 in the incident group and 0.75 in the neutral group (Welch t = −2.05, p = .042, d = −0.33, 95% CI [−0.65, −0.01]). The normative difference is ln 3 = 1.10, so both groups were less sensitive to the stated probability than the benchmark. The mixed model gave the same direction (incident × probability interaction = −0.24, SE = 0.10, p = .014), as did the model with covariates (−0.26, SE = 0.11, p = .022). Excluding respondents with S8 = 1 left the estimate similar but less precise (d = −0.31, 95% CI [−0.66, 0.04], p = .080; mixed model p = .031). We therefore treat H2c as supported in direction, with a confidence interval that approaches zero and a result that depends on the retained sample; it should be replicated with a larger sample.

## Secondary tests (Holm correction, family of two)

H2a: the incident group had a higher mean ln(WTP/L) (−3.02 vs. −3.31; t = 2.61, d = 0.42, 95% CI [0.10, 0.75]; Holm-adjusted p = .020), about 34% higher in geometric mean. With covariates the difference was 0.32 (SE = 0.11, p = .005); without S8 = 1 respondents it was similar (d = 0.44, adjusted p = .031). The neutral group's overall level (−3.31) was close to the normative level (−3.36), so the incident effect is an upward shift rather than a correction of an earlier bias.

H3a: showing accuracy plus cost per correct answer, rather than accuracy alone, did not detectably change the probability of choosing the local model (odds ratio = 1.21, 95% CI [0.81, 1.78], Holm-adjusted p = .348). Given the sample size this result is inconclusive for effects of moderate size; it is not evidence of no effect.

## Manipulation checks

Participants chose the local model far more often at a stated probability of 6% than at 2% (odds ratio = 10.8, p < .001), as the normative benchmark implies. The incident report did not raise participants' general estimate of the 12-month probability that a mid-sized company's data is exposed through an external AI vendor: it was 30.4% in the incident group and 36.6% in the neutral group (Welch t = −1.75, p = .082, d = −0.28), the opposite direction of the availability account. Both estimates are far above the stated scenario probabilities.

## Planned mediation (not interpreted confirmatorily)

The indirect effect of the incident report on mean ln(WTP/L) through the participant's excess probability estimate was −0.005 (95% bootstrap CI [−0.070, 0.012]); the within-person indirect effect of format on local choice through perceived quality disadvantage was −0.005 (95% CI [−0.018, 0.004]). Neither interval excludes zero.

## Exploratory analyses

The incident effects on S and on mean ln(WTP/L) did not vary detectably with organizational policy strictness (interaction on S = −0.10, SE = 0.20, p = .631; on mean ln(WTP/L) = −0.19, SE = 0.18, p = .317) or with personal discretion (S: 0.08, SE = 0.12, p = .525; mean ln(WTP/L): −0.06, SE = 0.11, p = .580). The incident did not detectably change how often security and privacy policy was ranked among the top three sourcing factors (91% vs. 85%, p = .292). Neither the incident × format interaction (p = .948) nor the format × numeracy interaction (p = .692) was detectable. Respondents whose organization prohibits external AI services entirely (n = 24) chose the local model in 47% of scenarios and had S = 0.67. None of these analyses was adjusted for multiple testing.

## Deviations from the preregistration (report in the paper)

1. Sample: 152 analysable participants instead of 200; 279 participants opened the survey (cap 300).
2. After the pilot (10 participants, not used in any test) the consistency-check exclusion rule was relaxed so that IT, data and security functions count as one group, and the stated duration was changed from about 19 to about 22 minutes.
3. A completion-code configuration error gave the earliest participants a wrong completion code; their submissions were approved manually. Responses were unaffected.
4. Implementation choices not fixed in the preregistration: mixed-effects logistic regression by maximum likelihood with Gauss-Hermite quadrature; covariates (numeracy, privacy concern, risk attitude, discretion); H3b as within-person mediation with participant-level bootstrap.

## Limitations to state

Hypothetical stakes and self-reported job roles; a single study; a sample below the planned size, with limited power for small effects and for the Holm family; the primary result crosses the .05 threshold only narrowly and weakens without S8 = 1 respondents; no support for the proposed mediating mechanism; scenario figures come from our own measurements of quantized models, not from the participants' organizations.
