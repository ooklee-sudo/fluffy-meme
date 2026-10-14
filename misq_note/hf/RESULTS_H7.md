# H7: war-period tick-level test on a human-labelled sample (plan: ANALYSIS_PLAN_HUMAN.md, Amendment 2; code: analysis_h7.py, analysis_human191.py; output: results_h7.json, results_human191.json, human_labels_191.csv)

All 191 keyword-selected war-period posts carry final human labels (consensus of two coders, else adjudicated by the principal investigator from text only; 23.6% adjudicated): OTHER 79, DEESC 46, ESC 41, MIXED 25. Model 1 against these labels: κ = 0.50 on all 191 (0.55 on the 130 posts of round 3). Among the 71 round-3 posts the model called OTHER or MIXED, 14 (20%) are human ESC or DEESC.

## Sample construction (R3b)
Cluster filter on the human-labelled series (a post is kept if at least three hours have passed since the previous post of any coded class): 141 of 191 posts kept; signal posts after the filter: 37 human-DEESC and 31 human-ESC. Tick-window coverage requires an open market at the post time, 30 minutes before and 30 minutes after: 29 DEESC and 16 ESC have it. The 23 excluded posts (8 DEESC, 15 ESC) are almost all weekend posts (19 of 23 on Saturday or Sunday; the others on Wednesday and Friday). Escalation posts are more often made when the market is closed, so the escalation estimates below describe open-market posts only.

## Results (directional return in %; tick data; Wilcoxon tests one-sided)
| Label source | Class | n | mean 5 min | mean 30 min | median 30 min | post30 > 0 (p) | week-block 95% CI (30 min) | mean pre-30 | post − pre (30 min) | post > pre (p) |
|---|---|---|---|---|---|---|---|---|---|---|
| Human | DEESC (H7a, H7b) | 29 | +0.67 | +1.05 | +0.47 | 0.00017 | 0.42 to 1.79 | +0.57 | +0.48 | **0.030** |
| Human | ESC (H7c) | 16 | +0.46 | +0.48 | +0.40 | 0.0065 | 0.10 to 0.84 | +0.22 | +0.26 | 0.058 |
| Model 1 | DEESC | 34 | +0.68 | +0.90 | +0.46 | 0.0004 | 0.37 to 1.59 | +0.39 | +0.51 | 0.018 |
| Model 1 | ESC | 24 | +0.34 | +0.17 | +0.11 | 0.26 | −0.18 to 0.53 | −0.09 | +0.26 | 0.24 |

**Decision under the pre-registered rule.** The human-labelled sample has 29 de-escalation posts with a tick window (≥ 20 required), so it may serve as the primary sample. H7a is supported (p = 0.0002). H7b is supported (p = 0.030): the 30 minutes after the post exceed the 30 minutes before it by +0.48 points, so the earlier failure of H6c (n = 25, p = 0.082) is not repeated on the larger human-labelled sample; the evidence for the post-versus-drift claim is marginal (p = 0.03; 0.082 on the narrower 25-post sample). H7c: human-labelled escalation posts are followed by +0.48% in 30 minutes (p = 0.0065), whereas the model's escalation label shows +0.17% (p = 0.26): the earlier "no response to escalation" was an artefact of the model's escalation label, which is right for 36% of posts in human judgment.
Exploratory (not pre-registered): the difference between de-escalation and escalation response in the human-labelled sample is not distinguishable from zero (Mann-Whitney p = 0.20; 1.05% vs 0.48%).

## Limits
Twenty-three posts (mostly weekend) have no tick window and are not analysed; the sample is keyword-selected; coders are two people plus adjudication by the principal investigator; two or three events dominate the means (medians are 0.4–0.5%); the tick source is a CFD; simultaneous news is not excluded; and nothing here establishes that the post, rather than a contemporaneous event, caused the move.
