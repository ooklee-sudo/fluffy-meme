# Results: matched-hour placebo (H5c) and anticipatory drift (H8) (plan: ANALYSIS_PLAN_H5C_H8.md; code: analysis_h5c_h8.py; numbers: results_h5c_h8.json)

Placebo tick data completed (728 additional WTI hours downloaded, no failures; 11.0 million ticks in total). Sample: human-labelled war-period posts after the 3-hour cluster filter with a valid market window: 26 de-escalation (DEESC) and 14 escalation (ESC) events; secondary: the 61 model-selected posts with model-1 labels (29 and 21 events). Placebo times: same UTC clock hour on days ±3 with the same weekday/weekend status, ≥2 hours from any labelled post, market open; 10,000 draws; about 120 candidates per event.

Statistics are mean directional returns in percent (each event's own sign applied to the placebo time).

| Sample / class | Statistic | Observed | Placebo mean (95th pct) | Share of draws ≥ observed |
|---|---|---|---|---|
| Human, DEESC (n = 26) | H5c post-30 min | +0.62 | +0.05 (0.22) | < .0001 |
| | H8a pre-60 [−60,−5] | +0.86 | +0.14 (0.35) | < .0001 |
| | H8a pre-30 | +0.57 | +0.09 (0.29) | < .0001 |
| | H8b ticks in pre-30 | 3,463 | 2,708 (ratio 1.28) | < .0001 |
| Human, ESC (n = 14) | H5c post-30 min | +0.53 | +0.05 (0.26) | .0003 |
| | H8a pre-60 | +0.06 | −0.02 (0.25) | .31 |
| | H8a pre-30 | +0.29 | −0.01 (0.21) | .016 |
| | H8b ticks in pre-30 | 3,481 | 3,182 (ratio 1.09) | .058 |
| Model labels (61), DEESC (n = 28) | post-30 / pre-60 / pre-30 / ticks | +0.51 / +0.85 / +0.50 / ratio 1.20 | placebo ≈ 0 | all < .0001 |
| Model labels (61), ESC (n = 21) | post-30 / pre-60 / pre-30 / ticks | +0.24 / −0.09 / −0.05 / ratio 1.09 | placebo ≈ 0 | .003 / .58 / .54 / .056 |

**H5c (post-window placebo): supported for both classes.** The 30 minutes after a labelled post show a directional move well beyond what fake times in comparable hours produce (+0.62 against a placebo 95th percentile of 0.22 for de-escalation; +0.53 against 0.26 for escalation). The same holds with model labels, with smaller sizes.

**H8a (anticipatory drift): supported for de-escalation, partly for escalation.** The directional drift before the post is also well above the placebo: +0.86 in [−60,−5] and +0.57 in the 30 minutes before for de-escalation posts. For escalation, the 30 minutes before is above the placebo 95th percentile (+0.29 against 0.21; p = .016) but the longer pre-60 window is not (p = .31), and on model labels neither is. By the rule fixed in advance this is "drift larger than in comparable hours; cause not identified". It is not evidence of leakage or of any party's conduct. Possible readings that the data do not separate: the post follows news already moving the market; the market anticipates a pattern; or the same event moves both.

**H8b (quote activity).** Ticks in the 30 minutes before the post are 28% above placebo hours for de-escalation posts and 9% above for escalation (p = .058; borderline). The CFD feed's tick count is only a rough proxy for activity.

**H8c (descriptive, 30 events overlapping the first-source classification).** Mean directional pre-30 return: POST_FIRST +0.28 (n = 10), OTHER_FIRST +0.66 (9), SIMULTANEOUS +1.57 (6), UNDETERMINABLE +0.30 (5). POST_FIRST versus OTHER_FIRST: two-sided p = .90. No difference by who reported first.

## What this means for the paper
1. The war-period co-movement (de-escalation +1.05% in the earlier tick analysis) is not an artefact of choosing clock hours: it exceeds matched fake times.
2. The pre-post drift is of a similar size to the post-post move for de-escalation (+0.57 against +0.62). The earlier statement that the post window exceeds the pre window (paired +0.48, p = .030, 29 events) still holds as a comparison of the two windows, but both windows exceed the placebo, so the post cannot be read as the sole origin of the move.
3. For the cross-domain comparison with LLM releases: the Truth Social side now has a placebo-matched directional effect, whereas the release side has a magnitude effect without direction. They are not the same statistic and should not be called the same finding.

## Caveats
- Sample sizes are small (26 and 14); the human sample is the adjudicated one (κ reported elsewhere) and the event-filtering rule (3 hours since the previous labelled post) removes clustered posts.
- Placebo times are limited to ±3 days and to the war period, so they inherit its volatility regime; the pool contains a few hundred candidates per event but they are autocorrelated.
- The events are not independent of the war's big days (23 March, 7 April, where the earlier analysis showed half of the summed move). No leave-out run was done here.
