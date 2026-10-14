# Is the arrival of Trump's Iran-attack signals a Poisson process? Analysis plan (fixed before counting)

**Status.** Written 2026-10-14 at the author's question ("don't Trump's attack signals follow a Poisson distribution?"). Only file structure (columns, date range) was inspected; no count was computed.
**Data.** CNN's public Truth Social archive of Donald Trump's posts (`ix.cnn.io/data/truth-social/truth_archive.csv`, through 13 Oct 2026; fields id, created_at (UTC), content). Posts that are pure re-posts ("RT:" without added text) are excluded. Window: 1 March 2026 (UTC) to 13 October 2026.
**Definition of an "attack signal" (fixed now).** S1: a post whose text matches Iran (`\biran`) AND at least one threat term (`attack|strik|bomb|destroy|obliterat|annihilat|wipe[sd]? out|blow(n)? up|kill|ultimatum|very hard`). S2 (stricter): S1 AND a forward-looking modality term (`will|would|going to|if |unless|or else|tonight|soon|next`). Counts are by day and by week (UTC dates; the week starts on Monday).
**Tests of the Poisson (constant-rate, independent) hypothesis.**
1. Dispersion index D = Σ(x−x̄)²/x̄ on daily counts against χ²(n−1); same for weekly counts; parametric-bootstrap p-value (5,000 Poisson samples) as a check.
2. Negative binomial fit vs Poisson (likelihood ratio, p halved for the boundary).
3. Inter-arrival times between consecutive signals (in hours): coefficient of variation (Poisson/exponential: CV = 1) and a Kolmogorov–Smirnov test against the exponential with the fitted rate.
4. Clustering: autocorrelation of daily counts at lags 1–7; a self-exciting (Hawkes) check by comparing the mean count on days after a day with ≥ 1 signal to days after a day with none.
5. Time-varying rate: Poisson regression of daily counts on week fixed effects; Pearson dispersion of the residuals (if ≈ 1, a time-varying Poisson rate is adequate).
6. Overlap with the 14 events used in `../bigtech/ANALYSIS_PLAN.md` (share of signals within ±1 day of those events).
**Interpretation.** The simple homogeneous Poisson is rejected if the dispersion p < 0.05 in both daily and weekly counts or the exponential KS p < 0.05. Expected finding (stated as a prior): clustering around news events, i.e., overdispersion.
**Limitations.** Keyword matching misclassifies (e.g., 'strike' in non-military senses; threats expressed without the listed words); only Truth Social posts, not speeches, interviews or other platforms; re-posts with comments are included as posts; UTC dates vs U.S. time zones; post counts also vary with Trump's overall posting rate (high-volume nights).
