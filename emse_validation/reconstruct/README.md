# Reconstruction of the ISRE-2026-4563 launch analysis (no original data available)

The original replication package, launch list and exposure coding were not available. The inputs were rebuilt from public sources, and the preregistered statistic (`../prereg/confirmatory_analysis.py`) was run on them. **Result: the original 3.4-day response was not reproduced.**

## Result (38 reconstructed launches, 999 placebo draws)

| Specification | Repos | Diff (days; + = exposed release sooner) | Placebo mean | p |
|---|---|---|---|---|
| PRIMARY: all releases, all controls | 19 | -1.43 | -0.98 | 0.57 |
| drop contaminated controls | 19 | -2.65 | -2.91 | 0.83 |
| regular releases only | 19 | -1.85 | -1.24 | 0.47 |
| regular only + drop contaminated | 19 | -3.15 | -3.20 | 0.97 |
| PRIMARY | 12 | -1.30 | -2.06 | 0.40 |
| regular releases only, share within 1 day | 12 | +5.7 pp | -6.0 pp | 0.008 |

Original paper: +3.4 days, placebo +0.9, p = 0.018 (primary); +17.5 pp within 1 day (p = 0.008).
The 12-repo row uses only repositories whose reconstructed release count is within 10% of Table 1 of the paper. Of the many cells in this table, the one with p = 0.008 is a single secondary statistic among eight; read it as noise unless it replicates.

Files: `data/result_all19.txt`, `data/result_close12.txt`.

## What this does and does not show
- It does **not** show the original result is wrong: every input differs from the original (below).
- It **does** show the result is not robust to how the inputs are built. Under three independent rebuilds of the inputs (19 repos, 12 repos, and four specifications each), no primary-style statistic is positive and significant. This is a warning for the manuscript, and it raises the value of the holdout test. Do not claim the 3.4-day result in a new submission unless it is reproduced on the original data.

## How the inputs were rebuilt and where they differ
| Input | Rebuilt from | Difference from the original |
|---|---|---|
| `releases.csv` (2,594 rows) | git tags (`fetch_releases.py`, `build_inputs.py`) | A tag is not a GitHub release. Lightweight-tag dates (most repos) are commit dates and can precede publication by days, which matters for a 1-day statistic. Prerelease flags come from tag names. Counts: 2,594 vs 2,456; close for anthropic-sdk, diffusers, TGI, lm-eval, trl, openai; far for sglang (155 vs 61), FastChat (23 vs 14), whisper.cpp (46 vs 36), autogen (102 vs 86), TensorRT-LLM (27 vs 23). |
| `launches.csv` (38 rows) | web search by a subagent | Not the original list; chosen by prominence. 22 open_weights + 6 OpenAI + 6 Anthropic + 4 Google, as in the paper. 2026 entries (9) could not be independently verified by me. OpenAI pages did not load, so some dates come from search results. Gpt-oss, Kimi K2, GLM-4.5 dates rest on Hugging Face commit history; Kimi K3 is the weights-public date. |
| `exposure.csv` | keyword rule on repo files (`code_exposure.py`) | Not two-coder. Exposed repos: open_weights 16, OpenAI 10, Anthropic 8, Google 7 (paper: 11, 6, 6, 5). Coded as of Oct 2026, not each launch date. |

## Next steps to settle it
1. **Exact release dates.** Run `fetch_releases_api.py` on a machine with a GitHub token (untested here, because the API is blocked in this session). Then rerun `python ../prereg/confirmatory_analysis.py releases_api.csv data/launches.csv data/exposure.csv`. If the result stays null, tag dating was not the cause.
2. **Original data.** If any of the original launch list, exposure coding or weekly aggregates can be found (earlier sessions, collaborators, the journal's submission files in ScholarOne), use them instead; that is the only way to test reproducibility proper.
3. **Sensitivity.** Rerun with each of: only annotated-tag repos, a different 28-day truncation, and exposure by the paper's counts (11/6/6/5) once the original coding is known.
