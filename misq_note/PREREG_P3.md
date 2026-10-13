# Pre-registration: Prediction 3 (strategic substitutability of review supply), Steam and Amazon (written before estimation)

**Source.** `THEORY_MEMO.md`, Proposition 2: if the marginal value of one more review falls with the stock N of existing reviews, review writing is a strategic substitute. Removing (Amazon) or de-weighting (Steam) incentive-driven reviews lowers N and raises the writing probability of organic reviewers, and this substitution is **larger the smaller the pre-policy stock of reviews**. The author reports the advisor agreed with the theoretical direction.

**What is already known (not evidence for P3).** Steam purchase reviews rose with key exposure (+0.060 per +10 pp, p = 0.03; no placebo run for this outcome) and Amazon non-flagged volume had a positive but insignificant coefficient (+0.054, p = 0.06; placebo failed). The heterogeneity prediction below has not been examined in any analysis.

**Prediction P3.** The substitution response of organic reviews to the policy exposure is decreasing in the pre-policy review stock: the interaction of exposure × Post with the (standardized log) pre-policy review count is **negative**.

**Steam (primary test P3-S).**
- Sample and exposure as in `steam/ANALYSIS_PLAN.md`: 5,345 eligible games, K10 = share of pre-window (2015-01 to 2016-08) reviews with steam_purchase == 0 in units of 10 pp; Post = month on or after 2016-10, 2016-09 excluded; window 2015-01 to 2017-12.
- zN0 = z-score across eligible games of log(number of reviews with known purchase status in 2015-01 to 2016-08).
- Model: Poisson PML, E[Y_gt] = exp(α_g + γ_t + β₁·K10·Post + β₂·K10·Post·zN0), outcome Y = purchase reviews (steam_purchase == 1), game and month effects, standard errors clustered by game. P3-S predicts **β₂ < 0**.

**Amazon (primary test P3-A).**
- Sample and exposure as in `study3/ANALYSIS_PLAN.md`: 2,454 eligible products, E10 = share of pre-window flagged (disclosed incentive) reviews in units of 10 pp; Post = month on or after 2016-10; window 2015-01 to 2017-12.
- zN0 = z-score across eligible products of log(number of reviews in 2014-01 to 2016-09).
- Model: Poisson PML, outcome = non-flagged reviews, product and month effects, clustered by product; E10·Post and E10·Post·zN0. P3-A predicts **β₂ < 0**.

**Multiple testing.** Holm adjustment over P3-S and P3-A (two primary tests). The main effects β₁ are secondary and are reported without a directional claim.

**Checks (reported next to each primary test).** (i) Placebo with a fake policy date one year earlier (2015-10; exposure and zN0 measured in the corresponding earlier window; Steam window 2014-03 to 2016-08, Amazon window 2014-07 to 2016-09). (ii) Steam: English-language reviews only. (iii) Dropping the top 5% of games or products by pre-policy volume.

**Interpretation rules fixed in advance.** A negative, significant β₂ with a null placebo interaction counts as support for P3; any other pattern is reported as not supporting it. Because the main volume designs for both platforms failed their placebo tests, support for P3 is described as suggestive, not causal. Exposure and stock are correlated by construction (K10 uses the same pre-window reviews that define N0); the K10 × zN0 correlation is reported.
