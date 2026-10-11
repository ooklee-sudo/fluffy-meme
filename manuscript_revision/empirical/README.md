# Empirical check of P5 and P7 on public GH Archive data

Reproduce:
1. `cat hours.txt | xargs -P4 -n1 ./hour.sh` streams GH Archive (2025-09-01 to 2025-09-14), keeps PR-closed, review and inline-review-comment events, and writes one jsonl per hour to `/tmp/gha/out` (paths are hard-coded; edit if needed).
2. `python3 analysis.py` classifies PRs, builds PR-level variables, and runs the main within-repo regressions (`results_main.txt`).
3. `python3 analysis2.py` runs the robustness checks (`results_robustness.txt`).

Needs: python3, pandas, numpy, pyarrow, statsmodels; network access to data.gharchive.org.
Note: GH Archive payloads from about 2025-10 onward no longer carry PR size or author fields, so the window had to precede that change.

## Replication across windows
`hour2.sh <hour> <outdir>` extracts any window (`hours.txt`: Sep 1-14; `hours_w2.txt`: Aug 1-14; `hours_w3.txt`: Sep 15-28). `analysis.py` reads `GHA_OUT`, `GHA_HOURS`, `GHA_START` and `GHA_PRS` from the environment, so run it once per window (one at a time: two at once exhausted 15 GB of memory). `analysis3.py` then prints the replication table (`results_replication.txt`).

## Self-admitted debt markers
`satd/count.py` streams AIDev v3 `pr_commit_details.parquet` (download from huggingface.co/datasets/hao-li/AIDev, tag v3, to `/tmp/aidev_v3`) and counts markers in added lines of code files; `satd/analyze.py` produces `satd/results.txt`.
