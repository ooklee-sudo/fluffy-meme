# Analysis plan (written before the LLM coding of the study sample and before any panel estimates)

**Data.** McAuley Lab Amazon Reviews 2023, category Appliances (2,128,605 reviews, 94,319 products, Oct 2000 – Sep 2023; collected 2023).
Public file: huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023.

**Research question.** Do the product attributes that reviewers mention, and the way they evaluate them, shape how many reviews a product receives next?

**Sample.** Random draw (seed 20261014) of 100 products with 150–400 reviews, first review in 2013 or later, and at least 36 months between first and last review. All reviews of these products are coded by an LLM (about 25–30k reviews).
Review *counts* are computed from the full file; coded text is used only for attribute variables.

**Unit and outcome.** Product-month from the product's first review through Aug 2023. Outcome: number of reviews Y_it.

**Hypotheses (directional, from prior literature on word of mouth and sales).**
- H1: A higher share of past reviews reporting a product defect is associated with fewer future reviews.
- H2: A higher share of past reviews that praise performance/fit is associated with more future reviews.
- H3: A higher share of past reviews that complain about price is associated with fewer future reviews.
- Controls: log(1 + prior review count), prior mean rating.

**Model.** Poisson PML with product and calendar-month fixed effects, clustered by product; NB2 as a check. Covariates are cumulative shares through month t-1 among the product's coded reviews (months with no prior review are dropped).
**Primary covariates** are fixed here: defect share, performance-positive share, price-negative share. All other aspects are secondary and reported as exploratory.
Multiple testing: the three primary tests are reported with Holm-adjusted p-values.

**Identification and robustness.**
1. Placebo leads: shares at t+1 and t+3 should not predict Y_it once lags are included.
2. Lag structure: 3-, 6-, 12-month windowed shares instead of cumulative.
3. Excluding the top 10% of products by volume; excluding the first 12 months of each product.
4. Regression discontinuity at the half-star display-rounding thresholds (3.25, 3.75, 4.25, 4.75) of the running mean rating, on all products with at least 100 reviews and at least 30 prior reviews (assumption: displayed stars round to the nearest half star; this is not verified here). Local Poisson, bandwidth 0.10, threshold and month effects, clustered by product.
5. Aggregate-series and dispersion analysis on the full category (monthly series, Poisson vs NB).

**Validation of LLM coding.** Fresh random sample of 400 from the study reviews; two LLM coders of different tiers; 150 reviews for blind human coding (pending). Reliability reported per aspect.
