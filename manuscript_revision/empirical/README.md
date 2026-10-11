# Empirical check of P5 and P7 on public GH Archive data

Reproduce:
1. `cat hours.txt | xargs -P4 -n1 ./hour.sh` streams GH Archive (2025-09-01 to 2025-09-14), keeps PR-closed, review and inline-review-comment events, and writes one jsonl per hour to `/tmp/gha/out` (paths are hard-coded; edit if needed).
2. `python3 analysis.py` classifies PRs, builds PR-level variables, and runs the main within-repo regressions (`results_main.txt`).
3. `python3 analysis2.py` runs the robustness checks (`results_robustness.txt`).

Needs: python3, pandas, numpy, pyarrow, statsmodels; network access to data.gharchive.org.
Note: GH Archive payloads from about 2025-10 onward no longer carry PR size or author fields, so the window had to precede that change.
