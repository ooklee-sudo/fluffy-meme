# Semiconductor channel (SOX) for the tariff/trade tweets (plan: ANALYSIS_PLAN_TARIFF.md, Amendment 2; code: analysis_sox.py; output: results_sox.json)

Design (registered before any SOX return was computed): daily abnormal return A = r_SOX − β̂·r_SPX (β̂ from the 250 trading days before); reaction day = next regular session for tweets outside regular hours; tweets published during 09:30–16:00 ET are excluded; directional A = +A for de-escalation, −A for escalation; one observation per (reaction day, class); one-sided Wilcoxon; Holm over H13 and H13b.

Sample: 182 kept tweets with agreed model labels; 41 were published in regular hours (excluded), 58 before the open, 83 after the close or on non-trading days; 141 usable events (74 de-escalation, 67 escalation); 63 of them in the China subset.

| Test | (day, class) obs / events | mean directional A | median | one-sided Wilcoxon p | sign-flip p | Holm |
|---|---|---|---|---|---|---|
| H13 China subset | 51 / 63 | +0.14% | +0.03% | 0.155 | 0.094 | 0.31 |
| H13b all tariff tweets | 120 / 141 | +0.02% | −0.09% | 0.49 | 0.41 | 0.49 |
H13c (semiconductor directional A minus S&P directional return, paired): −0.11 (China, p = 0.77) and −0.09 (all, p = 0.88): the semiconductor channel is not larger than the index response.
By class in the China subset: de-escalation +0.10% (36 observations), escalation +0.24% (15).

**Decision:** neither H13 nor H13b is supported (Wilcoxon p = 0.155, 0.49). Under the contingency in the plan (tick basket only if p < 0.10), no tick-level semiconductor basket is built.

Exploratory (outcomes of the Truth Social sample were already known): hourly SOX versus S&P 500 bars, 36 tariff signal posts of 2025–2026 (agreed labels), two-hour directional abnormal return +0.03% (median −0.12%; one-sided p = 0.69); directional SOX return +0.26% against +0.13% for the S&P 500; estimated hourly β = 1.81.

Limits: daily returns contain the whole overnight and session news flow; 51 observations in the China subset give little power; the model labels are unvalidated by humans; the first-day reaction excludes in-session tweets.
