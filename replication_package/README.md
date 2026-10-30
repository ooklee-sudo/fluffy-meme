# Replication package

for *Treating LLM Accuracy as an Exposure Variable: Measurement Reliability and Null Results in Studies of Stack Overflow's Decline* (manuscript draft for Empirical Software Engineering).

Everything needed to recompute every number in the paper from the stored data is in `workdir/`. Re-collecting the data is optional and costs money (see Section 3).

## 1. Layout

| Path | Content |
|---|---|
| `workdir/` | All code and data in one flat directory (the scripts read and write files in the current directory, so run them from here). |
| `outputs/` | Console output of every analysis script, as produced when this package was assembled. |
| `requirements.txt` | Python 3.13, numpy 2.5.3, duckdb 2.0.0 (only `build_panel.py`). Everything else is the standard library. |
| `NOTICE.md` | Licences, attribution, credentials. |
| `SHA256SUMS` | Checksums of all files. |

Environment variables (both optional; in the original environment authentication was injected by a proxy): `OPENROUTER_API_KEY` for `run_*.py`, `gen_tests.py`, `validity_check.py`, `robustness_formats.py`; `SE_KEY` (Stack Exchange API key, raises the daily quota from 300 to 10,000 requests) for `fetch_*.py`, `checks_v3.py`, `feasibility_v3.py`. `fetch_weekly_api.py` takes the key file path as an argument and needs a key.

## 2. Reproducing the numbers from the stored data (no network, no cost)

```bash
cd workdir
python3 -I analysis_validity.py                       # Table 2, execution-test accuracies
python3 -I analysis_formats.py                        # Tables 4 and 5
python3 -I analysis_delta_signal.py                   # Section 4.3 variances, cost per question
python3 -I analysis_llama2.py                         # Section 4.2, Llama 2 paragraph
python3 -I analysis_volume_structure.py               # Table 6 and the half-year break
python3 -I analysis_chatgpt.py                        # Section 4.4, ChatGPT window
python3 -I analysis_releases2.py gpt-3.5              # Table 7 (GPT-3.5 columns)
python3 -I analysis_releases2.py llama-3.1-8b         # Table 7 (Llama 3.1 8B columns)
python3 -I analysis_releases.py gpt-3.5               # Table 10 (earlier specification)
python3 -I analysis_recency.py                        # Table 8
python3 -I analyze.py                                 # first pilot (Section 5.2, item 7)
python3 -I analysis_so_survey.py <survey_dir>         # Section 5.3 (needs the survey CSVs, see 3.8)
```

| Manuscript item | Script | Main inputs | Stored console output |
|---|---|---|---|
| Table 1, Table 9 (cutoffs, release dates) | none (vendor documentation, see manuscript references); notes in `model_candidates.md` | | |
| Table 2, execution tests | `analysis_validity.py` | `validity_check.json`, `results_tests_v2.json` | `outputs/analysis_validity.txt` |
| Table 3 | `validity_prompt_format.py` (needs API; see 4) | `validity_check.json`, `results_v2.jsonl` | none (see 4) |
| Table 4, Table 5 | `analysis_formats.py` | `results_v2.jsonl`, `results_formats.jsonl` | `outputs/analysis_formats.txt` |
| Section 4.3 variances | `analysis_delta_signal.py` | `results_v2.jsonl` | `outputs/analysis_delta_signal.txt` |
| Llama 2 paragraph | `analysis_llama2.py` | `results_llama2.jsonl` | `outputs/analysis_llama2.txt` |
| Table 6 | `analysis_volume_structure.py` | `checks_v3.json`, `volume_v3.json` | `outputs/analysis_volume_structure.txt` |
| ChatGPT window | `analysis_chatgpt.py` | `panel_tag_week.csv`, `results_v2.jsonl` | `outputs/analysis_chatgpt.txt` |
| Table 7 | `analysis_releases2.py` | panels, `results_v2.jsonl`, `results_formats.jsonl` | `outputs/analysis_releases_specB_*.txt` |
| Table 8 | `analysis_recency.py` | `results_windows*.jsonl`, `checks_v3.json` | `outputs/analysis_recency.txt` |
| Table 10 | `analysis_releases.py` | panels, `results_v2.jsonl` | `outputs/analysis_releases_specA_*.txt` |
| Section 5.3 | `analysis_so_survey.py`, `scan_economic_index.py` | survey CSVs; Economic Index (streamed) | `outputs/analysis_so_survey.txt` |
| First pilot | `analyze.py` | `results.json` | `outputs/analyze_pilot_v1.txt` |

All values in the manuscript were checked against these outputs. Two entries differ from the first draft and were corrected in the final manuscript: the correlation of relative decline with the 2020-2022 decline is computed on relative (not log) declines, and the recent-block accuracy of Llama 3.1 8B in Table 8 is 13.7% (SE 2.7).

## 3. Re-collecting the data (optional)

Order, approximate API cost of the runs reported in the paper (OpenRouter, as logged in the result files), and notes. Model outputs are not exactly reproducible (Section 5).

1. `fetch_v2.py` (about 120 Stack Exchange API calls) -> `questions_v2.json`. Then run `python3 -I redact_tokens.py questions_v2.json` (token-like strings occur in some posts).
2. `build_panel.py` (reads 58 Hugging Face parquet files remotely, a few minutes) -> `panel_tag_week.csv`, `panel_total_week.csv`. The dump ends in the week of 2023-01-23 although its card states 2023-06-14.
3. `fetch_weekly_api.py <key_file>` (4,750 API calls, needs a Stack Exchange key) -> `panel_api_tag_week.jsonl`.
4. `run_v2.py` then `run_v2b.py` -> `results_v2.jsonl` (stored file: 4,563 unique rows, about USD 19.9). `run_v2.py` was first run for GPT-3.5, GPT-4, GPT-4o and Llama 3.1 8B and stopped early; GPT-4 covers about 195 questions and GPT-4o about 400 (the first 20 tags, 20 questions each); `run_v2b.py` completed GPT-3.5 and Llama 3.1 8B for all 2,000 rows. Both are resumable.
5. `robustness_formats.py` -> `results_formats.jsonl` (5,209 rows, USD 9.81).
6. `fetch_windows.py` -> `questions_windows.json` (then `redact_tokens.py`); `run_windows.py` -> `results_windows.jsonl` (USD 7.94); `run_windows_control.py` -> `results_windows_control.jsonl` (USD 1.98).
7. `gen_tests.py` -> `tests_v2.json`; `run_tests.py` -> `results_tests_v2.json`.
8. `validity_check.py` -> `validity_check.json` (USD 3.00). `validity_prompt_format.py` (about USD 0.9).
9. `checks_v3.py`, `feasibility_v3.py` -> `checks_v3.json`, `volume_v3.json` (Stack Exchange API counts used in Table 6).
10. Llama 2 (optional, needs a GPU): serve the two models with vLLM and run `run_llama2.py <pod_id> <key_file>`. We used a rented A100 80GB with the image `vllm/vllm-openai:latest` (the responses report vLLM 0.32.0) and one container running two servers:
    `python3 -m vllm.entrypoints.openai.api_server --model NousResearch/Llama-2-13b-chat-hf --served-model-name llama2-13b --port 8000 --api-key <KEY> --dtype float16 --max-model-len 4096 --gpu-memory-utilization 0.48`
    `python3 -m vllm.entrypoints.openai.api_server --model NousResearch/Llama-2-7b-chat-hf --served-model-name llama2-7b --port 8001 --api-key <KEY> --dtype float16 --max-model-len 4096 --gpu-memory-utilization 0.38`
    Weights come from a community mirror (the original Meta repositories are gated). `run_llama2.py` sends requests through the provider's HTTPS proxy URL; the proxy rejected the default Python User-Agent, so the script sets its own.
11. Survey and Economic Index (Section 5.3). Survey CSVs are Git LFS files: `https://media.githubusercontent.com/media/StackExchange/Survey/main/packages/archive/<year>/results.csv` for 2024 and 2025, `.../2026/survey_results_public.csv` for 2026; the 2023 file comes from the official 2023 data zip. Save them as `r2023.csv` ... `r2026.csv` in one directory and pass it to `analysis_so_survey.py`. `scan_economic_index.py` streams the Economic Index files.

Result files cover: `results_v2.jsonl` (questions_v2, F1 prompt), `results_formats.jsonl` (F2 and F3), `results_windows*.jsonl` (recency blocks), `results_llama2.jsonl` (Llama 2, 3,955 rows including 23 duplicate rows from a restarted run; scripts keep the first row per question and model), `results_tests_v2.json` (execution tests).

## 4. Known gaps and differences from the executed code

- **Table 3 raw output.** The F1 re-run of the 80 validity questions (GPT-3.5 55.0%, GPT-4o 52.5%) was run interactively; its raw outputs were not stored. `validity_prompt_format.py` recreates the step. A re-run will give somewhat different values (two runs with the same prompt agreed on 84% of questions for GPT-3.5 and 89% for GPT-4o).
- **Code changes.** The scripts are the ones that were executed, with one change: optional environment variables for API keys (see Section 1) and the helper `redact_tokens.py` (which was applied by a one-off command during the study).
- **Access labels.** The script outputs for the release analyses print a free/paid label that came from the study design notes and was not verified; it is not used in the manuscript.
- **Superseded files.** `run_pilot.py`, `fetch_questions.py`, `questions.json`, `results.json` belong to the first pilot (top-voted questions, 500-token cap); only its headline accuracies are cited. `postcutoff_sample_v3.json` is an exploratory sample of 2025-2026 questions that is not used in the paper. The `*_summary.md` and `*_check.md` files are working notes written during the study; where they differ from the manuscript, the manuscript and the scripts in Section 2 take precedence.
- **Redaction.** Strings that look like access tokens were replaced by `[REDACTED_TOKEN]` in sampled posts and model answers.
- **Dump coverage.** Weekly counts from the Hugging Face dump and from the API differ in level; the analyses only use within-source changes.
- **Deprecation.** Model identifiers (for example `openai/gpt-4`, `openai/gpt-3.5-turbo-0613`) may be retired or rerouted by providers, so re-collection may not be possible with the same models.

## 5. Determinism

All model calls used temperature 0, yet outputs are not fully reproducible (provider routing, silent model updates, floating-point nondeterminism). The stored outputs and grades are the reference for the paper.

## 6. Citation and contact

[Citation, DOI of the archived copy and contact to be inserted by the authors.]
