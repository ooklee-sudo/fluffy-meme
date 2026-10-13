# Yelp COVID-19 restaurant study: analysis plan (fixed before any outcome is estimated)

**Status of the idea.** COVID-19 and Yelp restaurant reviews have been studied extensively (rating and sentiment shifts, hygiene/safety/takeout topics via LDA or BERT, review counts early in 2020). Searches did not find a Yelp review-volume event study that uses a pre-determined takeout orientation, nor an LLM-coded attribute comparison with human validation. These searches were limited (no search of ISR/MISQ archives succeeded), so the novelty claim must be checked by the authors before use. A theoretical framing for an IS journal is **not yet specified** and is left to the authors.

**Data.** Yelp Open Dataset as mirrored on Hugging Face (`yashraizad/yelp-open-dataset-reviews` and `-business`; Apache-2.0 per card; 6,990,280 reviews, 150,346 businesses, review dates 2005-02 to 2022-01-19; business file has name, city, state, categories, location, stars, review_count but no attributes and no open/closed flag). Restaurants = businesses whose categories contain "Restaurants" (52,268). Jurisdictions: PA, FL, TN, MO, IN, LA, NJ, AZ, AB (Canada), NV, ID, CA, IL, DE.

**Shock.** The COVID-19 restrictions of March 2020. Primary: a common start in March 2020 (Post = review month on or after 2020-03). Jurisdiction-specific order dates are not used in the primary analysis (they would have to be compiled and verified from an official tracker before use; if used, only as a robustness check).

**Exposure (pre-determined, from pre-shock text only).** For restaurant i, T_i = share of its reviews posted 2018-03-01 to 2020-02-29 whose text matches the regular expression
`\b(take[- ]?out|to[- ]?go|carry[- ]?out|delivery|deliver(ed|s)?|drive[- ]?thr(u|ough)|pick[- ]?up)\b` (case-insensitive).
Higher T_i = more takeout/delivery oriented, hence a-priori less exposed to dine-in restrictions. Eligible: at least 10 reviews in that pre-window. Primary exposure is T_i standardized (per 1 SD). Secondary: category-based indicator (Fast Food, Pizza, Sandwiches, Burgers, Chicken Wings, Food Trucks, Bakeries, Coffee & Tea versus Bars, Nightlife, Steakhouses, Buffets, Breweries, Wine Bars).

**Hypotheses.**
- C1 (volume): after March 2020, restaurants with higher T_i lose less review volume (β > 0 for T_i × Post).
- C2 (rating): average star rating of new reviews shifts differently with T_i (two-sided; no prior).
- C3 (dynamics): the C1 effect appears at the onset (March–May 2020), not before (event study, reference 2020-02).
- C4 (content, LLM-coded sample; see below): the shares of reviews that mention safety/hygiene and takeout/delivery rise after March 2020 (replication of earlier findings), and rise more for low-T_i restaurants for safety and less for takeout (exploratory).

**Estimators.** Business-month panel, 2018-03 to 2021-12 (24 pre-months, 22 post-months; 2022-01 is partial and excluded). Rows: months from the start of the window for every eligible restaurant, with zeros when no reviews (restaurants that closed contribute zeros; there is no open/closed flag, so closure and reduced reviewing cannot be separated).
1. Counts: Poisson PML, E[Y_it] = exp(α_i + γ_t + β·T_i·Post_t), business and year-month effects, clustered by business. Robustness: clustered by city.
2. Rating: review-level OLS of stars on T_i × Post with business and year-month effects, clustered by business.
3. Event study: monthly interactions with T_i, reference 2020-02.
4. Holm adjustment over the primary family: C1 and C2.

**Checks.** (i) Placebo shock 2019-03 with exposure from 2017-03 to 2019-02 and window 2017-03 to 2020-02. (ii) Excluding Alberta; excluding the top 5% of restaurants by pre-period volume. (iii) Category-based exposure. (iv) Pre-window mention rate of takeout computed on 2017-03 to 2018-02 instead (stability of exposure). (v) Descriptive: a regex proxy for COVID/safety content (`covid|corona|pandemic|mask|social distanc|sanitiz|curbside|contactless`) by month.

**LLM coding (not yet run).** To be decided with the authors: random sample of restaurant reviews stratified by period (pre/post) and T_i tercile; codebook with safety/hygiene, takeout/delivery, service, price, food quality, and overall sentiment; two LLM coders; blind human coding of 150 reviews (pending). Cost is similar to the Amazon study.

**Threats stated in advance.** Yelp reviews are not visits; reviewer composition changed; T_i is estimated from text and may reflect restaurant type rather than takeout capability; restaurants adapted to takeout during the pandemic after T_i was measured; dataset construction and selection by Yelp are not documented; infection and policy severity differ across jurisdictions and are correlated with trends; no open/closed information.
