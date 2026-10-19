# Pilot plan (Months 1–2) and go/no-go gate

Purpose: decide whether the full study is feasible before building the panel.
Nothing here uses real patent data yet; `mixture.py` is tested only on simulated data.

## Code status
| File | Status |
|---|---|
| `mixture.py` | Group-level mixture estimator, bootstrap CI, document-count-conditional null threshold. Tested on simulated data only. |
| `synthetic_test.py` | Simulation: alpha recovery and false-positive rate. Idealized (words independent, model exactly specified), so real data will be worse. |

Simulation result (1,500-word vocabulary, 3,000-document reference corpora): alpha was recovered within about 0.01 for 200-document groups, with a false-positive rate of 0.7–3% at a 99th-percentile threshold. Treat this as a unit test, not evidence about patents.

## Steps
1. **Data.** Download PatentsView pre-grant publication full text for two fields (e.g., one software-heavy, one mechanical) for 2018–latest release. Confirm current download locations on the PatentsView site; they change between releases. Check whether the USPTO bulk XML lists agent/law-firm for application publications (gate criterion c).
2. **Vocabulary and features.** Tokenize description and summary separately; keep words above a document-frequency floor; build binary occurrence matrices. Exclude claims from the primary run.
3. **Human reference.** Sample applications filed before 2022-11-30; split into reference and held-out halves. Stratify by field and applicant country.
4. **Machine reference.** Rewrite a random sample of pre-2022 applications with at least three different LLMs under three prompt types (polish, expand summary, draft from disclosure). Estimate token cost first (specification length × sample size × models) and record model names, versions, prompts, and settings. Add a machine-translation corpus from non-English-origin filings.
5. **Estimate.** Fit p (human) and q (machine); compute alpha by field × quarter for 2019–2025, with bootstrap CIs.
6. **Validate.** False-positive rate on held-out pre-2022 text, by U.S./non-U.S. and translated filings; leave-one-generator-out; partial-editing; 2019–2021 placebo.

## Gate (all must hold to proceed to Months 3–5)
- (a) Alpha is clearly above a flat pre-2022 baseline in 2023–2025 and varies by field.
- (b) False-positive rate on held-out pre-2022 text is near zero, including non-U.S. and machine-translated filings.
- (c) Agent or law-firm information is available for application publications (otherwise fall back to assignee-level units with stronger caveats).

If (a) or (b) fails, reframe as a study of the limits of detection. Record the result either way before touching outcome variables, to keep the analysis plan pre-specified.

## Open decisions
- Minimum documents per drafting-unit quarter for stable estimates (set from the pilot's bootstrap widths).
- Whether the word-occurrence model needs a richer feature set (e.g., n-grams) if independence assumptions fit poorly on real text.
- Which LLMs and drafting tools enter the machine corpus (budget-dependent).

## Machine-corpus generation (`rewrite_corpus.py`)
Seven OpenRouter models: llama-4-maverick, qwen3.8-flash, deepseek-v4.1-flash, mistral-small-2603, gemini-3.8-flash (cheap tier); gpt-6.1-sol, claude-opus-5.5 (top tier). Three prompt types per model. Defaults: 1,000 chunks per prompt per cheap model, 500 per prompt per top model.

```
export OPENROUTER_API_KEY=...            # environment only; never commit
python3 pilot/rewrite_corpus.py --input chunks.jsonl --out rewrites.jsonl --dry-run   # cost estimate
python3 pilot/rewrite_corpus.py --input chunks.jsonl --out rewrites.jsonl --budget 500
```
- Hard budget cap: each call reserves 1.5× its estimated cost and the run stops before the cap is exceeded.
- Resumable: finished (model, prompt, chunk) triples are skipped on re-run.
- `<out>.manifest.json` records models, prompts, settings, seed, and budget; each output record stores the served model name and token usage (needed for the AI-use disclosure).
- Tested offline with a fake API (`test_rewrite.py`); not yet run against the live API.
- Reasoning is requested off, but some models may ignore it; reasoning tokens would then raise cost above the estimate, which the cap still covers.

## Data access (checked 2026-10-18) and chunk extraction (`build_chunks.py`)
PatentsView bulk downloads moved to the USPTO Open Data Portal (dataset `pvpgpubtxt` for pre-grant long text, per the transition guide). Downloading now requires a USPTO.gov account with an API key; the old S3 paths return 403 from this environment, and the portal pages are not readable without a browser session. So the long-text tables have to be downloaded by the account holder.

```
python3 pilot/build_chunks.py --desc <detail_desc_text.tsv[.zip]> --meta <application_with_filing_date.tsv> \
    [--brief <brief_summary_text.tsv>] --out chunks.jsonl --n 3000
```
- Keeps applications filed 2018 through 2022-11-29, one random ~1,100-word chunk per application.
- Column names are auto-detected from common names but must be checked against the data dictionary of the release actually downloaded; tested on synthetic files only (`test_build_chunks.py`).
- Metadata (filing date) lives in a different table from the long text; join key is the application/publication id.

## Cost check for the small run (live OpenRouter prices, synthetic 1,100-word chunks)
`--n-cheap 500 --n-top 200`: 8,700 calls, estimated maximum $89 (output priced at 1.6× chunk length, so the expected actual is lower, roughly $60–70). The 1,000/500 run would be about $184 at maximum. Real figures will be recomputed by `--dry-run` on the actual chunk file.

## Data dictionary check (PVPGPUBTXT, release of 2025-12-10)
- Confirmed columns: `pg_detail_desc_text_{year}`: `pgpub_id`, `description_length`, `description_text`; `pg_brf_sum_text_{year}`: `pgpub_id`, `summary_text`; `pg_claims_{year}`: `pgpub_id`, `claim_sequence`, `claim_number`, `claim_text`, `dependent`. `build_chunks.py` defaults now match these names.
- The long-text tables carry no filing date. `build_chunks.py` therefore works without `--meta`: `pgpub_id` begins with the publication year, and anything published in or before 2022 was filed before ChatGPT, so the human corpus is safe. Filing dates (needed later for cohorts) come from the application metadata table in the same portal, whose column names still need to be checked.
- Data are current through 2025-09-30. With an 18-month publication lag, filings are complete only through roughly early 2024, so the clean post-ChatGPT window is about 16 months. Check whether a 2026 release is available before the main analysis.
- Line breaks are kept in text from 2020 on; `clean()` collapses whitespace.

## First real-data run (2021 sample, 3,000 applications)
- `build_chunks.py` on the uploaded 2021 samples produced 600 chunks (median 1,084 words, max 1,100), all with a summary-based disclosure.
- Parsing artifact found: PatentsView text glues reference numerals to neighbors ("FIG. 1shows", "device100installed"). `clean()` now splits at letter/digit boundaries so human text carries no artifact that machine rewrites would lack. The feature extractor for the mixture model should also use alphabetic tokens only.
- Run-on blocks (tables, sequence lists) are dropped (chunks over 1.5× the target length).
- `--dry-run` for the small run (500 chunks per prompt per cheap model, 200 per top model; 8,700 calls) on the real chunks: estimated maximum $72.10. The expected actual cost is lower because the estimate prices output at 1.6× chunk length.

## Detector validation on real text (validate_detector.py, seed 0)
Full tables: `validation_results.md`. Setup: 2,366 human 2021 chunks (not sources of any rewrite) split into reference/null/test; 7,423 normalized rewrites from six complete generators plus 235 from mistral; source chunks split into train/test so q never sees the chunks it is tested on.
- Human-only groups get alpha-hat ≈ 0.05 (the independence model is misspecified, so the baseline is not 0); the document-count-conditional 99th-percentile threshold keeps the false-positive rate at 1–3.3%.
- Known mixtures are recovered with attenuation: true 25% → 0.20, true 50% → 0.34. Use a calibration curve (alpha-hat → true share) before reporting levels. With 100 documents per group, a 10% share is detected 67% of the time, 5% only 18%, 25% always.
- Unseen generators: pure-AI alpha-hat 0.54–0.70 and 25% mixtures 0.17–0.22, close to the in-training reference (0.18–0.21), so the detector generalizes across generators in this test.
- **Key finding by prompt type:** text drafted or expanded by an LLM is detected almost perfectly (alpha-hat 0.93), but **LLM-polished human text is not** (0.07, indistinguishable from the human baseline). The measure identifies LLM-drafted text, not light editing. This limits what "adoption" means in the paper and should be stated in Section 5 and the limitations.
- Gate status: (b) false positives near zero holds for U.S.-style 2021 text but has not been tested on non-U.S. or machine-translated filings (no applicant-country data loaded yet); (a) prevalence above baseline in 2023–2025 is untested (needs 2023–2025 files); (c) agent/law-firm availability is still unverified.
- Caveat: this is a laboratory check on pre-2022 human text and synthetic mixtures; real post-2022 filings may differ from any of the generators.

## Prevalence by year (estimate_prevalence.py; tables in prevalence_results.md and prevalence_results_cleanvocab.md)
Samples: ~3,000 random 2021/2024/2025 applications from PatentsView long-text files; q trained on draft+expand rewrites only; raw alpha-hat mapped to a calibrated share with known synthetic mixtures.
- 2021: alpha-hat 0.019–0.020 (the human baseline); 2024: 0.017–0.018, calibrated share 0.0% (95% CI up to 0.4%); 2025: 0.025–0.027, calibrated share about 0.7–0.8% (CI 0.1–1.5%).
- By publication quartile (serial number in pgpub_id), 2025 Q4 reaches alpha-hat 0.041–0.043 versus 0.014–0.030 in other quarters: a suggestive late-2025 uptick, about 2–3% calibrated, with no confidence interval yet.
- Robustness: restricting to the 300 most frequent words, and dropping words found in fewer than 15 machine documents (removes human-only parsing artifacts such as "infig", "tofig"), leaves the picture unchanged.
- Reading: through publications of 2025, the detectable share of LLM-drafted text is very small (at most a few percent). Because of the 18-month lag, 2025 publications reflect filings up to roughly mid-2024. Gate criterion (a) is therefore not met as stated: no clear prevalence above the baseline yet. 2026 publications (filings through about spring 2025) are the next test.

## Raw weekly XML (USPTO ODP dataset `appxml`)
Weekly files `ipaYYMMDD.zip` (150–260 MB each), available through 2026-10-15. Tools: `peek_xml.py` (cut the first MB to inspect real structure), `xml_to_tsv.py` (parse and sample; adds filing date, applicant countries, agent/law firm, CPC). The parser follows the DTD as recalled and is tested on synthetic XML only; verify with a real file first.
Plan: download one weekly file each for 2025-04-10, 2025-10-09, 2026-01-08, 2026-04-09, 2026-06-11, 2026-08-06, 2026-10-08 (post-period) and 2021-04-08, 2022-04-07 (baseline). Raw-XML text can differ in formatting from PatentsView text, so refit p on baseline XML weeks before comparing with later weeks.

### Weekly XML structure check (ipa261008, DTD v4.6)
Confirmed: publication number/date, filing date, appl-type, CPC, title, applicants (us-parties/us-applicants/us-applicant; individuals have no orgname), inventors, description paragraphs. The first application had **no agents element**: law-firm information is probably absent from application publications (as with PatentsView). `xml_to_tsv.py` now prints the share of applications with agents; if it is near zero, the assignee × law-firm drafting unit is not buildable from publications alone and the design needs an alternative (assignee-level units, or law firms from granted-patent XML).

### Weekly XML statistics (ipa261008, 8,898 usable utility applications; 1,000 sampled)
- Agents / law firm: **0.0%** → gate criterion (c) fails for application publications; the assignee × law-firm drafting unit cannot be built from them. Options: applicant-level (company) units; or law firms from granted-patent XML via the publication-to-grant crosswalk (only for applications already granted, with selection).
- Applicant is an organization: 94.0%; assignee element present: 36.8% (use applicant organization as the unit name).
- Any non-US applicant: **55.2%** → enough volume to test false positives by applicant country (gate criterion (b)), once a pre-2022 XML baseline week (ipa210408) is available.
- CPC 100%; filing date 100%.

## First weekly-XML analysis (1,000 docs per week; first version of analyze_weeks.py)
- Baseline false positives differ strongly by applicant group: with one pooled null threshold (0.030 for 100-doc groups) the false-positive rate was 75.7% for US-only groups versus 2.0% for non-US groups (baseline alpha-hat 0.046 vs 0.007). A single pooled human model is not valid across groups; **always compare within group**. This fails gate criterion (b) for pooled use and motivates stratification (or group-specific human models).
- Within-group comparison, alpha-hat 2021 baseline -> 2026 weeks: US 0.046 -> 0.073 / 0.100 / 0.097 (Jan/Apr/Oct); non-US 0.007 -> 0.031 / 0.038 / 0.035. Pooled calibrated shares 3.6% / 6.2% / 5.4%. Baseline groups had only ~150 documents, so these differences were not yet tested.
- By filing quarter (mixed groups, 75–450 docs each) alpha-hat fluctuates between 0.02 and 0.12 with no clean monotone trend.
- analyze_weeks.py now scores the baseline by 5-fold cross-fitting (all 990 documents), reports within-group differences with bootstrap intervals, and writes UTF-8.

## Weekly XML analysis v2 (cross-fitted baseline; results in weeks_results_v1.md)
All nine within-group differences between the 2026 weeks and the 2021-04 baseline are positive with 95% intervals excluding zero (pooled +0.025 to +0.049 in alpha-hat; calibrated share about 3–6% pooled, 6–9.5% for US applicants, 1–2% for non-US). So gate (a) is met weakly: a statistically detectable but modest rise in LLM-drafted-like text.
Cautions: (1) one baseline week only, so technology-mix drift is uncontrolled: need placebo with a second pre-2022 week (should give ≈0) and CPC-stratified comparison; (2) baseline US and non-US groups differ (0.036 vs 0.008): always stratify; (3) the 99th-percentile noise level for a 100-document group is 0.090 (US) and 0.030 (non-US), so a company-level binary adoption flag from ~100 documents is not reliable: use larger groups or continuous intensity; (4) calibrated share is "share resembling our generic-prompt machine drafts", not a measured adoption rate.

## Placebo passed (weeks_results_v2.md)
The 2022-04 publication week (pre-ChatGPT) shows no difference from the 2021-04 baseline in any group (all, US, non-US: differences −0.004, −0.013, +0.006; every 95% interval contains 0; calibrated share 0), while all three 2026 weeks keep significant positive differences (+0.024 to +0.064). Gate (a) is met: a real but modest rise (pooled calibrated share ≈3–6%; US ≈6–9%; non-US ≈1–2%). Still open: technology-mix control (CPC-stratified comparison) and firm-level feasibility (distribution of documents per applicant).

## Applicant concentration (ipa261008: 8,902 utility applications in one week)
3,875 distinct applicant organizations plus 486 individual applicants (5.5% of applications). Organizations with ≥5 applications that week: 262 (41.9% of applications); ≥10: 110 (31.1%); ≥20: 38 (20.4%); ≥50: 14 (13.3%). Top: TSMC 210, Samsung Electronics 178, Qualcomm 99, Samsung Display 78, Hyundai 77, Canon 76, Dell 72, Toyota 69, Xiaomi 59 (many large applicants are non-US).
Reading: roughly 110–260 organizations have ≥500–1,300 applications a year, so firm-level panels are possible only for a few hundred large firms. A group-level estimate needs ~100 documents per unit-period to detect shares of ~10% reliably, so quarterly firm-level treatment (65–130 documents per quarter for those firms) is noisy and attenuated, and the pool of firms is small for a staggered DID. Field-level (CPC × period), country-level, and firm-size-level analyses have far more documents per cell. Large non-US applicants (translated text) show low detected shares (1–2%), so LLM use there may be under-detected.
Options: (A) measurement-and-prevalence paper first (RQ1 by year, field, country, firm size, using many weekly files); (B) field-level DID later; (C) firm-level DID restricted to the largest firms with continuous intensity.

## Chosen direction: option A (measurement and prevalence paper first)
Goal: a prevalence curve of LLM-drafted-like text in US pre-grant publications, by publication week, with breakdowns by applicant group (US/non-US), firm size (applications per week), and CPC section; each document is compared with the human model of its own stratum.
Tools: `xml_to_tsv.py` (now also writes cpc_section and org_week_count), `make_samples.py` (batch sampling of all weekly zips in a folder), `prevalence_curve.py` (baseline weeks scored out-of-fold as placebo points; optional CPC-stratified human models via `--strata group_cpc`). Tested on synthetic data only.
Weekly files for the curve (one per half-year): baseline/placebo 2021-04-08, 2021-10-07, 2022-04-07, 2022-10-06; post 2023-04-06, 2023-10-05, 2024-04-04, 2024-10-03, 2025-04-03, 2025-10-02, 2026-01-08, 2026-04-09, 2026-10-08. Already downloaded: 210408, 220407, 260108, 260409, 261008.

## Prevalence curve v1 (15 weekly samples; curve_v1.md, figures/prevalence_curve.png)
Flat through publication 2023, then rising from 2024 publications and accelerating in 2026 (calibrated share ≈ 4.0%, 3.1%, 5.0% in Jan/Apr/Oct 2026); the six pre-ChatGPT baseline weeks serve as placebo points and stay at about 0. US applicants and small firms show higher levels; the largest sector increases are in CPC G (physics/computing), A, B. Added to prevalence_curve.py: a pooled by-filing-quarter table (re-run needed). Still to do: CPC-stratified rerun (`--strata group_cpc`), by-filing-quarter curve, more weeks (denser time series), uncertainty on group differences.

## Prevalence by filing quarter (curve_v2_filing_quarter.md, figures/prevalence_by_filing_quarter.png)
Filings through 2022Q3 are flat (alpha-hat ≈ 0.02, calibrated ≈ 0); 2022Q4–2023Q1 filings are at or below baseline; a break appears with 2023Q2 filings (calibrated 1.2%) and the share rises about one percentage point per half year to ≈5% by 2025Q4. The last two quarters are based on few early-published documents. Open: CPC-stratified rerun (`--strata group_cpc`), denser weekly sampling (more weeks per half year), group-by-quarter breakdowns, and filing-quarter confidence in the late quarters.
