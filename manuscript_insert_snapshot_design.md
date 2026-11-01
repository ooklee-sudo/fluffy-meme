# Text to add to the manuscript (snapshot design for RQ3)

All numbers come from `wildchat_rq3/results.txt` and `placebo_results.txt` (original detector patterns, `wildchat_rq3/detectors.py`).

---

## 4.3 Analysis (add one paragraph at the end)

**Snapshot contrast for RQ3.** The weekly drift tests rest on one trending series, so drift and calendar time cannot be separated (correlation 0.93 for the raw measure). WildChat, however, served models with different training cutoffs in the same weeks. We use the weeks in which both a GPT-3.5 and a GPT-4 snapshot were served (38 weeks; 100,362 multi-turn conversations after template de-duplication). We assume the cutoffs reported by the provider: September 2021 for all GPT-3.5 snapshots and for gpt-4-0314, April 2023 for gpt-4-1106-preview, and December 2023 for gpt-4-0125-preview. In the first period (April to June 2023) both families have the same cutoff, so it serves as the baseline. We estimate linear probability models of any correction on indicators for the three GPT-4 snapshots, with week fixed effects, controls for code content, first-prompt length and number of turns, and standard errors clustered by week. The contrast of interest is the difference between each later GPT-4 snapshot and gpt-4-0314, relative to GPT-3.5 in the same week, which is a difference-in-differences in which H3 predicts a negative sign (a fresher cutoff should mean fewer corrections). As a placebo we compare GPT-3.5 snapshots, which share one cutoff, with each other.

## 5.3 Results (add after "What the design could detect")

**Snapshot contrast.** Within the same week, gpt-4-1106-preview (cutoff 19 months later than that of GPT-3.5) had a higher v1 correction rate relative to GPT-3.5 than gpt-4-0314 did (difference-in-differences +1.31 percentage points, SE 0.30, p < 0.001), and gpt-4-0125-preview (27 months later) gave +0.65 points (SE 0.39, p = 0.095). The estimated change per month of cutoff advantage is +0.043 points (95% CI 0.016 to 0.070). With the v2 detector the corresponding differences are +1.24 points (SE 0.56, p = 0.028) and +0.54 points (SE 0.80, p = 0.50), and +0.039 points per month (95% CI −0.010 to 0.089). The sign is opposite to H3 for both detectors, so these results do not support H3.

**Placebo.** The comparison is not clean evidence of the opposite effect. GPT-3.5 snapshots share a cutoff, yet their correction rates differ: for v1, gpt-3.5-turbo-0613 and -0125 differ from -0301 by −0.36 points (p = 0.088) and −0.20 points (p = 0.48); for v2 by −0.77 points (p = 0.021) and −1.00 points (p = 0.063). For v2, the snapshot contrast is therefore of the same size as the change between snapshots with no change of cutoff. The two GPT-3.5 comparisons are also confounded with calendar time, because the snapshots were only served together in two weeks.

**Interpretation.** The contrast removes the calendar-time problem but not the model-generation problem: gpt-4-0314, gpt-4-1106-preview and gpt-4-0125-preview differ in capability and response style as well as in cutoff, and gpt-4-0314 had an unusually low correction rate (2.5% against 3.6% for gpt-4-1106-preview). With only three GPT-4 snapshots and three periods, we cannot separate a cutoff effect from a generation effect. We conclude that the snapshot design finds no sign of the drift effect that H3 predicts, and that it cannot rule out small effects of either sign.

---

## 6 Discussion (replace the sentence "the first requirement ... calendar time" or add after it)

Snapshot variation in WildChat meets the first requirement only in part. It breaks the collinearity between drift and calendar time, but at the price of confounding drift with model generation. A study that could hold the model fixed and vary only the training cutoff (for example, fine-tuned variants of one base model) would avoid this.

## 7 Threats to Validity (add)

**Snapshot design.** The cutoff dates are those stated by the provider and we have not verified them. Only three GPT-4 snapshots and one baseline period contribute to the contrast, so the per-month estimate relies on three points. The placebo shows that differences of about one percentage point arise between snapshots of the same cutoff.

---

## Corrections needed in the existing text

1. **Models used for RQ3 (Section 4.2 and 5.3).** The manuscript names "the gpt-3.5-turbo variants, gpt-4-0314, and gpt-4-0613 (381,201 conversations)". WildChat-1M contains no gpt-4-0613. The 381,201 conversations are the three GPT-3.5 snapshots (347,813) plus gpt-4-0314 (33,388). Replace "gpt-4-0613" by "gpt-4-0314" and recheck "the gpt-4 models" and "eight weeks" (gpt-4-0314 is served in 12 weeks; gpt-4-0125-preview in 8).
2. **Abstract and contributions.** Do not add the snapshot result to the abstract unless the placebo caveat is kept. A suitable sentence: "A same-week contrast of model snapshots with different training cutoffs also finds no support for the prediction, although it cannot separate cutoff from model generation."
3. **Data availability.** Replace "available upon request" by the repository DOI.

---

## 3.3 Testable implications (add at the end: why we do not estimate the refresh cost)

**Why we do not estimate the refresh cost.** The model has a structural parameter, the cost of a refresh (RC), and one could ask why we do not estimate it from the repository data. We do not, for three reasons. First, RC is identified only through the response of refresh timing to the state of the system. That response has two parts: errors must rise with the time since the last refresh (H1, γ > 0), and refreshes must become more likely as that time grows (H2). Neither holds in our data (RQ1: pooled slope −0.0005, 95% CI −0.010 to 0.009; RQ2: pooled slope −0.125, 95% CI −0.228 to −0.022, of the wrong sign). If γ is zero, no cost of refreshing can rationalize the observed timing, and a number returned by the estimator would reflect the functional form and not the maintainers' behavior. Second, even in the idealized benchmark of Section 3.4 the estimator is imprecise for panels of the length we have: the standard deviation of the estimated RC is 4.8 at 250 weekly observations and 6.7 at 100, against a true value of 40, and our repositories have between 145 and 414 weeks. Third, a release is only a proxy for a refresh in these repositories (Section 4.1), so an estimate would be a cost of releasing and not of retraining. We therefore use the model to derive H1 to H3 and to size the tests, and we provide the estimation code (`estimate_real.py`) in the replication package for readers who wish to apply it to data in which refresh dates are known.
