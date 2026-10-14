# Pre-registration of revision analyses prompted by simulated peer review (committed before estimation, 2026-10-14)

Source: reviews/review1_theory.md, review2_methods.md, review3_qual_llm.md. Already seen by the authors: the headline results (RESULTS.md), the pre-trend control, and reviewer 2's own recomputations quoted in the review (sign test 24/33 negative; Wilcoxon p ≈ 0.010; bar decomposition k−1 = −0.36%, k = −0.96%, k+1 = −0.34%; hour-matched standardized mean ≈ −1.33 sd; unconditional two-hour sd 0.60% before and 1.22% during the war). Anything derived from those is exploratory confirmation of the reviewer's computation, not a new test; what is new is marked N.

Sample: the 61 war-period posts (33 DEESC, 28 ESC) from `post_reactions_oil_coded.csv` with hourly bars `raw2y/CL_1h.csv`. k = bar containing the post. Directional reaction e = sgn × return (%), ESC +1, DEESC −1.

## R1 Timing decomposition (N for the primary)
Bar returns: b(k−1), b(k), b(k+1), b(k+2), each 100·ln(close/open) × sgn. **Primary revised statistic: mean of b(k+1) for DEESC (the first full hour after the post bar).** Test: one-sided Wilcoxon signed-rank, α = .05. Secondary: paired difference b(k+1) − b(k−1); b(k) − b(k−1); the same for ESC. Interpretation rule fixed now: if mean b(k−1) has the same sign as b(k+1) and the paired difference b(k+1) − b(k−1) is not significantly positive (one-sided p ≥ .05), the paper must say that a pre-post drift of comparable size exists and that the post-hour contribution cannot be separated.

## R2 Robust inference
For each directional cell (DEESC, ESC) report mean, median, 10% and 20% trimmed means, sign test, Wilcoxon, and a **week-block bootstrap** (resample ISO weeks, 20,000 draws, seed 20261014) 95% CI for the mean. Leave-one-week-out range of the mean.

## R3 Standardization and state-dependence in volatility units
z = e / sd of the two-hour changes (ln close[j+1]/open[j]) of the prior 300 bars. Report mean z for war DEESC and ESC. N: H1 contrast in z units: war-period DEESC (this sample) versus pre-war low-regime DEESC from `paper_signal_posts.csv` (topic O, regime low, agreed labels) computed the same way. One-sided permutation on the difference in mean z.

## R4 Timing placebo with matched hours (N)
For the 33 DEESC events, draw for each a placebo bar from the war period with the same ET clock hour and weekday/weekend status, within ±3 days of the event, excluding bars within ±2 h of any coded post; compute the mean directional two-hour reaction with sgn = −1 (DEESC-like). 10,000 draws. Report the share of draws ≥ the observed mean.

## R5 Asymmetry and horizons
Test DEESC − ESC directional mean difference (two-hour): permutation (20,000) and Mann-Whitney. Report cumulative directional returns from the open of bar k at 1, 2, 4, 6, 12 bars for both classes, with the week-block bootstrap CI. State minimum detectable effects for ESC (two-hour) = 2.8 × sd/√28.

## R6 Filter sensitivity (N)
Re-apply the cluster filter to the 191 coded keyword posts (`posts_coded.json` with times from the archive) with gaps of 0, 3 and 6 hours (previous post of any class), war period; report the number of DEESC/ESC posts kept and the two-hour directional mean for DEESC at each gap.

## R7 Is posting predicted by past prices? (N)
Hourly logit over war-period bars: y = 1 if a coded DEESC (separately ESC) post falls in the bar; regressors: prior 6-hour return (signed %, not directional), absolute prior 6-hour return, regular-hours indicator. Report coefficients, robust SEs, and the AUC. Purpose: evidence on whether posting follows prices.

## R8 Arrivals by coded class (N)
Dispersion index and negative-binomial vs Poisson LR for daily counts of coded DEESC and ESC posts (war period), plus the week-fixed-effects Pearson dispersion.

## Decision rules
R1 primary: "supported" only if the one-sided Wilcoxon p < .05 for b(k+1). Everything else is descriptive or sensitivity. All results go to RESULTS_REVISION.md as computed. Code: `analysis_revision.py`; output `results_revision.json`.

## Amendments
(none)
