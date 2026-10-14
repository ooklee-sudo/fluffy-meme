# Pre-registration (robustness; committed before the variants are computed, 2026-10-14)

Prompted by simulated review round 2 (reviews/review_round2_synthesis.md). Already seen: the baseline human-label results (RESULTS_H7.md: de-escalation n = 29, post-30 +1.05%, paired post−pre +0.48, p = .030; escalation n = 16, +0.48%) and the placebo analysis (RESULTS_H5C_H8.md). Not seen: any variant below.

## Baseline (to be reproduced exactly)
Human final labels over the 191 war-period posts; keep a post if at least 3 hours passed since the previous of the 191 posts; keep DEESC and ESC with a valid market window (last tick within 10 minutes at t and t+30 minutes); directional return = sign × 100 × ln(P(t+30 min)/P(t)); pre-30 likewise; one-sided Wilcoxon for post > 0 and post > pre.

## Variants (each changes one thing from the baseline)
V1 cluster rule: none; 1 h; 2 h; 6 h.
V2 labels: only posts on which both coders agreed before adjudication (source = consensus).
V3 windows: post and pre windows of 5, 15, 30 and 60 minutes.
V4 staleness cutoff: last tick at most 2, 5 or 10 minutes old.
V5 influence: drop events on the two largest-move days of the earlier model-labelled analysis (2026-03-23 and 2026-04-07, UTC); also leave-one-event-out range of the mean; 10% trimmed mean and median.
V6 quote quality: median bid–ask spread (feed units, same scale as price) at the post times, and the ratio of the mean post-30 move in price units to that spread.
Reconciliation table: 191 posts → after cluster filter → DEESC/ESC by human label → with valid post window → with valid pre-60 window (the sample of the placebo analysis).

## Reporting
For every variant and class: n, mean and median post-30 (or window), one-sided Wilcoxon p, mean pre, mean paired difference, Wilcoxon p for post > pre. Summary: the number of variants in which the sign matches the baseline and the share with one-sided p < .05 (descriptive, no adjustment, because the variants are not independent). No variant is used to select a new headline. If the paired post−pre excess is not significant in most variants, the manuscript states that the post window and the pre window cannot be separated.
Output: RESULTS_ROBUST_HEADLINE.md, results_robust_headline.json, analysis_robust_headline.py.
