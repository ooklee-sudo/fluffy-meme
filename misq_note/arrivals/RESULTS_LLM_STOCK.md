# Results (exploratory): stock reaction to LLM releases by listed developers (plan: ANALYSIS_PLAN_LLM_STOCK.md; code: analysis_llm_stock.py; numbers: results_llm_stock.json, results_llm_stock_events.csv)

31 events (35 listed rows, 4 dropped by the 3-trading-day clustering rule): Alphabet/Google 9, Alibaba 8, Meta 4, Microsoft 3, Xiaomi 3, Tencent 3, Nvidia 1. Daily Yahoo prices; CAR[0,1] from a market model on the S&P 500 (Hang Seng for Hong Kong listings), estimated on days [-250,-30].

| Hypothesis | Result | p | Holm p |
|---|---|---|---|
| H-L1 direction: mean CAR[0,1] ≠ 0 | +0.40 percentage points (SE 0.68; median −0.10; 48% positive) | .55 (Wilcoxon .76) | .55 |
| H-L2 magnitude: mean abs standardized CAR above random windows | 1.11 against 0.75 (random 2-day windows of the same firms, 5,000 draws) | .008 | .015 |

**Reading.** Release days show no detectable average direction; they do show larger movements than ordinary days. A magnitude effect without a direction is the same pattern as the information-theoretic account predicts (magnitude, not the sign assigned to a message) and as the war-period posts showed for de-escalation posts, but with 31 events and a single test it is a suggestion, not a replication. Power: the standard error of the mean CAR is 0.68 points, so a direction effect below about 1.3 points is not detectable.

Robustness (reported): CAR[0] +0.06 points (p = .90); CAR[−1,+1] +0.74 (p = .32); leave-one-firm-out means range from −0.24 (without Meta) to +1.22 (without Alphabet). By firm the means differ in sign: Alphabet −1.58 (9 events), Meta +4.75 (4), Tencent +2.06 (3), Alibaba +0.18, Microsoft +0.47, Nvidia −0.49 (1), Xiaomi −0.26.

**Confounds that I think apply, not verified in this session.** The three largest or most visible events may coincide with other news: Gemini 2.0 (2025-02-05, CAR −8.4%) appears to coincide with Alphabet's earnings reaction; Qwen2.5 (listed 2025-01-26, a Sunday, day 0 = 2025-01-27) with the trading day of the DeepSeek shock; Llama 4 (listed 2025-04-05, a Saturday, day 0 = 2025-04-07) with the tariff sell-off week. Without these three, the mean CAR is +0.36 (p = .57) and the mean abs SCAR is 0.96 against 0.75 for random windows (permutation p not recomputed): the magnitude excess shrinks by about 40% but does not vanish in the point estimates. The release table has no clock times, so a release after the close of day 0 is picked up in day 1, and weekend dates map to the next Monday.

**Limits.** Only listed developers (the unlisted OpenAI, Anthropic, DeepSeek and others are about half of the 2025–26 rows and are excluded by design). The firms' release dates are heterogeneous in scale (Phi-1 to Gemini 3). Release dates come from a crowd-edited list. Several firm-level means rest on 3–4 events. This is a generalization probe, not a result for the paper's main claims.
