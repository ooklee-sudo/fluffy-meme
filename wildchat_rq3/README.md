# Replication package: WildChat snapshot-design analysis (RQ3)

Same-week contrast of GPT-3.5 and GPT-4 snapshots with different training cutoffs (week fixed effects, template de-duplication), plus a same-cutoff placebo.

Run `./run_all.sh` (downloads WildChat-1M from Hugging Face, extracts binary per-conversation features, runs analyses). No conversation text is stored by the analysis scripts.

| File | Purpose |
|---|---|
| `extract.py` | per-shard feature extraction (correction flags v1/v2, year/product/code flags, template hash) |
| `build_all.py` | concatenates shard features |
| `design.py` | main contrast; writes `results.txt` |
| `placebo.py` | GPT-3.5 same-cutoff placebo; writes `placebo_results.txt` |
| `make_label_sheet.py`, `codebook.md`, `kappa.py` | human-labeling kit (the sheet contains text and is not distributed) |

Notes: detector patterns are the original ones (detectors.py, copied from ../retraining_rust/wildchat_drift.py). Assumed cutoffs: GPT-3.5 and gpt-4-0314 = 2021-09, gpt-4-1106 = 2023-04, gpt-4-0125 = 2023-12. GitHub collection and Bellman simulation are in ../retraining_rust.
