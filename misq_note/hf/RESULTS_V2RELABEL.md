# Results: model re-labelling under codebook v2; label-set comparison; reporting fixes (plan: ANALYSIS_PLAN_V2RELABEL.md; code: analysis_v2relabel.py, analysis_v4_headline.py; numbers: results_v2relabel.json, results_v4_headline.json; labels: model_v2_labels_191.csv)

Four blind runs (opus, sonnet, haiku, sonnet repeat) labelled the 191 posts from the codebook v2 text and the post texts alone, in different random orders. Majority label ties (15 posts) were resolved by the opus run.

## Agreement with the final human labels (all 191 posts)
| Labels | κ (95% bootstrap CI) | AC1 | κ round 2 | κ round 3 | ESC predicted | ESC precision / recall | DEESC precision / recall |
|---|---|---|---|---|---|---|---|
| Model 1 (original prompt) | 0.50 (0.41–0.59) | 0.53 | 0.29 | 0.55 | 63 | 0.49 / 0.76 | 0.61 / 0.76 |
| v2 opus | 0.48 (0.39–0.57) | 0.50 | 0.37 | 0.49 | 78 | 0.45 / 0.85 | 0.68 / 0.78 |
| v2 sonnet | 0.51 (0.43–0.60) | 0.53 | 0.41 | 0.53 | 85 | 0.45 / 0.93 | 0.76 / 0.74 |
| v2 haiku | 0.50 (0.41–0.58) | 0.52 | 0.43 | 0.49 | 76 | 0.46 / 0.85 | 0.77 / 0.74 |
| v2 sonnet repeat | 0.49 (0.41–0.58) | 0.51 | 0.45 | 0.48 | 73 | 0.48 / 0.85 | 0.70 / 0.70 |
| v2 majority | 0.50 (0.41–0.59) | 0.52 | 0.37 | 0.52 | 77 | 0.45 / 0.85 | 0.71 / 0.78 |

Human–human κ is 0.67 (190 posts with two labels). The four runs agree with each other at κ 0.69–0.84.
Human labels contain 41 escalation posts; every model run predicts 73–85. The v2 codebook raised agreement in round 2 (0.29 → 0.37–0.45) and left it at 0.48–0.51 over all 191 posts. By the rule fixed in advance (κ ≥ 0.60 and escalation precision ≥ 0.70), the first-stage failure is not explained by the prompt: it persisted under the clearer codebook, with the same pattern (models over-label escalation, humans call many of those posts mixed or other).

## Event study on the same events (95 events with a valid window after the three-hour filter)
Mean directional 30-minute WTI return by class (n; mean; median; two-sided Wilcoxon p):
| Label set | De-escalation | Escalation |
|---|---|---|
| Human | 29; 1.05; 0.47; .0003 | 16; 0.48; 0.40; .013 |
| Model 1 | 34; 0.90; 0.46; .0008 | 24; 0.17; 0.11; .53 |
| v2 majority (opus) | 33; 0.95; 0.47; .0001 | 30; 0.32; 0.31; .047 |
| v2 sonnet | 28; 1.04; 0.46; .0002 | 38; 0.24; 0.25; .072 |
| v2 haiku | 28; 1.04; 0.54; .0002 | 29; 0.35; 0.35; .019 |
| v2 sonnet repeat | 28; 0.99; 0.48; .0002 | 31; 0.22; 0.25; .16 |

Difference, human minus model labels, in the class mean (day-clustered bootstrap, 4,000 resamples, 95% CI; two-sided p):
| Comparison | De-escalation | Escalation |
|---|---|---|
| Human − model 1 | +0.15 (−0.11, 0.46); .25 | +0.31 (0.02, 0.65); .038 |
| Human − v2 majority | +0.10 (−0.12, 0.34); .38 | +0.16 (−0.12, 0.47); .27 |
| Human − v2 sonnet | +0.01 (−0.23, 0.20); .92 | +0.25 (0.00, 0.54); .046 |
| Human − v2 haiku | +0.01 (−0.24, 0.22); .95 | +0.13 (−0.14, 0.42); .36 |
| Human − v2 sonnet repeat | +0.06 (−0.20, 0.30); .60 | +0.26 (−0.05, 0.61); .099 |

**Reading.** (i) The de-escalation response is the same under every label set (0.90–1.05%). (ii) The escalation response is attenuated under every model label set (0.17–0.35 against 0.48), because model labels add many posts that humans do not call escalation. Under the original model labels the escalation estimate is indistinguishable from zero (p = .53) and differs from the human estimate (p = .038); under the v2 labels it is small and borderline (p = .02–.16) and its difference from the human estimate is mostly not detectable. The first-stage statement "escalation posts show no response" therefore holds only for the original model labels; "escalation posts are followed by a smaller and less certain response than de-escalation posts" is what all label sets support. (iii) The strong word "reversal" is not supported by the formal comparison.

## Adjudication sensitivity (human labels; headline sample; two-sided p; day-clustered bootstrap CI of the mean)
| Subset | De-escalation | Escalation |
|---|---|---|
| All final labels | n 29; mean 1.05 (0.44, 1.96); median 0.47 (0.21, 1.10); p = .0003 | n 16; 0.48 (0.17, 0.80); median 0.40 (0.02, 1.02); p = .013 |
| Coder consensus only | n 28; 1.03 (0.40, 1.93); p = .0006 | n 7; 0.71 (0.30, 1.17); p = .016 |
| Adjudicated only | n 1 | n 9; 0.30 (−0.11, 0.71); median 0.35 (−0.22, 1.14); p = .30 |
Of the 41 final escalation labels, 27 (66%) were adjudicated, against 5 of 46 (11%) for de-escalation. The 9 adjudicated escalation events with a window are not separately distinguishable from zero.

## Same-sample placebo (headline events; post-30 only; 10,000 draws)
De-escalation: observed +1.04 (28 of 29 events with a placebo pool) against placebo mean +0.04, 95th percentile 0.20, 99th 0.28; share of draws ≥ observed 0 of 10,000. Escalation (16 of 16): observed +0.48 against placebo mean +0.02, 95th percentile 0.20, 99th 0.28; 0 of 10,000. The result no longer depends on a different event set for the placebo.

## Headline with two-sided tests and day-clustered CIs
De-escalation: mean 1.05 (day-clustered 95% CI 0.44–1.96), median 0.47 (0.21–1.10), two-sided Wilcoxon p = .0003, 29 events on 25 days. Escalation: 0.48 (0.17–0.80), median 0.40 (0.02–1.02), p = .013, 16 events on 16 days.

## Event-time figure
figs/fig_human_path.png. The mean directional path before de-escalation posts rises by about 0.5 points between 20 and 15 minutes before the post and is flat in the last 15 minutes; the median does not show that jump. A gap of this kind in the mean, within a five-minute step, is what a few events moving at once would produce.
