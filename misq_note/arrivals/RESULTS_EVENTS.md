# Results (exploratory): do external events explain the over-dispersion of posting? (plan: ANALYSIS_PLAN_EVENTS.md; code: analysis_events.py; numbers: results_events.json)

Answer by the decision rules fixed in advance: **events are statistically related to posting, but they account for little of its over-dispersion.**

| Pairing | n days | alpha baseline | alpha with lagged events | R = 1 − ratio (block-bootstrap 95% CI) | LR p (Holm) | Rule |
|---|---|---|---|---|---|---|
| Twitter all × world conflict events | 1,443 | 0.345 | 0.277 | 0.198 (0.13, 0.30) | < .001 | little (borderline) |
| Twitter all × riots | 1,443 | 0.345 | 0.286 | 0.173 (0.02, 0.14*) | .002 | little |
| Twitter oil/Iran × Iran conflict events | 1,443 | 2.234 | 1.734 | 0.224 (0.06, 0.44) | < .001 | partly |
| Twitter tariff × US–China conflict events | 1,443 | 1.638 | 1.459 | 0.109 (0.05, 0.18) | < .001 | little |
| Truth Social all × Iran conflict events | 220 | 0.356 | 0.323 | 0.091 (0.04, 0.19) | .006 | little |
| Truth Social Iran posts × Iran conflict events | 220 | 0.357 | 0.269 | 0.249 (0.09, 0.72) | .003 | partly |

*The riots interval as computed does not contain the point estimate (0.173 vs (0.02, 0.14)); the bootstrap resampled days with the original weekday labels and used only 100 resamples, so intervals are approximate and this one should not be quoted.

Never "most" (R >= .5): in no pairing do lagged events remove half of the dispersion. Same-day events (contaminated by reverse causation) change R by at most 0.04.

## Benchmark: slowly varying rate
Calendar-week fixed effects remove 66% (all Twitter), 78% (tariff), 90% (oil/Iran) and 19% (Truth Social all) of alpha. For the sparse subset series (oil, Iran posts) and the 31-week Truth Social series, week effects nearly saturate the data (alpha → 0 for Truth Social Iran posts), so these figures overstate what a smooth rate explains. The qualitative reading holds: most dispersion is a slowly moving rate (attention levels, campaigns, news cycles) that the daily conflict-event counts do not capture.

## Dynamic dependence (NB-INGARCH with the same covariates in the baseline term)
- Twitter all-original: persistence a+b 0.988 → 0.980 when events are controlled; events do not remove the self-excitation. Log-likelihood gain 1.4 for four parameters.
- Truth Social all-original: a+b 0.959 → 0.464 and log-likelihood +8.7. Here the Iran event series is itself extremely persistent (lag-1 autocorrelation 0.96), so it takes over the slow level that the lagged-count terms otherwise carry; this does not show that the events cause the posting, and the result is for one 220-day series.

## The event series themselves are not Poisson
Daily GDELT counts of Iran-related conflict events: variance/mean 550 (2017–21) and 907 (2026); lag-1 autocorrelation 0.85 and 0.96; lag-7 0.42 and 0.80. World conflict, US–China conflict events: lag-1 0.75 and 0.74. GDELT counts reflect media coverage, not only the physical events, but whatever the posts respond to is at least this clustered. The premise "the events are Poisson" fails at the daily scale; this fits the Hawkes literature on conflict events (see the literature note in the session and the manuscript's Section 4.1 revision) and the Richardson result is about annual war onsets, not daily events within a war.

## Deviations and caveats
1. Block-bootstrap intervals use 100 resamples (plan: 2,000); the processes were run in a time-limited sandbox. Intervals are approximate.
2. The Truth Social "Iran posts" series is defined here as original posts whose text contains "iran" (case-insensitive); it is not the keyword threat class of Section 4.1.
3. Pairings run are exactly those listed in the plan; Truth Social all × world conflict was not run.
4. The question was posed after the dispersion results were seen. Everything here is exploratory.
5. GDELT 1.0 is media-derived; the posts themselves generate coverage. Lags and the N_ALL control only partly remove this.
