# Pre-registration: matched-hour placebo (H5c) and anticipatory-drift analysis (H8) (committed before the placebo data are analysed, 2026-10-14)

Already seen: tick-level post and pre 30-minute returns of the human-labelled sample (RESULTS_H7.md: de-escalation n = 29 mean pre-30 +0.57, post-30 +1.05; escalation n = 16 mean pre-30 +0.22, post-30 +0.48). Not seen: any placebo-time statistic, tick counts around posts, or the pre-post returns by first-source class on the human-labelled sample.

## Sample
Primary: the human-labelled war-period sample of RESULTS_H7.md (cluster filter: at least three hours since the previous post of any labelled class; market open at t−60 minutes, t, and t+30 minutes). Secondary: the 61 model-selected posts with model-1 labels.

## Placebo construction (both H5c and H8)
For each event, candidate placebo times are drawn uniformly within the same UTC clock hour on days −3 to +3 (excluding day 0) around the event day, restricted to the same weekday/weekend status; a candidate is dropped if it lies within ±2 hours of any labelled post (all 191 posts, any class) or if the market is not open at s−60, s and s+30 minutes (last tick within 10 minutes). One candidate per event per draw; 10,000 draws; the placebo statistic is the mean over events of the event-signed quantity (the event's own sign is applied to the placebo time). Events with no candidate are excluded and counted.

## H5c (post-window placebo)
Statistic: mean directional 30-minute return after the time. Test: observed mean ≥ the 95th percentile of the placebo distribution (one-sided α = .05); report the share of draws ≥ observed. Run for human-labelled DEESC (sign −1) and ESC (sign +1).

## H8 (anticipatory drift)
- **H8a:** mean directional return over [t−60, t−5] minutes and over [t−30, t) minutes compared with the placebo distribution of the same statistic (one-sided, α = .05, upper tail). Reported for DEESC and ESC. Interpretation rule fixed now: a result above the placebo's 95th percentile is "drift larger than in comparable hours"; it is not evidence of any particular cause.
- **H8b:** number of ticks in [t−30, t) relative to the placebo's mean tick count in the same window (a quote-activity proxy of the CFD feed); one-sided α = .05. Report the ratio.
- **H8c (public-news precedence; descriptive):** for events that have a first-source class (qual/wire_A–D.json; 61 events, partial overlap with the human sample), mean directional pre-30 return by class (POST_FIRST, OTHER_FIRST, SIMULTANEOUS) and the Wilcoxon two-sided comparison POST_FIRST vs OTHER_FIRST; no decision rule beyond reporting.

## Language rule
Neither result is evidence for or against information leakage or any named party's conduct; the manuscript will describe a significant H8a as "drift larger than in comparable hours, cause not identified".

## Reporting
RESULTS_H5C_H8.md; code `analysis_h5c_h8.py`; output `results_h5c_h8.json`.

## Amendments
(none)
