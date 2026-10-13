# Addendum 2 (written before any Yelp review text is LLM-coded): content analysis of restaurant reviews around March 2020

**Context.** `ANALYSIS_PLAN.md` (volume, rating, event study) and Addendum 1 (variance of monthly mean rating) are done. This addendum fixes the LLM-coded content analysis (hypothesis C4 of the main plan). The theory memo motivates it: a shock to visits (μ) should change what reviews are about, and information-arrival (λ) differs by takeout orientation T_i. The author reports that the advisor agreed with the theoretical direction. Prior work has already shown that safety/hygiene and takeout/delivery topics rose in Yelp restaurant reviews during COVID-19 (topic models, BERT); the first two hypotheses below replicate that, and only the heterogeneity hypotheses are new.

**Sample.** Eligible restaurants as in the main plan (at least 10 reviews in 2018-03 to 2020-02, T_i = pre-window takeout/delivery mention share). T-terciles are formed among eligible restaurants (Low, Mid, High). Periods: Pre = 2019-03 to 2020-02, Post = 2020-03 to 2021-02 (first pandemic year). Stratified random sample of reviews (seed 20261020): **3,300 reviews per tercile × period cell, 19,800 reviews**, no more than 5 reviews per restaurant per cell. Reviews are truncated to 1,500 characters. A fresh random subsample of 400 of these reviews is also coded by a second, larger model (coder A) for reliability; 150 of the 400 form the blind sheet for two human coders (pending).

**Coders.** Coder H: a smaller LLM (haiku tier), 150 reviews per batch, review text treated as data; coder A: a larger LLM (sonnet tier) on the 400 validation reviews. Prompts and codebook below are fixed; model versions will be recorded by the authors before submission.

**Codebook (restaurant v1).** For each review: `overall` (neg/neu/pos), and each of the following aspects coded 0 not mentioned, −1 mentioned negatively, 1 positively, 2 neutral or mixed:
`safety` (COVID safety, masks, distancing, sanitation, health rules), `takeout` (takeout, to-go, delivery, curbside, drive-through, third-party delivery apps), `service` (staff, friendliness, speed of service, wait), `price` (price, value, fees), `food` (taste, quality, portion, freshness), `space` (seating, atmosphere, noise, crowding, outdoor/indoor space).

**Outcomes (LLM-coded).** For each aspect the mention indicator (any non-zero code); for safety and takeout also the negative-mention indicator; overall negative indicator.

**Hypotheses.**
- L1 (replication): the share of reviews mentioning safety and the share mentioning takeout are higher in Post than in Pre.
- L2 (replication): the share with overall negative sentiment changes by no more than ±3 percentage points between Pre and Post (equivalence margin; stated in advance because earlier work reports small star-rating changes).
- L3 (new, heterogeneity): the Post-minus-Pre increase in safety mentions is larger for Low-T restaurants than for High-T restaurants (more dine-in-dependent restaurants face more safety-related discussion).
- L4 (new, heterogeneity): the Post-minus-Pre increase in takeout mentions is smaller for Low-T than High-T restaurants. (Direction not guaranteed because High-T restaurants already mention takeout often; reported as two-sided.)

**Estimators.** Review-level linear probability models of each outcome on Post, T-tercile indicators and Post × tercile interactions, state fixed effects, standard errors clustered by restaurant. L3 and L4 test the Post × Low and Post × High interactions (reference Mid). Holm adjustment over the four primary tests: L1-safety, L1-takeout, L3, L4. L2 is reported as an equivalence check (90% confidence interval within ±3 pp).

**Validation.** Cohen's κ between coder H and coder A for each field on the 400 shared reviews; agreement with human coders on the 150-review blind sheet when completed (pending). Aspects with κ below 0.60 are reported but excluded from the primary tests.

**Checks.** (i) Placebo comparison Pre-year 2018-03 to 2019-02 versus 2019-03 to 2020-02 for the sampled aspects (requires coding a separate placebo sample; only done if L1 holds). (ii) Regex proxy analyses (already run) are used only to compare with the LLM measure of safety and takeout mentions on the same reviews (correlation and agreement). (iii) Dropping Alberta.

**Threats stated in advance.** Review text sampled at random across restaurants (not a restaurant panel), so restaurant effects are not used; T_i is estimated from text and may reflect restaurant type; composition of reviewers changed during COVID; LLM coders may treat COVID language inconsistently (checked through κ); cost of coding is about the same as the Amazon study (about 130 batches of 150).
