# Results (exploratory): are LLM release times a Poisson process? (plan: ANALYSIS_PLAN_LLM_RELEASES.md; code: parse_llm.py, analysis_llm.py; numbers: results_llm.json)

Data: Wikipedia "List of large language models", wikitext fetched 2026-10-14; 188 rows parsed, 187 with at least a month, 126 with a full date (the one unparsable date is "28 August"). Rows by year: 2018 2, 2019 3, 2020 1, 2021 8, 2022 10, 2023 24, 2024 28, 2025 33, 2026 78. Day-precision dates are almost all from 2025–2026 (33 of 33 in 2025, 78 of 78 in 2026, 14 before), so A3–A6 are effectively 2025–2026 analyses even though the windows were set earlier.

**Answer: no, not a Poisson process, and not even a Poisson process with a smoothly changing rate.**

- **A1, monthly counts 2018-06 to 2026-09 (100 months, 186 rows).** The rate rises steeply, so a constant rate is not an option; with a linear or quadratic log-trend the counts are still over-dispersed (Pearson chi2/df 1.7, p < .001; NB alpha 0.25; Poisson→NB LR p = .0001, AIC better by about 12–14).
- **A2, 2024-01 to 2026-09 (33 months, 138 rows).** Still over-dispersed with a linear trend (alpha 0.16, LR p = .004). With a quadratic trend the evidence weakens (alpha 0.10; LR one-sided p = .028; Pearson p = .059): in this short window a flexible smooth rate absorbs much of it. A2's Holm-adjusted p is .028.
- **A3, weekday (125 day-precision rows since 2023).** Mon–Sun counts 20, 35, 23, 33, 9, 1, 4; weekend share 4% against 29% expected for a homogeneous process (chi2 = 62.1, 6 df, Holm p < 1e-10). Release dates follow the business calendar.
- **A4, gaps in days, 2024–2026 (119 gaps).** Mean 7.8, variance 145, CV 1.55, 21% same-day ties. Negative binomial best (ΔAIC 0); discrete lognormal +1.1; geometric (the memoryless Poisson-process case) +22.
- **A5, per developer (≥10 day-precision releases).** Anthropic 15 releases, mean gap 41.5 days, CV 0.67; OpenAI 13, 62.3 days, CV 0.81; Google DeepMind 10, 66.9 days, CV 1.12. A CV below 1 means a given developer releases more regularly than a Poisson process would; pooling developers produces the clustered pooled series.
- **A6, clustering across developers.** The share of releases followed within 14 days by another developer's release is 0.85 observed against 0.839 under random days within the quarter (all days; permutation p = 0.34 upper) and 0.843 under weekdays only (p = 0.44). No excess cross-developer clustering is detectable; with 119 releases in 8 quarters the share is near its ceiling, so the test has little power.

## Caveats
1. The list is crowd-edited, based on notability, and densest in 2026 (78 rows in under 10 months), so the rate trend partly reflects who was editing; a trend this steep is also what real growth looks like, and we cannot separate the two.
2. Day-precision data exist only for recent years; pre-2025 entries are monthly.
3. "Release" is whatever the editor recorded; model versions of one family are separate rows.
4. All analyses are exploratory; the Holm family of three (A1 quad LR, A2 quad LR, A3) gave p = 2e-4, .028 and 5e-11.
5. The comparison with the president's posting is descriptive only. Both series show over-dispersion and the business calendar matters for releases, but the two series differ in unit (events by many developers versus posts by one person).
