# Study 3 analysis plan (fixed before any outcome is estimated)

**Setting.** On 3 Oct 2016 Amazon banned reviews written in exchange for free or discounted products (Vine excepted; all categories but books; public announcement, widely reported). We study its effect on review supply and review content in the Appliances category of McAuley Lab Amazon Reviews 2023 (2,128,605 reviews, 94,319 products, Oct 2000–Sep 2023).
This design replaces the random-sample "attribute → inflow" design of `study2/` (which is retained as exploratory pilot material; its plan was written first and its coding was stopped at 33 of 165 batches).

**Exposure.** A review is *flagged* if `incentive.py` (v3; rule fixed here, estimated precision about 95% in a 40-review hand check; recall unknown and expected to be well below 1 because only disclosed incentives are visible) detects a disclosure of receiving the product free or discounted for a review.
Pre-policy window: 2014-01-01 to 2016-09-30. For product i: E_i = share of its pre-window reviews that are flagged.
Eligible products: at least 20 pre-window reviews and first review before 2016-07-01 (2,454 products). Treated (binary): at least 2 flagged pre-window reviews (137 products). Control candidates: 0 flagged pre-window reviews (2,270).

**Hypotheses.**
- H1 (supply): total monthly review counts fall more after the ban for products with higher E_i (β < 0).
- H2 (rating): the average star rating of new reviews falls more for higher E_i (β < 0), consistent with Amazon's stated reason that incentivized reviews are more positive.
- H3 (content): among non-flagged reviews, the share reporting a defect and the share with negative overall sentiment rise more for exposed products (β > 0), and the share praising performance falls (β < 0).
- H4 (heterogeneity, exploratory): the volume decline is larger for products with fewer pre-window reviews.

**Estimators.**
1. Volume: Poisson PML, E[Y_it] = exp(α_i + γ_t + β·E_i·Post_t), product and month effects, standard errors clustered by product. Window 2015-01 to 2017-12 (Post = on or after 2016-10); robustness window 2015-01 to 2018-12. Event-study version with quarter × E_i interactions, reference 2016Q3.
   Two outcomes: (a) all reviews; (b) non-flagged reviews only. (a) includes the mechanical disappearance of flagged reviews; (b) isolates spillovers on other reviews.
   Primary exposure: continuous E_i (effect reported per +10 percentage points). Secondary: binary treated vs. matched controls, and thresholds of at least 1 and at least 3 flagged reviews.
2. Rating: review-level OLS, rating on E_i·Post with product and month effects, clustered by product, non-flagged reviews, same window.
3. Content (LLM-coded): treated products (137) are matched 1:1 without replacement to control candidates by Mahalanobis distance on log pre-window review count, pre-window mean rating, and year of first review (matching uses pre-policy data only). For each product, up to 40 non-flagged reviews are drawn at random from 2016-01 to 2016-09 (pre) and up to 40 from 2016-10 to 2017-09 (post). LLM-coded outcomes: defect reported, negative overall sentiment, performance praised (performance = +1). Linear probability model with product and quarter effects on Treated × Post, clustered by product. Non-LLM outcomes (star rating, review length, verified purchase, helpful votes) are reported for the same sample.
4. Multiple testing: primary tests are H1(a) volume, H2 rating, and the three H3 outcomes (five tests), Holm-adjusted. Everything else is exploratory.

**Identification checks.** (i) Pre-trend and event-study coefficients before 2016Q4. (ii) Placebo policy date of 2015-10-01 with exposure measured on 2014-01 to 2015-09 and window 2014-07 to 2016-09. (iii) Alternative exposure definitions. (iv) Dropping the 5% highest-volume products. (v) Aggregate monthly series for the whole category: Poisson versus NB2 dispersion diagnostics, and a structural-break check at 2016-10.

**Threats stated in advance.** Exposure is measured only through disclosed incentives, so hidden incentives bias estimates toward zero; exposed products may be younger or be in categories that rely on early reviews (matching and fixed effects only partly address this); controls are not untouched because the policy applied platform-wide, so estimates are relative effects; Vine reviews are not identifiable and are likely to be in the data unflagged.

**Validation of LLM coding.** A fresh random sample of 400 from the content sample, coded by two LLM coders of different tiers; 150 reviews for blind coding by two humans (pending, to be completed by the authors); per-field κ reported.
