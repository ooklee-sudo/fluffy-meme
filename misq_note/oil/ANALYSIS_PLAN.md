# Oil-price shock (2026 Iran war) and short-term-rental review arrivals: analysis plan (fixed before any outcome is estimated)

**Status.** Written 2026-10-13 before any listing- or review-level outcome from Inside Airbnb was examined. The only data looked at so far are the existence, file structure and calendar coverage of the files (one city, Asheville, was opened to check columns and monthly counts; those counts are not used for design). The author reports that the advisor agreed with the direction. A literature search found hotel-demand studies of gasoline prices (e.g., Canina, Walsh and Enz) but no Airbnb/short-term-rental estimate; this was a single search and the novelty claim must be checked by the authors.

**Shock.** The 2026 Iran war began with US-Israeli strikes on Saturday 28 Feb 2026 (a non-trading day); oil markets reacted on Monday 2 Mar 2026. Brent rose from about 72 USD (27 Feb) to a peak near 120 USD, and about 51% in March (CNBC timeline, 2026-04-21; figures approximate and not verified against a price series). US gasoline was about 3.94 USD in late March and about 4.36 USD in mid-October 2026 (AAA via press). Fuel prices stay elevated and volatile through the data window, so the event is an onset with a persistent, fluctuating level.

**Data.** Inside Airbnb city files `reviews.csv.gz` (listing_id, review id, date, reviewer id, comments) and `listings.csv.gz` (location, type, price, host fields), scrape dates 14–23 Sep 2026. Primary sample: the 34 US cities. Exploratory: the non-US cities (Europe). Reviews are written after the stay (typically within about two weeks) and bookings made before the shock are still honored, so review arrivals respond with a lag; **Post = review month on or after April 2026; March 2026 is a transition month and excluded** (robustness: including March). September 2026 is partial and excluded.
Unit: listing-month review count, from the listing's first review month (or 2023-01 if earlier) through August 2026. Eligible listings: at least one review between 2024-03 and 2025-02 (active before the shock). Window: 2023-01 to 2026-08.

**Exposures (predetermined characteristics; measured from the listings snapshot, which is dated after the shock; this is stated as a threat).**
- Price tier: within-city tercile of the listed nightly price (low / mid / high). Prior: hotel studies find larger gasoline-price effects for economy than upscale lodging.
- Distance to the nearest large commercial airport (km, OurAirports data, `large_airport` with scheduled service), log(1 + km). Two competing channels (gasoline raises the cost of driving to far-from-airport locations; jet-fuel prices raise airfares for fly-in locations), so the sign is **not predicted**.
- Room type (entire home vs. private/shared room) as a secondary dimension.

**Hypotheses.**
- H1 (average effect, descriptive): reviews per listing fall after April 2026 relative to the seasonal-plus-trend counterfactual (interrupted time series; see Estimators).
- H2 (price tier, primary, directional): low-price-tier listings lose more review volume than high-price-tier listings in the same city and month (β < 0 for Low × Post, relative to High).
- H3 (airport distance, primary, two-sided): the sign of log(1 + distance to airport) × Post is estimated and reported without a directional claim.

**Estimators.**
1. H2 and H3: Poisson PML, E[Y_it] = exp(α_i + δ_{c(i),t} + β₁·Low_i·Post_t + β₂·Mid_i·Post_t + β₃·logDist_i·Post_t), with listing effects α_i and **city × year-month effects δ** (absorbing all city-wide shocks, seasonality and the common oil shock), standard errors clustered by listing; city-clustered standard errors as robustness (there are 34 clusters).
2. H1 (interrupted time series): Poisson PML with listing effects, city × calendar-month effects, a linear year trend estimated on 2023-01 to 2026-02, and Post (April–August 2026); the Post coefficient is the deviation from the seasonal-plus-trend counterfactual.
3. Event study: monthly interactions of Low_i (and logDist_i) with month, reference February 2026.
4. Holm adjustment over H2 and H3 (the two primary tests).

**Checks.** (i) Placebo shock dated 2025-03-01 (Post = 2025-04 to 2025-08), same estimators, window 2022-01 to 2025-08. (ii) Including March 2026 in Post. (iii) Non-US cities (exploratory, Europe). (iv) Dropping the top 5% of listings by review volume. (v) Alternative price definition: city-relative price rank continuous. (vi) Listings with at least 12 reviews before 2025-03 only.

**Not in scope / stated limitations.** No text analysis in this plan; no causal claim about fuel prices separately from the war's other effects (airfares, interest rates, consumer sentiment, security concerns, concurrent shocks); the listing snapshot is post-shock and excludes listings that left the platform; review counts are a lagged, incompletely observed proxy for stays; Inside Airbnb scrapes are collected by a third party and their completeness is not documented here; license terms of Inside Airbnb must be checked before publication.
