# Pre-registration: confirmatory test of the information-theoretic propositions on the 2017–2021 Twitter sample (oil/Iran/energy), committed before any model labelling, tick download or return computation (2026-10-14)

Already seen about this sample: only that the public archive exists, the number of keyword tweets by year (341 in the frame below: 2017 41, 2018 72, 2019 126, 2020 102), and a few sample texts. Not seen: any price, return, label or novelty score for these tweets. (The authors have seen the Truth Social results that motivate the propositions; this is an out-of-sample test of them.)

## Sample frame (fixed by rule, no outcome information)
Original tweets (not starting with "RT @") by @realDonaldTrump from 2017-01-20 to 2021-01-08 whose text matches (case-insensitive) iran*, oil, opec, saudi*, crude, gasoline, energy, hormuz, strait, petroleum, pipeline*, refiner*. 341 tweets; file `frame_oil_iran.csv`. Exact UTC time = Twitter snowflake id timestamp ((id >> 22) + 1288834974657 ms). Cluster filter: a frame tweet is kept if at least 3 hours have passed since the previous frame tweet.

## Market data
Dukascopy WTI crude CFD ticks (`LIGHTCMDUSD`), UTC; mid price; price at time s = mid of the last tick at or before s, valid only if that tick is at most 10 minutes old. An event needs valid prices at t, t+30 min and t−30 min. Events lacking them (market closed) are excluded and counted.
Daily WTI (FRED `DCOILWTICO`, `rawd/DCOILWTICO.csv`) for volatility scaling.

## Measures (computed without returns where possible)
- **Outcome |z|** = |100·ln(P(t+30 min)/P(t))| / s30, where s30 = σ_d × sqrt(30/1380) and σ_d = standard deviation (in percent) of the 60 daily log WTI returns before the tweet date (the 1380 assumes about 23 trading hours). Events with fewer than 40 valid daily returns are excluded.
- **Novelty N_c** (text only): conditional compression ratio as in ANALYSIS_PLAN_INFO.md, with the context = last 30,000 characters of the account's original tweets in the preceding 7 days (all topics); tweets shorter than 20 characters after removing URLs get N_c = 0. Robustness: N_t (TF-IDF) as before.
- **Prior-uncertainty U** = ln(sd of the 5 daily WTI log returns before the tweet date / sd of the 60 before it).
- **Labels:** direction (ESC, DEESC, MIXED, OTHER) by two independent model instances from text only with the human codebook v2; "agreed" label when both agree; human labels for as many posts as human coders can code, the human consensus (adjudicated by the principal investigator when needed) overriding the model.

## Hypotheses (confirmatory; decision rules fixed now)
Regression for HI1–HI3: |z| on N_c, U, N_c × U with year fixed effects; OLS; standard errors clustered by UTC day; sample = all frame tweets passing the filter with valid windows (label-free).
- **HI1:** coefficient of N_c > 0. **HI2:** coefficient of U > 0 (main-effects model). **HI3:** coefficient of N_c × U > 0 (model with both main effects).
- One-sided tests, Holm adjustment across the three at α = .05. "Supported" means Holm-adjusted p < .05 for that hypothesis. Failure is reported as failure.
- **H10 (directional response, replication of the Truth Social result):** among tweets with an agreed model label of de-escalation (DEESC), the mean directional 30-minute return (sign −1; positive = oil falls) > 0, one-sided Wilcoxon, α = .05; same for escalation (sign +1). Repeated on the human-labelled subset when available (primary if at least 20 human-labelled DEESC with windows). Also the paired post-30 minus pre-30 comparison (as H7b).
- **H9 (platform/era contrast; exploratory, no directional claim):** mean |z| of the tweets versus mean |z| of the Truth Social war-period keyword posts with tick windows (`human_labels_191.csv`, same scaling), two-sided permutation test. The comparison is confounded by the war state and cannot isolate the platform; it will be reported as descriptive.
- **Power statement:** with about 150–250 events with valid windows the coefficient of N_c will be estimated with a standard error of roughly 0.4–0.6 in |z| units; effects below about 1.0–1.5 cannot be excluded. A failure to reject is therefore not evidence of absence.

## Reporting
RESULTS_TWITTER.md; code `build_frame.py`, `analysis_twitter.py`; outputs `results_twitter.json`. Deviations go into the amendments log.

## Amendments
(none)
