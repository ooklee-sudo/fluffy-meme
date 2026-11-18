# Replication package

**When Should the Firm Take the Task Back? Error Dynamics and the Economics of Monitoring Autonomous AI Agents**

This package contains the code, run-level results and analysis outputs for every table and figure in the manuscript.
All numbers in the manuscript are read from the JSON outputs listed below.

## Contents

| Folder / file | What it contains |
|---|---|
| `extract_events.py`, `pilot_analysis.py`, `hawkes_re.py` | Observational study (Section 5.1, Table 1) on public SWE-agent trajectories |
| `pilot_results.json`, `hawkes_re_results*.json` | Outputs of the observational study |
| `theory/` | Numerical illustrations of Propositions 1–8 and Corollary 1, derailment estimates (Figures 1 and 4, Table 4) |
| `inject/` | Study 1: fault-injection experiment on τ²-bench (customer service), runner, analysis, run-level results |
| `inject_code/` | Study 2: fault-injection experiment on BugsInPy (code repair), runner, analysis inputs, run-level results |
| `figures/` | Figures 2 and 3 |

## Software

Python 3.12. Install the analysis dependencies with `pip install -r requirements.txt`.
Running the agents (not needed to reproduce the analyses) additionally requires an OpenRouter API key in `OPENROUTER_API_KEY`.

## Reproducing the analyses from the included results (no API calls)

```bash
# Table 2, Table 3 and the window analysis, Study 1 (writes inject/inject_results.json)
cd inject && python analyze.py && cd ..
# Same for Study 2 (writes inject_code/code_results.json)
cd inject && RESULTS_DIR=../inject_code/results OUT_FILE=../inject_code/code_results.json python analyze.py && cd ..
# Figures 2 and 3
python figures/figures.py
# Theory numerics: Propositions 1-5 (numerics.py, learning.py), Proposition 8 and Figure 1 (h_sens.py),
# Proposition 6 and Figure 4 (derail.py), Table 4 and Corollary 1 calibration (theta_all.py)
cd theory && python numerics.py && python learning.py && python h_sens.py && python derail.py && python theta_all.py && cd ..
```

Bootstrap intervals use fixed seeds; `analyze.py` uses 1,000 resamples (set `B=200` for a quick run).

## Reproducing the observational study (Section 5.1, Table 1)

1. Download the parquet shards of the public dataset `nebius/SWE-agent-trajectories` (Hugging Face, CC-BY-4.0).
2. `python -I extract_events.py events.parquet <shard files>` codes agent-side errors step by step.
3. `python -I pilot_analysis.py events.parquet pilot_results.json` gives the clustering, permutation and fixed-effect results.
4. `python -I hawkes_re.py events.parquet hawkes_re_results_all.json` fits the Hawkes models with and without a gamma baseline
   (multi-start; this takes several hours on a laptop).

## Re-running the experiments (API cost)

The run-level results in `inject/results/` and `inject_code/results/` are those analysed in the paper. Re-running the agents
produces new draws, because the models are sampled at temperature 0.5 and provider versions change over time.

**Study 1 (τ²-bench).** Clone `https://github.com/sierra-research/tau2-bench` at commit
`ebf990be93b594a08ed23cb8b7a9773cb9a03678` into `inject/tau2-bench`, install it with `uv sync`, then run
`python inject_run.py <model> --reps <r>` from `inject/` (see `run_all.sh`, `run_commercial.sh`). Models:
`llama8b`, `llama70b` (three repetitions), `deepseek`, `gpt61terra`, `sonnet55` (two repetitions).

**Study 2 (BugsInPy).** Clone `https://github.com/soarsmu/BugsInPy` into `inject_code/bugsinpy/work/bip`. `bugsinpy/bip_lib.py`
prepares each bug (worktree plus virtual environment) and `bip_validate.py` checks that the developer's test fails before and
passes after the fix; `valid_bugs.json` lists the outcome. `prep_meta.py` then records the fail-to-pass and pass-to-pass tests
and the failing output for the 87 valid bugs (`bug_list.json` gives the result without the projects' test files, which are not
redistributed here). Run `python code_inject.py <model> --reps 2` from `inject_code/` (see `run_all.sh`). Runs on the same bug
are serialized across processes with file locks in `RUN_DIR` (default `/tmp/bipruns`).

Approximate API cost of the runs reported in the paper: US$330 in total.

## Run-level data format

Each line of `results/<model>.jsonl` is one run with: `key` (model, task, arm, repetition), `arm` (`control`, `single` =
transient error, `blame` = misleading error, `multi` = repeated transient errors), `j` (injection index), `n_inj`, `reward`
(1 = success), `calls` (one entry per agent tool call with `injected` and `error` flags and the first characters of the error
message), and cost fields. Records with `ok = 0` are API failures that were re-run; the analysis keeps the last complete record
per key.

## Notes

- Agent errors are tool calls that the real environment rejected; injected calls are excluded from the error counts.
- Llama-3.1-8B often returns malformed tool arguments; both runners keep the first JSON object and record the event.
- The paper's manuscript files are not part of this package.
