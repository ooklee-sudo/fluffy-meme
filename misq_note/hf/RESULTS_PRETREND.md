# Pre-trend (momentum) control — results (plan: ANALYSIS_PLAN_PRETREND.md; code: analysis_pretrend.py; output: results_pretrend.json)

Sample: war-period posts with complete hourly bars — 33 de-escalation, 28 escalation. Momentum null: 3,244 war-period hourly bars without a coded signal post within ±2 h.

**Momentum in ordinary hours is negligible.** Forward two-hour WTI change regressed on the prior six-hour change: slope −0.027 (SE 0.019, p = 0.16); the 2-hour and 12-hour versions are similar (−0.050, p = 0.11; −0.018, p = 0.30). If anything there is slight mean reversion, not momentum.

**H1 (primary): supported.** De-escalation posts, abnormal directional reaction relative to the momentum null: +1.32% (95% bootstrap CI 0.44 to 2.37; one-sided p = 0.0005), against a raw directional mean of +1.29%. The control changes the estimate by 0.03 pp.

| | n | raw directional mean (%) | abnormal directional mean (%) | 95% CI | one-sided p |
|---|---|---|---|---|---|
| De-escalation, 6 h prior window (primary) | 33 | 1.29 | 1.32 | 0.44, 2.37 | 0.0005 |
| De-escalation, 2 h window | 33 | 1.29 | 1.32 | 0.44, 2.40 | 0.0004 |
| De-escalation, 12 h window | 33 | 1.29 | 1.32 | 0.45, 2.38 | 0.0004 |
| De-escalation excluding 23 Mar and 7 Apr | 31 | 0.67 | 0.69 | 0.18, 1.22 | 0.004 |
| Escalation, 6 h window | 28 | −0.02 | +0.01 | −0.51, 0.48 | 0.48 |

**Secondary S2 (post-level OLS, HC1).** De-escalation: intercept (effect at zero prior move) +1.22 (SE 0.46, p = 0.008); slope on the signed prior move +0.12 (SE 0.20, p = 0.55). Escalation: intercept −0.002 (SE 0.32), slope −0.01 (SE 0.09).

**Reading.** The war-period de-escalation response does not depend on pre-post momentum: the same size and the same significance after conditioning on the prior six-hour oil move, and still significant (about half the size, +0.69%) without the two extreme days. The pre-move seen in Figure 2 is not systematically related to the post-move (slope p = 0.55) and ordinary hours show no momentum to explain it. What this does not rule out: the post and the price move may both respond to the same news arriving at the same time (all 20 triangulated cases show other reported drivers). The control addresses momentum, not simultaneous news. Escalation posts remain null in the two-hour window.
