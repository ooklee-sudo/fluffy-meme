# Results: P7, timing surprisal (plan: ANALYSIS_PLAN_TIMING.md; code: analysis_timing.py; numbers: results_timing.json)

**P7 is not supported.** In the pooled primary model the standardized timing surprisal has beta_S = +0.040 (SE 0.065; one-sided p = .27; n = 685). The point estimate has the predicted sign, but it is small, at 0.04 SD of |z| per SD of S, and the interval comfortably includes zero.

| Sample | n valid | beta_S | SE | p (one-sided) | Holm p |
|---|---|---|---|---|---|
| Truth Social war-period signal posts (WTI) | 108 | -0.012 | 0.254 | .52 | 1 |
| Twitter oil/Iran (WTI) | 182 | -0.020 | 0.074 | .61 | 1 |
| Twitter tariff (S&P) | 395 | +0.080 | 0.094 | .20 | .60 |

Exploratory checks (none changes the conclusion): S x N_c interaction -0.061 (p = .56); count-based S_cnt -0.001; winsorized S +0.038; log|z| outcome +0.029; dropping posts within 5 min of the previous one -0.008 (n = 596); weekdays only +0.030. Spearman(S, |z|) = 0.014; Spearman(S, |z_pre|) = 0.047, so timing surprisal is almost unrelated to pre-post volatility, which means the null is not a volatility-control artifact.

## Sample accounting
- Truth Social: 191 signal posts (human_labels_191); 166 had S (at least 30 prior-60-day gaps in the session bucket); 108 had a tick window for N_c, U, z_pre and the outcome.
- Twitter oil: 278 kept frame posts (3-hour gap rule inherited from the frame); 272 with S; 182 with a valid window.
- Twitter tariff: 632 kept; 622 with S; 395 with a valid window.
- Windows are missing when the market was closed at the post time (staleness over 10 minutes), as in all earlier tick tests.

## Implementation notes and departures to report
1. "Original posts" for the gap stream = all posts that are not reposts (Truth Social: content starting "RT"; Twitter: text starting "RT @"). Link-only and media-only posts stay in the stream. The plan said "exactly as in the existing frames"; the frames filter only on this repost rule for the account stream, so this is the same rule.
2. The Truth Social sample is the 191 human-labelled signal posts. The plan's phrase "larger 5-min sample" was not used because no separate post list with N_c and U exists for it.
3. The minimum of 30 gaps is applied within the session bucket of the previous post.
4. S_cnt baseline uses only four weekly observations of the same hour-of-week, so it is noisy (robustness only).
5. The prior-hour post count control excludes the focal post.

## Interpretation
Timing surprisal under a rolling lognormal predictive model carries no detectable information about the 30-minute market reaction in any of the three samples. This is the fourth measurable information-theoretic implication that fails (with HI1, HI3 and the state-dependent P6), while only the descriptive mutual-information result for the war sample and HI2 in the tariff sample (volatility-confounded) held. The confidence interval for the pooled beta_S (about -0.09 to +0.17 SD) rules out a medium effect, but not a small one; with n = 685 the test could not detect effects below roughly 0.11 SD.
