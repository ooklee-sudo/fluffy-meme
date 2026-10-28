# Reproduction of Tables 3-5 and Sections 6.2, 7.1 (Canada), 7.3-7.5 (public data)

Pipeline (DATA = any working directory):
1. `python fetch_data.py DATA`  (Eurostat jvs_a_isco3_r1 and isoc_eb_ai, O*NET 29.1, ESCO->O*NET-SOC crosswalk)
2. `python score_tasks.py DATA DATA/scores.jsonl`  (LLM scores per O*NET task statement; set `SCORE_MODEL` for another scorer)
   The scores used in the manuscript are in `results/` (`task_scores_claude-haiku-5.5.jsonl`, `task_scores_gpt-5.6-luna.jsonl`); copy one to `DATA/scores.jsonl` to skip this step.
3. `python reproduce_tables.py DATA DATA/scores.jsonl OUT`  (Tables 4-5 inputs; writes `OUT/summary.json`, `OUT/exposure_by_isco3.csv`)
4. `python make_tables.py OUT/summary.json tables.md`
5. Canada: download StatCan table 14-10-0444 and the NOC 2021 v1.0 elements/structure files, extract the Canada-total "Job vacancies" rows to `DATA/cad_jv.csv`,
   then `python canada_prep.py DATA`, score the duties with `TASK_TEXTS=DATA/noc_duty_texts.json python score_tasks.py DATA DATA/noc_scores.jsonl`
   (scores in `results/noc_duty_scores_claude-haiku-5.5.jsonl`), and `python reproduce_extra.py DATA OUT` (Canada and the Section 7.4 interaction).
6. `python agreement.py SCORES_A SCORES_B agreement.json`  (agreement between two scorers)
7. `python reproduce_sections.py DATA OUT`  (Table 3, Section 6.2 correlations, sector exposure, Section 7.3 LFS employment, Section 7.5; writes `OUT/sections_summary.json`)

Choices made because the manuscript does not specify them (the main reasons the numbers differ from the original draft):
scorer and prompt wording; the language-model-exposure control is our own 0-2 text-work rubric (correlation with visual exposure 0.12);
ISCO-3 exposure = mean over pooled unique task statements of all O*NET-SOC occupations linked by the ESCO crosswalk (three-digit prefix);
standardization over occupations; per-year OLS with country fixed effects, ISCO-3 clustered standard errors (statsmodels, CR1);
randomization p from 5,000 permutations of exposure across occupations; pre-trend deviation from a joint stacked model.
Canada: 312 unit groups (all four 2022 quarters observed, 2022 total >= 1,000), NOC two-digit fixed effects, HC1 standard errors.

Section 6.2-7.5 choices: sector exposure = employment-weighted mean of one-digit ISCO exposure (2022 LFS, nine NACE sections C,F,G,H,I,J,L,M,N);
LFS growth = log(mean 2023-25 / mean 2019-21) for EU27, ages 15-74; Section 7.5 uses heteroskedasticity-robust standard errors and 258 country-sector cells.

Not reproduced: Tables 1 and 6 beyond the acquisition inputs (Table 6 follows from equation (5) and the Table 4 standard error; see manuscript),
the Census BTOS correlation (census.gov returned 403 to plain requests; the sentence was removed from the manuscript), human validation of the scores.
