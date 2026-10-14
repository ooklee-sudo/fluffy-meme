# Pre-registration (exploratory): stock reaction to LLM releases by listed developers (generalization test)

Written 2026-10-14 BEFORE any stock price was downloaded or related to a release date. Already seen: the release list (llm/llm_releases.csv) and developer counts, nothing about prices.

## Idea
Like a head of state's post, a company's model release is an act whose timing the actor controls. If the information-theoretic/event-study framing generalizes, the developer's stock should move (in magnitude) on release days more than on ordinary days.

## Events
Rows of llm_releases.csv with a full date (day precision) from 2023-01-01, whose developer string maps to a listed company by this fixed table: Google, Google DeepMind -> GOOGL; Meta, Meta AI -> META; Alibaba, Alibaba Cloud -> BABA; Microsoft -> MSFT; Nvidia -> NVDA; Baidu -> BIDU; Amazon -> AMZN; Xiaomi -> 1810.HK; Tencent -> 0700.HK. Unlisted developers (OpenAI, Anthropic, DeepSeek, Mistral and others) are excluded: no own stock exists. Multiple releases by one firm within 3 trading days count as one event (the first). Release day = the listed date; the first trading day on or after it is day 0.
Expected n is about 25–35 events, so power is low: with a 2-day abnormal-return SD near 3%, the standard error of the mean is about 0.55 percentage points.

## Data
Yahoo Finance daily adjusted closes via the public chart endpoint, 2022-01-01 to 2026-10-14, for each stock and its market index (S&P 500 for US-listed stocks including BABA and BIDU; Hang Seng for 1810.HK and 0700.HK). Intraday data are not used: exact release times are not in the list.

## Measures
Market model r_stock = a + b r_index estimated on trading days [-250, -30] before day 0 (at least 120 days required). Abnormal return AR_t = r_stock - a - b r_index. CAR[0,1] = AR_0 + AR_1 (two days, because the release time of day and time zone are unknown). Standardized by the estimation-window residual SD times sqrt(2): SCAR.
Magnitude: |SCAR|.

## Hypotheses (exploratory; Holm over the two)
H-L1 (direction): mean CAR[0,1] differs from zero (two-sided t-test with the standard error from the cross-section of events; also a Wilcoxon signed-rank test).
H-L2 (magnitude): mean |SCAR| of event windows exceeds the mean |SCAR| of same-firm random windows (one-sided permutation test, 5,000 draws of 2-day windows per event from the same firm's estimation-free calendar, excluding windows overlapping any release).

## Robustness (reported, not tested)
CAR[0] only; CAR[-1,+1]; market model on the sector (QQQ) instead of the broad index for US stocks; excluding events clustered with earnings dates (not available from this data, so noted as a limit); leave-one-firm-out.

## Interpretation rules
Both nulls -> "no detectable stock reaction in this sample; the test has low power for effects below about 1.5 percentage points". Either significant -> reported as an association; confounds named: the release day often coincides with other news, earnings, or product events, and release is partly anticipated. No causal wording. No claim about unlisted developers.

## Not allowed after prices are seen
Changing the firm mapping table, the window, the index, the clustering rule, or adding events.
