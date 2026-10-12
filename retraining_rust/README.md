# Replication package (EMSE manuscript: `manuscript_emse.md`)

| Step | Script | Output |
|---|---|---|
| Model + simulation benchmark | `rust_retrain.py` | `results.json` |
| GitHub weekly bugs + releases (needs `GITHUB_TOKEN`) | `collect_github.py` | `data2/*.csv` (included) |
| RQ1/RQ2 diagnostics | `diagnostics_real.py data2` | `diagnostics_real.json` |
| WildChat features and drift tokens | `wildchat_drift.py` (downloads shards from Hugging Face) | `conv_features.csv.gz`, `weekly_tokens.pkl` (not committed, regenerate) |
| RQ3 analysis | `analyze_drift.py <dir>` | `weekly_drift.csv`, `drift_results.json` |
| Status-page snapshot (supplementary, not used in the paper) | `collect_status.py` | `data_status/` |

`estimate_real.py` (structural estimator on weekly GitHub data) is provided but not reported: H1/H2 fail, so a cost estimate is not interpretable.
Requires: Python 3, numpy, scipy, pandas, pyarrow, statsmodels, requests.


## Additional files
- `sample_corrections.py`, `correction_validation*_labels.json`, `human_labeling/answer_key.json`, `human_labeling/human_labels_from_file.json`, `agreement.py`: validation of the correction detector (stratified samples; ids and labels only, no text).
- Human labelling workbook (`human_labeling/*.xlsx`) contains conversation excerpts and is not committed.
