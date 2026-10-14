# Results: robustness of the human-label headline (plan: ANALYSIS_PLAN_ROBUST_HEADLINE.md; code: analysis_robust_headline.py; numbers: results_robust_headline.json)

Baseline reproduced exactly: de-escalation n = 29, post-30 mean +1.05% (median 0.47), paired post − pre +0.48 (p = .030); escalation n = 16, +0.48% (median 0.40), paired +0.26 (p = .058).

| Variant | DEESC n | post mean (median) | p post > 0 | pre | paired post − pre | p post > pre | ESC n | post mean | p | paired | p |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Baseline (3 h filter, 30 min) | 29 | 1.05 (0.47) | .0002 | 0.57 | +0.48 | .030 | 16 | 0.48 | .0065 | +0.26 | .058 |
| No cluster filter | 34 | 0.91 (0.46) | .0002 | 0.49 | +0.44 | .026 | 19 | 0.46 | .0017 | +0.23 | .071 |
| 1 h filter | 30 | 1.01 (0.47) | .0002 | 0.56 | +0.45 | .038 | 19 | 0.46 | .0017 | +0.23 | .071 |
| 2 h filter | 29 | 1.05 (0.47) | .0002 | 0.57 | +0.48 | .030 | 18 | 0.49 | .0020 | +0.25 | .044 |
| 6 h filter | 25 | 1.08 (0.49) | .0002 | 0.66 | +0.42 | .063 | 14 | 0.54 | .0067 | +0.27 | .097 |
| Both coders agreed before adjudication | 28 | 1.03 (0.47) | .0003 | 0.59 | +0.44 | .045 | 7 | 0.71 | .0078 | +0.44 | .078 |
| Window 5 min | 29 | 0.67 (0.21) | .0006 | −0.05 | +0.72 | .003 | 16 | 0.46 | .0021 | +0.38 | .096 |
| Window 15 min | 29 | 0.76 (0.60) | .0006 | 0.00 | +0.76 | .005 | 16 | 0.57 | .0002 | +0.36 | .019 |
| Window 60 min | 28 | 1.18 (0.42) | .0033 | 0.83 | −0.15 | .365 | 16 | 0.48 | .033 | +0.44 | .086 |
| Drop 23 March and 7 April (3 events) | 26 | 0.80 (0.48) | .0001 | 0.30 | +0.49 | .025 | 16 | 0.48 | .0065 | +0.26 | .058 |

Staleness cutoff of 2, 5 and 10 minutes gives identical results (every used window has a tick within 2 minutes).

## What holds
- The direction of the post-window move is robust: it is positive and one-sided significant in every variant, for both classes, including when events on the two big days are dropped (de-escalation mean 0.80, median 0.48) and when only posts both coders labelled alike are used.
- The median (about 0.4–0.5% at 30 minutes) is stable across variants; the mean is pulled by a few large events. The three largest de-escalation events are 2.7%, 3.3% and 10.5% and make up 54% of the summed move; leave-one-event-out means range from 0.71 to 1.12. For escalation, the top three events make up 55% of the sum and leave-one-out means range from 0.39 to 0.56.
- Quote quality does not explain the result: the median bid–ask spread is 0.05 on a price near 89.6, while the median absolute 30-minute move is 0.46, about nine spreads.

## What does not hold up well
- The post-minus-pre excess at 30 minutes is borderline: de-escalation p = .026–.063 across cluster rules, .045 with consensus labels only; escalation p = .044–.097. It is not a stable result.
- It depends on the window. Over 5 and 15 minutes the pre-post comparison is clean for de-escalation (pre −0.05 and 0.00; paired +0.72 and +0.76; p = .003 and .005), so the move right after a post is not preceded by drift in the same minutes. Over 60 minutes the earlier drift has caught up (pre +0.83, paired −0.15, p = .37). This agrees with the matched-hour placebo result that the 30–60 minutes before a post also move in the same direction. The cleanest statement is therefore the short-window one, with a longer-window drift of unidentified cause.
- The consensus-only escalation sample has only 7 posts.

## Sample reconciliation (human labels)
191 war-period posts → 141 after the 3-hour filter → 68 posts with a signal label (37 de-escalation, 31 escalation) → 45 with a tick window at the post time and +30 minutes (29, 16) → 40 with also a valid −60-minute price (26, 14; the sample of the placebo analysis).
Of the 23 signal posts without a window, 83% were made on weekends or when the market was closed, against 29% of all signal posts. The retained sample therefore excludes weekend announcements; its results should not be generalized to them.
