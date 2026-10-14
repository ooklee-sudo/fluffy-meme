# Revision analyses prompted by simulated peer review (plan: ANALYSIS_PLAN_REVISION.md; code: analysis_revision.py; output: results_revision.json)

Sample with complete 300-bar history and bar windows: 33 de-escalation (DEESC) and **27** escalation (ESC) war-period posts (the earlier n = 28 for ESC drops one post that lacks the prior-300-bar window). Directional units are percent.

## R1 Timing decomposition — the primary revised statistic is NOT supported
| Bar (DEESC, n = 33) | mean | median | one-sided Wilcoxon p |
|---|---|---|---|
| k−1 (hour before the post bar; placebo) | +0.36 | +0.11 | 0.10 |
| k (post bar) | +0.96 | +0.36 | 0.007 |
| **k+1 (first full hour after; pre-registered primary)** | **+0.34** | +0.06 | **0.18** |
| k+2 | −0.06 | −0.13 | 0.74 |
Paired b(k+1) − b(k−1) = −0.02 (p = 0.43); b(k) − b(k−1) = +0.60 (p = 0.14).
Under the decision rule fixed in advance, the revised primary is not supported (p = 0.18) and a pre-post drift of the same sign and size as the post-post hour exists, so **the post-hour contribution cannot be separated from drift** with hourly bars. Most of the two-hour effect is in the bar that contains the post, which includes the part of the bar before the post. Escalation: b(k−1) +0.21, b(k) −0.05, b(k+1) +0.02, b(k+2) +0.18 (all n.s.).

## R2 Robust inference (two-hour directional reaction, DEESC)
Mean 1.29; median 0.31; 10%/20% trimmed means 0.81/0.73; sign test 24/33 positive, one-sided p = 0.007; Wilcoxon p = 0.005; week-block bootstrap 95% CI for the mean 0.43 to 2.27 (16 weeks); leave-one-week-out range of the mean 0.96 to 1.44. ESC: mean −0.03, median +0.14, week-block CI −0.58 to 0.35 (14 weeks).
The effect is not an artefact of two events in the sense of rank-based tests, but its size is about a quarter to a half of the mean for typical events (median 0.31, trimmed 0.73–0.81).

## R3 Volatility units
Mean standardized reaction z (two-hour reaction divided by the sd of two-hour changes over the previous 300 bars): war-period DEESC 0.93 (n = 33); pre-war low-regime DEESC from the unified design 0.07 (n = 25); difference 0.87, one-sided permutation p = 0.013. The state difference remains in volatility units when the pre-war cell is the pooled low-regime sample. (Reviewer 2 reports about 1.04 sd for the Iran-only pre-war cell with n = 8; that cell is small and is not re-estimated here.)

## R4 Timing placebo, matched hour and weekday status
Placebo bars from the same ET clock hour within ±3 days (excluding ±2 h of coded posts) give a mean directional (DEESC-like) reaction of −0.16 (sd 0.14); observed 1.29; share of 10,000 draws ≥ observed = 0.000. Caveat: the candidate pools are small (mean 3.1 bars per event, 32 of 33 events have a pool), so the placebo distribution is narrow and this test is weak evidence of anything beyond "not a typical same-hour bar".

## R5 Asymmetry and horizons
DEESC minus ESC two-hour directional difference: 1.31, permutation one-sided p = 0.011, Mann-Whitney p = 0.051. Minimum detectable effect for the ESC cell is 0.75, larger than the de-escalation median effect, so the data cannot rule out a modest escalation effect. Cumulative directional returns from the open of bar k (DEESC): +0.96 (1 h), +1.29 (2 h), +1.11 (4 h), +0.99 (6 h), +0.45 (12 h, CI −0.89 to 1.92); (ESC): −0.05, −0.03, +0.71 (4 h), +1.04 (6 h, CI −0.00 to 1.84), +1.36 (12 h, CI −0.01 to 2.57). Escalation posts show a slow upward drift at 4–12 hours that is borderline at the week-block level.

## R6 Cluster-filter sensitivity (DEESC, mean directional two-hour reaction)
No filter: 42 posts with bars, mean 1.15, median 0.33. Three-hour (main): 34, mean 1.28, median 0.37. Six-hour: 28, mean 1.52, median 0.65. Results are not sensitive to the filter; the keyword-selection recall is not assessed.

## R7 Is posting predicted by past prices?
Hourly logit over 3,605 war-period bars. DEESC (36 events): signed prior six-hour return −0.045 (p = 0.32); absolute prior six-hour return +0.115 (p = 0.033); regular-hours indicator +0.58 (p = 0.09); AUC 0.56. ESC (28 events): signed prior return +0.077 (p = 0.18); absolute prior return +0.144 (p = 0.024); regular hours +0.97 (p = 0.012); AUC 0.71. Posts are more likely after volatile hours (both classes) and, for escalation, in regular hours; the direction of the prior move does not predict posting. This is evidence that posting times are endogenous to market conditions.

## R8 Arrivals by coded class (war period, 226 days)
DEESC: 57 posts, mean 0.25, variance 0.41, dispersion index 367 (p < 1e-8), negative-binomial size 0.36 (LR p = 1.5e-6). ESC: 60 posts, mean 0.27, variance 0.51, dispersion index 430 (p < 1e-14), size 0.32 (LR p = 2e-8). Overdispersion holds within each coded class, so the arrival result is not an artefact of the keyword class. The week-fixed-effects dispersion was not recomputed for the coded classes (script error in the Pearson calculation); the earlier value 0.89 for the keyword class is the only such estimate.

## Net effect on the paper's claims
1. The headline two-hour result is robust to rank-based and week-block inference, filter choice, and volatility standardization, but it is not separable from a pre-post drift at hourly resolution; the bar after the post alone does not show it (p = 0.18).
2. Posting follows volatile hours, which is consistent with the endogeneity concern; causal wording must go.
3. The asymmetry (DEESC vs ESC) is supported in permutation (p = 0.011) but marginal in rank (p = 0.051), and the escalation cell has low power.
4. State dependence survives standardization against a pooled pre-war sample (p = 0.013).
