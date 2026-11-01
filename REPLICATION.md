# Replication package: "Does Release Timing in the LLM Software Ecosystem Respond to Accumulating Degradation?"

| Part | Folder | Entry point | Notes |
|---|---|---|---|
| Model and simulation benchmark (Sec. 3) | `retraining_rust/` | `python rust_retrain.py --out results.json` | ~6 min CPU. Reproduces the SD of the estimated RC at T=100..1000 (6.7, 4.8, 2.8, 2.1). |
| GitHub collection (RQ1, RQ2) | `retraining_rust/` | `collect_github.py` (needs `GITHUB_TOKEN`) | Collected weekly files are included in `data2/` (19 repositories + mlc-llm, ineligible). |
| RQ1/RQ2 diagnostics | `retraining_rust/` | `python diagnostics_real.py data2` | Repository-level slopes equal Table 1. Pooled estimates vary in the 3rd decimal with the bootstrap seed. |
| RQ3 as reported | `retraining_rust/` | `wildchat_drift.py`, `analyze_drift.py`, `agreement.py` | Detector validation labels (ids and labels only) in `*.json`, `human_labeling/`. |
| RQ3 snapshot design (added) | `wildchat_rq3/` | `./run_all.sh` | Same-week GPT-3.5 vs GPT-4 snapshot contrast and same-cutoff placebo; uses the original detector patterns (`detectors.py`). Downloads WildChat-1M (~3 GB). |

Requirements: Python 3, numpy, scipy, pandas, pyarrow, statsmodels, scikit-learn, requests.
No conversation text is stored. The human-labelling workbook and the blinded labelling sheet contain text and are not distributed.
`wildchat_rq3/results.txt` and `placebo_results.txt` are outputs of the included code.
