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
