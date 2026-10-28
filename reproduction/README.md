# Reproduction of Tables 4–5 (public data)

Pipeline: `fetch_data.py DATA` → `score_tasks.py DATA DATA/scores.jsonl` → `reproduce_tables.py DATA DATA/scores.jsonl OUT` → `make_tables.py OUT/summary.json tables.md`.
Precomputed LLM scores are in `results/task_scores_claude-haiku-5.5.jsonl` (17,358 unique O*NET task statements; temperature 0), so steps 1–2 can be skipped:
copy that file to `DATA/scores.jsonl` after running `fetch_data.py`.

Choices made here because the manuscript does not specify them (the main reasons the numbers differ from the manuscript):
- Scoring model and prompt wording (rubric text follows Appendix A; the model is `anthropic/claude-haiku-5.5` via OpenRouter).
- The language-model-exposure control is our own 0–2 text-work rubric (correlation with visual exposure 0.12 versus 0.27 reported in the manuscript).
- ISCO-3 exposure = mean score over the pooled unique task statements of all O*NET-SOC occupations linked by the ESCO crosswalk (three-digit prefix).
- Standardization over the 96 occupations; per-year OLS with country fixed effects; standard errors clustered by ISCO-3 (statsmodels, CR1);
  randomization p from 5,000 permutations of exposure across occupations; pre-trend deviation from a joint stacked model.

Not reproduced: Canadian series, human coding agreement (κ), rule-based score, Tables 1–3 and 6 beyond the acquisition inputs
(the Eurostat acquisition rates 9.6 / 36.2 / 2.1 percent and the Table 2 sector shares were checked against `isoc_eb_ai` / `isoc_eb_ain2` and match).
