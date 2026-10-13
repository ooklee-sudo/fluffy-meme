# Addendum 1 (written before estimation): New prediction P1 from the theory memo

**Context.** `THEORY_MEMO.md` (Poisson arrival of reviews, learning with signal arrival rate λ). The author reports that the advisor agreed with the theoretical direction. Prediction P1 is new: it has not been examined in any analysis so far (the volume, rating-level and event-study results of `ANALYSIS_PLAN.md` are known and are not re-used as evidence here).

**Prediction P1 (information arrival).** If reviews are signals of fixed latent quality arriving at rate λ, the variance of a restaurant's monthly mean rating is approximately σ²/n_it, so it rises when the number of reviews n falls. Restaurants whose review volume fell more after March 2020 (low takeout orientation T_i) should therefore show a larger rise in the within-restaurant variance of monthly mean ratings.

**Definitions (fixed here).**
- Monthly mean rating m_it = mean stars of restaurant i in month t, defined only for months with n_it ≥ 3.
- Period variance V_ip = sample variance of m_it over qualifying months in period p. Pre: 2018-03 to 2020-02. Post: 2020-03 to 2021-12. A restaurant enters only if it has at least 6 qualifying months in each period.
- Exposure: standardized T_i as in the main plan (pre-window takeout/delivery mention share, eligible if at least 10 reviews in that window).
- n_h,ip = harmonic mean of n_it over qualifying months of the period.

**Primary test (P1).** Restaurant-level regression log V_ip = α_i + γ·Post_p + β·(Post_p × T_i) + ε_ip with restaurant effects, standard errors clustered by restaurant. P1 predicts β < 0 (higher takeout orientation, smaller rise in variance).

**Secondary tests (learning-theory implications).**
- S1: In the same panel, log V_ip on log n_h,ip with restaurant effects. The theory implies an elasticity of −1; report the estimate and whether the confidence interval includes −1 and excludes 0.
- S2: Mediation check: add log n_h,ip to the primary regression. If information arrival drives the result, |β| should fall markedly.

**Checks.** (i) Placebo: periods 2017-03 to 2019-02 versus 2019-03 to 2020-02 (second period has 12 months; at least 6 qualifying months required in each); exposure from 2017-03 to 2019-02. (ii) Alternative threshold n ≥ 5. (iii) Category-based exposure (takeout-oriented versus dine-in-oriented categories). (iv) Excluding Alberta.

**Threats stated in advance.** Selection into qualifying months changes after the shock (fewer months reach n ≥ 3, mostly for low-T restaurants); the sample variance with few months is noisy; ratings are not independent signals (reviewer composition changed during COVID); the mean-variance link also holds mechanically for any process with a stable rating distribution, so P1 is a consistency check of the information-arrival channel, not proof of learning by consumers.
