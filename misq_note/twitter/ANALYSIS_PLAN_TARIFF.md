# Pre-registration: information-theoretic propositions on tariff/trade/China tweets, 2017–2021 (committed before labelling, tick download or return computation, 2026-10-14)

Same logic as ANALYSIS_PLAN_TWITTER.md (oil/Iran/energy sample, still in progress); this is a second, independent confirmatory sample with a different asset. Already seen: only the number of keyword tweets by year (937 in the frame: 2017 86, 2018 276, 2019 363, 2020 210, 2021 2; 632 after the filter below). Not seen: any price, return, label or novelty score for these tweets. Prior knowledge: the Truth Social tariff results (RESULTS_PAPER.md: hourly S&P futures; tariff escalation after April 2025 −0.35% directional, p = .09) and the oil-sample propositions.

## Frame (fixed by rule)
Original tweets (not starting with "RT @") by @realDonaldTrump, 2017-01-20 to 2021-01-08, containing (case-insensitive) tariff*, trade, duties, duty, nafta, usmca, korus, wto, dumping, steel, aluminum, aluminium, china, chinese, beijing, xi, huawei, zte, or "currency manipulat*" (`frame_tariff.csv`, 937 tweets). Exact UTC time from the snowflake id. Cluster filter: keep a tweet if at least 3 hours have passed since the previous frame tweet (632 kept). A tweet that also belongs to the oil/Iran frame stays in both analyses.

## Market data
Primary asset: Dukascopy S&P 500 index CFD (`USA500IDXUSD`; raw price/1000), mid price; price at s = last tick at or before s, valid only if at most 10 minutes old. Secondary asset: USD/CNH (`USDCNH`; raw/100000). Daily S&P 500 closes (Yahoo ^GSPC, `spx_daily.csv`) for scaling. An event needs valid prices at t−30, t and t+30 minutes.

## Measures
- |z| = |100·ln(P(t+30)/P(t))| / s30, s30 = σ_d × sqrt(30/1380), σ_d = sd (in percent) of the 60 daily S&P log returns before the tweet date; U = ln(sd of the 5 daily returns / sd of the 60); novelty N_c as in ANALYSIS_PLAN_INFO.md with a 7-day context of all original tweets (computed for the frame text only, no returns); robustness N_t.
- Directional convention: tariff escalation (ESC) → S&P down, so the directional S&P return is −r; tariff de-escalation (DEESC) → S&P up (+r). For USD/CNH: ESC → up (+), DEESC → down (−).
- Labels (two independent model instances, text only; humans on a subset): ESC = announces, threatens, imposes or celebrates tariffs, duties, quotas, trade restrictions, export or sanction measures on firms, or retaliation; criticises a trade partner in a way that signals coming trade action; demands backed by a threat of such measures. DEESC = announces or signals a trade deal or agreement, tariff reduction, pause, delay, exemption or exclusion, progress in talks, a meeting to resolve a dispute, purchase commitments by a trade partner, or relief on restrictions. MIXED = both clearly. OTHER = no implication for the course of trade policy: general statements on the economy or jobs, complaints about trade deficits without an announced action, praise of own policy, attacks on media or opponents, unrelated mentions (e.g., China outside trade), a bare link or no stated stance.

## Hypotheses (confirmatory; decision rules fixed now)
- **HI1–HI3** exactly as in ANALYSIS_PLAN_TWITTER.md (|z| on N_c, U, N_c × U; year fixed effects; clustered by UTC day; one-sided; Holm across the three at α = .05), on all kept frame tweets with valid windows (label-free).
- **H10:** among tweets with an agreed model label DEESC the mean directional 30-minute S&P return (+r) > 0; among ESC the mean (−r) > 0; one-sided Wilcoxon, α = .05; same on the human-labelled subset when available (primary if at least 20 human-labelled tweets in the class have windows); paired post-30 vs pre-30 comparison as in H7b.
- **H11 (secondary asset):** the same H10 tests for USD/CNH on the subset of tweets that mention china, chinese, beijing, xi, huawei, zte or "currency" (any case).
- **Power statement:** about 400–500 events with valid windows are expected; the standard error of the N_c coefficient is expected around 0.2–0.4 |z| units; effects below about 0.5–0.8 cannot be excluded.

## Reporting
RESULTS_TARIFF.md; code `build_frame_tariff.py`, `analysis_tariff.py`; output `results_tariff.json`. Deviations go to the amendments log. Neither positive nor negative results are suppressed.

## Amendments
(none)
