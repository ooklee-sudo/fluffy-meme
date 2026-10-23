# Deviation log

Entries after the freeze of 22 October 2026 (`freeze_manifest.json`). The frozen files (bank, prompts, generator, audit, `run/main_run.py`, `analysis.py`) were not modified.

## 2026-10-23: analyses added after the main run

Reason: the manuscript was redirected to a methods venue, and a reviewer-style objection (reasoning confounded with model) can be answered with within-model on/off pairs. Main-run results had been seen. Nothing here changes a main-run result.

- `extra/extra_run.py`: reasoning on/off for Haiku 4.5 (300-item stratified sample, `extra/sample300.json`, seed 2026102301), Qwen3.6-27B and Qwen3.8-27B (600 items), 11 channels per item (N x3, NEU, ST_AGAINST x4, ACC x3); one run of Gemini 3.1 Pro with all 21 channels (reasoning cannot be disabled). 2,048-token limit, the frozen long-form parser, temperature 1.0 for every call. Run order shuffled with seed 20261023.
- Model selection used a pilot of 1,450 calls (`extra/PILOT.md`): Sonnet 5.5 and Gemini 3.1 Pro cannot disable reasoning; older Qwen3 models keep emitting reasoning tokens when it is switched off; Qwen3.5 9B/27B truncate at 2,048 tokens with reasoning on (91% / 9%).
- `analysis_extra.py`: paired on/off differences (same resampled items, seed 20260101, 2,000 draws), a sensitivity analysis on items answered correctly in the reference run under both conditions, and missing-as-error. Equivalence margin for Delta s*: 0.05. No directional hypothesis.
- Cost: main run about US$170; additions US$170.56 as billed (45,600 calls, 0 unresolved errors after retrying 402 credit errors).
- Outputs: `results/extra/` (missing excluded) and `results/extra_err/` (missing as error).
