# Steam study: analysis plan (fixed before any outcome is estimated)

**Setting.** On 12 Sep 2016 Valve stopped counting reviews written by users who activated the game with a product key (not bought on Steam) in the displayed recent and overall review scores; those reviews remain visible. Valve cited an analysis that at least 160 titles had markedly higher positive shares among key-activated reviewers than among Steam purchasers (press coverage: about 14% of games affected). Later changes (gift and free-weekend reviews, language-specific scores, review sorting) are not studied here. Sources: Valve announcement (store.steampowered.com/oldnews/24155) and press coverage.
Parallel platform shock: Amazon's ban on incentivized reviews on 3 Oct 2016 (see `study3/`). The Steam study uses the same design logic so that the two can be compared.

**Data.** Kaggle `kieranpoc/steam-reviews` as mirrored at huggingface.co/datasets/adde023/steam-reviews (about 113 million reviews in 663 parquet parts, CC BY-NC 4.0). Fields used: appid, timestamp_created, steam_purchase, received_for_free, voted_up, language. Coverage after about Nov 2023 is not assumed. Whether the file is complete for each month is checked from monthly totals before analysis; months with collection anomalies are reported and excluded in robustness.

**Exposure (directly measured, no text rules).** For game g, K_g = share of its reviews posted 2015-01 to 2016-08 with steam_purchase == 0 (not bought on Steam, i.e. key-activated or otherwise obtained). Eligible games: at least 30 reviews in that pre-window and first review before 2016-01-01.
Primary exposure is continuous K_g (effects per +10 percentage points) and standardized (per 1 SD) for the comparison with Amazon.

**Hypotheses.**
- S1 (key supply): the monthly number of key-activated (steam_purchase == 0) reviews falls more after the policy for higher K_g (β < 0).
- S2 (total volume): total monthly reviews; two-sided, because purchasers' reviews may substitute.
- S3 (positivity): the share of positive (voted_up) reviews among new reviews falls more for higher K_g (β < 0), because key-driven positive reviews decline.
- S4 (within-game contrast, descriptive): the gap in positive share between key-activated and purchased reviews narrows after the policy.

**Estimators.** Game-month panel, window 2015-01 to 2017-12, Post = on or after 2016-10 (Sep 2016 is the transition month and is excluded).
1. Counts: Poisson PML, E[Y_gt] = exp(α_g + γ_t + β·K_g·Post_t), game and month effects, clustered by game. Outcomes: key reviews (S1), all reviews (S2).
2. Positivity: weighted least squares on the game-month share positive (weights = review counts), same effects, clustered by game (S3).
3. Event study with quarter × K_g interactions, reference 2016Q2 (the last full quarter before the policy; Q3 contains the transition).
4. Multiple testing: S1, S2, S3 as the primary family, Holm-adjusted.

**Checks.** (i) Placebo policy date 2015-09-12 with exposure from 2014-03 to 2015-08 and window 2014-03 to 2016-08. (ii) English-language reviews only. (iii) Alternative exposure definition: share with received_for_free == 1, and a binary top-tercile definition. (iv) Dropping the top 5% of games by pre-period volume. (v) Window extended to 2018-12.

**Comparison with Amazon (qualitative).** Report the sign and standardized magnitude of the key outcomes for both platforms side by side. No pooled test, because outcomes, exposure measures, and mechanisms differ (disclosed incentive vs. key activation).

**Threats stated in advance.** Key-activated reviewers include legitimate players who bought elsewhere (retail keys, bundles, Kickstarter backers), so K_g is not a pure incentive measure; early-access, release-timing and sales events differ across games and may confound; Valve's other 2016–2017 review changes may overlap; the dataset's collection process is not documented in detail; text-based analysis is out of scope here.

**Not in scope.** No LLM coding of review text in this study. The 2024 FTC rule (effective 21 Oct 2024) is outside the data period.
