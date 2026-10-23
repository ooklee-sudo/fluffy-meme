# Data and code for "Underpaid professors and world-leading firms"

Replication materials for the HSSC submission on academic pay stagnation and the flow of research talent into Korean industry.

The study is descriptive and uses only published aggregate figures. There are no individual-level or restricted data, and nothing was estimated beyond the arithmetic below.

## Files

| File | Manuscript item | Contents |
| --- | --- | --- |
| `data/table1_academic_pay_rd.csv` | Table 1, Fig. 1 | Full-professor salary (private universities), business R&D, CPI |
| `data/table2_pay_comparison.csv` | Table 2, Fig. 2 | Professor, large-firm employee and executive pay; sample sizes |
| `data/researchers.csv` | Results, "Growth of corporate research" | Researchers by sector, 2020 and 2024 |
| `data/hbm_share_2026q2.csv` | Results, "Market leadership" | HBM revenue shares |
| `reproduce.py` | all derived numbers | Recomputes every derived figure quoted in the text |

Run `python reproduce.py` (standard library only).

## Variable definitions

- `professor_salary_nominal_krw_million`: average annual salary of full professors at private four-year universities, Ministry of Education figures as reported in the press (KRW million, nominal). Empty = no figure published.
- `business_rd_nominal_krw_trillion`: business-sector R&D expenditure, national Survey of R&D (KRW trillion, nominal). The 2023 value is rounded.
- `cpi_2024_100`: CPI with 2024 = 100, chained from Statistics Korea annual inflation rates.
- `large_firm_*`: averages for listed firms among the 500 largest by sales, from CEO Score / Leaders Index analyses of business reports. Sample size varies by year (211-366), so the series are indicative, not strictly comparable. Employee averages for 2024-2025 exclude unregistered executives.
- `samsung_unregistered_exec_krw_million`: average for unregistered executives at Samsung Electronics, 2024.

## Transformations

- Real value in year t = nominal × CPI(2024) / CPI(t); indices set 2013 = 100.
- Growth rates are compound annual rates.
- Professor premium = professor pay ÷ large-firm employee pay; the executive multiple = executive pay ÷ professor pay in the same year.
- No values were interpolated. 2012/2013 are paired across years (employees 2012, professors 2013).
- Indices recomputed from the rounded CPI differ from Table 1 by at most 0.1 (e.g. 2016: 110.8 vs 110.7), because the published table used unrounded CPI values.

## Sources

Per-figure sources are given in the manuscript's Table 1/2 notes and Supplementary Table S1. Rows come from press reports of Ministry of Education data (the ministry does not publish them routinely) and press reports of CEO Score / Leaders Index analyses, so the raw data are the cited articles, not files we can redistribute. Each CSV value is a transcription of a figure in a cited source.
