# Stage D: multi-task study (Qwen2.5-3B-Instruct, Llama-3.2-3B-Instruct)

Tasks: alphabet, months, planets, number words. A planted run of m repeated items acts as the off-path attractor.

- `core.py`: backend (HF bf16 or llama.cpp), task definitions, trajectory simulation. Restricted softmax over the first tokens of the item list.
- `probe.py MODEL`: chooses weak, sticky and strong m from the next-item probability at T = 0.15 (writes `probe_MODEL.json`).
- `sweep.py MODEL`: runs the cells (40 trajectories each) and stores per-trajectory records in `cells_MODEL_TASK.json`.
- `analyze.py`: computes accuracy, lock-in, entropy, confidence, ECE, discrete semantic entropy and Teff, plus the matched-pair comparison (`analysis.json`).
- `regimes.py`, `stats_for_paper.py`, `figs_final.py`: curve classification, summary counts and figures.
- `stageC_*.json`: alphabet sweeps with a finer temperature grid (up to T = 5) for Qwen2.5-3B, Qwen2.5-7B (Q8_0) and Llama-3.2-3B (the code is in `../teff_stage3`).

Run order: `python3 probe.py qwen3b && python3 sweep.py qwen3b`, the same for `llama3b`, then `python3 analyze.py && python3 regimes.py && python3 figs_final.py`.
