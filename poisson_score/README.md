# poisson_score

Reference implementation of the Poisson-Score (see `../paper/manuscript.md`, Section 3).

Event families: **P** academic punctuation/symbols, **D** discourse markers, **N** passives + nominalizations.
Score = mean Hellinger distance between binned window-count distribution and Poisson(λ̂) over families, in [0,1].
Also reported: signed index of dispersion (direction), dispersion-test p-value, and an NB-Score against a negative-binomial benchmark fitted on human text.

    pip install numpy scipy pytest
    python -m pytest tests
    python -m poisson_score.cli explain paper.txt
    python -m poisson_score.cli score corpus_dir -o scores.csv
    python -m poisson_score.cli pilot --human human_dir --synthetic llm_dir -o pilot.csv

Inputs are plain `.txt` files (one document each). Rules are heuristic regex/suffix based (no spaCy) so every counted token is auditable; a POS-tagger-based passive detector is a planned upgrade.
`pilot` fits the NB reference in-sample; split calibration/test for the real study.

## Data and analysis scripts (`scripts/`)
- `collect_human.py` — PMC open-access full text + arXiv (via ar5iv), pre-Nov-2022, random within field.
- `collect_is.py` — **Information Systems journals** (MISQ, ISR, JMIS, JAIS, CAIS, EJIS, ISJ, JSIS, JIT, I&M, DSS):
  Crossref → random sample → Unpaywall legal OA PDF → pdftotext → cleanup. Needs only an email (no API keys).
  Only papers with a legal OA copy are retrievable (MISQ/ISR are mostly closed; green-OA preprints appear as
  `submittedVersion`, so check `oa_version` in `meta.csv`). Don't redistribute the texts.
- `generate_synthetic.py` — LLM counterparts at 3 prompt levels (Anthropic/OpenAI backends via env API key); logs model, level, temperature.
- `analyze.py` — H1a logit with controls (+ optional clustered SEs) and H1b DeLong test of AUC gain over baselines.

Extra deps: `requests lxml pandas statsmodels scikit-learn` (+ `anthropic`/`openai` for generation, poppler `pdftotext`).
