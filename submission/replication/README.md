# Replication package

**"Fewer Clicks, Not Fewer Searches: Generative AI and the Monetization of Search"**
Submitted to *Information Systems Research*. Package assembled 31 October 2026.

## 1. Overview

This package contains the code that produces every estimate in Section 5 (Tables 4–15, Figures 1–5) and the numerical examples for Propositions 8–10 (Sections 4.6–4.8). It also includes the hand-coded datasets used in the paper and the small data files that can be redistributed.

* `01_data_collection/` downloads the raw data from public sources: SEC EDGAR, Yahoo Finance, Google Trends, Wikimedia dumps, Eurostat, StatCounter and the World Bank.
* `02_analysis/` has one script per table or figure.
* `03_model/` has the numerical examples for Propositions 8, 9 and 10.

**How the code was produced (please read).** The analysis was carried out interactively in a single working session. The code was written as shell here-documents and inline Python blocks, then edited in place. The original working directory no longer exists. Every script here was **reconstructed from the session's command log**: the final version of each file was rebuilt by replaying, in order, the original file writes and every later edit (in-place `sed` substitutions, Python string replacements, appends). Inline analysis blocks became named scripts. The statistical code is otherwise unchanged. We made only these edits:

1. File paths now point to package folders (`data/raw`, `data/derived`, `output`) instead of a scratch directory.
2. The contact string in HTTP User-Agent headers is now a placeholder, `ResearchBot/1.0 (contact: REPLACE_WITH_YOUR_EMAIL)`. SEC EDGAR and Wikimedia require a real contact address, so replace it before collecting data.
3. Two scripts that were copies of each other with different language lists (`wiki_extra.py`, `wiki_eu.py`) are merged behind a command-line argument.
4. Where a session block computed several tables, it is split into one script per table. The code was not changed.
5. A docstring was added to each script.
6. The figures were originally drawn in the manuscript editor. The `f*.py` scripts rebuild exactly the plotted series, which were computed in the session, and draw them with matplotlib. The matplotlib plotting code is new.

Exploratory calls are omitted: endpoint probes, `ls`/`tail` checks, and a failed first version of the SEC scraper. A Stack Exchange data script (`so.py`) is also omitted: the API throttled us, and **no Stack Exchange data are used in the paper**. The Stack Overflow evidence in Table 1 is from published work.

## 2. Software

* Python 3.13. Package versions used in the session are in `requirements.txt`: pandas 3.0.5, numpy 2.5.3, statsmodels 0.15.0, scipy 1.18.1, requests 2.34.2, pytrends 4.9.2, matplotlib 3.11.2.
* Install with `pip install -r requirements.txt`. The estimation code has no other dependencies.
* Scripts locate the package root from their own path, so they can be run from any directory. `run_t04c.sh` and `run_all.sh` assume the package root is the working directory.

## 3. Data sources

All sources were accessed on **30 October 2026** (UTC).

| Source | What | Access | Script | Redistributed here? |
| --- | --- | --- | --- | --- |
| Yahoo Finance chart API | Daily adjusted closes: GOOGL, META, SPY, QQQ, BIDU, 035420.KS, ^KS11, MSFT, AMZN, 2021-01-04 to 2026-10-30 | `https://query1.finance.yahoo.com/v8/finance/chart/<ticker>` | `01_prices_yahoo.py` | No (terms of use). Re-download. |
| SEC EDGAR, Alphabet (CIK 1652044) | Form 8-K Item 2.02, Exhibit 99.1: "Google Search & other" revenue. Forms 10-Q: paid clicks and cost-per-click | `https://data.sec.gov/submissions/CIK0001652044.json`, `https://www.sec.gov/Archives/edgar/data/1652044/` | `02_…`, `05_…` | Transcribed series in `data/transcribed/` |
| SEC EDGAR XBRL, Meta (CIK 1326801) | Quarterly revenue | `https://data.sec.gov/api/xbrl/companyconcept/CIK0001326801/us-gaap/<concept>.json` | `03_…` | Transcribed series in `data/transcribed/quarterly.csv` |
| SEC EDGAR, Microsoft (CIK 789019) | Search (and news) advertising revenue growth ex TAC | `https://data.sec.gov/submissions/CIK0000789019.json` | `06_…`, `06b_…` | Hand-read growth rates in `data/hand_coded/msft_search_growth.csv` |
| Google Trends (via pytrends) | Monthly interest in "how to", "what is", "weather", "near me", "ChatGPT", 51 states + US, 2019-01 to 2026-10. ChatGPT interest by state; ChatGPT topic by country | `https://trends.google.com` | `07_…`, `08_…`, `09_…` | No (re-download; values are resampled, see §7) |
| Wikimedia hourly projectviews dumps | Project-level pageviews, desktop vs. mobile web, by edition | `https://dumps.wikimedia.org/other/pageviews/` | `10_…`, `14_…` | Trust-shock extract (`data/trust/hours.csv`, 1.7 MB) only. Monthly 2019–2026 extracts must be re-downloaded. |
| Eurostat | `isoc_ai_iaiu` (generative AI use, 2025); `isoc_ci_ifp_fu` (daily internet use, 2022) | `https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/<table>` | `11_eurostat.py` | Values used: `data/transcribed/eurostat_*.csv` |
| StatCounter Global Stats | Search engine market share, monthly: worldwide desktop/mobile and US all devices (2019-01 to 2026-09); 2022 home-market shares for 8 countries | `https://gs.statcounter.com/search-engine-market-share/` | `12_statcounter.py` | Bing series used: `data/transcribed/sc_desktop.csv`, `sc_us.csv` (CC BY-SA, attribution: StatCounter) |
| World Bank WDI API | 2023 GDP per capita, internet users (%), population | `https://api.worldbank.org/v2/country/all/indicator/<id>?date=2023` | `13_worldbank_covariates.py` | No (re-download; small and fast) |
| Company announcements, trade press, annual reports, Google help pages | AI-format launch dates of 17 search engines; 2022 legacy search revenue; Google AI Overviews / AI Mode rollout by country; AI Overviews language cohorts; event dates | Sources cited in Tables 5, 10, 13, 14 and Section 5.1 of the paper | hand-coded | Yes: `data/hand_coded/` |

The Wikimedia REST pageviews API returned HTTP 429 (rate limited) from our environment. All Wikipedia data therefore come from the hourly dump files, sampling a few hours per month or per day, as described in the paper.

## 4. Folder structure

```
replication/
├── README.md, requirements.txt, run_all.sh
├── 01_data_collection/   01–14: download and build raw/derived data (network)
├── 02_analysis/          t04a–t15a: tables; f1–f5: figures; run_t04c.sh: Test C specifications
├── 03_model/             prop8_numerical_check.py, prop9_numerical_example.py, prop10_trust_traps.py
├── tools/use_transcribed_data.py   copies data/transcribed/* to where the analysis expects it
├── data/
│   ├── hand_coded/   hand-collected datasets (CSV), identical to the literals in the scripts
│   ├── transcribed/  small series transcribed from the printed session output (see §6)
│   ├── trust/        trust-shock data and the session's original outputs
│   ├── raw/          (empty) filled by 01_data_collection
│   └── derived/      (empty) filled by 01_data_collection/04, 13 and by the analysis scripts
└── output/           (empty) tables' CSV outputs and figures
```

`data/hand_coded/`:

* `event_dates.csv`: event-study events and types (Table 5).
* `bing_events.csv`: Bing announcements (Section 5.6).
* `msft_search_growth.csv`: Microsoft search ad growth, read from 10-Q text.
* `search_engines_ai_formats.csv`: 17 engines, with 2022 share, summary month, full-answer month and in-house model indicator (Table 10).
* `legacy_search_revenue_2022.csv`: Table 13.
* `google_rollout_by_country.csv`: AI Overviews and AI Mode months for 49 countries, with EU/EEA, English and regulatory-dispute indicators (Table 14).
* `aio_rollout_wikipedia_cohorts.csv`: Test C cohorts.
* `wiki_edition_chatgpt_interest.csv`: Test B worldwide treatment.
* `eurostat_edition_country_map.csv`: Test B edition-to-country mapping.
* `manual_corrections.csv`: the one hand-read 10-Q value.

The analysis scripts contain these data as literals, exactly as in the session. The CSVs are provided for inspection and reuse.

## 5. Scripts and paper exhibits

Table numbers follow the submitted manuscript. Tables 1, 2 (Table A), 3 and 16 are literature or model summaries and need no code.

| Exhibit | Content | Script(s) | Inputs |
| --- | --- | --- | --- |
| Table 4, Test A | U.S. states, Google Trends DiD | `02_analysis/t04a_test_a_google_trends_states.py` | `raw/trends/`, `raw/chatgpt_by_state.csv` |
| Table 4, Test B | 24 European editions × Eurostat AI use | `t04b_test_b_eurostat_wikipedia.py` | `raw/wiki_hours*.csv`, Eurostat CSVs |
| Table 4, Test B (robustness) | 22 editions worldwide × Google Trends; trend checks | `t04b2_test_b_worldwide_trends.py` | `raw/wiki_hours.csv`, `raw/chatgpt_topic_by_country.csv` |
| Table 4, Test C | Callaway–Sant'Anna, AI Overviews launch | `t04c_test_c_callaway_santanna.py` via `run_t04c.sh` | `raw/wiki_hours.csv`, `raw/wiki_hours_extra.csv` |
| Table 5 | Event study, CAR[0,+1] | `t05_event_study.py` (+ `t05b_event_study_robustness.py`) | `raw/prices.csv` |
| Table 6 | Quarterly regressions (cols 1–3) | `t06_quarterly_regressions.py` | `derived/quarterly.csv` |
| Table 7 | Placebo break dates | `t07_placebo_breaks.py` (g_M×Post, AIC); trend-k column at end of `t06_…` | `derived/quarterly.csv` |
| Table 8 | CPC vs. paid clicks | `t08_cpc_regressions.py` | `raw/clicks.csv`, `derived/quarterly.csv` |
| Table 9 | Bing share segmented trends | `t09_bing_share.py`; revenue gap and Bing event returns in text: `t09b_bing_revenue_and_events.py` | `raw/sc_desktop.csv`, `raw/sc_us.csv` (`prices.csv`, `quarterly.csv`) |
| Table 10 | AI formats of 17 search engines | `t10_engine_formats.py` | hand-coded (in script) |
| Table 11 | Spearman correlations, share vs. timing | `t11_spearman_share_timing.py` | `derived/firm_panel.csv` |
| Table 12 | Prop. 9 regressions (share, share², in-house model) | `t12_prop9_regressions.py` | `derived/firm_panel.csv` |
| Table 13 | Legacy search revenue 2022; Spearman and log-revenue regressions (text) | `t13_legacy_revenue.py` | `derived/firm_panel.csv` + hand-coded revenue |
| Table 14 | Google AI Mode timing, 47 countries | `t14_google_ai_mode_countries.py` | `derived/country_covariates.csv` (from `01_…/13_worldbank_covariates.py`) |
| Table 15 | Trust shock, triple difference | `t15_trust_shock.py` (preliminary all-edition version: `t15a_…`) | `data/trust/hours.csv` |
| Figure 1 | AI Overviews event study (desktop, all platforms) | `f1_aio_event_study.py` | `output/cs_es_{desktop,all}.csv` from `run_t04c.sh` |
| Figure 2 | Search vs. Meta revenue growth | `f2_quarterly_growth.py` | `derived/quarterly.csv` |
| Figure 3 | Paid clicks and CPC growth | `f3_paid_clicks_cpc.py` | `derived/clicks_panel.csv` (from `t08`) |
| Figure 4 | Bing market share | `f4_bing_share.py` | `raw/sc_desktop.csv`, `raw/sc_us.csv` |
| Figure 5 | Trust-shock gap, desktop, 7-day MA | `f5_trust_shock_gap.py` | `output/trust/gap_desktop.csv` (from `t15`) |
| Prop. 8 (Lemma, threshold) | Numerical check of the closed forms | `03_model/prop8_numerical_check.py` | none |
| Prop. 9 | Numerical example (Section 4.7) | `03_model/prop9_numerical_example.py` | none |
| Prop. 10 | Trust-trap equilibria and hysteresis (Section 4.8) | `03_model/prop10_trust_traps.py` | none |

Each script's docstring states which printed lines correspond to which table cells. Scripts print results to the console; `run_all.sh` saves them to `logs/`.

## 6. Run order and runtimes

```
pip install -r requirements.txt
# (a) collect data (network; edit the contact placeholder first), then
bash run_all.sh --collect
# (b) or, without collecting anything, run what the shipped data allow:
python3 tools/use_transcribed_data.py
python3 02_analysis/t06_quarterly_regressions.py   # etc.: t06–t13, t15, t15a, f2–f5, 03_model/*
```

Dependencies between steps:

* `04_build_quarterly` must run after `02` and `03`.
* `t08` must run before `f3`.
* `t10` must run before `t11`, `t12` and `t13`.
* `13_worldbank_covariates` must run before `t14`.
* `run_t04c.sh` must run before `f1`.
* `t15` must run before `f5`.

Approximate runtimes on a laptop or small cloud VM:

| Step | Time |
| --- | --- |
| Prices, SEC 8-K/10-Q/XBRL, Eurostat, StatCounter, World Bank | under 2 minutes each |
| Google Trends, 52 geographies | 10–30 minutes (rate-limited; retries with back-off; resumable) |
| Wikimedia monthly dumps (`10_…`, about 370 files per language set × 3 sets) | roughly 5–30 minutes per set, depending on the dump server |
| Wikimedia trust-shock dumps (`14_…`, 976 files) | about 10–15 minutes |
| All regressions except Test C | seconds each (`t15`: about 30 s; `t15a`: about 10 s) |
| Test C (`run_t04c.sh`, 7 specifications × 499 bootstrap draws) | several minutes per specification |
| `03_model/*` | seconds |

## 7. Verification performed when assembling the package

* Every `.py` file passes `python3 -m py_compile`.
* **Run offline on the shipped data and checked against the session output:**
  * `t15_trust_shock.py` reproduces `data/trust/results.csv` byte for byte. Its `gap_desktop.csv` is identical to the session's.
  * Table 15 and the Figure 5 period means match the paper.
  * `03_model/*` reproduce the numbers quoted in Sections 4.6–4.8.
* **Run with `tools/use_transcribed_data.py`:**
  * `t08`, `t09`, `t10`–`t13` and `f2`–`f5` reproduce the session output exactly.
  * `t06`/`t07` reproduce the key Table 6 coefficients (g_M, k, g_M × Post) and their standard errors to three decimals. Other coefficients (intercept, ATT, COVID, Post) differ by less than 0.06. Some Table 7 entries differ in the third decimal (2021Q1: −0.362 vs. −0.366; AIC ±0.1). The cause is that Meta growth for 2019Q4–2020Q3 is available only rounded to 0.1 in the transcription (see §8.5). With freshly collected data (`01_…/02`–`04`), the session's code produced the published values.
* `t14_google_ai_mode_countries.py` reproduced Table 14 exactly after a fresh World Bank download (31 Oct 2026). The downloaded files are not shipped.
* **Not re-run:** Test A, Test B, Test C (Figure 1), Table 5 and Table 9b need data that are not redistributed (Google Trends, Wikimedia monthly extracts, Yahoo prices). Re-downloading takes longer than allowed when the package was assembled. Their code is the session code, which produced the published numbers.

## 8. Known caveats

1. **Reconstruction.** Scripts were rebuilt from the session log (§1). Each rebuilt script's final text is the last text that ran in the session, apart from the changes listed in §1. Where a figure or table was produced by an inline block, that block is now the named script.
2. **Google Trends is sampled and re-normalized** on each request. Re-downloading gives somewhat different indices, so Test A and the worldwide robustness of Test B will not reproduce to the last digit. The service is also rate-limited (HTTP 429). The script retries and can be restarted.
3. **Wikimedia sampling.** Monthly series use four hours per month (days 5 and 19 at 08:00 and 20:00 UTC). In the original run, the first months of 2019 for the main 22 editions were collected on a denser grid (days 5/12/19/26 × 02/08/14/20 UTC) before the grid was reduced. Re-collection with the shipped script uses the four-hour grid throughout, which may shift Test B (worldwide) and Test C estimates slightly. The Wikimedia REST API was rate-limited, so dumps are used. Pre-May-2025 dumps include traffic that Wikimedia later reclassified as automated.
4. **Hand-read values.**
   * The 2022-06-30 Alphabet 10-Q could not be parsed. Paid clicks +12% and CPC 0% were read from the filing and set in `t08_cpc_regressions.py`.
   * Microsoft's growth rates in `t09b` were read from 10-Q/10-K text snippets.
   * Search-engine launch dates, 2022 revenues and Google rollout dates were compiled from company announcements, trade press, filings and archived Google help pages. The sources are cited in the paper's tables.
5. **`data/transcribed/`** contains series copied from the printed session output, because the original downloads are gone. They are provided so the analysis can run offline. They are not a substitute for the collection scripts.
   * `quarterly.csv`: Search and Meta revenue levels are exact. Search growth is recomputed exactly from levels. Meta growth is exact from 2020Q4. For 2019Q4–2020Q3 it is rounded to 0.1, because the 2018Q4–2019Q3 Meta levels were not printed (column `g_m_precision`).
   * `clicks.csv`, `search_raw.csv`: exact. The 2022Q2 clicks are blank, as in the scraper output.
   * `sc_*.csv`: only the `bing` column, 2 decimals as published by StatCounter.
   * `eurostat_*.csv`: as returned by the API.
6. **`data/trust/`.**
   * `hours.csv` is the complete trust-shock extract.
   * `results.csv` and `gap_desktop.csv` are the session outputs of `t15` and are reproduced exactly.
   * `panel_{desktop,mobile,all}.csv` and `daily_gap.csv` were written by the preliminary script `t15a` while the download was still running. They cover 55 days (2024-04-15 to 2024-06-08) rather than 106. Re-running `t15a` on the complete `hours.csv` writes 106-day versions to `output/trust/`. These preliminary files do not feed any reported number.
7. **External sources change.**
   * Yahoo adjusted prices are revised after dividends and splits. Small differences in Table 5 are possible.
   * SEC filing indexes and the World Bank WDI are updated over time.
   * StatCounter revises recent months. The paper excludes September 2026 as an outlier (`t09` uses data through August 2026; `f4` plots all months).
8. **Proposition 8 check.** The session's first attempt used a bounded scalar minimizer that failed for this objective. It is replaced by the grid search in Part 1 of `prop8_numerical_check.py`, which was also the session's own fix. The threshold printout from the first attempt is kept as Part 3.
9. **Not used:** Stack Exchange API (throttled; not in the paper); plain-keyword Google Trends "ChatGPT" by country (superseded by the topic version in `09_…`).
