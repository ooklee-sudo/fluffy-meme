# Results: independent third-coder adjudication (plan: ANALYSIS_PLAN_THIRD_CODER.md; code: analysis_third_coder.py; numbers: results_third_coder.json; labels: third_coder_labels.csv; returned sheet: third_coder_returned.xlsx)

All 60 items were coded (two entries written in lower case were normalized). Item texts in the returned sheet match the sent sheet.

## Agreement
- 45 items on which the two coders disagreed: the third coder agrees with coder A at κ = 0.13 and with coder B at κ = 0.23 (A and B themselves: κ = −0.38 on these items, as expected from the selection); with the investigator's adjudicated labels κ = 0.23 (agreement 44%).
- 15 control items (coders had agreed): third coder versus consensus κ = 0.45 (agreement 67%), above the plan's 0.40 floor, so the analysis is not treated as unreliable, but the third coder is a noisy rater.
- On the 45 items the investigator's adjudication gave ESC 27, MIXED 7, OTHER 6, DEESC 5; the third coder gave DEESC 14, ESC 14, MIXED 10, OTHER 7.

## New final labels ("v3 final": majority of coder A, coder B and third coder; if all three differ, MIXED if any said MIXED, otherwise OTHER; 11 of the 45 items had three different labels)
24 final labels change. Final class counts, investigator versus v3: ESC 41 → 28; DEESC 46 → 46; MIXED 25 → 34; OTHER 79 → 83. Of the 41 investigator escalation labels, 13 change (6 to MIXED, 6 to OTHER, 1 to DEESC); of the 28 v3 escalation labels, 14 come from the 45 adjudicated items and 14 are coder-consensus labels. De-escalation: 5 of 46 from adjudicated items, all unchanged.

## Market result (30-minute directional WTI return, headline events: three-hour filter, valid window)
| Label set | De-escalation | Escalation |
|---|---|---|
| Investigator final (earlier) | n 29; mean 1.05 (day-clustered 95% CI 0.44–1.96); median 0.47; two-sided p .0003 | n 16; 0.48 (0.17–0.80); median 0.40; p .013 |
| v3 final | n 32; 0.94 (0.39–1.76); median 0.46; p .0003 | n 10; 0.45 (0.03–0.89); median 0.36 (−0.01–1.02); p .084 |
| Third coder only (45 items) | n 35; 0.85 (0.33–1.60); median 0.46; p .0005 | n 10; 0.45 (0.03–0.87); median 0.36; p .084 |
| Coder consensus only | n 28; 1.03 (0.41–1.99); p .0006 | n 7; 0.71 (0.31–1.16); p .016 |
By the rule fixed in the plan (the day-clustered 95% CI of the escalation mean excludes zero), the escalation estimate under v3 final remains positive (+0.45%, CI 0.03 to 0.89), but only just: the Wilcoxon test is not significant (p = .084), the median's CI includes zero, and n = 10 on 10 days. The de-escalation result is unchanged.

## Models against v3 final (all 191 posts)
Model 1 κ = 0.48 (escalation precision 0.35, recall 0.79; de-escalation 0.63, 0.78); v2 majority κ = 0.49 (escalation 0.32, 0.89; de-escalation 0.73, 0.80). Against the investigator labels the same models gave κ 0.50 and 0.50 and escalation precision 0.49 and 0.45; investigator final versus v3 final κ = 0.82.
Difference between the v3-final class mean and the model-label class mean on the same events (day-clustered bootstrap, 10,000 resamples): escalation, versus model 1 +0.28 (CI −0.07 to 0.68, p = .11); versus v2 majority +0.13 (CI −0.26 to 0.54, p = .51). De-escalation: +0.04 and −0.01. No difference is detectable under the independent labels.

## Reading
The escalation class is the ambiguous one: coders A and B disagreed on 45 items, 27 of which the investigator resolved to escalation and only 14 of which the third coder labelled escalation. Under independent adjudication the escalation class shrinks from 41 to 28 posts and the escalation estimate from 16 to 10 events with a mean of +0.45%, not distinguishable from the investigator-labelled +0.48% in size but not significant by a rank test. The models' over-labelling of escalation is as large or larger against the new labels (precision 0.32 to 0.35), but the difference between human-label and model-label escalation estimates is not detectable. The claims that survive are the de-escalation response, the direction (not the significance) of the escalation response, and the model's over-labelling of escalation.
