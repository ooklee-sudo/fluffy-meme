# Replication package: "Deference or Noise? Separating Stance Sensitivity from Instability in AI Reviewers and What It Costs"

Supplementary File S1 (code, item bank, results). Anonymized for double-blind review. It contains the item bank and its generator, the independent audit, the runner that queried the models, the analysis code and every result table in the manuscript. The raw model outputs are in Supplementary File S2.

## Contents

| Path | What it is |
|---|---|
| `bank/bank_gen.py` | Generates the 600-item bank and all 10,200 prompts (seed 2026102201). |
| `bank/audit.py` | Independent audit: re-derives every answer key from the stem text with its own parser and arithmetic; checks hashes, counts, grammar, letter balance, prompt structure. |
| `bank/out/` | `bank.json`, `prompts.jsonl`, `manifest.json` (SHA-256 of the two files). |
| `bank/review/` | Blind reviewer workbook (100-item stratified sample), the key map, and the scored review (`review_results.xlsx`); `review_packet.py`, `score_review.py`, `review_report.py` make and score them. |
| `run/main_run.py` | Runner: `plan`, `run`, `export`, `parsecheck`. Resumable; records provider, returned model id, finish reason and parser branch for every call. |
| `raw/` | Not in this file. The 176,400 raw calls (`main_run_raw.jsonl.gz`) and the run metadata are in Supplementary File S2; unzip it in this directory so that `raw/` appears next to `bank/`. |
| `analysis.py` | Estimators of Section 5.4, bootstrap, family differences, ranking, power check (`--power`). |
| `decisions.py` | Applies the fixed decision rules (Table 1 of the paper) and computes the one rank-correlation interval that needs the bootstrap draws. |
| `results/primary/` | Primary analysis (`model_metrics.csv`, `family_diffs.csv`, `sign_tests.csv`, `ranking.csv`, `decisions.json`, `rotation_checks.json`). |
| `results/robust/` | Robustness runs: missing coded as errors, one domain dropped at a time, exploratory handling of a leading ">", provider split. |
| `results/summary_by_model.csv` | One row per model: the values behind Tables 2 to 6. |
| `pilot/` | The 48-item stance-free pilot (separate items, seed 90210) and its raw outputs. |
| `freeze_manifest.json` | SHA-256 of the frozen generator, audit, runner, analysis script and bank files, with the freeze date. |
| `preregistration.md` | The analysis plan that was fixed before the main run. It was not registered with a third-party platform. |

## Reproduce

Python 3.10 or later with `numpy`, `pandas` and `openpyxl`. Commands are run from this directory.

```bash
# 1. regenerate the bank and compare with the frozen files
python bank/bank_gen.py /tmp/bank_check          # hashes must equal freeze_manifest.json / bank/out/manifest.json
python bank/audit.py bank/out                     # expect: ALL CHECKS PASSED

# 2. analysis from the raw outputs (no API access needed)
mkdir -p run/data && gunzip -k -c raw/main_run_raw.jsonl.gz > run/data/main.jsonl
python run/main_run.py parsecheck run/data/main.jsonl
python run/main_run.py export run/data/main.jsonl run/data/analysis_input.csv
python analysis.py run/data/analysis_input.csv results/primary_rerun --primary pref --missing exclude --boot 2000
PYTHONPATH=. python decisions.py run/data/analysis_input.csv results/primary_rerun

# 3. (optional) query the models again: needs access to the OpenRouter API; the 14 models are listed
#    in run/main_run.py. The original run cost about US$170 as billed.
python run/main_run.py plan bank/out
python run/main_run.py run bank/out run/data/new.jsonl --go
```

The bootstrap is seeded (20260101); step 2 reproduces the point estimates in `results/primary` (checked), and with `--boot 2000` and the fixed seed the intervals. Model outputs from hosted inference can change over time, so step 3 will not reproduce the raw file.

## Data schema

`raw/main_run_raw.jsonl.gz`: `key`, `model`, `family`, `size_rank`, `item_id`, `domain`, `tier`, `channel`, `level`, `rot`, `rep`, `letter` (parsed answer), `parser_branch`, `role` (gold, unsupported, other, or missing), `raw` (the model's text), `served_by`, `returned_model`, `finish_reason`, `temperature_sent`, `max_tokens`, `error`, `ts`.

Channels: `N` (stance-free, 5 replicates), `NEU` (neutral sentence), `ST_AGAINST` and `ST_FOR` (stance toward the unsupported or the gold option at levels `pref`, `weak`, `strong`, `disclaimer`), `ACC` (disclosed accuracy 20, 50, 80), `ROT_N` and `ROT_ST` (option letters shifted by one or two positions).

## Notes

- The long-form parser for three models and the 512/2,048-token settings are described in the paper (Section 5.3) and `run/main_run.py`.
- The answer key of the review sample (`bank/review/key_and_map.csv`) is included for verification; the workbook that reviewers saw is `reviewer_sheet.xlsx`.
