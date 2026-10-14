# Tick-level (5-minute resolution) test of post timing (plan: ANALYSIS_PLAN_5MIN.md; code: build_ticks.py, analysis_5min.py; output: results_5min.json)

Source: Dukascopy WTI crude CFD ticks (UTC), 61 war-period signal posts (33 DEESC, 28 ESC), market open at every post (no closed-market exclusions). Directional returns are measured from the last tick before the exact post time. **Validation passed:** the correlation of hourly returns from the tick series with the Yahoo CL=F hourly returns is 0.999 (n = 521 hours). Two-hour change from the bar open for de-escalation posts on tick data is +0.89% (n = 31) against +1.29% on CL=F; the CFD tracks the spot month, not the futures contract, so levels and some tails differ.
**H5c (matched-hour placebo) is not reported:** only 7 of 33 events had placebo candidates in the hours downloaded so far, so the pre-registered statistic cannot be computed; the download continues and H5c will be added when complete (it is not evidence either way).

## De-escalation posts (n = 33), directional return (%)
| Window after the post | mean | median | one-sided Wilcoxon p (> 0) | week-block 95% CI of mean |
|---|---|---|---|---|
| 5 min | +0.59 | +0.21 | 0.0003 | 0.27 to 0.98 |
| 15 min | +0.63 | +0.24 | 0.0016 | 0.31 to 1.02 |
| 30 min (H5a) | +0.86 | +0.41 | 0.0011 | 0.31 to 1.57 |
| 60 min | +1.03 | +0.42 | 0.0058 | 0.41 to 1.83 |
| 120 min | +0.85 | +0.61 | 0.018 | 0.12 to 1.69 |

| Window before the post (ending at t) | mean | paired difference post − pre | one-sided Wilcoxon p (post > pre) |
|---|---|---|---|
| 5 min | −0.12 | +0.71 | 0.00002 |
| 15 min | −0.12 | +0.74 | 0.002 |
| **30 min (H5b, primary)** | **+0.43** | **+0.43** | **0.025** |
| 60 min | +0.62 | −0.05 | 0.21 |
| 120 min | +0.56 | +0.32 | 0.16 |

**Decision under the pre-registered rule:** H5a supported (p = 0.0011) and H5b supported (p = 0.025), so the paper may claim that the post adds to a pre-post drift for de-escalation posts. The timing profile is informative: oil moved little in the 15 minutes before the post (−0.12%), had drifted in the direction of the post earlier in the hour (+0.43% over 30 minutes, +0.62% over 60 minutes), and then moved +0.59% within five minutes after the post. Longer windows (60 and 120 minutes) cannot separate the post from the earlier drift (paired differences −0.05 and +0.32, n.s.), which is why the hourly bars could not.

## Escalation posts (n = 28)
Post-window means: +0.21 (5 min), +0.09 (15), +0.07 (30), +0.22 (60), +0.39 (120); Wilcoxon p = 0.18, 0.26, 0.38, 0.11, 0.047. Only the 120-minute value passes an uncorrected one-sided 5% threshold (exploratory; five windows, not corrected); the paired post − pre differences are not significant (p ≥ 0.09). Escalation posts show no immediate response; the slower drift noted in the hourly data is consistent but weak.

## Descriptive: first-source class (30-minute directional return, both directions pooled)
POST_FIRST +0.67 (n = 32); OTHER_FIRST +0.15 (n = 14); SIMULTANEOUS +0.10 (n = 10); UNDETERMINABLE +1.18 (n = 5). Not tested (the pre-registered first-source test W1 was at the two-hour horizon).

## Limits
Tick source is a CFD, not exchange futures; 33 events, two of which are very large (the means of 0.6–1.0% are pulled by them; medians are 0.2–0.6%); the Wilcoxon p-values are not affected by the size of the two largest events but the pre/post paired tests use the same events; coder labels are from model instances; simultaneous news is still not excluded. A response within five minutes is consistent with the post being the news, but also with the post being published at nearly the same moment as other news.
