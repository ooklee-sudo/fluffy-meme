# Pre-registration: does the war-period oil response survive a pre-trend (momentum) control? (committed before estimation, 2026-10-14)

Motivation: Figure 2 of PAPER_DRAFT shows that WTI moved in the direction of the post during the five to six hours before the post (escalation: +1.38%, t = 1.57; de-escalation: −0.55%, t = −0.95), so part of the post-window move may be momentum or the same news. What is already seen: the raw two-hour reactions (RESULTS.md) and the pre-move means above; nothing else about this test.

## Data
`post_reactions_oil_coded.csv` rows with cls in {ESC, DEESC} and non-missing `oil` (n = 33 DEESC, 28 ESC at the stage of the headline result; the event-window figure uses the 60 with complete ±window bars). Hourly WTI bars `raw2y/CL_1h.csv`, war period (from 2 March 2026). Directional sign: ESC +1, DEESC −1 (oil expected up after escalation, down after de-escalation).

## Definitions
- Post reaction r_i = the existing two-hour reaction (`oil`, percent). Directional reaction e_i = sgn_i · r_i.
- Prior move p_i = ln(open of bar k / close of bar k−6) × 100 (six hours before the bar k containing the post). Sensitivity: 2 and 12 hours.
- Momentum null: all war-period bars j with no coded signal post within ±2 h. For each, forward_j = 100·ln(close[j+1]/open[j]), prior_j as above. Fit forward_j = c + d·prior_j by OLS (HC1) on those bars.
- Abnormal reaction: a_i = r_i − (ĉ + d̂·p_i); directional abnormal reaction e_i^abn = sgn_i · a_i.

## Primary hypothesis (single)
H1: mean e^abn for de-escalation posts > 0. Test: one-sided bootstrap (20,000 resamples of the 33 posts; the null-bar coefficients are held fixed; seed 20261014), α = .05. Report the mean, 95% CI, and the raw directional mean for comparison.
Decision: supported if the one-sided p < .05; "not robust to the pre-trend control" otherwise. A result between 25% and 75% of the raw mean with p ≥ .05 is reported as "attenuated and not significant".

## Secondary (reported, not decision-bearing)
S1. Same for escalation posts (n = 28).
S2. Post-level OLS with HC1 SEs: e_i = α + β·p_i^dir + ε for each direction, where p_i^dir = sgn_i · p_i (positive = oil had already moved in the post's direction); report α.
S3. H1 with prior windows of 2 h and 12 h.
S4. H1 excluding the two extreme de-escalation posts (23 March 11:23Z; 7 April 22:32Z).
S5. The momentum slope d̂ with CI (is there momentum in null bars at all?).

## Reporting
Results will be written to RESULTS_PRETREND.md exactly under the decision rule above, whatever the outcome. Code: `analysis_pretrend.py`; output `results_pretrend.json`.

## Amendments
(none)
